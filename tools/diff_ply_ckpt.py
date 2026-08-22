"""Numerical diff: gsplat checkpoint tensors vs ply_to_splat decode of the exported PLY."""
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
sys.path.insert(0, str(ROOT / "ChimeraEngine" / "native"))
from ply_to_splat import load_3dgs_ply  # noqa: E402

CKPT = ROOT / "capture" / "sv3d_bear" / "train_out5" / "ckpts" / "ckpt_29999_rank0.pt"
PLY = ROOT / "capture" / "sv3d_bear" / "train_out5" / "ply" / "point_cloud_29999.ply"

ck = torch.load(CKPT, map_location="cpu", weights_only=False)["splats"]
buf = load_3dgs_ply(str(PLY)).astype(np.float64)

n_ck, n_ply = len(ck["means"]), len(buf)
print(f"counts: ckpt {n_ck} ply {n_ply}")
n = min(n_ck, n_ply)

m_ck = ck["means"][:n].numpy()
m_py = buf[:n, 0:3]
print("pos   max|d|", np.abs(m_ck - m_py).max())

s_ck = np.exp(ck["scales"][:n].numpy())
s_py = buf[:n, 7:10]
print("scale ckpt  p50", np.median(s_ck), "max", s_ck.max())
print("scale ply   p50", np.median(s_py), "max", s_py.max())
print("scale max|d|", np.abs(s_ck - s_py).max(), "rel", np.abs(s_ck - s_py).max() / (np.median(s_ck)))

o_ck = torch.sigmoid(ck["opacities"][:n]).numpy()
o_py = buf[:n, 6]
print("alpha ckpt  p50", np.median(o_ck), " ply p50", np.median(o_py), " max|d|", np.abs(o_ck - o_py).max())

q_ck = F.normalize(ck["quats"][:n], dim=-1).numpy()
q_py = buf[:n, 10:14]
# sign-agnostic quat diff
d = np.minimum(np.abs(q_ck - q_py), np.abs(q_ck + q_py)).max()
print("quat  max|d| (sign-agnostic)", d)

sh0 = ck["sh0"][:n, 0].numpy()
rgb_ck = np.clip(0.5 + 0.28209479177387814 * sh0, 0, 1)
rgb_py = buf[:n, 3:6]
print("rgbDC max|d|", np.abs(rgb_ck - rgb_py).max())
