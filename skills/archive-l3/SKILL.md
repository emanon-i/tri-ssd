---
description: 実装が完了した L3 フェーズドキュメントを docs/l3_phases/_archive/ へ移動し、作業ディレクトリをクリーンに保つ。同梱スクリプトで決定的に移動。
when_to_use: フェーズの実装が完了してアーカイブしたい・archive したいと言われたとき。gen-code の完了後。
argument-hint: "[PH-xxxx|パス] - アーカイブ対象（省略時は全フェーズ確認）"
allowed-tools: Read, Glob, Grep, Bash
---

# L3 フェーズアーカイブコマンド

<tri_ssd_context>
Tri-SSD（Tri-Layer Slice Spec Driven）はAI/LLMコードエージェントを前提とした仕様駆動開発。

レイヤー構造:
- L0: アイディア・ラフメモ（docs/l0_ideas/）- 任意
- L1: 要件（docs/l1_requirements/vision.md）
- L2: システム構成（docs/l2_foundation/foundation.md）
- L3: フェーズ（docs/l3_phases/PH-xxx.md）- 機能+受け入れ条件

ID形式: PREFIX-nnnn（REQ, PH, F）
</tri_ssd_context>

## 概要

実装が完了して不要になったL3フェーズドキュメントを `_archive/` に移動する。
L3ドキュメントは実装完了後に陳腐化するため、アクティブな作業ディレクトリをクリーンに保つ。

## アーカイブ時の原則

<avoid_over_engineering>
- アーカイブは単純なファイル移動。メタデータの追加や要約生成はしない
- アーカイブ済みファイルを戻したい場合は手動で `_archive/` から移動すれば十分
- アーカイブ前のレビューや確認チェックは不要（ユーザーの判断を尊重）
</avoid_over_engineering>

## 引数

- `$ARGUMENTS` (省略可): アーカイブ対象
  - **PH-ID**: `PH-0001` → 指定フェーズをアーカイブ
  - **ファイルパス**: `docs/l3_phases/PH-0001_mvp.md` → 直接指定
  - **省略**: `docs/l3_phases/` 内の全フェーズを列挙し、ユーザーに選択させる

### 使用例

```
/archive-l3 PH-0001                         # 指定フェーズをアーカイブ
/archive-l3 docs/l3_phases/PH-0001_mvp.md   # パスで直接指定
/archive-l3                                  # 全フェーズを列挙して選択
```

## 前提処理

1. `$ARGUMENTS` で指定された対象を特定
   - ID指定: Glob で `docs/l3_phases/PH-*` を検索（`_archive/` は除外）
   - パス指定: 直接参照
   - 省略時: `docs/l3_phases/` 内の `PH-*` を全て列挙
2. 対象がアクティブ（`_archive/` 外）であることを確認

---

## 実行

同梱スクリプトで決定的に移動する:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/archive.py" --list        # アーカイブ可能なフェーズを一覧
python3 "${CLAUDE_SKILL_DIR}/scripts/archive.py" PH-0001       # 指定フェーズをアーカイブ
```

引数なしのときは、まず `--list` で一覧をユーザーに提示し、選択を受けてから対象を指定して実行する。`python3` が無ければ `python` / `py`。スクリプトが使えない場合のみ、下記「処理手順（フォールバック）」に従う。

## 処理手順（フォールバック）

### Step 1: 対象ファイル特定

**引数ありの場合**:
1. 対象ファイル/フォルダを特定
2. 存在確認

**引数なしの場合**:
1. `docs/l3_phases/` 内のアクティブなフェーズを列挙（`_archive/` 配下を除く）
2. 一覧をユーザーに提示

```markdown
## アーカイブ可能なフェーズ

| # | フェーズ | 形式 |
|---|---------|------|
| 1 | PH-0001_mvp.md | インライン |
| 2 | PH-0002_beta/ | フォルダ |

どのフェーズをアーカイブしますか？（番号、ID、または「all」）
```

3. ユーザーの選択に基づいて対象を決定

### Step 2: アーカイブディレクトリ確認

```bash
mkdir -p docs/l3_phases/_archive
```

### Step 3: ファイル移動

```bash
# インライン形式
mv docs/l3_phases/PH-xxxx_name.md docs/l3_phases/_archive/

# フォルダ形式
mv docs/l3_phases/PH-xxxx_name/ docs/l3_phases/_archive/
```

### Step 4: 完了報告

---

## 完了後の案内

```markdown
# アーカイブ完了

**移動先**: docs/l3_phases/_archive/

## アーカイブしたフェーズ
- PH-0001_mvp.md

## 残りのアクティブフェーズ
- PH-0002_beta.md
- PH-0003_release.md

**元に戻す場合**: `_archive/` から `docs/l3_phases/` に手動で移動してください
```

---

## エラーケース

| ケース | 対応 |
|--------|------|
| ファイルが見つからない | エラー: 「指定されたフェーズが見つかりません」 |
| 既にアーカイブ済み | 警告: 「既に `_archive/` にあります」 |
| `_archive/` に同名が存在 | エラー: 「同名ファイルが `_archive/` に存在します。手動で確認してください」 |
| アクティブなフェーズがない | 情報: 「アーカイブ可能なフェーズがありません」 |
