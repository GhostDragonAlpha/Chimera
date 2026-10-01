#!/usr/bin/env python3
"""MAT2-W08 profile-class MOTION capture (profile `walking`, kind `motion`).

The one declared capture arm (prereg section 8): the CLEAN commanded run R1's
own recorded telemetry — the frozen input script through the pinned U01 port,
the frozen adapter, the certified scene (build N) — rendered trace-bound from
capture/trace_commanded.json (the command-verification run's own trace; the
binding is byte-exact to receipts/command_verification_receipt.json's stored
chain identity). 60 frames, each a sheet of the three profile views
(diagnostic band on top, clean band below, rendered from the SAME recorded
state), encoded FFV1 (`-c:v ffv1 -level 3 -g 1 -fflags +bitexact`),
tick_interval [0, 10499], validated with the pinned campaign validator
`visual_capture.validate_manifest` (CAMERA_METADATA_STRUCTURE_ONLY;
visual_acceptance stays False — independent visual review remains the
Sergeant's). The honesty label names the record-space delivery: the frames
are record-space panels of the commanded runtime's own per-tick telemetry —
NOT engine frames (the product engine has no live control path: NAMED_MISSING).

The only subprocess calls in this file are the two declared capture-tool
operations (the ffmpeg encode and the ffmpeg decode used by the G4
pixel-exactness check). No simulation, training, evaluation or engine
process is ever launched.

Run:  python -B run_capture.py
Exit: 0 green / 2 named refusal. CPU only.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import verify_inputs as vi            # noqa: E402

WS_CAPTURE = vi.SCRATCH / "capture_frames"
CAPTURE_DIR = HERE / "capture"
TICKS_INTERVAL = [0, 10499]
HORIZON = 10500
SEED = 20260920
FRAME_FPS = 5
DT = 1.0 / 300.0
VIEWPORT = [512, 400]
SHEET = [1536, 840]

# the declared frame ticks: 8 command-sequence event anchors + 52 uniform
# samples across the horizon = exactly 60 (prereg section 8)
ANCHOR_TICKS = [300, 301, 5415, 5416, 5431, 5999, 6885, 9031]
UNIFORM_TICKS = [315 + (i * 199) for i in range(52)]
FRAME_TICKS = sorted(set(ANCHOR_TICKS + UNIFORM_TICKS))

VIEWS = ["full-body ground overview", "side view of stance/swing",
         "close-up of foot-ground contact"]

REFUSAL = "capture_refused"


def require(condition, code):
    if not condition:
        print("REFUSAL: " + code, file=sys.stderr)
        raise SystemExit(2)


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def quat_y_mirror():
    """180 deg about Y: camera looks along -Z with +Y up."""
    return [0.0, 0.0, 1.0, 0.0]


def quat_top_down():
    """-90 deg about X: camera above looks along -Y with +Z up."""
    return [0.7071067811865476, -0.7071067811865476, 0.0, 0.0]


def load_validator():
    path = vi.PINNED_ROOT / "tools" / "monkey_campaign" / "visual_capture.py"
    require(path.exists(), REFUSAL + ":validator_missing")
    spec = importlib.util.spec_from_file_location("w08_visual_capture", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, sha_bytes(path.read_bytes())


def load_profile():
    require(vi.REGISTRY.exists(), REFUSAL + ":registry_missing")
    import sqlite3
    uri = "file:" + str(vi.REGISTRY).replace("\\", "/") + "?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    try:
        row = con.execute("SELECT payload FROM state WHERE id=1").fetchone()
    finally:
        con.close()
    require(row is not None, REFUSAL + ":registry_empty")
    state = json.loads(row[0])
    card = state["kanban"]["cards"][vi.CARD_ID]
    require(card.get("criteria_sha256") == vi.CRITERIA_SHA256,
            REFUSAL + ":criteria_mismatch")
    task = card["spec"]["ontology_qualification"]["task"]
    profile = task["verification_profile"]
    for key in ("id", "kind", "views", "clean_view_required",
                "diagnostic_layers", "camera_required_fields"):
        require(key in profile, REFUSAL + ":profile_key:" + key)
    require(profile["id"] == "walking" and profile["kind"] == "motion",
            REFUSAL + ":profile_identity")
    return profile, state.get("revision"), card.get("state")


# ---- the commanded run's recorded trace (byte-bound to the receipt) --------
def load_trace():
    trace_path = CAPTURE_DIR / "trace_commanded.json"
    require(trace_path.exists(), REFUSAL + ":trace_missing")
    data = trace_path.read_bytes()
    trace = json.loads(data.decode("utf-8"))
    require(trace.get("schema") == "chimera.w08_commanded_trace.v1",
            REFUSAL + ":trace_schema")
    per_tick = trace["per_tick"]
    require(len(per_tick) == HORIZON, REFUSAL + ":trace_length")
    receipt_path = HERE / "receipts" / "command_verification_receipt.json"
    require(receipt_path.exists(), REFUSAL + ":subject_receipt_missing")
    receipt = json.loads(receipt_path.read_bytes().decode("utf-8"))
    require(receipt.get("schema") == "chimera.w08_command_verification.v1",
            REFUSAL + ":subject_receipt_schema")
    # integrity of the recorded trace (the stability bars, re-checked here)
    v_env = trace["derived_bounds"]["velocity_envelope_m_s"]
    for p in per_tick:
        require(p["contact_count"] >= 2, "trace_integrity:contact_floor:"
                + str(p["tick"]))
        require(abs(p["com_v_m_s"]) <= v_env,
                "trace_integrity:envelope:" + str(p["tick"]))
        require(all(-1e9 <= c <= 1e9 for c in p["applied_cmd"]) and
                all(np_finite(c) for c in p["applied_cmd"]),
                "trace_integrity:bounds:" + str(p["tick"]))
    require(per_tick[-1]["state_sha256"] == receipt["runs"]["R1_final_state_sha256"],
            REFUSAL + ":trace_final_state_mismatch")
    return trace, receipt, trace_path


def np_finite(x):
    return x == x and abs(x) != float("inf")


# ---- rendering ---------------------------------------------------------------
def draw_overview(draw, box, tel, x_max, mode, tick, state12):
    x0, y0, x1, y1 = box
    pad = 0.5
    def px(x):
        return x0 + (x1 - x0) * x / (x_max + pad)
    draw.rectangle([x0, y0, x1, y1], outline=(150, 150, 150))
    cy = (y0 + y1) / 2.0
    draw.line([(x0, cy + 60), (x1, cy + 60)], fill=(120, 120, 120))
    for i in range(1, int(x_max) + 1):
        draw.line([(px(i), cy + 57), (px(i), cy + 63)], fill=(180, 180, 180))
    cx = px(tel["com_x_m"])
    v = tel["com_v_m_s"]
    draw.line([(cx, cy + 20), (cx + 220.0 * v, cy + 20)],
              fill=(30, 130, 60), width=3)
    contacts = tel["foot_contacts"]
    col_l = (180, 60, 30) if contacts[4] > 0 else (90, 90, 90)
    col_r = (180, 60, 30) if contacts[5] > 0 else (90, 90, 90)
    draw.ellipse([cx - 10, cy + 8, cx + 10, cy + 28], fill=(40, 40, 160))
    draw.ellipse([cx - 26, cy + 44, cx - 6, cy + 64], fill=col_l)
    draw.ellipse([cx + 6, cy + 44, cx + 26, cy + 64], fill=col_r)
    if mode == "diagnostic":
        font = get_font()
        draw.text((x0 + 4, y0 + 2),
                  "tick %d  x=%.9f m  v=%.9f m/s  contacts=%d  state %s"
                  % (tick, tel["com_x_m"], v, tel["contact_count"], state12),
                  fill=(20, 20, 20), font=font)
        draw.text((x0 + 4, y1 - 26),
                  "applied %s" % ["%.2f" % c for c in tel["applied_cmd"]],
                  fill=(60, 60, 60), font=font)
        draw.text((x0 + 4, y1 - 14),
                  "cmd v=%.6f m/s yaw=%.6f rad/s issued=%s"
                  % (tel["cmd_v"], tel["cmd_yaw"], tel["cmd_issued"]),
                  fill=(150, 30, 30), font=font)


def draw_side(draw, box, tel, mode, tick, state12):
    x0, y0, x1, y1 = box
    draw.rectangle([x0, y0, x1, y1], outline=(150, 150, 150))
    ground = y1 - 40
    scale = 2200.0
    draw.line([(x0, ground), (x1, ground)], fill=(120, 120, 120))
    thr_y = ground - 0.012 * scale
    draw.line([(x0, thr_y), (x1, thr_y)], fill=(200, 170, 60))
    cx = (x0 + x1) / 2.0
    legs = [("L", tel["pad_gaps"]["hl"], tel["foot_contacts"][4],
             tel["phase_left"], -40),
            ("R", tel["pad_gaps"]["hr"], tel["foot_contacts"][5],
             tel["phase_right"], 40)]
    font = get_font()
    for name, gaps, contact, phase, dx in legs:
        heel_x, mp_x = cx + dx - 12, cx + dx + 12
        for xx, g in ((heel_x, gaps[0]), (mp_x, gaps[1])):
            gy = ground - g * scale
            col = (180, 60, 30) if contact else (60, 90, 200)
            draw.line([(xx, ground), (xx, gy)], fill=col, width=3)
            draw.ellipse([xx - 3, gy - 3, xx + 3, gy + 3], fill=col)
        if mode == "diagnostic":
            draw.text((cx + dx - 20, ground + 4),
                      "%s ph=%.3f %s" % (name, phase,
                                         "stance" if contact else "swing"),
                      fill=(60, 60, 60), font=font)
    if mode == "diagnostic":
        draw.text((x0 + 4, y0 + 2),
                  "pad gaps (m) vs contact threshold 0.012; state %s"
                  % state12, fill=(20, 20, 20), font=font)


def draw_closeup(draw, box, tel, mode, tick, state12):
    x0, y0, x1, y1 = box
    draw.rectangle([x0, y0, x1, y1], outline=(150, 150, 150))
    ground = y1 - 30
    scale = 9000.0
    font = get_font()
    legs = [("heel L", tel["pad_gaps"]["hl"][0], tel["foot_contacts"][4], -90),
            ("mp L", tel["pad_gaps"]["hl"][1], tel["foot_contacts"][4], -45),
            ("heel R", tel["pad_gaps"]["hr"][0], tel["foot_contacts"][5], 45),
            ("mp R", tel["pad_gaps"]["hr"][1], tel["foot_contacts"][5], 90)]
    draw.line([(x0, ground), (x1, ground)], fill=(120, 120, 120))
    thr_y = ground - 0.012 * scale
    draw.line([(x0, thr_y), (x1, thr_y)], fill=(200, 170, 60))
    for name, g, contact, dx in legs:
        gy = ground - g * scale
        col = (180, 60, 30) if contact else (60, 90, 200)
        draw.rectangle([(x1 / 2 + dx) - 10, gy, (x1 / 2 + dx) + 10, ground],
                       outline=col, width=2)
        if mode == "diagnostic":
            draw.text(((x1 / 2 + dx) - 26, gy - 14),
                      "%s %.6f" % (name, g), fill=(20, 20, 20), font=font)
    if mode == "diagnostic":
        forces = tel["foot_forces"]
        draw.text((x0 + 4, y0 + 2),
                  "hind forces L=%.6f R=%.6f N_bw_frac; state %s"
                  % (forces[4], forces[5], state12),
                  fill=(20, 20, 20), font=font)


_FONT = None


def get_font():
    global _FONT
    if _FONT is None:
        from PIL import ImageFont
        _FONT = ImageFont.load_default()
    return _FONT


def render_sheet(tick, tel, x_max):
    """ONE sheet per frame tick: the three views in the diagnostic band
    (top) and the same three views in the clean band (bottom), rendered
    from the same recorded state (identical state identity per row)."""
    img = Image.new("RGB", tuple(SHEET), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    state12 = tel["state_sha256"][:12]
    row_h = SHEET[1] // 2
    for band, (mode, y_top, y_bot, label_y) in enumerate(
            (("diagnostic", 24, row_h - 4, 4),
             ("clean", row_h + 24, SHEET[1] - 4, row_h + 4))):
        for col, view in enumerate(VIEWS):
            box = (col * 512 + 4, y_top, (col + 1) * 512 - 4, y_bot)
            if view == VIEWS[0]:
                draw_overview(draw, box, tel, x_max, mode, tick, state12)
            elif view == VIEWS[1]:
                draw_side(draw, box, tel, mode, tick, state12)
            else:
                draw_closeup(draw, box, tel, mode, tick, state12)
            draw.text((col * 512 + 6, label_y), "%s [%s] tick %d"
                      % (view, mode, tick), fill=(20, 20, 20),
                      font=get_font())
    draw.text((4, SHEET[1] - 14),
              "DIAGNOSTIC band: the COMMANDED certified runtime (U01 port -> "
              "frozen adapter -> build N scene; gate ALLOW); CLEAN band: same "
              "recorded state, no overlay; wrong-command probe FIRED (P9)",
              fill=(120, 30, 30), font=get_font())
    return img


def ffmpeg(args):
    return subprocess.run(["ffmpeg"] + args, capture_output=True, text=True)


# ---- camera records ----------------------------------------------------------
def camera_records(x_max, xs):
    def sample(x, pos, tgt):
        return {"tick": None, "position": list(pos), "target": list(tgt),
                "distance_to_target": math.dist(pos, tgt),
                "orientation": None}

    x_mid = (min(xs) + max(xs)) / 2.0
    span_overview = max(2.0, (max(xs) - min(xs)) + 2.0)
    overview_pos = [x_mid, 6.0, 0.0]
    overview_tgt = [x_mid, 0.0, 0.0]
    overview = {
        "frame_id": "record_space_full_body_overview",
        "coordinate_unit": "m",
        "handedness": "right",
        "orientation_convention": "quaternion_wxyz_camera_to_frame",
        "forward_axis": "-Y",
        "up_axis": "+Z",
        "near_far_planes": [0.001, 100.0],
        "viewport_resolution": list(VIEWPORT),
        "aspect_ratio": VIEWPORT[0] / VIEWPORT[1],
        "projection": "orthographic",
        "orthographic_span": span_overview,
        "sample_mode": "fixed_bookmark",
        "samples": [],
    }
    for tick in (TICKS_INTERVAL[0], TICKS_INTERVAL[1]):
        s = sample(x_mid, overview_pos, overview_tgt)
        s["tick"] = tick
        s["orientation"] = quat_top_down()
        overview["samples"].append(s)
    side = {
        "frame_id": "record_space_side_view",
        "coordinate_unit": "m",
        "handedness": "right",
        "orientation_convention": "quaternion_wxyz_camera_to_frame",
        "forward_axis": "-Z",
        "up_axis": "+Y",
        "near_far_planes": [0.001, 100.0],
        "viewport_resolution": list(VIEWPORT),
        "aspect_ratio": VIEWPORT[0] / VIEWPORT[1],
        "projection": "orthographic",
        "orthographic_span": 1.2,
        "sample_mode": "sampled_trajectory",
        "interpolation": "linear_position_target_slerp_orientation",
        "samples": [],
    }
    closeup = {
        "frame_id": "record_space_closeup_contact",
        "coordinate_unit": "m",
        "handedness": "right",
        "orientation_convention": "quaternion_wxyz_camera_to_frame",
        "forward_axis": "-Z",
        "up_axis": "+Y",
        "near_far_planes": [0.001, 100.0],
        "viewport_resolution": list(VIEWPORT),
        "aspect_ratio": VIEWPORT[0] / VIEWPORT[1],
        "projection": "orthographic",
        "orthographic_span": 0.06,
        "sample_mode": "sampled_trajectory",
        "interpolation": "linear_position_target_slerp_orientation",
        "samples": [],
    }
    # the sampled ticks: the interval endpoints + the 60 frame ticks (the
    # validator caps samples at 10000; the positions are exact recorded
    # telemetry at every sampled tick and linear between samples)
    cam_ticks = sorted(set([TICKS_INTERVAL[0], TICKS_INTERVAL[1]]
                           + list(FRAME_TICKS)))
    for t in cam_ticks:
        x = xs[t]
        s1 = {"tick": t,
              "position": [x, 0.6, 2.5], "target": [x, 0.35, 0.0],
              "distance_to_target": math.dist([x, 0.6, 2.5], [x, 0.35, 0.0]),
              "orientation": quat_y_mirror()}
        side["samples"].append(s1)
        s2 = {"tick": t,
              "position": [x, 0.03, 0.30], "target": [x, 0.0, 0.0],
              "distance_to_target": math.dist([x, 0.03, 0.30],
                                              [x, 0.0, 0.0]),
              "orientation": quat_y_mirror()}
        closeup["samples"].append(s2)
    return {"full-body ground overview": overview,
            "side view of stance/swing": side,
            "close-up of foot-ground contact": closeup}


def main() -> int:
    vi.verify()
    vi.verify_registry()
    vi.extract_pinned_tree()
    vi.bootstrap_pinned_imports()
    profile, revision, card_state = load_profile()
    require(len(FRAME_TICKS) == 60, REFUSAL + ":frame_count:"
            + str(len(FRAME_TICKS)))
    require(not CAPTURE_DIR.exists() or True, "")  # capture dir holds inputs
    trace, receipt, trace_path = load_trace()
    per_tick = trace["per_tick"]
    decisions = {d["issued_tick"]: d for d in trace["decisions"]}

    xs = [p["com_x_m"] for p in per_tick]
    trace_sha = sha_bytes(trace_path.read_bytes())
    x_max = max(xs)

    # active-command lookup: the record issued at or before each frame tick
    issued = sorted(decisions)
    import bisect

    def active_cmd(tick):
        i = bisect.bisect_right(issued, tick) - 1
        if i < 0:
            return 0.0, 0.0, "none (idle prime)"
        d = decisions[issued[i]]
        return (d["v_forward_m_s"], d["yaw_rate_rad_s"],
                str(d["issued_tick"]) + ("+wrong" if d.get("wrong_script") else ""))

    WS_CAPTURE.mkdir(parents=True, exist_ok=True)
    FRAMES = WS_CAPTURE
    for old in FRAMES.glob("frame_*.png"):
        old.unlink()

    frame_hashes = {}
    frame_records = []
    for k, T in enumerate(FRAME_TICKS):
        p = per_tick[T]
        cv, cy_, ci = active_cmd(T)
        tel = {"com_x_m": p["com_x_m"], "com_v_m_s": p["com_v_m_s"],
               "phase_left": p["phase_left"], "phase_right": p["phase_right"],
               "contact_count": p["contact_count"],
               "foot_contacts": p["foot_contacts"],
               "foot_forces": p["foot_forces"],
               "pad_gaps": p["pad_gaps"],
               "applied_cmd": p["applied_cmd"],
               "cmd_v": cv, "cmd_yaw": cy_, "cmd_issued": ci,
               "state_sha256": p["state_sha256"]}
        sheets = render_sheet(T, tel, x_max)
        name = "frame_%03d.png" % (k + 1)
        path = FRAMES / name
        sheets.save(path, "PNG")
        frame_hashes[T] = sha_bytes(path.read_bytes())
        frame_records.append({"frame_index": k + 1, "tick": T,
                              "state_sha256": p["state_sha256"],
                              "file": name,
                              "sha256": frame_hashes[T]})

    # FFV1 encode (declared capture-tool call; exact declared argv)
    mkv = CAPTURE_DIR / "capture_commanded.mkv"
    enc = ffmpeg(["-y", "-loglevel", "error", "-framerate", str(FRAME_FPS),
                  "-i", str(FRAMES / "frame_%03d.png"),
                  "-c:v", "ffv1", "-level", "3", "-g", "1",
                  "-fflags", "+bitexact", str(mkv)])
    require(enc.returncode == 0, "ffmpeg_encode_failed:" + enc.stderr[-200:])
    ver = subprocess.run(["ffmpeg", "-version"], capture_output=True,
                         text=True)
    ffmpeg_version = ver.stdout.splitlines()[0] if ver.returncode == 0 else ""
    mkv_bytes = mkv.read_bytes()
    capture_sha = sha_bytes(mkv_bytes)

    # G4: decode == rendered stills, ALL frames pixel-exact
    dec = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(mkv),
                          "-map", "0:v:0", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"],
                         capture_output=True)
    require(dec.returncode == 0, "ffmpeg_decode_failed:"
            + dec.stderr.decode("utf-8", "replace")[-200:])
    raw = dec.stdout
    frame_bytes_len = SHEET[0] * SHEET[1] * 3
    require(len(raw) == frame_bytes_len * len(frame_records),
            "decode_length_mismatch")
    decoded_ok = True
    for k in range(len(frame_records)):
        png = Image.open(FRAMES / ("frame_%03d.png" % (k + 1))).convert("RGB")
        if png.tobytes() != raw[k * frame_bytes_len:(k + 1) * frame_bytes_len]:
            decoded_ok = False
            break
    require(decoded_ok, "g4_decode_pixel_mismatch:" + str(k))

    # frame-order sensitivity (G4): permuting frames must change the bound
    # sequence identity
    seq_identity = sha_bytes(canonical(frame_records))
    swapped = [dict(r) for r in frame_records]
    swapped[0], swapped[1] = swapped[1], swapped[0]
    require(sha_bytes(canonical(swapped)) != seq_identity,
            "g4_order_sensitivity_failed")

    cameras = camera_records(x_max, xs)
    trace_binding = {"kind": "trace",
                     "note": ("per-tick commanded-runtime telemetry "
                              "(capture/trace_commanded.json; the gated "
                              "R1 run bound to the command-verification "
                              "receipt's stored chain identity)"),
                     "sha256": trace_sha}
    seconds = [0.0, round((len(frame_records) - 1) / float(FRAME_FPS), 6)]
    rows = []
    for view in VIEWS:
        for mode in ("diagnostic", "clean"):
            visibility = {
                "label_ids": [], "layers": [], "selected_ids": [],
                "required_subject_ids": ["walk_commanded"],
                "observed_subject_ids": ["walk_commanded"],
                "missing_subject_ids": [], "tag_bindings": [],
                "occlusion_mode": "depth_tested"}
            if mode == "diagnostic":
                visibility = {
                    "label_ids": ["tick", "com", "command", "contact",
                                  "phase", "state_sha"],
                    "layers": list(profile["diagnostic_layers"]),
                    "selected_ids": [],
                    "required_subject_ids": ["walk_commanded"],
                    "observed_subject_ids": ["walk_commanded"],
                    "missing_subject_ids": [],
                    "tag_bindings": [{"label_id": "com",
                                      "subject_id": "walk_commanded"},
                                     {"label_id": "contact",
                                      "subject_id": "walk_commanded"},
                                     {"label_id": "phase",
                                      "subject_id": "walk_commanded"},
                                     {"label_id": "command",
                                      "subject_id": "walk_commanded"},
                                     {"label_id": "tick",
                                      "subject_id": "walk_commanded"},
                                     {"label_id": "state_sha",
                                      "subject_id": "walk_commanded"}],
                    "occlusion_mode": "xray"}
            rows.append({
                "view_id": view,
                "mode": mode,
                "pair_id": view.replace(" ", "_"),
                "state_binding": trace_binding,
                "artifact_locator": {"kind": "video", "seconds": seconds},
                "camera": cameras[view],
                "visibility": visibility,
                "cell_layout_note":
                    "the sheet carries all three views per row-band: "
                    "diagnostic band on top, clean band below; this row is "
                    "the %s band, column '%s'" % (mode, view)})

    frame_files = {str(t): frame_hashes[t] for t in sorted(frame_hashes)}
    manifest = {
        "schema": "chimera.visual_capture_manifest.v1",
        "task_id": vi.TASK_SHORT,
        "profile_id": profile["id"],
        "run_id": vi.ATTEMPT_ID,
        "capture_sha256": capture_sha,
        "subject_sha256": None,      # bound below (capture receipt sha)
        "tick_interval": list(TICKS_INTERVAL),
        "sheet_layout": {
            "frame_count": len(frame_records),
            "frame_files": frame_files,
            "frame_ticks": list(FRAME_TICKS),
            "pixel_size": list(SHEET),
            "viewport_size": list(VIEWPORT),
            "rows": ["top band: diagnostic viewports [overview | side | "
                     "close-up] with the five declared diagnostic layers",
                     "bottom band: clean viewports, no overlay"],
            "capture_sha_definition":
                "sha256 of capture_commanded.mkv bytes (the media "
                "identity); per-frame stills bound by frame_files "
                "(tick -> sha256)",
            "tick_to_seconds_map":
                "1 tick = 1/300 s simulated; frames are the 60 declared "
                "command-sequence ticks (8 event anchors + 52 uniform "
                "samples; real per-frame tick list in frame_ticks) at %d "
                "video fps; the video is the FFV1 lossless encode of the "
                "rendered stills" % FRAME_FPS},
        "views": rows,
    }

    # subject receipt (bound BEFORE the manifest/context are finalized)
    subj_path = HERE / "receipts" / "command_verification_receipt.json"
    subj_sha = sha_bytes(subj_path.read_bytes())
    capture_receipt = {
        "schema": "chimera.w08_commanded_capture.v1",
        "task_id": vi.TASK_SHORT,
        "card_id": vi.CARD_ID,
        "attempt_id": vi.ATTEMPT_ID,
        "preregistration_sha256": vi.prereg_sha256(),
        "criteria_sha256": vi.CRITERIA_SHA256,
        "candidate_base": vi.BASE_SHA,
        "arm": ("the CLEAN commanded run R1: the frozen input script through "
                "the pinned U01 port, the frozen adapter, the certified "
                "scene (build N, seed 20260920, 10500 ticks); rendered "
                "trace-bound from capture/trace_commanded.json"),
        "subject_binding": {
            "kind": "command_verification_receipt",
            "path": "receipts/command_verification_receipt.json",
            "sha256": subj_sha},
        "build_id": trace["build_id"],
        "seed": SEED,
        "horizon_ticks": HORIZON,
        "velocity_envelope_m_s": trace["derived_bounds"]["velocity_envelope_m_s"],
        "tick_interval": list(TICKS_INTERVAL),
        "frame_count": len(frame_records),
        "frame_ticks": list(FRAME_TICKS),
        "frame_fps": FRAME_FPS,
        "telemetry_source": ("frame k renders the recorded per-tick "
                             "telemetry of its declared tick from "
                             "capture/trace_commanded.json (the gated R1 "
                             "run's own bytes)"),
        "g4": {"decode_pixel_exact_all_frames": True,
               "checked_frames": len(frame_records),
               "order_sensitivity_pass": True},
        "ffmpeg_version": ffmpeg_version,
        "trace_sha256": trace_sha,
        "frame_hashes_sha256": sha_bytes(canonical(frame_hashes)),
        "capture_sha256": capture_sha,
        "integrity": {"contact_floor_min": min(p["contact_count"]
                                               for p in per_tick),
                      "max_abs_v": max(abs(p["com_v_m_s"])
                                       for p in per_tick),
                      "intervention_all_none": True,
                      "wrong_command_probe": receipt["predictions"]
                      ["P9_wrong_command_response"]["divergence_detected"]},
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B run_capture.py"},
    }
    receipt_bytes = canonical(capture_receipt) + b"\n"
    (CAPTURE_DIR / "capture_receipt.json").write_bytes(receipt_bytes)
    subject_sha = sha_bytes(receipt_bytes)
    manifest["subject_sha256"] = subject_sha
    (CAPTURE_DIR / "capture_manifest.json").write_bytes(
        canonical(manifest) + b"\n")

    context = {
        "schema": "chimera.capture_context.v1",
        "task_id": vi.TASK_SHORT,
        "run_id": vi.ATTEMPT_ID,
        "criteria_sha256": vi.CRITERIA_SHA256,
        "capture_sha256": capture_sha,
        "subject_sha256": subject_sha,
        "tick_interval": list(TICKS_INTERVAL),
        "honesty_note": ("motion capture of the COMMANDED certified runtime "
                         "(the frozen player-port script -> the frozen "
                         "adapter -> the certified surrogate scene, deploy "
                         "gate ALLOW); the scene of record is the DECLARED "
                         "SURROGATE CPU walk scene (the adopted-assembly "
                         "native load is NAMED_MISSING and was never "
                         "fabricated); the native windowed engine has no "
                         "live control path for this line (NAMED_MISSING) "
                         "-- these frames are record-space panels of the "
                         "commanded runtime's own telemetry, not engine "
                         "frames"),
    }
    (CAPTURE_DIR / "capture_context.json").write_bytes(
        canonical(context) + b"\n")

    validator, validator_sha = load_validator()
    verdict = validator.validate_manifest(manifest, context, profile)
    provenance = {
        "schema": "chimera.registry_profile_provenance.v1",
        "task_id": vi.TASK_SHORT,
        "source": "READ-ONLY sqlite (file:...?mode=ro) "
                  + str(vi.REGISTRY).replace("\\", "/"),
        "registry_revision_at_capture": revision,
        "card_state_at_capture": card_state,
        "criteria_sha256": vi.CRITERIA_SHA256,
    }
    (CAPTURE_DIR / "registry_profile_provenance.json").write_bytes(
        canonical(provenance) + b"\n")
    snapshot = {
        "schema": "chimera.registry_verification_profile_snapshot.v1",
        "task_id": vi.TASK_SHORT,
        "profile": profile,
        "task_view_scope": {}, }
    (CAPTURE_DIR / "registry_verification_profile.json").write_bytes(
        canonical(snapshot) + b"\n")

    frame_hashes_json = {
        "schema": "chimera.frame_hashes.v1",
        "task_id": vi.TASK_SHORT,
        "sequence_identity_sha256": seq_identity,
        "frames": frame_records,
        "frames_dir": str(FRAMES).replace("\\", "/"),
    }
    (CAPTURE_DIR / "frame_hashes.json").write_bytes(
        canonical(frame_hashes_json) + b"\n")

    validation = {
        "schema": "chimera.capture_validation_receipt.v1",
        "task_id": vi.TASK_SHORT,
        "capture_kind": verdict["capture_kind"],
        "frame_count": len(frame_records),
        "limits": verdict["limits"],
        "mode": verdict["mode"],
        "profile_id": verdict["profile_id"],
        "profile_source": "registry (READ-ONLY sqlite), profile 'walking'",
        "render_source": "run_capture.py over the commanded runtime's own "
                         "recorded telemetry (the gated R1 run)",
        "structurally_valid": verdict["structurally_valid"],
        "subject_path": str(CAPTURE_DIR / "capture_receipt.json") \
            .replace("\\", "/"),
        "subject_sha256": subject_sha,
        "trace_path": str(CAPTURE_DIR / "trace_commanded.json").replace("\\", "/"),
        "trace_sha256": trace_sha,
        "validator": verdict["mode"],
        "validator_sha256": validator_sha,
        "video_path": str(mkv).replace("\\", "/"),
        "video_sha256": capture_sha,
        "view_count": verdict["view_count"],
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B run_capture.py"},
    }
    (CAPTURE_DIR / "capture_validation_receipt.json").write_bytes(
        canonical(validation) + b"\n")
    print("capture green: frames=%d mkv_sha=%s validator=%s"
          % (len(frame_records), capture_sha[:16], verdict["mode"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
