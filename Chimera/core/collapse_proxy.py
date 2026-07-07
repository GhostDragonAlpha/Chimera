"""Collapse proxy — the whole-experience observation amendment (2026-07-07).

THE HUMAN APPROVES THE EXPERIENCE AS A WHOLE, never feature-by-feature. This module
makes the per-feature queue drain from holistic signals only:

MODE A  --from-playtest <id> --valence accepted|rejected
    Sweep-attribute ONE human temperature across the whole queue, grounded in
    evidence of exercise (SimPlaytest beat outcomes + witness chronicles):
      valence accepted -> every queue feature EXERCISED in/for that build is
        attributed accepted-tacit (observer human-via-attribution, derived from
        the playtest). Silence over an exercised feature = passed the glance.
      valence rejected -> ONLY features the human's words implicate are rejected
        (the agent quotes them per the normal branch-B flow); everything else is
        left for sim-provisional collapse. A whole-experience rejection never
        mass-fails features the human did not indict.

MODE B  --tend  (runs nightly inside dream_loop)
    Provisional collapse between human temperatures: any queue feature exercised
    cleanly in >= --min-sessions sleepwalk sessions is recorded
    observed_provisional (observer agent-sim-provisional, accept-only).
    The human's NEXT holistic sentence — anytime — overrides everything:
    a rejection reopens the feature no matter how many sims passed it.

Usage:
  python -m core.collapse_proxy --tend [--dry-run] [--min-sessions 2]
  python -m core.collapse_proxy --from-playtest playtest_xxx --valence accepted [--dry-run]
"""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _queue_and_nodes():
    from core.graphify_interface import load_dna_graph, collect_observation_queue
    nodes = load_dna_graph().get("nodes", [])
    return collect_observation_queue(nodes), nodes


def _clean_exercises(nodes):
    """feature -> [simtest ids] where EVERY beat listing the feature was 'reached'."""
    per_feature = {}
    for n in nodes:
        if n.get("type") != "SimPlaytest":
            continue
        feats = {}
        for o in n.get("outcomes", []):
            for f in o.get("features", []):
                feats.setdefault(f, True)
                if o.get("outcome") != "reached":
                    feats[f] = False
        for f, clean in feats.items():
            if clean:
                per_feature.setdefault(f, []).append(n.get("id"))
    return per_feature


def tend(min_sessions: int = 2, dry_run: bool = False):
    from core.graphify_interface import record_observation, record_feature
    queue, nodes = _queue_and_nodes()
    exercised = _clean_exercises(nodes)
    collapsed, waiting = [], []
    for q in queue:
        f = q["feature"]
        evidence = exercised.get(f, [])
        if len(evidence) >= min_sessions:
            if not dry_run:
                record_observation(f, "accepted", observer="agent-sim-provisional",
                                   derived_from=evidence[-1], tacit=True,
                                   notes=f"provisional collapse: {len(evidence)} clean sleepwalk exercises; "
                                         f"human whole-experience verdict overrides anytime")
                record_feature(f, int(q.get("loop") or 0), "observed_provisional",
                               {"sim_evidence": evidence[:4]})
            collapsed.append(f"{f} ({len(evidence)} sessions)")
        else:
            waiting.append(f"{f} (evidence {len(evidence)}/{min_sessions})")
    mode = "DRY-RUN " if dry_run else ""
    print(f"[collapse_proxy] {mode}provisional: {len(collapsed)} collapsed, {len(waiting)} awaiting evidence")
    for c in collapsed:
        print(f"  collapsed~  {c}")
    for w in waiting[:12]:
        print(f"  waiting     {w}")
    return {"collapsed": collapsed, "waiting": waiting}


def sweep(playtest_id: str, valence: str, dry_run: bool = False):
    from core.graphify_interface import record_observation, record_feature
    queue, nodes = _queue_and_nodes()
    exercised = _clean_exercises(nodes)
    # provisional collapses count as already-swept; the queue holds the rest
    if valence == "rejected":
        print("[collapse_proxy] rejected valence: attribute ONLY the features the human's words "
              "implicate (branch B quote tier) — no mass action taken; everything else stays for --tend")
        return {"swept": []}
    swept, skipped = [], []
    for q in queue:
        f = q["feature"]
        if exercised.get(f):
            if not dry_run:
                record_observation(f, "accepted", observer="human-via-attribution",
                                   derived_from=playtest_id, tacit=True,
                                   notes="whole-experience acceptance sweep: exercised, unindicted")
                record_feature(f, int(q.get("loop") or 0), "observed",
                               {"holistic_sweep": playtest_id})
            swept.append(f)
        else:
            skipped.append(f)
    mode = "DRY-RUN " if dry_run else ""
    print(f"[collapse_proxy] {mode}holistic sweep ({playtest_id}): {len(swept)} accepted-tacit, "
          f"{len(skipped)} never exercised (stay queued for sim evidence)")
    for f in swept:
        print(f"  swept       {f}")
    for f in skipped[:12]:
        print(f"  unexercised {f}")
    print("Present this table to the human — any line reverses with one sentence.")
    return {"swept": swept, "skipped": skipped}


def main():
    parser = argparse.ArgumentParser(description="Whole-experience observation: sweep or provisional collapse")
    parser.add_argument("--tend", action="store_true")
    parser.add_argument("--from-playtest", dest="from_playtest")
    parser.add_argument("--valence", choices=["accepted", "rejected"])
    parser.add_argument("--min-sessions", type=int, default=2)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.from_playtest:
        if not args.valence:
            parser.error("--from-playtest requires --valence")
        sweep(args.from_playtest, args.valence, dry_run=args.dry_run)
    elif args.tend:
        tend(min_sessions=args.min_sessions, dry_run=args.dry_run)
    else:
        parser.error("use --tend or --from-playtest <id> --valence <v>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
