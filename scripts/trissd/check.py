"""整合性・衛生検査: 参照切れ・ID 重複・履歴汚染・重複記述・肥大化・状態マーカー・Task 書式。

検出は機械的に行い、意味的な判断（本当に履歴汚染か、どちらを正とするか）は
エージェントに委ねる。そのため履歴汚染・重複は警告（候補の提示）に留める。
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass

from . import md
from .project import CHANGELOG, MARKER_RE, TASK_STATUSES, Project
from .tasks import EVIDENCE_HEAD_RE

DOC_TOKENS_WARN = 4000
GOAL_TOKENS_WARN = 1500

# 履歴汚染の兆候（候補）。現在・将来のあるべき状態を書く Docs に、過去との対比や変更経緯が混入している疑い
HISTORY_PATTERNS = [
    r"以前は", r"以前の(仕様|方式|実装|設計|版)", r"当初(は|の)", r"かつて(は)?", r"元々(は)?", r"もともと",
    r"従来(は|の(仕様|方式|実装|設計))", r"旧(方式|仕様|実装|設計|版|バージョン)", r"変更前", r"変更後",
    r"(に|へ)変更(した|しました|された|されました)", r"から変更", r"(に|へ)置き換え(た|ました|られた)",
    r"(を)?廃止(した|しました|された)", r"これまで(は|の)", r"今(は|では)", r"現在では",
    r"(だった|でした|していた|していました)が", r"(に|へ)移行(した|しました)", r"v\d+(\.\d+)*\s*(で|から|以降|より)",
    r"\bpreviously\b", r"\boriginally\b", r"\bformerly\b", r"\bused to\b", r"\bno longer\b",
    r"\b(was|were|has been|have been) (changed|replaced|renamed|removed)\b", r"\bchanged from\b",
    r"\breplaced (by|with)\b", r"\bnow (uses|use|is|are)\b", r"\bas of v\d", r"\bin the (old|previous) (version|design)\b",
]
HISTORY_RE = re.compile("|".join(HISTORY_PATTERNS), re.I)
DATED_LINE_RE = re.compile(r"^\s*(?:[-*]\s*)?(?:\d{4}-\d{2}-\d{2}\b|\[?v\d+\.\d+)")
HISTORY_HEADING_RE = re.compile(r"(変更履歴|改訂履歴|更新履歴|revision history)", re.I)
STRIKE_RE = re.compile(r"~~[^~\n]+~~")
OK_MARK = "tri:ok"
MANAGED = ("docs/tasks/", "docs/notes/", ".tri-ssd/")


@dataclass
class Issue:
    level: str      # error | warn
    code: str
    path: str
    line: int
    msg: str

    def __str__(self):
        loc = f"{self.path}:{self.line}" if self.line else self.path
        icon = "❌" if self.level == "error" else "⚠️ "
        return f"{icon} [{self.code}] {loc} {self.msg}"


def run(p: Project, changed_base: str | None = None, focus: str | None = None) -> list[Issue]:
    """focus を指定すると重複検査をそのファイル起点に限定する（編集直後のフック用。O(n) で済む）。"""
    issues: list[Issue] = []
    issues += refs(p)
    issues += duplicate_ids(p)
    issues += hygiene(p)
    issues += duplicates(p, focus=focus)
    issues += markers(p)
    issues += tasks(p)
    if changed_base is not None:
        issues += changed(p, changed_base)
    return issues


def refs(p: Project) -> list[Issue]:
    out = []
    for e in p.edges:
        if e.kind == "contains":
            continue
        doc = p.doc_of(e.src)
        if doc.kind in ("task_done", "changelog"):
            continue  # 履歴は書かれた時点の参照を保持する
        if doc.kind == "task" and p.sections[e.src].level >= 2 and EVIDENCE_HEAD_RE.search(p.sections[e.src].title):
            continue  # 検証記録も履歴
        if e.dst.startswith("code:"):
            if e.line == 0 and not p.glob(e.dst[5:]):
                out.append(Issue("warn", "broken-code", doc.path, 0,
                                 f"frontmatter code: `{e.dst[5:]}` に一致するファイルがありません（計画中でなければ移動・削除を反映）"))
            continue
        if p.resolve(e.dst) is not None:
            continue
        level = "warn" if doc.kind == "note" else "error"
        if e.dst.startswith("id:"):
            out.append(Issue(level, "broken-id", doc.path, e.line, f"{e.dst[3:]} の定義がありません"))
        else:
            path, _, anchor = e.dst.partition("#")
            what = f"見出し #{anchor}" if path in p.docs else "ファイル"
            near = [s.slug for s in p.docs[path].sections if s.slug.lower() == md.slugify(anchor)] if path in p.docs else []
            hint = f"（#{near[0]} のこと? 見出しのアンカーは小文字・記号除去）" if near else ""
            out.append(Issue(level, "broken-link", doc.path, e.line, f"リンク先の{what}がありません: {e.dst}{hint}"))
    # 実在しないコードパスの疑い（先頭ディレクトリは実在するのに全体が無い）
    for doc in p.docs.values():
        if doc.kind not in ("goal", "doc"):
            continue
        for ln, line in md.prose_lines(doc.text):
            for cp in md.code_spans(line):
                first = cp.split("/")[0]
                if cp.startswith(MANAGED):
                    continue  # Tri-SSD が必要時に作る領域
                if ("/" in cp and not any(c in cp for c in "*?[") and first and
                        (p.root / first).is_dir() and not (p.root / cp.rstrip("/")).exists()):
                    out.append(Issue("warn", "stale-path", doc.path, ln + 1, f"`{cp}` が存在しません（移動・削除された?）"))
    return out


def duplicate_ids(p: Project) -> list[Issue]:
    return [Issue("error", "dup-id", keys[0].split("#")[0], 0, f"{id_} が複数箇所で定義されています: {', '.join(keys)}")
            for id_, keys in sorted(p.defs.items()) if len(keys) > 1]


def hygiene(p: Project) -> list[Issue]:
    out = []
    for doc in p.docs.values():
        if doc.kind not in ("goal", "doc"):
            continue
        raw = doc.text.splitlines()
        tokens = md.estimate_tokens(doc.text)
        limit = GOAL_TOKENS_WARN if doc.kind == "goal" else DOC_TOKENS_WARN
        if tokens > limit:
            out.append(Issue("warn", "size", doc.path, 0,
                             f"約 {tokens} トークン（目安 {limit}）。重複・過去情報を除去するか、更新契機で分割を検討"))
        if doc.history_allowed:
            continue
        for s in doc.sections[1:]:
            if HISTORY_HEADING_RE.search(s.title):
                out.append(Issue("warn", "history", doc.path, s.start + 1,
                                 f"見出し「{s.title}」: 変更履歴は CHANGELOG へ（Docs には現在の状態だけを書く）"))
        for ln, line in md.prose_lines(doc.text):
            if OK_MARK in raw[ln]:
                continue
            plain = md.strip_inline_code(line)
            m = HISTORY_RE.search(plain)
            if m:
                out.append(Issue("warn", "history", doc.path, ln + 1,
                                 f"履歴汚染の疑い「{m.group(0)}」: {line.strip()[:80]}"))
            elif DATED_LINE_RE.match(plain):
                out.append(Issue("warn", "history", doc.path, ln + 1, f"日付付きの記録: {line.strip()[:80]}"))
            elif STRIKE_RE.search(plain):
                out.append(Issue("warn", "history", doc.path, ln + 1, "取り消し線で旧記述を残している（削除して CHANGELOG へ）"))
    return out


def _paragraphs(doc):
    out, buf, start = [], [], 0
    for ln, line in md.prose_lines(doc.text) + [(10 ** 9, "")]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("|"):
            if buf:
                out.append((start, " ".join(buf)))
            buf = []
            continue
        if not buf:
            start = ln
        buf.append(stripped)
    return out


def _norm(text: str) -> str:
    return re.sub(r"[\W_]+", "", text.lower())


def duplicates(p: Project, min_len: int = 40, threshold: float = 0.8, focus: str | None = None) -> list[Issue]:
    """Goal/Docs 間で同じ事実を重複記述している段落・箇条を検出する（SSOT 違反の候補）。"""
    paras = []
    for doc in p.docs.values():
        if doc.kind not in ("goal", "doc"):
            continue
        for ln, text in _paragraphs(doc):
            n = _norm(text)
            if len(n) >= min_len:
                grams = {n[i:i + 4] for i in range(len(n) - 3)}
                paras.append((doc.path, ln + 1, n, grams))
    out = []
    seen = set()
    for i in range(len(paras)):
        pi, li, ni, gi = paras[i]
        for j in range(i + 1, len(paras)):
            pj, lj, nj, gj = paras[j]
            if focus and focus not in (pi, pj):
                continue
            if min(len(ni), len(nj)) / max(len(ni), len(nj)) < threshold:
                continue
            sim = 1.0 if ni == nj else len(gi & gj) / len(gi | gj)
            if sim >= threshold and (pj, lj) not in seen:
                seen.add((pj, lj))
                out.append(Issue("warn", "duplicate", pj, lj,
                                 f"{pi}:{li} とほぼ同じ記述（類似度 {sim:.2f}）。正を1箇所に決め他は参照に"))
    return out


def markers(p: Project) -> list[Issue]:
    out = []
    for doc in p.docs.values():
        if doc.kind not in ("goal", "doc"):
            continue
        for ln, line in md.prose_lines(doc.text):
            for m in MARKER_RE.finditer(md.strip_inline_code(line)):
                kind, id_ = m.group(1), m.group(2)
                if kind != "計画":
                    continue
                if not id_:
                    out.append(Issue("warn", "marker", doc.path, ln + 1, "（計画）マーカーに Task ID がありません: （計画: T-nnnn）"))
                    continue
                st = p.task_status(id_)
                if st in ("done", "dropped"):
                    out.append(Issue("error", "stale-marker", doc.path, ln + 1,
                                     f"{id_} は {st} です。実装済みならマーカーを外し、中止なら記述を見直す"))
    return out


def tasks(p: Project) -> list[Issue]:
    from .tasks import parse_acs
    out = []
    for doc in p.docs.values():
        if doc.kind not in ("task", "task_done"):
            continue
        fid = str(doc.fm.get("id", ""))
        st = str(doc.fm.get("status", ""))
        if not md.ID_RE.fullmatch(fid):
            out.append(Issue("error", "task", doc.path, 0, "frontmatter に id: T-nnnn がありません"))
        if st not in TASK_STATUSES:
            out.append(Issue("error", "task", doc.path, 0, f"status は {'|'.join(TASK_STATUSES)} のいずれか（現在: {st or '未設定'}）"))
        if doc.kind == "task_done" and st not in ("done", "dropped", ""):
            out.append(Issue("warn", "task", doc.path, 0, f"_done/ にあるが status: {st}"))
        if doc.kind == "task" and st in ("done", "dropped"):
            out.append(Issue("warn", "task", doc.path, 0, f"status: {st} なのに未アーカイブ（task close で検証・移動）"))
        if doc.kind == "task" and st in ("open", "active") and not parse_acs(doc.text):
            out.append(Issue("warn", "task", doc.path, 0, "受け入れ条件（- AC1: ...）がありません"))
    return out


def _git(p: Project, *args: str) -> str | None:
    try:
        r = subprocess.run(["git", *args], cwd=p.root, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout if r.returncode == 0 else None


def changed(p: Project, base: str) -> list[Issue]:
    """作業差分の検査: Docs の肥大化傾向・CHANGELOG の記録漏れ・CHANGELOG の書き換え。"""
    stat = _git(p, "diff", "--numstat", base, "--")
    if stat is None:
        return [Issue("warn", "changed", "", 0, f"git diff {base} を取得できません（git 管理外?）")]
    untracked = (_git(p, "ls-files", "-o", "--exclude-standard") or "").splitlines()
    changes = {}
    for line in stat.splitlines():
        a, d, path = line.split("\t", 2)
        changes[path] = (int(a) if a.isdigit() else 0, int(d) if d.isdigit() else 0)
    for path in untracked:
        if path.endswith(".md") and (p.root / path).is_file():
            changes.setdefault(path, (len((p.root / path).read_text(encoding="utf-8", errors="replace").splitlines()), 0))
    out = []
    spec = [(path, a, d) for path, (a, d) in changes.items()
            if path in p.docs and p.docs[path].kind in ("goal", "doc") and not p.docs[path].history_allowed]
    if spec and CHANGELOG not in changes:
        names = ", ".join(path for path, _, _ in spec)
        out.append(Issue("warn", "changelog", CHANGELOG, 0,
                         f"Docs が変更されたが CHANGELOG 未更新: {names}（意味のある仕様変更なら tri log で記録。文言修正のみなら不要）"))
    for path, a, d in spec:
        existed = _git(p, "cat-file", "-e", f"{base}:{path}") is not None  # 新規ファイルは追記偏重の対象外
        if existed and a >= 20 and d <= a // 10:
            out.append(Issue("warn", "growth", path, 0,
                             f"+{a} 行・削除 {d} 行。置き換えるべき旧記述や重複が残っていないか確認"))
    if CHANGELOG in changes:
        diff = _git(p, "diff", "-U0", base, "--", CHANGELOG) or ""
        lines = diff.splitlines()
        added = {ln[1:].strip() for ln in lines if ln.startswith("+") and not ln.startswith("+++")}
        old = _git(p, "show", f"{base}:{CHANGELOG}") or ""
        m = re.search(r"^## \[?(?!unreleased)[^\n]*\d", old, re.M | re.I)
        released = {ln.strip() for ln in old[m.start():].splitlines()} if m else set()
        removed = [ln for ln in lines if ln.startswith("-") and not ln.startswith("---")
                   and ln[1:].strip() and ln[1:].strip() not in added      # 移動（リリース時の繰り上げ）は除く
                   and ln[1:].strip() in released]                         # 未リリースの記録は直してよい
        if removed:
            out.append(Issue("warn", "changelog", CHANGELOG, 0,
                             f"リリース済みの履歴 {len(removed)} 行が削除・変更されています（リリース済みの記録は追記のみ）"))
    return out
