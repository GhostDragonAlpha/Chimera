"""Telemetry evidence collector for the result grader — zero model dependency.

Produces the grader's "telemetry" evidence sub-dict from real sources only:
- crash_free: newest UE log scanned for fatal/assertion markers
- fps: MCP performance stats when the engine is reachable; otherwise absent
- unbounded_growth: two scene-stat samples N seconds apart; absent if unmeasurable

NEVER fabricates: anything unmeasurable is omitted (scores zero in the rubric).

Usage:
    python -m core.telemetry_probe --out evidence.json [--soak 30] [--log path]
"""
import argparse
import json
import re
import time
import urllib.request
from pathlib import Path

LOG_DIR = Path("E:/PythonChimera/Chimera/Saved/Logs")
FATAL_MARKERS = ("Fatal error", "Assertion failed", "LowLevelFatalError", "=== Critical error")
MCP_URL = "http://localhost:3000/mcp"


def newest_log(explicit: str | None) -> Path | None:
    if explicit:
        p = Path(explicit)
        return p if p.exists() else None
    if not LOG_DIR.exists():
        return None
    logs = sorted(LOG_DIR.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    return logs[0] if logs else None


def check_crash_free(log_path: Path | None):
    if not log_path:
        return None, "no log found"
    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return None, f"log unreadable: {e}"
    hits = [m for m in FATAL_MARKERS if m in text]
    return (len(hits) == 0), (f"markers found: {hits}" if hits else f"clean ({log_path.name})")


def mcp_call(tool: str, arguments: dict, timeout: float = 5.0):
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": tool, "arguments": arguments},
    }).encode("utf-8")
    req = urllib.request.Request(MCP_URL, data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def probe_fps():
    try:
        result = mcp_call("inspect", {"action": "get_performance_stats"})
        text = json.dumps(result)
        m = re.search(r'"?fps"?\s*[:=]\s*([0-9.]+)', text, re.IGNORECASE)
        if m:
            return float(m.group(1)), "MCP get_performance_stats"
    except Exception as e:
        return None, f"engine unreachable ({type(e).__name__})"
    return None, "no fps field in performance stats"


def probe_growth(soak_seconds: int):
    def actor_count():
        result = mcp_call("inspect", {"action": "get_scene_stats"})
        m = re.search(r'"?actor_?count"?\s*[:=]\s*(\d+)', json.dumps(result), re.IGNORECASE)
        return int(m.group(1)) if m else None
    try:
        first = actor_count()
        if first is None:
            return None, "no actor count in scene stats"
        time.sleep(soak_seconds)
        second = actor_count()
        if second is None:
            return None, "second sample failed"
        grew = second > first * 1.05
        return grew, f"actors {first} -> {second} over {soak_seconds}s"
    except Exception as e:
        return None, f"engine unreachable ({type(e).__name__})"


def main():
    parser = argparse.ArgumentParser(description="Collect telemetry evidence for the result grader")
    parser.add_argument("--out", required=True, help="Path to write the telemetry evidence JSON")
    parser.add_argument("--soak", type=int, default=30, help="Seconds between growth samples")
    parser.add_argument("--log", help="Explicit UE log path (default: newest in Saved/Logs)")
    parser.add_argument("--skip-engine", action="store_true", help="Log-only probe (no MCP)")
    args = parser.parse_args()

    telemetry, notes = {}, {}

    crash_free, note = check_crash_free(newest_log(args.log))
    notes["crash_free"] = note
    if crash_free is not None:
        telemetry["crash_free"] = crash_free

    if not args.skip_engine:
        fps, note = probe_fps()
        notes["fps"] = note
        if fps is not None:
            telemetry["fps"] = fps
            telemetry["target_fps"] = 60

        grew, note = probe_growth(args.soak)
        notes["unbounded_growth"] = note
        if grew is not None:
            telemetry["unbounded_growth"] = grew

    out = Path(args.out)
    out.write_text(json.dumps({"telemetry": telemetry, "notes": notes}, indent=2), encoding="utf-8")
    print(json.dumps({"telemetry": telemetry, "notes": notes}, indent=2))


if __name__ == "__main__":
    main()
