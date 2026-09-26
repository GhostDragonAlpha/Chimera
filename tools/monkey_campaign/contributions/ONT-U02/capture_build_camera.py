"""capture_build_camera.py -- ONT-U02 motion capture: trace -> video -> manifest.

Renders the frozen camera trace (evidence/trace.jsonl from
camera_profile_probe.py) into ONE deterministic video (three views x 391
ticks, 640x360, 20 fps, ffmpeg libx264 bitexact), then writes and VALIDATES
the chimera.visual_capture_manifest.v1 camera manifest with the campaign's
own validator (visual_capture.validate_manifest) and acceptance binding
(visual_gate.verify) against the card's frozen profile (card_task.json).

HONEST BOUNDARY (PREREGISTRATION): the pixels are a deterministic CPU
visualization of the recorded headless trace of the pinned camera subject
(the module is headless by construction); these are NOT native engine frames
and carry no V03/V08 native-rendering claim.

Views (frozen in PREREGISTRATION.md):
  1. "normal follow-camera distance"      -- the BASELINE camera (clean scene)
  2. "obstructed and close-target views"  -- the SUBJECT camera (declared
     obstacles: trunk + pole + curb; avoidance + close-target trunk framing)
  3. "repeatable inspection side view"    -- fixed bookmark (radius 14,
     theta pi/2, phi 0.3, target (3,0,-2), pinned engine eye law)

    python -B tools/monkey_campaign/contributions/ONT-U02/capture_build_camera.py
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"
SCRATCH = HERE.parent.parent.parent.parent.parent / "scratch" / "ont-u02-frames"

W, H = 640, 360
FPS = 20
FOV_DEG = 45.0
TAN_HALF = math.tan(math.radians(FOV_DEG) / 2.0)
NEAR, FAR = 0.1, 200.0
FRAME_ID = "monkey_u02_world_yup_m"

CAMPAIGN_TOOLS = Path("E:/PythonChimera/tools/monkey_campaign")

RUN_ID = "ont-u02-camera-20260926-2c724944"
SUBJECT_SHA256 = "d61347f085644e66a5f29ab1e689e2bbd2cd5ff04099856ade70e5da90a791a7"

VIEW_FOLLOW_NORMAL = "normal follow-camera distance"
VIEW_OSTRUCT = "obstructed and close-target views"
VIEW_INSPECT = "repeatable inspection side view"
LAYERS = ["input/state/tick display",
          "camera target and frustum diagnostics",
          "selected creature labels"]
LABELS = [("input_state_banner", "input_state"),
          ("tick_banner", "tick_state"),
          ("camera_diag", "camera_solution"),
          ("frustum_diag", "frustum_geometry"),
          ("creature_label", "monkey_body"),
          ("creature_heading", "monkey_body")]

FONT = ImageFont.load_default()
BG = (15, 17, 23)
GRID = (52, 58, 72)
GRID_MAJOR = (80, 88, 106)
MONKEY = (86, 214, 130)
MONKEY_FILL = (28, 60, 40)
HEADING = (240, 214, 96)
TRUNK_COL = (150, 108, 60)
POLE_COL = (120, 120, 140)
CURB_COL = (96, 110, 96)
TARGET_MARK = (255, 120, 120)
RAY_COL = (255, 160, 90)
TXT = (222, 228, 240)
TXT_DIM = (150, 158, 176)
LAYER_TAG = (120, 200, 255)
DEGRADED_COL = (255, 90, 90)

CYLINDERS = [
    ("trunk", 3.4, -5.0, 0.5, 8.0, TRUNK_COL),
    ("pole", 2.0, 0.2, 0.3, 6.0, POLE_COL),
    ("curb", 3.0, 0.1, 0.12, 0.15, CURB_COL),
]


def load_trace():
    raw = (EVIDENCE / "trace.jsonl").read_bytes()
    rows = [json.loads(l) for l in raw.decode("utf-8").splitlines() if l]
    return raw, rows


def basis(eye, target):
    f = [target[i] - eye[i] for i in range(3)]
    n = math.sqrt(sum(c * c for c in f))
    z = [c / n for c in f]
    up = (0.0, 1.0, 0.0)
    x = [up[1] * z[2] - up[2] * z[1],
         up[2] * z[0] - up[0] * z[2],
         up[0] * z[1] - up[1] * z[0]]
    nx = math.sqrt(sum(c * c for c in x))
    x = [c / nx for c in x]
    y = [z[1] * x[2] - z[2] * x[1],
         z[2] * x[0] - z[0] * x[2],
         z[0] * x[1] - z[1] * x[0]]
    return x, y, z


def project(point, eye, axes):
    p = [point[i] - eye[i] for i in range(3)]
    vx = sum(axes[0][i] * p[i] for i in range(3))
    vy = sum(axes[1][i] * p[i] for i in range(3))
    vz = sum(axes[2][i] * p[i] for i in range(3))
    if vz <= NEAR:
        return None
    px = (vx / vz) / (TAN_HALF * (W / H))
    py = (vy / vz) / TAN_HALF
    return ((px + 1.0) * 0.5 * W, (1.0 - py) * 0.5 * H)


def cam_dist(point, eye):
    return math.dist(point, eye)


def draw_segment(d, p0, p1, eye, axes, fill, width=1):
    a = project(p0, eye, axes)
    b = project(p1, eye, axes)
    if a is None or b is None:
        return
    d.line([a, b], fill=fill, width=width)


def draw_cylinder(d, cx, cz, r, top, col, eye, axes):
    """Filled silhouette of a vertical cylinder: convex hull of the projected
    top/bottom rim circles (12 points each), plus rim outlines."""
    top_pts, bot_pts = [], []
    for k in range(12):
        a = 2.0 * math.pi * k / 12.0
        pt = (cx + r * math.cos(a), 0.0, cz + r * math.sin(a))
        tp = project((cx + r * math.cos(a), top, cz + r * math.sin(a)),
                     eye, axes)
        bp = project(pt, eye, axes)
        if tp is None or bp is None:
            return
        top_pts.append(tp)
        bot_pts.append(bp)
    d.polygon(top_pts + bot_pts, fill=col, outline=tuple(min(255, c + 40)
                                                         for c in col))


def draw_scene(d, row, eye, axes, diagnostic):
    """Depth-ordered scene: grid, cylinders far-to-near, monkey body."""
    g0, g1, step = -10.0, 12.0, 1.0
    i = g0
    while i <= g1 + 1e-9:
        c = GRID_MAJOR if abs(i) < 1e-9 else GRID
        draw_segment(d, (i, 0.0, -8.0), (i, 0.0, 2.0), eye, axes, c)
        draw_segment(d, (-2.0, 0.0, i * 1.0 - 3.0), (10.0, 0.0, i * 1.0 - 3.0),
                     eye, axes, c)
        i += step
    cyls = [(name, cx, cz, r, top, col,
            math.dist((cx, 0.0, cz), eye)) for name, cx, cz, r, top, col
           in CYLINDERS]
    ax, ay, az = row["anchor"]
    monkey_d = math.dist((ax, 0.0, az), eye)
    for name, cx, cz, r, top, col, dist in sorted(cyls, key=lambda e: -e[6]):
        draw_cylinder(d, cx, cz, r, top, col, eye, axes)
        if diagnostic:
            bp = project((cx, 0.0, cz), eye, axes)
            tp = project((cx, top, cz), eye, axes)
            if bp and tp:
                d.line([bp, tp], fill=tuple(min(255, c + 60) for c in col),
                       width=1)
                d.text((bp[0] + 3, bp[1] - 6), name, fill=col, font=FONT)
        if dist > monkey_d:
            draw_monkey(d, row, eye, axes, diagnostic)
    draw_monkey(d, row, eye, axes, diagnostic)


def draw_monkey(d, row, eye, axes, diagnostic):
    ax, ay, az = row["anchor"]
    r = 0.5
    pts = []
    for k in range(16):
        a = 2.0 * math.pi * k / 16.0
        q = project((ax + r * math.cos(a), 0.0, az + r * math.sin(a)),
                    eye, axes)
        if q is None:
            return
        pts.append(q)
    d.polygon(pts, fill=MONKEY_FILL, outline=MONKEY)
    base = project((ax, 0.0, az), eye, axes)
    top = project((ax, 1.0, az), eye, axes)
    if base and top:
        d.line([base, top], fill=MONKEY, width=3)
    hd = math.radians(row["yaw_deg"])
    tip = project((ax + 1.2 * math.sin(hd), 0.05, az + 1.2 * math.cos(hd)),
                  eye, axes)
    if base and tip:
        d.line([base, tip], fill=HEADING, width=2)
    if diagnostic:
        lbl = project((ax, 1.5, az), eye, axes)
        if lbl:
            d.text((lbl[0] + 4, lbl[1]), "monkey-01", fill=MONKEY, font=FONT)


def draw_aim(d, row, which, eye, axes):
    """Layer 2 scene parts: the aim target marker + the view axis ray."""
    src = row[which]
    tgt = tuple(src["target"])
    mark = project(tgt, eye, axes)
    if mark:
        d.ellipse([mark[0] - 4, mark[1] - 4, mark[0] + 4, mark[1] + 4],
                  outline=TARGET_MARK, width=2)
    draw_segment(d, eye, tgt, eye, axes, RAY_COL, 1)


def draw_diagnostics(d, row, view_name):
    """The three declared diagnostic layers, each tagged with its name."""
    x0, y0 = 6, 6
    s = row["subject"]
    # L1 input/state/tick display
    d.rectangle([x0 - 2, y0 - 2, x0 + 300, y0 + 44], fill=(0, 0, 0))
    d.text((x0, y0), "L1 input/state/tick display", fill=LAYER_TAG, font=FONT)
    d.text((x0, y0 + 12),
           "tick=%d t=%dms held=%s focus=%s recs=%d mode=%s"
           % (row["tick"], row["t_ms"], ",".join(row["held"]) or "-",
              row["focus_state"], len(row["records"]), row["mode"]),
           fill=TXT, font=FONT)
    y0 += 50
    # L2 camera target and frustum diagnostics
    d.rectangle([x0 - 2, y0 - 2, x0 + 340, y0 + 56], fill=(0, 0, 0))
    d.text((x0, y0), "L2 camera target and frustum diagnostics",
           fill=LAYER_TAG, font=FONT)
    v = s["applied_v"]
    d.text((x0, y0 + 12),
           "R=%.3f th=%+.3f ph=%+.3f tgt=(%.2f,%.2f,%.2f) d=%.2f%s"
           % (v[0], v[1], v[2], v[3], v[4], v[5], s["distance_to_target"],
              " DEGRADED" if s["degraded"] else ""),
           fill=DEGRADED_COL if s["degraded"] else TXT, font=FONT)
    d.text((x0, y0 + 24),
           "avoid=%s sub=%.1fdeg subG=%.1fdeg subC=%.1fdeg yaw=%+.1fdeg"
           % (",".join(s["avoidance_order"]) or "-"[:1] or "-",
              s["subtend_anchor_deg"], s["subtend_ground_ahead_deg"],
              s["subtend_contact_deg"], row["yaw_deg"]),
           fill=TXT_DIM, font=FONT)
    y0 += 62
    # L3 selected creature labels
    d.rectangle([x0 - 2, y0 - 2, x0 + 300, y0 + 44], fill=(0, 0, 0))
    d.text((x0, y0), "L3 selected creature labels", fill=LAYER_TAG, font=FONT)
    d.text((x0, y0 + 12),
           "monkey-01 anchor=(%.2f,%.2f) v_animal=%.3f m/s cut=%s"
           % (row["anchor"][0], row["anchor"][2], row["v_animal"],
              row["cut"]),
           fill=TXT, font=FONT)


def render_view_frame(d, row, view_name):
    diagnostic = True
    if view_name == VIEW_INSPECT:
        eye = tuple(row["inspection"]["position"])
        tgt = tuple(row["inspection"]["target"])
        axes = basis(eye, tgt)
    else:
        src = row["baseline" if view_name == VIEW_FOLLOW_NORMAL else "subject"]
        eye = tuple(src["position"])
        tgt = tuple(src["target"])
        axes = basis(eye, tgt)
    draw_scene(d, row, eye, axes, diagnostic)
    if view_name != VIEW_INSPECT:
        draw_aim(d, row, "baseline" if view_name == VIEW_FOLLOW_NORMAL
                 else "subject", eye, axes)
    draw_diagnostics(d, row, view_name)


def render_view_frame_clean(d, row, view_name):
    if view_name == VIEW_INSPECT:
        eye = tuple(row["inspection"]["position"])
        tgt = tuple(row["inspection"]["target"])
    else:
        src = row["baseline" if view_name == VIEW_FOLLOW_NORMAL else "subject"]
        eye = tuple(src["position"])
        tgt = tuple(src["target"])
    axes = basis(eye, tgt)
    draw_scene(d, row, eye, axes, False)


def build_video(frame_dir, n_frames, dst):
    if dst.exists():
        dst.unlink()
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "image2", "-framerate", str(FPS),
           "-i", str(frame_dir / "f%04d.png"),
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23",
           "-preset", "medium", "-flags", "+bitexact", "-fflags", "+bitexact",
           "-x264-params", "threads=1:ref=4",
           str(dst)]
    subprocess.run(cmd, check=True)
    return dst


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def camera_block(sample_mode, samples, interpolation=None):
    cam = {
        "frame_id": FRAME_ID,
        "coordinate_unit": "m",
        "handedness": "right",
        "orientation_convention": "quaternion_wxyz_camera_to_frame",
        "forward_axis": "+Z",
        "up_axis": "+Y",
        "near_far_planes": [NEAR, FAR],
        "viewport_resolution": [W, H],
        "aspect_ratio": W / H,
        "projection": "perspective",
        "vertical_fov_degrees": FOV_DEG,
        "sample_mode": sample_mode,
        "samples": samples,
    }
    if interpolation is not None:
        cam["interpolation"] = interpolation
    return cam


def sample_from(src, tick):
    return {"tick": tick,
            "position": list(src["position"]),
            "target": list(src["target"]),
            "distance_to_target": src["distance_to_target"],
            "orientation": list(src["orientation"])}


def visibility_block(mode):
    if mode == "diagnostic":
        return {
            "layers": list(LAYERS),
            "label_ids": [l for l, _ in LABELS],
            "selected_ids": ["monkey_body"],
            "required_subject_ids": ["monkey_body"],
            "observed_subject_ids": ["monkey_body", "ground_grid",
                                     "trunk_geometry", "pole_geometry",
                                     "curb_geometry", "input_state",
                                     "tick_state", "camera_solution",
                                     "frustum_geometry"],
            "missing_subject_ids": [],
            "occlusion_mode": "mixed",
            "tag_bindings": [{"label_id": l, "subject_id": s}
                             for l, s in LABELS],
        }
    return {
        "layers": [],
        "label_ids": [],
        "selected_ids": [],
        "required_subject_ids": ["ground_grid"],
        "observed_subject_ids": ["ground_grid", "trunk_geometry",
                                 "pole_geometry", "curb_geometry"],
        "missing_subject_ids": [],
        "occlusion_mode": "depth_tested",
        "tag_bindings": [],
    }


def main():
    trace_bytes, rows = load_trace()
    trace_sha = hashlib.sha256(trace_bytes).hexdigest()
    n = len(rows)
    t0, t1 = rows[0]["tick"], rows[-1]["tick"]
    duration = (6 * n) / FPS

    SCRATCH.mkdir(parents=True, exist_ok=True)
    for old in SCRATCH.glob("f*.png"):
        old.unlink()
    idx = 0
    for view, render in ((VIEW_FOLLOW_NORMAL, render_view_frame),
                         (VIEW_OSTRUCT, render_view_frame),
                         (VIEW_INSPECT, render_view_frame)):
        for row in rows:
            img = Image.new("RGB", (W, H), BG)
            d = ImageDraw.Draw(img)
            render(d, row, view)
            img.save(SCRATCH / ("f%04d.png" % idx))
            idx += 1
            img = Image.new("RGB", (W, H), BG)
            d = ImageDraw.Draw(img)
            render_view_frame_clean(d, row, view)
            img.save(SCRATCH / ("f%04d.png" % idx))
            idx += 1
    total = idx
    video = EVIDENCE / "capture.mp4"
    build_video(SCRATCH, total, video)
    capture_sha = sha256_file(video)
    shutil.rmtree(SCRATCH, ignore_errors=True)

    # seconds: the six back-to-back view segments (diagnostic+clean per view)
    seg = n / FPS
    seconds = {VIEW_FOLLOW_NORMAL: [0.0, 2 * seg],
               VIEW_OSTRUCT: [2 * seg, 4 * seg],
               VIEW_INSPECT: [4 * seg, 6 * seg]}
    follow_samples = [sample_from(r["baseline"], r["tick"]) for r in rows]
    obst_samples = [sample_from(r["subject"], r["tick"]) for r in rows]
    inspect_samples = [sample_from(r["inspection"], r["tick"]) for r in rows]
    follow_cam = camera_block("sampled_trajectory", follow_samples,
                              interpolation="recorded_each_tick")
    obst_cam = camera_block("sampled_trajectory", obst_samples,
                            interpolation="recorded_each_tick")
    inspect_cam = camera_block("fixed_bookmark", inspect_samples)

    def row_entry(view_id, mode, pair_id, cam):
        return {"view_id": view_id, "mode": mode, "pair_id": pair_id,
                "state_binding": {"kind": "trace", "sha256": trace_sha},
                "artifact_locator": {"kind": "video",
                                     "seconds": list(seconds[view_id])},
                "camera": cam,
                "visibility": visibility_block(mode)}

    manifest = {
        "schema": "chimera.visual_capture_manifest.v1",
        "task_id": "U02",
        "run_id": RUN_ID,
        "subject_sha256": SUBJECT_SHA256,
        "capture_sha256": capture_sha,
        "profile_id": "controls",
        "tick_interval": [t0, t1],
        "views": [
            row_entry(VIEW_FOLLOW_NORMAL, "diagnostic", VIEW_FOLLOW_NORMAL,
                      follow_cam),
            row_entry(VIEW_FOLLOW_NORMAL, "clean", VIEW_FOLLOW_NORMAL,
                      follow_cam),
            row_entry(VIEW_OSTRUCT, "diagnostic", VIEW_OSTRUCT, obst_cam),
            row_entry(VIEW_OSTRUCT, "clean", VIEW_OSTRUCT, obst_cam),
            row_entry(VIEW_INSPECT, "diagnostic", VIEW_INSPECT, inspect_cam),
            row_entry(VIEW_INSPECT, "clean", VIEW_INSPECT, inspect_cam),
        ],
    }
    manifest_path = EVIDENCE / "capture_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=1, sort_keys=True)
                             + "\n", encoding="utf-8")

    # validation with the campaign's own gate (read-only import)
    sys.path.insert(0, str(CAMPAIGN_TOOLS))
    sys.dont_write_bytecode = True
    for stale in [k for k in sys.modules if k in ("visual_gate",
                                                  "visual_capture",
                                                  "integrity")]:
        del sys.modules[stale]
    import visual_gate                                    # noqa: E402
    contract = json.loads((HERE / "card_task.json").read_text(encoding="utf-8"))
    receipt = {
        "evidence": {
            "camera": {"reference": str(manifest_path.resolve()),
                       "raw_sha256": sha256_file(manifest_path)},
            "visual": {"reference": str(video.resolve()),
                       "raw_sha256": capture_sha},
        },
        "capture_context": {
            "task_id": "U02",
            "subject_sha256": SUBJECT_SHA256,
            "run_id": RUN_ID,
            "capture_sha256": capture_sha,
            "tick_interval": [t0, t1],
        },
    }
    structural = visual_gate.verify(receipt, contract)

    capture_receipt = {
        "schema": "ont-u02.camera.capture.v1",
        "task_id": "U02",
        "run_id": RUN_ID,
        "subject_sha256": SUBJECT_SHA256,
        "honest_boundary": "Deterministic CPU visualization of the recorded "
                           "headless trace of the pinned camera subject "
                           "(trace.jsonl); NOT native engine frames; the "
                           "native integrated checkpoints (V03/V08) stay "
                           "with the integration lane.",
        "video": {"reference": str(video.resolve()),
                  "raw_sha256": capture_sha,
                  "bytes": video.stat().st_size,
                  "resolution": [W, H], "fps": FPS,
                  "frames": total, "duration_s": duration},
        "state_binding": {"kind": "trace", "raw_sha256": trace_sha,
                          "rows": n, "tick_interval": [t0, t1]},
        "manifest": {"reference": str(manifest_path.resolve()),
                     "raw_sha256": sha256_file(manifest_path)},
        "frame_map": {"diagnostic+clean interleaved per view": True,
                      "view_order": [VIEW_FOLLOW_NORMAL, VIEW_OSTRUCT,
                                     VIEW_INSPECT],
                      "frames_per_view": 2 * n,
                      "frame_index": "diagnostic and clean alternate per tick "
                                     "within each view segment"},
        "views": {
            VIEW_FOLLOW_NORMAL: {
                "seconds": seconds[VIEW_FOLLOW_NORMAL],
                "camera": "sampled_trajectory recorded_each_tick: the "
                          "BASELINE pinned FollowCamera (no obstacles) "
                          "applied solution per tick",
                "role": "normal follow-camera distance law; motion on "
                        "ground visible"},
            VIEW_OSTRUCT: {
                "seconds": seconds[VIEW_OSTRUCT],
                "camera": "sampled_trajectory recorded_each_tick: the "
                          "SUBJECT pinned FollowCamera (trunk+pole+curb) "
                          "applied solution per tick",
                "role": "obstruction avoidance episode + trunk-mode "
                        "close-target framing; degradation flag visible in "
                        "diagnostic rows"},
            VIEW_INSPECT: {
                "seconds": seconds[VIEW_INSPECT],
                "camera": "fixed_bookmark (radius 14, theta pi/2, phi 0.3, "
                          "target (3,0,-2)), pinned engine eye law",
                "role": "repeatable deterministic inspection side view"},
        },
        "render_referents": {
            "projection": "perspective 45 deg vertical FOV (tan_half "
                          "0.41421356), principal point centered",
            "frame": FRAME_ID + " (right-handed, Y-up, metres)",
            "cylinders": "projected rim-circle silhouettes (12-point hull); "
                         "clean rows draw scene only, depth-ordered",
            "source_module": "tools/monkey_campaign/product/follow_camera.py "
                             "@ f30f2224 (sha d61347f0)",
        },
        "gate_validation": structural,
    }
    (EVIDENCE / "capture_receipt.json").write_text(
        json.dumps(capture_receipt, indent=1, sort_keys=True) + "\n",
        encoding="utf-8")
    print("frames:", total, "video bytes:", video.stat().st_size)
    print("capture_sha256:", capture_sha)
    print("gate:", json.dumps(structural))
    print("RESULT:", "CAPTURE BUILT AND GATE-VALID"
          if structural.get("structurally_valid") else "GATE REJECTED")
    return 0 if structural.get("structurally_valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())
