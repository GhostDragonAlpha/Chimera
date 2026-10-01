#!/usr/bin/env python3
"""MAT2-U07: the declared camera views, occlusion probe and render helpers
(prereg section 5).

The camera LAW is the pinned U02 follow-camera geometry (its constants are
consumed through the pinned bytes; its HTTP transport is NOT — absent
inventory A4). The render path is W10's records-only software renderer,
imported UNMODIFIED from the byte-verified extraction. The render WRITES NO
state (P10; W10 FB6 sealed heritage).

Every geometric constant here is declared in the frozen preregistration
(section 5); nothing is discovered at run time.
"""
from __future__ import annotations

import math

import controls_harness as ch

require = ch.require

# --- declared views (body-anchored offsets; clearing frame x,z ground, y up)
U07_VIEWS = {
    "C_V1_normal_follow_distance": {
        "profile_name": "normal follow-camera distance",
        "position": [1.2, 1.6, 3.2], "target": [0.0, 0.5, 0.0],
        "vfov_deg": 50.0, "near_far": [0.05, 50.0]},
    "C_V2_obstructed": {
        "profile_name": "obstructed view",
        "position": [1.2, 1.6, 3.2], "target": [0.0, 0.5, 0.0],
        "vfov_deg": 50.0, "near_far": [0.05, 50.0]},
    "C_V2_close_target": {
        "profile_name": "close-target view",
        "position": [0.35, 0.7, 0.9], "target": [0.0, 0.5, 0.0],
        "vfov_deg": 45.0, "near_far": [0.01, 10.0]},
    "C_V3_inspection_side": {
        "profile_name": "repeatable inspection side view",
        "position": [0.0, 1.2, 4.0], "target": [0.0, 0.5, 0.0],
        "vfov_deg": 40.0, "near_far": [0.05, 50.0]},
}
VIEW_ORDER = ["C_V1_normal_follow_distance", "C_V2_obstructed",
              "C_V2_close_target", "C_V3_inspection_side"]
CLEAN_VIEW = "C_V1_normal_follow_distance"

# The declared occluder box (prereg section 5), body-anchored offsets, metres.
OCCLUDER = {"x": [-0.35, 0.35], "y": [0.5, 1.0], "z": [0.4, 0.8]}

# Declared frame plan (prereg section 3, camera arms; frozen numbers).
WINDOW = ch.WINDOW                # consumed-tick window [W0, W1)
WINDOW_STRIDE = ch.WINDOW_STRIDE  # one presentation frame per seam poll
PRESENT_TICKS = list(range(4365, 4666, 15))      # 21 presentation frames
DIAG_TICKS = [4365, 4500, 4650]                  # C_V1 diagnostic frames
OBSTRUCTED_TICKS = [4500]                        # obstructed clean+diagnostic
CLOSE_TICKS = [4500, 4650]                       # close-target clean frames
SIDE_TICK = 4365                                 # rendered TWICE (identity)


AXIS_INDEX = {"x": 0, "y": 1, "z": 2}


def seg_box_intersect(eye, target, box):
    """Segment-box intersection (slab method, inclusive bounds).

    eye/target are (x, y, z) sequences; box maps axis -> [lo, hi].
    Returns (hit, t_enter, t_exit) with t in [0,1] along eye->target.
    Pure declared arithmetic (prereg section 5); no scene access.
    """
    lo, hi = 0.0, 1.0
    for axis in ("x", "y", "z"):
        i = AXIS_INDEX[axis]
        d = target[i] - eye[i]
        b0, b1 = box[axis]
        if abs(d) < 1e-12:
            if not (b0 <= eye[i] <= b1):
                return False, None, None
            continue
        t0 = (b0 - eye[i]) / d
        t1 = (b1 - eye[i]) / d
        if t0 > t1:
            t0, t1 = t1, t0
        lo, hi = max(lo, t0), min(hi, t1)
        if lo > hi:
            return False, None, None
    return True, lo, hi


def convex_hull(points):
    """Monotone chain; points are (px, py) float pairs."""
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def point_in_hull(pt, hull):
    """Inclusive point-in-convex-polygon test."""
    n = len(hull)
    if n < 3:
        return False

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    signs = [cross(hull[i], hull[(i + 1) % n], pt) for i in range(n)]
    return all(s >= -1e-9 for s in signs) or all(s <= 1e-9 for s in signs)


def box_corner_offsets(box):
    xs, ys, zs = box["x"], box["y"], box["z"]
    return [(x, y, z) for x in xs for y in ys for z in zs]


def occlusion_probe(cam, view):
    """The declared obstruction probe, executed numerically (P9).

    Returns the named variables: ray intersection, occluder-in-front,
    target-inside-projected-footprint, plus the recorded geometry. The
    occluder EXISTS in this probe by declaration; concealment would be a
    missing/contradictory record, which the manifest structure forbids.
    """
    eye = tuple(view["position"])
    target = tuple(view["target"])
    hit, t0, t1 = seg_box_intersect(eye, target, OCCLUDER)
    eye_t = math.dist(eye, target)
    corners = box_corner_offsets(OCCLUDER)
    pixels = []
    for c in corners:
        pix = cam.pixel(list(c))
        require(pix is not None,
                "occlusion_corner_behind_camera:" + repr(c))
        pixels.append((float(pix[0]), float(pix[1])))
    tpix = cam.pixel(list(target))
    require(tpix is not None, "occlusion_target_behind_camera")
    tx, ty = float(tpix[0]), float(tpix[1])
    hull = convex_hull(pixels)
    covered = point_in_hull((float(tx), float(ty)), hull)
    return {
        "occluder_box_m": OCCLUDER,
        "eye_offset_m": list(eye), "target_offset_m": list(target),
        "segment_hits_box": bool(hit),
        "segment_enter_exit_t": [t0, t1] if hit else None,
        "occluder_in_front_of_target": bool(hit) and (t1 < 1.0 + 1e-12),
        "eye_to_target_distance_m": eye_t,
        "target_pixel": [float(tx), float(ty)],
        "box_corner_pixels": pixels,
        "target_inside_box_screen_footprint": bool(covered),
        "occlusion_declared": bool(hit and covered),
        "method": "segment-box slab test + 8-corner perspective projection "
                  "+ convex-hull containment (inclusive bounds)",
    }


def camera_view_record(cam, view, ticks, *, occlusion_mode, labels,
                       layers, frame_id, tick_interval):
    """The per-view camera record carrying the profile's EXACT
    camera_required_fields (asserted complete by the caller)."""
    rec = dict(cam.camera_record(ticks))
    rec["frame_id"] = frame_id
    rec["coordinate_unit"] = "m"
    rec["orientation_convention_and_values"] = {
        "convention": "quaternion_wxyz_camera_to_frame",
        "quaternion_wxyz": list(cam.quaternion_wxyz())}
    rec["target"] = list(view["target"])
    rec["distance_to_target"] = float(cam.distance_to_target)
    rec["projection"] = "perspective"
    rec["vertical_fov_or_orthographic_span"] = float(view["vfov_deg"])
    rec["near_far_planes"] = list(view["near_far"])
    rec["camera_motion_or_bookmark_sequence"] = {
        "sample_mode": "fixed_bookmark", "ticks": list(ticks)}
    rec["visibility_layers"] = list(layers)
    rec["label_ids"] = list(labels)
    rec["occlusion_or_xray_mode"] = occlusion_mode
    rec["state_or_tick_interval"] = list(tick_interval)
    return rec


def render_frames(f04, vz, rows, geom, view_spec_by_name, plan):
    """Render the declared frame plan from R1's per-tick records ONLY.

    plan: the declared frame list [{"frame_id", "view", "tick",
    "diagnostic", "render_index"}]. Returns the frame colour buffers (in
    plan order) plus per-frame metadata rows. The render consumes records
    only; state_chain was recorded BEFORE any render call (P10).
    """
    def row_at(tick):
        for r in rows:
            if r["tick"] == tick:
                return r
        raise RuntimeError("REFUSAL:render_tick_missing:" + str(tick))

    colours = []
    metas = []
    for spec in plan:
        view = view_spec_by_name[spec["view"]]
        row = row_at(spec["tick"])
        body_xy = (row["com_x_m"], 0.0)
        pose = vz.pose_at(row, geom, 0.0, body_xy)
        colour, drawn, cam = vz.render_frame(
            f04, view, pose, spec["diagnostic"], spec["tick"],
            "t%d v=%.3f %s" % (spec["tick"], row["com_v_m_s"],
                               spec["view"]))
        colours.append(colour)
        metas.append({"frame_id": spec["frame_id"], "view": spec["view"],
                      "tick": spec["tick"],
                      "diagnostic": spec["diagnostic"],
                      "render_index": spec["render_index"],
                      "triangles_drawn": int(drawn),
                      "state_sha256": row["state_sha256"],
                      "anchor_xy": [row["com_x_m"], 0.0]})
    return colours, metas


def build_frame_plan():
    """The declared render plan (deterministic order; frozen numbers)."""
    plan = []
    idx = 0

    def add(view, tick, diagnostic, frame_id):
        nonlocal idx
        plan.append({"frame_id": frame_id, "view": view, "tick": tick,
                     "diagnostic": diagnostic, "render_index": idx})
        idx += 1

    for k, tick in enumerate(PRESENT_TICKS):
        add(CLEAN_VIEW, tick, False, "P%02d_%s_t%d" % (k, CLEAN_VIEW, tick))
    for tick in DIAG_TICKS:
        add(CLEAN_VIEW, tick, True, "D_%s_t%d" % (CLEAN_VIEW, tick))
    for tick in OBSTRUCTED_TICKS:
        add("C_V2_obstructed", tick, False, "O_clean_t%d" % tick)
        add("C_V2_obstructed", tick, True, "O_diag_t%d" % tick)
    for tick in CLOSE_TICKS:
        add("C_V2_close_target", tick, False, "C_clean_t%d" % tick)
    add("C_V3_inspection_side", SIDE_TICK, False, "S_pass1_t%d" % SIDE_TICK)
    add("C_V3_inspection_side", SIDE_TICK, False, "S_pass2_t%d" % SIDE_TICK)
    add("C_V3_inspection_side", SIDE_TICK, True, "S_pass1_diag_t%d" % SIDE_TICK)
    add("C_V3_inspection_side", SIDE_TICK, True, "S_pass2_diag_t%d" % SIDE_TICK)
    return plan


def presented_frames_for(window_seqs, res):
    """Map each window chain to its REAL presented frame (P3).

    The chain's consumed tick c (≡1 mod 15) is presented by the first
    declared stride tick f >= c; lag = f - c <= WINDOW_STRIDE.
    """
    tracer = res["_tracer"]
    consumed = {e["seq"]: int(e["payload"]["consumed_tick"])
                for e in tracer.events()
                if e["stage"] == "simulation_consumed"}
    frames = []
    for seq in window_seqs:
        c = consumed[seq]
        f = next((t for t in PRESENT_TICKS if t >= c), None)
        if f is None:
            raise RuntimeError("REFUSAL:presentation_gap:seq%d:t%d"
                               % (seq, c))
        frames.append({"seq": int(seq), "consumed_tick": c,
                       "presented_tick": int(f),
                       "frame_id": "P%02d_%s_t%d"
                       % (PRESENT_TICKS.index(f), CLEAN_VIEW, f),
                       "view": CLEAN_VIEW})
    return frames
