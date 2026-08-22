"""Render all training views from a gsplat checkpoint and report per-view PSNR.

Usage: .venv-gs/Scripts/python.exe tools/audit_render_views.py
Identifies which supervision views the trained model cannot fit.
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

DATA = ROOT / "capture" / "sv3d_bear" / "data5"
CKPT = ROOT / "capture" / "sv3d_bear" / "train_out5" / "ckpts" / "ckpt_29999_rank0.pt"


def main():
    parser = Parser(data_dir=str(DATA), factor=1, normalize=True, test_every=8)
    ds = Dataset(parser, split="train")
    ds.indices = np.arange(len(parser.image_names))  # audit ALL views
    ckpt = torch.load(CKPT, map_location="cuda", weights_only=False)
    sd = ckpt["splats"]
    means = sd["means"].cuda()
    quats = F.normalize(sd["quats"].cuda(), dim=-1)
    scales = torch.exp(sd["scales"].cuda())
    opac = torch.sigmoid(sd["opacities"].cuda())
    sh0 = sd["sh0"].cuda()
    shN = sd["shN"].cuda()
    colors = torch.cat([sh0, shN], dim=1)

    print(f"{'idx':>4} {'name':>10} {'psnr':>6}")
    psnrs = []
    with torch.no_grad():
        for i in range(len(ds)):
            item = ds[i]
            c2w = item["camtoworld"].unsqueeze(0).cuda()
            K = item["K"].unsqueeze(0).cuda()
            img = item["image"].cuda().permute(2, 0, 1).unsqueeze(0) / 255.0
            h, w = img.shape[2], img.shape[3]
            render, _, _ = rasterization(
                means=means, quats=quats, scales=scales, opacities=opac,
                colors=colors, viewmats=torch.linalg.inv(c2w), Ks=K,
                width=w, height=h, sh_degree=3, backgrounds=None,
            )
            mse = F.mse_loss(render.permute(0, 3, 1, 2).clamp(0, 1), img)
            psnr = -10 * torch.log10(mse)
            psnrs.append(float(psnr))
            name = parser.image_names[i] if hasattr(parser, "image_names") else str(i)
            print(f"{i:>4} {name:>12} {psnr:6.2f}")
    arr = np.array(psnrs)
    print(f"\nmean={arr.mean():.2f}  min={arr.min():.2f} (idx {arr.argmin()})  "
          f"max={arr.max():.2f} (idx {arr.argmax()})")
    # per-ring means (21 per ring in order eq, top, bot)
    for r, name in enumerate(["eq", "top", "bot"]):
        seg = arr[r * 21:(r + 1) * 21]
        print(f"ring {name:>3}: mean={seg.mean():.2f} min={seg.min():.2f} max={seg.max():.2f}")


if __name__ == "__main__":
    sys.exit(main())
