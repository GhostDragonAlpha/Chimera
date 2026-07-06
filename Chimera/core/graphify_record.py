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
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from graphify_interface import (
        record_feature, record_pathway, record_loop, record_phase, record_grade,
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

    p = sub.add_parser("grade", help="Professor grade (A/B/C/F)")
    p.add_argument("--feature", required=True)
    p.add_argument("--grade", required=True, choices=["A", "B", "C", "F", "a", "b", "c", "f"])
    p.add_argument("--reasoning", default="")

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
        node_id = record_phase(args.phase, args.result, args.notes)
    else:
        node_id = record_grade(args.feature, args.grade.upper(), args.reasoning)

    print(node_id)
    if str(node_id).startswith("rejected_"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
