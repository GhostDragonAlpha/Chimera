"""reapply_materials.py — REAPPLY step: paint the extracted material genomes back onto the bear.

THEORY (Rule 0):
  STATEMENT  — the bear's see-through back is a model-generation asymmetry: back-side splats
               carry lower opacity and/or different sizes than front-side splats of the SAME
               material. A material is a distribution, not a position — so repainting every
               splat to its material's (front-measured) genome makes front and back agree.
  PREDICTION — before repaint, per-material back opacity/log_size differs measurably from
               front; after repaint they are identical by construction and the rendered back
               is visibly opaque.
  FALSIFIER  — if the pre-repaint front/back distributions already agree, the transparency
               cause is elsewhere (splat density, not per-splat genome) and this repaint
               cannot fix it.

What it does (THE_GAME-ASSET_WORKFLOW step 4):
  1. read the raw .splat records (32 B/splat — positions and rotations are NOT touched)
  2. per splat, by material assignment:
       color  <- material mean linear RGB
       scale  <- scaled so geomean(sx,sy,sz) == exp(material front mean log_size)
                 (anisotropy preserved: scale *= target_geo / current_geo)
       alpha  <- material FRONT mean opacity (the back inherits the front's coverage)
  3. write a new .splat; print the front/back distributions before and after (the GATE data).

  python ChimeraEngine/native/reapply_materials.py <splat> <materials.json> <assignment.npy> --out <splat>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from cpp_bridge import SPLAT_ORIENT  # noqa: E402  (oriented frame defines front/back: front = +z)


def _front_mask(pos_raw: np.ndarray) -> np.ndarray:
    """Front = the half facing the default camera (theta=pi -> +z in the oriented frame)."""
    world = pos_raw @ SPLAT_ORIENT.T
    return world[:, 2] > 0


def _stats(scale: np.ndarray, alpha: np.ndarray, labels: np.ndarray, names: list[str],
           front: np.ndarray) -> dict:
    geo = np.cbrt(np.maximum(scale[:, 0] * scale[:, 1] * scale[:, 2], 1e-30))
    log_size = np.log(geo)
    out = {}
    for j, name in enumerate(names):
        sel = labels == j
        for side, m in (("front", sel & front), ("back", sel & ~front)):
            if m.any():
                out[f"{name}/{side}"] = {
                    "n": int(m.sum()),
                    "opacity": float(alpha[m].mean()),
                    "log_size": float(log_size[m].mean()),
                }
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("splat")
    ap.add_argument("materials")
    ap.add_argument("assignment")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    mats = json.loads(Path(args.materials).read_text(encoding="utf-8"))
    names = list(mats.keys())
    labels = np.load(args.assignment).astype(np.int64)

    raw = np.fromfile(args.splat, dtype=np.uint8)
    n = len(raw) // 32
    if len(labels) != n:
        raise SystemExit(f"assignment has {len(labels)} rows but splat has {n}")
    rec = raw[: n * 32].reshape(n, 32).copy()

    pos = rec[:, 0:12].view(np.float32).reshape(n, 3).astype(np.float64)
    scale = rec[:, 12:24].view(np.float32).reshape(n, 3).astype(np.float64)
    rgba = rec[:, 24:28].astype(np.float64) / 255.0
    front = _front_mask(pos)

    print("== BEFORE ==")
    for k, v in _stats(scale, rgba[:, 3], labels, names, front).items():
        print(f"  {k}: n={v['n']} opacity={v['opacity']:.4f} log_size={v['log_size']:.4f}")

    # per-material FRONT means — the genome the whole material is repainted to
    geo = np.cbrt(np.maximum(scale[:, 0] * scale[:, 1] * scale[:, 2], 1e-30))
    log_size = np.log(geo)
    for j, name in enumerate(names):
        sel = labels == j
        fsel = sel & front
        ref = fsel if fsel.any() else sel
        target_alpha = float(rgba[ref, 3].mean())
        target_log_size = float(log_size[ref].mean())
        color = np.array(mats[name]["color"], dtype=np.float64)

        rgba[sel, 0:3] = color
        rgba[sel, 3] = target_alpha
        scale[sel] *= np.exp(target_log_size - log_size[sel])[:, None]

    rec[:, 12:24] = scale.astype(np.float32).view(np.uint8).reshape(n, 12)
    rec[:, 24:28] = np.clip(np.round(rgba * 255.0), 0, 255).astype(np.uint8)

    Path(args.out).write_bytes(rec.tobytes())

    print("== AFTER ==")
    for k, v in _stats(scale, rgba[:, 3], labels, names, front).items():
        print(f"  {k}: n={v['n']} opacity={v['opacity']:.4f} log_size={v['log_size']:.4f}")
    print(f"wrote {args.out} ({n} splats)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
