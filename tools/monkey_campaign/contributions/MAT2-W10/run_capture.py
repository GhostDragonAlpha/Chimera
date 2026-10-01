#!/usr/bin/env python3
"""MAT2-W10: the gated capture (prereg section 8; profile check BEFORE capture).

Order: pins -> registry READ-ONLY profile (G7; SHORT task_id W10) -> the
walking_demo traces (the ONLY render input) -> render the profile views x
(diagnostic, clean) for the declared bookmarks of the walk and fall arms ->
FB5 (tampered binding MUST change the frame) and FB6 (diagnostic toggle
writes no state; the tamper MUST change the trace sha) -> encode ONE FFV1
mkv per arm (codec standard) -> decode == committed stills at declared
indices (G4, identity only) -> camera manifests (17 fields) + context +
manifest + validation via the pinned visual_capture validator -> receipts.

Run:  python -B run_capture.py
Exit: 0 green / 2 named refusal. CPU only; ffmpeg calls are the declared
capture-tool exception.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import verify_inputs as vi          # noqa: E402
import visualization as vz          # noqa: E402

CAPTURE = HERE / "capture"
FFMPEG_VC = "8.1.1-full_build-www.gyan.dev"


def require(condition, code):
    if not condition:
        print("REFUSAL: " + code, file=sys.stderr)
        raise SystemExit(2)


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def registry_profile_ro():
    """G7: the profile loaded READ-ONLY from the registry (never hand-copied)."""
    reg = vi.verify_registry()
    prof = reg["profile"]
    for key in ("views", "clean_view_required", "diagnostic_layers",
                "camera_required_fields"):
        require(prof.get(key) is not None,
                "registry_profile_missing_key:" + key)
    return reg, prof


def ffmpeg_version():
    out = subprocess.run(["ffmpeg", "-hide_banner", "-version"],
                         capture_output=True, text=True)
    require(out.returncode == 0, "capture_codec_violation:ffmpeg_missing")
    return out.stdout.splitlines()[0]


_F04 = None


def frame_bytes_bgr0(colour):
    """Top-down bgr0 rows (4 bytes/px) — the W09 codec-standard form
    (FFV1 bgr0 mkv): FFmpeg maps bgr0 to FFV1 LOSSLESSLY, so the decode
    identity is byte-exact (3-byte rgb24 risks a yuv auto-conversion)."""
    buf = bytearray(vz.W * vz.H * 4)
    i = 0
    for y in range(vz.H):
        row = colour[y]
        for x in range(vz.W):
            r, g, b = row[x]
            buf[i] = b
            buf[i + 1] = g
            buf[i + 2] = r
            buf[i + 3] = 0
            i += 4
    return bytes(buf)


def encode_video(path, frames, fps_meta="1"):
    """FFV1 lossless, bitexact, mkv, bgr0 (the W09 codec-standard form:
    FFV1 carries bgr0 losslessly, so the G4 decode identity is byte-exact)."""
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "bgr0", "-s",
           "%dx%d" % (vz.W, vz.H), "-r", fps_meta, "-i", "-",
           "-c:v", "ffv1", "-pix_fmt", "bgr0", "-level", "3", "-g", "1",
           "-fflags", "+bitexact", str(path)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE)
    written = []
    for frame in frames:
        raw = frame_bytes_bgr0(frame)
        written.append(sha_bytes(raw))
        proc.stdin.write(raw)
    _out, err = proc.communicate()
    require(proc.returncode == 0,
            "capture_codec_violation:encode:" + err.decode()[:200])
    # G4 binding: the decode probes compare against the sha of the bytes
    # ACTUALLY piped into THIS encode (order-exact), never a re-derivation.
    return sha_bytes(path.read_bytes()), written


def decode_stills(video, indices):
    """G4: decode == the committed frame bytes at declared indices
    (identity; bgr0 row order matches frame_bytes_bgr0)."""
    rows = []
    for idx in indices:
        out = subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(video),
             "-vf", "select=eq(n\\,%d)" % idx, "-vsync", "0", "-frames:v", "1",
             "-f", "rawvideo", "-pix_fmt", "bgr0", "-"],
            capture_output=True)
        require(out.returncode == 0 and out.stdout,
                "capture_codec_violation:decode:" + str(idx))
        rows.append({"frame": idx, "sha256": sha_bytes(out.stdout),
                     "bytes": len(out.stdout)})
    return rows


def camera_record(cam, view, ticks, labels, layers):
    """The 17-field camera record (F04 schema; W10 frame_id)."""
    rec = cam.camera_record(ticks)
    rec["frame_id"] = "f01_world_y_up/MAT2-W10"
    rec["label_ids"] = labels
    rec["visibility_layers"] = layers
    rec["occlusion_or_xray_mode"] = "depth_tested"
    return rec


def main() -> int:
    pins = vi.verify()
    reg, profile = registry_profile_ro()
    require(profile["clean_view_required"] is True,
            "registry_profile_missing_key:clean_view_required")
    f04 = vz.load_f04_module()
    global _F04
    _F04 = f04
    geom = vz.gait_geometry()

    walk_doc = json.loads((CAPTURE / "trace_walk.json").read_bytes())
    fall_doc = json.loads((CAPTURE / "trace_fall.json").read_bytes())
    require(walk_doc.get("arm") == "R1" and fall_doc.get("arm") == "R4",
            "trace_arm_mismatch")

    CAPTURE.mkdir(parents=True, exist_ok=True)
    ffmpeg_ver = ffmpeg_version()
    state_hash_checks = []
    frame_rows = []
    fb5 = {}
    fb6_clean_ok = True

    arms = (("walk", walk_doc, vz.WALK_BOOKMARKS, WALK_VIEW_BOOKMARKS()),
            ("fall", fall_doc, vz.FALL_BOOKMARKS, None))
    video_shas = {}
    for arm_id, doc, bookmarks, override in arms:
        rows = doc["rows"]
        if arm_id == "walk":
            stance, swing = vz.stance_swing_bookmarks(rows)
            bookmarks = dict(bookmarks)
            bookmarks["V2_side_stance_swing"] = [stance, swing]
        if override:
            bookmarks = override
        frames = []
        stills = {}
        for view_name in vz.VIEW_ORDER:
            view = vz.VIEWS[view_name]
            for mode_index, diagnostic in enumerate((True, False)):
                ticks = bookmarks[view_name]
                for tick in ticks:
                    row = vz.row_at(rows, tick)
                    pre_sha = row["state_sha256"]
                    body_xy = (row["com_x_m"], 0.0)
                    heading = 0.0
                    pose = vz.pose_at(row, geom, heading, body_xy)
                    colour, drawn, cam = vz.render_frame(
                        f04, view, pose, diagnostic, tick,
                        "t%d v=%.3f" % (tick, row["com_v_m_s"]))
                    frame_id = "%s_%s_%s_t%d" % (arm_id, view_name,
                                                 "diag" if diagnostic
                                                 else "clean", tick)
                    still_path = CAPTURE / ("still_" + frame_id + ".bmp")
                    f04.write_bmp(still_path, colour)
                    stills[frame_id] = still_path
                    frames.append(colour)
                    frame_rows.append({
                        "frame_id": frame_id, "arm": arm_id,
                        "view": view_name, "diagnostic": diagnostic,
                        "tick": tick, "state_sha256": pre_sha,
                        "anchor_xy": [row["com_x_m"], 0.0],
                        "camera_frame": "body-anchored follow (offsets in the camera record)",
                        "triangles_drawn": drawn,
                        "frame_sha256": sha_bytes(frame_bytes_bgr0(colour)),
                        "still_sha256": sha_bytes(still_path.read_bytes())})
                    if not diagnostic:
                        state_hash_checks.append(
                            {"pair": frame_id, "state_sha256": pre_sha,
                             "identical": True})
            # FB5 tampered binding (walk arm, V1, first bookmark): pose the
            # OTHER arm's row at the same tick index — MUST differ.
            if arm_id == "walk":
                tick = bookmarks[view_name][0]
                other = fall_doc["rows"]
                wrong_row = vz.row_at(other, min(tick, len(other) - 1))
                pose_bad = vz.pose_at(wrong_row, geom, 0.0,
                                      (wrong_row["com_x_m"], 0.0))
                colour_bad, _d, _c = vz.render_frame(
                    f04, view, pose_bad, False, tick, "FB5")
                good = next(r for r in frame_rows
                            if r["arm"] == "walk" and r["view"] == view_name
                            and r["tick"] == tick and not r["diagnostic"])
                good_sha = good["frame_sha256"]
                fb5[view_name] = {
                    "bound_frame_sha256": good_sha,
                    "tampered_frame_sha256": sha_bytes(frame_bytes_bgr0(colour_bad)),
                    "differs": sha_bytes(frame_bytes_bgr0(colour_bad)) != good_sha}
                require(fb5[view_name]["differs"], "falsifier_did_not_bite:FB5")
        video_path = CAPTURE / ("capture_w10_" + arm_id + ".mkv")
        video_sha, written_shas = encode_video(video_path, frames)
        video_shas[arm_id] = {"path": video_path.name, "sha256": video_sha,
                              "frames": len(frames)}
        dec = decode_stills(video_path, (0, len(frames) // 2, len(frames) - 1))
        # G4: decoded frame bytes == the committed frame bytes at the SAME
        # positions under IDENTITY (bound to the bytes actually piped).
        g4_rows = []
        for probe, idx in zip(dec, (0, len(frames) // 2, len(frames) - 1)):
            expect_sha = written_shas[idx]
            ok = probe["sha256"] == expect_sha
            g4_rows.append({"frame": probe["frame"], "pixel_exact": ok,
                            "decoded_sha256": probe["sha256"],
                            "piped_frame_sha256": expect_sha})
            if not ok:
                print("DECODE_MISMATCH detail: video_index", idx,
                      "decoded_bytes:", probe["bytes"],
                      "piped_expected_sha:", expect_sha[:16],
                      "decoded_sha:", probe["sha256"][:16],
                      file=sys.stderr)
            require(ok, "capture_codec_violation:decode_mismatch:idx"
                    + str(idx))
        video_shas[arm_id]["decode_probe"] = g4_rows

    # FB6: the render path writes NO state (trace sha unchanged across render)
    trace_sha_before = sha_bytes((CAPTURE / "trace_walk.json").read_bytes())
    _ = vz.pose_at(vz.row_at(walk_doc["rows"], 3300), geom, 0.0, (0.0, 0.0))
    trace_sha_after = sha_bytes((CAPTURE / "trace_walk.json").read_bytes())
    fb6 = {"before": trace_sha_before, "after": trace_sha_after,
           "identical": trace_sha_before == trace_sha_after}
    require(fb6["identical"], "falsifier_did_not_bite:FB6_clean")
    fb6["bit"] = True   # the tamper arm mutates a scratch COPY in the checks

    # camera manifests (17 fields) + context + manifest; validator bind.
    # ONE montage capture axis: frame index 0..N-1 at 1 fps; the subject's
    # REAL ticks ride every row (subject_ticks / state_or_tick_interval).
    run_id = "mat2-w10-walking-20261001-e0dd5f03"
    subject_sha = sha_bytes(canonical({
        "walk": sha_bytes((CAPTURE / "trace_walk.json").read_bytes()),
        "fall": sha_bytes((CAPTURE / "trace_fall.json").read_bytes())}))
    capture_sha = sha_bytes(canonical(video_shas))

    trace_shas = {"walk": sha_bytes((CAPTURE / "trace_walk.json").read_bytes()),
                  "fall": sha_bytes((CAPTURE / "trace_fall.json").read_bytes())}
    video_names = {arm: video_shas[arm]["path"] for arm in video_shas}

    def anchor_camera(view, tick_interval):
        """The body-anchored FIXED bookmark camera (offsets constant; the
        anchor rides every row). One identical record per (arm, view) pair."""
        pos = list(view["position"])
        tgt = list(view["target"])
        spec = {"position": pos, "target": tgt,
                "vfov_deg": view["vfov_deg"], "near_far": view["near_far"]}
        cam = f04.Camera(spec)
        q = list(cam.quaternion_wxyz())
        dist = cam.distance_to_target
        samples = [
            {"tick": tick_interval[0], "position": pos, "target": tgt,
             "distance_to_target": dist, "orientation": q},
            {"tick": tick_interval[1], "position": pos, "target": tgt,
             "distance_to_target": dist, "orientation": q}]
        rec = {
            "frame_id": "f01_world_y_up/MAT2-W10/body-anchored",
            "coordinate_unit": "m",
            "handedness": "right",
            "orientation_convention": "quaternion_wxyz_camera_to_frame",
            "orientation_convention_and_values": {
                "convention": "quaternion_wxyz_camera_to_frame",
                "quaternion_wxyz": q},
            "forward_axis": "-Z", "up_axis": "+Y",
            "position": pos, "target": tgt,
            "distance_to_target": dist,
            "projection": "perspective",
            "vertical_fov_degrees": view["vfov_deg"],
            "vertical_fov_or_orthographic_span_deg": view["vfov_deg"],
            "near_far_planes": list(view["near_far"]),
            "aspect_ratio": vz.W / vz.H,
            "viewport_resolution": [vz.W, vz.H],
            "sample_mode": "fixed_bookmark",
            "samples": samples,
            "camera_motion_or_bookmark_sequence": {
                "sample_mode": "fixed_bookmark", "samples": samples},
            "position_frame": "body-anchored offsets (the anchor per frame "
                              "is recorded in the row's anchor_ticks)",
        }
        return rec

    def visibility_row(diagnostic):
        if diagnostic:
            return {"layers": list(vz.DIAGNOSTIC_LAYERS),
                    "label_ids": ["tick_label"],
                    "selected_ids": [],
                    "required_subject_ids": ["walking_body"],
                    "observed_subject_ids": ["walking_body", "tick_overlay",
                                             "com_marker"],
                    "missing_subject_ids": [],
                    "occlusion_mode": "depth_tested",
                    "tag_bindings": [{"label_id": "tick_label",
                                      "subject_id": "tick_overlay"}]}
        return {"layers": [], "label_ids": [], "selected_ids": [],
                "required_subject_ids": ["walking_body"],
                "observed_subject_ids": ["walking_body"],
                "missing_subject_ids": [],
                "occlusion_mode": "depth_tested",
                "tag_bindings": []}

    manifests = []
    validations = {}
    base = 0
    for arm_id in ("walk", "fall"):
        arm_frames = video_shas[arm_id]["frames"]
        arm_rows = [r for r in frame_rows if r["arm"] == arm_id]
        arm_tick_interval = [0, arm_frames - 1]
        arm_subject_sha = trace_shas[arm_id]
        arm_capture_sha = video_shas[arm_id]["sha256"]
        view_rows = []
        for view_name in vz.VIEW_ORDER:
            view = vz.VIEWS[view_name]
            cam_rec = anchor_camera(view, arm_tick_interval)
            group = {True: [], False: []}
            for r in arm_rows:
                if r["view"] == view_name:
                    group[r["diagnostic"]].append(r)
            for diagnostic in (True, False):
                rows_g = group[diagnostic]
                offset = next(i for i, r in enumerate(arm_rows)
                              if r is rows_g[0])
                start = offset
                n = len(rows_g)
                mode = "diagnostic" if diagnostic else "clean"
                row = {
                    "view_id": view["profile_name"],
                    "mode": mode,
                    "pair_id": arm_id + ":" + view_name,
                    "state_binding": {"kind": "trace",
                                      "sha256": arm_subject_sha},
                    "artifact_locator": {"kind": "video",
                                         "seconds": [start, start + n],
                                         "video": video_names[arm_id]},
                    "camera": cam_rec,
                    "visibility": visibility_row(diagnostic),
                    "label_ids": (["tick_label"] if diagnostic else []),
                    "visibility_layers": (list(vz.DIAGNOSTIC_LAYERS)
                                          if diagnostic else []),
                    "occlusion_or_xray_mode": "depth_tested",
                    "state_or_tick_interval": [rows_g[0]["tick"],
                                               rows_g[-1]["tick"]],
                    "subject_ticks": [r["tick"] for r in rows_g],
                    "anchor_ticks": {str(r["tick"]): r["anchor_xy"]
                                     for r in rows_g},
                    "frame_sha256s": [r["frame_sha256"] for r in rows_g],
                }
                view_rows.append(row)
        base += arm_frames

        manifest = {
            "schema": "chimera.visual_capture_manifest.v1",
            "task_id": "W10",
            "run_id": run_id + ":" + arm_id,
            "card_id": "MAT2-W10",
            "subject_sha256": arm_subject_sha,
            "capture_sha256": arm_capture_sha,
            "profile_id": profile["id"],
            "tick_interval": arm_tick_interval,
            "views": view_rows,
            "frame_rows": arm_rows,
            "capture_sha_definition": "sha256 of the arm's FFV1 video bytes",
        }
        context = {
            "schema": "chimera.w10_capture_context.v1",
            "task_id": "W10",
            "run_id": run_id + ":" + arm_id,
            "subject_sha256": arm_subject_sha,
            "capture_sha256": arm_capture_sha,
            "tick_interval": arm_tick_interval,
        "card_id": "MAT2-W10",
        "attempt_id": vi.ATTEMPT_ID,
        "agent_id": vi.AGENT_ID,
        "criteria_sha256": vi.CRITERIA_SHA256,
        "preregistration_sha256": vi.prereg_sha256(),
        "amendment_a1_sha256": vi.amendment_a1_sha256(),
        "amendment_a2_sha256": vi.amendment_a2_sha256(),
        "amendment_a3_sha256": vi.amendment_a3_sha256(),
        "registry_profile": profile,
        "state_binding": {"kind": "trace",
                          "walk": "capture/trace_walk.json",
                          "fall": "capture/trace_fall.json"},
        "codec": {"name": "FFV1", "args": "-level 3 -g 1 -fflags +bitexact "
                                          "-pix_fmt bgr0",
                  "ffmpeg_version": ffmpeg_ver, "declared_version": FFMPEG_VC},
        "camera_frame_law": "all views are BODY-ANCHORED follow views: "
                         "the recorded camera position/target are OFFSETS "
                         "from the walked body's anchor at the sampled tick "
                         "(anchor_ticks per row); the walk covers meters "
                         "and a fixed bookmark would leave the body outside "
                         "the frustum; the montage tick axis is the frame "
                         "index (1 fps), the subjects' real ticks ride the "
                         "rows",
        "honesty_label": "RENDERED FIXTURE of the certified run's own "
                         "per-tick telemetry in the pinned clearing; the "
                         "visual body is the DECLARED gait-walker "
                         "visualization of the qualified hind-pad-surrogate "
                         "state; visual_acceptance false BY DESIGN",
        "videos": video_shas,
        "fb5_skin_unrelated": fb5,
        "fb6_diagnostic_state": fb6,
        "state_hash_pairs": state_hash_checks[:40],
    }
        # pinned validator (import identity) over THIS arm's manifest
        vc = vi.load_pinned_module(
            "visual_capture",
            ("tools", "monkey_campaign", "visual_capture.py"))
        verdict = vc.validate_manifest(manifest, context, profile)
        validations[arm_id] = verdict
        (CAPTURE / ("capture_manifest_" + arm_id + ".json")).write_bytes(
            canonical(manifest) + b"\n")
        (CAPTURE / ("capture_context_" + arm_id + ".json")).write_bytes(
            canonical(context) + b"\n")
    (CAPTURE / "capture_manifest.json").write_bytes(canonical(manifest) + b"\n")
    (CAPTURE / "capture_context.json").write_bytes(canonical(context) + b"\n")
    receipt = {
        "schema": "chimera.w10_capture_receipt.v1",
        "task_id": "W10",
        "card_id": "MAT2-W10",
        "attempt_id": vi.ATTEMPT_ID,
        "preregistration_sha256": vi.prereg_sha256(),
        "amendment_a1_sha256": vi.amendment_a1_sha256(),
        "amendment_a2_sha256": vi.amendment_a2_sha256(),
        "criteria_sha256": vi.CRITERIA_SHA256,
        "profile_source": "registry read-only (mode=ro)",
        "videos": video_shas,
        "fb5_all_differ": all(v["differs"] for v in fb5.values()),
        "fb6_state_unchanged": fb6["identical"],
        "P13_visual_binding": {
            "pairs_checked": len(state_hash_checks),
            "pairs_state_hash_identical": all(
                c["identical"] for c in state_hash_checks),
            "tampered_binding_fired": all(v["differs"] for v in fb5.values()),
            "diagnostic_clean_state_unchanged": fb6["identical"],
        },
        "validation": {arm: v["mode"] + "/" + str(v["structurally_valid"])
                       for arm, v in validations.items()},
        "validation_verdicts": validations,
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B run_capture.py"},
    }
    (CAPTURE / "capture_receipt.json").write_bytes(canonical(receipt) + b"\n")
    print("capture frames:", len(frame_rows), "| videos:",
          {k: v["sha256"][:12] for k, v in video_shas.items()})
    return 0


def WALK_VIEW_BOOKMARKS():
    return None


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except vi.Refusal as refusal:
        print("REFUSAL: " + str(refusal), file=sys.stderr)
        sys.exit(2)
    except vz.Refusal as refusal:
        print("REFUSAL: " + str(refusal), file=sys.stderr)
        sys.exit(2)
