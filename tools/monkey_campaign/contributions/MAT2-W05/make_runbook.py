#!/usr/bin/env python3
"""MAT2-W05: generate the FROZEN runbook document + the TC-10 slot fill.

`runbook.json` is the ~1M-decision walking runbook (schema
chimera.w05_runbook.v1). Every constant below is copied from the prereg
(section 2) — the prereg is the single source; this generator must never
invent a value. `w05_freeze_fill.json` fills the three W04-owned nulls of the
sealed freeze manifest's `seeds_runbook_slot` (TC-10 / FC-4 / LT ruling
BQ-3): runbook_id, seeds, acceptance_criteria.

Run:  python -B make_runbook.py
Exit: 0 written / 2 refusal (prereg drift).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import verify_inputs as vi

HERE = Path(__file__).resolve().parent

RUNBOOK_ID = "walk1m-r1"
SEEDS = [20260919, 20260920, 20260921]

# --- frozen trainer constants (prereg 2G; declared, not tuned) -----------
ITERATIONS = 2000
EVALS_PER_ITER = 2
DECISIONS_PER_EVAL = 250
HOLD_TICKS = 15
PHYSICS_HZ = 300
POLICY_HZ = 20
TICKS_PER_EVAL = DECISIONS_PER_EVAL * HOLD_TICKS          # 3750
DECISIONS_TOTAL = ITERATIONS * EVALS_PER_ITER * DECISIONS_PER_EVAL  # 1,000,000
TICKS_TOTAL = DECISIONS_TOTAL * HOLD_TICKS                # 15,000,000
SPSA_C = 0.05            # perturbation size
SPSA_A = 0.01            # L1-mean-normalized step (mean |weight step| per iter)
SPSA_EPS = 1e-12         # normalizer floor
RNG_SEED_BASE = 700000000
PARAM_DIM = 25864        # 64*128+128 + 128*128+128 + 128*8+8
ARCHITECTURE = [64, 128, 128, 8]
ACTIVATION = "tanh"
NORMALIZATION_CLIP = 8.0
WALL_CLOCK_BUDGET_S = 5400
MEMORY_BOUND_BYTES = 1_000_000_000
HELDOUT_TICKS = 1500     # 100 decisions per held-out rollout (declared)
HELDOUT_MATRIX = "3x3 (each seed's final theta on each seed's scene); off-diagonal = held-out"
ANCHOR_STRIDE = 4096     # state-hash chain anchor stride (ticks)

BUILD_N_ID = "cpu-walk-scene-build-N"
BUILD_N_PARAMS_SHA = "3e770bef8b8707c99cdae2f2b2f4a8afb8d12430d987217016e6720a6d232036"
SCENE_VERSION = "cpu-walk-scene/1.0.0"
VELOCITY_ENVELOPE_M_S = 2.977443609022557   # derived: a_max/d_lo (recomputed by the executor)
SUITE_ID = "upgrade_gate_20260920/registered_cases_v1"
SUITE_CASES_SHA = "d6fa74bd89d14f2e49b4d196a974e00f7a19d167e516122e790f5b564937dea7"

MANIFEST_FILE_SHA = "aa5334f797b50c2ac3950cec5b82b439f982c1090dd66827754a1acbb8a26b6f"
MANIFEST_HASH = "9ca7e976dfb0dedd3f56dfa404673ee77c00801acb2753cdfd83604c480c35b7"
WEIGHTS_FILE_SHA = "5fb2b7857d872fccc0bb89d6733582647da04d11d636e84c266912ce9c027f0f"

TERMINATION_CODES = ["numerical_failure", "envelope_breach", "bounds_breach",
                     "contact_floor_breach", "availability_breach",
                     "intervention_observed", "wall_clock_budget",
                     "internal_error"]

HARD_GATES = [
    "no_nan_inf: no NaN/Inf in any recorded state quantity, every tick",
    "velocity_envelope: |v_t| <= 2.977443609022557 m/s (derived a_max/d_lo), every tick",
    "bounds_honored: every applied command within the manifest limiter bounds, every tick",
    "contact_floor: contact_count >= 2, every tick",
    "availability_exact: available_groups exactly the declared set, every tick",
    "no_intervention: intervention_reason == 'none', every tick",
]

REWARD = ("per decision r = x_after - x_before (com forward displacement in "
          "meters over the 15 hold ticks); evaluation-window fitness J(theta) "
          "= summed reward over one deterministic 3750-tick rollout from the "
          "declared entry state")


def acceptance_criteria() -> dict:
    """The K01 acceptance value filling the W04 slot (prereg section 2)."""
    return {
        "execution_integrity_gates": HARD_GATES,
        "per_seed_receipt_law": ("every seed carries a canonical per-seed "
                                 "receipt binding prereg, addendum, runbook "
                                 "sha, seed, scene/build identity, initial "
                                 "and final theta sha, decisions and ticks "
                                 "executed, termination code, state-hash "
                                 "chain anchors, iteration fitness curve "
                                 "digest; a claimed pass unsupported by "
                                 "these records fails"),
        "failure_retention": ("failures RETAINED: a seed that terminates is "
                              "recorded EXECUTED_TERMINATED_<code> with its "
                              "partial curve; the executor contains no "
                              "retry path; failures are never silently "
                              "retried away"),
        "termination_codes": TERMINATION_CODES,
        "held_out_checks": HELDOUT_MATRIX,
        "certificate_mismatch_rejection": ("the frozen deploy gate must BLOCK "
                                           "the trained bundle tuple against "
                                           "the sealed W04 certificate with "
                                           "the mismatch named, and ALLOW "
                                           "the certificate's own relation "
                                           "(gate-closes positive control)"),
        "success_metrics_reported_not_gated": [
            "total forward displacement (m) per seed",
            "mean com speed (m/s) per seed",
            "max |v| vs envelope per seed",
            "mean decision reward (m/decision), first vs last 100 iterations",
            "limiter saturation fraction per seed",
            "full fitness curve (2000 x (f_plus, f_minus)) per seed",
        ],
        "falsifier": ("Missing identities or a claimed pass unsupported by "
                      "records fails; a screenshot is not a substitute."),
        "profile": "records (offline); numerical evidence required; no camera record",
    }


def runbook_document() -> dict:
    return {
        "schema": "chimera.w05_runbook.v1",
        "runbook_id": RUNBOOK_ID,
        "title": "the frozen approximately 1M-decision walking runbook "
                 "(MAT2-W05; fills the W04 TC-10 slot values)",
        "preregistration_sha256": vi.prereg_sha256(),
        "preregistration_addendum_1_sha256": vi.addendum_sha256(),
        "criteria_sha256": vi.CRITERIA_SHA256,
        "candidate_base": vi.CANDIDATE_BASE,
        "seeds": {"values": SEEDS,
                  "identity": ("the three registered closed-loop corpus "
                               "seeds of " + SUITE_ID),
                  "suite_registered_cases_sha256": SUITE_CASES_SHA},
        "decisions": {"per_seed_total": DECISIONS_TOTAL,
                      "per_iteration": EVALS_PER_ITER * DECISIONS_PER_EVAL,
                      "iterations": ITERATIONS,
                      "evaluations_per_iteration": EVALS_PER_ITER,
                      "decisions_per_evaluation": DECISIONS_PER_EVAL,
                      "hold_ticks": HOLD_TICKS,
                      "physics_hz": PHYSICS_HZ, "policy_hz": POLICY_HZ,
                      "ticks_per_seed_total": TICKS_TOTAL},
        "observations": {
            "per_tick": "scene telemetry record (WalkScene.observation_record)",
            "per_decision": ("the frozen projection at the certificate "
                             "replay width: project_trace with the frozen P3 "
                             "manifest normalization (64), clip 8.0; v2 "
                             "interface (80 fields; FIELDS[:64] the frozen "
                             "v1 width); privileged_forbidden"),
            "manifest_file_sha256": MANIFEST_FILE_SHA,
            "manifest_hash": MANIFEST_HASH,
        },
        "actions": {
            "channels": 8,
            "limiter": "applied = clip(center + scale*a, lo, hi); the frozen manifest block",
            "clock_law": "decision iff tick % 15 == 0 else zero-order hold",
            "authority": ("commands enter ONLY through the walk interface; "
                          "no pose-writing, no teleport, no force outside "
                          "the capped channels"),
        },
        "reward": REWARD,
        "trainer": {
            "method": "SPSA (simultaneous perturbation stochastic approximation)",
            "parameter_vector": {"dim": PARAM_DIM, "dtype": "float64",
                                 "architecture": ARCHITECTURE,
                                 "activation": ACTIVATION,
                                 "normalization_clip": NORMALIZATION_CLIP},
            "init": ("theta0 = 0 (all weights and biases zero; the zero "
                     "policy outputs a = tanh(0) = 0, applied = the manifest "
                     "center — the certified entry law); the frozen P3 "
                     "weights are NOT used as init (reusability verdict: "
                     "NOT REUSABLE as-is)"),
            "perturbation": {"law": "Rademacher {+-1}^25864, iid",
                             "stream": "PCG64, seed 700000000 + run seed",
                             "size_c": SPSA_C},
            "gradient_estimate": "g_hat = ((J+ - J-) / (2c)) * delta",
            "step": {"rule": "theta <- theta - a_s * g_hat / (1e-12 + mean|g_hat|)",
                     "a_s": SPSA_A, "eps": SPSA_EPS,
                     "property": ("scale-free by construction: the mean "
                                  "absolute weight step per iteration is "
                                  "exactly a_s; no unit tuning exists")},
            "exploration_noise": "NONE anywhere in this runbook (deterministic rollouts)",
        },
        "environment": {
            "backend": "the certified CPU walk backend ONLY (LT ruling BQ-1)",
            "build_id": BUILD_N_ID,
            "scene_version": SCENE_VERSION,
            "build_params_sha256": BUILD_N_PARAMS_SHA,
            "entry_law": ("entry from rest at the manifest center commands; "
                          "the seed selects the entry phase residue "
                          "(half-cycle L/R offset); one PCG64 micro-terrain "
                          "draw per tick"),
            "gpu": ("NO GPU work exists in this lane (BQ-1); the GPU-03/"
                    "GPU-05 catalog refs are determined NOT-APPLICABLE to "
                    "this card's runs; the GPU mailbox is unused"),
        },
        "termination": {"codes": TERMINATION_CODES,
                        "wall_clock_budget_s": WALL_CLOCK_BUDGET_S,
                        "retry": "NONE: no retry path exists in the executor"},
        "bounded_resources": {
            "per_seed_wall_s": WALL_CLOCK_BUDGET_S,
            "resident_memory_bytes": MEMORY_BOUND_BYTES,
            "process_model": "sequential single-process CPU runs",
            "trajectory_retention": ("NONE: streaming chain hashing only; "
                                     "trajectory bytes never stored"),
            "p04_reservation_record": ("prereg commits separately BEFORE any "
                                       "run; bounds frozen in prereg section "
                                       "2 I; no GPU mailbox job (BQ-1); the "
                                       "P04 handoff gate governs GPU training "
                                       "launches on the live controller and "
                                       "no live controller session is "
                                       "provisioned to this attempt — the "
                                       "CPU-first bounded envelope is the "
                                       "operative admission of record; the "
                                       "limitation is named, not skipped"),
        },
        "retained_baseline": {
            "arm": ("the sealed certified reference line re-executed through "
                    "the UNMODIFIED pinned machinery: frozen P3 policy "
                    "closed-loop, build N, seed 20260920, 900 ticks"),
            "anchors": {
                "trajectory_sha256": "cd4944d99be1270951926be53859828a6b0aef21d32d6551f68e78d504ef6c7a",
                "initial_snapshot_sha256": "11ac68cfb2c237445902b65bd1ee3bd228d915e1009d01d1cd16a3e5aab13346",
                "final_state_sha256": "b9a7fb99c32013e2e993c8c81a88b0abea2d5e0ce19e010e344b5d4e8cb27d72",
            },
            "source": "the W04 certificate replay evidence (cert_hash 4b306f4f...)",
        },
        "explicit_controller_changes": [
            "the actor's weights become the trainable theta (zero-init; the frozen P3 bundle is never loaded as actor during training)",
            "the SPSA optimizer exists only between rollouts; the control loop remains the certified per-tick closed loop",
            "projection runs on DECISION ticks only (the frozen recipe's decision law consumes no hold-tick projection; proven byte-identical on the frozen corpus)",
        ],
        "held_out": {"ticks_per_rollout": HELDOUT_TICKS,
                     "decisions_per_rollout": HELDOUT_TICKS // HOLD_TICKS,
                     "matrix": HELDOUT_MATRIX,
                     "noise": "deterministic (no training, no exploration)"},
        "state_chain": {"anchor_stride_ticks": ANCHOR_STRIDE,
                        "law": ("chain = sha256(chain:tick:state:state_sha) "
                                "every ANCHOR_STRIDE ticks + final anchor; "
                                "per-iteration chain over theta sha + fitness")},
        "governing_laws": {
            "K01": "Observations, actions, reward, termination, success metrics, seeds, envelope and falsifiers approved before training",
            "P04": "APPROVED reservations before any training run; preregistration commits separately",
            "C10": "use the frozen runbook; separate train/evaluation cases; bind all dynamics-relevant state; per-seed receipts; certificate mismatch rejection; held-out checks",
        },
        "velocity_envelope_m_s": VELOCITY_ENVELOPE_M_S,
        "velocity_envelope_derivation": ("a_max = STRIDE_GAIN*stride_amp_hi "
                                         "= 0.99; d_lo = DAMPING*WARM_DAMP_LO "
                                         "= 0.3325; V = a_max/d_lo (recomputed "
                                         "from the pinned scene at run time)"),
    }


def main() -> int:
    vi.verify()
    vi.verify_registry()
    rb = runbook_document()
    rb_bytes = vi.canonical(rb)
    runbook_sha = vi.sha_bytes(rb_bytes)
    (HERE / "runbook.json").write_bytes(rb_bytes + b"\n")

    freeze = json.loads(
        (vi.STORE / "MAT2-W04/numerical/w04_freeze_manifest.json")
        .read_bytes().decode("utf-8"))
    slot = freeze["seeds_runbook_slot"]
    if slot["declared_fields"]["runbook_id"]["value"] is not None or \
            slot["declared_fields"]["seeds"]["value"] is not None or \
            slot["declared_fields"]["acceptance_criteria"]["value"] is not None:
        print("REFUSAL: slot_not_null_before_fill", file=sys.stderr)
        return 2

    fill = {
        "schema": "chimera.w05_tc10_slot_fill.v1",
        "clause": "TC-10 / FC-4 / LT ruling BQ-3",
        "card_id": "MAT2-W05",
        "task_id": "W05",
        "preregistration_sha256": vi.prereg_sha256(),
        "preregistration_addendum_1_sha256": vi.addendum_sha256(),
        "parent_freeze": {
            "path": "E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-W04/numerical/w04_freeze_manifest.json",
            "sha256": vi.sha_bytes(
                (vi.STORE / "MAT2-W04/numerical/w04_freeze_manifest.json").read_bytes()),
            "slot_status_before": slot["slot_status"],
            "declared_fields_before": {k: v["value"]
                                       for k, v in slot["declared_fields"].items()},
            "governing_laws": slot["governing_laws"],
        },
        "fill": {
            "runbook_id": RUNBOOK_ID,
            "seeds": SEEDS,
            "acceptance_criteria": acceptance_criteria(),
        },
        "runbook_document": {
            "path": "tools/monkey_campaign/contributions/MAT2-W05/runbook.json",
            "sha256": runbook_sha,
        },
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B make_runbook.py"},
    }
    (HERE / "w05_freeze_fill.json").write_bytes(
        vi.canonical(fill) + b"\n")
    print("runbook.json sha256:", runbook_sha)
    print("w05_freeze_fill.json written (slot filled)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except vi.Refusal as exc:
        print("REFUSAL: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
