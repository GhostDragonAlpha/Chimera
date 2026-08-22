"""Az sweep (0/45/90/.../315) of a world-frame baked .splat through gsplat.
Usage: world_sweep.py <splat> <out.png> [radius]
Camera: dataset convention (r=1.899, f=900, 576px, y-up, OpenCV y-down).
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

src, out = Path(sys.argv[1]), Path(sys.argv[2])
radius = float(sys.argv[3]) if len(sys.argv) > 3 else 1.899

buf = cb.load_splat(str(src)).astype(np.float64)
print(f"loaded {len(buf)} splats from {src.name}")


def world2cam(C):
    f = -C / np.linalg.norm(C)
    x = np.cross(f, [0.0, 1.0, 0.0])
    x /= np.linalg.norm(x)
    y = np.cross(f, x)
    return np.stack([x, y, f], 0)


means = torch.from_numpy(buf[:, 0:3]).float().cuda()
quats = torch.from_numpy(buf[:, 10:14]).float().cuda()
scales = torch.from_numpy(buf[:, 7:10]).float().cuda()
opac = torch.from_numpy(buf[:, 6]).float().cuda()
sh0 = torch.from_numpy((buf[:, 3:6] - 0.5) / 0.28209479177387814).float().cuda().unsqueeze(1)
K = torch.tensor([[[900.0, 0, 288], [0, 900.0, 288], [0, 0, 1]]]).float().cuda()

imgs = []
for az in range(0, 360, 45):
    a = np.radians(az)
    C = radius * np.array([np.sin(a), 0.0, np.cos(a)])
    c2w = np.eye(4)
    c2w[:3, :3] = world2cam(C).T
    c2w[:3, 3] = C
    vm = torch.linalg.inv(torch.from_numpy(c2w).float().cuda().unsqueeze(0))
    with torch.no_grad():
        r, _, _ = rasterization(means=means, quats=quats, scales=scales, opacities=opac,
                                colors=sh0, viewmats=vm, Ks=K, width=576, height=576,
                                sh_degree=0, backgrounds=None)
    img = (r[0].clamp(0, 1).cpu().numpy() * 255).astype(np.uint8)
    print(f"az{az}: mean {img.mean():.1f}")
    imgs.append(img)
row1 = np.concatenate(imgs[:4], axis=1)
row2 = np.concatenate(imgs[4:], axis=1)
imageio.imwrite(str(out), np.concatenate([row1, row2], axis=0))
print(f"wrote {out}  (row1: az0,45,90,135 | row2: az180,225,270,315)")
