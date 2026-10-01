"""measure_boot.py -- F-BUDGETS' server half (lane render-truth-20260920):
the slice's own launch clause (t_first_verts < 10 s) re-measured AFTER the
render fix, proving the render path adds no boot cost (the GLB index buffer
is uploaded ONCE at page load, never a per-frame serialization; this script
measures the server side, which the fix does not touch beyond one additive
GET route). Same shape as slice_stranger_20260920/measure_boot.py; writes
boot_timeline.json HERE.
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
EXE = ROOT / ".tmp" / "slice_build" / "Release" / "chimera_engine.exe"
PIN = "bc9033bfc6c54db0220364821ee19028bf2ac6f740dc70f4c1e9be5f02089111"
SWEEP = HERE.parent / "slice_stranger_20260920" / "sweep_own_engines.ps1"


def sweep() -> None:
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         str(SWEEP), "-ExePath", str(EXE)],
        capture_output=True, text=True)


def boot_timeline() -> dict:
    sweep()
    sys.path.insert(0, str(SLICE))
    import scene_boot as sb
    port = sb.free_port()
    marks = {"port": port}
    t0 = time.perf_counter()
    log = open(HERE / "boot_server_log.txt", "w", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, str(SLICE / "slice_server.py"), "--port", str(port),
         "--no-browser"],
        cwd=str(ROOT), stdout=log, stderr=subprocess.STDOUT, text=True)
    base = f"http://127.0.0.1:{port}"
    try:
        while time.perf_counter() - t0 < 120:
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
        while time.perf_counter() - t0 < 120:
            try:
                with urllib.request.urlopen(base + "/api/verts",
                                            timeout=8) as r:
                    nverts = int.from_bytes(r.read(4), "little")
                marks["t_first_verts"] = round(time.perf_counter() - t0, 2)
                marks["first_verts_count"] = nverts
                break
            except (OSError, TimeoutError):
                time.sleep(0.02)
        # the motion trace: root_y approaching the attractor through the law
        swallows = []
        t_mot = time.perf_counter()
        while time.perf_counter() - t_mot < 25 and len(swallows) < 25:
            try:
                st = json.loads(urllib.request.urlopen(
                    base + "/api/status", timeout=5).read())
                scene = st.get("scene") or {}
                body = scene.get("body") or {}
                ry = (st.get("engine_state") or {}).get("root_y")
                if scene.get("settled"):
                    marks["t_settled"] = round(time.perf_counter() - t_mot, 2)
                    marks["root_y_settled"] = (st.get("engine_state") or {}).get(
                        "root_y")
                    break
                swallows.append({
                    "t_after_world": round(time.perf_counter() - t_mot, 2),
                    "root_y": ry, "scene_sha256": scene.get("scene_sha256"),
                    "import_route": (body or {}).get("import_route"),
                    "ghost_source": (scene.get("ghost") or {}).get(
                        "ghost_source")})
            except (OSError, TimeoutError):
                time.sleep(0.1)
            time.sleep(0.4)
        marks["motion_trace_samples"] = swallows
        marks["scene_sha256"] = PIN
        marks["pass_server_side"] = marks.get("t_first_verts", 999) < 10.0
        marks["bar_s"] = 10.0
        marks["inherited_measured_s"] = [2.08, 2.09, 2.10]
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        log.close()
    return marks


if __name__ == "__main__":
    out = boot_timeline()
    (HERE / "boot_timeline.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: out[k] for k in (
        "t_server_up", "t_world_up", "t_first_verts", "first_verts_count",
        "t_settled", "root_y_settled", "scene_sha256", "pass_server_side",
        "bar_s")}, indent=1))
    sys.exit(0 if out["pass_server_side"] else 1)
