"""The queries: next-work, blockers, enablement closure.

The approved first-proof question:
  "which unfinished structures enable the press-and-response experience, have
   prerequisites available, and lack passing falsifiers?"
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from schema import PRIORITY_RANK, STATUS_RANK  # noqa: E402

AVAILABLE_THRESHOLD = "geometry_built"  # prerequisite exists as geometry to build against


def enables_closure(g, experience_id: str) -> set:
    """Everything that (transitively) enables the given player experience."""
    want = {experience_id}
    frontier = [experience_id]
    while frontier:
        cur = frontier.pop()
        for r in g.in_edges(cur, "enables_player_experience"):
            if r["src"] not in want:
                want.add(r["src"])
                frontier.append(r["src"])
    want.discard(experience_id)
    return want


def blockers_of(g, oid: str) -> list:
    """requires_implementation targets that do NOT yet exist as buildable
    geometry (status below geometry_built). Extracted never counts as built."""
    blocked = []
    for dep in g.requires(oid):
        dep_obj = g.get(dep)
        if STATUS_RANK.get(dep_obj["status"], -1) < STATUS_RANK[AVAILABLE_THRESHOLD]:
            blocked.append(dep)
    return sorted(blocked)


def lacks_passing_falsifier(g, oid: str) -> bool:
    fz = g.get(oid).get("falsifier") or {}
    return fz.get("status") != "passing"


def next_work(g, experience_id: str = "experience.press_and_response") -> dict:
    """Ordered list of unfinished structures that (a) enable the experience
    transitively, (b) have all prerequisites available (nothing below
    geometry_built in their requires_implementation set), (c) lack a passing
    falsifier. Ordered by inventory priority, then top-five build order, then
    an explicit per-object order hint, then id."""
    enablers = enables_closure(g, experience_id)
    actionable, blocked = [], []
    for oid in enablers:
        obj = g.get(oid)
        if obj["kind"] in ("type", "evidence", "experience", "capability", "work", "region"):
            continue
        if obj["status"] == "verified":
            continue
        if not lacks_passing_falsifier(g, oid):
            continue
        item = {
            "id": oid,
            "name": obj.get("name"),
            "status": obj["status"],
            "priority": obj.get("priority"),
            "build_rank": obj.get("build_rank"),
            "order_hint": obj.get("order_hint", 99),
            "blockers": blockers_of(g, oid),
            "falsifier": (obj.get("falsifier") or {}).get("statement"),
            "enables": g.enables(oid),
        }
        if not item["blockers"]:
            actionable.append(item)
        else:
            blocked.append(item)
    actionable.sort(key=lambda it: (
        PRIORITY_RANK.get(it["priority"], 3),
        it["build_rank"] if it["build_rank"] is not None else 9,
        it["order_hint"],
        it["id"],
    ))
    blocked.sort(key=lambda it: (
        len(it["blockers"]),
        PRIORITY_RANK.get(it["priority"], 3),
        it["build_rank"] if it["build_rank"] is not None else 9,
        it["order_hint"],
        it["id"],
    ))
    return {"experience": experience_id, "actionable": actionable, "blocked": blocked}


def proof_chain_for(g, oid: str) -> list:
    """What would prove this object works: its own falsifier plus the falsifiers
    of everything it enables (the experiment chain it participates in)."""
    chain = []
    obj = g.get(oid)
    fz = obj.get("falsifier") or {}
    if fz.get("statement"):
        chain.append({"object": oid, "falsifier": fz["statement"],
                      "acceptance_test": fz.get("acceptance_test"),
                      "status": fz.get("status", "untested")})
    seen = {oid}
    frontier = [oid]
    while frontier:
        cur = frontier.pop()
        for r in g.out_edges(cur, "enables_player_experience"):
            if r["dst"] not in seen:
                seen.add(r["dst"])
                frontier.append(r["dst"])
                exp = g.get(r["dst"])
                efz = exp.get("falsifier") or {}
                if efz.get("statement"):
                    chain.append({"object": r["dst"], "falsifier": efz["statement"],
                                  "acceptance_test": efz.get("acceptance_test"),
                                  "status": efz.get("status", "untested")})
    return chain
