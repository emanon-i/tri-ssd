# 引き継ぎ

更新: 2026-10-19 23:47

- 現在位置: v7.0.0（T-0016・T-0017）。共有 Skill（~/.agents/skills/tri-ssd-*）と PATH 上の tri で配る。この PC では `python scripts/install.py --prefix D:/Tools/tri-ssd --bin D:/Tools/bin` で導入し、~/.claude/skills に 3 つのジャンクション、~/.claude/settings.json にフックを登録済み
- 次の一手: 説明文に when_to_use をまとめたので、発火評価（evals/trigger、有料 約 10 USD）で回帰を確かめる。評価の前に作業ツリーを導入し直す
- 未解決: PostToolUse フックは cwd が Tri-SSD プロジェクトの Claude セッションでの実際の編集では未確認（claude -p が認証切れ）／`tri context --emit` を起点なしで呼ぶと見出しに None と出る／同じ事実の別表現の重複は検出できない
