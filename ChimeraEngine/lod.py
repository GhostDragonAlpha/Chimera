"""Trained Level-of-Detail for splat bodies -- the pixel-budget law, learned not hand-tuned.

THE LAW (scale-invariant screen-space density): a body whose projected radius is r_px pixels is rendered
with  N = rho * r_px^2  grains -> grains-per-pixel and per-pixel OVERDRAW are constant at every scale, so
one colour gain holds everywhere (no white blow-out when a planet shrinks in the solar-system view) and the
total grain work is bounded by screen area (the operator's "square-footage" budget -> framerate stops
depending on zoom).

Coarse levels are a MIP PYRAMID with spatially-AVERAGED colours: a 1px planet is the average of the whole
surface (not one arbitrary grain), a 4px planet is a handful of regional averages, etc. -- exactly a texture
mipmap, on the sphere. Built ONCE per body; runtime LOD is a cheap level lookup.

`rho` (density) and `beta` (grain overlap) are TRAINED by lod_train.py; loaded from lod.trained.json.
"""
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np

_TRAINED = Path(__file__).resolve().parent / "lod.trained.json"
_DEFAULT = {"rho": 0.45, "beta": 2.5, "n_min": 1}
_SIZE_COL = 20            # matches ParticleEngine.gpu_pipeline.SIZE / splat_appearance.SIZE


def params() -> dict:
    try:
        d = json.loads(_TRAINED.read_text())
        return {"rho": float(d["rho"]), "beta": float(d["beta"]), "n_min": int(d.get("n_min", 1)),
                "color_gain": [float(x) for x in d.get("color_gain", [1.0, 1.0, 1.0])]}
    except Exception:
        return dict(_DEFAULT, color_gain=[1.0, 1.0, 1.0])


def lod_count(r_px: float, n_base: int, p: dict | None = None) -> int:
    """Grains for a body of projected radius r_px (clamped to [n_min, n_base]). N = rho * r_px^2."""
    p = p or params()
    return max(p["n_min"], min(n_base, int(round(p["rho"] * r_px * r_px))))


def body_radius(buf: np.ndarray) -> float:
    return float(np.linalg.norm(buf[:, 0:3], axis=1).max()) if buf.shape[0] else 1.0


def projected_radius_px(radius_world: float, cam_distance: float, height_px: int, fov: float) -> float:
    focal = height_px / (2.0 * math.tan(fov / 2.0))
    return radius_world * focal / max(1e-6, cam_distance)


# ── the mip pyramid ────────────────────────────────────────────────────────────────────────────────────
_MIP_LEVELS = [1, 4, 16, 64, 256, 1024, 4096, 16384]     # + the base itself as the finest level


def build_mips(base: np.ndarray, radius_world: float, p: dict | None = None) -> list[np.ndarray]:
    """Precompute LOD levels for a body. Coarse levels use SPATIALLY-AVERAGED colours (nearest-representative
    clustering on the sphere); finer levels (> ~a few k) just subsample -- their detail is already sub-pixel
    when they're chosen. Each level's grain SIZE is set by the law (beta * 2R/sqrt(N)) so it tiles. Returns
    levels coarse->fine; the last is the base."""
    p = p or params()
    n_base = base.shape[0]
    dirs = base[:, 0:3] / (np.linalg.norm(base[:, 0:3], axis=1, keepdims=True) + 1e-9)
    levels = []
    for N in _MIP_LEVELS:
        if N >= n_base:
            break
        idx = np.linspace(0, n_base - 1, N).astype(np.int64)
        lvl = base[idx].copy()
        if N <= 4096:                                     # spatial colour average (mipmap): assign each base grain to
            reps = dirs[idx]                              # its nearest representative, average the colours per cell
            nearest = np.argmax(dirs @ reps.T, axis=1)    # (n_base,) -> which representative
            for c in (16, 17, 18):                        # CR, CG, CB
                sums = np.bincount(nearest, weights=base[:, c], minlength=N)
                cnts = np.bincount(nearest, minlength=N).clip(min=1)
                lvl[:, c] = (sums / cnts).astype(np.float32)
        lvl[:, _SIZE_COL] = p["beta"] * 2.0 * radius_world / math.sqrt(max(1, N))
        levels.append(lvl)
    base_lvl = base.copy()
    base_lvl[:, _SIZE_COL] = p["beta"] * 2.0 * radius_world / math.sqrt(max(1, n_base))
    levels.append(base_lvl)
    cg = p.get("color_gain", [1.0, 1.0, 1.0])            # re-expose for the law's overdraw (calibrated once)
    if cg != [1.0, 1.0, 1.0]:
        for lvl in levels:
            for i, c in enumerate((16, 17, 18)):
                lvl[:, c] = np.clip(lvl[:, c] * cg[i], 0.0, 1.0)
    return levels


def select(levels: list[np.ndarray], r_px: float, p: dict | None = None) -> np.ndarray:
    """Pick the coarsest mip level with at least lod_count(r_px) grains -> the fewest grains that suffice."""
    p = p or params()
    want = lod_count(r_px, levels[-1].shape[0], p)
    for lvl in levels:
        if lvl.shape[0] >= want:
            return lvl
    return levels[-1]
