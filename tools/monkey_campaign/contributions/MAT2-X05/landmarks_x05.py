#!/usr/bin/env python3
"""MAT2-X05: the declared stationary world LANDMARKS (prereg section 2).

Four world-fixed objects (2 trees, 2 rocks) at fixed clearing coordinates:
declared offsets from the anchor base `(x0, 0.0)`, where x0 is the body
anchor x at the first presented tick of the window (derived at run from the
run's OWN committed rows, prefix-identical across arms on the deterministic
line; receipted; never hand-copied). The landmarks are rasterized through
the SAME pinned F04 camera and depth buffer as the body (depth-tested; drawn
BEFORE the body), so their apparent motion IS the velocity signal: the
projection of the body's committed per-frame travel.

Declared palettes, ONE PER OBJECT (the per-object mask identity):
  landmark_tree_far : trunk (94,61,38) + canopy (34,94,44)
  landmark_tree_near: trunk (84,51,30) + canopy (26,82,36)
  landmark_rock_far : (132,132,126)
  landmark_rock_near: (108,108,102)

Declared geometry (metres, clearing frame):
  tree: trunk box half-width 0.12, height 1.0 (8 triangles); canopy
        tetrahedron radius 0.42 centred at height 1.25 (4 triangles)
  rock: ground tetrahedron, apex height 0.45, base radius 0.40 (4 triangles)

The landmarks add NO collision, NO contact and NO state channel (absent
inventory A8): the render writes no state (W10 FB6 heritage; X04 P4 form).

The live run-time checks are AUTHORITATIVE (the rock_near 0.83 px design
margin): any violation refuses (`x05_landmark_*`) and is a PRESERVED
FAILURE, never a retune.
"""
from __future__ import annotations

import math

TREE_HALF_WIDTH_M = 0.12
TREE_TRUNK_HEIGHT_M = 1.0
CANOPY_RADIUS_M = 0.42
CANOPY_CENTRE_HEIGHT_M = 1.25
ROCK_APEX_HEIGHT_M = 0.45
ROCK_BASE_RADIUS_M = 0.40

LANDMARK_PALETTES = {
    "landmark_tree_far": {"trunk": (94, 61, 38), "canopy": (34, 94, 44)},
    "landmark_tree_near": {"trunk": (84, 51, 30), "canopy": (26, 82, 36)},
    "landmark_rock_far": {"rock": (132, 132, 126)},
    "landmark_rock_near": {"rock": (108, 108, 102)},
}
ALL_LANDMARK_COLORS = tuple(
    color for pal in LANDMARK_PALETTES.values() for color in pal.values())

# The declared offsets from the anchor base (x0, 0.0) (prereg section 2).
LANDMARK_OFFSETS = {
    "landmark_tree_far": (-6.5, -2.5),
    "landmark_tree_near": (-3.5, -3.0),
    "landmark_rock_far": (-6.5, -4.0),
    "landmark_rock_near": (-3.5, -5.0),
}

LANDMARK_ORDER = ["landmark_tree_far", "landmark_tree_near",
                  "landmark_rock_far", "landmark_rock_near"]

# Declared live-check floors (the prereg's declared floors; the live check
# is authoritative; a refusal is a preserved failure).
ROI_CLEAR_PX = 110.0
MIN_PAIRWISE_SEPARATION_PX = 25.0
RASTER_TOLERANCE_PX = 2.0        # X-P3's declared +/-2 px per-edge tolerance


class Refusal(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise Refusal(code)


def landmark_base(x0, name):
    dx, dz = LANDMARK_OFFSETS[name]
    return (x0 + dx, 0.0 + dz)


def _box_side_tris(v):
    """8 triangles: the four side quads of the declared trunk box
    (vertices 0-3 base, 4-7 top, as in the declared construction)."""
    quads = [(0, 1, 5, 4), (3, 2, 6, 7), (1, 3, 7, 5), (2, 0, 4, 6)]
    tris = []
    for a, b, c, d in quads:
        tris.append((v[a], v[b], v[c]))
        tris.append((v[a], v[c], v[d]))
    return tris


def _tetra_tris(v):
    idx = [(0, 1, 2), (0, 3, 1), (0, 2, 3), (1, 2, 3)]
    return [(v[a], v[b], v[c]) for a, b, c in idx]


def tree_vertices(base_x, base_z):
    """The declared tree vertices: trunk box (8 corners) + canopy tetra (4).
    Same declared construction as the preregistered design preflight."""
    hw = TREE_HALF_WIDTH_M
    th = TREE_TRUNK_HEIGHT_M
    xs = [base_x - hw, base_x + hw]
    zs = [base_z - hw, base_z + hw]
    v = [(x, 0.0, z) for x in xs for z in zs] \
        + [(x, th, z) for x in xs for z in zs]
    cx, cy, cz, r = base_x, CANOPY_CENTRE_HEIGHT_M, base_z, CANOPY_RADIUS_M
    v += [(cx, cy + r, cz), (cx + r, cy - r / 2, cz + r / 2),
          (cx - r, cy - r / 2, cz + r / 2), (cx, cy - r / 2, cz - r)]
    return v


def rock_vertices(base_x, base_z):
    r = ROCK_BASE_RADIUS_M
    return [(base_x, ROCK_APEX_HEIGHT_M, base_z),
            (base_x + r, 0.0, base_z + r / 2),
            (base_x - r, 0.0, base_z + r / 2),
            (base_x, 0.0, base_z - r)]


def landmark_triangles(name, base_x, base_z):
    """The declared rasterization set: (triangle, palette_color) triples.
    tree = 8 trunk triangles + 4 canopy; rock = 4."""
    if name.startswith("landmark_tree"):
        v = tree_vertices(base_x, base_z)
        return ([(t, LANDMARK_PALETTES[name]["trunk"])
                 for t in _box_side_tris(v[:8])]
                + [(t, LANDMARK_PALETTES[name]["canopy"])
                   for t in _tetra_tris(v[8:])])
    require(name.startswith("landmark_rock"),
            "x05_landmark_unknown:" + name)
    v = rock_vertices(base_x, base_z)
    return [(t, LANDMARK_PALETTES[name]["rock"]) for t in _tetra_tris(v)]


def build_landmark_set(x0):
    """The declared set DERIVED at run from the anchor base x0."""
    return {name: {"base": landmark_base(x0, name),
                   "triangles": landmark_triangles(name, *landmark_base(x0, name)),
                   "vertices": (tree_vertices(*landmark_base(x0, name))
                                if name.startswith("landmark_tree")
                                else rock_vertices(*landmark_base(x0, name)))}
            for name in LANDMARK_ORDER}


def draw_landmarks(cam, f04, colour, depth, landmark_set, near, far):
    """Rasterize every declared landmark triangle through the pinned
    f04.raster_tri into the SAME colour/depth buffers (depth-tested; called
    BEFORE the body draw). Returns the drawn-triangle count."""
    drawn = 0
    for name in LANDMARK_ORDER:
        for (pa, pb, pc), rgb in landmark_set[name]["triangles"]:
            drawn += f04.raster_tri(cam, colour, depth, pa, pb, pc, rgb,
                                    near, far)
    return drawn


def project_vertices(cam, landmark_set):
    """Project every declared landmark vertex through the row-derived pinned
    F04 camera. Returns {name: [pixel or None per vertex]}."""
    return {name: [cam.pixel(list(v)) for v in landmark_set[name]["vertices"]]
            for name in LANDMARK_ORDER}


def bbox_of_points(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return [int(math.floor(min(xs))), int(math.floor(min(ys))),
            int(math.ceil(max(xs))), int(math.ceil(max(ys)))]


def live_checks(landmark_set, projections_per_frame, mask_frames,
                body_target_pixels, body_bbox_per_frame):
    """THE LIVE RUN-TIME CHECKS (authoritative; refusal = preserved failure).

    projections_per_frame: [{name: [vertex pixels]} per presented frame]
    mask_frames:           [{name: boolean mask array} per presented frame]
    body_target_pixels:    [(px, py) body-target pixel per frame]
    body_bbox_per_frame:   [body-ROI bbox (x0,y0,x1,y1) per frame or None]

    Checks, all frames, both arms:
    - in-frame: every vertex projects and lands inside the viewport
      (`x05_landmark_in_frame`);
    - clearance: every vertex >= ROI_CLEAR_PX from the body-target pixel
      (`x05_landmark_clearance`);
    - separation: minimum pairwise rendered-mask separation between distinct
      landmarks >= MIN_PAIRWISE_SEPARATION_PX (`x05_landmark_separation`);
    - non-occlusion: NO landmark mask pixel inside the body's declared ROI
      (`x05_landmark_occludes_roi`).
    """
    import numpy as np
    min_clear = float("inf")
    off_frame = 0
    behind = 0
    min_sep = float("inf")
    occlude_px = 0
    for i, projections in enumerate(projections_per_frame):
        tgt = body_target_pixels[i]
        for name in LANDMARK_ORDER:
            for p in projections[name]:
                if p is None:
                    behind += 1
                    continue
                if not (0 <= p[0] < 960 and 0 <= p[1] < 540):
                    off_frame += 1
                min_clear = min(min_clear,
                                math.hypot(p[0] - tgt[0], p[1] - tgt[1]))
        # pairwise separation: the declared vertex-based measure (the design
        # measure), exact over all 12 vertices per landmark; a rendered-mask
        # overlap pins it to 0.
        masks = mask_frames[i]
        for ai, a in enumerate(LANDMARK_ORDER):
            for b in LANDMARK_ORDER[ai + 1:]:
                if a in masks and b in masks and masks[a] is not None \
                        and masks[b] is not None \
                        and int(np.logical_and(masks[a], masks[b]).sum()) > 0:
                    min_sep = 0.0
                    continue
                pa = [p for p in projections[a] if p is not None]
                pb = [p for p in projections[b] if p is not None]
                for xa, ya, _ in pa:
                    for xb, yb, _ in pb:
                        min_sep = min(min_sep, math.hypot(xa - xb, ya - yb))
        bbox = body_bbox_per_frame[i]
        if bbox is not None:
            x0, y0, x1, y1 = bbox
            for name in LANDMARK_ORDER:
                if name not in masks:
                    continue
                m = masks[name][y0:y1 + 1, x0:x1 + 1]
                occlude_px += int(m.sum())
    require(behind == 0 and off_frame == 0,
            "x05_landmark_in_frame:off_%d_behind_%d" % (off_frame, behind))
    require(min_clear >= ROI_CLEAR_PX,
            "x05_landmark_clearance:%.2f" % min_clear)
    require(min_sep >= MIN_PAIRWISE_SEPARATION_PX,
            "x05_landmark_separation:%.2f" % min_sep)
    require(occlude_px == 0,
            "x05_landmark_occludes_roi:%d" % occlude_px)
    return {"min_clearance_px": round(min_clear, 2),
            "min_pairwise_separation_px": round(min_sep, 2),
            "off_frame_vertices": off_frame,
            "behind_camera_vertices": behind,
            "landmark_pixels_inside_body_roi": occlude_px,
            "floors": {"roi_clear_px": ROI_CLEAR_PX,
                       "min_pairwise_separation_px": MIN_PAIRWISE_SEPARATION_PX}}
