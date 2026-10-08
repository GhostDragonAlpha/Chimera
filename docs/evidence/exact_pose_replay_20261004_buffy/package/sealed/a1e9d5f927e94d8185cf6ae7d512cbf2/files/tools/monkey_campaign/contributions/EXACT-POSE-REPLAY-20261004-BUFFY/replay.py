"""Exact Stage 1/2 replay preparation; science requires published precommitment.

No placement construction, anatomy/parameter edits, scheduler mutation or cleanup.
The imported instrument and screen are hash-pinned, byte-unmodified dependencies.
"""
import argparse
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
REL = "tools/monkey_campaign/contributions/EXACT-POSE-REPLAY-20261004-BUFFY"
INHERITED = "tools/monkey_campaign/contributions/HAND-REMEDIATION-20261003"
ROOT = HERE.parents[3]
POSTURES = ("q_c_PRIMARY", "q_zero_CONTROL")
COUNTS = {"q_c_PRIMARY": 314, "q_zero_CONTROL": 40}
CONTACT = ("distal_thumb", "distph3")
SCHEMA = "chimera.exact_pose_replay.unit.v1"
TASK = "EXACT-POSE-REPLAY-20261004-BUFFY"
RUNNER_RESULTS = Path("E:/ChimeraWork/task-runner/results")


class Refused(ValueError):
    pass


def require(ok, code):
    if not ok:
        raise Refused(code)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode("utf-8")


def unique(pairs):
    out = {}
    for key, value in pairs:
        require(key not in out, "duplicate_json_key:" + key)
        out[key] = value
    return out


def read_json(path):
    def constant(value):
        raise Refused("nonfinite_json:" + value)
    return json.loads(Path(path).read_bytes(), object_pairs_hook=unique,
                      parse_constant=constant)


def finite(value):
    if isinstance(value, float):
        require(math.isfinite(value), "nonfinite_numeric")
    elif isinstance(value, dict):
        for child in value.values():
            finite(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            finite(child)


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("wb") as stream:
        stream.write(canonical(value))
        stream.flush()
        os.fsync(stream.fileno())
    # Windows filesystem observers may briefly hold the destination without
    # FILE_SHARE_DELETE. Retry only sharing/access failures for a bounded second;
    # any permanent error remains a nonzero job with the .tmp bytes preserved.
    deadline = time.monotonic() + 1.0
    while True:
        try:
            os.replace(tmp, path)
            break
        except PermissionError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.02)


def inputs():
    return read_json(HERE / "INPUTS.json")


def identities():
    return {"task": TASK,
            "preregistration_sha256": sha((HERE / "PREREGISTRATION.md").read_bytes()),
            "inputs_sha256": sha((HERE / "INPUTS.json").read_bytes()),
            "implementation_sha256": sha((HERE / "replay.py").read_bytes())}


def check_files(manifest, root=ROOT, external=True):
    require(manifest["schema"] == "chimera.exact_pose_replay.inputs.v1",
            "input_manifest_schema")
    for name, expected in sorted(manifest["local_files"].items()):
        path = Path(root) / name
        require(path.is_file(), "input_missing:" + name)
        require(sha(path.read_bytes()) == expected, "input_pin_drift:" + name)
    if external:
        for name, expected in sorted(manifest["external_read_only_files"].items()):
            path = Path(name)
            require(path.is_file(), "external_input_missing:" + name)
            require(sha(path.read_bytes()) == expected, "external_input_drift:" + name)


def pose_key(posture, row):
    require(posture in POSTURES, "unknown_posture")
    k, mirror = row.get("theta_index"), row.get("mirror")
    require(type(k) is int and 0 <= k < 720, "theta_index_invalid")
    require(type(mirror) is int and mirror in (0, 1), "mirror_invalid")
    return (posture, k, mirror)


def sort_key(key):
    return (POSTURES.index(key[0]), key[1], key[2])


def join_rows(stage1, stage2, expected=COUNTS):
    require(set(stage1["postures"]) == set(POSTURES), "stage1_posture_census")
    require(set(stage2["postures"]) == set(POSTURES), "stage2_posture_census")
    joined = []
    for posture in POSTURES:
        a_rows = stage1["postures"][posture]["survivors"]
        b_rows = stage2["postures"][posture]["capacity_rows"]
        require(len(a_rows) == expected[posture] and len(b_rows) == expected[posture],
                "pose_count_mismatch:" + posture)
        a, b = {}, {}
        for rows, target in [(a_rows, a), (b_rows, b)]:
            for row in rows:
                finite(row)
                key = pose_key(posture, row)
                require(key not in target, "duplicate_pose_key:" + repr(key))
                target[key] = row
        require(set(a) == set(b), "stage1_stage2_key_mismatch:" + posture)
        for key in sorted(a, key=sort_key):
            original, capacity = a[key], b[key]
            for field in ("pad_body", "pad_class", "pad_u"):
                require(original[field] == capacity[field], "joined_metadata_drift:" + field)
            require(original["pad_body"] in CONTACT, "undeclared_pad_contact_body")
            require(original["pad_class"] in ("PAD_CONTACT", "PAD_ABSORBED"),
                    "unknown_inherited_pad_class")
            for field in ("o", "u"):
                require(isinstance(original[field], list) and len(original[field]) == 3,
                        "pose_vector_shape:" + field)
                require(all(type(x) in (int, float) for x in original[field]),
                        "pose_vector_type:" + field)
            require(type(original["s_star"]) in (int, float), "s_star_invalid")
            joined.append({"key": list(key), "stage1": original, "stage2": capacity,
                           "pose_sha256": sha(canonical({"key": key, "stage1": original,
                                                         "stage2": capacity}))})
    return joined


def load_rows(manifest):
    check_files(manifest)
    source = ROOT / INHERITED
    return join_rows(read_json(source / "raised_cap_stage1_pad_receipt.json"),
                     read_json(source / "stage2_capacity_receipt.json"))


def metadata(rows, manifest):
    return {"schema": "chimera.exact_pose_replay.preflight.v1", **identities(),
            "input_commit": manifest["input_commit"],
            "execution_class": "METADATA_ONLY_NOT_COLLISION_EVIDENCE",
            "counts": {p: sum(r["key"][0] == p for r in rows) for p in POSTURES},
            "keys": [r["key"] for r in rows],
            "pose_hashes": [r["pose_sha256"] for r in rows],
            "body_census": manifest["body_census"],
            "certified_edges": manifest["certified_edges"],
            "constants": manifest["constants"],
            "geometry_executed": False,
            "gates_pending": ["PUBLISHED_PREREG_PIN", "LT_RELEASE",
                              "SERIAL_CONTROL_PARITY", "FULL_354_REPLAY",
                              "INDEPENDENT_REVIEW", "RUNTIME_PLAYABILITY"]}


def release_gate(release_path, operation, manifest, runner_base=None, git_reader=None):
    require(release_path is not None, "published_prereg_and_lt_release_required")
    release = read_json(release_path)
    require(release.get("schema") == "chimera.exact_pose_replay.release.v1",
            "release_schema_invalid")
    for k, v in identities().items():
        require(release.get(k) == v, "release_identity_mismatch:" + k)
    require(release.get("authority") in ("Lieutenant", "Captain"), "release_authority_invalid")
    require(isinstance(release.get("authority_reference"), str)
            and bool(release["authority_reference"].strip()), "release_reference_missing")
    require(operation in release.get("operations", []), "operation_not_released")
    require(release.get("anchor_policy") == "DIAGNOSTIC_ONLY_NO_SOLID_ANATOMY_RULING",
            "anchor_policy_boundary_not_acknowledged")
    require(release.get("owner") == "Buffy-Freebuff-20261004" or
            (isinstance(release.get("owner"), str) and release["owner"].strip()
             and release.get("handoff_reference")), "release_owner_missing")
    require(release.get("ownership_rechecked") is True, "ownership_recheck_required")
    require(release.get("release_id") and release.get("observed_utc"), "release_audit_identity_missing")
    require(release.get("implementation_sha256") == identities()["implementation_sha256"],
            "released_implementation_mismatch")
    require(release.get("sealed_manifest_sha256") == current_seal_sha256(),
            "released_seal_mismatch")
    require(release.get("resource_profile_sha256") == sha(Path(
        "E:/PythonChimera/tools/monkey_campaign/runner_profile.json").read_bytes()),
        "released_resource_profile_mismatch")
    require(release.get("unit_timeout_seconds") == 600, "undeclared_unit_timeout")
    require(release.get("geometry_scope") == "EXACT_STORED_STAGE1_POSES_NO_PLACEMENT_SOLVE",
            "released_geometry_scope_mismatch")
    require(release.get("independent_approval_claimed") is False, "release_self_approval_refused")
    require(operation not in ("replay", "combine") or release.get("control_gate_sha256"),
            "released_control_gate_hash_required")
    require(release.get("source_input_commit") == manifest["input_commit"],
            "release_source_input_mismatch")
    pin = release.get("published_prereg_commit", "")
    require(len(pin) == 40 and all(c in "0123456789abcdef" for c in pin),
            "published_prereg_commit_missing")
    base = runner_base if runner_base is not None else os.environ.get("CHIMERA_BASE_SHA")
    require(base is not None and release.get("sealed_base_commit") == base,
            "released_sealed_base_mismatch")
    require(base != manifest["input_commit"], "new_prereg_pin_not_in_sealed_base")
    if git_reader is None:
        repo = os.environ.get("CHIMERA_SOURCE_REPO")
        require(repo is not None, "approved_runner_context_required")
        def git_reader(*args):
            p = subprocess.run(["git", "-C", repo, *args], capture_output=True, timeout=30)
            require(p.returncode == 0, "publication_pin_git_check_failed")
            return p.stdout
    prereg_bytes = git_reader("show", pin + ":" + REL + "/PREREGISTRATION.md")
    require(prereg_bytes == (HERE / "PREREGISTRATION.md").read_bytes(),
            "published_prereg_bytes_drift")
    git_reader("merge-base", "--is-ancestor", pin, base)
    # This verifies the owner-supplied release and Git pin, not its authorship.
    # Independent authority remains the existing publication/dispatch workflow.
    return release


def current_seal_sha256():
    # The runner owns scratch and writes this job identity before copying files.
    jid_path = ROOT / ".chimera-runner-id"
    require(jid_path.is_file(), "approved_runner_job_identity_required")
    job = jid_path.read_text().strip()
    require(len(job) == 32 and all(c in "0123456789abcdef" for c in job), "runner_job_identity_invalid")
    # The lease is created atomically before process launch; final receipts
    # do not exist yet while a child is running. Never mutate or clean a lease.
    lease = read_json(ROOT.parent / "lease.json")
    require(lease.get("schema") == "chimera.runner_lease.v1" and lease.get("job") == job,
            "runner_lease_identity_mismatch")
    return lease["sealed_manifest_sha256"]


def import_physics():
    sys.path.insert(0, str(ROOT / INHERITED))
    return importlib.import_module("instrument_v2"), importlib.import_module("grasp_screen")


def build_frames(iv, gs, manifest):
    require({k: getattr(iv, k) for k in manifest["constants"]} == manifest["constants"],
            "frozen_constant_drift")
    require([list(x) for x in iv.CERTIFIED_EDGES] == manifest["certified_edges"],
            "exemption_map_drift")
    # Reuse the complete input gate, parser and geometry/FK checks, not a fixture.
    gate = iv.run_input_gate(str(ROOT / INHERITED / "PREREGISTRATION.md"))[0]
    require(gate["ok"], "inherited_input_gate_failed")
    model = gs.build_model()
    zero = {jn: 0.0 for jn in model[1]}
    primary = dict(zero)
    primary.update(iv.Q_C_PRIMARY)
    frames = {}
    qs = {POSTURES[0]: primary, POSTURES[1]: zero}
    for posture in POSTURES:
        prep = gs.prepare_posture(model, qs[posture], CONTACT)
        require(sorted(prep.frames) == manifest["body_census"], "model_body_census_drift")
        frames[posture] = prep.frames
    return frames, qs, gate


def rejection_reasons(records, pi_c):
    reasons = []
    for name, record in sorted(records.items()):
        cls = record["class"]
        require(cls in ("CLEAR", "TOUCHING", "GENUINE_PENETRATION"),
                "unknown_collision_class:" + name)
        finite(record)
        if name in CONTACT:
            if cls == "CLEAR":
                reasons.append("S2_REJECT_NO_CONTACT:" + name)
            elif cls == "GENUINE_PENETRATION":
                if record["depth"] is None or record["depth"] > pi_c:
                    reasons.append("S2_REJECT_DEEP:" + name)
        elif cls == "GENUINE_PENETRATION":
            reasons.append("S1_REJECT_NONCONTACT_PENETRATE:" + name)
        elif cls == "TOUCHING":
            reasons.append("S1_REJECT_NONCONTACT_TOUCH:" + name)
    return reasons


def record_identity_drift(original, records, anchor):
    drifts = []
    seen = set()
    for name, cls, margin, depth in original["bodies"]:
        require(name not in seen, "duplicate_inherited_body")
        seen.add(name)
        require(name in records, "inherited_body_missing")
        actual = records[name]
        if (cls, margin, depth) != (actual["class"], actual.get("d"), actual.get("depth")):
            drifts.append({"body": name, "expected": [cls, margin, depth],
                           "actual": [actual["class"], actual.get("d"), actual.get("depth")]})
    expected = original["anchor_envelope"]
    actual = records[anchor]
    e = [expected["cls"], expected["d"], expected["depth"], expected["flag"]]
    a = [actual["class"], actual.get("d"), actual.get("depth"), actual["level1"]["flag"]]
    if e != a:
        drifts.append({"body": anchor, "expected": e, "actual": a})
    return drifts


def unit_payload(row, records, qs, manifest, frame_table, classify):
    require(sorted(records) == manifest["body_census"], "unit_body_census_mismatch")
    original = row["stage1"]
    states = {name: {"cls": value["class"], "d": value.get("d"),
                     "depth": value.get("depth")} for name, value in records.items()}
    anchor = "macaque_hand_anchor"
    bone_verdict, bone_first = classify({n: s for n, s in states.items() if n != anchor}, CONTACT)
    all_verdict, all_first = classify(states, CONTACT)
    bone_reasons = rejection_reasons({n: r for n, r in records.items() if n != anchor},
                                    manifest["constants"]["PI_C"])
    all_reasons = rejection_reasons(records, manifest["constants"]["PI_C"])
    require((bone_verdict == "REJECT") == bool(bone_reasons), "bone_predicate_inconsistent")
    require((all_verdict == "REJECT") == bool(all_reasons), "all_body_predicate_inconsistent")
    require(bone_first == (bone_reasons[0] if bone_reasons else None), "bone_reason_order_drift")
    require(all_first == (all_reasons[0] if all_reasons else None), "all_reason_order_drift")
    payload = {"schema": SCHEMA, **identities(), "key": row["key"],
            "pose_sha256": row["pose_sha256"], "source_stage1": original,
            "source_stage2": row["stage2"], "posture_q": qs,
            "cylinder": {"o": original["o"], "u": original["u"],
                         "s_star": original["s_star"],
                         "radius_m": manifest["constants"]["TRUNK_R"],
                         "height_m": manifest["constants"]["TRUNK_H"]},
            "body_frames": frame_table,
            "body_records": [{"body": n, "pad_substituted_in_stage1": n == original["pad_body"],
                              "anchor_envelope": n == anchor, "collision": records[n],
                              "depth_bracket_edge": records[n].get("depth") is not None and
                                  records[n]["depth"] >= math.nextafter(
                                      manifest["constants"]["DEPTH_SEARCH_MAX"], -math.inf),
                              "depth_resolution_note": "INHERITED_20MM_BRACKET_NOT_UNBOUNDED_DEPTH_PROOF"}
                             for n in sorted(records)],
            "bone_diagnostic": {"verdict": bone_verdict, "reasons": bone_reasons},
            "anchor_inclusive_diagnostic": {"verdict": all_verdict, "reasons": all_reasons,
                                            "scope": "REPRESENTED_ENVELOPE_NOT_SOLID_ANATOMY_RULING"},
            "inherited_record_drifts": record_identity_drift(original, records, anchor),
            "physical_grasp_qualified": False, "independent_approval": False}
    # Detach nested lists/dicts from source rows and cached frame identities;
    # otherwise an in-memory mutation could alter both evidence and its oracle.
    return json.loads(canonical(payload))


def frame_identities(frames):
    return {name: {"position_m": list(f.pos), "rotation": f.rot,
                   "sphere_center_m": list(f.sphere_center), "sphere_radius_m": f.sphere_r,
                   "is_envelope": f.is_envelope,
                   "represented_mesh_sha256": sha(canonical({"vertices_world_m": f.mesh.verts,
                                                             "triangles": f.mesh.tris})),
                   "vertex_count": len(f.mesh.verts), "triangle_count": len(f.mesh.tris)}
            for name, f in sorted(frames.items())}


def evaluate_unit(row, frames, qs, manifest, iv, gs, serial_reference=False, frame_table=None,
                  checkpoint=None):
    original = row["stage1"]
    records = {}
    # Both routes call only the unmodified primitive. The serial control route
    # is a straight loop; the work-unit route consumes a sorted independent map.
    if serial_reference:
        for name in sorted(frames):
            records[name] = iv.adjudicate_body_vs_cylinder(
                frames[name], tuple(original["o"]), tuple(original["u"]), iv.TAU)
            if checkpoint:
                checkpoint(records)
    else:
        for name, frame in sorted(frames.items()):
            records[name] = iv.adjudicate_body_vs_cylinder(
                frame, tuple(original["o"]), tuple(original["u"]), iv.TAU)
            if checkpoint:
                checkpoint(records)
    frame_table = frame_table if frame_table is not None else frame_identities(frames)
    return unit_payload(row, records, qs, manifest, frame_table, gs.classify_placement_bones)


def unit_name(key):
    return "%s_%03d_%d.json" % tuple(key)


def declared_postures():
    # Metadata only: use literal declared posture constants and pinned joint
    # names, without importing/evaluating FK or constructing collision frames.
    import ast
    source = ROOT / INHERITED
    mutation = read_json(source / "mutation_structure.json")
    joints = [j["name"] for b in [mutation["anchor_body"], *mutation["bodies"]]
              for j in b.get("joints", [])]
    require(len(joints) == 22 and len(set(joints)) == 22, "declared_joint_census_drift")
    primary_literal = None
    for node in ast.parse((source / "instrument_v2.py").read_text()).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "Q_C_PRIMARY"
                                              for t in node.targets):
            primary_literal = ast.literal_eval(node.value)
    require(primary_literal is not None and set(primary_literal) == set(joints),
            "declared_primary_posture_missing")
    return {POSTURES[0]: primary_literal, POSTURES[1]: {j: 0.0 for j in joints}}


def validate_unit(unit, row, manifest, posture_values=None):
    require(unit.get("schema") == SCHEMA, "unit_schema_mismatch")
    for k, v in identities().items():
        require(unit.get(k) == v, "unit_identity_mismatch:" + k)
    require(unit.get("key") == row["key"], "unit_key_mismatch")
    require(unit.get("pose_sha256") == row["pose_sha256"], "unit_pose_hash_mismatch")
    require(canonical(unit.get("source_stage1")) == canonical(row["stage1"]) and
            canonical(unit.get("source_stage2")) == canonical(row["stage2"]),
            "unit_source_pose_drift")
    require([r["body"] for r in unit["body_records"]] == manifest["body_census"],
            "unit_body_census_mismatch")
    require(sorted(unit["body_frames"]) == manifest["body_census"], "unit_frame_census_mismatch")
    require(canonical(unit["cylinder"]) == canonical({"o": row["stage1"]["o"], "u": row["stage1"]["u"],
            "s_star": row["stage1"]["s_star"], "radius_m": manifest["constants"]["TRUNK_R"],
            "height_m": manifest["constants"]["TRUNK_H"]}), "unit_cylinder_pose_drift")
    if posture_values is not None:
        require(canonical(unit["posture_q"]) == canonical(posture_values[row["key"][0]]),
                "unit_posture_drift")
    for record in unit["body_records"]:
        name = record["body"]
        require(record["pad_substituted_in_stage1"] == (name == row["stage1"]["pad_body"]),
                "unit_pad_marker_drift")
        require(record["anchor_envelope"] == (name == "macaque_hand_anchor"), "unit_anchor_marker_drift")
        frame = unit["body_frames"][name]
        require(len(frame["position_m"]) == 3 and len(frame["rotation"]) == 3 and
                all(len(v) == 3 for v in frame["rotation"]), "unit_frame_shape_invalid")
        require(len(frame["represented_mesh_sha256"]) == 64 and
                all(c in "0123456789abcdef" for c in frame["represented_mesh_sha256"]),
                "unit_mesh_identity_invalid")
        require(frame["is_envelope"] == (name == "macaque_hand_anchor"), "unit_frame_envelope_marker_drift")
        require(type(frame["vertex_count"]) is int and frame["vertex_count"] > 0 and
                type(frame["triangle_count"]) is int and frame["triangle_count"] > 0,
                "unit_mesh_census_invalid")
        require(type(record["collision"]["level1"]["flag"]) is bool, "unit_proxy_flag_invalid")
    finite(unit)
    # Do not trust a unit's stored diagnostic labels during combination.
    records = {r["body"]: r["collision"] for r in unit["body_records"]}
    for record in unit["body_records"]:
        depth = record["collision"].get("depth")
        require(record["depth_bracket_edge"] == (depth is not None and depth >= math.nextafter(
                    manifest["constants"]["DEPTH_SEARCH_MAX"], -math.inf)), "unit_depth_bracket_label_drift")
        require(record["depth_resolution_note"] == "INHERITED_20MM_BRACKET_NOT_UNBOUNDED_DEPTH_PROOF",
                "unit_depth_resolution_note_drift")
    for label, rs in [("bone_diagnostic", {n: r for n, r in records.items() if n != "macaque_hand_anchor"}),
                      ("anchor_inclusive_diagnostic", records)]:
        reasons = rejection_reasons(rs, manifest["constants"]["PI_C"])
        require(unit[label]["reasons"] == reasons, "unit_diagnostic_reason_drift")
        require(unit[label]["verdict"] == ("REJECT" if reasons else "SURVIVOR"),
                "unit_diagnostic_verdict_drift")
    require(unit["inherited_record_drifts"] == record_identity_drift(
        row["stage1"], records, "macaque_hand_anchor"), "unit_record_drift_label_mismatch")
    require(unit["physical_grasp_qualified"] is False and unit["independent_approval"] is False,
            "unit_scope_promotion_refused")


def combine_units(units, rows, manifest, posture_values=None):
    wanted = {tuple(r["key"]): r for r in rows}
    require(len(wanted) == len(rows), "duplicate_expected_pose_key")
    actual = {}
    posture_frames = {}
    for unit in units:
        key = tuple(unit["key"])
        require(key in wanted, "foreign_unit_key")
        require(key not in actual, "duplicate_unit_key")
        validate_unit(unit, wanted[key], manifest, posture_values=posture_values)
        frame_digest = sha(canonical(unit["body_frames"]))
        require(key[0] not in posture_frames or posture_frames[key[0]] == frame_digest,
                "same_posture_frame_identity_drift")
        posture_frames[key[0]] = frame_digest
        actual[key] = unit
    require(set(actual) == set(wanted), "partial_result_not_full_replay")
    ordered = [actual[k] for k in sorted(wanted, key=sort_key)]
    return {"schema": "chimera.exact_pose_replay.combined.v1", **identities(),
            "execution_class": "OFFLINE_COLLISION_GEOMETRY_NOT_RUNTIME",
            "input_commit": manifest["input_commit"], "constants": manifest["constants"],
            "certified_edges": manifest["certified_edges"], "body_census": manifest["body_census"],
            "pose_count": len(ordered), "body_record_count": sum(len(u["body_records"]) for u in ordered),
            "counts_by_posture": {p: sum(u["key"][0] == p for u in ordered) for p in POSTURES},
            "bone_diagnostic_rejected": sum(u["bone_diagnostic"]["verdict"] == "REJECT" for u in ordered),
            "anchor_inclusive_rejected": sum(u["anchor_inclusive_diagnostic"]["verdict"] == "REJECT" for u in ordered),
            "inherited_record_drift_count": sum(len(u["inherited_record_drifts"]) for u in ordered),
            "units_sha256": sha(canonical(ordered)), "units": ordered,
            "physical_grasp_qualified": False, "independent_approval": False}


def retained_receipt(path):
    path = Path(path).resolve(strict=True)
    require(path.parent == RUNNER_RESULTS.resolve(strict=True), "noncanonical_runner_result_refused")
    require(not path.is_symlink(), "runner_result_reparse_refused")
    receipt = read_json(path / "receipt.json")
    require(receipt.get("job") == path.name, "runner_result_job_identity_mismatch")
    return path, receipt


def retained_run(path):
    path, receipt = retained_receipt(path)
    require(receipt.get("state") == "PASSED" and receipt.get("cleanup_verified") is True,
            "control_runner_not_completed")
    for name, digest in receipt.get("artifacts", {}).items():
        require(not Path(name).is_absolute() and ":" not in name and ".." not in Path(name).parts,
                "unsafe_runner_artifact_name")
        candidate = path / "runner.log" if name == "runner.log" else path / "artifacts" / name
        require(candidate.is_file() and sha(candidate.read_bytes()) == digest,
                "control_runner_artifact_drift:" + name)
    control_name = "outputs/replay/control.json"
    require(control_name in receipt.get("artifacts", {}), "control_runner_artifact_missing")
    control = read_json(path / "artifacts" / control_name)
    return receipt, control


def retained_units(directories, expected_seal, expected_base):
    units = []
    seen_paths = set()
    for directory in directories:
        d = Path(directory).resolve(strict=True)
        # Exact public interface: RESULT/artifacts/outputs/replay/units.
        require(d.parts[-4:] == ("artifacts", "outputs", "replay", "units"),
                "unit_directory_not_retained_runner_output")
        root, receipt = retained_receipt(d.parents[3])
        require(receipt.get("state") == "PASSED" and receipt.get("cleanup_verified") is True,
                "unit_runner_not_completed")
        require(receipt.get("sealed_manifest_sha256") == expected_seal and
                receipt.get("base") == expected_base, "unit_runner_wrong_candidate")
        for p in sorted(d.glob("*.json")):
            require(p.resolve() not in seen_paths, "duplicate_unit_input_path")
            seen_paths.add(p.resolve())
            rel = p.relative_to(root / "artifacts").as_posix()
            require(sha(p.read_bytes()) == receipt.get("artifacts", {}).get(rel),
                    "unit_runner_artifact_drift:" + rel)
            units.append(read_json(p))
    return units


def control_rows(rows):
    return [r for r in rows if r["key"][0] == "q_zero_CONTROL"][:4]


def control_gate(serial_path, units_path, rows, manifest):
    a, serial = retained_run(serial_path)
    b, units = retained_run(units_path)
    require(a["base"] == os.environ.get("CHIMERA_BASE_SHA"), "control_comparison_wrong_candidate_base")
    require(a["sealed_manifest_sha256"] == current_seal_sha256(), "control_comparison_wrong_candidate_seal")
    require(a["job"] != b["job"], "control_requires_distinct_runner_jobs")
    require(a["base"] == b["base"] and a["sealed_manifest_sha256"] == b["sealed_manifest_sha256"],
            "control_seal_or_base_mismatch")
    require(serial.get("schema") == "chimera.exact_pose_replay.control.v1" and
            units.get("schema") == "chimera.exact_pose_replay.control.v1", "control_schema_invalid")
    require(serial.get("route") == "serial" and units.get("route") == "units_reversed",
            "control_routes_not_distinct")
    for receipt, route in ((a, "serial"), (b, "units_reversed")):
        command = receipt.get("command", [])
        require(len(command) >= 8 and command[1:4] == ["-B", REL + "/replay.py", "control"] and
                command[4:6] == ["--route", route] and "--release" in command[6:],
                "control_runner_command_not_scientific_slice")
    require(serial.get("geometry_executed") is True and units.get("geometry_executed") is True,
            "fixture_not_control_runtime_evidence")
    require(serial.get("run_base_commit") == a["base"] and units.get("run_base_commit") == b["base"],
            "control_declared_base_mismatch")
    expected = control_rows(rows)
    s, u = serial["result"], units["result"]
    for result in (s, u):
        require(result == combine_units(result["units"], expected, manifest,
                                        posture_values=declared_postures()), "control_combination_invalid")
        require(result["inherited_record_drift_count"] == 0, "serial_inherited_record_drift")
    require(canonical(s) == canonical(u), "serial_control_payload_not_byte_identical")
    return {"schema": "chimera.exact_pose_replay.control_gate.v1", **identities(),
            "state": "PASSED", "geometry_executed": True,
            "serial_runner_job": a["job"], "units_runner_job": b["job"],
            "serial_run": str(Path(serial_path).resolve()), "units_run": str(Path(units_path).resolve()),
            "control_payload_sha256": sha(canonical(s)), "control_pose_count": len(expected),
            "base": a["base"], "sealed_manifest_sha256": a["sealed_manifest_sha256"],
            "independent_approval": False}


def check_control_gate(path, rows, manifest):
    require(path is not None, "serial_control_gate_required_before_scaling")
    old = read_json(path)
    new = control_gate(old["serial_run"], old["units_run"], rows, manifest)
    require(old == new, "serial_control_gate_drift")
    require(old["base"] == os.environ.get("CHIMERA_BASE_SHA"), "control_gate_wrong_candidate_base")
    return old


def output_dir():
    base = os.environ.get("CHIMERA_OUTPUT_DIR")
    require(base is not None, "approved_runner_output_context_required")
    out = Path(base) / "replay"
    out.mkdir(parents=True, exist_ok=True)
    return out


def execute(args, out):
    manifest = inputs()
    if args.op == "preflight":
        rows = load_rows(manifest)
        atomic_json(out / "preflight.json", metadata(rows, manifest))
        atomic_json(out / "progress.json", {**identities(), "state": "METADATA_COMPLETED",
                    "geometry_executed": False, "full_result": False})
        return
    # Release check is before any physics import, frame build or collision call.
    release = release_gate(args.release, args.op, manifest)
    rows = load_rows(manifest)
    if args.op in ("replay", "combine"):
        require(args.control_gate is not None, "serial_control_gate_required_before_scaling")
        require(sha(Path(args.control_gate).read_bytes()) == release["control_gate_sha256"],
                "released_control_gate_hash_mismatch")
    if args.op == "compare-control":
        result = control_gate(args.serial_run, args.units_run, rows, manifest)
        atomic_json(out / "control_gate.json", result)
        return
    if args.op == "combine":
        check_control_gate(args.control_gate, rows, manifest)
        units = retained_units(args.unit_dir, release["sealed_manifest_sha256"],
                               release["sealed_base_commit"])
        result = combine_units(units, rows, manifest, posture_values=declared_postures())
        require(result["pose_count"] == 354 and result["body_record_count"] == 7080,
                "full_replay_census_broken")
        require(result["inherited_record_drift_count"] == 0, "full_replay_record_drift_stop")
        atomic_json(out / "result.json", result)
        return
    if args.op == "replay":
        check_control_gate(args.control_gate, rows, manifest)
        if args.keys:
            selected = read_json(args.keys)
            require(isinstance(selected, list) and bool(selected), "unit_selection_empty")
            keys = [tuple(x) for x in selected]
            require(len(keys) == len(set(keys)), "unit_selection_duplicate")
            all_rows = {tuple(r["key"]): r for r in rows}
            require(all(k in all_rows for k in keys), "unit_selection_foreign_key")
            rows = [all_rows[k] for k in sorted(keys, key=sort_key)]
    else:
        rows = control_rows(rows)
    iv, gs = import_physics()
    frames, qs, input_gate = build_frames(iv, gs, manifest)
    frame_tables = {p: frame_identities(frames[p]) for p in POSTURES}
    atomic_json(out / "inherited_input_gate.json", input_gate)
    completed = []
    work = list(reversed(rows)) if args.op == "control" and args.route == "units_reversed" else rows
    for row in work:
        p = row["key"][0]
        def checkpoint(records):
            atomic_json(out / "partial_bodies" / unit_name(row["key"]), {
                **identities(), "state": "PARTIAL_BODY_RECORDS_NOT_COMPLETE_POSE",
                "key": row["key"], "pose_sha256": row["pose_sha256"],
                "completed_body_records": records, "full_result": False})
        result = evaluate_unit(row, frames[p], qs[p], manifest, iv, gs,
                               serial_reference=args.op == "control" and args.route == "serial",
                               frame_table=frame_tables[p], checkpoint=checkpoint)
        atomic_json(out / "units" / unit_name(row["key"]), result)
        completed.append(row["key"])
        atomic_json(out / "progress.json", {**identities(), "state": "PARTIAL",
                    "completed_keys": sorted(completed, key=sort_key), "requested_pose_count": len(rows),
                    "geometry_executed": True, "full_result": False})
        print("completed " + repr(row["key"]), flush=True)
        require(not result["inherited_record_drifts"], "inherited_record_drift_stop")
    if args.op == "control":
        combined = combine_units([read_json(out / "units" / unit_name(r["key"])) for r in rows], rows, manifest,
                                 posture_values=qs)
        atomic_json(out / "control.json", {"schema": "chimera.exact_pose_replay.control.v1",
                    "route": args.route, "geometry_executed": True,
                    "run_base_commit": os.environ["CHIMERA_BASE_SHA"], "result": combined})
    atomic_json(out / "progress.json", {**identities(), "state": "UNITS_COMPLETED",
                "completed_keys": sorted(completed, key=sort_key), "geometry_executed": True,
                "full_result": False, "next_gate": "CONTROL_COMPARISON_OR_CANONICAL_COMBINATION"})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="op", required=True)
    sub.add_parser("preflight", help="metadata/pins/key join only; never calls collision geometry")
    for op in ("control", "replay", "compare-control", "combine"):
        p = sub.add_parser(op)
        p.add_argument("--release")
        if op == "control":
            p.add_argument("--route", choices=("serial", "units_reversed"), required=True)
        elif op == "compare-control":
            p.add_argument("--serial-run", required=True)
            p.add_argument("--units-run", required=True)
        else:
            p.add_argument("--control-gate")
            if op == "replay":
                p.add_argument("--keys", help="JSON list of independent pose keys; omitted means all 354")
            else:
                p.add_argument("--unit-dir", action="append", required=True)
    args = parser.parse_args()
    out = output_dir()
    atomic_json(out / "progress.json", {**identities(), "state": "STARTED",
                                       "geometry_executed": False, "full_result": False})
    try:
        execute(args, out)
    except BaseException as exc:
        # The inherited instrument's GateRefusal derives from SystemExit, not
        # Exception. Preserve that exact refusal and any partial body records,
        # then re-raise: this never turns an error/interrupt into a passing job.
        atomic_json(out / "error.json", {**identities(), "state": "REFUSED_OR_FAILED",
                    "exception": type(exc).__name__, "reason": str(exc),
                    "instrument_code": getattr(exc, "code", None),
                    "instrument_detail": getattr(exc, "detail", None), "full_result": False})
        raise


if __name__ == "__main__":
    main()
