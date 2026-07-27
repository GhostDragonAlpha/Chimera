"""metronome — measure FEEL, not just function. The first tier-3 organ.

"AAA feel" is response: press a key, the world answers — fast, richly, and
without dead air. Nothing in the studio measured that band until now. The
metronome mines two streams the game ALREADY emits:

  chronicle (witness marks)   timestamped input actions (key/key_down/...)
  UE log                      timestamped feedback lines (Footstep Sync:,
                              Sprint ON/OFF, servo/audio logs)

and computes the classic feel metrics:

  input_feedback_ms   median press -> first-feedback latency. The literature's
                      rule of thumb: responses over ~100ms read as lag
                      (game-feel canon; Malcolm wall band [_, 150]).
  juice_density       feedback events per active-input second — richness.
  dead_air_max_s      the longest input-active stretch with ZERO feedback —
                      the silence that reads as "broken".

Writes docs/world/feel_last.json; rep_engine's gen_feel mints tier-3 atoms
against the bands. Runs automatically at the end of every sleepwalk.

CLI: python -m core.metronome analyze [--session NAME]
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEEL_LAST = ROOT / "docs" / "world" / "feel_last.json"
CHRONICLES = ROOT / "Saved" / "SessionChronicles"
LOGS = ROOT / "Saved" / "Logs"

FEEL_BANDS = {  # tier-3 walls; provenance: game-feel canon (~100ms response rule)
    "input_feedback_ms": {"max": 150.0},
    "juice_density": {"min": 0.5},          # >= 1 feedback per 2s of input
    "dead_air_max_s": {"max": 3.0},
}

_INPUT_KEYS = ("key", "key_down", "interact", "pickup", "drop")
_LOG_LINE = re.compile(r"^\[(\d{4})\.(\d{2})\.(\d{2})-(\d{2})\.(\d{2})\.(\d{2}):(\d{3})\].*?"
                       r"(Footstep Sync:|Sprint ON|Sprint OFF|PlayServo|PlayImpact)")


def parse_inputs(chronicle: dict) -> list:
    """UTC timestamps (epoch seconds) of input actions from witness marks."""
    out = []
    marks = chronicle if isinstance(chronicle, list) else \
        chronicle.get("marks", chronicle.get("events", []))
    for m in marks:
        data = m.get("data") or {}
        if m.get("kind") == "action" and any(k in data for k in _INPUT_KEYS):
            utc = m.get("utc")
            if utc:
                out.append(datetime.fromisoformat(utc).timestamp())
    return sorted(out)


def parse_feedback(log_text: str) -> list:
    """UTC timestamps of feedback lines from the UE log (log stamps are UTC)."""
    out = []
    for line in log_text.splitlines():
        m = _LOG_LINE.match(line)
        if m:
            y, mo, d, h, mi, s, ms = (int(g) for g in m.groups()[:7])
            out.append(datetime(y, mo, d, h, mi, s, ms * 1000,
                                tzinfo=timezone.utc).timestamp())
    return sorted(out)


def feel_metrics(inputs: list, feedback: list) -> dict:
    """The three feel numbers. Honest Nones when a stream is empty."""
    if not inputs:
        return {"note": "no input actions in chronicle"}
    latencies, uncovered = [], []
    fb_i = 0
    for t in inputs:
        while fb_i < len(feedback) and feedback[fb_i] < t:
            fb_i += 1
        if fb_i < len(feedback) and feedback[fb_i] - t <= 5.0:
            latencies.append((feedback[fb_i] - t) * 1000.0)
        else:
            uncovered.append(t)
    active_span = max(inputs[-1] - inputs[0], 1.0)
    in_window = [f for f in feedback if inputs[0] <= f <= inputs[-1] + 5.0]
    dead_max = 0.0
    events = sorted(inputs + in_window)
    for a, b in zip(events, events[1:]):
        if b - a > dead_max and any(a <= t <= b for t in inputs + [a]):
            dead_max = b - a
    return {
        "input_feedback_ms": round(statistics.median(latencies), 1) if latencies else None,
        "juice_density": round(len(in_window) / active_span, 3),
        "dead_air_max_s": round(dead_max, 2),
        "inputs": len(inputs), "feedback_events": len(in_window),
        "unanswered_inputs": len(uncovered),
    }


def analyze(session: str = None) -> dict:
    """Newest (or named) chronicle x newest UE log -> feel_last.json."""
    chron_files = sorted(CHRONICLES.glob("*.json"),
                         key=lambda p: p.stat().st_mtime, reverse=True)
    if session:
        chron_files = [p for p in chron_files if session in p.name] or chron_files
    if not chron_files:
        return {"note": "no chronicles yet"}
    logs = sorted(LOGS.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    log_text = logs[0].read_text(encoding="utf-8", errors="replace") if logs else ""
    chronicle = json.loads(chron_files[0].read_text(encoding="utf-8"))
    metrics = feel_metrics(parse_inputs(chronicle), parse_feedback(log_text))
    metrics["session"] = chron_files[0].stem
    metrics["ts"] = datetime.now(timezone.utc).isoformat()[:19]
    FEEL_LAST.parent.mkdir(parents=True, exist_ok=True)
    FEEL_LAST.write_text(json.dumps(metrics, indent=1), encoding="utf-8")
    return metrics


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze")
    a.add_argument("--session")
    args = p.parse_args()
    print(json.dumps(analyze(args.session), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
