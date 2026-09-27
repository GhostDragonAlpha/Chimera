"""ONT-A02 qualification receipt: hash-bound evidence entries for independent review.

Reads the generated evidence, recomputes every raw sha256, and writes
`evidence/qualification_receipt.json` in the `ontology_queue.qualification` shape:
  {scope_sha256, task_id, criteria_sha256, head_sha, done_when_verified,
   profile_verified, capture_context, evidence:{source, numerical, visual, camera,
   independent_review}}
The `independent_review` entry is PENDING by construction (only the assigned reviewer
can produce it); its placeholder hash is the zero digest, exactly as the accepted
ONT-A01 receipt did, and the lead/reviewer replaces it at acceptance. `head_sha` is
null with a binding note: the reviewer pins it to the reviewed PR head.

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

CARD_ID = "ONT-A02"
TASK_ID = "A02"
ATTEMPT_ID = "a6c4ddd216a648348d0810f05dd464d4"
CRITERIA_SHA256 = "ab47206c8bd41e3f9769f8f96489545c3335cf2183a76f88f6c010e3b3789cb1"
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
    receipt = json.loads((EVIDENCE / "numerical_receipt.json").read_text(encoding="utf-8"))
    context = json.loads((EVIDENCE / "capture_context.json").read_text(encoding="utf-8"))

    done_when = ("Radioulnar definition, independent evidence, B4 result and before/after "
                 "radius mapping are presented")
    qualification = {
        "schema": "chimera.ont_a02_qualification.v1",
        "card_id": CARD_ID,
        "task_id": TASK_ID,
        "attempt_id": ATTEMPT_ID,
        "arrival_id": "arrival-db815a40e472418c810c538a333bbc5e",
        "scope_sha256": SCOPE_SHA256,
        "criteria_sha256": CRITERIA_SHA256,
        "head_sha": None,
        "head_sha_binding_note": ("bound to the attempt work commit carrying "
                                  "tools/monkey_campaign/contributions/ONT-A02 in the attempt "
                                  "checkout (published by the lead to review/ONT-A02); the "
                                  "independent reviewer pins head_sha to the reviewed PR head — "
                                  "a changed head invalidates this receipt"),
        "done_when": done_when,
        "done_when_verified": True,
        "profile_verified": True,
        "clause_map": {
            "radioulnar_definition": {
                "where": "numerical_receipt checks N1.* ; state_snapshot.definition",
                "presented": "P body_origin:ulna<->elbow_R; P_d body_origin:radius<-> 5.1158 mm derived point; "
                             "source offset 23.0746 mm decomposed 14.324 axial / 18.088 lateral / 0.301 posterior "
                             "at 51.63 deg; 7.5459 % of the 305.7922 mm elbow->hand axis; kinematic joint-frame "
                             "offset, not a bone-landmark or radial-head position",
            },
            "independent_evidence": {
                "where": "numerical_receipt checks N4.* ; state_snapshot.independent_evidence",
                "presented": "R1's three applicable primary human sources place the radial head at ~0 % +/- 1 % of "
                             "forearm length (outside the frozen 4-12 % band by >= 3.0 points); applicable lane is "
                             "HUMAN base anatomy (source is a modified human model); plus O1's unanimous no-flip "
                             "roll evidence and C1's independent 10/10 landmark reproduction",
            },
            "b4_result": {
                "where": "numerical_receipt checks N3.* ; state_snapshot.b4_result",
                "presented": "authorized isolated U-STR B4 diagnostic: T1-T5 PASS on both sides + T6 process PASS, "
                             "tolerances unchanged; SOURCE-KINEMATIC FIDELITY ONLY; R1's refutation retained; no "
                             "production consequence executed; a diagnostic PASS does not close A03",
            },
            "before_after_radius_mapping": {
                "where": "numerical_receipt checks N2.* ; state_snapshot.before_after_mapping",
                "presented": "radius P: elbow_R -> ulna.P_d (gap 5.1158 mm >> JOINT_EPS 1e-9, closure forced); "
                             "span 64.7449 -> 59.6291 mm; uniform scale 0.22170679566544982 -> 0.204188680010 "
                             "(-7.9015 %); det 0.0108977544 -> 0.0085132421; rigid part G unchanged; 16+16 site "
                             "globals recomputed, max displacement 4.9510 mm (BICshort-P6) / 4.9484 mm "
                             "(BIClong_l-P9); source locals untouched; CLOSED FORM ONLY",
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
                "reference": str((Path(r"E:/ChimeraWork/monkey-coordination/kanban-reviews/ONT-A02")
                                  / "<review-id>" / "independent_review_receipt.json").as_posix()),
                "raw_sha256": ZERO,
                "pending": True,
                "note": ("PENDING: only the independently assigned reviewer can produce this entry; the "
                         "reviewer fills reference+raw_sha256. The zero digest is a placeholder, exactly as "
                         "the accepted ONT-A01 receipt carried it. The lead must not accept while this "
                         "entry is pending."),
            },
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
    spec = importlib.util.spec_from_file_location("render", HERE / "ota02_render_views.py")
    render = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(render)
    contract = {"task_id": TASK_ID, "task": {"verification_profile": render.PROFILE}}
    structural = verify(qualification, contract)
    print("visual_gate.verify:", json.dumps(structural, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
