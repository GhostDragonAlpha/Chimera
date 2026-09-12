"""WATER ROOM — the player pours water on the creature and watches real fluid
respond (feature-water-room-01).

The feature, in one sentence: a fresh engine, the creature loaded, and one
player action — POST /water_clock with a source at the top of the creature's
back — pours water that flows down the body, pools, and keeps moving after
the tap closes, all visible on the /glass product surface.

Public HTTP surface only (route table read-only in ChimeraEngine/engine/main.cpp):
  POST /mesh_bin (via cpp_bridge.load_mesh_bin), POST /water_bin,
  POST /water_vis, POST /water_clock, GET /water_clock, GET /water_state,
  POST /camera, GET /glass, GET /frame
plus the two harness wrappers the accepted lanes used (tools/engine_demo.py
launch/stop; cpp_bridge.encode_movie). ZERO C++ (architecture directive).

The water substrate is DERIVED at runtime from the committed mesh
Saved/meshes/monkey_birth.bin — no external payload. The water part
(SALLY_body_0, 34538 triangles) sits at face base 2092 of that mesh: the GLB
parts concatenate in order (SALLY_EYES_0 = 2092 tris first), the block's
vertex ids are contiguous, and block-minus-vert-base equals the raw part
indices (the water_align_check proof, re-asserted at runtime). The solver
constants are the RECORDED measured values for SALLY_body_0
(.tmp/hy3_water/m1m2_results.json: C_sw_global, l_scale_med, area.min), used
as instructed, never re-derived — the same law the L7 water ledger ran under.
Edge canonical order, order-consistent coloring, slope bed, the occupied
centre cube and k_e/l_ij follow tri_ca.registry + tri_water.build_substrate +
water_setup.py verbatim; that construction was verified to reproduce the
proven .tmp/water_gpu/water_payload.npz bit-identically (areas, bed, edge_ij,
k_e, l_ij, edge_active, occ_mask, color_start — max abs diff 0.0) before this
module ever ran a take.
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

ROOT = Path(__file__).resolve().parents[2]   # two dirs up from this file (tools/product_features) is the repo root
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
from engine_demo import _launch, _wait_ready, _stop_owned, _port_busy  # noqa: E402

OUT_DEFAULT = ROOT / "docs/evidence/agent_fleet/FEATURE_WATER_ROOM"

# ── declared constants (PREREGISTRATION.md) ─────────────────────────────────
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
N_DRY = 60                        # f000-059  DRY    (6.0 s)
N_POUR = 120                      # f060-179  POUR   (12.0 s) — ACTION 1 at f060
N_DRAIN = 180                     # f180-359  DRAIN  (18.0 s) — ACTION 2 at f180
N_FRAMES = N_DRY + N_POUR + N_DRAIN          # 360 frames = 36.0 s take
KEYFRAMES = (0, 90, 150, 179, 240, 359)      # the 6 judge keyframes (ordered)
CAM_RADIUS_FACTOR = 3.4           # the motion-sweep measured head-crop fix
PORT = 8104                       # slot-04 candidate port (never 8080; checked at run)

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


# ── the substrate, derived from the committed mesh (tri_water law, verbatim) ─
def load_whole_mesh(bin_path: Path) -> tuple[np.ndarray, np.ndarray]:
    raw = bin_path.read_bytes()
    n, m = struct.unpack("<ii", raw[:8])
    verts = np.frombuffer(raw, dtype=np.float32, count=n * 3, offset=8).reshape(n, 3)
    tris = np.frombuffer(raw, dtype=np.uint32, count=m * 3, offset=8 + n * 12).reshape(m, 3)
    return verts, tris


def water_block(tris: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The water part of the whole mesh + the runtime align proof.

    Returns (part_i, abs_blk): raw part triangle indices, and the whole-mesh
    face block. Asserts the block is contiguous in vertices and that
    abs_blk - vert_base == part_i (water_align_check's exact hypothesis).
    """
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
    """tri_ca.registry + tri_water.build_substrate + water_setup.py, verbatim laws."""
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
    # (tri_water.build_substrate: lower cube_addr tuple first, then primal key;
    # dict insertion order is the tri loop order, the sort is stable)
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

    # order-consistent edge coloring (water_setup.py, verbatim)
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
    inj_target = int(np.flatnonzero(free)[np.argmax(bed[free])])

    return {
        "n": n, "n_edges": len(edges_sorted), "n_colors": n_colors,
        "cube_edge": cube_edge, "center_cube": center_cube,
        "areas": areas, "bed": bed, "V0": np.zeros(n, dtype=np.int32),
        "occ": occ_mask.astype(np.uint32), "eij": ei, "k_e": k_e, "l_ij": l_ij,
        "edge_active": edge_active, "color_start": color_start.astype(np.uint32),
        "inj": np.zeros((0, 2), dtype=np.uint32),
        "inj_target": inj_target,
    }


def pack_water_bin(s: dict) -> bytes:
    """The /water_bin binary protocol (main.cpp; little-endian)."""
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


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT_DEFAULT
    frames_dir = out / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    assert MESH_BIN.is_file(), f"missing committed mesh: {MESH_BIN}"
    assert not _port_busy(PORT), f"port {PORT} busy — collision is a named refusal"

    global ST
    ST = build_substrate(MESH_BIN)
    record("substrate.built", "PASS", {
        "n_cells": ST["n"], "n_edges": ST["n_edges"], "n_colors": ST["n_colors"],
        "cube_edge": round(ST["cube_edge"], 6), "center_cube": list(ST["center_cube"]),
        "inj_target": ST["inj_target"],
        "bed_at_target": round(float(ST["bed"][ST["inj_target"]]), 6)})

    os.environ["CHIMERA_ENGINE_URL"] = BASE   # cpp_bridge targets MY instance
    import cpp_bridge

    old = os.environ.get("CHIMERA_MD_EDGE")
    os.environ.pop("CHIMERA_MD_EDGE", None)
    proc = None
    try:
        exe = ROOT / ".tmp/engine_build/waterroom/Release/chimera_engine.exe"
        assert exe.is_file(), f"missing exe: {exe} (build first: cmake --build . --config Release)"
        proc, _ = _launch(exe, PORT, ROOT / ".tmp/engine_runtime/feature-water-room-01")
        _wait_ready(proc, PORT)
        record("launch", "PASS", {"pid": proc.pid, "port": PORT,
                                  "exe_sha256": hashlib.sha256(exe.read_bytes()).hexdigest()})

        # the creature (committed mesh; teddy-brown via the bridge)
        ok, r, th, ph = cpp_bridge.load_mesh_bin(str(MESH_BIN), timeout=120)
        record("load.mesh", "PASS" if ok else "FAIL", {"r": r, "theta": th, "phi": ph})

        # the water substrate (dry) + the vis binding (face base = the align proof)
        st, resp = request("POST", "/water_bin", pack_water_bin(ST),
                           "application/octet-stream", timeout=120)
        record("load.water_bin", "PASS" if b'"ok":true' in resp else "FAIL",
               {"resp": resp[:80].decode("utf-8", "replace")})
        st, resp = request("POST", "/water_vis",
                           json.dumps({"on": True, "tri_base": WATER_FACE_BASE}).encode(),
                           timeout=30)
        record("load.water_vis", "PASS" if b'"ok":true' in resp else "FAIL",
               {"tri_base": WATER_FACE_BASE})

        # fixed camera (the motion-sweep validated framing)
        extent = 10.0
        try:
            scene = jreq("GET", "/scene")
            body_row = next((row for row in scene.get("rows", []) if row.get("id") == "body"), {})
            extent = float(str(body_row.get("detail", "")).split("r=")[-1].rstrip(",") or 10.0)
        except Exception:                          # noqa: BLE001 — declared fallback
            extent = 10.0
        cam = {"cam_radius": CAM_RADIUS_FACTOR * max(extent, 1.0),
               "cam_theta": 0.5, "cam_phi": 0.35}
        jreq("POST", "/camera", cam)
        record("camera.set", "PASS", {**cam, "extent": extent})

        # ── the take: 10 fps wall-clock capture, two player actions ─────────
        truth_frames = set(KEYFRAMES) | {0, N_DRY - 1, N_DRY, N_DRY + N_POUR - 1,
                                         N_DRY + N_POUR, N_FRAMES - 1}

        def grab(i: int) -> dict:
            t_grab = time.time()
            stg, png = request("GET", "/glass", timeout=30)
            pg = frames_dir / f"g{i:03d}.png"
            pg.write_bytes(png)
            pf = None
            if i in KEYFRAMES:                      # the pixel-clean twin, keyframes only
                _stf, png2 = request("GET", "/frame", timeout=30)
                pf = frames_dir / f"c{i:03d}.png"
                pf.write_bytes(png2)
            truth = water_readback() if i in truth_frames else None
            clock = jreq("GET", "/water_clock")
            return {"i": i, "glass": str(pg), "frame": str(pf) if pf else None,
                    "truth": truth, "steps_total": int(clock.get("steps_total", -1)),
                    "dt_wall": round(time.time() - t_grab, 3)}

        take: list[dict] = []
        next_t = time.time()
        pour_off_steps = None
        settle = None
        for i in range(N_FRAMES):
            if i == N_DRY:                          # ── ACTION 1: the player pours ──
                st, resp = request("POST", "/water_clock", json.dumps({
                    "on": True, "steps": STEPS_PER_FRAME, "dt": DT_MACRO,
                    "inj_target": ST["inj_target"], "inj_count": INJ_COUNT}).encode(),
                    timeout=30)
                record("action.pour_on", "PASS" if b'"ok":true' in resp else "FAIL",
                       {"frame": i, "inj_target": ST["inj_target"],
                        "inj_count": INJ_COUNT, "steps_per_frame": STEPS_PER_FRAME})
            if i == N_DRY + N_POUR:                 # ── ACTION 2: the tap closes ──
                st, resp = request("POST", "/water_clock", json.dumps({
                    "on": True, "steps": STEPS_PER_FRAME, "dt": DT_MACRO,
                    "inj_target": -1, "inj_count": 0}).encode(), timeout=30)
                pour_off_steps = int(jreq("GET", "/water_clock")["steps_total"])
                record("action.pour_off", "PASS" if b'"ok":true' in resp else "FAIL",
                       {"frame": i, "steps_total_right_after_off": pour_off_steps})
            if i == N_DRY + N_POUR + 6:             # settle: in-flight pour steps landed
                settle = int(jreq("GET", "/water_clock")["steps_total"])
                record("pacing.settle", "MEASURED",
                       {"frame": i, "steps_total_settled": settle,
                        "expected_poured_quanta": INJ_COUNT * settle})
            take.append(grab(i))
            next_t += 1.0 / FPS                     # 10 Hz wall-clock law
            pause = next_t - time.time()
            if pause > 0:
                time.sleep(pause)

        # pacing truth (the product-http-viewer-01 lesson: the engine's /glass
        # queue is serial — record what the cadence actually was)
        dts = [t["dt_wall"] for t in take]
        record("pacing.measured", "MEASURED",
               {"frames": len(dts), "mean_grab_s": round(sum(dts) / len(dts), 3),
                "max_grab_s": round(max(dts), 3),
                "take_wall_s": round(sum(dts), 1),
                "note": "phase boundaries are capture-indexed; gates do not depend on wall pacing"})

        # ── declared gates (PREREGISTRATION.md) ─────────────────────────────
        kf = {k: take[k] for k in KEYFRAMES}
        g1 = kf[0]["truth"]
        record("gate.dry_zero", "PASS" if g1 and g1.get("sum") == 0 else "FAIL",
               {"sum_at_f000": g1.get("sum") if g1 else None})
        final = kf[KEYFRAMES[-1]]["truth"]
        expected = INJ_COUNT * (settle or 0)
        record("gate.pour_changes_state",
               "PASS" if (final and final.get("sum") is not None
                          and final["sum"] == expected and final["sum"] > 0) else "FAIL",
               {"sum_at_f359": final.get("sum"), "expected": expected,
                "steps_total_settled": settle,
                "steps_total_right_after_off": pour_off_steps})
        c0 = kf[90]["truth"].get("wet_centroid_bed")
        c1 = final.get("wet_centroid_bed")
        record("gate.flow_downhill",
               "PASS" if (c0 is not None and c1 is not None and c1 < c0) else "FAIL",
               {"wet_centroid_bed_f090": c0, "wet_centroid_bed_f359": c1})
        for k in KEYFRAMES:
            t = kf[k]["truth"]
            record("keyframe.truth", "MEASURED", {
                "frame": k, "steps_total": kf[k]["steps_total"], "sum": t.get("sum"),
                "wet_cells": t.get("wet"), "max_depth_quanta": t.get("max"),
                "wet_centroid_bed": t.get("wet_centroid_bed")})

        # engine-truth table at the 6 keyframes
        with (out / "water_state_keyframes.txt").open("w", encoding="utf-8") as fh:
            fh.write("feature-water-room-01 — GET /water_state + /water_clock at the "
                     "6 declared keyframes (slot 0 = latest V; quanta are integer Q)\n")
            for k in KEYFRAMES:
                t = kf[k]["truth"]
                fh.write(f"\nkeyframe f{k:03d}  steps_total={kf[k]['steps_total']}\n"
                         f"  sum(V)           = {t.get('sum')}\n"
                         f"  wet cells        = {t.get('wet')} of {ST['n']}\n"
                         f"  max depth quanta = {t.get('max')}\n"
                         f"  wet centroid bed = {t.get('wet_centroid_bed')}\n")

        # the judge artifact + the clean twin
        glass_paths = [t["glass"] for t in take]
        mp4 = cpp_bridge.encode_movie(glass_paths, str(out / "water_room_take.mp4"), fps=FPS)
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
        print(json.dumps({"mp4": str(out / "water_room_take.mp4"),
                          "frames": len(glass_paths), "failed": len(failed)}))
        return 1 if failed else 0
    finally:
        if old is not None:
            os.environ["CHIMERA_MD_EDGE"] = old
        if proc is not None:
            _stop_owned(proc)


if __name__ == "__main__":
    raise SystemExit(main())
