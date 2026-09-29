"""terrain_contact -- MAT2-F02: the terrain asset bound to the SHARED contact path.

Card done_when (verbatim): "Rendered ground and physical query surfaces agree
within frozen geometric tolerance. Material-first addition: Terrain contact
uses the shared material/contact path; surface shape, material identity and
collision geometry stay tied to the rendered asset."

THE MECHANISM (frozen in PREREGISTRATION.md before any run):

1. ONE tied asset: the pinned F01 ``terrain_bundle.json`` whose
   ``render.vertices``/``render.indices`` are the engine ``load_mesh`` arrays
   and whose triangulation IS the physical query surface (``terrain_query.py``).
   Nothing here re-derives geometry: the contact body is SLICED from the same
   arrays (ground section, 3200 triangles), so the surface the contact path
   sees and the rendered surface are the same numbers by construction -- and
   checked to be so by hash (P1).

2. THE shared path: terrain contact goes through MAT2-M06's
   ``chimera.local_contact.v1`` (``local_contact.py``, vendored byte-identical,
   imported, never forked): candidate search -> exact tri-tri contact ->
   Coulomb friction -> CCD -> reciprocal impulses + ledger. There is no
   second solver; FB2 bites a parallel height-clamp to prove the check
   refuses one.

3. Frame map (declared, right-handed rotation +90 deg about +X, det=+1):
   clearing (x, y up, z) -> contact (x, -z, y); M06 gravity (-Z) maps back to
   clearing gravity (-Y). Inverse: contact (a, b, c) -> clearing (a, c, -b).
   Both bodies use the SAME map; records are mapped back before any
   comparison with the clearing-frame query surface.

4. Materials (synthetic_authored, M06 vocabulary, ``pair_mu`` = elementwise
   min): terrain ``monkey_clearing_ground`` / matter ``clearing_ground_topsoil``
   mu 0.9/0.65 thickness 0.002 (M02 shell pin), pinned; probe shells matter
   ``mass_tetra`` (pinned compiled mass row, 0.12 kg), mu 0.6/0.4 (M06 block
   declarations), thickness 0.002, free.

Frozen geometric tolerance (P3): settled probe bottom mid-surface separation
above the query height in [0.0015, 0.0025] m -- thickness inflations
(0.002 m) plus the M06 equilibrium band (SLOP+MARGIN), rounded up to the
millimetre. Derived, then frozen; never tuned after measurement.

CPU-only, stdlib-only, deterministic (no wall-clock, no RNG). Refusals are
named codes; nothing is silently repaired.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
PINS_DIR = HERE / "pins"
EVIDENCE = HERE / "evidence"
sys.path.insert(0, str(PINS_DIR))

import clearing_recipe as recipe            # noqa: E402 (vendored pin)
import terrain_bundle as tb                 # noqa: E402 (vendored pin)
import terrain_query                        # noqa: E402 (vendored pin)
import local_contact                        # noqa: E402 (vendored M06 pin)

SCHEMA = "chimera.mat2_f02.terrain_contact.v1"

# --- pinned inputs (PREREGISTRATION section 1; raw sha256 asserted) -----------
PINS = {
    "clearing_recipe_py": {
        "published": "contributions/MAT2-F01/evidence/pins_materialized/clearing_recipe.py",
        "sha256": "ab800d2257655118296519b606c77ddc7116f524ae0c2e6a0bab3b38473892dc"},
    "clearing_declaration_json": {
        "published": "contributions/MAT2-F01/evidence/pins_materialized/clearing_declaration.json",
        "sha256": "18dd2ff65410cd1cf184a7a8df61c7503a6ce15083f30159e727e9a8117bfbc1"},
    "terrain_bundle_py": {
        "published": "contributions/MAT2-F01/evidence/pins_materialized/terrain_bundle.py",
        "sha256": "c6ada25a1b6192aa86add8b09bc19161c0cd81e3fb3d4bd267492660c0be8f2e"},
    "terrain_query_py": {
        "published": "contributions/MAT2-F01/evidence/pins_materialized/terrain_query.py",
        "sha256": "b1e244b8843671afc29af530c4725bf812ffd5f8967130f0202792aeb7a8cce1"},
    "terrain_bundle_json": {
        "published": "contributions/MAT2-F01/evidence/pins_materialized/terrain_bundle.json",
        "sha256": "446ed3fbd0f50205c61a7233ceca289bfc3316f76dfc672fec307b20d8305d52"},
    "trunk_declaration_json": {
        "published": "contributions/MAT2-F01/evidence/pins_materialized/trunk_declaration.json",
        "sha256": "94ff906ec5e8b8388e4de318aa3321bad9c791fbb168e8234c371ed1d327e3f1"},
    "f01_implementation_py": {
        "published": "contributions/MAT2-F01/implementation.py",
        "file": "f01_implementation.py",
        "sha256": "50e191cfc6f592fd9919534c8986c049939a4e88c4922e135f383bbf06e693af"},
    "local_contact_py": {
        "published": "contributions/MAT2-M06/local_contact.py",
        "sha256": "1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc"},
    "contact_law_json": {
        "published": "contributions/MAT2-M06/contact_law.json",
        "sha256": "583962c29f18118a478dedb167f2c3667414b86f5cab4ee54763416f1df7e41b"},
}
PIN_SOURCE_TREE = "origin/astra/gait-capture @ 18327e7b6e7b8d4b2243362fb3d14a7a77f9672e"


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


# --- material declarations (PREREGISTRATION section 2; do not tune) -----------
GROUND_SURFACE_ID = "monkey_clearing_ground"     # EXACTLY the render section id
GROUND_MATTER_ID = "clearing_ground_topsoil"
GROUND_MU_S, GROUND_MU_K = 0.9, 0.65
PROBE_MATTER_ID = "mass_tetra"                   # pinned compiled matter row
PROBE_MASS_KG = 0.12                             # pinned mass_tetra value (M06 fixtures)
PROBE_MU_S, PROBE_MU_K = 0.6, 0.4                # M06 block declarations
THICKNESS_M = local_contact.THICKNESS_M          # 0.002, MAT2-M02 shell pin
PROBE_HALF_M = 0.1
DROP_M = 0.05
SETTLE_TICKS = 40
SHEAR_TICKS = 80
SHEAR_VX_M_S = -0.35
TOL_REST_LO_M, TOL_REST_HI_M = 0.0015, 0.0025    # frozen P3 window
PLANE_BAR_M = 1e-9
NORMAL_BAR = 1e-9
SPEED_BAR_M_S = 1e-4
SHEAR_DISPLACEMENT_BAR_M = 0.5

SITES = {
    "S1": {"x": 0.0, "z": 0.0, "ticks": SETTLE_TICKS, "vx": 0.0},
    "S2": {"x": -18.312917, "z": -6.422639, "ticks": SETTLE_TICKS, "vx": 0.0},
    "S3": {"x": -15.035646, "z": -6.422639, "ticks": SETTLE_TICKS, "vx": 0.0},
    "S4": {"x": 11.226783, "z": 2.471766, "ticks": SETTLE_TICKS, "vx": 0.0},
    "S5": {"x": 19.265584, "z": 6.057064, "ticks": SHEAR_TICKS, "vx": SHEAR_VX_M_S},
}


# --- pins ---------------------------------------------------------------------
def load_pins():
    """Verify every pinned byte in pins/ against the frozen raw sha256."""
    out = {}
    for key, pin in PINS.items():
        name = pin.get("file") or pathlib.Path(pin["published"]).name
        path = PINS_DIR / name
        require(path.is_file(), "f02_pin_missing", key)
        got = sha_bytes(path.read_bytes())
        require(got == pin["sha256"], "f02_pin_hash_mismatch",
                {"key": key, "expect": pin["sha256"], "got": got})
        out[key] = {"file": str(path), "sha256": got,
                    "published": pin["published"], "raw_match": True}
    return out


def load_sources():
    """Strict load of the tied asset + the query surface + the contact law."""
    bundle_raw = (PINS_DIR / "terrain_bundle.json").read_bytes()
    bundle = tb.loads(bundle_raw)                     # strict intake, schema check
    bundle_receipt = tb.validate_bundle(bundle)       # full validator (F01's own)
    surface = terrain_query.TerrainSurface(bundle, validate=False)  # validated above
    declaration = recipe.loads((PINS_DIR / "clearing_declaration.json").read_bytes())
    trunk = json.loads((PINS_DIR / "trunk_declaration.json").read_bytes())
    contact_law = json.loads((PINS_DIR / "contact_law.json").read_bytes())
    return bundle, bundle_raw, bundle_receipt, surface, declaration, trunk, contact_law


# --- frame map (declared rotation; det = +1) ------------------------------------
def to_contact(p):
    """clearing (x, y, z) -> contact (x, -z, y)."""
    return (p[0], -p[2], p[1])


def to_clearing(q):
    """contact (a, b, c) -> clearing (a, c, -b). Inverse of to_contact."""
    return (q[0], q[2], -q[1])


# --- the tied contact body (sliced from the render arrays) ----------------------
def ground_contact_body(bundle, matter_id=GROUND_MATTER_ID):
    """Build the pinned terrain Body from the RENDER ground section arrays.

    Vertices: the render positions, frame-mapped, in file order (identity by
    construction; P1 hashes both orders). Triangles: the ground index triples.
    """
    section = bundle["render"]["sections"]["ground"]
    require(section["surface_id"] == GROUND_SURFACE_ID, "f02_render_section_id",
            section["surface_id"])
    vs = bundle["render"]["vertices"]
    idx = bundle["render"]["indices"]
    g0, g1 = section["index_start"], section["index_start"] + section["index_count"]
    v0, v1 = section["vertex_start"], section["vertex_start"] + section["vertex_count"]
    vertices = [to_contact(vs[9 * i:9 * i + 3]) for i in range(v0, v1)]
    triangles = [(idx[k], idx[k + 1], idx[k + 2]) for k in range(g0, g1, 3)]
    for t in triangles:
        require(all(v0 <= i < v1 for i in t), "f02_body_index_outside_ground", t)
    return local_contact.Body(
        "terrain_ground", GROUND_SURFACE_ID, matter_id, 0.0,
        GROUND_MU_S, GROUND_MU_K, THICKNESS_M, vertices, triangles, pinned=True)


def asset_extent_xz(body):
    """Max |x|, |y| over the body's contact-frame vertices; contact x = clearing x
    and contact y = -clearing z, so this is the clearing-frame extent."""
    mx = my = 0.0
    for v in body.vertices:
        mx = max(mx, abs(v[0]))
        my = max(my, abs(v[1]))
    return mx, my


# --- probe shell -----------------------------------------------------------------
def _box_verts_local(half):
    a = half
    return [(-a, -a, -a), (a, -a, -a), (a, a, -a), (-a, a, -a),
            (-a, -a, a), (a, -a, a), (a, a, a), (-a, a, a)]


BOX_TRIANGLES = [(0, 2, 1), (0, 3, 2),          # bottom, outward -z
                 (4, 5, 6), (4, 6, 7),          # top, outward +z
                 (0, 1, 5), (0, 5, 4),          # -y side
                 (2, 3, 7), (2, 7, 6),          # +y side
                 (0, 4, 7), (0, 7, 3),          # -x side
                 (1, 2, 6), (1, 6, 5)]          # +x side


def probe_body(site_key, x, z, h_query, vx=0.0):
    """A 12-triangle box shell dropped with its bottom at h_query + DROP_M.

    Contact-frame centre: (x, -z, h_query + DROP_M + half); bottom face at
    h_query + DROP_M (the frozen drop height above the query surface).
    """
    a = PROBE_HALF_M
    centre = (x, -z, h_query + DROP_M + a)
    verts = [local_contact.vadd(centre, v) for v in _box_verts_local(a)]
    return local_contact.Body(
        "probe_" + site_key, "probe_" + site_key, PROBE_MATTER_ID, PROBE_MASS_KG,
        PROBE_MU_S, PROBE_MU_K, THICKNESS_M, verts, list(BOX_TRIANGLES),
        velocity=(vx, 0.0, 0.0))


def site_band(bundle, x, z, half=PROBE_HALF_M):
    """The asset's own within-cell relief under the probe footprint: max
    |h00 - h01 - h10 + h11| over every grid cell intersecting the square
    [x -/+ half] x [z -/+ half]. This is the diagonal-crease height a corner
    may legitimately rest on while its sampled 2D query point serves the
    neighbouring triangle of the same cell. Frozen asset quantity -- derived,
    never tuned. (PREREGISTRATION Amendment A1.)"""
    grid = bundle["terrain_surface"]["grid"]
    H = grid["heights_m"]
    worst = 0.0
    ix0 = max(0, int(math.floor((x - half - grid["x0_m"]) / grid["dx_m"])))
    ix1 = min(grid["nx"] - 2, int(math.floor((x + half - grid["x0_m"]) / grid["dx_m"])))
    iz0 = max(0, int(math.floor((z - half - grid["z0_m"]) / grid["dz_m"])))
    iz1 = min(grid["nz"] - 2, int(math.floor((z + half - grid["z0_m"]) / grid["dz_m"])))
    for iz in range(iz0, iz1 + 1):
        for ix in range(ix0, ix1 + 1):
            worst = max(worst, abs(H[iz][ix] - H[iz][ix + 1]
                                   - H[iz + 1][ix] + H[iz + 1][ix + 1]))
    return worst


# --- the settle experiment (ALL contact through local_contact.solve_tick) --------
def settle(body, surface, site_key, site, exhaustive=False):
    """Drop the probe at one frozen site; every tick through the shared path.

    body: the terrain contact body (pinned); surface: the TRUE query surface
    (deliberately a separate argument -- FB1 decouples them to prove the bars
    detect a drifted collision surface).

    Returns the observation record: last-tick contact records (mapped back),
    worst agreement numbers over ALL ticks, ledger residuals, resting metrics.
    """
    x, z, ticks, vx = site["x"], site["z"], site["ticks"], site["vx"]
    h_query = surface.height_at(x, z)
    probe = probe_body(site_key, x, z, h_query, vx=vx)
    bodies = [body, probe]
    tick_records = []
    ledgers = []
    for _ in range(ticks):
        records, ledger = local_contact.solve_tick(bodies, exhaustive=exhaustive)
        tick_records.append(records)
        ledgers.append(ledger)
    # ---- resting metrics (contact frame -> clearing frame) ----
    zs = [v[2] for v in probe.vertices]
    bottom = min(zs)
    bottom_idx = [i for i, v in enumerate(probe.vertices) if v[2] <= bottom + 1e-12]
    require(len(bottom_idx) == 4, "f02_probe_not_resting_flat", len(bottom_idx))
    bx = sum(probe.vertices[i][0] for i in bottom_idx) / len(bottom_idx)
    by = sum(probe.vertices[i][1] for i in bottom_idx) / len(bottom_idx)
    h_below = surface.height_at(bx, -by)
    separation = bottom - h_below
    corners = sorted(probe.vertices, key=lambda v: v[2])[:4]
    corner_seps = [v[2] - surface.height_at(v[0], -v[1]) for v in corners]
    all_seps = [v[2] - surface.height_at(v[0], -v[1]) for v in probe.vertices]
    min_corner_sep = min(all_seps)
    speed = local_contact.vlen(probe.velocity)
    # ---- contact-record identity/agreement (mapped back to clearing) ----
    total_records = 0
    worst_plane = 0.0
    worst_normal = 0.0
    last_tick_mapped = []
    for ti, records in enumerate(tick_records):
        for rec in records:
            require(rec["body_a"] == body.id and rec["body_b"] == probe.id,
                    "f02_contact_role_order", (rec["body_a"], rec["body_b"]))
            require(rec["surface_a"] == GROUND_SURFACE_ID, "f02_contact_surface_a",
                    rec["surface_a"])
            mapped = _mapped_record(rec, ti, body, surface)
            total_records += 1
            worst_plane = max(worst_plane, mapped["plane_err_m"])
            worst_normal = max(worst_normal, mapped["normal_err"])
            if ti == len(tick_records) - 1:
                last_tick_mapped.append(mapped)
    max_resid = max(local_contact.vlen(l["residual"][probe.id]) for l in ledgers)
    jt_total = sum(abs(r["jt_Ns"]) for r in last_tick_mapped)  # settled-tick shear
    jn_total = sum(r["jn_Ns"] for r in last_tick_mapped)
    jt_run = 0.0
    for records in tick_records:
        for rec in records:
            jt_run += abs(rec["jt_Ns"])
    displacement = math.dist((x, -z), (bx, by)) if vx else 0.0
    return {
        "site": site_key, "drop_target_xz": [x, z],
        "query_height_at_target_m": h_query,
        "ticks": ticks, "initial_vx_m_s": vx,
        "rest_bottom_centre_clearing_m": [bx, bottom, -by],
        "rest_probe_centre_clearing_m": probe_centre_clearing(probe),
        "separation_mid_above_query_m": separation,
        "min_corner_separation_m": min_corner_sep,
        "corner_separations_m": corner_seps,
        "final_speed_m_s": speed,
        "ground_contact_record_count_total": total_records,
        "ground_contact_record_count_last_tick": len(last_tick_mapped),
        "worst_contact_plane_err_m": worst_plane,
        "worst_contact_normal_err": worst_normal,
        "worst_ledger_residual": max_resid,
        "jt_last_tick_Ns": jt_total, "jn_last_tick_Ns": jn_total,
        "jt_total_run_Ns": jt_run,
        "horizontal_displacement_m": displacement,
        "records_last_tick": last_tick_mapped,
        "probe": probe,
    }


def probe_centre_clearing(probe):
    xs = [v[0] for v in probe.vertices]
    ys = [v[1] for v in probe.vertices]
    zs = [v[2] for v in probe.vertices]
    return to_clearing((sum(xs) / 8.0, sum(ys) / 8.0, sum(zs) / 8.0))


def _mapped_record(rec, tick_index, body, surface):
    """Map one contact record back to the clearing frame and re-derive its
    agreement numbers against the query surface (P4).

    body_a is the terrain: rec['point_a'] lies on the terrain midsurface
    triangle (the render plane); rec['normal'] points from B (probe) toward
    A (terrain), i.e. downward, and is sign-fixed to outward/up here.
    """
    p_g = to_clearing(rec["point_a"])          # on the terrain triangle
    tri = rec["tri_a"]
    pa, pb, pc = (to_clearing(v) for v in body.tri_verts(body.triangles[tri]))
    plane_h, inside = _plane_height(pa, pb, pc, p_g[0], p_g[2])
    require(inside, "f02_contact_point_outside_footprint", (tri, p_g))
    plane_err = abs(p_g[1] - plane_h)
    n_up = to_clearing((-rec["normal"][0], -rec["normal"][1], -rec["normal"][2]))
    # the recorded triangle's OWN face normal (engine formula, same vertices)
    face_n = local_contact.vunit(local_contact.vcross(
        local_contact.vsub(pb, pa), local_contact.vsub(pc, pa)))
    if face_n[1] < 0.0:                        # sign-fix outward/up (declared)
        face_n = local_contact.vscale(face_n, -1.0)
    centroid = ((pa[0] + pb[0] + pc[0]) / 3.0, (pa[1] + pb[1] + pc[1]) / 3.0,
                (pa[2] + pb[2] + pc[2]) / 3.0)
    query_face = surface.normal_at(centroid[0], centroid[2])  # centroid -> THIS triangle
    face_query_err = max(abs(face_n[i] - query_face[i]) for i in range(3))
    query_n = surface.normal_at(p_g[0], p_g[2])
    normal_err = max(abs(n_up[i] - query_n[i]) for i in range(3))
    tilt = math.acos(max(-1.0, min(1.0, local_contact.vdot(n_up, face_n))))
    return {
        "tick": tick_index, "kind": rec["kind"], "toc": rec["toc"],
        "tri_ground": tri, "tri_probe": rec["tri_b"],
        "surface_a": rec["surface_a"], "surface_b": rec["surface_b"],
        "matter_a": rec["matter_a"], "matter_b": rec["matter_b"],
        "contact_point_clearing_m": list(p_g),
        "plane_err_m": plane_err,
        "contact_normal_up_clearing": list(n_up),
        "face_normal_up": list(face_n),
        "face_normal_vs_query_at_centroid_err": face_query_err,
        "query_normal_up": list(query_n),
        "normal_err": normal_err,
        "normal_tilt_from_face_rad": tilt,
        "gap_m": rec["gap_m"], "jn_Ns": rec["jn_Ns"], "jt_Ns": rec["jt_Ns"],
    }


def _plane_height(pa, pb, pc, x, z):
    """Plane height of triangle (pa,pb,pc) at clearing (x, z) + footprint test."""
    det = ((pb[0] - pa[0]) * (pc[2] - pa[2]) - (pc[0] - pa[0]) * (pb[2] - pa[2]))
    require(abs(det) > 1e-12, "f02_degenerate_contact_triangle", det)
    w0 = ((pb[0] - x) * (pc[2] - z) - (pc[0] - x) * (pb[2] - z)) / det
    w1 = ((pc[0] - x) * (pa[2] - z) - (pa[0] - x) * (pc[2] - z)) / det
    w2 = 1.0 - w0 - w1
    inside = min(w0, w1, w2) >= -1e-9
    return w0 * pa[1] + w1 * pb[1] + w2 * pc[1], inside


# --- the frozen experiment set ---------------------------------------------------
def run_sites(bundle, surface):
    obs = {}
    for key in ("S1", "S2", "S3", "S4", "S5"):
        body = ground_contact_body(bundle)     # fresh body per site (no carryover)
        obs[key] = settle(body, surface, key, SITES[key])
    return obs


def tied_asset_checks(bundle, bundle_raw, terrain_body):
    """P1: the contact body IS the rendered ground (same numbers, by hash)."""
    section = bundle["render"]["sections"]["ground"]
    vs = bundle["render"]["vertices"]
    v0, v1 = section["vertex_start"], section["vertex_start"] + section["vertex_count"]
    render_mapped = [to_contact(vs[9 * i:9 * i + 3]) for i in range(v0, v1)]
    exact = render_mapped == terrain_body.vertices
    worst = 0.0
    if not exact:
        for a, b in zip(render_mapped, terrain_body.vertices):
            worst = max(worst, max(abs(a[i] - b[i]) for i in range(3)))
    extent_x, extent_z = asset_extent_xz(terrain_body)
    half = bundle["collision"]["boundary"]["half_width_m"]
    return {
        "prediction": "P1_tied_asset_identity",
        "render_vertex_count": len(render_mapped),
        "contact_vertex_count": len(terrain_body.vertices),
        "arrays_exact_equal": exact,
        "worst_component_diff": worst,
        "render_mapped_sha256": sha_bytes(canonical([list(v) for v in render_mapped])),
        "contact_mapped_sha256": sha_bytes(canonical([list(v) for v in terrain_body.vertices])),
        "asset_bundle_raw_sha256": sha_bytes(bundle_raw),
        "asset_bundle_sha256": bundle["bundle_sha256"],
        "surface_id": terrain_body.surface_id,
        "render_section_surface_id": section["surface_id"],
        "surface_id_match": terrain_body.surface_id == section["surface_id"],
        "matter_id": terrain_body.matter_id,
        "contact_extent_xz_m": [extent_x, extent_z],
        "rendered_half_width_m": half,
        "extent_matches_render": abs(extent_x - half) <= 1e-9 and abs(extent_z - half) <= 1e-9,
        "ok": (exact and terrain_body.surface_id == section["surface_id"]
               and abs(extent_x - half) <= 1e-9 and abs(extent_z - half) <= 1e-9),
    }


def shared_path_checks(obs, contact_law):
    """P2: every support impulse flowed through local_contact.v1; doc validates."""
    surfaces = [{
        "id": GROUND_SURFACE_ID, "matter_id": GROUND_MATTER_ID, "mass_kg": None,
        "pinned": True, "mu_s": GROUND_MU_S, "mu_k": GROUND_MU_K,
        "thickness_m": THICKNESS_M, "triangle_count": 3200,
        "provenance": "MAT2-F02 tied terrain asset: sliced from the pinned F01 "
                      "render ground section (same arrays as Engine::load_mesh)",
    }]
    known = {GROUND_SURFACE_ID}
    for key in sorted(obs):
        surfaces.append({
            "id": "probe_" + key, "matter_id": PROBE_MATTER_ID,
            "mass_kg": PROBE_MASS_KG, "pinned": False,
            "mu_s": PROBE_MU_S, "mu_k": PROBE_MU_K,
            "thickness_m": THICKNESS_M, "triangle_count": 12,
            "provenance": "MAT2-F02 probe shell; mass = pinned mass_tetra row, "
                          "friction = M06 block declarations"})
        known.add("probe_" + key)
    contacts = []
    for key in sorted(obs):
        for rec in obs[key]["records_last_tick"]:
            contacts.append({
                "surface_a": rec["surface_a"], "surface_b": rec["surface_b"],
                "matter_a": rec["matter_a"], "matter_b": rec["matter_b"],
                "gap_m": rec["gap_m"]})
    doc = {"schema": local_contact.SCHEMA, "revision": 1,
           "object_id": "mat2-f02-terrain-contact",
           "declarations": dict(contact_law["declarations"]),
           "surfaces": surfaces, "contacts": contacts}
    local_contact.validate_local_contact(doc, known)
    max_resid = max(o["worst_ledger_residual"] for o in obs.values())
    total = sum(o["ground_contact_record_count_total"] for o in obs.values())
    return {
        "prediction": "P2_contact_through_shared_path",
        "module": "local_contact (vendored M06 byte-identical, sha256 "
                  + PINS["local_contact_py"]["sha256"] + ")",
        "record_count_total_all_sites": total,
        "record_count_last_tick_validated": len(contacts),
        "validator": "local_contact.validate_local_contact -> passed",
        "declarations_match_law": all(
            contact_law["declarations"].get(k) == v
            for k, v in local_contact.DECL_KEYS),
        "worst_ledger_residual": max_resid,
        "ok": max_resid <= 1e-12,
    }


def exhaustive_reference_check(bundle, surface):
    """P2 (subset property): at S1 the sweep_and_prune resting state equals the
    exhaustive reference EXACTLY (same activated pairs -> same arithmetic)."""
    body_a = ground_contact_body(bundle)
    o_sweep = settle(body_a, surface, "S1", SITES["S1"])
    body_b = ground_contact_body(bundle)
    o_ex = settle(body_b, surface, "S1", SITES["S1"], exhaustive=True)
    va = sorted(o_sweep["probe"].vertices)
    vb = sorted(o_ex["probe"].vertices)
    return {"prediction": "P2b_exhaustive_reference_identical",
            "vertices_bit_identical": va == vb,
            "separation_sweep_m": o_sweep["separation_mid_above_query_m"],
            "separation_exhaustive_m": o_ex["separation_mid_above_query_m"],
            "ok": va == vb}


def resting_checks(obs, bundle):
    """P3 (Amendment A1 operationalization): the settled probe's lowest point
    above its local query height, in [0.0015, 0.0025 + site_band]. The band is
    the asset's own within-cell diagonal relief under the probe footprint
    (site_band, a frozen quantity of the pinned bytes). Centre separation and
    all corner separations recorded as diagnostics."""
    rows = {}
    ok = True
    for key in sorted(obs):
        o = obs[key]
        band = site_band(bundle, o["drop_target_xz"][0], o["drop_target_xz"][1])
        hi = TOL_REST_HI_M + band
        sep = o["min_corner_separation_m"]
        in_window = TOL_REST_LO_M <= sep <= hi
        stopped = o["final_speed_m_s"] <= SPEED_BAR_M_S
        rows[key] = {
            "min_corner_separation_m": sep,
            "window_m": [TOL_REST_LO_M, hi], "site_diagonal_band_m": band,
            "in_window": in_window,
            "centre_separation_diagnostic_m": o["separation_mid_above_query_m"],
            "corner_separations_m": o["corner_separations_m"],
            "final_speed_m_s": o["final_speed_m_s"], "stopped": stopped,
        }
        ok = ok and in_window and stopped
    return {"prediction": "P3_resting_agreement", "sites": rows, "ok": ok,
            "tolerance_derivation": "contact band: thickness/2 + thickness/2 (0.002) "
                                    "+ SLOP+MARGIN (2e-5), rounded up -> 0.0025; plus "
                                    "the site's own within-cell diagonal relief "
                                    "(site_band) for edge/crease resting"}


def point_normal_checks(obs, bundle):
    """P4 (Amendment A1 operationalization): exact identities stay at 1e-9;
    the raw closest-feature normal gets the asset's own declared tilt bound."""
    worst_plane = 0.0
    worst_face_query = 0.0
    worst_tilt = 0.0
    count = 0
    for key in sorted(obs):
        worst_plane = max(worst_plane, obs[key]["worst_contact_plane_err_m"])
        count += obs[key]["ground_contact_record_count_total"]
        for rec in obs[key]["records_last_tick"]:
            worst_face_query = max(worst_face_query,
                                   rec["face_normal_vs_query_at_centroid_err"])
            worst_tilt = max(worst_tilt, rec["normal_tilt_from_face_rad"])
    slope_bound = bundle["terrain_surface"]["max_slope_bound_m_per_m"]
    return {"prediction": "P4_point_and_normal_agreement",
            "records_checked": count,
            "worst_plane_err_m": worst_plane, "plane_bar_m": PLANE_BAR_M,
            "worst_face_normal_vs_query_at_centroid_err": worst_face_query,
            "face_query_bar": NORMAL_BAR,
            "worst_contact_normal_tilt_from_face_rad": worst_tilt,
            "tilt_declared_bound_rad_from_asset_slope_law": slope_bound,
            "ok": (worst_plane <= PLANE_BAR_M
                   and worst_face_query <= NORMAL_BAR
                   and worst_tilt <= slope_bound)}


def shear_checks(obs, bundle):
    """P6: the tangential impact is absorbed through friction; finite motion."""
    o = obs["S5"]
    displaced = o["horizontal_displacement_m"]
    band = site_band(bundle, o["drop_target_xz"][0], o["drop_target_xz"][1])
    sep = o["min_corner_separation_m"]
    window = [TOL_REST_LO_M, TOL_REST_HI_M + band]
    return {"prediction": "P6_shear_is_finite",
            "site": "S5", "initial_vx_m_s": o["initial_vx_m_s"],
            "jt_total_run_Ns": o["jt_total_run_Ns"],
            "jt_last_tick_Ns": o["jt_last_tick_Ns"],
            "jn_last_tick_Ns": o["jn_last_tick_Ns"],
            "horizontal_displacement_m": displaced,
            "displacement_bar_m": SHEAR_DISPLACEMENT_BAR_M,
            "final_speed_m_s": o["final_speed_m_s"], "speed_bar_m_s": SPEED_BAR_M_S,
            "min_corner_separation_m": sep, "window_m": window,
            "ok": (0.0 <= displaced < SHEAR_DISPLACEMENT_BAR_M
                   and o["final_speed_m_s"] <= SPEED_BAR_M_S
                   and window[0] <= sep <= window[1])}


# --- falsifier bites (run FIRST; every one must bite) -----------------------------
def bite_ghost_support_decoupled_asset(bundle, surface):
    """FB1: +0.01 m on ONE contact-body vertex under S1 (render and query
    surface untouched); the probe settles high, outside the P3 window."""
    body = ground_contact_body(bundle)
    target = to_contact((SITES["S1"]["x"], 0.0, SITES["S1"]["z"]))
    best_i, best_d = None, None
    for i, v in enumerate(body.vertices):
        d = (v[0] - target[0]) ** 2 + (v[1] - target[1]) ** 2
        if best_d is None or d < best_d:
            best_i, best_d = i, d
    body.vertices[best_i] = local_contact.vadd(body.vertices[best_i], (0.0, 0.0, 0.01))
    o = settle(body, surface, "S1", SITES["S1"])
    sep = o["min_corner_separation_m"]
    band = site_band(bundle, SITES["S1"]["x"], SITES["S1"]["z"])
    window = [TOL_REST_LO_M, TOL_REST_HI_M + band]
    return {"bite": "FB1_ghost_support_decoupled_asset",
            "vertex": best_i, "raised_m": 0.01,
            "min_corner_separation_m": sep,
            "window_m": window, "site_diagonal_band_m": band,
            "bites": not (window[0] <= sep <= window[1])}


def bite_parallel_solver_unaccepted(surface):
    """FB2: the forbidden second solver (direct height clamp, no shared path)
    'supports' the probe with ZERO local_contact records -> the P2 rule fires."""
    x, z = SITES["S1"]["x"], SITES["S1"]["z"]
    h = surface.height_at(x, z)
    probe = probe_body("S1", x, z, h - DROP_M)   # clamp: bottom exactly ON the query height
    bottoms = [v[2] for v in probe.vertices]
    clamped_bottom = min(bottoms)
    support_records = []                          # a clamp solver produces none
    fired = (len(support_records) == 0
             and clamped_bottom == h
             and local_contact.vlen(probe.velocity) == 0.0)
    return {"bite": "FB2_parallel_solver_unaccepted",
            "clamped_bottom_m": clamped_bottom,
            "query_height_m": h,
            "support_record_count": len(support_records),
            "rule": "every support impulse must appear as a local_contact.v1 record",
            "bites": fired}


def bite_material_identity_detached(bundle):
    """FB3: terrain matter renamed to a foreign id -> the material identity
    check against the declared asset material fires."""
    body = ground_contact_body(bundle, matter_id="mass_plate")
    fired = body.matter_id != GROUND_MATTER_ID
    refused = False
    try:
        require(body.matter_id == GROUND_MATTER_ID, "f02_matter_identity",
                (body.matter_id, GROUND_MATTER_ID))
    except Refusal as exc:
        refused = exc.code == "f02_matter_identity"
    return {"bite": "FB3_material_identity_detached",
            "matter_id": body.matter_id, "declared": GROUND_MATTER_ID,
            "check_refused": refused, "bites": fired and refused}


def bite_ghost_support_past_boundary(bundle):
    """FB4: one triangle appended 1 m past the rendered +x extent -> the
    contact-extent == rendered-extent rule fires (no invisible wall)."""
    body = ground_contact_body(bundle)
    half = 20.0
    body.vertices.extend([(half + 1.0, 0.0, 0.0),
                          (half + 1.0, 0.0, 1.0),
                          (half + 1.0, 0.5, 0.5)])
    n = len(body.vertices)
    body.triangles.append((n - 3, n - 2, n - 1))
    ex, ez = asset_extent_xz(body)
    return {"bite": "FB4_ghost_support_past_boundary",
            "contact_extent_xz_m": [ex, ez], "rendered_half_width_m": half,
            "bites": ex > half + 1e-9}


def bite_off_frame_probe_subject(f01):
    """FB5: a required subject 155.7 deg off the seam camera classifies
    OFF_FRAME (tags alone do not establish contact). F01's B4 form."""
    spec = f01.VIEWS["V2_seam_closeup"]
    fwd = f01.vnorm(f01.vsub(spec["target"], spec["position"]))
    point = [-20.0, 0.9, -20.0]                    # SW corner post top
    d = f01.vsub(point, spec["position"])
    dn = f01.vlen(d)
    dot = sum(d[i] * fwd[i] for i in range(3)) / dn
    off_axis_deg = math.degrees(math.acos(max(-1.0, min(1.0, dot))))
    behind = dot <= 0.0
    return {"bite": "FB5_off_frame_probe_subject",
            "subject": "post_top_SW", "camera": "V2_seam_closeup",
            "off_axis_deg": off_axis_deg, "behind_camera": behind,
            "bites": behind or off_axis_deg > 90.0}
