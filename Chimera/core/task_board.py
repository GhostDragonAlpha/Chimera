"""
Task Board — a parallel-safe task list for concurrent agents.

Problem
-------
task_progress.md hands every agent the SAME single rehearsal-chosen NEXT item,
so parallel agents duplicate work or collide on shared resources (module DLL,
PIE session, the same generated files). The editor_scheduler serializes editor
access at runtime, but nothing prevents two agents from *choosing* colliding
work in the first place.

Solution
--------
A file-locked board (same advisory-lock + heartbeat pattern as
editor_scheduler). Every task declares its RESOURCE FOOTPRINT:

    resources: {
        "files":     ["Source/Chimera/ProceduralGenerated/Sound/**"],  # glob scopes
        "editor":    "none" | "open" | "closed",                       # mode needed
        "exclusive": ["pie", "build", "level:L_RegolithYard"],         # named locks
    }

``claim`` only grants a task whose footprint is DISJOINT from every active
claim, so agents that pull from the board can genuinely run in parallel.
Conflict rules (conservative on purpose — a false conflict costs queueing,
a missed conflict costs a corrupted build):

  - same ``feature``                          -> conflict (duplicate work)
  - file scopes overlap (literal-prefix test) -> conflict
  - shared ``exclusive`` name                 -> conflict
  - editor 'closed' vs 'open' or 'closed'     -> conflict ('open'+'open' is fine;
    concurrent PIE is what the 'pie' exclusive is for)

Claims carry a heartbeat; a claim whose owner goes silent past the TTL is
reaped back to open, so a crashed agent can never wedge a task forever.
Runtime editor contention is still the editor_scheduler's job — the board
prevents agents from *picking* clashing work; the scheduler arbitrates the
editor itself.

State lives in core/task_board_state.json (gitignored, single-machine
coordination state like the editor scheduler's). docs/TASK_BOARD.md is a
regenerated human-readable snapshot. Durable history belongs in the DNA
graph via the normal record_* helpers, not here.

Usage (in code)
---------------
    from core.task_board import claim_task, complete_task, heartbeat
    agent_id = f"agent-{uuid4().hex[:8]}"
    task = claim_task(agent_id)              # best parallel-safe open task, or None
    ... do task["recipe"] ...
    complete_task(agent_id, task["id"], result="UBT pass; sim 5/5 beats")

CLI
---
    python -m core.task_board seed                          # bootstrap from rehearsal + graph
    python -m core.task_board add --title X --recipe "..." --files "docs/research/**" --editor none
    python -m core.task_board claim --agent a1 [--id tb-3] [--capable]
    python -m core.task_board done --agent a1 --id tb-3 --result "..."
    python -m core.task_board block --agent a1 --id tb-3 --reason "..."
    python -m core.task_board release --agent a1 --id tb-3 [--note "..."]
    python -m core.task_board heartbeat --agent a1
    python -m core.task_board list [--all]
    python -m core.task_board state
"""

import fnmatch
import functools
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

HERE = Path(__file__).parent
ROOT = HERE.parent

# Env overrides so forks/tests never touch live state (fork invariant).
STATE_PATH = Path(os.environ.get("CHIMERA_TASK_BOARD_STATE", HERE / "task_board_state.json"))
LOCK_PATH = Path(os.environ.get("CHIMERA_TASK_BOARD_LOCK", HERE / "task_board.lock"))
BOARD_MD = ROOT / "docs" / "TASK_BOARD.md"
CLAIM_TTL = float(os.environ.get("CHIMERA_TASK_CLAIM_TTL", 7200))  # 2h; tasks are coarse

OPEN, CLAIMED, DONE, BLOCKED, ABANDONED = "open", "claimed", "done", "blocked", "abandoned"
EDITOR_MODES = ("none", "open", "closed")

# ---------------------------------------------------------------------------
# Cross-platform advisory file lock (same pattern as editor_scheduler; held
# only briefly around state reads/writes).
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


# ---------------------------------------------------------------------------
# State read/write — atomic replace + .bak fallback. Unlike the editor
# scheduler, losing this state means losing the whole task list, so a crash
# mid-write must never leave a half-written file as the only copy.
# ---------------------------------------------------------------------------
def _empty_state():
    return {"next_id": 1, "tasks": []}


def _read_state():
    for path in (STATE_PATH, STATE_PATH.with_suffix(".json.bak")):
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
    return _empty_state()


def _write_state(state):
    tmp = STATE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    if STATE_PATH.exists():
        try:
            STATE_PATH.replace(STATE_PATH.with_suffix(".json.bak"))
        except Exception:
            pass
    tmp.replace(STATE_PATH)


def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------------------
# Conflict predicate
# ---------------------------------------------------------------------------
def _glob_prefix(g: str) -> str:
    """Literal directory prefix of a glob (everything before the first wildcard)."""
    g = g.replace("\\", "/").lstrip("./")
    for i, ch in enumerate(g):
        if ch in "*?[":
            return g[:i]
    return g


def _globs_overlap(a: str, b: str) -> bool:
    """Conservative overlap test: literal prefixes nest, or either full glob
    matches the other's prefix. Over-detects same-directory patterns like
    ``Sound/*.h`` vs ``Sound/*.cpp`` — acceptable, conflicts must err safe."""
    pa, pb = _glob_prefix(a), _glob_prefix(b)
    if pa.startswith(pb) or pb.startswith(pa):
        return True
    na, nb = a.replace("\\", "/"), b.replace("\\", "/")
    return fnmatch.fnmatch(pb.rstrip("/"), na) or fnmatch.fnmatch(pa.rstrip("/"), nb)


def _resources(task: dict) -> dict:
    r = task.get("resources") or {}
    return {
        "files": list(r.get("files") or []),
        "editor": r.get("editor") or "none",
        "exclusive": list(r.get("exclusive") or []),
    }


def tasks_conflict(a: dict, b: dict) -> Optional[str]:
    """Return a human-readable reason the two tasks cannot run in parallel,
    or None if their footprints are disjoint."""
    if a.get("feature") and a.get("feature") == b.get("feature"):
        return f"same feature ({a['feature']})"
    ra, rb = _resources(a), _resources(b)
    shared = set(ra["exclusive"]) & set(rb["exclusive"])
    if shared:
        return f"shared exclusive resource ({', '.join(sorted(shared))})"
    if "closed" in (ra["editor"], rb["editor"]) and \
            (ra["editor"], rb["editor"]) != ("closed", "none") and \
            (ra["editor"], rb["editor"]) != ("none", "closed"):
        return f"editor mode clash ({ra['editor']} vs {rb['editor']})"
    for ga in ra["files"]:
        for gb in rb["files"]:
            if _globs_overlap(ga, gb):
                return f"file scope overlap ({ga} ~ {gb})"
    return None


def _deps_done(task: dict, by_id: dict) -> bool:
    return all(by_id.get(d, {}).get("status") == DONE for d in task.get("depends_on", []))


def _capable_authorized(agent_id: str) -> bool:
    """capable_only lanes require the gauntlet's 'journeyman' role — earned, not
    self-declared. Credentials are read directly (no gauntlet import; it imports
    us). The human can always hand-grant: python -m core.gauntlet grant."""
    creds_path = Path(os.environ.get("CHIMERA_GAUNTLET_DIR",
                                     ROOT / "docs" / "gauntlet")) / "credentials.json"
    try:
        creds = json.loads(creds_path.read_text(encoding="utf-8"))
    except Exception:
        return False
    return "journeyman" in (creds.get(agent_id, {}).get("roles") or [])


def _reap_stale(state) -> list:
    """Reopen claims whose owner heartbeat exceeded the TTL. Returns reaped ids."""
    reaped = []
    now = time.time()
    for t in state["tasks"]:
        if t["status"] == CLAIMED and now - t.get("heartbeat", 0) > CLAIM_TTL:
            t["notes"].append({"ts": _now_iso(), "agent": "board",
                               "text": f"claim by {t.get('claimed_by')} reaped (heartbeat stale)"})
            t.update({"status": OPEN, "claimed_by": None, "claimed_at": 0, "heartbeat": 0})
            reaped.append(t["id"])
    return reaped


def _claimable(state, capable: bool) -> list:
    """Open tasks with satisfied deps that conflict with no ACTIVE claim,
    sorted by descending priority."""
    by_id = {t["id"]: t for t in state["tasks"]}
    active = [t for t in state["tasks"] if t["status"] == CLAIMED]
    out = []
    for t in state["tasks"]:
        if t["status"] != OPEN:
            continue
        if t.get("capable_only") and not capable:
            continue
        if not _deps_done(t, by_id):
            continue
        if any(tasks_conflict(t, c) for c in active):
            continue
        out.append(t)
    out.sort(key=lambda t: -t.get("priority", 1.0))
    return out


def parallel_frontier(state=None, capable: bool = True, limit: int = 10) -> list:
    """Greedy maximal set of open tasks that could all be claimed RIGHT NOW by
    different agents: each pick must be disjoint from active claims and from
    earlier picks. This is the board's headline number."""
    if state is None:
        state = get_state()
    picks = []
    for t in _claimable(state, capable):
        if not any(tasks_conflict(t, p) for p in picks):
            picks.append(t)
        if len(picks) >= limit:
            break
    return picks


# ---------------------------------------------------------------------------
# Mutations (all under the file lock)
# ---------------------------------------------------------------------------
def _locked(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        fd = _acquire_lock_fd()
        try:
            state = _read_state()
            _reap_stale(state)
            result = fn(state, *args, **kwargs)
            _write_state(state)
            return result
        finally:
            _release_lock_fd(fd)
    return wrapper


def _new_task(state, title: str, recipe: str, files=None, editor: str = "none",
              exclusive=None, feature: str = None, loop: int = None,
              priority: float = 1.0, depends_on=None, capable_only: bool = False,
              created_by: str = "manual", not_scope: dict = None) -> dict:
    """Append a task to an already-locked state. Callers hold the lock."""
    if editor not in EDITOR_MODES:
        raise ValueError(f"editor must be one of {EDITOR_MODES}, got {editor!r}")
    task = {
        "id": f"tb-{state['next_id']:04d}",
        "title": title,
        "recipe": recipe,
        "feature": feature,
        "loop": loop,
        "priority": float(priority),
        "capable_only": bool(capable_only),
        "status": OPEN,
        "resources": {"files": list(files or []), "editor": editor,
                      "exclusive": list(exclusive or [])},
        "depends_on": list(depends_on or []),
        "claimed_by": None, "claimed_at": 0, "heartbeat": 0,
        "created_at": _now_iso(), "created_by": created_by,
        "notes": [], "result": None,
    }
    if not_scope:
        task["not_scope"] = not_scope    # inversion boundary, printed at claim
    state["next_id"] += 1
    state["tasks"].append(task)
    return task


@_locked
def add_task(state, *args, **kwargs) -> dict:
    task = _new_task(state, *args, **kwargs)
    _render_md(state)
    return task


@_locked
def mark_superseded_by_decomposition(state, feature_or_id: str, dc_id: str) -> list:
    """The Decomposition Process's monolith guard: once a compound target is
    broken into parts, its bare-parent task can no longer be claimed — the
    parts get processed, never the system. Returns the tasks it blocked."""
    blocked = []
    for t in state["tasks"]:
        if t["status"] == OPEN and (t["id"] == feature_or_id
                                    or t.get("feature") == feature_or_id):
            t["status"] = BLOCKED
            t["notes"].append({"ts": _now_iso(), "agent": "decomposer",
                               "text": f"blocked: superseded by decomposition {dc_id} "
                                       f"— claim the parts, not the system"})
            blocked.append(t["id"])
    _render_md(state)
    return blocked


@_locked
def claim_task(state, agent_id: str, task_id: str = None, capable: bool = False):
    """Claim a specific task, or the best parallel-safe one. Returns the task
    dict or None. A refused specific claim raises with the conflict reason so
    the caller learns WHY instead of silently getting nothing."""
    if capable and not _capable_authorized(agent_id):
        raise ValueError(
            f"{agent_id} has no gauntlet credential for capable work — the only way "
            f"in is through: python -m core.gauntlet enter --agent {agent_id}")
    by_id = {t["id"]: t for t in state["tasks"]}
    active = [t for t in state["tasks"] if t["status"] == CLAIMED]
    if task_id:
        t = by_id.get(task_id)
        if t is None:
            raise KeyError(f"no such task {task_id}")
        if t["status"] != OPEN:
            raise ValueError(f"{task_id} is {t['status']}, not open")
        if t.get("capable_only") and not _capable_authorized(agent_id):
            # Explicit-id claims must not bypass the gauntlet (loophole found
            # live by preflight-checker-2 within minutes of the gate shipping).
            raise ValueError(
                f"{task_id} is capable_only and {agent_id} holds no journeyman "
                f"credential — python -m core.gauntlet enter --agent {agent_id}")
        if not _deps_done(t, by_id):
            raise ValueError(f"{task_id} has unmet dependencies: {t.get('depends_on')}")
        for c in active:
            reason = tasks_conflict(t, c)
            if reason:
                raise ValueError(f"{task_id} conflicts with {c['id']} "
                                 f"(claimed by {c['claimed_by']}): {reason}")
        pick = t
    else:
        options = _claimable(state, capable)
        if not options:
            return None
        pick = options[0]
    pick.update({"status": CLAIMED, "claimed_by": agent_id,
                 "claimed_at": time.time(), "heartbeat": time.time()})
    _render_md(state)
    return pick


def _finish(state, agent_id, task_id, status, text_field, text):
    by_id = {t["id"]: t for t in state["tasks"]}
    t = by_id.get(task_id)
    if t is None:
        raise KeyError(f"no such task {task_id}")
    if t["status"] == CLAIMED and t.get("claimed_by") != agent_id:
        raise ValueError(f"{task_id} is claimed by {t['claimed_by']}, not {agent_id}")
    t["status"] = status
    t[text_field] = text
    t["notes"].append({"ts": _now_iso(), "agent": agent_id, "text": f"{status}: {text}"})
    t.update({"claimed_by": None, "claimed_at": 0, "heartbeat": 0})
    _render_md(state)
    return t


@_locked
def complete_task(state, agent_id: str, task_id: str, result: str):
    if not (result or "").strip():
        raise ValueError("done requires --result (verbatim evidence, e.g. UBT output)")
    return _finish(state, agent_id, task_id, DONE, "result", result)


@_locked
def block_task(state, agent_id: str, task_id: str, reason: str):
    # Solver contract: bare 'blocked' is forbidden — a blocker names its cause.
    if not (reason or "").strip():
        raise ValueError("block requires --reason (bare 'blocked' is forbidden)")
    return _finish(state, agent_id, task_id, BLOCKED, "result", reason)


@_locked
def release_task(state, agent_id: str, task_id: str, note: str = ""):
    by_id = {t["id"]: t for t in state["tasks"]}
    t = by_id.get(task_id)
    if t is None:
        raise KeyError(f"no such task {task_id}")
    if t["status"] != CLAIMED or t.get("claimed_by") != agent_id:
        return None
    if note:
        t["notes"].append({"ts": _now_iso(), "agent": agent_id, "text": note})
    t.update({"status": OPEN, "claimed_by": None, "claimed_at": 0, "heartbeat": 0})
    _render_md(state)
    return t


@_locked
def heartbeat(state, agent_id: str) -> int:
    """Refresh every claim held by agent_id. Returns how many were refreshed."""
    n = 0
    for t in state["tasks"]:
        if t["status"] == CLAIMED and t.get("claimed_by") == agent_id:
            t["heartbeat"] = time.time()
            n += 1
    return n


@_locked
def reopen_task(state, agent_id: str, task_id: str, note: str = ""):
    """Reopen a blocked/abandoned task once its blocker is cleared."""
    by_id = {t["id"]: t for t in state["tasks"]}
    t = by_id.get(task_id)
    if t is None:
        raise KeyError(f"no such task {task_id}")
    if t["status"] not in (BLOCKED, ABANDONED):
        raise ValueError(f"{task_id} is {t['status']}; only blocked/abandoned reopen")
    t["status"] = OPEN
    t["notes"].append({"ts": _now_iso(), "agent": agent_id,
                       "text": f"reopened: {note or 'blocker cleared'}"})
    _render_md(state)
    return t


def get_state() -> dict:
    fd = _acquire_lock_fd()
    try:
        state = _read_state()
        if _reap_stale(state):
            _write_state(state)
        return state
    finally:
        _release_lock_fd(fd)


def reconcile_stale_pain_tasks() -> int:
    """Auto-close OPEN pain-verdict tasks whose pain already has a recorded
    verdict (pain phase_11103b6bf873a5df:P1, CONFIRMED live: after tb-0019
    refuted a pain, the board kept serving tb-0020/tb-0021 for its duplicates —
    already-answered questions). still-open verdicts stay claimable. Returns
    the number closed."""
    import re as _re
    state = get_state()
    candidates = [t for t in state["tasks"] if t["status"] == OPEN
                  and _re.search(r"phase_[0-9a-f]{6,}:P\d+",
                                 str(t.get("recipe", "")) + " " + str(t.get("title", "")))]
    if not candidates:
        return 0
    try:
        from core.graphify_interface import load_dna_graph, collect_inheritance
        open_ids = {p["id"] for p in
                    collect_inheritance(load_dna_graph().get("nodes", []))["open_pains"]}
    except Exception:
        return 0
    closed = 0
    for t in candidates:
        m = _re.search(r"phase_[0-9a-f]{6,}:P\d+",
                       str(t.get("recipe", "")) + " " + str(t.get("title", "")))
        if m and m.group(0) not in open_ids:
            try:
                complete_task("pain-reconciler", t["id"],
                              f"auto-closed: pain {m.group(0)} already dispositioned "
                              f"(verdict recorded in the DNA graph)")
                closed += 1
            except Exception:
                pass
    return closed


def board_summary() -> dict:
    """Cheap snapshot for preflight: counts + the current parallel frontier."""
    state = get_state()
    counts = {}
    for t in state["tasks"]:
        counts[t["status"]] = counts.get(t["status"], 0) + 1
    frontier = parallel_frontier(state, capable=True)
    claims = [(t["id"], t["title"], t["claimed_by"])
              for t in state["tasks"] if t["status"] == CLAIMED]
    return {"counts": counts, "frontier": frontier, "claims": claims,
            "total": len(state["tasks"])}


# ---------------------------------------------------------------------------
# Seeding — bootstrap the board from rehearsal's deterministic scoring plus
# pending technical_research. Idempotent: an existing non-done task with the
# same feature/title is never duplicated.
# ---------------------------------------------------------------------------
# Resource footprints for known feature families. Unknown features get the
# conservative whole-tree scope (correct but serial) — agents should narrow
# the scope when they know better.
_FEATURE_SCOPES = {
    "audio": {"files": ["Source/Chimera/ProceduralGenerated/Sound/**"],
              "editor": "open", "exclusive": ["pie"]},
    "sound": {"files": ["Source/Chimera/ProceduralGenerated/Sound/**"],
              "editor": "open", "exclusive": ["pie"]},
    "ground": {"files": ["Source/Chimera/ProceduralGenerated/Materials/**"],
               "editor": "open", "exclusive": ["pie"]},
    "dust": {"files": ["Source/Chimera/ProceduralGenerated/Materials/**"],
             "editor": "open", "exclusive": []},
    "verb": {"files": ["Source/Chimera/ProceduralGenerated/Interactions/**",
                       "Source/Chimera/ProceduralGenerated/Tools/**"],
             "editor": "open", "exclusive": ["pie"]},
    "sky": {"files": ["Source/Chimera/ProceduralGenerated/Sky/**"],
            "editor": "open", "exclusive": []},
}
_DEFAULT_SCOPE = {"files": ["Source/Chimera/ProceduralGenerated/**"],
                  "editor": "open", "exclusive": ["pie"]}


def _scope_for(name: str) -> dict:
    low = name.lower()
    for key, scope in _FEATURE_SCOPES.items():
        if key in low:
            return dict(scope)
    return dict(_DEFAULT_SCOPE)


@_locked
def _apply_seed(state, rows, research, created_by) -> list:
    """Dedup + insert atomically under the lock so concurrent seeders can't
    double-add. Graph loading stays OUTSIDE the lock (it is slow)."""
    live = {(t.get("feature") or t["title"]) for t in state["tasks"] if t["status"] != DONE}
    added = []
    for r in rows:
        name = r["name"]
        if name in live or r.get("score", 1.0) < 0.1:  # skip dead-end-demoted rows
            continue
        scope = _scope_for(name)
        added.append(_new_task(
            state, title=name, recipe=r.get("recipe", ""), feature=name,
            priority=r.get("score", 1.0), capable_only=r.get("capable_only", False),
            files=scope["files"], editor=scope["editor"], exclusive=scope["exclusive"],
            created_by=created_by))
        live.add(name)
    for text in research or []:
        title = f"Research: {text[:70]}"
        if title in live:
            continue
        added.append(_new_task(
            state, title=title,
            recipe=f"python -m core.spiral_forks --feature \"{text[:60]}\" --use-lm "
                   f"(3 briefs, winner proceeds); record findings via record_* helpers.",
            files=["docs/research/**"], editor="none", priority=0.8,
            created_by=created_by))
        live.add(title)
    if added:
        _render_md(state)
    return added


def seed_board(rows=None, research=None, created_by="seed") -> list:
    """Populate the board. rows: rehearsal-scored candidate dicts (injected in
    tests; loaded live otherwise). research: pending technical_research strings."""
    if rows is None or research is None:
        try:
            from core.graphify_interface import load_dna_graph
            from core.rehearsal import enumerate_candidates, score_candidates, apply_no_dead_ends
        except ImportError:
            sys.path.insert(0, str(HERE))
            from graphify_interface import load_dna_graph
            from rehearsal import enumerate_candidates, score_candidates, apply_no_dead_ends
        nodes = load_dna_graph().get("nodes", [])
        if rows is None:
            rows = apply_no_dead_ends(score_candidates(nodes, enumerate_candidates(nodes)), nodes)
        if research is None:
            research = [n.get("target_action", n.get("id", ""))
                        for n in nodes
                        if n.get("feature_type") == "technical_research"
                        and n.get("compilation_result") == "pending_discovery"]
    return _apply_seed(rows or [], research or [], created_by)


# ---------------------------------------------------------------------------
# Human-readable snapshot (docs/TASK_BOARD.md) — regenerated on mutations.
# ---------------------------------------------------------------------------
def _render_md(state):
    try:
        lines = [
            "# Task Board (generated — edit via `python -m core.task_board`, not by hand)",
            "",
            f"Updated {_now_iso()}. Claim work with "
            f"`python -m core.task_board claim --agent <your-id>`; the board only",
            "grants tasks whose resource footprint is disjoint from active claims,",
            "so claimed tasks are safe to run in parallel.",
            "",
        ]
        frontier = parallel_frontier(state, capable=True)
        lines.append(f"**Parallel frontier right now: {len(frontier)} task(s) "
                     f"can proceed simultaneously.**")
        lines.append("")
        order = {CLAIMED: 0, OPEN: 1, BLOCKED: 2, DONE: 3, ABANDONED: 4}
        lines.append("| id | status | pri | task | resources | agent / result |")
        lines.append("|---|---|---|---|---|---|")
        for t in sorted(state["tasks"], key=lambda t: (order.get(t["status"], 9),
                                                       -t.get("priority", 1.0))):
            r = _resources(t)
            res = "; ".join(filter(None, [
                ", ".join(r["files"][:2]) + ("…" if len(r["files"]) > 2 else ""),
                f"editor:{r['editor']}" if r["editor"] != "none" else "",
                f"excl:{','.join(r['exclusive'])}" if r["exclusive"] else "",
            ]))
            tail = t.get("claimed_by") or (t.get("result") or "")[:60]
            deps = f" ⇐ {','.join(t['depends_on'])}" if t.get("depends_on") else ""
            cap = " `capable`" if t.get("capable_only") else ""
            lines.append(f"| {t['id']} | {t['status']} | {t.get('priority', 1.0):.2g} "
                         f"| {t['title'][:60]}{cap}{deps} | {res} | {tail} |")
        BOARD_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except Exception:
        pass  # the snapshot is a courtesy; never fail a mutation over it


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _print_task(t):
    print(json.dumps(t, indent=2, default=str))


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description="Parallel task board for concurrent agents")
    sub = p.add_subparsers(dest="cmd", required=True)

    pa = sub.add_parser("add", help="Add a task")
    pa.add_argument("--title", required=True)
    pa.add_argument("--recipe", required=True)
    pa.add_argument("--files", default="", help="comma-separated glob scopes")
    pa.add_argument("--editor", choices=EDITOR_MODES, default="none")
    pa.add_argument("--exclusive", default="", help="comma-separated named locks (pie, build, level:X)")
    pa.add_argument("--feature", default=None)
    pa.add_argument("--loop", type=int, default=None)
    pa.add_argument("--priority", type=float, default=1.0)
    pa.add_argument("--depends", default="", help="comma-separated task ids")
    pa.add_argument("--capable-only", action="store_true")
    pa.add_argument("--agent", default="manual")

    pc = sub.add_parser("claim", help="Claim a task — THE single entry: opens your tunnel "
                                      "session, reserves the editor mode the task declares, "
                                      "prints the work packet")
    pc.add_argument("--agent", required=True)
    pc.add_argument("--id", default=None)
    pc.add_argument("--capable", action="store_true",
                    help="this session may take capable_only tasks")
    pc.add_argument("--raw", action="store_true",
                    help="bare claim only: no tunnel session, no editor, no packet")
    pc.add_argument("--editor-timeout", type=float, default=120.0)

    for name, extra in (("done", "result"), ("block", "reason")):
        px = sub.add_parser(name)
        px.add_argument("--agent", required=True)
        px.add_argument("--id", required=True)
        px.add_argument(f"--{extra}", required=True)

    pr = sub.add_parser("release", help="Put a claimed task back to open")
    pr.add_argument("--agent", required=True)
    pr.add_argument("--id", required=True)
    pr.add_argument("--note", default="")

    po = sub.add_parser("reopen", help="Reopen a blocked/abandoned task")
    po.add_argument("--agent", required=True)
    po.add_argument("--id", required=True)
    po.add_argument("--note", default="")

    ph = sub.add_parser("heartbeat")
    ph.add_argument("--agent", required=True)

    pl = sub.add_parser("list", help="Show the board")
    pl.add_argument("--all", action="store_true", help="include done/abandoned")

    sub.add_parser("state", help="Raw JSON state")
    ps = sub.add_parser("seed", help="Bootstrap from rehearsal candidates + pending research")
    ps.add_argument("--agent", default="seed")

    args = p.parse_args(argv)
    if args.cmd == "add":
        t = add_task(title=args.title, recipe=args.recipe,
                     files=[f.strip() for f in args.files.split(",") if f.strip()],
                     editor=args.editor,
                     exclusive=[e.strip() for e in args.exclusive.split(",") if e.strip()],
                     feature=args.feature, loop=args.loop, priority=args.priority,
                     depends_on=[d.strip() for d in args.depends.split(",") if d.strip()],
                     capable_only=args.capable_only, created_by=args.agent)
        _print_task(t)
    elif args.cmd == "claim":
        try:  # stale pain-verdict tasks are answered questions — close, don't serve
            _n_rec = reconcile_stale_pain_tasks()
            if _n_rec:
                print(f"[reconcile] auto-closed {_n_rec} stale pain-verdict task(s) "
                      f"(pain already dispositioned)")
        except Exception:
            pass
        if args.raw:
            try:
                t = claim_task(args.agent, task_id=args.id, capable=args.capable)
            except (KeyError, ValueError) as e:
                print(f"REFUSED: {e}")
                sys.exit(1)
            if t is None and not args.id:
                # THE WELLSPRING: an empty frontier is a signal, not an end state —
                # refill from helm gap / observation queue / red atoms, retry once.
                try:
                    from core.wellspring import replenish
                    _added = replenish()
                except Exception:
                    _added = []
                if _added:
                    print(f"[wellspring] board was dry -> seeded {len(_added)} task(s) "
                          f"from the steering organs; retrying claim")
                    t = claim_task(args.agent, task_id=None, capable=args.capable)
            if t is None:
                print("NONE (no parallel-safe open task; `list` shows what's claimed/blocked)")
                sys.exit(2)
            _print_task(t)
        else:
            # The task list is the single entry — a claim IS a tunnel enter.
            try:
                from core.agent_tunnel import enter, _print_packet
            except ImportError:
                from agent_tunnel import enter, _print_packet
            try:
                packet = enter(args.agent, task_id=args.id, capable=args.capable,
                               editor_timeout=args.editor_timeout)
            except (KeyError, ValueError, TimeoutError) as e:
                print(f"REFUSED: {e}")
                sys.exit(1)
            if packet is None and not args.id:
                # THE WELLSPRING: an empty frontier is a signal, not an end state.
                # The board cannot mean "nothing to do" while the seed is <100%
                # realized — refill from the steering organs and retry once.
                try:
                    from core.wellspring import replenish
                    _added = replenish()
                except Exception:
                    _added = []
                if _added:
                    print(f"[wellspring] board was dry -> seeded {len(_added)} task(s) "
                          f"from helm gap / observation queue / red atoms; retrying claim")
                    try:
                        packet = enter(args.agent, task_id=None, capable=args.capable,
                                       editor_timeout=args.editor_timeout)
                    except (KeyError, ValueError, TimeoutError) as e:
                        print(f"REFUSED: {e}")
                        sys.exit(1)
            if packet is None:
                print("NONE (no parallel-safe open task; `list` shows what's claimed/blocked)")
                sys.exit(2)
            _print_packet(packet)
            try:  # CAPCOM: announce the claim onto the operator channel
                from core.capcom import post_safe
                _ct = packet.get("task") or {}
                post_safe("board",
                          f"{args.agent} claimed {_ct.get('id', args.id or '?')}: "
                          f"{_ct.get('title', '')[:70]}", level="info", source="task_board")
            except Exception:
                pass
            # NOT-THIS: the task's inversion boundary — eliminated scope +
            # the feature's recorded eliminations. Hard negatives with
            # provenance; do not re-explore without new evidence.
            try:
                task = packet.get("task") or {}
                not_scope = task.get("not_scope") or {}
                elim_lines = []
                for sub, why in (not_scope.get("rationale") or {}).items():
                    elim_lines.append(f"x {sub}  — {why}")
                for sub in not_scope.get("subsystems") or []:
                    if sub not in (not_scope.get("rationale") or {}):
                        elim_lines.append(f"x {sub}")
                feat = task.get("feature")
                if feat:
                    from core.graphify_interface import load_dna_graph
                    for n in load_dna_graph().get("nodes", []):
                        if n.get("type") == "Elimination" and n.get("feature") == feat:
                            elim_lines.append(
                                f"x {n.get('boundary', '')[:70]}  "
                                f"— eliminated ({n.get('evidence_ref') or n.get('id')})")
                if elim_lines:
                    print("\nNOT THIS (eliminated / out of lane — needs NEW evidence to reopen):")
                    for line in elim_lines[:10]:
                        print(f"  {line}")
            except Exception:
                pass
    elif args.cmd in ("done", "block", "release"):
        # Exiting through the board closes the tunnel session too (releases the
        # editor, checks the footprint, prints the postflight command).
        try:
            from core.agent_tunnel import _read_session, exit_tunnel
        except ImportError:
            from agent_tunnel import _read_session, exit_tunnel
        sess = _read_session(args.agent)
        in_tunnel = (sess and not sess.get("exited_at") and sess.get("task_id") == args.id)
        outcome = {"done": "done", "block": "blocked", "release": "release"}[args.cmd]
        try:
            if in_tunnel:
                out = exit_tunnel(args.agent, outcome,
                                  result=getattr(args, "result", ""),
                                  reason=getattr(args, "reason", ""),
                                  note=getattr(args, "note", ""))
                print(f"{args.cmd.upper()}: {args.id} (tunnel exited)")
                for w in out.get("footprint_warnings", []):
                    print(f"  !! outside your footprint: {w}")
                print(f"record it: {out['postflight']}")
            elif args.cmd == "done":
                _print_task(complete_task(args.agent, args.id, args.result))
            elif args.cmd == "block":
                _print_task(block_task(args.agent, args.id, args.reason))
            else:
                t = release_task(args.agent, args.id, note=args.note)
                print("RELEASED" if t else "NOT_YOUR_CLAIM")
        except (KeyError, ValueError) as e:
            print(f"REFUSED: {e}")
            sys.exit(1)
        try:  # CAPCOM: announce the exit (reached only on success — refusals exit above)
            from core.capcom import post_safe
            _verb = {"done": "completed", "block": "BLOCKED", "release": "released"}[args.cmd]
            _detail = (getattr(args, "result", "") or getattr(args, "reason", "")
                       or getattr(args, "note", ""))
            post_safe("board", f"{args.agent} {_verb} {args.id}: {_detail[:80]}",
                      level=("warn" if args.cmd == "block" else "info"), source="task_board")
        except Exception:
            pass
    elif args.cmd == "reopen":
        _print_task(reopen_task(args.agent, args.id, note=args.note))
    elif args.cmd == "heartbeat":
        print(f"refreshed {heartbeat(args.agent)} claim(s)")
    elif args.cmd == "list":
        s = board_summary()
        state = get_state()
        print(f"Task board: {s['total']} task(s)  " +
              "  ".join(f"{k}:{v}" for k, v in sorted(s["counts"].items())))
        print(f"Parallel frontier: {len(s['frontier'])} task(s) can proceed simultaneously")
        hide = () if args.all else (DONE, ABANDONED)
        for t in state["tasks"]:
            if t["status"] in hide:
                continue
            r = _resources(t)
            res = "; ".join(filter(None, [
                ",".join(r["files"]) or None,
                f"editor:{r['editor']}" if r["editor"] != "none" else None,
                f"excl:{','.join(r['exclusive'])}" if r["exclusive"] else None]))
            who = f"  <- {t['claimed_by']}" if t["status"] == CLAIMED else ""
            print(f"  [{t['status']:>7}] {t['id']} p={t.get('priority', 1):.2g} "
                  f"{t['title'][:64]}{who}")
            if res:
                print(f"            {res}")
    elif args.cmd == "state":
        print(json.dumps(get_state(), indent=2))
    elif args.cmd == "seed":
        added = seed_board(created_by=args.agent)
        print(f"seeded {len(added)} task(s)")
        for t in added:
            print(f"  {t['id']}  p={t['priority']:.2g}  {t['title'][:70]}")


if __name__ == "__main__":
    main()
