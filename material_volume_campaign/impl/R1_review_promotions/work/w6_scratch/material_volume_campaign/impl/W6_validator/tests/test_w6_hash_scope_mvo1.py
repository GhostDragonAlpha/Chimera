"""W6 delta W6-MVO1 (MV-O1, decided): a blocked-body's reduced hash is documented
as covering exactly the exporter's reduced block record and is NEVER called a
full-report hash; full-report identity is verified separately at the handoff.

MV-O1: "Preserve the v1 producer's existing bytes and formula. Document precisely
which reduced object a blocked-body hash covers; never call it a full-report
hash. Verify full-report identity separately at the handoff. Add a regression for
the distinction."

Evidence: M07 decision request O1 — tools/material_volume_body_export.py
`_blocked_group` hashes the REDUCED two-field object
``{"decision": ..., "reason_codes": ...}`` for not_exported bodies (measured
298c544846f7...), while root and exported/unsupported records bind the FULL
admission report document (4d4c43e1e0d1...). The frozen fixture
``genuine_blocked_report.json`` was produced by the real exporter with the same
single-defect construction and reproduces those exact hashes.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")

import pytest  # noqa: E402

from test_validator import FIXTURES, ACCEPT, validator  # noqa: E402

GENUINE_BLOCKED = FIXTURES / "genuine_blocked_report.json"


def _scopes(verdict: dict) -> dict:
    block = verdict.get("admission_hash_scopes")
    assert isinstance(block, dict), "verdict carries no admission_hash_scopes block"
    return block


def test_blocked_body_hashes_documented_as_reduced_object() -> None:
    verdict, error = validator.validate_file(GENUINE_BLOCKED)
    assert error is None
    assert verdict["verdict"] == "REJECT"
    scopes = _scopes(verdict)
    for entry in scopes["bodies"]:
        assert entry["export_status"] == "not_exported"
        assert entry["scope"] == "reduced_block_record"
    # (a) documented PRECISELY: the exact reduced object is named, with the
    # exporter function, and the documentation states it is never a full-report hash.
    reduced_doc = scopes["scope_definitions"]["reduced_block_record"]
    assert '"decision"' in reduced_doc and '"reason_codes"' in reduced_doc
    assert "_blocked_group" in reduced_doc
    assert "full-report hash" in reduced_doc and "NEVER" in reduced_doc
    # ...and the documentation itself never labels a reduced scope a full-report hash.
    for entry in scopes["bodies"]:
        assert entry["scope"] != "full_report"
        assert "full_report" not in entry["scope"]


def test_documented_reduced_object_recomputes_to_the_recorded_hash() -> None:
    # The precision proof: recomputing the documented object from the fixture's
    # own fields reproduces each blocked body's recorded hash exactly.
    report = validator.load_json_file(GENUINE_BLOCKED)[0]
    verdict, error = validator.validate_file(GENUINE_BLOCKED)
    assert error is None
    by_id = {entry["body_id"]: entry for entry in _scopes(verdict)["bodies"]}
    for row in report["body_groups"]:
        recorded = row["admission_report_sha256"]
        recomputed = validator.canonical_hash(
            {"reason_codes": row["admission_reason_codes"],
             "decision": row["admission_status"]})
        assert recomputed == recorded, row["body_id"]
        assert by_id[row["body_id"]]["admission_report_sha256"] == recorded


def test_full_report_identity_verified_separately() -> None:
    raw_bytes = GENUINE_BLOCKED.read_bytes()
    canonical_content = raw_bytes.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    verdict, error = validator.validate_file(GENUINE_BLOCKED)
    assert error is None
    identity = _scopes(verdict)["full_report_identity"]
    assert identity["raw_file_sha256"] == hashlib.sha256(raw_bytes).hexdigest()
    assert identity["canonical_content_sha256"] == hashlib.sha256(
        canonical_content).hexdigest()
    # Distinct §6 claim kinds, named, never conflated with admission_report_sha256.
    assert "raw-file" in identity["claim_kinds"]
    assert "canonical-content" in identity["claim_kinds"]
    assert "admission_report_sha256" in identity["claim_kinds"]
    # The distinction, measured: the full-report identity differs from every
    # blocked-body reduced hash on the same document.
    report = validator.load_json_file(GENUINE_BLOCKED)[0]
    for row in report["body_groups"]:
        assert identity["raw_file_sha256"] != row["admission_report_sha256"]
    assert identity["raw_file_sha256"] != report["admission_report_sha256"]


def test_complete_report_scopes_are_full_documents() -> None:
    verdict, error = validator.validate_file(ACCEPT)
    assert error is None
    assert verdict["verdict"] == "ACCEPT"
    scopes = _scopes(verdict)
    assert scopes["root"]["scope"] == "admission_report_document"
    report = validator.load_json_file(ACCEPT)[0]
    for entry in scopes["bodies"]:
        assert entry["scope"] == "admission_report_document"
        assert entry["admission_report_sha256"] == report["admission_report_sha256"]
    assert scopes["full_report_identity"]["raw_file_sha256"] == hashlib.sha256(
        ACCEPT.read_bytes()).hexdigest()


def test_scope_definitions_cite_the_decided_rule() -> None:
    verdict, error = validator.validate_file(ACCEPT)
    assert error is None
    scopes = _scopes(verdict)
    assert "MV-O1" in scopes["rule"]
