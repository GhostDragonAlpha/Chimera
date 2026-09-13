"""classify_run.py -- classify the real monkey's triangles into CA types
(nearest measured joint), bind its vertices for travel, and post:
  /mesh_bin      the full-format monkey mesh
  /tick_classify [u32 n][u8 joint per triangle]
  /tick_vertbind [u32 n][u8 joint per vertex]
  /tick_joints   [u32 n][f32 x,y,z per joint]
Then pose/press intents drive the REAL object through the membrane tick.
"""
from __future__ import annotations

import json
import struct
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np


def parse_full(path: Path):
    raw = path.read_bytes()
    n, m = struct.unpack_from("<II", raw, 0)
    verts = np.frombuffer(raw, dtype=np.float32, count=n * 9,
                          offset=24).reshape(n, 9)
    idx = np.frombuffer(raw, dtype=np.uint32, count=m * 3,
                        offset=24 + n * 36)
    return verts, idx


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8107"
    root = Path(r"E:\ChimeraWork\slot-01\.tmp")
    joints = json.loads((root / "joints28.json").read_text())
    pins = np.asarray([j["J"] for j in joints], dtype=np.float32)

    verts, idx = parse_full(root / "monkey_full.bin")
    pos = verts[:, 0:3]
    centroids = pos[idx].mean(axis=1)

    # per-triangle and per-vertex nearest measured joint (the CA typing)
    d2t = ((centroids[:, None, :] - pins[None, :, :]) ** 2).sum(axis=2)
    tri_joint = d2t.argmin(axis=1).astype(np.uint8)
    d2v = ((pos[:, None, :] - pins[None, :, :]) ** 2).sum(axis=2)
    vert_joint = d2v.argmin(axis=1).astype(np.uint8)

    print("triangle types:", np.bincount(tri_joint, minlength=28).tolist())

    def post(path: str, body: bytes, timeout: int = 60) -> str:
        req = urllib.request.Request(base + path, data=body, method="POST",
                                     headers={"Content-Type":
                                              "application/octet-stream"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode()[:60]

    mesh = (root / "monkey_full.bin").read_bytes()
    print("mesh:", post("/mesh_bin", mesh, timeout=120))
    print("classify:", post("/tick_classify",
                            struct.pack("<I", len(tri_joint))
                            + tri_joint.tobytes()))
    print("vertbind:", post("/tick_vertbind",
                            struct.pack("<I", len(vert_joint))
                            + vert_joint.tobytes()))
    pins_body = struct.pack("<I", len(pins)) + np.ascontiguousarray(pins).tobytes()
    print("joints:", post("/tick_joints", pins_body))
    return 0


if __name__ == "__main__":
    sys.exit(main())
