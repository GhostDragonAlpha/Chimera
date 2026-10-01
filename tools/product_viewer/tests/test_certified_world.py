"""The certified-world sealed-capture surface: manifest, routes, page wiring.

wk-liveviewer-d01 (viewer lane) 2026-09-30. The viewer's honest increment
toward "monkey visible in the forest world": a sha-pinned gallery of SEALED
captures (certified walk states in the certified world buffer) served
byte-exact from disk after sha256 verification - with named refusals for
anything missing or mutated, and a buffer-only honesty twin kept separate
from overlay-augmented stills.

Contract pinned here:
- an entry is served ONLY when file exists AND sha256 AND size match the pin;
- a refused entry is NAMED in the page section and in /api/world/certified,
  never silently dropped;
- unknown names are 404; the PAGE keeps its CERTIFIED_WORLD placeholder so
  server-side injection cannot silently break;
- served bytes equal the pinned file bytes (no re-encode, engine-passthrough
  law extended to sealed captures).
"""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from tools.product_viewer import server as pv
from tools.product_viewer.server import (PAGE, certified_world_section,
                                         load_certified_world)

MANIFEST = pv.CERTIFIED_MANIFEST_PATH


def _write_png(path: Path, blob: bytes) -> str:
    path.write_bytes(blob)
    return hashlib.sha256(blob).hexdigest()


class CertifiedWorldContract(unittest.TestCase):
    """Self-contained contract tests (temp manifest + temp PNGs, any host)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="viewer_cert_"))
        self.good = self.tmp / "good.png"
        sha = _write_png(self.good, b"\x89PNG-fake-bytes-for-contract-test")
        self.bad = self.tmp / "bad.png"
        _write_png(self.bad, b"\x89PNG-tampered-bytes")
        self.manifest = self.tmp / "certified_world.json"
        self.manifest.write_text(json.dumps({
            "schema": "chimera.viewer.certified_world.v1",
            "declared_limits": ["test limit"],
            "entries": [
                {"name": "ok_capture", "file": str(self.good),
                 "sha256": sha, "bytes": self.good.stat().st_size,
                 "caption": "verified entry", "identity_note": "pin"},
                {"name": "mutated_capture", "file": str(self.bad),
                 "sha256": "0" * 64, "bytes": self.bad.stat().st_size,
                 "caption": "tampered entry"},
                {"name": "missing_capture", "file": str(self.tmp / "nope.png"),
                 "sha256": "1" * 64, "bytes": 1,
                 "caption": "absent entry"},
            ],
        }), encoding="utf-8")
        self.world = load_certified_world(self.manifest)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_verified_entry_passes_pins(self):
        e = self.world["entries"][0]
        self.assertTrue(e["verified"], e["refusal"])
        self.assertIsNone(e["refusal"])

    def test_mutated_entry_refused_by_name(self):
        e = self.world["entries"][1]
        self.assertFalse(e["verified"])
        self.assertIn("sha256 mismatch", e["refusal"])

    def test_missing_entry_refused_by_name(self):
        e = self.world["entries"][2]
        self.assertFalse(e["verified"])
        self.assertEqual("file missing", e["refusal"])

    def test_unreadable_manifest_is_honest_not_fatal(self):
        w = load_certified_world(self.tmp / "absent.json")
        self.assertFalse(w["loaded"])
        self.assertIn("unreadable", w["refusal"])
        self.assertEqual(certified_world_section(w),
                         certified_world_section(w))  # deterministic
        self.assertIn("not loaded", certified_world_section(w))

    def test_section_renders_verified_and_refused(self):
        html = certified_world_section(self.world)
        self.assertIn("SEALED CAPTURES", html)
        self.assertIn("/api/world/certified/frame?name=ok_capture", html)
        self.assertIn("NOT SERVED", html)
        self.assertIn("sha256 mismatch", html)
        self.assertIn("file missing", html)
        self.assertIn("test limit", html)

    def test_page_keeps_injection_placeholder(self):
        self.assertIn("<!--CERTIFIED_WORLD-->", PAGE)


class CertifiedWorldRoutes(unittest.TestCase):
    """Live server routes against a temp manifest (no engine, any host)."""

    @classmethod
    def setUpClass(cls):
        tmp = Path(tempfile.mkdtemp(prefix="viewer_routes_"))
        cls._tmp = tmp
        png = tmp / "frame.png"
        sha = _write_png(png, b"\x89PNG-route-test-bytes")
        manifest = tmp / "certified_world.json"
        manifest.write_text(json.dumps({
            "schema": "chimera.viewer.certified_world.v1",
            "declared_limits": [],
            "entries": [{"name": "route_capture", "file": str(png),
                         "sha256": sha, "bytes": png.stat().st_size,
                         "caption": "route entry",
                         "disclosure": "Known render anomaly (route-test copy): "
                                       "disclosed, not re-authored."}],
        }), encoding="utf-8")
        engine = pv.EngineClient("http://127.0.0.1:1")   # deliberately dead
        handler = type("BoundHandler", (pv.ViewerHandler,), {
            "engine": engine,
            "ring": pv.RingBuffer(4),
            "camera": pv.CameraPanel(engine),
            "started": 0.0,
            "capture_thread": None,
            "mirror": pv.EngineWindowMirror("http://127.0.0.1:1", 1),
            "world": load_certified_world(manifest),
        })
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.httpd.daemon_threads = True
        cls.port = cls.httpd.server_address[1]
        import threading
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

    def test_json_route_lists_entry_with_verification(self):
        st, body, _ = self._get("/api/world/certified")
        self.assertEqual(st, 200)
        d = json.loads(body)
        self.assertTrue(d["ok"])
        self.assertEqual(d["schema"], "chimera.viewer.certified_world.v1")
        self.assertEqual(len(d["entries"]), 1)
        self.assertTrue(d["entries"][0]["verified"])

    def test_route_projects_disclosure_field(self):
        """PR #291 review fix: the disclosure is part of the certified-world
        honest state, so the /api/world/certified projection must carry it
        (the original fixed key tuple omitted it; doc claimed otherwise)."""
        st, body, _ = self._get("/api/world/certified")
        self.assertEqual(st, 200)
        entry = json.loads(body)["entries"][0]
        self.assertIn("disclosure", entry)
        self.assertEqual(entry["disclosure"],
                         "Known render anomaly (route-test copy): "
                         "disclosed, not re-authored.")

    def test_frame_route_serves_pinned_bytes_exactly(self):
        st, body, ctype = self._get("/api/world/certified/frame?name=route_capture")
        self.assertEqual(st, 200)
        self.assertEqual(ctype, "image/png")
        self.assertEqual(body, (self._tmp / "frame.png").read_bytes())

    def test_unknown_name_is_404(self):
        st, body, _ = self._get("/api/world/certified/frame?name=nope")
        self.assertEqual(st, 404)
        self.assertIn("unknown certified capture", json.loads(body)["error"])

    def test_served_page_contains_section_and_img(self):
        st, body, ctype = self._get("/")
        self.assertEqual(st, 200)
        self.assertIn("text/html", ctype)
        html = body.decode("utf-8")
        self.assertNotIn("<!--CERTIFIED_WORLD-->", html)   # replaced, not leaked
        self.assertIn("/api/world/certified/frame?name=route_capture", html)
        self.assertIn("SEALED CAPTURES", html)


class ServeTimeGuard(unittest.TestCase):
    """Serving-state guard (PR #287 round 2): the load-time pins do NOT
    transfer to serve time. A pinned file deleted or MUTATED after startup
    must yield a NAMED 502 JSON refusal - the connection must ANSWER, never
    a raw disconnect (the round-1 defect: FileNotFoundError escaped
    do_GET, which catches only EngineError, and killed the request thread).
    """

    @classmethod
    def setUpClass(cls):
        tmp = Path(tempfile.mkdtemp(prefix="viewer_servetime_"))
        cls._tmp = tmp
        cls.vanish = tmp / "vanish.png"
        cls.mutate = tmp / "mutate.png"
        entries = []
        for name, p in (("vanish_me", cls.vanish), ("mutate_me", cls.mutate)):
            sha = _write_png(p, b"\x89PNG-servetime-" + name.encode())
            entries.append({"name": name, "file": str(p), "sha256": sha,
                            "bytes": p.stat().st_size, "caption": name})
        manifest = tmp / "certified_world.json"
        manifest.write_text(json.dumps({
            "schema": "chimera.viewer.certified_world.v1",
            "declared_limits": [], "entries": entries,
        }), encoding="utf-8")
        engine = pv.EngineClient("http://127.0.0.1:1")   # deliberately dead
        handler = type("BoundHandler", (pv.ViewerHandler,), {
            "engine": engine,
            "ring": pv.RingBuffer(4),
            "camera": pv.CameraPanel(engine),
            "started": 0.0,
            "capture_thread": None,
            "mirror": pv.EngineWindowMirror("http://127.0.0.1:1", 1),
            # sergeant lesson: pass the manifest path EXPLICITLY (the
            # load-time default argument bound at def time)
            "world": load_certified_world(manifest),
        })
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.httpd.daemon_threads = True
        cls.port = cls.httpd.server_address[1]
        import threading
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

    def test_deleted_after_startup_named_502_not_disconnect(self):
        # serving state: entry verified at startup, file then DELETED
        self.vanish.unlink()
        st, body, ctype = self._get("/api/world/certified/frame?name=vanish_me")
        self.assertEqual(st, 502)          # ANSWERED: no RemoteDisconnected
        self.assertIn("application/json", ctype)
        d = json.loads(body)
        self.assertFalse(d["ok"])
        self.assertIn("unreadable at serve time", d["error"])

    def test_mutated_after_startup_named_502(self):
        # serving state: file OVERWRITTEN with different bytes after startup
        self.mutate.write_bytes(b"\x89PNG-mutated-after-startup")
        st, body, ctype = self._get("/api/world/certified/frame?name=mutate_me")
        self.assertEqual(st, 502)
        self.assertIn("application/json", ctype)
        d = json.loads(body)
        self.assertFalse(d["ok"])
        self.assertIn("sha256 mismatch at serve time", d["error"])


class HostManifest(unittest.TestCase):
    """The committed manifest on THIS campaign host: everything verifies."""

    @unittest.skipUnless(MANIFEST.is_file(), "certified_world.json not committed")
    def test_all_entries_verify(self):
        w = load_certified_world()
        self.assertTrue(w["loaded"], w.get("refusal"))
        self.assertEqual(len(w["entries"]), 11)
        refused = [(e["name"], e["refusal"]) for e in w["entries"] if not e["verified"]]
        self.assertEqual(refused, [], f"unverified entries: {refused}")


class SingleResponseChain(unittest.TestCase):
    """Exactly ONE response per request (sgt-review-287b finding).

    do_GET carried TWO route chains: the second began with a bare
    `if path == "/graph"`, so every request answered by the FIRST chain fell
    through into the second chain's terminal else and attempted an
    unsolicited second 404 send. Client-invisible under HTTP/1.0 (one
    request per connection), but it cost one swallowed socketserver
    ConnectionAbortedError [WinError 10053] traceback per first-chain
    request on Windows. Pinned here deterministically: a stubbed _send must
    record exactly ONE call for a first-chain route (/api/world/certified),
    for the page route (/), and for the terminal unknown-route else alike.
    """

    def _sends_for(self, path):
        handler = type("SingleResponseHandler", (pv.ViewerHandler,), {
            "world": {"schema": "chimera.viewer.certified_world.v1",
                      "manifest": "test", "loaded": True,
                      "declared_limits": [], "entries": []},
        })
        h = handler.__new__(handler)
        calls = []
        h._send = lambda code, body, ctype: calls.append(code)  # stubbed
        h.path = path
        h.do_GET()
        return calls

    def test_exactly_one_response_per_request(self):
        # first-chain routes: one response, NO unsolicited second 404 send
        self.assertEqual(self._sends_for("/api/world/certified"), [200])
        self.assertEqual(self._sends_for("/"), [200])
        # the second chain's own terminal else stays a single response too
        self.assertEqual(self._sends_for("/nope"), [404])


if __name__ == "__main__":
    unittest.main()
