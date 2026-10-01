"""Wave-10 reachability-constrained trunk-vault derivation.

Rule-0 membrane is banked in receipt_wave10.json before this solver is run.
The decision vector is periodic theta and theta-dot at 21 phase nodes.  The
finite-difference acceleration is evaluated on the 0.71 s cycle.  The static
posture demand comes from derive_trunk_pitch.statics; the conservative posture
check also includes HAT pendulum gravity and collocation inertia.  The table is
accepted only when every node stays below 0.9 of the 11.2125 N.m posture cap.
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
CAP_POST = 11.2125
LIMIT = 0.9 * CAP_POST


def unpack(x):
    return np.asarray(x[:N]), np.asarray(x[N:])


def periodic_accel(v):
    return (np.roll(v, -1) - np.roll(v, 1)) / (2.0 * DT)


def row(theta, i):
    phi = i / 20.0
    tau, *_ = statics.statics(phi, (phi + 0.5) % 1.0, "L", phi, float(theta))
    return np.asarray(tau)


def metrics(x):
    theta, vel = unpack(x)
    acc = periodic_accel(vel)
    rows = []
    for i in range(N):
        tau = row(theta[i], i)
        static = float(tau[2])
        gravity = M_HAT * G * R_HAT * math.sin(float(theta[i]))
        inertial = I_HAT * float(acc[i])
        # Conservative actuator envelope: static plant demand plus the
        # pendulum's dynamic demand, with signs retained for diagnostics.
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
                     "posture_ratio": abs(required) / CAP_POST,
                     "stance_ratio": max(leg_ratios),
                     "leg_ratios": leg_ratios})
    return rows


def objective(x):
    rs = metrics(x)
    # Smooth-ish max surrogate: mean of node maxima is the requested primary
    # objective; a small velocity/curvature regularizer chooses the reachable
    # basin when several tables have equal demand.
    ratios = np.array([max(r["stance_ratio"], r["posture_ratio"]) for r in rs])
    return float(np.mean(ratios) + 1e-4 * np.mean(unpack(x)[1] ** 2) + 1e-5 * np.mean(np.diff(np.r_[unpack(x)[0], unpack(x)[0][0]]) ** 2))


def constraints(x):
    rs = metrics(x)
    return np.array([LIMIT - abs(r["required_posture_Nm"]) for r in rs])


def kinematic_constraints(x):
    theta, vel = unpack(x)
    return np.roll(theta, -1) - theta - 0.5 * DT * (np.roll(vel, -1) + vel)


def main():
    # Start at the smooth zero trajectory; also try the wave-8 trajectory and
    # retain the best feasible basin.  Bounds prevent the optimizer from
    # hiding a demand in an absurd pendulum pose or speed.
    old = np.array([-0.254, -0.0835, 0.087, 0.2575, 0.3292, 0.2182, 0.1201,
                    0.0588, -0.0441, -0.1568, -0.254, -0.0835, 0.087,
                    0.2575, 0.3292, 0.2182, 0.1201, 0.0588, -0.0441, -0.1568, -0.254])
    starts = [np.zeros(2 * N), np.r_[old, np.gradient(old, DT)]]
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
    max_combined = max(max(r["stance_ratio"], r["posture_ratio"]) for r in rs)
    feasible = bool(best.success and max_required <= LIMIT + 1e-7 and max_combined <= 0.9 + 1e-7)
    result = {
        "method": "SLSQP direct collocation, periodic theta/theta_dot, finite-difference theta_ddot",
        "success": bool(best.success), "message": str(best.message),
        "objective": float(best.fun), "T_s": T, "dt_node_s": DT,
        "hat_inertia_kg_m2": I_HAT, "gravity_moment_amplitude_Nm": M_HAT * G * R_HAT,
        "posture_cap_Nm": CAP_POST, "posture_limit_Nm": LIMIT,
        "feasible": feasible,        "max_required_posture_Nm": max_required,
        "max_ratio_to_cap": max_combined,

        "max_posture_ratio_to_cap": max(r["posture_ratio"] for r in rs),
        "nodes": rs,
        "theta_reachable_rad": [round(r["theta_rad"], 7) for r in rs],
        "theta_reachable_deg": [round(math.degrees(r["theta_rad"]), 4) for r in rs],
        "theta_dot_rad_s": [round(r["theta_dot_rad_s"], 7) for r in rs],
        "verdict": "FEASIBLE: every collocation node stays below 0.9 combined cap" if feasible else "INFEASIBLE: reachable stance/posture envelope exceeds 0.9 cap",
    }
    out = HERE / "trunk_vault_reachable.json"
    out.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("success", "feasible", "objective", "max_required_posture_Nm", "max_ratio_to_cap", "verdict")}, indent=2))
    print("table_deg", result["theta_reachable_deg"])
    print("written", out)


if __name__ == "__main__":
    main()
