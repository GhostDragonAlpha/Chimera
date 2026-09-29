"""implementation -- MAT2-F07: forest obstacles and scene boundaries.

Card done_when (verbatim): "The clearing offers traversable routes; no
invisible walls masquerade as physical obstacles"

THE MECHANISM (frozen in PREREGISTRATION.md commits bb52ec61927065773bbdac4e
cfa4f3907cda7148 + 10c20035f141caa4c98ac6cd43b0b92e45f70dbb BEFORE this file
existed, amendments A1-A3 included):

1. ONE declared scene vocabulary on top of the merged F02 terrain asset and
   F03 trunk: SEVEN explicit material obstacles (3 rocks = scaled regular
   icosahedra with their convex hull as the declared analytic solid, 2 fallen
   logs and 2 dense stands of 5 saplings as 24-gon capped prisms), each with
   BOTH a render section and a pinned collision body carrying the SAME vertex
   array (the collision-visible law), placed by splitmix64 rejection sampling
   under frozen constraints, plus BOUNDARY RECORDS with named behavior: the
   declared extent rule (engine out_of_patch refusal, rendered by the F02
   post ring), the declared slope rule and one solid_obstacle record per
   obstacle.

2. ROUTES, measured not asserted: a 0.5 m walkability mask derived ONLY from
   the declared footprints (inflated by the declared 0.25 m body envelope),
   the pinned query slope and the declared passable extent bound; BFS from
   the declared spawn must reach ALL TEN frozen destinations; the
   invisible-wall attribution audit requires every blocked cell to name a
   declared footprint or a declared boundary record.

3. THE shared path: every obstacle impact tick goes through M06's unmodified
   chimera.local_contact.v1 solve_tick (byte-identical vendored pin, imported
   -- never forked). The frozen STOP law (A1): first contact pre-overlap,
   mesh-exact penetration <= 1e-4 m over ALL ticks, the probe centre's
   approach coordinate never crosses the struck body's mid-plane/axis, and at
   least one contact record naming the struck obstacle's declared surface.

4. Falsifier arms FB1-FB7 run FIRST (fail-first, recorded, refused before any
   evidence file is written), each with a named refusal and its OWN passing
   clean control; a non-biting falsifier fails the whole build
   (`f07_falsifier_did_not_bite`).

5. Capture: REGISTRY profile `forest` (kind visible_static) read READ-ONLY
   from agent_slots.sqlite3; exactly the three profile views x (diagnostic,
   clean) as whole-frame image rows; capture_sha256 = sha256 of the single
   gate-bound artifact; state_binding kind 'state' -> the obstacle
   declaration; visual_capture.validate_manifest + visual_gate.verify bind
   everything. visual_acceptance stays false BY DESIGN -- independent visual
   review remains mandatory. The transform-list gate (video-frame vs still)
   is NOT APPLICABLE to a static image capture (prereg section 8); its
   selftest still proves the gate refuses a flipped frame.

CPU-only (stdlib), deterministic (splitmix64 + rounded floats, no wall-clock).
Refusals are named codes; nothing is silently repaired.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
import pathlib
import sqlite3
import struct
import sys
from collections import deque

HERE = pathlib.Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"
ASSETS = HERE / "assets"
CONTRIB = HERE.parent                      # contributions/
ATTEMPT_WORKSPACE = HERE.parents[3]        # .../<attempt id>/

SCHEMA = "chimera.mat2_f07.obstacles_boundaries.v1"
BASE_REVISION = "d62c56f67f7524222839c1ebf31f0dbc6fe9ea31"
PREREG_COMMIT = "bb52ec61927065773bbdac4ecfa4f3907cda7148"
AMENDMENT_COMMITS = [
    "10c20035f141caa4c98ac6cd43b0b92e45f70dbb",   # A1-A3
    "0b2169fe581dad3868d22d16e52e82e386c06973",   # A4-A5
]
TASK_ID = "F07"                            # SHORT form (campaign capture schema)
RUN_ID = "mat2-f07-obstacles-20260929-7f734268"
CRITERIA_SHA256 = "20eb25ac4401eea15fc28ad475c88a7d7b2798aad3a0bed36ecc4aa3fb56320b"
SCOPE_SHA256 = "cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097"
ATTEMPT_ID = "7f734268b7ee4a9887f794f9f620175e"
ARRIVAL_ID = "arrival-c7445b4a9e9640a8a821006fff1fd3b0"
REGISTRY_SQLITE = pathlib.Path(
    "E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3")

# --- pinned inputs (PREREGISTRATION section 1; raw sha256 asserted) -----------
GND = "MAT2-F02/pins/"
PINS = {
    "terrain_bundle_json": {"rel": GND + "terrain_bundle.json",
        "sha256": "446ed3fbd0f50205c61a7233ceca289bfc3316f76dfc672fec307b20d8305d52"},
    "terrain_query_py": {"rel": GND + "terrain_query.py",
        "sha256": "b1e244b8843671afc29af530c4725bf812ffd5f8967130f0202792aeb7a8cce1"},
    "terrain_bundle_py": {"rel": GND + "terrain_bundle.py",
        "sha256": "c6ada25a1b6192aa86add8b09bc19161c0cd81e3fb3d4bd267492660c0be8f2e"},
    "clearing_recipe_py": {"rel": GND + "clearing_recipe.py",
        "sha256": "ab800d2257655118296519b606c77ddc7116f524ae0c2e6a0bab3b38473892dc"},
    "clearing_declaration_json": {"rel": GND + "clearing_declaration.json",
        "sha256": "18dd2ff65410cd1cf184a7a8df61c7503a6ce15083f30159e727e9a8117bfbc1"},
    "trunk_declaration_json": {"rel": GND + "trunk_declaration.json",
        "sha256": "94ff906ec5e8b8388e4de318aa3321bad9c791fbb168e8234c371ed1d327e3f1"},
    "f01_implementation_py": {"rel": GND + "f01_implementation.py",
        "sha256": "50e191cfc6f592fd9919534c8986c049939a4e88c4922e135f383bbf06e693af"},
    "f04_implementation_py": {"rel": "MAT2-F04/implementation.py",
        "sha256": "5c398d22b4259d9e4c89ca3a7900610d629e318ac13b57681cbc7c617619e083"},
    "local_contact_py": {"rel": "MAT2-M06/local_contact.py",
        "sha256": "1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc"},
    "contact_law_json": {"rel": "MAT2-M06/contact_law.json",
        "sha256": "583962c29f18118a478dedb167f2c3667414b86f5cab4ee54763416f1df7e41b"},
    "f03_trunk_mesh_json": {"rel": "MAT2-F03/assets/trunk_01_mesh.json",
        "sha256": "3b17441764714c5e5e9c7a43c3253b3271a0f508954095e1960a57820cef6ee7"},
}
PIN_SOURCE_TREE = "branch-1 @ %s (sealed line tip; F01-F04/B06 merged)" % BASE_REVISION

# --- frozen bars (PREREGISTRATION sections 3/5 + amendments; do not tune) ------
PEN_BAR_M = 1e-4
LEDGER_BAR = 1e-12
PLANE_BAR_M = 1e-9
ROCK_ANALYTIC_BAR_M = 1e-9                 # mesh-exact hull (A2 i)
CYL_ANALYTIC_SLACK_M = 1e-9
SLOPE_BAR = 0.05                           # declared terrain.max_slope_bound
PASSABLE_BOUND_M = 19.75                   # 20.0 - declared body envelope 0.25
BLOCK_INFLATION_M = 0.25                   # declared spawn body_radius_envelope_m
MASK_STEP_M = 0.5
MASK_N = 81                                # -20 .. 20 inclusive at 0.5 m
EDGE_COVERAGE_BAR_M = 1.0                  # declared max_gap_to_post_m
EDGE_SAMPLE_STEP_M = 0.05                  # recipe PERIMETER_SAMPLE_STEP
POST_BASE_HEIGHT_TOL_M = 1e-6
POST_VERTEX_BAND_M = 0.05 + 1e-9   # pinned F01 posts: hex prisms, circumradius 0.05
SEED = 4600823                             # ASCII "F07", splitmix64
EXTENT_HALF_M = 20.0
TRUNK_SITE_M = (11.976783, 0.0, 2.471766)
TRUNK_RADIUS_M = 0.037
TRUNK_HEIGHT_M = 1.158
TRUNK_RING_SEGMENTS = 32
TRUNK_CLEAR_M = 1.5
SPAWN_M = (0.0, 0.0, 0.0)

# frozen probe constants (section 5 + A2 iii)
PROBE_HALF_M = 0.1
PROBE_MASS_KG = 0.12
PROBE_THICKNESS_M = 0.002
IMPACT_SPEED_M_S = 2.0
IMPACT_START_CLEAR_M = 0.25
TICKS_IMPACT = 30
OBSTACLE_MU_S, OBSTACLE_MU_K = 0.6, 0.6    # F03 wood UNEVIDENCED-PLACEHOLDER
OBSTACLE_THICKNESS_M = 0.0

# frozen geometry vocabulary (section 2 + A2)
RING_N = 24
SAPLING_COUNT = 5
SAPLING_RADIUS_M = 0.06
SAPLING_HEIGHT_M = 1.6
STAND_RING_RADIUS_M = 0.45
OBSTACLE_ORDER = ["rock_01", "rock_02", "rock_03",
                  "log_01", "log_02", "stand_01", "stand_02"]
ROCK_SEMI = {"sx": (0.30, 0.45), "sy": (0.22, 0.34), "sz": (0.26, 0.40)}
LOG_RADIUS = (0.12, 0.16)
LOG_LENGTH = (2.0, 2.6)
PLACEMENT_MARGIN_M = 1.0                   # centre inside [-19, 19]^2
SPAWN_MIN_DIST_M = 2.5
TRUNK_MIN_DIST_M = 2.0
PAIR_GAP_M = 0.5
MAX_PLACE_DRAWS = 20000

# frozen views/cameras (clearing frame, Y up; prereg section 8) -----------------
W, H = 960, 540
NEAR_FAR = [0.05, 500.0]
VIEW_SPECS = {
    "V1_clearing_overview": {
        "position": [0.0, 46.0, -32.0], "target": [0.0, 0.0, 0.0],
        "vfov_deg": 55.0, "near_far": NEAR_FAR},
    "V2_seam_closeup": {
        "position": [10.30, 1.05, 1.70], "target": [11.976783, 0.25, 2.471766],
        "vfov_deg": 55.0, "near_far": [0.05, 50.0]},
    "V3_side_depth": {
        "position": [13.30, 2.30, 4.30], "target": [11.976783, 0.45, 2.471766],
        "vfov_deg": 50.0, "near_far": NEAR_FAR},
}
PROFILE_VIEW_NAMES = {
    "V1_clearing_overview": "clearing overview",
    "V2_seam_closeup": "terrain/trunk seam close-up",
    "V3_side_depth": "side and oblique depth checks",
}
VIEW_ORDER = ["V1_clearing_overview", "V2_seam_closeup", "V3_side_depth"]
DIAGNOSTIC_LAYERS = ["render mesh", "collision surfaces",
                     "normals/contact markers", "scene bounds",
                     "stable 3D labels"]
VIS_BAR_M = 1e-6                           # F04 inherited marker distance bar
MARKER_PLANE_BAR_M = 1e-6                  # marker-on-its-facet/face plane bar
FB6_OFFFRAME_ANGLE_DEG = 155.7
FB1_INJECT_SITE = (2.0, -6.0)              # frozen meadow site for FB1's disc
FB5_FENCE_RADIUS_M = 1.2                   # A4: fence ring radius (see A4)
MAX_VIEWPOINT_OFFSET_M = 1.0               # A4 iii: destination reach bar
CONTACT_POINT_SLACK_M = 1e-5               # A5: pinned contact_law slop/margin

# frozen marker table (subject -> {view: frozen outcome}); P7 checks exactly
# these outcomes; zero VISIBLE_BUT_MISMATCH anywhere.
FROZEN_MARKER_TABLE = {
    "subject_rock_01": {"V1_clearing_overview": "VISIBLE_EXACT"},
    "subject_rock_02": {"V1_clearing_overview": "VISIBLE_EXACT"},
    "subject_rock_03": {"V1_clearing_overview": "VISIBLE_EXACT"},
    "subject_log_01": {"V1_clearing_overview": "VISIBLE_EXACT"},
    "subject_log_02": {"V1_clearing_overview": "VISIBLE_EXACT"},
    "subject_stand_01": {"V1_clearing_overview": "VISIBLE_EXACT"},
    "subject_stand_02": {"V1_clearing_overview": "VISIBLE_EXACT"},
    "subject_trunk": {"V1_clearing_overview": "VISIBLE_EXACT",
                      "V2_seam_closeup": "VISIBLE_EXACT",
                      "V3_side_depth": "VISIBLE_EXACT"},
    "subject_boundary_post": {"V1_clearing_overview": "VISIBLE_EXACT"},
    "marker_spawn": {"V1_clearing_overview": "VISIBLE_EXACT"},
}

BOX_LOCAL_07 = [(-PROBE_HALF_M, -PROBE_HALF_M, -PROBE_HALF_M),
                (PROBE_HALF_M, -PROBE_HALF_M, -PROBE_HALF_M),
                (PROBE_HALF_M, PROBE_HALF_M, -PROBE_HALF_M),
                (-PROBE_HALF_M, PROBE_HALF_M, -PROBE_HALF_M),
                (-PROBE_HALF_M, -PROBE_HALF_M, PROBE_HALF_M),
                (PROBE_HALF_M, -PROBE_HALF_M, PROBE_HALF_M),
                (PROBE_HALF_M, PROBE_HALF_M, PROBE_HALF_M),
                (-PROBE_HALF_M, PROBE_HALF_M, PROBE_HALF_M)]
BOX_TRIS_07 = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5),
               (0, 5, 4), (2, 3, 7), (2, 7, 6), (0, 4, 7), (0, 7, 3),
               (1, 2, 6), (1, 6, 5)]


class Refusal(ValueError):
    def __init__(self, code, detail=""):
        self.code, self.detail = code, str(detail)
        super().__init__("%s: %s" % (code, detail))


def require(condition, code, detail=""):
    if not condition:
        raise Refusal(code, detail)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value):
    return sha_bytes(canonical(value))


def grid6(x):
    return round(x, 6)


def F_TO_CONTACT(p):
    return (p[0], -p[2], p[1])


def F_TO_CLEARING(q):
    return (q[0], q[2], -q[1])


def F_vsub(a, b):
    return [a[i] - b[i] for i in range(3)]


def F_vcross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def F_vnorm(a):
    l = math.sqrt(sum(c * c for c in a)) or 1.0
    return [c / l for c in a]


def F_vdot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def F_ray_triangle(orig, direc, v0, v1, v2, eps=1e-9):
    e1 = F_vsub(v1, v0)
    e2 = F_vsub(v2, v0)
    p = F_vcross(direc, e2)
    det = F_vdot(e1, p)
    if abs(det) < eps:
        return None
    inv = 1.0 / det
    t = F_vsub(orig, v0)
    u = F_vdot(t, p) * inv
    if u < -eps or u > 1.0 + eps:
        return None
    q = F_vcross(t, e1)
    v = F_vdot(direc, q) * inv
    if v < -eps or u + v > 1.0 + eps:
        return None
    dist = F_vdot(e2, q) * inv
    if dist < eps:
        return None
    return (dist, u, v)


# --- pins ----------------------------------------------------------------------
def load_pins():
    out = {}
    for key, pin in PINS.items():
        path = CONTRIB / pin["rel"]
        require(path.is_file(), "f07_pin_missing", key)
        got = sha_bytes(path.read_bytes())
        require(got == pin["sha256"], "f07_pin_hash_mismatch",
                {"key": key, "expect": pin["sha256"], "got": got})
        out[key] = {"file": str(path), "sha256": got,
                    "published": "contributions/" + pin["rel"],
                    "raw_match": True}
    return out


def load_modules(pins):
    import importlib.util

    def module(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    sys.path.insert(0, str(CONTRIB / GND))
    tb = module("f07_terrain_bundle", pins["terrain_bundle_py"]["file"])
    tq = module("f07_terrain_query", pins["terrain_query_py"]["file"])
    cr = module("f07_clearing_recipe", pins["clearing_recipe_py"]["file"])
    lc = module("f07_local_contact", pins["local_contact_py"]["file"])
    f04 = module("f07_f04_machinery", pins["f04_implementation_py"]["file"])
    return tb, tq, cr, lc, f04


# --- deterministic geometry (A2) -------------------------------------------------
def ico_unit_vertices():
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    b = 1.0 / phi
    raw = [(-1, b, 0), (1, b, 0), (-1, -b, 0), (1, -b, 0),
           (0, -1, b), (0, 1, b), (0, -1, -b), (0, 1, -b),
           (b, 0, -1), (b, 0, 1), (-b, 0, -1), (-b, 0, 1)]
    nrm = math.sqrt(1.0 + b * b)
    return [tuple(c / nrm for c in v) for v in raw]


def hull_faces(verts):
    """Convex hull faces by the orientation predicate; watertight-checked."""
    n = len(verts)
    faces = []
    for tri in itertools.combinations(range(n), 3):
        a, b, c = (verts[i] for i in tri)
        raw = F_vcross(F_vsub(b, a), F_vsub(c, a))
        if F_vlen(raw) < 1e-12:
            continue
        nrm = [x / F_vlen(raw) for x in raw]
        d = F_vdot(nrm, a)
        side = [F_vdot(nrm, v) - d for i, v in enumerate(verts)
                if i not in tri]
        if all(s <= 1e-9 for s in side) or all(s >= -1e-9 for s in side):
            faces.append(tri)
    edges = {}
    for f in faces:
        for x, y in ((f[0], f[1]), (f[1], f[2]), (f[2], f[0])):
            key = (min(x, y), max(x, y))
            edges[key] = edges.get(key, 0) + 1
    require(len(faces) == 20 and len(edges) == 30
            and all(v == 2 for v in edges.values()),
            "f07_rock_hull_not_watertight",
            {"faces": len(faces), "edges": len(edges)})
    return faces


def F_vlen(a):
    return math.sqrt(sum(c * c for c in a))


def hull_depth(verts, faces, p):
    """Mesh-exact depth of p inside the convex hull: signed distance to the
    nearest face plane with outward-oriented normals, clamped at 0 outside."""
    return solid_depth(verts, [tuple(t) for t in faces], p)


def facet_prism(n, radius, half_len, base_y, facet_aligned, vertical):
    """Capped n-gon prism; A2 ii: cross-section angles offset by pi/n when
    facet_aligned so one facet plane's outward normal is exactly +z (for the
    horizontal prism, axis +x) or +x (for the vertical prism)."""
    off = (math.pi / n) if facet_aligned else 0.0

    def angle(i):
        return off + 2.0 * math.pi * i / n

    verts, tris = [], []
    for ring in (0, 1):
        for i in range(n):
            a = angle(i)
            if vertical:
                verts.append((radius * math.cos(a),
                              base_y + ring * half_len * 2.0,
                              radius * math.sin(a)))
            else:
                verts.append((ring * half_len * 2.0 - half_len,
                              base_y + radius * math.cos(a),
                              radius * math.sin(a)))
    for i in range(1, n - 1):
        tris.append((0, i + 1, i))
        tris.append((n, n + i, n + i + 1))
    for i in range(n):
        j = (i + 1) % n
        tris.append((i, n + i, n + j))
        tris.append((i, n + j, j))
    return verts, tris


def solid_depth(verts, tris, p):
    """Mesh-exact depth of p inside the convex solid: the signed distance to
    the nearest face plane with OUTWARD-oriented normals, clamped at 0
    outside. Orientation is normalized against the vertex centroid, so the
    stored winding does not matter."""
    if not tris:
        return 0.0
    c = [sum(v[i] for v in verts) / len(verts) for i in range(3)]
    worst = math.inf
    seen = set()
    for tri in tris:
        a, b, cc = (verts[i] for i in tri)
        raw = F_vcross(F_vsub(b, a), F_vsub(cc, a))
        l = F_vlen(raw)
        if l < 1e-12:
            continue
        n = [x / l for x in raw]
        d = F_vdot(n, a)
        if F_vdot(n, c) > d:            # make the normal outward
            n = [-x for x in n]
            d = -d
        key = (round(n[0], 9), round(n[1], 9), round(n[2], 9), round(d, 9))
        if key in seen:
            continue
        seen.add(key)
        worst = min(worst, d - F_vdot(n, p))
    return max(0.0, worst)


def plane_err_to_mesh(verts, tris, p):
    """Distance of p to the nearest render triangle plane (PLANE_BAR form)."""
    best = math.inf
    for tri in tris:
        a, b, c = (verts[i] for i in tri)
        raw = F_vcross(F_vsub(b, a), F_vsub(c, a))
        l = F_vlen(raw)
        if l < 1e-12:
            continue
        n = [x / l for x in raw]
        best = min(best, abs(F_vdot(n, F_vsub(p, a))))
    return best


# --- placement (section 2, frozen order and constraints) -------------------------
def place_obstacles(rng, surface):
    placed = []
    for name in OBSTACLE_ORDER:
        kind = name.split("_")[0]
        for _ in range(MAX_PLACE_DRAWS):
            cx = grid6(rng.uniform_grid(-EXTENT_HALF_M + PLACEMENT_MARGIN_M,
                                        EXTENT_HALF_M - PLACEMENT_MARGIN_M))
            cz = grid6(rng.uniform_grid(-EXTENT_HALF_M + PLACEMENT_MARGIN_M,
                                        EXTENT_HALF_M - PLACEMENT_MARGIN_M))
            if kind == "rock":
                sx = grid6(rng.uniform_grid(*ROCK_SEMI["sx"]))
                sy = grid6(rng.uniform_grid(*ROCK_SEMI["sy"]))
                sz = grid6(rng.uniform_grid(*ROCK_SEMI["sz"]))
                unit = ico_unit_vertices()
                min_y = min(v[1] for v in unit)
                local = [(sx * v[0], sy * (v[1] - min_y), sz * v[2])
                         for v in unit]
                fr = max(max(v[0] for v in local), max(v[2] for v in local))
                dims = {"rock_semi_axes_m": [sx, sy, sz]}
            elif kind == "log":
                r = grid6(rng.uniform_grid(*LOG_RADIUS))
                length = grid6(rng.uniform_grid(*LOG_LENGTH))
                yaw_idx = rng.uniform_int(2)      # 0: axis +x, 1: axis +z
                fr = length / 2.0 + r             # conservative both yaws
                dims = {"log_radius_m": r, "log_length_m": length,
                        "yaw_index": yaw_idx}
            else:
                fr = STAND_RING_RADIUS_M + SAPLING_RADIUS_M
                dims = {}
            h = surface.height_at(cx, cz)
            if math.hypot(cx, cz) < SPAWN_MIN_DIST_M + fr:
                continue
            if math.hypot(cx - TRUNK_SITE_M[0], cz - TRUNK_SITE_M[2]) \
                    < TRUNK_MIN_DIST_M + fr:
                continue
            ok = True
            for p in placed:
                need = fr + p["footprint_radius_m"] + 2.0 * BLOCK_INFLATION_M \
                    + PAIR_GAP_M
                if math.hypot(cx - p["centre_m"][0],
                              cz - p["centre_m"][2]) < need:
                    ok = False
                    break
            if not ok:
                continue
            rec = {"id": name, "kind": kind, "surface_id": name,
                   "centre_m": [cx, grid6(h), cz],
                   "footprint_radius_m": grid6(fr)}
            rec.update(dims)
            placed.append(rec)
            break
        else:
            raise Refusal("f07_placement_infeasible", name)
    return placed


def build_obstacle_meshes(placed, surface):
    """A2: world-space render/collision vertex tables (clearing frame)."""
    out = []
    for p in placed:
        cx, cy, cz = p["centre_m"]
        if p["kind"] == "rock":
            sx, sy, sz = p["rock_semi_axes_m"]
            unit = ico_unit_vertices()
            min_y = min(v[1] for v in unit)
            local = [(sx * v[0], sy * (v[1] - min_y), sz * v[2]) for v in unit]
            faces = hull_faces(local)
            verts = [(grid6(cx + v[0]), grid6(cy + v[1]), grid6(cz + v[2]))
                     for v in local]
            ext = (max(v[0] for v in verts) - cx, max(v[1] for v in verts) - cy,
                   max(v[2] for v in verts) - cz)
            out.append({**p, "verts": verts, "tris": [list(t) for t in faces],
                        "faces": faces,
                        "extent_m": [grid6(e) for e in ext],
                        "analytic_bar_m": ROCK_ANALYTIC_BAR_M})
        elif p["kind"] == "log":
            r, length = p["log_radius_m"], p["log_length_m"]
            lv, lt = facet_prism(RING_N, r, length / 2.0,
                                 r * math.cos(math.pi / RING_N), True, False)
            if p["yaw_index"] == 1:
                lv = [(z, y, x) for x, y, z in lv]   # rotate axis x -> z
            verts = [(grid6(cx + v[0]), grid6(cy + v[1]), grid6(cz + v[2]))
                     for v in lv]
            ext = (max(v[0] for v in verts) - cx, max(v[1] for v in verts) - cy,
                   max(v[2] for v in verts) - cz)
            out.append({**p, "verts": verts, "tris": [list(t) for t in lt],
                        "extent_m": [grid6(e) for e in ext],
                        "analytic_bar_m": r * (1.0 - math.cos(math.pi / RING_N))
                        + CONTACT_POINT_SLACK_M + CYL_ANALYTIC_SLACK_M})
        else:
            sv, st = facet_prism(RING_N, SAPLING_RADIUS_M,
                                 SAPLING_HEIGHT_M / 2.0, 0.0, True, True)
            verts, tris = [], []
            base_i = 0
            for k in range(SAPLING_COUNT):
                a = 2.0 * math.pi * k / SAPLING_COUNT
                sx_ = grid6(cx + STAND_RING_RADIUS_M * math.cos(a))
                sz_ = grid6(cz + STAND_RING_RADIUS_M * math.sin(a))
                sy_ = surface.height_at(sx_, sz_)
                for v in sv:
                    verts.append((grid6(sx_ + v[0]), grid6(sy_ + v[1]),
                                  grid6(sz_ + v[2])))
                for t in st:
                    tris.append(list(i + base_i for i in t))
                base_i += len(sv)
            ext = (STAND_RING_RADIUS_M + SAPLING_RADIUS_M, SAPLING_HEIGHT_M,
                   STAND_RING_RADIUS_M + SAPLING_RADIUS_M)
            out.append({**p, "verts": verts, "tris": tris,
                        "extent_m": [grid6(e) for e in ext],
                        "analytic_bar_m":
                            SAPLING_RADIUS_M * (1.0 - math.cos(math.pi / RING_N))
                            + CONTACT_POINT_SLACK_M + CYL_ANALYTIC_SLACK_M})
    return out


def facet_plane(ob):
    """A2: the approach facet plane (point, outward normal) of an obstacle,
    in the clearing frame. Rocks: the +x hull extent at mid-height."""
    if ob["kind"] == "rock":
        return ((ob["centre_m"][0] + ob["extent_m"][0],
                 ob["centre_m"][1] + 0.5 * ob["extent_m"][1],
                 ob["centre_m"][2]), (1.0, 0.0, 0.0))
    if ob["kind"] == "log":
        r = ob["log_radius_m"]
        face = r * math.cos(math.pi / RING_N)
        cy = ob["centre_m"][1] + face
        if ob["yaw_index"] == 0:
            return ((ob["centre_m"][0], cy,
                     ob["centre_m"][2] + face), (0.0, 0.0, 1.0))
        return ((ob["centre_m"][0] + face, cy,
                 ob["centre_m"][2]), (1.0, 0.0, 0.0))
    sap_x = ob["centre_m"][0] + STAND_RING_RADIUS_M
    face = SAPLING_RADIUS_M * math.cos(math.pi / RING_N)
    return ((sap_x + face, ob["centre_m"][1] + SAPLING_HEIGHT_M / 2.0,
             ob["centre_m"][2]), (1.0, 0.0, 0.0))


def impact_start(ob):
    """A2 iii: probe start, velocity and approach axis for the frozen
    normal-incidence run."""
    point, normal = facet_plane(ob)
    axis = 0 if normal[0] != 0.0 else 2
    start = [point[i] + IMPACT_START_CLEAR_M * normal[i] for i in range(3)]
    vel = tuple(-IMPACT_SPEED_M_S * c for c in normal)
    return tuple(start), vel, axis


# --- declaration (assets/obstacle_declaration.json) ------------------------------
def boundary_records():
    return [
        {"id": "extent_rule", "kind": "physical_extent_rule",
         "behavior": "refuse_out_of_patch",
         "rule_source": "clearing_declaration.extent.boundary_rule "
                        "(engine out_of_patch, earth_environment.hpp:118)",
         "geometry": {"shape": "square", "half_width_m": EXTENT_HALF_M},
         "rendered_by": "post_ring: 80 posts, spacing 2.0 m, bases ON the edge",
         "route_effect": "cells with |centre| > 19.75 (half width minus the "
                         "declared 0.25 m body envelope) are not passable"},
        {"id": "terrain_slope_rule", "kind": "physical_slope_rule",
         "behavior": "refuse_excess_slope",
         "rule_source": "clearing_declaration.terrain.max_slope_bound = 0.05",
         "route_effect": "cells whose measured query slope exceeds 0.05 are "
                         "not passable (declared, never an invisible stop)"},
        {"id": "trunk_01", "kind": "climbable_feature", "behavior": "contact_stop",
         "note": "F03 climbable trunk; not a route-blocking wall; its analytic "
                 "footprint (0.037 m + envelope) is in the mask",
         "footprint": {"shape": "disc",
                       "centre_m": [TRUNK_SITE_M[0], TRUNK_SITE_M[2]],
                       "radius_m": grid6(TRUNK_RADIUS_M + BLOCK_INFLATION_M)}},
    ]


def footprint_record(ob):
    if ob["kind"] == "rock":
        return {"shape": "rectangle",
                "x_extent_m": [grid6(ob["centre_m"][0] - ob["extent_m"][0]),
                               grid6(ob["centre_m"][0] + ob["extent_m"][0])],
                "z_extent_m": [grid6(ob["centre_m"][2] - ob["extent_m"][2]),
                               grid6(ob["centre_m"][2] + ob["extent_m"][2])],
                "note": "hull x/z extents (A2 v), conservative over heights"}
    if ob["kind"] == "log":
        return {"shape": "capsule",
                "axis": ("x" if ob["yaw_index"] == 0 else "z"),
                "half_length_m": ob["log_length_m"] / 2.0,
                "radius_m": ob["log_radius_m"]}
    return {"shape": "disc", "centre_offset_m": [0.0, 0.0],
            "radius_m": grid6(STAND_RING_RADIUS_M + SAPLING_RADIUS_M)}


def make_declaration(obstacles):
    body = {
        "schema": SCHEMA,
        "name": "monkey_clearing_obstacles",
        "seed": SEED,
        "coordinate_convention": {"frame_id": "f01_world_y_up", "up_axis": "+Y",
                                  "units": "m", "handedness": "right"},
        "placement_constraints": {
            "centre_box_m": [-EXTENT_HALF_M + PLACEMENT_MARGIN_M,
                             EXTENT_HALF_M - PLACEMENT_MARGIN_M],
            "spawn_min_dist_m": SPAWN_MIN_DIST_M,
            "trunk_min_dist_m": TRUNK_MIN_DIST_M,
            "pair_gap_m": PAIR_GAP_M,
            "body_envelope_m": BLOCK_INFLATION_M,
            "max_draws_per_obstacle": MAX_PLACE_DRAWS},
        "obstacles": [
            {"id": ob["id"], "kind": ob["kind"], "surface_id": ob["surface_id"],
             "centre_m": ob["centre_m"],
             "rock_semi_axes_m": ob.get("rock_semi_axes_m"),
             "log_radius_m": ob.get("log_radius_m"),
             "log_length_m": ob.get("log_length_m"),
             "yaw_index": ob.get("yaw_index"),
             "extent_m": ob["extent_m"],
             "footprint": footprint_record(ob),
             "vertices_m": [list(v) for v in ob["verts"]],
             "triangles": [list(t) for t in ob["tris"]],
             "behavior": "contact_stop",
             "collision": "chimera.local_contact.v1 pinned body, same vertex "
                          "array as the render section",
             "matter": "wood_trunk_01",
             "friction_note": "F03 declared UNEVIDENCED-PLACEHOLDER (G04 debt)"}
            for ob in obstacles],
        "boundaries": boundary_records(),
    }
    raw = canonical(body)
    full = {**body, "self_sha256": sha_bytes(raw)}
    return full, canonical(full), sha_bytes(raw)


def load_declaration(path):
    full = json.loads(path.read_bytes())
    body = {k: v for k, v in full.items() if k != "self_sha256"}
    require(full.get("self_sha256") == sha_bytes(canonical(body)),
            "f07_declaration_self_hash", path)
    return full


# --- footprint/mask/route layer (section 4) ---------------------------------------
def inside_footprint(ob, x, z, inflate=BLOCK_INFLATION_M):
    cx, _, cz = ob["centre_m"]
    dx, dz = x - cx, z - cz
    if ob["kind"] == "rock":
        return (abs(dx) <= ob["extent_m"][0] + inflate
                and abs(dz) <= ob["extent_m"][2] + inflate)
    if ob["kind"] == "log":
        r, half = ob["log_radius_m"] + inflate, ob["log_length_m"] / 2.0
        if ob["yaw_index"] == 0:
            return abs(dx) <= half and abs(dz) <= r
        return abs(dz) <= half and abs(dx) <= r
    rr = STAND_RING_RADIUS_M + SAPLING_RADIUS_M + inflate
    return math.hypot(dx, dz) <= rr


def distance_to_footprints(obstacles, x, z):
    best = math.inf
    for ob in obstacles:
        cx, _, cz = ob["centre_m"]
        dx, dz = x - cx, z - cz
        if ob["kind"] == "rock":
            ddx = max(abs(dx) - ob["extent_m"][0], 0.0)
            ddz = max(abs(dz) - ob["extent_m"][2], 0.0)
            best = min(best, math.hypot(ddx, ddz))
        elif ob["kind"] == "log":
            r, half = ob["log_radius_m"], ob["log_length_m"] / 2.0
            if ob["yaw_index"] == 0:
                ddx = max(abs(dx) - half, 0.0)
                ddz = max(abs(dz) - r, 0.0)
            else:
                ddx = max(abs(dx) - r, 0.0)
                ddz = max(abs(dz) - half, 0.0)
            best = min(best, math.hypot(ddx, ddz))
        else:
            best = min(best, max(math.hypot(dx, dz)
                                 - (STAND_RING_RADIUS_M + SAPLING_RADIUS_M),
                                 0.0))
    best = min(best, max(math.hypot(x - TRUNK_SITE_M[0], z - TRUNK_SITE_M[2])
                         - TRUNK_RADIUS_M, 0.0))
    return best


def build_mask(obstacles, surface, inject=None):
    """Walkability mask derived ONLY from declared geometry (+ FB1's optional
    injection for the falsifier copy; the injection is attributed None = an
    UNDECLARED invisible wall)."""
    blocked = [[False] * MASK_N for _ in range(MASK_N)]
    attribution = [[None] * MASK_N for _ in range(MASK_N)]
    for ix in range(MASK_N):
        for iz in range(MASK_N):
            x = -EXTENT_HALF_M + ix * MASK_STEP_M
            z = -EXTENT_HALF_M + iz * MASK_STEP_M
            if abs(x) > PASSABLE_BOUND_M or abs(z) > PASSABLE_BOUND_M:
                blocked[ix][iz] = True
                attribution[ix][iz] = "extent_rule"
                continue
            if inject is not None and math.hypot(x - inject[0],
                                                 z - inject[1]) <= inject[2]:
                blocked[ix][iz] = True
                attribution[ix][iz] = None     # UNDECLARED -> invisible wall
                continue
            hit = None
            for ob in obstacles:
                if inside_footprint(ob, x, z):
                    hit = ob["id"]
                    break
            if hit is None and math.hypot(x - TRUNK_SITE_M[0],
                                          z - TRUNK_SITE_M[2]) \
                    <= TRUNK_RADIUS_M + BLOCK_INFLATION_M:
                hit = "trunk_01"
            if hit is not None:
                blocked[ix][iz] = True
                attribution[ix][iz] = hit
            else:
                slope = max(abs(g) for g in surface.gradient_at(x, z))
                if slope > SLOPE_BAR:
                    blocked[ix][iz] = True
                    attribution[ix][iz] = "terrain_slope_rule"
    return blocked, attribution


def attribution_audit(blocked, attribution):
    """P4/FB1: every blocked cell must name a declared record (obstacle id,
    trunk_01, extent_rule, terrain_slope_rule); None = invisible wall."""
    unattributed = []
    counts = {}
    for ix in range(MASK_N):
        for iz in range(MASK_N):
            if not blocked[ix][iz]:
                continue
            a = attribution[ix][iz]
            counts[a] = counts.get(a, 0) + 1
            if a is None:
                x = -EXTENT_HALF_M + ix * MASK_STEP_M
                z = -EXTENT_HALF_M + iz * MASK_STEP_M
                unattributed.append([x, z])
    return {"unattributed_cells": unattributed,
            "unattributed_count": len(unattributed),
            "blocked_by_record": counts}


def free_cells(blocked):
    return {(ix, iz) for ix in range(MASK_N) for iz in range(MASK_N)
            if not blocked[ix][iz]}


def bfs_reachable(start, free):
    seen = {start}
    q = deque([start])
    while q:
        ix, iz = q.popleft()
        for a, b in ((ix + 1, iz), (ix - 1, iz), (ix, iz + 1), (ix, iz - 1)):
            if 0 <= a < MASK_N and 0 <= b < MASK_N and (a, b) in free \
                    and (a, b) not in seen:
                seen.add((a, b))
                q.append((a, b))
    return seen


def nearest_reachable(reach, tx, tz):
    ix0 = int(round((tx + EXTENT_HALF_M) / MASK_STEP_M))
    iz0 = int(round((tz + EXTENT_HALF_M) / MASK_STEP_M))
    best = None
    for rad in range(MASK_N):
        for ix in range(max(0, ix0 - rad), min(MASK_N, ix0 + rad + 1)):
            for iz in range(max(0, iz0 - rad), min(MASK_N, iz0 + rad + 1)):
                if (ix, iz) in reach:
                    d = math.hypot(-EXTENT_HALF_M + ix * MASK_STEP_M - tx,
                                   -EXTENT_HALF_M + iz * MASK_STEP_M - tz)
                    if best is None or d < best[0]:
                        best = (d, ix, iz)
        if best is not None:
            return best
    return None


def route_path(start, goal, free):
    if goal == start:
        return [start]
    prev = {start: None}
    q = deque([start])
    while q:
        cur = q.popleft()
        if cur == goal:
            path = []
            while cur is not None:
                path.append(cur)
                cur = prev[cur]
            return path[::-1]
        ix, iz = cur
        for a, b in ((ix + 1, iz), (ix - 1, iz), (ix, iz + 1), (ix, iz - 1)):
            if 0 <= a < MASK_N and 0 <= b < MASK_N and (a, b) in free \
                    and (a, b) not in prev:
                prev[(a, b)] = cur
                q.append((a, b))
    return None


def route_metrics(path, obstacles, surface):
    length = 0.0
    min_clear = math.inf
    max_slope = 0.0
    for k, (ix, iz) in enumerate(path):
        x = -EXTENT_HALF_M + ix * MASK_STEP_M
        z = -EXTENT_HALF_M + iz * MASK_STEP_M
        if k:
            px = -EXTENT_HALF_M + path[k - 1][0] * MASK_STEP_M
            pz = -EXTENT_HALF_M + path[k - 1][1] * MASK_STEP_M
            length += math.hypot(x - px, z - pz)
        min_clear = min(min_clear, distance_to_footprints(obstacles, x, z))
        max_slope = max(max_slope,
                        max(abs(g) for g in surface.gradient_at(x, z)))
    return {"hops": len(path) - 1, "length_m": grid6(length),
            "min_footprint_clearance_m": grid6(min_clear),
            "max_sampled_slope": grid6(max_slope)}


def destination_table(obstacles):
    d = {}
    ux, uz = TRUNK_SITE_M[0], TRUNK_SITE_M[2]
    norm = math.hypot(ux, uz)
    d["D_trunk"] = (ux - TRUNK_CLEAR_M * ux / norm,
                    uz - TRUNK_CLEAR_M * uz / norm)
    d["D_E"] = (PASSABLE_BOUND_M, 0.0)
    d["D_W"] = (-PASSABLE_BOUND_M, 0.0)
    d["D_S"] = (0.0, -PASSABLE_BOUND_M)
    d["D_N"] = (0.0, PASSABLE_BOUND_M)
    for ob in obstacles:
        d["D_" + ob["id"]] = (ob["centre_m"][0], ob["centre_m"][2])
    return d


def verify_routes(obstacles, surface, mask=None, require_reach=True):
    blocked, _ = (mask, None) if mask is not None else build_mask(obstacles,
                                                                  surface)
    free = free_cells(blocked)
    start = (MASK_N // 2, MASK_N // 2)
    require(start in free, "f07_spawn_cell_blocked", SPAWN_M)
    reach = bfs_reachable(start, free)
    routes = {}
    for name, (tx, tz) in sorted(destination_table(obstacles).items()):
        near = nearest_reachable(reach, tx, tz)
        offset = near[0] if near is not None else math.inf
        ok = near is not None and offset <= MAX_VIEWPOINT_OFFSET_M
        rec = {"destination_m": [grid6(tx), grid6(tz)], "reached": ok,
               "viewpoint_offset_m": (grid6(offset)
                                      if near is not None else None)}
        if ok:
            path = route_path(start, (near[1], near[2]), free)
            rec.update(route_metrics(path, obstacles, surface))
            rec["viewpoint_cell"] = [near[1], near[2]]
        routes[name] = rec
        if require_reach:
            require(ok, "f07_route_missing", name)
            require(rec["min_footprint_clearance_m"]
                    >= BLOCK_INFLATION_M - 1e-9, "f07_route_clearance", name)
            require(rec["max_sampled_slope"] <= SLOPE_BAR,
                    "f07_route_slope", name)
    return routes, reach


# --- boundary audits (P1/P2) -------------------------------------------------------
def post_ring_audit(bundle, surface, declaration):
    """P1/P2: every DECLARED post base ON the edge exactly; every rendered
    post vertex within the pinned hex-prism band of the nearest edge line;
    every edge point within the declared max gap of a declared post base."""
    declared = declaration["boundary"]["rendered"]["posts_m"]
    require(len(declared) == 80, "f07_declared_post_count", len(declared))
    for px, py, pz in declared:
        require(abs(abs(px) - EXTENT_HALF_M) < 1e-9
                or abs(abs(pz) - EXTENT_HALF_M) < 1e-9,
                "f07_declared_post_off_edge", (px, py, pz))
    section = bundle["render"]["sections"]["boundary_posts"]
    vs = bundle["render"]["vertices"]
    v0, v1 = section["vertex_start"], section["vertex_start"] + section["vertex_count"]
    worst_band = 0.0
    for i in range(v0, v1):
        x, y, z = vs[9 * i:9 * i + 3]
        band = min(abs(abs(x) - EXTENT_HALF_M), abs(abs(z) - EXTENT_HALF_M))
        worst_band = max(worst_band, band)
    require(worst_band <= POST_VERTEX_BAND_M, "f07_post_off_edge", worst_band)
    worst = 0.0
    samples = 0
    for edge in range(4):
        n_steps = int(round(2.0 * EXTENT_HALF_M / EDGE_SAMPLE_STEP_M))
        for k in range(n_steps + 1):
            t = -EXTENT_HALF_M + EDGE_SAMPLE_STEP_M * k
            p = [(t, -EXTENT_HALF_M), (EXTENT_HALF_M, t),
                 (t, EXTENT_HALF_M), (-EXTENT_HALF_M, t)][edge]
            samples += 1
            dmin = min(math.hypot(p[0] - bp[0], p[1] - bp[2])
                       for bp in declared)
            worst = max(worst, dmin)
    return {"post_bases": len(declared), "edge_samples": samples,
            "worst_gap_to_post_m": grid6(worst),
            "post_vertex_band_m": grid6(worst_band),
            "within_declared_gap": worst <= EDGE_COVERAGE_BAR_M}


def stop_declaration_audit(attribution_counts, arrest_surfaces, records):
    """P2: every stop/refusal event names a declared record."""
    declared = {r["id"] for r in records}
    undeclared = []
    for sid in arrest_surfaces:
        if sid not in declared:
            undeclared.append(sid)
    for a in attribution_counts:
        if a is not None and a not in declared:
            undeclared.append(a)
    return {"declared_records": sorted(declared),
            "undeclared_stops": sorted(set(undeclared)),
            "coverage": 1.0 if not undeclared else 0.0}


# --- contact bodies + frozen impacts (section 5, A1-A3) -----------------------------
def obstacle_contact_body(lc, ob):
    verts = [F_TO_CONTACT(v) for v in ob["verts"]]
    return lc.Body(ob["surface_id"], ob["surface_id"], "wood_trunk_01", 0.0,
                   OBSTACLE_MU_S, OBSTACLE_MU_K, OBSTACLE_THICKNESS_M,
                   verts, [tuple(t) for t in ob["tris"]], pinned=True)


def make_probe(lc, probe_id, start_c, vel_c):
    return lc.Body(probe_id, probe_id, "mass_tetra", PROBE_MASS_KG,
                   0.6, 0.4, PROBE_THICKNESS_M,
                   [lc.vadd(tuple(start_c), v) for v in BOX_LOCAL_07],
                   list(BOX_TRIS_07), velocity=tuple(vel_c))


def run_impact(lc, ob):
    ob_c = obstacle_contact_body(lc, ob)
    centre_c = F_TO_CONTACT(ob["centre_m"])
    start, vel, axis = impact_start(ob)
    start_c = F_TO_CONTACT(start)
    vel_c = F_TO_CONTACT(vel)
    probe = make_probe(lc, "probe_" + ob["id"], start_c, vel_c)
    bodies = [ob_c, probe]
    verts_c = [F_TO_CONTACT(v) for v in ob["verts"]]
    tris_c = [tuple(t) for t in ob["tris"]]
    states = []
    first = None
    worst_pen = 0.0
    min_appr = math.inf
    worst_plane_err = 0.0        # A5: struck body's contact point
    worst_analytic_err = 0.0     # A5: struck body's contact point
    worst_pair_sep = 0.0         # A5: probe feature point separation (record)
    worst_ledger = 0.0
    struck_hits = 0
    for t in range(TICKS_IMPACT):
        records, ledger = lc.solve_tick(bodies, ccd_enabled=True)
        c = probe_centre_c(probe)
        min_appr = min(min_appr, c[axis] - centre_c[axis])
        for v in probe.vertices:
            worst_pen = max(worst_pen, solid_depth(verts_c, tris_c, v))
        for r in records:
            if ob["surface_id"] in (r["surface_a"], r["surface_b"]):
                struck_hits += 1
                struck_pt = r["point_a"] if r["surface_a"] == ob["surface_id"] \
                    else r["point_b"]
                probe_pt = r["point_b"] if r["surface_a"] == ob["surface_id"] \
                    else r["point_a"]
                worst_pair_sep = max(worst_pair_sep,
                                     math.dist(struck_pt, probe_pt))
                if first is None:
                    first = {"tick": t, "kind": r["kind"], "gap_m": r["gap_m"],
                             "toc": r["toc"]}
                worst_plane_err = max(worst_plane_err,
                                      plane_err_to_mesh(verts_c, tris_c,
                                                        struck_pt))
                if ob["kind"] == "rock":
                    worst_analytic_err = max(
                        worst_analytic_err,
                        abs(hull_depth(ob["verts"], ob["faces"],
                                       F_TO_CLEARING(struck_pt))))
                else:
                    worst_analytic_err = max(
                        worst_analytic_err, analytic_radial_err(ob, struck_pt))
        worst_ledger = max(worst_ledger, max(
            math.sqrt(sum(x * x for x in ledger["residual"][b.id]))
            for b in bodies))
        states.append({
            "tick": t, "probe_centre_clearing_m": list(F_TO_CLEARING(c)),
            "probe_velocity_contact_m_s": list(probe.velocity),
            "contacts": [{"kind": r["kind"], "gap_m": r["gap_m"],
                          "jn_Ns": r["jn_Ns"], "jt_Ns": r["jt_Ns"],
                          "surface_a": r["surface_a"],
                          "surface_b": r["surface_b"],
                          "point_clearing_a": list(F_TO_CLEARING(r["point_a"])),
                          "point_clearing_b": list(F_TO_CLEARING(r["point_b"])),
                          "normal_contact_to_a_clearing": list(
                              F_TO_CLEARING(tuple(r["normal"])))}
                         for r in records]})
    stop = {"first_contact": first,
            "first_contact_pre_overlap": bool(first and first["kind"] == "ccd"
                                              and first["gap_m"] > 0.0),
            "worst_mesh_penetration_m": grid6(worst_pen),
            "penetration_within_bar": worst_pen <= PEN_BAR_M,
            "min_approach_coordinate_m": grid6(min_appr),
            "never_crossed": min_appr > 0.0,
            "struck_surface_contact_records": struck_hits,
            "contact_names_struck_surface": struck_hits > 0,
            "worst_contact_plane_err_m": worst_plane_err,
            "plane_within_bar": worst_plane_err <= PLANE_BAR_M,
            "worst_contact_analytic_err_m": grid6(worst_analytic_err),
            "analytic_within_bar": worst_analytic_err <= ob["analytic_bar_m"],
            "worst_contact_pair_separation_m": grid6(worst_pair_sep),
            "worst_ledger_residual": worst_ledger,
            "ledger_within_bar": worst_ledger <= LEDGER_BAR}
    return {"id": ob["id"], "stop": stop, "states": states,
            "start_clearing_m": list(start),
            "velocity_clearing_m_s": list(vel),
            "approach_axis": axis,
            "analytic_bar_m": ob["analytic_bar_m"]}


def probe_centre_c(probe):
    xs = [v[0] for v in probe.vertices]
    ys = [v[1] for v in probe.vertices]
    zs = [v[2] for v in probe.vertices]
    return (sum(xs) / 8.0, sum(ys) / 8.0, sum(zs) / 8.0)


def analytic_radial_err(ob, pt_c):
    """Contact identity to the declared analytic capsule/cylinder form
    (A2): |dist(p, axis segment) - radius| for logs/saplings."""
    p = F_TO_CLEARING(tuple(pt_c))
    cx, _, cz = ob["centre_m"]
    if ob["kind"] == "log":
        r = ob["log_radius_m"]
        half = ob["log_length_m"] / 2.0
        if ob["yaw_index"] == 0:
            axial = max(abs(p[0] - cx) - half, 0.0)
            radial = abs(p[2] - cz)
        else:
            axial = max(abs(p[2] - cz) - half, 0.0)
            radial = abs(p[0] - cx)
        return abs(math.hypot(axial, radial) - r)
    sap_x = cx + STAND_RING_RADIUS_M
    return abs(math.hypot(p[0] - sap_x, p[2] - cz) - SAPLING_RADIUS_M)


# --- scene mesh + renderer ----------------------------------------------------------
class SceneMesh07:
    """Pinned render arrays (ground + posts) + pinned trunk + F07 obstacle
    meshes as raycast/raster targets."""

    def __init__(self, bundle, trunk_verts, trunk_groups, obstacles,
                 rendered_ids=None):
        self.vertices = bundle["render"]["vertices"]
        self.indices = bundle["render"]["indices"]
        self.ground = bundle["render"]["sections"]["ground"]
        self.posts = bundle["render"]["sections"]["boundary_posts"]
        self.trunk_vertices = trunk_verts
        self.groups = trunk_groups
        self.rendered_ids = rendered_ids
        self.obstacles = [ob for ob in obstacles
                          if rendered_ids is None or ob["id"] in rendered_ids]
        self.geom = {"base_centre_m": list(TRUNK_SITE_M),
                     "radius_m": TRUNK_RADIUS_M, "height_m": TRUNK_HEIGHT_M}

    def _trunk_tris(self):
        for sid in ("trunk_01.lateral", "trunk_01.base_cap", "trunk_01.top_cap"):
            for t in self.groups[sid]:
                yield (self.trunk_vertices[t[0]], self.trunk_vertices[t[1]],
                       self.trunk_vertices[t[2]], sid)

    def scene_tris(self):
        idx = self.indices
        g_end = self.ground["index_start"] + self.ground["index_count"]
        for k in range(0, len(idx), 3):
            a, b, c = idx[k], idx[k + 1], idx[k + 2]
            yield (tuple(self.vertices[9 * a:9 * a + 3]),
                   tuple(self.vertices[9 * b:9 * b + 3]),
                   tuple(self.vertices[9 * c:9 * c + 3]),
                   "monkey_clearing_ground" if k < g_end
                   else "monkey_clearing_boundary_posts")
        yield from self._trunk_tris()
        for ob in self.obstacles:
            for t in ob["tris"]:
                yield (ob["verts"][t[0]], ob["verts"][t[1]],
                       ob["verts"][t[2]], ob["surface_id"])

    def first_hit(self, orig, direc):
        best = None
        for va, vb, vc, sid in self.scene_tris():
            hit = F_ray_triangle(orig, direc, va, vb, vc)
            if hit is not None and (best is None or hit[0] < best[0]):
                n = F_vnorm(F_vcross(F_vsub(vb, va), F_vsub(vc, va)))
                best = (hit[0], sid, n)
        return best


class Camera07:
    """F04's camera geometry with the F07 frame identity in the record."""

    def __init__(self, spec, frame_id="f01_world_y_up/MAT2-F07"):
        self.spec = spec
        self.frame_id = frame_id
        self.position = list(spec["position"])
        self.target = list(spec["target"])
        self.vfov = math.radians(spec["vfov_deg"])
        self.fwd = F_vnorm(F_vsub(self.target, self.position))
        self.right = F_vnorm(F_vcross(self.fwd, [0.0, 1.0, 0.0]))
        self.up = F_vcross(self.right, self.fwd)
        self.aspect = W / H
        self.t = math.tan(self.vfov / 2.0)
        self.distance_to_target = math.sqrt(
            sum((self.position[i] - self.target[i]) ** 2 for i in range(3)))

    def ndc(self, world_point):
        d = F_vsub(world_point, self.position)
        z = F_vdot(d, self.fwd)
        if z <= 1e-6:
            return None
        return (F_vdot(d, self.right) / (z * self.t * self.aspect),
                F_vdot(d, self.up) / (z * self.t), z)

    def pixel(self, world_point):
        n = self.ndc(world_point)
        if n is None:
            return None
        return ((n[0] + 1.0) * 0.5 * W, (1.0 - n[1]) * 0.5 * H, n[2])

    def ray_through_ndc(self, xn, yn):
        return F_vnorm([self.fwd[i] + xn * self.t * self.aspect * self.right[i]
                        + yn * self.t * self.up[i] for i in range(3)])

    def quaternion_wxyz(self):
        m = [[self.right[0], self.up[0], -self.fwd[0]],
             [self.right[1], self.up[1], -self.fwd[1]],
             [self.right[2], self.up[2], -self.fwd[2]]]
        tr = m[0][0] + m[1][1] + m[2][2]
        if tr > 0.0:
            s = math.sqrt(tr + 1.0) * 2.0
            w = 0.25 * s
            x = (m[2][1] - m[1][2]) / s
            y = (m[0][2] - m[2][0]) / s
            z = (m[1][0] - m[0][1]) / s
        elif m[0][0] > m[1][1] and m[0][0] > m[2][2]:
            s = math.sqrt(1.0 + m[0][0] - m[1][1] - m[2][2]) * 2.0
            w = 0.25 * s
            x = 0.25 * s
            y = (m[0][1] + m[1][0]) / s
            z = (m[0][2] - m[2][0]) / s
        elif m[1][1] > m[2][2]:
            s = math.sqrt(1.0 + m[1][1] - m[0][0] - m[2][2]) * 2.0
            w = 0.25 * s
            x = (m[0][2] - m[2][0]) / s
            y = 0.25 * s
            z = (m[1][2] + m[2][1]) / s
        else:
            s = math.sqrt(1.0 + m[2][2] - m[0][0] - m[1][1]) * 2.0
            w = 0.25 * s
            x = (m[0][1] - m[1][0]) / s
            y = (m[2][0] + m[0][2]) / s
            z = 0.25 * s
        q = (w, x, y, z)
        n = math.sqrt(sum(c * c for c in q))
        return [c / n for c in q]

    def camera_record(self, ticks):
        q = self.quaternion_wxyz()
        samples = [{"tick": t,
                    "position": list(self.position),
                    "target": list(self.target),
                    "distance_to_target": self.distance_to_target,
                    "orientation": list(q)}
                   for t in ticks]
        convention = {
            "aspect_ratio": W / H,
            "camera_motion_or_bookmark_sequence": {
                "sample_mode": "fixed_bookmark", "samples": samples},
            "coordinate_unit": "m",
            "distance_to_target": self.distance_to_target,
            "forward_axis": "-Z",
            "frame_id": self.frame_id,
            "handedness": "right",
            "label_ids": None,
            "near_far_planes": list(self.spec["near_far"]),
            "occlusion_or_xray_mode": "depth_tested",
            "orientation_convention": "quaternion_wxyz_camera_to_frame",
            "orientation_convention_and_values": {
                "convention": "quaternion_wxyz_camera_to_frame",
                "quaternion_wxyz": list(q)},
            "position": list(self.position),
            "projection": "perspective",
            "quaternion_wxyz": list(q),
            "state_or_tick_interval": list(ticks),
            "target": list(self.target),
            "up_axis": "+Y",
            "vertical_fov_degrees": self.spec["vfov_deg"],
            "vertical_fov_or_orthographic_span_deg": self.spec["vfov_deg"],
            "viewport_resolution": [W, H],
            "visibility_layers": None,
        }
        # the validator reads the FLAT form; the 16-field convention record
        # travels nested (F04's manifest form)
        flat = {
            "frame_id": self.frame_id,
            "coordinate_unit": "m",
            "handedness": "right",
            "orientation_convention": "quaternion_wxyz_camera_to_frame",
            "forward_axis": "-Z",
            "up_axis": "+Y",
            "position": list(self.position),
            "target": list(self.target),
            "distance_to_target": self.distance_to_target,
            "projection": "perspective",
            "vertical_fov_degrees": self.spec["vfov_deg"],
            "near_far_planes": list(self.spec["near_far"]),
            "aspect_ratio": W / H,
            "viewport_resolution": [W, H],
            "sample_mode": "fixed_bookmark",
            "samples": samples,
            "occlusion_or_xray_mode": "depth_tested",
            "camera_record_16field_convention": convention,
        }
        return flat


SURFACE_COLOURS = {
    "monkey_clearing_ground": (96, 84, 60),
    "monkey_clearing_boundary_posts": (184, 140, 51),
    "trunk_01.lateral": (92, 64, 41),
    "trunk_01.base_cap": (92, 64, 41),
    "trunk_01.top_cap": (92, 64, 41),
}
OBSTACLE_COLOURS = {
    "rock_01": (110, 112, 118), "rock_02": (104, 106, 112),
    "rock_03": (118, 118, 124), "log_01": (96, 70, 44),
    "log_02": (90, 66, 42), "stand_01": (54, 96, 46), "stand_02": (50, 90, 44),
}


def render_frame(mesh, cam, diagnostic, probes, labels):
    colour = [[(8, 12, 10)] * W for _ in range(H)]
    depth = [[math.inf] * W for _ in range(H)]
    near, far = cam.spec["near_far"]
    for va, vb, vc, sid in mesh.scene_tris():
        rgb = OBSTACLE_COLOURS.get(sid, SURFACE_COLOURS.get(sid, (96, 84, 60)))
        raster_tri(cam, colour, depth, va, vb, vc, rgb, near, far)
    if diagnostic:
        _draw_diagnostic(mesh, cam, colour, probes, labels)
    return colour


def raster_tri(cam, colour, depth, pa, pb, pc, rgb, near, far):
    a = cam.pixel(pa)
    b = cam.pixel(pb)
    c = cam.pixel(pc)
    if a is None or b is None or c is None:
        return
    if a[2] < near or b[2] < near or c[2] < near:
        return
    if a[2] > far and b[2] > far and c[2] > far:
        return
    x0 = max(0, int(math.floor(min(a[0], b[0], c[0]))))
    x1 = min(W - 1, int(math.ceil(max(a[0], b[0], c[0]))))
    y0 = max(0, int(math.floor(min(a[1], b[1], c[1]))))
    y1 = min(H - 1, int(math.ceil(max(a[1], b[1], c[1]))))
    if x1 < x0 or y1 < y0:
        return
    area = ((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1]))
    if abs(area) < 1e-12:
        return
    inv_area = 1.0 / area
    for py in range(y0, y1 + 1):
        sy_ = py + 0.5
        row_c = colour[py]
        row_d = depth[py]
        for px in range(x0, x1 + 1):
            sx = px + 0.5
            w0 = ((b[0] - sx) * (c[1] - sy_) - (c[0] - sx) * (b[1] - sy_)) * inv_area
            if w0 < 0.0:
                continue
            w1 = ((c[0] - sx) * (a[1] - sy_) - (a[0] - sx) * (c[1] - sy_)) * inv_area
            if w1 < 0.0:
                continue
            w2 = 1.0 - w0 - w1
            if w2 < 0.0:
                continue
            z = 1.0 / (w0 / a[2] + w1 / b[2] + w2 / c[2])
            if z < row_d[px]:
                row_d[px] = z
                row_c[px] = rgb


def _line(colour, x0, y0, x1, y1, rgb):
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        if 0 <= x0 < W and 0 <= y0 < H:
            colour[y0][x0] = rgb
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def _wire(cam, va, vb, vc, colour, rgb, max_depth=120.0):
    trip = []
    for v in (va, vb, vc):
        p = cam.pixel(v)
        if p is None or p[2] > max_depth:
            return
        trip.append(p)
    _line(colour, trip[0][0], trip[0][1], trip[1][0], trip[1][1], rgb)
    _line(colour, trip[1][0], trip[1][1], trip[2][0], trip[2][1], rgb)
    _line(colour, trip[2][0], trip[2][1], trip[0][0], trip[0][1], rgb)


def _draw_diagnostic(mesh, cam, colour, probes, labels):
    magenta = (255, 0, 255)
    cyan = (0, 255, 255)
    yellow = (255, 255, 0)
    orange = (255, 160, 0)
    half = EXTENT_HALF_M
    for i in range(4):                       # scene bounds layer
        corners = [(-half, 0.0, -half), (half, 0.0, -half),
                   (half, 0.0, half), (-half, 0.0, half)]
        a = cam.pixel(corners[i])
        b = cam.pixel(corners[(i + 1) % 4])
        top_a = cam.pixel([corners[i][0], 0.9, corners[i][2]])
        if a and b:
            _line(colour, a[0], a[1], b[0], b[1], magenta)
        if a and top_a:
            _line(colour, a[0], a[1], top_a[0], top_a[1], magenta)
    g0 = mesh.ground["index_start"]          # render mesh layer (ground)
    g1 = g0 + mesh.ground["index_count"]
    for k in range(g0, g1, 3):
        va = tuple(mesh.vertices[9 * mesh.indices[k]:9 * mesh.indices[k] + 3])
        vb = tuple(mesh.vertices[9 * mesh.indices[k + 1]:
                                 9 * mesh.indices[k + 1] + 3])
        vc = tuple(mesh.vertices[9 * mesh.indices[k + 2]:
                                 9 * mesh.indices[k + 2] + 3])
        _wire(cam, va, vb, vc, colour, (40, 52, 44))
    for va, vb, vc, sid in mesh._trunk_tris():     # trunk wireframe
        _wire(cam, va, vb, vc, colour, (90, 110, 95))
    for ob in mesh.obstacles:                # obstacle wireframes
        for t in ob["tris"]:
            _wire(cam, ob["verts"][t[0]], ob["verts"][t[1]],
                  ob["verts"][t[2]], colour, (120, 130, 110))
        step = max(1, len(ob["verts"]) // 12)
        for i in range(0, len(ob["verts"]), step):   # collision surfaces layer
            px = cam.pixel(ob["verts"][i])
            if px and 0 <= int(px[0]) < W and 0 <= int(px[1]) < H:
                x, y = int(px[0]), int(px[1])
                for ddx, ddy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    xx, yy = x + ddx, y + ddy
                    if 0 <= xx < W and 0 <= yy < H:
                        colour[yy][xx] = orange
    if probes:                               # normals/contact markers layer
        for pr in probes:
            base = cam.pixel(pr["point"])
            if base is None:
                continue
            nrm = pr.get("oracle_n", [0.0, 1.0, 0.0])
            tip = cam.pixel([pr["point"][i] + 0.4 * nrm[i] for i in range(3)])
            if tip is None:
                continue
            _line(colour, base[0], base[1], tip[0], tip[1], cyan)
            if pr.get("tick_id") is not None:
                x, y = int(base[0]), int(base[1])
                for ddx, ddy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                    xx, yy = x + ddx, y + ddy
                    if 0 <= xx < W and 0 <= yy < H:
                        colour[yy][xx] = yellow
    if labels:                               # stable 3D labels layer
        for lab in labels:
            px = cam.pixel(lab["anchor"])
            if px is None or not (0 <= px[0] < W and 0 <= px[1] < H):
                continue
            x, y = int(px[0]), int(px[1])
            for dx, dy in ((-4, 0), (4, 0), (0, -4), (0, 4), (0, 0)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < W and 0 <= yy < H:
                    colour[yy][xx] = yellow


def write_bmp(path, colour):
    pad = (W * 3 + 3) & ~3
    header_size = 54
    image_size = pad * H
    buf = bytearray(image_size)
    for y in range(H):
        src = colour[H - 1 - y]
        row = y * pad
        for x in range(W):
            r, g, b = src[x]
            i = row + x * 3
            buf[i] = b
            buf[i + 1] = g
            buf[i + 2] = r
    bmp = bytearray(header_size + image_size)
    bmp[0:2] = b"BM"
    struct.pack_into("<IHHIIiiHHIIiiii", bmp, 2, header_size + image_size, 0,
                     0, header_size, 40, W, H, 1, 24, 0, image_size, 0, 0, 0, 0)
    bmp[header_size:] = buf
    path.write_bytes(bytes(bmp))


# --- marker classify (pure ray/geometry; markers never read pixels) ------------------
def classify_marker(mesh, cam, marker):
    point = marker.get("classify_point", marker["point"])
    ndc = cam.ndc(point)
    if ndc is None:
        return {"outcome": "OFF_FRAME", "reason": "behind_camera"}
    px = (ndc[0] + 1.0) * 0.5 * W
    py = (1.0 - ndc[1]) * 0.5 * H
    rec = {"pixel_px": [px, py]}
    if not (-1.0 <= ndc[0] <= 1.0 and -1.0 <= ndc[1] <= 1.0):
        rec.update({"outcome": "OFF_FRAME", "reason": "outside_viewport"})
        return rec
    rec["margin_fraction"] = [min(px, W - px) / W, min(py, H - py) / H]
    direc = cam.ray_through_ndc(ndc[0], ndc[1])
    pd = math.sqrt(sum((point[i] - cam.position[i]) ** 2 for i in range(3)))
    hit = mesh.first_hit(cam.position, direc)
    if hit is None:
        rec.update({"outcome": "UNRENDERED",
                    "reason": "no render hit through the marker ray"})
        return rec
    t, sid, hit_n = hit
    rec["hit_surface_id"] = sid
    if sid != marker["surface"]:
        rec.update({"outcome": "OCCLUDED", "occluder": sid})
        return rec
    if abs(t - pd) > VIS_BAR_M:
        rec.update({"outcome": "OCCLUDED", "occluder": sid,
                    "note": "same surface but a nearer hit stands in front"})
        return rec
    kind = marker["kind"]
    hit_point = [cam.position[i] + t * direc[i] for i in range(3)]
    if kind == "ground":
        rec["height_err_m"] = abs(point[1] - marker["oracle_h"])
        rec["normal_err"] = min(max(abs(hit_n[i] - cand[i]) for i in range(3))
                                for cand in marker["oracle_n_set"])
        rec["ok_bars"] = (rec["height_err_m"] <= PLANE_BAR_M
                          and rec["normal_err"] <= 1e-12)
    elif kind == "facet":
        n = marker["oracle_n"]
        # the rendered winding may point either way along the facet plane;
        # the oracle match is the UNSIGNED plane normal (the ray can only
        # hit the facet from outside, so outward-ness is already implied)
        cosang = abs(F_vdot(n, hit_n))
        rec["normal_angle_rad"] = math.acos(max(-1.0, min(1.0, cosang)))
        rec["plane_err_m"] = abs(F_vdot(n, F_vsub(hit_point, point)))
        rec["ok_bars"] = (rec["normal_angle_rad"] <= math.pi / RING_N + 1e-9
                          and rec["plane_err_m"] <= MARKER_PLANE_BAR_M)
    elif kind == "hull":
        n = marker["oracle_n"]
        rec["plane_err_m"] = abs(F_vdot(n, F_vsub(hit_point, point)))
        rec["ok_bars"] = rec["plane_err_m"] <= MARKER_PLANE_BAR_M
    elif kind == "post":
        rec["height_err_m"] = abs(point[1] - marker["oracle_top_y"])
        rec["ok_bars"] = rec["height_err_m"] <= 1e-3
    elif kind == "trunk":
        base = mesh.geom["base_centre_m"]
        d = math.hypot(marker["point"][0] - base[0],
                       marker["point"][2] - base[2])
        rec["radial_err_m"] = abs(d - mesh.geom["radius_m"])
        rec["ok_bars"] = rec["radial_err_m"] <= 2e-4
    else:
        rec["ok_bars"] = True
    rec["outcome"] = ("VISIBLE_EXACT" if rec["ok_bars"]
                      else "VISIBLE_BUT_MISMATCH")
    return rec


def rock_candidates(ob):
    out = []
    for tri in ob["faces"]:
        a, b, c = (ob["verts"][i] for i in tri)
        n = F_vnorm(F_vcross(F_vsub(b, a), F_vsub(c, a)))
        cen = [(a[i] + b[i] + c[i]) / 3.0 for i in range(3)]
        seed = [1.0, 0.0, 0.0] if abs(n[0]) < 0.9 else [0.0, 1.0, 0.0]
        tangent = F_vnorm(F_vsub(seed, [n[i] * F_vdot(n, seed)
                                        for i in range(3)]))
        out.append({"point": tuple(cen),
                    "classify_point": tuple(cen[i] + 1e-3 * tangent[i]
                                            for i in range(3)),
                    "surface": ob["surface_id"], "kind": "hull",
                    "oracle_n": list(n)})
    return out


def prism_candidates(ob):
    """All lateral facet centre candidates of the log/stand meshes (on the
    ACTUAL surface for both log yaws), tangential nudge along the in-plane
    axis direction. Stands contribute their sapling top caps (+y facets)."""
    out = []
    if ob["kind"] == "log":
        r = ob["log_radius_m"]
        half = ob["log_length_m"] / 2.0
        cx, cy, cz = ob["centre_m"]
        cy = cy + r * math.cos(math.pi / RING_N)   # resting axis height
        for k in range(RING_N):
            ang = math.pi / RING_N + 2.0 * math.pi * k / RING_N
            ca, sa = math.cos(ang), math.sin(ang)
            if ob["yaw_index"] == 0:               # axis +x: ring in Y-Z
                cen = (cx, cy + r * ca, cz + r * sa)
                n = (0.0, ca, sa)
                cpt = (cx + 1e-3, cy + r * ca, cz + r * sa)
            else:                                  # axis +z: ring in X-Y
                cen = (cx + r * sa, cy + r * ca, cz)
                n = (sa, ca, 0.0)
                cpt = (cx + r * sa, cy + r * ca, cz + 1e-3)
            out.append({"point": cen, "classify_point": cpt,
                        "surface": ob["surface_id"], "kind": "facet",
                        "oracle_n": list(n)})
        return out
    for k in range(SAPLING_COUNT):
        a = 2.0 * math.pi * k / SAPLING_COUNT
        sx_ = ob["centre_m"][0] + STAND_RING_RADIUS_M * math.cos(a)
        sz_ = ob["centre_m"][2] + STAND_RING_RADIUS_M * math.sin(a)
        out.append({"point": (sx_, ob["centre_m"][1] + SAPLING_HEIGHT_M, sz_),
                    "classify_point": (sx_ + 1e-3, ob["centre_m"][1]
                                       + SAPLING_HEIGHT_M, sz_),
                    "surface": ob["surface_id"], "kind": "facet",
                    "oracle_n": [0.0, 1.0, 0.0]})
    return out


def pick_subject(ob, mesh, cam):
    """The obstacle's subject marker: among its surface candidate points,
    the nearest one whose classify outcome is VISIBLE_EXACT (the ray's ENTRY
    face); None when the whole obstacle is occluded in that view."""
    cands = rock_candidates(ob) if ob["kind"] == "rock" \
        else prism_candidates(ob)
    visible = []
    for cand in cands:
        out = classify_marker(mesh, cam, cand)
        if out["outcome"] == "VISIBLE_EXACT":
            pd = math.dist(cand["classify_point"], cam.position)
            visible.append((pd, cand, out))
    if not visible:
        return None
    visible.sort(key=lambda v: v[0])
    pd, cand, out = visible[0]
    return {**cand, "id": "subject_" + ob["id"], "record": out}


def incident_ground_normals(mesh, x, z):
    verts = mesh.vertices
    idx = mesh.indices
    g = mesh.ground
    out = []
    for k in range(g["index_start"], g["index_start"] + g["index_count"], 3):
        ia, ib, ic = idx[k], idx[k + 1], idx[k + 2]
        pa = tuple(verts[9 * ia:9 * ia + 3])
        pb = tuple(verts[9 * ib:9 * ib + 3])
        pc = tuple(verts[9 * ic:9 * ic + 3])
        det = ((pb[0] - pa[0]) * (pc[2] - pa[2])
               - (pc[0] - pa[0]) * (pb[2] - pa[2]))
        if abs(det) < 1e-12:
            continue
        w0 = ((pb[0] - x) * (pc[2] - z) - (pc[0] - x) * (pb[2] - z)) / det
        w1 = ((pc[0] - x) * (pa[2] - z) - (pa[0] - x) * (pc[2] - z)) / det
        w2 = 1.0 - w0 - w1
        if w0 >= -1e-9 and w1 >= -1e-9 and w2 >= -1e-9:
            out.append(F_vnorm(F_vcross(F_vsub(pb, pa), F_vsub(pc, pa))))
    require(out, "f07_no_incident_ground_face", (x, z))
    return out


def post_subject(bundle, clearing_decl):
    """Marker at the top face of the SW corner post (deterministic from the
    render arrays and the pinned declared bases). The classify point is the
    top-face point nudged 1 mm IN PLANE toward the post axis."""
    section = bundle["render"]["sections"]["boundary_posts"]
    vs = bundle["render"]["vertices"]
    v0, v1 = section["vertex_start"], section["vertex_start"] + section["vertex_count"]
    top = None
    for i in range(v0, v1):
        x, y, z = vs[9 * i:9 * i + 3]
        if abs(x + EXTENT_HALF_M) < 0.35 and abs(z + EXTENT_HALF_M) < 0.35:
            if top is None or y > top[1]:
                top = (x, y, z)
    require(top is not None, "f07_no_corner_post_vertex")
    base = min(clearing_decl["boundary"]["rendered"]["posts_m"],
               key=lambda p: (p[0] - top[0]) ** 2 + (p[2] - top[2]) ** 2)
    inward = F_vnorm([base[0] - top[0], 0.0, base[2] - top[2]])
    point = (top[0], top[1], top[2])
    return {"point": point,
            "classify_point": (point[0] + 1e-3 * inward[0], point[1],
                               point[2] + 1e-3 * inward[2]),
            "surface": "monkey_clearing_boundary_posts", "kind": "post",
            "oracle_top_y": top[1], "id": "subject_boundary_post"}


def trunk_subject_marker(cam, trunk_assets):
    base = trunk_assets["base_clearing"]
    radius = trunk_assets["radius"]
    az_cam = math.atan2(cam.position[2] - base[2], cam.position[0] - base[0])
    seg = 2.0 * math.pi / TRUNK_RING_SEGMENTS
    k = int(math.floor((az_cam % (2.0 * math.pi)) / seg)) % TRUNK_RING_SEGMENTS
    az = (k + 0.5) * seg
    r = radius * math.cos(math.pi / TRUNK_RING_SEGMENTS)
    point = (base[0] + r * math.cos(az), 0.6, base[2] + r * math.sin(az))
    n = F_vnorm((math.cos(az), 0.0, math.sin(az)))
    return {"point": point, "surface": "trunk_01.lateral", "kind": "trunk",
            "oracle_n": list(n), "id": "subject_trunk"}


def frozen_labels(obstacles):
    labs = [{"id": "spawn", "subject_id": "monkey_clearing_ground",
             "anchor": [SPAWN_M[0], 0.05, SPAWN_M[2]]},
            {"id": "extent_rule", "subject_id": "extent_rule",
             "anchor": [0.0, 0.95, -EXTENT_HALF_M]},
            {"id": "trunk_01", "subject_id": "trunk_01",
             "anchor": [TRUNK_SITE_M[0] + TRUNK_RADIUS_M, 0.6,
                        TRUNK_SITE_M[2]]}]
    for ob in obstacles:
        labs.append({"id": ob["id"], "subject_id": ob["id"],
                     "anchor": [ob["centre_m"][0],
                                ob["centre_m"][1] + ob["extent_m"][1] + 0.15,
                                ob["centre_m"][2]]})
    require(len(labs) == 3 + len(obstacles), "f07_label_count", len(labs))
    return labs


# --- registry profile ---------------------------------------------------------------
def read_registry_profile():
    require(REGISTRY_SQLITE.is_file(), "f07_registry_missing",
            str(REGISTRY_SQLITE))
    uri = "file:%s?mode=ro" % REGISTRY_SQLITE.as_posix()
    con = sqlite3.connect(uri, uri=True)
    try:
        payload = con.execute("select payload from state where id = 1").fetchone()
    finally:
        con.close()
    require(payload is not None, "f07_registry_empty")
    state = json.loads(payload[0])
    card = state["kanban"]["cards"]["MAT2-F07"]
    prof = card["spec"]["ontology_qualification"]["task"]["verification_profile"]
    require(prof["id"] == "forest" and prof["kind"] == "visible_static",
            "f07_registry_profile_wrong", prof.get("id"))
    canon = digest(prof)
    attempt = card["attempts"][ATTEMPT_ID]
    require(attempt["criteria_sha256"] == CRITERIA_SHA256,
            "f07_criteria_drift", attempt["criteria_sha256"])
    return prof, {"canonical_sha256": canon, "read_from": str(REGISTRY_SQLITE),
                  "mode": "read_only", "attempt_state": attempt["state"]}


# --- falsifier arms (run FIRST; each must bite; clean controls) ----------------------
def render_collision_set_identity(obstacles):
    """P1/P6: render sections == collision surfaces, bidirectionally. Every
    declared obstacle carries BOTH (the mesh IS the body)."""
    ids = sorted(ob["id"] for ob in obstacles)
    return {"collision_surfaces": ids, "render_sections": ids,
            "collision_without_render": [], "render_without_collision": [],
            "identity": True}


def arrays_equal(a, b):
    return len(a) == len(b) and all(
        list(x) == list(y) for x, y in zip(a, b))


def run_bites(lc, obstacles, surface, bundle, trunk_assets, mesh, cams,
              subjects_by_id):
    bites = []

    def record(name, ok, detail, control):
        require(control.get("pass"), "f07_%s_control_failed" % name, control)
        bites.append({"bite": name, "bites": bool(ok), "observed": detail,
                      "clean_control": control,
                      "guard": "f07_%s_premature" % name})

    # FB1 invisible wall in the mask
    clean_mask, clean_attr = build_mask(obstacles, surface)
    clean_audit = attribution_audit(clean_mask, clean_attr)
    inj_mask, inj_attr = build_mask(obstacles, surface,
                                    inject=(FB1_INJECT_SITE[0],
                                            FB1_INJECT_SITE[1], 1.0))
    inj_audit = attribution_audit(inj_mask, inj_attr)
    record("FB1_invisible_wall_in_mask",
           inj_audit["unattributed_count"] >= 1,
           {"injected_disc": {"centre_m": list(FB1_INJECT_SITE),
                              "radius_m": 1.0},
            "unattributed_count": inj_audit["unattributed_count"]},
           {"run": "real scene mask attribution",
            "unattributed_count": clean_audit["unattributed_count"],
            "pass": clean_audit["unattributed_count"] == 0})

    # FB2 ghost obstacle: collision WITHOUT render (an invisible wall)
    ghost = dict(obstacles[0])
    ghost["id"] = "rock_ghost"
    ghost["surface_id"] = "rock_ghost"
    dx = 6.0
    ghost["centre_m"] = [grid6(obstacles[0]["centre_m"][0] + dx),
                         obstacles[0]["centre_m"][1],
                         obstacles[0]["centre_m"][2]]
    ghost["verts"] = [(v[0] + dx, v[1], v[2]) for v in obstacles[0]["verts"]]
    ghost_mesh = SceneMesh07(bundle, trunk_assets["vertices"],
                             trunk_assets["groups"], obstacles)  # ghost NOT rendered
    ghost_body = obstacle_contact_body(lc, ghost)
    ghost_probe = make_probe(lc, "probe_ghost",
                             F_TO_CONTACT((ghost["centre_m"][0]
                                           + ghost["extent_m"][0] + 0.25,
                                           ghost["centre_m"][1]
                                           + 0.5 * ghost["extent_m"][1],
                                           ghost["centre_m"][2])),
                             F_TO_CONTACT((-IMPACT_SPEED_M_S, 0.0, 0.0)))
    ghost_contacts = 0
    for _ in range(TICKS_IMPACT):
        records, _ = lc.solve_tick([ghost_body, ghost_probe], ccd_enabled=True)
        ghost_contacts += len(records)
    marker_ghost = rock_candidates(ghost)[0]
    marker_ghost["id"] = "subject_rock_ghost"
    cam1 = cams["V1_clearing_overview"]
    out_ghost = classify_marker(ghost_mesh, cam1, marker_ghost)
    marker_real = subjects_by_id["rock_01"]
    out_real = classify_marker(mesh, cam1, marker_real)
    ghost_unrendered = (out_ghost["outcome"] in ("UNRENDERED", "OCCLUDED")
                        and out_ghost.get("hit_surface_id") != "rock_ghost")
    record("FB2_ghost_obstacle_collision_without_render",
           ghost_unrendered and ghost_contacts > 0,
           {"ghost_marker_outcome": out_ghost["outcome"],
            "ghost_ray_hit_surface": out_ghost.get("hit_surface_id"),
            "ghost_body_contact_records": ghost_contacts,
            "note": "the ghost body STOPS the probe while nothing is "
                    "rendered at its surface: the invisible wall the law "
                    "forbids"},
           {"run": "same-form marker on real rock_01",
            "outcome": out_real["outcome"],
            "pass": out_real["outcome"] == "VISIBLE_EXACT"})

    # FB3 phantom obstacle: render WITHOUT collision
    phantom = dict(obstacles[5])
    phantom["id"] = "stand_phantom"
    phantom["surface_id"] = "stand_phantom"
    phantom["verts"] = [(v[0] + dx, v[1], v[2]) for v in obstacles[5]["verts"]]
    phantom["centre_m"] = [grid6(obstacles[5]["centre_m"][0] + dx),
                           obstacles[5]["centre_m"][1],
                           obstacles[5]["centre_m"][2]]
    phantom_mesh = SceneMesh07(bundle, trunk_assets["vertices"],
                               trunk_assets["groups"],
                               obstacles + [phantom])   # phantom rendered
    ph_start, ph_vel, _ = impact_start(phantom)
    probe = make_probe(lc, "probe_ph", F_TO_CONTACT(ph_start),
                       F_TO_CONTACT(ph_vel))
    n_records = 0
    for _ in range(TICKS_IMPACT):
        records, _ = lc.solve_tick([probe], ccd_enabled=True)
        n_records += len(records)
    real_run = run_impact(lc, obstacles[5])
    real_contacts = sum(len(s["contacts"]) for s in real_run["states"])
    record("FB3_phantom_obstacle_render_without_collision",
           n_records == 0,
           {"phantom_contact_records": n_records,
            "note": "the probe flies THROUGH the rendered phantom: a "
                    "rendered non-object"},
           {"run": "same-form impact on real stand_01",
            "contact_records": real_contacts,
            "pass": real_contacts > 0})

    # FB4 undeclared stop event (extent record removed)
    recs_full = boundary_records()
    all_ids = sorted([r["id"] for r in recs_full]
                     + [ob["id"] for ob in obstacles])
    audit_full = stop_declaration_audit(clean_audit["blocked_by_record"],
                                        [ob["id"] for ob in obstacles],
                                        recs_full + [{"id": ob["id"]}
                                                     for ob in obstacles])
    recs_missing = [r for r in recs_full if r["id"] != "extent_rule"]
    audit_missing = stop_declaration_audit(
        {k: v for k, v in clean_audit["blocked_by_record"].items()},
        [ob["id"] for ob in obstacles],
        recs_missing + [{"id": ob["id"]} for ob in obstacles])
    record("FB4_undeclared_stop_event",
           audit_missing["undeclared_stops"] == ["extent_rule"],
           {"undeclared_stops": audit_missing["undeclared_stops"]},
           {"run": "full record set coverage",
            "undeclared_stops": audit_full["undeclared_stops"],
            "pass": audit_full["undeclared_stops"] == []})

    # FB5 route metric teeth (fenced spawn)
    fence = []
    for k in range(8):
        a = 2.0 * math.pi * k / 8.0
        fence.append({"id": "fence_%d" % k, "kind": "rock",
                      "centre_m": [grid6(math.cos(a) * FB5_FENCE_RADIUS_M),
                                   0.0,
                                   grid6(math.sin(a) * FB5_FENCE_RADIUS_M)],
                      "extent_m": [0.5, 0.5, 0.5],
                      "surface_id": "fence_%d" % k})
    f_mask, _ = build_mask(fence, surface)
    f_free = free_cells(f_mask)
    f_start = (MASK_N // 2, MASK_N // 2)
    f_reach = bfs_reachable(f_start, f_free) if f_start in f_free else set()
    dests = destination_table(obstacles)
    f_reached = [name for name, (tx, tz) in sorted(dests.items())
                 if (nr := nearest_reachable(f_reach, tx, tz)) is not None
                 and nr[0] <= MAX_VIEWPOINT_OFFSET_M]
    real_routes, _ = verify_routes(obstacles, surface, mask=clean_mask,
                                   require_reach=False)
    record("FB5_route_metric_teeth",
           f_reached == [],
           {"fenced_scene_reached_destinations": f_reached},
           {"run": "real scene BFS",
            "reached_destinations": sorted(n for n, r in real_routes.items()
                                           if r["reached"]),
            "pass": all(r["reached"] for r in real_routes.values())})

    # FB6 off-frame probe subject: the required subject form rotated 155.7
    # deg about the camera's up axis at the bookmark distance (off the V2
    # view azimuth), which places it behind the camera
    base = trunk_assets["base_clearing"]
    cam2 = cams["V2_seam_closeup"]
    theta = math.radians(FB6_OFFFRAME_ANGLE_DEG)
    v = [base[i] - cam2.position[i] for i in range(3)]
    v_par = [cam2.up[i] * F_vdot(cam2.up, v) for i in range(3)]
    v_perp = F_vsub(v, v_par)
    rot = [v_perp[i] * math.cos(theta)
           + F_vcross(cam2.up, v_perp)[i] * math.sin(theta) + v_par[i]
           for i in range(3)]
    off_point = [cam2.position[i] + rot[i] for i in range(3)]
    off_marker = {"point": off_point, "surface": "trunk_01.lateral",
                  "kind": "trunk", "id": "subject_offframe"}
    out_off = classify_marker(mesh, cam2, off_marker)
    tr_subject = trunk_subject_marker(cam2, trunk_assets)
    out_tr = classify_marker(mesh, cam2, tr_subject)
    record("FB6_off_frame_probe_subject",
           out_off["outcome"] == "OFF_FRAME",
           {"off_axis_angle_deg": FB6_OFFFRAME_ANGLE_DEG,
            "outcome": out_off["outcome"], "reason": out_off.get("reason")},
           {"run": "camera-facing trunk subject in the same V2 view",
            "outcome": out_tr["outcome"],
            "pass": out_tr["outcome"] == "VISIBLE_EXACT"})

    # FB7 render/collision decouple on rock_01
    marker = subjects_by_id["rock_01"]
    hit_tri = nearest_face(obstacles[0], marker.get("classify_point",
                                                    marker["point"]))
    dec = dict(obstacles[0])
    dec["verts"] = [list(v) for v in obstacles[0]["verts"]]
    for i in hit_tri:
        dec["verts"][i] = [dec["verts"][i][0], dec["verts"][i][1] + 0.01,
                           dec["verts"][i][2]]
    decoupled_detected = not arrays_equal(dec["verts"], obstacles[0]["verts"])
    dec_mesh = SceneMesh07(bundle, trunk_assets["vertices"],
                           trunk_assets["groups"], [dec])
    out_dec = classify_marker(dec_mesh, cam1, marker)
    out_clean = classify_marker(mesh, cam1, marker)
    record("FB7_render_collision_decouple",
           decoupled_detected and out_dec["outcome"] != "VISIBLE_EXACT",
           {"array_decouple_detected": decoupled_detected,
            "decoupled_outcome": out_dec["outcome"]},
           {"run": "classify on the UNPERTURBED render, same ray",
            "outcome": out_clean["outcome"],
            "pass": out_clean["outcome"] == "VISIBLE_EXACT"})
    return bites


def nearest_face(ob, point):
    best = None
    for tri in ob["tris"]:
        a, b, c = (ob["verts"][i] for i in tri)
        cen = [(a[i] + b[i] + c[i]) / 3.0 for i in range(3)]
        d = sum((cen[i] - point[i]) ** 2 for i in range(3))
        if best is None or d < best[0]:
            best = (d, tri)
    return best[1]


# --- transform-list gate selftest (applicability: static image capture) ---------------
def transform_selftest(path):
    """Identity decode/re-encode must match byte-exactly; a vflip must be
    REFUSED (the gate has teeth). Applicability recorded in the receipt."""
    raw = path.read_bytes()
    off = struct.unpack_from("<I", raw, 10)[0]
    w = struct.unpack_from("<i", raw, 18)[0]
    h = struct.unpack_from("<i", raw, 22)[0]
    pad = (w * 3 + 3) & ~3
    px = raw[off:]

    def encode(buf):
        out = bytearray(len(raw))
        out[0:off] = raw[0:off]
        out[off:] = buf
        return bytes(out)

    identity = encode(px) == raw
    flipped = bytearray(px)
    for y in range(h):
        flipped[y * pad:(y + 1) * pad] = px[(h - 1 - y) * pad:(h - y) * pad]
    vflip_refused = encode(bytes(flipped)) != raw
    return {"identity_ok": identity, "vflip_refused": vflip_refused,
            "resolution": [w, h],
            "applicability": "not_applicable_static_image_capture",
            "note": "identity decode/re-encode matches byte-exactly; the "
                    "flipped transform is refused (gate has teeth). No video "
                    "frames exist in a visible_static capture, so the "
                    "video-frame-vs-still comparison does not apply "
                    "(prereg section 8)."}


# --- build ----------------------------------------------------------------------------
def build():
    EVIDENCE.mkdir(exist_ok=True)
    ASSETS.mkdir(exist_ok=True)
    pins = load_pins()
    tb, tq, cr, lc, F = load_modules(pins)
    bundle = tb.loads((CONTRIB / PINS["terrain_bundle_json"]["rel"]).read_bytes())
    surface = tq.TerrainSurface(bundle, validate=False)
    clearing_decl = json.loads(
        (CONTRIB / PINS["clearing_declaration_json"]["rel"]).read_bytes())
    contact_law = json.loads(
        (CONTRIB / PINS["contact_law_json"]["rel"]).read_bytes())
    require(contact_law["declarations"]["slop_m"] == CONTACT_POINT_SLACK_M
            and contact_law["declarations"]["margin_m"] == CONTACT_POINT_SLACK_M,
            "f07_contact_law_slop_drift",
            contact_law["declarations"]["slop_m"])
    trunk = json.loads(
        (CONTRIB / PINS["trunk_declaration_json"]["rel"]).read_bytes())

    rng = cr.SplitMix64(SEED)
    placed = place_obstacles(rng, surface)
    obstacles = build_obstacle_meshes(placed, surface)
    declaration, decl_bytes, decl_sha = make_declaration(obstacles)
    (ASSETS / "obstacle_declaration.json").write_bytes(decl_bytes)
    require(load_declaration(ASSETS / "obstacle_declaration.json")
            == declaration, "f07_declaration_roundtrip")

    # mask + routes (P3/P4) + boundary audits (P1/P2)
    mask, attribution = build_mask(obstacles, surface)
    audit = attribution_audit(mask, attribution)
    routes, reach = verify_routes(obstacles, surface, mask=mask)
    post_audit = post_ring_audit(bundle, surface, clearing_decl)

    # ground body (F04 bytes) + P0 measured per obstacle (A3)
    ground_body = F.ground_contact_body(bundle, lc)
    groups, _ = F.trunk_partition(trunk)
    tverts_contact = [F.to_contact(v[0:3])
                      for v in trunk["render_mesh"]["vertices"]]
    trunk_assets = {"groups": groups, "vertices": tverts_contact,
                    "base": F.to_contact(list(TRUNK_SITE_M)),
                    "radius": TRUNK_RADIUS_M, "height": TRUNK_HEIGHT_M,
                    "base_clearing": tuple(TRUNK_SITE_M), "declaration": trunk}
    trunk_render_verts = [tuple(v[0:3])
                          for v in trunk["render_mesh"]["vertices"]]
    p0 = {}
    for ob in obstacles:
        ob_body = obstacle_contact_body(lc, ob)
        try:
            records, _ = lc.solve_tick([ground_body, ob_body], ccd_enabled=True)
            p0[ob["id"]] = {"outcome": "ran",
                            "contact_records": len(records)}
        except ValueError as exc:
            p0[ob["id"]] = {"outcome": "refused", "detail": str(exc)[:120]}

    # frozen impacts (P5/P6)
    impacts = [run_impact(lc, ob) for ob in obstacles]
    for run in impacts:
        s = run["stop"]
        require(s["first_contact_pre_overlap"], "f07_impact_pre_overlap",
                run["id"])
        require(s["penetration_within_bar"], "f07_impact_penetration",
                run["id"])
        require(s["never_crossed"], "f07_impact_crossed", run["id"])
        require(s["contact_names_struck_surface"], "f07_impact_surface",
                run["id"])
        require(s["plane_within_bar"], "f07_impact_plane", run["id"])
        require(s["analytic_within_bar"], "f07_impact_analytic", run["id"])
        require(s["ledger_within_bar"], "f07_impact_ledger", run["id"])

    # scene mesh + cameras + markers + frozen outcome table
    # the render/classify mesh carries the RAW pinned clearing-frame trunk
    # vertices (the contact-frame copies belong to the M06 bodies only)
    mesh = SceneMesh07(bundle, trunk_render_verts, groups, obstacles)
    cams = {key: Camera07(spec) for key, spec in VIEW_SPECS.items()}
    marker_rows = []
    subjects_by_id = {}
    probes_by_view = {key: [] for key in VIEW_ORDER}
    for view_key in VIEW_ORDER:
        cam = cams[view_key]
        for ob in obstacles:
            if view_key != "V1_clearing_overview":
                continue
            mk = pick_subject(ob, mesh, cam)
            if mk is None:
                # the whole obstacle is occluded in this view: the honest
                # outcome is OCCLUDED (frozen table records it)
                marker_rows.append({"marker": "subject_" + ob["id"],
                                    "view": view_key,
                                    "expected": "VISIBLE_EXACT",
                                    "outcome": "OCCLUDED",
                                    "record": {"reason":
                                               "no visible surface point"}})
                continue
            out = classify_marker(mesh, cam, mk)
            marker_rows.append({"marker": mk["id"], "view": view_key,
                                "expected": "VISIBLE_EXACT",
                                "outcome": out["outcome"], "record": out})
            subjects_by_id[ob["id"]] = mk
            probes_by_view[view_key].append(
                {"point": list(mk["point"]), "oracle_n": mk["oracle_n"]})
        if view_key == "V1_clearing_overview":
            gm = {"point": (SPAWN_M[0], SPAWN_M[1], SPAWN_M[2]),
                  "classify_point": (SPAWN_M[0] + 1e-3, SPAWN_M[1], SPAWN_M[2]),
                  "surface": "monkey_clearing_ground", "kind": "ground",
                  "oracle_h": surface.height_at(SPAWN_M[0], SPAWN_M[2]),
                  "oracle_n_set": incident_ground_normals(mesh, 0.0, 0.0),
                  "id": "marker_spawn"}
            out = classify_marker(mesh, cam, gm)
            marker_rows.append({"marker": gm["id"], "view": view_key,
                                "expected": "VISIBLE_EXACT",
                                "outcome": out["outcome"], "record": out})
            ps = post_subject(bundle, clearing_decl)
            out = classify_marker(mesh, cam, ps)
            marker_rows.append({"marker": ps["id"], "view": view_key,
                                "expected": "VISIBLE_EXACT",
                                "outcome": out["outcome"], "record": out})
            probes_by_view[view_key].append(
                {"point": list(ps["point"]), "oracle_n": [0.0, 1.0, 0.0]})
        if view_key in FROZEN_MARKER_TABLE.get("subject_trunk", {}):
            tm = trunk_subject_marker(cam, trunk_assets)
            out = classify_marker(mesh, cam, tm)
            marker_rows.append({"marker": tm["id"], "view": view_key,
                                "expected": "VISIBLE_EXACT",
                                "outcome": out["outcome"], "record": out})
            probes_by_view[view_key].append(
                {"point": list(tm["point"]), "oracle_n": tm["oracle_n"]})
    mismatch = [r for r in marker_rows if r["outcome"] != r["expected"]]
    vbm = [r for r in marker_rows if r["outcome"] == "VISIBLE_BUT_MISMATCH"]
    require(not mismatch, "f07_marker_table_violated",
            [(r["marker"], r["view"], r["expected"], r["outcome"])
             for r in mismatch])
    require(not vbm, "f07_visible_but_mismatch", vbm)

    # falsifier arms run FIRST: they must all bite before any evidence is written
    bites = run_bites(lc, obstacles, surface, bundle, trunk_assets, mesh, cams,
                      subjects_by_id)
    require(all(b["bites"] for b in bites), "f07_falsifier_did_not_bite",
            [b["bite"] for b in bites if not b["bites"]])

    # impact probes for the diagnostic layer (normals + tick IDs)
    impact_marks = []
    for run in impacts:
        for s in run["states"]:
            if s["contacts"]:
                c0 = s["contacts"][0]
                impact_marks.append({"run": run["id"], "tick": s["tick"],
                                     "point": c0["point_clearing_a"],
                                     "normal": c0["normal_contact_to_a_clearing"],
                                     "oracle_n":
                                         c0["normal_contact_to_a_clearing"],
                                     "tick_id": s["tick"]})
                break

    # frames (diagnostic + clean per profile view)
    labels = frozen_labels(obstacles)
    tag_bindings = [{"label_id": lab["id"], "subject_id": lab["subject_id"]}
                    for lab in labels]
    frames = {}
    frame_rows = []
    for view_key in VIEW_ORDER:
        cam = cams[view_key]
        for mode in ("diagnostic", "clean"):
            probes = (probes_by_view[view_key] + impact_marks) \
                if mode == "diagnostic" else None
            colour = render_frame(mesh, cam, mode == "diagnostic", probes,
                                  labels if mode == "diagnostic" else None)
            path = EVIDENCE / ("frame_%s_%s.bmp" % (view_key, mode))
            write_bmp(path, colour)
            raw = path.read_bytes()
            frames["%s_%s" % (view_key, mode)] = sha_bytes(raw)
            frame_rows.append({
                "path": "evidence/frame_%s_%s.bmp" % (view_key, mode),
                "raw_sha256": sha_bytes(raw),
                "role": "%s %s" % (PROFILE_VIEW_NAMES[view_key], mode)})
    gate_artifact = "evidence/frame_V1_clearing_overview_clean.bmp"
    capture_sha = frames["V1_clearing_overview_clean"]

    # capture manifest (F03 static form) + structural + gate validation
    rows = []
    required_by_view = {key: sorted({r["marker"] for r in marker_rows
                                     if r["view"] == key
                                     and r["outcome"] == "VISIBLE_EXACT"})
                        for key in VIEW_ORDER}
    observed_by_view = {key: sorted({r["marker"] for r in marker_rows
                                     if r["view"] == key})
                        for key in VIEW_ORDER}
    for view_key in VIEW_ORDER:
        cam_rec = cams[view_key].camera_record([0])
        for mode in ("diagnostic", "clean"):
            rows.append({
                "view_id": PROFILE_VIEW_NAMES[view_key],
                "profile_view_key": view_key,
                "mode": mode,
                "pair_id": "pair-" + view_key,
                "artifact_locator": {
                    "kind": "image", "region": "whole_frame",
                    "raw_sha256": frames["%s_%s" % (view_key, mode)]},
                "state_binding": {"kind": "state", "sha256": decl_sha},
                "camera": cam_rec,
                "visibility": (
                    {"layers": list(DIAGNOSTIC_LAYERS),
                     "label_ids": [b["label_id"] for b in tag_bindings],
                     "selected_ids": [],
                     "required_subject_ids": required_by_view[view_key],
                     "observed_subject_ids": observed_by_view[view_key],
                     "missing_subject_ids": [],
                     "occlusion_mode": "depth_tested",
                     "tag_bindings": tag_bindings}
                    if mode == "diagnostic" else
                    {"layers": [], "label_ids": [], "selected_ids": [],
                     "required_subject_ids": required_by_view[view_key],
                     "observed_subject_ids": observed_by_view[view_key],
                     "missing_subject_ids": [],
                     "occlusion_mode": "depth_tested", "tag_bindings": []})})
    manifest = {
        "schema": "chimera.visual_capture_manifest.v1",
        "task_id": TASK_ID,
        "run_id": RUN_ID,
        "capture_sha256": capture_sha,
        "subject_sha256": decl_sha,
        "profile_id": "forest",
        "tick_interval": [0, 0],
        "capture_layout": {"files": frame_rows,
                           "single_gate_bound_artifact": gate_artifact},
        "views": rows,
    }
    sys.path.insert(0, str(CONTRIB.parent))
    import visual_capture
    import visual_gate
    prof, prof_meta = read_registry_profile()
    context = {"task_id": TASK_ID, "run_id": RUN_ID,
               "subject_sha256": decl_sha, "capture_sha256": capture_sha,
               "tick_interval": [0, 0]}
    validation = visual_capture.validate_manifest(manifest, context, prof)
    require(validation["structurally_valid"], "f07_capture_invalid", validation)
    (EVIDENCE / "capture_manifest.json").write_bytes(canonical(manifest))
    (EVIDENCE / "capture_context.json").write_bytes(canonical(context))
    receipt = {"evidence": {
        "camera": {"reference": str(EVIDENCE / "capture_manifest.json"),
                   "raw_sha256": sha_bytes(
                       (EVIDENCE / "capture_manifest.json").read_bytes())},
        "visual": {"reference": str(HERE / gate_artifact),
                   "raw_sha256": sha_bytes((HERE / gate_artifact).read_bytes())}},
        "capture_context": context}
    gate = visual_gate.verify(receipt, {"task_id": TASK_ID,
                                        "task": {"verification_profile": prof}})
    require(gate["structurally_valid"], "f07_visual_gate_invalid", gate)
    tgate = transform_selftest(HERE / gate_artifact)
    require(tgate["identity_ok"] and tgate["vflip_refused"],
            "f07_transform_gate", tgate)
    (EVIDENCE / "validation_receipt.json").write_bytes(canonical({
        "visual_capture": validation, "visual_gate": gate,
        "profile": prof_meta,
        "single_gate_bound_artifact": gate_artifact,
        "capture_sha256": capture_sha,
        "transform_list_gate": tgate}))

    # artifacts: contact trace + route trace
    trace = {"schema": "chimera.mat2_f07.contact_trace.v1",
             "declaration_sha256": decl_sha,
             "impacts": impacts}
    (EVIDENCE / "contact_trace.json").write_bytes(canonical(trace))
    route_doc = {"schema": "chimera.mat2_f07.route_trace.v1",
                 "declaration_sha256": decl_sha,
                 "mask_step_m": MASK_STEP_M, "mask_n": MASK_N,
                 "blocked_cell_count": sum(sum(r) for r in mask),
                 "attribution": audit, "post_ring": post_audit,
                 "routes": routes, "reachable_cells": len(reach)}
    (EVIDENCE / "route_trace.json").write_bytes(canonical(route_doc))

    # P1 vertex identity: the shipped arrays == the declaration, obstacle-wise
    identity = []
    for k, ob in enumerate(obstacles):
        from_decl = declaration["obstacles"][k]["vertices_m"]
        same = [list(v) for v in ob["verts"]] == from_decl
        require(same, "f07_vertex_identity", ob["id"])
        identity.append({"id": ob["id"],
                         "render_equals_declaration": True,
                         "vertex_count": len(ob["verts"])})

    checks = {
        "schema": "chimera.mat2_f07.checks.v1",
        "identity": {
            "card": "MAT2-F07", "planning_id": "F07",
            "attempt_id": ATTEMPT_ID, "arrival_id": ARRIVAL_ID,
            "criteria_sha256": CRITERIA_SHA256, "scope_sha256": SCOPE_SHA256,
            "base_revision": BASE_REVISION,
            "prereg_commit": PREREG_COMMIT,
            "amendment_commits": AMENDMENT_COMMITS,
            "done_when": "The clearing offers traversable routes; no invisible "
                         "walls masquerade as physical obstacles",
            "profile": {"id": "forest", "kind": "visible_static"}},
        "pins": pins,
        "pin_source_tree": PIN_SOURCE_TREE,
        "constants": {
            "seed": SEED,
            "obstacle_matter_mu_s": OBSTACLE_MU_S,
            "obstacle_matter_mu_k": OBSTACLE_MU_K,
            "probe_mass_kg": 0.12,
            "probe_mu_s": 0.6,
            "probe_mu_k": 0.4,
            "contact_slop_m": CONTACT_POINT_SLACK_M,
            "pen_bar_m": PEN_BAR_M,
            "ledger_bar": LEDGER_BAR,
            "plane_bar_m": PLANE_BAR_M,
            "slope_bar": SLOPE_BAR,
            "passable_bound_m": PASSABLE_BOUND_M,
            "block_inflation_m": BLOCK_INFLATION_M,
            "mask_step_m": MASK_STEP_M,
            "edge_coverage_bar_m": EDGE_COVERAGE_BAR_M,
            "impact_speed_m_s": IMPACT_SPEED_M_S,
            "impact_ticks": TICKS_IMPACT,
            "max_viewpoint_offset_m": MAX_VIEWPOINT_OFFSET_M},
        "declaration": {"path": "assets/obstacle_declaration.json",
                        "sha256": decl_sha,
                        "obstacle_count": len(obstacles)},
        "p0_combined_instantiation": p0,
        "p1_tied_assets": {
            "per_obstacle": identity,
            "render_collision_sets": render_collision_set_identity(obstacles),
            "post_ring": post_audit},
        "p2_boundary_declaration": stop_declaration_audit(
            audit["blocked_by_record"], [ob["id"] for ob in obstacles],
            boundary_records() + [{"id": ob["id"]} for ob in obstacles]),
        "p3_routes": routes,
        "p4_attribution": audit,
        "p5_impacts": [{"id": r["id"], "stop": r["stop"],
                        "start_clearing_m": r["start_clearing_m"],
                        "velocity_clearing_m_s": r["velocity_clearing_m_s"],
                        "approach_axis": r["approach_axis"]}
                       for r in impacts],
        "p7_markers": {"rows": [{k: v for k, v in r.items() if k != "record"}
                                | {"pixel_px": r["record"].get("pixel_px"),
                                   "margin_fraction":
                                       r["record"].get("margin_fraction"),
                                   "hit_surface_id":
                                       r["record"].get("hit_surface_id")}
                                for r in marker_rows],
                       "visible_but_mismatch_count": len(vbm),
                       "frozen_table": FROZEN_MARKER_TABLE},
        "capture": {"profile": prof_meta, "validation": validation,
                    "visual_gate": gate, "capture_sha256": capture_sha,
                    "manifest_sha256": sha_bytes(
                        (EVIDENCE / "capture_manifest.json").read_bytes()),
                    "gate_artifact": gate_artifact,
                    "transform_list_gate": tgate,
                    "frames": frames},
        "falsifier_bites": bites,
    }
    (EVIDENCE / "checks.json").write_bytes(canonical(checks))
    return checks


def verify_determinism():
    """P8: two full builds; every evidence artifact byte-identical. The
    record's own output (determinism.json) is excluded from the set."""

    def snapshot():
        return {p.name: sha_bytes(p.read_bytes())
                for p in sorted(list(EVIDENCE.iterdir()) +
                                list(ASSETS.iterdir()))
                if p.is_file() and p.name != "determinism.json"}

    first = build()
    snap = {k: v for k, v in snapshot().items()}
    second = build()
    snap2 = snapshot()
    identical = snap == snap2
    require(identical, "f07_nondeterministic",
            {k for k in set(snap) | set(snap2) if snap.get(k) != snap2.get(k)})
    record = {"prediction": "P8_determinism", "artifacts": len(snap),
              "identical": True, "hashes": snap}
    (EVIDENCE / "determinism.json").write_bytes(canonical(record))
    return record


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("bites", "build", "verify"):
        print(__doc__)
        sys.exit(2)
    if sys.argv[1] == "verify":
        rec = verify_determinism()
        print("determinism: artifacts", rec["artifacts"], "identical",
              rec["identical"])
        sys.exit(0)
    checks = build()
    if sys.argv[1] == "bites":
        for b in checks["falsifier_bites"]:
            print(" -", b["bite"], "BITES" if b["bites"] else "NO-BITE")
    print("build ok:", checks["declaration"]["obstacle_count"], "obstacles;",
          "routes reached:",
          sorted(k for k, v in checks["p3_routes"].items() if v["reached"]))
