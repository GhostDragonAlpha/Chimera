"""Preregistered, configurable aspect/scale bounds for the compiler (Charset: ASCII).

The compiler NEVER silently "repairs" an implausible scale: when a fitted (resolved)
segment's per-axis scale lies outside the declared bounds it is either REFUSED
(Refusal 'aspect_out_of_bounds') or FLAGGED (residual aspect_flag.<body> + segment
status 'flagged_aspect'), depending on the profile. The bounds are preregistered here
so a reader can see exactly what was enforced on a given run; the fit receives a
profile dict (default = the original compiler's unbounded behaviour) plus optional
overrides.

Default profile (LEGACY): the v1 compiler had NO bounds and accepted the 7.155 x hand
scale. To preserve F1-F7 exactly, the unbounded profile is the default; the actual
fit and its regressions pass an explicit profile.

Structure:
    PROFILE = {
        "max_magnitude": float | None,   # max |scale| axis on any segment
        "min_magnitude": float | None,   # min |scale| axis
        "max_aspect":    float | None,   # max(s) / min(s) per segment (implausible stretch)
        "on_violation":  "refuse" | "flag",
    }
"""
from __future__ import annotations

import numpy as np

UNBOUNDED = {
    "max_magnitude": None,
    "min_magnitude": None,
    "max_aspect": None,
    "on_violation": "flag",
}

# The policed profile used for real-geometry fits: a >5x linear scale (125x volume,
# 125x mass at constant density) is treated as evidence of a mis-authored target
# unless the segment's axes are all directly measured. 7.155 (the original hand
# inflation) fails max_magnitude=5; a femur squashed to 1/8 also fails on the floor.
POLICED = {
    "max_magnitude": 5.0,
    "min_magnitude": 0.2,
    "max_aspect": 6.0,
    "on_violation": "refuse",
}

POLICED_FLAG = {**POLICED, "on_violation": "flag"}

PROFILES = {"unbounded": UNBOUNDED, "policed": POLICED, "policed_flag": POLICED_FLAG}


def merge_profile(base: dict | None = None, overrides: dict | None = None) -> dict:
    """Pre-registered profile with optional override keys; unknown profiles refuse."""
    base = dict(UNBOUNDED) if base is None else dict(PROFILES[base] if isinstance(base, str) else base)
    if overrides:
        base.update(overrides)
    if base.get("on_violation") not in ("refuse", "flag"):
        raise ValueError(f"on_violation must be refuse|flag, got {base.get('on_violation')!r}")
    return base


def check_segment(name: str, scale: np.ndarray, profile: dict) -> list[str]:
    """Return a list of violation messages for one resolved segment (empty = ok)."""
    msg: list[str] = []
    s = np.asarray(scale, dtype=np.float64)
    mag = float(np.abs(s).max())
    mn = float(np.abs(s).min())
    if profile.get("max_magnitude") is not None and mag > profile["max_magnitude"]:
        msg.append(f"max|scale| {mag:.4f} > {profile['max_magnitude']}")
    if profile.get("min_magnitude") is not None and mn < profile["min_magnitude"]:
        msg.append(f"min|scale| {mn:.4f} < {profile['min_magnitude']}")
    if profile.get("max_aspect") is not None and mn > 1e-12:
        ar = mag / mn
        if ar > profile["max_aspect"]:
            msg.append(f"axis ratio {ar:.4f} > {profile['max_aspect']}")
    return msg