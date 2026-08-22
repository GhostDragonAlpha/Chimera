"""Photometric refinement: AnySplat gaussians + predicted poses -> fit to the actual frames.

AnySplat gives geometry+poses in one pass but muted colors and holes on hard sides.
Its own authors ship a post-opt stage for this; this is our lean version (no viser,
no viewer, no COLMAP): init from the AnySplat PLY, optimize opacities/colors/scales/
quats/means against the real frames with gsplat rasterization, export a refined PLY.

Usage (.venv-gs):
  .venv-gs/Scripts/python.exe tools/anysplat_refine.py \
      --frames capture/genbear2/frames --skip 2 --k 64 \
      --ply capture/genbear2/anysplat64_crop.ply \
      --extrinsic capture/genbear2/anysplat64_extrinsic.npy \
      --intrinsic capture/genbear2/anysplat64_intrinsic.npy \
      --steps 3000 --out capture/genbear2/anysplat64_refined.ply
"""
import argparse
import os
import sys

import numpy as np
import torch
import torch.nn.functional as F

C0 = 0.28209479177387814


def logit(x):
    return torch.log(x.clamp(1e-6, 1 - 1e-6) / (1 - x.clamp(1e-6, 1 - 1e-6)))


def load_any_ply(path):
    from plyfile import PlyData
    v = PlyData.read(path)["vertex"].data
    means = np.stack([v["x"], v["y"], v["z"]], axis=1)
    f_dc = np.stack([v["f_dc_0"], v["f_dc_1"], v["f_dc_2"]], axis=1)
    rgb = np.clip(0.5 + C0 * f_dc, 0, 1)
    opac = np.clip(v["opacity"], 1e-6, 1 - 1e-6)
    log_scales = np.stack([v["scale_0"], v["scale_1"], v["scale_2"]], axis=1)
    quats = np.stack([v["rot_0"], v["rot_1"], v["rot_2"], v["rot_3"]], axis=1)
    quats = quats / np.linalg.norm(quats, axis=1, keepdims=True)
    return means, rgb, opac, log_scales, quats


def save_any_ply(path, means, rgb, opac, log_scales, quats):
    """Same layout as AnySplat export_ply (raw opacity, log scales, wxyz quat, DC only)."""
    from plyfile import PlyData, PlyElement
    f_dc = (rgb - 0.5) / C0
    names = ["x", "y", "z", "nx", "ny", "nz", "f_dc_0", "f_dc_1", "f_dc_2",
             "opacity", "scale_0", "scale_1", "scale_2", "rot_0", "rot_1", "rot_2", "rot_3"]
    n = means.shape[0]
    arr = np.empty(n, dtype=[(nm, "f4") for nm in names])
    arr["x"], arr["y"], arr["z"] = means.T
    arr["nx"], arr["ny"], arr["nz"] = 0.0, 0.0, 0.0
    arr["f_dc_0"], arr["f_dc_1"], arr["f_dc_2"] = f_dc.T
    arr["opacity"] = opac
    arr["scale_0"], arr["scale_1"], arr["scale_2"] = log_scales.T
    arr["rot_0"], arr["rot_1"], arr["rot_2"], arr["rot_3"] = quats.T
    PlyData([PlyElement.describe(arr, "vertex")], text=False).write(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", required=True)
    ap.add_argument("--ply", required=True, help="AnySplat init PLY (e.g. the orbit-cropped one)")
    ap.add_argument("--extrinsic", required=True)
    ap.add_argument("--intrinsic", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--skip", type=int, default=0)
    ap.add_argument("--k", type=int, default=64, help="must match the K used for the npy poses")
    ap.add_argument("--steps", type=int, default=3000)
    ap.add_argument("--res", type=int, default=448)
    ap.add_argument("--freeze-means", action="store_true")
    args = ap.parse_args()

    dev = torch.device("cuda")
    R = args.res

    # --- data: frames through the exact AnySplat transform (square: pure resize) ---
    from PIL import Image
    files = sorted(
        os.path.join(args.frames, f)
        for f in os.listdir(args.frames)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    )[args.skip:]
    step = max(1, len(files) // args.k)
    files = files[::step][: args.k]
    gt = torch.stack([
        torch.from_numpy(np.asarray(Image.open(f).convert("RGB").resize((R, R)), dtype=np.float32) / 255.0)
        for f in files
    ])  # [K,H,W,3]
    print(f"[refine] {len(files)} views at {R}x{R}")

    # --- cameras: AnySplat c2w -> gsplat viewmats (w2c); intrinsics normalized -> pixels ---
    ext = torch.from_numpy(np.load(args.extrinsic)).double()  # [K,4,4] cam2world
    viewmats = torch.inverse(ext).float().to(dev)
    Ks = torch.from_numpy(np.load(args.intrinsic)).float()  # [K,3,3] normalized
    Ks = Ks.clone()
    Ks[:, 0, :] *= R
    Ks[:, 1, :] *= R
    Ks = Ks.to(dev)
    print(f"[refine] fx~{Ks[0,0,0]:.1f} cx~{Ks[0,0,2]:.1f}")

    # --- init params ---
    means, rgb, opac, logs, quats = load_any_ply(args.ply)
    n = len(means)
    print(f"[refine] init {n} gaussians")
    p_means = torch.nn.Parameter(torch.from_numpy(means).float().to(dev))
    p_quats = torch.nn.Parameter(torch.from_numpy(quats).float().to(dev))
    p_logs = torch.nn.Parameter(torch.from_numpy(logs).float().to(dev))
    p_opac = torch.nn.Parameter(logit(torch.from_numpy(opac).float()).to(dev))
    p_rgb = torch.nn.Parameter(logit(torch.from_numpy(rgb).float()).to(dev))

    params = [
        {"params": p_rgb, "lr": 5e-3, "name": "rgb"},
        {"params": p_opac, "lr": 5e-3, "name": "opac"},
        {"params": p_logs, "lr": 5e-4, "name": "scales"},
        {"params": p_quats, "lr": 5e-4, "name": "quats"},
    ]
    if not args.freeze_means:
        params.append({"params": p_means, "lr": 2e-5, "name": "means"})
    opt = torch.optim.Adam(params)

    from gsplat import rasterization
    from torchmetrics.image import StructuralSimilarityIndexMeasure
    ssim = StructuralSimilarityIndexMeasure(data_range=1.0).to(dev)

    K = len(files)
    for it in range(args.steps):
        i = np.random.randint(K)
        viewmat = viewmats[i: i + 1]
        Kmat = Ks[i: i + 1]
        colors = torch.sigmoid(p_rgb)
        render, _, _ = rasterization(
            means=p_means, quats=F.normalize(p_quats, dim=-1), scales=torch.exp(p_logs),
            opacities=torch.sigmoid(p_opac), colors=colors,
            viewmats=viewmat, Ks=Kmat, width=R, height=R, packed=False,
        )
        img = render[0].permute(2, 0, 1).unsqueeze(0)  # [1,3,H,W]
        tgt = gt[i].permute(2, 0, 1).unsqueeze(0).to(dev)
        l1 = F.l1_loss(img, tgt)
        s = ssim(img, tgt)
        loss = l1 + 0.2 * (1.0 - s)
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        if (it + 1) % 200 == 0:
            mse = F.mse_loss(img, tgt).item()
            psnr = -10.0 * np.log10(max(mse, 1e-10))
            print(f"[refine] step {it+1}/{args.steps} L1 {l1.item():.4f} SSIM {s.item():.4f} PSNR {psnr:.2f}")

    with torch.no_grad():
        means_o = p_means.cpu().numpy()
        rgb_o = torch.sigmoid(p_rgb).cpu().numpy()
        opac_o = torch.sigmoid(p_opac).cpu().numpy()
        logs_o = p_logs.cpu().numpy()
        quats_o = F.normalize(p_quats, dim=-1).cpu().numpy()
    save_any_ply(args.out, means_o, rgb_o, opac_o, logs_o, quats_o)
    print(f"[refine] wrote {args.out}")


if __name__ == "__main__":
    main()
