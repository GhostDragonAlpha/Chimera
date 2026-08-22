"""Hypothesis test verdict: one-pass (eq-only, 21 views) vs mixed (101 views, 5 passes).
Renders BOTH ckpts at the eq-ring held-out views (test_every=8 -> indices 0, 8, 16,
same physical cameras in both datasets) and reports PSNR vs GT per view.
"""
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parent.parent
EX = ROOT / "tools" / "gsplat" / "examples"
sys.path.insert(0, str(EX))

from datasets.colmap import Dataset, Parser  # noqa: E402
from gsplat.rendering import rasterization  # noqa: E402

CASES = [
    ("eq-only(1 pass, 21v)", ROOT / "capture/sv3d_eqonly/data",
     ROOT / "capture/sv3d_eqonly/train_out/ckpts/ckpt_29999_rank0.pt"),
    ("mixed(5 passes, 101v)", ROOT / "capture/sv3d_bear/data5",
     ROOT / "capture/sv3d_bear/train_out5/ckpts/ckpt_29999_rank0.pt"),
]
TEST_IDX = [0, 8, 16]  # eq frames 00/08/16 in both datasets (eq ring listed first)


def psnr(a, b):
    mse = np.mean((a.astype(np.float64) / 255 - b.astype(np.float64) / 255) ** 2)
    return -10 * np.log10(max(mse, 1e-12))


for name, data, ckpt in CASES:
    parser = Parser(data_dir=str(data), factor=1, normalize=True, test_every=8)
    ds = Dataset(parser, split="train")
    ds.indices = np.arange(len(parser.image_names))
    ck = torch.load(ckpt, map_location="cuda", weights_only=False)["splats"]
    scores = []
    for i in TEST_IDX:
        item = ds[i]
        c2w = item["camtoworld"].unsqueeze(0).cuda()
        K = item["K"].unsqueeze(0).cuda()
        vm = torch.linalg.inv(c2w)
        gt = item["image"].numpy().astype(np.uint8)
        with torch.no_grad():
            r, _, _ = rasterization(
                means=ck["means"], quats=F.normalize(ck["quats"], dim=-1),
                scales=torch.exp(ck["scales"]), opacities=torch.sigmoid(ck["opacities"]),
                colors=torch.cat([ck["sh0"], ck["shN"]], dim=1),
                viewmats=vm, Ks=K, width=576, height=576, sh_degree=3)
        img = (r[0].clamp(0, 1).cpu().numpy() * 255).astype(np.uint8)
        scores.append(psnr(img, gt))
    print(f"{name}: PSNR per held-out eq view {[round(s, 2) for s in scores]} "
          f"| mean {np.mean(scores):.2f} dB | splats {len(ck['means'])}")
