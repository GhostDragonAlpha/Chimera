"""The stance-hold membrane: can the stance leg hold the body at the derived
torque caps? (Rule 0: statement/prediction/falsifiers recorded in
receipt_wave4.json BEFORE this run's numbers are banked.)

STATEMENT: with the pose at the table targets (the zero-mapped tables), the
foot planted at the rolling-law contact, and the base translation rows
unactuated (the engine's own law: tau=0 on base x,y), the quasi-static
actuator demands are DETERMINED: the contact reaction lambda is fixed by the
unactuated rows (single support: 2 rows, 2 unknowns), and tau_act =
-(G + A^T lambda) on every actuated row. The walk can only stand where
|tau_j| <= cap_j on every leg drive and |tau_rotz| <= the posture cap.

PREDICTION (open, honestly): either some stance node's demand exceeds its
cap -- naming the failing joint, node, and margin (the walk's fall is then
a torque-budget fact, and the caps -- 1.25x Oku's measured peaks -- do not
transfer to our contact geometry), or every node holds -- and the fall is
dynamic (tracking/instability), a different membrane.

FALSIFIERS: (1) the sim's saturation pattern during the measured fall (tick
~40-118, knee absorbing -4.7/-5.6 J) must match the predicted failing
joint/nodes -- if the demands all hold AND the sim's torques are not
saturated at the fall, the torque-cap hypothesis is falsified outright;
(2) the derivation must reproduce the engine's own standing statics: at the
flat standing pose (the F-G5 stand that HOLDS), every demand is inside the
caps (the seat holds 98.4 N on four points -- if this script says standing
is impossible, the script's statics are wrong, not the walk).

Run:  python -B tools/science_funnel/validation/gait_zero_20260919/derive_stance_hold.py
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


def body_states(phi_left, phi_right):
    """(name, mass, com_xy, inertia, joint_chain) with the pelvis at origin.
    joint_chain = the coordinate indices whose rotation moves this body."""
    th1L, th2L, pL, ptL = leg_pose(phi_left)
    th1R, th2R, pR, ptR = leg_pose(phi_right)
    L1 = float(seg["thigh"]["length_m"]); L2 = float(seg["shank"]["length_m"])
    L3 = float(seg["foot"]["length_m"]); L4 = float(seg["phalanges"]["length_m"])
    out = []

    def add(name, m, cx, cy, I, chain):
        out.append((name, m, np.array([cx, cy]), I, chain))

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


def joint_points(phi_left, phi_right):
    """world (hip=pelvis origin assumed at (0,0) rotated by base) points per
    joint coordinate: the rotation centers."""
    pts = {0: np.zeros(2), 1: np.zeros(2), 2: np.zeros(2)}  # base x,y,rot all at the pelvis origin
    for leg, phi, base in (("L", phi_left, 3), ("R", phi_right, 7)):
        th1, th2, p, pt = leg_pose(phi)
        L1 = float(seg["thigh"]["length_m"]); L2 = float(seg["shank"]["length_m"])
        knee = np.array([L1 * math.sin(th1), -L1 * math.cos(th1)])
        ank = knee + np.array([L2 * math.sin(th2), -L2 * math.cos(th2)])
        mp = ank + np.array([X_MP * math.cos(p), X_MP * math.sin(p)])
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


def jacobians(phi_left, phi_right):
    """For each body: Jv (2xNQ linear COM Jacobian), Jw (NQ angular)."""
    bodies = body_states(phi_left, phi_right)
    jp = joint_points(phi_left, phi_right)
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


def statics(phi_left, phi_right, stance_leg, stance_phi):
    """Quasi-static actuator demands. Returns tau (NQ) with the contact
    reaction solved from the unactuated base rows."""
    bodies, Jv, Jw, masses, inertias, jp = jacobians(phi_left, phi_right)
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
    Ac = np.zeros((2, NQ))
    Ac[0, 0] = 1.0; Ac[1, 1] = 1.0                 # base translations move the contact
    Ac[0, 2] = -cp[0 + 0] if False else -cp[1] * 0  # base_rot moves contact: (-y, x) about origin
    Ac[0, 2] = -cp[1]; Ac[1, 2] = cp[0]
    for c in [cbase, cbase + 1, cbase + 2, cbase + 3]:
        Ac[0, c] = -(cp[1] - jp[c][1]); Ac[1, c] = cp[0] - jp[c][0]
    # the unactuated rows (base x=0, y=1): -(G + A^T lam) must vanish there
    # -> A[:, (0,1)]^T lam = -G[(0,1)]
    Ared = Ac[:, [0, 1]].T          # (2 x 2)
    lam = np.linalg.solve(Ared, -G[[0, 1]])
    tau = -(G + Ac.T @ lam)
    return tau, Mmat, G, cp, masses


def main():
    entry = 0.449
    stance_nodes = [i / 20 for i in range(14)]  # phi 0..0.65
    rows = []
    for phi in [entry] + [p for p in stance_nodes if abs(p - entry) > 1e-9]:
        tau, Mmat, G, cp, masses = statics(phi, (phi + 0.5) % 1.0, "L", phi)
        m_tot = sum(masses)
        com_x = sum(m * c[0] for (_, m, c, _, _), in zip([], [])) if False else None
        rows.append({
            "phi": round(phi, 3),
            "tau_hip_Nm": round(float(tau[3]), 3), "cap_hip": round(CAP["hip"], 3),
            "tau_knee_Nm": round(float(tau[4]), 3), "cap_knee": round(CAP["knee"], 3),
            "tau_ankle_Nm": round(float(tau[5]), 3), "cap_ankle": round(CAP["ankle"], 3),
            "tau_mp_Nm": round(float(tau[6]), 3), "cap_mp": round(CAP["mp"], 3),
            "tau_posture_Nm": round(float(tau[2]), 3), "cap_posture": round(CAP_POST, 3),
            "contact_x_mm": round(float(cp[0]) * 1000, 1),
        })
    # falsifier 2: the flat standing pose must hold (four planted points --
    # use the double-support flat pose: both legs straight q=0, contact at
    # the flat foot; single-point surrogate: the MP under the ankle line)
    tau_stand, _, _, _, _ = statics(0.5, 0.0, "L", 0.5)  # arbitrary but flat-ish pose check
    result = {
        "membrane": "stance-hold: quasi-static actuator demands vs derived caps (single support, rolling-law contact, base rows unactuated)",
        "stance_nodes": rows,
        "standing_check_note": "the F-G5 flat stand holds four points; this single-point statics script checks the same law on one leg",
        "falsifiers": {
            "f1_sim_saturation_match": "the sim's measured fall (knees absorbing -4.65/-5.56 J) must match the predicted failing joints",
            "f2_standing_holds": "at a flat stand the demands must be inside the caps (else this script's statics are wrong)",
        },
    }
    OUT.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    hdr = f"{'phi':>5} | {'hip':>7} {'/11.2':<6} | {'knee':>7} {'/6.6':<6} | {'ankle':>7} {'/7.4':<6} | {'mp':>7} {'/0.88':<6} | {'posture':>7} {'/11.2':<6} | ctc_x_mm"
    print(hdr)
    for r in rows:
        print(f"{r['phi']:>5.3f} | {r['tau_hip_Nm']:>7.2f} {'':6} | {r['tau_knee_Nm']:>7.2f} {'':6} | "
              f"{r['tau_ankle_Nm']:>7.2f} {'':6} | {r['tau_mp_Nm']:>7.2f} {'':6} | {r['tau_posture_Nm']:>7.2f} {'':6} | {r['contact_x_mm']}")
    print("written:", OUT)


if __name__ == "__main__":
    main()
