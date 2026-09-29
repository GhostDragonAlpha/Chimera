"""Focused unit tests for MAT2-F07's frozen vocabulary and audits.

Fast: no capture frames, no full build. The pinned inputs are loaded once.
"""
from __future__ import annotations

import importlib.util
import json
import math
import pathlib
import struct
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
CONTRIB = HERE.parent
sys.path.insert(0, str(CONTRIB.parent))

spec = importlib.util.spec_from_file_location("f07_impl", HERE / "implementation.py")
impl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(impl)

PINS = impl.load_pins()
TB, TQ, CR, LC, F = impl.load_modules(PINS)
BUNDLE = TB.loads((impl.CONTRIB / impl.PINS["terrain_bundle_json"]["rel"]).read_bytes())
SURFACE = TQ.TerrainSurface(BUNDLE, validate=False)
OBSTACLES = None   # built once in setUpClass


def build_scene():
    rng = CR.SplitMix64(impl.SEED)
    placed = impl.place_obstacles(rng, SURFACE)
    return impl.build_obstacle_meshes(placed, SURFACE)


class DeterminismAndVocabulary(unittest.TestCase):
    """P8 foundation: the splitmix64 draws are stable; the placement obeys
    every frozen constraint; meshes are watertight vocabulary instances."""

    @classmethod
    def setUpClass(cls):
        global OBSTACLES
        OBSTACLES = build_scene()

    def test_placement_deterministic(self):
        again = build_scene()
        self.assertEqual([o["centre_m"] for o in OBSTACLES],
                         [o["centre_m"] for o in again])
        self.assertEqual([o["verts"] for o in OBSTACLES],
                         [o["verts"] for o in again])

    def test_placement_constraints(self):
        for ob in OBSTACLES:
            cx, _, cz = ob["centre_m"]
            fr = ob["footprint_radius_m"]
            self.assertLessEqual(max(abs(cx), abs(cz)),
                                 impl.EXTENT_HALF_M - impl.PLACEMENT_MARGIN_M,
                                 ob["id"])
            self.assertGreaterEqual(math.hypot(cx, cz),
                                    impl.SPAWN_MIN_DIST_M, ob["id"])
            self.assertGreaterEqual(
                math.hypot(cx - impl.TRUNK_SITE_M[0], cz - impl.TRUNK_SITE_M[2]),
                impl.TRUNK_MIN_DIST_M, ob["id"])
            for other in OBSTACLES:
                if other is ob:
                    continue
                need = fr + other["footprint_radius_m"] \
                    + 2.0 * impl.BLOCK_INFLATION_M + impl.PAIR_GAP_M
                self.assertGreaterEqual(
                    math.hypot(cx - other["centre_m"][0],
                               cz - other["centre_m"][2]), need,
                    (ob["id"], other["id"]))

    def test_vocabulary_counts(self):
        kinds = [ob["kind"] for ob in OBSTACLES]
        self.assertEqual(kinds.count("rock"), 3)
        self.assertEqual(kinds.count("log"), 2)
        self.assertEqual(kinds.count("stand"), 2)
        for ob in OBSTACLES:
            if ob["kind"] == "rock":
                self.assertEqual(len(ob["verts"]), 12)
                self.assertEqual(len(ob["tris"]), 20)
            elif ob["kind"] == "log":
                self.assertEqual(len(ob["verts"]), 2 * impl.RING_N)
            else:
                self.assertEqual(len(ob["verts"]),
                                 impl.SAPLING_COUNT * 2 * impl.RING_N)

    def test_rock_hull_watertight_and_solid(self):
        ob = OBSTACLES[0]
        edges = {}
        for tri in ob["tris"]:
            for x, y in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
                key = (min(x, y), max(x, y))
                edges[key] = edges.get(key, 0) + 1
        self.assertEqual(len(edges), 30)
        self.assertTrue(all(v == 2 for v in edges.values()))
        mid = (sum(v[0] for v in ob["verts"]) / len(ob["verts"]),
               (min(v[1] for v in ob["verts"])
                + max(v[1] for v in ob["verts"])) / 2.0,
               sum(v[2] for v in ob["verts"]) / len(ob["verts"]))
        self.assertGreater(impl.hull_depth(ob["verts"], ob["faces"], mid), 0.0)
        outside = (max(v[0] for v in ob["verts"]) + 1.0, mid[1], mid[2])
        self.assertEqual(impl.hull_depth(ob["verts"], ob["faces"], outside),
                         0.0)
        bottom = (min(ob["verts"], key=lambda v: v[1]))
        self.assertGreaterEqual(impl.hull_depth(ob["verts"], ob["faces"],
                                                bottom[:3]), 0.0)

    def test_prism_facet_alignment(self):
        ob = OBSTACLES[3]  # a log
        r = ob["log_radius_m"]
        face = r * math.cos(math.pi / impl.RING_N)
        cz = ob["centre_m"][2]
        if ob["yaw_index"] == 0:
            on_plane = [v for v in ob["verts"] if abs(v[2] - (cz + face)) < 1e-6]
            self.assertEqual(len(on_plane), 4)   # 2 rings x 2 facet vertices
            cx = ob["centre_m"][0]
            self.assertTrue(all(abs(v[0] - cx) <= ob["log_length_m"] / 2.0 + 1e-9
                                for v in on_plane))
        point, normal = impl.facet_plane(ob)
        self.assertIn(normal, [(1.0, 0.0, 0.0), (0.0, 0.0, 1.0)])
        # the facet plane point lies ON the declared plane
        self.assertAlmostEqual(sum((point[i]) * normal[i] for i in range(3))
                               - (sum((ob["centre_m"][i]) * normal[i]
                                      for i in range(3)) + face), 0.0,
                               places=6)

    def test_solid_depth_prism(self):
        ob = OBSTACLES[3]
        p = ob["centre_m"]
        verts = [impl.F_TO_CONTACT(v) for v in ob["verts"]]
        tris = [tuple(t) for t in ob["tris"]]
        self.assertGreater(impl.solid_depth(verts, tris,
                                            impl.F_TO_CONTACT(
                                                (p[0], p[1] + 0.5 * ob["log_radius_m"],
                                                 p[2]))), 0.0)
        far = impl.F_TO_CONTACT((p[0], p[1] + 50.0, p[2]))
        self.assertEqual(impl.solid_depth(verts, tris, far), 0.0)

    def test_impact_start_normal_incidence(self):
        for ob in OBSTACLES:
            start, vel, axis = impl.impact_start(ob)
            point, normal = impl.facet_plane(ob)
            dot = sum(vel[i] * normal[i] for i in range(3))
            self.assertAlmostEqual(abs(dot), impl.IMPACT_SPEED_M_S, places=9)
            gap = sum((start[i] - point[i]) * normal[i] for i in range(3))
            self.assertAlmostEqual(gap, impl.IMPACT_START_CLEAR_M, places=9)


class DeclarationAndAudits(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global OBSTACLES
        if OBSTACLES is None:
            OBSTACLES = build_scene()

    def test_declaration_self_hash_roundtrip(self):
        decl, raw, sha = impl.make_declaration(OBSTACLES)
        reloaded = json.loads(raw)
        body = {k: v for k, v in reloaded.items() if k != "self_sha256"}
        self.assertEqual(reloaded["self_sha256"], impl.sha_bytes(impl.canonical(body)))
        self.assertEqual(decl["boundaries"][0]["id"], "extent_rule")
        self.assertEqual(decl["boundaries"][0]["behavior"], "refuse_out_of_patch")

    def test_mask_attribution_clean(self):
        mask, attr = impl.build_mask(OBSTACLES, SURFACE)
        audit = impl.attribution_audit(mask, attr)
        self.assertEqual(audit["unattributed_count"], 0)
        self.assertGreater(sum(sum(r) for r in mask), 0)
        declared = ({ob["id"] for ob in OBSTACLES}
                    | {"extent_rule", "terrain_slope_rule", "trunk_01"})
        for key in audit["blocked_by_record"]:
            self.assertIn(key, declared)

    def test_mask_injection_bites(self):
        mask, attr = impl.build_mask(OBSTACLES, SURFACE,
                                     inject=(impl.FB1_INJECT_SITE[0],
                                             impl.FB1_INJECT_SITE[1], 1.0))
        audit = impl.attribution_audit(mask, attr)
        self.assertGreaterEqual(audit["unattributed_count"], 1)

    def test_routes_exist_and_metrics(self):
        routes, reach = impl.verify_routes(OBSTACLES, SURFACE)
        self.assertEqual(len(routes), 12)   # trunk + 4 edges + 7 obstacles
        for name, rec in routes.items():
            self.assertTrue(rec["reached"], name)
            self.assertGreaterEqual(rec["min_footprint_clearance_m"],
                                    impl.BLOCK_INFLATION_M - 1e-9)
            self.assertLessEqual(rec["max_sampled_slope"], impl.SLOPE_BAR)

    def test_fenced_spawn_reaches_nothing(self):
        fence = [{"id": "fence_%d" % k, "kind": "rock",
                  "centre_m": [math.cos(2.0 * math.pi * k / 8.0) * 1.2, 0.0,
                               math.sin(2.0 * math.pi * k / 8.0) * 1.2],
                  "extent_m": [0.5, 0.5, 0.5], "surface_id": "fence_%d" % k}
                 for k in range(8)]
        mask, _ = impl.build_mask(fence, SURFACE)
        free = impl.free_cells(mask)
        start = (impl.MASK_N // 2, impl.MASK_N // 2)
        self.assertIn(start, free)
        reach = impl.bfs_reachable(start, free)
        self.assertEqual(len(reach), 1)     # the spawn cell only
        for name, (tx, tz) in impl.destination_table(OBSTACLES).items():
            nr = impl.nearest_reachable(reach, tx, tz)
            self.assertTrue(nr is None or nr[0] > impl.MAX_VIEWPOINT_OFFSET_M,
                            name)

    def test_stop_declaration_audit_fires(self):
        clean_mask, _ = impl.build_mask(OBSTACLES, SURFACE)
        full = impl.boundary_records()
        stubs = [{"id": ob["id"]} for ob in OBSTACLES]
        ok = impl.stop_declaration_audit(
            {"rock_01": 3, "extent_rule": 40, "terrain_slope_rule": 0},
            ["rock_01"], full + stubs)
        self.assertEqual(ok["undeclared_stops"], [])
        broken = impl.stop_declaration_audit(
            {"rock_01": 3, "extent_rule": 40}, ["rock_01"],
            [r for r in full if r["id"] != "extent_rule"] + stubs)
        self.assertEqual(broken["undeclared_stops"], ["extent_rule"])

    def test_render_collision_identity(self):
        sets = impl.render_collision_set_identity(OBSTACLES)
        self.assertTrue(sets["identity"])
        self.assertEqual(sets["collision_surfaces"],
                         sorted(ob["id"] for ob in OBSTACLES))

    def test_arrays_equal_detects_decouple(self):
        a = [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]
        b = [[0.0, 0.0, 0.0], [1.0, 0.01, 0.0]]
        self.assertFalse(impl.arrays_equal(a, b))
        self.assertTrue(impl.arrays_equal(a, [list(x) for x in a]))


class CameraAndCapture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global OBSTACLES
        if OBSTACLES is None:
            OBSTACLES = build_scene()
        trunk = json.loads(
            (impl.CONTRIB / impl.PINS["trunk_declaration_json"]["rel"])
            .read_bytes())
        groups, _ = F.trunk_partition(trunk)
        tverts = [F.to_contact(v[0:3])
                  for v in trunk["render_mesh"]["vertices"]]
        cls.mesh = impl.SceneMesh07(BUNDLE, tverts, groups, OBSTACLES)
        cls.cams = {k: impl.Camera07(s) for k, s in impl.VIEW_SPECS.items()}

    def test_camera_record_fields(self):
        rec = self.cams["V1_clearing_overview"].camera_record([0])
        for field in ("frame_id", "coordinate_unit", "position", "target",
                      "distance_to_target", "projection",
                      "vertical_fov_degrees", "near_far_planes",
                      "aspect_ratio", "viewport_resolution",
                      "orientation_convention", "forward_axis", "up_axis",
                      "handedness", "sample_mode", "samples",
                      "occlusion_or_xray_mode",
                      "camera_record_16field_convention"):
            self.assertIn(field, rec)
        conv = rec["camera_record_16field_convention"]
        for field in ("orientation_convention_and_values",
                      "camera_motion_or_bookmark_sequence",
                      "state_or_tick_interval", "visibility_layers",
                      "label_ids", "vertical_fov_or_orthographic_span_deg"):
            self.assertIn(field, conv)
        q = rec["samples"][0]["orientation"]
        self.assertAlmostEqual(math.hypot(*q), 1.0, places=9)
        self.assertAlmostEqual(rec["aspect_ratio"], 960 / 540, places=9)
        self.assertEqual(rec["sample_mode"], "fixed_bookmark")

    def test_camera_distance_matches(self):
        for cam in self.cams.values():
            d = math.sqrt(sum((cam.position[i] - cam.target[i]) ** 2
                              for i in range(3)))
            self.assertAlmostEqual(cam.distance_to_target, d, places=9)

    def test_classify_off_frame_behind_camera(self):
        marker = {"point": (0.0, 0.5, 10.0), "surface": "trunk_01.lateral",
                  "kind": "trunk", "id": "x"}
        out = impl.classify_marker(self.mesh, self.cams["V2_seam_closeup"],
                                   marker)
        self.assertEqual(out["outcome"], "OFF_FRAME")

    def test_transform_selftest_on_synthetic_bmp(self):
        path = HERE / "evidence" / "_test_frame.bmp"
        path.parent.mkdir(exist_ok=True)
        colour = [[(1, 2, 3)] * impl.W for _ in range(impl.H)]
        colour[0][0] = (250, 251, 252)
        impl.write_bmp(path, colour)
        try:
            res = impl.transform_selftest(path)
            self.assertTrue(res["identity_ok"])
            self.assertTrue(res["vflip_refused"])
            self.assertEqual(res["resolution"], [impl.W, impl.H])
        finally:
            path.unlink(missing_ok=True)

    def test_post_ring_audit(self):
        clearing_decl = json.loads(
            (impl.CONTRIB / impl.PINS["clearing_declaration_json"]["rel"])
            .read_bytes())
        audit = impl.post_ring_audit(BUNDLE, SURFACE, clearing_decl)
        self.assertTrue(audit["within_declared_gap"])
        self.assertEqual(audit["post_bases"], 80)
        self.assertLessEqual(audit["worst_gap_to_post_m"],
                             impl.EDGE_COVERAGE_BAR_M)
        self.assertLessEqual(audit["post_vertex_band_m"],
                             impl.POST_VERTEX_BAND_M)


if __name__ == "__main__":
    unittest.main()
