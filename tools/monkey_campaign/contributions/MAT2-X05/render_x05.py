#!/usr/bin/env python3
"""MAT2-X05: the ONE render entry point (prereg section 2).

`render_frame_x05` (1) re-executes the pinned pose law over the committed
row, (2) builds the camera EXACTLY as the pinned `render_frame` follow law,
(3) draws the declared LANDMARK triangles through the pinned `f04.raster_tri`
into the SAME colour/depth buffers (depth-tested; drawn BEFORE the body),
(4) draws the body through the pinned `draw_pose` (imported, unmodified),
(5) draws the declared INSTRUMENT strip (its own glyph drawer), (6) returns.

The certified `visualization.py` bytes are imported, never edited. The
landmark-free path (`landmarks=None`, `instrument=False`) MUST be
byte-identical to the pinned renderer's own frame for the same rows (X-P2a)
— the executable proof that the layer is purely additive.
"""
from __future__ import annotations

import math

import landmarks_x05 as lm


def render_frame_x05(viz, f04, view, pose, diagnostic, tick, cmd_text,
                     landmark_set=None, instrument=False, ix_mod=None,
                     row=None):
    """One frame of the X05 presentation layer.

    landmark_set None + instrument False  -> byte-identical to the pinned
        viz.render_frame output for the same rows (X-P2a).
    landmark_set given                    -> the four world-fixed landmarks
        are rasterized before the body (same buffers, depth-tested).
    instrument True                       -> the declared velocity instrument
        strip is drawn last (screen-space, from the row's own value).
    """
    bx, bz = pose["body_xy"]
    # (2) the camera EXACTLY as the pinned render_frame follow law
    if view.get("follow"):
        pos = [bx + view["position"][0], view["position"][1],
               bz + view["position"][2]]
        tgt = [bx + view["target"][0], view["target"][1],
               bz + view["target"][2]]
    else:
        pos, tgt = list(view["position"]), list(view["target"])
    spec = {"position": pos, "target": tgt,
            "vfov_deg": view["vfov_deg"], "near_far": view["near_far"]}
    cam = f04.Camera(spec)
    near, far = view["near_far"]
    # the pinned F04 raster convention: colour[y][x] rgb tuples,
    # depth[y][x]; the pinned background fill (W10 render_frame, verbatim)
    colour = [[(168, 198, 150) for _ in range(960)] for _ in range(540)]
    depth = [[math.inf] * 960 for _ in range(540)]
    # (3) landmarks BEFORE the body, same buffers, depth-tested
    if landmark_set is not None:
        lm.draw_landmarks(cam, f04, colour, depth, landmark_set, near, far)
    # (4) the body through the pinned draw_pose (imported, unmodified)
    drawn = viz.draw_pose(cam, f04, colour, depth, pose, diagnostic,
                          near, far)
    if diagnostic:
        # the pinned diagnostic furniture, in the pinned order (X-P2a)
        viz.draw_glyph(colour, "1", 960 - 40, 10, 2, (180, 30, 30))
        viz.draw_overlay(colour, pose)
    # (5) the declared instrument strip (screen-space, topmost); the value
    # is derived from the presented frame's CONSUMED ROW (the pose is the
    # pinned pose law's output over that same row and carries its values
    # unchanged; the explicit row wins when the caller provides it)
    receipt = None
    if instrument:
        row_view = row if row is not None else {
            "com_v_m_s": pose["com_vel"], "tick": pose["tick"]}
        receipt = ix_mod.draw_instrument(colour, row_view)
    _ = tick
    _ = cmd_text
    return {"colour": colour, "depth": depth, "cam": cam,
            "triangles_drawn": int(drawn), "instrument_receipt": receipt}
