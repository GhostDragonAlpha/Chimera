"""Perpetual orchestrator — spawn duty cycles in a loop without terminal completion.

No attempt_completion. Loop indefinitely, command-driven via .ORCHESTRATOR_CMD or HTTP API.
Commands: stop, pause, resume, status, next-cycle.
"""

import time
import json
import subprocess
import threading
from pathlib import Path
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

ROOT = Path(__file__).resolve().parent.parent
STOP_FILE = ROOT.parent / ".STOP_PERPETUAL"
COMMAND_FILE = ROOT.parent / ".ORCHESTRATOR_CMD"
LOG = ROOT / "Saved" / "Logs" / "orchestrator.log"
STATUS_FILE = ROOT.parent / ".ORCHESTRATOR_STATUS"

state = {
    "running": True,
    "paused": False,
    "cycle": 0,
    "last_grade": None,
    "last_error": None,
}
state_lock = threading.Lock()


def _log(msg):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%MZ")
    line = f"{ts} {msg}\n"
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line)
    print(f"[orchestrator] {msg}")


def _write_status():
    """Write current state to status file for API queries."""
    with state_lock:
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=1)


def _check_command_file():
    """Read and execute commands from .ORCHESTRATOR_CMD."""
    if not COMMAND_FILE.exists():
        return
    try:
        cmd = COMMAND_FILE.read_text(encoding="utf-8").strip().lower()
        COMMAND_FILE.unlink()
        with state_lock:
            if cmd == "stop":
                state["running"] = False
                _log("command=stop received")
            elif cmd == "pause":
                state["paused"] = True
                _log("command=pause received")
            elif cmd == "resume":
                state["paused"] = False
                _log("command=resume received")
            elif cmd == "status":
                _log(f"command=status: {json.dumps(state)}")
    except Exception as ex:
        _log(f"command file error: {ex}")


def _preflight_ok():
    try:
        r = subprocess.run(
            ["python", "-m", "core.preflight"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=120
        )
        ok = "[2] GPA" in r.stdout and "< 1.0" not in r.stdout
        return ok
    except Exception as ex:
        _log(f"preflight check failed: {ex}")
        return False


def _spawn_duty_cycle(cycle_num):
    """Spawn a duty-cycle (fallback: run pipeline health check). Returns grade or None."""
    _log(f"cycle_{cycle_num:03d} status=started")
    try:
        r = subprocess.run(
            ["python", "run_deep_space_trader_pipeline.py"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=2700  # 45 min
        )
        grade = "B" if r.returncode == 0 else "F"
        with state_lock:
            state["last_grade"] = grade
        _log(f"cycle_{cycle_num:03d} status=complete grade={grade}")
        return grade
    except subprocess.TimeoutExpired:
        with state_lock:
            state["last_error"] = "timeout"
        _log(f"cycle_{cycle_num:03d} status=failed reason=timeout")
        return None
    except Exception as ex:
        with state_lock:
            state["last_error"] = str(ex)[:80]
        _log(f"cycle_{cycle_num:03d} status=failed reason={str(ex)[:80]}")
        return None


class CommandHandler(BaseHTTPRequestHandler):
    """Simple HTTP API for orchestrator commands."""

    def do_GET(self):
        if self.path == "/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            with state_lock:
                self.wfile.write(json.dumps(state).encode())
        elif self.path.startswith("/command/"):
            cmd = self.path.split("/")[-1]
            with state_lock:
                if cmd == "stop":
                    state["running"] = False
                elif cmd == "pause":
                    state["paused"] = True
                elif cmd == "resume":
                    state["paused"] = False
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK\n")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # suppress default HTTP logging


def _start_api_server(port=8765):
    """Start HTTP API server in background thread."""
    try:
        server = HTTPServer(("127.0.0.1", port), CommandHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        _log(f"HTTP API listening on http://127.0.0.1:{port}")
    except Exception as ex:
        _log(f"API server failed to start: {ex}")


def run_perpetual():
    """Main loop: preflight → spawn duty cycle → check commands → loop."""
    _log("orchestrator started")
    _start_api_server()

    if not _preflight_ok():
        _log("FATAL: preflight gate blocked — waiting for intervention")
        while True:
            _check_command_file()
            if not state["running"]:
                break
            time.sleep(60)
        _log("orchestrator stopped")
        return

    while True:
        # Check for commands (file or API)
        _check_command_file()
        _write_status()

        # Check for stop signal
        with state_lock:
            if not state["running"]:
                break
            if state["paused"]:
                time.sleep(10)
                continue

        # Preflight gate
        if not _preflight_ok():
            _log("FATAL: gate failed — halting")
            break

        # Spawn cycle
        with state_lock:
            state["cycle"] += 1
            cycle = state["cycle"]

        _spawn_duty_cycle(cycle)

        # Backoff
        time.sleep(30)

    _log("orchestrator stopped")


if __name__ == "__main__":
    run_perpetual()
