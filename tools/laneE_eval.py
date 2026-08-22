"""tools/laneE_eval.py

Evaluate the refined PLY against the enhanced views with the exact Lane E poses.
Renders every view at the same 512x512 square resolution used during refinement and
reports mean PSNR / SSIM / L1.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from plyfile import PlyData
from gsplat import rasterization
from torchmetrics.image import StructuralSimilarityIndexMeasure

ROOT = Path(__file__).resolve().parent.parent
C0 = 0.28209479177387814
R = 512


def load_ply(path: str):
    v = PlyData.read(path)["vertex"].data
    means = np.stack([v["x"], v["y"], v["z"]], axis=1)
    rgb = np.clip(0.5 + C0 * np.stack([v["f_dc_0"], v["f_dc_1"], v["f_dc_2"],], axis=1), 0, 1)
    opac = np.clip(v["opacity"], 1e-6, 1 - 1e-6)
    logs = np.stack([v["scale_0"], v["scale_1"], v["scale_2"]], axis=1)
    quats = np.stack([v["rot_0"], v["rot_1"], v["rot_2"], v["rot_3"]], axis=1)
    quats = quats / np.linalg.norm(quats, axis=1, keepdims=True)
    return means, rgb, opac, logs, quats


def main() -> int:
    meta = json.loads((ROOT / "capture/genbear3/laneE_views/laneE_views.json").read_text())
    ext = np.load(ROOT / "capture/genbear3/laneE_extrinsic.npy").astype(np.float64)
    K = np.load(ROOT / "capture/genbear3/laneE_intrinsic.npy").copy()
    K[:, 0, :] *= R
    K[:, 1, :] *= R

    means, rgb, opac, logs, quats = load_ply(str(ROOT / "models/genbear3/laneE_refined.ply"))
    dev = torch.device("cuda")
    means_t = torch.from_numpy(means).float().to(dev)
    rgb_t = torch.from_numpy(rgb).float().to(dev)
    opac_t = torch.from_numpy(opac).float().to(dev)
    logs_t = torch.from_numpy(logs).float().to(dev)
    quats_t = torch.from_numpy(quats).float().to(dev)

    viewmats = torch.from_numpy(np.linalg.inv(ext)).float().to(dev)
    Ks = torch.from_numpy(K).float().to(dev)
    ssim = StructuralSimilarityIndexMeasure(data_range=1.0).to(dev)

    img_dir = ROOT / "capture/genbear3/laneE_views_enhanced"
    l1s, mses, ssims = [], [], []
    for i, m in enumerate(meta):
        render, _, _ = rasterization(
            means=means_t,
            quats=F.normalize(quats_t, dim=-1),
            scales=torch.exp(logs_t),
            opacities=opac_t,
            colors=rgb_t,
            viewmats=viewmats[i:i+1],
            Ks=Ks[i:i+1],
            width=R,
            height=R,
            packed=False,
            backgrounds=torch.zeros((1, 3), device=dev),
        )
        img = render[0].permute(2, 0, 1).unsqueeze(0)
        tgt = torch.from_numpy(np.asarray(
            Image.open(img_dir / m["file"]).convert("RGB").resize((R, R)), dtype=np.float32) / 255.0
        ).permute(2, 0, 1).unsqueeze(0).to(dev)
        l1s.append(F.l1_loss(img, tgt).item())
        mses.append(F.mse_loss(img, tgt).item())
        ssims.append(ssim(img, tgt).item())

    l1 = float(np.mean(l1s))
    psnr = float(-10 * np.log10(max(np.mean(mses), 1e-10)))
    ssim_val = float(np.mean(ssims))
    print(f"views={len(meta)}  L1={l1:.4f}  PSNR={psnr:.2f}  SSIM={ssim_val:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
