"""F01 tests -- determinism, spawn safety, boundary consistency (CPU-only).

Exercises the frozen falsifiers (agents/F01_clearing/PREREGISTRATION.md):
  (a) same seed producing different declarations,
  (b) spawn intersecting a declared obstacle,
  (c) a boundary invisible in the render contract while blocking motion.

Run from anywhere:
  python tools/monkey_campaign/agents/F01_clearing/tests/test_clearing.py
or, from the repo root:
  python -m unittest tools.monkey_campaign.agents.F01_clearing.tests.test_clearing
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
MODULE_PATH = REPO / "tools" / "monkey_campaign" / "data" / "monkey_clearing" / "clearing_recipe.py"

try:                                   # house import when run from the repo root
    from tools.monkey_campaign.data.monkey_clearing import clearing_recipe as recipe
except ImportError:                    # direct run from any cwd
    import importlib.util
    _spec = importlib.util.spec_from_file_location("clearing_recipe", MODULE_PATH)
    recipe = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(recipe)

DECLARATION_PATH = MODULE_PATH.parent / "clearing_declaration.json"


def corrupt(declaration, mutator):
    """Apply a mutation and RE-PIN the digest, so semantic checks are reached
    (otherwise every corruption would die at f01_digest_mismatch first)."""
    bad = copy.deepcopy(declaration)
    mutator(bad)
    bad.pop("declaration_sha256", None)
    bad["declaration_sha256"] = recipe.digest(bad)
    return bad


class DeterminismTests(unittest.TestCase):
    """Falsifier (a): same seed producing different declarations."""

    def test_same_seed_byte_identical_in_process(self):
        first = recipe.compile_declaration()
        second = recipe.compile_declaration()
        self.assertEqual(recipe.canonical(first), recipe.canonical(second))
        self.assertEqual(first["declaration_sha256"], second["declaration_sha256"])

    def test_same_seed_byte_identical_fresh_subprocess(self):
        out = REPO / ".tmp" / "f01_determinism_subprocess"
        out.mkdir(parents=True, exist_ok=True)
        paths = []
        for name in ("sub_a.json", "sub_b.json"):
            target = out / name
            subprocess.run([sys.executable, str(MODULE_PATH), "compile", str(target)],
                           check=True, capture_output=True, cwd=str(REPO))
            paths.append(target.read_bytes())
        self.assertEqual(paths[0], paths[1])
        written = DECLARATION_PATH.read_bytes()
        self.assertEqual(written, paths[0], "committed declaration must match the seed")

    def test_different_seed_different_bytes(self):
        a = recipe.compile_declaration()
        b = recipe.compile_declaration(seed=recipe.SEED + 1)
        self.assertNotEqual(recipe.canonical(a), recipe.canonical(b))

    def test_pinned_digest_detects_tamper(self):
        declaration = recipe.compile_declaration()
        bad = copy.deepcopy(declaration)
        bad["extent"]["half_width_m"] = 19.0          # digest NOT re-pinned
        with self.assertRaises(recipe.Refusal) as caught:
            recipe.validate_declaration(bad)
        self.assertEqual(caught.exception.code, "f01_digest_mismatch")


class SchemaAndTerrainTests(unittest.TestCase):
    def test_authored_declaration_validates(self):
        receipt = recipe.validate_declaration(recipe.load_declaration(DECLARATION_PATH))
        self.assertTrue(receipt["validated"])
        self.assertLessEqual(receipt["worst_grid_slope_m_per_m"], recipe.MAX_SLOPE_BOUND)
        self.assertEqual(receipt["worst_grid_error_m"], 0.0)

    def test_grid_equals_function(self):
        declaration = recipe.load_declaration(DECLARATION_PATH)
        mounds = declaration["terrain"]["recipe"]["mounds"]
        grid = declaration["terrain"]["grid"]
        for iz in range(grid["nz"]):
            z = grid["z0_m"] + iz * grid["dz_m"]
            for ix in range(grid["nx"]):
                x = grid["x0_m"] + ix * grid["dx_m"]
                self.assertEqual(grid["heights_m"][iz][ix], recipe.height_at(mounds, x, z))

    def test_wrong_schema_refused(self):
        bad = corrupt(recipe.compile_declaration(),
                      lambda d: d.__setitem__("schema", "chimera.monkey_clearing.v2"))
        with self.assertRaises(recipe.Refusal) as caught:
            recipe.validate_declaration(bad)
        self.assertEqual(caught.exception.code, "f01_schema")

    def test_grid_tamper_refused(self):
        def bump(d):
            d["terrain"]["grid"]["heights_m"][20][20] += 0.01
        with self.assertRaises(recipe.Refusal) as caught:
            recipe.validate_declaration(corrupt(recipe.compile_declaration(), bump))
        self.assertEqual(caught.exception.code, "f01_grid_function_mismatch")

    def test_overlapping_mounds_refused(self):
        def overlap(d):
            mounds = d["terrain"]["recipe"]["mounds"]
            mounds[1]["centre_x_m"] = mounds[0]["centre_x_m"]
            mounds[1]["centre_z_m"] = mounds[0]["centre_z_m"]
        with self.assertRaises(recipe.Refusal) as caught:
            recipe.validate_declaration(corrupt(recipe.compile_declaration(), overlap))
        # which placement guard fires first depends on the sampled geometry; both
        # refusals enforce the same construction law (disjoint / spawn-excluded)
        self.assertIn(caught.exception.code,
                      ("f01_mounds_disjoint", "f01_mound_spawn_exclusion"))

    def test_slope_bound_law(self):
        """Continuous gentleness law: max slope <= max A_i*pi/(2R_i) <= 0.05."""
        declaration = recipe.load_declaration(DECLARATION_PATH)
        mounds = declaration["terrain"]["recipe"]["mounds"]
        bound = max(m["amplitude_m"] * recipe.math.pi / (2.0 * m["radius_m"]) for m in mounds)
        self.assertLessEqual(bound, recipe.MAX_SLOPE_BOUND)
        self.assertLessEqual(recipe.validate_declaration(declaration)["worst_grid_slope_m_per_m"],
                             recipe.MAX_SLOPE_BOUND)


class SpawnSafetyTests(unittest.TestCase):
    """Falsifier (b): spawn intersecting any declared obstacle."""

    def setUp(self):
        self.declaration = recipe.load_declaration(DECLARATION_PATH)

    def test_clearance_proof_from_stored_numbers(self):
        spawn = self.declaration["spawn"]["position_m"]
        site = self.declaration["trunk_sites"][0]
        r_bound = site["footprint_radius_bound_m"]
        required = self.declaration["spawn"]["required_clearance_m"]
        gap = recipe.math.hypot(site["site_m"][0] - spawn[0],
                                site["site_m"][2] - spawn[2]) - r_bound
        self.assertGreaterEqual(gap, required)
        self.assertEqual(required, recipe.R_TRUNK_BOUND_M + 4.0 * recipe.R_BODY_ENVELOPE_M)

    def test_spawn_flat_on_base_ground_by_construction(self):
        mounds = self.declaration["terrain"]["recipe"]["mounds"]
        spawn = self.declaration["spawn"]["position_m"]
        self.assertEqual(spawn[1], 0.0)
        for m in mounds:
            self.assertGreaterEqual(
                recipe.math.hypot(m["centre_x_m"], m["centre_z_m"]),
                m["radius_m"] + self.declaration["spawn"]["required_clearance_m"])

    def test_spawn_inside_trunk_footprint_refused(self):
        def move(d):
            site = d["trunk_sites"][0]["site_m"]
            d["spawn"]["position_m"] = [site[0], site[1], site[2]]
        with self.assertRaises(recipe.Refusal) as caught:
            recipe.validate_declaration(corrupt(self.declaration, move))
        self.assertEqual(caught.exception.code, "f01_spawn_centre")

    def test_spawn_off_centre_refused(self):
        """The by-construction law: the spawn IS the extent centre; moving it toward
        the trunk is refused by the centre guard before any clearance question."""
        def nudge(d):
            site = d["trunk_sites"][0]["site_m"]
            d["spawn"]["position_m"] = [site[0] - 1.0, 0.0, site[2]]
        with self.assertRaises(recipe.Refusal) as caught:
            recipe.validate_declaration(corrupt(self.declaration, nudge))
        self.assertEqual(caught.exception.code, "f01_spawn_centre")

    def test_clearance_guard_inequality_holds(self):
        """Direct check of the defense-in-depth inequality the validator enforces:
        distance(spawn, trunk) - r_trunk_bound >= R_clear."""
        d = self.declaration
        spawn, site = d["spawn"]["position_m"], d["trunk_sites"][0]
        gap = recipe.math.hypot(site["site_m"][0] - spawn[0],
                                site["site_m"][2] - spawn[2]) \
            - site["footprint_radius_bound_m"]
        self.assertGreaterEqual(gap, d["spawn"]["required_clearance_m"])

    def test_mound_over_spawn_refused(self):
        def cover(d):
            mounds = d["terrain"]["recipe"]["mounds"]
            mounds[0]["centre_x_m"] = 0.0
            mounds[0]["centre_z_m"] = 0.0
        with self.assertRaises(recipe.Refusal) as caught:
            recipe.validate_declaration(corrupt(self.declaration, cover))
        self.assertEqual(caught.exception.code, "f01_mound_spawn_exclusion")

    def test_spawn_lifted_off_ground_refused(self):
        def lift(d):
            d["spawn"]["position_m"][1] = 0.5
        with self.assertRaises(recipe.Refusal) as caught:
            recipe.validate_declaration(corrupt(self.declaration, lift))
        self.assertEqual(caught.exception.code, "f01_spawn_on_ground")

    def test_trunk_site_outside_annulus_refused(self):
        """Move the site onto flat ground at x=16.9 (inside the inset bound, beyond
        the annulus) so the annulus guard is the one that fires."""
        def far(d):
            mounds = d["terrain"]["recipe"]["mounds"]
            d["trunk_sites"][0]["site_m"] = [16.9, recipe.height_at(mounds, 16.9, 0.0), 0.0]
        with self.assertRaises(recipe.Refusal) as caught:
            recipe.validate_declaration(corrupt(self.declaration, far))
        self.assertEqual(caught.exception.code, "f01_trunk_annulus")

    def test_trunk_f03_marker_required(self):
        def unmark(d):
            d["trunk_sites"][0]["geometry_qualified_in"] = "F01"
        with self.assertRaises(recipe.Refusal) as caught:
            recipe.validate_declaration(corrupt(self.declaration, unmark))
        self.assertEqual(caught.exception.code, "f01_trunk_f03_marker")


class BoundaryTests(unittest.TestCase):
    """Falsifier (c): a boundary invisible in the render contract while blocking."""

    def setUp(self):
        self.declaration = recipe.load_declaration(DECLARATION_PATH)

    def test_posts_on_extent_edge_and_visible(self):
        half = recipe.EXTENT_HALF_WIDTH_M
        rendered = self.declaration["boundary"]["rendered"]
        for px, py, pz in rendered["posts_m"]:
            self.assertAlmostEqual(min(abs(abs(px) - half), abs(abs(pz) - half)), 0.0,
                                   delta=1e-9)
            self.assertGreaterEqual(rendered["post_height_m"],
                                    rendered["min_protrusion_m"])

    def test_perimeter_coverage(self):
        half = recipe.EXTENT_HALF_WIDTH_M
        posts = self.declaration["boundary"]["rendered"]["posts_m"]
        steps = 3200
        for i in range(steps):
            s = i * (4.0 * half / steps)
            edge = 2.0 * half
            if s < edge:
                q = (-half + s, -half)
            elif s < 2 * edge:
                q = (half, -half + (s - edge))
            elif s < 3 * edge:
                q = (half - (s - 2 * edge), half)
            else:
                q = (-half, half - (s - 3 * edge))
            gap = min(recipe.math.hypot(q[0] - p[0], q[1] - p[2]) for p in posts)
            self.assertLessEqual(gap, recipe.POST_MAX_GAP_M + 1e-6, (q, gap))

    def test_all_posts_removed_refused(self):
        def strip(d):
            d["boundary"]["rendered"]["posts_m"] = []
        with self.assertRaises(recipe.Refusal) as caught:
            recipe.validate_declaration(corrupt(self.declaration, strip))
        self.assertEqual(caught.exception.code, "f01_post_count")

    def test_one_post_removed_refused(self):
        def drop(d):
            d["boundary"]["rendered"]["posts_m"].pop()
        with self.assertRaises(recipe.Refusal) as caught:
            recipe.validate_declaration(corrupt(self.declaration, drop))
        self.assertEqual(caught.exception.code, "f01_post_count")

    def test_posts_moved_inward_refused(self):
        """The invisible-wall form: visible ring inside the blocking edge. Posts are
        re-based at their moved positions so ONLY the edge/coverage violation
        remains (the base-ground guard must not fire first)."""
        def inward(d):
            mounds = d["terrain"]["recipe"]["mounds"]
            for p in d["boundary"]["rendered"]["posts_m"]:
                p[0] -= 1.0 if p[0] > 0 else -1.0
                p[1] = recipe.height_at(mounds, p[0], p[2])
        with self.assertRaises(recipe.Refusal) as caught:
            recipe.validate_declaration(corrupt(self.declaration, inward))
        self.assertIn(caught.exception.code,
                      ("f01_post_off_edge", "f01_boundary_coverage"))

    def test_physical_bound_inside_ring_refused(self):
        def shrink(d):
            d["boundary"]["physical"]["half_width_m"] = 19.0
        with self.assertRaises(recipe.Refusal) as caught:
            recipe.validate_declaration(corrupt(self.declaration, shrink))
        self.assertEqual(caught.exception.code, "f01_boundary_physical")

    def test_post_visibility_shrunk_refused(self):
        def shrink(d):
            d["boundary"]["rendered"]["post_height_m"] = 0.3
        with self.assertRaises(recipe.Refusal) as caught:
            recipe.validate_declaration(corrupt(self.declaration, shrink))
        self.assertEqual(caught.exception.code, "f01_boundary_render_frozen")


class LoaderTests(unittest.TestCase):
    def test_duplicate_key_refused(self):
        raw = b'{"schema": "a", "schema": "b"}'
        with self.assertRaises(recipe.Refusal) as caught:
            recipe.loads(raw)
        self.assertEqual(caught.exception.code, "f01_duplicate_json_key")

    def test_nonfinite_refused(self):
        with self.assertRaises(recipe.Refusal) as caught:
            recipe.loads(b'{"x": NaN}')
        self.assertEqual(caught.exception.code, "f01_nonfinite_json")

    def test_invalid_json_refused(self):
        with self.assertRaises(recipe.Refusal) as caught:
            recipe.loads(b"{oops")
        self.assertEqual(caught.exception.code, "f01_invalid_json")

    def test_declared_file_exists_and_is_canonical(self):
        declaration = recipe.load_declaration(DECLARATION_PATH)
        self.assertEqual(DECLARATION_PATH.read_bytes(), recipe.canonical(declaration))


if __name__ == "__main__":
    unittest.main(verbosity=2)
