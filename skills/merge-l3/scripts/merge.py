#!/usr/bin/env python3
"""フォルダ構造の L3 フェーズをインライン形式の1ファイルに統合する。

_phase.md と F-*.md（ファイル名順）を PH-xxxx_name.md に統合する。
チェック状態 [x] は保持。統合後に元フォルダを削除する。
split.py の逆操作で、往復可能。

使い方:
    python3 merge.py <PH-ID | フォルダパス>
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):  # Windows 等でも UTF-8 出力を保証
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

PHASES_DIR = Path("docs/l3_phases")


def resolve_folder(target: str) -> Path | None:
    p = Path(target)
    if p.is_dir():
        return p
    if PHASES_DIR.exists():
        matches = [
            d for d in PHASES_DIR.glob("PH-*")
            if d.is_dir() and d.name != "_archive" and target in d.name
        ]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            joined = ", ".join(m.name for m in matches)
            print(f"error: '{target}' に複数一致: {joined}", file=sys.stderr)
    return None


def write_lf(path: Path, text: str) -> None:
    """改行を LF に固定して書き出す（OS 非依存の決定的出力）。"""
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def get_title(text: str) -> str:
    for ln in text.splitlines():
        if ln.startswith("# PH-"):
            return ln[2:].strip()
    return ""


def get_section(text: str, name: str) -> str:
    m = re.search(rf"(?m)^##\s+{re.escape(name)}\s*$", text)
    if not m:
        return ""
    start = m.end()
    nxt = re.search(r"(?m)^##\s+", text[start:])
    end = start + nxt.start() if nxt else len(text)
    return text[start:end].strip("\n")


def feature_to_inline(text: str) -> str:
    """F ファイル本文を ### F-xxxx ブロック（インライン形式）に変換する。"""
    lines = text.splitlines()
    title = ""
    rest_start = 0
    for i, ln in enumerate(lines):
        m = re.match(r"^#\s+(F-\d+\s*:.*)$", ln)
        if m:
            title = m.group(1).strip()
            rest_start = i + 1
            break
    body = "\n".join(lines[rest_start:]).strip("\n")
    # F ファイルの ## 受け入れ条件 をインラインの **受け入れ条件**: に戻す
    body = re.sub(r"(?m)^##\s+受け入れ条件\s*$", "**受け入れ条件**:", body)
    return f"### {title}\n{body}".rstrip()


def main() -> int:
    ap = argparse.ArgumentParser(description="L3 フェーズの統合")
    ap.add_argument("target", help="PH-ID またはフォルダパス")
    args = ap.parse_args()

    folder = resolve_folder(args.target)
    if folder is None:
        print(f"error: 指定されたフォルダが見つかりません: {args.target}", file=sys.stderr)
        return 1

    phase_file = folder / "_phase.md"
    if not phase_file.exists():
        print("error: _phase.md が見つかりません", file=sys.stderr)
        return 1
    f_files = sorted(folder.glob("F-*.md"), key=lambda p: p.name)
    if not f_files:
        print("error: 機能ファイル（F-*.md）が見つかりません", file=sys.stderr)
        return 1

    dest = folder.parent / (folder.name + ".md")
    if dest.exists():
        print(f"error: 同名ファイルが存在します: {dest}", file=sys.stderr)
        return 1

    phase_text = phase_file.read_text(encoding="utf-8")
    title = get_title(phase_text)
    purpose = get_section(phase_text, "目的")
    exit_c = get_section(phase_text, "Exit Criteria")

    blocks = [feature_to_inline(ff.read_text(encoding="utf-8")) for ff in f_files]
    feat_body = "\n\n---\n\n".join(blocks)

    inline = (
        f"# {title}\n\n## 目的\n{purpose}\n\n## 機能一覧\n\n"
        f"{feat_body}\n\n---\n\n## Exit Criteria\n{exit_c}\n"
    )
    write_lf(dest, inline)
    shutil.rmtree(folder)

    checked = len(re.findall(r"- \[x\]", inline))
    total = len(re.findall(r"- \[[ x]\]", inline))
    print("# 統合完了")
    print(f"\n**入力**: {folder}/")
    print(f"**出力**: {dest}")
    print(f"\n## 統合内容\n- 機能数: {len(f_files)}")
    print(f"\n## チェック状態\n- チェック済み: {checked}/{total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
