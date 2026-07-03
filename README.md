# Tri-SSD Plugin for Claude Code

AI/LLMコードエージェント向けのシンプルな仕様駆動開発フレームワーク

## インストール

```bash
# マーケットプレイスを追加
/plugin marketplace add emanon-i/tri-ssd

# プラグインをインストール
/plugin install tri-ssd@emanon-i-tri-ssd
```

## クイックスタート

```bash
# 1. ディレクトリ構造を初期化
/init-tri-ssd

# 2. L1（要件）を生成
/gen-l1

# 3. L2（システム構成）を生成
/gen-l2

# 4. L3（フェーズ・機能+受け入れ条件）を生成
/gen-l3

# 5. コード・テストを生成
/gen-code PH-xxxx

# 6. 整合性・進捗を確認（任意）
/review-tri-ssd

# 7. 完了したフェーズの完了処理（ゲート確認 → CHANGELOG → 知見還元 → アーカイブ）
/archive-l3 PH-xxxx
```

順序を覚える必要はありません — `/next-tri-ssd` が現在地から次の一手を提案します。

## コマンド一覧

| コマンド | 説明 |
|---------|------|
| `/next-tri-ssd` | 現在地を判定し次の一手を提案・実行（迷ったらこれ） |
| `/init-tri-ssd` | ディレクトリ構造と情報の在り処マップを初期化 |
| `/gen-l1 [ファイルパス]` | L1要件を生成（対話モード or 既存ドキュメント変換） |
| `/gen-l2` | L2システム構成を生成 |
| `/gen-interface` | L2インターフェース設計を深掘り（画面一覧・遷移図・導線 → interface.md） |
| `/gen-data` | L2データ設計を深掘り（概念モデル・ライフサイクル → data.md） |
| `/gen-l3` | L3フェーズ（機能+受け入れ条件）を生成 |
| `/reshape-l3 <PH-xxxx>` | L3フェーズの形式を相互変換（インライン⇔フォルダ） |
| `/gen-code <PH-xxxx\|F-xxxx>` | コード・テストを生成し、検証記録を残す |
| `/review-tri-ssd [PH-xxxx]` | ID整合性・要件網羅・進捗を検証 |
| `/archive-l3 [PH-xxxx]` | フェーズ完了処理（ゲート・CHANGELOG・知見還元・アーカイブ） |

### 引数記法の凡例

| 記法 | 意味 | 例 |
|------|------|-----|
| `<引数>` | 必須引数 | `/gen-code <PH-xxxx>` |
| `[引数]` | 省略可能な引数 | `/gen-l1 [ファイルパス]` |
| `...` | 複数指定可能 | `/gen-l3 PH-001 PH-002 ...` |

## 三層モデル

| レイヤー | 内容 | ファイル |
|---------|------|----------|
| L0 | アイディア・ラフメモ（任意） | docs/l0_ideas/ |
| L1 | 要件・意思決定（課題・動機・判断の記録） | docs/l1_requirements/vision.md |
| L2 | システム構成（技術スタック・アーキ） | docs/l2_foundation/foundation.md |
| L3 | フェーズ（機能一覧 + 受け入れ条件） | docs/l3_phases/PH-xxxx.md |

どの情報をどのレイヤーに置くかの判定ルール・ファイル分割基準・粒度基準は [docs/layer-rules.md](docs/layer-rules.md) を参照してください。

## ディレクトリ構成（生成後）

```
docs/
  l0_ideas/                     # L0: アイディア・ラフメモ（任意）
  l1_requirements/
    vision.md                   # L1: 要件
  l2_foundation/
    foundation.md               # L2: システム構成
  l3_phases/
    PH-nnnn_xxx.md               # L3: フェーズ（機能+受け入れ条件）
```

## ID形式

連番（4桁ゼロ埋め）:

| プレフィックス | 用途 | 例 |
|---------------|------|-----|
| `REQ` | 要件（L1内でインライン定義） | REQ-0001 |
| `PH` | フェーズ | PH-0001 |
| `F` | 機能 | F-0001 |

## ドキュメント

詳細なガイドは [docs/](docs/) を参照してください。

## 変更履歴

[CHANGELOG.md](CHANGELOG.md) を参照してください。

## ライセンス

MIT
