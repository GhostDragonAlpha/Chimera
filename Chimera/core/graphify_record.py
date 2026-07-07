"""Typed DNA-graph recorder CLI — never hand-write mutation detail dicts.

Usage (from E:/PythonChimera/Chimera):
    python -m core.graphify_record feature --name Verb_Step --loop 2 --status verified --param blueprint_path=/Game/X
    python -m core.graphify_record pathway --tool manage_asset --action create_material --result success --param name=MAT_X
    python -m core.graphify_record loop --loop 7 --name Travel --status all_features_verified --feature Travel_Walking --feature Travel_Ship_Exterior
    python -m core.graphify_record phase --phase "Loop 8 apply" --result "UBT pass"
    python -m core.graphify_record grade --feature System_Economy --grade A --reasoning "..."

--param may repeat; values parse as JSON when possible, else stay strings.
Add --backfilled when recording history after the fact (never fake timestamps).
"""
import argparse
import json
import sys
from pathlib import Path

try:
    from core.graphify_interface import (
        record_feature, record_pathway, record_loop, record_phase, record_grade,
        record_heuristic, record_surprise, record_observation, record_playtest,
        record_simtest, record_rollout,
        parse_pain_verdicts,
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from graphify_interface import (
        record_feature, record_pathway, record_loop, record_phase, record_grade,
        record_heuristic, record_surprise, record_observation, record_playtest,
        record_simtest, record_rollout,
        parse_pain_verdicts,
    )


def _params_to_dict(pairs):
    out = {}
    for pair in pairs or []:
        if "=" not in pair:
            raise SystemExit(f"--param must be key=value, got: {pair}")
        key, _, value = pair.partition("=")
        try:
            out[key] = json.loads(value)
        except (json.JSONDecodeError, ValueError):
            out[key] = value
    return out


def main():
    parser = argparse.ArgumentParser(description="Record a typed mutation to the DNA graph")
    sub = parser.add_subparsers(dest="kind", required=True)

    p = sub.add_parser("feature", help="Feature Ledger status change")
    p.add_argument("--name", required=True)
    p.add_argument("--loop", type=int, required=True)
    p.add_argument("--status", required=True)
    p.add_argument("--param", action="append", help="key=value (repeatable)")
    p.add_argument("--backfilled", action="store_true")

    p = sub.add_parser("pathway", help="MCP pathway attempt")
    p.add_argument("--tool", required=True)
    p.add_argument("--action", required=True)
    p.add_argument("--result", required=True)
    p.add_argument("--param", action="append", help="key=value (repeatable)")
    p.add_argument("--error", default="")
    p.add_argument("--backfilled", action="store_true")

    p = sub.add_parser("loop", help="Spiral loop completion")
    p.add_argument("--loop", type=int, required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--status", default="all_implemented")
    p.add_argument("--feature", action="append", help="completed feature name (repeatable)")
    p.add_argument("--anchor", default="", help="emotional anchor")
    p.add_argument("--backfilled", action="store_true")

    p = sub.add_parser("phase", help="Post-Flight phase completion")
    p.add_argument("--phase", required=True)
    p.add_argument("--result", required=True)
    p.add_argument("--notes", default="")
    p.add_argument("--phantom-pain", action="append", dest="phantom_pain",
                   help="predicted failure point for the next session to confirm/refute (repeatable, <=5)")
    p.add_argument("--inheritance", default="",
                   help="the Will: <=3 sentences on what this session sacrificed to learn")
    p.add_argument("--pain-verdict", action="append", dest="pain_verdict",
                   help="disposition an inherited pain: '<phase_node_id>:P<n>:confirmed|refuted|still-open' (repeatable)")

    p = sub.add_parser("grade", help="Professor grade (A/B/C/F)")
    p.add_argument("--feature", required=True)
    p.add_argument("--grade", required=True, choices=["A", "B", "C", "F", "a", "b", "c", "f"])
    p.add_argument("--reasoning", default="")

    p = sub.add_parser("heuristic", help="Gardener-APPROVED heuristic promotion")
    p.add_argument("--signature", required=True, help="failure signature/cluster this rule immunizes against")
    p.add_argument("--rule", required=True, help="the one-sentence constitutional rule")
    p.add_argument("--organ", required=True, choices=["gate", "claude_md", "mcp_pathways"])
    p.add_argument("--evidence", action="append", help="graph node id of teaching failure (repeatable)")

    p = sub.add_parser("observe", help="Observation verdict — direct human, or agent attribution of a playtest")
    p.add_argument("--feature", required=True)
    p.add_argument("--verdict", required=True, choices=["accepted", "rejected"])
    p.add_argument("--notes", default="", help="REQUIRED for rejections — the human's reason")
    p.add_argument("--loop", type=int, help="loop number (for the follow-up status flip)")
    p.add_argument("--derived-from", default="", dest="derived_from",
                   help="playtest node id when this is an agent attribution of a holistic temperature")
    p.add_argument("--quote", default="", help="the human's exact phrase implicating this feature (required for non-tacit attribution)")
    p.add_argument("--tacit", action="store_true",
                   help="feature was exercised in the playtest but unmentioned — silence passed the glance")

    p = sub.add_parser("playtest", help="The human's holistic temperature — verbatim, few tokens, whole build")
    p.add_argument("--notes", required=True, help="the human's words, VERBATIM")
    p.add_argument("--build", default="", help="commit/build reference")

    p = sub.add_parser("surprise", help="SurpriseMoment (Circadian dream fodder) — capture live")
    p.add_argument("--context", required=True, help="what was happening")
    p.add_argument("--reality", required=True, help="what actually happened / what the human said")
    p.add_argument("--expectation", default="", help="what was expected instead")
    p.add_argument("--lesson-hint", default="", dest="lesson_hint",
                   help="optional first guess at the lesson")
    p.add_argument("--source", default="agent", choices=["agent", "human", "engine"],
                   help="who produced the surprise (human = a correction from the user)")

    p = sub.add_parser("simtest", help="Sleepwalker beat-run record (agent-sim evidence, never a verdict)")
    p.add_argument("--session", required=True)
    p.add_argument("--demo", required=True)
    p.add_argument("--beats-total", type=int, required=True, dest="beats_total")
    p.add_argument("--beats-reached", type=int, required=True, dest="beats_reached")
    p.add_argument("--outcomes-json", default="[]", dest="outcomes_json")
    p.add_argument("--timeline", default="")
    p.add_argument("--temperature", default="")

    p = sub.add_parser("rollout", help="Rehearsal next-move decision (human may veto with one sentence)")
    p.add_argument("--chosen", required=True)
    p.add_argument("--candidates-json", default="[]", dest="candidates_json")
    p.add_argument("--rationale", default="")

    args = parser.parse_args()

    if args.kind == "feature":
        node_id = record_feature(args.name, args.loop, args.status,
                                 _params_to_dict(args.param), backfilled=args.backfilled)
    elif args.kind == "pathway":
        node_id = record_pathway(args.tool, args.action, args.result,
                                 _params_to_dict(args.param), args.error, backfilled=args.backfilled)
    elif args.kind == "loop":
        node_id = record_loop(args.loop, args.name, args.feature or [], args.status,
                              args.anchor, backfilled=args.backfilled)
    elif args.kind == "phase":
        node_id = record_phase(args.phase, args.result, args.notes,
                               phantom_pains=args.phantom_pain or [],
                               inheritance=args.inheritance,
                               pain_verdicts=parse_pain_verdicts(args.pain_verdict))
    elif args.kind == "heuristic":
        node_id = record_heuristic(args.signature, args.rule, args.organ,
                                   evidence_ids=args.evidence or [])
    elif args.kind == "surprise":
        node_id = record_surprise(args.context, args.reality, args.expectation,
                                  args.lesson_hint, args.source)
    elif args.kind == "observe":
        node_id = record_observation(args.feature, args.verdict, args.notes,
                                     derived_from=args.derived_from, quote=args.quote,
                                     tacit=args.tacit)
        if not str(node_id).startswith("rejected_"):
            status = "observed" if args.verdict == "accepted" else "needs_refinement"
            params = {"human_verdict": args.verdict}
            if args.notes:
                params["human_notes"] = args.notes
            if args.derived_from:
                params["attribution"] = f"derived from {args.derived_from}" + \
                    (f" | quote: {args.quote}" if args.quote else " | tacit (exercised, unmentioned)")
            fid = record_feature(args.feature, args.loop if args.loop is not None else 0,
                                 status, params)
            print(f"FeatureUpdate: {args.feature} -> {status} ({fid})")
    elif args.kind == "simtest":
        node_id = record_simtest(args.session, args.demo, args.beats_total, args.beats_reached,
                                 json.loads(args.outcomes_json), args.timeline, args.temperature)
    elif args.kind == "rollout":
        node_id = record_rollout(args.chosen, json.loads(args.candidates_json), args.rationale)
    elif args.kind == "playtest":
        node_id = record_playtest(args.notes, args.build)
    else:
        node_id = record_grade(args.feature, args.grade.upper(), args.reasoning)

    print(node_id)
    if str(node_id).startswith("rejected_"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
