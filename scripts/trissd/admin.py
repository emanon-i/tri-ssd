"""初期化・状況表示・差分マーカー一覧・CHANGELOG 追記・旧 Tri-SSD からの移行。"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

from . import md, notes, tasks
from .project import CHANGELOG, DONE, GOAL, MARKER_RE, NOTES, TASKS, Project

TEMPLATES = Path(__file__).resolve().parents[2] / "templates"


def template(file: str, **values: str) -> str:
    """templates/<file> を読み、{{key}} を置き換える（書式の正はテンプレートファイル）。"""
    text = (TEMPLATES / file).read_text(encoding="utf-8")
    for k, v in values.items():
        text = text.replace("{{" + k + "}}", v)
    return text

CHANGE_TYPES = ("Added", "Changed", "Deprecated", "Removed", "Fixed", "Security")


def init(root: Path, name: str | None = None) -> list[str]:
    created = []
    for d in (TASKS, NOTES):
        path = root / d
        if not path.exists():
            path.mkdir(parents=True)
            (path / ".gitkeep").touch()
            created.append(d + "/")
    goal = root / GOAL
    if not goal.exists():
        goal.write_text(template("goal.md", name=name or root.resolve().name), encoding="utf-8")
        created.append(GOAL)
    cl = root / CHANGELOG
    if not cl.exists():
        cl.write_text(template("changelog.md"), encoding="utf-8")
        created.append(CHANGELOG)
    if not (root / ".tri-ssd" / ".gitignore").exists():
        notes.ensure_local(root)
        created.append(".tri-ssd/（git 管理外）")
    return created


def is_project(root: Path) -> bool:
    return (root / GOAL).exists() or (root / TASKS).is_dir()


def marker_list(p: Project) -> list[tuple[str, str, int, str, str]]:
    """(種別, パス, 行, ID, 行テキスト)。Docs のうち「現在の実装」でない記述の一覧。"""
    out = []
    for d in p.docs.values():
        if d.kind not in ("goal", "doc"):
            continue
        for ln, line in md.prose_lines(d.text):
            for m in MARKER_RE.finditer(md.strip_inline_code(line)):
                out.append((m.group(1), d.path, ln + 1, m.group(2) or "", line.strip()))
    return out


def untracked_reqs(p: Project) -> list[str]:
    """どの Task（進行中・完了）からも参照されていない REQ。実装状況が未確認の候補。"""
    referenced = set()
    for d in p.docs.values():
        if d.kind in ("task", "task_done"):
            referenced |= {m.group(0) for m in md.ID_RE.finditer(d.text)}
    return sorted(i for i in p.defs if i.startswith("REQ-") and i not in referenced)


def status(p: Project, script: str, hook: bool = False) -> str:
    from .check import run as run_check
    out = []
    goal = p.docs.get(GOAL)
    gtitle = next((s.title for s in goal.sections if s.level == 1), GOAL) if goal else "（docs/goal.md がありません）"
    out.append(f"# Tri-SSD 状況（{p.root.name}）")
    out.append(f"Goal: {gtitle}" + (f"（{GOAL}, 約 {md.estimate_tokens(goal.text)} トークン）" if goal else ""))
    fp = None if hook else tasks.fingerprint(p.root)  # フックでは全ファイルのハッシュを避ける（大規模リポジトリで遅い）
    active = sorted(p.task_docs(), key=lambda d: str(d.fm.get("id")))
    counts: dict[str, int] = {}
    for d in active:
        counts[str(d.fm.get("status"))] = counts.get(str(d.fm.get("status")), 0) + 1
    done = sum(1 for d in p.task_docs(True) if d.kind == "task_done")
    out.append("Tasks: " + (" / ".join(f"{k} {v}" for k, v in sorted(counts.items())) or "進行中なし") + f"（完了 {done}）")
    for d in active[:15]:
        ok, n, stale = tasks.progress(d, fp)
        flag = f" stale {stale}" if stale else ""
        out.append(f"  {d.fm.get('id')} [{d.fm.get('status')}] AC {ok}/{n}{flag}  {tasks.title_of(d)}")
    for path, text in notes.read_handoff(p):
        lines = text.strip().splitlines()
        out.append(f"引き継ぎ（{path}）:")
        out += ["  " + x for x in lines[1:31] if x.strip()]
        if len(lines) > 31:
            out.append(f"  …（残り {len(lines) - 31} 行は {path}）")
    issues = run_check(p)
    errs = sum(1 for i in issues if i.level == "error")
    out.append(f"Check: エラー {errs} / 警告 {len(issues) - errs}" + ("（tri check で詳細）" if issues else ""))
    mk = marker_list(p)
    if mk:
        c: dict[str, int] = {}
        for k, *_ in mk:
            c[k] = c.get(k, 0) + 1
        out.append("差分マーカー: " + " / ".join(f"{k} {v}" for k, v in c.items()) + "（tri gaps で一覧）")
    out.append(f"CLI: python3 {script} <command>（context <Task-ID> --emit で作業に必要な文脈を取得）")
    return "\n".join(out)


def log(root: Path, kind: str, text: str, refs: list[str]) -> str:
    kind = kind.capitalize()
    if kind not in CHANGE_TYPES:
        raise SystemExit(f"error: 種別は {', '.join(CHANGE_TYPES)} のいずれか")
    path = root / CHANGELOG
    content = path.read_text(encoding="utf-8") if path.exists() else template("changelog.md")
    lines = content.splitlines()
    head = next((i for i, x in enumerate(lines) if re.match(r"^## \[?Unreleased\]?", x, re.I)), None)
    if head is None:
        first = next((i for i, x in enumerate(lines) if x.startswith("## ")), len(lines))
        lines[first:first] = ["## [Unreleased]", ""]
        head = first
    end = next((i for i in range(head + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    sub = next((i for i in range(head + 1, end) if lines[i].strip() == f"### {kind}"), None)
    entry = f"- {text.strip()}" + (f"（{', '.join(refs)}）" if refs else "")
    if sub is None:
        order = CHANGE_TYPES.index(kind)
        insert = end
        for i in range(head + 1, end):
            m = re.match(r"^### (\w+)", lines[i])
            if m and m.group(1) in CHANGE_TYPES and CHANGE_TYPES.index(m.group(1)) > order:
                insert = i
                break
        while insert > head + 1 and not lines[insert - 1].strip():
            insert -= 1
        lines[insert:insert] = ["", f"### {kind}", "", entry, ""]
    else:
        stop = next((i for i in range(sub + 1, end) if lines[i].startswith("### ")), end)
        insert = stop
        while insert > sub + 1 and not lines[insert - 1].strip():
            insert -= 1
        lines.insert(insert, entry)
    text_out = "\n".join(lines).rstrip("\n") + "\n"
    text_out = re.sub(r"\n{3,}", "\n\n", text_out)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text_out)
    return entry


# --- 旧 Tri-SSD（v5 以前: L0-L3）からの移行 ----------------------------------------------

PATH_REWRITES = [
    ("l1_requirements/vision.md", "goal.md"),
    ("l1_requirements/", ""),
    ("l2_foundation/", "design/"),
    ("l3_phases/_archive/", "tasks/_done/"),
    ("l3_phases/", "tasks/"),
    ("l0_ideas/", "notes/ideas/"),
]
MARKER_REWRITES = [
    (re.compile(r"<!--\s*TODO:\s*要確認\s*-->"), "（未確定）"),
    (re.compile(r"[（(]未確認・[^）)]*[）)]"), "（未検証）"),
]
STATUS_MAP = {"planned": "open", "in_progress": "active", "done": "done"}


def migrate(root: Path, apply: bool = False) -> list[str]:
    docs = root / "docs"
    plan: list[tuple[str, Path, Path | None]] = []   # (操作, 元, 先)
    l1, l2, l3, l0 = (docs / "l1_requirements", docs / "l2_foundation", docs / "l3_phases", docs / "l0_ideas")
    if not any(d.exists() for d in (l1, l2, l3, l0)):
        return ["旧 Tri-SSD の構造（docs/l1_requirements 等）が見つかりません。移行は不要です"]
    if (l1 / "vision.md").exists():
        plan.append(("move", l1 / "vision.md", docs / "goal.md"))
    for base, dest in ((l1, docs), (l2, docs / "design"), (l0, docs / "notes" / "ideas")):
        if base.exists():
            for f in sorted(base.rglob("*")):
                if f.is_file() and f.name != ".gitkeep" and not (base == l1 and f.name == "vision.md"):
                    plan.append(("move", f, dest / f.relative_to(base)))
    if l3.exists():
        for entry in sorted(l3.rglob("*")):
            rel = entry.relative_to(l3)
            archived = rel.parts[0] == "_archive"
            inner = Path(*rel.parts[1:]) if archived else rel
            if not inner.parts:
                continue
            top = l3 / ("_archive" if archived else "") / inner.parts[0]
            if entry != top:
                continue  # 各フェーズの最上位（ファイル or フォルダ）だけを扱う
            if entry.is_dir():
                plan.append(("merge-phase", entry, None))
            elif entry.suffix == ".md":
                plan.append(("phase", entry, None))
    readme = docs / "README.md"
    if readme.exists() and "ドキュメント構成（Tri-SSD）" in readme.read_text(encoding="utf-8"):
        plan.append(("delete", readme, None))

    report = []
    for op, src, dst in plan:
        if op == "move":
            report.append(f"移動: {src.relative_to(root)} → {dst.relative_to(root)}")
        elif op == "delete":
            report.append(f"削除: {src.relative_to(root)}（旧在り処マップ）")
        else:
            report.append(f"Task 化: {src.relative_to(root)} → docs/tasks/（status 変換・完了済みは _done/）")
    report.append("書き換え: パス参照（l1_requirements→goal.md 等）・旧マーカー（TODO: 要確認→（未確定）、（未確認…）→（未検証））")
    if not apply:
        return ["（ドライラン。--apply で実行）"] + report

    for op, src, dst in plan:
        if op == "move":
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            if dst.name == "goal.md":
                dst.write_text(re.sub(r"\]\(\.\./", "](", dst.read_text(encoding="utf-8")), encoding="utf-8")
        elif op == "delete":
            src.unlink()
        else:
            _migrate_phase(root, src, merge=(op == "merge-phase"))
    for old in (l1, l2, l3, l0):
        if old.exists():
            for g in old.rglob(".gitkeep"):
                g.unlink()
            for d in sorted((x for x in old.rglob("*") if x.is_dir()), key=lambda x: -len(x.parts)):
                if not any(d.iterdir()):
                    d.rmdir()
            if not any(old.iterdir()):
                old.rmdir()
    for f in list(docs.rglob("*.md")):
        text = f.read_text(encoding="utf-8")
        new = text
        for a, b in PATH_REWRITES:
            new = new.replace(a, b)
        for pat, rep in MARKER_REWRITES:
            new = pat.sub(rep, new)
        if new != text:
            f.write_text(new, encoding="utf-8")
    report += init(root)
    return report


def _migrate_phase(root: Path, src: Path, merge: bool):
    if merge:
        phase = src / "_phase.md"
        parts = [phase.read_text(encoding="utf-8")] if phase.exists() else []
        for f in sorted(src.glob("F-*.md")):
            body = f.read_text(encoding="utf-8")
            fm, start = md.parse_frontmatter(body)
            parts.append("\n".join(body.splitlines()[start:]))
        text = "\n\n".join(x.strip("\n") for x in parts) + "\n"
        name = src.name + ".md"
    else:
        text = src.read_text(encoding="utf-8")
        name = src.name
    fm, _ = md.parse_frontmatter(text)
    m = md.ID_RE.match(name)
    if "id" not in fm and m:
        text = md.set_fm_value(text, "id", m.group(0))
    st = STATUS_MAP.get(str(fm.get("status", "planned")), "open")
    archived = "_archive" in src.parts
    if archived:
        st = "done"
    text = md.set_fm_value(text, "status", st)
    dest_dir = root / (DONE if st == "done" else TASKS)
    dest_dir.mkdir(parents=True, exist_ok=True)
    (dest_dir / name).write_text(text, encoding="utf-8")
    if src.is_dir():
        shutil.rmtree(src)
    else:
        src.unlink()
