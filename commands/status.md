---
description: Tri-SSDドキュメントの進捗状況を確認する
argument-hint: "[--list-ids | ファイルパス] - オプション"
allowed-tools: Read, Glob, Grep
---

# Tri-SSD 進捗確認コマンド

<tri_ssd_context>
Tri-SSD（Tri-Layer Slice Spec Driven）はAI/LLMコードエージェントを前提とした仕様駆動開発。

レイヤー構造:
- L0: アイディア・ラフメモ（docs/l0_ideas/）- 任意
- L1: 要件（docs/l1_requirements/vision.md）
- L2: システム構成（docs/l2_foundation/foundation.md）
- L3: フェーズ（docs/l3_phases/PH-xxx.md）- 機能+受け入れ条件

ID形式: PREFIX-YYYYMMDD-nnn（REQ, PH, F）
</tri_ssd_context>

## 確認時の原則

<avoid_over_engineering>
- 軽量に実行（必要なファイルのみ読み込む）
- 詳細チェックはオプション（デフォルトはサマリ）
- 問題がなければ次のステップを提案
</avoid_over_engineering>

## 概要

Tri-SSD ドキュメントの進捗状況を確認する。

## 引数

- `$1` (省略可): 確認対象
  - **省略**: 全体の進捗確認
  - **`--list-ids`**: 存在するID一覧を表示
  - **ファイルパス**: 特定ファイルのみチェック

### 使用例

```
/status
/status --list-ids
/status docs/l3_phases/PH-20250203-001_mvp.md
```

## チェック項目

### ドキュメント存在確認
- [ ] L1: `docs/l1_requirements/vision.md` が存在するか
- [ ] L2: `docs/l2_foundation/foundation.md` が存在するか
- [ ] L3: `docs/l3_phases/` にフェーズファイルが存在するか

### ステータス集計
- [ ] `status: wip` のファイル数
- [ ] `status: done` のファイル数

### 参照整合性

**L3フェーズドキュメント**:
- [ ] 機能の対応REQ（REQ-xxx）が L1 に存在
- [ ] 機能ID（F-xxx）の重複がないか

**L1要件**:
- [ ] REQ IDが定義されているか

### 受け入れ条件の進捗（L3対象）
- [ ] 各フェーズの受け入れ条件チェック率
- [ ] Exit Criteria のチェック率

## 出力フォーマット

```markdown
# Tri-SSD 進捗確認

## サマリ

| レイヤー | ファイル | ステータス |
|---------|---------|----------|
| L1 | vision.md | done |
| L2 | foundation.md | wip |
| L3 | PH-xxx-001_mvp.md | wip (3/5) |
| L3 | PH-xxx-002_beta.md | wip (0/4) |

**全体進捗**: 1/4 完了

## 詳細

### L3 受け入れ条件
- PH-xxx-001: 3/5 チェック済み (60%)
- PH-xxx-002: 0/4 チェック済み (0%)

## 問題点（あれば）
1. [E001] ID重複: F-xxx (file1.md, file2.md)
2. [W001] 参照先不在: REQ-xxx (referenced in file.md)
```

## --list-ids 出力

```
REQ-20250125-001  docs/l1_requirements/vision.md
REQ-20250125-002  docs/l1_requirements/vision.md
PH-20250125-001   docs/l3_phases/PH-20250125-001_mvp.md
F-20250125-001    docs/l3_phases/PH-20250125-001_mvp.md
```

## 完了後の案内

- 次のステップを提案
  - L1がない → `/gen-l1` を案内
  - L2がない → `/gen-l2` を案内
  - L3がない → `/gen-l3` を案内
  - wip のファイルがある → `/done <ファイル>` で完了マーキングを案内
