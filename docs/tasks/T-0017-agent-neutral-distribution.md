---
id: T-0017
status: open
refs: [REQ-0010, docs/architecture.md#配布, docs/architecture.md#フック, docs/adr/0003-shared-skills-and-path-cli.md]
code: [scripts/install.py, scripts/tri.py, scripts/trissd/admin.py, skills/, tests/test_plugin.py, README.md]
created: 2026-10-19
---
# T-0017 全エージェントが共有 Skill と PATH 上の tri を1か所の正本から使う

## 目的の状態

Claude Code・Codex・Pi・OpenCode が、`scripts/install.py` で1回導入した同じ Skill（`~/.agents/skills/tri-ssd-*`）と PATH 上の同じ `tri` を使う。

- Skill は `${CLAUDE_SKILL_DIR}` もプラグインのフォルダの形も使わず、`tri` と `tri guide` と自分の `references/` だけを参照する
- Claude Code のフックは `~/.claude/settings.json` から `tri` を呼ぶ。プラグインとしての導入（marketplace・`hooks/hooks.json`）は無い
- README の導入手順は `scripts/install.py` とフックの登録だけを案内する

## 受け入れ条件

- AC1: 導入先を一時フォルダにした `install.py` が、起動スクリプトから `tri status`・`tri context` を動かし、Skill を `name` とフォルダ名をそろえて写す。再実行で消えた Skill を削除し、同じ状態に収束する
  - 検証: `python -m unittest discover -s tests -p test_install.py`
- AC2: Skill が置換変数・プラグインのパスを使わず、frontmatter が Agent Skills の形式（`name`・1024 文字以内の `description`）で、本文が使う `tri` のコマンドと `references/` が実在する。README がプラグインの導入を案内せず、フックの登録例のコマンドが実在する
  - 検証: `python -m unittest discover -s tests -p test_plugin.py`
- AC3: Claude Code で、`~/.claude/skills` のジャンクション経由の `tri-ssd-task` から `tri status`・`tri context` が動く
  - 検証: 手動: E:/Cella/Projects/celephais で `claude -p` に現在位置と次の Task の文脈を聞き、Skill の発火と 2 コマンドの実行を確かめる
- AC4: Codex で、`~/.agents/skills` の `tri-ssd-task` から `tri status`・`tri context` が動く
  - 検証: 手動: E:/Cella/Projects/celephais で `codex exec` に同じ依頼をして確かめる
- AC5: Pi で、`~/.agents/skills` の `tri-ssd-task` から `tri status`・`tri context` が動く
  - 検証: 手動: E:/Cella/Projects/celephais で `pi -p` に同じ依頼をして確かめる
- AC6: Claude Code のフックが `~/.claude/settings.json` から動く（セッション開始時の現在位置、docs 編集直後の検査）
  - 検証: 手動: celephais の一時コピーで `claude -p` を実行し、SessionStart の出力が文脈にあることと、docs を編集した直後に検査の指摘が返ることを確かめる
- AC7: Windows で unittest とコンテキスト効率の評価が通る
  - 検証: `python -m unittest discover -s tests -p "test_*.py"`
  - 検証: `python tests/eval_context.py`

## メモ

<!-- 作業中の発見・仮説・調べたこと。Task の完了と一緒に退場する。今後も真な事実は Docs へ移す -->

## 検証記録
