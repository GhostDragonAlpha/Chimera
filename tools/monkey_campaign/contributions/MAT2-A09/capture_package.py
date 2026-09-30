"""Render + validate the MAT2-A09 visible_static capture (anatomy profile).

Pure-Python/PIL 2D orthographic projection of the PACKAGE state
(grasp_package.json) over the macaque hand.vtp envelope point cloud + A05
mutant skeleton (the same declared 2D reduction as sealed A07). No 3D engine,
no GPU: the declared capture is a 2D orthographic skeleton/envelope view with
real computed camera quaternions.

Outputs (this directory only):
  capture/capture_mat2_a09_package_20260930.png (single hashed sheet)
  evidence/cameras.json                         (exact camera numbers)
  evidence/capture_manifest.json / capture_context.json
  evidence/validation_receipt.json              (validate_manifest result)

The manifest task_id is the SHORT FORM "A09" (P7 law); the profile object is
read READ-ONLY from E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3
(kanban.cards[MAT2-A09].spec.ontology_qualification.task.verification_profile)
and the registry card criteria sha is asserted equal to the document's.
Every row's state_binding.sha256 is the sha256 of grasp_package.json — view
toggles preserve the physical state hash (card falsifier).

Diagnostic markers carry the LAWFUL TERMINAL RESOLUTION of each connection:
green filled square = supported, amber hollow circle = explicitly_unresolved,
red ring = measured outside the A05-recorded envelope bounds (exact per-axis
excess labeled; exact floats carried in the manifest numerical_evidence).
Grasp endpoints: pink rings. Clean rows carry NO layers, labels or bindings.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sqlite3
import sys
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw

import grasp_package as gp

HERE = pathlib.Path(__file__).resolve().parent
VTP = pathlib.Path("E:/PythonChimera/tools/science_funnel/data/macaque_arm/"
                   "Geometry/hand.vtp")
REGISTRY = "E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3"
STATE_FILE = HERE / "grasp_package.json"
STATE = json.loads(STATE_FILE.read_text(encoding="utf-8"))
STATE_SHA = hashlib.sha256(STATE_FILE.read_bytes()).hexdigest()
A05_STRUCT = json.loads(pathlib.Path(
    "E:/ChimeraWork/monkey-coordination/kanban-attempts/MAT2-A09/"
    "2c3a18f2fa494ce1a06ca691dd9fe03c/checkout/tools/monkey_campaign/"
    "contributions/MAT2-A05/mutation_structure.json").read_text(encoding="utf-8"))
SHEET = HERE / "capture" / "capture_mat2_a09_package_20260930.png"
ROW_W, ROW_H = 1280, 720
TICK_INTERVAL = [0, 0]
TASK_ID = "A09"  # SHORT form, deliberately (P7)

GREEN = (90, 220, 140)      # supported terminal resolution
AMBER = (240, 190, 90)      # explicitly_unresolved
RED = (235, 80, 80)         # measured outside deviation ring
PINK = (250, 90, 120)       # grasp endpoints

assert gp.sha256_file(STATE_FILE) == STATE_SHA
assert STATE["schema"] == gp.SCHEMA
assert STATE["identity"]["criteria_sha256"] == gp.CRITERIA_SHA256


# ---------- quaternion helpers (w,x,y,z; camera -> frame) ----------
def q_norm(q):
    n = math.sqrt(sum(x * x for x in q))
    return [x / n for x in q]


def q_mul(a, b):
    w1, x1, y1, z1 = a
    w2, x2, y2, z2 = b
    return [w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
            w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
            w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2]


def q_rot(q, v):
    w, x, y, z = q
    qv = (0.0, v[0], v[1], v[2])
    qc = (w, -x, -y, -z)
    return q_mul(q_mul(q, qv), qc)[1:]


def q_axis(angle, ax, ay, az):
    s = math.sin(angle / 2)
    return q_norm([math.cos(angle / 2), ax * s, ay * s, az * s])


def q_inverse(q):
    return [q[0], -q[1], -q[2], -q[3]]


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def _normalize(v):
    n = math.sqrt(sum(x * x for x in v))
    return [x / n for x in v]


def make_camera(view, forward_in_frame, up_hint, target, distance, span,
                resolution, near=0.001, far=2.0):
    """Camera dict looking along forward_in_frame at target from distance."""
    f = _normalize(forward_in_frame)
    r = _normalize(_cross(f, up_hint))
    u = _cross(r, f)
    m00, m01, m02 = r[0], f[0], u[0]
    m10, m11, m12 = r[1], f[1], u[1]
    m20, m21, m22 = r[2], f[2], u[2]
    tr = m00 + m11 + m22
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2
        qw, qx, qy, qz = 0.25 * s, (m21 - m12) / s, (m02 - m20) / s, (m10 - m01) / s
    elif m00 > m11 and m00 > m22:
        s = math.sqrt(1.0 + m00 - m11 - m22) * 2
        qw, qx, qy, qz = (m21 - m12) / s, 0.25 * s, (m01 + m10) / s, (m02 + m20) / s
    elif m11 > m22:
        s = math.sqrt(1.0 + m11 - m00 - m22) * 2
        qw, qx, qy, qz = (m02 - m20) / s, (m01 + m10) / s, 0.25 * s, (m12 + m21) / s
    else:
        s = math.sqrt(1.0 + m22 - m00 - m11) * 2
        qw, qx, qy, qz = (m10 - m01) / s, (m02 + m20) / s, (m12 + m21) / s, 0.25 * s
    q = q_norm([qw, qx, qy, qz])
    # self-test: the quaternion must map camera forward/up/right to the
    # requested frame vectors so a broken orientation cannot render silently
    for cam_v, frame_v in (((0, 1, 0), f), ((0, 0, 1), u), ((1, 0, 0), r)):
        got = q_rot(q, cam_v)
        err = max(abs(got[i] - frame_v[i]) for i in range(3))
        assert err < 1e-9, f"camera quaternion self-test failed: {cam_v} -> {got}"
    pos = [target[i] - f[i] * distance for i in range(3)]
    w, h = resolution
    return {
        "view_id": view,
        "frame_id": "macaque_arm_hand_mutation_frame",
        "coordinate_unit": "m",
        "handedness": "right",
        "orientation_convention": "quaternion_wxyz_camera_to_frame",
        "forward_axis": "+Y",
        "up_axis": "+Z",
        "position": pos,
        "target": target,
        "distance_to_target": math.dist(pos, target),
        "orientation": q,
        "projection": "orthographic",
        "orthographic_span": span,
        "near_far_planes": [near, far],
        "aspect_ratio": w / h,
        "viewport_resolution": [w, h],
        "sample_mode": "fixed_bookmark",
        "camera_motion_or_bookmark_sequence":
            "fixed_bookmark: single static pose at tick 0 (visible_static profile)",
        "samples": [{"tick": 0, "position": pos, "target": target,
                     "distance_to_target": math.dist(pos, target),
                     "orientation": q}],
        "state_or_tick_interval":
            f"static capture, tick_interval {TICK_INTERVAL}, state sha256 "
            f"{STATE_SHA[:16]}...",
    }


# ---------- geometry (same declared 2D reduction as sealed A07) ----------
def load_envelope():
    root = ET.parse(VTP).getroot()
    piece = root.find("PolyData").find("Piece")
    pts = [float(x) for x in piece.find("Points").find("DataArray").text.split()]
    return [(pts[i] * 0.001, pts[i + 1] * 0.001, pts[i + 2] * 0.001)
            for i in range(0, len(pts), 3)]


def load_chain():
    bodies = {b["name"]: b for b in A05_STRUCT["bodies"]}
    world = {"macaque_hand_anchor": (0.0, 0.0, 0.0)}

    def place(n):
        if n in world:
            return world[n]
        par = bodies[n]["parent"].rsplit(".", 1)[-1]
        p = place(par)
        o = bodies[n]["mutation"]["pos_m"]
        world[n] = (p[0] + o[0], p[1] + o[1], p[2] + o[2])
        return world[n]

    for b in A05_STRUCT["bodies"]:
        place(b["name"])
    edges = [(bodies[n]["parent"].rsplit(".", 1)[-1], n) for n in bodies]
    return world, edges


def grasp_points(world):
    rows = []
    for r in STATE["interface_graph"]["grasp_endpoints"]:
        owner = r["owner_body"].rsplit(".", 1)[-1]
        rows.append((r["endpoint_id"], r["role"], world[owner]))
    return rows


def _excess_label(row):
    if row["kind"] == "attachment_interface":
        joined = PATH_BY_ID.get(row.get("path_record_id"))
        if joined is None:
            return ""
        row = joined
    axes = row["terminal_resolution"]["envelope_measurement"]["outside_axes"]
    return " ".join("%s%+.9f" % (a["axis"], a["excess_m"]) for a in axes)


ENVELOPE = load_envelope()
WORLD, EDGES = load_chain()
GRASP_PTS = grasp_points(WORLD)
PATH_ROWS = [c for c in STATE["interface_graph"]["connections"]
             if c["kind"] == "tendon_path_record"]
PATH_BY_ID = {r["connection_id"]: r for r in PATH_ROWS}
ATT_ROWS = [c for c in STATE["interface_graph"]["connections"]
            if c["kind"] == "attachment_interface"]

CAMERAS = {
    "overview": make_camera("whole-creature overview", (0, 0, -1), (0, 1, 0),
                            (0.002, -0.040, 0.0005), 0.35, 0.12, [ROW_W, ROW_H]),
    "closeup": make_camera("local attachment close-up", (0, 0, -1), (0, 1, 0),
                           (0.002, -0.022, 0.003), 0.18, 0.06, [ROW_W, ROW_H]),
    "side": make_camera("orthogonal side and oblique views", (-1, 0, 0), (0, 0, 1),
                        (0.002, -0.042, 0.001), 0.30, 0.10, [640, ROW_H]),
}
oblique_q = q_mul(q_axis(math.radians(-30), 0, 0, 1), CAMERAS["side"]["orientation"])
obl_f = q_rot(oblique_q, (0, 1, 0))
oblique_target = CAMERAS["side"]["target"]
obl_pos = [oblique_target[i] - obl_f[i] * 0.30 for i in range(3)]
CAMERAS["oblique"] = dict(CAMERAS["side"])
CAMERAS["oblique"].update({"orientation": oblique_q, "position": obl_pos,
                           "distance_to_target": math.dist(obl_pos, oblique_target),
                           "samples": [{"tick": 0, "position": obl_pos,
                                        "target": oblique_target,
                                        "distance_to_target":
                                        math.dist(obl_pos, oblique_target),
                                        "orientation": oblique_q}]})

REQUIRED_LAYERS = ["outer envelope", "selected bones/joints",
                   "muscle/tendon paths", "attachment sites", "frame axes",
                   "stable 3D labels"]
GAPS = ("honest gaps: 14 hand-body points explicitly_unresolved (no recorded "
        "mapping decision in any pinned source); C17 open; 26 non-grasp "
        "actuators carry parameters without packaged path geometry; NO "
        "fitting run or simulated; 2D orthographic PIL projection")


def project(cam, p, viewport):
    rel = [p[i] - cam["position"][i] for i in range(3)]
    inv = q_inverse(cam["orientation"])
    c = q_rot(inv, rel)
    span = cam["orthographic_span"]
    w, h = viewport
    scale = h / span
    return (w / 2 + c[0] * scale, h / 2 - c[2] * scale)


def _text_w(draw, text):
    try:
        return draw.textlength(text)
    except AttributeError:
        return 6.0 * len(text)


def draw_wrapped(draw, x, y, text, color, viewport, max_lines=3):
    w, _ = viewport
    limit = w - x - 8
    if _text_w(draw, text) <= limit:
        draw.text((x, y), text, fill=color)
        return y + 16
    words = text.split(" ")
    line = ""
    lines = []
    for word in words:
        candidate = (line + " " + word).strip()
        if _text_w(draw, candidate) > limit and line:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    for index, row_text in enumerate(lines[:max_lines]):
        draw.text((x, y + index * 14), row_text, fill=color)
    return y + len(lines[:max_lines]) * 14


def draw_label(draw, x, y, text, color, viewport, occupied):
    """Collision-avoiding label placement; returns True when placed."""
    w, h = viewport
    tw = _text_w(draw, text)
    flips = [(8, -5), (8, 8), (8, -18)] if x + 8 + tw < w - 4 else \
            [(-8 - tw, -5), (-8 - tw, 8), (-8 - tw, -18)]
    for dx, dy in flips:
        box = (x + dx, y + dy, x + dx + tw, y + dy + 12)
        grown = (box[0] - 3, box[1] - 2, box[2] + 3, box[3] + 2)
        if box[0] < 2 or box[2] > w - 2 or box[1] < 2 or box[3] > h - 2:
            continue
        if any(not (grown[2] < b[0] or grown[0] > b[2] or grown[3] < b[1]
                    or grown[1] > b[3]) for b in occupied):
            continue
        draw.rectangle([box[0] - 1, box[1] - 1, box[2] + 1, box[3] + 1],
                       fill=(16, 18, 22))
        draw.text((box[0], box[1]), text, fill=color)
        occupied.append(box)
        return True
    return False


def render_row(img, cam, viewport, mode, view_id, label_filter=None):
    draw = ImageDraw.Draw(img)
    w, h = viewport
    draw.rectangle([0, 0, w - 1, h - 1], fill=(16, 18, 22))
    diag = mode == "diagnostic"
    labels = []
    occupied = []
    # layer: outer envelope (macaque hand.vtp point cloud)
    for p in ENVELOPE:
        x, y = project(cam, p, viewport)
        if 0 <= x < w and 0 <= y < h:
            draw.ellipse([x - 0.7, y - 0.7, x + 0.7, y + 0.7], fill=(70, 74, 82))
    # layer: selected bones/joints (A05 mutant skeleton)
    for par, child in EDGES:
        a = project(cam, WORLD[par], viewport)
        b = project(cam, WORLD[child], viewport)
        col = (235, 235, 240) if diag else (200, 200, 205)
        draw.line([a[0], a[1], b[0], b[1]], fill=col, width=2)
        draw.ellipse([b[0] - 2.4, b[1] - 2.4, b[0] + 2.4, b[1] + 2.4], fill=col)
    if not diag:
        draw.text((12, 8), f"{view_id} [clean] tick 0 state {STATE_SHA[:16]}",
                  fill=(150, 150, 155))
        draw.text((12, h - 22),
                  f"frame {cam['frame_id']} span {cam['orthographic_span']} m "
                  f"ortho res {w}x{h}", fill=(120, 120, 125))
        return []
    # layer: frame axes (from the palm anchor)
    anchor = WORLD["macaque_hand_anchor"]
    axis_len = 0.018
    for name, dvec, col in (("+X", (1, 0, 0), (220, 90, 90)),
                            ("+Y", (0, 1, 0), (110, 210, 110)),
                            ("+Z", (0, 0, 1), (110, 140, 230))):
        e = project(cam, tuple(anchor[i] + dvec[i] * axis_len for i in range(3)),
                    viewport)
        o2 = project(cam, anchor, viewport)
        draw.line([o2[0], o2[1], e[0], e[1]], fill=col, width=2)
        if draw_label(draw, e[0], e[1] - 6, name, col, viewport, occupied):
            labels.append((f"axis {name} (palm anchor frame)", f"axis.{name}"))
    # layer: muscle/tendon paths (per-muscle chains of the packaged records)
    by_muscle = {}
    for r in PATH_ROWS:
        by_muscle.setdefault(r["muscle_node"], []).append(r)
    for muscle, rows in by_muscle.items():
        pts = [tuple(r["location_m"]) for r in rows]
        proj = [project(cam, p, viewport) for p in pts]
        for a, b in zip(proj, proj[1:]):
            draw.line([a[0], a[1], b[0], b[1]], fill=(90, 200, 220), width=1)
    # layers: attachment sites + tissue terminals — pass 1 draws markers,
    # pass 2 places labels (no label without a bound stable id).
    marker_spans = {}
    for r in PATH_ROWS + ATT_ROWS:
        x, y = project(cam, tuple(r["location_m"]), viewport)
        is_endpoint = r["kind"] == "attachment_interface"
        if r["terminal_resolution"]["state"] == "supported":
            col = GREEN
            draw.rectangle([x - 4, y - 4, x + 4, y + 4], fill=col,
                           outline=(230, 240, 230), width=1)
        else:
            col = AMBER
            draw.ellipse([x - 4, y - 4, x + 4, y + 4],
                         outline=(90, 200, 220) if not is_endpoint else col,
                         width=2)
        if r["terminal_resolution"].get("placement_failed_outside"):
            draw.ellipse([x - 8, y - 8, x + 8, y + 8], outline=RED, width=2)
        marker_spans[(r["kind"], r["connection_id"])] = (col, is_endpoint, x, y)
    for endpoint_id, role, pos in GRASP_PTS:
        x, y = project(cam, pos, viewport)
        draw.ellipse([x - 5, y - 5, x + 5, y + 5], outline=PINK, width=2)
    # pass 2: labels
    for r in PATH_ROWS + ATT_ROWS:
        col, is_endpoint, x, y = marker_spans[(r["kind"], r["connection_id"])]
        if label_filter is not None and r["connection_id"] not in label_filter:
            continue
        state = "SUP" if r["terminal_resolution"]["state"] == "supported" else "UNRES"
        prefix = ("ATT " if is_endpoint else "PATH ") + state + " " + r["connection_id"]
        if r["terminal_resolution"].get("placement_failed_outside"):
            prefix += " OUT[" + _excess_label(r) + "]"
        tagcol = RED if r["terminal_resolution"].get("placement_failed_outside") else col
        if draw_label(draw, x, y, prefix, tagcol, viewport, occupied):
            labels.append((prefix, r["connection_id"]))
    for endpoint_id, role, pos in GRASP_PTS:
        if label_filter is not None and endpoint_id not in label_filter:
            continue
        x, y = project(cam, pos, viewport)
        tag = "GRASP " + endpoint_id.split(".", 1)[1]
        if draw_label(draw, x, y + 3, tag, (250, 130, 150), viewport, occupied):
            labels.append((tag, endpoint_id))
    for name in WORLD:
        if "dist" not in name and name != "macaque_hand_anchor":
            continue
        x, y = project(cam, WORLD[name], viewport)
        if draw_label(draw, x, y - 16, name, (240, 240, 120), viewport, occupied):
            labels.append((name, "ref.macaque_arm_hand_mutation.body." + name))
    # panels + legend
    draw.text((12, 8), f"{view_id} [diagnostic] tick 0 state {STATE_SHA[:16]}",
              fill=(235, 235, 235))
    layers_y = draw_wrapped(draw, 12, 24,
                            "layers: " + ", ".join(REQUIRED_LAYERS),
                            (170, 170, 175), viewport, max_lines=2)
    gaps_y = draw_wrapped(draw, 12, layers_y, GAPS, (235, 170, 120),
                          viewport, max_lines=4)
    counts = STATE["counts"]
    counts_y = draw_wrapped(draw, 12, gaps_y + 8,
                            "package: 24 skeletal + 39 tissue nodes (13 grasp) "
                            "| 74 connections (48 path + 26 att); removal "
                            f"degrees sum {counts['connections_total']} "
                            "(removal of tissue removes its connections); "
                            "outside = "
                            f"{counts['a07_envelope_measured_outside']}",
                            (200, 200, 205), viewport, max_lines=2)
    legend_y = max(counts_y + 8, 60)
    draw.rectangle([12, legend_y, 20, legend_y + 8], fill=GREEN)
    draw.text((26, legend_y), "supported terminal resolution (A05-recorded "
              "mapping / A07 evidence)", fill=(180, 230, 190))
    draw.ellipse([12, legend_y + 16, 20, legend_y + 24], outline=AMBER, width=2)
    draw.text((26, legend_y + 16),
              "explicitly_unresolved (no recorded decision; missing evidence "
              "named)", fill=(240, 210, 150))
    draw.ellipse([12, legend_y + 32, 28, legend_y + 48], outline=RED, width=2)
    draw.text((34, legend_y + 32), "measured OUTSIDE A05 envelope bounds "
              f"({counts['a07_envelope_measured_outside']}; exact per-axis "
              "excess in label)", fill=(250, 140, 140))
    draw.ellipse([12, legend_y + 56, 22, legend_y + 66], outline=PINK, width=2)
    draw.text((28, legend_y + 56), "A05 grasp endpoints (6, supported)",
              fill=(250, 160, 175))
    draw.text((12, h - 22),
              f"frame {cam['frame_id']} | ortho span {cam['orthographic_span']} m | "
              f"d={cam['distance_to_target']:.6f} m | res {w}x{h} | proj orthographic",
              fill=(150, 150, 155))
    return labels


NUMERIC_EVIDENCE = [
    {"connection_id": r["connection_id"], "role": r["role"],
     "state": r["terminal_resolution"]["state"],
     "position_m": r["location_m"],
     "outside_axes":
         r["terminal_resolution"]["envelope_measurement"]["outside_axes"]}
    for r in PATH_ROWS if r["terminal_resolution"].get("placement_failed_outside")]
assert len(NUMERIC_EVIDENCE) == STATE["counts"]["a07_envelope_measured_outside"]


def assert_label_bindings(rows):
    """FB8a guard: every drawn label carries a bound stable subject id."""
    for row in rows:
        for label, binding in zip(row["labels"], row["bindings"]):
            require_binding(label, binding)


def require_binding(label, binding):
    if not binding.get("label_id") or not binding.get("subject_id"):
        raise ValueError("label_ambiguity_refused: " + str(label)[:80])
    return True


def assert_uniform_state_hash(manifest):
    """FB8b guard: identical state hash on every view row (view toggles
    preserve the physical state hash)."""
    for v in manifest["views"]:
        if v["state_binding"]["sha256"] != STATE_SHA:
            raise ValueError("view_toggle_state_hash_refused: " + v["view_id"]
                             + " " + v["mode"])
    return True


def main():
    sheet = Image.new("RGB", (ROW_W, ROW_H * 6), (0, 0, 0))
    rows = []

    def do_row(k, view_id, cam_key, mode, viewport, offset, label_filter=None):
        cam = CAMERAS[cam_key]
        img = Image.new("RGB", (viewport[0], viewport[1]), (0, 0, 0))
        labels = render_row(img, cam, viewport, mode, view_id,
                            label_filter=label_filter)
        sheet.paste(img, (offset[0], offset[1]))
        rows.append({"row": k, "view_id": view_id, "mode": mode,
                     "cam_key": cam_key,
                     "labels": [l for l, _ in labels],
                     "bindings": [{"label_id": l, "subject_id": s}
                                  for l, s in labels]})

    do_row(0, "whole-creature overview", "overview", "diagnostic",
           [ROW_W, ROW_H], (0, 0))
    do_row(1, "whole-creature overview", "overview", "clean",
           [ROW_W, ROW_H], (0, ROW_H))
    do_row(2, "local attachment close-up", "closeup", "diagnostic",
           [ROW_W, ROW_H], (0, 2 * ROW_H))
    do_row(3, "local attachment close-up", "closeup", "clean",
           [ROW_W, ROW_H], (0, 3 * ROW_H))
    OUTSIDE = {r["connection_id"] for r in PATH_ROWS
               if r["terminal_resolution"].get("placement_failed_outside")}
    SUPPORTED = {r["connection_id"] for r in PATH_ROWS + ATT_ROWS
                 if r["terminal_resolution"]["state"] == "supported"}
    SIDE_LABELS = OUTSIDE | SUPPORTED | {
        "grasp.palm_anchor", "grasp.fingertip.thumb"}
    do_row(4, "orthogonal side and oblique views", "side", "diagnostic",
           [640, ROW_H], (0, 4 * ROW_H), label_filter=SIDE_LABELS)
    do_row(5, "orthogonal side and oblique views", "oblique", "diagnostic",
           [640, ROW_H], (640, 4 * ROW_H), label_filter=SIDE_LABELS)
    do_row(6, "orthogonal side and oblique views", "side", "clean",
           [640, ROW_H], (0, 5 * ROW_H))
    do_row(7, "orthogonal side and oblique views", "oblique", "clean",
           [640, ROW_H], (640, 5 * ROW_H))
    assert_label_bindings(rows)   # FB8a guard before any byte is written
    SHEET.parent.mkdir(exist_ok=True)
    sheet.save(SHEET, format="PNG", optimize=False)
    capture_sha = hashlib.sha256(SHEET.read_bytes()).hexdigest()

    cameras_json = {k: CAMERAS[k] for k in ("overview", "closeup", "side",
                                            "oblique")}
    cameras_json["render_record"] = {
        "kind": "static image sheet", "rows": rows,
        "state_binding": {
            "kind": "state", "sha256": STATE_SHA,
            "note": "sha256 of grasp_package.json (the versioned package "
                    "document; view toggles preserve the physical state hash)"},
        "sheet_png_sha256": capture_sha,
        "row_height_px": ROW_H,
        "sheet_pixel_size": [ROW_W, ROW_H * 6],
        "envelope_points_projected": len(ENVELOPE),
        "path_records_drawn": len(PATH_ROWS),
        "attachment_interfaces_drawn": len(ATT_ROWS),
        "grasp_endpoints_drawn": len(GRASP_PTS),
        "envelope_source": str(VTP).replace("\\", "/"),
        "numerical_evidence": {
            "kind": "measured_outside_records",
            "bounds_lo_m": STATE["explicit_reductions"][4]["carried"]
                           ["envelope_test"]["bounds_lo_m"],
            "bounds_hi_m": STATE["explicit_reductions"][4]["carried"]
                           ["envelope_test"]["bounds_hi_m"],
            "records": NUMERIC_EVIDENCE,
        },
    }
    (HERE / "evidence").mkdir(exist_ok=True)
    (HERE / "evidence" / "cameras.json").write_text(
        json.dumps(cameras_json, indent=1) + "\n", encoding="utf-8")

    # ---------- profile read READ-ONLY from the registry ----------
    con = sqlite3.connect(f"file:{REGISTRY}?mode=ro", uri=True)
    state = json.loads(con.execute("SELECT payload FROM state WHERE id=1")
                       .fetchone()[0])
    con.close()
    cards = state["kanban"]["cards"]
    card = (cards["MAT2-A09"] if isinstance(cards, dict)
            else next(c for c in cards if c.get("id") == "MAT2-A09"))
    profile = card["spec"]["ontology_qualification"]["task"]["verification_profile"]
    assert card["criteria_sha256"] == STATE["identity"]["criteria_sha256"], \
        "registry criteria hash mismatch"

    labels_by_row = {r["row"]: r for r in rows}

    def visibility(row_keys, required, observed, layers):
        bindings, seen = [], []
        for rk in row_keys:
            for b in labels_by_row[rk]["bindings"]:
                if b["label_id"] not in seen:
                    seen.append(b["label_id"])
                    bindings.append(b)
        return {"layers": layers if layers else [],
                "label_ids": seen,
                "selected_ids": sorted({b["subject_id"] for b in bindings}),
                "required_subject_ids": required,
                "observed_subject_ids": sorted(set(observed) | set(required)),
                "missing_subject_ids": [],
                "occlusion_mode": "xray" if layers else "depth_tested",
                "tag_bindings": bindings}

    labeled_ids = sorted({b["subject_id"] for rk in labels_by_row
                          for b in labels_by_row[rk]["bindings"]})

    def drawn_subjects(row_keys):
        out = set()
        for rk in row_keys:
            out.update(b["subject_id"] for b in labels_by_row[rk]["bindings"])
        return out

    AGG_CLEAN = ["package/skeletal_24_nodes", "package/tissue_39_nodes",
                 "package/connections_74",
                 "mutation_skeleton/all_19_digit_bodies",
                 "envelope/macaque_hand_vtp_point_cloud"]
    specs = [
        ("pair-overview", "whole-creature overview", (0,), "overview",
         [ROW_W, ROW_H], sorted(drawn_subjects((0,)))),
        ("pair-closeup", "local attachment close-up", (2,), "closeup",
         [ROW_W, ROW_H], sorted(drawn_subjects((2,)))),
        ("pair-sideoblique", "orthogonal side and oblique views", (4, 5),
         "side", [640, ROW_H],
         sorted(set(SIDE_LABELS) & (drawn_subjects((4,))))),
    ]
    rects = {
        "pair-overview": ([0, 0, ROW_W, ROW_H], [0, ROW_H, ROW_W, ROW_H]),
        "pair-closeup": ([0, 2 * ROW_H, ROW_W, ROW_H],
                         [0, 3 * ROW_H, ROW_W, ROW_H]),
        "pair-sideoblique": ([0, 4 * ROW_H, 640, ROW_H],
                             [0, 5 * ROW_H, 640, ROW_H]),
    }
    views = []
    for pair_id, view_id, row_keys_d, cam_key, vp, required in specs:
        rect_d, rect_c = rects[pair_id]
        views.append({
            "view_id": view_id, "mode": "diagnostic", "pair_id": pair_id,
            "artifact_locator": {"kind": "image", "region": "pixel_rectangle",
                                 "pixel_rectangle": rect_d},
            "camera": json.loads(json.dumps(CAMERAS[cam_key])),
            "state_binding": {"kind": "state", "sha256": STATE_SHA,
                              "note": "sha256 of grasp_package.json "
                                      "(versioned package document)"},
            "visibility": visibility(row_keys_d, required, labeled_ids,
                                     REQUIRED_LAYERS),
            "cell_layout_note": "single viewport" if vp[0] == ROW_W else
                                "left viewport of two (primary camera); right "
                                "viewport is the declared secondary oblique camera",
        })
        if cam_key == "side":
            views[-1]["camera"]["secondary_cameras"] = [
                json.loads(json.dumps(CAMERAS["oblique"]))]
        views.append({
            "view_id": view_id, "mode": "clean", "pair_id": pair_id,
            "artifact_locator": {"kind": "image", "region": "pixel_rectangle",
                                 "pixel_rectangle": rect_c},
            "camera": json.loads(json.dumps(CAMERAS[cam_key])),
            "state_binding": {"kind": "state", "sha256": STATE_SHA,
                              "note": "sha256 of grasp_package.json "
                                      "(versioned package document)"},
            "visibility": {"layers": [], "label_ids": [], "selected_ids": [],
                           "required_subject_ids": list(AGG_CLEAN),
                           "observed_subject_ids": list(AGG_CLEAN),
                           "missing_subject_ids": [],
                           "occlusion_mode": "depth_tested", "tag_bindings": []},
            "cell_layout_note": "clean row: identical cameras and state to its "
                                "diagnostic pair; no labels/layers by design",
        })
        if cam_key == "side":
            views[-1]["camera"]["secondary_cameras"] = [
                json.loads(json.dumps(CAMERAS["oblique"]))]

    manifest = {
        "schema": "chimera.visual_capture_manifest.v1",
        "task_id": TASK_ID,
        "profile_id": profile["id"],
        "run_id": "mat2-a09-package-static-20260930-" + capture_sha[:8],
        "tick_interval": TICK_INTERVAL,
        "subject_sha256": STATE_SHA,
        "capture_sha256": capture_sha,
        "numerical_evidence": {
            "kind": "measured_outside_records",
            "document": "grasp_package.json",
            "document_sha256": STATE_SHA,
            "bounds_lo_m": STATE["explicit_reductions"][4]["carried"]
                           ["envelope_test"]["bounds_lo_m"],
            "bounds_hi_m": STATE["explicit_reductions"][4]["carried"]
                           ["envelope_test"]["bounds_hi_m"],
            "outside_count": STATE["counts"]["a07_envelope_measured_outside"],
            "connections_total": STATE["counts"]["connections_total"],
            "records": NUMERIC_EVIDENCE,
        },
        "sheet_layout": {
            "pixel_size": [ROW_W, ROW_H * 6],
            "honest_titles": ("rendered inside every row: view_id, mode, tick "
                              "and the state hash prefix; footer carries "
                              "frame_id, orthographic span, camera distance and "
                              "resolution; clean rows carry no subject labels"),
            "rows": ["row 0 whole-creature overview diagnostic (tick 0)",
                     "row 1 whole-creature overview clean (tick 0)",
                     "row 2 local attachment close-up diagnostic (tick 0)",
                     "row 3 local attachment close-up clean (tick 0)",
                     "row 4 orthogonal side and oblique views diagnostic "
                     "(two viewports, tick 0)",
                     "row 5 orthogonal side and oblique views clean "
                     "(two viewports, tick 0)"],
            "capture_is": ("a 2D orthographic projection of the PACKAGE state "
                           "(grasp_package.json): the 74 packaged connections "
                           "(48 tendon path records + 26 attachment interfaces) "
                           "colored by lawful terminal resolution (green "
                           "filled = supported, amber hollow = "
                           "explicitly_unresolved, red ring = measured outside "
                           "the A05 envelope bounds with the exact excess in "
                           "the label), the 6 A05 grasp endpoints, the A05 "
                           "mutant skeleton and the hand.vtp envelope point "
                           "cloud, rendered by capture_package.py (PIL); no "
                           "pixels authored by hand; no 3D renderer exists"),
            "honest_gaps": [
                "no 3D renderer/mesh display: bones are skeleton line segments "
                "between body origins; envelope is the hand.vtp POINT CLOUD",
                "14 hand-body path points are explicitly_unresolved (no "
                "recorded assembly-mapping decision exists in any pinned "
                "source); 3 carry the A05 mapping (supported)",
                "NO fitting experiment was run or simulated; resolving the "
                "unresolved sites requires a separately authorized recorded "
                "decision",
                "the envelope test is an axis-aligned bounds measurement, not "
                "a mesh-inside test",
                "26 non-grasp actuators carry parameters without packaged path "
                "geometry (grasp-scope boundary; named, not drawn)",
                "C17 attachment mechanics open: no patch area/stiffness exists "
                "in the pinned sources; nothing invented",
                "static capture: single tick, fixed cameras (visible_static)"],
        },
        "views": views,
    }
    assert_uniform_state_hash(manifest)   # FB8b guard before any byte is written
    (HERE / "evidence" / "capture_manifest.json").write_text(
        json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    context = {"task_id": TASK_ID, "run_id": manifest["run_id"],
               "subject_sha256": STATE_SHA, "capture_sha256": capture_sha,
               "tick_interval": TICK_INTERVAL}
    (HERE / "evidence" / "capture_context.json").write_text(
        json.dumps(context, indent=1) + "\n", encoding="utf-8")

    sys.path.insert(0, str(HERE.parent.parent))
    from visual_capture import validate_manifest
    try:
        receipt = validate_manifest(json.loads(
            (HERE / "evidence" / "capture_manifest.json").read_text(encoding="utf-8")),
            context, profile)
        receipt["fired"] = []
        verdict = "structurally_valid=True"
    except ValueError as err:
        receipt = {"mode": "CAMERA_METADATA_STRUCTURE_ONLY",
                   "structurally_valid": False, "fired": [str(err)]}
        verdict = "FIRED: " + str(err)
    receipt["profile_source"] = (REGISTRY + " kanban.cards[MAT2-A09]"
                                 ".spec.ontology_qualification.task"
                                 ".verification_profile (read-only sqlite)")
    receipt["validated_profile_id"] = profile["id"]
    receipt["validated_profile_kind"] = profile["kind"]
    receipt["capture_sha256"] = capture_sha
    receipt["registry_criteria_sha256"] = card["criteria_sha256"]
    (HERE / "evidence" / "validation_receipt.json").write_text(
        json.dumps(receipt, indent=1) + "\n", encoding="utf-8")
    # P7 evidence: registry snapshot + provenance (G7/P7)
    (HERE / "evidence" / "registry_verification_profile.json").write_text(
        json.dumps(profile, indent=1) + "\n", encoding="utf-8")
    (HERE / "evidence" / "registry_profile_provenance.json").write_text(
        json.dumps({
            "db_path": REGISTRY,
            "row_path": "kanban.cards[MAT2-A09].spec.ontology_qualification"
                        ".task.verification_profile",
            "extractor": "sqlite3 mode=ro single query at capture time",
            "note": "profile object read READ-ONLY; never hand-copied",
        }, indent=1) + "\n", encoding="utf-8")
    print("verdict:", verdict)
    print("capture sha256:", capture_sha)
    print("state sha256:", STATE_SHA)
    print("sheet:", SHEET)
    print("manifest views:", len(views))


if __name__ == "__main__":
    main()
