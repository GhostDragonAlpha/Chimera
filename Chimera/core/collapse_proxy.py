"""Collapse proxy — fully automated observation amendment (2026-07-07).

AUTOMATED EVALUATION DRAINS THE EXPERIENCE AS A WHOLE, never feature-by-feature. This module
makes the per-feature queue drain from holistic automated signals only:

MODE A  --from-simtest <id> --valence accepted|rejected
    Sweep-attribute ONE automated temperature across the whole queue, grounded in
    evidence of exercise (SimPlaytest beat outcomes + witness chronicles):
      valence accepted -> every queue feature EXERCISED in/for that build is
        attributed accepted-tacit (observer automated-via-attribution, derived from
        the simtest). Silence over an exercised feature = passed the glance.
      valence rejected -> ONLY features the simulation evidence implicates are rejected
        (the agent quotes them per the normal branch-B flow); everything else is
        left for provisional collapse. A whole-experience rejection never
        mass-fails features the simulation did not indict.

MODE A'  --from-playtest <id> --valence accepted|rejected
    The human-observer twin of MODE A (CYCLE_PROMPT.md Step B.4 / .roo/rules/03-circadian.md):
    sweeps ONE holistic human temperature (a PlaytestObservation node — record_playtest /
    _mutate_playtest in graphify_interface.py) across the whole queue:
      valence accepted -> every queue feature EXERCISED (same _clean_exercises evidence
        as MODE A — beat coverage/witness chronicles) is attributed accepted-tacit,
        derived_from the playtest. Silence over an exercised feature = passed the glance.
      valence rejected -> ONLY features already quoted against THIS playtest are rejected.
        A PlaytestObservation carries just the human's verbatim notes, never structured
        per-feature outcomes like SimPlaytest, so "the evidence" is whatever the agent
        already attributed feature-by-feature (`graphify_record observe --derived-from
        <playtest_id> --quote "..."` — CYCLE_PROMPT.md Step B.2, the normal branch-B flow)
        before running this sweep. A whole-experience rejection never mass-fails features
        the human's words did not name.

MODE B  --tend  (runs nightly inside dream_loop)
    Automated collapse between cycles: any queue feature exercised
    cleanly in >= --min-sessions sleepwalk sessions is recorded
    observed_provisional or observed (observer agent-sim-automated, accept-only).
    Machine signals are final in the distiller — automated rejection reopens the feature
    no matter how many sims passed it.

Usage:
  python -m core.collapse_proxy --tend [--dry-run] [--min-sessions 2]
  python -m core.collapse_proxy --from-simtest simtest_xxx --valence accepted [--dry-run]
  python -m core.collapse_proxy --from-playtest playtest_xxx --valence accepted [--dry-run]
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Handle relative imports when run as script vs module
try:
    from core.graphify_interface import load_dna_graph, collect_observation_queue
except ImportError:
    sys.path.insert(0, str(ROOT))
    from graphify_interface import load_dna_graph, collect_observation_queue


def _queue_and_nodes():
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


def _rep_gate_check(feature: str):
    """Resolution-by-repetition gate (core.rep_engine): a feature earns
    acceptance through ACCUMULATED constraint reps (>=200 with a clean
    8-run streak), never through one good night. Advisory by default;
    CHIMERA_ENFORCE_REP_GATE=1 makes it hard. Rejections are NEVER gated —
    you can always fail; you can't graduate without your reps."""
    import os
    enforce = os.environ.get("CHIMERA_ENFORCE_REP_GATE") == "1"
    try:
        from core.rep_engine import rep_gate
        ok, reason = rep_gate(feature)
    except Exception as e:                      # engine unavailable -> never block
        return (False, True, f"rep engine unavailable ({e})")
    return (enforce, ok, reason)


def tend(min_sessions: int = 2, dry_run: bool = False):
    try:
        from core.graphify_interface import record_observation, record_feature
    except ImportError:
        sys.path.insert(0, str(ROOT))
        from graphify_interface import record_observation, record_feature
    queue, nodes = _queue_and_nodes()
    exercised = _clean_exercises(nodes)
    collapsed, waiting = [], []
    rep_advisories = []
    for q in queue:
        f = q["feature"]
        evidence = exercised.get(f, [])
        enforce, rep_ok, rep_reason = _rep_gate_check(f)
        if len(evidence) >= min_sessions and enforce and not rep_ok:
            waiting.append(f"{f} (REP-GATED: {rep_reason})")
            continue
        if len(evidence) >= min_sessions and not rep_ok:
            rep_advisories.append(f"{f}: {rep_reason}")
        if len(evidence) >= min_sessions:
            # Training Gate (2026-07-14): collapse is the door the gate exists
            # for — un-schooled/under-trained features stay queued and KEEP
            # TRAINING instead of collapsing. CHIMERA_TRAINING_GATE=warn softens.
            try:
                from core.training_gate import check as _tg_check, enforced as _tg_enforced
                _tgs, _tgd = _tg_check(f, status="observed_provisional")
            except Exception:
                _tgs, _tgd = "n/a", ""
            if _tgs == "missing" and _tg_enforced():
                waiting.append(f"{f} (TRAINING GATE: {_tgd[:80]})")
                continue
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
    for adv in rep_advisories[:8]:
        print(f"  rep-gate(advisory)  {adv}   [set CHIMERA_ENFORCE_REP_GATE=1 to enforce]")
    return {"collapsed": collapsed, "waiting": waiting}


def _indicted_by_simtest(nodes, simtest_id):
    """feature -> [quote strings] for outcomes in the ONE named simtest that did NOT
    reach 'reached'. Scoped to a single simtest_id, matching both the docstring's "the
    simulation evidence implicates" and the module's own accepted-branch contract --
    attribution is grounded in one specific simtest's evidence, not aggregated history
    (that's _clean_exercises's job, used by --tend and the accepted branch below)."""
    indicted = {}
    for n in nodes:
        if n.get("type") != "SimPlaytest" or n.get("id") != simtest_id:
            continue
        for o in n.get("outcomes", []):
            if o.get("outcome") == "reached":
                continue
            evidence = o.get("evidence") or []
            last_note = evidence[-1].get("note", "no evidence") if evidence else "no evidence"
            quote = f"{o.get('beat', '?')} ({o.get('outcome')}: {last_note})"
            for f in o.get("features", []):
                indicted.setdefault(f, []).append(quote)
    return indicted


def _indicted_by_playtest(nodes, playtest_id):
    """feature -> [quote strings], sourced from a human Playtest node instead of a
    SimPlaytest node (MODE A'). A PlaytestObservation (record_playtest/_mutate_playtest
    in graphify_interface.py) carries only the human's holistic verbatim notes — no
    structured per-feature outcomes like SimPlaytest.outcomes. So unlike
    _indicted_by_simtest (which reads evidence off the simtest node itself), the
    per-feature breakdown here is whatever the agent already attributed to THIS
    playtest via the normal branch-B flow: `graphify_record observe --derived-from
    <playtest_id> --quote "..."` (CYCLE_PROMPT.md Step B.2) — i.e. Observation nodes
    with derived_from == playtest_id and verdict == 'rejected'. Scoped to a single
    playtest_id, matching _indicted_by_simtest's own contract — a different playtest's
    rejections must never leak in."""
    indicted = {}
    for n in nodes:
        if n.get("type") != "Observation" or n.get("derived_from") != playtest_id:
            continue
        if n.get("verdict") != "rejected":
            continue
        f = n.get("feature_name")
        if not f:
            continue
        quote = n.get("quote") or n.get("notes") or "no quote recorded"
        indicted.setdefault(f, []).append(quote)
    return indicted


def sweep(simtest_id: str, valence: str, dry_run: bool = False):
    from core.graphify_interface import record_observation, record_feature
    queue, nodes = _queue_and_nodes()
    exercised = _clean_exercises(nodes)
    # provisional collapses count as already-swept; the queue holds the rest
    if valence == "rejected":
        indicted = _indicted_by_simtest(nodes, simtest_id)
        queue_features = {q["feature"]: q for q in queue}
        rejected = []
        for f, quotes in indicted.items():
            if f not in queue_features:
                continue  # never reach outside the queue -- matches the module's own contract
            q = queue_features[f]
            if not dry_run:
                record_observation(f, "rejected", observer="automated-via-attribution",
                                   derived_from=simtest_id, quote=" | ".join(quotes[:3]),
                                   notes=f"automated rejection sweep: simulation evidence "
                                         f"indicts this feature ({len(quotes)} failing "
                                         f"outcome(s)) in {simtest_id}")
                record_feature(f, int(q.get("loop") or 0), "needs_refinement",
                               {"holistic_sweep": simtest_id, "indicted_by": quotes[:3]})
            rejected.append(f)
        skipped = [f for f in queue_features if f not in rejected]
        mode = "DRY-RUN " if dry_run else ""
        print(f"[collapse_proxy] {mode}automated rejection sweep ({simtest_id}): "
              f"{len(rejected)} rejected, {len(skipped)} left queued (not indicted)")
        for f in rejected:
            print(f"  rejected    {f}")
        print("Automated collapse complete. Machine signals are final in the distiller.")
        return {"rejected": rejected, "skipped": skipped}
    swept, skipped = [], []
    rep_gated = []
    for q in queue:
        f = q["feature"]
        if exercised.get(f):
            enforce, rep_ok, rep_reason = _rep_gate_check(f)
            if enforce and not rep_ok:
                rep_gated.append(f"{f}: {rep_reason}")
                skipped.append(f)
                continue
            if not rep_ok:
                rep_gated.append(f"(advisory) {f}: {rep_reason}")
            # Training Gate (2026-07-14): the full-automation sweep may not
            # collapse an un-schooled/under-trained feature — it stays queued
            # and keeps training. CHIMERA_TRAINING_GATE=warn softens.
            try:
                from core.training_gate import check as _tg_check, enforced as _tg_enforced
                _tgs, _tgd = _tg_check(f, status="observed")
            except Exception:
                _tgs, _tgd = "n/a", ""
            if _tgs == "missing" and _tg_enforced():
                skipped.append(f"{f} (TRAINING GATE: {_tgd[:80]})")
                continue
            if not dry_run:
                record_observation(f, "accepted", observer="automated-via-attribution",
                                   derived_from=simtest_id, tacit=True,
                                   notes="fully-automated acceptance sweep: exercised, unindicted")
                record_feature(f, int(q.get("loop") or 0), "observed",
                               {"holistic_sweep": simtest_id})
            swept.append(f)
        else:
            skipped.append(f)
    mode = "DRY-RUN " if dry_run else ""
    print(f"[collapse_proxy] {mode}automated sweep ({simtest_id}): {len(swept)} accepted-tacit, "
          f"{len(skipped)} never exercised (stay queued for sim evidence)")
    for g in rep_gated[:8]:
        print(f"  rep-gate    {g}")
    for f in swept:
        print(f"  swept       {f}")
    for f in skipped[:12]:
        print(f"  unexercised {f}")
    print("Automated collapse complete. Machine signals are final in the distiller.")
    return {"swept": swept, "skipped": skipped}


def sweep_playtest(playtest_id: str, valence: str, dry_run: bool = False):
    """MODE A' — mirrors sweep() but sourced from a human PlaytestObservation node
    instead of a SimPlaytest node (see module docstring). Same shape, same queue
    contract ("never reach outside the queue"), same record_observation +
    record_feature pairing per processed feature — only the evidence source and the
    attribution provenance (derived_from a playtest_id, observer human-via-attribution)
    differ."""
    from core.graphify_interface import record_observation, record_feature
    queue, nodes = _queue_and_nodes()
    exercised = _clean_exercises(nodes)
    if valence == "rejected":
        indicted = _indicted_by_playtest(nodes, playtest_id)
        queue_features = {q["feature"]: q for q in queue}
        rejected = []
        for f, quotes in indicted.items():
            if f not in queue_features:
                continue  # never reach outside the queue -- matches the module's own contract
            q = queue_features[f]
            if not dry_run:
                record_observation(f, "rejected", observer="human-via-attribution",
                                   derived_from=playtest_id, quote=" | ".join(quotes[:3]),
                                   notes=f"playtest rejection sweep: the human's holistic "
                                         f"temperature indicts this feature ({len(quotes)} "
                                         f"quoted observation(s)) via {playtest_id}")
                record_feature(f, int(q.get("loop") or 0), "needs_refinement",
                               {"holistic_sweep": playtest_id, "indicted_by": quotes[:3]})
            rejected.append(f)
        skipped = [f for f in queue_features if f not in rejected]
        mode = "DRY-RUN " if dry_run else ""
        print(f"[collapse_proxy] {mode}playtest rejection sweep ({playtest_id}): "
              f"{len(rejected)} rejected, {len(skipped)} left queued (not indicted)")
        for f in rejected:
            print(f"  rejected    {f}")
        print("Playtest collapse complete. The human's one sentence overrides anytime.")
        return {"rejected": rejected, "skipped": skipped}
    swept, skipped = [], []
    for q in queue:
        f = q["feature"]
        if exercised.get(f):
            if not dry_run:
                record_observation(f, "accepted", observer="human-via-attribution",
                                   derived_from=playtest_id, tacit=True,
                                   notes="playtest acceptance sweep: exercised, unindicted "
                                         "by the human's holistic temperature")
                record_feature(f, int(q.get("loop") or 0), "observed",
                               {"holistic_sweep": playtest_id})
            swept.append(f)
        else:
            skipped.append(f)
    mode = "DRY-RUN " if dry_run else ""
    print(f"[collapse_proxy] {mode}playtest sweep ({playtest_id}): {len(swept)} accepted-tacit, "
          f"{len(skipped)} never exercised (stay queued for exercise evidence)")
    for f in swept:
        print(f"  swept       {f}")
    for f in skipped[:12]:
        print(f"  unexercised {f}")
    print("Playtest collapse complete. The human's one sentence overrides anytime.")
    return {"swept": swept, "skipped": skipped}


def main():
    # Ensure imports work at module level too
    try:
        from core.graphify_interface import load_dna_graph, collect_observation_queue
    except ImportError:
        sys.path.insert(0, str(ROOT))
        from graphify_interface import load_dna_graph, collect_observation_queue
    parser = argparse.ArgumentParser(description="Fully automated observation: sweep or provisional collapse")
    parser.add_argument("--tend", action="store_true")
    parser.add_argument("--from-simtest", dest="from_simtest")
    parser.add_argument("--from-playtest", dest="from_playtest")
    parser.add_argument("--valence", choices=["accepted", "rejected"])
    parser.add_argument("--min-sessions", type=int, default=2)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.from_simtest and args.from_playtest:
        parser.error("use only one of --from-simtest or --from-playtest at a time")
    if args.from_simtest:
        if not args.valence:
            parser.error("--from-simtest requires --valence")
        sweep(args.from_simtest, args.valence, dry_run=args.dry_run)
    elif args.from_playtest:
        if not args.valence:
            parser.error("--from-playtest requires --valence")
        sweep_playtest(args.from_playtest, args.valence, dry_run=args.dry_run)
    elif args.tend:
        tend(min_sessions=args.min_sessions, dry_run=args.dry_run)
    else:
        parser.error("use --tend, --from-simtest <id> --valence <v>, or --from-playtest <id> --valence <v>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
