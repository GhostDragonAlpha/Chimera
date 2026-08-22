"""Decisive chain validation: render the UNNORMALIZED baked splat (sv3d5_world.splat)
from the EXACT original-world camera of a real training view (normalize=False),
side by side with the GT frame. If this render matches the GT bear, the
unnormalize+bake chain is correct and mush elsewhere = supervision sparsity.
"""
import sys
from pathlib import Path

import imageio
import numpy as np
import torch

ROOT = Path(__file__).resolve().parent.parent
EX = ROOT / "tools" / "gsplat" / "examples"
sys.path.insert(0, str(EX))
sys.path.insert(0, str(ROOT / "ChimeraEngine"))

from datasets.colmap import Dataset, Parser  # noqa: E402
from gsplat.rendering import rasterization  # noqa: E402
import cpp_bridge as cb  # noqa: E402

DATA = ROOT / "capture" / "sv3d_bear" / "data5"
SPLAT = ROOT / "models" / "genbear3" / "sv3d5_world.splat"
OUT = ROOT / ".tmp" / "chain_validate.png"
VIEW_IDX = 0  # frame_00 of eq ring = the anchor view

parser = Parser(data_dir=str(DATA), factor=1, normalize=False, test_every=8)
ds = Dataset(parser, split="train")
ds.indices = np.arange(len(parser.image_names))
item = ds[VIEW_IDX]
c2w = item["camtoworld"].unsqueeze(0).cuda()
K = item["K"].unsqueeze(0).cuda()
vm = torch.linalg.inv(c2w)
gt = item["image"].numpy().astype(np.uint8)
print("cam0 position (orig world):", c2w[0, :3, 3].cpu().numpy())
print("K:", K[0].cpu().numpy().diagonal())

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
img = (r[0].clamp(0, 1).cpu().numpy() * 255).astype(np.uint8)

imageio.imwrite(str(OUT), np.concatenate([gt, img], axis=1))
print("wrote", OUT, "| layout: GT frame_00 | world-splat render from exact cam0")
print("means: GT", gt.mean().round(1), "render", img.mean().round(1))
