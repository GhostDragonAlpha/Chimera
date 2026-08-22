"""Render a viewer-space .splat through gsplat from the viewer's own front camera.

If gsplat shows a good bear here while Spark shows dark mush, the file is good and
Spark's decode is the problem. If gsplat also shows dark mush, the file itself is bad.
"""
import sys
from pathlib import Path

import imageio
import numpy as np
import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools" / "gsplat" / "examples"))
sys.path.insert(0, str(ROOT / "ChimeraEngine"))

from gsplat.rendering import rasterization  # noqa: E402
import cpp_bridge as cb  # noqa: E402

SPLAT = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "models" / "genbear3" / "sv3d5_geom.splat")
OUT = sys.argv[2] if len(sys.argv) > 2 else str(ROOT / ".tmp" / "gsplat_viewspace.png")
TNORM = sys.argv[3] if len(sys.argv) > 3 else None  # norm_transform.npy -> apply T^-1

W, H = 576, 576
FOCAL = 900.0
C = np.array([0.0, 0.0, 1.899])  # original-world front camera (sv3d_to_colmap convention)


def world2cam(C):
    f = -C / np.linalg.norm(C)          # z_cam (forward, toward origin)
    x = np.cross(f, np.array([0.0, 1.0, 0.0]))
    x /= np.linalg.norm(x)
    y = np.cross(f, x)
    return np.stack([x, y, f], axis=0)  # rows, x-right y-down z-fwd (COLMAP/OpenCV)


buf = cb.load_splat(SPLAT).astype(np.float64)
if TNORM:
    T = np.load(TNORM)
    R, t = T[:3, :3], T[:3, 3]
    s = float(np.cbrt(abs(np.linalg.det(R))))  # similarity scale
    Rr = R / s
    buf[:, 0:3] = (buf[:, 0:3] - t) @ Rr / s   # x_orig = (1/s) R^T (x_norm - t)
    buf[:, 7:10] /= s
    # quats: the applied map F = Rr^T may be a reflection (det -1, gsplat's frame
    # flip). Gaussians are sign-symmetric per axis, so F @ diag(1,1,-1) is a proper
    # rotation producing the SAME covariance — use it for the quaternion.
    F = Rr.T
    if np.linalg.det(F) < 0:
        F = F @ np.diag([1.0, 1.0, -1.0])
    import scipy.spatial.transform as st
    qR = st.Rotation.from_matrix(F).as_quat()  # x,y,z,w
    qR = np.array([qR[3], qR[0], qR[1], qR[2]])   # -> w,x,y,z
    q = buf[:, 10:14]
    w1, x1, y1, z1 = qR
    w2, x2, y2, z2 = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    buf[:, 10:14] = np.stack([
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2], axis=1)
    print("unnormalized with 1/s =", round(1 / s, 3))


buf = cb.load_splat(SPLAT).astype(np.float64)
print("extent y:", np.percentile(buf[:, 1], [1, 50, 99]).round(3),
      "x:", np.percentile(buf[:, 0], [1, 99]).round(3),
      "z:", np.percentile(buf[:, 2], [1, 99]).round(3))

R_w2c = world2cam(C)
c2w = np.eye(4)
c2w[:3, :3] = R_w2c.T
c2w[:3, 3] = C
c2w_t = torch.from_numpy(c2w).float().cuda().unsqueeze(0)
K = torch.tensor([[[FOCAL, 0, W / 2], [0, FOCAL, H / 2], [0, 0, 1]]]).float().cuda()

rgb = buf[:, 3:6]
sh0_equiv = (rgb - 0.5) / 0.28209479177387814
with torch.no_grad():
    r, _, _ = rasterization(
        means=torch.from_numpy(buf[:, 0:3]).float().cuda(),
        quats=torch.from_numpy(buf[:, 10:14]).float().cuda(),
        scales=torch.from_numpy(buf[:, 7:10]).float().cuda(),
        opacities=torch.from_numpy(buf[:, 6]).float().cuda(),
        colors=torch.from_numpy(sh0_equiv).float().cuda().unsqueeze(1),
        viewmats=torch.linalg.inv(c2w_t), Ks=K, width=W, height=H, sh_degree=0,
        backgrounds=None)
img = (r[0].clamp(0, 1).cpu().numpy() * 255).astype(np.uint8)
imageio.imwrite(OUT, img)
print("wrote", OUT, "mean", img.mean().round(1))
