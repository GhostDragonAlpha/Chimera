"""MAT2-F04 frozen regression suite (offline, CPU-only, stdlib).

Runs against the committed implementation on the exact candidate revision.
The full build is exercised separately (`python -B implementation.py build`,
then `verify` for determinism); these tests pin the frozen identities,
refusals and falsifier forms without re-rendering the capture.
"""
from __future__ import annotations

import json
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import implementation as impl  # noqa: E402


def _assets():
    pins = impl.load_pins()
    tb, tq, lc = impl.load_modules(pins)
    bundle = tb.loads(
        (impl.CONTRIB / impl.PINS["terrain_bundle_json"]["rel"]).read_bytes())
    tb.validate_bundle(bundle)
    surface = tq.TerrainSurface(bundle, validate=False)
    trunk = json.loads(
        (impl.CONTRIB / impl.PINS["trunk_declaration_json"]["rel"]).read_bytes())
    groups, _ = impl.trunk_partition(trunk)
    tverts = [impl.to_contact(v[0:3])
              for v in trunk["render_mesh"]["vertices"]]
    impl.TRUNK_VERTS_CACHE = [tuple(v[0:3])
                              for v in trunk["render_mesh"]["vertices"]]
    ta = {"groups": groups, "vertices": tverts,
          "base": impl.to_contact(trunk["site"]["base_centre_m"]),
          "radius": trunk["geometry"]["radius_m"],
          "height": trunk["geometry"]["height_m"],
          "base_clearing": tuple(trunk["site"]["base_centre_m"]),
          "declaration": trunk}
    impl.BASE_APPROACH = ta["base"]
    return pins, tb, tq, lc, bundle, surface, trunk, groups, tverts, ta


class Pins(unittest.TestCase):
    def test_pins_hash_match(self):
        pins = impl.load_pins()
        self.assertTrue(all(p["raw_match"] for p in pins.values()))
        self.assertEqual(pins["local_contact_py"]["sha256"],
                         "1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc")


class FrozenForms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (cls.pins, cls.tb, cls.tq, cls.lc, cls.bundle, cls.surface,
         cls.trunk, cls.groups, cls.tverts, cls.ta) = _assets()

    def test_trunk_partition_is_center_vertex_rule(self):
        self.assertEqual([len(self.groups[k]) for k in
                          ("trunk_01.lateral", "trunk_01.base_cap",
                           "trunk_01.top_cap")], [64, 32, 32])

    def test_frame_map_round_trip(self):
        for p in ((0.0, 0.0, 0.0), (11.976783, 1.158, 2.471766),
                  (-19.3, 0.44, 17.2)):
            self.assertEqual(impl.to_clearing(impl.to_contact(p)), p)

    def test_combined_instantiation_refused_nonfinite_state(self):
        outcome = impl.combined_refusal_probe(
            self.lc, {"bundle": self.bundle}, self.ta)
        self.assertEqual(outcome["outcome"], "refused")
        self.assertIn("nonfinite_state", outcome["code"])

    def test_ground_crossing_ccd_on_is_pre_overlap_and_rests(self):
        sc = impl.scenario_g_high(self.lc, {"bundle": self.bundle},
                                  self.surface)
        firsts = impl.episode_firsts(sc["states"])
        self.assertTrue(firsts)
        self.assertEqual(firsts[0]["kind"], "ccd")
        self.assertGreater(firsts[0]["gap_m"], 0.0)
        worst = impl.metric_worst(sc["states"], "min_clearance_above_query_m")
        self.assertGreaterEqual(worst, -impl.PEN_BAR_M)
        probe = sc["probe"]
        seps = [v[2] - self.surface.height_at(v[0], -v[1])
                for v in probe.vertices]
        self.assertGreaterEqual(min(seps), impl.REST_LO_M)
        self.assertLessEqual(min(seps), impl.REST_HI_M)
        self.assertLessEqual(impl.lc_vlen(probe.velocity), impl.SPEED_BAR_M_S)

    def test_ground_crossing_ccd_off_control_tunnels(self):
        sc = impl.scenario_g_high(self.lc, {"bundle": self.bundle},
                                  self.surface, ccd=False)
        firsts = impl.episode_firsts(sc["states"])
        self.assertTrue(firsts)
        self.assertLess(firsts[0]["gap_m"], 0.0)
        self.assertGreater(-firsts[0]["gap_m"], impl.PEN_BAR_M)

    def test_trunk_crossing_ccd_on_never_enters_solid(self):
        sc = impl.scenario_t_cross(self.lc, self.ta)
        firsts = impl.episode_firsts(sc["states"])
        self.assertTrue(firsts)
        self.assertEqual(firsts[0]["kind"], "ccd")
        self.assertGreater(firsts[0]["gap_m"], 0.0)
        worst = impl.metric_worst(sc["states"], "min_radial_clearance_m")
        self.assertGreaterEqual(worst, -impl.PEN_BAR_M)

    def test_seam_high_phased_first_trunk_contact_is_pre_overlap_in_band(self):
        sc = impl.scenario_seam_high(self.lc, self.ta, self.surface)
        firsts = impl.episode_firsts(sc["states"])
        self.assertTrue(firsts)
        self.assertEqual(firsts[0]["kind"], "ccd")
        self.assertGreater(firsts[0]["gap_m"], 0.0)
        altitude = firsts[0]["point_clearing_a"][1]
        self.assertGreaterEqual(altitude, impl.SEAM_BAND_M[0])
        self.assertLessEqual(altitude, impl.SEAM_BAND_M[1])
        self.assertIsNotNone(sc["handover_tick"])

    def test_cap_rest_displaces_within_frozen_bar(self):
        sc = impl.scenario_trunk_top_rest(self.lc, self.ta)
        disp = max(st.get("max_displacement_m", 0.0)
                   for st in sc["states"])
        self.assertLessEqual(disp, impl.TRUNK_REST_DISP_BAR_M)
        cap_contact = any(
            "trunk_01.top_cap" in (c["surface_a"], c["surface_b"])
            for st in sc["states"] for c in st["contacts"])
        self.assertTrue(cap_contact)

    def test_all_falsifier_arms_bite(self):
        bites = impl.run_bites(self.lc, self.bundle, self.surface, self.ta)
        self.assertEqual(len(bites), 7)
        for row in bites:
            self.assertTrue(row["bites"], row["bite"])

    def test_asset_identity_exact(self):
        trunk_raw = (impl.CONTRIB
                     / impl.PINS["trunk_declaration_json"]["rel"]).read_bytes()
        trunk = json.loads(trunk_raw)
        groups, _ = impl.trunk_partition(trunk)
        tverts = [impl.to_contact(v[0:3])
                  for v in trunk["render_mesh"]["vertices"]]
        p1 = impl.identity_checks(b"b", self.bundle, b"t", trunk, groups,
                                  tverts,
                                  impl.ground_contact_body(self.bundle,
                                                           self.lc),
                                  self.lc)
        self.assertTrue(p1["ground"]["arrays_exact_equal"])
        self.assertTrue(p1["trunk"]["arrays_exact_equal"])
        self.assertLessEqual(p1["trunk"]["worst_radial_gap_to_analytic_m"],
                             impl.TRUNK_RADIAL_TOL_M)
        self.assertTrue(p1["ok"])

    def test_subject_probe_lands_on_camera_facing_facet(self):
        import math
        cam = impl.Camera(impl.VIEW_SPECS["V2_seam_closeup"])
        sp = impl.trunk_subject_probe(cam, self.ta, 0.3)
        base = self.ta["base_clearing"]
        az = math.degrees(math.atan2(sp["point"][2] - base[2],
                                     sp["point"][0] - base[0])) % 360.0
        cam_az = math.degrees(math.atan2(cam.position[2] - base[2],
                                         cam.position[0] - base[0])) % 360.0
        # the probe's facet midpoint must face the camera hemisphere
        self.assertLess(min(abs(az - cam_az), 360.0 - abs(az - cam_az)),
                        90.0 + 11.25)
        mesh = impl.SceneMesh(self.bundle, self.trunk,
                              impl.TRUNK_VERTS_CACHE, self.groups)
        rec = impl.classify_marker(mesh, cam, sp)
        self.assertEqual(rec["outcome"], "VISIBLE_EXACT")


if __name__ == "__main__":
    unittest.main()
