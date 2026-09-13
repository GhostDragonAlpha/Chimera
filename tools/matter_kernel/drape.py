"""B4 — the tension-only drape reference model (preregistration 06be7c05).

A membrane carries load in TENSION ONLY. A cloth dropped on a
frictionless horizontal rail drapes iff it can reach the rail's two
vertical tangent lines: free membrane segments hang EXACTLY vertical,
so lift-off sits at the equator and the threshold is exact:

    drape  iff  W_c >= pi * R

The excess (W_c - pi*R) hangs at the two lift-off lines; every tension
is >= 0; material is conserved exactly; the rail carries the whole
cloth weight. All values are per unit rail length (2D membrane).
Gravity g is a REQUIRED input (a known force, never defaulted).
"""
from __future__ import annotations

import math


class DrapeRefused(Exception):
    """A named refusal: nothing is computed, and the model says why."""


def drape_rail(cloth_width_m: float, rail_radius_m: float,
               areal_density_kgm2: float, g_mps2: float | None) -> dict:
    """Settle one cloth on one frictionless rail. Returns the drape:
    contact arc, lift-off geometry, excess, tensions, and the exact
    load-path breakdown — or a named refusal."""
    if g_mps2 is None or not isinstance(g_mps2, (int, float)) or g_mps2 <= 0:
        raise DrapeRefused("gravity_required: g in m/s^2 is a required "
                           "input — the load must be known, never defaulted")
    if cloth_width_m is None or not isinstance(cloth_width_m, (int, float)) \
            or cloth_width_m <= 0:
        raise DrapeRefused(f"invalid_width: {cloth_width_m!r} must be "
                           f"positive meters")
    if rail_radius_m is None or not isinstance(rail_radius_m, (int, float)) \
            or rail_radius_m <= 0:
        raise DrapeRefused(f"invalid_radius: {rail_radius_m!r} must be "
                           f"positive meters")
    if areal_density_kgm2 is None or not isinstance(areal_density_kgm2, (int, float)) \
            or areal_density_kgm2 <= 0:
        raise DrapeRefused(f"invalid_density: {areal_density_kgm2!r} must "
                           f"be positive kg/m^2")

    contact_full = math.pi * rail_radius_m
    if cloth_width_m < contact_full:
        raise DrapeRefused(
            "cannot_drape: cloth width "
            f"({cloth_width_m:.6g} m) is below the half-circumference "
            f"({contact_full:.6g} m) — on a frictionless rail it slides "
            f"off; no static drape exists")

    excess = cloth_width_m - contact_full
    weight_per_length = areal_density_kgm2 * g_mps2  # N/m^2 -> per unit rail length
    arc_weight = weight_per_length * contact_full    # N/m on the arc
    lift_pull_each = weight_per_length * excess / 2.0  # N/m per lift-off line
    total_support = arc_weight + 2.0 * lift_pull_each
    _expect = weight_per_length * cloth_width_m
    assert abs(total_support - _expect) <= 1e-9 * max(1.0, _expect)

    return {
        "drapes": True,
        "contact_arc_m": contact_full,
        "liftoff_angle_rad": math.pi / 2,  # both sides, exactly
        "excess_m": excess,
        "min_tension_n_per_m": 0.0 if excess == 0 else lift_pull_each,
        "liftoff_tension_each_n_per_m": lift_pull_each,
        "load_path": {
            "arc_weight_n_per_m": arc_weight,
            "liftoff_pulls_n_per_m": 2.0 * lift_pull_each,
            "total_n_per_m": total_support,
            "cloth_weight_n_per_m": weight_per_length * cloth_width_m,
        },
        "factors": {
            "cloth_width_m": float(cloth_width_m),
            "rail_radius_m": float(rail_radius_m),
            "areal_density_kgm2": float(areal_density_kgm2),
            "g_mps2": float(g_mps2),
            "fold_pitch": "OPEN — needs bending stiffness D = E h^3 / "
                          "(12 (1 - nu^2)); no fold count is claimed",
        },
    }
