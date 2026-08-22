"""Degradation budget at the anchor camera:
  GT frame_00 | ckpt full-SH3 | baked .splat SH0  (all from the same camera).
ckpt render is in the normalized frame (C_norm/Rw_norm via the norm transform);
baked renders use the normalized-frame file sv3d5_baked2.splat at the same camera.
"""
import sys
from pathlib import Path

import imageio
import numpy as np
import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parent.parent
EX = ROOT / "tools" / "gsplat" / "examples"
sys.path.insert(0, str(EX))
sys.path.insert(0, str(ROOT / "ChimeraEngine"))

from datasets.colmap import Dataset, Parser  # noqa: E402
from gsplat.rendering import rasterization  # noqa: E402
import cpp_bridge as cb  # noqa: E402

DATA = ROOT / "capture" / "sv3d_bear" / "data5"
CKPT = ROOT / "capture" / "sv3d_bear" / "train_out5" / "ckpts" / "ckpt_29999_rank0.pt"
SPLAT = ROOT / "models" / "genbear3" / "sv3d5_baked2.splat"
OUT = ROOT / ".tmp" / "budget.png"

parser = Parser(data_dir=str(DATA), factor=1, normalize=True, test_every=8)
ds = Dataset(parser, split="train")
ds.indices = np.arange(len(parser.image_names))
item = ds[0]
c2w = item["camtoworld"].unsqueeze(0).cuda()
K = item["K"].unsqueeze(0).cuda()
vm = torch.linalg.inv(c2w)
gt = item["image"].numpy().astype(np.uint8)

ck = torch.load(CKPT, map_location="cuda", weights_only=False)["splats"]
with torch.no_grad():
    r, _, _ = rasterization(
        means=ck["means"], quats=F.normalize(ck["quats"], dim=-1),
        scales=torch.exp(ck["scales"]), opacities=torch.sigmoid(ck["opacities"]),
        colors=torch.cat([ck["sh0"], ck["shN"]], dim=1),
        viewmats=vm, Ks=K, width=576, height=576, sh_degree=3)
img_ck = (r[0].clamp(0, 1).cpu().numpy() * 255).astype(np.uint8)

buf = cb.load_splat(str(SPLAT)).astype(np.float64)
sh0 = (buf[:, 3:6] - 0.5) / 0.28209479177387814
with torch.no_grad():
    r, _, _ = rasterization(
        means=torch.from_numpy(buf[:, 0:3]).float().cuda(),
        quats=torch.from_numpy(buf[:, 10:14]).float().cuda(),
        scales=torch.from_numpy(buf[:, 7:10]).float().cuda(),
        opacities=torch.from_numpy(buf[:, 6]).float().cuda(),
        colors=torch.from_numpy(sh0).float().cuda().unsqueeze(1),
        viewmats=vm, Ks=K, width=576, height=576, sh_degree=0)
img_sp = (r[0].clamp(0, 1).cpu().numpy() * 255).astype(np.uint8)

imageio.imwrite(str(OUT), np.concatenate([gt, img_ck, img_sp], axis=1))
print("wrote", OUT, "| GT | ckpt-SH3 | baked-SH0 (all @ cam0 anchor)")
print("means:", gt.mean().round(1), img_ck.mean().round(1), img_sp.mean().round(1))
