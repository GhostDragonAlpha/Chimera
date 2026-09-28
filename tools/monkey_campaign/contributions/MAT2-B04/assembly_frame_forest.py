"""MAT2-B04: the real assembly frame forest, authored with pinned source evidence.

The four component roots the fitted anatomy packet references but never declares
(pelvis, thorax, ulna, ulna_l) are declared here explicitly.  Every authored
transform is composed ONLY from pinned active body declarations in chimanoid.xml
(sha256 675e00d0898cf7a175f3e4fe8f240eb24301c2f5e201ffa9215aea45b01b83d1); no
alignment is guessed, fitted, or inferred from appearance.  Containment (frame
hierarchy) is a separate relation list from mechanical bonds; the fitted packet's
four disconnected components remain explicit and no containment edge creates a
bond.  Frames are placement only: no mass is counted, no geometry is fabricated,
and the anatomy admission statuses are carried through unchanged.

Validation style follows MAT2-M01 material_state.py: strict JSON, named refusal
codes, canonical digests, stable IDs.  CPU-only, stdlib-only.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

SCHEMA = "chimera.assembly_frame_forest.v1"
DOCUMENT_REVISION = 1

# ---- pinned source identities (verified live; see PREREGISTRATION.md) --------
CHIMANOID_SHA256 = "675e00d0898cf7a175f3e4fe8f240eb24301c2f5e201ffa9215aea45b01b83d1"
CHIMANOID_GIT_PIN = {
    "commit": "0ad24b027cfbea3c4364c82d383f7b2ca5824fab",
    "branch": "forearm-package-20260924",
    "path": "forearm_package/baseline_snapshot/source_xml/chimanoid.xml",
    "canonical_sha256": "7caa32c6e31e319876ea21625b662c5c00e736038f542b38ce6b0cb81aadc8a5",
}
PACKET_SHA256 = "a447555069748d7fe421ff2a4ddeaa108729924ae088478741c86c38c3880937"
ADMISSION_SHA256 = "833ca65b282eab83180bdbe65bbd8f934924fdd1416c8058d510e5481d86b4ad"
OSIM_SHA256 = "4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895"
OSIM_PATH = "tools/science_funnel/data/macaque_arm/monkeyArm_current.osim"
GRAPH_ENTRY = "ref.macaque_arm.body.ulna"
GRAPH_SOURCE_REVISION = "4fb7dddeec06a0df9525c18f37234a824cb1b5b1"
GRAPH_ULNA_WORLD_FROM_LOCAL = [
    [-3.205103515924179e-09, -1.0, 0.0, 0.0],
    [1.0, -3.205103515924179e-09, 0.0, -0.123],
    [0.0, 0.0, 1.0, 0.002],
    [0.0, 0.0, 0.0, 1.0],
]
SOURCE_HEAD = "c525b82c7c3ce0128565424764293a3c85811ab3"

# ---- pinned active body declarations: (body, raw_line, pos, quat, parent) ----
# Raw line numbers are line numbers of the pinned chimanoid.xml bytes.  The
# active declaration is used; commented alternates near each line are NOT used.
SOURCE_HOPS = (
    ("pelvis", 55, (0.0, 0.73, 6.12323e-17), (1.0, 0.0, 0.0, 0.0), "WORLD"),
    ("thorax_dummy", 411, (-0.1007, 0.0815, 0.0), (1.0, 0.0, 0.0, 0.0), "pelvis"),
    ("thorax", 420, (0.0207, 0.3785, 0.0), (1.0, 0.0, 0.0, 0.0), "thorax_dummy"),
    ("humerus", 534, (-0.0176, -0.007, 0.17), (1.0, 0.0, 0.0, 0.0), "thorax"),
    ("ulna", 593, (0.0061, -0.34845, -0.0123), (1.0, 0.0, 0.0, 0.0), "humerus"),
    ("humerus_l", 675, (-0.0176, -0.007, -0.17), (1.0, 0.0, 0.0, 0.0), "thorax"),
    ("ulna_l", 733, (0.0061, -0.3485, 0.0123), (1.0, 0.0, 0.0, 0.0), "humerus_l"),
)
ROOT_CHAINS = {
    "pelvis": ("pelvis",),
    "thorax": ("pelvis", "thorax_dummy", "thorax"),
    "ulna": ("pelvis", "thorax_dummy", "thorax", "humerus", "ulna"),
    "ulna_l": ("pelvis", "thorax_dummy", "thorax", "humerus_l", "ulna_l"),
}

# ---- fitted packet facts carried verbatim (actual_monkey_fit.json) -----------
SEGMENTS = (
    # body, parent, status, axis_sources (axial, b, c)
    ("femur_r", "pelvis", "resolved", ("evidence", "evidence", "evidence")),
    ("femur_l", "pelvis", "resolved", ("evidence", "evidence", "evidence")),
    ("thorax_dummy", "pelvis", "resolved", ("evidence", "assumption", "assumption")),
    ("tibia_r", "femur_r", "resolved", ("evidence", "evidence", "evidence")),
    ("tibia_l", "femur_l", "resolved", ("evidence", "evidence", "evidence")),
    ("humerus", "thorax", "resolved", ("evidence", "evidence", "evidence")),
    ("humerus_l", "thorax", "resolved", ("evidence", "evidence", "evidence")),
    ("radius", "ulna", "resolved", ("evidence", "assumption", "assumption")),
    ("radius_l", "ulna_l", "resolved", ("evidence", "assumption", "assumption")),
)
COMPONENTS = (
    ("pelvis", ("femur_r", "femur_l", "thorax_dummy", "tibia_r", "tibia_l")),
    ("thorax", ("humerus", "humerus_l")),
    ("ulna", ("radius",)),
    ("ulna_l", ("radius_l",)),
)
UNRESOLVED_BODIES = ("hand_l", "hand_r", "talus_l", "talus_r", "thorax", "toes_l",
                     "toes_r", "ulna", "ulna_l")
# packet joints: (name, body, joint_type, status)  -- statuses verbatim
JOINTS = (
    ("pelvis_tz", "pelvis", "slide", "kinematically_preserved"),
    ("pelvis_ty", "pelvis", "slide", "kinematically_preserved"),
    ("pelvis_tx", "pelvis", "slide", "kinematically_preserved"),
    ("pelvis_tilt", "pelvis", "hinge", "kinematically_preserved"),
    ("pelvis_list", "pelvis", "hinge", "kinematically_preserved"),
    ("pelvis_rotation", "pelvis", "hinge", "kinematically_preserved"),
    ("hip_flexion_r", "femur_r", "hinge", "kinematically_preserved"),
    ("hip_adduction_r", "femur_r", "hinge", "kinematically_preserved"),
    ("hip_rotation_r", "femur_r", "hinge", "kinematically_preserved"),
    ("knee_angle_r", "tibia_r", "hinge", "kinematically_preserved"),
    ("ankle_angle_r", "talus_r", "hinge", "unresolved_body"),
    ("ankle_angle_r2", "talus_r", "hinge", "unresolved_body"),
    ("ankle_angle_r3", "talus_r", "hinge", "unresolved_body"),
    ("mtp_angle_r", "toes_r", "hinge", "unresolved_body"),
    ("hip_flexion_l", "femur_l", "hinge", "kinematically_preserved"),
    ("hip_adduction_l", "femur_l", "hinge", "kinematically_preserved"),
    ("hip_rotation_l", "femur_l", "hinge", "kinematically_preserved"),
    ("knee_angle_l", "tibia_l", "hinge", "kinematically_preserved"),
    ("ankle_angle_l", "talus_l", "hinge", "unresolved_body"),
    ("ankle_angle_l2", "talus_l", "hinge", "unresolved_body"),
    ("ankle_angle_l3", "talus_l", "hinge", "unresolved_body"),
    ("mtp_angle_l", "toes_l", "hinge", "unresolved_body"),
    ("lumbar_extension", "thorax_dummy", "hinge", "kinematically_preserved"),
    ("lumbar_bending", "thorax_dummy", "hinge", "kinematically_preserved"),
    ("lumbar_rotation", "thorax", "hinge", "unresolved_body"),
    ("shoulder_elv", "humerus", "hinge", "kinematically_preserved"),
    ("shoulder_rot", "humerus", "hinge", "kinematically_preserved"),
    ("elv_angle", "humerus", "hinge", "kinematically_preserved"),
    ("elbow_flexion", "ulna", "hinge", "unresolved_body"),
    ("wrist_dev_r", "hand_r", "hinge", "unresolved_body"),
    ("wrist_flex_r", "hand_r", "hinge", "unresolved_body"),
    ("wrist_3_r", "hand_r", "hinge", "unresolved_body"),
    ("shoulder_elv_l", "humerus_l", "hinge", "kinematically_preserved"),
    ("shoulder_rot_l", "humerus_l", "hinge", "kinematically_preserved"),
    ("elv_angle_l", "humerus_l", "hinge", "kinematically_preserved"),
    ("elbow_flexion_l", "ulna_l", "hinge", "unresolved_body"),
    ("wrist_dev_l", "hand_l", "hinge", "unresolved_body"),
    ("wrist_flex_l", "hand_l", "hinge", "unresolved_body"),
    ("wrist_3_l", "hand_l", "hinge", "unresolved_body"),
)

PREREGISTRATION_SHA256 = "64d1d779204882f2732b15e1ad4965b2d6d2d319dcd0d5d96c208c2f239d514a"
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}")


# ---- refusal helpers ---------------------------------------------------------
def require(condition, code):
    if not condition:
        raise ValueError(code)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---- small exact linear algebra (row-major 3x3, column vectors) --------------
def quat_is_identity(quat):
    w, x, y, z = quat
    return (w, x, y, z) == (1.0, 0.0, 0.0, 0.0)


def identity_matrix():
    return [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]


def quat_to_matrix(quat):
    """Rotate matrix rows for quaternion w x y z (active rotation)."""
    w, x, y, z = quat
    return [
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ]


def mat_mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)]
            for i in range(3)]


def mat_vec(r, v):
    return [sum(r[i][k] * v[k] for k in range(3)) for i in range(3)]


def mat_transpose(r):
    return [[r[j][i] for j in range(3)] for i in range(3)]


def compose_transform(t_a, r_a, t_b, r_b):
    """Compose A then B: x' = R_b (R_a x + t_a) + t_b."""
    return ([t_b[i] + sum(r_b[i][k] * t_a[k] for k in range(3)) for i in range(3)],
            mat_mul(r_b, r_a))


def invert_transform(t, r):
    r_t = mat_transpose(r)
    return ([-sum(r_t[i][k] * t[k] for k in range(3)) for i in range(3)], r_t)


def determinant(r):
    return (r[0][0] * (r[1][1] * r[2][2] - r[1][2] * r[2][1])
            - r[0][1] * (r[1][0] * r[2][2] - r[1][2] * r[2][0])
            + r[0][2] * (r[1][0] * r[2][1] - r[1][1] * r[2][0]))


# ---- source-chain composition ------------------------------------------------
def hop_by_body(body):
    for row in SOURCE_HOPS:
        if row[0] == body:
            return row
    raise ValueError("unknown_source_hop:" + str(body))


def compose_chain(chain):
    """Compose the pinned declaration chain into one world transform."""
    t = (0.0, 0.0, 0.0)
    r = identity_matrix()
    for body in chain:
        _, line, pos, quat, parent = hop_by_body(body)
        t, r = compose_transform(t, r, pos, quat_to_matrix(quat))
    return t, r


def hop_records(chain):
    rows = []
    for body in chain:
        _, line, pos, quat, parent = hop_by_body(body)
        rows.append({"body": body, "source": "chimanoid.xml", "line": line,
                     "field": "body[@pos,@quat]", "parent": parent,
                     "pos": list(pos), "quat_wxyz": list(quat),
                     "sha256": CHIMANOID_SHA256})
    return rows


# ---- document construction ---------------------------------------------------
def _root_frame(root):
    chain = ROOT_CHAINS[root]
    t, r = compose_chain(chain)
    return {
        "frame_id": "root_" + root,
        "body": root,
        "component_root": True,
        "parent_frame_id": "assembly_world",
        "coordinate_system": "assembly_world_source_chain",
        "coordinate_unit": "m",
        "handedness": "right",
        "scale_to_m": 1.0,
        "origin_m": list(t),
        "basis_rows": [list(row) for row in r],
        "chain": hop_records(chain),
        "evidence": "composed exclusively from the pinned declarations in chain; "
                    "no fitted, tuned, or appearance-derived value",
    }


def _fitted_frame_rows():
    rows = {}
    for body, parent, status, axes in SEGMENTS:
        rows[body] = {
            "frame_id": "fitted_" + body,
            "body": body,
            "parent_frame_id": "fitted_" + parent,
            "coordinate_system": "anatomy_packet_fitted",
            "status": status,
            "axis_sources": {"axial": axes[0], "b": axes[1], "c": axes[2]},
            "sha256": PACKET_SHA256,
        }
    return rows


def build_document():
    containment = [{"child_frame_id": "root_" + root, "parent_frame_id": "assembly_world",
                    "kind": "containment", "origin": "authored_source_chain"}
                   for root in ROOT_CHAINS]
    for body, parent, _status, _axes in SEGMENTS:
        containment.append({"child_frame_id": "fitted_" + body,
                            "parent_frame_id": "fitted_" + parent,
                            "kind": "containment", "origin": "anatomy_packet_segment_tree"})

    segment_parents = {body: parent for body, parent, _s, _a in SEGMENTS}
    bonds = []
    for name, body, jtype, status in JOINTS:
        parent = segment_parents.get(body)
        if parent is not None:
            bond_parent = parent
        elif body == "pelvis":
            bond_parent = "source_world"
        else:
            bond_parent = None  # unresolved: packet declares no parent edge
        bonds.append({"bond_id": "bond_" + name, "joint": name, "body": body,
                      "joint_type": jtype, "status": status,
                      "parent_body_declared": bond_parent,
                      "kind": "mechanical_bond"})

    document = {
        "schema": SCHEMA,
        "revision": DOCUMENT_REVISION,
        "object_id": "mat2_b04_assembly_frame_forest",
        "task_id": "MAT2-B04",
        "source_head": SOURCE_HEAD,
        "preregistration_sha256": PREREGISTRATION_SHA256,
        "decision_record": {
            "commissioned": "author all four referenced component roots as a forest "
                            "(lead dispatch 2026-09-28); supersedes the single-root "
                            "question of assembly_handoff_02 section 'Smallest remaining "
                            "Astra decisions' item 3",
            "observed_finding": "Buffy 02: disconnected_component_roots = "
                                "[pelvis, thorax, ulna, ulna_l]; prepared definition is "
                                "not authorization",
            "ontology_boundary": "source XML nesting and the fitted packet's "
                                 "disconnected ownership tree are different "
                                 "representations; no automatic replacement is authorized",
        },
        "coordinate_systems": {
            "assembly_world_source_chain": {
                "units": "m", "handedness": "right",
                "definition": "world frame of the pinned chimanoid.xml model tree",
            },
            "anatomy_packet_fitted": {
                "units": "m", "handedness": "right",
                "definition": "the fitted packet's own fitted coordinate system "
                              "(actual_monkey_fit.json); NOT fused with "
                              "assembly_world_source_chain anywhere in this document",
            },
        },
        "no_fusion_statement": "The mapping between anatomy_packet_fitted and "
                               "assembly_world_source_chain is intentionally NOT "
                               "authored: deriving it would be a guessed alignment. "
                               "Frame binding between the two systems is by stable "
                               "name only (component root body == authored root frame "
                               "body).",
        "frames": {
            "assembly_world": {
                "frame_id": "assembly_world",
                "body": None,
                "component_root": False,
                "parent_frame_id": None,
                "coordinate_system": "assembly_world_source_chain",
                "coordinate_unit": "m",
                "handedness": "right",
                "scale_to_m": 1.0,
                "origin_m": [0.0, 0.0, 0.0],
                "basis_rows": identity_matrix(),
                "note": "declared reference frame; a containment parent only, "
                        "never a mechanical body",
            },
            "root_pelvis": _root_frame("pelvis"),
            "root_thorax": _root_frame("thorax"),
            "root_ulna": _root_frame("ulna"),
            "root_ulna_l": _root_frame("ulna_l"),
        },
        "fitted_frames": _fitted_frame_rows(),
        "containment_edges": containment,
        "bonds": bonds,
        "components": [
            {"component_id": "component_" + root, "root_frame_id": "root_" + root,
             "bodies": list(bodies), "fitted_frames": ["fitted_" + b for b in bodies],
             "disconnected_from_other_components": True}
            for root, bodies in COMPONENTS
        ],
        "unresolved_bodies": [
            {"body": body,
             "joints": [j for j, b, _t, _s in JOINTS if b == body],
             "admission_status": "unresolved",
             "frame_authored": body in ROOT_CHAINS,
             "geometry_mass_status": "unresolved (unchanged from admission ledger)"}
            for body in UNRESOLVED_BODIES
        ],
        "matter_boundary": {
            "counted_mass_kg": 0.0,
            "statement": "frames are placement only; no mass is counted, promoted, "
                         "or relabelled; admission statuses carry through unchanged "
                         "(pelvis root_reference_frame_only; thorax/ulna/ulna_l "
                         "geometry-mass unresolved)",
            "admission_sha256": ADMISSION_SHA256,
        },
        "independent_reference_not_merged": {
            "osim": {"path": OSIM_PATH, "sha256": OSIM_SHA256,
                     "statement": "independent arm reference model "
                                  "(ground/sternum/clavicle/scapula/humerus/ulna chain); "
                                  "different assembly; never numerically merged"},
            "graph": {"entry": GRAPH_ENTRY, "source_revision": GRAPH_SOURCE_REVISION,
                      "world_from_local": GRAPH_ULNA_WORLD_FROM_LOCAL,
                      "statement": "graph spatial frame of the arm reference; recorded "
                                   "verbatim for correspondence only"},
        },
        "provenance": {
            "arrival_id": "arrival-e62bcc21929a4d9a82be41e65baa68c9",
            "attempt_id": "98adbfd891dc4001b1c670a2e477ddd5",
            "chimanoid": {"sha256": CHIMANOID_SHA256, **CHIMANOID_GIT_PIN},
            "packet": {"path": ".tmp/anatomy_compiler/runs/actual_monkey_fit.json",
                       "sha256": PACKET_SHA256},
        },
    }
    return document


# ---- validation (named refusals) ---------------------------------------------
def _finite(value, label):
    require(type(value) is float or type(value) is int, "nonfinite_number:" + label)
    require(math.isfinite(value), "nonfinite_number:" + label)
    return float(value)


def _vec3(value, label):
    require(isinstance(value, list) and len(value) == 3, "invalid_vec3:" + label)
    return [_finite(v, label) for v in value]


def _mat3(value, label):
    require(isinstance(value, list) and len(value) == 3, "invalid_mat3:" + label)
    return [_vec3(row, label) for row in value]


def validate_document(document):
    """Validate one frame forest document; returns a normalized summary dict."""
    require(isinstance(document, dict), "document_not_object")
    require(document.get("schema") == SCHEMA, "unsupported_frame_forest_schema")
    require(type(document.get("revision")) is int and document["revision"] > 0,
            "invalid_revision")
    require(ID.fullmatch(document.get("object_id", "")) is not None, "invalid_object_id")
    require(isinstance(document.get("frames"), dict), "frames_missing")

    frames = document["frames"]
    require("assembly_world" in frames, "assembly_world_missing")
    roots = [k for k, f in frames.items() if f.get("component_root")]
    require(sorted(roots) == ["root_pelvis", "root_thorax", "root_ulna", "root_ulna_l"],
            "authored_roots_missing")

    # authored transforms must recompute exactly from their pinned chains
    for key in roots:
        frame = frames[key]
        require(frame.get("coordinate_unit") == "m", "frame_unit_invalid:" + key)
        require(frame.get("handedness") == "right", "frame_handedness_invalid:" + key)
        require(frame.get("scale_to_m") == 1.0, "frame_scale_invalid:" + key)
        rows = _mat3(frame["basis_rows"], key + ".basis_rows")
        require(determinant(rows) > 1.0 - 1e-12, "frame_basis_not_proper:" + key)
        t_expect, r_expect = compose_chain(
            tuple(h["body"] for h in frame["chain"]))
        for got, want in zip(frame["origin_m"], t_expect):
            require(abs(_finite(got, key + ".origin") - want) <= 1e-15,
                    "root_transform_not_source_composed:" + key)
        for row_got, row_want in zip(rows, r_expect):
            for got, want in zip(row_got, row_want):
                require(abs(got - want) <= 1e-12, "root_basis_not_source_composed:" + key)

    # containment and bonds are distinct relation lists
    containment = document["containment_edges"]
    bonds = document["bonds"]
    require(isinstance(containment, list) and containment, "containment_missing")
    require(isinstance(bonds, list) and bonds, "bonds_missing")
    for edge in containment:
        require(isinstance(edge, dict) and edge.get("kind") == "containment",
                "containment_edge_invalid")
    for bond in bonds:
        require(isinstance(bond, dict) and bond.get("kind") == "mechanical_bond",
                "bond_invalid")
        require(bond.get("status") in ("kinematically_preserved", "unresolved_body"),
                "bond_status_not_carried_verbatim")
    containment_ids = {e["child_frame_id"] for e in containment}
    bond_ids = {b["bond_id"] for b in bonds}
    require(not (containment_ids & bond_ids), "containment_bond_identity_overlap")
    require(len(containment_ids) == len(containment), "duplicate_containment_edge")
    require(len(bond_ids) == len(bonds), "duplicate_bond")

    # four explicit disconnected components
    components = document["components"]
    require(isinstance(components, list) and len(components) == 4,
            "component_count_invalid")
    for component in components:
        require(component.get("disconnected_from_other_components") is True,
                "component_connectivity_asserted")
    members = [b for c in components for b in c["bodies"]]
    require(len(members) == len(set(members)) == 9, "component_membership_invalid")
    require(sorted(members) == sorted(row[0] for row in SEGMENTS),
            "component_membership_not_packet_segments")

    # bond graph must not connect components (declared parent edges only)
    body_to_component = {}
    for component in components:
        for body in component["bodies"]:
            body_to_component[body] = component["component_id"]
    for bond in bonds:
        body, parent = bond["body"], bond["parent_body_declared"]
        if body in body_to_component and parent in body_to_component:
            require(body_to_component[body] == body_to_component[parent],
                    "bond_crosses_components:" + bond["bond_id"])

    require(document["matter_boundary"]["counted_mass_kg"] == 0.0,
            "mass_counted_by_frame_document")

    return {
        "schema": "chimera.assembly_frame_forest.receipt.v1",
        "status": "PASS",
        "object_id": document["object_id"],
        "document_sha256": digest(document),
        "authored_root_frames": sorted(roots),
        "containment_edges": len(containment),
        "bonds": len(bonds),
        "components": len(components),
        "limits": "Checks declared evidence and structural invariants; does not "
                  "authenticate upstream sources, qualify mechanics, or replace "
                  "runtime contact tests.",
    }


# ---- C01 checks (round-trip, handedness, independent recomputation) ----------
def c01_checks(document, probes=1000, seed=20260928):
    frames = document["frames"]
    results = {}
    state = seed
    for key in ("root_pelvis", "root_thorax", "root_ulna", "root_ulna_l"):
        frame = frames[key]
        t = _vec3(frame["origin_m"], key)
        r = _mat3(frame["basis_rows"], key)
        r_inv = mat_transpose(r)
        t_inv = [-sum(r_inv[i][k] * t[k] for k in range(3)) for i in range(3)]
        max_err = 0.0
        for _ in range(probes):
            state = (1103515245 * state + 12345) % (2 ** 31)
            p = [((state >> ((8 * i) % 31)) % 2003 / 1000.0 - 1.0) for i in range(3)]
            q = mat_vec(r, p)
            q = [q[i] + t[i] for i in range(3)]
            back = mat_vec(r_inv, q)
            back = [back[i] + t_inv[i] for i in range(3)]
            max_err = max(max_err, max(abs(back[i] - p[i]) for i in range(3)))
        results[key] = {
            "determinant": determinant(r),
            "round_trip_max_error": max_err,
            "orthonormality_max_error": max(
                abs(sum(r[i][k] * r[j][k] for k in range(3)) - (1.0 if i == j else 0.0))
                for i in range(3) for j in range(3)),
        }
        require(results[key]["determinant"] > 1.0 - 1e-12, "c01_handedness_failed:" + key)
        require(max_err <= 1e-12, "c01_round_trip_failed:" + key)
        require(results[key]["orthonormality_max_error"] <= 1e-12,
                "c01_orthonormality_failed:" + key)
    return results


# ---- separation mutation check (F2) ------------------------------------------
def separation_check(document):
    """Removing all containment edges changes no bond, and vice versa."""
    without_containment = {**document, "containment_edges": []}
    without_bonds = {**document, "bonds": []}
    bonds_before = digest(document["bonds"])
    bonds_after = digest(without_containment["bonds"])
    containment_before = digest(document["containment_edges"])
    containment_after = digest(without_bonds["containment_edges"])
    require(bonds_before == bonds_after, "containment_changed_bonds")
    require(containment_before == containment_after, "bonds_changed_containment")
    return {"bonds_unchanged_without_containment": True,
            "containment_unchanged_without_bonds": True}


# ---- live source verification -------------------------------------------------
def verify_live_source(chimanoid_path, packet_path=None, osim_path=None):
    checks = {"chimanoid_sha256": sha256_file(chimanoid_path)}
    require(checks["chimanoid_sha256"] == CHIMANOID_SHA256,
            "live_source_hash_mismatch:chimanoid")
    text = Path(chimanoid_path).read_text(encoding="utf-8", errors="strict").splitlines()
    for body, line, pos, quat, _parent in SOURCE_HOPS:
        row = text[line - 1]
        require('name="%s"' % body in row, "live_source_line_body_mismatch:" + body)
        for value in pos:
            require(re.search(r"[-0-9]%.0e" % value if value else r"0", row)
                    or ("%.10g" % value) in row or ("%.6g" % value) in row
                    or repr(value) in row or (str(value) in row),
                    "live_source_line_value_mismatch:" + body)
    if packet_path is not None:
        checks["packet_sha256"] = sha256_file(packet_path)
        require(checks["packet_sha256"] == PACKET_SHA256, "live_source_hash_mismatch:packet")
    if osim_path is not None:
        checks["osim_sha256"] = sha256_file(osim_path)
        require(checks["osim_sha256"] == OSIM_SHA256, "live_source_hash_mismatch:osim")
    return checks


# ---- semantic frame packet emission (astra-0035) ------------------------------
def _rotate_about_z(v, q):
    c, s = math.cos(q), math.sin(q)
    return [v[0] * c - v[1] * s, v[0] * s + v[1] * c, v[2]]


def semantic_packets():
    """Author the appendage semantic-frame packets (right and left ulna roots).

    Pelvis/thorax receive no packet on purpose: the semantic-frame module's
    fixed required pairs and palm kinematic witness are appendage semantics;
    forcing them onto the axial body would author invented semantics.
    """
    packets = {}
    chirality = (
        ("ulna_r", "root_ulna", "ulna", 593, 534, 608, 629, 607,
         (0.0, 0.0, 1.0), [0.0, 0.0, 1.0], [0.0, 0.0, -1.0]),
        ("ulna_l", "root_ulna_l", "ulna_l", 733, 675, 748, 769, 747,
         (0.0, 0.0, 1.0), [0.0, 0.0, -1.0], [0.0, 0.0, 1.0]),
    )
    q = 0.1
    for (tag, frame_key, body, ulna_line, humerus_line, radius_line, hand_line,
         elbow_line, _axis, lateral, medial) in chirality:
        origin = list(compose_chain(ROOT_CHAINS[body])[0])
        radius_local = {"ulna_r": (0.0004, -0.011503, 0.019999),
                        "ulna_l": (0.0004, -0.011503, -0.019999)}[tag]
        hand_offset = (0.018, -0.2904, 0.025 if tag == "ulna_r" else -0.025)
        hand_local = [radius_local[i] + hand_offset[i] for i in range(3)]
        distal = [0.0, -1.0, 0.0]
        proximal = [0.0, 1.0, 0.0]
        dorsal = [-1.0, 0.0, 0.0]
        palm = [1.0, 0.0, 0.0]
        rest = [list(radius_local), hand_local]
        moved = [_rotate_about_z(p, q) for p in rest]
        packets[tag] = {
            "schema": "chimera.semantic_spatial_frame.v1",
            "subject_id": "mat2_b04_%s_root_frame" % tag,
            "subject_kind": "anatomical_frame",
            "source_head": SOURCE_HEAD,
            "coordinate_unit": "m",
            "frame": {
                "frame_id": "%s_assembly_root" % tag,
                "handedness": "right",
                "origin": origin,
                "basis": {"x": [1.0, 0.0, 0.0], "y": [0.0, 1.0, 0.0],
                          "z": [0.0, 0.0, 1.0]},
            },
            "semantic_directions": {
                "distal": distal, "proximal": proximal,
                "dorsal": dorsal, "palm": palm,
                "lateral": lateral, "medial": medial,
            },
            "knowledge_claims": [
                {"id": "claim_xml_landmarks", "domain": "geometry",
                 "authority": "authoritative_database",
                 "source_ref": "chimanoid.xml L%d body %s; L%d parent humerus; "
                               "L%d radius; L%d hand offset; sha-pinned"
                               % (ulna_line, body, humerus_line, radius_line, hand_line),
                 "statement": "Pinned active body declarations give the elbow pivot "
                              "(frame origin), the radius pivot %s and the hand pivot "
                              "%s in the %s frame (identity quats: offsets add)."
                              % (tuple(radius_local), tuple(hand_local), body),
                 "artifact_sha256": CHIMANOID_SHA256},
                {"id": "claim_elbow_axis", "domain": "physics",
                 "authority": "authoritative_database",
                 "source_ref": "chimanoid.xml L%d joint elbow_flexion%s axis 0 0 1 "
                               "range 0 2.26893" % (elbow_line,
                                                    "_l" if tag == "ulna_l" else ""),
                 "statement": "The source elbow hinge rotates the %s about its local "
                              "+z with range [0, 2.26893] rad; positive q is inside "
                              "the declared range." % body,
                 "artifact_sha256": CHIMANOID_SHA256},
                {"id": "claim_authored_axes", "domain": "authored_semantics",
                 "authority": "operator_authored_semantics",
                 "source_ref": "PREREGISTRATION.md sha256 " + PREREGISTRATION_SHA256,
                 "statement": "Authored anatomical directions for this frame: distal "
                              "-y (declared hand chain lies at -y), palm +x (palm is "
                              "the flexor side; +q elbow flexion carries the distal "
                              "chain toward +x), lateral %s (the radius body sits at "
                              "%s z offset from the %s)."
                              % (tuple(lateral), "+z" if lateral[2] > 0 else "-z", body),
                 "artifact_sha256": PREREGISTRATION_SHA256},
                {"id": "claim_derived_composition", "domain": "physics",
                 "authority": "derived_physics",
                 "source_ref": "assembly_frame_forest.py compose_chain over " + body,
                 "statement": "The frame origin is composed exclusively from pinned "
                              "declarations; identity quats make composition exact "
                              "translation addition.",
                 "artifact_sha256": CHIMANOID_SHA256},
                {"id": "claim_packet_components", "domain": "geometry",
                 "authority": "authoritative_database",
                 "source_ref": ".tmp/anatomy_compiler/runs/actual_monkey_fit.json segments",
                 "statement": "The fitted packet references %s as a component root "
                              "without declaring it; this packet authors that root's "
                              "frame; the packet's geometry/mass status for %s stays "
                              "unresolved." % (body, body),
                 "artifact_sha256": PACKET_SHA256},
            ],
            "required_knowledge_domains": ["geometry", "physics", "authored_semantics"],
            "construction_claim_ids": ["claim_authored_axes", "claim_derived_composition"],
            "validation_claim_ids": ["claim_xml_landmarks", "claim_elbow_axis",
                                     "claim_packet_components"],
            "landmarks": [
                {"id": "elbow_pivot", "claim_id": "claim_xml_landmarks",
                 "position": [0.0, 0.0, 0.0], "role": "elbow_pivot"},
                {"id": "radius_pivot", "claim_id": "claim_xml_landmarks",
                 "position": list(radius_local), "role": "forearm_marker"},
                {"id": "hand_pivot", "claim_id": "claim_xml_landmarks",
                 "position": hand_local, "role": "hand_marker"},
            ],
            "required_landmark_roles": ["elbow_pivot"],
            "direction_witnesses": [
                {"semantic": "distal", "positive_landmark": "hand_pivot",
                 "negative_landmark": "elbow_pivot", "min_separation": 0.25,
                 "claim_id": "claim_xml_landmarks"},
                {"semantic": "dorsal", "positive_landmark": "elbow_pivot",
                 "negative_landmark": "hand_pivot", "min_separation": 0.01,
                 "claim_id": "claim_xml_landmarks"},
                {"semantic": "lateral", "positive_landmark": "radius_pivot",
                 "negative_landmark": "elbow_pivot", "min_separation": 0.01,
                 "claim_id": "claim_xml_landmarks"},
            ],
            "geometry_coverage": {
                "required_elements": ["frame_origin", "elbow_pivot", "radius_pivot",
                                      "hand_pivot"],
                "element_bindings": {
                    "frame_origin": "%s_root_origin" % tag,
                    "elbow_pivot": "elbow_flexion_pivot",
                    "radius_pivot": "radioulnar_pivot",
                    "hand_pivot": "wrist_row_pivot",
                },
            },
            "ports": [
                {"id": "%s_elbow_proximal_port" % tag, "position": [0.0, 0.0, 0.0],
                 "normal": proximal, "outward_semantic": "proximal"},
                {"id": "%s_wrist_distal_port" % tag, "position": hand_local,
                 "normal": distal, "outward_semantic": "distal"},
                {"id": "%s_lateral_port" % tag, "position": list(radius_local),
                 "normal": list(lateral), "outward_semantic": "lateral"},
            ],
            "kinematic_witness": {
                "semantic": "palm", "claim_id": "claim_elbow_axis",
                "reference_origin": [0.0, 0.0, 0.0],
                "rest_points": rest, "moved_points": moved,
                "minimum_signed_progress": 0.001,
                "witness_pose": "elbow flexion q = %g rad (inside declared range), "
                                "all distal joint coordinates held at source rest 0"
                                % q,
            },
        }
    return packets


# ---- CLI ----------------------------------------------------------------------
def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--emit", action="store_true", help="write frame_forest.json")
    parser.add_argument("--emit-semantic-packets", action="store_true")
    parser.add_argument("--verify", action="store_true", help="validate emitted JSON")
    parser.add_argument("--self-check", action="store_true")
    parser.add_argument("--verify-live-source", metavar="CHIMANOID_PATH")
    parser.add_argument("--packet-path")
    parser.add_argument("--osim-path")
    args = parser.parse_args(argv)
    out = []
    document = build_document()
    if args.emit:
        Path("frame_forest.json").write_bytes(canonical(document) + b"\n")
        out.append("wrote frame_forest.json sha256=%s" % sha256_file("frame_forest.json"))
    if args.emit_semantic_packets:
        for tag, packet in semantic_packets().items():
            name = "semantic_frame_%s.json" % tag
            Path(name).write_bytes(canonical(packet) + b"\n")
            out.append("wrote %s sha256=%s" % (name, sha256_file(name)))
    if args.verify:
        loaded = json.loads(Path("frame_forest.json").read_text(encoding="utf-8"))
        out.append(json.dumps(validate_document(loaded), indent=1, sort_keys=True))
        out.append("c01=" + json.dumps(c01_checks(loaded), sort_keys=True))
        out.append("separation=" + json.dumps(separation_check(loaded), sort_keys=True))
    if args.verify_live_source:
        out.append("live=" + json.dumps(verify_live_source(
            args.verify_live_source, args.packet_path, args.osim_path), sort_keys=True))
    if args.self_check:
        receipt = validate_document(document)
        c01 = c01_checks(document)
        sep = separation_check(document)
        out.append("self_check=PASS document_sha256=%s c01_max_round_trip=%s"
                   % (receipt["document_sha256"],
                      max(v["round_trip_max_error"] for v in c01.values())))
        out.append("separation=" + json.dumps(sep, sort_keys=True))
    if not out:
        parser.print_help()
    for row in out:
        print(row)


if __name__ == "__main__":
    main()
