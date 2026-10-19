---
code: [scripts/install.py, skills/]
---
# 配布

REQ-0010 を実現する。`python scripts/install.py` が、リポジトリから CLI と Skill の写しを作る。リンクは作らない。

| 置き場（オプション・既定） | 中身 |
|---|---|
| `--prefix`（`~/.local/share/tri-ssd`） | CLI の実行一式: `scripts/tri.py`・`scripts/trissd/`・`templates/`・`docs/knowledge-model.md`・`docs/writing-rules.md` |
| `--bin`（`~/.local/bin`） | 起動スクリプト `tri`（sh）。Windows では `tri.cmd` も置く。どちらも導入に使った Python の絶対パスで `<prefix>/scripts/tri.py` を起動する |
| `--skills`（`~/.agents/skills`。複数指定できる） | `tri-ssd-setup`・`tri-ssd-task`・`tri-ssd-docs`（`skills/` の写し） |

- `--bin` は PATH の通ったフォルダを指定する。PATH に無ければ導入時に警告する
- 置いたファイルの一覧を `<prefix>/install.json` に記録し、次の導入で一覧から消えたものを削除する。何度実行しても同じ状態になる
- 起動スクリプトが Python の絶対パスを持つので、`python3` と `python` のどちらが使えるかに依存しない

| エージェント | Skill を読む場所 |
|---|---|
| Codex・Pi・OpenCode | `~/.agents/skills` |
| Claude Code | `~/.claude/skills`。`--skills ~/.claude/skills` でもう1つ写すか、`~/.agents/skills` へのリンクを張る（リンクは利用者の環境の管理） |

## 選定理由と却下案

| 選んだこと | 理由 | 採らなかった案 |
|---|---|---|
| 共有 Skill と PATH 上の `tri` で配る | Claude Code・Codex・Pi・OpenCode が 1 つの正本から同じ版を使える | エージェントごとのプラグイン（導入が二重になり版がずれる）。リポジトリの `bin/` を PATH に足す（作業ツリーの変更が写しの Skill より先に全プロジェクトへ及ぶ）。`uv tool install`（雛形と規約をパッケージに入れるため構成を変える必要がある） |
| Skill が参照する規約を `tri guide` で読む | CLI と一緒に配られ、Skill に写しを持たない | 各 Skill の `references/` に写す。同じ文書が Skill の数だけ配られる |
| `description` に発火の手がかりをまとめる | `when_to_use` は Claude Code しか読まない | `when_to_use` を分けたままにする |
