"""W6 delta W6-D3 (D3 decided, CON-16): read-only verification aggregation.

D3 decided: "Allow read-only aggregate calculations for verification, with
explicit frames and disjoint cell ownership. Do not collapse bodies, infer
joints, or change runtime grouping."

CON-16: composite mass, COM, and full inertia may be computed across exported
bodies provided that (a) frames are stated explicitly, (b) cell ownership
remains disjoint with one mass owner per cell taken verbatim from
`cell_provenance`, (c) the result is recorded as a verification artifact with
its own error accounting, and (d) no body record is collapsed, rewritten, or
merged. Collapsed export bodies, inferred joints, and runtime regrouping stay
forbidden (R15 unchanged).
"""
from __future__ import annotations

import copy
import json
import os

import numpy as np
import pytest  # noqa: E402

os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")

import rigid_body_mass_consumption_validator as validator  # noqa: E402
from test_validator import FIXTURES, ACCEPT  # noqa: E402


def _artifact(path) -> dict:
    report = validator.load_json_file(path)[0]
    artifact, refusal = validator.verify_con16_aggregate(report)
    assert refusal is None, refusal
    return artifact


def test_aggregate_shape_is_a_verification_artifact() -> None:
    artifact = _artifact(ACCEPT)
    assert artifact["artifact_kind"] == "con16_verification_aggregate"
    assert artifact["not_a_v1_body_record"] is True
    assert artifact["consumable_unit"] is False
    assert artifact["read_only"] is True and artifact["static_only"] is True
    assert artifact["bodies_collapsed_or_merged"] is False
    assert artifact["joints_inferred"] is False
    assert artifact["runtime_grouping_changed"] is False
    assert "D3" in artifact["authority"] and "CON-16" in artifact["authority"]


def test_frames_stated_explicitly() -> None:
    artifact = _artifact(ACCEPT)
    frames = artifact["frames"]
    assert frames["target_frame"]["stated_explicitly"] is True
    assert frames["target_frame"]["kind"] == "domain"
    assert "x_domain" in frames["target_frame"]["convention"]
    assert sorted(frames["target_frame"]["constructed_from"]) == [
        "coupon-A-authored", "coupon-B-authored"]
    per_body = {row["body_id"]: row for row in frames["per_body"]}
    assert set(per_body) == {"coupon-body-A", "coupon-body-B"}
    for row in per_body.values():
        assert row["frame_id"] and len(row["rotation"]) == 3
        assert len(row["origin_m"]) == 3


def test_disjoint_ownership_taken_verbatim() -> None:
    artifact = _artifact(ACCEPT)
    ownership = artifact["ownership"]
    assert ownership["disjoint"] is True
    assert ownership["one_mass_owner_per_cell"] is True
    assert ownership["cell_owner_map"] == {"cell-A": "owner-A", "cell-B": "owner-B"}


def test_aggregate_mass_and_com_match_independent_recomputation() -> None:
    report = validator.load_json_file(ACCEPT)[0]
    artifact = _artifact(ACCEPT)
    assert artifact["aggregate"]["mass_kg"] == 3.0
    # Independent recomputation of the domain-frame COM from the raw report.
    num = np.zeros(3)
    den = 0.0
    for row in report["body_groups"]:
        R = np.asarray(row["body_frame"]["domain_from_body"]["rotation"], float)
        o = np.asarray(row["body_frame"]["domain_from_body"]["origin_m"], float)
        m = float(row["mass_properties"]["mass"]["value"])
        com_body = np.asarray(row["mass_properties"]["center_of_mass"]["value"], float)
        num += m * (R @ com_body + o)
        den += m
    expected_com = num / den
    got = np.asarray(artifact["aggregate"]["center_of_mass_domain_m"], float)
    assert np.allclose(got, expected_com, rtol=0.0, atol=1e-15)
    # Inertia: 3x3, symmetric, positive definite.
    inertia = np.asarray(
        artifact["aggregate"]["inertia_about_aggregate_com_domain_kg_m2"], float)
    assert inertia.shape == (3, 3)
    assert np.allclose(inertia, inertia.T, rtol=0.0, atol=0.0)
    assert np.all(np.linalg.eigvalsh(inertia) > 0.0)


def test_single_body_aggregate_recovers_rotated_properties_exactly() -> None:
    # CON-16 self-check: aggregating ONE rotated body must recover exactly
    # com_domain = R·com + origin and I_domain = R·I·Rᵀ (CON-10, never repaired).
    report = validator.load_json_file(ACCEPT)[0]
    single = copy.deepcopy(report)
    single["body_groups"] = [row for row in single["body_groups"]
                             if row["body_id"] == "coupon-body-B"]
    artifact, refusal = validator.verify_con16_aggregate(single)
    assert refusal is None, refusal
    row = single["body_groups"][0]
    R = np.asarray(row["body_frame"]["domain_from_body"]["rotation"], float)
    o = np.asarray(row["body_frame"]["domain_from_body"]["origin_m"], float)
    props = row["mass_properties"]
    com_body = np.asarray(props["center_of_mass"]["value"], float)
    I_body = np.asarray(props["inertia_tensor_about_com"]["value"], float)
    assert artifact["aggregate"]["mass_kg"] == float(props["mass"]["value"])
    assert np.allclose(np.asarray(artifact["aggregate"]["center_of_mass_domain_m"]),
                       R @ com_body + o, rtol=0.0, atol=1e-15)
    assert np.allclose(
        np.asarray(artifact["aggregate"]["inertia_about_aggregate_com_domain_kg_m2"]),
        R @ I_body @ R.T, rtol=0.0, atol=1e-12)


def test_error_accounting_present() -> None:
    artifact = _artifact(ACCEPT)
    accounting = artifact["error_accounting"]
    assert accounting["bodies_aggregated"] == 2
    assert accounting["tolerance"] == validator.ORTHONORMALITY_TOL
    assert accounting["orthonormality_residual_max"] <= validator.ORTHONORMALITY_TOL
    assert len(accounting["displacement_norms_m"]) == 2
    assert all(d >= 0.0 for d in accounting["displacement_norms_m"])


def test_aggregate_refuses_cross_body_ownership_overlap() -> None:
    # CON-16(b): one mass owner per cell. A report whose two exported bodies
    # both claim cell-A can still pass per-body validation (R11 is per-body),
    # but the aggregation MUST refuse it, naming the cell and both owners.
    report = validator.load_json_file(ACCEPT)[0]
    body_b = report["body_groups"][1]
    body_b["owned_cell_ids"] = ["cell-B", "cell-A"]
    body_b["cell_provenance"].append(
        {"cell_id": "cell-A", "mass_owner_id": "owner-B", "region_id": "region-B",
         "material_id": "tissue-B", "density_kg_m3": 6.0,
         "density_source": "analytic coupon fixture", "density_conditions": "uniform"})
    verdict = validator.validate_report(report)
    assert verdict["verdict"] == "ACCEPT"  # per-body rules alone do not see it
    artifact, refusal = validator.verify_con16_aggregate(report)
    assert artifact is None and refusal is not None
    assert "ownership_not_disjoint" in refusal
    assert "cell-A" in refusal and "owner-A" in refusal and "owner-B" in refusal


def test_aggregate_refuses_non_accepted_report() -> None:
    report = validator.load_json_file(FIXTURES / "reject_partial.json")[0]
    artifact, refusal = validator.verify_con16_aggregate(report)
    assert artifact is None
    assert "report_not_accepted" in refusal


def test_aggregate_never_mutates_the_report() -> None:
    report = validator.load_json_file(ACCEPT)[0]
    before = json.dumps(report, sort_keys=True)
    validator.verify_con16_aggregate(report)
    assert json.dumps(report, sort_keys=True) == before


def test_validation_verdict_carries_no_aggregate_math() -> None:
    # Separation: the validation verdict never silently expands into aggregate
    # output (CON-16 is a separate, explicit entry point).
    verdict = validator.validate_report(validator.load_json_file(ACCEPT)[0])
    for key in verdict:
        assert "con16" not in key and "aggregate" not in key


def test_cli_aggregate_flag(tmp_path) -> None:
    import subprocess
    import sys
    tool = tmp_path.parent / ".." / "nonexistent"  # unused; CLI run below
    from test_validator import AGENT_DIR
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    result = subprocess.run(
        [sys.executable, str(AGENT_DIR / "rigid_body_mass_consumption_validator.py"),
         str(ACCEPT), "--verify-aggregate"],
        capture_output=True, env=env)
    assert result.returncode == 0
    payload = json.loads(result.stdout.decode("utf-8"))
    assert payload["con16_verification_aggregate"] is not None
    assert payload["con16_aggregate_refusal"] is None
