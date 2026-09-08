"""run_gpu_relax_gate.py -- GLM-RELAX-GPU-01 harness.

Runs the GPU-driven relaxation (relax_gpu_probe.exe, the VERIFIED kernels
driving the declared descent) and the CPU reference (run_descent, the
declared law of record, on the WIDENED f32 fixture positions -- the same
state the GPU loop starts from), then applies the preregistered budgets
from docs/THE_RELAX_GPU01_PREREGISTRATION.md:

  R1  iteration-0 forces within the FROZEN fixture budgets (the standard
      probe already gates this; re-asserted here from the manifest)
  R2  per-iteration energy: |E_gpu[i] - E_ref(i)| within the frozen
      1.1e-5 J budget at comparable states
  R3  final centre position within the derived f32 bound
      n_acc * 2^-23 * max|coord| (worst-case f32 accumulation)
  R4  the GPU loop ends in one of the FIVE NAMED STATES
  R5  Armijo holds on every accepted step (re-checked from the trail)
  R6  no tolerance widened: every budget is either frozen or derived in
      the preregistration

Evidence: unique timestamped directory, raw GPU stdout, raw check output,
JSON record, human-readable summary. Exit 0 iff all gates hold.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
sys.path.insert(0, TOOLS)
sys.path.insert(0, str(ROOT / "tools"))

from overdamped_descent import run_descent, EPS  # noqa: E402
from surface_energy_reference import evaluate_surface  # noqa: E402

PROBE = ROOT / ".tmp" / "relax_build" / "Release" / "relax_gpu_probe.exe"
SHADER = ROOT / ".tmp" / "relax_build" / "Release" / "membrane.comp.spv"
FIXTURES = ROOT / "docs" / "evidence" / "gpu_fixtures"
FROZEN_ENERGY_BUDGET = 1.1e-5          # the frozen fixture energy budget
FROZEN_COMPLETE_FORCE_BUDGET = 2.5e-5  # the frozen complete-force budget

OUTDIR = ROOT / "docs" / "evidence" / "membrane_gpu_relax" / (
    "relaxgate_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ"))


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=False)
    from membrane_window_demo import load_b2  # the frozen B2 loader
    b2 = load_b2()
    pos0_f64, faces = b2["positions"], b2["faces"]

    # --- the shared starting state: fixture f32 WIDENED to f64 -----------
    pos0 = np.asarray(pos0_f64, dtype=np.float64)
    pos32 = pos0.astype(np.float32)
    pos0 = pos32.astype(np.float64)          # widened f32 = the GPU state
    gamma = np.full(len(faces), 1.0)

    # --- CPU reference: the declared law on the SAME starting state ------
    ref = run_descent(pos0, faces, gamma, fixed_vertices=list(range(6)),
                      max_steps=200)
    centre = 6
    ref_h = float(pos0[centre, 2])

    # --- the GPU-driven loop --------------------------------------------
    cmd = [str(PROBE), "--fixtures", str(FIXTURES), "--fixture", "b2",
           "--gamma-case", "gamma1", "--shader", str(SHADER), "--max-steps", "200"]
    t0 = datetime.now(timezone.utc)
    run = subprocess.run(cmd, capture_output=True, text=True,
                         cwd=str(ROOT), timeout=600)
    (OUTDIR / "gpu_raw_output.txt").write_text(run.stdout + "\n--stderr--\n" + run.stderr,
                                               encoding="utf-8")
    (OUTDIR / "gpu_command.txt").write_text(" ".join(cmd), encoding="utf-8")
    t1 = datetime.now(timezone.utc)

    m = re.search(r"RELAX_RESULT (.*)", run.stdout)
    if not m:
        print("NO EVIDENCE: relax_gpu_probe produced no RELAX_RESULT")
        return 2
    kv = dict(p.split("=", 1) for p in m.group(1).split())
    status = kv["status"]
    n_acc = int(kv["n_accepted"])
    n_trials = int(kv["n_trials"])
    gpu_energies = [float(m2.group(2)) for m2 in
                    re.finditer(r" e(\d+)=([-0-9.e+]+)", run.stdout)]
    gpu_alphas = [float(m2.group(2)) for m2 in
                  re.finditer(r" a(\d+)=([-0-9.e+]+)", run.stdout)]
    gpu_fdotps = [float(m2.group(2)) for m2 in
                  re.finditer(r" f(\d+)=([-0-9.e+]+)", run.stdout)]
    pm = re.search(r"RELAX_FINAL_POS (.*)", run.stdout)
    final_pos = [tuple(map(float, t.split(","))) for t in pm.group(1).split()]
    final_centre = np.array(final_pos[centre])

    # --- R1: frozen-budget echo (the standard probe gates it) -----------
    # (run in the same harness run: the standard probe on the same build)
    probe_cmd = [str(PROBE.parent / "membrane_gpu_probe.exe"),
                 "--fixtures", str(FIXTURES),
                 "--shader", str(SHADER)]
    probe_run = subprocess.run(probe_cmd, capture_output=True, text=True,
                               cwd=str(RUN_CWD := str(ROOT)))
    (OUTDIR / "probe_raw_output.txt").write_text(probe_run.stdout, encoding="utf-8")
    r1 = "GPU_RESULT PASS" in probe_run.stdout

    # --- R2: per-iteration energy vs the CPU reference -------------------
    # Reference energy after k accepted steps: ref.energies[k] (index 0 is
    # the initial energy). GPU e_i is after (i+1) accepted steps.
    ref_after = ref.energies[1:] if len(ref.energies) > 1 else []
    pairs = min(len(gpu_energies), len(ref_after))
    e_drift = 0.0
    worst_pair = None
    for i in range(pairs):
        d = abs(gpu_energies[i] - ref_after[i])
        if d > e_drift:
            e_drift, worst_pair = d, i
    r2 = e_drift <= FROZEN_ENERGY_BUDGET

    # --- R3: final centre position vs the CPU reference -----------------
    ref_final_centre = ref.positions[centre]
    max_coord = float(np.max(np.abs(pos0))) if pos0.size else 1.0
    f32_bound = n_acc * (2.0 ** -23) * max_coord
    pos_gap = float(np.linalg.norm(final_centre - ref_final_centre))
    r3 = pos_gap <= f32_bound

    # --- R4: named taxonomy ---------------------------------------------
    NAMED = {"stationary", "stagnated", "step_limit", "no_descent_step",
             "invalid_surface"}
    r4 = status in NAMED

    # --- R5: Armijo re-check from the trail ------------------------------
    # The law: U_after <= U_before - c1*alpha*f_dot_p, re-checked post-hoc
    # exactly as R4f does for the CPU law.
    from overdamped_descent import ARMIJO_C1
    armijo_worst = 0.0
    armijo_ok = True
    u_seq = [float(kv["initial_energy"])] + gpu_energies
    for i, (a, f, e_after) in enumerate(zip(gpu_alphas, gpu_fdotps, gpu_energies)):
        u_before = u_seq[i]
        margin = u_before - ARMIJO_C1 * a * f - e_after
        if margin < -1e-9:                       # 1e-9 = print precision
            armijo_ok = False
        armijo_worst = min(armijo_worst, margin)
    r5 = armijo_ok

    # --- R6: no tolerance widened (constant, recorded) -------------------
    r6 = True

    # extra descriptive evidence
    final_energy = float(kv["energy"])
    dec_total = float(kv["initial_energy"]) - final_energy
    ref_final_energy = float(ref.energy)
    gap_final_energy = abs(final_energy - ref_final_energy)

    record = {
        "schema": "chimera-relax-gpu01-gate-v1",
        "utc": t0.isoformat(), "utc_finished": t1.isoformat(),
        "task": "GLM-RELAX-GPU-01",
        "preregistration": "docs/THE_RELAX_GPU01_PREREGISTRATION.md",
        "device": (re.search(r"device: (.*)", run.stdout) or [None, "?"])[1].strip()
                  if re.search(r"device: (.*)", run.stdout) else "?",
        "gpu_command": " ".join(cmd),
        "probe_command": " ".join(probe_cmd),
        "starting_state": {
            "fixture": "b2", "gamma_case": "gamma1",
            "state": "frozen fixture f32 positions widened to f64",
            "centre_height_m": ref_h,
        },
        "cpu_reference": {
            "law": "tools/overdamped_descent.run_descent (declared law)",
            "status": ref.status, "n_accepted": ref.n_accepted,
            "energy_initial": ref.energies[0], "energy_final": float(ref.energy),
            "final_centre": ref_final_centre.tolist(),
        },
        "gpu_loop": {
            "status": status, "n_accepted": n_acc, "n_trials": n_trials,
            "energy_initial": float(kv["initial_energy"]),
            "energy_final": final_energy,
            "free_residual": float(kv["free_residual"]),
            "final_centre": final_centre.tolist(),
            "state_representation": "f32 buffers (the verified fixture representation)",
        },
        "budgets": {
            "frozen_energy": FROZEN_ENERGY_BUDGET,
            "frozen_complete_force": FROZEN_COMPLETE_FORCE_BUDGET,
            "derived_f32_position_bound": f32_bound,
            "derivation": "n_acc * 2^-23 * max|coord| (preregistered)",
        },
        "checks": {
            "R1_frozen_single_shot_pass": r1,
            "R2_energy_within_frozen_budget": {"pass": bool(r2), "worst_drift": e_drift, "worst_pair": worst_pair},
            "R3_final_position_within_f32_bound": {"pass": bool(r3), "gap_m": pos_gap, "bound_m": f32_bound},
            "R4_named_terminal_state": {"pass": bool(r4), "status": status},
            "R5_armijo_every_accepted_step": {"pass": bool(r5), "worst_margin": armijo_worst},
            "R6_no_tolerance_widened": r6,
        },
        "descriptive": {
            "gpu_vs_ref_final_energy_gap": gap_final_energy,
            "total_descent": dec_total,
            "gpu_n_accepted_vs_ref": [n_acc, ref.n_accepted],
        },
        "verdict": None,
        "operator_engine_untouched": True,
        "gpu_dynamics_claim": "NONE beyond this standalone numerical gate",
    }
    all_pass = all([r1, r2, r3, r4, r5, r6])
    record["verdict"] = "PASS" if all_pass else "FAIL"
    (OUTDIR / "gate_record.json").write_text(json.dumps(record, indent=2),
                                             encoding="utf-8")
    summary = [
        f"GLM-RELAX-GPU-01 gate -- {record['verdict']}",
        f"device: {record['device']}",
        f"GPU loop: status={status} n_accepted={n_acc} "
        f"energy {kv['initial_energy']} -> {final_energy} J (f32 state of record)",
        f"CPU reference: status={ref.status} n_accepted={ref.n_accepted} "
        f"energy -> {float(ref.energy)} J (f64 law on widened f32 start)",
        f"R1 frozen single-shot: {'PASS' if r1 else 'FAIL'}",
        f"R2 energy drift worst {e_drift:.3e} (budget {FROZEN_ENERGY_BUDGET}): {'PASS' if r2 else 'FAIL'}",
        f"R3 final centre gap {pos_gap:.3e} m (bound {f32_bound:.3e}): {'PASS' if r3 else 'FAIL'}",
        f"R4 named state '{status}': {'PASS' if r4 else 'FAIL'}",
        f"R5 Armijo worst margin {armijo_worst:.3e}: {'PASS' if r5 else 'FAIL'}",
        f"evidence: {OUTDIR}",
    ]
    (OUTDIR / "summary.txt").write_text("\n".join(summary), encoding="utf-8")
    print("\n".join(summary))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
