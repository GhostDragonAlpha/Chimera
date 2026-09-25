"""route_recipe -- M-F07: the clearing's route/blocking layer as deterministic data.

Schema ``chimera.monkey_routes.v1``. Map item F07, contracts C14 + C23(note):
"The clearing offers traversable routes; no invisible walls masquerade as
physical obstacles. Player steering needs no general autonomous pathfinding."

This module compiles the ROUTE/BLOCKING declarations from the three LIVE
integrated artifacts (F01 clearing, F02 terrain bundle, F03 trunk) -- it owns
NO geometry of its own: every blocker, bound and route below is derived from
pinned numbers, and the validator re-derives every claim from stored numbers.

The blocking-causes table (frozen in agents/F07_obstacles/PREREGISTRATION.md
BEFORE implementation) has exactly two YES rows -- B1 the extent rule (visible
as F01's 80-post ring standing on that same edge) and B2 the trunk solid
(F03's analytic cylinder + the walker's body envelope) -- and two NO rows
(N1 mound slopes under the 0.05 walk law; N2 boundary posts, render-only per
F04 VIS-03). ``traversable`` in the verify suite contains ONLY the B1/B2/N1
predicates; there is no post term and no other refuse site, which is the
structural half of the no-invisible-wall proof.

World convention: F01's (right-handed, +Y up, metres, origin at scene centre).
Stdlib-only, CPU-only, headless. Same live inputs -> byte-identical
declaration (derived floats snapped to the 1e-6 grid, F01's rule).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import sys

SCHEMA = "chimera.monkey_routes.v1"
NAME = "monkey_routes"

# --- frozen prereg values (agents/F07_obstacles/PREREGISTRATION.md) -----------
R_BODY_ENVELOPE_M = 0.25            # F01's declared body-footprint envelope (consumed)
STANCE_FLOOR_M = 2.0 * R_BODY_ENVELOPE_M          # 0.5 -- the envelope fits
W_ENV_M = 4.0 * R_BODY_ENVELOPE_M                 # 1.0 -- F01's passing-room quantum
CORRIDOR_MIN_CLEARANCE_M = W_ENV_M / 2.0          # 0.5 m min clearance to any blocker
R_TRUNK_M = 0.037                   # F03's analytic solid (consumed)
R_BLOCK_M = R_TRUNK_M + R_BODY_ENVELOPE_M         # 0.287 -- the routing blocker
APPROACH_ZONE_R_M = R_BLOCK_M + 2.0 * R_BODY_ENVELOPE_M   # 0.787 -- width -> 0 by design
MAX_SLOPE_M_PER_M = 0.05            # F01's walk law (consumed)
EXTENT_HALF_WIDTH_M = 20.0          # F01's extent (consumed)
GRID_STEP_M = 0.05                  # r_body / 5 -- stance radius spans 5 cells
GRID_N = 801                        # 40 m / 0.05 m + 1, over the CLOSED extent
CONNECTIVITY = 8                    # 8-connected BFS (cannot leak the ~11-cell B2 disk)
CONTACT_BAND_M = GRID_STEP_M * math.sqrt(2.0)    # contact-ring band width
STRAIGHT_SAMPLE_STEP_M = 0.01       # route sampling fineness (s_tick is 3.37e-3 m)
EDGE_RAY_MAX_STOP_SHORT_M = GRID_STEP_M          # ray must reach the post line
GRID_DECIMALS = 6                   # the 1e-6 determinism grid
# Derived rounding bound: the stored tangent direction is rounded to 1e-6, so the
# ray can rotate by |du| <= sqrt(2)*0.5e-6; over a lever arm up to the extent
# diagonal 20*sqrt(2) m the closest approach may fall short of the tangent radius
# by at most |du|*d_max = 2.0e-5 m (0.008% of the r_body = 0.25 m margin).
TANGENT_ROUND_TOL_M = 2.0e-5

# pinned walker numbers (citations, consumed -- not re-derived here)
STRIDE_M_PINNED = 0.72              # derived_numbers.json timing_paper.simulated_before
V_MAX_M_S = 1.01                    # same record, speed_m_s
DT_MAX_S = 1.0 / 300.0              # gait_controller.hpp:1961
SOLE_RADIUS_M = 0.004               # gait_scene.py:28
K_TOUCH = 1e-5                      # gait_scene.py:27

# frozen input pins (PREREGISTRATION.md; a mismatch is a refusal, not a re-pin)
_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))   # repo root (5 levels up)
INPUTS = {
    "clearing": {
        "path": "tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json",
        "schema": "chimera.monkey_clearing.v1",
        "declaration_sha256": "aa2607df97e0d6ec6a132b1e1ed0686da2ae920de7d659a8bb5ced013a358474",
        "file_sha256": "18dd2ff65410cd1cf184a7a8df61c7503a6ce15083f30159e727e9a8117bfbc1",
    },
    "terrain": {
        "path": "tools/monkey_campaign/data/monkey_clearing/terrain_bundle.json",
        "schema": "chimera.monkey_terrain.v1",
        "bundle_sha256": "8c7d60c88a75234a4ea94bc5ec83b666d620502b47cac8667e83b8713cb04fe0",
        "file_sha256": "446ed3fbd0f50205c61a7233ceca289bfc3316f76dfc672fec307b20d8305d52",
    },
    "trunk": {
        "path": "tools/monkey_campaign/data/monkey_trunk/trunk_declaration.json",
        "schema": "chimera.trunk_asset.v1",
        "declaration_sha256": "b7089e7826a221a570b261b8c69666a4017a6ab62d20a2223d061654d0f63fe3",
        "file_sha256": "94ff906ec5e8b8388e4de318aa3321bad9c791fbb168e8234c371ed1d327e3f1",
    },
}

WALKER_CITATIONS = [
    "tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json "
    "spawn.body_radius_envelope_m = 0.25 (F01's declared macaque envelope)",
    "F01 prereg passing-room derivation R_clear = r_trunk_bound + 4*r_body "
    "(agents/F01_clearing/PREREGISTRATION.md) -> W_env = 4*0.25 = 1.0 m",
    "tools/science_funnel/gait_scene.py:28 SOLE_RADIUS = 0.004 m; :27 K_TOUCH = 1e-5",
    "tools/science_funnel/validation/gait_controller_20260918/derived_numbers.json "
    "timing_paper.simulated_before speed_m_s 1.01, stride_m 0.72",
    "ChimeraEngine/engine/gait_controller.hpp:1961 dt <= 1/300 s",
    "tools/monkey_campaign/data/monkey_trunk/trunk_declaration.json "
    "geometry.radius_m = 0.037 (Oku foot 0.074/2)",
]


class Refusal(ValueError):
    """Strict intake refusal, house style."""

    def __init__(self, code, detail=""):
        self.code, self.detail = code, str(detail)
        super().__init__(code + (": " + self.detail if detail else ""))


def require(condition, code, detail=""):
    if not condition:
        raise Refusal(code, detail)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value):
    return sha(canonical(value))


def _grid6(value):
    return round(float(value), GRID_DECIMALS)


def file_sha256(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def _load_module(name, rel_path):
    """Import a sibling artifact module by package name, else by file path.

    ``rel_path`` is repo-relative without the .py extension, e.g.
    ``tools/monkey_campaign/data/monkey_clearing/clearing_recipe``.
    """
    try:
        return __import__("tools." + rel_path.replace("/", "."), fromlist=[name])
    except ImportError:
        path = os.path.join(_REPO, rel_path.replace("/", os.altsep or "/") + ".py")
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


def load_live_inputs():
    """Strict-load and fully validate the three live artifacts; return them."""
    clearing_mod = _load_module(
        "clearing_recipe", "tools/monkey_campaign/data/monkey_clearing/clearing_recipe")
    trunk_mod = _load_module(
        "trunk_recipe", "tools/monkey_campaign/data/monkey_trunk/trunk_recipe")
    out = {}
    for key, pin in INPUTS.items():
        path = os.path.join(_REPO, pin["path"])
        require(file_sha256(path) == pin["file_sha256"],
                "f07_input_drift", (key, pin["path"]))
    with open(os.path.join(_REPO, INPUTS["clearing"]["path"]), "rb") as handle:
        clearing = clearing_mod.loads(handle.read())
    receipt = clearing_mod.validate_declaration(clearing)
    require(receipt["declaration_sha256"] == INPUTS["clearing"]["declaration_sha256"],
            "f07_input_drift", "clearing body digest")
    with open(os.path.join(_REPO, INPUTS["trunk"]["path"]), "rb") as handle:
        trunk = trunk_mod.loads(handle.read())
    trunk_mod.validate_declaration(trunk)          # re-proves site vs LIVE F01 file
    require(trunk["declaration_sha256"] == INPUTS["trunk"]["declaration_sha256"],
            "f07_input_drift", "trunk body digest")
    terrain_mod = _load_module(
        "terrain_bundle", "tools/monkey_campaign/data/monkey_clearing/terrain_bundle")
    with open(os.path.join(_REPO, INPUTS["terrain"]["path"]), "rb") as handle:
        terrain = terrain_mod.loads(handle.read())
    terrain_mod.validate_bundle(terrain)
    require(terrain["bundle_sha256"] == INPUTS["terrain"]["bundle_sha256"],
            "f07_input_drift", "terrain self-pin")
    out.update(clearing=clearing, terrain=terrain, trunk=trunk,
               clearing_mod=clearing_mod, terrain_mod=terrain_mod,
               trunk_mod=trunk_mod)
    return out


# --- deterministic constructions (pure arithmetic on pinned numbers) ----------
def straight_route(spawn, site):
    """R0: the no-pathfinding route -- ONE heading from spawn to the trunk axis.

    The route ends at first contact with the B2 blocker disk (the walker's body
    envelope touching the solid). Sampling happens in the verify suite.
    """
    dx, dz = site[0] - spawn[0], site[2] - spawn[2]
    length = math.hypot(dx, dz)
    require(length > R_BLOCK_M, "f07_route_too_short", length)
    return {"id": "R0", "kind": "straight_heading",
            "from_m": [_grid6(spawn[0]), _grid6(spawn[2])],
            "to_m": [_grid6(site[0]), _grid6(site[2])],
            "length_m": _grid6(length),
            "contact_dist_from_axis_m": _grid6(R_BLOCK_M),
            "sample_step_m": STRAIGHT_SAMPLE_STEP_M,
            "note": "ends at the contact ring: dist_to_axis = r_block (envelope "
                    "touches the solid); the no-pathfinding claim is that this "
                    "single heading needs no waypoint search"}


def tangent_route(spawn, mound, side):
    """The straight segment from spawn tangent to the disk {C, R + r_body}.

    The walker's stance envelope must clear the visible footprint, so the
    tangent disk radius is R + r_body. Amendment 1 (prereg): the endpoint is
    the EARLIER of

      t_exit   -- exit from the enlarged disk {C, R + 2*r_body}: the walker has
                  passed the mound with the stance envelope clearing it. For a
                  ray at tangent distance rho = R + r_body the remaining
                  half-chord inside that disk is sqrt(r*(2R + 3r)) (exact:
                  (R+2r)^2 - (R+r)^2 = r*(2R+3r)), so t_exit = t_pass + that.
      t_extent -- the ray's exit from the closed extent (analytic wall times
                  on the stored direction): the walkable world ends there, at
                  the visible post line (declared cause B1).

    Closest approach to C equals the tangent radius by construction (within
    the derived direction-rounding tolerance); the verify suite measures it.
    """
    sx, sz = spawn[0], spawn[2]
    cx, cz = mound["centre_x_m"], mound["centre_z_m"]
    radius, rho = mound["radius_m"], _grid6(mound["radius_m"] + R_BODY_ENVELOPE_M)
    dx, dz = cx - sx, cz - sz
    d = math.hypot(dx, dz)
    require(d > rho, "f07_tangent_impossible", (mound, d, rho))
    alpha = math.asin(rho / d)                     # tangent half-angle
    base = math.atan2(dz, dx)
    sign = 1.0 if side == "L" else -1.0
    theta = base + sign * alpha
    ux, uz = _grid6(math.cos(theta)), _grid6(math.sin(theta))   # round FIRST: the
    # stored (rounded) direction is the single truth the validator re-derives from
    t_pass = dx * ux + dz * uz                     # = d*cos(alpha) on the stored dir
    half_chord = math.sqrt(R_BODY_ENVELOPE_M * (2.0 * radius + 3.0 * R_BODY_ENVELOPE_M))
    t_exit = t_pass + half_chord
    wall_times = []
    if ux > 0.0:
        wall_times.append((EXTENT_HALF_WIDTH_M - sx) / ux)
    elif ux < 0.0:
        wall_times.append((-EXTENT_HALF_WIDTH_M - sx) / ux)
    if uz > 0.0:
        wall_times.append((EXTENT_HALF_WIDTH_M - sz) / uz)
    elif uz < 0.0:
        wall_times.append((-EXTENT_HALF_WIDTH_M - sz) / uz)
    require(wall_times, "f07_tangent_zero_dir", (mound.get("_index"), side))
    t_extent = min(t for t in wall_times if t > 0.0)
    end_cause = "extent_edge" if t_extent <= t_exit else "passed_mound"
    t_end = _grid6(min(t_exit, t_extent))
    return {"id": "R%d%s" % (mound.get("_index", 0) + 1, side),
            "kind": "tangent_straight", "mound_index": mound.get("_index", 0),
            "side": side,
            "from_m": [_grid6(sx), _grid6(sz)],
            "dir_m": [ux, uz],
            "to_m": [_grid6(sx + ux * t_end), _grid6(sz + uz * t_end)],
            "t_end_m": t_end,
            "end_cause": end_cause,
            "mound_centre_m": [_grid6(cx), _grid6(cz)],
            "mound_radius_m": _grid6(radius),
            "mound_envelope_m": rho,
            "closest_approach_m": rho,             # by construction; measured in verify
            "pass_beyond_m": _grid6(half_chord),
            "sample_step_m": STRAIGHT_SAMPLE_STEP_M}


def build_routes(clearing):
    spawn = clearing["spawn"]["position_m"]
    site = clearing["trunk_sites"][0]["site_m"]
    mounds = []
    for index, m in enumerate(clearing["terrain"]["recipe"]["mounds"]):
        copy = dict(m)
        copy["_index"] = index
        mounds.append(copy)
    routes = {"spawn_m": [_grid6(spawn[0]), _grid6(spawn[1]), _grid6(spawn[2])],
              "trunk_axis_m": [_grid6(site[0]), _grid6(site[2])],
              "straight": straight_route(spawn, site),
              "tangents": [tangent_route(spawn, m, side)
                           for m in mounds for side in ("L", "R")]}
    return routes


def blocking_causes_table(trunk):
    """The frozen table: the two YES rows, two NO rows, zero unexplained."""
    solid = trunk["collision_representation"]["solid"]
    site = trunk["site"]["base_centre_m"]
    return {
        "blockers": [
            {"id": "B1", "kind": "extent_rule",
             "half_width_m": EXTENT_HALF_WIDTH_M, "strict_gt": True, "blocks": True,
             "predicate": "|x| > half or |z| > half",
             "visible": {"kind": "post_ring", "posts": 80, "post_height_m": 0.9,
                         "spacing_m": 2.0, "ring_extent_m": EXTENT_HALF_WIDTH_M},
             "physical_citation": "clearing.boundary.physical extent rule = engine "
                                  "out_of_patch (earth_environment.hpp:118)",
             "visible_citation": "clearing.boundary.rendered posts_m; F01 receipt "
                                 "worst off-edge 0.0, ring extent == 20.0"},
            {"id": "B2", "kind": "trunk_solid",
             "site_m": [_grid6(site[0]), _grid6(site[2])],
             "r_trunk_m": _grid6(solid["radius_m"]),
             "r_block_m": _grid6(R_BLOCK_M), "blocks": True,
             "predicate": "dist_to_axis < r_block (r_trunk + r_body)",
             "visible": {"mesh_vertices": trunk["render_mesh"]["vertex_count"],
                         "mesh_triangles": trunk["render_mesh"]["triangle_count"],
                         "representation_error_m": trunk["representation_error"]["max_measured_m"],
                         "representation_tolerance_m": trunk["representation_error"]["tolerance_m"]},
             "physical_citation": "trunk.collision_representation analytic_cylinder_solid "
                                  "(F03; F04 INT-01 tangency 7.0e-16)",
             "visible_citation": "trunk.render_mesh; F04 VIS-02 (inscribed within "
                                 "the declared 1.78307e-4 m)"},
        ],
        "non_blockers": [
            {"id": "N1", "kind": "mound_slopes", "blocks": False,
             "law_m_per_m": MAX_SLOPE_M_PER_M,
             "citation": "clearing.terrain.max_slope_bound (F01's walk law; "
                         "continuous bound <= 0.0471); F02 worst mesh slope 0.042522"},
            {"id": "N2", "kind": "boundary_posts", "blocks": False,
             "status": "render_only_no_claim",
             "citation": "F04 VIS-03 PASS-AS-DECLARED (NO-CLAIM): the physical "
                         "bound is the extent rule itself; posts are absent from "
                         "the traversal predicate (structural)"},
        ],
        "unexplained": [],
    }


def compile_declaration():
    """Deterministic compile from the LIVE artifacts (same inputs -> same bytes)."""
    live = load_live_inputs()
    clearing, trunk = live["clearing"], live["trunk"]
    spawn = clearing["spawn"]["position_m"]
    require(spawn[0] == 0.0 and spawn[2] == 0.0, "f07_spawn_not_centre", spawn)
    require(clearing["spawn"]["body_radius_envelope_m"] == R_BODY_ENVELOPE_M,
            "f07_r_body_frozen", clearing["spawn"]["body_radius_envelope_m"])
    site = clearing["trunk_sites"][0]["site_m"]
    require(trunk["geometry"]["radius_m"] == R_TRUNK_M, "f07_r_trunk_frozen",
            trunk["geometry"]["radius_m"])
    require(trunk["site"]["base_centre_m"] == site, "f07_site_identity",
            (trunk["site"]["base_centre_m"], site))

    inputs_out = {}
    for key in ("clearing", "terrain", "trunk"):
        pin = INPUTS[key]
        entry = {"path": pin["path"], "schema": pin["schema"],
                 "file_sha256": pin["file_sha256"]}
        if key == "terrain":
            entry["bundle_sha256"] = pin["bundle_sha256"]
        else:
            entry["declaration_sha256"] = pin["declaration_sha256"]
        inputs_out[key] = entry

    v_max = V_MAX_M_S
    declaration = {
        "schema": SCHEMA,
        "name": NAME,
        "inputs": inputs_out,
        "walker_envelope": {
            "r_body_m": R_BODY_ENVELOPE_M,
            "r_body_source": "clearing.spawn.body_radius_envelope_m (F01, live)",
            "stance_floor_m": _grid6(STANCE_FLOOR_M),
            "corridor_envelope_m": _grid6(W_ENV_M),
            "corridor_min_clearance_m": _grid6(CORRIDOR_MIN_CLEARANCE_M),
            "derivation": "stance floor = 2*r_body (the envelope fits); corridor "
                          "envelope W_env = 4*r_body = 1.0 m -- F01's own frozen "
                          "passing-room quantum (R_clear = r_trunk_bound + 4*r_body), "
                          "reused, not re-chosen; min clearance = W_env/2 = 0.5 m",
            "pinned": {"stride_m": STRIDE_M_PINNED, "v_max_m_s": v_max,
                       "dt_max_s": _grid6(DT_MAX_S),
                       "s_tick_m": _grid6(v_max / 300.0),
                       "sole_radius_m": SOLE_RADIUS_M, "k_touch": K_TOUCH,
                       "trunk_radius_m": R_TRUNK_M},
            "citations": list(WALKER_CITATIONS),
        },
        "blocking_causes": blocking_causes_table(trunk),
        "routes": build_routes(clearing),
        "route_grid": {"step_m": GRID_STEP_M, "x0_m": -EXTENT_HALF_WIDTH_M,
                       "z0_m": -EXTENT_HALF_WIDTH_M, "nx": GRID_N, "nz": GRID_N,
                       "connectivity": CONNECTIVITY, "row": "z", "col": "x",
                       "snap_decimals": GRID_DECIMALS,
                       "note": "Delta = r_body/5 = 0.05 m: the stance radius spans 5 "
                               "cells, the envelope width 20; per-tick travel s_tick "
                               "= 3.366667e-3 m is ~15x finer -- steering corrections "
                               "happen inside one route cell (no pathfinding)"},
        "bounds": {"max_slope_m_per_m": MAX_SLOPE_M_PER_M,
                   "corridor_min_clearance_m": _grid6(CORRIDOR_MIN_CLEARANCE_M),
                   "corridor_min_width_m": _grid6(W_ENV_M),
                   "approach_zone_r_m": _grid6(APPROACH_ZONE_R_M),
                   "contact_band_m": _grid6(CONTACT_BAND_M),
                   "edge_ray_max_stop_short_m": _grid6(EDGE_RAY_MAX_STOP_SHORT_M)},
        "scope": "Route/blocking layer for map item F07 (C14; C23 noted). Consumed "
                 "by F08 (repeatable loading re-compiles/re-validates these same "
                 "declarations), W10 (walking acceptance in this scene), F05 (the "
                 "terrain envelope spec feeds from the same slope data).",
    }
    declaration["route_declaration_sha256"] = digest(declaration)
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
            require(key not in out, "f07_duplicate_json_key", key)
            out[key] = value
        return out

    def no_const(value):
        raise Refusal("f07_nonfinite_json", value)

    try:
        return json.loads(raw, object_pairs_hook=unique, parse_constant=no_const)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise Refusal("f07_invalid_json", exc)


def load_declaration(path):
    with open(path, "rb") as handle:
        return loads(handle.read())


# --- validation (every check re-derived from stored numbers) -------------------
def _finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) \
        and math.isfinite(value)


def _seg_point_dist(ax, az, bx, bz, px, pz):
    """Distance from (px, pz) to segment [A, B] (exact, no search)."""
    abx, abz = bx - ax, bz - az
    denom = abx * abx + abz * abz
    if denom == 0.0:
        return math.hypot(px - ax, pz - az)
    t = ((px - ax) * abx + (pz - az) * abz) / denom
    t = max(0.0, min(1.0, t))
    return math.hypot(px - (ax + t * abx), pz - (az + t * abz))


def validate_declaration(declaration):
    """Full validation; raises Refusal on any violation. Returns a receipt."""
    require(isinstance(declaration, dict), "f07_declaration_object")
    require(declaration.get("schema") == SCHEMA, "f07_schema", declaration.get("schema"))
    require(declaration.get("name") == NAME, "f07_name", declaration.get("name"))
    pinned = declaration.get("route_declaration_sha256")
    body = {k: v for k, v in declaration.items() if k != "route_declaration_sha256"}
    require(isinstance(pinned, str) and len(pinned) == 64, "f07_digest_form", pinned)
    require(sha(canonical(body)) == pinned, "f07_digest_mismatch")

    # -- inputs: pinned digests identical to this module's frozen pins ----------
    inputs = declaration.get("inputs")
    require(isinstance(inputs, dict) and set(inputs) == set(INPUTS), "f07_inputs")
    for key, pin in INPUTS.items():
        got = inputs.get(key)
        require(isinstance(got, dict), "f07_input_object", key)
        require(got.get("path") == pin["path"]
                and got.get("schema") == pin["schema"]
                and got.get("file_sha256") == pin["file_sha256"],
                "f07_input_pin", key)
        if key == "terrain":
            require(got.get("bundle_sha256") == pin["bundle_sha256"],
                    "f07_input_pin", key)
        else:
            require(got.get("declaration_sha256") == pin["declaration_sha256"],
                    "f07_input_pin", key)

    # -- walker envelope: the derivation re-closes from stored numbers ---------
    env = declaration.get("walker_envelope")
    require(isinstance(env, dict), "f07_envelope_object")
    require(env.get("r_body_m") == R_BODY_ENVELOPE_M, "f07_r_body_frozen",
            env.get("r_body_m"))
    require(env.get("stance_floor_m") == _grid6(2.0 * R_BODY_ENVELOPE_M),
            "f07_stance_floor")
    require(env.get("corridor_envelope_m") == _grid6(4.0 * R_BODY_ENVELOPE_M),
            "f07_w_env")
    require(env.get("corridor_min_clearance_m")
            == _grid6(2.0 * R_BODY_ENVELOPE_M), "f07_min_clearance")
    pinned_nums = env.get("pinned")
    require(isinstance(pinned_nums, dict), "f07_pinned_object")
    require(pinned_nums.get("stride_m") == STRIDE_M_PINNED
            and pinned_nums.get("v_max_m_s") == V_MAX_M_S
            and pinned_nums.get("dt_max_s") == _grid6(1.0 / 300.0)
            and pinned_nums.get("s_tick_m") == _grid6(V_MAX_M_S / 300.0)
            and pinned_nums.get("sole_radius_m") == SOLE_RADIUS_M
            and pinned_nums.get("k_touch") == K_TOUCH,
            "f07_pinned_numbers", pinned_nums)
    require(pinned_nums.get("s_tick_m") < GRID_STEP_M / 10.0,
            "f07_s_tick_vs_grid")          # steering inside one cell: 15x margin
    require(isinstance(env.get("citations"), list) and len(env["citations"]) >= 5,
            "f07_citations")

    # -- blocking causes: the frozen two-YES/two-NO table, zero unexplained ----
    causes = declaration.get("blocking_causes")
    require(isinstance(causes, dict), "f07_causes_object")
    blockers = causes.get("blockers")
    require(isinstance(blockers, list) and len(blockers) == 2, "f07_blocker_rows")
    b1, b2 = blockers
    require(b1.get("id") == "B1" and b1.get("kind") == "extent_rule"
            and b1.get("blocks") is True
            and b1.get("half_width_m") == EXTENT_HALF_WIDTH_M
            and b1.get("strict_gt") is True, "f07_b1_row", b1)
    require(b1.get("visible", {}).get("posts") == 80
            and b1.get("visible", {}).get("ring_extent_m") == EXTENT_HALF_WIDTH_M,
            "f07_b1_visible")
    require(b2.get("id") == "B2" and b2.get("kind") == "trunk_solid"
            and b2.get("blocks") is True, "f07_b2_row", b2)
    require(b2.get("r_trunk_m") == R_TRUNK_M
            and b2.get("r_block_m") == _grid6(R_BLOCK_M), "f07_b2_radius")
    require(_finite(b2["site_m"][0]) and _finite(b2["site_m"][1]), "f07_b2_site")
    require(abs(b2["r_block_m"] - (b2["r_trunk_m"] + R_BODY_ENVELOPE_M)) <= 1e-9,
            "f07_b2_derivation")
    non_blockers = causes.get("non_blockers")
    require(isinstance(non_blockers, list) and len(non_blockers) == 2,
            "f07_non_blocker_rows")
    n1, n2 = non_blockers
    require(n1.get("id") == "N1" and n1.get("blocks") is False
            and n1.get("law_m_per_m") == MAX_SLOPE_M_PER_M, "f07_n1_row", n1)
    require(n2.get("id") == "N2" and n2.get("blocks") is False
            and n2.get("status") == "render_only_no_claim", "f07_n2_row", n2)
    require(causes.get("unexplained") == [], "f07_unexplained_must_be_empty")

    # -- routes: constructions re-derived from stored numbers ------------------
    routes = declaration.get("routes")
    require(isinstance(routes, dict), "f07_routes_object")
    spawn = routes.get("spawn_m")
    require(isinstance(spawn, list) and len(spawn) == 3
            and spawn[0] == 0.0 and spawn[2] == 0.0, "f07_spawn", spawn)
    axis = routes.get("trunk_axis_m")
    require(isinstance(axis, list) and len(axis) == 2, "f07_axis", axis)
    straight = routes.get("straight")
    require(isinstance(straight, dict) and straight.get("id") == "R0",
            "f07_r0")
    require(straight.get("from_m") == [0.0, 0.0]
            and straight.get("to_m") == [axis[0], axis[1]], "f07_r0_endpoints")
    length = math.hypot(axis[0], axis[1])
    require(abs(straight.get("length_m") - _grid6(length)) <= 1e-9, "f07_r0_length")
    require(straight.get("contact_dist_from_axis_m") == _grid6(R_BLOCK_M),
            "f07_r0_contact")
    tangents = routes.get("tangents")
    require(isinstance(tangents, list) and len(tangents) == 10, "f07_tangent_count")
    seen = set()
    for t in tangents:
        require(isinstance(t, dict), "f07_tangent_object")
        ident = (t.get("mound_index"), t.get("side"))
        require(ident not in seen, "f07_tangent_duplicate", ident)
        seen.add(ident)
        require(t.get("id") == "R%d%s" % (ident[0] + 1, ident[1]), "f07_tangent_id")
        rho = t.get("mound_envelope_m")
        require(rho == _grid6(t.get("mound_radius_m") + R_BODY_ENVELOPE_M),
                "f07_tangent_rho", t.get("id"))
        ux, uz = t.get("dir_m", [0.0, 0.0])
        require(abs(math.hypot(ux, uz) - 1.0) <= 2e-6, "f07_tangent_unit", t.get("id"))
        # re-derive the tangent construction from stored numbers
        sxp, szp = spawn[0], spawn[2]
        cxp, czp = t.get("mound_centre_m", [9e9, 9e9])
        dxp, dzp = cxp - sxp, czp - szp
        d = math.hypot(dxp, dzp)
        alpha = math.asin(_grid6(rho) / d)
        sign = 1.0 if ident[1] == "L" else -1.0
        theta = math.atan2(dzp, dxp) + sign * alpha
        require(abs(ux - math.cos(theta)) <= 2e-6
                and abs(uz - math.sin(theta)) <= 2e-6,
                "f07_tangent_dir", t.get("id"))
        t_pass = dxp * ux + dzp * uz
        radius_t = t.get("mound_radius_m")
        half_chord = math.sqrt(R_BODY_ENVELOPE_M
                               * (2.0 * radius_t + 3.0 * R_BODY_ENVELOPE_M))
        t_exit = t_pass + half_chord
        wall_times = []
        if ux > 0.0:
            wall_times.append((EXTENT_HALF_WIDTH_M - sxp) / ux)
        elif ux < 0.0:
            wall_times.append((-EXTENT_HALF_WIDTH_M - sxp) / ux)
        if uz > 0.0:
            wall_times.append((EXTENT_HALF_WIDTH_M - szp) / uz)
        elif uz < 0.0:
            wall_times.append((-EXTENT_HALF_WIDTH_M - szp) / uz)
        t_extent = min(w for w in wall_times if w > 0.0)
        t_end = t.get("t_end_m")
        require(abs(t_end - _grid6(min(t_exit, t_extent))) <= 2e-6,
                "f07_t_end", t.get("id"))
        expected_cause = "extent_edge" if t_extent <= t_exit else "passed_mound"
        require(t.get("end_cause") == expected_cause,
                "f07_end_cause", (t.get("id"), t.get("end_cause"), expected_cause))
        if expected_cause == "passed_mound":
            require(t_end >= t_pass - 2e-6, "f07_centre_plane_passed",
                    t.get("id"))
        require(abs(t.get("to_m")[0] - _grid6(sxp + ux * t_end)) <= 2e-6
                and abs(t.get("to_m")[1] - _grid6(szp + uz * t_end)) <= 2e-6,
                "f07_tangent_to", t.get("id"))
        # the construction's own invariant: closest approach == the envelope disk
        closest = _seg_point_dist(sxp, szp, t["to_m"][0], t["to_m"][1], cxp, czp)
        require(closest + TANGENT_ROUND_TOL_M >= rho,
                "f07_tangent_closest", (t.get("id"), closest, rho))
        require(abs(t.get("closest_approach_m") - rho) <= 1e-9,
                "f07_tangent_closest_field", t.get("id"))
        require(t.get("pass_beyond_m") == _grid6(half_chord),
                "f07_pass_beyond", t.get("id"))
        # the tangent route must clear the trunk blocker entirely (it is a
        # detour around a mound, never a trunk approach)
        require(_seg_point_dist(sxp, szp, t["to_m"][0], t["to_m"][1],
                                axis[0], axis[1])
                >= APPROACH_ZONE_R_M, "f07_tangent_trunk_clear", t.get("id"))

    # -- grid + bounds frozen ----------------------------------------------------
    grid = declaration.get("route_grid")
    require(isinstance(grid, dict), "f07_grid_object")
    require(grid.get("step_m") == GRID_STEP_M and grid.get("nx") == GRID_N
            and grid.get("nz") == GRID_N and grid.get("connectivity") == CONNECTIVITY
            and grid.get("row") == "z" and grid.get("col") == "x"
            and grid.get("x0_m") == -EXTENT_HALF_WIDTH_M
            and grid.get("z0_m") == -EXTENT_HALF_WIDTH_M
            and grid.get("snap_decimals") == GRID_DECIMALS, "f07_grid_frozen", grid)
    bounds = declaration.get("bounds")
    require(isinstance(bounds, dict), "f07_bounds_object")
    require(bounds.get("max_slope_m_per_m") == MAX_SLOPE_M_PER_M
            and bounds.get("corridor_min_clearance_m") == _grid6(CORRIDOR_MIN_CLEARANCE_M)
            and bounds.get("corridor_min_width_m") == _grid6(W_ENV_M)
            and bounds.get("approach_zone_r_m") == _grid6(APPROACH_ZONE_R_M)
            and bounds.get("contact_band_m") == _grid6(CONTACT_BAND_M)
            and bounds.get("edge_ray_max_stop_short_m") == _grid6(EDGE_RAY_MAX_STOP_SHORT_M),
            "f07_bounds_frozen", bounds)

    return {"schema": SCHEMA, "route_declaration_sha256": pinned,
            "blockers": 2, "non_blockers": 2, "unexplained": 0,
            "tangent_routes": len(tangents), "grid_cells": GRID_N * GRID_N,
            "validated": True}


def selftest():
    return validate_declaration(compile_declaration())


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    default = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "route_declaration.json")
    if not argv or argv[0] == "compile":
        path = argv[1] if len(argv) > 1 else default
        declaration = compile_declaration()
        raw = write_declaration(declaration, path)
        print(json.dumps({"declaration": path, "bytes": len(raw),
                          "route_declaration_sha256":
                              declaration["route_declaration_sha256"]}))
        return 0
    if argv[0] == "validate":
        path = argv[1] if len(argv) > 1 else default
        receipt = validate_declaration(load_declaration(path))
        print(json.dumps(receipt, sort_keys=True))
        return 0
    if argv[0] == "selftest":
        print(json.dumps(selftest(), sort_keys=True))
        return 0
    raise Refusal("f07_cli_verb", argv)


if __name__ == "__main__":
    sys.exit(main())
