"""measure_launch_realbody.py -- F-SLICE-LAUNCH, server timeline, real body
(lane slice_real_body_20260920; the 0921 instrument, pointed at this lane's
directory). The browser half (console transcript + first painted frame) is
measured with a real browser against this same server and recorded beside
this file (launch_browser_record_realbody.json).

PASS (server half) = t_first_verts < 10 s. The full falsifier adds the
browser console showing zero errors.
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


def sweep_own_engines() -> int:
    """Kill THIS repo's orphaned slice engines (never another worktree's):
    a hard-killed server orphans its engine child (measured this lane: three
    orphans made the next boot's /mesh_import die mid-parse), and a clean
    lane is the launch bar's own precondition. The sweep is a committed
    .ps1 run via -File."""
    exe = SLICE.parents[1] / ".tmp" / "slice_build" / "Release" / "chimera_engine.exe"
    r = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         str(HERE / "sweep_own_engines.ps1"), "-ExePath", str(exe)],
        capture_output=True, text=True)
    return r.returncode


def main() -> int:
    sys.path.insert(0, str(SLICE))
    import scene_boot as sb
    sweep_own_engines()
    port = sb.free_port()
    out = {"falsifier": "F-SLICE-LAUNCH", "port": port}
    t0 = time.perf_counter()
    log = open(HERE / "launch_server_log_realbody.txt", "w", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, str(SLICE / "slice_server.py"), "--port", str(port)],
        cwd=str(ROOT), stdout=log, stderr=subprocess.STDOUT, text=True)
    base = f"http://127.0.0.1:{port}"
    try:
        marks = {}
        while time.perf_counter() - t0 < 180:
            try:
                with urllib.request.urlopen(base + "/api/health", timeout=4) as r:
                    h = json.loads(r.read())
                if "t_server_up" not in marks:
                    marks["t_server_up"] = round(time.perf_counter() - t0, 2)
                if h.get("world_booted") and "t_world_up" not in marks:
                    marks["t_world_up"] = round(time.perf_counter() - t0, 2)
                    break
            except OSError:
                pass
            time.sleep(0.05)
        while time.perf_counter() - t0 < 180:
            try:
                with urllib.request.urlopen(base + "/api/verts", timeout=8) as r:
                    n = int.from_bytes(r.read(4), "little")
                marks["t_first_verts"] = round(time.perf_counter() - t0, 2)
                marks["first_verts_count"] = n
                break
            except (OSError, TimeoutError):
                time.sleep(0.05)
        while time.perf_counter() - t0 < 120:
            try:
                st = json.loads(urllib.request.urlopen(base + "/api/status",
                                                       timeout=5).read())
                if st.get("scene", {}).get("settled"):
                    marks["t_settled"] = round(time.perf_counter() - t0, 2)
                    break
            except (OSError, TimeoutError):
                time.sleep(0.2)
        try:
            page = urllib.request.urlopen(base + "/", timeout=15).read()
            marks["page_bytes"] = len(page)
        except OSError as e:
            marks["page_fetch_error"] = repr(e)
        out.update(marks)
        out["pass_server_side"] = marks.get("t_first_verts", 99) < 10.0
        out["law"] = ("first frame = the first /api/verts payload the WebGL2 "
                      "canvas renders; the browser console transcript is "
                      "recorded beside this file")
        out["server_url"] = base
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
    (HERE / "launch_server_timeline_realbody.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))
    return 0 if out["pass_server_side"] else 1


if __name__ == "__main__":
    sys.exit(main())
