"""Hip-quarantine-review extended-book derivation (2026-09-20 lane).

Consumes the landed hip-arms book (sha-pinned) and the k-fill force set, re-derives the
class curves with the LANDED protocol (hip_arms_20260920.derive_hip_arms imported
UNMODIFIED, which imports the pulley machinery UNMODIFIED), scans the four quarantined
hip-relevant muscles (R_RF, R_SAR, R_AB, R_BFS) as NAMED READINGS (no force consumed by
any sum), and re-runs the hip-extension book + rear-up C* verdict with the EXTENDED set
defined by adjudication.json (admitted set: empty - the adjudication verdicts all
QUARANTINE_STANDS, so the extended class equals the landed class).

The counterfactual block (quarantined row sheet PCSAs x rear-up arms) is a NEVER-CONSUMED
robustness record: it bounds what any future lawful resolution could add, proving the
C* verdict's robustness without admitting anything.

Determinism: pure float64 numpy, fixed grids, sort_keys JSON, no clock input.
"""

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

LANE_DIR = Path(__file__).resolve().parent
REPO = LANE_DIR.parents[3]
OUT_JSON = LANE_DIR / "extended_hip_book.json"

sys.path.insert(0, str(REPO / "tools/science_funnel/validation/hip_arms_20260920"))
ha = __import__("derive_hip_arms")  # UNMODIFIED (F5); itself imports the pulley machinery
dp = ha.dp

K_FILL_BOOK = ha.K_FILL_BOOK
HIP_ARMS_BOOK = ha.OUT_JSON
DERIVED_NUMBERS = ha.DERIVED_NUMBERS
GUIM_AUDIT = REPO / "tools/science_funnel/validation/guimaraes_pairing_20260921/audit_table.json"
ADJUDICATION = LANE_DIR / "adjudication.json"

EXPECTED_SHA = {
    "model": (ha.MODEL_PATH, "d5c65cbc0a72bd2d5c2258c6bd018fe850ae25cce6fb07c1f268b91e598c88e9"),
    "k_fill_book": (K_FILL_BOOK, "252105017e5fd87728cea0ec77058c08c7244a66e2a78aeff7841296c57eb55c"),
    "hip_arms_book": (HIP_ARMS_BOOK, "02a47c7dcc32f02f5cf6f77bdbd1019bb2000052dc371b39734d7eeff221b2ae"),
    "derive_hip_arms": (Path(ha.__file__), "40bdfb4c1b42e762376a807426fd39498f7d802070ea6ee87b68155569f61b18"),
    "machinery": (Path(dp.__file__), "ce93c114c4e89d2726dc4c04b15416518e16208ffadfe14595f9cb14cde5cfa1"),
    "derived_numbers": (DERIVED_NUMBERS, "013810f87a6ca7c1e01916ef7a5454e61e8d0e88f8d6a589fbfdd1514017a173"),
    "guimaraes_audit": (GUIM_AUDIT, "843d1e70a5a881819360e05cef961eee89108ec86e6cb82ff2dbf475a0979d88"),
}

SIGMA_PA = 3.0e5  # 0.30 MPa - the one cited constant (k-fill D1; never swept)
QUARANTINED_SCANS = ["R_RF", "R_SAR", "R_AB", "R_BFS"]
CSTAR_TOP = 33.6
CSTAR_FLOOR = 22.4


def sha256_of(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_inputs():
    got = {}
    for key, (path, want) in EXPECTED_SHA.items():
        h = sha256_of(path)
        if h != want:
            raise SystemExit("REFUSED: input %s drifted (got %s want %s)" % (key, h, want))
        got[key] = h
    return got


def capability(qs, window, names, forces, curves):
    """The landed cap law, unchanged: cap = max over window of SUM F_m |r_m(q)| with the
    per-muscle per-q sign gate (negative arm about hip_flexion_r = extension)."""
    idx = np.arange(len(qs))[(qs >= window[0] - 1e-12) & (qs <= window[1] + 1e-12)]
    cap, arg = None, None
    per_q_signouts = {n: 0 for n in names}
    for k in idx:
        tau = 0.0
        for n in names:
            r = curves[n][int(k)]
            if r < 0.0:
                tau += forces[n] * (-r)
            else:
                per_q_signouts[n] += 1
        if cap is None or tau > cap:
            cap, arg = tau, int(k)
    per = []
    for n in names:
        r = curves[n][arg]
        c = forces[n] * (-r) if r < 0.0 else 0.0
        per.append({"muscle": n, "arm_mm_at_argmax": round(float(r) * 1e3, 6),
                    "force_N": forces[n], "contribution_N_m": round(float(c), 9),
                    "sign_gated_out": bool(c == 0.0)})
    return {"cap_N_m": round(float(cap), 9), "argmax_q_deg": round(math.degrees(float(qs[arg])), 4),
            "argmax_index": arg, "per_muscle_at_argmax": per,
            "sign_gated_out_sample_counts": per_q_signouts}


def main(argv):
    out_path = Path(argv[1]) if len(argv) > 1 else OUT_JSON
    shas = verify_inputs()
    kfill = json.loads(K_FILL_BOOK.read_text(encoding="utf-8"))
    landed = json.loads(HIP_ARMS_BOOK.read_text(encoding="utf-8"))
    derived_numbers = json.loads(DERIVED_NUMBERS.read_text(encoding="utf-8"))
    audit = json.loads(GUIM_AUDIT.read_text(encoding="utf-8"))
    adjudication = json.loads(ADJUDICATION.read_text(encoding="utf-8"))

    admitted_rows = {n: v for n, v in adjudication["muscles"].items()
                     if v["verdict"] == "RESOLVED_BY_SECOND_SOURCE"}
    admitted_set = adjudication["admitted_set"]
    assert set(admitted_rows) == set(admitted_set), \
        "adjudication admitted_set disagrees with its own per-muscle verdicts"

    # forces: class byte-equal to the k-fill set (asserted); admitted rows derive under
    # the one cited sigma and the declared pennation law
    forces, curve_names = {}, list(ha.CLASS)
    for name in ha.CLASS:
        entry = kfill["derived_force_set"]["muscles"][name]
        if entry["force_N"] is None or entry["status"] != "paired_exact_admitted":
            raise SystemExit("REFUSED: class force %s is not paired_exact_admitted" % name)
        forces[name] = float(entry["force_N"])
    for name in admitted_set:
        row = adjudication["muscles"][name]
        forces[name] = float(row["admitted_force_N"])
        curve_names.append(name)

    model = dp.parse_model()
    qs = np.linspace(ha.HIP_RANGE_RAD[0], ha.HIP_RANGE_RAD[1], ha.N_SCAN)

    # windows off the pinned snapshot (never hardcoded)
    hip_ok = derived_numbers["oku_before_alteration"]["angles"]["hip"]
    win_walk = (float(hip_ok["min_rad"]), float(hip_ok["max_rad"]))
    win_rear = (ha.HIP_RANGE_RAD[0], ha.REARUP_HI_RAD)
    mid_stance_rad = float(derived_numbers["oku_before_alteration"]["node_table_rad"]["hip"][5])

    # re-derive the class curves with the landed protocol; assert byte equality against
    # the landed book's stored samples (cross-lane determinism check)
    curves = {}
    class_crosscheck = {}
    for name in ha.CLASS:
        arms, valid, stop = ha.scan_muscle(model, name, qs)
        stored = np.array(landed["directions"][name]["arm_samples_m"], dtype=float)
        curves[name] = arms
        class_crosscheck[name] = {
            "byte_equal_to_landed_samples": bool(np.array_equal(arms, stored)),
            "valid_samples": valid, "scan_stop": stop,
        }
    for name in admitted_set:
        arms, valid, stop = ha.scan_muscle(model, name, qs)
        curves[name] = arms

    # extended books (cap law unchanged)
    ext_walk = capability(qs, win_walk, curve_names, forces, curves)
    ext_rear = capability(qs, win_rear, curve_names, forces, curves)
    mid_idx = int(np.argmin(np.abs(qs - mid_stance_rad)))
    mid_parts = {}
    for n in curve_names:
        r = curves[n][mid_idx]
        if r < 0.0:
            mid_parts[n] = forces[n] * (-r)
    mid_sum = round(sum(mid_parts.values()), 9)

    # landed comparison (F2: no constant moved)
    landed_rear = landed["hip_book_derived"]["rearup_window"]
    landed_walk = landed["hip_book_derived"]["walk_window"]
    landed_mid = landed["hip_book_derived"]["mid_stance_x050"]["sum_N_m"]
    extended_equal_landed = bool(
        curve_names == list(ha.CLASS)
        and ext_rear["cap_N_m"] == landed_rear["cap_N_m"]
        and ext_walk["cap_N_m"] == landed_walk["cap_N_m"]
        and mid_sum == landed_mid
    )

    # quarantined named readings (scans, no force consumed by any sum)
    readings = {}
    audit_rows = {}
    for r in audit["rows"]:
        if r["field"] == "raw_pcsa_m2":
            audit_rows.setdefault(r["guimaraes"], {})["pcsa_m2"] = r["value"]
        elif r["field"] == "raw_penn_deg":
            audit_rows.setdefault(r["guimaraes"], {})["penn_deg"] = r["value"]
    for name in QUARANTINED_SCANS:
        arms, valid, stop = ha.scan_muscle(model, name, qs)
        finite = arms[~np.isnan(arms)]
        rear_idx = np.where((qs >= win_rear[0] - 1e-12) & (qs <= win_rear[1] + 1e-12))[0]
        rear_arms = arms[rear_idx]
        rear_valid = rear_arms[~np.isnan(rear_arms)]
        neg_rear = rear_valid[rear_valid < 0.0]
        # material = |r| above the zero-noise floor: a thigh->shank muscle's hip arm is
        # EXACTLY zero up to float cancellation (~1e-13 m), so its raw sign is noise;
        # a material extensor channel needs |r| > 1e-6 m (0.001 mm)
        neg_material = neg_rear[np.abs(neg_rear) > 1e-6]
        art_idx = np.where(~np.isnan(arms) & (np.abs(arms) > ha.ARTIFACT_THRESHOLD_M))[0]
        gkey = name[2:]  # R_RF -> RF
        row = audit_rows.get(gkey, {})
        pcsa = row.get("pcsa_m2")
        penn = row.get("penn_deg")
        cf_force = None if pcsa is None else SIGMA_PA * pcsa * (
            math.cos(math.radians(penn)) if penn is not None else 1.0)
        cf_add = None if (cf_force is None or len(neg_rear) == 0) else \
            float(cf_force * (-neg_rear.min()))
        readings[name] = {
            "status": "QUARANTINED_NAMED_READING_no_force_consumed",
            "verdict": adjudication["muscles"][name]["verdict"],
            "valid_samples": valid,
            "scan_stop": stop,
            "arm_range_m_all_valid": [float(finite.min()), float(finite.max())],
            "max_abs_arm_m_all_valid": float(np.abs(finite).max()),
            "negative_extensor_samples_in_rearup_window": int(len(neg_rear)),
            "material_negative_samples_rearup_abs_gt_1e-6_m": int(len(neg_material)),
            "most_negative_arm_m_rearup": float(neg_rear.min()) if len(neg_rear) else None,
            "p2_material_extensor_channel": bool(len(neg_material) > 0),
            "p2_note": "a material extensor channel means real NEGATIVE-arm samples "
                       "(|r| > 1e-6 m) in the rear-up window; counts below the 1e-6 m "
                       "floor on an exactly-zero arm (R_BFS) are float-sign noise, not "
                       "anatomy",
            "artifact_flag_count": int(len(art_idx)),
            "artifact_samples": [{"index": int(i), "q_deg": round(math.degrees(float(qs[int(i)])), 4),
                                  "arm_m": float(arms[int(i)])} for i in art_idx],
        }
        if name == "R_BFS":
            readings[name]["hip_arm_zero_check"] = {
                "expected": "identically zero (thigh_r->shank_r spans no pelvis point; rigid"
                            " under hip_flexion_r)",
                "max_abs_arm_m": float(np.abs(finite).max()),
                "zero_within_1e-6_m": bool(np.abs(finite).max() < 1e-6),
            }
        if cf_force is not None:
            readings[name]["counterfactual_bound_NEVER_CONSUMED"] = {
                "basis": "the quarantined row's own sheet PCSA x the cited sigma x the "
                         "declared pennation factor - the defect numbers themselves; a "
                         "bound on any future lawful resolution, consumed by no sum",
                "pcsa_m2": pcsa, "penn_deg": penn,
                "counterfactual_force_N": float(cf_force),
                "counterfactual_max_rearup_add_N_m": cf_add,
            }

    cf_total = landed_rear["cap_N_m"] + sum(
        r["counterfactual_bound_NEVER_CONSUMED"]["counterfactual_max_rearup_add_N_m"] or 0.0
        for r in readings.values())

    prior = kfill["rearup_verdict"]
    primary_cap = ext_rear["cap_N_m"]
    book = {
        "schema": "chimera.hip_quarantine_review.v1",
        "lane": "hip-quarantine-review-20260920",
        "inputs": {"sha256": shas,
                   "adjudication": "adjudication.json (in-lane)",
                   "machinery": "hip_arms_20260920/derive_hip_arms.py imported UNMODIFIED "
                                "(which imports pulley_rederivation_20260920 UNMODIFIED)"},
        "adjudication_summary": {
            "admitted_set": admitted_set,
            "per_muscle": {n: {"verdict": v["verdict"], "defects": v["defects"]}
                           for n, v in adjudication["muscles"].items()},
            "homolog_route": adjudication["law"]["homolog_route"],
        },
        "class_crosscheck_vs_landed_book": class_crosscheck,
        "extended_book": {
            "class": curve_names,
            "forces_N": {n: forces[n] for n in curve_names},
            "walk_window": ext_walk,
            "rearup_window": ext_rear,
            "mid_stance_x050": {"q_used_rad": mid_stance_rad,
                                "grid_index": mid_idx,
                                "q_used_deg": round(math.degrees(float(qs[mid_idx])), 4),
                                "per_muscle_N_m": {n: round(v, 9) for n, v in mid_parts.items()},
                                "sum_N_m": mid_sum},
        },
        "extended_vs_landed": {
            "extended_equal_landed": extended_equal_landed,
            "landed_rearup_cap_N_m": landed_rear["cap_N_m"],
            "landed_walk_cap_N_m": landed_walk["cap_N_m"],
            "landed_mid_stance_sum_N_m": landed_mid,
            "note": "admitted set empty by adjudication: the extended set IS the landed set;"
                    " constants moved: NONE (F2) - forces byte-equal, windows/cap law/C* fixed",
        },
        "quarantined_named_readings": readings,
        "counterfactual_bounds_NEVER_CONSUMED": {
            "landed_rearup_cap_N_m": landed_rear["cap_N_m"],
            "sum_of_counterfactual_max_adds_N_m": float(cf_total - landed_rear["cap_N_m"]),
            "counterfactual_total_N_m": float(cf_total),
            "cstar_floor_N_m": CSTAR_FLOOR,
            "cstar_top_N_m": CSTAR_TOP,
            "counterfactual_crosses_floor": bool(cf_total > CSTAR_FLOOR),
            "note": "even admitting EVERY quarantined row at its own conflicted sheet PCSA on"
                    " its most negative rear-up arm simultaneously, the C* window floor is/is"
                    " not crossed - the robustness bound of the verdict; no number here is"
                    " admitted or consumed",
        },
        "rearup_verdict": {
            "class": prior["class"],
            "covered_iff": prior["covered_iff"],
            "primary_max_capability_N_m": primary_cap,
            "primary_definition": "max over the extended hip book at the REAR-UP window "
                                  "(admitted set empty -> the landed derived book)",
            "covered": bool(primary_cap > CSTAR_TOP),
            "verdict": "COVERED" if primary_cap > CSTAR_TOP else "NOT COVERED",
            "verdict_vs_landed": "UNCHANGED" if primary_cap == landed_rear["cap_N_m"]
                                 else "CHANGED (recorded honestly)",
            "gap_to_floor_N_m": round(CSTAR_FLOOR - primary_cap, 9),
            "gap_multiple_to_floor": round(CSTAR_FLOOR / primary_cap, 6),
        },
    }
    out_path.write_text(json.dumps(book, indent=1, sort_keys=True), encoding="utf-8")
    print("wrote", out_path)
    print("sha256", sha256_of(out_path))
    print("class curves byte-equal to landed book:",
          all(v["byte_equal_to_landed_samples"] for v in class_crosscheck.values()))
    print("extended book equals landed book:", extended_equal_landed)
    for n, r in readings.items():
        print("%-6s valid %4d  stop %s  neg_rearup %d (material %d)  |r|max %.6f mm  cf_add %s"
              % (n, r["valid_samples"],
                 ("yes@" + str(r["scan_stop"]["q_deg"]) + "deg") if r["scan_stop"] else "no",
                 r["negative_extensor_samples_in_rearup_window"],
                 r["material_negative_samples_rearup_abs_gt_1e-6_m"],
                 r["max_abs_arm_m_all_valid"] * 1e3,
                 r.get("counterfactual_bound_NEVER_CONSUMED", {}).get("counterfactual_max_rearup_add_N_m")))
    print("counterfactual total %.6f N.m vs floor %.1f -> crosses_floor %s"
          % (cf_total, CSTAR_FLOOR, cf_total > CSTAR_FLOOR))
    print("REAR-UP VERDICT:", book["rearup_verdict"]["verdict"],
          "| cap %.6f N.m | gap_to_floor %.6f N.m (x%.4f)"
          % (primary_cap, CSTAR_FLOOR - primary_cap, CSTAR_FLOOR / primary_cap))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
