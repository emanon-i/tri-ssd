---
id: T-0012
status: done
refs: [REQ-0001, REQ-0006]
code: [scripts/, skills/, hooks/, templates/]
created: 2026-10-17
base: 8261c45758fa
closed: 2026-10-17
---
# T-0012 メモの置き場を Task 内に移し未使用の機能を削除

## 目的の状態

作業メモは Task と一緒に退場し、引き継ぎは上書きの1つだけ。効果を示せなかった機能（ノートの整理・依存候補・着手時点との比較・graph・JSON 出力・note スキル）が無く、書式の正がテンプレートファイルにある。

## 受け入れ条件

- [x] AC1: 新しい Task に `## メモ` 節があり、引き継ぎは上書きで1つに保たれ、個人用は git 管理外に置ける
  - 検証: `python3 -m unittest discover -s tests -p "test_[lt]*.py" -k HandoffTest -k test_template_has_memo_section`
- [x] AC2: 長期運用で Docs が増えても一時情報（引き継ぎとメモ）が増えない
  - 検証: `python3 -m unittest discover -s tests -p test_simulation.py`
- [x] AC3: 廃止した機能が CLI とフックに残っていない
  - 検証: `! python3 scripts/tri.py note add x 2>/dev/null && ! python3 scripts/tri.py graph 2>/dev/null && ! python3 scripts/tri.py track --hook 2>/dev/null && ! grep -q track hooks/hooks.json && ! test -e skills/note`

## メモ

- 評価の時間が 5〜15ms から 16〜37ms に増えた。コード内 ID の git grep（毎回の読み込み）が効いている可能性。体感に影響する規模ではないので、今回は扱わない

## 判断

取り締まる仕組み（範囲の宣言の義務化・量の上限・途中変更の可視化）を足す案はやめた。結果への対策で、管理のための管理を増やすため。置き場を寿命に合わせれば溜まる場所そのものが無くなる（ADR-0002 参照: docs/adr/0002-places-with-lifetimes.md）。

## 検証記録

- 2026-10-17 09:12 AC1 PASS `python3 -m unittest discover -s tests -p "test_[lt]*.py" -k HandoffTest -k test_template_has_memo_s tree=a3872df61986
  ection` → exit 0 「OK」
- 2026-10-17 09:12 AC2 PASS `python3 -m unittest discover -s tests -p test_simulation.py` → exit 0 「OK」 tree=a3872df61986
- 2026-10-17 09:12 AC3 PASS `! python3 scripts/tri.py note add x 2>/dev/null && ! python3 scripts/tri.py graph 2>/dev/null && ! tree=a3872df61986
  python3 scripts/tri.py track --hook 2>/dev/null && ! grep -q track hooks/hooks.json && ! test -e ski
  lls/note` → exit 0

