"""B2 — the glue reference model (preregistration 1ef3fff1).

A bond is a THIRD material between two membranes: the glue, with its own
cure strength, independent of the members it joins. Under a pull, every
load path carries capacity = strength x its own load-bearing area, and
the line with the SMALLEST capacity fails first:

    F_fail = min(cure * A_glue, yield_a * A_a, yield_b * A_b)

Two steel membranes with weak glue fail AT the glue line (spec battery
B2): the steel sits far below its own yield when the bond lets go.
Cure strength is per-bond data (KERNEL_SPEC.md 2) and is REQUIRED —
never defaulted (operator law: force and properties must be known).
Member yields come from the sourced constants table.
"""
from __future__ import annotations

from tools.matter_kernel.constants import lookup


class GlueRefused(Exception):
    """A named refusal: nothing is computed, and the model says why."""


def pull_bond(member_a: str, member_b: str, glue_area_m2: float,
              member_area_a: float, member_area_b: float,
              cure_strength_pa: float, force_n: float) -> dict:
    """Pull one bonded joint along its bond line. Returns the outcome:
    holds (with safety factor) or fails at the weakest line, which for
    a weak glue is the glue line itself, never the members."""
    if force_n is None or not isinstance(force_n, (int, float)):
        raise GlueRefused("force_required: force in newtons is a "
                          "required input, never defaulted")
    if force_n <= 0:
        raise GlueRefused(f"invalid_force: {force_n!r} must be positive")
    if cure_strength_pa is None or not isinstance(cure_strength_pa, (int, float)) \
            or cure_strength_pa <= 0:
        raise GlueRefused(f"invalid_cure: {cure_strength_pa!r} must be a "
                          f"positive per-bond cure strength in Pa")
    for label, area in (("glue", glue_area_m2),
                        ("member_a", member_area_a),
                        ("member_b", member_area_b)):
        if area is None or not isinstance(area, (int, float)) or area <= 0:
            raise GlueRefused(f"invalid_area: {label} area {area!r} must "
                              f"be positive square meters")

    ma, mb = lookup(member_a), lookup(member_b)

    cap_glue = cure_strength_pa * glue_area_m2
    cap_a = ma["yield"] * member_area_a
    cap_b = mb["yield"] * member_area_b
    # deterministic argmin; glue line checked first so an exact tie
    # names the bond, the honest reading of simultaneous failure
    capacities = [("glue_line", cap_glue),
                  (member_a, cap_a),
                  (member_b, cap_b)]
    site, fail_force = min(capacities, key=lambda kv: kv[1])

    failure_stress = fail_force / glue_area_m2
    holds = force_n < fail_force
    return {
        "holds": holds,
        "site": None if holds else site,
        "failure_force_n": fail_force,
        "safety_factor": fail_force / force_n,
        "force_n": float(force_n),
        "factors": {
            "glue_capacity_n": cap_glue,
            "member_a_capacity_n": cap_a,
            "member_b_capacity_n": cap_b,
            "weakest_line_stress_pa": failure_stress,
            "cure_strength_pa": float(cure_strength_pa),
            "glue_area_m2": float(glue_area_m2),
            "member_a_yield_pa": ma["yield"],
            "member_b_yield_pa": mb["yield"],
            "member_a_source": ma["source"],
            "member_b_source": mb["source"],
        },
    }
