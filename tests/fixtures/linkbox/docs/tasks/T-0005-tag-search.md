---
id: T-0005
status: active
refs: [REQ-0004, docs/search.md#タグ検索]
code: [src/search/]
created: 2026-09-20
---
# T-0005 タグ検索

## 目的の状態

search.md「タグ検索」の記述どおりに、複数タグの AND / OR 絞り込みと補完が動く。

## 受け入れ条件

- [x] AC1: AND 条件で全タグを持つブックマークだけが返る
  - 検証: `python3 -m unittest tests.test_search`
- [ ] AC2: 補完は前方一致で使用回数順に最大 10 件返る
  - 検証: 手動: タグ 20 個の環境で入力 "py" の候補を確認

## 検証記録
