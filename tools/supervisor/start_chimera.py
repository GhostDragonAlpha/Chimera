"""start_chimera.py -- bring the whole stack up, once, no duplicates.

Detects the live stack first (port + HTTP health on each piece): if all
three pieces are healthy it prints "stack already up" and exits 0 without
starting anything. Otherwise it starts only the dead pieces, in order
engine -> game shell -> website, waiting between starts and retrying once
per piece before giving up.

Run:  python tools/supervisor/start_chimera.py [--config pieces.json]

Pieces (default config):
  engine      .tmp/build_tick/Release/chimera_engine.exe 8107 --hidden
              (spawned directly -- NOT via launch_chimera.bat, which detaches;
              127.0.0.1:8107; needs shaders/ next to the exe)
  game_shell  python tools/game_shell/server.py 8206      (127.0.0.1:8206)
  website     python tools/website/server.py 8210         (127.0.0.1:8210)

Health checks:
  engine      GET /tick_state   body contains "ticks"
  game_shell  GET /api/health   JSON with ok == true
  website     GET /             HTTP 200

--config takes a JSON file shaped like DEFAULT_CONFIG["pieces"], used for
throwaway tests on alternate ports (see watchdog.py).
"""
from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[2]
CREATE_FLAGS = (
    subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
    if sys.platform == "win32"
    else 0
)

DEFAULT_CONFIG = {
    "pieces": [
        {
            # Spawn the exe DIRECTLY (not via launch_chimera.bat): the bat
            # detaches the engine with `start ""`, so the watchdog's child
            # handle is a cmd wrapper that exits at once -- the engine could
            # never be terminated on shutdown. Direct spawn = the handle IS
            # the engine. The exe needs shaders/ next to it (same dir as the
            # bat provides); world state/session logs still land in cwd.
            "name": "engine",
            "argv": ["chimera_engine.exe", "8107", "--hidden"],
            "cwd": ".tmp/build_tick/Release",
            "check": {"url": "http://127.0.0.1:8107/tick_state", "mode": "ticks"},
            "boot_seconds": 40,
        },
        {
            "name": "game_shell",
            "argv": [sys.executable, "tools/game_shell/server.py", "8206"],
            "cwd": ".",
            "check": {"url": "http://127.0.0.1:8206/api/health", "mode": "ok_json"},
            "boot_seconds": 10,
        },
        {
            "name": "website",
            "argv": [sys.executable, "tools/website/server.py", "8210"],
            "cwd": ".",
            "check": {"url": "http://127.0.0.1:8210/", "mode": "status200"},
            "boot_seconds": 10,
        },
    ]
}


def load_config(path: str | None) -> dict:
    """The default stack, or a JSON override ({"pieces": [...]})."""
    if not path:
        return DEFAULT_CONFIG
    return json.loads(Path(path).read_text(encoding="utf-8"))


def port_open(url: str) -> bool:
    """Is the host:port inside this URL listening?"""
    p = urlparse(url)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex((p.hostname or "127.0.0.1", p.port or 80)) == 0


def healthy(check: dict) -> bool:
    """Port listening AND the piece's HTTP health check passing."""
    url = check["url"]
    if not port_open(url):
        return False
    mode = check.get("mode", "status200")
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            if mode == "status200":
                return r.status == 200
            body = r.read().decode("utf-8", "replace")
            if mode == "ticks":
                return "ticks" in body
            if mode == "ok_json":
                return bool(json.loads(body).get("ok"))
    except Exception:
        return False
    return False


def spawn(piece: dict, spawned: list | None = None):
    """Start one piece detached; remember the handle for clean shutdown."""
    argv = [str(a) for a in piece["argv"]]
    cwd = ROOT / piece.get("cwd", ".")
    # A bare executable name ("chimera_engine.exe") must resolve against the
    # PIECE's cwd, not the caller's -- Windows CreateProcess does not use the
    # child cwd for the executable lookup (WinError 2). Resolving it here also
    # keeps the spawned handle on the engine process ITSELF, so shutdown can
    # actually stop it (the old launch_chimera.bat route detached the engine
    # via `start ""` and the watchdog's child was a cmd wrapper that exits
    # instantly -- Ctrl+C could never stop the engine it started).
    exe = Path(argv[0])
    if exe.suffix.lower() in (".exe", ".bat", ".cmd") and not exe.is_absolute():
        cand = cwd / exe
        if cand.exists():
            argv[0] = str(cand)
    cwd = str(cwd)
    p = subprocess.Popen(
        argv, cwd=cwd, creationflags=CREATE_FLAGS,
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if spawned is not None:
        spawned.append(p)
    return p


def ensure_piece(piece: dict, spawned: list | None = None, log=print) -> bool:
    """Start one piece and wait for health; retry once before giving up."""
    name = piece["name"]
    for attempt in (1, 2):
        if healthy(piece["check"]):
            return True
        log(f"piece={name} action=starting attempt={attempt}")
        spawn(piece, spawned)
        deadline = time.time() + piece.get("boot_seconds", 10)
        while time.time() < deadline:
            time.sleep(1)
            if healthy(piece["check"]):
                log(f"piece={name} action=up")
                return True
        log(f"piece={name} action=start_failed attempt={attempt}")
    return False


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    cfg_path = None
    if "--config" in args:
        cfg_path = args[args.index("--config") + 1]
    pieces = load_config(cfg_path)["pieces"]

    # THE DETECTION PATH: check every piece first, start nothing if all live.
    down = [p for p in pieces if not healthy(p["check"])]
    if not down:
        print("stack already up", flush=True)
        return 0

    spawned: list = []
    failed = []
    for piece in down:  # engine first, then its front doors
        if not ensure_piece(piece, spawned):
            failed.append(piece["name"])
        time.sleep(2)  # wait between starts
    if failed:
        print(f"failed to start: {', '.join(failed)}", flush=True)
        return 1
    print("stack up", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
