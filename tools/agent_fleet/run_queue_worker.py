"""Authenticated worker-side queue loop.

The controller remains the authority. This module only reads snapshots and
requests claims; it never edits Git, SQLite, worktrees, or engine state.
"""
from __future__ import annotations

import argparse
import json
import time
from typing import Callable


class WorkerQueue:
    def __init__(self, call: Callable[[str, dict], dict], *, sleep=time.sleep):
        self.call = call
        self.sleep = sleep

    def claim_once(self) -> dict | None:
        snapshot = self.call("snapshot", {})
        tasks = snapshot.get("result", snapshot).get("tasks", {})
        ready = sorted(
            (t for t in tasks.values() if t.get("state") == "READY"),
            key=lambda t: (-int(t.get("priority", 5)), t["id"]),
        )
        refusals = []
        for task in ready:
            try:
                result = self.call("claim", {"task": task["id"]})
                return {"task": task["id"], "claim": result.get("result", result)}
            except Exception as exc:  # only named controller contention is recoverable
                if not self._claim_contention(exc):
                    raise
                refusals.append(f"{task['id']}:{type(exc).__name__}")
        return {"task": None, "refusals": refusals} if ready else None

    @staticmethod
    def _claim_contention(exc: Exception) -> bool:
        """Classify only expected claim races; never mask auth or transport errors."""
        message = str(exc)
        try:
            code = json.loads(message).get("error")
        except (ValueError, TypeError, AttributeError):
            code = message
        return code in {
            "task_not_ready", "no_free_slot", "write_scope_conflict",
            "dependencies_not_integrated", "capability_missing", "agent_capacity_reached",
        }

    def run_forever(self, *, poll_seconds: float = 5.0, max_cycles: int | None = None,
                    on_assignment: Callable[[dict], None] | None = None) -> None:
        if poll_seconds < 0:
            raise ValueError("poll_seconds must be nonnegative")
        cycles = 0
        while max_cycles is None or cycles < max_cycles:
            assignment = self.claim_once()
            if assignment is not None and on_assignment:
                on_assignment(assignment)
            cycles += 1
            if max_cycles is None or cycles < max_cycles:
                self.sleep(poll_seconds)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True)
    parser.add_argument("--poll-seconds", type=float, default=5.0)
    args = parser.parse_args()
    from client import call
    import json
    from pathlib import Path
    session = json.loads(Path(args.session).read_text(encoding="utf-8"))
    worker = WorkerQueue(lambda op, values: call(session, op, values))

    def report(item):
        # Do not print the session or controller response wholesale.
        if item.get("task"):
            print(json.dumps({"claimed_task": item["task"]}), flush=True)
        else:
            print(json.dumps({"claimed_task": None, "refusals": item.get("refusals", [])}), flush=True)

    worker.run_forever(poll_seconds=args.poll_seconds, on_assignment=report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
