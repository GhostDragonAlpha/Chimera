"""
Editor Scheduler — coordinates exclusive Unreal Editor access across parallel agents.

Problem
-------
The 7-stage pipeline must CLOSE the editor to free the module DLL for linking
(LNK1104 when locked), but MCP / visual-verification stages need the editor OPEN.
When several agents run pipelines, sleepwalker beats, or verification in parallel
they stomp on each other's editor/lock state and builds fail or screenshots lie.

Solution
--------
A file-locked coordinator. An agent requests the editor in a required mode
("open" for MCP/verification, "closed" for builds). The scheduler grants
exclusive access, drives the editor into the requested mode, and queues other
requesters via polling with timeout. A heartbeat reclaims crashed owners so a
dead agent can never wedge the editor forever.

Within a single pipeline run the owner may transition the mode
(request_editor("open", same_agent_id) after a build) — the scheduler only
enforces that NO OTHER agent touches the editor while one holds it.

Usage (in code)
---------------
    from core.editor_scheduler import request_editor, release_editor
    agent_id = f"pipeline-{uuid4().hex[:8]}"
    if not request_editor("closed", agent_id, timeout=120):
        sys.exit("could not acquire editor lock")
    try:
        ... build (editor closed) ...
        request_editor("open", agent_id)   # transition for verification
        ... verify (editor open) ...
    finally:
        release_editor(agent_id)

CLI
---
    python -m core.editor_scheduler request --mode closed --agent pipeline-1 --timeout 120
    python -m core.editor_scheduler release --agent pipeline-1
    python -m core.editor_scheduler state
    python -m core.editor_scheduler heartbeat --agent pipeline-1
"""

import json
import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Optional

HERE = Path(__file__).parent
STATE_PATH = HERE / "editor_scheduler_state.json"
LOCK_PATH = HERE / "editor_scheduler.lock"
HEARTBEAT_TIMEOUT = 300  # seconds; a silent owner is reclaimed

# ---------------------------------------------------------------------------
# Cross-platform advisory file lock. Windows uses msvcrt; Unix uses fcntl.
# Held ONLY briefly around state reads/writes; waiting happens OUTSIDE the
# lock via polling so a slow owner never blocks the lock file itself.
# ---------------------------------------------------------------------------
if os.name == "nt":
    import msvcrt

    def _acquire_lock_fd():
        fd = os.open(LOCK_PATH, os.O_CREAT | os.O_RDWR)
        msvcrt.locking(fd, msvcrt.LK_LOCK, 1)  # blocks until acquired
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
        fcntl.flock(fd, fcntl.LOCK_EX)  # blocking exclusive lock
        return fd

    def _release_lock_fd(fd):
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        except Exception:
            pass
        os.close(fd)


# ---------------------------------------------------------------------------
# State read/write
# ---------------------------------------------------------------------------
def _read_state():
    if not STATE_PATH.exists():
        return {"owner": None, "mode": None, "acquired_at": 0, "heartbeat": 0}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"owner": None, "mode": None, "acquired_at": 0, "heartbeat": 0}


def _write_state(state):
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _is_owner_alive(state):
    if not state.get("owner"):
        return False
    return (time.time() - state.get("heartbeat", 0)) < HEARTBEAT_TIMEOUT


# ---------------------------------------------------------------------------
# Editor mode drivers (mirror build_orchestrator's lifecycle helpers)
# ---------------------------------------------------------------------------
def _kill_ue_processes():
    for name in ("UnrealEditor.exe", "UnrealEditor-Cmd.exe", "CrashReportClientEditor.exe"):
        try:
            subprocess.run(["taskkill", "/F", "/IM", name],
                           capture_output=True, text=True, timeout=15)
        except Exception:
            pass


def _ensure_editor_closed():
    _kill_ue_processes()
    time.sleep(3)  # allow the OS to release the module DLL


def _ensure_editor_open():
    # DISABLED 2026-07-26 (operator request): the UE5 pipeline is retired -- we render with the Chimera engine
    # (ParticleEngine/ChimeraEngine), NOT Unreal. This used to Popen UnrealEditor.exe, which was auto-starting
    # the editor. It is now a no-op so nothing in the retired tree can launch UE. (Restore from git if UE ever
    # returns.) _kill_ue_processes / _ensure_editor_closed are kept -- shutting UE down stays safe.
    return


def _ensure_mode(mode):
    if mode == "closed":
        _ensure_editor_closed()
    elif mode == "open":
        _ensure_editor_open()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def request_editor(mode: str, agent_id: str, timeout: float = 120.0,
                   poll: float = 2.0) -> bool:
    """Request exclusive editor access in mode ('open'|'closed').

    Returns True if granted (caller now owns the editor in the requested mode).
    Blocks/polls until granted or ``timeout`` seconds elapse.
    """
    if mode not in ("open", "closed"):
        raise ValueError(f"mode must be 'open' or 'closed', got {mode!r}")
    deadline = time.time() + timeout
    while time.time() < deadline:
        fd = _acquire_lock_fd()
        try:
            state = _read_state()
            # Reclaim a crashed/stale owner before evaluating.
            if state.get("owner") and not _is_owner_alive(state):
                state = {"owner": None, "mode": None, "acquired_at": 0, "heartbeat": 0}
            if state.get("owner") is None:
                _ensure_mode(mode)
                _write_state({"owner": agent_id, "mode": mode,
                              "acquired_at": time.time(), "heartbeat": time.time()})
                return True
            if state.get("owner") == agent_id:
                # Already mine — upgrade mode if requested and apply it.
                if state.get("mode") != mode:
                    _ensure_mode(mode)
                    state["mode"] = mode
                state["heartbeat"] = time.time()
                _write_state(state)
                return True
            # Owned by another agent — release lock and poll.
        finally:
            _release_lock_fd(fd)
        time.sleep(poll)
    return False


def release_editor(agent_id: str) -> bool:
    """Release editor access if owned by ``agent_id``. Returns True if released."""
    fd = _acquire_lock_fd()
    try:
        state = _read_state()
        if state.get("owner") == agent_id:
            _write_state({"owner": None, "mode": None, "acquired_at": 0, "heartbeat": 0})
            return True
        return False
    finally:
        _release_lock_fd(fd)


def heartbeat(agent_id: str) -> bool:
    """Refresh the owner heartbeat so a long build isn't reclaimed. Returns True if owned."""
    fd = _acquire_lock_fd()
    try:
        state = _read_state()
        if state.get("owner") == agent_id:
            state["heartbeat"] = time.time()
            _write_state(state)
            return True
        return False
    finally:
        _release_lock_fd(fd)


def get_editor_state() -> dict:
    """Return the current scheduler state (owner, mode, timestamps)."""
    fd = _acquire_lock_fd()
    try:
        return _read_state()
    finally:
        _release_lock_fd(fd)


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description="Editor scheduler for parallel agents")
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("request", help="Request editor in a mode")
    pr.add_argument("--mode", choices=["open", "closed"], required=True)
    pr.add_argument("--agent", required=True)
    pr.add_argument("--timeout", type=float, default=120.0)

    rl = sub.add_parser("release", help="Release editor")
    rl.add_argument("--agent", required=True)

    sub.add_parser("state", help="Show current scheduler state")

    hb = sub.add_parser("heartbeat", help="Refresh heartbeat")
    hb.add_argument("--agent", required=True)

    args = p.parse_args(argv)
    if args.cmd == "request":
        ok = request_editor(args.mode, args.agent, timeout=args.timeout)
        print("GRANTED" if ok else "TIMEOUT")
        sys.exit(0 if ok else 1)
    elif args.cmd == "release":
        print("RELEASED" if release_editor(args.agent) else "NOT_OWNER")
    elif args.cmd == "heartbeat":
        print("OK" if heartbeat(args.agent) else "NOT_OWNER")
    elif args.cmd == "state":
        print(json.dumps(get_editor_state(), indent=2))


if __name__ == "__main__":
    main()
