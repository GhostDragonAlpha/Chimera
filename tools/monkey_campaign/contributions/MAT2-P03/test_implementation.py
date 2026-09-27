"""test_implementation.py -- MAT2-P03 reconciliation tests.

Fixture tests in isolated temp registries (live-board gap detection, card
completeness, publication-request receipt classification, archive crosswalk
without promotion, honest UNAVAILABLE material-search entries) plus
live-registry structure checks (skipped when the live registry is absent).

The `kanban.LEAD` constant is used ONLY inside throwaway temp registries to
mirror the production board-creation path, exactly as in the accepted ONT-P03
fixture suite; it is never used as an actor identity against the live registry.

Failing-first: this file was written and executed BEFORE implementation.py
existed (expected failure: ModuleNotFoundError), then made to pass.
"""
import hashlib
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

OLD_SCOPE = "01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6"

OLD_OBJECTIVE = ("Reconcile current work and receipts into existing ledger "
                 "- Every active task has one owner, source revision, scoped "
                 "verdict, and receipt; prior completed work is reused")
NEW_OBJECTIVE = (OLD_OBJECTIVE + ". Material-first addition: Crosswalk old "
                 "receipts to revised requirements without promoting old DONE "
                 "to new acceptance. Search the existing material graph and "
                 "code before adding work.")

SPECS = [{"id": "MAT2-P03", "objective": NEW_OBJECTIVE, "falsifier": "f",
          "steps": ["s"], "completion": "c", "depends_on": []},
         {"id": "MAT2-A05", "objective": "o", "falsifier": "f",
          "steps": ["s"], "completion": "c", "depends_on": []}]


def seeded():
    tmp = tempfile.mkdtemp(prefix="mat2p03_fixture_")
    registry = Registry(pathlib.Path(tmp))
    registry.initialize()
    kanban.initialize(registry, SPECS, actor=kanban.LEAD)
    return registry


def archived_card(cid, state="DONE", objective=OLD_OBJECTIVE):
    return {"id": cid, "state": state, "criteria_sha256": "1" * 64,
            "attempts": {"att1": {"id": "att1", "agent_id": "w-old",
                                  "state": "WON" if state == "DONE" else "PR_SUBMITTED",
                                  "workspace": "E:/fixture", "criteria_sha256": "1" * 64}},
            "prs": {"https://github.com/GhostDragonAlpha/Chimera/pull/140": {
                "head_sha": "a" * 40, "criteria_sha256": "1" * 64,
                "attempt_id": "att1",
                "review": {"verdict": "ACCEPTED", "head_sha": "a" * 40}}},
            "winner": None if state != "DONE" else
            {"pr_url": "https://github.com/GhostDragonAlpha/Chimera/pull/140",
             "head_sha": "a" * 40, "merge_commit_sha": "b" * 40},
            "spec": {"objective": objective}}


def seed_archive(registry, cards):
    with registry.transaction() as state:
        state["scope_archives"] = {OLD_SCOPE: {
            "board": {"schema": "chimera.kanban.v1", "cards": cards},
            "board_sha256": "f" * 64, "reason": "fixture archive"}}


class FixtureLedgerTests(unittest.TestCase):
    def test_unclaimed_card_reported_as_owner_gap(self):
        registry = seeded()
        result = impl.reconcile(registry.root)
        gaps = {g["id"]: g["missing"] for g in result["missing_detail"]}
        self.assertIn("MAT2-P03", gaps)
        self.assertIn("owner:no_active_attempt", gaps["MAT2-P03"])
        self.assertFalse(result["all_identities_present"])

    def test_claimed_card_with_attempt_identities_complete(self):
        registry = seeded()
        kanban.join(registry, "w1", "MAT2-P03")
        result = impl.reconcile(registry.root)
        gaps = {g["id"] for g in result["missing_detail"]}
        self.assertNotIn("MAT2-P03", gaps)
        row = next(r for r in result["rows"] if r["id"] == "MAT2-P03")
        self.assertEqual(row["owners"], ["w1"])
        self.assertTrue(row["ledger_complete"])

    def test_winner_receipt_and_review_verdict_tabled(self):
        registry = seeded()
        packet = kanban.join(registry, "w1", "MAT2-P03")
        kanban.submit(registry, {
            "agent_id": "w1", "task_id": "MAT2-P03",
            "attempt_id": packet["attempt"]["id"],
            "criteria_sha256": packet["attempt"]["criteria_sha256"],
            "pr_url": "https://github.com/GhostDragonAlpha/Chimera/pull/9999",
            "head_sha": "a" * 40})
        with registry.transaction() as state:
            pr = state["kanban"]["cards"]["MAT2-P03"]["prs"][
                "https://github.com/GhostDragonAlpha/Chimera/pull/9999"]
            pr["review"] = {"verdict": "ACCEPTED", "head_sha": "a" * 40,
                            "criteria_sha256":
                                packet["attempt"]["criteria_sha256"],
                            "evidence_reference": "fixture",
                            "body": "fixture review", "reviewed_by": "lead"}
        result = impl.reconcile(registry.root)
        row = next(r for r in result["rows"] if r["id"] == "MAT2-P03")
        self.assertTrue(row["receipts"]["prs"])
        self.assertEqual(row["awaiting"], "review_or_merge")


class FixtureCrosswalkTests(unittest.TestCase):
    def test_done_ont_card_maps_without_promotion(self):
        registry = seeded()
        seed_archive(registry, {"ONT-P03": archived_card("ONT-P03")})
        result = impl.reconcile(registry.root)
        rows = result["crosswalk"]["rows"]
        row = next(r for r in rows if r["archived_id"] == "ONT-P03")
        self.assertEqual(row["mat2_id"], "MAT2-P03")
        self.assertEqual(row["target_kind"], "card")
        self.assertFalse(row["promoted_to_acceptance"])
        self.assertTrue(row["historical_evidence_only"])
        live = Registry(registry.root).readonly()
        live_criteria = live["kanban"]["cards"]["MAT2-P03"]["criteria_sha256"]
        self.assertEqual(row["target_criteria_sha256"], live_criteria)
        self.assertEqual(row["clause_relation"], "extended_material_first")

    def test_workflow_archived_card_maps_to_no_catalog(self):
        registry = seeded()
        seed_archive(registry, {"I-U07-TRACE": archived_card("I-U07-TRACE")})
        result = impl.reconcile(registry.root)
        row = result["crosswalk"]["rows"][0]
        self.assertIsNone(row["mat2_id"])
        self.assertEqual(row["target_kind"], "workflow")
        self.assertFalse(row["promoted_to_acceptance"])

    def test_no_row_ever_promotes_old_done(self):
        registry = seeded()
        seed_archive(registry, {"ONT-P03": archived_card("ONT-P03"),
                                "I-U07-TRACE": archived_card("I-U07-TRACE"),
                                "ONT-A05": archived_card("ONT-A05",
                                                         state="REVIEW")})
        result = impl.reconcile(registry.root)
        for row in result["crosswalk"]["rows"]:
            self.assertFalse(row["promoted_to_acceptance"])
            self.assertTrue(row["historical_evidence_only"])

    def test_clause_relation_classification(self):
        self.assertEqual(impl.classify_clause("x", "x"), "unchanged")
        self.assertEqual(impl.classify_clause("x", "x + more"),
                         "extended_material_first" if "Material-first" in
                         "x + more" else "extended")
        self.assertEqual(impl.classify_clause("x", "y"), "divergent")


class FixtureMaterialSearchTests(unittest.TestCase):
    def test_found_paths_carry_true_hashes_and_absent_are_unavailable(self):
        tmp = tempfile.mkdtemp(prefix="mat2p03_search_")
        root = pathlib.Path(tmp)
        (root / "sub").mkdir()
        payload = b"deterministic bytes\n"
        (root / "sub" / "real.txt").write_bytes(payload)
        probes = ["sub/real.txt", "sub/missing.txt"]
        result = impl.material_search(root, probes)
        self.assertEqual(result["found"][0]["path"], "sub/real.txt")
        self.assertEqual(result["found"][0]["sha256"],
                         hashlib.sha256(payload).hexdigest())
        self.assertEqual(result["unavailable"],
                         [{"path": "sub/missing.txt", "status": "UNAVAILABLE"}])


class LiveRegistryTests(unittest.TestCase):
    LIVE = pathlib.Path("E:/ChimeraWork/monkey-coordination")

    def setUp(self):
        if not (self.LIVE / "agent_slots.sqlite3").is_file():
            raise unittest.SkipTest("live registry absent")

    def test_live_reconciliation_tables_every_card(self):
        result = impl.reconcile(self.LIVE)
        self.assertGreaterEqual(result["card_count"], 6)
        self.assertTrue(all(r["id"] for r in result["rows"]))
        self.assertTrue(all(r["criteria_sha256_present"] for r in result["rows"]))
        p01 = next(r for r in result["rows"] if r["id"] == "MAT2-P01")
        self.assertEqual(p01["state"], "DONE")
        self.assertEqual(p01["source_revision"]["winner_pr"],
                         "https://github.com/GhostDragonAlpha/Chimera/pull/192")
        self.assertTrue(p01["source_revision"]["winner_head"])
        self.assertTrue(p01["source_revision"]["winner_merge"])
        self.assertEqual(len(result["missing_detail"]),
                         result["cards_with_missing_identities"])

    def test_live_crosswalk_covers_archive_without_promotion(self):
        result = impl.reconcile(self.LIVE)
        cw = result["crosswalk"]
        self.assertEqual(cw["archived_card_count"], 43)
        self.assertEqual(len(cw["rows"]), 43)
        self.assertTrue(all(r["promoted_to_acceptance"] is False
                            for r in cw["rows"]))
        self.assertEqual(cw["mapped_to_catalog"]
                         + cw["workflow_card_count"], 43)
        self.assertGreaterEqual(cw["mapped_to_catalog"], 22)
        self.assertGreaterEqual(cw["workflow_card_count"], 21)
        # every mapped target must exist in the live board or backlog
        state = Registry(self.LIVE).readonly()
        known = set(state["kanban"]["cards"]) | {
            b["id"] for b in state["kanban"]["backlog"]}
        for r in cw["rows"]:
            if r["mat2_id"]:
                self.assertIn(r["mat2_id"], known)

    def test_live_material_search_frozen_predictions(self):
        result = impl.reconcile(self.LIVE)
        ms = result["material_search"]
        found = {f["path"] for f in ms["found"]}
        unavailable = {u["path"] for u in ms["unavailable"]}
        self.assertNotIn("tools/monkey_campaign/monkey_completion_map.json",
                         unavailable)
        self.assertIn("tools/monkey_campaign/monkey_completion_map.json", found)
        self.assertIn("planning_inventory.json", unavailable)
        self.assertIn("plans/material-first-v2", unavailable)
        self.assertIn("forearm_package/ANATOMICAL_DECISION_TABLE.md",
                      unavailable)
        for f in ms["found"]:
            p = impl.REPO_ROOT / f["path"]
            self.assertEqual(f["sha256"],
                             hashlib.sha256(p.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main(verbosity=2)
