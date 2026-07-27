"""
The Gauntlet — the qualification crucible every agent runs before earning roles.

The human's vision (2026-07-12, verbatim intent)
------------------------------------------------
Every agent operates a little differently. Feed in as many agents of as many
types as you can; each one runs the gauntlet. At every station the agent must
ACHIEVE A CERTAIN OUTCOME before the next role can be attained — one complete
pass may take several turns if the agent lacks context, so progress persists.
The stations are laid out but the connections are NOT: briefs name where the
path runs (which organs, which docs), never the exact commands — the agent
must make the connections itself. Every station leaves an ARTIFACT CHECKPOINT
(written notes, verified mechanically). The only way out is through an
elaborate exit gate: a choice between real candidate next-moves, defended with
the agent's own research. Agents shine differently per station — the score
profile IS the capability map.

What this buys the studio
-------------------------
``--capable`` was self-declared; now it is EARNED. task_board refuses
capable_only claims from agents without the ``journeyman`` role (the human can
always hand-grant — one sentence outranks the machine). Station scores tag
specialties (researcher / cartographer / tunnel-runner), so heterogeneous
agents can be routed to where they shine.

Verification is MECHANICAL — every check cross-examines the artifact against
live state (the DNA graph, the task board, the tunnel, the filesystem). No LM
judges anything. When a station bounces you, it tells you exactly WHICH check
failed, never how to pass it.

Layout
------
    docs/gauntlet/<agent>/          artifact checkpoints (committed evidence)
    docs/gauntlet/runs/<agent>.json multi-turn run state
    docs/gauntlet/credentials.json  earned roles + station score profiles

CLI
---
    python -m core.gauntlet enter  --agent a1          # start (or resume) a run
    python -m core.gauntlet status --agent a1          # where am I, what's next
    python -m core.gauntlet brief  --agent a1          # reprint current station brief
    python -m core.gauntlet submit --agent a1          # verify current station, advance or bounce
    python -m core.gauntlet grant  --agent a1 --role journeyman --note "human fiat"
    python -m core.gauntlet roster                     # every agent's profile
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent

GAUNTLET_DIR = Path(os.environ.get("CHIMERA_GAUNTLET_DIR", ROOT / "docs" / "gauntlet"))
LOCK_PATH = Path(os.environ.get("CHIMERA_GAUNTLET_LOCK", HERE / "gauntlet.lock"))

SPECIALTY_THRESHOLD = 85
JOURNEYMAN_ROLE = "journeyman"
INITIATE_ROLE = "initiate"

# ---------------------------------------------------------------------------
# Advisory lock (same pattern as editor_scheduler / task_board).
# ---------------------------------------------------------------------------
if os.name == "nt":
    import msvcrt

    def _acquire_lock_fd():
        fd = os.open(LOCK_PATH, os.O_CREAT | os.O_RDWR)
        msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
        return fd

    def _release_lock_fd(fd):
        try:
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        except Exception:
            pass
        os.close(fd)
else:
    import fcntl

    def _acquire_lock_fd():
        fd = os.open(LOCK_PATH, os.O_CREAT | os.O_RDWR)
        fcntl.flock(fd, fcntl.LOCK_EX)
        return fd

    def _release_lock_fd(fd):
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        except Exception:
            pass
        os.close(fd)


def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _artifacts_dir(agent):
    return GAUNTLET_DIR / agent


def _run_path(agent):
    return GAUNTLET_DIR / "runs" / f"{agent}.json"


def _creds_path():
    return GAUNTLET_DIR / "credentials.json"


def _read_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


# ---------------------------------------------------------------------------
# Live facts — everything verifiers cross-examine artifacts against.
# Collected in ONE place so tests can monkeypatch collect_facts().
# ---------------------------------------------------------------------------
def collect_facts() -> dict:
    facts = {"gpa": None, "current_loop": None, "open_features": [],
             "open_task_ids": [], "open_pain_ids": [], "latest_build": None,
             "failed_builds": [], "feature_statuses": {}, "h_rule_ids": [],
             "candidates": [], "nodes": []}
    try:
        from core.graphify_interface import load_dna_graph, collect_inheritance
        nodes = load_dna_graph().get("nodes", [])
    except Exception:
        return facts
    facts["nodes"] = nodes

    gpas = sorted((n for n in nodes if n.get("type") == "ProfessorGPA"),
                  key=lambda n: n.get("timestamp", ""))
    if gpas:
        try:
            facts["gpa"] = float(gpas[-1].get("gpa"))
        except (TypeError, ValueError):
            pass

    # The exam key must BE the textbook: reuse preflight's exact helpers instead
    # of re-deriving. Two student-discovered bugs live in re-derivation: (1) a
    # different DONE_STATUSES set graded 'Loop 3' while preflight taught 'Loop 1';
    # (2) backfilled re-records shadow live statuses unless ranked below them
    # (preflight._latest_feature_statuses docstring, observed 2026-07-11).
    from core.preflight import _latest_feature_statuses, DONE_STATUSES
    updates = _latest_feature_statuses(nodes)
    ledger = {}
    for n in nodes:
        if n.get("type") == "Feature" and str(n.get("spiral_loop", "")).startswith("Loop"):
            try:
                ln = int(n["spiral_loop"].split()[-1])
            except (ValueError, IndexError):
                continue
            ledger.setdefault(ln, {})[n.get("name")] = n.get("status", "not_started")
    for ln in sorted(ledger):
        statuses = {f: updates.get(f, (None, s))[1] for f, s in ledger[ln].items()}
        open_feats = [f for f, s in statuses.items() if s not in DONE_STATUSES]
        if open_feats:
            facts["current_loop"] = ln
            facts["open_features"] = open_feats
            break
    facts["feature_statuses"] = {f: v[1] for f, v in updates.items()}

    builds = sorted((n for n in nodes if n.get("compilation_result") in ("pass", "fail")),
                    key=lambda n: n.get("timestamp", ""))
    if builds:
        b = builds[-1]
        facts["latest_build"] = {"result": b.get("compilation_result"),
                                 "timestamp": str(b.get("timestamp", "")), "id": b.get("id")}
    facts["failed_builds"] = [{"id": n.get("id"), "timestamp": str(n.get("timestamp", ""))}
                              for n in builds if n.get("compilation_result") == "fail"]

    try:
        pains = collect_inheritance(nodes).get("open_pains", [])
        facts["open_pain_ids"] = [str(p.get("id")) for p in pains]
    except Exception:
        pass

    try:
        from core.task_board import get_state
        tasks = get_state()["tasks"]
        facts["open_task_ids"] = [t["id"] for t in tasks if t["status"] == "open"]
        # Drift tolerance (pain phase_c2b05e119221ff60:P1, confirmed live within
        # the hour): the board moves between a student reading and submitting —
        # an id that was open can be claimed/blocked minutes later. Anchoring to
        # any LIVE task (not done/abandoned) is still honest work.
        facts["live_task_ids"] = [t["id"] for t in tasks
                                  if t["status"] in ("open", "claimed", "blocked")]
    except Exception:
        pass

    try:
        text = (ROOT.parent / "CLAUDE.md").read_text(encoding="utf-8")
        facts["h_rule_ids"] = re.findall(r"\[(H-\d+)[,\]]", text)
    except Exception:
        pass

    try:
        from core.rehearsal import enumerate_candidates, score_candidates
        candidates_file_path = ROOT / "docs/rehearsal_candidates.json"
        candidates_file = str(candidates_file_path) if candidates_file_path.exists() else None
        cands = enumerate_candidates(nodes, candidates_file)
        if cands:
            facts["candidates"] = [r["name"] for r in score_candidates(nodes, cands)[:10]]
    except Exception:
        pass
    return facts


def _read_artifact(agent, filename):
    p = _artifacts_dir(agent) / filename
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return None


# ---------------------------------------------------------------------------
# Stations. Each: name, artifact, brief (goals + where the path runs — never
# the commands), verify(agent, facts) -> (checks: list[(desc, bool)]).
# ---------------------------------------------------------------------------
def _v_orientation(agent, facts):
    text = _read_artifact(agent, "orientation.md")
    checks = [("artifact docs/gauntlet/%s/orientation.md exists" % agent, text is not None)]
    if text is None:
        return checks
    gpa = facts.get("gpa")
    gpa_ok = gpa is not None and (f"{gpa:.2f}" in text or f"{gpa:.1f}" in text)
    checks.append(("states the studio's current GPA", gpa_ok))
    loop = facts.get("current_loop")
    checks.append(("names the current spiral loop",
                   loop is not None and re.search(rf"\bLoop {loop}\b", text) is not None))
    checks.append(("names one of that loop's OPEN features",
                   any(f in text for f in facts.get("open_features", []))))
    # Self-teaching labels (Haiku test, 2026-07-15): a failed check must SHOW a
    # real, copy-pasteable example, not just name the requirement — the test
    # agent guessed a truncated pain id ('1b01fac') because the FULL form
    # ('phase_1b01fac303f3c24e:P1') was never surfaced at the point of failure.
    live = facts.get("live_task_ids") or facts.get("open_task_ids", [])
    eg_task = f" (e.g. {live[0]})" if live else " (run: python -m core.task_board list)"
    checks.append((f"cites a live board task id (tb-NNNN){eg_task}",
                   any(tid in text for tid in live)))
    pids = facts.get("open_pain_ids", [])
    eg_pain = (f" — copy the FULL id, e.g. {pids[0]}" if pids
               else " (see preflight section [3.75] 'Open phantom pains')")
    checks.append((f"cites one open phantom pain id{eg_pain}",
                   any(pid in text for pid in pids)))
    return checks


def _v_scribe(agent, facts):
    token = f"gauntlet:{agent}"
    hits = [n for n in facts.get("nodes", [])
            if n.get("type") == "SurpriseMoment" and token in json.dumps(n, default=str)]
    return [(f"a SurpriseMoment recorded via the typed helper carries the token '{token}'",
             bool(hits)),
            ("its source is 'agent' (typed recording, not a hand-written dict)",
             any(str(n.get("source", "")).lower() == "agent" for n in hits))]


def _v_scholar(agent, facts):
    text = _read_artifact(agent, "research.md")
    checks = [("artifact research.md exists", text is not None)]
    if text is None:
        return checks
    live = facts.get("live_task_ids") or facts.get("open_task_ids", [])
    checks.append(("anchored to a live board task id",
                   any(tid in text for tid in live)))
    cited = re.findall(r"(?:docs|research_corpus)[/\\][\w\-./\\]+", text)
    real = [c for c in cited if (ROOT / c).exists() or (ROOT.parent / c).exists()]
    checks.append((f"cites >=2 sources that exist on disk (found {len(real)})",
                   len(real) >= 2))
    checks.append(("states >=1 numeric acceptance criterion (research writes the exam)",
                   re.search(r"\d+(\.\d+)?\s*(fps|ms|s\b|m\b|cm|%|units)", text) is not None))
    return checks


def _v_cartographer(agent, facts):
    text = _read_artifact(agent, "graph.md")
    checks = [("artifact graph.md exists", text is not None)]
    if text is None:
        return checks
    lb = facts.get("latest_build") or {}
    checks.append(("reports the latest build's result (only the graph knows)",
                   bool(lb) and re.search(rf"\b{lb.get('result')}\b", text or "") is not None))
    checks.append(("pins it to the minute (timestamp[:16])",
                   bool(lb) and str(lb.get("timestamp", ""))[:16] in (text or "")))
    fs = facts.get("feature_statuses", {})
    named = [f for f in fs if f and f in text and fs[f] and str(fs[f]) in text]
    checks.append(("reports some feature's LATEST status, correctly paired", bool(named)))
    return checks


def _v_gatekeeper(agent, facts):
    text = _read_artifact(agent, "gates.md")
    checks = [("artifact gates.md exists", text is not None)]
    if text is None:
        return checks
    fails = facts.get("failed_builds", [])
    cited = any((f.get("id") and f["id"] in text) or
                (str(f.get("timestamp", ""))[:16] and str(f["timestamp"])[:16] in text)
                for f in fails)
    checks.append(("cites a REAL failed-build node (id or minute-timestamp)", cited))
    checks.append(("names the gate that guards it (gate_build_succeeded)",
                   "gate_build_succeeded" in text))
    checks.append(("applies a constitution H-rule by id",
                   any(h in text for h in facts.get("h_rule_ids", []))))
    return checks


def _v_tunnel_run(agent, facts):
    try:
        from core.task_board import get_state
        tasks = get_state()["tasks"]
    except Exception:
        tasks = []
    mine = [t for t in tasks if t.get("title") == f"Gauntlet sandbox: {agent}"]
    checks = [("your sandbox task exists on the board", bool(mine))]
    if not mine:
        return checks
    t = mine[0]
    done_by_me = (t["status"] == "done"
                  and any(n.get("agent") == agent and "done:" in n.get("text", "")
                          for n in t.get("notes", [])))
    checks.append(("you claimed it BY ID and finished it `done` (not release)", done_by_me))
    checks.append(("your `done` carried non-trivial evidence (>=20 chars)",
                   len((t.get("result") or "")) >= 20))
    try:
        from core.agent_tunnel import _read_session
        sess = _read_session(agent)
        checks.append(("the tunnel session opened AND exited cleanly",
                       bool(sess) and sess.get("exited_at") is not None
                       and sess.get("task_id") == t["id"]))
    except Exception:
        checks.append(("the tunnel session opened AND exited cleanly", False))
    return checks


def _v_exit_gate(agent, facts):
    text = _read_artifact(agent, "verdict.md")
    checks = [("artifact verdict.md exists", text is not None)]
    if text is None:
        return checks
    cands = facts.get("candidates", [])
    checks.append(("chooses a REAL live candidate (rehearsal's current top-10)",
                   any(c in text for c in cands) if cands else False))
    checks.append(("defends it with a constitution H-rule by id",
                   any(h in text for h in facts.get("h_rule_ids", []))))
    checks.append(("connects back to YOUR research artifact", "research.md" in text))
    checks.append(("cites a graph prior (grade / sim / surprise / phase node)",
                   re.search(r"(grade|sim|surprise|phase)_[0-9a-f]{6,}", text) is not None
                   or re.search(r"\bno prior\b", text) is not None))
    checks.append(("the reasoning is substantive (>=300 chars)", len(text) >= 300))
    return checks


STATIONS = [
    {"key": "orientation", "name": "ORIENTATION", "artifact": "orientation.md",
     "verify": _v_orientation, "specialty": None,
     "brief": ("Prove you can read the studio's live state. Write "
               "docs/gauntlet/<you>/orientation.md stating: the current GPA (2 "
               "decimals), the current spiral loop as 'Loop N' plus one of its OPEN "
               "features, one OPEN board task id (tb-NNNN), and one open phantom "
               "pain id. The path runs through: core.preflight, the task board, "
               "the inheritance section. Connect them yourself.")},
    {"key": "scribe", "name": "THE SCRIBE", "artifact": None,
     "verify": _v_scribe, "specialty": None,
     "brief": ("Prove typed recording. Put a SurpriseMoment into the DNA graph via "
               "the studio's typed helper — source agent — whose context or reality "
               "contains the exact token 'gauntlet:<you>'. Hand-written mutation "
               "dicts are the pollution the graph nearly drowned in; the helper is "
               "the law. The path runs through: core.graphify_record.")},
    {"key": "scholar", "name": "THE SCHOLAR'S DESK", "artifact": "research.md",
     "verify": _v_scholar, "specialty": "researcher",
     "brief": ("Research writes the exam. Pick any OPEN board task; write "
               "research.md anchored to its tb-id, citing at least TWO sources that "
               "exist on disk (docs/... or research_corpus/...), and state at least "
               "one NUMERIC acceptance criterion (fps/ms/%/units). The path runs "
               "through: core.scholar, docs/RESEARCH_CAMPUSES.md, the corpus.")},
    {"key": "cartographer", "name": "THE CARTOGRAPHER", "artifact": "graph.md",
     "verify": _v_cartographer, "specialty": "cartographer",
     "brief": ("Answer only what the graph knows. Write graph.md reporting: the "
               "LATEST build's result AND its timestamp to the minute, plus any "
               "feature's latest status — correctly paired (the graph punishes "
               "stale pairings). The path runs through: the DNA graph interface, "
               "not the docs.")},
    {"key": "gatekeeper", "name": "THE GATEKEEPER'S DRILL", "artifact": "gates.md",
     "verify": _v_gatekeeper, "specialty": None,
     "brief": ("Autopsy a real failure. Find an actual FAILED build in the graph; "
               "write gates.md citing that node (id or minute-timestamp), naming "
               "the gate that guards the pipeline against it, and applying one "
               "constitution H-rule by id to what went wrong. The path runs "
               "through: the graph's build records, core/gates.py, CLAUDE.md.")},
    {"key": "tunnel_run", "name": "THE TUNNEL RUN", "artifact": None,
     "verify": _v_tunnel_run, "specialty": "tunnel-runner",
     "brief": ("Walk the single entry for real. A sandbox task titled 'Gauntlet "
               "sandbox: <you>' has been seeded on the board with your name on it. "
               "Find its id, claim it BY ID through the single entry, do what its "
               "recipe says inside your footprint, and exit `done` with real "
               "evidence. Anything left dangling — claim, session, editor — fails "
               "you. The path runs through: core.task_board, core.agent_tunnel.")},
    {"key": "exit_gate", "name": "THE EXIT GATE", "artifact": "verdict.md",
     "verify": _v_exit_gate, "specialty": None,
     "brief": ("The only way out is a defended choice. Rehearsal keeps a live "
               "ranked candidate list; write verdict.md choosing ONE candidate and "
               "defending it with: an H-rule by id, a reference to YOUR research.md, "
               "and a graph prior (grade_/sim_/surprise_/phase_ node id — or the "
               "words 'no prior' if exploration is the argument). >=300 chars of "
               "reasoning. The path runs through: core.rehearsal, your own "
               "artifacts. Choose like the studio depends on it.")},
]


# ---------------------------------------------------------------------------
# Run state + credentials
# ---------------------------------------------------------------------------
def _load_run(agent):
    return _read_json(_run_path(agent), None)


def _save_run(run):
    _write_json(_run_path(run["agent"]), run)


def load_credentials():
    return _read_json(_creds_path(), {})


def has_role(agent, role) -> bool:
    return role in (load_credentials().get(agent, {}).get("roles") or [])


def _grant(agent, roles, scores=None, note=""):
    fd = _acquire_lock_fd()
    try:
        creds = load_credentials()
        entry = creds.setdefault(agent, {"roles": [], "station_scores": {}, "history": []})
        for r in roles:
            if r not in entry["roles"]:
                entry["roles"].append(r)
        if scores:
            entry["station_scores"].update(scores)
        entry["history"].append({"ts": _now_iso(), "granted": roles, "note": note})
        _write_json(_creds_path(), creds)
        return entry
    finally:
        _release_lock_fd(fd)


def _seed_sandbox_task(agent):
    """Station 6's live prop: a real board task scoped to the agent's own
    gauntlet directory, priced so it never outbids real work for anyone else."""
    try:
        from core.task_board import get_state, add_task
    except ImportError:
        from task_board import get_state, add_task
    title = f"Gauntlet sandbox: {agent}"
    if any(t["title"] == title for t in get_state()["tasks"]):
        return
    add_task(title=title,
             recipe=(f"Write docs/gauntlet/{agent}/tunnel_note.md: one paragraph on what "
                     f"your resource footprint is and why staying inside it protects the "
                     f"other agents. Exit done with the file path as evidence."),
             files=[f"docs/gauntlet/{agent}/**"], editor="none",
             priority=0.01, created_by="gauntlet")


def enter(agent):
    run = _load_run(agent)
    if run is None:
        run = {"agent": agent, "station": 0, "entered_at": _now_iso(),
               "attempts": [], "station_scores": {}, "completed_at": None}
        _artifacts_dir(agent).mkdir(parents=True, exist_ok=True)
        _save_run(run)
    if (not run.get("completed_at") and run["station"] < len(STATIONS)
            and STATIONS[run["station"]]["key"] == "tunnel_run"):
        _seed_sandbox_task(agent)  # resuming at the tunnel run re-seeds the prop
    return run


def submit(agent):
    """Verify the current station. Advance on pass; bounce with the exact failed
    checks on miss. Every attempt is recorded — the beating is part of the record."""
    run = _load_run(agent)
    if run is None:
        raise ValueError(f"{agent} has not entered — `enter` first")
    if run.get("completed_at"):
        return run, [("gauntlet already completed", True)], True
    station = STATIONS[run["station"]]
    facts = collect_facts()
    checks = station["verify"](agent, facts)
    passed = all(ok for _, ok in checks)
    score = round(100 * sum(1 for _, ok in checks if ok) / max(len(checks), 1))
    run["attempts"].append({"ts": _now_iso(), "station": station["key"],
                            "score": score, "passed": passed,
                            "failed_checks": [d for d, ok in checks if not ok]})
    if passed:
        run["station_scores"][station["key"]] = score
        run["station"] += 1
        if run["station"] == 3:
            # Surviving the first three stations earns 'initiate' mid-run.
            _grant(agent, [INITIATE_ROLE], note="first three stations passed")
        if run["station"] < len(STATIONS):
            nxt = STATIONS[run["station"]]
            if nxt["key"] == "tunnel_run":
                _seed_sandbox_task(agent)
        else:
            run["completed_at"] = _now_iso()
            roles = [INITIATE_ROLE, JOURNEYMAN_ROLE]
            roles += [s["specialty"] for s in STATIONS
                      if s.get("specialty")
                      and run["station_scores"].get(s["key"], 0) >= SPECIALTY_THRESHOLD]
            _grant(agent, roles, scores=run["station_scores"],
                   note=f"gauntlet completed in {len(run['attempts'])} attempt(s)")
            try:
                from core.graphify_interface import record_phase
                record_phase(f"Gauntlet completed: {agent}",
                             f"roles={roles} scores={run['station_scores']} "
                             f"attempts={len(run['attempts'])}", "")
            except Exception:
                pass
    _save_run(run)
    return run, checks, passed


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _print_brief(run):
    if run.get("completed_at"):
        print(f"{run['agent']} has COMPLETED the gauntlet.")
        return
    s = STATIONS[run["station"]]
    print(f"\n== STATION {run['station'] + 1}/{len(STATIONS)}: {s['name']} ==")
    print(s["brief"].replace("<you>", run["agent"]))
    if s.get("artifact"):
        print(f"\nartifact checkpoint: docs/gauntlet/{run['agent']}/{s['artifact']}")
    print(f"submit when ready: python -m core.gauntlet submit --agent {run['agent']}")


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description="The Gauntlet — agent qualification crucible")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("enter", "status", "brief", "submit"):
        px = sub.add_parser(name)
        px.add_argument("--agent", required=True)
    pg = sub.add_parser("grant", help="Human fiat — one sentence outranks the machine")
    pg.add_argument("--agent", required=True)
    pg.add_argument("--role", required=True)
    pg.add_argument("--note", default="human fiat")
    sub.add_parser("roster", help="Every agent's roles + station score profile")

    args = p.parse_args(argv)
    if args.cmd == "enter":
        run = enter(args.agent)
        print(f"{args.agent} enters the gauntlet (station {run['station'] + 1}"
              f"/{len(STATIONS)}; {len(run['attempts'])} prior attempt(s)).")
        _print_brief(run)
    elif args.cmd in ("status", "brief"):
        run = _load_run(args.agent)
        if run is None:
            print(f"{args.agent} has not entered. enter: python -m core.gauntlet "
                  f"enter --agent {args.agent}")
            sys.exit(1)
        if args.cmd == "status":
            done = run["station"] if not run.get("completed_at") else len(STATIONS)
            print(f"{args.agent}: {done}/{len(STATIONS)} stations"
                  f"  scores={run['station_scores']}  attempts={len(run['attempts'])}")
        _print_brief(run)
    elif args.cmd == "submit":
        try:
            run, checks, passed = submit(args.agent)
        except ValueError as e:
            print(f"REFUSED: {e}")
            sys.exit(1)
        for desc, ok in checks:
            print(f"  [{'PASS' if ok else 'FAIL'}] {desc}")
        if passed and run.get("completed_at"):
            creds = load_credentials().get(args.agent, {})
            print(f"\nTHE GAUNTLET IS BEHIND YOU. roles={creds.get('roles')}")
            print("capable_only lanes on the task board are now yours.")
        elif passed:
            print("\nSTATION CLEARED.")
            _print_brief(run)
        else:
            print("\nBOUNCED — the gauntlet tells you what failed, never how to pass.")
            sys.exit(1)
    elif args.cmd == "grant":
        entry = _grant(args.agent, [args.role], note=args.note)
        print(f"granted: {args.agent} roles={entry['roles']} ({args.note})")
    elif args.cmd == "roster":
        creds = load_credentials()
        if not creds:
            print("no credentialed agents yet — the gauntlet stands empty")
        for agent, e in sorted(creds.items()):
            print(f"  {agent}: roles={e.get('roles')} scores={e.get('station_scores')}")


if __name__ == "__main__":
    main()
