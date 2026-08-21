"""cut_anchor.py -- source photo -> centered RGBA anchor for the SV3D orbit rings.

SV3D is image-conditioned: the anchor IS frame_00 of every ring, so it must be a
clean cutout -- object centered, whole body visible, transparent background
(gen_ring.py/generate_rings.py paste it onto black via the alpha channel).

Usage:
  .venv-ga/Scripts/python.exe tools/cut_anchor.py <in.jpg> <out.png> [--size 1024] [--margin 0.08]
"""
from __future__ import annotations

import argparse

import numpy as np
from PIL import Image


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--size", type=int, default=1024)
    ap.add_argument("--margin", type=float, default=0.08, help="fraction of canvas kept clear on each side")
    args = ap.parse_args()

    from rembg import remove

    img = Image.open(args.src).convert("RGB")
    cut = remove(img)  # RGBA
    alpha = np.asarray(cut.split()[3])
    ys, xs = np.where(alpha > 16)
    if len(ys) == 0:
        raise SystemExit("rembg produced an empty mask -- check the source photo")
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    crop = cut.crop((x0, y0, x1, y1))

    canvas = Image.new("RGBA", (args.size, args.size), (0, 0, 0, 0))
    inner = int(args.size * (1.0 - 2.0 * args.margin))
    scale = min(inner / crop.width, inner / crop.height)
    resized = crop.resize((max(1, int(crop.width * scale)), max(1, int(crop.height * scale))),
                          Image.LANCZOS)
    canvas.paste(resized, ((args.size - resized.width) // 2, (args.size - resized.height) // 2),
                 resized)
    canvas.save(args.out)
    print(f"anchor -> {args.out} (bbox {x1 - x0}x{y1 - y0}px of {img.width}x{img.height}, "
          f"fill {(alpha > 16).mean() * 100:.1f}%)")


if __name__ == "__main__":
    main()
