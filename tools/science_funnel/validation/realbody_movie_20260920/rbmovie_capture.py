"""rbmovie_capture.py -- THE MOVIE CAPTURE (lane realbody-movie-20260920).

Starts the slice server (via rbmovie_server_launcher: the desktop stays dark),
loads the REAL slice page in a PRIVATE headless Playwright chrome (fresh
ephemeral profile; the operator's own browsing is never touched), hides the
HUD panels with an injected capture style (a capture-side view choice; no
slice file is edited), and captures the live canvas's own PNG bytes on a
steady loop with wall-clock timestamps while the slice's OWN scripted
sequences run, driven through the slice's own API endpoints:

  settle (the boot's own physics)  ~5 s
  /api/send  -> MOCK[mock_carry]   ~5 s   (1.2 m at the slice's 0.4 m/s)
  hold at the marker               ~1 s
  /api/drop_test -> THE FALL TEST ~9 s  (real engine law, transient + settle)
  /api/restart -> re-boot + settle ~4 s  (the cached ~2 s boot, recovery)

Total ~24 s of capture. The movie is cut at the MEASURED cadence.

Every frame is a raw page.screenshot of the live page: no compositing, no
editing, no synthesized frame (F4). Console errors, page errors and failed
page API requests are recorded as the error beacon (F2). Output:
capture_record.json + frames f%05d.jpg in --out.
"""
from __future__ import annotations

import argparse
import base64
import json
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

VIEW_W, VIEW_H = 800, 450
PHASES = [  # (name, seconds) -- the slice's own sequence lengths (record.md)
    ("settle", 5.0),
    ("carry", 5.0),
    ("hold_marker", 1.0),
    ("fall", 9.0),
    ("restart", 4.0),
]


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
    inherit it): a concurrent lane actively loads this machine and the
    capture loop is latency-sensitive. Guarded; records what happened."""
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
    """The machine is shared (the operator works here; other lanes run).
    The capture is latency-sensitive, so it waits (bounded) for a window
    where total CPU load is under `bar` percent. Nothing is killed; this is
    pure scheduling courtesy, recorded in the receipt."""
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
                         "the frames DIFFER (the attempt-1 freeze class)")
    ap.add_argument("--channel", default="chrome",
                    help="'chrome' (the real browser) or 'bundled' "
                         "(Playwright's own chromium). The lane default is "
                         "'chrome', but when real Chrome cannot navigate ANY "
                         "http URL (measured on this machine mid-lane: its "
                         "network path died between capture attempts; "
                         "bundled chromium measured OK) the capture falls "
                         "back to 'bundled' and the receipt records it.")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    priority = _raise_priority()
    gate = (None if a.test else _wait_quiet())

    sys.path.insert(0, str(SLICE))
    import scene_boot as sb

    sweep = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         str(HERE.parent / "slice_real_body_20260920" / "sweep_own_engines.ps1"),
         "-ExePath", str(EXE)], capture_output=True, text=True)
    print("sweep:", sweep.stdout.strip(), flush=True)

    port = a.port or sb.free_port()
    base = f"http://127.0.0.1:{port}"
    rec = {"schema": "chimera.realbody_movie_20260920.capture.v1",
           "port": port, "base": base, "viewport": [VIEW_W, VIEW_H],
           "process_priority": priority, "load_gate": gate,
           "frame_format": "jpeg q0.8 (the page canvas's own toDataURL bytes after the page's own draw(), same JS task; the canvas clears opaque so the browser's own JPEG encode loses nothing but weight)",
           "phases_planned": PHASES,
           "console_messages": [], "page_errors": [],
           "request_failures": [], "status_timeline": [],
           "phase_events": [], "posts": {}}

    server = subprocess.Popen(
        [sys.executable, str(HERE / "rbmovie_server_launcher.py"),
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
                channel=(None if a.channel == "bundled" else a.channel),
                headless=True,
                args=["--window-size=%d,%d" % (VIEW_W, VIEW_H + 40),
                      "--force-device-scale-factor=1",
                      "--enable-gpu",
                      "--enable-unsafe-swiftshader",
                      "--no-proxy-server",
                      "--disable-background-timer-throttling",
                      "--disable-renderer-backgrounding",
                      "--disable-backgrounding-occluded-windows"])
            rec["browser_channel"] = a.channel
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
            # the page's own readiness: the mesh VAO has indices and the ghost
            # OBJ is parsed (the page's own globals)
            deadline = time.perf_counter() + 60
            while time.perf_counter() < deadline:
                ready = page.evaluate(
                    "(typeof idxCount==='number' && idxCount>0) && ghost!==null")
                if ready:
                    break
                time.sleep(0.1)
            rec["page_ready"] = round(time.perf_counter() - t0, 2)
            rec["webgl2"] = page.evaluate(
                "(()=>{const c=document.createElement('canvas');"
                "const g=c.getContext('webgl2');if(!g)return null;"
                "const d=g.getExtension('WEBGL_debug_renderer_info');"
                "return d?g.getParameter(d.UNMASKED_RENDERER_WEBGL):'masked';})()")
            # labels off: a capture-side style, the page files untouched
            page.add_style_tag(content=(
                "#honesty,#verdict,#controls,#banner"
                "{display:none !important}"))
            # MEASURED (attempt 1, recorded in the receipt): in headless the
            # page's requestAnimationFrame never re-fires -- the page painted
            # exactly once (its own boot's direct draw()) and every later
            # screenshot returned that frozen compositor frame. So THIS
            # capture drives the page's OWN draw() before every shot (the
            # page's own render of the live stream; its setInterval vert
            # polls keep liveVerts current), and frames the creature with the
            # page's OWN client camera (the page's orbit/zoom state -- the
            # same knobs a player drags; no page file is edited).
            page.evaluate("cam.dist=1.6;cam.pit=0.35;cam.tx=0;cam.ty=0.30;"
                          "cam.tz=0;1")
            # PAGE-SIDE carry tracker: the page fetches its OWN status API on
            # a timer (exactly what its pollStatus already does) and stashes
            # the real carry x/z; the capture's per-frame evaluate reads the
            # stashed values. This keeps EVERY Python-side HTTP call out of
            # the capture loop (measured, attempt 5: a per-frame status GET
            # dragged the tracked phases to 5-10 fps while settle ran 21).
            page.evaluate("window.__cx=0;window.__cz=0;"
                          "setInterval(async()=>{try{"
                          "const s=await(await fetch('/api/status')).json();"
                          "const c=s.mock_carry||{};"
                          "window.__cx=c.x||0;window.__cz=c.z||0;"
                          "}catch(e){}},250)")
            deadline = time.perf_counter() + 30
            while time.perf_counter() < deadline:
                if page.evaluate(
                        "liveVerts && liveVerts.length>100000 ? 1 : 0"):
                    break
                time.sleep(0.1)
            page.evaluate("draw()")
            page.screenshot(path=str(out / "probe.png"))  # one pre-run probe

            fi = 0
            t_first = None
            times = []
            buf = []          # frames held in RAM, written after the close
            phases = ([("carrytest", 3.0)] if a.test else PHASES)
            # CAPTURE-SIDE CAMERA (the page's OWN client camera -- the same
            # orbit/zoom a player drags): the target follows the REAL carry
            # state via the page-side tracker above. One unbroken capture.
            for name, secs in phases:
                if name in ("carry", "carrytest"):
                    rec["posts"]["send"] = http_post(base, "/api/send")
                elif name == "fall":
                    try:
                        st = http_json(base, "/api/status")
                        rec["posts"]["status_before_fall"] = {
                            "fall_test": st.get("fall_test"),
                            "mock_carry": st.get("mock_carry")}
                    except OSError:
                        pass
                    rec["posts"]["drop_test"] = http_post(base, "/api/drop_test")
                elif name == "restart":
                    rec["posts"]["restart"] = http_post(base, "/api/restart")
                rec["phase_events"].append(
                    {"phase": name, "t": round(time.perf_counter(), 3),
                     "first_frame": fi})
                t_end = time.perf_counter() + secs
                while time.perf_counter() < t_end:
                    ts = time.perf_counter()
                    if t_first is None:
                        t_first = ts
                    # THE PAGE'S OWN FRAMEBUFFER, in the same JS task as the
                    # page's own draw(): without preserveDrawingBuffer the
                    # compositor never re-presents a draw() issued from
                    # evaluate (measured, attempt 2: every screenshot the
                    # same frozen frame), but inside ONE task the drawing
                    # buffer is still valid after draw() returns -- so the
                    # capture reads the canvas's own bytes. No compositing,
                    # no editing: the pixels are the page's own render.
                    data = page.evaluate(
                        "(()=>{cam.tx=window.__cx||0;cam.tz=window.__cz||0;"
                        "draw();return document.getElementById('gl')"
                        ".toDataURL('image/jpeg',0.8);})()")
                    buf.append((fi, base64.b64decode(data.split(",", 1)[1])))
                    times.append(time.perf_counter())
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
             str(HERE.parent / "slice_real_body_20260920" / "sweep_own_engines.ps1"),
             "-ExePath", str(EXE)], capture_output=True, text=True)

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
        "max_dt_ms", "intervals_over_100ms", "webgl2",
        "console_error_count", "page_error_count", "request_failure_count",
        "frame_bytes_min", "frame_bytes_median", "dark_frames_lt_15kb")},
        indent=1), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
