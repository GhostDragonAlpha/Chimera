"""terrain_bundle -- M-F02: the clearing's terrain as ONE render+collision declaration.

Schema ``chimera.monkey_terrain.v1``. Follows the house compiled-scene pattern
(tools/science_funnel/common.py, earth_scene.py::compile_scene): canonical JSON bytes, a
self-pinned sha256 over those bytes, strict ``require``/``Refusal`` intake, SI metres.

THE LAW THIS BUNDLE EXISTS FOR (map item F02, C14): "Rendered ground and physical query
surfaces agree within frozen geometric tolerance." The mechanism is the lineage's own
(graph_earth.hpp:102-105 renders the ground from the SAME slope the physics plane uses;
walker.py:556-563 renders grains AT heights_at()): one surface, two projections. Here the
surface is the TRIANGULATION of F01's stored 41x41 grid -- triangle planes are the
collision representation (terrain_query.py), and ``render.vertices``/``render.indices``
are verbatim the engine's ``Engine::load_mesh`` arrays (engine.hpp:140, main.cpp:764,
9 floats = position(3) + normal(3) + color(3), uint32 indices).

Normals are FLAT per-triangle face normals on fully duplicated vertices, computed with the
engine's own formula ``normalize(cross(b-a, c-a))`` (graph_earth.hpp:100). This is not a
style choice: the engine's normal-hygiene gate (engine.cpp:1854-1937) silently re-derives
any stored normal that is non-unit or points opposite its faces' winding sum, so a mesh
with shared/smooth normals would be rewritten at upload and render != query by the
engine's own correction. Duplicated face normals pass the gate untouched.

Gentleness/discretization: the surface is piecewise linear on the 1 m grid; its deviation
from F01's analytic mounds is bounded by 2*(1/8)*A_max*pi^2/(2*R_min^2) =
(0.12*pi^2/(2*16))/4*2 = 0.00925 m <= DISCRETIZATION_BOUND_M (frozen, see
agents/F02_terrain/PREREGISTRATION.md). That deviation is carried IDENTICALLY by the
render and the collision projection -- it is grid resolution, not disagreement.

Frozen prereg: agents/F02_terrain/PREREGISTRATION.md. Source of geometry: F01's committed
``clearing_declaration.json`` (pinned by file sha256 AND its own body pin) -- nothing here
re-derives mound placement or post positions.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

SCHEMA = "chimera.monkey_terrain.v1"
NAME = "monkey_clearing_terrain"

# --- frozen construction (PREREGISTRATION.md; do not tune) ---------------------
GROUND_CHECKER_RGB = [[0.16, 0.22, 0.17], [0.18, 0.24, 0.19]]   # graph_earth.hpp:105
POST_SIDES = 6                       # hexagonal prism (render row, THE HUMAN's to move)
POST_RADIUS_M = 0.05                 # circumscribed radius; render-legibility constant
POST_TOP_CAP = True
POST_BOTTOM_CAP = False              # open bottom: occluded by ground contact (declared)
DEGENERATE_EPS = 1e-16               # engine mirror: graph_earth.hpp earth_render_degenerate
DISCRETIZATION_BOUND_M = 0.01        # derived bound 0.00925 (prereg); measured in tests
GROUND_TRI_PER_CELL = 2
POST_TRI_PER_POST = POST_SIDES * 2 + (POST_SIDES if POST_TOP_CAP else 0)   # 18

_CITATIONS = {
    "upload": ["ChimeraEngine/engine/engine.hpp:140-141 load_mesh(verts,indices,vcount,icount)",
               "ChimeraEngine/engine/main.cpp:764 earth_mesh_upload_failed -> load_mesh",
               "ChimeraEngine/engine/graph_earth.hpp:47-48 mesh.bin twin layout"],
    "normal": ["ChimeraEngine/engine/graph_earth.hpp:100 n=cross(sub(b,a),sub(c,a)) normalized",
               "ChimeraEngine/engine/engine.cpp:1854-1937 normal-hygiene gate (must not fire)"],
    "ground_style": ["ChimeraEngine/engine/graph_earth.hpp:105 two-tone checker"],
    "boundary": ["ChimeraEngine/engine/earth_environment.hpp:118 out_of_patch |x|>half || |z|>half"],
}


def _load_sibling(name):
    """Import a sibling module (clearing_recipe) from the repo root, or by path."""
    full = "tools.monkey_campaign.data.monkey_clearing." + name
    try:
        return __import__(full, fromlist=[name])
    except ImportError:
        path = Path(__file__).resolve().with_name(name + ".py")
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


recipe = _load_sibling("clearing_recipe")

EXPECTED_POSTS = int(round(8.0 * recipe.EXTENT_HALF_WIDTH_M / recipe.POST_SPACING_M))  # 160 m / 2.0 m = 80


class Refusal(ValueError):
    """Strict intake refusal, house style (tools/science_funnel/common.py)."""

    def __init__(self, code, detail=""):
        self.code, self.detail = code, str(detail)
        super().__init__(code + (": " + self.detail if detail else ""))


def require(condition, code, detail=""):
    if not condition:
        raise Refusal(code, detail)


canonical = recipe.canonical
sha = recipe.sha
digest = recipe.digest
loads_raw = recipe.loads


def loads(raw):
    """Strict JSON intake (duplicate keys / non-finite refused) + schema check."""
    value = loads_raw(raw)
    require(isinstance(value, dict) and value.get("schema") == SCHEMA,
            "f02_schema", isinstance(value, dict) and value.get("schema"))
    return value


# --- geometry helpers (engine arithmetic, float64) ------------------------------
def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _norm(a):
    return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


def face_normal(pa, pb, pc):
    """The engine's triangle normal: normalize(cross(b-a, c-a)), graph_earth.hpp:100."""
    n = _cross(_sub(pb, pa), _sub(pc, pa))
    length = _norm(n)
    require(length > DEGENERATE_EPS, "f02_degenerate_triangle", (pa, pb, pc))
    return (n[0] / length, n[1] / length, n[2] / length)


# --- compile ---------------------------------------------------------------------
def _ground_cells(grid):
    nx, nz = grid["nx"], grid["nz"]
    for iz in range(nz - 1):
        for ix in range(nx - 1):
            yield ix, iz


def _node(grid, ix, iz):
    return (grid["x0_m"] + ix * grid["dx_m"], grid["heights_m"][iz][ix],
            grid["z0_m"] + iz * grid["dz_m"])


def _add_triangle(mesh, pa, pb, pc, color):
    """Flat-shaded triangle: three duplicated vertices carrying the face normal."""
    normal = face_normal(pa, pb, pc)
    start = len(mesh["vertices"]) // 9
    for p in (pa, pb, pc):
        mesh["vertices"].extend([p[0], p[1], p[2], normal[0], normal[1], normal[2],
                                 color[0], color[1], color[2]])
    mesh["indices"].extend([start, start + 1, start + 2])


def _build_ground(grid):
    """40x40 cells -> 3200 flat-shaded triangles; diagonal (00)-(11), +Y winding.

    Triangle A (node00, node01, node11) covers tz >= tx; triangle B
    (node00, node11, node10) covers tz < tx; terrain_query.py uses the SAME rule on
    the SAME arrays, which is the render/query identity falsifier (a) guards.
    """
    mesh = {"vertices": [], "indices": []}
    for ix, iz in _ground_cells(grid):
        n00, n10 = _node(grid, ix, iz), _node(grid, ix + 1, iz)
        n01, n11 = _node(grid, ix, iz + 1), _node(grid, ix + 1, iz + 1)
        color = GROUND_CHECKER_RGB[(ix + iz) % 2]
        _add_triangle(mesh, n00, n01, n11, color)      # A: tz >= tx
        _add_triangle(mesh, n00, n11, n10, color)      # B: tz <  tx
    return mesh


def _build_post(px, py, pz, colour):
    """One hexagonal prism: POST_SIDES*2 side triangles + flat top cap, +Y/outward."""
    mesh = {"vertices": [], "indices": []}
    top_y = py + recipe.POST_HEIGHT_M
    angles = [2.0 * math.pi * k / POST_SIDES for k in range(POST_SIDES)]
    ring_b = [(px + POST_RADIUS_M * math.cos(t), py, pz + POST_RADIUS_M * math.sin(t))
              for t in angles]
    ring_t = [(px + POST_RADIUS_M * math.cos(t), top_y, pz + POST_RADIUS_M * math.sin(t))
              for t in angles]

    def radial_out(mid_angle):
        return (math.cos(mid_angle), 0.0, math.sin(mid_angle))

    for k in range(POST_SIDES):
        k1 = (k + 1) % POST_SIDES
        mid = 2.0 * math.pi * (k + 0.5) / POST_SIDES
        before = len(mesh["indices"])
        _add_triangle(mesh, ring_b[k], ring_t[k1], ring_b[k1], colour)   # outward (prereg)
        _add_triangle(mesh, ring_b[k], ring_t[k], ring_t[k1], colour)
        for tri in range(before, len(mesh["indices"]), 3):
            ia, ib, ic = mesh["indices"][tri:tri + 3]
            get = lambda i: tuple(mesh["vertices"][9 * i:9 * i + 3])
            n = face_normal(get(ia), get(ib), get(ic))
            require(n[0] * radial_out(mid)[0] + n[2] * radial_out(mid)[2] > 0.0,
                    "f02_post_side_inward", (px, pz, k))
    if POST_TOP_CAP:
        centre = (px, top_y, pz)
        for k in range(POST_SIDES):
            k1 = (k + 1) % POST_SIDES
            before = len(mesh["indices"])
            _add_triangle(mesh, centre, ring_t[k1], ring_t[k], colour)   # +Y (prereg)
            for tri in range(before, len(mesh["indices"]), 3):
                ia = mesh["indices"][tri]
                n = tuple(mesh["vertices"][9 * ia + 3:9 * ia + 6])
                require(n[1] > 0.999, "f02_post_cap_not_up", (px, pz, k))
    return mesh


def compile_bundle(declaration_path):
    """Compile the terrain bundle from F01's committed declaration (pinned source).

    RNG-free: same declaration file -> byte-identical bundle, anywhere (falsifier-free
    determinism by construction, tested in-process x2 + subprocess).
    """
    path = Path(declaration_path)
    raw = path.read_bytes()
    declaration = recipe.loads(raw)
    recipe.validate_declaration(declaration)          # refuse a drifted source outright
    grid = declaration["terrain"]["grid"]
    mounds = declaration["terrain"]["recipe"]["mounds"]
    rendered = declaration["boundary"]["rendered"]
    posts = rendered["posts_m"]
    colour = rendered["colour_rgb"]

    ground = _build_ground(grid)
    ground_vertex_count = len(ground["vertices"]) // 9
    ground_index_count = len(ground["indices"])
    post_meshes = [_build_post(p[0], p[1], p[2], colour) for p in posts]
    vertices = list(ground["vertices"])
    indices = list(ground["indices"])
    for pm in post_meshes:
        offset = len(vertices) // 9
        vertices.extend(pm["vertices"])
        indices.extend(offset + i for i in pm["indices"])
    post_vertex_count = len(vertices) // 9 - ground_vertex_count
    post_index_count = len(indices) - ground_index_count

    bundle = {
        "schema": SCHEMA,
        "name": NAME,
        "derived_from": "F01 clearing declaration (chimera.monkey_clearing.v1); the "
                        "triangulation of its stored 41x41 grid IS both the render mesh "
                        "and the physical query surface (map item F02, contract C14).",
        "source": {
            "declaration_schema": recipe.SCHEMA,
            "declaration_relative_path":
                "tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json",
            "declaration_file_sha256": sha(raw),
            "declaration_sha256": declaration["declaration_sha256"],
            "recipe_seed": declaration["seed"],
        },
        "coordinate_convention": dict(declaration["coordinate_convention"]),
        "terrain_surface": {
            "kind": "triangulated_height_grid",
            "surface_id": "monkey_clearing_ground",
            "grid": {k: grid[k] for k in
                     ("x0_m", "z0_m", "dx_m", "dz_m", "nx", "nz", "heights_m")},
            "mounds": [dict(m) for m in mounds],
            "base_height_m": declaration["terrain"]["base_height_m"],
            "max_slope_bound_m_per_m": declaration["terrain"]["max_slope_bound"],
            "diagonal_rule": "cell (ix,iz) splits along node(ix,iz)-node(ix+1,iz+1); "
                             "triangle A=(00,01,11) covers tz>=tx, triangle B=(00,11,10) "
                             "covers tz<tx (tz = z-z_j, tx = x-x_i in metres)",
            "discretization_bound_m": DISCRETIZATION_BOUND_M,
            "discretization_derivation": "2*(1/8)*A_max*pi^2/(2*R_min^2) with A_max=0.12, "
                                         "R_min=4.0, dx=dz=1 -> 0.00925 m; carried "
                                         "identically by render and collision projections",
        },
        "render": {
            "mesh_layout": {"floats_per_vertex": 9,
                            "fields": ["position_m", "normal", "color_rgb"],
                            "index_type": "uint32",
                            "upload": "engine.load_mesh(vertices, indices, "
                                      "len(vertices)//9, len(indices))",
                            "citations": _CITATIONS["upload"]},
            "vertices": vertices,
            "indices": indices,
            "vertex_count": len(vertices) // 9,
            "index_count": len(indices),
            "triangle_count": len(indices) // 3,
            "sections": {
                "ground": {"vertex_start": 0, "vertex_count": ground_vertex_count,
                           "index_start": 0, "index_count": ground_index_count,
                           "surface_id": "monkey_clearing_ground"},
                "boundary_posts": {"vertex_start": ground_vertex_count,
                                   "vertex_count": post_vertex_count,
                                   "index_start": ground_index_count,
                                   "index_count": post_index_count,
                                   "surface_id": "monkey_clearing_boundary_posts"},
            },
            "style": {"ground_checker_rgb": GROUND_CHECKER_RGB,
                      "ground_checker_citation": _CITATIONS["ground_style"][0],
                      "post_sides": POST_SIDES, "post_radius_m": POST_RADIUS_M,
                      "post_top_cap": POST_TOP_CAP, "post_bottom_cap": POST_BOTTOM_CAP,
                      "post_colour_rgb": list(colour),
                      "post_height_m": recipe.POST_HEIGHT_M,
                      "normal_rule": "normalized cross(b-a, c-a) per triangle, duplicated "
                                     "flat-shaded vertices (hygiene gate passes untouched)",
                      "normal_rule_citations": _CITATIONS["normal"]},
        },
        "collision": {
            "kind": "triangle_surface",
            "same_arrays_as_render": True,
            "surface_id": "monkey_clearing_ground",
            "height_rule": "containing triangle's plane (exact, piecewise linear)",
            "gradient_rule": "plane gradient of the containing triangle; stored normal = "
                             "normalize(-gx, 1, -gz)",
            "normal_rule": "normalized cross(b-a, c-a) of the containing triangle on the "
                           "stored render positions (graph_earth.hpp:100)",
            "boundary": {"kind": "extent_rule", "half_width_m": recipe.EXTENT_HALF_WIDTH_M,
                         "rule": "outside means |x| > half_width_m or |z| > half_width_m "
                                 "(strict >)",
                         "citations": _CITATIONS["boundary"]},
            "query_outside_refusal": "f02_outside_extent",
        },
    }
    bundle["bundle_sha256"] = digest(bundle)          # over the bytes without the pin
    return bundle


def write_bundle(bundle, path):
    raw = canonical(bundle)
    with open(path, "wb") as handle:
        handle.write(raw)
    return raw


# --- validation (every check re-derived from stored numbers) ---------------------
def _finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) \
        and math.isfinite(value)


def validate_bundle(bundle):
    """Full structural + geometric validation; raises Refusal. Returns a receipt.

    Mirrors the engine's own upload gates: mesh length/finite/index checks
    (graph_earth.hpp:47-48, engine.cpp:1837-1841), the degenerate-triangle refusal
    (graph_earth.hpp:100) and the normal-hygiene gate (engine.cpp:1854-1937), plus the
    render/query identity data (grid == mounds, posts on the edge, boundary rule).
    """
    require(isinstance(bundle, dict) and bundle.get("schema") == SCHEMA,
            "f02_schema", bundle.get("schema") if isinstance(bundle, dict) else None)
    require(bundle.get("name") == NAME, "f02_name", bundle.get("name"))
    pinned = bundle.get("bundle_sha256")
    body = {k: v for k, v in bundle.items() if k != "bundle_sha256"}
    require(isinstance(pinned, str) and len(pinned) == 64, "f02_digest_form", pinned)
    require(sha(canonical(body)) == pinned, "f02_digest_mismatch")

    # -- source pins present ---------------------------------------------------
    source = bundle.get("source")
    require(isinstance(source, dict), "f02_source_object")
    require(source.get("declaration_schema") == recipe.SCHEMA, "f02_source_schema")
    for key in ("declaration_relative_path", "declaration_file_sha256",
                "declaration_sha256", "recipe_seed"):
        require(key in source, "f02_source_field", key)

    # -- convention + surface data ---------------------------------------------
    conv = bundle.get("coordinate_convention")
    require(isinstance(conv, dict) and conv.get("units") == "m"
            and conv.get("up_axis") == "+y" and conv.get("handedness") == "right",
            "f02_convention_frozen", conv)
    surface = bundle.get("terrain_surface")
    require(isinstance(surface, dict) and surface.get("kind") == "triangulated_height_grid",
            "f02_surface_kind", surface and surface.get("kind"))
    require(surface.get("surface_id") == "monkey_clearing_ground", "f02_surface_id")
    grid = surface.get("grid")
    require(isinstance(grid, dict) and grid.get("nx") == recipe.GRID_N
            and grid.get("nz") == recipe.GRID_N and grid.get("dx_m") == recipe.GRID_STEP_M
            and grid.get("dz_m") == recipe.GRID_STEP_M
            and grid.get("x0_m") == -recipe.EXTENT_HALF_WIDTH_M
            and grid.get("z0_m") == -recipe.EXTENT_HALF_WIDTH_M, "f02_grid_frame")
    mounds = surface.get("mounds")
    require(isinstance(mounds, list) and len(mounds) == recipe.MOUND_COUNT,
            "f02_mound_count")
    heights = grid.get("heights_m")
    require(isinstance(heights, list) and len(heights) == recipe.GRID_N, "f02_grid_rows")
    worst_grid_err = 0.0
    for iz, row in enumerate(heights):
        require(isinstance(row, list) and len(row) == recipe.GRID_N, "f02_grid_cols", iz)
        z = grid["z0_m"] + iz * grid["dz_m"]
        for ix, value in enumerate(row):
            require(_finite(value), "f02_grid_value", (iz, ix))
            x = grid["x0_m"] + ix * grid["dx_m"]
            worst_grid_err = max(worst_grid_err, abs(value - recipe.height_at(mounds, x, z)))
    require(worst_grid_err <= 1e-9, "f02_grid_mound_mismatch", worst_grid_err)
    require(surface.get("max_slope_bound_m_per_m") == recipe.MAX_SLOPE_BOUND,
            "f02_slope_bound")
    require(surface.get("discretization_bound_m") == DISCRETIZATION_BOUND_M,
            "f02_discretization_bound")

    # -- render mesh: engine upload gates --------------------------------------
    render = bundle.get("render")
    require(isinstance(render, dict), "f02_render_object")
    layout = render.get("mesh_layout")
    require(isinstance(layout, dict) and layout.get("floats_per_vertex") == 9
            and layout.get("index_type") == "uint32", "f02_mesh_layout", layout)
    vertices, indices = render.get("vertices"), render.get("indices")
    require(isinstance(vertices, list) and isinstance(indices, list), "f02_mesh_arrays")
    nv = len(vertices) // 9
    require(len(vertices) % 9 == 0 and nv > 0, "f02_mesh_length", len(vertices))
    require(len(indices) % 3 == 0 and len(indices) > 0, "f02_index_length", len(indices))
    require(render.get("vertex_count") == nv and render.get("index_count") == len(indices)
            and render.get("triangle_count") == len(indices) // 3, "f02_mesh_counts")
    for v in vertices:
        require(_finite(v), "f02_mesh_nonfinite", v)
    for i in indices:
        require(isinstance(i, int) and not isinstance(i, bool) and 0 <= i < nv,
                "f02_mesh_index", i)

    # sections contiguous and covering, counts derived from the frozen grid/posts
    sections = render.get("sections")
    require(isinstance(sections, dict) and set(sections) == {"ground", "boundary_posts"},
            "f02_sections", sections and set(sections))
    expected_ground_tris = (recipe.GRID_N - 1) * (recipe.GRID_N - 1) * GROUND_TRI_PER_CELL
    expected_post_tris = EXPECTED_POSTS * POST_TRI_PER_POST
    ground, postsec = sections["ground"], sections["boundary_posts"]
    require(ground.get("vertex_start") == 0 and ground.get("index_start") == 0,
            "f02_ground_section_origin")
    require(ground.get("index_count") == 3 * expected_ground_tris
            and ground.get("vertex_count") == 3 * expected_ground_tris,
            "f02_ground_section_counts", ground)
    require(postsec.get("vertex_start") == ground.get("vertex_count")
            and postsec.get("index_start") == ground.get("index_count"),
            "f02_post_section_contiguous")
    require(postsec.get("index_count") == 3 * expected_post_tris
            and postsec.get("vertex_count") == 3 * expected_post_tris,
            "f02_post_section_counts", postsec)
    require(postsec.get("vertex_start") + postsec.get("vertex_count") == nv
            and postsec.get("index_start") + postsec.get("index_count") == len(indices),
            "f02_sections_cover")

    # -- per-triangle: degenerate refusal, stored normal identity, winding -----
    ground_index_count = ground["index_count"]
    worst_normal_err = 0.0
    broken_normals = 0
    deviant_normals = 0
    min_cross_len = float("inf")
    for t in range(0, len(indices), 3):
        ia, ib, ic = indices[t], indices[t + 1], indices[t + 2]
        get = lambda i: tuple(vertices[9 * i:9 * i + 3])
        pa, pb, pc = get(ia), get(ib), get(ic)
        cross = _cross(_sub(pb, pa), _sub(pc, pa))
        length = _norm(cross)
        min_cross_len = min(min_cross_len, length)
        require(length > DEGENERATE_EPS, "f02_degenerate_triangle", t // 3)
        normal = (cross[0] / length, cross[1] / length, cross[2] / length)
        if t < ground_index_count:
            require(normal[1] > 0.0, "f02_ground_normal_down", t // 3)
        for i in (ia, ib, ic):
            stored = tuple(vertices[9 * i + 3:9 * i + 6])
            # hygiene mirror part 1: unit length in the gate's acceptance band
            slen = _norm(stored)
            if not 0.5 <= slen <= 2.0:
                broken_normals += 1
            worst_normal_err = max(worst_normal_err,
                                   max(abs(stored[k] - normal[k]) for k in range(3)))
            # hygiene mirror part 2: no dot<0 against the vertex's face sum (exactly
            # one adjacent triangle per duplicated vertex)
            if stored[0] * cross[0] + stored[1] * cross[1] + stored[2] * cross[2] < 0.0:
                deviant_normals += 1
    require(worst_normal_err <= 1e-12, "f02_stored_normal_mismatch", worst_normal_err)
    require(broken_normals == 0, "f02_hygiene_broken", broken_normals)
    require(deviant_normals == 0, "f02_hygiene_deviant", deviant_normals)

    # -- the SURFACE stays inside the CLOSED physical extent (no fake ground past
    #    the blocking edge); post MARKER girth may straddle the edge by its radius,
    #    since F01's law puts the post CENTRES on the edge itself -----------------
    half = recipe.EXTENT_HALF_WIDTH_M
    worst_out = 0.0
    for i in range(ground["vertex_count"]):
        x, z = vertices[9 * i], vertices[9 * i + 2]
        worst_out = max(worst_out, abs(x) - half, abs(z) - half)
    require(worst_out <= 1e-9, "f02_ground_outside_extent", worst_out)
    worst_post_out = 0.0
    for i in range(ground["vertex_count"], nv):
        x, z = vertices[9 * i], vertices[9 * i + 2]
        worst_post_out = max(worst_post_out, abs(x) - half - POST_RADIUS_M,
                             abs(z) - half - POST_RADIUS_M)
    require(worst_post_out <= 1e-9, "f02_post_girth_out_of_bounds", worst_post_out)

    # -- posts: positions, edge coincidence, ground coincidence, style ----------
    collision = bundle.get("collision")
    require(isinstance(collision, dict) and collision.get("kind") == "triangle_surface"
            and collision.get("same_arrays_as_render") is True, "f02_collision_object")
    boundary = collision.get("boundary")
    require(isinstance(boundary, dict) and boundary.get("kind") == "extent_rule"
            and boundary.get("half_width_m") == half, "f02_boundary_physical")
    style = render.get("style")
    require(style.get("post_sides") == POST_SIDES and style.get("post_radius_m") == POST_RADIUS_M
            and style.get("post_top_cap") is True and style.get("post_bottom_cap") is False
            and style.get("post_height_m") == recipe.POST_HEIGHT_M,
            "f02_post_style_frozen", style)

    # recover per-post geometry from the mesh itself: post n occupies its own vertex
    # block; the prism axis is recovered as the midpoint of the ring's extremes
    # (the hexagon is symmetric about the axis), the base as min y, the top as max y.
    post_verts_per_post = 3 * POST_TRI_PER_POST
    base_err = 0.0
    for p in range(EXPECTED_POSTS):
        base = ground["vertex_count"] + p * post_verts_per_post
        xs = [vertices[9 * (base + v)] for v in range(post_verts_per_post)]
        ys = [vertices[9 * (base + v) + 1] for v in range(post_verts_per_post)]
        zs = [vertices[9 * (base + v) + 2] for v in range(post_verts_per_post)]
        px, pz = (min(xs) + max(xs)) / 2.0, (min(zs) + max(zs)) / 2.0
        require(max(xs) - min(xs) <= 2.0 * POST_RADIUS_M + 1e-9
                and max(zs) - min(zs) <= 2.0 * POST_RADIUS_M + 1e-9,
                "f02_post_girth", (p, max(xs) - min(xs), max(zs) - min(zs)))
        base_y, top_y = min(ys), max(ys)
        require(abs(top_y - base_y - recipe.POST_HEIGHT_M) <= 1e-12,
                "f02_post_height", (p, top_y - base_y))
        on_edge = min(abs(abs(px) - half), abs(abs(pz) - half))
        require(on_edge <= 1e-6, "f02_post_off_edge", (p, px, pz))
        err = abs(base_y - recipe.height_at(mounds, px, pz))
        base_err = max(base_err, err)
        require(err <= 1e-9, "f02_post_base_ground", (p, err))
    ring_extent = 0.0
    for p in range(EXPECTED_POSTS):
        base = ground["vertex_count"] + p * post_verts_per_post
        xs = [vertices[9 * (base + v)] for v in range(post_verts_per_post)]
        zs = [vertices[9 * (base + v) + 2] for v in range(post_verts_per_post)]
        px, pz = (min(xs) + max(xs)) / 2.0, (min(zs) + max(zs)) / 2.0
        ring_extent = max(ring_extent, abs(px), abs(pz))
    require(abs(ring_extent - half) <= 1e-6, "f02_invisible_wall", ring_extent - half)

    # -- slope law on the surface (F01's MAX_SLOPE_BOUND, mesh-plane gradients) --
    worst_slope = 0.0
    worst_slope_at = None
    for t in range(0, ground_index_count, 3):
        ia, ib, ic = indices[t], indices[t + 1], indices[t + 2]
        pa = tuple(vertices[9 * ia:9 * ia + 3])
        pb = tuple(vertices[9 * ib:9 * ib + 3])
        pc = tuple(vertices[9 * ic:9 * ic + 3])
        n = face_normal(pa, pb, pc)                      # normalize(-gx, 1, -gz)
        slope = math.hypot(-n[0], -n[2]) / n[1]
        if slope > worst_slope:
            worst_slope, worst_slope_at = slope, (pa[0], pa[2])
    require(worst_slope <= recipe.MAX_SLOPE_BOUND, "f02_slope_law", worst_slope)

    # -- mesh vs analytic (the declared discretization, measured) ---------------
    worst_disc = 0.0
    worst_disc_at = None
    for ix, iz in _ground_cells(grid):
        corners = [_node(grid, ix, iz), _node(grid, ix + 1, iz),
                   _node(grid, ix, iz + 1), _node(grid, ix + 1, iz + 1)]
        for px, pz in ((corners[0][0] + 0.5, corners[0][2] + 0.5),          # cell centre
                       (corners[0][0] + 1 / 3, corners[0][2] + 2 / 3),      # centroid A
                       (corners[0][0] + 2 / 3, corners[0][2] + 1 / 3)):     # centroid B
            analytic = recipe.height_at(mounds, px, pz)
            err = abs(_plane_height(corners, px - corners[0][0], pz - corners[0][2])
                      - analytic)
            if err > worst_disc:
                worst_disc, worst_disc_at = err, (px, pz)
    require(worst_disc <= DISCRETIZATION_BOUND_M, "f02_discretization", worst_disc)

    return {"schema": SCHEMA, "bundle_sha256": pinned,
            "source_declaration_sha256": source["declaration_sha256"],
            "source_file_sha256": source["declaration_file_sha256"],
            "vertex_count": nv, "index_count": len(indices),
            "triangle_count": len(indices) // 3,
            "ground_triangles": expected_ground_tris,
            "post_triangles": expected_post_tris,
            "min_cross_length": min_cross_len,
            "worst_stored_normal_error": worst_normal_err,
            "hygiene_broken": broken_normals, "hygiene_deviant": deviant_normals,
            "worst_grid_error_m": worst_grid_err,
            "worst_ground_outside_extent_m": worst_out,
            "worst_post_girth_out_m": worst_post_out,
            "posts": 80, "worst_post_base_error_m": base_err,
            "worst_triangle_slope_m_per_m": worst_slope,
            "worst_slope_near_xy_m": list(worst_slope_at) if worst_slope_at else None,
            "worst_mesh_analytic_deviation_m": worst_disc,
            "worst_deviation_near_xz_m": list(worst_disc_at) if worst_disc_at else None,
            "validated": True}


def _plane_height(corners, tx, tz):
    """Plane height on the frozen triangulation (terrain_query.py's rule)."""
    h00, h10, h01, h11 = (corners[0][1], corners[1][1], corners[2][1], corners[3][1])
    if tz >= tx:                                          # A = (00, 01, 11)
        return h00 + (h11 - h01) * tx + (h01 - h00) * tz
    return h00 + (h10 - h00) * tx + (h11 - h10) * tz      # B = (00, 11, 10)


def selftest():
    """Compile + validate round trip from the committed declaration."""
    path = Path(__file__).resolve().with_name("clearing_declaration.json")
    return validate_bundle(compile_bundle(path))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    default = Path(__file__).resolve().with_name("terrain_bundle.json")
    declaration_default = Path(__file__).resolve().with_name("clearing_declaration.json")
    if not argv or argv[0] == "compile":
        out = Path(argv[1]) if len(argv) > 1 else default
        bundle = compile_bundle(declaration_default)
        raw = write_bundle(bundle, out)
        print(json.dumps({"bundle": str(out), "bytes": len(raw),
                          "bundle_sha256": bundle["bundle_sha256"]}))
        return 0
    if argv[0] == "validate":
        path = Path(argv[1]) if len(argv) > 1 else default
        receipt = validate_bundle(load_bundle(path))
        print(json.dumps(receipt, sort_keys=True))
        return 0
    if argv[0] == "selftest":
        print(json.dumps(selftest(), sort_keys=True))
        return 0
    raise Refusal("f02_cli_verb", argv)


def load_bundle(path):
    with open(path, "rb") as handle:
        return loads(handle.read())


if __name__ == "__main__":
    sys.exit(main())
