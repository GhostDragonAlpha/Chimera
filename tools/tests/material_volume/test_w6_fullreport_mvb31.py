"""W6 delta W6-RAW (MV-B3-1, decided): consumption validation reads the FULL raw
report; the reader's summary projection is refused BY NAME.

MV-B3-1: "summarize_export_report is a display projection... Consumption
validation reads the full raw report... Do not silently expand or reinterpret
the existing summary API."

The summary fed here is a GENUINE reader product: summarize_export_report is run
(read-only, bytecode writing disabled) on the clean accept fixture, exactly as
`tools/material_volume_body_export_reader.py` produces it.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")

import pytest  # noqa: E402

from test_validator import AGENT_DIR, FIXTURES, ACCEPT  # noqa: E402

sys.dont_write_bytecode = True
TOOLS = AGENT_DIR  # landed: AGENT_DIR already IS tools/ (home: repo root/tools)
sys.path.insert(0, str(TOOLS))

import material_volume_body_export_reader as reader  # noqa: E402
import rigid_body_mass_consumption_validator as validator  # noqa: E402


def _summary_file(tmp_path: Path) -> Path:
    raw = validator.load_json_file(ACCEPT)[0]
    summary = reader.summarize_export_report(raw)
    assert "bodies" in summary and "body_groups" not in summary
    path = tmp_path / "summary_of_accept.json"
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return path


def test_summary_projection_is_refused_by_name(tmp_path: Path) -> None:
    verdict, error = validator.validate_file(_summary_file(tmp_path))
    assert error is None
    assert verdict["verdict"] == "REJECT"
    failures = verdict["all_rule_failures"]
    named = [f for f in failures
             if f["reason"] == "summary_projection_is_not_a_consumption_document"]
    assert named, failures
    # Refused BY NAME: the refusal cites the display projection and the decision.
    assert any("MV-B3-1" in f["detail"] for f in named)
    assert any("summarize_export_report" in f["detail"] for f in named)


def test_raw_report_still_accepted(tmp_path: Path) -> None:
    # The named summary refusal must not disturb raw-report handling.
    verdict, error = validator.validate_file(ACCEPT)
    assert error is None
    assert verdict["verdict"] == "ACCEPT"


def test_summary_never_validates_as_accept_even_if_retyped(tmp_path: Path) -> None:
    # A summary re-labeled as a raw report (bodies grafted under body_groups)
    # escapes the summary-shaped detector by construction, but still cannot
    # pass: the projection dropped the §1 authoritative fields (B3 measured 42
    # DROPs), so the raw-report authority rules refuse it on their own names.
    raw = validator.load_json_file(ACCEPT)[0]
    summary = reader.summarize_export_report(raw)
    graft = dict(summary)
    graft["body_groups"] = graft.pop("bodies")
    path = tmp_path / "summary_retyped_raw.json"
    path.write_text(json.dumps(graft, indent=2), encoding="utf-8")
    verdict, error = validator.validate_file(path)
    assert error is None
    assert verdict["verdict"] == "REJECT"
    violated = set(verdict["rules_violated"])
    assert "R11" in violated and "R13" in violated  # provenance + fixed v1 flags dropped by the projection
