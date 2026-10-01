"""The six gap queries -- missing information made actionable.

The brief's shapes (2026-09-15):
  1. limb compartments lacking a closed, physically supported boundary
  2. structures that exist only as placeholders
  3. active parameters lacking units / source / applicability
  4. unfinished prerequisites blocking local withdrawal
  5. evidence that would go stale if a given septum or material changed
  6. the next ready task, by explicit authored priority, that enables the most
     relevant player experiment

Tasks follow AUTHORED requirements (kind=requirement); imported reference
facts NEVER become tasks here. Virtual simulator measurements and real-world
measurements are distinguished by the evidence/parameter records themselves
(see `engine` fields vs `conditions.specimen`).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from schema import STATUS_RANK, content_projection  # noqa: E402
from store import content_version  # noqa: E402

AVAILABLE_THRESHOLD = "geometry_built"  # prerequisite exists as buildable geometry


def _is_available(status: str) -> bool:
    return STATUS_RANK.get(status, -1) >= STATUS_RANK[AVAILABLE_THRESHOLD]


# ---------------------------------------------------------------------------
# Q1 -- compartments lacking a closed, physically supported boundary
# ---------------------------------------------------------------------------

def q_unsupported_boundaries(g, classification="type.A1"):
    """Inventory distinct registered boundary support, not geometric closure.
    Even built membranes and a verified object label cannot prove enclosure
    from a graph count alone. Topology and load transfer need measured evidence.
    """
    results = []
    for obj in g.objects.values():
        if obj["kind"] != "volume" or obj.get("classification") != classification:
            continue
        region = (obj.get("physical") or {}).get("region_a")
        walls = []
        seen_walls = set()
        for r in g.relations:
            if r["rel"] != "bounds_region":
                continue
            wall = g.objects.get(r["src"])
            if wall is None or wall["kind"] != "surface":
                continue
            phys = wall.get("physical") or {}
            if (region is not None and r["dst"] == region
                    and wall["id"] not in seen_walls
                    and region in (phys.get("region_a"), phys.get("region_b"))):
                seen_walls.add(wall["id"])
                geo = wall.get("geometry") or {}
                supported = _is_available(wall["status"]) and not geo.get("is_placeholder")
                walls.append({"membrane": wall["id"],
                              "side": "A" if phys.get("region_a") == region else "B",
                              "status": wall["status"],
                              "physically_supported": supported,
                              "shared_wall_with": (phys.get("region_b")
                                                   if phys.get("region_a") == region
                                                   else phys.get("region_a"))})
        n_support = sum(1 for w in walls if w["physically_supported"])
        results.append({
            "compartment": obj["id"],
            "status": obj["status"],
            "region": region,
            "bounding_membranes": walls,
            "distinct_supported_membranes": n_support,
            "closed_by_built_walls": None,  # graph registrations do not prove topology
            "closure_verification": "not established by this inventory query",
            "verdict": ("boundary support registered; closure unverified" if n_support > 0
                        else "boundary pending build" if walls
                        else "NO boundary in the graph"),
            "note": "each membrane appears once per region. Wall count does not "
                    "establish closure or load-bearing behavior; separate measured proof is required",
        })
    return results


# ---------------------------------------------------------------------------
# Q2 -- placeholder-only structures
# ---------------------------------------------------------------------------

def q_placeholder_only(g):
    """Objects whose geometry is a placeholder (no buildable geometry). Types
    are definitions (excluded); work items have no physical extent by design
    (excluded) -- everything else that is only a placeholder is a real gap."""
    out = []
    for obj in g.objects.values():
        if obj["kind"] in ("type", "work"):
            continue
        geo = obj.get("geometry") or {}
        if geo.get("is_placeholder"):
            out.append({"id": obj["id"], "kind": obj["kind"],
                        "status": obj["status"],
                        "name": obj.get("name"),
                        "unknowns": obj.get("unknowns") or []})
    return sorted(out, key=lambda x: x["id"])


# ---------------------------------------------------------------------------
# Q3 -- active parameters lacking units / source / applicability
# ---------------------------------------------------------------------------

def q_params_missing_provenance(g):
    """SELECTED parameters in use must carry units, source, applicability --
    'unknown' is an honest value but still a GAP to close; a model the
    parameter belongs to may also carry open unknowns. Virtual simulator
    measurements are those sourced from the engine/brief (they do not
    independently validate the simulator's material model)."""
    out = []
    for obj in g.objects.values():
        if obj["kind"] != "parameter":
            continue
        in_use = (obj.get("physical") or {}).get("selection_status") == "in_use"
        if not in_use:
            continue
        gaps = []
        if not obj.get("units"):
            gaps.append("no units")
        if not obj.get("source"):
            gaps.append("no source")
        elif "unknown" in (obj.get("source") or "").lower():
            gaps.append("source partly unknown")
        if not obj.get("applicability"):
            gaps.append("no applicability statement")
        if obj.get("validation") in (None, "unchecked against independent reference"):
            gaps.append("not validated against an independent reference "
                        "(virtual-simulator provenance does not count)")
        out.append({"parameter": obj["id"], "value": obj.get("value"),
                    "units": obj.get("units"), "gaps": gaps})
    return sorted(out, key=lambda x: x["parameter"])


# ---------------------------------------------------------------------------
# Q4 -- unfinished prerequisites blocking a goal (local withdrawal)
# ---------------------------------------------------------------------------

def q_blockers_for(g, experience_id="experience.local_withdrawal"):
    """Everything that enables the experience (or requires an enabler before it
    can exist) whose requires_implementation prerequisites are not yet
    available, plus the ready-now work (no blockers) ranked by authored
    priority. Readiness comes ONLY from the prerequisite DAG."""
    from queries import blockers_of  # local import to avoid cycles
    closure = []
    seen = {experience_id}
    frontier = [experience_id]
    while frontier:
        cur = frontier.pop()
        for r in g.in_edges(cur, "enables_player_experience"):
            if r["src"] not in seen:
                seen.add(r["src"])
                frontier.append(r["src"])
                closure.append(r["src"])
    # dependents: things that require an enabler (they are blocked BY the same
    # unfinished prerequisites -- e.g. compartments waiting on their partition)
    frontier = list(closure)
    while frontier:
        cur = frontier.pop()
        for r in g.in_edges(cur, "requires_implementation"):
            if r["src"] not in seen:
                seen.add(r["src"])
                frontier.append(r["src"])
                closure.append(r["src"])
    blocked, ready = [], []
    for oid in closure:
        obj = g.get(oid)
        if obj["kind"] in ("evidence", "type"):
            continue
        if obj["status"] == "verified":
            continue
        blockers = blockers_of(g, oid)
        entry = {"id": oid, "kind": obj["kind"], "status": obj["status"],
                 "blockers": blockers,
                 "authored_priority": obj.get("authored_priority"),
                 "falsifier": (obj.get("falsifier") or {}).get("statement")}
        (ready if not blockers else blocked).append(entry)
    ready.sort(key=lambda e: (e["authored_priority"] is None,
                              e["authored_priority"] or 99, e["id"]))
    blocked.sort(key=lambda e: (len(e["blockers"]), e["id"]))
    return {"experience": experience_id, "ready_now": ready,
            "blocked_by": blocked}


# ---------------------------------------------------------------------------
# Q5 -- evidence at risk if a given object changes
# ---------------------------------------------------------------------------

def q_evidence_at_risk(g, oid):
    """Evidence that would go stale if `oid` changed physically: records that
    captured `oid`'s content version directly, plus (for materials/models)
    records that captured any compartment USING that material/model."""
    g.get(oid)
    at_risk = []
    unknown = []
    for ev in g.evidence_records():
        reasons = g.stale_evidence(ev["id"])
        if reasons:
            unknown.append({"evidence": ev["id"], "reasons": reasons})
        deps = ev.get("deps") or []
        why = []
        if oid in deps:
            why.append("directly measured against it")
        else:
            target = g.get(oid)
            if target["kind"] in ("material", "model"):
                for d in deps:
                    d_obj = g.objects.get(d)
                    if d_obj is None:
                        continue
                    uses = [r["dst"] for r in g.out_edges(d, "uses_material")]
                    uses += [r["dst"] for r in g.out_edges(d, "uses_model")]
                    if oid in uses:
                        why.append(f"measured against {d} which uses it")
                        break
        if why:
            at_risk.append({"evidence": ev["id"],
                            "validation": ev.get("validation", "untested"),
                            "why": why[0]})
    return {"if_changed": oid, "evidence_records_considered": len(g.evidence_records()),
            "at_risk": at_risk, "unverifiable_captures": unknown,
            "coverage": "no evidence" if not g.evidence_records() else
                        "incomplete" if unknown else "captured declared scope only"}


# ---------------------------------------------------------------------------
# Q6 -- next ready task by explicit authored priority
# ---------------------------------------------------------------------------

def q_next_ready_task(g, experience_id="experience.local_withdrawal"):
    """Ready tasks (kind=work, prerequisites available, no passing falsifier
    yet) ranked by AUTHORED priority (explicit authored_priority field); the
    winner is the one enabling the most relevant experiment(s). Centrality is
    never used -- readiness comes only from the prerequisite DAG."""
    info = q_blockers_for(g, experience_id)
    ready_work = [e for e in info["ready_now"] if e["kind"] == "work"]
    if not ready_work:
        return {"next": None, "ready": ready_work, "blocked": info["blocked_by"]}
    ranked = sorted(ready_work, key=lambda e: (e["authored_priority"], e["id"]))
    top = ranked[0]
    obj = g.get(top["id"])
    top_out = dict(top)
    top_out["name"] = obj.get("name")
    top_out["plan"] = (obj.get("physical") or {}).get("plan")
    top_out["acceptance_test"] = (obj.get("falsifier") or {}).get("acceptance_test")
    top_out["enables"] = sorted(g.enables(top["id"]))
    top_out["evidence_it_would_add"] = evidence_added_by(g, top["id"])
    return {"next": top_out, "ready": ranked, "blocked": info["blocked_by"]}


def evidence_added_by(g, work_id):
    """The evidence the work's own acceptance test would add (stated on the
    work object; not invented)."""
    obj = g.get(work_id)
    fz = obj.get("falsifier") or {}
    return {"falsifier_statement": fz.get("statement"),
            "acceptance_test": fz.get("acceptance_test"),
            "would_attach_to": sorted(set(
                [r["dst"] for r in g.out_edges(work_id, "enables_player_experience")]
                + [o["id"] for o in g.objects.values()
                   if work_id in (o.get("dependencies") or [])]))}


def run_all_six(g, seps_or_material="memb.septum.feet_shins"):
    """Run the six shapes; returns a dict ready to serialize to evidence."""
    return {
        "q1_compartments_without_supported_boundaries":
            q_unsupported_boundaries(g),
        "q2_placeholder_only_structures": q_placeholder_only(g),
        "q3_active_params_missing_provenance": q_params_missing_provenance(g),
        "q4_blockers_for_local_withdrawal": q_blockers_for(
            g, "experience.local_withdrawal"),
        "q5_evidence_at_risk_if_changed": {
            "if_changed": seps_or_material,
            "at_risk": q_evidence_at_risk(g, seps_or_material),
            "also_material_water": q_evidence_at_risk(g, "material.water"),
        },
        "q6_next_ready_task": q_next_ready_task(
            g, "experience.local_withdrawal"),
    }
