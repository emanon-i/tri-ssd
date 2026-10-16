"""長期運用シミュレーション（tests/simulate.py）の不変条件。"""
import unittest

import helpers  # noqa: F401
import simulate


class SimulationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.good, cls.good_log = simulate.run(cycles=12, mode="disciplined")
        cls.bad, cls.bad_log = simulate.run(cycles=6, mode="careless")

    def test_disciplined_stays_healthy(self):
        for r in self.good:
            self.assertEqual((r["errors"], r["history"], r["duplicate"], r["broken"]), (0, 0, 0, 0), r)
            self.assertEqual(r["handoff_files"], 1)
            self.assertTrue(r["status_has_handoff"])
        self.assertEqual(self.good_log, [])

    def test_decision_change_replaces_old_text(self):
        self.assertTrue(self.good[2]["old_storage_text"])
        self.assertFalse(any(r["old_storage_text"] for r in self.good[3:]))

    def test_notes_do_not_accumulate(self):
        self.assertEqual(len({r["notes_tokens"] for r in self.good}), 1)

    def test_docs_grow_linearly_with_spec_not_history(self):
        growth = [b["docs_tokens"] - a["docs_tokens"] for a, b in zip(self.good, self.good[1:])]
        self.assertLess(max(growth), 150)  # 1 機能あたりの仕様量だけ増える

    def test_context_stays_flat_while_docs_grow(self):
        first, last = self.good[0], self.good[-1]
        self.assertGreater(last["docs_tokens"], 3 * first["docs_tokens"])
        self.assertLess(last["context_tokens"], 1.3 * first["context_tokens"])

    def test_careless_agent_is_detected(self):
        self.assertTrue(all("（計画:" in line for line in self.bad_log))  # 完了ゲートが毎回拒否
        last = self.bad[-1]
        self.assertGreaterEqual(last["stale_marker"], 6)
        self.assertGreaterEqual(last["history"], 1)
        self.assertTrue(last["old_storage_text"])
        self.assertGreater(last["notes_tokens"], self.bad[0]["notes_tokens"] * 4)


if __name__ == "__main__":
    unittest.main()
