---
description: L2 のインターフェース設計ドキュメント（docs/l2_foundation/interface.md）を対話的に生成する。gui は画面一覧・画面遷移図（Mermaid、ユーザー状態含む）・主要導線（操作→結果→応答/待ち時間フィードバック）、cli/api 等はコマンド体系・エンドポイント契約を記録し、foundation.md §3 が肥大したときの分離先となる。gen-l2 の後に使う。
when_to_use: 画面設計したい・画面遷移を決めたい・UI/UX を設計したい・ユーザー導線を整理したい・画面が増えてきたので整理したい・CLI のコマンド体系や API 契約を深く設計したい、と言われたとき。分離の目安は画面5枚超・主要導線3本超・foundation §3 が約100行超。英語では design screens / user flows。画面数枚の小規模なら gen-l2 の §3 インライン記述で足りる。技術スタック・アーキテクチャの設計は gen-l2、データ設計は gen-data を使う。
allowed-tools: Read, Write, Edit, Glob, Grep
---

# インターフェース設計コマンド

<tri_ssd_context>
Tri-SSD: L0(任意メモ docs/l0_ideas/) → L1(要件 docs/l1_requirements/vision.md) → L2(構成 docs/l2_foundation/foundation.md) → L3(フェーズ docs/l3_phases/PH-xxxx.md)。
ID形式: PREFIX-nnnn（REQ, PH, F）。番号は再利用しない（永久欠番）。
配置・分割・粒度の判断に迷ったら `${CLAUDE_SKILL_DIR}/../../docs/layer-rules.md` を読むこと。
</tri_ssd_context>

## 概要

L2 のインターフェース仕様を深掘りし、`docs/l2_foundation/interface.md` として foundation.md から分離・管理する。
foundation.md §3 のインライン記述では足りなくなった規模（画面5枚超・導線3本超・§3 が約100行超）で使う。

**書くのは L1 体験要件（要求）を満たす「具体形」だけ**。「〜できること」という要求の文が混ざったら L1 へ戻す。
更新トリガーは foundation.md と同じ「設計判断が変わる」（L2 の一部。フェーズ完了後も真であり続ける）。

## 設計時の原則

<avoid_over_engineering>
- 主要導線は L1 の体験要件にあるものだけ書く（全操作の網羅はしない）
- 待ち時間・フィードバックは「ユーザーが不安になる箇所」（1秒超の処理・失敗しうる操作）にだけ書く
- 全画面のワイヤーフレーム・ピクセル単位のレイアウトは書かない（それは実装かデザインツールの領分）
- 「念のため」の画面・遷移を追加しない
- 図はすべて Mermaid（ASCII アートを使わない）
</avoid_over_engineering>

## 引数

- 引数なし（L1/L2 から対話的に設計する）

### 使用例

```
/gen-interface
```

## 前提処理

1. `docs/l1_requirements/vision.md` を読み、`product_type` と体験要件を把握する
2. `docs/l2_foundation/foundation.md` を読み、§3 の既存インライン記述を確認する
3. `docs/l2_foundation/interface.md` が存在するか確認（→ 再生成モード）
4. product_type が gui 以外の場合は「cli/api 等のインターフェース体系を interface.md に分離しますか？（小規模なら foundation §3 のままを推奨）」と確認する

## 出力フォーマット（必須）

### YAMLフロントマター

```yaml
---
layer: L2
updated: YYYY-MM-DD
---
```

### 必須構造

**生成前に `${CLAUDE_SKILL_DIR}/references/interface-spec-guide.md` を必ず読む**。product_type 別のテンプレート（gui は画面一覧・画面遷移図・主要導線の3点セット）と記入基準・Mermaid 記入例が定義されている。
文体・構造化・図・機械契約マーカーの書式は `${CLAUDE_SKILL_DIR}/../../docs/writing-rules.md`（記載規約の SSOT）に従う。

## 生成手順（対話型）

### Step 1: 画面（または操作単位）の洗い出し

- L1 の体験要件・REQ から必要な画面を列挙し、画面一覧表（ID・画面・目的・主要素）を作る
- 既存の foundation §3 にインライン記述があれば取り込んでから拡張する

### Step 2: 遷移とユーザー状態

- 画面間の遷移を Mermaid `stateDiagram-v2` で描く
- ユーザー状態（未ログイン/ログイン済み・処理待ち等）を含める
- 画面が多い場合は機能グループ単位で遷移図を分割する（画面一覧は全体で1表を維持）

### Step 3: 主要導線

- L1 の体験要件・REQ と ID で対応付け、ステップごとに「ユーザーが何をする → 何ができるようになる → システム応答（待ち時間とフィードバック）」を書く
- 失敗時の見せ方は foundation §2.5 エラー処理方針と整合させる（個別文言はここに書かない）

### Step 4: foundation.md のポインタ化

`docs/l2_foundation/interface.md` を書き出したら、foundation.md の §3 を1行ポインタに置換する:

```markdown
## 3. インターフェース仕様

→ `interface.md` を参照（画面一覧・画面遷移図・主要導線）
```

## 再生成モード（既存 interface.md がある場合）

### 保持するもの（上書きしない）

| 対象 | 理由 |
|------|------|
| 既存の画面 ID（S-nn） | L3・実装からの参照を壊さない |
| 確定済みの導線（ユーザーが承認済み） | 設計判断の保持。変更時は差分を提示して確認 |
| ユーザーが追記したメモ | 手動編集を尊重 |

### 再生成時の手順

1. 既存 interface.md を読み、画面 ID・導線を把握
2. L1 の体験要件との差分を分析
3. ユーザーに「何を更新するか」を確認し、該当箇所のみ再生成

## 完了後の案内

- 生成ファイルのパス（`docs/l2_foundation/interface.md`）と画面数・導線数を報告
- foundation.md §3 をポインタ化した旨を報告
- TODO箇所の数を報告
- 次のステップ: `/gen-l3`（フェーズ計画）または `/gen-code`（UI 実装時に interface.md が参照される）

---

## エラーケース

| ケース | 対応 |
|--------|------|
| L1 が存在しない | エラー: 「L1が見つかりません。`/gen-l1` を先に実行してください」 |
| L2（foundation.md）が存在しない | エラー: 「L2が見つかりません。`/gen-l2` を先に実行してください」 |
| L1 に体験要件がない | 警告: 「L1 に体験要件がありません。先に `/gen-l1` で体験要件を追加するか、このまま対話で設計するか選んでください」 |
