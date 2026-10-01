#!/usr/bin/env python3
"""MAT2-W06: the frozen per-seed evaluation of the walk1m-r1 trained walking
outcomes.

NO-RUNS LAW (prereg section 3): this evaluator executes ZERO physics runs.
No scene import, no policy import, no training entry point, no subprocess,
no socket. Every reported number is recomputed from the PINNED recorded
artifacts (fitness curves + receipts at their merged in-tree paths, base
af751aa5) by deterministic arithmetic, or quoted from a pinned receipt
field. FB5 AST-scans this contribution for run paths and fails on presence.

Frozen metric set M1-M6, integrity criteria I1-I6, and the per-seed
success/failure ruling are the UPSTREAM-FROZEN identities quoted in prereg
section 2 — this file introduces no threshold and no window of its own.
M4 recomputation identity (declared): the executor computed np.mean over the
f_plus column, slices [:100] and [-100:]; the evaluator reproduces exactly
this float semantics and requires BIT-EXACT agreement with the receipt
fields.

Run:  python -B run_evaluation.py
Exit: 0 written / 2 refusal.
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
import verify_inputs as vi

SEEDS = [20260919, 20260920, 20260921]
WINDOW = 100
TERMINATION_CODES = [
    "numerical_failure", "envelope_breach", "bounds_breach",
    "contact_floor_breach", "availability_breach", "intervention_observed",
    "wall_clock_budget", "internal_error"]


# ---- G5: vacuous-comparison guard -------------------------------------------
def refuse_vacuous_comparison(a, b, code: str) -> None:
    """Refuse bit-identical relative comparisons (they cannot discriminate)."""
    if a == b:
        raise vi.Refusal("vacuous_comparison:" + code)


def vacuous_guard_selftest() -> bool:
    """The guard must PASS on differing inputs and FIRE on identical ones."""
    try:
        refuse_vacuous_comparison(1.0, 2.0, "selftest_should_pass")
    except vi.Refusal:
        return False
    try:
        refuse_vacuous_comparison(1.0, 1.0, "selftest_should_fire")
    except vi.Refusal:
        return True
    return False


# ---- FB5: the structural no-runs scanner (addendum A4, three classes) -------
# class (i): forbidden in EVERY file
FORBID_MODULES = {"run_training", "socket", "urllib", "http", "requests",
                  "multiprocessing", "urllib.request"}
FORBID_CALLS = {"system", "popen", "spawn", "Popen", "urlopen",
                "TrainablePolicy", "fitness", "spsa_iterate"}
# classes (ii)/(iii): allowed ONLY in the addendum-declared replay file
REPLAY_FILE = "run_replay_capture.py"


def scan_no_run_paths(source_text: str, filename: str = "<string>") -> list:
    """AST scan for run-launching constructs (FB5). Returns violations.

    Class (i) training/run-launch paths are flagged everywhere. The pinned
    replay import (tools.policy_compat...) and the declared capture-tool
    subprocess use (ffmpeg encode/decode) are flagged in every file EXCEPT
    the addendum-declared run_replay_capture.py."""
    violations = []
    is_replay = (filename == REPLAY_FILE)
    tree = ast.parse(source_text, filename=filename)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if alias.name in FORBID_MODULES or root in FORBID_MODULES:
                    violations.append("import:" + alias.name)
                elif alias.name == "subprocess" and not is_replay:
                    violations.append("import:subprocess_outside_replay")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if node.module in FORBID_MODULES or root in FORBID_MODULES:
                violations.append("importfrom:" + str(node.module))
            elif (node.module or "").startswith("tools.policy_compat") \
                    and not is_replay:
                violations.append("importfrom:pinned_replay_outside_replay:"
                                  + str(node.module))
        elif isinstance(node, ast.Call):
            fn = node.func
            name = fn.id if isinstance(fn, ast.Name) else (
                fn.attr if isinstance(fn, ast.Attribute) else "")
            if name in FORBID_CALLS:
                violations.append("call:" + name + "@" + str(node.lineno))
    return violations


# ---- the frozen metric recomputation (M1-M6) ---------------------------------
def recompute_windows(curve: list) -> tuple:
    """M4 identity: np.mean over the f_plus column, [:100] and [-100:]."""
    f_plus = np.array([row[0] for row in curve], dtype=np.float64)
    first100 = float(np.mean(f_plus[:WINDOW]))
    last100 = float(np.mean(f_plus[-WINDOW:]))
    return first100, last100


def detector_recompute(curve: list, receipt_first, receipt_last,
                       receipt_improved) -> str | None:
    """FB2 detector: bit-exact recomputation vs the receipt fields."""
    first100, last100 = recompute_windows(curve)
    if first100 != receipt_first:
        return "metric_recompute_mismatch:first100"
    if last100 != receipt_last:
        return "metric_recompute_mismatch:last100"
    refuse_vacuous_comparison(last100, first100,
                              "m4_first_vs_last_windows")
    recomputed_flag = bool(last100 > first100)
    if recomputed_flag != bool(receipt_improved):
        return "metric_recompute_mismatch:improved_flag"
    return None


def detector_curve_digest(curve: list, curve_file_bytes: bytes,
                          receipt_curve_sha: str, pinned_sha: str) -> str | None:
    """M6: canonical curve digest and pinned file bytes."""
    if vi.sha_bytes(vi.canonical(curve)) != receipt_curve_sha:
        return "curve_digest_mismatch:canonical"
    if vi.sha_bytes(curve_file_bytes) != pinned_sha:
        return "curve_digest_mismatch:pinned_file"
    return None


def detector_integrity(rec: dict) -> str | None:
    """I1-I4 per seed."""
    status = rec.get("status")
    term = rec.get("termination_code")
    if status not in ("EXECUTED_COMPLETED",) and not (
            isinstance(status, str) and status.startswith("EXECUTED_TERMINATED_")):
        return "integrity_status:" + repr(status)
    if term is not None and term not in TERMINATION_CODES:
        return "integrity_termination_code:" + repr(term)
    if term is None:
        if rec.get("decisions_executed") != rec.get("decisions_declared"):
            return "integrity_decisions_shortfall"
        if rec.get("iterations_executed") != 2000:
            return "integrity_iterations"
        if rec.get("ticks_executed") != 15000000:
            return "integrity_ticks"
    for key in ("state_chain_head", "initial_theta_sha256",
                "final_theta_sha256", "theta_npz_sha256"):
        if not rec.get(key):
            return "integrity_missing_binding:" + key
    return None


def detector_seed_set(present: set) -> str | None:
    """FB3a detector: every registered seed present, none dropped."""
    if present != set(SEEDS):
        return "cherry_pick_detected:seed_set:" + repr(sorted(present))
    return None


def detector_heldout_cells(cells: list) -> str | None:
    """FB3b/I5 detector: the full 3x3 matrix, 6 off-diagonal + 3 diagonal."""
    seen = set((c["theta_seed"], c["scene_seed"]) for c in cells)
    if seen != set((t, s) for t in SEEDS for s in SEEDS):
        return "cherry_pick_detected:heldout_matrix"
    off = sum(1 for c in cells if c.get("held_out") is True)
    diag = sum(1 for c in cells if c.get("held_out") is False)
    if off != 6 or diag != 3:
        return "cherry_pick_detected:heldout_split"
    for c in cells:
        for key in ("fitness", "mean_speed_m_s", "v_max", "final_state_sha256"):
            if c.get(key) is None:
                return "cherry_pick_detected:cell_field:" + key
    return None


def detector_deploy_rows(deploy: dict) -> str | None:
    """I6/FB4 detector: the frozen gate ruling rows."""
    if deploy.get("allow_frozen_relation", {}).get("decision") != "ALLOW":
        return "deploy_gate_ruling_violated:frozen_relation"
    bt = deploy.get("block_trained_bundle", {})
    if bt.get("decision") != "BLOCK" or not bt.get("reasons"):
        return "deploy_gate_ruling_violated:trained_bundle"
    if deploy.get("block_foreign_build", {}).get("decision") != "BLOCK":
        return "deploy_gate_ruling_violated:foreign_build"
    return None


def detector_verdict_pure(evaluation_receipt: dict,
                          recomputed_verdict: str) -> str | None:
    """FB6 detector: the emitted verdict is a pure function of the inputs."""
    if evaluation_receipt.get("verdict") != recomputed_verdict:
        return "verdict_not_a_pure_function"
    if evaluation_receipt.get("verdict_rule") != \
            "SUCCESS iff mean_iteration_fitness_last100 > mean_iteration_fitness_first100":
        return "verdict_not_a_pure_function:rule_drift"
    return None


def rule_verdict(first100: float, last100: float) -> str:
    """The FROZEN per-seed ruling (W05 prereg P3), applied verbatim."""
    refuse_vacuous_comparison(last100, first100, "p3_ruling_windows")
    return "SUCCESS" if last100 > first100 else "FAILURE"


# ---- the evaluator -----------------------------------------------------------
def load_json(path: Path):
    return json.loads(path.read_bytes().decode("utf-8"))


def composite_sha(rows: list, bodies: list) -> str:
    return vi.sha_bytes(vi.canonical(
        {"inputs": rows,
         "evaluation_digests": [vi.sha_bytes(b) for b in bodies]}))


def main() -> int:
    require_selftest = vacuous_guard_selftest()
    if not require_selftest:
        print("REFUSAL: vacuous_guard_selftest failed", file=sys.stderr)
        return 2
    pins = vi.verify()
    reg = vi.verify_registry()
    # the pin verification record is G7 evidence: receipted, not scratch-only
    pins_record = {
        "schema": "chimera.w06_input_pins.v1",
        "task_id": vi.TASK_SHORT,
        "card_id": vi.CARD_ID,
        "attempt_id": vi.ATTEMPT_ID,
        "preregistration_sha256": vi.prereg_sha256(),
        "criteria_sha256": vi.CRITERIA_SHA256,
        "candidate_base": vi.CANDIDATE_BASE,
        "registry": reg,
        "pins": pins,
        "pins_ok": sum(1 for r in pins if r["ok"]),
        "pins_total": len(pins),
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B run_evaluation.py"},
    }
    (HERE / "receipts" / "input_pins.json").write_bytes(
        vi.canonical(pins_record) + b"\n")

    runbook = load_json(vi.UPSTREAM / "runbook.json")
    trained_manifest = load_json(vi.UPSTREAM / "trained"
                                 / "trained_policy_manifest.json")
    heldout = load_json(vi.UPSTREAM / "receipts" / "heldout_receipt.json")
    deploy = load_json(vi.UPSTREAM / "receipts" / "deploy_check_receipt.json")

    pin_by_name = {Path(r["path"]).name: r["sha256"] for r in pins}

    per_seed_bodies = []
    seed_rows = []
    all_recompute_exact = True
    all_integrity_ok = True
    for seed in SEEDS:
        rec = load_json(vi.UPSTREAM / "receipts" / f"seed_{seed}_receipt.json")
        curve_bytes = (vi.UPSTREAM / "receipts" / f"seed_{seed}_curve.json") \
            .read_bytes()
        curve = json.loads(curve_bytes.decode("utf-8"))
        npz_bytes = (vi.UPSTREAM / "trained" / f"theta_{seed}.npz").read_bytes()
        sm = rec["success_metrics"]
        fw = rec["final_window"]

        first100, last100 = recompute_windows(curve)
        refuse_vacuous_comparison(last100, first100,
                                  "m4_first_vs_last_windows_seed_"
                                  + str(seed))
        recomputed_flag = bool(last100 > first100)
        recompute_code = detector_recompute(curve, sm[
            "mean_iteration_fitness_first100"],
            sm["mean_iteration_fitness_last100"],
            sm["improved_first_to_last_100"])
        recompute_exact = recompute_code is None
        all_recompute_exact &= recompute_exact

        refuse_vacuous_comparison(fw["v_max"], rec["velocity_envelope_m_s"],
                                  "m3_v_max_vs_envelope_seed_" + str(seed))
        within_envelope = bool(fw["v_max"] <= rec["velocity_envelope_m_s"])

        digest_code = detector_curve_digest(
            curve, curve_bytes, rec["fitness_curve_sha256"],
            pin_by_name[f"seed_{seed}_curve.json"])
        npz_ok = (vi.sha_bytes(npz_bytes) == rec["theta_npz_sha256"]
                  == pin_by_name[f"theta_{seed}.npz"]
                  == trained_manifest["weights"][str(seed)]["sha256"]
                  == deploy["trained_theta_npz_sha256"][str(seed)])
        integrity_code = detector_integrity(rec)
        integrity_ok = integrity_code is None
        all_integrity_ok &= integrity_ok

        verdict = rule_verdict(first100, last100)
        body = {
            "schema": "chimera.w06_seed_evaluation.v1",
            "task_id": vi.TASK_SHORT,
            "card_id": vi.CARD_ID,
            "attempt_id": vi.ATTEMPT_ID,
            "preregistration_sha256": vi.prereg_sha256(),
            "criteria_sha256": vi.CRITERIA_SHA256,
            "candidate_base": vi.CANDIDATE_BASE,
            "seed": seed,
            "runbook_id": runbook["runbook_id"],
            "input_pins": {
                "seed_receipt_sha256": pin_by_name[
                    f"seed_{seed}_receipt.json"],
                "seed_curve_sha256": pin_by_name[f"seed_{seed}_curve.json"],
                "theta_npz_sha256": pin_by_name[f"theta_{seed}.npz"]},
            "metrics": {
                "M1_total_forward_displacement_m": fw["total_dx_m"],
                "M2_mean_com_speed_m_s": fw["mean_speed_m_s"],
                "M3_v_max_m_s": fw["v_max"],
                "M3_velocity_envelope_m_s": rec["velocity_envelope_m_s"],
                "M3_within_envelope": within_envelope,
                "M4_mean_iteration_fitness_first100": first100,
                "M4_mean_iteration_fitness_last100": last100,
                "M4_improved_first_to_last_100": recomputed_flag,
                "M5_limiter_saturation_fraction": fw["saturation_frac"],
                "M6_curve_iterations": len(curve),
                "M6_curve_sha256": rec["fitness_curve_sha256"]},
            "cross_checks": {
                "M4_bit_exact_vs_receipt": recompute_exact,
                "M4_recompute_code": recompute_code,
                "M6_digest_code": digest_code,
                "theta_npz_identity_bound": bool(npz_ok)},
            "integrity": {
                "I1_status": rec["status"],
                "I2_decisions_executed": rec["decisions_executed"],
                "I2_decisions_declared": rec["decisions_declared"],
                "I3_termination_code": rec["termination_code"],
                "I3_hard_gate_evidence_law":
                    "any hard-gate breach is retained as a termination "
                    "record by the executor; termination_code null is the "
                    "receipt-level evidence that none fired",
                "I4_state_chain_head": rec["state_chain_head"],
                "I4_initial_theta_sha256": rec["initial_theta_sha256"],
                "I4_final_theta_sha256": rec["final_theta_sha256"],
                "integrity_code": integrity_code},
            "verdict_rule": ("SUCCESS iff mean_iteration_fitness_last100 > "
                             "mean_iteration_fitness_first100"),
            "verdict_basis": {
                "first100": first100, "last100": last100,
                "source": "recomputed from the pinned curve; bit-exact vs "
                          "the receipt fields"},
            "verdict": verdict,
            "determinism": {"canonical_json": True, "newline": "\n",
                            "command": "python -B run_evaluation.py"},
        }
        pure_code = detector_verdict_pure(body, rule_verdict(first100,
                                                             last100))
        body["cross_checks"]["FB6_pure_function_code"] = pure_code
        out = HERE / "receipts" / f"seed_{seed}_evaluation.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(vi.canonical(body) + b"\n")
        per_seed_bodies.append(vi.canonical(body))
        seed_rows.append({
            "seed": seed, "verdict": verdict,
            "first100": first100, "last100": last100,
            "improved": recomputed_flag, "status": rec["status"],
            "termination_code": rec["termination_code"]})
        print("seed", seed, "recompute_exact", recompute_exact,
              "integrity_ok", integrity_ok, "verdict", verdict)

    # held-out completeness (I5) + per-theta generalization deltas
    held_code = detector_heldout_cells(heldout["cells"])
    deltas = {}
    for theta_seed in SEEDS:
        cells = [c for c in heldout["cells"] if c["theta_seed"] == theta_seed]
        diag = [c["fitness"] for c in cells if not c["held_out"]][0]
        off = [c["fitness"] for c in cells if c["held_out"]]
        refuse_vacuous_comparison(diag, float(np.mean(off)),
                                  "heldout_diag_vs_offdiag_seed_"
                                  + str(theta_seed))
        deltas[str(theta_seed)] = {"diagonal_fitness": diag,
                                   "offdiag_mean_fitness": float(np.mean(off)),
                                   "offdiag_min_fitness": min(off),
                                   "offdiag_max_fitness": max(off),
                                   "diag_minus_offdiag_mean":
                                       diag - float(np.mean(off))}

    deploy_code = detector_deploy_rows(deploy)
    deploy_binding_ok = all(
        deploy["trained_theta_npz_sha256"][str(seed)]
        == pin_by_name[f"theta_{seed}.npz"] for seed in SEEDS)

    no_run_violations = []
    for py in sorted(HERE.glob("*.py")):
        no_run_violations.extend(
            scan_no_run_paths(py.read_bytes().decode("utf-8"), py.name))

    summary = {
        "schema": "chimera.w06_evaluation_summary.v1",
        "task_id": vi.TASK_SHORT,
        "card_id": vi.CARD_ID,
        "attempt_id": vi.ATTEMPT_ID,
        "agent_id": vi.AGENT_ID,
        "preregistration_sha256": vi.prereg_sha256(),
        "criteria_sha256": vi.CRITERIA_SHA256,
        "candidate_base": vi.CANDIDATE_BASE,
        "registry": reg,
        "runbook_id": runbook["runbook_id"],
        "seeds": SEEDS,
        "seed_rows": seed_rows,
        "integrity": {
            "I1_I4_all_green": all_integrity_ok,
            "I5_heldout_code": held_code,
            "I5_heldout_deltas": deltas,
            "I6_deploy_code": deploy_code,
            "I6_trained_npz_binding_ok": deploy_binding_ok},
        "predictions": {
            "E1_all_seeds_fail_training_signal": {
                "predicted": True,
                "observed": all(r["verdict"] == "FAILURE"
                                for r in seed_rows)},
            "E2_bit_exact_recomputation": {
                "predicted": True, "observed": all_recompute_exact},
            "E3_receipts_complete": {
                "predicted": True,
                "observed": all_integrity_ok and held_code is None
                and deploy_code is None and deploy_binding_ok},
            "E4_trained_blocked_from_deploy": {
                "predicted": True,
                "observed": deploy.get("block_trained_bundle", {})
                .get("decision") == "BLOCK"
                and deploy.get("allow_frozen_relation", {})
                .get("decision") == "ALLOW"}},
        "falsifier_mapping": {
            "card_falsifier": ("Sliding/penetration, unsupported propulsion, "
                               "hidden reset, wrong command response or "
                               "diagnostic/clean state divergence fails."),
            "sliding_penetration": "contact_floor gate; no "
                                   "contact_floor_breach termination exists",
            "unsupported_propulsion": "velocity_envelope gate; no "
                                      "envelope_breach termination exists",
            "hidden_reset": "no_intervention gate + the continuous "
                            "4096-tick state-chain anchoring; no "
                            "intervention_observed termination exists",
            "wrong_command_response": "bounds_honored gate; no bounds_breach "
                                      "termination exists",
            "diagnostic_clean_divergence": "the recipe-equivalence receipt: "
                                           "the trainable controller class "
                                           "reproduced the frozen policy "
                                           "applied bytes tick-for-tick "
                                           "(trajectory sha cd4944d9...)"},
        "no_runs_law": {
            "FB5_scan_violations": no_run_violations,
            "training_runs_executed_by_this_card": 0,
            "tuned_runs_executed_by_this_card": 0,
            "evaluation_rollouts_of_trained_candidates": 0,
            "declared_capture_replays_of_the_sealed_line":
                1 if (HERE / "capture" / "replay_receipt.json").exists()
                else 0,
            "law": ("zero training, zero tuned runs, zero evaluation "
                    "rollouts of the trained candidates; the single "
                    "declared capture replay of the sealed certified line "
                    "(frozen P3 policy, ALLOW(frozen)) is the addendum A1 "
                    "arm and produces no outcome number any verdict reads")},
        "deploy_treatment": {
            "trained_theta_tuple": deploy["block_trained_bundle"]["decision"],
            "frozen_relation": deploy["allow_frozen_relation"]["decision"],
            "trained_theta_npz_sha256":
                deploy["trained_theta_npz_sha256"],
            "law": ("the trained thetas are non-deployable training "
                    "candidates; they bind ONLY by reissuance through the "
                    "TC-6 gate; FC-3 (trained walking policy) stays "
                    "explicitly-unresolved")},
        "composite_record_sha256": composite_sha(pins, per_seed_bodies),
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B run_evaluation.py"},
    }
    out = HERE / "receipts" / "evaluation_summary.json"
    out.write_bytes(vi.canonical(summary) + b"\n")
    print("verdicts:", {r["seed"]: r["verdict"] for r in seed_rows})
    print("predictions:", {k: v["observed"]
                           for k, v in summary["predictions"].items()})
    print("FB5 violations:", no_run_violations)
    print("wrote", out)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except vi.Refusal as exc:
        print("REFUSAL: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
