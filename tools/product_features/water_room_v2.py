"""WATER ROOM v2 — water as a visible BODY: a pool with a rising level
(feature-water-room-v2-01).

The v1 blind judge CONFIRMED the simulation runs but wrote the v2 spec
verbatim: "The only visible evidence of water is a small blue patch at the
neck - there is no water surface, pool, or rising level on the floor or in
the room"; the pour start happened off-screen; spreading was not obviously
progressive between keyframes; the injection readout is cryptic.

v2's answer, ALL PYTHON, ZERO C++ (the engine service is frozen):

  The water vis plane (water_vis.comp) is NOT a tint — it emits real
  displaced geometry: every wet cell's triangle, displaced by depth
  d = V*Q/A along its own normal, fixed water blue. v1 fed that plane the
  CREATURE's surface and poured at the TOP cell, so only a thin cap ever
  existed. v2 derives a PLANAR FLOOR BASIN at runtime in Python (a square-
  grid disc appended to the creature mesh in ONE /mesh_bin composite; the
  disc block is the water part) and pours just outside the creature's
  silhouette on the camera side. On a flat disc the CA's bed is constant,
  so flow is pure surface-height equalization: the water SPREADS radially
  and the level RISES — a pool with a rising level, rendered as an actual
  body, measurable through /water_vis_state (the rendered water vertices).

Public HTTP surface only:
  POST /mesh_bin, POST /water_bin, POST /water_vis, POST /water_clock,
  GET /water_clock, GET /water_state, GET /state, GET /water_vis_state,
  POST /camera, GET /glass, GET /frame
plus the two harness wrappers (tools/engine_demo.py launch/stop;
cpp_bridge.encode_movie). The substrate laws are v1's
(tools/product_features/water_room.py), re-used verbatim where the
geometry is the same and re-derived where the substrate changed
(derivation IDs D1-D10 in PREREGISTRATION.txt).

Preregistration: docs/evidence/agent_fleet/FEATURE_WATER_ROOM_V2/
PREREGISTRATION.txt (RULE 0, committed BEFORE any run, zero actuals).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import struct
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
from engine_demo import _launch, _wait_ready, _stop_owned, _port_busy  # noqa: E402

OUT_DEFAULT = ROOT / "docs/evidence/agent_fleet/FEATURE_WATER_ROOM_V2"

# ── declared constants (PREREGISTRATION.txt D4: verbatim v1 recorded values) ─
MESH_BIN = ROOT / "Saved/meshes/monkey_birth.bin"
C_LOCAL = 0.07120992734952862     # measured C_sw_global (SALLY_body_0)
L_PART = 0.012259485812807563     # measured l_scale_med -> pipe height h_pipe
A_MIN = 4.1654367130014345e-07    # measured area.min
Q = A_MIN * L_PART                # integer quantum [m^3] (the ledger's Q law)
GRAV = 9.81                       # tri_water.G
ALPHA = 0.1                       # slope factor (CHOSEN-UNVERIFIED in the ledger)
DT_MACRO = 0.01                   # macro step [s]
STEPS_PER_FRAME = 4               # engine-clock water steps per rendered frame
INJ_COUNT = 2000                  # quanta/step while pouring (the proven visible rate)
FPS = 10                          # capture cadence (wall clock) and movie fps
N_DRY = 40                        # f000-039  DRY+idle    (4.0 s)
N_POUR = 140                      # f040-179 POUR        — ACTION 1 at f040
N_SETTLE = 60                     # f180-239 SETTLE      — ACTION 2 at f180
N_FRAMES = N_DRY + N_POUR + N_SETTLE          # 240 frames = 24.0 s take
KEYFRAMES = (30, 40, 42, 90, 150, 179, 239)   # engine-truth keyframes
JUDGE_KEYFRAMES = (30, 40, 42, 90, 150, 239)  # the ordered judge six (D8)
CAM_RADIUS_FACTOR = 3.4           # v1 recorded framing (motion-sweep fix)
CAM_THETA, CAM_PHI = 0.5, 0.35    # v1 recorded camera
FLOOR_COLOR = (0.22, 0.23, 0.25)  # D10: neutral basin gray (declared pre-run)
R_DISC_FACTOR = 2.5               # D2: disc radius = 2.5 x R_body
POUR_DIST_FACTOR = 1.35           # D6: pour point radius = 1.35 x R_body
LEVEL_REL_TOL = 1e-5              # g4 tolerance (f32 render vs f64 ledger)
PORT = 8103                       # slot-03 candidate port (never 8080; checked at run)

BASE = f"http://127.0.0.1:{PORT}"
ST: dict = {}
RECORDS: list[dict] = []


def record(name: str, verdict: str, detail: dict) -> None:
    RECORDS.append({"name": name, "verdict": verdict, "detail": detail})
    print(f"[{verdict}] {name} {json.dumps(detail, default=str)[:220]}", flush=True)


def request(method: str, path: str, body: bytes | None = None,
            ctype: str = "application/json", timeout: float = 60.0):
    req = urllib.request.Request(BASE + path, data=body, method=method)
    if body is not None:
        req.add_header("Content-Type", ctype)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def jreq(method: str, path: str, payload=None) -> dict:
    body = json.dumps(payload).encode() if payload is not None else None
    st, raw = request(method, path, body)
    return json.loads(raw.decode("utf-8", "replace"))


# ── the creature mesh (v1's loader, verbatim) ───────────────────────────────
def load_whole_mesh(bin_path: Path) -> tuple[np.ndarray, np.ndarray]:
    raw = bin_path.read_bytes()
    n, m = struct.unpack("<ii", raw[:8])
    verts = np.frombuffer(raw, dtype=np.float32, count=n * 3, offset=8).reshape(n, 3)
    tris = np.frombuffer(raw, dtype=np.uint32, count=m * 3, offset=8 + n * 12).reshape(m, 3)
    return verts, tris


# ── the derived floor basin (D1-D3, D10) ────────────────────────────────────
def tri_areas(verts: np.ndarray, tris: np.ndarray) -> np.ndarray:
    v = verts[tris.astype(np.int64)]
    return 0.5 * np.linalg.norm(np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0]),
                                axis=1).astype(np.float64)


def creature_mean_cell_area(verts: np.ndarray, tris: np.ndarray) -> float:
    """A_mean over the creature's WATER part (SALLY_body_0, v1's substrate).

    The disc's cells must run at the scale the solver constants were
    measured at (D3), so A_mean is the mean area of the v1 water cells,
    not of the whole mesh (the eyes part is finer/differently scaled).
    """
    part = tris[2092:2092 + 34538].astype(np.int64)
    return float(tri_areas(verts, part).mean())


def build_floor_disc(verts: np.ndarray, tris: np.ndarray) -> dict:
    """D1-D3, D10: the square-grid disc basin, derived from the creature.

    Returns the composite (verts, tris) plus the disc's geometry book:
    tri_base (first disc face in the composite), vert_base, cell grid and
    the disc cell centers (for the substrate build).
    """
    y_floor = float(verts[:, 1].min())                       # D1
    horiz = np.sqrt(verts[:, 0] ** 2 + verts[:, 2] ** 2)
    r_body = float(horiz.max())                              # D2
    centroid_xz = np.array([float(verts[:, 0].mean()), float(verts[:, 2].mean())])
    r_disc = R_DISC_FACTOR * r_body
    a_mean = creature_mean_cell_area(verts, tris)
    # each QUAD splits into 2 triangles (the water cells): quad side
    # s = sqrt(2*A_mean) makes every disc triangle's area == A_mean, the
    # measured scale of the solver constants (D3)
    s = math.sqrt(2.0 * a_mean)

    n_side = int(math.ceil(2.0 * r_disc / s)) + 1
    axis = (np.arange(n_side) - (n_side - 1) / 2.0) * s
    gx, gz = np.meshgrid(axis, axis, indexing="ij")
    keep = (gx ** 2 + gz ** 2) <= r_disc ** 2                # clip to the disc (D2)

    # full-grid vertex block (contiguous by construction; unreferenced
    # corner verts are never in the index buffer and never render)
    nv_axis = n_side + 1
    vx = (np.arange(nv_axis) - (nv_axis - 1) / 2.0) * s
    vxx, vzz = np.meshgrid(vx, vx, indexing="ij")
    disc_verts = np.column_stack([
        vxx.ravel().astype(np.float32),
        np.full(vxx.size, y_floor, dtype=np.float32),
        vzz.ravel().astype(np.float32)])
    v_id = np.arange(nv_axis * nv_axis, dtype=np.int64).reshape(nv_axis, nv_axis)

    cells = np.argwhere(keep)                                # (i, j) kept cells
    quad = np.stack([v_id[cells[:, 0], cells[:, 1]],
                     v_id[cells[:, 0] + 1, cells[:, 1]],
                     v_id[cells[:, 0] + 1, cells[:, 1] + 1],
                     v_id[cells[:, 0], cells[:, 1] + 1]], axis=1)
    disc_tris = np.concatenate([
        quad[:, [0, 2, 1]], quad[:, [0, 3, 2]]], axis=0).astype(np.uint32)

    # winding check is cheap and decisive: normals must be +Y (water
    # displacement is along the cell normal; the level must rise UP)
    tv = disc_verts[disc_tris.astype(np.int64)]
    nrm = np.cross(tv[:, 1] - tv[:, 0], tv[:, 2] - tv[:, 0])
    up_frac = float((nrm[:, 1] > 0).mean())
    assert up_frac == 1.0, f"disc winding broken: {up_frac} of normals +Y"

    vert_base = len(verts)
    tri_base = len(tris)
    comp_verts = np.concatenate([verts, disc_verts], axis=0)
    comp_tris = np.concatenate([
        tris.astype(np.uint32),
        (disc_tris + vert_base).astype(np.uint32)], axis=0)

    # declared feasibility bounds (named refusal, never a silent retune):
    # substrate within ~4x the proven v1 scale, composite POST within 64 MB
    n_cells_bound, post_mb_bound = 200_000, 64.0
    post_mb = (len(comp_verts) * 36 + len(comp_tris) * 4) / 1e6
    assert len(disc_tris) <= n_cells_bound, \
        f"disc cells {len(disc_tris)} > bound {n_cells_bound} (D3 bound)"
    assert post_mb <= post_mb_bound, \
        f"composite POST {post_mb:.1f} MB > bound {post_mb_bound} MB"

    centers = disc_verts[disc_tris.astype(np.int64)].mean(axis=1)
    return {
        "y_floor": y_floor, "r_body": r_body, "r_disc": r_disc,
        "a_mean": a_mean, "cell_size": s, "centroid_xz": centroid_xz,
        "vert_base": vert_base, "tri_base": tri_base,
        "n_cells": len(disc_tris),
        "comp_verts": comp_verts, "comp_tris": comp_tris,
        "disc_tris": disc_tris.astype(np.int64), "centers": centers,
        "up_frac": up_frac,
    }


# ── the substrate over the disc (v1's build_substrate law, disc part) ───────
def build_substrate_disc(D: dict) -> dict:
    """v1's tri_water laws over the disc cells: exactly-2-tri primal edges
    (the basin rim's 1-tri edges drop out — the disc cannot leak), canonical
    order, order-consistent coloring (contract-preserving greedy, D11),
    slope bed (constant on the flat disc), k_e/l_ij verbatim.

    D5 CORRECTION (measured before the run, recorded): v1's verbatim
    seen-set loop pairs each triangle t with each of its PRIMAL VERTEX ids
    u and reads centers[u] — a cell center indexed by a VERTEX id. On the
    creature the vertex and cell id ranges overlap, so cube_edge came out
    as a near-diameter scale and the "occupied centre cube" disabled
    whatever fell in it — harmless THERE, but on the disc the same loop
    disables 25% of cells (measured). The law's PURPOSE (water_setup.py)
    is to disable cells INSIDE the solid: a planar disc has no interior
    cells, so occ is NONE on the disc and every pipe is active. cube_addr
    survives ONLY as the canonical edge-sort key, now computed from the
    TRUE dual-adjacent pair distances (the comment's 'tight in-ring
    bound')."""
    part_v = D["comp_verts"][D["vert_base"]:].astype(np.float64)  # the disc's own block
    part_i = D["disc_tris"]                                       # disc-local indices
    centers = D["centers"]

    n = len(part_i)

    # dual edges: exactly-two-triangle primal edges, canonical order
    # (tri_water.build_substrate: lower cube_addr tuple first, then primal
    # key; dict insertion order is the tri loop order, the sort is stable)
    prim2tris: dict[tuple[int, int], list[int]] = {}
    for t, tri in enumerate(part_i):
        a, b, c = int(tri[0]), int(tri[1]), int(tri[2])
        for u, w in ((a, b), (b, c), (c, a)):
            key = (min(u, w), max(u, w))
            prim2tris.setdefault(key, []).append(t)
    edges = []
    for (pv0, pv1), ts in prim2tris.items():
        if len(ts) != 2:
            continue
        t0, t1 = ts[0], ts[1]
        l_ij = float(np.linalg.norm(centers[t0] - centers[t1]))
        if l_ij == 0.0:
            continue
        edge_len = float(np.linalg.norm(part_v[pv1] - part_v[pv0]))
        edges.append((t0, t1, l_ij, edge_len, (pv0, pv1)))

    # the tight in-ring bound, from TRUE dual pairs this time
    max_d = 0.0
    for e in edges:
        d = e[2]
        if d > max_d:
            max_d = d
    cube_edge = max_d
    cube_addr = np.floor(centers / cube_edge).astype(np.int64)

    # canonical orientation + order: lower cube_addr tuple first, then the
    # primal key (tri_water.build_substrate, verbatim rule)
    oriented = []
    for (t0, t1, l_ij, edge_len, pvk) in edges:
        if tuple(cube_addr[t0]) <= tuple(cube_addr[t1]):
            i0, i1 = t0, t1
        else:
            i0, i1 = t1, t0
        oriented.append((i0, i1, l_ij, edge_len, tuple(cube_addr[i0]), pvk))
    oriented.sort(key=lambda e: (e[4], e[5]))
    edges_sorted = oriented

    areas = tri_areas(part_v.astype(np.float32), part_i)

    # order-consistent edge coloring. v1's exact rule was c = 1+max(colors at
    # the two cells); on the creature's irregular duals that stays small
    # (63), but on a large regular grid the max+1 walk climbs unboundedly
    # (measured 853 here — a kernel-launch blowup for the color-serial
    # solver). The law's CONTRACT is: edges sharing a cell get DISTINCT
    # colors, chosen deterministically in the canonical edge order. That
    # contract is satisfied by the smallest-excluded-color greedy, which
    # stays <= degree+1 (<= 6 on the grid). Deviation recorded in
    # PREREGISTRATION.txt (D11); the assert below pins the bound.
    cell_colors: list[set[int]] = [set() for _ in range(n)]
    colors = np.zeros(len(edges_sorted), dtype=np.int32)
    for k, e in enumerate(edges_sorted):
        used = cell_colors[e[0]] | cell_colors[e[1]]   # sets hold COLORS
        c = 1
        while c in used:
            c += 1
        colors[k] = c
        cell_colors[e[0]].add(int(c))
        cell_colors[e[1]].add(int(c))
    n_colors = int(colors.max())
    sorted_colors = colors  # edges_sorted IS the canonical order already
    color_start = np.zeros(n_colors + 1, dtype=np.int64)
    for c in range(1, n_colors + 1):
        color_start[c] = int(np.searchsorted(sorted_colors, c, side="right"))

    downhill = np.array([0.0, 1.0, 0.0])
    bed = ALPHA * (centers @ downhill)
    mesh_center = centers.mean(axis=0)
    center_cube = tuple(np.floor(mesh_center / cube_edge).astype(np.int64))
    # D5 CORRECTION: no interior cells on a planar disc — every cell is a
    # surface cell, every pipe active (see the docstring; the verbatim
    # centre-cube loop would disable 25% of the disc by an index-overlap
    # accident, measured before the run and recorded in the prereg)
    occ_mask = np.zeros(n, dtype=bool)
    ei = np.array([[e[0], e[1]] for e in edges_sorted], dtype=np.int32)
    l_ij = np.array([e[2] for e in edges_sorted], dtype=np.float64)
    k_e = np.array([GRAV * (e[3] * L_PART) / e[2] for e in edges_sorted], dtype=np.float64)
    edge_active = np.ones(len(edges_sorted), dtype=np.uint32)

    free = np.flatnonzero(~occ_mask)

    # declared substrate sanity (a flat grid disc must satisfy these; a
    # violation means the derivation is corrupted — named refusal, never a
    # silent push to the engine)
    assert n_colors <= 32, f"edge coloring exploded: {n_colors} colors (grid must color in a handful)"
    # the coloring CONTRACT: every cell's edges carry pairwise-distinct
    # colors (this is what makes the color-serial solver step correct)
    seen_cell: dict[int, dict] = {}
    for k, e in enumerate(edges_sorted):
        for cell in (e[0], e[1]):
            s = seen_cell.setdefault(cell, {})
            if colors[k] in s:
                raise AssertionError(
                    f"coloring contract violated at cell {cell}: color "
                    f"{colors[k]} repeats on edges {s[colors[k]]} and "
                    f"{k} (edge cells {e[0]},{e[1]})")
            s[colors[k]] = k

    # D6: the pour point — camera-side, just outside the creature footprint.
    d_hat = np.array([math.sin(CAM_THETA), -math.cos(CAM_THETA)])   # engine camera law
    P = D["centroid_xz"] + POUR_DIST_FACTOR * D["r_body"] * d_hat
    cxz = centers[:, [0, 2]]
    dist_p = np.linalg.norm(cxz - P, axis=1)
    inj_target = int(free[np.argmin(dist_p[free])])

    return {
        "n": n, "n_edges": len(edges_sorted), "n_colors": n_colors,
        "cube_edge": cube_edge, "center_cube": center_cube,
        "centroid_xz": D["centroid_xz"],
        "areas": areas, "bed": bed, "V0": np.zeros(n, dtype=np.int32),
        "occ": occ_mask.astype(np.uint32), "eij": ei, "k_e": k_e, "l_ij": l_ij,
        "edge_active": edge_active, "color_start": color_start.astype(np.uint32),
        "inj": np.zeros((0, 2), dtype=np.uint32),
        "inj_target": inj_target, "pour_point": P,
    }


# ── the composite /mesh_bin POST (cpp_bridge.load_mesh_bin's law, in-memory) ─
def post_composite_mesh(D: dict) -> None:
    import cpp_bridge
    verts = np.ascontiguousarray(D["comp_verts"], dtype=np.float32)
    tris = np.ascontiguousarray(D["comp_tris"], dtype=np.uint32)
    normals = cpp_bridge._mesh_normals(verts, tris)
    colors = np.full((len(verts), 3), (0.8, 0.55, 0.35), dtype=np.float32)  # teddy brown
    colors[D["vert_base"]:] = np.array(FLOOR_COLOR, dtype=np.float32)
    verts9 = np.hstack([verts, normals, colors]).astype(np.float32)
    n, m = len(verts), int(tris.size)
    header = struct.pack("<II4f", n, m, 12.0, 0.0, 0.3, 0.0)
    payload = header + verts9.tobytes() + tris.astype(np.uint32).tobytes()
    st, resp = request("POST", "/mesh_bin", payload, "application/octet-stream",
                       timeout=180)
    ok = b'"ok":true' in resp
    record("load.mesh_composite", "PASS" if ok else "FAIL",
           {"verts": n, "tris": m // 3, "resp": resp[:80].decode("utf-8", "replace")})
    if not ok:
        raise SystemExit("composite mesh rejected — fallback arm required "
                         "(PREREGISTRATION.txt FALLBACK)")


def pack_water_bin(s: dict) -> bytes:
    """v1's /water_bin binary protocol (main.cpp), verbatim."""
    hdr = struct.pack("<4I3d", s["n"], s["n_edges"], s["n_colors"], s["inj"].shape[0],
                      Q, GRAV, C_LOCAL)
    return (hdr
            + s["areas"].astype(np.float64).tobytes()
            + s["bed"].astype(np.float64).tobytes()
            + s["V0"].astype(np.int32).tobytes()
            + s["occ"].astype(np.uint32).tobytes()
            + s["eij"].astype(np.int32).tobytes()
            + s["k_e"].astype(np.float64).tobytes()
            + s["l_ij"].astype(np.float64).tobytes()
            + s["edge_active"].astype(np.uint32).tobytes()
            + s["color_start"].astype(np.uint32).tobytes()
            + s["inj"].astype(np.uint32).tobytes())


def water_readback() -> dict:
    """GET /water_state -> slot 0 (latest V) + the derived truth numbers.

    max_depth is the ledger's own depth law max_i(V_i*Q/A_i) over wet
    cells — the exact quantity the vis plane renders as the pool level
    (g4 compares the RENDERED level against THIS, not against an
    approximation)."""
    try:
        st, raw = request("GET", "/water_state", timeout=120)
        ns, nc = struct.unpack("<2I", raw[:8])
        v = np.frombuffer(raw, dtype=np.int32, count=nc, offset=8)
    except Exception as e:                        # noqa: BLE001 — the failure IS the record
        return {"ok": False, "error": str(e), "sum": None, "wet": None,
                "max": None, "max_depth": None, "wet_centroid_r": None}
    wet = v > 0
    total = int(v.sum())
    # pool radius: wet-centroid distance from the disc centre (spreading metric)
    cxz = ST["centers"][:, [0, 2]]
    cent = cxz[wet].mean(axis=0) if wet.any() else None
    cent_r = float(np.linalg.norm(cent - ST["centroid_xz"])) if cent is not None else None
    max_depth = float((v[wet] * Q / ST["areas"][wet]).max()) if wet.any() else 0.0
    return {"ok": True, "sum": total, "wet": int(wet.sum()),
            "max": int(v.max()), "max_depth": max_depth,
            "wet_centroid_r": cent_r}


def vis_body_readback() -> dict:
    """GET /water_vis_state -> [4 u32 indirect][water verts, 9 f32 each].

    This is the RENDERED BODY, measured: vertex count, level (max Y above
    the floor), planar radius. g3/g4/g5 read this."""
    try:
        st, raw = request("GET", "/water_vis_state", timeout=60)
        indirect = np.frombuffer(raw, dtype=np.uint32, count=4, offset=0)
        nv = int(indirect[0])
        if nv <= 0:
            return {"ok": True, "verts": 0, "level": None, "radius": None, "max_y": None}
        fl = np.frombuffer(raw, dtype=np.float32, count=9 * nv, offset=16)
        pos = fl.reshape(nv, 9)[:, 0:3].astype(np.float64)
        max_y = float(pos[:, 1].max())
        r = float(np.sqrt((pos[:, 0] - ST["centroid_xz"][0]) ** 2
                          + (pos[:, 2] - ST["centroid_xz"][1]) ** 2).max())
        return {"ok": True, "verts": nv, "level": max_y - ST["y_floor"],
                "radius": r, "max_y": max_y}
    except Exception as e:                        # noqa: BLE001 — the failure IS the record
        return {"ok": False, "error": str(e), "verts": 0, "level": None,
                "radius": None, "max_y": None}


def hud_state() -> dict:
    try:
        j = jreq("GET", "/state")
        return j.get("hud", {}).get("water", {})
    except Exception:                              # noqa: BLE001
        return {}


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT_DEFAULT
    frames_dir = out / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    assert MESH_BIN.is_file(), f"missing committed mesh: {MESH_BIN}"
    assert not _port_busy(PORT), f"port {PORT} busy — collision is a named refusal"

    # ── derive everything BEFORE the engine exists (no live exploration) ──
    verts, tris = load_whole_mesh(MESH_BIN)
    D = build_floor_disc(verts, tris)
    global ST
    ST = build_substrate_disc(D)
    pour = ST["centers"][ST["inj_target"]]
    record("derived.basin", "PASS", {
        "y_floor": round(D["y_floor"], 6), "r_body": round(D["r_body"], 4),
        "r_disc": round(D["r_disc"], 4), "cell_size": round(D["cell_size"], 6),
        "n_cells": D["n_cells"], "up_frac": D["up_frac"],
        "tri_base": D["tri_base"], "vert_base": D["vert_base"],
        "composite_verts": len(D["comp_verts"]),
        "composite_tris": len(D["comp_tris"])})
    record("derived.substrate", "PASS", {
        "n_cells": ST["n"], "n_edges": ST["n_edges"], "n_colors": ST["n_colors"],
        "cube_edge": round(ST["cube_edge"], 6),
        "occ_cells": int(ST["occ"].sum()), "center_cube": list(ST["center_cube"]),
        "inj_target": ST["inj_target"],
        "pour_point": [round(float(pour[0]), 4), round(float(pour[1]), 4),
                       round(float(pour[2]), 4)],
        "pour_dist_from_centroid": round(
            float(np.linalg.norm(pour[[0, 2]] - ST["centroid_xz"])), 4)})

    os.environ["CHIMERA_ENGINE_URL"] = BASE
    import cpp_bridge

    old = os.environ.get("CHIMERA_MD_EDGE")
    os.environ.pop("CHIMERA_MD_EDGE", None)
    proc = None
    try:
        exe = ROOT / ".tmp/engine_build/waterroom_v2/Release/chimera_engine.exe"
        assert exe.is_file(), f"missing exe: {exe} (build first: cmake --build . --config Release)"
        proc, _ = _launch(exe, PORT, ROOT / ".tmp/engine_runtime/feature-water-room-v2-01")
        _wait_ready(proc, PORT)
        record("launch", "PASS", {"pid": proc.pid, "port": PORT,
                                  "exe_sha256": hashlib.sha256(exe.read_bytes()).hexdigest()})

        post_composite_mesh(D)

        st, resp = request("POST", "/water_bin", pack_water_bin(ST),
                           "application/octet-stream", timeout=180)
        record("load.water_bin", "PASS" if b'"ok":true' in resp else "FAIL",
               {"resp": resp[:80].decode("utf-8", "replace")})
        st, resp = request("POST", "/water_vis",
                           json.dumps({"on": True, "tri_base": D["tri_base"]}).encode(),
                           timeout=30)
        record("load.water_vis", "PASS" if b'"ok":true' in resp else "FAIL",
               {"tri_base": D["tri_base"]})

        # camera: v1's recorded framing, verbatim (D9)
        extent = 10.0
        try:
            scene = jreq("GET", "/scene")
            body_row = next((row for row in scene.get("rows", []) if row.get("id") == "body"), {})
            extent = float(str(body_row.get("detail", "")).split("r=")[-1].rstrip(",") or 10.0)
        except Exception:                          # noqa: BLE001 — declared fallback
            extent = 10.0
        cam = {"cam_radius": CAM_RADIUS_FACTOR * max(extent, 1.0),
               "cam_theta": CAM_THETA, "cam_phi": CAM_PHI}
        jreq("POST", "/camera", cam)
        record("camera.set", "PASS", {**cam, "extent": extent})

        # arm the clock (config loaded, NOT running): the armed state precedes
        # the take; the tap itself happens mid-capture (D7)
        st, resp = request("POST", "/water_clock", json.dumps({
            "on": False, "steps": STEPS_PER_FRAME, "dt": DT_MACRO,
            "inj_target": ST["inj_target"], "inj_count": INJ_COUNT}).encode(),
            timeout=30)
        record("action.arm", "PASS" if b'"ok":true' in resp else "FAIL",
               {"inj_target": ST["inj_target"], "inj_count": INJ_COUNT,
                "steps_per_frame": STEPS_PER_FRAME, "running": False})

        # ── the take: 10 fps wall-clock capture, two player actions ────────
        truth_frames = set(KEYFRAMES)

        def grab(i: int) -> dict:
            t_grab = time.time()
            stg, png = request("GET", "/glass", timeout=30)
            pg = frames_dir / f"g{i:03d}.png"
            pg.write_bytes(png)
            pf = None
            if i in JUDGE_KEYFRAMES:               # the pixel-clean twin, judge six only
                _stf, png2 = request("GET", "/frame", timeout=30)
                pf = frames_dir / f"c{i:03d}.png"
                pf.write_bytes(png2)
            if i in truth_frames:
                steps_before = int(jreq("GET", "/water_clock")["steps_total"])
                truth = water_readback()
                steps_after = int(jreq("GET", "/water_clock")["steps_total"])
                hud = hud_state()
                body = vis_body_readback()
                steps_total = steps_after
            else:
                truth, hud, body = None, {}, None
                steps_before = steps_after = \
                    int(jreq("GET", "/water_clock")["steps_total"])
                steps_total = steps_after
            return {"i": i, "glass": str(pg), "frame": str(pf) if pf else None,
                    "truth": truth, "body": body, "hud": hud,
                    "steps_total": steps_total,
                    "steps_before": steps_before, "steps_after": steps_after,
                    "dt_wall": round(time.time() - t_grab, 3)}

        take: list[dict] = []
        next_t = time.time()
        pour_off_steps = None
        for i in range(N_FRAMES):
            if i == N_DRY:                          # ── ACTION 1: the tap opens, ON-SCREEN ──
                st, resp = request("POST", "/water_clock", json.dumps({
                    "on": True, "steps": STEPS_PER_FRAME, "dt": DT_MACRO,
                    "inj_target": ST["inj_target"], "inj_count": INJ_COUNT}).encode(),
                    timeout=30)
                record("action.pour_on", "PASS" if b'"ok":true' in resp else "FAIL",
                       {"frame": i})
            if i == N_DRY + N_POUR:                 # ── ACTION 2: the tap closes, ON-SCREEN ──
                st, resp = request("POST", "/water_clock", json.dumps({
                    "on": True, "steps": STEPS_PER_FRAME, "dt": DT_MACRO,
                    "inj_target": -1, "inj_count": 0}).encode(), timeout=30)
                pour_off_steps = int(jreq("GET", "/water_clock")["steps_total"])
                record("action.pour_off", "PASS" if b'"ok":true' in resp else "FAIL",
                       {"frame": i, "steps_total_right_after_off": pour_off_steps})
            take.append(grab(i))
            next_t += 1.0 / FPS                     # 10 Hz wall-clock law
            pause = next_t - time.time()
            if pause > 0:
                time.sleep(pause)

        dts = [t["dt_wall"] for t in take]
        record("pacing.measured", "MEASURED",
               {"frames": len(dts), "mean_grab_s": round(sum(dts) / len(dts), 3),
                "max_grab_s": round(max(dts), 3), "take_wall_s": round(sum(dts), 1),
                "note": "phase boundaries are capture-indexed; gates do not depend on wall pacing"})

        # ── declared gates (PREREGISTRATION.txt g1-g7) ──────────────────────
        kf = {k: take[k] for k in KEYFRAMES}
        t30, t40 = kf[30], kf[40]
        hud30 = t30["hud"]

        record("gate.dry_zero", "PASS" if t30["truth"].get("sum") == 0 else "FAIL",
               {"sum_at_f030": t30["truth"].get("sum"),
                "steps_at_f030": t30["steps_total"]})
        armed_ok = (hud30.get("on") in (False, None)) and t30["steps_total"] == 0
        record("gate.armed_idle", "PASS" if armed_ok else "FAIL",
               {"hud_at_f030": hud30, "steps_at_f030": t30["steps_total"]})
        # live conservation identity, bracket-read (the engine keeps ticking
        # between two reads, so sum is bracketed by inj x the two clock reads:
        # inj*steps_before <= sum(read between) <= inj*steps_after during pour)
        s40 = t40["truth"]
        lo = INJ_COUNT * t40["steps_before"]
        hi = INJ_COUNT * t40["steps_after"]
        ident40 = lo <= s40.get("sum", -1) <= hi
        record("gate.pour_on_screen",
               "PASS" if t40["hud"].get("on") is True
               and t40["steps_total"] > 0 and ident40 else "FAIL",
               {"hud_on_at_f040": t40["hud"].get("on"),
                "steps_before": t40["steps_before"],
                "steps_after": t40["steps_after"], "sum_at_f040": s40.get("sum"),
                "identity_bracket": [lo, hi]})

        for k in KEYFRAMES[2:]:
            b = kf[k]["body"]
            ok3 = b.get("ok") and b.get("verts", 0) > 0 and (b.get("level") or 0) > 0
            record("gate.body_renders", "PASS" if ok3 else "FAIL",
                   {"frame": k, "verts": b.get("verts"), "level": b.get("level"),
                    "radius": b.get("radius")})

        for k in (42, 90, 150, 179, 239):
            b, t = kf[k]["body"], kf[k]["truth"]
            if not (b.get("verts") and t.get("sum") is not None and t.get("sum") > 0):
                record("gate.level_law", "FAIL",
                       {"frame": k, "reason": "missing or dry read",
                        "verts": b.get("verts"), "sum": t.get("sum")})
                continue
            expected = t["max_depth"]                       # ledger law max(V*Q/A)
            measured = b.get("level")                       # rendered max Y - y_floor
            rel = abs(measured - expected) / max(abs(expected), 1e-30)
            record("gate.level_law", "PASS" if rel < LEVEL_REL_TOL else "FAIL",
                   {"frame": k, "level_rendered": measured, "level_ledger": expected,
                    "rel_err": round(rel, 12)})

        prog_frames = (42, 90, 150, 179)
        for a, b_ in zip(prog_frames, prog_frames[1:]):
            ta, tb = kf[a], kf[b_]
            strict = (tb["truth"]["sum"] > ta["truth"]["sum"]
                      and tb["truth"]["wet"] > ta["truth"]["wet"]
                      and tb["body"]["verts"] > ta["body"]["verts"]
                      and tb["body"]["level"] > ta["body"]["level"])
            record("gate.progressive", "PASS" if strict else "FAIL",
                   {"pair": [a, b_],
                    "sum": [ta["truth"]["sum"], tb["truth"]["sum"]],
                    "wet": [ta["truth"]["wet"], tb["truth"]["wet"]],
                    "verts": [ta["body"]["verts"], tb["body"]["verts"]],
                    "level": [ta["body"]["level"], tb["body"]["level"]]})
        f179, f239 = kf[179], kf[239]
        settled = (f239["truth"]["sum"] == f179["truth"]["sum"]
                   and f239["body"]["verts"] >= f179["body"]["verts"]
                   and f239["body"]["level"] >= f179["body"]["level"])
        record("gate.progressive.settled", "PASS" if settled else "FAIL",
               {"pair": [179, 239], "sum_frozen": f239["truth"]["sum"],
                "verts": [f179["body"]["verts"], f239["body"]["verts"]],
                "level": [f179["body"]["level"], f239["body"]["level"]]})

        final_sum = f239["truth"]["sum"]
        expected_total = INJ_COUNT * (pour_off_steps or 0)
        record("gate.pour_footprint",
               "PASS" if final_sum == expected_total and final_sum > 0 else "FAIL",
               {"sum_at_f239": final_sum, "expected": expected_total,
                "steps_total_at_pour_off": pour_off_steps})

        # engine-truth + body table at the keyframes
        with (out / "water_state_keyframes.txt").open("w", encoding="utf-8") as fh:
            fh.write("feature-water-room-v2-01 — engine truth at the declared keyframes\n"
                     "(GET /water_state slot 0 + GET /water_clock + GET /state hud.water\n"
                     "+ GET /water_vis_state rendered-body reads; quanta are integer Q)\n")
            for k in KEYFRAMES:
                t, b, h = kf[k]["truth"], kf[k]["body"], kf[k]["hud"]
                fh.write(f"\nkeyframe f{k:03d}  steps_total={kf[k]['steps_total']}"
                         f"  (bracket {kf[k]['steps_before']}..{kf[k]['steps_after']})\n"
                         f"  sum(V)           = {t.get('sum')}\n"
                         f"  wet cells        = {t.get('wet')} of {ST['n']}\n"
                         f"  max depth quanta = {t.get('max')}\n"
                         f"  max depth law    = {t.get('max_depth')}\n"
                         f"  wet centroid r   = {t.get('wet_centroid_r')}\n"
                         f"  hud.water        = {json.dumps(h)}\n"
                         f"  body verts       = {b.get('verts')}\n"
                         f"  body level       = {b.get('level')}\n"
                         f"  body radius      = {b.get('radius')}\n")

        # the movie (the humanized companion — caption strips composed by
        # Python from engine truth — ships in the proof folder, clearly
        # marked; the judge frames stay clean)
        glass_paths = [t["glass"] for t in take]
        mp4 = cpp_bridge.encode_movie(glass_paths, str(out / "water_room_v2_take.mp4"), fps=FPS)
        record("encode.movie", "PASS",
               {"mp4": mp4, "frames": len(glass_paths),
                "sha256": hashlib.sha256(Path(mp4).read_bytes()).hexdigest()})

        (out / "render_records.json").write_text(
            json.dumps(RECORDS, indent=1, default=str), encoding="utf-8")
        (out / "render_records.txt").write_text(
            "\n".join(f"[{x['verdict']}] {x['name']} {json.dumps(x['detail'], default=str)}"
                      for x in RECORDS) + "\n", encoding="utf-8")

        _stop_owned(proc)
        proc = None
        record("engine.drain", "PASS", {"stopped": True})
        failed = [x for x in RECORDS if x["verdict"] == "FAIL"]
        print(json.dumps({"mp4": str(out / "water_room_v2_take.mp4"),
                          "frames": len(glass_paths), "failed": len(failed)}))
        return 1 if failed else 0
    finally:
        if old is not None:
            os.environ["CHIMERA_MD_EDGE"] = old
        if proc is not None:
            _stop_owned(proc)


if __name__ == "__main__":
    raise SystemExit(main())
