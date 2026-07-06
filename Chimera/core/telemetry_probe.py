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
import os
import re
import subprocess
import time
from pathlib import Path

LOG_DIR = Path("E:/PythonChimera/Chimera/Saved/Logs")
FATAL_MARKERS = ("Fatal error", "Assertion failed", "LowLevelFatalError", "=== Critical error")
MCP_CLI = r"E:\ChiR24-Unreal_mcp-test\dist\cli.js"


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


class MCPStdioClient:
    """Minimal MCP-over-stdio client for the chiR24 bridge CLI (newline-delimited JSON-RPC)."""

    def __init__(self):
        env = dict(os.environ, UE_PROJECT_PATH=r"E:\PythonChimera\Chimera")
        self.proc = subprocess.Popen(["node", MCP_CLI], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env)
        self._id = 0
        self._send({"jsonrpc": "2.0", "id": self._next(), "method": "initialize",
                    "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                               "clientInfo": {"name": "telemetry-probe", "version": "1.0"}}})
        if not self._read(self._id):
            raise RuntimeError("MCP initialize failed")
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def _next(self):
        self._id += 1
        return self._id

    def _send(self, obj):
        self.proc.stdin.write((json.dumps(obj) + "\n").encode())
        self.proc.stdin.flush()

    def _read(self, id_, timeout=30):
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = self.proc.stdout.readline()
            if not line:
                time.sleep(0.05)
                continue
            try:
                msg = json.loads(line.decode("utf-8", errors="replace"))
            except json.JSONDecodeError:
                continue
            if msg.get("id") == id_:
                return msg
        return None

    def call(self, tool: str, arguments: dict):
        self._send({"jsonrpc": "2.0", "id": self._next(), "method": "tools/call",
                    "params": {"name": tool, "arguments": arguments}})
        return self._read(self._id)

    def close(self):
        try:
            self.proc.kill()
        except OSError:
            pass


def _extract(pattern: str, msg) -> float | None:
    m = re.search(pattern, json.dumps(msg), re.IGNORECASE)
    return float(m.group(1)) if m else None


def probe_fps(client: "MCPStdioClient"):
    try:
        result = client.call("inspect", {"action": "get_performance_stats"})
        fps = _extract(r'fps"?\s*[:=]\s*"?([0-9.]+)', result)
        if fps is not None:
            return fps, "MCP get_performance_stats (stdio bridge)"
    except Exception as e:
        return None, f"engine unreachable ({type(e).__name__})"
    return None, "no fps field in performance stats"


def probe_growth(client: "MCPStdioClient", soak_seconds: int):
    def actor_count():
        result = client.call("inspect", {"action": "get_performance_stats"})
        count = _extract(r'actorCount"?\s*[:=]\s*"?(\d+)', result)
        return int(count) if count is not None else None
    try:
        first = actor_count()
        if first is None:
            return None, "no actor count in performance stats"
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
        client = None
        try:
            client = MCPStdioClient()
        except Exception as e:
            notes["engine"] = f"bridge unavailable ({type(e).__name__})"
        if client:
            fps, note = probe_fps(client)
            notes["fps"] = note
            if fps is not None:
                telemetry["fps"] = fps
                telemetry["target_fps"] = 60

            grew, note = probe_growth(client, args.soak)
            notes["unbounded_growth"] = note
            if grew is not None:
                telemetry["unbounded_growth"] = grew
            client.close()

    out = Path(args.out)
    out.write_text(json.dumps({"telemetry": telemetry, "notes": notes}, indent=2), encoding="utf-8")
    print(json.dumps({"telemetry": telemetry, "notes": notes}, indent=2))


if __name__ == "__main__":
    main()
