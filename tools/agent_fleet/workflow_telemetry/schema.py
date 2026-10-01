"""schema.py -- the append-only EVENT SCHEMA for workflow telemetry (Astra P0).

SIX-LINE SUMMARY (the schema):

  1. Every ATTEMPT (a wave lane run: registered -> decided) emits one event per
     phase it enters: registered|building|running|verifying|deciding.
  2. Event = {ts, lane, attempt_id, parent_manifest, claim_digest, phase,
     active_seconds, wait_seconds, outcome, resources, parent_attempt,
     child_attempts, policy_version, anchors, note}.
  3. ts is ISO-8601 local; UNKNOWN timing is null -- NEVER zero (a missing
     clock reading is not a measured zero, per the Astra registration envelope).
  4. outcome rides the deciding event: certified|fired|pruned|abandoned|pending
     -- certified and uneventful runs are recorded exactly like failures.
  5. anchors carry INDEPENDENT evidence: git commit shas, receipt sha256s,
     janitor events -- the reconciliation surface for F-EVENT-GAP.
  6. The file is APPEND-ONLY JSONL: one JSON object per line, no updates, no
     deletions; corrections are new events with causal links to the old.

`policy_version` names the workflow checklist / Rule-0 freeze in force at the
attempt (from the receipt's frozen rule_0 sha where the receipt carries one).
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Optional

PHASES = ("registered", "building", "running", "verifying", "deciding")
OUTCOMES = ("certified", "fired", "pruned", "abandoned", "pending")


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def digest(obj: Any) -> str:
    """Stable sha256 hex[:16] over canonical JSON of `obj`."""
    blob = json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


@dataclass
class Event:
    ts: Optional[str]                 # ISO-8601, or None = UNKNOWN (never 0)
    lane: str                         # lane branch / worktree name
    attempt_id: str                   # e.g. "wave-35"
    parent_manifest: Optional[str]    # parent ship sha + lane, from receipt base
    claim_digest: Optional[str]       # sha256[:16] of the frozen Rule-0 claim
    phase: str                        # registered|building|running|verifying|deciding
    active_seconds: Optional[float]   # measured active interval, null if unknown
    wait_seconds: Optional[float]     # measured waiting interval, null if unknown
    outcome: str = "pending"          # certified|fired|pruned|abandoned|pending
    resources: str = ""               # resource notes (cores, minutes, files)
    parent_attempt: Optional[str] = None
    child_attempts: list = field(default_factory=list)
    policy_version: Optional[str] = None  # checklist / rule-0 freeze in force
    anchors: dict = field(default_factory=dict)  # independent evidence refs
    note: str = ""

    def __post_init__(self):
        if self.phase not in PHASES:
            raise ValueError(f"illegal phase {self.phase!r}")
        if self.outcome not in OUTCOMES:
            raise ValueError(f"illegal outcome {self.outcome!r}")

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


def append(path: str, event: Event) -> None:
    """APPEND-ONLY: one line, O_APPEND, no rewrite, no delete."""
    line = event.to_json() + "\n"
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND)
    try:
        os.write(fd, line.encode("utf-8"))
    finally:
        os.close(fd)


def append_all(path: str, events) -> None:
    for e in events:
        append(path, e)


def read_ledger(path: str):
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out
