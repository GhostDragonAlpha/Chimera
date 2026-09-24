"""09 — consolidated GATE VALIDATION TABLE (acceptance criterion 2).

Reads the per-test receipts (01..07) and emits the known-good validation table
(radius + radius_l x T1..T6) with the measured numbers, plus the baseline
integrity check.
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import b4_common as C  # noqa: E402


def main() -> int:
    r01 = json.load(open(C.RECEIPTS / "01_known_good_records.json", encoding="utf-8"))
    r02 = json.load(open(C.RECEIPTS / "02_t1_provenance.json", encoding="utf-8"))
    r03 = json.load(open(C.RECEIPTS / "03_t2_landmarks.json", encoding="utf-8"))
    r04 = json.load(open(C.RECEIPTS / "04_t3_laterality.json", encoding="utf-8"))
    r05 = json.load(open(C.RECEIPTS / "05_t4_transform.json", encoding="utf-8"))
    r06 = json.load(open(C.RECEIPTS / "06_t5_uniqueness.json", encoding="utf-8"))
    r07 = json.load(open(C.RECEIPTS / "07_t6_utility_ban.json", encoding="utf-8"))

    bodies = ("radius", "radius_l")
    table = {}
    for b in bodies:
        t1 = next(c for c in r02["checks"] if b in c["check"] or c["check"].startswith("T1b"))
        t1_rows = [c for c in r02["checks"] if c["check"].endswith(b)]
        t1_ok = all(c["ok"] for c in t1_rows) and \
            next(c for c in r02["checks"] if "T1b" in c["check"])["ok"]
        t2 = next(c for c in r03["checks"] if c["check"] == f"T2 {b}")
        t3 = next(c for c in r04["checks"] if c["check"] == f"T3 {b}")
        t4 = next(c for c in r05["checks"] if c["check"] == f"T4 {b}")
        edge = "radius" if b == "radius" else "radius_l"
        t5 = r06["edges"][edge]
        table[b] = {
            "T1_source_provenance": {
                "verdict": "PASS" if t1_ok else "FAIL",
                "parent": t1_rows[0]["xml"],
                "site_set_equal": next(c for c in r02["checks"] if "T1b" in c["check"])["table"][b]["equal"],
                "resolutions": {"prox": t1_rows[1]["prox"], "dist": t1_rows[1]["dist"],
                                "roll": t1_rows[1]["roll"],
                                "roll_xml_owner": t1_rows[1]["roll_xml_owner"]},
            },
            "T2_landmark_sufficiency": {
                "verdict": "PASS" if t2["ok"] else "FAIL",
                "source_bone_len_m": t2["source_bone_len_m"],
                "target_pair_len_m": t2["target_pair_len_m"],
                "roll_t_norm_m": t2["roll_t_norm_m"],
                "roll_eps": t2["roll_eps"],
                "scale_policy": t2["scale_policy"],
            },
            "T3_laterality": {
                "verdict": "PASS" if t3["ok"] else "FAIL",
                "source_side": t3["source_side"], "target_side": t3["target_side"],
                "target_prox_joint": t3["target_prox_joint"],
                "det_Q_constructed": t3["det_Q_constructed"],
                "handedness": t3["handedness"],
                "packet_chirality_det": t3["packet_chirality_det"],
            },
            "T4_transform_explainability": {
                "verdict": "PASS" if t4["ok"] else "FAIL",
                "max_abs_diff": t4["max_abs_diff"],
                "orthonormality_constructed": t4["orthonormality_constructed"],
                "det_Q": t4["det_Q"],
                "reconstruction_worst_m": t4["reconstruction_worst"]["err_m"],
                "reconstruction_sites": t4["reconstruction_worst"]["n_sites"],
                "s_implied": t4["rebuilt_scale"][0],
                "plausibility_neighbor": t4["plausibility"]["neighbor"],
                "plausibility_in_band": t4["plausibility"]["in_band"],
                "aspect_policy_ok": t4["plausibility"]["aspect_policy"],
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
        "verdict": "PASS" if r07["ok"] else "FAIL",
        "banned_evidence_occurrences": len(r07["clean_hits"]),
        "packet_tendon_readers": r07["packet_tendon_readers"],
    }
    table["_correspondence_digest"] = {
        "rebuilt": r01["digest_rebuilt"], "recorded": r01["digest_recorded"],
        "match": r01["digest_match"],
    }

    # baseline integrity
    git = subprocess.run(
        ["git", "-C", "E:/PythonChimera", "status", "--porcelain", "--",
         "forearm_package/baseline_snapshot"],
        capture_output=True, text=True, shell=False)
    baseline_out = git.stdout.strip()
    table["_baseline_integrity"] = {
        "command": "git -C E:/PythonChimera status --porcelain -- forearm_package/baseline_snapshot",
        "output": baseline_out, "empty": baseline_out == "",
    }

    C.save_receipt("09_validation_table.json", table)

    print("=" * 100)
    print("KNOWN-GOOD GATE VALIDATION TABLE (radius + radius_l x T1..T6)")
    print("=" * 100)
    hdr = f"{'test':34s} {'radius':>14s} {'radius_l':>14s}  key numbers"
    print(hdr)
    rows = [
        ("T1 source-provenance", "T1_source_provenance",
         lambda d: f"parent={d['parent']}; sites==XML: {d['site_set_equal']}; "
                   f"roll owner={d['resolutions']['roll_xml_owner']}"),
        ("T2 landmark-sufficiency", "T2_landmark_sufficiency",
         lambda d: f"|t_roll|={d['roll_t_norm_m']:.4f} m >> eps {d['roll_eps']:g}"),
        ("T3 laterality", "T3_laterality",
         lambda d: f"{d['source_side']}->{d['target_side']}; detQ={d['det_Q_constructed']:.14f}"),
        ("T4 transform-explainability", "T4_transform_explainability",
         lambda d: f"recon {d['reconstruction_worst_m']:.1e} m; s={d['s_implied']:.12f}; "
                   f"band {d['plausibility_in_band']}"),
        ("T5 uniqueness", "T5_uniqueness",
         lambda d: f"supporters={d['resolution_supporters']} (count={d['supporter_count']})"),
    ]
    all_pass = True
    for label, key, detail in rows:
        v_r = table["radius"][key]["verdict"]
        v_l = table["radius_l"][key]["verdict"]
        all_pass &= (v_r == "PASS" and v_l == "PASS")
        print(f"{label:34s} {v_r:>14s} {v_l:>14s}  {detail(table['radius'][key])}")
    print(f"{'T6 utility-ban (process)':34s} {table['_T6_utility_ban']['verdict']:>31s}  "
          f"banned occurrences={table['_T6_utility_ban']['banned_evidence_occurrences']}")
    print(f"correspondence digest match: {table['_correspondence_digest']['match']}")
    print(f"baseline snapshot git status: '{baseline_out}' (empty = untouched)")
    print("GATE VALIDATION:", "ALL PASS" if all_pass else "FAILURES PRESENT")
    return 0 if (all_pass and table["_T6_utility_ban"]["verdict"] == "PASS"
                 and table["_baseline_integrity"]["empty"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
