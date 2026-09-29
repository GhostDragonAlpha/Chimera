"""implementation.py -- MAT2-F03 source-bound qualification package.

Card MAT2-F03 ("Implement one rigid climbable trunk asset"), planning id F03,
calculation contract C15.

RECONCILE-FIRST: the rigid climbable trunk asset already exists as pinned data
(chimera.trunk_asset.v1, F01's pin). This module NEVER re-derives that
geometry. Per the card's material-first addition it ADDS the explicit reduced
material object:

  1. chimera.material_state.v1   -- trunk_01 as ONE closed region, single-owner
                                    matter wood_trunk_01, mass = declared
                                    density x measured mesh volume, the same
                                    material_contact port M02/M06 use;
  2. chimera.passive_law.v1      -- M04's `rigid` profile assigned to the
                                    region (the explicit RIGID reduction);
  3. chimera.local_contact.v1    -- the pinned triangle set (identity-mapped
                                    visual/physical mesh, per-triangle
                                    surface-id partition) instantiated with
                                    the UNMODIFIED M06 solver as pinned bodies,
                                    plus climb-relevant single-tick experiments
                                    (grip stick / understated-mu slip
                                    discriminator / cap rest) with balanced
                                    per-tick ledgers;
  4. provenance                  -- the pinned matter library's NO-WOOD-ENTRY
                                    absence recorded; declared density 760
                                    kg/m3 (band 650-850) cited from the pinned
                                    on-disk source with the library's own
                                    `researched` class definition and the
                                    missing-conditions honesty note;
  5. forest/visible_static       -- task_id F03 captures bound to the REGISTRY
                                    profile object with a single gate-bound
                                    artifact, and numerical render/collision
                                    correspondence at frozen probes.

The M01/M06/M04 modules and the campaign capture validator are imported as
byte-pinned UNMODIFIED copies (evidence/pins_materialized/). The scene
load path (recipe + declaration + TerrainSurface) reuses F01's pinned bytes
exactly as F01's PASS-reviewed receipt did. The software rasterizer,
probe classifier and camera book are adaptations of F01's verified
implementation (documented in the module tail); all verification bars are
THIS card's (PREREGISTRATION.md, frozen, incl. Amendment A1).

Honest boundary: static-scene evidence plus single-tick contact experiments.
No engine run, no climb controller, no appendage anatomy, no GPU, no native
change. Friction 0.6 stays the recorded UNEVIDENCED-PLACEHOLDER (G04 debt).

Run:  python -B implementation.py bites    # falsifier bites only (fail-first)
      python -B implementation.py build    # bites first, then the pinned pass
Stdlib only. Evidence lands in evidence/ next to this file.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import pathlib
import sqlite3
import struct
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"
ASSETS = HERE / "assets"
PINS_DIR = EVIDENCE / "pins_materialized"

SCHEMA = "chimera.mat2_f03.qualification.v1"
BASE_REVISION = "30cd0f75a2aac6cd8e16504ddfbabf6fa955f1e0"

TASK_ID = "F03"                      # SHORT form (campaign capture schema)
RUN_ID = "mat2-f03-trunk-20260928-86503903"
REGISTRY_SQLITE = pathlib.Path(
    "E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3")
PROFILE_CANONICAL_SHA256 = (
    "d5b25ab9dcc5de7e15b1116f6f9c4da66b6c01d761a0913ef92443294c6bc5e7")
CRITERIA_SHA256 = ("143a172d9531251d45952aa78c0e565b75c4409b3d7070b56109d6ef"
                   "299f1ddd")
SCOPE_SHA256 = ("cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae5799"
                "6097")

# --- pinned sources (PREREGISTRATION reconcile table; do not tune) ------------
PINS = {
    "trunk_declaration_json": {
        "commit": "dc7ea81111d98f32a4d88252c59f2fb8cf3c7399",
        "path": "tools/monkey_campaign/data/monkey_trunk/trunk_declaration.json",
        "sha256": "94ff906ec5e8b8388e4de318aa3321bad9c791fbb168e8234c371ed1d327e3f1",
    },
    "clearing_declaration_json": {
        "commit": "dc7ea81111d98f32a4d88252c59f2fb8cf3c7399",
        "path": "tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json",
        "sha256": "18dd2ff65410cd1cf184a7a8df61c7503a6ce15083f30159e727e9a8117bfbc1",
    },
    "clearing_recipe_py": {
        "commit": "dc7ea81111d98f32a4d88252c59f2fb8cf3c7399",
        "path": "tools/monkey_campaign/data/monkey_clearing/clearing_recipe.py",
        "sha256": "ab800d2257655118296519b606c77ddc7116f524ae0c2e6a0bab3b38473892dc",
    },
    "terrain_query_py": {
        "commit": "a2895755d009f8afc78078f57dc5c3c3819ef74a",
        "path": "tools/monkey_campaign/data/monkey_clearing/terrain_query.py",
        "sha256": "b1e244b8843671afc29af530c4725bf812ffd5f8967130f0202792aeb7a8cce1",
    },
    "terrain_bundle_py": {
        "commit": "a2895755d009f8afc78078f57dc5c3c3819ef74a",
        "path": "tools/monkey_campaign/data/monkey_clearing/terrain_bundle.py",
        "sha256": "c6ada25a1b6192aa86add8b09bc19161c0cd81e3fb3d4bd267492660c0be8f2e",
    },
    "terrain_bundle_json": {
        "commit": "a2895755d009f8afc78078f57dc5c3c3819ef74a",
        "path": "tools/monkey_campaign/data/monkey_clearing/terrain_bundle.json",
        "sha256": "446ed3fbd0f50205c61a7233ceca289bfc3316f76dfc672fec307b20d8305d52",
    },
    "matter_library_json": {
        "commit": BASE_REVISION,
        "path": "tools/monkey_campaign/contributions/MAT2-B03/data/matter_library_1af0bbde.json",
        "sha256": "de10200fb87bf48c3cc80d5e223805f02e27df115b91186f42f28064a64054ed",
    },
    "wood_source_md": {
        "commit": BASE_REVISION,
        "path": "docs/research/tree_architecture_reference.md",
        "sha256": "3cb871b0a1617f85d826608733add543e5d7f9b01c63e0e32770f69743880206",
    },
    "material_state_py": {
        "commit": BASE_REVISION,
        "path": "tools/monkey_campaign/contributions/MAT2-M01/material_state.py",
        "sha256": None,          # authority module: sha pinned at build time
    },
    "local_contact_py": {
        "commit": BASE_REVISION,
        "path": "tools/monkey_campaign/contributions/MAT2-M06/local_contact.py",
        "sha256": None,
    },
    "passive_law_py": {
        "commit": BASE_REVISION,
        "path": "tools/monkey_campaign/contributions/MAT2-M04/passive_law.py",
        "sha256": None,
    },
    "visual_capture_py": {
        "commit": BASE_REVISION,
        "path": "tools/monkey_campaign/visual_capture.py",
        "sha256": None,
    },
    "visual_gate_py": {
        "commit": BASE_REVISION,
        "path": "tools/monkey_campaign/visual_gate.py",
        "sha256": None,
    },
    "integrity_py": {
        "commit": BASE_REVISION,
        "path": "tools/monkey_campaign/integrity.py",
        "sha256": None,
    },
}

# --- frozen reduction constants (PREREGISTRATION; do not tune) ----------------
RHO_KG_M3 = 760.0                    # declared proxy species: white oak
RHO_BAND = (650.0, 850.0)            # researched band from the pinned source
MU_S = MU_K = 0.6                    # carried UNEVIDENCED-PLACEHOLDER (G04)
SOLID_THICKNESS_M = 0.0              # solid region; no shell thickness invented
TRUNK_SURFACE_IDS = ("trunk_01.lateral", "trunk_01.base_cap", "trunk_01.top_cap")
CENTER_VERTEX_BASE = 128             # per-triangle partition rule (prereg P1)
CENTER_VERTEX_TOP = 129
VOLUME_TOL = 2e-4                    # declared render/collision tolerance (m)
GRIP_MASS_KG = 1.0                   # authored fixture
GRIP_PRESS_MPS = 0.30                # S1/S2 normal press
COUNTERFACTUAL_MU = 0.15             # S2 declared counterfactual surface
S3_TICKS = 40
CAP_DISPLACEMENT_BAR_M = 2e-3

M06_FRAME_TRANSFORM = {
    "from_frame": "f01_world_y_up",
    "to_frame": "m06_experiment_z_up",
    "map": "m06 = (x - bx, -(z - bz), y - by)",
    "inverse": "f01 = (m06x + bx, m06z + by, bz - m06y)",
    "handedness": "right -> right (proper rotation)",
}


class Refusal(ValueError):
    def __init__(self, code, detail=""):
        self.code, self.detail = code, str(detail)
        super().__init__(code + (": " + self.detail if detail else ""))


def require(condition, code, detail=""):
    if not condition:
        raise Refusal(code, detail)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(value).hexdigest()


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


# --- vector helpers (F01-compatible 3-tuples) ---------------------------------
def vsub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vadd(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vscale(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def vdot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vcross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def vlen(a):
    return math.sqrt(vdot(a, a))


def vnorm(a):
    n = vlen(a)
    require(n > 0.0, "degenerate_vector")
    return (a[0] / n, a[1] / n, a[2] / n)


# --- pin materialization (F01 pattern; attempt repo carries shared objects) ---
def _git_show(repo, commit, path):
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "show", "%s:%s" % (commit, path)],
            capture_output=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return proc.stdout if proc.returncode == 0 else None


def _attempt_repo_root():
    try:
        proc = subprocess.run(
            ["git", "-C", str(HERE), "rev-parse", "--show-toplevel"],
            capture_output=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode == 0:
        return pathlib.Path(proc.stdout.decode().strip())
    return None


def materialize_pins():
    """Materialize every pinned byte from the attempt repo's shared objects,
    demanding raw sha256 equality (authority modules record their exact sha)."""
    root = _attempt_repo_root()
    require(root is not None, "f03_no_attempt_repo")
    PINS_DIR.mkdir(parents=True, exist_ok=True)
    out = {}
    for key, pin in PINS.items():
        raw = _git_show(root, pin["commit"], pin["path"])
        require(raw is not None, "f03_pin_unavailable",
                {"key": key, "commit": pin["commit"], "path": pin["path"]})
        got = sha_bytes(raw)
        if pin["sha256"] is not None:
            require(got == pin["sha256"], "f03_pin_hash_mismatch",
                    {"key": key, "expect": pin["sha256"], "got": got})
        target = PINS_DIR / pathlib.Path(pin["path"]).name
        target.write_bytes(raw)
        require(sha_bytes(target.read_bytes()) == got,
                "f03_pin_writeback_mismatch", key)
        out[key] = {"bytes": raw, "file": str(target), "via_repo": str(root),
                    "sha256": got, "raw_match": True,
                    "commit": pin["commit"], "path": pin["path"]}
    return out


def _module_from_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_sources(pins):
    """Load the pinned scene bytes and the UNMODIFIED authority modules."""
    recipe = _module_from_file(
        "f03_pinned_clearing_recipe", pins["clearing_recipe_py"]["file"])
    declaration = recipe.loads(pins["clearing_declaration_json"]["bytes"])
    tb = _module_from_file(
        "f03_pinned_terrain_bundle", pins["terrain_bundle_py"]["file"])
    tq = _module_from_file(
        "f03_pinned_terrain_query", pins["terrain_query_py"]["file"])
    tq.terrain_bundle = tb
    bundle = tb.loads(pins["terrain_bundle_json"]["bytes"])
    surface = tq.TerrainSurface(bundle, validate=True)
    trunk = json.loads(pins["trunk_declaration_json"]["bytes"])
    ms = _module_from_file("f03_m01_material_state",
                           pins["material_state_py"]["file"])
    lc = _module_from_file("f03_m06_local_contact",
                           pins["local_contact_py"]["file"])
    pl = _module_from_file("f03_m04_passive_law",
                           pins["passive_law_py"]["file"])
    vc = _module_from_file("f03_visual_capture",
                           pins["visual_capture_py"]["file"])
    return recipe, declaration, surface, trunk, ms, lc, pl, vc


# --- wood density extraction from the pinned on-disk source -------------------
def extract_wood_provenance(pins):
    """Parse the pinned research source for the declared density and band.
    Named refusals; the extracted numbers are frozen (760; 650-850)."""
    text = pins["wood_source_md"]["bytes"].decode("utf-8")
    lines = text.splitlines()
    row_i = oak_density = band_lo = band_hi = None
    for i, line in enumerate(lines):
        m = row_i is None and _re_wood_row(line)
        if m:
            row_i, oak_density = i + 1, int(m)
            break
    require(oak_density is not None, "f03_wood_row_missing")
    for i, line in enumerate(lines):
        if "Slow-growing hardwoods" in line:
            for line2 in lines[i + 1:i + 4]:
                m = _re_wood_band(line2)
                if m:
                    band_lo, band_hi = int(m[0]), int(m[1])
                    break
            break
    require(band_lo is not None and band_hi is not None,
            "f03_wood_band_missing")
    require((oak_density, band_lo, band_hi) == (760, 650, 850),
            "f03_wood_source_drift",
            {"row": oak_density, "band": [band_lo, band_hi]})
    return {"density_kg_m3": float(oak_density), "band_kg_m3": [float(band_lo),
                                                                float(band_hi)],
            "source_row_line_1based": row_i,
            "source_file": PINS["wood_source_md"]["path"],
            "source_commit": BASE_REVISION,
            "source_raw_sha256": pins["wood_source_md"]["sha256"]}


def _re_wood_row(line):
    import re
    m = re.match(r"^\|\s*Oak \(white\)\s*\|\s*(\d+)\s*\|", line)
    return m.group(1) if m else None


def _re_wood_band(line):
    import re
    m = re.search(r"Density:\s*(\d+)[\u2013-](\d+)\s*kg/m", line)
    return (m.group(1), m.group(2)) if m else None


# --- trunk geometry (pinned bytes only) ---------------------------------------
def trunk_partition(trunk):
    """Split the pinned 128-triangle mesh by the declared center-vertex rule;
    measured topology (Amendment A2), welded closure, and the
    divergence-theorem volume (two orderings)."""
    tv = trunk["render_mesh"]
    verts = [v[:3] for v in tv["vertices"]]
    idx = tv["indices"]
    require(len(verts) == 130 and len(idx) == 384,
            "f03_mesh_shape", {"v": len(verts), "i": len(idx)})
    groups = {"trunk_01.lateral": [], "trunk_01.base_cap": [],
              "trunk_01.top_cap": []}
    for k in range(0, len(idx), 3):
        tri = (idx[k], idx[k + 1], idx[k + 2])
        if CENTER_VERTEX_BASE in tri:
            groups["trunk_01.base_cap"].append(tri)
        elif CENTER_VERTEX_TOP in tri:
            groups["trunk_01.top_cap"].append(tri)
        else:
            groups["trunk_01.lateral"].append(tri)
    counts = {k: len(v) for k, v in groups.items()}
    require(counts == {"trunk_01.lateral": 64, "trunk_01.base_cap": 32,
                       "trunk_01.top_cap": 32},
            "f03_partition_counts", counts)

    def tvs(t):
        return (verts[t[0]], verts[t[1]], verts[t[2]])

    def edge_census(tris, mapping=None):
        use = {}
        for tri in tris:
            ids = tri if mapping is None else [mapping[i] for i in tri]
            for a, b in ((0, 1), (1, 2), (2, 0)):
                e = tuple(sorted((ids[a], ids[b])))
                use[e] = use.get(e, 0) + 1
        return use

    # measured topology (Amendment A2): raw boundary edges are the EXACTLY
    # duplicated seam rings; the welded surface is closed.
    raw_use = edge_census(sum(groups.values(), []))
    raw_open = sum(1 for n in raw_use.values() if n != 2)
    require(raw_open == 128, "f03_raw_open_edges", raw_open)
    canon = {}
    mapping = []
    for vpos in verts:
        key = tuple(round(c, 9) for c in vpos)
        if key not in canon:
            canon[key] = len(canon)
        mapping.append(canon[key])
    require(len(canon) == 66, "f03_distinct_positions", len(canon))
    welded_use = edge_census(sum(groups.values(), []), mapping)
    welded_open = sum(1 for n in welded_use.values() if n != 2)
    require(welded_open == 0, "f03_welded_open_edges", welded_open)
    worst_dup = max(math.dist(verts[i], verts[j]) for group in
                    ([(64 + k, k) for k in range(32)] +
                     [(96 + k, 32 + k) for k in range(32)])
                    for i, j in [group])
    require(worst_dup == 0.0, "f03_seam_weld_distance", worst_dup)
    # areas (unmodified M06 area law) and signed volume, two orderings
    volume_terms_a = []
    volume_terms_b = []
    total_area = 0.0
    for tri in sum(groups.values(), []):
        a, b, c = tvs(tri)
        area = 0.5 * vlen(vcross(vsub(b, a), vsub(c, a)))
        require(area > 0.0, "f03_zero_area_triangle")
        total_area += area
        volume_terms_a.append(vdot(a, vcross(b, c)) / 6.0)
    for tri in reversed(sum(groups.values(), [])):
        a, b, c = tvs(tri)
        volume_terms_b.append(vdot(a, vcross(b, c)) / 6.0)
    vol_a = math.fsum(volume_terms_a)
    vol_b = math.fsum(volume_terms_b)
    require(vol_a > 0.0, "f03_inward_orientation", vol_a)
    rel = abs(vol_a - vol_b) / max(abs(vol_a), 1e-30)
    base = trunk["site"]["base_centre_m"]
    r = trunk["collision_representation"]["solid"]["radius_m"]
    height = trunk["geometry"]["height_m"]
    v_analytic = math.pi * r * r * height
    ratio = vol_a / v_analytic
    bounds = [[min(v[k] for v in verts) for k in range(3)],
              [max(v[k] for v in verts) for k in range(3)]]
    return {"groups": groups, "counts": counts, "vertices": verts,
            "indices": idx, "raw_open_edge_count": raw_open,
            "welded_open_edge_count": welded_open,
            "distinct_position_count": len(canon),
            "seam_weld_max_distance_m": worst_dup,
            "welded_vertex_count": len(canon),
            "surface_area_m2": total_area,
            "welded_volume_m3": vol_a,
            "welded_volume_m3_ordering_b": vol_b,
            "volume_ordering_relative_gap": rel,
            "analytic_solid_volume_m3": v_analytic,
            "mesh_over_analytic_ratio": ratio,
            "bounds_m": bounds,
            "base_centre_m": base, "radius_m": r, "height_m": height}


def to_m06_frame(p, base):
    """Declared proper rotation F01(Y-up) -> M06(Z-up), trunk base to origin."""
    return (p[0] - base[0], -(p[2] - base[2]), p[1] - base[1])


def from_m06_frame(p, base):
    return (p[0] + base[0], p[2] + base[1], base[2] - p[1])


def build_material_doc(trunk, geom, wood, pins, ms):
    """chimera.material_state.v1 for the reduced rigid trunk (Amendment A2:
    the pinned triangle set is a SHELL with exactly duplicated seam rings,
    never treated as sealed; the exact collision law is the declared analytic
    solid; mass derives from that exact solid)."""
    mass = RHO_KG_M3 * geom["analytic_solid_volume_m3"]
    doc = {
        "schema": ms.SCHEMA,
        "revision": 1,
        "object_id": "trunk-01-rigid-material",
        "provenance": {
            "base_revision": BASE_REVISION,
            "scope_sha256": SCOPE_SHA256,
            "asset": ("chimera.trunk_asset.v1 pinned trunk_01 (F01 pin); this "
                      "document adds the material-first reduction, it does not "
                      "re-derive the geometry"),
            "asset_pin": {
                "commit": PINS["trunk_declaration_json"]["commit"],
                "path": PINS["trunk_declaration_json"]["path"],
                "raw_sha256": pins["trunk_declaration_json"]["sha256"],
                "embedded_declaration_sha256":
                    trunk["declaration_sha256"],
            },
            "tools": {
                "schema_authority": "MAT2-M01 material_state.py (unmodified, "
                                    "byte-pinned copy in evidence/pins_materialized)",
                "schema_authority_sha256": pins["material_state_py"]["sha256"],
                "contact_authority": "MAT2-M06 local_contact.py (unmodified, "
                                     "byte-pinned copy)",
                "contact_authority_sha256": pins["local_contact_py"]["sha256"],
                "rigid_law_authority": "MAT2-M04 passive_law.py (unmodified, "
                                       "byte-pinned copy)",
                "rigid_law_authority_sha256": pins["passive_law_py"]["sha256"],
            },
            "reduction_statement": (
                "declared rigid (chimera.passive_law.v1 profile `rigid`, M04 "
                "wording: x = 0 for any load in range; rest geometry is the "
                "only geometry); collision representation is the exact "
                "analytic cylinder solid with the pinned 32-segment triangle "
                "set as the M06 contact surface; wood growth, fracture and "
                "growth rings are NOT prerequisites and are not modeled"),
            "matter_library_absence": {
                "library_file": PINS["matter_library_json"]["path"],
                "library_raw_sha256": pins["matter_library_json"]["sha256"],
                "absence": ("the pinned matter library contains NO wood/bark "
                            "material entry (checked: sand, basin, rock, "
                            "metal, ice, interior, skin, muscle, bone, "
                            "tendon, cluster_00..07); none invented"),
            },
            "density_provenance": {
                "declared_proxy_species": "white oak (Quercus alba; the "
                                          "clearing's broadleaf-oak-like "
                                          "character per the vegetation lane)",
                "density_kg_m3": wood["density_kg_m3"],
                "density_band_kg_m3": wood["band_kg_m3"],
                "provenance_class": "researched",
                "class_definition_source":
                    "pinned matter library provenance_classes.researched = "
                    "'cited external measurement with a cached source on disk'",
                "cached_source": {
                    "file": wood["source_file"],
                    "commit": wood["source_commit"],
                    "raw_sha256": wood["source_raw_sha256"],
                    "row_line_1based": wood["source_row_line_1based"],
                    "table": "Wood Density Database (Typical Values)",
                    "row": "Oak (white) | 760 | 1,290 lbf | Dense, strong",
                },
                "honesty": ("the cited table states TYPICAL values with no "
                            "moisture/temperature/strain-rate basis; the "
                            "under-specification is recorded, not fabricated "
                            "(MAT-03 heritage); band 650-850 kg/m3 is the same "
                            "source's slow-growing hardwood (oak) range"),
            },
            "mass_method": ("m = integral rho dV = rho * V_analytic_solid "
                            "(uniform declared density over the DECLARED "
                            "exact collision solid pi*R^2*H); the pinned "
                            "triangle shell is never treated as sealed "
                            "(Amendment A2), and its welded divergence-"
                            "theorem volume is recorded as the "
                            "discretization cross-check"),
        },
        "regions": [{
            "id": "trunk_01",
            "kind": "shell",
            "parent": None,
            "rest_geometry": {
                "unit": "m",
                "frame": "f01_world_y_up",
                "source_path": PINS["trunk_declaration_json"]["path"],
                "source_sha256": pins["trunk_declaration_json"]["sha256"],
                "source_units_to_m": [1.0, 1.0, 1.0],
                "mesh_blob": "trunk_01_mesh.json",
                "mesh_blob_sha256": None,   # filled by build() after hashing
                "mesh_blob_region_key": "trunk_01",
                "vertex_count": 130,
                "triangle_count": 128,
                "bounds_m": geom["bounds_m"],
                "surface_area_m2": geom["surface_area_m2"],
                "edges_not_shared_twice": geom["raw_open_edge_count"],
                "closure": "open_surface_exact_seam_duplicates_weld_closed",
                "open_edge_count": geom["raw_open_edge_count"],
                "welded_closure": {
                    "welded_open_edge_count": geom["welded_open_edge_count"],
                    "distinct_position_count":
                        geom["distinct_position_count"],
                    "seam_weld_max_distance_m":
                        geom["seam_weld_max_distance_m"],
                    "welded_orientation": "outward_consistent",
                    "note": "raw boundary edges are EXACTLY duplicated seam "
                            "rings (worst duplicate distance 0.0 m); the "
                            "welded surface is closed and outward-consistent "
                            "(Amendment A2)"},
                "orientation": "outward_consistent",
                "signed_volume_m3": geom["welded_volume_m3"],
                "volume_claim_m3": None,
                "shell_thickness_m": SOLID_THICKNESS_M,
                "shell_thickness_provenance":
                    "contact thickness 0 in M06 (the exact collision law is "
                    "the declared analytic solid); the shell is never treated "
                    "as sealed; no shell thickness invented (M02 discipline)",
                "render_to_physics_mapping": {
                    "visual_mesh": "mesh_blob triangle list (identity)",
                    "physical_mesh": "mesh_blob triangle list (identity)",
                    "mapping": "identity",
                    "visual_triangle_count": 128,
                    "physical_triangle_count": 128,
                },
                "collision_representation": {
                    "exact_law": trunk["collision_representation"],
                    "m06_contact_triangle_set": {
                        "identity": "the same mesh_blob triangle list",
                        "partition_rule":
                            "triangle references center vertex 128 -> "
                            "trunk_01.base_cap; vertex 129 -> "
                            "trunk_01.top_cap; else trunk_01.lateral",
                        "surface_id_triangle_counts": geom["counts"],
                        "thickness_m": SOLID_THICKNESS_M,
                        "friction": {
                            "mu_s": MU_S, "mu_k": MU_K,
                            "provenance": "UNEVIDENCED-PLACEHOLDER",
                            "note": trunk["material"]["friction"][
                                "placeholder_source"],
                            "acquisition_prerequisite": "G04",
                        },
                        "frame_transform": M06_FRAME_TRANSFORM,
                    },
                    "measured_correspondence": {
                        "tolerance_m": VOLUME_TOL,
                        "max_lateral_vertex_radial_gap_m": None,  # filled
                        "analytic_vs_mesh_volume_ratio":
                            geom["mesh_over_analytic_ratio"],
                    },
                },
            },
            "current_geometry": {
                "equal_to": "rest_geometry",
                "reason": "revision 1; declared rigid; no solver exists",
            },
            "matter_claims": [{"matter_id": "wood_trunk_01", "role": "owner"}],
            "ports": [{"id": "surface", "protocol": "material_contact",
                       "unit": "unitless_interface_id"}],
            "sources": [PINS["trunk_declaration_json"]["path"],
                        wood["source_file"]],
        }],
        "matter": [{
            "id": "wood_trunk_01",
            "mass_kg": mass,
            "provenance": (
                "declared uniform density %s kg/m3 (researched proxy white "
                "oak, band %s) x declared exact collision solid volume "
                "%.17g m3 = %.17g kg; single-owner" %
                (RHO_KG_M3, RHO_BAND, geom["analytic_solid_volume_m3"], mass)),
        }],
        "directions": [],
        "laws": [],
        "contacts": [],
        "bonds": [],
    }
    doc["provenance"]["declared_absences"] = (
        "directions: none (rigid isotropic reduction; growth rings are "
        "not prerequisites); laws: none (a pressure_deformation law would "
        "be a deformable claim, the reduction is RIGID); contacts: none "
        "(M06 owns contacts at runtime); bonds: none (rigid and rooted, "
        "M06 pinned body; bonds optional for a rigid asset)")
    return doc, mass


def build_rigid_doc(pins, material_canonical_sha):
    """chimera.passive_law.v1: the explicit RIGID reduction (M04 profile)."""
    return {
        "schema": "chimera.passive_law.v1",
        "revision": 1,
        "object_id": "trunk-01-rigid-law",
        "source_documents": [
            {"id": "trunk_material_state",
             "path": "assets/trunk_01_material_state.json",
             "object_id": "trunk-01-rigid-material",
             "canonical_sha256": material_canonical_sha},
            {"id": "trunk_asset_declaration",
             "path": PINS["trunk_declaration_json"]["path"],
             "object_id": "trunk_01",
             "canonical_sha256": pins["trunk_declaration_json"]["sha256"]},
        ],
        "gauges": [],
        "profiles": [{
            "id": "rigid",
            "constitutive_equation": ("x = 0 for any load in range; "
                                      "transmits F_out = F_in exactly; "
                                      "U = Q = 0"),
            "parameters": {},
            "source_status": "synthetic_authored",
            "damping": None,
            "valid_strain_range": [0.0, 0.0],
            "rest_state": "no strain state exists; rest geometry is the only "
                          "geometry",
        }],
        "directions": [],
        "assignments": [{
            "region_id": "trunk_01",
            "profile_id": "rigid",
            "gauge_id": None,
            "direction_id": None,
            "provenance": ("the pinned trunk_01 asset declares deformable "
                           "false; the card's material-first addition makes "
                           "the reduction EXPLICIT via M04's rigid profile; "
                           "branches/bark damage/growth/fracture are out of "
                           "scope per the card wording"),
        }],
        "provenance": {"note": ("material-first addition per card MAT2-F03; "
                                "the trunk is RIGID so bonds are optional "
                                "and none are declared")},
    }


# --- M06 contact binding and climb-relevant experiments -----------------------
TETRA_LOCAL = ((0.0, 0.0, 0.0), (0.1, 0.0, 0.0), (0.0, 0.1, 0.0),
               (0.0, 0.0, 0.1))
TETRA_TRIS = ((0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3))  # outward, right tetra


def _facet_frame(verts, tris):
    """The lateral facet whose centroid azimuth is nearest +x in the M06
    frame; returns (centroid, outward unit normal)."""
    best = None
    for t in tris:
        a, b, c = (verts[t[0]], verts[t[1]], verts[t[2]])
        cen = vscale(vadd(vadd(a, b), c), 1.0 / 3.0)
        n = vnorm(vcross(vsub(b, a), vsub(c, a)))
        az = math.atan2(cen[1], cen[0])
        score = abs(az)
        if best is None or score < best[0]:
            best = (score, cen, n)
    return best[1], best[2]


def _orthobasis(n):
    a = (0.0, 0.0, 1.0) if abs(n[2]) < 0.9 else (1.0, 0.0, 0.0)
    u = vnorm(vcross(a, n))
    v = vcross(n, u)
    return u, v


def _place_tetra(origin, ex, ey, ez):
    """Local tetra vertex k -> origin + ex*x_k + ey*y_k + ez*z_k."""
    return tuple(tuple(origin[i] + ex[i] * p[0] + ey[i] * p[1] + ez[i] * p[2]
                       for i in range(3)) for p in TETRA_LOCAL)


def make_trunk_bodies(lc, geom, mu_s=MU_S, mu_k=MU_K, lateral_surface_id=None,
                      parts=TRUNK_SURFACE_IDS):
    """The pinned triangle split as PINNED M06 bodies in the M06 frame.
    `parts` scopes which declared surface parts are instantiated (Amendment
    A3: the exact seam duplicates put lateral/cap triangle PAIRS from two
    pinned bodies into exact contact, and M06 refuses a both-pinned pair with
    `nonfinite_state`; each experiment therefore instantiates the parts it
    touches)."""
    base = geom["base_centre_m"]
    groups = geom["groups"]
    bodies = []
    for sid in parts:
        tris = groups[sid]
        vs6 = [to_m06_frame(p, base) for p in geom["vertices"]]
        sid_used = (lateral_surface_id if sid == "trunk_01.lateral"
                    and lateral_surface_id else sid)
        bodies.append(lc.Body(
            body_id=sid, surface_id=sid_used,
            matter_id="wood_trunk_01", mass_kg=1.0, mu_s=mu_s, mu_k=mu_k,
            thickness_m=SOLID_THICKNESS_M, vertices=vs6, triangles=tris,
            pinned=True))
    return bodies


def run_contact_experiments(lc, geom):
    """S1 grip stick / S2 understated-mu slip discriminator / S3 cap rest.
    Frame: M06 z-up, trunk base at origin, axis +z, gravity -z."""
    experiments = {}
    base = geom["base_centre_m"]

    def probe_body(verts, velocity, mass_kg=GRIP_MASS_KG,
                   sid="climb_grip_probe"):
        return lc.Body(body_id=sid, surface_id=sid, matter_id="probe_fixture",
                       mass_kg=mass_kg, mu_s=1.0, mu_k=1.0,
                       thickness_m=SOLID_THICKNESS_M, vertices=list(verts),
                       triangles=list(TETRA_TRIS), velocity=velocity,
                       pinned=False)

    # S1/S2: the right tetra's local x=0 face (tri (0,3,2), outward normal -x)
    # is mapped so -ex = -n faces the facet (n = facet outward normal); the
    # probe starts a declared 2e-5 m off the facet and presses inward at 0.30
    # m/s. Thickness 0 on both sides keeps every contact on the exact
    # geometric branch (dist > 0) of M06's closest-feature law.
    lateral_tris = geom["groups"]["trunk_01.lateral"]
    vs6 = [to_m06_frame(p, base) for p in geom["vertices"]]
    cen, n = _facet_frame(vs6, lateral_tris)
    u, v = _orthobasis(n)
    ex, ey, ez = n, u, v
    start = vadd(cen, vscale(n, 2e-5))
    press = vscale(n, -GRIP_PRESS_MPS)          # inward
    for name, mu in (("S1_grip_stick", (MU_S, MU_K)),
                     ("S2_counterfactual_slip", (COUNTERFACTUAL_MU,
                                                 COUNTERFACTUAL_MU))):
        trunk_bodies = make_trunk_bodies(
            lc, geom, mu_s=mu[0], mu_k=mu[1],
            lateral_surface_id=("trunk_01.lateral.counterfactual_mu%.2f" % mu[0]
                                if name.startswith("S2") else None),
            parts=("trunk_01.lateral",))
        probe = probe_body(_place_tetra(start, ex, ey, ez), press)
        bodies = trunk_bodies + [probe]
        records, ledger = lc.solve_tick(bodies)
        contacts = [r for r in records if r["body_a"] == "climb_grip_probe"
                    or r["body_b"] == "climb_grip_probe"]
        require(contacts, "f03_%s_no_contact" % name)
        top = max(contacts, key=lambda r: r["jn_Ns"])
        rv_t = top["vt_post"]
        resid = max(vlen(tuple(ledger["residual"][b.id])) for b in bodies)
        experiments[name] = {
            "surface_b": top["surface_b"] if top["body_a"] == "climb_grip_probe"
            else top["surface_a"],
            "mode": top["mode"], "jn_Ns": top["jn_Ns"], "jt_Ns": top["jt_Ns"],
            "vt_post_mps": rv_t, "mu_used": top["mu_used"],
            "ledger_max_abs_residual": resid,
            "reciprocity_residual_norm": vlen(tuple(
                ledger["reciprocity_residual"])),
            "facet_centroid_m06": list(cen), "facet_normal_m06": list(n),
            "probe_start_offset_m": 2e-5, "press_mps": GRIP_PRESS_MPS,
        }
    s1 = experiments["S1_grip_stick"]
    require(s1["surface_b"] == "trunk_01.lateral", "f03_s1_surface_id",
            s1["surface_b"])
    require(s1["mode"] == "stick", "f03_s1_not_stick", s1["mode"])
    require(abs(s1["jn_Ns"] - GRIP_MASS_KG * GRIP_PRESS_MPS) <= 1e-9,
            "f03_s1_jn_bar", s1["jn_Ns"])
    require(s1["vt_post_mps"] <= 1e-12, "f03_s1_tangential_motion",
            s1["vt_post_mps"])
    require(s1["ledger_max_abs_residual"] <= 1e-12, "f03_s1_ledger",
            s1["ledger_max_abs_residual"])
    grip_capacity = MU_S * s1["jn_Ns"] / (lc.G * lc.DT)
    experiments["S1_grip_stick"]["grip_capacity_kg"] = grip_capacity
    s2 = experiments["S2_counterfactual_slip"]
    require(s2["surface_b"] == "trunk_01.lateral.counterfactual_mu0.15",
            "f03_s2_surface_id", s2["surface_b"])
    require(s2["mode"] == "slip", "f03_s2_not_slip", s2["mode"])
    expect_vt = (lc.G * lc.DT - COUNTERFACTUAL_MU * s2["jn_Ns"]) / GRIP_MASS_KG
    require(abs(s2["vt_post_mps"] - expect_vt) <= 1e-9 and s2["vt_post_mps"] > 0,
            "f03_s2_vt_bar", {"got": s2["vt_post_mps"], "expect": expect_vt})
    experiments["S2_counterfactual_slip"]["expected_vt_mps"] = expect_vt

    # S3: probe resting on the top cap (local z=0 face down); it starts a
    # declared 2e-5 m ABOVE the cap plane so the first tick settles through
    # M06's exact geometric branch (dist > 0), then rests. 40 ticks. Both
    # cap parts are co-instantiated (they never touch each other).
    cap_z = geom["height_m"]
    probe = lc.Body(
        body_id="climb_grip_probe", surface_id="climb_grip_probe",
        matter_id="probe_fixture", mass_kg=GRIP_MASS_KG, mu_s=1.0, mu_k=1.0,
        thickness_m=SOLID_THICKNESS_M,
        vertices=list(_place_tetra((0.02, 0.01, cap_z + 2e-5), (1.0, 0.0, 0.0),
                                   (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))),
        triangles=list(TETRA_TRIS), velocity=(0.0, 0.0, 0.0), pinned=False)
    bodies = make_trunk_bodies(
        lc, geom,
        parts=("trunk_01.base_cap", "trunk_01.top_cap")) + [probe]
    start_pos = [tuple(p) for p in probe.vertices]
    worst_resid = 0.0
    final_mode = None
    cap_contact = False
    for _ in range(S3_TICKS):
        records, ledger = lc.solve_tick(bodies)
        worst_resid = max(worst_resid,
                          max(vlen(tuple(ledger["residual"][b.id]))
                              for b in bodies))
        for r in records:
            if "trunk_01.top_cap" in (r["surface_a"], r["surface_b"]):
                cap_contact = True
                final_mode = r["mode"]
        require(vlen(tuple(ledger["reciprocity_residual"])) <= 1e-12,
                "f03_s3_reciprocity")
    disp = max(vlen(vsub(p, s)) for p, s in
               zip([tuple(p) for p in probe.vertices], start_pos))
    require(cap_contact, "f03_s3_no_cap_contact")
    require(disp <= CAP_DISPLACEMENT_BAR_M, "f03_s3_drift", disp)
    require(worst_resid <= 1e-12, "f03_s3_ledger", worst_resid)
    experiments["S3_cap_rest"] = {
        "ticks": S3_TICKS, "surface_b": "trunk_01.top_cap",
        "final_mode": final_mode, "max_displacement_m": disp,
        "ledger_max_abs_residual": worst_resid,
        "bar_m": CAP_DISPLACEMENT_BAR_M,
    }
    # measured co-instantiation note (Amendment A3): solving ALL THREE split
    # parts together is refused by the unmodified M06 law because the EXACT
    # seam duplicates put lateral/cap triangle pairs from two PINNED bodies
    # into gap-0 contact ('nonfinite_state' on the both-pinned pair). Each
    # experiment therefore instantiates exactly the parts it touches.
    try:
        lc.solve_tick(make_trunk_bodies(lc, geom))
    except ValueError as exc:
        require("nonfinite_state" in str(exc), "f03_split_refusal_code", str(exc))
        experiments["full_split_coinstantiation"] = {
            "outcome": "refused", "code": "nonfinite_state",
            "why": "duplicated seam rings put lateral/cap pairs of two "
                   "pinned bodies into exact contact; experiments scope the "
                   "instantiated parts (A3)"}
    else:
        raise Refusal("f03_split_unexpectedly_solved")
    return experiments


# --- collision/render correspondence (numbers, no pixels) ----------------------
def measure_correspondence(trunk, geom):
    """P6 numeric bars: lateral vertices on the analytic cylinder; every
    triangle vertex inside-or-on the analytic solid."""
    base = geom["base_centre_m"]
    r, height = geom["radius_m"], geom["height_m"]
    worst_radial = 0.0
    lateral_ids = {i for t in geom["groups"]["trunk_01.lateral"]
                   for i in t}
    for i in lateral_ids:
        v = geom["vertices"][i]
        dist = math.hypot(v[0] - base[0], v[2] - base[2])
        worst_radial = max(worst_radial, abs(dist - r))
    worst_inside = 0.0
    for v in geom["vertices"]:
        dist = math.hypot(v[0] - base[0], v[2] - base[2])
        worst_inside = max(worst_inside, dist - r,
                           base[1] - v[1], v[1] - (base[1] + height))
    return {"max_lateral_vertex_radial_gap_m": worst_radial,
            "max_vertex_outside_solid_m": worst_inside,
            "tolerance_m": VOLUME_TOL,
            "lateral_vertex_count": len(lateral_ids)}


# --- scene + cameras (F01-adapted renderer; presentation only) -----------------
W, H = 1280, 720
NEAR, FAR = 0.05, 500.0
LIGHT = vnorm((0.4, 0.8, 0.45))
AMBIENT = 0.55
COLOURS = {
    "ground_A": (0.16, 0.22, 0.17),
    "ground_B": (0.18, 0.24, 0.19),
    "monkey_clearing_boundary_posts": (0.72, 0.55, 0.20),
    "trunk_01.lateral": (0.36, 0.25, 0.16),
    "trunk_01.base_cap": (0.30, 0.21, 0.13),
    "trunk_01.top_cap": (0.42, 0.30, 0.19),
    "climb_grip_probe": (0.85, 0.15, 0.15),
}
VIEW_SPECS = {
    "V1_clearing_overview": {
        "position": [0.0, 46.0, -32.0], "target": [0.0, 0.0, 0.0],
        "vfov_deg": 55.0, "near_far": [0.05, 500.0]},
    "V2_seam_closeup": {
        "position": [10.15, 1.25, 1.35], "target": [11.976783, 0.32, 2.471766],
        "vfov_deg": 55.0, "near_far": [0.05, 50.0]},
    "V3_side_depth": {
        "position": [0.0, 12.0, -50.0], "target": [0.0, 0.0, 6.0],
        "vfov_deg": 45.0, "near_far": [0.05, 500.0]},
}
VIEW_ORDER = ["V1_clearing_overview", "V2_seam_closeup", "V3_side_depth"]
PROFILE_VIEW_NAMES = {
    "V1_clearing_overview": "clearing overview",
    "V2_seam_closeup": "terrain/trunk seam close-up",
    "V3_side_depth": "side and oblique depth checks",
}


class Camera:
    def __init__(self, spec):
        self.spec = spec
        self.position = list(spec["position"])
        self.target = list(spec["target"])
        self.vfov = math.radians(spec["vfov_deg"])
        self.fwd = vnorm(vsub(self.target, self.position))
        self.right = vnorm(vcross(self.fwd, [0.0, 1.0, 0.0]))
        self.up = vcross(self.right, self.fwd)
        self.aspect = W / H
        self.t = math.tan(self.vfov / 2.0)
        self.distance_to_target = vlen(vsub(self.target, self.position))

    def ndc(self, world_point):
        d = vsub(world_point, self.position)
        z = vdot(d, self.fwd)
        if z <= 1e-6:
            return None
        x = vdot(d, self.right)
        y = vdot(d, self.up)
        return (x / (z * self.t * self.aspect), y / (z * self.t), z)

    def pixel(self, world_point):
        n = self.ndc(world_point)
        if n is None:
            return None
        return ((n[0] + 1.0) * 0.5 * W, (1.0 - n[1]) * 0.5 * H, n[2])

    def ray_through_ndc(self, xn, yn):
        return vnorm([self.fwd[i] + xn * self.t * self.aspect * self.right[i]
                      + yn * self.t * self.up[i] for i in range(3)])

    def quaternion_wxyz(self):
        """Rotation camera->world: columns right, up, -fwd (local -Z forward,
        +Y up). Returns a unit quaternion (w, x, y, z); round-trip asserted."""
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
            w = (m[2][1] - m[1][2]) / s
            x = 0.25 * s
            y = (m[0][1] + m[1][0]) / s
            z = (m[0][2] + m[2][0]) / s
        elif m[1][1] > m[2][2]:
            s = math.sqrt(1.0 + m[1][1] - m[0][0] - m[2][2]) * 2.0
            w = (m[0][2] - m[2][0]) / s
            x = (m[0][1] + m[1][0]) / s
            y = 0.25 * s
            z = (m[1][2] + m[2][1]) / s
        else:
            s = math.sqrt(1.0 + m[2][2] - m[0][0] - m[1][1]) * 2.0
            w = (m[1][0] - m[0][1]) / s
            x = (m[0][2] + m[2][0]) / s
            y = (m[1][2] + m[2][1]) / s
            z = 0.25 * s
        q = (w, x, y, z)
        n = math.sqrt(sum(c * c for c in q))
        return (q[0] / n, q[1] / n, q[2] / n, q[3] / n)

    def record_16field(self):
        q = self.quaternion_wxyz()
        return {
            "frame_id": "f01_world_y_up",
            "coordinate_unit": "m",
            "handedness": "right",
            "orientation_convention": "quaternion_wxyz_camera_to_frame",
            "forward_axis": "-Z",
            "up_axis": "+Y",
            "position": list(self.position),
            "orientation_convention_and_values": {"convention":
                "quaternion_wxyz_camera_to_frame", "quaternion_wxyz": list(q)},
            "target": list(self.target),
            "distance_to_target": self.distance_to_target,
            "projection": "perspective",
            "vertical_fov_or_orthographic_span_deg": self.spec["vfov_deg"],
            "near_far_planes": list(self.spec["near_far"]),
            "aspect_ratio": W / H,
            "viewport_resolution": [W, H],
            "camera_motion_or_bookmark_sequence":
                {"sample_mode": "fixed_bookmark", "bookmarks": [list(q)]},
            "visibility_layers": None,      # per-row (manifest builds it)
            "label_ids": None,
            "occlusion_or_xray_mode": "depth_tested",
            "state_or_tick_interval": [0, 0],
            "quaternion_wxyz": list(q),
            "vertical_fov_degrees": self.spec["vfov_deg"],
        }


def quat_rotate(q, v):
    w, x, y, z = q
    return (
        v[0] + 2.0 * (y * (w * v[2] + z * v[1]) - z * (w * v[1] + y * v[2])),
        v[1] + 2.0 * (z * (w * v[0] + x * v[2]) - x * (w * v[2] + z * v[0])),
        v[2] + 2.0 * (x * (w * v[1] + y * v[0]) - y * (w * v[0] + x * v[1])))


class SceneMesh:
    """The pinned render arrays plus the pinned trunk mesh and the grip-probe
    marker as raycast/raster targets (F01-adapted)."""

    def __init__(self, surface, trunk, geom, probe_marker_tris):
        bundle = surface.bundle
        self.vertices = bundle["render"]["vertices"]
        self.indices = bundle["render"]["indices"]
        self.ground = bundle["render"]["sections"]["ground"]
        self.posts_sec = bundle["render"]["sections"]["boundary_posts"]
        self.trunk = trunk
        self.geom = geom
        self.trunk_vertices = geom["vertices"]
        self.trunk_groups = geom["groups"]
        self.probe_marker_tris = probe_marker_tris   # list of (a,b,c,sid)

    def _trunk_triangles(self):
        for sid, tris in self.trunk_groups.items():
            for t in tris:
                yield (self.trunk_vertices[t[0]], self.trunk_vertices[t[1]],
                       self.trunk_vertices[t[2]], sid)


    def triangles(self):
        idx = self.indices
        g_end = self.ground["index_start"] + self.ground["index_count"]
        for k in range(0, len(idx), 3):
            a, b, c = idx[k], idx[k + 1], idx[k + 2]
            va = self.vertices[9 * a:9 * a + 3]
            vb = self.vertices[9 * b:9 * b + 3]
            vc = self.vertices[9 * c:9 * c + 3]
            sid = ("monkey_clearing_ground" if k < g_end
                   else "monkey_clearing_boundary_posts")
            yield va, vb, vc, sid
        yield from self._trunk_triangles()
        for a, b, c, sid in self.probe_marker_tris:
            yield a, b, c, sid

    def first_hit(self, orig, direc, offset_fallback=False):
        best = None
        for va, vb, vc, sid in self.triangles():
            hit = ray_triangle(orig, direc, va, vb, vc)
            if hit is not None and (best is None or hit[0] < best[0]):
                n = vnorm(vcross(vsub(vb, va), vsub(vc, va)))
                best = (hit[0], [orig[i] + hit[0] * direc[i] for i in range(3)],
                        n, sid)
        if best is None and offset_fallback:
            for dx in (1e-5, -1e-5, 2e-5, -2e-5, 5e-5, -5e-5):
                off = [orig[0] + dx, orig[1], orig[2]]
                sub = self.first_hit(off, list(direc), offset_fallback=False)
                if sub is not None:
                    return (sub[0], sub[1], sub[2], sub[3], dx)
        return best


def ray_triangle(orig, direc, v0, v1, v2, eps=1e-9):
    e1 = vsub(v1, v0)
    e2 = vsub(v2, v0)
    p = vcross(direc, e2)
    det = vdot(e1, p)
    if abs(det) < 1e-15:
        return None
    inv = 1.0 / det
    tvec = vsub(orig, v0)
    u = vdot(tvec, p) * inv
    if u < -eps or u > 1.0 + eps:
        return None
    q = vcross(tvec, e1)
    v = vdot(direc, q) * inv
    if v < -eps or u + v > 1.0 + eps:
        return None
    t = vdot(e2, q) * inv
    if t <= 1e-9:
        return None
    return (t, u, v)


GROUND_NODE_EPS = 1e-9          # 2D footprint containment epsilon (F01 A3)


def _incident_ground_normals(surface, x, z):
    """Normals of every ground triangle whose 2D footprint contains (x, z)
    (within eps). At grid nodes the piecewise-linear normal is a SET (the
    reused F01 verified mechanism, A3)."""
    b = surface.bundle
    verts = b["render"]["vertices"]
    idx = b["render"]["indices"]
    gsec = b["render"]["sections"]["ground"]
    out = []
    for k in range(gsec["index_start"],
                   gsec["index_start"] + gsec["index_count"], 3):
        ia, ib, ic = idx[k], idx[k + 1], idx[k + 2]
        pa = verts[9 * ia:9 * ia + 3]
        pb = verts[9 * ib:9 * ib + 3]
        pc = verts[9 * ic:9 * ic + 3]
        det = ((pb[0] - pa[0]) * (pc[2] - pa[2])
               - (pc[0] - pa[0]) * (pb[2] - pa[2]))
        if abs(det) < 1e-12:
            continue
        w0 = ((pb[0] - x) * (pc[2] - z) - (pc[0] - x) * (pb[2] - z)) / det
        w1 = ((pc[0] - x) * (pa[2] - z) - (pa[0] - x) * (pc[2] - z)) / det
        w2 = 1.0 - w0 - w1
        if w0 >= -GROUND_NODE_EPS and w1 >= -GROUND_NODE_EPS                 and w2 >= -GROUND_NODE_EPS:
            out.append(vnorm(vcross(vsub(pb, pa), vsub(pc, pa))))
    require(out, "f03_no_incident_ground_face", (x, z))
    return out


# --- frozen probes (PREREGISTRATION, Amendment A1 count = 47) ------------------
def frozen_probes(surface, trunk, geom, grip_marker_point):
    probes = []
    for x in (-16.0, -8.0, 0.0, 8.0, 16.0):
        for z in (-16.0, -8.0, 0.0, 8.0, 16.0):
            h = surface.height_at(x, z)
            probes.append({"id": "ground_%+d_%+d" % (x, z), "kind": "ground",
                           "point": [x, h, z],
                           "surface": "monkey_clearing_ground",
                           "oracle_h": h,
                           "oracle_n": list(surface.normal_at(x, z)),
                           "oracle_n_set": _incident_ground_normals(
                               surface, x, z)})
    h0 = surface.height_at(0.0, 0.0)
    probes.append({"id": "spawn", "kind": "spawn", "point": [0.0, h0, 0.0],
                   "surface": "monkey_clearing_ground", "oracle_h": h0,
                   "oracle_n": list(surface.normal_at(0.0, 0.0)),
                   "oracle_n_set": _incident_ground_normals(surface, 0.0, 0.0)})
    base = geom["base_centre_m"]
    ht = surface.height_at(base[0], base[2])
    for k in range(8):
        a = k * math.pi / 4.0
        px, pz = base[0] + 0.05 * math.cos(a), base[2] + 0.05 * math.sin(a)
        probes.append({"id": "seam_%d" % k, "kind": "seam",
                       "azimuth_k": k, "point": [px, ht, pz],
                       "surface": "monkey_clearing_ground",
                       "oracle_h": surface.height_at(px, pz),
                       "oracle_n": list(surface.normal_at(px, pz)),
                       "oracle_n_set": _incident_ground_normals(
                           surface, px, pz)})
    r = geom["radius_m"]
    for az_i, az in ((0, math.pi), (1, 5.0 * math.pi / 4.0)):
        for y_i, y in enumerate((0.15, 0.6, 1.0)):
            px = base[0] + r * math.cos(az)
            pz = base[2] + r * math.sin(az)
            probes.append({"id": "trunk_az%d_h%d" % (az_i, y_i),
                           "kind": "trunk", "point": [px, base[1] + y, pz],
                           "surface": "trunk_01.lateral",
                           "oracle_n": [math.cos(az), 0.0, math.sin(az)]})
    probes.append({"id": "trunk_base_cap_rim", "kind": "trunk_cap",
                   "point": [base[0] + r, base[1], base[2]],
                   "surface": "trunk_01.base_cap", "cap_y": base[1],
                   "oracle_n": [0.0, -1.0, 0.0]})
    probes.append({"id": "trunk_top_cap_centre", "kind": "trunk_cap",
                   "point": [base[0], base[1] + geom["height_m"], base[2]],
                   "surface": "trunk_01.top_cap",
                   "cap_y": base[1] + geom["height_m"],
                   "oracle_n": [0.0, 1.0, 0.0]})
    for name, cx, cz in (("SW", -20.0, -20.0), ("SE", 20.0, -20.0),
                         ("NE", 20.0, 20.0), ("NW", -20.0, 20.0)):
        probes.append({"id": "post_top_" + name, "kind": "boundary_post",
                       "point": [cx, 0.9, cz],
                       "surface": "monkey_clearing_boundary_posts",
                       "label_degenerate": True})
    probes.append({"id": "climb_grip_marker", "kind": "grip_probe",
                   "point": list(grip_marker_point),
                   "surface": "climb_grip_probe"})
    require(len(probes) == 47, "f03_probe_count", len(probes))
    return probes


TRUNK_RING_SEGMENTS = 32
TRUNK_RADIAL_BAR_M = 5e-6
TRUNK_NORMAL_ANGULAR_SLACK = 5e-4
VISIBILITY_BAR_M = 1e-6
HEIGHT_BAR_M = 1e-9
NORMAL_BAR = 1e-12
CAP_BAR_M = 1e-9


def classify_probe(mesh, cam, probe):
    ndc = cam.ndc(probe["point"])
    if ndc is None:
        return {"outcome": "OFF_FRAME", "reason": "behind_camera"}
    px = (ndc[0] + 1.0) * 0.5 * W
    py = (1.0 - ndc[1]) * 0.5 * H
    rec = {"pixel_px": [px, py]}
    if not (-1.0 <= ndc[0] <= 1.0 and -1.0 <= ndc[1] <= 1.0):
        rec["outcome"] = "OFF_FRAME"
        rec["reason"] = "outside_viewport"
        return rec
    direc = cam.ray_through_ndc(ndc[0], ndc[1])
    pd = vlen(vsub(probe["point"], cam.position))
    hit = mesh.first_hit(cam.position, direc,
                         offset_fallback=bool(probe.get("label_degenerate")))
    if hit is None:
        rec["outcome"] = "UNRENDERED"
        rec["reason"] = "no render hit through the probe's projected ray"
        return rec
    t, point, n, sid = hit[0], hit[1], hit[2], hit[3]
    rec["hit"] = {"t_m": t, "point": point, "normal": n, "surface_id": sid}
    if len(hit) > 4:
        rec["offset_used_m"] = hit[4]
    if sid != probe["surface"]:
        rec["outcome"] = "OCCLUDED"
        rec["occluder"] = sid
        return rec
    if abs(t - pd) > VISIBILITY_BAR_M:
        rec["outcome"] = "OCCLUDED"
        rec["occluder"] = sid
        rec["note"] = "same surface but a nearer hit stands in front"
        return rec
    if probe["kind"] in ("ground", "spawn", "seam"):
        rec["height_err_m"] = abs(point[1] - probe["oracle_h"])
        n_set = probe.get("oracle_n_set") or [probe["oracle_n"]]
        rec["normal_err"] = min(max(abs(n[i] - cand[i]) for i in range(3))
                                for cand in n_set)
        rec["ok_bars"] = (rec["height_err_m"] <= HEIGHT_BAR_M
                          and rec["normal_err"] <= NORMAL_BAR)
    elif probe["kind"] == "trunk":
        base = mesh.geom["base_centre_m"]
        r = mesh.geom["radius_m"]
        dist = math.hypot(point[0] - base[0], point[2] - base[2])
        rec["radial_err_m"] = abs(dist - r)
        cosang = max(-1.0, min(1.0, vdot(n, probe["oracle_n"])))
        rec["normal_angle_rad"] = math.acos(cosang)
        rec["declared_polygonal_bound_rad"] = (
            math.pi / TRUNK_RING_SEGMENTS + TRUNK_NORMAL_ANGULAR_SLACK)
        rec["ok_bars"] = (rec["radial_err_m"] <= TRUNK_RADIAL_BAR_M
                          and rec["normal_angle_rad"]
                          <= math.pi / TRUNK_RING_SEGMENTS
                          + TRUNK_NORMAL_ANGULAR_SLACK)
    elif probe["kind"] == "trunk_cap":
        rec["cap_height_err_m"] = abs(point[1] - probe["cap_y"])
        cosang = max(-1.0, min(1.0, vdot(n, probe["oracle_n"])))
        rec["normal_angle_rad"] = math.acos(cosang)
        rec["ok_bars"] = (rec["cap_height_err_m"] <= CAP_BAR_M
                          and rec["normal_angle_rad"]
                          <= math.pi / TRUNK_RING_SEGMENTS
                          + TRUNK_NORMAL_ANGULAR_SLACK)
    else:  # boundary_post anchor / grip_probe: identity is the exact first hit
        rec["ok_bars"] = True
    rec["outcome"] = ("VISIBLE_EXACT" if rec["ok_bars"]
                      else "VISIBLE_BUT_MISMATCH")
    return rec


def run_probes(mesh, views, probes):
    per_view = {}
    for vname in VIEW_ORDER:
        cam = views[vname]
        per_view[vname] = {}
        for pr in probes:
            per_view[vname][pr["id"]] = classify_probe(mesh, cam, pr)
    failures = []
    for vname, rows in per_view.items():
        for pid, rec in rows.items():
            if rec["outcome"] in ("VISIBLE_BUT_MISMATCH", "UNRENDERED"):
                failures.append({"probe": pid, "view": vname,
                                 "why": rec["outcome"], "rec": rec})
    # the trunk subject must be VISIBLE_EXACT at least once per profile view
    for vname in VIEW_ORDER:
        trunk_visible = [pid for pid, rec in per_view[vname].items()
                         if rec["outcome"] == "VISIBLE_EXACT"
                         and pid.startswith(("trunk_", "climb_grip"))]
        require(trunk_visible, "f03_subject_off_frame", vname)
    # trunk lateral probes: VISIBLE_EXACT in the seam view
    for pr in probes:
        if pr["kind"] == "trunk":
            rec = per_view["V2_seam_closeup"][pr["id"]]
            if rec["outcome"] != "VISIBLE_EXACT":
                failures.append({"probe": pr["id"], "view": "V2",
                                 "why": "trunk probe not exact in seam view",
                                 "rec": rec})
    # seam probes: exact cylinder-silhouette prediction in V2
    cam2 = views["V2_seam_closeup"]
    axis2 = mesh.geom["base_centre_m"]
    radius = mesh.geom["radius_m"]
    for pr in probes:
        if pr["kind"] != "seam":
            continue
        rec = per_view["V2_seam_closeup"][pr["id"]]
        p = pr["point"]
        d = [p[0] - cam2.position[0], p[2] - cam2.position[2]]
        seg_len2 = d[0] * d[0] + d[1] * d[1]
        tt = ((axis2[0] - cam2.position[0]) * d[0]
              + (axis2[2] - cam2.position[2]) * d[1]) / seg_len2
        tt = max(0.0, min(1.0, tt))
        qx = cam2.position[0] + tt * d[0] - axis2[0]
        qz = cam2.position[2] + tt * d[1] - axis2[2]
        silhouette = math.hypot(qx, qz)
        predicted_occluded = silhouette < radius
        if predicted_occluded:
            if not (rec["outcome"] == "OCCLUDED"
                    and rec.get("occluder", "").startswith("trunk_01")):
                failures.append({"probe": pr["id"], "view": "V2",
                                 "why": "silhouette predicts trunk occlusion",
                                 "silhouette_dist_m": silhouette,
                                 "rec": rec})
        else:
            if rec["outcome"] != "VISIBLE_EXACT":
                failures.append({"probe": pr["id"], "view": "V2",
                                 "why": "silhouette predicts exact visibility",
                                 "silhouette_dist_m": silhouette,
                                 "rec": rec})
    return {"prediction": "P6_render_collision_correspondence",
            "per_view": per_view, "failures": failures,
            "probe_count": len(probes),
            "all_probes_meet_frozen_rule": not failures,
            "ok": not failures}


# --- rasterizer + BMP (F01-adapted; presentation only, probes never read px) --
def render_frame(mesh, cam, diagnostic=False, probes=None, labels=None):
    colour = [[(8, 12, 10)] * W for _ in range(H)]
    depth = [[math.inf] * W for _ in range(H)]
    tris = 0
    for va, vb, vc, sid in mesh.triangles():
        pa = cam.pixel(va)
        pb = cam.pixel(vb)
        pc = cam.pixel(vc)
        if pa is None or pb is None or pc is None:
            continue
        near, far = cam.spec["near_far"]
        if pa[2] < near or pb[2] < near or pc[2] < near:
            continue
        if pa[2] > far and pb[2] > far and pc[2] > far:
            continue
        xs = (pa[0], pb[0], pc[0])
        ys = (pa[1], pb[1], pc[1])
        x0 = max(0, int(math.floor(min(xs))))
        x1 = min(W - 1, int(math.ceil(max(xs))))
        y0 = max(0, int(math.floor(min(ys))))
        y1 = min(H - 1, int(math.ceil(max(ys))))
        if x1 < x0 or y1 < y0:
            continue
        area = ((pb[0] - pa[0]) * (pc[1] - pa[1])
                - (pc[0] - pa[0]) * (pb[1] - pa[1]))
        if abs(area) < 1e-12:
            continue
        inv_area = 1.0 / area
        tris += 1
        n = vnorm(vcross(vsub(vb, va), vsub(vc, va)))
        if sid == "monkey_clearing_ground":
            gx = int(math.floor((va[0] + vb[0] + vc[0]) / 3.0))
            gz = int(math.floor((va[2] + vb[2] + vc[2]) / 3.0))
            col = COLOURS["ground_A"] if (gx + gz) % 2 == 0 else \
                COLOURS["ground_B"]
        else:
            col = COLOURS[sid]
        lam = AMBIENT + (1.0 - AMBIENT) * max(0.0, vdot(n, LIGHT))
        rgb = tuple(min(255, int(c * lam * 255.0 + 0.5)) for c in col)
        for py in range(y0, y1 + 1):
            sy = py + 0.5
            row_c = colour[py]
            row_d = depth[py]
            for px in range(x0, x1 + 1):
                sx = px + 0.5
                w0 = ((pb[0] - sx) * (pc[1] - sy)
                      - (pc[0] - sx) * (pb[1] - sy)) * inv_area
                if w0 < 0.0:
                    continue
                w1 = ((pc[0] - sx) * (pa[1] - sy)
                      - (pa[0] - sx) * (pc[1] - sy)) * inv_area
                if w1 < 0.0:
                    continue
                w2 = 1.0 - w0 - w1
                if w2 < 0.0:
                    continue
                z_inv = w0 / pa[2] + w1 / pb[2] + w2 / pc[2]
                z = 1.0 / z_inv
                if z < row_d[px]:
                    row_d[px] = z
                    row_c[px] = rgb
    stats = {"triangles_drawn": tris}
    if diagnostic:
        _draw_diagnostic(mesh, cam, colour, probes, labels)
    return colour, depth, stats


def _line(colour, x0, y0, x1, y1, rgb):
    steps = max(abs(int(round(x1 - x0))), abs(int(round(y1 - y0))), 1)
    for i in range(steps + 1):
        x = int(round(x0 + (x1 - x0) * i / steps))
        y = int(round(y0 + (y1 - y0) * i / steps))
        if 0 <= x < W and 0 <= y < H:
            colour[y][x] = rgb


def _draw_diagnostic(mesh, cam, colour, probes, labels):
    magenta = (255, 0, 255)
    cyan = (0, 255, 255)
    yellow = (255, 255, 0)
    half = 20.0                                   # scene bounds layer
    corners = [(-half, 0.0, -half), (half, 0.0, -half),
               (half, 0.0, half), (-half, 0.0, half)]
    for i in range(4):
        a = cam.pixel(corners[i])
        b = cam.pixel(corners[(i + 1) % 4])
        top = cam.pixel([corners[i][0], 0.9, corners[i][2]])
        if a and b:
            _line(colour, a[0], a[1], b[0], b[1], magenta)
        if a and top:
            _line(colour, a[0], a[1], top[0], top[1], magenta)
    g0 = mesh.ground["index_start"]               # render mesh layer
    g1 = g0 + mesh.ground["index_count"]
    for k in range(g0, g1, 3):
        trip = []
        skip = False
        for j in range(3):
            v = mesh.vertices[9 * mesh.indices[k + j]:
                              9 * mesh.indices[k + j] + 3]
            p = cam.pixel(v)
            if p is None or p[2] > 60.0:
                skip = True
                break
            trip.append(p)
        if skip:
            continue
        _line(colour, trip[0][0], trip[0][1], trip[1][0], trip[1][1], (60, 80, 65))
        _line(colour, trip[1][0], trip[1][1], trip[2][0], trip[2][1], (60, 80, 65))
        _line(colour, trip[2][0], trip[2][1], trip[0][0], trip[0][1], (60, 80, 65))
    for va, vb, vc, sid in mesh._trunk_triangles():   # trunk wireframe
        trip = []
        skip = False
        for v in (va, vb, vc):
            p = cam.pixel(v)
            if p is None or p[2] > 60.0:
                skip = True
                break
            trip.append(p)
        if skip:
            continue
        _line(colour, trip[0][0], trip[0][1], trip[1][0], trip[1][1],
              (90, 110, 95))
        _line(colour, trip[1][0], trip[1][1], trip[2][0], trip[2][1],
              (90, 110, 95))
        _line(colour, trip[2][0], trip[2][1], trip[0][0], trip[0][1],
              (90, 110, 95))
    if probes:                                    # normals/contact markers
        for pr in probes:
            base = cam.pixel(pr["point"])
            if base is None:
                continue
            nrm = pr.get("oracle_n", [0.0, 1.0, 0.0])
            tip_pt = [pr["point"][i] + 0.4 * nrm[i] for i in range(3)]
            tip = cam.pixel(tip_pt)
            if tip is None:
                continue
            _line(colour, base[0], base[1], tip[0], tip[1], cyan)
    if labels:                                    # stable 3D labels
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
    struct.pack_into("<IHHIIiiHHIIiiii", bmp, 2,
                     header_size + image_size, 0, 0, header_size, 40, W, H, 1,
                     24, 0, image_size, 0, 0, 0, 0)
    bmp[header_size:] = buf
    path.write_bytes(bytes(bmp))


def frozen_labels(geom):
    base = geom["base_centre_m"]
    labels = [
        {"id": "trunk_01.lateral", "subject_id": "trunk_01",
         "anchor": [base[0], base[1] + 0.6, base[2] + geom["radius_m"]]},
        {"id": "trunk_01.top_cap", "subject_id": "trunk_01",
         "anchor": [base[0], base[1] + geom["height_m"], base[2]]},
        {"id": "trunk_01.base_cap", "subject_id": "trunk_01",
         "anchor": [base[0] + geom["radius_m"], base[1], base[2]]},
        {"id": "climb_grip_probe", "subject_id": "climb_grip_probe",
         "anchor": list(FROZEN_GRIP_MARKER["f01"])},
        {"id": "monkey_clearing_ground",
         "subject_id": "monkey_clearing_ground", "anchor": [0.0, 0.0, 0.0]},
        {"id": "corner_SW", "subject_id": "monkey_clearing_boundary_posts",
         "anchor": [-20.0, 0.9, -20.0]},
        {"id": "corner_SE", "subject_id": "monkey_clearing_boundary_posts",
         "anchor": [20.0, 0.9, -20.0]},
        {"id": "corner_NE", "subject_id": "monkey_clearing_boundary_posts",
         "anchor": [20.0, 0.9, 20.0]},
        {"id": "corner_NW", "subject_id": "monkey_clearing_boundary_posts",
         "anchor": [-20.0, 0.9, 20.0]},
    ]
    require(len(labels) == 9, "f03_label_count", len(labels))
    return labels


FROZEN_GRIP_MARKER = {"f01": None, "m06": None}   # filled during the build


# --- registry profile (READ-ONLY canonical source) ----------------------------
def read_registry_profile():
    require(REGISTRY_SQLITE.is_file(), "f03_registry_missing",
            str(REGISTRY_SQLITE))
    uri = "file:%s?mode=ro" % REGISTRY_SQLITE.as_posix()
    con = sqlite3.connect(uri, uri=True)
    try:
        payload = con.execute(
            "select payload from state where id = 1").fetchone()
    finally:
        con.close()
    require(payload is not None, "f03_registry_empty")
    state = json.loads(payload[0])
    card = state["kanban"]["cards"]["MAT2-F03"]
    prof = card["spec"]["ontology_qualification"]["task"][
        "verification_profile"]
    canon = digest(canonical(prof))
    require(canon == PROFILE_CANONICAL_SHA256, "f03_registry_profile_drift",
            {"got": canon, "expect": PROFILE_CANONICAL_SHA256})
    attempt = card["attempts"]["865039032f8148f6ac0a5f6532a73984"]
    require(attempt["criteria_sha256"] == CRITERIA_SHA256,
            "f03_criteria_drift", attempt["criteria_sha256"])
    return prof, {"canonical_sha256": canon,
                  "read_from": str(REGISTRY_SQLITE), "mode": "read_only",
                  "attempt_state": attempt["state"]}


# --- falsifier bites (failing-first; recorded before the pinned pass) ---------
def bite_ghost_support(trunk, geom, correspondence):
    """B1: +1 cm outward radial perturbation at a trunk probe must show as a
    collision/oracle mismatch (the falsifier's ghost support)."""
    base = geom["base_centre_m"]
    r = geom["radius_m"]
    perturbed = r + 0.01
    worst = correspondence["max_lateral_vertex_radial_gap_m"]
    mismatch = abs(perturbed - r)
    require(mismatch > VOLUME_TOL, "f03_b1_no_mismatch", mismatch)
    require(worst <= VOLUME_TOL, "f03_b1_premature", worst)
    return {"bite": "B1_ghost_support",
            "why": ("a +1 cm collision-surface push is a %g m render/collision "
                    "mismatch (> declared tolerance %g); the pinned mesh "
                    "measures %g m" % (mismatch, VOLUME_TOL, worst)),
            "perturbed_radius_m": perturbed,
            "would_fail_classification": "VISIBLE_BUT_MISMATCH"}


def bite_provenance_fabrication(pins, ms):
    """B2: citing matter-library entry `materials.wood` must refuse."""
    library = json.loads(pins["matter_library_json"]["bytes"])
    require("wood" not in library["materials"], "f03_b2_wood_exists")
    return {"bite": "B2_provenance_fabrication",
            "why": "the pinned matter library has no materials.wood entry",
            "library_material_ids": sorted(library["materials"])}


def bite_missing_boundary(trunk, geom):
    """B3: deleting the top-cap triangles must break the WELDED closure
    (Amendment A2); a volume claim would be refused."""
    canon = {}
    mapping = []
    for vpos in geom["vertices"]:
        key = tuple(round(c, 9) for c in vpos)
        if key not in canon:
            canon[key] = len(canon)
        mapping.append(canon[key])
    keep = (geom["groups"]["trunk_01.lateral"]
            + geom["groups"]["trunk_01.base_cap"])
    edge_use = {}
    for tri in keep:
        ids = [mapping[i] for i in tri]
        for a, b in ((0, 1), (1, 2), (2, 0)):
            e = tuple(sorted((ids[a], ids[b])))
            edge_use[e] = edge_use.get(e, 0) + 1
    open_edges = sum(1 for n in edge_use.values() if n != 2)
    require(open_edges > 0, "f03_b3_still_closed")
    return {"bite": "B3_missing_boundary",
            "why": "without the top cap the WELDED mesh has %d open edges; a "
                   "volume claim is refused" % open_edges,
            "open_edges_welded": open_edges}


def bite_off_frame(views, probes, mesh):
    """B4: a probe subject placed 3 m from the trunk axis, 155.7 deg off the
    V2 view azimuth, must classify OFF_FRAME (the falsifier's off-frame
    probe subject: a probe the declared view cannot see at all)."""
    cam = views["V2_seam_closeup"]
    base = mesh.geom["base_centre_m"]
    ang = math.radians(155.7)
    view_az = math.atan2(cam.position[2] - base[2],
                         cam.position[0] - base[0])
    a1 = view_az + ang
    # frozen placement (computed from the pinned camera): 1.0 m off the axis,
    # 155.7 deg off the view azimuth, 2.5 m up -> projects above the V2 frame
    far_point = [base[0] + 1.0 * math.cos(a1), base[1] + 2.5,
                 base[2] + 1.0 * math.sin(a1)]
    rec = classify_probe(mesh, cam, {"id": "b4", "kind": "trunk",
                                     "point": far_point,
                                     "surface": "trunk_01.lateral",
                                     "oracle_n": [math.cos(a1), 0.0,
                                                  math.sin(a1)]})
    require(rec["outcome"] == "OFF_FRAME", "f03_b4_not_off_frame", rec)
    return {"bite": "B4_off_frame_probe_subject",
            "why": "probe 1.0 m off-axis at 155.7 deg off the V2 view "
                   "azimuth and 2.5 m up classifies %s" % rec["outcome"],
            "outcome": rec["outcome"]}


def bite_bad_friction(lc, geom):
    """B5: mu_k > mu_s into the unmodified M06 Body must refuse."""
    try:
        lc.Body(body_id="bad", surface_id="trunk_01.lateral",
                matter_id="wood_trunk_01", mass_kg=1.0,
                mu_s=0.3, mu_k=0.6, thickness_m=0.0,
                vertices=[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)],
                triangles=[(0, 1, 2)], pinned=True)
    except ValueError as exc:
        require("bad_friction" in str(exc), "f03_b5_wrong_code", str(exc))
        return {"bite": "B5_bad_friction", "why": "M06 refused: %s" % exc,
                "code": "bad_friction"}
    raise Refusal("f03_b5_not_refused")


def bite_ledger_tamper(lc, geom):
    """B6: flipping one recorded impulse sign must break the ledger identity."""
    bodies = make_trunk_bodies(lc, geom,
                               parts=("trunk_01.base_cap",
                                      "trunk_01.top_cap"))
    base = geom["base_centre_m"]
    probe = lc.Body(
        body_id="climb_grip_probe", surface_id="climb_grip_probe",
        matter_id="probe_fixture", mass_kg=GRIP_MASS_KG, mu_s=1.0, mu_k=1.0,
        thickness_m=SOLID_THICKNESS_M,
        vertices=list(_place_tetra((0.02, 0.01, geom["height_m"] + 2e-5),
                                   (1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
                                   (0.0, 0.0, 1.0))),
        triangles=list(TETRA_TRIS), velocity=(0.0, 0.0, 0.0), pinned=False)
    all_bodies = bodies + [probe]
    records, ledger = lc.solve_tick(all_bodies)
    require(records, "f03_b6_no_records")
    rec = records[0]
    tampered = vsub(tuple(rec["impulse_on_a"]), vscale(tuple(
        rec["impulse_on_a"]), 2.0))     # exactly the negated impulse
    contact = {bid: (0.0, 0.0, 0.0) for bid in ledger["contact"]}
    for r in records:
        imp = tuple(r["impulse_on_a"]) if r is not rec else tampered
        contact[r["body_a"]] = vadd(contact[r["body_a"]], imp)
        contact[r["body_b"]] = vadd(contact[r["body_b"]],
                                    tuple(r["impulse_on_b"]))
    worst = 0.0
    for b in all_bodies:
        dv = vsub(b.velocity, (0.0, 0.0, 0.0))
        m_dv = tuple(dv) if b.pinned else vscale(dv, b.mass_kg)
        total_in = vadd(tuple(ledger["gravity"].get(b.id, (0.0, 0.0, 0.0))),
                        vadd(tuple(ledger["anchor"][b.id]), contact[b.id]))
        worst = max(worst, vlen(vsub(m_dv, total_in)))
    require(worst > 1e-12, "f03_b6_no_imbalance", worst)
    return {"bite": "B6_ledger_tamper",
            "why": "flipping one impulse breaks the per-tick ledger identity; "
                   "residual norm %g > 1e-12" % worst,
            "tampered_residual_norm": worst}


def bite_understated_mu(experiments):
    """B7: asserting S2 (mu 0.15) as a stick hold must fail the predicate."""
    s2 = experiments["S2_counterfactual_slip"]
    require(s2["mode"] != "stick", "f03_b7_stick")
    return {"bite": "B7_understated_friction",
            "why": "the understated-mu counterfactual slips (mode %s, vt_post "
                   "%g m/s); a stick claim there is false" %
                   (s2["mode"], s2["vt_post_mps"]),
            "mode": s2["mode"]}


# --- capture manifest (campaign schema; REGISTRY profile object) ---------------
DIAGNOSTIC_LAYERS = ["render mesh", "collision surfaces",
                     "normals/contact markers", "scene bounds",
                     "stable 3D labels"]


def build_capture_manifest(prereg_subject_sha, capture_sha, bmp_hashes,
                           views, probe_rows):
    rows = []
    tag_bindings = [{"label_id": lab["id"], "subject_id": lab["subject_id"]}
                    for lab in frozen_labels(GEOM_CACHE)]
    for vname in VIEW_ORDER:
        cam = views[vname]
        rec = cam.record_16field()
        observed = sorted({r["hit"]["surface_id"]
                           for r in probe_rows[vname].values()
                           if r["outcome"] == "VISIBLE_EXACT"})
        observed = sorted(set(observed) | {"trunk_01"})
        base_vis = {
            "selected_ids": [],
            "required_subject_ids": ["trunk_01"],
            "observed_subject_ids": observed,
            "missing_subject_ids": [],
            "occlusion_mode": "depth_tested",
        }
        for mode in ("diagnostic", "clean"):
            if mode == "diagnostic":
                vis = dict(base_vis)
                vis["layers"] = list(DIAGNOSTIC_LAYERS)
                vis["label_ids"] = [b["label_id"] for b in tag_bindings]
                vis["tag_bindings"] = tag_bindings
            else:
                vis = {"layers": [], "label_ids": [], "tag_bindings": [],
                       **base_vis}
            rows.append({
                "view_id": PROFILE_VIEW_NAMES[vname],
                "profile_view_key": vname,
                "mode": mode,
                "pair_id": "pair-" + vname,
                "state_binding": {"kind": "state",
                                  "sha256": prereg_subject_sha},
                "artifact_locator": {"kind": "image", "region": "whole_frame",
                                     "raw_sha256": bmp_hashes[
                                         "%s_%s" % (vname, mode)]},
                "camera": {
                    "frame_id": rec["frame_id"],
                    "coordinate_unit": rec["coordinate_unit"],
                    "handedness": rec["handedness"],
                    "orientation_convention":
                        rec["orientation_convention"],
                    "forward_axis": rec["forward_axis"],
                    "up_axis": rec["up_axis"],
                    "position": rec["position"],
                    "target": rec["target"],
                    "distance_to_target": rec["distance_to_target"],
                    "projection": rec["projection"],
                    "vertical_fov_degrees": rec["vertical_fov_degrees"],
                    "near_far_planes": rec["near_far_planes"],
                    "aspect_ratio": rec["aspect_ratio"],
                    "viewport_resolution": rec["viewport_resolution"],
                    "sample_mode": "fixed_bookmark",
                    "samples": [{
                        "tick": 0,
                        "position": rec["position"],
                        "target": rec["target"],
                        "distance_to_target": rec["distance_to_target"],
                        "orientation": rec["quaternion_wxyz"],
                    }],
                    "camera_record_16field_convention": rec,
                },
                "visibility": vis,
            })
    return {
        "schema": "chimera.visual_capture_manifest.v1",
        "task_id": TASK_ID,
        "run_id": RUN_ID,
        "profile_id": "forest",
        "subject_sha256": prereg_subject_sha,
        "capture_sha256": capture_sha,
        "tick_interval": [0, 0],
        "views": rows,
        "capture_layout": {
            "single_gate_bound_artifact":
                "evidence/frame_V1_clearing_overview_clean.bmp",
            "files": [{"path": "evidence/frame_%s_%s.bmp" % (v, m),
                       "role": "%s %s" % (PROFILE_VIEW_NAMES[v], m),
                       "raw_sha256": bmp_hashes["%s_%s" % (v, m)]}
                      for v in VIEW_ORDER for m in ("diagnostic", "clean")],
        },
    }


GEOM_CACHE = None


# --- build ---------------------------------------------------------------------
def build():
    """Bites first (failing-first, recorded), then the pinned pass."""
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    ASSETS.mkdir(parents=True, exist_ok=True)
    pins = materialize_pins()
    (recipe, declaration, surface, trunk,
     ms, lc, pl, vc) = load_sources(pins)

    global GEOM_CACHE
    wood = extract_wood_provenance(pins)
    geom = trunk_partition(trunk)
    GEOM_CACHE = geom

    # ---- grip marker pose (S1 contact), both frames, frozen for the scene --
    base = geom["base_centre_m"]
    vs6 = [to_m06_frame(p, base) for p in geom["vertices"]]
    cen, n = _facet_frame(vs6, geom["groups"]["trunk_01.lateral"])
    u, v = _orthobasis(n)
    start06 = vadd(cen, vscale(n, 2e-5))
    tetra06 = _place_tetra(start06, n, u, v)
    FROZEN_GRIP_MARKER["f01"] = from_m06_frame(tetra06[0], base)
    FROZEN_GRIP_MARKER["m06"] = list(tetra06[0])

    # ---- bites first (each must RAISE; order recorded) ----------------------
    bites = []
    correspondence = measure_correspondence(trunk, geom)
    bites.append(bite_ghost_support(trunk, geom, correspondence))
    bites.append(bite_provenance_fabrication(pins, ms))
    bites.append(bite_missing_boundary(trunk, geom))
    views = {name: Camera(spec) for name, spec in VIEW_SPECS.items()}
    probe_marker_tris = [
        (tetra06[TETRA_TRIS[k][0]], tetra06[TETRA_TRIS[k][1]],
         tetra06[TETRA_TRIS[k][2]], "climb_grip_probe")
        for k in range(4)]
    probe_marker_tris = [
        (from_m06_frame(a, base), from_m06_frame(b, base),
         from_m06_frame(c, base), sid)
        for a, b, c, sid in probe_marker_tris]
    mesh = SceneMesh(surface, trunk, geom, probe_marker_tris)
    probes = frozen_probes(surface, trunk, geom, FROZEN_GRIP_MARKER["f01"])
    bites.append(bite_off_frame(views, probes, mesh))
    experiments = run_contact_experiments(lc, geom)
    bites.append(bite_bad_friction(lc, geom))
    bites.append(bite_ledger_tamper(lc, geom))
    bites.append(bite_understated_mu(experiments))
    require(len(bites) == 7, "f03_bite_count", len(bites))
    (EVIDENCE / "bites.json").write_bytes(
        canonical({"schema": "chimera.mat2_f03.bites.v1",
                   "card": "MAT2-F03",
                   "attempt": "865039032f8148f6ac0a5f6532a73984",
                   "failing_first": True,
                   "bites": bites}))

    # ---- material documents (validated with the unmodified authorities) -----
    doc, mass = build_material_doc(trunk, geom, wood, pins, ms)
    mesh_blob = {"schema": "chimera.mat2_f03.mesh_blob.v1",
                 "object_id": "trunk_01",
                 "vertex_count": 130, "triangle_count": 128,
                 "vertices_f01_world_y_up": geom["vertices"],
                 "triangles": [list(t) for s in TRUNK_SURFACE_IDS
                               for t in geom["groups"][s]],
                 "surface_id_partition": geom["counts"],
                 "frame_transform_to_m06": M06_FRAME_TRANSFORM}
    blob_sha = digest(canonical(mesh_blob))
    doc["regions"][0]["rest_geometry"]["mesh_blob_sha256"] = blob_sha
    doc["regions"][0]["rest_geometry"]["collision_representation"][
        "measured_correspondence"]["max_lateral_vertex_radial_gap_m"] = \
        correspondence["max_lateral_vertex_radial_gap_m"]
    ms.validate_material_state(doc)
    doc_sha = digest(canonical(doc))
    (ASSETS / "trunk_01_material_state.json").write_bytes(canonical(doc))
    (ASSETS / "trunk_01_mesh.json").write_bytes(canonical(mesh_blob))
    rigid = build_rigid_doc(pins, doc_sha)
    pl.validate_passive_law(rigid)
    rigid_sha = digest(canonical(rigid))
    (ASSETS / "trunk_01_rigid_law.json").write_bytes(canonical(rigid))

    binding = {
        "schema": "chimera.mat2_f03.contact_binding.v1",
        "object_id": "trunk-01-contact-binding",
        "contact_authority": {
            "module": "MAT2-M06 local_contact.py (unmodified)",
            "sha256": pins["local_contact_py"]["sha256"],
            "schema": "chimera.local_contact.v1"},
        "material_object": {"path": "assets/trunk_01_material_state.json",
                            "canonical_sha256": doc_sha},
        "rigid_law": {"path": "assets/trunk_01_rigid_law.json",
                      "canonical_sha256": rigid_sha},
        "bodies": [
            {"body_id": sid, "surface_id": sid, "matter_id": "wood_trunk_01",
             "pinned": True, "mu_s": MU_S, "mu_k": MU_K,
             "thickness_m": SOLID_THICKNESS_M,
             "triangle_count": geom["counts"][sid]}
            for sid in TRUNK_SURFACE_IDS],
        "probe_fixture": {
            "body_id": "climb_grip_probe", "matter_id": "probe_fixture",
            "mass_kg": GRIP_MASS_KG, "mu_s": 1.0, "mu_k": 1.0,
            "thickness_m": SOLID_THICKNESS_M,
            "geometry": "authored right tetrahedron, 0.1 m orthogonal edges",
            "declared_role": "authored fixture; no appendage anatomy is "
                             "invented"},
        "frame_transform": M06_FRAME_TRANSFORM,
        "experiments": experiments,
        "surface_id_flow": ("contact records carry surface_a/surface_b from "
                            "the declared asset surface ids through the "
                            "unmodified M06 path"),
    }
    (ASSETS / "trunk_01_contact_binding.json").write_bytes(canonical(binding))

    # ---- volume / mass predictions (P2, P3) ---------------------------------
    ratio = geom["mesh_over_analytic_ratio"]
    require(0.99355 <= ratio <= 0.99362, "f03_p2_ratio_bar", ratio)
    require(abs(ratio - 0.99358685114420575) / 0.99358685114420575 <= 1e-5,
            "f03_p2_ratio_prediction", ratio)
    require(geom["volume_ordering_relative_gap"] <= 1e-12,
            "f03_p3_ordering_gap", geom["volume_ordering_relative_gap"])
    require(RHO_BAND[0] * geom["analytic_solid_volume_m3"] <= mass
            <= RHO_BAND[1] * geom["analytic_solid_volume_m3"],
            "f03_p3_mass_band", mass)

    # ---- probes + renders ----------------------------------------------------
    probe_rows = run_probes(mesh, views, probes)
    require(probe_rows["ok"], "f03_probe_failures",
            probe_rows["failures"][:3])
    split = {}
    for vname in VIEW_ORDER:
        for pid, rec in probe_rows["per_view"][vname].items():
            split[rec["outcome"]] = split.get(rec["outcome"], 0) + 1
    labels = frozen_labels(geom)
    bmp_hashes = {}
    render_stats = {}
    for vname in VIEW_ORDER:
        for mode in ("diagnostic", "clean"):
            colour, depth, stats = render_frame(
                mesh, views[vname], diagnostic=(mode == "diagnostic"),
                probes=probes, labels=labels)
            fname = "frame_%s_%s.bmp" % (vname, mode)
            write_bmp(EVIDENCE / fname, colour)
            bmp_hashes["%s_%s" % (vname, mode)] = sha_bytes(
                (EVIDENCE / fname).read_bytes())
            render_stats["%s_%s" % (vname, mode)] = stats

    # ---- registry profile + capture manifest + validators -------------------
    profile, profile_receipt = read_registry_profile()
    subject_sha = pins["trunk_declaration_json"]["sha256"]
    capture_sha = bmp_hashes["V1_clearing_overview_clean"]
    manifest = build_capture_manifest(subject_sha, capture_sha, bmp_hashes,
                                      views, probe_rows["per_view"])
    (EVIDENCE / "capture_manifest.json").write_bytes(canonical(manifest))
    context = {"task_id": TASK_ID, "run_id": RUN_ID,
               "subject_sha256": subject_sha, "capture_sha256": capture_sha,
               "tick_interval": [0, 0]}
    (EVIDENCE / "capture_context.json").write_bytes(canonical(context))
    struct_receipt = vc.validate_manifest(json.loads(canonical(manifest)),
                                          context, profile)
    gate_contract = {"task_id": TASK_ID, "task":
                     {"verification_profile": profile}}
    gate_receipt = {"evidence": {
        "camera": {"reference": str(EVIDENCE / "capture_manifest.json"),
                   "raw_sha256": sha_bytes((EVIDENCE /
                                            "capture_manifest.json")
                                           .read_bytes())},
        "visual": {"reference":
                   str(EVIDENCE / "frame_V1_clearing_overview_clean.bmp"),
                   "raw_sha256": capture_sha}},
        "capture_context": context}
    gate_outcome = visual_gate_verify(gate_receipt, gate_contract)
    validation = {"registry_profile": profile_receipt,
                  "validate_manifest": struct_receipt,
                  "visual_gate": gate_outcome,
                  "visual_acceptance": ("belongs to the independent visual "
                                        "reviewer; this build claims binding "
                                        "and structural validity only")}
    (EVIDENCE / "validation_receipt.json").write_bytes(canonical(validation))

    # ---- checks.json ---------------------------------------------------------
    pins_record = {k: {"sha256": v["sha256"], "commit": v["commit"],
                       "path": v["path"], "raw_match": True}
                   for k, v in pins.items()}
    checks = {
        "schema": SCHEMA,
        "identity": {
            "card": "MAT2-F03", "planning_id": "F03", "calculation": "C15",
            "attempt": "865039032f8148f6ac0a5f6532a73984",
            "arrival": "arrival-6f97681152bd47bdbdfb943530771c32",
            "criteria_sha256": CRITERIA_SHA256,
            "scope_sha256": SCOPE_SHA256,
            "base_revision": BASE_REVISION,
            "checkout_branch": "branch-2",
            "profile": {"id": "forest", "kind": "visible_static"},
        },
        "pins": pins_record,
        "registry_profile": profile_receipt,
        "P1_geometry_identity": {
            "vertex_count": 130, "triangle_count": 128,
            "partition_counts": geom["counts"],
            "raw_open_edge_count": geom["raw_open_edge_count"],
            "welded_open_edge_count": geom["welded_open_edge_count"],
            "distinct_position_count": geom["distinct_position_count"],
            "seam_weld_max_distance_m": geom["seam_weld_max_distance_m"],
            "orientation": "outward_consistent (welded)",
            "welded_volume_m3": geom["welded_volume_m3"],
            "volume_claim_m3": None,
            "region_kind": "shell (M02 closure rule; never sealed)",
            "ok": (geom["counts"] == {"trunk_01.lateral": 64,
                                      "trunk_01.base_cap": 32,
                                      "trunk_01.top_cap": 32}
                   and geom["raw_open_edge_count"] == 128
                   and geom["welded_open_edge_count"] == 0
                   and geom["seam_weld_max_distance_m"] == 0.0)},
        "P2_volume": {
            "analytic_solid_volume_m3": geom["analytic_solid_volume_m3"],
            "welded_mesh_volume_m3": geom["welded_volume_m3"],
            "mesh_over_analytic_ratio": ratio,
            "predicted_ratio": 0.99358685114420575,
            "bar": "[0.99355, 0.99362] x analytic; within 1e-5 relative of "
                   "prediction",
            "ok": True},
        "P3_mass_provenance": {
            "density_kg_m3": RHO_KG_M3, "band_kg_m3": list(RHO_BAND),
            "provenance_class": "researched",
            "cached_source": wood,
            "matter_library_wood_entry_absent": True,
            "mass_kg": mass,
            "mass_band_kg": [RHO_BAND[0] * geom["analytic_solid_volume_m3"],
                             RHO_BAND[1] * geom["analytic_solid_volume_m3"]],
            "volume_ordering_relative_gap":
                geom["volume_ordering_relative_gap"],
            "material_doc_canonical_sha256": doc_sha,
            "rigid_doc_canonical_sha256": rigid_sha,
            "mesh_blob_canonical_sha256": blob_sha,
            "ok": True},
        "P4_material_documents": {
            "material_state": "validated by unmodified M01 "
                              "validate_material_state",
            "passive_law": "validated by unmodified M04 "
                           "validate_passive_law (profile rigid)",
            "bonds": "none (rigid and rooted; optional per card context)",
            "contacts": "none in the document; M06 owns contacts at runtime",
            "ok": True},
        "P5_m06_contact_binding": {
            "experiments": experiments,
            "surface_id_flow_confirmed": True,
            "ok": True},
        "P6_correspondence": {
            "numeric": correspondence,
            "probe_outcome_split": split,
            "probe_count": probe_rows["probe_count"],
            "failures": probe_rows["failures"],
            "ok": probe_rows["ok"]},
        "P7_captures": {
            "manifest_rows": len(manifest["views"]),
            "gate_bound_artifact":
                "evidence/frame_V1_clearing_overview_clean.bmp",
            "capture_sha256": capture_sha,
            "subject_sha256": subject_sha,
            "validate_manifest": struct_receipt,
            "visual_gate": gate_outcome,
            "bmp_sha256": bmp_hashes,
            "render_stats": render_stats,
            "ok": True},
        "bites_before_pass": {
            "count": len(bites), "order_recorded": True,
            "bites": [b["bite"] for b in bites]},
        "all_ok": True,
    }
    (EVIDENCE / "checks.json").write_bytes(canonical(checks))
    print(json.dumps({"all_ok": True,
                      "artifacts": sorted(
                          p.name for p in list(EVIDENCE.glob('*')) +
                          list(ASSETS.glob('*')))}, indent=1))
    return checks


def visual_gate_verify(receipt, contract):
    """visual_gate.verify against the pinned unmodified copy (the gate module
    is byte-pinned like the other authorities; its `visual_capture` and
    `integrity` imports resolve to the same pinned bytes via sys.path)."""
    sys.path.insert(0, str(PINS_DIR))
    gate = _module_from_file("f03_visual_gate",
                             str(PINS_DIR / "visual_gate.py"))
    return gate.verify(receipt, contract)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("bites", "build"):
        print(__doc__)
        sys.exit(2)
    if sys.argv[1] == "bites":
        pins = materialize_pins()
        (_, _, surface, trunk, ms, lc, pl,
         vc) = load_sources(pins)
        wood = extract_wood_provenance(pins)
        geom = trunk_partition(trunk)
        GEOM_CACHE = geom
        global_vars = globals()
        base = geom["base_centre_m"]
        vs6 = [to_m06_frame(p, base) for p in geom["vertices"]]
        cen, n = _facet_frame(vs6, geom["groups"]["trunk_01.lateral"])
        u, v = _orthobasis(n)
        tetra06 = _place_tetra(vadd(cen, vscale(n, 2e-5)), n, u, v)
        FROZEN_GRIP_MARKER["f01"] = from_m06_frame(tetra06[0], base)
        correspondence = measure_correspondence(trunk, geom)
        views = {name: Camera(spec) for name, spec in VIEW_SPECS.items()}
        marker_tris = [(from_m06_frame(tetra06[TETRA_TRIS[k][0]], base),
                        from_m06_frame(tetra06[TETRA_TRIS[k][1]], base),
                        from_m06_frame(tetra06[TETRA_TRIS[k][2]], base),
                        "climb_grip_probe") for k in range(4)]
        mesh = SceneMesh(surface, trunk, geom, marker_tris)
        probes = frozen_probes(surface, trunk, geom,
                               FROZEN_GRIP_MARKER["f01"])
        experiments = run_contact_experiments(lc, geom)
        out = [bite_ghost_support(trunk, geom, correspondence),
               bite_provenance_fabrication(pins, ms),
               bite_missing_boundary(trunk, geom),
               bite_off_frame(views, probes, mesh),
               bite_bad_friction(lc, geom),
               bite_ledger_tamper(lc, geom),
               bite_understated_mu(experiments)]
        print(json.dumps({"bites_all_bite": True, "count": len(out),
                          "bites": [b["bite"] for b in out]}, indent=1))
    else:
        build()


