"""M10 — STATIC consumption validator for ``chimera.rigid_body_mass_export.v1``.

Enforces the numbered rule set R1-R16 preregistered in
``PREREGISTRATION.md`` (this directory) against the contract
``Chimera/docs/matter/rigid_body_mass_export_consumption_contract_v1_proposal.md``
(proposal v0.9), under the STRICTEST reading of the five Astra-reserved
decisions (D1-D5): reject partial, no recombination, external flat frames,
no source masses, no readiness.

STATIC ONLY: this module never assembles, never mutates state, never runs
dynamics, and provides no readiness-promotion or composite-recombination path.
It only ACCEPTS/REJECTS report bodies for assembly ELIGIBILITY and reports
reasons. Every rule failure is preserved and enumerated.

Reuse: the existing read-only reader (``tools/material_volume_body_export_reader.py``)
is imported via ``sys.path`` with bytecode writing disabled and run as an
independent structural cross-check (R0). Hash recomputation mirrors the
exporter's ``_canonical_hash`` (canonical JSON, no trailing newline).

CLI:
    python rigid_body_mass_consumption_validator.py REPORT.json \
        [--admission-report ADMISSION.json] [--verify-aggregate] [--indent N]

Exit classes (M06-H04, decided): 0 = accepted static validation; 2 = named
input/status refusal (a REJECT verdict with reasons enumerated, an unreadable or
invalid input document, or a CLI usage error); 1 = unexpected internal failure
only. Compatibility: the original M10 tool (campaign artifact,
agents/M10_validator/) keeps its 0/1/2 = accept/reject/could-not-evaluate
mapping; THIS promoted tool carries the decided mapping.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # never write __pycache__ into the read-only tools tree

import argparse
import hashlib
import json
import math
import os
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

# --------------------------------------------------------------------------
# Frozen constants (PREREGISTRATION.md, rules R1-R16)
# --------------------------------------------------------------------------
CONTRACT_SCHEMA_VERSION = "chimera.rigid_body_mass_export.v1"
ROOT_EXPORT_STATUSES = ("complete", "partial", "blocked", "unsupported", "refused")
BODY_EXPORTED = "exported"
BODY_NOT_EXPORTED = "not_exported"
ADMISSION_ADMISSIBLE = "validation_only_admissible"
MASS_SOURCE_KIND = "reconstructed_material_volume"
MASS_AUTHORITY = "reconstructed_tissue_mass"
INERTIA_BASIS = "authored_body_frame"

SHA256_HEX_RE = re.compile(r"\A[0-9a-f]{64}\Z")
ORTHONORMALITY_TOL = 1.0e-12  # matches reader precedent; FC coupon error <= 9.4e-16

# R12 readiness-claim key patterns (case-insensitive substrings).
READINESS_CLAIM_PATTERNS = (
    "dynamics_readiness",
    "readiness_claimed",
    "dynamics_ready",
    "assembly_ready",
    "simulation_ready",
)
# R15 reserved recombination/composite field names (D3, strictest).
RECOMBINATION_FIELD_NAMES = (
    "composite_of",
    "composite",
    "is_composite",
    "recombined",
    "recombination",
    "parallel_axis_applied",
    "aggregated_from",
    "combined_from",
)
# R16 reserved parent-frame lineage field names (D4, strictest).
LINEAGE_FIELD_NAMES = (
    "frame_lineage",
    "parent_frame",
    "composed_from",
    "frame_lineage_schema",
    "lineage",
)

ROOT_REQUIRED_FLAGS = (
    # (field, required value) -- fixed v1 semantics, safety-relevant ones false.
    ("validation_only", True),
    ("dynamics_readiness_claimed", False),
    ("physical_state_mutated", False),
    ("production_wired", False),
    ("anatomical_completeness_certified", False),
    ("surface_mass_overlay_generated", False),
    ("source_effective_segment_payloads_consumed", False),
)
PROVENANCE_OVERLAY_FLAGS = (
    ("source_effective_segment_payloads_consumed", False),
    ("surface_mass_overlay_consumed", False),
    ("surface_mass_overlay_generated", False),
)

# --------------------------------------------------------------------------
# Reader reuse (R0 cross-check) -- read-only import, no bytecode written
# --------------------------------------------------------------------------
def _tools_dir() -> Path:
    override = os.environ.get("CHIMERA_TOOLS_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[3] / "tools"


_READER = None
_EXPORTER = None
READER_AVAILABLE = False
_READER_IMPORT_NOTE = ""
try:
    _candidate = str(_tools_dir())
    if _candidate not in sys.path:
        sys.path.insert(0, _candidate)
    import material_volume_body_export_reader as _reader_module  # noqa: E402

    _READER = _reader_module
    _EXPORTER = _reader_module.exporter
    READER_AVAILABLE = True
except Exception as error:  # pragma: no cover - only when repo layout changes
    _READER_IMPORT_NOTE = f"reader cross-check unavailable: {type(error).__name__}: {error}"


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def canonical_hash(document: Any) -> str | None:
    """Mirror of ``material_volume_body_export._canonical_hash`` (no trailing newline)."""
    try:
        serialized = json.dumps(document, sort_keys=True, separators=(",", ":"),
                                ensure_ascii=True, allow_nan=False)
    except (TypeError, ValueError, OverflowError):
        return None
    return hashlib.sha256(serialized.encode("ascii")).hexdigest()


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_mapping(value: Any) -> bool:
    return isinstance(value, Mapping)


def iter_entries(node: Any, path: str = "$"):
    """Yield ``(path, key, value)`` for every mapping entry at any depth."""
    if isinstance(node, Mapping):
        for key, value in node.items():
            entry_path = f"{path}.{key}"
            yield entry_path, key, value
            yield from iter_entries(value, entry_path)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            entry_path = f"{path}[{index}]"
            yield from iter_entries(value, entry_path)


class _FailureLog:
    def __init__(self) -> None:
        self.failures: list[dict] = []

    def add(self, rule: str, reason: str, detail: str, location: str = "$") -> None:
        self.failures.append({"rule": rule, "reason": reason, "detail": detail,
                              "location": location})

    def extend(self, other: "list[dict]") -> None:
        self.failures.extend(other)


def _require_mapping(log: _FailureLog, value: Any, rule: str, reason: str,
                     location: str) -> bool:
    if not _is_mapping(value):
        log.add(rule, reason, "expected a JSON object", location)
        return False
    return True


def _hex_field_ok(value: Any) -> bool:
    return isinstance(value, str) and SHA256_HEX_RE.match(value) is not None


# --------------------------------------------------------------------------
# R1 -- report identity and strict parse
# --------------------------------------------------------------------------
def rule_r1_identity(report: Any, log: _FailureLog) -> bool:
    if not _is_mapping(report):
        log.add("R1", "not_an_object", "export report must be a JSON object")
        return False
    version = report.get("schema_version")
    if version != CONTRACT_SCHEMA_VERSION:
        log.add("R1", "bad_schema_version",
                f"schema_version must be {CONTRACT_SCHEMA_VERSION!r}, got {version!r}")
    groups = report.get("body_groups")
    if not isinstance(groups, list):
        log.add("R1", "body_groups_not_a_list", "body_groups must be an array")
    elif report.get("export_status") == "complete" and len(groups) == 0:
        log.add("R1", "complete_report_has_no_bodies",
                "a complete report must contain at least one body record")
    # W6-RAW (MV-B3-1, decided): the reader's summarize_export_report output is a
    # display projection; consumption validation reads the FULL raw report. Refuse
    # a summary-shaped document BY NAME instead of only a generic shape error.
    # The summary API itself is never imported, extended, or reinterpreted here.
    if (isinstance(report.get("bodies"), list)
            and not isinstance(report.get("body_groups"), list)
            and version == CONTRACT_SCHEMA_VERSION):
        log.add("R1", "summary_projection_is_not_a_consumption_document",
                "MV-B3-1: this document carries its body records under 'bodies', the "
                "key layout of the reader's summarize_export_report display "
                "projection; consumption validation reads the full raw report "
                "(contract §1), never the summary API", "$")
    return _is_mapping(report) and isinstance(groups, list)


# --------------------------------------------------------------------------
# R2 -- root export_status gate (exhaustive, strictest per status)
# --------------------------------------------------------------------------
def rule_r2_root_status(report: Mapping, log: _FailureLog) -> str | None:
    status = report.get("export_status")
    if not isinstance(status, str):
        log.add("R2", "missing_or_nonstring_export_status",
                f"root export_status must be one of {ROOT_EXPORT_STATUSES}")
        return None
    if status not in ROOT_EXPORT_STATUSES:
        log.add("R2", "unknown_export_status",
                f"{status!r} is outside the exhaustive v1 status set")
        return status
    if status == "partial":
        log.add("R2", "partial_rejected",
                "contract §2: 'Silent partial assembly FORBIDDEN. Default: REJECT.' "
                "[D2 strictest: always rejected; no explicit-subset path exists]")
    elif status == "blocked":
        log.add("R2", "blocked_rejected",
                "contract §2: 'REJECT for dynamics consumption' (CON-4)")
    elif status == "unsupported":
        log.add("R2", "unsupported_rejected",
                "contract §2: 'REJECT. Source masses are never consumed' (CON-5) "
                "[D5 strictest]")
    elif status == "refused":
        log.add("R2", "refused_rejected",
                "contract §2/CON-6: 'refused reports are terminal'")
    return status


# --------------------------------------------------------------------------
# R3 -- admission_status exact value
# --------------------------------------------------------------------------
def rule_r3_admission_status(report: Mapping, log: _FailureLog) -> None:
    for location, container in (("$", report),) + tuple(
            (f"$.body_groups[{i}]", row)
            for i, row in enumerate(report.get("body_groups", []) or [])
            if _is_mapping(row)):
        value = container.get("admission_status")
        if value != ADMISSION_ADMISSIBLE:
            log.add("R3", "admission_status_not_admissible",
                    f"CON-13: admission_status must be exactly "
                    f"{ADMISSION_ADMISSIBLE!r} (case-sensitive), got {value!r}",
                    location)


# --------------------------------------------------------------------------
# R4 -- hash binding
# --------------------------------------------------------------------------
def _check_hash_field(log: _FailureLog, container: Mapping, field: str, location: str,
                      required: bool) -> None:
    if field not in container:
        if required:
            log.add("R4", "hash_binding_missing", f"{field} is absent", location)
        return
    value = container.get(field)
    if not _hex_field_ok(value):
        log.add("R4", "hash_binding_malformed",
                f"{field} must be 64 lowercase hex characters, got {value!r}", location)


def rule_r4_hash_binding(report: Mapping, log: _FailureLog,
                         admission_report: Any = None) -> None:
    status = report.get("export_status")
    complete = status == "complete"
    _check_hash_field(log, report, "admission_report_sha256", "$", required=True)
    hashes = report.get("input_hashes")
    if not _is_mapping(hashes):
        log.add("R4", "input_hashes_missing_or_malformed",
                "root input_hashes must be an object", "$")
    else:
        if hashes.get("algorithm") != "sha256":
            log.add("R4", "input_hashes_algorithm",
                    "input_hashes.algorithm must be 'sha256'", "$")
        for field in ("manifest_sha256", "partition_sha256", "body_groups_sha256"):
            value = hashes.get(field)
            if value is None and not complete:
                continue  # refusal-shaped reports may carry null anchors; R2 rejects them
            if not _hex_field_ok(value):
                log.add("R4", "input_hash_malformed",
                        f"input_hashes.{field} must be 64 lowercase hex, got {value!r}", "$")
    groups = report.get("body_groups")
    root_hash = report.get("admission_report_sha256")
    if isinstance(groups, list):
        for index, row in enumerate(groups):
            location = f"$.body_groups[{index}]"
            if not _is_mapping(row):
                continue
            _check_hash_field(log, row, "admission_report_sha256", location, required=True)
            if complete:
                body_hash = row.get("admission_report_sha256")
                if (_hex_field_ok(root_hash) and _hex_field_ok(body_hash)
                        and body_hash != root_hash):
                    log.add("R4", "hash_binding_mismatch",
                            "body admission_report_sha256 differs from the root binding "
                            "(CON-13 tamper signal)", location)
    # Optional recomputation -- only possible when the admission document is supplied.
    if admission_report is not None:
        recorded = report.get("admission_report_sha256")
        recomputed = canonical_hash(admission_report)
        if recomputed is None:
            log.add("R4", "admission_document_unserializable",
                    "supplied admission report cannot be canonicalized", "$")
        elif recorded != recomputed:
            log.add("R4", "admission_hash_recomputation_mismatch",
                    f"sha256(supplied admission report)={recomputed} != recorded "
                    f"{recorded!r} (CON-13 corruption/tamper refusal)", "$")


# --------------------------------------------------------------------------
# R5 -- per-body consumable status
# --------------------------------------------------------------------------
def rule_r5_body_status(report: Mapping, root_status: str | None,
                        log: _FailureLog) -> None:
    groups = report.get("body_groups")
    if not isinstance(groups, list):
        return
    for index, row in enumerate(groups):
        location = f"$.body_groups[{index}]"
        if not _is_mapping(row):
            continue
        status = row.get("export_status")
        if status == BODY_EXPORTED:
            if row.get("mass_properties") is None:
                log.add("R5", "exported_without_properties",
                        "CON-1: an exported body must carry non-null mass_properties",
                        location)
        elif status == BODY_NOT_EXPORTED:
            log.add("R5", "not_exported_is_diagnostic",
                    "CON-4/CON-7: not_exported bodies are diagnostics, never inputs; "
                    "no placeholder bodies, no estimated masses", location)
            if row.get("mass_properties") is not None:
                log.add("R5", "placeholder_mass_on_not_exported",
                        "§2: 'no placeholder bodies, no estimated masses' — a "
                        "not_exported body carries mass_properties", location)
            codes = row.get("reason_codes")
            if not isinstance(codes, list):
                log.add("R5", "not_exported_without_reason_codes",
                        "§2: not_exported bodies must carry reason_codes", location)
        else:
            log.add("R5", "unknown_body_export_status",
                    f"per-body export_status {status!r} is outside "
                    f"{{'exported', 'not_exported'}}", location)
    if root_status == "complete":
        for index, row in enumerate(groups):
            if _is_mapping(row) and row.get("export_status") != BODY_EXPORTED:
                log.add("R5", "complete_report_contains_not_exported_body",
                        "§2: root 'complete' means 'all bodies exported'; a "
                        f"non-exported body contradicts it",
                        f"$.body_groups[{index}]")


# --------------------------------------------------------------------------
# R6/R7/R8 -- mass, volume, center_of_mass authority fields
# --------------------------------------------------------------------------
def _vector3(log: _FailureLog, value: Any, rule: str, reason: str, location: str) -> None:
    if not (isinstance(value, list) and len(value) == 3
            and all(_is_number(v) for v in value)):
        log.add(rule, reason, "expected exactly 3 finite numbers", location)
        return
    if not all(math.isfinite(float(v)) for v in value):
        log.add(rule, reason, "vector contains a non-finite number", location)


def rule_r6_mass(props: Mapping, log: _FailureLog, location: str) -> None:
    mass = props.get("mass")
    if not _require_mapping(log, mass, "R6", "mass_field_missing", f"{location}.mass"):
        return
    value = mass.get("value")
    if not _is_number(value) or not math.isfinite(float(value)):
        log.add("R6", "mass_value_invalid", "mass.value must be a finite number", f"{location}.mass")
    elif float(value) <= 0.0:
        log.add("R6", "mass_not_positive", "authoritative mass must be > 0", f"{location}.mass")
    if mass.get("unit") != "kg":
        log.add("R6", "mass_unit_not_kg", f"CON-11: mass.unit must be 'kg', got "
                f"{mass.get('unit')!r}", f"{location}.mass")
    if mass.get("coordinate_frame") != "frame_invariant":
        log.add("R6", "mass_frame_not_invariant",
                "mass.coordinate_frame must be 'frame_invariant'", f"{location}.mass")
    if mass.get("frame_invariant") is not True:
        log.add("R6", "mass_frame_invariant_flag",
                "mass.frame_invariant must be exactly true", f"{location}.mass")


def rule_r7_volume(props: Mapping, log: _FailureLog, location: str) -> None:
    volume = props.get("volume")
    if not _require_mapping(log, volume, "R7", "volume_field_missing", f"{location}.volume"):
        return
    value = volume.get("value")
    if not _is_number(value) or not math.isfinite(float(value)) or float(value) <= 0.0:
        log.add("R7", "volume_value_invalid",
                "volume.value must be a finite positive number", f"{location}.volume")
    if volume.get("unit") != "m^3":
        log.add("R7", "volume_unit_not_m3",
                f"volume.unit must be 'm^3', got {volume.get('unit')!r}", f"{location}.volume")
    if volume.get("frame_invariant") is not True:
        log.add("R7", "volume_frame_invariant_flag",
                "volume.frame_invariant must be exactly true", f"{location}.volume")


def rule_r8_center_of_mass(props: Mapping, frame_id: Any, log: _FailureLog,
                           location: str) -> None:
    com = props.get("center_of_mass")
    if not _require_mapping(log, com, "R8", "center_of_mass_missing",
                            f"{location}.center_of_mass"):
        return
    _vector3(log, com.get("value"), "R8", "com_value_invalid",
             f"{location}.center_of_mass")
    if com.get("unit") != "m":
        log.add("R8", "com_unit_not_m", f"COM.unit must be 'm', got {com.get('unit')!r}",
                f"{location}.center_of_mass")
    if frame_id is not None and com.get("coordinate_frame") != frame_id:
        log.add("R8", "com_frame_mismatch",
                f"CON-11: COM must be expressed in frame_id {frame_id!r}, got "
                f"{com.get('coordinate_frame')!r}", f"{location}.center_of_mass")


# --------------------------------------------------------------------------
# R9 -- full-tensor integrity
# --------------------------------------------------------------------------
def rule_r9_inertia(props: Mapping, frame_id: Any, log: _FailureLog,
                    location: str) -> None:
    inertia = props.get("inertia_tensor_about_com")
    where = f"{location}.inertia_tensor_about_com"
    if not _require_mapping(log, inertia, "R9", "inertia_field_missing", where):
        return
    value = inertia.get("value")
    shape_ok = (isinstance(value, list) and len(value) == 3
                and all(isinstance(row, list) and len(row) == 3
                        and all(_is_number(v) for v in row) for row in value))
    if not shape_ok:
        log.add("R9", "tensor_not_3x3",
                "CON-9: all 9 entries must be retained (value[3][3], finite numbers)",
                where)
    else:
        matrix = np.asarray(value, dtype=np.float64)
        if not np.all(np.isfinite(matrix)):
            log.add("R9", "tensor_non_finite", "tensor contains a non-finite entry", where)
        if not np.array_equal(matrix, matrix.T):
            offenders = [(i, j) for i in range(3) for j in range(3)
                         if value[i][j] != value[j][i]]
            log.add("R9", "tensor_not_symmetric",
                    "CON-9: the full symmetric tensor is authoritative; "
                    f"asymmetric entries {offenders} (exact equality required)", where)
    if inertia.get("full_symmetric_tensor") is not True:
        log.add("R9", "full_symmetric_tensor_flag",
                "full_symmetric_tensor must be exactly true", where)
    if inertia.get("off_diagonal_terms_preserved") is not True:
        log.add("R9", "off_diagonal_preserved_flag",
                "CON-9: off_diagonal_terms_preserved must be exactly true "
                "(dropped off-diagonal terms are forbidden)", where)
    if inertia.get("principal_axis_transform_applied") is not False:
        log.add("R9", "principal_axis_transform_flag",
                "CON-9: principal_axis_transform_applied must remain exactly false",
                where)
    if inertia.get("unit") != "kg*m^2":
        log.add("R9", "tensor_unit", f"tensor unit must be 'kg*m^2', got "
                f"{inertia.get('unit')!r}", where)
    if frame_id is not None:
        if inertia.get("coordinate_frame") != frame_id:
            log.add("R9", "tensor_frame_mismatch",
                    f"CON-11: inertia must be expressed in frame_id {frame_id!r}, got "
                    f"{inertia.get('coordinate_frame')!r}", where)
        if "frame_id" in inertia and inertia.get("frame_id") != frame_id:
            log.add("R9", "tensor_frame_id_mismatch",
                    f"inertia.frame_id must equal body_frame.frame_id {frame_id!r}", where)
    if inertia.get("basis") != INERTIA_BASIS:
        log.add("R9", "tensor_basis",
                f"basis must be {INERTIA_BASIS!r}, got {inertia.get('basis')!r}", where)


# --------------------------------------------------------------------------
# R10 -- body frame authority
# --------------------------------------------------------------------------
def rule_r10_body_frame(row: Mapping, log: _FailureLog, location: str) -> Any:
    frame = row.get("body_frame")
    where = f"{location}.body_frame"
    if not _require_mapping(log, frame, "R10", "body_frame_missing", where):
        return None
    frame_id = frame.get("frame_id")
    if not (isinstance(frame_id, str) and frame_id.strip()):
        log.add("R10", "frame_id_invalid", "frame_id must be a non-empty string", where)
    if frame.get("handedness") != "right":
        log.add("R10", "handedness_not_right",
                f"CON-10: right-handed frames only, got {frame.get('handedness')!r}", where)
    if frame.get("coordinate_unit") != "m":
        log.add("R10", "coordinate_unit_not_m",
                f"CON-10: coordinate_unit must be 'm', got "
                f"{frame.get('coordinate_unit')!r}", where)
    domain = frame.get("domain_from_body")
    if not _require_mapping(log, domain, "R10", "domain_from_body_missing",
                            f"{where}.domain_from_body"):
        return frame_id
    rotation = domain.get("rotation")
    rot_ok = (isinstance(rotation, list) and len(rotation) == 3
              and all(isinstance(r, list) and len(r) == 3
                      and all(_is_number(v) for v in r) for r in rotation))
    if not rot_ok:
        log.add("R10", "rotation_not_3x3",
                "domain_from_body.rotation must be value[3][3] finite numbers",
                f"{where}.domain_from_body")
    else:
        matrix = np.asarray(rotation, dtype=np.float64)
        if not np.all(np.isfinite(matrix)):
            log.add("R10", "rotation_non_finite", "rotation contains a non-finite entry",
                    f"{where}.domain_from_body")
        else:
            # CON-10: proper orthonormal AS AUTHORED and NEVER repaired -> refuse.
            gram_error = float(np.max(np.abs(matrix.T @ matrix - np.eye(3))))
            det_error = abs(float(np.linalg.det(matrix)) - 1.0)
            if gram_error > ORTHONORMALITY_TOL or det_error > ORTHONORMALITY_TOL:
                log.add("R10", "rotation_not_proper_orthonormal",
                        f"CON-10: rotation is not proper orthonormal as authored "
                        f"(max|RtR-I|={gram_error:.3e}, |det-1|={det_error:.3e}, "
                        f"tol={ORTHONORMALITY_TOL:.0e}); refusing, never repairing",
                        f"{where}.domain_from_body")
    _vector3(log, domain.get("origin_m"), "R10", "origin_m_invalid",
             f"{where}.domain_from_body")
    return frame_id


# --------------------------------------------------------------------------
# R11 -- ownership verbatim; provenance travels
# --------------------------------------------------------------------------
def rule_r11_ownership(row: Mapping, log: _FailureLog, location: str) -> None:
    owned = row.get("owned_cell_ids")
    if not (isinstance(owned, list) and len(owned) >= 1
            and all(isinstance(c, str) and c.strip() for c in owned)):
        log.add("R11", "owned_cell_ids_invalid",
                "owned_cell_ids must be a non-empty list of non-empty strings", location)
        owned = None
    else:
        if len(set(owned)) != len(owned):
            log.add("R11", "owned_cell_ids_duplicated",
                    "owned_cell_ids entries must be unique", location)
    provenance = row.get("cell_provenance")
    if not isinstance(provenance, list) or not provenance:
        log.add("R11", "provenance_stripped",
                "CON-12: cell_provenance travels with the body; stripping provenance "
                "voids the contract", location)
        provenance = None
    owner_ids: list[str] = []
    if provenance is not None and owned is not None:
        seen: dict[str, str] = {}
        for p_index, prow in enumerate(provenance):
            p_where = f"{location}.cell_provenance[{p_index}]"
            if not _is_mapping(prow):
                log.add("R11", "provenance_row_not_object", "expected an object", p_where)
                continue
            cell_id = prow.get("cell_id")
            owner = prow.get("mass_owner_id")
            if not (isinstance(cell_id, str) and cell_id.strip()):
                log.add("R11", "provenance_cell_id_invalid",
                        "cell_id must be a non-empty string", p_where)
            if not (isinstance(owner, str) and owner.strip()):
                log.add("R11", "provenance_owner_invalid",
                        "CON-8: mass_owner_id must be a non-empty string (verbatim, "
                        "never inferred)", p_where)
            else:
                owner_ids.append(owner)
                if cell_id in seen and seen[cell_id] != owner:
                    log.add("R11", "conflicting_ownership",
                            "§1: one mass owner per cell (exporter-enforced); cell "
                            f"{cell_id!r} claimed by {seen[cell_id]!r} and {owner!r}",
                            p_where)
                seen[cell_id] = owner
            for field in ("region_id", "material_id", "density_source",
                          "density_conditions"):
                if not (isinstance(prow.get(field), str) and prow.get(field).strip()):
                    log.add("R11", "provenance_field_missing",
                            f"{field} must be a non-empty string", p_where)
            density = prow.get("density_kg_m3")
            if not _is_number(density) or not math.isfinite(float(density)) \
                    or float(density) <= 0.0:
                log.add("R11", "provenance_density_invalid",
                        "density_kg_m3 must be a finite positive number", p_where)
        if owned:
            missing = [c for c in owned if c not in seen]
            extra = [c for c in seen if c not in set(owned)]
            if missing:
                log.add("R11", "owned_cell_without_provenance",
                        f"CON-8/CON-12: owned cells {missing} have no provenance row",
                        location)
            if extra:
                log.add("R11", "provenance_cell_not_owned",
                        f"provenance rows for cells {extra} are not in owned_cell_ids",
                        location)
    source = row.get("material_mass_source_provenance")
    if not _require_mapping(log, source, "R11", "source_provenance_missing",
                            f"{location}.material_mass_source_provenance"):
        return
    if source.get("mass_source_kind") != MASS_SOURCE_KIND:
        log.add("R11", "mass_source_kind_wrong",
                f"CON-12: mass_source_kind must be {MASS_SOURCE_KIND!r}, got "
                f"{source.get('mass_source_kind')!r}",
                f"{location}.material_mass_source_provenance")
    if source.get("mass_authority") != MASS_AUTHORITY:
        log.add("R11", "mass_authority_not_reconstructed",
                f"mass_authority must be {MASS_AUTHORITY!r}; any other authority "
                f"(e.g. source-effective segment mass) is rejected [D5 strictest], got "
                f"{source.get('mass_authority')!r}",
                f"{location}.material_mass_source_provenance")
    recorded_owners = source.get("mass_owner_ids")
    if not (isinstance(recorded_owners, list)
            and all(isinstance(o, str) and o.strip() for o in recorded_owners)):
        log.add("R11", "mass_owner_ids_invalid",
                "mass_owner_ids must be a list of non-empty strings",
                f"{location}.material_mass_source_provenance")
    elif provenance is not None and owner_ids and set(recorded_owners) != set(owner_ids):
        log.add("R11", "mass_owner_ids_mismatch",
                f"CON-8: mass_owner_ids {sorted(set(recorded_owners))} must equal the "
                f"verbatim provenance owners {sorted(set(owner_ids))}",
                f"{location}.material_mass_source_provenance")
    if not (isinstance(source.get("integration_model"), str)
            and source.get("integration_model").strip()):
        log.add("R11", "integration_model_missing",
                "integration_model must be a non-empty string",
                f"{location}.material_mass_source_provenance")
    records = source.get("material_records")
    if not (isinstance(records, list) and records
            and all(_is_mapping(r) and isinstance(r.get("material_id"), str)
                    and r.get("material_id").strip() for r in records)):
        log.add("R11", "material_records_invalid",
                "material_records must be a non-empty list of records with material_id",
                f"{location}.material_mass_source_provenance")
    for field, required in PROVENANCE_OVERLAY_FLAGS:
        if source.get(field) is not required:
            log.add("R11", "provenance_overlay_flag",
                    f"{field} must be exactly {required!r} in v1 "
                    f"(got {source.get(field)!r})",
                    f"{location}.material_mass_source_provenance")


# --------------------------------------------------------------------------
# R12 -- readiness prohibition (CON-14, D1)
# --------------------------------------------------------------------------
def rule_r12_readiness(report: Mapping, log: _FailureLog) -> None:
    if report.get("dynamics_readiness_claimed") is not False:
        log.add("R12", "root_readiness_flag_not_false",
                f"CON-14: root dynamics_readiness_claimed must be exactly false, got "
                f"{report.get('dynamics_readiness_claimed')!r}")
    for path, key, value in iter_entries(report):
        lowered = key.lower() if isinstance(key, str) else ""
        if not lowered:
            continue
        if any(pattern in lowered for pattern in READINESS_CLAIM_PATTERNS) \
                and value is not False and value is not None:
            log.add("R12", "readiness_claim_found",
                    f"CON-14 [D1 strictest]: readiness claim {key!r}={value!r} found in a "
                    f"nested field; no field combination may be read as readiness", path)


# --------------------------------------------------------------------------
# R13 -- fixed v1 safety flags
# --------------------------------------------------------------------------
def rule_r13_safety_flags(report: Mapping, log: _FailureLog) -> None:
    for field, required in ROOT_REQUIRED_FLAGS:
        if field not in report:
            log.add("R13", "safety_flag_missing",
                    f"§1: flag {field!r} has fixed v1 semantics and must be present")
        elif report.get(field) is not required:
            log.add("R13", "safety_flag_not_false" if required is False
                    else "safety_flag_invalid",
                    f"§1: flag {field!r} must be exactly {required!r} in v1 "
                    f"(got {report.get(field)!r})")
    authority = report.get("mass_authority")
    if authority is not None and authority != MASS_AUTHORITY:
        log.add("R13", "root_mass_authority_not_reconstructed",
                f"root mass_authority must be {MASS_AUTHORITY!r} [D5 strictest], got "
                f"{authority!r}")
    codes = report.get("reason_codes")
    if not isinstance(codes, list):
        log.add("R13", "root_reason_codes_missing",
                "§1: root reason_codes (per-record disposition) must be a list")


# --------------------------------------------------------------------------
# R14 -- unassigned cells surfaced and consistent (CON-3/7, D2)
# --------------------------------------------------------------------------
def rule_r14_unassigned(report: Mapping, root_status: str | None,
                        log: _FailureLog) -> None:
    ids = report.get("unassigned_cell_ids")
    rows = report.get("unassigned_cells")
    flag = report.get("all_supplied_cells_assigned")
    if not isinstance(ids, list):
        log.add("R14", "unassigned_cell_ids_missing",
                "§1: root unassigned_cell_ids must be a list")
    if not isinstance(rows, list):
        log.add("R14", "unassigned_cells_missing",
                "§1: root unassigned_cells must be a list")
    if not isinstance(flag, bool):
        log.add("R14", "all_supplied_cells_assigned_missing",
                "§1: root all_supplied_cells_assigned must be a boolean")
    if root_status == "complete":
        if isinstance(ids, list) and ids:
            log.add("R14", "complete_with_unassigned_cells",
                    "CON-3/CON-7: root 'complete' contradicts unassigned_cell_ids "
                    f"{ids}; unassigned cells are surfaced gaps, never merged or dropped")
        if isinstance(rows, list) and rows:
            log.add("R14", "complete_with_unassigned_rows",
                    f"CON-3/CON-7: unassigned_cells {rows} contradict root 'complete'")
        if flag is False:
            log.add("R14", "complete_with_unassigned_flag",
                    "all_supplied_cells_assigned=false contradicts root 'complete'")


# --------------------------------------------------------------------------
# R15 -- no recombination / no runtime wiring (CON-15, D3)
# --------------------------------------------------------------------------
def rule_r15_no_recombination(report: Mapping, log: _FailureLog) -> None:
    for path, key, _value in iter_entries(report):
        if isinstance(key, str) and key.lower() in RECOMBINATION_FIELD_NAMES:
            log.add("R15", "recombination_claim_found",
                    f"CON-15/§5 [D3 strictest]: recombination field {key!r} present; "
                    f"composite recombination is not approved in v1 and this validator "
                    f"performs no composite math", path)


# --------------------------------------------------------------------------
# R16 -- v1 flat-frame purity, no lineage schema (CON-15/D4)
# --------------------------------------------------------------------------
def rule_r16_no_lineage(report: Mapping, log: _FailureLog) -> None:
    for path, key, _value in iter_entries(report):
        if isinstance(key, str) and key.lower() in LINEAGE_FIELD_NAMES:
            log.add("R16", "lineage_field_found",
                    f"CON-15/§5 [D4 strictest]: lineage field {key!r} present; the v2 "
                    f"lineage schema is not invented in v1", path)


# --------------------------------------------------------------------------
# R0 -- reader cross-check (reuse of the existing read-only reader)
# --------------------------------------------------------------------------
def rule_r0_reader_cross_check(report: Any, log: _FailureLog) -> dict:
    if not READER_AVAILABLE:
        return {"ran": False, "note": _READER_IMPORT_NOTE}
    try:
        _READER.summarize_export_report(report)
    except _EXPORTER.ExportInputError as error:
        log.add("R0", f"reader_{error.reason}", error.detail)
        return {"ran": True, "reader_verdict": "reject",
                "reason": error.reason, "detail": error.detail}
    return {"ran": True, "reader_verdict": "pass"}


# --------------------------------------------------------------------------
# MV-O1 (decided) -- admission-hash scope documentation + separate full-report
# identity (contract §6). A blocked body's hash covers a REDUCED object; it is
# never called a full-report hash, and full-report identity is verified
# separately at the handoff.
# --------------------------------------------------------------------------
ADMISSION_HASH_SCOPES_RULE = (
    "MV-O1 (decided): document precisely which reduced object a blocked-body hash "
    "covers; never call it a full-report hash; verify full-report identity "
    "separately at the handoff (contract §6 identity table)."
)
SCOPE_ADMISSION_DOCUMENT = "admission_report_document"
SCOPE_REDUCED_BLOCK_RECORD = "reduced_block_record"
SCOPE_DEFINITIONS = {
    SCOPE_ADMISSION_DOCUMENT:
        "canonical-JSON sha256 of the FULL admission report document "
        "(exporter _canonical_hash(admission_report)); this is the root binding and "
        "the binding of every 'exported' or 'unsupported' body record.",
    SCOPE_REDUCED_BLOCK_RECORD:
        "canonical-JSON sha256 of the REDUCED two-field object "
        '{\"decision\": <body admission_status>, \"reason_codes\": '
        "<body admission_reason_codes>} emitted by "
        "tools/material_volume_body_export.py::_blocked_group for a 'not_exported' "
        "body; it is NOT the admission report document and NEVER a full-report hash.",
}


def _raw_file_identity(raw_bytes: bytes | None) -> dict:
    """Full-report identity per the contract §6 identity table (binding on
    receipts and manifests): raw-file SHA-256 over the exact delivered bytes, and
    canonical-content SHA-256 (every CRLF and lone CR replaced by LF — the report
    is a declared text artifact). Distinct claims, computed separately from any
    admission_report_sha256 scope."""
    if raw_bytes is None:
        return {"claim_kinds": "contract §6: raw-file SHA-256; canonical-content "
                               "SHA-256; Git blob identity — distinct claims, never "
                               "conflated with any admission_report_sha256 scope",
                "raw_file_sha256": None, "canonical_content_sha256": None,
                "note": "in-memory verdict: no file bytes were read; the CLI "
                        "verifies full-report identity from the delivered file"}
    canonical_content = raw_bytes.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return {"claim_kinds": "contract §6: raw-file SHA-256 over the exact delivered "
                           "bytes; canonical-content SHA-256 (CRLF/CR -> LF, "
                           "declared text artifact) — distinct claims, never "
                           "conflated with any admission_report_sha256 scope",
            "raw_file_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "canonical_content_sha256": hashlib.sha256(canonical_content).hexdigest()}


def _admission_hash_scopes(report: Any,
                           full_report_identity: dict) -> dict:
    bodies = []
    if _is_mapping(report) and isinstance(report.get("body_groups"), list):
        for index, row in enumerate(report["body_groups"]):
            if not _is_mapping(row):
                continue
            bodies.append({
                "index": index,
                "body_id": row.get("body_id"),
                "export_status": row.get("export_status"),
                "admission_report_sha256": row.get("admission_report_sha256"),
                "scope": (SCOPE_REDUCED_BLOCK_RECORD
                          if row.get("export_status") == BODY_NOT_EXPORTED
                          else SCOPE_ADMISSION_DOCUMENT),
            })
    root_hash = report.get("admission_report_sha256") if _is_mapping(report) else None
    return {
        "rule": ADMISSION_HASH_SCOPES_RULE,
        "scope_definitions": SCOPE_DEFINITIONS,
        "root": {"admission_report_sha256": root_hash,
                 "scope": (SCOPE_ADMISSION_DOCUMENT
                           if _hex_field_ok(root_hash) else "null_binding")},
        "bodies": bodies,
        "full_report_identity": full_report_identity,
    }


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------
def validate_report(report: Any, admission_report: Any = None,
                    full_report_identity: dict | None = None) -> dict:
    """Static eligibility verdict for one export report.

    Returns a verdict dict; ACCEPT iff every rule passes for the root and for
    every body. Purely static: no assembly, no mutation, no dynamics.
    """
    log = _FailureLog()
    well_formed = rule_r1_identity(report, log)
    root_status = rule_r2_root_status(report, log) if _is_mapping(report) else None
    reader_note = rule_r0_reader_cross_check(report, log)
    if _is_mapping(report):
        rule_r3_admission_status(report, log)
        rule_r4_hash_binding(report, log, admission_report)
        rule_r5_body_status(report, root_status, log)
        rule_r12_readiness(report, log)
        rule_r13_safety_flags(report, log)
        rule_r14_unassigned(report, root_status, log)
        rule_r15_no_recombination(report, log)
        rule_r16_no_lineage(report, log)
        groups = report.get("body_groups")
        if isinstance(groups, list):
            for index, row in enumerate(groups):
                if not _is_mapping(row):
                    continue
                location = f"$.body_groups[{index}]"
                if row.get("export_status") == BODY_EXPORTED:
                    frame_id = rule_r10_body_frame(row, log, location)
                    props = row.get("mass_properties")
                    if _is_mapping(props):
                        rule_r6_mass(props, log, location)
                        rule_r7_volume(props, log, location)
                        rule_r8_center_of_mass(props, frame_id, log, location)
                        rule_r9_inertia(props, frame_id, log, location)
                    else:
                        log.add("R5", "mass_properties_not_an_object",
                                "CON-1: exported bodies need a mass_properties object",
                                location)
                rule_r11_ownership(row, log, location)
    failures = log.failures
    rules_hit = sorted({f["rule"] for f in failures})
    verdict = "ACCEPT" if not failures else "REJECT"

    # W6 reconciliation (contract v1.0 §5): D1-D5 are DECIDED (2026-09-24), not
    # pending. Each spot records the decided reading as issued, the reconciliation
    # outcome, and whether this report's shape exercised the spot.
    decision_records = [
        {"id": "D1", "title": "Readiness promotion authority",
         "decided": True, "decided_on": "2026-09-24",
         "decided_reading": "Approve the contract for static inspection and "
                            "validation only. Exporter success cannot promote a body "
                            "to dynamics-ready. Runtime binding requires a separate "
                            "Astra-approved qualification gate.",
         "enforced_by": "R12",
         "reconciliation": "NO-CHANGE: the strictest reading equals the decided "
                           "reading (CON-14 stands; the claim class stays closed); "
                           "R12 is unchanged.",
         "exercised": any(f["rule"] == "R12" for f in failures)},
        {"id": "D2", "title": "partial policy",
         "decided": True, "decided_on": "2026-09-24",
         "decided_reading": "Reject partial reports for assembly. Diagnostic tools "
                            "may inspect exported bodies only while explicitly "
                            "displaying omitted bodies and unassigned cells. No "
                            "subset-binding exception yet.",
         "enforced_by": "R2, R14 + preserved_diagnostics",
         "reconciliation": "REJECTION NO-CHANGE (partial-assembly rejection kept, "
                           "including any subset binding); DIAGNOSTIC DELTA "
                           "W6-D2: preserved_diagnostics now explicitly displays "
                           "omitted bodies and unassigned cells on partial roots "
                           "(CON-3 as amended by D2).",
         "exercised": any(f["rule"] in ("R2", "R14")
                          and f["reason"] in ("partial_rejected",
                                              "complete_with_unassigned_cells",
                                              "complete_with_unassigned_rows",
                                              "complete_with_unassigned_flag")
                          for f in failures)},
        {"id": "D3", "title": "Composite recombination / verification aggregation",
         "decided": True, "decided_on": "2026-09-24",
         "decided_reading": "Allow read-only aggregate calculations for "
                            "verification, with explicit frames and disjoint cell "
                            "ownership. Do not collapse bodies, infer joints, or "
                            "change runtime grouping.",
         "enforced_by": "R15 + separate verify_con16_aggregate entry point",
         "reconciliation": "REPORT-FIELD REJECTION NO-CHANGE (CON-16d: no body "
                           "record is collapsed, rewritten, or merged — collapsed "
                           "export bodies stay rejected); AGGREGATION DELTA "
                           "W6-D3: separate read-only CON-16 verification "
                           "aggregation (explicit frames, disjoint ownership, "
                           "verification artifact); the validation verdict itself "
                           "computes no aggregate math.",
         "exercised": any(f["rule"] == "R15" for f in failures)},
        {"id": "D4", "title": "Parent-frame lineage schema",
         "decided": True, "decided_on": "2026-09-24",
         "decided_reading": "Retain v1's flat, pre-composed transforms. Defer v2.",
         "enforced_by": "R16",
         "reconciliation": "NO-CHANGE: CON-15 stands; flat v1 frames kept; the v2 "
                           "lineage schema stays deferred and is not designed "
                           "here; R16 is unchanged.",
         "exercised": any(f["rule"] == "R16" for f in failures)},
        {"id": "D5", "title": "Source-effective segment mass transport",
         "decided": True, "decided_on": "2026-09-24",
         "decided_reading": "Source-effective masses remain unsupported. No "
                            "fallback or transport is authorized.",
         "enforced_by": "R2, R11, R13",
         "reconciliation": "NO-CHANGE: CON-5 stands for v1 with no substitution "
                           "path; source-effective exclusion kept exactly as "
                           "approved.",
         "exercised": any(f["rule"] in ("R2", "R11", "R13")
                          and ("unsupported" in f["reason"]
                               or "mass_authority" in f["reason"]
                               or "source_effective" in f["reason"]
                               or "source-effective" in f["detail"]
                               or "source_effective" in f["detail"])
                          for f in failures)},
    ]

    # Preservation duty (CON-4/CON-6): echo diagnostics from rejected records.
    # W6-D2 (D2 decided): a `partial` rejection must also explicitly display the
    # omitted bodies and the unassigned-cell gaps (CON-3 as amended) — by id,
    # never merged into a body.
    preserved: dict = {}
    if _is_mapping(report):
        if root_status in ("blocked", "refused"):
            preserved["root_reason_codes"] = report.get("reason_codes")
            if "detail" in report:
                preserved["root_detail"] = report.get("detail")
        if root_status == "partial":
            preserved["unassigned_cell_ids"] = report.get("unassigned_cell_ids")
            preserved["unassigned_cells"] = report.get("unassigned_cells")
            preserved["all_supplied_cells_assigned"] = \
                report.get("all_supplied_cells_assigned")
        if root_status in ("blocked", "refused", "partial"):
            groups = report.get("body_groups")
            if isinstance(groups, list):
                preserved["bodies"] = [
                    {k: row.get(k) for k in
                     ("body_id", "export_status", "reason_codes",
                      "blocking_cell_ids", "blocking_assignment_statuses",
                      "admission_reason_codes")
                     if _is_mapping(row) and row.get(k) is not None}
                    for row in groups if _is_mapping(row)
                ]

    bodies_summary: list[dict] = []
    if _is_mapping(report) and isinstance(report.get("body_groups"), list):
        for index, row in enumerate(report["body_groups"]):
            location = f"$.body_groups[{index}]"
            body_failures = [f for f in failures if f["location"].startswith(location)]
            bodies_summary.append({
                "index": index,
                "body_id": row.get("body_id") if _is_mapping(row) else None,
                "export_status": row.get("export_status") if _is_mapping(row) else None,
                "eligible_for_assembly": not body_failures and verdict == "ACCEPT",
                "rule_failures": body_failures,
            })
    return {
        "validator": "M10 rigid_body_mass_consumption_validator",
        "static_only": True,
        "runtime_wiring": False,
        "verdict": verdict,
        "assembly_eligible": verdict == "ACCEPT",
        "schema_version": report.get("schema_version") if _is_mapping(report) else None,
        "report_export_status": root_status,
        "admission_status": report.get("admission_status") if _is_mapping(report) else None,
        "root_rule_failures": [f for f in failures if f["location"] == "$"
                               or not f["location"].startswith("$.body_groups")],
        "bodies": bodies_summary,
        "all_rule_failures": failures,
        "rules_evaluated": ["R0", "R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8",
                            "R9", "R10", "R11", "R12", "R13", "R14", "R15", "R16"],
        "rules_violated": rules_hit,
        "decision_records": decision_records,
        "admission_hash_scopes": _admission_hash_scopes(
            report, full_report_identity or _raw_file_identity(None)),
        "reader_cross_check": reader_note,
        "preserved_diagnostics": preserved,
        "limits": [
            "L1: admission_report_sha256/input_hashes recomputation requires the source "
            "documents (--admission-report); otherwise presence, well-formedness, and "
            "root-body consistency are the static checks (PREREGISTRATION LIMIT 1).",
            "L2: a wrong-but-symmetric, correctly-flagged tensor is undecidable "
            "statically; integrity anchors are the hashes, verifiable only against "
            "supplied documents (PREREGISTRATION LIMIT 2, adversarial probe A5).",
        ],
    }


def load_json_file(path: str | Path) -> tuple[Any, str | None]:
    """Strict load mirroring the exporter's loader (duplicate keys / NaN refused)."""
    if READER_AVAILABLE:
        try:
            return _EXPORTER.read_json_file(str(path)), None
        except _EXPORTER.ExportInputError as error:
            return None, f"{error.reason}: {error.detail}"
    try:
        text = Path(path).read_text(encoding="utf-8")

        def _pairs(pairs):  # noqa: ANN001
            keys = [k for k, _ in pairs]
            if len(set(keys)) != len(keys):
                raise ValueError("duplicate JSON key")
            return dict(pairs)

        def _constant(token):  # noqa: ANN001
            raise ValueError(f"nonstandard JSON constant {token!r}")

        return json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant), None
    except (OSError, UnicodeError, ValueError) as error:
        return None, f"input_read_error: {type(error).__name__}: {error}"


def validate_file(report_path: str | Path,
                  admission_report_path: str | Path | None = None) -> tuple[dict, str | None]:
    report, error = load_json_file(report_path)
    if error is not None:
        return {}, error
    admission = None
    if admission_report_path is not None:
        admission, error = load_json_file(admission_report_path)
        if error is not None:
            return {}, f"admission report unreadable: {error}"
    # MV-O1 (decided): full-report identity is verified SEPARATELY at the handoff,
    # from the exact delivered bytes — never conflated with any
    # admission_report_sha256 scope.
    try:
        raw_bytes = Path(report_path).read_bytes()
    except OSError:
        raw_bytes = None
    identity = _raw_file_identity(raw_bytes)
    return validate_report(report, admission, identity), None


# --------------------------------------------------------------------------
# CON-16 (D3, decided) -- SEPARATE read-only verification aggregation.
# Permitted for verification only: composite mass, COM, and full inertia across
# exported bodies, with explicit frames, disjoint verbatim cell ownership, its
# own error accounting, and no body record collapsed, rewritten, or merged.
# Collapsed export bodies (R15), inferred joints, and runtime regrouping stay
# forbidden. This function never mutates its input and returns an in-memory
# verification artifact.
# --------------------------------------------------------------------------
def verify_con16_aggregate(report: Any) -> tuple[dict | None, str | None]:
    """Read-only CON-16 verification aggregate; returns ``(artifact, refusal)``.

    (a) runs only on reports whose full static validation ACCEPTs (CON-1/CON-2:
    exported bodies of a complete report); (b) refuses cross-body cell-ownership
    overlap, naming the cell and both verbatim owners; (c) states frames
    explicitly (target: the report's domain frame, CON-10 convention, rotations
    as authored and never repaired); (d) aggregates via parallel-axis terms in
    domain coordinates and records its own error accounting.
    """
    if not (_is_mapping(report) and isinstance(report.get("body_groups"), list)):
        return None, ("not_a_v1_report: CON-16 aggregation requires a "
                      "chimera.rigid_body_mass_export.v1 report with body_groups")
    verdict = validate_report(report)
    if verdict["verdict"] != "ACCEPT":
        return None, ("report_not_accepted: CON-16 aggregation runs only on "
                      "reports whose full static validation ACCEPTs (CON-1/CON-2); "
                      "see the validation verdict for the named failures")

    owner_of_cell: dict[str, str] = {}
    contributions = []
    frame_ids = []
    gram_residuals = []
    det_residuals = []
    for index, row in enumerate(report["body_groups"]):
        frame = row.get("body_frame") or {}
        frame_id = frame.get("frame_id")
        domain = frame.get("domain_from_body") or {}
        rotation = np.asarray(domain.get("rotation"), dtype=np.float64)
        origin = np.asarray(domain.get("origin_m"), dtype=np.float64)
        props = row.get("mass_properties") or {}
        mass = float(props["mass"]["value"])
        com_body = np.asarray(props["center_of_mass"]["value"], dtype=np.float64)
        inertia_body = np.asarray(props["inertia_tensor_about_com"]["value"],
                                  dtype=np.float64)
        # CON-10: rotations are consumed AS AUTHORED and never repaired.
        gram = float(np.max(np.abs(rotation.T @ rotation - np.eye(3))))
        det_error = abs(float(np.linalg.det(rotation)) - 1.0)
        if gram > ORTHONORMALITY_TOL or det_error > ORTHONORMALITY_TOL:
            return None, (f"frame_not_proper_orthonormal: body_groups[{index}] "
                          f"rotation (frame_id {frame_id!r}) is not proper "
                          f"orthonormal as authored (max|RtR-I|={gram:.3e}, "
                          f"|det-1|={det_error:.3e}); CON-10: refuse, never repair")
        gram_residuals.append(gram)
        det_residuals.append(det_error)
        frame_ids.append(frame_id)
        contributions.append({
            "body_id": row.get("body_id"),
            "mass_kg": mass,
            "com_domain_m": rotation @ com_body + origin,
            "inertia_domain_kg_m2": rotation @ inertia_body @ rotation.T,
        })
        for prow in row.get("cell_provenance") or []:
            cell_id = prow.get("cell_id")
            owner = prow.get("mass_owner_id")
            previous = owner_of_cell.get(cell_id)
            if previous is not None and previous != owner:
                return None, (f"ownership_not_disjoint: CON-16(b) requires one "
                              f"mass owner per cell taken verbatim from "
                              f"cell_provenance; cell {cell_id!r} is claimed by "
                              f"{previous!r} and {owner!r}")
            owner_of_cell[cell_id] = owner

    total_mass = sum(c["mass_kg"] for c in contributions)
    aggregate_com = sum((c["mass_kg"] * c["com_domain_m"] for c in contributions),
                        np.zeros(3)) / total_mass
    aggregate_inertia = np.zeros((3, 3))
    displacements = []
    for contribution in contributions:
        displacement = contribution["com_domain_m"] - aggregate_com
        displacements.append(float(np.linalg.norm(displacement)))
        parallel_term = contribution["mass_kg"] * (
            float(displacement @ displacement) * np.eye(3)
            - np.outer(displacement, displacement))
        aggregate_inertia += contribution["inertia_domain_kg_m2"] + parallel_term

    return {
        "artifact_kind": "con16_verification_aggregate",
        "not_a_v1_body_record": True,
        "consumable_unit": False,
        "read_only": True,
        "static_only": True,
        "runtime_grouping_changed": False,
        "joints_inferred": False,
        "bodies_collapsed_or_merged": False,
        "authority": "contract v1.0 §5 D3 (decided 2026-09-24) and CON-16: "
                     "read-only aggregate calculations for verification only",
        "frames": {
            "target_frame": {"kind": "domain", "stated_explicitly": True,
                             "convention": "x_domain = rotation · x_body + "
                                           "origin_m (CON-10); right-handed, "
                                           "meters; rotations as authored and "
                                           "never repaired",
                             "constructed_from": frame_ids},
            "per_body": [
                {"body_id": contribution["body_id"], "frame_id": frame_id,
                 "rotation": report["body_groups"][index]["body_frame"]
                             ["domain_from_body"]["rotation"],
                 "origin_m": report["body_groups"][index]["body_frame"]
                             ["domain_from_body"]["origin_m"]}
                for index, (contribution, frame_id) in
                enumerate(zip(contributions, frame_ids))],
        },
        "ownership": {
            "disjoint": True,
            "one_mass_owner_per_cell": True,
            "source": "cell_provenance.mass_owner_id, verbatim (CON-8/CON-16b); "
                      "never inferred",
            "cell_owner_map": owner_of_cell,
        },
        "aggregate": {
            "mass_kg": total_mass,
            "center_of_mass_domain_m": [float(v) for v in aggregate_com],
            "inertia_about_aggregate_com_domain_kg_m2":
                [[float(v) for v in row] for row in aggregate_inertia],
        },
        "error_accounting": {
            "bodies_aggregated": len(contributions),
            "tolerance": ORTHONORMALITY_TOL,
            "orthonormality_residual_max": max(gram_residuals),
            "determinant_residual_max": max(det_residuals),
            "displacement_norms_m": displacements,
            "method": "explicit parallel-axis aggregation of full symmetric "
                      "tensors in the report's domain frame; every body record "
                      "retained unmodified",
        },
    }, None


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="W6-promoted static consumption validator for "
                    "chimera.rigid_body_mass_export.v1 (assembly ELIGIBILITY only; "
                    "no runtime assembly, no dynamics, no mutation; reconciled to "
                    "contract v1.0 with D1-D5 decided 2026-09-24)",
        epilog="Exit classes (M06-H04, decided): exit 0 = accepted static "
               "validation; exit 2 = named input/status refusal (REJECT verdict, "
               "unreadable/invalid input, or usage error); exit 1 = unexpected "
               "internal failure only. Static-only: no runtime wiring.")
    parser.add_argument("--version", action="version",
                        version="rigid_body_mass_consumption_validator "
                                "W6-promotion 1.0.0 (M10 lineage, 71-test frozen "
                                "suite; contract v1.0, D1-D5 decided 2026-09-24; "
                                "exit classes 0=accepted/2=named refusal/"
                                "1=unexpected internal failure per M06-H04)")
    parser.add_argument("report", help="body-mass export report JSON")
    parser.add_argument("--admission-report", default=None,
                        help="optional admission report document; enables CON-13 hash "
                             "recomputation against the delivered document")
    parser.add_argument("--verify-aggregate", action="store_true",
                        help="after validation ACCEPTs, also emit the separate "
                             "read-only CON-16 verification aggregate (explicit "
                             "frames, disjoint ownership, verification artifact)")
    parser.add_argument("--indent", type=int, default=None,
                        help="pretty-print the verdict JSON with this indent")
    args = parser.parse_args(argv)
    try:
        verdict, error = validate_file(args.report, args.admission_report)
    except Exception as error:  # noqa: BLE001 - M06-H04: unexpected internal failure
        sys.stderr.write(f"unexpected_internal_failure: "
                         f"{type(error).__name__}: {error}\n")
        return 1
    if error is not None:
        sys.stderr.write(f"could_not_evaluate: {error}\n")
        return 2
    output = dict(verdict)
    if args.verify_aggregate:
        if verdict["verdict"] == "ACCEPT":
            aggregate, refusal = verify_con16_aggregate(
                load_json_file(args.report)[0])
            output["con16_verification_aggregate"] = aggregate \
                if refusal is None else None
            output["con16_aggregate_refusal"] = refusal
        else:
            output["con16_verification_aggregate"] = None
            output["con16_aggregate_refusal"] = (
                "report_not_accepted: CON-16 aggregation runs only on reports "
                "whose full static validation ACCEPTs (CON-1/CON-2)")
    sys.stdout.write(json.dumps(output, sort_keys=True, indent=args.indent,
                                ensure_ascii=True, allow_nan=False) + "\n")
    # M06-H04 (decided): 0 accepted static validation, 2 named input/status
    # refusal, 1 unexpected internal failure (handled above).
    return 0 if verdict["verdict"] == "ACCEPT" else 2


if __name__ == "__main__":
    raise SystemExit(main())
