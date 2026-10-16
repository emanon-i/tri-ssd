"""長期運用シミュレーション。

ブリーフ 12.3 の 10 操作を N サイクル繰り返し、各サイクル後に知識の健全性を測る。
エージェントの編集は決定的にスクリプト化する（同じ入力で同じ結果）:

  disciplined: Tri-SSD の更新プロトコルどおり（置換・マーカー除去・CHANGELOG・ノート昇格）
  careless   : 追記で済ませる・マーカーを外さない・ノートを溜める（典型的な失敗）

    python3 tests/simulate.py [--cycles 8] [--mode disciplined|careless]
"""
from __future__ import annotations

import argparse
import contextlib
import io
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import tri  # noqa: E402
from trissd import check, md, notes, resolve  # noqa: E402
from trissd.project import Project  # noqa: E402

FEATURES = [
    ("add", "メモを1コマンドで追加できる", "追加は `memo add <text>` で受け付け、本文と作成日時を保存する。"),
    ("list", "メモを新しい順に一覧できる", "一覧は作成日時の降順で 20 件ずつ表示する。"),
    ("search", "キーワードでメモを検索できる", "検索は本文の部分一致で行い、一致箇所を強調表示する。"),
    ("tag", "メモにタグを付けて絞り込める", "タグは `#tag` 記法で本文から抽出し、小文字で保存する。"),
    ("edit", "既存のメモを編集できる", "編集はエディタを起動し、保存時に更新日時を記録する。"),
    ("delete", "メモを削除し 7 日以内なら復元できる", "削除は論理削除とし、7 日経過後に物理削除する。"),
    ("export", "全メモを Markdown で書き出せる", "書き出しは 1 メモ 1 ファイルとし、タグを frontmatter に含める。"),
    ("sync", "複数端末でメモを同期できる", "同期は変更ログを単調増加の版番号で交換する。"),
    ("pin", "重要なメモを一覧の先頭に固定できる", "固定は pinned フラグで表し、一覧で先に並べる。"),
    ("stats", "メモの件数と週ごとの推移を確認できる", "統計は作成日時を週単位で集計して表示する。"),
]
STORAGE_OLD = "保存は JSON ファイル（`data/memos.json`）に行う。"
STORAGE_NEW = "保存は SQLite（`data/memos.db`）に行い、本文に全文検索インデックスを張る。"


class Sim:
    def __init__(self, root: Path, mode: str):
        self.root = root
        self.mode = mode
        self.log: list[str] = []

    def tri(self, *args: str, stdin: str | None = None) -> tuple[int, str]:
        out = io.StringIO()
        old = sys.stdin
        if stdin is not None:
            sys.stdin = io.StringIO(stdin)
        try:
            with contextlib.redirect_stdout(out):
                try:
                    code = tri.main(["--root", str(self.root), *args])
                except SystemExit as e:
                    code = e.code if isinstance(e.code, int) else 2
        finally:
            sys.stdin = old
        return code, out.getvalue()

    def path(self, rel):
        return self.root / rel

    def read(self, rel):
        return self.path(rel).read_text(encoding="utf-8")

    def write(self, rel, text):
        self.path(rel).parent.mkdir(parents=True, exist_ok=True)
        self.path(rel).write_text(text, encoding="utf-8")

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.root, capture_output=True, check=True)

    # --- 1-2. 初期化と Goal / Docs ---------------------------------------------------
    def setup(self):
        self.root.mkdir(parents=True, exist_ok=True)
        self.git("init", "-q")
        self.git("config", "user.email", "s@example.com")
        self.git("config", "user.name", "sim")
        self.tri("init", "--name", "Memo")
        self.write("docs/goal.md", "# Memo Goal\n\n## 目的\n\nターミナルで思いついたことを即座に残し、後で必ず見つけられる。\n\n"
                   "## 成功状態\n\n- 記録から再発見まで 10 秒以内\n\n## 原則\n\n- **入力の速さを最優先**する\n")
        self.write("docs/requirements.md", "# 要求\n")
        self.write("docs/design.md", f"---\ncode: [src/]\n---\n# 設計\n\n## 保存\n\n{STORAGE_OLD}\n\n## 機能\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "setup")

    # --- 1 サイクル ---------------------------------------------------------------
    def cycle(self, i: int):
        name, req_text, design_text = FEATURES[i % len(FEATURES)]
        name = f"{name}{i // len(FEATURES) or ''}"
        req = self.tri("id", "REQ")[1].strip()
        task = self.tri("id", "T")[1].strip()
        # 2. あるべき状態を Docs に定義
        self.write("docs/requirements.md", self.read("docs/requirements.md") + f"\n## {req} {name}\n\n{req_text}\n")
        # 3. 差分を Task 化し、未実装の記述に計画マーカーを付ける
        self.tri("task", "new", f"{name} feature", "--refs", req, "--code", f"src/{name}.py")
        self.write("docs/design.md", self.read("docs/design.md") +
                   f"\n### {name}\n\n{req} を実現する。（計画: {task}）\n{design_text} 実装は `src/{name}.py`。\n")
        tpath = next(self.path("docs/tasks").glob(f"{task}*.md")).relative_to(self.root).as_posix()
        t = self.read(tpath).replace("<!-- 観測可能な振る舞い1つ -->", f"{name} が動く")
        t = t.replace("<!-- `実行するコマンド` または 手動: 確認方法 -->", f"`python3 src/{name}.py`")
        self.write(tpath, t)
        # 9a. 作業中の発見をノートへ
        self.tri("note", "add", f"{name}: 標準入力が空のとき例外になる。空なら何もしないのが妥当", "--task", task)
        # 4. 実装と検証
        self.write(f"src/{name}.py", f"print('{name} ok')\n")
        code, _ = self.tri("task", "verify", task)
        assert code == 0, f"verify failed {task}"
        # 5. Docs を実装済みの状態へ
        if self.mode == "disciplined":
            self.write("docs/design.md", self.read("docs/design.md").replace(f"（計画: {task}）", ""))
        # 9b. ノートの知見を Docs へ昇格し、ノートから削除
        if self.mode == "disciplined":
            self.write("docs/design.md", self.read("docs/design.md").replace(
                f"実装は `src/{name}.py`。", f"実装は `src/{name}.py`。空の入力では何もしない。"))
            inbox = self.read("docs/notes/inbox.md")
            keep = [blk for blk in inbox.split("\n## ") if f"{name}: 標準入力" not in blk]
            self.write("docs/notes/inbox.md", "\n## ".join(keep))
        # 6. 技術判断の変更（サイクル 3 で保存方式を変える）
        if i == 3:
            d = self.read("docs/design.md")
            if self.mode == "disciplined":
                d = d.replace(STORAGE_OLD, STORAGE_NEW)
            else:
                d = d.replace(STORAGE_OLD, STORAGE_OLD + "\n当初は JSON だったが、件数増加により SQLite に変更した。" + STORAGE_NEW)
            self.write("docs/design.md", d)
            if self.mode == "disciplined":
                self.tri("log", "Changed", "保存方式を JSON から SQLite へ変更（件数増加に伴う検索性能のため）")
        # 7. CHANGELOG と完了
        code, out = self.tri("task", "close", task)
        if code != 0 and self.mode == "careless":
            self.log.append(f"cycle {i}: close 拒否 → --force（{out.splitlines()[1] if len(out.splitlines()) > 1 else out}）")
            self.tri("task", "close", task, "--force", "急いでいる")
        elif code != 0:
            raise AssertionError(out)
        if self.mode == "disciplined":
            self.tri("log", "Added", req_text, "--refs", task)
        # 8. 次の Task を追加（次サイクルの前触れ）＋ 10. 引き継ぎ
        if self.mode == "disciplined":
            self.tri("note", "handoff", f"{task} 完了。次は {FEATURES[(i + 1) % len(FEATURES)][0]} の要求定義から")
        else:
            self.tri("note", "add", f"引き継ぎ: {task} 完了。次は {FEATURES[(i + 1) % len(FEATURES)][0]}")
        self.git("add", "-A")
        self.git("commit", "-qm", f"cycle {i}")

    # --- 計測 --------------------------------------------------------------------
    def metrics(self, i: int) -> dict:
        p = Project(self.root)
        issues = check.run(p)
        docs_tokens = sum(md.estimate_tokens(d.text) for d in p.docs.values() if d.kind in ("goal", "doc"))
        notes_tokens = sum(e.tokens for e in notes.entries(p))
        handoffs = len(notes.read_handoff(p))
        # 10. 新しいセッション: status → 進行中 Task の文脈取得
        last = FEATURES[i % len(FEATURES)][0] + str(i // len(FEATURES) or "")
        self.tri("task", "new", "next feature", "--refs", f"REQ-{i + 1:04d}", "--code", f"src/{last}.py")
        p2 = Project(self.root)
        tid = sorted(str(d.fm["id"]) for d in p2.task_docs())[-1]
        t0 = time.perf_counter()
        r = resolve.context(p2, [tid])
        ms = (time.perf_counter() - t0) * 1000
        status_ok = "引き継ぎ" in self.tri("status")[1] if self.mode == "disciplined" else None
        self.tri("task", "drop", tid, "--reason", "計測用")
        self.git("add", "-A")
        self.git("commit", "-qm", f"measure {i}")
        return {
            "cycle": i + 1,
            "errors": sum(1 for x in issues if x.level == "error"),
            "history": sum(1 for x in issues if x.code == "history"),
            "duplicate": sum(1 for x in issues if x.code == "duplicate"),
            "stale_marker": sum(1 for x in issues if x.code == "stale-marker"),
            "broken": sum(1 for x in issues if x.code.startswith("broken")),
            "docs_tokens": docs_tokens,
            "notes_tokens": notes_tokens,
            "handoff_files": handoffs,
            "context_tokens": r.used,
            "context_ms": round(ms, 1),
            "status_has_handoff": status_ok,
            "old_storage_text": "JSON ファイル" in self.read("docs/design.md"),
        }


def run(cycles: int = 8, mode: str = "disciplined", root: Path | None = None) -> tuple[list[dict], list[str]]:
    with tempfile.TemporaryDirectory() as tmp:
        sim = Sim(root or Path(tmp) / "memo", mode)
        sim.setup()
        rows = []
        for i in range(cycles):
            sim.cycle(i)
            rows.append(sim.metrics(i))
        return rows, sim.log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cycles", type=int, default=8)
    ap.add_argument("--mode", choices=("disciplined", "careless"), default="disciplined")
    a = ap.parse_args()
    rows, log = run(a.cycles, a.mode)
    cols = list(rows[0])
    print("| " + " | ".join(cols) + " |")
    print("|" + "---|" * len(cols))
    for r in rows:
        print("| " + " | ".join(str(r[c]) for c in cols) + " |")
    for line in log:
        print(f"- {line}")


if __name__ == "__main__":
    main()
