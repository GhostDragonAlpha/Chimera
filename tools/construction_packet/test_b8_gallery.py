"""B8 acceptance-gallery closure battery: the four gallery items
(GAME_PLAN_ACTION_RPG.md §13 "acceptance gallery") that the B0-B7 batteries
did not yet exercise, qualified on the resident runtime.

Item -> test map:
  6  loose object inside a container ..... test_gallery_06_loose_object_in_container
  7/13 retessellation adds no strength ... test_gallery_07_13_retessellation_adds_no_strength
  15 select a moving part, delay the edit  test_gallery_15_delayed_edit_revalidates
  16 fast part vs thinnest wall .......... test_gallery_16_fast_thin_wall_no_tunneling

Gallery text, verbatim:
  6: "Move a loose object inside a container. It responds to the enclosure and
     pushes back; it neither passes through nor inherits a hidden welded
     transform."
  7: "Refine a thickness-bearing wall. Mass/inertia and the selected force
     response stay within declared tolerance; visual subdivision does not add
     material or strength." (13: "...a different triangle order or display LOD
     does not change material strength...")
  15: "Select a moving or interpolated part, then delay the edit. Revalidate
      the displayed-snapshot hit against current physical state; the operation
      updates safely or refuses instead of attaching to a stale world-space
      point."
  16: "Move quickly toward the thinnest admitted wall. Swept contact or
      qualified substeps prevent tunneling without silently enlarging the
      visible obstacle."

Item 16 drove the one engine change in this commit: the DECLARED IMPACT
BACKSTOP (b2_scene.cpp B8_STOP_M). The resting-calibrated penalty rung let a
20 mm plate dropped from 1 m sink fully below the plane (measured COM -31 mm)
and be ejected by the spring's stored energy. The declared policy: ordinary
rung to 15 mm penetration, then a stiff damped catch (200x rung stiffness,
zeta 0.7), spring energy booked in stored_penalty_j_, engagements counted in
state.backstop_engagements. Measured after: min COM -6.7 mm at 4.4 m/s
impact (plate top stays above the plane), max penetration 17.4 mm < 20 mm
thickness, settles, no ejection.

Run:  python tools/construction_packet/test_b8_gallery.py
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
PORT = 8799
BASE = f"http://127.0.0.1:{PORT}"

_proc: subprocess.Popen | None = None


def _get(path: str) -> dict:
    with urllib.request.urlopen(BASE + path, timeout=10) as r:
        return json.loads(r.read().decode())


def _post(path: str, body: str = "") -> dict:
    req = urllib.request.Request(BASE + path, data=body.encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())


def _state() -> dict:
    return _get("/tick_b2_state")


def _part(st: dict, pid: str) -> dict:
    return next(p for p in st["parts"] if p["id"] == pid)


def _wait_steps(n: int) -> None:
    s0 = _state()["steps"]
    deadline = time.time() + 30.0
    while time.time() < deadline:
        if _state()["steps"] >= s0 + n:
            return
        time.sleep(0.005)
    raise RuntimeError("engine is not stepping")


def _aim_camera(tx: float, ty: float, tz: float) -> None:
    # render-thread camera bookmark, exactly the B3 discipline: the 8 floats
    # are the LIVE camera state (r, theta, phi, target xyz, pan xy) — an
    # orbit around the target, not an eye/target pair. B3's proven framing
    # (r=1.0, theta=0.6, phi=0.4) resolves 0.1 m parts at this scale.
    name = "b8cam"
    assert _post("/cameras", json.dumps(
        {"op": "save", "name": name,
         "v": [1.0, 0.6, 0.4, tx, ty, tz, 0.0, 0.0]})).get("ok")
    assert _post("/cameras", json.dumps({"op": "recall", "name": name})).get("ok")


_framesz: tuple[int, int] | None = None


def _frame_size() -> tuple[int, int]:
    """The framebuffer the projection actually fills: measure it from the
    /frame PNG (B3's discipline) — the engine renders at the real swapchain
    size, which need not equal the --hidden window arguments."""
    global _framesz
    if _framesz is None:
        import io

        from PIL import Image
        with urllib.request.urlopen(BASE + "/frame", timeout=10) as r:
            png = r.read()
        _framesz = Image.open(io.BytesIO(png)).convert("RGB").size
    return _framesz


def _pick_at_world(x: float, y: float, z: float) -> dict:
    """Pick the pixel the engine camera sees this world point at."""
    r = _post("/project", json.dumps({"x": x, "y": y, "z": z}))
    assert r.get("ok"), r
    W, H = _frame_size()
    return _post("/tick_b2_pick", json.dumps({"px": r["sx"] / W,
                                              "py": r["sy"] / H}))


def _admit(parts: list[dict], reason: str) -> None:
    doc = {"schema": "chimera.b2_scene.v1", "gravity_m_s2": 9.81,
           "reason": reason, "parts": parts}
    r = _post("/tick_b2_admit", json.dumps(doc))
    assert r.get("ok"), r


def _box(pid, x0, x1, y0, y1, z0, z1, rho=600, mu=0.4):
    return b2_scene_gen.box_document(pid, x0, x1, y0, y1, z0, z1, rho, mu)


def _subdivided_box(pid, x0, x1, y0, y1, z0, z1, rho, mu) -> dict:
    """The same solid, retessellated: the four side faces and the top face
    are each split into four triangles around a face centre (one new vertex
    per face); the bottom face keeps its original two triangles so the
    ground-site count is untouched. Mass, COM, inertia and ground rung are
    the authored values of the plain box - if the solver let visual
    subdivision add material or strength, the settled response would move."""
    base = b2_scene_gen.box_document(pid, x0, x1, y0, y1, z0, z1, rho, mu)
    cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
    vs = list(base["vertices_local_m"])                 # 8 corners, as authored
    # corner indices (b2_scene_gen order):
    # 0(x0,y0,z0) 1(x1,y0,z0) 2(x1,y1,z0) 3(x0,y1,z0)
    # 4(x0,y0,z1) 5(x1,y0,z1) 6(x1,y1,z1) 7(x0,y1,z1)
    centres = [(cx, y1, cz), (cx, cy, z0), (cx, cy, z1), (x0, cy, cz), (x1, cy, cz)]
    for c in centres:
        vs.extend(c)
    ci = [8, 9, 10, 11, 12]                             # top, z0, z1, x0, x1
    tris: list[int] = []
    for quad, m in [((0, 1, 2, 3), ci[1]), ((5, 4, 7, 6), ci[2]),
                    ((4, 0, 3, 7), ci[3]), ((1, 5, 6, 2), ci[4]),
                    ((3, 2, 6, 7), ci[0])]:
        for k in range(4):
            tris += [quad[k], quad[(k + 1) % 4], m]
    # bottom face: the plain box's own two triangles (corners 0,1,4,5)
    bt = base["boundary_triangles"]
    # keep only triangles whose vertices are all bottom corners
    bottom = {0, 1, 4, 5}
    for i in range(0, len(bt), 3):
        if set(bt[i:i + 3]) <= bottom:
            tris += bt[i:i + 3]
    out = dict(base)
    out["vertices_local_m"] = vs
    out["boundary_triangles"] = tris
    return out


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
        _proc.wait(timeout=30)


class B8Gallery(unittest.TestCase):
    # ── gallery 16: fast part vs the thinnest admitted wall ─────────────────
    def test_gallery_16_fast_thin_wall_no_tunneling(self):
        # 20 mm plate (the smallest admitted thickness) dropped from 1 m:
        # impact ~4.4 m/s, 1.1 mm of travel per 250 us substep.
        _admit([_box("plate", -0.05, 0.05, 1.02, 1.04, -0.05, 0.05, 100, 0.4),
                _box("far", 50.0, 50.1, -b2_scene_gen.REST_SINK_M, 0.10,
                     -0.05, 0.05)], "b8-tunnel")
        min_com_y, max_pen, max_speed = 1e9, 0.0, 0.0
        bs0 = _state()["backstop_engagements"]
        deadline = time.time() + 6.0
        while time.time() < deadline:
            st = _state()
            p = _part(st, "plate")
            min_com_y = min(min_com_y, p["com_m"][1])
            max_pen = max(max_pen, st["max_penetration_m"])
            max_speed = max(max_speed, p["speed_m_s"])
            time.sleep(0.016)
        st = _state()
        p = _part(st, "plate")
        # never fully submerged: COM stays above -(stop + overshoot) so the
        # plate's TOP face stays above the plane (pre-fix measured -31 mm)
        self.assertGreater(min_com_y, -0.008,
                           f"plate sank through the plane (min COM {min_com_y})")
        # penetration bounded below the plate's own 20 mm thickness
        self.assertLess(max_pen, 0.02, "penetration exceeded wall thickness")
        # the declared catch actually engaged
        self.assertGreater(st["backstop_engagements"], bs0,
                           "backstop never engaged during a 4.4 m/s impact")
        # no ejection: rebound never exceeds the impact speed
        self.assertLess(max_speed, 4.6, "backstop ejected the plate")
        # and it settles on the plane, not inside it
        self.assertAlmostEqual(p["com_m"][1], 0.0, delta=2e-3)
        self.assertLess(p["speed_m_s"], 1e-3)
        # resting contact never touches the backstop (declared stop > rest sink)
        e0 = _state()["backstop_engagements"]
        _wait_steps(4000)
        self.assertEqual(_state()["backstop_engagements"], e0,
                         "resting contact must not engage the backstop")

    # ── gallery 6: a loose object inside a container ─────────────────────────
    def test_gallery_06_loose_object_in_container(self):
        # Design lessons measured the hard way, kept as comments because
        # they are the physics this scene must respect:
        #  * Coulomb friction gives no terminal velocity: a sustained 3 N
        #    on the 0.26 kg west wall ran it away to 48 m/s and fired the
        #    inner block through the east wall at 11 m/s. Short pulse only.
        #  * Coplanar bottoms used to kick the pair vertically: two boxes
        #    on the same ground rest with coplanar bottom faces, float
        #    noise made the bottom face a "penetrated" candidate, and the
        #    shallowest-face rule picked it over the side face actually
        #    entered (measured: block climbed the wall to COM 0.142, wall
        #    sank 45 mm). Fixed in the engine by B2_FACE_TOL: candidacy
        #    requires genuine penetration past the 0.1 mm noise floor.
        #  * The backstop's explicit-stability margin is MATERIAL-DEPENDENT:
        #    authoring the inner block 4x stiffer (2.5 mm sink) put the
        #    backstop's omega*h and c*h/m past their safe range for that
        #    mass/stiffness pair and the solver exploded (measured 81 m/s
        #    in 5 ms). The scene therefore uses the default ground, and the
        #    per-material stability envelope is recorded as the design
        #    input for the next gate (plan §11.3 swept-contact policy).
        #  * A THIN sliding block is likewise outside the penalty ground's
        #    honest range (friction torque pitches it nose-down with no
        #    pressure redistribution to answer; measured 91 m/s explosion).
        #    The inner block is squat (100x50x100 mm), the stable family of
        #    the B7 slide wedge.
        #  * A SLENDER STANDING WALL is outside it too, and this is the
        #    compliance envelope in its purest measured form: a 20 mm-wide,
        #    110 mm-tall steel wall toppled under a 2 N push at its COM.
        #    The base friction couple (F x 55 mm lever) needs ~11 N of
        #    normal shift across the 20 mm base; on a foundation that
        #    rests 10 mm sunk (REST_SINK_M), carrying that shift means
        #    tilting ~18 deg - past the wall's own 10 deg tipping angle.
        #    A part whose base half-width is comparable to the foundation
        #    sink cannot stand under lateral load, honest physics or not.
        #    The walls are therefore squat and wide-based (40 mm thick,
        #    70 mm tall): foundation tilt under the couple stays ~1 deg,
        #    far under the ~27 deg tipping angle.
        RS = b2_scene_gen.REST_SINK_M
        walls = [
            _box("w_w", -0.18, -0.14, -RS, 0.06, -0.18, 0.18),
            # steel east wall: static friction ~310 N outranks the contact
            # reaction, so the enclosure is an anchor, not a second mover
            _box("w_e", 0.14, 0.18, -RS, 0.06, -0.18, 0.18, 7850),
            _box("w_s", -0.14, 0.14, -RS, 0.06, -0.18, -0.14),
            _box("w_n", -0.14, 0.14, -RS, 0.06, 0.14, 0.18),
        ]
        inner = _box("inner", -0.05, 0.05, -RS, 0.04, -0.05, 0.05)
        _admit(walls + [inner], "b8-container")
        _wait_steps(2000)                       # everything settles
        st0 = _state()
        x0 = _part(st0, "inner")["com_m"][0]
        com = _part(st0, "inner")["com_m"]
        # 2.0 N outranks the inner block's 1.47 N ground friction; over
        # 0.35 s it crosses the 90 mm gap and meets the east wall near
        # 0.57 m/s (predicted penetration ~3 mm on the 79 kg steel anchor,
        # far under the 15 mm backstop stop)
        r = _post("/tick_b2_load", json.dumps(
            {"part": "inner", "force_n": [2.0, 0.0, 0.0], "point_world": com}))
        self.assertTrue(r.get("ok"), r)
        # sample THROUGH the pulse: the block crosses the gap and meets the
        # wall inside the 0.35 s window, so a post-pulse poll would only see
        # it at rest. Fast polling (~200 Hz) catches the >0.2 m/s cruise.
        max_speed, min_y, max_y = 0.0, 1.0, -1.0
        s0 = _state()["steps"]
        deadline = time.time() + 12.0
        zeroed = False
        while time.time() < deadline:
            st = _state()
            if not zeroed and st["steps"] >= s0 + 1400:   # 0.35 s pulse done
                _post("/tick_b2_load", json.dumps(
                    {"part": "inner", "force_n": [0.0, 0.0, 0.0],
                     "point_world": com}))
                zeroed = True
            inner = _part(st, "inner")
            max_speed = max(max_speed, inner["speed_m_s"])
            min_y = min(min_y, inner["com_m"][1])
            max_y = max(max_y, inner["com_m"][1])
            # the inner block never leaves the pen (no pass-through)
            self.assertLess(abs(inner["com_m"][0]), 0.13,
                            "inner block passed through a wall")
            self.assertLess(abs(inner["com_m"][2]), 0.13)
            # it stays near its own plane: never sinks through, never
            # climbs (transient contact compliance allowed, riding a wall
            # at COM 0.045 is not)
            self.assertGreater(min_y, 0.005, "inner block sank through the plane")
            self.assertLess(max_y, 0.045, "inner block climbed a wall")
            if zeroed and st["steps"] >= s0 + 4400:   # pulse + settle
                break
            time.sleep(0.004)
        self.assertTrue(zeroed, "engine is not stepping")
        st = _state()
        inn, we = _part(st, "inner"), _part(st, "w_e")
        d_in = inn["com_m"][0] - x0
        # it responded to the enclosure: it moved, under its own dynamics
        self.assertGreater(d_in, 0.05,
                           "inner block did not move under the push")
        self.assertGreater(max_speed, 0.2, "inner block has no own motion")
        # it pushes back: the wall's reaction stopped it short of the free
        # travel the pulse alone would have carried (~0.18 m)
        self.assertLess(d_in, 0.16, "the wall did not stop the inner block")
        # no hidden welded transform: the anchored wall did not travel
        # (authored COM 0.16, 0.025)
        self.assertLess(abs(we["com_m"][0] - 0.16), 2e-3,
                        "the east wall moved with the block")
        self.assertLess(abs(we["com_m"][1] - 0.025), 2e-3,
                        "the east wall was lifted")
        # it settles on its own ground contact: authored COM IS the resting
        # COM: (−REST_SINK+0.04)/2 = 0.015
        self.assertAlmostEqual(inn["com_m"][1], 0.015, delta=5e-3)

    # ── gallery 15: select a moving part, then delay the edit ────────────────
    def test_gallery_15_delayed_edit_revalidates(self):
        _admit([_box("box_a", 0.0, 0.10, -b2_scene_gen.REST_SINK_M, 0.10, -0.05, 0.05),
                _box("box_b", 3.0, 3.10, -b2_scene_gen.REST_SINK_M, 0.10, -0.05, 0.05)],
               "b8-delayed")
        # selection resolves parts by their CURRENT pose, not a snapshot:
        # box_b picks cleanly at its own projected top face at rest. (Done
        # before the fall: once support is off box_b is a 10 m/s moving
        # target, and the delayed-edit half below is about box_a.)
        _aim_camera(3.05, 0.045, 0.0)
        time.sleep(0.3)
        com_b = _part(_state(), "box_b")["com_m"]
        pk = _pick_at_world(com_b[0], com_b[1] + 0.055, com_b[2])
        self.assertEqual(pk.get("id"), "box_b", f"box_b at rest: {pk}")
        _aim_camera(0.05, 0.0, 0.0)             # frame the fall corridor
        _post("/tick_b2_support", json.dumps({"on": False}))   # both fall
        _wait_steps(400)                                       # 0.1 s of fall
        com = _part(_state(), "box_a")["com_m"]
        # aim just BELOW the measured centre: the box falls ~1 m/s while
        # the project->pick round trip is in flight, so a top-face point
        # would be stale above the box by the time the ray fires
        pk = _pick_at_world(com[0], com[1] - 0.02, com[2])
        self.assertTrue(pk.get("ok"), pk)
        self.assertEqual(pk["id"], "box_a")
        stale_point = pk["hit"]
        _wait_steps(800)                        # the edit is DELAYED: box_a moved
        # the edit names the part; it revalidates against CURRENT state and
        # acts through the part's present pose, not a frozen world point
        v0 = _part(_state(), "box_a")["speed_m_s"]
        r = _post("/tick_b2_load", json.dumps(
            {"part": "box_a", "force_n": [0.0, 20.0, 0.0],
             "point_world": stale_point}))
        self.assertTrue(r.get("ok"), r)         # 20 N up vs ~6.5 N weight
        _wait_steps(200)                        # 50 ms of net upward accel
        v1 = _part(_state(), "box_a")["speed_m_s"]
        self.assertLess(v1, v0 - 0.5,
                        "the delayed load did not act on the moving part")
        # remove the part the snapshot named; the delayed edit must now REFUSE
        # by name instead of attaching to the stale world-space point
        r = _post("/tick_b2_remove", json.dumps({"id": "box_a"}))
        self.assertTrue(r.get("ok"), r)
        r = _post("/tick_b2_load", json.dumps(
            {"part": "box_a", "force_n": [0.0, 1.0, 0.0],
             "point_world": stale_point}))
        self.assertFalse(r.get("ok"), r)
        self.assertIn("box_a", r["error"])
        # the stale pixel no longer resolves anything (the part is gone)
        r = _post("/project", json.dumps({"x": stale_point[0],
                                          "y": stale_point[1], "z": stale_point[2]}))
        W, H = _frame_size()
        pk = _post("/tick_b2_pick", json.dumps({"px": r["sx"] / W,
                                                "py": r["sy"] / H}))
        self.assertFalse(pk.get("ok", True), f"stale pixel still picks: {pk}")
        # (no support re-arm here: box_b has been falling since the test
        # began — re-enabling the ground under a part 5 m below the plane
        # would be a fake impact. admit() re-arms support for the next test.)

    # ── gallery 7/13: retessellation adds no material or strength ────────────
    def test_gallery_07_13_retessellation_adds_no_strength(self):
        RS = b2_scene_gen.REST_SINK_M
        plain = _box("plain", 0.0, 0.10, -RS, 0.10, -0.05, 0.05, 600, 0.4)
        subdiv = _subdivided_box("subdiv", 1.0, 1.10, -RS, 0.10, -0.05, 0.05, 600, 0.4)
        self.assertGreater(len(subdiv["boundary_triangles"]),
                           len(plain["boundary_triangles"]))
        _admit([plain, subdiv], "b8-retess")
        _wait_steps(4000)                       # 1 s: fully settled
        st = _state()
        a, b = _part(st, "plain"), _part(st, "subdiv")
        self.assertEqual(a["mass_kg"], b["mass_kg"], "subdivision changed mass")
        self.assertAlmostEqual(a["reaction_n"], b["reaction_n"],
                               delta=1e-9 * abs(a["reaction_n"]) + 1e-12,
                               msg="visual subdivision changed the force response")
        self.assertAlmostEqual(a["com_m"][1], b["com_m"][1], delta=1e-9,
                               msg="subdivision changed the settled sink")
        # both still pick as themselves through the same solver path
        for pid, xc in (("plain", 0.05), ("subdiv", 1.05)):
            _aim_camera(xc, 0.045, 0.0)
            time.sleep(0.3)                     # let the render thread apply it
            pk = _pick_at_world(xc, 0.10, 0.0)  # top-face centre
            self.assertEqual(pk.get("id"), pid, f"{pid}: {pk}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
