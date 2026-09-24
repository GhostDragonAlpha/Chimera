"""W6 deltas W6-D2 + decision-record reframing (reconciliation table, frozen).

D2 decided: "Reject partial reports for assembly. Diagnostic tools may inspect
exported bodies only while explicitly displaying omitted bodies and unassigned
cells." — the rejection is unchanged; a `partial` rejection must now explicitly
display the omitted bodies and the unassigned-cell gaps.

D1-D5 are DECIDED (contract v1.0 §5, 2026-09-24): the verdict reports them as
`decision_records` with the decided reading quoted and the reconciliation
outcome, no longer as pending requests.
"""
from __future__ import annotations

import os

os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")

import pytest  # noqa: E402

from test_validator import FIXTURES, ACCEPT, validator  # noqa: E402

GENUINE_PARTIAL = FIXTURES / "genuine_partial_report.json"


def _records(verdict: dict) -> dict:
    records = verdict.get("decision_records")
    assert isinstance(records, list), "verdict carries no decision_records"
    return {record["id"]: record for record in records}


def test_decision_records_present_and_decided() -> None:
    verdict, error = validator.validate_file(ACCEPT)
    assert error is None
    records = _records(verdict)
    assert set(records) == {"D1", "D2", "D3", "D4", "D5"}
    for record in records.values():
        assert record["decided"] is True
        assert record["decided_on"] == "2026-09-24"
        assert len(record["decided_reading"]) > 40  # the §5 as-issued reading, quoted
        assert len(record["reconciliation"]) > 20


def test_reconciliation_outcomes_match_the_frozen_table() -> None:
    verdict, error = validator.validate_file(ACCEPT)
    assert error is None
    records = _records(verdict)
    for spot in ("D1", "D4", "D5"):
        assert records[spot]["reconciliation"].startswith("NO-CHANGE"), spot
    assert "DIAGNOSTIC DELTA" in records["D2"]["reconciliation"]
    assert "AGGREGATION DELTA" in records["D3"]["reconciliation"]


def test_exercised_flags_survive_the_reframing() -> None:
    verdict, error = validator.validate_file(FIXTURES / "reject_partial.json")
    assert error is None
    assert _records(verdict)["D2"]["exercised"] is True
    verdict, error = validator.validate_file(
        FIXTURES / "reject_mass_authority_source.json")
    assert error is None
    assert _records(verdict)["D5"]["exercised"] is True
    verdict, error = validator.validate_file(ACCEPT)
    assert error is None
    assert all(record["exercised"] is False for record in _records(verdict).values())


def test_partial_rejection_explicitly_displays_gaps_and_omitted_bodies() -> None:
    verdict, error = validator.validate_file(GENUINE_PARTIAL)
    assert error is None
    # D2 decided keeps the rejection.
    assert verdict["verdict"] == "REJECT"
    assert any(f["reason"] == "partial_rejected"
               for f in verdict["all_rule_failures"])
    # ...and the diagnostic duty: the verdict explicitly displays the unassigned
    # gaps and the omitted (here: still-exported) bodies, by id, never merged.
    preserved = verdict["preserved_diagnostics"]
    assert preserved.get("unassigned_cell_ids") == ["cell-C"]
    rows = preserved.get("unassigned_cells")
    assert rows and rows[0]["cell_id"] == "cell-C"
    assert rows[0]["assignment_status"] == "resolved"
    assert rows[0]["reason"] == "not_assigned_to_an_authored_body_group"
    assert preserved.get("all_supplied_cells_assigned") is False
    body_echo = preserved.get("bodies")
    assert body_echo and [b["body_id"] for b in body_echo] == [
        "coupon-body-A", "coupon-body-B"]
    assert all(b["export_status"] == "exported" for b in body_echo)


def test_blocked_preservation_still_intact() -> None:
    # The pre-existing CON-4/CON-6 preservation duty is unchanged.
    verdict = validator.validate_file(FIXTURES / "reject_blocked.json")[0]
    preserved = verdict["preserved_diagnostics"]
    assert preserved.get("root_reason_codes") == ["missing_density"]
