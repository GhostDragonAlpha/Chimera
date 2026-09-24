"""B3 work copy of baseline mesh_target.py — input paths repointed to the READ-ONLY
baseline_snapshot copies; loader logic verbatim (hashes, JNT3 layout, unit scale).

Writes nothing outside audits/B3_mech_requirements/. Prints:
  - full target joint ledger (name, pos, axis, ROM, FK parent)
  - measured forearm chain lengths (shoulder/elbow/wrist, both sides)
  - mesh extent (verts, tris, bbox)
  - band sizes (vertex counts) for the forearm joints
  - digit-joint existence check (names containing finger/thumb/digit/phalanx)
"""
from __future__ import annotations

import hashlib
import os
import struct

import numpy as np

MESH_BIRTH = r"E:\PythonChimera\forearm_package\baseline_snapshot\inputs\monkey_birth.bin"
PACK_JNT3 = r"E:\PythonChimera\forearm_package\baseline_snapshot\inputs\monkey_joints.bin"

MESH_UNIT_TO_M = 0.065


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def load_mesh(path):
    b = open(path, "rb").read()
    N, M = struct.unpack("<ii", b[:8])
    V = np.frombuffer(b, np.float32, N * 3, 8).reshape(N, 3).astype(np.float64)
    F = np.frombuffer(b, np.uint32, M * 3, 8 + N * 12).reshape(M, 3)
    return V, F


def load_pack(path):
    b = open(path, "rb").read()
    tag = b[:4]
    assert tag == b"JNT3", tag
    nv, nj, nl = struct.unpack("<III", b[4:16])
    names = [n.decode("ascii") for n in b[16 : 16 + nl].split(b"\x00") if n][:nj]
    p = 16 + nl
    assign = np.frombuffer(b, np.int32, nv, p).copy()
    p += nv * 4
    w = np.frombuffer(b, np.float32, nv, p).copy()
    p += nv * 4
    J = np.frombuffer(b, np.float32, nj * 3, p).reshape(nj, 3).astype(np.float64).copy()
    p += nj * 12
    AX = np.frombuffer(b, np.float32, nj * 3, p).reshape(nj, 3).astype(np.float64).copy()
    p += nj * 12
    ROM = np.frombuffer(b, np.float32, nj * 2, p).reshape(nj, 2).copy()
    p += nj * 8
    parents = np.frombuffer(b, np.int32, nj, p).copy()
    p += nj * 4
    joint2 = np.frombuffer(b, np.int32, nv, p).copy()
    p += nv * 4
    w2 = np.frombuffer(b, np.float32, nv, p).copy()
    assert p + nv * 4 == len(b), (p + nv * 4, len(b))
    return {"names": names, "assign": assign, "w": w, "J": J, "AX": AX,
            "ROM": ROM, "parents": parents, "joint2": joint2, "w2": w2}


def main() -> int:
    print(f"birth sha256 {sha256_of(MESH_BIRTH)}")
    print(f"pack  sha256 {sha256_of(PACK_JNT3)}")
    V, F = load_mesh(MESH_BIRTH)
    pk = load_pack(PACK_JNT3)
    V = V * MESH_UNIT_TO_M
    J = pk["J"] * MESH_UNIT_TO_M
    names = pk["names"]
    idx = {n: i for i, n in enumerate(names)}
    print(f"mesh verts {len(V)} tris {len(F)}")
    print(f"bbox x [{V[:,0].min():.4f},{V[:,0].max():.4f}] y [{V[:,1].min():.4f},{V[:,1].max():.4f}] "
          f"z [{V[:,2].min():.4f},{V[:,2].max():.4f}] m")
    print(f"joints nj={len(names)}")
    for n, i in idx.items():
        par = names[pk['parents'][i]] if pk['parents'][i] >= 0 else "(root)"
        j = J[i]
        rom = pk["ROM"][i]
        print(f"  [{i:2d}] {n:12s} pos=({j[0]:+.4f},{j[1]:+.4f},{j[2]:+.4f}) m  "
              f"axis=({pk['AX'][i][0]:+.3f},{pk['AX'][i][1]:+.3f},{pk['AX'][i][2]:+.3f})  "
              f"ROM=[{rom[0]:+.2f},{rom[1]:+.2f}]  parent={par}")
    # digit check
    digit_hits = [n for n in names if any(k in n.lower() for k in
                  ("finger", "thumb", "digit", "phal", "mcp", "pip", "dip", "mc_"))]
    print(f"digit-like joint names: {digit_hits if digit_hits else 'NONE'}")
    # chain lengths
    for a, b_ in (("shoulder_R", "elbow_R"), ("elbow_R", "wrist_R"),
                  ("shoulder_L", "elbow_L"), ("elbow_L", "wrist_L")):
        d = float(np.linalg.norm(J[idx[b_]] - J[idx[a]]))
        print(f"|{b_} - {a}| = {d*1000:.3f} mm")
    # band sizes
    for n in ("elbow_R", "wrist_R", "elbow_L", "wrist_L", "hand_tip" if "hand_tip" in idx else "wrist_R"):
        cnt = int((pk["assign"] == idx[n]).sum())
        cnt2 = int((pk["joint2"] == idx[n]).sum())
        print(f"band {n}: primary-owner verts {cnt}, secondary-owner verts {cnt2}")
    # distal-most joints per side (FK leaves) and anything distal of wrist
    for side in ("R", "L"):
        wrist = f"wrist_{side}"
        wi = idx[wrist]
        # FK children in pack
        kids = [names[i] for i in range(len(names)) if pk["parents"][i] == wi]
        print(f"FK children of {wrist}: {kids if kids else 'NONE'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
