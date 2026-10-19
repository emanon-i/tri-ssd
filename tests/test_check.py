"""参照切れ・ID 重複・履歴汚染・重複記述・肥大化・状態マーカー・CHANGELOG 整合性の検出。"""
import unittest

from helpers import ProjectCase, git
from trissd import check


def codes(issues, path=None):
    return [(i.code, i.level) for i in issues if path is None or i.path == path]


class CheckTest(ProjectCase):
    def run_check(self, changed=None):
        return check.run(self.project(), changed)

    def test_fixture_is_clean(self):
        self.assertEqual(self.run_check(), [])

    def test_broken_references(self):
        self.write("docs/x.md", "# X\n\nREQ-0404 を満たす。[詳細](search.md#存在しない) と [無い](none.md)\n"
                   "例示の `REQ-0405` は参照ではない。\n")
        issues = self.run_check()
        msgs = [i.msg for i in issues if i.path == "docs/x.md"]
        self.assertTrue(any("REQ-0404" in m for m in msgs))
        self.assertTrue(any("#存在しない" in m for m in msgs))
        self.assertTrue(any("none.md" in m for m in msgs))
        self.assertFalse(any("REQ-0405" in m for m in msgs))
        self.assertTrue(all(i.level == "error" for i in issues if i.path == "docs/x.md"))

    def test_broken_anchor_suggests_slug(self):
        self.write("docs/y.md", "# Y\n\n## Tag Search\n\n本文。\n")
        self.write("docs/x.md", "# X\n\n[タグ](y.md#Tag-Search)\n")
        msgs = [i.msg for i in self.run_check() if i.path == "docs/x.md"]
        self.assertTrue(any("#tag-search のこと?" in m for m in msgs), msgs)

    def test_evidence_is_history(self):
        self.edit("tasks/T-0005-tag-search.md", "## 検証記録\n", "## 検証記録\n\n- 2026-10-01 10:00 AC2 PASS 手動: 別プロジェクトの T-0999 と同じ手順 tree=none\n")
        self.assertEqual(self.run_check(), [])
        self.edit("tasks/T-0005-tag-search.md", "## 目的の状態\n", "## 目的の状態\n\nT-0999 に依存する。\n")
        self.assertIn(("broken-id", "error"), codes(self.run_check()))

    def test_frontmatter_code_and_stale_path(self):
        self.write("docs/x.md", "---\ncode: [src/nothing/]\n---\n# X\n\n実装は `src/api/gone.py`。\n")
        got = codes(self.run_check(), "docs/x.md")
        self.assertIn(("broken-code", "warn"), got)
        self.assertIn(("stale-path", "warn"), got)

    def test_duplicate_id(self):
        self.write("docs/x.md", "# X\n\n## REQ-0004 重複\n")
        self.assertIn(("dup-id", "error"), codes(self.run_check()))

    def test_history_pollution(self):
        self.write("docs/x.md", "# X\n\n## 同期\n\n当初は WebSocket だったが、ポーリングに変更した。\n"
                   "The cache was replaced by FTS5.\n- 2026-10-01 方式を変えた\n~~旧方式~~ 新方式\n\n## 変更履歴\n\n"
                   "以前は A だった <!-- tri:ok -->\n`以前は` は引用。\n")
        hist = [i for i in self.run_check() if i.code == "history" and i.path == "docs/x.md"]
        lines = sorted(i.line for i in hist)
        self.assertEqual(lines, [5, 6, 7, 8, 10])  # 1行1件
        self.assertTrue(all(i.level == "warn" for i in hist))

    def test_history_allowed_places(self):
        self.write("NOTES.md", "# NOTES\n\n以前は A だった\n")
        self.write("docs/choice.md", "# 選択\n\n検索は B で行う。\n\n## 選定理由と却下案\n\nA は以前は速かったが件数で遅くなった。\n")
        self.write("docs/adr/0002-x.md", "# ADR\n\n当初は A を採用していた。\n")
        self.write("docs/history.md", "---\nkind: history\n---\n# 経緯\n\n当初は A。\n")
        self.assertEqual([i for i in self.run_check() if i.code == "history"], [])

    def test_duplicate_paragraphs(self):
        para = "取得したタイトル・本文抜粋は HTML エスケープしてから表示する。インポートする HTML は信頼しない。"
        self.write("docs/x.md", f"# X\n\n{para}\n")
        self.write("docs/y.md", f"# Y\n\n{para.replace('。', '．', 1)}\n")
        dup = [i for i in self.run_check() if i.code == "duplicate"]
        self.assertEqual(len(dup), 1)
        self.assertIn("docs/x.md", dup[0].msg)

    def test_size(self):
        self.write("docs/big.md", "# Big\n\n" + ("長い説明の文章です。" * 50 + "\n\n") * 10)
        self.assertIn(("size", "warn"), codes(self.run_check(), "docs/big.md"))

    def test_stale_plan_marker(self):
        self.edit("docs/search.md", "（計画: T-0005）", "（計画: T-0001）")
        self.assertIn(("stale-marker", "error"), codes(self.run_check(), "docs/search.md"))
        self.edit("docs/search.md", "（計画: T-0001）", "（計画）")
        self.assertIn(("marker", "warn"), codes(self.run_check(), "docs/search.md"))

    def test_task_format(self):
        self.write("tasks/T-0009-bad.md", "---\nid: T-0009\nstatus: doing\n---\n# T-0009 x\n")
        got = codes(self.run_check(), "tasks/T-0009-bad.md")
        self.assertIn(("task", "error"), got)
        self.write("tasks/T-0009-bad.md", "---\nid: T-0009\nstatus: open\n---\n# T-0009 x\n")
        self.assertIn(("task", "warn"), codes(self.run_check(), "tasks/T-0009-bad.md"))

    def test_changed_changelog_reminder_and_growth(self):
        self.edit("docs/sync.md", "5 秒ごと", "3 秒ごと")
        issues = self.run_check("HEAD")
        self.assertIn(("changelog", "warn"), codes(issues, "CHANGELOG.md"))
        self.edit("CHANGELOG.md", "## [Unreleased]\n", "## [Unreleased]\n\n### Changed\n\n- ポーリング間隔を 3 秒に\n")
        self.assertNotIn(("changelog", "warn"), codes(self.run_check("HEAD")))
        self.write("docs/sync.md", self.read("docs/sync.md") + "".join(f"\n- 追記 {n}" for n in range(25)))
        self.assertIn(("growth", "warn"), codes(self.run_check("HEAD"), "docs/sync.md"))
        self.write("docs/new.md", "# New\n" + "".join(f"\n- 項目 {n}" for n in range(30)))
        self.assertNotIn(("growth", "warn"), codes(self.run_check("HEAD"), "docs/new.md"))

    def test_changed_changelog_append_only(self):
        self.edit("CHANGELOG.md", "- 全文検索（T-0003）", "- 全文検索")
        self.assertIn(("changelog", "warn"), codes(self.run_check("HEAD"), "CHANGELOG.md"))
        git(self.root, "checkout", "--", "CHANGELOG.md")
        # リリース時の Unreleased → バージョン見出しへの移動は書き換えではない
        self.edit("CHANGELOG.md", "## [Unreleased]\n", "## [Unreleased]\n\n### Added\n\n- タグ検索（T-0005）\n")
        git(self.root, "commit", "-qam", "unreleased")
        self.edit("CHANGELOG.md", "## [Unreleased]\n\n### Added\n\n- タグ検索（T-0005）\n",
                  "## [Unreleased]\n\n## [0.4.0] - 2026-10-20\n\n### Added\n\n- タグ検索（T-0005）\n")
        self.assertNotIn(("changelog", "warn"), codes(self.run_check("HEAD"), "CHANGELOG.md"))

    def test_changed_unreleased_entries_may_be_corrected(self):
        self.edit("CHANGELOG.md", "## [Unreleased]\n", "## [Unreleased]\n\n### Added\n\n- ゴミ箱（30 日）\n")
        git(self.root, "commit", "-qam", "unreleased")
        self.edit("CHANGELOG.md", "- ゴミ箱（30 日）", "- ゴミ箱（14 日）")
        self.assertNotIn(("changelog", "warn"), codes(self.run_check("HEAD"), "CHANGELOG.md"))

    def test_cli_exit_codes(self):
        code, _ = self.tri("check")
        self.assertEqual(code, 0)
        self.write("docs/x.md", "# X\n\n以前は A だった。\n")
        self.assertEqual(self.tri("check")[0], 0)
        self.assertEqual(self.tri("check", "--strict")[0], 1)
        self.write("docs/x.md", "# X\n\nREQ-0404\n")
        self.assertEqual(self.tri("check")[0], 1)


if __name__ == "__main__":
    unittest.main()
