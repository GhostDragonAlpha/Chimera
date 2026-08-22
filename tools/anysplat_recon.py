"""AnySplat feed-forward multi-image -> 3DGS PLY (no COLMAP, no training).

Usage:
  .venv-anysplat/Scripts/python.exe tools/anysplat_recon.py \
      --frames capture/genbear2/frames --k 32 --skip 2 \
      --out capture/genbear2/anysplat.ply
"""
import argparse
import os
import sys

REPO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "external", "anysplat")
sys.path.insert(0, REPO)  # shims (torch_scatter, xformers) + src package

import torch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--k", type=int, default=32)
    ap.add_argument("--skip", type=int, default=0, help="skip first N frames (e.g. white-bg intros)")
    args = ap.parse_args()

    from src.model.model.anysplat import AnySplat
    from src.model.ply_export import export_ply
    from src.utils.image import process_image
    from pathlib import Path

    files = sorted(
        os.path.join(args.frames, f)
        for f in os.listdir(args.frames)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    )[args.skip:]
    step = max(1, len(files) // args.k)
    files = files[::step][: args.k]
    print(f"[anysplat] {len(files)} views from {args.frames}")

    device = torch.device("cuda")
    model = AnySplat.from_pretrained("lhjiang/anysplat").to(device).eval()
    for p in model.parameters():
        p.requires_grad = False

    images = torch.stack([process_image(f) for f in files], dim=0).unsqueeze(0).to(device)
    print(f"[anysplat] tensor {tuple(images.shape)}")

    with torch.no_grad():
        gaussians, pred_pose = model.inference((images + 1) * 0.5)

    g = gaussians
    print(f"[anysplat] {g.means[0].shape[0]} gaussians")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    export_ply(g.means[0], g.scales[0], g.rotations[0], g.harmonics[0], g.opacities[0], out)
    print(f"[anysplat] wrote {out}")

    # dump predicted poses for debugging/orientation
    import numpy as np

    np.save(str(out.with_suffix("")) + "_extrinsic.npy", pred_pose["extrinsic"][0].cpu().numpy())
    np.save(str(out.with_suffix("")) + "_intrinsic.npy", pred_pose["intrinsic"][0].cpu().numpy())


if __name__ == "__main__":
    main()
