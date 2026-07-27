"""Result Grader — grades the MEASURED game result against docs/RESULT_GRADING_RUBRIC.md.

Zero model dependency: no LM Studio, no local LLM. The driving agent supplies evidence
(test results, telemetry, checklist verdicts, spec-fidelity fraction); this module turns
it into the rubric score, letter grade, and a study guide for C/F retries, and records it
through the existing ProfessorGrade/GPA machinery.

Usage (module):
    from core.result_grader import grade_feature
    result = grade_feature("System_SaveLoad", evidence={...}, record=True)

Usage (CLI):
    python -m core.result_grader --feature System_SaveLoad --evidence evidence.json [--no-record]

Evidence schema (all keys optional — missing evidence scores zero, never assumed):
{
  "tests":     {"passed": 4, "failed": 0, "skipped": 0, "ran_in_editor": true,
                "criteria_total": 4},
                # criteria_total = how many acceptance criteria this feature DECLARES.
                # REQUIRED for any correctness points: pass rate is multiplied by
                # coverage (passed+failed)/criteria_total, so 1 test against 4 declared
                # criteria earns 10/40, not 40/40. Omitting it scores correctness ZERO —
                # it used to score FULL, which is how "missing evidence scores zero,
                # never assumed" came to mean its opposite. It was also undocumented
                # here, so the only agents it penalised were the honest ones.
  "telemetry": {"crash_free": true, "fps": 62.0, "target_fps": 60, "unbounded_growth": false},
  "checklist": {"feedback": true, "consistency": true, "meaningful_parameters": true,
                 "fail_safety": true, "balance_sanity": true},
  "spec_fidelity": 0.93   # fraction of DSL/researched parameters verified in the built result
}
"""
import argparse
import json
import sys
from pathlib import Path

try:
    from core.graphify_interface import record_grade
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from graphify_interface import record_grade

# Rubric weights (docs/RESULT_GRADING_RUBRIC.md)
W_CORRECTNESS = 40
W_STABILITY = 25
W_CHECKLIST = 20
W_FIDELITY = 15
HEADLESS_CORRECTNESS_CAP = 20  # tests that never ran cannot earn full correctness

CHECKLIST_ITEMS = ("feedback", "consistency", "meaningful_parameters",
                   "fail_safety", "balance_sanity")  # 4 pts each


def _score_correctness(tests: dict) -> tuple[float, str]:
    passed = int(tests.get("passed", 0))
    failed = int(tests.get("failed", 0))
    skipped = int(tests.get("skipped", 0))
    ran = bool(tests.get("ran_in_editor", False))
    # criteria_total: how many acceptance criteria the feature DEFINES. Pass rate is
    # multiplied by coverage so 1/1 passing of 4 declared criteria earns 10/40, not
    # 40/40 — thin coverage can no longer masquerade as correctness.
    #
    # IT DID EXACTLY THAT UNTIL 2026-07-16. This read
    #     criteria_total = max(int(tests.get("criteria_total", 0)), passed + failed)
    # so OMITTING the key gave max(0, total) == total, coverage == 1.0, and FULL marks:
    #     grade_feature("X", {"tests": {"passed": 1, "failed": 0, "ran_in_editor": True}})
    #         -> correctness 40.0/40, note "coverage 1/1 declared criteria"
    # for a feature that declared no criteria at all. The key was also absent from the
    # documented schema above, so the anti-masquerade engaged only when an agent
    # VOLUNTEERED a number against its own interest — while the docstring promised
    # "missing evidence scores zero, never assumed." It assumed, and it assumed in the
    # agent's favour. This is H-13's exact failure mode, defeated by its own default.
    #
    # Undeclared criteria are now UNKNOWN coverage, and unknown is not full. You cannot
    # claim correctness without first saying what correct means: no reference, no verdict.
    total = passed + failed
    declared = int(tests.get("criteria_total", 0))
    if total == 0:
        note = ("no tests executed"
                + (f" ({skipped} skipped — headless)" if skipped else " — no acceptance tests exist"))
        return 0.0, note
    if declared <= 0:
        return 0.0, (f"{passed}/{total} tests passed but the feature DECLARED NO acceptance "
                     f"criteria (tests.criteria_total) — coverage is unknown, and unknown "
                     f"scores zero rather than full. Declare what correct means, then test it.")
    criteria_total = max(declared, total)
    coverage = min(1.0, total / criteria_total)
    pts = (passed / total) * coverage * W_CORRECTNESS
    note = f"{passed}/{total} tests passed; coverage {total}/{criteria_total} declared criteria"
    if not ran:
        pts = min(pts, HEADLESS_CORRECTNESS_CAP)
        note += f" (not run in-editor: capped at {HEADLESS_CORRECTNESS_CAP})"
    return pts, note


def _score_stability(t: dict) -> tuple[float, str]:
    pts, notes = 0.0, []
    if t.get("crash_free") is True:
        pts += 12
        notes.append("crash-free")
    else:
        notes.append("crash evidence or unknown (0/12)")
    # fps is ONE INSTANTANEOUS SAMPLE — a coin toss, and this used to be the whole of
    # what "stability" meant here. Meanwhile telemetry_probe.probe_frame_time_stability
    # is the ONLY function in the instrument layer that takes MULTIPLE samples and
    # reports variance and worst-case, and `frame_time_stable` appeared NOWHERE in this
    # file: the honest measurement was computed, written to the evidence JSON, and
    # DISCARDED, while the coin toss was graded. The budget (12+5+4+4) exactly filled
    # W_STABILITY=25, so there was no slot left for it — the arithmetic itself was the
    # reason the good measure could never count. A feature with MEASURED frame
    # instability scored a PERFECT 25/25 stability grade.
    #
    # Now fps and stability SHARE the 5: an instantaneous reading is worth 2, and the
    # multi-sample verdict is worth 3 — the variance measurement outranks the snapshot,
    # because "one rollout is a coin toss" is this studio's own doctrine and an fps
    # reading is one rollout.
    fps, target = t.get("fps"), t.get("target_fps", 60)
    if fps is not None:
        if float(fps) >= float(target):
            pts += 2
            notes.append(f"fps {fps} >= {target} (2/2, one sample)")
        else:
            notes.append(f"fps {fps} < target {target} (0/2)")
    else:
        notes.append("fps unmeasured (0/2)")
    stable = t.get("frame_time_stable")
    if stable is True:
        pts += 3
        notes.append("frame time stable over soak (3/3, multi-sample)")
    elif stable is False:
        notes.append("frame time UNSTABLE over soak — measured hitches (0/3)")
    else:
        notes.append("frame-time stability unmeasured (0/3)")
    if t.get("unbounded_growth") is False:
        pts += 4
        notes.append("actor growth bounded")
    else:
        notes.append("actor growth unmeasured or unbounded (0/4)")
    if t.get("memory_bounded") is True:
        pts += 4
        notes.append("memory growth bounded (<10%)")
    else:
        notes.append("memory growth unmeasured or unbounded (0/4)")
    return pts, "; ".join(notes)


def _score_checklist(c: dict) -> tuple[float, str]:
    per_item = W_CHECKLIST / len(CHECKLIST_ITEMS)
    earned = [item for item in CHECKLIST_ITEMS if c.get(item) is True]
    missed = [item for item in CHECKLIST_ITEMS if c.get(item) is not True]
    note = f"met: {', '.join(earned) or 'none'}"
    if missed:
        note += f" | missed: {', '.join(missed)}"
    return per_item * len(earned), note


def _score_fidelity(fraction) -> tuple[float, str]:
    try:
        f = max(0.0, min(1.0, float(fraction)))
    except (TypeError, ValueError):
        return 0.0, "spec fidelity unmeasured"
    return f * W_FIDELITY, f"{int(f * 100)}% of spec parameters verified in the built result"


def _letter(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    return "F"


def grade_feature(feature: str, evidence: dict, record: bool = True) -> dict:
    """Score evidence against the rubric. Returns {feature, score, grade, breakdown,
    reasoning, study_guide}. Missing evidence scores zero — measurement, not faith."""
    evidence = evidence or {}
    parts = {
        "correctness": _score_correctness(evidence.get("tests", {}) or {}),
        "stability": _score_stability(evidence.get("telemetry", {}) or {}),
        "design_checklist": _score_checklist(evidence.get("checklist", {}) or {}),
        "spec_fidelity": _score_fidelity(evidence.get("spec_fidelity")),
    }
    maxima = {"correctness": W_CORRECTNESS, "stability": W_STABILITY,
              "design_checklist": W_CHECKLIST, "spec_fidelity": W_FIDELITY}

    score = round(sum(p[0] for p in parts.values()), 1)
    letter = _letter(score)
    breakdown = {k: {"points": round(v[0], 1), "max": maxima[k], "note": v[1]}
                 for k, v in parts.items()}

    # Study guide: the lowest-yield categories, quoted for the retry research prompt
    by_deficit = sorted(parts.items(), key=lambda kv: kv[1][0] / maxima[kv[0]])
    study_guide = [f"{name} ({parts[name][0]:.0f}/{maxima[name]}): {parts[name][1]}"
                   for name, _ in by_deficit[:2]] if letter in ("C", "F") else []

    reasoning = " | ".join(f"{k} {v['points']}/{v['max']}: {v['note']}"
                           for k, v in breakdown.items())
    result = {"feature": feature, "score": score, "grade": letter,
              "breakdown": breakdown, "reasoning": reasoning, "study_guide": study_guide}

    if record:
        result["grade_node"] = record_grade(feature, letter, f"[result-grader {score}/100] {reasoning}")
    return result


def main():
    parser = argparse.ArgumentParser(description="Grade a feature's MEASURED result (rubric-based, no LM)")
    parser.add_argument("--feature", required=True)
    parser.add_argument("--evidence", help="Path to evidence JSON (see module docstring)")
    parser.add_argument("--no-record", action="store_true", help="Score only; do not write a ProfessorGrade node")
    args = parser.parse_args()

    evidence = {}
    if args.evidence:
        evidence = json.loads(Path(args.evidence).read_text(encoding="utf-8"))

    result = grade_feature(args.feature, evidence, record=not args.no_record)
    print(json.dumps(result, indent=2))
    if result["grade"] in ("C", "F"):
        print("\nSTUDY GUIDE (feed into the retry research prompt):", file=sys.stderr)
        for line in result["study_guide"]:
            print(f"  - {line}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
