"""Note: 作業中の一時情報（現在位置・仮説・調査結果・引き継ぎ）。

- 記録時に分類や ID を強制しない（`## 日付 見出し` の追記だけ）
- handoff.md は追記せず上書きする（現在位置は常に1つ。溜まらない）
- 整理（triage）は機械で候補を出し、昇格・削除の判断はエージェントが行う
- 共有ノートは docs/notes/（git 管理）、個人・環境固有は .tri-ssd/notes/（git 管理外）
"""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import md
from .project import LOCAL, LOCAL_NOTES, NOTES, Project

HANDOFF = "handoff.md"
INBOX = "inbox.md"
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
STALE_DAYS = 14
KEEP_MARK = "tri:keep"   # 意図して残すエントリ（整理候補にしない）


def notes_dir(p: Project, local: bool) -> Path:
    d = p.root / (LOCAL_NOTES if local else NOTES)
    d.mkdir(parents=True, exist_ok=True)
    if local:
        ensure_local(p.root)
    return d


def ensure_local(root: Path):
    """.tri-ssd/ を自己完結で git 管理外にする（プロジェクトの .gitignore を書き換えない）。"""
    d = root / LOCAL
    d.mkdir(parents=True, exist_ok=True)
    gi = d / ".gitignore"
    if not gi.exists():
        gi.write_text("*\n", encoding="utf-8")


def add(p: Project, text: str, task: str | None = None, local: bool = False, file: str = INBOX) -> str:
    """`## 日時 [Task-ID] [題]` を追記する。題は複数行の本文の1行目だけ（1行の本文は見出しに重複させない）。"""
    path = notes_dir(p, local) / file
    lines = text.strip().splitlines()
    title, body = (lines[0].strip(), "\n".join(lines[1:]).strip()) if len(lines) > 1 else ("", text.strip())
    head = " ".join(x for x in (dt.datetime.now().strftime("%Y-%m-%d %H:%M"), task, title) if x)
    existing = path.read_text(encoding="utf-8") if path.exists() else "# ノート\n"
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(existing.rstrip("\n") + f"\n\n## {head}\n" + (f"\n{body}\n" if body else ""))
    return path.relative_to(p.root).as_posix()


def handoff(p: Project, text: str, local: bool = False) -> str:
    path = notes_dir(p, local) / HANDOFF
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# 引き継ぎ\n\n更新: {stamp}\n\n{text.strip()}\n")
    return path.relative_to(p.root).as_posix()


def read_handoff(p: Project) -> list[tuple[str, str]]:
    out = []
    for base in (NOTES, LOCAL_NOTES):
        f = p.root / base / HANDOFF
        if f.exists():
            out.append((f.relative_to(p.root).as_posix(), f.read_text(encoding="utf-8")))
    return out


@dataclass
class Entry:
    path: str
    line: int
    title: str
    date: str | None
    age: int | None
    tokens: int
    refs: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)


def entries(p: Project) -> list[Entry]:
    out = []
    today = dt.date.today()
    for doc in p.docs.values():
        if doc.kind != "note" or doc.path.endswith("/" + HANDOFF):
            continue
        units = [s for s in doc.sections if s.level == 2] or [doc.sections[0]]
        if units == [doc.sections[0]] or len(units) == 0:
            units = [doc.sections[0]]
            text_of = {units[0].key: doc.text}
        else:
            lines = doc.text.splitlines()
            text_of = {s.key: "\n".join(lines[s.start:s.subtree_end]) for s in units}
        for s in units:
            text = text_of[s.key]
            dm = DATE_RE.search(s.title)
            if dm:
                date = dm.group(1)
            else:
                date = dt.date.fromtimestamp((p.root / doc.path).stat().st_mtime).isoformat()
            try:
                age = (today - dt.date.fromisoformat(date)).days
            except ValueError:
                age = None
            refs = sorted({i for _, line in md.prose_lines(text) for i in md.ids_in(line)})
            first = next((x.strip() for x in text.splitlines()[1:] if x.strip() and not x.startswith("<!--")), "")
            label = (s.title if s.level else doc.path) + (f" — {first[:60]}" if first else "")
            e = Entry(doc.path, s.start + 1, label, date, age, md.estimate_tokens(text), refs)
            if KEEP_MARK in text:
                out.append(e)
                continue
            task_refs = [r for r in refs if p.task_status(r) is not None]
            if task_refs and all(p.task_status(r) in ("done", "dropped") for r in task_refs):
                e.flags.append("task-closed")  # 昇格・削除、未解決の問いなら tri:keep
            if age is not None and age > STALE_DAYS:
                e.flags.append("old")
            if e.tokens > 800:
                e.flags.append("large")
            out.append(e)
    return out
