"""implementation -- MAT2-F04: ground and trunk contact geometry, frozen cases.

Card done_when (verbatim): "No unacceptable tunnelling, ghost support,
interpenetration or visual/collision disagreement in frozen cases"

THE MECHANISM (frozen in PREREGISTRATION.md commits d71c7d8a + 56de4e44
BEFORE this file existed):

1. ONE combined subject: F02's tied terrain asset (render arrays = query
   triangulation) AND F03's pinned climbable trunk (render mesh = collision
   mesh), in ONE declared global frame map (F02's rotation, det=+1):
   clearing (x, y up, z) -> contact (x, -z, y). Asset identity is asserted by
   exact array equality per scenario build (P1); nothing re-derives geometry.

2. THE shared path: every tick of every frozen scenario goes through M06's
   unmodified chimera.local_contact.v1 solve_tick (byte-identical vendored pin,
   hash-asserted, imported -- never forked). Crossing and impact trajectories
   are replayed at ground, trunk and seam; FULL tick intervals are inspected
   for tunnelling (first-contact pre-overlap + per-tick penetration metric),
   ghost support (every impulse is a real record; ledger identity), and
   interpenetration (frozen 1e-4 m solver-anchored bar).

3. Combined-instantiation scope (P0, F03 A3 heritage measured at the seam):
   the trunk base ring touches the ground plane at exactly 0.0 m, so a solve
   containing both static parts is REFUSED by the pinned law
   (`nonfinite_state`, both-pinned exact contact). P0 measures that refusal
   first; dynamic scenarios instantiate exactly the static parts they touch;
   the composition limitation is inventoried (prereg section 8), never
   silently repaired.

4. Falsifier arms FB1-FB7 run FIRST (fail-first, recorded), each with a named
   refusal and its OWN passing clean control (F03 heritage premature guard:
   the bite is credited only when the clean control passes); a non-biting
   falsifier fails the whole build.

5. Capture: REGISTRY profile `contact-motion` (kind motion) read READ-ONLY
   from agent_slots.sqlite3; exactly the three profile views x (diagnostic,
   clean) as VIDEO rows of ONE deterministic FFV1/AVI capture whose sha256 is
   the capture_sha256 (single on-disk artifact in the attempt workspace);
   state_binding kind 'trace' -> evidence/contact_trace.json; committed stills
   (BMP, hash-listed supplementary); visual_capture.validate_manifest +
   visual_gate.verify bind everything. visual_acceptance stays false BY
   DESIGN -- independent visual review remains mandatory.

CPU-only (stdlib + ffmpeg for encoding), deterministic (no RNG, no
wall-clock). Refusals are named codes; nothing is silently repaired.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sqlite3
import struct
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"
CONTRIB = HERE.parent                      # contributions/
ATTEMPT_WORKSPACE = HERE.parents[3]        # .../<attempt id>/
CAPTURE_DIR_NAME = "capture-evidence-20260928"

SCHEMA = "chimera.mat2_f04.contact_geometry.v1"
BASE_REVISION = "459ab80136c1491138dece91ebbbf62ab8349cb1"
PREREG_COMMIT = "d71c7d8a805f2d734b881ac2d15657fb4fe061bc"
AMENDMENT_COMMITS = [
    "56de4e44875296ac0176395eab39420731e383f2",   # A1 seam window/handover
    "6d116eaa62e4bc8061f43f39f37987b9ed40bb0f",   # A2 FB2 late-detection form
    "43fc9e3abd5ece19cc3e9512887eb92c54402b87",   # A3 FB6 whole-hit-triangle
    "f5f26e8c19197f35542a159c2754d832c8806806",   # A4 FB6 loss-of-exact form
    "a35874d602f52bdf611bbc8eb97caa3dad529dc9",   # A5 seam handover 0.03 m
    "11a9ecf42727e259595ed19156dde2dfb29fa0f1",   # A6 measured tick interval
]
TASK_ID = "F04"                            # SHORT form (campaign capture schema)
RUN_ID = "mat2-f04-contact-20260928-c4064f0e"
CRITERIA_SHA256 = "4c0a901840d34736a3bcd4dee6a70e750b731a83ef4152a573b99e2dae6b7669"
SCOPE_SHA256 = "cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097"
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
    "local_contact_py": {"rel": "MAT2-M06/local_contact.py",
        "sha256": "1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc"},
    "contact_law_json": {"rel": "MAT2-M06/contact_law.json",
        "sha256": "583962c29f18118a478dedb167f2c3667414b86f5cab4ee54763416f1df7e41b"},
    "f03_trunk_mesh_json": {"rel": "MAT2-F03/assets/trunk_01_mesh.json", "sha256": None},
}
PIN_SOURCE_TREE = "branch-3 @ %s (sealed line tip; F02/F03 merged)" % BASE_REVISION

# --- frozen bars (PREREGISTRATION section 3; do not tune) ----------------------
PEN_BAR_M = 1e-4
REST_LO_M, REST_HI_M = 0.0015, 0.0025
TRUNK_REST_DISP_BAR_M = 2e-3
LEDGER_BAR = 1e-12
PLANE_BAR_M = 1e-9
NORMAL_BAR = 1e-9
TRUNK_RADIAL_TOL_M = 2e-4
SPEED_BAR_M_S = 1e-4
SEAM_BAND_M = (0.0, 0.15)
GROUND_MU_S, GROUND_MU_K = 0.9, 0.65
TRUNK_MU_S, TRUNK_MU_K = 0.6, 0.6          # F03 declared UNEVIDENCED-PLACEHOLDER
PROBE_MU_S, PROBE_MU_K = 0.6, 0.4
PROBE_MASS_KG = 0.12
PROBE_THICKNESS_M = 0.002
GROUND_THICKNESS_M = 0.002
TRUNK_THICKNESS_M = 0.0
GROUND_SURFACE_ID = "monkey_clearing_ground"
GROUND_MATTER_ID = "clearing_ground_topsoil"
CENTER_VERTEX_BASE = 128
CENTER_VERTEX_TOP = 129

# --- frozen scenario table (PREREGISTRATION section 4 as amended by A1) --------
TICKS_G_HIGH = 30
TICKS_T_CROSS = 30
TICKS_SEAM_HIGH = 40
TICKS_G_SEAM_REST = 40
TICKS_TRUNK_TOP_REST = 40

# Frozen video row plan (one row per profile view x diagnostic/clean; each
# row concatenates whole scenario replays, except the two rest tails which
# contribute their last 5 ticks). Module level so the capture-gate test
# derives still frame indices from the SAME plan the build encodes.
ROW_PLAN = [
    ("V1_clearing_overview", "diagnostic",
     [("G_HIGH", None), ("T_CROSS", None), ("SEAM_HIGH", None),
      ("G_SEAM_REST", range(TICKS_G_SEAM_REST - 5,
                            TICKS_G_SEAM_REST)),
       ("TRUNK_TOP_REST", range(TICKS_TRUNK_TOP_REST - 5,
                                TICKS_TRUNK_TOP_REST))]),
    ("V1_clearing_overview", "clean",
     [("G_HIGH", None), ("T_CROSS", None), ("SEAM_HIGH", None),
      ("G_SEAM_REST", range(TICKS_G_SEAM_REST - 5,
                            TICKS_G_SEAM_REST)),
       ("TRUNK_TOP_REST", range(TICKS_TRUNK_TOP_REST - 5,
                                TICKS_TRUNK_TOP_REST))]),
    ("V2_seam_closeup", "diagnostic", [("SEAM_HIGH", None)]),
    ("V2_seam_closeup", "clean", [("SEAM_HIGH", None)]),
    ("V3_opposite_oblique", "diagnostic", [("T_CROSS", None)]),
    ("V3_opposite_oblique", "clean", [("T_CROSS", None)]),
]

# Committed stills: the impact-tick (first-contact) frame of each row's
# still scenario.
STILL_OF = {
    "V1_clearing_overview": ("G_HIGH", None),   # first-contact tick
    "V2_seam_closeup": ("SEAM_HIGH", None),     # first trunk-contact tick
    "V3_opposite_oblique": ("T_CROSS", None),
}

# --- frozen views/cameras (clearing frame, Y up; prereg section 7) --------------
W, H = 960, 540
NEAR_FAR = [0.05, 500.0]
VIEW_SPECS = {
    "V1_clearing_overview": {
        "position": [0.0, 46.0, -32.0], "target": [0.0, 0.0, 0.0],
        "vfov_deg": 55.0, "near_far": NEAR_FAR},
    "V2_seam_closeup": {
        "position": [10.30, 1.05, 1.70], "target": [11.976783, 0.25, 2.471766],
        "vfov_deg": 55.0, "near_far": [0.05, 50.0]},
    "V3_opposite_oblique": {
        "position": [13.30, 2.30, 4.30], "target": [11.976783, 0.45, 2.471766],
        "vfov_deg": 50.0, "near_far": NEAR_FAR},
}
PROFILE_VIEW_NAMES = {
    "V1_clearing_overview": "clearing contact overview",
    "V2_seam_closeup": "terrain/trunk seam impact close-up",
    "V3_opposite_oblique": "opposite-trunk and oblique depth checks",
}
VIEW_ORDER = ["V1_clearing_overview", "V2_seam_closeup", "V3_opposite_oblique"]
DIAGNOSTIC_LAYERS = ["render and collision surfaces",
                     "probe trajectories",
                     "contact normals and tick IDs"]
VIS_BAR_M = 1e-6
HEIGHT_BAR_M = 1e-9
TRUNK_RING_SEGMENTS = 32
TRUNK_NORMAL_ANGULAR_SLACK = 5e-4
MARGIN_FRACTION = 0.03                     # clipped-subject guard per side

# A6: the manifest tick interval follows the ACTUAL concatenated replay
# length (measured at build time): SEAM_HIGH's frozen window-end rule
# (first trunk contact + 3 ticks) closed its window at 32 states, so the
# overview montage carries 30+30+32+5+5 = 102 states, not the 110 first
# estimated. Computed in build(); recorded in the receipt and manifest.
TICK_INTERVAL = None
ROW_STATES = {}                            # measured per row at build time
FPS = 1


class Refusal(ValueError):
    def __init__(self, code, detail=""):
        self.code, self.detail = code, str(detail)
        super().__init__(code + (": " + self.detail if detail else ""))


def require(condition, code, detail=""):
    if not condition:
        raise Refusal(code, detail)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value):
    return sha_bytes(canonical(value))


# --- pins ----------------------------------------------------------------------
def load_pins():
    out = {}
    for key, pin in PINS.items():
        path = CONTRIB / pin["rel"]
        require(path.is_file(), "f04_pin_missing", key)
        got = sha_bytes(path.read_bytes())
        if pin["sha256"] is not None:
            require(got == pin["sha256"], "f04_pin_hash_mismatch",
                    {"key": key, "expect": pin["sha256"], "got": got})
        out[key] = {"file": str(path), "sha256": got,
                    "published": "contributions/" + pin["rel"], "raw_match": True}
    return out


def load_modules(pins):
    import importlib.util

    def module(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    sys.path.insert(0, str(CONTRIB / GND))
    tb = module("f04_terrain_bundle", pins["terrain_bundle_py"]["file"])
    tq = module("f04_terrain_query", pins["terrain_query_py"]["file"])
    lc = module("f04_local_contact", pins["local_contact_py"]["file"])
    return tb, tq, lc


# --- frame map (F02's declared rotation, det = +1) ------------------------------
def to_contact(p):
    """clearing (x, y, z) -> contact (x, -z, y)."""
    return (p[0], -p[2], p[1])


def to_clearing(q):
    """contact (a, b, c) -> clearing (a, c, -b). Inverse of to_contact."""
    return (q[0], q[2], -q[1])


# --- asset bodies ----------------------------------------------------------------
def ground_contact_body(bundle, lc):
    """F02's tied contact body: sliced from the RENDER ground section arrays."""
    section = bundle["render"]["sections"]["ground"]
    require(section["surface_id"] == GROUND_SURFACE_ID, "f04_render_section_id",
            section["surface_id"])
    vs = bundle["render"]["vertices"]
    idx = bundle["render"]["indices"]
    g0, g1 = section["index_start"], section["index_start"] + section["index_count"]
    v0, v1 = section["vertex_start"], section["vertex_start"] + section["vertex_count"]
    vertices = [to_contact(vs[9 * i:9 * i + 3]) for i in range(v0, v1)]
    triangles = [(idx[k], idx[k + 1], idx[k + 2]) for k in range(g0, g1, 3)]
    for t in triangles:
        require(all(v0 <= i < v1 for i in t), "f04_body_index_outside_ground", t)
    return lc.Body("terrain_ground", GROUND_SURFACE_ID, GROUND_MATTER_ID, 0.0,
                   GROUND_MU_S, GROUND_MU_K, GROUND_THICKNESS_M, vertices,
                   triangles, pinned=True)


def trunk_partition(trunk):
    """F03's declared center-vertex rule (lateral 64 / base_cap 32 / top_cap 32)."""
    tidx = trunk["render_mesh"]["indices"]
    ttris = [(tidx[k], tidx[k + 1], tidx[k + 2]) for k in range(0, len(tidx), 3)]
    groups = {
        "trunk_01.lateral": [t for t in ttris
                             if CENTER_VERTEX_BASE not in t
                             and CENTER_VERTEX_TOP not in t],
        "trunk_01.base_cap": [t for t in ttris if CENTER_VERTEX_BASE in t],
        "trunk_01.top_cap": [t for t in ttris if CENTER_VERTEX_TOP in t],
    }
    require([len(groups[k]) for k in
             ("trunk_01.lateral", "trunk_01.base_cap", "trunk_01.top_cap")]
            == [64, 32, 32], "f04_trunk_partition",
            [len(v) for v in groups.values()])
    return groups, ttris


def trunk_body(lc, groups, vertices, sid, mu_s=TRUNK_MU_S, mu_k=TRUNK_MU_K):
    return lc.Body(sid, sid, "wood_trunk_01", 1.0, mu_s, mu_k,
                   TRUNK_THICKNESS_M, vertices, list(groups[sid]), pinned=True)


BOX_LOCAL = [(-0.1, -0.1, -0.1), (0.1, -0.1, -0.1), (0.1, 0.1, -0.1),
             (-0.1, 0.1, -0.1), (-0.1, -0.1, 0.1), (0.1, -0.1, 0.1),
             (0.1, 0.1, 0.1), (-0.1, 0.1, 0.1)]
BOX_TRIANGLES = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5),
                 (0, 5, 4), (2, 3, 7), (2, 7, 6), (0, 4, 7), (0, 7, 3),
                 (1, 2, 6), (1, 6, 5)]
TETRA_LOCAL = ((0.0, 0.0, 0.0), (0.1, 0.0, 0.0), (0.0, 0.1, 0.0), (0.0, 0.0, 0.1))
TETRA_TRIS = ((0, 2, 1), (0, 1, 3), (0, 3, 2), (1, 2, 3))


def box_probe(lc, probe_id, centre, velocity):
    verts = [lc.vadd(centre, v) for v in BOX_LOCAL]
    return lc.Body(probe_id, probe_id, "mass_tetra", PROBE_MASS_KG,
                   PROBE_MU_S, PROBE_MU_K, PROBE_THICKNESS_M, verts,
                   list(BOX_TRIANGLES), velocity=tuple(velocity))


def tetra_probe(lc, probe_id, origin, basis=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
                                             (0.0, 0.0, 1.0))):
    ex, ey, ez = basis
    verts = [tuple(origin[i] + ex[i] * p[0] + ey[i] * p[1] + ez[i] * p[2]
                   for i in range(3)) for p in TETRA_LOCAL]
    return lc.Body(probe_id, probe_id, "probe_fixture", PROBE_MASS_KG,
                   1.0, 1.0, TRUNK_THICKNESS_M, verts, list(TETRA_TRIS),
                   velocity=(0.0, 0.0, 0.0))


# --- per-tick inspection helpers --------------------------------------------------
def ground_clearance_m(probe, surface):
    """Min height of any probe vertex above the local query height (contact
    frame; contact z = clearing y up). Negative = below the surface."""
    worst = None
    for v in probe.vertices:
        c = v[2] - surface.height_at(v[0], -v[1])
        worst = c if worst is None else min(worst, c)
    return worst


def trunk_clearance_m(probe, base, radius):
    """Min radial distance of any probe vertex to the analytic cylinder surface
    (negative = inside the solid)."""
    worst = None
    for v in probe.vertices:
        d = math.hypot(v[0] - base[0], v[1] - base[1]) - radius
        worst = d if worst is None else min(worst, d)
    return worst


def record_contacts(records, tick, bodies_by_id):
    out = []
    for r in records:
        out.append({
            "tick": tick, "kind": r["kind"], "toc": r["toc"],
            "gap_m": r["gap_m"], "penetration_m": r["penetration_m"],
            "jn_Ns": r["jn_Ns"], "jt_Ns": r["jt_Ns"], "mode": r["mode"],
            "surface_a": r["surface_a"], "surface_b": r["surface_b"],
            "matter_a": r["matter_a"], "matter_b": r["matter_b"],
            "point_clearing_a": list(to_clearing(r["point_a"])),
            "point_clearing_b": list(to_clearing(r["point_b"])),
            "normal_contact_to_a_clearing": list(
                to_clearing(tuple(r["normal"]))),
        })
    return out


def state_of(probe, tick, records, ledger, bodies, extra=None):
    xs = [v[0] for v in probe.vertices]
    ys = [v[1] for v in probe.vertices]
    zs = [v[2] for v in probe.vertices]
    centre_c = (sum(xs) / 8.0, sum(ys) / 8.0, sum(zs) / 8.0)
    st = {
        "tick": tick,
        "probe_centre_clearing_m": list(to_clearing(centre_c)),
        "probe_vertices_clearing_m": [list(to_clearing(v))
                                      for v in probe.vertices],
        "probe_velocity_contact_m_s": list(probe.velocity),
        "contacts": record_contacts(records, tick, None),
        "ledger_max_residual": max(lc_vlen(tuple(ledger["residual"][b.id]))
                                   for b in bodies),
    }
    if extra:
        st.update(extra)
    return st


def lc_vlen(a):
    return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


# --- frozen scenarios -------------------------------------------------------------
def scenario_g_high(lc, ground, surface, ccd=True, ghost_vertex=False,
                    vertex_raise_m=0.0):
    body = ground_contact_body_from(lc, ground, ghost_vertex, vertex_raise_m)
    h = surface.height_at(0.0, 0.0)
    probe = box_probe(lc, "probe_G", (0.0, 0.0, h + 0.5 + 0.1), (0.0, 0.0, -4.0))
    bodies = [body, probe]
    states = []
    for t in range(TICKS_G_HIGH):
        records, ledger = lc.solve_tick(bodies, ccd_enabled=ccd)
        states.append(state_of(probe, t, records, ledger, bodies,
                               {"min_clearance_above_query_m":
                                ground_clearance_m(probe, surface)}))
    return {"name": "G_HIGH", "states": states, "probe": probe,
            "body": body, "surface": surface, "kind": "ground"}


def ground_contact_body_from(lc, ground, ghost_vertex, vertex_raise_m):
    body = ground_contact_body(ground["bundle"], lc)
    if ghost_vertex:
        target = to_contact((0.0, 0.0, 0.0))
        best_i, best_d = None, None
        for i, v in enumerate(body.vertices):
            d = (v[0] - target[0]) ** 2 + (v[1] - target[1]) ** 2
            if best_d is None or d < best_d:
                best_i, best_d = i, d
        body.vertices[best_i] = lc.vadd(body.vertices[best_i],
                                        (0.0, 0.0, vertex_raise_m))
    return body


def scenario_t_cross(lc, trunk_assets, ccd=True, ghost=False):
    groups, vertices = trunk_assets["groups"], trunk_assets["vertices"]
    base, radius = trunk_assets["base"], trunk_assets["radius"]
    body = trunk_body(lc, groups, vertices, "trunk_01.lateral")
    if ghost:
        # radially inward ghost vertex on the impacted facet
        target = (BASE_APPROACH[0], BASE_APPROACH[1], 0.5)
        best_i, best_d = None, None
        for i, v in enumerate(body.vertices):
            d = (v[0] - target[0]) ** 2 + (v[2] - target[2]) ** 2
            if best_d is None or d < best_d:
                best_i, best_d = i, d
        v = body.vertices[best_i]
        radial = (v[0] - base[0], v[1] - base[1])
        rl = math.hypot(*radial) or 1.0
        newr = max(rl - 0.01, 0.0)
        body.vertices[best_i] = (base[0] + radial[0] * newr / rl,
                                 base[1] + radial[1] * newr / rl, v[2])
    probe = box_probe(lc, "probe_T", T_CROSS_START, T_CROSS_VEL)
    bodies = [body, probe]
    states = []
    for t in range(TICKS_T_CROSS):
        records, ledger = lc.solve_tick(bodies, ccd_enabled=ccd)
        states.append(state_of(probe, t, records, ledger, bodies,
                               {"min_radial_clearance_m":
                                trunk_clearance_m(probe, base, radius)}))
    return {"name": "T_CROSS", "states": states, "probe": probe,
            "body": body, "kind": "trunk"}


BASE_APPROACH = None  # set in build(); contact-frame facet anchor
T_CROSS_START = (11.626783, -2.471766, 0.5)
T_CROSS_VEL = (4.0, 0.0, 0.0)
SEAM_START = (11.263783, -2.471766, 0.14)
SEAM_VEL = (4.0, 0.0, 0.5)


def scenario_seam_high(lc, trunk_assets, surface):
    """SEAM_HIGH (Amendments A1+A5): ballistic approach -> trunk phase."""
    groups, vertices = trunk_assets["groups"], trunk_assets["vertices"]
    base, radius = trunk_assets["base"], trunk_assets["radius"]
    probe = box_probe(lc, "probe_S", SEAM_START, SEAM_VEL)
    states = []
    handover_tick = None
    t = 0
    while t < TICKS_SEAM_HIGH:
        face_d = (base[0] - radius) - max(v[0] for v in probe.vertices)
        if face_d <= 0.03:             # A5: 1.5 ticks' motion, PRE-tick
            handover_tick = t
            break
        records, ledger = lc.solve_tick([probe], ccd_enabled=True)
        states.append(state_of(probe, t, records, ledger, [probe],
                               {"min_clearance_above_query_m":
                                ground_clearance_m(probe, surface),
                                "phase": "A"}))
        t += 1
    require(handover_tick is not None, "f04_seam_no_handover")
    body = trunk_body(lc, groups, vertices, "trunk_01.lateral")
    bodies = [body, probe]
    tail = 0
    while t < TICKS_SEAM_HIGH:
        records, ledger = lc.solve_tick(bodies, ccd_enabled=True)
        contact_now = bool(records)
        # Per-phase metric law (prereg section 8: the tail value is measured
        # and published): phase-B states carry BOTH the trunk radial metric
        # AND the ground-oracle clearance, so a phase-B metric never has to
        # be derived by scanning phase-A states.
        states.append(state_of(probe, t, records, ledger, bodies,
                               {"min_radial_clearance_m":
                                trunk_clearance_m(probe, base, radius),
                                "min_clearance_above_query_m":
                                ground_clearance_m(probe, surface),
                                "phase": "B"}))
        if contact_now:
            tail += 1
            if tail >= 4:                 # contact tick + 3 frozen tail ticks
                break
        t += 1
    return {"name": "SEAM_HIGH", "states": states, "probe": probe,
            "body": body, "kind": "trunk", "handover_tick": handover_tick}


def scenario_g_seam_rest(lc, ground, surface):
    body = ground_contact_body(ground["bundle"], lc)
    x, z = 11.226783, 2.471766
    h = surface.height_at(x, z)
    probe = box_probe(lc, "probe_R4", (x, -z, h + 0.05 + 0.1), (0.2, 0.0, 0.0))
    bodies = [body, probe]
    states = []
    for t in range(TICKS_G_SEAM_REST):
        records, ledger = lc.solve_tick(bodies, ccd_enabled=True)
        states.append(state_of(probe, t, records, ledger, bodies,
                               {"min_clearance_above_query_m":
                                ground_clearance_m(probe, surface)}))
    return {"name": "G_SEAM_REST", "states": states, "probe": probe,
            "body": body, "surface": surface, "kind": "ground"}


def scenario_trunk_top_rest(lc, trunk_assets):
    groups, vertices = trunk_assets["groups"], trunk_assets["vertices"]
    base = trunk_assets["base"]
    height = trunk_assets["height"]
    bodies = [trunk_body(lc, groups, vertices, "trunk_01.base_cap"),
              trunk_body(lc, groups, vertices, "trunk_01.top_cap")]
    origin = (base[0] + 0.02, base[1] + 0.01, height + 2e-5)
    probe = tetra_probe(lc, "probe_cap", origin)
    bodies.append(probe)
    start = [tuple(v) for v in probe.vertices]
    states = []
    for t in range(TICKS_TRUNK_TOP_REST):
        records, ledger = lc.solve_tick(bodies, ccd_enabled=True)
        disp = max(lc_vlen(lc.vsub(tuple(pv), sv))
                   for pv, sv in zip(probe.vertices, start))
        states.append(state_of(probe, t, records, ledger, bodies,
                               {"max_displacement_m": disp}))
    return {"name": "TRUNK_TOP_REST", "states": states, "probe": probe,
            "kind": "trunk_cap"}


# --- asset-identity checks (P1) ----------------------------------------------------
def identity_checks(bundle_raw, bundle, trunk_raw, trunk, groups, tverts,
                    ground_body, lc):
    section = bundle["render"]["sections"]["ground"]
    vs = bundle["render"]["vertices"]
    v0, v1 = section["vertex_start"], section["vertex_start"] + section["vertex_count"]
    render_mapped = [to_contact(vs[9 * i:9 * i + 3]) for i in range(v0, v1)]
    ground_exact = render_mapped == ground_body.vertices
    worst_g = 0.0
    if not ground_exact:
        for a, b in zip(render_mapped, ground_body.vertices):
            worst_g = max(worst_g, max(abs(a[i] - b[i]) for i in range(3)))
    trunk_render = [to_contact(v[0:3]) for v in trunk["render_mesh"]["vertices"]]
    trunk_exact = trunk_render == tverts
    worst_t = 0.0
    if not trunk_exact:
        for a, b in zip(trunk_render, tverts):
            worst_t = max(worst_t, max(abs(a[i] - b[i]) for i in range(3)))
    half = bundle["collision"]["boundary"]["half_width_m"]
    ex = max(max(abs(v[0]), abs(v[1])) for v in ground_body.vertices)
    # trunk RING vertices against the analytic solid (declared 2e-4 tolerance;
    # F03 P6 form: lateral ring vertices; the two cap-centre vertices sit on
    # the solid by construction and are excluded)
    base = to_contact(trunk["site"]["base_centre_m"])
    radius = trunk["geometry"]["radius_m"]
    height = trunk["geometry"]["height_m"]
    worst_radial = 0.0
    worst_inside = 0.0
    for i, v in enumerate(tverts):
        if i >= CENTER_VERTEX_BASE:
            continue
        d = math.hypot(v[0] - base[0], v[1] - base[1])
        worst_radial = max(worst_radial, abs(d - radius))
        worst_inside = max(worst_inside, max(0.0, radius - d, -v[2],
                                             v[2] - height))
    return {
        "prediction": "P1_tied_asset_identity",
        "ground": {"vertex_count": len(ground_body.vertices),
                   "arrays_exact_equal": ground_exact,
                   "worst_component_diff": worst_g,
                   "surface_id": ground_body.surface_id,
                   "render_section_surface_id": section["surface_id"],
                   "contact_extent_max_abs_m": ex,
                   "rendered_half_width_m": half,
                   "extent_matches_render": abs(ex - half) <= 1e-9},
        "trunk": {"vertex_count": len(tverts),
                  "arrays_exact_equal": trunk_exact,
                  "worst_component_diff": worst_t,
                  "worst_radial_gap_to_analytic_m": worst_radial,
                  "declared_radial_tolerance_m": TRUNK_RADIAL_TOL_M,
                  "worst_inside_solid_m": worst_inside,
                  "triangle_partition": {k: len(v) for k, v in groups.items()}},
        "ground_bundle_raw_sha256": sha_bytes(bundle_raw),
        "trunk_declaration_raw_sha256": sha_bytes(trunk_raw),
        "ok": (ground_exact and trunk_exact
               and abs(ex - half) <= 1e-9
               and worst_radial <= TRUNK_RADIAL_TOL_M
               and worst_inside <= TRUNK_RADIAL_TOL_M),
    }


# --- combined instantiation (P0) ----------------------------------------------------
def combined_refusal_probe(lc, ground, trunk_assets):
    body = ground_contact_body(ground["bundle"], lc)
    trunk = trunk_body(lc, trunk_assets["groups"], trunk_assets["vertices"],
                       "trunk_01.lateral")
    outcome = {"prediction": "P0_combined_instantiation_refusal"}
    try:
        records, ledger = lc.solve_tick([body, trunk])
        outcome.update({"outcome": "solved", "record_count": len(records)})
    except ValueError as exc:
        outcome.update({"outcome": "refused", "code": str(exc),
                        "why": "trunk base ring touches the ground plane at "
                               "0.0 m; both-pinned exact contact has zero "
                               "inverse-mass sum (F03 A3 heritage at the "
                               "ground/trunk seam)"})
    return outcome


# --- metric extraction (P3/P4/P5/P6) ------------------------------------------------
def episode_firsts(states):
    """First contact record of each maximal run of contact-bearing ticks."""
    firsts = []
    in_episode = False
    for st in states:
        has = bool(st["contacts"])
        if has and not in_episode:
            firsts.append(st["contacts"][0])
        in_episode = has
    return firsts


def metric_worst(states, key):
    vals = [st[key] for st in states if key in st]
    return min(vals) if vals else None


def phase_metric(states, phase, key):
    """Per-phase metric extraction. Review law: NEVER derive a phase metric
    by scanning heterogeneous states -- filter by the recorded per-state
    phase tag and require every state of that phase to carry the key."""
    sel = [st for st in states if st.get("phase") == phase]
    require(sel, "f04_seam_phase_missing", phase)
    require(all(key in st for st in sel), "f04_seam_phase_metric_key_missing",
            {"phase": phase, "key": key})
    return min(st[key] for st in sel)


def contact_geometry_checks(scenarios, trunk_assets, surface):
    """P3/P4/P6 over the CCD-on runs."""
    worst_pen = 0.0
    worst_plane = 0.0
    worst_radial = 0.0
    seam_altitudes = []
    pre_overlap_ok = True
    record_count = 0
    for name in ("G_HIGH", "T_CROSS", "SEAM_HIGH", "G_SEAM_REST"):
        sc = scenarios[name]
        firsts = episode_firsts(sc["states"])
        for f in firsts:
            pre_overlap_ok = pre_overlap_ok and f["kind"] == "ccd" \
                and f["gap_m"] > 0.0
        for st in sc["states"]:
            record_count += len(st["contacts"])
            if "min_clearance_above_query_m" in st:
                worst_pen = max(worst_pen,
                                max(0.0, -st["min_clearance_above_query_m"]))
            if "min_radial_clearance_m" in st:
                worst_pen = max(worst_pen,
                                max(0.0, -st["min_radial_clearance_m"]))
            for c in st["contacts"]:
                p = c["point_clearing_a"]
                if c["surface_a"] == GROUND_SURFACE_ID \
                        or c["surface_b"] == GROUND_SURFACE_ID:
                    tri_h = surface.height_at(p[0], p[2])
                    worst_plane = max(worst_plane, abs(p[1] - tri_h))
                else:
                    base = trunk_assets["base_clearing"]
                    radius = trunk_assets["radius"]
                    d = math.hypot(p[0] - base[0], p[2] - base[2])
                    worst_radial = max(worst_radial, abs(d - radius))
                    if name == "SEAM_HIGH":
                        seam_altitudes.append(p[1])
    worst_pen = round(worst_pen, 15)
    # A5: the seam band applies to the FIRST trunk contact (the impact);
    # tail contacts are recorded and published unconditionally.
    impact_altitude = seam_altitudes[0] if seam_altitudes else None
    impact_in_band = (impact_altitude is not None
                      and SEAM_BAND_M[0] <= impact_altitude <= SEAM_BAND_M[1])
    return {
        "prediction": "P3_no_tunnelling__P4_no_interpenetration__"
                      "P6_contact_geometry",
        "ccd_on_contact_records": record_count,
        "episode_first_contacts_pre_overlap": pre_overlap_ok,
        "worst_penetration_m": worst_pen,
        "penetration_bar_m": PEN_BAR_M,
        "worst_ground_contact_plane_err_m": worst_plane,
        "plane_bar_m": PLANE_BAR_M,
        "worst_trunk_contact_radial_err_m": worst_radial,
        "trunk_radial_tolerance_m": TRUNK_RADIAL_TOL_M,
        "seam_band_m": list(SEAM_BAND_M),
        "seam_impact_altitude_m": impact_altitude,
        "seam_impact_in_band": impact_in_band,
        "seam_tail_contact_altitudes_m": seam_altitudes[1:],
        "ok": (pre_overlap_ok and worst_pen <= PEN_BAR_M
               and worst_plane <= PLANE_BAR_M
               and worst_radial <= TRUNK_RADIAL_TOL_M and impact_in_band),
    }


def rest_checks(scenarios, bundle, trunk_assets, surface):
    """P4 (resting) + P5 (no ghost support)."""
    rows = {}
    ok = True
    sc = scenarios["G_HIGH"]
    probe = sc["probe"]
    seps = [v[2] - surface.height_at(v[0], -v[1]) for v in probe.vertices]
    band = site_band(bundle, 0.0, 0.0)
    rows["G_HIGH"] = {
        "min_corner_separation_m": min(seps),
        "window_m": [REST_LO_M, REST_HI_M + band], "site_band_m": band,
        "final_speed_m_s": lc_vlen(probe.velocity),
        "in_window": REST_LO_M <= min(seps) <= REST_HI_M + band,
        "stopped": lc_vlen(probe.velocity) <= SPEED_BAR_M_S,
    }
    ok = ok and rows["G_HIGH"]["in_window"] and rows["G_HIGH"]["stopped"]
    sc = scenarios["G_SEAM_REST"]
    probe = sc["probe"]
    seps = [v[2] - surface.height_at(v[0], -v[1]) for v in probe.vertices]
    band = site_band(bundle, 11.226783, 2.471766)
    rest_x = sum(v[0] for v in probe.vertices) / 8.0
    clearance = (trunk_assets["base_clearing"][0]
                 - trunk_assets["radius"] - 0.1) - rest_x
    rows["G_SEAM_REST"] = {
        "min_corner_separation_m": min(seps),
        "window_m": [REST_LO_M, REST_HI_M + band], "site_band_m": band,
        "final_speed_m_s": lc_vlen(probe.velocity),
        "horizontal_displacement_m": abs(rest_x - 11.226783),
        "trunk_surface_clearance_m": clearance,
        "in_window": REST_LO_M <= min(seps) <= REST_HI_M + band,
        "stopped": lc_vlen(probe.velocity) <= SPEED_BAR_M_S,
        "clearance_positive": clearance > 0.0,
    }
    ok = ok and rows["G_SEAM_REST"]["in_window"] \
        and rows["G_SEAM_REST"]["stopped"] \
        and rows["G_SEAM_REST"]["clearance_positive"]
    sc = scenarios["TRUNK_TOP_REST"]
    disp = max(st.get("max_displacement_m", 0.0) for st in sc["states"])
    cap_contact = any("trunk_01.top_cap" in (c["surface_a"], c["surface_b"])
                      for st in sc["states"] for c in st["contacts"])
    last_records = sc["states"][-1]["contacts"]
    final_mode = last_records[-1]["mode"] if last_records else None
    rows["TRUNK_TOP_REST"] = {
        "max_displacement_m": disp, "bar_m": TRUNK_REST_DISP_BAR_M,
        "cap_contact_observed": cap_contact, "final_mode": final_mode,
        "ok_rest": disp <= TRUNK_REST_DISP_BAR_M and cap_contact,
    }
    ok = ok and rows["TRUNK_TOP_REST"]["ok_rest"]
    # P5: every support impulse maps to a real contact record (ledger identity
    # already enforced per tick by the module; assert residuals here).
    worst_resid = 0.0
    for name in ("G_HIGH", "T_CROSS", "SEAM_HIGH", "G_SEAM_REST",
                 "TRUNK_TOP_REST"):
        for st in scenarios[name]["states"]:
            worst_resid = max(worst_resid, st["ledger_max_residual"])
    return {"prediction": "P4_resting__P5_no_ghost_support",
            "rests": rows, "worst_ledger_residual": worst_resid,
            "ledger_bar": LEDGER_BAR,
            "ok": ok and worst_resid <= LEDGER_BAR}


def site_band(bundle, x, z, half=0.1):
    grid = bundle["terrain_surface"]["grid"]
    Hh = grid["heights_m"]
    worst = 0.0
    ix0 = max(0, int(math.floor((x - half - grid["x0_m"]) / grid["dx_m"])))
    ix1 = min(grid["nx"] - 2,
              int(math.floor((x + half - grid["x0_m"]) / grid["dx_m"])))
    iz0 = max(0, int(math.floor((z - half - grid["z0_m"]) / grid["dz_m"])))
    iz1 = min(grid["nz"] - 2,
              int(math.floor((z + half - grid["z0_m"]) / grid["dz_m"])))
    for iz in range(iz0, iz1 + 1):
        for ix in range(ix0, ix1 + 1):
            worst = max(worst, abs(Hh[iz][ix] - Hh[iz][ix + 1]
                                   - Hh[iz + 1][ix] + Hh[iz + 1][ix + 1]))
    return worst


# --- shared-path document (P2) ------------------------------------------------------
def shared_path_checks(lc, contact_law, scenarios):
    surfaces = [{
        "id": GROUND_SURFACE_ID, "matter_id": GROUND_MATTER_ID, "mass_kg": None,
        "pinned": True, "mu_s": GROUND_MU_S, "mu_k": GROUND_MU_K,
        "thickness_m": GROUND_THICKNESS_M, "triangle_count": 3200,
        "provenance": "MAT2-F02 tied terrain asset"},
        {"id": "trunk_01.lateral", "matter_id": "wood_trunk_01",
         "mass_kg": None, "pinned": True, "mu_s": TRUNK_MU_S,
         "mu_k": TRUNK_MU_K, "thickness_m": TRUNK_THICKNESS_M,
         "triangle_count": 64,
         "provenance": "MAT2-F03 pinned trunk lateral mesh"},
        {"id": "trunk_01.base_cap", "matter_id": "wood_trunk_01",
         "mass_kg": None, "pinned": True, "mu_s": TRUNK_MU_S,
         "mu_k": TRUNK_MU_K, "thickness_m": TRUNK_THICKNESS_M,
         "triangle_count": 32,
         "provenance": "MAT2-F03 pinned trunk base cap"},
        {"id": "trunk_01.top_cap", "matter_id": "wood_trunk_01",
         "mass_kg": None, "pinned": True, "mu_s": TRUNK_MU_S,
         "mu_k": TRUNK_MU_K, "thickness_m": TRUNK_THICKNESS_M,
         "triangle_count": 32,
         "provenance": "MAT2-F03 pinned trunk top cap"},
    ]
    known = {s["id"] for s in surfaces}
    for pid in ("probe_G", "probe_T", "probe_S", "probe_R4", "probe_cap"):
        surfaces.append({"id": pid, "matter_id": "mass_tetra",
                         "mass_kg": PROBE_MASS_KG, "pinned": False,
                         "mu_s": PROBE_MU_S, "mu_k": PROBE_MU_K,
                         "thickness_m": PROBE_THICKNESS_M,
                         "triangle_count": 12,
                         "provenance": "MAT2-F04 probe shell"})
        known.add(pid)
    contacts = []
    for name in ("G_HIGH", "T_CROSS", "SEAM_HIGH", "G_SEAM_REST",
                 "TRUNK_TOP_REST"):
        for c in scenarios[name]["states"][-1]["contacts"]:
            contacts.append({"surface_a": c["surface_a"],
                             "surface_b": c["surface_b"],
                             "matter_a": c["matter_a"],
                             "matter_b": c["matter_b"],
                             "gap_m": c["gap_m"]})
    doc = {"schema": lc.SCHEMA, "revision": 1,
           "object_id": "mat2-f04-contact-geometry",
           "declarations": dict(contact_law["declarations"]),
           "surfaces": surfaces, "contacts": contacts}
    lc.validate_local_contact(doc, known)
    total = sum(len(st["contacts"]) for name in
                ("G_HIGH", "T_CROSS", "SEAM_HIGH", "G_SEAM_REST",
                 "TRUNK_TOP_REST")
                for st in scenarios[name]["states"])
    worst = 0.0
    for name in ("G_HIGH", "T_CROSS", "SEAM_HIGH", "G_SEAM_REST",
                 "TRUNK_TOP_REST"):
        for st in scenarios[name]["states"]:
            worst = max(worst, st["ledger_max_residual"])
    return {"prediction": "P2_contact_through_shared_path",
            "module": "local_contact (vendored M06 byte-identical, sha256 "
                      + PINS["local_contact_py"]["sha256"] + ")",
            "contact_record_count_total": total,
            "last_tick_records_validated": len(contacts),
            "validator": "local_contact.validate_local_contact -> passed",
            "declarations_match_law": all(
                contact_law["declarations"].get(k) == v
                for k, v in lc.DECL_KEYS),
            "worst_ledger_residual": worst,
            "ok": worst <= LEDGER_BAR}


# --- renderer (F01/F03-adapted software rasterizer; presentation only) --------------
LIGHT = None  # set after vector helpers


def vsub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vadd(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vscale(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def vdot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vcross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def vlen(a):
    return math.sqrt(vdot(a, a))


def vnorm(a):
    n = vlen(a)
    require(n > 0.0, "degenerate_vector")
    return (a[0] / n, a[1] / n, a[2] / n)


LIGHT = vnorm((0.4, 0.8, 0.45))
AMBIENT = 0.55
COLOURS = {
    "ground_A": (0.16, 0.22, 0.17),
    "ground_B": (0.18, 0.24, 0.19),
    "monkey_clearing_boundary_posts": (0.72, 0.55, 0.20),
    "trunk_01.lateral": (0.36, 0.25, 0.16),
    "trunk_01.base_cap": (0.30, 0.21, 0.13),
    "trunk_01.top_cap": (0.42, 0.30, 0.19),
    "probe": (0.85, 0.15, 0.15),
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
        return (vdot(d, self.right) / (z * self.t * self.aspect),
                vdot(d, self.up) / (z * self.t), z)

    def pixel(self, world_point):
        n = self.ndc(world_point)
        if n is None:
            return None
        return ((n[0] + 1.0) * 0.5 * W, (1.0 - n[1]) * 0.5 * H, n[2])

    def ray_through_ndc(self, xn, yn):
        return vnorm([self.fwd[i] + xn * self.t * self.aspect * self.right[i]
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
            z = (m[0][2] + m[2][0]) / s
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
        return (q[0] / n, q[1] / n, q[2] / n, q[3] / n)

    def camera_record(self, ticks):
        q = self.quaternion_wxyz()
        return {
            "frame_id": "f01_world_y_up/MAT2-F04",
            "coordinate_unit": "m",
            "handedness": "right",
            "orientation_convention": "quaternion_wxyz_camera_to_frame",
            "forward_axis": "-Z",
            "up_axis": "+Y",
            "position": list(self.position),
            "orientation_convention_and_values": {
                "convention": "quaternion_wxyz_camera_to_frame",
                "quaternion_wxyz": list(q)},
            "target": list(self.target),
            "distance_to_target": self.distance_to_target,
            "projection": "perspective",
            "vertical_fov_or_orthographic_span_deg": self.spec["vfov_deg"],
            "near_far_planes": list(self.spec["near_far"]),
            "aspect_ratio": W / H,
            "viewport_resolution": [W, H],
            "camera_motion_or_bookmark_sequence": {
                "sample_mode": "fixed_bookmark",
                "samples": [{"tick": t,
                             "position": list(self.position),
                             "target": list(self.target),
                             "distance_to_target": self.distance_to_target,
                             "orientation": list(q)}
                            for t in ticks]},
            "visibility_layers": None,
            "label_ids": None,
            "occlusion_or_xray_mode": "depth_tested",
            "state_or_tick_interval": list(ticks),
            "vertical_fov_degrees": self.spec["vfov_deg"],
            "quaternion_wxyz": list(q),
        }


class SceneMesh:
    """The pinned render arrays (ground + posts) plus the pinned trunk mesh as
    raycast/raster targets; the probe shell is passed per draw."""

    def __init__(self, bundle, trunk, tverts, groups):
        self.vertices = bundle["render"]["vertices"]
        self.indices = bundle["render"]["indices"]
        self.ground = bundle["render"]["sections"]["ground"]
        self.trunk_vertices = tverts
        self.groups = groups
        self.geom = {"base_centre_m": trunk["site"]["base_centre_m"],
                     "radius_m": trunk["geometry"]["radius_m"],
                     "height_m": trunk["geometry"]["height_m"]}
        self.probe_tris = []

    def set_probe(self, verts_clearing):
        tris = TETRA_TRIS if len(verts_clearing) == 4 else BOX_TRIANGLES
        self.probe_tris = [(verts_clearing[a], verts_clearing[b],
                            verts_clearing[c], "probe")
                           for a, b, c in tris]

    def _trunk_tris(self):
        for sid in ("trunk_01.lateral", "trunk_01.base_cap",
                    "trunk_01.top_cap"):
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

    def triangles(self):
        yield from self.scene_tris()
        yield from self.probe_tris

    def first_hit(self, orig, direc, with_probe=True):
        best = None
        for va, vb, vc, sid in self.scene_tris():
            hit = ray_triangle(orig, direc, va, vb, vc)
            if hit is not None and (best is None or hit[0] < best[0]):
                n = vnorm(vcross(vsub(vb, va), vsub(vc, va)))
                best = (hit[0], sid, n)
        if with_probe:
            for va, vb, vc, sid in self.probe_tris:
                hit = ray_triangle(orig, direc, va, vb, vc)
                if hit is not None and (best is None or hit[0] < best[0]):
                    best = (hit[0], sid, None)
        return best

    def hit_ground_triangle(self, orig, direc):
        """The ground triangle the ray hits first: (t, vertex_index_triple)."""
        best = None
        idx = self.indices
        g = self.ground
        g_end = g["index_start"] + g["index_count"]
        for k in range(0, g_end, 3):
            a, b, c = idx[k], idx[k + 1], idx[k + 2]
            hit = ray_triangle(orig, direc,
                               tuple(self.vertices[9 * a:9 * a + 3]),
                               tuple(self.vertices[9 * b:9 * b + 3]),
                               tuple(self.vertices[9 * c:9 * c + 3]))
            if hit is not None and (best is None or hit[0] < best[0]):
                best = (hit[0], (a, b, c))
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


def raster_tri(cam, colour, depth, pa, pb, pc, rgb, near, far):
    a = cam.pixel(pa)
    b = cam.pixel(pb)
    c = cam.pixel(pc)
    if a is None or b is None or c is None:
        return 0
    if a[2] < near or b[2] < near or c[2] < near:
        return 0
    if a[2] > far and b[2] > far and c[2] > far:
        return 0
    x0 = max(0, int(math.floor(min(a[0], b[0], c[0]))))
    x1 = min(W - 1, int(math.ceil(max(a[0], b[0], c[0]))))
    y0 = max(0, int(math.floor(min(a[1], b[1], c[1]))))
    y1 = min(H - 1, int(math.ceil(max(a[1], b[1], c[1]))))
    if x1 < x0 or y1 < y0:
        return 0
    area = ((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1]))
    if abs(area) < 1e-12:
        return 0
    inv_area = 1.0 / area
    n_drawn = 1
    for py in range(y0, y1 + 1):
        sy = py + 0.5
        row_c = colour[py]
        row_d = depth[py]
        for px in range(x0, x1 + 1):
            sx = px + 0.5
            w0 = ((b[0] - sx) * (c[1] - sy) - (c[0] - sx) * (b[1] - sy)) * inv_area
            if w0 < 0.0:
                continue
            w1 = ((c[0] - sx) * (a[1] - sy) - (a[0] - sx) * (c[1] - sy)) * inv_area
            if w1 < 0.0:
                continue
            w2 = 1.0 - w0 - w1
            if w2 < 0.0:
                continue
            z = 1.0 / (w0 / a[2] + w1 / b[2] + w2 / c[2])
            if z < row_d[px]:
                row_d[px] = z
                row_c[px] = rgb
    return n_drawn


def render_static(mesh, cam, diagnostic):
    colour = [[(8, 12, 10)] * W for _ in range(H)]
    depth = [[math.inf] * W for _ in range(H)]
    near, far = cam.spec["near_far"]
    tris = 0
    for va, vb, vc, sid in mesh.scene_tris():
        if sid == "monkey_clearing_ground":
            gx = int(math.floor((va[0] + vb[0] + vc[0]) / 3.0))
            gz = int(math.floor((va[2] + vb[2] + vc[2]) / 3.0))
            col = COLOURS["ground_A"] if (gx + gz) % 2 == 0 \
                else COLOURS["ground_B"]
        else:
            col = COLOURS[sid]
        n = vnorm(vcross(vsub(vb, va), vsub(vc, va)))
        lam = AMBIENT + (1.0 - AMBIENT) * max(0.0, vdot(n, LIGHT))
        rgb = tuple(min(255, int(c * lam * 255.0 + 0.5)) for c in col)
        tris += raster_tri(cam, colour, depth, va, vb, vc, rgb, near, far)
    if diagnostic:
        _static_diagnostic(mesh, cam, colour)
    return colour, depth, {"triangles_drawn": tris}


def _line(colour, x0, y0, x1, y1, rgb):
    steps = max(abs(int(round(x1 - x0))), abs(int(round(y1 - y0))), 1)
    for i in range(steps + 1):
        x = int(round(x0 + (x1 - x0) * i / steps))
        y = int(round(y0 + (y1 - y0) * i / steps))
        if 0 <= x < W and 0 <= y < H:
            colour[y][x] = rgb


def _static_diagnostic(mesh, cam, colour):
    magenta = (255, 0, 255)
    half = 20.0
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
    g0 = mesh.ground["index_start"]
    g1 = g0 + mesh.ground["index_count"]
    for k in range(g0, g1, 3):
        trip = []
        skip = False
        for j in range(3):
            v = mesh.vertices[9 * mesh.indices[k + j]:9 * mesh.indices[k + j] + 3]
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
    for va, vb, vc, sid in mesh._trunk_tris():
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
        for i in range(3):
            _line(colour, trip[i][0], trip[i][1],
                  trip[(i + 1) % 3][0], trip[(i + 1) % 3][1], (90, 110, 95))


def frame_from_state(mesh, cam, base_colour, base_depth, state, diagnostic):
    colour = [row[:] for row in base_colour]
    depth = [row[:] for row in base_depth]
    near, far = cam.spec["near_far"]
    verts = state["probe_vertices_clearing_m"]
    mesh.set_probe(verts)
    for a, b, c in (TETRA_TRIS if len(verts) == 4 else BOX_TRIANGLES):
        rgb = tuple(int(x * 255.0 + 0.5) for x in COLOURS["probe"])
        raster_tri(cam, colour, depth, verts[a], verts[b], verts[c],
                   rgb, near, far)
    if diagnostic:
        path = [tuple(st["probe_centre_clearing_m"]) for st in
                state["_scenario_states"][:state["_index"] + 1]]
        for i in range(1, len(path)):
            a = cam.pixel(path[i - 1])
            b = cam.pixel(path[i])
            if a and b:
                _line(colour, a[0], a[1], b[0], b[1], (0, 128, 255))
        marks = _contact_marks(state)
        cyan = (0, 255, 255)
        yellow = (255, 255, 0)
        for p, n in marks:
            base = cam.pixel(p)
            if base is None:
                continue
            tip = cam.pixel([p[0] + 0.12 * n[0], p[1] + 0.12 * n[1],
                             p[2] + 0.12 * n[2]])
            if tip is not None:
                _line(colour, base[0], base[1], tip[0], tip[1], cyan)
            x, y = int(base[0]), int(base[1])
            for dx, dy in ((-4, 0), (4, 0), (0, -4), (0, 4), (0, 0)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < W and 0 <= yy < H:
                    colour[yy][xx] = yellow
    return colour


def _contact_marks(state):
    """Episode-first and current-tick contacts (declared marker subset)."""
    out = []
    marks = []
    seen = set()
    scenario_states = state["_scenario_states"]
    idx = state["_index"]
    firsts = episode_firsts(scenario_states[:idx + 1])
    for c in firsts:
        key = tuple(round(x, 6) for x in c["point_clearing_a"])
        if key not in seen:
            seen.add(key)
            marks.append(c)
    for c in state["contacts"]:
        marks.append(c)
    for c in marks:
        p = tuple(c["point_clearing_a"])
        n = c["normal_contact_to_a_clearing"]
        nn = vnorm((-n[0], -n[1], -n[2]))  # contact normal points toward A
        out.append((p, nn))
    return out


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


def frame_bytes(colour):
    pad = (W * 3 + 3) & ~3
    buf = bytearray(pad * H)
    for y in range(H):
        # TOP-DOWN rows: ffmpeg's rawvideo rgb24 pipe consumes rows from the
        # top line down (unlike the BMP container, which stores rows
        # bottom-up; write_bmp handles that flip itself). Writing
        # colour[H-1-y] here mirrored every decoded frame against the bound
        # camera and the committed stills.
        src = colour[y]
        row = y * pad
        for x in range(W):
            r, g, b = src[x]
            i = row + x * 3
            buf[i] = b
            buf[i + 1] = g
            buf[i + 2] = r
    return bytes(buf)


def encode_video(path, frames_iter, total_frames):
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H),
           "-r", str(FPS), "-i", "pipe:",
           "-c:v", "ffv1", "-level", "3", "-coder", "1", "-g", "1",
           "-f", "avi", "-y", str(path)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    count = 0
    for colour in frames_iter:
        proc.stdin.write(frame_bytes(colour))
        count += 1
    proc.stdin.close()
    rc = proc.wait()
    require(rc == 0 and count == total_frames, "f04_video_encode_failed",
            {"rc": rc, "frames": count})
    return count


def probe_video(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
         "-show_entries",
         "stream=codec_name,width,height,nb_read_packets,avg_frame_rate",
         "-of", "json", str(path)],
        capture_output=True, text=True, timeout=600)
    require(out.returncode == 0, "f04_video_probe_failed", out.stderr[-400:])
    info = json.loads(out.stdout)["streams"][0]
    return info


# --- marker classify (pure ray/geometry; markers never read pixels) -----------------
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
            out.append(vnorm(vcross(vsub(pb, pa), vsub(pc, pa))))
    require(out, "f04_no_incident_ground_face", (x, z))
    return out


def classify_marker(mesh, cam, marker):
    """Pure ray/geometry classify of one contact marker. The ray targets the
    marker's classify_point: the contact point nudged 1 mm ALONG its facet
    (ground: +x; trunk lateral: +axis; cap: in-plane), because the exact
    contact points land on shared vertices/cap centres where the ray-triangle
    test is degenerate (F01 A3 heritage). The nudge stays on the same facet,
    so the frozen height/radial/normal bars are unchanged."""
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
    rec["margin_fraction"] = min(px, W - px) / W, min(py, H - py) / H
    direc = cam.ray_through_ndc(ndc[0], ndc[1])
    pd = vlen(vsub(point, cam.position))
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
    if marker["kind"] == "ground":
        h = marker["oracle_h"]
        hit_point = [cam.position[i] + t * direc[i] for i in range(3)]
        rec["height_err_m"] = abs(hit_point[1] - h)
        n_set = marker["oracle_n_set"]
        rec["normal_err"] = min(max(abs(hit_n[i] - cand[i]) for i in range(3))
                                for cand in n_set)
        rec["ok_bars"] = (rec["height_err_m"] <= HEIGHT_BAR_M
                          and rec["normal_err"] <= 1e-12)
    elif marker["kind"] in ("trunk", "trunk_cap"):
        geom = mesh.geom
        base = geom["base_centre_m"]
        if marker["kind"] == "trunk":
            d = math.hypot(marker["point"][0] - base[0],
                           marker["point"][2] - base[2])
            rec["radial_err_m"] = abs(d - geom["radius_m"])
            rec["ok_bars"] = rec["radial_err_m"] <= TRUNK_RADIAL_TOL_M
        else:
            rec["cap_height_err_m"] = abs(marker["point"][1]
                                          - marker["cap_y"])
            rec["ok_bars"] = rec["cap_height_err_m"] <= HEIGHT_BAR_M
        n = marker["oracle_n"]
        cosang = max(-1.0, min(1.0, vdot(n, marker.get("facet_n", n))))
        rec["normal_angle_rad"] = math.acos(cosang)
        rec["ok_bars"] = rec["ok_bars"] and rec["normal_angle_rad"] <= \
            math.pi / TRUNK_RING_SEGMENTS + TRUNK_NORMAL_ANGULAR_SLACK
    else:
        rec["ok_bars"] = True
    rec["outcome"] = ("VISIBLE_EXACT" if rec["ok_bars"]
                      else "VISIBLE_BUT_MISMATCH")
    return rec


def silhouette_predicts_trunk_occlusion(cam, mesh, point):
    geom = mesh.geom
    axis = geom["base_centre_m"]
    radius = geom["radius_m"]
    d = [point[0] - cam.position[0], point[2] - cam.position[2]]
    seg2 = d[0] * d[0] + d[1] * d[1]
    require(seg2 > 1e-18, "f04_silhouette_degenerate")
    tt = ((axis[0] - cam.position[0]) * d[0]
          + (axis[2] - cam.position[2]) * d[1]) / seg2
    tt = max(0.0, min(1.0, tt))
    qx = cam.position[0] + tt * d[0] - axis[0]
    qz = cam.position[2] + tt * d[1] - axis[2]
    return math.hypot(qx, qz) < radius


def nudge_trunk_point(point, base_clearing, radius,
                      delta_segments=0.5):
    """A contact point's classify point: snapped to the mid-facet azimuth of
    the ring segment containing the contact (exactly ON the facet chord), so
    the classify ray hits a triangle interior instead of the shared feature
    edge/vertex the solver reported. The marker bars are unchanged: the radial
    oracle reads the contact point (within the declared 2e-4 chord tolerance)
    and the facet-normal slack covers the half-segment offset."""
    bx, bz = base_clearing[0], base_clearing[2]
    seg = 2.0 * math.pi / TRUNK_RING_SEGMENTS
    az = math.atan2(point[2] - bz, point[0] - bx)
    k = int(math.floor((az % (2.0 * math.pi)) / seg)) % TRUNK_RING_SEGMENTS
    az_mid = (k + delta_segments) * seg
    r = radius * math.cos(math.pi / TRUNK_RING_SEGMENTS)
    return (bx + r * math.cos(az_mid), point[1], bz + r * math.sin(az_mid))


def trunk_subject_probe(cam, trunk_assets, altitude):
    """A camera-facing trunk surface subject (F03's frozen-probe pattern): the
    pinned lateral facet facing the camera, at mid-facet azimuth, placed just
    inside the facet chord so the classify ray hits a triangle interior --
    never a shared feature edge."""
    base = trunk_assets["base_clearing"]
    radius = trunk_assets["radius"]
    az_cam = math.atan2(cam.position[2] - base[2], cam.position[0] - base[0])
    seg = 2.0 * math.pi / TRUNK_RING_SEGMENTS
    k = int(math.floor((az_cam % (2.0 * math.pi)) / seg)) % TRUNK_RING_SEGMENTS
    az = (k + 0.5) * seg
    r = radius * math.cos(math.pi / TRUNK_RING_SEGMENTS)
    point = (base[0] + r * math.cos(az), altitude, base[2] + r * math.sin(az))
    n = vnorm((math.cos(az), 0.0, math.sin(az)))
    return {"point": point, "surface": "trunk_01.lateral", "kind": "trunk",
            "oracle_n": n, "id": "subject_trunk"}


# --- registry profile ----------------------------------------------------------------
def read_registry_profile():
    require(REGISTRY_SQLITE.is_file(), "f04_registry_missing",
            str(REGISTRY_SQLITE))
    uri = "file:%s?mode=ro" % REGISTRY_SQLITE.as_posix()
    con = sqlite3.connect(uri, uri=True)
    try:
        payload = con.execute(
            "select payload from state where id = 1").fetchone()
    finally:
        con.close()
    require(payload is not None, "f04_registry_empty")
    state = json.loads(payload[0])
    card = state["kanban"]["cards"]["MAT2-F04"]
    prof = card["spec"]["ontology_qualification"]["task"][
        "verification_profile"]
    require(prof["id"] == "contact-motion" and prof["kind"] == "motion",
            "f04_registry_profile_wrong", prof.get("id"))
    canon = digest(prof)
    attempt = card["attempts"]["c4064f0e999c40b3a9b18892b034f83c"]
    require(attempt["criteria_sha256"] == CRITERIA_SHA256,
            "f04_criteria_drift", attempt["criteria_sha256"])
    return prof, {"canonical_sha256": canon, "read_from": str(REGISTRY_SQLITE),
                  "mode": "read_only", "attempt_state": attempt["state"]}


# --- falsifier arms (run FIRST; each must bite) ---------------------------------------
def run_bites(lc, bundle, surface, trunk_assets):
    bites = []

    def add(arm, observed, bites_=None, extra=None):
        row = {"bite": arm, "bites": bool(bites_), "observed": observed}
        if extra:
            row.update(extra)
        bites.append(row)
        return row

    # FB1: CCD-off ground control tunnels. Clean control (prereg bite clause):
    # the SAME trajectory under the shipped CCD-on law must be pre-overlap
    # clean, or the bite is not credited (F03 heritage premature guard).
    sc = scenario_g_high(lc, {"bundle": bundle}, surface, ccd=False)
    firsts = episode_firsts(sc["states"])
    worst = metric_worst(sc["states"], "min_clearance_above_query_m")
    sc_on = scenario_g_high(lc, {"bundle": bundle}, surface, ccd=True)
    on_firsts = episode_firsts(sc_on["states"])
    on_worst = metric_worst(sc_on["states"], "min_clearance_above_query_m")
    on_clean = (bool(on_firsts) and on_firsts[0]["kind"] == "ccd"
                and on_firsts[0]["gap_m"] > 0.0 and on_worst >= -PEN_BAR_M)
    require(on_clean, "f04_fb1_premature",
            {"first_contact": on_firsts[0] if on_firsts else None,
             "worst_clearance_m": on_worst})
    bit = (bool(firsts) and firsts[0]["gap_m"] < 0.0 and worst < -PEN_BAR_M
           and on_clean)
    add("FB1_ccd_off_ground_tunnels",
        {"first_contact": firsts[0] if firsts else None,
         "worst_clearance_m": worst, "pen_bar_m": PEN_BAR_M,
         "clean_control": {"run": "G_HIGH same trajectory, CCD on",
                           "first_contact": on_firsts[0] if on_firsts else None,
                           "worst_clearance_m": on_worst,
                           "pre_overlap_clean": on_clean,
                           "guard": "f04_fb1_premature"}}, bit)
    # FB2: CCD-off trunk control tunnels (Amendment A2 form: late detection
    # after mid-surface overlap; pass-through is impossible at the frozen speed)
    sc = scenario_t_cross(lc, trunk_assets, ccd=False)
    firsts = episode_firsts(sc["states"])
    worst = metric_worst(sc["states"], "min_radial_clearance_m")
    # clean control: the shipped CCD-on trunk run is pre-overlap clean
    t_clean = scenario_t_cross(lc, trunk_assets, ccd=True)
    t_clean_firsts = episode_firsts(t_clean["states"])
    t_clean_worst = metric_worst(t_clean["states"], "min_radial_clearance_m")
    t_clean_ok = (bool(t_clean_firsts)
                  and t_clean_firsts[0]["kind"] == "ccd"
                  and t_clean_firsts[0]["gap_m"] > 0.0
                  and t_clean_worst >= -PEN_BAR_M)
    require(t_clean_ok, "f04_fb2_premature",
            {"first_contact": t_clean_firsts[0] if t_clean_firsts else None,
             "worst_radial_clearance_m": t_clean_worst})
    crossed = any(v[0] > trunk_assets["base"][0] + trunk_assets["radius"]
                  for st in sc["states"]
                  for v in st["probe_vertices_clearing_m"])
    pen_at_detection = (-firsts[0]["gap_m"]) if firsts else 0.0
    bit = bool(firsts) and firsts[0]["gap_m"] < 0.0 \
        and pen_at_detection > PEN_BAR_M and t_clean_ok
    add("FB2_ccd_off_trunk_tunnels",
        {"first_contact": firsts[0] if firsts else None,
         "penetration_at_detection_m": pen_at_detection,
         "pen_bar_m": PEN_BAR_M,
         "worst_radial_clearance_m": worst,
         "passed_through_far_side": crossed,
         "clean_control": {"run": "T_CROSS clean, CCD on",
                           "first_contact": t_clean_firsts[0]
                           if t_clean_firsts else None,
                           "worst_radial_clearance_m": t_clean_worst,
                           "pre_overlap_clean": t_clean_ok,
                           "guard": "f04_fb2_premature"},
         "form": "A2: late detection after mid-surface overlap (M06 X4 "
                 "control signature); 0.02 m/tick < 0.074 m trunk diameter "
                 "so full pass-through is geometrically impossible here"}, bit)
    # FB3: ghost ground vertex. Clean control: the unperturbed G_HIGH run
    # (sc_on, FB1's control) rests inside the frozen window and stops.
    sc = scenario_g_high(lc, {"bundle": bundle}, surface, ccd=True,
                         ghost_vertex=True, vertex_raise_m=0.01)
    probe = sc["probe"]
    seps = [v[2] - surface.height_at(v[0], -v[1]) for v in probe.vertices]
    band = site_band(bundle, 0.0, 0.0)
    sep = min(seps)
    on_probe = sc_on["probe"]
    on_seps = [v[2] - surface.height_at(v[0], -v[1]) for v in on_probe.vertices]
    clean_rest_ok = (REST_LO_M <= min(on_seps) <= REST_HI_M + band
                     and lc_vlen(on_probe.velocity) <= SPEED_BAR_M_S)
    require(clean_rest_ok, "f04_fb3_premature",
            {"min_corner_separation_m": min(on_seps),
             "window_m": [REST_LO_M, REST_HI_M + band]})
    bit = (not (REST_LO_M <= sep <= REST_HI_M + band)) and clean_rest_ok
    add("FB3_ghost_support_ground",
        {"min_corner_separation_m": sep,
         "window_m": [REST_LO_M, REST_HI_M + band],
         "clean_control": {"run": "G_HIGH clean (FB1 control run)",
                           "min_corner_separation_m": min(on_seps),
                           "window_m": [REST_LO_M, REST_HI_M + band],
                           "in_window_and_stopped": clean_rest_ok,
                           "guard": "f04_fb3_premature"}}, bit)
    # FB4: ghost trunk vertex (radially inward 1 cm; F03 B1 form). The metric
    # is P1's own scope: per-vertex radial gap of the collision body against
    # the analytic cylinder -- which IS the render array (P1 exact equality) --
    # with the two cap-centre vertices excluded (i >= CENTER_VERTEX_BASE; they
    # sit ON the axis by construction, exactly as identity_checks excludes
    # them). Without that scope the clean body already reads 0.037 (cap
    # centres) and the arm fires with no ghost. House standard (F03 heritage
    # premature guard): the clean control runs first and the bite is credited
    # only if it passes.
    def p1_scoped_radial_gap(vertices):
        worst = 0.0
        for i, v in enumerate(vertices):
            if i >= CENTER_VERTEX_BASE:
                continue
            d = math.hypot(v[0] - base[0], v[1] - base[1])
            worst = max(worst, abs(d - radius))
        return worst

    base = trunk_assets["base"]
    radius = trunk_assets["radius"]
    clean_body = trunk_body(lc, trunk_assets["groups"],
                            trunk_assets["vertices"], "trunk_01.lateral")
    clean_worst = p1_scoped_radial_gap(clean_body.vertices)
    require(clean_worst <= TRUNK_RADIAL_TOL_M, "f04_fb4_premature",
            clean_worst)
    sc = scenario_t_cross(lc, trunk_assets, ccd=True, ghost=True)
    worst = p1_scoped_radial_gap(sc["body"].vertices)
    bit = worst > TRUNK_RADIAL_TOL_M and clean_worst <= TRUNK_RADIAL_TOL_M
    add("FB4_ghost_support_trunk",
        {"worst_vertex_radial_gap_m": worst,
         "declared_tolerance_m": TRUNK_RADIAL_TOL_M,
         "clean_control": {"metric_scope": "P1 form: cap-centre vertices "
                           "(i >= %d) excluded" % CENTER_VERTEX_BASE,
                           "worst_vertex_radial_gap_m": clean_worst,
                           "within_tolerance":
                           clean_worst <= TRUNK_RADIAL_TOL_M,
                           "guard": "f04_fb4_premature"}}, bit)
    # FB5: forced interpenetration (probe corner starts 1 cm inside the solid)
    body = trunk_body(lc, trunk_assets["groups"], trunk_assets["vertices"],
                      "trunk_01.lateral")
    base = trunk_assets["base"]
    forced_centre = (base[0] - (trunk_assets["radius"] - 0.01) - 0.1,
                     base[1] - 0.1, 0.5)
    probe = box_probe(lc, "probe_FB5", forced_centre, (0.0, 0.0, 0.0))
    records, ledger = lc.solve_tick([body, probe], ccd_enabled=True)
    pen = -trunk_clearance_m(probe, base, trunk_assets["radius"])
    require(t_clean_ok, "f04_fb5_premature", t_clean_worst)
    bit = pen > PEN_BAR_M and len(records) > 0 and t_clean_ok
    add("FB5_forced_interpenetration",
        {"measured_penetration_m": pen, "pen_bar_m": PEN_BAR_M,
         "contact_records": len(records),
         "clean_control": {"run": "T_CROSS clean, CCD on (FB2 control run)",
                           "worst_radial_clearance_m": t_clean_worst,
                           "no_interpenetration": t_clean_worst >= -PEN_BAR_M,
                           "guard": "f04_fb5_premature"},
         "placement": "nearest box corner forced 0.01 m inside the analytic "
                      "cylinder (box half 0.1 m > trunk radius 0.037 m, so "
                      "axis-centring would place no vertex inside)"}, bit)
    # FB6: visual/collision decouple (render copy perturbed, collision intact).
    # The marker sits at a cell interior (the S1 spawn point is a grid NODE,
    # where the classify ray ties across the shared vertex -- F01 A3's
    # degenerate case); the raise is applied to ALL THREE vertices of the
    # ground triangle the ray actually hits (Amendments A3+A4).
    import copy as _copy
    mx, mz = 0.21, 0.13
    mesh_true = SceneMesh(bundle, _trunk_for_fb(lc, trunk_assets),
                          tverts_cache(), trunk_assets["groups"])
    marker = ground_marker_for(lc, bundle, surface, sc=(mx, mz),
                               mesh=mesh_true)
    cam = Camera(VIEW_SPECS["V1_clearing_overview"])
    ndc = cam.ndc(marker["point"])
    direc = cam.ray_through_ndc(ndc[0], ndc[1])
    hit_t, hit_verts = mesh_true.hit_ground_triangle(cam.position, direc)
    bundle2 = _copy.deepcopy(bundle)
    for vidx in hit_verts:                 # A3: raise the whole hit triangle
        bundle2["render"]["vertices"][vidx * 9 + 1] += 0.01
    mesh = SceneMesh(bundle2, _trunk_for_fb(lc, trunk_assets), tverts_cache(),
                     trunk_assets["groups"])
    rec = classify_marker(mesh, cam, marker)
    rec_true = classify_marker(mesh_true, cam, marker)
    identity_fired = bundle2["render"]["vertices"] != bundle["render"]["vertices"]
    # A4 form: the decouple flips the classification off VISIBLE_EXACT
    bit = (identity_fired
           and rec_true["outcome"] == "VISIBLE_EXACT"
           and rec["outcome"] in ("VISIBLE_BUT_MISMATCH", "OCCLUDED"))
    add("FB6_visual_collision_decouple",
        {"perturbed_render_vertices": list(hit_verts), "raised_m": 0.01,
         "ray_hit_triangle_vertices": list(hit_verts),
         "marker_xy": [mx, mz],
         "clean_control": {"run": "classify on the UNPERTURBED render, "
                           "same ray and marker",
                           "outcome": rec_true["outcome"],
                           "visible_exact": rec_true["outcome"]
                           == "VISIBLE_EXACT",
                           "guard": "bit requires the clean control "
                                    "VISIBLE_EXACT"},
         "marker_outcome_true_render": rec_true["outcome"],
         "marker_outcome_decoupled_render": rec["outcome"],
         "decouple_note": rec.get("note", ""),
         "form": "A3/A4: raise the whole ray-hit triangle; loss of "
                 "VISIBLE_EXACT is the discriminator; the marker is at a "
                 "cell interior because the spawn point is a degenerate "
                 "grid node (F01 A3)"}, bit)
    # FB7: off-frame probe subject. Clean control: an in-frame trunk subject
    # in the SAME view classifies VISIBLE_EXACT (the classifier is not
    # vacuously OFF_FRAME).
    cam2 = Camera(VIEW_SPECS["V2_seam_closeup"])
    fwd = vnorm(vsub(cam2.target, cam2.position))
    point = [-20.0, 0.9, -20.0]
    d = vsub(point, cam2.position)
    dot = vdot(d, fwd) / vlen(d)
    off_axis = math.degrees(math.acos(max(-1.0, min(1.0, dot))))
    m = {"point": point, "surface": "monkey_clearing_boundary_posts",
         "kind": "identity"}
    rec = classify_marker(mesh2_for_fb7(bundle, trunk_assets), cam2, m)
    sp_on = trunk_subject_probe(cam2, trunk_assets, 0.3)
    rec_on = classify_marker(mesh2_for_fb7(bundle, trunk_assets), cam2, sp_on)
    on_clean7 = rec_on["outcome"] == "VISIBLE_EXACT"
    require(on_clean7, "f04_fb7_premature", rec_on)
    bit = ((dot <= 0.0 or off_axis > 90.0)
           and rec["outcome"] == "OFF_FRAME" and on_clean7)
    add("FB7_off_frame_probe_subject",
        {"off_axis_deg": off_axis, "outcome": rec["outcome"],
         "clean_control": {"run": "trunk_subject_probe in the same V2 view",
                           "outcome": rec_on["outcome"],
                           "visible_exact": on_clean7,
                           "guard": "f04_fb7_premature"}}, bit)

    for row in bites:
        require(row["bites"], "f04_falsifier_did_not_bite", row["bite"])
    return bites


def _trunk_for_fb(lc, trunk_assets):
    return trunk_assets["declaration"]


def tverts_cache():
    return TRUNK_VERTS_CACHE


TRUNK_VERTS_CACHE = None


def mesh2_for_fb7(bundle, trunk_assets):
    return SceneMesh(bundle, trunk_assets["declaration"], TRUNK_VERTS_CACHE,
                     trunk_assets["groups"])


def ground_marker_for(lc, bundle, surface, sc, mesh=None):
    """A ground marker at (x, z): oracle height from the query surface, the
    incident-face normal set from the TRUE (unperturbed) render mesh."""
    x, z = sc
    h = surface.height_at(x, z)
    point = (x, h, z)
    n_set = incident_ground_normals(mesh, x, z) if mesh is not None else None
    return {"point": point, "surface": GROUND_SURFACE_ID, "kind": "ground",
            "oracle_h": h, "oracle_n_set": n_set, "id": "marker_ground_S1"}


# --- build ----------------------------------------------------------------------------
def build():
    global TRUNK_VERTS_CACHE, BASE_APPROACH
    pins = load_pins()
    tb, tq, lc = load_modules(pins)
    bundle_raw = (CONTRIB / PINS["terrain_bundle_json"]["rel"]).read_bytes()
    bundle = tb.loads(bundle_raw)
    tb.validate_bundle(bundle)
    surface = tq.TerrainSurface(bundle, validate=False)
    trunk_raw = (CONTRIB / PINS["trunk_declaration_json"]["rel"]).read_bytes()
    trunk = json.loads(trunk_raw)
    contact_law = json.loads(
        (CONTRIB / PINS["contact_law_json"]["rel"]).read_bytes())
    groups, ttris = trunk_partition(trunk)
    tverts = [to_contact(v[0:3]) for v in trunk["render_mesh"]["vertices"]]
    TRUNK_VERTS_CACHE = [tuple(v[0:3])
                         for v in trunk["render_mesh"]["vertices"]]
    base_c = to_contact(trunk["site"]["base_centre_m"])
    trunk_assets = {
        "groups": groups, "vertices": tverts, "tris": ttris,
        "base": base_c, "radius": trunk["geometry"]["radius_m"],
        "height": trunk["geometry"]["height_m"],
        "base_clearing": tuple(trunk["site"]["base_centre_m"]),
        "declaration": trunk,
    }
    BASE_APPROACH = base_c

    # ---- falsifiers first (fail-first) ----
    bites = run_bites(lc, bundle, surface, trunk_assets)

    # ---- P0 combined instantiation ----
    p0 = combined_refusal_probe(lc, {"bundle": bundle}, trunk_assets)
    require(p0["outcome"] == "refused"
            and "nonfinite_state" in p0["code"], "f04_p0_not_refused", p0)

    # ---- frozen scenarios (CCD on) ----
    scenarios = {
        "G_HIGH": scenario_g_high(lc, {"bundle": bundle}, surface),
        "T_CROSS": scenario_t_cross(lc, trunk_assets),
        "SEAM_HIGH": scenario_seam_high(lc, trunk_assets, surface),
        "G_SEAM_REST": scenario_g_seam_rest(lc, {"bundle": bundle}, surface),
        "TRUNK_TOP_REST": scenario_trunk_top_rest(lc, trunk_assets),
    }
    for name, sc in scenarios.items():
        for i, st in enumerate(sc["states"]):
            st["_scenario_states"] = sc["states"]
            st["_index"] = i

    # ---- predictions ----
    p1 = identity_checks(bundle_raw, bundle, trunk_raw, trunk, groups,
                         tverts, ground_contact_body(bundle, lc), lc)
    p2 = shared_path_checks(lc, contact_law, scenarios)
    p346 = contact_geometry_checks(scenarios, trunk_assets, surface)
    p45 = rest_checks(scenarios, bundle, trunk_assets, surface)
    require(p1["ok"], "f04_p1_asset_identity", p1)
    require(p2["ok"], "f04_p2_shared_path", p2)
    require(p346["ok"], "f04_p346_contact_geometry", p346)
    require(p45["ok"], "f04_p45_rest_ghost", p45)

    # ---- P7 markers (render/collision agreement, pure ray/geometry) ----
    # the render/classify mesh carries the RAW pinned clearing-frame vertices
    # (the contact-frame copies belong to the M06 bodies only)
    trunk_render_verts = [tuple(v[0:3])
                          for v in trunk["render_mesh"]["vertices"]]
    mesh = SceneMesh(bundle, trunk, trunk_render_verts, groups)
    views = {name: Camera(spec) for name, spec in VIEW_SPECS.items()}
    g_state = next(st for st in scenarios["G_HIGH"]["states"]
                   if st["contacts"])
    g_pt = g_state["contacts"][0]["point_clearing_a"]
    t_state = next(st for st in scenarios["T_CROSS"]["states"]
                   if st["contacts"])
    t_pt = t_state["contacts"][0]["point_clearing_a"]
    s_state = next(st for st in scenarios["SEAM_HIGH"]["states"]
                   if st["contacts"])
    s_pt = s_state["contacts"][0]["point_clearing_a"]
    r_state = scenarios["G_SEAM_REST"]["states"][-1]
    r_pt = list(r_state["probe_centre_clearing_m"])
    cap_pt = list(scenarios["TRUNK_TOP_REST"]["states"][-1]
                  ["probe_centre_clearing_m"])
    cap_y = trunk["geometry"]["height_m"]
    ground_n = incident_ground_normals(mesh, g_pt[0], g_pt[2])
    seam_normal = vnorm((-(s_pt[0] - trunk_assets["base_clearing"][0]), 0.0,
                         -(s_pt[2] - trunk_assets["base_clearing"][2])))
    t_normal = vnorm((-(t_pt[0] - trunk_assets["base_clearing"][0]), 0.0,
                      -(t_pt[2] - trunk_assets["base_clearing"][2])))
    cap_n = (0.0, 1.0, 0.0)
    # classify nudges: 1 mm ALONG the facet (see classify_marker docstring);
    # ground oracles are taken at the nudged footprint so the bar stays exact
    g_cx, g_cz = g_pt[0] + 1e-3, g_pt[2]
    r_bottom = (r_pt[0], r_pt[1] - 0.1, r_pt[2])
    r_cx, r_cz = r_bottom[0] + 1e-3, r_bottom[2]
    cap_pt_c = (cap_pt[0], cap_y, cap_pt[2] + 1e-3)
    top_pt = tuple(trunk_assets["base_clearing"][:1]) + (cap_y,) \
        + tuple(trunk_assets["base_clearing"][1:])
    top_pt_c = (top_pt[0], cap_y, top_pt[2] + 1e-3)
    markers = {
        "marker_ground_impact": {"point": tuple(g_pt),
                                 "classify_point": (g_cx, g_pt[1], g_cz),
                                 "surface": GROUND_SURFACE_ID,
                                 "kind": "ground",
                                 "oracle_h": surface.height_at(g_cx, g_cz),
                                 "oracle_n_set": incident_ground_normals(
                                     mesh, g_cx, g_cz)},
        "marker_trunk_impact": {"point": tuple(t_pt),
                                "classify_point": nudge_trunk_point(
                                    t_pt, trunk_assets["base_clearing"],
                                    trunk_assets["radius"]),
                                "surface": "trunk_01.lateral",
                                "kind": "trunk", "oracle_n": t_normal},
        "marker_seam_impact": {"point": tuple(s_pt),
                               "classify_point": nudge_trunk_point(
                                   s_pt, trunk_assets["base_clearing"],
                                   trunk_assets["radius"]),
                               "surface": "trunk_01.lateral",
                               "kind": "trunk", "oracle_n": seam_normal},
        "marker_seam_rest": {"point": r_bottom,
                             "classify_point": (r_cx, r_bottom[1], r_cz),
                             "surface": GROUND_SURFACE_ID, "kind": "ground",
                             "oracle_h": surface.height_at(r_cx, r_cz),
                             "oracle_n_set": incident_ground_normals(
                                 mesh, r_cx, r_cz)},
        "marker_cap_rest": {"point": (cap_pt[0], cap_y, cap_pt[2]),
                            "classify_point": cap_pt_c,
                            "surface": "trunk_01.top_cap",
                            "kind": "trunk_cap", "oracle_n": cap_n,
                            "cap_y": cap_y},
        "marker_trunk_top": {"point": top_pt,
                             "classify_point": top_pt_c,
                             "surface": "trunk_01.top_cap",
                             "kind": "trunk_cap", "oracle_n": cap_n,
                             "cap_y": cap_y},
    }
    probe_marker = {"point": tuple(t_pt), "surface": "probe",
                    "kind": "identity", "id": "probe_shell_T"}
    per_view = {}
    subject_probes = {}
    for vname in VIEW_ORDER:
        cam = views[vname]
        rows = {}
        for mid, m in markers.items():
            rows[mid] = classify_marker(mesh, cam, m)
        alt = 0.3 if vname == "V2_seam_closeup" else 0.6
        sp = trunk_subject_probe(cam, trunk_assets, alt)
        subject_probes[vname] = sp
        rows["subject_trunk"] = classify_marker(mesh, cam, sp)
        per_view[vname] = rows
    # required-subject rules
    failures = []
    for vname in VIEW_ORDER:
        trunk_vis = [mid for mid, r in per_view[vname].items()
                     if r["outcome"] == "VISIBLE_EXACT"
                     and mid.startswith(("marker_trunk", "subject_trunk"))]
        require(trunk_vis, "f04_subject_off_frame", vname)
        for mid, r in per_view[vname].items():
            if r["outcome"] == "VISIBLE_BUT_MISMATCH":
                failures.append({"marker": mid, "view": vname, "rec": r})
    # the seam marker must be VISIBLE_EXACT in V2 with margin >= 3% per side
    rec = per_view["V2_seam_closeup"]["marker_seam_impact"]
    require(rec["outcome"] == "VISIBLE_EXACT", "f04_seam_marker_not_exact",
            rec)
    margin = min(rec["margin_fraction"][0], rec["margin_fraction"][1])
    require(margin >= MARGIN_FRACTION, "f04_subject_clipped",
            {"margin": margin, "required": MARGIN_FRACTION})
    # opposite-side markers obey the exact silhouette prediction in V3
    cam3 = views["V3_opposite_oblique"]
    for mid in ("marker_ground_impact", "marker_seam_rest",
                "marker_trunk_impact"):
        r3 = per_view["V3_opposite_oblique"][mid]
        if r3["outcome"] == "OFF_FRAME":
            continue                     # the frustum check dominates
        predicted = silhouette_predicts_trunk_occlusion(
            cam3, mesh, list(markers[mid]["point"]))
        if predicted:
            if not (r3["outcome"] == "OCCLUDED"
                    and str(r3.get("occluder", "")).startswith("trunk_01")):
                failures.append({"marker": mid, "view": "V3",
                                 "why": "silhouette predicts trunk occlusion",
                                 "rec": r3})
        else:
            if r3["outcome"] not in ("VISIBLE_EXACT", "OCCLUDED"):
                failures.append({"marker": mid, "view": "V3",
                                 "why": "silhouette mismatch", "rec": r3})
    require(not failures, "f04_marker_mismatch", failures[:3])
    p7 = {"prediction": "P7_no_visual_collision_disagreement",
          "per_view": {v: {m: r["outcome"]
                           for m, r in per_view[v].items()}
                       for v in VIEW_ORDER},
          "seam_marker_margin_fraction": margin,
          "margin_required": MARGIN_FRACTION,
          "silhouette_rule": "V3 opposite-side markers: OCCLUDED by the trunk "
                             "exactly when the analytic cylinder silhouette "
                             "predicts it",
          "ok": True}

    # ---- trace + renders + capture ----
    EVIDENCE.mkdir(exist_ok=True)
    trace = {
        "schema": "chimera.mat2_f04.contact_trace.v1",
        "run_id": RUN_ID,
        "scenarios": {name: {"states": [
            {k: v for k, v in st.items()
             if not k.startswith("_")}
            for st in sc["states"]]}
            for name, sc in scenarios.items()},
    }
    trace_path = EVIDENCE / "contact_trace.json"
    trace_path.write_bytes(canonical(trace))
    trace_sha = sha_bytes(trace_path.read_bytes())

    subject_sha = sha_bytes(
        len(bundle_raw).to_bytes(8, "big") + bundle_raw
        + len(trunk_raw).to_bytes(8, "big") + trunk_raw)

    capture_dir = ATTEMPT_WORKSPACE / CAPTURE_DIR_NAME
    capture_dir.mkdir(exist_ok=True)
    video_path = capture_dir / "mat2_f04_contact_motion.avi"

    # static bases per (view, diagnostic)
    bases = {}
    for vname in VIEW_ORDER:
        cam = views[vname]
        c0, d0, _ = render_static(mesh, cam, diagnostic=False)
        c1, d1, _ = render_static(mesh, cam, diagnostic=True)
        bases[vname] = {"clean": (c0, d0), "diagnostic": (c1, d1)}

    def row_states(plan_row):
        vname, mode, segs = plan_row
        out = []
        for sname, rng in segs:
            sts = scenarios[sname]["states"]
            for i in (rng if rng is not None else range(len(sts))):
                out.append((sname, sts[i]))
        return out

    row_seconds = {}
    offset = 0
    for plan_row in ROW_PLAN:
        n = len(row_states(plan_row))
        row_seconds["%s_%s" % (plan_row[0], plan_row[1])] = [offset,
                                                             offset + n]
        offset += n
    total_frames = offset
    # A6: the tick interval is the measured replay length of the overview row
    global TICK_INTERVAL
    TICK_INTERVAL = [0, len(row_states(ROW_PLAN[0])) - 1]
    for vname in VIEW_ORDER:
        ROW_STATES[vname] = len(row_states(
            next(p for p in ROW_PLAN if p[0] == vname and p[1] == "diagnostic")))

    def all_frames():
        for plan_row in ROW_PLAN:
            vname, mode, _ = plan_row
            cam = views[vname]
            base_colour, base_depth = bases[vname][mode]
            for sname, st in row_states(plan_row):
                yield frame_from_state(mesh, cam, base_colour, base_depth,
                                       st, mode == "diagnostic")

    n_encoded = encode_video(video_path, all_frames(), total_frames)
    video_sha = sha_bytes(video_path.read_bytes())
    probe = probe_video(video_path)
    require(probe["codec_name"] == "ffv1"
            and int(probe["width"]) == W and int(probe["height"]) == H
            and int(probe["nb_read_packets"]) == total_frames,
            "f04_video_probe_mismatch", probe)

    # committed stills: the impact-tick frame of each row
    still_hashes = {}
    row_still_state = {}
    for vname, mode in [(v, m) for v in VIEW_ORDER
                        for m in ("diagnostic", "clean")]:
        sname, tick = STILL_OF[vname]
        sts = scenarios[sname]["states"]
        i = tick if tick is not None else next(
            idx for idx, st in enumerate(sts) if st["contacts"])
        st = sts[i]
        row_still_state["%s_%s" % (vname, mode)] = (sname, st)
        cam = views[vname]
        base_colour, base_depth = bases[vname][mode]
        colour = frame_from_state(mesh, cam, base_colour, base_depth, st,
                                  mode == "diagnostic")
        fname = "frame_%s_%s.bmp" % (vname, mode)
        write_bmp(EVIDENCE / fname, colour)
        still_hashes["%s_%s" % (vname, mode)] = sha_bytes(
            (EVIDENCE / fname).read_bytes())

    # ---- registry profile + manifest + validators ----
    profile, profile_receipt = read_registry_profile()
    sys.path.insert(0, str(CONTRIB.parent))
    import visual_capture as vc

    cam_samples = [TICK_INTERVAL[0], TICK_INTERVAL[1]]
    rows = []
    tag_bindings = [
        {"label_id": "lbl_ground_impact", "subject_id": "marker_ground_impact"},
        {"label_id": "lbl_trunk_impact", "subject_id": "marker_trunk_impact"},
        {"label_id": "lbl_seam_impact", "subject_id": "marker_seam_impact"},
        {"label_id": "lbl_seam_rest", "subject_id": "marker_seam_rest"},
        {"label_id": "lbl_cap_rest", "subject_id": "marker_cap_rest"},
    ]
    observed_map = {}
    for vname in VIEW_ORDER:
        obs = set()
        for mid, r in per_view[vname].items():
            if r["outcome"] in ("VISIBLE_EXACT", "OCCLUDED"):
                if mid.startswith("marker_"):
                    obs.add(mid)
                if r["outcome"] == "VISIBLE_EXACT" and r.get("hit_surface_id"):
                    obs.add(r["hit_surface_id"])
        observed_map[vname] = sorted(obs)
    for plan_row in ROW_PLAN:
        vname, mode, _ = plan_row
        cam = views[vname]
        rec = cam.camera_record(cam_samples)
        base_vis = {
            "selected_ids": [],
            "required_subject_ids": (
                ["trunk_01.lateral", "marker_seam_impact"]
                if vname == "V2_seam_closeup" else ["trunk_01.lateral"]),
            "observed_subject_ids": observed_map[vname],
            "missing_subject_ids": [],
            "occlusion_mode": "depth_tested",
        }
        if mode == "diagnostic":
            vis = dict(base_vis)
            vis["layers"] = list(DIAGNOSTIC_LAYERS)
            vis["label_ids"] = [b["label_id"] for b in tag_bindings]
            vis["tag_bindings"] = tag_bindings
        else:
            vis = {"layers": [], "label_ids": [], "tag_bindings": [],
                   **base_vis}
        key = "%s_%s" % (vname, mode)
        rows.append({
            "view_id": PROFILE_VIEW_NAMES[vname],
            "profile_view_key": vname,
            "mode": mode,
            "pair_id": "pair-" + vname,
            "state_binding": {"kind": "trace", "sha256": trace_sha},
            "artifact_locator": {"kind": "video",
                                 "seconds": list(row_seconds[key])},
            "camera": {
                "frame_id": rec["frame_id"],
                "coordinate_unit": rec["coordinate_unit"],
                "handedness": rec["handedness"],
                "orientation_convention": rec["orientation_convention"],
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
                "samples": rec["camera_motion_or_bookmark_sequence"]["samples"],
                "camera_record_16field_convention": rec,
            },
            "visibility": vis,
        })
    manifest = {
        "schema": "chimera.visual_capture_manifest.v1",
        "task_id": TASK_ID,
        "run_id": RUN_ID,
        "profile_id": profile["id"],
        "subject_sha256": subject_sha,
        "capture_sha256": video_sha,
        "tick_interval": list(TICK_INTERVAL),
        "views": rows,
        "capture_layout": {
            "capture_is": "one deterministic FFV1/AVI video (lossless, 1 fps); "
                          "each row's locator window replays the sha-bound "
                          "solver states of its frozen scenarios; clean rows "
                          "draw the pinned assets + probe shell only; "
                          "diagnostic rows add the three profile layers",
            "single_gate_bound_artifact": str(video_path),
            "subject_binding": "sha256(len8(terrain_bundle_raw) || "
                               "terrain_bundle_raw || len8(trunk_declaration"
                               "_raw) || trunk_declaration_raw)",
            "honest_titles": "the pinned F01 render law draws geometry only; "
                             "frame identity is bound by this manifest, the "
                             "per-row trace sha and the committed stills",
            "tick_to_seconds_map": "1 fps; row seconds = concatenated replay "
                                   "windows over the frozen scenarios",
            "files": [{"path": "evidence/frame_%s_%s.bmp" % (v, m),
                       "role": "%s %s still" % (PROFILE_VIEW_NAMES[v], m),
                       "raw_sha256": still_hashes["%s_%s" % (v, m)]}
                      for v in VIEW_ORDER for m in ("diagnostic", "clean")],
        },
    }
    (EVIDENCE / "capture_manifest.json").write_bytes(canonical(manifest))
    context = {"task_id": TASK_ID, "run_id": RUN_ID,
               "subject_sha256": subject_sha, "capture_sha256": video_sha,
               "tick_interval": list(TICK_INTERVAL)}
    (EVIDENCE / "capture_context.json").write_bytes(canonical(context))
    struct_receipt = vc.validate_manifest(
        json.loads(canonical(manifest)), context, profile)
    import visual_gate as vg

    gate_receipt = {"evidence": {
        "camera": {"reference": str(EVIDENCE / "capture_manifest.json"),
                   "raw_sha256": sha_bytes(
                       (EVIDENCE / "capture_manifest.json").read_bytes())},
        "visual": {"reference": str(video_path), "raw_sha256": video_sha}},
        "capture_context": context}
    gate_contract = {"task_id": TASK_ID,
                     "task": {"verification_profile": profile}}
    gate_outcome = vg.verify(gate_receipt, gate_contract)
    validation = {"registry_profile": profile_receipt,
                  "validate_manifest": struct_receipt,
                  "visual_gate": gate_outcome,
                  "visual_acceptance": ("belongs to the independent visual "
                                        "reviewer; this build claims binding "
                                        "and structural validity only")}
    (EVIDENCE / "validation_receipt.json").write_bytes(canonical(validation))

    # ---- camera manifest (16-field records) ----
    camera_manifest = {v: views[v].camera_record(cam_samples)
                       for v in VIEW_ORDER}
    (EVIDENCE / "camera_manifest.json").write_bytes(
        canonical(camera_manifest))

    # ---- assemble receipt ----
    checks = {
        "schema": SCHEMA,
        "card": "MAT2-F04", "task_id": TASK_ID, "planning_id": "F04",
        "run_id": RUN_ID,
        "base_revision": BASE_REVISION,
        "prereg_commit": PREREG_COMMIT,
        "amendment_commits": AMENDMENT_COMMITS,
        "criteria_sha256": CRITERIA_SHA256,
        "scope_sha256": SCOPE_SHA256,
        "attempt_id": "c4064f0e999c40b3a9b18892b034f83c",
        "arrival_id": "arrival-a6cc16fce0954ee789086633f911e1a3",
        "pin_source_tree": PIN_SOURCE_TREE,
        "pins": pins,
        "p0_combined_instantiation": p0,
        "p1_tied_asset_identity": p1,
        "p2_shared_path": p2,
        "p346_contact_geometry": p346,
        "p45_rest_ghost": p45,
        "p7_visual_collision": p7,
        "falsifier_bites": bites,
        "scenario_summary": {name: {
            "ticks": len(sc["states"]),
            "contact_ticks": sum(1 for st in sc["states"]
                                 if st["contacts"]),
            "contact_records": sum(len(st["contacts"])
                                   for st in sc["states"]),
            "first_contact_tick": next(
                (st["tick"] for st in sc["states"] if st["contacts"]), None),
            "handover_tick": sc.get("handover_tick"),
        } for name, sc in scenarios.items()},
        "seam_composition": {
            "phase_A": "ballistic, no static parts, clearance measured",
            "phase_B": "trunk_01.lateral instantiated (ground-oracle "
                       "clearance recorded per phase-B state as the "
                       "composition disclosure)",
            "metric_law": "phase metrics are extracted per phase via "
                          "phase_metric(states, phase, key) -- never by "
                          "scanning heterogeneous states",
            "phase_state_counts": {
                "A": sum(1 for st in scenarios["SEAM_HIGH"]["states"]
                         if st.get("phase") == "A"),
                "B": sum(1 for st in scenarios["SEAM_HIGH"]["states"]
                         if st.get("phase") == "B")},
            "per_phase_min_clearance_above_query_m": {
                "A": phase_metric(scenarios["SEAM_HIGH"]["states"], "A",
                                  "min_clearance_above_query_m"),
                "B": phase_metric(scenarios["SEAM_HIGH"]["states"], "B",
                                  "min_clearance_above_query_m")},
            "measured_phase_B_min_clearance_above_query_m":
                phase_metric(scenarios["SEAM_HIGH"]["states"], "B",
                             "min_clearance_above_query_m"),
            "measured_phase_B_min_radial_clearance_m":
                phase_metric(scenarios["SEAM_HIGH"]["states"], "B",
                             "min_radial_clearance_m"),
            "unsupported_sink_disclosure":
                "phase B runs without the ground body; the probe's post-"
                "arrest fall inside the frozen tail is a composition "
                "artifact, measured per phase beside this record and "
                "excluded from the interpenetration bar by the declared "
                "instantiation scope",
        },
        "capture": {
            "profile_id": profile["id"], "kind": profile["kind"],
            "task_id": TASK_ID,
            "video_path": str(video_path),
            "video_sha256": video_sha,
            "video_probe": probe,
            "frames": total_frames,
            "row_seconds": {k: list(v) for k, v in row_seconds.items()},
            "stills": still_hashes,
            "trace_sha256": trace_sha,
            "subject_sha256": subject_sha,
            "validation": validation,
        },
        "registry_profile": profile_receipt,
        "determinism": {"note": "P8 verified by build -> snapshot -> rebuild "
                                "comparison over every evidence artifact and "
                                "the video; see evidence/determinism.json "
                                "(written by `python -B implementation.py "
                                "verify`) and the report section"},
    }
    (EVIDENCE / "checks.json").write_bytes(canonical(checks))
    return checks


def verify_determinism():
    """P8: two full builds; every evidence artifact and the video byte-identical.
    The record's own output (determinism.json) is excluded from the compared
    set, so the artifact count is independent of whether a previous verify
    left a determinism.json behind."""
    def snapshot():
        return {p.name: sha_bytes(p.read_bytes())
                for p in sorted(EVIDENCE.iterdir())
                if p.is_file() and p.name != "determinism.json"}

    first = build()
    snap = snapshot()
    snap["__video__"] = first["capture"]["video_sha256"]
    second = build()
    snap2 = snapshot()
    snap2["__video__"] = second["capture"]["video_sha256"]
    identical = snap == snap2
    require(identical, "f04_nondeterministic",
            {k for k in set(snap) | set(snap2) if snap.get(k) != snap2.get(k)})
    record = {"prediction": "P8_determinism",
              "artifacts": len(snap) - 1, "identical": True,
              "hashes": snap,
              "video_sha256": snap["__video__"]}
    (EVIDENCE / "determinism.json").write_bytes(canonical(record))
    return record


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("bites", "build", "verify"):
        print(__doc__)
        sys.exit(2)
    if sys.argv[1] == "bites":
        pins = load_pins()
        tb, tq, lc = load_modules(pins)
        bundle = tb.loads(
            (CONTRIB / PINS["terrain_bundle_json"]["rel"]).read_bytes())
        tb.validate_bundle(bundle)
        surface = tq.TerrainSurface(bundle, validate=False)
        trunk = json.loads(
            (CONTRIB / PINS["trunk_declaration_json"]["rel"]).read_bytes())
        groups, _ = trunk_partition(trunk)
        tverts = [to_contact(v[0:3]) for v in trunk["render_mesh"]["vertices"]]
        TRUNK_VERTS_CACHE = [tuple(v[0:3])
                             for v in trunk["render_mesh"]["vertices"]]
        trunk_assets = {"groups": groups, "vertices": tverts,
                        "base": to_contact(trunk["site"]["base_centre_m"]),
                        "radius": trunk["geometry"]["radius_m"],
                        "height": trunk["geometry"]["height_m"],
                        "base_clearing": tuple(trunk["site"]["base_centre_m"]),
                        "declaration": trunk}
        BASE_APPROACH = trunk_assets["base"]
        bites = run_bites(lc, bundle, surface, trunk_assets)
        print("bites:", len(bites), "all bite:",
              all(b["bites"] for b in bites))
        for b in bites:
            print(" -", b["bite"], "BITES" if b["bites"] else "NO-BITE")
        sys.exit(0)
    if sys.argv[1] == "verify":
        record = verify_determinism()
        print("determinism: artifacts", record["artifacts"], "identical",
              record["identical"])
        sys.exit(0)
    checks = build()
    print("build ok:",
          all([checks["p1_tied_asset_identity"]["ok"],
               checks["p2_shared_path"]["ok"],
               checks["p346_contact_geometry"]["ok"],
               checks["p45_rest_ghost"]["ok"],
               checks["p7_visual_collision"]["ok"]]))
