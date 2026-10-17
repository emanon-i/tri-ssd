"""Note のライフサイクル・CHANGELOG 追記・フック・初期化・旧 Tri-SSD からの移行。"""
import json
import unittest

from helpers import ProjectCase, git


class HandoffTest(ProjectCase):
    """引き継ぎは上書きの1つだけ（溜まる場所を作らない）。個人用は git 管理外。"""

    def test_handoff_overwrites(self):
        self.tri("handoff", "1回目の引き継ぎ")
        self.tri("handoff", "-", stdin="2回目: T-0006 から再開\n")
        text = self.read("docs/notes/handoff.md")
        self.assertNotIn("1回目", text)
        self.assertIn("2回目", text)
        self.assertIn("2回目", self.tri("status")[1])

    def test_local_handoff_stays_out_of_git(self):
        self.tri("handoff", "社内 VPN 経由だと fetch が遅い", "--local")
        self.assertTrue((self.root / ".tri-ssd/handoff.md").exists())
        self.assertEqual((self.root / ".tri-ssd/.gitignore").read_text(), "*\n")
        self.assertNotIn(".tri-ssd", git(self.root, "status", "--porcelain"))
        self.assertIn("社内 VPN", self.tri("status")[1])


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
        self.assertIn("引き継ぎ", out)
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
        for rel in ("docs/goal.md", "docs/tasks/.gitkeep", "docs/notes/.gitkeep", "CHANGELOG.md", ".tri-ssd/.gitignore"):
            self.assertTrue((self.root / rel).exists(), rel)
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
        self.assertTrue((r / "docs/notes/ideas/brainstorm.md").exists())
        self.assertIn("status: done", self.read("docs/tasks/_done/PH-0001_mvp.md"))
        self.assertIn("status: active", self.read("docs/tasks/PH-0002_search.md"))
        merged = self.read("docs/tasks/PH-0003_sync.md")
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


if __name__ == "__main__":
    unittest.main()
