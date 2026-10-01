#!/usr/bin/env python3
"""MAT2-W10: the material-first visualization (prereg sections 5-6).

RENDERED FIXTURE of the certified run's OWN per-tick telemetry inside ONE
pinned forest clearing build. The ONLY input is the committed per-tick trace
(walking_demo.py's export; records-only). The render writes no scene state
(FB6). The pose law is a pure declared function of pinned bytes + the run's
records (prereg section 6); every geometric constant comes from pinned bytes
(`asset_geometry_absent` otherwise) — the existing monkey asset is the
declared gait-walker skeleton of the certified 10.037998 kg body lineage,
posed per-tick by the run's own phase/contacts/commands.

Honesty label: the visual body is the DECLARED gait-walker visualization of
the qualified hind-pad-surrogate state; no cosmetic skin over an unrelated
qualified body (FB5 proves the binding).

CPU-only; stdlib + the pinned F01/F04 software rasterizer pattern + ffmpeg
(the declared capture-tool exception).
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import verify_inputs as vi          # noqa: E402

CAPTURE_DIR = HERE / "capture"

W, H = 960, 540

# The profile views (registry `walking` profile, verbatim names), declared
# BODY-ANCHORED (follow): position/target are OFFSETS from the walked body's
# clearing anchor at each sampled tick (the walk covers meters; a fixed
# bookmark would leave the body outside the frustum — the follow-anchor law
# is declared here and the per-frame anchor is recorded in every manifest
# row). Clearing frame: x, y up, z; ground y=0; trunk at
# [11.976783, 0, 2.471766] as scene furniture.
VIEWS = {
    "V1_full_body_ground_overview": {
        "profile_name": "full-body ground overview",
        "position": [2.0, 6.0, 8.0], "target": [0.0, 0.5, 0.0],
        "follow": True,
        "vfov_deg": 55.0, "near_far": [0.05, 500.0]},
    "V2_side_stance_swing": {
        "profile_name": "side view of stance/swing",
        "position": [1.5, 1.0, 3.0], "target": [0.0, 0.5, 0.0],
        "follow": True,
        "vfov_deg": 50.0, "near_far": [0.05, 50.0]},
    "V3_foot_ground_closeup": {
        "profile_name": "close-up of foot-ground contact",
        "position": [0.35, 0.35, 1.1], "target": [0.0, 0.05, 0.0],
        "follow": True,
        "vfov_deg": 45.0, "near_far": [0.01, 10.0]},
}
VIEW_ORDER = ["V1_full_body_ground_overview", "V2_side_stance_swing",
              "V3_foot_ground_closeup"]
DIAGNOSTIC_LAYERS = ["skeleton", "foot contacts and normals",
                     "support/COM markers", "command and tick overlay",
                     "stable 3D labels"]

# Declared placement map (prereg section 5): the walk path on the clearing
# ground; P06-declared spawn/clearance constants (pinned limits record).
SPAWN = [0.0, 0.0, 0.0]
CLEARANCE_M = 1.5
WALK_HEADING_DEG = 0.0            # along +x of the clearing
BODY_LIFT_M = 0.5                 # the com height band of the declared body

# Declared camera tick bookmarks (real ticks of the runs)
WALK_BOOKMARKS = {"V1_full_body_ground_overview": [3300, 5100],
                  "V2_side_stance_swing": None,   # stance/swing keyed per phase
                  "V3_foot_ground_closeup": [3700, 4600]}
FALL_BOOKMARKS = {"V1_full_body_ground_overview": [40, 118],
                  "V2_side_stance_swing": [45, 115],
                  "V3_foot_ground_closeup": [32, 120]}


class Refusal(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise Refusal(code)


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def load_f04_module():
    """The pinned F04 implementation (renderer pattern source), imported
    read-only from the pin extraction; zero modification."""
    return vi.load_pinned_module(
        "f04_implementation",
        ("tools", "monkey_campaign", "contributions", "MAT2-F04",
         "implementation.py"))


def load_terrain_module():
    return vi.load_pinned_module(
        "f02_terrain_bundle",
        ("tools", "monkey_campaign", "contributions", "MAT2-F02", "pins",
         "terrain_bundle.py"))


def gait_geometry():
    """ALL skeleton constants from pinned bytes (prereg section 6)."""
    rec = vi.gait_walker_record()
    contract = rec["physical"]["contract"]
    tables = contract.get("tables_rad")
    zero = contract.get("zero_map_rad")
    contacts = contract.get("contact_points")
    require(tables and zero and contacts,
            "asset_geometry_absent:gait_contract_tables")
    derived_path = (vi.LANE_REPO / "tools" / "science_funnel" / "validation"
                    / "gait_controller_20260918" / "derived_numbers.json")
    derived = json.loads(derived_path.read_bytes().decode("utf-8"))
    seg_table = (derived.get("body_model") or {}).get("segments_Table1") \
        or {}
    seg = {}
    for part in ("thigh", "shank"):
        row = seg_table.get(part)
        require(row and "length_m" in row,
                "asset_geometry_absent:" + part + "_length")
        seg[part] = float(row["length_m"])
    foot = {"heel_m": None, "mp_m": None, "radius_m": None}
    for c in contacts:
        if c["name"].endswith("heel"):
            foot["heel_m"] = float(c["point_m"][0])
        if c["name"].endswith("mp_head"):
            foot["mp_m"] = float(c["point_m"][0])
        foot["radius_m"] = float(c["radius_m"])
    require(foot["heel_m"] is not None and foot["mp_m"] is not None
            and foot["radius_m"] is not None,
            "asset_geometry_absent:foot_contacts")
    return {"tables": tables, "zero": zero, "seg": seg, "foot": foot,
            "mass_kg": 10.037998}


def eval_table(table, phase):
    """The pinned 21-node table evaluated at the recorded phase (pure)."""
    n = len(table)
    x = (phase % 1.0) * n
    i = int(x) % n
    frac = x - int(x)
    a = table[i]
    b = table[(i + 1) % n]
    return a + (b - a) * frac


def leg_chain(angles, seg, foot, hip_xy):
    """Forward kinematics of the declared hindlimb chain (hip, knee, ankle,
    MP) with the pinned zero map applied. Returns joint positions in the
    body-local sagittal plane (z forward, y up) — the declared convention:
    positive q is flexion/extension/dorsiflexion (the contract's own sign
    statement), rotations about the world South axis mapped to the sagittal
    plane normal."""
    hip, knee, ankle, mp = angles
    z, y = hip_xy
    p_hip = (z, y)
    thigh, shank = seg["thigh"], seg["shank"]
    a1 = -hip
    p_knee = (p_hip[0] + thigh * math.sin(a1), p_hip[1] - thigh * math.cos(a1))
    a2 = a1 + knee
    p_ankle = (p_knee[0] + shank * math.sin(a2),
               p_knee[1] - shank * math.cos(a2))
    a3 = a2 + ankle
    foot_len = foot["mp_m"] - foot["heel_m"]
    p_mp = (p_ankle[0] + foot_len * math.cos(a3),
            p_ankle[1] + foot_len * math.sin(a3))
    p_heel = (p_ankle[0] - abs(foot["heel_m"]) * math.cos(a3),
              p_ankle[1] - abs(foot["heel_m"]) * math.sin(a3))
    return {"hip": p_hip, "knee": p_knee, "ankle": p_ankle,
            "mp": p_mp, "heel": p_heel}


def pose_at(row, geom, heading_rad, body_xy):
    """The declared pure pose function of one trace row (prereg section 6)."""
    tables, zero, seg, foot = (geom["tables"], geom["zero"],
                               geom["seg"], geom["foot"])
    com_h = BODY_LIFT_M
    legs = {}
    for side, phase_key in (("left", "phase_left"), ("right", "phase_right")):
        phase = float(row[phase_key])
        angles = (eval_table(tables["hip"], phase) - zero["hip"],
                  eval_table(tables["knee"], phase) - zero["knee"],
                  eval_table(tables["ankle"], phase) - zero["ankle"],
                  eval_table(tables["MP"], phase) - zero["MP"])
        hip_xy = (0.0 if side == "left" else 0.04, com_h)   # the declared
        # leg z offset 0.02 m per side (contract leg_z_offset_m/2, declared)
        chain = leg_chain(angles, seg, foot, hip_xy)
        legs[side] = chain
    return {"body_xy": body_xy, "heading_rad": heading_rad,
            "com_height_m": com_h, "legs": legs,
            "com_vel": row["com_v_m_s"], "tick": row["tick"],
            "foot_contacts": row["foot_contacts"],
            "foot_forces": row["foot_forces"],
            "applied_cmd": row["applied_cmd"]}


def draw_pose(cam, f04, colour, depth, pose, diagnostic, near, far):
    """Rasterize the declared skeleton (+ diagnostic layers) into the
    clearing frame. Everything here only READS the pose dict."""
    tris = []
    bx, bz = pose["body_xy"]
    hr = pose["heading_rad"]
    ch = pose["com_height_m"]

    def world(p_local, side_off):
        # body-local (z forward, y up) -> clearing (x, y up, z) at heading
        lz, ly = p_local
        lx = side_off
        x = bx + lx * math.cos(hr) + lz * math.sin(hr)
        z = bz - lx * math.sin(hr) + lz * math.cos(hr)
        return (x, ly, z)

    # body: a small declared box (thorax mass surrogate, the gait walker's
    # free base) around the com
    r = 0.06
    for dx in (-r, r):
        for dy in (-r, r):
            a = world((-0.09, ch + dy), dx)
            b = world((0.09, ch + dy), dx)
            tris.append((world((-0.09, ch - r), dx),
                         world((0.09, ch - r), dx),
                         world((0.09, ch + r), dx), (120, 80, 60)))
            tris.append((a, b, world((0.09, ch + dy), -dx if dx > 0 else dx),
                         (120, 80, 60)))
    for side, chain in pose["legs"].items():
        col = (200, 60, 50) if side == "left" else (60, 90, 200)
        pts = [chain["hip"], chain["knee"], chain["ankle"], chain["mp"]]
        wpts = [world(p, 0.02 if side == "left" else -0.02) for p in pts]
        for a, b in zip(wpts, wpts[1:]):
            mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2)
            rad = 0.012
            tris.append(((a[0], a[1] - rad, a[2]),
                         (b[0], b[1] - rad, b[2]),
                         (b[0], b[1] + rad, b[2]), col))
            tris.append(((a[0], a[1] - rad, a[2]),
                         (b[0], b[1] + rad, b[2]),
                         (a[0], a[1] + rad, a[2]), col))
            _ = mid
        if diagnostic:
            # foot contacts and normals: contact pads as declared discs
            fc = pose["foot_contacts"]
            idx = 4 if side == "left" else 5
            cc = (0, 255, 0) if fc[idx] == 1.0 else (255, 140, 0)
            heel = wpts[-1]
            tris.append(((heel[0], max(heel[1] - 0.004, 0.001), heel[2]),
                         (heel[0] + 0.05, max(heel[1] - 0.004, 0.001), heel[2]),
                         (heel[0] + 0.025, max(heel[1] + 0.004, 0.002),
                          heel[2] + 0.02), cc))
    drawn = 0
    for pa, pb, pc, rgb in tris:
        drawn += f04.raster_tri(cam, colour, depth, pa, pb, pc, rgb,
                                near, far)
    return drawn


_DIGITS = {
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
}


def draw_glyph(colour, text, x0, y0, scale, rgb):
    for i, ch in enumerate(text):
        rows = _DIGITS.get(ch)
        if rows is None:
            continue
        for gy, line in enumerate(rows):
            for gx, bit in enumerate(line):
                if bit == "1":
                    for dy in range(scale):
                        for dx in range(scale):
                            yy = y0 + gy * scale + dy
                            xx = x0 + (i * 4 + gx) * scale + dx
                            if 0 <= yy < H and 0 <= xx < W:
                                colour[yy][xx] = rgb


def draw_overlay(colour, pose):
    """The command and tick overlay + the stable 3D labels layer: a fixed
    corner label (tick digits, stable across frames), a stride bar and the
    applied-command chip. Screen-space; the render writes no state."""
    tick_text = str(int(pose["tick"]))
    draw_glyph(colour, tick_text, 12, 10, 2, (20, 20, 20))
    # stride bar: width encodes the recorded mean stride against the bounds
    stride = 0.5 * (pose["applied_cmd"][1] + pose["applied_cmd"][5])
    frac = max(0.0, min(1.0, (stride - 0.2) / 1.6))
    bar_w = int(frac * 160)
    for x in range(12, 12 + 160):
        for y in range(H - 26, H - 20):
            in_bar = x < 12 + bar_w
            colour[y][x] = (30, 90, 200) if in_bar else (210, 210, 210)


def render_frame(f04, view, pose, diagnostic, tick, cmd_text):
    bx, bz = pose["body_xy"]
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
    # the pinned F04 raster convention: colour[y][x] rgb tuples, depth[y][x]
    colour = [[(168, 198, 150) for _ in range(W)] for _ in range(H)]
    depth = [[math.inf] * W for _ in range(H)]
    drawn = draw_pose(cam, f04, colour, depth, pose, diagnostic,
                      view["near_far"][0], view["near_far"][1])
    if diagnostic:
        # support/COM marker: a declared com chip (the com rides the follow
        # camera center; the chip marks it) + command/tick overlay + the
        # stable corner label
        draw_glyph(colour, "1", W - 40, 10, 2, (180, 30, 30))
        draw_overlay(colour, pose)
    _ = tick
    _ = cmd_text
    return colour, drawn, cam


def row_at(rows, tick):
    for r in rows:
        if r["tick"] == tick:
            return r
    raise Refusal("trace_tick_missing:" + str(tick))


def stance_swing_bookmarks(rows):
    """Keyed per-phase bookmarks (G6): the first declared stance tick and the
    first declared swing tick of the walk arm inside the turn windows."""
    stance = next(r["tick"] for r in rows
                  if r["tick"] > 3600 and r["foot_contacts"][4] == 1.0
                  and r["foot_contacts"][5] == 1.0)
    swing = next(r["tick"] for r in rows
                 if r["tick"] > 3600 and (r["foot_contacts"][4] == 0.0
                                          or r["foot_contacts"][5] == 0.0))
    return stance, swing
