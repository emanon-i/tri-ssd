---
id: T-0003
status: done
refs: [REQ-0002]
code: [tests/eval_context.py]
created: 2026-10-16
closed: 2026-10-16
---
# T-0003 Context efficiency evaluation

## 目的の状態

複数の検証ケースで全文読み込みと context の取得量・取得率・混入率・時間を実測し evaluation.md に記録している。

## 受け入れ条件

- [x] AC1: 評価スクリプトが複数ケースのトークン量・取得率・混入率・時間を実測して表にする
  - 検証: `python3 tests/eval_context.py --check`
- [x] AC2: 実測結果と考察（未達を含む）が evaluation.md にある
  - 検証: 手動: evaluation.md の数値が評価スクリプトの最新出力と一致することを確認

## 検証記録

- 2026-10-16 22:49 AC1 PASS `python3 tests/eval_context.py --check` → exit 0 「✓ docs/evaluation.md は最新の実測と一致」 tree=3f5d8c69b302
- 2026-10-16 22:49 AC2 PASS 手動: evaluation.md の結果表は --check で最新実測と一致。考察の数値（削減65〜92%・混入0〜14%・取得率60〜100%・Docs17倍でcontext1.3倍）を表と照合 tree=3f5d8c69b302
