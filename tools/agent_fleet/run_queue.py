"""Pure run-queue state machine for the fleet controller.

This module deliberately performs no Git, engine, network, or filesystem work.
The service adapter supplies those effects after an assignment is accepted.
"""
from dataclasses import dataclass, field
import math
from dataclasses import replace
from typing import Iterable


class QueueRefusal(ValueError):
    """A stale or invalid queue transition."""


@dataclass
class Run:
    task: str
    dependencies: tuple[str, ...] = ()
    priority: int = 5
    sequence: int = 0
    state: str = "READY"
    owner: str | None = None
    generation: int = 0
    lease_until: float | None = None
    head: str | None = None
    evidence: str | None = None
    history: list[str] = field(default_factory=list)


class RunQueue:
    """Deterministic dispatch policy with fenced leases and review boundary."""

    def __init__(self):
        self._runs: dict[str, Run] = {}
        self._sequence = 0

    def enqueue(self, task: str, *, dependencies: Iterable[str] = (), priority: int = 5) -> Run:
        if not task or task in self._runs:
            raise QueueRefusal("duplicate_or_empty_task")
        if not 0 <= priority <= 9:
            raise QueueRefusal("invalid_priority")
        deps = tuple(dependencies)
        if any(d == task for d in deps):
            raise QueueRefusal("self_dependency")
        self._sequence += 1
        run = Run(task, deps, priority, self._sequence)
        self._runs[task] = run
        return self._view(run)

    def dispatch(self, *, owner: str, capacity: int, now: float, lease_seconds: float) -> list[Run]:
        if not owner or capacity < 0 or not math.isfinite(now) or not math.isfinite(lease_seconds) or lease_seconds <= 0:
            raise QueueRefusal("invalid_dispatch_parameters")
        active = sum(r.owner == owner and r.state == "RUNNING" for r in self._runs.values())
        room = max(0, capacity - active)
        candidates = sorted(
            (r for r in self._runs.values() if r.state == "READY" and all(self._runs.get(d, Run(d, state="BLOCKED")).state == "INTEGRATED" for d in r.dependencies)),
            key=lambda r: (-r.priority, r.sequence),
        )
        selected = candidates[:room]
        for run in selected:
            run.state = "RUNNING"
            run.owner = owner
            run.generation += 1
            run.lease_until = now + lease_seconds
            run.history.append(f"dispatched:{owner}:{run.generation}")
        return [self._view(r) for r in selected]

    def heartbeat(self, task: str, *, owner: str, generation: int, now: float, lease_seconds: float) -> Run:
        run = self._owned_running(task, owner, generation)
        if not math.isfinite(now) or not math.isfinite(lease_seconds):
            raise QueueRefusal("nonfinite_lease_parameters")
        if run.lease_until is None or now >= run.lease_until:
            raise QueueRefusal("lease_expired")
        if lease_seconds <= 0:
            raise QueueRefusal("invalid_lease")
        run.lease_until = now + lease_seconds
        return self._view(run)

    def submit_review(self, task: str, *, owner: str, generation: int, now: float, head: str, evidence: str) -> Run:
        run = self._owned_running(task, owner, generation)
        if run.lease_until is None or not math.isfinite(now) or now >= run.lease_until:
            raise QueueRefusal("lease_expired")
        if not head or not evidence:
            raise QueueRefusal("review_identity_and_evidence_required")
        run.state, run.lease_until = "REVIEW", None
        run.head, run.evidence = head, evidence
        run.history.append(f"review:{head}")
        return self._view(run)

    def acknowledge_integration(self, task: str, *, head: str) -> Run:
        run = self._runs.get(task)
        if run is None or run.state != "REVIEW":
            raise QueueRefusal("not_in_review")
        if head != run.head:
            raise QueueRefusal("review_head_mismatch")
        run.state = "INTEGRATED"
        run.history.append(f"integrated:{head}")
        return self._view(run)

    def expire(self, *, now: float) -> list[Run]:
        expired = [r for r in self._runs.values() if r.state == "RUNNING" and r.lease_until is not None and now >= r.lease_until]
        for run in expired:
            run.state, run.owner, run.lease_until = "READY", None, None
            run.history.append("lease_expired:requeue")
        return expired

    def snapshot(self) -> list[dict]:
        return [
            {"task": r.task, "state": r.state, "owner": r.owner, "generation": r.generation, "head": r.head}
            for r in sorted(self._runs.values(), key=lambda x: x.sequence)
        ]

    def _owned_running(self, task: str, owner: str, generation: int) -> Run:
        run = self._runs.get(task)
        if run is None or run.state != "RUNNING":
            raise QueueRefusal("task_not_running")
        if run.owner != owner or run.generation != generation:
            raise QueueRefusal("stale_generation_or_owner")
        return run

    @staticmethod
    def _view(run: Run) -> Run:
        """Return a detached value so callers cannot mutate queue state."""
        return replace(run, dependencies=tuple(run.dependencies), history=list(run.history))
