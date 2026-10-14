"""time_import.py -- isolated cost of the engine's own /mesh_import on the
pinned real-body payload (receipt evidence for F-SLICE-LAUNCH's RED: the
launch bar is dominated by the parse, not by anything the slice composes).
Engine only, no server, no ghost: start -> /frame -> time /mesh_import ->
/tick_gravity -> quit. Writes import_timing.json (HERE).
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SLICE = HERE.parents[3] / "tools" / "playable_slice"
sys.path.insert(0, str(SLICE))
import scene_boot as sb  # noqa: E402


def main() -> int:
    sb_free = sb.free_port()
    exe_dir = SLICE.parents[1] / ".tmp" / "slice_build" / "Release"
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         str(HERE / "sweep_own_engines.ps1"),
         "-ExePath", str(exe_dir / "chimera_engine.exe")],
        capture_output=True, text=True)
    proc = subprocess.Popen(
        [str(exe_dir / "chimera_engine.exe"), str(sb_free), "--no-restore",
         "--hidden"], cwd=str(exe_dir),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    url = f"http://127.0.0.1:{sb_free}"
    out = {"what": "isolated /mesh_import timing, pinned real-body payload "
                   "+ the first-boot ghost compose, each phase timed"}
    try:
        t0 = time.perf_counter()
        sb.wait_engine(url)
        out["t_engine_ready_s"] = round(time.perf_counter() - t0, 2)
        # the GHOST's first-boot cost (build_standing_layer_cached +
        # savetxt): in the server's boot path BEFORE the import
        t1 = time.perf_counter()
        gobj, grec = sb.build_ghost_obj()
        out["t_ghost_build_s"] = round(time.perf_counter() - t1, 2)
        out["ghost_bytes"] = len(gobj)
        obj, rec = sb.build_real_body()
        t2 = time.perf_counter()
        res = sb.http_post(url, "/mesh_import", b"O" + obj, timeout=600)
        out["t_mesh_import_s"] = round(time.perf_counter() - t2, 2)
        out["import_ok"] = bool(res.get("ok"))
        out["import_stats"] = {k: res[k] for k in res if k != "ok"}
        t3 = time.perf_counter()
        sb.http_post(url, "/tick_gravity", b'{"on":true}',
                     ctype="application/json")
        out["t_gravity_arm_s"] = round(time.perf_counter() - t3, 3)
        out["triangles"] = rec["triangles"]
    finally:
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                       capture_output=True)
    (HERE / "import_timing.json").write_text(json.dumps(out, indent=1),
                                             encoding="utf-8")
    print(json.dumps(out, indent=1))
    return 0 if out["import_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
