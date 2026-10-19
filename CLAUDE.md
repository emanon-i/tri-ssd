# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

このリポジトリは **Tri-SSD の開発リポジトリ** です。Claude Code・Codex・Pi・OpenCode が使う Skill と CLI `tri` を、`scripts/install.py` で配ります。

Tri-SSD は、AI エージェント駆動の長期開発で知識が陳腐化・肥大化しないよう、知識のライフサイクルとコンテキストを管理するハーネスです。
Goal・Docs・Tasks・引き継ぎ・CHANGELOG の置き場と寿命を定め、決定的な処理（知識グラフ・関連セクションの取得・逆引き・検査・完了ゲート）を CLI で行います。

核の哲学: **管理のための管理を増やさない**。**決定的に処理できることは機械で、意味の判断はエージェントで**。

## ディレクトリ構成

```text
skills/          # Skill（tri-ssd-setup / tri-ssd-task / tri-ssd-docs）。Agent Skills の形式。SKILL.md + references/
scripts/tri.py   # CLI の入口（標準ライブラリのみ）
scripts/install.py # CLI・起動スクリプト・Skill の写しを置く導入スクリプト
scripts/trissd/  # CLI の実装（md / project / resolve / check / tasks / notes / admin）
templates/       # Goal・Task・CHANGELOG の雛形（書式の正）
docs/            # フレームワーク仕様（knowledge-model / writing-rules / architecture）兼、このリポジトリ自身の Tri-SSD 知識
tests/           # unittest・長期運用シミュレーション・コンテキスト効率の評価・フィクスチャ
evals/           # claude plugin eval のケース（trigger/ 発火評価・heldout-* 成果の評価・dev の 5 件）
.claude-plugin/  # plugin.json（claude plugin eval で Skill を束ねるためだけ。導入には使わない）
.claude/rules/   # skills/ 編集時に自動注入される規約
```

## このリポジトリ自身を Tri-SSD で開発する

作業は Tri-SSD の流れで行う。作業ツリーの CLI は `python scripts/tri.py`（`python` が無ければ `python3`。PATH 上の `tri` は導入済みの版）:

1. `python scripts/tri.py status` で現在位置を確認する
2. `python scripts/tri.py context T-xxxx --emit` で必要な節だけ読む
3. 変更は Task にし、`task verify` → `task close` で証跡付きで完了する
4. 仕様の変更は docs/ を現在形のまま置き換え、`python scripts/tri.py log ...` で CHANGELOG に記録する
5. `python scripts/tri.py check` がエラー 0 であることを確認する

配置判断の正は `docs/knowledge-model.md`、書き方の正は `docs/writing-rules.md`、仕組みの正は `docs/architecture.md`。

## スキル定義の書き方

`skills/<name>/SKILL.md` に配置。規約は `.claude/rules/skill-development.md`（skills/ 編集時に自動注入）と `docs/skill-development-guide.md`。

- フロントマター: `name`（フォルダ名と同じ）+ `description`（何をするか・いつ使うか。1,024文字以内）
- 共通コンテキストブロックは規定文面のみ（`tests/test_skills.py` が一致を検査する）
- 本文500行未満、参照は1階層まで、決定的処理は CLI へ。特定のエージェントの置換変数（`${CLAUDE_SKILL_DIR}` 等）を使わない <!-- tri:ok -->

## 開発時の注意

- **テスト**: `python -m unittest discover -s tests -p "test_*.py"`（Skill から参照する CLI コマンドの実在も検査される）
- **外部依存を足さない**: CLI は Python 3.9+ の標準ライブラリのみ（CI は 3.9 と 3.13）
- **ID は CLI で採番**: `python scripts/tri.py id REQ` / `task new`（自前で採番しない）
- **変更時はバージョン更新を忘れない**: `CHANGELOG.md` と `.claude-plugin/plugin.json` のバージョンを同期
- **導入の確認**: Skill・CLI を変えたら `python scripts/install.py`（利用者と同じオプション）で導入し直し、`tri status` が動くことを確かめる
- **評価表の更新**: 取得ロジックを変えたら `python tests/eval_context.py --write` で docs/evaluation.md を更新する
- **Skill の評価**: スキルの説明文・手順を変えたら 作業ツリーを `python scripts/install.py` で導入し、`python evals/trigger/build.py` のあと `claude plugin eval . --tag trigger`（発火）と `--tag heldout`（成果）を回し、docs/skill-evaluation.md を実測値で更新する（有料。方法は同文書）

## Skill 開発原則

| 原則 | 要件 |
|------|------|
| ファイルサイズ | SKILL.md 本文500行未満（推奨200-300行） |
| 単一責任 | 1スキル = 1つの明確な能力（更新トリガーが同一の処理は同居可） |
| 段階的開示 | 本体は薄く、定型・詳細は references/ へ。決定的処理は CLI へ |
| SSOT | 同じ規約・テンプレートを複数ファイルに複製しない。正を1つ決め、他は参照 |
