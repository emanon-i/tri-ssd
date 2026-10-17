# Tri-SSD

AI コーディングエージェントによる長期開発のための、知識ライフサイクル管理とコンテキスト最適化のハーネス（Claude Code プラグイン）。

- **知識を寿命で分ける**: Goal（目的）・Docs（あるべき状態）・Tasks（差分を解消する作業。作業メモも Task の中）・引き継ぎ（上書きで1つ）・CHANGELOG（変更履歴）。溜まり続ける置き場を作らない
- **必要な部分だけ読む**: Task・ID・コードパスを起点に、読むべきセクションだけを知識グラフから選ぶ（理由・予算・省略の明示付き）
- **文書を腐らせない**: 参照切れ・履歴汚染・重複・肥大化を機械的に検出し、Docs を現在形のまま保つ
- **完了を証拠で決める**: 受け入れ条件ごとの検証証跡と、証跡取得後のコード変更検知による完了ゲート

設計の詳細は [docs/knowledge-model.md](docs/knowledge-model.md)（置き場と寿命）・[docs/writing-rules.md](docs/writing-rules.md)（書き方）・[docs/architecture.md](docs/architecture.md)（仕組み）・[docs/evaluation.md](docs/evaluation.md)（実測）。

## インストール

```bash
/plugin marketplace add emanon-i/tri-ssd
/plugin install tri-ssd@emanon-i-tri-ssd
```

必要なもの: Python 3.9 以上（動作を確認した下限。標準ライブラリのみ）と git。外部サービス・追加パッケージは不要。

| Skill | 使う場面 |
|---|---|
| `/tri-ssd:task` | 実装・バグ修正・Task の作成・検証・完了・作業の再開・作業メモ・引き継ぎ |
| `/tri-ssd:docs` | Goal・仕様・設計の作成と改訂、判断の記録 |
| `/tri-ssd:setup` | 初期化・既存プロジェクトへの導入・旧版からの移行 |

Skill は会話の内容から自動で選ばれる。名前を覚える必要はない。
プラグインは2つのフックを登録する: セッション開始時に現在位置を文脈へ入れ、`docs/` の Markdown を編集した直後に検査結果を返す。Tri-SSD プロジェクト以外や Python が見つからない環境では何もしない。

## 初期化

```bash
python3 <plugin>/scripts/tri.py init --name "My App"
```

または Claude に「Tri-SSD を始めたい」と伝える（setup スキル）。作成されるもの:

```text
docs/
  goal.md          # Goal: 目的・成功状態・原則・やらないこと（常に読まれるので短く）
  tasks/           # Task（完了すると tasks/_done/ へ）
  notes/handoff.md # 引き継ぎ（上書き。現在位置は常に1つ）
CHANGELOG.md       # 意味のある変更の履歴（Keep a Changelog）
.tri-ssd/          # 個人用の引き継ぎ（自身の .gitignore で git 管理外）
```

Docs は `docs/` 配下に自由に置く（例: `requirements.md`・`architecture.md`・`api.md`・`adr/`）。分類の基準は更新契機と寿命。
どの作業でも守る短い規則（例: 全クエリを利用者 ID で絞る）は、エージェントが常に読む指示ファイル（`CLAUDE.md`・`AGENTS.md`）に1規則1行で書く。

## 日常の使い方

普段は Claude に依頼するだけでよい（「T-0003 をやって」「この仕様を変えたい」「今日はここまで」）。Skill が以下の CLI を使う。

| 場面 | コマンド |
|---|---|
| 現在位置 | `tri status` |
| 作業に必要な文脈 | `tri context T-0003 --emit`（`REQ-0004`・`docs/x.md#見出し`・`src/path.py` も起点にできる） |
| 差分の一覧 | `tri gaps`（Docs の `（計画: T-nnnn）`・`（未確定）` 等と、Task から参照されていない REQ） |
| Task | `tri task new "題" --refs REQ-0004 --code src/search/` → `task verify` → `task report` → `task close` |
| 変更の影響 | `tri impact --git`（作業差分から見直すべき Docs と関係 Task） |
| 検査 | `tri check [--changed]` |
| 変更履歴 | `tri log Changed "何を・なぜ" --refs T-0003` |
| 引き継ぎ | `tri handoff -`（標準入力から。上書き） |

`tri` は `python3 <plugin>/scripts/tri.py` の略。プロジェクトルートで実行する（または `--root`）。

典型的な1サイクル:

1. あるべき状態を Docs に書く（未実装の記述には `（計画: T-nnnn）`）
2. `task new` で差分を Task にし、受け入れ条件と `検証:` コマンドを書く
3. `context` で必要な節だけ読んで実装し、発見は Task の `## メモ` に書く
4. Docs を実装後の状態に置き換え（計画マーカーを外す）、`task verify` → `task close`
5. 意味のある変更を `log`、`handoff` で引き継ぐ（メモは Task と一緒に退場する）

## 既存プロジェクトへの導入

1. `tri init`（既存ファイルは上書きしない。既存の `docs/*.md` はそのまま Docs になる）
2. README と既存文書から `docs/goal.md` を書く
3. `tri check` で既存文書の参照切れ・履歴汚染・重複を確認し、触る文書から直す
4. これから変更する範囲だけ、守るべき状態を Docs に書き（要求は `## REQ-nnnn` 見出し、構成文書は frontmatter `code:`）、Task を作る

全部を最初に文書化しない。コードが正となる詳細は Docs に書き写さない。

## 旧 Tri-SSD からの移行

v5 以前（`docs/l1_requirements/`・`l2_foundation/`・`l3_phases/`）のプロジェクトは移行コマンドで変換する。

```bash
tri migrate          # ドライラン（計画の表示のみ）
tri migrate --apply  # 実行
tri check            # 参照切れの確認
```

| 旧 | 新 |
|---|---|
| `l1_requirements/vision.md` | `docs/goal.md`（REQ はそのまま有効。大きければ REQ を `docs/requirements.md` へ移す） |
| `l2_foundation/**` | `docs/design/**` |
| `l3_phases/PH-*`（フォルダ形式は1ファイルに統合） | `docs/tasks/`（planned→open・in_progress→active・done は `_done/`） |
| `l3_phases/_archive/**` | `docs/tasks/_done/**` |
| `l0_ideas/**` | `docs/notes/ideas/**`（移行時に一度見直し、Task・Docs にするか削除する） |
| `<!-- TODO: 要確認 -->`・`（未確認…）` | `（未確定）`・`（未検証）` |

PH・F の ID は互換のため引き続き有効。新しい Task は `T-nnnn`。旧スキルとの対応:

| 旧スキル | 新しい手段 |
|---|---|
| `/init-tri-ssd` | setup スキル（`tri init`） |
| `/gen-l1`・`/gen-l2`・`/gen-interface`・`/gen-data`・`/gen-doc` | docs スキル（種類別ガイドは `skills/docs/references/doc-guide.md`） |
| `/gen-l3`・`/reshape-l3` | task スキル（`tri task new`。フェーズの代わりに検証可能な Task） |
| `/gen-code` | task スキル（`context` → 実装 → `task verify`） |
| `/archive-l3` | `tri task close`（ゲート・アーカイブ）＋ `tri log` |
| `/review-tri-ssd` | `tri check`・`tri gaps`・`tri status` |
| `/next-tri-ssd` | SessionStart フックと `tri status` |

## 開発

```bash
python3 -m unittest discover -s tests -p "test_*.py"   # 自動テスト
python3 tests/simulate.py --cycles 10                   # 長期運用シミュレーション
python3 tests/eval_context.py                           # コンテキスト効率の実測
```

このリポジトリ自身も Tri-SSD で管理している（`docs/goal.md`・`docs/tasks/`）。変更履歴は [CHANGELOG.md](CHANGELOG.md)。

## ライセンス

MIT
