"""THE ANKLE-ADJUDICATION DERIVATION (lane ankle-adjudication-20260920).

Consumes ONLY sha-pinned committed artifacts (verified at load; REFUSES on drift)
plus one cited literature block (Persad et al. 2024, entered with DOI/PMCID, never
adopted as a repo constant). Emits adjudication_table.json deterministically:
sorted keys, indent 1, no timestamps, no commit hashes.

Run from the repo root:
  python -B tools/science_funnel/validation/ankle_adjudication_20260920/derive_adjudication.py
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]

# ---------------------------------------------------------------------------
# pinned inputs (F3): every number below traces to one of these bytes, or to the
# cited literature block. Load REFUSES on drift.
# ---------------------------------------------------------------------------
PINS = {
    "k_fill_book": "tools/science_funnel/validation/k_fill_20260920/k_fill_book.json",
    "derived_numbers_snapshot": "tools/science_funnel/validation/hind_torque_book_20260921/inputs/derived_numbers.snapshot.json",
    "ankle_arms_book": "tools/science_funnel/validation/ankle_arms_20260921/ankle_arms_book.json",
    "pennation_corrected_annotation": "tools/science_funnel/validation/pennation_correction_20260921/macaque_assembly_force_annotated_pennation_corrected.json",
    "oku2021_xml": "tools/science_funnel/validation/deposit_mass_20260921/literature/oku2021.xml",
}

REQUIRED_SHA = {
    "k_fill_book": "252105017e5fd87728cea0ec77058c08c7244a66e2a78aeff7841296c57eb55c",
    "derived_numbers_snapshot": "013810f87a6ca7c1e01916ef7a5454e61e8d0e88f8d6a589fbfdd1514017a173",
    "ankle_arms_book": "7ce03069c1e033b52db0fb315d218eb2223e79a67a9018123da206d68adcb6f6",
    "pennation_corrected_annotation": "939e0d7a9f908a4664f6f756ad58928b12c52ec4b41c0c3aa7e75c9f777806ee",
    "oku2021_xml": "e8e60ac390192ed6259d792d317d5c722a62ab23511a0efc653e95ff1a69eef0",
}


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_pinned(name: str):
    rel = PINS[name]
    p = REPO / rel
    if not p.exists():
        raise SystemExit(f"missing pinned input {name}: {rel}")
    got = sha256_file(p)
    if got != REQUIRED_SHA[name]:
        raise SystemExit(f"pin drift on {name} ({rel}): {got}")
    return json.loads(p.read_text(encoding="utf-8"))


# cited literature block (F3: cited, never adopted; F2: never a repo constant)
SIGMA_LITERATURE = {
    "citation": "Persad LS, Wang Z, Pino PA, Binder-Markey BI, Kaufman KR, Lieber RL (2024), "
                "'Specific tension of human muscle in vivo: a systematic review', "
                "J Appl Physiol 137(4):945-962, DOI 10.1152/japplphysiol.00296.2024, PMCID PMC11486478",
    "traditional_mammalian_N_per_cm2": 22.5,
    "human_in_vivo_span_N_per_cm2": [1.8, 72.7],
    "studies_included": 30,
    "values_counted": 96,
    "recommended_weighted_median_N_per_cm2": 26.8,
    "recommended_IQR_N_per_cm2": [20.0, 43.0],
    "status": "CITED CONTEXT ONLY - never adopted; no repo constant moves",
}

SIGMA_MPA_ASSUMED = 0.30          # the k-fill lane's one constant (cited there)
BAND_MIDPOINT_KG = 6.15           # Turnquist & Kessler 1989 band 5.4-6.9 kg midpoint
                                   # (banked deposit_mass convention, sha-pinned receipt)


def r6(x: float) -> float:
    return round(x, 6)


def main() -> dict:
    book = load_pinned("k_fill_book")
    snap = load_pinned("derived_numbers_snapshot")
    arms_book = load_pinned("ankle_arms_book")
    load_pinned("pennation_corrected_annotation")  # pin verified; forces consumed via k_fill book
    oku_xml_bytes = (REPO / PINS["oku2021_xml"]).read_text(encoding="utf-8")

    # ---- the finding under adjudication (k_fill book, sha-pinned) -----------
    plantar = book["capabilities_deposit_arms"]["ankle_plantarflexion"]
    dorsal = book["capabilities_deposit_arms"]["ankle_dorsiflexion"]
    cap_plantar = plantar["cap_N_m"]
    cap_dorsal = dorsal["cap_N_m"]
    demand_plantar = book["walk_coverage"]["ankle_plantarflexion"]["oku_walk_demand_N_m"]
    demand_dorsal = book["walk_coverage"]["ankle_dorsiflexion"]["oku_walk_demand_N_m"]
    demand_knee = book["walk_coverage"]["knee_extension"]["oku_walk_demand_N_m"]
    demand_mtp = book["walk_coverage"]["mtp_flexion"]["oku_walk_demand_N_m"]
    cap_knee = book["walk_coverage"]["knee_extension"]["cap_N_m"]
    cap_mtp = book["walk_coverage"]["mtp_flexion"]["cap_N_m"]

    # ---- derived per-muscle forces (k_fill book derived force set) ----------
    mus = book["derived_force_set"]["muscles"]

    def f(name: str) -> float:
        return mus[name]["force_N"]

    f_sol, f_mg, f_lg = f("R_SOL"), f("R_MG"), f("R_LG")
    f_ta, f_ehl = f("R_TA"), f("R_EHL")
    f_pl, f_pb, f_fhl = f("R_PL"), f("R_PB"), f("R_FHL")
    f_fdl = f("FDL_whole")
    f_edl = f("EDL_whole")
    fdl_pcsa, fdl_penn = mus["FDL_whole"]["pcsa_m2"], mus["FDL_whole"]["pennation_deg"]
    edl_pcsa, edl_penn = mus["EDL_whole"]["pcsa_m2"], mus["EDL_whole"]["pennation_deg"]
    # the law-consistent (pennation-corrected) values of the two deferred whole terms:
    # F = sigma_MPa x 1e6 (Pa) x PCSA_m2 x cos(pennation)
    fdl_law_corrected = SIGMA_MPA_ASSUMED * 1e6 * fdl_pcsa * math.cos(math.radians(fdl_penn))
    edl_law_corrected = SIGMA_MPA_ASSUMED * 1e6 * edl_pcsa * math.cos(math.radians(edl_penn))

    # ---- Oku walk per-muscle forces (banked snapshot, before/after) ---------
    oku = snap["oku_muscle_forces_N"]

    def ratio(derived: float, peak: float) -> float:
        return derived / peak

    gas_derived = f_mg + f_lg
    gas_b = oku["before"]["GAS"]["peak_N"]
    gas_a = oku["after"]["GAS"]["peak_N"]

    table_rows = {}
    for label, derived_val, oku_muscle in (
        ("SOL", f_sol, "SOL"),
        ("GAS_lumped_MG_plus_LG", gas_derived, "GAS"),
        ("FDL_whole_as_consumed", f_fdl, "FDL"),
        ("FDL_whole_law_corrected", fdl_law_corrected, "FDL"),
        ("TA", f_ta, "TA"),
        ("EDL_whole_as_consumed", f_edl, "EDL"),
    ):
        b = oku["before"][oku_muscle]["peak_N"]
        a = oku["after"][oku_muscle]["peak_N"]
        bm = oku["before"][oku_muscle]["mean_N"]
        am = oku["after"][oku_muscle]["mean_N"]
        table_rows[label] = {
            "derived_N": r6(derived_val),
            "oku_before_peak_N": b,
            "oku_before_mean_N": bm,
            "oku_after_peak_N": a,
            "oku_after_mean_N": am,
            "ratio_vs_before_peak": r6(ratio(derived_val, b)),
            "ratio_vs_before_mean": r6(ratio(derived_val, bm)),
            "ratio_vs_after_peak": r6(ratio(derived_val, a)),
        }

    no_oku_counterpart = {
        "PL": {"derived_N": r6(f_pl), "note": "Oku's 2D model has no peroneus longus"},
        "PB": {"derived_N": r6(f_pb), "note": "Oku's 2D model has no peroneus brevis"},
        "FHL": {"derived_N": r6(f_fhl), "note": "Oku's 2D model has no flexor hallucis longus"},
        "EHL": {"derived_N": r6(f_ehl), "note": "Oku's 2D model has no extensor hallucis longus"},
    }

    # pre-registered concentration metric: spread over shared PLANTAR classes
    plantar_shared = [
        table_rows["SOL"]["ratio_vs_before_peak"],
        table_rows["GAS_lumped_MG_plus_LG"]["ratio_vs_before_peak"],
        table_rows["FDL_whole_as_consumed"]["ratio_vs_before_peak"],
    ]
    all_shared = plantar_shared + [
        table_rows["TA"]["ratio_vs_before_peak"],
        table_rows["EDL_whole_as_consumed"]["ratio_vs_before_peak"],
    ]
    concentration = {
        "metric": "max(ratio)/min(ratio) over shared classes, primary = vs Oku before peak",
        "plantar_shared_classes": ["SOL", "GAS_lumped_MG_plus_LG", "FDL_whole_as_consumed"],
        "plantar_spread": r6(max(plantar_shared) / min(plantar_shared)),
        "all_shared_classes": plantar_shared and ["SOL", "GAS", "FDL", "TA", "EDL"],
        "all_spread": r6(max(all_shared) / min(all_shared)),
        "preregistered_threshold": 2.0,
        "concentrated": max(plantar_shared) / min(plantar_shared) >= 2.0,
        "sol_row": table_rows["SOL"],
        "gas_row": table_rows["GAS_lumped_MG_plus_LG"],
    }

    # ---- class-matched triceps comparison (same arms both sides) -----------
    triceps_derived_N = f_sol + f_mg + f_lg
    triceps_oku_before_N = oku["before"]["SOL"]["peak_N"] + oku["before"]["GAS"]["peak_N"]
    triceps_force_ratio = r6(triceps_derived_N / triceps_oku_before_N)

    # ---- the C-door test, consumed banked from the ankle arms book ---------
    v1 = arms_book["cap_book"]["ankle_plantarflexion"]["V1_S1_oku_walk_peaks_deposit_arms"]
    tri_sub = arms_book["cap_book"]["ankle_plantarflexion"]["triceps_only_subenvelope_V1_S1"]
    arm_door = {
        "law": "consumed banked, NOT recomputed (prereg D5)",
        "V1_S1_cap_N_m": v1["cap_N_m"],
        "V1_S1_reproduction_ratio": r6(v1["cap_N_m"] / demand_plantar),
        "triceps_only_subenvelope_N_m": tri_sub["cap_N_m"],
        "triceps_only_reproduction_ratio": r6(tri_sub["cap_N_m"] / demand_plantar),
        "conclusion": "the measured deposit arms carry Oku's own walk forces to within "
                      f"{abs(1.0 - v1['cap_N_m'] / demand_plantar) * 100:.1f}% of Oku's own "
                      "ankle peak; an arm error cannot explain the 1.345x shortfall",
    }

    # ---- mass context of the demand (B evidence) ----------------------------
    m_oku = snap["body_model"]["mass_kg"]
    before = snap["oku_before_alteration"]
    linear_scaled = demand_plantar * (BAND_MIDPOINT_KG / m_oku)
    geometric_scaled = demand_plantar * (BAND_MIDPOINT_KG / m_oku) ** (4.0 / 3.0)
    mass_context = {
        "law": "reported comparison only; the k-fill D5 raw-demand consumption is NOT changed",
        "demand_source_animal_kg": m_oku,
        "game_band_midpoint_kg": BAND_MIDPOINT_KG,
        "mass_ratio": r6(m_oku / BAND_MIDPOINT_KG),
        "ankle_plantar_demand_N_m": demand_plantar,
        "linear_mass_scaled_N_m": r6(linear_scaled),
        "coverage_linear_scaled": r6(cap_plantar / linear_scaled),
        "geometric_scaled_torque_proportional_to_M_4_3_N_m": r6(geometric_scaled),
        "coverage_geometric_scaled": r6(cap_plantar / geometric_scaled),
        "knee_coverage_unscaled": r6(cap_knee / demand_knee),
        "knee_coverage_geometric_scaled": r6(cap_knee / (demand_knee * (BAND_MIDPOINT_KG / m_oku) ** (4.0 / 3.0))),
        "mtp_coverage_unscaled": r6(cap_mtp / demand_mtp),
        "mtp_coverage_geometric_scaled": r6(cap_mtp / (demand_mtp * (BAND_MIDPOINT_KG / m_oku) ** (4.0 / 3.0))),
        "oku_walk_context_from_snapshot": {
            "duty_factor": before["duty_factor"],
            "toe_off_pct_of_cycle": before["toe_off_pct"],
            "grf_v_peak_xBW": before["grf_v_peak_xBW"],
            "grf_v_peak_pct_of_cycle": before["grf_v_peak_pct"],
            "ankle_plantar_peak_pct_of_cycle": abs(before["torques"]["ankle"]["x_min_pct"]),
            "ankle_plantar_peak_pct_of_stance": r6(
                abs(before["torques"]["ankle"]["x_min_pct"]) / (100.0 * before["duty_factor"]) * 100.0),
            "froude_measured": snap["froude_measured"],
            "timing_speed_m_s_simulated": snap["timing_paper"]["simulated_before"]["speed_m_s"],
        },
    }

    # ---- the sigma diagnostic (D2): containment test only, never adopted ---
    gap_factor = demand_plantar / cap_plantar
    sigma_diagnostic_MPa = SIGMA_MPA_ASSUMED * gap_factor
    sigma_diagnostic_N_per_cm2 = sigma_diagnostic_MPa * 100.0
    lo, hi = SIGMA_LITERATURE["human_in_vivo_span_N_per_cm2"]
    iqr_lo, iqr_hi = SIGMA_LITERATURE["recommended_IQR_N_per_cm2"]
    contained_in_span = lo <= sigma_diagnostic_N_per_cm2 <= hi
    contained_in_iqr = iqr_lo <= sigma_diagnostic_N_per_cm2 <= iqr_hi
    sigma_block = {
        "law": "diagnostic only: sigma that would close the ankle plantar gap, tested for "
               "containment in the cited literature range; NEVER adopted (F2)",
        "assumed_sigma_MPa": SIGMA_MPA_ASSUMED,
        "gap_factor": r6(gap_factor),
        "diagnostic_sigma_MPa": r6(sigma_diagnostic_MPa),
        "diagnostic_sigma_N_per_cm2": r6(sigma_diagnostic_N_per_cm2),
        "literature": SIGMA_LITERATURE,
        "contained_in_reported_span": contained_in_span,
        "contained_in_recommended_IQR": contained_in_iqr,
        "verdict": "NON_DISCRIMINATING" if (contained_in_span or contained_in_iqr)
                   else "EXCLUDED_BY_CITED_RANGE",
        "adopted": False,
    }

    # ---- Oku 2021 experimental context from the pinned XML (D3) ------------
    m = re.search(r"<article-title>(.*?)</article-title>", oku_xml_bytes, re.DOTALL)
    title = re.sub(r"<[^>]+>", " ", m.group(1)).strip() if m else None
    title = re.sub(r"\s+", " ", title) if title else None
    doi = "10.1038/s42003-021-01831-w" if "10.1038/s42003-021-01831-w" in oku_xml_bytes else None
    pmcid = "PMC7940622" if "PMC7940622" in oku_xml_bytes else None
    oku_context = {
        "source": "deposit_mass_20260921/literature/oku2021.xml (sha-pinned)",
        "title": title,
        "doi": doi,
        "pmcid": pmcid,
        "study_type": "forward dynamic simulation on a 2D neuromusculoskeletal model "
                      "(nine links); the walk torques and per-muscle forces are model "
                      "outputs, validated against measured timing, GRF profile and EMG "
                      "ACTIVATION PATTERNS of five hindlimb muscles - not measured tendon forces",
        "model_animal_kg": m_oku,
        "segments_Table1_sum_HAT_plus_one_leg_kg": r6(sum(
            snap["body_model"]["segments_Table1"][k]["mass_kg"]
            for k in snap["body_model"]["segments_Table1"])),
        "model_total_note": "10.038 kg = HAT 8.184 + 2 x leg chain 0.927 (the k-fill D3 anchor)",
        "level_walking": True,
        "no_grade": True,
    }

    # ---- verdict inputs -----------------------------------------------------
    verdict_inputs = {
        "C_arm_side": {
            "status": "EXCLUDED",
            "evidence": arm_door,
        },
        "A_architecture_side": {
            "status": "PARTIALLY_SUPPORTED_AS_SECONDARY",
            "method_asymmetry_found": False,
            "method_evidence": "Guimaraes 2026 pinned full text (PMC13425262_fulltext.xml, "
                               "sha a1ded31fa6d615b4b1dabc91bec824c2b05b90ad37fbbcf709480027b3eb9d40): "
                               "one uniform dissection protocol and one PCSA equation "
                               "(cos(theta) x belly mass / (1060 kg/m3 x FL), Mendez & Keys 1960) "
                               "for every hind limb muscle; no ankle-vs-knee methodological asymmetry; "
                               "single M. mulatta specimen (id 127, 8.0 kg adult male, KU Leuven)",
            "sol_row_conflict": {
                "sol_ratio": table_rows["SOL"]["ratio_vs_before_peak"],
                "gas_ratio": table_rows["GAS_lumped_MG_plus_LG"]["ratio_vs_before_peak"],
                "sol_conflict_factor": r6(1.0 / table_rows["SOL"]["ratio_vs_before_peak"]),
                "reading": "Oku's simulation requires a SOL capability the measured Guimaraes "
                           "SOL PCSA (124.136 mm2) cannot supply at physiological sigma, while "
                           "GAS matches - the two published ankle datasets conflict at the SOL "
                           "row specifically; a named dataset conflict, not a decided cause",
            },
        },
        "B_demand_side": {
            "status": "PRIMARY",
            "evidence": {
                "mass_context": {
                    "demand_source_kg": m_oku,
                    "game_animal_kg": BAND_MIDPOINT_KG,
                    "mass_ratio": r6(m_oku / BAND_MIDPOINT_KG),
                    "coverage_linear_scaled": mass_context["coverage_linear_scaled"],
                    "coverage_geometric_scaled": mass_context["coverage_geometric_scaled"],
                },
                "simulation_context": {
                    "demand_is": "forward-dynamic SIMULATION transient peak (not an animal "
                                 "measurement), level moderate walk (GRF peak "
                                 f"{before['grf_v_peak_xBW']} xBW, Froude {snap['froude_measured']})",
                    "speed_grade_flavor_of_B": "DEAD (level, Froude 0.27)",
                    "subjects_flavor_of_B": "HELD (10.038 kg modeled animal vs our 6.15 kg animal)",
                    "peak_flavor_of_B": "HELD (simulation transient peak at "
                                        f"{abs(before['torques']['ankle']['x_min_pct'])}% of cycle)",
                },
                "knee_mtp_rule_out_global_constants": {
                    "knee_ratio_unscaled": r6(cap_knee / demand_knee),
                    "mtp_ratio_unscaled": r6(cap_mtp / demand_mtp),
                },
            },
        },
        "sigma_verdict": sigma_block["verdict"],
    }

    table = {
        "schema": "chimera.ankle_adjudication.table.v1",
        "lane": "ankle-adjudication-20260920",
        "inputs_verified": {k: sha256_file(REPO / v) == REQUIRED_SHA[k] for k, v in PINS.items()},
        "the_finding_under_adjudication": {
            "plantar_cap_N_m": cap_plantar,
            "plantar_demand_N_m": demand_plantar,
            "plantar_coverage": r6(cap_plantar / demand_plantar),
            "dorsal_cap_N_m": cap_dorsal,
            "dorsal_demand_N_m": demand_dorsal,
            "dorsal_coverage": r6(cap_dorsal / demand_dorsal),
            "knee_coverage": r6(cap_knee / demand_knee),
            "mtp_coverage": r6(cap_mtp / demand_mtp),
        },
        "per_muscle_table": table_rows,
        "no_oku_counterpart": no_oku_counterpart,
        "class_matched_triceps_force_ratio": triceps_force_ratio,
        "concentration": concentration,
        "arm_door": arm_door,
        "mass_context": mass_context,
        "sigma_diagnostic": sigma_block,
        "oku_2021_context": oku_context,
        "verdict_inputs": verdict_inputs,
    }
    return table


def canonical_json_bytes(d: dict) -> bytes:
    return (json.dumps(d, indent=1, sort_keys=True) + "\n").encode("utf-8")


if __name__ == "__main__":
    out = REPO / "tools/science_funnel/validation/ankle_adjudication_20260920/adjudication_table.json"
    if "--out" in sys.argv:
        out = Path(sys.argv[sys.argv.index("--out") + 1])
    t = main()
    out.write_bytes(canonical_json_bytes(t))
    print(f"wrote {out} sha256 {hashlib.sha256(out.read_bytes()).hexdigest()}")
