"""Context Resolver（読むべきセクションの選定）と Impact（変更から見直すべき Docs の逆引き）。

両者は同じ知識グラフを使い、辿る向きだけが違う:
  context: 起点から「依存先」へ（Task → 仕様 → その仕様が依存する仕様）
  impact : 変更点から「依存元」へ（コード → それを記述・統治する Docs → それを参照する Docs）
"""
from __future__ import annotations

import heapq
import math
import re
from collections import defaultdict
from dataclasses import dataclass, field

from . import md
from .project import Project, code_covers, code_related  # noqa: F401

# 辺の重み（スコアは起点 1.0 からの積）と、到達経路ごとに辿ってよい辺（下の EXPAND）
W_FWD = {"ref": 0.8, "link": 0.75, "depends": 0.9}   # 参照先（依存している仕様）
W_FWD_FROM_TASK = 0.95                                # Task が明示的に参照する先
W_DOWN = 0.9                                          # 見出し → 配下の小見出し
W_UP = 0.5                                            # 子 → 親（上位の文脈。親自身の本文だけ）
W_CODE = 0.95                                         # Task・起点 → 作業範囲のコード
W_EXACT = 0.9                                         # コード → そのパスを名指しで記述するセクション
W_GOV = 0.7                                           # コード → それを包含して記述・統治する Docs
W_REAL = 0.6                                          # REQ ← それを参照する設計（要求の実現先）
W_IN = {"note": 0.8, "task": 0.4, "goal": 0.35, "doc": 0.35}  # 被参照
W_GOV_DOWN = 0.75                                     # 統治経路では配下へ速く減衰させる（広い範囲を統治する文書の全文を避ける）
W_COMPLEMENT = 0.45                                   # 語彙の一致による補完（最上位でも 0.45）
COMPLEMENT_K = 5
MIN_SCORE = 0.12                                      # 探索を打ち切るスコア
MIN_INCLUDE = 0.3                                     # 必須でない項目を選定する下限（下回るものは参考候補として列挙のみ）
HISTORY_KINDS = ("task_done", "changelog")


@dataclass
class Item:
    key: str
    score: float
    must: bool
    reason: str
    tokens: int
    fallback: bool = False


@dataclass
class Result:
    seeds: list[str]
    selected: list[Item] = field(default_factory=list)
    omitted: list[Item] = field(default_factory=list)
    code: list[tuple[str, float]] = field(default_factory=list)
    weak: list[Item] = field(default_factory=list)
    unknown: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    budget: int = 0
    full_tokens: int = 0

    @property
    def used(self) -> int:
        return sum(i.tokens for i in self.selected)

    @property
    def omitted_must(self) -> list[Item]:
        return [i for i in self.omitted if i.must]


class Graph:
    """解決済みエッジの隣接表。"""

    def __init__(self, project: Project):
        self.p = project
        self.out: dict[str, list[tuple[str, str]]] = defaultdict(list)
        self.inc: dict[str, list[tuple[str, str]]] = defaultdict(list)
        self.code_edges: list[tuple[str, str]] = []
        self.inline_code: set[tuple[str, str]] = set()  # 本文で名指ししている (セクション, パス)
        for e in project.edges:
            dst = project.resolve(e.dst)
            if dst is None:
                continue
            if dst.startswith("code:"):
                self.code_edges.append((e.src, dst[5:]))
                if e.line > 0:
                    self.inline_code.add((e.src, dst[5:]))
            self.out[e.src].append((dst, e.kind))
            self.inc[dst].append((e.src, e.kind))

    def kind(self, key: str) -> str:
        return "code" if key.startswith("code:") else self.p.doc_of(key).kind

    def label(self, key: str) -> str:
        if key.startswith("code:"):
            return key[5:]
        for id_, keys in self.p.defs.items():
            if key in keys:
                return id_
        return key


def seed_keys(p: Project, seed: str) -> list[str] | None:
    s = seed.strip()
    if md.ID_RE.fullmatch(s):
        keys = p.defs.get(s)
        return keys[:1] if keys else None
    path, _, anchor = s.partition("#")
    path = path[2:] if path.startswith("./") else path
    if path.endswith(".md"):
        if path not in p.docs and f"docs/{path}" in p.docs:
            path = f"docs/{path}"
        key = p.resolve(f"{path}#{anchor}" if anchor else path)
        return [key] if key else None
    return ["code:" + path]


def context(p: Project, seeds: list[str], budget: int = 6000, query: str | None = None,
            include_goal: bool = True, include_history: bool = False, min_include: float = MIN_INCLUDE,
            complement: bool = True) -> Result:
    g = Graph(p)
    res = Result(seeds=seeds, budget=budget)
    res.full_tokens = sum(md.estimate_tokens(d.text) for d in p.docs.values() if d.kind in ("goal", "doc"))
    best: dict[str, float] = {}
    prev: dict[str, tuple[str, str]] = {}
    modes: dict[str, str] = {}
    must: set[str] = set()
    fallback: set[str] = set()
    heap: list[tuple[float, str]] = []

    def push(key: str, score: float, frm: str | None, how: str):
        if score < MIN_SCORE or score <= best.get(key, 0):
            return
        if not include_history and not key.startswith("code:") and g.kind(key) in HISTORY_KINDS:
            return
        best[key] = score
        modes[key] = how
        if frm is not None:
            prev[key] = (frm, how)
        heapq.heappush(heap, (-score, key))

    seed_set: list[str] = []
    for s in seeds:
        keys = seed_keys(p, s)
        if not keys:
            res.unknown.append(s)
            continue
        for k in keys:
            if not k.startswith("code:") and g.kind(k) in ("task", "task_done"):
                k = k.split("#")[0]  # Task は常にファイル全体を読む
            seed_set.append(k)
            for sec in ([] if k.startswith("code:") else p.subtree(k)):
                must.add(sec.key)
                push(sec.key, 1.0, None if sec.key == k else k, "seed")
            push(k, 1.0, None, "seed")
            if k.startswith("code:"):
                modes[k] = "code"


    # 起点からの直接参照（ref / link / depends）とその配下は必須扱い
    for k in list(must):
        for dst, kind in g.out.get(k, []):
            if kind in ("ref", "link", "depends") and not dst.startswith("code:") and g.kind(dst) not in HISTORY_KINDS:
                for sec in p.subtree(dst):
                    if g.kind(sec.key) != "note":
                        must.add(sec.key)

    # 依存が辿れない起点はキーワード探索へフォールバック
    q = query
    linked = any(k.startswith("code:") for k in seed_set) or any(kind != "contains" for k in seed_set for _, kind in g.out.get(k, []) + [
        x for sec in ([] if k.startswith("code:") else p.subtree(k)) for x in g.out.get(sec.key, [])])
    task_seed = any(not k.startswith("code:") and g.kind(k) == "task" for k in seed_set)
    if q is None and seed_set and not linked and task_seed:
        q = " ".join(sec.text for k in seed_set if not k.startswith("code:") for sec in p.subtree(k))[:2000]
        res.warnings.append("起点の Task に参照（refs・ID・リンク・コードパス）が無いため、本文のキーワード探索で補完しました（要確認）")
    if q:
        for key, sc in keyword_search(p, q):
            fallback.add(key)
            push(key, 0.6 * sc, None, "fwd")
    while heap:
        negs, key = heapq.heappop(heap)
        s = -negs
        if s < best.get(key, 0):
            continue
        mode = modes.get(key, "seed")
        if key.startswith("code:"):
            # 起点・Task の作業範囲のコードだけが、それを包含する Docs へ広がる（横移動はしない）
            if mode == "code":
                for src, cp in g.code_edges:
                    if code_covers(cp, key[5:]) and g.kind(src) in ("goal", "doc"):
                        exact = cp.rstrip("/") == key[5:].rstrip("/") and (src, cp) in g.inline_code
                        push(src, s * (W_EXACT if exact else W_GOV), key, "gov")
            continue
        if mode in ("note", "leaf"):
            continue
        sec = p.sections[key]
        if mode == "up":
            if sec.parent is not None and sec.index != 0:
                push(p.doc_of(key).sections[sec.parent].key, s * W_UP, key, "up")
            continue
        for dst, kind in g.out.get(key, []):
            if kind == "contains":
                push(dst, s * (W_GOV_DOWN if mode == "gov" else W_DOWN), key, "down" if mode not in ("gov", "real") else mode)
            elif mode in ("gov", "real"):
                continue  # 統治・実現の経路で来た文書は、その文書の中身だけを読む
            elif kind == "code":
                if mode == "seed" or g.kind(key) == "task":
                    push(dst, s * W_CODE, key, "code")
            else:
                w = W_FWD_FROM_TASK if g.kind(key) == "task" else W_FWD[kind]
                push(dst, s * w, key, "fwd")
        if mode in ("gov", "real"):
            continue
        defines_req = any(i.startswith("REQ-") and key in keys for i, keys in p.defs.items())
        for src, kind in g.inc.get(key, []):
            if kind == "contains":
                continue
            sk = g.kind(src)
            if sk == "doc" or sk == "goal":
                w, how = (W_REAL, "real") if defines_req else (W_IN[sk], "leaf")
            elif sk == "note":
                w, how = W_IN["note"], "note"
            elif sk == "task":
                w, how = W_IN["task"], "leaf"
            else:
                continue
            push(src, s * w, key, how)
        if sec.parent is not None and sec.index != 0:
            push(p.doc_of(key).sections[sec.parent].key, s * W_UP, key, "up")

    # 依存が書かれていない関係（エンティティ定義・横断的な制約）を語彙の一致で探す。
    # 既に関連と判定した Docs と同じ文書内の見出しは選定し、それ以外は「関連の弱い候補」として列挙だけする
    lexical: set[str] = set()
    if complement and seed_set and not q:
        ctext = " ".join(sec.text for k in seed_set if not k.startswith("code:") for sec in p.subtree(k))
        relevant_files = {k.split("#")[0] for k, sc in best.items()
                          if not k.startswith("code:") and sc >= W_DOWN * W_REAL and g.kind(k) == "doc"}
        hits = [(k, sc) for k, sc in keyword_search(p, ctext[:4000], k=40) if k not in best and sc >= 0.3]
        weak_n = 0
        for key, sc in hits:
            fallback.add(key)
            modes[key] = "leaf"
            if key.split("#")[0] in relevant_files and sc >= 0.4:
                best[key] = round(max(min_include, W_COMPLEMENT * sc), 3)  # 同一文書内の語彙一致
            elif weak_n < COMPLEMENT_K:
                weak_n += 1
                lexical.add(key)
                best[key] = round(W_COMPLEMENT * sc, 3)
            else:
                fallback.discard(key)

    # Goal は常に読む上位制約（必須）。Goal から先へは広げない（Goal 内の REQ を起点が参照した場合だけ上で展開済み）
    if include_goal and "docs/goal.md" in p.docs:
        for sec in p.docs["docs/goal.md"].sections:
            must.add(sec.key)
            if sec.key not in best:
                best[sec.key] = 0.99
                modes[sec.key] = "goal"

    items = []
    for key, score in best.items():
        if key.startswith("code:"):
            res.code.append((key[5:], round(score, 3)))
            continue
        sec = p.sections[key]
        if not sec.text.strip():
            continue
        reason = ("語彙の一致" if key in lexical else "同じ文書内の語彙の一致") if key in fallback and key not in prev \
            else _reason(g, prev, key)
        items.append(Item(key, round(score, 3), key in must, reason, md.estimate_tokens(sec.text), key in fallback))
    # 選定セクションが言及するコードも「関連コード」として示す（グラフはそこから広げない）
    for it in items:
        if it.score < min_include and not it.must:
            continue
        for dst, kind in g.out.get(it.key, []) + [x for x in g.out.get(it.key.split("#")[0], []) if x[1] == "code"]:
            if kind == "code" and best.get(dst, 0) < it.score * 0.8:
                best[dst] = it.score * 0.8
                res.code = [c for c in res.code if c[0] != dst[5:]] + [(dst[5:], round(it.score * 0.8, 3))]
    code_ids = p.code_ids()
    for it in items:
        if it.score < min_include and not it.must:
            continue
        for id_, keys in p.defs.items():
            if it.key in keys:
                for path in code_ids.get(id_, []):
                    sc = round(it.score * 0.95, 3)
                    res.code = [c for c in res.code if c[0] != path] + [(path, max(sc, dict(res.code).get(path, 0)))]
    order = {k: i for i, k in enumerate(p.sections)}
    items.sort(key=lambda i: (not i.must, -i.score, order[i.key]))
    used = 0
    for it in items:
        if not it.must and (it.score < min_include or it.key in lexical):
            res.weak.append(it)
        elif budget <= 0 or used + it.tokens <= budget:
            res.selected.append(it)
            used += it.tokens
        else:
            res.omitted.append(it)
    res.code.sort(key=lambda c: -c[1])
    if res.omitted_must:
        res.warnings.append(f"予算 {budget} トークンを超えるため必須セクション {len(res.omitted_must)} 件を省略しました"
                            "（omitted を確認し、必要なら --budget を増やすか個別に読むこと）")
    return res


def _reason(g: Graph, prev: dict[str, tuple[str, str]], key: str) -> str:
    chain = []
    cur = key
    for _ in range(3):
        if cur not in prev:
            break
        frm, how = prev[cur]
        chain.append(f"{g.label(frm)} -{how}-> ")
        cur = frm
    if not chain:
        return "seed"
    return ("… " if cur in prev else "") + "".join(reversed(chain)) + g.label(key)


# --- キーワード探索（フォールバック） ----------------------------------------------------

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]+|[぀-ヿ㐀-鿿ｦ-ﾟ]+")


def terms(text: str) -> list[str]:
    out = []
    for t in TOKEN_RE.findall(text):
        if t.isascii():
            if len(t) >= 3:
                out.append(t.lower())
        else:
            out += [t[i:i + 2] for i in range(max(1, len(t) - 1))]
    return out


def keyword_search(p: Project, query: str, k: int = 6) -> list[tuple[str, float]]:
    """BM25 による Goal/Docs セクションの全文探索。上位 k 件を (キー, 0-1正規化スコア) で返す。"""
    docs = [(s.key, terms(s.text)) for d in p.docs.values() if d.kind in ("goal", "doc")
            for s in d.sections if s.text.strip()]
    if not docs:
        return []
    n = len(docs)
    avg = sum(len(t) for _, t in docs) / n or 1
    df: dict[str, int] = defaultdict(int)
    for _, ts in docs:
        for t in set(ts):
            df[t] += 1
    qs = set(terms(query))
    scored = []
    for key, ts in docs:
        tf: dict[str, int] = defaultdict(int)
        for t in ts:
            tf[t] += 1
        sc = 0.0
        for t in qs:
            if t in tf:
                idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
                sc += idf * tf[t] * 2.2 / (tf[t] + 1.2 * (0.25 + 0.75 * len(ts) / avg))
        if sc > 0:
            scored.append((key, sc))
    scored.sort(key=lambda x: -x[1])
    top = scored[:k]
    mx = top[0][1] if top else 1
    return [(key, sc / mx) for key, sc in top]


# --- Impact（逆引き） -----------------------------------------------------------------

@dataclass
class Hit:
    key: str
    score: float
    reason: str


def impact(p: Project, paths: list[str], doc_lines: dict[str, set[int]] | None = None,
           hops: int = 2) -> dict:
    """変更されたパスから、見直すべき Docs セクションと影響する進行中 Task を返す。"""
    g = Graph(p)
    hits: dict[str, Hit] = {}
    tasks: dict[str, str] = {}
    uncovered: list[str] = []
    frontier: list[tuple[str, float, str]] = []

    def add(key: str, score: float, reason: str):
        kind = g.kind(key)
        if kind in HISTORY_KINDS or kind == "note" or (kind == "doc" and p.doc_of(key).history_allowed):
            return  # 履歴（ADR 等）は書き換えないので見直し対象にしない
        if kind == "task":
            tasks.setdefault(key.split("#")[0], reason)
            return
        if key not in hits or hits[key].score < score:
            hits[key] = Hit(key, round(score, 3), reason)
            frontier.append((key, score, reason))

    from .tasks import is_artifact
    for raw in paths:
        path = raw[2:] if raw.startswith("./") else raw
        if is_artifact(path):
            continue
        if path in p.docs:
            changed = (doc_lines or {}).get(path)
            secs = [s for s in p.docs[path].sections
                    if changed is None or any(s.start <= ln < s.end for ln in changed)]
            for s in secs:
                for src, kind in g.inc.get(s.key, []):
                    if kind != "contains":
                        add(src, 0.9, f"{g.label(s.key)} を参照（{path} を変更）")
            continue
        found = False
        for src, cp in g.code_edges:
            if code_covers(cp, path):
                exact = cp.rstrip("/") == path.rstrip("/")
                # 具体性: 広い範囲（`src/` 等）の言及ほど弱い（パスの深さの比）
                depth = len(cp.strip("/").split("/")) / max(len(path.strip("/").split("/")), 1)
                sc = 1.0 if exact else round(0.85 * min(1.0, depth), 3)
                if sc >= MIN_INCLUDE:
                    add(src, sc, f"`{cp}` を記述（{path} を変更）")
                    found = True
        for id_ in sorted(i for i, paths in p.code_ids().items() if path in paths):
            for key in p.defs.get(id_, [])[:1]:
                add(key, 0.95, f"コードが {id_} を参照（{path} を変更）")
                found = True
        if not found:
            uncovered.append(path)

    for _ in range(hops - 1):
        cur, frontier[:] = list(frontier), []
        for key, score, _r in cur:
            for src, kind in g.inc.get(key, []):
                if kind in ("ref", "link", "depends"):
                    add(src, score * 0.6, f"{g.label(key)} を参照（間接）")

    by_doc: dict[str, list[Hit]] = defaultdict(list)
    for h in sorted(hits.values(), key=lambda h: -h.score):
        by_doc[h.key.split("#")[0]].append(h)
    return {"docs": dict(by_doc), "tasks": tasks, "uncovered": uncovered}
