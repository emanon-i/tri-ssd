# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

このリポジトリは **Tri-SSD Claude Code プラグインの開発リポジトリ** です。

Tri-SSD は、AI エージェント駆動の長期開発で知識が陳腐化・肥大化しないよう、知識のライフサイクルとコンテキストを管理するハーネスです。
Goal・Docs・Tasks・Notes・CHANGELOG の置き場と寿命を定め、決定的な処理（知識グラフ・関連セクションの取得・逆引き・検査・完了ゲート）を CLI で行います。

核の哲学: **管理のための管理を増やさない**。**決定的に処理できることは機械で、意味の判断はエージェントで**。

## ディレクトリ構成

```text
skills/          # Skill（setup / task / docs / note）。SKILL.md + references/
scripts/tri.py   # CLI の入口（標準ライブラリのみ）
scripts/trissd/  # CLI の実装（md / project / resolve / check / tasks / notes / admin）
hooks/           # プラグインのフック（SessionStart・PostToolUse）
docs/            # フレームワーク仕様（knowledge-model / writing-rules / architecture）兼、このリポジトリ自身の Tri-SSD 知識
tests/           # unittest・長期運用シミュレーション・コンテキスト効率の評価・フィクスチャ
.claude-plugin/  # plugin.json / marketplace.json
.claude/rules/   # skills/ 編集時に自動注入される規約
```

## このリポジトリ自身を Tri-SSD で開発する

作業は Tri-SSD の流れで行う（CLI は `python3 scripts/tri.py`）:

1. `python3 scripts/tri.py status` で現在位置を確認する
2. `python3 scripts/tri.py context T-xxxx --emit` で必要な節だけ読む
3. 変更は Task にし、`task verify` → `task close` で証跡付きで完了する
4. 仕様の変更は docs/ を現在形のまま置き換え、`python3 scripts/tri.py log ...` で CHANGELOG に記録する
5. `python3 scripts/tri.py check` がエラー 0 であることを確認する

配置判断の正は `docs/knowledge-model.md`、書き方の正は `docs/writing-rules.md`、仕組みの正は `docs/architecture.md`。

## スキル定義の書き方

`skills/<name>/SKILL.md` に配置。規約は `.claude/rules/skill-development.md`（skills/ 編集時に自動注入）と `docs/plugin-development-guide.md`。

- フロントマター: `description`（必須）+ `when_to_use`（推奨）。合計1,536文字以内
- 共通コンテキストブロックは規定文面のみ（`tests/test_plugin.py` が一致を検査する）
- 本文500行未満、参照は1階層まで、決定的処理は CLI へ

## 開発時の注意

- **テスト**: `python3 -m unittest discover -s tests -p "test_*.py"`（Skill から参照する CLI コマンドの実在も検査される）
- **外部依存を足さない**: CLI は Python 3.10+ の標準ライブラリのみ
- **ID は CLI で採番**: `python3 scripts/tri.py id REQ` / `task new`（自前で採番しない）
- **変更時はバージョン更新を忘れない**: `CHANGELOG.md`、`.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json` のバージョンを同期
- **評価表の更新**: 取得ロジックを変えたら `python3 tests/eval_context.py --write` で docs/evaluation.md を更新する

## プラグイン開発原則

| 原則 | 要件 |
|------|------|
| ファイルサイズ | SKILL.md 本文500行未満（推奨200-300行） |
| 単一責任 | 1スキル = 1つの明確な能力（更新トリガーが同一の処理は同居可） |
| 段階的開示 | 本体は薄く、定型・詳細は references/ へ。決定的処理は CLI へ |
| SSOT | 同じ規約・テンプレートを複数ファイルに複製しない。正を1つ決め、他は参照 |
