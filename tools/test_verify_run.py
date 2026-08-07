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


def _write_log(tmp_path: Path, name: str, body: str) -> Path:
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return p


def test_cluster_split_body_2(tmp_path: Path) -> None:
    log = """======================================================================
THE KERNEL - CLUSTER TEST
======================================================================
FALSIFIERS:
  (a) LIFT    - main: load end rises >= 0.10 absolute z
  (d) INTEGRITY - one cluster each
======================================================================

Derived d_eq   = 0.04840

[test] N=100
[test] dt=0.0005 ticks=200 sample_every=100

[test] tick=     0 | load_gain=+0.0000 | angle=  0.00deg | gap=0.0500 | contact=-10.000 | clusters=1/1/1/1/1
[test] tick=   100 | load_gain=-0.0100 | angle=  1.00deg | gap=0.0500 | contact=-10.000 | clusters=1/1/1/1/1
[test] tick=   200 | load_gain=-0.0200 | angle=  2.00deg | gap=0.0500 | contact=-10.000 | clusters=1/1/2/1/1

[test] TEST FALSIFIERS:
  (a) LIFT      : FAIL  max load_gain=0.0000
  (d) INTEGRITY : FAIL  max clusters 1/1/2/1/1
======================================================================
"""
    path = _write_log(tmp_path, "cluster_test.txt", log)
    parsed = verify_run.parse_log(path)
    metrics = verify_run.recompute_metrics(parsed)
    splits = {s["body"]: s for s in metrics["cluster_splits"]}
    assert 2 in splits
    assert splits[2]["max"] == 2
    assert splits[2]["first_tick"] == 200
    verdicts = verify_run.check_verdicts(parsed, metrics)
    integrity = next(v for v in verdicts if v["name"] == "INTEGRITY")
    assert integrity["agree"] == "AGREE"


def test_spine_tilt_breach(tmp_path: Path) -> None:
    log = """======================================================================
THE KERNEL - SPINE TEST
======================================================================
FALSIFIERS:
  (f) FRAME - sacrum axis stays within 2 deg of vertical
======================================================================

Derived d_eq   = 0.04840

[spine] N=100
[spine] dt=0.0005 ticks=200 sample_every=100

[spine] tick=     0 | load_gain=+0.0000 | angle=  0.00deg | gap=0.0500 | contact=-10.000 | clusters=1/1/1 | sacrum_tilt=1.0deg | base_migration=0.0000
[spine] tick=   100 | load_gain=-0.0100 | angle=  1.00deg | gap=0.0500 | contact=-10.000 | clusters=1/1/1 | sacrum_tilt=2.1deg | base_migration=0.0000
[spine] tick=   200 | load_gain=-0.0200 | angle=  2.00deg | gap=0.0500 | contact=-10.000 | clusters=1/1/1 | sacrum_tilt=3.5deg | base_migration=0.0000

[spine] SPINE FALSIFIERS:
  (f) FRAME : FAIL  max sacrum_tilt=3.5deg (bar 2.0) max base_migration=0.0000 (bar 0.0242)
======================================================================
"""
    path = _write_log(tmp_path, "spine_tilt.txt", log)
    parsed = verify_run.parse_log(path)
    metrics = verify_run.recompute_metrics(parsed)
    assert metrics["tilt_breach"] is True
    assert metrics["max_sacrum_tilt"] == pytest.approx(3.5, abs=0.01)
    verdicts = verify_run.check_verdicts(parsed, metrics)
    frame = next(v for v in verdicts if v["name"] == "FRAME")
    assert frame["agree"] == "AGREE"


def test_250_body_cluster_vector(tmp_path: Path) -> None:
    parts = ["1"] * 250
    parts[150] = "2"
    cluster_str = "/".join(parts)
    sample = f"[big] tick=     0 | clusters={cluster_str}"
    log = f"""======================================================================
THE KERNEL - BIG CLUSTER TEST
======================================================================
FALSIFIERS:
  (d) INTEGRITY - one cluster each
======================================================================

[big] N=100
[big] dt=0.0005 ticks=0 sample_every=0

{sample}

[big] BIG FALSIFIERS:
  (d) INTEGRITY : FAIL  max clusters body 150
======================================================================
"""
    path = _write_log(tmp_path, "big_cluster.txt", log)
    parsed = verify_run.parse_log(path)
    metrics = verify_run.recompute_metrics(parsed)
    assert len(metrics["cluster_body_max"]) == 250
    splits = {s["body"]: s for s in metrics["cluster_splits"]}
    assert 150 in splits
    assert splits[150]["max"] == 2


def test_verdict_h_parsed(tmp_path: Path) -> None:
    log = """======================================================================
THE KERNEL - H TEST
======================================================================
FALSIFIERS:
  (a) LIFT    - main: load end rises >= 0.10
  (b) HOLD    - control: load end rises <= 0.05
  (c) BALANCE - settled sign matches sign(R_true - 1)
  (d) INTEGRITY - one cluster each
  (e) SAG     - sag detected
  (f) SLACK   - slack <= 0.20
  (g) FRAME   - sacrum axis stays within 2 deg
  (h) EXTRA   - custom falsifier
======================================================================

Derived d_eq   = 0.04840
Derived R_true = 1.500

[h] N=100
[h] dt=0.0005 ticks=200 sample_every=100

[h] tick=     0 | load_gain=+0.0000 | angle=  0.00deg | gap=0.0500 | contact=-10.000 | clusters=1/1/1/1
[h] tick=   100 | load_gain=-0.0100 | angle=  1.00deg | gap=0.0500 | contact=-10.000 | clusters=1/1/1/1
[h] tick=   200 | load_gain=-0.0200 | angle=  2.00deg | gap=0.0500 | contact=-10.000 | clusters=1/1/1/1

[h] H FALSIFIERS:
  (a) LIFT      : FAIL  max load_gain=0.0000
  (b) HOLD      : skipped (control)
  (c) BALANCE   : PASS  R_true=1.500 settled_angle_sign=1 predicted=1
  (d) INTEGRITY : PASS  max clusters 1/1/1/1
  (e) SAG       : not detected
  (f) SLACK     : PASS
  (g) FRAME     : PASS
  (h) EXTRA     : PASS
======================================================================
"""
    path = _write_log(tmp_path, "h_test.txt", log)
    parsed = verify_run.parse_log(path)
    letters = {v["letter"] for v in parsed["verdicts"]}
    assert "h" in letters
    metrics = verify_run.recompute_metrics(parsed)
    verdicts = verify_run.check_verdicts(parsed, metrics)
    assert len(verdicts) == 8
    h = next(v for v in verdicts if v["letter"] == "h")
    assert h["agree"] == "UNCHECKED"
