"""B3 — the tensile chain reference model (preregistration c3fb2152).

A chain of members and bonds in series under one pull carries the SAME
force in every link. Each link has capacity = strength x its own
load-bearing area:

    member: capacity = yield_material * area
    bond:   capacity = cure_strength  * area

The chain fails the moment the pull reaches the SMALLEST capacity, and
the failure lands on exactly that link — the weakest link fails first,
at its own capacity (spec battery B3: failure is computed, never
scripted). Cure strength is per-bond data and is REQUIRED for bonds —
never defaulted (operator law: properties must be known). Member yields
come from the sourced constants table.
"""
from __future__ import annotations

from tools.matter_kernel.constants import lookup


class ChainRefused(Exception):
    """A named refusal: nothing is computed, and the model says why."""


def _link_capacity(link: dict) -> tuple[float, str, dict]:
    """One link's capacity in newtons, plus its name and record.
    Refuses loudly on any malformed link."""
    if not isinstance(link, dict):
        raise ChainRefused(f"invalid_link: {link!r} is not a link object")
    name = link.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ChainRefused("invalid_link: every link needs a name")
    kind = link.get("kind")
    if kind not in ("member", "bond"):
        raise ChainRefused(f"invalid_link: {name!r} kind must be "
                           f"'member' or 'bond', got {kind!r}")
    area = link.get("area_m2")
    if area is None or not isinstance(area, (int, float)) or area <= 0:
        raise ChainRefused(f"invalid_area: link {name!r} area {area!r} "
                           f"must be positive square meters")
    mat = lookup(link.get("material"))
    if kind == "bond":
        cure = link.get("cure_strength_pa")
        if cure is None or not isinstance(cure, (int, float)) or cure <= 0:
            raise ChainRefused(f"invalid_cure: bond {name!r} needs a "
                               f"positive per-bond cure strength in Pa")
        return cure * area, name, {"capacity_n": cure * area,
                                   "strength_pa": cure,
                                   "area_m2": float(area)}
    return mat["yield"] * area, name, {"capacity_n": mat["yield"] * area,
                                       "strength_pa": mat["yield"],
                                       "area_m2": float(area)}


def pull_chain(links: list, force_n: float) -> dict:
    """Pull a series chain. Returns the outcome: holds (with safety
    factor) or fails at the weakest link, at exactly that link's
    capacity — computed from the constants, never scripted."""
    if force_n is None or not isinstance(force_n, (int, float)):
        raise ChainRefused("force_required: force in newtons is a "
                           "required input, never defaulted")
    if force_n <= 0:
        raise ChainRefused(f"invalid_force: {force_n!r} must be positive")
    if not isinstance(links, list) or not links:
        raise ChainRefused("empty_chain: a chain needs at least one link")

    capacities = [_link_capacity(link) for link in links]
    # deterministic argmin; first-weakest wins an exact tie
    weakest = min(range(len(capacities)), key=lambda i: capacities[i][0])
    fail_force = capacities[weakest][0]

    holds = force_n < fail_force
    link_report = {name: rec for _, name, rec in capacities}
    return {
        "holds": holds,
        "site": None if holds else capacities[weakest][1],
        "failure_force_n": fail_force,
        "safety_factor": fail_force / force_n,
        "force_n": float(force_n),
        "links": link_report,
    }
