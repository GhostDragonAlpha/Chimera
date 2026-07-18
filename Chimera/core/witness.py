"""Witness — shared beat-timeline recorder for playtest sessions.

Serves BOTH kinds of sessions (Generation Protocol / SLEEPWALKER_DESIGN.md):
  - human sessions: run as CLI alongside the playtest, poll runtime + tail [DEMOBEAT]
  - sleepwalks: used inline by core.sleepwalker to timestamp beat evidence

Output: Saved/SessionChronicles/<session>.json — a beat timeline whose entries
ground tacit attribution claims (the honest-tacit rule: no witness timestamp,
no tacit claim).
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

CHRONICLE_DIR = Path(__file__).resolve().parent.parent / "Saved" / "SessionChronicles"
LOG_PATH = Path(__file__).resolve().parent.parent / "Saved" / "Logs" / "Chimera.log"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Witness:
    """Collects timestamped events for one session and writes the chronicle."""

    def __init__(self, session: str, source: str = "agent-sim"):
        self.session = session
        self.source = source
        self.t0 = time.monotonic()
        self.events = []
        self._log_offset = LOG_PATH.stat().st_size if LOG_PATH.exists() else 0
        # tb-0185: the full unfiltered tail from the most recent drain_demobeats()
        # read, cached for drain_all_new() to serve — see that method's docstring.
        self._last_raw_lines = []

    def mark(self, kind: str, data: dict = None):
        self.events.append({
            "t": round(time.monotonic() - self.t0, 2),
            "utc": _now(),
            "kind": kind,
            "data": data or {},
        })

    def drain_demobeats(self) -> list:
        """Read NEW [DEMOBEAT] lines since the last drain; mark and return them.

        UNCHANGED BEHAVIOR (tb-0185): this remains a strict [DEMOBEAT]-only
        filter, byte-identical to before — same return value, same "demobeat"
        marks, same bounded (offset-cursor) read. Existing beats/consumers that
        key on this exact filtered stream see no change whatsoever.

        The same bounded read this performs also refreshes self._last_raw_lines
        (every NEW line since the last drain, UNFILTERED) so drain_all_new()
        can serve log_contains expects without a second file read — see that
        method's docstring for why it needs to exist (tb-0185: log_contains was
        structurally deaf to every non-[DEMOBEAT] witness marker)."""
        lines = []
        self._last_raw_lines = []
        if not LOG_PATH.exists():
            return lines
        try:
            with open(LOG_PATH, "r", encoding="utf-8", errors="replace") as f:
                f.seek(self._log_offset)
                chunk = f.read()
                self._log_offset = f.tell()
            raw = [line.strip() for line in chunk.splitlines()]
            self._last_raw_lines = raw
            for line in raw:
                if "[DEMOBEAT]" in line:
                    lines.append(line)
                    self.mark("demobeat", {"line": line[-200:]})
        except OSError:
            pass
        return lines

    def drain_all_new(self) -> list:
        """The FULL unfiltered log tail from the most recent drain_demobeats()
        call (tb-0185, surprise_9d8b5ee25b0ed9dc).

        THE BUG THIS FIXES: sleepwalker._check_expect's `log_contains` branch
        used to receive ONLY drain_demobeats()'s [DEMOBEAT]-filtered return
        value, so it could never match any witness marker not wearing that
        literal tag — every H-21 marker emitted by the rung-2 generators
        ([GestureWheel], [Weather], [Memorial], [Sacrifice], [Footstep],
        [NPCTrade], ...) was structurally inaudible to log_contains, regardless
        of whether the feature behind it actually fired. gesture_wheel.beats.json's
        two log_contains expects failed UNCONDITIONALLY for this reason, not
        because TAB was unwired (it is wired — DemoPlayerController::OnTabPressed
        binds "DemoGestureWheel"->Tab per Config/DefaultInput.ini and calls
        GestureWheelWidget->OpenWheel(), which logs the exact string the beat
        checks for).

        WHY THIS IS SAFE (DEMOBEAT behavior stays byte-identical): this shares
        drain_demobeats()'s single offset cursor — no independent/second file
        read, still exactly one bounded per-beat read of the log tail (never
        the whole file) — and is a strict SUPERSET of its [DEMOBEAT]-filtered
        sibling (every [DEMOBEAT] line is also a raw line), so any existing
        log_contains expect that matched inside a [DEMOBEAT] line still matches
        exactly as before; this only ADDS visibility, it narrows nothing.

        Call drain_demobeats() first in each polling cycle — this method does
        NOT itself advance the read cursor, so calling it without a preceding
        drain_demobeats() this cycle returns stale (previous cycle's) data."""
        return list(self._last_raw_lines)

    def finalize(self) -> str:
        CHRONICLE_DIR.mkdir(parents=True, exist_ok=True)
        out = CHRONICLE_DIR / f"{self.session}.json"
        payload = {
            "session": self.session,
            "source": self.source,
            "written": _now(),
            "events": self.events,
        }
        out.write_text(json.dumps(payload, indent=1), encoding="utf-8")
        return str(out)


def main():
    """CLI mode for HUMAN sessions: poll runtime + demobeats until Ctrl+C or --duration."""
    import argparse
    parser = argparse.ArgumentParser(description="Witness a playtest session")
    parser.add_argument("--session", required=True)
    parser.add_argument("--duration", type=int, default=900, help="seconds (default 15 min)")
    parser.add_argument("--poll", type=int, default=10, help="runtime poll interval seconds")
    parser.add_argument("--out", default=None, help="chronicle output path (default Saved/SessionChronicles/<session>.json)")
    args = parser.parse_args()

    from core.telemetry_probe import MCPStdioClient
    w = Witness(args.session, source="human-session-witness")
    c = MCPStdioClient()
    end = time.monotonic() + args.duration
    print(f"[witness] session={args.session} for {args.duration}s (Ctrl+C to stop)")
    try:
        while time.monotonic() < end:
            w.drain_demobeats()
            try:
                r = c.call("inspect", {"action": "runtime_report"})
                res = r.get("result", {}).get("structuredContent", {}).get("result", {}) or {}
                pawn = res.get("pawn") or {}
                loc = (pawn.get("transform") or {}).get("location") or {}
                w.mark("runtime", {"isPIE": res.get("isPIE"),
                                   "pawn": pawn.get("label"),
                                   "loc": [loc.get("x"), loc.get("y"), loc.get("z")]})
            except Exception as e:
                w.mark("poll_error", {"error": str(e)[:120]})
            time.sleep(args.poll)
    except KeyboardInterrupt:
        pass
    path = w.finalize()
    if args.out:
        import shutil
        shutil.copyfile(path, args.out)
        path = args.out
    print(f"[witness] chronicle -> {path} ({len(w.events)} events)")


if __name__ == "__main__":
    main()
