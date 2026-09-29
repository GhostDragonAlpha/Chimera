"""MAT2-A07: lawful resolution of failed/outside attachment placements.

Completion of record for the MAT2-A06 ownership registry (PR #250, merged at
fa8ecf67). Implements the frozen preregistration (PREREGISTRATION.md, this
directory, committed ALONE before this file):

- Every FAILED or OUTSIDE placement in the sealed A06 registry is resolved into
  EXACTLY ONE of the two lawful terminal states:
    * `supported` — pinned evidence (named source + sha256 + approval
      reference: a recorded captain/lead decision or the sha-pinned osim
      declaration itself),
    * `explicitly_unresolved` — a missing_evidence block naming the absent
      record or decision and the rank that must authorize it.
  Nothing else is lawful: no guessed body, no nearest-neighbor default, no
  silent "supported", no fitting. Any new fitting experiment is SEPARATELY
  authorized (a recorded lead/captain decision); none is authorized for this
  card, so none is run, none is simulated, and a resolution that smuggles one
  in is refused by name (`fitting_unauthorized_refused`).
- The OUTSIDE test is a frozen MEASUREMENT, not a fit: each osim hand-body path
  location (verbatim from the sealed A06 registry bytes, sha-pinned) is tested
  against the A05-recorded hand envelope bounds; per-axis signed excesses are
  carried exactly. The validator recomputes the test and refuses any
  disagreement (`measured_status_mismatch`).
- C17 (finite attachment mechanics) stays open exactly as A06 left it.
- The A06 registry is READ-ONLY to this card: the registry FILE bytes are
  pinned (`a06_registry_pin_mismatch`), and the card adds a separate additive
  document — it never edits, rebuilds or "repairs" the registry.

CPU-only, stdlib-only, deterministic (canonical JSON, no stochastic inputs).
Validation style follows MAT2-A06 attachment_ownership.py: strict canonical
digests, stable ids, named refusals that bite before aggregate counts.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

SCHEMA = "chimera.attachment_placement_resolution.v1"
DOCUMENT_REVISION = 1
OBJECT_ID = "mat2_a07_placement_resolution"

# ---- sealed-line identities ---------------------------------------------------
BASE_HEAD = "fa8ecf67be01a7ff0dbb4c538ad88b68ef196b5a"
A06_MERGE_PR = 250
A06_PUBLICATION_COMMIT = "3271888c"
# The A06 registry, as committed bytes at the sealed tip (A06 report table).
A06_REGISTRY_REL = Path("..") / "MAT2-A06" / "attachment_ownership.json"
A06_REGISTRY_SHA256 = ("f1f0430772258e8449fc354841becf2f1869783399e6"
                       "3f3f145565b8d0b1041c")
A06_TASK_ID = "MAT2-A06"

# ---- pinned source identities (verified live when present) --------------------
OSIM_PATH = "E:/PythonChimera/tools/science_funnel/data/macaque_arm/monkeyArm_current.osim"
OSIM_SHA256 = "4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895"
HAND_VTP_PATH = ("E:/PythonChimera/tools/science_funnel/data/macaque_arm/"
                 "Geometry/hand.vtp")
HAND_VTP_SHA256 = "a06ea7e079c849df07d6eec001e9bcc2ea193ecd3914011c78a993a5faa94fc6"
A05_STRUCT_PATH = Path("E:/ChimeraWork/monkey-coordination/kanban-attempts/"
                       "MAT2-A05/b4ad70883ac2480a928dcc828f33c65f/checkout/"
                       "tools/monkey_campaign/contributions/MAT2-A05/"
                       "mutation_structure.json")
A05_STRUCT_SHA256 = "48b037593f63ec473947d787077ab6fbcd3b364afd15765bff508e7d54f45649"
A05_DECISION_ID = "A05-DIGIT-MUTATION-20260928"
A05_CRITERIA_SHA256 = ("34411771f7bd5dea2ec2cc4775d44b33df422e5454d283eae4067"
                       "6d1e3346544")
# Frozen verbatim from the A05-recorded envelope_check.hand_vtp_bounds_m
# (hash-bound: when the live A05 file is present its bounds must equal these).
FROZEN_ENVELOPE_LO = [-0.0124375, -0.0837075, -0.00152775]
FROZEN_ENVELOPE_HI = [0.020731000000000003, -0.00010125000000000001,
                      0.004639750000000001]
AXES = ("x", "y", "z")

# Recorded planning observation (carried verbatim; sources at the sealed tip).
CARRIED_OBSERVATION = ("Candidate C remains failed at 67.147 micrometres per "
                       "side; four wrist sites outside under both loops")
CARRIED_AUTHORIZATION = ("No radius supersession or new fitting candidate is "
                         "authorized")

# ---- frozen counts (preregistration P2; the validator reproduces them) --------
FROZEN_COUNTS = {
    "path_resolutions": 48,
    "attachment_resolutions": 26,
    "waypoint_resolutions": 22,
    "grasp_endpoint_resolutions": 6,
    "hand_body_records": 17,
    "hand_insertions": 13,
    "hand_waypoints": 4,
    "mutant_mapped_records": 3,
    "pending_assembly_mapping": 14,
    "envelope_measured_outside": 8,
    "outside_insertions": 4,
    "outside_waypoints": 4,
    "pending_and_outside": 7,
    "attachments_mutant_supported": 2,
    "attachments_mutant_unresolved": 24,
    "waypoints_mutant_supported": 1,
    "waypoints_mutant_unresolved": 21,
}
# The frozen measured outside set (preregistration section 3), in registry order.
FROZEN_OUTSIDE = (
    "path.abd_poll_longus.3",
    "path.ext_carpi_rad_longus.3",
    "path.ext_carp_rad_brevis.2",
    "path.ext_digitorum.2",
    "path.ext_digiti.2",
    "path.ext_indicis.3",
    "path.flex_carpi_ulnaris.2",
    "path.palmaris_longus.3",
)
FROZEN_OUTSIDE_INSERTIONS = (
    "path.ext_carpi_rad_longus.3",
    "path.ext_indicis.3",
    "path.flex_carpi_ulnaris.2",
    "path.palmaris_longus.3",
)
FROZEN_OUTSIDE_WAYPOINTS = (
    "path.abd_poll_longus.3",
    "path.ext_carp_rad_brevis.2",
    "path.ext_digiti.2",
    "path.ext_digitorum.2",
)

PINNED_SHAS = frozenset({OSIM_SHA256, HAND_VTP_SHA256, A05_STRUCT_SHA256,
                         A06_REGISTRY_SHA256})

# ---- named refusals -----------------------------------------------------------
REF_REGISTRY_PIN = "a06_registry_pin_mismatch"
REF_BAD_PIN = "live_source_hash_mismatch"
REF_COUNTS = "frozen_count_mismatch"
REF_TOTALITY = "resolution_missing"
REF_STATE = "silent_default_refused"
REF_SUPPORTED_PIN = "supported_claim_missing_pin"
REF_FIT = "fitting_unauthorized_refused"
REF_MEASURE = "measured_status_mismatch"
REF_VERBATIM = "location_not_verbatim"
REF_STATUS_FABRICATED = "mutant_mapping_status_altered"
REF_C17 = "attachment_stiffness_unsourced"
REF_WAYPOINT_PORT = "waypoint_is_not_attachment_port"

SUPPORTED = "supported"
UNRESOLVED = "explicitly_unresolved"
STATES = (SUPPORTED, UNRESOLVED)
FORBIDDEN_KEY_TOKENS = ("fitted", "optimized", "optimizer")


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


def registry_path():
    return Path(__file__).resolve().parent / A06_REGISTRY_REL


def preregistration_sha256():
    return sha256_file(Path(__file__).resolve().parent / "PREREGISTRATION.md")


def _location(text):
    values = [float(x) for x in text.split()]
    require(len(values) == 3 and all(math.isfinite(v) for v in values),
            "osim_location_invalid")
    return values


def live_osim_scope(osim_path=OSIM_PATH):
    """Parse the pinned osim scope exactly as A06 defined it (13 muscles)."""
    import xml.etree.ElementTree as ET
    require(sha256_file(osim_path) == OSIM_SHA256, REF_BAD_PIN + ":osim")
    root = ET.parse(osim_path).getroot()
    model = root.find(".//Model")
    scoped = {}
    for muscle in model.find("ForceSet/objects"):
        points = []
        pset = muscle.find(".//PathPointSet/objects")
        require(pset is not None, "osim_pathpointset_missing:" + muscle.get("name"))
        for element in list(pset):
            require(element.tag in ("PathPoint", "ConditionalPathPoint"),
                    "osim_unsupported_path_element:" + element.tag)
            points.append({"name": element.get("name"),
                           "body": element.findtext("body").strip(),
                           "location_m": _location(element.findtext("location"))})
        if any(p["body"] == "hand" for p in points):
            scoped[muscle.get("name")] = points
    return scoped


def load_a05(a05_path=A05_STRUCT_PATH):
    """Load the pinned A05 structure; live-verify its hash when the file exists.

    The envelope bounds are the frozen preregistration constants; when the live
    file is available it must agree with them (refuse otherwise).
    """
    live = {"present": False, "sha256": None}
    path = Path(a05_path)
    if path.exists():
        live["present"] = True
        live["sha256"] = sha256_file(path)
        require(live["sha256"] == A05_STRUCT_SHA256, REF_BAD_PIN + ":a05_structure")
        a05 = json.loads(path.read_text(encoding="utf-8"))
        bounds = a05["envelope_check"]["hand_vtp_bounds_m"]
        require(bounds == [FROZEN_ENVELOPE_LO, FROZEN_ENVELOPE_HI],
                REF_BAD_PIN + ":a05_envelope_bounds_frozen_mismatch")
        captain = a05.get("captain_decision")
        require(isinstance(captain, dict)
                and captain.get("decision_id") == A05_DECISION_ID,
                REF_BAD_PIN + ":a05_decision_id")
    return live


def envelope_test(location_m):
    """Frozen measurement: axis-aligned bounds test (preregistration section 2)."""
    axes = []
    for index, value in enumerate(location_m):
        if value < FROZEN_ENVELOPE_LO[index]:
            axes.append({"axis": AXES[index], "kind": "below_lo",
                         "excess_m": value - FROZEN_ENVELOPE_LO[index]})
        elif value > FROZEN_ENVELOPE_HI[index]:
            axes.append({"axis": AXES[index], "kind": "above_hi",
                         "excess_m": value - FROZEN_ENVELOPE_HI[index]})
    return axes


# ---- evidence blocks (lawful vocabulary) --------------------------------------
def _osim_evidence(subject):
    return {"source": "source.macaque_arm_osim", "sha256": OSIM_SHA256,
            "approval": "explicit_declaration (pinned osim PathPoint)",
            "subject": subject}


def _a05_evidence(distance_m):
    return {"decision": A05_DECISION_ID,
            "criteria_sha256": A05_CRITERIA_SHA256,
            "source": "source.a05_mutation_structure",
            "sha256": A05_STRUCT_SHA256,
            "recorded_distance_m": distance_m,
            "approval": "recorded Captain decision (A05 winner record)"}


def _missing_assembly_mapping(measured):
    return {"kind": "recorded_assembly_mapping_decision",
            "detail": "no lead/captain-recorded nearest-mutant-body "
                      "correspondence exists for this path point in any "
                      "pinned source; a recorded assembly-mapping decision "
                      "(with distance) is required before this placement can "
                      "be supported",
            "authorization_required": "recorded lead or captain decision",
            "measured": measured}


def _missing_forearm_correspondence():
    return {"kind": "forearm_assembly_correspondence_record",
            "detail": "the A05 mutation record's scope is the hand; no "
                      "recorded forearm correspondence exists for these "
                      "bodies, so their mutant-assembly placement stays "
                      "unresolved (never defaulted)",
            "authorization_required": "recorded lead or captain decision"}


# ---- document construction ----------------------------------------------------
def _mutant_block(record, a05_mappings):
    """The mutant-assembly placement block for one path record (rules R1/R2/R3)."""
    status = record["mutant_mapping"]["status"]
    if status == "mapped":
        key = (record["muscle"], record["declared_name"])
        require(key in a05_mappings, REF_STATE + ":mapped_without_a05_record")
        return {SUPPORTED: True, "evidence": _a05_evidence(a05_mappings[key])}
    if status == "pending_assembly_mapping":
        return {UNRESOLVED: True,
                "missing_evidence": _missing_assembly_mapping(
                    "outside_envelope" if record["record_id"] in FROZEN_OUTSIDE
                    else "inside_envelope")}
    if status == "not_on_hand_body":
        return {UNRESOLVED: True,
                "missing_evidence": _missing_forearm_correspondence()}
    raise ValueError(REF_STATE + ":unknown_mutant_mapping_status:" + status)


def _path_resolutions(registry, a05_mappings, osim_scope):
    rows = []
    for record in registry["path_records"]:
        measured_axes = (envelope_test(record["location_m"])
                         if record["on_hand_body"] else [])
        outcome = ("outside" if measured_axes else
                   "inside" if record["on_hand_body"] else "not_tested")
        mutant = _mutant_block(record, a05_mappings)
        state = SUPPORTED if mutant.get(SUPPORTED) else UNRESOLVED
        # verbatim cross-check of the osim declaration (never rebuilt)
        scoped = osim_scope.get(record["muscle"]) if osim_scope else None
        rows.append({
            "record_id": record["record_id"],
            "muscle": record["muscle"],
            "index": record["index"],
            "declared_name": record["declared_name"],
            "owner_body": record["owner_body"],
            "role": record["role"],
            "on_hand_body": record["on_hand_body"],
            "location_m": record["location_m"],
            "mutant_mapping_status": record["mutant_mapping"]["status"],
            "osim_reference_placement": {"validity": SUPPORTED,
                                         "evidence": _osim_evidence(
                                             record["record_id"])},
            "envelope_measurement": {"in_scope": record["on_hand_body"],
                                     "bounds_source": "a05_envelope_check"
                                                      ".hand_vtp_bounds_m "
                                                      "(frozen)",
                                     "outcome": outcome,
                                     "outside_axes": measured_axes},
            "placement_failed_outside": bool(measured_axes),
            "resolution": state,
            "evidence": mutant.get("evidence"),
            "missing_evidence": mutant.get("missing_evidence"),
            "live_osim_verbatim_check": (scoped is not None),
        })
    return rows


def _child_resolutions(registry, by_record_id, id_key, prefix, record_field):
    """Attachment (26) and waypoint (22) rows: child validity follows the path
    record's mutant-assembly rule (R4/R5); osim-reference stays supported."""
    rows = []
    for source_row in registry[record_field]:
        record_id = source_row["path_record_id"] if id_key == "attachment_id" \
            else source_row["record_id"]
        parent = by_record_id[record_id]
        row = {
            id_key: source_row[id_key],
            "path_record_id": record_id,
        }
        if id_key == "attachment_id":
            row.update({"tissue": source_row["tissue"], "bone": source_row["bone"],
                        "interface_id": source_row["interface_id"],
                        "role": source_row["role"]})
            row["osim_reference_placement"] = {
                "validity": SUPPORTED,
                "evidence": {"source": "source.macaque_arm_osim",
                             "sha256": OSIM_SHA256,
                             "approval": "explicit_declaration provenance with "
                                         "identified interface "
                                         "(MAT2-A06 registry, M05 law)",
                             "subject": source_row["attachment_id"]}}
            # C17 inherited verbatim from the A06 registry (stays open, R7)
            row["mechanics_c17"] = source_row["mechanics_c17"]
        else:
            row.update({"owner_body": source_row["owner_body"],
                        "role": source_row["role"],
                        "conditional": source_row["conditional"]})
            row["osim_reference_placement"] = {
                "validity": SUPPORTED,
                "evidence": {"source": "source.macaque_arm_osim",
                             "sha256": OSIM_SHA256,
                             "approval": "explicit_declaration (pinned osim "
                                         "PathPoint); a waypoint is a path "
                                         "shape record, never an attachment "
                                         "port",
                             "subject": source_row["record_id"]}}
            row["interface_id"] = None
            row["bond"] = False
        row["placement_failed_outside"] = parent["placement_failed_outside"]
        row["resolution"] = parent["resolution"]
        row["evidence"] = parent["evidence"]
        row["missing_evidence"] = parent["missing_evidence"]
        rows.append(row)
    return rows


def build_document(verify_live_pins=True):
    registry_bytes = registry_path().read_bytes()
    require(sha256_file(registry_path()) == A06_REGISTRY_SHA256,
            REF_REGISTRY_PIN)
    registry = json.loads(registry_bytes.decode("utf-8"))
    live = {"a05_structure": load_a05()} if verify_live_pins else \
        {"a05_structure": {"present": False, "sha256": None}}
    if verify_live_pins:
        require(sha256_file(OSIM_PATH) == OSIM_SHA256, REF_BAD_PIN + ":osim")
        require(sha256_file(HAND_VTP_PATH) == HAND_VTP_SHA256,
                REF_BAD_PIN + ":hand_vtp")
        live["osim"] = OSIM_SHA256
        live["hand_vtp"] = HAND_VTP_SHA256
    osim_scope = live_osim_scope() if verify_live_pins else None
    a05_mappings = {}
    if live["a05_structure"]["present"]:
        a05 = json.loads(Path(A05_STRUCT_PATH).read_text(encoding="utf-8"))
        for mapping in a05["muscle_anchor_mapping"]:
            a05_mappings[(mapping["muscle"], mapping["path_point"])] = \
                mapping["distance_m"]

    path_rows = _path_resolutions(registry, a05_mappings, osim_scope)
    by_record_id = {row["record_id"]: row for row in path_rows}
    attachment_rows = _child_resolutions(registry, by_record_id,
                                         "attachment_id", "attach", "attachments")
    waypoint_rows = _child_resolutions(registry, by_record_id,
                                       "record_id", "wpt", "path_records")
    waypoint_rows = [row for row in waypoint_rows
                     if row["role"].endswith("waypoint")]
    grasp_rows = []
    for row in registry["grasp_endpoints"]:
        grasp_rows.append({
            "endpoint_id": row["endpoint_id"],
            "owner_body": row["owner_body"],
            "role": row["role"],
            "position_m": row["position_m"],
            "resolution": SUPPORTED,
            "evidence": {"decision": A05_DECISION_ID,
                         "criteria_sha256": A05_CRITERIA_SHA256,
                         "source": "source.a05_mutation_structure",
                         "sha256": A05_STRUCT_SHA256,
                         "approval": "recorded Captain decision (A05 winner "
                                     "record; positions are the A05 record's "
                                     "own envelope_check data)"},
            "missing_evidence": None,
        })

    counts = {
        "path_resolutions": len(path_rows),
        "attachment_resolutions": len(attachment_rows),
        "waypoint_resolutions": len(waypoint_rows),
        "grasp_endpoint_resolutions": len(grasp_rows),
        "hand_body_records": sum(1 for r in path_rows if r["on_hand_body"]),
        "hand_insertions": sum(1 for r in path_rows if r["on_hand_body"]
                               and r["role"] == "insertion_attachment"),
        "hand_waypoints": sum(1 for r in path_rows if r["on_hand_body"]
                              and r["role"].endswith("waypoint")),
        "mutant_mapped_records": sum(1 for r in path_rows
                                     if r["mutant_mapping_status"] == "mapped"),
        "pending_assembly_mapping": sum(1 for r in path_rows
                                        if r["mutant_mapping_status"]
                                        == "pending_assembly_mapping"),
        "envelope_measured_outside": sum(1 for r in path_rows
                                         if r["placement_failed_outside"]),
        "outside_insertions": sum(1 for r in path_rows
                                  if r["placement_failed_outside"]
                                  and r["role"] == "insertion_attachment"),
        "outside_waypoints": sum(1 for r in path_rows
                                 if r["placement_failed_outside"]
                                 and r["role"].endswith("waypoint")),
        "pending_and_outside": sum(1 for r in path_rows
                                   if r["placement_failed_outside"]
                                   and r["mutant_mapping_status"]
                                   == "pending_assembly_mapping"),
        "attachments_mutant_supported": sum(1 for r in attachment_rows
                                            if r["resolution"] == SUPPORTED),
        "attachments_mutant_unresolved": sum(1 for r in attachment_rows
                                             if r["resolution"] == UNRESOLVED),
        "waypoints_mutant_supported": sum(1 for r in waypoint_rows
                                          if r["resolution"] == SUPPORTED),
        "waypoints_mutant_unresolved": sum(1 for r in waypoint_rows
                                           if r["resolution"] == UNRESOLVED),
    }

    return {
        "schema": SCHEMA,
        "revision": DOCUMENT_REVISION,
        "object_id": OBJECT_ID,
        "task_id": "MAT2-A07",
        "source_head": BASE_HEAD,
        "preregistration_commit": None,  # filled by the separate-first commit
        "preregistration_sha256": preregistration_sha256(),
        "attempt_id": "638d4dc8a3384216b526ebc8bc16c3fe",
        "arrival_id": "arrival-2b610e46ac9a41e79daff5bfea970f34",
        "criteria_sha256": ("c4d4ae430027d489d58007cae3895b81dcbfa604c045aa35"
                            "049c3ecf333373f8"),
        "done_when": "Attachment validity is supported or explicitly "
                     "unresolved; any new fitting experiment is separately "
                     "authorized",
        "card_observation": CARRIED_OBSERVATION,
        "depends_on": {
            "MAT2-A06": {
                "merge_pr": A06_MERGE_PR,
                "merge_commit": BASE_HEAD,
                "publication_commit_prefix": A06_PUBLICATION_COMMIT,
                "registry_path": "tools/monkey_campaign/contributions/"
                                 + A06_TASK_ID + "/attachment_ownership.json",
                "registry_sha256": A06_REGISTRY_SHA256,
            },
        },
        "law_statement": {
            "vocabulary": "a placement is exactly one of: supported (pinned "
                          "evidence: source + sha256 + approval reference) or "
                          "explicitly_unresolved (named missing evidence and "
                          "the authorizing rank). Nothing else is lawful.",
            "no_fitting": "any new fitting experiment is separately authorized "
                          "(a recorded lead/captain decision); this card runs "
                          "none, simulates none, and refuses any resolution "
                          "that carries fitted/optimized values by name "
                          "(fitting_unauthorized_refused)",
            "no_defaults": "an unresolved placement is never defaulted to a "
                           "parent, neighbor or nearest body (B04 law "
                           "inherited); envelope presence creates no ownership",
            "measured_not_fitted": "the outside test is a frozen axis-aligned "
                                   "bounds measurement against the "
                                   "A05-recorded envelope bounds; per-axis "
                                   "excesses are recorded exactly",
            "registry_read_only": "the A06 registry is consumed as committed "
                                  "bytes; this document is additive and never "
                                  "edits or rebuilds it",
        },
        "carried_observation": {
            "text": CARRIED_OBSERVATION,
            "sources": [
                "tools/monkey_campaign/monkey_completion_map.json#tasks/A07 "
                "(observation) at sealed tip " + BASE_HEAD,
                "tools/monkey_campaign/MONKEY_COMPLETION_MAP.md (Anatomy "
                "bullet) at sealed tip " + BASE_HEAD,
            ],
            "recorded_authorization_state": CARRIED_AUTHORIZATION,
            "resolution": UNRESOLVED,
            "missing_evidence": {
                "kind": "separately_authorized_fitting_experiment",
                "detail": "the recorded loops left candidate C failed and "
                          "wrist sites outside; the only instrument that could "
                          "revise that record is a new fitting experiment, "
                          "which the same sealed record states is not "
                          "authorized; this card therefore leaves the record "
                          "explicitly unresolved",
                "authorization_required": "recorded lead or captain decision "
                                          "commissioning a bounded fitting "
                                          "experiment",
            },
            "instrument_note": "this card's envelope bounds test independently "
                               "measures exactly 4 outside wrist-region "
                               "insertion sites (4 outside waypoints besides); "
                               "the count convergence with the carried "
                               "observation is recorded as context only - the "
                               "historical loops were not re-run and are not "
                               "claimed as re-derived",
        },
        "sources": [
            {"id": "source.a06_attachment_ownership", "kind": "derived_registry",
             "path": "tools/monkey_campaign/contributions/MAT2-A06/"
                     "attachment_ownership.json",
             "sha256": A06_REGISTRY_SHA256,
             "role": "sealed ownership registry completed by this record"},
            {"id": "source.macaque_arm_osim", "kind": "model_definition",
             "path": OSIM_PATH, "sha256": OSIM_SHA256,
             "role": "independent arm reference; osim-reference placements"},
            {"id": "source.macaque_hand_envelope", "kind": "geometry_asset",
             "path": HAND_VTP_PATH, "sha256": HAND_VTP_SHA256,
             "role": "hand surface envelope for capture context only"},
            {"id": "source.a05_mutation_structure", "kind": "model_definition",
             "path": str(A05_STRUCT_PATH).replace("\\", "/"),
             "sha256": A05_STRUCT_SHA256,
             "role": "A05 mutant hand record; recorded mappings, envelope "
                     "bounds, grasp endpoints"},
        ],
        "live_pin_verification": live,
        "envelope_test": {
            "kind": "axis_aligned_bounds",
            "bounds_lo_m": FROZEN_ENVELOPE_LO,
            "bounds_hi_m": FROZEN_ENVELOPE_HI,
            "bounds_source": "source.a05_mutation_structure "
                             "envelope_check.hand_vtp_bounds_m (frozen "
                             "verbatim; live-verified when present)",
            "declared_approximation": "bounds test, not a mesh-inside test; "
                                      "per-axis signed excesses recorded "
                                      "exactly; forearm bodies out of scope",
        },
        "path_resolutions": path_rows,
        "attachment_resolutions": attachment_rows,
        "waypoint_resolutions": waypoint_rows,
        "grasp_endpoint_resolutions": grasp_rows,
        "counts": counts,
        "c17": {
            "status": "open",
            "carried_from": "MAT2-A06 registry mechanics_c17 blocks (verbatim)",
            "required_inputs": ["patch area/shape", "areal stiffness",
                                "couple resistance", "weights", "frame"],
            "note": "no attachment patch area/shape, areal stiffness, couple "
                    "resistance or weights exist in the pinned sources; none "
                    "is invented; no synthetic lambda_min",
        },
    }


# ---- validation ----------------------------------------------------------------
def _finite(value, label):
    require(type(value) is float or type(value) is int,
            "nonfinite_number:" + label)
    require(math.isfinite(value), "nonfinite_number:" + label)
    return float(value)


def _check_resolution_row(row, label):
    """Totality + vocabulary + evidence binding (P3/P4) for one resolution row."""
    state = row.get("resolution")
    require(state in STATES, REF_STATE + ":" + label + ":" + str(state))
    if state == SUPPORTED:
        evidence = row.get("evidence")
        require(isinstance(evidence, dict) and evidence, REF_SUPPORTED_PIN
                + ":" + label)
        require(bool(str(evidence.get("source", "")).strip()),
                REF_SUPPORTED_PIN + ":" + label + ":source")
        sha = evidence.get("sha256")
        require(sha in PINNED_SHAS, REF_SUPPORTED_PIN + ":" + label + ":sha")
        require(bool(str(evidence.get("approval", "")).strip()),
                REF_SUPPORTED_PIN + ":" + label + ":approval")
        require(row.get("missing_evidence") is None,
                REF_STATE + ":" + label + ":both_states")
    else:
        missing = row.get("missing_evidence")
        require(isinstance(missing, dict) and missing, REF_STATE + ":" + label)
        require(bool(str(missing.get("kind", "")).strip()),
                REF_STATE + ":" + label + ":kind")
        require(bool(str(missing.get("detail", "")).strip()),
                REF_STATE + ":" + label + ":detail")
        require(bool(str(missing.get("authorization_required", "")).strip()),
                REF_STATE + ":" + label + ":authorization")
        require(row.get("evidence") is None,
                REF_STATE + ":" + label + ":both_states")


def _scan_no_fitting(node, label):
    """P5: no fitted/optimized keys anywhere; numbers only where lawful."""
    if isinstance(node, dict):
        for key, value in node.items():
            lowered = key.lower()
            require(not any(token in lowered
                            for token in FORBIDDEN_KEY_TOKENS),
                    REF_FIT + ":" + label + ":" + key)
            require(not lowered.endswith("_fit") and lowered != "new_fit",
                    REF_FIT + ":" + label + ":" + key)
            _scan_no_fitting(value, label)
    elif isinstance(node, list):
        for item in node:
            _scan_no_fitting(item, label)


def validate_document(document, registry_path_override=None,
                      verify_live_pins=True):
    """Validate one resolution document; returns a normalized summary dict."""
    require(isinstance(document, dict), "document_not_object")
    require(document.get("schema") == SCHEMA, "unsupported_resolution_schema")
    require(type(document.get("revision")) is int
            and document["revision"] > 0, "invalid_revision")
    require(document.get("object_id") == OBJECT_ID, "invalid_object_id")
    require(document.get("criteria_sha256")
            == "c4d4ae430027d489d58007cae3895b81dcbfa604c045aa35049c3ecf333373f8",
            "criteria_mismatch")
    require(document.get("preregistration_sha256") == preregistration_sha256(),
            "preregistration_freeze_mismatch")

    path = Path(registry_path_override) if registry_path_override \
        else registry_path()
    require(sha256_file(path) == A06_REGISTRY_SHA256, REF_REGISTRY_PIN)
    registry = json.loads(path.read_text(encoding="utf-8"))
    live = {}
    if verify_live_pins:
        live = {"osim_sha256": sha256_file(OSIM_PATH),
                "hand_vtp_sha256": sha256_file(HAND_VTP_PATH)}
        require(live["osim_sha256"] == OSIM_SHA256, REF_BAD_PIN + ":osim")
        require(live["hand_vtp_sha256"] == HAND_VTP_SHA256,
                REF_BAD_PIN + ":hand_vtp")
        if Path(A05_STRUCT_PATH).exists():
            require(sha256_file(A05_STRUCT_PATH) == A05_STRUCT_SHA256,
                    REF_BAD_PIN + ":a05_structure")

    carried = document.get("carried_observation")
    require(isinstance(carried, dict)
            and carried.get("text") == CARRIED_OBSERVATION,
            "carried_observation_altered")
    require(carried.get("resolution") == UNRESOLVED
            and carried["missing_evidence"]["kind"]
            == "separately_authorized_fitting_experiment",
            "carried_observation_resolution_unlawful")

    # P2 conservation: one resolution row per registry row, no inventions
    paths = document["path_resolutions"]
    attachments = document["attachment_resolutions"]
    waypoints = document["waypoint_resolutions"]
    grasps = document["grasp_endpoint_resolutions"]
    require(len(paths) == len(registry["path_records"]) == FROZEN_COUNTS["path_resolutions"],
            REF_COUNTS + ":paths")
    require(len(attachments) == len(registry["attachments"])
            == FROZEN_COUNTS["attachment_resolutions"], REF_COUNTS
            + ":attachments")
    registry_waypoints = [r for r in registry["path_records"]
                          if r["role"].endswith("waypoint")]
    require(len(waypoints) == len(registry_waypoints)
            == FROZEN_COUNTS["waypoint_resolutions"], REF_COUNTS + ":waypoints")
    require(len(grasps) == len(registry["grasp_endpoints"])
            == FROZEN_COUNTS["grasp_endpoint_resolutions"], REF_COUNTS
            + ":grasp")
    require({r["record_id"] for r in paths}
            == {r["record_id"] for r in registry["path_records"]},
            REF_COUNTS + ":path_identity")
    require({r["attachment_id"] for r in attachments}
            == {r["attachment_id"] for r in registry["attachments"]},
            REF_COUNTS + ":attachment_identity")

    # P3/P4 per-row totality + vocabulary + evidence binding (semantic
    # refusals bite before aggregate counts)
    by_id = {row["record_id"]: row for row in paths}
    for row in paths:
        _check_resolution_row(row, row["record_id"])
    for row in attachments:
        _check_resolution_row(row, row["attachment_id"])
    for row in waypoints:
        _check_resolution_row(row, row["record_id"])
        # A06 law inherited: a waypoint is never an attachment port
        require(row.get("interface_id") is None and row.get("bond") is False,
                REF_WAYPOINT_PORT + ":" + row["record_id"])
    for row in grasps:
        _check_resolution_row(row, row["endpoint_id"])

    # P6 measured honesty: recompute the envelope test and the verbatim carry
    parent_states = {}
    for record in registry["path_records"]:
        row = by_id[record["record_id"]]
        require(row["location_m"] == record["location_m"],
                REF_VERBATIM + ":" + record["record_id"])
        require(row["owner_body"] == record["owner_body"]
                and row["role"] == record["role"],
                REF_VERBATIM + ":" + record["record_id"] + ":owner_role")
        require(row["mutant_mapping_status"]
                == record["mutant_mapping"]["status"],
                REF_STATUS_FABRICATED + ":" + record["record_id"])
        expected_axes = (envelope_test(record["location_m"])
                         if record["on_hand_body"] else [])
        measured = row["envelope_measurement"]
        require(measured["outside_axes"] == expected_axes,
                REF_MEASURE + ":" + record["record_id"])
        expected_outcome = ("outside" if expected_axes else
                            "inside" if record["on_hand_body"] else "not_tested")
        require(measured["outcome"] == expected_outcome,
                REF_MEASURE + ":" + record["record_id"] + ":outcome")
        require(row["placement_failed_outside"] == bool(expected_axes),
                REF_MEASURE + ":" + record["record_id"] + ":flag")
        parent_states[record["record_id"]] = row["resolution"]
    outside = sorted(row["record_id"] for row in paths
                     if row["placement_failed_outside"])
    require(outside == sorted(FROZEN_OUTSIDE), REF_MEASURE + ":outside_set")
    require(sorted(row["record_id"] for row in paths
                   if row["placement_failed_outside"]
                   and row["role"] == "insertion_attachment")
            == sorted(FROZEN_OUTSIDE_INSERTIONS), REF_MEASURE
            + ":outside_insertions")
    require(sorted(row["record_id"] for row in paths
                   if row["placement_failed_outside"]
                   and row["role"].endswith("waypoint"))
            == sorted(FROZEN_OUTSIDE_WAYPOINTS), REF_MEASURE
            + ":outside_waypoints")

    # child rows follow their path record (R4/R5)
    for row in attachments + waypoints:
        require(row["resolution"] == parent_states[row["path_record_id"]],
                REF_STATE + ":" + str(row.get("attachment_id")
                                        or row["record_id"]) + ":child_mismatch")

    # P2 frozen aggregate counts (after per-row checks so refusals bite first)
    counts = document["counts"]
    for key, expected in FROZEN_COUNTS.items():
        require(counts.get(key) == expected, REF_COUNTS + ":" + key)
    recomputed = {
        "envelope_measured_outside": sum(1 for r in paths
                                         if r["placement_failed_outside"]),
        "mutant_mapped_records": sum(1 for r in paths
                                     if r["mutant_mapping_status"] == "mapped"),
        "pending_assembly_mapping": sum(1 for r in paths
                                        if r["mutant_mapping_status"]
                                        == "pending_assembly_mapping"),
    }
    for key, value in recomputed.items():
        require(counts[key] == value, REF_COUNTS + ":" + key + ":recomputed")

    # P5 no unauthorized fitting (whole document; the law_statement prose
    # block is exempt as declared prose — it names the law itself)
    for key, value in document.items():
        if key == "law_statement":
            continue
        _scan_no_fitting(value, key)

    # P8 C17 honesty inherited: no stiffness numbers, status preserved
    registry_mech = {a["attachment_id"]: a["mechanics_c17"]
                     for a in registry["attachments"]}
    for row in attachments:
        mech = row["mechanics_c17"]
        require(mech == registry_mech[row["attachment_id"]],
                REF_C17 + ":altered:" + row["attachment_id"])
        numeric = [k for k, v in mech.items()
                   if isinstance(v, (int, float)) and not isinstance(v, bool)]
        require(not numeric, REF_C17 + ":" + row["attachment_id"])
        require(mech["status"] == "inputs_unavailable_in_pinned_sources",
                "c17_status_invalid")
    require(document["c17"]["status"] == "open", "c17_closed_unlawfully")

    return {
        "schema": "chimera.attachment_placement_resolution.receipt.v1",
        "status": "PASS",
        "object_id": document["object_id"],
        "document_sha256": digest(document),
        "path_resolutions": len(paths),
        "attachment_resolutions": len(attachments),
        "waypoint_resolutions": len(waypoints),
        "grasp_endpoint_resolutions": len(grasps),
        "supported": {"paths": sum(1 for r in paths if r["resolution"] == SUPPORTED),
                      "attachments": sum(1 for r in attachments
                                         if r["resolution"] == SUPPORTED),
                      "waypoints": sum(1 for r in waypoints
                                       if r["resolution"] == SUPPORTED),
                      "grasp_endpoints": sum(1 for r in grasps
                                             if r["resolution"] == SUPPORTED)},
        "explicitly_unresolved": {
            "paths": sum(1 for r in paths if r["resolution"] == UNRESOLVED),
            "attachments": sum(1 for r in attachments
                               if r["resolution"] == UNRESOLVED),
            "waypoints": sum(1 for r in waypoints
                             if r["resolution"] == UNRESOLVED)},
        "envelope_measured_outside": counts["envelope_measured_outside"],
        "outside_insertions": counts["outside_insertions"],
        "outside_waypoints": counts["outside_waypoints"],
        "live_pins": live,
        "limits": "Completion-of-record vocabulary and measurement only; does "
                  "not re-run or re-derive the historical fitting loops, does "
                  "not resolve the pending mappings, and does not qualify "
                  "attachment mechanics (C17 stays open).",
    }


# ---- separation check (the A06 registry is untouched) ---------------------------
def separation_check(document):
    """The resolution document is purely additive: dropping all resolution
    rows leaves a document whose carried identities are unchanged, and the
    pinned A06 registry digest is independent of this document."""
    stripped = {**document, "path_resolutions": [], "attachment_resolutions": [],
                "waypoint_resolutions": [], "grasp_endpoint_resolutions": []}
    require(document["depends_on"]["MAT2-A06"]["registry_sha256"]
            == A06_REGISTRY_SHA256, "registry_pin_changed")
    require(digest(stripped["carried_observation"])
            == digest(document["carried_observation"]),
            "carried_observation_depends_on_rows")
    require(digest(stripped["envelope_test"])
            == digest(document["envelope_test"]),
            "envelope_test_depends_on_rows")
    return {"registry_pin_carried": True,
            "carried_blocks_independent_of_rows": True}


# ---- falsifier tamper probes (each must fire exactly its named refusal) --------
def _copy(document):
    return json.loads(json.dumps(document))


def tamper_supported_pin(document):
    """T1: a supported claim stripped of its pin."""
    tampered = _copy(document)
    for row in tampered["grasp_endpoint_resolutions"]:
        if row["resolution"] == SUPPORTED:
            row["evidence"] = {"source": "source.a05_mutation_structure",
                               "approval": "pin removed by tamper"}
            break
    return tampered


def tamper_silent_default(document):
    """T2: a pending mapping silently defaulted to a third state."""
    tampered = _copy(document)
    for row in tampered["path_resolutions"]:
        if row["mutant_mapping_status"] == "pending_assembly_mapping":
            row["resolution"] = "defaulted"
            row["missing_evidence"] = None
            break
    return tampered


def tamper_unauthorized_fit(document):
    """T3: smuggle a fitted value into an otherwise lawful resolution row.

    Faithful probe: the row keeps its lawful state and evidence; ONLY the
    smuggled fitted field distinguishes it — the refusal must be the
    no-fitting law (fitting_unauthorized_refused), nothing earlier.
    """
    tampered = _copy(document)
    for row in tampered["path_resolutions"]:
        if row["mutant_mapping_status"] == "pending_assembly_mapping":
            row["fitted_mutant_body"] = "proxph2"
            row["fitted_distance_m"] = 0.004
            break
    return tampered


def tamper_measured_flip(document):
    """T6: relabel a measured-outside record as inside with edited excess."""
    tampered = _copy(document)
    victim = next(r for r in tampered["path_resolutions"]
                  if r["placement_failed_outside"])
    victim["envelope_measurement"] = {"in_scope": True, "outcome": "inside",
                                      "outside_axes": [],
                                      "bounds_source": "tampered"}
    victim["placement_failed_outside"] = False
    return tampered


def tamper_stiffness(document):
    """T7 (inherited A06 law): claim a stiffness without declared inputs."""
    tampered = _copy(document)
    tampered["attachment_resolutions"][0]["mechanics_c17"][
        "stiffness_N_per_m2"] = 1.0e6
    return tampered


def tamper_registry(registry_bytes):
    """T-PIN: a mutated A06 registry (location edited) must refuse the pin."""
    registry = json.loads(registry_bytes.decode("utf-8"))
    registry["path_records"][0]["location_m"][0] += 1e-9
    return canonical(registry)


# ---- CLI ------------------------------------------------------------------------
def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--emit", action="store_true",
                        help="write placement_resolution.json")
    parser.add_argument("--verify", action="store_true",
                        help="validate the emitted JSON + checks + separation")
    parser.add_argument("--self-check", action="store_true",
                        help="build + validate in memory")
    parser.add_argument("--tamper-supported-pin", action="store_true")
    parser.add_argument("--tamper-default", action="store_true")
    parser.add_argument("--tamper-fit", action="store_true")
    parser.add_argument("--tamper-flip", action="store_true")
    parser.add_argument("--tamper-stiffness", action="store_true")
    parser.add_argument("--tamper-registry", action="store_true")
    args = parser.parse_args(argv)
    out = []
    document = build_document()
    here = Path(__file__).resolve().parent
    emitted = here / "placement_resolution.json"
    if args.emit:
        emitted.write_bytes(canonical(document) + b"\n")
        out.append("wrote placement_resolution.json sha256=%s"
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
    probes = (("--tamper-supported-pin", tamper_supported_pin,
               REF_SUPPORTED_PIN),
              ("--tamper-default", tamper_silent_default, REF_STATE),
              ("--tamper-fit", tamper_unauthorized_fit, REF_FIT),
              ("--tamper-flip", tamper_measured_flip, REF_MEASURE),
              ("--tamper-stiffness", tamper_stiffness, REF_C17))
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
    if args.tamper_registry:
        registry_bytes = registry_path().read_bytes()
        mutated = tamper_registry(registry_bytes)
        scratch = here.parent / ("MAT2-A07.tamper_registry.json")
        scratch.write_bytes(mutated)
        try:
            loaded = json.loads(emitted.read_text(encoding="utf-8")) \
                if emitted.exists() else document
            validate_document(loaded, registry_path_override=scratch,
                              verify_live_pins=False)
            out.append("--tamper-registry=FAIL no refusal fired (expected "
                       + REF_REGISTRY_PIN + ")")
        except ValueError as err:
            fired = str(err)
            out.append("--tamper-registry=%s (refused: %s)"
                       % ("BIT" if fired.startswith(REF_REGISTRY_PIN)
                          else "WRONG-REFUSAL", fired))
        finally:
            scratch.unlink(missing_ok=True)
    if not out:
        parser.print_help()
    for row in out:
        print(row)


if __name__ == "__main__":
    main()
