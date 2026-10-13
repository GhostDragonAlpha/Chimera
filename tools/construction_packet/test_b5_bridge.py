"""B5 reuse battery: the cradle/frame parts and the B4 weld connector,
reused unchanged as a bridge on the resident runtime.

Section 13 B5 evidence column, runtime half: "One part/connector works in
multiple contexts ... no hand-authored genre-specific replacement physics".
The bridge is authored with the SAME b2_scene_gen.box_document + rung
derivation that built the B2/B3/B4 parts, joined by the SAME weld connector
document the B4 cradle clamp used, and loaded by the SAME timber block part
B4 placed (identical dimensions, density, friction, mass and inertia).  The
engine is not touched: the load path runs ground rung -> piers -> welds ->
deck -> contact -> load, and the measured reactions obey the same statics
and the same connector law F = k * stretch as the cradle.

The load sits OFF-CENTRE (x = 0.17 between weld centres 0.03/0.47), and the
prediction is NOT the rigid lever rule: the published B2 contact law applies
each pair's torque about the VERTEX OWNER's COM (b2_scene.cpp pp_pair_:
Ts -= (P - o.c) x f), so a box footprint symmetric about its own COM exerts
zero couple however off-centre it sits -- the load reaches the deck as a
force through the deck COM and the two welds must share it EXACTLY equally.
That position-independence, measured, is the evidence the connector and the
contact law compose the same way they did in the cradle.

Run:  python tools/construction_packet/test_b5_bridge.py
Requires: .tmp/body-engine/Release/chimera_engine.exe (Release build).
"""
from __future__ import annotations

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
RS = b2_scene_gen.REST_SINK_M

# ── the bridge, authored only from the B2/B3/B4 generators ────────────────
PIER_A = ("pier_a", 0.00, 0.06, -RS, 0.30, -0.05, 0.05, 2700, 0.6)
PIER_B = ("pier_b", 0.44, 0.50, -RS, 0.30, -0.05, 0.05, 2700, 0.6)
DECK_W0 = 600 * 0.62 * 0.03 * 0.10 * G          # deck weight, N
# weld equilibrium stretch: each weld carries half the deck, F = k * delta*
DECK_SAG = DECK_W0 / (2 * 2000.0)
# The deck is a SUSPENDED span: its soffit sits 60 mm above the pier tops
# and its corners overhang the piers by 60 mm, so every deck<->pier vertex
# pair stays outside the 50 mm part-part contact radius at rest (a 20 mm
# soffit gap measured spurious near-boundary contact pairs that walked the
# whole bridge apart).  The ONLY load path deck->piers is the weld connector
# -- exactly the B5 claim under test.  The deck is spawned delta* below its
# anchors so the connectors start at equilibrium tension: no release
# transient (the B3 spawn discipline, applied to welds).
DECK = ("deck", -0.06, 0.56, 0.36 - DECK_SAG, 0.39 - DECK_SAG, -0.05, 0.05,
        600, 0.3)
# the B4 cradle block verbatim (0.06 x 0.05 x 0.06 timber, rho 600, mu 0.3),
# now serving as the bridge load; spawned pre-sunk into the deck by the
# analytic pair-rung sink (the B3 spawn discipline)
# the load footprint sits strictly inside the deck top face with >= 10 mm
# edge margin and >= 22 mm clear of its triangulation diagonal
LOAD_X0, LOAD_Z0 = 0.14, -0.04
LOAD_DX, LOAD_DY, LOAD_DZ = 0.06, 0.04, 0.06
LOAD_MASS = 600 * LOAD_DX * LOAD_DY * LOAD_DZ
LOAD_W = LOAD_MASS * G
K_WELD = 2000.0
_kt_deck = 600 * 0.62 * 0.03 * 0.10 * G / RS
_kt_load = LOAD_MASS * G / RS
LOAD_SINK = LOAD_W / ((_kt_deck + _kt_load) / 2.0)
# the deck top sits at 0.39 - DECK_SAG minus the piers' extra sink under the
# half-deck weld load (~1.1 mm); spawn the load pre-sunk into that surface
LOAD_Y0 = 0.39 - DECK_SAG - 0.0011 - LOAD_SINK
# load centre sits at alpha ~ 0.32 between the pier centres (x = 0.03/0.47)
ALPHA = ((LOAD_X0 + LOAD_DX / 2) - 0.03) / (0.47 - 0.03)
# anchor pairs are NOT coincident: the deck-side point sits delta* below the
# pier-side point at the authored pose, i.e. every weld starts exactly at
# its equilibrium stretch.  Both points stay in the pier-top/deck-bottom gap.
def _anchors(x0: float, x1: float):
    # z-symmetric AND x-symmetric about the pier centre: an asymmetric
    # anchor set applies a net torque r x F to both parts even at the
    # equilibrium stretch, and that rotational mode walks the whole bridge
    # apart (measured: z = (-0.02,-0.02,+0.02) tipped the deck 2 deg in
    # 0.25 s, then the swing dragged the 49 N piers over at t ~ 1.5 s).
    return [((x0, 0.33 - DECK_SAG, -0.02), (x0, 0.33, -0.02)),
            ((x1, 0.33 - DECK_SAG, 0.02), (x1, 0.33, 0.02)),
            (((x0 + x1) / 2, 0.33 - DECK_SAG, 0.0),
             ((x0 + x1) / 2, 0.33, 0.0))]


WELD_A_ANCHORS = _anchors(0.02, 0.04)
WELD_B_ANCHORS = _anchors(0.46, 0.48)

PIER_W = 2700 * 0.06 * (0.30 + RS) * 0.10 * G
DECK_W = 600 * 0.62 * 0.03 * 0.10 * G

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


def _part(st: dict, pid: str) -> dict:
    return next(p for p in st["parts"] if p["id"] == pid)


def _weld(st: dict, a: str, b: str) -> dict:
    return next(w for w in st["welds"] if {w["a"], w["b"]} == {a, b})


def _settle(seconds: float) -> None:
    time.sleep(seconds)


def _box(pid, box, rho, mu) -> dict:
    return b2_scene_gen.box_document(pid, *box, rho, mu)


def weld_doc(a: str, b: str, anchors) -> dict:
    """The B4 cradle-clamp connector document, unchanged in schema.
    c_damp follows the rung's own damping-ratio law on the suspended mass:
    two welds at k each give c_crit = 2*sqrt(2k*m_deck) = 133.5 N.s/m, so
    zeta = 0.7 -> 66.7 per weld.  The underdamped release (c = 10, zeta
    0.11) overshoots 20+ mm and the reaction topples the 49 N piers."""
    return {"a": a, "b": b, "k": K_WELD, "c_damp": 66.7,
            "anchors_world": [[*pa, *pb] for pa, pb in anchors]}


def bridge_scene() -> dict:
    parts = [
        _box("pier_a", PIER_A[1:7], PIER_A[7], PIER_A[8]),
        _box("pier_b", PIER_B[1:7], PIER_B[7], PIER_B[8]),
        _box("deck", DECK[1:7], DECK[7], DECK[8]),
    ]
    return {"schema": "chimera.b2_scene.v1", "gravity_m_s2": G, "parts": parts,
            "reason": "B5 bridge: cradle/frame parts + B4 weld connector reused"}


def load_doc() -> dict:
    return _box("bridge_load",
                (LOAD_X0, LOAD_X0 + LOAD_DX, LOAD_Y0, LOAD_Y0 + LOAD_DY,
                 LOAD_Z0, LOAD_Z0 + LOAD_DZ), 600, 0.3)


def _pause(on: bool) -> None:
    assert _post("/tick_b2_pause", json.dumps({"on": on})).get("ok")


def build_bridge(with_load: bool = False) -> None:
    r = _post("/tick_b2_admit", json.dumps(bridge_scene()))
    assert r.get("ok"), f"admit refused: {r}"
    # the deck hangs on connectors that do not exist yet at admit: pause
    # the physics (the B4 control) so the weld anchors bake at the authored
    # pose, then release -- the deck's only transient is the weld settling
    _pause(True)
    assert _post("/tick_b2_weld", json.dumps(
        weld_doc("deck", "pier_a", WELD_A_ANCHORS))).get("ok")
    assert _post("/tick_b2_weld", json.dumps(
        weld_doc("deck", "pier_b", WELD_B_ANCHORS))).get("ok")
    if with_load:
        r = _post("/tick_b2_place", json.dumps(load_doc()))
        assert r.get("ok"), f"place refused: {r}"
    _pause(False)
    _settle(3.0)


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


def _rel(a: float, b: float) -> float:
    return abs(a - b) / max(abs(b), 1e-300)


class B5Bridge(unittest.TestCase):
    def setUp(self):
        _post("/tick_b2_clear")

    # ── the connector in a new context: statics + the connector law ───────
    def test_bridge_statics_and_connector_law(self):
        build_bridge()
        st0 = _get("/tick_b2_state")
        ra0 = _part(st0, "pier_a")["reaction_n"]
        rb0 = _part(st0, "pier_b")["reaction_n"]
        fa0 = _weld(st0, "deck", "pier_a")["force_n"]
        fb0 = _weld(st0, "deck", "pier_b")["force_n"]
        # baseline: the deck hangs on the welds, so the piers' ground
        # reactions already carry the whole scene: deck weight arrives
        # through the connectors, there is no separate deck rung reading
        self.assertLess(_rel(ra0 + rb0, st0["total_weight_n"]), 0.005)
        self.assertLess(_rel(st0["total_reaction_n"], st0["total_weight_n"]), 0.005)
        self.assertLess(_rel(fa0 + fb0, DECK_W), 0.01,
                        "welds must carry exactly the suspended deck weight")
        self.assertLess(_rel(fa0, fb0), 0.05, "symmetric deck -> equal welds")
        self.assertLess(_rel(ra0, PIER_W + fa0), 0.01,
                        "pier equilibrium: reaction = own weight + weld pull")
        deck_y0 = _part(st0, "deck")["com_m"][1]

        r = _post("/tick_b2_place", json.dumps(load_doc()))
        self.assertTrue(r.get("ok"), f"place refused: {r}")
        _settle(3.0)
        st1 = _get("/tick_b2_state")
        ra1 = _part(st1, "pier_a")["reaction_n"]
        rb1 = _part(st1, "pier_b")["reaction_n"]
        fa1 = _weld(st1, "deck", "pier_a")["force_n"]
        fb1 = _weld(st1, "deck", "pier_b")["force_n"]
        # the load's weight reaches the ground ONLY through the same weld
        # connector.  The published contact law (torque about the vertex
        # owner's COM) makes a self-symmetric footprint exert zero couple,
        # so the load enters the deck through its COM and BOTH welds take
        # exactly LOAD_W / 2 -- although the load sits at alpha = 0.32.
        self.assertLess(_rel(ra1 - ra0, LOAD_W / 2), 0.05,
                        f"pier_a delta {ra1 - ra0:.4f} vs half-load "
                        f"{LOAD_W / 2:.4f}")
        self.assertLess(_rel(rb1 - rb0, LOAD_W / 2), 0.05,
                        f"pier_b delta {rb1 - rb0:.4f} vs half-load "
                        f"{LOAD_W / 2:.4f}")
        self.assertLess(_rel(fa1 - fa0, LOAD_W / 2), 0.05)
        self.assertLess(_rel(fa1 + fb1, DECK_W + LOAD_W), 0.01,
                        "welds carry deck + load, nothing else")
        self.assertLess(_rel(st1["total_reaction_n"], st1["total_weight_n"]), 0.005)
        # the same connector law as the B4 cradle: stretch = F / k, now in
        # SERIES with the piers' ground rungs: the deck COM sinks by the
        # weld stretch plus the extra pier sink under the extra weld pull.
        k_rung_pier = PIER_W / RS
        sink_law = LOAD_W / (2 * K_WELD) + (LOAD_W / 2) / k_rung_pier
        sink = deck_y0 - _part(st1, "deck")["com_m"][1]
        self.assertGreater(sink, 0.0001, "deck must sag under the load")
        self.assertLess(_rel(sink, sink_law), 0.15,
                        f"deck sink {sink * 1e6:.0f} um vs series law "
                        f"{sink_law * 1e6:.0f} um")

    # ── severing the connector removes only its contribution ──────────────
    def test_connector_failure_redistributes(self):
        build_bridge(with_load=True)
        st0 = _get("/tick_b2_state")
        self.assertEqual(len(st0["welds"]), 2)
        rb0 = _part(st0, "pier_b")["reaction_n"]
        # sever while paused, so the removal itself is not a transient, and
        # sample the deterministic PRE-IMPACT window at 0.10 s (the deck
        # has swung ~0.13 rad on the surviving weld, its corner is still
        # 0.29 m up).  The wedged END state is deliberately NOT asserted
        # beyond survival facts: where the 0.62 m deck comes to rest
        # against the piers is bistable, and its friction can transiently
        # unload a pier.
        _pause(True)
        r = _post("/tick_b2_weld_remove",
                  json.dumps({"a": "deck", "b": "pier_b"}))
        self.assertTrue(r.get("ok"), f"weld_remove refused: {r}")
        _pause(False)
        _settle(0.10)
        st1 = _get("/tick_b2_state")
        self.assertEqual(len(st1["welds"]), 1,
                         "only the severed connector's contribution is gone")
        self.assertLess(_rel(rb0 - PIER_W, _weld(st0, "deck", "pier_b")["force_n"]),
                        0.02, "baseline: pier_b carried the weld pull")
        fa1 = _weld(st1, "deck", "pier_a")["force_n"]
        self.assertGreater(fa1, 1.0, "the surviving connector is engaged")
        # its magnitude rides the spring-mass engagement transient the
        # sever launches (omega = sqrt(k/m_deck) ~ 42 rad/s: the force
        # sweeps 5 -> 60 N within 0.1 s, phase-sensitive at read time), so
        # only engagement, not magnitude, is asserted here.
        deck1 = _part(st1, "deck")
        self.assertGreater(deck1["com_m"][1], 0.30,
                           "the deck is still suspended pre-impact")
        self.assertGreater(deck1["speed_m_s"], 0.3,
                           "the deck swings on the surviving weld")
        # the deck surface accelerates down at ~4.7 m/s2 < g, so the load
        # stays pressed onto the deck and rides it (measured 0.42-0.48 m/s
        # at 0.10 s, not the 0.98 m/s of free fall)
        load1 = _part(st1, "bridge_load")
        self.assertGreater(load1["com_m"][1], 0.33, "load still on the deck")
        self.assertGreater(load1["speed_m_s"], 0.2)
        self.assertLess(load1["speed_m_s"], 0.8, "riding, not free-falling")
        # pier reactions are NOT asserted after the sever: releasing weld_b
        # leaves pier_b rocking on its rung corners (pitch mode, period
        # ~1.7 s, zeta ~0.09 -- measured 3-5 N off its weight for seconds),
        # and the deck's post-impact tumble (~0.25 s) can load either pier.
        # The quantitative "removes exactly its contribution" claim is the
        # STATIC one proven above (pier_b carried the weld pull) plus the
        # connector bookkeeping below; the collapse itself is only asserted
        # to be survivable and to end with the load on the ground.
        # and after the collapse settles: the scene survives, the load
        # reached the ground, and the ground carries the whole scene within
        # the churn band of the wedged deck
        _settle(12.0)
        st2 = _get("/tick_b2_state")
        self.assertFalse(st2["diverged"])
        self.assertEqual(len(st2["welds"]), 1)
        load = _part(st2, "bridge_load")
        self.assertLess(load["com_m"][1], 0.08,
                        "the load must have fallen to the ground plane")
        self.assertLess(load["speed_m_s"], 0.02)
        self.assertLess(_rel(st2["total_reaction_n"], st2["total_weight_n"]),
                        0.02, "ground carries the whole scene (churn band)")

    # ── one part, one connector, multiple contexts (no new physics) ───────
    def test_part_and_connector_reuse(self):
        # the B4 cradle block verbatim: same extents, density, friction ->
        # same mass and inertia as the B4 test's BLOCK_BOX part
        b4_box = (0.10, 0.16, -RS, 0.04 - RS, 0.30, 0.36)
        b4 = _box("cradle_block", b4_box, 600, 0.3)
        ld = load_doc()
        self.assertAlmostEqual(ld["mass_kg"], b4["mass_kg"], places=12)
        for got, want in zip(ld["inertia_com_local_kg_m2"],
                             b4["inertia_com_local_kg_m2"]):
            self.assertAlmostEqual(got, want, places=12)
        self.assertEqual(ld["mu"], b4["mu"])
        # the connector document is the B4 weld schema, key for key
        self.assertEqual(set(weld_doc("a", "b", [((0, 0, 0), (0, 0, 0))] * 3)),
                         {"a", "b", "k", "c_damp", "anchors_world"})
        # every bridge part is box_document output: same field set as the
        # B3 stack layer documents -- no bridge-specific generator exists
        stack_doc = b2_scene_gen.box_document("x", 0, 1, 0, 1, 0, 1, 1000, 0.5)
        for doc in bridge_scene()["parts"] + [load_doc()]:
            self.assertEqual(set(doc), set(stack_doc))

    # ── the bridge is the bridge on screen ────────────────────────────────
    def test_frame_shows_bridge(self):
        import io
        from PIL import Image
        build_bridge(with_load=True)
        self.assertTrue(_post("/cameras", json.dumps(
            {"op": "save", "name": "b5test",
             "v": [1.3, 0.9, 0.2, 0.25, 0.18, 0.0, 0.0, 0.0]})).get("ok"))
        self.assertTrue(_post("/cameras", json.dumps(
            {"op": "recall", "name": "b5test"})).get("ok"))
        _settle(0.6)
        st = _get("/tick_b2_state")

        def hue(p):
            r, g, b = p
            if max(p) < 40:
                return "background"
            if r > g and r > b:
                return "yellow" if min(r - g, r - b) < 60 and g > 120 else "red"
            if g > r and g > b:
                return "green"
            if b > r and b > g:
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

        img = Image.open(io.BytesIO(_raw("/frame"))).convert("RGB")
        W, H = img.size
        probes = {}
        for pid, top in (("pier_a", 0.30), ("pier_b", 0.30),
                         ("deck", 0.35)):
            c = _part(st, pid)["com_m"]
            probes[pid] = (c[0], top, c[2])
        lc = _part(st, "bridge_load")["com_m"]
        probes["bridge_load"] = (lc[0], lc[1] + LOAD_DY / 2, lc[2])
        want = {"pier_a": "red", "pier_b": "green", "deck": "blue",
                "bridge_load": "yellow"}
        for pid, P in probes.items():
            r = _post("/project", json.dumps({"x": P[0], "y": P[1], "z": P[2]}))
            self.assertTrue(r.get("ok"), f"/project {pid}: {r}")
            got = hue_near(img, r["sx"], r["sy"])
            self.assertEqual(got, want[pid],
                             f"pixel at {pid}'s projected point: {got}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
