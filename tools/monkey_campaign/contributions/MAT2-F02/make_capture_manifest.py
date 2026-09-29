"""make_capture_manifest.py -- MAT2-F02 campaign capture-manifest generator.

M01/F01 pattern: bind the verified per-view camera records into the campaign
capture schema (`chimera.visual_capture_manifest.v1`, validator
`tools/monkey_campaign/visual_capture.validate_manifest`) with an identity
envelope whose hashes are RECOMPUTED from the committed evidence bytes by this
script (never copied):

- subject_sha256   = raw sha256 of pins/terrain_bundle.json (the tied asset:
                     the rendered ground IS the collision/query surface);
- capture_sha256   = raw sha256 of the gate-bound committed capture,
                     evidence/frame_V1_clearing_overview_clean.bmp (the single
                     on-disk artifact);
- artifact_locator.raw_sha256 per row = raw sha256 of that row's committed BMP;
- state_binding.sha256 = raw sha256 of evidence/contact_trace.json (the settled
  contact state the diagnostic rows draw);

and validated against the REGISTRY verification profile object, read
READ-ONLY from agent_slots.sqlite3
(kanban.cards[MAT2-F02].spec.ontology_qualification.task.verification_profile).

Run AFTER `python -B run_terrain_contact.py build`, from this directory:
    python -B make_capture_manifest.py
Stdlib only; writes evidence/capture_manifest.json + validation_receipt.json.
"""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sqlite3
import sys

import terrain_contact as tc
import f01_implementation as f01
import run_terrain_contact as run

HERE = pathlib.Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"

REPO_TOOLS_CANDIDATES = [
    pathlib.Path("E:/PythonChimera/tools/monkey_campaign"),
]
REGISTRY = "E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3"
TICK_INTERVAL = [0, 0]
PROFILE_ID = "forest"
TASK_ID_SHORT = "F02"

GATE_BOUND = run.GATE_BOUND_FILE


def require(ok, code):
    if not ok:
        raise SystemExit("make_capture_manifest: " + code)


def sha_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def registry_profile():
    """The profile object, read READ-ONLY from the coordination registry."""
    con = sqlite3.connect(f"file:{REGISTRY}?mode=ro", uri=True)
    state = json.loads(con.execute("SELECT payload FROM state WHERE id=1")
                       .fetchone()[0])
    con.close()
    cards = state["kanban"]["cards"]
    card = (cards["MAT2-F02"] if isinstance(cards, dict)
            else next(c for c in cards if c.get("id") == "MAT2-F02"))
    return card["spec"]["ontology_qualification"]["task"]["verification_profile"]


def load_validator():
    last_err = None
    for tools in REPO_TOOLS_CANDIDATES:
        if (tools / "visual_capture.py").is_file():
            sys.path.insert(0, str(tools))
            import visual_capture
            return visual_capture, str(tools)
        last_err = tools
    raise SystemExit(f"make_capture_manifest: visual_capture not found "
                     f"(tried {REPO_TOOLS_CANDIDATES})")


def rebuild_cameras(trace):
    """Deterministically rebuild the build's cameras: V1/V4 from the frozen
    specs; V2/V3 targets are the settled probe centres from the trace (the
    same rule run_terrain_contact.build used). No shared module state."""
    views = {"V1_clearing_overview": f01.Camera(run.VIEWS["V1_clearing_overview"]),
             "V4_oblique_depth": f01.Camera(run.VIEWS["V4_oblique_depth"])}
    v2 = dict(run.V2_SPEC)
    v2["target"] = list(trace["sites"]["S4"]["rest_probe_centre_clearing_m"])
    v3 = dict(run.V3_SPEC)
    v3["target"] = list(trace["sites"]["S3"]["rest_probe_centre_clearing_m"])
    views["V2_contact_seam"] = f01.Camera(v2)
    views["V3_side_depth"] = f01.Camera(v3)
    return views


def main():
    require((EVIDENCE / "checks.json").is_file(),
            "run run_terrain_contact.py build first")
    checks = json.loads((EVIDENCE / "checks.json").read_text(encoding="utf-8"))
    require(checks["all_ok"], "build_not_all_ok")
    records = json.loads((EVIDENCE / "camera_manifest.json").read_text(
        encoding="utf-8"))["views"]
    require(len(records) == 8, "expected 8 bare 16-field records")
    trace = json.loads((EVIDENCE / "contact_trace.json").read_text(encoding="utf-8"))
    cameras = rebuild_cameras(trace)

    asset = HERE / "pins" / "terrain_bundle.json"
    subject_sha = sha_file(asset)
    require(subject_sha == tc.PINS["terrain_bundle_json"]["sha256"],
            "subject asset bytes are not the pinned bundle")

    trace_path = EVIDENCE / "contact_trace.json"
    require(trace_path.is_file(), "evidence/contact_trace.json missing "
                                  "(written by run_terrain_contact.build)")
    trace_sha = sha_file(trace_path)

    files = {}
    for name in sorted(p.name for p in EVIDENCE.glob("*.bmp")):
        files[name] = sha_file(EVIDENCE / name)
    for vname in ("V1_clearing_overview", "V2_contact_seam", "V3_side_depth",
                  "V4_oblique_depth"):
        for variant in ("clean", "diagnostic"):
            require("frame_%s_%s.bmp" % (vname, variant) in files,
                    "missing rendered frame for %s_%s" % (vname, variant))
    require(GATE_BOUND in files, "gate-bound capture missing")
    capture_sha = files[GATE_BOUND]

    view_rows = []
    worst_q = 0.0
    for vname in run.MANIFEST_VIEW_ORDER:
        cam = cameras[vname]
        q, q_err = run.basis_quaternion(cam.position, cam.target)
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
                "rotation-matrix conversion (round-trip worst error in "
                "packaging.derivation)"),
            "near_far_planes": [f01.NEAR, f01.FAR],
            "viewport_resolution": [f01.W, f01.H],
            "aspect_ratio": f01.W / f01.H,
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
            "state_or_tick_interval": "static settled contact state, t=0",
        }
        state_binding = {"kind": "state", "reference": "evidence/contact_trace.json",
                         "sha256": trace_sha}
        labels = records[vname + "_clean"]["label_ids"]
        label_ids = [ln["id"] for ln in labels]
        require(set(label_ids) <= set(run.LABEL_SUBJECT),
                "unmapped label id in %s" % vname)
        in_frame = [ln["id"] for ln in labels if ln["in_frame"]]
        for variant in ("clean", "diagnostic"):
            record = records[vname + "_" + variant]
            name = "frame_%s_%s.bmp" % (vname, variant)
            if variant == "clean":
                visibility = {
                    "layers": [],
                    "label_ids": [],
                    "selected_ids": [],
                    "required_subject_ids": list(run.SUBJECTS),
                    "observed_subject_ids": list(run.SUBJECTS),
                    "missing_subject_ids": [],
                    "occlusion_mode": "depth_tested",
                    "tag_bindings": [],
                }
            else:
                observed = list(run.SUBJECTS) + [run.PROBE_SUBJECT] + \
                    list(run.DIAGNOSTIC_OVERLAYS)
                visibility = {
                    "layers": list(run.PROFILE_LAYERS),
                    "label_ids": in_frame,
                    "selected_ids": [],
                    "required_subject_ids": list(run.SUBJECTS)
                                            + [run.PROBE_SUBJECT],
                    "observed_subject_ids": observed,
                    "missing_subject_ids": [],
                    "occlusion_mode": "depth_tested",
                    "tag_bindings": [{"label_id": i, "subject_id": run.LABEL_SUBJECT[i]}
                                     for i in in_frame],
                }
            view_rows.append({
                "view_id": run.PROFILE_VIEW_IDS[vname],
                "mode": variant,
                "pair_id": run.PAIR_IDS[vname],
                "artifact_locator": {"kind": "image", "region": "whole_frame",
                                     "file": "evidence/" + name,
                                     "raw_sha256": files[name]},
                "camera": camera,
                "state_binding": state_binding,
                "visibility": visibility,
                "camera_record_16field_convention": record,
            })

    manifest = {
        "schema": "chimera.visual_capture_manifest.v1",
        "task_id": TASK_ID_SHORT,
        "profile_id": PROFILE_ID,
        "run_id": run.RUN_ID,
        "tick_interval": TICK_INTERVAL,
        "subject_sha256": subject_sha,
        "capture_sha256": capture_sha,
        "sheet_layout": {
            "pixel_size": [f01.W, f01.H],
            "honest_titles": ("rendered inside every diagnostic frame: view name, "
                              "mode, frame_id and the 16-field camera record's "
                              "layer list; clean rows intentionally carry no "
                              "labels and no diagnostic styling"),
            "rows": ["V1_clearing_overview clean+diagnostic",
                     "V2_contact_seam clean+diagnostic",
                     "V3_side_depth clean+diagnostic"],
            "supplementary": ["V4_oblique_depth clean+diagnostic+depth (committed, "
                              "sha256-listed under capture_layout.files; not a "
                              "manifest pair -- the profile declares exactly "
                              "three views)"],
            "tick_to_seconds_map": "visible_static: single frozen frame, t=0",
            "files": files,
            "capture_is": ("a z-buffer software raster of the pinned terrain "
                           "asset arrays (the SAME arrays the contact body was "
                           "sliced from) with the settled M06 contact state "
                           "drawn as declared diagnostic layers; probes never "
                           "read pixels -- the correspondence evidence is "
                           "pure ray/geometry (evidence/checks.json P5)"),
            "honest_gaps": [
                "no engine or native upload ran: the render law is F01's "
                "byte-identical CPU rasterizer over the pinned load_mesh arrays",
                "the probe shells and contact markers are diagnostic layers, "
                "not rendered scene assets; clean rows show the pinned asset "
                "unchanged",
                "boundary posts and the prototype trunk are rendered scene "
                "subjects but OUT of this card's contact scope",
            ],
        },
        "views": view_rows,
        "packaging": {"derivation": (
            "per-row unit quaternion derived from the recorded look-at basis; "
            "worst round-trip matrix error %.3e" % worst_q)},
    }
    (EVIDENCE / "capture_manifest.json").write_text(
        json.dumps(manifest, indent=1) + "\n", encoding="utf-8")

    context = {"task_id": TASK_ID_SHORT, "run_id": run.RUN_ID,
               "subject_sha256": subject_sha, "capture_sha256": capture_sha,
               "tick_interval": TICK_INTERVAL}

    profile = registry_profile()
    visual_capture, via = load_validator()
    try:
        receipt = visual_capture.validate_manifest(
            json.loads((EVIDENCE / "capture_manifest.json").read_text(encoding="utf-8")),
            context, profile)
        receipt["fired"] = []
        verdict = "structurally_valid=True"
    except ValueError as err:
        receipt = {"mode": "CAMERA_METADATA_STRUCTURE_ONLY",
                   "structurally_valid": False, "fired": [str(err)]}
        verdict = "FIRED: " + str(err)
    receipt["profile_source"] = REGISTRY + " kanban.cards[MAT2-F02]" \
        ".spec.ontology_qualification.task.verification_profile"
    receipt["validated_profile_id"] = profile["id"]
    receipt["validated_profile_kind"] = profile["kind"]
    receipt["validator_module"] = via + "/visual_capture.py"
    (EVIDENCE / "validation_receipt.json").write_text(
        json.dumps(receipt, indent=1) + "\n", encoding="utf-8")
    print("verdict:", verdict)
    print("run_id:", run.RUN_ID)
    print("capture_sha256:", capture_sha)
    print("subject_sha256:", subject_sha)
    print("trace_sha256:", trace_sha)
    print("manifest:", EVIDENCE / "capture_manifest.json")


if __name__ == "__main__":
    main()
