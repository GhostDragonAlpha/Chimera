"""A5 — re-derive the Candidate-C fitting-section violations from recorded data.

Uses the recorded optimum (db, dc) from experiment_transverse_candidate.json and the
objective as implemented in experiment_transverse_fit.py L265-273 (+L246: the NOMINAL
session-4 hull at each of the three fitting sections), re-evaluated with the
rebuilt sites/frame from reproduce.py's method (recorded fitted_pos_global + pack frame).
"""
import json
import sys

import numpy as np

sys.path.insert(0, "work")
from target_envelope import _dist_to_poly  # noqa: E402
from mesh_target import MonkeyTarget  # noqa: E402

BASE = r"E:/PythonChimera/forearm_package/baseline_snapshot"
MARGIN = 0.001
LAMBDA_RIDGE = 1e-2
BODIES = {"radius": ("elbow_R", "wrist_R"), "radius_l": ("elbow_L", "wrist_L")}

fit = json.load(open(BASE + "/runs/actual_monkey_fit.json"))
exp = json.load(open(BASE + "/runs/experiment_transverse_candidate.json"))
mt = MonkeyTarget(birth_path=BASE + "/inputs/monkey_birth.bin", pack_path=BASE + "/inputs/monkey_joints.bin")


def _unit(v):
    return v / np.linalg.norm(v)


def _band_roll(mt, prox_joint, P, a):
    verts = mt.band_verts(prox_joint)
    rel = verts - P
    perp = rel - np.outer(rel @ a, a)
    return verts[int(np.argmax((perp ** 2).sum(axis=1)))].copy()


def onb_from_points(p0, p1, q):
    a = _unit(p1 - p0)
    t = (q - p0) - a * (a @ (q - p0))
    b = _unit(t)
    return a, b, np.cross(a, b)


grand = {}
for body, (pj, dj) in BODIES.items():
    P = mt.joint_pos(pj)
    P_d = mt.joint_pos(dj)
    a_un = P_d - P
    L = float(np.linalg.norm(a_un))
    a_dir = a_un / L
    _, bu, cu = onb_from_points(P, P_d, _band_roll(mt, pj, P, a_un))
    sites_bc = []
    for s in fit["sites"]:
        if s["segment"] != body or s["unresolved"]:
            continue
        rel = np.asarray(s["fitted_pos_global"]) - P
        sites_bc.append({"name": s["name"], "axial": float(rel @ a_dir),
                         "b": float(rel @ bu), "c": float(rel @ cu)})
    hulls = {s["t"]: np.asarray(s["hull_bc"])
             for s in fit["measurements"]["outer_envelope"][body]["sections"]}
    db = exp["step_C_candidate"][body]["db_m"]
    dc = exp["step_C_candidate"][body]["dc_m"]
    ridge = LAMBDA_RIDGE * (db * db + dc * dc)
    rec_j = exp["step_C_candidate"][body]["objective_m2"]
    viol = []
    for s in sites_bc:
        for t, poly in hulls.items():
            d = _dist_to_poly(s["b"] + db, s["c"] + dc, poly)
            v = max(0.0, MARGIN - (-d))
            if v > 0:
                viol.append((s["name"], t, v))
    l1 = sum(v for _, _, v in viol)
    l2 = (sum(v * v for _, _, v in viol)) ** 0.5
    j_re = ridge + sum(v * v for _, _, v in viol)
    print(f"=== {body}: db={db} dc={dc} ===")
    print(f"  ridge term       = {ridge:.6e} m^2")
    print(f"  recorded objective = {rec_j:.6e} m^2")
    print(f"  recomputed objective = {j_re:.6e} m^2  (delta {abs(j_re-rec_j):.2e})")
    print(f"  violations: n={len(viol)}  L1(sum)={l1*1e6:.2f} um  L2(norm)={l2*1e6:.2f} um  max={max(v for _,_,v in viol)*1e6:.2f} um")
    for n, t, v in sorted(viol, key=lambda x: -x[2]):
        print(f"    {n:12s} t={t}: shortfall {v*1e6:7.2f} um below the -1mm margin")
    grand[body] = {"violations": [(n, t, v) for n, t, v in viol], "L1_um": l1 * 1e6, "L2_um": l2 * 1e6,
                   "j_recomputed": j_re, "j_recorded": rec_j}

print()
print("session-05 4-C prose: 'fitting sections violated by ~41 um total'")
json.dump(grand, open("receipts/candidate41.json", "w"), indent=1)
print("receipt -> receipts/candidate41.json")
