"""session_a_wired.py -- MAT2-X02 integrated motion probe (prereg P3, F2).

Drives the REAL reconstructed playable application with the NEW session
wiring, ONLY through the player entry controls of the served page
(capture-phase overlay keys -> /api/session/key), in a REAL headless Chrome,
against a REAL native engine process built from the pinned source. Every
screenshot is real page pixels; the camera-path artifact is the ENGINE's own
/frame image through the server's own passthru; the recording is a real
browser video of the live application. Synthetic/PIL frames are never
offered as evidence.

Usage:
  python -B session_a_wired.py --play-root <scratch>/run/play \
      --engine-exe <scratch>/run/engine/chimera_engine.exe \
      --out evidence/integrated [--viewport 1280x720]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

import psutil

HERE = Path(__file__).resolve().parent

PNG_MAGIC = b"\x89PNG"
NEVER_PORT = 8127


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def http_json(base: str, path: str, timeout: float = 10) -> dict:
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return json.loads(r.read().decode())


def http_get(base: str, path: str, timeout: float = 15) -> bytes:
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return r.read()


def free_port() -> int:
    for _ in range(64):
        s = socket.socket()
        try:
            s.bind(("127.0.0.1", 0))
            p = s.getsockname()[1]
            return p if p != NEVER_PORT else (p + 1)
        finally:
            s.close()


def engine_children(server_pid: int) -> list:
    out = []
    try:
        for c in psutil.Process(server_pid).children(recursive=True):
            if "chimera_engine" in (c.name() or "").lower():
                out.append(c.pid)
    except psutil.Error:
        pass
    return out


def all_engine_pids() -> list:
    return [p.pid for p in psutil.process_iter(["name"])
            if p.info["name"] and "chimera_engine" in p.info["name"].lower()]


def pids_all_gone(pids: list) -> bool:
    for pid in pids:
        try:
            if psutil.Process(pid).is_running():
                return False
        except psutil.Error:
            continue
    return True


def port_closed_probe(port: int) -> bool:
    s = socket.socket()
    try:
        return s.connect_ex(("127.0.0.1", port)) != 0
    finally:
        s.close()


def wait_until(fn, timeout: float, interval: float = 0.25):
    """Poll fn() until truthy; return its last value (raises on timeout)."""
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            last = fn()
            if last:
                return last
        except Exception:
            pass
        time.sleep(interval)
    return last


def wait_settled(base: str, timeout: float) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if http_json(base, "/api/status").get("scene", {}).get("settled"):
                return True
        except OSError:
            pass
        time.sleep(1.0)
    return False


def snap_png(page, kind: str) -> bytes:
    if kind == "diagnostic":
        return page.screenshot(type="png")
    # clean: the CANVAS's OWN pixels via the page's draw-path toDataURL --
    # the webgl2 context has no preserveDrawingBuffer, so the read must run
    # inside the same task as the page's own draw (rAF wrap, no re-render).
    data = page.evaluate("""() => new Promise((resolve) => {
        const orig = window.requestAnimationFrame.bind(window);
        window.requestAnimationFrame = (cb) => orig((t) => {
            const r = cb(t);
            const c = document.querySelector('canvas');
            resolve(c ? c.toDataURL('image/png') : '');
            return r;
        });
    })""")
    if not data.startswith("data:image/png;base64,"):
        return b""
    import base64
    return base64.b64decode(data.split(",", 1)[1])


class Marks:
    """Wall-clock marks mapped onto the recording (context creation = t0)."""

    def __init__(self):
        self.t0 = time.time()
        self.rows = []

    def mark(self, label: str):
        self.rows.append({"mark": label, "video_s": round(time.time() - self.t0, 3)})

    def span(self, start_label: str, end_label: str) -> list:
        s = next((r["video_s"] for r in self.rows if r["mark"] == start_label), 0.0)
        e = next((r["video_s"] for r in self.rows if r["mark"] == end_label),
                 time.time() - self.t0)
        return [round(max(0.0, s), 3), round(max(s + 0.01, e), 3)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--play-root", type=Path, required=True)
    ap.add_argument("--engine-exe", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--viewport", default="1280x720")
    ap.add_argument("--settle-timeout", type=float, default=420.0)
    ap.add_argument("--driver-script", type=Path,
                    default=HERE / "wired_main.py")
    a = ap.parse_args()
    out = a.out
    out.mkdir(parents=True, exist_ok=True)
    receipt: dict = {
        "schema": "chimera.mat2_x02.wired_session_a.v1",
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "engine_exe": str(a.engine_exe),
        "engine_exe_sha256": sha256(a.engine_exe.read_bytes()),
        "play_root": str(a.play_root),
        "viewport": a.viewport,
        "steps": {},
        "predictions": {},
    }
    checks: list = []

    def check(cid: str, ok: bool, detail):
        checks.append({"id": cid, "pass": bool(ok), "detail": detail})
        print(("  [PASS] " if ok else "  [FIRE] ") + cid + " -- " + str(detail)[:160])
        return ok

    preflight_engines = all_engine_pids()
    receipt["preflight_engine_pids"] = preflight_engines

    port = free_port()
    base = "http://127.0.0.1:%d" % port
    server_log_path = out / "server_log.txt"
    server_log = server_log_path.open("wb")
    server = subprocess.Popen(
        [sys.executable, "-B", str(a.driver_script),
         "--play-root", str(a.play_root),
         "--engine-exe", str(a.engine_exe),
         "--port", str(port)],
        stdout=server_log, stderr=subprocess.STDOUT,
        cwd=str(a.play_root))
    receipt["server_pid"] = server.pid
    receipt["server_port"] = port
    receipt["server_log"] = str(server_log_path)
    time.sleep(2.0)

    # ── A1 BOOT (the pinned boot path through wired_main) ────────────────
    health = wait_until(lambda: http_json(base, "/api/health"), 300)
    ok = bool(health and health.get("ok") and health.get("world_booted"))
    status1 = wait_until(lambda: http_json(base, "/api/status"), 60) or {}
    pids1 = engine_children(server.pid)
    scene_sha = (status1.get("scene") or {}).get("scene_sha256")
    receipt["steps"]["A1_boot"] = {
        "health": health, "boot_count": status1.get("boot_count"),
        "engine_children": pids1, "scene_sha256": scene_sha,
        "status_url": base + "/api/status",
    }
    check("A1_boot_world_booted", ok, health)
    check("A1_boot_single_engine_child", len(pids1) == 1, pids1)
    check("A1_boot_count_is_1", status1.get("boot_count") == 1,
          status1.get("boot_count"))

    trace_path = out / "wired_trace.jsonl"
    trace_stop = threading.Event()

    def sampler():
        t0 = time.time()
        with trace_path.open("w", encoding="utf-8") as f:
            while not trace_stop.is_set():
                try:
                    st = http_json(base, "/api/status", timeout=4)
                    sess = http_json(base, "/api/session", timeout=4)
                    eng = st.get("engine_state") or {}
                    f.write(json.dumps({
                        "rel_s": round(time.time() - t0, 3),
                        "engine_state": eng,
                        "boot_count": st.get("boot_count"),
                        "settled": (st.get("scene") or {}).get("settled"),
                        "session_state": sess.get("state"),
                        "records": sess.get("records"),
                        "held": sess.get("held"),
                    }) + "\n")
                    f.flush()
                except OSError:
                    pass
                trace_stop.wait(0.5)

    threading.Thread(target=sampler, daemon=True).start()

    # ── A2 PLAY REACHED + session controls (REAL headless chrome) ────────
    from playwright.sync_api import sync_playwright
    vw, vh = (int(x) for x in a.viewport.split("x"))
    video_dir = out / "_video"
    video_dir.mkdir(exist_ok=True)
    console_errors: list = []
    page_errors: list = []
    marks = Marks()
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(
            viewport={"width": vw, "height": vh},
            record_video_dir=str(video_dir),
            record_video_size={"width": vw, "height": vh})
        marks.t0 = time.time()          # recording starts with the context
        page = context.new_page()
        page.on("console", lambda m: console_errors.append(m.text)
                if m.type == "error" else None)
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.goto(base + "/", wait_until="load", timeout=60000)

        overlay = wait_until(lambda: page.evaluate(
            "window.__SESSION_OVERLAY__ === true"), 30)
        hud = wait_until(lambda: page.evaluate(
            "!!document.getElementById('sessionhud')"), 15)
        marks.mark("attract_loaded")
        sess0 = http_json(base, "/api/session")
        check("A2_overlay_loaded", bool(overlay), overlay)
        check("A2_session_hud_present", bool(hud), hud)
        check("A2_initial_state_attract", sess0.get("state") == "attract",
              sess0.get("state"))

        def cam_fields():
            return page.evaluate("""() => {
                const c = window.__CHIMERA_VIEW;
                const cv = document.querySelector('canvas');
                return c ? {yaw: c.yaw, pit: c.pit, dist: c.dist,
                            target: [c.tx, c.ty, c.tz],
                            viewport: [cv.width, cv.height]} : null;
            }""")

        def screenshots(tag: str):
            page.evaluate("document.getElementById('sessionhud')"
                          ".scrollIntoView({block:'nearest'})")
            diag = snap_png(page, "diagnostic")
            clean = snap_png(page, "clean")
            (out / ("view_%s_diagnostic.png" % tag)).write_bytes(diag)
            (out / ("view_%s_clean.png" % tag)).write_bytes(clean)
            return {"diagnostic_sha256": sha256(diag),
                    "clean_sha256": sha256(clean),
                    "diagnostic_bytes": len(diag),
                    "clean_bytes": len(clean)}

        # ATTRACT view (before any start)
        view_attract = screenshots("attract")
        marks.mark("attract_view")

        # START: key-only (the overlay's capture-phase Enter)
        page.keyboard.press("Enter")
        started = wait_until(lambda: http_json(base, "/api/session")
                             .get("state") == "playing", 10)
        marks.mark("start_playing")
        check("A2_start_key_only", bool(started), started)

        # DEMAND RECORDS while playing: hold W, mapper must record
        n0 = http_json(base, "/api/session").get("records", 0)
        page.keyboard.down("w")
        time.sleep(1.5)
        page.keyboard.up("w")
        time.sleep(0.8)
        sessw = http_json(base, "/api/session")
        check("A2_mapper_records_while_playing",
              sessw.get("records", 0) > n0,
              "records %d -> %d" % (n0, sessw.get("records")))
        time.sleep(0.8)   # decay tail to silence (the mapper's own law)

        # wait for the standing start settle (real physics)
        settled1 = wait_settled(base, a.settle_timeout)
        check("A2_settled_before_restart", settled1, settled1)

        # BEFORE pinned state
        st_before = http_json(base, "/api/status")
        scene_before = st_before.get("scene") or {}
        pids_before = engine_children(server.pid)
        before_binding = {
            "when": "before_restart",
            "scene_sha256": scene_before.get("scene_sha256"),
            "start_state_sha256": scene_before.get("start_state_sha256"),
            "start_root_y": scene_before.get("start_root_y"),
            "boot_count": st_before.get("boot_count"),
            "engine_children": pids_before,
            "camera": cam_fields(),
            "session": http_json(base, "/api/session"),
        }
        (out / "state_binding_before.json").write_text(
            json.dumps(before_binding, indent=1))
        marks.mark("before_state")
        view_before = screenshots("before")
        try:
            frame_before = http_get(base, "/api/frame")
            (out / "engine_frame_before.png").write_bytes(frame_before)
            frame_before_sha = sha256(frame_before)
        except OSError as e:
            frame_before = b""
            frame_before_sha = None
            check("A2_engine_frame_before", False, repr(e))
        marks.mark("before_view")

        # PAUSE: key-only Escape; quiesce; ZERO records while paused
        page.keyboard.press("Escape")
        paused = wait_until(lambda: http_json(base, "/api/session")
                            .get("state") == "paused", 10)
        marks.mark("paused")
        np0 = http_json(base, "/api/session").get("records", 0)
        time.sleep(2.0)   # overlay keeps ticking; the flow must drop it all
        np1 = http_json(base, "/api/session").get("records", 0)
        check("A3_pause_key_only", bool(paused), paused)
        check("A3_zero_records_while_paused", np0 == np1,
              "records %d -> %d across 2.0s of ticks" % (np0, np1))
        view_paused = screenshots("paused")
        marks.mark("paused_view")

        # RESTART from paused: EXACTLY ONE World.boot, new engine PID
        page.keyboard.press("r")
        restarted = wait_until(
            lambda: (http_json(base, "/api/session").get("state") == "playing"
                     and http_json(base, "/api/status").get("boot_count") == 2),
            30)
        marks.mark("restart_boot")
        pids_after_boot = wait_until(
            lambda: (engine_children(server.pid)
                     and engine_children(server.pid) != pids_before
                     and len(engine_children(server.pid)) == 1), 30)
        old_pid_gone = wait_until(lambda: pids_all_gone(pids_before), 20)
        check("A3_restart_from_paused_reached_playing", bool(restarted),
              restarted)
        check("A3_engine_pid_swapped",
              bool(pids_after_boot) and pids_after_boot != pids_before,
              "%s -> %s" % (pids_before, pids_after_boot))
        check("A3_old_engine_terminated", bool(old_pid_gone), pids_before)

        settled2 = wait_settled(base, a.settle_timeout)
        check("A3_settled_after_restart", settled2, settled2)
        st_after = http_json(base, "/api/status")
        scene_after = st_after.get("scene") or {}
        after_binding = {
            "when": "after_restart",
            "scene_sha256": scene_after.get("scene_sha256"),
            "start_state_sha256": scene_after.get("start_state_sha256"),
            "start_root_y": scene_after.get("start_root_y"),
            "boot_count": st_after.get("boot_count"),
            "engine_children": engine_children(server.pid),
            "camera": cam_fields(),
            "session": http_json(base, "/api/session"),
        }
        (out / "state_binding_after.json").write_text(
            json.dumps(after_binding, indent=1))
        marks.mark("after_state")
        view_after = screenshots("after")
        try:
            frame_after = http_get(base, "/api/frame")
            (out / "engine_frame_after.png").write_bytes(frame_after)
            frame_after_sha = sha256(frame_after)
        except OSError as e:
            frame_after = b""
            frame_after_sha = None
            check("A3_engine_frame_after", False, repr(e))
        marks.mark("after_view")

        receipt["steps"]["A3_pinned_state"] = {
            "scene_sha256_before": before_binding["scene_sha256"],
            "scene_sha256_after": after_binding["scene_sha256"],
            "scene_sha_equal": (before_binding["scene_sha256"]
                                == after_binding["scene_sha256"]),
            "start_state_sha256_before": before_binding["start_state_sha256"],
            "start_state_sha256_after": after_binding["start_state_sha256"],
            "start_state_equal": (before_binding["start_state_sha256"]
                                  == after_binding["start_state_sha256"]),
            "boot_count": st_after.get("boot_count"),
            "engine_pids_before": pids_before,
            "engine_pids_after": after_binding["engine_children"],
            "engine_frames": {"before": frame_before_sha,
                              "after": frame_after_sha,
                              "byte_equal": (frame_before_sha is not None
                                             and frame_before_sha
                                             == frame_after_sha)},
        }
        check("A3_scene_sha256_byte_equal",
              receipt["steps"]["A3_pinned_state"]["scene_sha_equal"],
              "scene identity across the reload")
        # the engine's determinism claim, recorded AS MEASURED (never tuned)
        receipt["predictions"]["P3_start_state_equality"] = {
            "expected": "equal across boots (determinism claim)",
            "measured_equal": receipt["steps"]["A3_pinned_state"]
            ["start_state_equal"],
            "outcome": "PASS" if receipt["steps"]["A3_pinned_state"]
            ["start_state_equal"] else "FIRED (recorded as measured)",
        }

        # EXIT: key-only Q -> owned engine dead through the app's teardown
        page.keyboard.press("Q")
        exited = wait_until(lambda: http_json(base, "/api/session")
                            .get("state") == "exited", 10)
        marks.mark("exit_pressed")
        engine_dead = wait_until(lambda: engine_children(server.pid) == [], 15)
        marks.mark("engine_dead")
        check("A4_exit_key_only", bool(exited), exited)
        check("A4_engine_child_dead", bool(engine_dead),
              engine_children(server.pid))
        view_exited = screenshots("exited")
        marks.mark("exited_view")

        time.sleep(1.0)
        context.close()        # finalizes the recording
        browser.close()
    trace_stop.set()

    # ── recording → artifacts ────────────────────────────────────────────
    videos = sorted(video_dir.glob("*.webm"))
    webm_path = None
    if videos:
        webm_path = out / "wired_session.webm"
        webm_path.write_bytes(videos[0].read_bytes())
    receipt["steps"]["A5_capture"] = {
        "webm_bytes": webm_path.stat().st_size if webm_path else 0,
        "webm_sha256": sha256(webm_path.read_bytes()) if webm_path else None,
        "console_errors": console_errors,
        "page_errors": page_errors,
        "marks": marks.rows,
        "views": {"attract": view_attract, "before": view_before,
                  "paused": view_paused, "after": view_after,
                  "exited": view_exited},
    }
    check("A2_zero_console_errors", not console_errors, console_errors)
    check("A2_zero_page_errors", not page_errors, page_errors)
    check("A5_real_video_captured", bool(webm_path), str(webm_path))

    # ── A4 server shutdown through its own path; leak census ─────────────
    server.terminate()
    try:
        server.wait(timeout=15)
    except subprocess.TimeoutExpired:
        server.kill()
        server.wait(timeout=10)
    server_log.close()
    time.sleep(3.0)
    port_closed = wait_until(lambda: port_closed_probe(port), 10)
    surviving = [pid for pid in all_engine_pids()
                 if pid not in preflight_engines]
    receipt["steps"]["A4_exit"] = {
        "exit_kind": "server_own_shutdown_after_session_exit",
        "server_exit_code": server.poll(),
        "server_port": port,
        "server_port_still_open": not port_closed,
        "engine_orphans_measured_after_kill": surviving,
        "orphans_terminated_by_driver": [],
        "preflight_engine_pids": preflight_engines,
    }
    check("A4_server_port_closed", port_closed, port)
    check("A4_zero_surviving_engines", not surviving, surviving)

    receipt["steps"]["A4_exit"]["server_log_bytes"] = server_log_path.stat().st_size
    receipt["marks"] = marks.rows
    receipt["checks"] = checks
    fired = [c for c in checks if not c["pass"]]
    receipt["verdict"] = ("ALL CHECKS PASS (%d checks)" % len(checks)
                          if not fired else
                          "%d of %d checks FIRED: %s" % (len(fired),
                                                         len(checks),
                                                         [c["id"] for c in fired]))
    receipt["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                            time.gmtime())
    (out / "session_a_wired_receipt.json").write_text(
        json.dumps(receipt, indent=1, default=str))
    print("SESSION A (wired) RESULT: " + receipt["verdict"])
    return 0 if not fired else 1


if __name__ == "__main__":
    raise SystemExit(main())
