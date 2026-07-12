"""The Critic — Games critic / benchmark analyst organ (DREAM_ROSTER.md #13, Tier 2).

ADVISORY ONLY — LM-generated estimate, does not gate the pipeline, does not substitute
for human observation. Nothing in result_grader.py / ProfessorGPA measures comparative
enjoyment; they measure pure technical correctness (test pass rate, stability, design
checklist, spec fidelity). The Critic answers a different question: "how does this feel
next to the AAA/notable titles a player would actually compare it to?" — expressed as
`overall_percentage`, an estimated player-enjoyment PERCENTILE relative to a named
benchmark set, NOT a probability of commercial success and NOT a re-derivation of the
technical grade.

Charter: given a feature, pull everything already recorded for it (latest record_grade
letter + per-category reasoning, FeatureUpdate parameters/evidence, SurpriseMoments,
Observation verdicts, ResearchDiscovery acceptance criteria) and hand that REAL evidence
to an LM Studio call that must (a) pick 2-4 genre-appropriate reference titles from the
project's benchmark pool (Elite Dangerous, No Man's Sky, Star Citizen, EVE Online,
Subnautica — a space-trader/exploration game with on-foot survival elements) and (b) score
seven axes: the project's own five design-standard checklist axes (Feedback, Consistency,
Meaningful Parameters, Fail-safety, Balance Sanity — docs/RESULT_GRADING_RUBRIC.md,
rescaled 0-20) plus two critic-only axes (Production Polish, Moment-to-Moment Feel). The
LM is grounded in recorded evidence, never left to free-associate.

LM Studio calling convention follows core/spiral_forks.py: HTTP POST to
http://localhost:1234/v1/chat/completions, model qwen3.6-35b-a3b-mtp@iq2_m, via
urllib.request. Per heuristic H-3 ("An LM response containing its own reasoning dump is a
RETRY with a larger token budget, never a verdict — schema-validate before consuming"):
both `content` and `reasoning_content` are regex-scanned for a JSON blob, the result is
schema-validated (required keys + types), and a malformed/invalid response triggers a
retry with a larger max_tokens budget — never silently accepted.

Wiring (at most four touchpoints, per DREAM_ROSTER.md's casting rule): one preflight.py
line surfacing the latest judgment; one Tier-2 DREAM_ROSTER.md entry; that's it for this
first hire — no dream_loop/candidates wiring yet.

Usage:
    python -m core.critic --feature Ground_Sand_Particles
    python -m core.critic --feature Ground_Sand_Particles --dry-run
    python -m core.critic --list-graded
"""
import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

try:
    from core.graphify_interface import (
        graphify_query, load_dna_graph, record_critic_judgment, CRITIC_ADVISORY_DISCLAIMER
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from graphify_interface import (
        graphify_query, load_dna_graph, record_critic_judgment, CRITIC_ADVISORY_DISCLAIMER
    )

CHIMERA_ROOT = Path(__file__).parent.parent

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
try:
    from core.lm_gateway import LM_MODEL as LM_STUDIO_MODEL   # single source of truth
except Exception:
    LM_STUDIO_MODEL = "qwen-agentworld-35b-a3b-nvfp4"

DISCLAIMER = CRITIC_ADVISORY_DISCLAIMER

# The project's own five design-standard axes (docs/RESULT_GRADING_RUBRIC.md checklist,
# 4pts/20 there) rescaled to a 0-20 full-mark axis here, plus two critic-only axes.
AXES = ["feedback", "consistency", "meaningful_parameters", "fail_safety",
        "balance_sanity", "production_polish", "moment_to_moment_feel"]

BENCHMARK_POOL = ["Elite Dangerous", "No Man's Sky", "Star Citizen", "EVE Online", "Subnautica"]

JUDGMENT_SCHEMA_HINT = {
    "overall_percentage": "<number 0-100: estimated player-enjoyment PERCENTILE relative to "
                          "the named benchmark set, NOT a probability of commercial success>",
    "benchmark_titles": [{"title": "<name>", "reason": "<one line: why this title is the "
                          "right comparison for THIS feature>"}],
    "axis_scores": {a: "<number 0-20>" for a in AXES},
    "named_comparisons": ["<concrete sentence citing a specific benchmark title by name>"],
    "rationale": "<short paragraph>",
}


# ---------------------------------------------------------------------------
# Evidence gathering — ground the LM's judgment in what was actually built and
# measured, never let it free-associate about a feature it has no facts on.
# ---------------------------------------------------------------------------

def gather_evidence(feature: str) -> dict:
    """Pull everything already recorded for `feature` from the DNA graph.

    Uses graphify_query('feature', ...) for FeatureUpdate history (same helper used in
    DEMO_ARCHITECTURE.md Phase 1 item 1), then reads ProfessorGrade / SurpriseMoment /
    Observation / ResearchDiscovery nodes directly (graphify_query has no dedicated
    lookup for those types)."""
    dna = load_dna_graph()
    nodes = dna.get("nodes", [])

    raw_updates = graphify_query("feature", feature) or []
    feature_updates = sorted(
        [n for n in raw_updates if isinstance(n, dict) and n.get("feature_name") == feature],
        key=lambda n: n.get("timestamp", ""))

    grades = sorted(
        [n for n in nodes if n.get("type") == "ProfessorGrade" and n.get("feature") == feature],
        key=lambda n: n.get("timestamp", ""))
    surprises = sorted(
        [n for n in nodes if n.get("type") == "SurpriseMoment" and feature.lower() in
         (str(n.get("context", "")) + " " + str(n.get("reality", ""))).lower()],
        key=lambda n: n.get("timestamp", ""))
    observations = sorted(
        [n for n in nodes if n.get("type") == "Observation" and n.get("feature_name") == feature],
        key=lambda n: n.get("timestamp", ""))
    research = sorted(
        [n for n in nodes if n.get("type") == "ResearchDiscovery" and n.get("feature") == feature],
        key=lambda n: n.get("timestamp", ""))

    latest_update = feature_updates[-1] if feature_updates else None
    latest_grade = grades[-1] if grades else None
    latest_observation = observations[-1] if observations else None
    latest_research = research[-1] if research else None

    return {
        "feature": feature,
        "has_evidence": bool(latest_update or latest_grade),
        "latest_status": latest_update.get("status") if latest_update else None,
        "latest_update_parameters": latest_update.get("parameters") if latest_update else {},
        "latest_grade_letter": latest_grade.get("grade") if latest_grade else None,
        "latest_grade_reasoning": latest_grade.get("reasoning") if latest_grade else "",
        "surprises": [{"context": s.get("context", ""), "reality": s.get("reality", "")}
                     for s in surprises[-4:]],
        "latest_observation": ({"verdict": latest_observation.get("verdict"),
                                "notes": latest_observation.get("notes")}
                               if latest_observation else None),
        "research_acceptance_criteria": (latest_research.get("acceptance_criteria", [])
                                         if latest_research else []),
        "feature_update_count": len(feature_updates),
    }


def list_graded_features() -> list:
    """Features with at least one ProfessorGrade recorded — cheap check for "enough
    evidence to be worth Critic judgment" (a single pass over already-loaded nodes)."""
    dna = load_dna_graph()
    nodes = dna.get("nodes", [])
    by_feature = {}
    for n in nodes:
        if n.get("type") != "ProfessorGrade":
            continue
        feat = n.get("feature")
        if not feat or feat == "unknown_feature":
            continue
        ts = n.get("timestamp", "")
        if feat not in by_feature or ts > by_feature[feat][0]:
            by_feature[feat] = (ts, n.get("grade"), n.get("score"))
    return sorted(
        [{"feature": f, "timestamp": v[0], "grade": v[1], "score": v[2]}
         for f, v in by_feature.items()],
        key=lambda d: d["timestamp"], reverse=True)


def _evidence_block(evidence: dict) -> str:
    lines = [f"- latest FeatureUpdate status: {evidence['latest_status'] or '(none recorded)'}"]
    if evidence["latest_update_parameters"]:
        lines.append(f"- latest FeatureUpdate parameters/evidence: "
                     f"{json.dumps(evidence['latest_update_parameters'], default=str)[:1500]}")
    if evidence["latest_grade_letter"]:
        lines.append(f"- latest record_grade: {evidence['latest_grade_letter']} — "
                     f"{evidence['latest_grade_reasoning']}")
    else:
        lines.append("- latest record_grade: (none recorded — no technical grade to anchor "
                     "against; judge cautiously and say so in the rationale)")
    if evidence["surprises"]:
        lines.append("- recorded SurpriseMoments (real dead-ends/corrections encountered "
                     "while building this feature):")
        for s in evidence["surprises"]:
            lines.append(f"    * expected '{s['context']}' -> reality: {s['reality']}"[:300])
    if evidence["latest_observation"]:
        lines.append(f"- latest human/attributed Observation: "
                     f"{evidence['latest_observation']['verdict']} — "
                     f"{evidence['latest_observation']['notes']}")
    if evidence["research_acceptance_criteria"]:
        lines.append(f"- declared acceptance criteria (the research exam this feature was "
                     f"built against): {evidence['research_acceptance_criteria']}")
    return "\n".join(lines)


def _build_prompt(feature: str, evidence_block: str) -> str:
    return (
        f"/no_think You are THE CRITIC, a games-critic and AAA-benchmark analyst organ "
        f"inside an autonomous UE5 space-trader/exploration game development pipeline "
        f"(Chimera). {DISCLAIMER}.\n\n"
        f"Your job: estimate `overall_percentage` = the feature's estimated PLAYER-ENJOYMENT "
        f"PERCENTILE relative to a benchmark set of real, named AAA/notable titles in the "
        f"same genre — NOT a probability of commercial success, and NOT a re-derivation of "
        f"technical correctness (that is measured elsewhere by result_grader.py and is "
        f"handed to you below as evidence; use it, don't re-score it).\n\n"
        f"FEATURE: {feature}\n\n"
        f"REAL EVIDENCE ALREADY RECORDED FOR THIS FEATURE (ground your judgment in this; do "
        f"not invent facts not supported here):\n{evidence_block}\n\n"
        f"BENCHMARK POOL (space-trader / exploration / on-foot-survival genre): "
        f"{', '.join(BENCHMARK_POOL)}.\n"
        f"Pick the 2-4 titles from this pool MOST relevant to this specific feature (e.g. a "
        f"trade-kiosk feature compares to Elite Dangerous's cockpit trade UI / EVE Online's "
        f"market; an on-foot gait/ground feature compares to Subnautica's or No Man's Sky's "
        f"walking feel). You may cite one title outside the pool ONLY if clearly more "
        f"relevant, but prefer the pool.\n\n"
        f"Score these SEVEN axes 0-20 each (the first five are the project's own "
        f"design-standard checklist from docs/RESULT_GRADING_RUBRIC.md, rescaled to a 20-pt "
        f"full-mark scale here; the last two are critic-only axes):\n"
        f"1. Feedback — every player-facing action produces an observable response\n"
        f"2. Consistency — same inputs -> same rules everywhere\n"
        f"3. Meaningful Parameters — every exposed tunable actually changes behavior\n"
        f"4. Fail-safety — invalid input degrades gracefully, never crashes\n"
        f"5. Balance Sanity — numbers land in playable, bounded ranges\n"
        f"6. Production Polish — visual/audio/animation fit-and-finish vs the benchmark "
        f"titles' shipped bar\n"
        f"7. Moment-to-Moment Feel — does the second-to-second handling/readability feel "
        f"like the benchmark titles, or like a placeholder/debug build?\n\n"
        f"named_comparisons must each cite a SPECIFIC benchmark title by name in a concrete "
        f"sentence (e.g. \"the kiosk reads as a debug bench, not Elite Dangerous's cockpit "
        f"trade panel\") — not generic praise/criticism.\n\n"
        f"Return ONLY a JSON object EXACTLY matching this schema (no prose, no markdown "
        f"fences):\n{json.dumps(JUDGMENT_SCHEMA_HINT, indent=1)}"
    )


# ---------------------------------------------------------------------------
# LM Studio call + H-3 retry-on-malformed-response
# ---------------------------------------------------------------------------

def _validate_schema(c) -> tuple:
    if not isinstance(c, dict):
        return False, "not a JSON object"
    pct = c.get("overall_percentage")
    if not isinstance(pct, (int, float)):
        return False, "overall_percentage missing/non-numeric"
    titles = c.get("benchmark_titles")
    if not isinstance(titles, list) or not (2 <= len(titles) <= 4):
        return False, "benchmark_titles must be a list of 2-4 entries"
    for t in titles:
        if not isinstance(t, dict) or not str(t.get("title", "")).strip():
            return False, "each benchmark_titles entry needs a non-empty 'title'"
    axes = c.get("axis_scores")
    if not isinstance(axes, dict) or any(a not in axes for a in AXES):
        return False, f"axis_scores must include all of {AXES}"
    for a in AXES:
        if not isinstance(axes.get(a), (int, float)):
            return False, f"axis_scores.{a} non-numeric"
    comps = c.get("named_comparisons")
    if not isinstance(comps, list) or not comps:
        return False, "named_comparisons must be a non-empty list"
    if not str(c.get("rationale", "")).strip():
        return False, "rationale missing/empty"
    return True, ""


def _normalize_judgment(c: dict) -> dict:
    pct = max(0.0, min(100.0, float(c["overall_percentage"])))
    axes = {a: round(max(0.0, min(20.0, float(c["axis_scores"][a]))), 1) for a in AXES}
    titles = [{"title": str(t.get("title", "")).strip(), "reason": str(t.get("reason", "")).strip()}
             for t in c["benchmark_titles"][:4]]
    comparisons = [str(x).strip() for x in c["named_comparisons"] if str(x).strip()]
    return {
        "overall_percentage": round(pct, 1),
        "benchmark_titles": titles,
        "axis_scores": axes,
        "named_comparisons": comparisons,
        "rationale": str(c.get("rationale", "")).strip(),
    }


def _lm_generate_judgment(feature: str, evidence: dict, max_retries: int = 2) -> dict:
    """Call LM Studio for the Critic's judgment.

    H-3 applies: an LM response containing its own reasoning dump ("Here's a thinking
    process") is a RETRY with a larger token budget, never a verdict — both `content` and
    `reasoning_content` are schema-validated before being consumed; a malformed or
    schema-invalid response retries with a larger max_tokens budget rather than being
    accepted as-is."""
    evidence_block = _evidence_block(evidence)
    token_budget = 3000
    last_err = "no attempt made"
    for attempt in range(max_retries + 1):
        prompt = _build_prompt(feature, evidence_block)
        payload = {
            "model": LM_STUDIO_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": token_budget,
            "temperature": 0.3,
        }
        req = urllib.request.Request(
            LM_STUDIO_URL, data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"})
        try:
            from core.lm_gateway import lm_urlopen, LM_TIMEOUT
            with lm_urlopen(req, timeout=LM_TIMEOUT, agent="critic") as r:
                msg = json.load(r)["choices"][0]["message"]
        except Exception as e:
            last_err = f"LM Studio request failed: {e}"
            print(f"[critic] attempt {attempt + 1}/{max_retries + 1} — {last_err}")
            token_budget += 2000
            continue

        found_json = False
        for text in (msg.get("content") or "", msg.get("reasoning_content") or ""):
            m = re.search(r"\{.*\}", text, re.DOTALL)
            if not m:
                continue
            found_json = True
            try:
                candidate = json.loads(m.group(0))
            except json.JSONDecodeError as e:
                last_err = f"JSON parse failed: {e}"
                continue
            ok, reason = _validate_schema(candidate)
            if ok:
                return _normalize_judgment(candidate)
            last_err = f"schema-invalid: {reason}"

        if not found_json:
            last_err = "no JSON blob found in content or reasoning_content"
        print(f"[critic] attempt {attempt + 1}/{max_retries + 1} — malformed/schema-invalid "
              f"response (H-3: retry with larger token budget, never consume as a verdict). "
              f"last_err={last_err}; token_budget was {token_budget}")
        token_budget += 2000  # H-3: larger budget on retry

    raise ValueError(f"LM returned no schema-valid judgment for '{feature}' after "
                     f"{max_retries + 1} attempts (last: {last_err}); schema-validate before "
                     f"consuming, per heuristic H-3.")


def judge_feature(feature: str, max_retries: int = 2) -> tuple:
    """Gather real evidence, call the LM, return (judgment_dict, evidence_dict)."""
    evidence = gather_evidence(feature)
    judgment = _lm_generate_judgment(feature, evidence, max_retries=max_retries)
    return judgment, evidence


def main():
    parser = argparse.ArgumentParser(
        description=f"The Critic — games-critic / AAA-benchmark analyst organ. {DISCLAIMER}")
    parser.add_argument("--feature", help="Feature name to judge (best with a record_grade already on file)")
    parser.add_argument("--dry-run", action="store_true", help="Print the judgment; record nothing to the graph")
    parser.add_argument("--list-graded", action="store_true",
                        help="List features with a ProfessorGrade on record (worth judging)")
    parser.add_argument("--max-retries", type=int, default=2,
                        help="LM malformed/schema-invalid-response retries with a larger token budget (H-3)")
    args = parser.parse_args()

    print(f"[critic] {DISCLAIMER}")

    if args.list_graded:
        graded = list_graded_features()
        if not graded:
            print("[critic] no ProfessorGrade nodes recorded yet — nothing to judge.")
            return 0
        print(f"[critic] {len(graded)} graded feature(s) (worth judging):")
        for g in graded:
            print(f"    {g['feature']:<32} {g['grade']} ({g['score']})  @ {g['timestamp'][:19]}")
        return 0

    if not args.feature:
        print("[critic] --feature <name> required (or --list-graded). "
              "Try: python -m core.critic --feature Ground_Sand_Particles --dry-run")
        return 1

    evidence = gather_evidence(args.feature)
    if not evidence["has_evidence"]:
        print(f"[critic] WARNING: no FeatureUpdate/ProfessorGrade evidence found for "
              f"'{args.feature}' — judging ungrounded is exactly the 'pure vibes' failure "
              f"this organ exists to avoid. Proceeding (the LM will be told evidence is "
              f"thin), but a record_grade on file first is strongly preferred.")
    print(f"[critic] gathered evidence for '{args.feature}': "
          f"status={evidence['latest_status']}  grade={evidence['latest_grade_letter']}  "
          f"surprises={len(evidence['surprises'])}  "
          f"observation={'yes' if evidence['latest_observation'] else 'no'}")

    try:
        judgment = _lm_generate_judgment(args.feature, evidence, max_retries=args.max_retries)
    except Exception as e:
        print(f"[critic] FAILED to produce a judgment: {e}")
        return 1

    print(f"\n=== CRITIC JUDGMENT: {args.feature} ===")
    print(f"{DISCLAIMER}")
    print(f"overall_percentage: {judgment['overall_percentage']}%  "
          f"(estimated player-enjoyment percentile vs benchmark set — NOT commercial-success odds)")
    print("benchmark_titles:")
    for bt in judgment["benchmark_titles"]:
        print(f"    - {bt['title']}: {bt['reason']}")
    print("axis_scores (0-20 each):")
    for axis in AXES:
        print(f"    {axis:<24} {judgment['axis_scores'].get(axis)}")
    print("named_comparisons:")
    for nc in judgment["named_comparisons"]:
        print(f"    - {nc}")
    print(f"rationale: {judgment['rationale']}")

    if args.dry_run:
        print("\n[critic] dry-run mode: no records written to graph")
        return 0

    node_id = record_critic_judgment(
        feature=args.feature,
        benchmark_titles=judgment["benchmark_titles"],
        overall_percentage=judgment["overall_percentage"],
        axis_scores=judgment["axis_scores"],
        named_comparisons=judgment["named_comparisons"],
        rationale=judgment["rationale"],
    )
    print(f"\n[critic] recorded CriticJudgment node: {node_id}  ({DISCLAIMER})")
    print("[critic] exit-0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
