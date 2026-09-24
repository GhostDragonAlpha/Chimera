"""W6 delta W6-EXIT (M06-H04, decided): promoted validation CLI exit classes.

M06-H04: "For the promoted validation CLI, use 0 for accepted static validation,
2 for named input/status refusal, 1 for unexpected internal failure."

Compatibility: the original M10 tool (campaign artifact) keeps 0/1/2 =
accept/reject/could-not-evaluate; the promoted tool carries the decided mapping.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")

import pytest  # noqa: E402

import rigid_body_mass_consumption_validator as validator  # noqa: E402
from test_validator import AGENT_DIR, FIXTURES, ACCEPT  # noqa: E402

TOOL = AGENT_DIR / "rigid_body_mass_consumption_validator.py"


def _run(*args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run([sys.executable, str(TOOL), *args],
                          capture_output=True, env=env)


def test_cli_accepted_static_validation_exits_zero() -> None:
    result = _run(str(ACCEPT))
    assert result.returncode == 0
    assert b'"verdict": "ACCEPT"' in result.stdout


def test_cli_status_refusal_exits_two() -> None:
    # A named status refusal (partial, decided D2) — was exit 1 under M10.
    result = _run(str(FIXTURES / "reject_partial.json"))
    assert result.returncode == 2
    assert b'"verdict": "REJECT"' in result.stdout
    assert b"partial_rejected" in result.stdout


def test_cli_named_input_refusal_exits_two() -> None:
    result = _run(str(FIXTURES / "no_such_file.json"))
    assert result.returncode == 2
    assert b"could_not_evaluate" in result.stderr


def test_cli_unexpected_internal_failure_exits_one(monkeypatch) -> None:
    def _explode(*_a, **_k):
        raise RuntimeError("injected internal failure")
    monkeypatch.setattr(validator, "validate_file", _explode)
    code = validator.main([str(ACCEPT)])
    assert code == 1  # was uncaught under M10's main; never exit 0 or 2


def test_cli_usage_error_exits_two() -> None:
    # argparse usage errors are named input refusals -> 2 (argparse default).
    result = _run()
    assert result.returncode == 2


def test_cli_carries_identity_note() -> None:
    result = _run("--version")
    out = result.stdout.decode("utf-8", "replace")
    assert result.returncode == 0
    assert "rigid_body_mass_consumption_validator" in out
    assert "W6" in out
    assert "0" in out and "2" in out and "1" in out  # exit-class contract stated
    assert "v1.0" in out  # reconciled contract version
    help_text = _run("--help").stdout.decode("utf-8", "replace")
    assert "exit 0" in help_text and "exit 2" in help_text and "exit 1" in help_text
