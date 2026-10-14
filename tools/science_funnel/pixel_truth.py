"""pixel_truth.py -- REUSABLE deterministic pixel verification for any visual lane.

Visual truth measured in PIXELS, not eyeballed by whoever happens to be
verifying (operator directive, lane agent/triangle-monkey-grid-20260920).
No vision model, no image-viewing agent, no model calls: every function here
is pure image + geometry arithmetic (numpy/scipy/PIL), deterministic, and
offline. Each function returns numbers a falsifier can gate.

WHAT IT MEASURES (each one earned its place on a measured defect):

  grain        median over an object's interior pixels of the local 5x5
               grayscale variance. A splat cloud is GRAINY (inter-splat
               texture); a shaded mesh tends to a smooth-shading floor.
               Defect A's grain falsifier.
  coverage     fraction of the object's projected convex-hull interior whose
               pixels actually show the object. A splat cloud leaves holes
               (coverage < 1); a triangle mesh fills its own silhouette
               (coverage ~ 1). Defect A's coverage falsifier, per region too.
  object_seen  fraction of a region-of-interest (e.g. a projected object
               footprint) whose pixels show the object. The two-sided grid
               guide check: the subject must be PRESENT through the guide
               plane from ANY side. Defect B's falsifier.
  guide_seen   fraction of a region-of-interest whose pixels match a guide
               ink family (color predicates). A guide invisible from one side
               is not a guide. Defect B's falsifier.
  clip_scan    per-frame visible-object pixel counts across a rendered orbit;
               a near-plane clip shows up as a frame whose count collapses
               vs its neighbors, and an edge clip as a NEW silhouette touch
               on the frame border. Defect C's falsifier.

COLOR PREDICATES: object pixels are detected by warm-dominance (the bone tint
family r>g>b with r-b >= warm_min and r >= r_min); guide lines by
blue-dominance; both are parameterised and calibrated against the actual
frames by reporting counts (never tuned silently — thresholds live in the
caller's receipt, pre-registered).

CLI (each subcommand prints one JSON object):
  python -B tools/science_funnel/pixel_truth.py grain IMG --mask MASK
  python -B tools/science_funnel/pixel_truth.py coverage IMG --mask MASK
  python -B tools/science_funnel/pixel_truth.py object-seen IMG --roi ROI
  python -B tools/science_funnel/pixel_truth.py guide-seen IMG --roi ROI
  python -B tools/science_funnel/pixel_truth.py clipscan FRAME_DIR GLOB

IMG/ROI/MASK are images (PNG); ROI/MASK: nonzero pixel = inside. `--mask -`
reads it from stdin. In-process use:

  from tools.science_funnel import pixel_truth as pt
  img = pt.load("frame.png")
  obj = pt.warm_mask(img)                    # object pixels by color
  hull = pt.hull_mask(pts_px, img.shape)     # projected geometry footprint
  cov = pt.coverage(obj, hull)               # -> {"coverage": 0.97, ...}
  g   = pt.grain(img, obj)
  scan = pt.clip_scan([pt.warm_mask(pt.load(f)) for f in frames])
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

try:
    from scipy import ndimage
    from scipy.spatial import ConvexHull
    HAVE_SCIPY = True
except Exception:                                        # pragma: no cover
    HAVE_SCIPY = False


# ── image + masks ────────────────────────────────────────────────────────────

def load(path_or_img) -> np.ndarray:
    """RGB uint8 array from a path or an already-loaded image."""
    if isinstance(path_or_img, (str, Path)):
        return np.asarray(Image.open(path_or_img).convert("RGB"))
    return np.asarray(path_or_img)


def warm_mask(img: np.ndarray, r_min: int = 70, warm_min: int = 25) -> np.ndarray:
    """Object pixels by warm dominance: r >= g >= b-ish tint family.
    The bone tint (0.82,0.75,0.60) shaded stays warm; the cool background
    (4,5,15), the gray floor (~55 flat) and the bluish grid lines never are."""
    im = img.astype(np.int16)
    return (im[:, :, 0] >= r_min) & ((im[:, :, 0] - im[:, :, 2]) >= warm_min)


def cool_line_mask(img: np.ndarray, b_min: int = 60, bgap_min: int = 20,
                   luma_max: int = 160) -> np.ndarray:
    """Guide-line pixels by blue dominance (the projected grid ink family:
    bluish-gray, b > g > r; the ink alpha-blends to ~ (55..98) blue channel
    over the floor/background, measured 2026-09-20 on the live engine)."""
    im = img.astype(np.int16)
    luma = (0.299 * im[:, :, 0] + 0.587 * im[:, :, 1] + 0.114 * im[:, :, 2])
    return (im[:, :, 2] >= b_min) & ((im[:, :, 2] - im[:, :, 0]) >= bgap_min) \
        & (luma <= luma_max)


def hull_mask(pts_px: np.ndarray, shape: tuple, dilate_px: int = 2) -> np.ndarray:
    """Rasterized convex hull of 2D pixel points (the projected footprint).
    pts_px: (n,2) float [x, y]. dilate_px grows the hull slightly so edge
    rasterization never under-covers the true footprint."""
    pts = np.asarray(pts_px, dtype=np.float64)
    _require(len(pts) >= 3, "hull_needs_3_points")
    _require(HAVE_SCIPY, "scipy_unavailable")
    hull = ConvexHull(pts)
    poly = pts[hull.vertices]
    im = Image.new("L", (shape[1], shape[0]), 0)
    ImageDraw.Draw(im).polygon([tuple(p) for p in poly], fill=1)
    m = np.asarray(im, dtype=bool)
    if dilate_px > 0:
        m = ndimage.binary_dilation(m, iterations=dilate_px)
    return m


def fill_holes(mask: np.ndarray) -> np.ndarray:
    _require(HAVE_SCIPY, "scipy_unavailable")
    return ndimage.binary_fill_holes(mask)


def interior(mask: np.ndarray, erode_px: int = 2) -> np.ndarray:
    """The interior of a mask (erosion kills the silhouette edge, where
    anti-aliasing and background blending would fake grain)."""
    if not HAVE_SCIPY or erode_px <= 0:
        return mask
    return ndimage.binary_erosion(mask, iterations=erode_px)


def _require(condition, code, detail=None):
    if not condition:
        raise ValueError(f"pixel_truth refusal: {code} {detail or ''}")


# ── the metrics ──────────────────────────────────────────────────────────────

def grain(img: np.ndarray, obj_mask: np.ndarray, window: int = 5,
          erode_px: int = 2) -> dict:
    """Median local variance (on the grayscale, over window x window) across
    the object's INTERIOR pixels. Deterministic; units are gray-level^2."""
    _require(window % 2 == 1, "window_must_be_odd", window)
    g = (0.299 * img[:, :, 0] + 0.587 * img[:, :, 1] + 0.114 * img[:, :, 2])
    gf = g.astype(np.float64)
    k = window // 2
    def _box_sum(a):
        padded = np.pad(a, k, mode="edge")
        s = np.cumsum(np.cumsum(padded, 0), 1)
        s = np.pad(s, ((1, 0), (1, 0)))   # integral image, shape (H+2k+1, W+2k+1)
        return (s[window:, window:] - s[:-window, window:]
                - s[window:, :-window] + s[:-window, :-window]) / float(window * window)
    m = _box_sum(gf)                # local mean
    m2 = _box_sum(gf * gf)          # local mean of squares
    var = np.maximum(m2 - m * m, 0.0)
    use = interior(obj_mask, erode_px=erode_px)
    n = int(use.sum())
    _require(n > 0, "empty_object_interior")
    return {
        "grain_median_local_variance": round(float(np.median(var[use])), 4),
        "grain_p90_local_variance": round(float(np.percentile(var[use], 90)), 4),
        "window": window,
        "interior_pixels": n,
    }


def coverage(obj_mask: np.ndarray, footprint_hull: np.ndarray) -> dict:
    """|object pixels| / |projected convex-hull interior|. A mesh fills its
    silhouette (-> ~1.0); a splat cloud leaves holes (< 1)."""
    area = int(footprint_hull.sum())
    _require(area > 0, "empty_footprint")
    seen = int((obj_mask & footprint_hull).sum())
    return {
        "coverage": round(seen / area, 4),
        "object_pixels_in_hull": seen,
        "hull_pixels": area,
    }


def object_seen(img: np.ndarray, roi: np.ndarray, r_min: int = 70,
                warm_min: int = 25, dim: bool = False) -> dict:
    """Fraction of the ROI (e.g. the object's projected footprint for THIS
    camera) whose pixels show the object. The two-sided guide check: >= 0.9
    means the subject survived the plane from this side.

    `dim=True` widens the detector to the body seen THROUGH the 50% guide
    plane (its bright faces blend to ~ (131,121,97), its dark shaded faces to
    ~ (48,43,33) — still warm-dominant, half as bright): r_min 40,
    warm_min 12. The gray plane ink (r-b <= 8) and the bluish grid lines stay
    excluded. The SAME predicate must be used on both sides of a comparison."""
    _require(int(roi.sum()) > 0, "empty_roi")
    if dim:
        r_min, warm_min = 40, 12
    obj = warm_mask(img, r_min=r_min, warm_min=warm_min)
    seen = int((obj & roi).sum())
    return {
        "object_seen_ratio": round(seen / int(roi.sum()), 4),
        "object_pixels_in_roi": seen,
        "roi_pixels": int(roi.sum()),
        "dim_detector": bool(dim),
    }


def guide_seen(img: np.ndarray, roi: np.ndarray, b_min: int = 60,
               bgap_min: int = 20, reference_count: int | None = None) -> dict:
    """Guide-line presence. `guide_seen_ratio` = guide ink pixels in the ROI
    normalized by the ROI's pixel area; when `reference_count` is given (the
    grid's own visible ink from the uncontested side), `guide_presence_ratio`
    = this ROI's ink / the reference ink — the grid's own-footprint presence
    (>= 0.05 pre-registered bar: a guide invisible from one side is not a
    guide)."""
    _require(int(roi.sum()) > 0, "empty_roi")
    lines = cool_line_mask(img, b_min=b_min, bgap_min=bgap_min)
    n = int((lines & roi).sum())
    out = {
        "guide_seen_ratio": round(n / int(roi.sum()), 6),
        "guide_pixels_in_roi": n,
        "roi_pixels": int(roi.sum()),
    }
    if reference_count is not None:
        out["reference_guide_pixels"] = int(reference_count)
        out["guide_presence_ratio"] = round(n / max(1, reference_count), 4)
    return out


def clip_scan(counts: list, boundary_touch: list | None = None,
              collapse_ratio: float = 0.5) -> dict:
    """Orbit clipping scan (Defect C). counts[i] = visible object pixels in
    frame i. FAILS (clip=True) if any frame's count drops below
    `collapse_ratio` x the median of its neighbors (a phase where the subject
    vanished), or if a frame grows a NEW silhouette touch on the frame border
    the previous frame did not have (edge clip)."""
    counts = [int(c) for c in counts]
    _require(len(counts) >= 5, "orbit_too_short", len(counts))
    n = len(counts)
    events = []
    for i in range(n):
        neigh = [counts[(i - 1) % n], counts[(i + 1) % n]]
        med = float(np.median(neigh))
        if med > 0 and counts[i] < collapse_ratio * med:
            events.append({"frame": i, "count": counts[i],
                           "neighbor_median": round(med, 1),
                           "kind": "collapse"})
    if boundary_touch is not None:
        for i in range(n):
            prev = boundary_touch[(i - 1) % n]
            if boundary_touch[i] and not prev:
                events.append({"frame": i, "kind": "new_boundary_touch"})
    return {
        "frames": n,
        "counts": counts,
        "collapse_ratio": collapse_ratio,
        "clip_events": events,
        "clip": bool(events),
    }


def boundary_touch(obj_mask: np.ndarray, band_px: int = 2) -> bool:
    """True when object pixels reach the frame's outer band (edge clip)."""
    m = obj_mask
    top, bot = m[:band_px, :], m[-band_px:, :]
    left, right = m[:, :band_px], m[:, -band_px:]
    return bool(top.any() or bot.any() or left.any() or right.any())


# ── CLI ──────────────────────────────────────────────────────────────────────

def _load_arg(path: str) -> np.ndarray:
    import io as _io
    if path == "-":
        return np.asarray(Image.open(_io.BytesIO(sys.stdin.buffer.read())).convert("RGB"))
    return load(path)


def main(argv=None) -> int:  # pragma: no cover - CLI
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("grain"); g.add_argument("img"); g.add_argument("--mask", required=True)
    c = sub.add_parser("coverage"); c.add_argument("img"); c.add_argument("--mask", required=True)
    o = sub.add_parser("object-seen"); o.add_argument("img"); o.add_argument("--roi", required=True)
    d = sub.add_parser("guide-seen"); d.add_argument("img"); d.add_argument("--roi", required=True)
    s = sub.add_parser("clipscan"); s.add_argument("frame_dir"); s.add_argument("glob")

    a = ap.parse_args(argv)
    if a.cmd == "grain":
        img, m = _load_arg(a.img), _load_arg(a.mask) > 0
        print(json.dumps(grain(img, m)))
    elif a.cmd == "coverage":
        img, m = _load_arg(a.img), _load_arg(a.mask) > 0
        obj = warm_mask(img)
        print(json.dumps(coverage(obj, m)))
    elif a.cmd == "object-seen":
        print(json.dumps(object_seen(_load_arg(a.img), _load_arg(a.roi) > 0)))
    elif a.cmd == "guide-seen":
        print(json.dumps(guide_seen(_load_arg(a.img), _load_arg(a.roi) > 0)))
    elif a.cmd == "clipscan":
        frames = sorted(Path(a.frame_dir).glob(a.glob))
        counts, touches = [], []
        for f in frames:
            m = warm_mask(load(f))
            counts.append(int(m.sum()))
            touches.append(boundary_touch(m))
        print(json.dumps(clip_scan(counts, touches)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
