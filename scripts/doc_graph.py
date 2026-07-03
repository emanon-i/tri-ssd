#!/usr/bin/env python3
"""Tri-SSD ドキュメントの依存グラフを抽出する（スキル共有スクリプト）。

docs/ 配下の Markdown から、既存の ID 参照と frontmatter を機械的に集めて
「どの文書がどの ID を定義し、どこから参照されているか」の依存マップを作る。
エッジは手で維持せず**既存データから導出**する（維持コストゼロ＝腐らない）。
任意の frontmatter `depends:`（ID または docs 相対パスのリスト）で明示エッジを補える。

エッジの種類:
  defines    : 文書 → ID（見出し・`- **ID**:` 行・frontmatter id・ファイル名による定義）
  references : 文書 → ID（定義以外の言及）
  requires   : 文書 → ID（frontmatter `requires:`）
  depends    : 文書 → ID/文書（frontmatter `depends:`。任意）
  pointer    : l2_foundation の文書 → 分離ファイル（interface.md / data.md / glossary.md）

使い方:
    python3 doc_graph.py [--docs DIR] [--format edges|mermaid|json]
    python3 doc_graph.py --focus F-0012 [--hops 2]

`--focus` は「その ID / 文書に着手する前に読むべき最小の文書集合」を返す
（gen-code の段階的注入＝関連文書だけ読むために使う）。
終了コード: 0 = 正常 / 2 = docs 不在・focus 対象不明
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):  # Windows 等でも UTF-8 出力を保証
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_ids import ID_RE, collect, read  # noqa: E402

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
LIST_KEY_RE = {
    key: re.compile(rf"^{key}:\s*\[([^\]]*)\]|^{key}:\s*$", re.MULTILINE)
    for key in ("requires", "depends")
}
BLOCK_ITEM_RE = re.compile(r"^\s*-\s*(.+?)\s*$")
POINTER_RE = re.compile(r"`((?:interface|data|glossary)\.md)`")


def frontmatter_list(fm: str, key: str) -> list[str]:
    """frontmatter からインライン形式・ブロック形式のリスト値を取り出す。"""
    m = LIST_KEY_RE[key].search(fm)
    if not m:
        return []
    if m.group(1) is not None:  # インライン形式 key: [a, b]
        return [v.strip().strip("\"'") for v in m.group(1).split(",") if v.strip()]
    items: list[str] = []  # ブロック形式 key:\n  - a
    for line in fm[m.end():].splitlines():
        im = BLOCK_ITEM_RE.match(line)
        if not im:
            break
        items.append(im.group(1).strip("\"'"))
    return items


def build_graph(docs: Path):
    """(edges, ノード種別) を返す。edges は (src, kind, dst) の集合。"""
    defined, referenced, _ = collect(docs)
    edges: set[tuple[str, str, str]] = set()
    explicit_map: dict[str, set[str]] = defaultdict(set)  # requires/depends 済みの ID

    for md in sorted(docs.rglob("*.md")):
        text = read(md)
        if not text:
            continue
        rel = md.relative_to(docs).as_posix()
        fm_m = FRONTMATTER_RE.match(text)
        fm = fm_m.group(1) if fm_m else ""
        for rid in frontmatter_list(fm, "requires"):
            if ID_RE.fullmatch(rid):
                edges.add((rel, "requires", rid))
                explicit_map[rel].add(rid)
        for dep in frontmatter_list(fm, "depends"):
            target = dep if ID_RE.fullmatch(dep) else Path(dep).as_posix()
            edges.add((rel, "depends", target))
            explicit_map[rel].add(target)
        if rel.startswith("l2_foundation/"):
            for m in POINTER_RE.finditer(text):
                target = f"l2_foundation/{m.group(1)}"
                if (docs / target).exists() and target != rel:
                    edges.add((rel, "pointer", target))

    for id_, places in defined.items():
        for p in set(places):
            edges.add((p, "defines", id_))
    for id_, places in referenced.items():
        for p in places:
            if id_ not in explicit_map.get(p, ()):  # requires / depends と重複させない
                edges.add((p, "references", id_))

    files = {e[0] for e in edges} | {e[2] for e in edges if "/" in e[2] or e[2].endswith(".md")}
    ids = {e[2] for e in edges if ID_RE.fullmatch(e[2])}
    return edges, files, ids


def neighbors(edges, node: str, hops: int) -> set[str]:
    """無向 BFS で node から hops 以内のノード集合を返す。"""
    adj: dict[str, set[str]] = defaultdict(set)
    for s, _, d in edges:
        adj[s].add(d)
        adj[d].add(s)
    seen = {node}
    frontier = {node}
    for _ in range(hops):
        frontier = {n for f in frontier for n in adj[f]} - seen
        seen |= frontier
    return seen


def to_mermaid(edges) -> str:
    def nid(name: str) -> str:
        return re.sub(r"[^0-9A-Za-z_]", "_", name)

    lines = ["flowchart LR"]
    names = {n for e in edges for n in (e[0], e[2])}
    for n in sorted(names):
        shape = f'{nid(n)}(["{n}"])' if ID_RE.fullmatch(n) else f'{nid(n)}["{n}"]'
        lines.append(f"    {shape}")
    for s, kind, d in sorted(edges):
        arrow = "-->" if kind in ("defines", "pointer") else "-.->"
        lines.append(f"    {nid(s)} {arrow}|{kind}| {nid(d)}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Tri-SSD ドキュメント依存グラフを抽出する")
    ap.add_argument("--docs", default="docs", help="検索対象ディレクトリ（既定: docs）")
    ap.add_argument("--format", choices=("edges", "mermaid", "json"), default="edges")
    ap.add_argument("--focus", help="ID（REQ/PH/F）または docs 相対パスで絞り込む")
    ap.add_argument("--hops", type=int, default=2, help="--focus の近傍距離（既定: 2）")
    args = ap.parse_args()

    docs = Path(args.docs)
    if not docs.exists():
        print(f"error: {docs} が見つかりません", file=sys.stderr)
        return 2

    edges, files, ids = build_graph(docs)

    if args.focus:
        focus = args.focus if ID_RE.fullmatch(args.focus) else Path(args.focus).as_posix()
        known = files | ids
        if focus not in known:
            print(f"error: '{args.focus}' はグラフに存在しません", file=sys.stderr)
            return 2
        keep = neighbors(edges, focus, args.hops)
        edges = {e for e in edges if e[0] in keep and e[2] in keep}
        read_set = sorted(n for n in keep if n in files and not ID_RE.fullmatch(n))
        print(f"# focus: {focus}（{args.hops} hops）")
        print("\n## 読むべき文書")
        for f in read_set:
            print(f"- {f}")
        print("\n## 関連エッジ")

    if args.format == "json":
        payload = {
            "edges": [{"src": s, "kind": k, "dst": d} for s, k, d in sorted(edges)],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=1))
    elif args.format == "mermaid":
        print(to_mermaid(edges))
    else:
        for s, kind, d in sorted(edges):
            print(f"{s} -{kind}-> {d}")
        if not args.focus:
            print(f"\n文書 {len([f for f in files if not ID_RE.fullmatch(f)])} 件 / "
                  f"ID {len(ids)} 件 / エッジ {len(edges)} 件")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
