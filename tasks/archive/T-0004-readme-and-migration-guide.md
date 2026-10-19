---
id: T-0004
status: done
refs: [REQ-0008]
code: []
created: 2026-10-16
closed: 2026-10-16
---
# T-0004 README and migration guide

## 目的の状態

README に導入・初期化・日常の利用・既存プロジェクトへの導入・旧 Tri-SSD からの移行が書かれている。

## 受け入れ条件

- [x] AC1: README にインストール・初期化・日常の利用・既存プロジェクトへの導入・旧版からの移行が書かれている
  - 検証: `python3 -m unittest discover -s tests -p test_plugin.py -k test_readme`
- [x] AC2: リポジトリの Markdown が markdownlint を通る
  - 検証: `npx --yes markdownlint-cli@0.41.0 "**/*.md" --ignore node_modules`

## 検証記録

- 2026-10-16 22:46 AC1 PASS `python3 -m unittest discover -s tests -p test_plugin.py -k test_readme` → exit 0 「OK」 tree=cfb20df25730
- 2026-10-16 22:46 AC2 FAIL `npx --yes markdownlint-cli@0.41.0 "**/*.md" --ignore node_modules` → exit 1 「docs/tasks/_done/T-000 tree=cfb20df25730
  2-skills-and-hooks.md:32:201 MD013/line-length Line length [Expected: 200; Act」
- 2026-10-16 22:47 AC1 PASS `python3 -m unittest discover -s tests -p test_plugin.py -k test_readme` → exit 0 「OK」 tree=3f5d8c69b302
- 2026-10-16 22:47 AC2 FAIL `npx --yes markdownlint-cli@0.41.0 "**/*.md" --ignore node_modules` → exit 1 「docs/tasks/T-0004-read tree=3f5d8c69b302
  me-and-migration-guide.md:24:201 MD013/line-length Line length [Expected: 200;」
- 2026-10-16 22:47 AC1 PASS `python3 -m unittest discover -s tests -p test_plugin.py -k test_readme` → exit 0 「OK」 tree=3f5d8c69b302
- 2026-10-16 22:47 AC2 PASS `npx --yes markdownlint-cli@0.41.0 "**/*.md" --ignore node_modules` → exit 0 tree=3f5d8c69b302
