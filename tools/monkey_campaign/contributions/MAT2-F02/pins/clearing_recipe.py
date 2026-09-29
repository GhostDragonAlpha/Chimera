"""clearing_recipe -- M-F01: the finite monkey clearing as deterministic data.

Schema ``chimera.monkey_clearing.v1``. Follows the house compiled-scene pattern
(tools/science_funnel/common.py): canonical JSON bytes, a self-pinned sha256 over
those bytes, strict ``require``/``Refusal`` intake, SI metres.

World convention (citations in agents/F01_clearing/discovery_note.md): right-handed,
+Y up, metres, origin at scene centre, base ground plane y=0. The physical extent is
a square of half-width EXTENT_HALF_WIDTH_M centred at the origin; "outside" is the
engine's existing out_of_patch rule (earth_environment.hpp:118), not a wall mesh.

Determinism: a self-contained splitmix64 integer PRNG -- stable across Python
versions and platforms, unlike ``random``. Every derived float is rounded onto the
1e-6 grid before the canonical write, so libm ulp differences cannot change the
bytes. Same seed -> byte-identical declaration anywhere.

Gentleness law (prereg amendments 1-2): mound footprints are DISJOINT by
construction (centre distance >= R_i + R_j), so at most one mound contributes at
any point and |grad h| <= max_i A_i*pi/(2*R_i) <= 0.12*pi/8 ~= 0.0471 <=
MAX_SLOPE_BOUND everywhere. Slopes of overlapping mounds would superpose (5 mounds
could reach ~0.236), which is why disjointness is a construction constraint, not a
style choice.

Frozen prereg: agents/F01_clearing/PREREGISTRATION.md (the values below ARE that
prereg, as amended by derivation before implementation).

F01 scope: terrain recipe + height grid, extent, safe spawn, one trunk SITE as data
(geometry qualified in F03), visible boundary ring. Terrain rendering and collision
surfaces are F02's; trunk geometry is F03's; obstacle placement is F07's.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys

SCHEMA = "chimera.monkey_clearing.v1"
NAME = "monkey_clearing"

# --- frozen prereg values (PREREGISTRATION.md; do not tune) -------------------
SEED = 4598321                      # 0x463031, ASCII "F01"
EXTENT_HALF_WIDTH_M = 20.0          # square extent: |x| <= 20 and |z| <= 20
MOUND_COUNT = 5
MOUND_RADIUS_MIN_M, MOUND_RADIUS_MAX_M = 4.0, 6.0
MOUND_AMPLITUDE_MIN_M, MOUND_AMPLITUDE_MAX_M = 0.05, 0.12
BASE_HEIGHT_M = 0.0
MAX_SLOPE_BOUND = 0.05              # |dh/dx|, |dh/dz| bound over the whole field
GRID_STEP_M = 1.0
GRID_N = 41                         # -20 .. 20 inclusive at 1 m spacing
R_BODY_ENVELOPE_M = 0.25            # declared macaque body-footprint envelope
R_TRUNK_BOUND_M = 0.5               # trunk footprint radius BOUND (geometry is F03's)
R_CLEAR_M = R_TRUNK_BOUND_M + 4.0 * R_BODY_ENVELOPE_M   # = 1.5, prereg derivation
TRUNK_ANNULUS_MIN_M, TRUNK_ANNULUS_MAX_M = 8.0, 14.0    # seeded distance from spawn
TRUNK_INSET_M = 3.0                 # trunk centre >= 3 m inside the extent
POST_HEIGHT_M = 0.9
POST_MIN_PROTRUSION_M = 0.6
POST_SPACING_M = 2.0
POST_MAX_GAP_M = POST_SPACING_M / 2.0                    # 1.0 m worst-case gap
POST_COLOUR_RGB = [0.72, 0.55, 0.20]
PERIMETER_SAMPLE_STEP_M = 0.05      # coverage sampling fineness for the validator
GRID_DECIMALS = 6                   # the 1e-6 determinism grid

_COORD_CITATIONS = [
    "ChimeraEngine/engine/coupled_dynamics.hpp:52 gravity_{0,-gravity,0} -> +Y up",
    "ChimeraEngine/engine/earth_environment.hpp:41,110 ground plane y=0, normal +Y",
    "ChimeraEngine/engine/earth_environment.hpp:44,68 potential m*g*x[1]; accel {0,-g,0}",
    "ChimeraEngine/engine/earth_environment.hpp:13-23 local frame EUS: x=east y=up z=south",
    "ChimeraEngine/engine/tests_environment/native.cpp:13 right_handed_frame east x up = south",
    "tools/science_funnel/units.py canonical SI length unit m",
    "ChimeraEngine/engine/earth_environment.hpp:118 out_of_patch: |x|>half or |z|>half",
]


class Refusal(ValueError):
    """Strict intake refusal, house style (tools/science_funnel/common.py)."""

    def __init__(self, code, detail=""):
        self.code, self.detail = code, str(detail)
        super().__init__(code + (": " + self.detail if detail else ""))


def require(condition, code, detail=""):
    if not condition:
        raise Refusal(code, detail)


def canonical(value):
    """House canonical bytes (tools/science_funnel/common.py::canonical)."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value):
    return sha(canonical(value))


def _grid6(value):
    """Snap onto the 1e-6 determinism grid (round-half-even, platform-stable)."""
    return round(float(value), GRID_DECIMALS)


# --- deterministic PRNG (splitmix64; self-contained, version-stable) ----------
_MASK64 = (1 << 64) - 1
_GOLDEN = 0x9E3779B97F4A7C15


class SplitMix64:
    def __init__(self, seed):
        require(isinstance(seed, int) and 0 <= seed <= _MASK64, "f01_seed_domain", seed)
        self._state = seed

    def next_u64(self):
        self._state = (self._state + _GOLDEN) & _MASK64
        z = self._state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _MASK64
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _MASK64
        return z ^ (z >> 31)

    def uniform_int(self, upper):
        """Uniform integer in [0, upper) via multiply-shift on the raw 64 bits."""
        require(upper > 0, "f01_rng_upper", upper)
        return (self.next_u64() * upper) >> 64

    def uniform_grid(self, low, high):
        """Uniform float in [low, high) snapped to the 1e-6 grid via integers."""
        span = int(round((high - low) * 10 ** GRID_DECIMALS))
        require(span > 0, "f01_rng_span", (low, high))
        return _grid6(low + self.uniform_int(span) / 10 ** GRID_DECIMALS)


# --- the terrain height function (single source of truth) ---------------------
def height_at(mounds, x, z):
    """Terrain height in metres at (x, z); base plane plus cosine mounds.

    Gentleness law: mounds are pairwise disjoint (centre distance >= R_i + R_j,
    enforced at placement and re-checked by the validator), so at most one mound
    contributes at any point and |grad h| <= max_i A_i*pi/(2*R_i)
    <= 0.12*pi/8 ~= 0.0471 <= MAX_SLOPE_BOUND everywhere.
    """
    h = BASE_HEIGHT_M
    for m in mounds:
        dx, dz = x - m["centre_x_m"], z - m["centre_z_m"]
        d = math.sqrt(dx * dx + dz * dz)
        if d < m["radius_m"]:
            h += m["amplitude_m"] * 0.5 * (1.0 + math.cos(math.pi * d / m["radius_m"]))
    return _grid6(h)


def _sample_mounds(rng):
    """MOUND_COUNT mounds, pairwise disjoint, centres kept >= radius + R_clear from
    the spawn at the origin, so the spawn disk sits on flat base ground by
    construction and the gentleness law holds without superposition."""
    mounds = []
    for _ in range(MOUND_COUNT):
        for _attempt in range(4096):
            radius = rng.uniform_grid(MOUND_RADIUS_MIN_M, MOUND_RADIUS_MAX_M)
            amplitude = rng.uniform_grid(MOUND_AMPLITUDE_MIN_M, MOUND_AMPLITUDE_MAX_M)
            cx = rng.uniform_grid(-EXTENT_HALF_WIDTH_M, EXTENT_HALF_WIDTH_M)
            cz = rng.uniform_grid(-EXTENT_HALF_WIDTH_M, EXTENT_HALF_WIDTH_M)
            if math.hypot(cx, cz) < radius + R_CLEAR_M:
                continue                                   # spawn exclusion
            if any(math.hypot(cx - m["centre_x_m"], cz - m["centre_z_m"])
                   < radius + m["radius_m"] for m in mounds):
                continue                                   # disjointness (amendment 2)
            mounds.append({"centre_x_m": cx, "centre_z_m": cz,
                           "radius_m": radius, "amplitude_m": amplitude})
            break
        else:
            raise Refusal("f01_mound_placement_exhausted")
    return mounds


def _sample_trunk_site(rng, mounds):
    """One trunk SITE inside the frozen annulus around the spawn and >= 3 m inside
    the extent. Spawn safety holds by construction: the annulus inner radius (8 m)
    strictly exceeds the required clearance (R_clear = 1.5 m plus the footprint
    bound, 2.0 m in total)."""
    lo = -EXTENT_HALF_WIDTH_M + TRUNK_INSET_M
    hi = EXTENT_HALF_WIDTH_M - TRUNK_INSET_M
    for _attempt in range(4096):
        x = rng.uniform_grid(lo, hi)
        z = rng.uniform_grid(lo, hi)
        if TRUNK_ANNULUS_MIN_M <= math.hypot(x, z) <= TRUNK_ANNULUS_MAX_M:
            slope = max(abs(height_at(mounds, x + 0.5, z) - height_at(mounds, x - 0.5, z)),
                        abs(height_at(mounds, x, z + 0.5) - height_at(mounds, x, z - 0.5)))
            return {"id": "trunk_01",
                    "site_m": [x, height_at(mounds, x, z), z],
                    "footprint_radius_bound_m": R_TRUNK_BOUND_M,
                    "axis": [0.0, 1.0, 0.0],
                    "geometry_qualified_in": "F03",
                    "note": "SITE data only: trunk geometry, surface IDs and material "
                            "provenance are qualified in F03; footprint_radius_bound_m "
                            "is the maximum envelope collision authoring must respect.",
                    "terrain_slope_at_site_m_per_m": _grid6(slope)}
    raise Refusal("f01_trunk_placement_exhausted")


def _perimeter_points():
    """Post anchor points ON the perimeter lines, 2.0 m apart, corners shared.

    south z=-20: x = -20..20 (21, both corners) · east x=+20: z = -18..20 (20,
    includes the top corner) · north z=+20: x = 18..-20 (20, includes the left
    corner) · west x=-20: z = 18..-18 (19). Total 80 = perimeter 160 m / 2.0 m.
    """
    half = EXTENT_HALF_WIDTH_M
    steps = int(round(2.0 * half / POST_SPACING_M))
    require(2.0 * half == steps * POST_SPACING_M, "f01_perimeter_not_on_grid")
    edge = [-half + i * POST_SPACING_M for i in range(steps + 1)]   # -20 .. 20
    pts = [(x, -half) for x in edge]                     # south: 21, both corners
    pts += [(half, z) for z in edge[1:]]                 # east: 20, incl. (20, 20)
    pts += [(x, half) for x in edge[-2::-1]]             # north: 20, incl. (-20, 20)
    pts += [(-half, z) for z in edge[-2:0:-1]]           # west: 19, no corners
    return pts


def _sample_boundary(mounds):
    posts = [[_grid6(x), height_at(mounds, x, z), _grid6(z)] for x, z in _perimeter_points()]
    return {"kind": "post_ring",
            "post_height_m": POST_HEIGHT_M,
            "min_protrusion_m": POST_MIN_PROTRUSION_M,
            "post_spacing_m": POST_SPACING_M,
            "max_gap_to_post_m": POST_MAX_GAP_M,
            "colour_rgb": list(POST_COLOUR_RGB),
            "posts_m": posts,
            "note": "Rendered markers for the physical extent edge (F02 renders them). "
                    "The blocking rule is the extent rule itself, and every post base "
                    "lies on that same edge -- no invisible wall may exist between the "
                    "walkable area and the visible ring (F07's law)."}


# --- compile / write / load ----------------------------------------------------
def compile_declaration(seed=SEED):
    """Deterministic compile: same seed -> byte-identical declaration, anywhere."""
    rng = SplitMix64(seed)
    mounds = _sample_mounds(rng)
    trunk = _sample_trunk_site(rng, mounds)
    xs = [_grid6(-EXTENT_HALF_WIDTH_M + i * GRID_STEP_M) for i in range(GRID_N)]
    zs = [_grid6(-EXTENT_HALF_WIDTH_M + i * GRID_STEP_M) for i in range(GRID_N)]
    grid = [[height_at(mounds, x, z) for x in xs] for z in zs]   # row = z, col = x
    declaration = {
        "schema": SCHEMA,
        "name": NAME,
        "seed": seed,
        "coordinate_convention": {
            "units": "m", "up_axis": "+y", "handedness": "right",
            "axes": {"x": "east", "y": "up", "z": "south"},
            "origin": "scene centre at the base ground plane (y=0)",
            "citations": list(_COORD_CITATIONS),
        },
        "extent": {
            "shape": "square", "half_width_m": EXTENT_HALF_WIDTH_M,
            "boundary_rule": "outside means |x| > half_width_m or |z| > half_width_m "
                             "(engine out_of_patch semantics, earth_environment.hpp:118)",
        },
        "terrain": {
            "base_height_m": BASE_HEIGHT_M,
            "recipe": {"kind": "cosine_mounds", "mounds": mounds,
                       "height_function": "h = base + A*(1+cos(pi*d/R))/2 for d < R, "
                                          "rounded to the 1e-6 grid"},
            "max_slope_bound": MAX_SLOPE_BOUND,
            "grid": {"x0_m": xs[0], "z0_m": zs[0],
                     "dx_m": GRID_STEP_M, "dz_m": GRID_STEP_M,
                     "nx": GRID_N, "nz": GRID_N, "heights_m": grid},
        },
        "spawn": {
            "position_m": [0.0, height_at(mounds, 0.0, 0.0), 0.0],
            "body_radius_envelope_m": R_BODY_ENVELOPE_M,
            "required_clearance_m": R_CLEAR_M,
            "derivation": "R_clear = r_trunk_bound + 4*r_body = "
                          f"{R_TRUNK_BOUND_M} + 4*{R_BODY_ENVELOPE_M} = {R_CLEAR_M}; "
                          "spawn fixed at the extent centre; mound footprints are "
                          "excluded within R_clear of it, so h(spawn)=0 by construction",
        },
        "trunk_sites": [trunk],
        "boundary": {"physical": {"kind": "extent_rule",
                                  "half_width_m": EXTENT_HALF_WIDTH_M},
                     "rendered": _sample_boundary(mounds)},
        "scope": "Finite clearing data for the monkey product lane. One clearing; no "
                 "planet or infinite-world requirement. Terrain rendering and collision "
                 "surfaces are F02's; trunk geometry, surface IDs and material "
                 "provenance are F03's (this file carries the SITE only); forest "
                 "obstacle placement is F07's.",
    }
    declaration["declaration_sha256"] = digest(declaration)   # over bytes without it
    return declaration


def write_declaration(declaration, path):
    raw = canonical(declaration)
    with open(path, "wb") as handle:
        handle.write(raw)
    return raw


def loads(raw):
    """Strict JSON intake: duplicate keys and non-finite numbers refused."""
    def unique(pairs):
        out = {}
        for key, value in pairs:
            require(key not in out, "f01_duplicate_json_key", key)
            out[key] = value
        return out

    def no_const(value):
        raise Refusal("f01_nonfinite_json", value)

    try:
        return json.loads(raw, object_pairs_hook=unique, parse_constant=no_const)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise Refusal("f01_invalid_json", exc)


def load_declaration(path):
    with open(path, "rb") as handle:
        return loads(handle.read())


# --- validation (every check re-derived from stored numbers) -------------------
def _finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) \
        and math.isfinite(value)


def _require_finite_list(value, code, n=None):
    require(isinstance(value, list) and all(_finite(v) for v in value), code, value)
    if n is not None:
        require(len(value) == n, code, len(value))


def _expected_posts():
    return len(_perimeter_points())


def validate_declaration(declaration, strict_prereg=True):
    """Full validation; raises Refusal on any violation. Returns a receipt dict.

    With ``strict_prereg`` the declaration is also checked against THIS module's
    frozen constants, so a hand-edited declaration cannot drift from the prereg.
    """
    require(isinstance(declaration, dict), "f01_declaration_object")
    require(declaration.get("schema") == SCHEMA, "f01_schema", declaration.get("schema"))
    require(declaration.get("name") == NAME, "f01_name", declaration.get("name"))
    seed = declaration.get("seed")
    require(isinstance(seed, int) and not isinstance(seed, bool) and seed >= 0,
            "f01_seed", seed)

    # pinned digest over the canonical bytes without the pin itself
    pinned = declaration.get("declaration_sha256")
    body = {k: v for k, v in declaration.items() if k != "declaration_sha256"}
    require(isinstance(pinned, str) and len(pinned) == 64, "f01_digest_form", pinned)
    require(sha(canonical(body)) == pinned, "f01_digest_mismatch")

    # -- coordinate convention (frozen; citations required in the data) --------
    conv = declaration.get("coordinate_convention")
    require(isinstance(conv, dict), "f01_convention_object")
    require(conv.get("units") == "m" and conv.get("up_axis") == "+y"
            and conv.get("handedness") == "right", "f01_convention_frozen", conv)
    require(isinstance(conv.get("citations"), list) and conv["citations"],
            "f01_convention_citations")

    # -- extent -----------------------------------------------------------------
    extent = declaration.get("extent")
    require(isinstance(extent, dict) and extent.get("shape") == "square"
            and extent.get("half_width_m") == EXTENT_HALF_WIDTH_M,
            "f01_extent_frozen", extent)
    require(isinstance(extent.get("boundary_rule"), str), "f01_extent_rule_text")

    # -- terrain: recipe, disjointness, grid == function, slope bound -----------
    terrain = declaration.get("terrain")
    require(isinstance(terrain, dict), "f01_terrain_object")
    require(terrain.get("base_height_m") == BASE_HEIGHT_M, "f01_terrain_base")
    recipe = terrain.get("recipe")
    require(isinstance(recipe, dict) and recipe.get("kind") == "cosine_mounds",
            "f01_terrain_recipe")
    mounds = recipe.get("mounds")
    require(isinstance(mounds, list) and len(mounds) == MOUND_COUNT,
            "f01_mound_count", mounds and len(mounds))
    spawn = declaration.get("spawn")
    require(isinstance(spawn, dict), "f01_spawn_object")
    for i, m in enumerate(mounds):
        require(isinstance(m, dict), "f01_mound_object")
        _require_finite_list([m.get("centre_x_m"), m.get("centre_z_m"),
                              m.get("radius_m"), m.get("amplitude_m")],
                             "f01_mound_fields", 4)
        require(MOUND_RADIUS_MIN_M <= m["radius_m"] <= MOUND_RADIUS_MAX_M,
                "f01_mound_radius", m["radius_m"])
        require(MOUND_AMPLITUDE_MIN_M <= m["amplitude_m"] <= MOUND_AMPLITUDE_MAX_M,
                "f01_mound_amplitude", m["amplitude_m"])
        require(math.hypot(m["centre_x_m"], m["centre_z_m"]) >= m["radius_m"] + R_CLEAR_M,
                "f01_mound_spawn_exclusion", m)
        for j in range(i):
            other = mounds[j]
            require(math.hypot(m["centre_x_m"] - other["centre_x_m"],
                               m["centre_z_m"] - other["centre_z_m"])
                    >= m["radius_m"] + other["radius_m"],
                    "f01_mounds_disjoint", (i, j))
    grid = terrain.get("grid")
    require(isinstance(grid, dict), "f01_grid_object")
    require(grid.get("nx") == GRID_N and grid.get("nz") == GRID_N, "f01_grid_dims")
    require(grid.get("dx_m") == GRID_STEP_M and grid.get("dz_m") == GRID_STEP_M
            and grid.get("x0_m") == -EXTENT_HALF_WIDTH_M
            and grid.get("z0_m") == -EXTENT_HALF_WIDTH_M, "f01_grid_frame")
    heights = grid.get("heights_m")
    require(isinstance(heights, list) and len(heights) == GRID_N, "f01_grid_rows")
    worst_grid_err = 0.0
    for iz, row in enumerate(heights):
        require(isinstance(row, list) and len(row) == GRID_N, "f01_grid_cols", iz)
        z = -EXTENT_HALF_WIDTH_M + iz * GRID_STEP_M
        for ix, value in enumerate(row):
            require(_finite(value), "f01_grid_value", (iz, ix))
            x = -EXTENT_HALF_WIDTH_M + ix * GRID_STEP_M
            worst_grid_err = max(worst_grid_err,
                                 abs(value - height_at(mounds, x, z)))
    require(worst_grid_err <= 1e-9, "f01_grid_function_mismatch", worst_grid_err)
    worst_slope = 0.0
    for iz in range(1, GRID_N - 1):
        for ix in range(1, GRID_N - 1):
            gx = abs(heights[iz][ix + 1] - heights[iz][ix - 1]) / (2.0 * GRID_STEP_M)
            gz = abs(heights[iz + 1][ix] - heights[iz - 1][ix]) / (2.0 * GRID_STEP_M)
            worst_slope = max(worst_slope, gx, gz)
    require(worst_slope <= MAX_SLOPE_BOUND, "f01_slope_bound", worst_slope)

    # -- spawn: on the ground, and the clearance derivation holds ---------------
    _require_finite_list(spawn.get("position_m"), "f01_spawn_position", 3)
    require(spawn.get("body_radius_envelope_m") == R_BODY_ENVELOPE_M
            and spawn.get("required_clearance_m") == R_CLEAR_M,
            "f01_spawn_bounds_frozen", spawn)
    require(isinstance(spawn.get("derivation"), str) and spawn["derivation"],
            "f01_spawn_derivation_text")
    sx, sy, sz = spawn["position_m"]
    require((sx, sz) == (0.0, 0.0), "f01_spawn_centre", (sx, sz))
    require(abs(sy - height_at(mounds, sx, sz)) <= 1e-9, "f01_spawn_on_ground", sy)
    require(sy == BASE_HEIGHT_M, "f01_spawn_flat_by_construction", sy)

    # -- trunk site: exactly one, safe distance, F03 marker ---------------------
    sites = declaration.get("trunk_sites")
    require(isinstance(sites, list) and len(sites) == 1, "f01_trunk_site_count")
    site = sites[0]
    require(isinstance(site, dict) and site.get("id") == "trunk_01", "f01_trunk_id")
    _require_finite_list(site.get("site_m"), "f01_trunk_site", 3)
    tx, ty, tz = site["site_m"]
    require(site.get("footprint_radius_bound_m") == R_TRUNK_BOUND_M,
            "f01_trunk_bound_frozen", site.get("footprint_radius_bound_m"))
    require(site.get("axis") == [0.0, 1.0, 0.0], "f01_trunk_axis")
    require(site.get("geometry_qualified_in") == "F03", "f01_trunk_f03_marker")
    require(abs(ty - height_at(mounds, tx, tz)) <= 1e-9, "f01_trunk_on_ground")
    inset = EXTENT_HALF_WIDTH_M - TRUNK_INSET_M
    require(abs(tx) <= inset and abs(tz) <= inset, "f01_trunk_inset", (tx, tz))
    dist_spawn = math.hypot(tx - sx, tz - sz)
    require(TRUNK_ANNULUS_MIN_M <= dist_spawn <= TRUNK_ANNULUS_MAX_M,
            "f01_trunk_annulus", dist_spawn)
    require(dist_spawn - R_TRUNK_BOUND_M >= R_CLEAR_M,
            "f01_spawn_clearance", dist_spawn - R_TRUNK_BOUND_M)

    # -- boundary: visible ring coincident with the physical edge ---------------
    boundary = declaration.get("boundary")
    require(isinstance(boundary, dict), "f01_boundary_object")
    physical = boundary.get("physical")
    require(isinstance(physical, dict)
            and physical.get("kind") == "extent_rule"
            and physical.get("half_width_m") == EXTENT_HALF_WIDTH_M,
            "f01_boundary_physical")
    rendered = boundary.get("rendered")
    require(isinstance(rendered, dict) and rendered.get("kind") == "post_ring",
            "f01_boundary_rendered")
    require(rendered.get("post_height_m") == POST_HEIGHT_M
            and rendered.get("min_protrusion_m") == POST_MIN_PROTRUSION_M
            and rendered.get("post_spacing_m") == POST_SPACING_M
            and rendered.get("max_gap_to_post_m") == POST_MAX_GAP_M
            and rendered.get("colour_rgb") == POST_COLOUR_RGB,
            "f01_boundary_render_frozen")
    posts = rendered.get("posts_m")
    require(isinstance(posts, list) and len(posts) == _expected_posts(),
            "f01_post_count", posts and len(posts))
    half = EXTENT_HALF_WIDTH_M
    worst_on_edge = 0.0
    for p in posts:
        _require_finite_list(p, "f01_post_fields", 3)
        px, py, pz = p
        on_edge = min(abs(abs(px) - half), abs(abs(pz) - half))
        worst_on_edge = max(worst_on_edge, on_edge)
        require(on_edge <= 1e-6, "f01_post_off_edge", (px, pz))
        require(abs(py - height_at(mounds, px, pz)) <= 1e-9, "f01_post_base_ground")
    require(POST_HEIGHT_M >= POST_MIN_PROTRUSION_M, "f01_post_visibility")
    # coverage: sample the whole perimeter, nearest-post distance <= the frozen gap
    worst_gap = 0.0
    steps = int(round(4.0 * half / PERIMETER_SAMPLE_STEP_M))
    edge_len = 2.0 * half
    for i in range(steps):
        s = i * PERIMETER_SAMPLE_STEP_M
        if s < edge_len:
            qx, qz = -half + s, -half
        elif s < 2 * edge_len:
            qx, qz = half, -half + (s - edge_len)
        elif s < 3 * edge_len:
            qx, qz = half - (s - 2 * edge_len), half
        else:
            qx, qz = -half, half - (s - 3 * edge_len)
        gap = min(math.hypot(qx - p[0], qz - p[2]) for p in posts)
        worst_gap = max(worst_gap, gap)
    require(worst_gap <= POST_MAX_GAP_M + 1e-6, "f01_boundary_coverage", worst_gap)
    # invisible-wall guard: the physical edge IS the rendered ring's edge
    ring_extent = max(max(abs(p[0]), abs(p[2])) for p in posts)
    require(abs(ring_extent - half) <= 1e-6, "f01_invisible_wall", ring_extent - half)

    return {"schema": SCHEMA, "seed": seed,
            "declaration_sha256": pinned,
            "mounds": len(mounds), "grid_points": GRID_N * GRID_N,
            "worst_grid_error_m": worst_grid_err,
            "worst_grid_slope_m_per_m": worst_slope,
            "spawn_clearance_m": dist_spawn - R_TRUNK_BOUND_M,
            "required_clearance_m": R_CLEAR_M,
            "trunk_site_m": [tx, ty, tz],
            "posts": len(posts), "worst_on_edge_error_m": worst_on_edge,
            "worst_gap_to_post_m": worst_gap,
            "validated": True}


def selftest():
    """Compile + validate round trip; returns the validation receipt."""
    return validate_declaration(compile_declaration())


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    default = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "clearing_declaration.json")
    if not argv or argv[0] == "compile":
        path = argv[1] if len(argv) > 1 else default
        declaration = compile_declaration()
        raw = write_declaration(declaration, path)
        print(json.dumps({"declaration": path, "bytes": len(raw),
                          "declaration_sha256": declaration["declaration_sha256"]}))
        return 0
    if argv[0] == "validate":
        path = argv[1] if len(argv) > 1 else default
        receipt = validate_declaration(load_declaration(path))
        print(json.dumps(receipt, sort_keys=True))
        return 0
    if argv[0] == "selftest":
        print(json.dumps(selftest(), sort_keys=True))
        return 0
    raise Refusal("f01_cli_verb", argv)


if __name__ == "__main__":
    sys.exit(main())
