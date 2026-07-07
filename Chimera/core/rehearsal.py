"""Rehearsal — data-level generational rollouts that decide the next move.

(SLEEPWALKER_DESIGN.md M2.) Enumerates candidate next-actions, scores each with
deterministic priors mined from the DNA graph (no LM, no wall-clock randomness),
prints a VETO TABLE (one human sentence reverses any decision), and on --decide
records a SimulationRollout node and prepends a recipe-carrying NEXT item to
task_progress.md (handoff invariant).

Candidates come from two sources, merged:
  1. the graph: every feature whose LATEST FeatureUpdate status is
     'needs_refinement' (human- or grade-reopened → highest value)
  2. optional --candidates-file JSON: [{"name", "recipe", "capable_only": bool,
     "value": float}] — how duty cycles/architecture docs curate structured work
     (e.g. DEMO_ARCHITECTURE phases)

Deterministic policy: score = value x p_success / cost (+ exploration bonus when
history is thin). All inputs printed; confidence exposed, never faked.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from core.graphify_interface import load_dna_graph, record_rollout
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from graphify_interface import load_dna_graph, record_rollout

ROOT = Path(__file__).resolve().parent.parent
TASK_PROGRESS = ROOT.parent / "task_progress.md"


def _latest_feature_statuses(nodes):
    latest = {}
    for n in nodes:
        if n.get("type") == "FeatureUpdate":
            name = n.get("feature_name") or n.get("feature") or (n.get("parameters") or {}).get("feature")
            ts = n.get("timestamp", "")
            st = n.get("status") or (n.get("parameters") or {}).get("status")
            if name and (name not in latest or ts > latest[name][1]):
                latest[name] = (st, ts)
    return {k: v[0] for k, v in latest.items()}


def _priors(nodes, name):
    """Mine per-candidate priors: grade history, sim outcomes, failure mentions."""
    p_success, evidence, n_signals = 0.6, [], 0  # uninformed prior
    grades = [n for n in nodes if n.get("type") == "ProfessorGrade"
              and name.lower() in json.dumps(n, default=str).lower()]
    if grades:
        g = sorted(grades, key=lambda n: n.get("timestamp", ""))[-1]
        letter = str(g.get("grade", "")).upper()[:1]
        p_success = {"A": 0.9, "B": 0.78, "C": 0.5, "F": 0.35}.get(letter, 0.6)
        evidence.append(f"grade:{letter}")
        n_signals += 1
    sims = [n for n in nodes if n.get("type") == "SimPlaytest"]
    hit_total = hit_reached = 0
    for s in sims:
        for o in s.get("outcomes", []):
            if name in (o.get("features") or []):
                hit_total += 1
                hit_reached += 1 if o.get("outcome") == "reached" else 0
    if hit_total:
        frac = hit_reached / hit_total
        p_success = 0.5 * p_success + 0.5 * frac
        evidence.append(f"sim:{hit_reached}/{hit_total}")
        n_signals += 1
    fails = sum(1 for n in nodes
                if n.get("error_category") not in (None, "", "none")
                and name.lower() in str(n.get("fix_description", "")).lower())
    if fails:
        p_success = max(0.2, p_success - 0.05 * min(fails, 6))
        evidence.append(f"failure_mentions:{fails}")
        n_signals += 1
    exploration = 0.25 if n_signals == 0 else (0.1 if n_signals == 1 else 0.0)
    return p_success, exploration, evidence


def enumerate_candidates(nodes, candidates_file=None):
    cands = {}
    for name, status in _latest_feature_statuses(nodes).items():
        if status == "needs_refinement":
            cands[name] = {"name": name, "value": 2.0, "capable_only": False,
                           "why": "needs_refinement (reopened)",
                           "recipe": f"fetch study guide: python -c \"from core.graphify_interface import graphify_query; import json; n=graphify_query('feature','{name}')[-1]; print(json.dumps(n.get('parameters',{{}}),default=str,indent=1)[:2000])\""}
    if candidates_file:
        for c in json.loads(Path(candidates_file).read_text(encoding="utf-8")):
            cands[c["name"]] = {"name": c["name"], "value": float(c.get("value", 1.0)),
                                "capable_only": bool(c.get("capable_only", False)),
                                "why": c.get("why", "curated"),
                                "recipe": c.get("recipe", "(no recipe provided — a wish, rank last)")}
    return list(cands.values())


def score_candidates(nodes, cands):
    rows = []
    for c in cands:
        p, explore, evidence = _priors(nodes, c["name"])
        cost = 2.0 if c.get("capable_only") else 1.0
        if "(no recipe" in c.get("recipe", ""):
            cost *= 2.0  # wishes are expensive
        score = (c["value"] * p) / cost + explore
        rows.append({**c, "p_success": round(p, 2), "explore_bonus": explore,
                     "cost": cost, "score": round(score, 3),
                     "evidence": evidence or ["no history (exploration)"]})
    rows.sort(key=lambda r: -r["score"])
    return rows


def veto_table(rows):
    lines = ["", "REHEARSAL DECISION — veto any line with one sentence to the agent",
             f"{'rank':<5}{'score':<8}{'p':<6}{'cost':<6}{'candidate':<38}why / evidence"]
    for i, r in enumerate(rows[:10], 1):
        lines.append(f"{i:<5}{r['score']:<8}{r['p_success']:<6}{r['cost']:<6}"
                     f"{r['name'][:36]:<38}{r['why']} | {','.join(r['evidence'])}")
    return "\n".join(lines)


def write_next_item(top):
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%MZ")
    block = (f"# Rehearsal decision {stamp} — next move: {top['name']}\n\n"
             f"Chosen by core.rehearsal (score {top['score']}, p_success {top['p_success']}, "
             f"evidence: {', '.join(top['evidence'])}). Human may veto with one sentence.\n\n"
             f"## NEXT (rehearsal-chosen; recipe per handoff invariant)\n"
             f"1. **{top['name']}**{' `capable sessions only`' if top.get('capable_only') else ''} — "
             f"{top['why']}. Recipe: {top['recipe']}\n"
             f"   Skip-condition: human vetoed in reply → rerun `python -m core.rehearsal --decide`.\n\n---\n\n")
    old = TASK_PROGRESS.read_text(encoding="utf-8") if TASK_PROGRESS.exists() else ""
    TASK_PROGRESS.write_text(block + old, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Rehearsal: decide the next move")
    parser.add_argument("--candidates-file", default=None)
    parser.add_argument("--decide", action="store_true",
                        help="record SimulationRollout + write NEXT item (default: dry-run)")
    parser.add_argument("--dry-run", action="store_true", help="explicit no-write mode")
    args = parser.parse_args()

    nodes = load_dna_graph().get("nodes", [])
    cands = enumerate_candidates(nodes, args.candidates_file)
    if not cands:
        print("rehearsal: no candidates (queue empty and no candidates file) — nothing to decide")
        return
    rows = score_candidates(nodes, cands)
    print(veto_table(rows))
    if args.decide and not args.dry_run:
        top = rows[0]
        node = record_rollout(chosen=top["name"],
                              candidates=[{k: r[k] for k in ("name", "score", "p_success", "cost", "why")}
                                          for r in rows[:10]],
                              rationale=f"value {top['value']} x p {top['p_success']} / cost {top['cost']} "
                                        f"+ explore {top['explore_bonus']}; evidence {top['evidence']}")
        write_next_item(top)
        print(f"\ndecided -> {node}; NEXT item prepended to {TASK_PROGRESS}")
    else:
        print("\n(dry-run: no records written; use --decide to commit the choice)")


if __name__ == "__main__":
    main()
