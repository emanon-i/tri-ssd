#!/usr/bin/env python3
"""Tri-SSD ドキュメントの ID 整合性を検証する（スキル共有スクリプト）。

検証内容:
  1. dangling 参照: 参照されている REQ / F / PH が定義に存在しない
  2. 重複定義: 同一 ID が複数箇所で定義されている
  3. status 突合: frontmatter `status: done` の PH に PASS 未記録の F がある
  4. 進捗サマリ: アクティブな PH ごとの status / F 数 / PASS 数

定義の判定:
  - REQ: docs/l1_requirements/ 配下の Markdown 見出し行、または
         `- **ID**: REQ-nnnn` 形式の行に現れる REQ-nnnn
  - PH : docs/l3_phases/ 配下のファイル名・frontmatter id・見出し行の PH-nnnn。
         フォルダ形式（PH-xxxx_name/ に _phase.md・F-*.md）はフォルダ単位で
         1定義に正規化する（フォルダ名・frontmatter id・見出しが同じ PH を
         指す限り、由来ファイルによらず同一の定義箇所として扱う）
  - F  : docs/l3_phases/ 配下の見出し行に現れる F-nnnn
  （`_archive/` 内の定義も有効。アーカイブ済み ID への参照はエラーにしない）

使い方:
    python3 validate_ids.py [--docs DIR] [--quiet]

終了コード: 0 = エラーなし / 1 = dangling 参照または重複定義あり
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):  # Windows 等でも UTF-8 出力を保証
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

ID_RE = re.compile(r"(?<![0-9A-Za-z])(REQ|PH|F)-(\d{4})(?![0-9])")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s")
REQ_DEF_RE = re.compile(r"^\s*-\s*\*\*ID\*\*:\s*(REQ-\d{4})")
FRONTMATTER_ID_RE = re.compile(r"^id:\s*(PH-\d{4})\s*$", re.MULTILINE)
STATUS_RE = re.compile(r"^status:\s*(\S+)\s*$", re.MULTILINE)
PASS_RE = re.compile(r"(?<![0-9A-Za-z])(F-\d{4})\b[^\n]*\bPASS\b")

HOME_DIR = {"REQ": "l1_requirements", "PH": "l3_phases", "F": "l3_phases"}


def read(md: Path) -> str:
    try:
        return md.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def folder_ph(md: Path, docs: Path) -> tuple[str | None, str | None]:
    """パス上にフォルダ形式 PH（PH-xxxx_name/）があれば (PH-ID, フォルダの相対パス) を返す。"""
    acc: list[str] = []
    for part in md.relative_to(docs).parts[:-1]:
        acc.append(part)
        m = ID_RE.fullmatch(part.split("_")[0])
        if m and m.group(1) == "PH":
            return m.group(0), "/".join(acc)
    return None, None


def collect(docs: Path):
    """定義・参照・PH 進捗情報を全 *.md から収集する。"""
    defined: dict[str, list[str]] = defaultdict(list)   # ID -> 定義箇所
    referenced: dict[str, set[str]] = defaultdict(set)  # ID -> 参照箇所

    # アクティブ PH の進捗情報（フォルダ形式はフォルダ単位に後で集約する）
    file_records: list[dict] = []
    folder_groups: dict[str, dict] = {}

    for md in sorted(docs.rglob("*.md")):
        text = read(md)
        if not text:
            continue
        rel = md.relative_to(docs).as_posix()
        in_l3 = rel.startswith("l3_phases/")
        archived = "/_archive/" in f"/{rel}"
        ph_folder_id, ph_folder_loc = folder_ph(md, docs)

        # ファイル名からの PH 定義（例: PH-0001_setup.md）。1回の走査結果を
        # defined 登録と、後段の ph_ids フォールバックの両方に使い回す。
        stem_ph_ids = [m.group(0) for m in ID_RE.finditer(md.stem) if m.group(1) == "PH"]
        for pid in stem_ph_ids:
            defined[pid].append(rel)

        # フォルダ形式 PH の定義箇所（フォルダ単位に正規化。由来ファイルが
        # 何であっても同一の場所文字列にすることで、正常な複数ファイルからの
        # 検出が「重複定義」に誤検知されないようにする）
        if ph_folder_id:
            defined[ph_folder_id].append(ph_folder_loc)

        # frontmatter id: からの PH 定義。フォルダ形式でフォルダ名と一致する
        # 場合はフォルダの定義箇所に畳み込み、別の ID を指す場合のみ個別に扱う。
        for m in FRONTMATTER_ID_RE.finditer(text):
            fid = m.group(1)
            loc = ph_folder_loc if (ph_folder_id and fid == ph_folder_id) else rel
            defined[fid].append(loc)

        # 行走査: 見出し行 / REQ の `- **ID**:` 行 = 定義（ホームレイヤー内のみ）、
        # それ以外 = 参照
        f_defined_this_file: set[str] = set()
        for line in text.splitlines():
            ids = list(ID_RE.finditer(line))
            if not ids:
                continue
            is_heading = bool(HEADING_RE.match(line))
            req_def_m = REQ_DEF_RE.match(line)
            for m in ids:
                full, prefix = m.group(0), m.group(1)
                home = rel.startswith(HOME_DIR[prefix] + "/")
                is_def = home and (
                    is_heading
                    or (prefix == "REQ" and req_def_m and req_def_m.group(1) == full)
                )
                if not is_def:
                    referenced[full].add(rel)
                    continue
                if prefix == "PH":
                    loc = ph_folder_loc if (ph_folder_id and full == ph_folder_id) else rel
                    defined[full].append(loc)
                else:
                    defined[full].append(rel)
                    if prefix == "F":
                        f_defined_this_file.add(full)

        # アクティブ PH の進捗情報
        if in_l3 and not archived:
            sm = STATUS_RE.search(text)
            record = {
                "status": sm.group(1) if sm else None,
                "features": f_defined_this_file,
                "passed": {m.group(1) for m in PASS_RE.finditer(text)},
            }
            if ph_folder_loc:
                g = folder_groups.setdefault(ph_folder_loc, {
                    "id": ph_folder_id, "file": ph_folder_loc + "/", "status": "-",
                    "features": set(), "passed": set(),
                })
                g["features"] |= record["features"]
                g["passed"] |= record["passed"]
                if md.name == "_phase.md" and record["status"]:
                    g["status"] = record["status"]
            else:
                file_records.append({
                    "id": (stem_ph_ids or ["(no PH id)"])[0],
                    "file": rel,
                    "status": record["status"] or "-",
                    "features": sorted(record["features"]),
                    "passed": sorted(record["passed"]),
                })

    phases = file_records + [
        {"id": g["id"], "file": g["file"], "status": g["status"],
         "features": sorted(g["features"]), "passed": sorted(g["passed"])}
        for g in folder_groups.values()
    ]

    return defined, referenced, phases


def main() -> int:
    ap = argparse.ArgumentParser(description="Tri-SSD ID 整合性を検証する")
    ap.add_argument("--docs", default="docs", help="検索対象ディレクトリ（既定: docs）")
    ap.add_argument("--quiet", action="store_true", help="エラー・警告のみ出力")
    args = ap.parse_args()

    docs = Path(args.docs)
    if not docs.exists():
        print(f"error: {docs} が見つかりません", file=sys.stderr)
        return 2

    defined, referenced, phases = collect(docs)
    errors: list[str] = []
    warnings: list[str] = []

    # 1. dangling 参照
    # PH-0000 のみ特例: gen-l2 の `（未確認・PH-0000 で検証）` 印は PH-0000 生成前に
    # 書かれる規定運用のため、未生成はエラーでなく情報として扱う
    for id_, places in sorted(referenced.items()):
        if id_ not in defined:
            where = ", ".join(sorted(places))
            if id_ == "PH-0000":
                warnings.append(
                    f"PH-0000 が未生成です（参照元: {where}）。/gen-l3 の初回実行で生成されます")
                continue
            errors.append(f"dangling 参照: {id_} は定義が見つかりません（参照元: {where}）")

    # 2. 重複定義（同一ファイル・同一フォルダ内の複数定義は1定義とみなす）
    for id_, places in sorted(defined.items()):
        uniq = sorted(set(places))
        if len(uniq) > 1:
            errors.append(f"重複定義: {id_} が複数箇所で定義されています（{', '.join(uniq)}）")

    # 3. status: done と検証記録の突合
    for ph in phases:
        if ph["status"] == "done":
            missing = [f for f in ph["features"] if f not in ph["passed"]]
            if missing:
                warnings.append(
                    f"{ph['id']} は status: done ですが PASS 未記録の機能があります: {', '.join(missing)}")

    for e in errors:
        print(f"❌ {e}")
    for w in warnings:
        print(f"⚠️  {w}")

    # 4. 進捗サマリ
    if not args.quiet:
        print()
        print("進捗サマリ（アクティブな PH）:")
        if not phases:
            print("  （アクティブな PH はありません）")
        for ph in sorted(phases, key=lambda p: p["id"]):
            n, p = len(ph["features"]), len(ph["passed"])
            print(f"  {ph['id']}  status={ph['status']}  F: {p}/{n} PASS  ({ph['file']})")
        print()
        print(f"検証完了: エラー {len(errors)} 件 / 警告 {len(warnings)} 件")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
