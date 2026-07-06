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
    from core.graphify_interface import graphify_query, record_phase, record_feature
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from graphify_interface import graphify_query, record_phase, record_feature


def main():
    parser = argparse.ArgumentParser(description="Record Post-Flight results to the DNA graph")
    parser.add_argument("--phase", required=True, help="Phase name, e.g. 'Loop 8 System_Economy apply'")
    parser.add_argument("--result", required=True, help="What happened, verbatim where possible")
    parser.add_argument("--notes", default="", help="Extra context")
    parser.add_argument("--feature", help="Optionally also update a Feature Ledger entry")
    parser.add_argument("--loop", type=int, help="Loop number for --feature")
    parser.add_argument("--status", help="Status for --feature (researching/applying/verified/encoded/blocked)")
    args = parser.parse_args()

    node_id = record_phase(args.phase, args.result, args.notes)
    print(f"PhaseComplete recorded: {node_id}")

    if args.feature:
        if args.loop is None or not args.status:
            parser.error("--feature requires --loop and --status")
        fid = record_feature(args.feature, args.loop, args.status)
        print(f"FeatureUpdate recorded: {args.feature} (loop {args.loop}) = {args.status} -> {fid}")

    gpa = graphify_query("gpa", "trend") or {}
    print(f"GPA: {gpa.get('gpa')}  trend: {gpa.get('trend')}  grades: {gpa.get('grades_count')}")
    if gpa.get("trend") == "falling":
        print("!! GPA is FALLING — the Contract requires reporting this with corrective action.")

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

    print("\nPost-Flight checklist:")
    print("  [ ] Exact UBT output reported verbatim (never summarized)")
    print("  [ ] Feature Ledger updated for every touched feature")
    print("  [ ] Every MCP call recorded as a pathway_attempt")
    print("  [ ] New discoveries recorded (research_discovery / technical_discovery)")
    print("  [ ] Git status reviewed and staged appropriate changes")
    print("  [ ] task_progress.md updated for the next session")


if __name__ == "__main__":
    main()
