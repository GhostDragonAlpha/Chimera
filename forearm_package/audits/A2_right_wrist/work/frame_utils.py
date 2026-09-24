"""frame_utils.py — A2 audit copy.

`_unit` and `onb_from_points` are extracted VERBATIM from the baseline
compiler.py (E:/PythonChimera/forearm_package/baseline_snapshot/code/compiler.py
lines 50-71). Extraction (not import) is only because compiler.py imports
schema/correspondence, whose module-level state the audit does not need; the
two functions below are byte-for-byte the baseline definitions except that
Refusal (a correspondence.py exception) is raised as RuntimeError with the
same name/code, which never triggers for the right-forearm roll witness used
here (verified: the call succeeds).
"""
from __future__ import annotations

import numpy as np

FD_EPS = 1e-5
ROLL_EPS = 1e-9


def _unit(v: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(v)
    if n < 1e-15:
        raise ValueError("degenerate vector")
    return v / n


def onb_from_points(p0: np.ndarray, p1: np.ndarray, q: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Proper ONB [a b c] with a = p1-p0 (bone) and b = roll-ref rejected off a."""
    a = _unit(p1 - p0)
    t = (q - p0) - a * (a @ (q - p0))
    if np.linalg.norm(t) < ROLL_EPS:
        raise RuntimeError("axis_parallel_roll: roll reference lies on the bone axis")
    b = _unit(t)
    c = np.cross(a, b)
    if abs(np.linalg.det(np.column_stack([a, b, c])) - 1.0) > 1e-9:
        raise RuntimeError("non_proper_target_frame: ONB construction failed to stay proper")
    return a, b, c
