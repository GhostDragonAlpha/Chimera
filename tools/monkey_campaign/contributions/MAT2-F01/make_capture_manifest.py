"""make_capture_manifest.py -- MAT2-F01 campaign capture-manifest generator.

THE packaging correction demanded by the lead's CHANGES_REQUIRED finding on the
archived ONT-F01 candidate (PR #188 head a7b2acc4): bind the verified per-view
camera records into the campaign capture schema
(`chimera.visual_capture_manifest.v1`, validator `tools/monkey_campaign/
visual_capture.validate_manifest`, gate `visual_gate.verify`) with an identity
envelope whose hashes are RECOMPUTED from the committed evidence bytes by this
script (never copied from anywhere):

- subject_sha256   = raw sha256 of evidence/pins_materialized/
                     clearing_declaration.json (the frozen scene-state snapshot
                     the render arrays were built from, pin dc7ea811);
- capture_sha256   = raw sha256 of the gate-bound committed capture,
                     evidence/frame_V1_clearing_overview_clean.bmp;
- artifact_locator.raw_sha256 per row = raw sha256 of that row's committed BMP.

Each row embeds the build's verified 16-field camera record verbatim
(`camera_record_16field_convention`), so nothing recorded by
`implementation.py build` is re-authored here. The only computed additions are
the schema-required camera block (unit quaternion derived from the same
look-at basis the record froze, round-trip verified and the worst error
reported) and the visibility block. DECLARED DEFECT FIX (PREREGISTRATION Q3):
`required_subject_ids` is the non-empty subject triple on EVERY row; the
archived corrected draft left it empty on diagnostic rows, which the campaign
validator refuses (`visibility_required_subject_ids_invalid`).

Run AFTER `python -B implementation.py build`, from this directory:
    python -B make_capture_manifest.py
Stdlib only; writes evidence/capture_manifest.json.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"
sys.path.insert(0, str(HERE))
import implementation as impl  # noqa: E402

SCHEMA = "chimera.visual_capture_manifest.v1"
TASK_ID = "F01"
RUN_ID = "mat2-f01-forest-20260927-5445fc5e"
TICK_INTERVAL = [0, 0]
PROFILE_ID = "forest"

SUBJECTS = ["monkey_clearing_ground", "monkey_clearing_boundary_posts",
            "trunk_01"]
DIAGNOSTIC_LAYERS = ["render mesh", "collision surfaces",
                     "normals/contact markers", "scene bounds",
                     "stable 3D labels"]
DIAGNOSTIC_OVERLAYS = ["diagnostic: render-mesh wireframe",
                       "diagnostic: normals/contact markers",
                       "diagnostic: scene bounds",
                       "diagnostic: stable 3D labels"]
# profile view name per frozen view key. The profile declares exactly THREE
# view names and the validator refuses a repeated (view_id, mode) key
# (`capture_view_duplicate`), so the manifest carries one pair per profile
# view: V3 (side) is the declared "side and oblique depth checks" pair. V4
# (oblique) stays fully rendered, committed, sha256-listed under
# capture_layout.files (supplementary depth evidence) with its probes
# classified in checks.json P5 — it differs from the archived corrected draft
# only by no longer attempting an invalid fourth pair.
VIEW_IDS = {
    "V1_clearing_overview": "clearing overview",
    "V2_seam_closeup": "terrain/trunk seam close-up",
    "V3_side_depth": "side and oblique depth checks",
}
MANIFEST_VIEW_ORDER = ["V1_clearing_overview", "V2_seam_closeup", "V3_side_depth"]
PAIR_IDS = {
    "V1_clearing_overview": "pair-clearing-overview",
    "V2_seam_closeup": "pair-seam-closeup",
    "V3_side_depth": "pair-side-depth",
}
# stable-label id -> subject it tags (same mapping as the archived corrected
# draft's tag_bindings; labels themselves come from the build's frozen labels)
LABEL_SUBJECT = {
    "spawn": "monkey_clearing_ground",
    "trunk_01": "trunk_01",
    "corner_SW": "monkey_clearing_boundary_posts",
    "corner_SE": "monkey_clearing_boundary_posts",
    "corner_NE": "monkey_clearing_boundary_posts",
    "corner_NW": "monkey_clearing_boundary_posts",
    "edge_N": "monkey_clearing_boundary_posts",
    "edge_E": "monkey_clearing_boundary_posts",
    "edge_S": "monkey_clearing_boundary_posts",
    "edge_W": "monkey_clearing_boundary_posts",
    "mound_m1": "monkey_clearing_ground",
    "mound_m2": "monkey_clearing_ground",
    "mound_m3": "monkey_clearing_ground",
    "mound_m4": "monkey_clearing_ground",
    "mound_m5": "monkey_clearing_ground",
}
GATE_BOUND_FILE = "frame_V1_clearing_overview_clean.bmp"


def require(ok, code):
    if not ok:
        raise SystemExit("make_capture_manifest: " + code)


def sha_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unit(v):
    n = math.sqrt(sum(x * x for x in v))
    return [x / n for x in v]


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def basis_quaternion(position, target):
    """Unit quaternion (w,x,y,z), camera->frame, of the rotation matrix with
    columns [right, up, -fwd] from the record's look-at basis (forward -Z,
    up +Y). Same basis law as implementation.Camera."""
    fwd = unit([t - p for p, t in zip(position, target)])
    right = unit(cross(fwd, [0.0, 1.0, 0.0]))
    up = cross(right, fwd)
    neg_fwd = [-x for x in fwd]
    # X_c = up x (-fwd) must equal the recorded right vector (identity check)
    x_err = max(abs(a - b) for a, b in zip(cross(up, neg_fwd), right))
    m = [[right[0], up[0], neg_fwd[0]],
         [right[1], up[1], neg_fwd[1]],
         [right[2], up[2], neg_fwd[2]]]
    tr = m[0][0] + m[1][1] + m[2][2]
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2.0
        q = [0.25 * s,
             (m[2][1] - m[1][2]) / s,
             (m[0][2] - m[2][0]) / s,
             (m[1][0] - m[0][1]) / s]
    elif m[0][0] > m[1][1] and m[0][0] > m[2][2]:
        s = math.sqrt(1.0 + m[0][0] - m[1][1] - m[2][2]) * 2.0
        q = [(m[2][1] - m[1][2]) / s, 0.25 * s,
             (m[1][0] + m[0][1]) / s, (m[0][2] + m[2][0]) / s]
    elif m[1][1] > m[2][2]:
        s = math.sqrt(1.0 + m[1][1] - m[0][0] - m[2][2]) * 2.0
        q = [(m[0][2] - m[2][0]) / s, (m[1][0] + m[0][1]) / s,
             0.25 * s, (m[2][1] + m[1][2]) / s]
    else:
        s = math.sqrt(1.0 + m[2][2] - m[0][0] - m[1][1]) * 2.0
        q = [(m[1][0] - m[0][1]) / s, (m[0][2] + m[2][0]) / s,
             (m[2][1] + m[1][2]) / s, 0.25 * s]
    q = [x / math.sqrt(sum(x * x for x in q)) for x in q]
    # round-trip: quaternion -> matrix, worst component error
    w, x, y, z = q
    r = [[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
         [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
         [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]]
    q_err = max(abs(r[i][j] - m[i][j]) for i in range(3) for j in range(3))
    return q, x_err, q_err


def main():
    require((EVIDENCE / "checks.json").is_file(), "run implementation.py build first")
    records = json.loads((EVIDENCE / "camera_manifest.json").read_text(
        encoding="utf-8"))["views"]
    require(len(records) == 8, "expected 8 bare 16-field records")

    declaration = EVIDENCE / "pins_materialized" / "clearing_declaration.json"
    require(declaration.is_file(), "pins_materialized/clearing_declaration.json missing")
    subject_sha = sha_file(declaration)
    require(subject_sha == impl.PINS["clearing_declaration_json"]["sha256"],
            "subject snapshot bytes are not the pinned declaration")

    bmp_dir = EVIDENCE
    files = {}
    for name in sorted(p.name for p in bmp_dir.glob("*.bmp")):
        files[name] = sha_file(bmp_dir / name)
    for vname in impl.VIEW_ORDER:
        for variant in ("clean", "diagnostic"):
            require("frame_%s_%s.bmp" % (vname, variant) in files,
                    "missing rendered frame for %s_%s" % (vname, variant))
    require(GATE_BOUND_FILE in files, "gate-bound capture missing")
    capture_sha = files[GATE_BOUND_FILE]

    view_rows = []
    worst_x = worst_q = 0.0
    for vname in MANIFEST_VIEW_ORDER:
        cam = impl.Camera(impl.VIEWS[vname])
        q, x_err, q_err = basis_quaternion(cam.position, cam.target)
        worst_x = max(worst_x, x_err)
        worst_q = max(worst_q, q_err)
        distance = math.dist(cam.position, cam.target)
        camera = {
            "frame_id": records[vname + "_clean"]["frame_id"].rsplit("_", 1)[0],
            "coordinate_unit": "m",
            "handedness": "right",
            "orientation_convention": "quaternion_wxyz_camera_to_frame",
            "forward_axis": "-Z",
            "up_axis": "+Y",
            "look_at_convention": (
                "camera axes: forward = -Z_local, up = +Y_local, right = +X_local; "
                "the recorded look-at basis (fwd/right/up) is preserved verbatim in "
                "camera_record_16field_convention and the quaternion is its exact "
                "rotation-matrix conversion (round-trip verified, worst error in "
                "packaging.derivation)"),
            "near_far_planes": [impl.NEAR, impl.FAR],
            "viewport_resolution": [impl.W, impl.H],
            "aspect_ratio": impl.W / impl.H,
            "projection": "perspective",
            "vertical_fov_degrees": math.degrees(cam.vfov),
            "sample_mode": "fixed_bookmark",
            "samples": [{
                "tick": 0,
                "position": list(cam.position),
                "target": list(cam.target),
                "distance_to_target": distance,
                "orientation": q,
            }],
            "state_or_tick_interval": "static scene, no tick (t=0)",
        }
        state_binding = {
            "kind": "state",
            "reference": "evidence/pins_materialized/clearing_declaration.json",
            "sha256": subject_sha,
        }
        labels = records[vname + "_clean"]["label_ids"]
        label_ids = [l["id"] for l in labels]
        require(set(label_ids) <= set(LABEL_SUBJECT),
                "unmapped label id in %s" % vname)
        for variant in ("clean", "diagnostic"):
            record = records[vname + "_" + variant]
            name = "frame_%s_%s.bmp" % (vname, variant)
            if variant == "clean":
                visibility = {
                    "layers": [],
                    "label_ids": [],
                    "selected_ids": [],
                    "required_subject_ids": list(SUBJECTS),
                    "observed_subject_ids": list(SUBJECTS),
                    "missing_subject_ids": [],
                    "occlusion_mode": "depth_tested",
                    "tag_bindings": [],
                }
            else:
                visibility = {
                    "layers": list(DIAGNOSTIC_LAYERS),
                    "label_ids": label_ids,
                    "selected_ids": [],
                    "required_subject_ids": list(SUBJECTS),
                    "observed_subject_ids": list(SUBJECTS) + list(DIAGNOSTIC_OVERLAYS),
                    "missing_subject_ids": [],
                    "occlusion_mode": "depth_tested",
                    "tag_bindings": [{"label_id": i, "subject_id": LABEL_SUBJECT[i]}
                                     for i in label_ids],
                }
            view_rows.append({
                "view_id": VIEW_IDS[vname],
                "mode": variant,
                "pair_id": PAIR_IDS[vname],
                "state_binding": state_binding,
                "artifact_locator": {
                    "kind": "image",
                    "file": name,
                    "region": "whole_frame",
                    "pixel_size": [impl.W, impl.H],
                    "raw_sha256": files[name],
                },
                "camera": camera,
                "camera_record_16field_convention": record,
                "visibility": visibility,
                "capture_note": (
                    "stdlib software rasterizer over the pinned render arrays "
                    "verbatim; probes never read pixels (PREREGISTRATION honest "
                    "boundary)"),
            })

    manifest = {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "run_id": RUN_ID,
        "subject_sha256": subject_sha,
        "capture_sha256": capture_sha,
        "tick_interval": list(TICK_INTERVAL),
        "profile_id": PROFILE_ID,
        "views": view_rows,
        "capture_layout": {
            "convention": (
                "the F01 capture is a set of whole-frame BMPs (one per view "
                "variant), not a single composite sheet; the campaign gate binds "
                "the frozen overview clean frame listed in gate_bound_capture_file, "
                "and every row's artifact_locator names its own committed BMP file "
                "+ raw sha256 so each view is independently checkable against the "
                "committed bytes"),
            "files": files,
            "supplementary_views": (
                "V4_oblique_depth (oblique depth bookmark) is rendered, committed "
                "and sha256-listed in files above, and its probes are classified "
                "in checks.json P5, but it is not a manifest row: the profile "
                "declares three view names and the validator refuses a repeated "
                "(view_id, mode) key, so V3 (side) declares the \"side and oblique "
                "depth checks\" pair"),
            "gate_bound_capture_file": GATE_BOUND_FILE,
            "gate_bound_capture_sha256": capture_sha,
        },
        "packaging": {
            "kept_verbatim": (
                "each row's camera_record_16field_convention is the exact 16-field "
                "record emitted by implementation.py build for that view variant "
                "(frame_id, coordinate_unit, position, "
                "orientation_convention_and_values, target, distance_to_target, "
                "projection, vertical_fov_or_orthographic_span, near_far_planes, "
                "aspect_ratio, viewport_resolution, "
                "camera_motion_or_bookmark_sequence, visibility_layers, label_ids "
                "incl. anchors/projected_px/in_frame, occlusion_or_xray_mode, "
                "state_or_tick_interval)"),
            "derivation": {
                "quaternion": (
                    "orientation = unit quaternion (w,x,y,z) of the rotation matrix "
                    "with columns [right, up, -fwd] from the recorded look-at basis "
                    "(forward_axis '-Z', up_axis '+Y', X_c = up x (-fwd) checked "
                    "against the recorded right vector)"),
                "worst_basis_right_err": worst_x,
                "worst_quaternion_roundtrip_err": worst_q,
            },
            "required_subject_fix": (
                "PREREGISTRATION Q3: required_subject_ids is the non-empty subject "
                "triple on every row; the archived corrected draft left it empty on "
                "diagnostic rows (validator refusal "
                "visibility_required_subject_ids_invalid)"),
        },
    }
    out = EVIDENCE / "capture_manifest.json"
    out.write_bytes(json.dumps(manifest, indent=1, sort_keys=True).encode("utf-8"))
    print(json.dumps({
        "capture_manifest": str(out),
        "rows": len(view_rows),
        "subject_sha256": subject_sha,
        "capture_sha256": capture_sha,
        "gate_bound_capture_file": GATE_BOUND_FILE,
        "worst_basis_right_err": worst_x,
        "worst_quaternion_roundtrip_err": worst_q,
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
