"""文書分類・索引生成・関連文書の取得・除外・依存変化への追従・追加/削除/移動・逆引き。"""
import unittest

from helpers import ProjectCase, git
from trissd import resolve


class ClassifyAndIndexTest(ProjectCase):
    def test_kinds(self):
        p = self.project()
        kinds = {path: d.kind for path, d in p.docs.items()}
        self.assertEqual(kinds["docs/goal.md"], "goal")
        self.assertEqual(kinds["docs/search.md"], "doc")
        self.assertEqual(kinds["tasks/T-0005-tag-search.md"], "task")
        self.assertEqual(kinds["tasks/archive/T-0001-register.md"], "task_done")
        self.assertEqual(kinds["NOTES.md"], "note")
        self.assertEqual(kinds["CHANGELOG.md"], "changelog")
        self.assertTrue(p.docs["docs/adr/0001-sqlite-fts.md"].history_allowed)
        self.assertFalse(p.docs["docs/search.md"].history_allowed)


    def test_definitions(self):
        p = self.project()
        self.assertEqual(p.defs["REQ-0004"], ["docs/requirements.md#req-0004-タグ検索"])
        self.assertEqual(p.defs["T-0005"], ["tasks/T-0005-tag-search.md"])
        self.assertIn("T-0001", p.defs)  # アーカイブ済みも定義として有効
        self.assertNotIn("T-0006", [i for i in p.defs if p.defs[i][0] == "NOTES.md"])

    def test_legacy_req_definition(self):
        self.write("docs/legacy.md", "# L\n\n### 古い要求\n\n- **ID**: REQ-0099\n- 背景\n")
        p = self.project()
        self.assertEqual(p.defs["REQ-0099"], ["docs/legacy.md#古い要求"])

    def test_edges(self):
        p = self.project()
        kinds = {(e.src, e.kind, e.dst) for e in p.edges}
        self.assertIn(("docs/api.md#http-api", "link", "docs/security.md#認証"), kinds)
        self.assertIn(("docs/sync.md#競合解決", "code", "code:src/sync/merge.py"), kinds)
        self.assertIn(("docs/search.md", "depends", "id:REQ-0003"), kinds)
        self.assertIn(("docs/data.md", "code", "code:src/storage/"), kinds)


class ContextTest(ProjectCase):
    def keys(self, r):
        return {i.key for i in r.selected}

    def files(self, r):
        return {i.key.split("#")[0] for i in r.selected}

    def test_relevant_selected_and_irrelevant_excluded(self):
        r = resolve.context(self.project(), ["T-0005"])
        k = self.keys(r)
        for need in ("docs/requirements.md#req-0004-タグ検索", "docs/search.md#タグ検索", "docs/api.md#get-search",
                     "docs/goal.md#原則", "NOTES.md#notes"):
            self.assertIn(need, k)
        for noise in ("docs/sync.md", "docs/ui.md", "docs/security.md", "docs/operations.md", "docs/glossary.md"):
            self.assertNotIn(noise, self.files(r))
        self.assertNotIn("docs/requirements.md#req-0010-アカウントと認証", k)  # 兄弟の要求は読まない
        self.assertFalse(any(x.startswith("tasks/archive") for x in self.files(r)))  # 履歴は読まない
        self.assertLess(r.used, r.full_tokens)

    def test_reasons_and_must(self):
        r = resolve.context(self.project(), ["T-0005"])
        by = {i.key: i for i in r.selected}
        self.assertTrue(by["docs/search.md#タグ検索"].must)
        self.assertIn("T-0005", by["docs/search.md#タグ検索"].reason)
        self.assertIn("REQ-0004", by["docs/api.md#get-search"].reason)

    def test_budget_never_drops_silently(self):
        r = resolve.context(self.project(), ["T-0005"], budget=300)
        self.assertTrue(r.omitted_must)
        self.assertTrue(any("必須" in w for w in r.warnings))
        self.assertLessEqual(r.used, 300)
        code, out = self.tri("context", "T-0005", "--budget", "300")
        self.assertEqual(code, 3)
        self.assertIn("予算外で省略", out)

    def test_follows_dependency_change(self):
        r = resolve.context(self.project(), ["T-0007"])
        self.assertNotIn("docs/data.md#整合性", self.keys(r))
        self.edit("tasks/T-0007-trash-purge.md", "refs: [REQ-0011]", "refs: [REQ-0011, docs/data.md#整合性]")
        r = resolve.context(self.project(), ["T-0007"])
        self.assertIn("docs/data.md#整合性", self.keys(r))
        self.edit("tasks/T-0007-trash-purge.md", ", docs/data.md#整合性", "")
        r = resolve.context(self.project(), ["T-0007"])
        self.assertNotIn("docs/data.md#整合性", self.keys(r))

    def test_added_doc_is_found(self):
        self.write("docs/autocomplete.md", "# 補完\n\n## 候補の並び\n\nREQ-0004 の補完は use_count 列で並べる。\n")
        r = resolve.context(self.project(), ["T-0005"])
        self.assertIn("docs/autocomplete.md#候補の並び", self.keys(r))

    def test_deleted_and_moved_doc(self):
        (self.root / "docs/search.md").unlink()
        r = resolve.context(self.project(), ["T-0005"])
        self.assertNotIn("docs/search.md", self.files(r))
        code, out = self.tri("check")
        self.assertEqual(code, 1)
        self.assertIn("broken-link", out)  # T-0005 の refs と data.md からのリンクが切れる
        git(self.root, "checkout", "--", "docs/search.md")
        (self.root / "docs/design").mkdir()
        (self.root / "docs/search.md").rename(self.root / "docs/design/search.md")
        code, out = self.tri("check")
        self.assertIn("docs/search.md#タグ検索", out)
        self.edit("tasks/T-0005-tag-search.md", "docs/search.md#", "docs/design/search.md#")
        self.edit("docs/data.md", "(sync.md)", "(sync.md)")
        r = resolve.context(self.project(), ["T-0005"])
        self.assertIn("docs/design/search.md#タグ検索", self.keys(r))

    def test_keyword_fallback_for_unlinked_task(self):
        self.write("tasks/T-0008-x.md", "---\nid: T-0008\nstatus: open\n---\n# T-0008 リンク切れ確認の再試行\n\n"
                   "## 受け入れ条件\n\n- AC1: 3 回連続失敗でリンク切れになる\n  - 検証: `true`\n")
        r = resolve.context(self.project(), ["T-0008"])
        self.assertTrue(any("キーワード" in w for w in r.warnings))
        self.assertIn("docs/operations.md#リンク確認", self.keys(r))
        self.assertTrue(any(i.fallback for i in r.selected))

    def test_code_seed_prefers_exact_mention(self):
        r = resolve.context(self.project(), ["src/sync/merge.py"], include_goal=False)
        top = max(r.selected, key=lambda i: i.score)
        self.assertEqual(top.key, "docs/sync.md#競合解決")
        self.assertNotIn("docs/search.md", self.files(r))

    def test_unknown_seed(self):
        code, out = self.tri("context", "T-0999")
        self.assertEqual(code, 2)
        self.assertIn("起点が見つかりません", out)

    def test_emit_outputs_section_text_only(self):
        code, out = self.tri("context", "T-0007", "--emit")
        self.assertEqual(code, 0)
        self.assertIn("30 日後に物理削除", out)
        self.assertNotIn("競合解決", out)


class CodeIdTest(ProjectCase):
    def setUp(self):
        super().setUp()
        self.write("src/worker/trash.py", "RETENTION_DAYS = 30  # REQ-0011\n")
        git(self.root, "add", "-A")

    def test_context_lists_code_that_mentions_the_id(self):
        r = resolve.context(self.project(), ["REQ-0011"])
        self.assertIn("src/worker/trash.py", dict(r.code))
        self.assertFalse(r.warnings)  # REQ を起点にした場合は参照が無くても警告しない

    def test_impact_finds_spec_via_code_id(self):
        res = resolve.impact(self.project(), ["src/worker/trash.py"])
        self.assertIn("docs/requirements.md", res["docs"])
        self.assertIn("REQ-0011", res["docs"]["docs/requirements.md"][0].reason)


class ImpactTest(ProjectCase):
    def test_broad_mentions_are_not_reported(self):
        res = resolve.impact(self.project(), ["src/sync/merge.py"])
        reasons = [h.reason for hits in res["docs"].values() for h in hits]
        self.assertFalse(any("`src/`" in r for r in reasons))  # src/ 全体への言及は具体性が低い
        self.assertTrue(any("`src/sync/`" in r for r in reasons))

    def test_code_change(self):
        res = resolve.impact(self.project(), ["src/sync/merge.py"])
        self.assertIn("docs/sync.md", res["docs"])
        self.assertEqual(res["docs"]["docs/sync.md"][0].key, "docs/sync.md#競合解決")
        self.assertNotIn("docs/ui.md", res["docs"])

    def test_task_scope_and_uncovered(self):
        res = resolve.impact(self.project(), ["src/search/query.py", "README.txt"])
        self.assertIn("docs/search.md", res["docs"])
        self.assertIn("tasks/T-0005-tag-search.md", res["tasks"])
        self.assertIn("README.txt", res["uncovered"])

    def test_git_doc_change_only_referencing_sections(self):
        self.edit("docs/requirements.md", "30 日経過後に完全に消える。", "30 日経過後に完全に消える。管理者も復元できない。")
        code, out = self.tri("impact", "--git")
        self.assertEqual(code, 0)
        self.assertIn("docs/data.md#ライフサイクル", out)
        self.assertIn("docs/operations.md#ゴミ箱の物理削除", out)
        self.assertIn("T-0007", out)
        self.assertNotIn("docs/search.md#タグ検索", out)  # 変更していない REQ-0004 の参照元は出ない


if __name__ == "__main__":
    unittest.main()
