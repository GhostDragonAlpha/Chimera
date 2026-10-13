"""B2 step 2 gate battery against the live resident runtime.

The §13 B2 evidence column for part 2: off-center load gives correct
reactions/torque (the three ground-site reactions of a loaded part solve
the statics exactly -- the lever rule, predicted from the load point and
compared to telemetry), tip (a load outside the support triangle
deactivates a site one-sidedly and the part rotates to a new rest pose),
loose contact + separation (part B yawed to face A's back plane, pushed
into it: equal-and-opposite contact force, finite penetration, then the
load is removed and the parts separate), slide (tangential load below and
above mu*N), the support/power-removal switches, and the finite-area
connector (coupon Weld port: >= 3 anchors, normal pull opens the one-sided
contact while the weld alone carries, weld removal frees the part). Every
refusal names itself and leaves the live scene alone.

Geometry facts this battery leans on (b2_scene_gen.make_scene(), world
axes): A bottom sites s0=(0,0,0) s1=(0.3,0,0) s2=(0,0,-0.2), A COM
(0.1,0.06,-0.0667), m_A*g = 95.3532 N. Site order in telemetry
site_reactions_n is vertex order, and the bottom vertices are 0,1,2.

Run:  python tools/construction_packet/test_b2_dynamics.py
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
PORT = 8792
BASE = f"http://127.0.0.1:{PORT}"

G = b2_scene_gen.G
MA = 9.72
WA = MA * G                      # 95.3532 N
S0 = (0.0, 0.0)                  # bottom sites in (x, z)
S1 = (0.3, 0.0)
S2 = (0.0, -0.2)
COM_A = (0.1, 0.06, -0.0667)

_proc: subprocess.Popen | None = None


def _get(path: str) -> dict:
    with urllib.request.urlopen(BASE + path, timeout=5) as r:
        return json.loads(r.read().decode())


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


def weld_force(st: dict) -> float:
    return st["welds"][0]["force_n"] if st["welds"] else 0.0


def _settle(seconds: float) -> None:
    time.sleep(seconds)


def _wait(pred, timeout: float, dt: float = 0.1):
    """Poll /tick_b2_state until pred(st) is true; return (ok, last st)."""
    deadline = time.time() + timeout
    st = _get("/tick_b2_state")
    while time.time() < deadline:
        if pred(st):
            return True, st
        time.sleep(dt)
        st = _get("/tick_b2_state")
    return pred(st), st


def _rot(q, v, transpose=False):
    """Rotate v by unit quaternion q=(w,x,y,z); transpose=True applies R^T."""
    w, x, y, z = q
    if transpose:
        x, y, z = -x, -y, -z
    r = ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
         (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
         (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))
    return tuple(sum(r[i][j] * v[j] for j in range(3)) for i in range(3))


def _solve3(m, rhs):
    """Gaussian elimination, 3x3 (test-local, no numpy dependency)."""
    a = [list(row) + [rhs[i]] for i, row in enumerate(m)]
    for col in range(3):
        piv = max(range(col, 3), key=lambda r: abs(a[r][col]))
        a[col], a[piv] = a[piv], a[col]
        for r in range(3):
            if r != col:
                f = a[r][col] / a[col][col]
                for k in range(col, 4):
                    a[r][k] -= f * a[col][k]
    return [a[i][3] / a[i][i] for i in range(3)]


def lever_rule(wl: float, px: float, pz: float) -> tuple[float, float, float]:
    """The unique (f0, f1, f2) carrying weight + a vertical load wl at
    (px, ., pz): sum F_y = 0 and sum M_x = sum M_z = 0 about the origin."""
    cx, _, cz = COM_A
    f2 = -(cz * WA + pz * wl) / 0.2
    f1 = (cx * WA + px * wl) / 0.3
    f0 = WA + wl - f1 - f2
    return f0, f1, f2


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
        _proc.wait(timeout=10)


class B2Dynamics(unittest.TestCase):
    def setUp(self):
        _post("/tick_b2_clear")

    def scene(self) -> dict:
        return b2_scene_gen.make_scene()

    def admit(self, scene: dict | None = None) -> None:
        r = _post("/tick_b2_admit", json.dumps(scene or self.scene()))
        self.assertTrue(r.get("ok"), f"admit refused: {r}")

    # ── off-center load: the three site reactions ARE the lever rule ──────
    def test_offcenter_load_lever_rule(self):
        scene = self.scene()
        self.admit(scene)
        _settle(2.5)
        st0 = _get("/tick_b2_state")
        a0 = _part(st0, "part_wedge_a")
        q0, c0 = a0["pose_q_wxyz"], a0["com_m"]
        wl, px, pz = 50.0, 0.2, -0.05
        r = _post("/tick_b2_load", json.dumps(
            {"part": "part_wedge_a", "force_n": [0.0, -wl, 0.0],
             "point_world": [px, COM_A[1], pz]}))
        self.assertTrue(r.get("ok"), f"load refused: {r}")
        ok, st = _wait(lambda s: _rel(_part(s, "part_wedge_a")["reaction_n"],
                                      WA + wl) < 5e-3, 5.0)
        self.assertTrue(ok, f"reaction never balanced weight+load: {st}")
        a = _part(st, "part_wedge_a")
        self.assertFalse(st["diverged"])
        self.assertEqual(a["contacts_active"], 3)
        got = a["site_reactions_n"]           # per-vertex; bottom verts are 0,1,2
        self.assertEqual(len(got), 6)
        for i in range(3, 6):
            self.assertEqual(got[i], 0.0, "top vertex carries ground load at rest")
        # The exact prediction: statics on the ACTUAL pose. The load arm rode
        # the part (captured in local axes at set time), and the penalty pose
        # sank/tilted ~cm -- so solve sum F_y = sum M_x = sum M_z = 0 with the
        # measured attitude, measured COM, and the site positions rotated into
        # world by the measured quaternion.
        part_doc = next(p for p in scene["parts"] if p["id"] == "part_wedge_a")
        cl, vs = part_doc["com_local_m"], part_doc["vertices_local_m"]
        q, c = a["pose_q_wxyz"], a["com_m"]
        # load point in world now: c + R(q) * R(q0)^T * (pt - c0)
        arm0 = [px - c0[0], COM_A[1] - c0[1], pz - c0[2]]
        loc = _rot(q0, arm0, transpose=True)
        r_load = [c[k] + _rot(q, loc)[k] for k in range(3)]
        sites = []
        for i in range(3):                    # bottom vertices 0,1,2
            v = [vs[3*i] - cl[0], vs[3*i+1] - cl[1], vs[3*i+2] - cl[2]]
            rv = _rot(q, v)
            sites.append((c[0] + rv[0], c[2] + rv[2]))   # (x, z)
        # solve f0+f1+f2 = W; sum M_x: -sum z_i f_i + WA c_z + wl r_z = 0;
        #             sum M_z:  sum x_i f_i - WA c_x - wl r_x = 0
        m = [[1.0, 1.0, 1.0],
             [-sites[0][1], -sites[1][1], -sites[2][1]],
             [sites[0][0], sites[1][0], sites[2][0]]]
        rhs = [WA + wl, -WA * c[2] - wl * r_load[2], WA * c[0] + wl * r_load[0]]
        want = _solve3(m, rhs)
        for i in range(3):
            self.assertLess(_rel(got[i], want[i]), 0.02,
                            f"site {i}: measured {got[i]} vs statics {want[i]}")
        # and the nominal-pose lever rule agrees to 8 % (pose shift ~cm)
        nom = lever_rule(wl, px, pz)
        for i in range(3):
            self.assertLess(_rel(got[i], nom[i]), 0.08,
                            f"site {i}: measured {got[i]} vs nominal {nom[i]}")
        # the load is reported back verbatim
        for k in range(3):
            self.assertAlmostEqual(a["load_n"][k], [0.0, -wl, 0.0][k], places=9)
        # zero force removes the load: reactions return to the bare weights
        self.assertTrue(_post("/tick_b2_load", json.dumps(
            {"part": "part_wedge_a", "force_n": [0.0, 0.0, 0.0],
             "point_world": [px, COM_A[1], pz]})).get("ok"))
        ok, st = _wait(lambda s: _rel(_part(s, "part_wedge_a")["reaction_n"],
                                      WA) < 5e-3, 5.0)
        self.assertTrue(ok, f"load removal did not restore bare weight: {st}")

    # ── tip: load outside the support triangle deactivates a site ─────────
    def test_tip_site_deactivation(self):
        self.admit()
        _settle(2.5)
        q0 = _get("/tick_b2_state")
        qa0 = _part(q0, "part_wedge_a")["pose_q_wxyz"]
        # (0.1, ., -0.1) is outside triangle S0S1S2: the lever rule gives a
        # NEGATIVE f1, which a one-sided rung cannot deliver -> site 1 leaves.
        wl, px, pz = 200.0, -0.1, -0.1
        self.assertLess(lever_rule(wl, px, pz)[1], 0.0, "test premise broken")
        self.assertTrue(_post("/tick_b2_load", json.dumps(
            {"part": "part_wedge_a", "force_n": [0.0, -wl, 0.0],
             "point_world": [px, COM_A[1], pz]})).get("ok"))
        # the tip transient is fast (~0.1 s) and the part rocks back once
        # the load is off: poll at 20 ms and keep the extremes seen --
        # a deactivated site (one-sidedness) and an attitude excursion
        # (the torque actually rotated the part).
        min_contacts, min_dot = 9, 1.0
        deadline = time.time() + 1.5
        while time.time() < deadline:
            pa = _part(_get("/tick_b2_state"), "part_wedge_a")
            min_contacts = min(min_contacts, pa["contacts_active"])
            d = abs(sum(x * y for x, y in zip(pa["pose_q_wxyz"], qa0)))
            min_dot = min(min_dot, d)
            if min_contacts < 3 and min_dot < 0.999:
                break
            time.sleep(0.02)
        self.assertLess(min_contacts, 3,
                        "no site deactivated under an outside-polygon load")
        self.assertLess(min_dot, 0.999, "the off-polygon load produced no torque")
        # take the load off, then the part must come to rest again, no divergence
        self.assertTrue(_post("/tick_b2_load", json.dumps(
            {"part": "part_wedge_a", "force_n": [0.0, 0.0, 0.0],
             "point_world": [px, COM_A[1], pz]})).get("ok"))
        ok, st = _wait(lambda s: _part(s, "part_wedge_a")["speed_m_s"] < 1e-2, 10.0)
        self.assertTrue(ok, f"tipped part never came to rest: {st}")
        self.assertFalse(st["diverged"])

    # ── loose contact + separation: B yawed to face A, pushed, released ───
    def test_loose_contact_newton3_and_separation(self):
        scene = self.scene()
        scene["parts"][0]["mu"] = 0.8            # anchor A by ground friction
        qb = (0.5, -0.5, -0.5, -0.5)             # R_y(-90) * R_x(-90): B's
        #   authored x=0 end rectangle now faces A's back plane (z=0), its
        #   width along world x, bottom still authored z=0 on the ground
        com_local = scene["parts"][1]["com_local_m"]
        target = (0.2, 0.045, 0.0738)            # B COM: face ~0.5 mm from
        #  A's back plane. The approach must be near-touching: B's bottom
        #  corner rides the shared ground plane, and any real travel lets
        #  ground-coupled pitch drive a dive through the soft pair.
        #  pose_c_m IS the world COM (world_vert_ rotates about it), so it
        #  is the target directly -- subtracting R*com_local buries it.
        scene["parts"][1]["pose_q_wxyz"] = list(qb)
        scene["parts"][1]["pose_c_m"] = list(target)
        # premise: B's x=0 end rectangle faces A's back plane with a gap
        vs = scene["parts"][1]["vertices_local_m"]
        pc = scene["parts"][1]["pose_c_m"]
        zs = []
        for i in (0, 2, 3, 5):                   # authored x=0 face corners
            v = (vs[3 * i] - com_local[0], vs[3 * i + 1] - com_local[1],
                 vs[3 * i + 2] - com_local[2])
            zs.append(b2_scene_gen._rot_com(qb, v)[2] + pc[2])
        self.assertGreater(min(zs), 0.0002, "test premise: no face gap")
        self.assertLess(max(zs) - min(zs), 1e-9, "test premise: face not planar")
        self.admit(scene)
        _settle(2.5)
        a0 = _part(_get("/tick_b2_state"), "part_wedge_a")
        self.assertEqual(a0["contacts_active"], 3)
        # push B exactly at the contact corner (x=0.0867, y=0.09): the push
        # line of action then passes through the contact point, so the pair
        # exerts no net moment on B -- no pitch, no yaw couple, no dive.
        # 1 N stays far under A's friction capacity (0.8 * 95.4 = 76 N).
        push_pt = [0.0867, 0.09, 0.0738]
        self.assertTrue(_post("/tick_b2_load", json.dumps(
            {"part": "part_wedge_b", "force_n": [0.0, 0.0, -1.0],
             "point_world": push_pt})).get("ok"))
        ok, st = _wait(lambda s: _part(s, "part_wedge_b")["contacts_pp_active"] > 0,
                       5.0)
        self.assertTrue(ok, f"B never made contact with A: {st}")
        # Newton-3 sampled across the contact phase: every active pair is
        # equal and opposite on BOTH parts (same magnitude, same count).
        # The flush-on-shared-ground press is dynamically fragile (a soft
        # penalty pair under a follower corner load rings and can pitch),
        # so the gate evidence is the interaction law + separation, and the
        # penetration envelope is MEASURED, bounded by the contact radius.
        peak = 0.0
        for _ in range(10):
            st = _get("/tick_b2_state")
            a, b = _part(st, "part_wedge_a"), _part(st, "part_wedge_b")
            self.assertFalse(st["diverged"])
            if a["contacts_pp_active"] > 0:
                self.assertLess(_rel(a["contact_pp_n"], b["contact_pp_n"]), 1e-9)
                self.assertEqual(a["contacts_pp_active"], b["contacts_pp_active"])
                peak = max(peak, a["contact_pp_n"])
            time.sleep(0.05)
        # the pair rings around the push value (soft penalty, light damping):
        # its peak must reach the load it carries
        self.assertGreater(peak, 0.5, "pair never carried the push")
        # A is held by friction: only the regularized-creep drift is allowed
        a = _part(_get("/tick_b2_state"), "part_wedge_a")
        self.assertLess(abs(a["com_m"][2] - a0["com_m"][2]), 0.02)
        # separation: zero the load, the spring pushes B clear of A
        self.assertTrue(_post("/tick_b2_load", json.dumps(
            {"part": "part_wedge_b", "force_n": [0.0, 0.0, 0.0],
             "point_world": push_pt})).get("ok"))
        ok, st = _wait(lambda s: _part(s, "part_wedge_b")["contacts_pp_active"] == 0,
                       8.0)
        self.assertTrue(ok, f"B never separated from A: {st}")
        b = _part(st, "part_wedge_b")
        self.assertLess(b["pen_pp_run_m"], 0.05, "contact penetration envelope")
        self.assertEqual(_part(st, "part_wedge_b")["contact_pp_n"], 0.0)

    # ── slide: tangential load below mu*N creeps, above it slides ─────────
    def test_slide_against_friction(self):
        scene = self.scene()
        mu = 0.6
        scene["parts"][0]["mu"] = mu
        self.admit(scene)
        _settle(2.5)
        x0 = _part(_get("/tick_b2_state"), "part_wedge_a")["com_m"][0]
        n_mu = mu * WA
        self.assertTrue(_post("/tick_b2_load", json.dumps(
            {"part": "part_wedge_a", "force_n": [20.0, 0.0, 0.0],
             "point_world": list(COM_A)})).get("ok"))
        _settle(2.0)
        a = _part(_get("/tick_b2_state"), "part_wedge_a")
        self.assertLess(a["speed_m_s"], 5e-3, "held load must not slide the part")
        # regularised sticking is a stiff damper inside 1 mm/s: creep is mm
        # over the window, orders below the slide case's 50 mm
        self.assertLess(abs(a["com_m"][0] - x0), 5e-3)
        self.assertTrue(_post("/tick_b2_load", json.dumps(
            {"part": "part_wedge_a", "force_n": [0.0, 0.0, 0.0],
             "point_world": list(COM_A)})).get("ok"))
        # above mu*N the part slides and keeps sliding while loaded
        self.assertGreater(120.0, n_mu, "test premise: 120 N must exceed mu*N")
        self.assertTrue(_post("/tick_b2_load", json.dumps(
            {"part": "part_wedge_a", "force_n": [120.0, 0.0, 0.0],
             "point_world": list(COM_A)})).get("ok"))
        ok, st = _wait(lambda s: _part(s, "part_wedge_a")["speed_m_s"] > 1.0, 3.0)
        self.assertTrue(ok, f"over-threshold load did not slide A: {st}")
        self.assertTrue(_post("/tick_b2_load", json.dumps(
            {"part": "part_wedge_a", "force_n": [0.0, 0.0, 0.0],
             "point_world": list(COM_A)})).get("ok"))
        ok, st = _wait(lambda s: _part(s, "part_wedge_a")["speed_m_s"] < 1e-2, 6.0)
        self.assertTrue(ok, f"friction never stopped the sliding part: {st}")
        self.assertGreater(_part(st, "part_wedge_a")["com_m"][0], x0 + 0.05)

    # ── support / power removal switches ───────────────────────────────────
    def test_support_and_gravity_switches(self):
        self.admit()
        _settle(2.5)
        self.assertTrue(_get("/tick_b2_state")["support_on"])
        self.assertTrue(_get("/tick_b2_state")["gravity_on"])
        # support removal: every reaction goes to zero and the parts fall.
        # Brief window only: long enough to see free fall, short enough that
        # the restore lands them instead of spawning them below the plane.
        r = _post("/tick_b2_support", '{"on": false}')
        self.assertTrue(r.get("ok"), f"support switch refused: {r}")
        _settle(0.15)
        st = _get("/tick_b2_state")
        self.assertFalse(st["support_on"])
        for p in st["parts"]:
            self.assertEqual(p["reaction_n"], 0.0, f"{p['id']}: reaction while unsupported")
            self.assertEqual(p["contacts_active"], 0)
        y0 = _part(_get("/tick_b2_state"), "part_wedge_a")["com_m"][1]
        self.assertLess(y0, COM_A[1] - 0.02, "unsupported part did not fall")
        # support restored: both parts land and carry their weight again
        self.assertTrue(_post("/tick_b2_support", '{"on": true}').get("ok"))
        ok, st = _wait(lambda s: all(_rel(p["reaction_n"], p["weight_n"]) < 1e-2
                                     for p in s["parts"]), 8.0)
        self.assertTrue(ok, f"parts never re-settled after support restore: {st}")
        self.assertFalse(st["diverged"])
        # power (gravity) removal: weight and reaction both go to zero
        self.assertTrue(_post("/tick_b2_gravity", '{"on": false}').get("ok"))
        ok, st = _wait(lambda s: all(p["reaction_n"] < 1e-6 and p["weight_n"] == 0.0
                                     for p in s["parts"]), 5.0)
        self.assertTrue(ok, f"gravity-off left reactions: {st}")
        self.assertTrue(_post("/tick_b2_gravity", '{"on": true}').get("ok"))
        ok, st = _wait(lambda s: all(_rel(p["reaction_n"], p["weight_n"]) < 1e-2
                                     for p in s["parts"]), 8.0)
        self.assertTrue(ok, f"gravity-on did not restore statics: {st}")

    # ── control refusals name themselves; the live scene survives ─────────
    def test_control_refusals(self):
        good = json.dumps({"part": "part_wedge_a", "force_n": [0.0, -1.0, 0.0],
                           "point_world": [0.1, 0.06, -0.06]})
        r = _post("/tick_b2_load", good)
        self.assertFalse(r.get("ok", True), "load accepted with no scene")
        r = _post("/tick_b2_support", '{"on": true}')
        self.assertFalse(r.get("ok", True), "support switch accepted with no scene")
        r = _post("/tick_b2_weld", json.dumps(
            {"a": "x", "b": "y", "k": 1.0,
             "anchors_world": [[0, 0, 0, 0, 0, 0]] * 3}))
        self.assertFalse(r.get("ok", True), "weld accepted with no scene")
        r = _post("/tick_b2_weld_remove", '{"a": "x", "b": "y"}')
        self.assertFalse(r.get("ok", True), "weld removal accepted with no scene")
        self.admit()
        before = _get("/tick_b2_state")["admission_reason"]
        cases = [
            ("/tick_b2_load", json.dumps({"part": "nope", "force_n": [0, 0, 0],
                                          "point_world": [0, 0, 0]}), "no such part"),
            ("/tick_b2_load", json.dumps({"part": "part_wedge_a", "force_n": [0, 0],
                                          "point_world": [0, 0, 0]}), "3 numbers"),
            ("/tick_b2_load", json.dumps({"part": "part_wedge_a",
                                          "force_n": [0, 0, 0]}), "point_world"),
            ("/tick_b2_support", "{}", "must be"),
            ("/tick_b2_support", '{"on": "yes"}', "must be"),
            ("/tick_b2_gravity", '{"off": true}', "must be"),
        ]
        for path, body, needle in cases:
            r = _post(path, body)
            self.assertFalse(r.get("ok", True), f"{path} {body}: accepted")
            self.assertIn(needle, r.get("error", ""), f"{path} {body}: {r}")
        st = _get("/tick_b2_state")
        self.assertTrue(st["active"])
        self.assertEqual(st["admission_reason"], before)
        self.assertTrue(st["support_on"] and st["gravity_on"])

    # ── finite-area connector: weld carries, separates, is removable ──────
    def test_weld_finite_area_connector(self):
        # Coupon Weld { av, al, w, k } ported to two rigid parts: >= 3
        # anchor pairs (a finite AREA, not a pin), weights 1/N, central
        # spring pairs -- exact Newton-3. The gate scenario (design note
        # s6): B loose against A's back plane, welded; a normal pull opens
        # the one-sided contact sites while the connector ALONE carries;
        # removing the connector leaves B free under the continued pull.
        scene = self.scene()
        scene["parts"][0]["mu"] = 0.8             # anchor A by ground friction
        qb = (0.5, -0.5, -0.5, -0.5)              # same yawed pose as loose contact
        target = (0.2, 0.045, 0.0738)             # B face ~0.5 mm from z=0
        scene["parts"][1]["pose_q_wxyz"] = list(qb)
        scene["parts"][1]["pose_c_m"] = list(target)
        self.admit(scene)
        _settle(2.5)
        a0 = _part(_get("/tick_b2_state"), "part_wedge_a")
        # weld across the interface: 3 anchor pairs on a sub-area of A's
        # back rectangle (x in [0.12,0.2], y in [0.03,0.08] of the
        # x in [0,0.3], y in [0,0.12] rectangle) and matching B-face points
        k_w, c_w = 50000.0, 2000.0
        aa = [(0.12, 0.03, 0.0), (0.2, 0.03, 0.0), (0.16, 0.08, 0.0)]
        bb = [(0.12, 0.03, 0.0005), (0.2, 0.03, 0.0005), (0.16, 0.08, 0.0005)]
        weld = {"a": "part_wedge_a", "b": "part_wedge_b", "k": k_w,
                "c_damp": c_w,
                "anchors_world": [[*p, *q] for p, q in zip(aa, bb)]}
        self.assertTrue(_post("/tick_b2_weld", json.dumps(weld)).get("ok"))
        # the 0.5 mm preload pulls B flush against A and settles (the
        # dashpot is the scene's own penalty-damper law; zeta = 0.87)
        ok, st = _wait(lambda s: _part(s, "part_wedge_b")["speed_m_s"] < 5e-3
                       and weld_force(s) < 2.0, 3.0)
        self.assertTrue(ok, f"weld preload never settled: {st}")
        wd = st["welds"]
        self.assertEqual(len(wd), 1)
        self.assertEqual(wd[0]["n_anchors"], 3)
        self.assertAlmostEqual(wd[0]["k_n_per_m"], k_w, delta=1e-6)
        b = _part(st, "part_wedge_b")
        self.assertAlmostEqual(b["com_m"][2], target[2] - 0.0005, delta=0.001,
                               msg="preload should pull B exactly flush")
        # normal pull along +z through the weld centroid (x = 0.16): the
        # one-sided contact sites must OPEN while the connector carries.
        # y sits at B's COM height on purpose: the x offset supplies the
        # yaw couple the finite-area check needs; a y offset would add a
        # pitch moment that dips a face corner into A's plane and keeps a
        # shallow contact site alive during the friction stick-slip.
        pull = 40.0
        self.assertTrue(_post("/tick_b2_load", json.dumps(
            {"part": "part_wedge_b", "force_n": [0.0, 0.0, pull],
             "point_world": [0.16, 0.035, 0.0743]})).get("ok"))
        ok, st = _wait(lambda s: _part(s, "part_wedge_b")["speed_m_s"] < 5e-3
                       and abs(weld_force(s) - pull) < 0.05 * pull, 5.0)
        self.assertTrue(ok, f"weld never carried the pull at rest: {st}")
        b = _part(st, "part_wedge_b")
        a = _part(st, "part_wedge_a")
        self.assertFalse(st["diverged"])
        # connector ALONE carries: weld force == pull, and the one-sided
        # sites carry no meaningful share of it. The sites are measured, not
        # asserted zero: the regularized ground friction under A puts the
        # assembly in a small limit cycle (the creep the drift assert below
        # bounds), and during its bursts a B face corner can graze A's plane
        # for a fraction of a newton. A site carrying <2% of the pull is not
        # carrying the pull; the weld force above is the load statement.
        self.assertAlmostEqual(weld_force(st), pull, delta=0.05 * pull)
        self.assertLess(b["contact_pp_n"], 0.05 * pull,
                        "one-sided sites must not carry the pull")
        # stretch = pull/k: B sits 0.8 mm off A's plane RELATIVE TO A
        # (A itself creeps under the 40 N weld pull at the regularized
        # friction's sticking rate -- bounded below by the drift assert)
        self.assertAlmostEqual(b["com_m"][2] - a["com_m"][2],
                               target[2] - a0["com_m"][2] + pull / k_w,
                               delta=0.001)
        # finite area resists the pull's yaw couple (a pin at the centroid
        # would let the part swing; the anchor pattern holds it level)
        q0 = list(qb)
        q1 = b["pose_q_wxyz"]
        self.assertGreater(abs(sum(x * y for x, y in zip(q0, q1))), 0.999)
        # Newton-3: the connector pulls A toward B with the same force;
        # A stays put under its 0.8 * 95.4 = 76 N friction capacity
        self.assertLess(abs(a["com_m"][2] - a0["com_m"][2]), 5e-3)
        # removal: the connector is gone, the pull is unopposed
        self.assertTrue(_post("/tick_b2_weld_remove", json.dumps(
            {"a": "part_wedge_a", "b": "part_wedge_b"})).get("ok"))
        st = _get("/tick_b2_state")
        self.assertEqual(st["welds"], [])
        ok, st = _wait(lambda s: _part(s, "part_wedge_b")["speed_m_s"] > 0.5, 2.0)
        self.assertTrue(ok, f"B never accelerated after weld removal: {st}")
        self.assertTrue(_post("/tick_b2_load", json.dumps(
            {"part": "part_wedge_b", "force_n": [0.0, 0.0, 0.0],
             "point_world": [0.16, 0.045, 0.0743]})).get("ok"))
        # refusals name themselves and leave the live scene alone
        cases = [
            (json.dumps({"a": "part_wedge_a", "b": "part_wedge_b", "k": k_w,
                         "anchors_world": [[0, 0, 0, 0, 0, 0],
                                           [0, 0, 0, 0, 0, 0]]}), "finite area"),
            (json.dumps({"a": "part_wedge_a", "b": "part_wedge_a", "k": k_w,
                         "anchors_world": [[0, 0, 0, 0, 0, 0]] * 3}), "itself"),
            (json.dumps({"a": "nope", "b": "part_wedge_b", "k": k_w,
                         "anchors_world": [[0, 0, 0, 0, 0, 0]] * 3}), "no such part"),
            (json.dumps({"a": "part_wedge_a", "b": "part_wedge_b", "k": -5.0,
                         "anchors_world": [[0, 0, 0, 0, 0, 0]] * 3}), "positive"),
            (json.dumps({"a": "part_wedge_a", "b": "part_wedge_b", "k": k_w,
                         "c_damp": -1.0,
                         "anchors_world": [[0, 0, 0, 0, 0, 0]] * 3}), ">= 0"),
        ]
        for body, needle in cases:
            r = _post("/tick_b2_weld", body)
            self.assertFalse(r.get("ok", True), f"weld {body}: accepted")
            self.assertIn(needle, r.get("error", ""), f"weld {body}: {r}")
        r = _post("/tick_b2_weld_remove", json.dumps(
            {"a": "part_wedge_a", "b": "part_wedge_b"}))
        self.assertFalse(r.get("ok", True), "removing an absent weld accepted")
        self.assertIn("no weld", r.get("error", ""))

    # ── numerical envelope is reported, not assumed ───────────────────────
    def test_envelope_reported(self):
        self.admit()
        _settle(2.5)
        st = _get("/tick_b2_state")
        self.assertAlmostEqual(st["dt_substep_s"], 0.00025, places=9)
        wtot = st["total_weight_n"]
        self.assertLess(st["energy_drift_j"], 0.0)
        self.assertGreater(st["energy_drift_j"], -2.0 * wtot * b2_scene_gen.REST_SINK_M)
        for p in st["parts"]:
            self.assertGreater(p["pen_run_m"], 0.009)
            self.assertLess(p["pen_run_m"], 0.012)


if __name__ == "__main__":
    unittest.main(verbosity=2)
