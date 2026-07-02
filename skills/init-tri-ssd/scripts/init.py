#!/usr/bin/env python3
"""Tri-SSD のディレクトリ構造を初期化する。

docs/ 配下に L0-L3 のディレクトリを .gitkeep 付きで作成する。
既存のディレクトリ・ファイルは上書きしない（決定的・冪等）。

使い方:
    python3 init.py [--root DIR]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):  # Windows 等でも UTF-8 出力を保証
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# (相対パス, 説明) — 説明は出力の可読性のためだけに使う
DIRS = [
    ("docs/l0_ideas", "アイディア・ラフメモ（任意）"),
    ("docs/l1_requirements", "要件定義"),
    ("docs/l2_foundation", "システム構成"),
    ("docs/l3_phases", "フェーズ（機能+受け入れ条件）"),
]


def main() -> int:
    ap = argparse.ArgumentParser(description="Tri-SSD ディレクトリ初期化")
    ap.add_argument("--root", default=".", help="プロジェクトルート（既定: カレント）")
    args = ap.parse_args()
    root = Path(args.root)

    created: list[str] = []
    skipped: list[str] = []
    for rel, _desc in DIRS:
        gitkeep = root / rel / ".gitkeep"
        if gitkeep.exists():
            skipped.append(rel)
            continue
        gitkeep.parent.mkdir(parents=True, exist_ok=True)
        gitkeep.touch()
        created.append(rel)

    print("# Tri-SSD 初期化完了")
    if created:
        print("\n## 作成したディレクトリ")
        for c in created:
            print(f"- {c}/")
    if skipped:
        print("\n## 既存（スキップ）")
        for s in skipped:
            print(f"- {s}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
