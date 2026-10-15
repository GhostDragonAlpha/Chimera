"""membrane_fixture_b2.py — ASTRA-B2 first membrane fixture, CPU side.

Implements the preregistered fixture from ASTRA's B2 (2026-09-07), which is
the registration of record. This file implements the CPU-verifiable subset
and must NOT widen any B2 budget after observing results.

FIXTURE (B2, fixed): six pinned rim vertices r_k = (cos kpi/3, sin kpi/3, 0),
centre c = (0,0,0.125) on a vertical rail (x=y=0), faces (c, r_k, r_{k+1})
CCW, gamma = 1 J/m^2, 1 wu = 1 m for this experiment. Seven vertices, six
faces, centre degree 6, rim degree 2. No gravity, inertia, other passes.

UPLOAD LAW  Coordinates are uploaded ONCE as binary32; the CPU reference
evaluates those exact uploaded values promoted to binary64. Ideal analytic
numbers are cross-checks, not substitutes for this matched-input comparison.

UPDATE LAW (optimization, NOT simulation time)  Projected gradient descent,
P = 1/gamma, alpha = 1/8, h+ = h + alpha*P*F_cz; Armijo c1 = 1e-4, halving
on rejection, max 20 halvings, exhaustion retains state and reports. For
this 1-DOF fixture h+ = h*(1 - 3alpha/sqrt(3/4 + h^2)).

ANALYTIC CROSS-CHECKS (ideal coordinates, centre height h):
    A(h) = 3*sqrt(3/4 + h^2)          F_cz = -3*gamma*h/sqrt(3/4 + h^2)
    A(0.125) = 2.625 m^2,  U0 = 2.625 J,  F_c = (0,0,-3/7) N,
    A_flat = 3*sqrt(3)/2 = 2.598076211353316 m^2,
    available ideal reduction = 0.026923788646684 J.

PREREGISTERED LAWS (ASTRA-B2 M1-M4; budgets fixed there):
  M1 force transcription  — GPU gates: per-corner 4.0e-6 N, assembly-only
     1.0e-6 N, complete force 2.5e-5 N (per component), energy 1.1e-5 J,
     all at gamma = 1 (doubled at gamma = 2). NOT applied here — they gate
     the GPU kernels; this file is the CPU reference side.
  M2 accepted relaxation — after 12 accepted steps: h <= 1e-3 m and
     0 <= U - gamma*A_flat <= 2.0e-6 J (B64 = 512*eps64*U0 ~= 2.985e-13 J
     covers reference roundoff below the lower bound); rim and centre x,y
     bit-identical; every accepted transition passes the Armijo and B64
     nonincrease gates. Twelve steps demonstrate relaxation; they certify
     neither stationarity nor physical relaxation time.
  M3 zero-gamma control — forces/energy numerically zero (signed zero ok),
     12 attempted ticks bit-identical, NO gamma reciprocal evaluated.
  M4 gamma-doubling control — same immutable uploaded positions; CPU-side
     exact 2x is assertable (power-of-two exactness); B2's conservative
     GPU cross-scaling bounds (4.4e-5 J, 1.0e-4 N) are recorded, not used.

CPU-vs-ANALYTIC allowance: |F_c - (0,0,-3/7)| <= 1e-6 N [PROVISIONAL,
derived from 2^-24 coordinate quantization; expected deviation ~1e-7].
DYAD (later, engine window): accepted states displayed 0.25 s wall-clock
each (presentation pacing); captures at steps 0, 1, 4, 8, 12 with state
IDs and height/energy. Nothing here makes a visual claim.

VERIFICATION CLASS: CPU numerical only. Iterations are not seconds.
"""
from __future__ import annotations

import json
import math
import platform
import sys
from pathlib import Path

import numpy as np

_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(_TOOLS))

from surface_energy_reference import evaluate_surface   # noqa: E402
from evidence_output import default_stamp               # noqa: E402

GAMMA = 1.0            # [J/m^2]
H0 = 0.125             # [m]  exact in binary32 (2^-3)
N_RIM = 6
ALPHA = 1.0 / 8.0      # dimensionless trial step (B2)
ARMIJO_C1 = 1e-4       # Armijo coefficient (numerical algorithm choice, B2)
MAX_HALVINGS = 20      # per-step backtracking budget (B2)
N_STEPS = 12           # accepted steps required by M2

# B2 GPU budgets, recorded for the transcription contract — NOT applied here:
B2_GPU_BUDGETS = {"corner_N": 4.0e-6, "assembly_N": 1.0e-6,
                  "complete_force_N": 2.5e-5, "energy_J": 1.1e-5,
                  "gamma2_cross_U_J": 4.4e-5, "gamma2_cross_F_N": 1.0e-4}


def b2_mesh():
    """Ideal float64 mesh; then the ONE binary32 upload, promoted to float64.
    Vertex order: rim 0..5, centre 6. Returns (V_ideal, V_up, F)."""
    ang = np.pi / 3.0 * np.arange(N_RIM)
    rim = np.stack([np.cos(ang), np.sin(ang), np.zeros(N_RIM)], axis=1)
    centre = np.array([[0.0, 0.0, H0]])
    V_ideal = np.vstack([rim, centre])
    F = np.array([[6, k, (k + 1) % N_RIM] for k in range(N_RIM)],
                 dtype=np.int64)
    V_up = V_ideal.astype(np.float32).astype(np.float64)
    return V_ideal, V_up, F


def main() -> int:
    V_ideal, V_up, F = b2_mesh()

    # ---- C1: analytic cross-checks on the IDEAL geometry ------------------
    A0_ideal = 3.0 * math.sqrt(0.75 + H0 ** 2)
    Fcz_ideal = -3.0 * GAMMA * H0 / math.sqrt(0.75 + H0 ** 2)
    A_flat_ideal = 3.0 * math.sqrt(3.0) / 2.0
    c1 = {
        "A0_is_2_625": A0_ideal == 2.625,
        "Fcz_is_minus_3_over_7": Fcz_ideal == -3.0 / 7.0,
        "A_flat_value": A_flat_ideal,
        "reduction_value": 2.625 - A_flat_ideal,
        "reduction_matches_B2": abs((2.625 - A_flat_ideal)
                                    - 0.026923788646684) < 1e-15,
    }
    c1_ok = (c1["A0_is_2_625"] and c1["Fcz_is_minus_3_over_7"]
             and c1["reduction_matches_B2"])

    # ---- C2: matched-input evaluation on the UPLOADED (binary32) geometry -
    ev_up = evaluate_surface(V_up, F, GAMMA)
    U0_up = ev_up.energy
    Fc0 = ev_up.vertex_forces[6].copy()          # all three, pre-projection
    dev = np.abs(Fc0 - np.array([0.0, 0.0, -3.0 / 7.0]))
    C2_ALLOW = 1e-6                              # PROVISIONAL (docstring)
    c2_ok = bool(dev.max() <= C2_ALLOW)
    B64 = 512.0 * np.finfo(np.float64).eps * U0_up   # B2 acceptance bound

    # ---- C3: M2 relaxation — 12 accepted steps on the vertical rail -------
    V = V_up.copy()
    U_prev = U0_up
    trail, all_gates, refused = [], True, None
    for step in range(1, N_STEPS + 1):
        ev = evaluate_surface(V, F, GAMMA)
        Fc = ev.vertex_forces[6].copy()
        P = 1.0 / GAMMA
        alpha, accepted = ALPHA, False
        for _ in range(MAX_HALVINGS + 1):
            dz = alpha * P * Fc[2]               # rail: only z moves
            Vt = V.copy()
            Vt[6, 2] = V[6, 2] + dz
            evt = evaluate_surface(Vt, F, GAMMA)
            inner = P * Fc[2] * Fc[2]            # <F_free, p> on the rail
            if (evt.energy <= U_prev - ARMIJO_C1 * alpha * inner + B64
                    and evt.energy - U_prev <= B64):
                accepted = True
                break
            alpha *= 0.5
        if not accepted:
            all_gates, refused = False, step
            break
        trail.append({"step": step, "h_before": float(V[6, 2]),
                      "U_before": U_prev, "F_c": Fc.tolist(),
                      "alpha": alpha, "dz": dz, "U_after": evt.energy,
                      "inner_positive": bool(inner > 0.0)})
        V, U_prev = Vt, evt.energy
    h_final = float(V[6, 2])
    Vflat = V_up.copy()
    Vflat[6, 2] = 0.0
    U_flat_up = evaluate_surface(Vflat, F, GAMMA).energy
    gap = U_prev - GAMMA * U_flat_up             # gamma * A_flat^(64)
    c3_ok = bool(all_gates and refused is None
                 and h_final <= 1e-3
                 and gap >= -B64 and gap <= 2.0e-6
                 and np.array_equal(V[:N_RIM], V_up[:N_RIM])
                 and V[6, 0] == 0.0 and V[6, 1] == 0.0)

    # ---- C4: M3 zero-gamma control ----------------------------------------
    ev_z = evaluate_surface(V_up, F, 0.0)
    Vz = V_up.copy()
    # 12 attempted ticks with gamma = 0: the guard returns before any
    # reciprocal of gamma is evaluated; positions never change.
    for _ in range(N_STEPS):
        if evaluate_surface(Vz, F, 0.0).vertex_forces.any():
            break                                # falsifier: any nonzero force
    c4_ok = bool(ev_z.energy == 0.0
                 and not ev_z.vertex_forces.any()   # signed zero ok
                 and np.array_equal(Vz, V_up))

    # ---- C5: M4 gamma-doubling, CPU exactness ------------------------------
    ev_2 = evaluate_surface(V_up, F, 2.0 * GAMMA)
    c5_ok = bool(ev_2.energy == 2.0 * ev_up.energy
                 and np.equal(ev_2.vertex_forces,
                              2.0 * ev_up.vertex_forces).all())

    checks = {
        "C1_analytic_ideal_crosscheck": c1_ok,
        "C2_matched_input_vs_analytic_1e-6_PROVISIONAL": c2_ok,
        "C3_M2_12_step_relaxation": c3_ok,
        "C4_M3_zero_gamma_control": c4_ok,
        "C5_M4_gamma_doubling_exact_cpu": c5_ok,
    }
    ok = all(checks.values())

    record = {
        "what": "ASTRA-B2 first membrane fixture — CPU reference side",
        "registration": "ASTRA B2 2026-09-07 (M1-M4); budgets fixed there",
        "verification_class": "CPU numerical only; GPU gates recorded, not applied",
        "time_note": "optimization iterations are NOT seconds",
        "python": platform.python_version(), "numpy": np.__version__,
        "constants": {
            "u_2^-24": 2.0 ** -24,
            "eta5_5u_over_1_minus_5u": 5.0 * 2.0 ** -24 / (1.0 - 5.0 * 2.0 ** -24),
            "eta64_64u_over_1_minus_64u": 64.0 * 2.0 ** -24 / (1.0 - 64.0 * 2.0 ** -24),
            "B64_J": B64,
            "note": "B2's printed 'eta5 = 2.5u' is a label typo; the VALUE "
                    "2.980233126948216e-7 equals 5u/(1-5u) (verified here).",
        },
        "fixture": {"gamma_J_per_m2": GAMMA, "h0_m": H0, "n_rim": N_RIM,
                    "alpha": ALPHA, "armijo_c1": ARMIJO_C1,
                    "max_halvings": MAX_HALVINGS, "n_steps": N_STEPS},
        "C1": c1,
        "C2": {"F_c_uploaded": Fc0.tolist(), "dev_vs_(0,0,-3/7)": dev.tolist(),
               "U0_uploaded_J": U0_up, "U0_vs_ideal_dev_J": U0_up - 2.625,
               "allowance_N_PROVISIONAL": C2_ALLOW},
        "C3": {"h_final_m": h_final, "U_final_J": U_prev,
               "U_flat_uploaded_J": U_flat_up, "gap_J": gap,
               "gap_bounds": [-B64, 2.0e-6], "refused_at_step": refused,
               "all_gates": all_gates,
               "rim_and_centre_xy_bitexact": bool(
                   np.array_equal(V[:N_RIM], V_up[:N_RIM])
                   and V[6, 0] == 0.0 and V[6, 1] == 0.0),
               "trail": trail,
               "dyad_capture_states": {str(s): (
                   {"h": t["h_before"], "U": t["U_before"]}
                   if (t := next((x for x in trail if x["step"] == s), None))
                   else {"h": h_final, "U": U_prev})
                   for s in (0, 1, 4, 8, 12)}},
        "C4": {"energy": ev_z.energy, "force_max_abs": float(
            np.abs(ev_z.vertex_forces).max())},
        "C5": {"exact_2x_energy": ev_2.energy == 2.0 * ev_up.energy,
               "b2_gpu_budgets_recorded": B2_GPU_BUDGETS},
        "checks": checks, "all_pass": ok,
    }

    out_dir = _TOOLS.parent / "agent_logs" / "glm_foundation_g01"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"membrane_fixture_b2_results_{default_stamp()}.json"
    if out_path.exists():                # evidence law: never silent overwrite
        raise SystemExit(f"evidence_path_exists: {out_path} — rerun or --out")
    out_path.write_text(json.dumps(record, indent=2), encoding="utf-8")

    width = max(len(k) for k in checks)
    for k, v in checks.items():
        print(f"  {k:<{width}}  {'PASS' if v else 'FAIL'}")
    print(f"  h: {H0} -> {h_final:.6e} m after 12 accepted steps")
    print(f"  U: {U0_up:.12g} -> {U_prev:.12g} J  "
          f"(uploaded flat ref {U_flat_up:.12g} J, gap {gap:.3e} J)")
    print(f"  F_c uploaded: ({Fc0[0]:+.3e}, {Fc0[1]:+.3e}, {Fc0[2]:+.12g}) N "
          f"vs analytic (0, 0, -3/7)")
    print(f"  results: {out_path}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
