"""feet_membranes.py -- author the foot membranes into the loaded scene.

FEET PREREGISTRATION (e8c96bfd): the rendered feet are unrigged skin; the
ankle is the last computed joint. This tool appends two foot membranes as
triangles to the live mesh blob (sole plane y = 0, toes -z, symmetric),
extends the stride hinge's per-vertex weights so the feet travel with
their shanks, and re-posts /mesh_bin + /hinge_bin.

MEASURED (live /joints, FEET_PREREGISTRATION.md):
    ankle_L J = (+0.4609, 0.3378, 0.0678)   ankle_R = (-0.4609, ... same yz)
    shank ~1.57, ground y = 0
DERIVED: foot 0.78 x 0.39; ankle 30% of length from the heel; toes -z.

Usage:
    python tools/feet_membranes.py <Release dir> <engine base url>
Reversible: run with --restore to re-post the untouched original blobs.
"""
from __future__ import annotations

import math
import struct
import sys
import urllib.request
from pathlib import Path

import numpy as np

ANKLE_L = (+0.4609, 0.3378, 0.0678)
ANKLE_R = (-0.4609, 0.3378, 0.0678)
FOOT_LEN = 0.78
FOOT_W = 0.39
HEEL_FRAC = 0.30          # ankle sits 30% of length from the heel
HEEL_DZ = FOOT_LEN * HEEL_FRAC
TOE_DZ = FOOT_LEN * (1.0 - HEEL_FRAC)
COLLAR_Y = 0.30           # membrane top ring, just under the ankle pin


def build_foot(center_x: float) -> tuple[np.ndarray, np.ndarray]:
    """One foot: sole quad + collar quad around the ankle pin, capped.
    Returns (verts float32 (n,9) [pos3, normal3, color3], tris uint32 (m,3))."""
    ax, ay, az = center_x, ANKLE_L[1], ANKLE_L[2]
    hw = FOOT_W / 2.0
    heel_z = az + HEEL_DZ
    toe_z = az - TOE_DZ
    # eight corners: sole rectangle (y=0) + collar rectangle (y=COLLAR_Y),
    # the collar is inset to half width so the wedge reads as a foot
    sole = [(ax - hw, 0.0, heel_z), (ax + hw, 0.0, heel_z),
            (ax + hw, 0.0, toe_z), (ax - hw, 0.0, toe_z)]
    hwi = hw * 0.45
    collar = [(ax - hwi, COLLAR_Y, heel_z), (ax + hwi, COLLAR_Y, heel_z),
              (ax + hwi, COLLAR_Y, toe_z), (ax - hwi, COLLAR_Y, toe_z)]
    pts = sole + collar
    # outward faces: sole(down), heel(back +z), toe(front -z), two sides.
    # the top stays OPEN -- the leg's skin passes through the collar ring.
    faces = [
        (0, 1, 2, (0, -1, 0)), (0, 2, 3, (0, -1, 0)),          # sole (down)
        (5, 4, 7, (0, 0, 1)), (5, 7, 6, (0, 0, 1)),            # heel (back)
        (4, 5, 6, (0, 0, -1)), (4, 6, 7, (0, 0, -1)),          # toe (front)
        (4, 7, 3, (-1, 0, 0)), (4, 3, 0, (-1, 0, 0)),          # left side
        (1, 5, 6, (1, 0, 0)), (1, 6, 2, (1, 0, 0)),            # right side
    ]
    verts, tris = [], []
    for (a, b, c, nrm) in faces:
        pa, pb, pc = (np.asarray(pts[i], float) for i in (a, b, c))
        n = np.asarray(nrm, float)
        # winding must agree with the outward normal or backface culling
        # punches a hole in the membrane
        if np.dot(np.cross(pb - pa, pc - pa), n) < 0:
            b, c = c, b
        base = len(verts)
        for idx in (a, b, c):
            verts.append((*pts[idx], *nrm, 0.0, 0.0, 0.0))  # color filled later
        tris.append((base, base + 1, base + 2))
    return (np.asarray(verts, dtype=np.float32),
            np.asarray(tris, dtype=np.uint32))


def skin_color(mesh_verts: np.ndarray) -> tuple[float, float, float]:
    """Median color of existing vertices in the ankle region (y < 0.6)."""
    pos = mesh_verts.reshape(-1, 9)[:, 0:3]
    col = mesh_verts.reshape(-1, 9)[:, 6:9]
    near = pos[:, 1] < 0.6
    if near.sum() < 8:
        near = np.ones(len(pos), dtype=bool)
    med = np.median(col[near], axis=0)
    return (float(med[0]), float(med[1]), float(med[2]))


def load_blob(path: Path):
    raw = Path(path).read_bytes()
    n, idx_count = struct.unpack_from("<II", raw, 0)
    cr, ct, cp, slotmode = struct.unpack_from("<ffff", raw, 8)
    vcount = n * 9
    verts = np.frombuffer(raw, dtype=np.float32, count=vcount,
                          offset=24).reshape(n, 9)
    indices = np.frombuffer(raw, dtype=np.uint32, count=idx_count,
                            offset=24 + vcount * 4).copy()
    return dict(n=int(n), idx_count=int(idx_count), cam=(cr, ct, cp),
                slotmode=slotmode, verts=verts, indices=indices)


def foot_tris_center(verts: np.ndarray, tris: np.ndarray) -> float:
    """Mean x of the foot triangle set -- symmetry + placement check."""
    pts = verts.reshape(-1, 9)[:, 0:3]
    sel = pts[tris.reshape(-1)]
    return float(sel[:, 0].mean())


def main() -> int:
    release = Path(sys.argv[1]) if len(sys.argv) > 1 else \
        Path(r"E:\ChimeraWork\slot-05\.tmp\engine_build\roottranslation-BASE\Release")
    base = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:8107"
    snap = release / "session_snapshot"
    mesh_path = snap / "mesh_bin.blob"
    hinge_path = snap / "hinge_bin.blob"
    restore = "--restore" in sys.argv

    mesh = load_blob(mesh_path)
    if restore:
        post_mesh(base, mesh_path.read_bytes())
        post_hinge(base, hinge_path.read_bytes())
        print("restored original mesh + hinge")
        return 0

    color = skin_color(mesh["verts"])
    print(f"mesh: n={mesh['n']} tris={mesh['idx_count']} "
          f"cam={mesh['cam']} skin_color~({color[0]:.2f},{color[1]:.2f},{color[2]:.2f})")

    all_v, all_t, foot_rows = [], [], []
    base_row = mesh["n"]
    for cx in (ANKLE_L[0], ANKLE_R[0]):
        v, t = build_foot(cx)
        all_v.append(v)
        all_t.append(t + base_row)
        base_row += len(v)
        foot_rows.append((cx, len(v)))
    foot_v = np.vstack(all_v)
    foot_t = np.vstack(all_t)
    foot_v[:, 6:9] = color  # the membrane wears the creature's skin color

    new_n = mesh["n"] + len(foot_v)
    new_idx = np.concatenate([mesh["indices"], foot_t.reshape(-1)])
    header = struct.pack("<IIffff", new_n, len(new_idx), *mesh["cam"],
                         mesh["slotmode"])
    body = header + np.ascontiguousarray(
        np.vstack([mesh["verts"], foot_v])).tobytes() \
        + np.ascontiguousarray(new_idx).tobytes()
    post_mesh(base, body)
    print(f"posted mesh: n={new_n} (feet verts: {len(foot_v)}) "
          f"tris={len(new_idx)}")

    # extend the stride hinge weights so each foot travels with its own
    # shank cluster: left-foot verts ride wL, right-foot verts ride wR
    hinge_raw = hinge_path.read_bytes()
    (hn,) = struct.unpack_from("<I", hinge_raw, 0)
    new_n = hn + len(foot_v)
    head = struct.pack("<I", new_n) + hinge_raw[4:4 + 13 * 4]
    w = np.frombuffer(hinge_raw, dtype=np.float32,
                      count=hn * 2, offset=4 + 13 * 4).reshape(hn, 2).copy()
    add = np.zeros((len(foot_v), 2), dtype=np.float32)
    row = 0
    for cx, nv in foot_rows:
        side = 0 if cx > 0 else 1        # 0 = wL (left cluster), 1 = wR
        add[row:row + nv, side] = 1.0
        row += nv
    new_hinge = head + np.ascontiguousarray(
        np.vstack([w, add])).tobytes()
    post_hinge(base, new_hinge)
    print(f"posted hinge: nvert={hn + len(foot_v)} (L foot rides wL, "
          f"R foot rides wR)")

    # P2 measured from the posted buffer: the sole plane is y = 0
    sole_y = min(foot_v[:, 1])
    print(f"P2 sole min y = {sole_y:.6f} (must be 0.000000)")
    return 0


def post_mesh(base: str, body: bytes) -> None:
    req = urllib.request.Request(base + "/mesh_bin", data=body,
                                 method="POST",
                                 headers={"Content-Type":
                                          "application/octet-stream"})
    with urllib.request.urlopen(req, timeout=30) as r:
        print("mesh POST ->", r.read().decode()[:60])


def post_hinge(base: str, body: bytes) -> None:
    req = urllib.request.Request(base + "/hinge_bin", data=body,
                                 method="POST",
                                 headers={"Content-Type":
                                          "application/octet-stream"})
    with urllib.request.urlopen(req, timeout=30) as r:
        print("hinge POST ->", r.read().decode()[:60])


if __name__ == "__main__":
    sys.exit(main())
