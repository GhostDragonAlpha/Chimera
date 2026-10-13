"""B3 gate battery: three dissimilar layers, loose and bonded variants.

The §13 B3 evidence column: "Distinct shear/slip behavior; no double mass;
render/pick/contact agree; delamination exposes the intended material."
The stack (b2_scene_gen.make_stack) is three rectangular layers of
different material, size and thickness -- granite base, steel middle,
timber top -- stacked so each upper layer's bottom vertices project
strictly inside the layer below. Both variants admit the IDENTICAL visible
shape; the bonded variant additionally gets the finite-area weld across
the steel/timber interface through the live control.

Run:  python tools/construction_packet/test_b3_layers.py
Requires: .tmp/body-engine/Release/chimera_engine.exe (Release build).
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
for p in (str(HERE), str(HERE.parent)):
    if p not in sys.path:
        sys.path.insert(0, p)

import b2_scene_gen  # noqa: E402

REPO = HERE.parent.parent
EXE = REPO / ".tmp" / "body-engine" / "Release" / "chimera_engine.exe"
PORT = 8793
BASE = f"http://127.0.0.1:{PORT}"

G = b2_scene_gen.G
IDS = [l[0] for l in b2_scene_gen.STACK_LAYERS]      # base, mid, top
MASS = {l[0]: l[7] * (l[2] - l[1]) * (l[4] - l[3]) * (l[6] - l[5])
        for l in b2_scene_gen.STACK_LAYERS}
MU = {l[0]: l[8] for l in b2_scene_gen.STACK_LAYERS}
TIMBER_COM = (0.15, 0.26 + b2_scene_gen.stack_rest_offsets()[2], 0.15)

_proc: subprocess.Popen | None = None


def _get(path: str) -> dict:
    with urllib.request.urlopen(BASE + path, timeout=5) as r:
        return json.loads(r.read().decode())


def _raw(path: str) -> bytes:
    with urllib.request.urlopen(BASE + path, timeout=25) as r:
        return r.read()


def _post(path: str, body: str = "") -> dict:
    req = urllib.request.Request(BASE + path, data=body.encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())


def _rel(a: float, b: float) -> float:
    return abs(a - b) / max(abs(b), 1e-300)


def _part(st: dict, pid: str) -> dict:
    return next(p for p in st["parts"] if p["id"] == pid)


def _settle(seconds: float) -> None:
    time.sleep(seconds)


def _wait(pred, timeout: float, dt: float = 0.05):
    deadline = time.time() + timeout
    st = _get("/tick_b2_state")
    while time.time() < deadline:
        if pred(st):
            return True, st
        time.sleep(dt)
        st = _get("/tick_b2_state")
    return pred(st), st


def _inspect(pid: str) -> dict:
    return _post("/tick_b2_inspect", json.dumps({"id": pid}))


def setUpModule():
    global _proc
    assert EXE.exists(), f"engine missing: {EXE} (build Release first)"
    _proc = subprocess.Popen(
        [str(EXE), str(PORT), "--hidden", "1600", "900", "--no-restore"],
        cwd=str(EXE.parent))
    deadline = time.time() + 30.0
    while time.time() < deadline:
        try:
            _get("/tick_state")
            return
        except Exception:
            time.sleep(0.25)
    raise RuntimeError("engine did not answer /tick_state within 30 s")


def tearDownModule():
    if _proc and _proc.poll() is None:
        _proc.terminate()


class B3Layers(unittest.TestCase):
    def setUp(self):
        _post("/tick_b2_clear")

    def admit(self, scene: dict) -> None:
        r = _post("/tick_b2_admit", json.dumps(scene))
        self.assertTrue(r.get("ok"), f"admit refused: {r}")

    # ── admission + no double mass ─────────────────────────────────────────
    def test_three_layers_no_double_mass(self):
        scene = b2_scene_gen.make_stack()
        self.admit(scene)
        _settle(2.5)
        st = _get("/tick_b2_state")
        self.assertFalse(st["diverged"])
        self.assertEqual(len(st["parts"]), 3)
        want = sum(m * G for m in MASS.values())
        self.assertLess(_rel(st["total_weight_n"], want), 1e-6,
                        "total weight must be the sum of the layer weights")
        for pid in IDS:
            p = _part(st, pid)
            self.assertLess(_rel(p["weight_n"], MASS[pid] * G), 1e-6)
        # the stack stands: base on 4 ground sites, both interfaces carry
        self.assertEqual(_part(st, "layer_base_granite")["contacts_active"], 4)
        self.assertGreater(_part(st, "layer_mid_steel")["contacts_pp_active"], 0)
        self.assertGreater(_part(st, "layer_top_timber")["contacts_pp_active"], 0)
        # the whole stack is at rest and the total reaction carries it
        for pid in IDS:
            self.assertLess(_part(st, pid)["speed_m_s"], 5e-3)
        self.assertLess(_rel(st["total_reaction_n"], want), 5e-3)

    # ── inspection by stable IDs ───────────────────────────────────────────
    def test_stable_id_inspection(self):
        scene = b2_scene_gen.make_stack()
        docs = {p["id"]: p for p in scene["parts"]}
        r = _inspect("layer_base_granite")
        self.assertFalse(r.get("ok", True), "inspect accepted with no scene")
        self.admit(scene)
        for pid in IDS:
            r = _inspect(pid)
            self.assertTrue(r.get("ok"), f"inspect {pid}: {r}")
            rec = r["part"]
            d = docs[pid]
            self.assertEqual(rec["id"], pid)
            self.assertAlmostEqual(rec["mass_kg"], d["mass_kg"], places=9)
            self.assertAlmostEqual(rec["mu"], d["mu"], places=9)
            self.assertEqual(rec["n_vertices"], 8)
            self.assertEqual(rec["n_triangles"], 12)
            for k in range(3):
                self.assertAlmostEqual(rec["com_local_m"][k],
                                       d["com_local_m"][k], places=9)
            for k in range(9):
                self.assertAlmostEqual(rec["inertia_com_local_kg_m2"][k],
                                       d["inertia_com_local_kg_m2"][k], places=9)
        r = _inspect("layer_nonexistent")
        self.assertFalse(r.get("ok", True), "unknown id accepted")
        self.assertIn("no part with id", r.get("error", ""))
        r = _post("/tick_b2_inspect", json.dumps({"id": 7}))
        self.assertFalse(r.get("ok", True), "non-string id accepted")

    # ── same initial visible shape, loose vs bonded ────────────────────────
    def test_variants_share_visible_shape(self):
        loose = b2_scene_gen.make_stack(bonded=False)
        bonded = b2_scene_gen.make_stack(bonded=True)
        for a, b in zip(loose["parts"], bonded["parts"]):
            self.assertEqual(a, b, "variants must admit identical part records")
        # both variants settle to the SAME rest pose (the weld anchors are
        # coincident -> zero preload -> the bonded variant's dynamics are
        # the loose variant's until a load asks the connector to carry)
        self.admit(loose)
        _settle(2.5)
        p_loose = {p["id"]: p["pose_c_m"] for p in _get("/tick_b2_parts")["parts"]}
        _post("/tick_b2_clear")
        self.admit(bonded)
        _settle(2.5)
        p_bond = {p["id"]: p["pose_c_m"] for p in _get("/tick_b2_parts")["parts"]}
        for pid in IDS:
            for k in range(3):
                self.assertAlmostEqual(p_loose[pid][k], p_bond[pid][k], delta=1e-3)

    # ── shear: loose slips, bonded does not ────────────────────────────────
    def _shear_pulse(self) -> tuple[float, float]:
        """3 N tangential pulse on the timber top; returns (top slip rel
        mid, mid slip rel base) after everything is at rest again."""
        st0 = _get("/tick_b2_state")
        x = {pid: _part(st0, pid)["com_m"][0] for pid in IDS}
        self.assertTrue(_post("/tick_b2_load", json.dumps(
            {"part": "layer_top_timber", "force_n": [3.0, 0.0, 0.0],
             "point_world": list(TIMBER_COM)})).get("ok"))
        _settle(0.08)
        self.assertTrue(_post("/tick_b2_load", json.dumps(
            {"part": "layer_top_timber", "force_n": [0.0, 0.0, 0.0],
             "point_world": list(TIMBER_COM)})).get("ok"))
        ok, st = _wait(lambda s: all(_part(s, pid)["speed_m_s"] < 5e-3
                                     for pid in IDS), 8.0)
        self.assertTrue(ok, f"stack never came to rest after the pulse: {st}")
        self.assertFalse(st["diverged"])
        x1 = {pid: _part(st, pid)["com_m"][0] for pid in IDS}
        return x1["layer_top_timber"] - x1["layer_mid_steel"], \
            x1["layer_mid_steel"] - x1["layer_base_granite"]

    def test_shear_slip_distinct(self):
        # loose: the timber top shears off the steel middle (mu_pair 0.35,
        # threshold 0.35 * W_top = 1.78 N < the 3 N pulse), the steel middle
        # stays on the granite base (capacity 0.45 * (W_mid + W_top) =
        # 102 N >> the shear it feels), the base stays on the ground
        # (capacity 0.5 * W_total = 256 N).
        self.admit(b2_scene_gen.make_stack(bonded=False))
        _settle(2.5)
        slip_top_loose, slip_mid_loose = self._shear_pulse()
        self.assertGreater(slip_top_loose, 0.008,
                           "loose stack must slip at the timber/steel interface")
        self.assertLess(slip_mid_loose, 0.005,
                        "only the loaded interface may slip")
        # bonded: the finite-area weld across the SAME interface carries
        # the shear; no relative slip anywhere
        _post("/tick_b2_clear")
        self.admit(b2_scene_gen.make_stack(bonded=True))
        _settle(2.5)
        self.assertTrue(_post("/tick_b2_weld", json.dumps(
            b2_scene_gen.stack_weld_document())).get("ok"))
        _settle(0.5)
        # the weld carries the pulse: sample its force while the load is on
        self.assertTrue(_post("/tick_b2_load", json.dumps(
            {"part": "layer_top_timber", "force_n": [3.0, 0.0, 0.0],
             "point_world": list(TIMBER_COM)})).get("ok"))
        ok, st = _wait(lambda s: s["welds"] and s["welds"][0]["force_n"] > 2.0, 2.0)
        self.assertTrue(ok, f"weld never carried the shear: {st}")
        self.assertTrue(_post("/tick_b2_load", json.dumps(
            {"part": "layer_top_timber", "force_n": [0.0, 0.0, 0.0],
             "point_world": list(TIMBER_COM)})).get("ok"))
        _settle(0.5)
        slip_top_bonded, slip_mid_bonded = self._shear_pulse()
        self.assertLess(slip_top_bonded, 0.002,
                        "bonded interface must not slip")
        self.assertLess(slip_mid_bonded, 0.005)
        # distinct behavior: the loose slip is an order of magnitude larger
        self.assertGreater(slip_top_loose, 4.0 * max(slip_top_bonded, 1e-9),
                           "loose and bonded shear behavior not distinct")

    # ── delamination exposes the intended material ─────────────────────────
    def test_delamination_exposes_material(self):
        self.admit(b2_scene_gen.make_stack(bonded=False))
        _settle(2.5)
        st0 = _get("/tick_b2_state")
        y0 = _part(st0, "layer_top_timber")["com_m"][1]
        rec_mid0 = _inspect("layer_mid_steel")["part"]
        # normal pull above the timber weight: the one-sided interface
        # opens -- delamination -- and the steel layer is what remains
        self.assertTrue(_post("/tick_b2_load", json.dumps(
            {"part": "layer_top_timber", "force_n": [0.0, 7.0, 0.0],
             "point_world": list(TIMBER_COM)})).get("ok"))
        ok, st = _wait(lambda s: _part(s, "layer_top_timber")["contacts_pp_active"] == 0
                       and _part(s, "layer_top_timber")["com_m"][1] > y0 + 0.02, 3.0)
        self.assertTrue(ok, f"top layer never delaminated: {st}")
        mid = _part(st, "layer_mid_steel")
        self.assertGreater(mid["contacts_pp_active"], 0,
                           "steel layer must still sit on the granite base")
        rec_mid = _inspect("layer_mid_steel")["part"]
        self.assertAlmostEqual(rec_mid["mu"], MU["layer_mid_steel"], places=9,
                               msg="exposed interface must be the steel's own material")
        self.assertAlmostEqual(rec_mid["mass_kg"], rec_mid0["mass_kg"], places=9)
        # release: the top falls back, the scene stays finite
        self.assertTrue(_post("/tick_b2_load", json.dumps(
            {"part": "layer_top_timber", "force_n": [0.0, 0.0, 0.0],
             "point_world": list(TIMBER_COM)})).get("ok"))
        _settle(2.0)
        self.assertFalse(_get("/tick_b2_state")["diverged"])


    # ── render / pick / contact agree ──────────────────────────────────────
    # The gate's "render/pick/contact agree": the overlay the renderer draws,
    # the ray pick, and the contact solver all walk the SAME world meshes.
    # Evidence: for each layer, the engine's own projection (/project) of a
    # point on that layer's exposed top face lands on a pixel that (a) picks
    # back that layer's stable ID at that plane and (b) renders that layer's
    # palette hue. Then a shear moves the timber: the pick follows the part
    # to its NEW pose, and the pixel it vacated stops rendering timber.
    def _project(self, p):
        r = _post("/project", json.dumps({"x": p[0], "y": p[1], "z": p[2]}))
        self.assertTrue(r.get("ok"), f"/project {p}: {r}")
        return r["sx"], r["sy"]

    def test_render_pick_contact_agree(self):
        import io
        from PIL import Image
        self.admit(b2_scene_gen.make_stack(bonded=False))
        _settle(2.5)
        # aim the engine camera at the stack (render-thread bookmark discipline)
        self.assertTrue(_post("/cameras", json.dumps(
            {"op": "save", "name": "b3test",
             "v": [1.0, 0.6, 0.4, 0.15, 0.14, 0.15, 0.0, 0.0]})).get("ok"))
        self.assertTrue(_post("/cameras", json.dumps(
            {"op": "recall", "name": "b3test"})).get("ok"))
        _settle(0.6)
        st = _get("/tick_b2_state")
        half = {"layer_base_granite": 0.06, "layer_mid_steel": 0.05,
                "layer_top_timber": 0.04}
        tops = {pid: _part(st, pid)["com_m"][1] + half[pid] for pid in half}
        probe = {"layer_top_timber": (0.15, 0.15),
                 "layer_mid_steel": (0.15, 0.10),
                 "layer_base_granite": (0.15, 0.04)}
        PAL = {"layer_base_granite": "red", "layer_mid_steel": "green",
               "layer_top_timber": "blue"}

        def hue(p):
            # Palette colors are strong-dominance primaries (kLayerRgb:
            # rendered timber blue is b-r ~ 150). The scene's background
            # gradient is a blue-gray (measured ~(54,62,86) beside the
            # stack, b-r ~ 32): a bare "b is largest" test mislabels it
            # timber-blue whenever the most saturated pixel in the scan
            # radius happens to be background. Require channel dominance
            # so "blue" means the palette, never the gradient.
            r, g, b = p
            if max(p) < 40:
                return "background"
            if r > g + 60 and r > b + 60:
                return "red"
            if g > r + 60 and g > b + 40:
                return "green"
            if b > r + 60 and b > g + 40:
                return "blue"
            return "other"

        def hue_near(img, sx, sy, rad=3):
            best, best_sat = None, -1
            for dy in range(-rad, rad + 1):
                for dx in range(-rad, rad + 1):
                    p = img.getpixel((int(sx) + dx, int(sy) + dy))
                    sat = max(p) - min(p)
                    if sat > best_sat:
                        best, best_sat = p, sat
            return hue(best)

        png = _raw("/frame")
        img = Image.open(io.BytesIO(png)).convert("RGB")
        W, H = img.size
        for pid, (x, z) in probe.items():
            P = (x, tops[pid], z)
            sx, sy = self._project(P)
            pk = _post("/tick_b2_pick",
                       json.dumps({"px": sx / W, "py": sy / H}))
            self.assertTrue(pk.get("ok"), f"pick {pid}: {pk}")
            self.assertEqual(pk["id"], pid,
                             f"pick at {pid}'s own projected point: {pk}")
            self.assertAlmostEqual(pk["hit"][1], tops[pid], delta=2e-3,
                                   msg="pick hit must lie on the projected plane")
            self.assertEqual(hue_near(img, sx, sy), PAL[pid],
                             f"rendered pixel at {pid}'s projected point")
        # the agreement tracks the CONTACT state, not a static snapshot:
        # a point just inside the timber's trailing edge renders and picks
        # timber before the shear; after the timber slides off it, the same
        # pixel is no longer timber (and the pick refuses it), while the
        # timber's NEW center still picks the timber by its stable ID.
        vac = (0.065, tops["layer_top_timber"], 0.15)
        sx0, sy0 = self._project(vac)
        pk = _post("/tick_b2_pick", json.dumps({"px": sx0 / W, "py": sy0 / H}))
        self.assertEqual(pk.get("id"), "layer_top_timber", f"pre-shear: {pk}")
        self.assertEqual(hue_near(img, sx0, sy0), "blue", "pre-shear pixel")
        slip, _ = self._shear_pulse()
        # the probe point sits 5 mm inside the trailing edge; the loose
        # slip measures 11-13 mm (the pulse is wall-clock, so it varies)
        self.assertGreater(slip, 0.008, "shear must clear the probe point")
        _settle(0.6)
        img = Image.open(io.BytesIO(_raw("/frame"))).convert("RGB")
        pk = _post("/tick_b2_pick", json.dumps({"px": sx0 / W, "py": sy0 / H}))
        self.assertFalse(pk.get("ok", True),
                         f"vacated pixel must stop picking timber: {pk}")
        # per-pixel agreement: the pick ray for THIS pixel refuses timber,
        # so THIS pixel must not render timber. (A scan radius here would
        # wander into the timber's own silhouette edge - the part legitimately
        # renders in the neighbouring pixels; the agreement claim is about
        # the pixel whose ray refused, measured center pixel.)
        self.assertNotEqual(hue(img.getpixel((int(sx0), int(sy0)))), "blue",
                            "the vacated pixel must stop rendering timber")
        st = _get("/tick_b2_state")
        newc = _part(st, "layer_top_timber")["com_m"]
        sx1, sy1 = self._project((newc[0], newc[1] + half["layer_top_timber"],
                                  newc[2]))
        pk = _post("/tick_b2_pick", json.dumps({"px": sx1 / W, "py": sy1 / H}))
        self.assertEqual(pk.get("id"), "layer_top_timber",
                         f"pick must follow the part to its new pose: {pk}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
