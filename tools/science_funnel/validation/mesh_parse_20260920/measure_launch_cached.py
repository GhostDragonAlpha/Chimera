"""measure_launch_cached.py -- F2-BAR's full-boot half (lane
mesh-parse-20260920; the landed lane's instrument, pointed at this lane's
directory and at THIS worktree's engine build).

PASS (server half) = t_first_verts < 10 s, the slice's own launch clause --
the same bar slice_real_body_20260920 preregistered, measured RED at
135.73 s on the OBJ-route boot, and left standing to its successor.

The boot here rides the admission caches: the derived GLB through the
engine's kind-'G' door and the cached ghost bytes. scene["body"] carries the
boot's own import_route ('cache') and the unchanged scene sha (the pinned
OBJ's sha). 3 boots: the bar and F4's boot-path byte stability in one run.
Writes launch_timeline_cached.json HERE.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SLICE = ROOT / "tools" / "playable_slice"
LANDED = HERE.parent / "slice_real_body_20260920"
EXE = ROOT / ".tmp" / "slice_build" / "Release" / "chimera_engine.exe"
PIN = "bc9033bfc6c54db0220364821ee19028bf2ac6f740dc70f4c1e9be5f02089111"


def sweep_own_engines() -> None:
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         str(LANDED / "sweep_own_engines.ps1"), "-ExePath", str(EXE)],
        capture_output=True, text=True)


def one_boot(n: int) -> dict:
    sweep_own_engines()
    sys.path.insert(0, str(SLICE))
    import scene_boot as sb
    port = sb.free_port()
    marks = {"boot": n, "port": port}
    t0 = time.perf_counter()
    log = open(HERE / f"launch_server_log_boot{n}.txt", "w", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, str(SLICE / "slice_server.py"), "--port", str(port)],
        cwd=str(ROOT), stdout=log, stderr=subprocess.STDOUT, text=True)
    base = f"http://127.0.0.1:{port}"
    try:
        while time.perf_counter() - t0 < 180:
            try:
                with urllib.request.urlopen(base + "/api/health",
                                            timeout=4) as r:
                    h = json.loads(r.read())
                if "t_server_up" not in marks:
                    marks["t_server_up"] = round(time.perf_counter() - t0, 2)
                if h.get("world_booted"):
                    marks["t_world_up"] = round(time.perf_counter() - t0, 2)
                    break
            except OSError:
                pass
            time.sleep(0.02)
        while time.perf_counter() - t0 < 180:
            try:
                with urllib.request.urlopen(base + "/api/verts",
                                            timeout=8) as r:
                    nverts = int.from_bytes(r.read(4), "little")
                marks["t_first_verts"] = round(time.perf_counter() - t0, 2)
                marks["first_verts_count"] = nverts
                break
            except (OSError, TimeoutError):
                time.sleep(0.02)
        while time.perf_counter() - t0 < 180:
            try:
                st = json.loads(urllib.request.urlopen(
                    base + "/api/status", timeout=5).read())
                scene = st.get("scene") or {}
                if scene.get("settled"):
                    marks["t_settled"] = round(time.perf_counter() - t0, 2)
                    marks["scene_sha256"] = scene.get("scene_sha256")
                    marks["start_state_sha256"] = scene.get(
                        "start_state_sha256")
                    body = scene.get("body") or {}
                    marks["import_route"] = body.get("import_route")
                    marks["import_ok"] = body.get("import_stats", {}).get(
                        "tris") == 499976
                    ghost = scene.get("ghost") or {}
                    marks["ghost_source"] = ghost.get("ghost_source")
                    break
            except (OSError, TimeoutError):
                time.sleep(0.1)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        log.close()
    marks["pass_server_side"] = marks.get("t_first_verts", 999) < 10.0
    return marks


def main() -> int:
    out = {"falsifier": "F-SLICE-LAUNCH bar, full boot, cached import",
           "bar_s": 10.0, "landed_RED_number_s": 135.73, "boots": []}
    for n in range(3):
        m = one_boot(n)
        out["boots"].append(m)
        print(json.dumps(m, indent=1), flush=True)
        (HERE / "launch_timeline_cached.json").write_text(
            json.dumps(out, indent=1), encoding="utf-8")
    b = out["boots"]
    out["t_first_verts_s"] = [x.get("t_first_verts") for x in b]
    out["scene_sha_equals_payload_pin_all"] = all(
        x.get("scene_sha256") == PIN for x in b)
    out["import_route_all"] = sorted({x.get("import_route") for x in b})
    out["start_state_sha_equal_x3"] = len(
        {x.get("start_state_sha256") for x in b}) == 1
    out["pass_all_boots"] = all(x.get("pass_server_side") for x in b)
    (HERE / "launch_timeline_cached.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: out[k] for k in
                      ("t_first_verts_s", "import_route_all",
                       "scene_sha_equals_payload_pin_all",
                       "start_state_sha_equal_x3", "pass_all_boots")},
                     indent=1))
    return 0 if out["pass_all_boots"] else 1


if __name__ == "__main__":
    sys.exit(main())
