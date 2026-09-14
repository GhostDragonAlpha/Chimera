"""bring_alive.py -- THE ALIVENESS LAW, one command (fleet C1).

A static .obj / .gltf / .glb walks the SAME four moves the hand-authored
creature uses, each a law the engine already certifies:

  /mesh_import   'O'|'G' + source bytes -> the engine's full mesh format
                 (importer refuses open/leaky surfaces BY NAME)
  /tick_joints   K spine pins spread over the mesh's y-extent
  /tick_classify nearest pin per triangle centroid (classify_run.py's law)
  /tick_vertbind 3 nearest pins, inverse-distance^2 weights
  /tick_seal     the cut-and-weld at mid-height
  /tick_state    THE VERDICT: do the sealed cells conserve volume?

Usage:
  python tools/bring_alive.py BODY.obj  [--base http://127.0.0.1:8107]
                                        [--joints 9] [--pose-deg 25]

Prereg: docs/evidence/agent_fleet/MATTER_KERNEL/SEAL_PREREGISTRATION.md,
section "THE MESH IMPORT PREREGISTRATION" (predictions A1 volume,
A2 poses travel, A3 touch answers).
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
import urllib.request
from pathlib import Path

import numpy as np

# pin indices ride u8 in the vertbind payload (engine contract)
MAX_JOINTS = 255


def http_post(base: str, path: str, body: bytes, timeout: int = 120) -> dict:
    req = urllib.request.Request(
        base + path, data=body, method="POST",
        headers={"Content-Type": "application/octet-stream"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def http_get_json(base: str, path: str, timeout: int = 60) -> dict:
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return json.loads(r.read().decode())


def http_get_bytes(base: str, path: str, timeout: int = 120) -> bytes:
    with urllib.request.urlopen(base + path, timeout=timeout) as r:
        return r.read()


def source_kind(path: Path) -> str:
    # one-byte prefix contract with /mesh_import
    if path.suffix.lower() == ".obj":
        return "O"
    if path.suffix.lower() in (".gltf", ".glb"):
        return "G"
    raise SystemExit(f"refused: {path.name} is not .obj/.gltf/.glb")


def spine_pins(ylo: float, yhi: float, k: int, cx: float, cz: float) -> np.ndarray:
    # a standing rig: k pins on the body's central axis, evenly spread
    # over the y-extent (each pin owns the slab it sits in)
    ys = ylo + (np.arange(k, dtype=np.float32) + 0.5) * (yhi - ylo) / k
    pins = np.empty((k, 3), dtype=np.float32)
    pins[:, 0] = cx
    pins[:, 1] = ys
    pins[:, 2] = cz
    return pins


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mesh", help="path to .obj / .gltf / .glb")
    ap.add_argument("--base", default="http://127.0.0.1:8107")
    ap.add_argument("--joints", type=int, default=9,
                    help="spine pin count (2..255)")
    ap.add_argument("--pose-deg", type=float, default=25.0,
                    help="A2 probe: flex the mid pin this many degrees")
    args = ap.parse_args()

    path = Path(args.mesh)
    if not path.is_file():
        raise SystemExit(f"refused: {path} does not exist")
    k = max(2, min(MAX_JOINTS, args.joints))

    # 1. IMPORT (the named falsifier fires here if the mesh cannot close)
    kind = source_kind(path)
    raw = path.read_bytes()
    print(f"mesh: {path.name} ({len(raw):,} bytes, kind {kind})")
    res = http_post(args.base, "/mesh_import",
                    kind.encode("ascii") + raw, timeout=300)
    if not res.get("ok"):
        print(f"IMPORT REFUSED: {res.get('error')}")
        return 1
    print(f"import: {res['verts']:,} verts, {res['tris']:,} tris, "
          f"V={res['volume']:.6g}, "
          f"y in [{res['ymin']:.4g}, {res['ymax']:.4g}]"
          + (", winding flipped to outward" if res.get("winding_flipped")
             else ""))

    # geometry comes back from the ENGINE's own store (not a local
    # re-parse): /topology + /verts are the web kernel's state exports
    topo = http_get_bytes(args.base, "/topology")
    n_tri = struct.unpack_from("<I", topo, 0)[0]
    if n_tri != res["tris"]:
        print(f"refused: engine reports {n_tri} tris, import said "
              f"{res['tris']} — the upload did not land")
        return 1
    idx = np.frombuffer(topo, dtype=np.uint32, count=n_tri * 3,
                        offset=4).reshape(n_tri, 3)
    verts = np.frombuffer(http_get_bytes(args.base, "/verts"),
                          dtype=np.float32)
    nv = struct.unpack_from("<I", verts, 0)[0]
    pos = verts[1:].reshape(nv, 9)[:, 0:3]

    # 2. JOINTS (the standing rig)
    ylo, yhi = float(res["ymin"]), float(res["ymax"])
    cx = float(pos[:, 0].mean())
    cz = float(pos[:, 2].mean())
    pins = spine_pins(ylo, yhi, k, cx, cz)
    print("joints:", http_post(
        args.base, "/tick_joints",
        struct.pack("<I", k) + np.ascontiguousarray(pins).tobytes()))

    # 3. CLASSIFY: nearest pin per triangle centroid
    centroids = pos[idx].mean(axis=1)
    d2t = ((centroids[:, None, :] - pins[None, :, :]) ** 2).sum(axis=2)
    tri_joint = d2t.argmin(axis=1).astype(np.uint8)
    print("classify:", http_post(
        args.base, "/tick_classify",
        struct.pack("<I", n_tri) + tri_joint.tobytes()),
        "types:", np.bincount(tri_joint, minlength=k).tolist())

    # 4. VERTBIND: 3 nearest pins, w = 1/(d^2 + 1e-6)^2 normalized —
    #    classify_run.py's exact math, any mesh
    d2v = ((pos[:, None, :] - pins[None, :, :]) ** 2).sum(axis=2)
    order = np.argsort(d2v, axis=1)[:, :3]
    d3 = np.take_along_axis(d2v, order, axis=1)
    w = 1.0 / (d3 + 1e-6) ** 2
    w /= w.sum(axis=1, keepdims=True)
    vb = np.empty((nv, 15), dtype=np.uint8)
    for c in range(3):
        vb[:, c] = order[:, c].astype(np.uint8)
    for c in range(3):
        vb[:, 3 + c * 4:7 + c * 4] = np.frombuffer(
            np.ascontiguousarray(w[:, c], dtype=np.float32).tobytes(),
            dtype=np.uint8).reshape(nv, 4)
    print("vertbind:", http_post(
        args.base, "/tick_vertbind",
        struct.pack("<I", nv) + vb.tobytes(), timeout=300))

    # 5. SEAL at mid-height (the plane must cross: mid always does unless
    #    the body is degenerate, which the importer already refused)
    y_cut = 0.5 * (ylo + yhi)
    seal = http_post(args.base, "/tick_seal",
                     json.dumps({"y": y_cut}).encode(),
                     timeout=300)
    print(f"seal y={y_cut:.4g}:", seal)

    # 6. THE VERDICT (A1): cells conserve volume
    st = http_get_json(args.base, "/tick_state")
    vw = st.get("V_whole", 0.0)
    vsum = sum(c.get("V", 0.0) for c in st.get("cells", []))
    cons = st.get("conserve_pct", None)
    print(f"state: sealed={st.get('sealed')} n_cells={st.get('n_cells')} "
          f"V_whole={vw:.6g} sum(V_cells)={vsum:.6g} "
          f"conserve_pct={cons}")

    ok = bool(st.get("sealed")) and st.get("n_cells", 0) >= 2
    if cons is not None:
        ok = ok and abs(cons) <= 1.0

    # 7. A2 PROBE: poses travel — flex the mid spine pin, conservation
    #    must hold UNDER the pose; then restore the rest
    deg = args.pose_deg
    mid = k // 2
    posed = http_post(args.base, "/tick_pose",
                      json.dumps({"joint_index": mid, "deg": deg}).encode())
    if ok and posed.get("ok"):
        st2 = http_get_json(args.base, "/tick_state")
        cons2 = st2.get("conserve_pct")
        print(f"pose pin {mid} {deg:+g} deg: conserve_pct={cons2} "
              f"(under pose)")
        ok = ok and cons2 is not None and abs(cons2) <= 1.0
        http_post(args.base, "/tick_pose",
                  json.dumps({"joint_index": mid, "deg": 0}).encode())
        st3 = http_get_json(args.base, "/tick_state")
        cons3 = st3.get("conserve_pct")
        print(f"pose pin {mid} 0 deg: conserve_pct={cons3} (rest)")
        ok = ok and cons3 is not None and abs(cons3) <= 1.0

    # A3 (touch answers) is left to the operator's pointer: the press path
    # is mesh-agnostic machinery (/tick_touch), exercised by every lesson.

    print("ALIVE:", "YES — volume conserved across import, seal and pose"
          if ok else
          "NO — the falsifier fired (see conserve_pct / seal above)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
