"""derive_standing_pose.py -- THE STANDING POSE SOLVE (preregistration 63e9def4...,
banked BEFORE this run; one solve, no sweep).

The constrained optimization the class records admit:
  x = [hipL flexion/adduction/rotation, hipR flexion/adduction/rotation,
       kneeL, kneeR, driverL, driverR]                    (10 recorded coordinates)
  bounds  = the committed joint_class ranges, parsed at run time
  constraints = the two hip seats under the committed 3.0 mm touching cut
  objective = J = V + kappa*d  (pads-coplanarity deficit + trunk-level deficit,
              kappa = V_rest/d_rest from committed bytes)
  solver  = scipy SLSQP, ftol 1e-12, maxiter 400, feasible rest start x0 = 0
  env     = single-threaded BLAS (set before numpy import; also set by caller)

The elbows are NOT variables: no pad or trunk authority (both their pad and
their parent are fixed by the class records); they carry the forced range floor
(the only class whose recorded range excludes theta = 0).

Run:  OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 python -B \
        tools/science_funnel/validation/standing_pose_20260921/derive_standing_pose.py
"""

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parents[1] / "hip_pivot_proof_20260921"))

from standing_pose_core import (StandingDerivation, CUT_MM, R12,
                                sanitize, rnd)

OUT = HERE / "pose.json"

SOLVER = {"method": "SLSQP", "ftol": 1e-12, "maxiter": 400}


def main():
    dv = StandingDerivation()

    result = minimize(
        lambda x: dv.objective_terms(x)[0] + dv.kappa * dv.objective_terms(x)[1],
        np.zeros(10), method=SOLVER["method"],
        bounds=dv.bounds(),
        constraints=[{"type": "ineq",
                      "fun": lambda x: dv.all_seat_constraints(x)}],
        options={"ftol": SOLVER["ftol"], "maxiter": SOLVER["maxiter"]})

    x = np.asarray(result.x, dtype=np.float64)
    V, d = dv.objective_terms(x)
    seats = dv.all_seat_constraints(x)

    pose_bonds = {}
    for side in ("L", "R"):
        h = dv.hip[side]
        for i, nm in enumerate(("flexion", "adduction", "rotation")):
            pose_bonds[h["bond"] + "." + nm] = {
                "bond": h["bond"], "coordinate": nm, "range_rad": h["range"][i],
                "theta": rnd(x[(0 if side == "L" else 3) + i])}
    pose_bonds[dv.knee["L"]["bond"]] = {"coordinate": "knee_angle", "theta": rnd(x[6])}
    pose_bonds[dv.knee["R"]["bond"]] = {"coordinate": "knee_angle", "theta": rnd(x[7])}
    pose_bonds[dv.driver["L"]["bond"]] = {"coordinate": "subtalar_class", "theta": rnd(x[8])}
    pose_bonds[dv.driver["R"]["bond"]] = {"coordinate": "subtalar_class", "theta": rnd(x[9])}
    for side in ("L", "R"):
        e = dv.elbow[side]
        for b in e["bonds"]:
            pose_bonds[b] = {"coordinate": "elbow_flexion", "theta": rnd(e["forced_theta"])}
    for b in ("bond.joint_10_12", "bond.joint_11_13", "bond.joint_07_18",
              "bond.joint_22_25", "bond.joint_23_24"):
        pose_bonds[b] = {"coordinate": "at_rest", "theta": 0.0}
    for b in ("bond.joint_06_20", "bond.joint_07_21"):
        pose_bonds[b] = {"coordinate": None, "theta": None,
                         "class": "syndesmosis_nodof"}
    for b in ("bond.joint_02_15", "bond.joint_03_17", "bond.joint_04_08", "bond.joint_05_09"):
        pose_bonds[b] = {"coordinate": None, "theta": None,
                         "class": "positional_contact"}
    for b in ("bond.joint_20_25", "bond.joint_21_24"):
        pose_bonds[b] = {"coordinate": None, "theta": None,
                         "note": "loop bond: no pose variable (the FK tree spans <= 2 edges "
                                 "of the 3-cycle); the seat is measured at the pose"}

    record = {
        "schema": "chimera.standing_pose.v1",
        "lane": "agent/standing-pose-20260921",
        "base_commit": "52f101c1",
        "preregistration_sha256": (HERE / "preregistration.sha256").read_text().split()[0],
        "trailer": "Agent: GLM 5.3",
        "solver": {
            **SOLVER,
            "library": "scipy.optimize.minimize",
            "start": "the feasible rest projection x0 = zeros(10)",
            "bounds_source": "the committed definition's joint_class records, parsed at run time",
            "constraints": "hip seats: 3.0 - law_gap(posed femur, composite) >= 0 (both sides); "
                           "tarsal loop seats (amendment 2): 3.0 - law_gap(posed loop members) "
                           ">= 0 for cycles A (20-25) and B (21-24) — the committed cut as the "
                           "derived band narrowing the class record pre-registered",
            "env": "OMP_NUM_THREADS=1, OPENBLAS_NUM_THREADS=1, MKL_NUM_THREADS=1",
            "success": bool(result.success),
            "status": int(result.status),
            "message": str(result.message),
            "iterations": int(result.nit),
            "constraint_violation_max_mm": rnd(max(0.0, float(-min(seats.min(), 0.0)))),
        },
        "objective": {
            "form": "J = V + kappa*d; V = population variance of the four posed pad centroids "
                    "along their scatter's least principal axis (lambda_min/4); "
                    "d = (trunk_axis . n_hat)^2; pads = mem.bone_08/09/22/23",
            "kappa": rnd(dv.kappa),
            "V_rest_mm2": rnd(dv.V_rest),
            "d_rest": rnd(dv.d_rest),
            "J_rest": rnd(dv.J_rest),
            "V_pose_mm2": rnd(V),
            "d_pose": rnd(d),
            "J_pose": rnd(V + dv.kappa * d),
        },
        "variables": {
            "names": StandingDerivation.VAR_NAMES,
            "x_full": [float(v) for v in x],
            "x_R12": [rnd(v) for v in x],
            "the_pose_of_record": "x_R12 (the house record rounding)",
        },
        "pose_bonds": pose_bonds,
        "derivations": {
            "hip": {s: {"pivot_mm": [rnd(v) for v in dv.hip[s]["c"]],
                         "e1": [rnd(v) for v in dv.hip[s]["e1"]],
                         "e2": [rnd(v) for v in dv.hip[s]["e2"]],
                         "e3": [rnd(v) for v in dv.hip[s]["e3"]],
                         "band_mm": rnd(dv.hip[s]["band"]),
                         "flex_sign_committed": dv.hip[s]["flex_sign"]}
                     for s in ("L", "R")},
            "knee": {s: {"pivot_mm": [rnd(v) for v in dv.knee[s]["M"]],
                          "axis": [rnd(v) for v in dv.knee[s]["axis"]],
                          "sigma": dv.knee[s]["sigma"],
                          "probe_rad": rnd(dv.knee[s]["probe_rad"]),
                          "probe_d_plus_mm": rnd(dv.knee[s]["probe_d_plus_mm"]),
                          "probe_d_minus_mm": rnd(dv.knee[s]["probe_d_minus_mm"])}
                      for s in ("L", "R")},
            "elbow": {s: {"pivot_mm": [rnd(v) for v in dv.elbow[s]["pivot"]],
                           "axis": [rnd(v) for v in dv.elbow[s]["axis"]],
                           "sigma": dv.elbow[s]["sigma"],
                           "forced_theta": rnd(dv.elbow[s]["forced_theta"]),
                           "probe_rad": rnd(dv.elbow[s]["probe_rad"]),
                           "probe_d_plus_mm": rnd(dv.elbow[s]["probe_d_plus_mm"]),
                           "probe_d_minus_mm": rnd(dv.elbow[s]["probe_d_minus_mm"])}
                       for s in ("L", "R")},
            "driver": {s: {"pivot_mm": [rnd(v) for v in dv.driver[s]["c"]],
                            "axis": [rnd(v) for v in dv.driver[s]["axis"]],
                            "band_mm": rnd(dv.driver[s]["band"])}
                        for s in ("L", "R")},
            "trunk_axis": [rnd(v) for v in dv.trunk_axis],
        },
    }

    text = json.dumps(sanitize(record), indent=1, sort_keys=True, ensure_ascii=True) + "\n"
    OUT.write_bytes(text.encode("utf-8"))
    (HERE / "pose.sha256").write_text(hashlib.sha256(text.encode("utf-8")).hexdigest() + "\n")
    print("pose written:", OUT)
    print("solver success:", result.success, "| nit:", result.nit, "|", result.message)
    print("x_R12:", [rnd(v) for v in x])
    print("V: %s -> %s mm2 | d: %s -> %s | J: %s -> %s" % (
        rnd(dv.V_rest), rnd(V), rnd(dv.d_rest), rnd(d), rnd(dv.J_rest), rnd(V + dv.kappa * d)))
    print("seats at pose (mm):", [rnd(s) for s in seats],
          "(headroom vs 3.0 cut: hips L/R then loops A/B: %s)" %
          [rnd(s) for s in seats])
    return 0 if (result.success and seats.min() >= 0.0) else 1


if __name__ == "__main__":
    sys.exit(main())
