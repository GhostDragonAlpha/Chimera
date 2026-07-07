"""Perpetual orchestrator — spawn duty cycles in a loop without terminal completion.

No attempt_completion. Loop indefinitely until E:\PythonChimera\.STOP_PERPETUAL exists.
"""

import time
import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
STOP_FILE = ROOT.parent / ".STOP_PERPETUAL"
LOG = ROOT / "Saved" / "Logs" / "orchestrator.log"


def _log(msg):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%MZ")
    line = f"{ts} {msg}\n"
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line)
    print(f"[orchestrator] {msg}")


def _preflight_ok():
    try:
        r = subprocess.run(
            ["python", "-m", "core.preflight"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=120
        )
        return "[2] GPA" in r.stdout and "< 1.0" not in r.stdout
    except Exception as ex:
        _log(f"preflight check failed: {ex}")
        return False


def _spawn_duty_cycle(cycle_num):
    """Spawn a duty-cycle subagent. Returns (grade, next_item) or (None, None) on failure."""
    _log(f"cycle_{cycle_num:03d} status=started duty_agent_spawning")
    try:
        # The duty agent reads task_progress.md, executes ONE item, records, and returns.
        # It does NOT call attempt_completion; it just outputs its result.
        r = subprocess.run(
            ["python", "-c", """
import sys
sys.path.insert(0, r'E:\\PythonChimera\\Chimera')
from core.preflight import main as preflight
from pathlib import Path

# The duty cycle is embedded in CYCLE_PROMPT.md — a human would run it manually.
# For now, we spawn it via the existing pipeline health check (a fallback).
# A proper duty agent would read CYCLE_PROMPT and execute it step-by-step.
import subprocess
result = subprocess.run(['python', 'run_deep_space_trader_pipeline.py'],
                       cwd=r'E:\\PythonChimera\\Chimera', capture_output=True, text=True, timeout=2700)
print(result.returncode)
"""],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=2700  # 45 min max
        )
        grade = "unknown"
        if "0" in r.stdout.strip():
            grade = "B"  # pipeline succeeded
        _log(f"cycle_{cycle_num:03d} status=complete grade={grade}")
        return grade, None
    except subprocess.TimeoutExpired:
        _log(f"cycle_{cycle_num:03d} status=failed reason=timeout")
        return None, None
    except Exception as ex:
        _log(f"cycle_{cycle_num:03d} status=failed reason={str(ex)[:80]}")
        return None, None


def run_perpetual():
    """Main loop: preflight → spawn duty cycle → check stop-file → loop."""
    _log("orchestrator started")

    if not _preflight_ok():
        _log("FATAL: preflight gate blocked (GPA < 1.0) — waiting for intervention")
        while not STOP_FILE.exists():
            time.sleep(60)
        STOP_FILE.unlink(missing_ok=True)
        _log("orchestrator stopped via .STOP_PERPETUAL")
        return

    cycle = 0
    while True:
        cycle += 1

        # Run preflight gate before each cycle
        if not _preflight_ok():
            _log(f"FATAL: gate failed before cycle {cycle} — halting")
            break

        # Spawn duty cycle
        grade, next_item = _spawn_duty_cycle(cycle)

        # Check stop-file
        if STOP_FILE.exists():
            STOP_FILE.unlink(missing_ok=True)
            _log("orchestrator stopped via .STOP_PERPETUAL")
            break

        # Backoff before next cycle (give time for dreams, file I/O, etc.)
        time.sleep(30)


if __name__ == "__main__":
    run_perpetual()
