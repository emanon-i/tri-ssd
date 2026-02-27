---
description: 分離されたL3フェーズを1ファイルに統合する
argument-hint: <PH-ID | フォルダパス> - 統合対象（必須）
allowed-tools: Read, Write, Glob, Grep, Bash
---

# L3 フェーズ統合コマンド

<tri_ssd_context>
Tri-SSD（Tri-Layer Slice Spec Driven）はAI/LLMコードエージェントを前提とした仕様駆動開発。

レイヤー構造:
- L0: アイディア・ラフメモ（docs/l0_ideas/）- 任意
- L1: 要件（docs/l1_requirements/vision.md）
- L2: システム構成（docs/l2_foundation/foundation.md）
- L3: フェーズ（docs/l3_phases/PH-xxx.md）- 機能+受け入れ条件

ID形式: PREFIX-YYYYMMDD-nnn（REQ, PH, F）
</tri_ssd_context>

## 概要

フォルダ構造（分離形式）のL3フェーズを、インライン形式の1ファイルに統合する。

**用途**:
- 機能開発が完了し、フェーズを1ファイルにまとめたい
- 分割の必要がなくなったフェーズをシンプル化
- `/split-l3` で分割したフェーズを元に戻す

## 統合時の原則

<avoid_over_engineering>
- チェック状態（`[x]`）は完全に保持する
- 機能ファイルはファイル名順でソートして統合
- status は全機能が done の場合のみ done、それ以外は wip
</avoid_over_engineering>

## 引数

- `$1`: 統合対象（必須）
  - PH-ID: `PH-20250204-001`
  - フォルダパス: `docs/l3_phases/PH-xxx_name/`

## 前提処理

1. `$1` で指定された対象フォルダを特定
   - ID指定: Glob で `docs/l3_phases/**/PH-*$1*/` を検索
   - パス指定: 直接参照
2. フォーマット検証（分離形式であること）
   - `_phase.md` の存在確認
   - `F-*.md` の存在確認
3. 同名ファイルが既に存在する場合はエラー

---

## 処理手順

### Step 1: フォルダ解析

対象フォルダから以下を読み込み:
- `_phase.md`: フェーズ概要、Exit Criteria
- `F-*.md`: 各機能ファイル（ファイル名順でソート）

### Step 2: ステータス判定

```
全機能の status が done → 統合ファイルも done
それ以外 → 統合ファイルは wip
```

### Step 3: 機能セクション統合

各機能ファイルを「機能セクション」として統合:

```markdown
### F-xxx: [機能名]
**対応REQ**: REQ-xxx

[機能の概要説明]

**受け入れ条件**:
- [ ] 条件1
- [x] 条件2（チェック済みは保持）

---
```

### Step 4: インライン形式ファイル生成

統合ファイルを作成:

```markdown
---
status: {判定されたstatus}
---

# PH-xxx: [フェーズ名]

## 目的
{_phase.mdから}

## 機能一覧

{各機能セクションを順番に配置}

## Exit Criteria
{_phase.mdから}
```

### Step 5: 元フォルダ削除

統合完了後、元のフォルダを削除。

---

## 出力フォーマット

### インライン形式ファイル

```yaml
---
status: wip
---
```

```markdown
# PH-xxx: [フェーズ名]

## 目的
このフェーズで達成すること

## 機能一覧

### F-xxx: [機能1]
**対応REQ**: REQ-xxx

[機能の概要説明]

**受け入れ条件**:
- [ ] 条件1
- [x] 条件2

---

### F-xxx: [機能2]
**対応REQ**: REQ-xxx

[機能の概要説明]

**受け入れ条件**:
- [ ] 条件1

---

## Exit Criteria
- [ ] 全機能の受け入れ条件がパス
- [x] 結合テストがパス
```

---

## エラーケース

| ケース | 対応 |
|--------|------|
| フォルダが見つからない | エラー: 「指定されたフォルダが見つかりません」 |
| 既にインライン形式 | エラー: 「既にインライン形式です。変換不要です」 |
| `_phase.md` がない | エラー: 「_phase.md が見つかりません」 |
| `F-*.md` がない | エラー: 「機能ファイル（F-*.md）が見つかりません」 |
| 同名ファイルが存在 | エラー: 「同名ファイルが存在します。手動で確認してください」 |

---

## ステータス管理の詳細

### 機能ファイルのステータス確認

```
F-001.md: status: done
F-002.md: status: wip
F-003.md: status: done
→ 統合ファイル: status: wip（1つでも wip があれば wip）
```

### Exit Criteria のチェック状態

`_phase.md` の Exit Criteria セクションのチェック状態は保持:

```markdown
## Exit Criteria
- [x] 全機能の受け入れ条件がパス
- [ ] 結合テストがパス
```

---

## 完了後の案内

```markdown
# 統合完了

**入力**: docs/l3_phases/PH-20250204-001_mvp/
**出力**: docs/l3_phases/PH-20250204-001_mvp.md

## 統合内容
- 機能数: 3
- ステータス: wip（F-002 が wip のため）

## チェック状態
- 受け入れ条件: 5/8 完了
- Exit Criteria: 1/2 完了

## 次のステップ
- `/split-l3 PH-20250204-001` で再度分割可能
- `/done PH-20250204-001` で完了マーキング
- `/gen-code PH-20250204-001` でコード生成
```
