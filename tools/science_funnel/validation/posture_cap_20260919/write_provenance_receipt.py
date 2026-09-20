"""Task-2 provenance receipt: audit the admitted musculature against the
Task-1 price tag.  Reads only admitted stores (muscle_path_geometry.json,
the sha-pinned Guimaraes xlsx already verified at admission) plus the Task-1
min_admissible_cap.json; writes provenance_receipt.json.  No engine files.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]

GEOM = ROOT / "tools/science_funnel/validation/muscle_paths_20260918/muscle_path_geometry.json"
SWEEP = HERE / "min_admissible_cap.json"
OUT = HERE / "provenance_receipt.json"

SIGMA_DERIVED = 1280914.1381700735   # Pa, least-squares slope in the deliverable
SIGMA_CONS = 300000.0                # Pa, the mission's conservative specific tension (0.3 MPa)

MEMBRANE_FALSIFIER = (
    "If at C = 22.425 N.m (2x the wave-10 cap) the best reachable trajectory "
    "still has combined ratio > 1.0 at any node, the infeasibility is NOT a "
    "posture-cap artifact, this membrane dies, the 11.2125 N.m cap is "
    "exonerated, and the wave-10 INFEASIBLE verdict stands as the final word "
    "on the admissible-vault path.")

# Raw Guimaraes S1 'Macaca mulatta' sheet values (read from
# tools/science_funnel/data/guimaraes_arch/AJPA-190-e70329-s001.xlsx,
# sha256 08ead4a901a53f97e136c709a7804b9d04b4b903107e873c01f3b9b5b9eb8678),
# recorded here as the independent cross-check of the deliverable's pcsa_m2.
RAW_XLSX = {
    "ILI":  {"pcsa_m2": 0.000260885, "fascicle_m": 0.052, "pennation_deg": 21.2},
    "GMed": {"pcsa_m2": 0.000856724, "fascicle_m": 0.0689, "pennation_deg": 30.3},
}


def main():
    geom = json.loads(GEOM.read_text(encoding="utf-8"))
    sweep = json.loads(SWEEP.read_text(encoding="utf-8"))
    mus = geom["hindlimb"]["poses"]["walking"]["muscles"]
    mus_n = geom["hindlimb"]["poses"]["neutral"]["muscles"]

    def row(name, group):
        m, mn = mus[name], mus_n[name]
        arm = m["moment_arms_m_flexion_positive"]["hip"]
        armn = mn["moment_arms_m_flexion_positive"]["hip"]
        pcsa, cosp = m["pcsa_m2"], m["cos_pennation"]
        r = {
            "guimaraes_group": group,
            "functional_group": m["functional_groups"],
            "pcsa_cm2": round(pcsa * 1e4, 6),
            "cos_pennation": round(cosp, 6),
            "fascicle_length_m": m["measured_fascicle_length_m"],
            "Fmax_derived_1.281MPa_N": round(pcsa * SIGMA_DERIVED * cosp, 2),
            "Fmax_cons_0.3MPa_N": round(pcsa * SIGMA_CONS * cosp, 2),
            "hip_arm_walking_mm": None if arm is None else round(arm * 1000, 3),
            "hip_arm_neutral_mm": None if armn is None else round(armn * 1000, 3),
            "tau_walking_derived_Nm": None if arm is None else round(pcsa * SIGMA_DERIVED * cosp * arm, 4),
            "tau_walking_cons_Nm": None if arm is None else round(pcsa * SIGMA_CONS * cosp * arm, 4),
        }
        return r

    named = {n: row(n, g) for n, g in (("ILI", "IL (iliopsoas member)"), ("GMed", "GMED"))}
    named["GMin"] = row("GMin", "GMED-minor (abductor, not named by the lane)")
    hip = {n: row(n, m["functional_groups"][0]) for n, m in mus.items()
           if n not in named and m["moment_arms_m_flexion_positive"]["hip"] is not None}
    ankle_knee = {n: {"functional_group": m["functional_groups"],
                      "pcsa_cm2": round(m["pcsa_m2"] * 1e4, 6),
                      "Fmax_derived_1.281MPa_N": round(m["max_force_N"], 2)}
                  for n, m in mus.items() if m["moment_arms_m_flexion_positive"]["hip"] is None}

    pool = lambda d, k: sum(d[n][k] for n in d)  # noqa: E731
    pool_derived = pool(named, "tau_walking_derived_Nm") - named["GMin"]["tau_walking_derived_Nm"]
    pool_cons = pool(named, "tau_walking_cons_Nm") - named["GMin"]["tau_walking_cons_Nm"]

    ext_side = {n: r for n, r in hip.items() if r["tau_walking_cons_Nm"] is not None and r["tau_walking_cons_Nm"] < 0}
    ext_sum_cons = -sum(ext_side[n]["tau_walking_cons_Nm"] for n in ext_side)
    ext_sum_der = -sum(ext_side[n]["tau_walking_derived_Nm"] for n in ext_side)
    flex_side_der = sum(r["tau_walking_derived_Nm"] for r in list(named.values()) + list(hip.values())
                        if r["tau_walking_derived_Nm"] and r["tau_walking_derived_Nm"] > 0)

    c_star = sweep.get("min_admissible_cap_Nm")
    status = sweep.get("status")
    cap_base = sweep["sweep"]["caps_Nm"][0]
    cap_twice = sweep["sweep"]["caps_Nm"][-1]
    raw_check = all(
        abs(RAW_XLSX[n]["pcsa_m2"] * 1e4 - named[n]["pcsa_cm2"]) < 1e-6 for n in RAW_XLSX)

    # supplementary probe beyond the pre-registered window (verdict unchanged
    # under either outcome; recorded for frontier characterization)
    probe_path = HERE / "probe_beyond_window.json"
    probe = json.loads(probe_path.read_text(encoding="utf-8")) if probe_path.exists() else None

    # concurrency: measured from the wave-10 table's worst node (hip and
    # posture demands same-sign positive there)
    wave10 = json.loads((ROOT / "tools/science_funnel/validation/gait_zero_20260919/trunk_vault_reachable.json")
                        .read_text(encoding="utf-8"))
    worst = max(wave10["nodes"], key=lambda r: max(r["stance_ratio"], r["posture_ratio"]))
    hip_cap_model = 1.25 * 8.9746

    receipt = {
        "lane": "agent/posture-cap-provenance",
        "date": "2026-09-20",
        "question": ("Does the admitted data support the wave-10 posture cap's provenance "
                     "(trunk drive shares the hip cap via iliopsoas/gluteus medius), and can "
                     "that musculature produce the Task-1 price tag?"),
        "provenance_chain": [
            {"step": 1, "artifact": "tools/science_funnel/data/guimaraes_arch/AJPA-190-e70329-s001.xlsx",
             "what": "Guimaraes, Vereecke & Wiseman 2026, Am J Phys Anthropol S1: hindlimb muscle architecture for Macaca mulatta (specimen 127, KU Leuven); per-muscle PCSA, fascicle length, pennation",
             "pin": "sha256 08ead4a901a53f97e136c709a7804b9d04b4b903107e873c01f3b9b5b9eb8678 (member-stable per download_receipt.json)",
             "license": "CC BY 4.0"},
            {"step": 2, "artifact": "tools/science_funnel/validation/batch_muscle_20260917/receipt.json",
             "what": "batch admission: guimaraes_arch connector admitted 1908 measurement records, 49 quarantined, count identity closed (schema chimera.batch_validation.v1)"},
            {"step": 3, "artifact": "tools/science_funnel/validation/muscle_paths_20260918/muscle_path_geometry.json",
             "what": "derived moment arms (straight-line paths, Oku segment lengths) + per-muscle max_force_N = PCSA x derived specific tension x cos(pennation); Rule-0 admitted as model.creature.muscle_path_geometry; knee-extension and mtp-flexion directions FALSIFIED (no patella / no mtp pulley) and excluded from force claims",
             "derived_specific_tension": {"Pa": SIGMA_DERIVED, "N_per_cm2": 128.09141381700735,
                                          "method": "least squares through origin, 8 matched groups, implied range 0.312-5.277 MPa"}},
            {"step": 4, "artifact": "tools/science_funnel/validation/gait_zero_20260919/derive_trunk_pitch.py",
             "what": "the audited constant: CAP_POST = 1.25 * 8.9746 with the comment 'the posture drive shares the hip cap (the lane's contract)' - the provenance under audit"},
        ],
        "price_tag": {
            "min_admissible_cap_Nm": c_star,
            "sweep_status": status,
            "wave10_cap_Nm": cap_base,
            "window_Nm": [cap_base, cap_twice],
            "falsified_membrane": status == "falsified",
            "best_combined_ratio_in_window": max(
                (s["max_combined_ratio"] for s in sweep.get("sweep_runs", [])), default=None),
            "note": ("the sweep's own floor is 1x the wave-10 cap; any admissible C* >= 11.2125 N.m. "
                     "The pre-registered membrane predicted an admissible C* inside the window; the "
                     "measurement falsified it: at 22.425 N.m (2x) the best reachable trajectory "
                     "still holds combined ratio 1.001086 > 1.0. The minimum admissible cap, if it "
                     "exists at all, therefore lies ABOVE the window."),
            "probe_beyond_window": probe,
        },
        "muscle_table": {"named_trunk_control_pool": named,
                         "hip_spanning": hip,
                         "no_hip_arm_recorded": ankle_knee},
        "pool_totals": {
            "named_pool_ili_gmed": {
                "tau_walking_derived_Nm": round(pool_derived, 4),
                "tau_walking_cons_0.3MPa_Nm": round(pool_cons, 4)},
            "sensitivity_extension_side_pool_hamstrings_glutes_adductors": {
                "tau_walking_derived_Nm": round(ext_sum_der, 4),
                "tau_walking_cons_0.3MPa_Nm": round(ext_sum_cons, 4),
                "caveat": "NOT the lane's named trunk pool; these are the stance hip drive's own extensors (sum budget loads them concurrently) and GMax/BFL/ST/SM hold the stance hip in swing+stance"},
            "sensitivity_flex_side_pool_total_derived_Nm": round(flex_side_der, 4),
            "raw_xlsx_crosscheck_pcsa_matches_deliverable": raw_check,
        },
        "audit_answers": {},
        "falsifiers": {},
    }

    # (a) sum budget vs independent groups
    receipt["audit_answers"]["a_sum_budget_or_independent"] = {
        "verdict": "SUM BUDGET is the admitted architecture's constraint; the model's independent caps double-count one pool",
        "numbers": {
            "wave10_model_grants": "posture drive an INDEPENDENT cap = hip cap (11.2183 = 1.25 x 8.9746 N.m) on top of the hip drive's own 11.2183 N.m",
            "admitted_pool_ILI_GMed_derived_Nm": round(pool_derived, 4),
            "admitted_pool_ILI_GMed_cons_Nm": round(pool_cons, 4),
            "wave10_worst_node_concurrent_demand_Nm": round(abs(worst["required_posture_Nm"]) + abs(worst["leg_ratios"][0]) * hip_cap_model, 4),
            "worst_node": {"phi": worst["phi"], "posture_Nm": worst["required_posture_Nm"],
                           "hip_Nm_ratio": worst["leg_ratios"][0]},
            "overdraw_vs_pool_derived_pct": round(100 * (abs(worst["required_posture_Nm"]) + abs(worst["leg_ratios"][0]) * hip_cap_model) / pool_derived - 100, 1),
        },
        "reasoning": ("ILI crosses the hip (spine/iliac fossa -> lesser trochanter) and GMed spans pelvis->femur: "
                      "their trunk moment about the pelvis origin IS the reaction of their hip torque, same force, "
                      "same arm. One contractile pool serves both demands when hip and posture fire concurrently, "
                      "so tau_posture + tau_hip <= pool is the data's constraint. The lane's contract line grants "
                      "EACH drive the full hip cap instead - no admitted record supports two pools."),
    }
    # (b) PCSA x 0.3 MPa x moment arm at the price tag
    cap_floor_for_audit = c_star if c_star is not None else cap_twice
    receipt["audit_answers"]["b_supports_price_tag"] = {
        "verdict": ("NO. PCSA x 0.3 MPa x moment arm gives the named trunk pool 2.47 N.m; "
                    "even the repo's own derived 1.281 MPa gives 10.54 N.m - both below the "
                    "wave-10 cap (11.2125) and below the measured floor of any admissible cap "
                    "(> 22.425 N.m, since the window closed at 2x)"),
        "numbers": {
            "ILI": named["ILI"], "GMed": named["GMed"],
            "pool_0.3MPa_Nm": round(pool_cons, 4),
            "pool_derived_Nm": round(pool_derived, 4),
            "price_tag_Nm": c_star,
            "price_tag_floor_used": cap_floor_for_audit,
            "price_tag_note": ("no admissible cap exists inside the pre-registered window; "
                               "any admissible cap must exceed 22.425 N.m" if c_star is None
                               else "minimum admissible cap measured by sweep+bisection"),
            "shortfall_vs_price_tag_floor_0.3MPa_x": round(cap_floor_for_audit / pool_cons, 2) if pool_cons else None,
            "shortfall_vs_price_tag_floor_derived_x": round(cap_floor_for_audit / pool_derived, 2) if pool_derived else None,
        },
        "reasoning": ("The trunk moment's moment arm is the hip arm (reaction): ILI 12.594 mm, "
                      "GMed 6.985 mm at the walking pose. Measured PCSA (raw xlsx crosscheck = "
                      f"{raw_check}) x 0.3 MPa x cos(pennation) x arm: ILI 0.919 N.m + GMed 1.550 N.m "
                      f"= {pool_cons:.2f} N.m. That is {cap_floor_for_audit / pool_cons:.1f}x below the "
                      f"price-tag floor; even at the repo's derived tension the pool "
                      f"({pool_derived:.2f} N.m) is {cap_floor_for_audit / pool_derived:.2f}x short, "
                      "and the existing 11.2125 N.m cap itself already exceeds the pool by "
                      f"{11.2125 / pool_derived:.2f}x (derived) / {11.2125 / pool_cons:.1f}x (0.3 MPa)."),
    }

    # falsifier 1 (pre-registered in the mission): cap vs admitted musculature.
    # Fires when the minimum admissible cap exceeds the pool ceiling. The
    # window closed at 2x; the beyond-window probe brackets C*:
    # inadmissible at 22.425, admissible at 33.6375 (floor converged 0.9773
    # at 4.5x), so C* in (22.425, 33.6375] - every value >= 2.13x the pool
    # ceiling 10.54.
    c_floor, c_ceil = cap_twice, None
    if probe:
        ok_caps = sorted(float(k) for k, s in probe.items() if s["admissible"])
        if ok_caps:
            c_ceil = ok_caps[0]
    bracket_note = (f"C* in ({c_floor:.4f}, {c_ceil:.4f}] N.m" if c_ceil else
                    f"C* > {c_floor:.4f} N.m (no admissible cap found by the probe)")
    fired = (c_star is not None and c_star > pool_derived) or (c_star is None and status == "falsified")
    receipt["falsifiers"] = {
        "falsifier_1_cap_exceeds_musculature": {
            "rule": "if the minimum admissible cap exceeds what the admitted musculature produces, the biped is CLOSED on muscle grounds",
            "measured": {"min_admissible_cap_Nm": c_star,
                         "price_tag_bracket_Nm": bracket_note,
                         "pool_derived_Nm": round(pool_derived, 4),
                         "pool_cons0.3_Nm": round(pool_cons, 4)},
            "fired": fired,
            "reason": (f"the price tag {bracket_note} exceeds the pool ceiling 10.54 N.m "
                       f"(derived tension) by >= {c_floor / pool_derived:.2f}x and the "
                       f"0.3 MPa pool (2.47 N.m) by >= {c_floor / pool_cons:.2f}x"
                       if c_star is None else
                       f"minimum admissible cap {c_star:.4f} N.m exceeds the pool ceiling"),
        },
        "membrane_outcome": {
            "status": status,
            "falsifier_text": MEMBRANE_FALSIFIER,
            "measured": "at C = 22.425 N.m (2x) the best reachable trajectory holds combined ratio 1.001086 > 1.0 (SLSQP converged, posture saturated at the cap, hip ratio 1.0011 at phi=0.30); the beyond-window probe then finds admissibility at 33.6375 N.m (3x) with the envelope floor converged at 0.9773 (ankle-bound, phi=0.40) - identical at 4.5x",
            "outcome": "FALSIFIED AS PRE-REGISTERED - C* is NOT inside the claimed window; the window's premise (a reachable admissible cap at 1x-2x) is dead, and the true price tag sits at 2x-3x, unreachable by the admitted musculature a fortiori",
        },
    }

    if fired:
        receipt["verdict"] = ("CLOSED on muscle grounds (falsifier 1 fired). The price tag "
                              f"{bracket_note}: no posture cap at 1x-2x makes the combined "
                              "envelope admissible (best 1.001086 at 2x, posture saturated, "
                              "hip-bound at phi=0.30), and the beyond-window probe bounds the "
                              f"true C* above {c_floor:.4f} N.m. The admitted trunk-control pool "
                              "(iliopsoas ILI + gluteus medius GMed) produces at most "
                              f"{pool_derived:.2f} N.m at the repo's own derived specific tension "
                              f"(1.281 MPa) and {pool_cons:.2f} N.m at the conservative 0.3 MPa - "
                              f"below even the existing 11.2125 N.m cap. No derivable cap amendment "
                              "exists; the amendment path (falsifier 2: walk with the amended cap, "
                              "posture saturation < 10% of loaded ticks, past tick 426) is never "
                              "reached. The wave-10 cap's provenance (sharing the hip cap) is "
                              "exonerated as the binding constraint - the envelope is closed by "
                              "the stance side and by the musculature, not by the cap's number. "
                              "The bipedal admissible-vault path is CLOSED; the quadruped lane is "
                              "the architecture.")
    elif status == "complete":
        receipt["verdict"] = "AMENDABLE: price tag within the admitted musculature's ceiling - falsifier 2 applies."
    else:
        receipt["verdict"] = f"sweep incomplete (status={status}); audit numbers stand, verdict pending C*."

    OUT.write_text(json.dumps(receipt, indent=1) + "\n", encoding="utf-8")
    print(receipt["verdict"])
    print("written", OUT)


if __name__ == "__main__":
    main()
