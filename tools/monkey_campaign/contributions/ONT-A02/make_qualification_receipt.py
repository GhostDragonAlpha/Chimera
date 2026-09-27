"""Build evidence/qualification_receipt.json (ontology_queue.qualification shape)
and evidence/independent_review_receipt.json, binding absolute evidence paths to
recomputed sha256 values. Deterministic; run with python -B.

head_sha is authored as null with an explicit binding note: the receipt binds to
the attempt commit that carries these artifacts; per card policy the reviewer
pins head_sha to the reviewed PR head (a changed PR head invalidates receipt and
review).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"

SCOPE_SHA256 = "01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6"
CRITERIA_SHA256 = "ab47206c8bd41e3f9769f8f96489545c3335cf2183a76f88f6c010e3b3789cb1"
ATTEMPT = "b4a2b12b8c854e55bc400c64a502c85c"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def item(path: Path) -> dict:
    return {"reference": str(path.resolve()), "raw_sha256": sha(path)}


def main() -> int:
    import ota02_radioulnar as core  # noqa: E402  (pinned paths + expectations)

    state = json.loads((EVIDENCE / "state_snapshot.json").read_text())
    manifest = json.loads((EVIDENCE / "capture_manifest.json").read_text())
    context = json.loads((EVIDENCE / "capture_context.json").read_text())

    prior_audits = {
        "O1_ulna_orientation": {
            "pin": f"{core.PINS['o1_report']} (+ brief.md and receipts, "
                   f"branch forearm-package-20260924)",
            "agent": "O1 evidence agent (wave 4, 2026-09-24), a different agent "
                     "and lane from attempt " + ATTEMPT,
            "used_here": "the frozen roll sign law and the declared candidate's "
                         "roll pair; re-verified from pins by ONT-A01 at "
                         "PR 176 (its own evidence, bound to A01)",
        },
        "R1_radioulnar_evidence": {
            "pin": f"{core.PINS['r1_report']} (+ receipts/arithmetic.txt, "
                   f"extracted hash-bound under reference/r1_receipts/)",
            "agent": "R1 evidence agent (wave 4, 2026-09-24), independent "
                     "web-primary-source lane",
            "used_here": "the RETAINED anatomical refutation and the 5.3 drift "
                         "law; its falsifier outcome is preserved, not relabeled",
        },
        "I7_isolated_ustr_b4": {
            "pin": f"{core.PINS['i7_gate_table']}, {core.PINS['i7_radius_before_after']}, "
                   f"{core.PINS['i7_coverage_topology']}",
            "agent": "M-A02diag (2026-09-24), distinct diagnostic lane",
            "used_here": "the receipted B4 T1-T6 verdicts (presented, not "
                         "re-run) and the before/after/coverage receipts this "
                         "attempt re-derived from raw pins",
        },
    }
    review_receipt = {
        "schema": "chimera.ota02_independent_review_receipt.v1",
        "task_id": "A02", "attempt_id": ATTEMPT,
        "prior_independent_audits": prior_audits,
        "this_attempt_separation": {
            "rederived_from_pins": ["chimanoid.xml", "actual_monkey_fit.json",
                                    "monkey_birth.bin", "monkey_joints.bin",
                                    "00_candidate_declaration.json",
                                    "01_known_good_records.json"],
            "method_identity": ("the DERIVATION 5.1 ONB construction law is "
                                "re-implemented in this attempt's module and "
                                "asserted equal to the pinned records (packet "
                                "site reproduction max err "
                                f"{MAP_VAL(state)} m) before any verdict"),
            "outcome": state["outcome"],
            "fired_falsifiers": state["fired_falsifiers"],
            "fired_note": ("P3:mirror_t_overbroad_prediction is THIS attempt's "
                           "own frozen prediction authored too broadly "
                           "(mirror-exactness claimed for a translation whose "
                           "inputs are asymmetric); the receipt itself carries "
                           "the same asymmetry; both readings preserved; no "
                           "tolerance was moved post hoc"),
        },
        "reviewer_review_still_required": (
            "a non-author independent review of THIS exact candidate head and "
            "evidence remains the review lane's step; the historical audits "
            "above are evidence inputs, not a review of this attempt"),
        "done_when_reading": (
            "done_when is conjunctive: radioulnar definition (P1/P2 + V3), "
            "independent evidence (this attempt's own pin-bound re-derivation "
            "+ the three pinned independent audits), B4 result (receipted "
            "T1-T6 table presented with its source-kinematic-only bound and "
            "the machine-forced closure mechanism re-derived), and before/after "
            "radius mapping (closed-form both sides, reproduced to 1e-12 where "
            "the receipts are exact) - all four are presented and hash-bound"),
    }
    (EVIDENCE / "independent_review_receipt.json").write_text(
        json.dumps(review_receipt, indent=2, sort_keys=True), encoding="utf-8")

    receipt = {
        "schema": "chimera.ontology_qualification_receipt.v1",
        "scope_sha256": SCOPE_SHA256,
        "task_id": "A02",
        "card_id": "ONT-A02",
        "attempt_id": ATTEMPT,
        "head_sha": None,
        "head_sha_binding_note": (
            "bound to the attempt work commit carrying tools/monkey_campaign/"
            "contributions/ONT-A02 in the attempt checkout (published by the "
            "lead to review/ONT-A02); the independent reviewer pins head_sha "
            "to the reviewed PR head - a changed PR head invalidates this "
            "receipt and its review (visual gate recomputes all hashes)"),
        "criteria_sha256": CRITERIA_SHA256,
        "done_when_verified": True,
        "profile_verified": True,
        "done_when_how_satisfied": review_receipt["done_when_reading"],
        "outcome": state["outcome"],
        "honesty": {
            "capture_kind": "component/records evidence for an anatomy "
                            "evidence subject (radioulnar definition, B4 "
                            "result, before/after radius mapping)",
            "native_engine_frames": False,
            "render_backend": manifest["render"]["backend"],
            "cpu_only": True, "gpu_used": False, "network_used": False,
            "deterministic": True,
            "behavior_claim_about_real_application": False,
            "supersession_executed": False,
            "production_authority_claimed": False,
            "anatomical_support_claimed": False,
            "outcome_note": ("DISCREPANCY_RECORDED refers to this attempt's "
                             "own over-broad frozen mirror prediction, "
                             "recorded per falsifier FA; every source-evidence "
                             "reproduction is within its frozen tolerance"),
        },
        "capture_context": context,
        "evidence": {
            "source": item(HERE / "reference" / "EXTRACTION.json"),
            "numerical": item(EVIDENCE / "numerical_receipt.json"),
            "state": item(EVIDENCE / "state_snapshot.json"),
            "independent_review": item(EVIDENCE / "independent_review_receipt.json"),
            "visual": item(EVIDENCE / "capture_sheet.png"),
            "camera": item(EVIDENCE / "capture_manifest.json"),
            "preregistration": item(HERE / "PREREGISTRATION.md"),
        },
    }

    # enforce the exact gate the reviewer runs, before publishing the receipt
    sys.path.insert(0, r"E:/PythonChimera/tools/monkey_campaign")
    from visual_gate import verify
    contract = {"task_id": "A02", "scope_sha256": SCOPE_SHA256,
                "task": {"id": "A02", "verification_profile": {
                    "id": "anatomy", "kind": "visible_static",
                    "views": ["whole-creature overview", "local attachment close-up",
                              "orthogonal side and oblique views"],
                    "diagnostic_layers": ["outer envelope", "selected bones/joints",
                                          "muscle/tendon paths", "attachment sites",
                                          "frame axes", "stable 3D labels"],
                    "clean_view_required": True}}}
    structural = verify(receipt, contract)
    assert structural["structurally_valid"] is True, structural

    (EVIDENCE / "qualification_receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print("visual_gate.verify:", structural["structurally_valid"],
          "| views:", structural["view_count"])
    print("wrote", EVIDENCE / "qualification_receipt.json")
    print("wrote", EVIDENCE / "independent_review_receipt.json")
    return 0


def MAP_VAL(state):
    return state["before_after_radius_map"]["right"]["packet_reconstruction_max_err_m"]


if __name__ == "__main__":
    raise SystemExit(main())
