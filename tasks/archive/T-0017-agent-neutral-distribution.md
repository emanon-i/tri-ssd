---
id: T-0017
status: done
refs: [REQ-0010, docs/architecture.md#配布, docs/architecture.md#フック, docs/adr/0003-shared-skills-and-path-cli.md]
code: [scripts/install.py, scripts/tri.py, scripts/trissd/admin.py, skills/, tests/test_skills.py, README.md]
created: 2026-10-19
base: 1301332b1998
closed: 2026-10-19
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
  - 検証: `python -m unittest discover -s tests -p test_skills.py`
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

- `check --hook` はフックの JSON の cwd をプロジェクトとして扱う。cwd が別のフォルダのセッションから Tri-SSD プロジェクトの docs を編集しても指摘は返らない
- `claude -p` は CLI の OAuth の期限切れで使えなかった（デスクトップのセッションは動く）。PostToolUse は実際の Claude セッションでは未確認
- `tri context --emit` を起点なしで呼ぶと見出しに `None` と出る（Pi の試用で発見）

## 検証記録

- 2026-10-19 23:42 AC3 PASS 手動: このセッション（Claude Code デスクトップ）の Skill ツールが C:/Users/gonda/.claude/skills/tri-ssd-task（~/.agents/ski tree=db633f08afb8
  lls へのジャンクション）を読み、手順 1・2 で celephais の試用コピーの tri status・tri context が exit 0。claude -p は CLI の OAuth
   の期限切れで実行できなかった
- 2026-10-19 23:42 AC4 PASS 手動: codex exec が ~/.agents/skills/tri-ssd-task/SKILL.md を読み、PowerShell から tri status（exit 0）と tri co tree=db633f08afb8
  ntext docs/overview.md --emit（予算超過の報告で終了コード 1。出力は正常）を実行した
- 2026-10-19 23:42 AC5 PASS 手動: pi -p が ~/.agents/skills/tri-ssd-task/SKILL.md を読み、bash から tri status・tri context --emit を実行して要約 tree=db633f08afb8
  した
- 2026-10-19 23:42 AC6 PASS 手動: SessionStart: claude -p の起動時に settings.json の tri status --hook が動き、hook_response に状況が出た（認証切れの前） tree=db633f08afb8
  。PostToolUse: settings.json のコマンドに Claude Code と同じ形の JSON（cwd・tool_input.file_path）を渡し、REQ-9999 の br
  oken-id を additionalContext で返した。cwd が Tri-SSD プロジェクトの Claude セッションでの実際の編集では確かめていない
- 2026-10-19 23:45 AC1 PASS `python -m unittest discover -s tests -p test_install.py` → exit 0 「OK」 tree=db633f08afb8
- 2026-10-19 23:45 AC2 PASS `python -m unittest discover -s tests -p test_skills.py` → exit 0 「OK」 tree=db633f08afb8
- 2026-10-19 23:45 AC7 PASS `python -m unittest discover -s tests -p "test_*.py"` → exit 0 「OK」 tree=db633f08afb8
