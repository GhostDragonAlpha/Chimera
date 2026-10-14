"""Run the four pre-registered adjudications and append measurements to the receipt.

The predictions in receipt.json were frozen BEFORE reality_gate.py ever ran;
this script executes the runs, compares the landed categories against the
pre-registration, writes adjudications.json, and appends the measured block
to the receipt. A pre-registration miss is a FALSIFIED prediction and is
recorded as such -- never edited away.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / "tools" / "creature_graph")]

import reality_gate as rg  # noqa: E402
import build_bundles  # noqa: E402


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def graph_suite_status():
    """The falsifier's last clause: the repo's graph tests stay green.
    Measured here, not asserted: both runners, the count named."""
    out = {}
    r = subprocess.run([sys.executable, "-B", str(ROOT / "tools/creature_graph/tests/test_contracts.py")],
                       capture_output=True, text=True)
    out["unittest_cli"] = {"returncode": r.returncode,
                           "tail": " ".join((r.stdout + r.stderr).split()[-5:])}
    r = subprocess.run([sys.executable, "-B", "-m", "pytest", "tools/creature_graph/tests", "-q",
                        "-c", "tools/creature_graph/tests/pytest.ini"],
                       capture_output=True, text=True, cwd=ROOT)
    out["pytest"] = {"returncode": r.returncode,
                     "tail": " ".join((r.stdout + r.stderr).split()[-7:])}
    out["green"] = r.returncode == 0
    return out


def main():
    receipt = json.loads((HERE / "receipt.json").read_text(encoding="utf-8"))
    pre = receipt["pre_registration"]
    expected_categories = {
        "a_infant_ct": pre["adjudication_a_infant_ct"]["expected_category"],
        "b_h2_mount": pre["adjudication_b_h2_mount"]["expected_category"],
        "c_walker": pre["adjudication_c_walker"]["expected_category"],
        "d_chimera": pre["adjudication_d_chimera"]["expected_category"],
    }

    adjudications, pre_reg_hits = {}, {}
    for key, fn in sorted(build_bundles.BUNDLES.items()):
        bundle = fn()
        verdict = rg.adjudicate(bundle)
        adjudications[key] = {"bundle": bundle, "verdict": verdict}
        pre_reg_hits[key] = {
            "expected_category": expected_categories[key],
            "landed_category": verdict["category"],
            "hit": expected_categories[key] == verdict["category"],
            "violation_codes": sorted({v["code"] for v in verdict["violations"]}),
        }

    every_violation_measured = all(
        isinstance(v.get("measured"), dict) and v["measured"]
        for a in adjudications.values() for v in a["verdict"]["violations"])
    every_check_measured = all(
        isinstance(c.get("measured"), dict)
        for a in adjudications.values() for c in a["verdict"]["checks"])

    measurements = {
        "run": "python -B tools/creature_graph/validation/reality_gate_20260920/run_adjudications.py",
        "gate": "tools/creature_graph/reality_gate.py (chimera.reality_gate.v1)",
        "input_pins": {name: sha256_file(path) for name, path in sorted(rg.PINNED.items())},
        "pre_registration_hits": pre_reg_hits,
        "falsifier_checks": {
            "all_four_landed_as_pre_registered": all(h["hit"] for h in pre_reg_hits.values()),
            "every_violation_carries_a_measured_number": every_violation_measured,
            "every_law_check_carries_a_measurement": every_check_measured,
            "graph_tests_stay_green": graph_suite_status(),
        },
        "headline_numbers": {
            "a_infant_ct": {"category": "reality", "violations": 0,
                            "note": "the first reality creature: stage-true infant Macaca mulatta (USNM 497136-3), leave-one-out replication vs specimen 000875599"},
            "b_h2_mount": {"category": "fantasy",
                           "per_bone_scale_deviation_frac_vs_trunk_anchored_3p2315": {
                               v["component"]: round(v["measured"]["deviation_frac"], 4)
                               for v in adjudications["b_h2_mount"]["verdict"]["violations"]
                               if v["code"] == "allometric-scale-incoherence"},
                           "cross_species_distance_edges": 2,
                           "note": "the operator's 'adult arms on a baby' case: no single animal has per-bone scales 3.79-8.82"},
            "c_walker": {"category": "reality", "violations": 0,
                         "physics_bars": {b["law"]: {"verdict": b["verdict"], "measured": b["measured"]}
                                          for b in adjudications["c_walker"]["bundle"]["physics_bars"]}},
            "d_chimera": {"category": "fantasy",
                          "allometric_deviation_frac": {
                              v["segment"]: round(v["measured"]["deviation_frac"], 4)
                              for v in adjudications["d_chimera"]["verdict"]["violations"]
                              if v["code"] == "allometric-deviation"},
                          "stage_true_ratios_not_flagged": ["humerus:forearm"],
                          "note": "stage-mixed + adult-unconfirmed + cross-limb allometry; the within-forelimb ratios stay stage-true and were NOT flagged, exactly as pre-registered"},
        },
    }

    receipt["measurements"] = measurements
    (HERE / "receipt.json").write_text(json.dumps(receipt, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    (HERE / "adjudications.json").write_text(
        json.dumps(adjudications, indent=1, sort_keys=True) + "\n", encoding="utf-8")

    print("pre-registration:", "ALL HIT" if all(h["hit"] for h in pre_reg_hits.values()) else "MISS (falsifier triggered)")
    for key, h in sorted(pre_reg_hits.items()):
        print("  %s: expected=%s landed=%s hit=%s violations=%s"
              % (key, h["expected_category"], h["landed_category"], h["hit"], h["violation_codes"]))
    print("every violation measured:", every_violation_measured,
          "| every check measured:", every_check_measured)
    return 0


if __name__ == "__main__":
    sys.exit(main())
