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
FATAL_MARKERS = (
    "Fatal error",
    "Assertion failed",
    "LowLevelFatalError",
    "=== Critical error",
)
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
    return (len(hits) == 0), (
        f"markers found: {hits}" if hits else f"clean ({log_path.name})"
    )


class MCPStdioClient:
    """Minimal MCP-over-stdio client for the chiR24 bridge CLI (newline-delimited JSON-RPC)."""

    def __init__(self):
        env = dict(os.environ, UE_PROJECT_PATH=r"E:\PythonChimera\Chimera")
        self.proc = subprocess.Popen(
            [
                r"C:\\Users\\allen\\node-portable\\node-v22.23.1-win-x64\\node.exe",
                MCP_CLI,
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=env,
        )
        self._id = 0
        self._send(
            {
                "jsonrpc": "2.0",
                "id": self._next(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "telemetry-probe", "version": "1.0"},
                },
            }
        )
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
        self._send(
            {
                "jsonrpc": "2.0",
                "id": self._next(),
                "method": "tools/call",
                "params": {"name": tool, "arguments": arguments},
            }
        )
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


def probe_memory(client: "MCPStdioClient", soak_seconds: int):
    """Probe memory growth over soak period. Detects unbounded memory accumulation.

    Returns: (is_bounded, note_string)
    - is_bounded: False if memory grew >10% (unbounded), True if stable, None if unmeasurable
    - note: human-readable measurement summary
    """
    def get_memory_mb():
        result = client.call("inspect", {"action": "get_memory_stats"})
        # Try multiple field names for memory (varies by MCP implementation)
        for pattern in [
            r'usedPhysical"?\s*[:=]\s*"?([0-9.]+)',  # Used physical RAM
            r'usedVirtual"?\s*[:=]\s*"?([0-9.]+)',   # Used virtual
            r'peakUsed"?\s*[:=]\s*"?([0-9.]+)',      # Peak memory
            r'currentUsed"?\s*[:=]\s*"?([0-9.]+)',   # Current usage
            r'memoryUsedMB"?\s*[:=]\s*"?([0-9.]+)',  # Generic "used MB"
        ]:
            val = _extract(pattern, result)
            if val is not None:
                return val
        return None

    try:
        first = get_memory_mb()
        if first is None:
            return None, "no memory data in get_memory_stats"
        time.sleep(soak_seconds)
        second = get_memory_mb()
        if second is None:
            return None, "second memory sample failed"

        delta_mb = second - first
        pct_growth = (delta_mb / first * 100) if first > 0 else 0

        # >10% growth over soak window is suspicious (unbounded)
        is_bounded = pct_growth <= 10.0

        return is_bounded, f"memory {first:.1f}MB -> {second:.1f}MB ({pct_growth:+.1f}%) over {soak_seconds}s"
    except Exception as e:
        return None, f"engine unreachable ({type(e).__name__})"


def probe_frame_time_stability(client: "MCPStdioClient", soak_seconds: int):
    """Probe frame time variance and hitches over soak period. Detects micro-stutters.

    Collects frame time samples at ~10Hz intervals during soak.
    Returns: (is_stable, note_string)
    - is_stable: False if variance exceeds threshold (>15ms stddev or >50% frame spike), True if stable, None if unmeasurable
    - note: human-readable variance summary with hitch count
    """
    def get_frame_time_ms():
        result = client.call("inspect", {"action": "get_performance_stats"})
        # Try multiple frame time field names (varies by MCP implementation)
        for pattern in [
            r'frameTime"?\s*[:=]\s*"?([0-9.]+)',         # Generic frame time
            r'avgFrameTime"?\s*[:=]\s*"?([0-9.]+)',       # Average frame time
            r'lastFrameTime"?\s*[:=]\s*"?([0-9.]+)',      # Last frame time
            r'deltaTime"?\s*[:=]\s*"?([0-9.]+)',          # Delta time (can be in ms or s)
        ]:
            val = _extract(pattern, result)
            if val is not None:
                # If value looks like seconds (< 1), convert to ms
                return val * 1000 if val < 1 else val
        return None

    try:
        frame_times = []
        samples = max(3, soak_seconds // 2)  # Sample at ~2Hz over soak period
        interval = soak_seconds / samples

        for i in range(samples):
            ft = get_frame_time_ms()
            if ft is not None:
                frame_times.append(ft)
            if i < samples - 1:
                time.sleep(interval)

        if len(frame_times) < 2:
            return None, "insufficient frame time samples"

        # Calculate statistics
        mean_ft = sum(frame_times) / len(frame_times)
        variance = sum((x - mean_ft) ** 2 for x in frame_times) / len(frame_times)
        stddev = variance ** 0.5
        max_ft = max(frame_times)
        min_ft = min(frame_times)

        # Detect hitches: frames >50% slower than average
        hitch_threshold = mean_ft * 1.5
        hitches = [ft for ft in frame_times if ft > hitch_threshold]

        # Frame time is stable if stddev <= 15ms AND no major hitches
        is_stable = stddev <= 15.0 and len(hitches) == 0

        note = (
            f"frame times: avg={mean_ft:.2f}ms, stddev={stddev:.2f}ms, "
            f"range=[{min_ft:.2f}, {max_ft:.2f}]ms, hitches={len(hitches)}"
        )
        return is_stable, note
    except Exception as e:
        return None, f"engine unreachable ({type(e).__name__})"


def _foreground_appactivate() -> bool:
    """Ensure editor is foregrounded for honest fps measurement.

    H-13: Economy features repeatedly grade C/F on partial criteria coverage and unmeasured fps;
    run telemetry foregrounded and test every declared criterion before grading System_Economy.

    Background throttle freezes fps AND all Niagara/anim simulation — need foreground execution.

    Returns True ONLY if AppActivate reported it found + raised the editor window. That
    boolean is the honest signal malcolm needs: an fps sampled while the window was NOT
    focused is a GPU-throttle artifact (~3fps), never an authoritative frame time."""
    try:
        import subprocess

        # AppActivate returns $true iff it located + activated the window. Echo it so we
        # record an HONEST foreground flag instead of blindly assuming the raise worked.
        proc = subprocess.run(
            [
                "powershell",
                "-Command",
                "$w=New-Object -ComObject wscript.shell; $ok=$w.AppActivate('Unreal Editor'); "
                "Start-Sleep 1; Write-Output $ok",
            ],
            shell=True,
            check=False,
            capture_output=True,
            text=True,
        )
        return "true" in (proc.stdout or "").strip().lower()
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Collect telemetry evidence for the result grader"
    )
    parser.add_argument(
        "--out", required=True, help="Path to write the telemetry evidence JSON"
    )
    parser.add_argument(
        "--soak", type=int, default=30, help="Seconds between growth samples"
    )
    parser.add_argument(
        "--log", help="Explicit UE log path (default: newest in Saved/Logs)"
    )
    parser.add_argument(
        "--skip-engine", action="store_true", help="Log-only probe (no MCP)"
    )
    parser.add_argument(
        "--foreground",
        action="store_true",
        help="Ensure editor is foregrounded for honest fps measurement",
    )
    args = parser.parse_args()

    # H-13: Ensure foreground execution for honest telemetry if requested. Record
    # whether the raise actually succeeded so malcolm can distinguish an authoritative
    # frame time from a background-throttled (~3fps) artifact.
    fg_ok = _foreground_appactivate() if args.foreground else False

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

            is_memory_bounded, note = probe_memory(client, args.soak)
            notes["memory_bounded"] = note
            if is_memory_bounded is not None:
                telemetry["memory_bounded"] = is_memory_bounded

            is_frame_stable, note = probe_frame_time_stability(client, args.soak)
            notes["frame_time_stable"] = note
            if is_frame_stable is not None:
                telemetry["frame_time_stable"] = is_frame_stable

            client.close()

    out = Path(args.out)
    out.write_text(
        json.dumps({"telemetry": telemetry, "notes": notes}, indent=2), encoding="utf-8"
    )
    print(json.dumps({"telemetry": telemetry, "notes": notes}, indent=2))

    _write_malcolm_snapshot(telemetry, foregrounded=fg_ok)


def _editor_memory_gb() -> float:
    """System-memory sensor without extra deps: tasklist reports the editor
    process working set (KB). Honest scope: this is the EDITOR's footprint,
    the closest measurable proxy until packaged-build telemetry exists."""
    import subprocess
    try:
        out = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq UnrealEditor.exe", "/FO", "CSV",
             "/NH"],
            capture_output=True, text=True, timeout=10).stdout
        total_kb = 0
        for line in out.splitlines():
            cells = [c.strip('" ') for c in line.split('","')]
            if len(cells) >= 5 and "UnrealEditor" in cells[0]:
                total_kb += int(cells[4].replace(",", "").replace(".", "")
                                .replace(" K", "").replace("K", "") or 0)
        return round(total_kb / (1024 * 1024), 2) if total_kb else None
    except Exception:
        return None


def _write_malcolm_snapshot(telemetry: dict, foregrounded: bool = False) -> None:
    """Feed THE CONTAINER (core.malcolm): every foregrounded soak refreshes
    docs/world/telemetry_last.json with the axes malcolm can read — the
    sensors that turn hardware walls from admission-only into gated. Only
    honestly-measured keys are written; absent keys stay UNMEASURED.

    `foregrounded` travels WITH the fps: malcolm treats an unfocused frame time as
    UNMEASURED (not a breach), so a background sample never trips a false CONTAIN."""
    snapshot = {}
    if telemetry.get("fps"):
        snapshot["fps"] = telemetry["fps"]           # malcolm derives frame_time_ms
        snapshot["foregrounded"] = bool(foregrounded)  # honest: was the editor focused when sampled?
    mem = _editor_memory_gb()
    if mem is not None:
        snapshot["system_memory_gb"] = mem
    if not snapshot:
        return
    try:
        path = Path(__file__).resolve().parents[1] / "docs" / "world" / "telemetry_last.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        snapshot["ts"] = __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc).isoformat()[:19]
        path.write_text(json.dumps(snapshot, indent=1), encoding="utf-8")
        print(f"[malcolm] sensor snapshot -> {path.name}: {sorted(snapshot)}")
    except Exception as e:
        print(f"[malcolm] sensor snapshot failed: {e}")


if __name__ == "__main__":
    main()
