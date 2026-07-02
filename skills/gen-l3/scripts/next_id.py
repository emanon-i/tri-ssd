#!/usr/bin/env python3
"""既存の Tri-SSD ID を走査し、次の連番 ID を出力する。

ID 形式は PREFIX-nnnn（4桁ゼロ埋め）。docs/ 配下の *.md を再帰的に
検索し、指定 PREFIX の最大番号 + 1 から採番する。1件も無ければ 0001。

使い方:
    python3 next_id.py <PREFIX> [--count N] [--docs DIR]

例:
    python3 next_id.py PH            # -> PH-0002
    python3 next_id.py F --count 3   # -> F-0012 / F-0013 / F-0014（改行区切り）
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):  # Windows 等でも UTF-8 出力を保証
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def find_max(prefix: str, docs_dir: Path) -> int:
    # 前後が英数字でない位置の PREFIX-nnnn のみを対象にする（誤マッチ防止）
    pattern = re.compile(rf"(?<![0-9A-Za-z]){re.escape(prefix)}-(\d{{4}})(?![0-9])")
    max_n = 0
    if not docs_dir.exists():
        return 0
    for md in docs_dir.rglob("*.md"):
        try:
            text = md.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for m in pattern.finditer(text):
            max_n = max(max_n, int(m.group(1)))
    return max_n


def main() -> int:
    ap = argparse.ArgumentParser(description="次の Tri-SSD 連番 ID を出力する")
    ap.add_argument("prefix", help="ID プレフィックス（REQ / PH / F）")
    ap.add_argument("--count", type=int, default=1, help="出力する ID の個数（既定: 1）")
    ap.add_argument("--docs", default="docs", help="検索対象ディレクトリ（既定: docs）")
    args = ap.parse_args()

    if args.count < 1:
        print("error: --count は 1 以上を指定してください", file=sys.stderr)
        return 2

    start = find_max(args.prefix, Path(args.docs)) + 1
    for i in range(args.count):
        print(f"{args.prefix}-{start + i:04d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
