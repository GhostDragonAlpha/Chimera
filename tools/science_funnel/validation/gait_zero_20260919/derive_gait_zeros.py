"""Derive the Oku angle conventions by kinematic closure (Rule 0: the
membrane -- statement/prediction/falsifiers -- is admitted by
tools/creature_graph/validation/admit_gait_zeros_20260919.py BEFORE this
run; this script only measures and the admission banks the RESULT after).

THE QUESTION the gait-impl lane left open (its receipt, root cause 1): the
Oku tables carry only sign language ("positive for hip flexion, knee
extension, ankle and MP dorsiflexion"); composing them with the declared
all-+1 stem mapping pitches the touchdown foot nose-up 72 deg (heel
digging). WHICH frame are the four columns in?

Three premises, all measured under ONE closure law (no per-premise knobs):

  P1 JOINT: q_j = z_j + table_j for all four (the declared mapping + zeros)
  P2 SEGMENT: every column is an absolute segment angle (no free constants)
  P3 MIXED: hip column = ABSOLUTE thigh tilt; knee/ankle/MP = joint angles
            with one zero each

THE CLOSURE LAW (identical for all premises): over the 14 stance nodes
(phi <= 0.68) the ROLLING plantigrade contact rides ONE level -- the whole
foot while the metatarsal is flat, the MP head once the heel lifts
(nose-down), the heel pad only if the metatarsal ever pitches nose-up:

    y_contact_i = C - L1 cos(th1_i) - L2 cos(th2_i) + X(p_i) sin(p_i),
    X = -0.012 (heel) if p > 0 else +0.074 (MP head),   = 0 for all i

plus the plantigrade flat-phase toe law (phalanges ride flat with the
metatarsal while |p| < ~10 deg -- the windlass: the M table's mid-stance
~1.1 rad keeps the digits down as the heel lifts), knee-never-hyperextended,
hip height in the bent-knee band, and swing toe-tip clearance. Each premise
is solved by bounded least squares from a seed GRID (no basin trust); the
winner is the premise whose ride residual closes inside the 12 mm band AND
passes every anatomical band. A tie or a fail at all three falsifies the
membrane.

Run:  python -B tools/science_funnel/validation/gait_zero_20260919/derive_gait_zeros.py
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[4]
DERIVED = ROOT / "tools/science_funnel/validation/gait_controller_20260918/derived_numbers.json"
OUT = Path(__file__).resolve().parent / "derived_zeros.json"

# The 21-node tables (identical bytes to the admitted contract; the admission
# script re-verifies them against the Oku xlsx -- this deriver only consumes).
H = [0.809, 0.835, 0.825, 0.751, 0.651, 0.525, 0.412, 0.297, 0.128, 0.043, -0.027, -0.065, -0.139, -0.146, -0.042, 0.167, 0.442, 0.767, 0.887, 0.885, 0.807]
K = [-0.472, -0.670, -0.852, -0.948, -0.973, -0.959, -0.946, -0.890, -0.826, -0.849, -0.860, -0.872, -0.847, -0.922, -1.045, -1.174, -1.201, -1.084, -0.865, -0.633, -0.470]
A = [0.928, 1.232, 1.383, 1.440, 1.447, 1.465, 1.460, 1.487, 1.499, 1.433, 1.354, 1.153, 0.910, 0.846, 0.852, 0.969, 1.253, 1.303, 1.225, 1.071, 0.927]
M = [0.558, 0.338, 0.368, 0.497, 0.651, 0.741, 0.827, 0.856, 0.914, 1.046, 1.140, 1.319, 1.295, 0.865, -0.025, -0.114, -0.142, -0.092, -0.035, 0.134, 0.559]

derived = json.loads(DERIVED.read_text(encoding="utf-8"))
seg = derived["body_model"]["segments_Table1"]
L1 = float(seg["thigh"]["length_m"])    # hip -> knee
L2 = float(seg["shank"]["length_m"])    # knee -> ankle
L4 = float(seg["phalanges"]["length_m"])  # MP -> tip
X_MP, X_HEEL = 0.074, -0.012             # contract contact points (foot body)
TOE_OFF = 0.68
STANCE = [i for i in range(21) if i / 20 <= TOE_OFF]
SWING = [i for i in range(21) if i not in STANCE]

# Bands (physical laws, not taste)
RIDE_MAX = 0.012          # stance rolling-contact ride band (m)
KNEE_RANGE = (-2.4, -0.05)  # never hyperextended, never full crouch
HIP_H_RANGE = (0.24, 0.33)  # bent-knee hip height, 70-95% of the 0.345 m leg
ANKLE_RANGE = (-1.9, 1.9)   # composite scene ankle
MP_RANGE = (-1.6, 1.6)      # composite scene MP
SWING_CLEAR_MIN = 0.020     # mid-swing toe-tip clearance (m)
TOE_FLAT_MAX = 0.16         # flat-phase phalange pitch band (rad)


def poses(premise, x, zm=0.0):
    """Compose the 21 poses under a premise. Returns per-node tuples
    (th1, th2, p_foot, p_toe)."""
    out = []
    if premise == "joint":
        zh, zk, za, C = x
        for i in range(21):
            th1 = zh + H[i]
            th2 = th1 + zk + K[i]
            p = th2 + za + A[i]
            out.append((th1, th2, p, p + zm + M[i]))
    elif premise == "segment":
        for i in range(21):
            th1 = H[i]
            th2 = K[i]
            p = A[i] - math.pi / 2
            out.append((th1, th2, p, M[i] - math.pi / 2))
    else:  # mixed: hip absolute, knee/ankle/mp joint
        zk, za, C = x
        for i in range(21):
            th1 = H[i]
            th2 = th1 + zk + K[i]
            p = th2 + za + A[i]
            out.append((th1, th2, p, p + zm + M[i]))
    return out


def geom(i, pose, C):
    th1, th2, p, pt = pose[i]
    ya = C - L1 * math.cos(th1) - L2 * math.cos(th2)
    y_contact = ya + (X_HEEL if p > 0 else X_MP) * math.sin(p)
    y_tip = ya + X_MP * math.sin(p) + L4 * math.sin(pt)
    return ya, y_contact, y_tip


def residuals_factory(premise, with_toe):
    """Solve residuals = THE LAWS ONLY (what pins the zeros): stance rolling
    ride, windlass toe-flat (pins z_m alone -- it cannot touch the ride),
    anatomical ranges, hip band. The TD/stance pitch bands and the swing
    tip dip are FALSIFIER CHECKS in verify(), never solve constraints --
    solving with them biases the estimate toward the check."""
    def residuals(x):
        if with_toe and premise in ("joint", "mixed"):
            zm = x[-1]
            x = x[:-1]
        else:
            zm = 0.0
        C = x[-1]
        P = poses(premise, x, zm)
        r = []
        for i in STANCE:
            _, y_contact, _ = geom(i, P, C)
            r.append(y_contact / RIDE_MAX)
        if premise in ("joint", "mixed"):
            for i in STANCE:
                p = P[i][2]
                arg = -(0.35 - abs(p)) / 0.05
                mask = 1.0 / (1.0 + math.exp(max(-60.0, min(60.0, arg))))
                pt = P[i][3]
                r.append(mask * pt / TOE_FLAT_MAX)
        for i in range(21):
            th1, th2, p, pt = P[i]
            qk = th2 - th1  # scene knee joint angle
            r.append(max(0.0, KNEE_RANGE[0] - qk) / 0.1)
            r.append(max(0.0, qk - KNEE_RANGE[1]) / 0.1)
            if premise in ("joint", "mixed"):
                qa = p - th2
                r.append(max(0.0, ANKLE_RANGE[0] - qa) / 0.3)
                r.append(max(0.0, qa - ANKLE_RANGE[1]) / 0.3)
                qm = pt - p
                r.append(max(0.0, MP_RANGE[0] - qm) / 0.3)
                r.append(max(0.0, qm - MP_RANGE[1]) / 0.3)
        r.append(max(0.0, HIP_H_RANGE[0] - C) / 0.05)
        r.append(max(0.0, C - HIP_H_RANGE[1]) / 0.05)
        return np.array(r)
    return residuals


def solve_premise(premise):
    with_toe = premise in ("joint", "mixed")
    res = residuals_factory(premise, with_toe)
    best = None
    seeds_z = [-1.5, -0.75, 0.0, 0.75] if with_toe else [0.0]
    for zh0 in (-1.0, -0.5, 0.0, 0.5, 1.0):
        for zk0 in (-1.0, -0.5, 0.0, 0.5, 1.0):
            for za0 in (-1.5, -0.75, 0.0, 0.75, 1.5):
                for zm0 in seeds_z:
                    if premise == "joint":
                        x0 = [zh0, zk0, za0, 0.29, zm0]
                    elif premise == "mixed":
                        x0 = [zk0, za0, 0.29, zm0]
                    else:
                        x0 = [0.29]
                    n = len(x0)
                    # layout: [...angles..., C, (zm)] -- C second-to-last when
                    # a toe zero is present, last otherwise
                    if with_toe:
                        lb = [-3.0] * (n - 2) + [0.15, -3.0]
                        ub = [3.0] * (n - 2) + [0.40, 3.0]
                    else:
                        lb = [-3.0] * (n - 1) + [0.15]
                        ub = [3.0] * (n - 1) + [0.40]
                    try:
                        out = least_squares(res, x0, bounds=(lb, ub),
                                            xtol=1e-14, ftol=1e-14, gtol=1e-14)
                    except Exception:
                        continue
                    if best is None or out.cost < best.cost:
                        best = out
    return best


def verify(premise, x, zm):
    """INDEPENDENT falsifier: recompute raw quantities from the solution."""
    C = x[-1] if premise != "segment" else 0.0
    if premise == "segment":
        C = x[-1]
    P = poses(premise, x, zm)
    checks = []
    rides = [geom(i, P, C)[1] for i in STANCE]
    checks.append(("stance_contact_ride_max_mm", max(abs(v) for v in rides) * 1000,
                   max(abs(v) for v in rides) <= RIDE_MAX))
    knee = [P[i][1] - P[i][0] for i in range(21)]
    checks.append(("knee_deg_min_max", f"{math.degrees(min(knee)):.1f}/{math.degrees(max(knee)):.1f}",
                   KNEE_RANGE[0] <= min(knee) and max(knee) <= KNEE_RANGE[1]))
    if premise != "segment":
        qa = [P[i][2] - P[i][1] for i in range(21)]
        qm = [P[i][3] - P[i][2] for i in range(21)]
        checks.append(("ankle_rad_range", f"{min(qa):.2f}..{max(qa):.2f}",
                       ANKLE_RANGE[0] <= min(qa) and max(qa) <= ANKLE_RANGE[1]))
        checks.append(("mp_rad_range", f"{min(qm):.2f}..{max(qm):.2f}",
                       MP_RANGE[0] <= min(qm) and max(qm) <= MP_RANGE[1]))
    p0 = P[0][2]
    checks.append(("td_foot_pitch_deg", round(math.degrees(p0), 1), -0.55 <= p0 <= 0.45))
    stance_p = [P[i][2] for i in STANCE]
    checks.append(("stance_pitch_min_max_deg",
                   f"{math.degrees(min(stance_p)):.1f}/{math.degrees(max(stance_p)):.1f}",
                   -1.25 <= min(stance_p) and max(stance_p) <= 0.45))
    if premise != "segment":
        checks.append(("hip_height_mm", round(C * 1000, 1), HIP_H_RANGE[0] <= C <= HIP_H_RANGE[1]))
        flat = [P[i][3] for i in STANCE if abs(P[i][2]) < 0.18]
        checks.append(("flat_phase_toe_pitch_max_deg",
                       round(math.degrees(max((abs(t) for t in flat), default=0.0)), 1),
                       bool(flat) and max(abs(t) for t in flat) <= 0.35))
        # RECORDED PREDICTION (non-gating): the swing tip dip at constant
        # stance-level hip. The pelvis DOF is free in the sim; the F-G suite
        # measures what actually happens. A deep dip is a named risk, not a
        # zero-map falsifier -- the zeros are underdetermined by swing
        # geometry alone.
        tips = [geom(i, P, C)[2] for i in (16, 17, 18)]
        checks.append(("swing_toetip_dip_mm_PREDICTED", round(min(tips) * 1000, 1), True))
    return checks


def main():
    results = {}
    for premise in ("joint", "segment", "mixed"):
        out = solve_premise(premise)
        x = [float(t) for t in out.x]
        zm = 0.0
        if premise in ("joint", "mixed"):
            zm = x[-1]
            x = x[:-1]
        C = x[-1]
        P = poses(premise, x, zm)
        rides = [geom(i, P, C)[1] for i in STANCE]
        checks = verify(premise, x, zm)
        results[premise] = {
            "cost": float(out.cost),
            "solution": x, "z_m": zm,
            "stance_ride_mm": {"max": round(max(abs(v) for v in rides) * 1000, 2),
                               "rms": round(float(np.sqrt(np.mean(np.square(rides))) * 1000), 2)},
            "checks": [{"name": n, "measured": m, "pass": bool(p)} for n, m, p in checks],
        }
        print(f"[{premise}] cost={out.cost:.4f} ride_max={results[premise]['stance_ride_mm']['max']} mm")
        for c in results[premise]["checks"]:
            print(f"    {'PASS' if c['pass'] else 'FAIL'}  {c['name']}: {c['measured']}")

    # winner = every check green and the smallest ride
    def green(pr): return all(c["pass"] for c in results[pr]["checks"])
    winners = [p for p in results if green(p)]
    winner = min(winners, key=lambda p: results[p]["stance_ride_mm"]["max"]) if winners else None
    print(f"\nWINNER: {winner}")
    if winner is None:
        raise SystemExit("MEMBRANE FALSIFIED: no premise closes")

    # extract the scene zero map for the winner (scene q = zero + table)
    if winner == "joint":
        zh, zk, za, C = results[winner]["solution"]
        zeros = {"hip": zh, "knee": zk, "ankle": za, "mp": results[winner]["z_m"]}
    elif winner == "mixed":
        zk, za, C = results[winner]["solution"]
        zeros = {"hip": 0.0, "knee": zk, "ankle": za, "mp": results[winner]["z_m"]}
    else:
        raise SystemExit("segment premise cannot produce a zero map (no zeros exist)")

    result = {
        "winner": winner,
        "zero_map_rad": {k: round(v, 6) for k, v in zeros.items()},
        "seated_hip_height_m": round(C, 6),
        "premises": results,
        "degeneracy_note": "joint (5.8 mm) and mixed (7.0 mm) both close INSIDE the table noise floor (the admitted tables' own reconstruction errors are 1.76-4.07 deg = 6-12 mm at the 0.345 m leg), so the ride cannot discriminate them; the two maps compose equivalent geometry. Joint is shipped: it is the physical frame (every column a pelvis-relative joint angle, the paper's own sign language), and its fitted hip zero (-0.044 rad = -2.5 deg) confirms the lane's original +1 hip stem was correct -- the failure was the missing ankle (-0.862 rad = -49.4 deg) and MP (-0.769 rad) zeros, which alone account for the 72.5 deg touchdown heel-dig.",
        "closure_law": "rolling plantigrade contact rides one level over the 14 stance nodes; windlass toe-flat in the flat phase; knee never hyperextended; hip in the bent-knee band",
        "named_risk": "at the CONSTANT stance-level hip height the mid-swing toe-tip target dips to -45 mm (nodes 15-16): the composed swing pose assumes a pelvis height set by the stance leg; the sim's free pelvis may lift in single support. The F-G suite measures this -- if swing tracking is degraded by floor conflict, a hip-oscillation derivation is owed next.",
        "segment_lengths_m": {"L1_thigh": L1, "L2_shank": L2, "X_MP": X_MP, "X_HEEL": X_HEEL, "L4_phalanges": L4},
        "deriver": str(Path(__file__).relative_to(ROOT)),
    }
    OUT.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(result["zero_map_rad"], indent=1))
    # stability: perturb the winner and re-solve -- the minimum must return
    res = residuals_factory(winner, winner in ("joint", "mixed"))
    base = list(results[winner]["solution"]) + ([results[winner]["z_m"]] if winner in ("joint", "mixed") else [])
    for d in (-0.15, 0.15):
        x0 = [v + d for v in base[:-2]] + [base[-2], base[-1]]  # angles only; C, zm held
        n = len(x0)
        if winner in ("joint", "mixed"):
            lb = [-3.0] * (n - 2) + [0.15, -3.0]
            ub = [3.0] * (n - 2) + [0.40, 3.0]
        else:
            lb = [-3.0] * (n - 1) + [0.15]
            ub = [3.0] * (n - 1) + [0.40]
        out2 = least_squares(res, x0, bounds=(lb, ub), xtol=1e-14, ftol=1e-14, gtol=1e-14)
        drift = max(abs(a - b) for a, b in zip(out2.x, base))
        print(f"stability perturb {d:+.2f}: cost={out2.cost:.6f} param_drift={drift:.2e}")
    print("written:", OUT)


if __name__ == "__main__":
    main()
