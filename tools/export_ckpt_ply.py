"""export_ckpt_ply.py -- gsplat simple_trainer ckpt -> standard 3DGS PLY.

For runs that forgot --save_ply: loads ckpt_{step}_rank0.pt and calls the same
gsplat.export_splats the trainer would have. Saves a 30k-step re-run.

Usage (from tools/gsplat/examples):
  ../../../.venv-gs/Scripts/python.exe ../../../tools/export_ckpt_ply.py \
      --ckpt E:/PythonChimera/capture/sv3d_real/train_out/ckpts/ckpt_29999_rank0.pt \
      --out  E:/PythonChimera/capture/sv3d_real/train_out/ply/point_cloud_29999.ply
"""
from __future__ import annotations

import argparse
import os

import torch


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    from gsplat import export_splats

    ckpt = torch.load(args.ckpt, map_location="cpu", weights_only=False)
    splats = ckpt["splats"]
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    export_splats(
        means=splats["means"],
        scales=splats["scales"],
        quats=splats["quats"],
        opacities=splats["opacities"],
        sh0=splats["sh0"],
        shN=splats["shN"],
        format="ply",
        save_to=args.out,
    )
    print(f"exported {splats['means'].shape[0]} gaussians -> {args.out}")


if __name__ == "__main__":
    main()
