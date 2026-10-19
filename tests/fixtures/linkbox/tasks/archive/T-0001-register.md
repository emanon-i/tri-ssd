---
id: T-0001
status: done
refs: [REQ-0001]
closed: 2026-08-10
---
# T-0001 ブックマーク登録

## 受け入れ条件

- [x] AC1: URL を POST すると 201 が返る
  - 検証: `python3 -m unittest tests.test_bookmarks`

## 検証記録

- 2026-08-10 10:00 AC1 PASS `python3 -m unittest tests.test_bookmarks` → exit 0 「OK」 tree=none
