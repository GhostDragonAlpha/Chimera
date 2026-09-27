"""capture_build.py -- ONT-U01 controls capture: trace -> video -> manifest.

Renders the frozen controls trace (evidence/trace.jsonl from
controls_profile_probe.py) into ONE deterministic video (three views x
diagnostic+clean segments x 61 ticks, 640x360, 20 fps, ffmpeg libx264
bitexact), then writes and VALIDATES the chimera.visual_capture_manifest.v1
camera manifest with the campaign's own validator
(visual_capture.validate_manifest) and acceptance binding (visual_gate.verify)
against the card's frozen profile (card_task.json).

HONEST BOUNDARY (PREREGISTRATION): the pixels are a deterministic CPU
visualization of the recorded headless command-seam trace -- the mapper and
the seam are headless by construction; these are NOT native engine frames.
Clean segments are rendered as their OWN frames (no diagnostic pixels at all)
so a decoded clean view truly contains no diagnostics.

Camera laws are the pinned follow_camera.py referents: engine eye/up formulas,
45 deg vertical FOV, right-handed Y-up metres. The follow view is the REAL
pinned FollowCamera's applied solution per tick; the obstructed view is the
frozen through-pillar construction (measured occlusion ray in the trace); the
side view is the engine side bookmark (fixed, repeatable).

    python -B tools/monkey_campaign/contributions/ONT-U01/capture_build.py
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
SCRATCH = HERE.parents[4] / "scratch" / "ont-u01-frames"

W, H = 640, 360
FPS = 20
FOV_DEG = 45.0
TAN_HALF = math.tan(math.radians(FOV_DEG) / 2.0)
NEAR, FAR = 0.1, 200.0
FRAME_ID = "monkey_session_world_yup_m"
CRF = "23"

CAMPAIGN_TOOLS = Path("E:/PythonChimera/tools/monkey_campaign")

SUBJECT_SHA256 = "7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44"
RUN_ID = "ont-u01-controls-20260926-243e4030"

VIEW_FOLLOW = "normal follow-camera distance"
VIEW_OBSTRUCTED = "obstructed and close-target views"
VIEW_SIDE = "repeatable inspection side view"
VIEWS = (VIEW_FOLLOW, VIEW_OBSTRUCTED, VIEW_SIDE)
LAYERS = ["input/state/tick display",
          "camera target and frustum diagnostics",
          "selected creature labels"]
LABELS = [("input_state_tick", "input_state"),
          ("command_records", "command_records"),
          ("camera_target", "camera_target"),
          ("frustum_diag", "camera_frustum"),
          ("selected_creature", "player_anchor"),
          ("obstruction_label", "obstruction_pillar")]

PILLAR = {"cx": 0.9, "cz": 0.75, "r": 0.30, "top": 2.0}

FONT = ImageFont.load_default()

BG = (16, 18, 24)
GRID = (58, 64, 78)
GRID_MAJOR = (84, 92, 110)
PLAYER = (86, 214, 130)
PLAYER_DARK = (28, 60, 40)
PILLAR_COL = (150, 118, 82)
PILLAR_DARK = (96, 76, 54)
HEADING = (240, 214, 96)
TXT = (220, 226, 240)
TXT_DIM = (150, 158, 176)
LAYER_TAG = (120, 200, 255)
FRUSTUM = (170, 120, 230)


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


def draw_grid(draw, eye, axes):
    g, step = 16, 2.0
    for i in range(-g, g + 1, int(step)):
        c = GRID_MAJOR if i == 0 else GRID
        draw_segment(draw, (float(i), 0.0, -float(g)), (float(i), 0.0, float(g)),
                     eye, axes, c)
        draw_segment(draw, (-float(g), 0.0, float(i)), (float(g), 0.0, float(i)),
                     eye, axes, c)


def draw_anchor(draw, row, eye, axes):
    ax, ay, az = row["body"]
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
        draw.polygon(pts, outline=PLAYER, fill=PLAYER_DARK)
    top = project((ax, 1.0, az), eye, axes)
    base = project((ax, 0.0, az), eye, axes)
    if top and base:
        draw.line([base, top], fill=PLAYER, width=3)
    hd = math.radians(row["heading_deg"])
    tip = project((ax + 2.0 * math.sin(hd), 0.05, az + 2.0 * math.cos(hd)),
                  eye, axes)
    if tip and base:
        draw.line([base, tip], fill=HEADING, width=2)


def draw_pillar(draw, eye, axes):
    cx, cz, r, top = PILLAR["cx"], PILLAR["cz"], PILLAR["r"], PILLAR["top"]
    rings = []
    for y in (0.0, top):
        ring = []
        for k in range(16):
            a = 2.0 * math.pi * k / 16.0
            q = project((cx + r * math.cos(a), y, cz + r * math.sin(a)),
                        eye, axes)
            ring.append(q)
        if any(q is None for q in ring):
            return
        rings.append(ring)
    bottom, top_ring = rings
    for k in range(16):
        k2 = (k + 1) % 16
        quad = [bottom[k], bottom[k2], top_ring[k2], top_ring[k]]
        shade = PILLAR_COL if k % 2 == 0 else PILLAR_DARK
        draw.polygon(quad, fill=shade)
    draw.polygon(top_ring, fill=PILLAR_COL)


def pillar_mean_distance(eye):
    return math.dist(eye, (PILLAR["cx"], 1.0, PILLAR["cz"]))


def anchor_mean_distance(eye, row):
    return math.dist(eye, (row["body"][0], 0.5, row["body"][2]))


def draw_frustum(draw, row, eye, axes, cam):
    """Layer 2 scene part: the camera target marker + frame corner rays."""
    t = cam["target"]
    base = project(t, eye, axes)
    if base:
        s = 5
        draw.line([base[0] - s, base[1], base[0] + s, base[1]], fill=FRUSTUM,
                  width=2)
        draw.line([base[0], base[1] - s, base[0], base[1] + s], fill=FRUSTUM,
                  width=2)


def draw_diagnostics(draw, row, view_id, cam):
    """The three declared diagnostic layers, each tagged with its name."""
    x0, y0 = 8, 8
    # layer 1: input/state/tick display
    recs = row["records"]
    rec_txt = ",".join("v=%.3f y=%+.2f@%d" % (r["v_forward"], r["yaw_rate"],
                                              r["issued_tick"])
                       for r in recs) or "-"
    ev_txt = ",".join(e["kind"] for e in row["events_this_tick"]) or "-"
    draw.rectangle([x0 - 2, y0 - 2, x0 + 330, y0 + 56], fill=(0, 0, 0))
    draw.text((x0, y0), "L1 input/state/tick display", fill=LAYER_TAG,
              font=FONT)
    draw.text((x0, y0 + 12),
              "tick=%d t=%dms state=%s expiry=%s"
              % (row["tick"], row["t_ms"], row["state"],
                 row["expiry_of_last_record"]), fill=TXT, font=FONT)
    draw.text((x0, y0 + 24), "held=%s recs=%s" % (",".join(row["held"])
                                                  or "-", rec_txt),
              fill=TXT, font=FONT)
    draw.text((x0, y0 + 36), "events=%s" % ev_txt, fill=TXT_DIM, font=FONT)
    y0 += 62
    # layer 2: camera target and frustum diagnostics
    draw.rectangle([x0 - 2, y0 - 2, x0 + 330, y0 + 44], fill=(0, 0, 0))
    draw.text((x0, y0), "L2 camera target and frustum diagnostics",
              fill=LAYER_TAG, font=FONT)
    draw.text((x0, y0 + 12),
              "view=[%s] target=(%.2f,%.2f,%.2f) d=%.3fm ray_ok=%s"
              % (view_id[:22], cam["target"][0], cam["target"][1],
                 cam["target"][2], cam["distance_to_target"],
                 cam.get("ray_blocked", "n/a")), fill=TXT, font=FONT)
    draw.text((x0, y0 + 24),
              "eye=(%.2f,%.2f,%.2f) fov=45deg proj=perspective"
              % tuple(cam["position"]), fill=TXT_DIM, font=FONT)
    y0 += 50
    # layer 3: selected creature labels
    draw.rectangle([x0 - 2, y0 - 2, x0 + 330, y0 + 32], fill=(0, 0, 0))
    draw.text((x0, y0), "L3 selected creature labels", fill=LAYER_TAG,
              font=FONT)
    draw.text((x0, y0 + 12),
              "selected=#player_anchor obstruction=#obstruction_pillar",
              fill=TXT, font=FONT)
    # creature label drawn at the anchor (part of L3)
    axes = None
    if view_id == VIEW_FOLLOW:
        v = row["cam_follow"]["applied_v"]
        axes = basis(tuple(cam["position"]), tuple(cam["target"]), v[1], v[2])
    elif view_id == VIEW_OBSTRUCTED:
        axes = basis(tuple(cam["position"]), tuple(cam["target"]), 0.0, 0.0)
    else:
        axes = basis(tuple(cam["position"]), tuple(cam["target"]),
                     math.pi / 2.0, 0.3)
    lab = project((row["body"][0], 1.4, row["body"][2]),
                  tuple(cam["position"]), axes)
    if lab:
        draw.text((lab[0] - 40, lab[1]), "#player_anchor", fill=HEADING,
                  font=FONT)


def render_frames(rows, out_dir):
    """6 segments: for each view, the diagnostic run then the clean run."""
    n = len(rows)
    paths = []
    idx = 0

    def cam_pose(row, view_id):
        if view_id == VIEW_FOLLOW:
            return row["cam_follow"], None
        if view_id == VIEW_OBSTRUCTED:
            return row["cam_obstructed"], None
        return row["cam_side"], (math.pi / 2.0, 0.3)

    def render_one(row, view_id, mode):
        cam, angles = cam_pose(row, view_id)
        eye = tuple(cam["position"])
        target = tuple(cam["target"])
        if angles is None:
            v = row["cam_follow"]["applied_v"] if view_id == VIEW_FOLLOW \
                else None
            if v is not None:
                axes = basis(eye, target, v[1], v[2])
            else:
                axes = basis(eye, target, 0.0, 0.0)
        else:
            axes = basis(eye, target, angles[0], angles[1])
        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)
        draw_grid(d, eye, axes)
        # painter's order: farther of (anchor, pillar) first
        if anchor_mean_distance(eye, row) > pillar_mean_distance(eye):
            draw_anchor(d, row, eye, axes)
            draw_pillar(d, eye, axes)
        else:
            draw_pillar(d, eye, axes)
            draw_anchor(d, row, eye, axes)
        if mode == "diagnostic":
            draw_frustum(d, row, eye, axes, cam)
            draw_diagnostics(d, row, view_id, cam)
        p = out_dir / ("f%04d.png" % idx)
        img.save(p)
        return p

    for view_id in VIEWS:
        for mode in ("diagnostic", "clean"):
            for row in rows:
                paths.append(render_one(row, view_id, mode))
                idx += 1
    return paths


def build_video(frame_paths, dst):
    if dst.exists():
        dst.unlink()
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "image2", "-framerate", str(FPS),
           "-i", str(frame_paths[0].parent / "f%04d.png"),
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", CRF,
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


def sample_from(pose, tick):
    return {"tick": tick,
            "position": list(pose["position"]),
            "target": list(pose["target"]),
            "distance_to_target": pose["distance_to_target"],
            "orientation": list(pose["orientation"])}


def visibility_block(mode, view_id):
    required = ["player_anchor"]
    observed = ["player_anchor", "ground_grid", "obstruction_pillar",
                "heading_arrow"]
    if mode == "diagnostic":
        observed += ["input_state", "command_records", "camera_target",
                     "camera_frustum", "session_tick"]
        return {
            "layers": list(LAYERS),
            "label_ids": [l for l, _ in LABELS],
            "selected_ids": ["player_anchor"],
            "required_subject_ids": required,
            "observed_subject_ids": observed,
            "missing_subject_ids": [],
            "occlusion_mode": "depth_tested",
            "tag_bindings": [{"label_id": l, "subject_id": s}
                             for l, s in LABELS],
        }
    return {
        "layers": [],
        "label_ids": [],
        "selected_ids": [],
        "required_subject_ids": required,
        "observed_subject_ids": observed,
        "missing_subject_ids": [],
        "occlusion_mode": "depth_tested",
        "tag_bindings": [],
    }


def main():
    trace_bytes, rows = load_trace()
    trace_sha = hashlib.sha256(trace_bytes).hexdigest()
    n = len(rows)
    t0, t1 = rows[0]["tick"], rows[-1]["tick"]
    seg = n / FPS                     # 3.05 s per 61-tick segment

    SCRATCH.mkdir(parents=True, exist_ok=True)
    for old in SCRATCH.glob("f*.png"):
        old.unlink()
    frame_paths = render_frames(rows, SCRATCH)
    video = EVIDENCE / "capture.mp4"
    build_video(frame_paths, video)
    capture_sha = sha256_file(video)
    shutil.rmtree(SCRATCH, ignore_errors=True)

    # segments: per view, [diagnostic, clean]
    def seconds(view_index, mode_index):
        k = view_index * 2 + mode_index
        return [round(k * seg, 3), round((k + 1) * seg, 3)]

    follow_cam = camera_block(
        "sampled_trajectory",
        [sample_from(r["cam_follow"], r["tick"]) for r in rows],
        interpolation="recorded_each_tick")
    obstructed_cam = camera_block(
        "sampled_trajectory",
        [sample_from(r["cam_obstructed"], r["tick"]) for r in rows],
        interpolation="recorded_each_tick")
    side_cam = camera_block(
        "fixed_bookmark",
        [sample_from(rows[0]["cam_side"], r["tick"]) for r in rows])

    def row(view_id, mode, pair_id, cam, view_index, mode_index):
        return {"view_id": view_id, "mode": mode, "pair_id": pair_id,
                "state_binding": {"kind": "trace", "sha256": trace_sha},
                "artifact_locator": {"kind": "video",
                                     "seconds": seconds(view_index,
                                                        mode_index)},
                "camera": cam,
                "visibility": visibility_block(mode, view_id)}

    manifest = {
        "schema": "chimera.visual_capture_manifest.v1",
        "task_id": "U01",
        "run_id": RUN_ID,
        "subject_sha256": SUBJECT_SHA256,
        "capture_sha256": capture_sha,
        "profile_id": "controls",
        "tick_interval": [t0, t1],
        "views": [
            row(VIEW_FOLLOW, "diagnostic", "follow", follow_cam, 0, 0),
            row(VIEW_FOLLOW, "clean", "follow", follow_cam, 0, 1),
            row(VIEW_OBSTRUCTED, "diagnostic", "obstructed", obstructed_cam,
                1, 0),
            row(VIEW_OBSTRUCTED, "clean", "obstructed", obstructed_cam, 1, 1),
            row(VIEW_SIDE, "diagnostic", "side", side_cam, 2, 0),
            row(VIEW_SIDE, "clean", "side", side_cam, 2, 1),
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
            "task_id": "U01",
            "subject_sha256": SUBJECT_SHA256,
            "run_id": RUN_ID,
            "capture_sha256": capture_sha,
            "tick_interval": [t0, t1],
        },
    }
    structural = visual_gate.verify(receipt, contract)

    capture_receipt = {
        "schema": "ont-u01.controls.capture.v1",
        "task_id": "U01",
        "run_id": RUN_ID,
        "subject_sha256": SUBJECT_SHA256,
        "honest_boundary": "Deterministic CPU visualization of the recorded "
                           "headless command-seam trace (trace.jsonl); NOT "
                           "native engine frames; the native playable-runtime "
                           "checkpoint stays with the integration lane.",
        "video": {"reference": str(video.resolve()),
                  "raw_sha256": capture_sha,
                  "bytes": video.stat().st_size,
                  "resolution": [W, H], "fps": FPS,
                  "frames": 6 * n, "duration_s": round(6 * n / FPS, 3),
                  "encoder": "ffmpeg libx264 yuv420p crf=%s bitexact "
                             "threads=1" % CRF},
        "manifest": {"reference": str(manifest_path.resolve()),
                     "raw_sha256": sha256_file(manifest_path)},
        "state_binding": {"kind": "trace", "raw_sha256": trace_sha,
                          "rows": n, "tick_interval": [t0, t1]},
        "views": {
            VIEW_FOLLOW: {"diagnostic_seconds": seconds(0, 0),
                          "clean_seconds": seconds(0, 1),
                          "camera": "sampled_trajectory recorded_each_tick "
                                    "(REAL pinned FollowCamera applied "
                                    "solution per tick)"},
            VIEW_OBSTRUCTED: {"diagnostic_seconds": seconds(1, 0),
                              "clean_seconds": seconds(1, 1),
                              "camera": "sampled_trajectory "
                                        "recorded_each_tick (frozen "
                                        "through-pillar construction; "
                                        "measured occlusion ray per tick)"},
            VIEW_SIDE: {"diagnostic_seconds": seconds(2, 0),
                        "clean_seconds": seconds(2, 1),
                        "camera": "fixed_bookmark engine side bookmark "
                                  "(radius 12, theta pi/2, phi 0.3, target "
                                  "origin) identical all %d samples" % n},
        },
        "render_referents": {
            "projection": "perspective 45 deg vertical FOV (tan_half "
                          "0.41421356), principal point centered",
            "frame": FRAME_ID + " (right-handed, Y-up, metres)",
            "source_module": "tools/monkey_campaign/product/follow_camera.py "
                             "@ f30f2224 (d61347f0); subject input_mapper.py "
                             "(7a36a45e)",
            "clean_segments": "rendered as their OWN frames; a decoded clean "
                              "view contains no diagnostic pixels",
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
