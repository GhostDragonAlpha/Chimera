"""test_verify_ontology.py -- ONT-X02 reconciliation tests.

Run:  python -B -m unittest test_verify_ontology -v
"""
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import verify_ontology as vo  # noqa: E402


class OntX02ReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = vo.run_all()

    def test_all_green(self):
        self.assertTrue(self.r["all_green"], self.r)

    def test_done_when_clauses(self):
        self.assertTrue(self.r["reaches_play"])
        self.assertTrue(self.r["pause_via_key"])
        self.assertTrue(self.r["exit_via_key"])
        self.assertTrue(self.r["restart_explicit_user_action"])

    def test_recovery_profile(self):
        self.assertTrue(self.r["pause_quiesces_mapper"])
        self.assertTrue(self.r["paused_emits_nothing"])
        self.assertTrue(self.r["teardown_once_ordered"])
        self.assertTrue(self.r["exited_is_terminal"])
        self.assertTrue(self.r["resume_accepts_keys"])

    def test_no_hidden_or_developer_transitions(self):
        self.assertTrue(self.r["start_is_key_only"])
        self.assertTrue(self.r["restart_requires_paused"])
        self.assertTrue(self.r["no_timer_transitions"])
        self.assertTrue(self.r["restart_quiesces_then_boots"])

    def test_existing_suite_passes_at_pinned_head(self):
        self.assertTrue(self.r["existing_suite_exit_0"])
        self.assertTrue(self.r["existing_suite_all_pass"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
