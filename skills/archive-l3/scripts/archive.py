#!/usr/bin/env python3
"""完了した L3 フェーズを docs/l3_phases/_archive/ へ移動する。

インライン形式（PH-xxxx_name.md）とフォルダ形式（PH-xxxx_name/）の
両方に対応する。単純な移動のみ（メタデータ追加や要約はしない）。

使い方:
    python3 archive.py --list                 # アクティブなフェーズを一覧
    python3 archive.py <PH-ID | パス>          # 指定フェーズをアーカイブ
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):  # Windows 等でも UTF-8 出力を保証
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

PHASES_DIR = Path("docs/l3_phases")
ARCHIVE_DIR = PHASES_DIR / "_archive"


def active_entries() -> list[Path]:
    if not PHASES_DIR.exists():
        return []
    return sorted(
        p for p in PHASES_DIR.iterdir()
        if p.name.startswith("PH-") and p.name != "_archive"
    )


def resolve(target: str) -> Path | None:
    p = Path(target)
    if p.exists():
        return p
    matches = [e for e in active_entries() if target in e.name]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        joined = ", ".join(m.name for m in matches)
        print(f"error: '{target}' に複数一致しました: {joined}", file=sys.stderr)
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="L3 フェーズのアーカイブ")
    ap.add_argument("target", nargs="?", help="PH-ID またはパス")
    ap.add_argument("--list", action="store_true", help="アクティブなフェーズを一覧表示")
    args = ap.parse_args()

    if args.list or not args.target:
        entries = active_entries()
        if not entries:
            print("アーカイブ可能なフェーズがありません")
            return 0
        print("## アーカイブ可能なフェーズ")
        for e in entries:
            kind = "フォルダ" if e.is_dir() else "インライン"
            print(f"- {e.name}（{kind}）")
        return 0

    target = resolve(args.target)
    if target is None:
        print(f"error: 指定されたフェーズが見つかりません: {args.target}", file=sys.stderr)
        return 1

    if ARCHIVE_DIR.resolve() in target.resolve().parents:
        print(f"warning: 既に _archive/ にあります: {target}", file=sys.stderr)
        return 0

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    dest = ARCHIVE_DIR / target.name
    if dest.exists():
        print(f"error: 同名が _archive/ に存在します: {dest}", file=sys.stderr)
        return 1

    shutil.move(str(target), str(dest))

    print("# アーカイブ完了")
    print(f"\n**移動**: {target} -> {dest}")
    remaining = active_entries()
    print("\n## 残りのアクティブフェーズ")
    if remaining:
        for e in remaining:
            print(f"- {e.name}")
    else:
        print("- （なし）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
