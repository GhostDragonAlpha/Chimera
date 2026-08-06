"""
Tests for LightEngine/queue_runner.py.

These keep the anti-sweep gate honest: no concept runs without a falsifier_ref,
batches are uniform-N, and the ledger schema is stable.
"""

import json
import os
import tempfile

import pytest

from LightEngine import queue_runner


def _write_tmp_manifest(entries):
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(entries, f)
    return path


def test_manifest_validation_refuses_missing_falsifier_ref():
    """An entry without falsifier_ref must be refused (anti-sweep gate)."""
    entries = [{
        "id": "bad_concept",
        "category": "test",
        "structure": "random",
        "geometry": {},
        "seed": 0,
        "n": 64,
        # falsifier_ref intentionally omitted
    }]
    path = _write_tmp_manifest(entries)
    with pytest.raises(ValueError) as excinfo:
        queue_runner.load_manifest(path)
    assert "falsifier_ref" in str(excinfo.value)


def test_manifest_validation_refuses_empty_falsifier_ref():
    entries = [{
        "id": "bad_concept",
        "category": "test",
        "structure": "random",
        "geometry": {},
        "seed": 0,
        "n": 64,
        "falsifier_ref": "",
    }]
    path = _write_tmp_manifest(entries)
    with pytest.raises(ValueError) as excinfo:
        queue_runner.load_manifest(path)
    assert "no falsifier_ref" in str(excinfo.value)


def test_grouping_enforces_uniform_n():
    """Mixed-N entries must be split into separate batches; solo entries skipped."""
    entries = [
        {"id": "a", "n": 64, "runner": "batch"},
        {"id": "b", "n": 64, "runner": "batch"},
        {"id": "c", "n": 128, "runner": "batch"},
        {"id": "d", "n": 64, "runner": "solo"},
    ]
    groups = queue_runner.group_by_n(entries)
    assert set(groups.keys()) == {64, 128}
    assert [e["id"] for e in groups[64]] == ["a", "b"]
    assert [e["id"] for e in groups[128]] == ["c"]


def test_ledger_write_schema():
    """write_ledger appends rows and preserves the expected schema."""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    rows = [
        {
            "id": "test_1",
            "batch_id": "N64_B1",
            "verdict": "PASS",
            "reasons": [],
            "metrics": {"final_bound_frac": 0.75},
            "n": 64,
            "ticks": 100,
            "wall_seconds": 0.1,
            "timestamp": queue_runner._now(),
            "diagnostic_note": None,
        }
    ]
    queue_runner.write_ledger(rows, path)
    with open(path, "r", encoding="utf-8") as f:
        ledger = json.load(f)
    assert len(ledger) == 1
    row = ledger[0]
    for key in ("id", "batch_id", "verdict", "metrics", "n", "ticks",
                "wall_seconds", "timestamp"):
        assert key in row


def test_build_cushion_cube_shape():
    pos, vel = queue_runner._build_cushion_cube(side=3, spacing=0.05, seed=0)
    assert pos.shape == (27, 3)
    assert vel.shape == (27, 3)
    # all velocities zero (cold print)
    assert pytest.approx(vel.sum(), abs=1e-6) == 0.0


def test_build_packed_bed_count():
    pos, vel = queue_runner._build_packed_bed(n=125, spacing=0.15, seed=7)
    assert pos.shape[0] == 125
    assert vel.shape[0] == 125


def test_concept_verdict_settled_translation():
    """Intended mono-condensed equilibrium must not read COLLAPSE as failure."""
    verdict, std = queue_runner._concept_verdict(
        "COLLAPSE", "mono_condensed", final_max=100, final_bound=1.0,
        cluster_cv=0.0, n=100)
    assert verdict == "SETTLED"
    assert std == "COLLAPSE"
    # a flickering mono-cluster does NOT earn SETTLED
    verdict, std = queue_runner._concept_verdict(
        "COLLAPSE", "mono_condensed", final_max=100, final_bound=1.0,
        cluster_cv=0.5, n=100)
    assert verdict == "COLLAPSE"
    assert std is None
    # no expectation declared: standard verdict passes through
    verdict, std = queue_runner._concept_verdict(
        "COLLAPSE", None, final_max=100, final_bound=1.0,
        cluster_cv=0.0, n=100)
    assert verdict == "COLLAPSE"
    assert std is None
