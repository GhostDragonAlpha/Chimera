"""07 — consolidated GATE TABLE for the declared U-STR candidate (ulna + ulna_l x T1..T6).

Reads the per-test receipts (01..06) and emits the candidate gate table with the
measured numbers, plus the baseline integrity check. Verdict rule: PASS requires
T1 AND T2 AND T3 AND T4 AND T5 (AND T6 process) per side; any FAIL refuses the
candidate; the refusal must name the fired falsifier and the numbers.
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i7_common as IC  # noqa: E402

BODIES = IC.CANDIDATE_BODIES


def main() -> int:
    r01 = json.load(open(IC.RECEIPTS / "01_t1_provenance.json", encoding="utf-8"))
    r02 = json.load(open(IC.RECEIPTS / "02_t2_landmarks.json", encoding="utf-8"))
    r03 = json.load(open(IC.RECEIPTS / "03_t3_laterality.json", encoding="utf-8"))
    r04 = json.load(open(IC.RECEIPTS / "04_t4_transform.json", encoding="utf-8"))
    r05 = json.load(open(IC.RECEIPTS / "05_t5_uniqueness.json", encoding="utf-8"))
    r06 = json.load(open(IC.RECEIPTS / "06_t6_utility_ban.json", encoding="utf-8"))
    r00 = IC.load_candidate()

    table = {}
    for b in BODIES:
        t1_rows = [c for c in r01["checks"] if c["check"].endswith(b)]
        t1_ok = all(c["ok"] for c in t1_rows) and \
            next(c for c in r01["checks"] if "T1b" in c["check"])["ok"]
        t2 = next(c for c in r02["checks"] if c["check"] == f"T2 {b}")
        t3 = next(c for c in r03["checks"] if c["check"] == f"T3 {b}")
        t4 = next(c for c in r04["checks"] if c["check"] == f"T4 {b}")
        t5 = r05["edges"][b]
        table[b] = {
            "T1_source_provenance": {
                "verdict": "PASS" if t1_ok else "FAIL",
                "parent": t1_rows[0]["xml"],
                "site_set_equal": next(c for c in r01["checks"] if "T1b" in c["check"])["table"][b]["equal"],
                "resolutions": {"prox": t1_rows[1]["prox"], "dist": t1_rows[1]["dist"],
                                "roll": t1_rows[1]["roll"],
                                "roll_xml_owner": t1_rows[1]["roll_xml_owner"]},
            },
            "T2_landmark_sufficiency": {
                "verdict": "PASS" if t2["ok"] else "FAIL",
                "source_bone_len_m": t2["source_bone_len_m"],
                "target_pair_len_m": t2["target_pair_len_m"],
                "roll_t_norm_source_m": t2["roll_t_norm_source_m"],
                "roll_t_norm_target_m": t2["roll_t_norm_target_m"],
                "roll_eps": t2["roll_eps"],
                "scale_policy": t2["scale_policy"],
            },
            "T3_laterality": {
                "verdict": "PASS" if t3["ok"] else "FAIL",
                "source_side": t3["source_side"], "target_side": t3["target_side"],
                "target_prox_joint": t3["target_prox_joint"],
                "det_Q_constructed": t3["det_Q_constructed"],
                "handedness": t3["handedness"],
            },
            "T4_transform_explainability": {
                "verdict": "PASS" if t4["ok"] else "FAIL",
                "subchecks": t4["subchecks"],
                "s_implied": t4["rebuilt_scale"][0],
                "anchor_gap_m": t4["anchor_gap_m"],
                "c1_10_of_10": t4["subchecks"]["c1_independent_10_of_10_reproduced"],
                "worst_c1_delta_pts": max(p["delta_pts"] for p in t4["c1_placement"]),
                "plausibility": t4["plausibility"],
            },
            "T5_uniqueness": {
                "verdict": "PASS" if t5["ok"] else "FAIL",
                "resolution_supporters": t5["resolution_supporters"],
                "supporter_count": t5["supporter_count"],
                "declared_roll_xml_owner": t5["declared_roll_xml_owner"],
                "nearest_scale_alternative": t5["nearest_scale_alternative"],
                "in_band_others_context": t5["in_band_others_context"],
            },
        }
    table["_T6_utility_ban"] = {
        "verdict": "PASS" if r06["ok"] else "FAIL",
        "banned_evidence_occurrences": len(r06["clean_hits"]),
        "packet_tendon_readers": r06["packet_tendon_readers"],
    }
    table["_declaration"] = {
        "roll_choice": r00["roll_choice"]["declared_source_site"],
        "residual_deg": r00["roll_choice"]["residual_deg"],
        "law": r00["roll_choice"]["law"],
        "frozen_before_evaluation": r00["frozen_before_evaluation"],
    }

    git = subprocess.run(
        ["git", "-C", "E:/PythonChimera", "status", "--porcelain", "--",
         "forearm_package/baseline_snapshot"],
        capture_output=True, text=True, shell=False)
    baseline_out = git.stdout.strip()
    table["_baseline_integrity"] = {
        "command": "git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot",
        "output": baseline_out, "empty": baseline_out == "",
    }

    IC.save_receipt("07_gate_table.json", table)

    print("=" * 100)
    print("ISOLATED U-STR CANDIDATE GATE TABLE (ulna + ulna_l x T1..T6, protocol unchanged)")
    print("=" * 100)
    hdr = f"{'test':34s} {'ulna':>14s} {'ulna_l':>14s}  key numbers"
    print(hdr)
    rows = [
        ("T1 source-provenance", "T1_source_provenance",
         lambda d: f"parent={d['parent']}; sites==XML: {d['site_set_equal']}; "
                   f"roll owner={d['resolutions']['roll_xml_owner']}"),
        ("T2 landmark-sufficiency", "T2_landmark_sufficiency",
         lambda d: f"|src|={d['source_bone_len_m']:.6f} m |P_d-P|={d['target_pair_len_m']:.6f} m "
                   f"|t|={d['roll_t_norm_target_m']:.4f} m"),
        ("T3 laterality", "T3_laterality",
         lambda d: f"{d['source_side']}->{d['target_side']} ({d['target_prox_joint']}); "
                   f"detQ={d['det_Q_constructed']:.14f}"),
        ("T4 transform-explainability", "T4_transform_explainability",
         lambda d: f"s={d['s_implied']:.12f}; anchor_gap={d['anchor_gap_m']:.1e} m; "
                   f"C1 10/10={d['c1_10_of_10']} (worst {d['worst_c1_delta_pts']:.3f} pts)"),
        ("T5 uniqueness", "T5_uniqueness",
         lambda d: f"supporters={d['resolution_supporters']} (count={d['supporter_count']})"),
    ]
    all_pass = True
    for label, key, detail in rows:
        v_r = table["ulna"][key]["verdict"]
        v_l = table["ulna_l"][key]["verdict"]
        all_pass &= (v_r == "PASS" and v_l == "PASS")
        print(f"{label:34s} {v_r:>14s} {v_l:>14s}  {detail(table['ulna'][key])}")
    print(f"{'T6 utility-ban (process)':34s} {table['_T6_utility_ban']['verdict']:>31s}  "
          f"banned occurrences={table['_T6_utility_ban']['banned_evidence_occurrences']}")
    print(f"baseline snapshot git status: '{baseline_out}' (empty = untouched)")
    gate = "ALL PASS" if all_pass and table["_T6_utility_ban"]["verdict"] == "PASS" else "FAILURES PRESENT"
    print("CANDIDATE GATE:", gate)
    return 0 if (gate == "ALL PASS" and table["_baseline_integrity"]["empty"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
