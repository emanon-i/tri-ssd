---
description: Tri-SSD プロジェクト（docs/goal.md がある）で開発作業を進める。作業開始時に現在位置と Task に必要な文脈だけを CLI で取得し、仕様と実装の差分を Task にし、受け入れ条件を検証証跡付きで満たして完了させる。
when_to_use: 実装して・続きをやって・次は何をする？・T-0003 をやって・このバグを直して・この仕様を実装して・Task を作って・検証して・完了にして・作業を再開して、と言われたとき。Tri-SSD のプロジェクトでコードを変更する作業全般。英語では implement / continue / next task / fix this / close the task。文書の改訂だけなら docs、メモ・引き継ぎだけなら note、導入・移行は setup を使う。
argument-hint: "[T-xxxx | 作業内容] - 対象 Task または依頼内容（省略時は現在位置から選ぶ）"
allowed-tools: Read, Edit, Write, Glob, Grep, Bash
---

# Task を進める

<tri_ssd_context>
Tri-SSD: Goal（docs/goal.md）・Docs（docs/ のあるべき状態）・Tasks（docs/tasks/ 差分を解消する検証可能な作業）・Notes（docs/notes/・.tri-ssd/notes/ 一時情報）・CHANGELOG（意味のある変更の履歴）。
決定的処理は CLI `python3 "${CLAUDE_SKILL_DIR}/../../scripts/tri.py"`（以下 `tri`）で行う。文書を開く前に `tri context` で必要なセクションだけを取得する。
置き場・寿命の判断に迷ったら `${CLAUDE_SKILL_DIR}/../../docs/knowledge-model.md` を読むこと。
</tri_ssd_context>

<avoid_over_engineering>
- docs/ を Glob・Read で総なめしない。`tri context` の出力で足りなければ、出力が示す候補だけを読む
- Task に書かれていない機能・「念のため」の処理を足さない
- 差分を何でも Task にしない（下の分類表）。Task を細かく割りすぎない（1 Task = 1つの観測可能な状態変化）
- 作業中の気づきはまず Note に書く。Docs へは検証済みで今後も真なものだけを昇格する
</avoid_over_engineering>

## 手順

### 1. 現在位置を知る

セッション開始時のフックが状況を注入していればそれを使う。無ければ:

```bash
tri status      # Goal・進行中 Task と AC 進捗・引き継ぎ・検査結果
```

対象 Task の決め方: ユーザーが指定 → それ（引き継ぎの順番より優先。他の active はそのままでよい）。無ければ `active` → 引き継ぎが示す Task → `open` の若い番号。
該当が無く依頼内容があるときは手順 3 で Task を作る。

### 2. 文脈を取得する

```bash
tri task start T-xxxx           # open → active
tri context T-xxxx --emit       # Task 全文・Goal・参照先の仕様・関連ノートの本文
```

- 出力の「選定」と本文を読んで作業を始める。「予算外で省略」「関連の弱い候補」は、Task の目的に関係しそうなものだけ Read する
- 「目的の状態」に出てくる語（例: 「関連データ」）の定義が選定に無ければ、選定済み文書の見出し一覧（`grep '^#' docs/x.md`）から該当節を探して Read する。docs/ 全体を総なめしない
- 関連コードは出力の「関連コード」から辿る。空なら `tri context src/候補のディレクトリ --emit --no-goal` か、選定された Docs が名指しするパスから探す
- 同じセッションで 2 回目以降の context は `--no-goal`（Goal は既に読んでいる）

<self_healing_graph>
context に含まれなかったが作業に必要だった Docs の節やコードを見つけたら、次回から自動で取得されるように関係を書き足す:
- Docs の節: Task の frontmatter `refs:` に `docs/x.md#見出し` を追加し、恒久的な依存なら仕様側の本文にも ID かリンクを書く（例: 「物理削除の整合性は [整合性](data.md#整合性) に従う」）
- コード: 仕様の本文で実装箇所をパスで名指しする（`` `src/worker/trash.py` ``）か、コードのコメントに ID を書く（`# REQ-0011`）
</self_healing_graph>

### 3. 差分を Task にする（Task が無いとき・新たな差分を見つけたとき）

`tri gaps` で Docs の差分マーカーと未追跡の REQ を確認し、コードと照合して分類する:

| 状況 | 扱い |
|---|---|
| Docs が正しく、コードが未達 | Task を作り、Docs の該当記述に `（計画: T-nnnn）` を付ける |
| Docs が誤り | docs スキルの手順で Docs を直す |
| 設計が未確定 / 意図的に後回し / 前提が未検証 | Docs に `（未確定）` / `（保留）` / `（未検証）` を付ける。必要なら Note に判断材料を残す |

```bash
tri task new "Tag search" --refs REQ-0004 docs/search.md#タグ検索 --code src/search/ --goal "完了時に成立している状態"
tri task new "タグ検索" --slug tag-search ...   # 題が日本語ならファイル名用に --slug（ファイル名は後で変えてもよい）
```

作成したファイルの `## 受け入れ条件` を書く。AC の規則は1つ: **「目的の状態のどの要素が欠けても、少なくとも1つの AC が必ず落ちる」を満たす最小の数**。1つの AC で複数の要素を確かめてよい。

```markdown
- [ ] AC1: AND 条件で全タグを持つブックマークだけが返る
  - 検証: `python3 -m pytest tests/test_search.py -k and_mode`
- [ ] AC2: 補完候補が使用回数順に並ぶ
  - 検証: 手動: タグ 20 個の環境で入力 "py" の候補を確認
```

- 他の確認が通れば論理的に通るはずの確認は AC にしない。網羅的なテストを足すのは通常の開発作業で、AC にはしない
- コマンドで検証できる AC はコマンドにする（手動は自動化できないものだけ）
- 各 AC の検証コマンドはその AC だけを確かめる粒度にする（テスト名・`-k` で絞る）。広すぎると無関係な失敗で FAIL になる
- 既存 Task の AC で欠けても落ちない要素を見つけたら、AC を追加または広げ、そのことを完了報告に書く
- 方法の選択で判断が分かれたときだけ、Task に `## 判断` 節を作り「選んだ方法・やめた案・理由」を1〜3行書く（報告に載る）

### 4. 実装する

- 既存コードのパターンに合わせる。Docs の契約（やらないこと・性能予算）を守る
- 実装中の発見・仮説は `tri note add "内容" --task T-xxxx` に記録する
- 前提が崩れた（Docs の設計が成り立たない）ら実装を止め、Docs の見直しをユーザーに提案する
- 「目的の状態」の一部がこの Task では実現できないと分かったら、黙って閉じない。実現できる範囲に目的の状態を書き直し、残りは新しい Task にする（Docs の該当記述には `（計画: T-nnnn）`）
- 他の進行中 Task の範囲（同じテーブル・同じモジュール）に触れる必要があれば、最小限にとどめ、`tri note add "..." --task <相手のID>` で相手側に知らせる

### 5. Docs を実装後の状態にする

- この Task で満たした記述の `（計画: T-xxxx）` を外す（外さないと完了ゲートを通らない）。マーカーが無ければ何もしない
- `tri impact --git` で見直すべき Docs を確認し、実装と食い違う記述は docs スキルの更新プロトコルで直す
- 検証済みで今後も真な発見（外部仕様・制約）は Note から Docs へ昇格する

### 6. 検証する

```bash
tri task verify T-xxxx                                  # 検証: のコマンドを実行し証跡を追記
tri task verify T-xxxx --against-base                   # 全部通ったら一度: 着手時点のコードでも実行し、そこでは落ちるか確かめる
tri task record T-xxxx AC2 pass --note "確認した内容"     # 手動の AC
```

`--against-base` で「着手時点 PASS」と出た AC は、変更について何も確かめていない。振る舞いを変えない Task（リファクタ等）でなければ、検証コマンドを直す。

<verification_judgment>
PASS は「コマンドが成功した」ことしか意味しない。各 AC について、検証コマンドが AC の文言どおりの振る舞いを実際に確かめているかを確認する。
確かめていなければ、テストを直すか AC の検証手段を直してから再検証する。証跡や AC のチェックを手で書き換えない。
完了の前に、「目的の状態」の各要素がどれかの AC で検証されているかを確認する（ゲートはこの対応を機械では判定できない）。
</verification_judgment>

### 7. 完了する

```bash
tri task report T-xxxx    # 人間向けの報告（目的・満たす仕様・検証・判断・変更・CHANGELOG）。close の前に見て、欠けを直す
tri task close T-xxxx
```

- ゲート未達の項目が表示されたら解消して再実行する。`--force "理由"` はユーザーが了承したときだけ使う
- 利用者に見える機能の追加・修正、または仕様・設計の意味のある変更があれば `tri log Added|Changed|Fixed "何を・なぜ" --refs T-xxxx`（内部の作業経過は記録しない）
- close が「書かれていない依存の候補」を示したら、この Task で実際に必要だったものだけを refs や仕様本文のリンクとして書き足す（次回から context に入る）
- close が示した関連ノートを note スキルの基準で整理する（昇格・削除）
- 完了した Task（`_done/`）は履歴。後の変更で検証コマンドが古くなっても直さない

### 8. 中断・セッション終了

```bash
tri note handoff - <<'EOF'
- 現在位置: T-0005 の AC1 PASS、AC2 未着手
- 次の一手: AC2（補完の並び順）
- 未解決: use_count 列を足すかユーザー判断待ち
EOF
```

上書きされる（過去の引き継ぎは残らない）。複数行は `-` で標準入力から渡す。

## 完了後の案内

- `tri task report` の内容（何を・なぜ・どう確かめたか・判断・Goal のどこに近づいたか）。ユーザーはこれを読んで判断し、納得できないときだけコードを見る
- 「着手時点でも通る」と出た検証が残っていれば、その理由
- 次の候補（`tri status` の進行中 Task、または `tri gaps` の差分）

## エラーケース

| ケース | 対応 |
|---|---|
| docs/goal.md も docs/tasks/ も無い | setup スキルで初期化・導入する |
| `tri context` が終了コード 3 | 必須セクションが予算を超えた。省略一覧を読むか `--budget` を増やす |
| `task verify` が FAIL | 実装を直して再検証する。3 回続けて同じ失敗なら原因と選択肢をユーザーに報告する |
| ゲートが「検証後にコードが変更」 | `tri task verify` を再実行する |
| `python3` が無い | `python` / `py` で同じコマンドを実行する |
