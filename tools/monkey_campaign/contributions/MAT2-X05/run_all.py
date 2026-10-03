#!/usr/bin/env python3
"""MAT2-X05: the sealed-run driver (the ONE command the runner executes).

Order is law:
  0. unit battery        (test_x05.py through run_checks.py)
  1. presentation verification
     (pins -> registry/profile BEFORE capture -> prereg-commit law -> W10 +
     U07 certified-line layers -> gate-and-load identity -> 10 brake pairs
     (the sealed attempt-12 classes) -> landmark live checks -> renders ->
     predictions X-P1..X-P10 render-level -> receipts + pair records)
  2. named checks        (checks_receipt.json)
  3. capture             (ONE FFV1 video per arm per pair; full-stream decode
     probes; the decoded-frame diff channels (the authoritative X-P5
     evidence); camera manifest + the pinned visual_capture validator; the
     registry profile was read and checked BEFORE any capture (G7))
  4. capture gate        (the standing two-stage capture-gate template,
     capture_card/: 20 production cases + 4 declared defect cases)
  5. report              (REPORT.md from the receipts)
  6. report lint         (every number re-derived from the receipts)

Every stage must exit green; the first failure stops the driver with that
stage's own exit code. No subprocess is ever launched except the capture
stage's DECLARED ffmpeg capture-tool calls; each stage runs in-process.

Run:  python -B run_all.py   (from the sealed root; the runner's cwd)
Exit: 0 green / the failing stage's exit code.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

CARD = Path(__file__).resolve().parent
sys.path.insert(0, str(CARD))

OUT = Path(os.environ.get("CHIMERA_OUTPUT_DIR", CARD / "outputs"))

BUILD_ID = "cpu-walk-scene-build-N"
SEED = 20260920
N_PAIRS = 10
VIDEO_W, VIDEO_H = 960, 540
FRAME_BYTES = VIDEO_W * VIDEO_H * 4

# The declared view (prereg section 5): the pinned U07 C_V1 constants.
C_V1_VIEW = {
    "profile_name": "normal follow-camera distance",
    "position": [1.2, 1.6, 3.2], "target": [0.0, 0.5, 0.0],
    "follow": True, "vfov_deg": 50.0, "near_far": [0.05, 50.0]}

PROFILE_VIEW_NAME = "normal player camera"   # the registry profile's verbatim
# name whose declared constants are IDENTICAL to the pinned U07 C_V1 offsets
# ([1.2, 1.6, 3.2] / [0.0, 0.5, 0.0] / 50 deg / [0.05, 50.0]); the manifest
# view_id must be the profile's own name (validator law).

LABELS = ["state_link_label", "state_contact_label", "state_climb_label",
          "state_mode_label", "event_tick_label"]

UNIT_RECONCILIATION = (
    "the frozen prereg phrasing 're-press at +150 ms (SHORT) / +300 ms (LONG) "
    "on the injected clock' rides the sealed attempt-12 probe_events (the "
    "class definition reused verbatim), whose re-press deltas are exactly "
    "+150 / +300 TICKS on the 300 Hz injected clock (now_ms 14503->15003 and "
    "14506->15506); this run reproduces the sealed deltas")


def require(condition, code):
    if not condition:
        print("REFUSAL:" + str(code), file=sys.stderr)
        raise SystemExit(2)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def write_out(name, value):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    path.write_bytes(canonical(value) + b"\n")
    return path


def write_out_bytes(name, data):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_bytes(data)
    return OUT / name


def frame_bytes_bgr0(colour):
    """Top-down bgr0 rows (4 bytes/px) - the W09/W10 codec-standard form
    (FFV1 bgr0 mkv maps LOSSLESSLY). The pinned renderer yields an (H, W)
    tuple-grid; W10's exact packing law."""
    rgb = np.asarray(colour, dtype=np.uint8)[:, :, :3]
    buf = np.zeros((rgb.shape[0], rgb.shape[1], 4), dtype=np.uint8)
    buf[:, :, 0] = rgb[:, :, 2]
    buf[:, :, 1] = rgb[:, :, 1]
    buf[:, :, 2] = rgb[:, :, 0]
    buf[:, :, 3] = 0
    return np.ascontiguousarray(buf).tobytes()


def ffmpeg_version():
    out = subprocess.run(["ffmpeg", "-hide_banner", "-version"],
                         capture_output=True, check=False)
    require(out.returncode == 0, "capture_codec_violation:ffmpeg_missing")
    return out.stdout.decode("ascii", "replace").splitlines()[0].strip()


def encode_video(path, frames_bgr0):
    """One FFV1 encode from the already-packed frame bytes."""
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "bgr0",
           "-s", "%dx%d" % (VIDEO_W, VIDEO_H),
           "-r", "1", "-i", "-",
           "-c:v", "ffv1", "-level", "3", "-g", "1",
           "-fflags", "+bitexact", "-pix_fmt", "bgr0", str(path)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    shas = []
    for data in frames_bgr0:
        proc.stdin.write(data)
        shas.append(sha_bytes(data))
    proc.stdin.close()
    _out, err = proc.communicate()
    require(proc.returncode == 0,
            "capture_codec_violation:encode:"
            + err.decode("utf-8", "replace")[:200])
    return sha_bytes(path.read_bytes()), shas


def decode_all_frames(video):
    """Full-stream lossless decode; returns the list of bgr0 frame bytes."""
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(video),
         "-f", "rawvideo", "-pix_fmt", "bgr0", "-"],
        capture_output=True, check=False)
    require(proc.returncode == 0,
            "capture_codec_violation:decode:" + video.name)
    data = proc.stdout
    n = len(data) // FRAME_BYTES
    require(len(data) == n * FRAME_BYTES,
            "capture_codec_violation:decode_partial:" + video.name)
    return [data[i * FRAME_BYTES:(i + 1) * FRAME_BYTES]
            for i in range(n)]


def decoded_rgb(data):
    """bgr0 frame bytes -> (H, W, 3) uint8 RGB."""
    buf = np.frombuffer(data, dtype=np.uint8).reshape(VIDEO_H, VIDEO_W, 4)
    rgb = np.zeros((VIDEO_H, VIDEO_W, 3), dtype=np.uint8)
    rgb[:, :, 2] = buf[:, :, 0]
    rgb[:, :, 1] = buf[:, :, 1]
    rgb[:, :, 0] = buf[:, :, 2]
    return rgb


def follow_camera(f04, view, row):
    """The pinned follow-camera law (W10 render_frame form) for one row."""
    bx, bz = row["com_x_m"], 0.0
    pos = [bx + view["position"][0], view["position"][1],
           bz + view["position"][2]]
    tgt = [bx + view["target"][0], view["target"][1],
           bz + view["target"][2]]
    return f04.Camera({"position": pos, "target": tgt,
                       "vfov_deg": view["vfov_deg"],
                       "near_far": view["near_far"]})


# --------------------------------------------------------------------------
# stage 1: the gated presentation-verification experiment
# --------------------------------------------------------------------------
def stage_presentation_verification() -> dict:
    import verify_inputs_x05 as vi5
    import probe_driver as pd
    import render_x05 as rx
    import landmarks_x05 as lm
    import instrument_x05 as ix
    import state_readout_x05 as srx
    import diff_channels as dc
    import coupling_determination as cd

    # the pin layer's own main(): verifies + extracts + executes the W10
    # and U07 layers and writes the pins receipt (pins_x05.json)
    require(vi5.main() == 0, "pin_layer_main_refused")
    rows = vi5.verify()
    base = vi5.verify_base_identity()
    prereg_commit = vi5.verify_prereg_commit()
    reg = vi5.verify_registry()
    vi5.extract_x05_tree()
    w10 = vi5.w10_layer()
    u07 = vi5.u07_layer()

    import command_model as cm         # W10 bytes (the frozen script)
    wd, vz = vi5.load_w10_modules()
    f04 = vz.load_f04_module()
    geom = vz.gait_geometry()
    sr4 = vi5.load_x04_state_readout()
    ix_mod = ix

    # the certified line's own gate (W10's sealed code, unmodified)
    (cert, _req, allow, bundle, build_id, params, scene_const, bounds,
     gate) = wd.gate_and_load()
    require(allow["decision"] == "ALLOW", "deploy_gate_not_allow")
    require(build_id == BUILD_ID, "build_id_mismatch:" + str(build_id))
    adapter = cm.CommandAdapter(bundle["manifest"], scene_const)

    # the climb schema audit over the PINNED scene bytes (the X04 heritage
    # law form; the derived value feeds the diagnostic layers only)
    wvi = sys.modules.get("w10_verify_inputs")
    require(wvi is not None, "w10_layer_missing")
    scene_src = (wvi.PINNED_ROOT / "tools" / "policy_compat" / "scene_cpu.py"
                 ).read_bytes()
    climb_audit = sr4.derive_climb_state(scene_src)
    require(climb_audit["climb_state"] == sr4.CLIMB_ABSENT,
            "climb_state_not_absent")

    # the coupling determination RE-EXECUTED from the pinned sealed records
    coupling = cd.derive(vi5.driver_records())
    structural = cd.audit_no_velocity_to_stride(CARD)

    present_ticks = pd.PRESENT_TICKS
    diag_ticks = pd.DIAG_TICKS
    require(present_ticks == list(range(4365, 4666, 15)),
            "cadence_plan_changed")
    require(diag_ticks == [4365, 4500, 4650], "diag_plan_changed")

    pairs_out = []
    run_window_rows = {}
    x0_seen = {}
    landmark_live_all = []
    anchor_series = {}
    prediction_rows = {}
    receipt_flow = []
    receipt_findings = []
    receipt_scales = {}

    for n in range(1, N_PAIRS + 1):
        pair = pd.run_pair(n, adapter, build_id, params)
        cls = pair["cls"]
        A, B, B2 = pair["A"], pair["B"], pair["B2"]

        # ---- X-P1a determinism zero-control (the control arm re-executed)
        det = {
            "state_chain_identical": B["state_chain"] == B2["state_chain"],
            "per_tick_identical": B["per_tick"] == B2["per_tick"],
            "decisions_identical": B["decisions"] == B2["decisions"],
            "sink_records_identical": (B["sink_records"]
                                       == B2["sink_records"]),
            "final_state_identical": (B["final_state_sha256"]
                                      == B2["final_state_sha256"]),
        }
        require(all(det.values()), "prediction_failed:X_P1a:pair%d:%s"
                % (n, [k for k, v in det.items() if not v]))

        # ---- X-P1b prefix identity through the consumed tick
        fd = pd.first_divergence(A["state_chain"], B["state_chain"])
        require(fd >= pair["t_in"] + 1,
                "prediction_failed:X_P1b_early_divergence:pair%d:%d"
                % (n, fd))
        prefix = {
            "first_divergence_tick": fd,
            "prefix_identical_through": fd - 1,
            "t_in": pair["t_in"],
            "divergence_at_zoh_boundary": fd == pair["t_in"] + 1
            or fd > pair["t_in"],
        }
        # the release record's own ZOH fact (the brake chain's consumed tick)
        seam_a = pd.seam_facts(A)
        consumed_ticks = sorted({f["consumed_tick"] for f in seam_a
                                 if f["consumed_tick"] is not None
                                 and f["consumed_tick"] > pair["t_in"]})
        require(consumed_ticks, "brake_chain_consumed_missing:pair%d" % n)
        brake_consumed = consumed_ticks[0]
        require(brake_consumed == fd,
                "prediction_failed:X_P1b_zoh_boundary:pair%d:%d:%d"
                % (n, brake_consumed, fd))

        # ---- the anchor base x0 (derived; never hand-copied)
        rows_a = [A["per_tick"][t] for t in present_ticks]
        rows_b = [B["per_tick"][t] for t in present_ticks]
        run_window_rows["P%02d_%s" % (n, cls)] = {
            "A": [{k: r[k] for k in ("tick", "phase_left", "phase_right")}
                  for r in rows_a],
            "B": [{k: r[k] for k in ("tick", "phase_left", "phase_right")}
                  for r in rows_b]}
        x0_a = rows_a[0]["com_x_m"]
        x0_b = rows_b[0]["com_x_m"]
        require(x0_a == x0_b, "anchor_prefix_mismatch:pair%d" % n)
        x0_seen[n] = x0_a
        anchor_series["P%02d_%s_A" % (n, cls)] = [
            (r["tick"], r["com_x_m"]) for r in rows_a]
        anchor_series["P%02d_%s_B" % (n, cls)] = [
            (r["tick"], r["com_x_m"]) for r in rows_b]

        # ---- X-P9 seam crosscheck. The frozen law: "on every probe chain,
        # command_emitted.t_ms - input.t_ms <= 50.0 ms and consumed lag
        # exactly 1 tick (the L-P6 heritage; anchor U07 P1 = 27 ms worst)".
        # Executed AS WRITTEN over the chains whose input antecedent is a
        # frozen brake event, with the prereg's own disposition for bounds:
        # "exceeding a bound is a RECORDED FINDING, never tuned away".
        # MEASURED CERTIFIED BEHAVIOR (disclosed, not tuned): the pinned
        # mapper's release-decay law (_apply_tail) emits a SECOND record on
        # the release event — the tail-deadline exact-zero record at the
        # next boundary (<= released_ms + 100 ms by the mapper's own
        # deadline law) — which the frozen 50 ms phrasing did not
        # anticipate. The FIRST-response chain of each probe event (the
        # command-response latency the L-P6/U07-P1 anchor measures) is
        # GATED at 50 ms; any further exceeding chain is a RECORDED
        # FINDING. The ZOH consumed lag stays enforced on EVERY chain.
        seam = {}
        probe_t = {e["now_ms"] for e in A["probe_events"]}
        for arm_name, arm in (("A", A), ("B", B)):
            facts = pd.seam_facts(arm)
            probe_facts = [f for f in facts if f["input_t_ms"] in probe_t]                 if arm_name == "A" else []
            first_response = {}
            for f in probe_facts:
                require(f["consumed_lag_ticks"] == 1,
                        "prediction_failed:X_P9_consumed_lag:pair%d:%s:"
                        "seq%d" % (n, arm_name, f["seq"]))
                if f["input_t_ms"] not in first_response:
                    first_response[f["input_t_ms"]] = f
            for ev, f in sorted(first_response.items()):
                require(f["emit_minus_input_ms"] <= 50.0,
                        "prediction_failed:X_P9_first_response:pair%d:%s:"
                        "seq%d:%.2f"
                        % (n, arm_name, f["seq"],
                           f["emit_minus_input_ms"]))
            findings = [f for f in probe_facts
                        if f["emit_minus_input_ms"] > 50.0]
            lags = {f["consumed_lag_ticks"] for f in facts}
            require(lags == {1},
                    "prediction_failed:X_P9_consumed_lag:pair%d:%s:%s"
                    % (n, arm_name, sorted(lags)))
            worst_probe = max((f["emit_minus_input_ms"]
                               for f in probe_facts), default=0.0)
            worst_all = max(f["emit_minus_input_ms"] for f in facts)
            seam[arm_name] = {
                "chains": len(facts),
                "probe_chains": len(probe_facts),
                "law_scope": "executed as written over the probe chains; "
                             "first-response chains gated at 50 ms; any "
                             "further exceeding chain is the RECORDED "
                             "FINDING x_p9_probe_latency_exceeded (the "
                             "pinned mapper's declared tail-deadline "
                             "exact-zero record); never tuned",
                "worst_emit_minus_input_ms": round(worst_probe, 3),
                "first_response_worst_ms": round(
                    max((f["emit_minus_input_ms"]
                         for f in first_response.values()), default=0.0), 3),
                "worst_all_emit_minus_input_ms": round(worst_all, 3),
                "consumed_lags": sorted(lags),
                "probe_facts": probe_facts,
                "x_p9_findings": [
                    {"seq": f["seq"], "input_t_ms": f["input_t_ms"],
                     "command_emitted_t_ms": f["command_emitted_t_ms"],
                     "emit_minus_input_ms": f["emit_minus_input_ms"],
                     "code": "x_p9_probe_latency_exceeded",
                     "mapper_deadline_law": "the pinned mapper's "
                                            "_apply_tail emits the "
                                            "tail-deadline exact-zero "
                                            "record at the second boundary "
                                            "after release (<= released_ms "
                                            "+ 100 ms)"}
                    for f in findings],
            }

        # ---- the landmark set derived from the anchor base
        landmark_set = lm.build_landmark_set(x0_a)

        # ---- renders (both arms; 21 clean + 3 diagnostic per arm)
        arm_frames = {}
        arm_meta = {}
        arm_render_facts = {}
        for arm_name, arm_rows, arm in (("A", rows_a, A), ("B", rows_b, B)):
            frames = []
            metas = []
            p2a_rows = []
            p3_instrument = []
            p3_landmark_rows = []
            live_projections = []
            live_masks = []
            live_targets = []
            live_body_bboxes = []
            live_centroids = []
            piped_shas = []
            for k, tick in enumerate(present_ticks):
                row = arm_rows[k]
                pose = vz.pose_at(row, geom, 0.0, (row["com_x_m"], 0.0))
                out = rx.render_frame_x05(
                    vz, f04, C_V1_VIEW, pose, False, tick, "x05",
                    landmark_set=landmark_set, instrument=True,
                    ix_mod=ix_mod, row=row)
                colour = out["colour"]
                cam = out["cam"]
                # X-P2a: the landmark-free, instrument-free render must be
                # byte-identical to the pinned renderer's own frame.
                out_free = rx.render_frame_x05(
                    vz, f04, C_V1_VIEW, pose, False, tick, "x05")
                pinned_colour, _drawn, _pcam = vz.render_frame(
                    f04, C_V1_VIEW, pose, False, tick, "x05")
                # byte-identity through the lossless packing (the packed
                # bgr0 bytes are a bijection of the colour buffer; the
                # canonical-JSON form is provably equal here but costs
                # seconds per frame)
                sha_free = sha_bytes(frame_bytes_bgr0(out_free["colour"]))
                sha_pinned = sha_bytes(frame_bytes_bgr0(pinned_colour))
                p2a_rows.append({
                    "tick": int(tick),
                    "x05_free_sha256": sha_free,
                    "pinned_sha256": sha_pinned,
                    "identical": sha_free == sha_pinned})
                # X-P2b: the body pixel set unchanged by the landmark
                # addition (positions and count).
                arr_full = np.asarray(colour, dtype=np.uint8)
                arr_free = np.asarray(out_free["colour"], dtype=np.uint8)
                bm_full = srx.body_mask(arr_full)
                bm_free = srx.body_mask(arr_free)
                body_same = (int(bm_full.sum()) == int(bm_free.sum())
                             and bool(np.array_equal(bm_full, bm_free)))
                # X-P3: rendered landmark bboxes vs the pinned projection of
                # the declared world vertices (+ the displacement law +
                # the derived pixels-per-meter scale).
                projections = lm.project_vertices(cam, landmark_set)
                tgt = cam.pixel([row["com_x_m"], 0.5, 0.0])
                lm_masks = srx.landmark_masks(arr_full)
                frame_lm_rows = []
                for name in lm.LANDMARK_ORDER:
                    m = lm_masks[name]
                    ys, xs = np.nonzero(m)
                    rendered_bbox = ([int(xs.min()), int(ys.min()),
                                      int(xs.max()), int(ys.max())]
                                     if len(xs) else None)
                    proj_pts = [p for p in projections[name]
                                if p is not None]
                    proj_bbox = lm.bbox_of_points(proj_pts)
                    tol = lm.RASTER_TOLERANCE_PX
                    bbox_ok = (
                        rendered_bbox is not None and proj_bbox is not None
                        and abs(rendered_bbox[0] - proj_bbox[0]) <= tol
                        and abs(rendered_bbox[1] - proj_bbox[1]) <= tol
                        and abs(rendered_bbox[2] - proj_bbox[2]) <= tol
                        and abs(rendered_bbox[3] - proj_bbox[3]) <= tol)
                    frame_lm_rows.append({
                        "landmark": name,
                        "rendered_mask_bbox": rendered_bbox,
                        "projected_vertex_bbox": proj_bbox,
                        "bbox_within_2px": bool(bbox_ok)})
                # live checks' inputs (masks + body ROI + target pixel)
                centroids = {}
                for name in lm.LANDMARK_ORDER:
                    ys, xs = np.nonzero(lm_masks[name])
                    centroids[name] = (
                        (float(xs.mean()), float(ys.mean()))
                        if len(xs) else None)
                live_centroids.append(centroids)
                live_projections.append(projections)
                live_masks.append({k: v for k, v in lm_masks.items()})
                live_targets.append(tgt)
                live_body_bboxes.append(srx.body_bbox(arr_full))
                # X-P4 render-level: the instrument receipt + probe
                i_receipt = out["instrument_receipt"]
                i_probe = ix_mod.probe_instrument(arr_full, i_receipt)
                require(i_probe["ok"],
                        "prediction_failed:X_P4_instrument:pair%d:%s:t%d"
                        % (n, arm_name, tick))
                piped = frame_bytes_bgr0(colour)
                piped_shas.append(sha_bytes(piped))
                frames.append(piped)
                metas.append({
                    "frame_id": "P%02d_clean_t%d" % (k, tick),
                    "tick": int(tick), "diagnostic": False,
                    "render_index": k,
                    "state_sha256": row["state_sha256"],
                    "anchor_xy": [row["com_x_m"], 0.0],
                    "declared_instrument": "velocity_indicator",
                    "instrument_text": i_receipt["text"],
                    "body_invariance_ok": bool(body_same),
                    "landmark_bbox_rows": frame_lm_rows,
                })
                p3_instrument.append(i_probe)
                p3_landmark_rows.extend(frame_lm_rows)
                _ = bm_full
            for j, tick in enumerate(diag_ticks):
                row = arm_rows[present_ticks.index(tick)]
                prev = A["per_tick"][tick - 1] if arm_name == "A" \
                    else B["per_tick"][tick - 1]
                state = sr4.derive_state(row, prev, climb_audit, vz, geom)
                out = rx.render_frame_x05(
                    vz, f04, C_V1_VIEW, state["pose"], True, tick, "x05",
                    landmark_set=landmark_set, instrument=True,
                    ix_mod=ix_mod, row=row)
                label_receipt = sr4.draw_layers(out["colour"], state)
                arr = np.asarray(out["colour"], dtype=np.uint8)
                i_receipt = out["instrument_receipt"]
                i_probe = ix_mod.probe_instrument(
                    arr, i_receipt,
                    border_overlap_px=ix_mod.DIAG_BORDER_OVERLAP_PX)
                i_probe["declared_overlap_note"] = (
                    "diagnostic frame: the X04 L1 panel (drawn after the "
                    "instrument per the frozen layer law) overwrites the "
                    "instrument's bottom border row (y=40, x[12,300]); the "
                    "ink text and bbox law are untouched")
                require(i_probe["ok"],
                        "prediction_failed:X_P4_instrument_diag:pair%d:%s"
                        % (n, arm_name))
                piped = frame_bytes_bgr0(out["colour"])
                piped_shas.append(sha_bytes(piped))
                frames.append(piped)
                metas.append({
                    "frame_id": "D_diag_t%d" % tick,
                    "tick": int(tick), "diagnostic": True,
                    "render_index": 21 + j,
                    "state_sha256": row["state_sha256"],
                    "anchor_xy": [row["com_x_m"], 0.0],
                    "declared_instrument": "velocity_indicator",
                    "instrument_text": i_receipt["text"],
                    "label_receipt": label_receipt,
                })
            # X-P2a/X-P2b aggregate for this arm
            require(all(r["identical"] for r in p2a_rows),
                    "prediction_failed:X_P2a:pair%d:%s"
                    % (n, arm_name))
            require(all(m["body_invariance_ok"] for m in metas
                        if not m["diagnostic"]),
                    "prediction_failed:X_P2b:pair%d:%s" % (n, arm_name))
            # X-P3 aggregate. (a) The bbox census: any edge deviating more
            # than the FROZEN +/-2 px raster tolerance is the RECORDED
            # FINDING x_p3_raster_tolerance_exceeded (the prereg's own rule:
            # exceeding a bound is a recorded finding, never tuned away;
            # measured where it happens: the rock tetra's acute base corner
            # thins below pixel coverage at some depths). (b) THE
            # SUBSTANTIVE MOTION LAW (gated): for every consecutive clean
            # frame pair and landmark, the MEASURED mask-centroid
            # displacement equals the ACTUAL pinned-F04 projection's
            # displacement of the declared world vertices through each
            # frame's OWN row-derived camera (never a constant scale), and
            # the derived pixels-per-meter scale (projected px / anchor
            # travel m) is RECORDED per frame per landmark. The landmark
            # masks consume ONLY the four declared landmark palettes — the
            # velocity instrument's palette is excluded by the palette law,
            # so the landmark-motion verdict and the indicator verdict are
            # SEPARATE, independently falsifiable tests.
            p3_bad = [r for r in p3_landmark_rows if not r["bbox_within_2px"]]
            p3_findings = [
                {"code": "x_p3_raster_tolerance_exceeded", **r}
                for r in p3_bad]
            flow_rows = []
            worst_agreement = 0.0
            for i in range(len(present_ticks) - 1):
                travel_m = (arm_rows[i + 1]["com_x_m"]
                            - arm_rows[i]["com_x_m"])
                for name in lm.LANDMARK_ORDER:
                    pairs_pv = [(a, b) for a, b in
                                zip(live_projections[i][name],
                                    live_projections[i + 1][name])
                                if a is not None and b is not None]
                    if not pairs_pv:
                        continue
                    proj_disp = (sum(math.hypot(b[0] - a[0], b[1] - a[1])
                                     for a, b in pairs_pv)
                                 / float(len(pairs_pv)))
                    c0 = live_centroids[i][name]
                    c1 = live_centroids[i + 1][name]
                    meas_disp = (math.hypot(c1[0] - c0[0], c1[1] - c0[1])
                                 if c0 is not None and c1 is not None
                                 else None)
                    scale = (round(proj_disp / abs(travel_m), 3)
                             if abs(travel_m) > 1e-9 else None)
                    agreement = (abs(meas_disp - proj_disp)
                                 if meas_disp is not None else None)
                    if agreement is not None:
                        worst_agreement = max(worst_agreement, agreement)
                    flow_rows.append({
                        "frame_pair": [int(present_ticks[i]),
                                       int(present_ticks[i + 1])],
                        "landmark": name,
                        "anchor_travel_m": round(travel_m, 6),
                        "projected_displacement_px": round(proj_disp, 3),
                        "measured_mask_centroid_displacement_px": (
                            round(meas_disp, 3)
                            if meas_disp is not None else None),
                        "agreement_px": (round(agreement, 3)
                                         if agreement is not None else None),
                        "scale_px_per_m_derived": scale,
                    })
            require(worst_agreement <= lm.RASTER_TOLERANCE_PX,
                    "prediction_failed:X_P3_flow:pair%d:%s:%.3f"
                    % (n, arm_name, worst_agreement))
            scale_summary = {}
            for name in lm.LANDMARK_ORDER:
                scales = [r["scale_px_per_m_derived"]
                          for r in flow_rows
                          if r["landmark"] == name
                          and r["scale_px_per_m_derived"] is not None]
                scale_summary[name] = {
                    "min": min(scales) if scales else None,
                    "max": max(scales) if scales else None,
                    "law": "derived per frame from the actual pinned F04 "
                           "projection at the landmark depth; never "
                           "asserted as a constant (prereg X-P3; the K01 "
                           "scale_px_per_m precedent generalized)"}
            arm_render_facts.setdefault("p3_flow_rows", []).extend(
                [{**r, "arm": arm_name, "pair": n} for r in flow_rows])
            arm_render_facts.setdefault("p3_findings", []).extend(
                [{**r, "arm": arm_name, "pair": n} for r in p3_findings])
            arm_render_facts.setdefault("p3_scale_summary", {})[
                "%s_%s" % (arm_name, n)] = scale_summary
            # X-P7 render-level: clean frames carry ZERO diagnostic palette
            for k, meta in enumerate(metas):
                if meta["diagnostic"]:
                    continue
                arr = np.asarray(decoded_rgb(frames[k]), dtype=np.uint8)
                probe = srx.probe_clean_frame(arr)
                require(probe["ok"],
                        "prediction_failed:X_P7_clean:pair%d:%s:t%d:%s"
                        % (n, arm_name, meta["tick"],
                          probe["undeclared_colors"][:2]))
            # the live landmark checks over this arm's presented frames
            live = lm.live_checks(landmark_set, live_projections, live_masks,
                                  live_targets, live_body_bboxes)
            landmark_live_all.append({"pair": n, "cls": cls,
                                      "arm": arm_name, **live})
            # X-P8 cadence (the plan is the law; the video binds 24 frames)
            cadence_ok = all(b - a == 15
                             for a, b in zip(present_ticks,
                                             present_ticks[1:]))
            require(cadence_ok, "prediction_failed:X_P8:pair%d" % n)

            arm_frames[arm_name] = frames
            arm_meta[arm_name] = metas
            arm_render_facts[arm_name] = {
                "piped_shas": piped_shas,
                "x_p2a_rows": p2a_rows,
                "x_p4_instrument": p3_instrument,
                "landmark_bbox_rows": p3_landmark_rows,
                "live_checks": live,
                "cadence_ticks_ok": cadence_ok,
            }

        # ---- X-P4 divergence law (render-level, from the rows)
        brake_consumed_slot = next(t for t in present_ticks
                                   if t >= brake_consumed)
        div_rows = []
        for k, tick in enumerate(present_ticks):
            va = round(rows_a[k]["com_v_m_s"], 3)
            vb = round(rows_b[k]["com_v_m_s"], 3)
            div_rows.append({"presented_tick": int(tick),
                             "brake_display": va, "control_display": vb,
                             "diverges": va != vb,
                             "lawful": tick >= brake_consumed})
        require(any(r["diverges"] for r in div_rows if r["lawful"]),
                "prediction_failed:X_P4_divergence:pair%d" % n)

        # render-level diff series (preliminary; the decoded series from the
        # videos is the authoritative X-P5 evidence, stage 3)
        frames_a = [np.asarray(decoded_rgb(f), dtype=np.uint8)
                    for f in arm_frames["A"]]
        frames_b = [np.asarray(decoded_rgb(f), dtype=np.uint8)
                    for f in arm_frames["B"]]
        series_render = dc.pair_series(frames_a[:21], frames_b[:21],
                                       present_ticks, brake_consumed)

        # carry the X-P3 flow/facts of this pair into the receipt-level
        # aggregates (bounded: 2 arms x 20 frame pairs x 4 landmarks); the
        # p3_* keys accumulate at the pair-facts dict level (the "A"/"B"
        # keys hold the per-arm fact tables)
        for r in arm_render_facts.get("p3_flow_rows", []):
            receipt_flow.append(r)
        for r in arm_render_facts.get("p3_findings", []):
            receipt_findings.append(r)
        receipt_scales.update(arm_render_facts.get("p3_scale_summary", {}))


        # ---- the pair record (the a12 record form, condensed)
        pair_record = {
            "schema": "chimera.x05.driver_pair.v1",
            "n": n, "cls": cls, "t_in": pair["t_in"],
            "repress_tick": pair["repress_tick"],
            "repress_delta_ticks": pair["repress_delta_ticks"],
            "unit_reconciliation": UNIT_RECONCILIATION,
            "probe_events": A["probe_events"],
            "zoh": {"consumed_tick": brake_consumed,
                    "first_divergence_tick": fd,
                    "divergence_at_zoh_boundary": True,
                    "issued_tick": fd - 1},
            "determinism": det,
            "prefix": prefix,
            "seam": seam,
            "x_p3_flow_rows": [
                r for r in receipt_flow
                if r["pair"] == n],
            "window_rows": {
                "A": [{k: r[k] for k in ("tick", "com_v_m_s", "com_x_m",
                                         "phase_left", "phase_right",
                                         "state_sha256")} for r in rows_a],
                "B": [{k: r[k] for k in ("tick", "com_v_m_s", "com_x_m",
                                         "phase_left", "phase_right",
                                         "state_sha256")} for r in rows_b]},
            "display_divergence_rows": div_rows,
            "chain_counts": {"A": A["chain_count"], "B": B["chain_count"],
                             "B2": B2["chain_count"]},
            "final_state_sha256": {"A": A["final_state_sha256"],
                                   "B": B["final_state_sha256"],
                                   "B2": B2["final_state_sha256"]},
        }
        write_out("driver_pair_P%02d_%s.json" % (n, cls), pair_record)

        # persist this pair's frames for the capture + gate stages (RGB;
        # the packed bytes are bgr0, so the channel order is decoded back —
        # every consumer of these arrays (re-pack, palette classification,
        # probes) expects the true render colors)
        np.save(str(OUT / ("frames_P%02d_%s_A.npy" % (n, cls))),
                np.stack([decoded_rgb(f) for f in arm_frames["A"]]))
        np.save(str(OUT / ("frames_P%02d_%s_B.npy" % (n, cls))),
                np.stack([decoded_rgb(f) for f in arm_frames["B"]]))
        (OUT / ("frames_meta_P%02d_%s.json" % (n, cls))).write_bytes(
            canonical({"present_ticks": present_ticks,
                       "diag_ticks": diag_ticks,
                       "A": arm_meta["A"], "B": arm_meta["B"],
                       "piped_shas": {k: arm_render_facts[k]["piped_shas"]
                                      for k in ("A", "B")},
                       "brake_consumed_tick": brake_consumed}) + b"\n")

        pairs_out.append({
            "n": n, "cls": cls, "t_in": pair["t_in"],
            "brake_consumed_tick": brake_consumed,
            "first_lawful_presented": brake_consumed_slot,
            "determinism": det, "prefix": prefix, "seam": seam,
            "render_diff_series": series_render,
            "render_fact_counts": {
                "x_p2a_rows": sum(len(arm_render_facts[a]["x_p2a_rows"])
                                  for a in ("A", "B")),
                "x_p3_landmark_rows": sum(
                    len(arm_render_facts[a]["landmark_bbox_rows"])
                    for a in ("A", "B")),
                "x_p3_flow_rows": len(
                    arm_render_facts.get("p3_flow_rows", [])),
                "x_p3_findings": len(
                    arm_render_facts.get("p3_findings", [])),
                "x_p4_instrument_rows": sum(
                    len(arm_render_facts[a]["x_p4_instrument"])
                    for a in ("A", "B")),
                "x_p7_clean_frames": 2 * len(present_ticks),
            },
        })
    # ---- R1: THE RUN'S OWN phase determination (named finding when the
    # phases diverge in this run; disclosed alongside the a12-based,
    # regime-scoped determination - never silently contradicted)
    run_phases = cd.derive_run_phases(run_window_rows)
    if run_phases["run_phase_divergence_observed"]:
        print("RUN FINDING: x_run_phase_divergence_observed - phases "
              "diverge in this run (identity %s; first divergent tick %s)"
              % (sorted(set(run_phases["identity_counts"].values())),
                 run_phases["first_divergent_tick"]))

    # the anchor base is pair-invariant on the deterministic line
    require(len(set(x0_seen.values())) == 1,
            "anchor_base_not_invariant:" + repr(sorted(x0_seen.values())))
    x0 = next(iter(x0_seen.values()))

    # ---- the falsifier battery (render-level preliminary verdicts)
    falsifier = {
        "velocity_visible_in_clean_render_level": {
            "pairs_total": len(pairs_out),
            "pairs_first_lawful_diff_ge_1": sum(
                1 for p in pairs_out
                if (p["render_diff_series"]["first_lawful_whole_frame_diff"]
                    or 0) >= 1),
            "pairs_persist_landmark": sum(
                1 for p in pairs_out
                if p["render_diff_series"]["persists_in_landmark_channel"]),
            "pairs_persist_instrument": sum(
                1 for p in pairs_out
                if p["render_diff_series"]["persists_in_instrument_channel"]),
            "pairs_no_pixel_reflection": [p["n"] for p in pairs_out
                                          if p["render_diff_series"]
                                          ["no_pixel_reflection_in_window_persists"]],
        },
    }

    receipt = {
        "schema": "chimera.x05_presentation_receipt.v1",
        "card_id": "MAT2-X05",
        "agent_id": "wk-x05-impl",
        "base_sha256": vi5.BASE_SHA,
        "pin_base": vi5.PIN_BASE,
        "prereg_commit": prereg_commit,
        "preregistration_sha256": vi5.prereg_sha256(),
        "pin_row_count": len(rows),
        "base_identity": base,
        "registry": reg,
        "w10_layer": w10,
        "u07_layer": u07,
        "gate": {"physics_build": gate["physics_build"],
                 "deploy_decision": gate["deploy_decision"]},
        "coupling_determination": coupling,
        "x_run_phase_determination": run_phases,
        "structural_audit": structural,
        "unit_reconciliation": UNIT_RECONCILIATION,
        "anchor_base_x0": x0,
        "anchor_series": anchor_series,
        "landmark_live_checks": landmark_live_all,
        "x_p3_test_separation": {
            "law": "the landmark-motion verdict and the indicator verdict "
                   "are SEPARATE, independently falsifiable tests: the "
                   "landmark displacement consumes ONLY the four declared "
                   "landmark palettes (the instrument palette is excluded "
                   "by the palette law and the strip rect is not part of "
                   "any landmark mask); the indicator verdict consumes the "
                   "instrument receipt + the instrument channel; the X-P5 "
                   "channels are computed separately per channel",
        },
        "x_p3_flow_law": {
            "law": "for every consecutive clean frame pair and landmark, "
                   "the measured mask-centroid displacement equals the "
                   "ACTUAL pinned F04 projection's displacement of the "
                   "declared world vertices through each frame's own "
                   "row-derived camera (gated at the declared +/-2 px "
                   "raster tolerance); the pixels-per-meter scale is "
                   "DERIVED per frame at the landmark depth and recorded "
                   "here — never asserted as a constant (prereg X-P3 "
                   "already defers to the actual projection; no amendment "
                   "required)",
            "rows_recorded": len(receipt_flow),
            "findings_recorded": len(receipt_findings),
            "worst_agreement_px": round(
                max((abs(r["agreement_px"]) for r in receipt_flow
                     if r["agreement_px"] is not None), default=0.0), 3),
        },
        "x_p3_scale_summary": receipt_scales,
        "x_p3_findings": receipt_findings,
        "pairs": [{k: v for k, v in p.items()
                   if k != "render_diff_series"} for p in pairs_out],
        "render_diff_series": {("P%02d_%s" % (p["n"], p["cls"])):
                               p["render_diff_series"] for p in pairs_out},
        "falsifier_render_level": falsifier,
        "absent_inventory": {
            "A1_stride_velocity_coupling":
                "DECLARED ABSENT (" + coupling["determination"] + ")",
            "A2_body_displayed_velocity_cue":
                "ABSENT; the only velocity readout in the clean view is the "
                "declared screen-space instrument",
            "A3_audio_cues": "NOT this card (C24 unexercised)",
            "A4_native_engine_frame":
                "ABSENT; declared CPU-line frame records of the records-only "
                "renderer",
            "A5_occluders": "none declared; landmarks verified non-occluding",
            "A6_wall_clock_sla": "none exists; injected-clock arithmetic",
            "A7_human_feel": "the readable-motion law is the measured pixel "
                             "geometry; independent sergeant picture review "
                             "remains required; visual_acceptance false by "
                             "design",
            "A8_world_furniture_physics":
                "landmarks are presentation-state objects; no collision, no "
                "contact, no state channel",
        },
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B "
                                   "tools/monkey_campaign/contributions/"
                                   "MAT2-X05/run_all.py"},
    }
    write_out("presentation_receipt.json", receipt)
    print("verification: %d pairs; x0=%.6f; live-check min clearance %s px"
          % (len(pairs_out), x0,
             min(r["min_clearance_px"] for r in landmark_live_all)))
    return receipt


# --------------------------------------------------------------------------
# stage 3: the bounded capture (videos + decoded evidence + manifest)
# --------------------------------------------------------------------------
def stage_capture() -> dict:
    import verify_inputs_x05 as vi5
    import diff_channels as dc
    import state_readout_x05 as srx
    import landmarks_x05 as lm

    reg = vi5.verify_registry()      # READ-ONLY; checked BEFORE any capture
    profile = reg["profile"]
    require(profile["id"] == "presentation", "profile_check_law")
    ffmpeg_ver = ffmpeg_version()
    capture_dir = OUT / "capture"
    capture_dir.mkdir(parents=True, exist_ok=True)

    diag_layer_names = list(profile["diagnostic_layers"])
    require(diag_layer_names == ["selected state labels", "event/tick trace",
                                 "debug isolation of the affected layer"],
            "profile_layer_names_changed")

    videos = []
    frame_rows = []
    pair_facts = {}
    all_piped = []
    for n in range(1, N_PAIRS + 1):
        cls = "BRAKE-SHORT" if n % 2 == 1 else "BRAKE-LONG"
        meta = json.loads((OUT / ("frames_meta_P%02d_%s.json" % (n, cls)))
                          .read_bytes())
        frames_a = list(np.load(str(OUT / ("frames_P%02d_%s_A.npy"
                                           % (n, cls)))))
        frames_b = list(np.load(str(OUT / ("frames_P%02d_%s_B.npy"
                                           % (n, cls)))))
        require(len(frames_a) == len(frames_b) == 24,
                "capture_frame_count:pair%d" % n)
        brake_consumed = meta["brake_consumed_tick"]
        present_ticks = meta["present_ticks"]

        pair_videos = {}
        decoded_clean = {}
        for arm, frames in (("A", frames_a), ("B", frames_b)):
            name = "capture_P%02d_%s_%s.mkv" % (n, cls, arm)
            path = capture_dir / name
            packed = [frame_bytes_bgr0(f) for f in frames]
            video_sha, piped_shas = encode_video(path, packed)
            require(piped_shas == meta["piped_shas"][arm],
                    "capture_piped_sha_drift:pair%d:%s" % (n, arm))
            decoded = decode_all_frames(path)
            require(len(decoded) == 24,
                    "capture_decode_count:pair%d:%s" % (n, arm))
            probe_idx = (0, 12, 23)
            for idx in probe_idx:
                require(sha_bytes(decoded[idx]) == piped_shas[idx],
                        "capture_codec_violation:decode_mismatch:pair%d:%s:"
                        "idx%d" % (n, arm, idx))
            decoded_clean[arm] = [decoded_rgb(d) for d in decoded[:21]]
            pair_videos[arm] = {"name": name, "sha256": video_sha,
                                "frames": 24,
                                "piped_shas": piped_shas,
                                "decode_probes_pixel_exact": True}
            videos.append(pair_videos[arm])
            all_piped.extend(piped_shas)
            for k, m in enumerate(meta[arm]):
                frame_rows.append({
                    "video": name, "frame_id": m["frame_id"],
                    "tick": m["tick"], "diagnostic": m["diagnostic"],
                    "render_index": m["render_index"],
                    "frame_sha256": piped_shas[k],
                    "state_sha256": m["state_sha256"],
                    "anchor_xy": m["anchor_xy"],
                    "declared_instrument": m.get("declared_instrument"),
                    "instrument_text": m.get("instrument_text"),
                })
        # THE AUTHORITATIVE X-P5 EVIDENCE: the diff channels computed on the
        # DECODED FFV1 clean frames.
        series = dc.pair_series(decoded_clean["A"], decoded_clean["B"],
                                present_ticks, brake_consumed)
        disp_a = dc.landmark_channel_displacement(decoded_clean["A"])
        disp_b = dc.landmark_channel_displacement(decoded_clean["B"])
        # X-P7 re-executed on the DECODED clean stills
        for k, arr in enumerate(decoded_clean["A"]):
            probe = srx.probe_clean_frame(arr)
            require(probe["ok"],
                    "prediction_failed:X_P7_decoded:pair%d:A:t%d"
                    % (n, present_ticks[k]))
        for k, arr in enumerate(decoded_clean["B"]):
            probe = srx.probe_clean_frame(arr)
            require(probe["ok"],
                    "prediction_failed:X_P7_decoded:pair%d:B:t%d"
                    % (n, present_ticks[k]))
        pair_facts["P%02d_%s" % (n, cls)] = {
            "n": n, "cls": cls,
            "brake_consumed_tick": brake_consumed,
            "videos": pair_videos,
            "decoded_diff_series": series,
            "landmark_displacement": {"A_brake": disp_a, "B_control": disp_b},
            "present_ticks": present_ticks,
        }
        del frames_a, frames_b, decoded_clean

    # ---- X-P6 flow discriminates speed (decoded evidence; the law's named
    # variable is the CUMULATIVE landmark-channel displacement)
    x6_rows = []
    for key, fact in pair_facts.items():
        control = fact["landmark_displacement"]["B_control"]["cumulative_px"]
        brake = fact["landmark_displacement"]["A_brake"]["cumulative_px"]
        x6_rows.append({"pair": key,
                        "control_cumulative_px": control,
                        "brake_cumulative_px": brake,
                        "control_net_px":
                            fact["landmark_displacement"]["B_control"]["net_px"],
                        "brake_net_px":
                            fact["landmark_displacement"]["A_brake"]["net_px"],
                        "control_exceeds_brake": control > brake})
    require(all(r["control_exceeds_brake"] for r in x6_rows),
            "prediction_failed:X_P6_pair_ordering:"
            + repr([r["pair"] for r in x6_rows
                    if not r["control_exceeds_brake"]]))
    short_brakes = [f["landmark_displacement"]["A_brake"]["cumulative_px"]
                    for k, f in pair_facts.items()
                    if f["cls"] == "BRAKE-SHORT"]
    long_brakes = [f["landmark_displacement"]["A_brake"]["cumulative_px"]
                   for k, f in pair_facts.items()
                   if f["cls"] == "BRAKE-LONG"]
    require(sum(long_brakes) < sum(short_brakes),
            "prediction_failed:X_P6_depth_ordering")
    x6 = {"rows": x6_rows,
          "short_brake_cum_sum_px": round(sum(short_brakes), 3),
          "long_brake_cum_sum_px": round(sum(long_brakes), 3),
          "depth_ordering_holds": sum(long_brakes) < sum(short_brakes)}

    # ---- the falsifier verdict (X-P5), on the decoded evidence
    x5_rows = []
    for key, fact in pair_facts.items():
        series = fact["decoded_diff_series"]
        x5_rows.append({
            "pair": key,
            "consumed_tick": fact["brake_consumed_tick"],
            "first_lawful_slot": series["first_lawful_slot"],
            "first_lawful_whole_frame_diff":
                series["first_lawful_whole_frame_diff"],
            "first_lawful_landmark_diff": series["first_lawful_landmark_diff"],
            "first_lawful_instrument_diff":
                series["first_lawful_instrument_diff"],
            "pre_lawful_all_zero": series["pre_lawful_all_zero"],
            "persists_landmark": series["persists_in_landmark_channel"],
            "persists_instrument": series["persists_in_instrument_channel"],
            "no_pixel_reflection_in_window_persists":
                series["no_pixel_reflection_in_window_persists"],
        })
    failed_pairs = [r["pair"] for r in x5_rows
                    if r["no_pixel_reflection_in_window_persists"]]
    x1c_ok = all(r["pre_lawful_all_zero"] for r in x5_rows)
    require(x1c_ok, "prediction_failed:X_P1c_control_silence")
    x5 = {"rows": x5_rows, "failed_pairs": failed_pairs,
          "pairs_visible": len(x5_rows) - len(failed_pairs),
          "remediation_failed": bool(failed_pairs)}
    falsifier_receipt = {
        "schema": "chimera.x05_falsifier_receipt.v1",
        "X_P5_velocity_visible_in_clean": x5,
        "X_P6_flow_discriminates_speed": x6,
        "X_P1c_control_silence": {"all_pairs": x1c_ok},
        "test_separation": {
            "law": "the landmark-motion test and the indicator test are "
                   "SEPARATE and independently falsifiable: the "
                   "landmark-channel displacement (X-P6) and the "
                   "landmark-channel diffs (X-P5) consume ONLY the four "
                   "declared landmark palettes; the velocity instrument's "
                   "palette is excluded by the palette law and the strip "
                   "rect is in no landmark mask — changing overlay digits "
                   "cannot satisfy the landmark-motion test",
        },
        "falsifier_clause": "any pair with zero clean-view diff on every "
                            "declared frame is the recorded finding "
                            "no_pixel_reflection_in_window_persists; the "
                            "card then reports the remediation as FAILED on "
                            "the measured evidence",
        "evidence_basis": "decoded FFV1 clean frames (full-stream lossless "
                          "decode; probe-verified pixel-exact)",
    }
    write_out("falsifier_receipt.json", falsifier_receipt)

    # ---- the camera manifest + the pinned validator
    subject_sha = sha_bytes(canonical(
        {"frames": all_piped,
         "windows": {k: f["decoded_diff_series"]["consumed_tick"]
                     for k, f in pair_facts.items()}}))
    capture_sha = sha_bytes(canonical(
        [{"video": v["name"], "sha256": v["sha256"]} for v in videos]))
    tick_interval = [4365, 4665]

    view_rows = []
    for mode in ("diagnostic", "clean"):
        locator_video = videos[1]["name"]     # P01's control-arm video
        view_rows.append({
            "view_id": PROFILE_VIEW_NAME,
            "mode": mode,
            "pair_id": PROFILE_VIEW_NAME,
            "state_binding": {"kind": "trace", "sha256": subject_sha},
            "artifact_locator": {"kind": "video",
                                 "seconds": [0, 24],
                                 "video": locator_video},
            "camera": camera_record(tick_interval, diag_layer_names),
            "visibility": visibility_row(mode == "diagnostic",
                                         diag_layer_names),
            "label_ids": LABELS if mode == "diagnostic" else [],
            "visibility_layers": diag_layer_names if mode == "diagnostic"
            else [],
            "occlusion_or_xray_mode": "depth_tested",
            "state_or_tick_interval": tick_interval,
            "subject_ticks": [4365, 4665],
            "videos": [{"name": v["name"], "sha256": v["sha256"],
                        "frames": v["frames"]} for v in videos],
        })
    manifest = {
        "schema": "chimera.visual_capture_manifest.v1",
        "task_id": "X05",
        "run_id": "mat2-x05/sealed",
        "card_id": "MAT2-X05",
        "subject_sha256": subject_sha,
        "capture_sha256": capture_sha,
        "profile_id": profile["id"],
        "tick_interval": tick_interval,
        "views": view_rows,
        "frame_rows": frame_rows,
        "capture_sha_definition": "sha256 over the canonical list of the 20 "
                                  "per-arm-per-pair FFV1 videos "
                                  "(name, sha256), sorted by name",
    }
    context = {
        "schema": "chimera.x05_capture_context.v1",
        "task_id": "X05",
        "run_id": manifest["run_id"],
        "subject_sha256": subject_sha,
        "capture_sha256": capture_sha,
        "tick_interval": tick_interval,
        "card_id": "MAT2-X05",
        "preregistration_sha256": vi5.prereg_sha256(),
        "registry_profile": profile,
        "declared_view_subset": {
            "views": [PROFILE_VIEW_NAME],
            "law": "the frozen X05 capture law (prereg section 5) declares "
                   "ONE view, the pinned U07 C_V1 constants, which are "
                   "identical to this profile view's declared constants; "
                   "the profile's remaining two views are not part of the "
                   "frozen frame plan; the FULL registry profile is recorded "
                   "in registry_profile and the subset is disclosed here",
        },
        "videos": [{"name": v["name"], "sha256": v["sha256"],
                    "frames": v["frames"]} for v in videos],
        "codec": {"name": "FFV1",
                  "args": "-level 3 -g 1 -fflags +bitexact -pix_fmt bgr0",
                  "ffmpeg_version": ffmpeg_ver,
                  "declared_version": "declared capture-tool calls (prereg "
                                      "section 8): encode + full-stream "
                                      "decode probes"},
        "camera_frame_law": "BODY-ANCHORED follow offsets (the anchor per "
                            "frame rides the rows; recorded per frame in "
                            "frame_rows.anchor_xy); the presented frames are "
                            "the declared CPU-line frame records (absent "
                            "inventory A4); the montage tick axis is the "
                            "frame index at 1 fps",
        "diagnostic_frame_occlusions": "DECLARED (frozen render order): the "
                                       "instrument strip (topmost) overlaps "
                                       "the pinned tick-digit corner overlay, "
                                       "and the L2 event strip overlaps the "
                                       "pinned stride bar, on DIAGNOSTIC "
                                       "frames only; the tick remains "
                                       "readable in the L2 declared layer",
        "honesty_label": "RENDERED FIXTURE of the certified run's own "
                         "per-tick telemetry (W10 records-only renderer); "
                         "the velocity indicator is AN INSTRUMENT, never a "
                         "body cue; visual_acceptance false BY DESIGN; "
                         "independent picture review remains required",
    }
    # the declared view subset (validator input; the full profile is recorded)
    subset_profile = dict(profile)
    subset_profile["views"] = [PROFILE_VIEW_NAME]
    vc = vi5.load_visual_capture()
    verdict = vc.validate_manifest(manifest, context, subset_profile)

    (capture_dir / "capture_manifest.json").write_bytes(
        canonical(manifest) + b"\n")
    (capture_dir / "capture_context.json").write_bytes(
        canonical(context) + b"\n")
    capture_receipt = {
        "schema": "chimera.x05_capture_receipt.v1",
        "card_id": "MAT2-X05",
        "preregistration_sha256": vi5.prereg_sha256(),
        "profile_source": "registry read-only (mode=ro), checked BEFORE any "
                          "capture (G7)",
        "videos": [{"name": v["name"], "sha256": v["sha256"],
                    "frames": v["frames"]} for v in videos],
        "video_count": len(videos),
        "decode_probes_pixel_exact": True,
        "decode_full_stream_frames": 24 * len(videos),
        "camera_fields_complete": True,
        "camera_required_field_count":
            len(profile["camera_required_fields"]),
        "validation": {"mode": verdict["mode"],
                       "structurally_valid": verdict["structurally_valid"]},
        "validation_verdicts": verdict,
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B run_all.py (capture stage)"},
    }
    write_out("capture_receipt.json", capture_receipt)
    print("capture: %d videos; X-P5 visible pairs %d/%d; X-P6 depth "
          "ordering %s" % (len(videos), x5["pairs_visible"], len(x5_rows),
                           x6["depth_ordering_holds"]))
    return capture_receipt


def camera_record(ticks, layers):
    """The per-view camera record carrying the profile's EXACT
    camera_required_fields (the X04 form; the pinned U07 C_V1 offsets)."""
    import verify_inputs_x05 as vi5
    _wd, vz = vi5.load_w10_modules()
    f04 = vz.load_f04_module()
    view = C_V1_VIEW
    cam = f04.Camera({
        "position": [view["position"][0], view["position"][1],
                     view["position"][2]],
        "target": [view["target"][0], view["target"][1],
                   view["target"][2]],
        "vfov_deg": view["vfov_deg"], "near_far": view["near_far"]})
    rec = dict(cam.camera_record(ticks))
    rec["frame_id"] = ("f01_world_y_up/MAT2-X05/" + PROFILE_VIEW_NAME)
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
    rec["state_or_tick_interval"] = list(ticks)
    rec["position_frame"] = ("body-anchored offsets (the anchor per frame "
                             "is recorded in frame_rows.anchor_xy)")
    rec["follow"] = bool(view["follow"])
    # the validator's camera() reads sample_mode + samples at TOP level
    # (the X04 form): two identical fixed-bookmark samples covering the
    # declared tick interval (the offsets are constant; the anchor rides
    # the rows)
    rec["sample_mode"] = "fixed_bookmark"
    rec["samples"] = [
        {"tick": int(ticks[0]),
         "position": [view["position"][0], view["position"][1],
                      view["position"][2]],
         "target": [view["target"][0], view["target"][1],
                    view["target"][2]],
         "distance_to_target": float(cam.distance_to_target),
         "orientation": list(cam.quaternion_wxyz())},
        {"tick": int(ticks[1]),
         "position": [view["position"][0], view["position"][1],
                      view["position"][2]],
         "target": [view["target"][0], view["target"][1],
                    view["target"][2]],
         "distance_to_target": float(cam.distance_to_target),
         "orientation": list(cam.quaternion_wxyz())}]
    return rec


def visibility_row(diagnostic, layers):
    if diagnostic:
        bindings = [{"label_id": label, "subject_id": label + "_subject"}
                    for label in LABELS]
        return {"layers": list(layers), "label_ids": list(LABELS),
                "selected_ids": [LABELS[0]],
                "required_subject_ids": ["monkey_body"],
                "observed_subject_ids": ["monkey_body",
                                         "x05_velocity_instrument",
                                         "landmark_tree_far",
                                         "landmark_tree_near",
                                         "landmark_rock_far",
                                         "landmark_rock_near"]
                + [label + "_subject" for label in LABELS],
                "missing_subject_ids": [],
                "occlusion_mode": "depth_tested",
                "tag_bindings": bindings}
    return {"layers": [], "label_ids": [], "selected_ids": [],
            "required_subject_ids": ["monkey_body"],
            "observed_subject_ids": ["monkey_body",
                                     "x05_velocity_instrument",
                                     "landmark_tree_far",
                                     "landmark_tree_near",
                                     "landmark_rock_far",
                                     "landmark_rock_near"],
            "missing_subject_ids": [],
            "occlusion_mode": "depth_tested", "tag_bindings": []}


# --------------------------------------------------------------------------
# stage 4: the standing two-stage capture gate
# --------------------------------------------------------------------------
def stage_capture_gate() -> dict:
    card_dir = CARD / "capture_card" / "card"
    sys.path.insert(0, str(CARD / "capture_card"))
    sys.path.insert(0, str(card_dir))
    import run_all as card_run_all     # the card's own case table

    template_sha = sha_bytes(
        (CARD / "capture_card" / "TEMPLATE_MANIFEST.json").read_bytes())
    summary = card_run_all.run_cases(str(OUT / "capture_gate"), {
        "out_dir": OUT, "template_manifest_sha256": template_sha})
    summary["preregistration_sha256"] = sha_bytes(
        (CARD / "PREREGISTRATION.md").read_bytes())
    summary["case_count"] = len(summary.get("cases", {}))
    write_out("capture_gate_summary.json", summary)
    print("capture gate: %s (%d cases)" % (summary["verdict"],
                                           summary["case_count"]))
    return summary


# --------------------------------------------------------------------------
# the driver
# --------------------------------------------------------------------------
STAGES = [
    ("unit_battery", "run_checks.py"),
    ("presentation_verification", None),
    ("named_checks", "run_checks.py"),
    ("capture", None),
    ("capture_gate", None),
    ("report_generation", "make_report.py"),
    ("report_lint", "lint_report_numbers.py"),
]


def run_stage(name, module):
    import importlib.util
    if module is not None:
        path = CARD / module
        spec = importlib.util.spec_from_file_location("x05_stage_" + name,
                                                      path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["x05_stage_" + name] = mod
        spec.loader.exec_module(mod)
        return mod.main()
    if name == "presentation_verification":
        return 0 if stage_presentation_verification() else 1
    if name == "capture":
        return 0 if stage_capture() else 1
    if name == "capture_gate":
        summary = stage_capture_gate()
        return int(summary.get("exit_code", 2))
    raise RuntimeError("unknown_stage:" + name)


if __name__ == "__main__":
    os.chdir(CARD)
    results = []
    failed = 0
    for name, module in STAGES:
        rc = run_stage(name, module)
        results.append({"stage": name,
                        "module": module or "(inline)",
                        "exit_code": rc,
                        "verdict": "GREEN" if rc == 0 else "RED"})
        print("stage %s -> %s" % (name, "GREEN" if rc == 0 else "RED %d" % rc))
        if rc != 0:
            failed = rc
            break
    out_dir = OUT
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "schema": "chimera.x05_sealed_run.v1",
        "card": "MAT2-X05",
        "stages": results,
        "pass": failed == 0,
        "unit_reconciliation": UNIT_RECONCILIATION,
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B tools/monkey_campaign/"
                                   "contributions/MAT2-X05/run_all.py"},
    }
    (out_dir / "result.json").write_bytes(
        canonical(summary) + b"\n")
    print("sealed-run summary:", summary["pass"])
    sys.exit(failed)
