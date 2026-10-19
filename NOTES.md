# NOTES

更新: 2026-10-20 00:57

- 現在位置: v7.0.0（T-0016〜T-0018）。共有 Skill（~/.agents/skills/tri-ssd-*）と PATH 上の tri で配り、置き場は docs/・tasks/・NOTES.md・CHANGELOG.md
  - この PC の導入: `python scripts/install.py --prefix D:/Tools/tri-ssd --bin D:/Tools/bin`
  - ~/.claude/skills に 3 つのジャンクション、~/.claude/settings.json にフックを登録済み
- 次にやること: 説明文と置き場が変わったので、発火評価（evals/trigger、有料 約 10 USD）と成果の評価で回帰を確かめる。評価の前に作業ツリーを導入し直す
- 未決事項: 同じ事実の別表現の重複は検出できない／トークン数は推定値
