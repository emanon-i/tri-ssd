"""Task の採番・検証証跡・完了ゲート・アーカイブ。"""
import json
import unittest

from helpers import ProjectCase, git
from trissd import tasks


def task_text(id_, cmd1="true", cmd2="手動: 画面で確認", refs="REQ-0005"):
    return (f"---\nid: {id_}\nstatus: open\nrefs: [{refs}]\ncode: [src/api/import.py]\n---\n# {id_} 取り込み\n\n"
            "## 目的の状態\n\nREQ-0005 を満たす。\n\n## 受け入れ条件\n\n"
            f"- [ ] AC1: 取り込める\n  - 検証: `{cmd1}`\n- [ ] AC2: 表示される\n  - 検証: {cmd2}\n\n## 検証記録\n")


class DiscoverTest(ProjectCase):
    """書かれていない依存の候補: Task の間に変更・参照したが context に入っていなかった Docs。"""

    def make_closable(self):
        self.tri("task", "start", "T-0007")
        self.edit("docs/tasks/T-0007-trash-purge.md", "`python3 -m unittest tests.test_trash`", "`true`")

    def test_start_records_base(self):
        self.tri("task", "start", "T-0007")
        text = self.read("docs/tasks/T-0007-trash-purge.md")
        self.assertRegex(text, r"started: \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")
        self.assertRegex(text, r"base: [0-9a-f]{12}")

    def test_changed_code_described_outside_context(self):
        self.make_closable()
        self.write("src/storage/schema.sql", "CREATE TABLE bookmarks (id INTEGER, deleted_at TEXT);\n")
        self.tri("task", "verify", "T-0007")
        code, out = self.tri("task", "close", "T-0007")
        self.assertEqual(code, 0, out)
        self.assertIn("書かれていない依存の候補", out)
        self.assertIn("docs/data.md#データ設計", out)  # schema.sql を名指しする節

    def test_reads_outside_context(self):
        self.make_closable()
        lines = self.read("docs/data.md").splitlines()
        start = next(i for i, x in enumerate(lines) if x.startswith("## 整合性")) + 1
        for payload in ({"tool_name": "Read", "tool_input": {"file_path": str(self.root / "docs/data.md"),
                                                               "offset": start, "limit": 4}},
                        {"tool_name": "Bash", "tool_input": {"command": "grep -n '^#' docs/security.md"}},
                        {"tool_name": "Read", "tool_input": {"file_path": str(self.root / "src/sync/merge.py")}}):
            payload["cwd"] = str(self.root)
            self.assertEqual(self.tri("track", "--hook", stdin=json.dumps(payload)), (0, ""))
        self.tri("task", "verify", "T-0007")
        code, out = self.tri("task", "close", "T-0007")
        self.assertEqual(code, 0, out)
        self.assertIn("docs/data.md#整合性", out)
        self.assertIn("docs/security.md  ← この Task の間に文書全体を参照", out)
        self.assertNotIn("merge.py", out)
        self.assertNotIn(".tri-ssd", git(self.root, "status", "--porcelain"))

    def test_nothing_reported_when_context_was_enough(self):
        self.make_closable()
        self.tri("task", "verify", "T-0007")
        code, out = self.tri("task", "close", "T-0007")
        self.assertEqual(code, 0, out)
        self.assertNotIn("書かれていない依存の候補", out)


class GateScopeTest(ProjectCase):
    """ゲートを検問にしない: 無関係な誤りでは止めず、手で確かめた記録はコード変更で失効させない。"""

    def setUp(self):
        super().setUp()
        self.write("docs/unrelated.md", "# U\n\nREQ-0405 を参照する。\n")  # 着手前からある無関係な誤り
        git(self.root, "add", "-A")
        git(self.root, "commit", "-qm", "pre-existing")
        self.write("docs/tasks/T-0010-x.md", task_text("T-0010"))
        self.tri("task", "start", "T-0010")
        self.tri("task", "verify", "T-0010")
        self.tri("task", "record", "T-0010", "AC2", "pass", "--note", "画面で確認")

    def test_unrelated_error_does_not_block(self):
        self.assertEqual(self.tri("check")[0], 1)
        code, out = self.tri("task", "close", "T-0010")
        self.assertEqual(code, 0, out)

    def test_error_in_referenced_or_changed_doc_blocks(self):
        self.edit("docs/requirements.md", "## REQ-0005 インポート\n", "## REQ-0005 インポート\n\nREQ-0404 に従う。\n")
        code, out = self.tri("task", "close", "T-0010")
        self.assertEqual(code, 1)
        self.assertIn("REQ-0404", out)

    def test_manual_evidence_survives_code_change(self):
        self.write("src/api/import.py", "def import_html(data):\n    return []\n")
        code, out = self.tri("task", "close", "T-0010")
        self.assertEqual(code, 1)
        self.assertIn("AC1: 検証後にコードが変更", out)
        self.assertNotIn("AC2:", out)


class AgainstBaseTest(ProjectCase):
    """意味のない検証の検出: 着手時点のコードでも通る検証は、変更を確かめていない。"""

    def setUp(self):
        super().setUp()
        self.tri("task", "start", "T-0007")
        self.edit("docs/tasks/T-0007-trash-purge.md", "- [ ] AC1: 30 日経過分だけが削除され、29 日目のものは残る\n  - 検証: `python3 -m unittest tests.test_trash`",
                  "- [ ] AC1: 30 日経過分だけが削除され、29 日目のものは残る\n  - 検証: `python3 -m unittest tests.test_trash`\n"
                  "- [ ] AC2: 定期ジョブが存在する\n  - 検証: `test -f src/worker/trash.py`")
        self.write("src/worker/trash.py", "def purge_trash(days):\n    return [d for d in days if d < 30]\n")
        self.write("tests/test_trash.py", "import unittest\nfrom src.worker.trash import purge_trash\n\n"
                   "class T(unittest.TestCase):\n    def test_boundary(self):\n"
                   "        self.assertEqual(purge_trash([29, 30, 31]), [29])\n")

    def test_real_check_fails_before_and_vacuous_check_passes(self):
        code, out = self.tri("task", "verify", "T-0007", "--against-base")
        self.assertEqual(code, 0, out)
        self.assertIn("AC1 着手時点 FAIL", out)
        self.assertIn("AC2 着手時点 PASS", out)
        self.assertNotIn("worktree", git(self.root, "status", "--porcelain"))
        rep = self.tri("task", "report", "T-0007")[1]
        self.assertIn("着手時点では落ちる＝変更を確かめている", rep)
        self.assertIn("⚠️ 着手時点でも通る", rep)
        self.assertEqual(self.tri("task", "close", "T-0007")[0], 0)  # 警告であってゲートではない


class ReportTest(ProjectCase):
    def test_report_from_existing_records(self):
        self.tri("task", "start", "T-0007")
        self.edit("docs/tasks/T-0007-trash-purge.md", "`python3 -m unittest tests.test_trash`", "`true`")
        self.edit("docs/tasks/T-0007-trash-purge.md", "## 検証記録", "## 判断\n\n日次ジョブで消す。トリガー方式は件数が少なく不要と判断。\n\n## 検証記録")
        self.write("src/worker/trash.py", "def purge_trash():\n    return 0\n")
        self.tri("task", "verify", "T-0007")
        self.tri("log", "Added", "ゴミ箱の自動削除", "--refs", "T-0007")
        out = self.tri("task", "report", "T-0007")[1]
        for part in ("## 目的の状態", "- REQ-0011 削除とゴミ箱\n", "- AC1: 30 日経過分だけ",
                     "結果: PASS", "## 判断（なぜこの方法か）", "トリガー方式は", "- src/worker/trash.py",
                     "- ゴミ箱の自動削除（T-0007）"):
            self.assertIn(part, out)
        self.tri("task", "close", "T-0007")
        done = self.tri("task", "report", "T-0007")[1]
        self.assertIn("（done・", done)
        self.assertNotIn("## 変更したファイル", done)


class TaskTest(ProjectCase):
    def test_new_numbering_is_permanent(self):
        code, out = self.tri("task", "new", "Export JSON", "--refs", "REQ-0006", "--code", "src/api/")
        self.assertEqual(code, 0)
        self.assertIn("docs/tasks/T-0008-export-json.md", out)
        text = self.read("docs/tasks/T-0008-export-json.md")
        self.assertIn("refs: [REQ-0006]", text)
        # CHANGELOG にだけ残る番号も再利用しない
        self.edit("CHANGELOG.md", "- 全文検索（T-0003）", "- 全文検索（T-0003）\n- 中止（T-0020）")
        self.assertEqual(self.tri("id", "T")[1].strip(), "T-0021")

    def test_japanese_title_slug(self):
        self.tri("task", "new", "保持期間を 14 日にする")
        self.assertTrue((self.root / "docs/tasks/T-0008.md").exists())
        self.tri("task", "new", "保持期間", "--slug", "trash retention")
        self.assertTrue((self.root / "docs/tasks/T-0009-trash-retention.md").exists())

    def test_parse_acs(self):
        acs = tasks.parse_acs(task_text("T-0010", "python3 -m unittest x", "手動: 見る"))
        self.assertEqual([a.label for a in acs], ["AC1", "AC2"])
        self.assertEqual(acs[0].commands, ["python3 -m unittest x"])
        self.assertTrue(acs[1].manual)

    def test_verify_records_evidence_and_ticks(self):
        self.write("docs/tasks/T-0010-x.md", task_text("T-0010", "echo ok"))
        code, out = self.tri("task", "verify", "T-0010")
        self.assertEqual(code, 0)
        self.assertIn("AC1 PASS", out)
        self.assertIn("手動確認が必要: AC2", out)
        text = self.read("docs/tasks/T-0010-x.md")
        self.assertIn("- [x] AC1", text)
        self.assertIn("status: active", text)
        ev = tasks.parse_evidence(text)
        self.assertEqual((ev[0].label, ev[0].result), ("AC1", "PASS"))
        self.assertIn("「ok」", ev[0].detail)
        self.assertRegex(ev[0].tree, r"^[0-9a-f]{12}$")

    def test_long_evidence_wraps(self):
        self.write("docs/tasks/T-0010-x.md", task_text("T-0010"))
        self.tri("task", "record", "T-0010", "AC2", "pass", "--note", "確認" * 150)
        text = self.read("docs/tasks/T-0010-x.md")
        self.assertTrue(all(len(line) <= 200 for line in text.splitlines()))
        ev = tasks.parse_evidence(text)
        self.assertEqual((ev[-1].label, ev[-1].result), ("AC2", "PASS"))

    def test_verify_failure_unticks(self):
        self.write("docs/tasks/T-0010-x.md", task_text("T-0010", "exit 3").replace("- [ ] AC1", "- [x] AC1"))
        code, out = self.tri("task", "verify", "T-0010")
        self.assertEqual(code, 1)
        self.assertIn("AC1 FAIL", out)
        self.assertIn("- [ ] AC1", self.read("docs/tasks/T-0010-x.md"))

    def test_gate_requires_every_ac(self):
        self.write("docs/tasks/T-0010-x.md", task_text("T-0010"))
        self.tri("task", "verify", "T-0010")
        code, out = self.tri("task", "close", "T-0010")
        self.assertEqual(code, 1)
        self.assertIn("AC2: 検証記録がありません", out)
        self.tri("task", "record", "T-0010", "AC2", "fail", "--note", "表示崩れ")
        self.assertIn("最新の検証結果が FAIL", self.tri("task", "close", "T-0010")[1])
        self.tri("task", "record", "T-0010", "AC2", "pass", "--note", "修正後に表示を確認")
        code, out = self.tri("task", "close", "T-0010")
        self.assertEqual(code, 0, out)
        self.assertFalse((self.root / "docs/tasks/T-0010-x.md").exists())
        done = self.read("docs/tasks/_done/T-0010-x.md")
        self.assertIn("status: done", done)
        self.assertIn("closed: ", done)

    def test_gate_detects_stale_evidence(self):
        self.write("docs/tasks/T-0010-x.md", task_text("T-0010", cmd2="`true`"))
        self.tri("task", "verify", "T-0010")
        self.write("src/api/import.py", "def import_html(data):\n    return []\n")
        code, out = self.tri("task", "close", "T-0010")
        self.assertEqual(code, 1)
        self.assertIn("検証後にコードが変更されています", out)
        # docs だけの変更では古くならない
        self.tri("task", "verify", "T-0010")
        self.edit("docs/api.md", "20MB", "30MB")
        self.assertEqual(self.tri("task", "close", "T-0010")[0], 0)

    def test_gate_requires_plan_marker_removed(self):
        text = self.read("docs/tasks/T-0005-tag-search.md").replace("手動: タグ 20 個の環境で入力 \"py\" の候補を確認", "`true`")
        text = text.replace("`python3 -m unittest tests.test_search`", "`true`")
        self.write("docs/tasks/T-0005-tag-search.md", text)
        self.tri("task", "verify", "T-0005")
        code, out = self.tri("task", "close", "T-0005")
        self.assertEqual(code, 1)
        self.assertIn("（計画: T-0005）が残っています", out)
        self.edit("docs/search.md", "REQ-0004 を実現する。（計画: T-0005）", "REQ-0004 を実現する。")
        code, out = self.tri("task", "close", "T-0005")
        self.assertEqual(code, 0, out)
        self.assertIn("この Task に言及するノート", out)
        self.assertIn("inbox.md", out)

    def test_force_and_drop_are_recorded(self):
        self.write("docs/tasks/T-0010-x.md", task_text("T-0010"))
        code, out = self.tri("task", "close", "T-0010", "--force", "外部APIが停止中のため後続で検証")
        self.assertEqual(code, 0)
        self.assertIn("FORCED-CLOSE: 外部APIが停止中", self.read("docs/tasks/_done/T-0010-x.md"))
        self.tri("task", "drop", "T-0006", "--reason", "要求を取り下げ")
        text = self.read("docs/tasks/_done/T-0006-import.md")
        self.assertIn("status: dropped", text)
        self.assertIn("DROPPED: 要求を取り下げ", text)

    def test_list_shows_partial_progress(self):
        self.write("docs/tasks/T-0010-x.md", task_text("T-0010"))
        self.tri("task", "verify", "T-0010")
        code, out = self.tri("task", "list")
        self.assertIn("T-0010  [active]  AC 1/2", out)
        self.write("src/new.py", "x = 1\n")
        self.assertIn("AC 1/2 stale 1", self.tri("task", "list")[1])

    def test_status_transitions(self):
        self.assertEqual(self.tri("task", "status", "T-0006", "blocked")[0], 0)
        self.assertIn("status: blocked", self.read("docs/tasks/T-0006-import.md"))
        self.assertEqual(self.tri("task", "status", "T-0006", "done")[0], 2)  # 完了は close のみ


if __name__ == "__main__":
    unittest.main()
