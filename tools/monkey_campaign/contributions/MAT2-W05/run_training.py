#!/usr/bin/env python3
"""MAT2-W05: execute the frozen walk1m-r1 runbook (prereg section 2).

Phases (all CPU, BQ-1; sequential single-process; no retry path exists):
  A  retained-baseline arm: the frozen P3 policy closed loop (build N, seed
     20260920, 900 ticks) through the UNMODIFIED pinned runner; anchors must
     reproduce the W04 certificate replay evidence EXACTLY (refusal
     `baseline_drift` otherwise).
  B  recipe-equivalence proof: the trainable policy class, loaded with the
     FROZEN bundle weights, must reproduce the frozen NumpyPolicy applied
     bytes tick-for-tick on the baseline rollout (refusal
     `recipe_equivalence_failed`).
  C  per-seed training: SPSA, 2000 iterations x 2 antithetic evaluations x
     250 decisions = 1,000,000 decisions = 15,000,000 ticks per seed, seeds
     [20260919, 20260920, 20260921]; hard gates at every tick; termination
     codes declared; failures RETAINED (receipt records EXECUTED_TERMINATED_
     <code> and stops that seed only; the partial curve is preserved).
  D  held-out: 3x3 deterministic evaluation matrix (100 decisions per cell).
  E  certificate mismatch rejection: the frozen deploy gate BLOCKs the
     trained tuple, ALLOWs the certificate's own relation, BLOCKs a foreign
     build (refusal `deploy_gate_failed`).

Large artifacts (per-iteration thetas, raw curves beyond the receipt) stay in
the attempt scratch; receipts + trained weights land in the card dir.

Run:  python -B run_training.py
Exit: 0 all phases recorded / 2 named refusal.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
import verify_inputs as vi

RUNBOOK_SHA = vi.sha_bytes((HERE / "runbook.json").read_bytes().rstrip(b"\n"))
RB = json.loads((HERE / "runbook.json").read_bytes().decode("utf-8"))

SEEDS = RB["seeds"]["values"]
ITERATIONS = RB["decisions"]["iterations"]
DECISIONS_PER_EVAL = RB["decisions"]["decisions_per_evaluation"]
SPSA_C = RB["trainer"]["perturbation"]["size_c"]
SPSA_A = RB["trainer"]["step"]["a_s"]
SPSA_EPS = RB["trainer"]["step"]["eps"]
RNG_SEED_BASE = 700000000
ANCHOR_STRIDE = RB["state_chain"]["anchor_stride_ticks"]
WALL_BUDGET_S = RB["termination"]["wall_clock_budget_s"]
HELDOUT_TICKS = RB["held_out"]["ticks_per_rollout"]
PARAM_DIM = RB["trainer"]["parameter_vector"]["dim"]

TRAIN_DIR = HERE / "trained"
RECEIPT_DIR = HERE / "receipts"
THETA_DIR = vi.SCRATCH / "thetas"

CERT_PATH = vi.STORE / "MAT2-W04/numerical/w04_certificate.json"
CERT = json.loads(CERT_PATH.read_bytes().decode("utf-8"))
BASELINE_ANCHORS = RB["retained_baseline"]["anchors"]
BASELINE_HORIZON = 900

# set in main() before any rollout (the frozen manifest blocks)
MEAN = STD = LO = HI = SCALE = CENTER = None
DECLARED_GROUPS = None
PROJECT = None


class SeedTerminated(Exception):
    def __init__(self, code: str, detail: str):
        super().__init__(code + ": " + detail)
        self.code = code
        self.detail = detail


# ------------------------------------------------------------- the policy
def theta_to_weights(theta: np.ndarray):
    """Split the flat float64 vector per the frozen architecture
    [64,128,128,8] (W0,b0,W1,b1,W2,b2), float32 contiguous for the recipe."""
    t = np.asarray(theta, dtype=np.float64)
    assert t.shape == (PARAM_DIM,)
    blocks = []
    i = 0
    for shape in ((64, 128), (128,), (128, 128), (128,), (128, 8), (8,)):
        n = int(np.prod(shape))
        blocks.append(t[i:i + n].reshape(shape))
        i += n
    W = [np.ascontiguousarray(b.astype(np.float32)) for b in (blocks[0], blocks[2], blocks[4])]
    b = [np.ascontiguousarray(bb.astype(np.float32)) for bb in (blocks[1], blocks[3], blocks[5])]
    return W, b


def weights_to_theta(bundle) -> np.ndarray:
    """Flatten the FROZEN bundle weights into the trainable vector (Phase B),
    in the trainable layout order W0,b0,W1,b1,W2,b2."""
    params = bundle["params"]
    order = [("W0", (64, 128)), ("b0", (128,)), ("W1", (128, 128)),
             ("b1", (128,)), ("W2", (128, 8)), ("b2", (8,))]
    parts = [np.asarray(params[key], dtype=np.float64).reshape(shape)
             for key, shape in order]
    return np.concatenate([p.ravel() for p in parts])


class TrainablePolicy:
    """The frozen inference recipe with a trainable float64 parameter vector.

    Structure, dtypes, clock and bookkeeping are the frozen NumpyPolicy
    recipe (pinned infer_numpy): projection on DECISION ticks only;
    x = clip((obs-mean)/std, -8, +8) float32; h = tanh(x@W+b) float32;
    applied = clip(center + scale*a, lo, hi) float32; zero-order hold
    otherwise. Phase B proves byte equivalence on the frozen weights."""

    def __init__(self, theta: np.ndarray):
        self.mean = MEAN
        self.std = STD
        self.lo = LO
        self.hi = HI
        self.scale = SCALE
        self.center = CENTER
        self.set_theta(theta)
        self.reset()

    def set_theta(self, theta: np.ndarray) -> None:
        self.W, self.b = theta_to_weights(theta)
        self.theta_sha = vi.sha_bytes(
            np.asarray(theta, dtype=np.float64).astype("<f8").tobytes())

    def reset(self) -> None:
        self.clock_tick = 0
        self.decisions = 0
        self.prev_applied = self.center.copy()
        self.prev_sat = np.zeros(8, dtype=np.float32)
        self.ticks_since_intervention = 10 ** 6
        self.ticks_since_reset = 0
        self._prev_yaw_rate = 0.0

    def _forward(self, x: np.ndarray) -> np.ndarray:
        h = x
        for W, b in zip(self.W, self.b):
            h = h @ W + b
            h = np.tanh(h, out=h) if h.dtype == np.float32 else np.tanh(h)
            h = h.astype(np.float32, copy=False)
        return h

    def act(self, rec: dict) -> np.ndarray:
        deciding = self.clock_tick % 15 == 0
        # the frozen NumpyPolicy bookkeeping, line for line: the record the
        # projector sees carries the same controller fields
        rec = dict(rec)
        rec.setdefault("available_groups", None)
        rec["is_decision_tick"] = deciding
        rec.setdefault("hold_tick", self.clock_tick % 15)
        rec.setdefault("ticks_since_reset", self.ticks_since_reset)
        reason = rec.get("intervention_reason", "none")
        if reason != "none":
            self.ticks_since_intervention = 0
        rec["ticks_since_intervention"] = min(self.ticks_since_intervention,
                                              3000)
        if deciding:
            x, _mask = PROJECT(rec, self.mean, self.std,
                               {"yaw_rate": self._prev_yaw_rate})
            a = self._forward(x)
            raw = self.center + self.scale * a
            applied = np.clip(raw, self.lo, self.hi).astype(np.float32)
            self.prev_sat = (np.abs(applied - raw) > 0).astype(np.float32)
            self.decisions += 1
            self.prev_applied = applied
        applied = self.prev_applied
        self.ticks_since_intervention += 1
        self.ticks_since_reset += 1
        self._prev_yaw_rate = float(rec.get("yaw_rate", 0.0) or 0.0)
        self.clock_tick += 1
        return applied


# ------------------------------------------------------------- execution
def hard_gates(scene, rec, applied, v_env) -> None:
    """The six hard gates (prereg 2 A.2); any breach raises SeedTerminated."""
    sv = scene.state_vector()
    for q in sv:
        if not np.isfinite(q):
            raise SeedTerminated("numerical_failure", repr(sv))
    if abs(scene.v) > v_env:
        raise SeedTerminated("envelope_breach", repr(scene.v))
    if any(not (LO[k] - 1e-6 <= float(applied[k]) <= HI[k] + 1e-6)
           for k in range(8)):
        raise SeedTerminated("bounds_breach", repr([float(a) for a in applied]))
    if int(rec["contact_count"]) < 2:
        raise SeedTerminated("contact_floor_breach", repr(rec["contact_count"]))
    if set(rec["available_groups"]) != set(DECLARED_GROUPS):
        raise SeedTerminated("availability_breach", repr(rec["available_groups"]))
    if rec["intervention_reason"] != "none":
        raise SeedTerminated("intervention_observed",
                             repr(rec["intervention_reason"]))


def evaluate(policy: TrainablePolicy, scene, horizon: int,
             collect: bool = False) -> dict:
    """One deterministic closed-loop rollout of the frozen runbook loop."""
    scene.begin([float(c) for c in CENTER])
    policy.reset()
    chain = vi.sha_bytes(b"initial")
    initial_snapshot_sha = vi.sha_bytes(vi.canonical({
        "seed": scene.seed, "build_id": scene.build_id,
        "params_sha256": scene.params_sha(), "v": repr(scene.v),
        "x": repr(scene.x), "phase_l": repr(scene.phase_l),
        "phase_r": repr(scene.phase_r)}))
    total_r = 0.0
    v_max = 0.0
    n_sat = 0
    x_before = scene.x
    decisions_here = 0
    anchors = 0
    records = [] if collect else None
    v_digest = hashlib.sha256()
    for t in range(horizon):
        rec = scene.observation_record()
        if collect:
            records.append(json.loads(json.dumps(rec)))
        if t % 15 == 0:
            x_before = scene.x
        applied = policy.act(rec)
        scene.step(applied, policy.prev_sat)
        v_digest.update(np.asarray([scene.v], dtype="<f8").tobytes())
        v_max = max(v_max, abs(scene.v))
        n_sat += int(np.any(policy.prev_sat > 0))
        if (t + 1) % 15 == 0:
            total_r += scene.x - x_before
            decisions_here += 1
        if (t + 1) % ANCHOR_STRIDE == 0 or t == horizon - 1:
            ssha = scene.state_sha256()
            chain = vi.sha_bytes(f"{chain}:{t}:state:{ssha}".encode("utf-8"))
            anchors += 1
        hard_gates(scene, rec, applied, RB["velocity_envelope_m_s"])
    return {"fitness": total_r, "chain_head": chain, "anchors": anchors,
            "initial_snapshot_sha256": initial_snapshot_sha,
            "final_state_sha256": scene.state_sha256(),
            "v_max": v_max, "saturation_frac": n_sat / float(horizon),
            "decisions": decisions_here,
            "mean_speed_m_s": scene.x / (horizon / 300.0),
            "total_dx_m": scene.x,
            "v_series_sha256": v_digest.hexdigest(),
            "records": records}


def fitness(scene, theta: np.ndarray) -> float:
    return evaluate(TrainablePolicy(theta), scene,
                    DECISIONS_PER_EVAL * 15)["fitness"]


def spsa_iterate(seed: int, theta: np.ndarray, scene) -> tuple:
    """The frozen trainer loop (prereg 2G). No retry path; partial curves
    are preserved on termination."""
    rng = np.random.Generator(np.random.PCG64(RNG_SEED_BASE + seed))
    chain = vi.sha_bytes(f"runbook:{RUNBOOK_SHA}:seed:{seed}".encode("utf-8"))
    curve = []
    try:
        for k in range(ITERATIONS):
            delta = (rng.integers(0, 2, size=theta.shape[0], dtype=np.int8)
                     * 2 - 1).astype(np.float64)
            f_plus = fitness(scene, theta + SPSA_C * delta)
            f_minus = fitness(scene, theta - SPSA_C * delta)
            ghat = ((f_plus - f_minus) / (2.0 * SPSA_C)) * delta
            theta = theta - SPSA_A * ghat / (SPSA_EPS + float(np.mean(np.abs(ghat))))
            curve.append([f_plus, f_minus])
            chain = vi.sha_bytes(
                f"{chain}:it{k}:{vi.sha_bytes(theta.astype('<f8').tobytes())}:"
                f"{float(f_plus).hex()}:{float(f_minus).hex()}".encode("utf-8"))
            if (k + 1) % 100 == 0:
                print(f"  seed {seed} iteration {k + 1}/{ITERATIONS} "
                      f"fit+ {f_plus:.6f} fit- {f_minus:.6f}", flush=True)
            if (k + 1) * 500 > RB["decisions"]["per_seed_total"]:
                break
    except SeedTerminated:
        raise
    return theta, chain, curve


def fresh_scene(scene_cpu, build_id, params, seed: int):
    return lambda: scene_cpu.make_scene(build_id, params, seed)


def main() -> int:
    t0 = time.time()
    vi.verify()
    reg = vi.verify_registry()
    vi.extract_pinned_tree()
    vi.bootstrap_pinned_imports()
    from tools.policy_compat import runner as gate_runner  # pinned bytes
    from tools.policy_compat import scene_cpu              # pinned bytes
    global MEAN, STD, LO, HI, SCALE, CENTER, DECLARED_GROUPS, PROJECT
    from observation_schema import project_trace           # pinned bytes
    PROJECT = project_trace

    bundle = gate_runner.load_bundle()
    manifest = bundle["manifest"]
    MEAN = np.asarray(manifest["normalization"]["mean"], dtype=np.float32)
    STD = np.asarray(manifest["normalization"]["std"], dtype=np.float32)
    act = manifest["action"]
    LO = np.asarray(act["bounds_lo"], dtype=np.float32)
    HI = np.asarray(act["bounds_hi"], dtype=np.float32)
    SCALE = np.asarray(act["scale"], dtype=np.float32)
    CENTER = np.asarray(act["center"], dtype=np.float32)
    DECLARED_GROUPS = list(scene_cpu.AVAILABLE_GROUPS)
    v_env = scene_cpu.derived_envelope()["velocity_envelope_m_s"]
    if abs(v_env - RB["velocity_envelope_m_s"]) > 1e-12:
        print("REFUSAL: envelope_derivation_mismatch", file=sys.stderr)
        return 2
    build_id, params = scene_cpu.build_n()
    if scene_cpu.params_sha(params) != RB["environment"]["build_params_sha256"]:
        print("REFUSAL: input_pin_mismatch:build_params", file=sys.stderr)
        return 2
    scenes = {seed: fresh_scene(scene_cpu, build_id, params, seed)
              for seed in set(SEEDS) | {20260920}}

    RECEIPT_DIR.mkdir(parents=True, exist_ok=True)

    # ---- Phase A: retained baseline --------------------------------------
    t_a = time.time()
    base = gate_runner.run_closed_loop(bundle, build_id, params, 20260920,
                                       BASELINE_HORIZON)
    got = {
        "trajectory_sha256": vi.sha_bytes(base["traj_bytes"]),
        "initial_snapshot_sha256": base["initial_snapshot_sha256"],
        "final_state_sha256": base["final_state_sha256"],
    }
    comparisons = {}
    for key, frozen in BASELINE_ANCHORS.items():
        ok = got[key] == frozen
        comparisons[key] = {"frozen": frozen, "reproduced": got[key],
                            "verdict": "EXACT" if ok else "DRIFT"}
        if not ok:
            print("REFUSAL: baseline_drift:" + key, file=sys.stderr)
            return 2
    baseline_receipt = {
        "schema": "chimera.w05_baseline.v1",
        "task_id": "W05", "card_id": "MAT2-W05",
        "attempt_id": vi.ATTEMPT_ID,
        "preregistration_sha256": vi.prereg_sha256(),
        "preregistration_addendum_1_sha256": vi.addendum_sha256(),
        "runbook_sha256": RUNBOOK_SHA,
        "arm": "retained baseline: frozen P3 policy closed loop, build N, "
               "seed 20260920, 900 ticks, UNMODIFIED pinned runner",
        "build_id": build_id,
        "events": len(base["events"]),
        "anchor_comparisons": comparisons,
        "registry": reg,
        "measured_resources": {"wall_s": round(time.time() - t_a, 1)},
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B run_training.py"},
    }
    (RECEIPT_DIR / "baseline_receipt.json").write_bytes(
        vi.canonical(baseline_receipt) + b"\n")
    print("Phase A baseline: anchors EXACT")

    # ---- Phase B: recipe equivalence on the FROZEN weights ----------------
    t_b = time.time()
    frozen_theta = weights_to_theta(bundle)
    frozen_res = gate_runner.run_closed_loop(bundle, build_id, params,
                                             20260920, BASELINE_HORIZON)
    scene_b = scenes[20260920]()
    scene_b.begin([float(c) for c in CENTER])
    tr_policy = TrainablePolicy(frozen_theta)
    traj = bytearray()
    for _t in range(BASELINE_HORIZON):
        rec = scene_b.observation_record()
        applied = tr_policy.act(rec)
        scene_b.step(applied, tr_policy.prev_sat)
        traj += np.asarray(applied, dtype="<f4").tobytes()
    equiv = vi.sha_bytes(bytes(traj)) == vi.sha_bytes(frozen_res["traj_bytes"])
    if not equiv:
        print("REFUSAL: recipe_equivalence_failed", file=sys.stderr)
        return 2
    (RECEIPT_DIR / "recipe_equivalence_receipt.json").write_bytes(
        vi.canonical({
            "schema": "chimera.w05_recipe_equivalence.v1",
            "task_id": "W05", "card_id": "MAT2-W05",
            "preregistration_sha256": vi.prereg_sha256(),
            "preregistration_addendum_1_sha256": vi.addendum_sha256(),
            "runbook_sha256": RUNBOOK_SHA,
            "claim": ("the trainable policy class with the FROZEN bundle "
                      "weights reproduces the frozen NumpyPolicy applied "
                      "bytes tick-for-tick over the 900-tick baseline "
                      "rollout (same projection width, dtypes, limiter, "
                      "clock, bookkeeping)"),
            "frozen_trajectory_sha256": vi.sha_bytes(frozen_res["traj_bytes"]),
            "trainable_trajectory_sha256": vi.sha_bytes(bytes(traj)),
            "byte_identical": equiv,
            "measured_resources": {"wall_s": round(time.time() - t_b, 1)},
            "determinism": {"canonical_json": True, "newline": "\n",
                            "command": "python -B run_training.py"},
        }) + b"\n")
    print("Phase B recipe equivalence: applied bytes IDENTICAL")

    # ---- Phase C: the three seed runs (failures retained) -----------------
    THETA_DIR.mkdir(parents=True, exist_ok=True)
    TRAIN_DIR.mkdir(parents=True, exist_ok=True)
    for seed in SEEDS:
        t_s = time.time()
        theta = np.zeros(PARAM_DIM, dtype=np.float64)
        initial_theta_sha = vi.sha_bytes(theta.astype("<f8").tobytes())
        try:
            theta, chain, curve = spsa_iterate(seed, theta, scenes[seed]())
            status = "EXECUTED_COMPLETED"
            term_code = None
            term_detail = None
        except SeedTerminated as term:
            status = "EXECUTED_TERMINATED_" + term.code
            term_code = term.code
            term_detail = term.detail
            chain = vi.sha_bytes(f"{RUNBOOK_SHA}:terminated:{term.code}"
                                 .encode("utf-8"))
        final_theta_sha = vi.sha_bytes(theta.astype("<f8").tobytes())
        np.savez(THETA_DIR / f"theta_{seed}.npz", theta=theta)
        np.savez(TRAIN_DIR / f"theta_{seed}.npz", theta=theta)
        final_eval = evaluate(TrainablePolicy(theta), scenes[seed](),
                              DECISIONS_PER_EVAL * 15)
        decisions_executed = len(curve) * 2 * DECISIONS_PER_EVAL
        first100 = float(np.mean([f for f, _ in curve[:100]])) if curve else None
        last100 = float(np.mean([f for f, _ in curve[-100:]])) if curve else None
        receipt = {
            "schema": "chimera.w05_seed_run.v1",
            "task_id": "W05", "card_id": "MAT2-W05",
            "attempt_id": vi.ATTEMPT_ID,
            "preregistration_sha256": vi.prereg_sha256(),
            "preregistration_addendum_1_sha256": vi.addendum_sha256(),
            "runbook_id": RB["runbook_id"],
            "runbook_sha256": RUNBOOK_SHA,
            "seed": seed,
            "status": status,
            "termination_code": term_code,
            "termination_detail": term_detail,
            "decisions_declared": RB["decisions"]["per_seed_total"],
            "decisions_executed": decisions_executed,
            "ticks_executed": decisions_executed * 15,
            "iterations_executed": len(curve),
            "initial_theta_sha256": initial_theta_sha,
            "final_theta_sha256": final_theta_sha,
            "theta_npz_sha256": vi.sha_bytes(
                (TRAIN_DIR / f"theta_{seed}.npz").read_bytes()),
            "state_chain_head": chain,
            "final_window": {k: final_eval[k] for k in
                             ("fitness", "chain_head", "anchors",
                              "final_state_sha256", "v_max",
                              "saturation_frac", "decisions",
                              "mean_speed_m_s", "total_dx_m",
                              "v_series_sha256")},
            "velocity_envelope_m_s": v_env,
            "success_metrics": {
                "mean_iteration_fitness_first100": first100,
                "mean_iteration_fitness_last100": last100,
                "improved_first_to_last_100": (None if first100 is None
                                               else bool(last100 > first100)),
            },
            "fitness_curve_sha256": vi.sha_bytes(vi.canonical(curve)),
            "build_id": build_id,
            "scene_version": scene_cpu.SCENE_VERSION,
            "build_params_sha256": scene_cpu.params_sha(params),
            "architecture": RB["trainer"]["parameter_vector"]["architecture"],
            "registry": reg,
            "measured_resources": {"wall_s": round(time.time() - t_s, 1)},
            "determinism": {"canonical_json": True, "newline": "\n",
                            "command": "python -B run_training.py"},
        }
        (RECEIPT_DIR / f"seed_{seed}_receipt.json").write_bytes(
            vi.canonical(receipt) + b"\n")
        (RECEIPT_DIR / f"seed_{seed}_curve.json").write_bytes(
            vi.canonical(curve) + b"\n")
        print(f"Phase C seed {seed}: {status} ({decisions_executed} "
              f"decisions; fit {first100} -> {last100})", flush=True)

    # ---- Phase D: held-out 3x3 -------------------------------------------
    t_d = time.time()
    cells = []
    for seed in SEEDS:
        theta = np.load(TRAIN_DIR / f"theta_{seed}.npz")["theta"]
        for env_seed in SEEDS:
            pol = TrainablePolicy(theta)
            ev = evaluate(pol, scenes[env_seed](), HELDOUT_TICKS)
            cells.append({"theta_seed": seed, "scene_seed": env_seed,
                          "held_out": seed != env_seed,
                          "fitness": ev["fitness"],
                          "total_dx_m": ev["total_dx_m"],
                          "mean_speed_m_s": ev["mean_speed_m_s"],
                          "v_max": ev["v_max"],
                          "saturation_frac": ev["saturation_frac"],
                          "final_state_sha256": ev["final_state_sha256"],
                          "v_series_sha256": ev["v_series_sha256"]})
    (RECEIPT_DIR / "heldout_receipt.json").write_bytes(
        vi.canonical({
            "schema": "chimera.w05_heldout.v1",
            "task_id": "W05", "card_id": "MAT2-W05",
            "preregistration_sha256": vi.prereg_sha256(),
            "preregistration_addendum_1_sha256": vi.addendum_sha256(),
            "runbook_sha256": RUNBOOK_SHA,
            "ticks_per_rollout": HELDOUT_TICKS,
            "decisions_per_rollout": HELDOUT_TICKS // 15,
            "cells": cells,
            "held_out_cells": sum(1 for c in cells if c["held_out"]),
            "determinism": {"canonical_json": True, "newline": "\n",
                            "command": "python -B run_training.py"},
            "measured_resources": {"wall_s": round(time.time() - t_d, 1)},
        }) + b"\n")
    print("Phase D held-out: 9 cells recorded")

    # ---- Phase E: certificate mismatch rejection --------------------------
    from tools.policy_compat.certificate import check_deploy  # pinned bytes
    relation = CERT["relation"]
    keys = ("policy_bundle", "physics_build", "runtime_profile",
            "body_domain", "test_suite")
    req_frozen = {k: relation[k] for k in keys}
    allow = check_deploy(req_frozen, CERT)
    trained_theta_npz_sha = {
        seed: vi.sha_bytes((TRAIN_DIR / f"theta_{seed}.npz").read_bytes())
        for seed in SEEDS}
    trained_identity = vi.sha_bytes(vi.canonical({
        "trained_by": "MAT2-W05 walk1m-r1", "seeds": SEEDS,
        "weights": trained_theta_npz_sha}))
    trained_bundle = dict(req_frozen["policy_bundle"])
    trained_bundle.update({
        "manifest_hash": trained_identity,
        "weights_sha256": vi.sha_bytes(vi.canonical(trained_theta_npz_sha)),
        "manifest_file_sha256": trained_identity,
        "weights_file_sha256": vi.sha_bytes(vi.canonical(trained_theta_npz_sha)),
        "loader": "MAT2-W05 trained theta npz (float64; per-seed)",
    })
    req_trained = dict(req_frozen)
    req_trained["policy_bundle"] = trained_bundle
    block_trained = check_deploy(req_trained, CERT)
    req_foreign = json.loads(json.dumps(req_frozen))
    req_foreign["physics_build"] = dict(req_frozen["physics_build"])
    req_foreign["physics_build"]["build_id"] = "cpu-walk-scene-build-N+1"
    block_foreign = check_deploy(req_foreign, CERT)
    if not (allow["decision"] == "ALLOW"
            and block_trained["decision"] == "BLOCK"
            and block_foreign["decision"] == "BLOCK"):
        print("REFUSAL: deploy_gate_failed", file=sys.stderr)
        return 2
    (RECEIPT_DIR / "deploy_check_receipt.json").write_bytes(
        vi.canonical({
            "schema": "chimera.w05_deploy_check.v1",
            "task_id": "W05", "card_id": "MAT2-W05",
            "preregistration_sha256": vi.prereg_sha256(),
            "preregistration_addendum_1_sha256": vi.addendum_sha256(),
            "certificate": {"path": str(CERT_PATH).replace("\\", "/"),
                            "sha256": vi.sha_bytes(CERT_PATH.read_bytes())},
            "allow_frozen_relation": allow,
            "block_trained_bundle": {"decision": block_trained["decision"],
                                     "reasons": block_trained["reasons"]},
            "block_foreign_build": {"decision": block_foreign["decision"],
                                    "reasons": block_foreign["reasons"]},
            "trained_theta_npz_sha256": trained_theta_npz_sha,
            "determinism": {"canonical_json": True, "newline": "\n",
                            "command": "python -B run_training.py"},
        }) + b"\n")
    print("Phase E deploy gate: ALLOW(frozen)/BLOCK(trained)/BLOCK(foreign)")

    # ---- the trained-policy export manifest (W06's input) ------------------
    seed_recs = {seed: json.loads(
        (RECEIPT_DIR / f"seed_{seed}_receipt.json").read_bytes()
        .decode("utf-8")) for seed in SEEDS}
    (TRAIN_DIR / "trained_policy_manifest.json").write_bytes(
        vi.canonical({
            "schema": "chimera.w05_trained_policy_manifest.v1",
            "runbook_id": RB["runbook_id"],
            "runbook_sha256": RUNBOOK_SHA,
            "preregistration_sha256": vi.prereg_sha256(),
            "preregistration_addendum_1_sha256": vi.addendum_sha256(),
            "architecture": RB["trainer"]["parameter_vector"]["architecture"],
            "activation": RB["trainer"]["parameter_vector"]["activation"],
            "normalization": {
                "mean_source": "frozen P3 manifest normalization (64)",
                "manifest_hash": RB["observations"]["manifest_hash"],
                "clip": RB["trainer"]["parameter_vector"]["normalization_clip"]},
            "action_block_source": ("frozen P3 manifest action block "
                                    "(center/scale/bounds/clock)"),
            "clock": {"policy_hz": 20, "physics_hz": 300, "hold_ticks": 15},
            "weights": {str(seed): {
                "file": f"theta_{seed}.npz",
                "sha256": trained_theta_npz_sha[seed],
                "theta_sha256": seed_recs[seed]["final_theta_sha256"],
                "status": seed_recs[seed]["status"],
                "decisions_executed": seed_recs[seed]["decisions_executed"]}
                for seed in SEEDS},
            "inference_recipe": ("project_trace (v1 width 64, frozen P3 "
                                 "normalization) -> x = clip((x-mean)/std, "
                                 "-8, 8) -> tanh MLP [64,128,128,8] float32 "
                                 "-> applied = clip(center + scale*a, lo, "
                                 "hi); decision iff tick % 15 == 0"),
            "claim": ("training candidates + per-seed receipts for W06 "
                      "evaluation; NOT a certified trained walking policy "
                      "(FC-3 stays explicitly-unresolved; binds only by "
                      "reissuance through the TC-6 gate)"),
            "determinism": {"canonical_json": True, "newline": "\n",
                            "command": "python -B run_training.py"},
        }) + b"\n")

    print("runbook executed; total wall", round(time.time() - t0, 1), "s")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except vi.Refusal as exc:
        print("REFUSAL: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
