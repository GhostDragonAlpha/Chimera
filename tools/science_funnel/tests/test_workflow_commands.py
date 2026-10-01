"""test_workflow_commands.py -- the falsifier gates for the workflow command
surface (lane agent/workflow-mcp-20260920).

Rule 0 receipt: tools/science_funnel/validation/workflow_mcp_20260920/receipt.json

Run (both sys.path roots):
  python -B -m unittest tools.science_funnel.tests.test_workflow_commands -v
"""
from __future__ import annotations

import ast
import asyncio
import io
import json
import sys
import threading
import unittest
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np
from PIL import Image

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

ROOT = Path(__file__).resolve().parents[3]

BONE_TINT = (210, 192, 153)     # warm-dominant: r > g > b
BACKGROUND = (4, 5, 15)         # the engine's cool background family


def _png(arr: np.ndarray) -> bytes:
    buf = io.BytesIO()
    Image.fromarray(arr.astype(np.uint8)).save(buf, format="PNG")
    return buf.getvalue()


def _bone_frame(w: int = 128, h: int = 96, present: bool = True,
                value: int = 0) -> bytes:
    """A deterministic frame: cool background, one warm bone-tint ellipse well
    inside the frame (never touching the border band)."""
    img = np.zeros((h, w, 3), dtype=np.uint8)
    img[:, :] = BACKGROUND
    if present:
        yy, xx = np.mgrid[0:h, 0:w]
        inside = (((xx - w / 2) / (w * 0.25)) ** 2
                  + ((yy - h / 2) / (h * 0.3)) ** 2) <= 1.0
        for c in range(3):
            img[:, :, c][inside] = BONE_TINT[c]
    if value:
        img[:, :, 0][0, 0] = value     # version stamp pixel (top-left)
    return _png(img)


class _VersionedRecorder(BaseHTTPRequestHandler):
    """Engine-shaped recorder: /frame answers a frame that CHANGES after every
    POST (the settle-capture law needs two consecutive equal captures that
    differ from the pre-POST reference); every hit is recorded."""

    hits: list = []
    version: int = 0

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
        self.rfile.read(n)
        type(self).hits.append({"path": self.path, "bytes": n})
        type(self).version += 1
        self._answer(b'{"ok":true}', "application/json")

    def do_GET(self):
        type(self).hits.append({"path": self.path, "bytes": 0})
        if self.path.startswith("/frame"):
            self._answer(_bone_frame(value=type(self).version % 255), "image/png")
        else:
            self._answer(b"{}", "application/json")


def _infant_bundle(name: str = "probe-bundle", stage: str | None = "infant",
                   second_stage: str | None = None) -> dict:
    comps = [{"id": "bones", "stage": ({"label": stage, "confirmed": True,
                                        "provenance": "USNM 497135 collection record"}
                                       if stage else None)}]
    if second_stage:
        comps.append({"id": "adult_arm", "stage": {"label": second_stage,
                                                   "confirmed": True,
                                                   "provenance": "collection"}})
    return {"schema": "chimera.creature_bundle.v1", "name": name,
            "components": comps}


class FreePortLaw(unittest.TestCase):
    def test_01_free_port_is_bind_tested_and_never_8127(self):
        from tools.science_funnel import workflow_commands as wc
        for _ in range(20):
            port = wc.free_port()
            self.assertNotEqual(port, 8127)
            self.assertGreater(port, 0)
        # the law is enforced even if a caller asks for an avoid-set without it
        port = wc.free_port(avoid=())
        self.assertNotEqual(port, 8127)

    def test_02_start_engine_refuses_missing_binary(self):
        from tools.science_funnel import workflow_commands as wc
        with self.assertRaises(RuntimeError) as ctx:
            wc.start_engine("Z:/definitely/not/here/chimera_engine.exe")
        self.assertIn("engine_binary_missing", str(ctx.exception))


class NoSplatPathConformance(unittest.TestCase):
    """FALSIFIER no_splat_path: render_creature has NO route to the splat
    pipeline -- grep-provable (AST) AND wire-provable (recorder)."""

    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _VersionedRecorder)
        cls.port = cls.server.server_address[1]
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_03_ast_render_path_has_no_membrane_or_splat_reference(self):
        import tools.science_funnel.workflow_commands as wcmod
        src = Path(wcmod.__file__).read_text(encoding="utf-8")
        tree = ast.parse(src)
        render_fns = {"render_creature", "_compose_triangle", "_post_mesh",
                      "_settle_capture", "_fetch_frame", "_post_json"}
        forbidden_strings = ("/membrane", "layer_splat_buffer", "splat_bin")
        checked = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in render_fns:
                checked += 1
                doc_const = None
                if (node.body and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Constant)
                        and isinstance(node.body[0].value.value, str)):
                    doc_const = node.body[0].value   # the docstring NAMES the absence
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                        if sub is doc_const:
                            continue
                        for bad in forbidden_strings:
                            self.assertNotIn(
                                bad, sub.value,
                                f"REGRESSION: {node.name} references {bad!r} "
                                "-- the splat route is reachable again")
        self.assertEqual(checked, len(render_fns), "render-path functions moved")

    def test_04_render_creature_wire_never_posts_membrane_bin(self):
        from tools.science_funnel import workflow_commands as wc
        _VersionedRecorder.hits = []
        _VersionedRecorder.version = 0
        out = ROOT / ".tmp/wfmcp_gate/render"
        res = wc.render_creature("ct_skeleton", out_dir=out, orbit_frames=6,
                                 engine=self.url)
        paths = [h["path"] for h in _VersionedRecorder.hits]
        self.assertIn("/mesh_bin", paths, "the mesh compose never reached /mesh_bin")
        self.assertIn("/camera", paths)
        self.assertNotIn(
            "/membrane_bin", paths,
            "REGRESSION: render_creature posted a splat buffer -- the old "
            "splat-cloud technique is reachable from the command again")
        self.assertFalse(res["render_path"]["splat_route_reachable"])
        self.assertEqual(len(res["orbit"]["pngs"]), 6)
        self.assertTrue((out / "a_pose.png").is_file())
        self.assertTrue((out / "render_record.json").is_file())
        mesh_hits = [h for h in _VersionedRecorder.hits if h["path"] == "/mesh_bin"]
        self.assertGreaterEqual(mesh_hits[0]["bytes"], 1_000_000,
                                "the mesh upload is implausibly small")


class VerifyVisualGates(unittest.TestCase):
    def _frames(self, dirp: Path, n: int = 6, drop_frame: int | None = None):
        dirp.mkdir(parents=True, exist_ok=True)
        for i in range(n):
            (dirp / f"f{i:03d}.png").write_bytes(
                _bone_frame(present=(drop_frame != i)))

    def test_05_gates_pass_on_a_clean_bone_sequence(self):
        from tools.science_funnel import workflow_commands as wc
        fdir = ROOT / ".tmp/wfmcp_gate/frames_ok"
        mdir = ROOT / ".tmp/wfmcp_gate/masks_ok"
        self._frames(fdir)
        mdir.mkdir(parents=True, exist_ok=True)
        for p in sorted(fdir.glob("*.png")):
            m = np.zeros((96, 128), dtype=np.uint8)
            yy, xx = np.mgrid[0:96, 0:128]
            m[(((xx - 64) / 40.0) ** 2 + ((yy - 48) / 40.0) ** 2) <= 1.0] = 255
            Image.fromarray(m).save(mdir / f"{p.stem}_hull.png")
        res = wc.verify_visual(fdir, masks_dir=mdir)
        self.assertEqual(res["n_gates_fail"], 0,
                         json.dumps(res["gates"], indent=1))
        self.assertGreaterEqual(res["n_gates_pass"], 3)
        gates = {g["metric"]: g for g in res["gates"]}
        self.assertTrue(gates["whole_hull_coverage_median"]["pass"])
        self.assertEqual(gates["clipscan_collapse_events"]["value"], 0)
        # the per-frame minimum is REPORTED, never gated (protocol law)
        self.assertIsNone(gates["whole_hull_coverage_min_frame"]["pass"])
        self.assertIsNotNone(gates["whole_hull_coverage_min_frame"]["value"])

    def test_06_gates_flag_a_collapsed_frame_as_red(self):
        from tools.science_funnel import workflow_commands as wc
        fdir = ROOT / ".tmp/wfmcp_gate/frames_clip"
        self._frames(fdir, drop_frame=3)
        res = wc.verify_visual(fdir)
        self.assertEqual(res["n_gates_fail"], 1)
        self.assertIn("clipscan_collapse_events", res["reds"])
        gates = {g["metric"]: g for g in res["gates"]}
        self.assertEqual(gates["clipscan_collapse_events"]["value"], 1)

    def test_07_absent_instruments_are_named_not_assumed(self):
        from tools.science_funnel import workflow_commands as wc
        fdir = ROOT / ".tmp/wfmcp_gate/frames_bare"
        self._frames(fdir, n=3)
        res = wc.verify_visual(fdir)
        gates = {g["metric"]: g for g in res["gates"]}
        self.assertIsNone(gates["whole_hull_coverage"]["pass"])
        self.assertIn("--masks", gates["whole_hull_coverage"]["not_measured_reason"])
        self.assertIsNone(gates["object_seen"]["pass"])
        self.assertGreater(res["n_gates_not_measured"], 0)


class HonestAbsence(unittest.TestCase):
    """FALSIFIER honest_absence: on THIS lineage (no tools/creature_graph/
    reality_gate.py) the gate commands return the STRUCTURED absence --
    never a crash, never a silent pass."""

    def test_08_adjudicate_returns_structured_absence(self):
        from tools.science_funnel import workflow_commands as wc
        try:
            import tools.creature_graph.reality_gate  # noqa: F401
            self.skipTest("reality_gate resolved on this checkout -- the "
                          "absence branch is not exercisable here")
        except Exception:
            pass
        p = ROOT / ".tmp/wfmcp_gate/bundle.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(_infant_bundle()), encoding="utf-8")
        for fn in (wc.adjudicate, wc.bio_check):
            res = fn(p)
            self.assertEqual(res["status"], "unavailable")
            self.assertEqual(res["error"], "reality_gate_not_resolvable")
            self.assertIn("integrated on master pending", res["message"])
            self.assertEqual(res["branch"], "agent/reality-fantasy-gate-20260920")

    def test_09_bio_stage_is_gate_independent(self):
        from tools.science_funnel import workflow_commands as wc
        p = ROOT / ".tmp/wfmcp_gate/stage_ok.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(_infant_bundle()), encoding="utf-8")
        res = wc.bio_stage(p)
        self.assertEqual(res["status"], "labeled")
        self.assertEqual(res["stage_label"], "infant")
        unlabeled = ROOT / ".tmp/wfmcp_gate/stage_missing.json"
        unlabeled.write_text(json.dumps(_infant_bundle(stage=None)), encoding="utf-8")
        res = wc.bio_stage(unlabeled)
        self.assertEqual(res["status"], "failed_unadmittable")
        self.assertIn("like a missing sha256", res["reason"])
        mixed = ROOT / ".tmp/wfmcp_gate/stage_mixed.json"
        mixed.write_text(json.dumps(_infant_bundle(second_stage="adult")),
                         encoding="utf-8")
        res = wc.bio_stage(mixed)
        self.assertEqual(res["status"], "failed_unadmittable")
        self.assertIn("one life stage", res["reason"])

    def test_10_fantasy_acknowledge_records_then_names_gate_state(self):
        from tools.science_funnel import workflow_commands as wc
        p = ROOT / ".tmp/wfmcp_gate/fantasy.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(_infant_bundle(stage=None)), encoding="utf-8")
        res = wc.bio_fantasy_acknowledge(p)
        self.assertTrue(res["fantasy_manifest_acknowledged"])
        ack = Path(res["acknowledged_bundle"])
        self.assertTrue(ack.is_file())
        self.assertTrue(json.loads(ack.read_text(encoding="utf-8"))
                        ["fantasy_manifest_acknowledged"])
        # adjudication either classified (gate resolved) or honestly absent
        self.assertIn(res["adjudication"]["status"], ("classified", "unavailable"))


class ChecklistWalk(unittest.TestCase):
    def test_11_every_step_is_command_or_named_judgment(self):
        from tools.science_funnel import workflow_commands as wc
        res = wc.checklist()
        sections = {s["section"] for s in res["walk"]}
        self.assertEqual(sections, {"0", "1", "2", "3", "4", "5", "6"})
        all_steps = [st for sec in res["walk"] for st in sec["steps"]]
        for st in all_steps:
            self.assertTrue(st["needs_judgment"] != bool(st["commands"]),
                            f"step {st['step_id']} must be command XOR judgment")
            self.assertTrue(st["what_the_command_does"])
        by_name = {st["name"].lower(): st for st in all_steps}
        tri = next(v for k, v in by_name.items() if "triangle technique" in k)
        self.assertIn("render_creature", tri["commands"])
        pix = next(v for k, v in by_name.items() if "deterministic pixel" in k)
        self.assertIn("verify_visual", pix["commands"])
        cls = next(v for k, v in by_name.items() if "classification" in k)
        self.assertIn("adjudicate", cls["commands"])
        self.assertGreater(res["n_steps_needing_judgment"], 0,
                           "judgment steps must be named, not commanded away")


class McpRegistry(unittest.TestCase):
    """FALSIFIER registry: the server lists the new commands; orient/next are
    untouched and still working."""

    def test_12_registry_lists_new_and_old(self):
        sys.path.insert(0, str(ROOT / "ChimeraEngine"))
        import mcp_server                                    # noqa: PLC0415
        tools = {t.name for t in asyncio.run(mcp_server.mcp.list_tools())}
        for name in ("orient", "next",                      # the existing surface
                     "frame", "question", "classify", "render", "prove",
                     "decide", "hear", "reload", "parts_fit", "part_spray",
                     "material_train", "hunt_view"):
            self.assertIn(name, tools, f"pre-existing tool {name} vanished")
        for name in ("render_creature", "verify_visual", "adjudicate",
                     "bio_stage", "bio_check", "bio_fantasy_acknowledge",
                     "checklist"):
            self.assertIn(name, tools, f"new command {name} not registered")

    def test_13_orient_and_next_still_answer(self):
        sys.path.insert(0, str(ROOT / "ChimeraEngine"))
        import mcp_server                                    # noqa: PLC0415
        orient = mcp_server.ENG.orient()
        self.assertTrue(orient and isinstance(orient, str))
        nxt = mcp_server.ENG.next_term()
        self.assertIsInstance(nxt, (str, type(None)))


if __name__ == "__main__":
    unittest.main()
