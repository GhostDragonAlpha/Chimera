"""verify_pinned_seam.py -- MAT2-U01 reconciliation verifier (frozen probe).

Executes EXACTLY the frozen PREREGISTRATION.md probes, in order:
  1. FAILING-FIRST mutant run  -> PREDICTION P3: FAIL (exit 1, >=1 FAIL line)
  2. pinned falsifier run      -> PREDICTION P2: GREEN (exit 0, 0 FAIL lines)
  3. lineage hash assertion    -> PREDICTION P1: 7/7 pinned hashes match

CPU-only, stdlib only, python -B, no network, no engine, no wall clock in any
asserted path (timestamps recorded are metadata of the run, never asserted).
Writes evidence/verification_receipt.json from what it observed.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PINNED = HERE / "reconcile" / "pinned_seam"
MUTANT = HERE / "reconcile" / "mutant_seam"
EVIDENCE = HERE / "evidence"
TESTS_REL = Path("tools/monkey_campaign/product/input_mapper_tests.py")

# The accepted ONT-U01 qualification_receipt.json pinned_lineage.sources table
# (verbatim; the assertion target frozen in PREREGISTRATION.md).
PINNED_LINEAGE = {
    "tools/monkey_campaign/product/input_mapper.py":
        "7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44",
    "tools/science_funnel/typeb_export/command_record.py":
        "6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e",
    "tools/monkey_campaign/product/follow_camera.py":
        "d61347f085644e66a5f29ab1e689e2bbd2cd5ff04099856ade70e5da90a791a7",
    "tools/monkey_campaign/product/input_mapper_tests.py":
        "95f44e90998f9728802ff5f7cb8628f18f2026bef1fb2c4de681e5253381216e",
    "tools/monkey_campaign/agents/U01_input/PREREGISTRATION.md":
        "0aadc3cd5fec7e7bd0a7aba0bcfa2a5d05edf8fcb6805eda2ecae92d4d3d1b5f",
    "tools/monkey_campaign/agents/U01_input/discovery_note.md":
        "38efdf393bd03b7b1260896e917231f2968963a501a180f4fc01491a02b30849",
    "tools/monkey_campaign/agents/U01_input/receipts/input_mapper_tests_20260924.txt":
        "00c73e346298f3880c61f4f30c77f490565c6f630e61f9bf414839ae6f6fa84c",
}

# The single frozen mutant semantic: the command cadence bound itself.
MUTANT_TARGET = "tools/monkey_campaign/product/input_mapper.py"
MUTANT_OLD = "INTERVAL_MS = 50"
MUTANT_NEW = "INTERVAL_MS = 40"


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_suite(tree: Path, label: str) -> dict:
    tests = tree / TESTS_REL
    proc = subprocess.run(
        [sys.executable, "-B", str(tests)],
        cwd=str(tree), capture_output=True, text=True, timeout=600)
    out = proc.stdout + proc.stderr
    fail_lines = [ln for ln in out.splitlines() if "[FAIL]" in ln]
    verdict = None
    for ln in out.splitlines():
        if ln.startswith("VERDICT:"):
            verdict = ln.strip()
    return {
        "label": label,
        "exit_code": proc.returncode,
        "fail_count": len(fail_lines),
        "fail_lines": fail_lines,
        "verdict_line": verdict,
        "stdout_tail": out[-2000:],
    }


def main() -> int:
    EVIDENCE.mkdir(exist_ok=True)
    receipt = {
        "schema": "mat2-u01.reconciliation.verification.v1",
        "task_id": "MAT2-U01",
        "attempt_id": "c1488004ef62400389ba98a46837e5b7",
        "agent_id": "arrival-e922be0c34ef46ff84f504eb27e99178",
        "criteria_sha256": "bda3feb8fa32838f8799a83939af08a2d70c6069ec5af7b6c355b759f5aa019e",
        "probes": [],
    }

    # ── probe 1: FAILING-FIRST mutant run (P3 expects FAIL) ─────────────────
    mutant_input = MUTANT / MUTANT_TARGET
    src = (PINNED / MUTANT_TARGET).read_text(encoding="utf-8")
    assert src.count(MUTANT_OLD) == 1, "frozen mutant anchor not unique in pinned bytes"
    mutant_input.parent.mkdir(parents=True, exist_ok=True)
    mutant_input.write_text(src.replace(MUTANT_OLD, MUTANT_NEW, 1), encoding="utf-8")
    mutant_mutation_sha = sha256_file(mutant_input)
    run1 = run_suite(MUTANT, "mutant_INTERVAL_MS_40")
    run1["mutated_file"] = str(mutant_input)
    run1["mutated_file_sha256"] = mutant_mutation_sha
    run1["mutation"] = {"old": MUTANT_OLD, "new": MUTANT_NEW,
                        "semantic": "command cadence bound 50 ms -> 40 ms"}
    receipt["probes"].append(run1)
    print(f"[probe 1 mutant] exit={run1['exit_code']} fails={run1['fail_count']} "
          f"verdict={run1['verdict_line']}")

    # ── probe 2: pinned falsifier run (P2 expects GREEN) ────────────────────
    run2 = run_suite(PINNED, "pinned_bytes")
    receipt["probes"].append(run2)
    print(f"[probe 2 pinned] exit={run2['exit_code']} fails={run2['fail_count']} "
          f"verdict={run2['verdict_line']}")

    # ── probe 3: lineage assertion (P1 expects 7/7) ─────────────────────────
    lineage = []
    for rel, want in PINNED_LINEAGE.items():
        got = sha256_file(PINNED / rel)
        lineage.append({"path": rel, "expected": want, "observed": got,
                        "match": got == want})
    receipt["lineage_assertion"] = {
        "expected_count": len(PINNED_LINEAGE),
        "match_count": sum(1 for e in lineage if e["match"]),
        "entries": lineage,
    }
    print(f"[probe 3 lineage] {receipt['lineage_assertion']['match_count']}/"
          f"{receipt['lineage_assertion']['expected_count']} pinned hashes match")

    # ── frozen predictions, judged from observation ─────────────────────────
    receipt["predictions"] = {
        "P1_lineage_7of7": {"prediction": "match_count == 7",
                            "observed": receipt["lineage_assertion"]["match_count"],
                            "held": receipt["lineage_assertion"]["match_count"] == 7},
        "P2_pinned_green": {"prediction": "exit 0, 0 FAIL lines",
                            "observed": {"exit": run2["exit_code"],
                                         "fails": run2["fail_count"]},
                            "held": run2["exit_code"] == 0 and run2["fail_count"] == 0},
        "P3_mutant_fails": {"prediction": "exit 1, >=1 FAIL line",
                            "observed": {"exit": run1["exit_code"],
                                         "fails": run1["fail_count"]},
                            "held": run1["exit_code"] != 0 and run1["fail_count"] >= 1},
    }
    receipt["falsifier_outcomes"] = {
        "F-A_lineage_drift": "did not fire" if receipt["predictions"]["P1_lineage_7of7"]["held"]
                             else "FIRED",
        "F-B_pinned_fail": "did not fire" if receipt["predictions"]["P2_pinned_green"]["held"]
                           else "FIRED",
        "F-C_suite_vacuous": "did not fire" if receipt["predictions"]["P3_mutant_fails"]["held"]
                             else "FIRED",
    }
    all_held = all(p["held"] for p in receipt["predictions"].values())
    receipt["reconciliation_verified"] = bool(all_held)
    receipt["evidence_class"] = ("component-level over the REAL pinned seam bytes; "
                                 "NOT an integrated-application claim")

    out = EVIDENCE / "verification_receipt.json"
    out.write_text(json.dumps(receipt, indent=1, sort_keys=True), encoding="utf-8")
    print(f"[receipt] {out}")
    print(f"[verdict] all frozen predictions held: {all_held}")
    return 0 if all_held else 1


if __name__ == "__main__":
    sys.exit(main())
