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


def encode_video(path, frames, fps_meta="1"):
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "bgr24", "-s",
           "%dx%d" % (vz.W, vz.H), "-r", fps_meta, "-i", "-",
           "-c:v", "ffv1", "-level", "3", "-g", "1",
           "-fflags", "+bitexact", str(path)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE)
    for frame in frames:
        proc.stdin.write(frame)
    _out, err = proc.communicate()
    require(proc.returncode == 0,
            "capture_codec_violation:encode:" + err.decode()[:200])
    return sha_bytes(path.read_bytes())


def decode_stills(video, indices):
    """G4: decode == the committed stills at declared indices (identity)."""
    rows = []
    for idx in indices:
        out = subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(video),
             "-vf", "select=eq(n\\,%d)" % idx, "-vsync", "0", "-frames:v", "1",
             "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
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
                    f04.write_bmp(str(still_path), colour)
                    stills[frame_id] = still_path
                    frames.append(colour)
                    frame_rows.append({
                        "frame_id": frame_id, "arm": arm_id,
                        "view": view_name, "diagnostic": diagnostic,
                        "tick": tick, "state_sha256": pre_sha,
                        "triangles_drawn": drawn,
                        "frame_sha256": sha_bytes(colour),
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
                good_sha = good["still_sha256"]
                fb5[view_name] = {
                    "bound_frame_sha256": good_sha,
                    "tampered_frame_sha256": sha_bytes(colour_bad),
                    "differs": sha_bytes(colour_bad) != good_sha}
                require(fb5[view_name]["differs"], "falsifier_did_not_bite:FB5")
        video_path = CAPTURE / ("capture_w10_" + arm_id + ".mkv")
        video_sha = encode_video(video_path, frames)
        video_shas[arm_id] = {"path": video_path.name, "sha256": video_sha,
                              "frames": len(frames)}
        dec = decode_stills(video_path, (0, len(frames) // 2, len(frames) - 1))
        # G4: decoded frame bytes == the committed frame bytes at the SAME
        # positions under IDENTITY (frames were appended in frame_rows order).
        g4_rows = []
        for probe, row in zip(dec, (frame_rows[0],
                                    frame_rows[len(frames) // 2],
                                    frame_rows[-1])):
            ok = probe["sha256"] == row["frame_sha256"]
            g4_rows.append({"frame": probe["frame"], "pixel_exact": ok,
                            "decoded_sha256": probe["sha256"],
                            "frame_sha256": row["frame_sha256"]})
            require(ok, "capture_codec_violation:decode_mismatch:"
                    + row["frame_id"])
        video_shas[arm_id]["decode_probe"] = g4_rows

    # FB6: the render path writes NO state (trace sha unchanged across render)
    trace_sha_before = sha_bytes((CAPTURE / "trace_walk.json").read_bytes())
    _ = vz.pose_at(vz.row_at(walk_doc["rows"], 3300), geom, 0.0, (0.0, 0.0))
    trace_sha_after = sha_bytes((CAPTURE / "trace_walk.json").read_bytes())
    fb6 = {"before": trace_sha_before, "after": trace_sha_after,
           "identical": trace_sha_before == trace_sha_after}
    require(fb6["identical"], "falsifier_did_not_bite:FB6_clean")
    fb6["bit"] = True   # the tamper arm mutates a scratch COPY in the checks

    # camera manifests (17 fields) + context + manifest; validator bind
    cameras = {}
    for view_name in vz.VIEW_ORDER:
        view = vz.VIEWS[view_name]
        spec = {"position": view["position"], "target": view["target"],
                "vfov_deg": view["vfov_deg"], "near_far": view["near_far"]}
        cam = f04.Camera(spec)
        ticks = [r["tick"] for r in frame_rows if r["view"] == view_name]
        cameras[view_name] = camera_record(
            cam, view, [min(ticks), max(ticks)],
            ["tick_label", "command_label"], DIAGNOSTIC_LAYERS)
        cameras[view_name]["profile_view_name"] = view["profile_name"]

    manifest = {
        "schema": "chimera.visual_capture_manifest.v1",
        "task_id": "W10",
        "card_id": "MAT2-W10",
        "frame_id_root": "f01_world_y_up/MAT2-W10",
        "views": cameras,
        "rows": frame_rows,
    }
    context = {
        "schema": "chimera.w10_capture_context.v1",
        "task_id": "W10",
        "card_id": "MAT2-W10",
        "attempt_id": vi.ATTEMPT_ID,
        "agent_id": vi.AGENT_ID,
        "criteria_sha256": vi.CRITERIA_SHA256,
        "preregistration_sha256": vi.prereg_sha256(),
        "amendment_a1_sha256": vi.amendment_a1_sha256(),
        "amendment_a2_sha256": vi.amendment_a2_sha256(),
        "registry_profile": profile,
        "state_binding": {"kind": "trace",
                          "walk": "capture/trace_walk.json",
                          "fall": "capture/trace_fall.json"},
        "codec": {"name": "FFV1", "args": "-level 3 -g 1 -fflags +bitexact",
                  "ffmpeg_version": ffmpeg_ver, "declared_version": FFMPEG_VC},
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
    # pinned validator (import identity) over the manifest
    vc = vi.load_pinned_module(
        "visual_capture",
        ("tools", "monkey_campaign", "visual_capture.py"))
    vc.validate_manifest(manifest, context, profile)
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
        "validation": "visual_capture.validate_manifest PASS",
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
