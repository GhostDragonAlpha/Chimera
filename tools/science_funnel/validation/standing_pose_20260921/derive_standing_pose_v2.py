"""derive_standing_pose_v2.py -- THE AMENDED STANDING POSE SOLVE
(preregistration_amendment_4.md, sha 3ad74c44..., banked BEFORE this run;
ONE derived problem per phase, TWO declared starts each, no sweep).

PHASE 1 -- the strict solve (the outcome-S attempt):
  minimize J = V + kappa*d (the v1 objective, unchanged)
  s.t. T3: h_min(m; x) >= EPSILON_MM for all 21 non-pad membranes,
       the v1 seat constraints (both hips + both tarsal loops, committed cut),
       bounds = the recorded class ranges.
  DECLARED STARTS: (a) x0 = zeros(10) (the rest projection);
                   (b) x0 = the v1 pose of record x_R12 (declared in amendment 4).
  OUTCOME S iff any start exits clearance-feasible with T1/T2 verdicts GREEN.

PHASE 2 (outcome I only) -- the maximin best-effort:
  maximize t over (x, t) s.t. h_min(m; x) - t >= 0 (21),
    V(x) <= V_rest, d(x) <= d_rest (the corpse's committed readings),
    the v1 seat constraints, bounds = the recorded ranges, t in [-100, 100].
  DECLARED STARTS: (a) x=0 with t0 = its measured min non-pad clearance;
                   (b) x = the v1 pose of record with t0 = its measured min.
  POSE OF RECORD = the better t_max (tie -> start (a)); must pass the FV2
  lawfulness screen to be minted.

Determinism: fresh-process double runs are byte-identical (falsifier FV3).
Env: single-threaded BLAS (set before numpy import; also set by the caller).

Run:  OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 python -B \
        tools/science_funnel/validation/standing_pose_20260921/derive_standing_pose_v2.py
"""

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parents[1] / "hip_pivot_proof_20260921"))

from standing_pose_core_v2 import (StandingV2, NONPAD_BONES, EPSILON_MM,
                                   SECONDARY_EPSILON_MM)  # noqa: E402
from standing_pose_core import rnd, sanitize  # noqa: E402  (house rounding + JSON sanitizer)

OUT = HERE / "pose_v2.json"

SOLVER = {"method": "SLSQP", "ftol": 1e-12, "maxiter": 400}


def main():
    sv = StandingV2()
    dv = sv.dv

    # ---- design-time-banked numbers re-measured (P-AV2-1, P-AV2-2) ---------
    hs_v1, n_v1, _ = sv.heights(sv.x_v1)
    v1_min = min(hs_v1[r][0] for r in NONPAD_BONES)
    v1_argmin = "bone_%02d" % NONPAD_BONES[int(np.argmin([hs_v1[r][0] for r in NONPAD_BONES]))]
    skull_v1, cut = sv.skull_window_hmin(sv.x_v1)
    pinned_consts, n_pin = sv.pinned_constants()
    dev_pin = float(np.abs(n_v1 - n_pin).max())
    fixed_forced = (1, 4, 5, 10, 11, 12, 13, 14, 16, 19)

    # ---- PHASE 1: the strict solve, both declared starts --------------------
    strict = {}
    strict_x0 = {}
    for name, x0 in (("rest", np.zeros(10)), ("v1_pose_of_record", sv.x_v1)):
        strict_x0[name] = np.asarray(x0, dtype=np.float64).copy()
        strict[name] = sv.strict_solve(x0)
        print("strict[%s]: success=%s status=%s '%s' | J=%s minT3slack=%s mm at %s" % (
            name, strict[name]["success"], strict[name]["status"],
            strict[name]["message"], strict[name]["J_at_return"],
            strict[name]["min_T3_slack_mm"], strict[name]["argmin_membrane"]))
    outcome_S = bool(any(strict[k]["clearance_feasible_T1_T2"] for k in strict))

    record = {
        "schema": "chimera.standing_pose_v2.v1",
        "lane": "agent/standing-pose-v2-20260921",
        "base_commit": "4ea008cb (agent/standing-pose-20260921: the v1 lane)",
        "preregistration_sha256":
            (HERE / "preregistration.sha256").read_text().split()[0],
        "amendment_4_sha256":
            (HERE / "preregistration_amendment_4.sha256").read_text().split()[0],
        "trailer": "Agent: GLM 5.3",
        "solver": {**SOLVER,
                   "library": "scipy.optimize.minimize",
                   "env": "OMP_NUM_THREADS=1, OPENBLAS_NUM_THREADS=1, MKL_NUM_THREADS=1",
                   "starts": "amendment 4 section 3/4: BOTH starts declared pre-bank"},
        "epsilon": {
            "primary_mm": EPSILON_MM,
            "primary_source": "the committed P6' interpenetration tolerance REUSED: "
                              "tol_ip = specimen.resolution_um/2 = 0.08 mm (the definition's "
                              "resolution_um = 160; law doc section 5B resolution floor)",
            "secondary_mm": SECONDARY_EPSILON_MM,
            "secondary_source": "the committed touching-class cut (the seat family's "
                                "separation constant; recorded as the secondary reading)",
        },
        "amended_definition_verdicts": {
            "T1_pad_coplanarity": "V(x) <= V_v1 (%s mm^2, the v1 committed record)" % rnd(sv.V_v1),
            "T2_trunk_level": "d(x) <= d_v1 (%s, the v1 committed record)" % rnd(sv.d_v1),
            "T3_floor_clearance": "h_min(m; x) >= EPSILON_MM for all 21 non-pad membranes",
            "T4_pads_only_contact": "exclusivity (= T3) + |h_cen(pad)| <= EPSILON_MM (all four)",
            "T5_head_clearance": "skull-region h_min >= EPSILON_MM (the head window)",
        },
        "structural_pin": {
            "pinned_plane_normal": [rnd(v) for v in n_pin],
            "v1_pose_normal": [rnd(v) for v in n_v1],
            "max_component_dev": rnd(dev_pin),
            "pinned_equals_v1_within_1e-6": bool(dev_pin <= 1e-6),
            "head_window_cut_mm": rnd(cut),
            "head_window_rule": "bone_01 vertices with x > max_x(hand pads 08/09) "
                                "(the hands are the last pre-head objects on +x)",
            "fixed_forced_constants_mm": {("bone_%02d" % r): rnd(pinned_consts[r])
                                          for r in fixed_forced},
            "smallest_fixed_deficit_mm": rnd(EPSILON_MM
                                             - max(pinned_consts[r]
                                                   for r in (1, 4, 5, 14, 16, 19))),
            "deepest_fixed_h_min_mm": rnd(min(pinned_consts[r]
                                              for r in (1, 4, 5, 14, 16, 19))),
        },
        "v1_pose_under_amended_definition": {
            "min_non_pad_h_min_mm": rnd(v1_min),
            "argmin_membrane": v1_argmin,
            "skull_region_h_min_mm": rnd(skull_v1),
            "all_21_below_plane": bool(v1_min < 0.0),
            "note": "P-AV2-1: the fired v1 falsifier, quantified (the heap, in numbers)",
        },
        "strict_solve": strict,
        "outcome": None,
        "pose_bonds": None,
        "maximin": None,
    }

    if outcome_S:
        # OUTCOME S: mint the clearance-feasible pose of record (full-precision
        # point regenerated from the SAME declared start -- the deterministic
        # solve reproduces the strict run bit-for-bit).
        from scipy.optimize import minimize
        name = next(k for k in ("rest", "v1_pose_of_record")
                    if strict[k]["clearance_feasible_T1_T2"])
        res = minimize(sv.strict_objective, strict_x0[name],
                       method="SLSQP", bounds=dv.bounds(),
                       constraints=[{"type": "ineq", "fun": lambda z: sv.t3_slacks(z)}],
                       options={"ftol": 1e-12, "maxiter": 400})
        x_full = np.asarray(res.x, dtype=np.float64)
        record["outcome"] = "S"
        record["pose_of_record_source"] = "strict_solve[%s]" % name
        record["variables"] = {
            "names": ["hipL_flexion", "hipL_adduction", "hipL_rotation",
                      "hipR_flexion", "hipR_adduction", "hipR_rotation",
                      "kneeL", "kneeR", "driverL_06_25", "driverR_07_24"],
            "x_full": [float(v) for v in x_full],
            "x_R12": [rnd(v) for v in x_full],
            "the_pose_of_record": "x_R12 (the house record rounding)",
        }
        x_rec = np.array([rnd(v) for v in x_full])
        pose_bonds = {}
        for side in ("L", "R"):
            h = dv.hip[side]
            for i, nm in enumerate(("flexion", "adduction", "rotation")):
                pose_bonds[h["bond"] + "." + nm] = {
                    "bond": h["bond"], "coordinate": nm,
                    "range_rad": h["range"][i],
                    "theta": rnd(x_rec[(0 if side == "L" else 3) + i])}
        pose_bonds[dv.knee["L"]["bond"]] = {"coordinate": "knee_angle", "theta": rnd(x_rec[6])}
        pose_bonds[dv.knee["R"]["bond"]] = {"coordinate": "knee_angle", "theta": rnd(x_rec[7])}
        pose_bonds[dv.driver["L"]["bond"]] = {"coordinate": "subtalar_class", "theta": rnd(x_rec[8])}
        pose_bonds[dv.driver["R"]["bond"]] = {"coordinate": "subtalar_class", "theta": rnd(x_rec[9])}
        for side in ("L", "R"):
            for b in dv.elbow[side]["bonds"]:
                pose_bonds[b] = {"coordinate": "elbow_flexion",
                                 "theta": rnd(dv.elbow[side]["forced_theta"])}
        for b in ("bond.joint_10_12", "bond.joint_11_13", "bond.joint_07_18",
                  "bond.joint_22_25", "bond.joint_23_24"):
            pose_bonds[b] = {"coordinate": "at_rest", "theta": 0.0}
        for b in ("bond.joint_06_20", "bond.joint_07_21"):
            pose_bonds[b] = {"coordinate": None, "theta": None, "class": "syndesmosis_nodof"}
        for b in ("bond.joint_02_15", "bond.joint_03_17", "bond.joint_04_08", "bond.joint_05_09"):
            pose_bonds[b] = {"coordinate": None, "theta": None, "class": "positional_contact"}
        for b in ("bond.joint_20_25", "bond.joint_21_24"):
            pose_bonds[b] = {"coordinate": None, "theta": None,
                             "note": "loop bond: no pose variable; seat measured at the pose"}
        record["pose_bonds"] = pose_bonds
        hs, n_fix, _ = sv.heights(x_rec)
        record["clearance_at_pose_of_record"] = {
            "per_membrane_h_min_mm": {("bone_%02d" % r): rnd(hs[r][0]) for r in NONPAD_BONES},
            "min_non_pad_h_min_mm": rnd(min(hs[r][0] for r in NONPAD_BONES)),
            "skull_region_h_min_mm": rnd(sv.skull_window_hmin(x_rec)[0]),
            "plane_normal_ct": [rnd(v) for v in n_fix],
            "pad_report": {("bone_%02d" % r): {k: rnd(v) for k, v in
                            zip(("h_cen_mm", "h_min_mm", "h_max_mm"), sv.pad_report(x_rec)[r])}
                           for r in (8, 9, 22, 23)},
        }
    else:
        # OUTCOME I: the maximin best-effort, both declared starts.
        record["outcome"] = "I"
        mx = {}
        for name, x0 in (("rest", np.zeros(10)), ("v1_pose_of_record", sv.x_v1)):
            t0 = sv.maximin_t0(x0)
            mx[name] = sv.maximin_solve(x0, t0)
            print("maximin[%s]: success=%s status=%s '%s' | t_max=%s mm at %s "
                  "(V=%s d=%s seat_breach=%s)" % (
                      name, mx[name]["success"], mx[name]["status"], mx[name]["message"],
                      mx[name]["t_max_recomputed_mm"], mx[name]["argmin_membrane"],
                      mx[name]["V_at_pose"], mx[name]["d_at_pose"],
                      mx[name]["seat_breach_mm_recorded"]))
        lawful = [k for k in mx if mx[k]["lawful_screen_FV2"]]
        if not lawful:
            record["maximin"] = {
                "starts": mx,
                "pose_of_record": None,
                "note": "NO maximin start returned a point passing the FV2 lawfulness "
                        "screen: no maximin pose is minted; the impossibility stands on "
                        "the strict solves + the fixed-set constants (amendment 4 section 6)",
            }
        else:
            best = sorted(lawful, key=lambda k: (-mx[k]["t_max_recomputed_mm"], k))[0]
            mx["pose_of_record"] = best
            record["maximin"] = mx
            x_rec = np.array(mx[best]["x_R12"], dtype=np.float64)
            record["pose_of_record_source"] = "maximin[%s]" % best
            record["variables"] = {
                "names": ["hipL_flexion", "hipL_adduction", "hipL_rotation",
                          "hipR_flexion", "hipR_adduction", "hipR_rotation",
                          "kneeL", "kneeR", "driverL_06_25", "driverR_07_24"],
                "x_full": mx[best]["x_full"],
                "x_R12": mx[best]["x_R12"],
                "the_pose_of_record": "x_R12 (the house record rounding)",
                "t_max_mm": mx[best]["t_max_recomputed_mm"],
                "argmin_membrane": mx[best]["argmin_membrane"],
            }
            pose_bonds = {}
            for side in ("L", "R"):
                h = dv.hip[side]
                for i, nm in enumerate(("flexion", "adduction", "rotation")):
                    pose_bonds[h["bond"] + "." + nm] = {
                        "bond": h["bond"], "coordinate": nm,
                        "range_rad": h["range"][i],
                        "theta": rnd(x_rec[(0 if side == "L" else 3) + i])}
            pose_bonds[dv.knee["L"]["bond"]] = {"coordinate": "knee_angle", "theta": rnd(x_rec[6])}
            pose_bonds[dv.knee["R"]["bond"]] = {"coordinate": "knee_angle", "theta": rnd(x_rec[7])}
            pose_bonds[dv.driver["L"]["bond"]] = {"coordinate": "subtalar_class",
                                                  "theta": rnd(x_rec[8])}
            pose_bonds[dv.driver["R"]["bond"]] = {"coordinate": "subtalar_class",
                                                  "theta": rnd(x_rec[9])}
            for side in ("L", "R"):
                for b in dv.elbow[side]["bonds"]:
                    pose_bonds[b] = {"coordinate": "elbow_flexion",
                                     "theta": rnd(dv.elbow[side]["forced_theta"])}
            for b in ("bond.joint_10_12", "bond.joint_11_13", "bond.joint_07_18",
                      "bond.joint_22_25", "bond.joint_23_24"):
                pose_bonds[b] = {"coordinate": "at_rest", "theta": 0.0}
            for b in ("bond.joint_06_20", "bond.joint_07_21"):
                pose_bonds[b] = {"coordinate": None, "theta": None,
                                 "class": "syndesmosis_nodof"}
            for b in ("bond.joint_02_15", "bond.joint_03_17",
                      "bond.joint_04_08", "bond.joint_05_09"):
                pose_bonds[b] = {"coordinate": None, "theta": None,
                                 "class": "positional_contact"}
            for b in ("bond.joint_20_25", "bond.joint_21_24"):
                pose_bonds[b] = {"coordinate": None, "theta": None,
                                 "note": "loop bond: no pose variable; seat measured at the pose"}
            record["pose_bonds"] = pose_bonds
            hs, n_fix, _ = sv.heights(x_rec)
            record["clearance_at_pose_of_record"] = {
                "per_membrane_h_min_mm": {("bone_%02d" % r): rnd(hs[r][0])
                                          for r in NONPAD_BONES},
                "min_non_pad_h_min_mm": rnd(min(hs[r][0] for r in NONPAD_BONES)),
                "skull_region_h_min_mm": rnd(sv.skull_window_hmin(x_rec)[0]),
                "plane_normal_ct": [rnd(v) for v in n_fix],
                "pad_report": {("bone_%02d" % r): {k: rnd(v) for k, v in
                                zip(("h_cen_mm", "h_min_mm", "h_max_mm"),
                                    sv.pad_report(x_rec)[r])}
                               for r in (8, 9, 22, 23)},
                "T3_verdict_primary_epsilon": bool(min(hs[r][0] for r in NONPAD_BONES)
                                                   >= EPSILON_MM),
                "T5_verdict_primary_epsilon": bool(sv.skull_window_hmin(x_rec)[0] >= EPSILON_MM),
            }

    text = json.dumps(sanitize(record), indent=1, sort_keys=True, ensure_ascii=True) + "\n"
    OUT.write_bytes(text.encode("utf-8"))
    (HERE / "pose_v2.sha256").write_text(
        hashlib.sha256(text.encode("utf-8")).hexdigest() + "\n")
    print("pose_v2 written:", OUT)
    print("OUTCOME:", record["outcome"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
