"""The trunk-vault membrane (Rule 0, banked before the walk run): the trunk
pitch is a load-bearing DOF, not a posture to pin.

STATEMENT: for each single-support stance phase phi there exists a trunk pitch
theta*(phi) that centers the leg's actuator demands inside their caps --
leaning the HAT moves the whole assembly's CoM toward the contact, shortening
the ankle lever and re-balancing the hip/knee moments (the CoM-over-CoP
condition is theta's lever on the posture row).

MODEL: the wave-4 statics machinery (derive_stance_hold.py, imported, not
copied) plus exactly two extensions.
  (1) THE BASE-ROT DOF: the engine's trunk pitch (base_rot_z, the posture
      drive's coordinate) rides the WHOLE assembly -- the trunk is body 0 and
      every leg coordinate is measured from its parent body, so pitching the
      trunk rigidly rotates legs+trunk about the pelvis origin (the hip line).
      The engine's leg servo targets are absolute model angles equal to the
      table values, i.e. RELATIVE angles: the leg geometry in the trunk frame
      is unchanged by theta; every world position rotates.
  (2) THE SOLE CoP ENVELOPE: the wave-6/7 finding -- the foot loads through a
      CoP anywhere on the heel..MP sole segment (the migrating sole row), not
      one fixed point. The CoP is a free static unknown constrained to the
      segment [X_HEEL, X_MP] along the sole direction.

STATICS (identical law to wave 4, now per theta): the contact reaction is
solved from the unactuated base rows -- lambda = (0, M g): vertical, full
weight, at the chosen CoP (base_x unactuated gives lambda_x = 0 exactly as in
wave 4; base_y gives lambda_y = M g). Then tau_j = -(G_j + r_j . lambda) on
every actuated row, G from the per-body COM Jacobians of the ROTATED pose.

SOLVER: per stance node phi, minimize over (theta, x_cop) the max
demand/cap ratio over the nine actuated rows (4 stance drives, 4 swing
drives, the posture drive). The min-max value IS the falsifier: if it stays
>= 1 at some node, NO trunk pitch centers the demands -- the bipedal hindlimb
lift is statically infeasible at any trunk pitch and the quadruped lane is
confirmed. If < 1 at every single-support node, theta*(phi) exists.

CONVENTION: theta_world > 0 = CCW about +z = nose-UP (backward lean); the
emitted vault table uses HAT-FORWARD-POSITIVE (theta_vault = -theta_world),
the sign the scene maps onto base_rot_z after the engine-sign probe.

Run:  python -B tools/science_funnel/validation/gait_zero_20260919/derive_trunk_vault.py
"""
import json
import math
from pathlib import Path

import numpy as np

from derive_stance_hold import (CAP, CAP_POST, G_ACC, H, K, A, M, NQ, X_MP,
                                X_HEEL, body_states, contact_point, joint_points,
                                leg_pose, seg)

OUT_DIR = Path(__file__).resolve().parent
STANCE_HOLD_TRUNK = OUT_DIR / "stance_hold_trunk.json"
TRUNK_VAULT = OUT_DIR / "trunk_vault.json"

THETA_GRID = np.arange(-0.50, 0.5001, 0.005)     # world CCW+, rad (~ +/-28.6 deg)
COP_GRID = np.arange(X_HEEL, X_MP + 1e-9, 0.002)  # the sole segment, m
# single-support window (duty 0.683, legs offset 0.5): left stance without the
# other leg's stance overlap. Wave-4: the double-support nodes overestimate
# single-support statics; the verdict lives on this window.
SS_LO, SS_HI = 0.183, 0.50
NODES = [round(SS_LO + 0.02 * i, 3) for i in range(16)] + [SS_HI]


def rot(xy, th):
    c, s = math.cos(th), math.sin(th)
    return np.array([xy[0] * c - xy[1] * s, xy[0] * s + xy[1] * c])


def sole_point(phi, x_cop):
    """the CoP on the sole segment along the (unrotated) sole direction."""
    th1, th2, p, pt = leg_pose(phi)
    L1 = float(seg["thigh"]["length_m"]); L2 = float(seg["shank"]["length_m"])
    knee = np.array([L1 * math.sin(th1), -L1 * math.cos(th1)])
    ank = knee + np.array([L2 * math.sin(th2), -L2 * math.cos(th2)])
    return ank + np.array([x_cop * math.cos(p), x_cop * math.sin(p)])


def demands(th, phi_stance, phi_swing, x_cop):
    """Actuator demands at trunk pitch th (world CCW+), stance L at phi_stance,
    swing R at phi_swing, CoP at x_cop on the stance sole. Returns (tau, rows,
    names, caps, com_x, cop_x) in the rotated frame."""
    bodies = body_states(phi_stance, phi_swing)
    jp = joint_points(phi_stance, phi_swing)
    cp = rot(sole_point(phi_stance, x_cop), th)
    coms = [(name, m, rot(com, th), I, chain) for (name, m, com, I, chain) in bodies]
    jpr = {c: (rot(v, th) if c not in (0, 1, 2) else v) for c, v in jp.items()}

    m_tot = sum(m for (_, m, _, _, _) in coms)
    G = np.zeros(NQ)           # the script's convention: G = -dPE/dq
    for (_, m, com, _, chain) in coms:
        G[2] += -m * G_ACC * com[0]              # base-rot moves EVERY body
        for c in chain:
            G[c] += -m * G_ACC * (com[0] - jpr[c][0])
    r = np.zeros(NQ)           # contact y-velocity row (the normal row)
    r[1] = 1.0
    r[2] = cp[0]
    cbase = 3                  # stance leg = LEFT (phi_swing = phi+0.5 carries right)
    for c in (cbase, cbase + 1, cbase + 2, cbase + 3):
        r[c] = cp[0] - jpr[c][0]   # the SWING rows stay zero: the stance contact's Jacobian does not reach them
    lam = np.array([0.0, m_tot * G_ACC])         # the unactuated base-row solve
    tau = -(G + r * lam[1])
    names = ["hip_L", "knee_L", "ankle_L", "mp_L", "hip_R", "knee_R", "ankle_R", "mp_R", "posture"]
    rows = [3, 4, 5, 6, 7, 8, 9, 10, 2]
    caps = [CAP["hip"], CAP["knee"], CAP["ankle"], CAP["mp"],
            CAP["hip"], CAP["knee"], CAP["ankle"], CAP["mp"], CAP_POST]
    com_x = sum(m * com[0] for (_, m, com, _, _) in coms) / m_tot
    return tau, rows, names, caps, com_x, cp


def ratio_at(th, phi_stance, phi_swing, x_cop):
    tau, rows, names, caps, com_x, cp = demands(th, phi_stance, phi_swing, x_cop)
    ratios = [abs(tau[c]) / cap for c, cap in zip(rows, caps)]
    k = int(np.argmax(ratios))
    return max(ratios), {"theta_world": round(float(th), 4), "cop_m": round(float(x_cop), 4),
                         "worst": names[k], "ratio": round(max(ratios), 4),
                         "tau_posture_Nm": round(float(tau[2]), 3),
                         "tau_knee_Nm": round(float(tau[4]), 3),
                         "tau_ankle_Nm": round(float(tau[5]), 3),
                         "tau_hip_Nm": round(float(tau[3]), 3),
                         "com_x_m": round(float(com_x), 4), "cop_x_m": round(float(cp[0]), 4)}


def solve_node(phi):
    best, best_detail = 1e9, None
    phi_swing = (phi + 0.5) % 1.0
    for th in THETA_GRID:
        for xc in COP_GRID:
            r, detail = ratio_at(th, phi, phi_swing, xc)
            if r < best:
                best, best_detail = r, detail
    # refine around the winner (local polish on the 2-D grid)
    th0, xc0 = best_detail["theta_world"], best_detail["cop_m"]
    for th in np.arange(th0 - 0.006, th0 + 0.0061, 0.001):
        for xc in np.arange(max(X_HEEL, xc0 - 0.003), min(X_MP, xc0 + 0.003) + 1e-9, 0.0005):
            r, detail = ratio_at(th, phi, phi_swing, xc)
            if r < best:
                best, best_detail = r, detail
    return best, best_detail


def main():
    rows = []
    for phi in NODES:
        best, detail = solve_node(phi)
        detail["phi"] = phi
        detail["theta_vault_fwd_rad"] = round(-detail["theta_world"], 4)  # HAT-forward+
        detail["theta_vault_fwd_deg"] = round(-detail["theta_world"] * 180 / math.pi, 2)
        rows.append(detail)
        print(f"phi={phi:.3f}  minmax_ratio={best:.3f}  worst={detail['worst']:>8s}"
              f"  theta_fwd={detail['theta_vault_fwd_deg']:+7.2f} deg"
              f"  cop={detail['cop_m']*1000:+6.1f} mm  post={detail['tau_posture_Nm']:+7.2f}"
              f"  knee={detail['tau_knee_Nm']:+7.2f}  ankle={detail['tau_ankle_Nm']:+7.2f}"
              f"  hip={detail['tau_hip_Nm']:+7.2f}")

    worst = float(max(r["ratio"] for r in rows))
    feasible = bool(worst < 1.0)
    # master table: 0.5-periodic; solved on [SS_LO, SS_HI]; linear bridge across
    # the double-support windows (wave 4: single-support statics OVERestimates
    # the shared-load nodes, so bridging them is the honest coarse read).
    lo_t = [r for r in rows if abs(r["phi"] - SS_LO) < 1e-9][0]["theta_vault_fwd_rad"]
    hi_t = [r for r in rows if abs(r["phi"] - SS_HI) < 1e-9][0]["theta_vault_fwd_rad"]
    table = [0.0] * 21
    for i in range(21):
        phi = i / 20.0
        if phi > 0.5 + 1e-9:
            table[i] = table[i - 10]   # the trunk is 0.5-periodic (left/right symmetry): mirror
            continue
        if SS_LO - 1e-9 <= phi <= SS_HI + 1e-9:
            tv = float(np.interp(phi, [r["phi"] for r in rows], [r["theta_vault_fwd_rad"] for r in rows]))
        else:
            tv = float(np.interp(phi, [0.0, SS_LO], [hi_t, lo_t]))  # double-support bridge; T[0]=T[0.5]=hi_t
        table[i] = round(tv, 4)
    verdict = {
        "membrane": "trunk-vault: theta*(phi) solving the min-max demand/cap ratio per single-support stance node",
        "model": "wave-4 statics + base-rot DOF (rigid assembly rotation about the pelvis origin; leg coordinates relative) + sole CoP envelope [heel,MP]; lambda=(0,Mg) from the unactuated base rows",
        "convention": "theta_vault_fwd > 0 = HAT-forward (nose-down) lean; emitted table is 0.5-periodic, solved on the single-support window [0.183,0.50], bridged across double support",
        "single_support_window": [SS_LO, SS_HI],
        "nodes": rows,
        "worst_minmax_ratio": round(worst, 4),
        "verdict": "FEASIBLE: theta*(phi) exists -- every single-support node centers inside the caps" if feasible
                   else "INFEASIBLE: no trunk pitch brings every demand inside its caps -- the bipedal hindlimb lift is statically infeasible at any trunk pitch; the quadruped lane is confirmed",
        "feasible": feasible,
        "master_table_21_vault_fwd_rad": table,
    }
    STANCE_HOLD_TRUNK.write_text(json.dumps(verdict, indent=1) + "\n", encoding="utf-8")
    TRUNK_VAULT.write_text(json.dumps({"membrane": "trunk-vault theta*(phi) master table (HAT-forward+ rad, 21 nodes, 0.5-periodic)",
                                       "derived_by": "derive_trunk_vault.py", "worst_minmax_ratio": round(worst, 4),
                                       "feasible": feasible, "theta_vault_fwd_rad": table}, indent=1) + "\n", encoding="utf-8")
    print("\nVERDICT:", verdict["verdict"])
    print("worst min-max ratio:", round(worst, 4))
    print("master table (HAT-forward+ rad):", table)
    print("written:", STANCE_HOLD_TRUNK, "and", TRUNK_VAULT)


if __name__ == "__main__":
    main()
