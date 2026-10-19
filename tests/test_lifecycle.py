"""NOTES.md のライフサイクル・CHANGELOG 追記・フック・初期化・旧い配置からの移行。"""
import json
import unittest

from helpers import ProjectCase, git


class NotesTest(ProjectCase):
    """NOTES.md は上書きの1つだけ（溜まる場所を作らない）。"""

    def test_notes_overwrites(self):
        self.tri("notes", "1回目の現在位置")
        self.tri("notes", "-", stdin="2回目: T-0006 から再開\n")
        text = self.read("NOTES.md")
        self.assertNotIn("1回目", text)
        self.assertIn("2回目", text)
        self.assertIn("2回目", self.tri("status")[1])


class ChangelogTest(ProjectCase):
    def test_log_inserts_under_unreleased_in_order(self):
        self.tri("log", "Fixed", "補完の並び順を修正", "--refs", "T-0005")
        self.tri("log", "Added", "タグ検索", "--refs", "T-0005")
        self.tri("log", "added", "インポート")
        text = self.read("CHANGELOG.md")
        unreleased = text.split("## [0.3.0]")[0]
        self.assertLess(unreleased.index("### Added"), unreleased.index("### Fixed"))
        self.assertIn("- タグ検索（T-0005）\n- インポート\n", unreleased)
        self.assertIn("- 全文検索（T-0003）", text.split("## [0.3.0]")[1])
        self.assertEqual(self.tri("log", "Bogus", "x")[0], 2)

    def test_log_creates_changelog(self):
        (self.root / "CHANGELOG.md").unlink()
        self.tri("log", "Changed", "x")
        self.assertIn("## [Unreleased]\n\n### Changed\n\n- x\n", self.read("CHANGELOG.md"))


class HookTest(ProjectCase):
    def test_status_hook_silent_outside_project(self):
        (self.root / "docs").rename(self.root / "other")
        code, out = self.tri("status", "--hook", stdin=json.dumps({"cwd": str(self.root)}))
        self.assertEqual((code, out), (0, ""))

    def test_status_hook_in_project(self):
        code, out = self.tri("status", "--hook", stdin=json.dumps({"cwd": str(self.root)}))
        self.assertIn("T-0005 [active]", out)
        self.assertIn("NOTES.md:", out)
        self.assertLess(len(out), 10000)

    def test_check_hook_reports_only_edited_doc(self):
        self.write("docs/sync.md", self.read("docs/sync.md") + "\n当初は WebSocket を使っていた。\n")
        payload = {"cwd": str(self.root), "tool_input": {"file_path": str(self.root / "docs/sync.md")}}
        code, out = self.tri("check", "--hook", stdin=json.dumps(payload))
        self.assertEqual(code, 0)
        ctx = json.loads(out)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("当初は", ctx)
        payload["tool_input"]["file_path"] = str(self.root / "docs/ui.md")
        self.assertEqual(self.tri("check", "--hook", stdin=json.dumps(payload)), (0, ""))
        payload["tool_input"]["file_path"] = str(self.root / "src/sync/merge.py")
        self.assertEqual(self.tri("check", "--hook", stdin=json.dumps(payload)), (0, ""))


class InitTest(ProjectCase):
    fixture = None

    def test_init_idempotent(self):
        code, out = self.tri("init", "--name", "Demo")
        self.assertEqual(code, 0)
        self.assertEqual(sorted(p.relative_to(self.root).as_posix() for p in self.root.rglob("*")
                                if p.is_file() and ".git" not in p.parts), ["CHANGELOG.md", "docs/goal.md"])
        self.assertIn("# Demo Goal", self.read("docs/goal.md"))
        self.write("docs/goal.md", "# Mine\n")
        self.assertIn("既に初期化済み", self.tri("init")[1])
        self.assertEqual(self.read("docs/goal.md"), "# Mine\n")
        self.assertEqual(self.tri("check")[0], 0)


class MigrateTest(ProjectCase):
    fixture = "v5project"

    def test_dry_run_changes_nothing(self):
        before = git(self.root, "status", "--porcelain")
        code, out = self.tri("migrate")
        self.assertIn("ドライラン", out)
        self.assertIn("docs/l1_requirements/vision.md → docs/goal.md", out)
        self.assertEqual(git(self.root, "status", "--porcelain"), before)

    def test_apply(self):
        code, out = self.tri("migrate", "--apply")
        self.assertEqual(code, 0, out)
        r = self.root
        for gone in ("docs/l1_requirements", "docs/l2_foundation", "docs/l3_phases", "docs/l0_ideas", "docs/README.md"):
            self.assertFalse((r / gone).exists(), gone)
        goal = self.read("docs/goal.md")
        self.assertIn("[構成](design/foundation.md)", goal)
        self.assertIn("（未確定）", goal)
        self.assertIn("（未検証）", self.read("docs/design/foundation.md"))
        self.assertTrue((r / "docs/design/features/sync.md").exists())
        self.assertTrue((r / "tmp/notes/ideas/brainstorm.md").exists())
        self.assertFalse((r / "docs/tasks").exists() or (r / "docs/notes").exists())
        self.assertIn("status: done", self.read("tasks/archive/PH-0001_mvp.md"))
        self.assertIn("status: active", self.read("tasks/PH-0002_search.md"))
        merged = self.read("tasks/PH-0003_sync.md")
        self.assertIn("status: open", merged)
        self.assertIn("F-0003: Git 同期", merged)
        self.assertLess(merged.index("F-0003: Git 同期"), merged.index("## 検証記録"))  # 機能の節を検証記録に入れない
        p = self.project()
        self.assertEqual(p.defs["REQ-0002"], ["docs/goal.md#同期"])
        self.assertIn("PH-0003", p.defs)
        self.assertIn("F-0003", p.defs)
        code, out = self.tri("check")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.tri("id", "T")[1].strip(), "T-0001")
        self.assertEqual(self.tri("id", "F")[1].strip(), "F-0004")
        code, out = self.tri("context", "PH-0003")
        self.assertIn("docs/design/features/sync.md", out)  # Goal 内の REQ-0002 を実現する契約まで辿る



class LayoutMigrateTest(ProjectCase):
    """v6 の配置（docs/tasks・docs/notes・.tri-ssd）から今の配置へ。"""
    fixture = None

    def setUp(self):
        super().setUp()
        self.write("docs/goal.md", "# G\n\n## 目的\n\nx\n")
        self.write("docs/search.md", "# 検索\n\n## REQ-0001 検索\n\n作業は [T-0002](tasks/T-0002-x.md)。\n")
        self.write("docs/tasks/T-0002-x.md", "---\nid: T-0002\nstatus: open\nrefs: [REQ-0001]\n---\n# T-0002 x\n\n"
                   "仕様は [検索](../search.md)。引き継ぎは `docs/notes/handoff.md`。\n\n## 受け入れ条件\n\n- AC1: x\n  - 検証: `true`\n")
        self.write("docs/tasks/_done/T-0001-y.md", "---\nid: T-0001\nstatus: done\n---\n# T-0001 y\n\n[検索](../../search.md)\n")
        self.write("docs/tasks/.gitkeep", "")
        self.write("docs/notes/handoff.md", "# 引き継ぎ\n\n- 次: T-0002\n")
        self.write("docs/notes/ideas.md", "# ideas\n")
        self.write(".tri-ssd/.gitignore", "*\n")

    def test_apply_moves_and_relinks(self):
        code, out = self.tri("migrate", "--apply")
        self.assertEqual(code, 0, out)
        r = self.root
        for gone in ("docs/tasks", "docs/notes", ".tri-ssd"):
            self.assertFalse((r / gone).exists(), gone)
        self.assertIn("[T-0002](../tasks/T-0002-x.md)", self.read("docs/search.md"))
        task = self.read("tasks/T-0002-x.md")
        self.assertIn("[検索](../docs/search.md)", task)
        self.assertIn("`NOTES.md`", task)
        self.assertIn("[検索](../../docs/search.md)", self.read("tasks/archive/T-0001-y.md"))
        self.assertTrue(self.read("NOTES.md").startswith("# NOTES\n"))
        self.assertTrue((r / "tmp/notes/ideas.md").exists())
        self.assertIn("T-0002", self.tri("status")[1])
        self.assertEqual(self.tri("check")[0], 0)

    def test_keeps_local_notes_with_content(self):
        self.write(".tri-ssd/handoff.md", "# 個人\n")
        code, out = self.tri("migrate", "--apply")
        self.assertIn("残す: .tri-ssd/", out)
        self.assertTrue((self.root / ".tri-ssd/handoff.md").exists())


if __name__ == "__main__":
    unittest.main()
