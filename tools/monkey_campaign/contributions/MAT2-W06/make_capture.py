#!/usr/bin/env python3
"""MAT2-W06 RETIRED record-space raster generator (additional
evidence only; the profile-conformant capture is run_replay_capture.py
per prereg addendum 1 - under a motion profile the format validator
forbids image rows, so these rasters are NOT the capture manifest).

Original header: MAT2-W06 profile-class capture (profile `walking`, kind `motion`).

HONESTY LABEL (carried in the manifest, the context and burned into every
diagnostic frame): this is a deterministic CPU software raster of the
ATTEMPT'S PINNED RECEIPTS (the W05 walk1m-r1 fitness curves, the frozen
per-seed metric windows and the 3x3 held-out matrix). It is NOT native
engine frames and NOT a runtime render. Native pose/contact trajectory
records are inventoried ABSENT (the runbook's bounded-resources law:
trajectory_retention NONE, streaming chain hashing only) — the profile's
native views (full-body ground overview; side view of stance/swing; close-up
of foot-ground contact) are delivered as DECLARED record-space panels of the
pinned outcome records, never as invented bodies. Screens never gate; the
receipts are the numerical evidence the profile demands. Full camera field
vocabulary per view row (16-key manifest vocabulary); visible_static... this
card's delivery is the PNG image set; the capture identity is the
ordered-concatenation sha256 (P8) and every view row (clean AND diagnostic)
carries the SAME composite evaluation-record sha (the profile falsifier's
view-toggle instrument). Registry profile loaded READ-ONLY (G7).

Run:  python -B make_capture.py     (writes capture/*)
Exit: 0 green / 2 named refusal. CPU only.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
import verify_inputs as vi
from run_evaluation import SEEDS, recompute_windows

CAPTURE = HERE / "capture"
VIEWPORT = [640, 480]
TICK_INTERVAL = [0, 0]
REFUSAL = "capture_refused"

HONESTY = ("RECORD-SPACE RASTER of pinned receipts - not engine frames; "
           "native pose/contact trajectory records inventoried ABSENT "
           "(runbook trajectory_retention NONE; streaming chain hashing "
           "only)")

LAYERS_BY_VIEW = {
    "training-signal overview": ["fitness curves (f_plus, f_minus)",
                                 "iteration windows (first/last 100)",
                                 "window mean markers"],
    "window detail": ["frozen metric window bars",
                      "window mean value labels"],
    "held-out matrix": ["held-out fitness matrix",
                        "diagonal/off-diagonal markers"],
}


def require(condition, code):
    if not condition:
        print("REFUSAL: " + code, file=sys.stderr)
        raise SystemExit(2)


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def load_profile():
    require(vi.REGISTRY.exists(), REFUSAL + ":registry_missing")
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
    return profile, task, state.get("revision"), card.get("state")


# ---- record-space data -------------------------------------------------------
def load_records():
    summary = json.loads((HERE / "receipts" / "evaluation_summary.json")
                         .read_bytes().decode("utf-8"))
    curves = {}
    windows = {}
    for seed in SEEDS:
        curves[seed] = json.loads(
            (vi.UPSTREAM / "receipts" / f"seed_{seed}_curve.json")
            .read_bytes().decode("utf-8"))
        windows[seed] = recompute_windows(curves[seed])
    heldout = json.loads((vi.UPSTREAM / "receipts" / "heldout_receipt.json")
                         .read_bytes().decode("utf-8"))
    return summary, curves, windows, heldout


def quat_wxyz_identity():
    return [1.0, 0.0, 0.0, 0.0]


def camera_record(view_id, mode, span, subject_sha, panel_note):
    """The full camera field vocabulary (structure-only, record space)."""
    return {
        "frame_id": "record_space_" + view_id + "_" + mode,
        "coordinate_unit": "m (record space; axes declared per view)",
        "position": [0.0, 0.0, 1.0],
        "orientation_convention_and_values":
            "wxyz " + json.dumps(quat_wxyz_identity())
            + " (camera-to-frame; identity)",
        "target": [0.0, 0.0, 0.0],
        "distance_to_target": 1.0,
        "projection": "orthographic (record space; no perspective)",
        "vertical_fov_or_orthographic_span": span,
        "near_far_planes": [0.001, 10.0],
        "aspect_ratio": VIEWPORT[0] / VIEWPORT[1],
        "viewport_resolution": VIEWPORT,
        "camera_motion_or_bookmark_sequence":
            "single fixed bookmark (static record-space view; "
            + panel_note + ")",
        "visibility_layers": LAYERS_BY_VIEW[view_id],
        "label_ids": [] if mode == "clean" else
            ["window markers", "window means", "seed ids", "verdicts",
             "honesty label"],
        "occlusion_or_xray_mode": "none (record-space raster; no z-buffer)",
        "state_or_tick_interval": ("static record set; no simulation tick; "
                                   "composite evaluation-record sha "
                                   + subject_sha[:12]),
    }


FONT = None


def get_font():
    global FONT
    if FONT is None:
        FONT = ImageFont.load_default()
    return FONT


def panel_curve(draw, box, curve, mode, seed, first100, last100, verdict):
    x0, y0, x1, y1 = box
    f_plus = [row[0] for row in curve]
    f_minus = [row[1] for row in curve]
    lo = min(min(f_plus), min(f_minus))
    hi = max(max(f_plus), max(f_minus))
    pad = 0.05 * (hi - lo)
    lo -= pad
    hi += pad
    n = len(curve)

    def px(i):
        return x0 + (x1 - x0) * i / (n - 1)

    def py(v):
        return y1 - (y1 - y0) * (v - lo) / (hi - lo)

    if mode == "diagnostic":
        for (a, b, col) in ((0, 100, (250, 235, 205)),
                            (n - 100, n, (205, 235, 250))):
            draw.rectangle([px(a), y0, px(b), y1], fill=col)
    draw.line([(px(i), py(f_minus[i])) for i in range(n)],
              fill=(60, 90, 200), width=1)
    draw.line([(px(i), py(f_plus[i])) for i in range(n)],
              fill=(30, 130, 60), width=1)
    if mode == "diagnostic":
        draw.line([(px(0), py(first100)), (px(99), py(first100))],
                  fill=(180, 60, 30), width=2)
        draw.line([(px(n - 100), py(last100)), (px(n - 1), py(last100))],
                  fill=(180, 60, 30), width=2)
        font = get_font()
        draw.text((x0 + 4, y0 + 2),
                  "seed %d  first100 %.10f -> last100 %.10f  verdict %s"
                  % (seed, first100, last100, verdict),
                  fill=(20, 20, 20), font=font)
        draw.text((x0 + 4, y1 - 12),
                  "f_plus (green) / f_minus (blue); shaded: frozen "
                  "first/last-100 windows", fill=(60, 60, 60), font=font)


def view_training_overview(mode, summary, curves, windows):
    img = Image.new("RGB", tuple(VIEWPORT), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    top = 18 if mode == "diagnostic" else 6
    if mode == "diagnostic":
        draw.text((4, 2), HONESTY, fill=(120, 30, 30), font=get_font())
    verdicts = {r["seed"]: r["verdict"] for r in summary["seed_rows"]}
    h = (VIEWPORT[1] - top - 6) / 3.0
    for k, seed in enumerate(SEEDS):
        first100, last100 = windows[seed]
        panel_curve(draw,
                    (44, top + k * h + 4, VIEWPORT[0] - 6,
                     top + (k + 1) * h - 4),
                    curves[seed], mode, seed, first100, last100,
                    verdicts[seed])
        draw.line([(44, top + k * h + 2), (VIEWPORT[0] - 6,
                                           top + k * h + 2)],
                  fill=(200, 200, 200))
    return img, ("3 stacked panels; x = iteration 0..1999; "
                 "y = fitness m/250-decision window")


def view_window_detail(mode, summary, curves, windows):
    img = Image.new("RGB", tuple(VIEWPORT), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    top = 18 if mode == "diagnostic" else 6
    if mode == "diagnostic":
        draw.text((4, 2), HONESTY, fill=(120, 30, 30), font=get_font())
    vals = []
    for seed in SEEDS:
        vals.extend(windows[seed])
    hi = max(vals) * 1.1
    bw = VIEWPORT[0] / 8.0
    for k, seed in enumerate(SEEDS):
        first100, last100 = windows[seed]
        bx = VIEWPORT[0] / 3.0 * k + bw * 0.5
        for j, (label, v) in enumerate((("first100", first100),
                                        ("last100", last100))):
            hgt = (VIEWPORT[1] - top - 30) * v / hi
            x0 = bx + j * bw * 0.9
            col = (30, 130, 60) if j == 0 else (180, 60, 30)
            draw.rectangle([x0, VIEWPORT[1] - 24 - hgt,
                            x0 + bw * 0.7, VIEWPORT[1] - 24], fill=col)
            if mode == "diagnostic":
                draw.text((x0, VIEWPORT[1] - 40 - hgt),
                          "%.6f" % v, fill=(20, 20, 20), font=get_font())
        draw.text((bx, VIEWPORT[1] - 18), "seed %d" % seed,
                  fill=(20, 20, 20), font=get_font())
    draw.text((4, top), "frozen M4 windows: mean iteration fitness "
              "(m per 250-decision window)", fill=(60, 60, 60),
              font=get_font())
    return img, "6 bars (3 seeds x first/last-100); y = fitness m"


def view_heldout_matrix(mode, summary, curves, windows, heldout):
    img = Image.new("RGB", tuple(VIEWPORT), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    top = 30 if mode == "diagnostic" else 12
    if mode == "diagnostic":
        draw.text((4, 2), HONESTY, fill=(120, 30, 30), font=get_font())
    cell_w = (VIEWPORT[0] - 70) / 3.0
    cell_h = (VIEWPORT[1] - top - 26) / 3.0
    fits = [c["fitness"] for c in heldout["cells"]]
    lo, hi = min(fits), max(fits)
    font = get_font()
    for c in heldout["cells"]:
        i = SEEDS.index(c["theta_seed"])
        j = SEEDS.index(c["scene_seed"])
        x0 = 60 + j * cell_w
        y0 = top + i * cell_h
        frac = 0.0 if hi == lo else (c["fitness"] - lo) / (hi - lo)
        col = (int(255 - 120 * frac), int(200 + 40 * frac), 200)
        draw.rectangle([x0 + 3, y0 + 3, x0 + cell_w - 3, y0 + cell_h - 3],
                       fill=col,
                       outline=(20, 20, 20) if not c["held_out"]
                       else (120, 120, 120))
        draw.text((x0 + 8, y0 + 8), "%.9f" % c["fitness"],
                  fill=(20, 20, 20), font=font)
        if mode == "diagnostic":
            draw.text((x0 + 8, y0 + cell_h - 18),
                      "held_out %s" % ("false (diag)" if not c["held_out"]
                                       else "true"),
                      fill=(60, 30, 120), font=font)
    for j, s in enumerate(SEEDS):
        draw.text((60 + j * cell_w + 8, top - 12), "scene %d" % s,
                  fill=(20, 20, 20), font=font)
        draw.text((6, top + j * cell_h + 8), "theta %d" % s,
                  fill=(20, 20, 20), font=font)
    draw.text((4, VIEWPORT[1] - 14),
              "3x3 held-out fitness matrix (m); all 9 cells receipted, "
              "none cherry-picked", fill=(60, 60, 60), font=font)
    return img, "9 cells; rows = theta seed; cols = scene seed"


def main() -> int:
    profile, task, revision, card_state = load_profile()
    summary, curves, windows, heldout = load_records()
    subject_sha = summary["composite_record_sha256"]
    require(CAPTURE.exists() is False or not any(CAPTURE.iterdir()),
            REFUSAL + ":capture_dir_not_empty")
    CAPTURE.mkdir(parents=True, exist_ok=True)

    span_by_view = {
        "training-signal overview": "0..2000 iterations (x) by fitness "
                                    "0..~20 m (y)",
        "window detail": "0..~18 m window-mean scale (y)",
        "held-out matrix": "fitness range %.9f..%.9f m"
                           % (min(c["fitness"] for c in heldout["cells"]),
                              max(c["fitness"] for c in heldout["cells"]))}

    rows = []
    frame_files = {}
    builders = {
        "training-signal overview": lambda m: view_training_overview(
            m, summary, curves, windows),
        "window detail": lambda m: view_window_detail(
            m, summary, curves, windows),
        "held-out matrix": lambda m: view_heldout_matrix(
            m, summary, curves, windows, heldout),
    }
    for view_id in ("training-signal overview", "window detail",
                    "held-out matrix"):
        for mode in ("diagnostic", "clean"):
            img, panel_note = builders[view_id](mode)
            name = ("frame_" + view_id.replace(" ", "_") + "_"
                    + mode + ".png")
            path = CAPTURE / name
            img.save(path, "PNG")
            frame_files[name] = sha_bytes(path.read_bytes())
            rows.append({
                "view": view_id,
                "mode": mode,
                "native_view_declared_absent": True,
                "record_space_mapping": (
                    "the profile view cannot be rendered from retained "
                    "records (no pose/contact bytes retained); this panel "
                    "is the declared record-space counterpart of the view, "
                    "rendered from the pinned receipts"),
                "honesty_label": HONESTY if mode == "diagnostic" else
                    "clean record-space raster of pinned receipts (no "
                    "diagnostic overlay)",
                "camera": camera_record(view_id, mode,
                                        span_by_view[view_id], subject_sha,
                                        panel_note),
                "frame_file": name,
                "frame_sha256": frame_files[name],
                "subject_sha256": subject_sha,
            })

    ordered = [frame_files[k] for k in sorted(frame_files)]
    capture_sha = sha_bytes(b"".join(
        bytes.fromhex(h) for h in ordered))
    manifest = {
        "schema": "chimera.visual_capture_manifest.v1",
        "task_id": vi.TASK_SHORT,
        "profile_id": profile["id"],
        "run_id": vi.ATTEMPT_ID,
        "capture_sha256": capture_sha,
        "subject_sha256": subject_sha,
        "tick_interval": TICK_INTERVAL,
        "sheet_layout": {
            "capture_sha_definition":
                "sha256 over the concatenation of the frame PNG bytes in "
                "sorted frame_files order (the B03 image-set convention)",
            "frame_count": len(frame_files),
            "frame_files": frame_files},
        "views": rows,
        "absent_inventory": [
            "native pose/contact trajectory records (the runbook retains "
            "NONE: streaming chain hashing only) - the three profile views "
            "are delivered as declared record-space panels of the pinned "
            "outcome receipts, never as invented bodies",
            "native camera frames (no runtime session exists in this lane; "
            "the native visual walk claim belongs to the W07 runtime-"
            "consumption card)"],
        "validator": "CAMERA_METADATA_STRUCTURE_ONLY",
        "visual_acceptance": False,
        "visual_acceptance_reason":
            "record-space rasters of receipts are not engine frames; "
            "numerical evidence is the receipts; independent visual review "
            "remains the Sergeant's",
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B make_capture.py"},
    }
    (CAPTURE / "capture_manifest.json").write_bytes(canonical(manifest) + b"\n")

    context = {
        "schema": "chimera.capture_context.v1",
        "task_id": vi.TASK_SHORT,
        "run_id": vi.ATTEMPT_ID,
        "criteria_sha256": vi.CRITERIA_SHA256,
        "capture_sha256": capture_sha,
        "subject_sha256": subject_sha,
        "tick_interval": TICK_INTERVAL,
        "honesty_note": HONESTY,
        "state_hash_note":
            "every view row (clean AND diagnostic) carries the composite "
            "evaluation-record sha; view toggles preserve the record "
            "identity (profile falsifier instrument)",
        "artifact": {"kind": "image_set", "path": str(CAPTURE).replace(
            "\\", "/"), "sha256": capture_sha},
        "renderer": {"engine": "PIL Image (CPU software raster)",
                     "pillow_version": __import__("PIL").__version__,
                     "determinism": "fixed viewport/order; no z-buffer, "
                                    "no alpha blending"},
    }
    (CAPTURE / "capture_context.json").write_bytes(canonical(context) + b"\n")

    provenance = {
        "schema": "chimera.registry_profile_provenance.v1",
        "task_id": vi.TASK_SHORT,
        "source": "READ-ONLY sqlite (file:...?mode=ro) "
                  + str(vi.REGISTRY).replace("\\", "/"),
        "registry_revision_at_capture": revision,
        "card_state_at_capture": card_state,
        "criteria_sha256": vi.CRITERIA_SHA256,
    }
    (CAPTURE / "registry_profile_provenance.json").write_bytes(
        canonical(provenance) + b"\n")
    snapshot = {
        "schema": "chimera.registry_verification_profile_snapshot.v1",
        "task_id": vi.TASK_SHORT,
        "profile": profile,
        "task_view_scope": task.get("ontology", {}),
    }
    (CAPTURE / "registry_verification_profile.json").write_bytes(
        canonical(snapshot) + b"\n")

    # structure validation receipt (the validator named above)
    required = ["frame_id", "coordinate_unit", "position",
                "orientation_convention_and_values", "target",
                "distance_to_target", "projection",
                "vertical_fov_or_orthographic_span", "near_far_planes",
                "aspect_ratio", "viewport_resolution",
                "camera_motion_or_bookmark_sequence", "visibility_layers",
                "label_ids", "occlusion_or_xray_mode",
                "state_or_tick_interval"]
    row_checks = []
    for row in rows:
        cam = row["camera"]
        missing = [k for k in required if k not in cam]
        same_subject = row["subject_sha256"] == subject_sha
        row_checks.append({"frame_id": cam["frame_id"],
                           "camera_fields_present": len(cam) >= 16
                           and not missing,
                           "missing": missing,
                           "subject_sha_matches": same_subject})
    validation = {
        "schema": "chimera.capture_validation_receipt.v1",
        "task_id": vi.TASK_SHORT,
        "validator": "CAMERA_METADATA_STRUCTURE_ONLY",
        "rows": row_checks,
        "rows_total": len(row_checks),
        "rows_ok": sum(1 for r in row_checks
                       if r["camera_fields_present"]
                       and r["subject_sha_matches"]),
        "all_rows_share_subject_sha": all(r["subject_sha_matches"]
                                          for r in row_checks),
        "visual_acceptance": False,
        "determinism": {"canonical_json": True, "newline": "\n",
                        "command": "python -B make_capture.py"},
    }
    (CAPTURE / "capture_validation_receipt.json").write_bytes(
        canonical(validation) + b"\n")
    print("capture sha256:", capture_sha)
    print("rows:", validation["rows_ok"], "/", validation["rows_total"],
          "structure-OK; all rows share the subject sha:",
          validation["all_rows_share_subject_sha"])
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except vi.Refusal as exc:
        print("REFUSAL: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
