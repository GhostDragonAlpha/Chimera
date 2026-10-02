"""MAT2-X04 capture-card run_all: the NORMAL pipeline entry (template recipe
step 4) — prereg -> capture -> two-stage GATE -> receipts -> review export,
one run per declared case. The gate call is part of the flow: no case can
emit a pass without pipeline.run_pipeline having run the two-stage gate over
every captured frame.

Case table (card-owned, declared before capture in card_prereg.json).
Production cases carry the ACTUAL committed frames of the frozen 39-frame
plan (bound by frame_id from the sealed run's frames artifact); defect cases
are declared perturbations of committed frames proving the gate REJECTS the
four planted classes through THIS card's spec:

    presentation_frames_V1   29 clean + 3 diagnostic  -> EXPECT PASS
    presentation_frames_V2    2 clean + 1 diagnostic  -> EXPECT PASS
    presentation_frames_V3    2 clean + 2 diagnostic  -> EXPECT PASS
    defect_label_missing_but_claimed  (V1 diag 4470)  -> EXPECT REJECT
    defect_body_recolor_shared        (V1 clean 4260) -> EXPECT REJECT
    defect_subject_absent             (V1 diag 4470)  -> EXPECT REJECT
    defect_clean_layer_leak           (V1 clean 4260) -> EXPECT REJECT

Exit law (documented, enforced by the caller shim): 0 iff every production
case's pipeline verdict is GREEN AND every defect case's verdict is RED with
the expected dominant failure code; 1 on any wrong verdict; 2 on a REFUSED
run (prereg or capture-contract violation). verify_pipeline_receipt
re-checks every case's receipt chain from disk as defense in depth.
"""
import json
import os
import sys

CARD = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PARENT = os.path.dirname(CARD)
if TEMPLATE_PARENT not in sys.path:
    sys.path.insert(0, TEMPLATE_PARENT)

from capture_gate import pipeline, view_spec  # noqa: E402

sys.path.insert(0, CARD)
import render_x04  # noqa: E402

CARD_ID = "MAT2-X04"

V1_DIAG_FRAME = "D_V1_t4470"
V1_CLEAN_FRAME = "P00_V1_clean_t4260"

PRODUCTION_CASES = [
    ("presentation_frames_V1", "V1_clean", "V1_diag", "V1_normal_player_camera"),
    ("presentation_frames_V2", "V2_clean", "V2_diag", "V2_detail_display_asset"),
    ("presentation_frames_V3", "V3_clean", "V3_diag", "V3_alternate_angle"),
]

DEFECT_CASES = [
    ("defect_label_missing_but_claimed", V1_DIAG_FRAME, "V1_diag",
     render_x04.LABEL_MISSING_BUT_CLAIMED, "COLOCATION_MISMATCH"),
    ("defect_body_recolor_shared", V1_CLEAN_FRAME, "V1_clean",
     render_x04.BODY_RECOLOR_SHARED, "COLOCATION_MISMATCH"),
    ("defect_subject_absent", V1_DIAG_FRAME, "V1_diag",
     render_x04.SUBJECT_ABSENT, "SUBJECT_MASK_BELOW_FLOOR"),
    ("defect_clean_layer_leak", V1_CLEAN_FRAME, "V1_clean",
     render_x04.CLEAN_LAYER_LEAK, "UNDECLARED_MASK_ID"),
]


def view_class_of(meta):
    return (meta["view"].split("_")[0]
            + ("_diag" if meta["diagnostic"] else "_clean"))


def run_cases(out_root, ctx):
    """Run every declared case through the real pipeline; return summary.

    ``ctx`` carries the sealed run's committed artifacts:
    frames_by_id: {frame_id: (H, W, 3) uint8}, metas: the frame metas.
    """
    spec_path = os.path.join(CARD, "view_spec.json")
    with open(spec_path, "rb") as handle:
        spec = json.loads(handle.read().decode("utf-8"))
    problems = view_spec.validate_spec(spec)
    if problems:
        return {"schema": "chimera.x04_capture_gate_summary.v1",
                "card_id": CARD_ID, "verdict": "REFUSED",
                "refusal": "view_spec_invalid:" + ";".join(problems)}
    render_fn = render_x04.make_renderer(ctx["frames_by_id"], spec)

    metas = ctx["metas"]
    summary = {
        "schema": "chimera.x04_capture_gate_summary.v1",
        "card_id": CARD_ID,
        "template_manifest_sha256": ctx.get("template_manifest_sha256"),
        "view_spec_prereg_sha256":
            view_spec.spec_prereg_sha256(spec),
        "cases": {},
        "production_frames_total": 0,
        "all_production_green": True,
        "all_defects_rejected": True,
    }
    exit_code = 0
    for case_id, clean_cls, diag_cls, view_name in PRODUCTION_CASES:
        members = [m for m in metas if m["view"] == view_name]
        members.sort(key=lambda m: m["render_index"])
        frames_plan = [{"frame_id": m["frame_id"],
                        "view_class": view_class_of(m),
                        "defect": None} for m in members]
        for entry in frames_plan:
            if entry["view_class"] not in (clean_cls, diag_cls):
                return {"schema": "chimera.x04_capture_gate_summary.v1",
                        "card_id": CARD_ID, "verdict": "REFUSED",
                        "refusal": "case_view_class_mismatch:" + case_id}
        out_dir = os.path.join(out_root, "cases", case_id)
        receipt, rc = pipeline.run_pipeline(
            CARD, out_dir, CARD_ID, case_id, render_fn, frames_plan)
        verify = pipeline.verify_pipeline_receipt(out_dir)
        green = receipt.get("verdict") == "GREEN" and not verify
        summary["cases"][case_id] = {
            "kind": "PRODUCTION", "verdict": receipt.get("verdict"),
            "frames_total": receipt.get("gate", {}).get("frames_total"),
            "frames_green": receipt.get("gate", {}).get("frames_green"),
            "verify_problems": verify, "exit_code": rc}
        summary["production_frames_total"] += int(
            receipt.get("gate", {}).get("frames_total") or 0)
        if rc != 0 or not green:
            summary["all_production_green"] = False
            exit_code = exit_code or 1
    for case_id, frame_id, view_class, defect, expected in DEFECT_CASES:
        frames_plan = [{"frame_id": frame_id, "view_class": view_class,
                        "defect": defect}]
        out_dir = os.path.join(out_root, "cases", case_id)
        receipt, rc = pipeline.run_pipeline(
            CARD, out_dir, CARD_ID, case_id, render_fn, frames_plan)
        verify = pipeline.verify_pipeline_receipt(out_dir)
        dominant = None
        if receipt.get("verdict") == "RED":
            rows = receipt.get("gate", {})
            dominant = _dominant_code(out_dir)
        rejected = (receipt.get("verdict") == "RED"
                    and dominant == expected and rc == 1)
        summary["cases"][case_id] = {
            "kind": "DEFECT", "verdict": receipt.get("verdict"),
            "dominant_code": dominant, "expected_code": expected,
            "verify_problems": verify, "exit_code": rc}
        if not rejected:
            summary["all_defects_rejected"] = False
            exit_code = exit_code or 1
    summary["verdict"] = ("GREEN" if exit_code == 0
                          else ("RED" if exit_code == 1 else "REFUSED"))
    summary["exit_code"] = exit_code
    return summary


def _dominant_code(out_dir):
    path = os.path.join(out_dir, pipeline.GATE_RECEIPT_FILENAME)
    with open(path, "rb") as handle:
        gate = json.loads(handle.read().decode("utf-8"))
    codes = []
    for row in gate.get("frames", []):
        for failure in row.get("stage1", {}).get("failures", []):
            codes.append(failure["code"])
        for failure in row.get("stage0", {}).get("failures", []):
            codes.append(failure["code"])
    if not codes:
        return None
    return sorted(set(codes))[0] if len(set(codes)) == 1 else \
        sorted(codes, key=codes.count)[-1]
