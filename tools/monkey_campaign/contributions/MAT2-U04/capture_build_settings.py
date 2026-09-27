"""capture_build_settings.py -- MAT2-U04 motion capture: trace -> video -> manifest.

Renders the frozen input-settings trace (evidence/trace.jsonl from
input_settings_probe.py) into ONE deterministic video (three profile views x
diagnostic+clean segments, 391 ticks each, 640x360, 20 fps, ffmpeg libx264
bitexact), then writes and VALIDATES the chimera.visual_capture_manifest.v1
camera manifest with the campaign's own validator
(visual_capture.validate_manifest) and acceptance binding (visual_gate.verify)
against the card's frozen contract (card_task.json).

HONEST BOUNDARY (PREREGISTRATION): the pixels are a deterministic CPU
visualization of the recorded headless trace of the pinned settings subject
(the module is headless by construction); the body is the harness's declared
integration of the real emitted CommandRecords. These are NOT native engine
frames and carry no native-rendering claim.

Views (frozen in PREREGISTRATION.md):
  1. "normal follow-camera distance"      -- follow cam 3.0 m behind, 1.4 m up
  2. "obstructed and close-target views"  -- close cam 1.7 m behind in the
     declared obstacle scene (trunk/pole/curb, depth-tested dressing only)
  3. "repeatable inspection side view"    -- fixed bookmark: target trunk
     (3.4, 0.5, -5.0), eye 14.0 m away at elevation 0.3 rad

    python -B tools/monkey_campaign/contributions/MAT2-U04/capture_build_settings.py
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"
SCRATCH = HERE.parents[3] / "scratch" / "mat2-u04-frames"

W, H = 640, 360
FPS = 20
FOV_DEG = 45.0
TAN_HALF = math.tan(math.radians(FOV_DEG) / 2.0)
TAN_HALF_H = TAN_HALF * (W / H)
NEAR, FAR = 0.1, 200.0
FRAME_ID = "monkey_u04_world_yup_m"

CAMPAIGN_TOOLS = Path("E:/PythonChimera/tools/monkey_campaign")

RUN_ID = "mat2-u04-input-20260927-d9ce4334"
SUBJECT_SHA256 = "8d1a49d63f85164f3b9ac27f3387237d0a0790f68075e2455a74e2caa485a2f1"
TASK_ID = "U04"
CARD_ID = "MAT2-U04"
ATTEMPT_ID = "d9ce4334674e435d95b9cb95373327e5"
AGENT_ID = "arrival-1390bce44d204c709636097a9613e84f"

VIEW_FOLLOW = "normal follow-camera distance"
VIEW_CLOSE = "obstructed and close-target views"
VIEW_INSPECT = "repeatable inspection side view"
VIEWS = [VIEW_FOLLOW, VIEW_CLOSE, VIEW_INSPECT]
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

CYLINDERS = [
    ("trunk", 3.4, -5.0, 0.5, 8.0, TRUNK_COL),
    ("pole", 2.0, 0.2, 0.3, 6.0, POLE_COL),
    ("curb", 3.0, 0.1, 0.12, 0.15, CURB_COL),
]

SEGMENT_S = 391 / FPS          # 19.55 s per (view, mode) segment


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
    px = (vx / vz) / (TAN_HALF_H)
    py = (vy / vz) / TAN_HALF
    return ((px + 1.0) * 0.5 * W, (1.0 - py) * 0.5 * H)


def quat_wxyz_camera_to_frame(eye, target):
    """Unit quaternion (w,x,y,z), camera->frame; camera-local +Z forward,
    +Y up, +X right, right-handed; frame is the Y-up metre world.
    Unit-tested: rotating (0,0,1) lands on the eye->target unit forward,
    (1,0,0) on the camera right axis, (0,1,0) on camera up."""
    f = tuple(target[i] - eye[i] for i in range(3))
    n = math.sqrt(sum(c * c for c in f))
    z = tuple(c / n for c in f)
    up_world = (0.0, 1.0, 0.0)
    x = (up_world[1] * z[2] - up_world[2] * z[1],
         up_world[2] * z[0] - up_world[0] * z[2],
         up_world[0] * z[1] - up_world[1] * z[0])
    nx = math.sqrt(sum(c * c for c in x))
    x = tuple(c / nx for c in x)
    y = (z[1] * x[2] - z[2] * x[1],
         z[2] * x[0] - z[0] * x[2],
         z[0] * x[1] - z[1] * x[0])
    # rotation matrix whose COLUMNS are the camera axes in the frame
    m00, m01, m02 = x[0], y[0], z[0]
    m10, m11, m12 = x[1], y[1], z[1]
    m20, m21, m22 = x[2], y[2], z[2]
    tr = m00 + m11 + m22
    if tr > 0.0:
        s = math.sqrt(tr + 1.0) * 2.0
        w = 0.25 * s
        cx = (m21 - m12) / s
        cy = (m02 - m20) / s
        cz = (m10 - m01) / s
    elif m00 > m11 and m00 > m22:
        s = math.sqrt(1.0 + m00 - m11 - m22) * 2.0
        w = (m21 - m12) / s
        cx = 0.25 * s
        cy = (m01 + m10) / s
        cz = (m02 - m20) / s
    elif m11 > m22:
        s = math.sqrt(1.0 + m11 - m00 - m22) * 2.0
        w = (m02 - m20) / s
        cx = (m01 + m10) / s
        cy = 0.25 * s
        cz = (m12 + m21) / s
    else:
        s = math.sqrt(1.0 + m22 - m00 - m11) * 2.0
        w = (m10 - m01) / s
        cx = (m02 + m20) / s
        cy = (m12 + m21) / s
        cz = 0.25 * s
    return (w, cx, cy, cz)


def camera_solutions(row):
    """The three frozen view solutions for one trace row (PREREGISTRATION)."""
    b = row["body"]
    pos = (b["x"], b["y"], b["z"])
    h = b["heading"]
    ch, sh = math.cos(h), math.sin(h)
    follow_eye = (pos[0] - ch * 3.0, 1.4, pos[2] - sh * 3.0)
    follow_tgt = (pos[0], 0.5, pos[2])
    close_eye = (pos[0] - ch * 1.7, 0.95, pos[2] - sh * 1.7)
    close_tgt = (pos[0] + ch * 0.6, 0.1, pos[2] + sh * 0.6)
    insp_tgt = (3.4, 0.5, -5.0)
    insp_eye = (insp_tgt[0] + 14.0 * math.cos(0.3),
                insp_tgt[1] + 14.0 * math.sin(0.3), insp_tgt[2])
    return {VIEW_FOLLOW: (follow_eye, follow_tgt),
            VIEW_CLOSE: (close_eye, close_tgt),
            VIEW_INSPECT: (insp_eye, insp_tgt)}


def camera_block(sample_mode, samples, interpolation=None):
    cam = {"frame_id": FRAME_ID, "coordinate_unit": "m", "handedness": "right",
           "orientation_convention": "quaternion_wxyz_camera_to_frame",
           "forward_axis": "+Z", "up_axis": "+Y",
           "near_far_planes": [NEAR, FAR], "viewport_resolution": [W, H],
           "aspect_ratio": W / H, "projection": "perspective",
           "vertical_fov_degrees": FOV_DEG, "sample_mode": sample_mode,
           "samples": samples}
    if interpolation is not None:
        cam["interpolation"] = interpolation
    return cam


def visibility_block(mode):
    if mode == "clean":
        return {"layers": [], "label_ids": [], "selected_ids": [],
                "required_subject_ids": ["monkey_body"],
                "observed_subject_ids": ["monkey_body", "ground_grid",
                                         "trunk_geometry", "pole_geometry",
                                         "curb_geometry"],
                "missing_subject_ids": [], "occlusion_mode": "depth_tested",
                "tag_bindings": []}
    return {"layers": list(LAYERS),
            "label_ids": [l[0] for l in LABELS],
            "selected_ids": ["monkey_body"],
            "required_subject_ids": ["monkey_body"],
            "observed_subject_ids": ["monkey_body", "ground_grid",
                                     "trunk_geometry", "pole_geometry",
                                     "curb_geometry", "input_state",
                                     "tick_state", "camera_solution",
                                     "frustum_geometry"],
            "missing_subject_ids": [], "occlusion_mode": "mixed",
            "tag_bindings": [{"label_id": l, "subject_id": s}
                             for l, s in LABELS]}


def draw_grid(d, eye, axes):
    for i in range(-12, 13):
        col = GRID_MAJOR if i % 5 == 0 else GRID
        a = project((i, 0.0, -12.0), eye, axes)
        b = project((i, 0.0, 12.0), eye, axes)
        if a and b:
            d.line([a, b], fill=col, width=1)
        a = project((-12.0, 0.0, i), eye, axes)
        b = project((12.0, 0.0, i), eye, axes)
        if a and b:
            d.line([a, b], fill=col, width=1)


def draw_cylinders(d, eye, axes, row):
    depth = lambda cx, cz: math.dist(eye, (cx, 0.0, cz))
    body_d = math.dist(eye, (row["body"]["x"], 0.0, row["body"]["z"]))
    items = sorted(CYLINDERS, key=lambda c: depth(c[1], c[2]), reverse=True)
    drew_body = False
    for name, cx, cz, r, top, col in items:
        if depth(cx, cz) > body_d and not drew_body:
            draw_body(d, eye, axes, row)
            drew_body = True
        base = project((cx, 0.0, cz), eye, axes)
        top_p = project((cx, top, cz), eye, axes)
        left = project((cx - r, 0.0, cz), eye, axes)
        right = project((cx + r, 0.0, cz), eye, axes)
        if base and top_p and left and right:
            wdt = min(max(2.0, abs(right[0] - left[0])), 4.0 * W)
            x0, x1 = base[0] - wdt / 2, base[0] + wdt / 2
            y0, y1 = min(top_p[1], base[1]), max(top_p[1], base[1])
            if x1 > x0 and y1 > y0:
                d.rectangle([x0, y0, x1, y1], fill=col)
    if not drew_body:
        draw_body(d, eye, axes, row)


def draw_body(d, eye, axes, row):
    b = row["body"]
    pos = (b["x"], b["y"], b["z"])
    h = b["heading"]
    p = project(pos, eye, axes)
    if p:
        d.ellipse([p[0] - 7, p[1] - 7, p[0] + 7, p[1] + 7],
                  fill=MONKEY_FILL, outline=MONKEY, width=2)
    ahead = project((pos[0] + math.cos(h) * 0.7, 0.1,
                     pos[2] + math.sin(h) * 0.7), eye, axes)
    if p and ahead:
        d.line([p, ahead], fill=HEADING, width=3)


def draw_diagnostics(d, eye, target, axes, row, solution):
    t = project(target, eye, axes)
    if t:
        d.line([t[0] - 8, t[1], t[0] + 8, t[1]], fill=TARGET_MARK, width=1)
        d.line([t[0], t[1] - 8, t[0], t[1] + 8], fill=TARGET_MARK, width=1)
    dist = math.dist(eye, target)
    for sx in (-1, 1):
        for sy in (-1, 1):
            corner_cam = (sx * TAN_HALF_H * dist, sy * TAN_HALF * dist, dist)
            world = tuple(eye[i] + axes[0][i] * corner_cam[0]
                          + axes[1][i] * corner_cam[1]
                          + axes[2][i] * corner_cam[2] for i in range(3))
            p = project(world, eye, axes)
            if t and p:
                d.line([t, p], fill=RAY_COL, width=1)
    e = project(eye, eye, axes)  # never visible; marker at frame edge instead
    d.text((8, H - 14), "camera_solution eye=(%.3f, %.3f, %.3f) d=%.3f"
           % (eye[0], eye[1], eye[2], dist), fill=TXT_DIM, font=FONT)


def draw_banner(d, row, view_name, mode):
    st = row["settings"]
    lines = [
        "MAT2-U04 input settings  U04  %s  [%s]" % (RUN_ID, view_name),
        "tick %d  t=%dms  phase=%s  mode=%s" % (row["tick"], row["t_ms"],
                                                row["phase"], mode),
        "settings: sensitivity=%r invert_yaw=%r" % (st["sensitivity"],
                                                    st["invert_yaw"]),
        "bindings sha256: %s" % st["bindings_sha256"][:16],
        "events: %s" % (row["events"] or "-"),
        "keys held: %s" % (",".join(row["keys_held"]) or "-"),
        "records: %s" % (row["records"] or "-"),
        "refusals: %s" % (row["refusals"] or "-"),
    ]
    y = 6
    for i, line in enumerate(lines):
        d.text((8, y + i * 12), line, fill=TXT if i else LAYER_TAG, font=FONT)
    for i, layer in enumerate(LAYERS):
        d.text((W - 210, 6 + i * 12), "[L] %s" % layer, fill=LAYER_TAG, font=FONT)
    b = row["body"]
    d.text((8, 110), "body: x=%.3f z=%.3f heading=%.3f" % (b["x"], b["z"],
                                                           b["heading"]),
           fill=TXT_DIM, font=FONT)
    d.text((8, 122), "labels: monkey_body@body_heading-arrow", fill=TXT_DIM,
           font=FONT)
    p_body = None  # labels are drawn at the body in draw_body callers
    return p_body


def draw_label(d, eye, axes, row):
    b = row["body"]
    p = project((b["x"], 0.9, b["z"]), eye, axes)
    if p:
        d.text((p[0] + 9, p[1] - 6), "monkey_body", fill=MONKEY, font=FONT)


def render_frame(row, view_name, mode, out_path):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    solution = camera_solutions(row)
    eye, target = solution[view_name]
    axes = basis(eye, target)
    draw_grid(d, eye, axes)
    draw_cylinders(d, eye, axes, row)
    if mode == "diagnostic":
        draw_diagnostics(d, eye, target, axes, row, solution)
        draw_banner(d, row, view_name, mode)
        draw_label(d, eye, axes, row)
    img.save(out_path, format="PNG")


def build_video(frame_dir: Path, n_frames: int, dst: Path):
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


def build_once(raw_trace, rows, frame_dir: Path, dst: Path):
    if frame_dir.exists():
        shutil.rmtree(frame_dir)
    frame_dir.mkdir(parents=True)
    idx = 0
    for view_name in VIEWS:
        for mode in ("diagnostic", "clean"):
            for row in rows:
                render_frame(row, view_name, mode,
                             frame_dir / ("f%04d.png" % idx))
                idx += 1
    build_video(frame_dir, idx, dst)
    return idx


def main():
    started = time.monotonic()
    raw_trace, rows = load_trace()
    trace_sha = hashlib.sha256(raw_trace).hexdigest()
    assert len(rows) == 391, "trace rows %d" % len(rows)
    EVIDENCE.mkdir(exist_ok=True)

    print("building capture A ...")
    n_a = build_once(raw_trace, rows, SCRATCH / "a", SCRATCH / "capture_a.mp4")
    print("building capture B (bitexact proof) ...")
    n_b = build_once(raw_trace, rows, SCRATCH / "b", SCRATCH / "capture_b.mp4")
    hash_a = sha256_file(SCRATCH / "capture_a.mp4")
    hash_b = sha256_file(SCRATCH / "capture_b.mp4")
    bitexact = hash_a == hash_b
    print("frames:", n_a, n_b, "| bitexact:", bitexact)
    if not bitexact:
        raise SystemExit("CAPTURE NOT BITEXACT")

    shutil.copyfile(SCRATCH / "capture_a.mp4", EVIDENCE / "capture.mp4")
    capture_sha = sha256_file(EVIDENCE / "capture.mp4")

    samples_by_view = {}
    for view_name in VIEWS:
        samples = []
        for row in rows:
            eye, target = camera_solutions(row)[view_name]
            samples.append({
                "tick": row["tick"], "position": list(eye),
                "target": list(target),
                "distance_to_target": math.dist(eye, target),
                "orientation": list(quat_wxyz_camera_to_frame(eye, target))})
        samples_by_view[view_name] = samples

    views = []
    for i, view_name in enumerate(VIEWS):
        sample_mode = ("fixed_bookmark" if view_name == VIEW_INSPECT
                       else "sampled_trajectory")
        interpolation = (None if sample_mode == "fixed_bookmark"
                         else "recorded_each_tick")
        base_s = i * 2 * SEGMENT_S
        for mode in ("diagnostic", "clean"):
            s0 = base_s + (0 if mode == "diagnostic" else SEGMENT_S)
            views.append({
                "view_id": view_name, "mode": mode, "pair_id": view_name,
                "state_binding": {"kind": "trace", "sha256": trace_sha},
                "artifact_locator": {"kind": "video",
                                     "seconds": [s0, s0 + SEGMENT_S]},
                "camera": camera_block(sample_mode,
                                       samples_by_view[view_name],
                                       interpolation),
                "visibility": visibility_block(mode)})
    manifest = {
        "schema": "chimera.visual_capture_manifest.v1",
        "task_id": TASK_ID, "run_id": RUN_ID, "profile_id": "controls",
        "subject_sha256": SUBJECT_SHA256, "capture_sha256": capture_sha,
        "tick_interval": [rows[0]["tick"], rows[-1]["tick"]],
        "views": views}
    manifest_path = EVIDENCE / "capture_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=1, sort_keys=True)
                             + "\n", encoding="utf-8")

    # ── campaign's own structural gate + acceptance binding ─────────────────
    for stale in [k for k in sys.modules if k in ("visual_gate",
                                                  "visual_capture")]:
        del sys.modules[stale]
    sys.path.insert(0, str(CAMPAIGN_TOOLS))
    import visual_capture                                     # noqa: E402
    import visual_gate                                        # noqa: E402
    context = {"task_id": TASK_ID, "subject_sha256": SUBJECT_SHA256,
               "run_id": RUN_ID, "capture_sha256": capture_sha,
               "tick_interval": manifest["tick_interval"]}
    profile = manifest_profile = json.loads(
        (HERE / "card_task.json").read_text(encoding="utf-8"))
    structural = visual_capture.validate_manifest(manifest, context,
                                                  profile["task"]["verification_profile"])
    print("structural:", structural)
    receipt = {"evidence": {
        "camera": {"reference": str(manifest_path.resolve()),
                   "raw_sha256": sha256_file(manifest_path)},
        "visual": {"reference": str((EVIDENCE / "capture.mp4").resolve()),
                   "raw_sha256": capture_sha}},
        "capture_context": context}
    gate = visual_gate.verify(receipt, profile)
    print("gate:", gate)

    capture_receipt = {
        "schema": "mat2-u04.input-settings.capture.v1",
        "task_id": TASK_ID, "card_id": CARD_ID, "run_id": RUN_ID,
        "attempt_id": ATTEMPT_ID, "agent_id": AGENT_ID,
        "criteria_sha256": "192ca43f061c4b6b2763d11213e0246ea075c3f62e6948948ba8c64213bf5180",
        "video": {"reference":
                  "tools/monkey_campaign/contributions/MAT2-U04/evidence/capture.mp4",
                  "sha256": capture_sha,
                  "bytes": (EVIDENCE / "capture.mp4").stat().st_size,
                  "frames": n_a, "fps": FPS,
                  "segments": "3 views x diagnostic+clean, 391 frames each",
                  "duration_s": n_a / FPS},
        "bitexact_proof": {"capture_a_sha256": hash_a,
                           "capture_b_sha256": hash_b, "equal": bitexact},
        "ffmpeg": ["-f", "image2", "-framerate", "20", "-i", "f%04d.png",
                   "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23",
                   "-preset", "medium", "-flags", "+bitexact",
                   "-fflags", "+bitexact", "-x264-params", "threads=1:ref=4"],
        "manifest": {"reference":
                     "tools/monkey_campaign/contributions/MAT2-U04/evidence/capture_manifest.json",
                     "sha256": sha256_file(manifest_path), "views": len(views)},
        "validation": {"visual_capture.validate_manifest": structural,
                       "visual_gate.verify": gate},
        "honest_boundary": "Deterministic CPU visualization of the recorded "
                           "headless trace; the body is the harness's declared "
                           "integration of the real emitted CommandRecords; NOT "
                           "native engine frames (PREREGISTRATION).",
        "wall_clock_build_seconds": time.monotonic() - started,
    }
    (EVIDENCE / "capture_receipt.json").write_text(
        json.dumps(capture_receipt, indent=1, sort_keys=True) + "\n",
        encoding="utf-8")
    print("capture receipt written; capture_sha256:", capture_sha[:12])
    return 0


if __name__ == "__main__":
    sys.exit(main())
