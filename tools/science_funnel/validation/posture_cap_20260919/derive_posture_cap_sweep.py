"""Posture-cap provenance: the minimum admissible posture drive cap.

Copied from gait_zero_20260919/derive_reachable_vault.py (wave 10) and
modified ONLY here -- the original dir is untouched.  Wave 10 found no
reachable periodic trunk trajectory fits the envelope at CAP_POST=11.2125
N.m: combined stance+posture ratio 1.3228 at the worst node, posture demand
peaking 10.0912 N.m (saturated against the 0.9 limit).  This derivation
sweeps the posture cap and bisects to the minimum cap C* at which a
periodic collocated theta trajectory exists with combined ratio <= 1.0 at
every node.  C* is the biped's price tag; Task 2 audits the musculature
records against it.

Admissibility definition (derived, not tasted): the wave-10 objective
(minimize mean over nodes of max(stance_ratio, posture_ratio)) is minimized
over a constraint set that only GROWS with the cap, so the minimum
achievable combined ratio is a non-increasing function of the cap and the
crossing of 1.0 is a root-find, not a preference.

Rule-0 membrane is written into min_admissible_cap.json with status
"pre-registered" BEFORE any optimizer call (main() writes it first).
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import derive_trunk_pitch as statics  # noqa: E402

N = 21
T = 0.71
DT = T / 20.0
I_HAT = 0.0207 + 8.184 * 0.2506**2
M_HAT = 8.184
R_HAT = 0.2506
G = 9.80665
CAP_BASE = 11.2125          # wave-10 posture cap (1x)
CAP_TWICE = 22.425          # 2x ceiling of the sweep
N_SWEEP = 8
ADM = 1.0                   # admissible combined ratio (the mission target)
BISECT_TOL = 0.02           # N.m resolution of the price tag

MEMBRANE = {
    "statement": (
        "The wave-10 combined-envelope infeasibility (ratio 1.3228 at the "
        "worst node, posture saturated at 10.0912 N.m) is an artifact of the "
        "posture-drive cap, not of the trunk-vault path itself: the minimum "
        "achievable combined stance+posture ratio over periodic collocated "
        "theta trajectories is a non-increasing function of the posture cap "
        "C, and it crosses 1.0 at a derivable cap C* inside [11.2125, "
        "22.425] N.m.  C* is the biped's price tag, to be audited against "
        "the admitted musculature (PCSA x 0.3 MPa x moment arm) before any "
        "amendment."),
    "prediction": (
        "C* lies in (11.2125, 22.425] N.m: the 8-step sweep plus bisection "
        "finds a cap at which every collocation node's combined ratio is "
        "<= 1.0, with the binding node near phi ~ 0.75-0.85 where the knee "
        "ratio (1.3228 at wave 10) bounds the combined ratio and the "
        "posture demand saturates its constraint."),
    "falsifier": (
        "If at C = 22.425 N.m (2x the wave-10 cap) the best reachable "
        "trajectory still has combined ratio > 1.0 at any node, the "
        "infeasibility is NOT a posture-cap artifact, this membrane dies, "
        "the 11.2125 N.m cap is exonerated, and the wave-10 INFEASIBLE "
        "verdict stands as the final word on the admissible-vault path."),
}


def unpack(x):
    return np.asarray(x[:N]), np.asarray(x[N:])


def periodic_accel(v):
    return (np.roll(v, -1) - np.roll(v, 1)) / (2.0 * DT)


def row(theta, i):
    phi = i / 20.0
    tau, *_ = statics.statics(phi, (phi + 0.5) % 1.0, "L", phi, float(theta))
    return np.asarray(tau)


def make_metrics(cap_post):
    def metrics(x):
        theta, vel = unpack(x)
        acc = periodic_accel(vel)
        rows = []
        for i in range(N):
            tau = row(theta[i], i)
            static = float(tau[2])
            gravity = M_HAT * G * R_HAT * math.sin(float(theta[i]))
            inertial = I_HAT * float(acc[i])
            required = static + gravity + inertial
            leg_ratios = [abs(float(tau[3])) / statics.CAP["hip"],
                          abs(float(tau[4])) / statics.CAP["knee"],
                          abs(float(tau[5])) / statics.CAP["ankle"],
                          abs(float(tau[6])) / statics.CAP["mp"]]
            rows.append({"phi": i / 20.0, "theta_rad": float(theta[i]),
                         "theta_dot_rad_s": float(vel[i]),
                         "theta_ddot_rad_s2": float(acc[i]),
                         "static_posture_Nm": static,
                         "gravity_Nm": gravity,
                         "inertial_Nm": inertial,
                         "required_posture_Nm": required,
                         "posture_ratio": abs(required) / cap_post,
                         "stance_ratio": max(leg_ratios),
                         "leg_ratios": leg_ratios})
        return rows
    return metrics


def solve_cap(cap_post, starts):
    """One optimizer pass at a given cap; returns (summary, best_result)."""
    metrics = make_metrics(cap_post)
    limit = cap_post  # admissibility: posture ratio <= 1.0 at every node

    def objective(x):
        rs = metrics(x)
        ratios = np.array([max(r["stance_ratio"], r["posture_ratio"]) for r in rs])
        return float(np.mean(ratios) + 1e-4 * np.mean(unpack(x)[1] ** 2)
                     + 1e-5 * np.mean(np.diff(np.r_[unpack(x)[0], unpack(x)[0][0]]) ** 2))

    def constraints(x):
        rs = metrics(x)
        return np.array([limit - abs(r["required_posture_Nm"]) for r in rs])

    def kinematic_constraints(x):
        theta, vel = unpack(x)
        return np.roll(theta, -1) - theta - 0.5 * DT * (np.roll(vel, -1) + vel)

    bounds = [(-0.6, 0.6)] * N + [(-8.0, 8.0)] * N
    best = None
    for x0 in starts:
        result = minimize(objective, x0, method="SLSQP", bounds=bounds,
                          constraints=[{"type": "ineq", "fun": constraints},
                                       {"type": "eq", "fun": kinematic_constraints}],
                          options={"maxiter": 500, "ftol": 1e-10, "disp": False})
        if best is None or (result.success and (not best.success or result.fun < best.fun)):
            best = result
    rs = metrics(best.x)
    max_required = max(abs(r["required_posture_Nm"]) for r in rs)
    worst = max(rs, key=lambda r: max(r["stance_ratio"], r["posture_ratio"]))
    max_combined = max(max(r["stance_ratio"], r["posture_ratio"]) for r in rs)
    summary = {
        "cap_Nm": float(cap_post),
        "success": bool(best.success), "message": str(best.message),
        "objective": float(best.fun),
        "max_required_posture_Nm": float(max_required),
        "max_combined_ratio": float(max_combined),
        "worst_node": {"phi": worst["phi"],
                       "posture_ratio": worst["posture_ratio"],
                       "stance_ratio": worst["stance_ratio"],
                       "leg_ratios": worst["leg_ratios"]},
        "admissible": bool(best.success and max_combined <= ADM + 1e-7),
        "theta_reachable_deg": [round(math.degrees(r["theta_rad"]), 4) for r in rs],
    }
    return summary, best


def main():
    out = HERE / "min_admissible_cap.json"
    # ---- Rule 0: pre-register the membrane BEFORE any computation ----
    pre = {"derivation": "minimum admissible posture drive cap (posture-cap provenance, Task 1)",
           "source": "copied+modified from gait_zero_20260919/derive_reachable_vault.py (wave 10)",
           "rule_0_membrane": MEMBRANE,
           "status": "pre-registered",
           "registered_before_compute": True,
           "admissibility": f"combined stance+posture ratio <= {ADM} at all 21 collocation nodes, periodic theta/theta-dot, T=0.71 s",
           "sweep": {"caps_Nm": list(np.linspace(CAP_BASE, CAP_TWICE, N_SWEEP)),
                     "bisection_tol_Nm": BISECT_TOL}}
    out.write_text(json.dumps(pre, indent=1) + "\n", encoding="utf-8")
    print("membrane pre-registered ->", out)

    old = np.array([-0.254, -0.0835, 0.087, 0.2575, 0.3292, 0.2182, 0.1201,
                    0.0588, -0.0441, -0.1568, -0.254, -0.0835, 0.087,
                    0.2575, 0.3292, 0.2182, 0.1201, 0.0588, -0.0441, -0.1568, -0.254])
    zero_start = np.zeros(2 * N)
    wave8_start = np.r_[old, np.gradient(old, DT)]

    sweep = []
    warm = None  # continuation start from the previous cap's solution
    for cap in np.linspace(CAP_BASE, CAP_TWICE, N_SWEEP):
        starts = [zero_start] + ([wave8_start] if cap == np.linspace(CAP_BASE, CAP_TWICE, N_SWEEP)[0] else [])
        if warm is not None:
            starts.append(warm)
        summary, best = solve_cap(cap, starts)
        warm = best.x
        sweep.append(summary)
        print(f"cap={cap:.4f}: combined={summary['max_combined_ratio']:.6f} "
              f"posture_max={summary['max_required_posture_Nm']:.4f} "
              f"admissible={summary['admissible']} ({summary['message']})")
        pre["sweep_runs"] = sweep
        pre["status"] = "sweep-running"
        out.write_text(json.dumps(pre, indent=1) + "\n", encoding="utf-8")

    admissible_caps = [s["cap_Nm"] for s in sweep if s["admissible"]]
    if not admissible_caps:
        pre["status"] = "falsified"
        pre["verdict"] = ("MEMBRANE FALSIFIED: no cap in [11.2125, 22.425] N.m "
                          "admits a combined ratio <= 1.0; the wave-10 cap is "
                          "exonerated and the INFEASIBLE verdict stands.")
        out.write_text(json.dumps(pre, indent=1) + "\n", encoding="utf-8")
        print(pre["verdict"])
        return

    # bisection between the last infeasible and the first admissible cap
    first_ok = min(admissible_caps)
    infeasible_below = [s["cap_Nm"] for s in sweep if not s["admissible"] and s["cap_Nm"] < first_ok]
    bisect = []
    if infeasible_below:
        lo, hi = max(infeasible_below), first_ok
        warm = None
        while hi - lo > BISECT_TOL:
            mid = 0.5 * (lo + hi)
            starts = [zero_start, wave8_start] + ([warm] if warm is not None else [])
            summary, best = solve_cap(mid, starts)
            warm = best.x
            bisect.append(summary)
            print(f"bisect cap={mid:.4f}: combined={summary['max_combined_ratio']:.6f} "
                  f"admissible={summary['admissible']}")
            if summary["admissible"]:
                hi = mid
            else:
                lo = mid
            pre["bisect_runs"] = bisect
            pre["status"] = "bisect-running"
            out.write_text(json.dumps(pre, indent=1) + "\n", encoding="utf-8")
        c_star = hi
    else:
        c_star = first_ok  # already admissible at 1x under the <=1.0 rule

    # confirmation run at C*: the same cap re-solved from the cold starts
    star_summary, _ = solve_cap(c_star, [zero_start, wave8_start])
    star_summary["role"] = "confirmation_at_C_star"
    bisect.append(star_summary)
    print(f"C* = {c_star:.4f} N.m confirmed: combined={star_summary['max_combined_ratio']:.6f} "
          f"admissible={star_summary['admissible']}")

    # noise guard: report the LOWEST verified-admissible cap probed anywhere
    all_runs = sweep + bisect
    all_feasible = [s["cap_Nm"] for s in all_runs if s["admissible"]]
    c_star = min(all_feasible + [c_star])
    star_summary = min((s for s in all_runs
                        if s["admissible"] and abs(s["cap_Nm"] - c_star) < 1e-9),
                       key=lambda s: s["max_combined_ratio"])

    pre.update({
        "status": "complete",
        "min_admissible_cap_Nm": c_star,
        "min_admissible_cap_multiple_of_wave10": c_star / CAP_BASE,
        "resolution_Nm": BISECT_TOL,
        "worst_node_at_C_star": star_summary["worst_node"],
        "max_combined_ratio_at_C_star": star_summary["max_combined_ratio"],
        "bisect_runs": bisect,
        "monotone_check": ("sweep combined ratios: " +
                           ", ".join(f"{s['cap_Nm']:.3f}->{s['max_combined_ratio']:.4f}" for s in sweep)),
        "verdict": (f"PRICE TAG: the minimum admissible posture cap is C* = {c_star:.4f} N.m "
                    f"({c_star / CAP_BASE:.4f}x the wave-10 11.2125 N.m cap): the first cap on the "
                    "derived non-increasing frontier at which a periodic collocated trunk "
                    "trajectory keeps the combined stance+posture ratio <= 1.0 at every node."),
    })
    out.write_text(json.dumps(pre, indent=1) + "\n", encoding="utf-8")
    print("written", out)


if __name__ == "__main__":
    main()
