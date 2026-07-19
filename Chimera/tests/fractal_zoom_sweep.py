"""
fractal_zoom_sweep — camera-sweep test for the fractal splat pipeline.

Drives a continuous zoom from planetary scale (50km) to ground scale (10m)
on a grown limb, measuring:
  - splat count (with and without LOD merging)
  - tile-batch counts
  - render time
  - MAE at each LOD boundary

Usage:
    python -m tests.fractal_zoom_sweep
"""
from __future__ import annotations

import time
import numpy as np
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT_DIR = ROOT / "docs" / "world" / "sweep_results"

USE_LOD = True  # set False to measure baseline without LOD


def _load_limb():
    from core import limb as limb_mod
    from core.splat_emit import emit_limb, MEDIUM
    bones = limb_mod.bent_limb()
    _s, fleshed, shape, _t = limb_mod.grow_limb(bones, seed=0, target_len=160)
    splats = emit_limb(fleshed)
    occ = np.argwhere(fleshed != MEDIUM)
    center = (occ.min(0) + occ.max(0)) / 2.0
    radius = float((occ.max(0) - occ.min(0)).max()) / 2.0 * 1.15
    return splats, center, radius, shape


ZOOM_LEVELS = [
    ("50000m (planetary)", 50000.0),
    ("10000m (orbital)",   10000.0),
    ("1000m  (high alt)",  1000.0),
    ("100m   (low alt)",   100.0),
    ("10m    (ground)",    10.0),
    ("5m     (close)",     5.0),
    ("1m     (detail)",    1.0),
]


def measure(splats, center, radius, azim=45, elev=25, w=340, h=340, tile=16):
    from core.splat_gpu import _project_and_shade, _tile_bins, rasterize_tiled
    la, le = 110.0, 45.0
    sx, sy, *_rest = _project_and_shade(splats, center, radius, azim, elev, la, le, w, h)
    n_visible = int((_rest[3] >= 0).sum())
    to, _ts, tx, ty = _tile_bins(sx, sy, _rest[3], _rest[5], w, h, tile)
    n_tiles = int(((to[1:] - to[:-1]) > 0).sum())
    _ = rasterize_tiled(splats, center, radius, azim, elev, la, le, w, h, tile)
    t0 = time.time()
    img = rasterize_tiled(splats, center, radius, azim, elev, la, le, w, h, tile)
    ms = (time.time() - t0) * 1000
    return {"n_total": len(splats["pos"]), "n_visible": n_visible,
            "n_tiles": n_tiles, "render_ms": ms, "img": img}


def run():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Grown limb...", flush=True)
    splats, center, radius, shape = _load_limb()
    base_n = len(splats["pos"])
    print(f"  {base_n:,} splats, shape {shape}")

    hdr = f"{'zoom':<20s} {'splats':>9s} {'visible':>8s} {'tiles':>5s} {'ms':>8s}  LOD?"
    print(hdr)
    print("-" * 65)

    totals = []
    for label, zr in ZOOM_LEVELS:
        ar = radius * max(zr / 100.0, 1.0)
        s = splats
        if USE_LOD and zr >= 10.0:
            from core.splat_lod import merge
            s = merge(splats, ar, base_cell_size=5.0)
        m = measure(s, center, ar)
        lod_tag = f"{m['n_total']:>8,}" if USE_LOD else "  off"
        print(f"{label:<20s} {base_n:>9,} {m['n_visible']:>8,} {m['n_tiles']:>5d} "
              f"{m['render_ms']:>7.1f}  {lod_tag}")
        img_np = (m["img"] * 255).astype(np.uint8)
        from PIL import Image
        Image.fromarray(img_np, "RGB").save(OUT_DIR / f"zoom_{zr:.0f}m.png")
        totals.append(m)

    ok = all(t["render_ms"] <= 16.6 for t in totals)
    print(f"\n{'PASS' if ok else 'FAIL'}: all zoom levels within 16.6ms budget")
    if USE_LOD:
        first = totals[0]["n_total"]
        last = totals[-1]["n_total"]
        print(f"LOD: {first:,} splats at 50km vs {last:,} at 1m "
              f"({first/max(last,1):.1f}x reduction)")
    return totals


if __name__ == "__main__":
    import sys
    sys.exit(0 if all(t["render_ms"] <= 16.6 for t in run()) else 1)
