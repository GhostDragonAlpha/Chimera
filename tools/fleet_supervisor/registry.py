# fleet_supervisor/registry.py -- the durable ownership record (JSONL, append-only).
#
# Astra's law (astra-round6-answer-20260922.md):
#   "Every execution attempt has a unique ID, owner lane, worktree, command,
#    ports, browser profile, and declared resource requirements."
#   "PID records need creation time because PIDs are reused."
# Identity = (pid, creation_time). Nothing else. The file is the truth across
# supervisor restarts; the fold of the last event per session is the state.
from __future__ import annotations

import json
import os
import time
import uuid

REGISTRY_VERSION = 1
ACTIVE_STATUSES = {"running", "completing"}
TERMINAL_STATUSES = {"completed", "terminated", "orphaned_completed", "refused", "cannot_complete"}

DEFAULT_REGISTRY = r"E:\ChimeraWork\control\fleet_registry.jsonl"


def new_session_id(kind: str) -> str:
    return f"{kind}-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + f".{int(time.time()%1*1000):03d}Z"


def append(registry_path: str, record: dict) -> dict:
    """Append one record with durability (flush + fsync). Returns it."""
    record = dict(record)
    record.setdefault("v", REGISTRY_VERSION)
    record.setdefault("ts", _now_iso())
    os.makedirs(os.path.dirname(registry_path), exist_ok=True)
    with open(registry_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    return record


def launch_record(session_id: str, spec: dict, pid: int, creation_time_us: int,
                  job_name: str, supervisor_pid: int) -> dict:
    return {
        "event": "launch",
        "session_id": session_id,
        "owner_lane": spec["owner_lane"],
        "worktree": spec.get("worktree"),
        "command": spec["command"],
        "ports": sorted(set(spec.get("ports") or [])),
        "kind": spec["kind"],
        "resources": spec.get("resources") or {},
        "pid": int(pid),
        "creation_time_us": int(creation_time_us),   # raw FILETIME: identity, never pid alone
        "job_name": job_name,
        "status": "running",
        "supervisor_pid": supervisor_pid,
        "last_activity": time.time(),
    }


def status_record(session_id: str, status: str, **extra) -> dict:
    assert status in ACTIVE_STATUSES | TERMINAL_STATUSES, status
    rec = {"event": "status", "session_id": session_id, "status": status}
    rec.update(extra)
    return rec


def fold(registry_path: str) -> dict[str, dict]:
    """Fold the JSONL to the latest record per session (file order wins).
    A session with a launch but a later status keeps the launch identity fields
    (pid/creation/job_name) merged into the folded view."""
    sessions: dict[str, dict] = {}
    if not os.path.exists(registry_path):
        return sessions
    with open(registry_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue  # a torn tail line from a hard crash never poisons the fold
            sid = rec.get("session_id")
            if not sid:
                continue
            prev = sessions.get(sid, {})
            merged = {**prev, **{k: v for k, v in rec.items() if v is not None}}
            sessions[sid] = merged
    return sessions


def active_sessions(registry_path: str) -> dict[str, dict]:
    return {sid: rec for sid, rec in fold(registry_path).items()
            if rec.get("status") in ACTIVE_STATUSES and "pid" in rec}


def declared_mem_gib(rec: dict) -> float:
    return float((rec.get("resources") or {}).get("mem_gib") or 0)


def identity_matches(rec: dict, pid: int, creation_time_us: int) -> bool:
    """THE dedup rule: pid AND creation time. Never pid alone."""
    return (rec.get("pid") == pid and rec.get("creation_time_us") == creation_time_us)
