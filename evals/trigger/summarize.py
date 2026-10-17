"""発火評価の結果（claude plugin eval --json の出力）を、依頼ごとの発火率とスキルごとの精度・再現率にまとめる。

    python3 evals/trigger/summarize.py result.json [--split validation]

依頼ごとに各スキルが呼ばれた割合を求め、0.5 以上を「呼ばれた」とする（skill-creator と同じ基準）。
単位は依頼（実行ではない）。割合には Wilson の 95% 信頼区間を付ける。
"""
import argparse
import json
import math
from pathlib import Path

SKILLS = ("task", "docs", "setup")


def wilson(k: int, n: int) -> str:
    if n == 0:
        return "—"
    z, p = 1.96, k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return f"{k}/{n}（{max(0, c - h):.2f}〜{min(1, c + h):.2f}）"


def rates(result: dict) -> dict:
    """case 名 → スキルごとの発火率。grader の合否から Skill が呼ばれたかを読む。"""
    out = {}
    for case in result["cases"]:
        runs = case["arms"]["with"]
        r = {}
        for s in SKILLS:
            hits = 0
            for run in runs:
                for g in run["graders"]:
                    if g["name"] == f"fires-{s}":
                        hits += g["passed"]
                    elif g["name"] == f"not-{s}":
                        hits += not g["passed"]
            r[s] = hits / len(runs) if runs else 0.0
        out[case["name"].removeprefix("trigger-")] = r
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("result", nargs="+")
    ap.add_argument("--split")
    a = ap.parse_args()
    queries = {q["id"]: q for q in json.loads((Path(__file__).parent / "queries.json").read_text(encoding="utf-8"))}
    got = {}
    for f in a.result:
        got.update(rates(json.loads(Path(f).read_text(encoding="utf-8"))))
    ids = [i for i in queries if i in got and (not a.split or queries[i]["split"] == a.split)]
    correct = 0
    print("| 依頼 | 期待 | task | docs | setup |\n|---|---|---|---|---|")
    for i in ids:
        q, r = queries[i], got[i]
        fired = {s for s in SKILLS if r[s] >= 0.5}
        ok = fired == ({q["expect"]} if q["expect"] != "none" else set())
        correct += ok
        mark = "" if ok else " ✗"
        print(f"| {i}{mark} | {q['expect']} | " + " | ".join(f"{r[s]:.2f}" for s in SKILLS) + " |")
    print(f"\n正しく振り分けた依頼: {wilson(correct, len(ids))}\n")
    print("| スキル | 再現率（呼ぶべき依頼で呼ばれた） | 精度（呼ばれたうち正しい） |\n|---|---|---|")
    for s in SKILLS:
        pos = [i for i in ids if queries[i]["expect"] == s]
        fired = [i for i in ids if got[i][s] >= 0.5]
        tp = sum(1 for i in fired if queries[i]["expect"] == s)
        print(f"| {s} | {wilson(tp, len(pos))} | {wilson(tp, len(fired))} |")


if __name__ == "__main__":
    main()
