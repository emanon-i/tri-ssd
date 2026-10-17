---
id: T-0014
status: done
refs: [docs/skill-evaluation.md, docs/architecture.md#テスト戦略]
code: [evals/, skills/, scripts/trissd/admin.py, scripts/trissd/tasks.py]
created: 2026-10-17
base: 657dfc0f557e
closed: 2026-10-17
---
# T-0014 Skill の発火と効果を claude plugin eval で実測する

## 目的の状態

3 スキルについて、呼ぶべき依頼で呼ばれ呼ぶべきでない依頼で呼ばれないこと、呼ばれたときにプラグイン無しより良い結果を出すことを claude plugin eval で実測し、結果と見つかった原因の修正が skill-evaluation.md に実測値で載っている

## 受け入れ条件

- AC1: `evals/` の 5 ケース（発火すべき 3・すべきでない 2）をスキルあり／なしで実行し、発火の精度と点数の差が docs/skill-evaluation.md に実測値で載っている。修正後の再実行で、プラグインのディレクトリへの cd が 0 回になっている
  - 検証: 手動: `claude plugin eval` の aggregate-result.json と skill-evaluation.md の表を突き合わせる
- AC2: フォルダ形式のフェーズを移行すると、機能の節が検証記録の節より前に入る
  - 検証: `cd tests && python3 -m unittest test_lifecycle -k test_apply`
- AC3: 3 スキルの共通コンテキストブロックが一致し、参照する CLI コマンドが実在する
  - 検証: `cd tests && python3 -m unittest test_plugin`
- AC4: 「手動」で始まる検証行にバッククォートのコマンドがあっても、`task verify` は実行せず手動の AC として扱う
  - 検証: `cd tests && python3 -m unittest test_tasks -k test_parse_acs`

## メモ

- 初回の試行（各ケース 1 回）で、task・setup の with 側 3 回中 2 回がプラグインのディレクトリへ cd して CLI を実行した。`tri` はカレントディレクトリをプロジェクトとして扱い、配布されたプラグイン自体も docs/goal.md を持つので、別のプロジェクトを操作しうる
- 同じく setup の試行で、`migrate` がフォルダ形式のフェーズの機能を `## 検証記録` の下に入れ、AC が読まれなかった（エージェントが手で直していた）
- スキル側のエージェントは Docs を Edit ではなく Bash（python の置換）で編集することが多い。Edit ツールの呼び出しを数える採点器は使えず、最終ファイルの内容で判定する
- この Task の AC1（手動）の確認方法に `claude plugin eval` と書いたら、`task verify` がそれを実行しようとした。手動かどうかをコマンドの有無で判定していたため。「手動」で始まる検証行はコマンドとして扱わないよう直した
- eval の子セッションはサンドボックスに bubblewrap と socat が要る（無いと Bash を使うケースが 0 点になる）

## 検証記録

- 2026-10-17 11:12 AC1 PASS 手動: 最終版の全ケース×あり/なし×3回（overallScore 0.93・meanDelta 0.30、発火 9/9・誤発火 0/6）と修正前後の切り分け実行の aggregate-result tree=6dc8f42526dd
  .json を docs/skill-evaluation.md の表と突き合わせた。プラグインへの cd は修正後 0/39
- 2026-10-17 11:12 AC2 PASS `cd tests && python3 -m unittest test_lifecycle -k test_apply` → exit 0 「OK」 tree=6dc8f42526dd
- 2026-10-17 11:12 AC3 PASS `cd tests && python3 -m unittest test_plugin` → exit 0 「OK」 tree=6dc8f42526dd
- 2026-10-17 11:12 AC4 PASS `cd tests && python3 -m unittest test_tasks -k test_parse_acs` → exit 0 「OK」 tree=6dc8f42526dd
