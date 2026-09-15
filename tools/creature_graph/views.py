"""Three coordinated views projected from the ONE object store.

spatial  -- the body in engine coordinates (joints28 measured frames, band
            boxes, curve endpoints) with TRANSPARENT PLACEHOLDERS for unbuilt
            structures (is_placeholder).
physical -- compartments / membranes / attachments / laws, each membrane with
            its oriented surface and the regions on both sides.
roadmap  -- what exists, what is missing, what blocks it, which experiment
            proves completion (falsifier + acceptance test + evidence).

Selecting an object in any view selects the SAME object in all three: every
projection is keyed by the object id and is computed from the same store, so a
mutation in the store reflects in all three (tested in cli verify).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from schema import REL_ATTACHED, REL_BOUNDS, REL_FORCE, REL_INSIDE, REL_SIGNAL  # noqa: E402


def _place(obj) -> str:
    sp = obj.get("spatial") or {}
    if sp.get("origin"):
        return "origin " + str(sp["origin"])
    if sp.get("endpoints"):
        return "endpoints " + str(sp["endpoints"][0]) + " -> " + str(sp["endpoints"][1])
    if sp.get("band_y"):
        lo, hi = sp["band_y"]
        return f"height band y in [{lo}, {hi}]"
    if sp.get("anchored_to"):
        return "anchored to " + str(sp["anchored_to"])
    return "(no engine placement)"


def spatial_view(g):
    """id -> projection of WHERE it is in engine coordinates, placeholders marked."""
    out = {}
    for oid, obj in g.objects.items():
        if obj.get("spatial") is None and obj.get("kind") not in ("region",):
            continue
        geo = obj.get("geometry") or {}
        out[oid] = {
            "kind": obj["kind"],
            "place": _place(obj),
            "is_placeholder": bool(geo.get("is_placeholder")),
            "shape": geo.get("shape"),
            "draw_as": "transparent-placeholder" if geo.get("is_placeholder") else obj["kind"],
        }
    return out


def physical_view(g):
    """id -> projection of WHAT it is physically: law, both sides, neighbors."""
    out = {}
    for oid, obj in g.objects.items():
        phys = obj.get("physical")
        atts = obj.get("attachments") or []
        force_to = [r["dst"] for r in g.out_edges(oid, REL_FORCE)]
        force_from = [r["src"] for r in g.in_edges(oid, REL_FORCE)]
        signal_to = [r["dst"] for r in g.out_edges(oid, REL_SIGNAL)]
        inside = [r["dst"] for r in g.out_edges(oid, REL_INSIDE)]
        bounds = [r["dst"] for r in g.out_edges(oid, REL_BOUNDS)]
        attached = sorted(set(
            [r["dst"] for r in g.out_edges(oid, REL_ATTACHED)]
            + [r["src"] for r in g.in_edges(oid, REL_ATTACHED)]))
        if phys is None and not (force_to or force_from or signal_to or inside or bounds or attached or atts):
            continue
        out[oid] = {
            "kind": obj["kind"],
            "classification": obj.get("classification"),
            "law": (phys or {}).get("law"),
            "region_a": (phys or {}).get("region_a"),
            "region_b": (phys or {}).get("region_b"),
            "carries": (phys or {}).get("carries"),
            "attachments": atts,
            "inside": inside,
            "bounds": bounds,
            "attached_to": attached,
            "transmits_force_to": force_to,
            "force_from": force_from,
            "carries_signal_to": signal_to,
            "status": obj["status"],
        }
    return out


def roadmap_view(g):
    """id -> projection of BUILD STATE: exists/missing, blockers, proof."""
    from queries import blockers_of  # local import, no cycle at module load
    out = {}
    for oid, obj in g.objects.items():
        fz = obj.get("falsifier") or {}
        ev = [r["dst"] for r in g.out_edges(oid, "verified_by")]
        en = g.enables(oid)
        reqs = g.requires(oid)
        out[oid] = {
            "status": obj["status"],
            "priority": obj.get("priority"),
            "build_rank": obj.get("build_rank"),
            "dependencies": reqs,
            "blockers": blockers_of(g, oid),
            "falsifier": fz.get("statement"),
            "acceptance_test": fz.get("acceptance_test"),
            "falsifier_status": fz.get("status", "untested"),
            "evidence": ev,
            "enables": en,
            "inventory_anchor": obj.get("inventory_anchor"),
        }
    return out


def select(g, oid: str) -> dict:
    """Selecting in any view = the same object in all three, plus the four
    questions the design demands: where it belongs, what it must do, what
    blocks it, what would prove it."""
    obj = g.get(oid)
    return {
        "id": oid,
        "name": obj.get("name"),
        "where_it_belongs": spatial_view(g).get(oid, {"place": "(not spatial)"},
                                                ) if False else spatial_view(g).get(oid),
        "what_it_must_do": physical_view(g).get(oid),
        "build_state": roadmap_view(g).get(oid),
        "must_do_law": (obj.get("physical") or {}).get("law"),
        "unknowns": obj.get("unknowns") or [],
        "player_moment": (obj.get("physical") or {}).get("player_moment"),
    }


def layout_roadmap(g):
    """Deterministic roadmap graph-layout positions, stored SEPARATELY from
    physical positions: tier = build order rank (verified/existing first),
    x = alphabetical slot inside the tier."""
    tiers = {}
    for oid, obj in g.objects.items():
        if obj["status"] == "verified":
            tier = 0
        elif obj.get("build_rank") is not None:
            tier = int(obj["build_rank"])
        else:
            tier = 9
        tiers.setdefault(tier, []).append(oid)
    layout = {}
    for tier in sorted(tiers):
        for x, oid in enumerate(sorted(tiers[tier])):
            layout[oid] = {"roadmap_tier": tier, "roadmap_x": x}
    return layout
