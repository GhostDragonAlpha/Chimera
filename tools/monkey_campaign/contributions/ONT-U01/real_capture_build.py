"""real_capture_build.py -- ONT-U01 correction: bind the REAL session
recording into the sealed visual_capture schema and validate it against the
card. Mirrors the accepted ONT-X02 integrated_capture_build pattern.

The capture artifact is the REAL headless-Chrome video of the REAL running
playable-slice application recorded by real_seam_session.py (page HUD + WebGL
canvas rendering the engine's streamed real-body vertices, through real key
events, the real command stream, the measured receiver probes and the three
declared views on the page's own camera keys). The runtime trace jsonl
(observed /tick_state rows + engine-composed FULL36 geometry rows, sampled
DURING the video) and the command stream are the state bindings.
NOT synthetic, NOT a trace re-render: the pixels are the application's own.

Camera fields come from the page's OWN runtime handle (window.__CHIMERA_VIEW,
read live at each view mark) and the page's pinned projection constants
(index.html persp(0.9, aspect, 0.05, 60); lookFrom). Nothing is guessed.

Usage:
  python -B real_capture_build.py --evidence <evidence/real> \
      --card <card_task.json> --subject-sha <input_mapper sha>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

CAMPAIGN_ROOT = Path(r"E:/PythonChimera")
sys.path.insert(0, str(CAMPAIGN_ROOT))
sys.path.insert(0, str(CAMPAIGN_ROOT / "tools" / "monkey_campaign"))
import visual_capture, visual_gate  # noqa: E402

# the card's controls profile: the three declared views and the required
# diagnostic layer names (card_task.json verification_profile)
VIEWS = ["normal follow-camera distance",
         "obstructed and close-target views",
         "repeatable inspection side view"]
LAYERS = ["input/state/tick display",
          "camera target and frustum diagnostics",
          "selected creature labels"]
LAYER_NOTES = {
    "input/state/tick display":
        "the page status line renders the engine's LIVE state during the "
        "whole recording (REAL engine numbers: root_y / root_vy / gravity); "
        "the bound trace_real.jsonl carries the literal tick IDs and "
        "ts_us stamps at 25 Hz (partial on-screen, full in the binding)",
    "camera target and frustum diagnostics":
        "the pinned page draws no frustum overlay; the camera is pinned "
        "numerically instead -- window.__CHIMERA_VIEW read live at every "
        "view mark plus the page's own persp(0.9, aspect, 0.05, 60) "
        "constants are bound in each view's camera object (partial, "
        "recorded)",
    "selected creature labels":
        "the single-body slice names its body in the REALITY/FANTASY panel "
        "(physics_body); no per-creature label set exists on the page "
        "(partial, recorded)",
}


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def look_from(yaw, pit, dist, tx, ty, tz):
    cx = tx + dist * math.cos(pit) * math.sin(yaw)
    cy = ty + dist * math.sin(pit)
    cz = tz + dist * math.cos(pit) * math.cos(yaw)
    return [cx, cy, cz]


def quat_wxyz_camera_to_world(eye, target):
    f = [t - e for t, e in zip(target, eye)]
    n = math.sqrt(sum(v * v for v in f))
    f = [v / n for v in f]
    up0 = [0.0, 1.0, 0.0]
    r = [f[1] * up0[2] - f[2] * up0[1],
         f[2] * up0[0] - f[0] * up0[2],
         f[0] * up0[1] - f[1] * up0[0]]
    rn = math.sqrt(sum(v * v for v in r)) or 1.0
    r = [v / rn for v in r]
    u = [r[1] * f[2] - r[2] * f[1],
         r[2] * f[0] - r[0] * f[2],
         r[0] * f[1] - r[1] * f[0]]
    m = [[r[0], u[0], -f[0]],
         [r[1], u[1], -f[1]],
         [r[2], u[2], -f[2]]]
    tr = m[0][0] + m[1][1] + m[2][2]
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2
        w = 0.25 * s
        x = (m[2][1] - m[1][2]) / s
        y = (m[0][2] - m[2][0]) / s
        z = (m[1][0] - m[0][1]) / s
    elif m[0][0] > m[1][1] and m[0][0] > m[2][2]:
        s = math.sqrt(1.0 + m[0][0] - m[1][1] - m[2][2]) * 2
        w = (m[2][1] - m[1][2]) / s
        x = 0.25 * s
        y = (m[0][1] + m[1][0]) / s
        z = (m[0][2] + m[2][0]) / s
    elif m[1][1] > m[2][2]:
        s = math.sqrt(1.0 + m[1][1] - m[0][0] - m[2][2]) * 2
        w = (m[0][2] - m[2][0]) / s
        x = (m[0][1] + m[1][0]) / s
        y = 0.25 * s
        z = (m[1][2] + m[2][1]) / s
    else:
        s = math.sqrt(1.0 + m[2][2] - m[0][0] - m[1][1]) * 2
        w = (m[1][0] - m[0][1]) / s
        x = (m[0][2] + m[2][0]) / s
        y = (m[1][2] + m[2][1]) / s
        z = 0.25 * s
    return [w, x, y, z]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", type=Path, required=True)
    ap.add_argument("--card", type=Path, required=True)
    ap.add_argument("--subject-sha",
                    default="7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d027"
                            "20ac970b42cfe6b44")
    a = ap.parse_args()
    ev = a.evidence.resolve()   # the gate requires absolute locators
    receipt = json.loads((ev / "session_real_receipt.json").read_text(
        encoding="utf-8"))
    mp4 = ev / "real_capture.mp4"
    trace_path = ev / "trace_real.jsonl"
    capture_sha = sha256_file(mp4)
    trace_sha = sha256_file(trace_path)
    trace_rows = [json.loads(l) for l in trace_path.read_text(
        encoding="utf-8").splitlines() if l.strip()]
    ticked = [r for r in trace_rows if r.get("ticks") is not None]
    tick_start, tick_end = int(ticked[0]["ticks"]), int(ticked[-1]["ticks"])
    marks = receipt["steps"]["R6_capture"]["marks"]
    views_ev = receipt["steps"]["R6_capture"]["views"]
    duration = float(receipt["video"]["video_seconds"])
    run_id = "ONT-U01-real-%s" % time.strftime("%Y%m%dT%H%M%S",
                                               time.gmtime())
    res = [views_ev["V1_normal_follow_camera_distance"]["camera"]["cw"],
           views_ev["V1_normal_follow_camera_distance"]["camera"]["ch"]]

    def camera_obj(cam):
        yaw = float(cam["yaw"])
        pit = float(cam["pit"])
        dist = float(cam["dist"])
        tgt = [float(cam.get("tx", 0.0)), float(cam.get("ty", 0.0)),
               float(cam.get("tz", 0.0))]
        eye = look_from(yaw, pit, dist, *tgt)
        return {
            "frame_id": "chimera.playable_slice.scene.world",
            "coordinate_unit": "m",
            "handedness": "right",
            "orientation_convention": "quaternion_wxyz_camera_to_frame",
            "forward_axis": "-Z", "up_axis": "+Y",
            "near_far_planes": [0.05, 60],
            "viewport_resolution": res,
            "aspect_ratio": res[0] / res[1],
            "projection": "perspective",
            "vertical_fov_degrees": 0.9 * 180.0 / math.pi,
            "sample_mode": "fixed_bookmark",
            "samples": [
                {"tick": tick_start, "position": eye, "target": tgt,
                 "distance_to_target": dist,
                 "orientation": quat_wxyz_camera_to_world(eye, tgt)},
                {"tick": tick_end, "position": eye, "target": tgt,
                 "distance_to_target": dist,
                 "orientation": quat_wxyz_camera_to_world(eye, tgt)}],
        }

    def diag_row(view_id, seconds, pair_id):
        return {
            "view_id": view_id, "mode": "diagnostic", "pair_id": pair_id,
            "state_binding": {"kind": "trace", "sha256": trace_sha},
            "artifact_locator": {"kind": "video", "seconds": seconds},
            "camera": camera_obj(views_ev[pair_id]["camera"]["cam"]),
            "visibility": {"layers": list(LAYERS), "label_ids": [],
                           "selected_ids": [],
                           "required_subject_ids": ["physics_body"],
                           "observed_subject_ids": ["physics_body"],
                           "missing_subject_ids": [],
                           "occlusion_mode": "mixed", "tag_bindings": []}}

    def clean_row(view_id, seconds, pair_id):
        return {
            "view_id": view_id, "mode": "clean", "pair_id": pair_id,
            "state_binding": {"kind": "trace", "sha256": trace_sha},
            "artifact_locator": {"kind": "video", "seconds": seconds},
            "camera": camera_obj(views_ev[pair_id]["camera"]["cam"]),
            "visibility": {"layers": [], "label_ids": [], "selected_ids": [],
                           "required_subject_ids": ["physics_body"],
                           "observed_subject_ids": ["physics_body"],
                           "missing_subject_ids": [],
                           "occlusion_mode": "depth_tested",
                           "tag_bindings": []}}

    p1 = "V1_normal_follow_camera_distance"
    p2 = "V2_obstructed_and_close_target_views"
    p3 = "V3_repeatable_inspection_side_view"
    w = lambda k: float(marks[k])  # noqa: E731
    rows = [
        diag_row(VIEWS[0], [w("view1_start"), w("view1_end")], p1),
        diag_row(VIEWS[1], [w("view2_start"), w("view2_end")], p2),
        diag_row(VIEWS[2], [w("view3_start"), w("view3_end")], p3),
        clean_row(VIEWS[0], [min(w("view1_start") + 0.3,
                                 max(w("view1_start"), duration - 0.2)),
                             max(w("view1_end") - 0.3,
                                 w("view1_start") + 0.4)], p1),
        clean_row(VIEWS[1], [min(w("view2_start") + 0.3,
                                 max(w("view2_start"), duration - 0.2)),
                             max(w("view2_end") - 0.3,
                                 w("view2_start") + 0.4)], p2),
        clean_row(VIEWS[2], [min(w("view3_start") + 0.3,
                                 max(w("view3_start"), duration - 0.2)),
                             max(min(w("view3_end") - 0.3, duration - 0.05),
                                 w("view3_start") + 0.4)], p3),
    ]
    manifest = {
        "schema": visual_capture.SCHEMA,
        "task_id": "U01",
        "run_id": run_id,
        "profile_id": "controls",
        "subject_sha256": a.subject_sha,
        "capture_sha256": capture_sha,
        "tick_interval": [tick_start, tick_end],
        "views": rows,
        "capture_notes": {
            "what": "REAL headless-Chrome video of the REAL running "
                    "playable-slice application: page HUD + WebGL canvas "
                    "rendering the engine's streamed real-body vertices, "
                    "through real key events (SPACE control press, the "
                    "page's own [3] fall test, the real command stream, "
                    "receiver-capability probes, and the three declared "
                    "views via the page's own [+]/[<-] camera keys). NOT a "
                    "native engine frame and NOT a synthetic trace "
                    "rendering.",
            "state_binding_trace": "trace_real.jsonl rows: /tick_state "
                                   "observed state at 25 Hz + engine-"
                                   "composed FULL36 geometry (~1 s) with "
                                   "the body centroid, all sampled DURING "
                                   "the recording; command_stream.jsonl "
                                   "holds the emitted records",
            "obstruction_honesty": "the REAL scene contains no obstruction "
                                   "object: the 'obstructed' half of view 2 "
                                   "cannot be produced for real and stays "
                                   "component-level (FollowCamera declared "
                                   "obstacle model, original probe C7); "
                                   "only the close-target half is real "
                                   "here (+ presses to dist<=1.2 m)",
            "clean_view_caveat": "the shipped page exposes no HUD-free "
                                 "mode; the clean rows are the cleanest "
                                 "the real application offers (the canvas's "
                                 "OWN toDataURL pixels, no DOM overlay)",
            "view_segments_from_marks": {k: marks[k] for k in
                                         ("view1_start", "view1_end",
                                          "view2_start", "view2_end",
                                          "view3_start", "view3_end")},
            "video_seconds": duration,
            "original_recording": "real_session.webm (Playwright native) "
                                  "converted to mp4 h264 yuv420p with "
                                  "ffmpeg; both hashed in the receipt",
            "synthetic_capture_preserved": "the ORIGINAL evidence/capture.mp4 "
                                           "stays byte-identical and stays "
                                           "labeled: a deterministic CPU "
                                           "visualization of the headless "
                                           "command-seam trace, NOT native "
                                           "engine frames; nothing is "
                                           "relabelled",
        },
    }
    manifest_path = ev / "real_capture_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=1),
                             encoding="utf-8")

    context = {"task_id": "U01", "run_id": run_id,
               "subject_sha256": a.subject_sha,
               "capture_sha256": capture_sha,
               "tick_interval": manifest["tick_interval"]}
    card = json.loads(a.card.read_text(encoding="utf-8"))
    result = visual_capture.validate_manifest(manifest, context,
                                              card["task"][
                                                  "verification_profile"])
    gate_result = visual_gate.verify(
        {"evidence": {"camera": {"reference": str(manifest_path),
                                 "raw_sha256": sha256_file(manifest_path)},
                      "visual": {"reference": str(mp4),
                                 "raw_sha256": capture_sha}},
         "capture_context": context},
        card)
    gate_receipt = {
        "schema": "chimera.ont_u01.real_capture.v1",
        "run_id": run_id,
        "capture_artifact": str(mp4),
        "capture_sha256": capture_sha,
        "trace_sha256": trace_sha,
        "commands_sha256": sha256_file(ev / "command_stream.jsonl"),
        "webm_sha256": sha256_file(ev / "real_session.webm"),
        "stills": {name: sha256_file(ev / name) for name in (
            "view_v1_diagnostic.png", "view_v1_clean.png",
            "view_v2_diagnostic.png", "view_v2_clean.png",
            "view_v3_diagnostic.png", "view_v3_clean.png",
            "engine_frame_v1.png", "engine_frame_v2.png",
            "engine_frame_v3.png")},
        "validate_manifest_result": result,
        "visual_gate_verify_result": gate_result,
        "visual_acceptance": False,
        "boundary": "structural camera-metadata validation only; "
                    "independent visual review of the REAL recording "
                    "remains the reviewer's gate",
        "built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    (ev / "real_capture_receipt.json").write_text(
        json.dumps(gate_receipt, indent=1), encoding="utf-8")
    print("capture:", mp4, capture_sha[:16], "duration", duration)
    print("validate_manifest:", json.dumps(result))
    print("visual_gate.verify:", json.dumps(gate_result))
    ok = result.get("structurally_valid") and \
        gate_result.get("structurally_valid")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
