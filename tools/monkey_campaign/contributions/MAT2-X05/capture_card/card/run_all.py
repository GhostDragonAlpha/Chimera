"""MAT2-X05 capture-card run_all: the NORMAL pipeline entry (template recipe
step 4) — prereg -> capture -> two-stage GATE -> receipts -> review export,
one run per declared case. The gate call is part of the flow: no case can
emit a pass without pipeline.run_pipeline having run the two-stage gate over
every captured frame.

Case table (card-owned, declared before capture in card_prereg.json).
Production cases carry the ACTUAL committed frames of the frozen 24-frame
plan per arm per pair (bound by frame_id from the sealed run's frames
artifacts); defect cases are declared perturbations of committed frames
proving the gate REJECTS the four planted classes through THIS card's spec:

    presentation_frames_P01..P10 x {A, B}   21 clean + 3 diagnostic each
                                            -> EXPECT PASS (20 cases)
    defect_instrument_erased_but_claimed  (P01_B clean 4365) -> EXPECT REJECT
    defect_landmark_recolor_shared        (P01_B clean 4365) -> EXPECT REJECT
    defect_body_absent                    (P01_B clean 4365) -> EXPECT REJECT
    defect_clean_diagnostic_leak          (P01_B clean 4365) -> EXPECT REJECT

Exit law (documented, enforced by the caller stage): 0 iff every production
case's pipeline verdict is GREEN AND every defect case's verdict is RED with
the expected dominant failure code; 1 on any wrong verdict; 2 on a REFUSED
run (prereg or capture-contract violation). verify_pipeline_receipt
re-checks every case's receipt chain from disk as defense in depth.
"""
import json
import os
import sys

import numpy as np

CARD = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PARENT = os.path.dirname(CARD)
if TEMPLATE_PARENT not in sys.path:
    sys.path.insert(0, TEMPLATE_PARENT)

from capture_gate import pipeline, view_spec  # noqa: E402

sys.path.insert(0, CARD)
import render_x05_card  # noqa: E402

CARD_ID = "MAT2-X05"

N_PAIRS = 10
FRAME_COUNT = 24
CLEAN_COUNT = 21


class FrameStore:
    """Lazy committed-frame store: loads one pair npy at a time from the
    sealed run's frames artifacts (never a second render)."""

    def __init__(self, out_dir):
        self.out_dir = out_dir
        self._cache_key = None
        self._cache = None

    def _pair_frames(self, key):
        if self._cache_key != key:
            path = os.path.join(self.out_dir, "frames_%s.npy" % key)
            self._cache = np.load(path)
            self._cache_key = key
        return self._cache

    def frame(self, key, render_index):
        return np.ascontiguousarray(
            self._pair_frames(key)[render_index])


def view_class_of(meta):
    return "x05_diag" if meta["diagnostic"] else "x05_clean"


def pair_keys():
    out = []
    for n in range(1, N_PAIRS + 1):
        cls = "BRAKE-SHORT" if n % 2 == 1 else "BRAKE-LONG"
        out.append("P%02d_%s" % (n, cls))
    return out


def run_cases(out_root, ctx):
    """Run every declared case through the real pipeline; return summary.

    ``ctx`` carries: out_dir (the sealed run's outputs dir holding the
    frames artifacts) and template_manifest_sha256.
    """
    out_dir = ctx["out_dir"]
    store = FrameStore(str(out_dir))
    frames_by_id = {}

    class _Lazy:
        def __getitem__(self, frame_id):
            key, _, rest = frame_id.partition("@")
            idx = int(rest.split("|")[1])
            return store.frame(key, idx)

    spec_path = os.path.join(CARD, "view_spec.json")
    with open(spec_path, "rb") as handle:
        spec = json.loads(handle.read().decode("utf-8"))
    problems = view_spec.validate_spec(spec)
    if problems:
        return {"schema": "chimera.x05_capture_gate_summary.v1",
                "card_id": CARD_ID, "verdict": "REFUSED",
                "refusal": "view_spec_invalid:" + ";".join(problems)}
    frames_by_id = _Lazy()
    render_fn = render_x05_card.make_renderer(frames_by_id, spec)

    summary = {
        "schema": "chimera.x05_capture_gate_summary.v1",
        "card_id": CARD_ID,
        "template_manifest_sha256": ctx.get("template_manifest_sha256"),
        "view_spec_prereg_sha256": view_spec.spec_prereg_sha256(spec),
        "cases": {},
        "production_frames_total": 0,
        "all_production_green": True,
        "all_defects_rejected": True,
    }
    exit_code = 0

    # ---- production cases: one per arm per pair (20 cases x 24 frames)
    for key in pair_keys():
        meta_path = os.path.join(out_dir, "frames_meta_%s.json" % key)
        with open(meta_path, "rb") as handle:
            meta = json.loads(handle.read().decode("utf-8"))
        for arm in ("A", "B"):
            case_id = "presentation_frames_%s_%s" % (key, arm)
            members = sorted(meta[arm], key=lambda m: m["render_index"])
            require_count = len(members) == FRAME_COUNT
            if not require_count:
                return {"schema": "chimera.x05_capture_gate_summary.v1",
                        "card_id": CARD_ID, "verdict": "REFUSED",
                        "refusal": "case_frame_count:" + case_id}
            frames_plan = []
            for m in members:
                view_class = view_class_of(m)
                frames_plan.append({
                    "frame_id": "%s_%s@%s|%d" % (key, arm, m["frame_id"],
                                                 m["render_index"]),
                    "view_class": view_class,
                    "defect": None})
            out_case = os.path.join(out_root, "cases", case_id)
            receipt, rc = pipeline.run_pipeline(
                CARD, out_case, CARD_ID, case_id, render_fn, frames_plan)
            verify = pipeline.verify_pipeline_receipt(out_case)
            green = receipt.get("verdict") == "GREEN" and not verify
            summary["cases"][case_id] = {
                "kind": "PRODUCTION", "verdict": receipt.get("verdict"),
                "frames_total": receipt.get("gate", {}).get("frames_total"),
                "frames_green": receipt.get("gate", {}).get("frames_green"),
                "verify_problems": verify, "exit_code": rc,
                "x05_projected_bbox_law":
                    "executed per frame in the sealed verification battery "
                    "(presentation_receipt landmark facts); the template "
                    "gate's stage-1 owns the palette co-location; no fork"}
            summary["production_frames_total"] += int(
                receipt.get("gate", {}).get("frames_total") or 0)
            if rc != 0 or not green:
                summary["all_production_green"] = False
                exit_code = exit_code or 1

    # ---- defect cases (P01 control-arm frames)
    key = pair_keys()[0]
    meta_path = os.path.join(out_dir, "frames_meta_%s.json" % key)
    with open(meta_path, "rb") as handle:
        meta = json.loads(handle.read().decode("utf-8"))
    clean = sorted((m for m in meta["B"] if not m["diagnostic"]),
                   key=lambda m: m["render_index"])
    diag = sorted((m for m in meta["B"] if m["diagnostic"]),
                  key=lambda m: m["render_index"])
    clean_fid = "%s_B@%s|%d" % (key, clean[0]["frame_id"],
                                clean[0]["render_index"])
    defect_cases = [
        ("defect_instrument_erased_but_claimed", clean_fid, "x05_clean",
         render_x05_card.INSTRUMENT_ERASED_BUT_CLAIMED,
         "COLOCATION_MISMATCH"),
        ("defect_landmark_recolor_shared", clean_fid, "x05_clean",
         render_x05_card.LANDMARK_RECOLOR_SHARED, "COLOCATION_MISMATCH"),
        ("defect_body_absent", clean_fid, "x05_clean",
         render_x05_card.BODY_ABSENT, "SUBJECT_MASK_BELOW_FLOOR"),
        # the leak paints the x04_event_strip (L2) layer rect — chosen
        # because it contains NO landmark footprint (the L1 rect covers
        # rock_far, whose floor failure would tie-break the dominant code
        # away from the leak's essence: the clean-law violation)
        ("defect_clean_diagnostic_leak", clean_fid, "x05_clean",
         render_x05_card.CLEAN_DIAGNOSTIC_LEAK, "UNDECLARED_MASK_ID"),
    ]
    for case_id, frame_id, view_class, defect, expected in defect_cases:
        frames_plan = [{"frame_id": frame_id, "view_class": view_class,
                        "defect": defect}]
        out_case = os.path.join(out_root, "cases", case_id)
        receipt, rc = pipeline.run_pipeline(
            CARD, out_case, CARD_ID, case_id, render_fn, frames_plan)
        verify = pipeline.verify_pipeline_receipt(out_case)
        dominant = None
        if receipt.get("verdict") == "RED":
            dominant = _dominant_code(out_case)
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
