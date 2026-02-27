---
description: Tri-SSD用のディレクトリ構造を初期化する
argument-hint: なし
allowed-tools: Read, Write, Bash
---

# Tri-SSD 初期化コマンド

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

Tri-SSD 用のディレクトリ構造を初期化する。
プロジェクト開始時に1回のみ実行。

## 初期化時の原則

<avoid_over_engineering>
- 既存ファイルは上書きしない
- l0_ideas/ はワークフロー外（自由なメモ置き場）
- ディレクトリ作成のみ（テンプレートファイル自動生成はしない）
</avoid_over_engineering>

## 作成するディレクトリ

以下のディレクトリ構造を作成：

```
docs/
├── l0_ideas/           # アイディア・ラフメモ（任意）
│   └── .gitkeep
├── l1_requirements/    # 要件定義
│   └── .gitkeep
├── l2_foundation/      # システム構成
│   └── .gitkeep
└── l3_phases/          # フェーズ（機能+受け入れ条件）
    └── .gitkeep
```

## ID形式

タイムスタンプベース: `PREFIX-YYYYMMDD-nnn`

| ID種別 | 例 |
|--------|-----|
| 要件 | REQ-20250125-001 |
| フェーズ | PH-20250125-001 |
| 機能 | F-20250125-001 |

## 手順

1. **既存確認**: `docs/` が存在するか確認
2. **ディレクトリ作成**: 存在しない場合のみ作成
3. **完了報告**: 作成したディレクトリ構造を報告

## 完了後の案内

**出力**:
- 作成したディレクトリ一覧

**次のステップ**:
- `/gen-l1` → L1要件を生成（対話または既存ドキュメント変換）

---

## エラーケース

| ケース | 対応 |
|--------|------|
| docs/ が既に存在 | 警告表示、既存を維持して欠落ディレクトリのみ作成 |
