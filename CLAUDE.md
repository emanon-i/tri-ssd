# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

このリポジトリは **Tri-SSD Claude Code プラグインの開発リポジトリ** です。

Tri-SSD（Tri-Layer Slice Spec Driven）は、AI/LLMコードエージェントを前提としたシンプルな仕様駆動開発フレームワークです。このリポジトリでは、そのフレームワークを Claude Code で利用するためのプラグイン（コマンド）を開発しています。

## ディレクトリ構成

```
commands/           # コマンド定義（.md）
docs/               # フレームワーク仕様・ガイド
.claude-plugin/     # プラグイン設定（plugin.json, marketplace.json）
.claude/rules/      # コンテキスト依存ルール
```

## Tri-SSD レイヤー構造

| レイヤー | 内容 | ファイル |
|---------|------|----------|
| L0 | アイディア・ラフメモ（任意） | docs/l0_ideas/ |
| L1 | 要件・意思決定（課題・動機・判断の記録） | docs/l1_requirements/vision.md |
| L2 | システム構成（技術スタック・アーキ） | docs/l2_foundation/foundation.md |
| L3 | フェーズ（機能一覧 + 受け入れ条件） | docs/l3_phases/PH-xxx.md |

## コマンド定義の書き方（commands/*.md）

### フロントマター形式

```yaml
---
description: コマンドの説明（1行）
argument-hint: "[引数] - 説明"
allowed-tools: Read, Write, Edit, Glob, Grep
---
```

| フィールド | 必須 | 説明 |
|-----------|------|------|
| description | ○ | コマンドの簡潔な説明 |
| argument-hint | △ | 引数がある場合の説明 |
| allowed-tools | ○ | 使用を許可するツール |

### 本文の重要な構成要素

#### 1. 共通コンテキストブロック

```markdown
<tri_ssd_context>
Tri-SSD（Tri-Layer Slice Spec Driven）はAI/LLMコードエージェントを前提とした仕様駆動開発。

レイヤー構造:
- L0: アイディア・ラフメモ（docs/l0_ideas/）- 任意
- L1: 要件（docs/l1_requirements/vision.md）
- L2: システム構成（docs/l2_foundation/foundation.md）
- L3: フェーズ（docs/l3_phases/PH-xxx.md）- 機能+受け入れ条件

ID形式: PREFIX-nnnn（REQ, PH, F）
</tri_ssd_context>
```

#### 2. 過剰設計回避の指示

```markdown
<avoid_over_engineering>
- 必要以上に詳細を聞き出さない
- 「わからない」→ TODOマークして先に進む
- テンプレートの全セクションを埋める必要はない
- 「念のため」でセクションを追加しない
</avoid_over_engineering>
```

#### 3. 出力フォーマット（必須セクション）

- YAMLフロントマター形式の定義
- 必須構造（Markdownテンプレート）
- 省略可能なセクションの明記

#### 4. 完了後の案内

- 作成ファイルのパスを報告
- TODO箇所の数を報告
- 次のコマンドを案内

#### 5. 使用例（推奨）

引数セクションの直後に配置:

````markdown
### 使用例

```
/gen-l1                           # 対話モード
/gen-l1 docs/existing-spec.md     # 既存ドキュメントを変換
```
````

#### 6. エラーケースセクション（推奨）

ファイル末尾に配置:

```markdown
## エラーケース

| ケース | 対応 |
|--------|------|
| ファイルが存在しない | エラー: 「指定されたファイルが見つかりません」 |
| 前提条件を満たさない | エラー or 警告（続行確認） |
```

### セクション名の標準

| 用途 | 標準名 |
|------|--------|
| コマンドの目的説明 | 概要 |
| 処理完了後の報告 | 完了後の案内 |
| 生成物のフォーマット | 出力フォーマット |

## ID形式（本文中で使用）

| プレフィックス | 用途 |
|---------------|------|
| REQ | 要件（L1内でインライン定義） |
| PH | フェーズ |
| F | 機能 |

ID形式: `PREFIX-nnnn`（例: REQ-0001）

## 開発時の注意

- **レイヤーをスキップしない**: L1/L2なしでL3を生成しない
- **コマンドは Markdown で定義**: `commands/*.md` に配置
- **ID形式を守る**: 連番 `PREFIX-nnnn`
- **変更時はバージョン更新を忘れない**: 変更を加えたら `CHANGELOG.md`、`.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json` のバージョンを同期

## プラグイン開発原則

コマンドを開発する際は、以下の原則を遵守してください。

### 必須ルール

| 原則 | 要件 |
|------|------|
| ファイルサイズ | 200-400行推奨、最大800行厳守 |
| 単一責任 | 1コマンド = 1つの明確な責任 |
| 段階的開示 | 基本機能→詳細機能の順で設計 |

### コンテキスト効率

- 大きなファイルを一度に読み込まない
- 必要な部分のみを参照
- ドキュメント間の重複を避ける
