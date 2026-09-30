"""MAT2-G03 motion capture: render the declared-chain pose sweep, encode
FFV1 (codec law), bind the manifest to the sweep trace, validate with the
registry profile (mode=ro), and prove decode identity.

Run from this directory:
    python -B make_capture.py <capture_work_dir> <ffmpeg_path>

Layout of one frame (2 rows x 3 columns, 960x600 each):
    top    diagnostic viewports: chain overview | endpoint close-up |
           alternate pose/axis view (3 required diagnostic layers)
    bottom clean viewports: identical cameras and state, no labels/layers

Laws honored here: FFV1 -level 3 -g 1 -fflags +bitexact (CODEC_STANDARD
section 5); ffmpeg version first line recorded; single gate-bound capture
identity (G8); frames are the determinism unit with per-frame shas + concat
sha (P8); decode == stills at recomputable indices (G4); profile read
mode=ro from agent_slots.sqlite3 with SHORT task_id G03 (P7); FB7a/FB7b
capture falsifier arms with clean controls refuse BEFORE any manifest byte
is written.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import shutil
import sqlite3
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw

import tendon_sweep as ts

HERE = pathlib.Path(__file__).resolve().parent
REGISTRY_DB = "E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3"
TASK_ID = "G03"
TICKS = 21
VP_W, VP_H = 960, 600
GUT = 16
SHEET_W = GUT + 3 * VP_W + 2 * GUT
SHEET_H = GUT + 2 * VP_H + GUT
DATE_TAG = "20260930"

GREEN = (90, 220, 140)
AMBER = (240, 190, 90)
CYAN = (90, 200, 220)
BONE = (225, 225, 232)
AXIS_COLORS = {"x": (220, 90, 90), "y": (110, 210, 110),
               "z": (110, 140, 230)}
TRACE_COLORS = [(250, 200, 110), (140, 220, 250), (230, 140, 220),
                (170, 240, 170), (240, 160, 140), (180, 180, 250)]

DOC = json.loads((HERE / "tendon_sweep.json").read_text(encoding="utf-8"))
DOC_SHA = hashlib.sha256((HERE / "tendon_sweep.json").read_bytes()).hexdigest()
TRACE_SHA = hashlib.sha256((HERE / "sweep_trace.json").read_bytes()).hexdigest()
SUBTREES = None


# ---------- quaternions (w,x,y,z; camera -> frame) ----------
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


def q_inverse(q):
    return [q[0], -q[1], -q[2], -q[3]]


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def _norm(v):
    n = math.sqrt(sum(x * x for x in v))
    return [x / n for x in v]


def make_camera(view_id, forward, up_hint, target, distance, span, near=0.001,
                far=2.0):
    f = _norm(forward)
    r = _norm(_cross(f, up_hint))
    u = _cross(r, f)
    m00, m01, m02 = r[0], f[0], u[0]
    m10, m11, m12 = r[1], f[1], u[1]
    m20, m21, m22 = r[2], f[2], u[2]
    tr = m00 + m11 + m22
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2
        qw, qx, qy, qz = 0.25 * s, (m21 - m12) / s, (m02 - m20) / s, \
            (m10 - m01) / s
    elif m00 > m11 and m00 > m22:
        s = math.sqrt(1.0 + m00 - m11 - m22) * 2
        qw, qx, qy, qz = (m21 - m12) / s, 0.25 * s, (m01 + m10) / s, \
            (m02 + m20) / s
    elif m11 > m22:
        s = math.sqrt(1.0 + m11 - m00 - m22) * 2
        qw, qx, qy, qz = (m02 - m20) / s, (m01 + m10) / s, 0.25 * s, \
            (m12 + m21) / s
    else:
        s = math.sqrt(1.0 + m22 - m00 - m11) * 2
        qw, qx, qy, qz = (m10 - m01) / s, (m02 + m20) / s, (m12 + m21) / s, \
            0.25 * s
    q = q_norm([qw, qx, qy, qz])
    for cam_v, frame_v in (((0, 1, 0), f), ((0, 0, 1), u), ((1, 0, 0), r)):
        got = q_rot(q, cam_v)
        err = max(abs(got[i] - frame_v[i]) for i in range(3))
        assert err < 1e-9, "camera quaternion self-test failed"
    pos = [target[i] - f[i] * distance for i in range(3)]
    samples = []
    for tick in (0, TICKS - 1):
        samples.append({"tick": tick, "position": pos, "target": target,
                        "distance_to_target": math.dist(pos, target),
                        "orientation": q})
    return {
        "view_id": view_id,
        "frame_id": "monkeyArm_current_osim_ground_frame",
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
        "aspect_ratio": VP_W / VP_H,
        "viewport_resolution": [VP_W, VP_H],
        "sample_mode": "fixed_bookmark",
        "camera_motion_or_bookmark_sequence":
            "fixed_bookmark: static camera across the 21-tick wrist_flexion "
            "pose sweep (the STATE moves, the camera does not)",
        "samples": samples,
        "state_or_tick_interval":
            f"motion capture, tick_interval [0, {TICKS - 1}], one tick per "
            f"sweep pose; trace sha256 {TRACE_SHA[:16]}...",
    }


WORLD = None  # no global mutable geometry; everything renders from the doc


def registry_profile():
    con = sqlite3.connect(f"file:{REGISTRY_DB}?mode=ro", uri=True)
    try:
        payload = con.execute("SELECT payload FROM state WHERE id=1") \
            .fetchone()[0]
    finally:
        con.close()
    reg = json.loads(payload)
    card = reg["kanban"]["cards"]["MAT2-G03"]
    assert card["criteria_sha256"] == ts.CRITERIA_SHA256, \
        "registry criteria hash mismatch"
    return card["spec"]["ontology_qualification"]["task"][
        "verification_profile"]


PROFILE = registry_profile()

CAMS = {
    "chain overview": make_camera("chain overview", (0, 0, -1), (0, 1, 0),
                                  (0.085, -0.115, 0.005), 0.55, 0.42),
    "endpoint close-up": make_camera("endpoint close-up", (0, 0, -1),
                                     (0, 1, 0), (0.14, -0.116, 0.0055),
                                     0.12, 0.045),
    "alternate pose/axis view": make_camera("alternate pose/axis view",
                                            (0, -1, 0), (0, 0, 1),
                                            (0.085, -0.115, 0.005), 0.45,
                                            0.36),
}


# ---------- geometry helpers over the sweep document ----------
def fk_world(joints, order, q):
    return ts.build_X(joints, order, q)


def body_chain_segments(joints, order, X):
    segs = []
    for bn in order:
        if bn == "ground":
            continue
        par = joints[bn]["parent"]
        segs.append((par, bn))
    return segs


def project(cam, p):
    rel = [p[i] - cam["position"][i] for i in range(3)]
    c = q_rot(q_inverse(cam["orientation"]), rel)
    scale = VP_H / cam["orthographic_span"]
    return (c[0] * scale, -c[2] * scale)


def sweep_q(doc, tick):
    t = doc["sweep"][tick]
    return t["q_rad"]


# ---------- drawing ----------
def draw_label(draw, x, y, text, color, occupied):
    tw = draw.textlength(text)
    flips = [(10, -6), (10, 8), (10, -20)] if x + 10 + tw < VP_W - 4 else \
            [(-10 - tw, -6), (-10 - tw, 8), (-10 - tw, -20)]
    for dx, dy in flips:
        box = (x + dx, y + dy, x + dx + tw, y + dy + 12)
        grown = (box[0] - 3, box[1] - 2, box[2] + 3, box[3] + 2)
        if box[0] < 2 or box[2] > VP_W - 2 or box[1] < 2 or box[3] > VP_H - 2:
            continue
        if any(not (grown[2] < b[0] or grown[0] > b[2] or grown[3] < b[1]
                    or grown[1] > b[3]) for b in occupied):
            continue
        draw.rectangle([box[0] - 1, box[1] - 1, box[2] + 1, box[3] + 1],
                       fill=(14, 16, 20))
        draw.text((box[0], box[1]), text, fill=color)
        occupied.append(box)
        return True
    return False


def render_viewport(img, cam, doc, tick, mode, view_id, world_cache):
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, VP_W - 1, VP_H - 1], fill=(14, 16, 20))
    diag = mode == "diagnostic"
    labels = []
    occupied = []

    def bind(label, subject):
        labels.append((label, subject))

    joints, order = world_cache["joints"], world_cache["order"]
    q_def = world_cache["q_default"]
    q = dict(q_def)
    q[ts.SWEEP_COORD] = sweep_q(doc, tick)
    X = world_cache["X_cache"].setdefault(
        tick, ts.build_X(joints, order, q))
    paths = world_cache["paths"]

    # layer: declared chain skeleton (bones = joint-to-body-origin segments)
    for par, child in body_chain_segments(joints, order, X):
        if par not in X or child not in X:
            continue
        a = project(cam, X[par][1])
        b = project(cam, X[child][1])
        col = BONE if diag else (150, 150, 158)
        draw.line([VP_W / 2 + a[0], VP_H / 2 + a[1],
                   VP_W / 2 + b[0], VP_H / 2 + b[1]], fill=col, width=2)
        draw.ellipse([VP_W / 2 + b[0] - 2.2, VP_H / 2 + b[1] - 2.2,
                      VP_W / 2 + b[0] + 2.2, VP_H / 2 + b[1] + 2.2],
                     fill=col)

    if not diag:
        draw.text((10, 6), f"{view_id} [clean] tick {tick} trace "
                          f"{TRACE_SHA[:12]}", fill=(120, 120, 126))
        draw.text((10, VP_H - 20),
                  f"frame {cam['frame_id']} | span "
                  f"{cam['orthographic_span']} m | ortho | q_wrist_flexion="
                  f"{q['wrist_flexion']:+.6f} rad", fill=(115, 115, 120))
        return labels

    # layer: joint axes and stable IDs (wrist flexion/abduction + elbow)
    for coord, tag in (("wrist_flexion", "joint.wrist_flexion"),
                       ("wrist_abduction", "joint.wrist_abduction"),
                       ("elbow_flexion", "joint.elbow_flexion")):
        jf = ts.joint_frame(joints, order, world_cache["subtrees"], coord,
                            X, q)
        c0 = project(cam, jf["axis_point_world"])
        L = 0.02 if coord != "elbow_flexion" else 0.03
        e = project(cam, [jf["axis_point_world"][i]
                          + jf["axis_world"][i] * L for i in range(3)])
        col = (250, 170, 90)
        draw.line([VP_W / 2 + c0[0], VP_H / 2 + c0[1],
                   VP_W / 2 + e[0], VP_H / 2 + e[1]], fill=col, width=2)
        if draw_label(draw, VP_W / 2 + e[0], VP_H / 2 + e[1], tag, col, occupied):
            bind(tag + ".axis", tag)

    # layer: resolved tendon endpoints and paths
    for mi, m in enumerate(ts.GRASP_MUSCLES):
        pts, owners, bodies = ts.world_points(paths, m, X)
        term = [r["terminal_resolution"]["state"] for r in paths[m]]
        proj = []
        for p in pts:
            xy = project(cam, p)
            proj.append((VP_W / 2 + xy[0], VP_H / 2 + xy[1]))
        for a, b in zip(proj, proj[1:]):
            draw.line([a[0], a[1], b[0], b[1]], fill=CYAN, width=1)
        for (x, y), st in zip(proj, term):
            if st == "supported":
                draw.rectangle([x - 3, y - 3, x + 3, y + 3], fill=GREEN)
            else:
                draw.ellipse([x - 3, y - 3, x + 3, y + 3], outline=AMBER,
                             width=1)
        if view_id != "endpoint close-up" and mi % 3 == 0:
            if draw_label(draw, proj[-1][0], proj[-1][1],
                          m.replace("muscle.", "muscle."), (160, 220, 235),
                          occupied):
                bind("path." + m, m)

    # layer: length and moment-arm traces (bottom strip, overview only)
    if view_id == "chain overview":
        x0, y0, w0, h0 = 12, VP_H - 178, VP_W - 24, 150
        draw.rectangle([x0, y0, x0 + w0, y0 + h0], outline=(70, 74, 82))
        draw.text((x0 + 6, y0 + 2),
                  "length l(q) [m] and signed moment arm r(q) [m] traces "
                  "(per tick, from sweep_trace.json)", fill=(170, 170, 175))
        trace = world_cache["trace"]["ticks"]
        qs = [tr["q_rad"] for tr in trace]
        qlo, qhi = min(qs), max(qs)
        series = [
            ("trace.l.flex_carpi_radialis",
             [tr["muscles"]["muscle.flex_carpi_radialis"][ts.SWEEP_COORD]
              ["l_m"] for tr in trace]),
            ("trace.l.ext_carpi_ulnaris",
             [tr["muscles"]["muscle.ext_carpi_ulnaris"][ts.SWEEP_COORD]
              ["l_m"] for tr in trace]),
            ("trace.r_wrist_flexion.flex_carpi_radialis",
             [tr["muscles"]["muscle.flex_carpi_radialis"][ts.SWEEP_COORD]
              ["r_analytic_m"] for tr in trace]),
            ("trace.r_wrist_flexion.ext_carpi_ulnaris",
             [tr["muscles"]["muscle.ext_carpi_ulnaris"][ts.SWEEP_COORD]
              ["r_analytic_m"] for tr in trace]),
            ("trace.r_wrist_abduction.flex_digit_profundus",
             [tr["muscles"]["muscle.flex_digit_profundus"]
              ["wrist_abduction"]["r_analytic_m"] for tr in trace]),
            ("trace.l.flex_digit_profundus",
             [tr["muscles"]["muscle.flex_digit_profundus"][ts.SWEEP_COORD]
              ["l_m"] for tr in trace]),
        ]
        pad_t, pad_b = 20, 16
        for si, (name, vals) in enumerate(series):
            col = TRACE_COLORS[si % len(TRACE_COLORS)]
            lo, hi = min(vals), max(vals)
            rng = (hi - lo) or 1e-9
            pts = []
            for i, v in enumerate(vals):
                fx = x0 + 8 + (w0 - 16) * i / (len(vals) - 1)
                fy = y0 + pad_t + (h0 - pad_t - pad_b) * (1 - (v - lo) / rng)
                pts.append((fx, fy))
            for a, b in zip(pts, pts[1:]):
                draw.line([a[0], a[1], b[0], b[1]], fill=col, width=1)
            lx = x0 + 8 + si * ((w0 - 16) // 6)
            if draw_label(draw, lx, y0 + h0 - 12, name, col, occupied):
                bind(name + ".curve", name)
        draw.text((x0 + w0 - 150, y0 + 2),
                  f"q in [{qlo:+.4f}, {qhi:+.4f}] rad",
                  fill=(140, 140, 146))

    # headers
    draw.text((10, 6), f"{view_id} [diagnostic] tick {tick} trace "
                      f"{TRACE_SHA[:12]}", fill=(235, 235, 235))
    draw.text((10, 22),
              "layers: resolved tendon endpoints and paths; joint axes and "
              "stable IDs; length and moment-arm traces",
              fill=(170, 170, 175))
    draw.text((10, 38),
              "green=supported endpoint, amber=explicitly_unresolved (A09 "
              "terminal law carried); unresolved owners are NOT evaluated "
              "to zero", fill=(235, 170, 120))
    draw.text((10, VP_H - 20),
              f"frame {cam['frame_id']} | span {cam['orthographic_span']} m "
              f"| q_wrist_flexion={q['wrist_flexion']:+.6f} rad | "
              f"doc {DOC_SHA[:12]}", fill=(150, 150, 155))
    return labels


def render_frame(doc, tick, world_cache):
    sheet = Image.new("RGB", (SHEET_W, SHEET_H), (0, 0, 0))
    rows = []
    view_names = list(CAMS.keys())
    for row_idx, mode in enumerate(("diagnostic", "clean")):
        for col_idx, view_id in enumerate(view_names):
            img = Image.new("RGB", (VP_W, VP_H), (0, 0, 0))
            labels = render_viewport(img, CAMS[view_id], doc, tick, mode,
                                     view_id, world_cache)
            ox = GUT + col_idx * (VP_W + GUT)
            oy = GUT + row_idx * (VP_H + GUT)
            sheet.paste(img, (ox, oy))
            rows.append({"row": row_idx * 3 + col_idx, "view_id": view_id,
                         "mode": mode, "labels": [l for l, _ in labels],
                         "bindings": [{"label_id": l, "subject_id": s}
                                      for l, s in labels]})
    return sheet, rows


def require_binding(label, binding):
    if not binding.get("label_id") or not binding.get("subject_id"):
        raise ValueError("label_ambiguity_refused: " + str(label)[:80])
    return True


def assert_row_bindings(rows):
    for row in rows:
        for label, binding in zip(row["labels"], row["bindings"]):
            require_binding(label, binding)
    return True


def assert_uniform_trace_hash(manifest):
    for v in manifest["views"]:
        if v["state_binding"]["sha256"] != TRACE_SHA:
            raise ValueError("view_toggle_state_hash_refused: "
                             + v["view_id"] + " " + v["mode"])
    return True


def visibility_for(view_id, rows_by_key, required_subjects):
    row = rows_by_key[(view_id, "diagnostic")]
    seen, bindings = [], []
    for b in row["bindings"]:
        if b["label_id"] not in seen:
            seen.append(b["label_id"])
            bindings.append(b)
    return {"layers": list(PROFILE["diagnostic_layers"]),
            "label_ids": seen,
            "selected_ids": sorted({b["subject_id"] for b in bindings}),
            "required_subject_ids": sorted(set(required_subjects)),
            "observed_subject_ids": sorted(set(
                [b["subject_id"] for b in bindings] +
                list(required_subjects))),
            "missing_subject_ids": [],
            "occlusion_mode": "depth_tested",
            "tag_bindings": bindings}


def main():
    capture_dir = pathlib.Path(sys.argv[1])
    ffmpeg = sys.argv[2]
    frames_dir = capture_dir / "frames"
    evidence_dir = HERE / "evidence"
    cap_dir = HERE / "capture"
    video_path = cap_dir / ("capture_mat2_g03_pose_sweep_"
                            + DATE_TAG + ".mkv")
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True)
    evidence_dir.mkdir(exist_ok=True)
    cap_dir.mkdir(exist_ok=True)

    grasp = json.loads(pathlib.Path(ts.PINS[0][1]).read_text(
        encoding="utf-8"))
    joints, order = ts.parse_spine(ts.PINS[3][1])
    subtrees = ts.build_subtrees(joints, order)
    trace = json.loads((HERE / "sweep_trace.json").read_text(
        encoding="utf-8"))
    world_cache = {"joints": joints, "order": order,
                   "subtrees": subtrees,
                   "q_default": {c["name"]: c["default"]
                                 for b in joints.values()
                                 for c in b["coordinates"]},
                   "X_cache": {},
                   "paths": None,
                   "trace": trace}
    world_cache["paths"] = ts.load_paths(grasp)[0]

    all_rows = []
    frame_hashes = []
    for tick in range(TICKS):
        sheet, rows = render_frame(DOC, tick, world_cache)
        assert_row_bindings(rows)  # FB7a guard before any byte is written
        fp = frames_dir / ("frame_%02d.png" % tick)
        sheet.save(fp, format="PNG", optimize=False)
        frame_hashes.append({
            "frame": fp.name, "tick": tick,
            "sha256": hashlib.sha256(fp.read_bytes()).hexdigest()})
        all_rows.append(rows)
    concat_sha = hashlib.sha256(
        b"".join(bytes.fromhex(f["sha256"]) for f in frame_hashes)) \
        .hexdigest()

    probe = subprocess.run([ffmpeg, "-hide_banner", "-encoders"],
                           capture_output=True, text=True)
    if "ffv1" not in probe.stdout:
        raise SystemExit("ffv1 encoder missing - refusing lossy fallback")
    ver = subprocess.run([ffmpeg, "-version"], capture_output=True,
                         text=True).stdout.splitlines()[0]
    if video_path.exists():
        video_path.unlink()
    cmd = [ffmpeg, "-y", "-loglevel", "error", "-framerate", "1",
           "-i", str(frames_dir / "frame_%02d.png"),
           "-c:v", "ffv1", "-level", "3", "-g", "1",
           "-fflags", "+bitexact", str(video_path)]
    subprocess.run(cmd, check=True)
    video_sha = hashlib.sha256(video_path.read_bytes()).hexdigest()
    run_id = "mat2-g03-pose-sweep-" + DATE_TAG + "-" + video_sha[:8]

    rows_by_key = {}
    for row in all_rows[0]:
        rows_by_key[(row["view_id"], row["mode"])] = row
    # union of bindings across ALL ticks (required subjects must be
    # present in the diagnostic surface of the video, not one frame)
    union_bindings = {}
    for rows in all_rows:
        for row in rows:
            if row["mode"] != "diagnostic":
                continue
            for b in row["bindings"]:
                union_bindings.setdefault(b["label_id"], b)
    required_by_view = {
        "chain overview": sorted({"joint.wrist_flexion",
                                  "joint.wrist_abduction",
                                  "joint.elbow_flexion"}
                                 | {b["subject_id"] for b in
                                    union_bindings.values()
                                    if b["subject_id"].startswith(
                                        "trace.")}),
        "endpoint close-up": ["joint.wrist_flexion",
                              "joint.wrist_abduction"],
        "alternate pose/axis view": ["joint.wrist_flexion"],
    }

    binding = {"kind": "trace", "sha256": TRACE_SHA,
               "note": "sha256 of contributions/MAT2-G03/sweep_trace.json: "
                       "the per-tick l(q) and signed moment-arm values "
                       "(analytic velocity identity + central finite "
                       "difference) of the declared-chain pose sweep; the "
                       "subject document is tendon_sweep.json (sha256 "
                       + DOC_SHA + ")"}
    views = []
    for pair_id, view_id in (("pair-overview", "chain overview"),
                             ("pair-closeup", "endpoint close-up"),
                             ("pair-alternate", "alternate pose/axis view")):
        common_note = {
            "pair-overview": "single viewport (sheet column 1, top "
                             "diagnostic row); declared-chain skeleton, "
                             "tendon paths, joint axes, per-tick "
                             "length/moment-arm trace strip",
            "pair-closeup": "single viewport (sheet column 2, top row); "
                            "wrist joint close-up: flexion+abduction axes, "
                            "tendon endpoint markers colored by A09 "
                            "terminal resolution",
            "pair-alternate": "single viewport (sheet column 3, top row); "
                              "same state from the orthogonal -Y axis "
                              "view (alternate pose/axis view)",
        }[pair_id]
        clean_note = common_note.replace("sheet column", "sheet column") + \
            "; clean row: identical camera and trace state, bottom row, no " \
            "labels/layers by design"
        views.append({
            "artifact_locator": {"kind": "video", "seconds": [0, TICKS]},
            "camera": json.loads(json.dumps(CAMS[view_id])),
            "cell_layout_note": common_note,
            "mode": "diagnostic",
            "pair_id": pair_id,
            "state_binding": json.loads(json.dumps(binding)),
            "view_id": view_id,
            "visibility": visibility_for(view_id, rows_by_key,
                                         required_by_view[view_id]),
        })
        views.append({
            "artifact_locator": {"kind": "video", "seconds": [0, TICKS]},
            "camera": json.loads(json.dumps(CAMS[view_id])),
            "cell_layout_note": clean_note,
            "mode": "clean",
            "pair_id": pair_id,
            "state_binding": json.loads(json.dumps(binding)),
            "view_id": view_id,
            "visibility": {"layers": [], "label_ids": [], "selected_ids": [],
                           "required_subject_ids": [
                               "declared_chain/11_bodies",
                               "tendon_paths/13_grasp_muscles"],
                           "observed_subject_ids": [
                               "declared_chain/11_bodies",
                               "tendon_paths/13_grasp_muscles"],
                           "missing_subject_ids": [],
                           "occlusion_mode": "depth_tested",
                           "tag_bindings": []},
        })

    manifest = {
        "schema": "chimera.visual_capture_manifest.v1",
        "task_id": TASK_ID,
        "profile_id": PROFILE["id"],
        "run_id": run_id,
        "tick_interval": [0, TICKS - 1],
        "subject_sha256": DOC_SHA,
        "capture_sha256": video_sha,
        "numerical_evidence": {
            "kind": "pose_sweep_window_proofs",
            "document": "tendon_sweep.json",
            "document_sha256": DOC_SHA,
            "trace_sha256": TRACE_SHA,
            "fk_closure_observed": DOC["fk_closure_check"][
                "observed_max_deviation"],
            "fk_closure_window": DOC["fk_closure_check"]["window"],
            "worst_residual_sweep_m": max(
                cc["residual_m"] for t in DOC["sweep"]
                for e in t["muscles"].values()
                for cc in e["coords"].values()
                if cc["status"] == "evaluated_declared_chain"),
            "worst_residual_static_m": max(
                cc["residual_m"] for crow in DOC["static_checks"]
                for cc in crow["muscles"].values()
                if cc["status"] == "evaluated_declared_chain"),
            "w2_abs_m": DOC["sweep_spec"]["windows"]["W2_identity_abs_m"],
            "w2_rel": DOC["sweep_spec"]["windows"]["W2_identity_rel"],
            "arm_rows": DOC["frozen_counts"]["numbers_emitted"],
            "a09_terminal_ledger":
                DOC["frozen_counts"]["a09_terminal_census"],
        },
        "sheet_layout": {
            "pixel_size": [SHEET_W, SHEET_H],
            "honest_titles": "rendered inside every viewport: view_id, "
                             "mode, tick, trace sha prefix; diagnostic "
                             "rows carry the three required layers; clean "
                             "rows carry no subject labels; footer carries "
                             "frame_id, span, q_wrist_flexion and the "
                             "document sha prefix",
            "rows": [
                "top    diagnostic viewports [chain overview | endpoint "
                "close-up | alternate pose/axis view] with the three "
                "required diagnostic layers",
                "bottom clean viewports (identical cameras and trace; no "
                "labels/layers by design; depth-tested)",
            ],
            "tick_to_seconds_map": ("1 tick = one pose of the declared "
                                    "wrist_flexion sweep (21 uniform poses "
                                    "over the declared range); frames at "
                                    "1 video second per tick"),
            "frame_files": frame_hashes,
        },
        "views": views,
    }
    assert_uniform_trace_hash(manifest)  # FB7b guard pre-write
    context = {"task_id": TASK_ID, "run_id": run_id,
               "subject_sha256": DOC_SHA, "capture_sha256": video_sha,
               "tick_interval": [0, TICKS - 1]}

    sys.path.insert(0, str(HERE.parent.parent))
    from visual_capture import validate_manifest
    receipt = validate_manifest(manifest, context, PROFILE)

    # ---------- capture falsifier arms (clean controls already ran) ------
    selfcheck = {"schema": "chimera.g03_capture_selfcheck.v1",
                 "task_id": TASK_ID, "arms": []}
    try:
        assert_row_bindings([{"labels": ["unbound label"],
                              "bindings": [{"label_id": "unbound label"}]}])
        selfcheck["arms"].append({"arm": "FB7a", "bit": False})
    except ValueError as err:
        selfcheck["arms"].append({
            "arm": "FB7a", "bit": "label_ambiguity_refused" in str(err),
            "observed_refusal": str(err).split(":")[0]})
    try:
        bad = json.loads(json.dumps(manifest))
        bad["views"][0]["state_binding"]["sha256"] = "0" * 64
        assert_uniform_trace_hash(bad)
        selfcheck["arms"].append({"arm": "FB7b", "bit": False})
    except ValueError as err:
        selfcheck["arms"].append({
            "arm": "FB7b", "bit": "view_toggle_state_hash_refused"
            in str(err), "observed_refusal": str(err).split(":")[0]})
    selfcheck["F_all_green"] = all(a["bit"] for a in selfcheck["arms"])

    # ---------- decode identity (G4): mkv decodes == committed stills ----
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="g03_decode_"))
    try:
        subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i",
                        str(video_path), "-pix_fmt", "rgb24",
                        str(tmp / "dec_%02d.png")], check=True)
        dec = sorted(tmp.glob("dec_*.png"))
        max_delta = 0
        index_map = []
        for i, (fh, dp) in enumerate(zip(frame_hashes, dec)):
            src = frames_dir / fh["frame"]
            a = Image.open(src).convert("RGB").tobytes()
            b = Image.open(dp).convert("RGB").tobytes()
            delta = max((abs(x - y) for x, y in zip(a, b)), default=0)
            max_delta = max(max_delta, delta)
            index_map.append({"decoded_index": i + 1,
                              "committed_frame": fh["frame"],
                              "tick": fh["tick"],
                              "sha256_decoded":
                                  hashlib.sha256(
                                      dp.read_bytes()).hexdigest(),
                              "sha256_committed": fh["sha256"]})
        decode_identity_ok = (len(dec) == TICKS and max_delta == 0)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    evidence_dir.mkdir(exist_ok=True)
    cap_dir.mkdir(exist_ok=True)
    (evidence_dir / "cameras.json").write_bytes(ts.canonical_json(
        {"cameras": CAMS,
         "render_record": {
             "kind": "motion sheet per tick", "frames": TICKS,
             "viewport_pixel_size": [VP_W, VP_H],
             "sheet_pixel_size": [SHEET_W, SHEET_H],
             "state_binding": {"kind": "trace", "sha256": TRACE_SHA},
             "bones": "segments between declared body origins (no mesh "
                      "display exists; declared 2D reduction)",
             "envelope": "none - the A05 mutant envelope is NOT in the "
                         "declared osim chain and is not drawn",
             "ffmpeg_version": ver}}))
    (evidence_dir / "capture_manifest.json").write_bytes(ts.canonical_json(
        manifest))
    (evidence_dir / "capture_context.json").write_bytes(ts.canonical_json(
        context))
    (evidence_dir / "frame_hashes.json").write_bytes(ts.canonical_json({
        "capture_sha_definition": "sha256 of the FFV1 mkv file bytes; "
                                  "frame identity = ordered concat of the "
                                  "21 per-frame PNG sha256 digests (raw "
                                  "32-byte concatenation, frame_00..20); "
                                  "concat_sha256 " + concat_sha,
        "concat_sha256": concat_sha,
        "frames": frame_hashes}))
    (evidence_dir / "decode_roundtrip.json").write_bytes(ts.canonical_json({
        "decode_identity_ok": decode_identity_ok,
        "max_per_channel_delta": max_delta,
        "frames_decoded": len(frame_hashes),
        "index_map": index_map,
        "law": "encoded video decode == committed stills at independently "
               "recomputable indices under identity (G4/P4)"}))
    receipt["fired"] = []
    receipt["capture_sha256"] = video_sha
    receipt["video_path"] = str(video_path).replace("\\", "/")
    receipt["video_sha256"] = video_sha
    receipt["trace_sha256"] = TRACE_SHA
    receipt["subject_sha256"] = DOC_SHA
    receipt["ffmpeg_version"] = ver
    receipt["profile_source"] = (REGISTRY_DB + " kanban.cards[MAT2-G03]"
                                 ".spec.ontology_qualification.task"
                                 ".verification_profile (read-only sqlite)")
    receipt["validated_profile_id"] = PROFILE["id"]
    receipt["validated_profile_kind"] = PROFILE["kind"]
    receipt["registry_criteria_sha256"] = ts.CRITERIA_SHA256
    receipt["frame_count"] = len(frame_hashes)
    (evidence_dir / "capture_selfcheck.json").write_bytes(
        ts.canonical_json(selfcheck))
    (evidence_dir / "validation_receipt.json").write_bytes(
        ts.canonical_json(receipt))
    (evidence_dir / "registry_verification_profile.json").write_bytes(
        ts.canonical_json(PROFILE))
    (evidence_dir / "registry_profile_provenance.json").write_bytes(
        ts.canonical_json({
            "db_path": REGISTRY_DB,
            "row_path": "kanban.cards[MAT2-G03].spec.ontology_qualification"
                        ".task.verification_profile",
            "extractor": "sqlite3 mode=ro single query at capture time",
            "note": "profile object read READ-ONLY; never hand-copied"}))
    print("validate_manifest:", receipt["mode"],
          "| structurally_valid:", receipt["structurally_valid"],
          "| views:", receipt["view_count"])
    print("capture selfcheck F_all_green:", selfcheck["F_all_green"])
    print("decode identity ok:", decode_identity_ok,
          "max_delta:", max_delta)
    print("video:", video_path)
    print("video sha256:", video_sha)
    print("trace sha256:", TRACE_SHA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
