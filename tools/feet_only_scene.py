"""feet_only_scene.py -- the membrane feet ALONE as the mesh scene.

The new system's first citizen: two foot membranes (triangle sets) on the
ground plane at the measured ankles, rendered through /mesh_bin. The old
skin is retired from the render.
"""
from __future__ import annotations

import struct
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np

sys.path.insert(0, r"E:\ChimeraWork\slot-01\tools")
from feet_membranes import ANKLE_L, ANKLE_R, build_foot  # noqa: E402

COLOR = (0.80, 0.55, 0.35)
CAM = (3.2, -0.7, 0.42)


def feet_mesh_blob() -> bytes:
    all_v, all_t, base = [], [], 0
    for cx in (ANKLE_L[0], ANKLE_R[0]):
        v, t = build_foot(cx)
        v[:, 6:9] = COLOR
        all_v.append(v)
        all_t.append(t + base)
        base += len(v)
    verts = np.vstack(all_v)
    tris = np.vstack(all_t)
    header = struct.pack("<IIffff", len(verts), tris.size, *CAM, 0.0)
    return header + np.ascontiguousarray(verts).tobytes() \
        + np.ascontiguousarray(tris).tobytes()


def post(base: str, blob: bytes) -> None:
    req = urllib.request.Request(base + "/mesh_bin", data=blob, method="POST",
                                 headers={"Content-Type":
                                          "application/octet-stream"})
    with urllib.request.urlopen(req, timeout=30) as r:
        print("mesh POST ->", r.read().decode()[:40])


def capture(base: str, out: Path) -> None:
    time.sleep(1.5)
    with urllib.request.urlopen(base + "/frame", timeout=30) as r:
        out.write_bytes(r.read())
    print("captured:", out)


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8107"
    proof = Path(r"C:\Users\allen\Desktop\CHIMERA_PROOF\FEET")
    proof.mkdir(parents=True, exist_ok=True)
    blob = feet_mesh_blob()
    post(base, blob)
    time.sleep(1.5)
    capture(base, proof / "feet_only_mesh.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
