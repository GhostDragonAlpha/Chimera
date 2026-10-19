"""The LIVE ENGINE pane: supervisor, proven-payload ingestion, honest state.

wk-play-live (viewer lane) 2026-10-01. The viewer's next playable increment:
the LIVE pane starts/stops the engine process (the W2 build+launch law),
POSTs the two PROVEN W2 payloads to /mesh_bin + /skin_bin after sha256
verification, and serves the engine's OWN /frame bytes as the only live
pixels plus /scene + /debug JSON explicitly labeled STATE.

Contract pinned here:
- the launch law is THE W2 LAW: [chimera_engine.exe, PORT, --no-restore];
  the viewer never adopts or kills a process it did not start (an already
  answering engine yields a named engine_already_up refusal, ingest only);
- ingest verifies sha256 AND byte-size pins BEFORE any POST; the refusal is
  named; the engine's own responses are reported VERBATIM; the W2 law holds:
  /skin_bin is a rest-pose splat upload (B=1 identity pose), NOT a
  simulation; zero physics claims anywhere;
- pixels are only ever the engine's own /frame bytes (proxied, never
  re-encoded, never viewer-drawn); /scene + /debug are served as STATE with
  state_kind naming them NOT pixels;
- THE FALSIFIER: killing the engine flips every live surface to a named
  down-state within LIVE_DOWN_FLIP_BOUND_S (contract-pinned here against a
  dying stub engine; MEASURED against the real engine by the gated
  EngineUpIntegration battery, driven by live_engine_battery.py);
- handler states without the live surface answer honestly (the single-
  surface idiom of PR #287/#290); the PAGE keeps the LIVE_ENGINE placeholder
  so server-side injection cannot silently break; LIVE_JS parses as
  JavaScript (the 2026-09-28 audit lesson).

The stub engine used here mirrors the engine's OBSERVED public HTTP contract
at revision e219e324 (W2 ENGINE_UP_RECEIPT.md). It pins VIEWER behavior; it
is not evidence about the engine itself — that is the gated battery's job.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from tools.product_viewer import server as pv
from tools.product_viewer.server import (LIVE_JS, PAGE, LiveEngineSupervisor,
                                         live_section)

# The sealed W2 payloads on this campaign host (referenced by hash; the pins
# themselves live in server.py and are re-verified before every POST).
SEALED_TILE = Path("E:/ChimeraWork/monkey-coordination/ingestion-spike/tile_mesh_meshbin.bin")
SEALED_BODY = Path("E:/ChimeraWork/monkey-coordination/ingestion-spike/body_tick10_skinbin.bin")


def _payloads_present() -> bool:
    if not (SEALED_TILE.is_file() and SEALED_BODY.is_file()):
        return False
    return (hashlib.sha256(SEALED_TILE.read_bytes()).hexdigest() == pv.LIVE_TILE_SHA256
            and hashlib.sha256(SEALED_BODY.read_bytes()).hexdigest() == pv.LIVE_BODY_SHA256)


# ---------------------------------------------------------------------------
# A stub engine mirroring the W2-observed public contract (viewer-side only).
# ---------------------------------------------------------------------------


class _StubEngine(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, obj, code=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        p = self.path.split("?")[0]
        srv = self.server
        if p == "/debug":
            if srv.require_marker is not None and not srv.require_marker.exists():
                self._send({"ok": False, "error": "not up yet"}, 404)
                return
            self._send({"n": srv.n, "active": True, "vp_valid": True})
        elif p == "/state":
            self._send({"n": srv.n})
        elif p == "/scene":
            self._send({"rows": [
                {"id": "body", "detail": "no mesh", "state": 0},
                {"id": "overlay", "detail": "loaded" if srv.tile_loaded else "none",
                 "state": 1 if srv.tile_loaded else 0}]})
        else:
            self._send({"ok": False, "error": "unknown route"}, 404)

    def do_POST(self):
        p = self.path.split("?")[0]
        srv = self.server
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n)
        if p == "/mesh_bin":
            if len(body) != pv.LIVE_TILE_BYTES:
                self._send({"ok": False, "error": "size mismatch"})
                return
            srv.tile_loaded = True
            self._send({"ok": True})
        elif p == "/skin_bin":
            if len(body) != pv.LIVE_BODY_BYTES:
                self._send({"ok": False, "error": "size mismatch"})
                return
            srv.body_loaded = True
            srv.n = 60000
            self._send({"ok": True})
        else:
            self._send({"ok": False, "error": "unknown route"}, 404)


def _start_stub(require_marker=None):
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _StubEngine)
    httpd.daemon_threads = True
    httpd.n = 0
    httpd.tile_loaded = False
    httpd.body_loaded = False
    httpd.require_marker = require_marker    # Path|None: /debug 404s until it exists
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd, f"http://127.0.0.1:{port}", t


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _get(base, path, timeout=20):
    try:
        with urllib.request.urlopen(base + path, timeout=timeout) as r:
            return r.status, r.read(), r.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        return e.code, e.read(), e.headers.get("Content-Type", "")


def _post(base, path, timeout=60):
    req = urllib.request.Request(base + path, data=b"", method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


# ---------------------------------------------------------------------------
# Launch law + refusals (no engine, any host).
# ---------------------------------------------------------------------------


class LaunchLaw(unittest.TestCase):
    def test_default_argv_is_the_w2_law(self):
        sup = LiveEngineSupervisor(pv.EngineClient("http://127.0.0.1:1"),
                                   "http://127.0.0.1:8157")
        self.assertEqual(sup.launch_argv("C:/x/chimera_engine.exe", 8157),
                         ["C:/x/chimera_engine.exe", "8157", "--no-restore"])

    def test_pins_are_the_proven_w2_payloads(self):
        self.assertEqual(pv.LIVE_TILE_SHA256,
                         "ab76eec64b5cf608afb036f82bcd1a5cff500165a24ed8db87e7b2647b976ea3")
        self.assertEqual(pv.LIVE_TILE_BYTES, 98940)
        self.assertEqual(pv.LIVE_BODY_SHA256,
                         "012b8b330f4dda814fe3a4622a8cd0382b981492590ae5adcdd8ab182cc926eb")
        self.assertEqual(pv.LIVE_BODY_BYTES, 4320020)

    def test_start_without_exe_refused_by_name(self):
        sup = LiveEngineSupervisor(pv.EngineClient("http://127.0.0.1:1"),
                                   "http://127.0.0.1:1")
        r = sup.start()
        self.assertFalse(r["ok"])
        self.assertEqual(r["state"], "not_configured")
        self.assertIn("--live-engine-exe", r["error"])
        self.assertIn("cmake", r["error"])

    def test_start_with_missing_exe_refused_by_name(self):
        sup = LiveEngineSupervisor(pv.EngineClient("http://127.0.0.1:1"),
                                   "http://127.0.0.1:1",
                                   exe_path="Z:/nope/chimera_engine.exe")
        r = sup.start()
        self.assertFalse(r["ok"])
        self.assertEqual(r["state"], "exe_missing")
        self.assertIn("missing", r["error"])

    def test_status_is_honest_and_never_raises(self):
        sup = LiveEngineSupervisor(pv.EngineClient("http://127.0.0.1:1"),
                                   "http://127.0.0.1:1")
        s = sup.status()
        self.assertTrue(s["ok"])
        self.assertFalse(s["engine_up"])          # dead URL probed honestly
        self.assertFalse(s["exe_configured"])
        self.assertIsNone(s["viewer_started"])
        self.assertIn("cmake -S ChimeraEngine/engine", s["build_recipe"])
        self.assertIn("--config Release", s["build_recipe"])
        self.assertEqual(s["pins"]["tile_bytes"], pv.LIVE_TILE_BYTES)


class IngestRefusalContract(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="viewer_live_"))
        self.sup = LiveEngineSupervisor(pv.EngineClient("http://127.0.0.1:1"),
                                        "http://127.0.0.1:1")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_engine_down_refused_by_name(self):
        r = self.sup.ingest()
        self.assertFalse(r["ok"])
        self.assertEqual(r["state"], "engine_down")
        self.assertIn("start it first", r["error"])

    def test_unconfigured_payload_refused_by_name(self):
        stub, url, _thread = _start_stub()
        try:
            sup = LiveEngineSupervisor(pv.EngineClient(url), url)
            r = sup.ingest()
            self.assertFalse(r["ok"])
            self.assertEqual(r["state"], "tile_refused")
            self.assertIn("--ingest-tile", r["error"])
        finally:
            stub.shutdown()

    def test_missing_payload_file_refused_by_name(self):
        stub, url, _thread = _start_stub()
        try:
            sup = LiveEngineSupervisor(pv.EngineClient(url), url,
                                       tile_path=str(self.tmp / "nope.bin"))
            r = sup.ingest()
            self.assertFalse(r["ok"])
            self.assertEqual(r["state"], "tile_refused")
            self.assertIn("unreadable", r["error"])
        finally:
            stub.shutdown()

    def test_wrong_bytes_refused_before_any_post(self):
        # ANY other bytes must be refused by name BEFORE a POST happens: the
        # stub engine records nothing, so a wrong-sha refusal must leave it
        # untouched (overlay row still "none").
        wrong = self.tmp / "wrong.bin"
        wrong.write_bytes(b"\x00" * pv.LIVE_TILE_BYTES)   # right size, wrong identity
        stub, url, _thread = _start_stub()
        try:
            sup = LiveEngineSupervisor(pv.EngineClient(url), url,
                                       tile_path=str(wrong))
            r = sup.ingest()
            self.assertFalse(r["ok"])
            self.assertEqual(r["state"], "tile_refused")
            self.assertIn("sha256 mismatch", r["error"])
            self.assertIn("refusing to POST unverified bytes", r["error"])
            self.assertFalse(stub.tile_loaded)
        finally:
            stub.shutdown()


# ---------------------------------------------------------------------------
# Supervisor mechanics against a sleeper process + stub engine contract.
# ---------------------------------------------------------------------------


class SupervisorMechanics(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="viewer_live_sup_"))
        self.marker = self.tmp / "engine_up.marker"
        self.sleeper = self.tmp / "sleeper.py"
        self.sleeper.write_text(
            "import sys, time\n"
            "open(sys.argv[1], 'w').write('up')\n"
            "time.sleep(180)\n", encoding="utf-8")
        # The stub's /debug answers 404 until the SPAWNED process touches the
        # marker: start()'s pre-check sees "not up", the spawn happens, the
        # bounded probe then finds the port answering — the real start loop.
        self.stub, self.url, self.thread = _start_stub(require_marker=self.marker)
        self.sup = None

    def tearDown(self):
        sup = self.sup
        if sup is not None and sup.proc is not None and sup.proc.poll() is None:
            sup.proc.kill()
            try:
                sup.proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                pass
        self.stub.shutdown()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _sup(self):
        sup = LiveEngineSupervisor(pv.EngineClient(self.url), self.url,
                                   exe_path=sys.executable)
        sup.launch_argv = lambda exe, port: [sys.executable, "-B", str(self.sleeper),
                                             str(self.marker)]
        self.sup = sup
        return sup

    def test_start_status_stop_cycle(self):
        sup = self._sup()
        r = sup.start()
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["state"], "up")
        self.assertTrue(sup.up())                     # the stub answers /debug
        self.assertTrue(sup.status()["viewer_started"]["alive"])
        self.assertTrue(sup.status()["engine_up"])
        s = sup.stop()
        self.assertTrue(s["ok"], s)
        self.assertEqual(s["state"], "stopped")
        self.assertIsNotNone(sup.proc.poll())         # process really gone
        self.assertFalse(sup.status()["viewer_started"]["alive"])
        self.assertTrue(sup.status()["engine_up"])    # stub still answers

    def test_second_start_refused_while_running(self):
        sup = self._sup()
        self.assertTrue(sup.start()["ok"])
        r = sup.start()
        self.assertFalse(r["ok"])
        self.assertEqual(r["state"], "already_running")
        self.assertIn("pid", r["error"])

    def test_start_refuses_engine_it_did_not_start(self):
        # an engine (here: an unprimed stub) already answering on the URL ->
        # the viewer refuses to adopt: named engine_already_up, none spawned
        stub2, url2, _thread2 = _start_stub()
        try:
            sup = LiveEngineSupervisor(pv.EngineClient(url2), url2,
                                       exe_path=sys.executable)
            sup.launch_argv = lambda exe, port: [sys.executable, "-B",
                                                 str(self.sleeper), str(self.marker)]
            r = sup.start()
            self.assertFalse(r["ok"])
            self.assertEqual(r["state"], "engine_already_up")
            self.assertIn("will not adopt", r["error"])
            self.assertIsNone(sup.proc)
        finally:
            stub2.shutdown()

    def test_stop_without_process_refused_honestly(self):
        sup = LiveEngineSupervisor(pv.EngineClient(self.url), self.url)
        r = sup.stop()
        self.assertFalse(r["ok"])
        self.assertEqual(r["state"], "not_running")
        self.assertIn("no viewer-started engine process", r["error"])


class IngestAgainstStub(unittest.TestCase):
    """Happy-path ingest against the W2-shaped stub, using the REAL pinned
    payloads (the pins are the identity; nothing else can pass them)."""

    @classmethod
    def setUpClass(cls):
        if not _payloads_present():
            raise unittest.SkipTest("sealed W2 payloads not present on this host")
        cls.stub, cls.url, cls.thread = _start_stub()
        cls.sup = LiveEngineSupervisor(pv.EngineClient(cls.url), cls.url,
                                       tile_path=str(SEALED_TILE),
                                       body_path=str(SEALED_BODY))

    @classmethod
    def tearDownClass(cls):
        cls.stub.shutdown()

    def test_ingest_reports_engine_words_verbatim_and_state_flip(self):
        r = self.sup.ingest()
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["state"], "ingested")
        self.assertEqual(r["tile"]["http"], 200)
        self.assertEqual(r["tile"]["engine_response"]["verbatim"], '{"ok": true}')
        self.assertEqual(r["body"]["http"], 200)
        self.assertEqual(r["body"]["engine_response"]["verbatim"], '{"ok": true}')
        # W2 acceptance channel: /scene overlay row none->loaded, /debug n 0->60000
        self.assertEqual(r["debug_before"], {"n": 0, "active": True, "vp_valid": True})
        self.assertEqual(r["debug_after"]["n"], 60000)
        overlay_after = next(row for row in r["scene_after"]["rows"]
                             if row["id"] == "overlay")
        self.assertEqual(overlay_after["state"], 1)
        self.assertEqual(overlay_after["detail"], "loaded")
        # the result persists in status (the pane renders from it)
        self.assertTrue(self.sup.status()["ingest"]["ok"])

    def test_engine_size_mismatch_is_reported_verbatim(self):
        # negative control at the contract level: the W2 negative control's
        # exact engine response, observed through the same client the
        # supervisor uses (the engine refuses wrong-sized bytes by name).
        st, body = self.sup.engine.post_raw("/mesh_bin", b"\x00" * 24)
        self.assertEqual(st, 200)
        self.assertEqual(json.loads(body.decode()),
                         {"ok": False, "error": "size mismatch"})


# ---------------------------------------------------------------------------
# Routes + page wiring.
# ---------------------------------------------------------------------------


class RouteWiring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stub, cls.url, cls.thread = _start_stub()
        engine = pv.EngineClient(cls.url)
        handler = type("BoundHandler", (pv.ViewerHandler,), {
            "engine": engine,
            "ring": pv.RingBuffer(4),
            "camera": pv.CameraPanel(engine),
            "started": 0.0,
            "capture_thread": None,
            "mirror": pv.EngineWindowMirror(cls.url, 1),
            "live": LiveEngineSupervisor(engine, cls.url),
        })
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.httpd.daemon_threads = True
        cls.port = cls.httpd.server_address[1]
        t = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        t.start()
        cls.base = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.stub.shutdown()

    def test_engine_status_route(self):
        st, body, ctype = _get(self.base, "/api/live/engine")
        self.assertEqual(st, 200)
        self.assertIn("application/json", ctype)
        d = json.loads(body)
        self.assertTrue(d["ok"])
        self.assertTrue(d["engine_up"])            # the stub answers
        self.assertFalse(d["exe_configured"])
        self.assertEqual(d["pins"]["tile_sha256"], pv.LIVE_TILE_SHA256)

    def test_state_route_labels_state_not_pixels(self):
        st, body, _ = _get(self.base, "/api/live/state")
        self.assertEqual(st, 200)
        d = json.loads(body)
        self.assertTrue(d["ok"])
        self.assertIn("STATE", d["state_kind"])
        self.assertIn("NOT pixels", d["state_kind"])
        self.assertEqual(d["scene"]["rows"][1]["id"], "overlay")
        # n is whatever the shared stub's current state is (alphabetical test
        # order means the ingest happy-path may already have run): the STATE
        # route must echo the ENGINE'S value verbatim, never a local guess.
        self.assertIsInstance(d["debug"].get("n"), int)

    def test_ingest_route_happy_path(self):
        if not _payloads_present():
            self.skipTest("sealed W2 payloads not present on this host")
        # give the route's supervisor the sealed payload paths
        live = self.httpd.RequestHandlerClass.live
        live.tile_path = str(SEALED_TILE)
        live.body_path = str(SEALED_BODY)
        st, body = _post(self.base, "/api/live/engine/ingest")
        self.assertEqual(st, 200)
        d = json.loads(body)
        self.assertTrue(d["ok"], d)
        self.assertEqual(d["tile"]["engine_response"]["verbatim"], '{"ok": true}')

    def test_start_route_refuses_when_engine_already_up(self):
        st, body = _post(self.base, "/api/live/engine/start")
        self.assertEqual(st, 200)
        d = json.loads(body)
        self.assertFalse(d["ok"])
        self.assertEqual(d["state"], "engine_already_up")

    def test_page_renders_live_section_and_declared_states(self):
        st, body, _ = _get(self.base, "/")
        self.assertEqual(st, 200)
        html = body.decode("utf-8")
        self.assertNotIn("<!--LIVE_ENGINE-->", html)     # replaced, not leaked
        self.assertIn("LIVE ENGINE", html)
        self.assertIn('id="liveStart"', html)
        self.assertIn('id="liveStop"', html)
        self.assertIn('id="liveIngest"', html)
        self.assertIn('id="liveFrame"', html)
        self.assertIn('id="liveStateText"', html)
        self.assertIn("UP_NOT_OURS", html)               # declared states
        self.assertIn("UP+INGESTED", html)
        self.assertIn("FALSIFIER", html)
        self.assertIn("an UPLOAD, not", html)            # the W2 law copy
        self.assertIn("zero physics claims", html)
        self.assertIn("never leaves play mode", html)

    def test_live_js_parses_as_javascript(self):
        import shutil as _sh
        node = _sh.which("node")
        if not node:
            self.skipTest("node not on PATH")
        from tools.product_viewer.tests.test_page_script import js_parses
        ok, detail = js_parses(LIVE_JS)
        self.assertTrue(ok, f"LIVE_JS fails new Function parse: {detail}")


class SingleSurfaceIdiom(unittest.TestCase):
    """A handler WITHOUT the live surface answers honestly (the PR #287/#290
    single-surface idiom); the page keeps its placeholder."""

    def _handler(self):
        engine = pv.EngineClient("http://127.0.0.1:1")
        return type("BareHandler", (pv.ViewerHandler,), {
            "engine": engine,
            "ring": pv.RingBuffer(4),
            "camera": pv.CameraPanel(engine),
            "started": 0.0,
            "capture_thread": None,
            "mirror": pv.EngineWindowMirror("http://127.0.0.1:1", 1),
        })

    def test_live_routes_answer_without_surface(self):
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), self._handler())
        httpd.daemon_threads = True
        port = httpd.server_address[1]
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
        try:
            st, body, _ = _get(f"http://127.0.0.1:{port}", "/api/live/engine")
            self.assertEqual(st, 502)
            self.assertIn("live engine surface not configured",
                          json.loads(body)["error"])
            st, body = _post(f"http://127.0.0.1:{port}", "/api/live/engine/start")
            self.assertEqual(st, 502)
            self.assertIn("live engine surface not configured",
                          json.loads(body)["error"])
            st, body, _ = _get(f"http://127.0.0.1:{port}", "/")
            self.assertEqual(st, 200)
            self.assertIn("<!--LIVE_ENGINE-->", body.decode("utf-8"))
        finally:
            httpd.shutdown()

    def test_live_section_none_is_honest(self):
        html = live_section(None)
        self.assertIn("not configured", html)
        self.assertIn("LIVE ENGINE", html)


# ---------------------------------------------------------------------------
# THE FALSIFIER, contract level: a dying engine must flip the pane honestly.
# (The REAL kill is measured by EngineUpIntegration below.)
# ---------------------------------------------------------------------------


class DownFlipContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stub, cls.url, cls.thread = _start_stub()
        engine = pv.EngineClient(cls.url)
        handler = type("BoundHandler", (pv.ViewerHandler,), {
            "engine": engine,
            "ring": pv.RingBuffer(4),
            "camera": pv.CameraPanel(engine),
            "started": 0.0,
            "capture_thread": None,
            "mirror": pv.EngineWindowMirror(cls.url, 1),
            "live": LiveEngineSupervisor(engine, cls.url),
        })
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.httpd.daemon_threads = True
        cls.port = cls.httpd.server_address[1]
        t = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        t.start()
        cls.base = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

    def test_engine_death_flips_every_surface_within_bound(self):
        self.assertEqual(json.loads(_get(self.base, "/api/live/engine")[1])["engine_up"],
                         True)
        t0 = time.monotonic()
        self.stub.shutdown()                       # THE ENGINE DIES
        deadline = t0 + pv.LIVE_DOWN_FLIP_BOUND_S
        flip_s = None
        while time.monotonic() < deadline:
            d = json.loads(_get(self.base, "/api/live/engine")[1])
            if d["engine_up"] is False:
                flip_s = time.monotonic() - t0
                break
            time.sleep(0.05)
        self.assertIsNotNone(
            flip_s, f"pane did not flip to DOWN within {pv.LIVE_DOWN_FLIP_BOUND_S}s")
        st, body, _ = _get(self.base, "/api/live/state")
        self.assertEqual(st, 502)
        self.assertFalse(json.loads(body)["ok"])     # NAMED transport refusal
        st, body, _ = _get(self.base, "/api/live/frame")
        self.assertEqual(st, 502)
        d = json.loads(body)
        self.assertFalse(d["ok"])
        self.assertIn("GET /frame", d["error"])


# ---------------------------------------------------------------------------
# THE REAL THING (gated): the engine-up battery, driven by
# live_engine_battery.py, which builds the engine with the W2 recipe and sets
# CHIMERA_LIVE_ENGINE_EXE / CHIMERA_LIVE_TILE_PATH / CHIMERA_LIVE_BODY_PATH.
# ---------------------------------------------------------------------------


@unittest.skipUnless(os.environ.get("CHIMERA_LIVE_ENGINE_EXE"),
                     "real engine not built (run live_engine_battery.py)")
class EngineUpIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        exe = os.environ["CHIMERA_LIVE_ENGINE_EXE"]
        tile = os.environ.get("CHIMERA_LIVE_TILE_PATH")
        body = os.environ.get("CHIMERA_LIVE_BODY_PATH")
        if tile and not Path(tile).is_file():
            raise unittest.SkipTest(f"tile payload missing: {tile}")
        if body and not Path(body).is_file():
            raise unittest.SkipTest(f"body payload missing: {body}")
        cls.engine_port = _free_port()
        cls.engine_url = f"http://127.0.0.1:{cls.engine_port}"
        cls.httpd = pv.make_server(cls.engine_url, 0, history=8,
                                   live_engine_exe=exe, ingest_tile=tile,
                                   ingest_body=body)
        cls.port = cls.httpd.server_address[1]
        cls.base = f"http://127.0.0.1:{cls.port}"
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.sup = cls.httpd.RequestHandlerClass.live
        cls.out_dir = Path(os.environ.get("CHIMERA_OUTPUT_DIR") or Path.cwd())

    @classmethod
    def tearDownClass(cls):
        try:
            if cls.sup.proc is not None and cls.sup.proc.poll() is None:
                cls.sup.proc.kill()
                cls.sup.proc.wait(timeout=15)
        finally:
            cls.httpd.shutdown()

    def _artifact(self, name: str, data) -> None:
        try:
            (self.out_dir / name).write_bytes(
                data if isinstance(data, bytes) else data.encode("utf-8"))
        except OSError:
            pass

    def test_01_start_real_engine(self):
        st, body = _post(self.base, "/api/live/engine/start", timeout=180)
        d = json.loads(body)
        self._artifact("live_start_result.json", body)
        self.assertEqual(st, 200)
        self.assertTrue(d["ok"], d)
        self.assertEqual(d["state"], "up")
        self.assertTrue(self.sup.up())
        st, body, _ = _get(self.base, "/api/live/state")
        d = json.loads(body)
        self.assertTrue(d["ok"])
        # fresh boot under --no-restore: the W2 pre-state (n=0, overlay none)
        self.assertEqual(d["debug"], {"n": 0, "active": True, "vp_valid": True})

    def test_02_ingest_proven_payloads(self):
        st, body = _post(self.base, "/api/live/engine/ingest", timeout=180)
        d = json.loads(body)
        self._artifact("live_ingest_result.json", body)
        self.assertEqual(st, 200)
        self.assertTrue(d["ok"], d)
        self.assertEqual(d["state"], "ingested")
        # the engine's own words, verbatim (W2 acceptance channel 1)
        self.assertEqual(d["tile"]["http"], 200)
        self.assertEqual(d["tile"]["engine_response"]["verbatim"], '{"ok":true}')
        self.assertEqual(d["body"]["http"], 200)
        self.assertEqual(d["body"]["engine_response"]["verbatim"], '{"ok":true}')
        # W2 acceptance channels 3+2: /debug n==60000, /scene overlay loaded
        self.assertEqual(d["debug_after"]["n"], 60000)
        overlay = next(row for row in d["scene_after"]["rows"]
                       if row["id"] == "overlay")
        self.assertEqual(overlay["state"], 1)
        self.assertEqual(overlay["detail"], "loaded")
        self._artifact("live_engine_status_after_ingest.json",
                       json.dumps(self.sup.status(), indent=1))

    def test_03_engine_pixels_and_state(self):
        t0 = time.monotonic()
        st, png, ctype = _get(self.base, "/api/live/frame", timeout=120)
        self.assertEqual(st, 200)
        self.assertEqual(ctype, "image/png")
        self.assertTrue(png.startswith(b"\x89PNG"))
        self._artifact("live_frame_after_ingest.png", png)
        st, body, _ = _get(self.base, "/api/live/state", timeout=60)
        d = json.loads(body)
        self.assertTrue(d["ok"])
        self.assertIn("NOT pixels", d["state_kind"])
        self._artifact("live_pixels_and_state.json", json.dumps(
            {"frame_png_bytes": len(png),
             "frame_png_sha256": hashlib.sha256(png).hexdigest(),
             "frame_fetch_s": round(time.monotonic() - t0, 2),
             "state_kind": d["state_kind"], "debug": d["debug"]}, indent=1))
        # NOTE (the W2 law): the PNG's CONTENT is not judged here — this
        # worker is text-only; the pinned artifact awaits Sergeant review.

    def test_04_kill_flips_pane_down_within_bound(self):
        # THE FALSIFIER, measured: kill the engine; every live surface must
        # answer with a named down-state within the declared bound.
        # NOTE: the engine's stdout is NOT a gating observable here — the CRT
        # fully buffers a non-console stdout and TerminateProcess discards the
        # buffer (measured: empty tail in battery job b8324ae722054bfdab4fea
        # 9455e87bdf). Acceptance rests on the OBSERVABLE channels this class
        # already pinned: the engine's verbatim {"ok":true} responses, the
        # /scene overlay flip, /debug n==60000, and the /frame PNG bytes. The
        # supervisor keeps the stdout tail as diagnostic data only.
        self.assertIsNotNone(self.sup.proc)
        pid = self.sup.proc.pid
        t0 = time.monotonic()
        self.sup.proc.kill()
        self.sup.proc.wait(timeout=15)
        deadline = t0 + pv.LIVE_DOWN_FLIP_BOUND_S
        flip_s = None
        while time.monotonic() < deadline:
            d = json.loads(_get(self.base, "/api/live/engine")[1])
            if d["engine_up"] is False:
                flip_s = time.monotonic() - t0
                break
            time.sleep(0.05)
        self.assertIsNotNone(flip_s, "engine_up stayed true after kill")
        self.assertLessEqual(flip_s, pv.LIVE_DOWN_FLIP_BOUND_S)
        st, body, _ = _get(self.base, "/api/live/frame", timeout=60)
        self.assertEqual(st, 502)
        self.assertIn("GET /frame", json.loads(body)["error"])
        st, body, _ = _get(self.base, "/api/live/state", timeout=60)
        self.assertEqual(st, 502)
        self._artifact("live_kill_flip.json", json.dumps(
            {"killed_pid": pid, "flip_s": round(flip_s, 3),
             "bound_s": pv.LIVE_DOWN_FLIP_BOUND_S}, indent=1))

    def test_05_stop_route_on_fresh_start(self):
        st, body = _post(self.base, "/api/live/engine/start", timeout=180)
        self.assertTrue(json.loads(body)["ok"], body)
        st, body = _post(self.base, "/api/live/engine/stop", timeout=60)
        d = json.loads(body)
        self._artifact("live_stop_result.json", body)
        self.assertEqual(st, 200)
        self.assertTrue(d["ok"], d)
        self.assertEqual(d["state"], "stopped")
        self.assertFalse(d["engine_up_after"])
        s = self.sup.status()
        self.assertFalse(s["viewer_started"]["alive"])
        self.assertFalse(s["engine_up"])


if __name__ == "__main__":
    unittest.main()
