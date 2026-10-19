"""プロジェクトの知識グラフ: 文書の分類・セクション索引・ID 定義・エッジ。

すべて元データ（Markdown・frontmatter・ファイル配置）から毎回導出する。
手で維持する索引やキャッシュは持たない（腐らない・食い違わない）。
"""
from __future__ import annotations

import fnmatch
import posixpath
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import md

DOCS = "docs"
GOAL = "docs/goal.md"
TASKS = "tasks"
DONE = "tasks/archive"
NOTES = "NOTES.md"
CHANGELOG = "CHANGELOG.md"

TASK_STATUSES = ("open", "active", "blocked", "done", "dropped")
HISTORY_KINDS = ("adr", "history")

# 状態マーカー（Docs の記述が「現在の実装」でないことを示す）
MARKER_RE = re.compile(r"[（(](計画|保留|未確定|未検証)(?:\s*[:：]\s*([A-Z]+-\d{4}))?[）)]")


@dataclass
class Edge:
    src: str        # セクションキー
    dst: str        # セクションキー / "id:XXX"（未解決）/ "code:path"
    kind: str       # contains | ref | link | depends | code
    line: int       # 参照元の行（1始まり、ファイル基準。0 = frontmatter）


@dataclass
class Doc:
    path: str
    kind: str                       # goal | doc | task | task_done | note | changelog
    text: str
    fm: dict
    sections: list[md.Section]

    @property
    def history_allowed(self) -> bool:
        return (self.fm.get("kind") in HISTORY_KINDS
                or "/adr/" in f"/{self.path}"
                or self.kind in ("task", "task_done", "note", "changelog"))

    def section_at(self, line0: int) -> md.Section:
        """0始まりの行番号を含む最も深いセクション。"""
        for s in self.sections[1:]:
            if s.start <= line0 < s.end:
                return s
        return self.sections[0]


def classify(rel: str) -> str:
    if rel == GOAL:
        return "goal"
    if rel == CHANGELOG:
        return "changelog"
    if rel.startswith(DONE + "/"):
        return "task_done"
    if rel.startswith(TASKS + "/"):
        return "task"
    if rel == NOTES:
        return "note"
    return "doc"


def is_knowledge(rel: str) -> bool:
    """Tri-SSD が読む知識のファイルか（docs/・tasks/ の Markdown、NOTES.md、CHANGELOG.md）。"""
    return rel in (NOTES, CHANGELOG) or (rel.endswith(".md") and rel.startswith((DOCS + "/", TASKS + "/")))


class Project:
    def __init__(self, root: str | Path = "."):
        self.root = Path(root).resolve()
        self.docs: dict[str, Doc] = {}
        self.sections: dict[str, md.Section] = {}
        self.defs: dict[str, list[str]] = {}        # ID -> 定義セクションキー（ファイル単位で重複排除）
        self.edges: list[Edge] = []
        self._load()

    # --- 読み込み ---------------------------------------------------------------
    def _files(self):
        for base in (DOCS, TASKS):
            d = self.root / base
            if d.is_dir():
                yield from sorted(p for p in d.rglob("*.md") if p.is_file())
        for name in (NOTES, CHANGELOG):
            f = self.root / name
            if f.is_file():
                yield f

    def _load(self):
        for p in self._files():
            rel = p.relative_to(self.root).as_posix()
            try:
                text = p.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            fm, body = md.parse_frontmatter(text)
            secs = md.split_sections(rel, text, body)
            doc = Doc(rel, classify(rel), text, fm, secs)
            self.docs[rel] = doc
            for s in secs:
                self.sections[s.key] = s
        for doc in self.docs.values():
            self._index(doc)

    def _index(self, doc: Doc):
        secs = doc.sections
        for s in secs[1:]:
            self.edges.append(Edge(secs[s.parent].key, s.key, "contains", s.start + 1))
        if doc.kind == "changelog":
            return  # 履歴は定義・参照の対象にしない（採番の走査対象にはなる）
        home_task = doc.kind in ("task", "task_done")
        home_req = doc.kind in ("goal", "doc")

        def define(id_: str, sec: md.Section):
            keys = self.defs.setdefault(id_, [])
            if not any(k.split("#")[0] == sec.path for k in keys):
                keys.append(sec.key)

        fid = str(doc.fm.get("id", ""))
        if md.ID_RE.fullmatch(fid):
            define(fid, secs[0])
        for key in ("refs", "depends", "requires"):
            for v in md.fm_list(doc.fm, key):
                self.edges.append(Edge(secs[0].key, self._target(doc.path, v), "depends", 0))
        for v in md.fm_list(doc.fm, "code"):
            self.edges.append(Edge(secs[0].key, "code:" + v.strip("/") + ("/" if v.endswith("/") else ""), "code", 0))

        body = self._body_start(doc)
        for ln, line in md.prose_lines(doc.text):
            if ln < body:
                continue
            sec = doc.section_at(ln)
            is_heading = ln == sec.start and sec.level > 0
            legacy = md.LEGACY_REQ_DEF_RE.match(line)
            for i, id_ in enumerate(md.ids_in(line)):
                prefix = id_.split("-")[0]
                defines = (
                    (is_heading and i == 0 and ((prefix == "REQ" and home_req) or (prefix in md.TASK_PREFIXES and home_task)))
                    or (legacy and legacy.group(1) == id_ and home_req)
                )
                if defines:
                    define(id_, sec)
                else:
                    self.edges.append(Edge(sec.key, "id:" + id_, "ref", ln + 1))
            for target in md.links_in(line):
                self.edges.append(Edge(sec.key, self._target(doc.path, target, relative=True), "link", ln + 1))
            for cp in md.code_spans(line):
                tgt = self._code_or_doc(cp)
                if tgt:
                    self.edges.append(Edge(sec.key, tgt, "link" if not tgt.startswith("code:") else "code", ln + 1))

    def _body_start(self, doc: Doc) -> int:
        m = md.FM_RE.match(doc.text)
        return m.group(0).count("\n") if m else 0

    def _target(self, src_path: str, value: str, relative: bool = False) -> str:
        """frontmatter / リンクの値を ID・セクションキー・code: に正規化する。"""
        value = value.strip()
        if md.ID_RE.fullmatch(value):
            return "id:" + value
        path, _, anchor = value.partition("#")
        if not path:
            path = src_path
        elif relative:
            path = posixpath.normpath(posixpath.join(posixpath.dirname(src_path), path))
        else:
            path = posixpath.normpath(path)
            if not (self.root / path).exists() and (self.root / DOCS / path).exists():
                path = f"{DOCS}/{path}"  # docs 相対の表記も受け付ける
        if path.endswith(".md"):
            return f"{path}#{anchor}" if anchor else path
        return "code:" + path

    def _code_or_doc(self, span: str) -> str | None:
        """インラインコードのパスが実在するときだけエッジにする（例示の誤検出を防ぐ）。"""
        p = span.rstrip("/")
        if any(c in p for c in "*?["):
            return "code:" + span if self.glob(span) else None
        full = self.root / p
        if not full.exists():
            return None
        if is_knowledge(p):
            return p
        return "code:" + (p + "/" if full.is_dir() else p)

    # --- 問い合わせ -------------------------------------------------------------
    def resolve(self, dst: str) -> str | None:
        """エッジの宛先をセクションキーへ解決する（解決できなければ None）。"""
        if dst.startswith("id:"):
            keys = self.defs.get(dst[3:])
            return keys[0] if keys else None
        if dst.startswith("code:"):
            return dst
        if dst in self.sections:
            return dst
        path, _, anchor = dst.partition("#")
        if anchor and path in self.docs:
            for s in self.docs[path].sections:
                if s.slug == anchor:
                    return s.key
        return None

    def code_ids(self) -> dict[str, list[str]]:
        """コード（docs/・tasks/・Markdown 以外の git 管理ファイル）に書かれた ID → パス。`git grep` で求める。"""
        if hasattr(self, "_code_ids"):
            return self._code_ids
        import subprocess
        self._code_ids: dict[str, list[str]] = {}
        try:
            r = subprocess.run(["git", "grep", "-I", "-o", "-E", r"\b(REQ|T|PH|F)-[0-9]{4}\b", "--", ".",
                                ":(exclude)docs", ":(exclude)tasks", ":(exclude)*.md"],
                               cwd=self.root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        except (OSError, subprocess.TimeoutExpired):
            return self._code_ids
        for line in r.stdout.splitlines():
            path, _, id_ = line.rpartition(":")
            if path and id_ in self.defs:
                paths = self._code_ids.setdefault(id_, [])
                if path not in paths:
                    paths.append(path)
        return self._code_ids

    def glob(self, pattern: str) -> list[str]:
        pat = pattern.rstrip("/")
        if not any(c in pat for c in "*?["):
            return [pat] if (self.root / pat).exists() else []
        return [p.relative_to(self.root).as_posix() for p in self.root.glob(pat)
                if ".git" not in p.parts][:1000]

    def doc_of(self, key: str) -> Doc:
        return self.docs[key.split("#")[0]]

    def subtree(self, key: str) -> list[md.Section]:
        s = self.sections[key]
        return [x for x in self.docs[s.path].sections if x.start >= s.start and x.end <= s.subtree_end and x.index >= s.index]

    def task_docs(self, include_done: bool = False) -> list[Doc]:
        kinds = ("task", "task_done") if include_done else ("task",)
        return [d for d in self.docs.values() if d.kind in kinds and md.ID_RE.fullmatch(str(d.fm.get("id", "")))]

    def task_status(self, id_: str) -> str | None:
        for key in self.defs.get(id_, []):
            d = self.doc_of(key)
            if d.kind in ("task", "task_done"):
                return str(d.fm.get("status", "done" if d.kind == "task_done" else "open"))
        return None

    def max_id(self, prefix: str) -> int:
        """全文書（アーカイブ・ノート・CHANGELOG 含む）に現れた最大番号。永久欠番の根拠。"""
        pat = re.compile(rf"(?<![0-9A-Za-z_-]){re.escape(prefix)}-(\d{{4}})(?![0-9])")
        n = 0
        for d in self.docs.values():
            for _, line in md.prose_lines(d.text):  # コードブロック・インラインコード内は例示
                for m in pat.finditer(md.strip_inline_code(line)):
                    n = max(n, int(m.group(1)))
            for v in (d.fm.get("id"), *md.fm_list(d.fm, "refs")):
                m = pat.fullmatch(str(v or ""))
                if m:
                    n = max(n, int(m.group(1)))
        for p in (self.root / TASKS).rglob("*.md") if (self.root / TASKS).is_dir() else []:
            for m in pat.finditer(p.name):
                n = max(n, int(m.group(1)))
        return n


def code_covers(pattern: str, path: str) -> bool:
    """コードパターン（ファイル・ディレクトリ・glob）が path を含むか。"""
    pat = pattern.rstrip("/")
    path = path.rstrip("/")
    if any(c in pat for c in "*?["):
        return fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(path, pat + "/*") or fnmatch.fnmatch(path + "/x", pat)
    return path == pat or path.startswith(pat + "/")


def code_related(a: str, b: str) -> bool:
    return code_covers(a, b) or code_covers(b, a)
