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
  "tests":     {"passed": 4, "failed": 0, "skipped": 0, "ran_in_editor": true},
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
    total = passed + failed
    if total == 0:
        note = ("no tests executed"
                + (f" ({skipped} skipped — headless)" if skipped else " — no acceptance tests exist"))
        return 0.0, note
    pts = (passed / total) * W_CORRECTNESS
    note = f"{passed}/{total} tests passed"
    if not ran:
        pts = min(pts, HEADLESS_CORRECTNESS_CAP)
        note += f" (not run in-editor: capped at {HEADLESS_CORRECTNESS_CAP})"
    return pts, note


def _score_stability(t: dict) -> tuple[float, str]:
    pts, notes = 0.0, []
    if t.get("crash_free") is True:
        pts += 15
        notes.append("crash-free")
    else:
        notes.append("crash evidence or unknown (0/15)")
    fps, target = t.get("fps"), t.get("target_fps", 60)
    if fps is not None:
        if float(fps) >= float(target):
            pts += 5
            notes.append(f"fps {fps} >= {target}")
        else:
            notes.append(f"fps {fps} < target {target} (0/5)")
    else:
        notes.append("fps unmeasured (0/5)")
    if t.get("unbounded_growth") is False:
        pts += 5
        notes.append("no unbounded growth")
    else:
        notes.append("growth unmeasured or unbounded (0/5)")
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
