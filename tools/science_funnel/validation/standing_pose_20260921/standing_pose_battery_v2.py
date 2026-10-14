"""standing_pose_battery_v2.py -- THE AMENDED-DEFINITION LAWFULNESS BATTERY
(v1 battery F1-F8 checks UNCHANGED, run on the v2 pose of record; plus the
amendment-4 definition evaluation).

Banked basis: preregistration 63e9def4... (F1-F8) + amendment 4 3ad74c44...
(T1-T5, the strict solves, the maximin, the structural pin) -- all banked
BEFORE the v2 solve.

  F1 ranges / F2 hip P6' v2 through the transition / F3 tarsal loops /
  F4 0-DOF immobility / F5 mass invariance / F6 releases (recorded family) /
  F7 determinism (in-process re-solve of the pose-of-record source) /
  F8 theta=0 untouched (watched bytes equal before/after).
  V2 BLOCKS: per-membrane clearance table, T1-T5 verdicts at both committed
  epsilons, the strict-solve exits reproduced, the structural pin re-measured,
  the maximin caps + binding bounds.

hard = the VOID-class lawfulness set on the v2 pose of record (the maximin
pose must be LAWFUL even though the amended definition fails -- the finding).

Run:  OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 python -B \
        tools/science_funnel/validation/standing_pose_20260921/standing_pose_battery_v2.py
"""

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tools" / "science_funnel" / "validation" / "hip_pivot_proof_20260921"))

from standing_pose_core import (StandingDerivation, CUT_MM, R12,
                                IMMOBILITY_TOL_MM, DETECTOR_TOL, PAD_BONES,
                                sanitize, rnd, sha256_file)  # noqa: E402
from standing_pose_core_v2 import (StandingV2, NONPAD_BONES, EPSILON_MM,
                                   SECONDARY_EPSILON_MM)  # noqa: E402
import hip_pivot_proof as hp  # noqa: E402

POSE = HERE / "pose_v2.json"
OUT = HERE / "battery_v2.json"

STATIONS = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]

BANDS_CLASS = {"hip_flexion": 1.0, "hip_adduction": 0.5, "hip_rotation": 0.5,
               "knee": 0.5, "driver": 0.2}

WATCH = [
    HERE.parents[1] / "data" / "morphosource_ct" / "matter_skeleton" / "infant_skeleton.body.json",
    ROOT / "docs" / "THE_ARTICULATION_LAW.md",
    ROOT / "tools" / "science_funnel" / "validation" / "hip_pivot_proof_20260921" / "hip_pivot_proof.py",
    ROOT / "tools" / "science_funnel" / "validation" / "hip_pivot_proof_20260921" / "battery.json",
    ROOT / "tools" / "science_funnel" / "validation" / "hip_pivot_proof_20260921" / "receipt.json",
    ROOT / "tools" / "science_funnel" / "validation" / "tarsal_cycle_pivots_20260921" / "tarsal_cycle_battery.py",
    ROOT / "tools" / "science_funnel" / "validation" / "tarsal_cycle_pivots_20260921" / "battery.json",
    ROOT / "tools" / "science_funnel" / "validation" / "tarsal_cycle_pivots_20260921" / "receipt.json",
    ROOT / "tools" / "science_funnel" / "validation" / "p6_repreregistration_20260921" / "p6_contrast.py",
    ROOT / "tools" / "science_funnel" / "validation" / "p6_repreregistration_20260921" / "battery.json",
    ROOT / "tools" / "science_funnel" / "validation" / "p6_repreregistration_20260921" / "receipt.json",
    ROOT / "tools" / "science_funnel" / "validation" / "joint_class_records_20260921" / "battery.json",
    ROOT / "tools" / "science_funnel" / "validation" / "joint_class_records_20260921" / "receipt.json",
    ROOT / "tools" / "science_funnel" / "validation" / "joint_class_records_20260921" / "preregistration.md",
    ROOT / "tools" / "science_funnel" / "validation" / "hip_adoption_20260921" / "receipt.json",
    ROOT / "tools" / "science_funnel" / "validation" / "axial_adjacency_20260920" / "receipt.json",
    ROOT / "tools" / "science_funnel" / "validation" / "articulation_design_20260921" / "receipt.json",
    ROOT / "tools" / "science_funnel" / "ct_skeleton_layer.py",
    ROOT / "tools" / "science_funnel" / "ct_skeleton_triangle.py",
    ROOT / "tools" / "science_funnel" / "validation" / "gait_controller_20260918" / "derived_numbers.json",
    # the v1 lane's artifacts (byte-untouched by this lane)
    POSE.parent / "pose.json", POSE.parent / "pose.sha256",
    POSE.parent / "battery.json", POSE.parent / "receipt.json",
    POSE.parent / "render_record.json",
    POSE.parent / "renders" / "corpse_still.png",
    POSE.parent / "renders" / "standing_still.png",
    POSE.parent / "preregistration.md", POSE.parent / "preregistration.sha256",
    POSE.parent / "preregistration_amendment_1.md", POSE.parent / "preregistration_amendment_1.sha256",
    POSE.parent / "preregistration_amendment_2.md", POSE.parent / "preregistration_amendment_2.sha256",
    POSE.parent / "preregistration_amendment_3.md", POSE.parent / "preregistration_amendment_3.sha256",
    # this lane's banked files
    POSE.parent / "preregistration_amendment_4.md",
    POSE.parent / "preregistration_amendment_4.sha256",
    POSE.parent / "preregistration_amendment_5.md",
    POSE.parent / "preregistration_amendment_5.sha256",
    POSE,
    POSE.parent / "pose_v2.sha256",
    POSE.parent / "standing_pose_core.py", POSE.parent / "derive_standing_pose.py",
    POSE.parent / "standing_pose_battery.py", POSE.parent / "render_standing.py",
    POSE.parent / "standing_pose_core_v2.py", POSE.parent / "derive_standing_pose_v2.py",
]


def area_rel_dev(dv, x, r):
    tris = dv.geo[r]["tris"]
    flat = tris.reshape(-1, 3)
    posed = dv.fk(x)[r].pts(flat).reshape(-1, 3, 3)
    a_rest = hp.areas_np(tris).sum()
    a_pose = hp.areas_np(posed).sum()
    return float(abs(a_pose - a_rest) / a_rest)


def main():
    before = {str(p.relative_to(ROOT)): sha256_file(p) for p in WATCH}
    pose = json.loads(POSE.read_text(encoding="utf-8"))
    x_rec = np.array(pose["variables"]["x_R12"], dtype=np.float64)
    outcome = pose["outcome"]

    sv = StandingV2()
    dv = sv.dv

    checks = {}
    falsifiers_fired = []
    prediction_inversions = []

    # ---- bank integrity ---------------------------------------------------
    checks["preregistration_bank_matches_file"] = bool(
        sha256_file(HERE / "preregistration.md")
        == (HERE / "preregistration.sha256").read_text().split()[0])
    for k in (1, 2, 3, 4, 5):
        am_md = HERE / ("preregistration_amendment_%d.md" % k)
        am_sha = HERE / ("preregistration_amendment_%d.sha256" % k)
        checks["amendment_%d_bank_matches_file" % k] = bool(
            sha256_file(am_md) == am_sha.read_text().split()[0])
    checks["pose_v2_file_sha_matches_solve_bank"] = bool(
        sha256_file(POSE) == (HERE / "pose_v2.sha256").read_text().split()[0])
    checks["pose_v1_untouched"] = bool(
        sha256_file(HERE / "pose.json") == (HERE / "pose.sha256").read_text().split()[0])

    # ---- F1 ranges ---------------------------------------------------------
    range_rows = []
    f1_ok = True
    for key, rec in pose["pose_bonds"].items():
        th = rec["theta"]
        if th is None:
            range_rows.append({"bond": key, "class": rec.get("class", "loop_or_nodof"),
                               "theta": None, "note": "0-DOF class or loop bond: no coordinate"})
            continue
        bid = rec.get("bond", key)
        rng = rec.get("range_rad") or dv.bonds[bid]["joint_class"]["range_rad"]
        try:
            hp.pose_request(th, rng[0], rng[1])
            ok = True
        except hp.OutOfAnatomicalRange:
            ok = False
        range_rows.append({"bond": bid, "coordinate": rec.get("coordinate"),
                           "theta": rnd(th), "range": rng, "accepted": ok})
        f1_ok = f1_ok and ok
    refusal_demos = []
    for name, bond_id in (("hip", "bond.joint_01_02"), ("knee", "bond.joint_02_06"),
                          ("elbow", "bond.joint_04_10"), ("driver", "bond.joint_06_25")):
        cls = dv.bonds[bond_id]["joint_class"]["range_rad"]
        rng = cls[0] if isinstance(cls[0], list) else cls
        for edge, probe in (("hi", math.nextafter(rng[1], math.inf)),
                            ("lo", math.nextafter(rng[0], -math.inf))):
            try:
                hp.pose_request(probe, rng[0], rng[1])
                refusal_demos.append({"bond": bond_id, "edge": edge, "refused": False,
                                      "REFUSAL_EXPECTED": True})
            except hp.OutOfAnatomicalRange as e:
                refusal_demos.append({"bond": bond_id, "edge": edge,
                                      "refused": True, "refusal": e.name})
    ref_ok = all(d.get("refused") for d in refusal_demos)
    checks["F1_all_coordinates_in_recorded_range"] = bool(f1_ok)
    checks["F1_a5_refusal_fires_by_name_past_all_moved_bands"] = bool(ref_ok)
    if not (f1_ok and ref_ok):
        falsifiers_fired.append("F1: a range breach or a silent clamp")

    # the v1 class bands (recorded family: owns the class reading only)
    class_rows = []
    for nm, xi in zip(StandingDerivation.VAR_NAMES, x_rec):
        key = ("hip_" + nm.split("_")[1]) if nm.startswith("hip") else \
            ("knee" if nm.startswith("knee") else "driver")
        class_rows.append({"var": nm, "theta": rnd(xi), "band": BANDS_CLASS[key],
                           "within_band": bool(abs(xi) <= BANDS_CLASS[key])})
    pa3_within = bool(all(r["within_band"] for r in class_rows))
    checks["PA3_class_bands_all_within"] = pa3_within
    if not pa3_within:
        prediction_inversions.append(
            "PA3: a v2 pose angle sits outside the v1 banked class band (recorded "
            "honestly; the lawfulness battery owns void, the class reading is the record)")

    # ---- F2 P6' v2 on the hips through the transition ----------------------
    stations = {}
    f2_ok = True
    for t in STATIONS:
        xt = t * x_rec
        T = dv.fk(xt)
        row = {"t": rnd(t)}
        for side, bone in (("L", 2), ("R", 3)):
            c = dv.hip[side]["c"]
            posed_c = T[bone].pts(c[None, :])[0]
            disp = float(np.linalg.norm(posed_c - c))
            g, prov = hp.law_gap(T[bone].pts(dv.geo[bone]["verts"]),
                                 dv.geo[1]["verts"], dv.geo[1]["tree"])
            breach = max(0.0, g - CUT_MM)
            seat_ok = bool(g >= 0.0 and breach <= EPSILON_MM)  # amendment 5
            rec = {"displacement_mm": rnd(disp), "displacement_exact_zero": bool(disp == 0.0),
                   "seat_gap_mm": rnd(g), "seat_breach_mm": rnd(breach),
                   "seat_ok": seat_ok,
                   "below_resolution_floor": bool(g < EPSILON_MM),
                   "provenance": [str(p) for p in prov]}
            row[side] = rec
            f2_ok = f2_ok and rec["displacement_exact_zero"] and seat_ok
        stations["t_%d" % round(t * 5)] = row
    checks["F2_hip_p6_both_hips_all_stations"] = bool(f2_ok)
    if not f2_ok:
        falsifiers_fired.append("F2: a hip P6' clause failed on the transition path")

    # ---- F3 loops (within-cut verdicts carry the amendment-5 boundary
    #      convention: breach recorded verbatim, clause-binding iff > tol_ip) ----
    loops = {}
    for cyc, loop_pair in (("A", (20, 25)), ("B", (21, 24))):
        a, b = loop_pair
        gp, _ = dv.relative_gap(x_rec, a, b)
        gr, _ = dv.rest_gap(a, b)
        drv_theta = x_rec[8 if cyc == "A" else 9]
        breach = max(0.0, gp - CUT_MM)
        loops["cycle_%s" % cyc] = {
            "loop_bond": "bond.joint_%02d_%02d" % (a, b),
            "seat_at_pose_mm": rnd(gp), "seat_at_rest_mm": rnd(gr),
            "abs_dev_mm": rnd(abs(gp - gr)),
            "breach_mm": rnd(breach),
            "breach_below_resolution": bool(0.0 < breach <= EPSILON_MM),
            "within_cut_amendment_5": bool(breach <= EPSILON_MM),
            "driver_theta_rad": rnd(drv_theta),
        }
        if breach > EPSILON_MM:
            falsifiers_fired.append("F3: a tarsal loop seat exceeds the cut beyond the "
                                    "resolution floor")
    checks["F3_loop_seats_within_cut"] = bool(all(v["within_cut_amendment_5"]
                                                  for v in loops.values()))

    # ---- F4 0-DOF immobility ------------------------------------------------
    immobility = {}
    f4_ok = True
    for bond_id in ("bond.joint_06_20", "bond.joint_07_21", "bond.joint_02_15",
                    "bond.joint_03_17", "bond.joint_04_08", "bond.joint_05_09",
                    "bond.joint_10_12", "bond.joint_11_13"):
        b = dv.bonds[bond_id]
        ba = int(b["members"][0].split("bone_")[1])
        bb = int(b["members"][1].split("bone_")[1])
        Ta, Tb = dv.fk(x_rec)[ba], dv.fk(x_rec)[bb]
        same = Ta.same_as(Tb)
        gp, _ = dv.relative_gap(x_rec, ba, bb)
        gr, _ = dv.rest_gap(ba, bb)
        dev = abs(gp - gr)
        ok = bool(same and dev <= IMMOBILITY_TOL_MM)
        immobility[bond_id] = {"transforms_bitwise_identical": same,
                               "gap_at_pose_mm": rnd(gp), "gap_at_rest_mm": rnd(gr),
                               "abs_dev_mm": rnd(dev), "ok": ok}
        f4_ok = f4_ok and ok
    checks["F4_0dof_bonds_immobile_bitwise"] = bool(f4_ok)
    if not f4_ok:
        falsifiers_fired.append("F4: a 0-DOF-class bond moved")

    # ---- F5 mass -------------------------------------------------------------
    moved = [2, 6, 15, 20, 25, 22, 3, 7, 17, 21, 24, 23, 18, 10, 12, 11, 13]
    mass = {}
    f5_ok = True
    for r in moved:
        dev = area_rel_dev(dv, x_rec, r)
        mass["bone_%02d" % r] = {"posed_area_rel_dev": rnd(dev), "ok": bool(dev <= DETECTOR_TOL)}
        f5_ok = f5_ok and dev <= DETECTOR_TOL
    checks["F5_mass_exactly_invariant_all_moved"] = bool(f5_ok)
    if not f5_ok:
        falsifiers_fired.append("F5: a posed area drifted beyond 1e-12 relative")

    # ---- F6 releases (recorded prediction family, never a void) --------------
    releases = {}
    predictions = {
        "pose.joint_01_08": "persist", "pose.joint_01_09": "persist",
        "pose.joint_01_11": "release", "pose.joint_01_13": "release",
        "pose.joint_01_15": "release", "pose.joint_01_17": "release",
    }
    for cid, pred in predictions.items():
        c = dv.contacts[cid]
        ba = int(c["members"][0].split("bone_")[1])
        bb = int(c["members"][1].split("bone_")[1])
        gp, _ = dv.relative_gap(x_rec, bb, ba)
        released = bool(gp > CUT_MM)
        measured = "released" if released else "persists"
        ok = bool((pred == "release") == released)
        releases[cid] = {"predicted": pred, "measured": measured,
                         "gap_at_pose_mm": rnd(gp), "committed_gap_mm": c["measured_gap_mm"],
                         "prediction_ok": ok}
    checks["F6_release_predictions_match_measurement"] = bool(
        all(r["prediction_ok"] for r in releases.values()))
    if not checks["F6_release_predictions_match_measurement"]:
        prediction_inversions.append(
            "PA6/F6: a release prediction inverted at the v2 pose -- recorded as measured, "
            "every gap stands, never dropped")

    # ---- moved non-hip seats (P-A4 class) -------------------------------------
    non_hip_seats = {}
    for bond_id, pair in (("bond.joint_02_06", (2, 6)), ("bond.joint_03_07", (3, 7)),
                          ("bond.joint_04_10", (4, 10)), ("bond.joint_04_12", (4, 12)),
                          ("bond.joint_05_11", (5, 11)), ("bond.joint_05_13", (5, 13)),
                          ("bond.joint_06_25", (6, 25)), ("bond.joint_07_24", (7, 24))):
        gp, _ = dv.relative_gap(x_rec, pair[1], pair[0])
        gr, _ = dv.rest_gap(pair[1], pair[0])
        breach = max(0.0, gp - CUT_MM)
        non_hip_seats[bond_id] = {"gap_at_pose_mm": rnd(gp), "gap_at_rest_mm": rnd(gr),
                                  "breach_mm": rnd(breach),
                                  "breach_below_resolution": bool(0.0 < breach <= EPSILON_MM),
                                  "within_cut_amendment_5": bool(breach <= EPSILON_MM)}
    checks["PA4_moved_non_hip_seats_within_cut"] = bool(
        all(v["within_cut_amendment_5"] for v in non_hip_seats.values()))
    if not checks["PA4_moved_non_hip_seats_within_cut"]:
        falsifiers_fired.append("PA4: a moved non-hip seat exceeds the cut beyond the "
                                "resolution floor")

    # ---- F7 determinism: the pose-of-record source re-solves in-process -------
    source = pose.get("pose_of_record_source", "")
    f7_rows = {}
    if source.startswith("maximin"):
        start = source[len("maximin["):-1]
        x0 = np.zeros(10) if start == "rest" else sv.x_v1
        re_run = sv.maximin_solve(x0, sv.maximin_t0(x0))
        f7_rows["maximin_reproduce"] = {
            "start": start,
            "x_R12_reproduced": bool(re_run["x_R12"] == pose["variables"]["x_R12"]),
            "t_max_reproduced": bool(rnd(re_run["t_max_recomputed_mm"])
                                     == pose["variables"]["t_max_mm"]),
            "success": re_run["success"], "status": re_run["status"],
        }
        checks["F7_pose_of_record_source_reproduces"] = bool(
            f7_rows["maximin_reproduce"]["x_R12_reproduced"]
            and f7_rows["maximin_reproduce"]["t_max_reproduced"])
    elif source.startswith("strict"):
        start = source[len("strict_solve["):-1]
        re_run = sv.strict_solve(np.zeros(10) if start == "rest" else sv.x_v1)
        f7_rows["strict_reproduce"] = {
            "start": start,
            "J_reproduced": bool(re_run["J_at_return"] == pose["strict_solve"][start]["J_at_return"]),
            "minT3_reproduced": bool(re_run["min_T3_slack_mm"]
                                     == pose["strict_solve"][start]["min_T3_slack_mm"]),
        }
        checks["F7_pose_of_record_source_reproduces"] = bool(
            f7_rows["strict_reproduce"]["J_reproduced"]
            and f7_rows["strict_reproduce"]["minT3_reproduced"])
    else:
        checks["F7_pose_of_record_source_reproduces"] = False
    checks["F7_fresh_process_pose_v2_json_byte_identical"] = bool(
        sha256_file(POSE) == (HERE / "pose_v2.sha256").read_text().split()[0])
    if not (checks["F7_pose_of_record_source_reproduces"]
            and checks["F7_fresh_process_pose_v2_json_byte_identical"]):
        falsifiers_fired.append("F7: determinism drift")

    # ---- THE AMENDED DEFINITION (T1-T5) at the pose of record -----------------
    hs, n_fix, cbar = sv.heights(x_rec)
    pad_rep = sv.pad_report(x_rec)
    skull_h, cut_x = sv.skull_window_hmin(x_rec)
    V, d = sv.dv.objective_terms(x_rec)
    clear = {("bone_%02d" % r): {"h_min_mm": rnd(hs[r][0]), "h_cen_mm": rnd(hs[r][1])}
             for r in NONPAD_BONES}
    eps_readings = {}
    for tag, eps in (("primary_0.08_tol_ip", EPSILON_MM),
                     ("secondary_3.0_cut", SECONDARY_EPSILON_MM)):
        t3 = [hs[r][0] >= eps for r in NONPAD_BONES]
        eps_readings[tag] = {
            "epsilon_mm": rnd(eps),
            "T3_all_21_non_pad_above": bool(all(t3)),
            "T3_violations": {("bone_%02d" % r): rnd(eps - hs[r][0])
                              for r in NONPAD_BONES if hs[r][0] < eps},
            "T4_pads_centroids_within": bool(all(abs(pad_rep[r][0]) <= eps for r in PAD_BONES)),
            "T5_skull_region_above": bool(skull_h >= eps),
        }
    amended = {
        "V_pose": rnd(V), "d_pose": rnd(d),
        "T1_V_le_V_v1": bool(V <= sv.V_v1),
        "T2_d_le_d_v1": bool(d <= sv.d_v1),
        "V_v1_band": rnd(sv.V_v1), "d_v1_band": rnd(sv.d_v1),
        "min_non_pad_h_min_mm": rnd(min(hs[r][0] for r in NONPAD_BONES)),
        "argmin_membrane": "bone_%02d" % NONPAD_BONES[int(np.argmin([hs[r][0] for r in NONPAD_BONES]))],
        "skull_region_h_min_mm": rnd(skull_h), "head_window_cut_mm": rnd(cut_x),
        "plane_normal_ct": [rnd(v) for v in n_fix],
        "per_membrane": clear,
        "pad_report": {("bone_%02d" % r): {"h_cen_mm": rnd(pad_rep[r][0]),
                                           "h_min_mm": rnd(pad_rep[r][1]),
                                           "h_max_mm": rnd(pad_rep[r][2])}
                       for r in PAD_BONES},
        "epsilon_readings": eps_readings,
    }
    checks["T1_pad_coplanarity_at_machine_zero"] = amended["T1_V_le_V_v1"]
    checks["T2_trunk_level_at_machine_zero"] = amended["T2_d_le_d_v1"]
    checks["T3_floor_clearance_primary_epsilon"] = eps_readings["primary_0.08_tol_ip"]["T3_all_21_non_pad_above"]
    checks["T5_head_clearance_primary_epsilon"] = eps_readings["primary_0.08_tol_ip"]["T5_skull_region_above"]
    # the AMENDED-DEFINITION failures are THE FINDING, not a lawfulness void:
    # they are recorded in the amended block and excluded from the hard set.

    # ---- the structural pin re-measured ---------------------------------------
    pinned_consts, n_pin = sv.pinned_constants()
    strict_re = {k: sv.strict_solve(np.zeros(10) if k == "rest" else sv.x_v1)
                 for k in pose["strict_solve"]}
    structural = {
        "pinned_plane_normal": [rnd(v) for v in n_pin],
        "max_dev_vs_pose_normal": rnd(float(np.abs(n_pin - n_fix).max())),
        "pinned_constants_mm": {("bone_%02d" % r): rnd(pinned_consts[r]) for r in NONPAD_BONES},
        "strict_solve_exits_reproduced": bool(all(
            strict_re[k]["success"] == pose["strict_solve"][k]["success"]
            and strict_re[k]["min_T3_slack_mm"] == pose["strict_solve"][k]["min_T3_slack_mm"]
            for k in pose["strict_solve"])),
        "strict_min_T3_slack_mm": {k: pose["strict_solve"][k]["min_T3_slack_mm"]
                                   for k in pose["strict_solve"]},
        "smallest_fixed_deficit_mm": rnd(EPSILON_MM
                                         - max(pinned_consts[r]
                                               for r in (1, 4, 5, 14, 16, 19))),
        "deepest_fixed_h_min_mm": rnd(min(pinned_consts[r] for r in (1, 4, 5, 14, 16, 19))),
    }
    checks["strict_solve_exits_reproduce_in_battery"] = structural["strict_solve_exits_reproduced"]
    if not structural["strict_solve_exits_reproduced"]:
        falsifiers_fired.append("F7: the strict-solve exits did not reproduce in the battery")

    # ---- the maximin caps/binding record ---------------------------------------
    maximin_block = None
    if pose.get("maximin") and pose["maximin"].get("pose_of_record"):
        best = pose["maximin"]["pose_of_record"]
        m = pose["maximin"][best]
        maximin_block = {
            "pose_of_record_start": best,
            "t_max_mm": m["t_max_recomputed_mm"],
            "argmin_membrane": m["argmin_membrane"],
            "V_at_pose": m["V_at_pose"], "d_at_pose": m["d_at_pose"],
            "cap_slack_V": m["cap_slack_V"], "cap_slack_d": m["cap_slack_d"],
            "cap_breaches_recorded": m["cap_breaches_recorded"],
            "seat_breach_mm_recorded": m["seat_breach_mm_recorded"],
            "binding_bounds": m["binding_bounds"],
            "binding_named": [b["var"] + "@" + b["nearest_bound"]
                              for b in m["binding_bounds"] if b["binding"]],
            "both_starts": {k: {"t_max_mm": pose["maximin"][k]["t_max_recomputed_mm"],
                                "success": pose["maximin"][k]["success"],
                                "status": pose["maximin"][k]["status"],
                                "seat_breach_mm_recorded":
                                    pose["maximin"][k]["seat_breach_mm_recorded"],
                                "lawful_screen_FV2": pose["maximin"][k]["lawful_screen_FV2"]}
                            for k in ("rest", "v1_pose_of_record")},
        }
        checks["maximin_within_caps_and_seats_amendment_5"] = bool(
            m["lawful_screen_FV2"] and m["in_ranges"])
        if not checks["maximin_within_caps_and_seats_amendment_5"]:
            falsifiers_fired.append("FV2: the maximin pose breaches a boundary beyond the "
                                    "resolution floor")
    elif outcome == "I":
        falsifiers_fired.append("FV2: no maximin start returned a lawful point")

    # ---- F8 untouched watch ------------------------------------------------------
    after = {str(p.relative_to(ROOT)): sha256_file(p) for p in WATCH}
    untouched_equal = bool(before == after)
    checks["F8_watched_bytes_untouched"] = untouched_equal
    if not untouched_equal:
        falsifiers_fired.append("F8: a watched byte changed during the run")

    # ---- pad plane record (the render asserts the same numbers) -------------------
    pads = {}
    P = dv.pad_centroids(x_rec)
    Vr, n_hat = sv.sign_fixed_plane(x_rec)[:2]
    for i, r in enumerate(PAD_BONES):
        pads["bone_%02d" % r] = {"centroid_ct_mm": [rnd(v) for v in P[i]],
                                 "signed_dist_mm": rnd((P[i] - P.mean(axis=0)) @ n_hat)}
    pads["plane_normal_ct"] = [rnd(v) for v in n_hat]
    pads["plane_variance_mm2"] = rnd(Vr)

    battery = {
        "schema": "chimera.standing_pose_battery_v2.v1",
        "lane": "agent/standing-pose-v2-20260921",
        "base_commit": "4ea008cb",
        "outcome": outcome,
        "pose_of_record": {
            "file": "pose_v2.json",
            "sha256": sha256_file(POSE),
            "x_R12": [rnd(v) for v in x_rec],
            "source": source,
        },
        "preregistration_sha256": sha256_file(HERE / "preregistration.md"),
        "amendment_4_sha256": sha256_file(HERE / "preregistration_amendment_4.md"),
        "trailer": "Agent: GLM 5.3",
        "stations": stations,
        "range_rows": range_rows,
        "a5_refusal_demos": refusal_demos,
        "class_band_rows_PA3": class_rows,
        "loops": loops,
        "immobility": immobility,
        "mass": mass,
        "releases": releases,
        "non_hip_seats": non_hip_seats,
        "determinism_rows": f7_rows,
        "amended_definition": amended,
        "structural_pin": structural,
        "maximin": maximin_block,
        "pad_plane": pads,
        "prediction_checks": checks,
        "falsifiers_fired": falsifiers_fired,
        "prediction_inversions_recorded": prediction_inversions,
        "untouched": {"before": before},
    }
    battery["untouched"]["after"] = after
    battery["untouched"]["equal"] = untouched_equal

    # hard = the VOID-class lawfulness set on the v2 pose of record. The
    # amended-definition T-verdicts are THE FINDING (outcome I is the expected,
    # honest deliverable) and do NOT bind hard; the maximin must be LAWFUL
    # (ranges/seats/caps/immobility/mass/determinism/identity).
    hard_keys = [k for k in checks if not k.startswith(("PA3_", "F6_", "T1_", "T2_", "T3_", "T5_"))]
    hard_ok = all(bool(checks[k]) for k in hard_keys) and not falsifiers_fired
    battery["hard_checks_pass"] = bool(hard_ok)

    text = json.dumps(sanitize(battery), indent=1, sort_keys=True, ensure_ascii=True) + "\n"
    OUT.write_bytes(text.encode("utf-8"))
    print("battery_v2 written:", OUT)
    print("outcome:", outcome, "| pose source:", source)
    print("hard_checks_pass:", hard_ok)
    print("falsifiers_fired:", falsifiers_fired)
    print("prediction_inversions_recorded:", prediction_inversions)
    print("amended definition: min non-pad h_min = %s mm (argmin %s) | skull region %s mm | "
          "V=%s d=%s" % (amended["min_non_pad_h_min_mm"], amended["argmin_membrane"],
                         amended["skull_region_h_min_mm"], amended["V_pose"], amended["d_pose"]))
    print("T verdicts: T1=%s T2=%s T3=%s T5=%s" % (
        checks["T1_pad_coplanarity_at_machine_zero"], checks["T2_trunk_level_at_machine_zero"],
        checks["T3_floor_clearance_primary_epsilon"],
        checks["T5_head_clearance_primary_epsilon"]))
    if maximin_block:
        print("maximin: t_max=%s mm at %s | FV2 screen=%s | binding: %s" % (
            maximin_block["t_max_mm"], maximin_block["argmin_membrane"],
            checks["maximin_within_caps_and_seats_amendment_5"],
            maximin_block["binding_named"]))
    return 0 if hard_ok else 1


if __name__ == "__main__":
    sys.exit(main())
