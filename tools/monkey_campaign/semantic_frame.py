"""Machine-checkable semantic 3D frame qualification.

This module does not infer anatomy from appearance.  It checks that a producer has
bound geometry to explicit semantic directions, independent landmarks, knowledge
claims, topology coverage, ports, and a physical motion witness.  Missing evidence
is a named refusal; contradictory evidence is a named failure.  Rendered views are
debug instruments generated from the qualified frame, never the source of the
semantic answer.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from typing import Any


SCHEMA = "chimera.semantic_spatial_frame.v1"
SEMANTIC_PAIRS = (("distal", "proximal"), ("dorsal", "palm"), ("lateral", "medial"))
ALLOWED_DOMAINS = {"biology", "physics", "geometry", "authored_semantics"}
ALLOWED_AUTHORITIES = {
    "primary_measurement",
    "peer_reviewed_reference",
    "authoritative_database",
    "derived_physics",
    "operator_authored_semantics",
}


@dataclass(frozen=True)
class SemanticFrameError(ValueError):
    outcome: str
    code: str
    details: dict[str, Any]

    def __str__(self) -> str:
        return f"{self.outcome}:{self.code}:{json.dumps(self.details, sort_keys=True)}"


def _refuse(code: str, **details: Any) -> None:
    raise SemanticFrameError("REFUSED", code, details)


def _fail(code: str, **details: Any) -> None:
    raise SemanticFrameError("FAIL", code, details)


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _digest(value: Any, length: int = 64) -> bool:
    return isinstance(value, str) and re.fullmatch(f"[0-9a-f]{{{length}}}", value) is not None


def _number(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def _vec(value: Any, label: str) -> tuple[float, float, float]:
    if not isinstance(value, list) or len(value) != 3 or not all(_number(v) for v in value):
        _fail("vector_invalid", field=label)
    return tuple(float(v) for v in value)


def _dot(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _sub(a: tuple[float, ...], b: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(x - y for x, y in zip(a, b))


def _norm(a: tuple[float, ...]) -> float:
    return math.sqrt(_dot(a, a))


def _cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _unit(value: Any, label: str, tol: float) -> tuple[float, float, float]:
    result = _vec(value, label)
    if not math.isclose(_norm(result), 1.0, rel_tol=tol, abs_tol=tol):
        _fail("direction_not_unit", field=label, norm=_norm(result))
    return result


def _unique_text_list(value: Any, label: str, *, nonempty: bool = True) -> list[str]:
    if (not isinstance(value, list) or not all(_text(v) for v in value)
            or len(set(value)) != len(value) or (nonempty and not value)):
        _fail("identity_list_invalid", field=label)
    return value


def _claims(packet: dict[str, Any]) -> dict[str, dict[str, Any]]:
    claims = packet.get("knowledge_claims")
    if not isinstance(claims, list) or not claims:
        _refuse("knowledge_claims_missing")
    indexed: dict[str, dict[str, Any]] = {}
    for row in claims:
        if not isinstance(row, dict) or not _text(row.get("id")) or row["id"] in indexed:
            _fail("knowledge_claim_invalid")
        if row.get("domain") not in ALLOWED_DOMAINS:
            _fail("knowledge_domain_invalid", claim_id=row["id"])
        if row.get("authority") not in ALLOWED_AUTHORITIES:
            _fail("knowledge_authority_invalid", claim_id=row["id"])
        if not _text(row.get("source_ref")) or not _text(row.get("statement")):
            _refuse("knowledge_provenance_missing", claim_id=row["id"])
        if not _digest(row.get("artifact_sha256")):
            _refuse("knowledge_artifact_hash_missing", claim_id=row["id"])
        indexed[row["id"]] = row
    required_domains = set(_unique_text_list(packet.get("required_knowledge_domains"),
                                             "required_knowledge_domains"))
    unknown = required_domains - ALLOWED_DOMAINS
    if unknown:
        _fail("required_knowledge_domain_invalid", domains=sorted(unknown))
    present = {claim["domain"] for claim in indexed.values()}
    missing = required_domains - present
    if missing:
        _refuse("required_knowledge_domain_missing", domains=sorted(missing))
    construction = set(_unique_text_list(packet.get("construction_claim_ids"),
                                         "construction_claim_ids"))
    validation = set(_unique_text_list(packet.get("validation_claim_ids"),
                                       "validation_claim_ids"))
    unknown_ids = (construction | validation) - indexed.keys()
    if unknown_ids:
        _fail("knowledge_claim_reference_unknown", claim_ids=sorted(unknown_ids))
    overlap = construction & validation
    if overlap:
        _refuse("circular_validation_claim", claim_ids=sorted(overlap))
    return indexed


def _frame(packet: dict[str, Any], tol: float) -> tuple[dict[str, Any], dict[str, tuple[float, float, float]]]:
    frame = packet.get("frame")
    if not isinstance(frame, dict) or not _text(frame.get("frame_id")):
        _refuse("frame_missing")
    if packet.get("coordinate_unit") not in ("m", "cm", "mm"):
        _fail("coordinate_unit_invalid")
    if frame.get("handedness") != "right":
        _fail("frame_handedness_invalid", expected="right")
    _vec(frame.get("origin"), "frame.origin")
    basis_raw = frame.get("basis")
    if not isinstance(basis_raw, dict) or set(basis_raw) != {"x", "y", "z"}:
        _fail("frame_basis_invalid")
    basis = {name: _unit(basis_raw[name], f"frame.basis.{name}", tol) for name in ("x", "y", "z")}
    for a, b in (("x", "y"), ("x", "z"), ("y", "z")):
        if not math.isclose(_dot(basis[a], basis[b]), 0.0, abs_tol=tol):
            _fail("frame_basis_not_orthogonal", axes=[a, b])
    determinant = _dot(_cross(basis["x"], basis["y"]), basis["z"])
    if not math.isclose(determinant, 1.0, rel_tol=tol, abs_tol=tol):
        _fail("frame_basis_not_proper", determinant=determinant)
    return frame, basis


def _semantics(packet: dict[str, Any], tol: float) -> dict[str, tuple[float, float, float]]:
    raw = packet.get("semantic_directions")
    required = {name for pair in SEMANTIC_PAIRS for name in pair}
    if not isinstance(raw, dict) or not required <= raw.keys():
        _refuse("semantic_directions_missing", required=sorted(required))
    directions = {name: _unit(raw[name], f"semantic_directions.{name}", tol)
                  for name in required}
    for positive, negative in SEMANTIC_PAIRS:
        if not math.isclose(_dot(directions[positive], directions[negative]), -1.0,
                            rel_tol=tol, abs_tol=tol):
            _fail("semantic_opposites_inconsistent", pair=[positive, negative])
    independent = (directions["distal"], directions["dorsal"], directions["lateral"])
    determinant = _dot(_cross(independent[0], independent[1]), independent[2])
    if abs(determinant) < 1.0 - tol:
        _fail("semantic_axes_not_independent", determinant=determinant)
    return directions


def _landmarks(packet: dict[str, Any], claims: dict[str, dict[str, Any]],
               directions: dict[str, tuple[float, float, float]], tol: float) -> dict[str, tuple[float, float, float]]:
    rows = packet.get("landmarks")
    if not isinstance(rows, list) or len(rows) < 3:
        _refuse("independent_landmarks_missing", minimum=3)
    points: dict[str, tuple[float, float, float]] = {}
    roles: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or not _text(row.get("id")) or row["id"] in points:
            _fail("landmark_invalid")
        claim_id = row.get("claim_id")
        if claim_id not in claims:
            _fail("landmark_claim_unknown", landmark_id=row["id"])
        points[row["id"]] = _vec(row.get("position"), f"landmarks.{row['id']}.position")
        if _text(row.get("role")):
            roles.add(row["role"])
    required_roles = set(_unique_text_list(packet.get("required_landmark_roles"),
                                           "required_landmark_roles"))
    missing_roles = required_roles - roles
    if missing_roles:
        _refuse("required_landmark_role_missing", roles=sorted(missing_roles))
    ids = list(points)
    p0 = points[ids[0]]
    independent = False
    for i in range(1, len(ids)):
        for j in range(i + 1, len(ids)):
            if _norm(_cross(_sub(points[ids[i]], p0), _sub(points[ids[j]], p0))) > tol:
                independent = True
                break
        if independent:
            break
    if not independent:
        _refuse("landmarks_collinear")
    witnesses = packet.get("direction_witnesses")
    witnessed: set[str] = set()
    if not isinstance(witnesses, list):
        _refuse("direction_witnesses_missing")
    validation_ids = set(packet["validation_claim_ids"])
    for witness in witnesses:
        if not isinstance(witness, dict) or witness.get("semantic") not in directions:
            _fail("direction_witness_invalid")
        positive, negative = witness.get("positive_landmark"), witness.get("negative_landmark")
        if positive not in points or negative not in points:
            _fail("direction_witness_landmark_unknown", semantic=witness.get("semantic"))
        if witness.get("claim_id") not in validation_ids:
            _refuse("direction_witness_not_independent", semantic=witness["semantic"])
        separation = _dot(_sub(points[positive], points[negative]), directions[witness["semantic"]])
        minimum = witness.get("min_separation")
        if not _number(minimum) or minimum <= 0:
            _fail("direction_witness_threshold_invalid", semantic=witness["semantic"])
        if separation < minimum:
            _fail("direction_witness_contradiction", semantic=witness["semantic"],
                  separation=separation, required=minimum)
        witnessed.add(witness["semantic"])
    missing = {"distal", "dorsal", "lateral"} - witnessed
    if missing:
        _refuse("semantic_direction_unwitnessed", semantics=sorted(missing))
    return points


def _coverage(packet: dict[str, Any]) -> None:
    coverage = packet.get("geometry_coverage")
    if not isinstance(coverage, dict):
        _refuse("geometry_coverage_missing")
    required = _unique_text_list(coverage.get("required_elements"), "geometry_coverage.required_elements")
    mapped = coverage.get("element_bindings")
    if not isinstance(mapped, dict) or not all(_text(k) and _text(v) for k, v in mapped.items()):
        _fail("geometry_element_bindings_invalid")
    missing = sorted(set(required) - mapped.keys())
    if missing:
        _refuse("semantic_geometry_coverage_missing", elements=missing)
    if len(set(mapped[element] for element in required)) != len(required):
        _fail("geometry_element_binding_not_injective")


def _ports(packet: dict[str, Any], directions: dict[str, tuple[float, float, float]], tol: float) -> None:
    ports = packet.get("ports")
    if not isinstance(ports, list) or not ports:
        _refuse("semantic_ports_missing")
    seen = set()
    for port in ports:
        if not isinstance(port, dict) or not _text(port.get("id")) or port["id"] in seen:
            _fail("semantic_port_invalid")
        seen.add(port["id"])
        _vec(port.get("position"), f"ports.{port['id']}.position")
        normal = _unit(port.get("normal"), f"ports.{port['id']}.normal", tol)
        semantic = port.get("outward_semantic")
        if semantic not in directions:
            _fail("semantic_port_direction_unknown", port_id=port["id"])
        if _dot(normal, directions[semantic]) < 1.0 - tol:
            _fail("semantic_port_normal_contradiction", port_id=port["id"], semantic=semantic)


def _motion_witness(packet: dict[str, Any], directions: dict[str, tuple[float, float, float]]) -> None:
    witness = packet.get("kinematic_witness")
    if not isinstance(witness, dict):
        _refuse("semantic_kinematic_witness_missing")
    if witness.get("semantic") != "palm" or witness.get("claim_id") not in packet["validation_claim_ids"]:
        _refuse("semantic_kinematic_witness_not_independent")
    origin = _vec(witness.get("reference_origin"), "kinematic_witness.reference_origin")
    rest = witness.get("rest_points")
    moved = witness.get("moved_points")
    if (not isinstance(rest, list) or not isinstance(moved, list) or not rest
            or len(rest) != len(moved)):
        _refuse("semantic_kinematic_witness_points_missing")
    rest_points = [_vec(p, "kinematic_witness.rest_points") for p in rest]
    moved_points = [_vec(p, "kinematic_witness.moved_points") for p in moved]
    normal = directions["palm"]
    delta = sum(_dot(_sub(b, origin), normal) - _dot(_sub(a, origin), normal)
                for a, b in zip(rest_points, moved_points)) / len(rest_points)
    minimum = witness.get("minimum_signed_progress")
    if not _number(minimum) or minimum <= 0:
        _fail("kinematic_witness_threshold_invalid")
    if delta < minimum:
        _fail("kinematic_witness_semantic_contradiction", semantic="palm",
              signed_progress=delta, required=minimum)


def validate_semantic_frame(packet: dict[str, Any], *, tolerance: float = 1e-6) -> dict[str, Any]:
    """Validate one semantic frame without filesystem, network, image, or model access."""
    if not isinstance(packet, dict) or packet.get("schema") != SCHEMA:
        _fail("semantic_frame_schema_invalid")
    for field in ("subject_id", "subject_kind"):
        if not _text(packet.get(field)):
            _fail("semantic_frame_identity_missing", field=field)
    if not _digest(packet.get("source_head"), 40):
        _fail("semantic_frame_source_head_invalid")
    claims = _claims(packet)
    frame, _ = _frame(packet, tolerance)
    directions = _semantics(packet, tolerance)
    points = _landmarks(packet, claims, directions, tolerance)
    _coverage(packet)
    _ports(packet, directions, tolerance)
    _motion_witness(packet, directions)
    canonical = json.dumps(packet, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return {
        "schema": "chimera.semantic_spatial_frame_receipt.v1",
        "status": "PASS",
        "machine_qualified": True,
        "visual_acceptance": False,
        "subject_id": packet["subject_id"],
        "frame_id": frame["frame_id"],
        "packet_sha256": hashlib.sha256(canonical).hexdigest(),
        "landmark_count": len(points),
        "knowledge_claim_count": len(claims),
        "debug_views": ["+x", "-x", "+y", "-y", "+z", "-z", "port_normals", "semantic_axes"],
        "limits": "Checks declared evidence and physical invariants; does not infer missing anatomy, authenticate sources, inspect pixels, or replace runtime contact tests.",
    }


def main() -> None:
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Validate a Chimera semantic 3D frame packet")
    parser.add_argument("packet")
    args = parser.parse_args()
    try:
        result = validate_semantic_frame(json.loads(Path(args.packet).read_text(encoding="utf-8")))
    except SemanticFrameError as error:
        result = {"status": error.outcome, "code": error.code, "details": error.details}
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(2 if error.outcome == "REFUSED" else 1)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
