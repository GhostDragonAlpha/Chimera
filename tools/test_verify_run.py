"""pytest suite for tools/verify_run.py.

Uses the three committed LightEngine fixture logs and a synthetic temp log to
exercise parsing, recomputation, physics-flag detection, and exit-code logic.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

import verify_run


FIXTURES = [
    Path("LightEngine/output/print_leg_v2_log.txt"),
    Path("LightEngine/output/print_lever_v6_log.txt"),
    Path("LightEngine/output/print_leg_v1_log.txt"),
    Path("LightEngine/output/print_leg_v3_log.txt"),
    Path("LightEngine/output/print_leg_v3_control_log.txt"),
]

V3_MAIN = Path("LightEngine/output/print_leg_v3_log.txt")
V3_CONTROL = Path("LightEngine/output/print_leg_v3_control_log.txt")


@pytest.mark.parametrize("path", FIXTURES)
def test_parse_yields_41_samples(path: Path) -> None:
    parsed = verify_run.parse_log(path)
    assert len(parsed["samples"]) == 41


@pytest.mark.parametrize("path", FIXTURES)
def test_settled_sign_matches_balance_verdict(path: Path) -> None:
    parsed = verify_run.parse_log(path)
    metrics = verify_run.recompute_metrics(parsed)
    balance = next(v for v in parsed["verdicts"] if v["name"] == "BALANCE")
    r_true = parsed["derived"]["R_true"]
    predicted = verify_run._sign(r_true - 1.0)
    recomputed = "PASS" if metrics["settled_sign"] == predicted else "FAIL"
    assert recomputed == balance["status"]


def test_leg_v1_droplet_leap() -> None:
    parsed = verify_run.parse_log(FIXTURES[2])
    metrics = verify_run.recompute_metrics(parsed)
    assert metrics["leap"] is True
    assert metrics["apex_range"] is not None
    assert abs(metrics["apex_range"] - 0.0755) < 0.001


def test_leg_v2_main_rod_compression_event() -> None:
    parsed = verify_run.parse_log(FIXTURES[0])
    metrics = verify_run.recompute_metrics(parsed)
    ticks = {e["tick"]: e["force"] for e in metrics["compression_events"]}
    assert 200 in ticks
    assert abs(ticks[200] - (-181.78)) < 0.01


def test_lever_v6_reversal_spike_at_tick_400() -> None:
    parsed = verify_run.parse_log(FIXTURES[1])
    metrics = verify_run.recompute_metrics(parsed)
    assert metrics["reversal_spike"] is not None
    assert metrics["reversal_spike"]["tick"] == 400


def test_exit_code_all_fixtures_agree() -> None:
    result = subprocess.run(
        [sys.executable, "tools/verify_run.py"] + [str(p) for p in FIXTURES],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr


def test_exit_code_one_disagree(tmp_path: Path) -> None:
    original = FIXTURES[0].read_text(encoding="utf-8")
    modified = original.replace(
        "  (c) BALANCE   : FAIL  R_true=1.003 settled_angle_sign=-1 predicted=1 (last 8/41 samples)",
        "  (c) BALANCE   : PASS  R_true=1.003 settled_angle_sign=-1 predicted=1 (last 8/41 samples)",
    )
    fake = tmp_path / "fake_leg_v2.txt"
    fake.write_text(modified, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "tools/verify_run.py", str(fake)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1, result.stdout + "\n" + result.stderr


def test_v3_stops_parsed() -> None:
    for path in (V3_MAIN, V3_CONTROL):
        parsed = verify_run.parse_log(path)
        first = parsed["samples"][0]
        assert "theta_stop_muscle" in first
        assert "theta_stop_load" in first
        assert first["theta_stop_load"] == pytest.approx(-120.0)


def test_v3_main_rope_fractions_match_telemetry() -> None:
    parsed = verify_run.parse_log(V3_MAIN)
    metrics = verify_run.recompute_metrics(parsed)
    assert metrics["rope_fracs"]["tension"] == pytest.approx(0.05, abs=0.02)
    assert metrics["rope_fracs"]["slack"] == pytest.approx(0.95, abs=0.02)
    assert metrics["rope_fracs"]["compression"] == pytest.approx(0.00, abs=0.02)


def test_v3_main_theta_exceedance_flagged() -> None:
    parsed = verify_run.parse_log(V3_MAIN)
    metrics = verify_run.recompute_metrics(parsed)
    assert metrics["theta_exceedance"] is not None
    assert metrics["max_abs_theta"] == pytest.approx(49.22, abs=0.1)


def test_v3_control_no_theta_exceedance() -> None:
    parsed = verify_run.parse_log(V3_CONTROL)
    metrics = verify_run.recompute_metrics(parsed)
    assert metrics["theta_exceedance"] is None
    assert metrics["max_abs_theta"] == pytest.approx(17.07, abs=0.1)
