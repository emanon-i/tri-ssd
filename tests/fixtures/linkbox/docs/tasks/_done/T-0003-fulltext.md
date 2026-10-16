---
id: T-0003
status: done
refs: [REQ-0003]
closed: 2026-09-01
---
# T-0003 全文検索

## 受け入れ条件

- [x] AC1: 日本語の部分一致で見つかる
  - 検証: `python3 -m unittest tests.test_search`

## 検証記録

- 2026-09-01 10:00 AC1 PASS `python3 -m unittest tests.test_search` → exit 0 「OK」 tree=none
