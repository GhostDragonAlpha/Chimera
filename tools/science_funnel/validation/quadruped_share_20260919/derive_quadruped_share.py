"""The quadruped load-share membrane: how much margin do forelimbs buy the
hindlimbs, at what share? (Rule 0: statement/prediction/falsifiers banked in
receipt_quadruped_share.json alongside this run's numbers; the machinery is
derive_stance_hold.py at the MP-Jacobian-corrected tip fdc74523, extended --
no engine files, pure Python derivation.)

STATEMENT: with a forelimb pair sharing the load at fore share s, every
hindlimb demand/cap ratio falls below the bipedal worst by at least the
share itself (at fixed pose the hind demands are EXACTLY affine in s --
the load-share model's sharp form, verified numerically below).

PREDICTION: at the macaque's measured fore share (s ~ 0.4-0.55 of body
weight in quadrupedal stance), the hindlimb worst demand/cap ratio drops
below 0.6 (operational margin, not 5%).

FALSIFIERS: (1) the relief must be monotone in s -- non-monotone points
falsify the load-share model (evaluated on the signed demands, which the
model constrains to be affine in s; ratio non-monotonicity at a signed
zero-crossing is reported as such, not silently); (2) the forelimb's OWN
demands (same statics machinery on the forelimb chain) must stay within
caps scaled by their segment sizes -- if the forelimb demands exceed any
plausible cap, the quadruped trades one infeasibility for another, and
that is the finding.

Forelimb provenance (docs/research/20260918_monkey_assembly_derivation.md):
arm chain mass 0.406001 kg/side (model.anatomy.macaque_arm, measured);
bone lengths humerus 0.125 m, forearm 0.132 m and elbow flexion 66.74 deg
(sec 3.1, Janisch cercopithecoid ensemble); hip-to-shoulder closure
(0.2689, -0.1331) m (sec 3.1, trunk pitch 26.33 deg); doc-derived fore
share 2x34.18/98.44 = 0.6944 (sec 3.2). The doc carries NO per-segment
arm masses (its arm is 11 bodies / 7 coordinates, admitted as a whole), so
the per-segment split is DERIVED, not measured: the hindlimb Table-1
thigh:shank mass proportion 0.557:0.269 is transferred to the fore
humerus:forearm pair, giving humerus 0.2737 kg @ 0.125 m and forearm
0.1323 kg @ 0.132 m. The documented fore lengths are retained directly;
COM fractions inherit the hind chain's convention (0.41/0.40), and
inertias are slender-rod I = mL^2/12.
The 2-segment planar chain (shoulder+elbow) is the doc's own Stage-A
qualified mounted-arm reduction; the paw is welded to the forearm segment
and contacts at its distal tip. Plant rule: paw tip target directly below
the shoulder (tenability-optimal l = 0, the doc's sec 3.3 window is
l <= 0.110 m) at the hind contact's height; the reach residual is solved
on a grid over (shoulder, elbow) angles in declared bands and REPORTED,
never silently absorbed.

Caps: hind = 1.25x Oku measured peaks (the lane's contract, unchanged).
Fore caps scale by the driven segment's mass x length product (the same
product that builds the gravitational demand), normalized to the hind
chain's hip/thigh and knee/shank pairs:
  cap_shoulder = 11.218 x (0.2436006x0.118756)/(0.557x0.163) = 3.575 N.m
  cap_elbow    =  6.643 x (0.1624004x0.102679)/(0.269x0.182) = 2.263 N.m
with the doc's own triceps capacity 3.76 N.m (sec 3.3) carried as the
muscle-anchored cross-check on the elbow.

Run:  python -B tools/science_funnel/validation/quadruped_share_20260919/derive_quadruped_share.py
"""
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
DERIVED = ROOT / "tools/science_funnel/validation/gait_controller_20260918/derived_numbers.json"
OUT = Path(__file__).resolve().parent / "quadruped_share.json"

H = [0.809, 0.835, 0.825, 0.751, 0.651, 0.525, 0.412, 0.297, 0.128, 0.043, -0.027, -0.065, -0.139, -0.146, -0.042, 0.167, 0.442, 0.767, 0.887, 0.885, 0.807]
K = [-0.472, -0.670, -0.852, -0.948, -0.973, -0.959, -0.946, -0.890, -0.826, -0.849, -0.860, -0.872, -0.847, -0.922, -1.045, -1.174, -1.201, -1.084, -0.865, -0.633, -0.470]
A = [0.928, 1.232, 1.383, 1.440, 1.447, 1.465, 1.460, 1.487, 1.499, 1.433, 1.354, 1.153, 0.910, 0.846, 0.852, 0.969, 1.253, 1.303, 1.225, 1.071, 0.927]
M = [0.558, 0.338, 0.368, 0.497, 0.651, 0.741, 0.827, 0.856, 0.914, 1.046, 1.140, 1.319, 1.295, 0.865, -0.025, -0.114, -0.142, -0.092, -0.035, 0.134, 0.559]

Z = {"hip": -0.044399, "knee": -0.080389, "ankle": -0.862213, "mp": -0.768513}
CAP = {"hip": 1.25 * 8.9746, "knee": 1.25 * 5.3144, "ankle": 1.25 * 5.9171, "mp": 1.25 * 0.7051}
CAP_POST = 1.25 * 8.9746  # the posture drive shares the hip cap (the lane's contract)

G_ACC = 9.80665

# ---- forelimb derivation (declared, parameter-free given the doc) ----
M_ARM = 0.406001                     # kg/side, measured (macaque_arm effective segments)
L_HUM_DOC, L_FARM_DOC = 0.125, 0.132 # m, doc sec 3.1 (Janisch ensemble)
HIND_THIGH_M, HIND_SHANK_M = 0.557, 0.269         # admitted hind Table-1 masses
M_HUM = M_ARM * HIND_THIGH_M / (HIND_THIGH_M + HIND_SHANK_M)
M_FARM = M_ARM * HIND_SHANK_M / (HIND_THIGH_M + HIND_SHANK_M)
L_HUM, L_FARM = L_HUM_DOC, L_FARM_DOC           # documented fore lengths, retained directly
I_HUM = M_HUM * L_HUM ** 2 / 12.0    # slender rod about COM (declared)
I_FARM = M_FARM * L_FARM ** 2 / 12.0
CF_HUM, CF_FARM = 0.41, 0.40         # COM fractions: the hind chain's convention (declared)
MOUNT = np.array([0.2689, -0.1331])  # doc sec 3.1 hip->shoulder closure (declared)

CAP_SHOULDER = CAP["hip"] * (M_HUM * L_HUM) / (0.557 * 0.163)
CAP_ELBOW = CAP["knee"] * (M_FARM * L_FARM) / (0.269 * 0.182)
CAP_ELBOW_DOC = 3.76                 # doc sec 3.3 triceps capacity (muscle-anchored cross-check)

S_GRID = [0.0, 0.25, 0.4, 0.55, 0.6944]  # mission grid + the doc-derived fore share
S_DOC = 0.6944
NODES = [i / 20 for i in range(14)]       # stance window 0..0.65 (the vault scan's nodes)
SS = [p for p in NODES if 0.20 - 1e-9 <= p <= 0.50 + 1e-9]  # single-support subwindow
THETAS = [t / 100 for t in range(-60, 61)]  # -0.60..+0.60 rad at 0.01 (the vault scan's grid, doubled resolution)
A_BAND = (-1.2, 1.2)   # shoulder angle from vertical (body frame), rad
B_BAND = (-1.2, 1.2)   # forearm angle from vertical (body frame), rad
INT_BAND = (1.75, 2.44)  # ELBOW INTERNAL angle band rad (Janisch TD 127.4 deg, doc stand 113.3 deg inside)

derived = json.loads(DERIVED.read_text(encoding="utf-8"))
seg = derived["body_model"]["segments_Table1"]
HAT_FULL = float(seg["HAT"]["mass_kg"])          # 8.184 (Oku row, forelimbs inside)
HAT_EFF = HAT_FULL - 2 * M_ARM                   # 7.371998 (the doc's carve-out)
W_FULL = (HAT_EFF + 2 * M_ARM + 2 * 0.927) * G_ACC   # 98.44 N (the doc's assembly total)
W_BIPED = (HAT_EFF + 2 * 0.927) * G_ACC              # carved-out biped, fore absent


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
    return np.array([c * xy[0] - sn * xy[1], sn * xy[0] + c * xy[1]])


X_MP, X_HEEL = 0.074, -0.012


def contact_point(phi):
    """the rolling-law contact point on the hind foot at phase phi (body frame)."""
    th1, th2, p, pt = leg_pose(phi)
    L1 = float(seg["thigh"]["length_m"]); L2 = float(seg["shank"]["length_m"])
    knee = np.array([L1 * math.sin(th1), -L1 * math.cos(th1)])
    ank = knee + np.array([L2 * math.sin(th2), -L2 * math.cos(th2)])
    x = X_HEEL if p > 0 else X_MP
    return ank + np.array([x * math.cos(p), x * math.sin(p)])


def solve_fore_pose(phi):
    """Paw-tip plant: target directly below the shoulder (l=0) at the hind
    contact's height (in the BODY frame the ground plane is y = cp.y -- a
    rigid whole-body rotation preserves internal geometry, so the solve is
    theta-independent). Grid + refinement over (a, b) in the declared bands
    with the ELBOW INTERNAL angle (pi - |a - b|) constrained to INT_BAND
    (Janisch TD/doc stand inside); of the (mirrored) solutions the
    straighter arm (larger internal angle, the doc's sec-3.3 tenability
    branch -- half the elbow lever) wins ties."""
    cp = contact_point(phi)
    target = np.array([MOUNT[0], cp[1]])

    def miss(a, b):
        elbow = MOUNT + L_HUM * np.array([math.sin(a), -math.cos(a)])
        tip = elbow + L_FARM * np.array([math.sin(b), -math.cos(b)])
        internal = math.pi - abs(a - b)
        pen = max(0.0, INT_BAND[0] - internal) + max(0.0, internal - INT_BAND[1])
        d = tip - target
        # lexicographic: internal-angle slack first (posture legality),
        # then the tip plant residual (10:1 vertical, 1:1 horizontal)
        return (pen, 10.0 * d[1] ** 2 + d[0] ** 2), elbow, tip, internal

    best = None
    for a in np.arange(A_BAND[0], A_BAND[1] + 1e-9, 0.05):
        for b in np.arange(B_BAND[0], B_BAND[1] + 1e-9, 0.05):
            e = miss(a, b)
            if best is None or e[0] < best[0]:
                best = e + (a, b)
    for step in (0.01, 0.002):
        a0, b0 = best[4], best[5]
        for a in np.arange(a0 - step, a0 + step + 1e-9, step / 5):
            for b in np.arange(b0 - step, b0 + step + 1e-9, step / 5):
                if not (A_BAND[0] <= a <= A_BAND[1] and B_BAND[0] <= b <= B_BAND[1]):
                    continue
                e = miss(a, b)
                if e[0] < best[0]:
                    best = e + (a, b)
    err, elbow, tip, internal, a, b = best
    return {"a": float(a), "b": float(b), "elbow": elbow, "tip": tip,
            "internal_rad": float(internal), "internal_deg": round(math.degrees(internal), 1),
            "miss_mm": float(np.linalg.norm(tip - target) * 1000),
            "target": target}


def body_states(phi_left, phi_right, theta, fore, with_fore, hat_mass):
    """(name, mass, com_xy(body frame), inertia, joint_chain). The fore chain
    rides only if with_fore (the biped baselines exclude it entirely)."""
    L1 = float(seg["thigh"]["length_m"]); L2 = float(seg["shank"]["length_m"])
    L3 = float(seg["foot"]["length_m"]); L4 = float(seg["phalanges"]["length_m"])
    out = []

    def add(name, m, cx, cy, I, chain):
        out.append((name, m, np.array([cx, cy]), I, chain))

    add("HAT", hat_mass, 0.0, float(seg["HAT"]["com_frac"]) * float(seg["HAT"]["length_m"]),
        float(seg["HAT"]["I_com"]), [])
    for leg, phi, base in (("L", phi_left, 3), ("R", phi_right, 7)):
        th1, th2, p, pt = leg_pose(phi)
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
    if with_fore:
        elbow, tipf = fore["elbow"], fore["tip"]
        for leg, fb in (("L", 11), ("R", 13)):  # mirrored chain, identical pose -> identical rows
            up_com = MOUNT + CF_HUM * (elbow - MOUNT)
            fa_com = elbow + CF_FARM * (tipf - elbow)
            add(f"upperarm{leg}", M_HUM, up_com[0], up_com[1], I_HUM, [fb])
            add(f"forearm{leg}", M_FARM, fa_com[0], fa_com[1], I_FARM, [fb, fb + 1])
    return out


def joint_points(phi_left, phi_right, theta, fore, with_fore):
    L1 = float(seg["thigh"]["length_m"]); L2 = float(seg["shank"]["length_m"])
    pts = {0: np.zeros(2), 1: np.zeros(2), 2: np.zeros(2)}
    for leg, phi, base in (("L", phi_left, 3), ("R", phi_right, 7)):
        th1, th2, p, pt = leg_pose(phi)
        knee = np.array([L1 * math.sin(th1), -L1 * math.cos(th1)])
        ank = knee + np.array([L2 * math.sin(th2), -L2 * math.cos(th2)])
        mp = ank + np.array([X_MP * math.cos(p), X_MP * math.sin(p)])
        pts[base] = np.zeros(2)
        pts[base + 1] = knee
        pts[base + 2] = ank
        pts[base + 3] = mp
    if with_fore:
        for leg, fb in (("L", 11), ("R", 13)):
            pts[fb] = MOUNT.copy()
            pts[fb + 1] = fore["elbow"]
    return pts


def statics(phi_left, phi_right, stance_leg, stance_phi, s, theta, fore, with_fore, hat_mass):
    """Quasi-static demands with the weight split by share s between the hind
    contact (single support, (1-s)*W) and the two fore paw tips (s*W/2 each,
    vertical). The base x/y rows are unactuated and satisfied exactly by the
    prescribed split (verified as residuals); every torque is EXACTLY affine
    in s at fixed pose. Contact columns follow the MP-Jacobian-corrected
    convention: a contact point is a point of its DISTAL body -- the hind
    contact (heel/MP head, on the foot body) gets hip/knee/ankle columns
    only; the paw tip (on the forearm body) gets shoulder/elbow columns
    only; MP and (nonexistent here) distal wrist columns stay zero."""
    NQ = 15
    bodies = body_states(phi_left, phi_right, theta, fore, with_fore, hat_mass)
    jp = joint_points(phi_left, phi_right, theta, fore, with_fore)
    Jv, Jw, masses, inertias = [], [], [], []
    for name, m, com_b, I, chain in bodies:
        com = _rot(com_b, theta)
        J = np.zeros((2, NQ))
        J[0, 0] = 1.0; J[1, 1] = 1.0
        J[0, 2] = -com[1]; J[1, 2] = com[0]
        for c in chain:
            jw = _rot(jp[c], theta)
            J[0, c] = -(com[1] - jw[1]); J[1, c] = com[0] - jw[0]
        w = np.zeros(NQ)
        w[2] = 1.0
        for c in chain:
            w[c] = 1.0
        Jv.append(J); Jw.append(w); masses.append(m); inertias.append(I)
    G = np.zeros(NQ)
    for b in range(len(bodies)):
        G += -masses[b] * G_ACC * Jv[b][1]

    cp_h_b = contact_point(stance_phi)
    cp_h = _rot(cp_h_b, theta)
    cbase = 3 if stance_leg == "L" else 7
    Ac = np.zeros((6, NQ))

    def contact_rows(row, cp, chain_cols):
        Ac[row, 0] = 1.0; Ac[row + 1, 1] = 1.0
        Ac[row, 2] = -cp[1]; Ac[row + 1, 2] = cp[0]
        for c in chain_cols:
            jw = _rot(jp[c], theta)
            Ac[row, c] = -(cp[1] - jw[1]); Ac[row + 1, c] = cp[0] - jw[0]

    contact_rows(0, cp_h, [cbase, cbase + 1, cbase + 2])          # hind: foot-body point, NO mp column
    if with_fore:
        for k, fb in ((2, 11), (4, 13)):                           # paw tips: forearm-body points
            tip_w = _rot(fore["tip"], theta)
            contact_rows(k, tip_w, [fb, fb + 1])
    W = sum(masses) * G_ACC
    lam = np.zeros(6)
    lam[1] = -(1.0 - s) * W           # hind contact carries (1-s) of the body weight
    if with_fore:
        lam[3] = lam[5] = -s * W / 2.0    # each fore paw carries s/2
    tau = -(G + Ac.T @ lam)
    resid = [float(G[0] + Ac[0, 0] * lam[0] + Ac[2, 0] * lam[2] + Ac[4, 0] * lam[4]),
             float(G[1] + lam[1] + lam[3] + lam[5])]
    return tau, cp_h, masses, resid, W


def ratios_of(tau, with_fore):
    r = {"hip": abs(tau[3]) / CAP["hip"], "knee": abs(tau[4]) / CAP["knee"],
         "ankle": abs(tau[5]) / CAP["ankle"], "mp": abs(tau[6]) / CAP["mp"],
         "posture": abs(tau[2]) / CAP_POST}
    if with_fore:
        r["shoulder"] = abs(tau[11]) / CAP_SHOULDER
        r["elbow"] = abs(tau[12]) / CAP_ELBOW
    return r


def scan_theta(phi, s, fore, with_fore, hat_mass, rows_key):
    """theta* minimax over the requested ratio rows; returns (theta*, worst, ratios, hind_worst)."""
    best = None
    for th in THETAS:
        tau, cp_h, _, resid, W = statics(phi, (phi + 0.5) % 1.0, "L", phi, s, th, fore, with_fore, hat_mass)
        r = ratios_of(tau, with_fore)
        worst = max(r[k] for k in rows_key)
        hind_worst = max(r[k] for k in ("hip", "knee", "ankle", "mp"))
        if best is None or worst < best[1]:
            best = (th, worst, r, hind_worst)
    return best


def main():
    fores = {phi: solve_fore_pose(phi) for phi in NODES}
    print("fore plant (l=0 target, body frame):")
    for phi, f in fores.items():
        print(f"  phi={phi:.2f}: a={f['a']:+.3f} b={f['b']:+.3f} elbow_internal={f['internal_deg']:5.1f} deg "
              f"miss={f['miss_mm']:5.1f} mm tip=({f['tip'][0]*1000:+7.1f},{f['tip'][1]*1000:+7.1f})mm")

    # -- config 0: replication anchor -- the banked vault biped (full HAT 8.184, no fore)
    rep = {round(phi, 3): scan_theta(phi, 0.0, fores[phi], False, HAT_FULL, ("hip", "knee", "ankle", "mp", "posture")) for phi in NODES}
    rep_ss = max(rep[round(p, 3)][1] for p in SS)
    print(f"\nreplica (full-HAT biped, theta* minimax): single-support worst = {rep_ss:.4f}  (banked: 0.8809 / 0.92-0.95 receipt wording)")

    # -- config 1: carved-out biped baseline (no fore masses) --
    base = {round(phi, 3): scan_theta(phi, 0.0, fores[phi], False, HAT_EFF, ("hip", "knee", "ankle", "mp", "posture")) for phi in NODES}
    base_ss = max(base[round(p, 3)][1] for p in SS)
    print(f"biped baseline (HAT_eff {HAT_EFF:.3f} kg, no fore): single-support worst = {base_ss:.4f}")

    # -- the s-series --
    series = {}
    for s in S_GRID:
        nodes_out, fixed = {}, {}
        for phi in NODES:
            key = round(phi, 3)
            fore = fores[phi]
            tau0, cp_h, _, resid, W = statics(phi, (phi + 0.5) % 1.0, "L", phi, s, 0.0, fore, True, HAT_EFF)
            r0 = ratios_of(tau0, True)
            tstar, worst, rstar, hind_worst = scan_theta(phi, s, fore, True, HAT_EFF, ("hip", "knee", "ankle", "mp", "posture", "shoulder", "elbow"))
            nodes_out[key] = {
                "theta0_ratios": {k: round(v, 4) for k, v in r0.items()},
                "theta0_demands_Nm": {k: round(float(tau0[i]), 3) for k, i in
                                      (("hip", 3), ("knee", 4), ("ankle", 5), ("mp", 6), ("posture", 2), ("shoulder", 11), ("elbow", 12))},
                "theta_star_rad": round(tstar, 4),
                "worst_ratio_at_theta_star": round(worst, 4),
                "hind_worst_at_theta_star": round(hind_worst, 4),
                "ratios_at_theta_star": {k: round(v, 4) for k, v in rstar.items()},
                "base_residuals": [round(resid[0], 12), round(resid[1], 9)],
                "cp_hind_x_mm": round(float(cp_h[0]) * 1000, 1),
            }
            fixed[key] = (r0, tau0)
        hw0 = max(max(fixed[round(p, 3)][0][k] for k in ("hip", "knee", "ankle", "mp")) for p in SS)
        hws = max(nodes_out[round(p, 3)]["hind_worst_at_theta_star"] for p in SS)
        ws = max(nodes_out[round(p, 3)]["worst_ratio_at_theta_star"] for p in SS)
        series[round(s, 4)] = {"nodes": nodes_out, "hind_worst_theta0_ss": round(hw0, 4),
                               "hind_worst_thetastar_ss": round(hws, 4), "worst_all_thetastar_ss": round(ws, 4)}
        print(f"s={s:.4f}: hind worst SS  theta0={hw0:.4f}  theta*={hws:.4f}  worst-all(theta*)={ws:.4f}")

    # -- falsifier 1: monotone relief.  The model's sharp form: signed demands
    # affine in s.  Verify affinity on the theta0 track across the grid, then
    # monotonicity of the hind worst (both tracks).
    aff_res = 0.0
    s0, s1 = S_GRID[0], S_GRID[-1]
    for phi in (0.3, 0.45):
        fore = fores[phi]
        t_a, _, _, _, _ = statics(phi, (phi + 0.5) % 1.0, "L", phi, s0, 0.0, fore, True, HAT_EFF)
        t_b, _, _, _, _ = statics(phi, (phi + 0.5) % 1.0, "L", phi, s1, 0.0, fore, True, HAT_EFF)
        t_m, _, _, _, _ = statics(phi, (phi + 0.5) % 1.0, "L", phi, 0.5 * (s0 + s1), 0.0, fore, True, HAT_EFF)
        pred = 0.5 * (t_a + t_b)
        aff_res = max(aff_res, float(np.max(np.abs(t_m - pred))))
    print(f"\naffinity check (tau affine in s, theta0): max residual = {aff_res:.3e} N.m")

    keys = [round(s, 4) for s in S_GRID]
    mono0 = all(series[keys[i + 1]]["hind_worst_theta0_ss"] <= series[keys[i]]["hind_worst_theta0_ss"] + 1e-9 for i in range(len(keys) - 1))
    monos = all(series[keys[i + 1]]["hind_worst_thetastar_ss"] <= series[keys[i]]["hind_worst_thetastar_ss"] + 1e-9 for i in range(len(keys) - 1))
    # signed-demand monotonicity per hind joint (theta0, stance nodes): each signed |tau| may
    # only shrink toward its self-weight asymptote; the affine law makes the SIGNED tau
    # monotone in s iff its s-slope sign matches its sign at s=1... report raw sequences.
    signed = {}
    for jname, idx in (("hip", 3), ("knee", 4), ("ankle", 5), ("mp", 6)):
        seq = []
        for s in S_GRID:
            vals = []
            for phi in SS:
                vals.append(float(series[round(s, 4)]["nodes"][round(phi, 3)]["theta0_demands_Nm"][jname]))
            seq.append(round(max(vals, key=abs), 3))
        signed[jname] = seq
    print("signed hind demands over s (max-|tau| stance node, theta0):", json.dumps(signed))
    print(f"monotone hind-worst relief: theta0={mono0}  theta*={monos}")

    # -- prediction: hind worst < 0.6 at the measured shares --
    pred_hits = {round(s, 4): {"hind_worst_theta0": series[round(s, 4)]["hind_worst_theta0_ss"],
                               "hind_worst_thetastar": series[round(s, 4)]["hind_worst_thetastar_ss"],
                               "below_0p6": bool(series[round(s, 4)]["hind_worst_theta0_ss"] < 0.6 and series[round(s, 4)]["hind_worst_thetastar_ss"] < 0.6)}
                 for s in (0.4, 0.55)}
    print("prediction (hind worst < 0.6 at measured shares):", json.dumps(pred_hits))

    # -- falsifier 2: the forelimb's own demands vs scaled caps (and the doc's triceps anchor) --
    fore_rows = {}
    for s in S_GRID:
        w_sh = max(series[round(s, 4)]["nodes"][round(p, 3)]["ratios_at_theta_star"]["shoulder"] for p in SS)
        w_el = max(series[round(s, 4)]["nodes"][round(p, 3)]["ratios_at_theta_star"]["elbow"] for p in SS)
        el_doc = max(abs(series[round(s, 4)]["nodes"][round(p, 3)]["theta0_demands_Nm"]["elbow"]) / CAP_ELBOW_DOC for p in SS)
        fore_rows[round(s, 4)] = {"shoulder_ratio": round(w_sh, 4), "elbow_ratio_scaled_cap": round(w_el, 4),
                                  "elbow_ratio_doc_cap": round(el_doc, 4)}
        print(f"s={s:.4f}: fore rows at theta*  shoulder={w_sh:.3f}  elbow/{CAP_ELBOW:.2f}Nm={w_el:.3f}  elbow/{CAP_ELBOW_DOC:.2f}Nm(doc)={el_doc:.3f}")

    result = {
        "membrane": "quadruped load-share: hindlimb demand/cap vs fore share s (single support hind contact, vertical paw reactions s*W/2 each, base rows unactuated and exactly satisfied by the prescribed split)",
        "machinery": "derive_stance_hold.py at fdc74523 (MP-Jacobian-corrected) + the trunk-scan theta DOF; fore chain = the doc's Stage-A 2-coordinate reduction; NQ=15",
        "declarations": {
            "fore_segments": "humerus 0.2737 kg @ 0.125 m, forearm 0.1323 kg @ 0.132 m (masses derived from the admitted hind Table-1 thigh:shank proportion 0.557:0.269; documented fore lengths retained; rod inertias; hind-chain COM fractions)",
            "mount": "doc sec 3.1 hip->shoulder closure (0.2689, -0.1331) m, carried with the trunk bounds [0.28, 0.482] m as the declared unknown",
            "plant": "paw tip target directly below the shoulder (l=0, tenability-optimal) at the hind contact height; grid-solved in bands shoulder/forearm within +/-1.2 rad of vertical, elbow INTERNAL angle constrained to 1.75-2.44 rad (Janisch TD 127.4 deg, doc stand 113.3 deg inside), straighter-arm branch wins ties; residuals reported per node",
            "fore_caps": {"shoulder_Nm": round(CAP_SHOULDER, 3), "elbow_Nm": round(CAP_ELBOW, 3),
                          "law": "hind cap x (driven segment mass x length)/(hind reference pair); doc triceps 3.76 N.m carried as the muscle-anchored elbow cross-check"},
            "shares": "mission grid {0, 0.25, 0.4, 0.55} + doc-derived 0.6944 (= 2x34.18/98.44, sec 3.2)",
        },
        "fore_plant": {str(round(p, 3)): {k: (v if not isinstance(v, np.ndarray) else [round(float(x), 6) for x in v])
                                          for k, v in fores[p].items()} for p in NODES},
        "replication_anchor": {"config": "full-HAT 8.184 biped, no fore, theta* minimax (the vault scan)",
                               "single_support_worst": round(rep_ss, 4),
                               "banked": "trunk_vault.json 0.8809; receipt wording 0.92-0.95"},
        "biped_baseline": {"config": "HAT_eff 7.371998 kg (carve-out), no fore masses",
                           "single_support_worst": round(base_ss, 4)},
        "series": series,
        "affinity_residual_Nm": aff_res,
        "monotone_relief": {"theta0": bool(mono0), "theta_star": bool(monos),
                            "signed_demands_over_s": signed},
        "prediction_check": pred_hits,
        "fore_rows_at_theta_star": fore_rows,
    }
    OUT.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print("\nwritten:", OUT)


if __name__ == "__main__":
    main()
