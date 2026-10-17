#!/usr/bin/env python3
"""Tri-SSD CLI — 知識ライフサイクル管理とコンテキスト最適化のための決定的処理。

標準ライブラリのみで動作する。プロジェクトルート（docs/ の親）で実行するか --root を指定する。

    python3 tri.py status                       # 現在位置（Task・引き継ぎ・健全性）
    python3 tri.py context T-0003 --emit        # Task に必要な Docs セクションだけを取得
    python3 tri.py impact --git                 # 作業差分から見直すべき Docs を逆引き
    python3 tri.py check [--changed]            # 参照切れ・履歴汚染・重複・肥大化の検査
    python3 tri.py task new|list|verify|record|close|drop|start ...
    python3 tri.py handoff "現在位置・次の一手"     # 引き継ぎを上書き
    python3 tri.py log Changed "..." --refs T-0003
    python3 tri.py gaps | id T | init | migrate [--apply]

終了コード: 0 = 正常 / 1 = 検査エラー・ゲート未達 / 2 = 引数・対象の誤り / 3 = 予算超過で必須情報を省略
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import re
import signal
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
if hasattr(signal, "SIGPIPE"):
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # head 等へのパイプで BrokenPipeError を出さない
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from trissd import admin, check, md, notes, resolve, tasks  # noqa: E402
from trissd.project import Project  # noqa: E402

SCRIPT = Path(__file__).resolve().as_posix()


def _stdin_json() -> dict:
    if sys.stdin is None or sys.stdin.isatty():
        return {}
    try:
        return json.loads(sys.stdin.read() or "{}")
    except (json.JSONDecodeError, OSError):
        return {}


def cmd_init(a):
    created = admin.init(Path(a.root), a.name)
    print("# Tri-SSD 初期化\n")
    print("\n".join(f"- 作成: {c}" for c in created) or "- 既に初期化済み（変更なし）")
    print("\n次: docs/goal.md を記入し、あるべき状態を Docs に書く。差分は task new で Task にする")
    return 0


def cmd_status(a):
    root = Path(a.root)
    if a.hook:
        data = _stdin_json()
        root = Path(data.get("cwd") or a.root)
        if not admin.is_project(root):
            return 0
    print(admin.status(Project(root), SCRIPT, a.hook))
    return 0


def cmd_context(a):
    t0 = time.perf_counter()
    p = Project(a.root)
    r = resolve.context(p, a.seeds, a.budget, a.query, not a.no_goal, min_include=a.min_score)
    ms = (time.perf_counter() - t0) * 1000
    print(f"# context: {' '.join(a.seeds) or a.query}（使用 {r.used} / 予算 {r.budget or '無制限'} トークン。"
          f"Goal+Docs 全文は約 {r.full_tokens}。{ms:.0f}ms）")
    for w in r.warnings:
        print(f"⚠️  {w}")
    for u in r.unknown:
        print(f"❌ 起点が見つかりません: {u}")
    print("\n## 選定（* = 必須。スコアは起点からの近さ。← は選定理由）")
    for line in _grouped(p, r.selected):
        print(line)
    if r.omitted:
        print(f"\n## 予算外で省略（{len(r.omitted)} 件。必要なら個別に読む）")
        for i in r.omitted[:15]:
            print(f"- {'*' if i.must else ' '} {i.key}  {i.tokens}t  {i.score}  ← {i.reason}")
    if r.weak:
        print(f"\n## 関連の弱い候補（{len(r.weak)} 件。本文は未取得。必要なら Read する）")
        for i in sorted(r.weak, key=lambda i: -i.score)[:8]:
            print(f"-   {i.key}  {i.tokens}t  {i.score}  ← {i.reason}")
    if r.code:
        print("\n## 関連コード")
        for path, sc in r.code[:15]:
            print(f"- {path}  {sc}")
    if a.emit:
        print("\n## 本文")
        chosen = {i.key for i in r.selected}
        files = list(dict.fromkeys(i.key.split("#")[0] for i in r.selected))
        for path in files:
            doc = p.docs[path]
            secs = [s for s in doc.sections if s.key in chosen and s.text.strip()]
            if not secs:
                continue
            print(f"\n===== {path} =====")
            last = None
            for s in secs:
                if last is not None and s.index != last + 1:
                    print("\n…")
                if last is None or s.index != last + 1:
                    crumbs, cur = [], doc.sections[s.parent] if s.parent is not None else None
                    while cur is not None and cur.index != 0:
                        crumbs.append(cur.title)
                        cur = doc.sections[cur.parent] if cur.parent is not None else None
                    if crumbs:
                        print(f"（位置: {' › '.join(reversed(crumbs))}）")
                print(s.text)
                last = s.index
    return 2 if r.unknown else (3 if r.omitted_must else 0)


def _grouped(p: Project, items) -> list[str]:
    """同じファイルの全セクションが選ばれていれば1行（全体）にまとめる。"""
    by_file: dict[str, list] = {}
    for i in items:
        by_file.setdefault(i.key.split("#")[0], []).append(i)
    out = []
    for path, its in by_file.items():
        nonempty = {s.key for s in p.docs[path].sections if s.text.strip()}
        if len(its) > 1 and nonempty <= {i.key for i in its}:
            top = max(its, key=lambda i: i.score)
            out.append(f"- {'*' if any(i.must for i in its) else ' '} {path}（全体） {sum(i.tokens for i in its)}t"
                       f"  {top.score}  ← {top.reason if top.reason != 'seed' or top.score == 1 else 'goal'}")
            continue
        for i in its:
            out.append(f"- {'*' if i.must else ' '} {i.key}  {i.tokens}t  {i.score}  ← {i.reason}"
                       f"{' [keyword]' if i.fallback else ''}")
    return out


def _git_changes(root: Path, base: str) -> tuple[list[str], dict[str, set[int]]]:
    def git(*args):
        r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f"error: git {' '.join(args)}: {r.stderr.strip()}")
        return r.stdout
    names = git("diff", "--name-only", base, "--").split("\n") + git("ls-files", "-o", "--exclude-standard").split("\n")
    paths = sorted({n for n in names if n and not tasks.is_artifact(n)})
    lines: dict[str, set[int]] = {}
    for path in paths:
        if not path.endswith(".md"):
            continue
        diff = git("diff", "-U0", base, "--", path)
        if not diff:
            continue  # 未追跡ファイルはファイル全体を対象にする
        changed = set()
        for h in re.finditer(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", diff, re.M):
            start, n = int(h.group(1)), int(h.group(2) or 1)
            changed |= set(range(start - 1, start - 1 + max(n, 1)))
        lines[path] = changed
    return paths, lines


def cmd_impact(a):
    root = Path(a.root)
    paths, lines = list(a.paths), {}
    if a.git is not None:
        gp, lines = _git_changes(root, a.git)
        paths += gp
    if not paths:
        print("変更パスがありません（パスを指定するか --git）")
        return 0
    p = Project(root)
    res = resolve.impact(p, paths, lines)
    print(f"# impact: {len(paths)} パス")
    if res["docs"]:
        print("\n## 見直すべき Docs（記述が変更後の実装と一致しているか確認）")
        for doc, hits in res["docs"].items():
            print(f"- {doc}")
            for h in hits:
                print(f"  - {h.key}  {h.score}  ← {h.reason}")
    else:
        print("\n影響する Docs はありません")
    if res["tasks"]:
        print("\n## 関係する進行中 Task")
        for t, why in res["tasks"].items():
            print(f"- {t}  ← {why}")
    code_uncovered = [u for u in res["uncovered"] if not u.startswith("docs/") and u != "CHANGELOG.md"]
    if code_uncovered:
        print("\n## Docs から参照されていない変更（記述不要なら対応不要）")
        for u in code_uncovered[:30]:
            print(f"- {u}")
    return 0


def cmd_check(a):
    root = Path(a.root)
    target = a.file
    if a.hook:
        data = _stdin_json()
        root = Path(data.get("cwd") or a.root)
        fp = (data.get("tool_input") or {}).get("file_path") or ""
        if not fp or not admin.is_project(root):
            return 0
        try:
            target = Path(fp).resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            return 0
        if not target.endswith(".md") or not (target.startswith("docs/") or target == "CHANGELOG.md"):
            return 0
    p = Project(root)
    issues = check.run(p, a.changed, focus=target if a.hook else None)
    if target:
        issues = [i for i in issues if i.path == target or (i.code == "duplicate" and target in i.msg)]
    errs = [i for i in issues if i.level == "error"]
    if a.hook:
        if issues:
            msg = (f"Tri-SSD check（{target}）: 以下を確認し、必要なら修正すること。"
                   "履歴汚染は現在の状態へ書き換えて経緯は CHANGELOG へ、意図的なら行末に <!-- tri:ok -->。\n"
                   + "\n".join(str(i) for i in issues[:20]))
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}},
                             ensure_ascii=False))
        return 0
    for i in issues:
        print(i)
    print(f"\n検査完了: エラー {len(errs)} / 警告 {len(issues) - len(errs)}")
    return 1 if errs or (a.strict and issues) else 0


def cmd_gaps(a):
    p = Project(a.root)
    mk = admin.marker_list(p)
    print("# 差分マーカー（Docs のうち現在の実装と一致しない・未確定の記述）")
    if not mk:
        print("（なし）")
    for kind, path, ln, id_, line in mk:
        st = f" → {id_} [{p.task_status(id_) or '未定義'}]" if id_ else ""
        print(f"- （{kind}）{path}:{ln}{st}  {line[:90]}")
    ur = admin.untracked_reqs(p)
    if ur:
        print(f"\n## どの Task からも参照されていない REQ（{len(ur)} 件。実装・検証状況が未確認の候補）")
        for r in ur:
            print(f"- {r}  {p.defs[r][0]}")
    return 0


def cmd_task(a):
    p = Project(a.root)
    if a.tcmd == "new":
        rel = tasks.new(p, a.title, a.refs or [], a.code or [], a.goal or "", a.slug)
        print(f"作成: {rel}\n次: 目的の状態・受け入れ条件（AC と 検証: `cmd`）を記入する")
        return 0
    if a.tcmd == "list":
        fp = tasks.fingerprint(p.root)
        for d in sorted(p.task_docs(a.all), key=lambda d: str(d.fm.get("id"))):
            ok, n, stale = tasks.progress(d, None if d.kind == "task_done" else fp)  # 完了 Task は履歴。失効を数えない
            print(f"{d.fm.get('id')}  [{d.fm.get('status')}]  AC {ok}/{n}{f' stale {stale}' if stale else ''}  "
                  f"{tasks.title_of(d)}  ({d.path})")
        return 0
    if a.tcmd in ("start", "status"):
        st = "active" if a.tcmd == "start" else a.state
        if st not in ("open", "active", "blocked"):
            raise SystemExit("error: status は open / active / blocked（完了は close、中止は drop）")
        cur = tasks.find_task(p, a.id)
        was = str(cur.fm.get("status")) if cur else None
        path = tasks.set_status(p, a.id, st)
        print(f"{a.id}: 既に {st}（{path}）" if was == st else f"{a.id}: status {was} → {st}（{path}）")
        others = [str(d.fm.get("id")) for d in p.task_docs() if d.fm.get("status") == "active" and d.fm.get("id") != a.id]
        if st == "active" and others:
            print(f"⚠️  他にも active の Task があります: {', '.join(others)}（並行が意図どおりでなければ task status <ID> open|blocked）")
        return 0
    if a.tcmd == "verify":
        results = tasks.verify(p, a.id, a.ac)
        bad = 0
        for ac, res, detail in results:
            print(f"- {ac.label} {res}  {detail}")
            bad += res == "FAIL"
        manual = [ac.label for ac, res, _ in results if res == "MANUAL"]
        if manual:
            print(f"\n手動確認が必要: {', '.join(manual)} → 確認後 task record {a.id} <AC> pass --note \"確認内容\"")
        print("\n※ PASS は検証コマンドが成功したことだけを示す。そのコマンドが AC の文言どおりの振る舞いを確かめているか、"
              "AC 全体で「目的の状態」を覆っているかは別途確認すること")
        return 1 if bad else 0
    if a.tcmd == "report":
        print(tasks.report(p, a.id), end="")
        return 0
    if a.tcmd == "record":
        print(tasks.record(p, a.id, a.ac, a.result, a.note))
        return 0
    if a.tcmd in ("close", "drop"):
        fails, dest = tasks.close(p, a.id, a.force if a.tcmd == "close" else a.reason, drop=a.tcmd == "drop")
        if dest is None:
            print(f"# {a.id} は完了条件を満たしていません")
            print("\n".join(f"- {f}" for f in fails))
            return 1
        if fails:
            print("⚠️  ゲート未達のまま強制完了:\n" + "\n".join(f"- {f}" for f in fails))
        print(f"{a.id}: {'中止' if a.tcmd == 'drop' else '完了'} → {dest}")
        print("\n次: 仕様・設計に意味のある変更があれば `log` で CHANGELOG に記録。"
              "`impact --git` で見直すべき Docs を確認")
        return 0
    return 2


def cmd_handoff(a):
    text = sys.stdin.read() if a.text == "-" else a.text
    print(f"更新: {notes.handoff(Project(a.root), text, a.local)}（上書き。過去の引き継ぎは残らない）")
    return 0


def cmd_log(a):
    print(f"CHANGELOG [Unreleased] {a.type.capitalize()}: {admin.log(Path(a.root), a.type, a.text, a.refs or [])}")
    return 0


def cmd_id(a):
    p = Project(a.root)
    n = p.max_id(a.prefix)
    for i in range(a.count):
        print(f"{a.prefix}-{n + 1 + i:04d}")
    return 0


def cmd_migrate(a):
    for line in admin.migrate(Path(a.root), a.apply):
        print(f"- {line}" if not line.startswith("（") else line)
    if a.apply:
        print(f"\n次: python3 {SCRIPT} check で参照切れを確認し、goal.md から REQ 詳細を Docs へ分離（Goal は短く）")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="tri.py", description="Tri-SSD CLI")
    ap.add_argument("--root", default=os.environ.get("TRI_SSD_ROOT", "."), help="プロジェクトルート（既定: カレント）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="docs/goal.md・tasks/・notes/・CHANGELOG・.tri-ssd/ を作成（冪等）")
    s.add_argument("--name")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("status", help="現在位置: Task・引き継ぎ・健全性")
    s.add_argument("--hook", action="store_true", help="SessionStart フック用（Tri-SSD でなければ何も出さない）")
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("context", help="起点（Task/ID/パス/コード）に必要なセクションを選定")
    s.add_argument("seeds", nargs="*")
    s.add_argument("--budget", type=int, default=6000, help="トークン予算（0 = 無制限。既定 6000）")
    s.add_argument("--query", help="キーワード探索を併用（依存が不明なとき）")
    s.add_argument("--emit", action="store_true", help="選定セクションの本文も出力する")
    s.add_argument("--no-goal", action="store_true", help="Goal を含めない")
    s.add_argument("--min-score", type=float, default=resolve.MIN_INCLUDE,
                   help=f"必須でない項目の選定下限（既定 {resolve.MIN_INCLUDE}。0 で予算まで詰める）")
    s.set_defaults(fn=cmd_context)

    s = sub.add_parser("impact", help="変更パスから見直すべき Docs・関係 Task を逆引き")
    s.add_argument("paths", nargs="*")
    s.add_argument("--git", nargs="?", const="HEAD", help="git の作業差分を対象にする（既定 base: HEAD）")
    s.set_defaults(fn=cmd_impact)

    s = sub.add_parser("check", help="参照切れ・ID 重複・履歴汚染・重複記述・肥大化・マーカー・Task 書式")
    s.add_argument("--changed", nargs="?", const="HEAD", help="git 差分の検査も行う（CHANGELOG 記録漏れ・追記偏重）")
    s.add_argument("--file", help="指定ファイルの指摘だけを表示")
    s.add_argument("--hook", action="store_true", help="PostToolUse フック用（stdin の JSON を読む）")
    s.add_argument("--strict", action="store_true", help="警告でも終了コード 1")
    s.set_defaults(fn=cmd_check)

    s = sub.add_parser("gaps", help="Docs の差分マーカー（計画・保留・未確定・未検証）と未追跡 REQ の一覧")
    s.set_defaults(fn=cmd_gaps)

    s = sub.add_parser("task", help="Task の作成・検証・完了")
    ts = s.add_subparsers(dest="tcmd", required=True)
    t = ts.add_parser("new")
    t.add_argument("title")
    t.add_argument("--refs", nargs="*", help="満たすべき仕様（ID・docs パス#見出し）")
    t.add_argument("--code", nargs="*", help="作業範囲のコードパス・glob")
    t.add_argument("--goal", help="目的の状態（1〜3行）")
    t.add_argument("--slug", help="ファイル名の英数部分（題が日本語のとき）")
    t = ts.add_parser("list")
    t.add_argument("--all", action="store_true", help="完了済みも表示")
    t = ts.add_parser("start")
    t.add_argument("id")
    t = ts.add_parser("status")
    t.add_argument("id")
    t.add_argument("state")
    t = ts.add_parser("verify", help="AC の 検証: `cmd` を実行し証跡を記録")
    t.add_argument("id")
    t.add_argument("--ac", nargs="*", help="対象 AC（既定: 全 AC）")
    t = ts.add_parser("report", help="人間向けの報告（目的・満たす仕様・検証・判断・変更・CHANGELOG）を既存の記録から組み立てる")
    t.add_argument("id")
    t = ts.add_parser("record", help="手動確認の結果を記録")
    t.add_argument("id")
    t.add_argument("ac")
    t.add_argument("result", choices=("pass", "fail", "PASS", "FAIL"))
    t.add_argument("--note", required=True)
    t = ts.add_parser("close", help="完了ゲートを通過したら done にして _done/ へ")
    t.add_argument("id")
    t.add_argument("--force", metavar="REASON", help="ゲート未達でも理由を記録して完了")
    t = ts.add_parser("drop", help="中止して _done/ へ")
    t.add_argument("id")
    t.add_argument("--reason", required=True)
    s.set_defaults(fn=cmd_task)

    s = sub.add_parser("handoff", help="引き継ぎ（現在位置・次の一手・未解決の問い）を上書き。- で stdin")
    s.add_argument("text")
    s.add_argument("--local", action="store_true", help=".tri-ssd/（git 管理外）に書く")
    s.set_defaults(fn=cmd_handoff)

    s = sub.add_parser("log", help="CHANGELOG の [Unreleased] に追記")
    s.add_argument("type", help="Added / Changed / Deprecated / Removed / Fixed / Security")
    s.add_argument("text")
    s.add_argument("--refs", nargs="*")
    s.set_defaults(fn=cmd_log)

    s = sub.add_parser("id", help="次の連番 ID（永久欠番を考慮）")
    s.add_argument("prefix", choices=md.ID_PREFIXES)
    s.add_argument("--count", type=int, default=1)
    s.set_defaults(fn=cmd_id)

    s = sub.add_parser("migrate", help="旧 Tri-SSD（L0-L3）から移行（既定はドライラン）")
    s.add_argument("--apply", action="store_true")
    s.set_defaults(fn=cmd_migrate)

    return ap


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    if not Path(a.root).is_dir():
        print(f"error: {a.root} がありません", file=sys.stderr)
        return 2
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
