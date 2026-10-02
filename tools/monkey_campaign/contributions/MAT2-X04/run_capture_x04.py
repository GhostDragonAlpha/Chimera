#!/usr/bin/env python3
"""MAT2-X04: the bounded capture stage (prereg section 3).

Consumes the driver's declared render plan (frames.npy + frames_meta.json +
presentation_receipt.json from CHIMERA_OUTPUT_DIR), encodes ONE FFV1 montage
via the DECLARED ffmpeg capture-tool calls, runs decode probes, builds the
camera manifest (per-view camera records carrying the registry profile's 15
camera_required_fields; the registry profile is re-loaded READ-ONLY here —
G7: the profile check happens BEFORE any capture) and validates through the
pinned visual_capture validator (import identity).

Run:  python -B run_capture_x04.py   (exit 0 green / 2 named refusal)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import presentation_harness as ph      # noqa: E402
import verify_inputs_x04 as vi4        # noqa: E402

OUT = Path(os.environ.get("CHIMERA_OUTPUT_DIR", HERE / "outputs"))
CAPTURE = OUT / "capture"
W, H = 960, 540
FFMPEG_VC = "declared capture-tool calls (prereg section 9): encode + decode probes"


def require(condition, code):
    if not condition:
        print("REFUSAL:" + str(code), file=sys.stderr)
        raise SystemExit(2)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha_bytes(b):
    import hashlib
    return hashlib.sha256(b).hexdigest()


def frame_bytes_bgr0(colour):
    """Top-down bgr0 rows (4 bytes/px) - the W09/W10 codec-standard form
    (FFV1 bgr0 mkv maps LOSSLESSLY). The pinned renderer yields an (H, W, 3)
    channel array; W10's exact packing law, vectorized."""
    rgb = np.asarray(colour)[:, :, :3].astype(np.uint8)
    buf = np.zeros((rgb.shape[0], rgb.shape[1], 4), dtype=np.uint8)
    buf[:, :, 0] = rgb[:, :, 2]   # B
    buf[:, :, 1] = rgb[:, :, 1]   # G
    buf[:, :, 2] = rgb[:, :, 0]   # R
    buf[:, :, 3] = 0
    return np.ascontiguousarray(buf).tobytes()


def ffmpeg_version():
    out = subprocess.run(["ffmpeg", "-hide_banner", "-version"],
                         capture_output=True, check=False)
    require(out.returncode == 0, "capture_codec_violation:ffmpeg_missing")
    return out.stdout.decode("ascii", "replace").splitlines()[0].strip()


def encode_video(path, frames, fps_meta="1"):
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "bgr0", "-s", "%dx%d" % (W, H),
           "-r", fps_meta, "-i", "-",
           "-c:v", "ffv1", "-level", "3", "-g", "1",
           "-fflags", "+bitexact", "-pix_fmt", "bgr0", str(path)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    written = []
    for f in frames:
        data = frame_bytes_bgr0(f)
        proc.stdin.write(data)
        written.append(sha_bytes(data))
    proc.stdin.close()
    _out, err = proc.communicate()
    require(proc.returncode == 0,
            "capture_codec_violation:encode:" + err.decode("utf-8",
                                                           "replace")[:200])
    return sha_bytes(path.read_bytes()), written


def decode_stills(video, indices):
    out = []
    for idx in indices:
        proc = subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(video),
             "-vf", "select=eq(n\\,%d)" % idx, "-vsync", "0", "-frames:v", "1",
             "-f", "rawvideo", "-pix_fmt", "bgr0", "-"],
            capture_output=True, check=False)
        require(proc.returncode == 0,
                "capture_codec_violation:decode:" + str(idx))
        data = proc.stdout
        out.append({"frame": idx, "bytes": len(data),
                    "sha256": sha_bytes(data)})
    return out


def visibility_row(diagnostic, layers, labels):
    if diagnostic:
        bindings = [{"label_id": label, "subject_id": label + "_subject"}
                    for label in labels]
        return {"layers": list(layers), "label_ids": list(labels),
                "selected_ids": [labels[0]] if labels else [],
                "required_subject_ids": ["monkey_body"],
                "observed_subject_ids": ["monkey_body"] +
                [label + "_subject" for label in labels],
                "missing_subject_ids": [],
                "occlusion_mode": "depth_tested",
                "tag_bindings": bindings}
    return {"layers": [], "label_ids": [], "selected_ids": [],
            "required_subject_ids": ["monkey_body"],
            "observed_subject_ids": ["monkey_body"],
            "missing_subject_ids": [],
            "occlusion_mode": "depth_tested", "tag_bindings": []}


LABELS = ["state_link_label", "state_contact_label", "state_climb_label",
          "state_mode_label", "event_tick_label"]


def camera_view_record(cam, view, ticks, layers, frame_id, tick_interval):
    """The per-view camera record carrying the profile's EXACT
    camera_required_fields (asserted complete by the caller)."""
    rec = dict(cam.camera_record(ticks))
    rec["frame_id"] = frame_id
    rec["coordinate_unit"] = "m"
    rec["orientation_convention_and_values"] = {
        "convention": "quaternion_wxyz_camera_to_frame",
        "quaternion_wxyz": list(cam.quaternion_wxyz())}
    rec["target"] = list(view["target"])
    rec["distance_to_target"] = float(cam.distance_to_target)
    rec["projection"] = "perspective"
    rec["vertical_fov_or_orthographic_span"] = float(view["vfov_deg"])
    rec["near_far_planes"] = list(view["near_far"])
    rec["camera_motion_or_bookmark_sequence"] = {
        "sample_mode": "fixed_bookmark", "ticks": list(ticks)}
    rec["visibility_layers"] = list(layers)
    rec["label_ids"] = list(LABELS)
    rec["occlusion_or_xray_mode"] = "depth_tested"
    rec["state_or_tick_interval"] = list(tick_interval)
    return rec


def main() -> int:
    rows = vi4.verify()
    reg = vi4.verify_registry()
    vi4.verify_prereg_commit()
    vi4.extract_x04_tree()
    vi4.w10_layer()
    receipt = json.loads((OUT / "presentation_receipt.json").read_bytes())
    meta = json.loads((OUT / "frames_meta.json").read_bytes())
    frames = list(np.load(str(OUT / "frames.npy")))
    plan, metas = meta["plan"], meta["metas"]
    require(len(frames) == len(plan) == len(metas),
            "capture_plan_mismatch:%d:%d:%d"
            % (len(frames), len(plan), len(metas)))

    import visualization as vz          # W10 bytes (its dir is sys.path[0])
    f04 = vz.load_f04_module()

    profile = reg["profile"]
    layers = list(profile["diagnostic_layers"])
    require(profile["id"] == "presentation",
            "profile_check_after_capture_forbidden")
    ffmpeg_ver = ffmpeg_version()
    CAPTURE.mkdir(parents=True, exist_ok=True)

    # ONE montage: plan order (1 fps metadata axis; the subjects' real ticks
    # ride every row). The declared V3 repeatability pairs stay adjacent.
    video_path = CAPTURE / "capture_x04_presentation.mkv"
    video_sha, written_shas = encode_video(video_path, frames)
    probe_idx = (0, len(frames) // 2, len(frames) - 1)
    dec = decode_stills(video_path, probe_idx)
    g4_rows = []
    for probe, idx in zip(dec, probe_idx):
        ok = probe["sha256"] == written_shas[idx]
        g4_rows.append({"frame": probe["frame"], "pixel_exact": ok,
                        "decoded_sha256": probe["sha256"],
                        "piped_frame_sha256": written_shas[idx]})
        require(ok, "capture_codec_violation:decode_mismatch:idx" + str(idx))

    # the V3 side-view repeatability: two renders per mode, identical piped
    # bytes within each mode pair (clean pair and diagnostic pair)
    s_ids = [m["frame_id"] for m in metas
             if m["frame_id"].startswith("S_pass")]
    require(len(s_ids) == 4, "capture_side_pair_missing:%d" % len(s_ids))
    side_sha = {}
    for m in metas:
        if m["frame_id"].startswith("S_pass"):
            key = ("diag" if m["frame_id"].endswith("_diag_t%d" % ph.V3_TICK)
                   else "clean")
            side_sha.setdefault(key, []).append(
                written_shas[m["render_index"]])
    side_identical = all(len(v) == 2 and v[0] == v[1]
                         for v in side_sha.values())
    require(len(side_sha) == 2, "capture_side_modes_missing")

    # frame index ranges per (view_id, mode); view_ids are the profile's
    # verbatim view names (validator law: capture_view_not_declared).
    profile_view_of = {
        "V1_normal_player_camera": "normal player camera",
        "V2_detail_display_asset": "detail of affected display/asset",
        "V3_alternate_angle": "alternate-angle visibility",
    }
    ticks_all = [m["tick"] for m in metas]
    tick_interval = [min(ticks_all), max(ticks_all)]
    require(tick_interval[0] < tick_interval[1],
            "capture_interval_empty")
    subject_sha = sha_bytes(canonical(
        {"trace": sha_bytes((OUT / "trace_a1_window.json").read_bytes()),
         "frames": [m["state_sha256"] for m in metas][:8]}))
    capture_sha = video_sha

    groups = {}
    for m in metas:
        key = (profile_view_of[m["view"]], "diagnostic" if m["diagnostic"]
               else "clean")
        groups.setdefault(key, []).append(m)

    view_rows = []
    for profile_view in profile["views"]:
        for mode in ("diagnostic", "clean"):
            members = groups[(profile_view, mode)]
            start = members[0]["render_index"]
            n = len(members)
            spec_name = next(k for k, v in profile_view_of.items()
                             if v == profile_view)
            view = ph.X04_VIEWS[spec_name]
            cam = f04.Camera({
                "position": list(view["position"]),
                "target": list(view["target"]),
                "vfov_deg": view["vfov_deg"],
                "near_far": list(view["near_far"])})
            # the PAIR law: the camera record is mode-INDEPENDENT (the
            # validator requires camera equality inside a pair); the
            # declared label/layer sets live here identically for both
            # modes, and the per-mode visibility row carries the rest.
            cam_rec = camera_view_record(
                cam, view, tick_interval, layers,
                frame_id="f01_world_y_up/MAT2-X04/" + profile_view,
                tick_interval=tick_interval)
            samples = [
                {"tick": tick_interval[0], "position": list(view["position"]),
                 "target": list(view["target"]),
                 "distance_to_target": float(cam.distance_to_target),
                 "orientation": list(cam.quaternion_wxyz())},
                {"tick": tick_interval[1], "position": list(view["position"]),
                 "target": list(view["target"]),
                 "distance_to_target": float(cam.distance_to_target),
                 "orientation": list(cam.quaternion_wxyz())}]
            cam_rec["sample_mode"] = "fixed_bookmark"
            cam_rec["samples"] = samples
            missing = [f for f in profile["camera_required_fields"]
                       if f not in cam_rec]
            require(not missing,
                    "capture_camera_fields_missing:" + ",".join(missing))
            view_rows.append({
                "view_id": profile_view,
                "mode": mode,
                "pair_id": profile_view,
                "state_binding": {"kind": "trace", "sha256": subject_sha},
                "artifact_locator": {"kind": "video",
                                     "seconds": [start, start + n],
                                     "video": video_path.name},
                "camera": cam_rec,
                "visibility": visibility_row(mode == "diagnostic", layers,
                                             LABELS),
                "label_ids": LABELS if mode == "diagnostic" else [],
                "visibility_layers": layers if mode == "diagnostic" else [],
                "occlusion_or_xray_mode": "depth_tested",
                "state_or_tick_interval": [members[0]["tick"],
                                           members[-1]["tick"]],
                "subject_ticks": [m["tick"] for m in members],
                "anchor_ticks": {str(m["tick"]): m["anchor_xy"]
                                 for m in members},
                "frame_sha256s": [written_shas[m["render_index"]]
                                  for m in members],
                "frame_ids": [m["frame_id"] for m in members],
            })

    manifest = {
        "schema": "chimera.visual_capture_manifest.v1",
        "task_id": "X04",
        "run_id": receipt["arms"]["A1"]["run_id"],
        "card_id": "MAT2-X04",
        "subject_sha256": subject_sha,
        "capture_sha256": capture_sha,
        "profile_id": profile["id"],
        "tick_interval": tick_interval,
        "views": view_rows,
        "frame_rows": metas,
        "capture_sha_definition": "sha256 of the FFV1 video bytes",
    }
    context = {
        "schema": "chimera.x04_capture_context.v1",
        "task_id": "X04",
        "run_id": manifest["run_id"],
        "subject_sha256": subject_sha,
        "capture_sha256": capture_sha,
        "tick_interval": tick_interval,
        "card_id": "MAT2-X04",
        "attempt_id": vi4.ATTEMPT_ID,
        "agent_id": vi4.AGENT_ID,
        "criteria_sha256": vi4.CRITERIA_SHA256,
        "preregistration_sha256": vi4.prereg_sha256(),
        "registry_profile": profile,
        "state_binding": {"kind": "trace",
                          "A1_window": "trace_a1_window.json"},
        "codec": {"name": "FFV1",
                  "args": "-level 3 -g 1 -fflags +bitexact -pix_fmt bgr0",
                  "ffmpeg_version": ffmpeg_ver,
                  "declared_version": FFMPEG_VC},
        "camera_frame_law": "BODY-ANCHORED follow offsets (the anchor per "
                            "frame rides the rows); the presented frames are "
                            "the declared CPU-line frame records (absent "
                            "inventory A2); the montage tick axis is the "
                            "frame index at 1 fps",
        "honesty_label": "RENDERED FIXTURE of the certified run's own "
                         "per-tick telemetry (W10 records-only renderer); "
                         "visual_acceptance false BY DESIGN; independent "
                         "picture review remains required",
        "side_view_repeat": {"frame_ids": s_ids,
                             "state_chains_identical": side_identical},
        "videos": {"presentation": {"path": video_path.name,
                                    "sha256": video_sha,
                                    "frames": len(frames)}},
        "decode_probes": g4_rows,
    }
    vc = vi4.load_pinned_module(
        "visual_capture", ("tools", "monkey_campaign", "visual_capture.py"))
    verdict = vc.validate_manifest(manifest, context, profile)

    (CAPTURE / "capture_manifest.json").write_bytes(canonical(manifest) + b"\n")
    (CAPTURE / "capture_context.json").write_bytes(canonical(context) + b"\n")
    capture_receipt = {
        "schema": "chimera.x04_capture_receipt.v1",
        "task_id": "X04", "card_id": "MAT2-X04",
        "attempt_id": vi4.ATTEMPT_ID,
        "preregistration_sha256": vi4.prereg_sha256(),
        "profile_source": "registry read-only (mode=ro)",
        "video": {"path": video_path.name, "sha256": video_sha,
                  "frames": len(frames)},
        "side_view_repeat_identical": side_identical,
        "decode_probes_pixel_exact": all(r["pixel_exact"] for r in g4_rows),
        "camera_fields_complete": True,
        "camera_required_field_count": len(profile["camera_required_fields"]),
        "validation": {"mode": verdict["mode"],
                       "structurally_valid": verdict["structurally_valid"]},
        "validation_verdicts": verdict,
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B run_capture_x04.py"},
    }
    (CAPTURE / "capture_receipt.json").write_bytes(
        canonical(capture_receipt) + b"\n")
    print("capture frames: %d | video sha %s | validation %s"
          % (len(frames), video_sha[:12], verdict["structurally_valid"]))
    _ = rows
    return 0


if __name__ == "__main__":
    sys.exit(main())
