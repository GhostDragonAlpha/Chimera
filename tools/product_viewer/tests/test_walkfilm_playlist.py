"""The walkfilm playlist: sealed-frame manifest, routes, page wiring.

wk-liveviewer-d02 (viewer lane) 2026-09-30. The 202-frame sealed W03 walk
becomes browsable: a sha-pinned playlist (tick -> frame) served byte-exact
from disk after sha256 verification - with named refusals for anything
missing or mutated. SEALED CAPTURE REPLAY ONLY: a client-side cycler over
the frames; zero engine work, zero physics claims, the sealed trace strictly
read-only.

Contract pinned here:
- a frame is served ONLY when file exists AND sha256 AND size match the pin;
- the sha is RE-VERIFIED AT SERVE TIME (a file mutated after load is
  refused with a named 502, not served);
- a refused frame is NAMED in the page section and in /api/world/walkfilm,
  never silently dropped; unknown names are 404;
- served bytes equal the pinned file bytes (no re-encode);
- the PAGE keeps its WALKFILM_PLAYLIST placeholder so server-side injection
  cannot silently break, and the cycler script parses as JavaScript;
- the playlist binds to the SEALED lineage: trace sha prefix, world-buffer
  pin, stride-3 tick grid 0..300 (101 ticks x 2 shots = 202 frames);
- the play-mode law is declared: play/pause/scrub are LOCAL UI controls
  that never touch the engine and never change any mode.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from tools.product_viewer import server as pv
from tools.product_viewer.server import (PAGE, WALKFILM_JS, load_walkfilm_playlist,
                                         walkfilm_section)

MANIFEST = pv.WALKFILM_PLAYLIST_PATH


def _write_png(path: Path, blob: bytes) -> str:
    path.write_bytes(blob)
    return hashlib.sha256(blob).hexdigest()


class PlaylistContract(unittest.TestCase):
    """Self-contained contract tests (temp manifest + temp PNGs, any host)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="viewer_wf_"))
        self.good = self.tmp / "f0000.png"
        sha = _write_png(self.good, b"\x89PNG-fake-frame-bytes")
        self.bad = self.tmp / "f0001.png"
        _write_png(self.bad, b"\x89PNG-tampered-frame")
        self.manifest = self.tmp / "walkfilm_playlist.json"
        self.manifest.write_text(json.dumps({
            "schema": "chimera.viewer.walkfilm_playlist.v1",
            "declared_limits": ["SEALED CAPTURE REPLAY - not live pixels",
                                "play/pause/scrub are LOCAL UI controls"],
            "pins": {"trace_sha256_file": "b47b709c" + "0" * 56},
            "counts": {"frames": 3},
            "frames": [
                {"name": "wf_f0000", "frame": 0, "tick": 0, "shot": "track",
                 "file": str(self.good), "sha256": sha,
                 "bytes": self.good.stat().st_size,
                 "buffer_sha256": "7e10b555" + "0" * 56},
                {"name": "wf_f0001", "frame": 1, "tick": 3, "shot": "track",
                 "file": str(self.bad), "sha256": "0" * 64,
                 "bytes": self.bad.stat().st_size,
                 "buffer_sha256": "0" * 64},
                {"name": "wf_f0002", "frame": 2, "tick": 6, "shot": "track",
                 "file": str(self.tmp / "nope.png"), "sha256": "1" * 64,
                 "bytes": 1, "buffer_sha256": "1" * 64},
            ],
        }), encoding="utf-8")
        self.pl = load_walkfilm_playlist(self.manifest)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_verified_frame_passes_pins(self):
        e = self.pl["frames"][0]
        self.assertTrue(e["verified"], e["refusal"])
        self.assertIsNone(e["refusal"])

    def test_mutated_frame_refused_by_name(self):
        e = self.pl["frames"][1]
        self.assertFalse(e["verified"])
        self.assertIn("sha256 mismatch", e["refusal"])

    def test_missing_frame_refused_by_name(self):
        e = self.pl["frames"][2]
        self.assertFalse(e["verified"])
        self.assertEqual("file missing", e["refusal"])

    def test_unreadable_manifest_is_honest_not_fatal(self):
        pl = load_walkfilm_playlist(self.tmp / "absent.json")
        self.assertFalse(pl["loaded"])
        self.assertIn("unreadable", pl["refusal"])
        self.assertIn("not loaded", walkfilm_section(pl))

    def test_section_names_refusals_and_declares_controls(self):
        html = walkfilm_section(self.pl)
        self.assertIn("SEALED CAPTURE REPLAY", html)
        self.assertIn("wf_f0001: NOT SERVED", html)
        self.assertIn("sha256 mismatch", html)
        self.assertIn("wf_f0002: NOT SERVED", html)
        self.assertIn("file missing", html)
        self.assertIn('id="wfplay"', html)
        self.assertIn('id="wfscrub"', html)
        self.assertIn("never leaves play mode", html)
        self.assertIn("LOCAL UI CONTROLS", html)

    def test_page_keeps_injection_placeholder(self):
        self.assertIn("<!--WALKFILM_PLAYLIST-->", PAGE)


class PlaylistRoutes(unittest.TestCase):
    """Live server routes against a temp playlist (no engine, any host)."""

    @classmethod
    def setUpClass(cls):
        tmp = Path(tempfile.mkdtemp(prefix="viewer_wf_routes_"))
        cls._tmp = tmp
        png = tmp / "f0000.png"
        sha = _write_png(png, b"\x89PNG-route-frame-bytes")
        manifest = tmp / "walkfilm_playlist.json"
        manifest.write_text(json.dumps({
            "schema": "chimera.viewer.walkfilm_playlist.v1",
            "declared_limits": [], "pins": {}, "counts": {"frames": 1},
            "frames": [{"name": "wf_f0000", "frame": 0, "tick": 0,
                        "shot": "track", "file": str(png), "sha256": sha,
                        "bytes": png.stat().st_size,
                        "buffer_sha256": "7e10b555" + "0" * 56}],
        }), encoding="utf-8")
        engine = pv.EngineClient("http://127.0.0.1:1")   # deliberately dead
        handler = type("BoundHandler", (pv.ViewerHandler,), {
            "engine": engine,
            "ring": pv.RingBuffer(4),
            "camera": pv.CameraPanel(engine),
            "started": 0.0,
            "capture_thread": None,
            "mirror": pv.EngineWindowMirror("http://127.0.0.1:1", 1),
            "walkfilm": load_walkfilm_playlist(manifest),
        })
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.httpd.daemon_threads = True
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def _get(self, path: str):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{self.port}{path}",
                                        timeout=10) as r:
                return r.status, r.read(), r.headers.get("Content-Type", "")
        except urllib.error.HTTPError as e:
            return e.code, e.read(), e.headers.get("Content-Type", "")

    def test_json_route_lists_frames_with_verification(self):
        st, body, _ = self._get("/api/world/walkfilm")
        self.assertEqual(st, 200)
        d = json.loads(body)
        self.assertTrue(d["ok"])
        self.assertEqual(d["schema"], "chimera.viewer.walkfilm_playlist.v1")
        self.assertEqual(len(d["frames"]), 1)
        self.assertTrue(d["frames"][0]["verified"])
        self.assertEqual(d["frames"][0]["tick"], 0)

    def test_frame_route_serves_pinned_bytes_exactly(self):
        st, body, ctype = self._get("/api/world/walkfilm/frame?name=wf_f0000")
        self.assertEqual(st, 200)
        self.assertEqual(ctype, "image/png")
        self.assertEqual(body, (self._tmp / "f0000.png").read_bytes())

    def test_unknown_name_is_404(self):
        st, body, _ = self._get("/api/world/walkfilm/frame?name=wf_f9999")
        self.assertEqual(st, 404)
        self.assertIn("unknown walkfilm frame", json.loads(body)["error"])

    def test_serve_time_mutation_is_refused_by_name(self):
        # Tamper AFTER load: the serve-time re-verification must catch it.
        png = self._tmp / "f0000.png"
        original = png.read_bytes()
        try:
            png.write_bytes(original + b"tampered-after-load")
            st, body, _ = self._get("/api/world/walkfilm/frame?name=wf_f0000")
            self.assertEqual(st, 502)
            self.assertIn("sha256 mismatch at serve time",
                          json.loads(body)["error"])
        finally:
            png.write_bytes(original)

    def test_served_page_contains_section_and_cycler(self):
        st, body, ctype = self._get("/")
        self.assertEqual(st, 200)
        self.assertIn("text/html", ctype)
        html = body.decode("utf-8")
        self.assertNotIn("<!--WALKFILM_PLAYLIST-->", html)  # replaced, not leaked
        self.assertIn('id="wfimg"', html)
        self.assertIn("/api/world/walkfilm", html)
        self.assertIn("SEALED CAPTURE REPLAY", html)
        # every <script> block of the SERVED page (main + cycler) must be
        # non-empty; the real JS-engine parse is pinned in ParseGate below.
        scripts = re.findall(r"<script>(.*?)</script>", html, re.S)
        self.assertGreaterEqual(len(scripts), 2)


@unittest.skipUnless(shutil.which("node"), "node not on PATH")
class ParseGate(unittest.TestCase):
    """The injected cycler script must parse under the same V8 gate as the
    PAGE template (audit lesson: a script that fails at parse silently kills
    every feature it carries)."""

    def test_cycler_script_parses(self):
        from tools.product_viewer.tests.test_page_script import js_parses
        ok, detail = js_parses(WALKFILM_JS)
        self.assertTrue(ok, f"cycler script fails new Function parse: {detail}")

    def test_parse_gate_can_fail(self):
        from tools.product_viewer.tests.test_page_script import js_parses
        ok, detail = js_parses("next();\n}")
        self.assertFalse(ok)
        self.assertIn("SyntaxError", detail)


class HostPlaylist(unittest.TestCase):
    """The committed playlist on THIS campaign host: everything verifies and
    the sealed lineage is exactly the declared one."""

    @unittest.skipUnless(MANIFEST.is_file(), "walkfilm_playlist.json not committed")
    def test_sealed_lineage_and_full_verification(self):
        pl = load_walkfilm_playlist()
        self.assertTrue(pl["loaded"], pl.get("refusal"))
        frames = pl["frames"]
        self.assertEqual(len(frames), 202)
        refused = [(e["name"], e["refusal"]) for e in frames if not e["verified"]]
        self.assertEqual(refused, [], f"unverified frames: {refused}")
        # tick grid: stride 3, 0..300, each tick exactly twice (track+approach)
        ticks = [e["tick"] for e in frames]
        self.assertEqual(sorted(set(ticks)), list(range(0, 301, 3)))
        for t in set(ticks):
            self.assertEqual(ticks.count(t), 2, f"tick {t} not sampled twice")
        shots = {e["shot"] for e in frames}
        self.assertEqual(shots, {"track", "approach"})
        names = [e["name"] for e in frames]
        self.assertEqual(len(set(names)), 202)
        self.assertEqual(names[0], "wf_f0000")
        self.assertEqual(names[-1], "wf_f0201")
        # sealed pins
        pins = pl["pins"]
        self.assertTrue(str(pins.get("trace_sha256_file", "")).startswith("b47b709c"))
        self.assertTrue(str(pins.get("world_with_monkey_sha256_array_bytes", "")
                            ).startswith("16a978f8"))
        bufs = {e["buffer_sha256"] for e in frames}
        self.assertEqual(len(bufs), 101)   # 101 unique buffers shared across shots
        self.assertTrue(frames[0]["buffer_sha256"].startswith("7e10b555"))
        self.assertTrue(frames[-1]["buffer_sha256"].startswith("ef720dea"))
        # limits + play-mode law shipped in the manifest
        self.assertTrue(pl["declared_limits"])
        joined = " ".join(pl["declared_limits"])
        self.assertIn("never leaves play mode", joined)
        self.assertIn("NOT interactive control", joined)

    @unittest.skipUnless(MANIFEST.is_file(), "walkfilm_playlist.json not committed")
    def test_section_renders_all_verified(self):
        html = walkfilm_section(load_walkfilm_playlist())
        self.assertIn("all 202 frames sha-verified", html)
        self.assertNotIn("NOT SERVED", html)


if __name__ == "__main__":
    unittest.main()
