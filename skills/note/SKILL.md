---
description: Tri-SSD プロジェクトで作業中の一時情報（発見・仮説・調査結果・引き継ぎ）を Note に記録し、溜まった Note を Docs・Task へ昇格するか削除して整理する。セッション終了時の引き継ぎを上書きで更新する。
when_to_use: メモして・記録しておいて・覚えておいて・調べた結果を残して・引き継ぎを書いて・今日はここまで・中断する・ノートを整理して・メモが溜まった、と言われたとき。セッションを終えるとき、Task を完了したとき。英語では take a note / handoff / wrap up / triage notes。仕様の改訂は docs、実装は task を使う。
argument-hint: "[記録する内容 | handoff | triage]"
allowed-tools: Read, Edit, Bash
---

# Note を記録・整理する

<tri_ssd_context>
Tri-SSD: Goal（docs/goal.md）・Docs（docs/ のあるべき状態）・Tasks（docs/tasks/ 差分を解消する検証可能な作業）・Notes（docs/notes/・.tri-ssd/notes/ 一時情報）・CHANGELOG（意味のある変更の履歴）。
決定的処理は CLI `python3 "${CLAUDE_SKILL_DIR}/../../scripts/tri.py"`（以下 `tri`）で行う。文書を開く前に `tri context` で必要なセクションだけを取得する。
置き場・寿命の判断に迷ったら `${CLAUDE_SKILL_DIR}/../../docs/knowledge-model.md` を読むこと。
</tri_ssd_context>

<avoid_over_engineering>
- 記録時に分類・清書しない。1〜3 行で要点を書くだけでよい
- Note の全文を読まない。整理は `tri note triage` の候補一覧から始める
- 検証していない推測を Docs へ昇格しない
</avoid_over_engineering>

## 記録する

```bash
tri note add "FTS5 trigram は 2 文字のクエリに一致しない" --task T-0005   # docs/notes/inbox.md に追記
tri note add "手元の VPN だと外部 fetch が 3 秒かかる" --local              # .tri-ssd/notes/（git 管理外）
```

- Task に関係するなら `--task` を付ける（その Task の context に自動で含まれる）
- 個人の事情・環境固有の情報は `--local`。共有すべき知見は付けない
- 長い調査ログは別ファイル（`--file topic.md`）に書き、inbox には結論だけを書く
- 複数行のメモは1行目が見出しになる。1行のメモは日時と Task ID だけが見出しになる

## 引き継ぐ（セッション終了・中断時）

```bash
tri note handoff - <<'EOF'
- 現在位置: T-0005 の AC1 PASS
- 次の一手: AC2（補完の並び順）
- 未解決: use_count 列を足すか判断待ち（候補 2 案は inbox 参照）
EOF
```

- 上書きされる。書くのは現在位置・次の一手・未解決の問いだけ（経緯は書かない）。1行なら `tri note handoff "..."` でもよい
- 次のセッション開始時にフック（または `tri status`）が表示する

## 整理する（Task 完了時・セッション終了時・triage が候補を示したとき）

```bash
tri note triage     # 各エントリの経過日数・参照 Task の状態・サイズ・整理候補の印
```

印の意味: `task-closed`（参照先 Task が完了済み）・`old`（14 日超）・`large`（約 800 トークン超）。
エントリごとに行き先を決め、移したら Note から削除する（Edit でエントリの見出しごと消す）:

| 内容 | 行き先 |
|---|---|
| 検証済みで今後も真な仕様・設計・外部の事実 | Docs（docs スキルの更新プロトコルで反映） |
| 解消すべき未達事項 | Task（task スキルで作成） |
| 繰り返し使う手順 | Docs の手順書（同じ手順が 3 回以上出たら Skill 化の候補として handoff に書く） |
| 作業再開に必要・ユーザー判断待ちの問い | 残す。本文に `<!-- tri:keep -->` を書く（整理候補の印が付かなくなる。解決したら消す） |
| 不要・すでに反映済み | 削除 |

## 完了後の案内

- 記録・更新したファイル
- 整理した件数（昇格 / Task 化 / 削除 / 残した）と、残りの Note の推定トークン

## エラーケース

| ケース | 対応 |
|---|---|
| docs/notes/ が無い | `tri init`（既存ファイルは上書きしない）で作成する |
| 昇格先の Docs が判断できない | `${CLAUDE_SKILL_DIR}/../../docs/knowledge-model.md` の判定フローに従う。それでも決まらなければ Note に残す |
