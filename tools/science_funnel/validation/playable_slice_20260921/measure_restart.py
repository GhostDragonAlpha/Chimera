"""measure_restart.py -- F-SLICE-RESTART: a session restarts byte-clean.

Two independent restarts of the slice world (the server's own /api/restart,
waited for by polling), then the recorded scene sha and the settled
start-state sha (/verts bytes) are compared. Same scene sha AND same start
sha = PASS; any difference = FAIL, recorded with both shas.

The determinism chain: the import bytes are a pure function of committed
files (scene_boot, byte-checked twice at build), the engine's tick is
deterministic, and the settled start rides an attractor (the root law's
equilibrium) -- the measured start sha is the evidence, not the assumption.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SLICE = HERE.parents[3] / "tools" / "playable_slice"
ROOT = SLICE.parents[1]


def post(base: str, path: str, timeout: int = 30) -> dict:
    req = urllib.request.Request(base + path, data=b"{}", method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def get_json(base: str, path: str, timeout: int = 30) -> dict:
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return json.loads(r.read().decode())


def get_bytes(base: str, path: str, timeout: int = 60, attempts: int = 4) -> bytes:
    last = None
    for i in range(attempts):
        try:
            with urllib.request.urlopen(base + path, timeout=timeout) as r:
                return r.read()
        except OSError as e:
            last = e
            time.sleep(0.5 * (i + 1))
    raise last


def wait_settled(base: str, timeout: float = 90.0) -> dict:
    t0 = time.time()
    st = {}
    while time.time() - t0 < timeout:
        try:
            st = get_json(base, "/api/status")
        except OSError:
            time.sleep(0.5)
            continue
        if st.get("scene", {}).get("settled"):
            return st
        time.sleep(0.3)
    return st


def main() -> int:
    sys.path.insert(0, str(SLICE))
    import scene_boot as sb
    port = sb.free_port()
    log = open(HERE / "restart_server_log.txt", "w", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, "-X", "faulthandler",
         str(SLICE / "slice_server.py"), "--port", str(port)],
        cwd=str(ROOT), stdout=log, stderr=subprocess.STDOUT, text=True)
    base = f"http://127.0.0.1:{port}"
    out = {"falsifier": "F-SLICE-RESTART", "restarts": []}
    try:
        t0 = time.time()
        while time.time() - t0 < 90:
            try:
                h = get_json(base, "/api/health", timeout=3)
                if h.get("ok"):
                    break
            except OSError:
                pass
            time.sleep(0.5)
        for i in range(3):     # boot + two restarts
            if i:
                post(base, "/api/restart")
            st = wait_settled(base)
            scene = st.get("scene", {})
            verts = get_bytes(base, "/api/verts")
            import hashlib
            served_sha = hashlib.sha256(verts).hexdigest()
            out["restarts"].append({
                "n": i,
                "scene_sha256": scene.get("scene_sha256"),
                "start_state_sha256": scene.get("start_state_sha256"),
                "served_verts_sha256_unoffset": served_sha,
                "settled_root_y": scene.get("start_root_y"),
            })
            time.sleep(0.5)
        r = out["restarts"]
        same_scene = len({x["scene_sha256"] for x in r}) == 1
        same_start = len({x["start_state_sha256"] for x in r}) == 1
        out["same_scene_sha"] = same_scene
        out["same_start_state_sha"] = same_start
        out["pass"] = bool(same_scene and same_start)
        out["law"] = ("the import bytes are a pure function of committed files; "
                      "the settled start rides the root law's attractor; the "
                      "start-state sha is the measured evidence")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    (HERE / "restart_measurement.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))
    return 0 if out["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
