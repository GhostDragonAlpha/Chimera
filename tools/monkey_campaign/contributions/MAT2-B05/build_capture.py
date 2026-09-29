"""MAT2-B05 capture builder — motion-profile (grasp) replay, frames, video,
manifest and validation.

Pipeline (run from this directory):
    python -B build_capture.py <attempt_capture_dir> <ffmpeg_path> \
        <registry_sqlite_path>

1. derive() the committed mechanical port requirements document; the replay
   consumes its DECLARED values only (attachment stiffness k = kappa_areal *
   A_patch from the C17 requirement check; hook stiffness from pinned M05
   K_TENSION_N_PER_M).
2. deterministic replay of the profile procedure: approach, attach, load,
   hold, TRANSFER (declared carriage + hook carry the load, supported at every
   tick, strap unbound during transfer), release (all bond/patch forces bitwise
   zero, stored elastic energy dissipated as a reported ledger term) —
   attachment and force telemetry per tick.
3. render the structured-records sheets (top row diagnostic viewports, middle
   row clean viewports with identical cameras, bottom row telemetry traces +
   honest footer), encode ONE mkv, and bind:
   subject_sha256 = sha256(mechanical_port_requirements.json),
   state_binding  = sha256(replay_trace.json),
   capture_sha256 = sha256(mkv)  (single on-disk artifact).
4. the verification PROFILE OBJECT is read READ-ONLY from the coordination
   registry (never hand-copied); validate_manifest must return
   structurally_valid=True before handoff.

Honest scope: a CPU structured-records replay of DECLARED requirements at
chosen detail (the carrier box is a translucent visual carrier, not the real
mesh; occlusion_mode 'mixed' is declared; the patch element is an axial
ligament of declared rest length carrying the document's derived attachment
stiffness).  This is not a native-engine runtime run.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sqlite3
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, "E:/PythonChimera/tools/monkey_campaign")

import mechanical_port_requirements as mpr  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402
from visual_capture import validate_manifest  # noqa: E402

TICKS = 360
DT = 1.0 / 300.0
SUBSTEPS = 16
G = 9.80665

SHEET = (2560, 840)
HEADER_H = 20
VIEW_W, VIEW_H = 848, 300
TOP_Y = HEADER_H
MID_Y = HEADER_H + VIEW_H
BOT_Y = MID_Y + VIEW_H
FOOTER_Y = SHEET[1] - 24
VIEWPORT_X = [8, 8 + VIEW_W, 8 + 2 * VIEW_W]

# declared replay constants (chosen detail; provenance recorded in the trace)
M_LOAD = 2.0e-3     # authored replay carried load (kg); the physiological
# carried-load segment weights stay BLOCKED in the document and are NOT used
C_PATCH = 0.05      # authored patch-element damping (N*s/m)
C_HOOK = 0.60       # authored hook damping (N*s/m)
L_ELEMENT = 0.05    # declared hook AND patch ligament rest length (m)
STRAND_PRETENSION_M = 3.0e-3
STAND_ANCHOR = (-0.05, -0.12, 0.0)
K_HOOK = None       # filled from pinned M05 K_TENSION_N_PER_M
K_PATCH = None      # filled from the document's C17 requirement check

PHASES = [
    (0, 47, "approach (carriage descends, strap tip gap -> 0)"),
    (48, 48, "attach (explicit bind: strap -> port; patch ligament engages)"),
    (49, 59, "load handover hook -> patch A"),
    (60, 60, "hook opens bitwise (patch A carries)"),
    (61, 150, "hold A (patch A carries; strap bound to port A)"),
    (151, 160, "transfer handover patch A -> hook (hook re-engages)"),
    (161, 161, "patch A bitwise 0; strap unbinds port A"),
    (162, 261, "transfer carriage path (supported by hook; strap unbound)"),
    (262, 262, "explicit bind: strap -> port B; patch B engages"),
    (263, 272, "transfer handover hook -> patch B"),
    (273, 273, "hook opens bitwise (patch B carries)"),
    (274, 295, "hold B (patch B carries; strap bound to port B)"),
    (296, 296, "release (all bond/patch forces bitwise 0; stored energy "
               "dissipated as a declared ledger term)"),
    (297, 359, "post-release: unsupported free flight"),
]

# declared carriage path vertices (tip = carriage + (0, -L_ELEMENT, 0))
P_START = (-0.002, 0.0625, -0.002)
P_AT_A = (-0.002, 0.0125, -0.002)     # tip at anchor A
P_ACROSS = (0.0419, 0.0125, 0.0224)   # lateral move high above the carrier
P_AT_B = (0.0419, -0.1710, 0.0224)    # tip at anchor B


def phase_of(tick):
    for lo, hi, name in PHASES:
        if lo <= tick <= hi:
            return name
    raise AssertionError(tick)


def smoothstep(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3.0 - 2.0 * u)


def path_point(tick):
    """Declared carriage path (piecewise linear, smoothstep-eased)."""
    def seg(a, b, lo, hi):
        u = smoothstep((tick - lo) / float(hi - lo))
        return [a[i] + (b[i] - a[i]) * u for i in range(3)]
    if tick < 162:
        return seg(P_START, P_AT_A, 0, 47)
    if tick < 194:
        return seg(P_AT_A, P_ACROSS, 162, 193)
    return seg(P_ACROSS, P_AT_B, 194, 261)


# ---------------------------------------------------------------------------
# small vector helpers
# ---------------------------------------------------------------------------
def vec_add(a, b, s=1.0):
    return [a[i] + s * b[i] for i in range(3)]


def vec_sub(a, b):
    return [a[i] - b[i] for i in range(3)]


def vec_scale(a, s):
    return [a[i] * s for i in range(3)]


def vec_dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def vec_norm(a):
    return math.sqrt(vec_dot(a, a))


def unit(a):
    n = vec_norm(a)
    return vec_scale(a, 1.0 / n) if n > 0.0 else [0.0, 0.0, 0.0]


def vec_cross(a, b):
    return [a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def tick_state_hash(rec):
    payload = {k: v for k, v in rec.items() if k != "state_hash"}
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# replay
# ---------------------------------------------------------------------------
def simulate(k_patch, k_hook, anchor_a, anchor_b):
    p = vec_add(P_START, [0.0, -(L_ELEMENT + M_LOAD * G / k_hook), 0.0])
    v = [0.0, 0.0, 0.0]
    e_ref = None
    e_diss = 0.0
    w_act = 0.0
    released_energy = 0.0
    patch_id = None       # None | 'A' | 'B'
    bond = None           # None | 'A' | 'B'
    hook_open = False
    w_patch = 0.0
    trace = []
    for tick in range(TICKS):
        phase = phase_of(tick)
        events = []
        if tick == 48:
            patch_id, bond, w_patch = "A", "A", 0.0
            events.append("explicit bind: strap -> port BIClong-P11; patch ligament "
                          "engages at rest length (proximity never bonds: the bind is explicit)")
        if tick == 49:
            events.append("handover blend hook -> patch A begins")
        if tick == 60 and not hook_open:
            hook_open = True
            events.append("hook opens bitwise; patch A carries")
        if tick == 151:
            if hook_open:
                hook_open = False
            events.append("hook re-engages; handover blend patch A -> hook begins")
        if tick == 161:
            patch_id = None
            bond = None
            w_patch = 0.0
            events.append("patch A forces bitwise 0; strap unbinds port A (tension 0)")
        if tick == 262:
            patch_id, bond, w_patch = "B", "B", 0.0
            events.append("explicit bind: strap -> port BRD-P3; patch ligament engages "
                          "at rest length")
        if tick == 263:
            events.append("handover blend hook -> patch B begins")
        if tick == 273 and not hook_open:
            hook_open = True
            events.append("hook opens bitwise; patch B carries")
        if tick == 296:
            released_energy = e_elastic_prev
            e_diss += e_elastic_prev
            patch_id = None
            bond = None
            w_patch = 0.0
            events.append("RELEASE: all bond/patch forces bitwise 0; stored elastic "
                          f"{released_energy:.6e} J dissipated (declared ledger term)")
        if 48 <= tick < 60 and patch_id == "A":
            w_patch = smoothstep((tick - 47) / 11.0)
        elif 60 <= tick < 151 and patch_id == "A":
            w_patch = 1.0
        elif 151 <= tick < 161 and patch_id == "A":
            w_patch = 1.0 - smoothstep((tick - 150) / 10.0)
        elif 263 <= tick < 273 and patch_id == "B":
            w_patch = smoothstep((tick - 262) / 10.0)
        elif tick >= 273 and patch_id == "B":
            w_patch = 1.0

        carriage = path_point(tick)
        tip = vec_add(carriage, [0.0, -L_ELEMENT, 0.0])
        tip_prev = vec_add(path_point(tick - 1), [0.0, -L_ELEMENT, 0.0]) if tick else tip
        tip_v = vec_scale(vec_sub(tip, tip_prev), 1.0 / DT)

        f_patch_tick = [0.0, 0.0, 0.0]
        f_hook_tick = [0.0, 0.0, 0.0]
        e_patch_store = 0.0
        for _ in range(SUBSTEPS):
            h = DT / SUBSTEPS
            f = [0.0, -M_LOAD * G, 0.0]
            f_patch = [0.0, 0.0, 0.0]
            f_hook = [0.0, 0.0, 0.0]
            e_patch_store = 0.0
            if patch_id is not None and w_patch > 0.0:
                a = anchor_a if patch_id == "A" else anchor_b
                d = vec_sub(p, a)
                dist = vec_norm(d)
                stretch = dist - L_ELEMENT
                if dist > 0.0 and stretch > 0.0:
                    mag = k_patch * stretch
                    f_patch = vec_scale(unit(d), -mag * w_patch)
                    vrel = vec_dot(v, unit(d))
                    f_patch = vec_add(f_patch, vec_scale(unit(d), -C_PATCH * vrel * w_patch))
                    e_patch_store = 0.5 * k_patch * stretch * stretch * w_patch
                f = vec_add(f, f_patch)
            if not hook_open:
                hook_share = (1.0 - w_patch) if patch_id is not None else 1.0
                d = vec_sub(p, tip)
                dist = vec_norm(d)
                stretch = dist - L_ELEMENT
                if dist > 0.0 and stretch > 0.0:
                    mag = k_hook * stretch
                    f_hook = vec_scale(unit(d), -mag * hook_share)
                    vrel = vec_dot(vec_sub(v, tip_v), unit(d))
                    f_hook = vec_add(f_hook, vec_scale(unit(d), -C_HOOK * vrel * hook_share))
                f = vec_add(f, f_hook)
            v = vec_add(v, vec_scale(f, h / M_LOAD))
            p = vec_add(p, vec_scale(v, h))
            # dissipation only from ACTIVE force elements (never phantom)
            if not hook_open:
                e_diss += C_HOOK * vec_dot(vec_sub(v, tip_v), vec_sub(v, tip_v)) \
                    * h * hook_share
            if patch_id is not None and w_patch > 0.0:
                e_diss += C_PATCH * vec_dot(v, v) * h * w_patch
            w_act += vec_dot(f_hook, tip_v) * h
            f_patch_tick = f_patch
            f_hook_tick = f_hook
        e_kin = 0.5 * M_LOAD * vec_dot(v, v)
        e_pot = M_LOAD * G * p[1]
        hook_stretch = max(0.0, vec_norm(vec_sub(p, tip)) - L_ELEMENT)
        e_elastic = e_patch_store + (0.0 if hook_open else
                                     0.5 * k_hook * hook_stretch ** 2)
        e_elastic_prev = e_elastic
        e_mech = e_kin + e_pot + e_elastic
        if e_ref is None:
            e_ref = e_mech
        residual = (e_mech - e_ref) + e_diss - w_act

        gap = vec_norm(vec_sub(anchor_a, tip)) if tick < 48 else 0.0
        strap_tension = 0.0
        if bond == "A":
            d = vec_sub(anchor_a, STAND_ANCHOR)
            strap_tension = 60.0 * max(0.0, vec_norm(d) - (vec_norm(d) - STRAND_PRETENSION_M))
        elif bond == "B":
            d = vec_sub(anchor_b, STAND_ANCHOR)
            strap_tension = 60.0 * max(0.0, vec_norm(d) - (vec_norm(d) - STRAND_PRETENSION_M))
        support_paths = []
        if not hook_open:
            support_paths.append("hook+carriage")
        if patch_id is not None:
            support_paths.append(f"patch {patch_id}")
        if bond is not None:
            support_paths.append(f"strap->{bond}")
        rec = {
            "tick": tick,
            "t_s": tick * DT,
            "phase": phase,
            "events": events,
            "load_pos_m": [float(x) for x in p],
            "load_vel_m_per_s": [float(x) for x in v],
            "carriage_pos_m": [float(x) for x in carriage],
            "strap_tip_m": [float(x) for x in tip],
            "approach_gap_m": float(gap),
            "bond": bond,
            "hook_open": bool(hook_open),
            "patch_active": patch_id,
            "patch_force_n": [float(x) for x in f_patch_tick],
            "patch_force_mag_n": float(vec_norm(f_patch_tick)),
            "hook_force_n": [float(x) for x in f_hook_tick],
            "strap_tension_n": float(strap_tension),
            "support_state": "supported" if support_paths else "unsupported",
            "support_paths": support_paths,
            "energy": {
                "kinetic_j": float(e_kin),
                "potential_j": float(e_pot),
                "elastic_j": float(e_elastic),
                "dissipated_j": float(e_diss),
                "actuator_work_j": float(w_act),
                "release_dissipation_j": float(released_energy if tick >= 296 else 0.0),
                "ledger_residual_j": float(residual),
            },
        }
        rec["state_hash"] = tick_state_hash(rec)
        trace.append(rec)
    return trace


# ---------------------------------------------------------------------------
# cameras / projection
# ---------------------------------------------------------------------------
def look_at(pos, target):
    fwd = unit(vec_sub(target, pos))
    right = unit(vec_cross(fwd, [0.0, 1.0, 0.0]))
    if vec_norm(right) < 1e-9:
        right = [1.0, 0.0, 0.0]
    up = vec_cross(right, fwd)
    return right, up, fwd


def quat_wxyz_from_basis(right, up, fwd):
    m00, m01, m02 = right[0], up[0], -fwd[0]
    m10, m11, m12 = right[1], up[1], -fwd[1]
    m20, m21, m22 = right[2], up[2], -fwd[2]
    tr = m00 + m11 + m22
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2
        w, x, y, z = 0.25 * s, (m21 - m12) / s, (m02 - m20) / s, (m10 - m01) / s
    elif m00 > m11 and m00 > m22:
        s = math.sqrt(1.0 + m00 - m11 - m22) * 2
        w, x, y, z = (m21 - m12) / s, 0.25 * s, (m01 + m10) / s, (m02 + m20) / s
    elif m11 > m22:
        s = math.sqrt(1.0 + m11 - m00 - m22) * 2
        w, x, y, z = (m02 - m20) / s, (m01 + m10) / s, 0.25 * s, (m12 + m21) / s
    else:
        s = math.sqrt(1.0 + m22 - m00 - m11) * 2
        w, x, y, z = (m10 - m01) / s, (m02 + m20) / s, (m12 + m21) / s, 0.25 * s
    q = [w, x, y, z]
    n = math.sqrt(sum(c * c for c in q))
    return [c / n for c in q]


def make_camera(viewport, pos, target, *, vfov=None, span=None, frame_id,
                near_far=(0.001, 20.0)):
    right, up, fwd = look_at(pos, target)
    cam = {
        "frame_id": frame_id,
        "coordinate_unit": "m",
        "handedness": "right",
        "orientation_convention": "quaternion_wxyz_camera_to_frame",
        "forward_axis": "-Z",
        "up_axis": "+Y",
        "near_far_planes": [float(near_far[0]), float(near_far[1])],
        "aspect_ratio": viewport[0] / viewport[1],
        "viewport_resolution": [int(viewport[0]), int(viewport[1])],
        "projection": "perspective" if vfov is not None else "orthographic",
        "sample_mode": "fixed_bookmark",
        "camera_motion_or_bookmark_sequence": (
            "fixed_bookmark: identical pose at both sampled ticks (and every rendered "
            "frame); the SUBJECT moves (strap tip, carriage, load, force arrows), "
            "never the camera"),
        "samples": [
            {"tick": 0, "position": [float(x) for x in pos],
             "target": [float(x) for x in target],
             "distance_to_target": float(vec_norm(vec_sub(target, pos))),
             "orientation": quat_wxyz_from_basis(right, up, fwd)},
            {"tick": TICKS - 1, "position": [float(x) for x in pos],
             "target": [float(x) for x in target],
             "distance_to_target": float(vec_norm(vec_sub(target, pos))),
             "orientation": quat_wxyz_from_basis(right, up, fwd)},
        ],
    }
    if vfov is not None:
        cam["vertical_fov_degrees"] = float(vfov)
    else:
        cam["orthographic_span"] = float(span)
    return cam


def projector(cam):
    w, h = cam["viewport_resolution"]
    s0 = cam["samples"][0]
    pos = s0["position"]
    right, up, fwd = look_at(pos, s0["target"])

    def proj(pt):
        d = vec_sub(pt, pos)
        x, y, z = vec_dot(d, right), vec_dot(d, up), vec_dot(d, fwd)
        if z <= 1e-9:
            return [0.0, 0.0, -1.0]
        if cam["projection"] == "perspective":
            f = (h / 2.0) / math.tan(math.radians(cam["vertical_fov_degrees"]) / 2.0)
            return [w / 2.0 + (x / z) * f, h / 2.0 - (y / z) * f, z]
        scale = h / cam["orthographic_span"]
        return [w / 2.0 + x * scale, h / 2.0 - y * scale, z]
    return proj


# ---------------------------------------------------------------------------
# scene rendering (structured records; declared mixed occlusion)
# ---------------------------------------------------------------------------
COL_STAND = (125, 125, 132)
COL_RAIL = (92, 96, 104)
COL_CARRIER = (70, 110, 170)
COL_CARRIER_EDGE = (110, 150, 205)
COL_PATCH_A = (232, 202, 44)
COL_PATCH_B = (44, 205, 215)
COL_STRAP = (175, 62, 62)
COL_HOOK = (224, 142, 42)
COL_LOAD = (212, 52, 52)
COL_ARROW = (64, 202, 94)
COL_TEXT = (240, 240, 240)

CARRIER_BOX = ((-0.015, -0.245, -0.015), (0.025, 0.005, 0.015))
STAND_BASE = ((-0.09, -0.31, -0.05), (0.01, -0.292, 0.05))
STAND_POST = ((-0.056, -0.30, -0.006), (-0.044, -0.05, 0.006))
STRUT = ((-0.05, -0.06, 0.0), (-0.01, -0.20, 0.0))
RAIL_POLYLINE = [P_START, P_AT_A, P_ACROSS, P_AT_B]
RIM_OFFSETS = None  # set in main from the document's declared anchors


def box_edges(b):
    (x0, y0, z0), (x1, y1, z1) = b
    c = [[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    pairs = []
    for i in range(len(c)):
        for j in range(i + 1, len(c)):
            if sum(1 for k in range(3) if abs(c[i][k] - c[j][k]) > 1e-12) == 1:
                pairs.append((c[i], c[j]))
    return pairs


def disc_ring(center, normal, radius, segments=28):
    n = unit(normal)
    helper = [0.0, 0.0, 1.0]
    if abs(vec_dot(n, helper)) > 0.9:
        helper = [0.0, 1.0, 0.0]
    u = unit(vec_cross(n, helper))
    v = vec_cross(n, u)
    return [vec_add(center, vec_add(vec_scale(u, radius * math.cos(2 * math.pi * i / segments)),
                                    vec_scale(v, radius * math.sin(2 * math.pi * i / segments))))
            for i in range(segments)]


def render_viewport(tile, cam, rec, mode, doc_info):
    draw = ImageDraw.Draw(tile)
    proj = projector(cam)
    solid = []

    def sline(a, b, color, width=2):
        pa, pb = proj(a), proj(b)
        if pa[2] <= 0 or pb[2] <= 0:
            return
        solid.append(((pa[2] + pb[2]) / 2.0,
                      lambda pa=pa, pb=pb, color=color, width=width:
                      draw.line([pa[0], pa[1], pb[0], pb[1]], fill=color, width=width)))

    for a, b in box_edges(STAND_BASE) + box_edges(STAND_POST):
        sline(a, b, COL_STAND, 2)
    sline(list(STRUT[0]), list(STRUT[1]), COL_STAND, 3)
    for i in range(len(RAIL_POLYLINE) - 1):
        sline(list(RAIL_POLYLINE[i]), list(RAIL_POLYLINE[i + 1]), COL_RAIL, 3)
    anchor_a, anchor_b = doc_info["anchor_a"], doc_info["anchor_b"]
    r_p = doc_info["patch_radius"]
    normal = doc_info["patch_normal"]

    # carrier: translucent faces (composited), solid edges
    (x0, y0, z0), (x1, y1, z1) = CARRIER_BOX
    faces = [
        [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)],
        [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
        [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
        [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)],
        [(x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)],
        [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)],
    ]
    for a, b in box_edges(CARRIER_BOX):
        sline(a, b, COL_CARRIER_EDGE, 2)

    # declared patches (geometry in both modes; labels/arrows diagnostic only)
    ring_a = disc_ring(anchor_a, normal, r_p)
    ring_b = disc_ring(anchor_b, normal, r_p)
    for ring, col in ((ring_a, COL_PATCH_A), (ring_b, COL_PATCH_B)):
        pix = [proj(p) for p in ring]
        if all(p[2] > 0 for p in pix):
            depth = sum(p[2] for p in pix) / len(pix)

            def fn(pix=pix, col=col, mode=mode):
                pts = [(p[0], p[1]) for p in pix]
                if mode == "diagnostic":
                    draw.polygon(pts, fill=col + (90,))
                draw.line(pts + [pts[0]], fill=col, width=3)
            solid.append((depth, fn))
    for anchor, col in ((anchor_a, COL_PATCH_A), (anchor_b, COL_PATCH_B)):
        for off in RIM_OFFSETS:
            sline(anchor, vec_add(anchor, off), col, 1)

    # frame axes gizmo (diagnostic layer: joint/frame axes)
    if mode == "diagnostic":
        o = [0.005, -0.24, 0.0]
        for vec, col in (((0.022, 0, 0), (222, 72, 72)),
                         ((0, 0.022, 0), (72, 202, 72)),
                         ((0, 0, 0.022), (90, 118, 235))):

            def arrow(o=o, vec=vec, col=col):
                pa, pb = proj(o), proj(vec_add(o, vec))
                if pa[2] > 0 and pb[2] > 0:
                    draw.line([pa[0], pa[1], pb[0], pb[1]], fill=col, width=2)
            solid.append((proj(o)[2], arrow))

    # strap, hook, carriage
    tip = rec["strap_tip_m"]
    if rec["bond"] is not None or rec["tick"] < 48:
        sline(list(STAND_ANCHOR), list(tip), COL_STRAP, 3)
    carriage = rec["carriage_pos_m"]
    if not rec["hook_open"]:
        sline(carriage, vec_add(carriage, [0.0, -L_ELEMENT, 0.0]), COL_HOOK, 2)
        sline(vec_add(carriage, [0.0, -L_ELEMENT, 0.0]), list(rec["load_pos_m"]),
              COL_HOOK, 2)
    # carriage block
    cb = [[carriage[0] - 0.004, carriage[1] + 0.006, carriage[2] - 0.004],
          [carriage[0] + 0.004, carriage[1] - 0.004, carriage[2] + 0.004]]
    for a, b in box_edges((cb[0], cb[1])):
        sline(a, b, COL_RAIL, 2)

    solid.sort(key=lambda t: -t[0])
    for _, fn in solid:
        fn()

    # translucent carrier faces composited AFTER solids (declared order:
    # occlusion_mode 'mixed' — the carrier is a translucent visual carrier)
    overlay = Image.new("RGBA", tile.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    for f in faces:
        pix = [proj(list(p)) for p in f]
        if all(p[2] > 0 for p in pix):
            odraw.polygon([(p[0], p[1]) for p in pix], fill=COL_CARRIER + (30,))
    tile.alpha_composite(overlay)
    draw = ImageDraw.Draw(tile)

    # load marker (always visible — declared overlay on the translucent carrier)
    lp = proj(rec["load_pos_m"])
    if lp[2] > 0:
        draw.ellipse([lp[0] - 5, lp[1] - 5, lp[0] + 5, lp[1] + 5], fill=COL_LOAD)

    if mode == "diagnostic":
        if rec["patch_force_mag_n"] > 1e-9:
            at = anchor_a if rec["patch_active"] == "A" else anchor_b
            col = COL_PATCH_A if rec["patch_active"] == "A" else COL_PATCH_B
            d = vec_scale(unit(rec["patch_force_n"]) if vec_norm(rec["patch_force_n"]) > 0
                          else [0, 0, 0], 0.035)
            pa, pb = proj(at), proj(vec_add(at, d))
            if pa[2] > 0 and pb[2] > 0:
                draw.line([pa[0], pa[1], pb[0], pb[1]], fill=col, width=3)
                draw.text((pb[0] + 3, pb[1] - 12),
                          f"Fpatch={rec['patch_force_mag_n']:.4f} N", fill=col)
        # weight arrow
        pa, pb = proj(rec["load_pos_m"]), proj(vec_add(rec["load_pos_m"], [0, -0.03, 0]))
        if pa[2] > 0 and pb[2] > 0:
            draw.line([pa[0], pa[1], pb[0], pb[1]], fill=(205, 90, 90), width=2)
            draw.text((pb[0] + 3, pb[1]), f"mg={M_LOAD * G:.4f} N", fill=(205, 90, 90))
        if rec["strap_tension_n"] > 1e-9:
            mid = proj(vec_scale(vec_add(STAND_ANCHOR, tip), 0.5))
            if mid[2] > 0:
                draw.text((mid[0] + 4, mid[1] - 12),
                          f"T={rec['strap_tension_n']:.3f} N", fill=COL_STRAP)
        if rec["tick"] < 18:
            pa, pb = proj(anchor_a), proj(tip)
            if pa[2] > 0 and pb[2] > 0:
                mid = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
                draw.text((mid[0] + 4, mid[1]),
                          f"gap={rec['approach_gap_m'] * 1e3:.1f} mm", fill=COL_HOOK)
        labels = [(anchor_a, "port:BIClong-P11", COL_PATCH_A),
                  (anchor_b, "port:BRD-P3", COL_PATCH_B),
                  (list(STAND_ANCHOR), "support:stand", COL_STAND),
                  (list(rec["load_pos_m"]), f"load m={M_LOAD:.1e} kg", COL_LOAD),
                  (P_ACROSS, "transfer:rail(path)", COL_RAIL)]
        for pt3, text, col in labels:
            pt = proj(pt3)
            if pt[2] > 0:
                draw.text((pt[0] + 5, pt[1] + 5), text, fill=col)
        draw.text((8, 6), f"support: {rec['support_state']}  paths={rec['support_paths']}",
                  fill=COL_TEXT)
        en = rec["energy"]
        draw.text((8, 20), f"E k={en['kinetic_j']:.2e} p={en['potential_j']:.3f} "
                           f"el={en['elastic_j']:.2e} diss={en['dissipated_j']:.4e} "
                           f"res={en['ledger_residual_j']:.1e} J", fill=COL_TEXT)


def draw_traces(draw, rec, traces):
    x0, y0 = 8, BOT_Y + 16
    w, h = SHEET[0] - 16, FOOTER_Y - BOT_Y - 22
    draw.text((x0, BOT_Y + 2),
              "telemetry: patch |F| A (yellow) / B (cyan) · strap tension (red) · "
              "approach gap mm (orange) · support band (green) · release line (magenta)",
              fill=COL_TEXT)

    def tx(t):
        return x0 + (t / (TICKS - 1)) * w

    def ty(f, fmax):
        return y0 + h - max(0.0, min(1.0, f / fmax)) * h

    draw.rectangle([tx(296), y0, tx(297), y0 + h], fill=(120, 40, 120))
    for series, col, fmax in (("patchA", COL_PATCH_A, 0.06), ("patchB", COL_PATCH_B, 0.06),
                              ("strap", COL_STRAP, 0.30), ("gap_mm", COL_HOOK, 80.0)):
        pts = [(tx(t), ty(traces[series][t], fmax)) for t in range(TICKS)]
        draw.line(pts, fill=col, width=2)
    for t in range(TICKS):
        if traces["supported"][t]:
            draw.rectangle([tx(t) - 1, y0 + h - 3, tx(t) + 1, y0 + h], fill=(60, 200, 90))
    draw.line([tx(0), y0 + h, tx(TICKS - 1), y0 + h], fill=(90, 96, 104), width=1)
    draw.text((x0, y0 + h - 12),
              f"tick 0..{TICKS - 1} (1 tick = 1/300 s simulated; frame t = tick t)",
              fill=(150, 158, 168))


def render_sheet(rec, cams, doc_info, footer, header, traces):
    img = Image.new("RGBA", SHEET, (16, 18, 22, 255))
    draw = ImageDraw.Draw(img)
    draw.text((8, 4), header, fill=COL_TEXT)
    for i, (vid, cam) in enumerate(cams["diag"].items()):
        tile = Image.new("RGBA", (VIEW_W, VIEW_H), (24, 26, 32, 255))
        render_viewport(tile, cam, rec, "diagnostic", doc_info)
        td = ImageDraw.Draw(tile)
        td.text((6, VIEW_H - 14), f"{vid} | diagnostic | tick {rec['tick']} | {rec['phase']}",
                fill=(185, 192, 202, 255))
        img.paste(tile, (VIEWPORT_X[i], TOP_Y))
    for i, (vid, cam) in enumerate(cams["clean"].items()):
        tile = Image.new("RGBA", (VIEW_W, VIEW_H), (24, 26, 32, 255))
        render_viewport(tile, cam, rec, "clean", doc_info)
        td = ImageDraw.Draw(tile)
        td.text((6, VIEW_H - 14), f"{vid} | clean | tick {rec['tick']}",
                fill=(150, 158, 168, 255))
        img.paste(tile, (VIEWPORT_X[i], MID_Y))
    draw_traces(draw, rec, traces)
    draw.text((8, FOOTER_Y + 6), footer, fill=(172, 180, 190, 255))
    return img.convert("RGB")


# ---------------------------------------------------------------------------
# manifest
# ---------------------------------------------------------------------------
def registry_profile(sqlite_path):
    con = sqlite3.connect("file:" + pathlib.Path(sqlite_path).absolute().as_posix()
                          + "?mode=ro", uri=True)
    try:
        payload = json.loads(con.execute(
            "SELECT payload FROM state WHERE id=1").fetchone()[0])
    finally:
        con.close()
    card = payload["kanban"]["cards"]["MAT2-B05"]
    prof = card["spec"]["ontology_qualification"]["task"]["verification_profile"]
    assert prof["id"] == "grasp" and prof["kind"] == "motion", (prof["id"], prof["kind"])
    return prof, card.get("criteria_sha256")


def sha256_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def main():
    capture_dir = pathlib.Path(sys.argv[1])
    ffmpeg = sys.argv[2]
    registry = sys.argv[3]
    profile, registry_criteria = registry_profile(registry)

    doc_path = HERE / "mechanical_port_requirements.json"
    if not doc_path.exists():
        mpr.write_outputs(mpr.derive())
    doc = mpr.load_json(doc_path)
    consts = mpr.parse_m05_constants()
    k_hook = consts["k_tension_n_per_m"]
    anchor_a = anchor_b = None
    gate = None
    for p in doc["ports"]:
        if p["port_id"] == "BIClong-P11":
            anchor_a = [float(v) for v in p["source_pos_local_m"]]
            gate = p["inputs"]["c17_requirement_check"]
        if p["port_id"] == "BRD-P3":
            anchor_b = [float(v) for v in p["source_pos_local_m"]]
    k_patch = gate["k_n_per_m"]
    global RIM_OFFSETS
    RIM_OFFSETS = [vec_sub(x, anchor_a) for x in gate["anchors_source_local_m"]]
    doc_info = {"anchor_a": anchor_a, "anchor_b": anchor_b,
                "patch_radius": 2.5e-3, "patch_normal": [1.0, 0.0, 0.0]}

    trace = simulate(k_patch, k_hook, anchor_a, anchor_b)
    traces = {
        "patchA": [t["patch_force_mag_n"] if t["patch_active"] == "A" else 0.0 for t in trace],
        "patchB": [t["patch_force_mag_n"] if t["patch_active"] == "B" else 0.0 for t in trace],
        "strap": [t["strap_tension_n"] for t in trace],
        "gap_mm": [t["approach_gap_m"] * 1e3 for t in trace],
        "supported": [t["support_state"] == "supported" for t in trace],
    }
    trace_path = HERE / "replay_trace.json"
    mpr.write_text_canonical(trace_path, mpr.canonical_json({
        "schema": "chimera.b05_replay_trace.v1",
        "declared_inputs": {
            "k_patch_n_per_m": k_patch,
            "kappa_areal_n_m3": gate["kappa_areal_n_m3"],
            "patch_area_m2": gate["patch_area_m2"],
            "patch_element_rest_length_m": L_ELEMENT,
            "patch_element_note": ("the document's disc patch is the attachment region; the "
                                   "replay couples the load through an axial ligament carrying "
                                   "the document's derived attachment stiffness k = "
                                   "kappa_areal * A_patch (chosen-detail demo declaration)"),
            "k_hook_n_per_m": k_hook,
            "k_hook_source": "pinned M05 K_TENSION_N_PER_M (data/interface_exchange_m05.py)",
            "m_load_kg": M_LOAD,
            "m_load_note": ("authored chosen-detail replay load; the physiological carried-load "
                            "segment weights remain BLOCKED in the requirements document and "
                            "are NOT used"),
            "c_patch_n_s_per_m": C_PATCH, "c_hook_n_s_per_m": C_HOOK,
            "g_m_per_s2": G, "dt_s": DT, "substeps": SUBSTEPS,
            "schedule": [[lo, hi, name] for lo, hi, name in PHASES],
        },
        "ticks": trace,
    }))

    cams_diag = {
        profile["views"][0]: make_camera((VIEW_W, VIEW_H),
                                         (0.34, 0.10, 0.50), (-0.005, -0.14, 0.0),
                                         vfov=42.0, frame_id="b05_whole_view_m"),
        profile["views"][1]: make_camera((VIEW_W, VIEW_H),
                                         (0.070, -0.030, 0.062), anchor_a,
                                         vfov=35.0, frame_id="b05_closeup_port_a_m"),
        profile["views"][2]: make_camera((VIEW_W, VIEW_H),
                                         (0.60, -0.135, 0.004), (-0.02, -0.135, 0.004),
                                         span=0.24, frame_id="b05_ortho_interfaces_m"),
    }
    cams_clean = {vid: json.loads(json.dumps(cam)) for vid, cam in cams_diag.items()}

    frames_dir = capture_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    doc_sha = sha256_file(doc_path)
    frame_files = {}
    for rec in trace:
        header = (f"MAT2-B05 {rec['phase']} | tick {rec['tick']} ({rec['t_s']:.5f} s sim) | "
                  f"bond={rec['bond']} patch={rec['patch_active']} | doc sha256 {doc_sha[:12]}")
        footer = (f"MAT2-B05 capture | tick {rec['tick']} = {rec['t_s']:.5f} s simulated "
                  f"(1 tick = 1/300 s; replayed at 1 video second per tick, slow motion x300) | "
                  f"state {rec['state_hash'][:16]} | requirements doc sha256 {doc_sha[:16]}")
        img = render_sheet(rec, {"diag": cams_diag, "clean": cams_clean}, doc_info,
                           footer, header, traces)
        fp = frames_dir / f"frame_{rec['tick']:03d}.png"
        img.save(fp, compress_level=6)
        frame_files[fp.name] = sha256_file(fp)
    trace_sha = sha256_file(trace_path)

    video_path = capture_dir / "capture" / "capture_mat2_b05_ports_20260928.mkv"
    video_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-framerate", "1",
                    "-i", str(frames_dir / "frame_%03d.png"),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                    "-pix_fmt", "yuv420p", str(video_path)], check=True)
    video_sha = sha256_file(video_path)
    run_id = "mat2-b05-portrequirements-visual-20260928-" + video_sha[:8]

    subjects = ["port:BIClong-P11", "port:BRD-P3", "load", "strap", "stand", "carrier",
                "transfer:rail"]

    def vis_diag():
        return {"layers": list(profile["diagnostic_layers"]),
                "label_ids": list(subjects),
                "selected_ids": list(subjects),
                "required_subject_ids": list(subjects),
                "observed_subject_ids": list(subjects),
                "missing_subject_ids": [],
                "occlusion_mode": "mixed",
                "tag_bindings": [{"label_id": s, "subject_id": s} for s in subjects]}

    def vis_clean():
        return {"layers": [], "label_ids": [], "selected_ids": [],
                "required_subject_ids": list(subjects),
                "observed_subject_ids": list(subjects),
                "missing_subject_ids": [],
                "occlusion_mode": "depth_tested",
                "tag_bindings": []}

    binding = {"kind": "trace", "sha256": trace_sha,
               "note": ("sha256 of contributions/MAT2-B05/replay_trace.json: per-tick replay "
                        "telemetry (phase, approach gap, bond/patch/strap/hook forces, support "
                        "state, energy ledger, per-tick state hash); rendered positions replay "
                        "this trace")}

    notes = {
        profile["views"][0]: ("single viewport (top row, column 1): whole scene — stand, "
                              "translucent carrier, rail path, strap, carriage, load; the "
                              "approach/attach/load/hold/transfer/release sequence is visible "
                              "in full"),
        profile["views"][1]: ("single viewport (top row, column 2): close-up of the declared "
                              "BIClong-P11 patch (disc at its pinned source-local position, 3 "
                              "rim anchors) with the attachment force arrow while loaded"),
        profile["views"][2]: ("single viewport (top row, column 3): orthographic face-on view "
                              "along the declared patch normals showing EACH loaded interface "
                              "(BIClong-P11 and BRD-P3 discs face-on simultaneously)"),
    }
    views = []
    for i, vid in enumerate(profile["views"]):
        views.append({"artifact_locator": {"kind": "video", "seconds": [0, TICKS]},
                      "camera": cams_diag[vid],
                      "cell_layout_note": notes[vid],
                      "mode": "diagnostic",
                      "pair_id": f"pair-{i}",
                      "state_binding": binding,
                      "view_id": vid,
                      "visibility": vis_diag()})
        views.append({"artifact_locator": {"kind": "video", "seconds": [0, TICKS]},
                      "camera": cams_clean[vid],
                      "cell_layout_note": ("clean row: identical camera and state to its "
                                           "diagnostic pair; no labels, layers or diagnostic "
                                           "overlays by design"),
                      "mode": "clean",
                      "pair_id": f"pair-{i}",
                      "state_binding": binding,
                      "view_id": vid,
                      "visibility": vis_clean()})

    manifest = {
        "schema": "chimera.visual_capture_manifest.v1",
        "task_id": "B05",
        "profile_id": "grasp",
        "run_id": run_id,
        "tick_interval": [0, TICKS - 1],
        "subject_sha256": doc_sha,
        "capture_sha256": video_sha,
        "sheet_layout": {
            "pixel_size": list(SHEET),
            "honest_titles": ("rendered inside every viewport: view_id, mode, tick and phase; "
                              "every diagnostic viewport carries the five declared diagnostic "
                              "layers (attachment patches and endpoint IDs, tendon/strap path, "
                              "joint/frame axes gizmo, contact/force arrows, support-state "
                              "line) plus the energy ledger line; the footer carries the "
                              "tick-to-seconds map and the per-tick state hash; the carrier "
                              "box is a TRANSLUCENT visual carrier (declared occlusion_mode "
                              "'mixed'), not the real mesh"),
            "rows": ["top    diagnostic viewports [whole | close-up | orthogonal face-on of "
                     "each loaded interface] with all five declared diagnostic layers",
                     "middle clean viewports (identical cameras, no labels, no overlays)",
                     "bottom telemetry traces (patch |F| A/B, strap tension, approach gap, "
                     "support band, release line) + footer"],
            "tick_to_seconds_map": ("1 tick = 1/300 s simulated, replayed at 1 video second "
                                    "per tick (slow motion x300); frame t = tick t"),
            "frame_files": frame_files,
        },
        "views": views,
    }
    context = {"task_id": "B05", "run_id": run_id,
               "subject_sha256": doc_sha, "capture_sha256": video_sha,
               "tick_interval": [0, TICKS - 1]}
    receipt = validate_manifest(manifest, context, profile)
    receipt["video_path"] = str(video_path)
    receipt["video_sha256"] = video_sha
    receipt["subject_path"] = ("tools/monkey_campaign/contributions/MAT2-B05/"
                               "mechanical_port_requirements.json")
    receipt["subject_sha256"] = doc_sha
    receipt["trace_path"] = "tools/monkey_campaign/contributions/MAT2-B05/replay_trace.json"
    receipt["trace_sha256"] = trace_sha
    receipt["frame_count"] = len(frame_files)
    receipt["profile_source"] = {
        "registry": str(registry),
        "read_mode": "sqlite3 mode=ro (read-only)",
        "card_path": ("kanban.cards.MAT2-B05.spec.ontology_qualification.task."
                      "verification_profile"),
        "profile_id": profile["id"], "kind": profile["kind"],
        "registry_criteria_sha256": registry_criteria}
    receipt["validator"] = "tools/monkey_campaign/visual_capture.py validate_manifest"
    receipt["limits"] = ("Structural camera-metadata validation only; independent image/physics "
                         "review remains mandatory. CPU structured-records replay of DECLARED "
                         "requirements at chosen detail; not a native-engine runtime run; "
                         "post-release free flight shows no floor contact (out of B05 scope).")
    mpr.write_text_canonical(HERE / "capture_manifest.json", mpr.canonical_json(manifest))
    mpr.write_text_canonical(HERE / "capture_context.json", mpr.canonical_json(context))
    mpr.write_text_canonical(HERE / "capture_validation_receipt.json",
                             mpr.canonical_json(receipt))
    worst = max(abs(t["energy"]["ledger_residual_j"]) for t in trace)
    print("video:", video_path)
    print("video sha256:", video_sha)
    print("trace sha256:", trace_sha)
    print("subject (requirements doc) sha256:", doc_sha)
    print("validate_manifest:", receipt["mode"], "| structurally_valid:",
          receipt["structurally_valid"], "| views:", receipt["view_count"],
          "| profile:", receipt["profile_id"], "| profile_source: registry read-only")
    print(f"worst ledger residual: {worst:.3e} J")
    return 0


if __name__ == "__main__":
    sys.exit(main())
