#!/usr/bin/env python3
"""MAT2-W06 named checks: every evaluation claim is asserted against the
pinned bytes, and every falsifier arm carries its own passing clean control
FIRST, then the bite (G1). Zero skips by design (G12).

G5: refuse_vacuous_comparison + vacuous_guard_selftest() run at import; the
frozen first-vs-last window ruling goes through the guard both here and in
the evaluator.

Run:  python -B run_checks.py   (unittest discover -p test_*.py)
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

import verify_inputs as vi
from run_evaluation import (
    SEEDS,
    detector_curve_digest,
    detector_deploy_rows,
    detector_heldout_cells,
    detector_recompute,
    detector_seed_set,
    detector_verdict_pure,
    recompute_windows,
    rule_verdict,
    scan_no_run_paths,
    vacuous_guard_selftest,
)

assert vacuous_guard_selftest(), "vacuous_guard_selftest failed at import"

HERE = Path(__file__).resolve().parent
UP = vi.UPSTREAM

# scratch bite texts (string constants only; the FB5 scanner sees no import)
SCRATCH_RUN_TEXT = "import subprocess\nsubprocess.run(['x'])\n"
SCRATCH_TRAIN_TEXT = "from run_training import main\nmain()\n"
SCRATCH_SCENE_TEXT = "import scene_cpu\n"
SCRATCH_SOCKET_TEXT = "import socket\ns = socket.socket()\n"

FROZEN_RULE = ("SUCCESS iff mean_iteration_fitness_last100 > "
               "mean_iteration_fitness_first100")


def load(path: Path):
    return json.loads(path.read_bytes().decode("utf-8"))


def load_seed(seed: int):
    return (load(UP / "receipts" / f"seed_{seed}_receipt.json"),
            load(UP / "receipts" / f"seed_{seed}_curve.json"))


class W06Identity(unittest.TestCase):
    def test_registry_identity(self):
        reg = vi.verify_registry()
        # criteria/agent are attempt-immutable; mutable card state is only
        # RECORDED (the F03 F-1 law: no live mutable assertion).
        self.assertEqual(reg["criteria_sha256"], vi.CRITERIA_SHA256)
        self.assertEqual(reg["attempt_agent"], vi.AGENT_ID)

    def test_prereg_frozen_and_pinned(self):
        self.assertTrue((HERE / "PREREGISTRATION.md").exists())
        for seed in SEEDS:
            body = load(HERE / "receipts" / f"seed_{seed}_evaluation.json")
            self.assertEqual(body["preregistration_sha256"],
                             vi.prereg_sha256())
        summary = load(HERE / "receipts" / "evaluation_summary.json")
        self.assertEqual(summary["preregistration_sha256"],
                         vi.prereg_sha256())

    def test_pins_live(self):
        rows = vi.verify()
        self.assertEqual(len(rows), 21)
        self.assertTrue(all(r["ok"] for r in rows))

    def test_frozen_rule_verbatim_in_prereg(self):
        text = (HERE / "PREREGISTRATION.md").read_bytes().decode("utf-8")
        self.assertIn("SUCCESS iff `mean_iteration_fitness_last100 > "
                      "mean_iteration_fitness_first100`", text)
        self.assertIn("without cherry-picking or additional tuned runs", text)


class FB1PinBite(unittest.TestCase):
    def test_mutated_pin_refused(self):
        parts, good = vi.PINS_UPSTREAM[0]
        mutated = [(parts, "0" * 64)]
        try:
            vi.verify(expect=mutated)
        except vi.Refusal as exc:
            self.assertTrue(str(exc).startswith("input_pin_mismatch:"))
        else:
            self.fail("mutated pin did not refuse")


class MetricRecomputeChecks(unittest.TestCase):
    def test_m4_bit_exact_all_seeds(self):
        for seed in SEEDS:
            rec, curve = load_seed(seed)
            sm = rec["success_metrics"]
            self.assertIsNone(detector_recompute(
                curve, sm["mean_iteration_fitness_first100"],
                sm["mean_iteration_fitness_last100"],
                sm["improved_first_to_last_100"]))

    def test_m6_curve_digests(self):
        for seed in SEEDS:
            rec, curve = load_seed(seed)
            code = detector_curve_digest(
                curve,
                (UP / "receipts" / f"seed_{seed}_curve.json").read_bytes(),
                rec["fitness_curve_sha256"],
                vi.sha_bytes((UP / "receipts"
                              / f"seed_{seed}_curve.json").read_bytes()))
            self.assertIsNone(code)

    def test_theta_npz_identity_chain(self):
        manifest = load(UP / "trained" / "trained_policy_manifest.json")
        deploy = load(UP / "receipts" / "deploy_check_receipt.json")
        for seed in SEEDS:
            rec, _ = load_seed(seed)
            disk = vi.sha_bytes(
                (UP / "trained" / f"theta_{seed}.npz").read_bytes())
            self.assertEqual(disk, rec["theta_npz_sha256"])
            self.assertEqual(disk,
                             manifest["weights"][str(seed)]["sha256"])
            self.assertEqual(disk,
                             deploy["trained_theta_npz_sha256"][str(seed)])


class FB2RecomputeBite(unittest.TestCase):
    def test_perturbed_curve_detected(self):
        rec, curve = load_seed(SEEDS[0])
        sm = rec["success_metrics"]
        tampered = json.loads(json.dumps(curve))
        tampered[0][0] = tampered[0][0] + 5.0
        code = detector_recompute(
            tampered, sm["mean_iteration_fitness_first100"],
            sm["mean_iteration_fitness_last100"],
            sm["improved_first_to_last_100"])
        self.assertIsNotNone(code)
        self.assertTrue(code.startswith("metric_recompute_mismatch:"))


class CherryPickChecks(unittest.TestCase):
    def test_seed_set_complete(self):
        self.assertIsNone(detector_seed_set(set(SEEDS)))
        summary = load(HERE / "receipts" / "evaluation_summary.json")
        self.assertEqual(sorted(r["seed"] for r in summary["seed_rows"]),
                         sorted(SEEDS))

    def test_heldout_matrix_complete(self):
        heldout = load(UP / "receipts" / "heldout_receipt.json")
        self.assertIsNone(detector_heldout_cells(heldout["cells"]))
        self.assertEqual(len(heldout["cells"]), 9)

    def test_integrity_receipts(self):
        for seed in SEEDS:
            rec, _ = load_seed(seed)
            self.assertEqual(rec["status"], "EXECUTED_COMPLETED")
            self.assertIsNone(rec["termination_code"])
            self.assertEqual(rec["decisions_executed"],
                             rec["decisions_declared"])


class FB3CherryPickBite(unittest.TestCase):
    def test_missing_seed_detected(self):
        code = detector_seed_set(set(SEEDS[:2]))
        self.assertIsNotNone(code)
        self.assertTrue(code.startswith("cherry_pick_detected:seed_set"))

    def test_missing_heldout_cell_detected(self):
        heldout = load(UP / "receipts" / "heldout_receipt.json")
        cells = [c for c in heldout["cells"]
                 if not (c["theta_seed"] == 20260920
                         and c["scene_seed"] == 20260921)]
        self.assertEqual(len(cells), 8)
        code = detector_heldout_cells(cells)
        self.assertIsNotNone(code)
        self.assertTrue(code.startswith("cherry_pick_detected:heldout"))


class DeployGateChecks(unittest.TestCase):
    def test_three_decisions(self):
        deploy = load(UP / "receipts" / "deploy_check_receipt.json")
        self.assertIsNone(detector_deploy_rows(deploy))
        self.assertEqual(deploy["allow_frozen_relation"]["decision"],
                         "ALLOW")
        self.assertEqual(deploy["block_trained_bundle"]["decision"],
                         "BLOCK")
        self.assertEqual(deploy["block_foreign_build"]["decision"], "BLOCK")
        self.assertTrue(deploy["block_trained_bundle"]["reasons"])

    def test_certificate_pin(self):
        rows = {Path(r["path"]).name: r for r in vi.verify()}
        self.assertTrue(rows["w04_certificate.json"]["ok"])
        self.assertTrue(rows["w04_freeze_manifest.json"]["ok"])


class FB4DeployGateBite(unittest.TestCase):
    def test_trained_allow_tamper_detected(self):
        deploy = load(UP / "receipts" / "deploy_check_receipt.json")
        deploy["block_trained_bundle"]["decision"] = "ALLOW"
        code = detector_deploy_rows(deploy)
        self.assertIsNotNone(code)
        self.assertEqual(code, "deploy_gate_ruling_violated:trained_bundle")


class VerdictChecks(unittest.TestCase):
    def test_verdicts_match_frozen_rule(self):
        for seed in SEEDS:
            rec, curve = load_seed(seed)
            first100, last100 = recompute_windows(curve)
            verdict = rule_verdict(first100, last100)
            body = load(HERE / "receipts"
                        / f"seed_{seed}_evaluation.json")
            self.assertIsNone(detector_verdict_pure(body, verdict))
            self.assertEqual(body["verdict_rule"], FROZEN_RULE)
            self.assertEqual(body["verdict"], verdict)
            self.assertEqual(
                body["verdict"],
                "SUCCESS" if last100 > first100 else "FAILURE")

    def test_all_failures_recorded_honestly(self):
        # the honest expected outcome (prereg E1): the check pins the REPORT
        # to the recomputation, so a flipped or cherry-picked verdict REDs.
        for seed in SEEDS:
            rec, curve = load_seed(seed)
            first100, last100 = recompute_windows(curve)
            self.assertGreater(first100, last100)
            body = load(HERE / "receipts"
                        / f"seed_{seed}_evaluation.json")
            self.assertEqual(body["verdict"], "FAILURE")


class FB6VerdictBite(unittest.TestCase):
    def test_flipped_verdict_detected(self):
        seed = SEEDS[0]
        rec, curve = load_seed(seed)
        first100, last100 = recompute_windows(curve)
        body = load(HERE / "receipts" / f"seed_{seed}_evaluation.json")
        tampered = dict(body)
        tampered["verdict"] = ("SUCCESS" if body["verdict"] == "FAILURE"
                               else "FAILURE")
        self.assertIsNotNone(detector_verdict_pure(tampered,
                                                   rule_verdict(first100,
                                                                last100)))


class FalsifierMappingChecks(unittest.TestCase):
    def test_no_termination_codes(self):
        # the card falsifier classes map to the runbook's hard-gate
        # termination records; none fired on any seed.
        codes = {"contact_floor_breach", "envelope_breach",
                 "intervention_observed", "bounds_breach",
                 "numerical_failure", "availability_breach"}
        for seed in SEEDS:
            rec, _ = load_seed(seed)
            self.assertIsNone(rec["termination_code"])
            self.assertNotIn(rec["termination_code"], codes)

    def test_recipe_equivalence_clean(self):
        equiv = load(UP / "receipts" / "recipe_equivalence_receipt.json")
        self.assertTrue(equiv["byte_identical"])
        self.assertEqual(equiv["frozen_trajectory_sha256"],
                         "cd4944d99be1270951926be53859828a6b0aef21d32d6551f"
                         "68e78d504ef6c7a")

    def test_state_chain_heads_present(self):
        for seed in SEEDS:
            rec, _ = load_seed(seed)
            self.assertEqual(len(rec["state_chain_head"]), 64)


class NoRunsStructuralChecks(unittest.TestCase):
    def test_contribution_scan_green(self):
        violations = []
        for py in sorted(HERE.glob("*.py")):
            violations.extend(
                scan_no_run_paths(py.read_bytes().decode("utf-8"), py.name))
        self.assertEqual(violations, [])

    def test_run_path_bites(self):
        for text, marker in ((SCRATCH_RUN_TEXT, "import:subprocess"),
                             (SCRATCH_TRAIN_TEXT, "importfrom:run_training"),
                             (SCRATCH_SCENE_TEXT, "import:scene_cpu"),
                             (SCRATCH_SOCKET_TEXT, "import:socket")):
            violations = scan_no_run_paths(text, "scratch_bite.py")
            self.assertTrue(any(v.startswith(marker) for v in violations),
                            "%s not detected in %r" % (marker, violations))

    def test_no_runs_recorded(self):
        summary = load(HERE / "receipts" / "evaluation_summary.json")
        self.assertEqual(summary["no_runs_law"][
            "physics_runs_executed_by_this_card"], 0)
        self.assertEqual(summary["no_runs_law"][
            "training_runs_executed_by_this_card"], 0)
        self.assertEqual(summary["no_runs_law"][
            "tuned_runs_executed_by_this_card"], 0)


class PredictionChecks(unittest.TestCase):
    def test_summary_predictions_match_recomputation(self):
        summary = load(HERE / "receipts" / "evaluation_summary.json")
        preds = summary["predictions"]
        all_fail = all(
            load(HERE / "receipts" / f"seed_{s}_evaluation.json")["verdict"]
            == "FAILURE" for s in SEEDS)
        self.assertEqual(preds["E1_all_seeds_fail_training_signal"][
            "observed"], all_fail)
        self.assertTrue(preds["E2_bit_exact_recomputation"]["observed"])
        self.assertTrue(preds["E3_receipts_complete"]["observed"])
        self.assertTrue(preds["E4_trained_blocked_from_deploy"]["observed"])

    def test_deploy_treatment_recorded(self):
        summary = load(HERE / "receipts" / "evaluation_summary.json")
        self.assertEqual(
            summary["deploy_treatment"]["trained_theta_tuple"], "BLOCK")
        self.assertEqual(summary["deploy_treatment"]["frozen_relation"],
                         "ALLOW")


if __name__ == "__main__":
    unittest.main()
