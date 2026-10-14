"""TypeB-P3: assemble + freeze the policy manifest (Astra's missing piece #2).

Builds the complete contract for the dummy actor: weights+architecture+observation
schema+normalization+action mapping+inference clock+reset/state semantics+reflex
version+physics version+CPU runtime+evaluation distribution+receipts. Writes
policy_manifest.json + dummy_actor.npz into the validation dir and prints the
canonical manifest hash.

Usage: python build_policy_manifest.py <validation_dir>
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dummy_actor  # noqa: E402
import observation_schema as oschema  # noqa: E402
import policy_manifest as pman  # noqa: E402

PREREG_SHA = "6ec61b901b2e4754a730dfa6650c01636f9a9582c64439c19c72067fb4717433"
EVAL_SEED = 20260921
SLICE_PASSES = 3   # 302-tick slice x 3 = 906 ticks, truncated to 900
N_DECISIONS = 60   # 900 ticks / hold 15 = exactly 60 decisions (ticks 0,15,...,885)
N_TICKS_CAP = 900  # prereg fixes the fixed sequence at 60 decisions

# action channels: 2 legs x (phase_off, stride_amp, lift_amp, stiff)
_LEG_BOUNDS = {
    "phase_off":  (-0.25, 0.25),   # cycle-fraction phase command
    "stride_amp": (0.2, 1.8),      # multiplier on the banked stride amplitude
    "lift_amp":   (0.2, 1.8),      # multiplier on swing lift amplitude
    "stiff":      (0.5, 2.0),      # multiplier on stance stiffness term
}


def normalization_from_slice(slice_path: str) -> tuple[np.ndarray, np.ndarray, dict]:
    """Per-field mean/std over the ticks where the slice actually delivers the group.

    Fields never available in the record: mean 0, std 1 (declared; the mask carries
    the unavailability). Half-decimated: std floored at 1e-3.
    """
    with open(slice_path, "rb") as f:
        sl = json.loads(f.read().decode("utf-8"))
    recs = sl["ticks"]
    # derive each field's raw value once per tick via the projector's reader
    mean = np.zeros(oschema.OBS_DIM, dtype=np.float64)
    std = np.ones(oschema.OBS_DIM, dtype=np.float64)
    counts = np.zeros(oschema.OBS_DIM, dtype=np.int64)
    sums = np.zeros(oschema.OBS_DIM, dtype=np.float64)
    sqsums = np.zeros(oschema.OBS_DIM, dtype=np.float64)
    zero = np.zeros(oschema.OBS_DIM, dtype=np.float32)
    for rec in recs:
        obs, mask = oschema.project_trace(rec, zero, np.ones_like(zero), {})
        for i in range(oschema.OBS_DIM):
            if mask[i] > 0:
                counts[i] += 1
                sums[i] += float(obs[i])
                sqsums[i] += float(obs[i]) ** 2
    for i in range(oschema.OBS_DIM):
        if counts[i] >= 2:
            mean[i] = sums[i] / counts[i]
            var = max(sqsums[i] / counts[i] - mean[i] ** 2, 0.0)
            std[i] = max(float(np.sqrt(var)), 1e-3)
    meta = {"counts": counts.tolist(), "rule": "mean/std over available ticks of the recorded slice; never-available -> 0/1"}
    return mean.astype(np.float32), std.astype(np.float32), meta


def build(validation_dir: str) -> dict:
    slice_path = os.path.join(validation_dir, "trace_slice_wave38.json")
    with open(slice_path, "rb") as f:
        slice_bytes = f.read()
    slice_sha = hashlib.sha256(slice_bytes).hexdigest()

    params = dummy_actor.export_dummy_actor()
    wb = dummy_actor.weights_bytes(params)
    wsha = hashlib.sha256(wb).hexdigest()
    with open(os.path.join(validation_dir, "dummy_actor.npz"), "wb") as f:
        f.write(wb)

    norm_mean, norm_std, norm_meta = normalization_from_slice(slice_path)
    obs_block = oschema.schema_summary(norm_mean, norm_std)

    names = oschema.FIELD_NAMES
    bounds_lo, bounds_hi, scale, center = [], [], [], []
    channels = []
    for leg in ("left", "right"):
        for ch, (lo, hi) in _LEG_BOUNDS.items():
            bounds_lo.append(lo); bounds_hi.append(hi)
            center.append((lo + hi) / 2.0)
            # half-range scale: |raw|>0.5 saturates the limiter, exercising the
            # intervention indicators even before a real limiter is in the loop
            scale.append((hi - lo) / 4.0)
            channels.append(f"{leg}.{ch}")

    env = pman.build_env()
    import subprocess
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                          cwd=os.path.dirname(os.path.abspath(__file__))).stdout.strip()

    manifest = {
        "manifest_version": pman.MANIFEST_VERSION,
        "kind": "typeb_policy_manifest",
        "claim": {
            "statement": "Frozen-policy CPU export contract (DUMMY weights): the manifest pins every component needed to reproduce the actor's action stream byte-for-byte on the registered CPU runtime, and the batch-one inference fits the 20 Hz decision budget.",
            "grade": "Type-B empirical artifact (weights are seeded dummies, not laws; no behavior claim)",
        },
        "named_falsifiers": ["F-CPU-POLICY-BYTES", "F-INFERENCE-BUDGET"],
        "cpu_reference": {
            "commit": head,
            "branch": "agent/typeb-p3-export-20260921",
            "record_set_digest": slice_sha,
            "record_set_path": "tools/science_funnel/validation/typeb_p3_20260921/trace_slice_wave38.json",
            "build_env": env,
        },
        "horizon_and_ticks": {
            "physics_hz": 300, "policy_hz": 20, "hold_ticks": 15,
            "tick_convention": "1 physics tick = 1/300 s; 1 decision per 15 ticks, zero-order held",
            "walk_horizon_ticks_recorded": 302,
        },
        "scene_and_receipts": {
            "baseline_scene": "banked wave-38 gait walk (commit 30821ef7, refused_tick=295, worst_ledger_J=30.219924)",
            "original_letters": "wave-38 ship letters on the parent build (calendar-arithmetic waive scope guard)",
            "receipts_dir": "tools/science_funnel/validation/typeb_p3_20260921/",
            "prereg_sha256": PREREG_SHA,
        },
        "body": {
            "status": "UNBOUND_dummy",
            "digest": None,
            "note": "mesh/topology/material/mass/actuator digests bind when a trained actor freezes; this manifest pins the CONTRACT",
        },
        "reflex_set": {
            "version": "wave38-banked-reflex/1.0.0",
            "option_definitions": "none (single skill; no option transitions in the dummy)",
            "frozen_within_training_run": True,
        },
        "physics_version": {
            "name": "chimera-cpu-engine", "version": "wave38",
            "digest": None, "status": "UNBOUND_dummy",
        },
        "observation": obs_block,
        "normalization": {
            "mean": norm_mean.tolist(), "std": norm_std.tolist(), "clip": 8.0,
            "recipe": oschema.schema_summary.__doc__ and "x = clip((x - mean)/std, -clip, +clip); unavailable -> mean-filled (0.0 in normalized space)",
            "derived_from": norm_meta,
            "digest": hashlib.sha256(canonical := json.dumps(
                {"mean": norm_mean.tolist(), "std": norm_std.tolist(), "clip": 8.0},
                sort_keys=True).encode()).hexdigest(),
        },
        "action": {
            "dim": 8,
            "channels": channels,
            "units": ["cycle_frac", "mult", "mult", "mult"] * 2,
            "frames": ["walk_interface"] * 8,
            "raw_activation": "tanh",
            "mapping": "applied = clip(center + scale * raw, lo, hi) -- the command limiter; requested==applied except where clipped",
            "bounds_lo": bounds_lo, "bounds_hi": bounds_hi,
            "scale": scale, "center": center,
            "authority_note": "commands enter ONLY through the walk interface; the policy has no authority over body state, anatomy, gravity, root pose, monitors or physics",
            "clock": {"policy_hz": 20, "physics_hz": 300, "hold_ticks": 15},
            "hold_semantics": "zero-order hold; decision iff physics_tick % 15 == 0; applied commands persist otherwise",
        },
        "policy": {
            "architecture": list(dummy_actor.ARCHITECTURE),
            "activation": dummy_actor.ACTIVATION,
            "weights_format": "npz/float32/c-contiguous",
            "weights_sha256": wsha,
            "weights_path": "tools/science_funnel/validation/typeb_p3_20260921/dummy_actor.npz",
            "param_count": dummy_actor.param_count(),
            "mac_count": dummy_actor.mac_count(),
            "seed": dummy_actor.SEED,
            "training_backend": "NONE (fixed-seed dummy; GPU training is a later, separately registered candidate)",
            "immutable_candidate": True,
        },
        "inference": {
            "runtime": "pure-numpy/1.0.0 (batch one)",
            "compute_dtype": "float32",
            "recipe": [
                "project trace record -> x[64] via observation_schema.project_trace",
                "x = clip((x - mean)/std, -8, +8)",
                "h1 = tanh(x @ W0 + b0); h2 = tanh(h1 @ W1 + b1); a = tanh(h2 @ W2 + b2)",
                "applied = clip(center + scale*a, lo, hi)",
                "decision iff tick % 15 == 0, else hold previous applied",
            ],
            "deterministic": True,
            "engine_option_note": "the engine may reimplement the same pinned recipe (float32 arrays, tanh, one matvec per layer); re-run F-CPU-POLICY-BYTES against any new implementation before deployment",
        },
        "reset": {
            "semantics": "neutral commands (center), phase 0, ticks_since_intervention = large, clock tick 0 is a decision tick",
            "initial_obs": "mean-fill everywhere (normalized zeros) until the first tick's projection",
            "phase0": 0.0,
            "reset_distribution": "single banked reset (wave-38 settle transient excluded from judgement per F-Gfore note)",
        },
        "evaluation": {
            "fixed_obs_sequence": {
                "source": "trace_slice_wave38.json",
                "sha256": slice_sha,
                "passes": SLICE_PASSES,
                "n_ticks": N_TICKS_CAP,
                "n_ticks_uncapped": 302 * SLICE_PASSES,
                "n_decisions": N_DECISIONS,
                "tick_source": "slice tick (t mod 302), truncated to the first 900 ticks",
            },
            "distribution": "single recorded slice; dev/sealed split arrives with a trained actor",
            "sealed": False,
            "seed": EVAL_SEED,
        },
        "receipts": {
            "prereg": "tools/science_funnel/validation/typeb_p3_20260921/prereg.json",
            "prereg_sha256": PREREG_SHA,
            "falsifier_drivers": ["run_f_cpu_policy_bytes.py", "run_f_inference_budget.py"],
        },
    }
    manifest["manifest_hash"] = pman.manifest_hash(manifest)

    errs = pman.validate_manifest(manifest, wb)
    if errs:
        raise SystemExit("manifest INVALID: " + "; ".join(errs))
    with open(os.path.join(validation_dir, "policy_manifest.json"), "wb") as f:
        f.write(json.dumps(manifest, indent=1, sort_keys=True).encode("utf-8"))
    print("manifest_hash:", manifest["manifest_hash"])
    print("weights_sha256:", wsha, f"({len(wb)} bytes)")
    print("param_count:", manifest["policy"]["param_count"],
          "mac_count:", manifest["policy"]["mac_count"])
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else
          os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "validation", "typeb_p3_20260921"))
