"""watchdog.py -- the stack watchdog: the game never stays dead.

Every 5 seconds it health-checks the three pieces (engine 8107, game
shell 8206, website 8210). Any dead piece is restarted through the same
starters start_chimera.py uses. Every event is one line -- timestamp,
piece, action -- written to watchdog.log next to this file AND stdout.
Ctrl+C stops the loop cleanly and terminates only the children this
watchdog itself spawned; pieces that were already running are untouched.

Run:  python tools/supervisor/watchdog.py [--config pieces.json]
                                            [--max-seconds N]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import start_chimera as starter  # the same starters, one definition

LOG_FILE = Path(__file__).resolve().parent / "watchdog.log"
INTERVAL = 5.0


def log(msg: str) -> None:
    line = f"{datetime.now().isoformat(timespec='seconds')} {msg}"
    print(line, flush=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def shutdown(spawned: list[subprocess.Popen]) -> int:
    """Terminate the children this watchdog spawned, and only those."""
    killed = 0
    for p in spawned:
        if p.poll() is None:
            try:
                p.terminate()
                killed += 1
            except OSError:
                pass
    for p in spawned:
        try:
            p.wait(timeout=5)
        except Exception:
            pass
    return killed


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Chimera stack watchdog")
    ap.add_argument("--config", help="JSON piece config override (alternate ports)")
    ap.add_argument("--max-seconds", type=float, default=None,
                    help="stop cleanly after N seconds (same path as Ctrl+C)")
    args = ap.parse_args(argv)

    pieces = starter.load_config(args.config)["pieces"]
    spawned: list[subprocess.Popen] = []
    log(f"watchdog_started pieces={','.join(p['name'] for p in pieces)} interval={INTERVAL:g}s")
    started = time.time()
    try:
        while True:
            for piece in pieces:
                if starter.healthy(piece["check"]):
                    continue
                log(f"piece={piece['name']} action=down")
                ok = starter.ensure_piece(piece, spawned, log=log)
                log(f"piece={piece['name']} action="
                    f"{'restarted' if ok else 'restart_failed'}")
            if args.max_seconds is not None and time.time() - started >= args.max_seconds:
                break
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        log("watchdog_interrupted")
    log("watchdog_stopping")
    killed = shutdown(spawned)
    log(f"watchdog_stopped children_terminated={killed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
