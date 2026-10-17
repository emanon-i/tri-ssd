---
id: T-0011
status: done
refs: [REQ-0005, docs/architecture.md#完了ゲート]
code: [scripts/trissd/tasks.py, scripts/tri.py]
created: 2026-10-17
started: 2026-10-17 07:13:26
base: 487f5ca0cd53
closed: 2026-10-17
---
# T-0011 Verification at pivot points with a readable report

## 目的の状態

ゲートは関係する文書の誤りだけで止まり手の確認は失効しない。変更を確かめていない検証が警告され、人間向けの報告が既存の記録から出る。

## 受け入れ条件

- [x] AC1: 無関係な文書の誤りでは完了が止まらず、関係する文書の誤りでは止まり、手で確かめた記録はコード変更で失効しない
  - 検証: `python3 -m unittest discover -s tests -p test_tasks.py -k GateScopeTest`
- [x] AC2: 着手時点で落ちる検証と通ってしまう検証を区別して記録し、報告に出す
  - 検証: `python3 -m unittest discover -s tests -p test_tasks.py -k AgainstBaseTest`
- [x] AC3: 報告が目的・満たす仕様・検証・判断・変更・CHANGELOG を既存の記録から組み立てる
  - 検証: `python3 -m unittest discover -s tests -p test_tasks.py -k ReportTest`

## 判断

報告の項目を AI に書かせてゲートで強制する案はやめた。文章の有無しか機械で判定できず、既存の記録と重複し、強制完了の常態化を招くため。意味のない検証は文章でなく実行結果（着手時点でも通るか）で判定する。

## 検証記録

- 2026-10-17 07:13 AC1 PASS `python3 -m unittest discover -s tests -p test_tasks.py -k GateScopeTest` → exit 0 「OK」 tree=3fc9b8f031d9
- 2026-10-17 07:13 AC2 PASS `python3 -m unittest discover -s tests -p test_tasks.py -k AgainstBaseTest` → exit 0 「OK」 tree=3fc9b8f031d9
- 2026-10-17 07:13 AC3 PASS `python3 -m unittest discover -s tests -p test_tasks.py -k ReportTest` → exit 0 「OK」 tree=3fc9b8f031d9
- 2026-10-17 07:13 AC1 着手時点 FAIL（変更を確かめている）
- 2026-10-17 07:13 AC2 着手時点 FAIL（変更を確かめている）
- 2026-10-17 07:13 AC3 着手時点 FAIL（変更を確かめている）
