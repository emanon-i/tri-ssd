---
id: T-0002
status: done
refs: [REQ-0007, docs/architecture.md#フック]
code: [skills/, hooks/]
created: 2026-10-16
closed: 2026-10-16
---
# T-0002 Skills and hooks

## 目的の状態

4 つの Skill（setup・task・docs・note）と hooks.json が公式仕様に沿って存在し、CLI と知識モデルを参照する。

## 受け入れ条件

- [x] AC1: 各 Skill の frontmatter（description + when_to_use 1536 文字以内）・本文 500 行未満・共通コンテキストブロック・CLI 参照が規約どおり
  - 検証: `python3 -m unittest discover -s tests -p test_plugin.py -k SkillTest`
- [x] AC2: hooks.json が公式スキーマの形で SessionStart と PostToolUse を登録し、コマンドが実在する CLI を指す
  - 検証: `python3 -m unittest discover -s tests -p test_plugin.py -k HookTest`
- [x] AC3: Skill の手順どおりにエージェントが別プロジェクトで Task を完了できる
  - 検証: 手動: サブエージェントに Skill 本文だけを渡して実行させ、結果のリポジトリを check と目視で確認

## 検証記録

- 2026-10-16 22:28 AC1 FAIL `python3 -m unittest discover -s tests -p test_plugin.py` → exit 1 「FAILED (failures=1)」 tree=21e24d29b327
- 2026-10-16 22:28 AC2 FAIL `python3 -m unittest discover -s tests -p test_plugin.py` → exit 1 「FAILED (failures=1)」 tree=21e24d29b327
- 2026-10-16 22:28 AC1 PASS `python3 -m unittest discover -s tests -p test_plugin.py -k SkillTest` → exit 0 「OK」 tree=21e24d29b327
- 2026-10-16 22:28 AC2 PASS `python3 -m unittest discover -s tests -p test_plugin.py -k HookTest` → exit 0 「OK」 tree=21e24d29b327
- 2026-10-16 22:44 AC1 PASS `python3 -m unittest discover -s tests -p test_plugin.py -k SkillTest` → exit 0 「OK」 tree=c0aaa77259c2
- 2026-10-16 22:44 AC2 PASS `python3 -m unittest discover -s tests -p test_plugin.py -k HookTest` → exit 0 「OK」 tree=c0aaa77259c2
- 2026-10-16 22:44 AC3 PASS 手動: サブエージェント2体に Skill 本文だけを渡し linkbox 複製で試行。試行1: T-0007 を実装・検証・完了・引き継ぎ（check エラー0）。試行2: 新セッションで仕様変更（ tree=c0aaa77259c2
  保持期間30→14日）を Docs 置換・CHANGELOG・Task 完了・引き継ぎ（check --changed エラー0・履歴汚染0）。指摘25件を Skill/CLI に反映
- 2026-10-16 22:46 AC1 PASS `python3 -m unittest discover -s tests -p test_plugin.py -k SkillTest` → exit 0 「OK」 tree=cfb20df25730
- 2026-10-16 22:46 AC2 PASS `python3 -m unittest discover -s tests -p test_plugin.py -k HookTest` → exit 0 「OK」 tree=cfb20df25730
- 2026-10-16 22:46 AC3 PASS 手動: 試行1・2の指摘を反映した後の最終状態で、Skill 本文の手順と CLI の対応を test_plugin（全 tri サブコマンドの実在）と hooks の実コマンド実行で再確認 tree=cfb20df25730
