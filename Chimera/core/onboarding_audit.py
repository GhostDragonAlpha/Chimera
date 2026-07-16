"""
onboarding_audit - score a session against the MASTER_ONBOARDING checkpoints.

WHY THIS EXISTS (2026-07-16): the operator tests `docs/MASTER_ONBOARDING.md` by
restarting a FRESH agent after every revision - one prompt version per clean agent.
That only yields a real result if every revision is scored the SAME way. Hand-auditing
drifts: you find what you went looking for, and you rationalise afterward. So the pass
criteria are PRE-REGISTERED here, in code, before the run.

THE AUDIT READS THE RECORDS, NEVER THE AGENT'S SUMMARY. The session that motivated
this reported "postflight completed successfully" while: the deep brain was down (its
gate silently skipped), ZERO research was done (the research gate passed on ANOTHER
session's node), nothing was committed, and the studio's #1 seed gap was released for
the third time. Every one of those is invisible in a summary and obvious in the graph.

READ-ONLY BY CONSTRUCTION - it must not perturb what it measures:
  - graph via load_dna_graph()          (load, no save)
  - CAPCOM via _con()/recent()          (NOT `brief`: that ingests the inbox + acks)
  - board via task_board._read_state()  (NOT `claim`: that reconciles ghost tasks)
  - ds4 via health(), git via log/status
Nothing here writes. If you add a check, keep it that way.

TIME: CAPCOM signals carry a real epoch `ts`; DNA nodes carry UTC-naive ISO strings
(CAPCOM *renders* local - a 5h offset that already cost one audit a false negative).
Window on epoch, compare graph nodes against the UTC form of the same instant.

  python -m core.onboarding_audit [--hours 6] [--since <UTC ISO>] [--json]

Exit: 0 = every REQUIRED check passed * 1 = at least one failed/unproven.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

PASS, FAIL, NA = "PASS", "FAIL", "n/a"


# --------------------------------------------------------------------------
# window helpers
# --------------------------------------------------------------------------
def _epoch(iso):
    dt = datetime.fromisoformat(iso.strip().replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


def _utc_iso(epoch):
    return datetime.fromtimestamp(epoch, timezone.utc).replace(tzinfo=None).isoformat()


def _window(hours, since, until):
    """A BOUNDED window. --until matters: revisions are compared session-vs-session,
    and an unbounded 'since X to now' bleeds the next run into the last one's score."""
    end = _epoch(until) if until else time.time()
    start = _epoch(since) if since else end - hours * 3600.0
    return {"start": start, "end": end, "start_iso": _utc_iso(start), "end_iso": _utc_iso(end)}


def _graph_nodes(win):
    from core.graphify_interface import load_dna_graph
    nodes = load_dna_graph().get("nodes", [])
    return [n for n in nodes
            if win["start_iso"] <= str(n.get("timestamp", "")) <= win["end_iso"]]


def _signals(win, limit=800):
    from core import capcom
    con = capcom._con()
    return [s for s in capcom.recent(con, limit=limit)
            if win["start"] <= float(s.get("ts") or 0) <= win["end"]]


def _git(*args):
    try:
        return subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True,
                              text=True, timeout=60).stdout.strip()
    except Exception:
        return ""


# --------------------------------------------------------------------------
# the checks - each returns (status, detail, evidence[])
# --------------------------------------------------------------------------
def check_ds4_up(win_nodes, sigs, win):
    """Rule 11: BOTH brains up; the LEAD brings the deep one up.
    A down deep brain SILENTLY skips the Council review - nothing errors."""
    ev = []
    ds4_sigs = [s for s in sigs if (s.get("source") == "ds4_brain" or s.get("channel") == "ds4")]
    for s in ds4_sigs[:3]:
        ev.append(f"capcom {s.get('ts_iso')} ({s.get('channel')}) {str(s.get('msg'))[:90]}")
    # Live status is evidence ONLY for a window that ends ~now. Scoring a HISTORICAL
    # session, "it's up at this moment" says nothing about whether it was up THEN -
    # and would hand a false PASS to the very session that left it down.
    live_counts = (time.time() - win["end"]) < 900
    if live_counts:
        try:
            from core import ds4_brain
            live = ds4_brain.health(timeout=6.0)
        except Exception as e:
            live = {"up": False, "error": str(e)[:80]}
        ev.append(f"live ds4_brain.health() -> up={live.get('up')}")
    else:
        live = {"up": False}
        ev.append("live status NOT consulted (historical window - only in-window signals count)")
    # Secondary proof: the council CANNOT run without the deep brain, so any council
    # signal in-window is evidence it was up even after a `stop` (which is a sensible
    # thing to do - it holds ~80GB of RAM).
    council_sigs = [s for s in sigs if s.get("channel") == "council" or s.get("source") == "council"]
    for s in council_sigs[:2]:
        ev.append(f"capcom {s.get('ts_iso')} (council) {str(s.get('msg'))[:80]}")
    if ds4_sigs:
        return PASS, "deep brain came up during the session (capcom ds4 signal)", ev
    if council_sigs:
        return PASS, "council ran, which is impossible with the deep brain down", ev
    if live.get("up"):
        return PASS, "deep brain is up at session end", ev
    # NOTE: ds4_brain.serve() posts NOTHING to capcom, so absence of a signal is not
    # by itself proof it never came up - only proof the audit cannot SEE that it did.
    # Run this promptly after a session, or a correct `serve` + `stop` reads as a miss.
    return FAIL, ("no evidence the deep brain was ever up (Council review silently "
                  "skipped). NB: serve() leaves no capcom trace - audit promptly"), ev


def check_research_scoped(win_nodes, sigs, win):
    """Rule 9: research is SELF-IMPOSED per session.

    THE CHECK THE GATE CANNOT DO. research_gate.check() accepts ANY research node
    from an 8h graph-wide lookback, so a neighbouring session satisfies yours. Here
    we demand what 'this session' actually means: a ResearchDiscovery sharing a
    run_id with this session's PhaseComplete."""
    phases = [n for n in win_nodes if n.get("type") == "PhaseComplete"]
    research = [n for n in win_nodes if n.get("type") == "ResearchDiscovery"]
    waivers = [s for s in sigs if s.get("channel") == "research" or "research WAIVED" in str(s.get("msg"))]
    ev = [f"PhaseComplete in window: {len(phases)}  ResearchDiscovery: {len(research)}  waivers: {len(waivers)}"]
    for r in research[:4]:
        ev.append(f"  research run_id={r.get('run_id')} feature={str(r.get('feature'))[:50]}")
    if not phases:
        return NA, "no postflight in window - session did not close", ev
    rruns = {r.get("run_id") for r in research if r.get("run_id")}
    unmatched = [p for p in phases if p.get("run_id") not in rruns]
    for p in unmatched[:4]:
        ev.append(f"  UNMATCHED phase run_id={p.get('run_id')} phase={str(p.get('phase'))[:50]}")
    if not unmatched:
        return PASS, f"every postflight ({len(phases)}) carries its OWN research node", ev
    if waivers:
        return PASS, f"{len(unmatched)} postflight(s) without research, but waived (reasoned skip)", ev
    return FAIL, (f"{len(unmatched)}/{len(phases)} postflight(s) recorded NO research of their own "
                  f"(the 8h lookback let them sail through)"), ev


def check_seed_task_not_abandoned(win_nodes, sigs, win):
    """Rule 7: a 'Build toward the seed' task's PREMISE is absence - absence IS the
    work. Releasing it re-queues the studio's top gap forever. Also: a release/block
    with an empty reason is forbidden."""
    from core.task_board import _read_state
    tasks = {t.get("id"): t for t in (_read_state().get("tasks") or [])}
    ev, bad = [], []
    for s in sigs:
        msg = str(s.get("msg") or "")
        if s.get("source") != "task_board":
            continue
        if " released tb-" not in msg and " blocked tb-" not in msg:
            continue
        ev.append(f"capcom {s.get('ts_iso')} {msg[:100]}")
        tid = ""
        for tok in msg.split():
            if tok.startswith("tb-"):
                tid = tok.rstrip(":")
                break
        title = str((tasks.get(tid) or {}).get("title", ""))
        reason = msg.split(":", 1)[1].strip() if ":" in msg else ""
        if title.lower().startswith("build toward the seed"):
            bad.append(f"{tid} is a BUILD task ('{title[:52]}') released - absence IS the work")
        if not reason:
            bad.append(f"{tid} released/blocked with an EMPTY reason")
    bad = list(dict.fromkeys(bad))          # same task released N times = ONE finding
    open_seed = [t for t in tasks.values()
                 if str(t.get("title", "")).lower().startswith("build toward the seed")
                 and t.get("status") == "open"]
    ev.append(f"'Build toward the seed' tasks still open: {len(open_seed)}"
              + (f" (e.g. {open_seed[0].get('id')} {str(open_seed[0].get('title'))[:44]})" if open_seed else ""))
    if bad:
        return FAIL, "; ".join(bad[:3]), ev
    return PASS, "no seed/build task abandoned; no empty release reasons", ev


def check_committed_with_sha(win_nodes, sigs, win):
    """Rule 12: state the SHA - a session that ends with no SHA did not happen.
    Untracked artifacts get swept into a generic auto-flush and lose provenance."""
    raw = _git("log", f"--since={win['start_iso']}Z", f"--until={win['end_iso']}Z",
               "--format=%h|%s")
    commits = [l for l in raw.splitlines() if l.strip()]
    real = [c for c in commits if "auto-flush" not in c.lower()]
    ev = [f"commits in window: {len(commits)} (real: {len(real)}, auto-flush: {len(commits)-len(real)})"]
    ev += [f"  {c[:96]}" for c in commits[:6]]
    # `git status` has no history: untracked files are a NOW fact, so they only
    # indict a session whose window ends about now (else you blame it for someone
    # else's mess - including your own).
    arts = []
    if (time.time() - win["end"]) < 900:
        untracked = [l[3:] for l in _git("status", "--porcelain").splitlines() if l.startswith("??")]
        arts = [u for u in untracked if u.endswith((".json", ".md", ".py", ".cpp", ".h"))]
        if arts:
            ev.append(f"UNTRACKED artifacts left behind: {len(arts)} (e.g. {', '.join(arts[:3])})")
    else:
        ev.append("untracked files NOT consulted (historical window)")
    if not real:
        return FAIL, "no real commit in window (only auto-flush, or nothing) - no SHA to state", ev
    if arts:
        return FAIL, f"committed ({len(real)}) but left {len(arts)} untracked artifact(s)", ev
    return PASS, f"{len(real)} real commit(s), tree clean of artifacts", ev


def check_postflight_once(win_nodes, sigs, win):
    """Postflight ONCE per phase - a second run writes a duplicate PhaseComplete."""
    phases = [n for n in win_nodes if n.get("type") == "PhaseComplete"]
    c = Counter(str(n.get("phase")) for n in phases)
    dupes = {k: v for k, v in c.items() if v > 1}
    ev = [f"{n} x  {p[:78]}" for p, n in c.most_common(6)]
    if not phases:
        return NA, "no postflight in window", ev
    if dupes:
        return FAIL, f"{len(dupes)} phase(s) postflighted more than once (duplicate nodes)", ev
    return PASS, f"{len(phases)} phase(s), each postflighted exactly once", ev


def check_instrument_used(win_nodes, sigs, win):
    """INFORMATIONAL - the prompt asks the agent to report a gate that passes
    UNEARNED (`capcom tell "GATE DEFECT: ..."`). Finding one is the instrument
    WORKING, not a failure; absence just means nothing was reported."""
    hits = [s for s in sigs if "GATE DEFECT" in str(s.get("msg", "")).upper()]
    ev = [f"capcom {s.get('ts_iso')} {str(s.get('msg'))[:100]}" for s in hits[:4]]
    if hits:
        return PASS, f"{len(hits)} GATE DEFECT report(s) - the agent used the instrument", ev
    return NA, "no GATE DEFECT reported (nothing observed, or nothing noticed)", ev


REQUIRED = [
    ("DS4_UP", "r11", check_ds4_up),
    ("RESEARCH_SCOPED", "r9", check_research_scoped),
    ("SEED_TASK_KEPT", "r7", check_seed_task_not_abandoned),
    ("COMMITTED_SHA", "r12", check_committed_with_sha),
    ("POSTFLIGHT_ONCE", "III.6", check_postflight_once),
]
INFORMATIONAL = [
    ("GATE_DEFECT_REPORTED", "WHAT MATTERS", check_instrument_used),
]


def _context(win_nodes, sigs):
    lines = []
    c = Counter(str(n.get("type")) for n in win_nodes)
    lines.append("  nodes: " + (", ".join(f"{k}x{v}" for k, v in c.most_common(8)) or "none"))
    board = [s for s in sigs if s.get("source") == "task_board"]
    lines.append(f"  board signals: {len(board)}")
    for s in board[:6]:
        lines.append(f"    {s.get('ts_iso')} {str(s.get('msg'))[:86]}")
    return lines


def run(hours=6.0, since="", until="", as_json=False):
    win = _window(hours, since, until)
    win_nodes = _graph_nodes(win)
    sigs = _signals(win)

    results = []
    for name, rule, fn in REQUIRED + INFORMATIONAL:
        try:
            status, detail, ev = fn(win_nodes, sigs, win)
        except Exception as e:               # a broken check must not read as a pass
            status, detail, ev = FAIL, f"check errored: {type(e).__name__}: {e}", []
        results.append({"check": name, "rule": rule, "status": status,
                        "detail": detail, "evidence": ev,
                        "required": (name, rule, fn) in REQUIRED})

    failed = [r for r in results if r["required"] and r["status"] == FAIL]
    unproven = [r for r in results if r["required"] and r["status"] == NA]

    if as_json:
        print(json.dumps({"window_start_utc": win["start_iso"], "window_end_utc": win["end_iso"],
                          "nodes": len(win_nodes), "signals": len(sigs), "results": results,
                          "verdict": "PASS" if not failed else "FAIL"}, indent=2))
        return 0 if not failed else 1

    print("=" * 78)
    print("ONBOARDING AUDIT - did the agent FOLLOW the system? (records, not its summary)")
    print(f"window: {win['start_iso']}Z .. {win['end_iso']}Z"
          f"   nodes={len(win_nodes)}  signals={len(sigs)}")
    print("=" * 78)
    print("\nSESSION CONTEXT")
    for l in _context(win_nodes, sigs):
        print(l)
    print("\nREQUIRED CHECKPOINTS")
    for r in results:
        if not r["required"]:
            continue
        mark = {PASS: "[PASS]", FAIL: "[FAIL]", NA: "[ n/a]"}[r["status"]]
        print(f"\n{mark} {r['check']:<18} ({r['rule']})  {r['detail']}")
        for e in r["evidence"][:6]:
            print(f"         {e}")
    print("\nINFORMATIONAL")
    for r in results:
        if r["required"]:
            continue
        print(f"\n[{r['status']:>4}] {r['check']:<18} ({r['rule']})  {r['detail']}")
        for e in r["evidence"][:4]:
            print(f"         {e}")
    print("\n" + "=" * 78)
    if failed:
        print(f"VERDICT: FAIL - {len(failed)} required checkpoint(s) missed: "
              f"{', '.join(r['check'] for r in failed)}")
        print("The PROMPT did not carry these. Either sharpen it, or (if it says the")
        print("right thing plainly and was still ignored) the GATE must enforce it.")
    else:
        print("VERDICT: PASS - every required checkpoint hit."
              + (f"  ({len(unproven)} unproven: {', '.join(r['check'] for r in unproven)})" if unproven else ""))
    print("=" * 78)
    return 0 if not failed else 1


def main(argv=None):
    p = argparse.ArgumentParser(prog="onboarding_audit",
                                description="Score a session against the MASTER_ONBOARDING checkpoints (read-only).")
    p.add_argument("--hours", type=float, default=6.0, help="window size back from --until (default 6)")
    p.add_argument("--since", default="", help="UTC ISO start instead of --hours")
    p.add_argument("--until", default="", help="UTC ISO end (default: now). Bound the window to "
                                               "score ONE session - revisions are compared session-vs-session.")
    p.add_argument("--json", action="store_true", dest="as_json")
    a = p.parse_args(argv)
    return run(hours=a.hours, since=a.since, until=a.until, as_json=a.as_json)


if __name__ == "__main__":
    sys.exit(main())
