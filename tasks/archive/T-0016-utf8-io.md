---
id: T-0016
status: done
refs: []
code: [scripts/tri.py, scripts/trissd/]
created: 2026-10-19
base: 2c49cd56a00e
closed: 2026-10-19
---
# T-0016 Windows で日本語の標準入出力と子プロセス出力を UTF-8 で扱う

## 目的の状態

ロケールが UTF-8 でない環境（Windows の cp932）でも、`tri` は標準入力（`handoff -` とフックの JSON）・標準出力・git と検証コマンドの出力を UTF-8 で扱い、`PYTHONUTF8` なしで日本語を失わず落ちない。Windows でも unittest がすべて通る

## 受け入れ条件

- AC1: 入出力の既定が UTF-8 でない環境で、`handoff -` に渡した日本語がそのまま引き継ぎに書かれる
  - 検証: `python -m unittest discover -s tests -p test_io_encoding.py -k handoff`
- AC2: 同じ環境で、フックの JSON の日本語の cwd を読んで現在位置を返す
  - 検証: `python -m unittest discover -s tests -p test_io_encoding.py -k hook`
- AC3: 同じ環境で、検証コマンドが UTF-8 で出した日本語を検証記録に残す
  - 検証: `python -m unittest discover -s tests -p test_io_encoding.py -k verify`
- AC4: Windows で unittest がすべて通る（migrate の報告のパス区切り・シミュレーションの検証コマンド）
  - 検証: `python -m unittest discover -s tests -p "test_*.py"`

## メモ

- 標準入力は Windows では cp932・surrogateescape で開かれ、UTF-8 の日本語が孤立サロゲートになって書き込みで落ちていた
- この環境の `python3` は Microsoft Store のスタブで動かない。AC の検証は `python` で書いた

## 検証記録

- 2026-10-19 23:10 AC1 PASS `python -m unittest discover -s tests -p test_io_encoding.py -k handoff` → exit 0 「OK」 tree=1cdcead46f2b
- 2026-10-19 23:10 AC2 PASS `python -m unittest discover -s tests -p test_io_encoding.py -k hook` → exit 0 「OK」 tree=1cdcead46f2b
- 2026-10-19 23:10 AC3 PASS `python -m unittest discover -s tests -p test_io_encoding.py -k verify` → exit 0 「OK」 tree=1cdcead46f2b
- 2026-10-19 23:10 AC4 PASS `python -m unittest discover -s tests -p "test_*.py"` → exit 0 「OK」 tree=1cdcead46f2b
