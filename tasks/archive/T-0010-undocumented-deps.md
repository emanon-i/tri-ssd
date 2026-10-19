---
id: T-0010
status: done
refs: [REQ-0002, REQ-0007, docs/architecture.md#書かれていない依存の候補]
code: [scripts/trissd/discover.py, hooks/hooks.json]
created: 2026-10-17
started: 2026-10-17 06:54:11
base: 30a85827824f
closed: 2026-10-17
---
# T-0010 Undocumented dependency discovery and resilient hooks

## 目的の状態

Task 完了時に context 外で変更・参照した Docs が候補として示され、フックは Python が無い環境で何もしない。

## 受け入れ条件

- [x] AC1: context に入らなかったが Task の間に差分のあるコードを記述する節・参照した節が、close 時に候補として出る。context で足りた Task では何も出ない
  - 検証: `python3 -m unittest discover -s tests -p test_tasks.py -k DiscoverTest`
- [x] AC2: フックのコマンドが python3・python・Python なしの3環境で終了コード 0 になり、Python があれば出力が得られる
  - 検証: 手動: hooks.json の SessionStart コマンドを PATH を変えた /bin/sh で3通り実行して確認

## 検証記録

- 2026-10-17 06:54 AC1 PASS `python3 -m unittest discover -s tests -p test_tasks.py -k DiscoverTest` → exit 0 「OK」 tree=7baaebc1afb1
- 2026-10-17 06:54 AC2 PASS 手動: hooks.json の SessionStart コマンドを /bin/sh で実行: python3 あり→状況を出力・exit 0、python のみ（PATH=/tmp/nopy）→状 tree=7baaebc1afb1
  況を出力・exit 0、Python なし（PATH=/nonexistent）→出力なし・exit 0
