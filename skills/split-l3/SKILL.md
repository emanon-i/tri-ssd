---
description: インライン1ファイルの L3 フェーズを、機能ごとのフォルダ構造（_phase.md + F-xxxx_*.md）に分割する。同梱スクリプトで決定的に変換。
when_to_use: フェーズを機能単位で分けて管理したい・チームで機能ごとに担当を分けたい・split したいと言われたとき。
argument-hint: <PH-ID | ファイルパス> - 分割対象（必須）
allowed-tools: Read, Write, Glob, Grep, Bash
---

# L3 フェーズ分割コマンド

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

インライン形式のL3フェーズファイルを、フォルダ構造（分離形式）に変換する。

**用途**:
- 慎重に進めたいフェーズを機能単位で管理
- チーム開発で機能ごとに担当を分ける
- 機能数が多いフェーズを整理

## 分割時の原則

<avoid_over_engineering>
- 機能が1〜2個しかないフェーズは分割する必要がない（警告は出さない）
- 分割後も `/merge-l3` で元に戻せる
- チェック状態（`[x]`）は保持する
</avoid_over_engineering>

## 引数

- `$ARGUMENTS`: 分割対象（必須）
  - PH-ID: `PH-0001`
  - ファイルパス: `docs/l3_phases/PH-xxx_name.md`

## 前提処理

1. `$ARGUMENTS` で指定された対象ファイルを特定・読み込む
   - ID指定: Glob で `docs/l3_phases/**/PH-*$ARGUMENTS*.md` を検索
   - パス指定: 直接読み込み
2. フォーマット検証（インライン形式であること）
   - フォルダが既に存在する場合はエラー

---

## 実行

同梱スクリプトで決定的に分割する（チェック状態 `[x]` を保持、`/merge-l3` と往復可能）:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/split.py" PH-0001
# パス指定も可: python3 "${CLAUDE_SKILL_DIR}/scripts/split.py" docs/l3_phases/PH-0001_mvp.md
```

`python3` が無ければ `python` / `py`。スクリプトが使えない場合のみ、下記「処理手順（フォールバック）」に従って手作業で分割する。

## 処理手順（フォールバック）

### Step 1: ファイル解析

入力ファイルから以下を抽出:
- タイトル（`# PH-xxx: [フェーズ名]`）
- 目的セクション
- 機能セクション（`### F-xxx` で始まる各ブロック）
- Exit Criteria セクション

### Step 2: フォルダ作成

```
docs/l3_phases/{元ファイル名から拡張子を除いたもの}/
```

例: `PH-0001_mvp.md` → `PH-0001_mvp/`

### Step 3: `_phase.md` 生成

フェーズ概要ファイルを作成:

```markdown
# PH-xxx: [フェーズ名]

## 目的
{元ファイルの「目的」セクション}

## 機能一覧
- F-xxx: [機能1]
- F-xxx: [機能2]
...

## Exit Criteria
{元ファイルの「Exit Criteria」セクション}
```

### Step 4: 各機能ファイル生成

機能ごとに独立ファイルを作成:

ファイル名: `F-xxx_[kebab-case-機能名].md`

```markdown
# F-xxx: [機能名]

**対応REQ**: REQ-xxx

{機能の概要説明}

## 受け入れ条件
- [ ] 条件1
- [x] 条件2（チェック済みは保持）
```

### Step 5: 元ファイル削除

分割完了後、元のインライン形式ファイルを削除。

---

## 出力フォーマット

### フォルダ構造

```
docs/l3_phases/PH-xxx_[phase-name]/
├── _phase.md           # フェーズ概要 + Exit Criteria
├── F-xxx_feature1.md   # 機能1
├── F-xxx_feature2.md   # 機能2
└── F-xxx_feature3.md   # 機能3
```

### `_phase.md` 形式

```markdown
# PH-xxx: [フェーズ名]

## 目的
このフェーズで達成すること

## 機能一覧
- F-xxx: [機能1]
- F-xxx: [機能2]

## Exit Criteria
- [ ] 全機能の受け入れ条件がパス
- [ ] 結合テストがパス
```

### `F-xxx_[name].md` 形式

```markdown
# F-xxx: [機能名]

**対応REQ**: REQ-xxx

[機能の概要説明]

## 受け入れ条件
- [ ] 条件1
- [ ] 条件2
```

---

## エラーケース

| ケース | 対応 |
|--------|------|
| ファイルが見つからない | エラー: 「指定されたファイルが見つかりません」 |
| 既にフォルダ形式 | エラー: 「既に分離形式です。変換不要です」 |
| フォルダが既に存在 | エラー: 「同名フォルダが存在します。手動で確認してください」 |
| 機能セクションがない | エラー: 「機能セクション（### F-xxx）が見つかりません」 |

---

## 完了後の案内

```markdown
# 分割完了

**入力**: docs/l3_phases/PH-0001_mvp.md
**出力**: docs/l3_phases/PH-0001_mvp/

## 生成ファイル
- _phase.md（フェーズ概要）
- F-0001_login.md
- F-0002_dashboard.md
- F-0003_settings.md

**分割数**: 3機能

## 次のステップ
- 各機能ファイルを個別に編集可能
- `/merge-l3 PH-0001` で元のインライン形式に戻せます
- `/gen-code F-xxx` で機能単位でコード生成可能
```
