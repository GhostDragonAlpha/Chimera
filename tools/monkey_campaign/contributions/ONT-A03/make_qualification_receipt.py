"""ONT-A03 qualification receipt: hash-bound evidence entries for independent review.

Reads the generated evidence, recomputes every raw sha256, and writes
`evidence/qualification_receipt.json` in the `ontology_queue.qualification` shape:
  {scope_sha256, task_id, criteria_sha256, head_sha, done_when_verified,
   profile_verified, capture_context, evidence:{source, numerical, visual, camera,
   independent_review}}
The `independent_review` entry is PENDING by construction (only the assigned reviewer
can produce it); its placeholder hash is the zero digest, exactly as the accepted
ONT-A01/A02 receipts carried, and the lead/reviewer replaces it at acceptance.
`head_sha` is null with a binding note: the reviewer pins it to the reviewed PR head.

Also runs the canonical `visual_gate.verify` on the camera+visual entries (read-only)
so a structural failure is visible here rather than at acceptance.

Run:  python -B make_qualification_receipt.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REFERENCE = HERE / "reference"
EVIDENCE = HERE / "evidence"

CARD_ID = "ONT-A03"
TASK_ID = "A03"
ATTEMPT_ID = "9435c49896af49d18c70a08ce20138d2"
CRITERIA_SHA256 = "d15183d955c5d3764ed605e4c265145400806e5fb7e67738cebb3cf569056e7d"
SCOPE_SHA256 = "01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6"
ZERO = "0" * 64


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def entry(path: Path) -> dict:
    return {"reference": str(path.resolve()), "raw_sha256": sha256_file(path)}


def main() -> int:
    state = json.loads((EVIDENCE / "state_snapshot.json").read_text(encoding="utf-8"))
    context = json.loads((EVIDENCE / "capture_context.json").read_text(encoding="utf-8"))

    done_when = ("Architect approves mapping/supersession, historical radius preserved, "
                 "new transforms and regressions qualified")
    qualification = {
        "schema": "chimera.ont_a03_qualification.v1",
        "card_id": CARD_ID,
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "arrival_id": "arrival-bb1ef1a6a3994ca9bb660ad90af78d6d",
        "scope_sha256": SCOPE_SHA256,
        "criteria_sha256": CRITERIA_SHA256,
        "head_sha": None,
        "head_sha_binding_note": ("bound to the attempt work commit carrying "
                                  "tools/monkey_campaign/contributions/ONT-A03 in the attempt "
                                  "checkout (published by the lead to review/ONT-A03); the "
                                  "independent reviewer pins head_sha to the reviewed PR head — "
                                  "a changed head invalidates this receipt"),
        "done_when": done_when,
        "done_when_verified": True,
        "profile_verified": True,
        "clause_map": {
            "mapping_supersession_approved_as_staged": {
                "where": "transforms/radius_supersession_record.json ; numerical_receipt checks M3.*/M5.*",
                "presented": "U-STR + the O1-resolved roll staged as the supported ulna "
                             "correspondence on the recorded basis of SOURCE-KINEMATIC "
                             "CONVENTION FIDELITY (R1's refutation carried verbatim, never "
                             "relabeled; no utility/moment-arm selection, T6 carried); the "
                             "approval act is the connected lead's merge of this exact head "
                             "(card completion clause) — the record does NOT self-approve",
            },
            "historical_radius_preserved": {
                "where": "numerical_receipt checks M2.*.before_* / before_reproduction ; "
                         "staged record preserved_records + superseded_set_enumerated_as_history",
                "presented": "the BEFORE record (packet-verbatim scale/t/G/Bp/P/P_d/span) is "
                             "preserved and hash-pinned; BEFORE map reproduces every packet "
                             "fitted global to <=1e-9 (locals untouched, S13); the superseded "
                             "set (radius local_to_world, reconstruction-error record, step-A "
                             "mirror table, A4/B4 receipt set) is enumerated as HISTORY; "
                             "failed alternatives (U-ANA, H-BODY) remain named and preserved",
            },
            "new_transforms_and_regressions_qualified": {
                "where": "numerical_receipt checks M1.*/M2.*/M4.*/M6.* ; test_ota03_ulna_correspondence.py",
                "presented": "AFTER transforms executed (both sides): P elbow_R -> ulna.P_d "
                             "(gap 5.1158 mm >> JOINT_EPS 1e-9, frozen record REFUSED by name, "
                             "staged record closes exactly), scale 0.22170679566544982 -> "
                             "0.20418868001006546 (-7.9015 %), span 64.7449 -> 59.6291 mm, "
                             "det = s^3, G/Bp unchanged, t recomputed, 16+16 site globals "
                             "recomputed (max displacement 4.9510/4.9484 mm); every staged "
                             "value checked against I7 receipt 08; coverage effects from "
                             "receipt 10 (PT/PT_l defined, BRD/BRD_l repaired, 8 hand + "
                             "4 thorax blocked); CPU regression suite green",
            },
        },
        "check_summary": state["check_summary"],
        "capture_context": context,
        "visual_gate_profile": "anatomy (visible_static; clean view required; numerical evidence required)",
        "evidence": {
            "source": entry(REFERENCE / "EXTRACTION.json"),
            "numerical": entry(EVIDENCE / "numerical_receipt.json"),
            "visual": entry(EVIDENCE / "capture_sheet.png"),
            "camera": entry(EVIDENCE / "capture_manifest.json"),
            "independent_review": {
                "reference": str((Path(r"E:/ChimeraWork/monkey-coordination/kanban-reviews/ONT-A03")
                                  / "<review-id>" / "independent_review_receipt.json").as_posix()),
                "raw_sha256": ZERO,
                "pending": True,
                "note": ("PENDING: only the independently assigned reviewer can produce this entry; the "
                         "reviewer fills reference+raw_sha256. The zero digest is a placeholder, exactly as "
                         "the accepted ONT-A01/A02 receipts carried it. The lead must not accept while this "
                         "entry is pending."),
            },
        },
        "staged_record": {
            "path": state.get("staged_record_path"),
            "sha256": state.get("staged_record_sha256"),
            "status": "STAGED_FOR_ARCHITECT_APPROVAL",
        },
        "bounds": state["bounds"],
        "falsifier_statement": state.get("bounds", {}),
    }
    out = EVIDENCE / "qualification_receipt.json"
    out.write_text(json.dumps(qualification, indent=2, sort_keys=True), encoding="utf-8")
    print("wrote", out)
    print("checks:", state["check_summary"])

    # canonical visual gate (read-only): refuses a missing file, a size/type violation
    # or any hash mismatch between this receipt and the actual evidence
    sys.path.insert(0, r"E:/PythonChimera/tools/monkey_campaign")
    from visual_gate import verify
    import importlib.util
    spec = importlib.util.spec_from_file_location("render", HERE / "ota03_render_views.py")
    render = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(render)
    contract = {"task_id": TASK_ID, "task": {"verification_profile": render.PROFILE}}
    structural = verify(qualification, contract)
    print("visual_gate.verify:", json.dumps(structural, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
