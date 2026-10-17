"""書かれていない依存の発見: Task の間に変更したコード・参照した Docs のうち、context に入っていなかったもの。

依存を推測で当てるのではなく、作業中に実際に必要になった事実（変更・参照）と、
context が選んだ範囲との差を機械的に示す。書き足すかどうかはエージェントが判断する。
"""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

from . import resolve
from .project import LOCAL, Project
from .tasks import changed_paths

READS = f"{LOCAL}/reads.log"
DOC_PATH_RE = re.compile(r"(?<![\w/.-])((?:\./)?docs/[\w./-]+\.md)")


def track(root: Path, payload: dict) -> int:
    """PostToolUse（Read・Bash）で docs/ の文書を参照したことを記録する。記録だけで何も出力しない。"""
    tool = payload.get("tool_name", "")
    inp = payload.get("tool_input") or {}
    hits: list[tuple[str, str, str]] = []
    if tool == "Read" and inp.get("file_path"):
        try:
            rel = Path(inp["file_path"]).resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            return 0
        start = int(inp.get("offset") or 1)
        end = start + int(inp["limit"]) - 1 if inp.get("limit") else ""
        hits.append((rel, str(start) if inp.get("offset") or inp.get("limit") else "", str(end)))
    elif tool == "Bash":
        for m in DOC_PATH_RE.finditer(inp.get("command", "")):
            hits.append((m.group(1).removeprefix("./"), "", ""))
    hits = [h for h in hits if h[0].startswith("docs/") and h[0].endswith(".md")
            and not h[0].startswith(("docs/tasks/", "docs/notes/"))]
    if not hits:
        return 0
    log = root / READS
    log.parent.mkdir(parents=True, exist_ok=True)
    gi = log.parent / ".gitignore"
    if not gi.exists():
        gi.write_text("*\n", encoding="utf-8")
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log, "a", encoding="utf-8") as f:
        for path, start, end in hits:
            f.write(f"{stamp}\t{path}\t{start}\t{end}\n")
    return 0


def _changed_since(root: Path, base: str | None) -> list[str]:
    return [x for x in changed_paths(root, base) if not x.startswith("docs/") and x != "CHANGELOG.md"]


def _reads_since(root: Path, started: str) -> list[tuple[str, int | None, int | None]]:
    log = root / READS
    if not log.exists() or not started:
        return []
    out = []
    for line in log.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) == 4 and parts[0] >= started:
            out.append((parts[1], int(parts[2]) if parts[2] else None, int(parts[3]) if parts[3] else None))
    return out


def discoveries(p: Project, doc) -> list[tuple[str, str]]:
    """(セクションキー or パス, 理由)。context が選ばなかったのに、この Task で変更・参照に関係した Docs。"""
    id_ = str(doc.fm.get("id"))
    selected = {i.key for i in resolve.context(p, [id_], budget=0).selected}
    selected_files = {k.split("#")[0] for k in selected}
    out: dict[str, str] = {}
    changed = _changed_since(p.root, str(doc.fm.get("base") or "") or None)
    if changed:
        for hits in resolve.impact(p, changed, hops=1)["docs"].values():
            for h in hits:
                if h.key not in selected:
                    out.setdefault(h.key, f"差分のあるコードに関係: {h.reason}")
    for path, start, end in _reads_since(p.root, str(doc.fm.get("started") or "")):
        d = p.docs.get(path)
        if not d or d.kind not in ("goal", "doc"):
            continue
        if start is None:
            if path not in selected_files:
                out.setdefault(path, "この Task の間に文書全体を参照")
            elif not {s.key for s in d.sections if s.text.strip()} <= selected:
                out.setdefault(path, "この Task の間に文書全体を参照（context は一部だけを選定）")
            continue
        for s in d.sections:
            if s.key not in selected and s.text.strip() and s.start < (end or start + 2000) and s.end >= start:
                out.setdefault(s.key, f"この Task の間に参照（{start}行目〜）")
    return sorted(out.items())
