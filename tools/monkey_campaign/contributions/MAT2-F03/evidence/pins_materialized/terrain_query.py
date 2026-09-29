"""terrain_query -- M-F02: the clearing's physical query surface (collision binding).

Map item F02, contract C14: "compute geometry and gradient/normal consistently with
physical collision representation." The physical collision representation IS the
triangulation stored in ``terrain_bundle.json`` -- the SAME arrays the renderer uploads
via ``Engine::load_mesh``. This module reads those arrays and answers:

  height_at    the containing triangle's plane value        (exact, piecewise linear)
  gradient_at  the containing triangle's plane gradient     (exact per triangle)
  normal_at    normalized cross(b-a, c-a) on the stored positions
               (the engine's own formula, graph_earth.hpp:100 -- so the collision normal
               is bit-for-bit the normal the renderer stored)
  classify     the engine's out_of_patch rule, strict '>':
               outside = |x| > half_width_m or |z| > half_width_m
               (earth_environment.hpp:118); queries OFF the patch are REFUSED
               (f02_outside_extent) -- the engine stops there, no surface is served past it.

House laws honoured here (walker.py:163-174): ONE implementation -- there is no second
scalar truth, no duplicate bilinear, no re-derived grid. The module is stdlib-only and
refuses anything not proven by the bundle's own pinned numbers (validate_bundle runs at
load).
"""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path


def _load_sibling(name):
    full = "tools.monkey_campaign.data.monkey_clearing." + name
    try:
        return __import__(full, fromlist=[name])
    except ImportError:
        path = Path(__file__).resolve().with_name(name + ".py")
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


terrain_bundle = _load_sibling("terrain_bundle")

Refusal = terrain_bundle.Refusal
require = terrain_bundle.require


class TerrainSurface:
    """The clearing's ground: render arrays and query answers from one bundle."""

    def __init__(self, bundle, validate=True):
        if validate:
            terrain_bundle.validate_bundle(bundle)
        self.bundle = bundle
        grid = bundle["terrain_surface"]["grid"]
        self.mounds = bundle["terrain_surface"]["mounds"]
        self.x0 = grid["x0_m"]
        self.z0 = grid["z0_m"]
        self.dx = grid["dx_m"]
        self.dz = grid["dz_m"]
        self.nx = grid["nx"]
        self.nz = grid["nz"]
        self.heights = grid["heights_m"]
        self.half = bundle["collision"]["boundary"]["half_width_m"]
        render = bundle["render"]
        self.vertices = render["vertices"]
        self.indices = render["indices"]
        self.ground_index_count = render["sections"]["ground"]["index_count"]
        self.triangles_per_row = 2 * (self.nx - 1)

    # -- boundary (the physical rule; never refuses, mirrors out_of_patch) -------
    def classify(self, x, z):
        """'outside' means |x| > half or |z| > half (strict >), earth_environment.hpp:118."""
        require(math.isfinite(x) and math.isfinite(z), "f02_nonfinite_query", (x, z))
        outside = abs(x) > self.half or abs(z) > self.half
        return "outside" if outside else "inside"

    def _require_inside(self, x, z):
        require(math.isfinite(x) and math.isfinite(z), "f02_nonfinite_query", (x, z))
        require(abs(x) <= self.half and abs(z) <= self.half,
                "f02_outside_extent", (x, z, self.half))

    # -- containing triangle (the frozen diagonal rule) --------------------------
    def cell_of(self, x, z):
        """Grid cell (ix, iz) and local (tx, tz) in metres; edge-clamped on the max side."""
        self._require_inside(x, z)
        fx = (x - self.x0) / self.dx
        fz = (z - self.z0) / self.dz
        ix = min(int(math.floor(fx)), self.nx - 2)
        iz = min(int(math.floor(fz)), self.nz - 2)
        require(ix >= 0 and iz >= 0, "f02_query_below_grid", (x, z))
        tx = x - (self.x0 + ix * self.dx)
        tz = z - (self.z0 + iz * self.dz)
        return ix, iz, tx, tz

    def _corners(self, ix, iz):
        """Node heights (h00, h10, h01, h11): row = z, col = x (F01's grid convention)."""
        return (self.heights[iz][ix], self.heights[iz][ix + 1],
                self.heights[iz + 1][ix], self.heights[iz + 1][ix + 1])

    def which_triangle(self, tx, tz):
        """'A' = (00,01,11) covers tz >= tx; 'B' = (00,11,10) covers tz < tx."""
        return "A" if tz >= tx else "B"

    def triangle_index(self, ix, iz, which):
        base = 3 * (iz * self.triangles_per_row + 2 * ix + (0 if which == "A" else 1))
        require(base + 2 < self.ground_index_count, "f02_triangle_index", (ix, iz, which))
        return self.indices[base], self.indices[base + 1], self.indices[base + 2]

    def triangle_positions(self, ix, iz, which):
        return [tuple(self.vertices[9 * i:9 * i + 3])
                for i in self.triangle_index(ix, iz, which)]

    # -- the physical queries -----------------------------------------------------
    def height_at(self, x, z):
        ix, iz, tx, tz = self.cell_of(x, z)
        h00, h10, h01, h11 = self._corners(ix, iz)
        if self.which_triangle(tx, tz) == "A":            # (00, 01, 11)
            return h00 + (h11 - h01) * tx + (h01 - h00) * tz
        return h00 + (h10 - h00) * tx + (h11 - h10) * tz  # (00, 11, 10)

    def gradient_at(self, x, z):
        """(dh/dx, dh/dz): the containing triangle's OWN plane gradient (exact)."""
        ix, iz, tx, tz = self.cell_of(x, z)
        h00, h10, h01, h11 = self._corners(ix, iz)
        if self.which_triangle(tx, tz) == "A":
            return h11 - h01, h01 - h00
        return h10 - h00, h11 - h10

    def normal_at(self, x, z):
        """The engine's triangle normal on the stored render positions."""
        ix, iz, tx, tz = self.cell_of(x, z)
        which = self.which_triangle(tx, tz)
        pa, pb, pc = self.triangle_positions(ix, iz, which)
        return terrain_bundle.face_normal(pa, pb, pc)

    # -- surface-wide measurements -------------------------------------------------
    def worst_triangle_slope(self):
        """Max plane-slope magnitude over the ground triangles, and where it sits."""
        worst, where = 0.0, None
        for t in range(0, self.ground_index_count, 3):
            pa = tuple(self.vertices[9 * self.indices[t]:9 * self.indices[t] + 3])
            n = terrain_bundle.face_normal(
                pa,
                tuple(self.vertices[9 * self.indices[t + 1]:9 * self.indices[t + 1] + 3]),
                tuple(self.vertices[9 * self.indices[t + 2]:9 * self.indices[t + 2] + 3]))
            slope = math.hypot(-n[0], -n[2]) / n[1]
            if slope > worst:
                worst, where = slope, (pa[0], pa[2])
        return worst, where

    def posts(self):
        """The 80 declared post records recovered from the render mesh (axis midpoint)."""
        render = self.bundle["render"]
        postsec = render["sections"]["boundary_posts"]
        style = render["style"]
        per_post = 3 * (2 * style["post_sides"] + (style["post_sides"] if style["post_top_cap"] else 0))
        out = []
        for p in range(postsec["vertex_count"] // per_post):
            base = postsec["vertex_start"] + p * per_post
            xs = [self.vertices[9 * (base + v)] for v in range(per_post)]
            ys = [self.vertices[9 * (base + v) + 1] for v in range(per_post)]
            zs = [self.vertices[9 * (base + v) + 2] for v in range(per_post)]
            out.append({"position_m": [(min(xs) + max(xs)) / 2.0, min(ys),
                                        (min(zs) + max(zs)) / 2.0],
                        "top_y_m": max(ys)})
        return out

    def height_function(self):
        """The analytic mound function bound to THIS bundle's stored mounds (F01's
        height_at). Used only to measure the declared discretization -- never as a
        second query truth."""
        height_at = terrain_bundle.recipe.height_at
        mounds = self.mounds

        def h(x, z):
            return height_at(mounds, x, z)

        return h


def load(path):
    """Strict load: bundle bytes -> schema/digest/layout/geometry validation -> surface."""
    with open(path, "rb") as handle:
        bundle = terrain_bundle.loads(handle.read())
    return TerrainSurface(bundle, validate=True)
