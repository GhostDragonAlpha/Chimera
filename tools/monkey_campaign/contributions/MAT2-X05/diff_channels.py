#!/usr/bin/env python3
"""MAT2-X05: the A-vs-B diff channels (prereg section 3).

Computed on DECODED FFV1 clean frames (A vs B per pair):
  - whole-frame diff count;
  - the declared LANDMARK channel (union of the four landmark palette masks);
  - the declared INSTRUMENT channel (the strip rect);
  - the declared BODY channel (body+legs palettes).
Per-frame series recorded in full, no thresholding beyond `count >= 1`.

Attribution law (amendment-A1 form): the zero-law binds
`presented_tick < consumed_tick` of the pair's command chain; the FIRST
LAWFUL slot for a nonzero diff is the first `presented_tick >= consumed_tick`
(consumed = issued + 1; first presented >= consumed). A pair whose whole-frame
diff REMAINS 0 on every declared frame records the finding
`no_pixel_reflection_in_window_persists` — the remediation FAILED for that
pair; recorded, never tuned (X-P5).
"""
from __future__ import annotations

import numpy as np

import landmarks_x05 as lm
import state_readout_x05 as srx

W, H = 960, 540
INSTRUMENT_RECT = (12, 8, 300, 40)


def frame_array(colour):
    """colour[y][x] tuple buffer -> (H, W, 3) uint8."""
    return np.asarray(colour, dtype=np.uint8)


def diff_count(a, b):
    """The whole-frame diff count between two decoded frames."""
    return int(np.count_nonzero(np.any(a != b, axis=2)))


def channel_masks(arr):
    """The declared per-frame channel masks."""
    lm_masks = lm_mask_union(arr)
    instr = np.zeros(arr.shape[:2], dtype=bool)
    x0, y0, x1, y1 = INSTRUMENT_RECT
    instr[y0:y1 + 1, x0:x1 + 1] = True
    body = srx.body_mask(arr)
    return {"landmark": lm_masks, "instrument": instr, "body": body}


def union_channel_masks(a, b):
    """The channel masks as the UNION of both arms' frames: a channel pixel
    that appears on only one side must count in that channel's diff."""
    ma, mb = channel_masks(a), channel_masks(b)
    return {k: (ma[k] | mb[k]) for k in ma}


def lm_mask_union(arr):
    masks = srx.landmark_masks(arr)
    union = None
    for m in masks.values():
        union = m if union is None else (union | m)
    return union


def _channel_diff(a, b, mask):
    if not mask.any():
        return 0
    return int(np.count_nonzero(np.any(a[mask] != b[mask], axis=1)))


def pair_series(frames_a, frames_b, present_ticks, consumed_tick):
    """The full per-frame A-vs-B channel series for one pair.

    frames_a/frames_b: decoded clean frames in PRESENT_TICKS order
    (list of (H, W, 3) uint8). consumed_tick: the pair's brake-chain ZOH
    boundary (the first state-divergent tick)."""
    rows = []
    for i, tick in enumerate(present_ticks):
        a, b = frames_a[i], frames_b[i]
        diff = diff_count(a, b)
        masks = union_channel_masks(a, b)
        row = {
            "presented_tick": int(tick),
            "lawful": bool(tick >= consumed_tick),
            "whole_frame_diff": diff,
            "landmark_channel_diff": _channel_diff(a, b, masks["landmark"]),
            "instrument_channel_diff": _channel_diff(a, b,
                                                     masks["instrument"]),
            "body_channel_diff": _channel_diff(a, b, masks["body"]),
        }
        rows.append(row)
    first_lawful = next((r for r in rows if r["lawful"]), None)
    series = {
        "consumed_tick": int(consumed_tick),
        "rows": rows,
        "pre_lawful_slots": [r for r in rows if not r["lawful"]],
        "pre_lawful_all_zero":
            all(r["whole_frame_diff"] == 0
                for r in rows if not r["lawful"]),
        "first_lawful_slot": (first_lawful or {}).get("presented_tick"),
        "first_lawful_whole_frame_diff":
            (first_lawful or {}).get("whole_frame_diff"),
        "first_lawful_landmark_diff":
            (first_lawful or {}).get("landmark_channel_diff"),
        "first_lawful_instrument_diff":
            (first_lawful or {}).get("instrument_channel_diff"),
        "persists_in_landmark_channel":
            bool(first_lawful is not None
                 and all(r["landmark_channel_diff"] >= 1
                         for r in rows if r["lawful"])),
        "persists_in_instrument_channel":
            bool(first_lawful is not None
                 and all(r["instrument_channel_diff"] >= 1
                         for r in rows if r["lawful"])),
    }
    series["no_pixel_reflection_in_window_persists"] = bool(
        all(r["whole_frame_diff"] == 0 for r in rows))
    return series


def landmark_channel_displacement(frames):
    """The measured net + cumulative displacement of the landmark-channel
    union-mask centroid across a window (X-P6's named variable)."""
    points = []
    for arr in frames:
        m = lm_mask_union(arr)
        ys, xs = np.nonzero(m)
        if not len(xs):
            points.append(None)
            continue
        points.append((float(xs.mean()), float(ys.mean())))
    known = [p for p in points if p is not None]
    if len(known) < 2:
        return {"net_px": 0.0, "cumulative_px": 0.0}
    net = ((known[-1][0] - known[0][0]) ** 2
           + (known[-1][1] - known[0][1]) ** 2) ** 0.5
    cum = sum(((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
              for a, b in zip(known, known[1:]))
    return {"net_px": round(net, 3), "cumulative_px": round(cum, 3)}
