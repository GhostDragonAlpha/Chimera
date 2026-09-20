"""The posture-cap sweep: wave 10's own optimizer re-run at a range of caps.

Prompt-3 Task 1 (lane buffy/posture-cap-provenance, 2026-09-19).  Wave 10's
verdict was that no reachable periodic trunk trajectory fits the combined
envelope under the 11.2125 N.m posture cap (pre-registered margin 0.9).  The
cap's provenance is the softest constant in the walker: the gait-impl lane
set it to the HIP cap (1.25 x 8.9746 N.m, the measured Oku hip peak) on the
assertion "the same musculature carries the trunk moment", without deriving
whether the sharing is a cap on EACH drive or on the SUM.  This script does
not re-type the optimizer: it imports wave 10's derive_reachable_vault
module (its statics come from derive_trunk_pitch, whose caps flow through
module globals) and re-runs its exact SLSQP collocation -- same starts,
bounds, objective, kinematic constraints -- with CAP_POST (and the margin
bound derived from it) re-pinned per sweep point, and with the leg demands
carried as HARD constraints at the swept ratio bound (wave 10 embedded them
only in the objective; the prompt's admissibility is the combined envelope).

Swept: caps in [11.2, 22.4] N.m (1x to 2x the current).  Primary bound:
ratio <= 1.0 (the prompt's admissibility).  Secondary bound: ratio <= 0.9
(wave 10's pre-registered margin -- operationally the walker lane's
"saturation < 10%" requirement).  Bisection refines each threshold.  The
minimum admissible cap is the biped's price tag; a cap the admitted
musculature cannot produce is Task 2's closing falsifier.

Run from the worktree root with the project interpreter:
  python -B tools/science_funnel/validation/posture_cap_20260919/sweep_posture_cap.py
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

HERE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
GAIT_ZERO = REPO / "tools/science_funnel/validation/gait_zero_20260919"

# Import the wave-10 module under its own name so derive_trunk_pitch (its
# statics dependency) resolves; the sweep patches that module's CAP_POST and
# its derived LIMIT per sweep point -- the lane's own contract, re-pinned,
# never re-typed.
spec = importlib.util.spec_from_file_location(
    "derive_reachable_vault", GAIT_ZERO / "derive_reachable_vault.py")
drv = importlib.util.module_from_spec(spec)
sys.modules["derive_reachable_vault"] = drv
spec.loader.exec_module(drv)

# statics is a pure function of (phi_left, phi_right, stance, stance_phi,
# theta) and does NOT depend on the swept cap: memoize it.  Identical
# numbers (the same code path, cached), orders-of-magnitude fewer repeat
# evaluations across the SLSQP gradient steps and the sweep's repeated
# warm starts.
_memo = {}
_orig_statics = drv.statics.statics


def _memo_statics(phi_left, phi_right, stance_leg, stance_phi, theta=0.0):
    key = (round(float(phi_left), 12), round(float(phi_right), 12), stance_leg,
           round(float(stance_phi), 12), round(float(theta), 12))
    hit = _memo.get(key)
    if hit is None:
        hit = _orig_statics(phi_left, phi_right, stance_leg, stance_phi, theta)
        _memo[key] = hit
    return hit


drv.statics.statics = _memo_statics

N = drv.N  # 21 nodes
OUT = HERE / "min_admissible_cap.json"

# -- the stored cap provenance chain (measured, not edited) --
CAP_CURRENT = 11.2125            # 1.25 * 8.9746: the HIP cap, adopted as the posture cap
HIP_TAU_PEAK_N_M = 8.9746        # Oku measured hip torque peak (gait_controller_20260918)
HEADROOM = 1.25                  # derivation doc section 4.3 headroom factor
W10_STORED_WORST_COMBINED = 1.3227763257041534   # trunk_vault_reachable.json
W10_STORED_WORST_PHI = 0.75      # the stored run's binding node (receipt text says phi~0.85)


def _wave10_start_table():
    """The wave-10 warm start, copied verbatim from derive_reachable_vault.main."""
    return np.array([-0.254, -0.0835, 0.087, 0.2575, 0.3292, 0.2182, 0.1201,
                     0.0588, -0.0441, -0.1568, -0.254, -0.0835, 0.087,
                     0.2575, 0.3292, 0.2182, 0.1201, 0.0588, -0.0441,
                     -0.1568, -0.254])


def run_optimizer(cap: float, margin: float, maxiter: int = 220,
                  both_starts: bool = True):
    """Wave-10's collocation with the posture cap re-pinned to `cap` N.m and
    the acceptance bound at `margin` * cap (both posture and stance hard
    constraints; kinematics and objective exactly wave 10's)."""
    drv.CAP_POST = float(cap)
    drv.LIMIT = margin * float(cap)
    bound = margin * float(cap)

    old = _wave10_start_table()
    starts = [np.zeros(2 * N)]
    if both_starts:
        starts.append(np.r_[old, np.gradient(old, drv.DT)])

    # Stance demands are ratios against the LEG caps (statics.CAP), so the
    # hard constraint is ratio <= margin directly; posture demand is absolute.
    def constraints_full(x):
        rs = drv.metrics(x)
        rows = [bound - abs(r["required_posture_Nm"]) for r in rs]
        rows += [margin - r["stance_ratio"] for r in rs]
        return np.array(rows)

    def kin(x):
        return drv.kinematic_constraints(x)

    def objective(x):
        rs = drv.metrics(x)
        ratios = np.array([max(r["stance_ratio"], r["posture_ratio"]) for r in rs])
        theta, vel = drv.unpack(x)
        return float(np.mean(ratios)
                     + 1e-4 * np.mean(vel ** 2)
                     + 1e-5 * np.mean(np.diff(np.r_[theta, theta[0]]) ** 2))

    best = None
    for x0 in starts:
        result = minimize(objective, x0, method="SLSQP",
                          bounds=[(-0.6, 0.6)] * N + [(-8.0, 8.0)] * N,
                          constraints=[{"type": "ineq", "fun": constraints_full},
                                       {"type": "eq", "fun": kin}],
                          options={"maxiter": maxiter, "ftol": 1e-10, "disp": False})
        rs = drv.metrics(result.x)
        max_post = max(abs(r["required_posture_Nm"]) for r in rs)
        max_comb = max(max(r["stance_ratio"], r["posture_ratio"]) for r in rs)
        # Acceptance = CONSTRAINT SATISFACTION, not the KKT success flag: the
        # sweep asks whether an admissible table EXISTS at this cap, and a
        # collocation iterate that meets every envelope constraint IS a
        # witness.  The kinematic residual is recorded so the witness's
        # periodicity/velocity consistency is auditable (SLSQP holds eq
        # constraints at its own tolerance; we verify, not trust).
        kin_res = float(np.max(np.abs(drv.kinematic_constraints(result.x))))
        ok = bool(max_post <= bound + 1e-7 and max_comb <= margin + 1e-7
                  and kin_res <= 1e-6)
        cand = (ok, float(result.fun), result, max_post, max_comb, kin_res)
        if best is None or (cand[0] and (not best[0] or cand[1] < best[1])):
            best = cand
    ok, fun, res, max_post, max_comb, kin_res = best
    return {"feasible": bool(ok), "optimizer_success": bool(res.success),
            "objective": fun, "message": str(res.message),
            "kinematic_residual": kin_res,
            "max_required_posture_Nm": max_post, "max_combined_ratio": max_comb,
            "theta_rad": [round(float(t), 6) for t in drv.unpack(res.x)[0]]}


def probe(cap: float, margin: float, maxiter: int = 220, both_starts: bool = True) -> dict:
    r = run_optimizer(cap, margin, maxiter=maxiter, both_starts=both_starts)
    return {
        "cap_Nm": round(cap, 6),
        "margin": margin,
        "feasible": r["feasible"],
        "optimizer_success": r["optimizer_success"],
        "objective": round(r["objective"], 6),
        "max_required_posture_Nm": round(r["max_required_posture_Nm"], 6),
        "max_posture_ratio": round(r["max_required_posture_Nm"] / cap, 6),
        "max_combined_ratio": round(r["max_combined_ratio"], 6),
        "kinematic_residual": round(r["kinematic_residual"], 12),
        "message": r["message"],
        "theta_rad": r["theta_rad"],
    }


def find_threshold(margin: float, coarse, bisections: int = 10) -> dict:
    sweep = {}
    for c in coarse:
        sweep[round(c, 4)] = probe(c, margin)
        print(f"  [margin {margin}] cap {c:6.2f} N.m -> "
              f"feasible={sweep[round(c, 4)]['feasible']} "
              f"max_combined={sweep[round(c, 4)]['max_combined_ratio']:.4f}")
    feas = [c for c in coarse if sweep[round(c, 4)]["feasible"]]
    if not feas:
        return {"feasible_anywhere": False, "sweep": sweep, "threshold_Nm": None}
    lo_f = coarse[0]
    infeas = [c for c in coarse if not sweep[round(c, 4)]["feasible"]]
    lo_f = float(max(infeas)) if infeas else float(coarse[0])
    hi_f = float(min(feas))
    trace = []
    for _ in range(bisections):
        mid = 0.5 * (lo_f + hi_f)
        f = probe(mid, margin, maxiter=220, both_starts=False)["feasible"]
        trace.append({"cap_Nm": round(mid, 4), "feasible": bool(f)})
        print(f"  [margin {margin}] bisect {mid:8.4f} -> {'FEASIBLE' if f else 'infeasible'}")
        if f:
            hi_f = mid
        else:
            lo_f = mid
    return {"feasible_anywhere": True, "sweep": sweep, "trace": trace,
            "threshold_Nm": round(hi_f, 4), "bracket_low_Nm": round(lo_f, 4),
            "floor_note": ("the sweep floor is 11.2 N.m; a feasible point AT the floor "
                           "means the true threshold may lie below it" if lo_f == coarse[0] else
                           "bracket is interior to the swept range")}


def main():
    coarse = [11.2, 11.2125, 12.0, 14.0, 16.0, 18.0, 20.0, 22.4]
    print("== primary bound: combined ratio <= 1.0 (the prompt's admissibility) ==")
    primary = find_threshold(1.0, coarse)
    print("== secondary bound: combined ratio <= 0.9 (wave-10 margin / walker <10% saturation) ==")
    secondary = find_threshold(0.9, coarse)
    # Extension (declared): the prompt's range was [11.2, 22.4], but the
    # primary bound is feasible AT the floor -- the true threshold lies at or
    # below it.  Bisect downward to locate the actual minimum admissible cap.
    print("== extension: primary bound, downward [8.0, 11.2] (the floor masked the threshold) ==")
    downward = find_threshold(1.0, [8.0, 9.0, 10.0, 10.5, 11.0, 11.2])

    def threshold_of(r):
        return r["threshold_Nm"] if r["feasible_anywhere"] else None

    out = {
        "schema": "chimera.posture_cap_sweep.v1",
        "lane": "buffy/posture-cap-provenance",
        "date": "2026-09-19",
        "agent": "Buffy",
        "method": "wave-10 SLSQP collocation re-run by module import (CAP_POST and the derived "
                  "margin bound re-pinned; starts/bounds/objective/kinematics verbatim); leg "
                  "demands carried as hard constraints at the swept ratio bound; coarse grid "
                  "[11.2, 12, 14, 16, 18, 20, 22.4] N.m + 10-step bisection per bound",
        "cap_current_Nm": CAP_CURRENT,
        "cap_current_provenance": "1.25 x 8.9746 N.m -- the HIP drive cap (Oku measured hip torque "
                                  "peak x the derived headroom factor), adopted by the gait-impl lane "
                                  "as the posture cap under 'the same musculature carries the trunk "
                                  "moment' (gait_controller.hpp posture-drive comment; "
                                  "derive_trunk_pitch.py CAP_POST = 1.25 * 8.9746)",
        "wave10_stored_reference": {
            "max_combined_ratio": W10_STORED_WORST_COMBINED,
            "binding_node_phi": W10_STORED_WORST_PHI,
            "note": "receipt_wave10.json text says phi~0.85; the stored trunk_vault_reachable.json "
                    "nodes put the binding stance node at phi=0.75 (ratios 1.258, 1.323, 0.977 at "
                    "phi=0.70/0.75/0.85). The artifact is authoritative.",
        },
        "primary_ratio_le_1_0": primary,
        "secondary_ratio_le_0_9": secondary,
        "downward_extension_ratio_le_1_0": downward,
        "min_admissible_cap_Nm": threshold_of(primary),
        "min_admissible_cap_at_wave10_margin_Nm": threshold_of(secondary),
        "min_admissible_cap_true_Nm": threshold_of(downward),
        "verdict": ("AMENDMENT_DERIVABLE" if (threshold_of(primary) or 1e9) > CAP_CURRENT + 1e-9
                    else "CURRENT_CAP_ADMISSIBLE_AT_RATIO_1_0"),
    }
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("min_admissible_cap_Nm",
                                          "min_admissible_cap_at_wave10_margin_Nm",
                                          "min_admissible_cap_true_Nm",
                                          "verdict")}, indent=1))
    print("written", OUT)


if __name__ == "__main__":
    main()
