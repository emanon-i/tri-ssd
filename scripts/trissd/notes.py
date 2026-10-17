"""引き継ぎ: 次のセッションが作業を再開するための現在位置。

作業中のメモは Task ファイルの `## メモ` 節に書き、Task の完了と一緒に退場させる（溜まる場所を作らない）。
ここで扱うのは Task をまたぐ引き継ぎだけで、常に上書きする（現在位置は1つ）。
共有の引き継ぎは docs/notes/handoff.md、個人・環境固有のものは .tri-ssd/handoff.md（git 管理外）。
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from .project import LOCAL, NOTES, Project

HANDOFF = "handoff.md"


def ensure_local(root: Path):
    """.tri-ssd/ を自己完結で git 管理外にする（プロジェクトの .gitignore を書き換えない）。"""
    d = root / LOCAL
    d.mkdir(parents=True, exist_ok=True)
    gi = d / ".gitignore"
    if not gi.exists():
        gi.write_text("*\n", encoding="utf-8")


def handoff(p: Project, text: str, local: bool = False) -> str:
    if local:
        ensure_local(p.root)
    path = p.root / (LOCAL if local else NOTES) / HANDOFF
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# 引き継ぎ\n\n更新: {stamp}\n\n{text.strip()}\n")
    return path.relative_to(p.root).as_posix()


def read_handoff(p: Project) -> list[tuple[str, str]]:
    out = []
    for base in (NOTES, LOCAL):
        f = p.root / base / HANDOFF
        if f.exists():
            out.append((f.relative_to(p.root).as_posix(), f.read_text(encoding="utf-8")))
    return out
