"""trunk_recipe -- M-F03: one rigid climbable trunk as deterministic data.

Schema ``chimera.trunk_asset.v1``. Follows the house compiled-scene pattern
(tools/science_funnel/common.py via F01's clearing_recipe): canonical JSON bytes,
a self-pinned sha256 over those bytes, strict ``require``/``Refusal`` intake,
SI metres, right-handed +Y-up world convention (citations in
agents/F03_trunk/discovery_note.md and inside the declaration).

Item F03 (verbatim): "Trunk geometry, surface IDs, material provenance and collision
representation are explicit. Deformable branches and bark damage deferred."

COLLISION REPRESENTATION (frozen C++ consequence, discovery note section 2): the
engine's only physics contacts are analytic (gait: contact-point spheres vs ONE plane;
earth: body vs inclined plane); there is NO mesh-collision route in the HTTP contract.
The trunk's collision representation is therefore an EXACT analytic solid -- a right
circular cylinder plus two caps with closed-form contact normals -- and the render
mesh is its tessellation, so the representation error (mesh discretization vs the
analytic surface) is a measured number, not an assumption. Any collision consumer
(F04 verification, a future engine integration behind its own gate) must reproduce
this analytic contract.

RIGID ONLY: no deformability, no damage model, no branches. The validator enforces a
CLOSED key vocabulary, so such fields cannot silently appear (prereg falsifier d).

MATERIAL PROVENANCE: the lineage has no evidenced bark friction (searched: the gait
contract's own 0.6 is an uncited design constant; dryad_granatosky is gait kinematics;
usgs_splib07 has no curated bark entry -- discovery note section 3). The friction
coefficient is declared UNEVIDENCED-PLACEHOLDER, carrying the walking lane's 0.6 as a
transparent seed, with acquisition named as a G04 prerequisite. No invented number is
presented as evidence.

FROZEN PREREG: agents/F03_trunk/PREREGISTRATION.md (the values below ARE that prereg).
Height and radius are derived from P02P03-pinned Oku-2021 walker numbers, not chosen:
H = (0.419 + 0.482) + (0.125 + 0.132) = 1.158 m; R = 0.074/2 = 0.037 m.
The site is consumed from F01's live declaration (site is F01's data; the geometry is
what this task qualifies, C15).

Determinism: the geometry is pure arithmetic (no PRNG at all) -- same inputs give
byte-identical declarations on any platform; all floats are snapped to the 1e-6 grid
before the canonical write.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import sys

SCHEMA = "chimera.trunk_asset.v1"
NAME = "monkey_trunk"
OBJECT_ID = "trunk_01"

# --- the F01 source of the site (consumed, never re-derived) -------------------
_F01_SCHEMA = "chimera.monkey_clearing.v1"
_F01_RECIPE_REL = os.path.join("tools", "monkey_campaign", "data", "monkey_clearing",
                               "clearing_recipe.py")
_F01_DECL_REL = os.path.join("tools", "monkey_campaign", "data", "monkey_clearing",
                             "clearing_declaration.json")
_F01_BODY_SHA256 = "aa2607df97e0d6ec6a132b1e1ed0686da2ae920de7d659a8bb5ced013a358474"

# --- frozen prereg values (PREREGISTRATION.md; do not tune) --------------------
# pinned walker numbers (P02P03 lineage pin; citations in the declaration)
WALKER_MASS_KG = 10.038            # Oku 2021 Table 1 assembly total
GRAVITY_M_S2 = 9.80665             # engine gravity (gait_scene.py Assembly gravity)
LEG_HIP_TO_MP_M = 0.419            # derived_numbers.json body_model.leg_len_hip_to_MP_m
HAT_LENGTH_M = 0.482               # derived_numbers.json segments_Table1.HAT.length_m
UPPERARM_LENGTH_M = 0.125          # gait_scene.py fore struts ("upperarm", ..., 0.125)
FOREARM_LENGTH_M = 0.132           # gait_scene.py fore struts ("forearm", ..., 0.132)
FOOT_LENGTH_M = 0.074              # derived_numbers.json segments_Table1.foot.length_m
SOLE_CONTACT_RADIUS_M = 0.004      # gait_scene.py SOLE_RADIUS

STANDING_HEIGHT_BOUND_M = LEG_HIP_TO_MP_M + HAT_LENGTH_M      # 0.901 max ground reach
FORELIMB_CHAIN_M = UPPERARM_LENGTH_M + FOREARM_LENGTH_M       # 0.257
TRUNK_HEIGHT_M = STANDING_HEIGHT_BOUND_M + FORELIMB_CHAIN_M   # 1.158 (grid-snapped)
TRUNK_RADIUS_M = FOOT_LENGTH_M / 2.0                          # 0.037 opposed-grip rule
FOOTPRINT_BOUND_M = 0.5            # F01's bound; the spawn-clearance derivation uses it
EXTENT_HALF_WIDTH_M = 20.0         # F01 extent (approach check only)
REQUIRED_CLEARANCE_M = 1.5         # F01 R_clear (re-proven with the REAL radius)

# representation error (prereg): tolerance derived from the contact machinery,
# ring count derived from the tolerance. delta(N) = R*(1 - cos(pi/N)) <= TOL.
REP_TOL_M = 0.05 * SOLE_CONTACT_RADIUS_M                     # 2e-4 m
RING_SEGMENTS = 32                 # smallest power of two >= N_min = 31 (derived)

# material provenance (frozen; discovery note section 3)
MATERIAL_ID = "mat.bark.trunk_01"
FRICTION_PLACEHOLDER = 0.6         # walking lane's uncited design constant, seed only
FRICTION_PROVENANCE = "UNEVIDENCED-PLACEHOLDER"
FRICTION_ACQUISITION = "G04"
BARK_COLOUR_RGB = [0.36, 0.25, 0.16]
BARK_COLOUR_CLASS = "design"

GRID_DECIMALS = 6                  # the 1e-6 determinism grid

SURFACE_IDS = ("trunk_01.lateral", "trunk_01.base_cap", "trunk_01.top_cap")

_COORD_CITATIONS = [
    "ChimeraEngine/engine/coupled_dynamics.hpp:52 gravity_{0,-gravity,0} -> +Y up",
    "ChimeraEngine/engine/earth_environment.hpp:41,110 ground plane y=0, normal +Y",
    "ChimeraEngine/engine/tests_environment/native.cpp:13 right_handed_frame east x up = south",
    "tools/science_funnel/units.py canonical SI length unit m",
    "tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json (F01) same convention",
]

_WALKER_CITATIONS = [
    "tools/science_funnel/validation/gait_controller_20260918/derived_numbers.json "
    "body_model.mass_kg=10.038, leg_len_hip_to_MP_m=0.419, segments_Table1 (HAT 0.482 m, foot 0.074 m)",
    "tools/science_funnel/gait_scene.py fore struts upperarm 0.125 m + forearm 0.132 m; SOLE_RADIUS=0.004",
    "tools/science_funnel/gait_scene.py:164 Assembly gravity [0,-9.80665,0]",
    "tools/monkey_campaign/agents/P02P03/report.md section 1 'Training body (physics)' row (the 10.038 kg pin)",
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


def _grid(value, decimals=GRID_DECIMALS):
    """Snap onto the determinism grid (round-half-even, platform-stable)."""
    return round(float(value), decimals)


def _repo_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))


def _load_f01_recipe():
    """Import F01's clearing_recipe regardless of the caller's cwd."""
    try:
        from tools.monkey_campaign.data.monkey_clearing import clearing_recipe as f01
        return f01
    except ImportError:
        pass
    path = os.path.join(_repo_root(), _F01_RECIPE_REL)
    spec = importlib.util.spec_from_file_location("f01_clearing_recipe", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_f01_declaration(f01=None):
    """Load and STRICTLY validate F01's live declaration; refuse if it drifted."""
    f01 = f01 or _load_f01_recipe()
    path = os.path.join(_repo_root(), _F01_DECL_REL)
    require(os.path.exists(path), "f03_f01_declaration_missing", path)
    declaration = f01.load_declaration(path)
    receipt = f01.validate_declaration(declaration)          # re-derives every claim
    require(receipt.get("validated") is True, "f03_f01_validation_failed")
    require(declaration.get("declaration_sha256") == _F01_BODY_SHA256,
            "f03_f01_drift", declaration.get("declaration_sha256"))
    return declaration


# --- analytic surface (the collision representation's ground truth) -----------
def dist_to_axis(x, z, cx, cz):
    return math.hypot(x - cx, z - cz)


def on_lateral(x, y, z, site, radius, height, tol=1e-9):
    """True iff the point is on the lateral surface (exact analytic predicate)."""
    cx, y0, cz = site
    return abs(dist_to_axis(x, z, cx, cz) - radius) <= tol and y0 - tol <= y <= y0 + height + tol


def sagitta(radius, segments):
    """Discretization error of an inscribed N-gon: R*(1 - cos(pi/N))."""
    return radius * (1.0 - math.cos(math.pi / segments))


def min_ring_segments(radius, tol):
    """Smallest N with sagitta(N) <= tol (derived, per prereg)."""
    n = 1
    while sagitta(radius, n) > tol:
        n += 1
        require(n < 100000, "f03_segments_search_runaway", n)
    return n


# --- the render mesh (tessellation of the analytic surface) --------------------
def build_mesh(site, radius, height, segments):
    """Deterministic prism tessellation; every vertex exactly on the analytic
    surface with its exact analytic normal; outward winding per triangle
    (renderer normal = cross(b-a, c-a), graph_earth.hpp:82).

    Layout: [0,segments) bottom lateral ring, [segments,2*segments) top lateral
    ring, [2*segments,3*segments) base-cap ring, [3*segments,4*segments) top-cap
    ring, 4*segments base centre, 4*segments+1 top centre.
    """
    cx, y0, cz = site
    y1 = y0 + height
    vertices = []
    radial = lambda k: (math.cos(2.0 * math.pi * k / segments), 0.0,
                        math.sin(2.0 * math.pi * k / segments))
    for k in range(segments):
        nx, _, nz = radial(k)
        vertices.append([_grid(cx + radius * nx), _grid(y0), _grid(cz + radius * nz),
                         _grid(nx), 0.0, _grid(nz),
                         BARK_COLOUR_RGB[0], BARK_COLOUR_RGB[1], BARK_COLOUR_RGB[2]])
    for k in range(segments):
        nx, _, nz = radial(k)
        vertices.append([_grid(cx + radius * nx), _grid(y1), _grid(cz + radius * nz),
                         _grid(nx), 0.0, _grid(nz),
                         BARK_COLOUR_RGB[0], BARK_COLOUR_RGB[1], BARK_COLOUR_RGB[2]])
    for k in range(segments):
        nx, _, nz = radial(k)
        vertices.append([_grid(cx + radius * nx), _grid(y0), _grid(cz + radius * nz),
                         0.0, -1.0, 0.0,
                         BARK_COLOUR_RGB[0], BARK_COLOUR_RGB[1], BARK_COLOUR_RGB[2]])
    for k in range(segments):
        nx, _, nz = radial(k)
        vertices.append([_grid(cx + radius * nx), _grid(y1), _grid(cz + radius * nz),
                         0.0, 1.0, 0.0,
                         BARK_COLOUR_RGB[0], BARK_COLOUR_RGB[1], BARK_COLOUR_RGB[2]])
    vertices.append([_grid(cx), _grid(y0), _grid(cz), 0.0, -1.0, 0.0,
                     BARK_COLOUR_RGB[0], BARK_COLOUR_RGB[1], BARK_COLOUR_RGB[2]])
    vertices.append([_grid(cx), _grid(y1), _grid(cz), 0.0, 1.0, 0.0,
                     BARK_COLOUR_RGB[0], BARK_COLOUR_RGB[1], BARK_COLOUR_RGB[2]])

    indices = []
    for k in range(segments):
        k1 = (k + 1) % segments
        b0, b1, t0, t1 = k, k1, segments + k, segments + k1
        indices += [b0, t0, b1, t0, t1, b1]                    # lateral, outward
        indices += [4 * segments, 2 * segments + k, 2 * segments + k1]   # base cap, -Y
        indices += [4 * segments + 1, 3 * segments + k1, 3 * segments + k]  # top cap, +Y
    return vertices, indices


def measure_representation_error(vertices, site, radius, segments):
    """Max radial deficit of the RENDER surface vs the analytic cylinder:
    for each ring edge, the chord midpoint's radial distance shortfall."""
    cx, _, cz = site
    worst = 0.0
    for base in (0, segments):                       # bottom and top lateral rings
        for k in range(segments):
            k1 = segments + ((k + 1) % segments) if base else (k + 1) % segments
            a, b = vertices[base + k], vertices[k1]
            mx, mz = (a[0] + b[0]) / 2.0, (a[2] + b[2]) / 2.0
            worst = max(worst, radius - dist_to_axis(mx, mz, cx, cz))
    return worst


# --- compile / write / load ----------------------------------------------------
def compile_declaration(ring_segments=RING_SEGMENTS, f01_declaration=None):
    """Deterministic compile: same inputs -> byte-identical declaration, anywhere.

    The SITE comes from F01's live declaration (validated with F01's own validator
    and digest-checked); the geometry is derived from the pinned walker numbers.
    """
    require(isinstance(ring_segments, int) and ring_segments >= 3,
            "f03_segments_domain", ring_segments)
    require(sagitta(TRUNK_RADIUS_M, ring_segments) <= REP_TOL_M,
            "f03_segments_below_tolerance",
            (ring_segments, sagitta(TRUNK_RADIUS_M, ring_segments), REP_TOL_M))

    f01_decl = f01_declaration or load_f01_declaration()
    f01 = _load_f01_recipe()
    site_rec = f01_decl["trunk_sites"][0]
    require(site_rec.get("id") == OBJECT_ID, "f03_site_id", site_rec.get("id"))
    site = [float(site_rec["site_m"][0]), float(site_rec["site_m"][1]),
            float(site_rec["site_m"][2])]
    require(site[1] == f01.height_at(f01_decl["terrain"]["recipe"]["mounds"],
                                     site[0], site[2]),
            "f03_site_height", site[1])

    radius, height = _grid(TRUNK_RADIUS_M), _grid(TRUNK_HEIGHT_M)
    weight = _grid(WALKER_MASS_KG * GRAVITY_M_S2)
    energy_full = _grid(WALKER_MASS_KG * GRAVITY_M_S2 * TRUNK_HEIGHT_M)
    energy_above = _grid(WALKER_MASS_KG * GRAVITY_M_S2 * FORELIMB_CHAIN_M)
    vertices, indices = build_mesh(site, radius, height, ring_segments)
    measured = _grid(measure_representation_error(vertices, site, radius, ring_segments), 9)
    formula = _grid(sagitta(radius, ring_segments), 9)
    axis_distance = _grid(math.hypot(site[0], site[2]))
    spawn = f01_decl["spawn"]["position_m"]
    axis_from_spawn = _grid(math.hypot(site[0] - spawn[0], site[2] - spawn[2]))

    declaration = {
        "schema": SCHEMA,
        "name": NAME,
        "object_id": OBJECT_ID,
        "coordinate_convention": {
            "units": "m", "up_axis": "+y", "handedness": "right",
            "axes": {"x": "east", "y": "up", "z": "south"},
            "origin": "scene centre at the base ground plane (y=0), F01's world",
            "citations": list(_COORD_CITATIONS),
        },
        "site": {
            "id": OBJECT_ID,
            "base_centre_m": site,
            "axis_dir": [0.0, 1.0, 0.0],
            "terrain_height_at_site_m": _grid(site[1]),
            "terrain_slope_at_site_m_per_m": 0.0,
            "footprint_bound_m": FOOTPRINT_BOUND_M,
            "provenance": {
                "file": "tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json",
                "schema": _F01_SCHEMA,
                "declaration_sha256": _F01_BODY_SHA256,
                "note": "F01 pins the SITE as data; F03 qualifies the geometry, surface "
                        "IDs and material provenance at that site (C15). The 0.5 m "
                        "footprint bound feeds F01's spawn-clearance derivation, so "
                        "geometry beyond it is a prereg change, not an edit.",
            },
        },
        "geometry": {
            "profile_kind": "right_circular_cylinder",
            "radius_m": radius,
            "height_m": height,
            "base_elevation_m": _grid(site[1]),
            "profile_function": "r(y) = radius_m, constant, for base_elevation_m <= y "
                                "<= base_elevation_m + height_m (a RIGHT circular "
                                "cylinder; no taper, no buttress, no bark relief)",
            "derivation": {
                "walker_mass_kg": WALKER_MASS_KG,
                "gravity_m_s2": GRAVITY_M_S2,
                "weight_N": weight,
                "leg_hip_to_mp_m": LEG_HIP_TO_MP_M,
                "hat_length_m": HAT_LENGTH_M,
                "upperarm_length_m": UPPERARM_LENGTH_M,
                "forearm_length_m": FOREARM_LENGTH_M,
                "foot_length_m": FOOT_LENGTH_M,
                "sole_contact_radius_m": SOLE_CONTACT_RADIUS_M,
                "standing_height_bound_m": _grid(STANDING_HEIGHT_BOUND_M),
                "forelimb_chain_m": _grid(FORELIMB_CHAIN_M),
                "height_rule": "H = standing_height_bound + forelimb_chain = "
                               "(leg_hip_to_mp + hat) + (upperarm + forearm); the top "
                               "exceeds the animal's max ground-static reach by exactly "
                               "one pinned forelimb chain, so a hold at the top is a "
                               "genuine climb (feet clear by construction)",
                "radius_rule": "R = foot_length/2; an opposed grip must span the trunk "
                               "diameter with one appendage, and the pinned Oku foot is "
                               "the assembly's only measured appendage length (map A05: "
                               "hand digits not yet assembled); G01 consumes this radius",
                "full_ascent_gain_J": energy_full,
                "above_reach_gain_J": energy_above,
                "citations": list(_WALKER_CITATIONS),
            },
        },
        "collision_representation": {
            "kind": "analytic_cylinder_solid",
            "exact": True,
            "solid": {
                "axis_base_m": site,
                "axis_dir": [0.0, 1.0, 0.0],
                "radius_m": radius,
                "height_m": height,
                "containment_law": "inside iff dist_to_axis((x,z),(cx,cz)) <= radius_m "
                                   "and base_elevation_m <= y <= base_elevation_m + "
                                   "height_m; lateral surface at dist_to_axis = radius_m",
            },
            "contact_normals": {
                "lateral": "n = (x-cx, 0, z-cz)/|(x-cx, 0, z-cz)| (radial outward) at "
                           "dist_to_axis = R, y0 <= y <= y0+H",
                "base_cap": "(0,-1,0) at y = y0, dist_to_axis <= R",
                "top_cap": "(0,+1,0) at y = y0+H, dist_to_axis <= R",
            },
            "engine_binding": {
                "render_route": "engine.load_mesh / mesh_bin, 9-float vertex layout "
                                "pos+normal+color (graph_earth.hpp:26-30)",
                "collision_route": "NONE in the frozen engine HTTP contract (route "
                                   "survey, agents/F03_trunk/discovery_note.md section "
                                   "2): every engine contact is analytic and plane-only. "
                                   "Collision consumers implement THIS analytic contract; "
                                   "any engine-side mesh collision is a separately gated "
                                   "engine change (frozen C++ untouched here).",
            },
            "rigid": True,
            "deformable": False,
            "damage_model": "none",
            "branches": "deferred",
        },
        "surface_ids": [
            {
                "id": "trunk_01.lateral",
                "surface": "lateral",
                "analytic": "dist_to_axis((x,z),(cx,cz)) = radius_m and "
                            "base_elevation_m <= y <= base_elevation_m + height_m",
                "normal_law": "radial outward (x-cx, 0, z-cz)/|(x-cx, 0, z-cz)|",
                "material": MATERIAL_ID,
                "climbable": True,
                "role": "grip and climb surface (the C15/C19 contact surface)",
            },
            {
                "id": "trunk_01.base_cap",
                "surface": "base_cap",
                "analytic": "y = base_elevation_m and dist_to_axis <= radius_m",
                "normal_law": "(0,-1,0)",
                "material": MATERIAL_ID,
                "climbable": False,
                "role": "ground joint at the F01 site (terrain height 0.0, slope 0.0)",
            },
            {
                "id": "trunk_01.top_cap",
                "surface": "top_cap",
                "analytic": "y = base_elevation_m + height_m and dist_to_axis <= radius_m",
                "normal_law": "(0,+1,0)",
                "material": MATERIAL_ID,
                "climbable": False,
                "role": "top boundary; the max hold height the climb task may use",
            },
        ],
        "material": {
            "id": MATERIAL_ID,
            "kind": "bark_placeholder_rigid",
            "friction": {
                "coefficient_placeholder": FRICTION_PLACEHOLDER,
                "provenance": FRICTION_PROVENANCE,
                "placeholder_source": "the walking lane's uncited design constant "
                                      "CONTACT_FRICTION = 0.6 "
                                      "(tools/creature_graph/validation/"
                                      "admit_gait_walker_20260919.py:60; carried in "
                                      "creature_graph.json model.dynamics.gait_walker "
                                      "physical.contract.contact_friction) -- carried as "
                                      "a seed ONLY, not evidence",
                "acquisition_prerequisite": FRICTION_ACQUISITION,
                "evidence_search": "no evidenced bark/wood-on-skin friction exists on the "
                                   "lineage (searched: creature_graph gait contract; "
                                   "docs/research/20260918_gait_controller_derivation.md; "
                                   "tools/science_funnel/data/ incl. dryad_granatosky "
                                   "gait kinematics and usgs_splib07 without a curated "
                                   "bark entry) -- agents/F03_trunk/discovery_note.md "
                                   "section 3",
                "g01_note": "G01 may compute PROVISIONAL envelopes from this placeholder "
                            "and must label them provisional; no grip verdict is final "
                            "until G04 acquires a measured bark-on-appendage coefficient",
            },
            "colour_rgb": list(BARK_COLOUR_RGB),
            "colour_provenance_class": BARK_COLOUR_CLASS,
            "taxonomy_note": "provenance classes per Chimera/docs/matter/"
                             "matter_library.json (seed/code/researched/provisional/"
                             "trained/design); this friction value is BELOW 'provisional' "
                             "on that ladder -- an unevidenced placeholder debt",
            "contact_surface_ids": list(SURFACE_IDS),
        },
        "render_mesh": {
            "vertex_layout": "pos3 + normal3 + colour3 (9 floats per vertex, "
                             "graph_earth.hpp:26-30)",
            "index_type": "uint32",
            "ring_segments": ring_segments,
            "vertex_count": len(vertices),
            "triangle_count": len(indices) // 3,
            "winding_rule": "triangle normal = cross(b-a, c-a) faces outward "
                            "(graph_earth.hpp:82); verified per triangle by the validator",
            "vertices": vertices,
            "indices": indices,
        },
        "representation_error": {
            "tolerance_m": REP_TOL_M,
            "tolerance_rule": "5% of the walker's 0.004 m sole contact-sphere radius "
                              "(the finest contact feature the creature machinery uses)",
            "measure": "max over ring edges of (radius_m - chord-midpoint radial "
                       "distance), from the ROUNDED vertex table (inscribed polygon, "
                       "render inside the analytic surface)",
            "max_measured_m": measured,
            "sagitta_formula_m": formula,
            "ring_segments_derivation": "delta(N) = R*(1-cos(pi/N)) <= 2e-4 requires "
                                        "N >= pi/acos(1 - TOL/R) = 30.2, i.e. N_min = 31 "
                                        "(delta(30) = 2.027e-4 > TOL); N = 32 is the "
                                        "smallest power of two >= N_min "
                                        "(delta(32) = 1.782e-4 <= TOL)",
        },
        "approach_and_bounds": {
            "spawn_position_m": [float(v) for v in spawn],
            "required_clearance_m": REQUIRED_CLEARANCE_M,
            "axis_distance_from_spawn_m": axis_from_spawn,
            "clearance_with_trunk_radius_m": _grid(axis_from_spawn - radius),
            "extent_half_width_m": EXTENT_HALF_WIDTH_M,
            "solid_within_extent": True,
        },
        "scope": "ONE rigid climbable trunk asset (map F03, C15) at F01's pinned site. "
                 "Rigid only: deformable branches and bark damage are DEFERRED (map "
                 "wording) and are NOT modeled anywhere in this record. Terrain "
                 "rendering and collision are F02's; contact verification is F04's; "
                 "grip feasibility consumes this file's friction placeholder and radius "
                 "in G01; measured friction acquisition is G04's.",
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
            require(key not in out, "f03_duplicate_json_key", key)
            out[key] = value
        return out

    def no_const(value):
        raise Refusal("f03_nonfinite_json", value)

    try:
        return json.loads(raw, object_pairs_hook=unique, parse_constant=no_const)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise Refusal("f03_invalid_json", exc)


def load_declaration(path):
    with open(path, "rb") as handle:
        return loads(handle.read())


# --- validation (every check re-derived from stored numbers) -------------------
_TOP_KEYS = {"schema", "name", "object_id", "coordinate_convention", "site", "geometry",
             "collision_representation", "surface_ids", "material", "render_mesh",
             "representation_error", "approach_and_bounds", "scope",
             "declaration_sha256"}
_GEOM_KEYS = {"profile_kind", "radius_m", "height_m", "base_elevation_m",
              "profile_function", "derivation"}
_COLL_KEYS = {"kind", "exact", "solid", "contact_normals", "engine_binding",
              "rigid", "deformable", "damage_model", "branches"}
_MATERIAL_KEYS = {"id", "kind", "friction", "colour_rgb", "colour_provenance_class",
                  "taxonomy_note", "contact_surface_ids"}


def _finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) \
        and math.isfinite(value)


def _require_finite_list(value, code, n=None):
    require(isinstance(value, list) and all(_finite(v) for v in value), code, value)
    if n is not None:
        require(len(value) == n, code, len(value))


def validate_declaration(declaration, strict_prereg=True):
    """Full validation; raises Refusal on any violation. Returns a receipt dict.

    With ``strict_prereg`` the declaration is also checked against THIS module's
    frozen constants (closed vocabulary included), so a hand-edited declaration
    cannot drift from the prereg and deformable/damage fields cannot appear.
    """
    require(isinstance(declaration, dict), "f03_declaration_object")
    require(declaration.get("schema") == SCHEMA, "f03_schema", declaration.get("schema"))
    require(declaration.get("name") == NAME, "f03_name", declaration.get("name"))
    require(declaration.get("object_id") == OBJECT_ID, "f03_object_id")

    if strict_prereg:
        require(set(declaration.keys()) == _TOP_KEYS, "f03_top_level_vocabulary",
                sorted(set(declaration.keys()) ^ _TOP_KEYS))

    # pinned digest over the canonical bytes without the pin itself
    pinned = declaration.get("declaration_sha256")
    body = {k: v for k, v in declaration.items() if k != "declaration_sha256"}
    require(isinstance(pinned, str) and len(pinned) == 64, "f03_digest_form", pinned)
    require(sha(canonical(body)) == pinned, "f03_digest_mismatch")

    conv = declaration.get("coordinate_convention")
    require(isinstance(conv, dict) and conv.get("units") == "m"
            and conv.get("up_axis") == "+y" and conv.get("handedness") == "right",
            "f03_convention_frozen", conv)
    require(isinstance(conv.get("citations"), list) and conv["citations"],
            "f03_convention_citations")

    # -- site: must be F01's live pinned site, unchanged ------------------------
    site_block = declaration.get("site")
    require(isinstance(site_block, dict), "f03_site_object")
    require(site_block.get("id") == OBJECT_ID, "f03_site_id")
    _require_finite_list(site_block.get("base_centre_m"), "f03_site_centre", 3)
    require(site_block.get("axis_dir") == [0.0, 1.0, 0.0], "f03_site_axis")
    require(site_block.get("footprint_bound_m") == FOOTPRINT_BOUND_M,
            "f03_footprint_bound_frozen", site_block.get("footprint_bound_m"))
    prov = site_block.get("provenance")
    require(isinstance(prov, dict)
            and prov.get("schema") == _F01_SCHEMA
            and prov.get("declaration_sha256") == _F01_BODY_SHA256,
            "f03_site_provenance", prov)
    f01_decl = load_f01_declaration()
    f01 = _load_f01_recipe()
    f01_site = f01_decl["trunk_sites"][0]
    require([float(v) for v in f01_site["site_m"]] == [float(v) for v in site_block["base_centre_m"]],
            "f03_site_mismatch", (f01_site["site_m"], site_block["base_centre_m"]))
    site = [float(v) for v in site_block["base_centre_m"]]
    cx, y0, cz = site
    require(site[1] == f01.height_at(f01_decl["terrain"]["recipe"]["mounds"], cx, cz),
            "f03_site_height", site[1])
    require(site_block.get("terrain_height_at_site_m") == _grid(site[1]),
            "f03_site_height_field")

    # -- geometry: derived numbers re-derived from the pinned inputs ------------
    geometry = declaration.get("geometry")
    require(isinstance(geometry, dict), "f03_geometry_object")
    if strict_prereg:
        require(set(geometry.keys()) == _GEOM_KEYS, "f03_geometry_vocabulary",
                sorted(set(geometry.keys()) ^ _GEOM_KEYS))
    require(geometry.get("profile_kind") == "right_circular_cylinder",
            "f03_profile_kind", geometry.get("profile_kind"))
    radius, height = geometry.get("radius_m"), geometry.get("height_m")
    require(_finite(radius) and _finite(height), "f03_geometry_numbers")
    require(radius == _grid(TRUNK_RADIUS_M), "f03_radius_frozen", radius)
    require(height == _grid(TRUNK_HEIGHT_M), "f03_height_frozen", height)
    require(geometry.get("base_elevation_m") == _grid(site[1]), "f03_base_elevation")
    derivation = geometry.get("derivation")
    require(isinstance(derivation, dict), "f03_derivation_object")
    # the stored pinned inputs must equal THIS module's pinned constants ...
    for key, frozen in (("walker_mass_kg", WALKER_MASS_KG),
                        ("gravity_m_s2", GRAVITY_M_S2),
                        ("leg_hip_to_mp_m", LEG_HIP_TO_MP_M),
                        ("hat_length_m", HAT_LENGTH_M),
                        ("upperarm_length_m", UPPERARM_LENGTH_M),
                        ("forearm_length_m", FOREARM_LENGTH_M),
                        ("foot_length_m", FOOT_LENGTH_M),
                        ("sole_contact_radius_m", SOLE_CONTACT_RADIUS_M)):
        require(derivation.get(key) == frozen, "f03_pinned_input", (key, derivation.get(key)))
    # ... and the derived fields must re-derive from them (falsifier on hidden edits)
    standing = _grid(derivation["leg_hip_to_mp_m"] + derivation["hat_length_m"])
    fore = _grid(derivation["upperarm_length_m"] + derivation["forearm_length_m"])
    require(derivation.get("standing_height_bound_m") == standing, "f03_standing_bound")
    require(derivation.get("forelimb_chain_m") == fore, "f03_forelimb_chain")
    require(height == _grid(standing + fore), "f03_height_derivation")
    require(radius == _grid(derivation["foot_length_m"] / 2.0), "f03_radius_derivation")
    require(derivation.get("weight_N") == _grid(WALKER_MASS_KG * GRAVITY_M_S2),
            "f03_weight_derivation")
    require(derivation.get("full_ascent_gain_J")
            == _grid(WALKER_MASS_KG * GRAVITY_M_S2 * TRUNK_HEIGHT_M),
            "f03_energy_full_derivation")
    require(derivation.get("above_reach_gain_J")
            == _grid(WALKER_MASS_KG * GRAVITY_M_S2 * FORELIMB_CHAIN_M),
            "f03_energy_above_derivation")
    require(isinstance(derivation.get("citations"), list) and derivation["citations"],
            "f03_derivation_citations")
    require(isinstance(geometry.get("profile_function"), str)
            and geometry["profile_function"], "f03_profile_function_text")

    # -- footprint + extent bounds (falsifier a) --------------------------------
    require(radius <= FOOTPRINT_BOUND_M, "f03_footprint_bound", radius)
    half = EXTENT_HALF_WIDTH_M
    require(abs(cx) + radius <= half and abs(cz) + radius <= half,
            "f03_extent_bounds", (cx, cz))
    require(0.0 <= y0 and y0 + height <= 200.0, "f03_height_sanity", (y0, height))

    # -- collision representation: closed vocabulary, rigid only (falsifier d) --
    coll = declaration.get("collision_representation")
    require(isinstance(coll, dict), "f03_collision_object")
    if strict_prereg:
        require(set(coll.keys()) == _COLL_KEYS, "f03_rigid_vocabulary",
                sorted(set(coll.keys()) ^ _COLL_KEYS))
    require(coll.get("kind") == "analytic_cylinder_solid" and coll.get("exact") is True,
            "f03_collision_kind", (coll.get("kind"), coll.get("exact")))
    require(coll.get("rigid") is True and coll.get("deformable") is False
            and coll.get("damage_model") == "none" and coll.get("branches") == "deferred",
            "f03_rigid_flags", (coll.get("rigid"), coll.get("deformable"),
                                coll.get("damage_model"), coll.get("branches")))
    solid = coll.get("solid")
    require(isinstance(solid, dict), "f03_solid_object")
    _require_finite_list(solid.get("axis_base_m"), "f03_solid_axis_base", 3)
    require(solid["axis_base_m"] == site_block["base_centre_m"], "f03_solid_site")
    require(solid.get("axis_dir") == [0.0, 1.0, 0.0], "f03_solid_axis")
    require(solid.get("radius_m") == radius and solid.get("height_m") == height,
            "f03_solid_dimensions")
    require(isinstance(solid.get("containment_law"), str)
            and solid["containment_law"], "f03_containment_law_text")
    normals = coll.get("contact_normals")
    require(isinstance(normals, dict) and isinstance(normals.get("lateral"), str)
            and isinstance(normals.get("base_cap"), str)
            and isinstance(normals.get("top_cap"), str), "f03_contact_normal_laws")
    binding = coll.get("engine_binding")
    require(isinstance(binding, dict) and isinstance(binding.get("render_route"), str)
            and isinstance(binding.get("collision_route"), str),
            "f03_engine_binding_text")

    # -- surface IDs: explicit, unique, resolvable (falsifier c) ----------------
    surfaces = declaration.get("surface_ids")
    require(isinstance(surfaces, list) and len(surfaces) == 3, "f03_surface_count")
    seen, by_surface = set(), {}
    for entry in surfaces:
        require(isinstance(entry, dict), "f03_surface_object")
        sid = entry.get("id")
        require(isinstance(sid, str) and sid, "f03_surface_id")
        require(sid not in seen, "f03_surface_duplicate", sid)
        seen.add(sid)
        surface = entry.get("surface")
        require(surface in ("lateral", "base_cap", "top_cap"), "f03_surface_kind", surface)
        by_surface[surface] = entry
        require(isinstance(entry.get("analytic"), str) and entry["analytic"],
                "f03_surface_analytic", sid)
        require(isinstance(entry.get("normal_law"), str) and entry["normal_law"],
                "f03_surface_normal_law", sid)
        require(entry.get("material") == MATERIAL_ID, "f03_surface_material_ref", sid)
        require(isinstance(entry.get("climbable"), bool), "f03_surface_climbable", sid)
        require(isinstance(entry.get("role"), str) and entry["role"],
                "f03_surface_role", sid)
    require(seen == set(SURFACE_IDS), "f03_surface_ids_frozen", sorted(seen))
    require(by_surface["lateral"]["climbable"] is True, "f03_lateral_climbable")
    require(by_surface["base_cap"]["climbable"] is False
            and by_surface["top_cap"]["climbable"] is False, "f03_caps_not_climbable")

    # -- material: provenance explicit, honest, closed (falsifier c) ------------
    material = declaration.get("material")
    require(isinstance(material, dict), "f03_material_object")
    if strict_prereg:
        require(set(material.keys()) == _MATERIAL_KEYS, "f03_material_vocabulary",
                sorted(set(material.keys()) ^ _MATERIAL_KEYS))
    require(material.get("id") == MATERIAL_ID, "f03_material_id")
    friction = material.get("friction")
    require(isinstance(friction, dict), "f03_friction_object")
    require(friction.get("coefficient_placeholder") == FRICTION_PLACEHOLDER,
            "f03_friction_value", friction.get("coefficient_placeholder"))
    require(friction.get("provenance") == FRICTION_PROVENANCE,
            "f03_friction_provenance", friction.get("provenance"))
    require(friction.get("acquisition_prerequisite") == FRICTION_ACQUISITION,
            "f03_friction_acquisition", friction.get("acquisition_prerequisite"))
    for key in ("placeholder_source", "evidence_search", "g01_note"):
        require(isinstance(friction.get(key), str) and friction[key],
                "f03_friction_field", key)
    require(material.get("colour_rgb") == list(BARK_COLOUR_RGB), "f03_colour_frozen")
    require(material.get("colour_provenance_class") == BARK_COLOUR_CLASS,
            "f03_colour_class")
    require(isinstance(material.get("taxonomy_note"), str)
            and material["taxonomy_note"], "f03_taxonomy_note")
    require(material.get("contact_surface_ids") == list(SURFACE_IDS),
            "f03_material_surface_refs")

    # -- render mesh: on the analytic surface, exact normals, outward winding ---
    mesh = declaration.get("render_mesh")
    require(isinstance(mesh, dict), "f03_mesh_object")
    segments = mesh.get("ring_segments")
    require(segments == RING_SEGMENTS, "f03_ring_segments", segments)
    vertices, indices = mesh.get("vertices"), mesh.get("indices")
    require(isinstance(vertices, list) and len(vertices) == 4 * segments + 2,
            "f03_vertex_count", vertices and len(vertices))
    require(isinstance(indices, list) and len(indices) == 12 * segments,
            "f03_index_count", indices and len(indices))
    for v in vertices:
        _require_finite_list(v, "f03_vertex_fields", 9)
        require(v[6] == BARK_COLOUR_RGB[0] and v[7] == BARK_COLOUR_RGB[1]
                and v[8] == BARK_COLOUR_RGB[2], "f03_vertex_colour", v)
    y1 = _grid(y0 + height)
    worst_on_surface = 0.0
    for i, v in enumerate(vertices):
        x, y, z, nx, ny, nz = v[0], v[1], v[2], v[3], v[4], v[5]
        d = dist_to_axis(x, z, cx, cz)
        cap_ring = 2 * segments <= i < 4 * segments or i >= 4 * segments
        if cap_ring:
            require(abs(ny) == 1.0 and nx == 0.0 and nz == 0.0,
                    "f03_cap_normal", i)
            require(d <= radius + 1e-6, "f03_cap_vertex_radius", (i, d))
        else:
            require(y in (y0, y1), "f03_ring_vertex_y", (i, y))
            # vertex positions are trig values snapped to the 1e-6 grid, so the
            # on-surface tolerance is the rounding envelope (2e-6 m), while the
            # MEASURED representation error below carries the discretization.
            require(abs(d - radius) <= 2e-6, "f03_vertex_off_surface", (i, d - radius))
            worst_on_surface = max(worst_on_surface, abs(d - radius))
            norm = math.sqrt(nx * nx + ny * ny + nz * nz)
            require(abs(norm - 1.0) <= 2e-6, "f03_normal_unit", (i, norm))
            # normal-vs-position consistency: position rounding (5e-7 m) divides by
            # radius (0.037 m) -> up to ~1.4e-5 of direction error; tolerance 4e-5.
            require(abs(nx - (x - cx) / radius) <= 4e-5
                    and abs(nz - (z - cz) / radius) <= 4e-5 and ny == 0.0,
                    "f03_normal_not_radial", i)
        require(radius <= FOOTPRINT_BOUND_M and d <= FOOTPRINT_BOUND_M + 1e-9,
                "f03_vertex_footprint", (i, d))       # falsifier (a), per vertex
    require(indices == build_mesh(site, radius, height, segments)[1],
            "f03_indices_not_canonical")
    for t in range(len(indices) // 3):
        a, b, c = (vertices[indices[3 * t + j]] for j in range(3))
        ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        gx, gy, gz = (a[0] + b[0] + c[0]) / 3.0, (a[1] + b[1] + c[1]) / 3.0, \
                     (a[2] + b[2] + c[2]) / 3.0
        if gy <= y0 + 1e-9 and dist_to_axis(gx, gz, cx, cz) < radius - 1e-9:
            outward = (0.0, -1.0, 0.0)                # base cap
        elif gy >= y1 - 1e-9 and dist_to_axis(gx, gz, cx, cz) < radius - 1e-9:
            outward = (0.0, 1.0, 0.0)                 # top cap
        else:
            d = dist_to_axis(gx, gz, cx, cz) or 1e-12
            outward = ((gx - cx) / d, 0.0, (gz - cz) / d)   # lateral
        require(nx * outward[0] + ny * outward[1] + nz * outward[2] > 0.0,
                "f03_winding_inward", t)

    # -- representation error: measured vs formula vs tolerance (falsifier b) ---
    rep = declaration.get("representation_error")
    require(isinstance(rep, dict), "f03_representation_object")
    require(rep.get("tolerance_m") == REP_TOL_M, "f03_tolerance_frozen",
            rep.get("tolerance_m"))
    measured, formula = rep.get("max_measured_m"), rep.get("sagitta_formula_m")
    require(_finite(measured) and _finite(formula), "f03_representation_numbers")
    require(formula == _grid(sagitta(radius, segments), 9), "f03_sagitta_formula",
            formula)
    require(measured <= REP_TOL_M, "f03_representation_over_tolerance", measured)
    require(abs(measured - formula) <= 2e-6, "f03_measured_vs_formula",
            (measured, formula))
    recomputed = _grid(measure_representation_error(vertices, site, radius, segments), 9)
    require(abs(measured - recomputed) <= 1e-9, "f03_measured_vs_recomputed",
            (measured, recomputed))
    require(isinstance(rep.get("tolerance_rule"), str)
            and isinstance(rep.get("measure"), str)
            and isinstance(rep.get("ring_segments_derivation"), str),
            "f03_representation_texts")

    # -- reachable approach (C15), re-proven with the REAL radius ---------------
    approach = declaration.get("approach_and_bounds")
    require(isinstance(approach, dict), "f03_approach_object")
    _require_finite_list(approach.get("spawn_position_m"), "f03_spawn_position", 3)
    spawn = approach["spawn_position_m"]
    require(spawn == [float(v) for v in f01_decl["spawn"]["position_m"]],
            "f03_spawn_mismatch")
    require(approach.get("required_clearance_m") == REQUIRED_CLEARANCE_M,
            "f03_required_clearance")
    axis_spawn = math.hypot(cx - spawn[0], cz - spawn[2])
    require(approach.get("axis_distance_from_spawn_m") == _grid(axis_spawn),
            "f03_axis_distance", (approach.get("axis_distance_from_spawn_m"), axis_spawn))
    require(approach.get("clearance_with_trunk_radius_m")
            == _grid(axis_spawn - radius), "f03_clearance_field")
    require(axis_spawn - radius >= REQUIRED_CLEARANCE_M, "f03_spawn_clearance",
            axis_spawn - radius)
    require(approach.get("extent_half_width_m") == EXTENT_HALF_WIDTH_M
            and approach.get("solid_within_extent") is True, "f03_extent_fields")

    require(isinstance(declaration.get("scope"), str) and declaration["scope"],
            "f03_scope_text")

    return {"schema": SCHEMA, "object_id": OBJECT_ID,
            "declaration_sha256": pinned,
            "site_m": [cx, y0, cz], "radius_m": radius, "height_m": height,
            "ring_segments": segments, "vertices": len(vertices),
            "triangles": len(indices) // 3,
            "worst_vertex_on_surface_error_m": worst_on_surface,
            "representation_error_m": measured, "representation_tolerance_m": REP_TOL_M,
            "footprint_bound_m": FOOTPRINT_BOUND_M,
            "spawn_clearance_m": _grid(axis_spawn - radius),
            "friction_provenance": FRICTION_PROVENANCE,
            "validated": True}


def selftest():
    """Compile + validate round trip; returns the validation receipt."""
    return validate_declaration(compile_declaration())


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    default = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "trunk_declaration.json")
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
    raise Refusal("f03_cli_verb", argv)


if __name__ == "__main__":
    sys.exit(main())
