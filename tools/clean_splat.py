"""clean_splat.py — remove reconstruction junk from a trained 3DGS .splat cloud.

Why this stage exists: a cloud trained from an AI-generated orbit video carries junk the
loss tolerated because the video background was near-black: gray smoke hugging the
silhouette, near-zero-width needle splats (aniso > 1e5), a dense dark glossy shell behind
the subject, and warm "ember" specks. On a black background at the training views they are
invisible; the engine's depth sort + free camera expose them, and skinning (LBS) stretches
them into streaks. Eye-verified on genbear 2026-08-19 (docs/SESSION_LOG_2026-08-19.md).

Filters (all thresholds measured, not guessed — see the session log):
  smoke    luminance < 0.08 AND anisotropy > 8        (dark elongated haze)
  needles  anisotropy > 150 AND luminance < 0.35      (degenerate thin streaks)
  big      max scale axis > 0.02                      (oversized background billboards)
  embers   red-dominant specks / saturated off-warm hue (bear palette is warm hue 0..0.16)
  sparse   fewer than 8 neighbours within r=0.04       (isolated floaters)
  box cut  optional --cut-box xmin xmax ymin ymax zmax (eye-directed; per-object — the
           genbear needed one behind/above the head where junk was as dense as real fur)

Every filter was confirmed by render-only-the-suspects / render-without-them frames
through the live engine before removal. The box cut is the ONE subjective step: render
the zone alone first (`--show-zone`) and confirm it draws nothing recognisable.

Usage:
  python tools/clean_splat.py in.splat out.splat [--cut-box -0.5 0.12 0.15 0.6 -0.6 -0.02] \
      [--weights skin_weights.npz --weights-out skin_weights_clean.npz] [--show-zone]
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ChimeraEngine"))
import cpp_bridge as cb  # noqa: E402

LUM_W = np.array([0.2126, 0.7152, 0.0722])


def neighbour_counts(pos: np.ndarray, r: float = 0.04) -> np.ndarray:
    key = np.floor(pos / r).astype(np.int64)
    cellmap = defaultdict(list)
    for i, k in enumerate(map(tuple, key)):
        cellmap[k].append(i)
    counts = np.zeros(len(pos), dtype=np.int32)
    r2 = r * r
    for c, idxs in cellmap.items():
        cand = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    cand += cellmap.get((c[0] + dx, c[1] + dy, c[2] + dz), [])
        if not cand:
            continue
        pp = pos[np.array(cand)]
        for i in idxs:
            counts[i] = int((((pp - pos[i]) ** 2).sum(1) < r2).sum())
    return counts


def junk_mask(buf: np.ndarray, cut_box: list[float] | None) -> dict[str, np.ndarray]:
    pos = buf[:, 0:3].astype(np.float64)
    rgb = buf[:, 3:6].astype(np.float64)
    scale = buf[:, 7:10]
    lum = rgb @ LUM_W
    s = np.sort(scale, axis=1)
    aniso = s[:, 2] / np.maximum(s[:, 0], 1e-8)
    mx, mn = rgb.max(1), rgb.min(1)
    sat = np.where(mx > 1e-4, (mx - mn) / np.maximum(mx, 1e-4), 0)
    d = np.maximum(mx - mn, 1e-8)
    hue = np.where(mx == rgb[:, 0], ((rgb[:, 1] - rgb[:, 2]) / d) % 6,
                   np.where(mx == rgb[:, 1], (rgb[:, 2] - rgb[:, 0]) / d + 2,
                            (rgb[:, 0] - rgb[:, 1]) / d + 4)) / 6.0
    masks = {
        "smoke":   (lum < 0.08) & (aniso > 8),
        "needles": (aniso > 150) & (lum < 0.35),
        "big":     s[:, 2] > 0.02,
        "embers":  ((rgb[:, 0] > 0.4) & (rgb[:, 0] > 2.2 * np.maximum(rgb[:, 1], 1e-4))
                    & (rgb[:, 0] > 2.2 * np.maximum(rgb[:, 2], 1e-4)))
                   | ((sat > 0.35) & ~((hue > 0.0) & (hue < 0.16))),
        "sparse":  neighbour_counts(pos) < 8,
    }
    if cut_box:
        x0, x1, y0, y1, z0, z1 = cut_box
        masks["box"] = ((pos[:, 0] > x0) & (pos[:, 0] < x1) & (pos[:, 1] > y0)
                        & (pos[:, 1] < y1) & (pos[:, 2] > z0) & (pos[:, 2] < z1))
    return masks


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("splat")
    ap.add_argument("out", nargs="?", default=None)
    ap.add_argument("--cut-box", nargs=6, type=float, default=None,
                    metavar=("X0", "X1", "Y0", "Y1", "Z0", "Z1"))
    ap.add_argument("--weights", default=None, help="skin_weights.npz aligned with the input splat")
    ap.add_argument("--weights-out", default=None)
    ap.add_argument("--show-zone", action="store_true",
                    help="don't write anything; save the cut-box zone as a standalone .splat "
                         "(<out>.zone.splat) so you can render it alone and eye-check it")
    a = ap.parse_args()

    buf = cb.load_splat(a.splat)
    masks = junk_mask(buf, a.cut_box)
    drop = np.zeros(len(buf), dtype=bool)
    for name, m in masks.items():
        print(f"  {name:8s} {int(m.sum()):6d}")
        drop |= m
    keep = ~drop
    print(f"  TOTAL drop {int(drop.sum())} / {len(buf)} -> keep {int(keep.sum())}")

    if a.show_zone:
        if "box" not in masks:
            print("--show-zone needs --cut-box")
            return 1
        cb.save_splat(str(a.out) + ".zone.splat", buf[masks["box"]])
        print("zone splat saved for eye-check")
        return 0

    if not a.out:
        print("no output path given; dry run")
        return 0
    cb.save_splat(a.out, buf[keep])
    print("saved", a.out)
    if a.weights and a.weights_out:
        wz = np.load(a.weights)
        np.savez(a.weights_out,
                 bone0=wz["bone0"][keep], w0=wz["w0"][keep],
                 bone1=wz["bone1"][keep], w1=wz["w1"][keep], bones=wz["bones"])
        print("weights masked ->", a.weights_out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
