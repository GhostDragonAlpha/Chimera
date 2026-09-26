"""integrated_capture_build.py -- ONT-X02: bind the REAL Session A recording
into the sealed visual_capture schema and validate it against the card.

The capture artifact is the REAL headless-Chrome video of the REAL running
playable-slice application (page HUD + WebGL canvas rendering the engine's
streamed real-body vertices), recorded by integrated_session_a.py through the
player entry controls (boot -> play -> [H] -> Shift+R restart -> settled).
The runtime trace jsonl (ticks/root_y/root_vy/boot_count/settled at 0.5 s)
recorded DURING the video is the state binding. NOT synthetic, NOT a trace
re-render: the pixels are the application's own output.

Camera fields come from the page's OWN runtime handle (window.__CHIMERA_VIEW,
read at both capture marks) and the page's pinned projection constants
(index.html: persp(0.9, aspect, 0.05, 60); lookFrom). Nothing is guessed.

The card's verification_profile is kind 'motion': the validator demands a
video artifact with trace bindings; this build complies (capture_kind video,
state_binding kind 'trace', per-view second windows measured from the marks).

Usage:
  python -B integrated_capture_build.py --evidence <dir> --card <card_task.json> \
         --session-a-receipt <session_a_receipt.json>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

# the campaign's own validators (canonical checkout; sparse attempt checkouts
# do not carry them). Overridable for review reruns.
CAMPAIGN_ROOT = Path(r"E:/PythonChimera")
sys.path.insert(0, str(CAMPAIGN_ROOT))
sys.path.insert(0, str(CAMPAIGN_ROOT / "tools" / "monkey_campaign"))
import visual_capture, visual_gate  # noqa: E402

RUN_ID = "ONT-X02-integrated-%s" % time.strftime("%Y%m%dT%H%M%S",
                                                 time.gmtime())


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def look_from(yaw: float, pit: float, dist: float,
              tx: float, ty: float, tz: float):
    """The page's own lookFrom (pinned index.html:188) -- camera EYE."""
    cx = tx + dist * math.cos(pit) * math.sin(yaw)
    cy = ty + dist * math.sin(pit)
    cz = tz + dist * math.cos(pit) * math.cos(yaw)
    return [cx, cy, cz]


def quat_wxyz_camera_to_world(eye, target):
    """Unit quaternion (w,x,y,z) mapping CAMERA coords -> WORLD frame for the
    OpenGL-style camera the page uses: +X right, +Y up, looks down -Z."""
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
    trace = m[0][0] + m[1][1] + m[2][2]
    if trace > 0:
        s = math.sqrt(trace + 1.0) * 2
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
    ap.add_argument("--session-a-receipt", type=Path, required=True)
    a = ap.parse_args()
    ev = a.evidence
    receipt_a = json.loads(a.session_a_receipt.read_text(encoding="utf-8"))

    mp4 = ev / "integrated_capture.mp4"
    trace_path = ev / "integrated_trace.jsonl"
    capture_sha = sha256_file(mp4)
    trace_sha = sha256_file(trace_path)
    trace_rows = [json.loads(l) for l in trace_path.read_text(
        encoding="utf-8").splitlines() if l.strip()]
    ticked = [r for r in trace_rows if r.get("ticks") is not None]
    tick_start, tick_end = ticked[0]["ticks"], ticked[-1]["ticks"]

    marks = receipt_a["steps"]["A5_capture"]["marks"]
    duration = float(receipt_a["steps"]["A5_capture"]["video_seconds"])
    guide_off = float(marks["help_toggled_off"])
    press = float(marks["restart_pressed"])
    settled = float(marks["recovered_settled"])

    v_before = receipt_a["steps"]["A3_after_restart"]["views_before"]
    v_after = receipt_a["steps"]["A3_after_restart"]["views_after"]
    res = [v_before["camera"]["cw"], v_before["camera"]["ch"]]

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
            "near_far_planes": [0.05, 60],   # pinned persp(0.9, a, 0.05, 60)
            "viewport_resolution": res,
            "aspect_ratio": res[0] / res[1],
            "projection": "perspective",
            "vertical_fov_degrees": 0.9 * 180.0 / math.pi,
            "sample_mode": "fixed_bookmark",
            "samples": [
                {"tick": int(tick_start), "position": eye, "target": tgt,
                 "distance_to_target": dist,
                 "orientation": quat_wxyz_camera_to_world(eye, tgt)},
                {"tick": int(tick_end), "position": eye, "target": tgt,
                 "distance_to_target": dist,
                 "orientation": quat_wxyz_camera_to_world(eye, tgt)},
            ],
        }

    LAYERS = ["state and tick IDs", "active skill/contact labels",
              "resource/session diagnostics"]
    LAYER_NOTES = {
        "state and tick IDs":
            "the page status line renders the engine's live state (REAL "
            "engine numbers - root_y / root_vy / gravity); literal tick IDs "
            "live in the bound trace jsonl, not on screen (partial, "
            "recorded)",
        "active skill/contact labels":
            "the objective line + keys card name the press/carry skills; at "
            "the standing start no skill is active to label (partial, "
            "recorded)",
        "resource/session diagnostics":
            "the page's REALITY/FANTASY panel names the resource/session "
            "state (render engine, physics_body, gravity, floor_contact, "
            "press, fall_test, camera, MOCK mock_carry, pending locomotion) "
            "and the beacon shows 'no page errors' (full)",
    }

    def rows(view_id, seconds, gx, pair_id):
        """The diagnostic row of one view (the clean pair row is appended
        separately with its own measured second window)."""
        visibility = {
            "layers": list(LAYERS),
            "label_ids": [],
            "selected_ids": [],
            "required_subject_ids": ["physics_body"],
            "observed_subject_ids": ["physics_body", "marker"],
            "missing_subject_ids": [],
            "occlusion_mode": "mixed",
            "tag_bindings": [],
        }
        cam_obj = camera_obj(v_before["camera"]["cam"] if gx == 0
                             else v_after["camera"]["cam"])
        return [{
            "view_id": view_id,
            "mode": "diagnostic",
            "pair_id": pair_id,
            "state_binding": {"kind": "trace", "sha256": trace_sha},
            "artifact_locator": {"kind": "video",
                                 "seconds": seconds},
            "camera": cam_obj,
            "visibility": visibility,
        }]

    # measured segments of the REAL recording (marks, seconds):
    #  V1 diagnostic: play live .. [H] pressed      (the page's guide open)
    #  V1 clean:      after [H] .. Shift+R          (guide hidden, same world)
    #  V2 diagnostic: Shift+R .. recovered+settled  (the RESTARTING pill and
    #                                               the world coming back)
    #  V2 clean:      settled .. end of recording   (guide still hidden)
    views = []
    views += rows("matched before/after camera bookmark",
                  [float(marks["play_live"]), guide_off], 0, "V1")
    views += rows("normal follow view during recovery",
                  [press, settled], 1, "V2")
    clean_extra = [
        {"view_id": "matched before/after camera bookmark",
         "mode": "clean", "pair_id": "V1",
         "state_binding": {"kind": "trace", "sha256": trace_sha},
         "artifact_locator": {"kind": "video",
                              "seconds": [guide_off + 1.0, press - 0.1]},
         "camera": camera_obj(v_before["camera"]["cam"]),
         "visibility": {"layers": [], "label_ids": [], "selected_ids": [],
                        "required_subject_ids": ["physics_body"],
                        "observed_subject_ids": ["physics_body", "marker"],
                        "missing_subject_ids": [],
                        "occlusion_mode": "depth_tested",
                        "tag_bindings": []}},
        {"view_id": "normal follow view during recovery",
         "mode": "clean", "pair_id": "V2",
         "state_binding": {"kind": "trace", "sha256": trace_sha},
         "artifact_locator": {"kind": "video",
                              "seconds": [min(settled + 0.2, duration - 0.2),
                                          duration - 0.05]},
         "camera": camera_obj(v_after["camera"]["cam"]),
         "visibility": {"layers": [], "label_ids": [], "selected_ids": [],
                        "required_subject_ids": ["physics_body"],
                        "observed_subject_ids": ["physics_body", "marker"],
                        "missing_subject_ids": [],
                        "occlusion_mode": "depth_tested",
                        "tag_bindings": []}},
    ]
    views += clean_extra

    manifest = {
        "schema": visual_capture.SCHEMA,
        "task_id": "X02",
        "run_id": RUN_ID,
        "profile_id": "recovery",
        "subject_sha256": receipt_a["steps"]["A1_boot"]["scene_sha256"],
        "capture_sha256": capture_sha,
        "tick_interval": [int(tick_start), int(tick_end)],
        "views": views,
        "capture_notes": {
            "what": "REAL headless-Chrome video of the REAL running "
                    "playable-slice application: page HUD + WebGL canvas "
                    "rendering the engine's streamed real-body vertices, "
                    "through the page's own [H] and [R] keys (boot -> play "
                    "-> help hidden -> FULL World.boot restart -> settled). "
                    "NOT a native engine frame and NOT a synthetic trace "
                    "rendering.",
            "state_binding_trace": "integrated_trace.jsonl rows (rel_s, "
                                   "ticks, root_y, root_vy, gravity_on, "
                                   "boot_count, settled) sampled at 0.5 s "
                                   "DURING the recording; sha256 is the "
                                   "binding of every view",
            "engine_camera_path_artifacts": {
                "engine_frame_before.png": receipt_a["steps"][
                    "A2_engine_frame_before"].get("sha256"),
                "engine_frame_after.png": receipt_a["steps"][
                    "A3_engine_frame_after"].get("sha256"),
                "note": "the ENGINE's own rendered frames fetched through "
                        "the server's /api/frame passthru (?w=640); "
                        "byte-identical before/after the restart (the "
                        "engine's own byte-clean reload, measured)",
            },
            "clean_view_caveat":
                "the shipped page exposes NO HUD-free mode; its [H] key "
                "dismisses the help guide (verified display:'none' in the "
                "receipt) but the status/objective/buttons chrome remains "
                "on every segment - the clean rows are the cleanEST the "
                "real application offers, recorded honestly",
            "clean_vs_diagnostic_identical_bytes_note":
                "element screenshots composite the DOM overlays and were "
                "MEASURED byte-identical to full-page shots; the still "
                "clean views therefore use the canvas's OWN toDataURL in "
                "the same rAF task as the page's draw",
            "view_segments_from_marks": {k: marks[k] for k in
                                         ("page_load", "play_live",
                                          "help_toggled_off",
                                          "restart_pressed",
                                          "recovered_settled")},
            "video_seconds": duration,
            "original_recording": "integrated_session.webm (Playwright "
                                  "native) converted to mp4 h264 yuv420p "
                                  "with ffmpeg; both hashed in the capture "
                                  "receipt",
        },
    }
    manifest_path = ev / "integrated_capture_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=1),
                             encoding="utf-8")

    # ── validate with the campaign validators (structural only) ─────────
    context = {"task_id": "X02", "run_id": RUN_ID,
               "subject_sha256": manifest["subject_sha256"],
               "capture_sha256": capture_sha,
               "tick_interval": manifest["tick_interval"]}
    profile = json.loads(a.card.read_text(encoding="utf-8"))["task"][
        "verification_profile"]
    result = visual_capture.validate_manifest(manifest, context, profile)
    # the visual_gate entry shape, against the SAME card contract
    gate_result = visual_gate.verify(
        {"evidence": {"camera": {"reference": str(manifest_path),
                                 "raw_sha256": sha256_file(manifest_path)},
                      "visual": {"reference": str(mp4),
                                 "raw_sha256": capture_sha}},
         "capture_context": context},
        json.loads(a.card.read_text(encoding="utf-8")))

    gate_receipt = {"schema": "chimera.ont_x02.integrated_capture.v1",
                    "run_id": RUN_ID,
                    "capture_artifact": str(mp4),
                    "capture_sha256": capture_sha,
                    "trace_sha256": trace_sha,
                    "webm_sha256": sha256_file(
                        ev / "integrated_session.webm"),
                    "stills": {name: sha256_file(ev / name) for name in
                               ("view_before_diagnostic.png",
                                "view_before_clean.png",
                                "view_after_diagnostic.png",
                                "view_after_clean.png",
                                "engine_frame_before.png",
                                "engine_frame_after.png")},
                    "state_bindings": {
                        "before": v_before["state_binding_sha256"],
                        "after": v_after["state_binding_sha256"]},
                    "validate_manifest_result": result,
                    "visual_gate_verify_result": gate_result,
                    "visual_acceptance": False,
                    "boundary": "structural camera-metadata validation "
                                "only; independent visual review of the "
                                "REAL recording remains the reviewer's "
                                "gate",
                    "built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                               time.gmtime())}
    (ev / "integrated_capture_receipt.json").write_text(
        json.dumps(gate_receipt, indent=1), encoding="utf-8")
    print("capture:", mp4, capture_sha[:16], "duration", duration)
    print("validate_manifest:", json.dumps(result))
    print("visual_gate.verify:", json.dumps(gate_result))
    ok = result.get("structurally_valid") and \
        gate_result.get("structurally_valid")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
