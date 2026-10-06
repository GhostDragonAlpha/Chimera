"""implementation.py -- ONT-F01 source-bound qualification package.

Card ONT-F01 ("Author the finite clearing and its spatial units"), planning id
F01. RECONCILE-FIRST: the deterministic recipe, declaration, render/collision
bundle, trunk asset and play receipts already exist pinned in git; this module
NEVER re-derives them. It (1) materializes the pinned bytes from git objects
and re-hashes them under the R5 three-convention policy, (2) re-runs the
numeric proofs in this attempt, (3) evidences the C01 frame chain, and (4)
produces the `forest` visible_static profile's visual evidence set with a
stdlib-only software rasterizer fed by the pinned render vertices VERBATIM,
plus numerical render/collision correspondence at frozen probes.

PREREGISTRATION.md (same directory, Amendment A1 included) is frozen before
this implementation; predictions P1-P8, falsifier bites B1-B4, the 44 probes
and the 4 views below are that file's, not invented here.

Honest boundary: static-scene evidence only. No engine run, no HTTP
load_mesh exercise, no native query route, no walk replay, no training.

Run:  python -B implementation.py build    # bites first (failing-first), then pinned pass
      python -B implementation.py bites    # falsifier bites only
Stdlib only. Evidence lands in evidence/ next to this file.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import pathlib
import struct
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"

SCHEMA = "chimera.ont_f01.qualification.v1"

# --- pinned sources (PREREGISTRATION reconcile table; do not tune) ------------
GAME_REPO_CANDIDATES = [
    pathlib.Path("E:/PythonChimera"),
]

PINS = {
    "clearing_recipe_py": {
        "commit": "dc7ea81111d98f32a4d88252c59f2fb8cf3c7399",
        "path": "tools/monkey_campaign/data/monkey_clearing/clearing_recipe.py",
        "sha256": "ab800d2257655118296519b606c77ddc7116f524ae0c2e6a0bab3b38473892dc",
    },
    "clearing_declaration_json": {
        "commit": "dc7ea81111d98f32a4d88252c59f2fb8cf3c7399",
        "path": "tools/monkey_campaign/data/monkey_clearing/clearing_declaration.json",
        "sha256": "18dd2ff65410cd1cf184a7a8df61c7503a6ce15083f30159e727e9a8117bfbc1",
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
    "trunk_declaration_json": {
        "commit": "dc7ea81111d98f32a4d88252c59f2fb8cf3c7399",
        "path": "tools/monkey_campaign/data/monkey_trunk/trunk_declaration.json",
        "sha256": "94ff906ec5e8b8388e4de318aa3321bad9c791fbb168e8234c371ed1d327e3f1",
    },
    "f01_play_report_md": {
        "commit": "f30f2224",
        "path": "tools/monkey_campaign/agents/F01_clearing/report.md",
        "sha256": "9d29bdb8494b4729d8c3a84a2eb9e6f0e282c2eccc94dee278e1e4748e7d8839",
    },
    "gait_controller_hpp": {
        "commit": "33e7a444fe7b4c35aa99afe7ef898046877025b4",
        "path": "ChimeraEngine/engine/gait_controller.hpp",
        "sha256": "f0ffea12795bd47f7c48f5ed9b8aa98869725467d94a1081b1d942f6fba129bd",
    },
    "native_collision_brief_json": {
        "commit": "86d0d8d461ea50420c053681f7e297343e3fbb97",
        "path": "tools/monkey_campaign/contributions/D-FOREST-RUNTIME-20260924/native_collision_brief.json",
        "sha256": "bc0c723592aff3e3116952b8e647a0c80ada8b011d1d659af8b61b90fccc709d",
        "blob": "c34ee9b48e599c99c1561cf3c4abc0b105ce9f3f",
    },
    "completion_contract_json": {
        "commit": "dce368d75000d19a5041604dfe3fed904233db2f",
        "path": "tools/monkey_campaign/contributions/ONT-P01/completion_contract.json",
        "sha256": "80b2e2f2736ce6fd594633f85fa22bda702991c3ed4d415a0d9c4eadd377163b",
    },
    "followup_proposed_patch": {
        "commit": "960a2f551703a3e84c04e88b5d688dc7166ec35b",
        "path": "tools/monkey_campaign/contributions/D-FOREST-RUNTIME-20260924-FOLLOWUP/proposed.patch",
        "sha256": "b02fc9e65da5459120249d8fd2ec3068818dcd0c43385ffe4331815ac431acb8",
    },
}

MERGED_FOLLOWUP = {
    "card": "D-FOREST-RUNTIME-20260924-FOLLOWUP",
    "head": "960a2f551703a3e84c04e88b5d688dc7166ec35b",
    "merge_commit": "a16080f9f39ff5d3ac941f3fe490e2c1e03e0823",
    "merged_at": "2026-09-27T00:23:16Z",
    "embedded_terrain_surface_hpp_sha256":
        "24f47dbbba31d880e9cba983376b428877ef4cebf7f4f852c4f9e8e238eb87e2",
}


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


def normalized_hashes(raw):
    """R5 three-convention policy: raw / lf_normalized / crlf_normalized."""
    text = raw.decode("utf-8")
    return {
        "raw": sha_bytes(raw),
        "lf_normalized": sha_bytes(text.replace("\r\n", "\n").encode("utf-8")),
        "crlf_normalized": sha_bytes(
            text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")),
    }


# --- pin materialization (git objects only; never a drifted worktree) ---------
def _git_show(repo, commit, path):
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "show", "%s:%s" % (commit, path)],
            capture_output=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode == 0:
        return proc.stdout
    return None


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
    """Return {key: {bytes, file, via_repo, ...}}. Tries the attempt checkout's
    own repo first (it can carry fetched review-lineage objects), then the
    known game repos. Raw sha256 equality is demanded for every pin (the
    normalized conventions are recorded, never substituted, per the R5
    policy). Bytes are written verbatim to evidence/pins_materialized/ so the
    pinned modules import with a real __file__ and reviewers can re-hash the
    exact inputs."""
    repos = []
    root = _attempt_repo_root()
    if root is not None:
        repos.append(root)
    repos.extend(r for r in GAME_REPO_CANDIDATES
                 if r.is_dir() and r not in repos)
    require(repos, "f01_no_git_repo", list(map(str, GAME_REPO_CANDIDATES)))
    pins_dir = EVIDENCE / "pins_materialized"
    pins_dir.mkdir(parents=True, exist_ok=True)
    out = {}
    for key, pin in PINS.items():
        raw = None
        via = None
        for repo in repos:
            raw = _git_show(repo, pin["commit"], pin["path"])
            if raw is not None:
                via = str(repo)
                break
        require(raw is not None, "f01_pin_unavailable",
                {"key": key, "commit": pin["commit"], "path": pin["path"],
                 "hint": "git fetch origin " + pin["commit"]})
        got = sha_bytes(raw)
        require(got == pin["sha256"], "f01_pin_hash_mismatch",
                {"key": key, "expect": pin["sha256"], "got": got})
        target = pins_dir / pathlib.Path(pin["path"]).name
        target.write_bytes(raw)
        if sha_bytes(target.read_bytes()) != got:
            raise Refusal("f01_pin_writeback_mismatch", key)
        out[key] = {"bytes": raw, "file": str(target), "via_repo": via,
                    "sha256": got, "raw_match": True,
                    "commit": pin["commit"], "path": pin["path"]}
    return out


# --- pinned module loading ----------------------------------------------------
def _module_from_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_sources(pins):
    """Load pinned recipe + oracle + bundle + trunk; returns
    (recipe, declaration, surface, trunk, tb_module)."""
    recipe = _module_from_file(
        "f01_pinned_clearing_recipe", pins["clearing_recipe_py"]["file"])
    declaration = recipe.loads(pins["clearing_declaration_json"]["bytes"])
    tb = _module_from_file(
        "f01_pinned_terrain_bundle", pins["terrain_bundle_py"]["file"])
    tq = _module_from_file(
        "f01_pinned_terrain_query", pins["terrain_query_py"]["file"])
    tq.terrain_bundle = tb
    bundle = tb.loads(pins["terrain_bundle_json"]["bytes"])
    surface = tq.TerrainSurface(bundle, validate=True)
    trunk = json.loads(pins["trunk_declaration_json"]["bytes"])
    return recipe, declaration, surface, trunk, tb


# --- geometry helpers ---------------------------------------------------------
def vsub(a, b):
    return [a[i] - b[i] for i in range(3)]


def vdot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vcross(a, b):
    return [a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def vlen(a):
    return math.sqrt(vdot(a, a))


def vnorm(a):
    l = vlen(a)
    require(l > 0.0, "f01_zero_vector", a)
    return [a[i] / l for i in range(3)]


def ray_triangle(orig, direc, v0, v1, v2, eps=1e-9):
    """Moller-Trumbore; returns (t, u, v) or None. Boundary hits count (eps)."""
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


class SceneMesh:
    """The render arrays (pinned bytes, verbatim) as a raycast/raster target."""

    def __init__(self, surface, trunk):
        bundle = surface.bundle
        self.vertices = bundle["render"]["vertices"]          # flat 9-float
        self.indices = bundle["render"]["indices"]
        self.ground = bundle["render"]["sections"]["ground"]
        self.posts_sec = bundle["render"]["sections"]["boundary_posts"]
        self.trunk = trunk
        tv = trunk["render_mesh"]
        self.trunk_vertices = [v[:3] for v in tv["vertices"]]
        self.trunk_indices = tv["indices"]

    def triangles(self):
        """Yield (v0, v1, v2, surface_id) over ground + posts + trunk."""
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
        ti = self.trunk_indices
        for k in range(0, len(ti), 3):
            yield (self.trunk_vertices[ti[k]], self.trunk_vertices[ti[k + 1]],
                   self.trunk_vertices[ti[k + 2]], "trunk_01")

    def first_hit(self, orig, direc, offset_fallback=False):
        """Nearest hit (t, point, normal, surface_id[, offset_used]).
        offset_fallback: retry with deterministic lateral offsets (label-anchor
        cap-centre degeneracy only; recorded when used)."""
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
                d = list(direc)
                sub = self.first_hit(off, d, offset_fallback=False)
                if sub is not None:
                    return (sub[0], sub[1], sub[2], sub[3], dx)
        return best


# --- C01 frame chain (calculation contract: x_world = R x_local + t) ----------
def c01_frame_checks(surface, trunk, declaration):
    """Round-trip, handedness and landmark checks, independently computed."""
    checks = {}
    axis = trunk["site"]["axis_dir"]
    require(axis == [0.0, 1.0, 0.0], "f01_c01_trunk_axis", axis)
    base = trunk["site"]["base_centre_m"]
    R = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]  # identity (world-frame mesh)
    det = (R[0][0] * (R[1][1] * R[2][2] - R[1][2] * R[2][1])
           - R[0][1] * (R[1][0] * R[2][2] - R[1][2] * R[2][0])
           + R[0][2] * (R[1][0] * R[2][1] - R[1][1] * R[2][0]))
    checks["R_determinant_plus_one_right_handed"] = {"det": det, "ok": det == 1.0}
    xh = vcross([1.0, 0.0, 0.0], [0.0, 1.0, 0.0])
    checks["handedness_cross_x_y_equals_z"] = {"cross": xh,
                                               "ok": xh == [0.0, 0.0, 1.0]}
    # round-trip world -> local -> world over every trunk mesh vertex,
    # composing x_world = R x_local + t explicitly (t inverts the declared base)
    t = [-base[0], -base[1], -base[2]]
    tv = trunk["render_mesh"]["vertices"]
    worst_rt = 0.0
    for v in tv:
        local = [sum(R[i][k] * (v[k] + t[k]) for k in range(3)) for i in range(3)]
        world = [sum(R[i][k] * local[k] for k in range(3)) - t[i] for i in range(3)]
        worst_rt = max(worst_rt, max(abs(world[k] - v[k]) for k in range(3)))
    checks["trunk_mesh_roundtrip_worst_err_m"] = {
        "worst": worst_rt, "bar": 1e-12, "ok": worst_rt <= 1e-12}
    # landmark: lateral ring vertices obey the declared radius law
    radii = trunk["collision_representation"]["solid"]["radius_m"]
    height = trunk["geometry"]["height_m"]
    lat = [v for v in tv
           if abs(math.hypot(v[0] - base[0], v[2] - base[2]) - radii) < 1e-6]
    checks["lateral_ring_vertex_count_nonzero"] = {
        "count": len(lat), "ok": len(lat) > 0}
    worst_rad = 0.0
    for v in lat:
        worst_rad = max(worst_rad,
                        abs(math.hypot(v[0] - base[0], v[2] - base[2]) - radii))
    checks["lateral_radius_law_worst_dev_m"] = {
        "worst": worst_rad, "bar": 1e-6, "ok": worst_rad <= 1e-6}
    # landmark: the mesh's y SPAN matches the declared base and height
    ymin = min(v[1] for v in tv)
    ymax = max(v[1] for v in tv)
    y_err = max(abs(ymin - base[1]), abs(ymax - (base[1] + height)))
    checks["mesh_y_span_matches_declared_base_and_height"] = {
        "worst_m": y_err, "bar": 1e-6, "ok": y_err <= 1e-6,
        "mesh_y_min": ymin, "mesh_y_max": ymax,
        "base_centre": base, "height_m": height}
    # landmark: trunk asset site == F01 declaration trunk site (exact)
    site_f01 = declaration["trunk_sites"][0]["site_m"]
    checks["trunk_site_matches_f01_declaration"] = {
        "trunk": base, "f01": site_f01, "ok": base == site_f01}
    # landmark: all 80 post bases stand on the collision surface
    posts = surface.posts()
    worst_post = 0.0
    for p in posts:
        h = surface.height_at(p["position_m"][0], p["position_m"][2])
        worst_post = max(worst_post, abs(h - p["position_m"][1]))
    checks["post_bases_on_collision_surface_worst_m"] = {
        "worst": worst_post, "bar": 1e-9, "posts": len(posts),
        "ok": worst_post <= 1e-9}
    checks["all_ok"] = all(v["ok"] for v in checks.values()
                           if isinstance(v, dict) and "ok" in v)
    return checks


# --- cameras (frozen in PREREGISTRATION) --------------------------------------
W, H = 1280, 720
NEAR, FAR = 0.05, 200.0
VIEWS = {
    "V1_clearing_overview": {
        "position": [0.0, 46.0, -32.0], "target": [0.0, 0.0, 0.0],
        "vfov_deg": 55.0},
    "V2_seam_closeup": {
        "position": [10.15, 1.25, 1.35], "target": [11.976783, 0.32, 2.471766],
        "vfov_deg": 55.0},
    "V3_side_depth": {
        "position": [0.0, 12.0, -50.0], "target": [0.0, 0.0, 6.0],
        "vfov_deg": 45.0},
    "V4_oblique_depth": {
        "position": [-34.0, 20.0, -30.0], "target": [0.0, 0.0, 0.0],
        "vfov_deg": 55.0},
}
VIEW_ORDER = ["V1_clearing_overview", "V2_seam_closeup", "V3_side_depth",
              "V4_oblique_depth"]


class Camera:
    def __init__(self, spec):
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


# --- frozen probes (PREREGISTRATION + A1/A3) -----------------------------------
TRUNK_RING_SEGMENTS = 32          # declared render_mesh.ring_segments (A3)
TRUNK_RADIAL_BAR_M = 5e-6         # 1e-6 grid quantization of mesh vertices
# A5: face-normal tilt bound from the declared vertex quantization:
# 2*sqrt(2)*q / chord, chord = 2*R*sin(pi/32) = 7.24e-3 m  ->  3.91e-4 rad;
# rounded up to 5e-4 rad (derivation in PREREGISTRATION.md A5).
TRUNK_NORMAL_ANGULAR_SLACK = 5e-4
GROUND_NODE_EPS = 1e-9            # 2D footprint containment epsilon


def _incident_ground_normals(surface, x, z):
    """Normals of every ground triangle whose 2D footprint contains (x, z)
    (within eps). At grid nodes the piecewise-linear normal is a SET (A3)."""
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
        if w0 >= -GROUND_NODE_EPS and w1 >= -GROUND_NODE_EPS \
                and w2 >= -GROUND_NODE_EPS:
            out.append(vnorm(vcross(vsub(pb, pa), vsub(pc, pa))))
    require(out, "f01_no_incident_ground_face", (x, z))
    return out


def frozen_probes(surface, trunk):
    """44 world points ON the collision surfaces (oracle/analytic laws)."""
    probes = []
    for x in (-16.0, -8.0, 0.0, 8.0, 16.0):
        for z in (-16.0, -8.0, 0.0, 8.0, 16.0):
            h = surface.height_at(x, z)
            probes.append({"id": "ground_%+d_%+d" % (x, z), "kind": "ground",
                           "point": [x, h, z],
                           "surface": "monkey_clearing_ground",
                           "oracle_h": h,
                           "oracle_n": list(surface.normal_at(x, z)),
                           "oracle_n_set":
                               _incident_ground_normals(surface, x, z)})
    h0 = surface.height_at(0.0, 0.0)
    probes.append({"id": "spawn", "kind": "spawn", "point": [0.0, h0, 0.0],
                   "surface": "monkey_clearing_ground", "oracle_h": h0,
                   "oracle_n": list(surface.normal_at(0.0, 0.0)),
                   "oracle_n_set": _incident_ground_normals(surface, 0.0, 0.0)})
    base = trunk["site"]["base_centre_m"]
    ht = surface.height_at(base[0], base[2])
    for k in range(8):
        a = k * math.pi / 4.0
        px, pz = base[0] + 0.05 * math.cos(a), base[2] + 0.05 * math.sin(a)
        probes.append({"id": "seam_%d" % k, "kind": "seam",
                       "azimuth_k": k, "point": [px, ht, pz],
                       "surface": "monkey_clearing_ground", "oracle_h": ht,
                       "oracle_n": list(surface.normal_at(px, pz)),
                       "oracle_n_set": _incident_ground_normals(surface, px, pz)})
    r = trunk["collision_representation"]["solid"]["radius_m"]
    for az_i, az in ((0, math.pi), (1, 5.0 * math.pi / 4.0)):   # A1: V2-facing
        for y_i, y in enumerate((0.15, 0.6, 1.0)):
            px = base[0] + r * math.cos(az)
            pz = base[2] + r * math.sin(az)
            probes.append({"id": "trunk_az%d_h%d" % (az_i, y_i),
                           "kind": "trunk", "point": [px, base[1] + y, pz],
                           "surface": "trunk_01",
                           "oracle_n": [math.cos(az), 0.0, math.sin(az)]})
    for name, cx, cz in (("SW", -20.0, -20.0), ("SE", 20.0, -20.0),
                         ("NE", 20.0, 20.0), ("NW", -20.0, 20.0)):
        probes.append({"id": "post_top_" + name, "kind": "boundary_post",
                       "point": [cx, 0.9, cz],
                       "surface": "monkey_clearing_boundary_posts",
                       "label_degenerate": True})
    require(len(probes) == 44, "f01_probe_count", len(probes))
    return probes


# --- rasterizer (stdlib; pinned vertices verbatim; presentation only) ---------
LIGHT = vnorm([0.4, 0.8, 0.45])
AMBIENT = 0.55
COLOURS = {
    "ground_A": (0.16, 0.22, 0.17),
    "ground_B": (0.18, 0.24, 0.19),
    "monkey_clearing_boundary_posts": (0.72, 0.55, 0.20),
    "trunk_01": (0.36, 0.25, 0.16),
}


def render_frame(mesh, cam, diagnostic=False, probes=None, labels=None):
    """Z-buffer rasterizer over the pinned render arrays. Returns
    (colour rows, depth rows, stats). Probes NEVER read pixels -- the
    correspondence evidence is pure ray/geometry."""
    colour = [[(8, 12, 10)] * W for _ in range(H)]
    depth = [[math.inf] * W for _ in range(H)]
    tris = 0
    g_idx0 = mesh.ground["index_start"]
    for va, vb, vc, sid in mesh.triangles():
        pa = cam.pixel(va)
        pb = cam.pixel(vb)
        pc = cam.pixel(vc)
        if pa is None or pb is None or pc is None:
            continue                      # behind camera (no clip: recorded)
        if pa[2] < NEAR or pb[2] < NEAR or pc[2] < NEAR:
            continue
        if pa[2] > FAR and pb[2] > FAR and pc[2] > FAR:
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
            # checker two-tone from the bundle's frozen style by grid parity
            gx = int(math.floor((va[0] + vb[0] + vc[0]) / 3.0))
            gz = int(math.floor((va[2] + vb[2] + vc[2]) / 3.0))
            col = COLOURS["ground_A"] if (gx + gz) % 2 == 0 else COLOURS["ground_B"]
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
    half = 20.0                                        # scene bounds layer
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
    g0 = mesh.ground["index_start"]                    # render mesh layer
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
    if probes:                                         # normals/contact layer
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
    if labels:                                         # stable 3D labels layer
        for lab in labels:
            px = cam.pixel(lab["anchor"])
            if px is None or not (0 <= px[0] < W and 0 <= px[1] < H):
                continue
            x, y = int(px[0]), int(px[1])
            for dx, dy in ((-4, 0), (4, 0), (0, -4), (0, 4), (0, 0)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < W and 0 <= yy < H:
                    colour[yy][xx] = yellow


# --- BMP writers ---------------------------------------------------------------
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


def write_depth_bmp(path, depth):
    finite = [z for row in depth for z in row if math.isfinite(z)]
    require(finite, "f01_empty_depth", path.name)
    zmin, zmax = min(finite), max(finite)
    colour = [[(0, 0, 0)] * W for _ in range(H)]
    span = (zmax - zmin) or 1.0
    for y in range(H):
        row = depth[y]
        crow = colour[y]
        for x in range(W):
            z = row[x]
            if math.isfinite(z):
                v = max(0, min(255, int((z - zmin) / span * 255.0 + 0.5)))
                crow[x] = (v, v, v)
    write_bmp(path, colour)
    return {"depth_min_m": zmin, "depth_max_m": zmax}


# --- probes: render/collision correspondence -----------------------------------
VISIBILITY_BAR_M = 1e-6
HEIGHT_BAR_M = 1e-9
NORMAL_BAR = 1e-12
TRUNK_BAR_M = 1e-9


def classify_probe(mesh, cam, probe):
    """Outcome per frozen view: VISIBLE_EXACT / VISIBLE_BUT_MISMATCH /
    OCCLUDED / OFF_FRAME / UNRENDERED, with numerical bars (P5)."""
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
        base = mesh.trunk["site"]["base_centre_m"]
        r = mesh.trunk["collision_representation"]["solid"]["radius_m"]
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
    else:  # boundary_post anchor: identity is the section + exact first hit
        rec["ok_bars"] = True
    rec["outcome"] = ("VISIBLE_EXACT" if rec["ok_bars"]
                      else "VISIBLE_BUT_MISMATCH")
    return rec




def run_probes(mesh, views, probes):
    """Frozen P5 (as amended by A1): per-kind acceptance + global no-mismatch."""
    per_view = {}
    for vname in VIEW_ORDER:
        cam = views[vname]
        per_view[vname] = {}
        for pr in probes:
            per_view[vname][pr["id"]] = classify_probe(mesh, cam, pr)
    by_id = {pr["id"]: pr for pr in probes}
    failures = []
    # global: no VISIBLE_BUT_MISMATCH anywhere (render/collision divergence)
    for vname, rows in per_view.items():
        for pid, rec in rows.items():
            if rec["outcome"] == "VISIBLE_BUT_MISMATCH":
                failures.append({"probe": pid, "view": vname,
                                 "why": "visible but bars breached",
                                 "rec": rec})
    # ground + spawn: VISIBLE_EXACT with bars in >= 1 view
    for pr in probes:
        if pr["kind"] in ("ground", "spawn"):
            ok_views = [v for v in VIEW_ORDER
                        if per_view[v][pr["id"]]["outcome"] == "VISIBLE_EXACT"]
            if not ok_views:
                failures.append({"probe": pr["id"], "why": "never visible",
                                 "outcomes": {v: per_view[v][pr["id"]]["outcome"]
                                              for v in VIEW_ORDER}})
    # boundary post tops: VISIBLE_EXACT in the overview
    for pr in probes:
        if pr["kind"] == "boundary_post":
            if per_view["V1_clearing_overview"][pr["id"]]["outcome"] != "VISIBLE_EXACT":
                failures.append({"probe": pr["id"], "view": "V1",
                                 "why": "post top not visible in overview",
                                 "rec": per_view["V1_clearing_overview"][pr["id"]]})
    # trunk lateral: VISIBLE_EXACT in V2
    for pr in probes:
        if pr["kind"] == "trunk":
            rec = per_view["V2_seam_closeup"][pr["id"]]
            if rec["outcome"] != "VISIBLE_EXACT":
                failures.append({"probe": pr["id"], "view": "V2",
                                 "why": "trunk probe not visible in seam view",
                                 "rec": rec})
    # seam probes: exact cylinder-silhouette prediction (A6). A probe is
    # predicted OCCLUDED-by-trunk_01 in V2 iff the sightline's closest
    # horizontal approach to the trunk axis is < R; else VISIBLE_EXACT.
    cam2 = views["V2_seam_closeup"]
    axis2 = mesh.trunk["site"]["base_centre_m"]
    radius = mesh.trunk["collision_representation"]["solid"]["radius_m"]
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
                    and rec.get("occluder") == "trunk_01"):
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
    return {"prediction": "P5_render_collision_correspondence",
            "per_view": per_view, "failures": failures,
            "probe_count": len(probes),
            "all_probes_meet_frozen_rule": not failures,
            "ok": not failures}


# --- labels -------------------------------------------------------------------
def frozen_labels(declaration, trunk):
    mounds = declaration["terrain"]["recipe"]["mounds"]
    labels = [{"id": "spawn", "anchor": [0.0, 0.0, 0.0]}]
    base = trunk["site"]["base_centre_m"]
    labels.append({"id": "trunk_01",
                   "anchor": [base[0], base[1] + trunk["geometry"]["height_m"],
                              base[2]]})
    for name, x, z in (("SW", -20.0, -20.0), ("SE", 20.0, -20.0),
                       ("NE", 20.0, 20.0), ("NW", -20.0, 20.0)):
        labels.append({"id": "corner_" + name, "anchor": [x, 0.9, z]})
    for name, x, z in (("N", 0.0, 20.0), ("E", 20.0, 0.0),
                       ("S", 0.0, -20.0), ("W", -20.0, 0.0)):
        labels.append({"id": "edge_" + name, "anchor": [x, 0.9, z]})
    for i, m in enumerate(mounds, 1):
        labels.append({"id": "mound_m%d" % i,
                       "anchor": [m["centre_x_m"], m["amplitude_m"],
                                  m["centre_z_m"]]})
    require(len(labels) == 15, "f01_label_count", len(labels))
    return labels


# --- falsifier bites (failing-first) -------------------------------------------
def bite_ghost_support(surface, trunk, tb):
    """B1: +0.01 m on one ground vertex of a bundle copy (with its stored
    face normals recomputed so the copy LOADS clean -- the engine hygiene gate
    is not the thing under test) must break the correspondence bar at that
    triangle's centroid probe. Demonstrates the check is not tag-based."""
    bundle = json.loads(json.dumps(surface.bundle))
    verts = bundle["render"]["vertices"]
    gsec = bundle["render"]["sections"]["ground"]
    target = (-8.0, -8.0)
    best_i, best_d = None, None
    for i in range(gsec["vertex_start"],
                   gsec["vertex_start"] + gsec["vertex_count"]):
        x, y, z = verts[9 * i:9 * i + 3]
        d = (x - target[0]) ** 2 + (z - target[1]) ** 2
        if best_d is None or d < best_d:
            best_i, best_d = i, d
    verts[9 * best_i + 1] += 0.01
    # find and repair the stored normals of every triangle using that vertex
    # (fully duplicated vertices: only this triangle's copies move)
    g0, g1 = gsec["index_start"], gsec["index_start"] + gsec["index_count"]
    idx = bundle["render"]["indices"]
    touched = []
    for k in range(g0, g1, 3):
        if best_i in (idx[k], idx[k + 1], idx[k + 2]):
            pa = verts[9 * idx[k]:9 * idx[k] + 3]
            pb = verts[9 * idx[k + 1]:9 * idx[k + 1] + 3]
            pc = verts[9 * idx[k + 2]:9 * idx[k + 2] + 3]
            n = vnorm(vcross(vsub(pb, pa), vsub(pc, pa)))
            for j in range(3):
                verts[9 * idx[k + j] + 3:9 * idx[k + j] + 6] = n
            touched.append(k // 3)
    require(len(touched) == 1, "f01_bite_not_one_triangle",
            {"vertex": best_i, "triangles": touched})
    body = {k: v for k, v in bundle.items() if k != "bundle_sha256"}
    bundle["bundle_sha256"] = digest(body)
    tampered_surface = type(surface)(tb.loads(canonical(bundle)), validate=True)
    mesh = SceneMesh(tampered_surface, trunk)
    tri_idx = touched[0] * 3
    tx = [idx[tri_idx], idx[tri_idx + 1], idx[tri_idx + 2]]
    cx = sum(verts[9 * i] for i in tx) / 3.0
    cz = sum(verts[9 * i + 2] for i in tx) / 3.0
    h_true = surface.height_at(cx, cz)
    probe = {"id": "bite_ghost", "kind": "ground", "point": [cx, h_true, cz],
             "surface": "monkey_clearing_ground", "oracle_h": h_true,
             "oracle_n": list(surface.normal_at(cx, cz))}
    cam = Camera(VIEWS["V1_clearing_overview"])
    rec = classify_probe(mesh, cam, probe)
    bites = rec["outcome"] in ("VISIBLE_BUT_MISMATCH", "OCCLUDED", "UNRENDERED")
    return {"bite": "B1_ghost_support", "tampered_vertex_index": best_i,
            "tampered_triangle": touched[0],
            "probe_point": probe["point"],
            "oracle_height_m": h_true,
            "outcome": rec["outcome"],
            "height_err_m": rec.get("height_err_m"),
            "bar_m": HEIGHT_BAR_M,
            "loads_clean": True,
            "bites": bites}


def _redigest(declaration):
    body = {k: v for k, v in declaration.items() if k != "declaration_sha256"}
    declaration["declaration_sha256"] = digest(body)
    return declaration


def bite_missing_boundary(recipe, declaration):
    """B2: one post moved 0.5 m inward must refuse (off-edge/invisible-wall)."""
    tampered = json.loads(json.dumps(declaration))
    tampered["boundary"]["rendered"]["posts_m"][0][2] += 0.5
    _redigest(tampered)
    try:
        recipe.validate_declaration(recipe.loads(canonical(tampered)))
    except recipe.Refusal as exc:
        return {"bite": "B2_missing_boundary", "refused": True,
                "code": exc.code, "detail": exc.detail, "bites": True}
    return {"bite": "B2_missing_boundary", "refused": False, "bites": False}


def bite_unsafe_spawn(recipe, declaration):
    """B3: a mound re-centred near the spawn must refuse (spawn exclusion)."""
    tampered = json.loads(json.dumps(declaration))
    tampered["terrain"]["recipe"]["mounds"][0]["centre_x_m"] = 2.0
    tampered["terrain"]["recipe"]["mounds"][0]["centre_z_m"] = 2.0
    _redigest(tampered)
    try:
        recipe.validate_declaration(recipe.loads(canonical(tampered)))
    except recipe.Refusal as exc:
        return {"bite": "B3_unsafe_spawn", "refused": True,
                "code": exc.code, "detail": exc.detail, "bites": True}
    return {"bite": "B3_unsafe_spawn", "refused": False, "bites": False}


def bite_off_frame(mesh):
    """B4 (Amendment A2): the SW corner post top 'required visible' in the
    seam close-up (155.7 deg off the view axis, behind the camera) must
    classify OFF_FRAME -- the visibility classifier detects off-frame
    subjects rather than passing them."""
    probe = {"id": "post_top_SW", "kind": "boundary_post",
             "point": [-20.0, 0.9, -20.0],
             "surface": "monkey_clearing_boundary_posts",
             "label_degenerate": True}
    rec = classify_probe(mesh, Camera(VIEWS["V2_seam_closeup"]), probe)
    return {"bite": "B4_off_frame", "outcome": rec["outcome"],
            "view": "V2_seam_closeup",
            "bites": rec["outcome"] == "OFF_FRAME"}


# --- pinned predictions ---------------------------------------------------------
def check_p1_determinism(recipe, pins):
    pinned = pins["clearing_declaration_json"]["bytes"]
    runs = []
    for i in range(4):
        raw = canonical(recipe.compile_declaration())
        runs.append({"run": i, "sha256": sha_bytes(raw),
                     "identical": raw == pinned})
    return {"prediction": "P1_determinism", "runs": runs,
            "ok": all(r["identical"] for r in runs)}


def check_p2_numbers(recipe, surface, pins):
    receipt = recipe.validate_declaration(recipe.loads(
        pins["clearing_declaration_json"]["bytes"]))
    worst_tri_slope, where = surface.worst_triangle_slope()
    mounds = receipt and json.loads(pins["clearing_declaration_json"]["bytes"]
                                    .decode("utf-8"))["terrain"]["recipe"]["mounds"]
    continuous_bound = max(m["amplitude_m"] * math.pi / (2.0 * m["radius_m"])
                           for m in mounds)
    checks = {
        "spawn_clearance_m": receipt["spawn_clearance_m"],
        "required_clearance_m": receipt["required_clearance_m"],
        "spawn_clearance_ok":
            receipt["spawn_clearance_m"] >= receipt["required_clearance_m"],
        "worst_grid_slope_m_per_m": receipt["worst_grid_slope_m_per_m"],
        "worst_triangle_slope_m_per_m": worst_tri_slope,
        "worst_triangle_slope_where": where,
        "continuous_slope_bound_m_per_m": continuous_bound,
        "slope_bound_ok": max(receipt["worst_grid_slope_m_per_m"],
                              worst_tri_slope) <= 0.05,
        "continuous_bound_le_0_0471": continuous_bound <= 0.0471 + 1e-12,
        "grid_points": receipt["grid_points"],
        "worst_grid_error_m": receipt["worst_grid_error_m"],
        "grid_identity_ok": receipt["worst_grid_error_m"] <= 1e-9,
        "mounds": receipt["mounds"],
        "posts": receipt["posts"],
        "worst_gap_to_post_m": receipt["worst_gap_to_post_m"],
        "gap_ok": receipt["worst_gap_to_post_m"] <= 1.0 + 1e-6,
        "worst_on_edge_error_m": receipt["worst_on_edge_error_m"],
        "trunk_site_m": receipt["trunk_site_m"],
        "self_digest_rederived": receipt["declaration_sha256"],
    }
    checks["ok"] = (checks["spawn_clearance_ok"] and checks["slope_bound_ok"]
                    and checks["continuous_bound_le_0_0471"]
                    and checks["grid_identity_ok"] and checks["gap_ok"]
                    and checks["worst_on_edge_error_m"] == 0.0
                    and checks["mounds"] == 5 and checks["posts"] == 80)
    checks["prediction"] = "P2_gentleness_safety_numbers"
    return checks


def check_p3_extent(recipe, surface, declaration):
    half = declaration["extent"]["half_width_m"]
    probes = {
        "corner_sw_inside": surface.classify(-half, -half),
        "corner_ne_inside": surface.classify(half, half),
        "edge_inside": surface.classify(half, 0.0),
        "just_outside_x": surface.classify(half + 1e-6, 0.0),
        "just_outside_z": surface.classify(0.0, -half - 1e-6),
    }
    classify_ok = (probes["corner_sw_inside"] == "inside"
                   and probes["corner_ne_inside"] == "inside"
                   and probes["edge_inside"] == "inside"
                   and probes["just_outside_x"] == "outside"
                   and probes["just_outside_z"] == "outside")
    refusals = []
    for x, z in ((half + 1e-6, 0.0), (0.0, half + 1e-6),
                 (-(half + 1e-6), 0.0), (0.0, -(half + 1e-6))):
        try:
            surface.height_at(x, z)
            refusals.append({"query": [x, z], "refused": False, "code": None})
        except Exception as exc:  # the oracle's own strict intake refusal
            refusals.append({"query": [x, z],
                             "refused": hasattr(exc, "code"),
                             "code": getattr(exc, "code", repr(exc))})
    refusals_ok = all(r["refused"] and r["code"] == "f02_outside_extent"
                      for r in refusals)
    posts = declaration["boundary"]["rendered"]["posts_m"]
    ring_extent = max(max(abs(p[0]), abs(p[2])) for p in posts)
    invisible_wall_ok = abs(ring_extent - half) <= 1e-6
    return {"prediction": "P3_extent_strict_gt",
            "classify": probes, "classify_ok": classify_ok,
            "off_patch_refusals": refusals, "refusals_ok": refusals_ok,
            "ring_extent_m": ring_extent,
            "invisible_wall_ok": invisible_wall_ok,
            "boundary_rule_text": declaration["extent"]["boundary_rule"],
            "ok": classify_ok and refusals_ok and invisible_wall_ok}


def check_p6_spawn(mesh, surface):
    hit = mesh.first_hit([0.0, 50.0, 0.0], [0.0, -1.0, 0.0])
    require(hit is not None, "f01_spawn_ray_no_hit", None)
    t, point, n, sid = hit[0], hit[1], hit[2], hit[3]
    h = surface.height_at(0.0, 0.0)
    return {"prediction": "P6_spawn_on_surface",
            "first_hit_surface": sid, "hit_y": point[1],
            "oracle_height": h, "err_m": abs(point[1] - h),
            "bar": HEIGHT_BAR_M,
            "same_arrays_as_render":
                surface.bundle["collision"]["same_arrays_as_render"],
            "ok": (sid == "monkey_clearing_ground"
                   and abs(point[1] - h) <= HEIGHT_BAR_M)}


def check_p7_boundary(mesh, surface):
    posts = surface.posts()
    sec = mesh.posts_sec
    cam = Camera(VIEWS["V1_clearing_overview"])
    visible = 0
    rows = []
    for i, p in enumerate(posts):
        anchor = [p["position_m"][0], p["top_y_m"], p["position_m"][2]]
        pr = {"id": "post_%02d" % i, "kind": "boundary_post",
              "point": anchor, "surface": "monkey_clearing_boundary_posts",
              "label_degenerate": True}
        rec = classify_probe(mesh, cam, pr)
        rows.append({"post": i, "outcome": rec["outcome"],
                     "offset_used_m": rec.get("offset_used_m")})
        if rec["outcome"] == "VISIBLE_EXACT":
            visible += 1
    derived_post_verts = len(posts) * 3 * (2 * 6 + 6)
    return {"prediction": "P7_boundary_visibility",
            "posts_in_mesh_section": sec["vertex_count"],
            "derived_post_vertices": derived_post_verts,
            "posts_recovered": len(posts),
            "surface_id": sec["surface_id"],
            "visible_in_overview": visible, "total": len(posts),
            "offsets_used": sum(1 for r in rows if r["offset_used_m"]),
            "ok": (len(posts) == 80 and sec["vertex_count"] == 4320
                   and derived_post_verts == 4320
                   and visible == len(posts))}


def camera_manifest(view_name, variant, cam, labels_proj, layers):
    return {
        "frame_id": "ONT-F01/%s_%s" % (view_name, variant),
        "coordinate_unit": "m",
        "position": cam.position,
        "orientation_convention_and_values": (
            "look-at, right-handed, x=east y=up z=south; fwd=%s right=%s up=%s "
            "(unit vectors)" % (fmt_vec(cam.fwd), fmt_vec(cam.right),
                                fmt_vec(cam.up))),
        "target": cam.target,
        "distance_to_target": cam.distance_to_target,
        "projection": "perspective pinhole",
        "vertical_fov_or_orthographic_span": math.degrees(cam.vfov),
        "near_far_planes": [NEAR, FAR],
        "aspect_ratio": cam.aspect,
        "viewport_resolution": [W, H],
        "camera_motion_or_bookmark_sequence":
            "static bookmark (single frozen frame)",
        "visibility_layers": layers,
        "label_ids": labels_proj,
        "occlusion_or_xray_mode": "opaque z-buffer (no x-ray)",
        "state_or_tick_interval": "static scene, no tick (t=0)",
    }


def fmt_vec(v):
    return "[%.17g, %.17g, %.17g]" % (v[0], v[1], v[2])


# --- the build -----------------------------------------------------------------
PREDICTION_KEYS = ["P1_determinism", "P2_numbers", "P3_extent", "C01_frames",
                   "P5_correspondence", "P6_spawn", "P7_boundary", "P8_frames"]


def run_bites(pins, recipe, declaration, surface, trunk, tb):
    mesh = SceneMesh(surface, trunk)
    bites = [
        bite_ghost_support(surface, trunk, tb),
        bite_missing_boundary(recipe, declaration),
        bite_unsafe_spawn(recipe, declaration),
        bite_off_frame(mesh),
    ]
    return bites


def build():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    results = {"schema": SCHEMA, "card": "ONT-F01",
               "attempt_id": "ff6ee7ed079c48a3b3835cd146f89bfd",
               "criteria_sha256":
                   "cbbcae167a0930f55ba11b7da57a5827013e70e6fbcb0fae8f70c3cd7914e654",
               "order": ["bites_first_failing", "pinned_pass_second"]}

    pins = materialize_pins()
    results["pins"] = {k: {kk: vv for kk, vv in v.items() if kk != "bytes"}
                       for k, v in pins.items()}
    results["pins_hash_conventions"] = {
        k: normalized_hashes(v["bytes"]) for k, v in pins.items()}

    recipe, declaration, surface, trunk, tb = load_sources(pins)

    # ---- failing-first falsifier bites (B1-B4), recorded BEFORE the pass ----
    bites = run_bites(pins, recipe, declaration, surface, trunk, tb)
    results["falsifier_bites"] = bites
    results["all_bites_bite"] = all(b.get("bites", False) for b in bites)
    (EVIDENCE / "bites.json").write_bytes(json.dumps(
        {"bites": bites, "all_bite": results["all_bites_bite"]},
        indent=1, sort_keys=True).encode("utf-8"))

    # ---- pinned pass ----
    mesh = SceneMesh(surface, trunk)
    results["P1_determinism"] = check_p1_determinism(recipe, pins)
    results["P2_numbers"] = check_p2_numbers(recipe, surface, pins)
    results["P3_extent"] = check_p3_extent(recipe, surface, declaration)
    results["C01_frames"] = c01_frame_checks(surface, trunk, declaration)

    views = {k: Camera(v) for k, v in VIEWS.items()}
    probes = frozen_probes(surface, trunk)
    results["P5_correspondence"] = run_probes(mesh, views, probes)
    results["P6_spawn"] = check_p6_spawn(mesh, surface)
    results["P7_boundary"] = check_p7_boundary(mesh, surface)

    labels = frozen_labels(declaration, trunk)
    manifest = {}
    frames = {}
    for vname in VIEW_ORDER:
        cam = views[vname]
        labels_proj = []
        for lab in labels:
            px = cam.pixel(lab["anchor"])
            labels_proj.append({"id": lab["id"], "anchor": lab["anchor"],
                                "projected_px": [px[0], px[1]] if px else None,
                                "in_frame": bool(px and 0 <= px[0] < W
                                                 and 0 <= px[1] < H)})
        layers = ["monkey_clearing_ground", "monkey_clearing_boundary_posts",
                  "trunk_01"]
        colour, depth, stats = render_frame(mesh, cam, diagnostic=False)
        clean_name = "frame_%s_clean.bmp" % vname
        write_bmp(EVIDENCE / clean_name, colour)
        depth_name = "depth_%s.bmp" % vname
        dinfo = write_depth_bmp(EVIDENCE / depth_name, depth)
        colour_d, _, stats_d = render_frame(mesh, cam, diagnostic=True,
                                            probes=probes, labels=labels)
        diag_name = "frame_%s_diagnostic.bmp" % vname
        write_bmp(EVIDENCE / diag_name, colour_d)
        manifest[vname + "_clean"] = camera_manifest(
            vname, "clean", cam, labels_proj, layers)
        manifest[vname + "_diagnostic"] = camera_manifest(
            vname, "diagnostic", cam, labels_proj,
            layers + ["diagnostic: render-mesh wireframe",
                      "diagnostic: normals/contact markers",
                      "diagnostic: scene bounds",
                      "diagnostic: stable 3D labels"])
        frames[vname] = {"clean": clean_name, "diagnostic": diag_name,
                         "depth": depth_name,
                         "triangles_drawn_clean": stats["triangles_drawn"],
                         "triangles_drawn_diagnostic": stats_d["triangles_drawn"],
                         "depth_range": dinfo}
    results["P8_frames"] = {
        "prediction": "P8_frames_manifest",
        "frames": frames,
        "camera_manifest_views": sorted(manifest.keys()),
        "camera_fields_order": [
            "frame_id", "coordinate_unit", "position",
            "orientation_convention_and_values", "target", "distance_to_target",
            "projection", "vertical_fov_or_orthographic_span",
            "near_far_planes", "aspect_ratio", "viewport_resolution",
            "camera_motion_or_bookmark_sequence", "visibility_layers",
            "label_ids", "occlusion_or_xray_mode", "state_or_tick_interval"],
        "ok": len(frames) == 4 and all(
            len(manifest[m]) == 16 for m in manifest)}
    (EVIDENCE / "camera_manifest.json").write_bytes(json.dumps(
        {"views": manifest}, indent=1, sort_keys=True).encode("utf-8"))

    results["all_ok"] = (results["all_bites_bite"]
                         and all(results[k].get(
                             "ok", results[k].get("all_ok")) for k in PREDICTION_KEYS))
    results["merged_followup_context"] = MERGED_FOLLOWUP
    results["honest_boundary"] = {
        "claim": "static-scene qualification of the pinned clearing data "
                 "package plus an attempt-local stdlib render of those bytes",
        "not_claimed": [
            "engine run or HTTP load_mesh exercise",
            "native collision query route (#120 S1-3)",
            "engine-side render upload (#120 S1-4)",
            "engine walk replay or playable-build acceptance",
            "trunk contact subsystem (Stage 2)",
            "training or runtime acceptance",
            "W10 scene readiness"],
        "play_lane_citation_policy": "R5 correction: play artifacts cited as "
                                     "static/data-package evidence only"}
    (EVIDENCE / "checks.json").write_bytes(json.dumps(
        results, indent=1, sort_keys=True).encode("utf-8"))
    print(json.dumps({"evidence": str(EVIDENCE),
                      "all_ok": results["all_ok"],
                      "bites_all_bite": results["all_bites_bite"]}))
    return results


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] == "build":
        results = build()
        return 0 if results["all_ok"] else 1
    if argv[0] == "bites":
        pins = materialize_pins()
        recipe, declaration, surface, trunk, tb = load_sources(pins)
        bites = run_bites(pins, recipe, declaration, surface, trunk, tb)
        ok = all(b.get("bites", False) for b in bites)
        print(json.dumps({"bites": bites, "all_bite": ok}))
        return 0 if ok else 1
    raise Refusal("f01_cli_verb", argv)


if __name__ == "__main__":
    sys.exit(main())
