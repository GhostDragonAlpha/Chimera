"""
THE WELLSPRING — the task board can never run dry while the vision is unrealized.

Why (2026-07-14, the human): an agent ran the full duty cycle, drained the board
(56 done / 0 open) and declared "the system is completely idle, awaiting your
directive" — in the same report that listed 22 features awaiting observation, a
CONFIRMED pain naming unwired tests, and a helm reading of ~46% vision realized
(more than half the game unbuilt). "I thought we had a system that made it so
there was always something to do?" — we did, but the feeders never fed the BOARD:
the ripener only converts pains, and seed_board only pulls rehearsal candidates +
pending research. When those run dry the board LOOKS finished while the seed
(CHIMERA_VISION.py) is barely half real.

The wellspring closes that loop. When a claim finds the frontier empty, it
replenishes the board from the studio's own steering organs, in priority order:

  C. RED REP ATOMS (score 1.2)  — regressions first: every battery failing in the
     latest rep run becomes a fix lane (classify honest-dead / stale / unspawned,
     fix at the right layer — the proven 25->10 method).
  B. OBSERVATION QUEUE (0.9)    — features system-finalized but awaiting automated
     observation become witness lanes (sleepwalker beats -> collapse_proxy).
  A. HELM VISION GAP (0.5+gap/2)— the design authority: every seed system realized
     <95% is a build lane, priority scaled by its gap.

Dedup is seed_board's job (live titles are skipped), so replenish() is idempotent
against the current board. Agent-agnostic: plain Python; any harness that runs
`task_board claim` inherits it.

CLI:
    python -m core.wellspring            # dry-run: show what would be seeded
    python -m core.wellspring --seed     # seed the board now
"""
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
REPS_DB = ROOT / "docs" / "world" / "reps.db"

MAX_BUILD = 10       # helm targets per replenish (the ranked worst)
MAX_WITNESS = 12     # observation-queue lanes per replenish
REALIZED_DONE = 0.95 # a seed system this realized is not a build lane


def _red_atom_rows():
    rows = []
    try:
        con = sqlite3.connect(str(REPS_DB))
        latest = con.execute("SELECT run_id FROM reps ORDER BY ts DESC LIMIT 1").fetchone()
        if latest:
            fails = con.execute(
                "SELECT feature, COUNT(*) FROM reps WHERE passed=0 AND run_id=? "
                "GROUP BY feature ORDER BY COUNT(*) DESC", (latest[0],)).fetchall()
            for feat, n in fails:
                rows.append({
                    "name": f"Fix {n} red rep atom(s): {feat}",
                    "score": 1.2,
                    "recipe": (
                        f"Query docs/world/reps.db for the latest run's failing atoms of {feat} "
                        f"(SELECT atom_id, evidence FROM reps WHERE passed=0 AND feature='{feat}' "
                        f"AND run_id=(SELECT run_id FROM reps ORDER BY ts DESC LIMIT 1)). Classify "
                        f"each red: HONEST dead-metadata (prop declared, unused -> WIRE it into real "
                        f"behavior), STALE probe (construct removed -> python -m core.rep_engine, "
                        f"prune_to_current), or UNSPAWNED component (H-34 -> attach it to its rightful "
                        f"owner). Generator-owned files: fix core/game_code_generator.py, never the C++. "
                        f"Re-measure: python -m core.rep_engine tend."),
                })
        con.close()
    except Exception:
        pass
    return rows


def _has_engine_witness(nodes, feat):
    """Is there an ENGINE-witnessed simtest for this feature already? (the credential,
    2026-07-17). A collapse task is pointless without one — collapse_proxy reads
    exercise from a real run, and a forged/absent witness proves only RECORDED."""
    toks = [w for w in str(feat).lower().replace("_", " ").split() if len(w) >= 4]
    for n in nodes:
        if n.get("type") != "SimPlaytest":
            continue
        if n.get("witnessed_by_engine") is False:      # a forgery is not a witness
            continue
        blob = f"{n.get('session','')} {n.get('demo','')}".lower()
        if any(t in blob for t in toks) and (n.get("beats_reached") or 0) > 0:
            return True
    return False


def _observation_rows(nodes):
    """SPLIT: Witness (completable in ONE session) vs Collapse (fires when EARNED).

    THE BUG THIS FIXES (2026-07-17, four sessions of it): one "Witness & collapse: X"
    task bundled a one-session job with a multi-night one. Collapse is rep-gated
    (rep_engine.rep_gate — reps accumulate across NIGHTS by design), so a single
    session could NEVER complete it: every agent wrote a beat, ran a clean witness,
    hit the rep wall at collapse, and then — measured — reported "collapse accepted"
    anyway. The task asked for something the session could not deliver, so the honest
    close was impossible and the dishonest one was inevitable.

    The split makes each task COMPLETABLE by whoever draws it:
      WITNESS  — write/lint the beat, run the engine (earns the authentic simtest +
                 reps). Completable now. Does NOT mention collapse; nobody is asked to
                 report a collapse they cannot perform.
      COLLAPSE — appears ONLY when the feature is rep-ready AND already
                 engine-witnessed. Now collapse_proxy can actually accept it, so the
                 task can actually close.
    A feature with neither → WITNESS. Witnessed but not yet rep-ready → still WITNESS
    (earn more reps). Rep-ready + witnessed → COLLAPSE.
    """
    rows = []
    try:
        try:
            from core.graphify_interface import collect_observation_queue
            from core.rep_engine import rep_gate
        except ImportError:
            sys.path.insert(0, str(HERE))
            from graphify_interface import collect_observation_queue
            from rep_engine import rep_gate
        for q in collect_observation_queue(nodes)[:MAX_WITNESS]:
            feat, loop = q.get("feature"), q.get("loop")
            if not feat:
                continue
            try:
                rep_ready, rep_reason = rep_gate(feat)
            except Exception:
                rep_ready, rep_reason = False, "rep gate unreadable"
            witnessed = _has_engine_witness(nodes, feat)

            if rep_ready and witnessed:
                # COLLAPSE — the one task that can now succeed, because both preconditions
                # the collapse depends on are already met.
                rows.append({
                    "name": f"Collapse: {feat}",
                    "score": 1.0,               # slightly above witness: finish what's ready
                    "recipe": (
                        f"{feat} (loop {loop}) is engine-witnessed AND rep-ready — collapse "
                        f"can now ACCEPT it. Find its clean simtest (docs/world/dna.db search, "
                        f"or `python -m core.dna_sqlite_backend search --query {str(feat)[:20]}`), "
                        f"then: python -m core.collapse_proxy --from-simtest <simtest_id>  <-- NO "
                        f"--valence (the SIMTEST decides: clean beats -> accepted; a contradicting "
                        f"--valence is REFUSED, exit 1). Confirm it reached 'observed': "
                        f"python -m core.why --feature {feat} --loop should now say YES via PHYSICS. "
                        f"If collapse still says 'unexercised', the beat did not name {feat} in its "
                        f"outcomes[].features — fix the beat, re-witness, then collapse."),
                })
            else:
                # WITNESS — completable now: run the engine, earn the credential + reps.
                # State the true blocker so the agent knows collapse is NOT this task.
                blocker = ("not yet engine-witnessed" if not witnessed
                           else f"witnessed, but {rep_reason}")
                rows.append({
                    "name": f"Witness: {feat}",
                    "score": 0.9,
                    "recipe": (
                        f"{feat} (loop {loop}) is system-finalized, awaiting observation. "
                        f"THIS TASK IS THE WITNESS ONLY — do NOT run collapse and do NOT report "
                        f"one ({blocker}; collapse is rep-gated across nights and becomes its own "
                        f"task when earned). Steps: (1) enroll + earn reps: python -m core.curriculum "
                        f"enroll --feature \"{feat}\" ; python -m core.rep_engine tend. (2) Pick/extend "
                        f"a beat under docs/beats/ that exercises {feat} with REAL input (H-14/H-21) "
                        f"and NAMES it in outcomes[].features. LINT FIRST: python -m core.beat_lint "
                        f"--beats docs/beats/<demo>.beats.json (a typo condemns the feature; it also "
                        f"flags an expect that has ALWAYS failed — a WALL, fix the cause). (3) Run the "
                        f"engine: python -m core.witness_runner --beats docs/beats/<demo>.beats.json "
                        f"--session obs_{str(feat)[:24]}. A clean run mints an ENGINE-witnessed simtest "
                        f"(witnessed_by_engine=True) — that is the credential collapse will later need. "
                        f"Close honestly: witness ran / did not; NEVER claim a collapse."),
                })
    except Exception:
        pass
    return rows


def _helm_rows():
    rows = []
    try:
        try:
            from core.helm import vision_gap
        except ImportError:
            sys.path.insert(0, str(HERE))
            from helm import vision_gap
        for t in (vision_gap().get("targets") or [])[:MAX_BUILD]:
            name = t.get("name")
            realized = float(t.get("realization", 0.0) or 0.0)
            gap = float(t.get("gap_value", 1.0 - realized) or 0.0)
            if not name or realized >= REALIZED_DONE:
                continue
            rows.append({
                "name": f"Build toward the seed: {name}",
                "score": round(0.5 + gap / 2.0, 2),
                "recipe": (
                    f"{name} is {realized:.0%} realized (gap {gap:.2f}) — {str(t.get('doc',''))[:120]}. "
                    f"ENROLL FIRST: python -m core.curriculum enroll --feature {name} (the training "
                    f"gate refuses un-enrolled verification — every piece goes through school). "
                    f"Research first (python -m core.spiral_forks --feature {name} --use-lm; Research "
                    f"Depth Protocol applies). Implement at the RIGHT layer: game content -> the DSL "
                    f"spec; code shape -> core/game_code_generator.py; loop-built subsystems -> hand-edit. "
                    f"Prove with reps + a witness run; the coin judges claim vs evidence at postflight."),
            })
    except Exception:
        pass
    return rows


def gather(nodes=None):
    """All candidate rows (deduped later by seed_board against the live board)."""
    if nodes is None:
        try:
            try:
                from core.graphify_interface import load_dna_graph
            except ImportError:
                sys.path.insert(0, str(HERE))
                from graphify_interface import load_dna_graph
            nodes = load_dna_graph().get("nodes", [])
        except Exception:
            nodes = []
    return _red_atom_rows() + _observation_rows(nodes) + _helm_rows()


def replenish(created_by="wellspring"):
    """Seed the board from the steering organs. Idempotent (seed_board dedups).
    Returns the list of tasks actually added."""
    rows = gather()
    if not rows:
        return []
    try:
        from core.task_board import seed_board
    except ImportError:
        sys.path.insert(0, str(HERE))
        from task_board import seed_board
    added = seed_board(rows=rows, research=[], created_by=created_by)
    if added:
        try:
            from core.capcom import post_safe
            post_safe("board", f"wellspring replenished the board: {len(added)} task(s) "
                      f"from helm gap / observation queue / red atoms",
                      level="info", source="wellspring")
        except Exception:
            pass
    return added


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(prog="wellspring",
                                description="THE WELLSPRING - the board cannot run dry")
    p.add_argument("--seed", action="store_true", help="seed the board (default: dry-run)")
    a = p.parse_args(argv)
    rows = gather()
    if not a.seed:
        print(f"would seed {len(rows)} candidate(s) (dedup happens at seed time):")
        for r in rows:
            print(f"  p={r['score']:<5} {r['name']}")
        print("seed them: python -m core.wellspring --seed")
        return 0
    added = replenish()
    print(f"seeded {len(added)} task(s) (rest were already live on the board)")
    for t in added:
        print(f"  {t['id']}  p={t.get('priority', 1):<5} {t['title'][:70]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
