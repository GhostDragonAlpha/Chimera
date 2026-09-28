"""input_trace.py -- I-U07-TRACE: strict trace ingestion + matched-stage latency.

The four measured stages of the input pipeline (PREREGISTRATION.md, frozen
before this build):

    input -> command_emitted -> simulation_consumed -> presented

  * input               the player intent is observed (key state change);
  * command_emitted     a versioned CommandRecord is handed to the seam sink
                        (tools/science_funnel/typeb_export/command_record.py,
                        pinned 9afbddcd: v_forward m/s, yaw_rate rad/s,
                        issued_tick, source; 20 Hz over 300 Hz physics);
  * simulation_consumed the physics tick that zero-order-holds that record
                        (issued_tick at the 15-tick hold boundary);
  * presented           a frame containing that tick is offered to the player.

THE LAW OF THIS MODULE (the card's falsifier, operationalized): a latency is
EXACTLY the difference of two matched-stage timestamps on one clock identity,
one run identity and one build identity. Anything that cannot be matched is
REFUSED -- never interpolated, imputed, or "best-effort" paired. A refused
trace produces NO latency output. Acceptance limits exist only as explicit
caller data (P06 is an unresolved decision card); without them the verdict is
`unqualified`, however good the numbers look.

Headless and deterministic by construction: no wall clock, no window, no
network; the only I/O is the caller-supplied input and the CLI output.

Event record (one JSON object per event; JSONL or JSON array):

    seq     int    chain id (the input sequence number); the four stages of
                   one chain share it
    stage   str    one of the four STAGES
    t       float  finite timestamp on the trace's clock
    unit    str    "ms" (default) or "s" -- per event, converted canonically
                   to ms before any comparison; the original value is kept
    clock   str    clock identity (e.g. "steady", "injected_ms"); one per trace
    run     str    run identity; one per trace
    build   str    build identity; one per trace
    payload any    optional opaque passthrough (CommandRecord fields, tick,
                   frame id, ...)

stdlib only, Python 3.11+.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

__all__ = [
    "STAGES", "STAGE_INDEX", "TraceRefused", "TraceEvent", "parse_trace",
    "chain_latencies", "summarize", "load_limits", "main",
]

STAGES = ("input", "command_emitted", "simulation_consumed", "presented")
STAGE_INDEX = {s: i for i, s in enumerate(STAGES)}

REQUIRED_FIELDS = ("seq", "stage", "t", "clock", "run", "build")
UNITS_TO_MS = {"ms": 1.0, "s": 1000.0}

# Metrics a caller may pin limits on (limits are CALLER DATA, never defaults).
LIMITABLE_METRICS = (
    "end_to_end_ms",
    "seg_input_to_command_ms",
    "seg_command_to_consumed_ms",
    "seg_consumed_to_presented_ms",
    "p95_end_to_end_ms",
    "p99_end_to_end_ms",
)

PERCENTILE_METHOD = "nearest-rank (ceil(p*N) on the ascending sort)"


class TraceRefused(Exception):
    """The trace carries no usable latency information; nothing is invented.

    `reason` is a stable machine name; `details` cites the offending events.
    No latency number may be derived from a refused trace.
    """

    def __init__(self, reason: str, details: dict[str, Any] | None = None):
        super().__init__(f"{reason}: {details or {}}")
        self.reason = reason
        self.details = details or {}


@dataclass(frozen=True)
class TraceEvent:
    """One validated stage observation. `t_ms` is the canonical ms value;
    `t`/`unit` preserve the caller's original representation (units are data)."""

    seq: int
    stage: str
    t: float
    unit: str
    t_ms: float
    clock: str
    run: str
    build: str
    payload: Any = None


def _num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def parse_trace(records: Iterable[dict[str, Any]]) -> list[TraceEvent]:
    """Validate every record; refuse the WHOLE trace on the first law break.

    Refusal reasons: empty_trace, record_not_object, missing_field, bad_type,
    non_finite_time, unknown_stage, bad_unit, duplicate_seq_stage, mixed_clock,
    mixed_run, mixed_build, missing_stage, reversed_stage_order.
    """
    events: list[TraceEvent] = []
    seen: dict[tuple[int, str], int] = {}
    clock: Optional[str] = None
    run: Optional[str] = None
    build: Optional[str] = None

    for i, rec in enumerate(records):
        if not isinstance(rec, dict):
            raise TraceRefused("record_not_object", {"index": i, "type": type(rec).__name__})
        for k in REQUIRED_FIELDS:
            if k not in rec or rec[k] is None:
                raise TraceRefused("missing_field", {"index": i, "field": k})
        seq, stage, t = rec["seq"], rec["stage"], rec["t"]
        if not isinstance(seq, int) or isinstance(seq, bool) or seq < 0:
            raise TraceRefused("bad_type", {"index": i, "field": "seq", "value": repr(seq)})
        if not isinstance(stage, str):
            raise TraceRefused("bad_type", {"index": i, "field": "stage", "value": repr(stage)})
        if not _num(t):
            raise TraceRefused("bad_type", {"index": i, "field": "t", "value": repr(t)})
        if not math.isfinite(float(t)):
            raise TraceRefused("non_finite_time", {"index": i, "seq": seq, "stage": stage, "value": repr(t)})
        if stage not in STAGE_INDEX:
            raise TraceRefused("unknown_stage", {"index": i, "seq": seq, "stage": stage})
        unit = rec.get("unit", "ms")
        if unit not in UNITS_TO_MS:
            raise TraceRefused("bad_unit", {"index": i, "seq": seq, "unit": repr(unit)})
        for name, val in (("clock", rec["clock"]), ("run", rec["run"]), ("build", rec["build"])):
            if not isinstance(val, str) or not val:
                raise TraceRefused("bad_type", {"index": i, "field": name, "value": repr(val)})
        if (seq, stage) in seen:
            raise TraceRefused("duplicate_seq_stage",
                               {"seq": seq, "stage": stage, "first_index": seen[(seq, stage)], "index": i})
        seen[(seq, stage)] = i
        if clock is None:
            clock, run, build = rec["clock"], rec["run"], rec["build"]
        else:
            if rec["clock"] != clock:
                raise TraceRefused("mixed_clock",
                                   {"seq": seq, "stage": stage, "clocks": sorted({clock, rec["clock"]})})
            if rec["run"] != run:
                raise TraceRefused("mixed_run", {"seq": seq, "stage": stage, "runs": sorted({run, rec["run"]})})
            if rec["build"] != build:
                raise TraceRefused("mixed_build",
                                   {"seq": seq, "stage": stage, "builds": sorted({build, rec["build"]})})
        # lead correction: refuse overflow AFTER unit conversion -- a finite
        # t in seconds can still overflow to inf in milliseconds
        t_ms = float(t) * UNITS_TO_MS[unit]
        if not math.isfinite(t_ms):
            raise TraceRefused("time_overflow",
                               {"seq": seq, "stage": stage, "unit": unit,
                                "t": repr(t), "t_ms": repr(t_ms)})
        events.append(TraceEvent(seq=seq, stage=stage, t=float(t), unit=unit,
                                 t_ms=t_ms, clock=rec["clock"],
                                 run=rec["run"], build=rec["build"],
                                 payload=rec.get("payload")))

    if not events:
        raise TraceRefused("empty_trace")

    by_chain: dict[int, dict[str, TraceEvent]] = {}
    for e in events:
        by_chain.setdefault(e.seq, {})[e.stage] = e
    for seq in sorted(by_chain):
        chain = by_chain[seq]
        missing = [s for s in STAGES if s not in chain]
        if missing:
            raise TraceRefused("missing_stage", {"seq": seq, "missing": missing,
                                                 "present": sorted(chain)})
        ts = [chain[s].t_ms for s in STAGES]
        for j in range(1, len(ts)):  # equal timestamps are legal (finite clock
            if ts[j] < ts[j - 1]:    # resolution); strictly earlier is reversal
                raise TraceRefused("reversed_stage_order",
                                   {"seq": seq, "at_stage": STAGES[j],
                                    "t_ms": [repr(v) for v in ts]})
    return events


@dataclass(frozen=True)
class ChainLatency:
    """Latencies of one COMPLETE chain -- exact differences of matched stages."""

    seq: int
    seg_input_to_command_ms: float
    seg_command_to_consumed_ms: float
    seg_consumed_to_presented_ms: float
    end_to_end_ms: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "seq": self.seq,
            "seg_input_to_command_ms": self.seg_input_to_command_ms,
            "seg_command_to_consumed_ms": self.seg_command_to_consumed_ms,
            "seg_consumed_to_presented_ms": self.seg_consumed_to_presented_ms,
            "end_to_end_ms": self.end_to_end_ms,
        }


def chain_latencies(events: Iterable[TraceEvent]) -> list[ChainLatency]:
    """Matched-stage latencies for every chain. Only complete chains reach the
    arithmetic: parse_trace already refused incomplete ones, so this function
    NEVER sees a partial chain (and adds its own refusal if handed one)."""
    by_chain: dict[int, dict[str, TraceEvent]] = {}
    for e in events:
        by_chain.setdefault(e.seq, {})[e.stage] = e
    out: list[ChainLatency] = []
    for seq in sorted(by_chain):
        chain = by_chain[seq]
        missing = [s for s in STAGES if s not in chain]
        if missing:
            raise TraceRefused("missing_stage", {"seq": seq, "missing": missing})
        a, b, c, d = (chain[s].t_ms for s in STAGES)
        segs = (b - a, c - b, d - c, d - a)
        # lead correction: latency arithmetic itself must stay finite
        # (inf - inf would emit NaN into every statistic downstream)
        if not all(math.isfinite(v) for v in segs):
            raise TraceRefused("latency_overflow",
                               {"seq": seq,
                                "t_ms": [chain[s].t_ms for s in STAGES]})
        out.append(ChainLatency(seq=seq,
                                seg_input_to_command_ms=segs[0],
                                seg_command_to_consumed_ms=segs[1],
                                seg_consumed_to_presented_ms=segs[2],
                                end_to_end_ms=segs[3]))
    if not out:
        raise TraceRefused("empty_trace")
    return out


def _nearest_rank(sorted_vals: list[float], p: float) -> float:
    """Nearest-rank percentile: the ceil(p*N)-th smallest (1-indexed)."""
    n = len(sorted_vals)
    k = max(1, math.ceil(p * n))
    return sorted_vals[k - 1]


def _stats(vals: list[float]) -> dict[str, float]:
    s = sorted(vals)
    n = len(s)
    if n == 0:
        raise TraceRefused("empty_stats", {"vals": vals})
    # Use stable arithmetic with overflow check for statistics
    total = sum(s)
    if not math.isfinite(total):
        raise TraceRefused("statistics_overflow", {"reason": "non_finite_statistics_sum", "vals": vals})
    mean = total / n
    return {"count": n, "min_ms": s[0], "max_ms": s[-1], "mean_ms": mean,
            "p50_ms": _nearest_rank(s, 0.50), "p95_ms": _nearest_rank(s, 0.95),
            "p99_ms": _nearest_rank(s, 0.99)}


def summarize(events: list[TraceEvent],
              limits: Optional[dict[str, float]] = None) -> dict[str, Any]:
    """Full summary. Latency arithmetic ONLY on complete matched chains; the
    qualification verdict derives ONLY from caller-supplied limits (P06 is an
    unresolved decision card -- absent limits mean `unqualified`)."""
    chains = chain_latencies(events)
    segs = {
        "seg_input_to_command_ms": [c.seg_input_to_command_ms for c in chains],
        "seg_command_to_consumed_ms": [c.seg_command_to_consumed_ms for c in chains],
        "seg_consumed_to_presented_ms": [c.seg_consumed_to_presented_ms for c in chains],
        "end_to_end_ms": [c.end_to_end_ms for c in chains],
    }
    summary: dict[str, Any] = {
        "schema": "chimera.input_trace.summary.v1",
        "identity": {"clock": events[0].clock, "run": events[0].run,
                     "build": events[0].build, "chains": len(chains),
                     "stages": list(STAGES),
                     "percentile_method": PERCENTILE_METHOD},
        "chains": [c.as_dict() for c in chains],
        "segments": {k: _stats(v) for k, v in segs.items()},
    }

    if limits is None or not limits:
        # lead correction: EMPTY limits are as absent as None -- a vacuous
        # `pass` with zero checks is impossible by construction
        summary["qualification"] = {"status": "unqualified",
                                    "reason": ("p06_limits_absent" if limits is None
                                               else "p06_limits_empty"),
                                    "note": "P06 (release acceptance limits) is an "
                                            "unresolved decision card; no limits "
                                            "are inferred or defaulted here"}
        return summary

    checks = {}
    for name, cap in sorted(limits.items()):
        if not _num(cap) or not math.isfinite(float(cap)):
            raise TraceRefused("bad_limit", {"limit": name, "value": repr(cap)})
        if name not in LIMITABLE_METRICS:
            raise TraceRefused("unknown_limit_key",
                               {"limit": name, "limitable": list(LIMITABLE_METRICS)})
        if name == "p95_end_to_end_ms":
            observed = summary["segments"]["end_to_end_ms"]["p95_ms"]
        elif name == "p99_end_to_end_ms":
            observed = summary["segments"]["end_to_end_ms"]["p99_ms"]
        else:
            observed = summary["segments"][name]["max_ms"]
        checks[name] = {"observed_ms": observed, "limit_ms": float(cap),
                        "pass": observed <= float(cap)}
    summary["qualification"] = {
        "status": "pass" if all(c["pass"] for c in checks.values()) else "fail",
        "source": "explicit caller data",
        "checks": checks,
    }
    return summary


def load_limits(path: str | None) -> Optional[dict[str, float]]:
    """Limits exist only as caller data; a file is read only when named."""
    if path is None:
        return None
    with open(path, "r", encoding="utf-8") as fh:
        obj = json.load(fh)
    if not isinstance(obj, dict):
        raise TraceRefused("bad_limit", {"limits_file": path, "type": type(obj).__name__})
    return obj


def _read_records(path: str) -> list[dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    stripped = text.lstrip()
    if stripped.startswith("["):
        obj = json.loads(text)
        if not isinstance(obj, list):
            raise TraceRefused("bad_input", {"path": path, "type": type(obj).__name__})
        return obj
    return [json.loads(line) for line in (ln for ln in text.splitlines() if ln.strip())]


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="input_trace",
        description="Strict four-stage input-trace ingestion and matched-stage "
                    "latency analysis (I-U07-TRACE). A refused trace prints ONLY "
                    "the refusal -- never a latency number.")
    ap.add_argument("--input", required=True, help="trace file: JSONL or JSON array")
    ap.add_argument("--limits", default=None,
                    help="optional JSON dict of caller-supplied acceptance limits "
                         f"(keys from {list(LIMITABLE_METRICS)}); absent => unqualified")
    ap.add_argument("--output", default=None, help="write JSON here (default stdout)")
    args = ap.parse_args(argv)

    try:
        records = _read_records(args.input)
        events = parse_trace(records)
        result = summarize(events, load_limits(args.limits))
    except TraceRefused as ref:
        payload = {"schema": "chimera.input_trace.refusal.v1",
                   "refused": ref.reason, "details": ref.details,
                   "latency_output": None}  # NO numbers on refusal, by law
        text = json.dumps(payload, indent=1, sort_keys=True)
        (open(args.output, "w", encoding="utf-8") if args.output else sys.stdout).write(text + "\n")
        return 2

    text = json.dumps(result, indent=1, sort_keys=True)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    else:
        sys.stdout.write(text + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
