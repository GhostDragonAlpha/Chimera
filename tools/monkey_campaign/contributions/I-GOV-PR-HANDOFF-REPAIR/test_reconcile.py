"""test_reconcile.py -- I-GOV-PR-HANDOFF-REPAIR correction tests.

Wraps the reconciliation probe as unittest: the historical PR #128's two
defect scenarios cannot reproduce against the CURRENT installed modules in an
isolated registry, and the card falsifier invariants hold. Read-only over the
production modules; all registry operations run in temp directories.

Run:  python -B -m unittest test_reconcile -v
"""
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import reconcile  # noqa: E402


class ReconciliationProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = reconcile.run_all()

    def test_probe_all_green(self):
        self.assertTrue(self.results["all_green"],
                        str(self.results.get("probe_error", self.results)))

    def test_d1_explicit_routing_never_wrong_card(self):
        r = self.results
        self.assertTrue(r["d1_refusal_named"])          # named refusal, not a card
        self.assertTrue(r["d1_no_autodisplacement"])    # astra-0022 law intact
        self.assertTrue(r["d1_explicit_never_wrong_card"])
        self.assertTrue(r["d1_explicit_positive_control"])

    def test_d2_durable_pr_request_bridge(self):
        r = self.results
        self.assertTrue(r["d2_request_recorded"])
        self.assertTrue(r["d2_state_is_publication_requested"])
        self.assertTrue(r["d2_idempotent_same_request"])
        self.assertTrue(r["d2_wrong_criteria_refused"])
        self.assertTrue(r["d2_next_card_differs"])

    def test_falsifier_invariants(self):
        r = self.results
        self.assertTrue(r["capacity_stays_ten"])
        self.assertTrue(r["criteria_hashes_unchanged"])
        self.assertTrue(r["foreign_attempts_untouched"])

    def test_probe_uses_current_installed_modules(self):
        self.assertEqual(reconcile.MODULES_DIR,
                         pathlib.Path("E:/PythonChimera/tools/monkey_campaign"))
        self.assertTrue((reconcile.MODULES_DIR / "continuous_cycle.py").is_file())


if __name__ == "__main__":
    unittest.main(verbosity=2)
