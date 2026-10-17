"""Task: あるべき状態（Docs）と現実（コード等）の差分を解消する検証可能な作業単位。

完了は自己申告ではなく、受け入れ条件（AC）ごとの検証証跡で判定する:
  - AC の `検証:` 行のコマンドを実行し、結果を「検証記録」へ追記する（task verify）
  - 手動確認の AC は確認者のメモ付きで記録する（task record）
  - 証跡には作業ツリーの指紋（docs/ を除くコードの内容ハッシュ）を残し、
    検証後にコードが変わった証跡は古いもの（stale）として扱う
"""
from __future__ import annotations

import datetime as dt
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from . import md
from .project import DONE, MARKER_RE, TASKS, Project

AC_HEAD_RE = re.compile(r"受け入れ条件|acceptance", re.I)
EVIDENCE_HEAD_RE = re.compile(r"検証記録|evidence", re.I)
CHECK_RE = re.compile(r"^(\s{0,1})[-*] \[( |x|X)\] (.*)$")
LABEL_RE = re.compile(r"^(AC\d+)\s*[:：.]?\s*")
VERIFY_RE = re.compile(r"^\s+[-*]\s*(?:検証|verify)\s*[:：]\s*(.*)$", re.I)
EVIDENCE_RE = re.compile(
    r"^- (\d{4}-\d{2}-\d{2}(?: \d{2}:\d{2})?) (AC\d+) (PASS|FAIL)\b(.*?)(?:\s+tree=([0-9a-f]+|none))?\s*$")
CMD_RE = re.compile(r"`([^`]+)`")


@dataclass
class AC:
    label: str
    line: int                  # 0始まり
    checked: bool
    text: str
    verify: str | None = None
    commands: list[str] = field(default_factory=list)

    @property
    def manual(self) -> bool:
        return not self.commands


@dataclass
class Evidence:
    when: str
    label: str
    result: str
    detail: str
    tree: str | None

    @property
    def manual(self) -> bool:
        return self.detail.startswith("手動")

    def stale(self, fp: str | None) -> bool:
        """コマンドの証跡だけが、取得後のコード変更で古くなる（手で確かめた記録は失効させない）。"""
        return bool(fp and not self.manual and self.tree and self.tree != "none" and self.tree != fp)


def now() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M")


def today() -> str:
    return dt.date.today().isoformat()


def _section_range(text: str, head_re) -> tuple[int, int] | None:
    secs = md.split_sections("", text, md.parse_frontmatter(text)[1])
    for s in secs[1:]:
        if head_re.search(s.title):
            return s.start, s.subtree_end
    return None


def parse_acs(text: str) -> list[AC]:
    lines = text.splitlines()
    rng = _section_range(text, AC_HEAD_RE)
    ev = _section_range(text, EVIDENCE_HEAD_RE)
    start, end = rng if rng else (0, len(lines))
    acs: list[AC] = []
    fence = False
    for i in range(start, end):
        if md.FENCE_RE.match(lines[i]):
            fence = not fence
        if fence or (ev and ev[0] <= i < ev[1]):
            continue
        m = CHECK_RE.match(lines[i])
        if not m:
            continue
        body = m.group(3)
        lm = LABEL_RE.match(body)
        label = lm.group(1) if lm else f"AC{len(acs) + 1}"
        ac = AC(label, i, m.group(2) != " ", body[lm.end():] if lm else body)
        for j in range(i + 1, min(i + 6, end)):
            vm = VERIFY_RE.match(lines[j])
            if vm:
                ac.verify = md.COMMENT_RE.sub("", vm.group(1)).strip()
                ac.commands = CMD_RE.findall(ac.verify)
                break
            if CHECK_RE.match(lines[j]) or not lines[j].startswith((" ", "\t")):
                break
        acs.append(ac)
    return acs


def parse_evidence(text: str) -> list[Evidence]:
    rng = _section_range(text, EVIDENCE_HEAD_RE)
    if not rng:
        return []
    out = []
    for line in text.splitlines()[rng[0]:rng[1]]:
        m = EVIDENCE_RE.match(line.rstrip())
        if m:
            out.append(Evidence(m.group(1), m.group(2), m.group(3), m.group(4).strip(), m.group(5)))
    return out


def latest(evs: list[Evidence]) -> dict[str, Evidence]:
    out: dict[str, Evidence] = {}
    for e in evs:
        out[e.label] = e  # 記録は追記順なので後勝ち
    return out


ARTIFACT_DIRS = ("__pycache__", "node_modules", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv", ".tox")
ARTIFACT_EXCLUDES = [f":(exclude,glob)**/{d}/**" for d in ARTIFACT_DIRS] + [":(exclude,glob)**/*.pyc"]


def is_artifact(path: str) -> bool:
    """テスト・ビルドの副産物（.gitignore が無くても変更とみなさない）。"""
    return path.endswith(".pyc") or any(part in ARTIFACT_DIRS for part in path.split("/"))


def fingerprint(root: Path) -> str | None:
    """docs/・ローカル領域・CHANGELOG を除く作業ツリーの内容ハッシュ（git の tree id）。

    コミットの有無に依存せず、内容が同じなら同じ値になる。git 管理外なら None。
    """
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(tmp) / "index"))
        try:
            add = subprocess.run(
                ["git", "add", "-A", "--", ".", ":(exclude)docs", ":(exclude).tri-ssd", ":(exclude)CHANGELOG.md",
                 *ARTIFACT_EXCLUDES],
                cwd=root, env=env, capture_output=True, text=True, timeout=120)
            if add.returncode != 0:
                return None
            tree = subprocess.run(["git", "write-tree"], cwd=root, env=env, capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired):
            return None
        return tree.stdout.strip()[:12] if tree.returncode == 0 else None


# --- ファイル操作 -------------------------------------------------------------------

def find_task(p: Project, id_: str, include_done: bool = False):
    for d in p.task_docs(include_done):
        if str(d.fm.get("id")) == id_:
            return d
    return None


def title_of(doc) -> str:
    for s in doc.sections[1:]:
        if s.level == 1:
            return md.ID_RE.sub("", s.title, count=1).strip(" :：-")
    return doc.path


def _append_evidence(text: str, lines_to_add: list[str]) -> str:
    rng = _section_range(text, EVIDENCE_HEAD_RE)
    lines = text.splitlines()
    if not rng:
        while lines and not lines[-1].strip():
            lines.pop()
        lines += ["", "## 検証記録", ""]
        insert = len(lines)
    else:
        insert = rng[1]
        while insert > rng[0] + 1 and not lines[insert - 1].strip():
            insert -= 1
        if insert == rng[0] + 1:
            lines.insert(insert, "")
            insert += 1
    lines[insert:insert] = lines_to_add
    return "\n".join(lines) + "\n"


EVIDENCE_WIDTH = 100  # 1行の本文の最大文字数（Markdown の行長制限に収める）


def evidence_lines(stamp: str, label: str, result: str, detail: str, tree: str) -> list[str]:
    """`- 日時 AC PASS 詳細 tree=...` の1行に収め、長い詳細は字下げした継続行に折り返す。"""
    head, rest = detail[:EVIDENCE_WIDTH], detail[EVIDENCE_WIDTH:]
    lines = [f"- {stamp} {label} {result} {head} tree={tree}".replace("  ", " ")]
    while rest:
        lines.append("  " + rest[:EVIDENCE_WIDTH])
        rest = rest[EVIDENCE_WIDTH:]
    return lines


def _set_check(text: str, ac: AC, checked: bool) -> str:
    lines = text.splitlines()
    lines[ac.line] = re.sub(r"\[( |x|X)\]", "[x]" if checked else "[ ]", lines[ac.line], count=1)
    return "\n".join(lines) + "\n"


def _write(p: Project, rel: str, text: str):
    with open(p.root / rel, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


TEMPLATE = """---
id: {id}
status: open
refs: [{refs}]
code: [{code}]
created: {date}
---
# {id} {title}

## 目的の状態

{goal}

## 受け入れ条件

- [ ] AC1: <!-- 観測可能な振る舞い1つ -->
  - 検証: <!-- `実行するコマンド` または 手動: 確認方法 -->

## 検証記録
"""


def new(p: Project, title: str, refs: list[str], code: list[str], goal: str = "", slug: str | None = None) -> str:
    """ファイル名は `T-nnnn-slug.md`。slug は英数の題から作るか --slug で指定（ファイル名は自由に変えてよい。正は frontmatter の id）。"""
    n = max(p.max_id("T"), 0) + 1
    id_ = f"T-{n:04d}"
    words = re.findall(r"[a-z0-9]+", (slug or title).lower())
    slug = "-".join(words)[:40].strip("-") if any(re.search("[a-z]", w) for w in words) else ""
    rel = f"{TASKS}/{id_}{'-' + slug if slug else ''}.md"
    (p.root / TASKS).mkdir(parents=True, exist_ok=True)
    _write(p, rel, TEMPLATE.format(id=id_, title=title, refs=", ".join(refs), code=", ".join(code), date=today(),
                                   goal=goal or "<!-- 完了時に成立している状態。満たすべき Docs の記述（ID・リンク）を参照する -->"))
    return rel


def _git_head(root: Path) -> str | None:
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout.strip()[:12] if r.returncode == 0 else None


def _mark_started(p: Project, text: str) -> str:
    """着手時刻と着手時点のコミットを記録する（完了時に「この Task の間の変更・参照」を求める基準）。"""
    fm, _ = md.parse_frontmatter(text)
    if not fm.get("started"):
        text = md.set_fm_value(text, "started", dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        head = _git_head(p.root)
        if head:
            text = md.set_fm_value(text, "base", head)
    return text


def set_status(p: Project, id_: str, status: str) -> str:
    doc = find_task(p, id_)
    if not doc:
        raise SystemExit(f"error: アクティブな Task {id_} が見つかりません")
    text = md.set_fm_value(doc.text, "status", status)
    _write(p, doc.path, _mark_started(p, text) if status == "active" else text)
    return doc.path


def progress(doc, fp: str | None = None) -> tuple[int, int, int]:
    """(PASS 数, AC 数, stale 数)。"""
    acs = parse_acs(doc.text)
    lt = latest(parse_evidence(doc.text))
    ok = stale = 0
    for ac in acs:
        e = lt.get(ac.label)
        if e and e.result == "PASS":
            ok += 1
            if e.stale(fp):
                stale += 1
    return ok, len(acs), stale


def verify(p: Project, id_: str, only: list[str] | None = None, timeout: int = 900) -> list[tuple[AC, str, str]]:
    doc = find_task(p, id_)
    if not doc:
        raise SystemExit(f"error: アクティブな Task {id_} が見つかりません")
    text = doc.text
    acs = [a for a in parse_acs(text) if not only or a.label in only]
    if not acs:
        raise SystemExit(f"error: {id_} に受け入れ条件がありません（- [ ] AC1: ... と - 検証: `cmd`）")
    results = []
    for ac in acs:
        if ac.manual:
            results.append((ac, "MANUAL", ac.verify or "検証手段が未記載"))
            continue
        ok, detail = True, ""
        for cmd in ac.commands:
            try:
                r = subprocess.run(cmd, shell=True, cwd=p.root, capture_output=True, text=True, timeout=timeout)
                out = (r.stdout + "\n" + r.stderr).strip().splitlines()
                last = next((x.strip() for x in reversed(out) if x.strip()), "")
                detail = f"`{cmd}` → exit {r.returncode}" + (f" 「{last[:100]}」" if last else "")
                if r.returncode != 0:
                    ok = False
                    break
            except subprocess.TimeoutExpired:
                ok, detail = False, f"`{cmd}` → timeout {timeout}s"
                break
        results.append((ac, "PASS" if ok else "FAIL", detail))
    fp = fingerprint(p.root) or "none"
    stamp = now()
    add = []
    for ac, res, detail in results:
        if res == "MANUAL":
            continue
        add += evidence_lines(stamp, ac.label, res, detail, fp)
        text = _set_check(text, ac, res == "PASS")
    if add:
        text = _append_evidence(text, add)
    if str(doc.fm.get("status")) == "open":
        text = md.set_fm_value(text, "status", "active")
    _write(p, doc.path, _mark_started(p, text))
    return results


def _run_all(cmds: list[str], cwd: Path, timeout: int) -> bool:
    for cmd in cmds:
        try:
            if subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout).returncode != 0:
                return False
        except subprocess.TimeoutExpired:
            return False
    return True


def against_base(p: Project, id_: str, labels: list[str], timeout: int = 900) -> dict[str, str]:
    """検証コマンドを着手時点（base）のコードで実行する。着手時点のコードでも通る検証は、変更について何も確かめていない。

    base の作業ツリーを一時的に作り、検証コマンドが名指しする変更済みファイル（新しいテスト等）だけを
    現在の内容で重ねてから実行する。結果: FAIL = 変更を確かめている / PASS = 確かめていない可能性。
    """
    doc = find_task(p, id_)
    base = str(doc.fm.get("base") or "")
    acs = [a for a in parse_acs(doc.text) if a.label in labels and a.commands]
    if not base or not acs:
        return {}
    changed = changed_paths(p.root, base)
    out: dict[str, str] = {}
    with tempfile.TemporaryDirectory() as tmp:
        wt = Path(tmp) / "base"
        r = subprocess.run(["git", "worktree", "add", "--detach", "--quiet", str(wt), base],
                           cwd=p.root, capture_output=True, text=True)
        if r.returncode != 0:
            return {}
        try:
            for ac in acs:
                cmdline = " ".join(ac.commands)
                for f in changed:
                    module = f[:-3].replace("/", ".") if f.endswith(".py") else None
                    named = f in cmdline or (module and module in cmdline) or re.search(
                        rf"(?<![\w/.-]){re.escape(Path(f).name)}(?![\w.-])", cmdline)
                    if named and (p.root / f).is_file():
                        (wt / f).parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(p.root / f, wt / f)
                out[ac.label] = "PASS" if _run_all(ac.commands, wt, timeout) else "FAIL"
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(wt)], cwd=p.root, capture_output=True)
    lines = []
    stamp = now()
    for label, res in out.items():
        meaning = "変更を確かめている" if res == "FAIL" else "着手時点でも通る。振る舞いを変えない Task でなければ変更を確かめていない"
        lines.append(f"- {stamp} {label} 着手時点 {res}（{meaning}）")
    if lines:
        doc = find_task(p, id_)
        _write(p, doc.path, _append_evidence(doc.text, lines))
    return out


DECISION_HEAD_RE = re.compile(r"^判断|^decision", re.I)
BASE_LINE_RE = re.compile(r"^- (\S+ \S+) (AC\d+) 着手時点 (PASS|FAIL)")


def _section_text(text: str, head_re) -> str:
    rng = _section_range(text, head_re)
    if not rng:
        return ""
    lines = text.splitlines()[rng[0] + 1:rng[1]]
    return md.COMMENT_RE.sub("", "\n".join(lines)).strip()


def report(p: Project, id_: str) -> str:
    """人間がコードを読む代わりに読む報告。新しく書かせず、Task・検証記録・差分・CHANGELOG から組み立てる。"""
    doc = find_task(p, id_, include_done=True)
    if not doc:
        raise SystemExit(f"error: Task {id_} が見つかりません")
    text = doc.text
    st = str(doc.fm.get("status"))
    out = [f"# {id_} {title_of(doc)}（{st}{'・' + str(doc.fm.get('closed')) if doc.fm.get('closed') else ''}）", ""]
    out += ["## 目的の状態", "", _section_text(text, re.compile("目的の状態")) or "（未記入）", ""]
    refs = md.fm_list(doc.fm, "refs")
    if refs:
        out += ["## 満たす仕様", ""]
        for r in refs:
            key = p.resolve(p._target(doc.path, r))
            sec = p.sections.get(key) if key else None
            if not sec:
                out.append(f"- {r}（見つかりません）")
                continue
            body = next((x.strip() for x in sec.text.splitlines()[1:] if x.strip()), "")
            name = sec.title if sec.title.startswith(r) else f"{r}: {sec.title}"
            out.append(f"- {name}" + (f" — {body[:80]}" if body else ""))
        out.append("")
    lt = latest(parse_evidence(text))
    base_res = {m.group(2): m.group(3) for m in (BASE_LINE_RE.match(x) for x in text.splitlines()) if m}
    out += ["## 検証（何を・どう確かめたか）", ""]
    for ac in parse_acs(text):
        e = lt.get(ac.label)
        res = f"{e.result}（{e.when}）" if e else "未検証"
        b = base_res.get(ac.label)
        extra = {"FAIL": "／着手時点では落ちる＝変更を確かめている", "PASS": "／⚠️ 着手時点でも通る"}.get(b, "")
        out.append(f"- {ac.label}: {ac.text}")
        out.append(f"  - 方法: {ac.verify or '未記載'}")
        out.append(f"  - 結果: {res}{extra}")
    out.append("")
    decision = _section_text(text, DECISION_HEAD_RE)
    if decision:
        out += ["## 判断（なぜこの方法か）", "", decision, ""]
    if doc.kind == "task":
        changed = changed_paths(p.root, str(doc.fm.get("base") or "") or None)
        if changed:
            out += [f"## 変更したファイル（着手時点 {doc.fm.get('base')} からの差分）", ""]
            out += [f"- {c}" for c in changed if not c.startswith("docs/tasks/")]
            out.append("")
    cl = p.docs.get("CHANGELOG.md")
    logged = [x.strip() for x in (cl.text.splitlines() if cl else []) if id_ in x and x.strip().startswith("-")]
    out += ["## CHANGELOG", ""] + (logged or ["（記録なし）"])
    return "\n".join(out).rstrip() + "\n"


def record(p: Project, id_: str, label: str, result: str, note: str) -> str:
    doc = find_task(p, id_)
    if not doc:
        raise SystemExit(f"error: アクティブな Task {id_} が見つかりません")
    acs = {a.label: a for a in parse_acs(doc.text)}
    if label not in acs:
        raise SystemExit(f"error: {id_} に {label} がありません（{', '.join(acs) or 'AC なし'}）")
    res = result.upper()
    if res not in ("PASS", "FAIL"):
        raise SystemExit("error: 結果は pass / fail")
    text = _set_check(doc.text, acs[label], res == "PASS")
    lines = evidence_lines(now(), label, res, f"手動: {note}", fingerprint(p.root) or "none")
    _write(p, doc.path, _append_evidence(text, lines))
    return "\n".join(lines)


def gate(p: Project, doc) -> list[str]:
    """完了ゲート。満たしていない条件の一覧を返す（空なら完了可）。"""
    from .check import run as run_check
    fails = []
    id_ = str(doc.fm.get("id"))
    acs = parse_acs(doc.text)
    if not acs:
        fails.append("受け入れ条件がありません")
    lt = latest(parse_evidence(doc.text))
    fp = fingerprint(p.root)
    for ac in acs:
        e = lt.get(ac.label)
        if not e:
            hint = f"task record {id_} {ac.label} pass --note ..." if ac.manual else f"task verify {id_}"
            fails.append(f"{ac.label}: 検証記録がありません（{hint}）")
        elif e.result != "PASS":
            fails.append(f"{ac.label}: 最新の検証結果が {e.result} です")
        elif e.stale(fp):
            fails.append(f"{ac.label}: 検証後にコードが変更されています（tree {e.tree} → {fp}）。再検証が必要")
    for d in p.docs.values():
        if d.kind not in ("goal", "doc"):
            continue
        for ln, line in md.prose_lines(d.text):
            for m in MARKER_RE.finditer(line):
                if m.group(1) == "計画" and m.group(2) == id_:
                    fails.append(f"{d.path}:{ln + 1} に（計画: {id_}）が残っています。実装済みの状態として記述を確定しマーカーを外す")
    relevant = relevant_docs(p, doc)
    for issue in run_check(p):
        if issue.level == "error" and issue.code != "stale-marker" and issue.path in relevant:
            fails.append(f"check: {issue}")
    return fails


def changed_paths(root: Path, base: str | None) -> list[str]:
    """base から作業ツリーまでに差分のあるパス（未追跡を含む。テスト・ビルドの副産物は除く）。"""
    if not base:
        return []
    out = []
    for args in (["diff", "--name-only", base, "--"], ["ls-files", "-o", "--exclude-standard"]):
        try:
            r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.TimeoutExpired):
            return []
        if r.returncode == 0:
            out += [x for x in r.stdout.splitlines() if x]
    return sorted({x for x in out if not is_artifact(x) and not x.startswith(".tri-ssd/")})


def relevant_docs(p: Project, doc) -> set[str]:
    """完了ゲートが検査エラーを見る範囲: Task 自身・Task が参照する文書・この Task の間に変更した文書。

    無関係な文書の誤りで正当な完了を止めない（止めると強制完了が常態化し、ゲートが信用されなくなる）。
    """
    out = {doc.path}
    for e in p.edges:
        if e.src.split("#")[0] == doc.path and e.kind != "contains":
            dst = p.resolve(e.dst)
            if dst and not dst.startswith("code:"):
                out.add(dst.split("#")[0])
    out |= {x for x in changed_paths(p.root, str(doc.fm.get("base") or "") or None)
            if x.startswith("docs/") or x == "CHANGELOG.md"}
    return out


def close(p: Project, id_: str, force_reason: str | None = None, drop: bool = False) -> tuple[list[str], str | None]:
    doc = find_task(p, id_)
    if not doc:
        raise SystemExit(f"error: アクティブな Task {id_} が見つかりません")
    fails = [] if drop else gate(p, doc)
    if fails and not force_reason:
        return fails, None
    text = doc.text
    if drop or force_reason:
        what = "DROPPED" if drop else "FORCED-CLOSE"
        text = _append_evidence(text, [f"- {now()} {what}: {force_reason or ''}".rstrip()])
    text = md.set_fm_value(text, "status", "dropped" if drop else "done")
    text = md.set_fm_value(text, "closed", today())
    dest = f"{DONE}/{Path(doc.path).name}"
    (p.root / DONE).mkdir(parents=True, exist_ok=True)
    if (p.root / dest).exists():
        raise SystemExit(f"error: {dest} が既に存在します")
    _write(p, doc.path, text)
    shutil.move(str(p.root / doc.path), str(p.root / dest))
    return fails, dest
