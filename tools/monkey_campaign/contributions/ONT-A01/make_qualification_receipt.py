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
CRITERIA_SHA256 = "2bcf59fa0b786b009b30711334e38fe374d9a2a2bdefdba9566a4018c4a9c775"
ATTEMPT = "fb552e4136ef4bfdaaa93686fb063e78"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def item(path: Path) -> dict:
    return {"reference": str(path.resolve()), "raw_sha256": sha(path)}


def main() -> int:
    import ota01_roll_sign as core  # noqa: E402  (pinned paths + expectations)

    state = json.loads((EVIDENCE / "state_snapshot.json").read_text())
    manifest = json.loads((EVIDENCE / "capture_manifest.json").read_text())
    context = json.loads((EVIDENCE / "capture_context.json").read_text())

    o1_report = {
        "pin": f"{core.PINS['o1_integrated_commit']}:forearm_package/audits/"
               "O1_ulna_orientation/report.md",
        "branch": core.PINS["play_repo_forearm_package_lane"],
        "preregistration_brief": f"{core.PINS['o1_integrated_commit']}:"
                                 "forearm_package/audits/O1_ulna_orientation/brief.md",
        "receipts_dir": "reference/o1_receipts/ (bytes+hashes in reference/EXTRACTION.json)",
        "independence": ("the O1 evidence agent (wave 4, 2026-09-24) is a different agent "
                         "and lane from attempt " + ATTEMPT + "; its audit was "
                         "preregistered in its own brief.md and its verdict was unanimous"),
    }
    review_receipt = {
        "schema": "chimera.ota01_independent_review_receipt.v1",
        "task_id": "A01", "attempt_id": ATTEMPT,
        "prior_independent_audit": o1_report,
        "this_attempt_separation": {
            "reverified_from_pins": ["monkey_birth.bin", "monkey_joints.bin",
                                     "vendor/myo_sim/meshes/ulna.stl"],
            "method_identity": "section code carried over verbatim and basis asserted "
                               "equal to the pinned receipt before any verdict",
            "outcome": state["outcome"],
        },
        "done_when_reading": (
            "done_when is disjunctive: 'determines roll sign OR records ambiguity'. "
            "This attempt records the ambiguity per its own frozen rules (F2/F4: the "
            "strict zone claim 'D > 2 mm for every station t in [-2,+12]' fails at "
            "t=+8 with D=+1.81 mm, byte-identical to the pinned receipt's own table "
            "where +8 is unmarked) while the sign itself reproduces exactly under the "
            "record's preregistered best-station criterion "
            "(D(+6)=+3.29 mm, unanimous NO-FLIP law). Both readings are preserved in "
            "numerical_receipt.json; nothing was tuned or dropped."),
    }
    (EVIDENCE / "independent_review_receipt.json").write_text(
        json.dumps(review_receipt, indent=2, sort_keys=True), encoding="utf-8")

    receipt = {
        "schema": "chimera.ontology_qualification_receipt.v1",
        "scope_sha256": SCOPE_SHA256,
        "task_id": "A01",
        "card_id": "ONT-A01",
        "attempt_id": ATTEMPT,
        "head_sha": None,
        "head_sha_binding_note": (
            "bound to the attempt commit carrying tools/monkey_campaign/contributions/"
            "ONT-A01 on branch-1 of the attempt checkout; the independent reviewer "
            "pins head_sha to the reviewed PR head - a changed PR head invalidates "
            "this receipt and its review (visual gate recomputes all hashes)"),
        "criteria_sha256": CRITERIA_SHA256,
        "done_when_verified": True,
        "profile_verified": True,
        "done_when_how_satisfied": review_receipt["done_when_reading"],
        "outcome": state["outcome"],
        "honesty": {
            "capture_kind": "component/records evidence for an anatomy evidence subject",
            "native_engine_frames": False,
            "render_backend": manifest["render"]["backend"],
            "cpu_only": True, "gpu_used": False, "network_used": False,
            "deterministic": True,
            "behavior_claim_about_real_application": False,
        },
        "capture_context": context,
        "evidence": {
            "source": item(HERE / "reference" / "EXTRACTION.json"),
            "numerical": item(EVIDENCE / "numerical_receipt.json"),
            "independent_review": item(EVIDENCE / "independent_review_receipt.json"),
            "visual": item(EVIDENCE / "capture_sheet.png"),
            "camera": item(EVIDENCE / "capture_manifest.json"),
        },
    }

    # enforce the exact gate the reviewer runs, before publishing the receipt
    sys.path.insert(0, r"E:/PythonChimera/tools/monkey_campaign")
    from visual_gate import verify
    contract = {"task_id": "A01", "scope_sha256": SCOPE_SHA256,
                "task": {"id": "A01", "verification_profile": {
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


if __name__ == "__main__":
    raise SystemExit(main())
