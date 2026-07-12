"""herald — the morning page written for the HUMAN, not for agents.

The owner said the complexity had passed their comprehension. That is not an
owner-problem; it is a missing organ. The studio can explain itself to agents
across fifteen preflight sections — it must also be able to explain itself to
its human in one breath. Five plain sentences, no jargon, every dawn:

  1. what got better overnight
  2. what broke (and who is already on it)
  3. what graduated / is close to graduating
  4. what the container is proposing
  5. whether anything actually needs YOU today (usually: nothing)

Rendered to docs/HERALD.md by dream_loop each night. `python -m core.herald
write` any time.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERALD_MD = ROOT / "docs" / "HERALD.md"


def gather() -> dict:
    """Collect the day's facts from organs that already know them."""
    facts = {"date": datetime.now(timezone.utc).isoformat()[:10]}
    try:
        from core.rep_engine import all_battery_features, status, rep_gate
        feats = all_battery_features()
        stats = [status(f) for f in feats]
        facts["graduated"] = [s["feature"] for s in stats if s.get("gate")]
        facts["close"] = [s["feature"] for s in stats
                          if not s.get("gate") and s.get("streak", 0) >= 5]
        facts["red_features"] = [s["feature"] for s in stats
                                 if s.get("recent_rate", 1) < 0.9 and s.get("reps")]
    except Exception:
        pass
    try:
        from core.malcolm import status as mstatus, load_envelope
        rows = mstatus()
        facts["breaches"] = [r["axis"] for r in rows if r["state"] == "BREACH"]
        facts["gauge"] = next((r for r in rows
                               if r["axis"] == "engine_surprise_rate_per_week"), None)
        facts["proposals"] = [p for p in load_envelope().get("pending_adjustments", [])
                              if p.get("status") == "pending"]
    except Exception:
        pass
    try:
        from core.task_board import _read_state
        tasks = _read_state().get("tasks", [])
        facts["open_tasks"] = sum(1 for t in tasks if t["status"] == "open")
        facts["done_today"] = [t["title"][:60] for t in tasks
                               if t["status"] == "done"
                               and str(t.get("created_at", ""))[:10] == facts["date"]]
    except Exception:
        pass
    try:
        from core.graphify_interface import load_dna_graph, collect_inheritance
        inh = collect_inheritance(load_dna_graph().get("nodes", []))
        facts["open_pains"] = len(inh.get("open_pains", []))
        will = inh.get("will") or {}
        facts["will"] = str(will.get("inheritance", ""))[:200]
    except Exception:
        pass
    return facts


def render(facts: dict) -> str:
    """Five sentences a tired human can read. Plain words only."""
    lines = [f"# The Herald — {facts.get('date', '?')}", ""]
    grads = facts.get("graduated") or []
    close = facts.get("close") or []
    if grads:
        lines.append(f"**Good news:** {len(grads)} feature(s) have now earned full "
                     f"trust through repeated testing — {', '.join(grads[:3])}"
                     + (" and more." if len(grads) > 3 else "."))
    elif close:
        lines.append(f"**Good news:** {len(close)} feature(s) are a few clean nights "
                     f"away from earning full trust ({', '.join(close[:3])}).")
    else:
        lines.append("**Progress:** the nightly checks ran; trust is accumulating "
                     "quietly, nothing graduated yet.")
    reds = facts.get("red_features") or []
    breaches = facts.get("breaches") or []
    if breaches:
        lines.append(f"**Broken:** the safety container reports {len(breaches)} "
                     f"limit(s) exceeded ({', '.join(breaches[:2])}) — the pipeline "
                     f"will hold until an agent fixes this.")
    elif reds:
        lines.append(f"**Watch:** {len(reds)} feature(s) failed some checks recently "
                     f"({', '.join(r for r in reds[:3])}); they are on the work "
                     f"board with evidence attached.")
    else:
        lines.append("**Broken:** nothing the checks can see.")
    lines.append(f"**The queue:** {facts.get('open_tasks', '?')} task(s) open for "
                 f"agents; {facts.get('open_pains', '?')} old worries await a "
                 f"confirm-or-refute verdict.")
    props = facts.get("proposals") or []
    if props:
        p = props[0]
        lines.append(f"**The container proposes:** {p.get('direction', '?')} the "
                     f"'{p.get('axis', '?')}' limit — it waits for a yes/no "
                     f"(edit docs/envelope.json, status field).")
    else:
        lines.append("**The container:** holding steady at the edge; no changes proposed.")
    needs = []
    if props:
        needs.append("rule on the container proposal above")
    if breaches:
        needs.append("a breach needs attention")
    lines.append(f"**Needs you today:** {'; '.join(needs) if needs else 'nothing — rest.'}")
    if facts.get("will"):
        lines += ["", f"*Last will:* {facts['will']}"]
    lines += ["", "*(Generated nightly. The machinery underneath: "
                  "docs/HISTORY_BOOK.md is searchable; preflight has the dials.)*", ""]
    return "\n".join(lines)


def write() -> str:
    facts = gather()
    HERALD_MD.write_text(render(facts), encoding="utf-8")
    return f"[herald] morning page -> {HERALD_MD.relative_to(ROOT)}"


if __name__ == "__main__":
    import sys
    print(write() if "write" in sys.argv else render(gather()))
