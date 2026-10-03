"""MAT2-X05 capture-card render callback (template recipe step 3).

``render(view_class, frame_id, defect)`` returns ``(beauty, mask)`` uint8
(H, W, 3). The beauty channel is THE committed capture frame of the frozen
24-frame plan (the sealed run's own frames artifacts, bound by frame_id) —
never a second render. The mask channel is the object-ID identity buffer,
derived from that beauty by the declared palette classification (the
view-spec palettes partition the renderer's complete declared color set;
state_readout_x05 proves the X05 palettes disjoint from every pinned color).
The mask is never composited into beauty.

Defect cases (each a DECLARED perturbation class the gate must REJECT):
- INSTRUMENT_ERASED_BUT_CLAIMED: the instrument strip is erased from beauty
  only; the mask keeps claiming it -> stage-1 COLOCATION_MISMATCH.
- LANDMARK_RECOLOR_SHARED: all of tree_near's canopy beauty pixels are
  repainted with tree_far's canopy color -> COLOCATION_MISMATCH (the
  shared-color defense).
- BODY_ABSENT: the body is erased from BOTH channels (an honest missing
  subject) -> SUBJECT_MASK_BELOW_FLOOR.
- CLEAN_DIAGNOSTIC_LEAK: the x04_state_labels layer is drawn on a CLEAN
  frame in BOTH channels -> UNDECLARED_MASK_ID (the X05 clean law; the X04
  layers stay diagnostic-only).
"""
from __future__ import annotations

import numpy as np

INSTRUMENT_ERASED_BUT_CLAIMED = "INSTRUMENT_ERASED_BUT_CLAIMED"
LANDMARK_RECOLOR_SHARED = "LANDMARK_RECOLOR_SHARED"
BODY_ABSENT = "BODY_ABSENT"
CLEAN_DIAGNOSTIC_LEAK = "CLEAN_DIAGNOSTIC_LEAK"


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


def _palette_footprint(arr, spec, object_id):
    pal = [tuple(int(c) for c in color)
           for color in spec["objects"][object_id]["beauty_palette"]]
    m = np.zeros(arr.shape[:2], dtype=bool)
    for color in pal:
        m |= np.all(arr == np.array(color, dtype=np.uint8), axis=2)
    return m


def apply_defect(beauty, mask, spec, defect):
    """Return a defect-perturbed (beauty, mask) pair for a DECLARED class."""
    beauty = np.array(beauty, dtype=np.uint8, copy=True)
    mask = np.array(mask, dtype=np.uint8, copy=True)
    if defect == INSTRUMENT_ERASED_BUT_CLAIMED:
        x0, y0, x1, y1 = spec["fixture_geometry"]["rects_xyxy"][
            "x05_velocity_instrument"]
        bg = np.array(spec["background"]["beauty_color"], dtype=np.uint8)
        beauty[y0:y1 + 1, x0:x1 + 1] = bg       # beauty only: claimed, absent
        return beauty, mask
    if defect == LANDMARK_RECOLOR_SHARED:
        donor = np.array(
            spec["objects"]["landmark_tree_far"]["beauty_palette"][1],
            dtype=np.uint8)
        fp = _palette_footprint(beauty, spec, "landmark_tree_near") \
            & _palette_footprint(beauty, spec, "landmark_tree_near")
        # the canopy share: the donor color's own footprint defines it
        canopy = np.all(beauty == np.array(
            spec["objects"]["landmark_tree_near"]["beauty_palette"][1],
            dtype=np.uint8), axis=2)
        beauty[canopy] = donor                   # another landmark's color
        _ = fp
        return beauty, mask
    if defect == BODY_ABSENT:
        bgb = np.array(spec["background"]["beauty_color"], dtype=np.uint8)
        bgm = np.array(spec["background"]["mask_code"], dtype=np.uint8)
        fp = _palette_footprint(beauty, spec, "monkey_body")
        fp |= np.all(mask == np.array(
            spec["objects"]["monkey_body"]["mask_code"], dtype=np.uint8),
            axis=2)
        beauty[fp] = bgb
        mask[fp] = bgm                           # honest: absent in both
        return beauty, mask
    if defect == CLEAN_DIAGNOSTIC_LEAK:
        # the L2 (x04_event_strip) rect — contains no landmark footprint,
        # so the leak's dominant code is exactly the clean-law violation
        x0, y0, x1, y1 = spec["fixture_geometry"]["rects_xyxy"][
            "x04_event_strip"]
        pal = spec["objects"]["x04_event_strip"]["beauty_palette"]
        code = np.array(spec["objects"]["x04_event_strip"]["mask_code"],
                        dtype=np.uint8)
        beauty[y0:y1 + 1, x0:x1 + 1] = np.array(pal[0], dtype=np.uint8)
        mask[y0:y1 + 1, x0:x1 + 1] = code        # consistent: the leak is
        return beauty, mask                      # in a CLEAN class
    raise ValueError("undeclared_defect:" + str(defect))


def make_renderer(frames_by_id, spec):
    """The template render_fn: committed frames only, one declared table.

    ``frames_by_id`` maps "<KEY>@<frame_id>" -> (H, W, 3) uint8 (the lazy
    frame store; committed frames only)."""
    def render(view_class, frame_id, defect=None):
        beauty = frames_by_id[frame_id]
        mask = classify_mask(beauty, spec)
        if defect:
            beauty, mask = apply_defect(beauty, mask, spec, defect)
        return beauty, mask

    return render
