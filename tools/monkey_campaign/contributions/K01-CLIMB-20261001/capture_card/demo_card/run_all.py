#!/usr/bin/env python
"""Demo card run_all: the NORMAL pipeline entry (prereg -> capture -> GATE ->
receipts -> review export).

The gate call is part of this flow, not an optional add-on: run_all has no
code path that emits a pass without pipeline.run_pipeline having run the
two-stage gate (stage-0 palette blank-check + stage-1 mask co-location) over
every captured frame. A capture plan whose frames fail the gate REJECTS the
run (exit 1); a prereg or capture-contract violation REFUSES the run
pre-render (exit 2); only a fully GREEN gated pipeline exits 0.

Usage:
    python -B run_all.py --case healthy_clean
    python -B run_all.py --all --out-dir OUT

Case table (card-owned; defect injection is fixture-only, for proving
rejection through the real pipeline path):

    healthy_clean                        clean       -> EXPECT PASS
    healthy_close                        close       -> EXPECT PASS
    declared_occlusion                   obstructed  -> EXPECT PASS via
                                                        preregistered
                                                        occlusion exception
    defect_wrong_body_color_share        clean       -> EXPECT REJECT
    defect_shared_color_inflation_absent clean       -> EXPECT REJECT
    defect_subject_absent                clean       -> EXPECT REJECT
    defect_undeclared_occlusion          clean       -> EXPECT REJECT
"""

import argparse
import os
import sys

TEMPLATE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if TEMPLATE_ROOT not in sys.path:
    sys.path.insert(0, TEMPLATE_ROOT)

from capture_gate import pipeline  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render_card  # noqa: E402

DEFECT_WRONG_BODY_COLOR_SHARE = "WRONG_BODY_COLOR_SHARE"
DEFECT_SHARED_COLOR_INFLATION_ABSENT = "SHARED_COLOR_INFLATION_ABSENT"
DEFECT_SUBJECT_ABSENT = "SUBJECT_ABSENT"
DEFECT_UNDECLARED_OCCLUSION = "UNDECLARED_OCCLUSION"

# case_id, view_class, defect, expectation
CASES = [
    ("healthy_clean", "clean", None, "EXPECT_PASS"),
    ("healthy_close", "close", None, "EXPECT_PASS"),
    ("declared_occlusion", "obstructed", None, "EXPECT_PASS_VIA_EXCEPTION"),
    ("defect_wrong_body_color_share", "clean",
     DEFECT_WRONG_BODY_COLOR_SHARE, "EXPECT_REJECT"),
    ("defect_shared_color_inflation_absent", "clean",
     DEFECT_SHARED_COLOR_INFLATION_ABSENT, "EXPECT_REJECT"),
    ("defect_subject_absent", "clean", DEFECT_SUBJECT_ABSENT, "EXPECT_REJECT"),
    ("defect_undeclared_occlusion", "clean",
     DEFECT_UNDECLARED_OCCLUSION, "EXPECT_REJECT"),
]

CASES_BY_ID = {case[0]: case for case in CASES}


def frames_plan_for(case_id):
    """One single-frame capture plan per case (one pipeline run per case)."""
    _, view_class, defect, _ = CASES_BY_ID[case_id]
    return [{"frame_id": case_id, "view_class": view_class, "defect": defect}]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--case", choices=sorted(CASES_BY_ID))
    group.add_argument("--all", action="store_true")
    parser.add_argument("--out-dir", default=None,
                        help="output root (default $CHIMERA_OUTPUT_DIR or ./outputs)")
    args = parser.parse_args(argv)

    out_root = args.out_dir or os.environ.get("CHIMERA_OUTPUT_DIR") or "outputs"
    selected = [case[0] for case in CASES] if args.all else [args.case]

    any_failure = False
    for case_id in selected:
        out_dir = os.path.join(out_root, "cases", case_id)
        receipt, exit_code = pipeline.run_pipeline(
            render_card.CARD_ROOT, out_dir, render_card.CARD_ID,
            case_id, render_card.render, frames_plan_for(case_id))
        verdict = receipt["verdict"]
        if verdict == "REFUSED":
            print("REFUSED case=%s reason=%s" % (case_id, receipt["refusal"]))
            return 2
        failures = []
        exceptions = 0
        gate_path = os.path.join(out_dir, pipeline.GATE_RECEIPT_FILENAME)
        if os.path.isfile(gate_path):
            with open(gate_path, "rb") as handle:
                import json
                gate = json.loads(handle.read().decode("utf-8"))
            for row in gate["frames"]:
                failures.extend(
                    "%s:%s" % (f["code"], f["object_id"])
                    for f in row["stage1"]["failures"])
                failures.extend(
                    "%s:%s" % (f["code"], "*")
                    for f in row["stage0"]["failures"])
            exceptions = len(gate["exception_rows"])
        if exit_code == 0:
            print("PASSED case=%s verdict=%s exceptions=%d gate_receipt=%s"
                  % (case_id, verdict, exceptions,
                     receipt["gate"]["receipt_sha256"]))
        else:
            any_failure = True
            print("REJECTED case=%s verdict=%s failures=%s gate_receipt=%s"
                  % (case_id, verdict, sorted(set(failures)),
                     receipt["gate"]["receipt_sha256"]))
    return 1 if any_failure else 0


if __name__ == "__main__":
    sys.exit(main())
