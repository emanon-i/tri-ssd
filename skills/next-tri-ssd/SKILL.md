---
description: Tri-SSD の現在地（docs/ の状態）を決定的に判定し、次に実行すべきスキルを理由付きで提案・実行するオーケストレーター。要件→設計→計画→実装→完了処理のワークフロー全体を、ユーザーは「問題を語る」と「提案の承認」だけで進められる。
when_to_use: 次何すればいい？・どこまで進んだ？何する？・続きを進めて・このまま進めて・お任せで進めて・Tri-SSD で開発を進めて・何から始めればいい？・作りたいものがあるんだけど、と言われたとき。英語では what's next / continue the workflow。実行したい工程が明確な場合は各スキル（gen-l1 / gen-code 等）を直接使う。
allowed-tools: Read, Glob, Grep, Bash
---

# 次の一手コマンド（オーケストレーター）

<tri_ssd_context>
Tri-SSD: L0(任意メモ docs/l0_ideas/) → L1(要件 docs/l1_requirements/vision.md) → L2(構成 docs/l2_foundation/foundation.md) → L3(フェーズ docs/l3_phases/PH-xxxx.md)。
ID形式: PREFIX-nnnn（REQ, PH, F）。番号は再利用しない（永久欠番）。
配置・分割・粒度の判断に迷ったら `${CLAUDE_SKILL_DIR}/../../docs/layer-rules.md` を読むこと。
</tri_ssd_context>

## 概要

docs/ の状態から現在地を判定し、「次の一手」を理由付きで提案する。承認されたら該当スキルを実行し、完了後に次の一手を再提示する。
ユーザーが工程の順序（init → gen-l1 → gen-l2 → gen-l3 → gen-code → archive-l3）を知らなくても開発を進められるようにするのが目的。

## 実行時の原則

<avoid_over_engineering>
- 1回の提案 = 1工程。**承認なしに複数工程を連続実行しない**
- ユーザーが明示的に「お任せで」「全部進めて」と言った場合のみ連続実行してよい。ただし各スキル内の対話ポイント（技術選定・フェーズ計画の承認・再生成の選択等）では必ず停止する
- 状態判定のために docs 全文を読まない（存在確認・frontmatter・進捗サマリのみ）
- 整合性の深い検証は自前でやらず review-tri-ssd に委ねる
</avoid_over_engineering>

## 引数

- 引数なし（状態判定から始める）。ユーザーの発話に新しい要望・作りたいものの相談が含まれる場合は、状態判定より先にそれを扱う（下記 Step 0）

### 使用例

```
/next-tri-ssd
```

## 実行手順

### Step 0: 要望の受け取り（発話に要望がある場合のみ）

ユーザーが「〜を作りたい」「〜できるようにしたい」と問題・要望を語っている場合:
- docs/ が未初期化 → `/init-tri-ssd` → `/gen-l1` の順を提案
- L1 が既にある → 要望を L1 への追記として `/gen-l1`（再生成モード: 追記）を提案

### Step 1: 状態判定（決定的・上から順に評価し、最初に該当した行が現在地）

| # | 判定（Glob / Read） | 現在地 | 次の一手 |
|---|---|---|---|
| 1 | `docs/l1_requirements/` が存在しない | 未初期化 | `/init-tri-ssd` |
| 2 | `docs/l1_requirements/vision.md` が存在しない | 要件未定義 | `/gen-l1` |
| 3 | `docs/l2_foundation/foundation.md` が存在しない | 設計未着手 | `/gen-l2` |
| 4 | foundation.md に「（未作成）」の骨子ポインタが残っている | 分離設計が未実施 | `/gen-interface` または `/gen-data`（該当する方） |
| 5 | L2 に `（未確認・要検証）` 印（検証場所未確定）が残っている | 前提の振り分け待ち | `/gen-l3`（振り分けと検証作業化を行う） |
| 6 | アクティブな PH が0件（`PH-*.md` も `PH-*/_phase.md` も無い。`_archive/` 除外） | 計画未着手（または次期計画待ち） | `/gen-l3` |
| 7 | `status: planned` または `in_progress` の PH がある | 実装中 | `/gen-code PH-xxxx`（番号の若い未完了フェーズから） |
| 8 | `status: done` の PH がある | 完了処理待ち | `/archive-l3 PH-xxxx` |
| 9 | 全 PH がアーカイブ済み | 開発サイクル完了 | 次の要望をヒアリング → `/gen-l1`（要件追記）→ `/gen-l3`（次期計画） |

### Step 2: 健全性の確認（軽く）

共有スクリプトで整合性と進捗を取得する:

```bash
python3 "${CLAUDE_SKILL_DIR}/../../scripts/validate_ids.py"
```

`python3` が使えない環境（Windows の python3 は Store スタブの場合がある）では `python` / `py`。
エラーが出た場合は次の一手より先に `/review-tri-ssd` を提案する（壊れた状態の上に積まない）。

### Step 3: 提案と実行

1. 現在地・進捗サマリ・次の一手を**理由付きで**提示する（例: 「PH-0001 が in_progress で F 1/3 PASS。続きは `/gen-code PH-0001`」）
2. 承認されたら該当スキルを実行する
3. 完了後、状態を再判定して次の一手を提示する（ユーザーが「続けて」と言ったら次工程へ）

## 完了後の案内

- 実行した工程と、その次の一手を報告
- 開発サイクル完了時（判定9）: アーカイブ済みフェーズ数と、次サイクルの始め方（要望ヒアリング → gen-l1 追記）を案内

---

## エラーケース

| ケース | 対応 |
|--------|------|
| docs/ が存在しない | 判定1に該当 → `/init-tri-ssd` を提案（エラーにしない） |
| validate_ids がエラーを報告 | `/review-tri-ssd` を先に提案し、修正後に次の一手へ戻る |
| 判定が複数に該当しうる曖昧な状態 | 上の行（より上流の工程）を優先する |
