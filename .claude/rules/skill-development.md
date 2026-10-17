---
globs: skills/**/*.md
---

# スキル開発ルール

このルールは `skills/` ディレクトリ内のファイル（SKILL.md・参照ファイル）を編集する際に適用されます。

## フロントマター

```yaml
---
name: skill-name                       # 原則書かない（呼び出し名はディレクトリ名で決まる）
description: 何をするか（1〜2文、必須）
when_to_use: いつ使うか。自然な発火フレーズを列挙（推奨）
argument-hint: "[引数] - 説明"          # 引数がある場合
allowed-tools: Read, Write, Edit, Glob, Grep  # 事前承認するツールのみ列挙
---
```

- `description` + `when_to_use` は**合計1,536文字以内**（超過分はトランケートされ発火精度が落ちる）
- `description` は三人称で「何をするか＋いつ使うか」。`when_to_use` にトリガー語（「〜したい」等の口語）を列挙
- `allowed-tools` は「制限」ではなく「事前承認」。確実に使うツールのみ列挙する

## XML タグによる強指示

逸脱してほしくない制約・思考手順は XML タグのブロック（`<tri_ssd_context>` `<avoid_over_engineering>` `<thinking_process>` 等）で囲む。タグで囲まれた指示は LLM が優先的に遵守する。通常の説明・手順は Markdown のまま書く（何でも囲むとタグの効果が薄れる）。
なお**生成されるドキュメント側**では XML タグを使わない（人間可読性優先。記載規約は `docs/writing-rules.md` が正）。

## 共通コンテキストブロック

すべてのスキルに含める（規定文面のまま。`tests/test_plugin.py` が全スキルでの一致を検査する）:

```markdown
<tri_ssd_context>
Tri-SSD: Goal（docs/goal.md）・Docs（docs/ のあるべき状態）・Tasks（docs/tasks/ 差分を解消する検証可能な作業。作業メモも Task の中）・引き継ぎ（docs/notes/handoff.md）・CHANGELOG（意味のある変更の履歴）。常に守る規則はエージェントが常に読む指示ファイル（CLAUDE.md・AGENTS.md）に置く。
決定的処理は CLI `python3 "${CLAUDE_SKILL_DIR}/../../scripts/tri.py"`（以下 `tri`）で行う。`tri` はカレントディレクトリをプロジェクトとして扱うので、プロジェクトのルートでこの絶対パスのまま実行する（プラグインのディレクトリへ cd しない）。文書を開く前に `tri context` で必要なセクションだけを取得する。
置き場・寿命の判断に迷ったら `${CLAUDE_SKILL_DIR}/../../docs/knowledge-model.md` を読むこと。
</tri_ssd_context>
```

置き場・寿命の詳細を各スキルに複製しない。正は `docs/knowledge-model.md`。

`<avoid_over_engineering>` ブロック（スキルごとに内容調整可）も含める。

## 段階的開示

| 対象 | 上限 |
|------|------|
| SKILL.md 本文 | 500行未満（推奨 200〜300行） |
| 参照の深さ | 1階層まで（SKILL.md → references/*.md は可、その先の多段参照は不可） |

- 定型テンプレートや長い出力例は `references/` に外出しし、必要時のみ読む
- 決定的処理（採番・解析・検査・移動）は CLI（`scripts/tri.py` のサブコマンド）に実装し、スキルからは `tri <command>` で呼ぶ。スキルが使うサブコマンドは `tests/test_plugin.py` が実在を検査する

## 必須セクション

1. **出力フォーマット定義** — YAMLフロントマター形式・必須Markdown構造・省略可能なセクション
2. **ID採番**（ID生成を行う場合）— `tri id <PREFIX>` / `tri task new` を使う（自前で採番ロジックを書かない）
3. **完了後の案内** — 作成ファイルのパス・TODO箇所の数・次のスキル

## 単一責任

1スキル = 1つの明確な能力。複数の責任を持ちそうなら分割を検討。
ただし**更新トリガーが同一**の処理（例: フェーズ完了時のゲート＋CHANGELOG＋知見還元）は1スキルにまとめてよい。
