"""WATER ROOM v2 — water as a visible BODY with a rising level
(feature-water-room-v2-01, AMENDMENT 1 delivery arm).

The v1 blind judge CONFIRMED the simulation runs but wrote the v2 spec
verbatim: "The only visible evidence of water is a small blue patch at the
neck - there is no water surface, pool, or rising level on the floor or in
the room"; the pour start happened off-screen; spreading was not obviously
progressive between keyframes; the injection readout is cryptic.

v2's delivery (ALL PYTHON, ZERO C++ — the engine service is frozen):

  v1 poured at the TOP cell (argmax bed), so the water formed a cap at the
  head/neck — a stain with nowhere to go. v2 pours at the LOWEST cell
  (argmin bed — the creature's ground-contact point): the pool fills the
  ground basin and the surface CLIMBS the legs — a rising level on the
  creature (the spec's "and/or a surface over the creature"). The pour
  tap opens and closes ON-SCREEN (capture-indexed keyframes straddle both
  actions), and the judge six keyframes are spaced so every consecutive
  pair shows unambiguous progression.

Run 1 (the flat-disc floor-basin arm, PREREGISTRATION.txt D1-D11) measured
the frozen solver's stability envelope honestly: on a wide thin flat pool
the CFL sub-step dt_ij = c_local*l_ij/c exceeds dt_macro, n_sub floors to
1, the q_e momentum accumulator pumps the quantum grain and cells wrap
int32 (sum -1.27e14 vs the exact 26,184,000). That arm is RETIRED as the
recorded engine-service gap (failed_run_1_disc/); Amendment 1 moved the
delivery to THIS arm — the v1-proven conserved substrate, verbatim laws.

Public HTTP surface only:
  POST /mesh_bin (via cpp_bridge.load_mesh_bin), POST /water_bin,
  POST /water_vis, POST /water_clock, GET /water_clock, GET /water_state,
  GET /state, GET /water_vis_state, POST /camera, GET /glass, GET /frame
plus the two harness wrappers (tools/engine_demo.py launch/stop;
cpp_bridge.encode_movie). Substrate laws are v1's
(tools/product_features/water_room.py) VERBATIM — the recorded constants
were measured with them (provenance asserted at runtime against v1's
recorded substrate numbers); the ONLY change is the pour cell
(argmin bed, PREREGISTRATION.txt Amendment 1).

Preregistration: docs/evidence/agent_fleet/FEATURE_WATER_ROOM_V2/
PREREGISTRATION.txt (RULE 0 committed before any run; Amendment 1
disclosed with run 1's failed evidence retained).
"""
from __future__ import annotations

import hashlib
import json
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
WATER_FACE_BASE = 2092            # glTF part order: SALLY_EYES_0 (2092 tris) first
WATER_TRI_COUNT = 34538           # SALLY_body_0 triangles = water cells
WATER_VERT_COUNT = 17409          # contiguous vertex span of the part
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
N_DRY = 40                        # f000-039  DRY+idle   (4.0 s)
N_POUR = 140                      # f040-179 POUR       — ACTION 1 at f040
N_SETTLE = 60                     # f180-239 SETTLE     — ACTION 2 at f180
N_FRAMES = N_DRY + N_POUR + N_SETTLE          # 240 frames = 24.0 s take
KEYFRAMES = (30, 40, 42, 90, 150, 179, 239)   # engine-truth keyframes
JUDGE_KEYFRAMES = (30, 40, 42, 90, 150, 239)  # the ordered judge six (D8)
CAM_RADIUS_FACTOR = 3.4           # v1 recorded framing (motion-sweep fix)
CAM_THETA, CAM_PHI = 0.5, 0.35    # v1 recorded camera
LEVEL_REL_TOL = 1e-5              # (rendered-level tolerance; see vis route cap)
PORT = 8103                       # slot-03 candidate port (never 8080; checked at run)

# v1's recorded substrate numbers (provenance binding for the verbatim law)
V1_RECORDED = {"n": 34538, "n_edges": 51711, "n_colors": 63,
               "cube_edge": 9.904747, "inj_target_argmax": 446}

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


# ── the substrate, derived from the committed mesh (v1 laws, VERBATIM) ──────
def load_whole_mesh(bin_path: Path) -> tuple[np.ndarray, np.ndarray]:
    raw = bin_path.read_bytes()
    n, m = struct.unpack("<ii", raw[:8])
    verts = np.frombuffer(raw, dtype=np.float32, count=n * 3, offset=8).reshape(n, 3)
    tris = np.frombuffer(raw, dtype=np.uint32, count=m * 3, offset=8 + n * 12).reshape(m, 3)
    return verts, tris


def water_block(tris: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The water part of the whole mesh + the runtime align proof (v1 verbatim)."""
    abs_blk = tris[WATER_FACE_BASE:WATER_FACE_BASE + WATER_TRI_COUNT].astype(np.int64)
    vert_base = int(abs_blk.min())
    part_i = abs_blk - vert_base
    span = sorted(np.unique(abs_blk).tolist())
    contiguous = span == list(range(vert_base, vert_base + WATER_VERT_COUNT))
    if not contiguous or int(part_i.max()) != WATER_VERT_COUNT - 1:
        raise SystemExit(f"align proof FAILED: water face block not contiguous "
                         f"(vert_base={vert_base}, span={span[0]}..{span[-1]})")
    return part_i, abs_blk


def build_substrate(bin_path: Path) -> dict:
    """tri_ca.registry + tri_water.build_substrate + water_setup.py, VERBATIM
    (v1's tools/product_features/water_room.py, byte-same laws — the recorded
    constants were measured with exactly this construction; the ONLY change
    is the pour cell below, declared in Amendment 1)."""
    verts, tris = load_whole_mesh(bin_path)
    part_i, abs_blk = water_block(tris)
    vert_base = int(abs_blk.min())
    part_v = verts[vert_base:vert_base + WATER_VERT_COUNT].astype(np.float64)

    n = len(part_i)
    centers = part_v[part_i].mean(axis=1)

    # dual adjacency (tri_ca.registry: seen-set over primal keys, insertion order)
    seen: set[tuple[int, int]] = set()
    adj: list[list[int]] = [[] for _ in range(n)]
    max_d = 0.0
    for t, tri in enumerate(part_i):
        a, b, c = int(tri[0]), int(tri[1]), int(tri[2])
        for u, w in ((a, b), (b, c), (c, a)):
            key = (t, u) if t < u else (u, t)
            if key in seen:
                continue
            seen.add(key)
            adj[t].append(u)
            adj[u].append(t)
            d = float(np.linalg.norm(centers[t] - centers[u]))
            if d > max_d:
                max_d = d
    cube_edge = max_d                 # the tight in-ring bound (registry law)
    cube_addr = np.floor(centers / cube_edge).astype(np.int64)

    # dual edges: exactly-two-triangle primal edges, canonical order
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
        if tuple(cube_addr[t0]) <= tuple(cube_addr[t1]):
            i0, i1 = t0, t1
        else:
            i0, i1 = t1, t0
        edges.append((i0, i1, l_ij, edge_len, tuple(cube_addr[i0]), (pv0, pv1)))
    edges.sort(key=lambda e: (e[4], e[5]))

    areas = 0.5 * np.linalg.norm(np.cross(part_v[part_i[:, 1]] - part_v[part_i[:, 0]],
                                          part_v[part_i[:, 2]] - part_v[part_i[:, 0]]),
                                 axis=1).astype(np.float64)

    # order-consistent edge coloring (water_setup.py, verbatim — v1's exact rule)
    cell_colors: list[set[int]] = [set() for _ in range(n)]
    colors = np.zeros(len(edges), dtype=np.int32)
    for k, e in enumerate(edges):
        c = 1 + max([0] + [colors[k2] for k2 in cell_colors[e[0]] | cell_colors[e[1]]])
        colors[k] = c
        cell_colors[e[0]].add(k)
        cell_colors[e[1]].add(k)
    n_colors = int(colors.max())
    order = np.lexsort((np.arange(len(edges)), colors))
    edges_sorted = [edges[k] for k in order]
    sorted_colors = colors[order]
    color_start = np.zeros(n_colors + 1, dtype=np.int64)
    for c in range(1, n_colors + 1):
        color_start[c] = int(np.searchsorted(sorted_colors, c, side="right"))

    # slope bed + the occupied centre cube (water_setup.py, verbatim)
    downhill = np.array([0.0, 1.0, 0.0])
    bed = ALPHA * (centers @ downhill)
    mesh_center = centers.mean(axis=0)
    center_cube = tuple(np.floor(mesh_center / cube_edge).astype(np.int64))
    occ_mask = np.array([tuple(cube_addr[t]) == center_cube for t in range(n)], dtype=bool)
    ei = np.array([[e[0], e[1]] for e in edges_sorted], dtype=np.int32)
    l_ij = np.array([e[2] for e in edges_sorted], dtype=np.float64)
    k_e = np.array([GRAV * (e[3] * L_PART) / e[2] for e in edges_sorted], dtype=np.float64)
    edge_active = np.array([(not occ_mask[e[0]]) and (not occ_mask[e[1]])
                            for e in edges_sorted], dtype=np.uint32)

    free = (~occ_mask) & (areas > 0)
    inj_argmax = int(np.flatnonzero(free)[np.argmax(bed[free])])   # v1's recorded pour

    # ── THE v2 CHANGE (Amendment 1): pour at the LOWEST free cell ──────────
    inj_target = int(np.flatnonzero(free)[np.argmin(bed[free])])

    return {
        "n": n, "n_edges": len(edges_sorted), "n_colors": n_colors,
        "cube_edge": cube_edge, "center_cube": center_cube,
        "areas": areas, "bed": bed, "V0": np.zeros(n, dtype=np.int32),
        "occ": occ_mask.astype(np.uint32), "eij": ei, "k_e": k_e, "l_ij": l_ij,
        "edge_active": edge_active, "color_start": color_start.astype(np.uint32),
        "inj": np.zeros((0, 2), dtype=np.uint32),
        "inj_target": inj_target, "inj_argmax": inj_argmax,
        "centers": centers,
    }


def pack_water_bin(s: dict) -> bytes:
    """The /water_bin binary protocol (main.cpp; little-endian). v1 verbatim."""
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
    """GET /water_state -> slot 0 (latest V) + the derived truth numbers."""
    try:
        st, raw = request("GET", "/water_state", timeout=120)
        ns, nc = struct.unpack("<2I", raw[:8])
        v = np.frombuffer(raw, dtype=np.int32, count=nc, offset=8)
    except Exception as e:                        # noqa: BLE001 — the failure IS the record
        return {"ok": False, "error": str(e), "sum": None, "wet": None,
                "max": None, "wet_centroid_bed": None}
    wet = v > 0
    bed = ST["bed"]
    total = int(v.sum())
    cent_bed = float((bed[wet] * v[wet]).sum() / total) if total > 0 else None
    return {"ok": True, "sum": total, "wet": int(wet.sum()),
            "max": int(v.max()), "wet_centroid_bed": cent_bed}


def vis_vertex_count() -> dict:
    """GET /water_vis_state -> the indirect counts ONLY.

    The frozen debug route is CAPPED at 512 floats (water_vis_debug(states,
    512)) — full vertex positions are unreadable, so the rendered-body
    identity is carried by indirect[0] (vertexCount; water_vis.comp emits
    exactly 3 verts per wet cell)."""
    try:
        st, raw = request("GET", "/water_vis_state", timeout=60)
        indirect = struct.unpack("<4I", raw[:16])
        return {"ok": True, "verts": int(indirect[0]),
                "instances": int(indirect[1])}
    except Exception as e:                        # noqa: BLE001 — the failure IS the record
        return {"ok": False, "error": str(e), "verts": None}


def hud_water_state() -> dict:
    try:
        j = jreq("GET", "/state")
        return j.get("water", {})          # top-level "water" (main.cpp /state)
    except Exception:                      # noqa: BLE001
        return {}


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT_DEFAULT
    frames_dir = out / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    assert MESH_BIN.is_file(), f"missing committed mesh: {MESH_BIN}"
    assert not _port_busy(PORT), f"port {PORT} busy — collision is a named refusal"

    # ── derive the substrate BEFORE the engine exists (no live exploration) ─
    global ST
    ST = build_substrate(MESH_BIN)
    # provenance binding: the substrate construction must reproduce v1's
    # recorded numbers (the constants were measured on THIS construction)
    prov_ok = (ST["n"] == V1_RECORDED["n"] and ST["n_edges"] == V1_RECORDED["n_edges"]
               and ST["n_colors"] == V1_RECORDED["n_colors"]
               and abs(ST["cube_edge"] - V1_RECORDED["cube_edge"]) < 1e-3
               and ST["inj_argmax"] == V1_RECORDED["inj_target_argmax"])
    lowest_y = float(ST["bed"][ST["inj_target"]]) / ALPHA
    pour = ST["centers"][ST["inj_target"]]
    record("derived.substrate", "PASS" if prov_ok else "FAIL", {
        "n_cells": ST["n"], "n_edges": ST["n_edges"], "n_colors": ST["n_colors"],
        "cube_edge": round(ST["cube_edge"], 6), "center_cube": list(ST["center_cube"]),
        "v1_provenance": prov_ok,
        "v1_argmax_cell": ST["inj_argmax"],
        "v2_pour_cell_argmin": ST["inj_target"],
        "pour_point": [round(float(pour[0]), 4), round(float(pour[1]), 4),
                       round(float(pour[2]), 4)],
        "pour_height_y": round(lowest_y, 6)})
    if not prov_ok:
        raise SystemExit("substrate provenance binding FAILED — not the v1-proven "
                         "construction; refusing to run (Amendment 1 delivery arm)")

    os.environ["CHIMERA_ENGINE_URL"] = BASE   # cpp_bridge targets MY instance
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

        # the creature (committed mesh; the v1-proven wrapper: teddy colors,
        # area-weighted normals, camera from extent)
        ok, r, th, ph = cpp_bridge.load_mesh_bin(str(MESH_BIN), timeout=120)
        record("load.mesh", "PASS" if ok else "FAIL", {"r": r, "theta": th, "phi": ph})

        # the water substrate (dry) + the vis binding (face base = align proof)
        st, resp = request("POST", "/water_bin", pack_water_bin(ST),
                           "application/octet-stream", timeout=120)
        record("load.water_bin", "PASS" if b'"ok":true' in resp else "FAIL",
               {"resp": resp[:80].decode("utf-8", "replace")})
        st, resp = request("POST", "/water_vis",
                           json.dumps({"on": True, "tri_base": WATER_FACE_BASE}).encode(),
                           timeout=30)
        record("load.water_vis", "PASS" if b'"ok":true' in resp else "FAIL",
               {"tri_base": WATER_FACE_BASE})

        # fixed camera (the v1 recorded framing; extent read live as v1 did)
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
                hud = hud_water_state()
                body = vis_vertex_count()
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

        # ── declared gates (PREREGISTRATION.txt Amendment 1, g1-g7) ─────────
        kf = {k: take[k] for k in KEYFRAMES}
        t30, t40 = kf[30], kf[40]

        record("gate.dry_zero", "PASS" if t30["truth"].get("sum") == 0 else "FAIL",
               {"sum_at_f030": t30["truth"].get("sum"),
                "steps_at_f030": t30["steps_total"]})
        armed_ok = (t30["hud"].get("on") in (False, None)) and t30["steps_total"] == 0
        record("gate.armed_idle", "PASS" if armed_ok else "FAIL",
               {"hud_at_f030": t30["hud"], "steps_at_f030": t30["steps_total"]})
        # live conservation identity, bracket-read (the engine keeps ticking
        # between the two clock reads, so sum is bracketed by inj x them)
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

        # g3 vis_identity: rendered vertexCount == 3 x wet cells (the vis plane
        # emits exactly 3 verts per wet cell — the body IS the ledger's)
        for k in (42, 90, 150, 179, 239):
            b, t = kf[k]["body"], kf[k]["truth"]
            if not (b.get("ok") and t.get("sum") is not None and t.get("sum") > 0):
                record("gate.vis_identity", "FAIL",
                       {"frame": k, "reason": "missing or dry read",
                        "verts": b.get("verts"), "sum": t.get("sum")})
                continue
            expected = 3 * t["wet"]
            record("gate.vis_identity",
                   "PASS" if b.get("verts") == expected else "FAIL",
                   {"frame": k, "verts": b.get("verts"), "expected_3x_wet": expected})

        # g4 pool_rises: the wet-centroid bed CLIMBS across the pour pairs
        # (the level rising from the ground-contact point — Amendment 1)
        prog_pairs = [(42, 90), (90, 150), (150, 179)]
        for a, b_ in prog_pairs:
            ca, cb = kf[a]["truth"].get("wet_centroid_bed"), kf[b_]["truth"].get("wet_centroid_bed")
            record("gate.pool_rises",
                   "PASS" if (ca is not None and cb is not None and cb > ca) else "FAIL",
                   {"pair": [a, b_], "centroid_bed": [ca, cb]})

        # g5 progressive: sum, wet, verts strictly increase on pour pairs
        for a, b_ in prog_pairs:
            ta, tb = kf[a]["truth"], kf[b_]["truth"]
            strict = (tb["sum"] > ta["sum"] and tb["wet"] > ta["wet"]
                      and kf[b_]["body"]["verts"] > kf[a]["body"]["verts"])
            record("gate.progressive", "PASS" if strict else "FAIL",
                   {"pair": [a, b_],
                    "sum": [ta["sum"], tb["sum"]],
                    "wet": [ta["wet"], tb["wet"]],
                    "verts": [kf[a]["body"]["verts"], kf[b_]["body"]["verts"]]})
        f179, f239 = kf[179], kf[239]
        settled = (f239["truth"]["sum"] == f179["truth"]["sum"]
                   and f239["truth"]["wet"] >= f179["truth"]["wet"]
                   and f239["body"]["verts"] >= f179["body"]["verts"])
        record("gate.progressive.settled", "PASS" if settled else "FAIL",
               {"pair": [179, 239], "sum_frozen": f239["truth"]["sum"],
                "wet": [f179["truth"]["wet"], f239["truth"]["wet"]],
                "verts": [f179["body"]["verts"], f239["body"]["verts"]]})

        # g6 pour footprint (the v1-corrected identity)
        final_sum = f239["truth"]["sum"]
        expected_total = INJ_COUNT * (pour_off_steps or 0)
        record("gate.pour_footprint",
               "PASS" if final_sum == expected_total and final_sum > 0 else "FAIL",
               {"sum_at_f239": final_sum, "expected": expected_total,
                "steps_total_at_pour_off": pour_off_steps})

        # engine-truth + body table at the keyframes
        with (out / "water_state_keyframes.txt").open("w", encoding="utf-8") as fh:
            fh.write("feature-water-room-v2-01 (run 2, creature arm) — engine truth at "
                     "the declared keyframes\n(GET /water_state slot 0 + GET /water_clock "
                     "+ GET /state water + GET /water_vis_state indirect;\nquanta are "
                     "integer Q; pour cell = argmin bed = the ground-contact point)\n")
            for k in KEYFRAMES:
                t, b, h = kf[k]["truth"], kf[k]["body"], kf[k]["hud"]
                fh.write(f"\nkeyframe f{k:03d}  steps_total={kf[k]['steps_total']}"
                         f"  (bracket {kf[k]['steps_before']}..{kf[k]['steps_after']})\n"
                         f"  sum(V)           = {t.get('sum')}\n"
                         f"  wet cells        = {t.get('wet')} of {ST['n']}\n"
                         f"  max depth quanta = {t.get('max')}\n"
                         f"  wet centroid bed = {t.get('wet_centroid_bed')}\n"
                         f"  hud.water        = {json.dumps(h)}\n"
                         f"  vis vertexCount  = {b.get('verts')}\n")

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
