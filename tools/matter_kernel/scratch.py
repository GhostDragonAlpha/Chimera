"""B1 — the scratch reference model (preregistration 111a82f6).

Pressure is PINNED at the softer material's hardness: the softer surface
yields until its load-bearing area carries the applied force at exactly
that pressure; the harder member never yields because the pinned pressure
sits below its own hardness. Groove depth for a round tip:

    d = F / (2 * pi * R * H_soft)      (d << R, projected area ~ pi*2Rd)

Force in newtons is a REQUIRED input (operator law 2026-09-12: how much
force you put on the object must be known) — omitted force refuses.
Hardness values come from the sourced constants table; the HV -> Pa
conversion is 9.80665 MPa per HV unit.
"""
from __future__ import annotations

import math

from tools.matter_kernel.constants import lookup

HV_TO_PA = 9.80665e6  # 1 kgf/mm^2 = 9.80665 MPa


class ScratchRefused(Exception):
    """A named refusal: no cut happens, and the model says why."""


def scratch(tip_material: str, plate_material: str, force_n: float,
            tip_radius_m: float) -> dict:
    """Compute one scratch. Returns groove geometry on the member that
    yields; refuses (raises) when the ordering law says no cut occurs."""
    if force_n is None or not isinstance(force_n, (int, float)):
        raise ScratchRefused("force_required: force in newtons is a "
                             "required input, never defaulted")
    if force_n <= 0:
        raise ScratchRefused(f"invalid_force: {force_n!r} must be positive")
    if tip_radius_m is None or tip_radius_m <= 0:
        raise ScratchRefused("invalid_tip_radius: must be positive meters")

    mt, mp = lookup(tip_material), lookup(plate_material)
    h_tip = mt["hardness_vickers"] * HV_TO_PA
    h_plate = mp["hardness_vickers"] * HV_TO_PA

    if h_tip <= h_plate:
        raise ScratchRefused(
            "no_cut_ordering: tip hardness "
            f"({mt['hardness_vickers']} HV) does not exceed plate hardness "
            f"({mp['hardness_vickers']} HV); neither member yields")

    # ordering holds: the plate is the softer member and takes the groove.
    # Contact pressure pins at the plate's hardness; the tip sees exactly
    # that pressure — h_plate < h_tip, so the tip cannot yield.
    depth = force_n / (2.0 * math.pi * tip_radius_m * h_plate)
    width = 2.0 * math.sqrt(max(tip_radius_m * depth, 0.0))  # chord at depth
    tip_depth = 0.0  # pinned pressure (h_plate) is below the tip's hardness
    return {
        "yields": plate_material,
        "groove_depth_m": depth,
        "groove_width_m": width,
        "tip_damage_m": tip_depth,
        "pinned_pressure_pa": h_plate,
        "force_n": float(force_n),
        "tip_radius_m": float(tip_radius_m),
        "factors": {
            "tip_hardness_pa": h_tip, "plate_hardness_pa": h_plate,
            "hardness_ratio": round(h_tip / h_plate, 3),
            "tip_source": mt["source"], "plate_source": mp["source"],
        },
    }
