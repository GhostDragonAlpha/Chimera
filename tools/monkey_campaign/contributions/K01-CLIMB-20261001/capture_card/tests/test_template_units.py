#!/usr/bin/env python
"""Template unit tests (deterministic; canonical JSON receipts; no RNG).

Covers the integration-specific behavior that the VISUAL-GATE-1 prototype
did not have:

- prereg binding: pin present/matching, tamper refusal BEFORE capture;
- sidecar capture: channel-isolation refusals, deterministic manifests;
- pipeline: gate-not-run refusal, tamper-evident receipt chain, exit-code
  law through the real run_pipeline path;
- palette stage-0: blank detection; totals kept as smoke census only.

Run: python -B tests/test_template_units.py   (exit 0 iff all checks pass)
"""

import json
import os
import shutil
import sys
import tempfile

TEMPLATE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if TEMPLATE_ROOT not in sys.path:
    sys.path.insert(0, TEMPLATE_ROOT)

sys.path.insert(0, os.path.join(TEMPLATE_ROOT, "demo_card"))
import render_card  # noqa: E402

from capture_gate import mask_gate, palette_stage, pipeline, prereg, sidecar, view_spec  # noqa: E402

FAILED = []
CHECKS_RUN = [0]


def check(name, condition, detail=""):
    CHECKS_RUN[0] += 1
    status = "PASS" if condition else "FAIL"
    print("[%s] %s%s" % (status, name, (" :: " + detail) if detail and not condition else ""))
    if not condition:
        FAILED.append(name)
    return condition


def case_plan(case_id, view_class, defect=None):
    return [{"frame_id": case_id, "view_class": view_class, "defect": defect}]


def run_case(tmp, case_id, view_class, defect=None, card_root=None):
    out_dir = os.path.join(tmp, case_id)
    return pipeline.run_pipeline(
        card_root or render_card.CARD_ROOT, out_dir, render_card.CARD_ID,
        case_id, render_card.render, case_plan(case_id, view_class, defect))


def main():
    # t01: the card view-spec validates and matches the prereg pin.
    spec = render_card.load_card_spec()
    check("t01_demo_spec_valid", view_spec.validate_spec(spec) == [])
    prereg_dict, _, binding = prereg.check_prereg_stage(render_card.CARD_ROOT, spec=spec)
    check("t02_prereg_pin_matches_spec",
          binding["prereg_sha256"] == prereg_dict["view_spec"]["prereg_sha256"]
          == view_spec.spec_prereg_sha256(spec))

    # t03: threshold tamper is refused BEFORE capture.
    tampered = view_spec.load_spec(spec)
    tampered["view_classes"]["clean"]["min_visible_pixels"]["thorax"] += 1
    try:
        prereg.check_prereg_stage(render_card.CARD_ROOT, spec=tampered)
        check("t03_tampered_spec_refused", False, "no refusal raised")
    except prereg.PreregRefused as refused:
        check("t03_tampered_spec_refused",
              "prereg_spec_hash_mismatch" in str(refused), str(refused))

    # t04: missing pin fields and false declared-before flags are refused.
    for field in ("prereg_sha256", "spec_id"):
        broken = json.loads(json.dumps(prereg_dict))
        if field == "prereg_sha256":
            del broken["view_spec"]["prereg_sha256"]
        else:
            broken["view_spec"]["spec_id"] = "other-spec"
        problems = prereg.binding_problems(broken, spec)
        check("t04_prereg_missing_%s_refused" % field,
              any(field in p for p in problems), ";".join(problems))
    falsey = json.loads(json.dumps(prereg_dict))
    falsey["declared_before_capture"] = False
    problems = prereg.binding_problems(falsey, spec)
    check("t05_declared_before_capture_false_refused",
          "prereg_declared_before_capture_must_be_true" in problems, ";".join(problems))

    # t06: beauty carrying a mask code is refused at capture time.
    beauty, mask = render_card.render("clean", "t6")

    def leaky_render(view_class, frame_id, defect=None):
        bad = beauty.copy()
        bad[60, 20] = mask[60, 20]  # leg_left's object-ID code in the beauty frame
        return bad, mask

    try:
        sidecar.capture_frame(spec, "clean", leaky_render, "t6")
        check("t06_beauty_mask_code_leak_refused", False, "no refusal raised")
    except sidecar.CaptureRefused as refused:
        check("t06_beauty_mask_code_leak_refused",
              "beauty_carries_mask_code" in str(refused), str(refused))

    # t07: an undeclared mask code is refused at capture time...
    bad_mask = mask.copy()
    bad_mask[5, 5] = (1, 2, 3)

    def rogue_render(view_class, frame_id, defect=None):
        return beauty, bad_mask

    try:
        sidecar.capture_frame(spec, "clean", rogue_render, "t7")
        check("t07_mask_undeclared_code_refused", False, "no refusal raised")
    except sidecar.CaptureRefused as refused:
        check("t07_mask_undeclared_code_refused",
              "mask_undeclared_code" in str(refused), str(refused))
    # ...and the stage-1 gate re-checks declared codes as defense in depth.
    direct = mask_gate.evaluate_frame(spec, "clean", beauty, bad_mask, "t7")
    check("t08_gate_rechecks_undeclared_code",
          direct["verdict"] == "RED"
          and any(f["code"] == "UNDECLARED_MASK_ID" for f in direct["failures"]),
          str(direct["failures"]))

    # t09: capture manifests are byte-deterministic for identical plans.
    tmp = tempfile.mkdtemp(prefix="cg-units-")
    try:
        for run in ("a", "b"):
            out_dir = os.path.join(tmp, "det_" + run)
            pipeline.run_pipeline(render_card.CARD_ROOT, out_dir,
                                  render_card.CARD_ID, "det",
                                  render_card.render, case_plan("det", "clean"))
        with open(os.path.join(tmp, "det_a", "capture_manifest.json"), "rb") as h:
            bytes_a = h.read()
        with open(os.path.join(tmp, "det_b", "capture_manifest.json"), "rb") as h:
            bytes_b = h.read()
        check("t09_capture_manifest_deterministic", bytes_a == bytes_b)

        # t10: a pipeline receipt cannot be assembled without a gate receipt.
        try:
            pipeline.assemble_pipeline_receipt("x", "card", spec, binding,
                                               "0" * 64, None, None, None)
            check("t10_gate_not_run_refused", False, "no refusal raised")
        except pipeline.GateNotRun as refused:
            check("t10_gate_not_run_refused",
                  "gate_not_run" in str(refused), str(refused))

        # t11: the receipt chain detects a tampered gate receipt on disk.
        receipt, exit_code = run_case(tmp, "chain", "clean")
        check("t11_healthy_case_green_exit0",
              receipt["verdict"] == "GREEN" and exit_code == 0,
              "%s/%s" % (receipt["verdict"], exit_code))
        out_dir = os.path.join(tmp, "chain")
        gate_path = os.path.join(out_dir, "gate_receipt.json")
        with open(gate_path, "rb") as handle:
            gate_bytes = handle.read()
        with open(gate_path, "wb") as handle:
            handle.write(gate_bytes.replace(b'"frames_green":1', b'"frames_green":2', 1))
        problems = pipeline.verify_pipeline_receipt(out_dir)
        check("t12_tampered_gate_detected",
              "gate_receipt_sha256_mismatch" in problems, ";".join(problems))
        with open(gate_path, "wb") as handle:
            handle.write(gate_bytes)
        check("t13_chain_verifies_when_intact",
              pipeline.verify_pipeline_receipt(out_dir) == [])

        # t14: stage-0 blank detection still works (U07 law retained).
        blank = palette_stage.evaluate_frame_palette(
            (beauty * 0 + beauty.reshape(-1, 3)[0]).astype("uint8"))
        check("t14_stage0_blank_red",
              blank["verdict"] == "RED"
              and any(f["code"] == "BLANK_UNIFORM" for f in blank["failures"]))
        stage0 = palette_stage.evaluate_frame_palette(beauty)
        check("t15_stage0_healthy_green", stage0["verdict"] == "GREEN")

        # t16-t19: the four planted defect classes REJECT through the real
        # pipeline path with the designed failure codes.
        designed = [
            ("def_wrong_body", "clean", "WRONG_BODY_COLOR_SHARE",
             ("COLOCATION_MISMATCH", "leg_left")),
            ("def_shared_inflation", "clean", "SHARED_COLOR_INFLATION_ABSENT",
             ("SUBJECT_MASK_BELOW_FLOOR", "leg_left")),
            ("def_subject_absent", "clean", "SUBJECT_ABSENT",
             ("SUBJECT_MASK_BELOW_FLOOR", "leg_right")),
            ("def_undeclared_occl", "clean", "UNDECLARED_OCCLUSION",
             ("UNDECLARED_MASK_ID", "occluder")),
        ]
        for case_id, view_class, defect, expected in designed:
            receipt, exit_code = run_case(tmp, case_id, view_class, defect)
            with open(os.path.join(tmp, case_id, "gate_receipt.json"), "rb") as h:
                gate = json.loads(h.read().decode("utf-8"))
            codes = {(f["code"], f["object_id"])
                     for row in gate["frames"] for f in row["stage1"]["failures"]}
            check("t16_%s_rejected_exit1" % case_id,
                  receipt["verdict"] == "RED" and exit_code == 1
                  and expected in codes,
                  "%s/%s/%s" % (receipt["verdict"], exit_code, sorted(codes)))

        # t20: declared occlusion passes via exception with census + review.
        receipt, exit_code = run_case(tmp, "decl", "obstructed")
        out_dir = os.path.join(tmp, "decl")
        with open(os.path.join(out_dir, "gate_receipt.json"), "rb") as h:
            gate = json.loads(h.read().decode("utf-8"))
        check("t20_declared_occlusion_green_exception1",
              receipt["verdict"] == "GREEN" and exit_code == 0
              and len(gate["exception_rows"]) == 1
              and gate["exception_rows"][0]["exception_class"] == "DECLARED_OCCLUSION")
        review_manifest_path = os.path.join(out_dir, "review", "review_manifest.json")
        with open(review_manifest_path, "rb") as handle:
            review = json.loads(handle.read().decode("utf-8"))
        crop_path = os.path.join(out_dir, "review", review["entries"][0]["crop_file"])
        check("t21_review_crop_hash_bound",
              review["exception_count"] == 1
              and prereg.sha256_file(crop_path)
              == review["entries"][0]["crop_sha256"]
              and receipt["review_export"]["manifest_sha256"]
              == prereg.sha256_file(review_manifest_path))

        # t22: the healthy 'close' class passes through the same path.
        receipt, exit_code = run_case(tmp, "close", "close")
        check("t22_close_class_green",
              receipt["verdict"] == "GREEN" and exit_code == 0)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("UNIT %s: %d checks, %d failed"
          % ("GREEN" if not FAILED else "RED", CHECKS_RUN[0], len(FAILED)))
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
