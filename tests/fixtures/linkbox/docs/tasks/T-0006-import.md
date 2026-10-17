---
id: T-0006
status: open
refs: [REQ-0005]
code: [src/api/import.py]
created: 2026-10-01
---
# T-0006 ブラウザ HTML のインポート

## 目的の状態

api.md「POST /import」のとおり、Netscape Bookmark File を非同期に取り込める。

## 受け入れ条件

- AC1: フォルダ階層がタグに変換される
  - 検証: `python3 -m unittest tests.test_import`
- AC2: 重複 URL は取り込まれずレポートに件数が出る
  - 検証: `python3 -m unittest tests.test_import`

## 検証記録
