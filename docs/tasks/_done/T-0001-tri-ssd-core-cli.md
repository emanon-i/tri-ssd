---
id: T-0001
status: done
refs: [REQ-0001, REQ-0002, REQ-0003, REQ-0004, REQ-0005, REQ-0006, REQ-0009]
code: [scripts/]
created: 2026-10-16
closed: 2026-10-16
---
# T-0001 Tri-SSD Core CLI

## 目的の状態

architecture.md の知識グラフ・取得・逆引き・検査・完了ゲートが CLI として動き、自動テストで裏付けられている。

## 受け入れ条件

- [x] AC1: 解析・グラフ・取得・逆引き・検査・Task・Note・CHANGELOG・移行の自動テストがすべて通る
  - 検証: `python3 -m unittest discover -s tests -p "test_*.py"`
- [x] AC2: 長期運用シミュレーションで、規律ある運用は健全性を保ち、不注意な運用は検出される
  - 検証: `python3 -m unittest discover -s tests -p test_simulation.py`
- [x] AC3: このリポジトリ自身の知識に検査エラーがない
  - 検証: `python3 scripts/tri.py check`

## 検証記録

- 2026-10-16 22:25 AC1 PASS `python3 -m unittest discover -s tests -p "test_*.py"` → exit 0 「OK」 tree=ea0e78a21be3
- 2026-10-16 22:25 AC2 FAIL `python3 -m unittest discover -s tests -p test_simulation.py` → exit 1 「FAILED (errors=1)」 tree=ea0e78a21be3
- 2026-10-16 22:25 AC3 FAIL `python3 scripts/tri.py check` → exit 1 「検査完了: エラー 1 / 警告 10」 tree=ea0e78a21be3
- 2026-10-16 22:46 AC1 PASS `python3 -m unittest discover -s tests -p "test_*.py"` → exit 0 「OK」 tree=cfb20df25730
- 2026-10-16 22:46 AC2 PASS `python3 -m unittest discover -s tests -p test_simulation.py` → exit 0 「OK」 tree=cfb20df25730
- 2026-10-16 22:46 AC3 PASS `python3 scripts/tri.py check` → exit 0 「検査完了: エラー 0 / 警告 0」 tree=cfb20df25730
