"""Render a converted .splat through gsplat's own rasterizer from a known dataset camera.

Decisive A/B: if this render matches the trainer's val renders, the conversion is
faithful and any confetti lives in the viewer/engine path. If it's confetti here too,
the conversion (ply_to_splat / save_splat quantization) is the culprit.
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
sys.path.insert(0, str(ROOT / "ChimeraEngine" / "native"))

from datasets.colmap import Dataset, Parser  # noqa: E402
from gsplat.rendering import rasterization  # noqa: E402
import cpp_bridge as cb  # noqa: E402

DATA = ROOT / "capture" / "sv3d_bear" / "data5"
SPLAT = ROOT / "models" / "genbear3" / "sv3d5_baked.splat"
OUT = ROOT / ".tmp" / "ab_baked_gsplat.png"
VIEW_IDX = 2


def main():
    buf = cb.load_splat(str(SPLAT)).astype(np.float64)
    print("splat:", buf.shape, "alpha range", buf[:, 6].min(), buf[:, 6].max())
    means = torch.from_numpy(buf[:, 0:3]).float().cuda()
    colors = torch.from_numpy(buf[:, 3:6]).float().cuda().unsqueeze(1)  # (N,1,3) DC only
    opac = torch.from_numpy(buf[:, 6]).float().cuda()
    scales = torch.from_numpy(buf[:, 7:10]).float().cuda()
    quats = torch.from_numpy(buf[:, 10:14]).float().cuda()

    parser = Parser(data_dir=str(DATA), factor=1, normalize=True, test_every=8)
    ds = Dataset(parser, split="train")
    ds.indices = np.arange(len(parser.image_names))
    item = ds[VIEW_IDX]
    c2w = item["camtoworld"].unsqueeze(0).cuda()
    K = item["K"].unsqueeze(0).cuda()
    h = w = 576

    with torch.no_grad():
        render, _, _ = rasterization(
            means=means, quats=quats, scales=scales, opacities=opac,
            colors=colors, viewmats=torch.linalg.inv(c2w), Ks=K,
            width=w, height=h, sh_degree=0, backgrounds=None,
        )
    img = (render[0].clamp(0, 1).cpu().numpy() * 255).astype(np.uint8)
    imageio.imwrite(str(OUT), img)
    print("wrote", OUT)


if __name__ == "__main__":
    sys.exit(main())
