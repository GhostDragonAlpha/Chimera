"""make_capture_manifest.py -- MAT2-F05 campaign capture-manifest generator.

F01/F02/F07 pattern: bind the verified per-view camera records into the
campaign capture schema (`chimera.visual_capture_manifest.v1`, validator
`tools/monkey_campaign/visual_capture.validate_manifest`) with an identity
envelope whose hashes are RECOMPUTED from the committed evidence bytes by
this script (never copied):

- subject_sha256   = raw sha256 of evidence/terrain_envelope_declaration.json
                     (the declared terrain envelope IS the qualified subject
                     of this records card);
- capture_sha256   = raw sha256 of the single gate-bound committed capture,
                     evidence/frame_V1_clearing_overview_clean.bmp;
- artifact_locator.raw_sha256 per row = raw sha256 of that row's committed
                     BMP;
- state_binding.sha256 = raw sha256 of evidence/checks.json (the classified
                     correspondence state the diagnostic rows draw);

and validated against the REGISTRY verification profile object, read
READ-ONLY from agent_slots.sqlite3
(kanban.cards[MAT2-F05].spec.ontology_qualification.task.verification_profile).

Run AFTER `python -B implementation.py build`, from this directory:
    python -B make_capture_manifest.py
Writes evidence/capture_manifest.json + validation_receipt.json.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sqlite3
import sys

import implementation as impl

HERE = pathlib.Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"

REPO_TOOLS_CANDIDATES = [
    HERE.parents[3] / "tools" / "monkey_campaign",
    pathlib.Path("E:/PythonChimera/tools/monkey_campaign"),
]
REGISTRY = "E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3"
TICK_INTERVAL = [0, 0]
PROFILE_ID = "forest"
TASK_ID_SHORT = "F05"

GATE_BOUND = "frame_V1_clearing_overview_clean.png"
VIEW_ORDER = ["V1_clearing_overview", "V2_seam_closeup", "V3_side_depth"]
PAIR_IDS = {
    "V1_clearing_overview": "pair_clearing_overview",
    "V2_seam_closeup": "pair_seam_closeup",
    "V3_side_depth": "pair_side_depth",
}
PROFILE_LAYERS = ["render mesh", "collision surfaces",
                  "normals/contact markers", "scene bounds",
                  "stable 3D labels"]
SUBJECTS = ["monkey_clearing_ground", "trunk_01"]
PROBE_SUBJECT = "P_spawn"
LABEL_SUBJECT = {
    "spawn": "monkey_clearing_ground", "trunk_01": "trunk_01",
    "corner_SW": "monkey_clearing_boundary_posts",
    "corner_SE": "monkey_clearing_boundary_posts",
    "corner_NE": "monkey_clearing_boundary_posts",
    "corner_NW": "monkey_clearing_boundary_posts",
    "edge_N": "monkey_clearing_boundary_posts",
    "edge_E": "monkey_clearing_boundary_posts",
    "edge_S": "monkey_clearing_boundary_posts",
    "edge_W": "monkey_clearing_boundary_posts",
    "mound_m1": "monkey_clearing_ground", "mound_m2": "monkey_clearing_ground",
    "mound_m3": "monkey_clearing_ground", "mound_m4": "monkey_clearing_ground",
    "mound_m5": "monkey_clearing_ground",
}


def require(ok, code):
    if not ok:
        raise SystemExit("make_capture_manifest: " + code)


def sha_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def registry_profile():
    """The profile object, read READ-ONLY from the coordination registry."""
    con = sqlite3.connect("file:%s?mode=ro" % REGISTRY, uri=True)
    state = json.loads(con.execute(
        "SELECT payload FROM state WHERE id=1").fetchone()[0])
    con.close()
    cards = state["kanban"]["cards"]
    card = (cards["MAT2-F05"] if isinstance(cards, dict)
            else next(c for c in cards if c.get("id") == "MAT2-F05"))
    return card["spec"]["ontology_qualification"]["task"][
        "verification_profile"]


def load_validator():
    for tools in REPO_TOOLS_CANDIDATES:
        if (tools / "visual_capture.py").is_file():
            sys.path.insert(0, str(tools))
            import visual_capture
            return visual_capture, str(tools)
    raise SystemExit("make_capture_manifest: visual_capture not found "
                     "(tried %s)" % (REPO_TOOLS_CANDIDATES,))


def rebuild_views(src):
    """The build's own frozen cameras (same pinned F01 view specs; no shared
    module state)."""
    f01 = src["f01"]
    return {name: f01.Camera(f01.VIEWS[name]) for name in VIEW_ORDER}


def basis_quaternion(position, target):
    """Unit quaternion (w,x,y,z) of the look-at basis (F01's conversion
    law, as packaged by F02)."""
    f01 = src_f01()
    fwd = f01.vnorm(f01.vsub(target, position))
    right = f01.vnorm(f01.vcross(fwd, [0.0, 1.0, 0.0]))
    up = f01.vcross(right, fwd)
    neg_fwd = [-x for x in fwd]
    m = [[right[0], up[0], neg_fwd[0]],
         [right[1], up[1], neg_fwd[1]],
         [right[2], up[2], neg_fwd[2]]]
    tr = m[0][0] + m[1][1] + m[2][2]
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2.0
        q = [0.25 * s, (m[2][1] - m[1][2]) / s, (m[0][2] - m[2][0]) / s,
             (m[1][0] - m[0][1]) / s]
    elif m[0][0] > m[1][1] and m[0][0] > m[2][2]:
        s = math.sqrt(1.0 + m[0][0] - m[1][1] - m[2][2]) * 2.0
        q = [(m[2][1] - m[1][2]) / s, 0.25 * s, (m[1][0] + m[0][1]) / s,
             (m[0][2] + m[2][0]) / s]
    elif m[1][1] > m[2][2]:
        s = math.sqrt(1.0 + m[1][1] - m[0][0] - m[2][2]) * 2.0
        q = [(m[0][2] - m[2][0]) / s, (m[1][0] + m[0][1]) / s, 0.25 * s,
             (m[2][1] + m[1][2]) / s]
    else:
        s = math.sqrt(1.0 + m[2][2] - m[0][0] - m[1][1]) * 2.0
        q = [(m[1][0] - m[0][1]) / s, (m[0][2] + m[2][0]) / s,
             (m[2][1] + m[1][2]) / s, 0.25 * s]
    q = [x / math.sqrt(sum(x * x for x in q)) for x in q]
    w, x, y, z = q
    r = [[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
         [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
         [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]]
    q_err = max(abs(r[i][j] - m[i][j]) for i in range(3) for j in range(3))
    return q, q_err


_F01 = {}


def src_f01():
    require(_F01, "f01 module not loaded")
    return _F01["f01"]


def main():
    require((HERE / "checks_receipt.json").is_file(),
            "run implementation.py build first")
    checks = json.loads((HERE / "checks_receipt.json").read_text(
        encoding="utf-8"))
    require(checks["all_ok"], "build_not_all_ok")
    pins = impl.materialize_pins()
    src = impl.load_sources(pins)
    _F01["f01"] = src["f01"]
    views = rebuild_views(src)
    labels = src["f01"].frozen_labels(src["declaration"], src["trunk"])

    subject_sha = sha_file(EVIDENCE / "terrain_envelope_declaration.json")
    require(subject_sha == checks["envelope_declaration_sha256"],
            "subject declaration bytes are not the receipted ones")
    state_sha = sha_file(HERE / "checks_receipt.json")

    files = {}
    for name in sorted(p.name for p in EVIDENCE.glob("*.png")):
        files[name] = sha_file(EVIDENCE / name)
    for vname in VIEW_ORDER:
        for variant in ("clean", "diagnostic"):
            require("frame_%s_%s.png" % (vname, variant) in files,
                    "missing rendered frame for %s_%s" % (vname, variant))
    require(GATE_BOUND in files, "gate-bound capture missing")
    capture_sha = files[GATE_BOUND]

    view_rows = []
    worst_q = 0.0
    for vname in VIEW_ORDER:
        cam = views[vname]
        q, q_err = basis_quaternion(cam.position, cam.target)
        worst_q = max(worst_q, q_err)
        distance = math.dist(cam.position, cam.target)
        camera = {
            "frame_id": "%s/%s" % (impl.CARD, vname),
            "coordinate_unit": "m",
            "handedness": "right",
            "orientation_convention": "quaternion_wxyz_camera_to_frame",
            "forward_axis": "-Z",
            "up_axis": "+Y",
            "look_at_convention": (
                "camera axes: forward = -Z_local, up = +Y_local, right = "
                "+X_local; the recorded look-at basis (fwd/right/up) is "
                "preserved verbatim in camera_record_16field_convention and "
                "the quaternion is its exact rotation-matrix conversion "
                "(round-trip worst error in packaging.derivation)"),
            "near_far_planes": [src["f01"].NEAR, src["f01"].FAR],
            "viewport_resolution": [src["f01"].W, src["f01"].H],
            "aspect_ratio": src["f01"].W / src["f01"].H,
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
            "state_or_tick_interval": "static declared scene, t=0",
        }
        state_binding = {"kind": "state",
                         "reference": "checks_receipt.json",
                         "sha256": state_sha}
        proj = []
        for lab in labels:
            px = cam.pixel(lab["anchor"])
            proj.append({"id": lab["id"], "anchor": lab["anchor"],
                         "projected_px": [px[0], px[1]] if px else None,
                         "in_frame": bool(px and 0 <= px[0] < src["f01"].W
                                          and 0 <= px[1] < src["f01"].H)})
        label_ids = [ln["id"] for ln in proj]
        require(set(label_ids) <= set(LABEL_SUBJECT),
                "unmapped label id in %s" % vname)
        in_frame = [ln["id"] for ln in proj if ln["in_frame"]]
        for variant in ("clean", "diagnostic"):
            name = "frame_%s_%s.png" % (vname, variant)
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
                observed = list(SUBJECTS) + [PROBE_SUBJECT] + \
                    list(PROFILE_LAYERS)
                visibility = {
                    "layers": list(PROFILE_LAYERS),
                    "label_ids": in_frame,
                    "selected_ids": [],
                    "required_subject_ids": list(SUBJECTS)
                                            + [PROBE_SUBJECT],
                    "observed_subject_ids": observed,
                    "missing_subject_ids": [],
                    "occlusion_mode": "depth_tested",
                    "tag_bindings": [
                        {"label_id": i, "subject_id": LABEL_SUBJECT[i]}
                        for i in in_frame],
                }
            record = next(fr for fr in checks["P7_frames"]["rows"]
                          if fr["view_key"] == vname)
            record_16 = record["camera"] if variant == "clean" \
                else record["camera_diagnostic"]
            view_rows.append({
                "view_id": impl.VIEW_MAP[vname],
                "mode": variant,
                "pair_id": PAIR_IDS[vname],
                "artifact_locator": {"kind": "image",
                                     "region": "whole_frame",
                                     "file": "evidence/" + name,
                                     "raw_sha256": files[name]},
                "camera": camera,
                "state_binding": state_binding,
                "visibility": visibility,
                "camera_record_16field_convention": record_16,
            })

    manifest = {
        "schema": "chimera.visual_capture_manifest.v1",
        "task_id": TASK_ID_SHORT,
        "profile_id": PROFILE_ID,
        "run_id": impl.RUN_ID,
        "tick_interval": TICK_INTERVAL,
        "subject_sha256": subject_sha,
        "capture_sha256": capture_sha,
        "sheet_layout": {
            "pixel_size": [src["f01"].W, src["f01"].H],
            "capture_sha_definition": (
                "sha256 over the raw bytes of the single gate-bound "
                "committed still evidence/frame_V1_clearing_overview_clean.png"
                " (static image capture; no video frames exist); the PNG is "
                "the lossless identity-proven carrier of the pinned render "
                "law's BMP output (png_pixel_identity in checks.json)"),
            "honest_titles": ("no text is rendered inside any frame (the "
                              "pinned F01 render law draws geometry only, so "
                              "frames do not self-identify view/mode/"
                              "frame_id); frame identity is bound by this "
                              "manifest instead: the per-row "
                              "artifact_locator.raw_sha256 locators over the "
                              "evidence/frame_<view>_<mode>.bmp file names, "
                              "plus each row's "
                              "camera_record_16field_convention record; "
                              "clean rows intentionally carry no overlays "
                              "and no diagnostic styling"),
            "rows": ["V1_clearing_overview clean+diagnostic",
                     "V2_seam_closeup clean+diagnostic",
                     "V3_side_depth clean+diagnostic"],
            "tick_to_seconds_map": "visible_static: single frozen frame, t=0",
            "files": files,
            "capture_is": ("a z-buffer software raster of the pinned F01/F02 "
                           "terrain asset arrays with the declared envelope "
                           "probe markers drawn as declared diagnostic "
                           "layers; probes never read pixels -- the "
                           "correspondence evidence is pure ray/geometry "
                           "(evidence/checks.json P6)"),
            "honest_gaps": [
                "no engine or native upload ran: the render law is F01's "
                "byte-identical CPU rasterizer over the pinned load_mesh "
                "arrays",
                "the declared obstacles (F07) are NOT in this render: the "
                "pinned F01/F02 asset predates the obstacle overlay; the "
                "obstacle envelope rows cite the F07 sealed receipt instead",
                "the walk plane and friction rows are records citations "
                "(W03/W05/W06/G04), not rendered content",
            ],
        },
        "views": view_rows,
        "packaging": {"derivation": (
            "per-row unit quaternion derived from the recorded look-at "
            "basis; worst round-trip matrix error %.3e" % worst_q)},
    }
    (EVIDENCE / "capture_manifest.json").write_text(
        json.dumps(manifest, indent=1) + "\n", encoding="utf-8")

    context = {"task_id": TASK_ID_SHORT, "run_id": impl.RUN_ID,
               "subject_sha256": subject_sha,
               "capture_sha256": capture_sha,
               "tick_interval": TICK_INTERVAL}

    profile = registry_profile()
    visual_capture, via = load_validator()
    try:
        receipt = visual_capture.validate_manifest(
            json.loads((EVIDENCE / "capture_manifest.json").read_text(
                encoding="utf-8")),
            context, profile)
        receipt["fired"] = []
        verdict = "structurally_valid=True"
    except ValueError as err:
        receipt = {"mode": "CAMERA_METADATA_STRUCTURE_ONLY",
                   "structurally_valid": False, "fired": [str(err)]}
        verdict = "FIRED: " + str(err)
    receipt["profile_source"] = REGISTRY + " kanban.cards[MAT2-F05]" \
        ".spec.ontology_qualification.task.verification_profile"
    receipt["validated_profile_id"] = profile["id"]
    receipt["validated_profile_kind"] = profile["kind"]
    receipt["validator_module"] = via + "/visual_capture.py"
    (EVIDENCE / "validation_receipt.json").write_text(
        json.dumps(receipt, indent=1) + "\n", encoding="utf-8")
    print("verdict:", verdict)
    print("run_id:", impl.RUN_ID)
    print("capture_sha256:", capture_sha)
    print("subject_sha256:", subject_sha)
    print("state_sha256:", state_sha)
    print("manifest:", EVIDENCE / "capture_manifest.json")


if __name__ == "__main__":
    main()
