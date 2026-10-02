"""K02 card run_all: the NORMAL pipeline entry (prereg -> capture -> GATE ->
receipts -> review export), replacing the demo case table per the template
recipe. The gate call is part of the flow: no case can emit a pass without
pipeline.run_pipeline having run the two-stage gate over every captured
frame.

Case table (card-owned, declared before capture). Production cases carry
recorded run state captured from the K02 battery in the same process; defect
cases are fixture-only injections proving the gate REJECTS the four planted
defect classes through THIS card's spec (K02 prereg section 9 declared
views; the release case carries the fall/ground-contact frame pair):

    hold_w20                     normal/detail/alternate x c/d -> EXPECT PASS
    hold_w100                    (same six frames)             -> EXPECT PASS
    hold_w300                    (same six frames)             -> EXPECT PASS
    hold_mu041_slip              (same six frames)             -> EXPECT PASS
    release_to_ground            normal/alternate/fall x c/d   -> EXPECT PASS
    defect_wrong_pad_color_share alternate_clean               -> EXPECT REJECT
    defect_shared_color_inflation_absent normal_clean          -> EXPECT REJECT
    defect_subject_absent        normal_clean                  -> EXPECT REJECT
    defect_undeclared_occlusion  normal_clean                  -> EXPECT REJECT

Card exit law (documented, enforced here): 0 iff every production case's
pipeline verdict is GREEN AND every defect case's verdict is RED with the
expected dominant failure code; 1 on any wrong verdict; 2 on a REFUSED run
(prereg or capture-contract violation). verify_pipeline_receipt re-checks
every case's receipt chain from disk as defense in depth.
"""
import hashlib
import json
import os
import sys

CARD = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PARENT = os.path.dirname(CARD)
if TEMPLATE_PARENT not in sys.path:
    sys.path.insert(0, TEMPLATE_PARENT)

from capture_gate import pipeline  # noqa: E402

sys.path.insert(0, CARD)
import render_k02  # noqa: E402

CARD_ID = "K02-STATIC-HOLD-20261002"

# production cases: (case_id, [(frame_id, view_class)], state_key)
FALL_FRAMES = [("fall_clean", "fall_clean"), ("fall_diag", "fall_diag")]


def _case_frames(suffix, families):
    pairs = []
    for fam in families:
        pairs.append((fam + "_clean" + suffix, fam + "_clean"))
        pairs.append((fam + "_diag" + suffix, fam + "_diag"))
    return pairs


PRODUCTION_CASES = [
    ("hold_w20", _case_frames("__hold_w20", ("normal", "detail",
                                             "alternate")), "hold_w20"),
    ("hold_w100", _case_frames("__hold_w100", ("normal", "detail",
                                               "alternate")), "hold_w100"),
    ("hold_w300", _case_frames("__hold_w300", ("normal", "detail",
                                               "alternate")), "hold_w300"),
    ("hold_mu041_slip",
     _case_frames("__hold_mu041_slip", ("normal", "detail", "alternate")),
     "hold_mu041"),
    ("release_to_ground",
     _case_frames("__release_to_ground", ("normal", "alternate"))
     + [(fid + "__release_to_ground", vc)
        for fid, vc in FALL_FRAMES],
     "release_to_ground"),
]

DEFECT_WRONG_BODY_COLOR_SHARE = "WRONG_BODY_COLOR_SHARE"
DEFECT_SHARED_COLOR_INFLATION_ABSENT = "SHARED_COLOR_INFLATION_ABSENT"
DEFECT_SUBJECT_ABSENT = "SUBJECT_ABSENT"
DEFECT_UNDECLARED_OCCLUSION = "UNDECLARED_OCCLUSION"

# defect cases: (case_id, view_class, defect, expected dominant code)
# wrong_pad_color_share fires in the alternate view, where pad_1 is the
# visible subject (in the normal view pad_1 is declared occluded, so a
# shared-color defect on it cannot bite there).
DEFECT_CASES = [
    ("defect_wrong_pad_color_share", "alternate_clean",
     DEFECT_WRONG_BODY_COLOR_SHARE, "COLOCATION_MISMATCH"),
    ("defect_shared_color_inflation_absent", "normal_clean",
     DEFECT_SHARED_COLOR_INFLATION_ABSENT, "SUBJECT_MASK_BELOW_FLOOR"),
    ("defect_subject_absent", "normal_clean",
     DEFECT_SUBJECT_ABSENT, "SUBJECT_MASK_BELOW_FLOOR"),
    ("defect_undeclared_occlusion", "normal_clean",
     DEFECT_UNDECLARED_OCCLUSION, "OCCLUDED_SUBJECT_VISIBLE"),
]


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def run_cases(out_root, states):
    """Run every declared case through the real pipeline; return summary."""
    summary = {
        "schema": "chimera.k02_capture_summary.v1",
        "card_id": CARD_ID,
        "cases": {}, "all_production_green": True,
        "all_defects_rejected": True,
    }
    plan = [(cid, frames, states[key], None, "PRODUCTION")
            for cid, frames, key in PRODUCTION_CASES]
    plan += [(cid, [(cid + "__1", vc)],
              dict(states["hold_w20"], defect=defect), defect, "DEFECT")
             for cid, vc, defect, _exp in DEFECT_CASES]
    for case_id, frames_plan, state, defect, kind in plan:
        out_dir = os.path.join(out_root, "cases", case_id)
        render = render_k02.make_renderer(state, render_k02.load_card_spec())
        entry_frames = [{"frame_id": fid, "view_class": vc, "defect": defect}
                        for fid, vc in frames_plan]
        receipt, exit_code = pipeline.run_pipeline(
            CARD, out_dir, CARD_ID, case_id, render, entry_frames)
        verdict = receipt["verdict"]
        problems = []
        if verdict != "REFUSED":
            problems = pipeline.verify_pipeline_receipt(out_dir)
        gate_path = os.path.join(out_dir, pipeline.GATE_RECEIPT_FILENAME)
        codes = []
        exceptions = 0
        if os.path.isfile(gate_path):
            with open(gate_path, "rb") as handle:
                gate = json.loads(handle.read().decode("utf-8"))
            for row in gate["frames"]:
                codes.extend(f["code"] for f in row["stage1"]["failures"])
                codes.extend(f["code"] for f in row["stage0"]["failures"])
            exceptions = len(gate["exception_rows"])
        row = {
            "kind": kind, "verdict": verdict, "pipeline_exit_code": exit_code,
            "failure_codes": sorted(set(codes)), "exception_rows": exceptions,
            "receipt_problems": problems,
            "state_sha256": hashlib.sha256(json.dumps(
                state, sort_keys=True, separators=(",", ":"),
                ensure_ascii=True).encode("utf-8")).hexdigest(),
        }
        for name, fname in (("pipeline_receipt", pipeline.PIPELINE_RECEIPT_FILENAME),
                            ("gate_receipt", pipeline.GATE_RECEIPT_FILENAME),
                            ("capture_manifest", "capture_manifest.json")):
            path = os.path.join(out_dir, fname)
            row[name + "_sha256"] = sha256_file(path) if \
                os.path.isfile(path) else None
        review_dir = os.path.join(out_dir, pipeline.REVIEW_DIRNAME)
        review_files = []
        if os.path.isdir(review_dir):
            for name in sorted(os.listdir(review_dir)):
                path = os.path.join(review_dir, name)
                if os.path.isfile(path):
                    review_files.append([name, sha256_file(path)])
        row["review_files"] = review_files
        summary["cases"][case_id] = row
        if kind == "PRODUCTION":
            if verdict != "GREEN" or problems or exit_code != 0:
                summary["all_production_green"] = False
        else:
            expected = dict((cid, exp)
                            for cid, _vc, _d, exp in DEFECT_CASES)[case_id]
            row["expected_dominant_code"] = expected
            ok = (verdict == "RED" and not problems
                  and expected in row["failure_codes"])
            row["rejection_as_expected"] = ok
            if not ok:
                summary["all_defects_rejected"] = False
    summary["exit_law_verdict"] = (
        "PASS" if (summary["all_production_green"]
                   and summary["all_defects_rejected"]) else "FAIL")
    return summary


def main(argv=None):
    """Standalone calibration mode: render the declared cases from a trace
    states JSON (written by the battery) instead of live run state."""
    import argparse
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--states", required=True)
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args(argv)
    out_root = args.out_dir or os.environ.get("CHIMERA_OUTPUT_DIR") or "outputs"
    with open(args.states, "rb") as handle:
        states = json.loads(handle.read().decode("utf-8"))
    summary = run_cases(out_root, states)
    print(json.dumps({k: v for k, v in summary.items() if k != "cases"},
                     indent=2, sort_keys=True))
    return 0 if summary["exit_law_verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
