"""コンテキスト効率の実測（ブリーフ 12.2）。

各ケースについて「全文読み込み」と「context（または impact）」を比較する:
  - トークン量（推定。md.estimate_tokens）
  - 必要情報の取得率（required のうち選定されたセクションの割合）
  - 無関係な情報の混入率（required でも acceptable でもない選定トークンの割合）
  - 取得処理の時間（プロジェクト読み込み込み。5 回の中央値）
  - 欠落した必要情報

required / acceptable は、そのケースの作業者が判断・実装に必要とする情報を人手で判定した正解集合。
グラフで辿れない横断的な制約もあえて required に含める（取得機構の限界を隠さないため）。

    python3 tests/eval_context.py            # 表を出力
    python3 tests/eval_context.py --write    # docs/evaluation.md の結果表を更新
    python3 tests/eval_context.py --check    # docs/evaluation.md の表が最新の実測と一致するか検査
"""
from __future__ import annotations

import argparse
import re
import statistics
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
from trissd import md, resolve  # noqa: E402
from trissd.project import Project  # noqa: E402

LB = ROOT / "tests/fixtures/linkbox"
REQ = "docs/requirements.md#req-"

CASES = [
    {
        "id": "L1", "corpus": LB, "seeds": ["T-0005"], "what": "Task: タグ検索（AND/OR・補完）",
        "required": [f"{REQ}0004-タグ検索", "docs/search.md#タグ検索", "docs/search.md#性能予算",
                     "docs/api.md#get-search", "docs/api.md#get-tagssuggest", "docs/data.md#tag",
                     "docs/security.md#認可"],  # 横断制約: 全クエリを利用者 ID で絞る
        "acceptable": ["docs/goal.md*", "docs/search.md*", "docs/architecture.md*", "docs/requirements.md#要求",
                       "NOTES.md*", "docs/api.md#http-api", "docs/api.md#検索", "docs/ui.md#検索の操作",
                       "docs/data.md#概念モデル", "docs/data.md#データ設計"],
    },
    {
        "id": "L2", "corpus": LB, "seeds": ["T-0006"], "what": "Task: ブラウザ HTML のインポート",
        "required": [f"{REQ}0005-インポート", "docs/api.md#post-import", "docs/architecture.md#エラー処理方針",
                     "docs/data.md#bookmark",          # 重複判定は正規化後の URL
                     "docs/security.md#入力の扱い"],   # 横断制約: javascript: URL を捨てる
        "acceptable": ["docs/goal.md*", "docs/architecture.md*", "docs/api.md#http-api", "docs/api.md#入出力",
                       "docs/requirements.md#要求", "NOTES.md*", "docs/data.md#整合性",
                       f"{REQ}0002-タグ付け"],
    },
    {
        "id": "L3", "corpus": LB, "seeds": ["T-0007"], "what": "Task: ゴミ箱の自動削除",
        "required": [f"{REQ}0011-削除とゴミ箱", "docs/data.md#ライフサイクル", "docs/data.md#整合性",
                     "docs/operations.md#ゴミ箱の物理削除"],
        "acceptable": ["docs/goal.md*", "docs/requirements.md#要求", "docs/api.md#delete-bookmarksid",
                       "docs/operations.md#定期ジョブ", "docs/architecture.md*", "docs/data.md#データ設計"],
    },
    {
        "id": "L4", "corpus": LB, "seeds": ["src/sync/merge.py"], "what": "コード起点: 同期のマージ処理を直す",
        "required": ["docs/sync.md#競合解決"],
        "acceptable": ["docs/goal.md*", "docs/sync.md*", "docs/architecture.md*", "docs/data.md#synclog"],
    },
    {
        "id": "L5", "corpus": LB, "query": "リンク切れ確認の再試行間隔を変えたい", "what": "依存不明: キーワード起点",
        "required": [f"{REQ}0009-リンク切れの検出", "docs/operations.md#リンク確認"],
        "acceptable": ["docs/goal.md*", "docs/requirements.md#要求", "docs/operations.md#定期ジョブ",
                       "docs/glossary.md*"],
    },
    {
        "id": "S1", "corpus": ROOT, "seeds": ["REQ-0005"], "what": "自己適用: 完了ゲートの仕様を変える",
        "required": ["docs/requirements.md#req-0005-検証証跡による完了判定", "docs/architecture.md#完了ゲート",
                     "docs/knowledge-model.md#task"],
        "acceptable": ["docs/goal.md*", "docs/requirements.md#要求", "docs/architecture.md*",
                       "docs/knowledge-model.md*", "docs/writing-rules.md#機械契約"],
    },
    {
        "id": "S2", "corpus": ROOT, "seeds": ["scripts/trissd/check.py"], "what": "自己適用: 検査ロジックを直す",
        "required": ["docs/architecture.md#検査"],
        "acceptable": ["docs/goal.md*", "docs/architecture.md*", "docs/requirements.md#req-0004-整合性と衛生の検査",
                       "docs/writing-rules.md*", "docs/knowledge-model.md*"],
    },
]


def match(key: str, patterns: list[str]) -> bool:
    return any(key.startswith(p[:-1]) if p.endswith("*") else key == p for p in patterns)


def baseline(p: Project) -> tuple[int, int]:
    """(Goal+Docs 全文, Goal+Docs+進行中Task+Notes 全文) の推定トークン。"""
    docs = sum(md.estimate_tokens(d.text) for d in p.docs.values() if d.kind in ("goal", "doc"))
    work = docs + sum(md.estimate_tokens(d.text) for d in p.docs.values() if d.kind in ("task", "note"))
    return docs, work


def load(corpus: Path) -> Project:
    p = Project(corpus)
    # 評価結果の文書自体は計測対象から外す（書き込むたびに数値が変わるのを防ぐ）
    report = p.docs.pop("docs/evaluation.md", None)
    if report:
        for s in report.sections:
            p.sections.pop(s.key, None)
        p.edges = [e for e in p.edges if not e.src.startswith("docs/evaluation.md")]
    return p


def run_case(c: dict) -> dict:
    p = load(c["corpus"])
    r = resolve.context(p, c.get("seeds", []), query=c.get("query"))
    times = []
    for _ in range(5):
        t0 = time.perf_counter()
        resolve.context(load(c["corpus"]), c.get("seeds", []), query=c.get("query"))
        times.append((time.perf_counter() - t0) * 1000)
    sel = {i.key: i.tokens for i in r.selected}
    seed_files = {k.split("#")[0] for s in c.get("seeds", []) for k in (resolve.seed_keys(p, s) or [])}
    judged = {k: t for k, t in sel.items() if k.split("#")[0] not in seed_files}  # 起点そのものは評価対象外
    req = c["required"]
    hit = [k for k in req if k in sel]
    noise = sum(t for k, t in judged.items() if not match(k, req) and not match(k, c["acceptable"]))
    docs, work = baseline(p)
    return {
        "id": c["id"], "what": c["what"], "docs": docs, "work": work, "used": r.used,
        "ratio": r.used / work, "recall": len(hit) / len(req), "noise": noise / max(sum(judged.values()), 1),
        "ms": statistics.median(times), "missed": [k for k in req if k not in sel],
        "weak": [k for k in req if k not in sel and k in {i.key for i in r.weak}],
    }


def growth(cycles: int = 40) -> list[dict]:
    """長期運用で Docs が増えても context の量が一定に保たれるか（simulate.py の生成物で計測）。"""
    import simulate
    with tempfile.TemporaryDirectory() as tmp:
        rows, _ = simulate.run(cycles, "disciplined", Path(tmp) / "memo")
    return [r for r in rows if r["cycle"] in (1, 10, 20, 30, 40)]


def table(results: list[dict]) -> str:
    lines = ["| ケース | 内容 | 全文（Goal+Docs / +Task・NOTES.md） | context | 削減 | 取得率 | 混入率 | 欠落（未選定の必要情報） |",
             "|---|---|---|---|---|---|---|---|"]
    for r in results:
        missed = "・".join(f"`{m}`" + ("（弱い候補に列挙）" if m in r["weak"] else "") for m in r["missed"]) or "なし"
        lines.append(f"| {r['id']} | {r['what']} | {r['docs']} / {r['work']} | {r['used']} | {1 - r['ratio']:.0%} | "
                     f"{r['recall']:.0%} | {r['noise']:.0%} | {missed} |")
    return "\n".join(lines)


def growth_table(rows: list[dict]) -> str:
    lines = ["| サイクル | Goal+Docs | context（最新 Task） | 検査エラー | 一時情報（NOTES.md＋メモ） |", "|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['cycle']} | {r['docs_tokens']} | {r['context_tokens']} | {r['errors']} | {r['notes_tokens']} |")
    return "\n".join(lines)


BEGIN, END = "<!-- eval:begin -->", "<!-- eval:end -->"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    results = [run_case(c) for c in CASES]
    body = table(results) + "\n\n" + growth_table(growth())
    timing = " / ".join(f"{r['id']} {r['ms']:.0f}ms" for r in results)
    print(body)
    print(f"\n取得時間（中央値、読み込み込み）: {timing}")
    target = ROOT / "docs/evaluation.md"
    if a.write:
        text = target.read_text(encoding="utf-8")
        text = re.sub(f"{re.escape(BEGIN)}.*?{re.escape(END)}", f"{BEGIN}\n{body}\n{END}", text, flags=re.S)
        target.write_text(text, encoding="utf-8")
        print(f"\n更新: {target.relative_to(ROOT)}")
    if a.check:
        text = target.read_text(encoding="utf-8") if target.exists() else ""
        m = re.search(f"{re.escape(BEGIN)}\n(.*?)\n{re.escape(END)}", text, flags=re.S)
        if not m or m.group(1) != body:
            print("\n❌ docs/evaluation.md の結果表が最新の実測と一致しません（--write で更新）")
            return 1
        print("\n✓ docs/evaluation.md は最新の実測と一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
