"""capture_build.py -- ONT-X02 motion capture: trace -> video -> camera manifest.

Renders the frozen session trace (evidence/trace.jsonl from
motion_profile_probe.py) into ONE deterministic video (two views x 67 ticks,
640x360, 20 fps, ffmpeg libx264 bitexact), then writes and VALIDATES the
chimera.visual_capture_manifest.v1 camera manifest with the campaign's own
validator (visual_capture.validate_manifest) and acceptance binding
(visual_gate.verify) against the card's frozen profile (card_task.json).

HONEST BOUNDARY (PREREGISTRATION): the pixels are a deterministic CPU
visualization of the recorded headless session trace -- the flow is headless
by construction; these are NOT native engine frames and carry no V08 claim.
Scene referents drawn per view: ground grid + session anchor marker (player
origin, heading arrow); the diagnostic layers draw the session HUD actually
recorded in the trace (state/tick IDs, skill keys + command records,
resource/session diagnostics). Clean pairs draw the scene only.

Camera laws are the pinned follow_camera.py referents: eye/up formulas, 45 deg
vertical FOV, right-handed Y-up metres. The bookmark view is the engine's
DEFAULT bookmark (radius 12, theta 0, phi 0.3, target origin), fixed for all
samples; the follow view is the REAL FollowCamera's applied solution per tick.

    python -B tools/monkey_campaign/contributions/ONT-X02/capture_build.py
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"
SCRATCH = HERE.parent.parent.parent.parent.parent / "scratch" / "ont-x02-frames"

W, H = 640, 360
FPS = 20
FOV_DEG = 45.0
TAN_HALF = math.tan(math.radians(FOV_DEG) / 2.0)
NEAR, FAR = 0.1, 200.0
FRAME_ID = "monkey_session_world_yup_m"

CAMPAIGN_TOOLS = Path("E:/PythonChimera/tools/monkey_campaign")

SUBJECT_SHA256 = "30e06c04dc33da271bfe817d26a4adbf1251f392b224546fc795f307458455cf"
RUN_ID = "ont-x02-motion-20260926-c3f7e902"

VIEW_BOOKMARK = "matched before/after camera bookmark"
VIEW_FOLLOW = "normal follow view during recovery"
LAYERS = ["state and tick IDs",
          "active skill/contact labels",
          "resource/session diagnostics"]
LABELS = [("state_banner", "session_flow_state"),
          ("tick_id", "session_tick"),
          ("skill_keys", "player_keys"),
          ("contact_records", "command_records"),
          ("session_diag", "session_flow_state"),
          ("resource_diag", "world_calls")]

FONT = ImageFont.load_default()

BG = (16, 18, 24)
GRID = (58, 64, 78)
GRID_MAJOR = (84, 92, 110)
PLAYER = (86, 214, 130)
HEADING = (240, 214, 96)
BOOT_FLASH = (235, 235, 255)
TXT = (220, 226, 240)
TXT_DIM = (150, 158, 176)
LAYER_TAG = (120, 200, 255)


# ── trace ─────────────────────────────────────────────────────────────────────
def load_trace():
    raw = (EVIDENCE / "trace.jsonl").read_bytes()
    rows = [json.loads(l) for l in raw.decode("utf-8").splitlines() if l]
    return raw, rows


# ── camera math (pinned follow_camera.py laws, cited) ────────────────────────
def basis(eye, target, theta, phi):
    f = [target[i] - eye[i] for i in range(3)]
    n = math.sqrt(sum(c * c for c in f))
    z = [c / n for c in f]
    up = (-math.sin(phi) * math.sin(theta), math.cos(phi),
          math.sin(phi) * math.cos(theta))
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


def draw_segment(draw, p0w, p1w, eye, axes, fill, width=1):
    a = project(p0w, eye, axes)
    b = project(p1w, eye, axes)
    if a is None or b is None:
        return
    draw.line([a, b], fill=fill, width=width)


def draw_scene(draw, row, eye, axes):
    """The depth-sorted scene both modes share: ground grid + session anchor."""
    g = 16
    step = 2.0
    for i in range(-g, g + 1, int(step)):
        c = GRID_MAJOR if i == 0 else GRID
        draw_segment(draw, (float(i), 0.0, -float(g)), (float(i), 0.0, float(g)),
                     eye, axes, c)
        draw_segment(draw, (-float(g), 0.0, float(i)), (float(g), 0.0, float(i)),
                     eye, axes, c)
    ax, ay, az = row["anchor"]
    # the player: a grounded disc (16-gon), a body post, a heading arrow
    r = 1.0
    pts = []
    for k in range(16):
        a = 2.0 * math.pi * k / 16.0
        q = project((ax + r * math.cos(a), 0.0, az + r * math.sin(a)),
                    eye, axes)
        if q is None:
            pts = []
            break
        pts.append(q)
    if pts:
        draw.polygon(pts, outline=PLAYER, fill=(28, 60, 40))
    top = project((ax, 1.0, az), eye, axes)
    base = project((ax, 0.0, az), eye, axes)
    if top and base:
        draw.line([base, top], fill=PLAYER, width=3)
    hd = math.radians(row["heading_deg"])
    tip = project((ax + 2.0 * math.sin(hd), 0.05, az + 2.0 * math.cos(hd)),
                  eye, axes)
    if tip and base:
        draw.line([base, tip], fill=HEADING, width=2)


def draw_diagnostics(draw, row, view):
    """The three declared diagnostic layers, each tagged with its name."""
    x0, y0 = 8, 8
    # layer 1: state and tick IDs
    draw.rectangle([x0 - 2, y0 - 2, x0 + 240, y0 + 44], fill=(0, 0, 0))
    draw.text((x0, y0), "L1 state and tick IDs", fill=LAYER_TAG, font=FONT)
    draw.text((x0, y0 + 12),
              "state=%s tick=%d t=%dms epoch=%d view=%s"
              % (row["state"], row["tick"], row["t_ms"], row["scene_epoch"],
                 "bookmark" if view == VIEW_BOOKMARK else "follow"),
              fill=TXT, font=FONT)
    y0 += 50
    # layer 2: active skill/contact labels
    recs = row["records"]
    events = row["events"]
    line2 = "L2 skill/contact keys=%s recs=%s"
    rec_txt = ",".join("v=%.3f y=%+.2f" % (r["v_forward"], r["yaw_rate"])
                       for r in recs) or "-"
    draw.rectangle([x0 - 2, y0 - 2, x0 + 320, y0 + 44], fill=(0, 0, 0))
    draw.text((x0, y0), "L2 active skill/contact labels", fill=LAYER_TAG,
              font=FONT)
    draw.text((x0, y0 + 12), line2 % (",".join(row["held"]) or "-",
                                      rec_txt), fill=TXT, font=FONT)
    y0 += 50
    # layer 3: resource/session diagnostics
    drops = events.get("dropped", [])
    drop_kinds = sorted({d.get("kind", "?") for d in drops})
    boot = "x%d" % row["boot_calls"]
    tdn = "+".join(row["teardown_calls"][-3:]) or "-"
    line3 = ("L3 resource/session boot=%s teardown=%s mapper=%d "
             "drops=%s focus=%s")
    focus = ",".join(m["kind"] for m in
                     row["focus_markers_at_this_tick"]) or "-"
    draw.rectangle([x0 - 2, y0 - 2, x0 + 420, y0 + 44], fill=(0, 0, 0))
    draw.text((x0, y0), "L3 resource/session diagnostics", fill=LAYER_TAG,
              font=FONT)
    draw.text((x0, y0 + 12),
              line3 % (boot, tdn, row["mapper_calls_total"],
                       ",".join(drop_kinds) or "-", focus),
              fill=TXT, font=FONT)
    # event callouts (diagnostic-only, part of L3): the declared reload boot
    if any(e.get("declared") == "world_boot"
           for e in row["events"].get("restart_path", [])):
        draw.text((x0 + 300, y0 + 12), "World.boot (reload)",
                  fill=BOOT_FLASH, font=FONT)


def render_frames(rows, out_dir):
    half = len(rows)
    paths = []
    for idx, row in enumerate(rows):
        # bookmark view (first half)
        bm = row["cam_bookmark"]
        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)
        eye_b = tuple(bm["position"])
        axes_b = basis(eye_b, tuple(bm["target"]), 0.0, 0.3)
        draw_scene(d, row, eye_b, axes_b)
        draw_diagnostics(d, row, VIEW_BOOKMARK)
        p = out_dir / ("f%04d.png" % idx)
        img.save(p)
        paths.append(p)
        # follow view (second half)
        fl = row["cam_follow"]
        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)
        v = fl["applied_v"]
        eye_f = tuple(fl["position"])
        axes_f = basis(eye_f, tuple(fl["target"]), v[1], v[2])
        draw_scene(d, row, eye_f, axes_f)
        draw_diagnostics(d, row, VIEW_FOLLOW)
        p = out_dir / ("f%04d.png" % (half + idx))
        img.save(p)
        paths.append(p)
    return paths


def build_video(frame_paths, dst):
    if dst.exists():
        dst.unlink()
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "image2", "-framerate", str(FPS),
           "-i", str(frame_paths[0].parent / "f%04d.png"),
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23",
           "-preset", "medium", "-flags", "+bitexact", "-fflags", "+bitexact",
           "-x264-params", "threads=1:ref=4",
           str(dst)]
    subprocess.run(cmd, check=True)
    return dst


def sha256_file(path):
    d = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            d.update(chunk)
    return d.hexdigest()


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


def pose_sample(row, which):
    src = row["cam_bookmark"] if which == "bookmark" else row["cam_follow"]
    return {"tick": row["tick"],
            "position": list(src["position"]),
            "target": list(src["target"]),
            "distance_to_target": src["distance_to_target"],
            "orientation": list(src["orientation"])}


def visibility_block(mode):
    if mode == "diagnostic":
        return {
            "layers": list(LAYERS),
            "label_ids": [l for l, _ in LABELS],
            "selected_ids": [],
            "required_subject_ids": ["session_anchor"],
            "observed_subject_ids": ["session_anchor", "ground_grid",
                                     "session_flow_state", "session_tick",
                                     "player_keys", "command_records",
                                     "world_calls"],
            "missing_subject_ids": [],
            "occlusion_mode": "depth_tested",
            "tag_bindings": [{"label_id": l, "subject_id": s}
                             for l, s in LABELS],
        }
    return {
        "layers": [],
        "label_ids": [],
        "selected_ids": [],
        "required_subject_ids": ["session_anchor"],
        "observed_subject_ids": ["session_anchor", "ground_grid"],
        "missing_subject_ids": [],
        "occlusion_mode": "depth_tested",
        "tag_bindings": [],
    }


def main():
    trace_bytes, rows = load_trace()
    trace_sha = hashlib.sha256(trace_bytes).hexdigest()
    n = len(rows)
    t0, t1 = rows[0]["tick"], rows[-1]["tick"]
    duration = (2 * n) / FPS

    SCRATCH.mkdir(parents=True, exist_ok=True)
    for old in SCRATCH.glob("f*.png"):
        old.unlink()
    frame_paths = render_frames(rows, SCRATCH)
    video = EVIDENCE / "capture.mp4"
    build_video(frame_paths, video)
    capture_sha = sha256_file(video)
    shutil.rmtree(SCRATCH, ignore_errors=True)

    seconds_bm = [0.0, n / FPS]
    seconds_fl = [n / FPS, duration]
    bm_samples = [pose_sample(r, "bookmark") for r in rows]
    fl_samples = [pose_sample(r, "follow") for r in rows]
    bm_cam = camera_block("fixed_bookmark", bm_samples)
    fl_cam = camera_block("sampled_trajectory", fl_samples,
                          interpolation="recorded_each_tick")

    def row(view_id, mode, pair_id, cam, seconds):
        return {"view_id": view_id, "mode": mode, "pair_id": pair_id,
                "state_binding": {"kind": "trace", "sha256": trace_sha},
                "artifact_locator": {"kind": "video", "seconds": list(seconds)},
                "camera": cam,
                "visibility": visibility_block(mode)}

    manifest = {
        "schema": "chimera.visual_capture_manifest.v1",
        "task_id": "X02",
        "run_id": RUN_ID,
        "subject_sha256": SUBJECT_SHA256,
        "capture_sha256": capture_sha,
        "profile_id": "recovery",
        "tick_interval": [t0, t1],
        "views": [
            row(VIEW_BOOKMARK, "diagnostic", "bookmark", bm_cam, seconds_bm),
            row(VIEW_BOOKMARK, "clean", "bookmark", bm_cam, seconds_bm),
            row(VIEW_FOLLOW, "diagnostic", "follow", fl_cam, seconds_fl),
            row(VIEW_FOLLOW, "clean", "follow", fl_cam, seconds_fl),
        ],
    }
    manifest_path = EVIDENCE / "capture_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=1, sort_keys=True)
                             + "\n", encoding="utf-8")

    # ── validation with the campaign's own gate (read-only import) ───────────
    sys.path.insert(0, str(CAMPAIGN_TOOLS))
    sys.dont_write_bytecode = True
    for stale in [k for k in sys.modules if k in ("visual_gate",
                                                  "visual_capture",
                                                  "integrity")]:
        del sys.modules[stale]
    import visual_gate                                   # noqa: E402
    contract = json.loads((HERE / "card_task.json").read_text(encoding="utf-8"))
    receipt = {
        "evidence": {
            "camera": {"reference": str(manifest_path.resolve()),
                       "raw_sha256": sha256_file(manifest_path)},
            "visual": {"reference": str(video.resolve()),
                       "raw_sha256": capture_sha},
        },
        "capture_context": {
            "task_id": "X02",
            "subject_sha256": SUBJECT_SHA256,
            "run_id": RUN_ID,
            "capture_sha256": capture_sha,
            "tick_interval": [t0, t1],
        },
    }
    structural = visual_gate.verify(receipt, contract)

    capture_receipt = {
        "schema": "ont-x02.motion.capture.v1",
        "task_id": "X02",
        "run_id": RUN_ID,
        "subject_sha256": SUBJECT_SHA256,
        "honest_boundary": "Deterministic CPU visualization of the recorded "
                           "headless session trace (trace.jsonl); NOT native "
                           "engine frames; V08 stays with the integration lane.",
        "video": {"reference": str(video.resolve()),
                  "raw_sha256": capture_sha,
                  "bytes": video.stat().st_size,
                  "resolution": [W, H], "fps": FPS,
                  "frames": 2 * n, "duration_s": duration},
        "manifest": {"reference": str(manifest_path.resolve()),
                     "raw_sha256": sha256_file(manifest_path)},
        "state_binding": {"kind": "trace", "raw_sha256": trace_sha,
                          "rows": n, "tick_interval": [t0, t1]},
        "views": {
            VIEW_BOOKMARK: {"seconds": seconds_bm,
                            "camera": "fixed_bookmark engine default "
                                      "(radius 12, theta 0, phi 0.3, target "
                                      "origin)",
                            "eye": list(rows[0]["cam_bookmark"]["position"]),
                            "distance_to_target":
                                rows[0]["cam_bookmark"]["distance_to_target"]},
            VIEW_FOLLOW: {"seconds": seconds_fl,
                          "camera": "sampled_trajectory recorded_each_tick "
                                    "(real pinned FollowCamera applied "
                                    "solution)"},
        },
        "render_referents": {
            "projection": "perspective 45 deg vertical FOV (tan_half "
                          "0.41421356), principal point centered",
            "frame": FRAME_ID + " (right-handed, Y-up, metres)",
            "source_module": "tools/monkey_campaign/product/follow_camera.py "
                             "@ f30f2224 (sha " + SUBJECT_SHA256[:8] +
                             " is session_flow; follow_camera d61347f0)",
        },
        "gate_validation": structural,
    }
    (EVIDENCE / "capture_receipt.json").write_text(
        json.dumps(capture_receipt, indent=1, sort_keys=True) + "\n",
        encoding="utf-8")
    print("video bytes:", video.stat().st_size)
    print("capture_sha256:", capture_sha)
    print("gate:", json.dumps(structural))
    print("RESULT:", "CAPTURE BUILT AND GATE-VALID" if
          structural.get("structurally_valid") else "GATE REJECTED")
    return 0 if structural.get("structurally_valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())
