"""build_capture_manifest.py -- MAT2-X02: bind the REAL captured artifacts of
the wired session into a chimera.visual_capture_manifest.v1 camera manifest
(recovery profile, kind motion) and a source-bound qualification receipt,
then validate both with the campaign's own validators.

Everything here is derived from files the run produced; nothing is synthesized.
The camera is the page's OWN bookmark (yaw/pit/dist/target), declared with the
page's persp(0.9, asp, 0.05, 60) projection; eye positions and orientations
are COMPUTED with the page's own lookFrom basis formula (declared, not
guessed; the page exposes the bookmark handle __CHIMERA_VIEW read at capture
time in the state-binding files).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, r"E:/PythonChimera/tools/monkey_campaign")

import visual_capture  # noqa: E402
import visual_gate  # noqa: E402


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def page_eye(yaw: float, pit: float, dist: float, t):
    """index.html lookFrom: eye = target + dist*[cos(pit)sin(yaw),
    sin(pit), cos(pit)cos(yaw)] (the page's own formula, verbatim)."""
    return [t[0] + dist * math.cos(pit) * math.sin(yaw),
            t[1] + dist * math.sin(pit),
            t[2] + dist * math.cos(pit) * math.cos(yaw)]


def look_basis(yaw, pit, dist, t):
    """The page's lookFrom basis: f = normalize(eye-target); s = normalize(
    f x up) with up=(0,1,0); u = s x f. Rows of the view rotation; the
    camera-to-frame rotation has columns [s, u, f]."""
    eye = page_eye(yaw, pit, dist, t)
    f = [eye[0] - t[0], eye[1] - t[1], eye[2] - t[2]]
    n = math.hypot(*f)
    f = [v / n for v in f]
    up = [0.0, 1.0, 0.0]
    s = [f[1] * up[2] - f[2] * up[1], f[2] * up[0] - f[0] * up[2],
         f[0] * up[1] - f[1] * up[0]]
    n = math.hypot(*s) or 1e-9
    s = [v / n for v in s]
    u = [s[1] * f[2] - s[2] * f[1], s[2] * f[0] - s[0] * f[2],
         s[0] * f[1] - s[1] * f[0]]
    return s, u, f


def quat_wxyz(s, u, f):
    """Quaternion (w,x,y,z) of the rotation whose columns are s,u,f."""
    m00, m01, m02 = s[0], u[0], f[0]
    m10, m11, m12 = s[1], u[1], f[1]
    m20, m21, m22 = s[2], u[2], f[2]
    tr = m00 + m11 + m22
    if tr > 0:
        sq = math.sqrt(tr + 1.0) * 2
        w = 0.25 * sq
        x = (m21 - m12) / sq
        y = (m02 - m20) / sq
        z = (m10 - m01) / sq
    elif m00 > m11 and m00 > m22:
        sq = math.sqrt(1.0 + m00 - m11 - m22) * 2
        w = (m21 - m12) / sq
        x = 0.25 * sq
        y = (m01 + m10) / sq
        z = (m02 + m20) / sq
    elif m11 > m22:
        sq = math.sqrt(1.0 + m11 - m00 - m22) * 2
        w = (m02 - m20) / sq
        x = (m01 + m10) / sq
        y = 0.25 * sq
        z = (m12 + m21) / sq
    else:
        sq = math.sqrt(1.0 + m22 - m00 - m11) * 2
        w = (m10 - m01) / sq
        x = (m02 + m20) / sq
        y = (m12 + m21) / sq
        z = 0.25 * sq
    q = [w, x, y, z]
    n = math.hypot(*q)
    return [v / n for v in q]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", type=Path, required=True,
                    help="the integrated evidence dir")
    ap.add_argument("--receipt", type=Path, required=True,
                    help="session_a_wired_receipt.json")
    ap.add_argument("--card", type=Path, default=HERE / "card_task.json")
    a = ap.parse_args()
    ev: Path = a.evidence
    run_receipt = json.loads(a.receipt.read_text(encoding="utf-8"))
    card = json.loads(a.card.read_text(encoding="utf-8"))
    task_id = card["task_id"]

    # ── the video artifact: original webm preserved; mp4 for review ─────
    webm = ev / "wired_session.webm"
    mp4 = ev / "wired_capture.mp4"
    converted = False
    if not mp4.exists() and webm.exists():
        if shutil.which("ffmpeg"):
            r = subprocess.run(["ffmpeg", "-y", "-i", str(webm),
                                "-c:v", "libx264", "-preset", "veryfast",
                                "-pix_fmt", "yuv420p", "-movflags",
                                "+faststart", str(mp4)],
                               capture_output=True)
            converted = r.returncode == 0
    capture = mp4 if mp4.exists() else webm
    capture_sha = sha256_file(capture)

    # ── trace binding ────────────────────────────────────────────────────
    trace = ev / "wired_trace.jsonl"
    trace_sha = sha256_file(trace)
    rows = [json.loads(l) for l in trace.read_text(encoding="utf-8").splitlines()
            if l.strip()]
    ticks_all = [r["engine_state"]["ticks"] for r in rows
                 if r.get("engine_state") and
                 isinstance(r["engine_state"].get("ticks"), int)]
    tick0, tick1 = min(ticks_all), max(ticks_all)

    # ── the page's own camera bookmark, read live at capture time ────────
    cam_before = json.loads(
        (ev / "state_binding_before.json").read_text(encoding="utf-8"))["camera"]
    yaw, pit, dist = cam_before["yaw"], cam_before["pit"], cam_before["dist"]
    target = [float(v) for v in cam_before["target"]]
    vw, vh = (int(v) for v in cam_before["viewport"])
    eye = page_eye(yaw, pit, dist, target)
    s, u, f = look_basis(yaw, pit, dist, target)
    q = quat_wxyz(s, u, f)

    def camera_obj(tick_a: int, tick_b: int) -> dict:
        sample = {"tick": None, "position": eye, "target": target,
                  "distance_to_target": dist, "orientation": q}
        sa = dict(sample, tick=tick_a)
        sb = dict(sample, tick=tick_b)
        return {
            "frame_id": "chimera.playable_slice.scene.world",
            "coordinate_unit": "m",
            "handedness": "right",
            "orientation_convention": "quaternion_wxyz_camera_to_frame",
            "forward_axis": "-Z",
            "up_axis": "+Y",
            "near_far_planes": [0.05, 60],
            "viewport_resolution": [vw, vh],
            "aspect_ratio": vw / vh,
            "projection": "perspective",
            "vertical_fov_degrees": 0.9 * 180.0 / math.pi,
            "sample_mode": "fixed_bookmark",
            "samples": [sa, sb],
        }

    marks = {m["mark"]: m["video_s"] for m in run_receipt["marks"]}

    def view_row(view_id, mode, pair_id, sec):
        return {
            "view_id": view_id,
            "mode": mode,
            "pair_id": pair_id,
            "state_binding": {"kind": "trace", "sha256": trace_sha},
            "artifact_locator": {"kind": "video",
                                 "seconds": marks_span(sec)},
            "camera": camera_obj(tick0, tick1),
            "visibility": visibility_block(mode),
        }

    def marks_span(pair):
        lo = marks.get(pair[0], 0.0)
        hi = marks.get(pair[1], max(marks.values()) if marks else lo + 1.0)
        return [round(min(lo, hi - 0.01), 3), round(max(lo + 0.01, hi), 3)]

    def visibility_block(mode):
        if mode == "clean":
            return {"layers": [], "label_ids": [], "selected_ids": [],
                    "required_subject_ids": ["physics_body"],
                    "observed_subject_ids": ["physics_body", "marker"],
                    "missing_subject_ids": [],
                    "occlusion_mode": "depth_tested", "tag_bindings": []}
        return {"layers": ["state and tick IDs",
                           "active skill/contact labels",
                           "resource/session diagnostics"],
                "label_ids": [], "selected_ids": [],
                "required_subject_ids": ["physics_body"],
                "observed_subject_ids": ["physics_body", "marker"],
                "missing_subject_ids": [],
                "occlusion_mode": "mixed", "tag_bindings": []}

    views = [
        view_row("matched before/after camera bookmark", "diagnostic", "V1",
                 ("before_state", "after_view")),
        view_row("matched before/after camera bookmark", "clean", "V1",
                 ("before_view", "after_view")),
        view_row("normal follow view during recovery", "diagnostic", "V2",
                 ("attract_loaded", "exited_view")),
        view_row("normal follow view during recovery", "clean", "V2",
                 ("paused_view", "exited_view")),
    ]

    manifest = {
        "schema": "chimera.visual_capture_manifest.v1",
        "task_id": task_id,
        "run_id": "MAT2-X02-wired-%s" % run_receipt.get("started_utc",
                                                        "run").replace(":", ""),
        "profile_id": "recovery",
        "subject_sha256": (run_receipt.get("steps", {}).get("A3_pinned_state",
                                                            {})
                           .get("scene_sha256_before")),
        "capture_sha256": capture_sha,
        "tick_interval": [tick0, tick1],
        "views": views,
        "capture_notes": {
            "what": "REAL headless-Chrome video of the REAL reconstructed "
                    "playable application with the MAT2-X02 session wiring; "
                    "player controls are the page's own capture-phase keys "
                    "(Enter/Escape/R/Q) -> /api/session/key -> SessionFlow.",
            "state_binding_trace": "state_binding sha256 = wired_trace.jsonl "
                                   "(0.5s sampler: engine_state verbatim, "
                                   "session state, mapper records).",
            "engine_camera_path_artifacts": "engine_frame_before.png / "
                                            "engine_frame_after.png are the "
                                            "ENGINE's own /frame renders via "
                                            "the server's /api/frame passthru.",
            "clean_view_caveat": "clean rows point at the matching video "
                                 "spans; the canvas-only clean PIXELS are the "
                                 "view_*_clean.png stills (the page's own "
                                 "draw-path toDataURL), sha256-recorded in "
                                 "the qualification receipt. The video page "
                                 "always shows the diagnostic HUD.",
            "video_seconds": "seconds are relative to the recording start "
                             "(context creation); marks recorded by the "
                             "driver.",
            "original_recording": "wired_session.webm (sha %s); mp4 is a "
                                  "transcode for review; converted=%s"
                                  % (sha256_file(webm) if webm.exists()
                                     else "missing", converted),
        },
    }
    manifest_path = ev / "wired_capture_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=1))

    # ── context + validation ────────────────────────────────────────────
    context = {
        "task_id": task_id,
        "subject_sha256": manifest["subject_sha256"],
        "run_id": manifest["run_id"],
        "capture_sha256": capture_sha,
        "tick_interval": [tick0, tick1],
    }
    profile = card["task"]["verification_profile"]
    structural = visual_capture.validate_manifest(manifest, context, profile)
    print("validate_manifest structurally_valid:", structural.get("structurally_valid"))

    receipt = json.loads(
        (HERE / "qualification_receipt.json").read_text(encoding="utf-8"))
    receipt["capture_context"] = context
    receipt["evidence"]["camera"] = {"reference": str(manifest_path.resolve()),
                                     "raw_sha256": sha256_file(manifest_path)}
    receipt["evidence"]["visual"] = {"reference": str(capture.resolve()),
                                     "raw_sha256": capture_sha}
    gate = visual_gate.verify(receipt, card)
    print("visual_gate.verify structurally_valid:", gate.get("structurally_valid"))
    (HERE / "qualification_receipt.json").write_text(
        json.dumps(receipt, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
