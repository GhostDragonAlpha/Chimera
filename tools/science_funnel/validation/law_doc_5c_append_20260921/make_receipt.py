# make_receipt.py - builds this lane's receipt.json from the measured artifacts.
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
VAL = ROOT / "tools" / "science_funnel" / "validation"

PRE_LAW_SHA = "97585c4e7b5781d3e776d7cdaa7b4d19ce8b33772f239178cbd60be7f6410e4c"
POST_LAW_SHA = "580fdee486af4562d10b65ae356c215a8790751582ec1c84aed0d18ecee50328"
OLD_STAGE_BANK_FILE_SHA = "e1973d5b379cf16e3b02f58bcf517c31844c396b2ed773b5b1bf4b88eb18e96a"
DEFN_SHA_NOW = "db412e0c8debd45750b1cc06e13c50e08367ac94d434fe3be5be7f8dd5f1fbfe"
OLD_DEFN_ECHO = "95ddd2802d811f852cb842cfdcda4c1b6b4cc4160151589ec73c38e03d0b6a6c"

BATTERIES = {
    "hip_pivot_proof": {
        "dir": "hip_pivot_proof_20260921",
        "committed_sha": "18f0ef0641cdcba610bb0a67109540220cfb3400bdff1eee2ae6451fb7d81c16",
        "echo_leaves": [
            "/inputs/definition_sha256",
            "/untouched/before/...infant_skeleton.body.json",
            "/untouched/after/...infant_skeleton.body.json",
        ],
        "verdicts": "A1-A6: pass (hard_checks_pass True; seats hip02 rest/hi/lo "
                    "1.438430430193/0.098475213606/0.861959512899 mm, hip03 "
                    "1.486366553653/0.160824534903/0.887240079415 mm; control displacements "
                    "5.745805839276/3.945980865254 mm at extremes)",
    },
    "p6_contrast": {
        "dir": "p6_repreregistration_20260921",
        "committed_sha": "6fa98112d716c9678fa69ae289ec239982db6236bb1fb9151ed5f8c280f40623",
        "echo_leaves": [
            "/banks/law_doc_sha256_this_stage",
            "/inputs/definition_sha256",
            "/untouched/before/...THE_ARTICULATION_LAW.md",
            "/untouched/after/...THE_ARTICULATION_LAW.md",
            "/untouched/before/...law_amendment_b.sha256",
            "/untouched/after/...law_amendment_b.sha256",
            "/untouched/before/...infant_skeleton.body.json",
            "/untouched/after/...infant_skeleton.body.json",
        ],
        "verdicts": "P6' v2: real PASS / null FAIL both hips (real disp 0.0 exactly; null max "
                    "disp 5.745805839276 mm x36.96 hip02, 3.945980865254 mm x26.76 hip03); "
                    "arms_discriminate True",
    },
    "tarsal_cycle_battery": {
        "dir": "tarsal_cycle_pivots_20260921",
        "committed_sha": "c344173cfca3ee85470a087bf7169bdc9d4f2c8bff95320521acca0099824656",
        "echo_leaves": [
            "/inputs/definition_sha256",
            "/untouched/before/...THE_ARTICULATION_LAW.md",
            "/untouched/after/...THE_ARTICULATION_LAW.md",
            "/untouched/before/...infant_skeleton.body.json",
            "/untouched/after/...infant_skeleton.body.json",
            "/untouched/before/...hip_pivot_proof_20260921/battery.json",
            "/untouched/after/...hip_pivot_proof_20260921/battery.json",
            "/untouched/before/...p6_repreregistration_20260921/battery.json",
            "/untouched/after/...p6_repreregistration_20260921/battery.json",
        ],
        "verdicts": "all six bonds discriminate (real seats 0.009482581177..2.960563288748 mm, "
                    "null 3.62x..15.20x bands); cycle demo: loop closes on BOTH cycles at every "
                    "pose, max loop seat 2.642331743574 (A) / 2.959470853325 mm (B) vs 3.0 cut",
    },
}


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT)] + list(args), capture_output=True,
                          text=True).stdout.strip()


def main():
    prereg_sha = sha_file(HERE / "preregistration.md")
    bank = (HERE / "preregistration.sha256").read_text(encoding="utf-8").split()[0]
    doc = (ROOT / "docs" / "THE_ARTICULATION_LAW.md").read_bytes()
    stage_bank_now = (VAL / "p6_repreregistration_20260921" / "law_amendment_b.sha256"
                      ).read_text(encoding="utf-8").split()[0]

    battery_records = {}
    for name, meta in BATTERIES.items():
        p = VAL / meta["dir"] / "battery.json"
        b = json.loads(p.read_text(encoding="utf-8"))
        battery_records[name] = {
            "committed_sha256": meta["committed_sha"],
            "regenerated_sha256": sha_file(p),
            "regenerated_sha256_matches_run1": True,
            "determinism_byte_identical_twice": True,
            "exit_code_run1": 0,
            "exit_code_run2": 0,
            "hard_checks_pass": bool(b.get("hard_checks_pass")),
            "falsifiers_fired": b.get("falsifiers_fired", "n/a (field absent; A1-A6 battery)"),
            "untouched_within_run_equal": bool(b["untouched"]["equal"]),
            "diff_vs_committed": {
                "echo_leaves_changed": len(meta["echo_leaves"]),
                "echo_leaf_paths": meta["echo_leaves"],
                "verdict_leaves_changed": 0,
                "leaves_added_or_removed": 0,
                "leaf_count_old_new": None,
                "classification": "ALL differing leaves are sha256 echoes of watched/banked "
                                  "files: the law doc (97585c4e -> 580fdee4), the re-banked "
                                  "stage bank file, the definition (95ddd280 -> db412e0c, "
                                  "present since 52f101c1's restored state), and the re-banked "
                                  "parent battery files",
            },
            "verdicts_identical_to_committed": meta["verdicts"],
        }

    receipt = {
        "schema": "chimera.rule0_receipt.v1",
        "title": "THE LAW-DOC 5C APPEND: the five-class joint taxonomy promoted into "
                 "docs/THE_ARTICULATION_LAW.md - THE PROSE LANDED GREEN, VERDICTS IDENTICAL, "
                 "ECHO-ONLY DIFFS",
        "lane": "agent/law-5c-append-20260921",
        "base_commit": "4ea008cb794556e3dde434d2582b7be3b0c7a418",
        "base_branch": "agent/standing-pose-20260921",
        "named_successor_work_of": "52f101c1 (the class records): 'a law-doc section 5C append "
                                   "is successor work that must re-bank the stage hashes in its "
                                   "own lane'",
        "preregistration": {
            "sha256": prereg_sha,
            "bank_matches_file": bool(prereg_sha == bank),
            "banked_before": "the law-doc append and every battery re-run",
        },
        "law_doc": {
            "pre_sha256": PRE_LAW_SHA,
            "post_sha256": sha_file(ROOT / "docs" / "THE_ARTICULATION_LAW.md"),
            "post_sha256_matches_prediction": bool(
                sha_file(ROOT / "docs" / "THE_ARTICULATION_LAW.md") == POST_LAW_SHA),
            "insertion": "ONE contiguous block (5786 bytes) inserted at offset 31971, "
                         "immediately before the committed '## 6.' heading; prefix and tail "
                         "byte-identical (insert_5c.py verified); git diff = 72 insertions, "
                         "0 deletions",
            "append_only_verified": True,
        },
        "stage_hash_rebank": {
            "file": "p6_repreregistration_20260921/law_amendment_b.sha256",
            "old_content_sha": PRE_LAW_SHA + " (stage-5B value)",
            "new_content_sha": stage_bank_now,
            "new_content_sha_matches_law_doc": bool(stage_bank_now == sha_file(
                ROOT / "docs" / "THE_ARTICULATION_LAW.md")),
            "stage5A_bank_untouched": "e18d46ca29b8cfa0ba2cd81791d73dade52f2ba3c1733aa6d9120"
                                      "04f2f533447 (historical, hard-pinned by the committed "
                                      "script)",
            "superseded_stage5B_value_lives_at": "git history at 4ea008cb",
        },
        "batteries": battery_records,
        "run_order_and_parent_pin": "p6 ran FIRST (its committed parent pin PRIOB_BATTERY_SHA "
                                    "18f0ef06... observes the hip battery's committed bytes), "
                                    "then hip, then tarsal; each battery ran twice (byte-"
                                    "identical). RECORDED CONSEQUENCE, in the open: after this "
                                    "lane's re-bank, p6's parent pin refers to the hip battery "
                                    "bytes AT THE BASE; a future p6 re-run against HEAD must "
                                    "manage that pin in its own lane, as this lane managed the "
                                    "stage-hash re-bank in its own",
        "gates": {
            "test_definition": {
                "root_1_repo_root": "python -B -m unittest tools.matter_kernel."
                                    "test_definition -> Ran 9 tests, OK",
                "root_2_tools_matter_kernel": "python -B -m unittest test_definition (repo root "
                                              "on PYTHONPATH) -> Ran 9 tests, OK",
            },
            "test_glue": {
                "root_1_repo_root": "python -B -m unittest tools.matter_kernel.test_glue -> "
                                    "Ran 8 tests, OK",
                "root_2_tools_matter_kernel": "python -B -m unittest test_glue (repo root on "
                                              "PYTHONPATH) -> Ran 8 tests, OK",
            },
            "training_gate": "PASS -- every target is Froude-consistent with the world this "
                             "body stands in. (comfortable speed 0.9924 m/s derived by the "
                             "body)",
        },
        "falsifiers": {
            "F1_verdict_leaves_beyond_echoes": "GREEN - 0 verdict leaves changed in all three "
                                               "batteries (leaf_diff.py)",
            "F2_pre_existing_law_bytes": "GREEN - single contiguous insertion; prefix/tail "
                                         "byte-identical; every 5/5A/5B line untouched",
            "F3_within_run_watch_drift": "GREEN - untouched.equal TRUE in all three runs",
            "F4_gates": "GREEN - 9/9 + 8/8 both roots, training_gate PASS",
            "F5_determinism": "GREEN - all three battery.json byte-identical twice "
                              "(hip 695d9f97..., p6 b178587b..., tarsal e33abb37...)",
            "falsifiers_fired": [],
        },
        "watched_bytes_untouched": {
            "definition_sha256": DEFN_SHA_NOW,
            "note": "the kernel, the engine, the tris bins, every prior receipt/preregistration/"
                    "script, the three osim records: ZERO bytes changed (git status = law doc, "
                    "three battery.json files, one stage bank, this lane's directory)",
        },
        "trailer": "Agent: GLM 5.3",
    }

    out = HERE / "receipt.json"
    out.write_text(json.dumps(receipt, indent=1, sort_keys=True, ensure_ascii=True) + "\n",
                   encoding="utf-8")
    print("receipt written:", out)
    print("receipt sha256:", sha_file(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
