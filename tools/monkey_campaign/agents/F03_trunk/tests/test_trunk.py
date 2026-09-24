"""F03 tests -- the rigid trunk's geometry, identity, provenance, representation
error, and rigid-only law (CPU-only).

Exercises the frozen falsifiers (agents/F03_trunk/PREREGISTRATION.md):
  (a) geometry exceeding F01's 0.5 m footprint bound,
  (b) the collision/render representation diverging beyond the frozen 2e-4 m
      tolerance (mesh discretization vs the analytic cylinder),
  (c) missing/implicit surface or material identity,
  (d) any deformable/damage claim (forbidden -- rigid only),
plus determinism (house law: same inputs -> byte-identical declaration) and the
site contract against F01's LIVE declaration.

Run from anywhere:
  python tools/monkey_campaign/agents/F03_trunk/tests/test_trunk.py
or, from the repo root:
  python -m unittest tools.monkey_campaign.agents.F03_trunk.tests.test_trunk
"""
from __future__ import annotations

import copy
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
MODULE_PATH = REPO / "tools" / "monkey_campaign" / "data" / "monkey_trunk" / "trunk_recipe.py"
DECL_PATH = REPO / "tools" / "monkey_campaign" / "data" / "monkey_trunk" / "trunk_declaration.json"

try:                                   # house import when run from the repo root
    from tools.monkey_campaign.data.monkey_trunk import trunk_recipe as recipe
    from tools.monkey_campaign.data.monkey_clearing import clearing_recipe as f01
except ImportError:                    # direct run from any cwd
    import importlib.util
    _spec = importlib.util.spec_from_file_location("trunk_recipe", MODULE_PATH)
    recipe = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(recipe)
    _spec = importlib.util.spec_from_file_location(
        "clearing_recipe",
        REPO / "tools" / "monkey_campaign" / "data" / "monkey_clearing" / "clearing_recipe.py")
    f01 = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(f01)


def committed():
    return recipe.load_declaration(str(DECL_PATH))


def tampered(mutate):
    declaration = committed()
    mutate(declaration)
    # Re-pin the digest so the SEMANTIC refusal under test fires. The pin itself
    # is separately exercised by test_digest_tamper_refused (which does NOT
    # re-pin and must hit f03_digest_mismatch).
    body = {k: v for k, v in declaration.items() if k != "declaration_sha256"}
    declaration["declaration_sha256"] = recipe.sha(recipe.canonical(body))
    return declaration


def refuses(mutate, code, strict=True):
    """A tampered declaration must be refused with the named code."""
    try:
        recipe.validate_declaration(tampered(mutate), strict_prereg=strict)
    except recipe.Refusal as refusal:
        return refusal.code
    raise AssertionError(f"expected Refusal({code}); validation passed")


class Determinism(unittest.TestCase):
    """House law: same inputs -> byte-identical declaration, anywhere."""

    def test_compile_twice_inprocess_byte_identical(self):
        a = recipe.canonical(recipe.compile_declaration())
        b = recipe.canonical(recipe.compile_declaration())
        self.assertEqual(a, b)

    def test_committed_file_matches_compile_and_pin(self):
        declaration = committed()
        raw = DECL_PATH.read_bytes()
        self.assertEqual(raw, recipe.canonical(declaration))
        # the pin covers the BODY without the pin (house rule; the raw file bytes
        # hash differently by construction -- see F01's two-digest receipt)
        body = {k: v for k, v in declaration.items() if k != "declaration_sha256"}
        self.assertEqual(recipe.sha(recipe.canonical(body)),
                         declaration["declaration_sha256"])

    def test_compile_in_fresh_subprocess_byte_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = str(Path(tmp) / "sub.json")
            for _ in range(2):
                proc = subprocess.run(
                    [sys.executable, str(MODULE_PATH), "compile", out],
                    capture_output=True, text=True, cwd=str(tmp))
                self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(Path(out).read_bytes(), DECL_PATH.read_bytes())

    def test_validate_receipt_on_committed_file(self):
        receipt = recipe.validate_declaration(committed())
        self.assertTrue(receipt["validated"])
        self.assertEqual(receipt["object_id"], "trunk_01")
        self.assertEqual(receipt["schema"], "chimera.trunk_asset.v1")


class LoaderStrictness(unittest.TestCase):
    """Strict intake, house style."""

    def test_duplicate_key_refused(self):
        raw = b'{"schema":"chimera.trunk_asset.v1","name":"a","name":"b"}'
        with self.assertRaises(recipe.Refusal) as caught:
            recipe.loads(raw)
        self.assertEqual(caught.exception.code, "f03_duplicate_json_key")

    def test_nonfinite_refused(self):
        raw = b'{"schema":"chimera.trunk_asset.v1","x":NaN}'
        with self.assertRaises(recipe.Refusal) as caught:
            recipe.loads(raw)
        self.assertEqual(caught.exception.code, "f03_nonfinite_json")

    def test_malformed_json_refused(self):
        with self.assertRaises(recipe.Refusal) as caught:
            recipe.loads(b"{nope")
        self.assertEqual(caught.exception.code, "f03_invalid_json")

    def test_digest_tamper_refused(self):
        """Without re-pinning, any content change must hit the digest pin."""
        declaration = committed()
        declaration["scope"] = declaration["scope"] + " tampered"
        with self.assertRaises(recipe.Refusal) as caught:
            recipe.validate_declaration(declaration, strict_prereg=False)
        self.assertEqual(caught.exception.code, "f03_digest_mismatch")


class SiteContract(unittest.TestCase):
    """The site is F01's data; the trunk must sit exactly on it."""

    def test_site_equals_f01_live_trunk_site(self):
        declaration = committed()
        f01_declaration = f01.load_declaration(
            str(REPO / "tools" / "monkey_campaign" / "data" / "monkey_clearing"
                / "clearing_declaration.json"))
        f01.validate_declaration(f01_declaration)
        site = declaration["site"]["base_centre_m"]
        self.assertEqual([float(v) for v in f01_declaration["trunk_sites"][0]["site_m"]],
                         [float(v) for v in site])
        self.assertEqual(declaration["site"]["id"], "trunk_01")
        self.assertEqual(declaration["site"]["axis_dir"], [0.0, 1.0, 0.0])

    def test_site_terrain_height_is_zero(self):
        declaration = committed()
        f01_declaration = f01.load_declaration(
            str(REPO / "tools" / "monkey_campaign" / "data" / "monkey_clearing"
                / "clearing_declaration.json"))
        x, y, z = declaration["site"]["base_centre_m"]
        self.assertEqual(y, f01.height_at(
            f01_declaration["terrain"]["recipe"]["mounds"], x, z))
        self.assertEqual(y, 0.0)

    def test_moved_site_refused(self):
        def move(declaration):
            declaration["site"]["base_centre_m"][0] += 0.001
        self.assertEqual(refuses(move, "f03_site_mismatch"), "f03_site_mismatch")

    def test_drifted_f01_pin_refused_in_recipe(self):
        declaration = tampered(lambda d: d["site"]["provenance"].__setitem__(
            "declaration_sha256", "0" * 64))
        with self.assertRaises(recipe.Refusal) as caught:
            recipe.validate_declaration(declaration)
        self.assertEqual(caught.exception.code, "f03_site_provenance")


class GeometryDerivation(unittest.TestCase):
    """Height and radius re-derive from pinned walker numbers -- no free choices."""

    def test_height_equals_pinned_sum(self):
        declaration = committed()
        derivation = declaration["geometry"]["derivation"]
        standing = derivation["leg_hip_to_mp_m"] + derivation["hat_length_m"]
        fore = derivation["upperarm_length_m"] + derivation["forearm_length_m"]
        self.assertEqual(standing, 0.901)
        self.assertEqual(fore, 0.257)
        self.assertEqual(declaration["geometry"]["height_m"], standing + fore)
        self.assertEqual(declaration["geometry"]["height_m"], 1.158)

    def test_radius_equals_half_pinned_foot(self):
        declaration = committed()
        derivation = declaration["geometry"]["derivation"]
        self.assertEqual(declaration["geometry"]["radius_m"],
                         derivation["foot_length_m"] / 2.0)
        self.assertEqual(declaration["geometry"]["radius_m"], 0.037)

    def test_energy_scales_rederive(self):
        declaration = committed()
        derivation = declaration["geometry"]["derivation"]
        m, g = derivation["walker_mass_kg"], derivation["gravity_m_s2"]
        self.assertEqual(derivation["full_ascent_gain_J"],
                         round(m * g * declaration["geometry"]["height_m"], 6))
        self.assertEqual(derivation["full_ascent_gain_J"], 113.992539)
        self.assertEqual(derivation["above_reach_gain_J"], 25.298862)

    def test_pinned_input_tamper_refused(self):
        def bump(declaration):
            declaration["geometry"]["derivation"]["foot_length_m"] = 0.08
        self.assertEqual(refuses(bump, "f03_pinned_input"), "f03_pinned_input")

    def test_height_tamper_refused(self):
        def stretch(declaration):
            declaration["geometry"]["height_m"] = 2.0
        self.assertEqual(refuses(stretch, "f03_height_frozen"), "f03_height_frozen")


class FootprintBound(unittest.TestCase):
    """Falsifier (a): geometry exceeding the 0.5 m footprint."""

    def test_radius_inside_bound_and_extent(self):
        declaration = committed()
        radius = declaration["geometry"]["radius_m"]
        self.assertLessEqual(radius, declaration["site"]["footprint_bound_m"])
        self.assertLessEqual(radius, 0.5)
        x, _, z = declaration["site"]["base_centre_m"]
        half = declaration["approach_and_bounds"]["extent_half_width_m"]
        self.assertLessEqual(abs(x) + radius, half)
        self.assertLessEqual(abs(z) + radius, half)

    def test_every_vertex_inside_bound(self):
        declaration = committed()
        bound = declaration["site"]["footprint_bound_m"]
        x, _, z = declaration["site"]["base_centre_m"]
        for i, v in enumerate(declaration["render_mesh"]["vertices"]):
            d = math.hypot(v[0] - x, v[2] - z)
            self.assertLessEqual(d, bound + 1e-9, f"vertex {i} at {d}")

    def test_giant_radius_refused(self):
        def grow(declaration):
            declaration["geometry"]["radius_m"] = 0.6
        self.assertEqual(refuses(grow, "f03_radius_frozen"), "f03_radius_frozen")


class RepresentationError(unittest.TestCase):
    """Falsifier (b): mesh-vs-analytic divergence beyond the frozen tolerance."""

    def test_measured_error_within_frozen_tolerance(self):
        declaration = committed()
        rep = declaration["representation_error"]
        self.assertEqual(rep["tolerance_m"], 2e-4)
        self.assertLessEqual(rep["max_measured_m"], rep["tolerance_m"])
        self.assertGreater(rep["max_measured_m"], 0.0)   # the error is REAL, measured

    def test_measured_matches_sagitta_formula(self):
        declaration = committed()
        rep = declaration["representation_error"]
        radius = declaration["geometry"]["radius_m"]
        segments = declaration["render_mesh"]["ring_segments"]
        formula = radius * (1.0 - math.cos(math.pi / segments))
        self.assertAlmostEqual(rep["sagitta_formula_m"], formula, places=9)
        self.assertLess(abs(rep["max_measured_m"] - formula), 2e-6)

    def test_every_declared_vertex_on_analytic_surface(self):
        declaration = committed()
        radius = declaration["geometry"]["radius_m"]
        x, y0, z = declaration["site"]["base_centre_m"]
        height = declaration["geometry"]["height_m"]
        segments = declaration["render_mesh"]["ring_segments"]
        vertices = declaration["render_mesh"]["vertices"]
        worst = 0.0
        for i, v in enumerate(vertices[:2 * segments]):     # the lateral rings
            d = math.hypot(v[0] - x, v[2] - z)
            worst = max(worst, abs(d - radius))
            self.assertIn(v[1], (y0, round(y0 + height, 6)))
        self.assertLessEqual(worst, 2e-6)

    def test_measured_error_recomputes_from_stored_vertices(self):
        declaration = committed()
        rep = declaration["representation_error"]
        vertices = declaration["render_mesh"]["vertices"]
        site = declaration["site"]["base_centre_m"]
        radius = declaration["geometry"]["radius_m"]
        segments = declaration["render_mesh"]["ring_segments"]
        recomputed = recipe.measure_representation_error(vertices, site, radius, segments)
        self.assertAlmostEqual(rep["max_measured_m"], round(recomputed, 9), places=9)

    def test_ring_count_is_derived_not_chosen(self):
        n_min = recipe.min_ring_segments(recipe.TRUNK_RADIUS_M, recipe.REP_TOL_M)
        self.assertEqual(n_min, 31)
        self.assertEqual(recipe.RING_SEGMENTS, 32)              # smallest power of two >= 31
        self.assertGreater(recipe.sagitta(recipe.TRUNK_RADIUS_M, 30), recipe.REP_TOL_M)
        self.assertLessEqual(recipe.sagitta(recipe.TRUNK_RADIUS_M, 32), recipe.REP_TOL_M)

    def test_compile_refuses_segments_below_tolerance(self):
        with self.assertRaises(recipe.Refusal) as caught:
            recipe.compile_declaration(ring_segments=24)
        self.assertEqual(caught.exception.code, "f03_segments_below_tolerance")

    def test_declaration_with_shrunk_segments_refused(self):
        def shrink(declaration):
            declaration["render_mesh"]["ring_segments"] = 24
        self.assertEqual(refuses(shrink, "f03_ring_segments"), "f03_ring_segments")

    def test_widened_tolerance_refused(self):
        def widen(declaration):
            declaration["representation_error"]["tolerance_m"] = 1e-3
        self.assertEqual(refuses(widen, "f03_tolerance_frozen"), "f03_tolerance_frozen")

    def test_false_measured_error_refused(self):
        """Zeroing the measured error breaks BOTH the formula identity and the
        recomputation-from-stored-vertices identity."""
        def lie(declaration):
            declaration["representation_error"]["max_measured_m"] = 0.0
        self.assertEqual(refuses(lie, "f03_measured_vs_formula"),
                         "f03_measured_vs_formula")

    def test_displaced_vertex_refused(self):
        def shove(declaration):
            declaration["render_mesh"]["vertices"][0][0] += 1e-3
        self.assertEqual(refuses(shove, "f03_vertex_off_surface"),
                         "f03_vertex_off_surface")

    def test_inward_winding_refused(self):
        def flip(declaration):
            idx = declaration["render_mesh"]["indices"]
            idx[0], idx[2] = idx[2], idx[0]
        self.assertEqual(refuses(flip, "f03_indices_not_canonical"),
                         "f03_indices_not_canonical")


class SurfaceAndMaterialIdentity(unittest.TestCase):
    """Falsifier (c): missing/implicit surface or material identity."""

    def test_surface_ids_explicit_unique_resolvable(self):
        declaration = committed()
        surfaces = declaration["surface_ids"]
        self.assertEqual(len(surfaces), 3)
        ids = [s["id"] for s in surfaces]
        self.assertEqual(len(set(ids)), 3)
        self.assertEqual(set(ids), {"trunk_01.lateral", "trunk_01.base_cap",
                                    "trunk_01.top_cap"})
        for surface in surfaces:
            self.assertTrue(surface["analytic"])
            self.assertTrue(surface["normal_law"])
            self.assertEqual(surface["material"], declaration["material"]["id"])
        by_surface = {s["surface"]: s for s in surfaces}
        self.assertTrue(by_surface["lateral"]["climbable"])
        self.assertFalse(by_surface["base_cap"]["climbable"])
        self.assertFalse(by_surface["top_cap"]["climbable"])

    def test_contact_normals_explicit(self):
        declaration = committed()
        normals = declaration["collision_representation"]["contact_normals"]
        for key in ("lateral", "base_cap", "top_cap"):
            self.assertIn("(", normals[key])       # a concrete law, not prose hand-waving
        self.assertIn("radial outward", normals["lateral"])

    def test_friction_provenance_is_explicitly_unevidenced(self):
        declaration = committed()
        friction = declaration["material"]["friction"]
        self.assertEqual(friction["provenance"], "UNEVIDENCED-PLACEHOLDER")
        self.assertEqual(friction["acquisition_prerequisite"], "G04")
        self.assertEqual(friction["coefficient_placeholder"], 0.6)
        self.assertIn("not evidence", friction["placeholder_source"])
        self.assertTrue(friction["evidence_search"])
        self.assertEqual(declaration["material"]["colour_provenance_class"], "design")

    def test_renamed_material_ref_refused(self):
        def rename(declaration):
            declaration["surface_ids"][0]["material"] = "mat.bark.something_else"
        self.assertEqual(refuses(rename, "f03_surface_material_ref"),
                         "f03_surface_material_ref")

    def test_deleted_surface_refused(self):
        def drop(declaration):
            declaration["surface_ids"] = [s for s in declaration["surface_ids"]
                                          if s["surface"] != "top_cap"]
        self.assertEqual(refuses(drop, "f03_surface_count"), "f03_surface_count")

    def test_duplicate_surface_refused(self):
        def dupe(declaration):
            # count stays 3; one id appears twice
            declaration["surface_ids"][2] = dict(declaration["surface_ids"][0])
        self.assertEqual(refuses(dupe, "f03_surface_duplicate"), "f03_surface_duplicate")

    def test_false_evidence_claim_refused(self):
        """The honest-provenance law: relabelling the placeholder as 'researched'
        (or dropping the acquisition debt) is refused."""
        self.assertEqual(refuses(lambda d: d["material"]["friction"].__setitem__(
            "provenance", "researched"), "f03_friction_provenance"),
            "f03_friction_provenance")
        self.assertEqual(refuses(lambda d: d["material"]["friction"].__setitem__(
            "acquisition_prerequisite", ""), "f03_friction_acquisition"),
            "f03_friction_acquisition")
        self.assertEqual(refuses(lambda d: d["material"]["friction"].__setitem__(
            "coefficient_placeholder", 0.4), "f03_friction_value"),
            "f03_friction_value")

    def test_unresolvable_material_id_refused(self):
        def rename(declaration):
            declaration["material"]["id"] = "mat.other"
        self.assertEqual(refuses(rename, "f03_material_id"), "f03_material_id")


class RigidOnly(unittest.TestCase):
    """Falsifier (d): any deformable/damage claim is refused (closed vocabulary)."""

    def test_rigid_flags_frozen(self):
        coll = committed()["collision_representation"]
        self.assertIs(coll["rigid"], True)
        self.assertIs(coll["deformable"], False)
        self.assertEqual(coll["damage_model"], "none")
        self.assertEqual(coll["branches"], "deferred")

    def test_damage_value_injection_refused(self):
        def damage(declaration):
            declaration["collision_representation"]["damage_model"] = "bark_crack"
        self.assertEqual(refuses(damage, "f03_rigid_flags"), "f03_rigid_flags")

    def test_deformable_flip_refused(self):
        def soft(declaration):
            declaration["collision_representation"]["deformable"] = True
        self.assertEqual(refuses(soft, "f03_rigid_flags"), "f03_rigid_flags")

    def test_extra_physics_field_refused(self):
        def plastic(declaration):
            declaration["collision_representation"]["plasticity_modulus_pa"] = 1e9
        self.assertEqual(refuses(plastic, "f03_rigid_vocabulary"),
                         "f03_rigid_vocabulary")

    def test_extra_material_field_refused(self):
        def extra(declaration):
            declaration["material"]["damage_threshold_J"] = 5.0
        self.assertEqual(refuses(extra, "f03_material_vocabulary"),
                         "f03_material_vocabulary")

    def test_extra_geometry_field_refused(self):
        def branch(declaration):
            declaration["geometry"]["branch_nodes"] = []
        self.assertEqual(refuses(branch, "f03_geometry_vocabulary"),
                         "f03_geometry_vocabulary")

    def test_extra_top_level_field_refused(self):
        def extra(declaration):
            declaration["branches_geometry"] = {"limbs": 3}
        self.assertEqual(refuses(extra, "f03_top_level_vocabulary"),
                         "f03_top_level_vocabulary")


class ReachableApproach(unittest.TestCase):
    """C15: reachable approach and geometry bounds, re-proven with the REAL radius."""

    def test_clearance_holds_with_actual_radius(self):
        declaration = committed()
        approach = declaration["approach_and_bounds"]
        self.assertGreaterEqual(approach["clearance_with_trunk_radius_m"],
                                approach["required_clearance_m"])
        self.assertAlmostEqual(approach["axis_distance_from_spawn_m"],
                               math.hypot(11.976783, 2.471766), places=6)

    def test_solid_inside_extent(self):
        declaration = committed()
        x, _, z = declaration["site"]["base_centre_m"]
        half = declaration["approach_and_bounds"]["extent_half_width_m"]
        self.assertLess(abs(x), half)
        self.assertLess(abs(z), half)
        self.assertTrue(declaration["approach_and_bounds"]["solid_within_extent"])

    def test_trunk_height_supports_a_genuine_climb(self):
        """The top must exceed the walker's standing-height bound -- a hold at the
        top cannot be reached standing on the ground."""
        declaration = committed()
        derivation = declaration["geometry"]["derivation"]
        self.assertGreater(declaration["geometry"]["height_m"],
                           derivation["standing_height_bound_m"])
        self.assertGreater(derivation["above_reach_gain_J"], 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
