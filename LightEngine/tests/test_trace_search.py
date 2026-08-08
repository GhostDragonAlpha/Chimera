"""Tests for trace_search -- the two searches of operator datum 7:
find the beginning and the end; read everything between them."""

from __future__ import annotations

import numpy as np

from LightEngine.trace_search import find_bounds, read_interval, search_event


def test_no_crossing_is_none():
    # a signal that never crosses has no event: None, not index 0
    assert find_bounds(np.zeros(100), 1.0) is None
    assert find_bounds(np.ones(50), 0.5, side="below") is None
    assert find_bounds([], 0.0) is None
    assert search_event(np.zeros(10), 1.0) is None


def test_beginning_is_first_crossing():
    x = np.zeros(100)
    x[37:] = 1.0
    assert find_bounds(x, 0.5) == (37, 99)


def test_pulse_has_both_bounds():
    x = np.zeros(100)
    x[20:45] = 3.0
    assert find_bounds(x, 1.0) == (20, 44)


def test_event_that_never_returns_runs_to_the_end():
    # the fall that does not recover: end == the trace's last index
    x = np.linspace(0.0, 2.0, 200)
    assert find_bounds(x, 1.0) == (100, 199)


def test_side_below():
    x = np.ones(80)
    x[10:30] = -0.5
    assert find_bounds(x, 0.0, side="below") == (10, 29)


def test_read_interval_absolute_indices():
    x = np.zeros(100)
    x[20] = -2.0   # interior minimum
    x[60] = 5.0    # interior maximum
    r = read_interval(x, 10, 70)
    assert r["count"] == 61
    assert r["argmin"] == 20
    assert r["argmax"] == 60
    assert r["min"] == -2.0
    assert r["max"] == 5.0
    assert r["first"] == 0.0
    assert r["last"] == 0.0


def test_read_interval_slope_and_sign():
    x = np.arange(50, dtype=np.float64) + 1.0  # +1 slope, all positive
    r = read_interval(x, 0, 49)
    assert abs(r["slope"] - 1.0) < 1e-12
    assert r["sign_consistency"] == 1.0
    assert r["growth"] == 50.0
    x0 = np.arange(10, dtype=np.float64)
    assert read_interval(x0, 0, 9)["growth"] == float("inf")  # first == 0


def test_search_event_composes():
    x = np.zeros(60)
    x[5:25] = np.linspace(1.0, 2.0, 20)
    r = search_event(x, 0.5)
    assert r is not None
    assert r["begin"] == 5
    assert r["end"] == 24
    assert r["count"] == 20
    assert r["first"] == 1.0
    assert r["last"] == 2.0


def test_empty_interval_raises():
    try:
        read_interval(np.zeros(10), 20, 30)
    except ValueError:
        return
    raise AssertionError("empty interval must raise")
