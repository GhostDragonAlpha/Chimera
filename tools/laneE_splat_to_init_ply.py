"""tools/laneE_splat_to_init_ply.py

Convert the oriented viewer .splat (models/genbear3/laneD_diffsplat.splat) into the
standard 3DGS PLY layout that tools/anysplat_refine.py expects: DC color, raw opacity,
log scales, normalized quats. The .splat is already in the viewer's orient=0 frame, so
the resulting PLY aligns exactly with the Lane E extrinsics.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from plyfile import PlyData, PlyElement

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ChimeraEngine"))

C0 = 0.28209479177387814


def load_raw_splat(path: str):
    raw = np.fromfile(path, dtype=np.uint8)
    n = len(raw) // 32
    rec = raw[: n * 32].reshape(n, 32)
    pos = rec[:, 0:12].view(np.float32).reshape(n, 3).astype(np.float64)
    scale = rec[:, 12:24].view(np.float32).reshape(n, 3).astype(np.float64)
    rgba = rec[:, 24:28].astype(np.float64)
    rgb = rgba[:, :3] / 255.0
    alpha = rgba[:, 3] / 255.0
    rot_u8 = rec[:, 28:32].astype(np.float64)
    rot = (rot_u8 - 128.0) / 128.0
    rot = rot / np.linalg.norm(rot, axis=1, keepdims=True)
    return pos, rot, scale, rgb, alpha


def save_ply(path: str, pos, rot, scale, rgb, alpha):
    n = len(pos)
    f_dc = (rgb - 0.5) / C0
    names = [
        "x", "y", "z", "nx", "ny", "nz",
        "f_dc_0", "f_dc_1", "f_dc_2",
        "opacity", "scale_0", "scale_1", "scale_2",
        "rot_0", "rot_1", "rot_2", "rot_3",
    ]
    arr = np.empty(n, dtype=[(nm, "f4") for nm in names])
    arr["x"], arr["y"], arr["z"] = pos.T
    arr["nx"], arr["ny"], arr["nz"] = 0.0, 0.0, 0.0
    arr["f_dc_0"], arr["f_dc_1"], arr["f_dc_2"] = f_dc.T
    arr["opacity"] = alpha
    arr["scale_0"], arr["scale_1"], arr["scale_2"] = np.log(scale).T
    arr["rot_0"], arr["rot_1"], arr["rot_2"], arr["rot_3"] = rot.T
    PlyData([PlyElement.describe(arr, "vertex")], text=False).write(path)


def main() -> int:
    splat = ROOT / "models/genbear3/laneD_diffsplat.splat"
    out = ROOT / "models/genbear3/laneE_init.ply"
    pos, rot, scale, rgb, alpha = load_raw_splat(str(splat))
    save_ply(str(out), pos, rot, scale, rgb, alpha)
    print(f"wrote {out}  ({len(pos)} gaussians)")

    # Sanity check: reload with the same loader the refine script uses.
    sys.path.insert(0, str(ROOT / "tools"))
    import anysplat_refine as ar
    means, rgb2, opac, logs, quats = ar.load_any_ply(str(out))
    print(f"reload check: means {means.shape} opacity range [{opac.min():.3f}, {opac.max():.3f}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
