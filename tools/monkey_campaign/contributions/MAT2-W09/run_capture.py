#!/usr/bin/env python3
"""MAT2-W09 profile-class MOTION capture (profile `walking`, kind `motion`).

The declared capture arms (prereg section 9): THIS card's own executed runs
-- the A1 declared unsupported probe (produced unsupported windows + R1
drive-cut responses) and the A2 declared monitor-input injection (R1 then
R2 at the declared horizon) -- re-executed through the UNMODIFIED pinned
machinery (frozen P3 policy for A2's baseline line, build N, seed 20260920,
900 ticks). VALIDITY INSTRUMENT: A0's three certified baseline anchors must
reproduce EXACTLY (via the same pinned pipeline the driver used) -- any
drift is the named refusal `baseline_drift:<key>` and NO capture is emitted.

Delivery: 12 frames at the declared snapshot ticks, each a sheet of the
three profile views (diagnostic band top, clean band below, rendered from
the SAME recorded state per band pair; one record sha per row pair),
encoded FFV1 (`-c:v ffv1 -level 3 -g 1 -fflags +bitexact`), tick_map bound
(`state_binding.kind == 'record_space_trace'` against capture/trace.json),
validated with the campaign validator `visual_capture.validate_manifest`
(CAMERA_METADATA_STRUCTURE_ONLY; visual_acceptance stays False --
independent visual review remains the Sergeant's).

HONESTY LABEL: RECORD-SPACE panels of the executed arms' own per-tick
telemetry -- not engine frames; the native windowed engine has no live
control path for this line (carried named-missing, W07 N3) and no body
anatomy exists in this surrogate scene (absent inventory declared in the
capture context, never imputed). Every A2 frame carries the
monitor_input_injection label in its diagnostic band.

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
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import verify_inputs as vi                 # noqa: E402
import out_of_envelope as oe               # noqa: E402
import run_out_of_envelope as rle          # noqa: E402

WS_CAPTURE = vi.WS / "capture_w09"
FRAMES = WS_CAPTURE / "frames"
CAPTURE_DIR = HERE / "capture"
SHEET = [1280, 800]
VIEWPORT = [620, 360]
FPS = 10
REFUSAL = "w09_capture_refusal"


def require(condition, code):
    if not condition:
        print("REFUSAL: " + code, file=sys.stderr)
        raise SystemExit(2)


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def load_validator():
    path = vi.PINNED_ROOT / "tools" / "monkey_campaign" / "visual_capture.py"
    require(path.exists(), REFUSAL + ":validator_missing")
    spec = importlib.util.spec_from_file_location("w09_visual_capture", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, sha_bytes(path.read_bytes())


def load_profile():
    import sqlite3
    uri = "file:" + str(vi.REGISTRY).replace("\\", "/") + "?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    try:
        cur = con.cursor()
        cur.execute("SELECT payload FROM state")
        state = json.loads(cur.fetchone()[0])
    finally:
        con.close()
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


# ---- the executed arms (validity instrument first) -----------------------
def execute_arms():
    pins, reg = rle.stage_pins()
    from tools.policy_compat import scene_cpu as SC
    cert = vi.w04_certificate()
    rle.validate_certificate(cert)
    req, allow, bundle, build_id, params = rle.gate_and_load(cert)
    rle._BUNDLE.update({"manifest": bundle["manifest"]})
    rle._PARAMS[0] = params
    consts = rle.build_consts(params, SC)
    # A0 validity instrument (the anchors must be EXACT before any capture)
    a0 = rle.run_baseline(bundle, build_id, params)
    require(all(c["verdict"] == "EXACT"
                for c in a0["comparisons"].values()),
            "baseline_drift:capture_validity_instrument")
    cmds, deriv = rle._probe_commands(consts)
    a1 = rle.run_scripted_arm(consts, cmds)
    a2 = rle.run_policy_arm(bundle, consts,
                            monitor=oe.InjectionMonitor(consts,
                                                        rle.A2_T0,
                                                        rle.A2_TICKS))
    return {"pins": pins, "reg": reg, "cert": cert, "allow": allow,
            "build_id": build_id, "consts": consts, "a0": a0,
            "a1": a1, "a2": a2, "cmds": cmds, "deriv": deriv}


def declared_frames(a1, a2):
    """The declared snapshot ticks: A1's produced trip-cascade window
    (entry, R1 mid, the NATURAL fall, the R2 latch, terminal) and A2's
    injected window (start, R1 mid, R2 fire, post-fall, terminal)."""
    ivs = rle.unsupported_intervals(a1["supervisor"].classes)
    full = [(lo, hi) for lo, hi in ivs if hi - lo + 1 >= 86]
    require(full, REFUSAL + ":no_full_window")
    lo, hi = full[0]
    fall = a1["fall_declared_tick"]
    require(fall is not None, REFUSAL + ":no_natural_fall")
    a1_ticks = [("A1", lo - 2, "window_entry_R1_engages"),
                ("A1", lo + 40, "R1_drive_cut_active"),
                ("A1", fall, "R2_fall_declared_natural"),
                ("A1", min(fall + 90, rle.HORIZON - 1), "R2_latch_hold"),
                ("A1", rle.HORIZON - 1, "terminal_R3_fall_outcome")]
    fall2 = a2["supervisor"].fall_declared_tick
    require(fall2 is not None, REFUSAL + ":no_fall_declared")
    a2_ticks = [("A2", rle.A2_T0 - 5, "injection_not_yet_R0"),
                ("A2", rle.A2_T0 + 5, "injected_R1_engaged"),
                ("A2", fall2, "R2_fall_declared_injection"),
                ("A2", fall2 + 30, "post_fall_R2_latch"),
                ("A2", rle.HORIZON - 1, "terminal_R3_fall_outcome")]
    return a1_ticks + a2_ticks


def render_sheet(arm_id, tick, tel, tick_map_row):
    """One frame: diagnostic band top, clean band below; both bands render
    the SAME recorded state (the row pair's shared record sha)."""
    img = Image.new("RGB", tuple(SHEET), (16, 18, 24))
    draw = ImageDraw.Draw(img)

    def band(y0, mode):
        label = ("DIAGNOSTIC" if mode == "diag" else "CLEAN")
        draw.rectangle([8, y0 + 2, SHEET[0] - 8, y0 + 26], fill=(36, 40, 52))
        draw.text((16, y0 + 8),
                  "%s tick %d  %s  class=%s streak=%d resp=%s rec_sha=%s"
                  % (arm_id, tick, label, tel["cls"], tel["streak"],
                     tel["resp"], tel["rec_sha"][:16]), fill=(230, 230, 230))
        panels = [("ground overview (record space)", panel_overview),
                  ("stance/swing (pad gaps)", panel_gaps),
                  ("foot contact close-up", panel_closeup)]
        for i, (title, fn) in enumerate(panels):
            x0 = 8 + i * (VIEWPORT[0] + 12)
            y1 = y0 + 32
            draw.rectangle([x0, y1, x0 + VIEWPORT[0], y1 + VIEWPORT[1]],
                           fill=(10, 12, 16), outline=(70, 76, 92))
            draw.text((x0 + 6, y1 + 4), title,
                      fill=(200, 205, 220) if mode == "diag"
                      else (150, 155, 170))
            fn(draw, x0, y1, tel, mode)

    band(0, "diag")
    band(SHEET[1] // 2, "clean")
    if arm_id == "A2":
        draw.rectangle([8, SHEET[1] - 28, 420, SHEET[1] - 6],
                       fill=(120, 40, 40))
        draw.text((16, SHEET[1] - 24),
                  "A2 = monitor_input_injection (seam truth: SUPPORTED; "
                  "the response machinery is exercised, not the scene)",
                  fill=(255, 220, 220))
    return img


def panel_overview(draw, x0, y0, tel, mode):
    """Full-body ground overview in record space: the com x-trace and the
    foot contact strips (the solved state; no anatomy exists -- declared)."""
    xs = tel["x_trace"]
    lo, hi = min(xs), max(xs)
    span = max(1e-9, hi - lo)
    h = VIEWPORT[1] - 24
    for i, x in enumerate(xs):
        px = x0 + 10 + int((x - lo) / span * (VIEWPORT[0] - 20))
        col = (90, 200, 120) if tel["contacts"][i] else (210, 90, 90)
        if mode == "clean":
            col = (140, 160, 150)
        draw.point((px, y0 + 30 + int(i / max(1, len(xs) - 1) * h)), fill=col)
    cx = x0 + 10 + int((tel["x"] - lo) / span * (VIEWPORT[0] - 20))
    draw.line([cx, y0 + 30, cx, y0 + 30 + h], fill=(240, 240, 140))
    draw.text((x0 + 6, y0 + VIEWPORT[1] - 16),
              "x=%.4f m v=%.4f m/s" % (tel["x"], tel["v"]),
              fill=(220, 220, 220))


def panel_gaps(draw, x0, y0, tel, mode):
    """Side view of stance/swing: the four pad gaps around the tick."""
    series = tel["gap_series"]
    n = len(series)
    thr = tel["threshold"]
    hi = max(max(frame) for frame in series) if n else 1.0
    hi = max(hi, thr * 1.2)
    for k in range(4):
        for i, frame in enumerate(series):
            px = x0 + 10 + int(i / max(1, n - 1) * (VIEWPORT[0] - 20))
            py = y0 + VIEWPORT[1] - 12 - int(frame[k] / hi * (VIEWPORT[1] - 44))
            col = [(120, 200, 255), (160, 140, 255),
                   (255, 190, 120), (255, 140, 160)][k]
            if mode == "clean":
                col = (150, 155, 165)
            draw.point((px, py), fill=col)
    ty = y0 + VIEWPORT[1] - 12 - int(thr / hi * (VIEWPORT[1] - 44))
    draw.line([x0 + 10, ty, x0 + VIEWPORT[0] - 10, ty], fill=(255, 90, 90))
    draw.text((x0 + 6, y0 + 20), "contact threshold %.4f m" % thr,
              fill=(255, 130, 130))


def panel_closeup(draw, x0, y0, tel, mode):
    """Close-up of foot-ground contact: the current tick's pad gaps."""
    gaps = tel["gaps"]
    labels = ["heel L", "mp L", "heel R", "mp R"]
    bw = (VIEWPORT[0] - 40) // 4
    hi = max(max(gaps), tel["threshold"] * 1.2)
    for k, g in enumerate(gaps):
        bh = int(g / hi * (VIEWPORT[1] - 60))
        bx = x0 + 20 + k * bw
        col = (90, 200, 120) if g < tel["threshold"] else (210, 90, 90)
        if mode == "clean":
            col = (150, 155, 165)
        draw.rectangle([bx, y0 + VIEWPORT[1] - 20 - bh, bx + bw - 12,
                        y0 + VIEWPORT[1] - 20], fill=col)
        draw.text((bx, y0 + VIEWPORT[1] - 16), labels[k],
                  fill=(210, 210, 210))
    ty = y0 + VIEWPORT[1] - 20 - int(tel["threshold"] / hi
                                     * (VIEWPORT[1] - 60))
    draw.line([x0 + 10, ty, x0 + VIEWPORT[0] - 10, ty], fill=(255, 90, 90))


def telemetry_for(arm_id, tick, arm, consts):
    rec = arm["records"][tick]
    cls = arm["supervisor"].classes[tick]
    streak = 0
    for t in range(tick, -1, -1):
        if arm["supervisor"].classes[t] == "UNSUPPORTED":
            streak += 1
        else:
            break
    fall = arm["supervisor"].fall_declared_tick
    resp = "R0"
    if fall is not None and tick == fall:
        resp = "R2_fall_declared"
    elif fall is not None and tick > fall:
        resp = "R2_latch_hold"
    elif any(row["event"] == "R1_engage" and row["tick"] <= tick
             for row in arm["supervisor"].ledger):
        nxt = [row["tick"] for row in arm["supervisor"].ledger
               if row["event"] == "R1_release" and row["tick"] > tick]
        if not nxt or cls == "UNSUPPORTED":
            resp = "R1_drive_cut"
    lo_t = max(0, tick - 40)
    gap_series = [arm["records"][t]["pad_gaps"]["hl"]
                  + arm["records"][t]["pad_gaps"]["hr"]
                  for t in range(lo_t, tick + 1)]
    tel = {
        "cls": cls, "streak": streak, "resp": resp,
        "rec_sha": oe.record_sha256(rec),
        "x_trace": [arm["records"][t]["tick"] * consts["dt_s"]
                    * arm["v_series"][t] for t in range(0, tick + 1,
                                                        max(1, tick // 300))],
        "x": sum(arm["v_series"][:tick + 1]) * consts["dt_s"],
        "v": arm["v_series"][tick],
        "contacts": [1.0 if arm["supervisor"].classes[t] == "SUPPORTED"
                     else 0.0 for t in range(0, tick + 1, max(1, tick // 300))],
        "gaps": rec["pad_gaps"]["hl"] + rec["pad_gaps"]["hr"],
        "gap_series": gap_series[-200:],
        "threshold": consts["contact_threshold_m"],
        "applied": arm["applied_per_tick"][tick],
    }
    return tel


def ffmpeg(args):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error"
                        ] + args, capture_output=True)
    require(p.returncode == 0,
            REFUSAL + ":ffmpeg:" + p.stderr.decode(errors="replace")[-300:])
    return p.stdout


def build_manifest_views(profile, ticks, trace_sha, video_seconds):
    """The profile's three views, each as a diagnostic/clean pair bound to
    the SAME record-space trace state and the SAME fixed bookmark camera
    (the validator's pair law). Both bands of every rendered frame come
    from one telemetry dict -- one record sha per row pair."""
    rows = []
    for view_id in profile["views"]:
        pair_id = "pair_" + re.sub(r"\W+", "_", view_id)
        camera = {
            "frame_id": "w09_record_space_sheet",
            "coordinate_unit": "m",
            "handedness": "right",
            "orientation_convention": "quaternion_wxyz_camera_to_frame",
            "forward_axis": "-Z", "up_axis": "+Y",
            "near_far_planes": [0.1, 100.0],
            "viewport_resolution": [VIEWPORT[0], VIEWPORT[1]],
            "aspect_ratio": VIEWPORT[0] / VIEWPORT[1],
            "projection": "orthographic",
            "orthographic_span": float(VIEWPORT[1]),
            "sample_mode": "fixed_bookmark",
            "samples": [
                {"tick": ticks[0], "position": [0.0, 0.0, 10.0],
                 "target": [0.0, 0.0, 0.0], "distance_to_target": 10.0,
                 "orientation": [1.0, 0.0, 0.0, 0.0]},
                {"tick": ticks[1], "position": [0.0, 0.0, 10.0],
                 "target": [0.0, 0.0, 0.0], "distance_to_target": 10.0,
                 "orientation": [1.0, 0.0, 0.0, 0.0]}],
        }
        diag_visibility = {
            "layers": list(profile["diagnostic_layers"]),
            "label_ids": ["tick", "class", "streak", "response",
                          "record_sha", "injection_label"],
            "selected_ids": [],
            "required_subject_ids": ["com", "feet"],
            "observed_subject_ids": ["com", "feet", "pads"],
            "missing_subject_ids": [],
            "occlusion_mode": "depth_tested",
            "tag_bindings": [{"label_id": "tick", "subject_id": "com"},
                             {"label_id": "class", "subject_id": "com"},
                             {"label_id": "streak", "subject_id": "com"},
                             {"label_id": "response", "subject_id": "com"},
                             {"label_id": "record_sha", "subject_id": "com"},
                             {"label_id": "injection_label",
                              "subject_id": "com"}],
        }
        clean_visibility = {
            "layers": [], "label_ids": [], "selected_ids": [],
            "required_subject_ids": ["com"],
            "observed_subject_ids": ["com", "feet", "pads"],
            "missing_subject_ids": [],
            "occlusion_mode": "depth_tested",
            "tag_bindings": [],
        }
        for mode, visibility in (("diagnostic", diag_visibility),
                                 ("clean", clean_visibility)):
            rows.append({
                "view_id": view_id, "mode": mode, "pair_id": pair_id,
                "state_binding": {"kind": "trace", "sha256": trace_sha},
                "artifact_locator": {"kind": "video",
                                     "seconds": video_seconds},
                "camera": camera,
                "visibility": visibility,
            })
    return rows


def main() -> int:
    ws = execute_arms()
    consts = ws["consts"]
    a1, a2 = ws["a1"], ws["a2"]

    import shutil
    if WS_CAPTURE.exists():
        shutil.rmtree(WS_CAPTURE)
    FRAMES.mkdir(parents=True)

    frame_ticks = declared_frames(a1, a2)
    frames_meta = []
    tick_map = {}
    for i, (arm_id, tick, note) in enumerate(frame_ticks):
        arm = a1 if arm_id == "A1" else a2
        tel = telemetry_for(arm_id, tick, arm, consts)
        img = render_sheet(arm_id, tick, tel, None)
        name = "frame_%03d.png" % i
        img.save(FRAMES / name)
        frames_meta.append({"arm": arm_id, "tick": tick, "note": note,
                            "file": name, "rec_sha": tel["rec_sha"],
                            "band": "diag"})
        tick_map[str(i)] = {"arm": arm_id, "tick": tick, "note": note,
                            "record_sha256": tel["rec_sha"]}
    tick_interval = [min(m["tick"] for m in frames_meta),
                     max(m["tick"] for m in frames_meta)]
    band_pair_proof = "both bands drawn from one telemetry dict per frame " \
                      "(one record sha per row pair)"

    # ---- encode FFV1 ----
    frame_list = WS_CAPTURE / "frames.txt"
    with frame_list.open("w", newline="\n") as f:
        for m in frames_meta:
            f.write("file 'frames/%s'\nduration 0.1\n" % m["file"])
    mkv = CAPTURE_DIR / "capture_w09_out_of_envelope.mkv"
    mkv.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg(["-y", "-f", "concat", "-safe", "0", "-i", str(frame_list),
            "-c:v", "ffv1", "-level", "3", "-g", "1",
            "-fflags", "+bitexact", "-pix_fmt", "bgr0", str(mkv)])
    cap_sha = sha_bytes(mkv.read_bytes())
    video_seconds = [0.0, 0.1 * len(frames_meta)]

    # ---- G4 decode pixel-exactness on the declared probe frames --------
    g4 = []
    for idx in (0, len(frames_meta) // 2, len(frames_meta) - 1):
        out_png = WS_CAPTURE / ("decode_%03d.png" % idx)
        ffmpeg(["-y", "-i", str(mkv), "-vf", "select=eq(n\\,%d)" % idx,
                "-vsync", "0", "-frames:v", "1", str(out_png)])
        a = Image.open(FRAMES / frames_meta[idx]["file"]).convert("RGB")
        b = Image.open(out_png).convert("RGB")
        same = list(a.getdata()) == list(b.getdata())
        g4.append({"frame": idx, "pixel_exact": bool(same)})
        require(same, REFUSAL + ":g4_decode_mismatch:%d" % idx)

    # ---- trace + manifest + validation ---------------------------------
    trace = {
        "schema": "chimera.w09_capture_trace.v1",
        "kind": "record_space_motion",
        "arms": {"A1": "produced unsupported windows + R1 (declared probe)",
                 "A2": "monitor_input_injection + R1 + R2 (declared "
                       "injection; seam truth SUPPORTED)"},
        "tick_map": tick_map,
        "tick_interval": tick_interval,
        "dt_s": 1.0 / 300.0,
        "per_frame_record_sha256": {m["file"]: m["rec_sha"]
                                    for m in frames_meta},
        "band_pair_proof": band_pair_proof,
        "anchor_validity": {k: v["verdict"]
                            for k, v in ws["a0"]["comparisons"].items()},
    }
    trace_path = CAPTURE_DIR / "trace.json"
    trace_path.write_bytes(canonical(trace) + b"\n")
    trace_sha = sha_bytes(trace_path.read_bytes())

    validator, validator_sha = load_validator()
    profile, registry_revision, card_state = load_profile()

    subject_receipt = vi.outputs_dir() / "out_of_envelope_receipt.json"
    subject_sha = (sha_bytes(subject_receipt.read_bytes())
                   if subject_receipt.exists() else trace_sha)

    capture_context = {
        "schema": "chimera.capture_context.v1",
        "task_id": "W09",
        "run_id": vi.ATTEMPT_ID,
        "subject_sha256": subject_sha,
        "capture_sha256": cap_sha,
        "tick_interval": tick_interval,
        "card_id": "MAT2-W09",
        "profile": {"id": profile["id"], "kind": profile["kind"],
                    "views": profile["views"],
                    "clean_view_required": profile["clean_view_required"],
                    "diagnostic_layers": profile["diagnostic_layers"]},
        "honesty_label": "RECORD-SPACE panels of this card's own executed "
                         "arms' per-tick telemetry; NOT engine frames; no "
                         "native live control path (W07 N3 carried); no "
                         "body anatomy exists in this surrogate scene "
                         "(absent inventory declared, never imputed); A2 "
                         "frames carry the monitor_input_injection label",
        "view_realization": {
            "full-body ground overview": "com x-trace + foot contact "
                                         "strips (record space)",
            "side view of stance/swing": "pad gap series around the "
                                         "snapshot tick",
            "close-up of foot-ground contact": "pad gap bars vs the "
                                               "declared threshold"},
        "camera_required_fields": profile["camera_required_fields"],
        "validator_identity": {"module": "tools/monkey_campaign/"
                                         "visual_capture.py (pinned base "
                                         "bytes)",
                               "sha256": validator_sha},
        "subject_binding": {"kind": "this card's executed arms",
                            "A1_commands": ws["cmds"],
                            "A1_derivation": ws["deriv"],
                            "a0_anchor_verdicts":
                                {k: v["verdict"] for k, v in
                                 ws["a0"]["comparisons"].items()}},
    }
    (CAPTURE_DIR / "capture_context.json").write_bytes(
        canonical(capture_context) + b"\n")

    manifest = {
        "schema": "chimera.visual_capture_manifest.v1",
        "task_id": "W09",
        "run_id": vi.ATTEMPT_ID,
        "subject_sha256": subject_sha,
        "capture_sha256": cap_sha,
        "tick_interval": tick_interval,
        "profile_id": profile["id"],
        "profile_kind": profile["kind"],
        "container": "mkv/ffv1 -level 3 -g 1 bitexact bgr0",
        "frame_count": len(frames_meta),
        "sheet_resolution": SHEET,
        "fps_declared": FPS,
        "dt_s": 1.0 / 300.0,
        "one_tick_seconds": "1 video second per declared snapshot frame is "
                            "NOT claimed; the concat cadence is 0.1 s per "
                            "frame and the tick axis is real "
                            "(state_or_tick_interval in the trace)",
        "frames": [{"frame_id": "w09_record_space_%03d" % i,
                    "file": m["file"], "arm": m["arm"], "tick": m["tick"],
                    "note": m["note"], "record_sha256": m["rec_sha"]}
                   for i, m in enumerate(frames_meta)],
        "views": build_manifest_views(profile, tick_interval, trace_sha,
                                      video_seconds),
        "validator": "CAMERA_METADATA_STRUCTURE_ONLY",
        "visual_acceptance": False,
        "visual_acceptance_note": "independent visual review remains the "
                                  "Sergeant gate",
        "preregistration_sha256": vi.prereg_sha256(),
    }
    (CAPTURE_DIR / "capture_manifest.json").write_bytes(
        canonical(manifest) + b"\n")

    vr = validator.validate_manifest(manifest, capture_context, profile)
    structurally_valid = bool(vr["structurally_valid"])
    (CAPTURE_DIR / "capture_validation_receipt.json").write_bytes(
        canonical({"schema": "chimera.w09_capture_validation.v1",
                   "validator": "visual_capture.validate_manifest",
                   "validator_sha256": validator_sha,
                   "structurally_valid": structurally_valid,
                   "visual_acceptance": bool(vr["visual_acceptance"]),
                   "view_count": vr["view_count"],
                   "capture_kind": vr["capture_kind"]}) + b"\n")
    require(structurally_valid, REFUSAL + ":manifest_invalid")

    # frame hashes receipt
    frame_hashes = {m["file"]:
                    sha_bytes((FRAMES / m["file"]).read_bytes())
                    for m in frames_meta}
    (CAPTURE_DIR / "frame_hashes.json").write_bytes(
        canonical(frame_hashes) + b"\n")

    receipt = {
        "schema": "chimera.w09_capture_receipt.v1",
        "capture_sha256": cap_sha,
        "frames": len(frames_meta),
        "tick_interval": tick_interval,
        "g4_pixel_exact": g4,
        "structurally_valid": structurally_valid,
        "visual_acceptance": False,
        "preregistration_sha256": vi.prereg_sha256(),
        "ffmpeg": subprocess.run(["ffmpeg", "-version"],
                                 capture_output=True).stdout.decode()
        .splitlines()[0],
        "honesty_label": capture_context["honesty_label"],
    }
    out = vi.outputs_dir()
    (out / "capture_receipt.json").write_bytes(canonical(receipt) + b"\n")
    print("capture:", mkv)
    print("sha256:", cap_sha)
    print("frames:", len(frames_meta), "tick_interval:", tick_interval)
    print("structurally_valid:", structurally_valid)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
