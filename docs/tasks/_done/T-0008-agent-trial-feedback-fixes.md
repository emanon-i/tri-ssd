---
id: T-0008
status: done
refs: [REQ-0004, REQ-0005]
code: [scripts/trissd/]
created: 2026-10-16
closed: 2026-10-16
---
# T-0008 Agent trial feedback fixes

## 目的の状態

実エージェント試行で見つかった CLI の不具合（検証記録の行長・検証記録内の参照の扱い）が直り、テストで裏付けられている。

## 受け入れ条件

- [x] AC1: CLI が書く検証記録の各行が 200 文字以内に収まり、折り返しても証跡として読める
  - 検証: `python3 -m unittest discover -s tests -p test_tasks.py -k test_long_evidence_wraps`
- [x] AC2: Task の検証記録内の ID は参照切れの対象外で、本文の ID は対象のまま
  - 検証: `python3 -m unittest discover -s tests -p test_check.py -k test_evidence_is_history`
- [x] AC3: 既存の全テストが通る
  - 検証: `python3 -m unittest discover -s tests -p "test_*.py"`

## 検証記録

- 2026-10-16 22:47 AC1 PASS `python3 -m unittest discover -s tests -p test_tasks.py -k test_long_evidence_wraps` → exit 0 「OK」 tree=3f5d8c69b302
- 2026-10-16 22:47 AC2 PASS `python3 -m unittest discover -s tests -p test_check.py -k test_evidence_is_history` → exit 0 「OK」 tree=3f5d8c69b302
- 2026-10-16 22:47 AC3 PASS `python3 -m unittest discover -s tests -p "test_*.py"` → exit 0 「OK」 tree=3f5d8c69b302
