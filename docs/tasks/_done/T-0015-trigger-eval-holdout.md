---
id: T-0015
status: done
refs: [docs/skill-evaluation.md]
code: [evals/, skills/]
created: 2026-10-17
base: 375688ba4d5c
closed: 2026-10-17
---
# T-0015 発火評価を学習・検証の分割で測り直す

## 目的の状態

3 スキルの振り分け（どのスキルが呼ばれるか）を、固定した学習・検証の分割を持つ約 40 件の依頼で測り、検証側の精度・再現率を信頼区間付きで skill-evaluation.md に載せている。テストの文言を写した説明文が無い

## 受け入れ条件

- AC1: 発火評価の 40 件から 40 ケースが生成され、学習 24・検証 16 の分割が固定されている
  - 検証: `python3 evals/trigger/build.py && test $(ls evals/trigger/cases | wc -l) -eq 40 && test $(grep -c '"split": "validation"' evals/trigger/queries.json) -eq 16`
- AC2: スキルの説明文に評価の依頼文を写した語が無い
  - 検証: `test -z "$(grep -rn '20 件' skills/)"`
- AC3: 検証側の精度・再現率（信頼区間付き）と、採点を固定した成果のケースごとの差（信頼区間付き）が docs/skill-evaluation.md に実測値で載っている
  - 検証: 手動: claude plugin eval の結果（aggregate-result）と summarize.py の出力を表と突き合わせる

## メモ

- 発火評価は両方の版で上限近く（修正前 39/40、現在 40/40）で、版の差は測れなかった。飽和した評価は回帰の評価として使う
- 成果の held-out では差が手順の成果物（CHANGELOG・証跡付き Task・Goal）だけから出た。コードの正しさはスキルなしでも同じだった
- 導入で Goal に「Python 標準ライブラリだけで動く」と書いた回が 3 回中 1 回。1 回のため手順は足していない

## 検証記録

- 2026-10-17 11:45 AC1 PASS `python3 evals/trigger/build.py && test $(ls evals/trigger/cases | wc -l) -eq 40 && test $(grep -c ' tree=d7f6d18cc9c9
  "split": "validation"' evals/trigger/queries.json) -eq 16` → exit 0 「生成: /home/user/tri-ssd/evals/tr
  igger/cases」
- 2026-10-17 11:45 AC2 PASS `test -z "$(grep -rn '20 件' skills/)"` → exit 0 tree=d7f6d18cc9c9
- 2026-10-17 11:45 AC3 PASS 手動: 発火: 修正前 学習23/24・検証16/16、現在 学習24/24・検証16/16（summarize.py 出力と一致）。成果 held-out: 差の平均 +0.37（95%CI 0.1 tree=d7f6d18cc9c9
  1〜0.63、6 ケース）、pass^3 あり 5/6・なし 0/6（aggregate-result から再計算して一致）
