---
id: T-0009
status: done
refs: [REQ-0004]
code: [scripts/trissd/check.py]
created: 2026-10-16
closed: 2026-10-16
---
# T-0009 Growth check ignores new files

## 目的の状態

check --changed の追記偏重の警告が既存文書だけを対象にし、新規文書では出ない。

## 受け入れ条件

- [x] AC1: 既存文書への大量追記は警告し、新規文書は警告しない
  - 検証: `python3 -m unittest discover -s tests -p test_check.py -k test_changed_changelog_reminder_and_growth`
- [x] AC2: このリポジトリの作業差分に対する check --changed が警告 0
  - 検証: `python3 scripts/tri.py check --changed HEAD --strict`

## 検証記録

- 2026-10-16 22:50 AC1 PASS `python3 -m unittest discover -s tests -p test_check.py -k test_changed_changelog_reminder_and_growt tree=c8b465279150
  h` → exit 0 「OK」
- 2026-10-16 22:50 AC2 PASS `python3 scripts/tri.py check --changed HEAD --strict` → exit 0 「検査完了: エラー 0 / 警告 0」 tree=c8b465279150
