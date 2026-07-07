"""Dream Loop — the Circadian Protocol's Dusk/Night consolidation (WS2.5).

Pure Python, zero model dependency, safe to run unattended (e.g. a 2 AM
scheduled task). It does three things and then goes back to sleep:

  1. Distills the day's failures/surprises into at most --max-candidates
     new pending heuristics (core.heuristic_distiller).
  2. Previews graph compaction (core.graph_compactor, dry-run only — the
     compactor is never auto-applied).
  3. Writes docs/DREAM_REPORT.md — the morning briefing for the human
     Gardener: what the night distilled, which pains are still open,
     what awaits approval.

It NEVER promotes heuristics, never archives, never touches the level or
generated code. Consolidation stages; the human decides at dawn.

Usage:
    python -m core.dream_loop [--max-candidates 2] [--min-cluster 3]

Schedule (optional, user opt-in), Windows Task Scheduler:
    schtasks /Create /SC DAILY /ST 02:00 /TN ChimeraDreamLoop
        /TR "python -m core.dream_loop" /V1  (run from E:\\PythonChimera\\Chimera)
"""
import argparse
import io
import re
import sys
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path

try:
    from core.graphify_interface import (load_dna_graph, collect_inheritance,
                                         collect_observation_queue)
    from core import heuristic_distiller, graph_compactor
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from graphify_interface import (load_dna_graph, collect_inheritance,
                                    collect_observation_queue)
    import heuristic_distiller
    import graph_compactor

CHIMERA_ROOT = Path(__file__).parent.parent
REPORT_PATH = CHIMERA_ROOT / "docs" / "DREAM_REPORT.md"
PENDING_PATH = CHIMERA_ROOT / "docs" / "PENDING_HEURISTICS.md"


def _run_captured(module_main, argv) -> str:
    buf = io.StringIO()
    old_argv = sys.argv
    try:
        sys.argv = ["x"] + argv
        with redirect_stdout(buf):
            module_main()
    except SystemExit:
        pass
    finally:
        sys.argv = old_argv
    return buf.getvalue()


def pending_summary() -> tuple:
    if not PENDING_PATH.exists():
        return 0, []
    text = PENDING_PATH.read_text(encoding="utf-8")
    entries = re.findall(r"^## (H-\d+): (.+?)$\n- status: (\w+)", text, re.MULTILINE)
    pending = [(num, sig) for num, sig, status in entries if status == "pending"]
    return len(pending), pending[:8]


def main():
    parser = argparse.ArgumentParser(description="Nightly consolidation: distill, preview, brief the Gardener")
    parser.add_argument("--max-candidates", type=int, default=2,
                        help="circadian cap: new candidates per night (default 2)")
    parser.add_argument("--min-cluster", type=int, default=3)
    parser.add_argument("--no-tend", action="store_true",
                        help="skip the delegated-Gardener tend pass (amendment 2026-07-07)")
    args = parser.parse_args()

    stamp = datetime.now(timezone.utc).isoformat()[:19] + "Z"
    print(f"[dream] consolidation starting {stamp}")

    distill_out = _run_captured(
        heuristic_distiller.main,
        ["--max-candidates", str(args.max_candidates), "--min-cluster", str(args.min_cluster)])
    print(distill_out, end="")

    # Delegated Gardener (amendment 2026-07-07): auto-rule the pending queue.
    # Human keeps veto-after: edit any status to `vetoed` and the next tend demotes it.
    tend_out = ""
    if not args.no_tend:
        try:
            from core import gardener
            report = gardener.tend(dry_run=False)
            tend_out = "; ".join(f"{k}:{len(v)}" for k, v in report.items() if v) or "queue clean"
            print(f"[dream] gardener tend -> {tend_out}")
        except Exception as ex:
            tend_out = f"tend FAILED: {ex}"
            print(f"[dream] {tend_out}")

    compact_out = _run_captured(graph_compactor.main, ["--dry-run"])
    print(compact_out, end="")

    nodes = load_dna_graph().get("nodes", [])
    inh = collect_inheritance(nodes)
    n_pending, pending = pending_summary()

    lines = [
        "# DREAM REPORT — morning briefing for the Gardener",
        f"consolidated: {stamp}",
        "",
        "## Awaiting your approval",
        f"{n_pending} pending heuristic(s) in docs/PENDING_HEURISTICS.md:" if n_pending
        else "No pending heuristics — the constitution covers everything the night found.",
    ]
    for num, sig in pending:
        lines.append(f"- {num}: {sig}")
    lines += ["", "## Open phantom pains"]
    if inh["open_pains"]:
        for p in inh["open_pains"][:6]:
            lines.append(f"- {p['id']} [{p['age_days']}d] {p['text']}")
    else:
        lines.append("None — all inherited pains dispositioned.")

    obs = collect_observation_queue(nodes)
    lines += ["", "## Observation queue — the true collapse awaits your eyes"]
    if obs:
        for q in obs[:10]:
            hint = f" — {q['grade_hint']}" if q["grade_hint"] else ""
            lines.append(f"- Loop {q['loop']} **{q['feature']}**{hint} "
                         f"(system-verified {q['verified_at']})")
        lines.append("")
        lines.append("Record verdicts: `python -m core.graphify_record observe --feature X "
                     "--verdict accepted|rejected --notes \"...\" --loop N`")
    else:
        lines.append("Empty — every system-verified feature has been human-observed.")
    lines += ["", "## Gardener tend (delegated authority — veto any line by editing its status)",
              f"`{tend_out or 'skipped (--no-tend)'}`",
              "", "## Tonight's distillation", "```", distill_out.strip(), "```",
              "", "## Compaction preview (dry-run — apply is always manual)",
              "```", compact_out.strip(), "```", ""]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"[dream] report -> {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
