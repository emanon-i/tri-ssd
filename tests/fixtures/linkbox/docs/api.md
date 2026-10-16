---
code: [src/api/]
---
# HTTP API

すべてのエンドポイントは認証必須（[認証](security.md#認証)）。エラー形式は [エラー処理方針](architecture.md#エラー処理方針) に従う。

## ブックマーク

### POST /bookmarks

REQ-0001。`{url, tags?, memo?}` を受け取り 201 を返す。タイトル取得は非同期に行い、取得前は URL をタイトルとする。
同一 URL が既にあれば 409 と既存の ID を返す。

### PATCH /bookmarks/{id}

タグ・メモ・タイトルを更新する。REQ-0002 のタグ付け外しもここで行う。

### DELETE /bookmarks/{id}

ゴミ箱へ移動する（REQ-0011）。`POST /bookmarks/{id}/restore` で復元する。

## 検索

### GET /search

`q`（全文）と `tags`（カンマ区切り）と `mode=and|or` を受け取る。REQ-0003 と REQ-0004。
結果は 50 件ずつのカーソルページング。

### GET /tags/suggest

`prefix` を受け取り、タグ候補を最大 10 件返す。

## 入出力

### POST /import

REQ-0005。multipart で HTML を受け取り、ジョブ ID を返す。取り込みは非同期で、`GET /import/{job}` で進捗を返す。
1 ファイル 20MB まで。解析できない行はスキップしてレポートに含める。

### GET /export

REQ-0006。`format=json|html`。全件をストリームで返す。
