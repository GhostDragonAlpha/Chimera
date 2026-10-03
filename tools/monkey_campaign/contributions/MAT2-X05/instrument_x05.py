#!/usr/bin/env python3
"""MAT2-X05: the declared velocity INSTRUMENT (prereg section 2, object
`x05_velocity_instrument`).

A screen-space strip, rect x[12,300] y[8,40]: 1-px border (90,20,120),
bg (252,252,252), text (10,82,10) at declared origin (18,14), scale 2.
Content law: the string `V=<com_v rounded 3 decimals>` rendered from a
declared 3x5 glyph table (set: V, 0-9, ., =), drawn by THIS module's own
drawer (the pinned `draw_glyph` covers digits only and is NOT modified).

The displayed value is DERIVED at render time from the presented frame's
consumed row: `round(row.com_v_m_s, 3)`. This is AN INSTRUMENT, never a body
cue (absent inventory A2): manifest rows record the object as
`declared_instrument: velocity_indicator`.

Readability is MEASURED (the X04 P9 measured-geometry form): every drawn
string's expected pixel bbox/count is derived from the glyph law and compared
against the committed still exactly.

Pure stdlib + numpy at the probe boundary; deterministic.
"""
from __future__ import annotations

import numpy as np

# ---------------------------------------------------------------- palettes
INSTRUMENT_BG = (252, 252, 252)
INSTRUMENT_INK = (10, 82, 10)
INSTRUMENT_BORDER = (90, 20, 120)
INSTRUMENT_PALETTE = (INSTRUMENT_BG, INSTRUMENT_INK, INSTRUMENT_BORDER)
INSTRUMENT_RECT = (12, 8, 300, 40)          # x0, y0, x1, y1 (inclusive)
INSTRUMENT_TEXT_X0, INSTRUMENT_TEXT_Y0 = 18, 14
INSTRUMENT_SCALE = 2
DECLARED_INSTRUMENT = "velocity_indicator"

# ------------------------------------------------------------------- font
# The declared 3x5 glyph table (set: V, 0-9, ., =). The digit rows are the
# pinned W10 digit table's rows (visually identical, declared here because
# this module owns the whole string).
_GLYPHS = {
    "V": ["101", "101", "101", "101", "010"],
    "0": ["111", "101", "101", "101", "111"],
    "1": ["010", "110", "010", "010", "111"],
    "2": ["111", "001", "111", "100", "111"],
    "3": ["111", "001", "111", "001", "111"],
    "4": ["101", "101", "111", "001", "001"],
    "5": ["111", "100", "111", "001", "111"],
    "6": ["111", "100", "111", "101", "111"],
    "7": ["111", "001", "001", "001", "001"],
    "8": ["111", "101", "111", "101", "111"],
    "9": ["111", "101", "111", "001", "111"],
    ".": ["000", "000", "000", "000", "010"],
    "=": ["000", "111", "000", "111", "000"],
}
GLYPH_ON_COUNT = {ch: sum(row.count("1") for row in rows)
                  for ch, rows in _GLYPHS.items()}


class Refusal(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise Refusal(code)


def instrument_string(row):
    """The content law: derived from the consumed row at render time."""
    return "V=%.3f" % round(float(row["com_v_m_s"]), 3)


def expected_text_metrics(text: str, scale: int = INSTRUMENT_SCALE):
    """The glyph law: width/height/pixel-count of one drawn string."""
    require(all(ch in _GLYPHS for ch in text),
            "x05_glyph_missing:" + repr(text))
    n = len(text)
    return {"text": text,
            "width_px": (n * 4 - 1) * scale,
            "height_px": 5 * scale,
            "pixel_count": sum(GLYPH_ON_COUNT[ch] for ch in text)
            * scale * scale}


def draw_text(colour, text, x0, y0, scale, rgb):
    """Draw one string with the declared font (exact pixels; no clipping)."""
    require(all(ch in _GLYPHS for ch in text),
            "x05_glyph_missing:" + repr(text))
    for i, ch in enumerate(text):
        rows = _GLYPHS[ch]
        for gy, line in enumerate(rows):
            for gx, bit in enumerate(line):
                if bit == "1":
                    for dy in range(scale):
                        for dx in range(scale):
                            yy = y0 + gy * scale + dy
                            xx = x0 + (i * 4 + gx) * scale + dx
                            colour[yy][xx] = rgb


def fill_rect(colour, rect, rgb):
    x0, y0, x1, y1 = rect
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            colour[y][x] = rgb


def border_rect(colour, rect, rgb):
    x0, y0, x1, y1 = rect
    for x in range(x0, x1 + 1):
        colour[y0][x] = rgb
        colour[y1][x] = rgb
    for y in range(y0, y1 + 1):
        colour[y][x0] = rgb
        colour[y][x1] = rgb


def border_pixel_count(rect):
    x0, y0, x1, y1 = rect
    return 2 * (x1 - x0 + 1) + 2 * (y1 - y0 + 1) - 4


def draw_instrument(colour, row):
    """Draw the declared strip; return the frame's instrument receipt (exact
    string, origin, glyph-law expectation, strip census expectations)."""
    text = instrument_string(row)
    fill_rect(colour, INSTRUMENT_RECT, INSTRUMENT_BG)
    border_rect(colour, INSTRUMENT_RECT, INSTRUMENT_BORDER)
    draw_text(colour, text, INSTRUMENT_TEXT_X0, INSTRUMENT_TEXT_Y0,
              INSTRUMENT_SCALE, INSTRUMENT_INK)
    metrics = expected_text_metrics(text)
    return {"declared_instrument": DECLARED_INSTRUMENT,
            "text": text,
            "rect": list(INSTRUMENT_RECT),
            "text_x0": INSTRUMENT_TEXT_X0, "text_y0": INSTRUMENT_TEXT_Y0,
            "scale": INSTRUMENT_SCALE,
            "expected": metrics,
            "expected_counts": {
                "bg_px": ((INSTRUMENT_RECT[2] - INSTRUMENT_RECT[0] + 1)
                          * (INSTRUMENT_RECT[3] - INSTRUMENT_RECT[1] + 1)
                          - border_pixel_count(INSTRUMENT_RECT)
                          - metrics["pixel_count"]),
                "border_px": border_pixel_count(INSTRUMENT_RECT),
                "ink_px": metrics["pixel_count"]},
            "com_v_m_s_row": float(row["com_v_m_s"]),
            "row_tick": int(row["tick"])}


def _mask(arr, palette):
    return np.all(arr == np.array(palette, dtype=np.uint8), axis=2)


def _rect_mask(mask, rect):
    x0, y0, x1, y1 = rect
    out = np.zeros_like(mask)
    out[y0:y1 + 1, x0:x1 + 1] = mask[y0:y1 + 1, x0:x1 + 1]
    return out


# The declared overlap: on DIAGNOSTIC frames the X04 L1 panel (the pinned
# state_readout layer machinery, drawn after the instrument per the frozen
# layer law) fills row y=40 over x[12,300] — exactly the instrument's
# bottom border row (the frozen rects share that row; both are prereg
# constants). The declared overlap is 289 px of border; the ink text
# (y[14,24]) is untouched.
DIAG_BORDER_OVERLAP_PX = 300 - 12 + 1


def probe_instrument(arr, receipt, border_overlap_px=0):
    """The executed truthful-indicator probe (X-P4): the committed still's
    ink pixels and bbox inside the strip must EQUAL the glyph law exactly;
    the bg/border counts must match exactly (minus any DECLARED overlap,
    diag frames only); the rendered string must be exactly the derivation
    of the recorded row value."""
    text = receipt["text"]
    metrics = receipt["expected"]
    band = (INSTRUMENT_RECT[0], INSTRUMENT_RECT[1],
            INSTRUMENT_RECT[2], INSTRUMENT_RECT[3])
    ink = _rect_mask(_mask(arr, INSTRUMENT_INK), band)
    count = int(ink.sum())
    ys, xs = np.nonzero(ink)
    bbox = ([int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
            if count else None)
    exp_bbox = [receipt["text_x0"], receipt["text_y0"],
                receipt["text_x0"] + metrics["width_px"] - 1,
                receipt["text_y0"] + metrics["height_px"] - 1]
    bg = _rect_mask(_mask(arr, INSTRUMENT_BG), band)
    border = _rect_mask(_mask(arr, INSTRUMENT_BORDER), band)
    findings = {
        "text": text,
        "measured_ink_count": count,
        "expected_ink_count": metrics["pixel_count"],
        "measured_ink_bbox": bbox, "expected_ink_bbox": exp_bbox,
        "count_ok": count == metrics["pixel_count"],
        "bbox_ok": bbox == exp_bbox,
        "bg_px": int(bg.sum()),
        "bg_expected": receipt["expected_counts"]["bg_px"],
        "border_px": int(border.sum()),
        "border_expected": receipt["expected_counts"]["border_px"]
        - border_overlap_px,
        "declared_border_overlap_px": int(border_overlap_px),
        "truthful": text == "V=%.3f" % round(receipt["com_v_m_s_row"], 3),
    }
    findings["ok"] = (findings["count_ok"] and findings["bbox_ok"]
                      and findings["bg_px"] == findings["bg_expected"]
                      and findings["border_px"] == findings["border_expected"]
                      and findings["truthful"])
    return findings
