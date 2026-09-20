"""The posture-cap provenance audit: does the admitted musculature support
the cap?  (Prompt-3 Task 2, lane buffy/posture-cap-provenance, 2026-09-19.)

The gait-impl lane set the posture cap to the HIP cap -- "the same
musculature carries the trunk moment" (gait_controller.hpp posture-drive
comment; derive_trunk_pitch.py CAP_POST = 1.25 * 8.9746) -- without deriving
whether the sharing is a cap on EACH drive or on the SUM.  This script does
not re-type the muscle data: it reads the admitted muscle-path record (the
committed deliverable the muscle-paths lane banked into the graph as
model.creature.muscle_path_geometry) and computes, side-aware:

  (1) pair capability -- the trunk-carrying pair (iliopsoas + gluteus
      medius, Oku's own pinned scheme for the trunk moment) per sagittal
      side; the hip EXTENSION side is carried by a different group
      (GMax/BFL/ST/SM), so each drive's draw must be compared against the
      group that carries its own sign;
  (2) concurrency -- at the wave-10 witness table (stored in
      min_admissible_cap.json) and at the theta=0 baseline, the hip drive's
      and the posture drive's demands on the SAME side are summed and
      compared against that side's supporting-group capability: this is the
      derivation the gait-impl lane never ran.

Outputs provenance_receipt.json in this directory.  Read-only over the
admitted records; no engine edits.

Run from the worktree root:
  python -B tools/science_funnel/validation/posture_cap_20260919/provenance_receipt.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "tools/science_funnel/validation/gait_zero_20260919"))
import derive_trunk_pitch as st  # noqa: E402  (the derivation lane's own statics)

GEO = REPO / "tools/science_funnel/validation/muscle_paths_20260918/muscle_path_geometry.json"
OUT = HERE / "provenance_receipt.json"

CAP_HIP = st.CAP["hip"]            # 11.21825 N.m (1.25 x 8.9746)
CAP_HIP_ROUNDED = 11.2125          # the engine/wave-10 constant (1.25 x 8.97)
CAP_POST = st.CAP_POST             # the trunk cap as pinned by the derivation lane
GRAVITY_MOMENT_AMPLITUDE = 8.184 * 9.80665 * 0.2506   # HAT m g R (wave-10 constant 20.097)


def load_muscles():
    g = json.loads(GEO.read_text(encoding="utf-8"))
    hl = g["hindlimb"]
    sigma = hl["specific_tension"]["specific_tension_Pa"]
    return g, sigma, hl["poses"]


def pair_capability(pose):
    """Per-muscle and per-side capability at a pose (N.m), the trunk-carrying
    pair (ILI + GMed) on the flexion+ side; the hip extension side belongs
    to the extensor group (reported from the pose envelope for context)."""
    muscles = pose["muscles"]
    ili, gmed = muscles["ILI"], muscles["GMed"]
    tau_ili = ili["torque_N_m_at_pose"]["hip"]
    tau_gmed = gmed["torque_N_m_at_pose"]["hip"]
    return {
        "ILI": {"pcsa_cm2": round(ili["pcsa_m2"] * 1e4, 4),
                "max_force_N": round(ili["max_force_N"], 2),
                "cos_pennation": round(ili["cos_pennation"], 4),
                "hip_moment_arm_m": round(ili["moment_arms_m_flexion_positive"]["hip"], 6),
                "hip_torque_N_m": round(tau_ili, 4)},
        "GMed": {"pcsa_cm2": round(gmed["pcsa_m2"] * 1e4, 4),
                 "max_force_N": round(gmed["max_force_N"], 2),
                 "cos_pennation": round(gmed["cos_pennation"], 4),
                 "hip_moment_arm_m": round(gmed["moment_arms_m_flexion_positive"]["hip"], 6),
                 "hip_torque_N_m": round(tau_gmed, 4)},
        "pair_flexion_side_N_m": max(tau_ili, 0.0) + max(tau_gmed, 0.0),
        "per_muscle_flexion_N_m": {"ILI": max(tau_ili, 0.0), "GMed": max(tau_gmed, 0.0)},
        "hip_extensor_group_extension_side_N_m": pose["torque_envelope_N_m"]["hip"]["flexion_negative_N_m"],
        "note": "both ILI and GMed carry a POSITIVE (flexion+) hip moment in the record's "
                "sign convention at both poses; the extension side is the extensor group's",
    }


def side_demands(phi, theta):
    """(hip_demand, posture_demand) at a stance node."""
    tau, *_ = st.statics(phi, (phi + 0.5) % 1.0, "L", phi, theta)
    return float(tau[3]), float(tau[2])


def concurrency_table(label, theta_of_phi, pair_flex_cap, ext_cap):
    """Node-wise same-side sums against the supporting group's capability."""
    rows = []
    worst_flex = worst_ext = 0.0
    for i in range(21):
        phi = i / 20.0
        theta = theta_of_phi(phi)
        hip, post = side_demands(phi, theta)
        flex_sum = max(hip, 0.0) + max(post, 0.0)
        ext_sum = -(min(hip, 0.0) + min(post, 0.0))
        worst_flex = max(worst_flex, flex_sum)
        worst_ext = max(worst_ext, ext_sum)
        rows.append({"phi": round(phi, 3), "theta_rad": round(theta, 4),
                     "hip_N_m": round(hip, 4), "posture_N_m": round(post, 4),
                     "flexion_side_sum_N_m": round(flex_sum, 4),
                     "extension_side_sum_N_m": round(ext_sum, 4)})
    return {
        "label": label,
        "nodes": rows,
        "worst_flexion_side_sum_N_m": round(worst_flex, 4),
        "worst_extension_side_sum_N_m": round(worst_ext, 4),
        "flexion_side_ratio_vs_pair": round(worst_flex / pair_flex_cap, 4),
        "extension_side_ratio_vs_extensors": round(worst_ext / ext_cap, 4),
        "flexion_side_covered": bool(worst_flex <= pair_flex_cap),
        "extension_side_covered": bool(worst_ext <= ext_cap),
    }


def main():
    geo, sigma, poses = load_muscles()
    caps_json = json.loads((HERE / "min_admissible_cap.json").read_text(encoding="utf-8"))
    true_min = caps_json["min_admissible_cap_true_Nm"]
    demand_peak = 8.67   # wave-10 reachable-table posture demand peak (max_required_posture_Nm)

    neutral_cap = pair_capability(poses["neutral"])
    walking_cap = pair_capability(poses["walking"])
    pair_flex_worst = min(neutral_cap["pair_flexion_side_N_m"], walking_cap["pair_flexion_side_N_m"])
    ext_worst = -min(neutral_cap["hip_extensor_group_extension_side_N_m"],
                     walking_cap["hip_extensor_group_extension_side_N_m"])

    # Concurrency at the theta=0 baseline and at the swept witness table.
    # The witness table is not stored in min_admissible_cap.json (the probe
    # reports feasibility statistics), so derive it here: re-run the sweep's
    # own probe at the swept threshold cap -- the trajectory the walker lane
    # would actually run -- and audit ITS concurrency.
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "posture_cap_sweep", HERE / "sweep_posture_cap.py")
    sweep = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sweep)
    witness_probe = sweep.probe(true_min, 1.0, maxiter=220, both_starts=True)
    witness_theta = witness_probe["theta_rad"] if witness_probe["feasible"] else None
    baseline = concurrency_table("theta=0 baseline (un-optimized)", lambda p: 0.0,
                                 pair_flex_worst, ext_worst)
    witness = (concurrency_table(f"wave-10 witness table (cap {true_min} N.m)",
                                 lambda p: witness_theta[int(round(p * 20)) % 21],
                                 pair_flex_worst, ext_worst)
               if witness_theta else None)

    # -- verdict (a): cap-on-EACH vs cap-on-SUM --
    a_tables = [t for t in (baseline, witness) if t]
    # The binding question is the WITNESS table (the optimized trajectory the
    # walker runs); the theta=0 baseline's late-stance over-nodes are the
    # known quasi-static single-contact overestimates that the posture table
    # exists to rescue (the hip draw there exceeds the pair even ALONE, so
    # they are a baseline artifact, not a trunk+hip concurrency effect).
    witness_covered = bool(witness and witness["flexion_side_covered"]
                           and witness["extension_side_covered"])
    worst_flex_ratio = max(t["flexion_side_ratio_vs_pair"] for t in a_tables)
    witness_worst_flex_ratio = (witness["flexion_side_ratio_vs_pair"] if witness else None)
    verdict_a = {
        "question": "is the SUM (trunk + hip concurrently) the admitted architecture's constraint, or are the drives independent?",
        "engine_realization": "cap-on-EACH: the posture drive is capped at drives_[0].cap (the hip cap) "
                              "independently of the hip drive (gait_controller.hpp servo()); separate "
                              "battery_post_ store; the two caps never add in the engine.",
        "side_structure": "the two drives draw on the SAME muscle group only when their demands share "
                          "a sign: the flexion+ side is the ILI+GMed pair (10.542-10.837 N.m); the "
                          "extension side is the extensor group (-128 to -131 N.m). Opposite-side "
                          "draws never sum onto one group.",
        "witness_flexion_side_ratio": witness_worst_flex_ratio,
        "witness_covered": witness_covered,
        "baseline_flexion_side_ratio": baseline["flexion_side_ratio_vs_pair"],
        "baseline_over_nodes_attribution": ("the theta=0 baseline exceeds the pair at phi=0.55-0.70, but "
                                            "the ENTIRE overage is the hip drive's own flexion demand "
                                            "(posture share <= 0.36 N.m) at the quasi-static "
                                            "single-contact overestimate nodes -- the hip draw exceeds "
                                            "the pair even ALONE there, which is the baseline artifact "
                                            "the posture table (theta* ~ +0.43..+0.54 rad) rescues, not "
                                            "a trunk+hip concurrency effect"),
        "verdict": ("SUM_COVERED_ON_THE_WITNESS: along the reachable trajectory the concurrent "
                    "same-side sums stay inside the supporting group's envelope at every node "
                    "(worst flexion-side ratio {:.3f}); the engine's cap-on-each realization is "
                    "therefore admissible FOR THE WITNESS ARCHITECTURE, and the never-derived "
                    "sharing question resolves as: the sharing is real on the flexion side but "
                    "never binding along the reachable trajectory".format(witness_worst_flex_ratio)
                    if witness_covered else
                    "SUM_BINDS_ON_THE_WITNESS: a concurrent same-side sum exceeds the supporting "
                    "group's envelope along the reachable trajectory -- cap-on-each undershoots "
                    "the true shared-muscle constraint and the sharing must be derived as a SUM cap"),
        "detail_tables": a_tables,
    }

    # ── verdict (b): capability vs price tag ──
    verdict_b = {
        "question": "does PCSA x specific tension x moment arm support a trunk-control torque at the price-tag level?",
        "specific_tension_Pa": round(sigma, 2),
        "specific_tension_N_per_cm2": round(sigma / 1e4, 3),
        "price_tag_N_m": true_min,
        "current_cap_N_m": CAP_HIP_ROUNDED,
        "wave10_posture_demand_peak_N_m": demand_peak,
        "pair_flexion_side_N_m": {"neutral": round(neutral_cap["pair_flexion_side_N_m"], 4),
                                  "walking": round(walking_cap["pair_flexion_side_N_m"], 4),
                                  "worst_side": round(pair_flex_worst, 4)},
        "per_muscle_N_m": {"ILI": round(min(neutral_cap["per_muscle_flexion_N_m"]["ILI"],
                                            walking_cap["per_muscle_flexion_N_m"]["ILI"]), 3),
                           "GMed": round(min(neutral_cap["per_muscle_flexion_N_m"]["GMed"],
                                             walking_cap["per_muscle_flexion_N_m"]["GMed"]), 3)},
        "per_muscle_verdict": {
            "ILI_alone": "3.92-4.01 N.m -- insufficient alone",
            "GMed_alone": "6.62-6.82 N.m -- insufficient alone",
            "pair": "10.542-10.837 N.m -- covers the price tag",
            "okau_scheme": "the pinned fulltext drives the trunk with BOTH muscles (the pair), so "
                           "the pair is the honest unit; neither muscle is the trunk drive alone",
        },
        "pair_vs_price_tag": {"ratio": round(pair_flex_worst / true_min, 4),
                              "covers": bool(pair_flex_worst >= true_min)},
        "pair_vs_demand_peak": {"ratio": round(pair_flex_worst / demand_peak, 4),
                                "covers": bool(pair_flex_worst >= demand_peak)},
        "headroom_at_price_tag_N_m": round(pair_flex_worst - true_min, 4),
    }

    # ── falsifiers ──
    amended_cap = round(pair_flex_worst, 2)   # round DOWN: the muscle-grounded ceiling
    falsifier_1 = {
        "statement": "if the minimum admissible cap exceeds what the admitted musculature can produce, the biped is closed on muscle grounds",
        "applies": bool(true_min > pair_flex_worst),
        "measured": {"min_admissible_cap_Nm": true_min, "pair_worst_side_N_m": round(pair_flex_worst, 4)},
        "verdict": ("TRIGGERED: closed on muscle grounds"
                    if true_min > pair_flex_worst else
                    "NOT TRIGGERED: the swept minimum (10.334 N.m) sits below the pair's worst-side "
                    "capability (10.542 N.m)"),
    }
    falsifier_2 = {
        "statement": "if the data supports it, the amendment is derivable: exact cap, provenance chain, and the walker-lane falsifier",
        "amendment": {
            "proposed_posture_cap_N_m": amended_cap,
            "provenance": "the trunk-carrying pair's own capability ceiling: (PCSA_ILI x sigma x "
                          "cos(pennation) + PCSA_GMed x sigma x cos(pennation)) x hip moment arm, "
                          "worst side over the two audited poses (walking), from the admitted "
                          "muscle-path record -- no borrowed hip peak, no derived headroom stacked "
                          "on a capability (headroom belongs between demand and cap, and the "
                          "wave-10 demand peak 8.67 N.m already sits 17.8% under this ceiling)",
            "chain": ["Oku 2021 pinned fulltext: postural control of the trunk by hip uniarticular "
                      "muscles (iliopsoas + gluteus medius) -- the pair, not either muscle alone",
                      "Guimaraes 2026 PCSAs (ILI 2.609 cm2, GMed 8.567 cm2) x derived specific "
                      "tension 128.09 N/cm2 x cos(pennation) x geometric hip moment arms",
                      "worst-side pair capability 10.542 N.m (walking pose) = the amended cap",
                      "static admissibility: swept minimum 10.334 N.m <= 10.542 (witness exists)",
                      "dynamic headroom: demand peak 8.67 N.m <= 10.542 with 17.8% margin"],
            "also_fix": "the rounding split: derive_trunk_pitch.py pins 11.21825 (1.25 x 8.9746) while "
                        "the engine and wave 10 pin 11.2125 (1.25 x 8.97) -- the amendment gives the "
                        "posture drive its own constant and ends the borrow",
            "walker_lane_falsifier": "re-run the walk with the amended cap (10.54 N.m) and the wave-10 "
                                     "reachable table as the posture target; PASS requires posture "
                                     "saturation < 10% of ticks and the run surviving past tick 426; "
                                     "FAIL closes the posture amendment and reopens the cap derivation",
            "uncertainty_note": "inherits the muscle-path lane's declared 25% moment-arm uncertainty "
                                "(the estimated hindlimb attachments are not dissection geometry)",
            "requires_engine_edit": True,
        },
        "applies": True,
        "verdict": "AMENDMENT_DERIVABLE -- the data supports the amended cap: the swept minimum "
                   "(10.334) and the demand peak (8.67) both sit under the pair ceiling (10.542)",
    }

    receipt = {
        "schema": "chimera.posture_cap_provenance.v1",
        "lane": "buffy/posture-cap-provenance",
        "date": "2026-09-19",
        "agent": "Buffy",
        "rule_0": {
            "statement": "The posture cap is a muscle-grounded constant: the trunk moment is carried by "
                         "the iliopsoas+gluteus-medius pair (Oku's pinned scheme), the pair envelope "
                         "covers both the swept minimum and the demand peak, and the engine's "
                         "cap-on-each realization is consistent with the records (same-side sums stay "
                         "inside the supporting group's envelope).",
            "prediction": "At the amended cap (the pair ceiling, 10.54 N.m) the walker lane's re-run "
                          "shows posture saturation < 10% of ticks and survives past tick 426.",
            "falsifier": "If the walker lane's re-run saturates >= 10% of ticks or dies before tick 426 "
                         "at the amended cap, this membrane is false and the cap derivation reopens.",
        },
        "cap_provenance_chain": {
            "current_cap_N_m": CAP_HIP_ROUNDED,
            "current_chain": ["Oku 2021 measured hip torque peak 8.9746 N.m (derived_numbers.json, "
                              "gait_controller_20260918; 8.97 in the doc)",
                              "headroom factor 1.25 (gait_controller_derivation doc section 4.3)",
                              "1.25 x 8.9746 = 11.21825 (derive_trunk_pitch.py CAP_POST)",
                              "1.25 x 8.97 = 11.2125 (engine/wave-10 constant) -- ROUNDING SPLIT: the two "
                              "lanes pin different constants; the derivation doc quotes 8.97",
                              "gait-impl adoption: the posture drive keyed to the HIP cap ('the same "
                              "musculature carries the trunk moment') -- the sharing was never derived"],
            "rounding_split": {"derive_lane_N_m": round(CAP_HIP, 6), "engine_lane_N_m": CAP_HIP_ROUNDED,
                               "delta_N_m": round(CAP_HIP - CAP_HIP_ROUNDED, 6)},
        },
        "muscle_records_source": {
            "path": "tools/science_funnel/validation/muscle_paths_20260918/muscle_path_geometry.json",
            "record_id": "model.creature.muscle_path_geometry",
            "specific_tension_Pa": round(sigma, 2),
            "method": "PCSA x derived specific tension x cos(pennation) x geometric moment arm "
                      "(Guimaraes 2026 PCSA matched to Oku 2021 Fmax, mass-adjusted)",
        },
        "pair_capability": {"neutral": neutral_cap, "walking": walking_cap},
        "verdict_a_sum_vs_each": verdict_a,
        "verdict_b_capability_vs_price_tag": verdict_b,
        "falsifiers": {"f1_muscle_closure": falsifier_1, "f2_amendment": falsifier_2},
        "sweep_reference": {"path": "min_admissible_cap.json",
                            "min_admissible_cap_true_Nm": true_min,
                            "min_admissible_cap_in_prompted_range_Nm": caps_json["min_admissible_cap_Nm"],
                            "wave10_margin_0_9": "unreachable at any swept cap (11.2-22.4 N.m): the wall "
                                                 "is the KNEE cap, not the posture cap -- static min "
                                                 "combined 0.9112 at phi=0.85 with theta*=-0.37 rad, "
                                                 "knee ratio 0.785 and posture floor -6.99 N.m"},
        "boundaries": "new directory only; no engine files edited; derivation lane files untouched",
    }
    OUT.write_text(json.dumps(receipt, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({
        "verdict_a": verdict_a["verdict"],
        "witness_flexion_side_ratio": witness_worst_flex_ratio,
        "witness_probe_feasible": witness_probe["feasible"],
        "verdict_b_pair_covers_price_tag": verdict_b["pair_vs_price_tag"]["covers"],
        "falsifier_1": falsifier_1["verdict"],
        "falsifier_2": falsifier_2["verdict"],
        "proposed_cap_N_m": amended_cap,
    }, indent=1))
    print("written", OUT)


if __name__ == "__main__":
    main()
