"""Final chain check: same camera, same bake — normalized frame vs world frame.
Left:  sv3d5_baked2.splat rendered with cam0 transformed into the NORMALIZED frame.
Right: sv3d5_world.splat rendered with cam0 in the ORIGINAL world (fixed quat fold).
If the fold fix is exact, the two renders are near-identical.
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

T = np.load(str(ROOT / "capture" / "sv3d_bear" / "norm_transform.npy"))
Rn, tn = T[:3, :3], T[:3, 3]
sc = float(np.cbrt(abs(np.linalg.det(Rn))))
Rr = Rn / sc  # proper-up-to-sign rotation part of the norm map


def world2cam(C):
    f = -C / np.linalg.norm(C)
    x = np.cross(f, [0.0, 1.0, 0.0])
    x /= np.linalg.norm(x)
    y = np.cross(f, x)
    return np.stack([x, y, f], 0)


C_orig = np.array([0.0, 0.0, 1.8987342])
Rw_orig = world2cam(C_orig)  # rows: cam axes in world

# normalized-frame camera: p_norm = sc*Rr @ p_orig + tn
C_norm = sc * Rr @ C_orig + tn
Rw_norm = Rw_orig @ Rr.T  # world->cam rotation composed with orig->norm rotation

K = torch.tensor([[[900.0, 0, 288], [0, 900.0, 288], [0, 0, 1]]]).float().cuda()


def render(splat, C, Rw):
    buf = cb.load_splat(str(splat)).astype(np.float64)
    c2w = np.eye(4)
    c2w[:3, :3] = Rw.T
    c2w[:3, 3] = C
    vm = torch.linalg.inv(torch.from_numpy(c2w).float().cuda().unsqueeze(0))
    sh0 = (buf[:, 3:6] - 0.5) / 0.28209479177387814
    with torch.no_grad():
        r, _, _ = rasterization(
            means=torch.from_numpy(buf[:, 0:3]).float().cuda(),
            quats=torch.from_numpy(buf[:, 10:14]).float().cuda(),
            scales=torch.from_numpy(buf[:, 7:10]).float().cuda(),
            opacities=torch.from_numpy(buf[:, 6]).float().cuda(),
            colors=torch.from_numpy(sh0).float().cuda().unsqueeze(1),
            viewmats=vm, Ks=K, width=576, height=576, sh_degree=0)
    return (r[0].clamp(0, 1).cpu().numpy() * 255).astype(np.uint8)


a = render(ROOT / "models" / "genbear3" / "sv3d5_baked2.splat", C_norm, Rw_norm)
b = render(ROOT / "models" / "genbear3" / "sv3d5_world.splat", C_orig, Rw_orig)
diff = np.abs(a.astype(int) - b.astype(int))
print(f"norm-frame mean {a.mean():.1f} | world-frame mean {b.mean():.1f} | "
      f"mean|diff| {diff.mean():.2f}, p99 {np.percentile(diff, 99):.0f}")
imageio.imwrite(str(ROOT / ".tmp" / "frame_ab.png"),
                np.concatenate([a, b, np.clip(diff * 4, 0, 255).astype(np.uint8)], axis=1))
print("wrote .tmp/frame_ab.png  (normalized | world | 4x diff)")
