# fleet_supervisor/queue.py -- the BOUNDED GPU broker queue (Astra round 6, section 3).
#
# Contract this file implements (astra-round6-answer-20260922.md, verbatim-cited):
#   "Use a single GPU broker with exclusive ownership of fleet GPU execution."
#   "Interactive fleet work: schedule captures and judge requests by deadline, with
#    aging to prevent starvation."
#   "Batch a few judge requests to amortize model loading, but cap batch duration so
#    captures cannot starve."
#   "Do not send requests to Ollama while waiting for the GPU. Maintain the queue in
#    your broker. Distinguish: Queue deadline. Model-load timeout after admission.
#    Inference timeout after readiness. This makes a deferred request visibly deferred
#    instead of repeatedly 'failing inference.'"
#
# The queue NEVER talks to a model. It holds requests; the judge service (judge.py)
# is only ever invoked AFTER the GPU reservation is held by this broker. A request
# that times out while WAITING is terminal state QUEUE_DEADLINE_EXCEEDED with a
# queue-worded label -- the label scan in tests_gpu_broker.py fails the lane if a
# waiting request is ever mislabeled as a model failure (F3).
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field

# ---------------------------------------------------------------- states
# The THREE Astra timeout states are terminal and mutually distinct:
QUEUED = "queued"                              # waiting for the reservation: VISIBLY DEFERRED
ADMITTED_LOADING = "admitted_loading"          # admitted; model loading
RUNNING = "running"                            # model ready; inference running
COMPLETED = "completed"

QUEUE_DEADLINE_EXCEEDED = "queue_deadline_exceeded"   # never admitted: deferred past deadline
MODEL_LOAD_TIMEOUT = "model_load_timeout"             # admitted; load stalled past its budget
INFERENCE_TIMEOUT = "inference_timeout"               # ready; inference stalled past its budget
CANCELLED = "cancelled"
REFUSED = "refused"                                    # queue full (backpressure): explicit

TERMINAL_STATES = {COMPLETED, QUEUE_DEADLINE_EXCEEDED, MODEL_LOAD_TIMEOUT,
                   INFERENCE_TIMEOUT, CANCELLED, REFUSED}
# requests that were NEVER admitted to the model phase (F3 domain)
NEVER_ADMITTED_STATES = {QUEUED, QUEUE_DEADLINE_EXCEEDED, CANCELLED, REFUSED}

KINDS = ("capture", "judge")

# label wording for a pure queue wait -- MUST NOT contain model/inference failure
# words (the F3 scan greps never-admitted labels for them; a deferred request's
# label must never read as a model failure)
_QUEUE_WAIT_LABEL = ("deferred: waiting in the GPU broker queue (position {pos}, "
                     "waited {waited:.1f}s, deadline in {remaining:.1f}s)")
_QUEUE_EXPIRED_LABEL = ("deferred: queue wait exceeded its deadline before admission "
                        "(never admitted; no GPU work was started)")
_REFUSED_LABEL = "refused: the GPU broker queue is full (backpressure; nothing was started)"
_CANCELLED_LABEL = "cancelled by owner while queued"


def _now_iso(ts: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(ts)) + f".{int(ts % 1 * 1000):03d}Z"


@dataclass
class Request:
    request_id: str
    kind: str                 # "capture" | "judge"
    owner_lane: str
    deadline_ts: float        # ABSOLUTE time by which the request must be ADMITTED
    enqueued_ts: float
    model: str | None = None  # judges only
    payload: dict = field(default_factory=dict)
    state: str = QUEUED
    label: str = ""
    admitted_ts: float | None = None
    completed_ts: float | None = None
    error: str | None = None

    def waited_s(self, now: float) -> float:
        return (self.admitted_ts or now) - self.enqueued_ts


class GrantLedger:
    """Every exclusive GPU grant, as a half-open time interval. F1 checks this:
    exclusive grants must never overlap."""
    def __init__(self):
        self.grants: list[dict] = []

    def open(self, owner: str, kind: str, start_ts: float, request_ids: list[str]) -> dict:
        g = {"owner": owner, "kind": kind, "start_ts": start_ts, "end_ts": None,
             "request_ids": list(request_ids)}
        self.grants.append(g)
        return g

    def close(self, grant: dict, end_ts: float) -> None:
        if grant["end_ts"] is None:
            grant["end_ts"] = end_ts

    def overlapping_pairs(self) -> list[tuple[dict, dict]]:
        closed = [g for g in self.grants if g["end_ts"] is not None]
        closed.sort(key=lambda g: g["start_ts"])
        out = []
        for i, a in enumerate(closed):
            for b in closed[i + 1:]:
                if b["start_ts"] >= a["end_ts"]:
                    break
                out.append((a, b))
        return out


class GpuBrokerQueue:
    """The bounded broker queue. Pure decision logic: `now` is always a parameter,
    so the falsifier suite can run deterministic/synthetic timelines; production
    passes time.time."""

    def __init__(self, *, max_depth: int = 64, aging_gain: float = 1.0,
                 batch_duration_cap_s: float = 30.0, max_batch_size: int = 4,
                 journal_path: str | None = None):
        if aging_gain < 0:
            raise ValueError("aging_gain must be >= 0")
        self.max_depth = int(max_depth)
        self.aging_gain = float(aging_gain)
        self.batch_duration_cap_s = float(batch_duration_cap_s)
        self.max_batch_size = int(max_batch_size)
        self.journal_path = journal_path
        self.requests: dict[str, Request] = {}
        self.ledger = GrantLedger()

    # ------------------------------------------------------------ durability
    def _journal(self, event: dict) -> None:
        if not self.journal_path:
            return
        os.makedirs(os.path.dirname(self.journal_path), exist_ok=True)
        with open(self.journal_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def _transition(self, r: Request, state: str, label: str, now: float,
                    **extra) -> None:
        r.state = state
        r.label = label
        ev = {"event": "state", "ts": _now_iso(now), "request_id": r.request_id,
              "kind": r.kind, "owner_lane": r.owner_lane,
              "state": state, "label": label}
        ev.update(extra)
        self._journal(ev)

    # ------------------------------------------------------------ submission
    def submit(self, kind: str, owner_lane: str, deadline_s: float, *, now: float,
               model: str | None = None, payload: dict | None = None,
               request_id: str | None = None) -> Request:
        """Enter the queue. BOUNDED: beyond max_depth the request is REFUSED
        explicitly (honest backpressure) -- never silently dropped or queued
        unboundedly."""
        if kind not in KINDS:
            raise ValueError(f"kind must be one of {KINDS}")
        now = time.time() if now is None else now
        active = sum(1 for r in self.requests.values()
                     if r.state not in TERMINAL_STATES)
        r = Request(
            request_id=request_id or f"{kind}-{uuid.uuid4().hex[:8]}",
            kind=kind, owner_lane=owner_lane, deadline_ts=now + float(deadline_s),
            enqueued_ts=now, model=model, payload=dict(payload or {}))
        if active >= self.max_depth:
            r.state = REFUSED
            r.label = _REFUSED_LABEL
            r.completed_ts = now
        else:
            r.label = _QUEUE_WAIT_LABEL.format(pos=active + 1, waited=0.0,
                                               remaining=float(deadline_s))
        self.requests[r.request_id] = r
        self._journal({"event": "submit", "ts": _now_iso(now), "request_id": r.request_id,
                       "kind": kind, "owner_lane": owner_lane,
                       "deadline_ts": r.deadline_ts, "state": r.state})
        return r

    def cancel(self, request_id: str, *, now: float) -> bool:
        r = self.requests.get(request_id)
        if r is None or r.state in TERMINAL_STATES:
            return False
        if r.state in NEVER_ADMITTED_STATES:
            self._transition(r, CANCELLED, _CANCELLED_LABEL, now)
            r.completed_ts = now
            return True
        return False  # already at the model: the judge service owns it now

    # ------------------------------------------------------------ scheduling
    def score(self, r: Request, now: float) -> float:
        """Deadline ordering WITH AGING: the effective deadline advances by
        aging_gain for every second waited, so a request that keeps losing the
        comparison eventually wins it (neither captures nor judges can starve).
        gain=0 recovers pure deadline order (the starvable baseline)."""
        return r.deadline_ts - self.aging_gain * (now - r.enqueued_ts)

    def _queued_reqs(self) -> list[Request]:
        return [r for r in self.requests.values() if r.state == QUEUED]

    def expire_pass(self, *, now: float) -> list[str]:
        """Queue-deadline enforcement. A request whose deadline passes while it
        WAITS is terminal QUEUE_DEADLINE_EXCEEDED -- visibly deferred, never a
        model failure (it was never sent)."""
        expired = []
        for r in self._queued_reqs():
            if now > r.deadline_ts:
                self._transition(r, QUEUE_DEADLINE_EXCEEDED, _QUEUE_EXPIRED_LABEL, now,
                                 waited_s=round(now - r.enqueued_ts, 3))
                r.completed_ts = now
                expired.append(r.request_id)
        return expired

    def admit_pass(self, *, now: float, gpu_free: bool,
                   batch: "BatchWindow | None" = None) -> "Admission | None":
        """One admission decision.
          - batch open and not full -> waiting judges JOIN it (no new model load);
          - gpu free -> the best-scoring request wins; a winning judge opens a
            JUDGE BATCH (bounded size, bounded duration) to amortize model loads;
            a winning capture gets ONE exclusive grant for its payload duration.
        Never called while the GPU is busy with anything else: exclusivity is
        structural (one current activity in the BrokerService) AND audited here."""
        if batch is not None and batch.open(now=now):
            joins = [r for r in self._queued_reqs() if r.kind == "judge"]
            joins.sort(key=lambda r: (self.score(r, now), r.enqueued_ts))
            room = self.max_batch_size - len(batch.members)
            joins = joins[:max(0, room)]
            if joins:
                for r in joins:
                    r.admitted_ts = now
                    self._transition(r, ADMITTED_LOADING,
                                     "admitted: joined the open judge batch (no new load)",
                                     now, waited_s=round(r.waited_s(now), 3))
                return Admission("judge_join", joins, batch)
            return None

        if not gpu_free:
            return None
        waiting = self._queued_reqs()
        if not waiting:
            return None
        waiting.sort(key=lambda r: (self.score(r, now), r.enqueued_ts))
        best = waiting[0]
        if best.kind == "judge":
            members = [r for r in waiting if r.kind == "judge"][:self.max_batch_size]
            members.sort(key=lambda r: (self.score(r, now), r.enqueued_ts))
            new_batch = BatchWindow(closed_at_ts=now + self.batch_duration_cap_s)
            new_batch.members = members
            for r in members:
                r.admitted_ts = now
                self._transition(r, ADMITTED_LOADING,
                                 "admitted: judge batch opening (one model load amortized "
                                 "over %d request(s))" % len(members),
                                 now, waited_s=round(r.waited_s(now), 3))
            return Admission("judge_batch", members, new_batch)
        best.admitted_ts = now
        self._transition(best, ADMITTED_LOADING,
                         "admitted: exclusive capture grant", now,
                         waited_s=round(best.waited_s(now), 3))
        return Admission("capture", [best], None)


class BatchWindow:
    """A bounded judging batch: capped member count (admission) and a HARD
    wall-clock cap (duration). The cap is what keeps captures from starving
    while judge requests keep arriving (Astra rule 5)."""
    def __init__(self, *, closed_at_ts: float):
        self.closed_at_ts = float(closed_at_ts)   # hard cap: no extensions, ever
        self.members: list[Request] = []
        self.joined: list[Request] = []

    def open(self, *, now: float) -> bool:
        return now < self.closed_at_ts

    def remaining_s(self, now: float) -> float:
        return max(0.0, self.closed_at_ts - now)


@dataclass
class Admission:
    kind: str                # "capture" | "judge_batch" | "judge_join"
    members: list[Request]
    batch: BatchWindow | None


# ------------------------------------------------------------ visible status
def status_of(queue: GpuBrokerQueue, request_id: str, *, now: float | None = None) -> dict:
    """THE visible-deferral contract: every request ever submitted is queryable
    at any time, and a WAITING request's status says DEFERRED with numbers --
    it never reads as an inference/model failure."""
    now = time.time() if now is None else now
    r = queue.requests.get(request_id)
    if r is None:
        return {"request_id": request_id, "state": "unknown",
                "label": "no such request in this broker's queue"}
    out = {
        "request_id": r.request_id, "kind": r.kind, "owner_lane": r.owner_lane,
        "state": r.state, "label": r.label,
        "waited_s": round(r.waited_s(now), 3),
        "deadline_in_s": round(r.deadline_ts - now, 3),
        "terminal": r.state in TERMINAL_STATES,
    }
    if r.state == QUEUED:
        pos = sorted((x for x in queue._queued_reqs()),
                     key=lambda x: (queue.score(x, now), x.enqueued_ts))
        out["queue_position"] = pos.index(r) + 1 if r in pos else None
    if r.error:
        out["error"] = r.error
    return out
