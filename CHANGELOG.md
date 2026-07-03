# Changelog

Tri-SSD (Tri-Layer Slice Spec Driven) フレームワークの変更履歴です。

形式は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に準拠しています。

## [5.0.0] - 2026-07-03

### Added

- **スキル4件を新設**（8→12スキル）
  - `/next-tri-ssd` — 工程のオーケストレーター。docs/ の状態から現在地を決定的に判定し、次の一手を理由付きで提案・実行（ワークフローの順序を覚えなくてよい）
  - `/gen-doc` — 配置のオーケストレーター。書きたい情報を layer-rules の判定で振り分け（画面→gen-interface / データ→gen-data へ委譲。機能契約 `features/`・教訓 `lessons.md`・検証実証ログ `validation/`・用語集は自ら生成）
  - `/gen-interface` — L2 インターフェース設計の深掘り → `interface.md`（画面一覧・画面遷移図（Mermaid stateDiagram-v2、ユーザー状態含む）・主要導線（操作→結果→応答/待ち時間フィードバック））
  - `/gen-data` — L2 データ設計の深掘り → `data.md`（概念モデル（erDiagram）・データライフサイクル（発生・更新頻度・増加ペース・保持/ローテーション・削除）・整合性の判断基準。カラム定義は書かない＝正は実装コード）
- **`/review-tri-ssd` スキルを新設** — 整合性検証と進捗サマリ（読み取り専用）
  - ID 整合性は `scripts/validate_ids.py` で機械的に検証（dangling 参照・重複定義・status と検証記録の突合）
  - 要件の網羅性・仕様と実装の乖離を読み合わせで確認。ドキュメント衛生（未解決の分離ポインタ・300行超過・未振り分けの印）も検査
- **規約文書2件を新設**（SSOT の分離: 配置 = layer-rules / 書き方 = writing-rules）
  - `docs/layer-rules.md` — 配置決定表・判定フロー（Q0〜Q4）・曖昧ケースの裁定・ファイル分割ルール・適正粒度基準。判定軸は「更新トリガー」（L1=実現手段を決めなくても真、L2=フェーズ完了後も真、L3=完了で腐る）
  - `docs/writing-rules.md` — 文章原則（1文1事実・修飾語禁止）・構造化（表>箇条書き>散文）・図の Mermaid 統一・機械契約マーカー表（TODO / `（未確認…）` 印 / `検証:` 行 / `depends:`）
- **共有スクリプト基盤**（プラグインルート `scripts/`）
  - `next_id.py` を一本化（gen-l1 / gen-l3 の重複コピーを削除。`_archive/` 含む走査＝永久欠番）
  - `validate_ids.py` — ID 整合性検証と進捗サマリ（フォルダ形式 PH・L2 複数ファイル対応）
  - `doc_graph.py` — ID 参照から文書依存グラフを自動導出（維持コストゼロ）。`--focus <ID>` が「着手前に読むべき最小の文書集合」を返し、gen-code の段階的注入を決定的にする。任意 frontmatter `depends:` で文書間依存を補完可能
- **PH-0000 に「技術前提の事実検証（スパイク）」を追加**（環境構築5機能に続く第6の機能）
  - 計画全体が依存する未確認の前提（外部 API の実在・レート制限、核心処理の実現可否、ライブラリ制約）を実装前に最小の検証コード・実測で確認。前提の不成立も `PASS（前提不成立を確認、日付）` として成果扱い
  - 印のライフサイクル: gen-l2 が `（未確認・要検証）` 印を付与 → gen-l3 が検証場所を確定（PH-0000 スパイク or 該当フェーズの事前確認）→ gen-code が判明した事実を「確認済みの前提」へ昇格して印を外す
- **L1/L2/L3 テンプレートに YAML frontmatter を導入**
  - L1: `layer` / `product_type`（gui|cli|api|library|batch|data|doc|other）/ `updated`
  - L2: `layer` / `updated` / `depends`（任意）。L3: `id` / `status`（planned|in_progress|done）/ `requires` / `updated`
- **テンプレート新セクション**（いずれも任意・追加式で後方互換）
  - L1: 「原則」・「体験要件」（product_type 別）・「やらないこと」
  - L2: 「インターフェース仕様」・「確認済みの前提」・「設計判断の記録」・「データモデル」（erDiagram 例付き）・「エラー処理方針」・「運用」（省略可・記入判断基準付き）
  - L3: 「事前確認」（作業のみ。結果は L2 へ）・「検証記録」（事後証跡）・「完了サマリ」（archive 時に記入）
- **`/gen-code` を実装完了の門番に強化**
  - Phase 0（clarify）: 未解決 TODO・矛盾・検証手段の不足がある場合のみ質問（なければ質問ゼロ）。「事前確認」節の未チェック項目はここで実行
  - 機能契約の「やらないこと」を実装時の契約として遵守。L2 分離ファイルは依存グラフで関連分のみ読む
- **`/archive-l3` をフェーズ完了処理に拡張** — ゲート（全 F PASS 確認）・CHANGELOG 自動追記（出所は L3 完了サマリに一本化）・知見還元の提案（L1/L2/lessons.md へ、承認制）
- **`/init-tri-ssd` が docs/README.md（情報の在り処マップ）を生成**するように拡張

### Changed

- **L2 を複数ファイル構成に**（foundation.md をハブに、関心領域ごとのサブ文書を規模で分離: interface.md / data.md / features/ / validation/ / lessons.md / glossary.md。分離時は1行ポインタに置換）
- **`/split-l3` と `/merge-l3` を `/reshape-l3` に統合**（破壊的変更）
  - 1能力（インライン⇔フォルダの往復変換）・同一更新トリガーのため統合。変換方向は対象の形式から自動判定
  - split.py / merge.py を原文の行を保持する方式に改修（phase-template 準拠なら往復 diff ゼロを実測確認）
- **gen-l1 / gen-l2 / gen-l3 の出力テンプレートを「テンプレート＋記入判断基準」として `references/` に外出し**（段階的開示。本文には必須構造の要点と参照指示のみ）
- **既存8スキルの description / when_to_use の発火語彙を増強**（口語トリガー・英語表現・「〜のときは別スキル」の区別。新設4スキルは初版から適用）
- **図を Mermaid に統一**（構成図=flowchart / 遷移=stateDiagram-v2 / ER=erDiagram / 時系列=sequenceDiagram。ASCII 図を廃止）
- 全スキルの `<tri_ssd_context>` を3行の共通ブロックに縮小（レイヤー詳細の複製をやめ layer-rules.md への参照に置換）
- 検証結果の記録先を AC 行への追記から「検証記録」セクションに変更（Plan と事後証跡の分離）
- `.claude/rules/command-development.md` → `skill-development.md`（globs 修正。XML タグによる強指示の使い分けを明文化）
- CLAUDE.md / docs/plugin-development-guide.md を skills 形式の実態に全面改訂。三層モデル表の重複を解消（正は layer-rules.md）
- **内部品質**: リリース前に実行エージェント視点の多段レビュー（Codex＋サブエージェント計7体・3巡）と記載品質レビューを実施し、スキル間の受け渡し契約の矛盾（フォルダ形式の片側契約・初回実行判定・印のライフサイクル・完了条件の自己矛盾など30件超）と文章の不揃いを解消

### Fixed

- `.gitignore` に `__pycache__/`・`*.pyc` を追加し、混入していた `.pyc` を削除
- 引数を取らないスキルの `argument-hint: なし` を削除（規約は「引数がある場合」のみ記載）
- split / merge（v3 由来）の往復変換で見出し直後の空行が失われるバグを修正（`\s*$` が改行を跨いで消費していた）

### Migration（v4.0.0 からの移行）

| 旧 | 新 |
|----|----|
| `/split-l3 PH-xxxx` | `/reshape-l3 PH-xxxx`（方向は自動判定） |
| `/merge-l3 PH-xxxx` | `/reshape-l3 PH-xxxx`（同上） |
| 既存の vision.md / foundation.md / PH ファイル | そのまま有効（frontmatter・新セクションはすべて任意・追加式） |

## [4.0.0] - 2026-07-03

### Changed

- **コマンド（`commands/`）をスキル（`skills/`）へ全面移行**（破壊的変更・内部構造）
  - 各コマンド `commands/x.md` を `skills/x/SKILL.md` に再配置。呼び出し名 `/tri-ssd:x` は不変（利用者のコマンド名・ワークフローは変わらない）
  - `plugin.json` の `commands` 配列を削除（`skills/` は自動検出されるため宣言不要）
  - 位置引数を skills 準拠の `$ARGUMENTS` に変更（旧 `$1`。skills は位置引数が 0 始まりのため）
  - ※ v3.6.0 で廃止した「orchestrator スキル」とは別物。今回は全コマンド自体をスキル形式へ移行したもの
- **全スキルの `description` を「何をするか＋いつ使うか」形式に書き直し、`when_to_use` を追加**
  - Claude の description ベース自動発火の精度を向上（Skill オーサリングのベストプラクティスに準拠）

### Added

- **決定的処理を同梱スクリプト化**（`skills/*/scripts/*.py`。実行のみでコンテキストに読み込まれず、出力だけがトークンを消費）
  - `init-tri-ssd`: `init.py` — L0-L3 ディレクトリ + `.gitkeep` 作成（冪等・既存は上書きしない）
  - `gen-l1` / `gen-l3`: `next_id.py` — 既存 ID 走査 → 連番採番（採番ミス防止）
  - `split-l3` / `merge-l3`: `split.py` / `merge.py` — インライン⇔フォルダの相互変換（往復可能・チェック状態 `[x]` 保持・改行 LF 固定でOS非依存）
  - `archive-l3`: `archive.py` — 完了フェーズを `_archive/` へ移動
  - `python3` が無い環境では `python` / `py`、それも不可なら各 SKILL.md の「フォールバック」手順で手作業

## [3.6.0] - 2026-03-23

### Added

- **`/archive-l3` コマンド** - 完了したL3フェーズを `_archive/` に移動
  - L3ドキュメントは実装完了後に陳腐化するため、アクティブなディレクトリをクリーンに保つ
  - 引数なしで全フェーズ一覧表示、PH-ID指定で個別アーカイブ
- **L3 受け入れ条件に検証手段（`- 検証:`）サブ行を導入**
  - 各ACにエージェントが自律検証可能な手段を明示（テスト名、コマンド、目視確認）
  - 省略可（省略時はテストで確認がデフォルト）、後方互換あり

### Changed

- **ID形式をタイムスタンプベースから連番に変更**
  - 旧: `PREFIX-YYYYMMDD-nnn`（例: REQ-20250203-001）
  - 新: `PREFIX-nnnn`（例: REQ-0001）
  - 対象: REQ, PH, F すべてのプレフィックス
  - ID採番ロジックを簡素化（日時取得ステップを削除）
- **`/gen-l2`**: 出力テンプレートにセクション5「テスト・検証戦略」を追加（省略可）
  - テストフレームワーク、検証ツール、カバレッジ基準を定義する場所を提供
- **`/gen-l3`**: Step 3 に検証手段の種類テーブルと具体例を追加
  - テスト / コマンド実行 / 目視確認の3種類を定義
- **`/gen-code`**: 検証手段を活用した検証ループに拡張
  - Phase 2: AC→テストケース表に検証手段列を追加
  - Phase 5: コマンド検証（Bash実行）を検証ループに追加
  - Phase 6: 検証証跡をL3ドキュメントに記録
- `/gen-code` の完了後案内を `/done` から `/archive-l3` に変更
- `/gen-l3` の完了後案内に `/archive-l3` を追加
- `/merge-l3` からステータス集約ロジックを削除
- `/split-l3` からステータス継承ロジックを削除

### Removed

- **スキル機能（`tri-ssd-orchestrator`）を廃止**
  - 実運用で使われないことが判明。スキルの役割（ワークフロー統括・レイヤースキップ防止）は各コマンドで代替済み
  - `skills/` ディレクトリ、`.claude/rules/skill-development.md` を削除
  - `plugin.json` から `skills` フィールドを削除
  - `docs/plugin-development-guide.md` からスキル設計パターンセクションを削除
- **`status: wip|done` フロントマターフィールドを廃止**
  - 実運用で有用でないことが判明。L3の完了はアーカイブで表現
  - 全コマンド・テンプレートから status 参照を除去
- **`/done` コマンドを廃止** - status フィールド廃止に伴い不要に
- **`/status` コマンドを廃止** - status フィールド廃止に伴い不要に

## [3.2.1] - 2026-02-21

### Fixed

- **README.md を v3.x に全面書き換え**
  - 旧コマンド名（`/draft-l1`, `/draft-l2`, `/gen-phases` 等）を現行コマンドに更新
  - 旧ディレクトリ構造（`l1_vision.md`, `l2_system/`, `l3_features/`）を v3.x 形式に修正
  - 旧ID形式（VISION-xxx, NF-xxx, RULES-xxx, SP-xxx）を REQ/PH/F の3種に整理

- **ドキュメント間の不整合を修正**
  - CLAUDE.md のディレクトリ構成に `.claude-plugin/`, `.claude/rules/` を追記
  - `docs/plugin-development-guide.md` のセクション名を実態に合わせて修正（目的→概要、入力→引数、処理手順→手順）
  - `.claude/rules/skill-development.md` のセクション名を SKILL.md の実態に合わせて修正（Instructions→実行手順、Limitations→制約事項）
  - SKILL.md の重複セクション（Limitations）を制約事項に統合
  - `gen-l1.md`, `status.md`, `done.md` に標準の「概要」セクションを追加

## [3.2.0] - 2026-02-04

### Changed

- **コマンド構造の統一**
  - セクション名を統一（「概要」「完了後の案内」「出力フォーマット」）
  - 全コマンドに使用例を追加
  - init-tri-ssd, status に `<avoid_over_engineering>` ブロックを追加
  - 引数セクションのスタイルを統一

- **SKILL.md の充実**
  - Instructions セクションを日本語化・詳細化
  - コマンド表に「前提条件」「使い分け」列を追加
  - 意思決定ツリーを追加
  - 推奨フロー図を視覚化

### Added

- **エラーケースセクション** を全コマンドに追加
  - gen-l1, gen-l2, gen-l3, gen-code, done, init-tri-ssd

## [3.1.0] - 2026-02-04

### Added

- **`/split-l3` コマンド** - L3フェーズをフォルダ構造に分割
  - インライン形式（1ファイル）→ 分離形式（フォルダ）に変換
  - 慎重に進めたいフェーズや、チーム開発での機能分担に対応
  - チェック状態（`[x]`）を完全に保持

- **`/merge-l3` コマンド** - 分離されたL3フェーズを統合
  - 分離形式（フォルダ）→ インライン形式（1ファイル）に変換
  - ステータス管理: 全機能が done → done、それ以外 → wip
  - チェック状態を保持しながら統合

## [3.0.0] - 2026-02-04

### Changed

- **フロントマター仕様を大幅簡素化**
  - 変更前: `id`, `kind`, `layer`, `status`, `doc_status` の5フィールド
  - 変更後: `status: wip|done` の1フィールドのみ
  - ID形式（REQ-xxx, PH-xxx, F-xxx）は本文中で引き続き使用

- **コマンド名を統一**
  - `/draft-l1` → `/gen-l1`
  - `/draft-l2` → `/gen-l2`
  - `/gen-phases` → `/gen-l3`
  - `/check` → `/status`（進捗確認に特化）
  - `/review` → `/done`（完了マーキングに特化）

- **三層構造をシンプル化**
  - L3フェーズに機能と受け入れ条件をインライン化
  - L2のrules.mdを廃止（Claude Codeデフォルト機能と重複）

### Removed

- `/draft-rules` コマンド（L2 rules.md廃止に伴い削除）
- `docs/samples/` ディレクトリ（サンプルドキュメント削除）
- `docs/guide.md`, `docs/glossary.md`, `docs/checklists.md`, `docs/frontmatter_spec.md`

## [2.2.0] - 2026-01-23

### Added

- **プラグイン開発原則ガイドを追加**
  - `docs/plugin-development-guide.md` - 包括的な開発ガイド（301行）
  - ファイルサイズ制限、単一責任、段階的開示などの原則を明文化
  - Tri-SSD三層モデルとの整合性セクション
  - アンチパターンとチェックリスト

- **コンテキスト依存ルールを追加**
  - `.claude/rules/command-development.md` - コマンド開発時に自動読み込み
  - `.claude/rules/skill-development.md` - スキル開発時に自動読み込み
  - 該当ファイル編集時のみルールが適用される効率的な設計

### Changed

- **CLAUDE.mdにプラグイン開発原則セクションを追加**
  - 必須ルール（ファイルサイズ、テスト、単一責任、段階的開示）
  - コンテキスト効率の指針
  - 詳細ガイドへの参照

## [2.1.1] - 2026-01-21

### Changed

- **SKILL.md descriptionをベストプラクティスに準拠して改善**
  - 言語を英日混在から日本語統一に変更（ユーザー発話とのマッチング向上）
  - 「使用タイミング」パターンで8つのユースケースを明示
  - トリガーワードを9個から19個に拡充
  - Claude Codeプラグインのdescriptionベストプラクティスに完全準拠

## [2.1.0] - 2026-01-19

### Changed

- **出力フォーマットをコマンドに直接埋め込み**
  - 各コマンド（draft-l1, draft-l2, gen-phases, draft-rules, gen-l3）にYAMLフロントマター形式と必須セクション構造を埋め込み
  - テンプレートファイル参照のバグを根本解決
  - コマンド単体で完結して動作するように改善

- **L3フォルダ構造をフェーズ別に変更**
  - 変更前: `docs/l3_features/F-xxx_feature.md`（フラット）
  - 変更後: `docs/l3_features/PH-xxx_phase-name/F-xxx_feature.md`（フェーズごと）
  - フェーズが複数機能を持つ場合の視認性向上

### Removed

- `templates/` フォルダを削除
  - 出力フォーマットがコマンドに埋め込まれたため不要に
  - 約1,400行の削減

### Added

- check.md にフェーズフォルダ整合性チェック項目を追加
- SKILL.md にL3フォルダ構造の説明を追加
- **SKILL.md にフェーズガイドラインと知見反映フローを追加**
  - 共通原則（理由の記録、知見の共有、過剰設計の回避）
  - 知見の反映先（L1/L2/L3 への還元ガイド）
  - フェーズごとのガイド（L1、L2、L3、実装、レビュー）

### Fixed

- ドキュメント内のL3パス例をフェーズフォルダ形式に統一
  - guide.md, check.md, review.md, samples/l2_foundation_taskflow.md

## [2.0.0] - 2026-01-16

### Changed

- **フレームワーク名を SSDD から Tri-SSD に変更**
  - SSDD (Slices Specification-Driven Development) → Tri-SSD (Tri-Layer Slice Spec Driven)
  - 三層構造を名前で明示
- リポジトリ構造を整理
  - `ssdd-plugin/` の内容をルートに移動
  - `eval/`, `archive/` を削除
- コマンド名を変更
  - `/init-ssdd` → `/init-tri-ssd`
- スキル名を変更
  - `ssdd-orchestrator` → `tri-ssd-orchestrator`
- プラグイン名を変更
  - `ssdd` → `tri-ssd`

## [1.0.0] - 2025-12-30

### Added

- GitHub マーケットプレイス対応
  - marketplace.json を GitHub 配布形式に更新
  - LICENSE ファイル (MIT) を追加
  - plugin.json に repository/license メタデータを追加
  - パブリックリリース準備完了

## [0.8.0] - 2025-12-11

### Added

- ssdd-orchestrator スキル（ClaudeCode Skills 対応）
  - Tri-SSD ワークフローのオーケストレーション
  - 「仕様」「L1」「L2」「L3」等のキーワードで自動起動
  - Instructions / Examples / Limitations セクション完備

## [0.7.1] - 2025-12-05

### Changed

- validation_tools.md を checklists.md に統合（セクション 4: バリデーションコマンド）
- changelog_management.md の SSDD 固有部分を guide.md に統合（セクション 6.5: ドキュメント更新の判断基準）

### Removed

- error_messages.md（未実装のエラーコードシステム）
- validation_tools.md（checklists.md に統合）
- changelog_management.md（guide.md に統合）

## [0.7.0] - 2025-12-04

### Added

- GitHub Actions による Markdown リンティング

### Changed

- draft-l1 と convert-l1 を統合（引数なし: 対話モード、引数あり: 変換モード）
- テンプレートを ssdd-plugin/templates/ に移動

### Removed

- convert-l1 コマンド（draft-l1 に統合）
- skills フォルダ（コマンドに SSDD コンテキストを埋め込み）
- ドキュメントからの v0.x バージョン参照

### Improved

- 全コマンドのプロンプト品質を改善
  - 不要な ASCII 図・サンプルを削除
  - 重複した検証コマンドを統合
  - 出力例をシンプル化

## [0.6.0] - 2025-12-03

### Added

- gen-code コマンド（L3 機能ドキュメントからコード・テストを生成）
- marketplace.json（ローカルプラグインテスト用）
- SSDD プロンプト品質評価システム（eval/）

### Changed

- gen-l2 → draft-l2、gen-rules → draft-rules にリネーム
- gen-code の技術スタック検出を foundation.md からプロジェクト設定ファイル（package.json, pyproject.toml 等）の自動検出に変更
- promote-status と propagate-change を既存コマンドに統合

### Removed

- SKILL.md（各コマンドに SSDD コンテキストを埋め込み）

## [0.5.0] - 2025-11-27

### Added

- rules.md サポート（L2 実装ルール）
- gen-phases コマンド（フェーズ定義・機能一覧を生成）
- 全 gen コマンドに再生成サポート
- Claude 4 ベストプラクティスの適用

### Changed

- L2 技術基盤ファイル名を overview.md → foundation.md に変更
- draft-l2 を foundation.md 生成に限定（フェーズ生成は gen-phases に分離）
- kind 値を変更（overview → foundation）
- L2/L3 テンプレートを包括的セクションで強化

## [0.4.0] - 2025-11-26

### Changed

- ssdd-plugin を正本化（`.claude/` との二重管理を解消）
- L3 テンプレートを汎用テンプレート 1 つに統合
- kind 値を整理（vision, foundation, phase, feature の 4 種類に）

### Removed

- ドメイン特化 L3 テンプレート（Web/Desktop/Mobile/CLI）
- `.claude/commands/` と `.claude/skills/` の重複ファイル
- depends_on フィールド（廃止）
- 未使用の kind 値（req, nfr, spike）

## [0.3.0] - 2025-11-26

### Added

- L3 軽量運用ガイドライン（小規模機能向けの簡略化オプション）
- 定量的指標をプロジェクト規模の目安として再定義

### Changed

- スキルファイルをモジュール化（SKILL.md, examples.md, troubleshooting.md）
- 全コマンドの前提処理を統一（SKILL.md を参照）
- gen-l2 の技術候補数を「最低 3 個」に明確化

### Fixed

- L3 の設計思想を明文化（分割統治による AI 活用）
- ID 採番ルールにタイムゾーン・上限規定を追加

## [0.2.0] - 2025-11-26

### Added

- check --list-ids オプション
- review コマンドにステータス昇格機能を統合
- 定量的レビュー基準（L1/L2/L3 各層の数値目安）
- gen-l2 --simple モード（小規模プロジェクト向け 1 ファイル構成）
- コマンドへの包括的エラーハンドリング

### Changed

- gen-l2 技術選定プロセスを対話型に改善
- フロントマター仕様の完全適用（title フィールド廃止）

## [0.1.0] - 2025-11-26

### Added

- タイムスタンプベース ID 形式（PREFIX-YYYYMMDD-nnn）
- doc_status フィールド（draft/reviewed/implemented）
- 三層モデルの正式導入（L1/L2/L3）

### Changed

- title フィールドを廃止、本文の # 見出しをタイトルとして使用
- フロントマター必須フィールドの整理

### Removed

- 旧形式の連番 ID（REQ-001 形式）

## [0.0.1] - 2025-11-25

### Added

- 初期リリース
- 基本的なコマンド群（init-tri-ssd, draft-l1, gen-l2, gen-l3, check, review）
- スキルファイル（SKILL.md）
- テンプレート群
- ガイドドキュメント
