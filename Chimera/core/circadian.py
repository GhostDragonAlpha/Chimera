"""circadian — the studio's own clock. No OS scheduler; the 24/7 agent reads
system time as part of its qualification (preflight) and that determines which
MODE the studio is in, and whether a NIGHT is due.

The rhythm already exists in GENERATION_PROTOCOL.md — Dawn (wake/preflight),
Day (build features), Dusk (the Will/postflight), Night (dream_loop
consolidation). What was missing: nothing read the clock. A cron would run
nights while everyone slept, but the human doesn't want a scheduler — the
agent is always awake, so the agent owns the clock. Each work cycle it checks
the time; if a night is due (night hours with no consolidation this window,
or simply >20h since the last one), it runs the night itself.

  python -m core.circadian            # status: phase, time, is-night-due
  python -m core.circadian tick --run # the self-pacing primitive: runs the
                                      # night IFF due, else a cheap no-op —
                                      # safe to call every cycle
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAST_NIGHT = ROOT / "docs" / "world" / "last_night.json"   # machine-local, gitignored

OVERDUE_HOURS = 20        # a night this long ago is due regardless of clock hour
NIGHT_OPENS = 22          # local hour the night window opens
NIGHT_CLOSES = 5          # local hour it closes (next day)

PHASES = {
    "dawn":  ("Dawn", "wake — read the board, claim your lane, inherit the Will"),
    "day":   ("Day", "build — drive features through the conveyor, accumulate reps"),
    "dusk":  ("Dusk", "the Will — wrap current work, postflight, declare pains"),
    "night": ("Night", "dream — consolidate: distill, tend, breathe, ripen, report"),
}


def phase_of(hour: int) -> str:
    if NIGHT_OPENS <= hour or hour < NIGHT_CLOSES:
        return "night"
    if NIGHT_CLOSES <= hour < 9:
        return "dawn"
    if 9 <= hour < 18:
        return "day"
    return "dusk"           # 18:00–22:00


def _night_window_start(now: datetime) -> datetime:
    """The most recent moment the night window opened (today 22:00, or
    yesterday 22:00 if we're in the small hours before it closes)."""
    if now.hour < NIGHT_CLOSES:
        base = now - timedelta(days=1)
    else:
        base = now
    return base.replace(hour=NIGHT_OPENS, minute=0, second=0, microsecond=0)


def last_night_ts() -> datetime | None:
    if LAST_NIGHT.exists():
        try:
            return datetime.fromisoformat(json.loads(LAST_NIGHT.read_text())["iso"])
        except Exception:
            return None
    return None


def mark_night_ran(now: datetime = None) -> None:
    """dream_loop calls this on completion so the clock knows a night happened."""
    now = now or datetime.now()
    LAST_NIGHT.parent.mkdir(parents=True, exist_ok=True)
    LAST_NIGHT.write_text(json.dumps({"iso": now.isoformat(timespec="seconds")}),
                          encoding="utf-8")


def night_due(now: datetime = None) -> tuple:
    """(due: bool, reason: str). The agent's self-pacing test."""
    now = now or datetime.now()
    last = last_night_ts()
    if last is None:
        return True, "no consolidation on record yet"
    hours_since = (now - last).total_seconds() / 3600.0
    if hours_since >= OVERDUE_HOURS:
        return True, f"overdue: {hours_since:.0f}h since last night (>= {OVERDUE_HOURS}h)"
    if phase_of(now.hour) == "night" and last < _night_window_start(now):
        return True, "night hours and no consolidation this window"
    return False, (f"not due ({hours_since:.1f}h since last night; "
                   f"phase {phase_of(now.hour)})")


def status(now: datetime = None) -> dict:
    now = now or datetime.now()
    phase = phase_of(now.hour)
    due, reason = night_due(now)
    last = last_night_ts()
    return {
        "time": now.strftime("%Y-%m-%d %H:%M"),
        "phase": phase,
        "phase_label": PHASES[phase][0],
        "directive": PHASES[phase][1],
        "night_due": due,
        "reason": reason,
        "last_night": last.strftime("%Y-%m-%d %H:%M") if last else "never",
    }


def tick(run: bool = False, now: datetime = None) -> dict:
    """The primitive the always-on agent calls each cycle. If a night is due
    and run=True, run the consolidation now (self-paced, no scheduler)."""
    st = status(now)
    st["ran_night"] = False
    if st["night_due"] and run:
        print(f"[circadian] night is due ({st['reason']}) — running consolidation")
        try:
            from core import dream_loop
            dream_loop.main([])                 # the night
            mark_night_ran(now)
            st["ran_night"] = True
        except SystemExit:
            mark_night_ran(now)
            st["ran_night"] = True
        except Exception as e:                  # a failed night must not wedge the agent
            print(f"[circadian] night FAILED: {e}")
    return st


def preflight_line(now: datetime = None) -> str:
    """One block for preflight's wake section — the clock the agent qualifies against."""
    st = status(now)
    lines = [f"[0] Circadian: {st['phase_label'].upper()} @ {st['time']} "
             f"(local) — {st['directive']}"]
    if st["night_due"]:
        lines.append(f"    ** NIGHT IS DUE ({st['reason']}) -> run "
                     f"`python -m core.circadian tick --run` (or `python -m core.dream_loop`) **")
    else:
        lines.append(f"    last night {st['last_night']}; {st['reason']}")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd")
    t = sub.add_parser("tick")
    t.add_argument("--run", action="store_true",
                   help="actually run the night if one is due")
    args = parser.parse_args(argv)
    if args.cmd == "tick":
        st = tick(run=args.run)
        print(json.dumps(st, indent=1))
    else:
        st = status()
        print(f"{st['phase_label']} @ {st['time']} — {st['directive']}")
        print(f"night due: {st['night_due']} ({st['reason']}); last night {st['last_night']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
