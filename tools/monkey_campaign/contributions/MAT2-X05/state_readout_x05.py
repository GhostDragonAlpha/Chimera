#!/usr/bin/env python3
"""MAT2-X05: the palette law + the clean-view probes (prereg sections 2 and
5; X04's `state_readout` discipline re-executed for the NEW palettes).

The disjointness assertion EXECUTES AT SPEC LOAD (import time): any collision
between an X05 palette (instrument + landmarks) and any existing pinned
palette (W10 render colors, W10 diagnostic-only colors, X04 layer palettes,
U07 diagnostic markers) — or between two X05 palettes — refuses
`x05_palette_collision`.

X05's clean law (X-P7) preserves X04 P7's substance: every X05 CLEAN frame
carries ZERO pixels of any X04 diagnostic-layer palette and ZERO
W10-diagnostic palette pixels (exact-RGB probe over the committed stills);
the declared instrument and landmark palettes are the ONLY added content.
The X04 diagnostic layers stay diagnostic-only and are drawn on X05's
DIAGNOSTIC context frames through the PINNED X04 state_readout layer
machinery (imported, unmodified — the declared profile layers ARE the X04
layers).
"""
from __future__ import annotations

import numpy as np

import instrument_x05 as ix
import landmarks_x05 as lm

# ------------------------------------------------- existing (pinned, untouched)
GROUND = (168, 198, 150)
BODY_THORAX = (120, 80, 60)
LEG_LEFT = (200, 60, 50)
LEG_RIGHT = (60, 90, 200)
BODY_PALETTE = (BODY_THORAX, LEG_LEFT, LEG_RIGHT)

# W10 diagnostic-only (drawn ONLY on diagnostic frames by the pinned code)
W10_CONTACT_HIT = (0, 255, 0)
W10_CONTACT_MISS = (255, 140, 0)
W10_CHIP = (180, 30, 30)
W10_TICK_TEXT = (20, 20, 20)
W10_STRIDE_BAR_FILL = (30, 90, 200)
W10_STRIDE_BAR_TRACK = (210, 210, 210)
W10_DIAGNOSTIC_PALETTE = (W10_CONTACT_HIT, W10_CONTACT_MISS, W10_CHIP,
                          W10_TICK_TEXT, W10_STRIDE_BAR_FILL,
                          W10_STRIDE_BAR_TRACK)

# X04 diagnostic layers (L1 selected state labels / L2 event+tick trace /
# L3 debug isolation) — diagnostic-only on X05 frames too
L1_BG, L1_TEXT, L1_BORDER = (250, 250, 250), (15, 15, 15), (0, 90, 220)
L2_BG, L2_TEXT = (255, 238, 200), (90, 45, 10)
L3_BG = (232, 242, 232)
X04_LAYER_PALETTE = (L1_BG, L1_TEXT, L1_BORDER, L2_BG, L2_TEXT, L3_BG)

# U07 diagnostic markers (heritage; never drawn by X05, probed on clean)
U07_FRUSTUM_MARKER = (255, 0, 255)
U07_BODY_LABEL_MARKER = (0, 220, 220)
U07_OCCLUDER_FILL = (60, 60, 70)
U07_DIAGNOSTIC_PALETTE = (U07_FRUSTUM_MARKER, U07_BODY_LABEL_MARKER,
                          U07_OCCLUDER_FILL)

EXISTING_PALETTES = {
    "ground": (GROUND,),
    "body+legs": BODY_PALETTE,
    "w10_diagnostic_only": W10_DIAGNOSTIC_PALETTE,
    "x04_layer_diagnostic_only": X04_LAYER_PALETTE,
    "u07_diagnostic_markers": U07_DIAGNOSTIC_PALETTE,
}

# ------------------------------------------------------- X05's OWN palettes
X05_PALETTES = {
    "x05_velocity_instrument": ix.INSTRUMENT_PALETTE,
}
for _name, _pal in lm.LANDMARK_PALETTES.items():
    X05_PALETTES[_name] = tuple(_pal.values())

X05_ADDED_COLORS = tuple(c for pal in X05_PALETTES.values() for c in pal)


def assert_palette_disjointness():
    """The spec-load law: executes at import (see module docstring)."""
    seen = {}
    for group, palettes in EXISTING_PALETTES.items():
        for color in palettes:
            if color in seen:
                raise AssertionError(
                    "x05_palette_collision:" + repr(color)
                    + ":" + group + ":" + seen[color])
            seen[color] = group
    for group, palettes in X05_PALETTES.items():
        for color in palettes:
            if color in seen:
                raise AssertionError(
                    "x05_palette_collision:" + repr(color)
                    + ":" + group + ":" + seen[color])
            seen[color] = group
    return {"law": "every X05 palette color is distinct from every pinned "
                   "render/diagnostic color and from every other X05 color",
            "checked_colors": len(seen),
            "x05_added_colors": len(X05_ADDED_COLORS),
            "groups": sorted(seen.values())}


# executed at spec load (X04 state_readout discipline)
PALETTE_LAW = assert_palette_disjointness()


def _mask(arr, palette):
    return np.all(arr == np.array(palette, dtype=np.uint8), axis=2)


def palette_pixel_counts(arr):
    """Exact-RGB census of every declared palette color on one frame."""
    counts = {}
    for group, palettes in list(EXISTING_PALETTES.items()) \
            + list(X05_PALETTES.items()):
        for color in palettes:
            counts["%s:%d,%d,%d" % ((group,) + color)] = \
                int(_mask(arr, color).sum())
    return counts


def probe_clean_frame(arr):
    """X-P7: a clean frame must carry ZERO X04-diagnostic, W10-diagnostic
    and U07-marker palette pixels; the ONLY added content is the declared
    X05 palette set; every color on the frame must be a DECLARED color
    (ground, body+legs, X05 instrument/landmarks)."""
    diag = 0
    for pal in W10_DIAGNOSTIC_PALETTE + X04_LAYER_PALETTE \
            + U07_DIAGNOSTIC_PALETTE:
        diag += int(_mask(arr, pal).sum())
    declared = {GROUND} | set(BODY_PALETTE) | set(X05_ADDED_COLORS)
    flat = np.asarray(arr)
    if flat.ndim == 2:
        flat = np.stack([flat] * 3, axis=-1)
    unique = {tuple(int(c) for c in row)
              for row in np.unique(flat.reshape(-1, flat.shape[2]), axis=0)}
    undeclared = sorted(unique - declared)
    return {"diagnostic_palette_pixels": diag,
            "clean_ok": diag == 0,
            "undeclared_colors": [list(c) for c in undeclared],
            "only_declared_content": not undeclared,
            "ok": diag == 0 and not undeclared}


def body_mask(arr):
    m = _mask(arr, BODY_THORAX)
    for pal in (LEG_LEFT, LEG_RIGHT):
        m |= _mask(arr, pal)
    return m


def landmark_masks(arr):
    out = {}
    for name, pal in lm.LANDMARK_PALETTES.items():
        m = None
        for color in pal.values():
            mm = _mask(arr, color)
            m = mm if m is None else (m | mm)
        out[name] = m
    return out


def body_bbox(arr):
    m = body_mask(arr)
    ys, xs = np.nonzero(m)
    if not len(xs):
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]


def bbox_of_mask(m):
    ys, xs = np.nonzero(m)
    if not len(xs):
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
