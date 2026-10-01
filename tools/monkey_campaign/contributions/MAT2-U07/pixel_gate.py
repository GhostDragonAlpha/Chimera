#!/usr/bin/env python3
"""MAT2-U07: the MECHANICAL pixel-content gate (correction r1, A4).

Motivation (review sgt-pr312-69772e91, PIXEL-FAIL): the previous sealed run
passed every STRUCTURE gate — 16/16 manifest fields, the pinned validator,
byte-identical side-view repeats — while ALL 32 committed frames were a
single uniform background colour. Structure cannot see an empty render.
This gate asserts PIXEL CONTENT on the DECODED frames of the committed
video bytes:

  (a) non-uniform content: every frame carries >= 2 unique colours;
  (b) body presence: the pinned renderer's body palette (thorax
      (120,80,60), left leg (200,60,50), right leg (60,90,200)) appears
      with at least the declared per-class minimum pixel count;
  (c) declared layers where declared: the overlay furniture (tick digits,
      stride bar, corner chip), the camera-target/frustum marker and the
      body-associated label marker on every diagnostic frame, and the
      declared occluder fill on the C_V2 obstructed view.

The palette constants are the PINNED renderer's own exact raster colours
(FFV1 bgr0 is lossless, so decoded pixels are exact). Minimum counts are
declared constants with recorded derivations — they are acceptance floors,
not tuned thresholds. A deliberately blank frame FAILS (planted-defect
selftest); a synthetic content-bearing frame PASSES (negative control).

Pure numpy + stdlib; no scene, registry or state access.
"""
from __future__ import annotations

import numpy as np

SCHEMA = "chimera.u07_pixel_gate.v1"

# The pinned renderer's exact colours (W10 visualization.py, unmodified):
BACKGROUND_RGB = (168, 198, 150)
BODY_PALETTE = {"thorax": (120, 80, 60),
                "leg_left": (200, 60, 50),
                "leg_right": (60, 90, 200)}
OVERLAY_PALETTE = {"tick_digits": (20, 20, 20),
                   "stride_bar_fill": (30, 90, 200),
                   "stride_bar_track": (210, 210, 210),
                   "corner_chip": (180, 30, 30)}
FRUSTUM_MARKER_RGB = (255, 0, 255)     # camera target + frustum diagnostics
BODY_LABEL_MARKER_RGB = (0, 220, 220)  # selected creature labels (body)
OCCLUDER_FILL_RGB = (60, 60, 70)       # declared C_V2 occluder box
CONTACT_PAD_RGB = {"hit": (0, 255, 0), "miss": (255, 140, 0)}  # informational

# Declared per-class floors. Derivations (recorded, not tuned): the floors
# were first declared from skeleton geometry, then CORRECTED once from the
# r1 dev-run census (sealed-run refusal D9 in DEV_RUN_REFUSALS.md) and
# re-frozen BEFORE the evidence run:
#   clean/diagnostic_view 200 px: the pinned body renders 385-418 px at the
#     C_V1 distance in the dev census; the floor sits at roughly half that
#     minimum and two orders above stray-pixel noise.
#   close_target 200 px: the dev census renders ~6300 px (floor far below).
#   side 100 px: the dev census renders 137-144 px at 4.06 m; the floor is
#     ~70 percent of the observed minimum, far above noise.
#   obstructed: body_min_px 0 WITH DECLARED REASON - the frozen occluder box
#     provably stands between camera and body (the P9 numerics: the target
#     lies inside the box's projected footprint) and the dev census shows it
#     FULLY conceals the body (fill 17678 px, body 0 px). Hiding that fact
#     would be the "concealed obstruction" falsifier; the required content
#     on obstructed frames is the occluder fill itself (floor 100 px,
#     measured ~17.7k), with the body count recorded informationally.
#   overlay: the pinned draw_overlay always paints the full 160x6 stride bar
#     region (>= 900 px), 3-4 tick digit glyphs (scale 2, >= 20 stroke px)
#     and the corner chip (>= 10 px).
#   frustum marker >= 40 px: crosshair (13x2 arms) + 4 corner brackets
#     (2x14 px each) = order 10^2 px; the crosshair alone exceeds 40.
#   body label marker >= 8 px: an 11x2-arm crosshair.
CLASS_LAW = {
    "clean_view":       {"body_min_px": 200, "diagnostics": False,
                         "occluder": False},
    "diagnostic_view":  {"body_min_px": 200, "diagnostics": True,
                         "occluder": False},
    "obstructed_clean": {"body_min_px": 0, "diagnostics": False,
                         "occluder": True,
                         "body_reason": "declared full occlusion allowed: "
                                        "the frozen occluder covers the "
                                        "target (P9 numerics); the occluder "
                                        "fill is the required content"},
    "obstructed_diag":  {"body_min_px": 0, "diagnostics": True,
                         "occluder": True,
                         "body_reason": "declared full occlusion allowed: "
                                        "the frozen occluder covers the "
                                        "target (P9 numerics); the occluder "
                                        "fill is the required content"},
    "close_target_clean": {"body_min_px": 200, "diagnostics": False,
                           "occluder": False},
    "side_clean":       {"body_min_px": 100, "diagnostics": False,
                         "occluder": False},
    "side_diag":        {"body_min_px": 100, "diagnostics": True,
                         "occluder": False},
}
MIN_OVERLAY_PX = {"tick_digits": 20, "stride_bar_region": 900,
                  "corner_chip": 10}
MIN_FRUSTUM_MARKER_PX = 40
MIN_BODY_LABEL_MARKER_PX = 8
MIN_OCCLUDER_FILL_PX = 100


def classify(meta):
    """The declared frame class from the render-plan metadata."""
    view = meta["view"]
    diag = bool(meta["diagnostic"])
    if view == "C_V1_normal_follow_distance":
        return "diagnostic_view" if diag else "clean_view"
    if view == "C_V2_obstructed":
        return "obstructed_diag" if diag else "obstructed_clean"
    if view == "C_V2_close_target":
        return "close_target_clean"
    if view == "C_V3_inspection_side":
        return "side_diag" if diag else "side_clean"
    raise ValueError("pixel_gate:unknown_view:" + str(view))


def _packed(frame):
    """(H,W,3) uint8 -> (H,W) uint32 0xRRGGBB (vectorized, exact)."""
    a = frame.astype(np.uint32)
    return (a[:, :, 0] << 16) | (a[:, :, 1] << 8) | a[:, :, 2]


def _count(frame_packed, rgb):
    key = (rgb[0] << 16) | (rgb[1] << 8) | rgb[2]
    return int(np.count_nonzero(frame_packed == key))


def gate_frame(frame, meta):
    """Gate ONE decoded frame against its declared class law.

    Returns the measurement row; 'failures' carries named codes (empty
    list = the frame PASSES its class law)."""
    klass = classify(meta)
    law = CLASS_LAW[klass]
    packed = _packed(frame)
    total = int(packed.size)
    unique = int(np.unique(packed).size)
    body = {name: _count(packed, rgb) for name, rgb in BODY_PALETTE.items()}
    overlay = {name: _count(packed, rgb)
               for name, rgb in OVERLAY_PALETTE.items()}
    row = {
        "frame_id": meta["frame_id"], "view": meta["view"],
        "tick": int(meta["tick"]), "diagnostic": bool(meta["diagnostic"]),
        "class": klass,
        "unique_colors": unique,
        "background_pixels": _count(packed, BACKGROUND_RGB),
        "background_fraction": round(_count(packed, BACKGROUND_RGB) / total,
                                     6),
        "body_palette_px": body,
        "body_palette_total": sum(body.values()),
        "overlay_px": overlay,
        "frustum_marker_px": _count(packed, FRUSTUM_MARKER_RGB),
        "body_label_marker_px": _count(packed, BODY_LABEL_MARKER_RGB),
        "occluder_fill_px": _count(packed, OCCLUDER_FILL_RGB),
        "contact_pad_px": {k: _count(packed, rgb) for k, rgb
                           in CONTACT_PAD_RGB.items()},
        "failures": [],
    }
    fid = meta["frame_id"]
    if unique < 2:
        row["failures"].append("pixel_gate:uniform_frame:" + fid)
    if row["body_palette_total"] < law["body_min_px"]:
        row["failures"].append(
            "pixel_gate:body_palette_missing:%s:%d/%d"
            % (fid, row["body_palette_total"], law["body_min_px"]))
    if law["diagnostics"]:
        if overlay["tick_digits"] < MIN_OVERLAY_PX["tick_digits"]:
            row["failures"].append("pixel_gate:overlay_tick_missing:" + fid)
        if (overlay["stride_bar_fill"] + overlay["stride_bar_track"]
                < MIN_OVERLAY_PX["stride_bar_region"]):
            row["failures"].append("pixel_gate:overlay_stride_bar_missing:"
                                   + fid)
        if overlay["corner_chip"] < MIN_OVERLAY_PX["corner_chip"]:
            row["failures"].append("pixel_gate:overlay_chip_missing:" + fid)
        if row["frustum_marker_px"] < MIN_FRUSTUM_MARKER_PX:
            row["failures"].append("pixel_gate:frustum_marker_missing:" + fid)
        if row["body_label_marker_px"] < MIN_BODY_LABEL_MARKER_PX:
            row["failures"].append("pixel_gate:body_label_missing:" + fid)
    if law["occluder"] and row["occluder_fill_px"] < MIN_OCCLUDER_FILL_PX:
        row["failures"].append("pixel_gate:occluder_missing:" + fid)
    return row


def run_gate(frames, metas):
    """Gate EVERY declared frame (order = render plan order).

    Returns the receipt; verdict GREEN only when every frame passes its
    declared class law."""
    require(len(frames) == len(metas),
            "pixel_gate:plan_mismatch:%d:%d" % (len(frames), len(metas)))
    rows = [gate_frame(np.asarray(f, dtype=np.uint8), m)
            for f, m in zip(frames, metas)]
    failures = [c for r in rows for c in r["failures"]]
    return {
        "schema": SCHEMA,
        "law": "decoded-pixel content gate: non-uniform content, body "
               "palette presence (declared per-class floors), declared "
               "diagnostics layers and occluder where declared "
               "(correction r1, AMENDMENT-A4)",
        "palette": {"background": list(BACKGROUND_RGB),
                    "body": {k: list(v) for k, v in BODY_PALETTE.items()},
                    "overlay": {k: list(v)
                                for k, v in OVERLAY_PALETTE.items()},
                    "frustum_marker": list(FRUSTUM_MARKER_RGB),
                    "body_label_marker": list(BODY_LABEL_MARKER_RGB),
                    "occluder_fill": list(OCCLUDER_FILL_RGB),
                    "contact_pad": {k: list(v) for k, v
                                    in CONTACT_PAD_RGB.items()}},
        "class_law": CLASS_LAW,
        "min_overlay_px": MIN_OVERLAY_PX,
        "min_frustum_marker_px": MIN_FRUSTUM_MARKER_PX,
        "min_body_label_marker_px": MIN_BODY_LABEL_MARKER_PX,
        "min_occluder_fill_px": MIN_OCCLUDER_FILL_PX,
        "frames_decoded": len(rows),
        "frames_with_body_palette": sum(1 for r in rows
                                        if r["body_palette_total"] > 0),
        "frames_non_uniform": sum(1 for r in rows
                                  if r["unique_colors"] >= 2),
        "frames": rows,
        "failure_codes": failures,
        "first_failure_code": failures[0] if failures else None,
        "verdict": "GREEN" if not failures else "RED",
    }


def require(condition, code):
    if not condition:
        raise RuntimeError("REFUSAL:" + str(code))


def _synth_clean_frame(body=True):
    """Background + (optional) body-palette blocks (the negative control)."""
    f = np.empty((540, 960, 3), dtype=np.uint8)
    f[:, :] = BACKGROUND_RGB
    if body:
        f[200:240, 400:460] = BODY_PALETTE["thorax"]      # 2400 px
        f[240:340, 420:430] = BODY_PALETTE["leg_left"]    # 1000 px
        f[240:340, 432:442] = BODY_PALETTE["leg_right"]   # 1000 px
    return f


def _add_overlay(frame):
    """The pinned overlay furniture (exact palette pixels, >= floors)."""
    frame[10:16, 12:60] = OVERLAY_PALETTE["tick_digits"]       # >= 20 px
    frame[514:520, 12:172] = OVERLAY_PALETTE["stride_bar_track"]
    frame[514:520, 12:100] = OVERLAY_PALETTE["stride_bar_fill"]
    frame[10:18, 920:928] = OVERLAY_PALETTE["corner_chip"]     # >= 10 px
    return frame


def _add_markers(frame):
    frame[270:290, 470:490] = FRUSTUM_MARKER_RGB               # 400 px
    frame[300:310, 500:510] = BODY_LABEL_MARKER_RGB            # 100 px
    return frame


def selftest():
    """The planted-defect selftest (AMENDMENT-A4): a deliberately blank
    frame MUST fail the gate; the historical overlay-only defect (a clean
    frame with furniture but NO body) MUST fail body presence; content-
    bearing frames of each declared class MUST pass. Returns the record;
    raises REFUSAL on any unexpected outcome."""
    blank = _synth_clean_frame(body=False)
    blank_row = gate_frame(blank, {"frame_id": "PLANTED_BLANK",
                                   "view": "C_V1_normal_follow_distance",
                                   "tick": 0, "diagnostic": False})
    planted_uniform = any(c.startswith("pixel_gate:uniform_frame:")
                          for c in blank_row["failures"])
    planted_body = any(c.startswith("pixel_gate:body_palette_missing:")
                       for c in blank_row["failures"])

    hist = _add_overlay(_synth_clean_frame(body=False))
    hist_row = gate_frame(hist, {"frame_id": "HISTORICAL_OVERLAY_ONLY",
                                 "view": "C_V1_normal_follow_distance",
                                 "tick": 0, "diagnostic": False})
    hist_body = any(c.startswith("pixel_gate:body_palette_missing:")
                    for c in hist_row["failures"])
    hist_uniform_ok = hist_row["unique_colors"] >= 2   # furniture only is
    # non-uniform: the STRUCTURE-blind defect this gate exists for

    healthy = _add_markers(_synth_clean_frame(body=True))
    healthy_row = gate_frame(healthy, {"frame_id": "HEALTHY_CLEAN",
                                       "view": "C_V1_normal_follow_distance",
                                       "tick": 0, "diagnostic": False})

    diag = _add_markers(_add_overlay(_synth_clean_frame(body=True)))
    diag_row = gate_frame(diag, {"frame_id": "HEALTHY_DIAG",
                                 "view": "C_V1_normal_follow_distance",
                                 "tick": 0, "diagnostic": True})

    occl = _synth_clean_frame(body=True)
    occl[100:180, 380:520] = OCCLUDER_FILL_RGB                 # 11200 px
    occl_row = gate_frame(occl, {"frame_id": "HEALTHY_OCCLUDED",
                                 "view": "C_V2_obstructed",
                                 "tick": 0, "diagnostic": False})
    occl_missing = _synth_clean_frame(body=True)
    occl_missing_row = gate_frame(
        occl_missing, {"frame_id": "OCCLUDER_ABSENT",
                       "view": "C_V2_obstructed",
                       "tick": 0, "diagnostic": False})
    occl_bite = any(c.startswith("pixel_gate:occluder_missing:")
                    for c in occl_missing_row["failures"])

    require(planted_uniform and planted_body,
            "pixel_gate_selftest:blank_frame_not_refused")
    require(hist_body and hist_uniform_ok,
            "pixel_gate_selftest:historical_defect_not_refused")
    require(not healthy_row["failures"],
            "pixel_gate_selftest:healthy_clean_rejected:"
            + ",".join(healthy_row["failures"]))
    require(not diag_row["failures"],
            "pixel_gate_selftest:healthy_diag_rejected:"
            + ",".join(diag_row["failures"]))
    require(not occl_row["failures"],
            "pixel_gate_selftest:healthy_occluded_rejected:"
            + ",".join(occl_row["failures"]))
    require(occl_bite, "pixel_gate_selftest:occluder_law_no_bite")
    return {
        "schema": "chimera.u07_pixel_gate_selftest.v1",
        "planted_blank_frame": {"verdict": "RED" if blank_row["failures"]
                                else "GREEN",
                                "refused_uniform": planted_uniform,
                                "refused_body_absent": planted_body},
        "historical_overlay_only_frame": {
            "verdict": "RED" if hist_row["failures"] else "GREEN",
            "non_uniform_as_expected": hist_uniform_ok,
            "refused_body_absent": hist_body},
        "negative_controls_pass": {
            "clean": "GREEN" if not healthy_row["failures"] else "RED",
            "diagnostic": "GREEN" if not diag_row["failures"] else "RED",
            "obstructed": "GREEN" if not occl_row["failures"] else "RED"},
        "occluder_absence_bites": occl_bite,
        "verdict": "GREEN",
    }


if __name__ == "__main__":
    print(selftest()["verdict"])
