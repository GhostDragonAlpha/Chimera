"""rbmovie_boot_check.py -- the boot check BEFORE the movie (lane
realbody-movie-20260920). Starts the slice server through the CACHED path and
measures the timeline the landed mesh-parse lane claimed (full boot ~2.1 s):
t_server_up, t_world_up, t_first_verts, import_route (cache|fresh), t_settled.

PASS bar (the slice's own): t_first_verts < 10 s (F-SLICE-LAUNCH's bar; the
mesh-parse lane's claim is ~2 s through the cache). The browser half is NOT
this instrument's job; the movie capture records the page's own console.

Output: boot_timing.json beside this file. Exit 0 iff t_first_verts < 10 s
and import_route == "cache".
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
EXE = ROOT / ".tmp" / "slice_build" / "Release" / "chimera_engine.exe"


def main() -> int:
    sys.path.insert(0, str(SLICE))
    import scene_boot as sb

    r = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         str(HERE.parent / "slice_real_body_20260920" / "sweep_own_engines.ps1"),
         "-ExePath", str(EXE)], capture_output=True, text=True)
    print(r.stdout.strip(), flush=True)

    port = sb.free_port()
    out = {"schema": "chimera.realbody_movie_20260920.boot_check.v1",
           "port": port, "engine_exe": str(EXE)}
    t0 = time.perf_counter()
    log = open(HERE / "boot_server_log.txt", "w", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, str(HERE / "rbmovie_server_launcher.py"),
         "--port", str(port), "--engine-exe", str(EXE),
         "--log", str(HERE / "boot_server_log.txt")],
        cwd=str(ROOT), stdout=log, stderr=subprocess.STDOUT)
    base = f"http://127.0.0.1:{port}"
    try:
        while time.perf_counter() - t0 < 120:
            try:
                with urllib.request.urlopen(base + "/api/health", timeout=4) as rsp:
                    h = json.loads(rsp.read())
                if "t_server_up" not in out:
                    out["t_server_up"] = round(time.perf_counter() - t0, 2)
                if h.get("world_booted"):
                    out["t_world_up"] = round(time.perf_counter() - t0, 2)
                    break
            except OSError:
                pass
            time.sleep(0.05)
        else:
            out["error"] = "world never booted within 120 s"
        if out.get("t_world_up") is not None:
            while time.perf_counter() - t0 < 120:
                try:
                    with urllib.request.urlopen(base + "/api/verts", timeout=8) as rsp:
                        n = int.from_bytes(rsp.read(4), "little")
                    out["t_first_verts"] = round(time.perf_counter() - t0, 2)
                    out["first_verts_count"] = n
                    break
                except (OSError, TimeoutError):
                    time.sleep(0.05)
        deadline = time.perf_counter() + 90
        while time.perf_counter() < deadline:
            try:
                st = json.loads(urllib.request.urlopen(base + "/api/status",
                                                       timeout=5).read())
                sc = st.get("scene") or {}
                if sc.get("settled"):
                    out["t_settled"] = round(time.perf_counter() - t0, 2)
                    body = sc.get("body") or {}
                    out["import_route"] = body.get("import_route")
                    out["import_bytes"] = body.get("import_bytes")
                    out["scene_sha256"] = (sc.get("scene_sha256") or "")[:16]
                    out["start_root_y"] = sc.get("start_root_y")
                    break
            except (OSError, TimeoutError):
                time.sleep(0.2)
        out["pass"] = (out.get("t_first_verts", 99) < 10.0
                       and out.get("import_route") == "cache")
        out["claim_under_test"] = "full boot ~2.1 s through the cached path (landed mesh-parse lane)"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
    (HERE / "boot_timing.json").write_text(json.dumps(out, indent=1),
                                           encoding="utf-8")
    print(json.dumps(out, indent=1), flush=True)
    return 0 if out.get("pass") else 1


if __name__ == "__main__":
    sys.exit(main())
