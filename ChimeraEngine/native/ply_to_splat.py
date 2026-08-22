"""ply_to_splat.py — standard 3DGS .ply (gsplat/INRIA export) -> 32-byte .splat.

The capture pipeline's last mile: gsplat trains in the COLMAP world frame and exports the
standard .ply (f_dc_*, f_rest_*, opacity logit, scale logs, rot quats). This converts to the
compact .splat the engine/viewer consume: rgb = 0.5 + C0*f_dc (SH rest dropped — flat color,
matching every other source in the repo), alpha = sigmoid(opacity), scale = exp(log_scale),
rot normalized. Header-driven (property names, not a fixed dtype) so both gsplat and INRIA
exports read. No axis remap: capture frames are arbitrary (COLMAP world); re-orient with the
same raw-space rotation step used for the koala (front=+z) BEFORE measuring downstream.

Usage (from the repo root):
    python ChimeraEngine/native/ply_to_splat.py capture/myobject/train_out/ply/splat_29999.ply \
        --out models/capture/myobject.splat
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_CHIMERA_ENGINE = _HERE.parent
if str(_CHIMERA_ENGINE) not in sys.path:
    sys.path.insert(0, str(_CHIMERA_ENGINE))

import cpp_bridge as cb          # noqa: E402

C0 = 0.28209479177387814


def load_3dgs_ply(ply_path: str, opacity_raw: bool = False) -> np.ndarray:
    """Standard 3DGS PLY -> (n,14) [x,y,z, r,g,b, a, sx,sy,sz, qw,qx,qy,qz], header-driven.

    opacity_raw: True when the PLY stores raw alpha in (0,1) instead of a logit
    (AnySplat's export_ply does; gsplat/INRIA store the logit)."""
    with open(ply_path, "rb") as f:
        props, n_verts = [], 0
        for line in iter(f.readline, b""):
            line = line.strip().split()
            if line[:2] == [b"element", b"vertex"]:
                n_verts = int(line[2])
            elif line[:1] == [b"property"] and line[1] == b"float":
                props.append(line[2].decode())
            elif line[:1] == [b"end_header"]:
                break
        raw = np.fromfile(f, dtype=np.float32, count=n_verts * len(props))
    v = raw.reshape(n_verts, len(props))
    col = {p: i for i, p in enumerate(props)}

    def g(name, alt=None):
        if name in col:
            return v[:, col[name]].astype(np.float64)
        if alt is not None and alt in col:
            return v[:, col[alt]].astype(np.float64)
        raise KeyError(f"{name} not in ply properties")

    pos = np.stack([g("x"), g("y"), g("z")], axis=1)
    rgb = np.clip(0.5 + C0 * np.stack([g("f_dc_0"), g("f_dc_1"), g("f_dc_2")], axis=1), 0, 1)
    op = g("opacity")
    alpha = np.clip(op, 0.0, 1.0) if opacity_raw else 1.0 / (1.0 + np.exp(-op))
    scale = np.exp(np.stack([g("scale_0"), g("scale_1"), g("scale_2")], axis=1))
    rot = np.stack([g("rot_0"), g("rot_1"), g("rot_2"), g("rot_3")], axis=1)
    rot = rot / np.linalg.norm(rot, axis=1, keepdims=True)
    return np.concatenate([pos, rgb, alpha[:, None], scale, rot], axis=1).astype(np.float32)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("target", help="input 3DGS .ply")
    ap.add_argument("--out", required=True, help="output .splat")
    a = ap.parse_args()
    buf = load_3dgs_ply(a.target)
    cb.save_splat(a.out, buf)
    print(f"ply -> splat: {len(buf)} splats -> {a.out}")


if __name__ == "__main__":
    main()
