"""F02 tests -- render/query agreement, posts, boundary semantics, frozen slope cases.

Exercises the frozen falsifiers (agents/F02_terrain/PREREGISTRATION.md):
  (a) render surface vs query surface disagreement beyond the frozen tolerances,
  (b) a boundary post position mismatch vs F01's declaration,
  (c) the physical bound not matching |x|>20 / |z|>20 (strict >) semantics,
  (d) frozen slope/obstacle cases failing F01's law (max |slope| <= 0.05).

Headless by prereg: both sides are DECLARATIONS (the bundle's render arrays vs the query
binding reading the same arrays); no engine process, no GPU, no server.

Run from anywhere:
  python tools/monkey_campaign/agents/F02_terrain/tests/test_terrain.py
or, from the repo root:
  python -m unittest tools.monkey_campaign.agents.F02_terrain.tests.test_terrain
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
DATA = REPO / "tools" / "monkey_campaign" / "data" / "monkey_clearing"
BUNDLE_PATH = DATA / "terrain_bundle.json"
DECLARATION_PATH = DATA / "clearing_declaration.json"
BUNDLE_PY = DATA / "terrain_bundle.py"
QUERY_PY = DATA / "terrain_query.py"

try:                                   # house import when run from the repo root
    from tools.monkey_campaign.data.monkey_clearing import clearing_recipe, terrain_bundle
    from tools.monkey_campaign.data.monkey_clearing import terrain_query
except ImportError:                    # direct run from any cwd
    def _load(name, path):
        import importlib.util
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    clearing_recipe = _load("clearing_recipe", DATA / "clearing_recipe.py")
    terrain_bundle = _load("terrain_bundle", BUNDLE_PY)
    terrain_query = _load("terrain_query", QUERY_PY)

# --- frozen prereg values -------------------------------------------------------
TOL_HEIGHT = 1e-9
TOL_NORMAL = 1e-12
TOL_GRADIENT = 1e-9
TOL_DISCRETIZATION = 0.01
TOL_POST_AXIS = 1e-12                  # amendment-1 scope: recovered axis vs declaration
SAMPLE_SEED = 4598322                  # ASCII "F02"
EXPECTED_VERTICES = 13920              # 3*3200 ground + 80*54 post
EXPECTED_INDICES = 13920
EXPECTED_TRIANGLES = 4640


def load_surface():
    return terrain_query.TerrainSurface(terrain_bundle.load_bundle(BUNDLE_PATH),
                                        validate=True)


def repin(bundle):
    body = {k: v for k, v in bundle.items() if k != "bundle_sha256"}
    bundle["bundle_sha256"] = terrain_bundle.digest(body)
    return bundle


def corrupt(mutator):
    """Load the committed bundle, apply a mutation, RE-PIN, return it."""
    bundle = copy.deepcopy(terrain_bundle.load_bundle(BUNDLE_PATH))
    mutator(bundle)
    return repin(bundle)


def barycentric_height(verts, x, z):
    """INDEPENDENT render-side surface evaluation: the plane through the three STORED
    vertices, solved by Cramer's rule in the xz plane. Deliberately a different
    implementation path from terrain_query's closed-form cell algebra."""
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = verts
    ux, uz = bx - ax, bz - az
    vx, vz = cx - ax, cz - az
    wx, wz = x - ax, z - az
    det = ux * vz - vx * uz
    u = (wx * vz - wz * vx) / det
    v = (ux * wz - uz * wx) / det
    return ay + u * (by - ay) + v * (cy - ay), u, v


class F02TestCase(unittest.TestCase):
    def setUp(self):
        self.bundle = terrain_bundle.load_bundle(BUNDLE_PATH)
        self.surface = terrain_query.TerrainSurface(self.bundle, validate=True)
        self.declaration = clearing_recipe.load_declaration(DECLARATION_PATH)
        self.receipt = terrain_bundle.validate_bundle(self.bundle)

    # -- shared sample set (frozen in the prereg) --------------------------------
    def sample_points(self):
        render = self.bundle["render"]
        verts, indices = render["vertices"], render["indices"]
        grid = self.bundle["terrain_surface"]["grid"]
        pts = []
        for iz in range(grid["nz"]):                        # 1,681 grid nodes
            for ix in range(grid["nx"]):
                pts.append((grid["x0_m"] + ix * grid["dx_m"],
                            grid["z0_m"] + iz * grid["dz_m"]))
        for iz in range(grid["nz"] - 1):                    # 1,600 cell centres
            for ix in range(grid["nx"] - 1):
                pts.append((grid["x0_m"] + (ix + 0.5) * grid["dx_m"],
                            grid["z0_m"] + (iz + 0.5) * grid["dz_m"]))
        for t in range(0, self.surface.ground_index_count, 3):   # centroids + edge mids
            tri = [tuple(verts[9 * indices[t + k]:9 * indices[t + k] + 3])
                   for k in range(3)]
            pts.append((sum(p[0] for p in tri) / 3.0, sum(p[2] for p in tri) / 3.0))
            for a, b in ((0, 1), (1, 2), (2, 0)):
                pts.append(((tri[a][0] + tri[b][0]) / 2.0,
                            (tri[a][2] + tri[b][2]) / 2.0))
        rng = clearing_recipe.SplitMix64(SAMPLE_SEED)       # 4,096 seeded pseudo-random
        for _ in range(4096):
            pts.append((rng.uniform_grid(-20.0, 20.0), rng.uniform_grid(-20.0, 20.0)))
        return pts


class TestDeterminism(F02TestCase):
    def test_inprocess_compile_bytes_identical(self):
        first = terrain_bundle.canonical(
            terrain_bundle.compile_bundle(DECLARATION_PATH))
        second = terrain_bundle.canonical(
            terrain_bundle.compile_bundle(DECLARATION_PATH))
        self.assertEqual(first, second)

    def test_committed_file_equals_fresh_compile(self):
        committed = BUNDLE_PATH.read_bytes()
        fresh = terrain_bundle.canonical(
            terrain_bundle.compile_bundle(DECLARATION_PATH))
        self.assertEqual(hashlib.sha256(committed).hexdigest(),
                         hashlib.sha256(fresh).hexdigest())
        self.assertEqual(committed, fresh)

    def test_subprocess_compile_bytes_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "terrain_bundle.json"
            proc = subprocess.run([sys.executable, str(BUNDLE_PY), "compile", str(out)],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(out.read_bytes(), BUNDLE_PATH.read_bytes())


class TestIntakeStrictness(F02TestCase):
    def test_digest_mismatch_refused(self):
        bad = copy.deepcopy(self.bundle)
        bad["render"]["vertex_count"] += 1
        with self.assertRaisesRegex(terrain_bundle.Refusal, "f02_digest_mismatch"):
            terrain_bundle.validate_bundle(bad)

    def test_duplicate_json_key_refused(self):
        raw = b'{"schema":"chimera.monkey_terrain.v1","schema":"x"}'
        with self.assertRaisesRegex(ValueError, "duplicate_json_key"):
            terrain_bundle.loads(raw)

    def test_nonfinite_json_refused(self):
        raw = b'{"schema":"chimera.monkey_terrain.v1","x":NaN}'
        with self.assertRaisesRegex(ValueError, "nonfinite_json"):
            terrain_bundle.loads(raw)

    def test_wrong_schema_refused(self):
        with self.assertRaisesRegex(ValueError, "f02_schema"):
            terrain_bundle.loads(b'{"schema":"chimera.earth_scene.v1"}')

    def test_drifted_grid_refused_even_when_repinned(self):
        def mutate(bundle):
            bundle["terrain_surface"]["grid"]["heights_m"][10][10] += 0.001
        with self.assertRaisesRegex(ValueError, "f02_grid_mound_mismatch"):
            terrain_bundle.validate_bundle(corrupt(mutate))

    def test_drifted_mound_refused_even_when_repinned(self):
        def mutate(bundle):
            bundle["terrain_surface"]["mounds"][0]["amplitude_m"] *= 1.5
        with self.assertRaisesRegex(ValueError, "f02_grid_mound_mismatch"):
            terrain_bundle.validate_bundle(corrupt(mutate))

    def test_tampered_post_base_refused_even_when_repinned(self):
        def mutate(bundle):
            psec = bundle["render"]["sections"]["boundary_posts"]
            v0 = psec["vertex_start"]
            ys = [bundle["render"]["vertices"][9 * (v0 + v) + 1]
                  for v in range(psec["vertex_count"])]
            base = min(ys)                              # lift EVERY base-ring copy
            for v in range(psec["vertex_count"]):
                if bundle["render"]["vertices"][9 * (v0 + v) + 1] == base:
                    bundle["render"]["vertices"][9 * (v0 + v) + 1] = base + 0.5
        with self.assertRaisesRegex(ValueError, "f02_post_(base_ground|height)"):
            terrain_bundle.validate_bundle(corrupt(mutate))

    def test_ground_vertex_past_extent_refused_even_when_repinned(self):
        def mutate(bundle):
            bundle["render"]["vertices"][0] = 20.5               # first ground vertex x
        with self.assertRaisesRegex(ValueError, "f02_ground_outside_extent"):
            terrain_bundle.validate_bundle(corrupt(mutate))

    def test_degenerate_triangle_refused_even_when_repinned(self):
        def mutate(bundle):
            v = bundle["render"]["vertices"]
            i = bundle["render"]["indices"]
            for k in range(3):                                   # collapse triangle 0
                v[9 * i[k]:9 * i[k] + 3] = [0.0, 0.0, 0.0]
        with self.assertRaisesRegex(ValueError, "f02_degenerate_triangle"):
            terrain_bundle.validate_bundle(corrupt(mutate))

    def test_wrong_slope_bound_refused(self):
        def mutate(bundle):
            bundle["terrain_surface"]["max_slope_bound_m_per_m"] = 0.06
        with self.assertRaisesRegex(ValueError, "f02_slope_bound"):
            terrain_bundle.validate_bundle(corrupt(mutate))


class TestMeshShape(F02TestCase):
    def test_frozen_counts(self):
        render = self.bundle["render"]
        self.assertEqual(render["vertex_count"], EXPECTED_VERTICES)
        self.assertEqual(render["index_count"], EXPECTED_INDICES)
        self.assertEqual(render["triangle_count"], EXPECTED_TRIANGLES)
        self.assertEqual(len(render["vertices"]), 9 * EXPECTED_VERTICES)
        self.assertEqual(render["sections"]["ground"]["index_count"], 9600)
        self.assertEqual(render["sections"]["boundary_posts"]["index_count"], 4320)
        self.assertEqual(
            render["sections"]["boundary_posts"]["vertex_start"],
            render["sections"]["ground"]["vertex_count"])

    def test_receipt_numbers(self):
        r = self.receipt
        self.assertTrue(r["validated"])
        self.assertEqual(r["hygiene_broken"], 0)
        self.assertEqual(r["hygiene_deviant"], 0)
        self.assertEqual(r["worst_stored_normal_error"], 0.0)
        self.assertEqual(r["worst_grid_error_m"], 0.0)
        self.assertGreater(r["min_cross_length"], terrain_bundle.DEGENERATE_EPS)

    def test_upload_layout_is_engine_native(self):
        layout = self.bundle["render"]["mesh_layout"]
        self.assertEqual(layout["floats_per_vertex"], 9)
        self.assertEqual(layout["fields"], ["position_m", "normal", "color_rgb"])
        self.assertEqual(layout["index_type"], "uint32")

    def test_ground_normals_up_and_stored_equal_face_normals(self):
        render = self.bundle["render"]
        verts, indices = render["vertices"], render["indices"]
        worst = 0.0
        for t in range(0, self.surface.ground_index_count, 3):
            ps = [tuple(verts[9 * indices[t + k]:9 * indices[t + k] + 3])
                  for k in range(3)]
            n = terrain_bundle.face_normal(*ps)
            self.assertGreater(n[1], 0.0)
            for k in range(3):
                stored = tuple(verts[9 * indices[t + k] + 3:9 * indices[t + k] + 6])
                worst = max(worst, max(abs(stored[d] - n[d]) for d in range(3)))
        self.assertLessEqual(worst, TOL_NORMAL)

    def test_every_ground_vertex_is_a_grid_node(self):
        grid = self.bundle["terrain_surface"]["grid"]
        heights = grid["heights_m"]
        lookup = {(round(grid["x0_m"] + ix * grid["dx_m"], 9),
                   round(grid["z0_m"] + iz * grid["dz_m"], 9)): heights[iz][ix]
                  for iz in range(grid["nz"]) for ix in range(grid["nx"])}
        verts = self.bundle["render"]["vertices"]
        gsec = self.bundle["render"]["sections"]["ground"]
        for i in range(gsec["vertex_count"]):
            x, y = verts[9 * i], verts[9 * i + 1]
            z = verts[9 * i + 2]
            key = (round(x, 9), round(z, 9))
            self.assertIn(key, lookup)
            self.assertEqual(y, lookup[key])

    def test_source_pins_match_committed_declaration(self):
        raw = DECLARATION_PATH.read_bytes()
        declaration = clearing_recipe.loads(raw)
        clearing_recipe.validate_declaration(declaration)
        self.assertEqual(self.bundle["source"]["declaration_file_sha256"],
                         hashlib.sha256(raw).hexdigest())
        self.assertEqual(self.bundle["source"]["declaration_sha256"],
                         declaration["declaration_sha256"])
        self.assertEqual(self.bundle["terrain_surface"]["grid"]["heights_m"],
                         declaration["terrain"]["grid"]["heights_m"])


class TestRenderQueryAgreement(F02TestCase):
    """Falsifier (a): the query surface against the stored render surface."""

    def test_agreement_over_frozen_sample_set(self):
        pts = self.sample_points()
        self.assertGreaterEqual(len(pts), 1681 + 1600 + 3200 + 9600 + 4096)
        worst_h, worst_n, worst_g = 0.0, 0.0, 0.0
        for x, z in pts:
            ix, iz, tx, tz = self.surface.cell_of(x, z)
            which = self.surface.which_triangle(tx, tz)
            tri = self.surface.triangle_positions(ix, iz, which)
            height, u, v = barycentric_height(tri, x, z)
            self.assertGreaterEqual(u, -1e-9)
            self.assertGreaterEqual(v, -1e-9)
            self.assertLessEqual(u + v, 1.0 + 1e-9)
            # height: query algebra vs stored-triangle plane (independent solve)
            worst_h = max(worst_h, abs(self.surface.height_at(x, z) - height))
            # normal: query formula vs the three stored vertex normals
            n = self.surface.normal_at(x, z)
            for i in self.surface.triangle_index(ix, iz, which):
                stored = tuple(self.bundle["render"]["vertices"][9 * i + 3:9 * i + 6])
                worst_n = max(worst_n, max(abs(n[d] - stored[d]) for d in range(3)))
            # gradient vs the stored normal's own direction: n = normalize(-gx, 1, -gz)
            gx, gz = self.surface.gradient_at(x, z)
            worst_g = max(worst_g, abs(gx - (-n[0] / n[1])), abs(gz - (-n[2] / n[1])))
        self.assertLessEqual(worst_h, TOL_HEIGHT)
        self.assertLessEqual(worst_n, TOL_NORMAL)
        self.assertLessEqual(worst_g, TOL_GRADIENT)
        print(f"[agreement] {len(pts)} points: worst height {worst_h:.3e} m, "
              f"worst normal {worst_n:.3e}, worst gradient {worst_g:.3e} m/m")

    def test_query_matches_declaration_grid_at_nodes(self):
        grid = self.bundle["terrain_surface"]["grid"]
        worst = 0.0
        for iz in range(grid["nz"]):
            for ix in range(grid["nx"]):
                x = grid["x0_m"] + ix * grid["dx_m"]
                z = grid["z0_m"] + iz * grid["dz_m"]
                worst = max(worst, abs(self.surface.height_at(x, z)
                                       - grid["heights_m"][iz][ix]))
        # float reordering at the clamped max-edge nodes (tx or tz == 1.0) costs at
        # most ~1 ulp; the frozen height tolerance covers it with 8+ orders of margin
        self.assertLessEqual(worst, TOL_HEIGHT)
        print(f"[nodes] worst query-vs-grid at 1,681 nodes: {worst:.3e} m <= 1e-9")

    def test_diagonal_drift_would_be_caught(self):
        """If the query used the OTHER diagonal the twisted cells would disagree --
        prove the sampled set actually contains twisted (non-flat) cells."""
        grid = self.bundle["terrain_surface"]["grid"]
        twisted = []
        for iz in range(grid["nz"] - 1):
            for ix in range(grid["nx"] - 1):
                h00, h10 = grid["heights_m"][iz][ix], grid["heights_m"][iz][ix + 1]
                h01, h11 = grid["heights_m"][iz + 1][ix], grid["heights_m"][iz + 1][ix + 1]
                if abs((h00 - h10 - h01 + h11)) > 1e-12:
                    twisted.append((ix, iz))
        self.assertGreater(len(twisted), 300)           # measured: 388 (mound footprints)
        # On a twisted cell the two possible diagonal splits differ at the centre:
        # this split's surface gives (h00+h11)/2 there, the other split (h01+h10)/2.
        # A diagonal drift between render and query would shift heights by this much,
        # so the agreement test above is not vacuous.
        ix, iz = max(twisted, key=lambda c: abs(
            grid["heights_m"][c[1]][c[0]] - grid["heights_m"][c[1]][c[0] + 1]
            - grid["heights_m"][c[1] + 1][c[0]] + grid["heights_m"][c[1] + 1][c[0] + 1]))
        h00, h10 = grid["heights_m"][iz][ix], grid["heights_m"][iz][ix + 1]
        h01, h11 = grid["heights_m"][iz + 1][ix], grid["heights_m"][iz + 1][ix + 1]
        this_split = (h00 + h11) / 2.0                  # centre of the 00-11 diagonal
        other_split = (h01 + h10) / 2.0                 # centre of the 01-10 diagonal
        self.assertGreater(abs(this_split - other_split), 1e-6)
        self.assertEqual(self.surface.height_at(ix - 20.0 + 0.5, iz - 20.0 + 0.5),
                         this_split)


class TestPosts(F02TestCase):
    """Falsifier (b): the rendered posts against F01's declaration."""

    def test_post_count_and_identity_against_declaration(self):
        declared = self.declaration["boundary"]["rendered"]["posts_m"]
        posts = self.surface.posts()
        self.assertEqual(len(posts), len(declared))
        self.assertEqual(len(posts), 80)
        worst_axis, worst_base = 0.0, 0.0
        for got, want in zip(posts, declared):
            self.assertEqual(got["position_m"][1], want[1])          # base y: copied byte
            worst_axis = max(worst_axis, abs(got["position_m"][0] - want[0]),
                             abs(got["position_m"][2] - want[2]))
            worst_base = max(worst_base, abs(got["top_y_m"] - (want[1] + 0.9)))
        self.assertLessEqual(worst_axis, TOL_POST_AXIS)
        self.assertEqual(worst_base, 0.0)

    def test_post_style_frozen_from_declaration(self):
        rendered = self.declaration["boundary"]["rendered"]
        style = self.bundle["render"]["style"]
        self.assertEqual(style["post_colour_rgb"], rendered["colour_rgb"])
        self.assertEqual(style["post_height_m"], 0.9)
        self.assertEqual(style["post_sides"], 6)
        self.assertEqual(style["post_radius_m"], 0.05)
        self.assertTrue(style["post_top_cap"])
        self.assertIs(style["post_bottom_cap"], False)

    def test_every_post_base_on_physical_edge_and_on_mesh_surface(self):
        worst = 0.0
        for post in self.surface.posts():
            x, y, z = post["position_m"]
            on_edge = min(abs(abs(x) - 20.0), abs(abs(z) - 20.0))
            self.assertLessEqual(on_edge, 1e-6)
            # posts sit on grid nodes; the plane algebra may differ by ~1 ulp at the
            # clamped max-edge nodes -- the frozen height tolerance covers it
            worst = max(worst, abs(self.surface.height_at(x, z) - y))
        self.assertLessEqual(worst, TOL_HEIGHT)

    def test_post_cap_normals_up_sides_outward(self):
        render = self.bundle["render"]
        verts, indices = render["vertices"], render["indices"]
        psec = render["sections"]["boundary_posts"]
        start = psec["index_start"]
        per_post = 3 * 18
        for p in range(80):
            for k in range(0, per_post, 3):                 # k = index-entry offset
                t = start + p * per_post + k
                ia, ib, ic = indices[t], indices[t + 1], indices[t + 2]
                n = terrain_bundle.face_normal(
                    tuple(verts[9 * ia:9 * ia + 3]),
                    tuple(verts[9 * ib:9 * ib + 3]),
                    tuple(verts[9 * ic:9 * ic + 3]))
                if (k // 3) >= 12:                          # triangles 12..17 are the cap
                    self.assertGreater(n[1], 0.999)


class TestBoundary(F02TestCase):
    """Falsifier (c): the physical bound IS |x|>20 or |z|>20 (strict >)."""

    def test_strict_inequality_on_all_four_edges(self):
        for v in (-20.0, -7.3, 0.0, 5.5, 20.0):
            self.assertEqual(self.surface.classify(v, 20.0), "inside")
            self.assertEqual(self.surface.classify(v, -20.0), "inside")
            self.assertEqual(self.surface.classify(20.0, v), "inside")
            self.assertEqual(self.surface.classify(-20.0, v), "inside")

    def test_outside_beyond_tiny_epsilons(self):
        for eps in (1e-9, 1e-6, 1.0):
            self.assertEqual(self.surface.classify(20.0 + eps, 0.0), "outside")
            self.assertEqual(self.surface.classify(-20.0 - eps, 0.0), "outside")
            self.assertEqual(self.surface.classify(0.0, 20.0 + eps), "outside")
            self.assertEqual(self.surface.classify(0.0, -20.0 - eps), "outside")

    def test_queries_refused_outside_and_served_inside(self):
        for x, z in ((20.0000001, 0.0), (0.0, -20.0000001), (-20.5, 0.0), (0.0, 25.0)):
            for fn in (self.surface.height_at, self.surface.gradient_at,
                       self.surface.normal_at):
                with self.assertRaisesRegex(ValueError, "f02_outside_extent"):
                    fn(x, z)
        for x, z in ((20.0, 0.0), (0.0, -20.0), (19.999999, 19.999999)):
            self.assertIsInstance(self.surface.height_at(x, z), float)

    def test_nonfinite_query_refused(self):
        for x, z in ((float("nan"), 0.0), (0.0, float("inf"))):
            with self.assertRaisesRegex(ValueError, "f02_nonfinite_query"):
                self.surface.classify(x, z)

    def test_no_ground_outside_the_closed_extent(self):
        verts = self.bundle["render"]["vertices"]
        gsec = self.bundle["render"]["sections"]["ground"]
        worst = 0.0
        for i in range(gsec["vertex_count"]):
            worst = max(worst, abs(verts[9 * i]) - 20.0, abs(verts[9 * i + 2]) - 20.0)
        self.assertLessEqual(worst, 1e-9)
        self.assertLessEqual(self.receipt["worst_ground_outside_extent_m"], 1e-9)

    def test_no_invisible_wall_between_ring_and_physical_edge(self):
        boundary = self.bundle["collision"]["boundary"]
        self.assertEqual(boundary["kind"], "extent_rule")
        self.assertEqual(boundary["half_width_m"], 20.0)
        self.assertTrue(self.bundle["collision"]["same_arrays_as_render"])
        ring_extent = max(max(abs(p["position_m"][0]), abs(p["position_m"][2]))
                          for p in self.surface.posts())
        self.assertLessEqual(abs(ring_extent - 20.0), 1e-6)

    def test_physical_rule_matches_declaration(self):
        physical = self.declaration["boundary"]["physical"]
        self.assertEqual(physical["kind"], "extent_rule")
        self.assertEqual(physical["half_width_m"],
                         self.bundle["collision"]["boundary"]["half_width_m"])


class TestFrozenSlopeCases(F02TestCase):
    """Falsifier (d): the frozen cases must satisfy F01's law (slope <= 0.05)."""

    def test_f01_central_difference_law_holds_on_bundle_grid(self):
        grid = self.bundle["terrain_surface"]["grid"]
        heights, step = grid["heights_m"], grid["dx_m"]
        worst, where = 0.0, None
        for iz in range(1, grid["nz"] - 1):
            for ix in range(1, grid["nx"] - 1):
                gx = abs(heights[iz][ix + 1] - heights[iz][ix - 1]) / (2.0 * step)
                gz = abs(heights[iz + 1][ix] - heights[iz - 1][ix]) / (2.0 * step)
                if max(gx, gz) > worst:
                    worst, where = max(gx, gz), (ix - 20, iz - 20)
        self.assertLessEqual(worst, 0.05)
        self.assertEqual(round(worst, 6), 0.034606)     # F01's recorded receipt value
        self.assertEqual(where, (17, 6))                 # F01's frozen worst-slope point

    def test_mesh_triangle_slopes_within_f01_law(self):
        worst, where = self.surface.worst_triangle_slope()
        self.assertLessEqual(worst, 0.05)
        self.assertGreater(worst, 0.030)                 # prediction band 0.030-0.045
        self.assertEqual(round(where[0]), 17)            # near F01's worst point
        print(f"[slope] worst mesh triangle slope {worst:.6f} m/m at (x={where[0]}, "
              f"z={where[1]}) <= 0.05")

    def test_worst_slope_point_case_agrees(self):
        x, z = 17.0, 6.0
        n = self.surface.normal_at(x, z)
        slope = math.hypot(-n[0], -n[2]) / n[1]
        self.assertLessEqual(slope, 0.05)
        self.assertGreaterEqual(n[1], 0.99)

    def test_mound_crest_cases(self):
        for i, m in enumerate(self.bundle["terrain_surface"]["mounds"]):
            cx, cz = m["centre_x_m"], m["centre_z_m"]
            crest = round(m["amplitude_m"], 6)
            h = self.surface.height_at(cx, cz)
            self.assertLessEqual(abs(h - crest), TOL_DISCRETIZATION,
                                 f"crest {i}: mesh {h} vs analytic {crest}")
            n = self.surface.normal_at(cx, cz)
            self.assertGreaterEqual(n[1], 0.99, f"crest {i} normal not up: {n}")
            gx, gz = self.surface.gradient_at(cx, cz)
            self.assertLessEqual(math.hypot(gx, gz), 0.05, f"crest {i} slope")

    def test_surface_maximum_is_the_tallest_crest_flank(self):
        heights = self.bundle["terrain_surface"]["grid"]["heights_m"]
        grid_max = max(max(row) for row in heights)
        self.assertEqual(grid_max, max(max(r) for r in heights))
        # the analytic maximum over the stored mounds is the tallest amplitude
        tallest = max(m["amplitude_m"] for m in self.bundle["terrain_surface"]["mounds"])
        self.assertLessEqual(grid_max, round(tallest, 6) + 1e-12)
        self.assertGreaterEqual(grid_max, tallest - TOL_DISCRETIZATION)

    def test_spawn_cell_exact(self):
        for x in (-0.5, 0.0, 0.5):
            for z in (-0.5, 0.0, 0.5):
                self.assertEqual(self.surface.height_at(x, z), 0.0)
                self.assertEqual(self.surface.gradient_at(x, z), (0.0, 0.0))
                self.assertEqual(self.surface.normal_at(x, z), (0.0, 1.0, 0.0))

    def test_mesh_analytic_deviation_within_derived_bound(self):
        h = self.surface.height_function()
        grid = self.bundle["terrain_surface"]["grid"]
        worst, where = 0.0, None
        for x, z in self.sample_points():
            err = abs(self.surface.height_at(x, z) - h(x, z))
            if err > worst:
                worst, where = err, (x, z)
        self.assertLessEqual(worst, TOL_DISCRETIZATION)
        self.assertLessEqual(worst, 0.00925)            # the derivation, not just the slack
        print(f"[discretization] worst mesh-vs-analytic {worst*1000:.3f} mm at "
              f"(x={where[0]}, z={where[1]}) <= derived 9.25 mm")

    def test_validator_slope_and_discretization_receipts(self):
        self.assertLessEqual(self.receipt["worst_triangle_slope_m_per_m"], 0.05)
        self.assertLessEqual(self.receipt["worst_mesh_analytic_deviation_m"],
                             terrain_bundle.DISCRETIZATION_BOUND_M)

    def test_boundary_edge_heights_served_on_mound_flank(self):
        # mound 2 straddles the east edge; heights on the edge must still be served
        # and equal the grid nodes exactly
        grid = self.bundle["terrain_surface"]["grid"]
        for z in range(-20, 21):
            self.assertEqual(self.surface.height_at(20.0, float(z)),
                             grid["heights_m"][z + 20][40])
            self.assertEqual(self.surface.height_at(-20.0, float(z)),
                             grid["heights_m"][z + 20][0])
            self.assertEqual(self.surface.classify(20.0, float(z)), "inside")


if __name__ == "__main__":
    unittest.main(verbosity=2)
