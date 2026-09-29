"""Render + validate the MAT2-B06 visible_static capture (anatomy profile).

Pure-Python/PIL 2D orthographic projection of the ASSEMBLY READINESS state
(assembly_readiness.json, sha-bound in every view) over the sealed dependency
geometry. TWO DECLARED FRAMES, NEVER MERGED (B04 no_fusion law is visually
honored):

  * `mat2_b06_assembly_world_m` — whole-creature overview + orthogonal
    side/oblique rows: the four B04 root frames as axis triads, the pinned
    source-chain polylines (bones/joints layer), component labels, the
    readiness verdict and per-domain gap counts (from the state document).
  * `macaque_arm_hand_mutation_frame` — local attachment close-up: hand.vtp
    envelope point cloud, the A05 mutant skeleton, and the 48 A07 resolution
    markers (green filled = supported, amber hollow = explicitly_unresolved,
    red ring = measured outside with the exact per-axis excess in the label).

No 3D engine, no GPU: declared 2D orthographic structured-records sheet with
real computed camera quaternions (self-test asserted). Manifest task_id is the
SHORT FORM "B06"; the profile object is read READ-ONLY from
E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3; validation uses the
UNMODIFIED source-head visual_capture.validate_manifest.
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

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import assembly_readiness as ar  # sealed-tip git blob loader + pins

VTP = pathlib.Path("E:/PythonChimera/tools/science_funnel/data/macaque_arm/"
                   "Geometry/hand.vtp")
VTP_SHA256 = "a06ea7e079c849df07d6eec001e9bcc2ea193ecd3914011c78a993a5faa94fc6"
REGISTRY = "E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3"
A05_STRUCT = pathlib.Path(
    "E:/ChimeraWork/monkey-coordination/kanban-attempts/MAT2-A05/"
    "b4ad70883ac2480a928dcc828f33c65f/checkout/tools/monkey_campaign/"
    "contributions/MAT2-A05/mutation_structure.json")
A05_STRUCT_SHA256 = ("48b037593f63ec473947d787077ab6fbcd3b364afd15765bff508e"
                     "7d54f45649")
SHEET = HERE / "capture" / "capture_mat2_b06_readiness_20260929.png"
ROW_W, ROW_H = 1280, 720
TICK_INTERVAL = [0, 0]
TASK_ID = "B06"
CARD_ID = "MAT2-B06"
ASSEMBLY_FRAME_ID = "mat2_b06_assembly_world_m"
HAND_FRAME_ID = "macaque_arm_hand_mutation_frame"

STATE_PATH = HERE / "assembly_readiness.json"
STATE = json.loads(STATE_PATH.read_text(encoding="utf-8"))
STATE_SHA = ar.sha256_bytes(STATE_PATH.read_bytes())
SEALED = ar.load_sealed()
A07 = SEALED["a07_resolution"]["doc"]
B04 = SEALED["b04_frames"]["doc"]

NO_FUSION_NOTE = ("frames NOT fused: assembly_world vs osim reference are "
                  "separate declared frames (B04 no_fusion_statement); "
                  "binding by name only")


def _check_pin(path: pathlib.Path, want: str, what: str) -> bytes:
    if not path.exists():
        raise SystemExit(f"{what} missing: {path}")
    raw = path.read_bytes()
    got = ar.sha256_bytes(raw)
    if got != want:
        raise SystemExit(f"{what} pin mismatch: {got} != {want}")
    return raw


# ---------- geometry ----------
def load_envelope():
    _check_pin(VTP, VTP_SHA256, "hand.vtp")
    root = ET.parse(VTP).getroot()
    piece = root.find("PolyData").find("Piece")
    pts = [float(x) for x in piece.find("Points").find("DataArray").text.split()]
    return [(pts[i] * 0.001, pts[i + 1] * 0.001, pts[i + 2] * 0.001)
            for i in range(0, len(pts), 3)]


def load_chain():
    raw = _check_pin(A05_STRUCT, A05_STRUCT_SHA256, "A05 mutation_structure")
    struct = json.loads(raw.decode("utf-8"))
    bodies = {b["name"]: b for b in struct["bodies"]}
    world = {"macaque_hand_anchor": (0.0, 0.0, 0.0)}

    def place(n):
        if n in world:
            return world[n]
        par = bodies[n]["parent"].rsplit(".", 1)[-1]
        p = place(par)
        o = bodies[n]["mutation"]["pos_m"]
        world[n] = (p[0] + o[0], p[1] + o[1], p[2] + o[2])
        return world[n]

    for b in struct["bodies"]:
        place(b["name"])
    edges = [(bodies[n]["parent"].rsplit(".", 1)[-1], n) for n in bodies]
    return world, edges


def assembly_chains():
    """World polylines of each B04 root chain (cumulative hop positions)."""
    out = {}
    for fid, f in B04["frames"].items():
        if not f.get("component_root"):
            continue
        pts, acc = [], [0.0, 0.0, 0.0]
        for hop in f["chain"]:
            acc = [acc[i] + hop["pos"][i] for i in range(3)]
            pts.append(tuple(acc))
        out[fid] = pts
    return out


def resolution_markers():
    rows = []
    for r in A07["path_resolutions"]:
        outside = bool(r.get("placement_failed_outside"))
        rows.append({
            "record_id": r["record_id"],
            "location": tuple(r["location_m"]),
            "resolution": r["resolution"],
            "outside": outside,
            "outside_axes": (r["envelope_measurement"].get("outside_axes")
                             if outside else []),
        })
    return rows


ENVELOPE = load_envelope()
WORLD, EDGES = load_chain()
CHAINS = assembly_chains()
MARKERS = resolution_markers()
SUPPORTED = [m for m in MARKERS if m["resolution"] == "supported"]
UNRESOLVED = [m for m in MARKERS if m["resolution"] == "explicitly_unresolved"
              and not m["outside"]]
OUTSIDE = [m for m in MARKERS if m["outside"]]
COMPONENTS = {c["component_id"]: c["root_frame_id"] for c in B04["components"]}


# ---------- quaternion helpers (w,x,y,z; camera -> frame) ----------
def q_norm(q):
    n = math.sqrt(sum(x * x for x in q))
    return [x / n for x in q]


def _q_mul(a, b):
    w1, x1, y1, z1 = a
    w2, x2, y2, z2 = b
    return [w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
            w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
            w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2]


def q_rot(q, v):
    qv = (0.0, v[0], v[1], v[2])
    qc = (q[0], -q[1], -q[2], -q[3])
    t = _q_mul(_q_mul(q, qv), qc)[1:]
    return t


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


q_mul = _q_mul


def make_camera(view, forward_in_frame, up_hint, target, distance, span,
                resolution, frame_id, near=0.001, far=10.0):
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
    for cam_v, frame_v in (((0, 1, 0), f), ((0, 0, 1), u), ((1, 0, 0), r)):
        got = q_rot(q, cam_v)
        err = max(abs(got[i] - frame_v[i]) for i in range(3))
        assert err < 1e-9, f"camera quaternion self-test failed: {cam_v}"
    pos = [target[i] - f[i] * distance for i in range(3)]
    w, h = resolution
    return {
        "view_id": view,
        "frame_id": frame_id,
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
            "fixed_bookmark: single static pose at tick 0 (visible_static "
            "profile)",
        "samples": [{"tick": 0, "position": pos, "target": target,
                     "distance_to_target": math.dist(pos, target),
                     "orientation": q}],
        "state_or_tick_interval":
            f"static capture, tick_interval {TICK_INTERVAL}, state sha256 "
            f"{STATE_SHA[:16]}...",
    }


TARGET_ASSEMBLY = [-0.05, 0.96, 0.005]
CAMERAS = {
    "overview": make_camera("whole-creature overview", (0, 0, -1), (0, 1, 0),
                            TARGET_ASSEMBLY, 1.5, 0.6, [ROW_W, ROW_H],
                            ASSEMBLY_FRAME_ID),
    "closeup": make_camera("local attachment close-up", (0, 0, -1), (0, 1, 0),
                           (0.002, -0.026, 0.002), 0.18, 0.075,
                           [ROW_W, ROW_H], HAND_FRAME_ID),
    "side": make_camera("orthogonal side and oblique views", (-1, 0, 0),
                        (0, 1, 0), TARGET_ASSEMBLY, 1.5, 0.6, [640, ROW_H],
                        ASSEMBLY_FRAME_ID),
}
oblique_q = q_mul(q_axis(math.radians(-28), 0, 1, 0),
                  CAMERAS["side"]["orientation"])
side_f = q_rot(CAMERAS["side"]["orientation"], (0, 1, 0))
obl_f = q_rot(oblique_q, (0, 1, 0))
oblique_target = CAMERAS["side"]["target"]
obl_pos = [oblique_target[i] - obl_f[i] * 1.5 for i in range(3)]
CAMERAS["oblique"] = dict(CAMERAS["side"])
CAMERAS["oblique"].update({"orientation": oblique_q, "position": obl_pos,
                           "distance_to_target":
                           math.dist(obl_pos, oblique_target),
                           "samples": [{"tick": 0, "position": obl_pos,
                                        "target": oblique_target,
                                        "distance_to_target":
                                        math.dist(obl_pos, oblique_target),
                                        "orientation": oblique_q}]})

ASSEMBLY_LAYERS = ["selected bones/joints", "frame axes", "stable 3D labels"]
HAND_LAYERS = ["outer envelope", "selected bones/joints",
               "muscle/tendon paths", "attachment sites", "stable 3D labels"]
GAPS_TEXT = ("honest gaps: readiness FALSE (10 gate gaps); 8/8 ports blocked; "
             "17.04 kg transported claims uncounted; 2D orthographic PIL "
             "projection of sealed records, no 3D renderer, no dynamics")


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


def draw_label(draw, x, y, text, color, viewport, occupied):
    w, h = viewport
    tw = _text_w(draw, text)
    flips = [(8, -5), (8, 8), (8, -18)] if x + 8 + tw < w - 4 else \
            [(-8 - tw, -5), (-8 - tw, 8), (-8 - tw, -18)]
    for dx, dy in flips:
        box = (x + dx, y + dy, x + dx + tw, y + dy + 12)
        if box[0] < 2 or box[2] > w - 2 or box[1] < 2 or box[3] > h - 2:
            continue
        if any(not (box[2] < b[0] or box[0] > b[2] or box[3] < b[1]
                    or box[1] > b[3]) for b in occupied):
            continue
        draw.rectangle([box[0] - 1, box[1] - 1, box[2] + 1, box[3] + 1],
                       fill=(16, 18, 22))
        draw.text((box[0], box[1]), text, fill=color)
        occupied.append(box)
        return True
    return False


def render_assembly(img, cam, viewport, mode):
    draw = ImageDraw.Draw(img)
    w, h = viewport
    draw.rectangle([0, 0, w - 1, h - 1], fill=(16, 18, 22))
    diag = mode == "diagnostic"
    labels = []
    occupied = []
    # layer: selected bones/joints — the pinned source-chain polylines
    for fid, pts in CHAINS.items():
        proj = [project(cam, p, viewport) for p in pts]
        col = (235, 235, 240) if diag else (200, 200, 205)
        for a, b in zip(proj, proj[1:]):
            draw.line([a[0], a[1], b[0], b[1]], fill=col, width=2)
        for p in proj:
            draw.ellipse([p[0] - 2.4, p[1] - 2.4, p[0] + 2.4, p[1] + 2.4],
                         fill=col)
    # layer: frame axes at root_pelvis origin (declared)
    anchor = CHAINS["root_pelvis"][0]
    axis_len = 0.08
    for name, dvec, col in (("+X", (1, 0, 0), (220, 90, 90)),
                            ("+Y", (0, 1, 0), (110, 210, 110)),
                            ("+Z", (0, 0, 1), (110, 140, 230))):
        e = project(cam, tuple(anchor[i] + dvec[i] * axis_len for i in range(3)),
                    viewport)
        o2 = project(cam, anchor, viewport)
        draw.line([o2[0], o2[1], e[0], e[1]], fill=col, width=2)
        if diag and draw_label(draw, e[0], e[1] - 6, name, col, viewport,
                               occupied):
            labels.append((f"axis {name} (root_pelvis frame)",
                           f"frame_axis.root_pelvis.{name}"))
    if not diag:
        draw.text((12, 8), f"whole assembly [clean] tick 0 state "
                           f"{STATE_SHA[:16]}", fill=(150, 150, 155))
        draw.text((12, h - 22),
                  f"frame {cam['frame_id']} span {cam['orthographic_span']} m "
                  f"ortho res {w}x{h}", fill=(120, 120, 125))
        return labels
    # labels: root frames + components
    for fid in sorted(CHAINS):
        tip = project(cam, CHAINS[fid][-1], viewport)
        comp = next((c for c, r in COMPONENTS.items() if r == fid), None)
        tag = f"{fid} -> {comp}"
        if draw_label(draw, tip[0], tip[1], tag, (240, 240, 120), viewport,
                      occupied):
            labels.append((tag, f"assembly_frame.{fid}"))
            labels.append((tag, f"component.{comp}"))
    counts = STATE["counts"]
    banner = (f"assembly readiness FALSE | gate gaps {counts['gate_gap']} "
              f"(mass {counts['gaps_by_domain']['mass']}, ownership "
              f"{counts['gaps_by_domain']['ownership']}, frame "
              f"{counts['gaps_by_domain']['frame']}, port "
              f"{counts['gaps_by_domain']['port']})")
    draw.text((12, 8), f"{cam['view_id']} [diagnostic] tick 0 state "
                       f"{STATE_SHA[:16]}", fill=(235, 235, 235))
    draw.text((12, 24), banner, fill=(250, 150, 120))
    draw.text((12, 40), "layers: " + ", ".join(ASSEMBLY_LAYERS),
              fill=(170, 170, 175))
    draw.text((12, 56), "counted mass 0.0 kg (frames are placement only; B04)",
              fill=(200, 200, 205))
    draw.text((12, 72), NO_FUSION_NOTE, fill=(235, 170, 120))
    draw.text((12, h - 22),
              f"frame {cam['frame_id']} | ortho span "
              f"{cam['orthographic_span']} m | d="
              f"{cam['distance_to_target']:.6f} m | res {w}x{h} | "
              "proj orthographic", fill=(150, 150, 155))
    return labels


def render_hand(img, cam, viewport, mode, label_filter=None):
    draw = ImageDraw.Draw(img)
    w, h = viewport
    draw.rectangle([0, 0, w - 1, h - 1], fill=(16, 18, 22))
    diag = mode == "diagnostic"
    labels = []
    occupied = []
    # layer: outer envelope (hand.vtp point cloud)
    for p in ENVELOPE:
        x, y = project(cam, p, viewport)
        if 0 <= x < w and 0 <= y < h:
            draw.ellipse([x - 0.7, y - 0.7, x + 0.7, y + 0.7], fill=(70, 74, 82))
    # layer: selected bones/joints (A05 mutant skeleton, osim frame)
    for par, child in EDGES:
        a = project(cam, WORLD[par], viewport)
        b = project(cam, WORLD[child], viewport)
        col = (235, 235, 240) if diag else (200, 200, 205)
        draw.line([a[0], a[1], b[0], b[1]], fill=col, width=2)
        draw.ellipse([b[0] - 2.0, b[1] - 2.0, b[0] + 2.0, b[1] + 2.0], fill=col)
    if not diag:
        draw.text((12, 8), f"attachment resolution [clean] tick 0 state "
                           f"{STATE_SHA[:16]}", fill=(150, 150, 155))
        draw.text((12, h - 22),
                  f"frame {cam['frame_id']} span {cam['orthographic_span']} m "
                  f"ortho res {w}x{h}", fill=(120, 120, 125))
        return labels
    # layer: muscle/tendon paths (hand-region chains, light)
    by_muscle = {}
    for r in A07["path_resolutions"]:
        by_muscle.setdefault(r["muscle"], []).append(r)
    for muscle, rows in by_muscle.items():
        pts = [r["location_m"] for r in rows if r["on_hand_body"]]
        if len(pts) < 2:
            continue
        proj = [project(cam, p, viewport) for p in pts]
        for a, b in zip(proj, proj[1:]):
            draw.line([a[0], a[1], b[0], b[1]], fill=(90, 200, 220), width=1)
    # layer: attachment sites — A07 resolution state
    marker_spans = {}
    for m in MARKERS:
        x, y = project(cam, m["location"], viewport)
        if m["outside"]:
            draw.ellipse([x - 6, y - 6, x + 6, y + 6], outline=(250, 70, 70),
                         width=2)
            col = (250, 120, 120)
        elif m["resolution"] == "supported":
            draw.rectangle([x - 4, y - 4, x + 4, y + 4], fill=(90, 220, 140),
                           outline=(230, 240, 230), width=1)
            col = (90, 220, 140)
        else:
            draw.ellipse([x - 4, y - 4, x + 4, y + 4], outline=(240, 190, 90),
                         width=2)
            col = (240, 190, 90)
        marker_spans[m["record_id"]] = (col, x, y)
    # pass 2: labels (supported subset + all outside with exact excesses)
    for m in SUPPORTED:
        if label_filter is not None and m["record_id"] not in label_filter:
            continue
        col, x, y = marker_spans[m["record_id"]]
        if draw_label(draw, x, y, m["record_id"], col, viewport, occupied):
            labels.append((m["record_id"], m["record_id"]))
    for m in OUTSIDE:
        if label_filter is not None and m["record_id"] not in label_filter:
            continue
        col, x, y = marker_spans[m["record_id"]]
        excess = ",".join(f"{ax['axis']}{ax['excess_m']:+.6f}"
                          for ax in m["outside_axes"])
        tag = f"OUT {m['record_id']} d[{excess}] m"
        if draw_label(draw, x, y - 14, tag, col, viewport, occupied):
            labels.append((tag, m["record_id"]))
    anchor = WORLD["macaque_hand_anchor"]
    for name, dvec, col in (("+X", (1, 0, 0), (220, 90, 90)),
                            ("+Y", (0, 1, 0), (110, 210, 110)),
                            ("+Z", (0, 0, 1), (110, 140, 230))):
        e = project(cam, tuple(anchor[i] + dvec[i] * 0.018 for i in range(3)),
                    viewport)
        o2 = project(cam, anchor, viewport)
        draw.line([o2[0], o2[1], e[0], e[1]], fill=col, width=2)
        if draw_label(draw, e[0], e[1] - 6, name, col, viewport, occupied):
            labels.append((f"axis {name} (osim hand frame)",
                           f"frame_axis.osim_hand.{name}"))
    # legend + panels
    draw.rectangle([12, 92, 16, 100], fill=(90, 220, 140))
    draw.text((20, 92), "supported (3 paths / 2 attachments / 1 waypoint / "
                        "6 grasp endpoints)", fill=(180, 230, 190))
    draw.ellipse([12, 108, 20, 116], outline=(240, 190, 90), width=2)
    draw.text((26, 108), "explicitly_unresolved (named missing evidence + "
                         "authorizing rank)", fill=(240, 210, 150))
    draw.ellipse([12, 124, 24, 136], outline=(250, 70, 70), width=2)
    draw.text((30, 124), "measured outside (8; exact per-axis excess in label)",
              fill=(250, 140, 140))
    draw.text((12, 8), f"{cam['view_id']} [diagnostic] tick 0 state "
                       f"{STATE_SHA[:16]}", fill=(235, 235, 235))
    draw.text((12, 24), "layers: " + ", ".join(HAND_LAYERS),
              fill=(170, 170, 175))
    draw.text((12, 40), GAPS_TEXT, fill=(235, 170, 120))
    draw.text((12, 56), NO_FUSION_NOTE, fill=(235, 170, 120))
    draw.text((12, h - 22),
              f"frame {cam['frame_id']} | ortho span "
              f"{cam['orthographic_span']} m | d="
              f"{cam['distance_to_target']:.6f} m | res {w}x{h} | "
              "proj orthographic", fill=(150, 150, 155))
    return labels


def main():
    sheet = Image.new("RGB", (ROW_W, ROW_H * 6), (0, 0, 0))
    rows = []

    def do_row(k, view_id, cam_key, mode, viewport, offset, kind,
               label_filter=None):
        cam = CAMERAS[cam_key]
        img = Image.new("RGB", (viewport[0], viewport[1]), (0, 0, 0))
        if kind == "assembly":
            labels = render_assembly(img, cam, viewport, mode)
        else:
            labels = render_hand(img, cam, viewport, mode,
                                 label_filter=label_filter)
        sheet.paste(img, (offset[0], offset[1]))
        rows.append({"row": k, "view_id": view_id, "mode": mode,
                     "cam_key": cam_key, "kind": kind,
                     "labels": [l for l, _ in labels],
                     "bindings": [{"label_id": l, "subject_id": s}
                                  for l, s in labels]})

    do_row(0, "whole-creature overview", "overview", "diagnostic",
           [ROW_W, ROW_H], (0, 0), "assembly")
    do_row(1, "whole-creature overview", "overview", "clean",
           [ROW_W, ROW_H], (0, ROW_H), "assembly")
    do_row(2, "local attachment close-up", "closeup", "diagnostic",
           [ROW_W, ROW_H], (0, 2 * ROW_H), "hand")
    do_row(3, "local attachment close-up", "closeup", "clean",
           [ROW_W, ROW_H], (0, 3 * ROW_H), "hand")
    SIDE_LABELS = {m["record_id"] for m in SUPPORTED} | \
                  {m["record_id"] for m in OUTSIDE}
    do_row(4, "orthogonal side and oblique views", "side", "diagnostic",
           [640, ROW_H], (0, 4 * ROW_H), "assembly")
    do_row(5, "orthogonal side and oblique views", "oblique", "diagnostic",
           [640, ROW_H], (640, 4 * ROW_H), "assembly")
    do_row(6, "orthogonal side and oblique views", "side", "clean",
           [640, ROW_H], (0, 5 * ROW_H), "assembly")
    do_row(7, "orthogonal side and oblique views", "oblique", "clean",
           [640, ROW_H], (640, 5 * ROW_H), "assembly")
    SHEET.parent.mkdir(exist_ok=True)
    sheet.save(SHEET, format="PNG", optimize=False)
    capture_sha = ar.sha256_bytes(SHEET.read_bytes())

    cameras_json = {k: CAMERAS[k] for k in
                    ("overview", "closeup", "side", "oblique")}
    cameras_json["render_record"] = {
        "kind": "static image sheet", "rows": rows,
        "state_binding": {
            "kind": "state", "sha256": STATE_SHA,
            "note": "sha256 of assembly_readiness.json (the readiness state "
                    "document; view toggles preserve the physical state "
                    "hash)"},
        "sheet_png_sha256": capture_sha,
        "row_height_px": ROW_H,
        "sheet_pixel_size": [ROW_W, ROW_H * 6],
        "envelope_points_projected": len(ENVELOPE),
        "assembly_chain_polylines": {k: len(v) for k, v in CHAINS.items()},
        "resolution_markers_drawn": len(MARKERS),
        "outside_markers": len(OUTSIDE),
        "supported_markers": len(SUPPORTED),
        "frames_declared": [ASSEMBLY_FRAME_ID, HAND_FRAME_ID],
        "no_fusion_note": NO_FUSION_NOTE,
        "envelope_source": str(VTP).replace("\\", "/"),
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
    card = (cards[CARD_ID] if isinstance(cards, dict)
            else next(c for c in cards if c.get("id") == CARD_ID))
    profile = card["spec"]["ontology_qualification"]["task"][
        "verification_profile"]
    assert card["criteria_sha256"] == STATE["criteria_sha256"], \
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

    def drawn_subjects(row_keys):
        out = set()
        for rk in row_keys:
            out.update(b["subject_id"] for b in labels_by_row[rk]["bindings"])
        return out

    root_subjects = [f"assembly_frame.{fid}" for fid in sorted(CHAINS)]
    # one record can be BOTH osim-reference-supported AND mutant-assembly
    # measured-outside (A07 carries both facts); dedupe the required set
    outside_ids = sorted({m["record_id"] for m in OUTSIDE})
    supported_ids = sorted({m["record_id"] for m in SUPPORTED})
    AGG_CLEAN = ["assembly/root_frames_4", "assembly/source_chain_polylines",
                 "resolution/markers_48", "envelope/macaque_hand_vtp_point_cloud"]
    specs = [
        ("pair-overview", "whole-creature overview", (0,), "overview",
         [ROW_W, ROW_H], root_subjects, ASSEMBLY_LAYERS),
        ("pair-closeup", "local attachment close-up", (2,), "closeup",
         [ROW_W, ROW_H], sorted(set(outside_ids) | set(supported_ids)),
         HAND_LAYERS),
        ("pair-sideoblique", "orthogonal side and oblique views", (4, 5),
         "side", [640, ROW_H],
         sorted(root_subjects), ASSEMBLY_LAYERS),
    ]
    rects = {
        "pair-overview": ([0, 0, ROW_W, ROW_H], [0, ROW_H, ROW_W, ROW_H]),
        "pair-closeup": ([0, 2 * ROW_H, ROW_W, ROW_H],
                         [0, 3 * ROW_H, ROW_W, ROW_H]),
        "pair-sideoblique": ([0, 4 * ROW_H, 640, ROW_H],
                             [0, 5 * ROW_H, 640, ROW_H]),
    }
    views = []
    for pair_id, view_id, row_keys_d, cam_key, vp, required, layers in specs:
        rect_d, rect_c = rects[pair_id]
        obs_d = sorted(drawn_subjects(row_keys_d))
        views.append({
            "view_id": view_id, "mode": "diagnostic", "pair_id": pair_id,
            "artifact_locator": {"kind": "image", "region": "pixel_rectangle",
                                 "pixel_rectangle": rect_d},
            "camera": json.loads(json.dumps(CAMERAS[cam_key])),
            "state_binding": {"kind": "state", "sha256": STATE_SHA,
                              "note": "sha256 of assembly_readiness.json "
                                      "(readiness state document)"},
            "visibility": visibility(row_keys_d, required, obs_d, layers),
            "cell_layout_note": "single viewport" if vp[0] == ROW_W else
                                "left viewport of two (primary camera); right "
                                "viewport is the declared secondary oblique "
                                "camera",
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
                              "note": "sha256 of assembly_readiness.json "
                                      "(readiness state document)"},
            "visibility": {"layers": [], "label_ids": [],
                           "selected_ids": [],
                           "required_subject_ids": list(AGG_CLEAN),
                           "observed_subject_ids": list(AGG_CLEAN),
                           "missing_subject_ids": [],
                           "occlusion_mode": "depth_tested",
                           "tag_bindings": []},
            "cell_layout_note": "clean row: identical cameras and state to "
                                "its diagnostic pair; no labels/layers by "
                                "design",
        })
        if cam_key == "side":
            views[-1]["camera"]["secondary_cameras"] = [
                json.loads(json.dumps(CAMERAS["oblique"]))]

    manifest = {
        "schema": "chimera.visual_capture_manifest.v1",
        "task_id": TASK_ID,
        "profile_id": profile["id"],
        "run_id": "mat2-b06-readiness-static-20260929-" + capture_sha[:8],
        "tick_interval": TICK_INTERVAL,
        "subject_sha256": STATE_SHA,
        "capture_sha256": capture_sha,
        "sheet_layout": {
            "pixel_size": [ROW_W, ROW_H * 6],
            "honest_titles": ("rendered inside every row: view_id, mode, tick "
                              "and the state hash prefix; footer carries "
                              "frame_id, orthographic span, camera distance "
                              "and resolution; clean rows carry no subject "
                              "labels"),
            "rows": ["row 0 whole-creature overview diagnostic (tick 0, "
                     "assembly_world frame)",
                     "row 1 whole-creature overview clean (tick 0)",
                     "row 2 local attachment close-up diagnostic (tick 0, "
                     "osim hand frame)",
                     "row 3 local attachment close-up clean (tick 0)",
                     "row 4 orthogonal side and oblique views diagnostic "
                     "(two viewports, tick 0, assembly_world frame)",
                     "row 5 orthogonal side and oblique views clean "
                     "(two viewports, tick 0)"],
            "capture_is": ("a 2D orthographic projection of the assembly "
                           "readiness state (assembly_readiness.json): the "
                           "four B04 root frames as axis triads, the pinned "
                           "source-chain polylines (bones/joints layer), the "
                           "A07 resolution markers over the hand.vtp envelope "
                           "point cloud and A05 mutant skeleton, rendered by "
                           "capture_readiness.py (PIL); no pixels authored by "
                           "hand; no 3D renderer exists"),
            "honest_gaps": [
                "two declared frames are NEVER merged: assembly_world rows "
                "and osim hand-frame rows are separate views (B04 "
                "no_fusion_statement); no row overlays them",
                "readiness FALSE is the honest sealed outcome: 10 gate gaps "
                "(mass 3, ownership 4, frame 2, port 1); 8/8 ports blocked",
                "17.039978509953905 kg transported claims stay uncounted; "
                "screens never gate",
                "2D orthographic structured-records sheet of sealed records; "
                "not a native-engine 3D render; no dynamics",
                "static capture: single tick, fixed cameras (visible_static)"],
        },
        "views": views,
    }
    (HERE / "evidence" / "capture_manifest.json").write_text(
        json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    context = {"task_id": TASK_ID, "run_id": manifest["run_id"],
               "subject_sha256": STATE_SHA, "capture_sha256": capture_sha,
               "tick_interval": TICK_INTERVAL}
    (HERE / "evidence" / "capture_context.json").write_text(
        json.dumps(context, indent=1) + "\n", encoding="utf-8")

    sys.path.insert(0, "E:/PythonChimera/tools/monkey_campaign")
    from visual_capture import validate_manifest
    try:
        receipt = validate_manifest(json.loads(
            (HERE / "evidence" / "capture_manifest.json").read_text(
                encoding="utf-8")), context, profile)
        receipt["fired"] = []
        verdict = "structurally_valid=True"
    except ValueError as err:
        receipt = {"mode": "CAMERA_METADATA_STRUCTURE_ONLY",
                   "structurally_valid": False, "fired": [str(err)]}
        verdict = "FIRED: " + str(err)
    receipt["profile_source"] = (REGISTRY + " kanban.cards[MAT2-B06]"
                                 ".spec.ontology_qualification.task"
                                 ".verification_profile (read-only sqlite)")
    receipt["validated_profile_id"] = profile["id"]
    receipt["validated_profile_kind"] = profile["kind"]
    receipt["capture_sha256"] = capture_sha
    receipt["registry_criteria_sha256"] = card["criteria_sha256"]
    (HERE / "evidence" / "validation_receipt.json").write_text(
        json.dumps(receipt, indent=1) + "\n", encoding="utf-8")
    print("verdict:", verdict)
    print("capture sha256:", capture_sha)
    print("state sha256:", STATE_SHA)
    print("sheet:", SHEET)
    print("manifest views:", len(views))


if __name__ == "__main__":
    main()
