"""measure_launch.py -- F-SLICE-LAUNCH (server side of the instrument).

The preregistered bar: clean-machine launch to first frame < 10 s, no console
errors. This script owns the SERVER timeline: kill nothing but this lane's own
leftovers (a clean machine has none), start slice_server.py the way the R1
launcher does (a fresh process, free port), and measure:

  t_server_up   the first /api/health answer
  t_world_up    the engine booted + the standing start imported + gravity armed
  t_first_verts the first /api/verts payload served (what the page's WebGL2
                canvas renders as frame 1)
  t_settled     the standing start's settle landed (the attractor)

The browser half (console transcript, first painted frame) is measured with a
real browser against this same server; its transcript lands alongside
(launch_browser_record.json). PASS = t_first_verts < 10 s and the browser
console shows zero errors.
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


def main() -> int:
    sys.path.insert(0, str(SLICE))
    import scene_boot as sb
    port = sb.free_port()
    out = {"falsifier": "F-SLICE-LAUNCH", "port": port}
    t0 = time.perf_counter()
    # the R1 launcher redirects the server's output to FILES; the measurement
    # must too -- an undrained PIPE fills and blocks the server mid-run
    log = open(HERE / "launch_server_log.txt", "w", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, str(SLICE / "slice_server.py"), "--port", str(port)],
        cwd=str(ROOT), stdout=log, stderr=subprocess.STDOUT, text=True)
    base = f"http://127.0.0.1:{port}"
    try:
        marks = {}
        stall = 0
        while time.perf_counter() - t0 < 180:
            try:
                with urllib.request.urlopen(base + "/api/health", timeout=4) as r:
                    h = json.loads(r.read())
                if "t_server_up" not in marks:
                    marks["t_server_up"] = round(time.perf_counter() - t0, 2)
                if h.get("world_booted") and "t_world_up" not in marks:
                    marks["t_world_up"] = round(time.perf_counter() - t0, 2)
                    break
                stall = 0
            except OSError:
                stall += 1
            time.sleep(0.05)
        while time.perf_counter() - t0 < 180:
            try:
                with urllib.request.urlopen(base + "/api/verts", timeout=8) as r:
                    n = int.from_bytes(r.read(4), "little")
                marks["t_first_verts"] = round(time.perf_counter() - t0, 2)
                marks["first_verts_count"] = n
                break
            except (OSError, TimeoutError):
                stall += 1
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
        # the server shuts its own engine down on terminate
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
    (HERE / "launch_server_timeline.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))
    return 0 if out["pass_server_side"] else 1


if __name__ == "__main__":
    sys.exit(main())
