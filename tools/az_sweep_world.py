"""Azimuth sweep of the unnormalized baked cloud through gsplat — find the bright side."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "gsplat" / "examples"))
sys.path.insert(0, str(ROOT / "ChimeraEngine"))

import imageio
import numpy as np
import scipy.spatial.transform as st
import torch
from gsplat.rendering import rasterization

import cpp_bridge as cb

buf = cb.load_splat(str(ROOT / "models" / "genbear3" / "sv3d5_baked2.splat")).astype(np.float64)
T = np.load(str(ROOT / "capture" / "sv3d_bear" / "norm_transform.npy"))
R, t = T[:3, :3], T[:3, 3]
s = float(np.cbrt(abs(np.linalg.det(R))))
Rr = R / s
buf[:, 0:3] = (buf[:, 0:3] - t) @ Rr / s
buf[:, 7:10] /= s
F = Rr.T
if np.linalg.det(F) < 0:
    F = F @ np.diag([1.0, 1.0, -1.0])
q4 = st.Rotation.from_matrix(F).as_quat()
qR = np.array([q4[3], q4[0], q4[1], q4[2]])
w1, x1, y1, z1 = qR
w2, x2, y2, z2 = buf[:, 10], buf[:, 11], buf[:, 12], buf[:, 13]
buf[:, 10:14] = np.stack([w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
                          w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
                          w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                          w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2], axis=1)


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
for az in [0, 90, 180, 270]:
    a = np.radians(az)
    C = 1.899 * np.array([np.sin(a), 0.0, np.cos(a)])
    Rw = world2cam(C)
    c2w = np.eye(4)
    c2w[:3, :3] = Rw.T
    c2w[:3, 3] = C
    vm = torch.linalg.inv(torch.from_numpy(c2w).float().cuda().unsqueeze(0))
    with torch.no_grad():
        r, _, _ = rasterization(means=means, quats=quats, scales=scales, opacities=opac,
                                colors=sh0, viewmats=vm, Ks=K, width=576, height=576,
                                sh_degree=0, backgrounds=None)
    img = (r[0].clamp(0, 1).cpu().numpy() * 255).astype(np.uint8)
    print(f"az{az}: mean {img.mean():.1f}")
    imgs.append(img)
imageio.imwrite(str(ROOT / ".tmp" / "az_sweep.png"), np.concatenate(imgs, axis=1))
print("wrote .tmp/az_sweep.png  (order: az0 az90 az180 az270)")
