#!/usr/bin/env python3
"""MAT2-X04 capture-card render callback (template recipe step 3).

``render(view_class, frame_id, defect)`` returns ``(beauty, mask)`` uint8
(H, W, 3). The beauty channel is THE committed capture frame of the frozen
39-frame plan (the sealed run's own frames artifact, bound by frame_id) —
never a second render. The mask channel is the object-ID identity buffer,
derived from that beauty by the declared palette classification (the
view-spec palettes partition the renderer's complete declared color set;
state_readout proves X04 palettes disjoint from every W10 render color).
The mask is never composited into beauty.

Defect cases (each a DECLARED perturbation class the gate must REJECT):
- LABEL_MISSING_BUT_CLAIMED: the L1 panel is erased from beauty only; the
  mask keeps claiming it -> stage-1 COLOCATION_MISMATCH (the FB3 class).
- BODY_RECOLOR_SHARED: a declared share of body beauty pixels is repainted
  with ANOTHER object's declared palette color -> COLOCATION_MISMATCH (the
  shared-color defense).
- SUBJECT_ABSENT: the body is erased from BOTH channels (an honest missing
  subject) -> SUBJECT_MASK_BELOW_FLOOR.
- CLEAN_LAYER_LEAK: the L1 layer is drawn on a CLEAN frame in BOTH channels
  -> UNDECLARED_MASK_ID (the clean-class accounting law; the FB4 class).
"""
from __future__ import annotations

import numpy as np

LABEL_MISSING_BUT_CLAIMED = "LABEL_MISSING_BUT_CLAIMED"
BODY_RECOLOR_SHARED = "BODY_RECOLOR_SHARED"
SUBJECT_ABSENT = "SUBJECT_ABSENT"
CLEAN_LAYER_LEAK = "CLEAN_LAYER_LEAK"

BODY_SHARE = 0.30          # declared recolor share for BODY_RECOLOR_SHARED

# the view-spec's classification table (imported from the spec file by
# run_all; kept in one place here through load_table)
_TABLE = None


def load_table(spec):
    """Build the exact beauty-color -> object_id table."""
    table = {}
    for name, obj in spec["objects"].items():
        for color in obj["beauty_palette"]:
            table[tuple(int(c) for c in color)] = name
    return table


def classify_mask(beauty, spec):
    """Derive the object-ID mask from the committed beauty frame."""
    table = load_table(spec)
    mask_codes = {name: tuple(int(c) for c in obj["mask_code"])
                  for name, obj in spec["objects"].items()}
    bg = tuple(int(c) for c in spec["background"]["mask_code"])
    beauty_bg = tuple(int(c) for c in spec["background"]["beauty_color"])
    flat = np.asarray(beauty, dtype=np.uint8)
    out = np.zeros(flat.shape, dtype=np.uint8)
    for color, name in table.items():
        hit = np.all(flat == np.array(color, dtype=np.uint8), axis=2)
        if hit.any():
            out[hit] = np.array(mask_codes[name], dtype=np.uint8)
    out[np.all(flat == np.array(beauty_bg, dtype=np.uint8), axis=2)] = \
        np.array(bg, dtype=np.uint8)
    return out


def _body_footprint(arr, spec):
    pal = [tuple(int(c) for c in color)
           for color in spec["objects"]["monkey_body"]["beauty_palette"]]
    m = np.zeros(arr.shape[:2], dtype=bool)
    for color in pal:
        m |= np.all(arr == np.array(color, dtype=np.uint8), axis=2)
    return m


def apply_defect(beauty, mask, spec, defect):
    """Return a defect-perturbed (beauty, mask) pair for a DECLARED class."""
    beauty = np.array(beauty, dtype=np.uint8, copy=True)
    mask = np.array(mask, dtype=np.uint8, copy=True)
    if defect == LABEL_MISSING_BUT_CLAIMED:
        x0, y0, x1, y1 = spec["fixture_geometry"]["rects_xyxy"][
            "x04_state_labels"]
        bg = np.array(spec["background"]["beauty_color"], dtype=np.uint8)
        beauty[y0:y1 + 1, x0:x1 + 1] = bg          # beauty only: claimed, absent
        return beauty, mask
    if defect == BODY_RECOLOR_SHARED:
        donor = np.array(
            spec["objects"]["x04_event_strip"]["beauty_palette"][0],
            dtype=np.uint8)
        fp = _body_footprint(beauty, spec)
        ys, xs = np.nonzero(fp)
        take = ys[::int(1.0 / BODY_SHARE)], xs[::int(1.0 / BODY_SHARE)]
        beauty[take] = donor                        # another object's color
        return beauty, mask
    if defect == SUBJECT_ABSENT:
        bgb = np.array(spec["background"]["beauty_color"], dtype=np.uint8)
        bgm = np.array(spec["background"]["mask_code"], dtype=np.uint8)
        fp = _body_footprint(beauty, spec)
        fp |= np.all(mask == np.array(
            spec["objects"]["monkey_body"]["mask_code"], dtype=np.uint8),
            axis=2)
        beauty[fp] = bgb
        mask[fp] = bgm                              # honest: absent in both
        return beauty, mask
    if defect == CLEAN_LAYER_LEAK:
        x0, y0, x1, y1 = spec["fixture_geometry"]["rects_xyxy"][
            "x04_state_labels"]
        pal = spec["objects"]["x04_state_labels"]["beauty_palette"]
        code = np.array(spec["objects"]["x04_state_labels"]["mask_code"],
                        dtype=np.uint8)
        beauty[y0:y1 + 1, x0:x1 + 1] = np.array(pal[0], dtype=np.uint8)
        beauty[y0, x0:x1 + 1] = np.array(pal[2], dtype=np.uint8)
        beauty[y1, x0:x1 + 1] = np.array(pal[2], dtype=np.uint8)
        mask[y0:y1 + 1, x0:x1 + 1] = code           # consistent: the leak is
        return beauty, mask                         # in a CLEAN class
    raise ValueError("undeclared_defect:" + str(defect))


def make_renderer(frames_by_id, spec):
    """The template render_fn: committed frames only, one declared table."""

    def render(view_class, frame_id, defect=None):
        key = frame_id.split("@")[0]
        beauty = frames_by_id[key]
        mask = classify_mask(beauty, spec)
        if defect:
            beauty, mask = apply_defect(beauty, mask, spec, defect)
        return beauty, mask

    return render
