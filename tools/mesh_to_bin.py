"""mesh_to_bin.py — any mesh -> the engine's /mesh_bin format.

    python tools/mesh_to_bin.py <in.glb|.ply|.obj> [out.bin]

The engine's triangle route (POST /mesh_bin) takes ONE flat little-endian blob:

    [int32 N][int32 M][N*3 float32 xyz][M*3 uint32 indices]

`ChimeraEngine/cpp_bridge.load_mesh_bin` reads exactly that, so anything
converted here can be uploaded as-is. There is no scale factor and no axis flip
here on purpose: the mesh goes in at its own coordinates, because a converter
that "fixes" orientation is a converter that hides it. Read the extents it prints
and set the camera to match.

The subject was living in .tmp/ (scratch, quarantined) — the converter writes to
Saved/meshes/ so the pipeline's one subject is not one `rm -rf` from gone.
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path("E:/PythonChimera")
OUT_DIR = ROOT / "Saved" / "meshes"


def to_bin(src: Path, dst: Path) -> dict:
    m = trimesh.load(str(src), force="mesh")
    if isinstance(m, trimesh.Scene):
        m = m.dump(concatenate=True)
    v = np.ascontiguousarray(m.vertices, dtype=np.float32)
    f = np.ascontiguousarray(m.faces, dtype=np.uint32)
    # uint32 indices: a mesh over 4.29e9 verts is not a thing, but a NEGATIVE
    # int would silently wrap into a wild index and draw garbage.
    if f.size and (f.min() < 0 or f.max() >= len(v)):
        raise SystemExit(f"index out of range: min {f.min()} max {f.max()} for {len(v)} verts")

    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "wb") as fh:
        fh.write(struct.pack("<ii", len(v), len(f)))
        fh.write(v.tobytes())
        fh.write(f.tobytes())

    return {"src": str(src), "bin": str(dst), "verts": int(len(v)), "tris": int(len(f)),
            "bounds_min": m.bounds[0].round(4).tolist(),
            "bounds_max": m.bounds[1].round(4).tolist(),
            "size": m.extents.round(4).tolist(),
            "watertight": bool(m.is_watertight), "bytes": dst.stat().st_size}


def main() -> int:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else OUT_DIR / (src.stem + ".bin")
    info = to_bin(src, dst)
    for k, val in info.items():
        print(f"  {k:12}: {val}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
