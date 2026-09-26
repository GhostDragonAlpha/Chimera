"""test_implementation.py -- ONT-P03 reconciliation tests.

Fixture tests in isolated temp registries (gap detection, complete cards,
publication-request receipt classification) plus a live-registry structure
check (skipped when the live registry is absent).
"""
import pathlib
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import implementation as impl  # noqa: E402

MODULES = impl.MODULES
sys.path.insert(0, str(MODULES))
import kanban  # noqa: E402
from agent_slots import Registry  # noqa: E402

SPECS = [{"id": "A", "objective": "o", "falsifier": "f", "steps": ["s"],
          "completion": "c", "depends_on": []},
         {"id": "B", "objective": "o", "falsifier": "f", "steps": ["s"],
          "completion": "c", "depends_on": []}]


def seeded():
    tmp = tempfile.mkdtemp(prefix="p03_fixture_")
    registry = Registry(pathlib.Path(tmp))
    registry.initialize()
    kanban.initialize(registry, SPECS, actor=kanban.LEAD)
    return registry


class FixtureTests(unittest.TestCase):
    def test_unclaimed_card_reported_as_owner_gap(self):
        registry = seeded()
        result = impl.reconcile(registry.root)
        gaps = {g["id"]: g["missing"] for g in result["missing_detail"]}
        self.assertIn("A", gaps)
        self.assertIn("owner:no_active_attempt", gaps["A"])
        self.assertFalse(result["all_identities_present"])

    def test_claimed_card_with_attempt_identities_complete(self):
        registry = seeded()
        packet = kanban.join(registry, "w1", "A")
        result = impl.reconcile(registry.root)
        gaps = {g["id"] for g in result["missing_detail"]}
        self.assertNotIn("A", gaps)
        row = next(r for r in result["rows"] if r["id"] == "A")
        self.assertEqual(row["owners"], ["w1"])
        self.assertTrue(row["ledger_complete"])

    def test_winner_receipt_and_review_verdict_tabled(self):
        registry = seeded()
        packet = kanban.join(registry, "w1", "A")
        kanban.submit(registry, {
            "agent_id": "w1", "task_id": "A",
            "attempt_id": packet["attempt"]["id"],
            "criteria_sha256": packet["attempt"]["criteria_sha256"],
            "pr_url": "https://github.com/GhostDragonAlpha/Chimera/pull/9999",
            "head_sha": "a" * 40})
        # simulate the recorded review shape kanban.review() produces
        # (lead-side authority checks are out of this fixture's scope)
        with registry.transaction() as state:
            pr = state["kanban"]["cards"]["A"]["prs"][
                "https://github.com/GhostDragonAlpha/Chimera/pull/9999"]
            pr["review"] = {"verdict": "ACCEPTED", "head_sha": "a" * 40,
                            "criteria_sha256":
                                packet["attempt"]["criteria_sha256"],
                            "evidence_reference": "fixture",
                            "body": "fixture review",
                            "reviewed_by": "lead"}
            state["kanban"]["cards"]["A"].setdefault(
                "worker_reviews", []).append(
                {"agent_id": "w2", "pr_url":
                    "https://github.com/GhostDragonAlpha/Chimera/pull/9999",
                 "head_sha": "a" * 40, "state": "COMPLETE",
                 "criteria_sha256": packet["attempt"]["criteria_sha256"]})
        result = impl.reconcile(registry.root)
        row = next(r for r in result["rows"] if r["id"] == "A")
        self.assertTrue(row["receipts"]["prs"])
        self.assertEqual(row["awaiting"], "review_or_merge")


class LiveRegistryTests(unittest.TestCase):
    def test_live_reconciliation_tables_every_card(self):
        live = pathlib.Path("E:/ChimeraWork/monkey-coordination")
        if not (live / "agent_slots.sqlite3").is_file():
            raise unittest.SkipTest("live registry absent")
        result = impl.reconcile(live)
        self.assertGreaterEqual(result["card_count"], 20)
        self.assertEqual(result["done_with_winner"], 8)
        self.assertGreaterEqual(result["cards_awaiting_lead_publication"], 1)
        self.assertTrue(all(r["id"] for r in result["rows"]))
        # gaps are named, never silent
        self.assertEqual(len(result["missing_detail"]),
                         result["cards_with_missing_identities"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
