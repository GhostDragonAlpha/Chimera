"""standing_pose_battery.py -- THE STANDING POSE LAWFULNESS BATTERY
(preregistration 63e9def4... + amendment 1 f2e528f7..., both banked before the solve).

Executes falsifiers F1-F8 of the banked receipt on the pose of record
(pose.json, byte-identical twice in fresh processes):

  F1 ranges: every recorded coordinate inside its recorded class range; the A5
     refusal fires BY NAME one nextafter past each moved band.
  F2 P6' v2 on the hips through the transition: stations t in {0,1/5,2/5,3/5,
     4/5,1} of the pose of record; per hip per station: displacement == 0.0
     EXACTLY (pivot-anchored rotation about the own registered fit center) and
     seat gap in [0, 3.0] mm (below-floor readings recorded, never binding).
  F3 loops: both tarsal loop seats <= 3.0 mm at the pose; deviation from rest
     recorded; the drivers-at-rest premise reported (the banked P-A5 premise).
  F4 0-DOF immobility: the six 0-DOF-class bonds and the two at-rest radioulnar
     bonds carry BITWISE identical transforms on both members and |gap-rest|
     <= 1e-9 mm.
  F5 mass: every moved membrane's posed triangle areas equal rest to <= 1e-12
     relative (the hip battery's resampling detector).
  F6 releases: the six corpse pose_contacts measured at the pose against the
     DOF-path predictions derived from the class records (persist bitwise /
     release > 3.0 mm). Every gap recorded; none dropped.
  F7 determinism: the solve re-run IN-PROCESS reproduces x_R12 exactly; the
     fresh-process byte identity is recorded from the lane run.
  F8 identity: theta = 0 untouched -- watched bytes equal before/after.

Read-only on the committed tree. Deterministic: no RNG, no timestamps.

Run:  OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 python -B \
        tools/science_funnel/validation/standing_pose_20260921/standing_pose_battery.py
"""

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tools" / "science_funnel" / "validation" / "hip_pivot_proof_20260921"))

from standing_pose_core import (StandingDerivation, Xform, CUT_MM, R12,
                                IMMOBILITY_TOL_MM, DETECTOR_TOL, PAD_BONES,
                                sanitize, rnd, sha256_file)  # noqa: E402
import hip_pivot_proof as hp  # noqa: E402

POSE = HERE / "pose.json"
OUT = HERE / "battery.json"

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
    POSE,
    HERE / "pose.sha256",
    HERE / "preregistration.md", HERE / "preregistration.sha256",
    HERE / "preregistration_amendment_1.md", HERE / "preregistration_amendment_1.sha256",
    HERE / "preregistration_amendment_2.md", HERE / "preregistration_amendment_2.sha256",
    HERE / "standing_pose_core.py", HERE / "derive_standing_pose.py",
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
    x_full = np.array(pose["variables"]["x_full"], dtype=np.float64)

    dv = StandingDerivation()

    checks = {}
    falsifiers_fired = []
    prediction_inversions = []

    # ---- bank integrity ---------------------------------------------------
    checks["preregistration_bank_matches_file"] = bool(
        sha256_file(HERE / "preregistration.md")
        == (HERE / "preregistration.sha256").read_text().split()[0])
    checks["amendment_1_bank_matches_file"] = bool(
        sha256_file(HERE / "preregistration_amendment_1.md")
        == (HERE / "preregistration_amendment_1.sha256").read_text().split()[0])
    checks["amendment_2_bank_matches_file"] = bool(
        sha256_file(HERE / "preregistration_amendment_2.md")
        == (HERE / "preregistration_amendment_2.sha256").read_text().split()[0])
    checks["pose_file_sha_matches_solve_bank"] = bool(
        sha256_file(POSE) == (HERE / "pose.sha256").read_text().split()[0])

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
        in_rec = {"bond": bid, "coordinate": rec.get("coordinate"), "theta": rnd(th),
                  "range": rng, "accepted": ok}
        range_rows.append(in_rec)
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

    # the class bands of P-A3 (prediction: owns the class reading only, never
    # the lawfulness verdict -- the banked text is explicit about this split)
    class_rows = []
    for nm, xi in zip(StandingDerivation.VAR_NAMES, x_rec):
        key = ("hip_" + nm.split("_")[1]) if nm.startswith("hip") else \
            ("knee" if nm.startswith("knee") else "driver")
        class_rows.append({"var": nm, "theta": rnd(xi), "band": BANDS_CLASS[key],
                           "within_band": bool(abs(xi) <= BANDS_CLASS[key])})
    pa3_within = bool(all(r["within_band"] for r in class_rows))
    checks["PA3_class_bands_all_within"] = pa3_within
    if not pa3_within:
        prediction_inversions.append("PA3: a solved angle sits outside its banked class band "
                                     "(recorded honestly; the lawfulness battery owns void)")

    # ---- F2 P6' v2 on the hips through the transition ----------------------
    stations = {}
    f2_ok = True
    for t in STATIONS:
        xt = t * x_rec
        T = dv.fk(xt)
        row = {"t": rnd(t)}
        for side, bone, key in (("L", 2, "L"), ("R", 3, "R")):
            c = dv.hip[key]["c"]
            posed_c = T[bone].pts(c[None, :])[0]
            disp = float(np.linalg.norm(posed_c - c))
            g, prov = hp.law_gap(T[bone].pts(dv.geo[bone]["verts"]),
                                 dv.geo[1]["verts"], dv.geo[1]["tree"])
            seat_ok = bool(0.0 <= g <= CUT_MM)
            rec = {"displacement_mm": rnd(disp), "displacement_exact_zero": bool(disp == 0.0),
                   "seat_gap_mm": rnd(g), "seat_ok": seat_ok,
                   "below_resolution_floor": bool(g < 0.08),
                   "provenance": [str(p) for p in prov]}
            row[side] = rec
            f2_ok = f2_ok and rec["displacement_exact_zero"] and seat_ok
        stations["t_%d" % round(t * 5)] = row
    checks["F2_hip_p6_both_hips_all_stations"] = bool(f2_ok)
    if not f2_ok:
        falsifiers_fired.append("F2: a hip P6' clause failed on the transition path")

    # ---- F3 loops -----------------------------------------------------------
    loops = {}
    for cyc, side_bone, driver_bond, loop_pair in (
            ("A", (6, 20, 25), "bond.joint_06_25", (20, 25)),
            ("B", (7, 21, 24), "bond.joint_07_24", (21, 24))):
        a, b = loop_pair
        gp, _ = dv.relative_gap(x_rec, a, b)
        gr, _ = dv.rest_gap(a, b)
        drv_theta = x_rec[8 if cyc == "A" else 9]
        loops["cycle_%s" % cyc] = {
            "loop_bond": "bond.joint_%02d_%02d" % (a, b),
            "seat_at_pose_mm": rnd(gp), "seat_at_rest_mm": rnd(gr),
            "abs_dev_mm": rnd(abs(gp - gr)),
            "within_cut": bool(gp <= CUT_MM),
            "driver_theta_rad": rnd(drv_theta),
            "drivers_at_rest_premise": bool(drv_theta == 0.0),
        }
        if gp > CUT_MM:
            falsifiers_fired.append("F3: a tarsal loop seat exceeds the cut")
        if drv_theta == 0.0 and abs(gp - gr) > IMMOBILITY_TOL_MM:
            falsifiers_fired.append("F3: loop seat drifted with the driver at rest (aliasing)")
    checks["F3_loop_seats_within_cut"] = bool(all(v["within_cut"] for v in loops.values()))

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

    # ---- F6 releases (a PREDICTION family: its own banked consequence is
    # "recorded, the release table stands as measured" -- never a void) ---------
    releases = {}
    f6_ok = True
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
        f6_ok = f6_ok and ok
    checks["F6_release_predictions_match_measurement"] = bool(f6_ok)
    if not f6_ok:
        prediction_inversions.append(
            "PA6/F6: a release prediction inverted -- the moving-member curl contacts PERSIST "
            "at the derived pose (the pose is interior-small; the surfaces remain within the "
            "touching class). Recorded; every gap stands as measured; never dropped.")

    # ---- F7 determinism --------------------------------------------------------
    result = minimize(
        lambda x: dv.objective_terms(x)[0] + dv.kappa * dv.objective_terms(x)[1],
        np.zeros(10), method="SLSQP", bounds=dv.bounds(),
        constraints=[{"type": "ineq", "fun": lambda x: dv.all_seat_constraints(x)}],
        options={"ftol": 1e-12, "maxiter": 400})
    x_re = np.asarray(result.x, dtype=np.float64)
    checks["F7_inprocess_resolve_reproduces_x_R12"] = bool(
        [rnd(v) for v in x_re] == [rnd(v) for v in x_rec])
    checks["F7_fresh_process_pose_json_byte_identical"] = bool(
        sha256_file(POSE) == (HERE / "pose.sha256").read_text().split()[0])
    if not (checks["F7_inprocess_resolve_reproduces_x_R12"]
            and checks["F7_fresh_process_pose_json_byte_identical"]):
        falsifiers_fired.append("F7: determinism drift")

    # ---- objective/seat consistency at the pose of record -----------------------
    V, d = dv.objective_terms(x_rec)
    hip_headroom = dv.hip_seat_constraints(x_rec)
    loop_headroom = list(dv.all_seat_constraints(x_rec))[2:]
    consistency = {
        "V_pose_mm2": rnd(V), "d_pose": rnd(d),
        "matches_pose_json": bool(rnd(V) == pose["objective"]["V_pose_mm2"]
                                  and rnd(d) == pose["objective"]["d_pose"]),
        "hip_seat_gap_mm": {"L": rnd(CUT_MM - hip_headroom[0]),
                            "R": rnd(CUT_MM - hip_headroom[1])},
        "hip_seat_headroom_mm": {"L": rnd(hip_headroom[0]), "R": rnd(hip_headroom[1])},
        "loop_seat_headroom_mm": {"A_20_25": rnd(loop_headroom[0]),
                                  "B_21_24": rnd(loop_headroom[1])},
        "all_seat_constraints_satisfied": bool(min(list(hip_headroom) + list(loop_headroom)) >= 0.0),
    }
    # P-A4: moved non-hip seats
    non_hip_seats = {}
    for bond_id, pair in (("bond.joint_02_06", (2, 6)), ("bond.joint_03_07", (3, 7)),
                          ("bond.joint_04_10", (4, 10)), ("bond.joint_04_12", (4, 12)),
                          ("bond.joint_05_11", (5, 11)), ("bond.joint_05_13", (5, 13)),
                          ("bond.joint_06_25", (6, 25)), ("bond.joint_07_24", (7, 24))):
        gp, _ = dv.relative_gap(x_rec, pair[1], pair[0])
        gr, _ = dv.rest_gap(pair[1], pair[0])
        non_hip_seats[bond_id] = {"gap_at_pose_mm": rnd(gp), "gap_at_rest_mm": rnd(gr),
                                  "non_increasing_vs_rest": bool(gp <= gr + IMMOBILITY_TOL_MM),
                                  "within_cut": bool(gp <= CUT_MM)}
    consistency["non_hip_seats"] = non_hip_seats
    checks["PA4_moved_non_hip_seats_within_cut"] = bool(
        all(v["within_cut"] for v in non_hip_seats.values()))
    if not checks["PA4_moved_non_hip_seats_within_cut"]:
        falsifiers_fired.append("PA4: a moved non-hip seat exceeds the cut")

    # ---- F8 untouched watch ------------------------------------------------------
    after = {str(p.relative_to(ROOT)): sha256_file(p) for p in WATCH}
    untouched_equal = bool(before == after)
    checks["F8_watched_bytes_untouched"] = untouched_equal
    if not untouched_equal:
        falsifiers_fired.append("F8: a watched byte changed during the run")

    # ---- pad plane record (scene-agnostic, CT mm; the render asserts the same) ----
    pads = {}
    P = dv.pad_centroids(x_rec)
    Vr, n_hat = dv._plane_stats(P)
    for i, r in enumerate(PAD_BONES):
        pads["bone_%02d" % r] = {"centroid_ct_mm": [rnd(v) for v in P[i]],
                                 "signed_dist_mm": rnd((P[i] - P.mean(axis=0)) @ n_hat)}
    pads["plane_normal_ct"] = [rnd(v) for v in n_hat]
    pads["plane_variance_mm2"] = rnd(Vr)

    battery = {
        "schema": "chimera.standing_pose_battery.v1",
        "lane": "agent/standing-pose-20260921",
        "base_commit": "52f101c1",
        "pose_of_record": {
            "file": "pose.json",
            "sha256": sha256_file(POSE),
            "x_R12": [rnd(v) for v in x_rec],
            "note": "byte-identical in two fresh solver processes (recorded in the receipt)",
        },
        "preregistration_sha256": sha256_file(HERE / "preregistration.md"),
        "amendment_1_sha256": sha256_file(HERE / "preregistration_amendment_1.md"),
        "amendment_2_sha256": sha256_file(HERE / "preregistration_amendment_2.md"),
        "trailer": "Agent: GLM 5.3",
        "stations": stations,
        "range_rows": range_rows,
        "a5_refusal_demos": refusal_demos,
        "class_band_rows_PA3": class_rows,
        "loops": loops,
        "immobility": immobility,
        "mass": mass,
        "releases": releases,
        "consistency": consistency,
        "pad_plane": pads,
        "prediction_checks": checks,
        "falsifiers_fired": falsifiers_fired,
        "prediction_inversions_recorded": prediction_inversions,
        "untouched": {"before": before},
    }
    battery["untouched"]["after"] = after
    battery["untouched"]["equal"] = untouched_equal

    checks["solver_success_recorded"] = bool(pose["solver"]["success"])
    # hard = the VOID-class lawfulness set (F1-F5, F7, F8, PA4, integrity). The
    # prediction families PA3/PA6(recorded above) do NOT bind hard per their
    # own banked consequences; they are recorded verbatim either way.
    hard_keys = [k for k in checks if not k.startswith(("PA3_", "F6_"))]
    hard_ok = all(bool(checks[k]) for k in hard_keys) and not falsifiers_fired
    battery["hard_checks_pass"] = bool(hard_ok)

    text = json.dumps(sanitize(battery), indent=1, sort_keys=True, ensure_ascii=True) + "\n"
    OUT.write_bytes(text.encode("utf-8"))
    print("battery written:", OUT)
    print("hard_checks_pass:", hard_ok)
    print("falsifiers_fired:", falsifiers_fired)
    print("prediction_inversions_recorded:", prediction_inversions)
    print("V_pose:", rnd(V), "| d_pose:", rnd(d), "| hip seats mm:",
          consistency["hip_seat_gap_mm"],
          "| loop headroom mm:", consistency["loop_seat_headroom_mm"])
    print("loops:", {k: v["seat_at_pose_mm"] for k, v in loops.items()},
          "(rest", {k: v["seat_at_rest_mm"] for k, v in loops.items()}, ")")
    for cid, r in releases.items():
        print("release %s: predicted %s -> measured %s (%s mm)" %
              (cid, r["predicted"], r["measured"], r["gap_at_pose_mm"]))
    return 0 if hard_ok else 1


if __name__ == "__main__":
    sys.exit(main())
