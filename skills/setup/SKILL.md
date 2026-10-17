---
description: プロジェクトに Tri-SSD を導入する。新規プロジェクトの初期化、既存プロジェクトへの導入（既存コード・文書から Goal と最小限の Docs を起こす）、旧 Tri-SSD（L0〜L3 構成）からの移行を行う。
when_to_use: Tri-SSD を始めたい・導入したい・セットアップして・初期化して・既存プロジェクトに入れたい・旧バージョンの Tri-SSD から移行したい・l1_requirements や l3_phases がある、と言われたとき。英語では set up Tri-SSD / adopt / migrate from v5。導入済みのプロジェクトでの作業は task・docs を使う。
argument-hint: "[new | adopt | migrate]"
allowed-tools: Read, Edit, Write, Glob, Grep, Bash
---

# Tri-SSD を導入する

<tri_ssd_context>
Tri-SSD: Goal（docs/goal.md）・Docs（docs/ のあるべき状態）・Tasks（docs/tasks/ 差分を解消する検証可能な作業。作業メモも Task の中）・引き継ぎ（docs/notes/handoff.md）・CHANGELOG（意味のある変更の履歴）。常に守る規則はエージェントが常に読む指示ファイル（CLAUDE.md・AGENTS.md）に置く。
決定的処理は CLI `python3 "${CLAUDE_SKILL_DIR}/../../scripts/tri.py"`（以下 `tri`）で行う。文書を開く前に `tri context` で必要なセクションだけを取得する。
置き場・寿命の判断に迷ったら `${CLAUDE_SKILL_DIR}/../../docs/knowledge-model.md` を読むこと。
</tri_ssd_context>

<avoid_over_engineering>
- 最初から文書を揃えない。Goal と、最初の Task に必要な Docs だけを書く
- 既存コードの詳細を Docs に書き写さない（コードが正）。Docs に書くのは守るべき状態・判断・契約だけ
- 既存の文書を消さない。移行は既定でドライランから始める
</avoid_over_engineering>

## 状況の判定

| 状態 | 手順 |
|---|---|
| `docs/l1_requirements/` 等（旧 Tri-SSD）がある | 移行 |
| コードや文書が既にある | 既存プロジェクトへの導入 |
| 空に近い | 新規 |

## 新規

1. `tri init --name "<名前>"` — `docs/goal.md`・`docs/tasks/`・`docs/notes/`・`CHANGELOG.md`・`.tri-ssd/`（git 管理外）を作る。既存ファイルは上書きしない
2. ユーザーに目的と成功状態を聞き、`docs/goal.md` を書く（docs スキルの「Goal を書く・直すとき」）
3. 最初に作るものの要求・構成を Docs に書き、task スキルで最初の Task を作る

## 既存プロジェクトへの導入

1. `tri init`。既存の `docs/*.md` はそのまま Docs として扱われる
2. README・既存文書・コード構成から Goal の案を作り、ユーザーに確認して `docs/goal.md` を書く
3. `tri check` で既存文書の参照切れ・履歴汚染・重複を確認する。修正は一度に全部やらず、触る文書から直す
4. これから変更する範囲についてだけ、守るべき状態を Docs に書き（要求は `## REQ-nnnn` 見出し、構成文書は frontmatter `code:`）、Task を作る

## 旧 Tri-SSD（v5 以前）からの移行

1. `tri migrate` — ドライラン。移動・変換の計画を表示する
2. ユーザーに計画を見せて了承を得てから `tri migrate --apply`

| 旧 | 新 |
|---|---|
| `docs/l1_requirements/vision.md` | `docs/goal.md`（REQ はそのまま有効） |
| `docs/l2_foundation/**` | `docs/design/**` |
| `docs/l3_phases/PH-*.md`（フォルダ形式は1ファイルに統合） | `docs/tasks/`（`status`: planned→open, in_progress→active。done は `_done/`） |
| `docs/l3_phases/_archive/**` | `docs/tasks/_done/**` |
| `docs/l0_ideas/**` | `docs/notes/ideas/**`（移行時に一度だけ見直し、Task・Docs にするか削除する） |
| `<!-- TODO: 要確認 -->`・`（未確認…）` | `（未確定）`・`（未検証）` |

3. 移行後の仕上げ:
   - `tri check` のエラーを直す（相対リンクのずれ等）
   - `docs/goal.md` が大きい（size 警告）なら、REQ の節を `docs/requirements.md` へ移し、Goal には目的・成功状態・原則・やらないことだけを残す
   - 進行中の PH Task の AC に `検証:` コマンドを書く（旧形式の「テスト」等は手動扱いになる）
   - L2 にあった「設計判断の記録」の経緯部分は ADR へ移す
4. `tri log Changed "Tri-SSD v6 の構成へ移行"`

## フック

プラグインはフックを登録する（`hooks/hooks.json`）。Tri-SSD プロジェクト以外や Python が見つからない環境では何もしない（Skill の手順だけで全機能が使える）。

- セッション開始時: `tri status` の要約を文脈に入れる
- `docs/` の Markdown を編集した直後: その文書への検査指摘を返す
- `docs/` の文書を読んだとき: 参照を `.tri-ssd/reads.log` に記録する（Task 完了時の「書かれていない依存の候補」に使う）

## 完了後の案内

- 作成・移動したファイルと `tri check` の結果
- 次の一手: Goal の記入 → 最初の Task（task スキル）

## エラーケース

| ケース | 対応 |
|---|---|
| `python3` が無い | `python` / `py` で同じコマンドを実行する（Python 3.9 以上） |
| 移行で `_done/` に同名がある | 手動で名前を変えてから再実行する |
| `docs/` が別用途（生成された API 文書等）で使われている | 生成物のディレクトリを `docs/` 外へ移すか、そのまま Docs として扱われることをユーザーに確認する |
