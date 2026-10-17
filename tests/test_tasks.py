"""Task の採番・検証証跡・完了ゲート・アーカイブ。"""
import unittest

from helpers import ProjectCase, git
from trissd import tasks


def task_text(id_, cmd1="true", cmd2="手動: 画面で確認", refs="REQ-0005"):
    return (f"---\nid: {id_}\nstatus: open\nrefs: [{refs}]\ncode: [src/api/import.py]\n---\n# {id_} 取り込み\n\n"
            "## 目的の状態\n\nREQ-0005 を満たす。\n\n## 受け入れ条件\n\n"
            f"- AC1: 取り込める\n  - 検証: `{cmd1}`\n- AC2: 表示される\n  - 検証: {cmd2}\n\n## 検証記録\n")


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
        self.assertNotIn("## メモ", out)

        self.tri("task", "close", "T-0007")
        done = self.tri("task", "report", "T-0007")[1]
        self.assertIn("（done・", done)
        self.assertNotIn("## 変更したファイル", done)


    def test_report_shows_memo_and_other_task_files(self):
        self.tri("task", "start", "T-0005")
        self.edit("docs/tasks/T-0006-import.md", "## 検証記録", "## メモ\n\n- T-0005 が tags 表を触る\n\n## 検証記録")
        out = self.tri("task", "report", "T-0005")[1]
        self.assertIn("## メモ（作業中の発見）", out)
        self.assertIn("tags.use_count", out)
        self.assertIn("- docs/tasks/T-0006-import.md", out)
        self.assertNotIn("- docs/tasks/T-0005-tag-search.md", out)

    def test_start_reports_unchanged_status(self):
        self.assertIn("既に active", self.tri("task", "start", "T-0005")[1])
        self.assertIn("open → active", self.tri("task", "start", "T-0007")[1])


class TaskTest(ProjectCase):
    def test_new_numbering_is_permanent(self):
        code, out = self.tri("task", "new", "Export JSON", "--refs", "REQ-0006", "--code", "src/api/")
        self.assertEqual(code, 0)
        self.assertIn("docs/tasks/T-0008-export-json.md", out)
        text = self.read("docs/tasks/T-0008-export-json.md")
        self.assertIn("refs: [REQ-0006]", text)
        self.assertIn("- AC1: ", text)
        self.assertNotIn("[ ]", text)  # AC の状態は検証記録だけが持つ
        # CHANGELOG にだけ残る番号も再利用しない
        self.edit("CHANGELOG.md", "- 全文検索（T-0003）", "- 全文検索（T-0003）\n- 中止（T-0020）")
        self.assertEqual(self.tri("id", "T")[1].strip(), "T-0021")

    def test_japanese_title_slug(self):
        self.tri("task", "new", "保持期間を 14 日にする")
        self.assertTrue((self.root / "docs/tasks/T-0008.md").exists())
        self.tri("task", "new", "保持期間", "--slug", "trash retention")
        self.assertTrue((self.root / "docs/tasks/T-0009-trash-retention.md").exists())

    def test_title_with_section_word(self):
        text = task_text("T-0010", "true").replace("# T-0010", "# T-0010 検証記録と受け入れ条件の整理", 1)
        self.assertEqual([a.label for a in tasks.parse_acs(text)], ["AC1", "AC2"])

    def test_parse_acs(self):
        acs = tasks.parse_acs(task_text("T-0010", "python3 -m unittest x", "手動: 見る"))
        self.assertEqual([a.label for a in acs], ["AC1", "AC2"])
        self.assertEqual(acs[0].commands, ["python3 -m unittest x"])
        self.assertTrue(acs[1].manual)
        acs = tasks.parse_acs(task_text("T-0010", "true", "手動: `claude plugin eval` の結果を見る"))
        self.assertTrue(acs[1].manual)  # 手動の確認方法に書いたコマンドは実行しない

    def test_verify_records_evidence(self):
        self.write("docs/tasks/T-0010-x.md", task_text("T-0010", "echo ok"))
        code, out = self.tri("task", "verify", "T-0010")
        self.assertEqual(code, 0)
        self.assertIn("AC1 PASS", out)
        self.assertIn("手動確認が必要: AC2", out)
        text = self.read("docs/tasks/T-0010-x.md")
        self.assertIn("- AC1: 取り込める", text)
        self.assertNotIn("[x]", text)
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

    def test_evidence_keeps_latest_result_per_ac(self):
        self.write("docs/tasks/T-0010-x.md", task_text("T-0010", "exit 1"))
        self.tri("task", "verify", "T-0010")
        self.edit("docs/tasks/T-0010-x.md", "`exit 1`", "`true`")
        self.tri("task", "verify", "T-0010")
        self.tri("task", "record", "T-0010", "AC2", "fail", "--note", "崩れ")
        self.tri("task", "record", "T-0010", "AC2", "pass", "--note", "修正後に確認" * 30)
        ev = tasks.parse_evidence(self.read("docs/tasks/T-0010-x.md"))
        self.assertEqual([(e.label, e.result) for e in ev], [("AC1", "PASS"), ("AC2", "PASS")])
        self.assertNotIn("崩れ", self.read("docs/tasks/T-0010-x.md"))

    def test_template_has_memo_section(self):
        self.tri("task", "new", "Export", "--refs", "REQ-0006")
        text = self.read("docs/tasks/T-0008-export.md")
        for head in ("## 目的の状態", "## 受け入れ条件", "## メモ", "## 検証記録"):
            self.assertIn(head, text)
        self.assertIn("refs: [REQ-0006]", text)

    def test_legacy_checkbox_is_read_and_dropped(self):
        # 旧形式のチェック欄は状態を持たない。[x] でも検証記録が FAIL なら FAIL
        self.write("docs/tasks/T-0010-x.md", task_text("T-0010", "exit 3").replace("- AC1", "- [x] AC1"))
        self.assertEqual(tasks.parse_acs(self.read("docs/tasks/T-0010-x.md"))[0].label, "AC1")
        code, out = self.tri("task", "verify", "T-0010")
        self.assertEqual(code, 1)
        self.assertIn("AC1 FAIL", out)
        self.assertIn("- AC1: 取り込める", self.read("docs/tasks/T-0010-x.md"))

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
        self.edit("docs/search.md", "REQ-0004 を実現する。（計画: T-0005）", "REQ-0004 を実現する。例: `（計画: T-0005）`")
        code, out = self.tri("task", "close", "T-0005")  # インラインコード内の例示はマーカーではない
        self.assertEqual(code, 0, out)

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
