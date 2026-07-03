# Changelog

Tri-SSD (Tri-Layer Slice Spec Driven) フレームワークの変更履歴です。

形式は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に準拠しています。

## [5.0.0] - 2026-07-03

### Added

- **`docs/layer-rules.md` を新設**（レイヤー配置ルールの SSOT）
  - 配置決定表・配置判定フロー（Q0〜Q4）・曖昧ケースの裁定・ファイル分割ルール・適正粒度基準を明文化
  - 判定軸は「更新トリガー」: L1=「実現手段を決めなくても真か」、L2/L3=「フェーズ完了後も真か」
  - 全スキルの `<tri_ssd_context>` から参照される（配置判断に迷ったときだけロードする段階的注入）
- **`/review-tri-ssd` スキルを新設** — 整合性検証と進捗サマリ（読み取り専用）
  - `scripts/validate_ids.py`（新設・共有）で dangling 参照・重複定義・status と検証記録の突合を機械的に検証
  - 要件の網羅性（どの PH からも参照されない REQ）と仕様⇔実装の乖離（converge 軽量版）を読み合わせで確認
- **L1/L2/L3 テンプレートに YAML frontmatter を導入**
  - L1: `layer` / `product_type`（gui|cli|api|library|batch|data|doc|other）/ `updated`
  - L2: `layer` / `updated`
  - L3: `id` / `status`（planned|in_progress|done）/ `requires`（REQ 参照）/ `updated`
- **テンプレート新セクション**（いずれも任意・追加式で後方互換）
  - L1: 「原則」（1.4 を改名）・「体験要件」（product_type 別の使い勝手の要求）・「やらないこと」
  - L2: 「インターフェース仕様」（product_type 別の具体仕様）・「確認済みの前提」（スパイクで判明した事実・出所付き）・「設計判断の記録」
  - L3: 「事前確認」（確認作業のみ。結果は L2 へ）・「検証記録」（事後証跡）・「完了サマリ」（archive 時に記入）
- **`/gen-code` に Phase 0（clarify）を追加** — 対象 F に未解決 TODO・矛盾がある場合のみ最大3〜5問を確認（なければ質問ゼロで即実装）
- **`/archive-l3` をフェーズ完了処理に拡張**
  - ゲート: 検証記録の全 F PASS を確認（未達は警告+続行確認）
  - 完了サマリから生成プロダクトの CHANGELOG.md へ自動追記（出所は L3 完了サマリに一本化）
  - 知見の L1/L2 反映を提案（承認制）。「仕様は腐る、コードが真実」の思想を明文化
- **`/init-tri-ssd` が docs/README.md（情報の在り処マップ）を生成**するように拡張
- **`/next-tri-ssd` スキルを新設** — オーケストレーター（現在地判定→次の一手の提案・実行）
  - docs/ の状態から現在地を決定的に判定（未初期化→init、要件なし→gen-l1、…、全アーカイブ→次期計画）し、ワークフローの順序を知らなくても開発を進められる
  - validate_ids で健全性を確認し、エラー時は review-tri-ssd を先に提案。「（未作成）」ポインタ・未振り分けの `（未確認・要検証）` 印も検出
- **`docs/writing-rules.md` を新設**（記載規約の SSOT。配置=layer-rules / 書き方=writing-rules の分離）
  - 文章原則（1文1事実・修飾語禁止・結論先行）・構造化（表>箇条書き>散文・見出し=参照単位）・図の Mermaid 統一・SSOT・300行分割・**機械契約マーカー表**（TODO / `（未確認…）` 印 / `検証:` 行 / frontmatter が機械的に読まれる契約であることを明文化）
  - 生成系5スキル（gen-l1/l2/l3/interface/data）の出力フォーマット節から参照
- **`.claude/rules/skill-development.md` に「XML タグによる強指示」を明文化**（強い制約はタグで囲む理由と、生成ドキュメント側では使わない使い分け）
- **`/gen-interface` スキルを新設** — L2 インターフェース設計の深掘り（`docs/l2_foundation/interface.md`）
  - gui は「画面一覧・画面遷移図（Mermaid stateDiagram-v2、ユーザー状態含む）・主要導線（何をする→何ができる→応答/待ち時間フィードバック）」の3点セット
  - cli / api / library / batch / doc の簡潔テンプレも収録（`references/interface-spec-guide.md`）
  - foundation §3 の肥大時の分離先（分離の目安: 画面5枚超・主要導線3本超・約100行超）。分離時は foundation にポインタを残す
- **`/gen-data` スキルを新設** — L2 データ設計の深掘り（`docs/l2_foundation/data.md`）
  - 概念モデル（Mermaid erDiagram）・**データライフサイクル**（発生トリガー・更新頻度・増加ペース・保持/ローテーション・削除方針）・整合性の判断基準（`references/data-design-guide.md`）
  - **SSOT 裁定**: スキーマのカラム定義の正は実装コード（migration/DDL/ORM）。data.md には判断基準と正へのパス参照のみ置き、全カラム表を複製しない
  - 分離の目安: エンティティ7個超・ライフサイクル要件あり・約100行超
- **PH-0000 に第6の機能「技術前提の事実検証（スパイク）」を追加**
  - 計画全体が依存する未確認の前提（外部 API の実在・レート制限、核心処理の実現可否、ライブラリ制約）を実装前に最小の検証コード・実測で確認
  - gen-l2 が技術選定時に未確認の仮定へ `（未確認・PH-0000 で検証）` 印を残し、gen-l3 が拾って検証作業化。判明した事実は L2「確認済みの前提」へ昇格
  - 前提の振り分け: 計画全体を左右する → PH-0000 スパイク F ／ 特定フェーズのみ → 該当 PH の「事前確認」節

### Changed

- **`/split-l3` と `/merge-l3` を `/reshape-l3` に統合**（破壊的変更）
  - 1能力（インライン⇔フォルダの往復変換）・同一更新トリガーのため統合。変換方向は対象の形式から自動判定
  - split.py / merge.py を frontmatter・全セクション順序（検証記録・完了サマリ等）保持に改修（往復 diff ゼロを維持）
- **`next_id.py` をプラグインルート `scripts/` に一本化**（gen-l1 / gen-l3 の重複コピーを削除）
  - `_archive/` も走査対象であることを明記し、上書き再生成時の採番手順（破棄前に採番）を gen-l1 に追加（REQ ID 巻き戻りによる L3 参照のサイレント破壊を防止＝永久欠番方式）
- **全スキルの `<tri_ssd_context>` を4行版に縮小**（レイヤー詳細の複製をやめ layer-rules.md への参照に置換。8スキル×11行の重複を解消）
- **`/gen-l3` の PH-0000 定型を `references/ph-0000-template.md` に外出し**（本文 364行→269行。初回実行時のみロード）
- 検証結果の記録先を AC 行への追記から「検証記録」セクションに変更（Plan と事後証跡の分離）
- `.claude/rules/command-development.md` → `skill-development.md`（globs を `skills/**/*.md` に修正。v4.0.0 以降デッドルールだったものを再生）
- CLAUDE.md / docs/plugin-development-guide.md を v4 以降の実態（skills 形式・`when_to_use`・description+when_to_use 合計1,536字制限）に全面改訂
- 三層モデル表の重複を解消（正は docs/layer-rules.md。README はナビ用の派生複製として維持）
- **全8スキルの `description` / `when_to_use` の発火語彙を増強**（口語トリガー・英語表現・成果物と前提条件を明記。誤発火防止に「〜のときは別スキル」の区別を追加）
- **gen-l1 / gen-l2 / gen-l3 の出力テンプレートを「テンプレート＋記入ガイド」として `references/` に外出し**（段階的開示の徹底）
  - `gen-l1/references/vision-template.md`・`gen-l2/references/foundation-template.md`・`gen-l3/references/phase-template.md`
  - 各セクションに「何を書く/書かないの判断基準・良い例/悪い例」を追加（本文は必須構造の要点と参照指示のみ残す）
- **L2 テンプレートに品質セクションを追加**（いずれも省略可・記入判断基準付き）
  - 「データモデル」（Mermaid erDiagram 例付き）・「エラー処理方針」（分類・見せ方・リトライ方針。L3 の AC「エラー時〜」の上流定義）・「運用」（環境変数・デプロイ・監視）
  - layer-rules.md の配置決定表にも対応行を追加（SSOT 同期）
- **L2 を複数ファイル構成に**（foundation.md をハブとし、規模で `interface.md` / `data.md` を分離）
  - layer-rules.md のファイル分割ルール（L2 の適用結果）を改訂し、分離判定の目安とポインタ書式を明文化
  - 曖昧ケースの裁定に「スキーマ定義 vs データ設計」「未確認の仮定 vs 確認済みの前提」を追加
  - gen-code は実装対象に関連する分離ファイルだけ読む（UI 実装→interface.md、データ層→data.md。段階的注入）。review-tri-ssd も分離ファイルを乖離チェック対象に追加
- **図を Mermaid に統一**（ASCII 図の廃止）
  - 構成図=flowchart / 画面遷移=stateDiagram-v2 / データ関係=erDiagram / 時系列=sequenceDiagram。foundation §2.2 のコンポーネント構成図を ASCII 図から Mermaid flowchart に変更（ディレクトリツリー表示は図ではないため維持）

### Fixed

- `.gitignore` に `__pycache__/`・`*.pyc` を追加し、混入していた `skills/reshape-l3/scripts/__pycache__/` を削除
- 引数を取らないスキル（init-tri-ssd / gen-l2）の `argument-hint: なし` を削除（規約は「引数がある場合」のみ記載）
- **実行エージェント視点レビュー（Codex＋サブエージェント2体）で検出した不整合を修正**:
  - gen-code / archive-l3 にフォルダ形式（reshape-l3 split 後）の書き込み先ルールを追加（AC は `F-*.md`、status・検証記録は `_phase.md`。reshape-l3 との片側契約を解消）
  - gen-l3 の初回実行判定を修正（全フェーズアーカイブ後の再計画・フォルダ形式のみの状態で PH-0000 を重複生成しない）
  - `（未確認・PH-0000 で検証）` 印の除去を gen-code の正規操作として明記（スパイク AC「印が外れている」を満たせるように。前提が崩れた場合の中断・L2 見直し提案も追加）
  - CHANGELOG の出所を archive-l3（L3 完了サマリ）に一本化（gen-l2 再生成時に CHANGELOG へ直接書く指示を削除）
  - reshape-l3 の往復変換で見出し直後の空行が失われるバグを修正（`\s*$` が改行を跨いで消費していた。split→merge の往復 diff ゼロを実測確認）
  - validate_ids.py: PH-0000 未生成時の印参照を dangling エラーでなく情報扱いに（規定フローの正常状態が偽エラーになっていた）
  - gen-code: PH-0000 実装時は「プロジェクト設定ファイル必須」の例外・テスト型 AC 0件の F は Phase 3 をスキップ・目視確認 AC の事後完了フロー・検証に必要な外部手段の不足を Phase 0 の質問トリガーに追加
  - erDiagram 記入例に「属性はキー・制約のみ」注記（スキーマ複製の誘発防止）/ WebSearch を候補が自明でない場合のみに条件付き化 / `<!-- TODO: 要確認 -->` マーカー形式を layer-rules に明文化（gen-code の検出契約を全レイヤー共通に）
  - ph-0000-template の「6機能/5機能」不一致・PH-0000 の `requires` 空リスト可・reshape-l3 の Glob パターン・プレースホルダ表記（`PREFIX-xxx` → `PREFIX-xxxx`）・S-nn の採番ルール・「converge」ジャーゴン等の細部を統一
- **第2次レビュー（初見エージェント＋敵対的契約監査）で検出した不整合を修正**:
  - `（未確認…）` 印のライフサイクルを再設計: gen-l2 は `（未確認・要検証）` で付与 → gen-l3 が検証場所を確定して `（未確認・PH-xxxx で検証）` に更新 → gen-code が昇格時に除去（文言ハードコードによる振り分けズレ・PH-0000 アーカイブ後の行き場なし・表記ゆれを一括解消。非初回の計画レベル前提は次期フェーズ先頭にスパイク F を置く）
  - **「事前確認」節の実行工程を gen-code に追加**（実行者不在だったワークフローの穴。Phase 0 で未チェックの事前確認を実施→L2 記録→印除去→チェック）
  - gen-code の「部分成功は認めない」に目視確認 AC の例外を明記（PARTIAL 正常終了と矛盾していた）。PARTIAL 記録は AC-n でなく条件の要約で書く（AC-n 禁止則との矛盾解消）
  - スパイク F の「前提が崩れた」場合の終了状態を定義（不成立の確認も成果 = `PASS（前提不成立を確認、日付）` で正常終了し計画見直しを提案）
  - gen-l3: 再生成モードにフォルダ形式の書き込み先規則を追加（単一ファイル並存生成の禁止）・「初回実行」節と ph-0000-template の旧条件文を前提処理の厳密判定に統一・PH-0000 は 2〜4 フェーズの数に含めないと明記
  - archive-l3: 知見還元時の印除去・全アーカイブ後の次サイクル案内（終端の解消）。gen-code/gen-l3 の archive 案内を「フェーズ単位」に統一
  - gen-l2: 分離判定に「§2.4 約100行超」トリガー補完・§3 記入条件に「外部との契約」補完・再生成時の印棚卸し・L3 完了サマリへの越権記入を削除
  - review-tri-ssd: 引数省略時/指定時のスコープを明確化・「ドキュメント衛生」チェック新設（未作成ポインタ・300行超過・未振り分け印）
  - layer-rules: F 番号は全体通し・永久欠番の理由・検証結果の値は PASS/PARTIAL（FAIL は幽霊ステートだった）
  - reshape-l3 の「常に往復可能」を正確化（テンプレ準拠なら diff ゼロ、逸脱時は機能一覧が正規化・F-ID 順）・S-nn は validate 対象外と明記・スパイク検証コードの置き場（spike/ 使い捨て）を規定

### Migration（v4.0.0 からの移行）

| 旧 | 新 |
|----|----|
| `/split-l3 PH-xxx` | `/reshape-l3 PH-xxx`（方向は自動判定） |
| `/merge-l3 PH-xxx` | `/reshape-l3 PH-xxx`（同上） |
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
