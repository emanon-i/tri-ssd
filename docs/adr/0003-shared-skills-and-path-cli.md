---
kind: adr
---
# ADR-0003 プラグインではなく、共有 Skill と PATH 上の CLI で配る

## 状況

Tri-SSD は Claude Code のプラグインとして配っていた。利用者は Claude Code・Codex・Pi・OpenCode を同じプロジェクトで使い分ける。

- Skill は `${CLAUDE_SKILL_DIR}/../../scripts/tri.py` で CLI を探していた。置換変数は Claude Code だけのもので、プラグインのフォルダの形を前提にしている
- Codex・Pi・OpenCode は共有の Skill フォルダ（`~/.agents/skills`）を直接読む。Claude Code はプラグインとは別に `~/.claude/skills` を読む
- エージェントごとにプラグイン・拡張で配ると、同じ Skill と CLI が導入先の数だけ版違いで残る

## 決定

- Skill を Agent Skills の形式（`name` はフォルダ名と同じ `tri-ssd-<名前>`）で書き、CLI は PATH 上の `tri` で呼ぶ
- `scripts/install.py` が、リポジトリから CLI の実行一式・起動スクリプト・Skill の写しを1回で作る。Skill と CLI はいつも同じ版になる
- Skill が参照する規約（知識モデル・記載規約）は `tri guide <名前>` で読む。CLI と一緒に配られるので、Skill に写しを持たない
- Claude Code のフックは、利用者の `~/.claude/settings.json` に `tri` を呼ぶコマンドとして登録する
- `.claude-plugin/plugin.json` は `claude plugin eval` で Skill を束ねるためだけに残す

## 却下した案

| 案 | 理由 |
|---|---|
| エージェントごとにプラグイン・拡張を作る | 導入が二重になり、版がずれる |
| リポジトリの `bin/` に起動スクリプトを置き、PATH に足す | 作業ツリーの変更・ブランチの切り替えが、写しで配った Skill より先にすべてのプロジェクトへ及ぶ。Skill と CLI の版がずれる |
| `pyproject.toml` を足して `uv tool install`・`pipx install` で入れる | 雛形・規約の文書をパッケージに入れるためにリポジトリの構成を変える必要がある。導入先を利用者が選びにくい |
| 規約の文書を各 Skill の `references/` に写す | 同じ文書が Skill の数だけ配られる。リポジトリの `skills/` だけでは参照が解決せず、評価が配布物と別物になる |
| Skill の説明と `when_to_use` を分けたままにする | `when_to_use` は Claude Code だけが読む。他のエージェントは発火の手がかりを失うので、`description` にまとめる（1024 文字以内） |

## 結果

- 導入は `python scripts/install.py` と、Claude Code ではフックの登録の2つになる
- Skill の更新はリポジトリで行い、導入し直して配る。配った写しを直接直さない
