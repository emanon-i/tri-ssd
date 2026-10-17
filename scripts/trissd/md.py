"""Markdown の機械解析: frontmatter・セクション・ID 参照・リンク・コードパス・トークン推定。

外部依存なし（標準ライブラリのみ）。解析結果はグラフ構築・検査・解決の共通基盤になる。
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# --- ID -----------------------------------------------------------------------
# REQ = Goal/Docs の規範項目、T = Task。PH / F は旧 Tri-SSD（v5 以前）からの移行互換。
ID_PREFIXES = ("REQ", "T", "PH", "F")
ID_RE = re.compile(r"(?<![0-9A-Za-z_-])(REQ|T|PH|F)-(\d{4})(?![0-9A-Za-z])")
TASK_PREFIXES = ("T", "PH", "F")

FM_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.S)
HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
FENCE_RE = re.compile(r"^[ \t]{0,3}(```+|~~~+)")
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
INLINE_CODE_RE = re.compile(r"(`+)(.+?)\1")
LINK_RE = re.compile(r"(?<!!)\[[^\]\n]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
LEGACY_REQ_DEF_RE = re.compile(r"^\s*-\s*\*\*ID\*\*:\s*(REQ-\d{4})")
PATHLIKE_RE = re.compile(r"^\.?/?[\w.\-*]+(?:/[\w.\-*]*)*/?$")


def parse_frontmatter(text: str) -> tuple[dict, int]:
    """YAML frontmatter の最小サブセットを読む（key: value / key: [a, b] / ブロックリスト）。

    戻り値: (辞書, 本文開始行番号)。
    """
    m = FM_RE.match(text)
    if not m:
        return {}, 0
    data: dict = {}
    key = None
    for raw in m.group(1).splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        item = re.match(r"^\s+-\s*(.*)$", line)
        if item and key is not None:
            if not isinstance(data.get(key), list):
                data[key] = []
            data[key].append(_scalar(item.group(1)))
            continue
        kv = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if not kv:
            continue
        key, val = kv.group(1), kv.group(2).strip()
        if val.startswith("[") and val.endswith("]"):
            data[key] = [_scalar(v) for v in val[1:-1].split(",") if v.strip()]
        elif val == "":
            data[key] = []
        else:
            data[key] = _scalar(val)
    return data, m.group(0).count("\n")


def _scalar(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def fm_list(fm: dict, key: str) -> list[str]:
    v = fm.get(key)
    if v is None or v == "":
        return []
    return [str(x) for x in v] if isinstance(v, list) else [str(v)]


def set_fm_value(text: str, key: str, value: str) -> str:
    """frontmatter の key を書き換える（無ければ追加）。他の行の書式は保持する。"""
    m = FM_RE.match(text)
    if not m:
        return f"---\n{key}: {value}\n---\n" + text
    block = m.group(1)
    pat = re.compile(rf"^{re.escape(key)}:.*$", re.M)
    block = pat.sub(f"{key}: {value}", block, count=1) if pat.search(block) else f"{block}\n{key}: {value}"
    end = m.group(0)[m.group(0).rfind("---"):]
    return f"---\n{block}\n{end}" + text[m.end():]


# --- セクション ------------------------------------------------------------------

def slugify(title: str) -> str:
    """GitHub 互換のアンカー slug（小文字化・記号除去・空白をハイフンに）。"""
    s = unicodedata.normalize("NFKC", title).strip().lower()
    s = INLINE_CODE_RE.sub(lambda m: m.group(2), s)
    s = re.sub(r"[^\w\- ]", "", s)
    return s.replace(" ", "-")


@dataclass
class Section:
    path: str            # リポジトリ相対パス
    index: int           # ファイル内の通し番号（0 = 見出し前のプリアンブル）
    level: int           # 0 = プリアンブル, 1-6 = 見出しレベル
    title: str
    slug: str
    start: int           # 開始行（0始まり、見出し行を含む）
    end: int             # 自身の本文の終端（次の見出し行。排他的）
    subtree_end: int     # 配下を含む終端（同レベル以上の次の見出し。排他的）
    parent: int | None
    text: str = ""       # 自身の本文（見出し行を含む。配下の小見出しは含まない）

    @property
    def key(self) -> str:
        return self.path if self.index == 0 else f"{self.path}#{self.slug}"


def split_sections(path: str, text: str, body_start: int = 0) -> list[Section]:
    """見出しでセクションに分割する（コードフェンス内の # は見出しとみなさない）。"""
    lines = text.splitlines()
    heads: list[tuple[int, int, str]] = []
    fence = None
    for i, line in enumerate(lines):
        if i < body_start:
            continue
        fm = FENCE_RE.match(line)
        if fm:
            mark = fm.group(1)[0]
            if fence is None:
                fence = mark
            elif fence == mark:
                fence = None
            continue
        if fence:
            continue
        hm = HEADING_RE.match(line)
        if hm:
            heads.append((i, len(hm.group(1)), hm.group(2).strip()))

    sections = [Section(path, 0, 0, path, "", 0, heads[0][0] if heads else len(lines), len(lines), None)]
    seen: dict[str, int] = {}
    stack: list[int] = []
    for n, (ln, level, title) in enumerate(heads):
        end = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
        sub_end = len(lines)
        for ln2, lv2, _ in heads[n + 1:]:
            if lv2 <= level:
                sub_end = ln2
                break
        while stack and sections[stack[-1]].level >= level:
            stack.pop()
        parent = stack[-1] if stack else 0
        base = slugify(title)
        slug = base if base not in seen else f"{base}-{seen[base]}"
        seen[base] = seen.get(base, 0) + 1
        sections.append(Section(path, len(sections), level, title, slug, ln, end, sub_end, parent))
        stack.append(len(sections) - 1)
    for s in sections:
        s.text = "\n".join(lines[s.start:s.end]).strip("\n")
    return sections


# --- 参照抽出 ---------------------------------------------------------------------

def prose_lines(text: str) -> list[tuple[int, str]]:
    """(行番号, 行) のうちコードフェンス外の行を返す。HTML コメントは空白化する。"""
    stripped = COMMENT_RE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)
    out = []
    fence = None
    for i, line in enumerate(stripped.splitlines()):
        fm = FENCE_RE.match(line)
        if fm:
            mark = fm.group(1)[0]
            if fence is None:
                fence = mark
            elif fence == mark:
                fence = None
            continue
        if not fence:
            out.append((i, line))
    return out


def strip_inline_code(line: str) -> str:
    return INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), line)


def ids_in(line: str) -> list[str]:
    """地の文の ID 参照（インラインコード内は例示とみなし除外）。"""
    return [m.group(0) for m in ID_RE.finditer(strip_inline_code(line))]


def links_in(line: str) -> list[str]:
    """外部 URL 以外の Markdown リンク先（インラインコード内は除外）。"""
    out = []
    for m in LINK_RE.finditer(strip_inline_code(line)):
        target = m.group(1).strip("<>")
        if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I):
            continue
        out.append(target)
    return out


def code_spans(line: str) -> list[str]:
    """パスらしいインラインコード（`src/x.py` 等）を返す。存在確認は呼び出し側で行う。"""
    out = []
    for m in INLINE_CODE_RE.finditer(line):
        s = m.group(2).strip()
        s = re.sub(r"(:\d+(-\d+)?|#L\d+(-L?\d+)?)$", "", s)
        if " " in s or "://" in s or not PATHLIKE_RE.match(s):
            continue
        if "/" not in s and "." not in s:
            continue
        if s.startswith("./"):
            s = s[2:]
        out.append(s)
    return out


# --- トークン推定 -------------------------------------------------------------------

def estimate_tokens(text: str) -> int:
    """トークン数の推定（ASCII は約4文字/トークン、非 ASCII は約1文字/トークン）。

    実トークナイザに依存しない近似値。比較・予算判定用であり課金計算には使わない。
    """
    ascii_n = sum(1 for c in text if ord(c) < 128)
    return int(ascii_n / 4 + (len(text) - ascii_n)) + 1
