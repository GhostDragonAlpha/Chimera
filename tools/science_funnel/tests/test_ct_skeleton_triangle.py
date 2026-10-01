"""test_ct_skeleton_triangle.py -- the Defect A conformance gate (lane
agent/triangle-monkey-grid-20260920).

THE GATE: the monkey scene's visual path must compose MESH geometry through
the engine's triangle pipeline (/mesh_bin) and must NEVER post the skeleton as
a splat buffer (/membrane_bin). The divergence (the monkey rendered as a splat
cloud) cannot silently return: these tests drive the REAL compose + render
path against a local recorder HTTP server and inspect the wire.

Rule 0 receipt: tools/science_funnel/validation/triangle_monkey_20260920/receipt.json
Run (both sys.path roots):
  python -B -m unittest tools.science_funnel.tests.test_ct_skeleton_triangle -v
"""
from __future__ import annotations

import json
import sys
import threading
import unittest
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

ROOT = Path(__file__).resolve().parents[2]

# a deterministic 64x48 gray PNG the recorder serves for /frame (x264 needs
# even dimensions >= 2 when the movie runner encodes)
import io as _io
from PIL import Image as _Image
_buf = _io.BytesIO()
_Image.new("RGB", (64, 48), (40, 40, 40)).save(_buf, format="PNG")
_PNG_64X48 = _buf.getvalue()


class _Recorder(BaseHTTPRequestHandler):
    """Records every (path, body-length) hit; serves engine-shaped answers."""

    hits: list = []

    def log_message(self, *a):  # silence
        pass

    def _answer(self, body: bytes, ctype: str):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n)
        type(self).hits.append({"path": self.path, "bytes": len(body)})
        if self.path == "/mesh_bin":
            ok = b'{"ok":true}'
        elif self.path == "/camera":
            ok = b'{"ok":true}'
        elif self.path.startswith("/membrane"):
            ok = b'{"ok":true}'
        else:
            ok = b'{"ok":true}'
        self._answer(ok, "application/json")

    def do_GET(self):
        type(self).hits.append({"path": self.path, "bytes": 0})
        if self.path.startswith("/frame"):
            self._answer(_PNG_64X48, "image/png")
        else:
            self._answer(b"{}", "application/json")


class ConformanceGate(unittest.TestCase):
    """A-conformance: the monkey scene composes the TRIANGLE technique."""

    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _Recorder)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_01_triangle_layer_composes_indexed_mesh(self):
        """The compose emits real indexed triangle geometry for all 25 bones."""
        from tools.science_funnel import ct_skeleton_triangle as cst
        layer = cst.layer_triangle_mesh()
        v9, tris = layer["verts9"], layer["tris"]
        self.assertEqual(v9.shape[1], 9)                 # pos3+normal3+color3
        self.assertTrue(np.isfinite(v9).all())
        self.assertEqual(tris.size % 3, 0)
        self.assertGreater(tris.size // 3, 500_000)      # the 25 committed previews
        self.assertEqual(int(tris.max()), v9.shape[0] - 1)  # indices in range
        self.assertEqual(layer["record"]["bones"], 25)

    def test_02_registration_is_shared_with_the_splat_layer(self):
        """One mount, two presentations: the triangle layer reuses the pinned
        registration (the same scale the splat layer derived)."""
        from tools.science_funnel import ct_skeleton_triangle as cst
        from tools.science_funnel import ct_skeleton_layer as csl
        layer = cst.layer_triangle_mesh()
        scale_mesh = layer["record"]["scale_scene_per_mm"]
        buf, rec = csl.layer_splat_buffer(3)
        self.assertEqual(scale_mesh, rec["scale_scene_per_mm"])

    def test_03_movie_default_renders_mesh_and_never_posts_membrane_bin(self):
        """THE GATE: skeleton_movie.main() with the DEFAULT --render (mesh)
        must hit /mesh_bin + /camera + /frame and NEVER hit /membrane_bin."""
        from tools.science_funnel import skeleton_movie as sm
        _Recorder.hits = []
        sm.main(["--engine", self.url, "--render", "mesh",
                 "--scratch", str(ROOT / ".tmp/tmg_gate_scratch"),
                 "--out", str(ROOT / ".tmp/tmg_gate_out"),
                 "--frames", "6", "--no-judge"])
        paths = [h["path"] for h in _Recorder.hits]
        self.assertIn("/mesh_bin", paths, "the mesh compose never reached /mesh_bin")
        self.assertIn("/camera", paths)
        self.assertNotIn(
            "/membrane_bin", paths,
            "REGRESSION: the monkey scene posted a splat buffer to "
            "/membrane_bin — the old splat-cloud technique is back")
        mesh_hits = [h for h in _Recorder.hits if h["path"] == "/mesh_bin"]
        self.assertGreaterEqual(mesh_hits[0]["bytes"], 1_000_000,
                                "the mesh upload is implausibly small")

    def test_04_splat_render_flag_still_posts_membrane_bin(self):
        """The splat machinery stays alive behind --render splat (other users;
        the A/B measurement lane). Explicit, not default."""
        from tools.science_funnel import skeleton_movie as sm
        _Recorder.hits = []
        sm.main(["--engine", self.url, "--render", "splat",
                 "--scratch", str(ROOT / ".tmp/tmg_gate_scratch_splat"),
                 "--out", str(ROOT / ".tmp/tmg_gate_out"),
                 "--frames", "6", "--no-judge"])
        paths = [h["path"] for h in _Recorder.hits]
        self.assertIn("/membrane_bin", paths)
        self.assertNotIn("/mesh_bin", paths)

    def test_05_parser_default_is_mesh(self):
        """The default compose of the monkey scene is the triangle technique."""
        import argparse
        from tools.science_funnel import skeleton_movie as sm
        src = Path(sm.__file__).read_text(encoding="utf-8")
        self.assertIn('default="mesh"', src,
                      "skeleton_movie --render default is no longer mesh")


if __name__ == "__main__":
    unittest.main()
