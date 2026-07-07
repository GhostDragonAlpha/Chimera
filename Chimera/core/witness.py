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

    def mark(self, kind: str, data: dict = None):
        self.events.append({
            "t": round(time.monotonic() - self.t0, 2),
            "utc": _now(),
            "kind": kind,
            "data": data or {},
        })

    def drain_demobeats(self) -> list:
        """Read NEW [DEMOBEAT] lines since the last drain; mark and return them."""
        lines = []
        if not LOG_PATH.exists():
            return lines
        try:
            with open(LOG_PATH, "r", encoding="utf-8", errors="replace") as f:
                f.seek(self._log_offset)
                chunk = f.read()
                self._log_offset = f.tell()
            for line in chunk.splitlines():
                if "[DEMOBEAT]" in line:
                    lines.append(line.strip())
                    self.mark("demobeat", {"line": line.strip()[-200:]})
        except OSError:
            pass
        return lines

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
