"""One-command Post-Flight — records the Contract's end-of-phase results.

Usage:
    python -m core.postflight --phase "Loop 8 System_Economy apply" --result "UBT pass" \
        [--notes "..."] [--feature System_Economy --loop 8 --status verified]

Records a PhaseComplete node (plus an optional FeatureUpdate), then prints the
GPA trend and the Post-Flight checklist so nothing gets skipped.
"""
import argparse
import subprocess
import sys
from pathlib import Path

try:
    from core.graphify_interface import (graphify_query, record_phase, record_feature,
                                         parse_pain_verdicts, load_dna_graph,
                                         collect_inheritance)
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from graphify_interface import (graphify_query, record_phase, record_feature,
                                    parse_pain_verdicts, load_dna_graph,
                                    collect_inheritance)


def main():
    parser = argparse.ArgumentParser(description="Record Post-Flight results to the DNA graph")
    parser.add_argument("--phase", required=True, help="Phase name, e.g. 'Loop 8 System_Economy apply'")
    parser.add_argument("--result", required=True, help="What happened, verbatim where possible")
    parser.add_argument("--notes", default="", help="Extra context")
    parser.add_argument("--feature", help="Optionally also update a Feature Ledger entry")
    parser.add_argument("--loop", type=int, help="Loop number for --feature")
    parser.add_argument("--status", help="Status for --feature (researching/applying/verified/encoded/blocked)")
    parser.add_argument("--phantom-pain", action="append", dest="phantom_pain",
                        help="Generation Protocol: predicted failure point the next session must "
                             "confirm/refute (repeatable, <=5, aim for 3 sharp ones)")
    parser.add_argument("--inheritance", default="",
                        help="Generation Protocol: the Will — <=3 sentences on what this session "
                             "sacrificed itself to teach")
    parser.add_argument("--pain-verdict", action="append", dest="pain_verdict",
                        help="Disposition an inherited pain: "
                             "'<phase_node_id>:P<n>:confirmed|refuted|still-open' (repeatable)")
    args = parser.parse_args()

    node_id = record_phase(args.phase, args.result, args.notes,
                           phantom_pains=args.phantom_pain or [],
                           inheritance=args.inheritance,
                           pain_verdicts=parse_pain_verdicts(args.pain_verdict))
    print(f"PhaseComplete recorded: {node_id}")
    if str(node_id).startswith("rejected_"):
        raise SystemExit(1)
    for i, pain in enumerate(args.phantom_pain or [], start=1):
        print(f"  phantom pain declared -> {node_id}:P{i}  {pain[:80]}")

    if args.feature:
        if args.loop is None or not args.status:
            parser.error("--feature requires --loop and --status")
        fid = record_feature(args.feature, args.loop, args.status)
        print(f"FeatureUpdate recorded: {args.feature} (loop {args.loop}) = {args.status} -> {fid}")

    gpa = graphify_query("gpa", "trend") or {}
    print(f"GPA: {gpa.get('gpa')}  trend: {gpa.get('trend')}  grades: {gpa.get('grades_count')}")
    if gpa.get("trend") == "falling":
        print("!! GPA is FALLING — the Contract requires reporting this with corrective action.")

    # Tunnel containment — a session that postflights while still inside the
    # tunnel is the #1 leak (claim + editor left dangling for the reaper).
    try:
        from core.agent_tunnel import active_sessions
        open_sessions = active_sessions()
        if open_sessions:
            print("\n!! STILL IN THE TUNNEL — exit with evidence before you finish:")
            for s in open_sessions:
                print(f"   {s['agent']} holds {s['task_id']} ({s['task_title'][:48]})"
                      f"{' + editor ' + s['editor_mode'] if s.get('editor_held') else ''}")
                print(f"   -> python -m core.task_board done --agent {s['agent']} "
                      f"--id {s['task_id']} --result \"<verbatim evidence>\"  "
                      f"(or block --reason / release --note)")
    except Exception:
        pass

    # Git status check — surfaces uncommitted changes
    print()
    try:
        git_out = subprocess.run(
            ["git", "-C", str(Path(__file__).parent.parent), "status", "--short"],
            capture_output=True, text=True, timeout=10
        )
        git_lines = [l for l in git_out.stdout.splitlines() if l.strip()]
        if git_lines:
            print(f"[Git] {len(git_lines)} uncommitted change(s):")
            for l in git_lines[:10]:
                print(f"      {l}")
            if len(git_lines) > 10:
                print(f"      ... and {len(git_lines) - 10} more")
            # Check for untracked files
            untracked = [l for l in git_lines if l.startswith("??")]
            if untracked:
                print(f"      ({len(untracked)} untracked — add or .gitignore before committing)")
        else:
            print("[Git] Working tree is clean")
    except Exception as e:
        print(f"[Git] Status check failed: {e}")

    # Generation Protocol: warn if inherited pains remain un-dispositioned
    try:
        inh = collect_inheritance(load_dna_graph().get("nodes", []))
        undispositioned = [p for p in inh["open_pains"] if p["id"].split(":P")[0] != node_id]
        if undispositioned:
            print(f"\n[Inheritance] {len(undispositioned)} phantom pain(s) still open "
                  f"(confirm/refute with --pain-verdict):")
            for p in undispositioned[:5]:
                flag = " (still-open)" if p.get("still_open") else ""
                print(f"      {p['id']}  [{p['age_days']}d]{flag}  {p['text'][:70]}")
    except Exception as e:
        print(f"[Inheritance] scan failed: {e}")

    print("\nPost-Flight checklist:")
    print("  [ ] Exact UBT output reported verbatim (never summarized)")
    print("  [ ] Feature Ledger updated for every touched feature")
    print("  [ ] Every MCP call recorded as a pathway_attempt")
    print("  [ ] New discoveries recorded (research_discovery / technical_discovery)")
    print("  [ ] Phantom pains declared for next session + inherited pains dispositioned")
    print("  [ ] Evidenced features collapsed by AUTOMATED observation (sleepwalker/telemetry/grading — the measure)")
    print("  [ ] Git status reviewed and staged appropriate changes")
    print("  [ ] task_progress.md updated for the next session")


if __name__ == "__main__":
    main()
