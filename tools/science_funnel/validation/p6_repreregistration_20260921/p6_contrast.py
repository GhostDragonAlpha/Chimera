"""THE P6 RE-PREREGISTRATION CONTRAST BATTERY, predicate v2
(preregistration 3cbb37d8... + amendment 3, banked before THIS run).

Executes the CORRECTED two-arm contrast of docs/THE_ARTICULATION_LAW.md §5B
(§5A's own falsifier L6 fired on run 1: seated rigid impingement at d == 0.0
exactly reads 0.053906119839 mm — below any mesh-derived localization — so the
hard lower edge was the mis-derivation) on the two committed hip bonds:

  - LEG 1: the seat band [0, cut] — contact is IN the touching class; cut =
    3.0 mm committed. The interpenetration tolerance KEEPS its derived value
    tol_ip = specimen.resolution_um / 2 = 0.08 mm as the gap metric's
    RESOLUTION FLOOR: readings below it lie inside the surfaces' own
    localization (seated-impingement contact and through-crossing are both
    unresolvable there) — RECORDED per pose, never clause-binding.
  - LEG 2 (load-bearing, the not-through test at the head): the head-center
    displacement band d(theta) = |pose(c*) - c*| <= band_h, the registered
    fit's own RMS residual — the pivot's measured radius+residual ARE the
    socket's geometry; displacement beyond the band is a dislocation.

Arms: REAL (head-fit pivots, bilateral axis) and NULL (recorded closest-points
midpoints, registered control axis), over the derived grid
{−R} ∪ {R·k/5 : k = −4..4} ∪ {+R}.

The registered derivation is NOT re-derived here: the primitives (inlier rule,
Rodrigues, law metric) are imported from the committed
hip_pivot_proof_20260921.hip_pivot_proof module verbatim, and this battery
verifies its fits EQUAL the committed battery.json records (reproduction
guards). Zero new free numbers; no number's value changed between v1 and v2 —
one number's role did, forced by the fired falsifier (amendment 3, tuning
audit therein).

Read-only on the committed tree. Deterministic: no RNG, no timestamps, no
set-order leakage; the output JSON is byte-stable across runs.

Run:  python -B tools/science_funnel/validation/p6_repreregistration_20260921/p6_contrast.py
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
PRIOR = ROOT / "tools" / "science_funnel" / "validation" / "hip_pivot_proof_20260921"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(PRIOR))

import hip_pivot_proof as hp  # the committed module: registered primitives only

DATA = ROOT / "tools" / "science_funnel" / "data" / "morphosource_ct" / "matter_skeleton"
DEFN = DATA / "infant_skeleton.body.json"
OSIM = ROOT / "research_references" / "human" / "opensim" / "gait2392_thelen2003muscle.osim"
OSIM_SHA = "18e5b3e406a619a78d109e81e6e2cd4f58681a967808fb52a992bbd2b27db019"
PRIOB_BATTERY_SHA = "18f0ef0641cdcba610bb0a67109540220cfb3400bdff1eee2ae6451fb7d81c16"

CUT_MM = 3.0                    # committed touching-class cut (upper edge)
METRIC_TRANSFER_TOL = 0.005     # house metric-transfer tolerance
FORMULA_TOL = 1e-9              # mm; the 2*|c_perp|*sin(theta/2) reproduction bound

OUT = HERE / "battery.json"
R12 = 12


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rnd(x):
    return round(float(x), R12)


def sanitize(o):
    if isinstance(o, dict):
        return {k: sanitize(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [sanitize(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return rnd(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


def main():
    body = json.loads(DEFN.read_text(encoding="utf-8"))
    bonds = {b["id"]: b for b in body["bonds"]}
    contacts = {c["id"]: c for c in body["pose_contacts"]["contacts"]}
    mems = {m["id"]: m for m in body["membranes"]}
    committed = json.loads((PRIOR / "battery.json").read_text(encoding="utf-8"))

    watch = [
        DEFN, OSIM,
        DATA / "tris" / "bone_01.bin", DATA / "tris" / "bone_02.bin", DATA / "tris" / "bone_03.bin",
        ROOT / "tools" / "science_funnel" / "validation" / "axial_adjacency_20260920" / "receipt.json",
        ROOT / "tools" / "science_funnel" / "validation" / "hip_adoption_20260921" / "receipt.json",
        ROOT / "tools" / "science_funnel" / "validation" / "articulation_design_20260921" / "receipt.json",
        PRIOR / "preregistration.md", PRIOR / "preregistration.sha256",
        PRIOR / "preregistration_amendment_1.md", PRIOR / "preregistration_amendment_1.sha256",
        PRIOR / "preregistration_amendment_2.md", PRIOR / "preregistration_amendment_2.sha256",
        PRIOR / "battery.json", PRIOR / "receipt.json", PRIOR / "hip_pivot_proof.py",
        HERE / "preregistration.md", HERE / "preregistration.sha256",
        HERE / "preregistration_amendment_3.md", HERE / "preregistration_amendment_3.sha256",
        HERE / "law_amendment.sha256", HERE / "law_amendment_b.sha256",
        HERE / "battery_run1_predicate_v1_l6_fired.json",
        ROOT / "tools" / "science_funnel" / "validation" / "p6_repreregistration_20260921_replica" / "hip_pivot_proof.py",
        ROOT / "tools" / "science_funnel" / "validation" / "p6_repreregistration_20260921_replica" / "preregistration.md",
        ROOT / "docs" / "THE_ARTICULATION_LAW.md",
    ]
    before = {str(p.relative_to(ROOT)): sha256_file(p) for p in watch}

    # input integrity + the committed prior's identity
    osim_sha = sha256_file(OSIM)
    committed_battery_sha = sha256_file(PRIOR / "battery.json")
    committed_script_sha = sha256_file(PRIOR / "hip_pivot_proof.py")
    replica_script_sha = sha256_file(ROOT / "tools" / "science_funnel" / "validation" / "p6_repreregistration_20260921_replica" / "hip_pivot_proof.py")
    replica_prereg_sha = sha256_file(ROOT / "tools" / "science_funnel" / "validation" / "p6_repreregistration_20260921_replica" / "preregistration.md")
    lane_prereg_sha = sha256_file(HERE / "preregistration.md")
    prereg_bank = (HERE / "preregistration.sha256").read_text(encoding="utf-8").split()[0]
    amendment3_sha = sha256_file(HERE / "preregistration_amendment_3.md")
    amendment3_bank = (HERE / "preregistration_amendment_3.sha256").read_text(encoding="utf-8").split()[0]
    law_b_sha = sha256_file(ROOT / "docs" / "THE_ARTICULATION_LAW.md")
    law_b_bank = (HERE / "law_amendment_b.sha256").read_text(encoding="utf-8").split()[0]
    law_stage1_bank = (HERE / "law_amendment.sha256").read_text(encoding="utf-8").split()[0]
    run1_battery_sha = sha256_file(HERE / "battery_run1_predicate_v1_l6_fired.json")

    # committed geometry (via the committed module's loaders)
    blobs, tri_sets, vert_sets, face_sets = {}, {}, {}, {}
    for r in (1, 2, 3):
        blobs[r], tri_sets[r] = hp.load_blob(r)
        vert_sets[r], face_sets[r] = hp.unique_verts(tri_sets[r])
    tree1 = cKDTree(vert_sets[1])
    vertex_books_match = all(
        hp.vertex_records_sha(blobs[r]) == mems["mem.bone_%02d" % r]["vertex_sha256"]
        for r in (2, 3))

    # range record parsed from the committed osim
    import xml.etree.ElementTree as ET
    root = ET.parse(OSIM).getroot()
    ranges = {}
    for co in root.iter("Coordinate"):
        nm = co.get("name")
        if nm in ("hip_flexion_l", "hip_flexion_r"):
            ranges[nm] = [float(x) for x in co.find("range").text.split()]
    R = ranges["hip_flexion_l"][1]
    if ranges["hip_flexion_l"] != ranges["hip_flexion_r"]:
        raise SystemExit("asymmetric hip range record")

    # ---- THE DERIVED BANDS -------------------------------------------------
    resolution_um = body["specimen"]["resolution_um"]
    tol_ip_mm = (resolution_um / 2.0) / 1000.0   # half the committed CT sampling step, in mm

    hip_defs = [
        {"key": "02", "bond": "bond.joint_01_02", "child": 2, "side": "left",
         "osim_coord": "hip_flexion_l", "curl_contact": "pose.joint_01_15",
         "committed_fit": committed["fits"]["02"]},
        {"key": "03", "bond": "bond.joint_01_03", "child": 3, "side": "right",
         "osim_coord": "hip_flexion_r", "curl_contact": "pose.joint_01_17",
         "committed_fit": committed["fits"]["03"]},
    ]

    fits = {}
    repro_ok = True
    for hd in hip_defs:
        k = hd["key"]
        ch = hd["child"]
        bond = bonds[hd["bond"]]
        on_ch = np.array(bond["closest_points_mm"]["on_%s" % k], dtype=float)
        on_01 = np.array(bond["closest_points_mm"]["on_01"], dtype=float)
        med = float(np.median(np.concatenate([
            np.linalg.norm(tri_sets[ch][:, 1] - tri_sets[ch][:, 0], axis=1),
            np.linalg.norm(tri_sets[ch][:, 2] - tri_sets[ch][:, 1], axis=1),
            np.linalg.norm(tri_sets[ch][:, 0] - tri_sets[ch][:, 2], axis=1)])))
        fit = hp.inlier_rule(vert_sets[ch], face_sets[ch], on_ch, med)
        if fit.get("outcome") != "fixed_point":
            raise SystemExit("hip %s: fit refused (%s)" % (k, fit.get("outcome")))
        c = fit.pop("_c")
        inl = fit.pop("_inliers")
        cc, rr, gn_it = hp.sphere_fit(vert_sets[ch][inl])
        res = np.abs(np.linalg.norm(vert_sets[ch][inl] - cc, axis=1) - rr)
        rms = float(np.sqrt((res * res).mean()))
        maxres = float(res.max())
        rec = {
            "seed_vertex": fit["seed_vertex"],
            "band_eps_mm": rnd(med),
            "iterations": fit["iterations"],
            "outcome": fit["outcome"],
            "inliers": fit["inliers"],
            "center_mm": [rnd(x) for x in cc],
            "radius_mm": rnd(rr),
            "rms_residual_mm": rnd(rms),
            "max_residual_mm": rnd(maxres),
            "gauss_newton_iters_final": gn_it,
        }
        diffs = [f for f in rec if rec[f] != hd["committed_fit"][f]]
        repro_ok = repro_ok and not diffs
        hd["fit"] = {"c": cc, "radius": rr, "rms": rms, "inliers": inl,
                     "record": rec, "repro_diffs": diffs}
        hd["bond"] = bond
        hd["on_ch"] = on_ch
        hd["on_01"] = on_01
        hd["M"] = (on_01 + on_ch) / 2.0
        fits[k] = rec

    band = {hd["key"]: hd["fit"]["rms"] for hd in hip_defs}

    # axis constructions (registered)
    c2 = hip_defs[0]["fit"]["c"]
    c3 = hip_defs[1]["fit"]["c"]
    u = (c3 - c2) / np.linalg.norm(c3 - c2)
    M2, M3 = hip_defs[0]["M"], hip_defs[1]["M"]
    u_ctrl = (M3 - M2) / np.linalg.norm(M3 - M2)

    # the derived grid: endpoints exact, interior at the registered probe fraction R/5
    thetas = [(-R, "lo_endpoint"), (R, "hi_endpoint")]
    for kk in range(-4, 5):
        th = R * kk / 5.0
        lab = "rest" if kk == 0 else "grid_k%+d" % kk
        thetas.append((th, lab))
    thetas.sort(key=lambda t: t[0])

    # flexion sign (registered rule; labeling only)
    signs = {}
    for hd in hip_defs:
        k = hd["key"]
        c = hd["fit"]["c"]
        distal = int(np.argmax(np.linalg.norm(vert_sets[hd["child"]] - c, axis=1)))
        q = np.array(contacts[hd["curl_contact"]]["closest_points_mm"]["on_01"], dtype=float)
        tp = R / 5.0
        d_plus = float(np.linalg.norm(hp.rodrigues(vert_sets[hd["child"]][distal][None, :], c, u, tp)[0] - q))
        d_minus = float(np.linalg.norm(hp.rodrigues(vert_sets[hd["child"]][distal][None, :], c, u, -tp)[0] - q))
        signs[k] = 1 if d_plus < d_minus else -1

    # metric-transfer preamble at rest (house tolerance)
    transfer = {}
    for hd in hip_defs:
        k = hd["key"]
        g, prov = hp.law_gap(vert_sets[hd["child"]], vert_sets[1], tree1)
        transfer[k] = {
            "law_gap_theta0_mm": rnd(g),
            "committed_measured_gap_mm": hd["bond"]["measured_gap_mm"],
            "abs_dev_mm": rnd(abs(g - hd["bond"]["measured_gap_mm"])),
            "pass": bool(abs(g - hd["bond"]["measured_gap_mm"]) <= METRIC_TRANSFER_TOL),
        }

    # ---- THE TWO ARMS ON THE GRID ------------------------------------------
    def run_arm(pivot_for, axis_for):
        out = {}
        for hd in hip_defs:
            k = hd["key"]
            ch = hd["child"]
            c = hd["fit"]["c"]
            band_h = band[k]
            v_child = vert_sets[ch]
            rows = []
            for th, lab in thetas:
                piv = pivot_for(hd)
                ax = axis_for()
                vp = hp.rodrigues(v_child, piv, ax, th)
                g, prov = hp.law_gap(vp, vert_sets[1], tree1)
                d = float(np.linalg.norm(hp.rodrigues(c[None, :], piv, ax, th)[0] - c))
                pred = None
                if piv is hd["M"]:
                    cwv = c - piv
                    cpar = float(cwv @ ax)
                    cperp = math.sqrt(max(float(cwv @ cwv) - cpar * cpar, 0.0))
                    pred = 2.0 * cperp * math.sin(abs(th) / 2.0)
                rows.append({
                    "theta_rad": rnd(th), "label": lab,
                    "seat_gap_mm": rnd(g), "provenance": prov,
                    "seat_ok": bool(0.0 <= g <= CUT_MM),
                    "reading_class": "below_resolution_floor" if g < tol_ip_mm else "resolved",
                    "displacement_mm": rnd(d),
                    "band_mm": rnd(band_h),
                    "displacement_exact_zero": bool(d == 0.0),
                    "displacement_ok": bool(d <= band_h),
                    "predicted_displacement_mm": None if pred is None else rnd(pred),
                    "formula_abs_dev_mm": None if pred is None else rnd(abs(d - pred)),
                    "formula_ok": None if pred is None else bool(abs(d - pred) <= FORMULA_TOL),
                })
            seat_all = all(r["seat_ok"] for r in rows)
            disp_all = all(r["displacement_ok"] for r in rows)
            breaches = [r["label"] for r in rows if not (r["seat_ok"] and r["displacement_ok"])]
            out[k] = {
                "rows": rows,
                "seat_clause_ok_all_grid": seat_all,
                "displacement_clause_ok_all_grid": disp_all,
                "min_seat_mm": rnd(min(r["seat_gap_mm"] for r in rows)),
                "max_seat_mm": rnd(max(r["seat_gap_mm"] for r in rows)),
                "max_displacement_mm": rnd(max(r["displacement_mm"] for r in rows)),
                "below_floor_readings": [r["label"] for r in rows if r["reading_class"] == "below_resolution_floor"],
                "band_mm": rnd(band_h),
                "clause_breaches_at": breaches,
                "pass_p6_corrected": bool(seat_all and disp_all),
            }
        return out

    real = run_arm(lambda hd: hd["fit"]["c"], lambda: u)
    null = run_arm(lambda hd: hd["M"], lambda: u_ctrl)

    real_pass = all(real[k]["pass_p6_corrected"] for k in real)
    null_fail = all(not null[k]["pass_p6_corrected"] for k in null)
    discriminate = bool(real_pass and null_fail)

    # prediction checks vs the committed records (determinism cross-check)
    checks = {}
    for k in ("02", "03"):
        rmap = {r["label"]: r for r in real[k]["rows"]}
        nmap = {r["label"]: r for r in null[k]["rows"]}
        cseat = committed["real_arm"][k]["A2_seat"]
        creal = {"rest": cseat["rest"]["min_gap_mm"], "hi_endpoint": cseat["hi_endpoint"]["min_gap_mm"],
                 "lo_endpoint": cseat["lo_endpoint"]["min_gap_mm"]}
        checks["real_seats_reproduce_committed_%s" % k] = bool(
            all(rmap[lab]["seat_gap_mm"] == val for lab, val in creal.items()))
        cc = committed["control_arm"][k]
        cnul = {"rest": cc["rest"]["min_gap_mm"], "hi_endpoint": cc["hi_endpoint"]["min_gap_mm"],
                "lo_endpoint": cc["lo_endpoint"]["min_gap_mm"]}
        checks["null_seats_reproduce_committed_%s" % k] = bool(
            all(nmap[lab]["seat_gap_mm"] == val for lab, val in cnul.items()))
        checks["null_disp_reproduces_committed_%s" % k] = bool(
            nmap["hi_endpoint"]["displacement_mm"] == cc["hi_endpoint"]["center_displacement_mm"]
            and nmap["lo_endpoint"]["displacement_mm"] == cc["lo_endpoint"]["center_displacement_mm"])
        demo_lab = "grid_k%+d" % signs[k]
        checks["real_demo_seat_reproduces_committed_%s" % k] = bool(
            rmap[demo_lab]["seat_gap_mm"] == committed["pose_record"][k]["demo_pose"]["min_gap_mm"])
    checks["real_disp_exact_zero_all_grid"] = bool(all(
        r["displacement_exact_zero"] for k in real for r in real[k]["rows"]))
    checks["null_formula_ok_all_grid"] = bool(all(
        r["formula_ok"] for k in null for r in null[k]["rows"]))
    checks["null_disp_beyond_band_both_hips"] = bool(all(
        not null[k]["displacement_clause_ok_all_grid"] for k in null))
    checks["real_seats_below_cut_all_grid"] = bool(all(
        real[k]["seat_clause_ok_all_grid"] for k in real))
    checks["null_seats_below_cut_all_grid_recorded"] = bool(all(
        null[k]["seat_clause_ok_all_grid"] for k in null))

    # margins
    margins = {}
    for k in ("02", "03"):
        nh = [r for r in null[k]["rows"] if r["label"] in ("hi_endpoint", "lo_endpoint")]
        margins["null_disp_over_band_%s" % k] = rnd(
            max(r["displacement_mm"] for r in nh) / band[k])
        margins["real_min_seat_over_tol_%s" % k] = rnd(real[k]["min_seat_mm"] / tol_ip_mm)
        lo = [r for r in null[k]["rows"] if r["label"] == "hi_endpoint"][0]
        margins["null_hip%s_hi_seat_over_tol" % k] = rnd(lo["seat_gap_mm"] / tol_ip_mm)

    battery = {
        "schema": "chimera.p6_contrast_battery.v2",
        "lane": "agent/p6-repreregistration-20260921",
        "base_commit": "427e9d0 (agent/hip-pivot-proof-20260921, the proof head)",
        "parent_lane": "agent/hip-pivot-proof-20260921 (P6 as written: VOID in the record, fired 2026-09-21)",
        "parent_battery_sha256": committed_battery_sha,
        "parent_battery_sha_matches_receipt": bool(committed_battery_sha == PRIOB_BATTERY_SHA),
        "predicate_version": "v2 per preregistration_amendment_3.md: seat band [0, cut]; tol_ip = 0.08 mm retained as the RESOLUTION FLOOR (recorded, not clause-binding) after v1's hard lower edge was voided by its own falsifier L6 on run 1; displacement band (fit RMS) load-bearing",
        "run1_record": {
            "file": "battery_run1_predicate_v1_l6_fired.json",
            "sha256": run1_battery_sha,
            "l6_firing": "real hip 02 grid_k-3: seat gap 0.053906119839 mm < 0.08 at displacement 0.0 exactly",
            "run1_determinism": "battery byte-identical on immediate re-run (run1 sha c82947c22e85c75b2537175fd18a17842279b9d80e2f049f8b843be44788a77d)",
        },
        "banks": {
            "preregistration_sha256": lane_prereg_sha,
            "preregistration_bank_matches_file": bool(lane_prereg_sha == prereg_bank),
            "amendment_3_sha256": amendment3_sha,
            "amendment_3_bank_matches_file": bool(amendment3_sha == amendment3_bank),
            "law_doc_sha256_this_stage": law_b_sha,
            "law_amendment_b_bank_matches_file": bool(law_b_sha == law_b_bank),
            "law_amendment_stage1_bank_sha256": law_stage1_bank,
            "law_amendment_stage1_bank_expected": "e18d46ca29b8cfa0ba2cd81791d73dade52f2ba3c1733aa6d912004f2f533447",
            "law_amendment_stage1_bank_matches_run1_stage": bool(
                law_stage1_bank == "e18d46ca29b8cfa0ba2cd81791d73dade52f2ba3c1733aa6d912004f2f533447"),
        },
        "trailer": "Agent: GLM 5.3",
        "inputs": {
            "definition_sha256": before[str(DEFN.relative_to(ROOT))],
            "osim_sha256": osim_sha,
            "osim_sha_matches_citation": bool(osim_sha == OSIM_SHA),
            "vertex_books_match_membranes": bool(vertex_books_match),
        },
        "corrected_predicate": {
            "definition": "SEATED at theta iff (0 <= seat_gap <= cut) AND (displacement <= band_h); passes P6' iff both hold at every theta of the closed cited range. seat clause = amendment 3 Leg 1 [0, cut]; displacement clause = Leg 2, the load-bearing not-through test at the head",
            "tol_ip_mm": rnd(tol_ip_mm),
            "tol_ip_derivation": "specimen.resolution_um/2 = %d um / 2 = 0.08 mm: half the committed CT sampling step; the gap metric's RESOLUTION FLOOR — readings below it lie inside the surfaces' own localization (recorded per pose as below_resolution_floor, never clause-binding)" % resolution_um,
            "resolution_um": resolution_um,
            "cut_mm": CUT_MM,
            "cut_source": "bone_identification_v3 derived_cuts.joint_gap_mm (committed)",
            "band_source": "the registered fit's own RMS residual (the pivot's measured radius+residual ARE the socket's geometry)",
            "range_coverage": "grid {−R} ∪ {R·k/5, k = −4..4} ∪ {+R}; displacement covered on the whole range: real arm identity (d ≡ 0), null arm monotone 2|c_perp| sin(|θ|/2) (endpoints dominate)",
        },
        "bands": {
            "band_02_mm": rnd(band["02"]),
            "band_03_mm": rnd(band["03"]),
            "tol_ip_mm": rnd(tol_ip_mm),
            "cut_mm": CUT_MM,
        },
        "fits": {k: hip_defs[i]["fit"]["record"] for i, k in enumerate(("02", "03"))},
        "reproduction_guards": {
            "fits_equal_committed_battery_records": bool(repro_ok),
            "repro_diffs": {hd["key"]: hd["fit"]["repro_diffs"] for hd in hip_defs},
            "axis_u": [rnd(x) for x in u],
            "control_axis_u": [rnd(x) for x in u_ctrl],
            "axis_equal_committed": bool(
                [rnd(x) for x in u] == committed["axis"]["u"]
                and [rnd(x) for x in u_ctrl] == committed["axis"]["control_axis_null_unit"]),
        },
        "grid": {
            "definition": "endpoints exact; interior R*k/5.0 (the prior lane's registered probe fraction)",
            "thetas_rad": [rnd(t) for t, _ in thetas],
            "flexion_signs": signs,
        },
        "metric_transfer": transfer,
        "real_arm": real,
        "null_arm": null,
        "prediction_checks": checks,
        "margins": margins,
        "replica_integrity": {
            "script_byte_identical_to_committed": bool(replica_script_sha == committed_script_sha),
            "committed_script_sha256": committed_script_sha,
            "prereg_copy_equals_lane_prereg": bool(replica_prereg_sha == lane_prereg_sha),
            "expected_field_diff_vs_committed_battery": ["preregistration_sha256"],
        },
        "verdict": {
            "real_arm_passes_p6_corrected": bool(real_pass),
            "null_arm_fails_p6_corrected": bool(null_fail),
            "arms_discriminate": discriminate,
        },
        "untouched": {"before": before},
    }

    battery["untouched"]["after"] = {str(p.relative_to(ROOT)): sha256_file(p) for p in watch}
    battery["untouched"]["equal"] = bool(battery["untouched"]["before"] == battery["untouched"]["after"])

    hard_ok = (
        battery["parent_battery_sha_matches_receipt"]
        and battery["banks"]["preregistration_bank_matches_file"]
        and battery["banks"]["amendment_3_bank_matches_file"]
        and battery["banks"]["law_amendment_b_bank_matches_file"]
        and battery["banks"]["law_amendment_stage1_bank_matches_run1_stage"]
        and battery["inputs"]["osim_sha_matches_citation"]
        and battery["inputs"]["vertex_books_match_membranes"]
        and repro_ok
        and battery["reproduction_guards"]["axis_equal_committed"]
        and all(v["pass"] for v in transfer.values())
        and battery["untouched"]["equal"]
        and all(checks.values())
        and discriminate
    )
    battery["hard_checks_pass"] = bool(hard_ok)

    text = json.dumps(sanitize(battery), indent=1, sort_keys=True, ensure_ascii=True) + "\n"
    OUT.write_bytes(text.encode("utf-8"))
    print("battery written:", OUT)
    print("hard_checks_pass:", hard_ok)
    print("arms_discriminate:", discriminate, " real_pass:", real_pass, " null_fail:", null_fail)
    for k in ("02", "03"):
        print("hip %s real: seat all %s / disp all %s / seat %s..%s mm / below-floor at %s" % (
            k, real[k]["seat_clause_ok_all_grid"], real[k]["displacement_clause_ok_all_grid"],
            real[k]["min_seat_mm"], real[k]["max_seat_mm"], real[k]["below_floor_readings"]))
        print("hip %s null: seat all %s / disp all %s / max disp %s mm (band %s, x%.2f) breaches at %s" % (
            k, null[k]["seat_clause_ok_all_grid"], null[k]["displacement_clause_ok_all_grid"],
            null[k]["max_displacement_mm"], null[k]["band_mm"],
            margins["null_disp_over_band_%s" % k], null[k]["clause_breaches_at"]))
    return 0 if hard_ok else 1


if __name__ == "__main__":
    sys.exit(main())
