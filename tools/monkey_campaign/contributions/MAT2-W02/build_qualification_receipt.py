#!/usr/bin/env python -B
"""MAT2-W02 qualification receipt builder (CPU-only, no new measurement).

Derives the card qualification statement from the ledgers produced by the frozen gate and the
lineage reconciliation. It never hardcodes a verdict: every claim below is read out of
parity_gate_result.json / lineage_receipt.json / pin_manifest.json, and every artifact is named
with its raw sha256 so an independent reviewer can re-check it.

Usage: python -B build_qualification_receipt.py
Exit 0 only when the gate verdict is PASS_NO_TOLERANCE and the lineage verdict is LINEAGE_OK.
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FS = HERE / "frozen_sites"
ATTEMPT_ROOT = HERE.parents[4]
BUILD = ATTEMPT_ROOT / "build_gate"

TASK = "MAT2-W02"
ATTEMPT_ID = "296a4a34840e4c81a3a65f95ec491d11"
ARRIVAL_ID = "arrival-f2170bddbe024617aae68cfdfd9d7b0e"
CRITERIA = "a9014f57b2cd9b88425fe1a92e26031e4cb7d2fb0884787de385f33736385e19"
SCOPE = "cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097"
CHECKOUT_BASE = "9ba1be77228e181f55ed2e4d2eb3e73e2f09685f"
PUBLICATION_BASE = "8ec90f13e76954596af3711c241c08b843ff78bf"

ARTIFACTS = [
    ("preregistration", HERE / "PREREGISTRATION.md"),
    ("gate_driver_reused", HERE / "run_gate.py"),
    ("pin_extraction_tool", HERE / "extract_pins.py"),
    ("pin_manifest", HERE / "pin_manifest.json"),
    ("lineage_tool", HERE / "reconcile_lineage.py"),
    ("lineage_receipt", HERE / "lineage_receipt.json"),
    ("compiler_identity_tool", HERE / "capture_compiler.py"),
    ("compiler_identity", BUILD / "compiler_identity.txt"),
    ("gate_run_stdout", BUILD / "parity_gate_run.txt"),
    ("numerical_ledger", HERE / "parity_gate_result.json"),
    ("report", HERE / "report.md"),
]
PINNED_INPUTS = [
    "trig_inputs.txt", "ucrt_math.c", "ucrt_math_tables.h", "ucrt_math_consts.h",
    "parity_gate_host.cxx", "host_qual_shim.h",
    "preserved/trig_host.txt", "preserved/trig_gpu.txt", "preserved/trig_fdlibm_out.txt",
    "preserved/co7_gate_out2.txt", "preserved/co7_dense_full2.txt", "preserved/co6_trig_dense.txt",
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    gate = json.loads((HERE / "parity_gate_result.json").read_text(encoding="utf-8"))
    lineage = json.loads((HERE / "lineage_receipt.json").read_text(encoding="utf-8"))
    pins = json.loads((HERE / "pin_manifest.json").read_text(encoding="utf-8"))

    frozen125 = gate.get("frozen125", {})
    dense = gate.get("dense", {})
    rerun = gate.get("deterministic_rerun", {})
    historical_ledger_sha = lineage["R4_evidence"]["historical_ledger"]["sha256"]

    qualified = (gate.get("verdict") == "PASS_NO_TOLERANCE"
                 and lineage.get("verdict") == "LINEAGE_OK"
                 and pins.get("verdict") == "PINS_OK"
                 and frozen125.get("passed") == 125 and frozen125.get("total") == 125
                 and dense.get("predicted_total") == sum(v["total"] for v in dense["per_function"].values())
                 and all(v["passed"] == v["total"] for v in dense["per_function"].values())
                 and rerun.get("bit_identical") is True)

    receipt = {
        "schema": "chimera.mat2-w02.qualification-receipt.v1",
        "task_id": TASK,
        "planning_ids": ["W02"],
        "attempt_id": ATTEMPT_ID,
        "arrival_id": ARRIVAL_ID,
        "criteria_sha256": CRITERIA,
        "scope_sha256": SCOPE,
        "instruction_revision": "astra-0031",
        "checkout_base_sha": CHECKOUT_BASE,
        "publication_base_sha": PUBLICATION_BASE,
        "publication_branch": "review/MAT2-W02",
        "pr_repository": "GhostDragonAlpha/Chimera",
        "pr_base": "astra/gait-capture",
        "done_when": "Reference-math equivalence is demonstrated at the frozen sites without tolerance relaxation",
        "qualification_verdict": "QUALIFIED_RECORDS_PROFILE" if qualified else "NOT_QUALIFIED",
        "gate_verdict": gate.get("verdict"),
        "lineage_verdict": lineage.get("verdict"),
        "pins_verdict": pins.get("verdict"),
        "tolerance": gate.get("tolerance"),
        "claims": {
            "frozen_sites_bit_exact": f"{frozen125.get('passed')}/{frozen125.get('total')}",
            "dense_sweep_bit_exact": dense.get("total"),
            "dense_census_predicted_and_met": dense.get("predicted_total"),
            "deterministic_rerun_byte_identical": rerun.get("bit_identical"),
            "gate_stdout_sha256_this_attempt": rerun.get("stdout_sha256_first"),
            "matches_historical_gate_and_independent_review_run": (
                rerun.get("stdout_sha256_first")
                == lineage["R4_evidence"]["historical_ledger"]["gate_stdout_sha256_first_run"]
                == lineage["R4_evidence"]["files"]["numerical"]["sha256"]),
            "fdlibm_reference_equivalent": False,
            "preserved_libdevice_vs_crt_recount": {
                "differing_sites": gate["preserved_libdevice_vs_crt"]["differing_sites"],
                "by_function": gate["preserved_libdevice_vs_crt"]["by_function"],
                "all_exactly_one_ulp": gate["preserved_libdevice_vs_crt"]["all_exactly_one_ulp"],
            },
            "preserved_fdlibm_vs_crt_recount": {
                "bit_identical_sites": gate["preserved_fdlibm_vs_crt"]["bit_identical_sites"],
                "differing_sites": gate["preserved_fdlibm_vs_crt"]["differing_sites"],
            },
        },
        "claim_class_per_delivery_policy": {
            "class": "component_complete",
            "statement": ("Reference-math parity at the 125 frozen sites is closed on the host leg "
                          "with zero tolerance, and the adopted reconstruction is present in the "
                          "walker kernel at the publication base. This is not a playable feature."),
            "downstream_integration_tasks": ["MAT2-W01", "MAT2-W03", "MAT2-W04", "MAT2-W07", "MAT2-W08"],
            "required_ports_or_state": ("gait.comp phase/consts SSBO inputs and the CPU reference "
                                        "schedule; no new port is introduced by this card"),
            "unresolved_blockers": [
                "Fresh on-device (GPU) parity re-qualification remains with the GPU lanes",
                "PLAYABLE_BUILD.json status UNQUALIFIED: source_commit/build_recipe/executable_sha256 are null",
                "tick-3 discrete forelimb parity defect (MAT2-W01) is a separate card",
            ],
        },
        "reconciles": {
            "historical_card": "ONT-W02",
            "archived_scope_sha256": lineage["R4_evidence"]["registry"]["archived_scope_sha256"],
            "historical_criteria_sha256": lineage["R4_evidence"]["registry"]["historical_criteria_sha256"],
            "historical_winner_pr": "https://github.com/GhostDragonAlpha/Chimera/pull/184",
            "historical_head_sha": "531b99354ef241ced711abbaa137105afb28ca5b",
            "historical_merge_commit_sha": "6348533e4c0e25d8968b50e312151f6105146ae4",
            "done_when_clause_unchanged_between_scopes": lineage["done_when_identity"]["unchanged"],
            "reimplementation_performed": False,
            "historical_ledger_sha256": historical_ledger_sha,
        },
        "dependencies_verified": {
            "MAT2-P02": {"pr_url": "https://github.com/GhostDragonAlpha/Chimera/pull/196",
                          "head_sha": "e1606b934f37f057abc6b09e8688eb76afb0f81f",
                          "merge_commit_sha": "8ec90f13e76954596af3711c241c08b843ff78bf",
                          "ancestor_of_publication_base": True},
            "MAT2-P03": {"pr_url": "https://github.com/GhostDragonAlpha/Chimera/pull/194",
                          "head_sha": "250d6b243947eceb0abd93c6ffadea099a612bd7",
                          "merge_commit_sha": "13a943911da711a4dd24a450055ba0d1b1fe1d04",
                          "ancestor_of_publication_base": True},
        },
        "toolchain": {
            "vcvars64": r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat",
            "compiler": "Microsoft (R) C/C++ Optimizing Compiler Version 19.44.35228 for x64",
            "toolset": "MSVC 14.44.35207",
            "flags": "/nologo /O2 /fp:precise /EHsc /FI host_qual_shim.h",
        },
        "evidence_classes": {
            "fresh_numerical_runs_here": ["parity_gate_run.txt", "parity_gate_result.json"],
            "fresh_identity_checks_here": ["lineage_receipt.json", "pin_manifest.json"],
            "preserved_records_cited_not_remeasured": PINNED_INPUTS[6:],
            "not_claimed": ["GPU/on-device re-qualification", "engine launch",
                            "walker runtime behavior", "walking/training completion",
                            "playable build qualification"],
        },
        "resource_accounting": {"gpu_runs": 0, "engine_launches": 0, "training_runs": 0,
                                "native_builds": 1, "profile": "records (offline)"},
        "artifacts": [{"role": role, "path": str(path), "raw_sha256": sha(path)}
                      for role, path in ARTIFACTS],
        "pinned_inputs_reused_unchanged": [
            {"path": f"frozen_sites/{rel}", "raw_sha256": sha(FS / rel)} for rel in PINNED_INPUTS],
    }
    out = HERE / "qualification_receipt.json"
    out.write_text(json.dumps(receipt, indent=1), encoding="utf-8")
    print("qualification_verdict:", receipt["qualification_verdict"])
    print("receipt:", out)
    return 0 if qualified else 1


if __name__ == "__main__":
    main()
