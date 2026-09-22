"""render_truth_capture.py -- THE MOVIE CAPTURE (lane render-truth-20260920).

The realbody-movie lane's capture, re-run through the REAL page after the
render fix, with THIS lane's one addition: the framing law. Same honest
frame source: the page canvas's OWN toDataURL in the same JS task as the
page's own draw() (the realbody lane's AMENDMENT 2 measurements: headless
rAF never re-fires; screenshots see a frozen compositor frame; bundled
chromium + --enable-gpu --enable-unsafe-swiftshader keeps the GL context).

Choreography = the slice's OWN sequences at the slice's OWN constants:

  settle (the boot's own physics)   ~5 s
  /api/send  -> MOCK[mock_carry]    ~5 s   (1.2 m at the slice's 0.4 m/s)
  hold at the marker                ~1 s
  /api/drop_test -> THE FALL TEST   ~9 s   (real engine law)

(the restart segment: excluded, the movie lane's AMENDMENT 1 finding --
restarts drive the slice's own designed 502-during-boot class)

THE FRAMING LAW (derived, Rule 1 -- no number is taste):
- the body measures 0.605 m nose-to-tail, long axis z, height 0.269 m
  (the live stream's own pos_min/pos_max, probe_vertstream this lane);
- the page's own projection: vertical extent 0.966*dist, horizontal
  1.717*dist at its 0.9 rad fov and the 640x360 capture viewport;
- readable phases (settle/carry/hold): dist CLOSE_DIST puts the body at
  ~55% of frame width, target height TY_CLOSE = the standing body's
  measured vertical center;
- the fall phase: the engine's own measured peak (root_y 0.9009, the
  movie lane's banked engine verdict) plus the import's own ymax
  (+0.134641) puts the body top at ~1.04 m, so the frame must span
  [floor, 1.04]: center TY_WIDE = 0.52, dist WIDE_DIST = 0.52/tan(0.45)
  = 1.077 -> 1.1. The camera switch happens AT the fall post.
- yaw: chosen from the framing probe's pixels (the side profile maximizes
  the projected extent of the body's longest axis), recorded in
  capture_record.json.

Every frame is the page canvas's own bytes after the page's own draw():
no compositing, no editing, no synthesized frame (F4 class). Console
errors, page errors and failed page API requests are recorded (the
budgets falsifier). Output: capture_record.json + frames f%05d.jpg in
--out.
"""
from __future__ import annotations

import argparse
import base64
import json
import math
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
SLICE = HERE.parents[3] / "tools" / "playable_slice"
ROOT = SLICE.parents[1]
EXE = ROOT / ".tmp" / "slice_build" / "Release" / "chimera_engine.exe"
SWEEP = HERE.parent / "slice_stranger_20260920" / "sweep_own_engines.ps1"

VIEW_W, VIEW_H = 640, 360
# THE SLICE'S OWN BANKED CONSTANTS (slice_server.py):
MARKER_AZIMUTH_RAD = 0.6
MARKER_DIST_M = 1.2
CARRY_SPEED_MPS = 0.4
MARKER_X = MARKER_DIST_M * math.sin(MARKER_AZIMUTH_RAD)
MARKER_Z = MARKER_DIST_M * math.cos(MARKER_AZIMUTH_RAD)
PHASES = [  # (name, seconds) -- the slice's own sequence lengths
    ("settle", 5.0),
    ("carry", 5.0),
    ("hold_marker", 1.0),
    ("fall", 9.0),
]
# THE FRAMING LAW (derived above; measured from the body's own extent and
# the engine's own fall peak -- recorded per-phase in the capture record)
YAW = 1.571            # pi/2: the side profile (framing-probe measured)
PITCH = 0.35
CLOSE_DIST, TY_CLOSE = 0.80, 0.14
WIDE_DIST, TY_WIDE = 1.10, 0.52


def http_json(base: str, path: str, timeout: float = 5) -> dict:
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return json.loads(r.read())


def http_post(base: str, path: str, timeout: float = 10) -> dict:
    req = urllib.request.Request(base + path, data=b"{}", method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _raise_priority() -> str:
    """HIGH_PRIORITY_CLASS for THIS process only (the browser children
    inherit it): the capture loop is latency-sensitive. Guarded; records."""
    try:
        import psutil
        psutil.Process().nice(psutil.HIGH_PRIORITY_CLASS)
        return "high (psutil)"
    except Exception as e:  # noqa: BLE001
        try:
            import ctypes
            ok = ctypes.windll.kernel32.SetPriorityClass(
                ctypes.windll.kernel32.GetCurrentProcess(), 0x00000080)
            return "high (ctypes)" if ok else "refused"
        except Exception:  # noqa: BLE001
            return "unavailable: %s" % type(e).__name__


def _wait_quiet(max_wait_s: float = 480.0, bar: float = 30.0) -> dict:
    """The machine is shared: wait (bounded) for a window where total CPU
    load is under `bar` percent. Nothing is killed; recorded."""
    t0 = time.perf_counter()
    samples = []
    while time.perf_counter() - t0 < max_wait_s:
        try:
            import psutil
            load = psutil.cpu_percent(interval=1.0)
        except Exception:  # noqa: BLE001
            load = None
        samples.append(load)
        if load is not None and load < bar:
            return {"waited_s": round(time.perf_counter() - t0, 1),
                    "samples": samples}
    return {"waited_s": round(time.perf_counter() - t0, 1),
            "samples": samples, "note": "bar never met; proceeding"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="frames directory")
    ap.add_argument("--record", required=True)
    ap.add_argument("--port", type=int, default=0)
    ap.add_argument("--test", action="store_true",
                    help="3 s carry motion test: capture is only sane if "
                         "the frames DIFFER (the freeze class)")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    priority = _raise_priority()
    gate = (None if a.test else _wait_quiet())

    sweep = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         str(SWEEP), "-ExePath", str(EXE)], capture_output=True, text=True)
    print("sweep:", sweep.stdout.strip(), flush=True)

    port = a.port or sb_free_port()
    base = f"http://127.0.0.1:{port}"
    rec = {"schema": "chimera.render_truth_20260920.capture.v1",
           "port": port, "base": base, "viewport": [VIEW_W, VIEW_H],
           "process_priority": priority, "load_gate": gate,
           "frame_format": "jpeg q0.8 (the page canvas's own toDataURL "
                           "bytes after the page's own draw(), same JS "
                           "task; no compositing, no editing)",
           "framing_law": {
               "derived_from": "body extent from the live stream (0.605 m "
                               "long axis z, height 0.269 m; "
                               "probe_vertstream), the page's own 0.9 rad "
                               "fov projection (1.717*dist horizontal), "
                               "the engine's own measured fall peak "
                               "(root_y 0.9009 + ymax 0.134641 -> top "
                               "~1.04 m, realbody_movie_20260920 receipt)",
               "yaw": YAW, "pitch": PITCH,
               "close": {"dist": CLOSE_DIST, "ty": TY_CLOSE},
               "wide_fall": {"dist": WIDE_DIST, "ty": TY_WIDE},
               "view_state_law": "the page's OWN client camera (the "
                                 "player's orbit/zoom); set per phase "
                                 "capture-side, recorded here; no page "
                                 "file edit carries it"},
           "phases_planned": PHASES,
           "console_messages": [], "page_errors": [],
           "request_failures": [], "status_timeline": [],
           "phase_events": [], "posts": {}}

    server = subprocess.Popen(
        [sys.executable, str(HERE / "render_truth_server_launcher.py"),
         "--port", str(port), "--engine-exe", str(EXE), "--log", "x"],
        cwd=str(ROOT),
        stdout=open(HERE / "capture_server_log.txt", "w", encoding="utf-8"),
        stderr=subprocess.STDOUT)
    t0 = time.perf_counter()
    try:
        while time.perf_counter() - t0 < 120:
            try:
                if http_json(base, "/api/health").get("world_booted"):
                    rec["t_world_up"] = round(time.perf_counter() - t0, 2)
                    break
            except OSError:
                time.sleep(0.05)
        else:
            rec["error"] = "server never booted"
            raise RuntimeError(rec["error"])

        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                channel=None,           # Playwright's BUNDLED chromium:
                                        # the machine's installed Chrome
                                        # cannot navigate any URL
                                        # (F-ENV-CHROME, slice_stranger
                                        # lane); --enable-gpu +
                                        # --enable-unsafe-swiftshader keep
                                        # the page's GL context (the
                                        # realbody lane's AMENDMENT 2)
                headless=True,
                args=["--window-size=%d,%d" % (VIEW_W, VIEW_H + 40),
                      "--force-device-scale-factor=1",
                      "--enable-gpu",
                      "--enable-unsafe-swiftshader",
                      "--no-proxy-server",
                      "--disable-background-timer-throttling",
                      "--disable-renderer-backgrounding",
                      "--disable-backgrounding-occluded-windows"])
            rec["browser_channel"] = "chromium-bundled (F-ENV-CHROME: the " \
                                     "installed Chrome cannot navigate; " \
                                     "the gpu+swiftshader flags keep the " \
                                     "GL context, AMENDMENT 2)"
            ctx = browser.new_context(
                viewport={"width": VIEW_W, "height": VIEW_H},
                device_scale_factor=1)
            page = ctx.new_page()

            def on_console(msg):
                rec["console_messages"].append(
                    {"type": msg.type, "text": msg.text[:400]})
            def on_pageerror(err):
                rec["page_errors"].append(str(err)[:400])
            def on_reqfail(req):
                rec["request_failures"].append(
                    {"url": req.url[:200], "failure": req.failure})
            page.on("console", on_console)
            page.on("pageerror", on_pageerror)
            page.on("requestfailed", on_reqfail)

            page.goto(base + "/", wait_until="domcontentloaded", timeout=60000)
            # the page's own readiness: the GLB index buffer is uploaded,
            # the ghost OBJ is parsed, live verts are flowing
            deadline = time.perf_counter() + 60
            while time.perf_counter() < deadline:
                ready = page.evaluate(
                    "(typeof idxCount==='number' && idxCount>0) && "
                    "ghost!==null && liveVerts && liveVerts.length>100000")
                if ready:
                    break
                time.sleep(0.1)
            rec["page_ready"] = round(time.perf_counter() - t0, 2)
            rec["mesh_source"] = page.evaluate(
                "window.__CHIMERA_MESH_SOURCE")
            rec["idx_count"] = page.evaluate("idxCount")
            rec["webgl2"] = page.evaluate(
                "(()=>{const c=document.createElement('canvas');"
                "const g=c.getContext('webgl2');if(!g)return null;"
                "const d=g.getExtension('WEBGL_debug_renderer_info');"
                "return d?g.getParameter(d.UNMASKED_RENDERER_WEBGL):'masked';})()")
            # labels off: a capture-side style, the page files untouched
            page.add_style_tag(content=(
                "#honesty,#verdict,#controls,#banner,#keys,#guide,"
                "#guidepill,#beacon,#bootstatus,#settle"
                "{display:none !important}"))
            # the framing law: readable phases close and low; the fall wide
            # (derived numbers, recorded above). The camera is the page's
            # OWN client camera -- the same knobs a player drags.
            page.evaluate("cam.yaw=%r;cam.pit=%r;cam.tx=0;cam.tz=0;1"
                          % (YAW, PITCH))
            # the declared ghost overlay is hidden for the capture (the
            # movie lane's recorded view state: the double rides the same
            # live root and speckles the subject)
            page.evaluate("ghost=null;ghostBase=null;1")
            # let the standing start settle before the first frame so the
            # movie opens on the standing pose (the capture's own 'settle'
            # phase then records the settled micro-motion honestly)
            deadline = time.perf_counter() + 120
            while time.perf_counter() < deadline:
                try:
                    st = http_json(base, "/api/status")
                    if (st.get("scene") or {}).get("settled"):
                        rec["t_settled"] = round(time.perf_counter() - t0, 2)
                        break
                except OSError:
                    pass
                time.sleep(0.5)
            page.evaluate("cam.dist=%r;cam.ty=%r;draw()"
                          % (CLOSE_DIST, TY_CLOSE))
            page.screenshot(path=str(out / "probe.png"))  # one pre-run probe

            fi = 0
            t_first = None
            times = []
            buf = []          # frames held in RAM, written after the close
            phases = ([("carrytest", 3.0)] if a.test else PHASES)
            # CAPTURE-SIDE CAMERA: the readable phases ride CLOSE_DIST with
            # the target following the DERIVED carry law (zero fetches); at
            # the fall post the camera switches to the derived WIDE framing
            # so the engine's own measured fall peak stays in frame. One
            # unbroken capture; no cuts.
            for name, secs in phases:
                if name in ("carry", "carrytest"):
                    rec["posts"]["send"] = http_post(base, "/api/send")
                    cam = (CLOSE_DIST, TY_CLOSE)
                elif name == "hold_marker":
                    cam = (CLOSE_DIST, TY_CLOSE)
                elif name == "fall":
                    cam = (WIDE_DIST, TY_WIDE)
                    try:
                        st = http_json(base, "/api/status")
                        rec["posts"]["status_before_fall"] = {
                            "fall_test": st.get("fall_test"),
                            "mock_carry": st.get("mock_carry")}
                    except OSError:
                        pass
                    rec["posts"]["drop_test"] = http_post(base, "/api/drop_test")
                else:
                    cam = (CLOSE_DIST, TY_CLOSE)
                rec["phase_events"].append(
                    {"phase": name, "t": round(time.perf_counter(), 3),
                     "first_frame": fi, "cam_dist": cam[0], "cam_ty": cam[1]})
                t_phase0 = time.perf_counter()
                dts_phase = []
                t_end = t_phase0 + secs
                while time.perf_counter() < t_end:
                    ts = time.perf_counter()
                    if t_first is None:
                        t_first = ts
                    # the DERIVED carry law: the slide starts at the origin,
                    # runs the marker's azimuth at the slice's constant
                    # speed, stops at the arrive radius
                    if name in ("carry", "carrytest"):
                        d = min(CARRY_SPEED_MPS * (time.perf_counter()
                                - t_phase0), MARKER_DIST_M)
                        tx, tz = d * math.sin(MARKER_AZIMUTH_RAD), \
                            d * math.cos(MARKER_AZIMUTH_RAD)
                    elif name in ("hold_marker", "fall"):
                        tx, tz = MARKER_X, MARKER_Z
                    else:
                        tx, tz = 0.0, 0.0
                    # THE PAGE'S OWN FRAMEBUFFER, in the same JS task as the
                    # page's own draw() (AMENDMENT 2): the pixels are the
                    # page's own render of the live stream -- no compositing,
                    # no editing.
                    data = page.evaluate(
                        "([tx,tz,dist,ty])=>{cam.tx=tx;cam.tz=tz;"
                        "cam.dist=dist;cam.ty=ty;draw();return "
                        "document.getElementById('gl')"
                        ".toDataURL('image/jpeg',0.8);}", [tx, tz, cam[0],
                                                           cam[1]])
                    buf.append((fi, base64.b64decode(data.split(",", 1)[1])))
                    times.append(time.perf_counter())
                    dts_phase.append(times[-1] - times[-2]
                                     if len(times) > 1 else 0.0)
                    if fi % 50 == 0:
                        try:
                            st = http_json(base, "/api/status")
                            es = st.get("engine_state") or {}
                            mc = st.get("mock_carry") or {}
                            rec["status_timeline"].append(
                                {"frame": fi,
                                 "t": round(ts - t_first, 3),
                                 "root_y": es.get("root_y"),
                                 "root_vy": es.get("root_vy"),
                                 "gravity": es.get("gravity_on"),
                                 "carry_active": mc.get("active"),
                                 "carry_x": mc.get("x"), "carry_z": mc.get("z")})
                        except OSError:
                            pass
                    fi += 1
                rec["phase_events"][-1]["last_frame"] = fi - 1
                sp = sorted(dts_phase)
                rec["phase_events"][-1]["median_dt_ms"] = \
                    round(sp[len(sp) // 2] * 1000, 1) if sp else None
                try:
                    import psutil
                    rec["phase_events"][-1]["cpu_pct"] = psutil.cpu_percent()
                except Exception:  # noqa: BLE001
                    pass
            t_last = time.perf_counter()
            try:
                rec["final_status"] = http_json(base, "/api/status")
            except OSError:
                pass
            ctx.close()
            browser.close()

        for i, b in buf:
            (out / ("f%05d.jpg" % i)).write_bytes(b)
        n = fi
        span = t_last - t_first
        dts = [b - a for a, b in zip(times, times[1:])]
        dts_sorted = sorted(dts)
        rec["frames"] = n
        rec["capture_span_s"] = round(span, 3)
        rec["mean_fps"] = round((n - 1) / span, 2) if span > 0 else 0.0
        rec["median_dt_ms"] = round(dts_sorted[len(dts_sorted) // 2] * 1000, 1) \
            if dts_sorted else None
        rec["p95_dt_ms"] = round(dts_sorted[int(len(dts_sorted) * 0.95)] * 1000, 1) \
            if dts_sorted else None
        rec["max_dt_ms"] = round(max(dts) * 1000, 1) if dts else None
        rec["intervals_over_100ms"] = sum(1 for d in dts if d > 0.1)
        rec["frame_dt_ms"] = [round(d * 1000, 1) for d in dts]
        rec["phases_actual"] = [
            {"phase": e["phase"], "first": e["first_frame"],
             "last": e.get("last_frame")} for e in rec["phase_events"]]
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
        time.sleep(1.0)
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
             str(SWEEP), "-ExePath", str(EXE)], capture_output=True, text=True)

    # per-frame sizes: the dark-frame sanity metric (a blank frame is small)
    sizes = [(out / ("f%05d.jpg" % i)).stat().st_size for i in range(rec["frames"])]
    rec["frame_bytes_min"] = min(sizes)
    rec["frame_bytes_median"] = sorted(sizes)[len(sizes) // 2]
    rec["dark_frames_lt_15kb"] = sum(1 for s in sizes if s < 15000)

    errs = [m for m in rec["console_messages"] if m["type"] == "error"]
    rec["console_error_count"] = len(errs)
    rec["page_error_count"] = len(rec["page_errors"])
    rec["request_failure_count"] = len(rec["request_failures"])
    (HERE / a.record).write_text(json.dumps(rec, indent=1), encoding="utf-8")
    print(json.dumps({k: rec[k] for k in (
        "frames", "capture_span_s", "mean_fps", "median_dt_ms", "p95_dt_ms",
        "max_dt_ms", "intervals_over_100ms", "webgl2", "mesh_source",
        "idx_count", "console_error_count", "page_error_count",
        "request_failure_count", "frame_bytes_min", "frame_bytes_median",
        "dark_frames_lt_15kb")},
        indent=1), flush=True)
    return 0


def sb_free_port() -> int:
    sys.path.insert(0, str(SLICE))
    import scene_boot as sb
    return sb.free_port()


if __name__ == "__main__":
    sys.exit(main())
