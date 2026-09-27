"""U02 follow-camera tests — headless, stdlib-only, deterministic.

Proves the frozen prereg (tools/monkey_campaign/agents/U02_camera/
PREREGISTRATION.md, Amendments 1-4): the NEVER-moves-the-animal invariant on
the recorded command stream, the frozen obstruction cases against mocked
vertical cylinders, and the Python-side latency budgets (C12-compliant: the
20 Hz tick interval and the measured latencies are reported SEPARATELY).
The engine is MOCKED with declared deadlines; real-engine frame cost is a
recorded follow-up need (U07), not a claim made here.

Run from the repo root:
  python -m unittest tools.monkey_campaign.product.follow_camera_tests -v
"""
from __future__ import annotations

import json
import math
import unittest

from tools.monkey_campaign.product import follow_camera as fc
from tools.monkey_campaign.product.follow_camera import (
    Cylinder, FollowCamera, StaticAnchorProvider, RecordingClient,
    engine_eye, point_clear, ray_clear, subtend_deg_from_axis,
    TAN_HALF_FOV, HALF_FOV, PHI_MAX_GROUND, H_EYE_MIN,
    R_MAX, CameraConfigError,
)

# ---------------------------------------------------------------------------
# Frozen test constants (prereg "Frozen obstruction cases"; F01 bounds cited)
# ---------------------------------------------------------------------------

ANCHOR0 = (0.0, 0.0, 0.0)
MESH_R = 0.5                       # the /scene body-row mesh sphere mock
                                   # (the engine prints r with %.1f -- 0.5 is
                                   # exact under that display law)
JOINTS = [                         # rig mock: 6 joints, centroid = origin,
                                   # extent = 0.5 by construction; sized so
                                   # R_ground exceeds the frozen low-eye bound
    (0.5, 0.0, 0.0), (-0.5, 0.0, 0.0),
    (0.0, 0.5, 0.0), (0.0, -0.5, 0.0),
    (0.0, 0.0, 0.5), (0.0, 0.0, -0.5),
]
EXTENT = max(math.dist(j, ANCHOR0) for j in JOINTS)      # 0.5 by construction
R_SUBJECT = EXTENT + MESH_R
R_GROUND = R_SUBJECT / TAN_HALF_FOV * 1.05
PHI_MIN = math.asin(min(1.0, H_EYE_MIN / R_GROUND))
PHI_GROUND = 0.5 * (PHI_MIN + PHI_MAX_GROUND)

TRUNK = Cylinder(0.0, 0.0, 0.5, 3.0)   # F01 trunk footprint bound 0.5 m;
                                       # declared test height 3.0 m (F03 owns
                                       # the real geometry)
POST = Cylinder(-1.5, 1.0, 0.12, 0.9)  # F01 boundary post: h 0.9 m


def _framed(fcam, v):
    """FE: the anchor stays inside the frame for the commanded v."""
    eye = engine_eye(v)
    return subtend_deg_from_axis(eye, (v[3], v[4], v[5]),
                                 fcam._smoothed_anchor_ref) < HALF_FOV


def _base_v():
    """Base ground framing with no obstacles and no heading:
    [R_ground, 0, phi_ground, anchor, 0, 0]."""
    return (R_GROUND, 0.0, PHI_GROUND, 0.0, 0.0, 0.0, 0.0, 0.0)


# ---------------------------------------------------------------------------
# The mock engine (contract-level: same route shapes, engine laws clamped)
# ---------------------------------------------------------------------------


class MockEngine:
    """In-process fake of the engine's HTTP surface for the routes the module
    uses. Declared simulated deadlines: render-thread apply <= 1 frame at
    60 fps (1/60 s), /frame period 1/30 s. Real engine costs are NOT claimed.
    GET /frame answers JSON {"armed_after": <ack count>} so the harness can
    prove the freshness CONTRACT (the frame postdates the last camera ack)."""

    APPLY_DEADLINE_S = 1.0 / 60.0
    FRAME_PERIOD_S = 1.0 / 30.0

    def __init__(self, mesh_r=MESH_R, loaded=True):
        self.mesh_r = mesh_r
        self.loaded = loaded
        self.cam_v = (12.0, 0.0, 0.3, 0.0, 0.0, 0.0, 0.0, 0.0)
        self.log = []                       # (method, path, payload|None)
        self.ack_count = 0

    def get(self, path):
        path = path.split("?")[0]
        self.log.append(("GET", path, None))
        if path == "/joints":
            if not self.loaded:
                return 200, json.dumps({"loaded": False}).encode(), "application/json"
            doc = {"loaded": True, "n_joints": len(JOINTS),
                   "joints": [{"name": f"j{k}", "theta": 0.0,
                               "J": [j[0], j[1], j[2]], "axis": [0, 1, 0]}
                              for k, j in enumerate(JOINTS)],
                   "parents": [-1] * len(JOINTS)}
            return 200, json.dumps(doc).encode(), "application/json"
        if path == "/scene":
            # the REAL body-row format (engine.cpp scene_rows: "%u tris,
            # %u verts, r=%.1f") -- the r= value comes LAST
            scene = {"rows": [{"id": "body", "label": "body",
                               "detail": f"12 tris, 8 verts, r={self.mesh_r:.1f}",
                               "state": 1, "toggleable": False}]}
            return 200, json.dumps(scene).encode(), "application/json"
        if path == "/frame":
            return 200, json.dumps(
                {"armed_after": self.ack_count}).encode(), "application/json"
        return 404, b'{"ok":false,"error":"unknown route"}', "application/json"

    def post_json(self, path, payload, timeout=None):
        path = path.split("?")[0]
        self.log.append(("POST", path, dict(payload)))
        if path == "/camera":
            for k in ("cam_radius", "cam_theta", "cam_phi", "pan_x", "pan_y",
                      "target_x", "target_y", "target_z"):
                if k not in payload:        # the always-send-all-8 law
                    return 400, b'{"ok":false,"error":"missing field"}'
            r = max(max(1.0, 1.02 * self.mesh_r), float(payload["cam_radius"]))
            self.cam_v = (r, float(payload["cam_theta"]),
                          float(payload["cam_phi"]),
                          float(payload["target_x"]), float(payload["target_y"]),
                          float(payload["target_z"]),
                          float(payload["pan_x"]), float(payload["pan_y"]))
            self.ack_count += 1
            return 200, b'{"ok":true}'
        if path == "/project":
            cam = [round(float(x), 5) for x in self.cam_v]  # engine %.5f echo
            return 200, json.dumps({"ok": True, "sx": 0.0, "sy": 0.0,
                                    "cam": cam}).encode()
        return 404, b'{"ok":false,"error":"unknown route"}'


def make_camera(obstacles=(), provider=None, mock=None, **kw):
    mock = mock if mock is not None else MockEngine()
    rec = RecordingClient(mock)
    prov = provider if provider is not None else \
        StaticAnchorProvider(ANCHOR0, extent=EXTENT)
    fcam = FollowCamera(rec, prov, obstacles=obstacles,
                        mesh_r=mock.mesh_r, **kw)
    fcam.bind()
    return mock, rec, fcam


# ---------------------------------------------------------------------------
# Derived framing + strict intake
# ---------------------------------------------------------------------------


class TestDerivedFraming(unittest.TestCase):

    def test_frozen_constants_match_independent_derivation(self):
        _m, _r, fcam = make_camera()
        self.assertAlmostEqual(fcam.r_subject, R_SUBJECT, places=9)
        self.assertAlmostEqual(fcam.r_ground, R_GROUND, places=9)
        self.assertAlmostEqual(fcam.phi_ground, PHI_GROUND, places=9)
        self.assertAlmostEqual(fcam.r_floor, max(1.0, 1.02 * MESH_R), places=9)

    def test_engine_rig_provider_reads_the_contract(self):
        mock = MockEngine()
        rec = RecordingClient(mock)
        prov = fc.EngineRigProvider(rec)
        fcam = FollowCamera(rec, prov, obstacles=(), mesh_r=None)
        fcam.bind()
        self.assertAlmostEqual(fcam.r_subject, R_SUBJECT, places=6)
        issued = {(m, p) for m, p, _ in rec.log}
        self.assertEqual(issued, {("GET", "/scene"), ("GET", "/joints")})

    def test_bind_refuses_unloaded_rig(self):
        with self.assertRaises(CameraConfigError):
            make_camera(mock=MockEngine(loaded=False),
                        provider=fc.EngineRigProvider(
                            RecordingClient(MockEngine(loaded=False))))

    def test_strict_intake_rejects_bad_construction(self):
        with self.assertRaises(CameraConfigError):
            Cylinder(0, 0, -1.0, 3.0)
        with self.assertRaises(CameraConfigError):
            FollowCamera(RecordingClient(MockEngine()),
                         StaticAnchorProvider(ANCHOR0), tau=0.0)
        with self.assertRaises(CameraConfigError):
            StaticAnchorProvider((0.0, float("nan"), 0.0))

    def test_low_eye_priority_law_records_hint(self):
        """Amendment 1.2: when the eye-height bound is unreachable the feet
        criterion wins, phi = PHI_MAX_GROUND, and the hint is recorded."""
        _m, _r, fcam = make_camera(provider=StaticAnchorProvider(ANCHOR0,
                                                                 extent=0.10))
        self.assertAlmostEqual(fcam.phi_ground, PHI_MAX_GROUND, places=9)
        self.assertEqual(fcam._low_eye_hint, "low_eye")
        rep = fcam.tick()                      # and it still works
        self.assertFalse(rep.degraded)
        self.assertAlmostEqual(rep.commanded_v[2], PHI_MAX_GROUND, places=9)

    def test_ground_mode_first_command(self):
        mock, rec, fcam = make_camera()
        rep = fcam.tick()
        self.assertEqual(rep.mode, "ground")
        self.assertTrue(rep.wrote)
        issued = {(m, p) for m, p, _ in rec.log}
        self.assertEqual(issued, {("POST", "/camera")},
                         "the tick path must issue exactly one write")
        v = rep.commanded_v
        self.assertAlmostEqual(v[0], R_GROUND, places=9)
        self.assertAlmostEqual(v[2], PHI_GROUND, places=9)
        self.assertEqual(v[3:6], ANCHOR0)
        self.assertEqual(v[6], 0.0)
        self.assertEqual(v[7], 0.0)
        self.assertTrue(_framed(fcam, v))


# ---------------------------------------------------------------------------
# FA: the never-moves-the-animal invariant, on the recorded command stream
# ---------------------------------------------------------------------------


class TestNoForceInvariant(unittest.TestCase):

    SCENARIOS = {"clean": (), "trunk": (TRUNK,), "post": (POST,),
                 "both": (TRUNK, POST)}

    def test_allowlist_and_pan_across_scenarios(self):
        for name, obstacles in self.SCENARIOS.items():
            with self.subTest(scenario=name):
                _m, rec, fcam = make_camera(obstacles)
                for _ in range(12):
                    rep = fcam.tick()
                    self.assertFalse(rep.cut)
                self.assertEqual(rec.allowlist_violations(), [],
                                 f"allowlist violated in {name}")
                self.assertEqual(rec.forbidden_hits(), [],
                                 f"forbidden route touched in {name}")
                for payload in rec.camera_writes():
                    for k in ("cam_radius", "cam_theta", "cam_phi", "pan_x",
                              "pan_y", "target_x", "target_y", "target_z"):
                        self.assertIn(k, payload, f"{k} missing in {name}")
                    self.assertEqual(payload["pan_x"], 0.0)
                    self.assertEqual(payload["pan_y"], 0.0)

    def test_body_moving_routes_never_issued(self):
        _m, rec, fcam = make_camera((TRUNK,))
        for _ in range(5):
            fcam.tick()
            fcam.verify_apply()
        issued = {(m, p) for m, p, _ in rec.log}
        for forbidden in ("/membrane", "/mesh_bin", "/joints_bin", "/hinge_bin",
                          "/gait", "/stride", "/pose_apply", "/cameras"):
            self.assertNotIn(("POST", forbidden), issued)

    def test_no_command_carries_body_shaped_fields(self):
        _m, rec, fcam = make_camera((TRUNK,))
        for _ in range(3):
            fcam.tick()
        body_shaped = ("force", "torque", "teleport", "pos", "qpos", "theta",
                       "hinge", "stride", "gait", "term", "count")
        for _m, _p, payload in rec.log:
            if isinstance(payload, dict):
                for k in body_shaped:
                    self.assertNotIn(k, payload)


# ---------------------------------------------------------------------------
# The frozen obstruction cases (geometries derived from the frozen camera law)
# ---------------------------------------------------------------------------


class TestObstructionCases(unittest.TestCase):

    def test_OC4_clean_scene_is_bitwise_noop(self):
        _m, _r, fcam = make_camera(())
        rep1 = fcam.tick()
        rep2 = fcam.tick()
        self.assertTrue(rep1.wrote)
        self.assertFalse(rep2.wrote, "idle tick must be deadband-silent")
        for got, want in zip(rep1.commanded_v, _base_v()):
            self.assertAlmostEqual(got, want, delta=1e-9)
        self.assertEqual(rep1.avoidance.get("order"), [])

    def test_OC1_tall_pole_on_sightline_resolved_by_height_law(self):
        # a tall THIN pole (r=0.15 < the 0.25 trunk designation bound) never
        # becomes "the trunk" (Amendment 5): ground mode keeps, and the
        # height law must lift the camera over it
        eye = engine_eye(_base_v())
        cx = eye[0] + 0.6 * (ANCHOR0[0] - eye[0])
        cz = eye[2] + 0.6 * (ANCHOR0[2] - eye[2])
        obst = (Cylinder(cx, cz, 0.15, 3.0),)    # 60% along the sight line
        _m, _r, fcam = make_camera(obst)
        rep = fcam.tick()
        self.assertEqual(rep.mode, "ground")
        self.assertFalse(rep.degraded, rep.degrade_reason)
        self.assertNotIn("pull_in", rep.avoidance.get("order", []),
                         "eye was clear: pull-in must be skipped (Amend 3.1)")
        self.assertIn("height_radius", rep.avoidance.get("order", []),
                      "a tall mid-line pole must be looked over")
        v = rep.commanded_v
        self.assertLessEqual(v[0], R_MAX)
        f_eye, f_target = engine_eye(v), (v[3], v[4], v[5])
        for o in obst:
            self.assertTrue(point_clear(f_eye, o), "eye not clear")
            self.assertTrue(ray_clear(f_eye, f_target, o), "look-ray not clear")
        self.assertLess(subtend_deg_from_axis(f_eye, f_target, ANCHOR0),
                        HALF_FOV, "anchor left the frame")
        self.assertGreaterEqual(v[0], fcam.r_ground - 1e-9)

    def test_trunk_designation_law(self):
        """Amendment 5: a post-only scene has NO trunk-approach mode."""
        _m, _r, fcam = make_camera((POST,))
        self.assertIsNone(fcam._trunk)
        rep = fcam.tick()
        self.assertEqual(rep.mode, "ground")
        # a trunk-scale cylinder designates fine
        _m2, _r2, fcam2 = make_camera((POST, TRUNK))
        self.assertIsNotNone(fcam2._trunk)
        self.assertEqual(fcam2._trunk.r, TRUNK.r)

    def test_OC2_eye_trapped_near_trunk_resolved(self):
        eye = engine_eye(_base_v())
        cz = eye[2] + 0.60          # eye->anchor line, 0.60 m from the eye
        self.assertLess(abs(eye[2] - cz), 0.75,
                        "setup: eye must start inside the margin disk")
        self.assertGreater(abs(ANCHOR0[2] - cz), 0.75,
                           "setup: anchor must be outside the margin disk")
        obst = (Cylinder(0.0, cz, 0.5, 3.0),)
        _m, _r, fcam = make_camera(obst)
        rep = fcam.tick()
        self.assertFalse(rep.degraded, rep.degrade_reason)
        v = rep.commanded_v
        f_eye, f_target = engine_eye(v), (v[3], v[4], v[5])
        for o in obst:
            self.assertTrue(point_clear(f_eye, o), "eye not clear")
            self.assertTrue(ray_clear(f_eye, f_target, o), "look-ray not clear")
        self.assertLess(subtend_deg_from_axis(f_eye, f_target, ANCHOR0),
                        HALF_FOV)

    def test_OC3_trunk_approach_framing_keeps_both_visible(self):
        anchor = (1.0, 0.0, 0.0)      # 1.0 m from the trunk axis: approach
        _m, _r, fcam = make_camera((TRUNK,),
                                   provider=StaticAnchorProvider(anchor,
                                                                 extent=EXTENT))
        rep = fcam.tick()
        self.assertEqual(rep.mode, "trunk")
        self.assertFalse(rep.degraded, rep.degrade_reason)
        v = rep.commanded_v
        f_eye, f_target = engine_eye(v), (v[3], v[4], v[5])
        self.assertTrue(point_clear(f_eye, TRUNK))
        self.assertTrue(ray_clear(f_eye, f_target, TRUNK))
        self.assertLess(subtend_deg_from_axis(f_eye, f_target, anchor), HALF_FOV)
        contact = (TRUNK.cx + TRUNK.r, 0.0, TRUNK.cz)   # surface, anchor side
        self.assertLess(subtend_deg_from_axis(f_eye, f_target, contact),
                        HALF_FOV)

    def test_OC3b_unreachable_geometry_degrades_honestly(self):
        anchor = (0.5, 0.0, 0.0)      # pressed against the trunk surface
        tall = Cylinder(0.0, 0.0, 0.5, 50.0)   # 50 m: unoverlookable at 40 m
        _m, _r, fcam = make_camera((tall,),
                                   provider=StaticAnchorProvider(anchor,
                                                                 extent=EXTENT))
        rep = fcam.tick()
        self.assertTrue(rep.degraded,
                        "impossible geometry MUST report degraded, not fake it")
        self.assertTrue(rep.degrade_reason)
        self.assertEqual(rep.commanded_v[6], 0.0)   # even degraded: pan 0
        self.assertEqual(rep.commanded_v[7], 0.0)

    def test_OC5_off_line_and_flyover_obstacles_do_not_fire(self):
        eye = engine_eye(_base_v())
        off_line = Cylinder(1.0, 0.5, 0.12, 0.9)
        on_line_below = Cylinder(eye[0], eye[2] * 0.4945, 0.12, 0.01)
        for name, obst in (("off_line", (off_line,)),
                           ("flyover", (on_line_below,))):
            with self.subTest(case=name):
                _m, _r, fcam = make_camera(obst)
                rep = fcam.tick()
                self.assertEqual(rep.avoidance.get("order"), [],
                                 "must not fire on flyovers/off-line posts")
                for got, want in zip(rep.commanded_v, _base_v()):
                    self.assertAlmostEqual(got, want, delta=1e-9)

    def test_OC6_hysteresis_latches_then_releases(self):
        eye = engine_eye(_base_v())
        z0 = eye[2]
        _m, _r, fcam = make_camera((Cylinder(0.30, z0, 0.12, 0.9),))
        rep1 = fcam.tick()
        self.assertFalse(rep1.degraded, rep1.degrade_reason)
        self.assertGreater(rep1.commanded_v[2], PHI_GROUND + 0.1,
                           "setup: tick1 must have engaged avoidance")
        # clears by LESS than the latch: the solution persists
        fcam.obstacles = (Cylinder(0.45, z0, 0.12, 0.9),)
        rep2 = fcam.tick()
        self.assertEqual(rep2.avoidance.get("order"), ["latch"],
                         "an engaged avoidance must persist within hysteresis")
        self.assertAlmostEqual(rep2.commanded_v[2], rep1.commanded_v[2],
                               places=6)
        # clears by MORE than the latch: back to the base framing
        fcam.obstacles = (Cylinder(0.70, z0, 0.12, 0.9),)
        rep3 = fcam.tick()
        self.assertEqual(rep3.avoidance.get("order"), [])
        self.assertAlmostEqual(rep3.commanded_v[0], R_GROUND, places=6)
        self.assertAlmostEqual(rep3.commanded_v[2], PHI_GROUND, places=6)

    def test_OC7_pull_in_takes_the_largest_feasible_radius(self):
        # derived per Amendment 3.1: cylinder near the EYE of a WIDE base pose
        # (R = 4.0 > R_ground): the eye exits the margin disk near R' ~= 2.8
        anchor = ANCHOR0
        base_r = 4.0
        theta = math.pi
        phi = PHI_GROUND
        eye_z = base_r * math.cos(phi)
        obst = (Cylinder(0.0, eye_z - 0.366, 0.5, 2.0),)  # eye inside margin
        _m, _r, fcam = make_camera(obst)
        fcam._smoothed_anchor_ref = anchor
        r_out, th_out, ph_out, info = fcam._avoid(anchor, base_r, theta, phi)
        self.assertIn("pull_in", info["order"])
        self.assertGreaterEqual(r_out, fcam.r_ground - 1e-9)
        e = engine_eye((r_out, th_out, ph_out, 0.0, 0.0, 0.0, 0.0, 0.0))
        for o in obst:
            self.assertTrue(point_clear(e, o))
            self.assertTrue(ray_clear(e, anchor, o))
        # maximality: nothing in (r_out, base_r] may be a clear EYE
        step = max(1e-3, (base_r - r_out) / 8.0)
        r_probe = r_out + step
        while r_probe <= base_r:
            e_probe = engine_eye((r_probe, theta, phi,
                                  0.0, 0.0, 0.0, 0.0, 0.0))
            self.assertFalse(point_clear(e_probe, obst[0]),
                             "a larger clear radius existed: scan not maximal")
            r_probe += step


# ---------------------------------------------------------------------------
# FF: smoothing, speed bound, cut policy
# ---------------------------------------------------------------------------


class TestSmoothingAndSpeed(unittest.TestCase):

    def test_camera_speed_bounded_by_twice_animal_speed(self):
        class Walker:
            def __init__(self):
                self.t = 0.0
                self.p = (3.0, 0.0, 0.0)     # starts outside the trunk ring

            def read(self):
                self.t += 0.05
                x, _y, z = self.p
                self.p = (x + 0.02, 0.0, z + 0.01)
                return fc.AnchorReading(self.p, (0.02, 0.01), self.t)

        _m, _r, fcam = make_camera((TRUNK,), provider=Walker())
        prev_target = None
        for _ in range(30):
            rep = fcam.tick()
            if prev_target is not None and rep.wrote and not rep.cut:
                step = math.dist(rep.commanded_v[3:6], prev_target)
                bound = max(0.05, 2.0 * rep.v_animal) * 0.05
                self.assertLessEqual(step, bound + 1e-6,
                                     "camera outran the animal (FF hit)")
            prev_target = rep.commanded_v[3:6]

    def test_cut_policy_snaps_on_teleport_scale_jump(self):
        pts = [(0.0, 0.0, 0.0), (0.001, 0.0, 0.0), (30.0, 0.0, 30.0)]

        class Teleporter:
            def __init__(self):
                self.i = 0
                self.t = 0.0

            def read(self):
                self.t += 0.05
                p = pts[min(self.i, len(pts) - 1)]
                self.i += 1
                return fc.AnchorReading(p, None, self.t)

        _m, _r, fcam = make_camera((), provider=Teleporter())
        rep1 = fcam.tick()
        rep2 = fcam.tick()          # the teleport lands on tick 2
        self.assertFalse(rep1.cut)
        self.assertTrue(rep2.cut, "teleport-scale jump must be a declared cut")
        self.assertAlmostEqual(rep2.commanded_v[3], 30.0, places=6)
        self.assertAlmostEqual(rep2.commanded_v[5], 30.0, places=6)


# ---------------------------------------------------------------------------
# FD: latency budgets (C12-compliant) + the /frame freshness contract
# ---------------------------------------------------------------------------


class TestLatencyBudgets(unittest.TestCase):

    def test_budgets_and_freshness_contract(self):
        _m, _r, fcam = make_camera((TRUNK,))
        rows = []
        compute_max = roundtrip_max = chain_max = pres_max = 0.0
        for i in range(50):
            rep = fcam.tick()
            compute = (rep.t_solution - rep.t_anchor) * 1e3
            if rep.wrote:
                roundtrip = (rep.t_acked - rep.t_solution) * 1e3
                chain = (rep.t_acked - rep.t_state) * 1e3
                # presentation: chain + the mock's DECLARED deadlines
                pres = chain + (MockEngine.APPLY_DEADLINE_S
                                + MockEngine.FRAME_PERIOD_S) * 1e3
            else:
                roundtrip = chain = pres = 0.0
            compute_max = max(compute_max, compute)
            roundtrip_max = max(roundtrip_max, roundtrip)
            chain_max = max(chain_max, chain)
            pres_max = max(pres_max, pres)
            rows.append({"i": i, "mode": rep.mode, "wrote": rep.wrote,
                         "compute_ms": round(compute, 4),
                         "roundtrip_ms": round(roundtrip, 4),
                         "presentation_est_ms": round(pres, 3),
                         "degraded": rep.degraded})
        # (a) the module must never be the bottleneck of its own 20 Hz tick
        self.assertLessEqual(chain_max, 50.0,
                             "state->ack chain exceeded one command interval")
        # (b) presentation with the declared mock deadlines vs the F2 law
        self.assertLessEqual(pres_max, 200.0, "presentation budget exceeded")
        # freshness CONTRACT: a /frame requested now must arm at/after the
        # last camera ack (the mock encodes the ack count)
        acks_before = _m.ack_count
        _st, body, _ct = _m.get("/frame")
        armed = json.loads(body.decode())["armed_after"]
        self.assertGreaterEqual(armed, acks_before,
                                "/frame did not postdate the last camera ack")
        import pathlib
        out = (pathlib.Path(__file__).resolve().parents[1]
               / "agents" / "U02_camera" / "receipts")
        out.mkdir(parents=True, exist_ok=True)
        (out / "latency_run.json").write_text(json.dumps({
            "clock": "time.perf_counter (host wall)",
            "tick_setpoint_ms": 50.0,
            "NOTE": "the 20 Hz tick setpoint is NOT a latency claim (C12); "
                    "presentation adds the mock's DECLARED deadlines; the "
                    "real engine frame cost is U07's follow-up need",
            "max_compute_ms": round(compute_max, 4),
            "max_roundtrip_ms": round(roundtrip_max, 4),
            "max_state_to_ack_chain_ms": round(chain_max, 4),
            "max_presentation_est_ms": round(pres_max, 3),
            "budgets_ms": {"python_state_to_ack": 50.0,
                           "presentation_mock_deadlines": 200.0},
            "ticks": rows}, indent=1))


# ---------------------------------------------------------------------------
# FG: the apply echo (the engine must have APPLIED our camera)
# ---------------------------------------------------------------------------


class TestApplyEcho(unittest.TestCase):

    def test_echo_matches_command(self):
        mock, _r, fcam = make_camera((TRUNK,))
        rep = fcam.tick()
        self.assertTrue(rep.wrote)
        verdict = fcam.verify_apply()
        self.assertTrue(verdict["ok"], f"echo mismatch: {verdict}")

    def test_echo_detects_a_failed_apply(self):
        mock, _r, fcam = make_camera(())
        fcam.tick()
        mock.cam_v = (12.0, 0.0, 0.3, 0.0, 0.0, 0.0, 0.0, 0.0)  # sim. no-apply
        verdict = fcam.verify_apply()
        self.assertFalse(verdict["ok"], "echo check must not be vacuous")


# ---------------------------------------------------------------------------
# Heading follow (the derived theta law)
# ---------------------------------------------------------------------------


class TestHeadingFollow(unittest.TestCase):

    def test_camera_places_itself_behind_the_heading(self):
        class East:
            def __init__(self):
                self.t = 0.0

            def read(self):
                self.t += 0.05
                return fc.AnchorReading((0.0, 0.0, 0.0), (1.0, 0.0), self.t)

        _m, _r, fcam = make_camera((), provider=East())
        rep = fcam.tick()
        theta = rep.commanded_v[1]
        self.assertAlmostEqual(math.sin(theta), -1.0, places=6,
                               msg="theta_des = atan2(-hx, hz)")
        eye = engine_eye(rep.commanded_v)
        self.assertLess(eye[0], 0.0, "camera must sit behind a +x heading")


if __name__ == "__main__":
    unittest.main(verbosity=2)
