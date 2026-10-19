---
id: T-0018
status: done
refs: [REQ-0001, REQ-0006, REQ-0008, docs/knowledge-model.md#置き場, docs/knowledge-model.md#名前の規則]
code: [scripts/trissd/, scripts/tri.py, skills/, templates/, tests/]
created: 2026-10-20
base: 0c3a64eef3bb
closed: 2026-10-20
---
# T-0018 置き場を Goal・Docs・Tasks・NOTES・CHANGELOG に絞り、名前で中身が分かる配置にする

## 目的の状態

Tri-SSD の置き場は `docs/`（Goal とあるべき状態）・`tasks/`（作業。完了・中止は `tasks/archive/`）・`NOTES.md`（現在位置）・`CHANGELOG.md` だけで、名前から中身が分かる。

- `init` は `docs/goal.md` と `CHANGELOG.md` だけを作る。`.tri-ssd/` と `tri handoff --local` は無く、NOTES は `tri notes` で書く
- 判断の理由は各文書の `## 選定理由と却下案` の節に書き、その節は履歴汚染と存在しないパスの検査から外れる。ADR は無い
- v5（L0〜L3）と v6（`docs/tasks/`・`docs/notes/`・`.tri-ssd/`）の配置を `tri migrate` で移せる。相対リンクと旧いパスへの言及も書き直す
- Skill・README・知識モデルは新しい配置だけを案内し、tri-ssd 自身も新しい配置で `tri check` がエラー 0 になる
- 導入し直した `tri` で、Claude Code・Codex・Pi が新しい配置のプロジェクトを扱える

## 受け入れ条件

- AC1: `init`・`notes`・Task の作成と完了が新しい置き場を使い、`.tri-ssd/` を作らない
  - 検証: `python -m unittest discover -s tests -p test_lifecycle.py -k Init -k Notes`
  - 検証: `python -m unittest discover -s tests -p test_tasks.py`
- AC2: v5 と v6 の配置を `migrate --apply` で移し、相対リンクと言及を書き直し、移行後の `check` がエラー 0 になる
  - 検証: `python -m unittest discover -s tests -p test_lifecycle.py -k Migrate`
- AC3: `## 選定理由と却下案` の節は履歴汚染の検査から外れ、ほかの節の経緯は検出される
  - 検証: `python -m unittest discover -s tests -p test_check.py -k history`
- AC4: Skill が新しい配置のコマンドだけを使い、tri-ssd 自身の `check` がエラー 0・警告 0 になる
  - 検証: `python -m unittest discover -s tests -p test_skills.py`
  - 検証: `python scripts/tri.py check`
- AC5: 導入し直した `tri` で、Claude Code・Codex・Pi が新しい配置のプロジェクトの `tri status`・`tri context` を動かせる
  - 検証: 手動: 試用のプロジェクトで各エージェントに tri-ssd-task の手順 1・2 を頼み、実行されたコマンドと結果を確かめる
- AC6: Windows で unittest とコンテキスト効率の評価が通る
  - 検証: `python -m unittest discover -s tests -p "test_*.py"`
  - 検証: `python tests/eval_context.py`

## メモ

<!-- 作業中の発見・仮説・調べたこと。Task の完了と一緒に退場する。今後も真な事実は Docs へ移す -->

## 検証記録

- 2026-10-20 00:56 AC5 PASS 手動: 導入し直した tri で、celephais の写し（新しい配置）に対し Claude Code（claude -p。SessionStart フック・ジャンクション経由の tri-ssd-t tree=2c1069a004a8
  ask）・Codex（PowerShell）・Pi（bash）が tri status・tri context・tri notes を実行し、NOTES.md だけが変わった。PostToolUse 
  フックも実際の Claude セッションで docs/goal.md の編集直後に broken-id の指摘を返した
- 2026-10-20 00:57 AC1 PASS `python -m unittest discover -s tests -p test_lifecycle.py -k Init -k Notes` → exit 0 「OK」 tree=2c1069a004a8
- 2026-10-20 00:57 AC2 PASS `python -m unittest discover -s tests -p test_lifecycle.py -k Migrate` → exit 0 「OK」 tree=2c1069a004a8
- 2026-10-20 00:57 AC3 PASS `python -m unittest discover -s tests -p test_check.py -k history` → exit 0 「OK」 tree=2c1069a004a8
- 2026-10-20 00:57 AC4 PASS `python -m unittest discover -s tests -p test_skills.py` → exit 0 「OK」 tree=2c1069a004a8
- 2026-10-20 00:57 AC6 PASS `python -m unittest discover -s tests -p "test_*.py"` → exit 0 「OK」 tree=2c1069a004a8
