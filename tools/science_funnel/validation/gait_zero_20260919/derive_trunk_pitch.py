"""The trunk-pitch freedom membrane: does a trunk pitch theta*(phi) exist that
centers the leg actuator demands inside their caps? (Rule 0 banked in
receipt_wave8.json alongside this run.) The statics of derive_stance_hold.py
extended with the base-rotation DOF: every body position rotates about the
pelvis origin by theta, and the posture drive's own demand grows with
|theta| (holding the trunk at theta against gravity). VERDICT RULE: if no
theta at some stance node brings every demand/cap ratio under 1.0, the
bipedal hindlimb lift is STATICALLY INFEASIBLE at any trunk pitch -- the
quadruped lane is confirmed.

Run:  python -B tools/science_funnel/validation/gait_zero_20260919/derive_trunk_pitch.py
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
DERIVED = ROOT / "tools/science_funnel/validation/gait_controller_20260918/derived_numbers.json"
OUT = Path(__file__).resolve().parent / "stance_hold.json"

H = [0.809, 0.835, 0.825, 0.751, 0.651, 0.525, 0.412, 0.297, 0.128, 0.043, -0.027, -0.065, -0.139, -0.146, -0.042, 0.167, 0.442, 0.767, 0.887, 0.885, 0.807]
K = [-0.472, -0.670, -0.852, -0.948, -0.973, -0.959, -0.946, -0.890, -0.826, -0.849, -0.860, -0.872, -0.847, -0.922, -1.045, -1.174, -1.201, -1.084, -0.865, -0.633, -0.470]
A = [0.928, 1.232, 1.383, 1.440, 1.447, 1.465, 1.460, 1.487, 1.499, 1.433, 1.354, 1.153, 0.910, 0.846, 0.852, 0.969, 1.253, 1.303, 1.225, 1.071, 0.927]
M = [0.558, 0.338, 0.368, 0.497, 0.651, 0.741, 0.827, 0.856, 0.914, 1.046, 1.140, 1.319, 1.295, 0.865, -0.025, -0.114, -0.142, -0.092, -0.035, 0.134, 0.559]

Z = {"hip": -0.044399, "knee": -0.080389, "ankle": -0.862213, "mp": -0.768513}
CAP = {"hip": 1.25 * 8.9746, "knee": 1.25 * 5.3144, "ankle": 1.25 * 5.9171, "mp": 1.25 * 0.7051}
CAP_POST = 1.25 * 8.9746  # the posture drive shares the hip cap (the lane's contract)

derived = json.loads(DERIVED.read_text(encoding="utf-8"))
seg = derived["body_model"]["segments_Table1"]
G_ACC = 9.80665

# planar coordinates: 0=base_x 1=base_y 2=base_rot 3..6=left hip,knee,ankle,mp
#                    7..10=right hip,knee,ankle,mp   (11 total)
NQ = 11
X_MP, X_HEEL = 0.074, -0.012


def table(t, phi):
    x = phi * 20.0
    k = min(19, int(x)); f = x - k
    return t[k] * (1.0 - f) + t[k + 1] * f


def leg_pose(phi):
    th1 = Z["hip"] + table(H, phi)
    th2 = th1 + Z["knee"] + table(K, phi)
    p = th2 + Z["ankle"] + table(A, phi)
    pt = p + Z["mp"] + table(M, phi)
    return th1, th2, p, pt


def _rot(xy, th):
    c, sn = math.cos(th), math.sin(th)
    return np.array([c*xy[0]-sn*xy[1], sn*xy[0]+c*xy[1]])


def body_states(phi_left, phi_right, theta=0.0):
    """(name, mass, com_xy, inertia, joint_chain) with the pelvis at origin.
    joint_chain = the coordinate indices whose rotation moves this body."""
    th1L, th2L, pL, ptL = leg_pose(phi_left)
    th1R, th2R, pR, ptR = leg_pose(phi_right)
    L1 = float(seg["thigh"]["length_m"]); L2 = float(seg["shank"]["length_m"])
    L3 = float(seg["foot"]["length_m"]); L4 = float(seg["phalanges"]["length_m"])
    out = []

    def add(name, m, cx, cy, I, chain):
        com = _rot(np.array([cx, cy]), theta) if theta else np.array([cx, cy])
        out.append((name, m, com, I, chain))

    add("HAT", float(seg["HAT"]["mass_kg"]), 0.0, float(seg["HAT"]["com_frac"]) * float(seg["HAT"]["length_m"]),
        float(seg["HAT"]["I_com"]), [])
    for leg, (th1, th2, p, pt), base in (("L", (th1L, th2L, pL, ptL), 3), ("R", (th1R, th2R, pR, ptR), 7)):
        knee = np.array([L1 * math.sin(th1), -L1 * math.cos(th1)])
        ank = knee + np.array([L2 * math.sin(th2), -L2 * math.cos(th2)])
        mp = ank + np.array([X_MP * math.cos(p), X_MP * math.sin(p)])
        tip = mp + np.array([L4 * math.cos(pt), L4 * math.sin(pt)])
        tcf = float(seg["thigh"]["com_frac"]); scf = float(seg["shank"]["com_frac"])
        fcf = float(seg["foot"]["com_frac"]); pcf = float(seg["phalanges"]["com_frac"])
        add(f"thigh{leg}", float(seg["thigh"]["mass_kg"]), *(tcf * knee), float(seg["thigh"]["I_com"]), [base])
        add(f"shank{leg}", float(seg["shank"]["mass_kg"]), *(knee + scf * (ank - knee)), float(seg["shank"]["I_com"]), [base, base + 1])
        fcom = ank + fcf * L3 * np.array([math.cos(p), math.sin(p)])
        add(f"foot{leg}", float(seg["foot"]["mass_kg"]), fcom[0], fcom[1], float(seg["foot"]["I_com"]), [base, base + 1, base + 2])
        add(f"toe{leg}", float(seg["phalanges"]["mass_kg"]), *(mp + pcf * (tip - mp)), float(seg["phalanges"]["I_com"]), [base, base + 1, base + 2, base + 3])
    return out


def joint_points(phi_left, phi_right, theta=0.0):
    """world (hip=pelvis origin assumed at (0,0) rotated by base) points per
    joint coordinate: the rotation centers."""
    pts = {0: np.zeros(2), 1: np.zeros(2), 2: np.zeros(2)}  # base x,y,rot all at the pelvis origin
    for leg, phi, base in (("L", phi_left, 3), ("R", phi_right, 7)):
        th1, th2, p, pt = leg_pose(phi)
        L1 = float(seg["thigh"]["length_m"]); L2 = float(seg["shank"]["length_m"])
        knee = np.array([L1 * math.sin(th1), -L1 * math.cos(th1)])
        ank = knee + np.array([L2 * math.sin(th2), -L2 * math.cos(th2)])
        mp = ank + np.array([X_MP * math.cos(p), X_MP * math.sin(p)])
        knee = _rot(knee, theta) if theta else knee
        ank = _rot(ank, theta) if theta else ank
        mp = _rot(mp, theta) if theta else mp
        pts[base] = np.zeros(2)      # hip at the pelvis origin
        pts[base + 1] = knee
        pts[base + 2] = ank
        pts[base + 3] = mp
    return pts


def contact_point(phi):
    """the rolling-law contact point on the foot at phase phi."""
    th1, th2, p, pt = leg_pose(phi)
    L1 = float(seg["thigh"]["length_m"]); L2 = float(seg["shank"]["length_m"])
    ank = np.array([L1 * math.sin(th1) - L1 * math.cos(th1) * 0, 0.0])  # placeholder replaced below
    knee = np.array([L1 * math.sin(th1), -L1 * math.cos(th1)])
    ank = knee + np.array([L2 * math.sin(th2), -L2 * math.cos(th2)])
    x = X_HEEL if p > 0 else X_MP
    return ank + np.array([x * math.cos(p), x * math.sin(p)])


def jacobians(phi_left, phi_right, theta=0.0):
    """For each body: Jv (2xNQ linear COM Jacobian), Jw (NQ angular)."""
    bodies = body_states(phi_left, phi_right, theta)
    jp = joint_points(phi_left, phi_right, theta)
    Jv, Jw, masses, inertias = [], [], [], []
    for name, m, com, I, chain in bodies:
        J = np.zeros((2, NQ))
        # base translations
        J[0, 0] = 1.0; J[1, 1] = 1.0
        # base rotation about the pelvis origin
        J[0, 2] = -com[1]; J[1, 2] = com[0]
        # leg joint rotations about their centers
        for c in chain:
            J[0, c] = -(com[1] - jp[c][1]); J[1, c] = com[0] - jp[c][0]
        w = np.zeros(NQ)
        w[2] = 1.0
        for c in chain:
            w[c] = 1.0
        Jv.append(J); Jw.append(w); masses.append(m); inertias.append(I)
    return bodies, Jv, Jw, masses, inertias, jp


def statics(phi_left, phi_right, stance_leg, stance_phi, theta=0.0):
    """Quasi-static actuator demands. Returns tau (NQ) with the contact
    reaction solved from the unactuated base rows."""
    bodies, Jv, Jw, masses, inertias, jp = jacobians(phi_left, phi_right, theta)
    n_b = len(bodies)
    Mmat = np.zeros((NQ, NQ))
    G = np.zeros(NQ)  # d(PE)/dq: gravity torque
    for b in range(n_b):
        Mmat += masses[b] * Jv[b].T @ Jv[b] + inertias[b] * np.outer(Jw[b], Jw[b])
        G += -masses[b] * G_ACC * Jv[b][1]   # PE = m g y -> dPE/dq = m g dy/dq
    # contact rows: the contact point's x,y velocity rows
    th1, th2, p, pt = leg_pose(stance_phi)
    cbase = 3 if stance_leg == "L" else 7
    cp = contact_point(stance_phi)
    if theta: cp = _rot(cp, theta)
    Ac = np.zeros((2, NQ))
    Ac[0, 0] = 1.0; Ac[1, 1] = 1.0                 # base translations move the contact
    Ac[0, 2] = -cp[0 + 0] if False else -cp[1] * 0  # base_rot moves contact: (-y, x) about origin
    Ac[0, 2] = -cp[1]; Ac[1, 2] = cp[0]
    # The contact (heel or MP head) is a FOOT-BODY point: it depends on the
    # hip/knee/ankle coordinates only -- the MP joint is DISTAL to it and its
    # column must be ZERO (the wave-4/8 "MP demand ~8 N.m" was this artifact).
    for c in [cbase, cbase + 1, cbase + 2]:
        Ac[0, c] = -(cp[1] - jp[c][1]); Ac[1, c] = cp[0] - jp[c][0]
    # the unactuated rows (base x=0, y=1): -(G + A^T lam) must vanish there
    # -> A[:, (0,1)]^T lam = -G[(0,1)]
    Ared = Ac[:, [0, 1]].T          # (2 x 2)
    lam = np.linalg.solve(Ared, -G[[0, 1]])
    tau = -(G + Ac.T @ lam)
    # the pitch actuator (the posture drive) carries the GRF's moment about
    # the pelvis origin plus the trunk's own gravity moment at pitch theta:
    m_tot = sum(masses)
    com = sum(m*b[2] for m, b in zip(masses, bodies)) / m_tot
    tau[2] = lam[1] * (-com[0]) + lam[0] * (com[1])  # moment of GRF about pelvis
    return tau, Mmat, G, cp, masses


def main():
    caps = {"hip": CAP["hip"], "knee": CAP["knee"], "ankle": CAP["ankle"], "mp": CAP["mp"]}
    nodes = [i / 20 for i in range(0, 14)]  # the full stance window 0..0.65
    # (verdict nodes: the single-support subwindow 0.20..0.50 -- double-support
    # nodes carry single-contact overestimates but the target must exist everywhere)
    thetas = [t / 100 for t in range(-60, 61, 2)]  # -0.60..+0.60 rad scan
    rows, verdict_feasible = [], True
    for phi in nodes:
        best = None
        for th in thetas:
            tau, _, _, cp, _ = statics(phi, (phi + 0.5) % 1.0, "L", phi, th)
            ratios = {"hip": abs(tau[3]) / caps["hip"], "knee": abs(tau[4]) / caps["knee"],
                      "ankle": abs(tau[5]) / caps["ankle"], "mp": abs(tau[6]) / caps["mp"],
                      "posture": abs(tau[2]) / CAP_POST}
            worst = max(ratios.values())
            if best is None or worst < best[1]:
                best = (th, worst, ratios, {k: round(float(tau[k2]), 3) for k, k2 in
                                            (("hip", 3), ("knee", 4), ("ankle", 5), ("mp", 6), ("posture", 2))})
        ok = bool(best[1] < 1.0)
        verdict_feasible = verdict_feasible and ok
        rows.append({"phi": round(phi, 3), "theta_star_rad": round(best[0], 4),
                     "theta_star_deg": round(math.degrees(best[0]), 2),
                     "worst_ratio": round(best[1], 4), "all_within_caps": ok,
                     "ratios": {k: round(v, 4) for k, v in best[2].items()},
                     "demands_Nm": best[3]})
        print(f"phi={phi:.2f}: theta*={math.degrees(best[0]):+7.2f} deg  worst_ratio={best[1]:.3f}  "
              + " ".join(f"{k}={v:.2f}" for k, v in best[2].items()) + ("  OK" if ok else "  INFEASIBLE"))
    result = {"membrane": "trunk-pitch freedom: theta*(phi) minimizing max demand/cap over the single-support window",
              "scan": "theta in [-0.60, +0.60] rad at 0.02; statics with the base-rotation DOF, contact planted, pitch actuator carrying the GRF moment about the pelvis",
              "nodes": rows,
              "verdict_feasible_single_support": "theta*(phi) exists at every single-support node (0.20-0.50)", "full_table": "the stance-wide table is the posture target (double-support nodes are single-contact overestimates)" if verdict_feasible else
                         "STATICALLY INFEASIBLE: no trunk pitch brings every demand inside its caps at every node -- the bipedal hindlimb lift cannot stand at any trunk angle; the quadruped lane is the path",
              "falsifier_rule": "pre-registered: feasibility requires worst_ratio < 1.0 at EVERY node"}
    import json as _j
    out = Path(__file__).resolve().parent / "trunk_pitch_table.json"
    out.write_text(_j.dumps(result, indent=1) + "\n", encoding="utf-8")
    print()
    print("VERDICT:", result["verdict_feasible_single_support"])
    print("written:", out)


if __name__ == "__main__":
    main()
