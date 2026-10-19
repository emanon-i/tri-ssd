---
id: T-0013
status: done
refs: [REQ-0005, docs/architecture.md#完了ゲート]
code: [scripts/trissd/tasks.py]
created: 2026-10-17
base: 415d3dd2dff1
closed: 2026-10-17
---
# T-0013 AC の状態を検証記録だけに持たせる

## 目的の状態

- AC の状態（満たしたか）は検証記録だけが持つ。雛形の AC にチェック欄が無く、旧形式のチェック欄は読めるが状態として扱わない。Task の題に「検証記録」等の語が入っても AC を読める
- `task report` に作業メモと、他の Task ファイルへの変更が載る
- 見出しアンカーの大文字小文字違いのリンク切れには正しい綴りを示し、`task start` は状態が変わらないときそう言う

## 受け入れ条件

- AC1: 雛形の AC にチェック欄が無く、旧形式の `[x]` でも検証が FAIL なら FAIL になり欄が外れる。題に節名の語があっても AC を読める
  - 検証: `cd tests && python3 -m unittest test_tasks -k template_has_memo -k legacy_checkbox -k verify_records -k title_with_section`
- AC2: 報告に `## メモ` と他 Task ファイルの変更が載り、Task 自身は変更一覧に出ない
  - 検証: `cd tests && python3 -m unittest test_tasks -k memo_and_other_task`
- AC3: アンカーの大小違いに正しい slug を示し、既に active の Task の start は「既に」と出る
  - 検証: `cd tests && python3 -m unittest test_check test_tasks -k broken_anchor_suggests -k unchanged_status`

## メモ

- 試行4で、検証記録の無い `[x]` が完了済みに見えた。原因はチェック欄と検証記録が同じ状態を2か所に持っていたこと
- この Task の題（「検証記録」を含む）で AC が0件と判定された。題の見出しを節と見なしていた。節の判定は見出しレベル 2 以上に限定

## 判断

チェック欄を廃止した。チェック欄と検証記録の食い違いを検査する案は、同じ状態を2か所に持つ原因を残したまま検査を増やすのでやめた。

## 検証記録

- 2026-10-17 09:25 AC1 PASS `cd tests && python3 -m unittest test_tasks -k template_has_memo -k legacy_checkbox -k verify_record tree=bbd5e7b49222
  s -k title_with_section` → exit 0 「OK」
- 2026-10-17 09:25 AC2 PASS `cd tests && python3 -m unittest test_tasks -k memo_and_other_task` → exit 0 「OK」 tree=bbd5e7b49222
- 2026-10-17 09:25 AC3 PASS `cd tests && python3 -m unittest test_check test_tasks -k broken_anchor_suggests -k unchanged_status tree=bbd5e7b49222
  ` → exit 0 「OK」

