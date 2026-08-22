"""Side-by-side: ckpt (SH3) vs baked .splat (SH0) rendered by gsplat from the same camera."""
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
OUT = ROOT / ".tmp" / "ab_side_by_side.png"
VIEW_IDX = 2

parser = Parser(data_dir=str(DATA), factor=1, normalize=True, test_every=8)
ds = Dataset(parser, split="train")
ds.indices = np.arange(len(parser.image_names))
item = ds[VIEW_IDX]
c2w = item["camtoworld"].unsqueeze(0).cuda()
K = item["K"].unsqueeze(0).cuda()
vm = torch.linalg.inv(c2w)
gt = item["image"].numpy().astype(np.uint8)

ck = torch.load(CKPT, map_location="cuda", weights_only=False)["splats"]
with torch.no_grad():
    r_ck, _, _ = rasterization(
        means=ck["means"], quats=F.normalize(ck["quats"], dim=-1),
        scales=torch.exp(ck["scales"]), opacities=torch.sigmoid(ck["opacities"]),
        colors=torch.cat([ck["sh0"], ck["shN"]], dim=1),
        viewmats=vm, Ks=K, width=576, height=576, sh_degree=3)
img_ck = (r_ck[0].clamp(0, 1).cpu().numpy() * 255).astype(np.uint8)

buf = cb.load_splat(str(SPLAT)).astype(np.float64)
rgb = buf[:, 3:6]
sh0_equiv = (rgb - 0.5) / 0.28209479177387814  # gsplat evaluates C0*c + 0.5 even at sh_degree=0
with torch.no_grad():
    r_sp, _, _ = rasterization(
        means=torch.from_numpy(buf[:, 0:3]).float().cuda(),
        quats=torch.from_numpy(buf[:, 10:14]).float().cuda(),
        scales=torch.from_numpy(buf[:, 7:10]).float().cuda(),
        opacities=torch.from_numpy(buf[:, 6]).float().cuda(),
        colors=torch.from_numpy(sh0_equiv).float().cuda().unsqueeze(1),
        viewmats=vm, Ks=K, width=576, height=576, sh_degree=0)
img_sp = (r_sp[0].clamp(0, 1).cpu().numpy() * 255).astype(np.uint8)

imageio.imwrite(str(OUT), np.concatenate([gt, img_ck, img_sp], axis=1))
print("wrote", OUT, "| layout: GT | ckpt-SH3 | baked-splat-SH0")
print("render means: GT", gt.mean(), "ckpt", img_ck.mean(), "splat", img_sp.mean())
