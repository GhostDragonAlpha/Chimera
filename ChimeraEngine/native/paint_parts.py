"""paint_parts.py — reference-authored part painting for a 3DGS cloud.

WHY THIS EXISTS (operator, 2026-08-19): the koala source is exact geometry but has no real
appearance — the mesh2splat LOD green is a color CODE, and the original Thingiverse upload
(thing:182225, recovered from archive.org) was a BLUE 3D-print model; no textured version
of this koala has ever existed. "No reference, no verdict": the material reference here is
a human-authored palette sampled from REAL koala photography (Phascolarctos cinereus —
grey dorsal fur, cream ventral/inner-ear, black nose, dark muzzle), applied per SECTIONED
PART. This is workflow step 4 (REAPPLY) run with the reference external to the splat.

THEORY (Rule 0):
  STATEMENT  — a part-painted cloud with a fur value-noise term reads as the animal's
               coloring without any per-splat texture: parts carry the hue, the noise
               carries the fur.
  PREDICTION — the eye, asked "what animal and what colors", reports a grey/cream koala.
  FALSIFIER  — if the eye still reports green/flat plastic, the noise term or the palette
               is wrong, not the geometry.

The noise is DETERMINISTIC (seeded), low-amplitude luminance jitter — fur, not confetti.

Usage (from the repo root):
  python ChimeraEngine/native/paint_parts.py models/koala/koala_500k_front.splat \
      --dir models/koala/section --palette models/koala/rig/palette_koala.json \
      --out models/koala/koala_500k_painted.splat
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent
_CHIMERA_ENGINE = _HERE.parent
if str(_CHIMERA_ENGINE) not in sys.path:
    sys.path.insert(0, str(_CHIMERA_ENGINE))

import cpp_bridge as cb          # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("target", help="path to the .splat")
    ap.add_argument("--dir", required=True, help="section workdir (parts.json, part_assignment.npy)")
    ap.add_argument("--palette", required=True, help="JSON: part -> [r,g,b] 0..1, optional '_noise': amplitude")
    ap.add_argument("--out", required=True, help="output .splat path")
    a = ap.parse_args()

    workdir = Path(a.dir)
    parts = json.loads((workdir / "parts.json").read_text(encoding="utf-8"))["parts"]
    label = np.load(workdir / "part_assignment.npy")
    palette = json.loads(Path(a.palette).read_text(encoding="utf-8"))
    noise_amp = float(palette.get("_noise", 0.06))

    buf = cb.load_splat(a.target)
    n = len(buf)
    rng = np.random.default_rng(7)
    noise = 1.0 + noise_amp * rng.standard_normal(n)          # per-splat luminance jitter
    noise = np.clip(noise, 1.0 - 3 * noise_amp, 1.0 + 3 * noise_amp)

    # KEEP the source's baked shading: the LOD green carries baked lambert in its luminance.
    # s_i = per-splat luminance relative to its PART's median — the face's lighter oval and
    # the under-body shadow survive the repaint; the hue does not.
    lum = 0.2126 * buf[:, 3] + 0.7152 * buf[:, 4] + 0.0722 * buf[:, 5]
    shade = np.ones(n)
    for i in range(len(parts)):
        sel = label == i
        if sel.any():
            med = float(np.median(lum[sel]))
            if med > 1e-6:
                shade[sel] = lum[sel] / med
    shade = np.clip(shade, 0.55, 1.6)          # bound: shading, not holes

    default_rgb = np.array(palette.get("_default", [0.45, 0.42, 0.40]))
    rgb = np.tile(default_rgb, (n, 1))
    for i, name in enumerate(parts):
        if name in palette:
            rgb[label == i] = np.array(palette[name], dtype=np.float64)
    rgb = np.clip(rgb * shade[:, None] * noise[:, None], 0.0, 1.0)

    out = buf.copy()
    out[:, 3:6] = rgb.astype(np.float32)
    out_path = Path(a.out)
    cb.save_splat(out_path, out)
    print(f"painted {n} splats ({len(palette) - 2} part colors, noise ±{noise_amp}) -> {out_path}")


if __name__ == "__main__":
    main()
