"""M10 frozen acceptance tests (PREREGISTRATION.md, frozen before implementation),
staged for W6 promotion (impl/W6_validator) — path adaptation only; assertions are
changed only by the preregistered reconciliation deltas (PREREGISTRATION.md).

Run (landed; canonical command in tools/tests/material_volume/README.md):
    CHIMERA_TOOLS_DIR=<worktree>/tools PYTHONDONTWRITEBYTECODE=1 \
        python -m pytest tools/tests/material_volume/ -v
Every reject fixture lives in tests/fixtures and is a single mutation of the
verbatim copy of the tools example report. tools/ is never touched.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")

HERE = Path(__file__).resolve().parent
AGENT_DIR = HERE.parents[1]  # landed: tools/ (home layout had tests/ beside the tool)
FIXTURES = HERE / "fixtures"
sys.dont_write_bytecode = True
sys.path.insert(0, str(AGENT_DIR))

import pytest  # noqa: E402

import rigid_body_mass_consumption_validator as validator  # noqa: E402

ACCEPT = FIXTURES / "accept_complete_report.json"

# (fixture, rules that MUST appear among rules_violated)
REJECT_TABLE = [
    # R2 root export_status gate (+ decision requests D2/D5)
    ("reject_partial.json", ["R2"]),
    ("reject_blocked.json", ["R2", "R3", "R5"]),
    ("reject_unsupported.json", ["R2", "R5"]),
    ("reject_refused.json", ["R2", "R3", "R4", "R13", "R14"]),
    ("reject_unknown_status.json", ["R2"]),
    ("adversarial_case_variant_status.json", ["R2", "R5"]),      # A3
    # R3 admission_status
    ("reject_admission_case.json", ["R3"]),
    ("reject_admission_loose.json", ["R3"]),
    # R4 hash binding
    ("reject_hash_missing.json", ["R4"]),
    ("reject_hash_short.json", ["R4"]),
    ("reject_hash_mismatch.json", ["R4"]),
    ("reject_hash_uppercase.json", ["R4"]),
    # R5 per-body status
    ("reject_not_exported.json", ["R5"]),
    ("reject_placeholder_mass.json", ["R5"]),
    # R6 mass authority
    ("reject_mass_unit.json", ["R6"]),
    ("reject_mass_negative.json", ["R6"]),
    ("reject_mass_not_invariant.json", ["R6"]),
    # R7 volume form
    ("reject_volume_unit.json", ["R7"]),
    # R8 center of mass
    ("reject_com_frame.json", ["R8"]),
    ("reject_com_short.json", ["R8"]),
    # R9 full-tensor integrity
    ("reject_tensor_truncated.json", ["R9"]),                    # A1
    ("reject_tensor_asymmetric.json", ["R9"]),                   # A2
    ("reject_tensor_pa_true.json", ["R9"]),
    ("reject_tensor_offdiag_flag.json", ["R9"]),
    ("reject_tensor_full_flag.json", ["R9"]),
    ("reject_tensor_unit.json", ["R9"]),
    ("reject_tensor_frame.json", ["R9"]),
    # R10 body frame
    ("reject_frame_lefthanded.json", ["R10"]),
    ("reject_frame_nonorthonormal.json", ["R10"]),
    ("reject_frame_handedness.json", ["R10"]),
    ("reject_frame_unit.json", ["R10"]),
    # R11 ownership / provenance (D5 for mass authority)
    ("reject_provenance_stripped.json", ["R11"]),
    ("reject_owned_missing_provenance.json", ["R11"]),
    ("reject_conflicting_owner.json", ["R11"]),
    ("reject_owner_ids_mismatch.json", ["R11"]),
    ("reject_source_kind.json", ["R11"]),
    ("reject_mass_authority_source.json", ["R11"]),
    # R12 readiness (D1)
    ("reject_readiness_root.json", ["R12"]),
    ("reject_readiness_body.json", ["R12"]),
    ("adversarial_readiness_nested.json", ["R12"]),              # A4
    # R13 fixed v1 safety flags (D5 for source payloads)
    ("reject_production_wired.json", ["R13"]),
    ("reject_state_mutated.json", ["R13"]),
    ("reject_source_payloads.json", ["R13"]),
    ("reject_validation_only_false.json", ["R13"]),
    # R14 unassigned cells (D2)
    ("reject_unassigned_in_complete.json", ["R14"]),
    ("reject_all_supplied_false.json", ["R14"]),
    # R15 recombination (D3)
    ("reject_composite.json", ["R15"]),
    # R16 lineage (D4)
    ("reject_lineage.json", ["R16"]),
]

DECISION_EXERCISE = [
    ("reject_readiness_root.json", "D1"),
    ("reject_readiness_body.json", "D1"),
    ("adversarial_readiness_nested.json", "D1"),
    ("reject_partial.json", "D2"),
    ("reject_unassigned_in_complete.json", "D2"),
    ("reject_all_supplied_false.json", "D2"),
    ("reject_composite.json", "D3"),
    ("reject_lineage.json", "D4"),
    ("reject_unsupported.json", "D5"),
    ("reject_source_payloads.json", "D5"),
    ("reject_mass_authority_source.json", "D5"),
]


def verdict_for(name: str) -> dict:
    verdict, error = validator.validate_file(FIXTURES / name)
    assert error is None, f"fixture {name} unreadable: {error}"
    return verdict


def test_accept_clean_example_report() -> None:
    verdict, error = validator.validate_file(ACCEPT)
    assert error is None
    assert verdict["verdict"] == "ACCEPT"
    assert verdict["assembly_eligible"] is True
    assert verdict["rules_violated"] == []
    assert verdict["all_rule_failures"] == []
    assert all(body["eligible_for_assembly"] for body in verdict["bodies"])
    assert len(verdict["bodies"]) == 2
    assert verdict["report_export_status"] == "complete"
    assert verdict["static_only"] is True and verdict["runtime_wiring"] is False
    # W6 reconciliation: D1-D5 are DECIDED (contract v1.0 §5); the verdict reports
    # them as decision_records with the decided reading, no longer requests.
    records = verdict["decision_records"]
    assert len(records) == 5
    assert all(d["decided"] is True for d in records)
    assert all(d["exercised"] is False for d in records)


def test_reader_cross_check_passes_on_accept() -> None:
    verdict = verdict_for("accept_complete_report.json")
    assert verdict["reader_cross_check"] == {"ran": True, "reader_verdict": "pass"}


def test_validator_reads_raw_report_not_reader_summary() -> None:
    # The reader's summary hard-codes readiness False; the validator must see the
    # real flag. The root-readiness mutant must still be rejected.
    verdict = verdict_for("reject_readiness_root.json")
    reasons = [f["reason"] for f in verdict["all_rule_failures"]]
    assert "root_readiness_flag_not_false" in reasons


@pytest.mark.parametrize("fixture_name,expected_rules", REJECT_TABLE,
                         ids=[row[0] for row in REJECT_TABLE])
def test_reject_fixture(fixture_name: str, expected_rules: list[str]) -> None:
    verdict = verdict_for(fixture_name)
    assert verdict["verdict"] == "REJECT", fixture_name
    assert verdict["assembly_eligible"] is False
    violated = set(verdict["rules_violated"])
    for rule in expected_rules:
        assert rule in violated, (fixture_name, rule, verdict["all_rule_failures"])
    # every failure names its rule and carries a reason and detail
    for failure in verdict["all_rule_failures"]:
        assert failure["rule"] and failure["reason"] and failure["detail"]


@pytest.mark.parametrize("fixture_name,decision_id", DECISION_EXERCISE,
                         ids=[f"{row[1]}<-{row[0]}" for row in DECISION_EXERCISE])
def test_decision_request_exercised(fixture_name: str, decision_id: str) -> None:
    verdict = verdict_for(fixture_name)
    assert verdict["verdict"] == "REJECT"
    # W6 reconciliation: D1-D5 are DECIDED; the verdict's records keep the
    # exercised flags under decision_records.
    exercised = {d["id"]: d["exercised"] for d in verdict["decision_records"]}
    assert exercised[decision_id] is True, fixture_name


def test_adversarial_a5_diagonalized_limit_is_declared() -> None:
    # PREREGISTRATION LIMIT 2 / probe A5: a wrong-but-symmetric, correctly-flagged
    # tensor is statically undecidable; the validator ACCEPTS it by design and the
    # verdict carries the recorded limit. This is the pre-declared behavior.
    verdict = verdict_for("adversarial_diagonalized.json")
    assert verdict["verdict"] == "ACCEPT"
    assert any("L2" in limit for limit in verdict["limits"])
    assert "R9" not in verdict["rules_violated"]


def test_recompute_path_match() -> None:
    verdict, error = validator.validate_file(FIXTURES / "recompute_report.json",
                                             FIXTURES / "recompute_admission.json")
    assert error is None
    assert verdict["verdict"] == "ACCEPT", verdict["all_rule_failures"]


def test_recompute_path_mismatch_is_tamper() -> None:
    verdict, error = validator.validate_file(FIXTURES / "recompute_report.json",
                                             FIXTURES / "recompute_admission_mismatched.json")
    assert error is None
    assert verdict["verdict"] == "REJECT"
    reasons = [f["reason"] for f in verdict["all_rule_failures"]]
    assert "admission_hash_recomputation_mismatch" in reasons


def test_recompute_path_rejects_wrong_document_for_original_report() -> None:
    # The original example's admission document is NOT supplied; supplying any
    # other document must produce a tamper refusal, never a silent pass.
    verdict, error = validator.validate_file(ACCEPT,
                                             FIXTURES / "recompute_admission.json")
    assert error is None
    assert verdict["verdict"] == "REJECT"
    reasons = [f["reason"] for f in verdict["all_rule_failures"]]
    assert "admission_hash_recomputation_mismatch" in reasons


def test_blocked_report_preserves_blocking_diagnostics() -> None:
    verdict = verdict_for("reject_blocked.json")
    preserved = verdict["preserved_diagnostics"]
    assert preserved.get("root_reason_codes") == ["missing_density"]
    body_echo = preserved.get("bodies", [])
    assert body_echo and body_echo[0]["blocking_cell_ids"] == ["cell-A"]
    assert body_echo[0]["blocking_assignment_statuses"] == [
        {"cell_id": "cell-A", "status": "missing_density"}]


def test_refused_report_preserves_reason_and_detail() -> None:
    verdict = verdict_for("reject_refused.json")
    preserved = verdict["preserved_diagnostics"]
    assert preserved.get("root_reason_codes") == ["duplicate_json_key"]
    assert preserved.get("root_detail") == "duplicate JSON key"


def test_cli_exit_codes() -> None:
    # W6-EXIT delta (M06-H04, decided): the promoted CLI uses 0 = accepted,
    # 2 = named input/status refusal (REJECT verdict or unreadable input),
    # 1 = unexpected internal failure. The original M10 tool keeps 0/1/2 =
    # accept/reject/unreadable as the campaign artifact.
    base = [sys.executable, str(AGENT_DIR / "rigid_body_mass_consumption_validator.py")]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    accept = subprocess.run(base + [str(ACCEPT)], capture_output=True, env=env)
    assert accept.returncode == 0
    assert b'"verdict": "ACCEPT"' in accept.stdout
    reject = subprocess.run(base + [str(FIXTURES / "reject_partial.json")],
                            capture_output=True, env=env)
    assert reject.returncode == 2
    missing = subprocess.run(base + [str(FIXTURES / "no_such_file.json")],
                             capture_output=True, env=env)
    assert missing.returncode == 2
    assert b"could_not_evaluate" in missing.stderr


def test_no_bytecode_written_into_tools() -> None:
    tools_pycache = HERE.parents[1] / "__pycache__"  # landed: tools/ directly
    if tools_pycache.exists():
        leaked = list(tools_pycache.glob("material_volume_body_export*"))
        assert leaked == [], f"bytecode written into read-only tools/: {leaked}"
    assert sys.dont_write_bytecode is True


def test_validator_module_makes_no_physics_or_runtime_claims() -> None:
    # W6-D3 (D3 decided): the blanket composite-math ban is narrowed — CON-16
    # permits a SEPARATE read-only verification aggregate (verify_con16_aggregate,
    # pinned by tests/test_w6_con16_aggregate.py, including that validate_report
    # never emits aggregate math). Runtime assembly, dynamics, and readiness
    # promotion remain banned outright.
    source = (AGENT_DIR / "rigid_body_mass_consumption_validator.py").read_text("utf-8")
    for banned in ("def assemble", "set_ready(", "promote_readiness",
                   "import pygame", "physics_engine"):
        assert banned not in source, banned
    # The only aggregation entry point is the CON-16 one.
    aggregate_defs = [line.strip() for line in source.splitlines()
                      if line.lstrip().startswith("def ") and "aggregate" in line]
    assert aggregate_defs == ["def verify_con16_aggregate(report: Any) -> tuple[dict | None, str | None]:"]
