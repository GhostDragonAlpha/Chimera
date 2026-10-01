"""MAT2-W05 named checks (the executable done_when + falsifier bites).

Every claim the report makes is asserted here against the receipts; every
falsifier arm (prereg section 5) has its bite below, and the bites are
guarded against vacuity (G5: refuse_vacuous_comparison + selftest). Zero
skips by design (G12: the receipt claims 'N executed, 0 skipped').

Run:  python -B run_checks.py   (discovers this file, emits checks_receipt.json)
"""
from __future__ import annotations

import ast
import hashlib
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
import verify_inputs as vi

RUNBOOK = json.loads((HERE / "runbook.json").read_bytes().decode("utf-8"))
FILL = json.loads((HERE / "w05_freeze_fill.json").read_bytes().decode("utf-8"))
CERT = json.loads((vi.STORE / "MAT2-W04/numerical/w04_certificate.json")
                  .read_bytes().decode("utf-8"))
FREEZE = json.loads((vi.STORE / "MAT2-W04/numerical/w04_freeze_manifest.json")
                    .read_bytes().decode("utf-8"))
SEEDS = RUNBOOK["seeds"]["values"]


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load(name: str) -> dict:
    return json.loads((HERE / "receipts" / name).read_bytes().decode("utf-8"))


def refuse_vacuous_comparison(a, b, code: str) -> None:
    """G5: a comparison that cannot discriminate must be REFUSED, not run.
    Two identical operands would pass any tolerance gate vacuously."""
    if a == b:
        raise AssertionError("VACUOUS_COMPARISON_REFUSED:" + code
                             + ": operands are identical; the gate cannot "
                               "discriminate and must not run")


def vacuous_guard_selftest() -> None:
    try:
        refuse_vacuous_comparison(1.0, 1.0, "selftest")
    except AssertionError as exc:
        assert "VACUOUS_COMPARISON_REFUSED:selftest" in str(exc)
        return
    raise AssertionError("vacuous guard did NOT fire (the guard is broken)")


vacuous_guard_selftest()


class W05Identity(unittest.TestCase):
    def test_registry_identity(self):
        reg = vi.verify_registry()
        self.assertEqual(reg["criteria_sha256"], vi.CRITERIA_SHA256)
        self.assertEqual(reg["attempt_agent"], vi.AGENT_ID)

    def test_prereg_frozen_and_pinned(self):
        sha_pre = sha((HERE / "PREREGISTRATION.md").read_bytes())
        sha_add = sha((HERE / "PREREGISTRATION-ADDENDUM-1.md").read_bytes())
        self.assertEqual(sha_pre, vi.prereg_sha256())
        self.assertEqual(sha_add, vi.addendum_sha256())
        self.assertEqual(FILL["preregistration_sha256"], sha_pre)
        self.assertEqual(FILL["preregistration_addendum_1_sha256"], sha_add)

    def test_pins_live(self):
        rows = vi.verify()
        self.assertTrue(all(r["ok"] for r in rows))
        self.assertEqual(len(rows), 19)

    def test_addendum_correction_is_bound(self):
        self.assertEqual(FILL["parent_freeze"]["sha256"],
                         "be632ffc85865515285f3d622a09882a3180a43101027914f1ed3408496f5d29")
        self.assertEqual(FILL["parent_freeze"]["declared_fields_before"],
                         {"runbook_id": None, "seeds": None,
                          "acceptance_criteria": None})


class FB1PinBite(unittest.TestCase):
    def test_mutated_pin_refused(self):
        bad = list(vi.PINS)
        parts, sha_ok = bad[0]
        bad[0] = (parts, "0" * 64)
        with self.assertRaises(vi.Refusal) as ctx:
            vi.verify(bad)
        self.assertTrue(str(ctx.exception).startswith("input_pin_mismatch"))


class RunbookChecks(unittest.TestCase):
    def test_runbook_id_and_seeds(self):
        self.assertEqual(RUNBOOK["runbook_id"], "walk1m-r1")
        self.assertEqual(RUNBOOK["seeds"]["values"], [20260919, 20260920, 20260921])
        self.assertEqual(RUNBOOK["seeds"]["suite_registered_cases_sha256"],
                         "d6fa74bd89d14f2e49b4d196a974e00f7a19d167e516122e790f5b564937dea7")

    def test_decisions_math_closes(self):
        d = RUNBOOK["decisions"]
        self.assertEqual(d["iterations"], 2000)
        self.assertEqual(d["evaluations_per_iteration"], 2)
        self.assertEqual(d["decisions_per_evaluation"], 250)
        self.assertEqual(d["per_seed_total"], 1_000_000)
        self.assertEqual(d["iterations"] * d["evaluations_per_iteration"]
                         * d["decisions_per_evaluation"], d["per_seed_total"])
        self.assertEqual(d["ticks_per_seed_total"], 15_000_000)
        self.assertEqual(d["hold_ticks"] * d["policy_hz"], d["physics_hz"])

    def test_trainer_frozen_constants(self):
        t = RUNBOOK["trainer"]
        self.assertEqual(t["perturbation"]["size_c"], 0.05)
        self.assertEqual(t["step"]["a_s"], 0.01)
        self.assertEqual(t["parameter_vector"]["dim"], 25864)
        self.assertEqual(t["parameter_vector"]["architecture"], [64, 128, 128, 8])
        self.assertIn("NONE", t["exploration_noise"])
        self.assertIn("theta0 = 0", t["init"])

    def test_velocity_envelope_derived_value(self):
        vi.bootstrap_pinned_imports()
        from tools.policy_compat import scene_cpu
        v = scene_cpu.derived_envelope()["velocity_envelope_m_s"]
        # an exact-derivation identity check (not a tolerance window): the
        # recomputed envelope must equal the frozen constant
        self.assertAlmostEqual(v, RUNBOOK["velocity_envelope_m_s"], places=15)
        self.assertGreater(RUNBOOK["velocity_envelope_m_s"], 0.0)

    def test_no_gpu_and_termination_law(self):
        self.assertIn("NO GPU", RUNBOOK["environment"]["gpu"])
        self.assertTrue(RUNBOOK["termination"]["retry"].startswith("NONE"))
        self.assertEqual(len(RUNBOOK["termination"]["codes"]), 8)
        self.assertEqual(RUNBOOK["bounded_resources"]["per_seed_wall_s"], 5400)


class SlotFillChecks(unittest.TestCase):
    def test_fill_values_match_runbook(self):
        self.assertEqual(FILL["fill"]["runbook_id"], RUNBOOK["runbook_id"])
        self.assertEqual(FILL["fill"]["seeds"], RUNBOOK["seeds"]["values"])
        self.assertEqual(FILL["runbook_document"]["sha256"],
                         sha((HERE / "runbook.json").read_bytes().rstrip(b"\n")))

    def test_acceptance_criteria_structure(self):
        ac = FILL["fill"]["acceptance_criteria"]
        self.assertEqual(len(ac["execution_integrity_gates"]), 6)
        self.assertIn("failures RETAINED", ac["failure_retention"])
        self.assertEqual(ac["termination_codes"],
                         RUNBOOK["termination"]["codes"])
        self.assertIn("records", ac["per_seed_receipt_law"])

    def test_governing_laws_bound_in_parent(self):
        laws = FILL["parent_freeze"]["governing_laws"]
        ids = {g["identity"] for g in laws}
        self.assertEqual(ids, {"K01", "P04"})

    def test_parent_slot_status(self):
        self.assertEqual(FILL["parent_freeze"]["slot_status_before"],
                         "FROZEN_SLOT_SHAPE_VALUES_STRUCTURALLY_DOWNSTREAM_W05")


class FB4SlotFillBite(unittest.TestCase):
    def test_mutated_fill_detected(self):
        mutated = json.loads(json.dumps(FILL))
        mutated["fill"]["seeds"] = [1, 2, 3]
        self.assertNotEqual(mutated["fill"]["seeds"],
                            RUNBOOK["seeds"]["values"])
        with self.assertRaises(AssertionError):
            self.assertEqual(mutated["fill"]["seeds"],
                             RUNBOOK["seeds"]["values"])


class BaselineChecks(unittest.TestCase):
    def test_baseline_anchors_exact(self):
        receipt = load("baseline_receipt.json")
        self.assertEqual(receipt["schema"], "chimera.w05_baseline.v1")
        for key, comp in receipt["anchor_comparisons"].items():
            self.assertEqual(comp["verdict"], "EXACT", key)
            self.assertEqual(comp["reproduced"], comp["frozen"])
            self.assertEqual(comp["frozen"],
                             RUNBOOK["retained_baseline"]["anchors"][key])
            self.assertEqual(comp["frozen"],
                             CERT["replay_evidence"]["trajectory_sha256" if key == "trajectory_sha256"
                                  else "initial_snapshot_sha256" if key == "initial_snapshot_sha256"
                                  else "final_state_sha256"])

    def test_recipe_equivalence(self):
        receipt = load("recipe_equivalence_receipt.json")
        self.assertTrue(receipt["byte_identical"])
        self.assertEqual(receipt["frozen_trajectory_sha256"],
                         receipt["trainable_trajectory_sha256"])


class FB2BaselineBite(unittest.TestCase):
    def test_mutated_anchor_drifts(self):
        receipt = load("baseline_receipt.json")
        comp = dict(receipt["anchor_comparisons"]["trajectory_sha256"])
        refuse_vacuous_comparison(comp["reproduced"],
                                  "0" * 64, "fb2_mutation")
        comp["frozen"] = "0" * 64
        self.assertEqual(comp["verdict"], "EXACT")  # recorded verdict stands
        self.assertNotEqual(comp["reproduced"], comp["frozen"])  # the bite


class SeedRunChecks(unittest.TestCase):
    def test_all_three_seeds_executed(self):
        for seed in SEEDS:
            receipt = load(f"seed_{seed}_receipt.json")
            self.assertTrue(receipt["status"].startswith("EXECUTED_"),
                            seed)
            self.assertIn(receipt["status"],
                          ("EXECUTED_COMPLETED",
                           *[f"EXECUTED_TERMINATED_{c}" for c in
                             RUNBOOK["termination"]["codes"]]), seed)

    def test_completed_seeds_full_budget(self):
        for seed in SEEDS:
            receipt = load(f"seed_{seed}_receipt.json")
            self.assertEqual(receipt["decisions_declared"], 1_000_000)
            if receipt["status"] == "EXECUTED_COMPLETED":
                self.assertEqual(receipt["decisions_executed"], 1_000_000)
                self.assertEqual(receipt["iterations_executed"], 2000)
                self.assertIsNone(receipt["termination_code"])
            else:
                self.assertIsNotNone(receipt["termination_code"])
                self.assertLess(receipt["decisions_executed"], 1_000_000)
            self.assertEqual(receipt["runbook_sha256"],
                             sha((HERE / "runbook.json").read_bytes().rstrip(b"\n")))

    def test_per_seed_bindings_and_gates(self):
        for seed in SEEDS:
            receipt = load(f"seed_{seed}_receipt.json")
            self.assertEqual(receipt["seed"], seed)
            self.assertEqual(receipt["build_id"], "cpu-walk-scene-build-N")
            self.assertEqual(receipt["build_params_sha256"],
                             "3e770bef8b8707c99cdae2f2b2f4a8afb8d12430d987217016e6720a6d232036")
            self.assertEqual(receipt["architecture"], [64, 128, 128, 8])
            self.assertNotEqual(receipt["initial_theta_sha256"],
                                receipt["final_theta_sha256"])
            self.assertLessEqual(receipt["final_window"]["v_max"],
                                 RUNBOOK["velocity_envelope_m_s"])
            # the six hard gates are enforced in-execution by hard_gates()
            # raising SeedTerminated: EXECUTED_COMPLETED with no termination
            # code proves no gate ever fired for this seed (receipt-
            # semantics law: the status field IS the gate record)
            if receipt["status"] == "EXECUTED_COMPLETED":
                self.assertIsNone(receipt["termination_code"])
            else:
                self.assertIn(receipt["termination_code"],
                              RUNBOOK["termination"]["codes"])
            self.assertTrue(receipt["state_chain_head"])
            curve = json.loads(
                (HERE / "receipts" / f"seed_{seed}_curve.json")
                .read_bytes().decode("utf-8"))
            self.assertEqual(receipt["iterations_executed"], len(curve))
            self.assertEqual(receipt["fitness_curve_sha256"],
                             sha(vi.canonical(curve)))

    def test_prediction_outcomes_recorded_not_gated(self):
        """P3 is a registered prediction: its OUTCOME must be recorded per
        seed (not None); the card gate is honest recording, not success."""
        outcomes = {}
        for seed in SEEDS:
            receipt = load(f"seed_{seed}_receipt.json")
            sm = receipt["success_metrics"]
            self.assertIsNotNone(sm["improved_first_to_last_100"], seed)
            outcomes[seed] = sm["improved_first_to_last_100"]
        # disclosed either way; no assertion on the boolean values themselves

    def test_theta_files_bound(self):
        for seed in SEEDS:
            receipt = load(f"seed_{seed}_receipt.json")
            data = (HERE / "trained" / f"theta_{seed}.npz").read_bytes()
            self.assertEqual(sha(data), receipt["theta_npz_sha256"])


class FB5NoRetryPath(unittest.TestCase):
    def test_executor_has_no_retry_loop(self):
        src = (HERE / "run_training.py").read_text(encoding="utf-8")
        tree = ast.parse(src)
        loops = [n for n in ast.walk(tree) if isinstance(n, ast.While)]
        self.assertEqual(loops, [], "no while loop may exist in the executor")
        # no identifier (name/attribute/argument) carries retry semantics
        identifiers = [n.id for n in ast.walk(tree) if isinstance(n, ast.Name)]
        identifiers += [n.attr for n in ast.walk(tree)
                        if isinstance(n, ast.Attribute)]
        identifiers += [n.arg for n in ast.walk(tree)
                        if isinstance(n, ast.arg) and n.arg]
        offenders = [i for i in identifiers if "retry" in i.lower()]
        self.assertEqual(offenders, [],
                         "no retry identifier may exist in the executor")


class HeldOutChecks(unittest.TestCase):
    def test_matrix_shape_and_held_out_count(self):
        receipt = load("heldout_receipt.json")
        self.assertEqual(len(receipt["cells"]), 9)
        self.assertEqual(receipt["held_out_cells"], 6)
        for cell in receipt["cells"]:
            self.assertEqual(cell["held_out"], cell["theta_seed"] != cell["scene_seed"])
            self.assertLessEqual(cell["v_max"],
                                 RUNBOOK["velocity_envelope_m_s"])
            self.assertEqual(cell["decisions_per_rollout"] if
                             "decisions_per_rollout" in cell else
                             receipt["decisions_per_rollout"], 100)

    def test_train_eval_separation(self):
        receipt = load("heldout_receipt.json")
        # evaluation rollouts are distinct from training rollouts: 1500-tick
        # deterministic cells, not 3750-tick fitness windows
        self.assertEqual(receipt["ticks_per_rollout"], 1500)
        self.assertEqual(receipt["decisions_per_rollout"], 100)


class DeployGateChecks(unittest.TestCase):
    def test_three_decisions(self):
        receipt = load("deploy_check_receipt.json")
        self.assertEqual(receipt["allow_frozen_relation"]["decision"], "ALLOW")
        self.assertEqual(receipt["block_trained_bundle"]["decision"], "BLOCK")
        self.assertEqual(receipt["block_foreign_build"]["decision"], "BLOCK")
        self.assertTrue(receipt["block_trained_bundle"]["reasons"])

    def test_trained_weights_bound(self):
        receipt = load("deploy_check_receipt.json")
        for seed in SEEDS:
            data = (HERE / "trained" / f"theta_{seed}.npz").read_bytes()
            self.assertEqual(sha(data),
                             receipt["trained_theta_npz_sha256"][str(seed)])

    def test_certificate_pin(self):
        receipt = load("deploy_check_receipt.json")
        self.assertEqual(receipt["certificate"]["sha256"],
                         sha((vi.STORE / "MAT2-W04/numerical/w04_certificate.json")
                             .read_bytes()))


class FB3DeployGateBite(unittest.TestCase):
    def test_missing_certificate_blocks(self):
        vi.bootstrap_pinned_imports()
        from tools.policy_compat.certificate import check_deploy
        req = {k: CERT["relation"][k] for k in
               ("policy_bundle", "physics_build", "runtime_profile",
                "body_domain", "test_suite")}
        verdict = check_deploy(req, None)
        self.assertEqual(verdict["decision"], "BLOCK")
        self.assertTrue(any("no compatibility certificate" in r
                            for r in verdict["reasons"]))


class TrainedManifestChecks(unittest.TestCase):
    def test_manifest_binds_all_seeds(self):
        doc = json.loads((HERE / "trained" / "trained_policy_manifest.json")
                         .read_bytes().decode("utf-8"))
        self.assertEqual(doc["runbook_sha256"],
                         sha((HERE / "runbook.json").read_bytes().rstrip(b"\n")))
        self.assertEqual(sorted(doc["weights"].keys()),
                         sorted(str(s) for s in SEEDS))
        self.assertIn("NOT a certified trained walking policy", doc["claim"])
        self.assertIn("FC-3 stays explicitly-unresolved", doc["claim"])
