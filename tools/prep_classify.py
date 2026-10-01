"""prep_classify.py -- rebuild the monkey mesh blob (full format) and
capture the 28 joint pins from the old engine for classification."""
import json
import struct
import sys
import urllib.request
from pathlib import Path

import numpy as np

BIRTH = Path(r"E:\PythonChimera\Saved\meshes\monkey_birth.bin")
JOINTS_BIN = Path(r"E:\PythonChimera\Saved\meshes\monkey_joints.bin")
OUT = Path(r"E:\ChimeraWork\slot-01\.tmp")
COLOR = (0.80, 0.55, 0.35)


def main() -> int:
    old_base = "http://127.0.0.1:8090"
    raw = BIRTH.read_bytes()
    n, m = struct.unpack_from("<II", raw, 0)
    pos = np.frombuffer(raw, dtype=np.float32, count=n * 3, offset=8).reshape(n, 3)
    idx = np.frombuffer(raw, dtype=np.uint32, count=m * 3,
                        offset=8 + n * 12)

    # vertex normals: area-weighted from face normals (welded mesh)
    idx = idx.reshape(-1, 3)
    tri = pos[idx]
    fn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    norm = np.zeros((n, 3), dtype=np.float32)
    for k in range(3):
        np.add.at(norm, idx[:, k], fn)
    lens = np.linalg.norm(norm, axis=1, keepdims=True)
    lens[lens == 0] = 1.0
    norm = norm / lens

    verts9 = np.empty((n, 9), dtype=np.float32)
    verts9[:, 0:3] = pos
    verts9[:, 3:6] = norm
    verts9[:, 6:9] = COLOR

    blob = struct.pack("<IIffff", n, m * 3, 26.0, -0.55, 0.42, 0.0) \
        + np.ascontiguousarray(verts9).tobytes() \
        + np.ascontiguousarray(idx).tobytes()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "monkey_full.bin").write_bytes(blob)
    print(f"monkey_full.bin: verts={n} tris={m} bytes={len(blob)}")

    # boot the old engine is done by the caller; here we just capture
    if "--capture" in sys.argv:
        j = json.loads(urllib.request.urlopen(old_base + "/joints",
                                              timeout=15).read())
        joints = [{"name": t["name"], "J": t["J"], "axis": t["axis"],
                   "ext": t["ext"], "flex": t["flex"]}
                  for t in j["joints"]]
        (OUT / "joints28.json").write_text(json.dumps(joints, indent=1))
        print("captured", len(joints), "joints")
    return 0


if __name__ == "__main__":
    sys.exit(main())
