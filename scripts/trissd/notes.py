"""NOTES.md: 次のセッションが作業を再開するための現在位置・次にやること・未決事項。

作業中のメモは Task ファイルの `## メモ` 節に書き、Task の完了と一緒に退場させる（溜まる場所を作らない）。
NOTES.md は Task をまたぐ現在位置だけを持ち、常に上書きする（現在位置は1つ）。
"""
from __future__ import annotations

import datetime as dt

from .project import NOTES, Project


def write(p: Project, text: str) -> str:
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(p.root / NOTES, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# NOTES\n\n更新: {stamp}\n\n{text.strip()}\n")
    return NOTES


def read(p: Project) -> str | None:
    f = p.root / NOTES
    return f.read_text(encoding="utf-8") if f.exists() else None
