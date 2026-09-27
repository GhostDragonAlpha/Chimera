"""real_seam_session.py -- ONT-U01 correction: the bounded REAL
command-boundary/receiver run (PREREGISTRATION_REAL_RUN.md, frozen at
5751ae10 BEFORE this run).

What runs (all real): the pinned playable-slice application (play
8550b634, raw-blob reconstruction; slice_server owns a real native
chimera_engine.exe built from the pinned engine source of the same
commit), the served page in headless Chrome channel "chrome", and the
REAL pinned U01 InputMapper + CommandRecord v1 seam imported byte-exact
from this contribution's hash-asserted reference/ subtree inside THIS
driver process.

The correction's non-circular structure:
  * INPUT: real key events traverse the browser's real input pipeline into
    the page's real keydown/keyup handlers; an ADDITIVE in-page hook
    (installed via page.evaluate; the pinned page file is not edited)
    mirrors what the page received to the driver.
  * COMMAND BOUNDARY: the real pinned mapper emits CommandRecord v1
    records at its real 20 Hz grid on the real monotonic clock (issued_tick
    anchored to the ENGINE's own tick counter).
  * RECEIVER: the real engine process. Its real ingestion answers are
    MEASURED (R5), including the gait machine's own refusal and the 404s
    of candidate command routes.
  * OBSERVATION: the receiving body state is read ONLY from the engine's
    own state/frame path (/tick_state stamps, /api/snapshot FULL36
    geometry, /api/frame pixels) -- never reconstructed from commands.
  * The body-vs-command law (R4) is evaluated on the OBSERVED states.

Usage:
  python -B real_seam_session.py --play-root <run play copy> \
      --engine-exe <built exe> --reference <contrib ONT-U01 reference> \
      --out <evidence/real>
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import struct
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import psutil

PNG_MAGIC = b"\x89PNG"
SNAP_HDR = "<IQIfffffQII"
SNAP_MAGIC = 0x31534854
V_MAX_M_S = 0.763625          # the seam's own in-band ceiling (command_record)
OMEGA_MAX = 1.6
CODE_TO_NAME = {"KeyW": "W", "KeyA": "A", "KeyD": "D", "KeyS": "S"}


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def http_json(base: str, path: str, timeout: float = 10) -> dict:
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return json.loads(r.read().decode())


def http_post_json(base: str, path: str, obj: dict, timeout: float = 10):
    # COMPACT body: the engine's boolean routes parse by literal
    # '"on":true' substring -- a pretty-printed space after the colon
    # would silently measure the off-path instead of the refusal.
    req = urllib.request.Request(
        base + path, data=json.dumps(obj, separators=(",", ":")).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")


def engine_children(server_pid: int) -> list:
    out = []
    try:
        for c in psutil.Process(server_pid).children(recursive=True):
            if "chimera_engine" in (c.name() or "").lower():
                out.append(c.pid)
    except psutil.Error:
        pass
    return out


class Trace:
    """One jsonl for observed states, geometry, events, commands."""

    def __init__(self, path: Path):
        self.fh = open(path, "w", encoding="utf-8")
        self.lock = threading.Lock()
        self.t0 = time.perf_counter()

    def wall_ms(self) -> int:
        return int(round((time.perf_counter() - self.t0) * 1000))

    def row(self, **kw):
        kw["wall_ms"] = self.wall_ms()
        with self.lock:
            self.fh.write(json.dumps(kw) + "\n")
            self.fh.flush()

    def close(self):
        with self.lock:
            self.fh.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--play-root", type=Path, required=True)
    ap.add_argument("--engine-exe", type=Path, required=True)
    ap.add_argument("--reference", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--viewport", default="1280x720")
    a = ap.parse_args()
    out = a.out
    out.mkdir(parents=True, exist_ok=True)
    receipt: dict = {"schema": "chimera.ont_u01.real_seam_session.v1",
                     "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                  time.gmtime()),
                     "engine_exe": str(a.engine_exe),
                     "engine_exe_sha256": sha256(a.engine_exe.read_bytes()),
                     "play_root": str(a.play_root),
                     "reference": str(a.reference),
                     "viewport": a.viewport,
                     "steps": {}}

    def step(name, obj_):
        receipt["steps"][name] = obj_
        (out / "session_real_receipt.json").write_text(
            json.dumps(receipt, indent=1), encoding="utf-8")
        print("  [real] %s: %s" % (name, json.dumps(obj_, default=str)[:220]))

    # ── the REAL pinned seam (hash-asserted import; TIE2 guard) ─────────
    sys.path.insert(0, str(a.reference))
    PINNED = {
        "tools/monkey_campaign/product/input_mapper.py":
            "7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44",
        "tools/science_funnel/typeb_export/command_record.py":
            "6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e",
    }
    pins = {}
    for rel, want in PINNED.items():
        got = sha256((a.reference / rel).read_bytes())
        if got != want:
            step("pin_drift", {"rel": rel, "got": got, "want": want})
            return 1
        pins[rel] = got
    from tools.science_funnel.typeb_export.command_record import (  # noqa: E402
        CommandRecord, V1FamilyAdapter, decode_v1, HOLD_TICKS, PHYSICS_HZ,
        POLICY_HZ, V_MAX_IN_BAND_M_S)
    from tools.monkey_campaign.product.input_mapper import (  # noqa: E402
        InputMapper, MockSink, INTERVAL_MS, RELEASE_DECAY_MS)
    step("seam_pins", {"pins": pins, "PHYSICS_HZ": PHYSICS_HZ,
                       "POLICY_HZ": POLICY_HZ, "HOLD_TICKS": HOLD_TICKS,
                       "INTERVAL_MS": INTERVAL_MS,
                       "V_MAX_IN_BAND_M_S": V_MAX_IN_BAND_M_S})

    # ── preflight: only MY workspace's leftovers ─────────────────────────
    pre = []
    for p in psutil.process_iter(["name"]):
        try:
            if p.info["name"] and "chimera_engine" in p.info["name"].lower():
                if str(a.engine_exe.parent) in (p.cwd() or ""):
                    p.terminate()
                    pre.append(p.pid)
        except (psutil.Error, TypeError, PermissionError):
            continue
    if pre:
        time.sleep(3.0)
    receipt["preflight_terminated_leftover_engines"] = pre

    # ── R1: the server owns the real engine ─────────────────────────────
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
            step("R1_launch_failed", {"exit": proc.returncode})
            return 1
        for line in srv_out.read_text(errors="replace").splitlines():
            if line.startswith("slice: "):
                url = line.split(" ", 1)[1].strip()
        time.sleep(0.25)
    if url is None:
        step("R1_no_url", {})
        proc.kill()
        return 1
    health = None
    boot_deadline = time.time() + 300
    while time.time() < boot_deadline:
        try:
            h = http_json(url, "/api/health", timeout=5)
            if h.get("world_booted"):
                health = h
                break
        except OSError:
            pass
        time.sleep(1.0)
    kids = engine_children(proc.pid)
    st = http_json(url, "/api/status")
    engine_pid = kids[0] if kids else None
    engine_port = None
    if engine_pid:
        try:
            for c in psutil.Process(engine_pid).net_connections(kind="inet"):
                if c.status == psutil.CONN_LISTEN and c.laddr:
                    engine_port = c.laddr.port
                    break
        except (psutil.Error, OSError):
            pass
    step("R1_boot", {"ok": bool(health and len(kids) == 1),
                     "url": url, "server_pid": proc.pid,
                     "engine_pid": engine_pid, "engine_port": engine_port,
                     "boot_seconds": round(time.time() - t0, 2),
                     "health": health,
                     "scene_sha256": (st.get("scene") or {}).get("scene_sha256"),
                     "boot_count": st.get("boot_count")})
    if not (health and kids):
        step("R1_VERDICT", "FAIL")
        proc.kill()
        return 1
    engine_url = "http://127.0.0.1:%d" % engine_port if engine_port else None

    # settle (the scene's own flag; slice_server's convergence window)
    settled = False
    deadline = time.time() + 420
    while time.time() < deadline:
        try:
            s = http_json(url, "/api/status")
            if (s.get("scene") or {}).get("settled"):
                settled = True
                break
        except OSError:
            pass
        time.sleep(1.0)
    scene = (s.get("scene") or {})
    step("R1_settled", {"ok": settled,
                        "settled_root_y": scene.get("start_root_y"),
                        "start_state_sha256": scene.get("start_state_sha256"),
                        "scene_sha256": scene.get("scene_sha256"),
                        "wait_seconds": round(time.time() - t0, 1)})

    try:
        run_session(a, receipt, step, proc, url, engine_url, engine_pid,
                    CommandRecord, V1FamilyAdapter, decode_v1, InputMapper,
                    MockSink, PHYSICS_HZ)
    finally:
        teardown(proc, engine_pid, out, receipt, step)

    verdict_ok = all(receipt["steps"].get(k, {}).get("ok", False)
                     for k in ("R1_boot", "R1_settled", "R2_control_press",
                               "R3_stream", "R6_capture"))
    receipt["verdict"] = "PASS" if verdict_ok else "CHECK_STEPS"
    receipt["R4_note"] = "the R4 no-teleportation law on OBSERVED body " \
                         "state is evaluated by real_numerical.py into " \
                         "numerical_receipt_real.json from trace_real.jsonl"
    receipt["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                            time.gmtime())
    (out / "session_real_receipt.json").write_text(
        json.dumps(receipt, indent=1), encoding="utf-8")
    print("REAL SESSION VERDICT:", receipt["verdict"])
    return 0


def run_session(a, receipt, step, proc, url, engine_url, engine_pid,
                CommandRecord, V1FamilyAdapter, decode_v1, InputMapper,
                MockSink, PHYSICS_HZ):
    out = a.out
    vw, vh = (int(x) for x in a.viewport.split("x"))
    trace = Trace(out / "trace_real.jsonl")
    cmd_fh = open(out / "command_stream.jsonl", "w", encoding="utf-8")
    console_errors: list = []
    page_errors: list = []

    from playwright.sync_api import sync_playwright

    video_dir = out / "_video_raw"
    video_dir.mkdir(exist_ok=True)

    def status_now():
        return http_json(url, "/api/status", timeout=5)

    with sync_playwright() as pw:
        browser = page = context = None
        channel_used = None
        deviations = []
        for attempt_channel in ("chrome", None):
            try:
                kwargs = {"headless": True, "timeout": 120000,
                          "args": ["--enable-gpu",
                                   "--enable-unsafe-swiftshader"]}
                if attempt_channel:
                    kwargs["channel"] = attempt_channel
                b = pw.chromium.launch(**kwargs)
                ctx = b.new_context(
                    viewport={"width": vw, "height": vh},
                    record_video_dir=str(video_dir),
                    record_video_size={"width": vw, "height": vh})
                p = ctx.new_page()
                p.set_default_timeout(120000)
                p.goto(url + "mock_registry.json",
                       wait_until="domcontentloaded", timeout=45000)
                browser, page, context = b, p, ctx
                channel_used = attempt_channel or "chromium-bundled"
                break
            except Exception as e:  # noqa: BLE001
                try:
                    b.close()
                except Exception:
                    pass
                deviations.append({"channel": attempt_channel
                                   or "chromium-bundled",
                                   "error": str(e)[:300]})
        if browser is None:
            raise RuntimeError("no browser channel could navigate")
        step("R6_browser_channel", {"channel": channel_used,
                                    "deviations": deviations})
        page.on("console", lambda m: console_errors.append(m.text)
                if m.type == "error" else None)
        page.on("pageerror", lambda e: page_errors.append(str(e)))

        t_load = time.perf_counter()
        page.goto(url, wait_until="domcontentloaded", timeout=120000)
        live = False
        line = ""
        deadline = time.time() + 90
        while time.time() < deadline:
            try:
                line = page.evaluate(
                    "document.getElementById('status').textContent")
            except Exception:
                line = ""
            if line.startswith("REAL engine numbers"):
                live = True
                break
            time.sleep(0.5)
        ticks_a = status_now().get("engine_state", {}).get("ticks")
        time.sleep(2.0)
        ticks_b = status_now().get("engine_state", {}).get("ticks")
        cam0 = page.evaluate("JSON.stringify(window.__CHIMERA_VIEW||null)")
        marks = {"page_load": round(t_load - trace.t0, 3),
                 "play_live": round(time.perf_counter() - trace.t0, 3)}
        step("R2_page_live", {"ok": bool(live and ticks_b != ticks_a),
                              "status_line": line,
                              "ticks_advanced": ticks_b != ticks_a,
                              "camera_handle": cam0,
                              "marks": marks,
                              "console_errors": console_errors,
                              "page_errors": page_errors})

        # the additive in-page hook (page file untouched): mirror what the
        # page's own handlers receive to the driver
        page.evaluate("""() => {
            window.__U01_EV = [];
            const push = (e, down) => window.__U01_EV.push(
                {code: e.code, key: e.key, down: down,
                 t: performance.now()});
            window.addEventListener('keydown', e => push(e, true), true);
            window.addEventListener('keyup', e => push(e, false), true);
            window.addEventListener('blur',
                () => window.__U01_EV.push(
                    {code: '__blur__', key: '__blur__', down: true,
                     t: performance.now()}), true);
        }""")

        # ── R2: the observer-validation control (the page's own SPACE) ──
        pre = status_now().get("engine_state", {})
        rest_y = float(pre.get("root_y", 0.0))
        trace.row(kind="event", event="R2_space_press")
        page.keyboard.press("Space")
        max_vy, max_dy = 0.0, 0.0
        deadline = time.time() + 20
        while time.time() < deadline:
            es = status_now().get("engine_state", {})
            vy = abs(float(es.get("root_vy", 0.0)))
            dy = abs(float(es.get("root_y", rest_y)) - rest_y)
            max_vy, max_dy = max(max_vy, vy), max(max_dy, dy)
            trace.row(kind="obs", phase="R2", ts_us=es.get("ts_us"),
                      ticks=es.get("ticks"), root_y=es.get("root_y"),
                      root_vy=es.get("root_vy"))
            if time.time() > deadline - 14 and vy < 1e-4 and dy < 5e-4:
                break
            time.sleep(0.04)
        r2 = {"ok": bool(max_vy > 0.01 and max_dy > 1e-3),
              "rest_root_y": rest_y, "max_abs_root_vy": round(max_vy, 6),
              "max_abs_root_y_delta": round(max_dy, 6),
              "frozen_prediction": "max|vy|>0.01 and max|dy|>1e-3",
              "observed_transient": bool(max_vy > 0 or max_dy > 0)}
        step("R2_control_press", r2)

        # AUX (declared auxiliary in the receipt): the page's OWN fall test
        # is the engine's root law demo -- the strong observer validation.
        trace.row(kind="event", event="AUX_drop_test")
        page.keyboard.press("3")
        aux_vy = aux_dy = 0.0
        deadline = time.time() + 100
        while time.time() < deadline:
            try:
                s = status_now()
                es = s.get("engine_state", {})
                ft = s.get("fall_test") or {}
                if ft.get("phase") == "done":
                    break
                vy = abs(float(es.get("root_vy", 0.0)))
                aux_vy = max(aux_vy, vy)
                time.sleep(0.1)
            except OSError:
                time.sleep(0.5)
        verdict_ft = s.get("fall_test") or {}
        # wait back at rest
        deadline = time.time() + 120
        while time.time() < deadline:
            es = status_now().get("engine_state", {})
            if abs(float(es.get("root_y", 99)) - rest_y) < 5e-4 and \
                    abs(float(es.get("root_vy", 1))) < 1e-3:
                break
            time.sleep(0.5)
        step("AUX_observer_validation", {
            "ok": bool(aux_vy > 0.05),
            "max_abs_root_vy": round(aux_vy, 4),
            "engine_verdict": verdict_ft,
            "note": "auxiliary (not a frozen clause): the page's own [3] "
                    "fall test is the engine's root law demo; it shows the "
                    "observation channel sees LARGE real body motion"})

        # ── R3+R4: the real stream ───────────────────────────────────────
        sink = MockSink()
        engine_ticks0 = status_now().get("engine_state", {}).get("ticks", 0)
        t0_ms = trace.wall_ms()

        def tick_source() -> int:
            return int(engine_ticks0 +
                       (trace.wall_ms() - t0_ms) * PHYSICS_HZ // 1000)

        mapper = InputMapper(sink, tick_source=tick_source)
        adapter = V1FamilyAdapter()

        SCHEDULE = [  # (kind, code/name, at_s)  -- PREREG frozen timeline
            ("key_down", "KeyW", 0.0), ("key_down", "KeyA", 1.0),
            ("key_up", "KeyA", 2.0), ("key_down", "KeyD", 3.0),
            ("key_up", "KeyD", 3.5), ("key_up", "KeyW", 4.0),
            ("key_down", "KeyW", 6.0), ("blur", None, 7.0),
            ("key_down", "KeyW", 10.0), ("key_up", "KeyW", 12.0)]
        STREAM_END_S, TAIL_S = 16.0, 20.0

        sampler_stop = threading.Event()

        def sampler():
            next_geom = time.perf_counter()
            while not sampler_stop.is_set():
                w = trace.wall_ms()
                try:
                    es = status_now().get("engine_state", {})
                    trace.row(kind="obs", phase="stream", ts_us=es.get("ts_us"),
                              ticks=es.get("ticks"), root_y=es.get("root_y"),
                              root_vy=es.get("root_vy"))
                except OSError:
                    pass
                if time.perf_counter() >= next_geom:
                    next_geom = time.perf_counter() + 1.0
                    try:
                        with urllib.request.urlopen(
                                url + "/api/snapshot?fmt=FULL36",
                                timeout=30) as r:
                            raw = r.read()
                        magic, ts_us, ticks, ry, rv, pl, pu, dm, gap, \
                            fmtc, n = struct.unpack_from(SNAP_HDR, raw, 0)
                        import numpy as np
                        V = np.frombuffer(raw, dtype=np.float32,
                                          count=9 * n, offset=52)
                        g = V.reshape(n, 9)
                        trace.row(kind="geom", ticks=int(ticks),
                                  ts_us=int(ts_us), root_y=float(ry),
                                  root_vy=float(rv), n=int(n),
                                  cx=float(g[:, 0].mean()),
                                  cy=float(g[:, 1].mean()),
                                  cz=float(g[:, 2].mean()),
                                  magic_ok=magic == SNAP_MAGIC)
                    except (OSError, Exception) as e:  # noqa: BLE001
                        trace.row(kind="geom_error", error=str(e)[:120])
                sampler_stop.wait(0.04)

        th = threading.Thread(target=sampler, daemon=True)
        th.start()

        schedule_pending = list(SCHEDULE)
        emitted = []
        page_key_log = []
        t_stream = time.perf_counter()

        def stream_now_s() -> float:
            return time.perf_counter() - t_stream

        def drain_events():
            evs = page.evaluate("window.__U01_EV.splice(0)")
            for e in evs or []:
                name = CODE_TO_NAME.get(e.get("code"))
                if e.get("code") == "__blur__":
                    mapper.release_all(trace.wall_ms())
                    trace.row(kind="event", event="blur_release_all",
                              page_t=e.get("t"))
                elif name and e.get("down") is True:
                    mapper.press(name, trace.wall_ms())
                    trace.row(kind="event", event="page_key_down",
                              name=name, raw_key=e.get("key"),
                              code=e.get("code"), page_t=e.get("t"))
                elif name and e.get("down") is False:
                    mapper.release(name, trace.wall_ms())
                    trace.row(kind="event", event="page_key_up",
                              name=name, raw_key=e.get("key"),
                              code=e.get("code"), page_t=e.get("t"))

        def fire_due():
            while schedule_pending and \
                    stream_now_s() >= schedule_pending[0][2]:
                kind, code, at = schedule_pending.pop(0)
                if kind == "key_down":
                    page.keyboard.down(code[3].lower())
                elif kind == "key_up":
                    page.keyboard.up(code[3].lower())
                elif kind == "blur":
                    page.evaluate(
                        "window.dispatchEvent(new Event('blur'))")
                page_key_log.append({"kind": kind, "code": code,
                                     "at_s": at,
                                     "fired_s": round(stream_now_s(), 4)})
                trace.row(kind="event", event="driver_" + kind,
                          code=code, at_s=at)

        # the boundary loop: real monotonic clock, <= 5 ms steps
        while stream_now_s() < TAIL_S:
            loop_start = time.perf_counter()
            fire_due()
            drain_events()
            now = trace.wall_ms()
            for rec in mapper.tick(now):
                proj = adapter.project(rec)
                back = decode_v1(rec.canonical_fields())
                row = {"kind": "cmd", "wall_ms": now,
                       "v_forward": rec.v_forward,
                       "yaw_rate": rec.yaw_rate,
                       "issued_tick": rec.issued_tick,
                       "source": rec.source,
                       "stream_s": round(stream_now_s(), 4),
                       "proj_commanded_target_velocity_x":
                           proj.get("commanded_target_velocity_x"),
                       "roundtrip_bit_identical":
                           back.canonical_bytes() == rec.canonical_bytes()}
                emitted.append(row)
                cmd_fh.write(json.dumps(row) + "\n")
                cmd_fh.flush()
            time.sleep(max(0.0, 0.005 - (time.perf_counter() - loop_start)))
        sampler_stop.set()
        th.join(timeout=10)
        sink_pure = all(c[0] == "emit" for c in sink.calls)
        gaps = [emitted[i + 1]["wall_ms"] - emitted[i]["wall_ms"]
                for i in range(len(emitted) - 1)]
        held_gaps = [g for g in gaps if 35 <= g <= 65]
        step("R3_stream", {"ok": bool(emitted and sink_pure),
                           "records_emitted": len(emitted),
                           "sink_calls": len(sink.calls),
                           "sink_emit_only": sink_pure,
                           "max_abs_v_forward": max(
                               [abs(e["v_forward"]) for e in emitted]
                               or [0]),
                           "max_abs_yaw_rate": max(
                               [abs(e["yaw_rate"]) for e in emitted] or [0]),
                           "boundary_gap_ms_min": min(gaps or [0]),
                           "boundary_gap_ms_max": max(gaps or [0]),
                           "held_50ms_gaps": len(held_gaps),
                           "driver_key_log": page_key_log,
                           "page_events_total": len(page_key_log)})

        # ── R5: receiver capability, measured on the running engine ─────
        probes = {}
        if engine_url:
            stc, body = http_post_json(engine_url, "/tick_gait",
                                       {"on": True})
            probes["POST_/tick_gait_on"] = {"status": stc, "body": body}
            ts_after = http_json(engine_url, "/tick_state", timeout=5)
            probes["gait_enable_block_in_state"] = \
                ts_after.get("gait_enable_block")
            stc, body = http_post_json(engine_url, "/tick_stance",
                                       {"on": True})
            probes["POST_/tick_stance_on"] = {"status": stc, "body": body}
            for route in ("/command", "/api/command", "/tick_command"):
                stc, body = http_post_json(
                    engine_url, route,
                    {"v_forward": 0.5, "yaw_rate": 0.0,
                     "issued_tick": tick_source(),
                     "source": "u01_input_mapper"})
                probes["POST_" + route] = {"status": stc,
                                           "body": body[:200]}
        body_text = page.evaluate("document.body.innerText")
        loco_lines = [l.strip() for l in body_text.splitlines()
                      if "locomotion" in l.lower() or "MOCK" in l]
        probes["page_own_declarations"] = loco_lines[:8]
        step("R5_receiver_capability", {
            "engine_url": engine_url, "engine_pid": engine_pid,
            "probes": probes,
            "note": "R5 RECORDS the real answers; the frozen prediction is "
                    "that no route consumes V1 speed/heading records and "
                    "the gait machine refuses enablement for this body"})

        # ── R6: the three declared views through the page's own keys ────
        def capture_views(tag):
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
                clean.write_bytes(base64.b64decode(
                    data_url.split(",", 1)[1]))
            meta = page.evaluate(
                "JSON.stringify({cam: window.__CHIMERA_VIEW,"
                " cw: (document.getElementsByTagName('canvas')[0]||{}).width,"
                " ch: (document.getElementsByTagName('canvas')[0]||{}).height"
                "})")
            try:
                with urllib.request.urlopen(url + "/api/frame?w=640",
                                            timeout=30) as r:
                    raw = r.read()
                (out / ("engine_frame_%s.png" % tag)).write_bytes(raw)
                eng = {"sha256": sha256(raw), "bytes": len(raw)}
            except OSError as e:
                eng = {"error": str(e)}
            return {"diagnostic": {"path": str(diag),
                                   "sha256": sha256(diag.read_bytes())},
                    "clean": {"path": str(clean),
                              "sha256": sha256(clean.read_bytes())},
                    "camera": json.loads(meta), "engine_frame": eng}

        views = {}
        marks["view1_start"] = round(time.perf_counter() - trace.t0, 3)
        views["V1_normal_follow_camera_distance"] = capture_views("v1")
        marks["view1_end"] = round(time.perf_counter() - trace.t0, 3)

        page.keyboard.press("+")           # the page's own zoom-in key
        page.wait_for_timeout(400)
        page.keyboard.press("+")
        page.wait_for_timeout(400)
        page.keyboard.press("+")
        page.wait_for_timeout(600)
        cam2 = page.evaluate(
            "JSON.stringify(window.__CHIMERA_VIEW||null)")
        marks["view2_start"] = round(time.perf_counter() - trace.t0, 3)
        views["V2_obstructed_and_close_target_views"] = capture_views("v2")
        marks["view2_end"] = round(time.perf_counter() - trace.t0, 3)

        for _ in range(13):                # ~90 deg side orbit, page's key
            page.keyboard.press("ArrowLeft")
            page.wait_for_timeout(220)
        cam3 = page.evaluate(
            "JSON.stringify(window.__CHIMERA_VIEW||null)")
        marks["view3_start"] = round(time.perf_counter() - trace.t0, 3)
        views["V3_repeatable_inspection_side_view"] = capture_views("v3")
        marks["view3_end"] = round(time.perf_counter() - trace.t0, 3)
        step("R6_capture", {"ok": all(
            v["diagnostic"]["sha256"] and v["clean"]["sha256"]
            for v in views.values()),
            "views": views, "marks": marks,
            "camera_v2_close": json.loads(cam2),
            "camera_v3_side": json.loads(cam3)})

        video_path = page.video.path()
        context.close()
        browser.close()

    trace.row(kind="event", event="session_end")
    trace.close()
    cmd_fh.close()

    # video: webm -> mp4 beside it (conversion only)
    webms = list(video_dir.glob("*.webm"))
    webm_keep = out / "real_session.webm"
    mp4 = out / "real_capture.mp4"
    if webm_keep.exists():
        webm_keep.unlink()          # re-runs overwrite the previous artifact
    if mp4.exists():
        mp4.unlink()
    if webms:
        webms[0].rename(webm_keep)
    ff = None
    from shutil import which
    ff = which("ffmpeg")
    dur = None
    if webm_keep.exists() and ff:
        subprocess.run([ff, "-y", "-loglevel", "error", "-i",
                        str(webm_keep), "-c:v", "libx264", "-pix_fmt",
                        "yuv420p", "-movflags", "+faststart",
                        str(mp4)], check=True)
        pr = subprocess.run([ff, "-i", str(mp4)], capture_output=True,
                            text=True, timeout=60)
        import re as _re
        m = _re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", pr.stderr or "")
        if m:
            dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + \
                float(m.group(3))
    receipt["video"] = {"mp4": str(mp4),
                        "mp4_sha256": sha256(mp4.read_bytes())
                        if mp4.exists() else None,
                        "webm_sha256": sha256(webm_keep.read_bytes())
                        if webm_keep.exists() else None,
                        "video_seconds": dur}


def teardown(proc, engine_pid, out, receipt, step):
    """Kill only MY processes, by PID; verify nothing survives."""
    kids = engine_children(proc.pid) if proc.pid else []
    if proc.poll() is None:
        proc.kill()
    try:
        rc = proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        rc = None
    time.sleep(2.0)
    terminated = []
    for k in set(kids) | ({engine_pid} if engine_pid else set()):
        try:
            if psutil.pid_exists(k) and "chimera_engine" in \
                    (psutil.Process(k).name() or "").lower():
                psutil.Process(k).terminate()
                terminated.append(k)
        except psutil.Error:
            pass
    if terminated:
        time.sleep(3.0)
    still = [k for k in terminated if psutil.pid_exists(k)
             and "chimera_engine" in
             (psutil.Process(k).name() or "").lower()]
    glob = [p.pid for p in psutil.process_iter(["name"])
            if p.info["name"] and "chimera_engine" in
            p.info["name"].lower()]
    step("R7_teardown", {"ok": not still,
                         "server_exit_code": rc,
                         "engine_children": kids,
                         "terminated_by_driver": terminated,
                         "still_alive": still,
                         "engines_global_remaining": glob,
                         "note": "global count is shown for honesty; any "
                                 "nonzero remainder is NOT this lane's "
                                 "process (this lane's cwd-scoped "
                                 "preflight and child set are empty)"})


if __name__ == "__main__":
    raise SystemExit(main())
