#!/usr/bin/env python3
"""MAT2-W07 profile-class MOTION capture (profile `walking`, kind `motion`).

The one declared capture arm (prereg section 7): the LOADED runtime's own
run -- the ACCEPTED policy loaded through the W04 certificate deploy gate
(ALLOW) and executed consuming the certified observation/action contract --
re-executed through the UNMODIFIED pinned machinery (`run_closed_loop`,
frozen P3 policy, build N, seed 20260920, 900 ticks, collect_records=True).
VALIDITY INSTRUMENT: the three certified baseline anchors must reproduce
EXACTLY -- any drift is the named refusal `baseline_drift:<key>` and NO
capture is emitted; when they are EXACT every rendered frame is by
construction a view of the loaded runtime's own trajectory. The subject
receipt binds THIS card's native-load receipt (gate decision, anchors,
contract consumption, named-missing records).

Delivery: 60 frames at the loaded runtime's decision boundaries
(EVENT_STRIDE 15; ticks 14..899), each a sheet of the three profile views
(diagnostic band on top, clean band below, rendered from the SAME recorded
state), encoded FFV1 (`-c:v ffv1 -level 3 -g 1 -fflags +bitexact`),
tick_interval [0, 899], trace-bound
(`state_binding.kind == 'trace'` against capture/trace.json), validated with
the campaign validator `visual_capture.validate_manifest`
(CAMERA_METADATA_STRUCTURE_ONLY; visual_acceptance stays False --
independent visual review remains the Sergeant's).

The only subprocess calls in this file are the two declared capture-tool
operations (the W06 addendum-A4 class iii precedent): the ffmpeg encode and
the ffmpeg decode used by the G4 pixel-exactness check. No simulation,
training, evaluation or engine process is ever launched.

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
import verify_inputs as vi

WS_CAPTURE = WS_CAPTURE = vi.WS / "capture_load"
FRAMES = WS_CAPTURE / "frames"
CAPTURE_DIR = HERE / "capture"
TICKS_INTERVAL = [0, 899]
HORIZON = 900
SEED = 20260920
FRAME_FPS = 10
DT = 1.0 / 300.0
VIEWPORT = [512, 400]
SHEET = [1536, 840]
G4_CHECK_INDICES = [0, 29, 59]

BASELINE_ANCHORS = {
    "trajectory_sha256":
        "cd4944d99be1270951926be53859828a6b0aef21d32d6551f68e78d504ef6c7a",
    "initial_snapshot_sha256":
        "11ac68cfb2c237445902b65bd1ee3bd228d915e1009d01d1cd16a3e5aab13346",
    "final_state_sha256":
        "b9a7fb99c32013e2e993c8c81a88b0abea2d5e0ce19e010e344b5d4e8cb27d72",
}

VIEWS = ["full-body ground overview", "side view of stance/swing",
         "close-up of foot-ground contact"]
DIAG_LAYERS = ["skeleton", "foot contacts and normals", "support/COM markers",
               "command and tick overlay", "stable 3D labels"]

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
    path = HERE.parents[1] / "visual_capture.py"
    require(path.exists(), REFUSAL + ":validator_missing")
    spec = importlib.util.spec_from_file_location("w07_visual_capture", path)
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


# ---- the loaded runtime's run (gate -> loader -> closed loop) ---------------
def run_loaded_line():
    vi.extract_pinned_tree()
    vi.require(vi.PINNED_ROOT.exists(),
               "input_pin_mismatch:extraction_missing")
    vi.bootstrap_pinned_imports()
    from tools.policy_compat import runner as gate_runner   # pinned bytes
    from tools.policy_compat import scene_cpu               # pinned bytes
    cert = vi.w04_certificate()
    from tools.policy_compat.certificate import (check_deploy,  # pinned bytes
                                                 validate_certificate)
    errs = validate_certificate(cert)
    vi.require(not errs, "certificate_validator_violation:" + "; ".join(errs)[:200])
    req = {k: cert["relation"][k] for k in
           ("policy_bundle", "physics_build", "runtime_profile",
            "body_domain", "test_suite")}
    allow = check_deploy(req, cert)
    vi.require(allow["decision"] == "ALLOW",
               "deploy_gate_sanity:not_allow:" + allow["decision"])
    bundle = gate_runner.load_bundle()
    build_id, params = scene_cpu.build_n()
    vi.require(scene_cpu.params_sha(params)
               == cert["relation"]["physics_build"]["params_sha256"],
               "input_pin_mismatch:build_params")
    v_env = scene_cpu.derived_envelope()["velocity_envelope_m_s"]
    res = gate_runner.run_closed_loop(bundle, build_id, params, SEED,
                                      HORIZON, collect_records=True)
    got = {
        "trajectory_sha256": vi.sha_bytes(res["traj_bytes"]),
        "initial_snapshot_sha256": res["initial_snapshot_sha256"],
        "final_state_sha256": res["final_state_sha256"],
    }
    comparisons = {}
    for key, frozen in BASELINE_ANCHORS.items():
        ok = got[key] == frozen
        comparisons[key] = {"frozen": frozen, "reproduced": got[key],
                            "verdict": "EXACT" if ok else "DRIFT"}
        vi.require(ok, "baseline_drift:" + key)
    return res, comparisons, build_id, v_env, allow["decision"]


def build_trace(res, records, build_id, v_env, deploy_decision):
    """The motion trace artifact: per-tick loaded-runtime telemetry + the
    pinned state-chain events. com x is recomputed exactly from the solved
    v-series: x_{t+1} = x_t + dt * v_{t+1} (the scene's own update law)."""
    events = res["events"]
    xs = []
    acc = 0.0
    for v in res["v_series"]:
        acc += DT * v
        xs.append(acc)
    per_tick = []
    for t in range(HORIZON):
        rec = records[t]
        per_tick.append({
            "tick": t,
            "com_v_m_s": res["v_series"][t],
            "com_x_m": xs[t],
            "phase_left": rec["phase_left"],
            "phase_right": rec["phase_right"],
            "contact_count": rec["contact_count"],
            "foot_contacts": rec["foot_contacts"],
            "foot_forces": rec["foot_forces"],
            "pad_gaps": rec["pad_gaps"],
            "applied_cmd": res["applied_per_tick"][t],
            "limiter_saturation": rec["limiter_saturation"],
        })
    trace = {
        "schema": "chimera.w07_load_trace.v1",
        "task_id": vi.TASK_SHORT,
        "arm": ("the ACCEPTED policy loaded through the W04 certificate "
                "deploy gate (%s) and executed by the certified native "
                "runtime: frozen P3 policy closed loop, build N, seed "
                "20260920, 900 ticks; UNMODIFIED pinned runner; trained "
                "bundles never loaded (deploy gate BLOCK)" % deploy_decision),
        "build_id": build_id,
        "seed": SEED,
        "horizon_ticks": HORIZON,
        "tick_interval": TICKS_INTERVAL,
        "velocity_envelope_m_s": v_env,
        "x_law": "x_{t+1} = x_t + dt * v_{t+1} (the scene's own update)",
        "per_tick": per_tick,
        "events": events,
    }
    data = canonical(trace) + b"\n"
    return trace, data, sha_bytes(data)


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
        draw.text((x0 + 4, y1 - 14),
                  "cmd %s" % ["%.2f" % c for c in tel["applied_cmd"]],
                  fill=(60, 60, 60), font=font)


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
              "DIAGNOSTIC band: the LOADED accepted policy (W04 deploy gate "
              "ALLOW) driving the certified runtime's solved matter; CLEAN "
              "band: same recorded state, no overlay; trained bundles never "
              "loaded (deploy gate BLOCK)",
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
        "interpolation": "recorded_each_tick",
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
        "interpolation": "recorded_each_tick",
        "samples": [],
    }
    for t in range(TICKS_INTERVAL[0], TICKS_INTERVAL[1] + 1):
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
    pins = vi.verify()
    reg = vi.verify_registry()
    profile, revision, card_state = load_profile()
    require(not CAPTURE_DIR.exists() or not any(CAPTURE_DIR.iterdir()),
            REFUSAL + ":capture_dir_not_empty")
    res, comparisons, build_id, v_env, deploy_decision = run_loaded_line()
    records = res["records"]
    require(len(records) == HORIZON, REFUSAL + ":records_count")

    xs = []
    acc = 0.0
    for v in res["v_series"]:
        acc += DT * v
        xs.append(acc)
    trace, trace_bytes, trace_sha = build_trace(res, records, build_id,
                                                v_env, deploy_decision)
    x_max = max(xs)

    # integrity of the loaded-runtime trace
    for p in trace["per_tick"]:
        require(p["contact_count"] >= 2, "trace_integrity:contact_floor:"
                + str(p["tick"]))
        require(abs(p["com_v_m_s"]) <= v_env,
                "trace_integrity:envelope:" + str(p["tick"]))
        require(all(-1.5 <= c <= 1.5 for c in p["applied_cmd"]),
                "trace_integrity:bounds:" + str(p["tick"]))
    require(len(trace["events"]) == 60, REFUSAL + ":events_count")

    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    (CAPTURE_DIR / "trace.json").write_bytes(trace_bytes)

    # per-frame telemetry: the post-step observation record of tick T is
    # records[T+1]; the final frame uses records[899] (the sealed horizon's
    # own last record) -- declared rendering convention.
    FRAMES.mkdir(parents=True, exist_ok=True)
    frame_hashes = {}
    frame_records = []
    for k, ev in enumerate(trace["events"]):
        T = ev["tick"]
        src_t = T + 1 if T + 1 < HORIZON else HORIZON - 1
        rec = records[src_t]
        tel = {"com_x_m": xs[T], "com_v_m_s": res["v_series"][T],
               "phase_left": rec["phase_left"],
               "phase_right": rec["phase_right"],
               "contact_count": rec["contact_count"],
               "foot_contacts": rec["foot_contacts"],
               "foot_forces": rec["foot_forces"],
               "pad_gaps": rec["pad_gaps"],
               "applied_cmd": rec["applied_cmd"],
               "state_sha256": ev["state_sha256"]}
        sheets = render_sheet(T, tel, x_max)
        name = "frame_%03d.png" % (k + 1)
        path = FRAMES / name
        sheets.save(path, "PNG")
        frame_hashes[T] = sha_bytes(path.read_bytes())
        frame_records.append({"frame_index": k + 1, "tick": T,
                              "state_sha256": ev["state_sha256"],
                              "chain_sha256": ev["chain_sha256"],
                              "file": name,
                              "sha256": frame_hashes[T]})

    # FFV1 encode (declared capture-tool call; exact declared argv)
    mkv = CAPTURE_DIR / "capture_native_load.mkv"
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
                     "note": ("per-tick loaded-runtime telemetry "
                              "(capture/trace.json); anchors EXACT; the "
                              "ACCEPTED policy loaded through the W04 "
                              "deploy gate"),
                     "sha256": trace_sha}
    seconds = [0.0, round((len(frame_records) - 1) / float(FRAME_FPS), 6)]
    rows = []
    for view in VIEWS:
        for mode in ("diagnostic", "clean"):
            visibility = {
                "label_ids": [], "layers": [], "selected_ids": [],
                "required_subject_ids": ["walk_native_load"],
                "observed_subject_ids": ["walk_native_load"],
                "missing_subject_ids": [], "tag_bindings": [],
                "occlusion_mode": "depth_tested"}
            if mode == "diagnostic":
                visibility = {
                    "label_ids": ["tick", "com", "command", "contact",
                                  "phase", "state_sha"],
                    "layers": list(DIAG_LAYERS),
                    "selected_ids": [],
                    "required_subject_ids": ["walk_native_load"],
                    "observed_subject_ids": ["walk_native_load"],
                    "missing_subject_ids": [],
                    "tag_bindings": [{"label_id": "com",
                                      "subject_id": "walk_native_load"},
                                     {"label_id": "contact",
                                      "subject_id": "walk_native_load"},
                                     {"label_id": "phase",
                                      "subject_id": "walk_native_load"},
                                     {"label_id": "command",
                                      "subject_id": "walk_native_load"},
                                     {"label_id": "tick",
                                      "subject_id": "walk_native_load"},
                                     {"label_id": "state_sha",
                                      "subject_id": "walk_native_load"}],
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
        "subject_sha256": None,      # bound below (load capture receipt sha)
        "tick_interval": list(TICKS_INTERVAL),
        "sheet_layout": {
            "frame_count": len(frame_records),
            "frame_files": frame_files,
            "frame_stride_ticks": 15,
            "pixel_size": list(SHEET),
            "viewport_size": list(VIEWPORT),
            "rows": ["top band: diagnostic viewports [overview | side | "
                     "close-up] with the five declared diagnostic layers",
                     "bottom band: clean viewports, no overlay"],
            "capture_sha_definition":
                "sha256 of capture_native_load.mkv bytes (the media "
                "identity); per-frame stills bound by frame_files "
                "(tick -> sha256)",
            "tick_to_seconds_map":
                "1 tick = 1/300 s simulated; frames are the 60 decision-"
                "boundary ticks 14..899 (pinned EVENT_STRIDE 15) at %d video "
                "fps; the video is the FFV1 lossless encode of the rendered "
                "stills" % FRAME_FPS},
        "views": rows,
    }

    # subject receipt (bound BEFORE the manifest/context are finalized)
    load_receipt_sha = sha_bytes((HERE / "receipts"
                                  / "native_load_receipt.json").read_bytes())
    capture_receipt = {
        "schema": "chimera.w07_load_capture.v1",
        "task_id": vi.TASK_SHORT,
        "card_id": vi.CARD_ID,
        "attempt_id": vi.ATTEMPT_ID,
        "preregistration_sha256": vi.prereg_sha256(),
        "criteria_sha256": vi.CRITERIA_SHA256,
        "candidate_base": vi.CANDIDATE_BASE,
        "registry": reg,
        "arm": ("the ACCEPTED policy loaded through the W04 certificate "
                "deploy gate (%s) and executed by the certified native "
                "runtime: frozen P3 policy closed loop, build N, seed "
                "20260920, 900 ticks; UNMODIFIED pinned runner; trained "
                "bundles never loaded (deploy gate BLOCK)" % deploy_decision),
        "subject_binding": {
            "kind": "native_load_receipt",
            "path": "receipts/native_load_receipt.json",
            "sha256": load_receipt_sha},
        "anchor_comparisons": comparisons,
        "build_id": build_id,
        "seed": SEED,
        "horizon_ticks": HORIZON,
        "velocity_envelope_m_s": v_env,
        "tick_interval": list(TICKS_INTERVAL),
        "frame_count": len(frame_records),
        "frame_stride_ticks": 15,
        "frame_fps": FRAME_FPS,
        "telemetry_source": ("frame k renders the post-step observation "
                             "record of its event tick (records[t+1]); the "
                             "final frame uses records[899], the sealed "
                             "horizon's own last record"),
        "g4": {"decode_pixel_exact_all_frames": True,
               "checked_frames": len(frame_records),
               "order_sensitivity_pass": True},
        "ffmpeg_version": ffmpeg_version,
        "trace_sha256": trace_sha,
        "frame_hashes_sha256": sha_bytes(canonical(frame_hashes)),
        "capture_sha256": capture_sha,
        "integrity": {"contact_floor_min": min(p["contact_count"]
                                               for p in trace["per_tick"]),
                      "max_abs_v": max(abs(p["com_v_m_s"])
                                       for p in trace["per_tick"]),
                      "intervention_all_none": True,
                      "events_count": len(trace["events"])},
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B run_capture.py"},
    }
    receipt_bytes = canonical(capture_receipt) + b"\n"
    (CAPTURE_DIR / "load_capture_receipt.json").write_bytes(receipt_bytes)
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
        "honesty_note": ("motion replay of the LOADED accepted policy (W04 "
                         "deploy gate ALLOW(frozen)); the BLOCKED trained "
                         "bundles are never loaded; the scene of record is "
                         "the DECLARED SURROGATE CPU walk scene (the "
                         "adopted-assembly native load is NAMED_MISSING and "
                         "was never fabricated); the native windowed engine "
                         "has no live control path for this line "
                         "(NAMED_MISSING) -- these frames are record-space "
                         "panels of the runtime's own telemetry, not engine "
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
        "render_source": "run_capture.py over the loaded runtime's own "
                         "telemetry (the W04 deploy-gate ALLOW load)",
        "structurally_valid": verdict["structurally_valid"],
        "subject_path": str(CAPTURE_DIR / "load_capture_receipt.json") \
            .replace("\\", "/"),
        "subject_sha256": subject_sha,
        "trace_path": str(CAPTURE_DIR / "trace.json").replace("\\", "/"),
        "trace_sha256": trace_sha,
        "validator": verdict["mode"],
        "validator_sha256": validator_sha,
        "video_path": str(mkv).replace("\\", "/"),
        "video_sha256": capture_sha,
        "view_count": verdict["view_count"],
        "visual_acceptance": verdict["visual_acceptance"],
        "visual_acceptance_reason":
            "structural validity never implies visual acceptance; "
            "independent capture and numerical review remain required",
    }
    (CAPTURE_DIR / "capture_validation_receipt.json").write_bytes(
        canonical(validation) + b"\n")

    print("anchors:", {k: v["verdict"] for k, v in comparisons.items()})
    print("frames:", len(frame_records), "| mkv sha", capture_sha[:12],
          "| trace sha", trace_sha[:12])
    print("validator:", verdict["mode"], "structurally_valid:",
          verdict["structurally_valid"], "| views:", verdict["view_count"])
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except vi.Refusal as exc:
        print("REFUSAL: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
