# Tri-SSD

AI コーディングエージェントによる長期開発のための、知識ライフサイクル管理とコンテキスト最適化のハーネス。Claude Code・Codex・Pi・OpenCode が同じ Skill と CLI `tri` を使う。

- **知識を寿命で分ける**: Goal（目的）・Docs（あるべき状態）・Tasks（差分を解消する作業。作業メモも Task の中）・NOTES（現在位置。上書きで1つ）・CHANGELOG（変更履歴）。溜まり続ける置き場を作らない
- **必要な部分だけ読む**: Task・ID・コードパスを起点に、読むべきセクションだけを知識グラフから選ぶ（理由・予算・省略の明示付き）
- **文書を腐らせない**: 参照切れ・履歴汚染・重複・肥大化を機械的に検出し、Docs を現在形のまま保つ
- **完了を証拠で決める**: 受け入れ条件ごとの検証証跡と、証跡取得後のコード変更検知による完了ゲート

設計の詳細は [docs/knowledge-model.md](docs/knowledge-model.md)（置き場と寿命）・[docs/writing-rules.md](docs/writing-rules.md)（書き方）・[docs/architecture.md](docs/architecture.md)（仕組み）・[docs/evaluation.md](docs/evaluation.md)・[docs/skill-evaluation.md](docs/skill-evaluation.md)（実測）。

## インストール

必要なもの: Python 3.9 以上（動作を確認した下限。標準ライブラリのみ）と git。外部サービス・追加パッケージは不要。

```bash
git clone https://github.com/emanon-i/tri-ssd
cd tri-ssd
python scripts/install.py    # python が無ければ python3
```

1 回のコマンドで、CLI と Skill を同じ版で置く。リンクは作らず写しを置き、再実行すると同じ状態になる（更新も同じコマンド）。

| オプション（既定） | 置くもの |
|---|---|
| `--prefix`（`~/.local/share/tri-ssd`） | CLI の実行一式 |
| `--bin`（`~/.local/bin`） | 起動スクリプト `tri`（Windows では `tri.cmd` も）。PATH の通ったフォルダを指定する |
| `--skills`（`~/.agents/skills`。複数可） | Skill `tri-ssd-setup`・`tri-ssd-task`・`tri-ssd-docs` |

Codex・Pi・OpenCode は `~/.agents/skills` を読む。Claude Code は `~/.claude/skills` を読むので、`--skills ~/.agents/skills --skills ~/.claude/skills` と2か所に写すか、`~/.claude/skills` から `~/.agents/skills` の各 Skill へリンクを張る。

Claude Code では、`~/.claude/settings.json` にフックを登録する（既に `hooks` があれば各イベントの配列に足す）。セッション開始時に現在位置を文脈へ入れ、`docs/` の Markdown を編集した直後に検査結果を返す。Tri-SSD プロジェクト以外と `tri` が無い環境では何もしない。

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume|clear|compact",
        "hooks": [{ "type": "command", "command": "tri status --hook 2>/dev/null || true", "timeout": 30 }]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [{ "type": "command", "command": "tri check --hook 2>/dev/null || true", "timeout": 30 }]
      }
    ]
  }
}
```

| Skill | 使う場面 |
|---|---|
| `tri-ssd-task` | 実装・バグ修正・Task の作成・検証・完了・作業の再開・作業メモ・NOTES |
| `tri-ssd-docs` | Goal・仕様・設計の作成と改訂、判断の記録 |
| `tri-ssd-setup` | 初期化・既存プロジェクトへの導入・旧版からの移行 |

Skill は会話の内容から自動で選ばれる。名前を覚える必要はない。

## 初期化

```bash
tri init --name "My App"
```

またはエージェントに「Tri-SSD を始めたい」と伝える（tri-ssd-setup スキル）。`init` は `docs/goal.md` と `CHANGELOG.md` を作る。ほかは最初に使うときに作られる。

```text
CHANGELOG.md       # 何をなぜ変えたか（Keep a Changelog）
NOTES.md           # 現在位置・次にやること・未決事項（上書き。tri notes で書く）
docs/              # あるべき状態の文書
  goal.md          # Goal: 目的・成功状態・原則・やらないこと（常に読まれるので短く）
tasks/             # Task。1 件 1 ファイル
  archive/         # 完了・中止した Task
```

Docs は `docs/` 配下に自由に置く（例: `requirements.md`・`architecture.md`・`api.md`）。分類の基準は更新契機と寿命。判断が分かれた箇所には、その文書に `## 選定理由と却下案` の節を置く。
Tri-SSD が読むのは `docs/`・`tasks/`・`NOTES.md`・`CHANGELOG.md` だけ。一時的な調査は git 管理外の `tmp/` などに置く。
どの作業でも守る短い規則（例: 全クエリを利用者 ID で絞る）は、エージェントが常に読む指示ファイル（`CLAUDE.md`・`AGENTS.md`）に1規則1行で書く。

## 日常の使い方

普段はエージェントに依頼するだけでよい（「T-0003 をやって」「この仕様を変えたい」「今日はここまで」）。Skill が以下の CLI を使う。

| 場面 | コマンド |
|---|---|
| 現在位置 | `tri status` |
| 作業に必要な文脈 | `tri context T-0003 --emit`（`REQ-0004`・`docs/x.md#見出し`・`src/path.py` も起点にできる） |
| 差分の一覧 | `tri gaps`（Docs の `（計画: T-nnnn）`・`（未確定）` 等と、Task から参照されていない REQ） |
| Task | `tri task new "題" --refs REQ-0004 --code src/search/` → `task verify` → `task report` → `task close` |
| 変更の影響 | `tri impact --git`（作業差分から見直すべき Docs と関係 Task） |
| 検査 | `tri check [--changed]` |
| 変更履歴 | `tri log Changed "何を・なぜ" --refs T-0003` |
| 現在位置の記録 | `tri notes -`（標準入力から。`NOTES.md` を上書き） |

`tri` はプロジェクトルートで実行する（または `--root`）。Skill が参照する規約は `tri guide knowledge-model`・`tri guide writing-rules` で読める。

典型的な1サイクル:

1. あるべき状態を Docs に書く（未実装の記述には `（計画: T-nnnn）`）
2. `task new` で差分を Task にし、受け入れ条件と `検証:` コマンドを書く
3. `context` で必要な節だけ読んで実装し、発見は Task の `## メモ` に書く
4. Docs を実装後の状態に置き換え（計画マーカーを外す）、`task verify` → `task close`
5. 意味のある変更を `log`、現在位置を `notes` で残す（メモは Task と一緒に退場する）

## 既存プロジェクトへの導入

1. `tri init`（既存ファイルは上書きしない。既存の `docs/*.md` はそのまま Docs になる）
2. README と既存文書から `docs/goal.md` を書く
3. `tri check` で既存文書の参照切れ・履歴汚染・重複を確認し、触る文書から直す
4. これから変更する範囲だけ、守るべき状態を Docs に書き（要求は `## REQ-nnnn` 見出し、構成文書は frontmatter `code:`）、Task を作る

全部を最初に文書化しない。コードが正となる詳細は Docs に書き写さない。

## 旧 Tri-SSD からの移行

v5 以前（`docs/l1_requirements/`・`l2_foundation/`・`l3_phases/`）と v6（`docs/tasks/`・`docs/notes/`・`.tri-ssd/`）のプロジェクトは移行コマンドで変換する。

```bash
tri migrate          # ドライラン（計画の表示のみ）
tri migrate --apply  # 実行
tri check            # 参照切れの確認
```

| 旧 | 新 |
|---|---|
| `l1_requirements/vision.md` | `docs/goal.md`（REQ はそのまま有効。大きければ REQ を `docs/requirements.md` へ移す） |
| `l2_foundation/**` | `docs/design/**` |
| `l3_phases/PH-*`（フォルダ形式は1ファイルに統合） | `tasks/`（planned→open・in_progress→active・done は `tasks/archive/`） |
| `l3_phases/_archive/**` | `tasks/archive/**` |
| `docs/tasks/**`（v6） | `tasks/**`（`_done/` は `archive/`） |
| `docs/notes/handoff.md`（v6） | `NOTES.md` |
| `l0_ideas/**`・`docs/notes/` のその他 | `tmp/` の下（Tri-SSD は読まない。移行時に一度見直し、Task・Docs にするか削除する） |
| `.tri-ssd/`（v6） | 中身が無ければ削除。あれば残すので、`NOTES.md` へ移すか削除する |
| `<!-- TODO: 要確認 -->`・`（未確認…）` | `（未確定）`・`（未検証）` |

PH・F の ID は互換のため引き続き有効。新しい Task は `T-nnnn`。旧スキルとの対応:

| 旧スキル | 新しい手段 |
|---|---|
| `/init-tri-ssd` | tri-ssd-setup スキル（`tri init`） |
| `/gen-l1`・`/gen-l2`・`/gen-interface`・`/gen-data`・`/gen-doc` | tri-ssd-docs スキル（種類別ガイドは `skills/tri-ssd-docs/references/doc-guide.md`） |
| `/gen-l3`・`/reshape-l3` | tri-ssd-task スキル（`tri task new`。フェーズの代わりに検証可能な Task） |
| `/gen-code` | tri-ssd-task スキル（`context` → 実装 → `task verify`） |
| `/archive-l3` | `tri task close`（ゲート・アーカイブ）＋ `tri log` |
| `/review-tri-ssd` | `tri check`・`tri gaps`・`tri status` |
| `/next-tri-ssd` | Claude Code の SessionStart フックと `tri status` |

## 開発

```bash
python3 -m unittest discover -s tests -p "test_*.py"   # 自動テスト
python3 tests/simulate.py --cycles 10                   # 長期運用シミュレーション
python3 tests/eval_context.py                           # コンテキスト効率の実測
python3 scripts/install.py                              # 作業ツリーを導入（Skill の評価は PATH 上の tri を使う）
python3 evals/trigger/build.py                          # 発火評価のケースを生成（evals/trigger/queries.json から）
claude plugin eval . --tag trigger --ablation none --scaffold --allow-tools Bash Write Edit   # Skill の発火（有料）
claude plugin eval . --tag heldout --scaffold --allow-tools Bash Write Edit                   # Skill の成果を Skill 無しと比較（有料）
```

このリポジトリ自身も Tri-SSD で管理している（`docs/goal.md`・`tasks/`・`NOTES.md`）。`.claude-plugin/plugin.json` は `claude plugin eval` で Skill を束ねるためだけにあり、導入には使わない。変更履歴は [CHANGELOG.md](CHANGELOG.md)。

## ライセンス

MIT
