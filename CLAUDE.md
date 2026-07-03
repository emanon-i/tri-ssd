# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

このリポジトリは **Tri-SSD Claude Code プラグインの開発リポジトリ** です。

Tri-SSD（Tri-Layer Slice Spec Driven）は、AI/LLMコードエージェントを前提としたシンプルな仕様駆動開発フレームワークです。このリポジトリでは、そのフレームワークを Claude Code で利用するためのプラグイン（スキル群）を開発しています。

核の哲学: **極小構成・過剰設計回避が最優先**。**仕様は腐る、コードが真実**（L3 は完了後にアーカイブして葬る）。

## ディレクトリ構成

```
skills/             # スキル定義（skills/<name>/SKILL.md + scripts/ + references/）
scripts/            # スキル横断の共有スクリプト（ID採番・整合性検証・依存グラフ抽出）
docs/               # フレームワーク仕様・ガイド
  layer-rules.md    #   レイヤー配置ルール（配置判断の SSOT）
  writing-rules.md  #   記載規約（生成ドキュメントの書き方の SSOT）
  plugin-development-guide.md  # プラグイン開発ガイド
.claude-plugin/     # プラグイン設定（plugin.json, marketplace.json）
.claude/rules/      # コンテキスト依存ルール（skills/ 編集時に自動注入）
```

## Tri-SSD レイヤー構造

L0（任意メモ）→ L1（要件 vision.md）→ L2（構成 foundation.md）→ L3（フェーズ PH-nnnn.md）。
ID形式: `PREFIX-nnnn`（REQ, PH, F）。番号は再利用しない（永久欠番）。

**どの情報をどのレイヤーに置くかの判定・ファイル分割・粒度の正規ルールは `docs/layer-rules.md` を参照**（配置判断の唯一の出所）。

## スキル定義の書き方

`skills/<name>/SKILL.md` に配置。書き方の規約は `.claude/rules/skill-development.md`（skills/ 編集時に自動注入される）と `docs/plugin-development-guide.md` を参照。

要点のみ:

- フロントマター: `description`（必須）+ `when_to_use`（推奨）。合計1,536文字以内
- 共通コンテキストブロックは規定文面のみ（レイヤー詳細は layer-rules.md に委譲、複製しない）
- 本文500行未満、参照は1階層まで、決定的処理は scripts/ へ

## 開発時の注意

- **レイヤーをスキップしない**: L1/L2なしでL3を生成しない
- **ID形式を守る**: 連番 `PREFIX-nnnn`、採番は `scripts/next_id.py` を使う（自前実装しない）
- **変更時はバージョン更新を忘れない**: 変更を加えたら `CHANGELOG.md`、`.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json` のバージョンを同期

## プラグイン開発原則

| 原則 | 要件 |
|------|------|
| ファイルサイズ | SKILL.md 本文500行未満（推奨200-300行） |
| 単一責任 | 1スキル = 1つの明確な能力（更新トリガーが同一の処理は同居可） |
| 段階的開示 | 本体は薄く、定型・詳細は references/ へ。決定的処理は scripts/ へ |
| SSOT | 同じ規約・テンプレートを複数ファイルに複製しない。正を1つ決め、他は参照 |

## コンテキスト効率

- 大きなファイルを一度に読み込まない。必要な部分のみを参照
- ドキュメント間の重複を避ける（索引・リンクは複製可、正規の事実は複製しない）
