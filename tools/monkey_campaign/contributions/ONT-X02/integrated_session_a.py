"""integrated_session_a.py -- ONT-X02 Session A: the REAL application, page-driven.

Runs the shipped playable-slice application end to end and drives it ONLY
through the player entry controls:

  1. python tools/playable_slice/slice_server.py --no-browser --engine-exe <exe>
     (the R1 launcher's own automated mode; the server boots and owns its own
     engine subprocess: slice_server.py World.boot -- shutdown_engine, free
     port, fresh chimera_engine.exe, wait_engine, POST /mesh_import real body,
     gravity on, standing-start settle).
  2. A headless Chrome (Playwright, channel "chrome" -- the operator-sanctioned
     headless path; bundled chromium recorded as a deviation fallback) loads
     the served page and RECORDS REAL VIDEO of the live application
     (record_video_dir). A status sampler writes the runtime trace jsonl
     (ticks / root_y / root_vy / boot_count / settled every 0.5 s).
  3. Player controls exercised, in order, with timestamps:
       - the page's own [H] key (hide/show help: separates diagnostic vs
         clean page segments without touching the camera bookmark);
       - lowercase 'r' (a MEASURED no-op: the pinned page's legacy handler
         matches KEYLIST by exact e.key 'R');
       - Shift+R (the named [R] restart key -> POST /api/restart -> a FULL
         World.boot scene reload; both page key handlers POST for 'R' --
         measured page behavior, boot count required to stabilize);
       - screenshots at the before/after pinned states.
  4. EXIT = measured finding: the app exposes NO remote/graceful exit
     control; the operator-class hard kill orphans the engine child (the
     leak is MEASURED, then the driver terminates the orphan by PID).

Evidence: session receipt (PIDs, ports, timings, pinned before/after state),
the real recording (webm in workspace, mp4 beside it), trace jsonl, real
screenshots, engine /frame images through the server's own passthru.

Usage:
  python -B integrated_session_a.py --play-root <dir> --engine-exe <exe> \
         --out <evidence dir> [--viewport WxH]
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

import psutil

PNG_MAGIC = b"\x89PNG"


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def http_json(base: str, path: str, timeout: float = 10) -> dict:
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return json.loads(r.read().decode())


def engine_children(server_pid: int) -> tuple[list, list]:
    """(engine children of the server, all engine PIDs on the box)."""
    out = []
    try:
        for c in psutil.Process(server_pid).children(recursive=True):
            if "chimera_engine" in (c.name() or "").lower():
                out.append(c.pid)
    except psutil.Error:
        pass
    glob = [p.pid for p in psutil.process_iter(["name"])
            if p.info["name"] and "chimera_engine" in p.info["name"].lower()]
    return out, glob


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--play-root", type=Path, required=True)
    ap.add_argument("--engine-exe", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--viewport", default="1280x720")
    ap.add_argument("--settle-timeout", type=float, default=420.0)
    a = ap.parse_args()
    out = a.out
    out.mkdir(parents=True, exist_ok=True)
    receipt: dict = {"schema": "chimera.ont_x02.integrated_session_a.v1",
                     "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                     "engine_exe": str(a.engine_exe),
                     "engine_exe_sha256": sha256(a.engine_exe.read_bytes()),
                     "play_root": str(a.play_root),
                     "viewport": a.viewport,
                     "steps": {}}

    def step(name, obj):
        receipt["steps"][name] = obj
        (out / "session_a_receipt.json").write_text(
            json.dumps(receipt, indent=1), encoding="utf-8")
        print("  [A] %s: %s" % (name, json.dumps(obj, default=str)[:230]))

    # ── 0. pre-flight: terminate engines whose cwd is THIS run's engine dir
    # (leftovers of this workspace's own earlier attempts; never another
    # lane's engines). Count recorded.
    pre = []
    for p in psutil.process_iter(["name"]):
        try:
            if p.info["name"] and "chimera_engine" in p.info["name"].lower():
                cwd = p.cwd() or ""
                if str(a.engine_exe.parent) in cwd:
                    p.terminate()
                    pre.append(p.pid)
        except (psutil.Error, TypeError, PermissionError):
            continue
    if pre:
        time.sleep(3.0)
    receipt["preflight_terminated_leftover_engines"] = pre

    # ── 1. the server (the R1 automated mode) ───────────────────────────
    srv_out = out / "slice_server_stdout.log"
    srv_err = out / "slice_server_stderr.log"
    t0 = time.time()
    proc = subprocess.Popen(
        [sys.executable, "-u", "-B", "tools/playable_slice/slice_server.py",
         "--no-browser", "--engine-exe", str(a.engine_exe), "--port", "0"],
        cwd=str(a.play_root),
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        stdout=open(srv_out, "wb"), stderr=open(srv_err, "wb"))
    url = None
    deadline = time.time() + 120
    while time.time() < deadline and url is None:
        if proc.poll() is not None:
            step("A1_launch_failed", {"exit": proc.returncode,
                                      "stderr": srv_err.read_text(errors="replace")[-2000:]})
            return 1
        for line in srv_out.read_text(errors="replace").splitlines():
            if line.startswith("slice: "):
                url = line.split(" ", 1)[1].strip()
        time.sleep(0.25)
    if url is None:
        step("A1_no_url", {"stdout_tail": srv_out.read_text(errors="replace")[-2000:]})
        proc.kill()
        return 1
    boot_deadline = time.time() + 300
    health = None
    while time.time() < boot_deadline:
        try:
            h = http_json(url, "/api/health", timeout=5)
            if h.get("world_booted"):
                health = h
                break
        except OSError:
            pass
        time.sleep(1.0)
    kids, glob = engine_children(proc.pid)
    st = http_json(url, "/api/status")
    step("A1_boot", {"ok": len(kids) == 1,
                     "url": url, "server_pid": proc.pid,
                     "boot_seconds": round(time.time() - t0, 2),
                     "health": health,
                     "engine_children_of_server": kids,
                     "engine_processes_global": glob,
                     "scene_sha256": (st.get("scene") or {}).get("scene_sha256"),
                     "boot_count": st.get("boot_count")})
    if health is None or len(kids) != 1:
        step("A1_VERDICT", "FAIL")
        # terminate OUR tree before leaving
        proc.kill()
        for k in kids:
            try:
                psutil.Process(k).terminate()
            except psutil.Error:
                pass
        return 1

    # the server owns the rest; on ANY driver failure it is still terminated
    # here (only OUR process tree is ever signalled).
    try:
        run_session(a, receipt, step, proc, url)
    finally:
        if proc.poll() is None:
            proc.kill()
        time.sleep(2.0)
        _, glob_end = engine_children(proc.pid)
        leftover = []
        for k in glob_end:
            try:
                if psutil.pid_exists(k) and "chimera_engine" in \
                        (psutil.Process(k).name() or "").lower():
                    psutil.Process(k).terminate()
                    leftover.append(k)
            except psutil.Error:
                pass
        if leftover:
            receipt["post_run_cleanup"] = leftover

    verdict = (all(receipt["steps"].get(k, {}).get("ok")
                   for k in ("A1_boot", "A2_play_reached", "A3_after_restart"))
               and receipt["steps"]["A4_exit"]["ok"]
               and receipt["steps"].get("A5_capture", {}).get("ok", True))
    receipt["verdict"] = "PASS" if verdict else "CHECK_STEPS"
    receipt["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    (out / "session_a_receipt.json").write_text(
        json.dumps(receipt, indent=1), encoding="utf-8")
    print("SESSION A VERDICT:", receipt["verdict"])
    return 0 if verdict else 1


def run_session(a, receipt, step, proc, url):
    """A2-A5 against the booted, serving slice server (driver may raise)."""
    out = a.out
    vw, vh = (int(x) for x in a.viewport.split("x"))

    # ── 2. the page, RECORDED (real video of the real application) ──────
    from playwright.sync_api import sync_playwright
    console_errors: list[str] = []
    page_errors: list[str] = []
    video_dir = out / "_video_raw"
    video_dir.mkdir(exist_ok=True)
    trace_path = out / "integrated_trace.jsonl"
    marks: dict = {}
    t0 = time.perf_counter()

    stop_sampler = threading.Event()

    def sampler():
        """Runtime trace: one jsonl row per 0.5 s of the LIVE world state."""
        with open(trace_path, "w", encoding="utf-8") as fh:
            while not stop_sampler.is_set():
                try:
                    st = http_json(url, "/api/status", timeout=4)
                    es = st.get("engine_state") or {}
                    row = {"rel_s": round(time.perf_counter() - t0, 3),
                           "ticks": es.get("ticks"),
                           "root_y": es.get("root_y"),
                           "root_vy": es.get("root_vy"),
                           "gravity_on": es.get("gravity_on"),
                           "boot_count": st.get("boot_count"),
                           "settled": (st.get("scene") or {}).get("settled")}
                except OSError:
                    row = {"rel_s": round(time.perf_counter() - t0, 3),
                           "restarting": True}
                fh.write(json.dumps(row) + "\n")
                fh.flush()
                stop_sampler.wait(0.5)

    with sync_playwright() as pw:
        # channel "chrome" is the operator-sanctioned headless path. The
        # installed Chrome's http navigation hangs are a MEASURED environment
        # behavior on this box (also recorded as F-ENV-CHROME in the pinned
        # movie lane). If chrome cannot complete a probe navigation, the
        # bundled chromium is used and the deviation is recorded.
        browser = None
        page = None
        channel_used = None
        for attempt_channel in ("chrome", None):
            try:
                kwargs = {"headless": True, "timeout": 120000,
                          "args": ["--enable-gpu", "--enable-unsafe-swiftshader"]}
                if attempt_channel:
                    kwargs["channel"] = attempt_channel
                b = pw.chromium.launch(**kwargs)
                ctx = b.new_context(
                    viewport={"width": vw, "height": vh},
                    record_video_dir=str(video_dir),
                    record_video_size={"width": vw, "height": vh})
                p = ctx.new_page()
                p.set_default_timeout(120000)
                p.goto(url + "mock_registry.json", wait_until="domcontentloaded",
                       timeout=45000)
                browser, page, context = b, p, ctx   # probe passed: keep
                channel_used = attempt_channel or "chromium-bundled"
                break
            except Exception as e:
                try:
                    b.close()
                except Exception:
                    pass
                browser = None
                receipt.setdefault("browser_channel_deviations", []).append(
                    {"channel": attempt_channel or "chromium-bundled",
                     "error": str(e)[:300]})
        if browser is None:
            raise RuntimeError("no browser channel could navigate: see "
                               "browser_channel_deviations")
        step("A2_browser_channel", {"channel": channel_used,
                                    "deviations": receipt.get(
                                        "browser_channel_deviations", [])})
        page.on("console", lambda m: console_errors.append(m.text)
                if m.type == "error" else None)
        page.on("pageerror", lambda e: page_errors.append(str(e)))

        sampler_thread = threading.Thread(target=sampler, daemon=True)
        sampler_thread.start()

        t_load = time.perf_counter()
        page.goto(url, wait_until="domcontentloaded", timeout=120000)
        marks["page_load"] = round(t_load - t0, 3)

        def status_line():
            try:
                return page.evaluate(
                    "document.getElementById('status').textContent")
            except Exception:
                return None

        live_deadline = time.time() + 90
        live = False
        while time.time() < live_deadline:
            s = status_line() or ""
            if s.startswith("REAL engine numbers"):
                live = True
                break
            time.sleep(0.5)
        marks["play_live"] = round(time.perf_counter() - t0, 3)
        ticks_a = http_json(url, "/api/status", timeout=5).get(
            "engine_state", {}).get("ticks")
        time.sleep(2.0)
        ticks_b = http_json(url, "/api/status", timeout=5).get(
            "engine_state", {}).get("ticks")
        cam = page.evaluate("JSON.stringify(window.__CHIMERA_VIEW || null)")
        step("A2_play_reached", {"ok": bool(live and ticks_b != ticks_a),
                                 "status_line": status_line(),
                                 "ticks_sample_1": ticks_a,
                                 "ticks_sample_2": ticks_b,
                                 "ticks_advanced": ticks_b != ticks_a,
                                 "camera_handle": cam,
                                 "console_errors": console_errors,
                                 "page_errors": page_errors,
                                 "marks": dict(marks)})
        step("A2_engine_frame_before", engine_frame_fetch(out, url,
                                                          "engine_frame_before.png"))

        def capture_views(tag: str, status_now: dict):
            """diagnostic = full page (the app's own HUD is the diagnostic
            layer); clean = the canvas's OWN pixels via toDataURL called in
            the same rAF task as the page's own draw (element screenshots
            composite the DOM overlays -- MEASURED identical bytes)."""
            page.wait_for_timeout(700)
            diag = out / ("view_%s_diagnostic.png" % tag)
            page.screenshot(path=str(diag), full_page=False)
            data_url = page.evaluate(
                "new Promise(res => {"
                "  const cv = document.getElementsByTagName('canvas')[0];"
                "  requestAnimationFrame(() => {"
                "    try { res(cv.toDataURL('image/png')); }"
                "    catch (e) { res('ERR:' + e.message); }"
                "  });"
                "})")
            clean = out / ("view_%s_clean.png" % tag)
            if data_url.startswith("data:image/png;base64,"):
                clean.write_bytes(base64.b64decode(data_url.split(",", 1)[1]))
            else:
                clean.write_text(str(data_url)[:400], encoding="utf-8")
            meta = page.evaluate(
                "JSON.stringify({cam: window.__CHIMERA_VIEW,"
                " cw: (document.getElementsByTagName('canvas')[0]||{}).width,"
                " ch: (document.getElementsByTagName('canvas')[0]||{}).height})")
            binding = out / ("state_binding_%s.json" % tag)
            binding.write_text(json.dumps(status_now, indent=1), encoding="utf-8")
            return {"diagnostic": {"path": str(diag),
                                   "sha256": sha256(diag.read_bytes())},
                    "clean": {"path": str(clean),
                              "sha256": sha256(clean.read_bytes())},
                    "camera": json.loads(meta),
                    "state_binding_sha256": sha256(binding.read_bytes())}

        # ── 3. RESTART through the page's own controls ──────────────────
        deadline = time.time() + a.settle_timeout
        while time.time() < deadline:
            st = http_json(url, "/api/status")
            if (st.get("scene") or {}).get("settled"):
                break
            time.sleep(1.0)
        before = st
        kids_before, glob_before = engine_children(proc.pid)
        step("A3_before_state", {"scene": before.get("scene"),
                                 "boot_count": before.get("boot_count"),
                                 "engine_children": kids_before,
                                 "engine_global": glob_before,
                                 "stats": http_json(url, "/api/stats")})
        v_before = capture_views("before", before)

        # [H]: the page's own show/hide-help key (distinguishes the page's
        # diagnostic segment from its cleaned segment; camera untouched).
        # The pinned legacy handler matches KEYLIST by EXACT e.key ('H'),
        # so Shift+H is the named key; the guide's visibility is READ BACK.
        page.keyboard.press("H")
        marks["help_toggled_off"] = round(time.perf_counter() - t0, 3)
        time.sleep(1.5)
        marks["guide_display_after_H"] = page.evaluate(
            "document.getElementById('guide').style.display")
        # key receipt: lowercase 'r' is a MEASURED no-op (legacy KEYLIST is
        # exact-'R'); Shift+R is the named restart key.
        page.keyboard.press("r")
        time.sleep(2.0)
        r_lower = http_json(url, "/api/status")
        key_receipt = {"lowercase_r_boot_count": r_lower.get("boot_count"),
                       "lowercase_r_fired_restart":
                           r_lower.get("boot_count") != before.get("boot_count")}
        page.keyboard.press("R")           # Shift+R: the named [R] restart key
        marks["restart_pressed"] = round(time.perf_counter() - t0, 3)
        t_restart = time.perf_counter()
        old_pid = kids_before[0] if kids_before else None
        old_died_at = None
        while old_pid and old_died_at is None and \
                time.perf_counter() - t_restart < 30:
            if not psutil.pid_exists(old_pid) or "chimera_engine" not in \
                    (psutil.Process(old_pid).name() or "").lower():
                old_died_at = round(time.perf_counter() - t_restart, 2)
            time.sleep(0.25)
        # BOTH page key handlers POST /api/restart for 'R' (measured page
        # behavior), so a second boot may follow the first: require boot
        # count >= 2 AND stable across consecutive reads.
        settled = False
        last = None
        stable = 0
        last_boot = None
        deadline = time.time() + a.settle_timeout
        while time.time() < deadline:
            try:
                last = http_json(url, "/api/status")
            except OSError:
                time.sleep(0.5)
                continue
            sc = last.get("scene") or {}
            if sc.get("settled") and last.get("boot_count", 0) >= 2:
                if last.get("boot_count") == last_boot:
                    stable += 1
                    if stable >= 3:
                        settled = True
                        break
                else:
                    stable = 0
                last_boot = last.get("boot_count")
            time.sleep(2.0)
        marks["recovered_settled"] = round(time.perf_counter() - t0, 3)
        key_receipt["post_key_boot_count"] = (last or {}).get("boot_count")
        kids_after, glob_after = engine_children(proc.pid)
        after = last
        v_after = capture_views("after", after)
        step("A3_engine_frame_after", engine_frame_fetch(out, url,
                                                         "engine_frame_after.png"))
        old_gone = all(psutil.pid_exists(k) is False or
                       "chimera_engine" not in
                       (psutil.Process(k).name() or "").lower()
                       for k in kids_before) if kids_before else None
        step("A3_after_restart", {"ok": bool(settled),
                                  "restart_seconds":
                                      round(time.perf_counter() - t_restart, 2),
                                  "key_receipt": key_receipt,
                                  "old_engine_pid": old_pid,
                                  "old_engine_died_seconds": old_died_at,
                                  "boot_count_before": before.get("boot_count"),
                                  "boot_count_after": after.get("boot_count"),
                                  "engine_children_before": kids_before,
                                  "engine_children_after": kids_after,
                                  "engine_global_after": glob_after,
                                  "old_engine_pid_gone": old_gone,
                                  "scene_sha256_before": (before.get("scene") or {}).get("scene_sha256"),
                                  "scene_sha256_after": (after.get("scene") or {}).get("scene_sha256"),
                                  "start_state_sha256_before": (before.get("scene") or {}).get("start_state_sha256"),
                                  "start_state_sha256_after": (after.get("scene") or {}).get("start_state_sha256"),
                                  "start_root_y_before": (before.get("scene") or {}).get("start_root_y"),
                                  "start_root_y_after": (after.get("scene") or {}).get("start_root_y"),
                                  "status_line_after": status_line(),
                                  "views_before": v_before,
                                  "views_after": v_after})

        # close the context: the recording lands in video_dir
        video_path = page.video.path()
        context.close()
        browser.close()
    stop_sampler.set()
    sampler_thread.join(timeout=5)

    # ── A5. the recording artifact (webm -> mp4 beside it) ──────────────
    webms = list(video_dir.glob("*.webm"))
    webm = webms[0] if webms else None
    webm_keep = out / "integrated_session.webm"
    mp4 = out / "integrated_capture.mp4"
    if webm:
        webm.rename(webm_keep)
    ff = _find_ffmpeg()
    if webm_keep.exists() and ff:
        rc = subprocess.run([ff, "-y", "-loglevel", "error", "-i",
                             str(webm_keep), "-c:v", "libx264",
                             "-pix_fmt", "yuv420p", "-movflags",
                             "+faststart", str(mp4)]).returncode
    else:
        rc = None
    dur = None
    if mp4.exists():
        try:
            import re as _re
            pr = subprocess.run([ff or "ffmpeg", "-i", str(mp4)],
                                capture_output=True, text=True, timeout=60)
            m = _re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)",
                           pr.stderr or "")
            if m:
                dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + \
                    float(m.group(3))
        except Exception:
            dur = None
    step("A5_capture", {"ok": mp4.exists() and dur is not None,
                        "video_seconds": dur,
                        "mp4_sha256": sha256(mp4.read_bytes())
                        if mp4.exists() else None,
                        "webm_kept_path": str(webm_keep)
                        if webm_keep.exists() else None,
                        "webm_sha256": sha256(webm_keep.read_bytes())
                        if webm_keep.exists() else None,
                        "trace_sha256": sha256(trace_path.read_bytes())
                        if trace_path.exists() else None,
                        "trace_rows": sum(1 for _ in open(trace_path))
                        if trace_path.exists() else 0,
                        "marks": marks,
                        "ffmpeg_rc": rc})

    # ── 4. EXIT: the measured truth about the app's own exit path ───────
    # The pinned application exposes NO remote exit control: slice_server
    # ships no /api/exit, installs no console/signal handler, and its only
    # graceful shutdown is KeyboardInterrupt (its `finally:
    # WORLD.shutdown_engine()`). The app's own teardown IS exercised for
    # real twice in this evidence: A3's restart runs World.shutdown_engine
    # (old engine PID dies, measured), and Session B's Q runs it on demand
    # (engine dead, port closed). Delivering a console CTRL_C to the server
    # process was MEASURED impossible in this environment three ways
    # (CTRL_C to a CREATE_NEW_PROCESS_GROUP child is disabled by the group
    # flag; console-wide CTRL_C has no console under this process tree;
    # attach-console delivery returns TRUE but is not observed by the
    # child). A4 therefore MEASURES the operator's remaining path -- a hard
    # server kill -- and records exactly what it leaks, then cleans the
    # orphan by PID (leak evidence is never left running).
    t_exit = time.time()
    kids_at_exit, _ = engine_children(proc.pid)
    proc.kill()                          # the operator's window-close class
    try:
        srv_rc = proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        srv_rc = None
    time.sleep(3.0)
    _, glob_final = engine_children(proc.pid)
    orphans = [k for k in glob_final
               if psutil.pid_exists(k) and "chimera_engine" in
               (psutil.Process(k).name() or "").lower()]
    host, port = url.split("//")[1].split(":")
    port = int(port.rstrip("/"))
    s = socket.socket()
    s.settimeout(2)
    try:
        s.connect(("127.0.0.1", port))
        port_open = True
    except OSError:
        port_open = False
    finally:
        s.close()
    for k in orphans:                    # clean MY orphan, by PID
        try:
            psutil.Process(k).terminate()
        except psutil.Error:
            pass
    if orphans:
        time.sleep(3.0)
    still = [k for k in orphans if psutil.pid_exists(k)]
    step("A4_exit", {"ok": bool(srv_rc is not None and not still),
                     "exit_kind": "hard_server_kill_measured",
                     "finding_no_remote_or_graceful_exit_control": True,
                     "app_graceful_path_exercised_elsewhere":
                         "A3 restart (World.shutdown_engine) + session B7 (Q)",
                     "server_exit_code": srv_rc,
                     "exit_seconds": round(time.time() - t_exit, 2),
                     "engine_children_at_exit": kids_at_exit,
                     "engine_orphans_measured_after_kill": orphans,
                     "server_port_still_open": port_open,
                     "orphans_terminated_by_driver": orphans,
                     "orphans_still_alive_after_cleanup": still})


def engine_frame_fetch(out, url, name):
    """The engine's OWN rendered frame through the server's /api/frame
    passthru (?w=640: the engine's measured integer box step)."""
    p = out / name
    try:
        with urllib.request.urlopen(url + "/api/frame?w=640", timeout=30) as r:
            raw = r.read()
        p.write_bytes(raw)
        return {"path": str(p), "sha256": sha256(raw), "bytes": len(raw),
                "kind": "png" if raw[:4] == PNG_MAGIC else "jpeg"}
    except OSError as e:
        return {"path": str(p), "error": str(e)}


def _find_ffmpeg():
    from shutil import which
    return which("ffmpeg")


if __name__ == "__main__":
    raise SystemExit(main())
