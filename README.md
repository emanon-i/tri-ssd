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
/gen-code PH-xxx

# 6. 完了したフェーズをアーカイブ
/archive-l3 PH-xxx
```

## コマンド一覧

| コマンド | 説明 |
|---------|------|
| `/init-tri-ssd` | ディレクトリ構造を初期化 |
| `/gen-l1 [ファイルパス]` | L1要件を生成（対話モード or 既存ドキュメント変換） |
| `/gen-l2` | L2システム構成を生成 |
| `/gen-l3` | L3フェーズ（機能+受け入れ条件）を生成 |
| `/split-l3 <PH-xxx>` | L3フェーズをフォルダ構造に分割 |
| `/merge-l3 <PH-xxx>` | 分離されたL3フェーズを統合 |
| `/gen-code <PH-xxx\|F-xxx>` | コード・テストを生成 |
| `/archive-l3 [PH-xxx]` | 完了したL3フェーズをアーカイブ |

### 引数記法の凡例

| 記法 | 意味 | 例 |
|------|------|-----|
| `<引数>` | 必須引数 | `/gen-code <PH-xxx>` |
| `[引数]` | 省略可能な引数 | `/gen-l1 [ファイルパス]` |
| `...` | 複数指定可能 | `/gen-l3 PH-001 PH-002 ...` |

## 三層モデル

| レイヤー | 内容 | ファイル |
|---------|------|----------|
| L0 | アイディア・ラフメモ（任意） | docs/l0_ideas/ |
| L1 | 要件・意思決定（課題・動機・判断の記録） | docs/l1_requirements/vision.md |
| L2 | システム構成（技術スタック・アーキ） | docs/l2_foundation/foundation.md |
| L3 | フェーズ（機能一覧 + 受け入れ条件） | docs/l3_phases/PH-xxx.md |

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
