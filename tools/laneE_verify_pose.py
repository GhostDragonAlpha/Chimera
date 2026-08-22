"""tools/laneE_verify_pose.py

Render the oriented splat with gsplat using the computed Lane E pose for one view
and compare to the Playwright screenshot from the HTTP viewer. This catches
sign/dimension mismatches before the expensive refinement.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from gsplat import rasterization

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ChimeraEngine"))


def load_raw_splat(path: str):
    """Load a .splat file as raw arrays in the viewer's native (orient=0) frame."""
    raw = np.fromfile(path, dtype=np.uint8)
    n = len(raw) // 32
    rec = raw[: n * 32].reshape(n, 32)
    pos = rec[:, 0:12].view(np.float32).reshape(n, 3).astype(np.float64)
    scale = np.exp(rec[:, 12:24].view(np.float32).reshape(n, 3).astype(np.float64))
    rgba = rec[:, 24:28].astype(np.float64)
    rgb = rgba[:, :3] / 255.0
    alpha = rgba[:, 3:4] / 255.0
    rot_u8 = rec[:, 28:32].astype(np.float64)
    rot = (rot_u8 - 128.0) / 128.0
    rot = rot / np.linalg.norm(rot, axis=1, keepdims=True)
    return pos, rot, scale, rgb, alpha.squeeze(-1)


def main() -> int:
    splat_path = ROOT / "models/genbear3/laneD_diffsplat.splat"
    meta_path = ROOT / "capture/genbear3/laneE_views/laneE_views.json"
    extrinsic_path = ROOT / "capture/genbear3/laneE_extrinsic.npy"
    intrinsic_path = ROOT / "capture/genbear3/laneE_intrinsic.npy"
    view_dir = ROOT / "capture/genbear3/laneE_views"

    meta = json.loads(meta_path.read_text())
    # Pick a few representative views: front, side, top.
    test_indices = [0, 2, 9, 16]
    extrinsic = np.load(extrinsic_path).astype(np.float64)
    intrinsic = np.load(intrinsic_path).astype(np.float64)

    pos, quat, scale, rgb, alpha = load_raw_splat(str(splat_path))
    print(f"loaded {len(pos)} splats from {splat_path}")

    dev = torch.device("cuda")
    means_t = torch.from_numpy(pos).float().to(dev)
    quats_t = torch.from_numpy(quat).float().to(dev)
    scales_t = torch.from_numpy(scale).float().to(dev)
    colors_t = torch.from_numpy(rgb).float().to(dev)
    opacities_t = torch.from_numpy(alpha).float().to(dev)

    W, H = 1280, 720

    for idx in test_indices:
        m = meta[idx]
        c2w = extrinsic[idx]
        viewmat = np.linalg.inv(c2w).astype(np.float32)
        K = intrinsic[idx].copy()
        K[0, :] *= W
        K[1, :] *= H

        render, _, _ = rasterization(
            means=means_t,
            quats=F.normalize(quats_t, dim=-1),
            scales=scales_t,
            opacities=opacities_t,
            colors=colors_t,
            viewmats=torch.from_numpy(viewmat).unsqueeze(0).to(dev),
            Ks=torch.from_numpy(K).unsqueeze(0).float().to(dev),
            width=W,
            height=H,
            packed=False,
            backgrounds=torch.zeros((1, 3), device=dev),
        )
        img = render[0].detach().cpu().numpy()  # H,W,3
        img_u8 = (np.clip(img, 0, 1) * 255).astype(np.uint8)
        out_png = ROOT / f".tmp/laneE_verify_view_{idx:03d}.png"
        out_png.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(img_u8).save(out_png)

        ref = np.asarray(Image.open(view_dir / m["file"]).convert("RGB"), dtype=np.float32) / 255.0
        diff = np.abs(img - ref).mean()
        print(f"view {idx:03d} az={m['az']:.3f} el={m['el']:.3f} mean_abs_diff={diff:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
