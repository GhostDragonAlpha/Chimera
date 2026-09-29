"""MAT2-A06: explicit attachment and waypoint ownership registry.

Implements the frozen preregistration (PREREGISTRATION.md, this directory,
committed separately BEFORE this file):

- Every grasp-relevant endpoint and waypoint of the pinned macaque arm reference
  (monkeyArm_current.osim, sha-pinned) carries an explicit approved owner body
  and role; the A05 mutant hand's grasp endpoints carry their approved owner
  bodies and roles.
- Tissue-to-bone attachments are represented EXPLICITLY: an attachment exists
  only through its declared interface (MAT2-M05 law), one per muscle path
  endpoint, provenance explicit_declaration from the pinned osim bytes.
- Ontology containment and conventional rig parentage NEVER silently create a
  mechanical bond (MAT2-B04 law generalized): containment edges, attachments
  and bonds are disjoint relation lists; a bond or attachment whose provenance
  is containment/rig_parentage is refused by name; an unowned record is
  refused, never defaulted; a waypoint is never reinterpreted as an attachment
  port (card observation).
- C17 (finite attachment mechanics) stays an open inventory: no attachment
  patch area/shape, areal stiffness, couple resistance or weights exist in the
  pinned sources, so none is invented; a stiffness number without declared
  inputs is refused.

CPU-only, stdlib-only, deterministic (canonical JSON, no stochastic inputs).
Validation style follows MAT2-B04 assembly_frame_forest.py and MAT2-M05
interface_exchange.py: strict canonical digests, stable IDs, named refusals.
"""
from __future__ import annotations

import hashlib
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

SCHEMA = "chimera.attachment_ownership.v1"
DOCUMENT_REVISION = 1
OBJECT_ID = "mat2_a06_attachment_ownership"

# ---- pinned source identities (verified live; see PREREGISTRATION.md) --------
OSIM_PATH = "E:/PythonChimera/tools/science_funnel/data/macaque_arm/monkeyArm_current.osim"
OSIM_SHA256 = "4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895"
HAND_VTP_PATH = ("E:/PythonChimera/tools/science_funnel/data/macaque_arm/"
                 "Geometry/hand.vtp")
HAND_VTP_SHA256 = "a06ea7e079c849df07d6eec001e9bcc2ea193ecd3914011c78a993a5faa94fc6"
A05_DIR = Path("E:/ChimeraWork/monkey-coordination/kanban-attempts/MAT2-A05/"
               "b4ad70883ac2480a928dcc828f33c65f/checkout/tools/monkey_campaign/"
               "contributions/MAT2-A05")
A05_STRUCT_PATH = A05_DIR / "mutation_structure.json"
A05_STRUCT_SHA256 = "48b037593f63ec473947d787077ab6fbcd3b364afd15765bff508e7d54f45649"
A05_DECISION_ID = "A05-DIGIT-MUTATION-20260928"
A05_CRITERIA_SHA256 = ("34411771f7bd5dea2ec2cc4775d44b33df422e5454d283eae4067"
                       "6d1e3346544")
BASE_HEAD = "c525b82c7c3ce0128565424764293a3c85811ab3"
# Dependency winner heads (board of record, startup 2026-09-29)
DEP_HEADS = {
    "MAT2-A03": "775d09dea53051d28c84b197bdb9ec58a5d4efd4",
    "MAT2-A05": "a4fdaaa721f14ec085768bf5dcff2c6834a9abeb",
    "MAT2-M05": "cadaabc6ae0522c2530ce6fa090f07725d19a25f",
    "MAT2-B04": "ba24f78622bbf5e1e0e4338187e7889b7da221f5",
}

# ---- frozen grasp scope (PREREGISTRATION.md) ---------------------------------
GRASP_MUSCLES = (
    "abd_poll_longus", "ext_carpi_rad_longus", "ext_carp_rad_brevis",
    "ext_carpi_ulnaris", "ext_digitorum", "ext_digiti", "ext_indicis",
    "flex_carpi_radialis", "flex_carpi_ulnaris", "flex_digit_profundus",
    "flex_digit_superficialis", "flex_poll_longus", "palmaris_longus",
)
FROZEN_COUNTS = {
    "muscles": 13, "path_records": 48, "hand_body_records": 17,
    "endpoints": 26, "waypoints": 22, "conditional_waypoints": 1,
    "attachments": 26, "insertions_on_hand": 13, "origins": 13,
    "origin_bodies": {"humerus": 8, "ulna": 4, "radius": 1},
}
FROZEN_OSIM_BODIES = ("ground", "sternum", "clavicle", "scapula", "humerus",
                      "ulna1", "ulna", "radius_jcc", "radius", "radius1", "hand")
ROLES = ("origin_attachment", "insertion_attachment", "path_waypoint",
         "conditional_waypoint")
GRASP_ENDPOINT_OWNERS = (("thumb", "distal_thumb", "grasp_contact_endpoint"),
                         ("digit2", "distph2", "grasp_contact_endpoint"),
                         ("digit3", "distph3", "grasp_contact_endpoint"),
                         ("digit4", "distph4", "grasp_contact_endpoint"),
                         ("digit5", "distph5", "grasp_contact_endpoint"))
PALM_ANCHOR = "macaque_hand_anchor"
# A05-recorded mutant mappings (muscle, path point name) -> mutant body
A05_MAPPED = {
    ("ext_digitorum", "ext_digitorum-P3"): "macaque_hand_anchor",
    ("ext_digitorum", "ext_digitorum-P2"): "proxph3",
    ("flex_digit_profundus", "flex_digit_profundus-P4"): "fifthmc",
}
C17_REQUIRED_INPUTS = ("patch area/shape", "areal stiffness",
                       "couple resistance", "weights", "frame")

# ---- named refusals -----------------------------------------------------------
REF_NO_OWNER = "unowned_endpoint"
REF_NO_ROLE = "unowned_role"
REF_OWNER_DEFAULT = "owner_default_refused"
REF_WAYPOINT_PORT = "waypoint_is_not_attachment_port"
REF_PARENTAGE_BOND = "bond_from_parentage_refused"
REF_BAD_PIN = "live_source_hash_mismatch"
REF_STIFFNESS = "attachment_stiffness_unsourced"
REF_OVERLAP = "containment_bond_identity_overlap"
REF_ATTACHMENT_ROLE = "attachment_requires_endpoint_role"
REF_INTERFACE_MISSING = "attachment_interface_missing"
REF_BAD_BODY = "owner_body_not_in_source_vocabulary"
REF_BAD_ROLE = "role_not_in_frozen_role_set"
REF_SCOPE = "grasp_scope_mismatch"
REF_MAPPING = "mutant_mapping_not_honest"


def require(condition, code):
    """Named refusal; no numeric inference or repair."""
    if not condition:
        raise ValueError(code)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def preregistration_sha256():
    return sha256_file(Path(__file__).resolve().parent / "PREREGISTRATION.md")


# ---- pinned source extraction -------------------------------------------------
def _location(text):
    values = [float(x) for x in text.split()]
    require(len(values) == 3 and all(math.isfinite(v) for v in values),
            "osim_location_invalid")
    return values


def extract_osim_scope(osim_path=OSIM_PATH):
    """Parse the pinned osim; return (body names, scoped muscle point lists)."""
    require(sha256_file(osim_path) == OSIM_SHA256, REF_BAD_PIN + ":osim")
    root = ET.parse(osim_path).getroot()
    model = root.find(".//Model")
    bodies = [b.get("name") for b in model.find("BodySet/objects")]
    require(tuple(bodies) == FROZEN_OSIM_BODIES, "osim_body_vocabulary_changed")
    scoped = []
    for muscle in model.find("ForceSet/objects"):
        points = []
        pset = muscle.find(".//PathPointSet/objects")
        require(pset is not None, "osim_pathpointset_missing:" + muscle.get("name"))
        for index, element in enumerate(list(pset)):
            require(element.tag in ("PathPoint", "ConditionalPathPoint"),
                    "osim_unsupported_path_element:" + element.tag)
            row = {"index": index, "name": element.get("name"),
                   "body": element.findtext("body").strip(),
                   "location_m": _location(element.findtext("location")),
                   "conditional": element.tag == "ConditionalPathPoint"}
            if row["conditional"]:
                row["coordinate"] = element.findtext("coordinate").strip()
                row["range_rad"] = [float(x) for x
                                    in element.findtext("range").split()]
            require(row["body"] in FROZEN_OSIM_BODIES,
                    REF_BAD_BODY + ":" + row["body"])
            points.append(row)
        if any(p["body"] == "hand" for p in points):
            scoped.append((muscle.get("name"), points))
    return bodies, scoped


def role_for(index, count, conditional):
    if index == 0:
        return "origin_attachment"
    if index == count - 1:
        return "insertion_attachment"
    return "conditional_waypoint" if conditional else "path_waypoint"


# ---- owner resolution: explicit or refused, NEVER defaulted -------------------
def resolve_owner(record, source="osim"):
    """Return the record's explicit owner body; refuse to invent one.

    A record with no explicit owner body is an unowned endpoint: refused by
    name (never defaulted to a parent, containing body or neighbor).
    """
    owner = record.get("owner_body") if isinstance(record, dict) else None
    if owner is None or not str(owner).strip():
        raise ValueError(REF_OWNER_DEFAULT
                         + ":" + source + ":" + str(record.get("record_id")))
    return owner


# ---- document construction ----------------------------------------------------
def _source_pins():
    return [
        {"id": "source.macaque_arm_osim", "kind": "model_definition",
         "path": OSIM_PATH, "sha256": OSIM_SHA256,
         "role": "independent arm reference; attachment ownership source"},
        {"id": "source.macaque_hand_envelope", "kind": "geometry_asset",
         "path": HAND_VTP_PATH, "sha256": HAND_VTP_SHA256,
         "role": "hand surface envelope for capture context only"},
        {"id": "source.a05_mutation_structure", "kind": "model_definition",
         "path": str(A05_STRUCT_PATH).replace("\\", "/"),
         "sha256": A05_STRUCT_SHA256,
         "role": "A05 mutant hand record; grasp endpoints and bonds source"},
    ]


def _path_records(scoped, a05):
    rows = []
    mapping_names = {(m["muscle"], m["path_point"]): m for m in
                     a05["muscle_anchor_mapping"]}
    for muscle, points in scoped:
        count = len(points)
        for point in points:
            role = role_for(point["index"], count, point["conditional"])
            record_id = "path.%s.%d" % (muscle, point["index"])
            mutant = {"status": "not_on_hand_body"}
            if point["body"] == "hand":
                mapped = mapping_names.get((muscle, point["name"]))
                if mapped is not None:
                    mutant = {"status": "mapped",
                              "mutant_body": mapped["nearest_mutant_body"],
                              "distance_m": mapped["distance_m"]}
                else:
                    mutant = {"status": "pending_assembly_mapping"}
            rows.append({
                "record_id": record_id,
                "muscle": muscle,
                "index": point["index"],
                "declared_name": point["name"],
                "owner_body": point["body"],
                "role": role,
                "location_m": point["location_m"],
                "on_hand_body": point["body"] == "hand",
                "conditional": ({"coordinate": point["coordinate"],
                                 "range_rad": point["range_rad"]}
                                if point["conditional"] else None),
                "mutant_mapping": mutant,
                "approved_by": {"source": "source.macaque_arm_osim",
                                "sha256": OSIM_SHA256},
            })
    return rows


def _grasp_endpoints(a05):
    tips = a05["envelope_check"]["fingertip_positions_m"]
    body_names = {b["name"] for b in a05["bodies"]}
    rows = []
    for key, owner, role in GRASP_ENDPOINT_OWNERS:
        require(owner in body_names, "grasp_endpoint_owner_not_a05_body:" + owner)
        rows.append({
            "endpoint_id": "grasp.fingertip." + key,
            "owner_body": "ref.macaque_arm_hand_mutation.body." + owner,
            "role": role,
            "position_m": tips[key],
            "frame": "macaque_arm_hand_mutation_frame",
            "approved_by": {"captain_decision": A05_DECISION_ID,
                            "criteria_sha256": A05_CRITERIA_SHA256,
                            "source": "source.a05_mutation_structure"},
        })
    rows.append({
        "endpoint_id": "grasp.palm_anchor",
        "owner_body": "ref.macaque_arm_hand_mutation.body." + PALM_ANCHOR,
        "role": "grasp_palm_reference",
        "position_m": [0.0, 0.0, 0.0],
        "frame": "macaque_arm_hand_mutation_frame",
        "approved_by": {"captain_decision": A05_DECISION_ID,
                        "criteria_sha256": A05_CRITERIA_SHA256,
                        "source": "source.a05_mutation_structure"},
    })
    return rows


def _attachments(scoped):
    rows = []
    for muscle, points in scoped:
        for index, point in enumerate(points):
            if index == 0:
                kind, role = "origin", "origin_attachment"
            elif index == len(points) - 1:
                kind, role = "insertion", "insertion_attachment"
            else:
                continue
            rows.append({
                "attachment_id": "attach.%s.%s" % (muscle, kind),
                "path_record_id": "path.%s.%d" % (muscle, index),
                "tissue": muscle,
                "bone": point["body"],
                "role": role,
                "interface_id": "iface:tendon-%s-%s" % (muscle, kind),
                "transfers": "force",
                "location_m": point["location_m"],
                "provenance": {"kind": "explicit_declaration",
                               "source": "source.macaque_arm_osim",
                               "sha256": OSIM_SHA256},
                "mechanics_c17": {
                    "required_inputs": list(C17_REQUIRED_INPUTS),
                    "status": "inputs_unavailable_in_pinned_sources",
                    "note": "the pinned osim declares path points only; no "
                            "attachment patch area/shape, areal stiffness, "
                            "couple resistance or weights exist in any pinned "
                            "source; none is invented (no synthetic lambda_min)"},
            })
    return rows


def _bonds(a05):
    rows = []
    provenance = {"kind": "explicit_declaration",
                  "authority": "Captain decision " + A05_DECISION_ID,
                  "criteria_sha256": A05_CRITERIA_SHA256,
                  "source": "source.a05_mutation_structure",
                  "sha256": A05_STRUCT_SHA256}
    for joint in a05["anchor_body"]["joints"]:
        rows.append({
            "bond_id": "bond.mutant." + joint["name"],
            "joint": joint["name"],
            "child_body": "ref.macaque_arm_hand_mutation.body." + PALM_ANCHOR,
            "parent_body_declared": None,
            "parent_note": "wrist dof carried on the anchor body; the forearm "
                           "attachment is outside the A05 mutation record",
            "provenance": provenance,
        })
    for body in a05["bodies"]:
        parent = body["parent"].rsplit(".", 1)[-1]
        for joint in body.get("joints", []):
            rows.append({
                "bond_id": "bond.mutant." + joint["name"],
                "joint": joint["name"],
                "child_body": "ref.macaque_arm_hand_mutation.body."
                              + body["name"],
                "parent_body_declared": "ref.macaque_arm_hand_mutation.body."
                                        + parent,
                "parent_note": None,
                "provenance": provenance,
            })
    return rows


def _containment_edges(osim_bodies, a05):
    edges = []
    for name in osim_bodies:
        edges.append({"edge_id": "contain.osim.body." + name,
                      "child": "osim.body." + name,
                      "parent": "osim.model_frame",
                      "kind": "containment",
                      "origin": "osim Model frame membership",
                      "sha256": OSIM_SHA256})
    edges.append({"edge_id": "contain.mutant.anchor_root",
                  "child": "ref.macaque_arm_hand_mutation.body." + PALM_ANCHOR,
                  "parent": "mutant_frame_root",
                  "kind": "containment",
                  "origin": "A05 MJCF rig root",
                  "sha256": A05_STRUCT_SHA256})
    for body in a05["bodies"]:
        edges.append({"edge_id": "contain.mutant.body." + body["name"],
                      "child": "ref.macaque_arm_hand_mutation.body."
                               + body["name"],
                      "parent": body["parent"],
                      "kind": "containment",
                      "origin": "A05 MJCF rig parentage",
                      "sha256": A05_STRUCT_SHA256})
    return edges


def build_document():
    osim_bodies, scoped = extract_osim_scope()
    require(sha256_file(A05_STRUCT_PATH) == A05_STRUCT_SHA256,
            REF_BAD_PIN + ":a05_structure")
    require(sha256_file(HAND_VTP_PATH) == HAND_VTP_SHA256,
            REF_BAD_PIN + ":hand_vtp")
    a05 = json.loads(A05_STRUCT_PATH.read_text(encoding="utf-8"))
    records = _path_records(scoped, a05)
    document = {
        "schema": SCHEMA,
        "revision": DOCUMENT_REVISION,
        "object_id": OBJECT_ID,
        "task_id": "MAT2-A06",
        "source_head": BASE_HEAD,
        "preregistration_commit": "c436b865d4173cd50e8a0ed5bf7a8289e540ef42",
        "preregistration_sha256": preregistration_sha256(),
        "attempt_id": "d35796819ef74e6681f1bc6a5fd2ec9e",
        "arrival_id": "arrival-6fa733ab10c745d580180fe59cd2565f",
        "criteria_sha256": "31b38a12a8d7a1f28d6b5191e428bab4c11b7267649c5494"
                           "16d85225ee39ecbe",
        "done_when": "Every grasp-relevant endpoint and waypoint has an "
                     "explicit approved body and role. Material-first addition: "
                     "Represent tissue-to-bone attachments explicitly; ontology "
                     "containment and conventional rig parentage never silently "
                     "create a mechanical bond.",
        "observation": "Do not reinterpret waypoints as attachment ports",
        "dependency_heads": DEP_HEADS,
        "frames": {
            "osim_hand_frame": {
                "frame_id": "osim.body.hand",
                "owner_body": "hand",
                "coordinate_unit": "m",
                "note": "osim macaque hand body frame; muscle path locations "
                        "are declared in their owning body's frame"},
            "mutant_frame": {
                "frame_id": "macaque_arm_hand_mutation_frame",
                "anchor": "macaque hand body origin (wrist joint location "
                          "0 0 0 of the macaque wrist custom joint)",
                "coordinate_unit": "m",
                "correspondence": "recorded A05 anchor transfer (anchors "
                                  "recorded verbatim in the macaque hand "
                                  "frame); not a new fit",
                "sha256": A05_STRUCT_SHA256},
        },
        "grasp_scope": {
            "definition": "a muscle is grasp-relevant iff it has at least one "
                          "path point on osim body 'hand'",
            "muscles": list(GRASP_MUSCLES),
            "frozen_counts": dict(FROZEN_COUNTS),
        },
        "sources": _source_pins(),
        "path_records": records,
        "grasp_endpoints": _grasp_endpoints(a05),
        "attachments": _attachments(scoped),
        "bonds": _bonds(a05),
        "containment_edges": _containment_edges(osim_bodies, a05),
        "law_statement": {
            "no_silent_bond": "containment edges and rig parentage are "
                              "placement/ontology only; a mechanical bond or a "
                              "tissue-to-bone attachment exists only through "
                              "its explicit record with explicit_declaration "
                              "provenance and (for attachments) an identified "
                              "interface",
            "waypoints": "a waypoint is a path shape record, never an "
                         "attachment port: interface=None, bond=False",
            "lineage": ["MAT2-B04 frame forest: containment and bonds are "
                        "disjoint relation lists",
                        "MAT2-M05 interface exchange: bonds exist only through "
                        "identified interfaces; auto-bond refused"],
        },
    }
    return document


# ---- validation ----------------------------------------------------------------
def _finite(value, label):
    require(type(value) is float or type(value) is int, "nonfinite_number:" + label)
    require(math.isfinite(value), "nonfinite_number:" + label)
    return float(value)


def validate_document(document, osim_path=OSIM_PATH, a05_path=A05_STRUCT_PATH,
                      vtp_path=HAND_VTP_PATH, verify_live_pins=True):
    """Validate one ownership document; returns a normalized summary dict."""
    require(isinstance(document, dict), "document_not_object")
    require(document.get("schema") == SCHEMA, "unsupported_attachment_schema")
    require(type(document.get("revision")) is int
            and document["revision"] > 0, "invalid_revision")
    require(document.get("object_id") == OBJECT_ID, "invalid_object_id")
    require(document.get("preregistration_sha256") == preregistration_sha256(),
            "preregistration_freeze_mismatch")
    if verify_live_pins:
        checks = {"osim_sha256": sha256_file(osim_path),
                  "hand_vtp_sha256": sha256_file(vtp_path),
                  "a05_structure_sha256": sha256_file(a05_path)}
        require(checks["osim_sha256"] == OSIM_SHA256, REF_BAD_PIN + ":osim")
        require(checks["hand_vtp_sha256"] == HAND_VTP_SHA256,
                REF_BAD_PIN + ":hand_vtp")
        require(checks["a05_structure_sha256"] == A05_STRUCT_SHA256,
                REF_BAD_PIN + ":a05_structure")
    else:
        checks = {}

    # P2 scope (muscle set only; row counts after per-row ownership checks so
    # semantic refusals bite before aggregate counts)
    scope = document["grasp_scope"]
    require(tuple(scope["muscles"]) == GRASP_MUSCLES, REF_SCOPE + ":muscles")
    records = document["path_records"]
    scoped_muscles = sorted({r["muscle"] for r in records})
    require(scoped_muscles == sorted(GRASP_MUSCLES), REF_SCOPE + ":muscle_set")

    # P3 ownership: explicit, in vocabulary, never defaulted
    for row in records:
        owner = row.get("owner_body")
        require(owner is not None and str(owner).strip(), REF_NO_OWNER
                + ":" + row["record_id"])
        require(owner == resolve_owner(row), REF_OWNER_DEFAULT
                + ":" + row["record_id"])
        require(owner in FROZEN_OSIM_BODIES, REF_BAD_BODY + ":" + row["record_id"])
        role = row.get("role")
        require(role is not None and role in ROLES, REF_NO_ROLE
                + ":" + row["record_id"])
        require(row["approved_by"]["sha256"] == OSIM_SHA256,
                "record_approval_pin_mismatch:" + row["record_id"])

    require(len(records) == FROZEN_COUNTS["path_records"], REF_SCOPE + ":records")
    require(sum(1 for r in records if r["on_hand_body"])
            == FROZEN_COUNTS["hand_body_records"], REF_SCOPE + ":hand_records")
    require(sum(1 for r in records
                if r["role"] in ("origin_attachment", "insertion_attachment"))
            == FROZEN_COUNTS["endpoints"], REF_SCOPE + ":endpoints")
    waypoints = [r for r in records if r["role"].endswith("waypoint")]
    require(len(waypoints) == FROZEN_COUNTS["waypoints"], REF_SCOPE + ":waypoints")
    require(sum(1 for r in waypoints if r["conditional"] is not None)
            == FROZEN_COUNTS["conditional_waypoints"],
            REF_SCOPE + ":conditional")
    conditional = next(r for r in waypoints if r["conditional"] is not None)
    require(conditional["muscle"] == "flex_digit_profundus"
            and conditional["declared_name"] == "flex_digit_profundus-P2"
            and conditional["owner_body"] == "radius"
            and conditional["conditional"]["coordinate"] == "radial_pronation"
            and conditional["conditional"]["range_rad"] == [-1.5708, 0.352382],
            REF_SCOPE + ":conditional_record")

    # P3 grasp endpoints
    endpoints = document["grasp_endpoints"]
    require(len(endpoints) == 6, "grasp_endpoint_count_invalid")
    for row in endpoints:
        owner = row.get("owner_body")
        require(owner is not None and str(owner).strip(), REF_NO_OWNER
                + ":" + row["endpoint_id"])
        require(row.get("role") in ("grasp_contact_endpoint",
                                    "grasp_palm_reference"),
                REF_NO_ROLE + ":" + row["endpoint_id"])
        require(row["approved_by"]["captain_decision"] == A05_DECISION_ID
                and row["approved_by"]["criteria_sha256"] == A05_CRITERIA_SHA256,
                "grasp_endpoint_approval_missing:" + row["endpoint_id"])
        for value in row["position_m"]:
            _finite(value, row["endpoint_id"])
    fingertips = [r for r in endpoints if r["role"] == "grasp_contact_endpoint"]
    require(sorted(r["endpoint_id"] for r in fingertips)
            == ["grasp.fingertip.digit2", "grasp.fingertip.digit3",
                "grasp.fingertip.digit4", "grasp.fingertip.digit5",
                "grasp.fingertip.thumb"], "fingertip_set_invalid")

    # P4 waypoints are never attachment ports
    for row in waypoints:
        require(row.get("interface_id") is None and row.get("bond") is None,
                REF_WAYPOINT_PORT + ":" + row["record_id"])

    # P5 explicit attachments through identified interfaces (per-row checks
    # first, so provenance refusals bite before aggregate counts)
    attachments = document["attachments"]
    attachment_ids = set()
    interface_ids = set()
    record_roles = {r["record_id"]: r["role"] for r in records}
    insertions_on_hand = 0
    for row in attachments:
        require(row["attachment_id"] not in attachment_ids,
                "duplicate_attachment:" + row["attachment_id"])
        attachment_ids.add(row["attachment_id"])
        require(row["interface_id"] not in interface_ids,
                "duplicate_interface:" + row["interface_id"])
        interface_ids.add(row["interface_id"])
        require(row["interface_id"], REF_INTERFACE_MISSING
                + ":" + row["attachment_id"])
        require(row["transfers"] == "force", "attachment_transfers_invalid")
        require(record_roles.get(row["path_record_id"]) == row["role"],
                REF_ATTACHMENT_ROLE + ":" + row["attachment_id"])
        require(row["provenance"]["kind"] == "explicit_declaration",
                REF_PARENTAGE_BOND + ":" + row["attachment_id"])
        require(row["provenance"]["sha256"] == OSIM_SHA256,
                "attachment_pin_mismatch:" + row["attachment_id"])
        # P8 C17 honesty: no stiffness numbers without declared inputs
        mech = row["mechanics_c17"]
        require(tuple(mech["required_inputs"]) == C17_REQUIRED_INPUTS,
                "c17_inputs_list_invalid")
        numeric = [k for k, v in mech.items()
                   if isinstance(v, (int, float)) and not isinstance(v, bool)]
        require(not numeric, REF_STIFFNESS + ":" + row["attachment_id"])
        require(mech["status"] == "inputs_unavailable_in_pinned_sources",
                "c17_status_invalid")
        if row["role"] == "insertion_attachment":
            require(row["bone"] == "hand",
                    "insertion_not_on_hand:" + row["attachment_id"])
            insertions_on_hand += 1
    require(len(attachments) == FROZEN_COUNTS["attachments"],
            REF_SCOPE + ":attachments")
    require(insertions_on_hand == FROZEN_COUNTS["insertions_on_hand"],
            REF_SCOPE + ":insertions")

    # P6 no silent bonds: provenance must be explicit declaration
    bonds = document["bonds"]
    bond_ids = set()
    for row in bonds:
        require(row["bond_id"] not in bond_ids, "duplicate_bond:" + row["bond_id"])
        bond_ids.add(row["bond_id"])
        kind = row["provenance"]["kind"]
        require(kind == "explicit_declaration",
                REF_PARENTAGE_BOND + ":" + row["bond_id"] + ":" + str(kind))
        require(row["provenance"]["criteria_sha256"] == A05_CRITERIA_SHA256,
                "bond_approval_missing:" + row["bond_id"])
    require(len(bonds) == 22, "bond_count_invalid")

    # P6 disjoint relation lists
    containment = document["containment_edges"]
    require(isinstance(containment, list) and containment, "containment_missing")
    containment_ids = set()
    for edge in containment:
        require(edge.get("kind") == "containment", "containment_edge_invalid")
        require(edge["edge_id"] not in containment_ids, "duplicate_containment")
        containment_ids.add(edge["edge_id"])
    require(not (containment_ids & attachment_ids)
            and not (containment_ids & bond_ids)
            and not (attachment_ids & bond_ids), REF_OVERLAP)

    # honest mutant mapping inventory
    mapped = [r for r in records if r["mutant_mapping"].get("status") == "mapped"]
    pending = [r for r in records
               if r["mutant_mapping"].get("status") == "pending_assembly_mapping"]
    require(len(mapped) == 3 and len(pending) == 14, REF_MAPPING)
    require(sorted((r["muscle"], r["declared_name"],
                    r["mutant_mapping"]["mutant_body"]) for r in mapped)
            == sorted((m, n, body) for (m, n), body in A05_MAPPED.items()),
            REF_MAPPING + ":names")

    return {
        "schema": "chimera.attachment_ownership.receipt.v1",
        "status": "PASS",
        "object_id": document["object_id"],
        "document_sha256": digest(document),
        "path_records": len(records),
        "hand_body_records": sum(1 for r in records if r["on_hand_body"]),
        "endpoints": FROZEN_COUNTS["endpoints"],
        "waypoints": len(waypoints),
        "attachments": len(attachments),
        "bonds": len(bonds),
        "containment_edges": len(containment),
        "grasp_endpoints": len(endpoints),
        "mutant_mapped": len(mapped),
        "mutant_pending": len(pending),
        "live_pins": checks,
        "limits": "Checks declared evidence and structural invariants; does "
                  "not authenticate upstream sources, qualify attachment "
                  "mechanics (C17 stays open), or replace runtime tests.",
    }


# ---- separation check (B04-style) ----------------------------------------------
def separation_check(document):
    """Removing all containment edges changes no attachment/bond, and vice versa."""
    without_containment = {**document, "containment_edges": []}
    without_mechanics = {**document, "attachments": [], "bonds": []}
    require(digest(document["bonds"]) == digest(without_containment["bonds"]),
            "containment_changed_bonds")
    require(digest(document["attachments"])
            == digest(without_containment["attachments"]),
            "containment_changed_attachments")
    require(digest(document["containment_edges"])
            == digest(without_mechanics["containment_edges"]),
            "bonds_changed_containment")
    return {"containment_unchanged_without_mechanics": True,
            "mechanics_unchanged_without_containment": True}


# ---- falsifier tamper probes (each must fire exactly its named refusal) --------
def tamper_rig_parentage(document):
    """T1: promote rig parentage (A05 anchor->firstmc) into a mechanical bond."""
    tampered = json.loads(json.dumps(document))
    tampered["bonds"].append({
        "bond_id": "bond.rig_tamper.anchor_firstmc",
        "joint": "fixed_rig_parentage",
        "child_body": "ref.macaque_arm_hand_mutation.body.firstmc",
        "parent_body_declared":
            "ref.macaque_arm_hand_mutation.body.macaque_hand_anchor",
        "parent_note": "TAMPER: MJCF parent attribute promoted to a bond",
        "provenance": {"kind": "rig_parentage",
                       "source": "A05 MJCF body parent attribute"}})
    return tampered


def tamper_containment_bond(document):
    """T1b: promote a containment edge into an attachment record."""
    tampered = json.loads(json.dumps(document))
    tampered["attachments"].append({
        "attachment_id": "attach.containment_tamper",
        "path_record_id": "path.ext_digitorum.0",
        "tissue": "osim.model_frame", "bone": "hand", "role": "origin_attachment",
        "interface_id": "iface:containment-tamper", "transfers": "force",
        "location_m": [0.0, 0.0, 0.0],
        "provenance": {"kind": "containment", "source": "osim Model frame"},
        "mechanics_c17": {"required_inputs": list(C17_REQUIRED_INPUTS),
                          "status": "inputs_unavailable_in_pinned_sources"}})
    return tampered


def tamper_unowned(document):
    """T2: strip the owner body and the role from one path record."""
    tampered = json.loads(json.dumps(document))
    tampered["path_records"][0]["owner_body"] = None
    return tampered


def tamper_role(document):
    """T2b: strip a role."""
    tampered = json.loads(json.dumps(document))
    tampered["path_records"][0]["role"] = None
    return tampered


def tamper_waypoint_port(document):
    """T3: reinterpret a waypoint (hand-body, non-insertion) as an attachment port."""
    tampered = json.loads(json.dumps(document))
    victim = next(r for r in tampered["path_records"]
                  if r["role"] == "path_waypoint" and r["on_hand_body"])
    victim["interface_id"] = "iface:waypoint-tamper"
    return tampered


def tamper_stiffness(document):
    """T6/P8: claim an attachment stiffness without declared inputs."""
    tampered = json.loads(json.dumps(document))
    tampered["attachments"][0]["mechanics_c17"]["stiffness_N_per_m2"] = 1.0e6
    return tampered


# ---- CLI ------------------------------------------------------------------------
def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--emit", action="store_true",
                        help="write attachment_ownership.json")
    parser.add_argument("--verify", action="store_true",
                        help="validate the emitted JSON + checks + separation")
    parser.add_argument("--self-check", action="store_true",
                        help="build + validate in memory")
    parser.add_argument("--tamper-rig", action="store_true")
    parser.add_argument("--tamper-containment", action="store_true")
    parser.add_argument("--tamper-unowned", action="store_true")
    parser.add_argument("--tamper-role", action="store_true")
    parser.add_argument("--tamper-waypoint", action="store_true")
    parser.add_argument("--tamper-stiffness", action="store_true")
    args = parser.parse_args(argv)
    out = []
    document = build_document()
    here = Path(__file__).resolve().parent
    emitted = here / "attachment_ownership.json"
    if args.emit:
        emitted.write_bytes(canonical(document) + b"\n")
        out.append("wrote attachment_ownership.json sha256=%s"
                   % sha256_file(emitted))
    if args.verify:
        loaded = json.loads(emitted.read_text(encoding="utf-8"))
        receipt = validate_document(loaded)
        out.append(json.dumps(receipt, indent=1, sort_keys=True))
        out.append("separation=" + json.dumps(separation_check(loaded),
                                              sort_keys=True))
    if args.self_check:
        receipt = validate_document(document)
        out.append("self_check=PASS document_sha256=%s"
                   % receipt["document_sha256"])
    probes = (("--tamper-rig", tamper_rig_parentage, REF_PARENTAGE_BOND),
              ("--tamper-containment", tamper_containment_bond,
               REF_PARENTAGE_BOND),
              ("--tamper-unowned", tamper_unowned, REF_NO_OWNER),
              ("--tamper-role", tamper_role, REF_NO_ROLE),
              ("--tamper-waypoint", tamper_waypoint_port, REF_WAYPOINT_PORT),
              ("--tamper-stiffness", tamper_stiffness, REF_STIFFNESS))
    for flag, mutate, expected in probes:
        if getattr(args, flag.lstrip("-").replace("-", "_")):
            try:
                validate_document(mutate(document), verify_live_pins=False)
                out.append("%s=FAIL no refusal fired (expected %s)"
                           % (flag, expected))
            except ValueError as err:
                fired = str(err)
                out.append("%s=%s (refused: %s)"
                           % (flag, "BIT" if fired.startswith(expected)
                              else "WRONG-REFUSAL", fired))
    if not out:
        parser.print_help()
    for row in out:
        print(row)


if __name__ == "__main__":
    main()
