"""measure_restart_realbody.py -- F-SLICE-RESTART on the real body (lane
slice_real_body_20260920; adapted from playable_slice_20260921's harness: the
server now boots THE REAL BODY, and the scene sha must equal the payload's
manifest pin, not just match across boots).

Three independent worlds (the server's own boot, then two /api/restart), each
waited for the settled start; the recorded scene sha and settled start-state
sha (/verts bytes) are compared across boots AND against the pin.

Same scene sha (== pin) AND same start sha x3 = PASS.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SLICE = HERE.parents[3] / "tools" / "playable_slice"
ROOT = SLICE.parents[1]
PIN_MANIFEST = (ROOT / "tools/science_funnel/data/morphosource_ct/"
                "meshes_body_20260922/body_manifest.json")


def post(base: str, path: str, timeout: int = 30) -> dict:
    req = urllib.request.Request(base + path, data=b"{}", method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def get_json(base: str, path: str, timeout: int = 30) -> dict:
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return json.loads(r.read().decode())


def get_bytes(base: str, path: str, timeout: int = 60, attempts: int = 12) -> bytes:
    last = None
    for i in range(attempts):
        try:
            with urllib.request.urlopen(base + path, timeout=timeout) as r:
                return r.read()
        except OSError as e:
            last = e
            time.sleep(1.0 * (i + 1))
    raise last


def wait_boot_swapped(base: str, prev_sha: str | None, timeout: float = 90.0):
    """Wait until the server's boot() has REPLACED the scene spec (the old
    spec stays visible -- settled=True -- while the engine restarts; polling
    verts in that window races the swap, measured this lane as a 502)."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            scene = get_json(base, "/api/status").get("scene")
        except OSError:
            time.sleep(0.3)
            continue
        if not scene or not scene.get("settled") \
                or scene.get("scene_sha256") != prev_sha:
            return
        time.sleep(0.2)


def wait_settled(base: str, timeout: float = 120.0) -> dict:
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
    pin = json.loads(PIN_MANIFEST.read_text())["import_payload"]["sha256"]
    port = sb.free_port()
    log = open(HERE / "restart_server_log_realbody.txt", "w", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, "-X", "faulthandler",
         str(SLICE / "slice_server.py"), "--port", str(port)],
        cwd=str(ROOT), stdout=log, stderr=subprocess.STDOUT, text=True)
    base = f"http://127.0.0.1:{port}"
    out = {"falsifier": "F-SLICE-RESTART", "body": "the real skeleton",
           "payload_pin_sha256": pin, "restarts": []}
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
        prev_sha = None
        for i in range(3):     # boot + two restarts
            if i:
                post(base, "/api/restart")
                wait_boot_swapped(base, prev_sha)
            st = wait_settled(base)
            scene = st.get("scene", {})
            prev_sha = scene.get("scene_sha256")
            verts = get_bytes(base, "/api/verts")
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
        scene_is_pin = all(x["scene_sha256"] == pin for x in r)
        out["same_scene_sha"] = same_scene
        out["same_start_state_sha"] = same_start
        out["scene_sha_equals_payload_pin"] = scene_is_pin
        out["pass"] = bool(same_scene and same_start and scene_is_pin)
        out["law"] = ("the import bytes are committed bytes (sha == the "
                      "manifest pin); the engine's tick is deterministic; the "
                      "settled start rides the root law's attractor -- the "
                      "start-state sha is the measured evidence")
    finally:
        # kill the TREE: terminating only the server orphans its engine child
        # (measured this lane -- orphans crashed the next boot's import)
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                       capture_output=True)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
    (HERE / "restart_measurement_realbody.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))
    return 0 if out["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
