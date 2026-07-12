"""
Agent Tunnel — one entrance, one exit for every parallel agent.

Problem
-------
The task board decides WHAT can run in parallel and the editor scheduler
arbitrates the one shared device, but the lifecycle BETWEEN them is manual
ritual: claim, request the editor in the right mode, fetch the study guide,
find which constitution heuristics apply, heartbeat two schedulers, exit with
evidence, release everything. Every forgotten step is a recorded failure class
(H-2, H-7, H-14 exist because agents improvised the ritual).

Solution
--------
Route agents through a tunnel:

    enter  -> claim a parallel-safe task, acquire the editor in the task's
              declared mode (the resource footprint IS the reservation),
              assemble a WORK PACKET (task + recipe + matching H-heuristics
              from CLAUDE.md + study guide from the DNA graph + open phantom
              pains + MCP traps that mention the feature), write a session
              record.
    heartbeat -> refresh BOTH the board claim and the editor lock in one call.
    exit   -> done requires verbatim evidence / blocked requires a reason
              (board-enforced), the editor is released, and a prefilled
              postflight command is printed so recording is copy-paste.

Nothing here invents policy: claiming is task_board's, editor arbitration is
editor_scheduler's, recording stays graphify's. The tunnel only sequences them
so a weak session cannot skip a wall.

Usage
-----
    python -m core.agent_tunnel enter --agent a1 [--capable] [--task tb-N] [--json]
    python -m core.agent_tunnel heartbeat --agent a1
    python -m core.agent_tunnel exit --agent a1 --outcome done --result "<UBT verbatim>"
    python -m core.agent_tunnel exit --agent a1 --outcome blocked --reason "..."
    python -m core.agent_tunnel exit --agent a1 --outcome release [--note "..."]
    python -m core.agent_tunnel status
"""

import fnmatch
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

HERE = Path(__file__).parent
ROOT = HERE.parent
SESSIONS_DIR = Path(os.environ.get("CHIMERA_TUNNEL_SESSIONS", HERE / "tunnel_sessions"))
CONSTITUTION = ROOT.parent / "CLAUDE.md"
MCP_PATHWAYS = ROOT / "docs" / "MCP_PATHWAYS.md"

try:
    from core.task_board import (claim_task, complete_task, block_task, release_task,
                                 get_state as board_state, heartbeat as board_heartbeat)
    from core.editor_scheduler import (request_editor, release_editor,
                                       heartbeat as editor_heartbeat)
except ImportError:
    sys.path.insert(0, str(HERE))
    from task_board import (claim_task, complete_task, block_task, release_task,
                            get_state as board_state, heartbeat as board_heartbeat)
    from editor_scheduler import (request_editor, release_editor,
                                  heartbeat as editor_heartbeat)

_STOPWORDS = {"with", "this", "that", "from", "into", "python", "core", "the",
              "and", "for", "task", "feature", "recipe", "fetch", "study",
              "guide", "json", "print", "import", "research"}


def _tokens(*texts) -> set:
    """Keyword tokens for relevance matching: alnum runs >= 4 chars, minus noise."""
    toks = set()
    for t in texts:
        for w in re.split(r"[^a-zA-Z0-9]+", (t or "").lower()):
            if len(w) >= 4 and w not in _STOPWORDS:
                toks.add(w)
    return toks


def _match_lines(text: str, tokens: set, must_contain: str = None, cap: int = 6) -> list:
    """Lines of ``text`` that mention any token (optionally filtered to lines
    containing ``must_contain``), ranked by distinct-token hits."""
    scored = []
    for line in (text or "").splitlines():
        if must_contain and must_contain not in line:
            continue
        low = line.lower()
        hits = sum(1 for t in tokens if t in low)
        if hits:
            scored.append((hits, line.strip()))
    scored.sort(key=lambda x: -x[0])
    return [l for _, l in scored[:cap]]


def _relevant_heuristics(tokens: set) -> list:
    """Constitution H-rules whose text mentions the task's keywords."""
    try:
        text = CONSTITUTION.read_text(encoding="utf-8")
    except OSError:
        return []
    h_lines = [l for l in text.splitlines() if "**[H-" in l]
    return _match_lines("\n".join(h_lines), tokens, cap=6)


def _relevant_traps(tokens: set) -> list:
    try:
        text = MCP_PATHWAYS.read_text(encoding="utf-8")
    except OSError:
        return []
    return [l[:220] for l in _match_lines(text, tokens, must_contain="TRAP", cap=4)]


def _graph_context(feature: str, tokens: set) -> dict:
    """Study guide (latest node parameters for the feature) + open phantom pains
    that mention the task's keywords. Best-effort: a missing graph never blocks
    the tunnel."""
    out = {"study_guide": None, "open_pains": []}
    try:
        from core.graphify_interface import load_dna_graph, collect_inheritance
    except ImportError:
        from graphify_interface import load_dna_graph, collect_inheritance
    try:
        nodes = load_dna_graph().get("nodes", [])
    except Exception:
        return out
    if feature:
        def _param_feature(n):
            p = n.get("parameters")
            return p.get("feature") if isinstance(p, dict) else None
        cands = [n for n in nodes
                 if feature in (n.get("feature_name"), n.get("feature"), n.get("name"),
                                _param_feature(n))]
        cands.sort(key=lambda n: n.get("timestamp", ""))
        for n in reversed(cands):
            params = n.get("parameters")
            if isinstance(params, dict) and params:
                out["study_guide"] = json.dumps(params, default=str, indent=1)[:1500]
                break
    try:
        pains = collect_inheritance(nodes).get("open_pains", [])
        out["open_pains"] = [f"{p.get('id')}: {str(p.get('text'))[:140]}"
                             for p in pains
                             if any(t in str(p.get("text", "")).lower() for t in tokens)][:4]
    except Exception:
        pass
    return out


EXIT_CONTRACT = (
    "EXIT CONTRACT: `exit --outcome done` demands --result with VERBATIM evidence "
    "(UBT output / test counts / read-backs — never a summary). `blocked` demands "
    "--reason naming the cause (bare 'blocked' forbidden — run core.solver first). "
    "Before done, answer the Frame Audit (docs/RESULT_GRADING_RUBRIC.md): is the "
    "evidence the TARGET or a proxy? who judged it? did you fix the generator or "
    "the artifact? Record via record_* helpers; the tunnel prints your postflight."
)


def _session_path(agent_id: str) -> Path:
    return SESSIONS_DIR / f"{agent_id}.json"


def _write_session(data: dict):
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    _session_path(data["agent"]).write_text(json.dumps(data, indent=2), encoding="utf-8")


def _read_session(agent_id: str):
    p = _session_path(agent_id)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------
def tend() -> list:
    """Close tunnel sessions whose board claim has vanished (heartbeat-reaped or
    settled behind the agent's back): release their editor lock, mark the session
    ``abandoned``. Runs on every enter, so the pool self-cleans at exactly the
    moment someone new walks in. Returns the sessions it closed."""
    state = board_state()  # reaps stale board claims as a side effect
    live = {(t.get("claimed_by"), t["id"]) for t in state["tasks"]
            if t["status"] == "claimed"}
    closed = []
    for sess in active_sessions():
        if (sess["agent"], sess["task_id"]) not in live:
            if sess.get("editor_held"):
                try:
                    release_editor(sess["agent"])
                except Exception:
                    pass
            sess.update({"exited_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                         "outcome": "abandoned"})
            _write_session(sess)
            closed.append(sess)
    return closed


def _offenders_from_porcelain(porcelain: str, scopes: list) -> list:
    """Modified working-tree paths that fall outside the declared file scopes.
    Pure function (testable); paths are matched both repo-relative and with the
    leading ``Chimera/`` stripped, since scopes are Chimera-relative."""
    if not scopes:
        return []
    offenders = []
    for line in (porcelain or "").splitlines():
        path = line[3:].strip().strip('"').replace("\\", "/")
        if not path:
            continue
        rel = path[len("Chimera/"):] if path.startswith("Chimera/") else path
        if not any(fnmatch.fnmatch(rel, g) or fnmatch.fnmatch(path, g)
                   or rel.startswith(g.split("*")[0]) for g in scopes):
            offenders.append(path)
    return offenders[:8]


def _footprint_warnings(task: dict) -> list:
    """Warn (never block) when the working tree holds changes outside the task's
    declared footprint. Parallel agents dirty their own lanes, so out-of-scope
    paths may be someone else's live work — the warning is a containment signal,
    not an accusation."""
    scopes = (task.get("resources") or {}).get("files") or []
    if not scopes:
        return []
    try:
        porcelain = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT.parent,
                                   capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return []
    return _offenders_from_porcelain(porcelain, scopes)


def enter(agent_id: str, task_id: str = None, capable: bool = False,
          editor_timeout: float = 120.0, assemble: bool = True):
    """Claim work + acquire the editor + assemble the packet. Returns the packet
    dict, or None when the board has no parallel-safe work. Raises the board's
    refusal (with reason) for an explicit --task that conflicts."""
    tend()
    existing = _read_session(agent_id)
    if existing and not existing.get("exited_at"):
        raise ValueError(f"{agent_id} already has an open tunnel session on "
                         f"{existing.get('task_id')} — exit it first")
    task = claim_task(agent_id, task_id=task_id, capable=capable)
    if task is None:
        return None

    mode = (task.get("resources") or {}).get("editor", "none")
    editor_held = False
    if mode in ("open", "closed"):
        if not request_editor(mode, agent_id, timeout=editor_timeout):
            # A claim we cannot work blocks everyone else's frontier — put it back.
            release_task(agent_id, task["id"],
                         note=f"tunnel: editor '{mode}' not granted in {editor_timeout}s")
            raise TimeoutError(
                f"editor '{mode}' not granted within {editor_timeout}s — claim on "
                f"{task['id']} released; retry when the editor frees up")
        editor_held = True

    packet = {
        "agent": agent_id,
        "task": {k: task[k] for k in ("id", "title", "recipe", "feature", "loop",
                                      "priority", "resources", "capable_only")},
        "editor_held": editor_held,
        "editor_mode": mode,
        "exit_contract": EXIT_CONTRACT,
    }
    if assemble:
        toks = _tokens(task.get("title"), task.get("feature"), task.get("recipe"))
        packet["heuristics"] = _relevant_heuristics(toks)
        packet["mcp_traps"] = _relevant_traps(toks)
        packet.update(_graph_context(task.get("feature"), toks))

    _write_session({"agent": agent_id, "task_id": task["id"], "task_title": task["title"],
                    "editor_mode": mode, "editor_held": editor_held,
                    "entered_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "exited_at": None, "outcome": None})
    return packet


def tunnel_heartbeat(agent_id: str) -> dict:
    """One call refreshes the board claim AND the editor lock."""
    refreshed = {"board_claims": board_heartbeat(agent_id), "editor": False}
    sess = _read_session(agent_id)
    if sess and sess.get("editor_held") and not sess.get("exited_at"):
        refreshed["editor"] = editor_heartbeat(agent_id)
    return refreshed


def exit_tunnel(agent_id: str, outcome: str, result: str = "", reason: str = "",
                note: str = "") -> dict:
    """Finish the session: settle the board task, release the editor, return
    what happened (including the prefilled postflight command)."""
    sess = _read_session(agent_id)
    if not sess or sess.get("exited_at"):
        raise ValueError(f"no open tunnel session for {agent_id}")
    tid = sess["task_id"]
    warnings = []
    if outcome == "done":
        task = complete_task(agent_id, tid, result=result)      # demands evidence
        warnings = _footprint_warnings(task)
    elif outcome == "blocked":
        task = block_task(agent_id, tid, reason=reason)         # demands a cause
    elif outcome == "release":
        task = release_task(agent_id, tid, note=note or "tunnel release")
    else:
        raise ValueError("outcome must be done|blocked|release")

    if sess.get("editor_held"):
        release_editor(agent_id)

    sess.update({"exited_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "outcome": outcome, "footprint_warnings": warnings})
    _write_session(sess)

    evidence = result or reason or note or "..."
    postflight = (f'python -m core.postflight --phase "{sess["task_title"]}" '
                  f'--result "{evidence[:200]}" --inheritance "<=3 sentences" '
                  f'--phantom-pain "<declare one>" --pain-verdict "<id>:still-open"')
    return {"task": task, "outcome": outcome, "postflight": postflight,
            "footprint_warnings": warnings}


def active_sessions() -> list:
    if not SESSIONS_DIR.exists():
        return []
    out = []
    for p in sorted(SESSIONS_DIR.glob("*.json")):
        try:
            s = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not s.get("exited_at"):
            out.append(s)
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _print_packet(packet: dict):
    t = packet["task"]
    print(f"# TUNNEL PACKET — {t['id']} for {packet['agent']}")
    print(f"\n**{t['title']}**  (priority {t.get('priority')}, "
          f"feature {t.get('feature') or '—'}, editor {packet['editor_mode']}"
          f"{', HELD' if packet['editor_held'] else ''})")
    print(f"\n## Recipe\n{t['recipe']}")
    r = t.get("resources") or {}
    print(f"\n## Your resource footprint (stay inside it)")
    print(f"  files: {', '.join(r.get('files') or ['(none declared)'])}")
    if r.get("exclusive"):
        print(f"  exclusive: {', '.join(r['exclusive'])}")
    if packet.get("heuristics"):
        print("\n## Constitution heuristics that mention this work")
        for h in packet["heuristics"]:
            print(f"  {h}")
    if packet.get("mcp_traps"):
        print("\n## MCP traps near this work")
        for tr in packet["mcp_traps"]:
            print(f"  {tr}")
    if packet.get("study_guide"):
        print(f"\n## Study guide (latest graph parameters)\n{packet['study_guide']}")
    if packet.get("open_pains"):
        print("\n## Open phantom pains touching this area")
        for pn in packet["open_pains"]:
            print(f"  {pn}")
    print(f"\n## Exit\n{packet['exit_contract']}")
    print(f"\nheartbeat: python -m core.agent_tunnel heartbeat --agent {packet['agent']}")
    print(f"exit:      python -m core.agent_tunnel exit --agent {packet['agent']} "
          f"--outcome done --result \"<verbatim evidence>\"")


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description="Agent tunnel: enter -> work -> exit")
    sub = p.add_subparsers(dest="cmd", required=True)

    pe = sub.add_parser("enter", help="Claim + acquire editor + print the work packet")
    pe.add_argument("--agent", default=None, help="default: tunnel-<8hex>")
    pe.add_argument("--task", default=None, help="specific tb-N (default: best parallel-safe)")
    pe.add_argument("--capable", action="store_true")
    pe.add_argument("--editor-timeout", type=float, default=120.0)
    pe.add_argument("--json", action="store_true")

    ph = sub.add_parser("heartbeat")
    ph.add_argument("--agent", required=True)

    px = sub.add_parser("exit")
    px.add_argument("--agent", required=True)
    px.add_argument("--outcome", choices=["done", "blocked", "release"], required=True)
    px.add_argument("--result", default="")
    px.add_argument("--reason", default="")
    px.add_argument("--note", default="")

    sub.add_parser("status", help="Active tunnel sessions")
    sub.add_parser("tend", help="Close sessions whose claim vanished; free their editor")

    args = p.parse_args(argv)
    if args.cmd == "enter":
        agent = args.agent or f"tunnel-{uuid4().hex[:8]}"
        try:
            packet = enter(agent, task_id=args.task, capable=args.capable,
                           editor_timeout=args.editor_timeout)
        except (KeyError, ValueError, TimeoutError) as e:
            print(f"REFUSED: {e}")
            sys.exit(1)
        if packet is None:
            print("NONE (no parallel-safe open task — `python -m core.task_board list`)")
            sys.exit(2)
        if args.json:
            print(json.dumps(packet, indent=2, default=str))
        else:
            _print_packet(packet)
    elif args.cmd == "heartbeat":
        print(json.dumps(tunnel_heartbeat(args.agent)))
    elif args.cmd == "exit":
        try:
            out = exit_tunnel(args.agent, args.outcome, result=args.result,
                              reason=args.reason, note=args.note)
        except (KeyError, ValueError) as e:
            print(f"REFUSED: {e}")
            sys.exit(1)
        print(f"{args.outcome.upper()}: {out['task']['id'] if out['task'] else '—'}")
        for w in out.get("footprint_warnings", []):
            print(f"  !! outside your footprint: {w} (yours? widen the task's files; "
                  f"another agent's? ignore)")
        print(f"record it: {out['postflight']}")
    elif args.cmd == "tend":
        closed = tend()
        print(f"tended: closed {len(closed)} abandoned session(s)")
        for s in closed:
            print(f"  {s['agent']} was in {s['task_id']} ({s['task_title'][:50]})")
    elif args.cmd == "status":
        sessions = active_sessions()
        if not sessions:
            print("no active tunnel sessions")
        for s in sessions:
            print(f"  {s['agent']}  {s['task_id']}  {s['task_title'][:52]}  "
                  f"editor:{s['editor_mode']}{' HELD' if s.get('editor_held') else ''}  "
                  f"since {s['entered_at']}")


if __name__ == "__main__":
    main()
