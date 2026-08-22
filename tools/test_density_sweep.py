"""Az sweep + scale-factor test on sv3d5_world.splat (already unnormalized, SH-baked).

Renders through gsplat at the dataset camera (r=1.899, f=900, 576px).
Row 1: az 0/90/180/270 at native scale  -> confirm bright face + orientation.
Row 2: az 90 (front) at scale x1, x3, x5 -> does footprint size fix the mush?
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "gsplat" / "examples"))
sys.path.insert(0, str(ROOT / "ChimeraEngine"))

import imageio
import numpy as np
import torch
from gsplat.rendering import rasterization

import cpp_bridge as cb

SRC = ROOT / "models" / "genbear3" / "sv3d5_world.splat"
OUT = ROOT / ".tmp" / "density_sweep.png"

buf = cb.load_splat(str(SRC)).astype(np.float64)
print(f"loaded {len(buf)} splats from {SRC.name}")
print(f"scale p50 per axis: {np.percentile(buf[:, 7:10], 50, axis=0)}")


def world2cam(C):
    f = -C / np.linalg.norm(C)
    x = np.cross(f, [0.0, 1.0, 0.0])
    x /= np.linalg.norm(x)
    y = np.cross(f, x)
    return np.stack([x, y, f], 0)


means = torch.from_numpy(buf[:, 0:3]).float().cuda()
quats = torch.from_numpy(buf[:, 10:14]).float().cuda()
scales0 = torch.from_numpy(buf[:, 7:10]).float().cuda()
opac = torch.from_numpy(buf[:, 6]).float().cuda()
sh0 = torch.from_numpy((buf[:, 3:6] - 0.5) / 0.28209479177387814).float().cuda().unsqueeze(1)
K = torch.tensor([[[900.0, 0, 288], [0, 900.0, 288], [0, 0, 1]]]).float().cuda()


def render(az, scale_mul):
    a = np.radians(az)
    C = 1.899 * np.array([np.sin(a), 0.0, np.cos(a)])
    c2w = np.eye(4)
    c2w[:3, :3] = world2cam(C).T
    c2w[:3, 3] = C
    vm = torch.linalg.inv(torch.from_numpy(c2w).float().cuda().unsqueeze(0))
    with torch.no_grad():
        r, _, _ = rasterization(means=means, quats=quats, scales=scales0 * scale_mul,
                                opacities=opac, colors=sh0, viewmats=vm, Ks=K,
                                width=576, height=576, sh_degree=0, backgrounds=None)
    img = (r[0].clamp(0, 1).cpu().numpy() * 255).astype(np.uint8)
    print(f"az{az} x{scale_mul}: mean {img.mean():.1f}")
    return img


row1 = [render(az, 1.0) for az in [0, 90, 180, 270]]
row2 = [render(90, m) for m in [1.0, 3.0, 5.0, 8.0]]
grid = np.concatenate([np.concatenate(row1, axis=1), np.concatenate(row2, axis=1)], axis=0)
imageio.imwrite(str(OUT), grid)
print(f"wrote {OUT}  (row1: az0,90,180,270 @x1 | row2: az90 @x1,x3,x5,x8)")
