"""horizon — the studio's explicit terminal/idle state (2026-07-15).

The missing state: when the task board hit open:0 the duty loop had no word
for "the season is complete" and flailed — re-running duty cycles, floors,
and pipeline checks against a finished board. The horizon is the single
authoritative answer to "is there ANY autonomous work left?":

  1. board          — open + claimed tasks (blocked is informational: it
                      needs a solver/human, not a fresh duty cycle)
  2. ripening pains — open phantom pains past the age gate that ripener
                      would seed next tend (uncited on the board)
  3. observation    — system-verified features awaiting simulation evidence
                      (collect_observation_queue — CYCLE_PROMPT branch B work)
  4. gate approvals — PENDING_HEURISTICS.md entries approved but awaiting a
                      capable implementation cycle (branch A work)
  5. follow-ups     — recently CONFIRMED pain verdicts with no follow-up
                      task on the board yet (ripener.confirmed_unaddressed)

All five zero -> IDLE (terminal): write docs/SESSION_SUMMARY.md and HALT
cleanly. Halting at the horizon is a SUCCESS, not a failure — the studio
wakes again when a pain ages past the gate, a feature reaches the
observation queue, or a human seeds the board. (The container's
open_board_tasks floor of 3 is a starvation warning for a RUNNING conveyor;
the horizon's IDLE is the one legitimate state below it.)

CLI:
    python -m core.horizon               # status; exit 0 = work pending, 10 = IDLE
    python -m core.horizon --summarize   # if IDLE, also write docs/SESSION_SUMMARY.md
    python -m core.horizon --json        # machine-readable status
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]            # E:/PythonChimera/Chimera
SUMMARY_PATH = ROOT / "docs" / "SESSION_SUMMARY.md"
PENDING_PATH = ROOT / "docs" / "PENDING_HEURISTICS.md"

IDLE_EXIT_CODE = 10   # distinct from failure so orchestrators can branch on it


def _approved_pending_implementation() -> list:
    """PENDING_HEURISTICS.md entries whose status is 'approved' (auto gate-organ
    or human-written) — branch-A work awaiting a capable cycle. 'promoted' and
    'vetoed' statuses are finished business."""
    if not PENDING_PATH.exists():
        return []
    text = PENDING_PATH.read_text(encoding="utf-8")
    out = []
    for m in re.finditer(r"(?m)^## (H-\d+): (.+?)$([\s\S]*?)(?=^## H-\d+: |\Z)", text):
        hid, sig, block = m.group(1), m.group(2).strip(), m.group(3)
        sm = re.search(r"(?m)^- status:\s*(.+)$", block)
        status = (sm.group(1).strip().lower() if sm else "")
        if status.startswith("approved"):
            out.append({"id": hid, "signature": sig[:80], "status": status[:60]})
    return out


def pending_work(nodes: list = None, state: dict = None) -> dict:
    """The authoritative pending-autonomous-work snapshot. Pass preloaded
    nodes/state to avoid re-reading the graph (preflight does)."""
    from core.graphify_interface import (load_dna_graph, collect_inheritance,
                                         collect_observation_queue)
    from core.task_board import get_state
    from core.ripener import ripe_pains, already_cited, confirmed_unaddressed

    if nodes is None:
        nodes = load_dna_graph().get("nodes", [])
    if state is None:
        state = get_state()
    tasks = state.get("tasks", [])

    by_status = {}
    for t in tasks:
        by_status.setdefault(t.get("status", "?"), []).append(t)
    open_tasks = by_status.get("open", [])
    claimed = by_status.get("claimed", [])
    blocked = by_status.get("blocked", [])
    done = by_status.get("done", [])

    ripe = [p for p in ripe_pains(nodes) if not already_cited(p["id"], tasks)]
    obs = collect_observation_queue(nodes)
    gate = _approved_pending_implementation()
    followups = confirmed_unaddressed(nodes, tasks)
    open_pains = collect_inheritance(nodes).get("open_pains", [])

    total = len(open_tasks) + len(claimed) + len(ripe) + len(obs) + len(gate) + len(followups)
    return {
        "board_open": len(open_tasks),
        "board_claimed": len(claimed),
        "board_blocked": len(blocked),          # informational, not pending
        "board_done": len(done),
        "board_total": len(tasks),
        "ripe_pains": [{"id": p["id"], "text": str(p["text"])[:80]} for p in ripe],
        "observation_queue": [{"feature": q["feature"], "loop": q["loop"]} for q in obs],
        "gate_approvals": gate,
        "confirmed_followups": [{"id": f["id"], "text": str(f["text"])[:80]} for f in followups],
        "open_pains_unripe": max(0, len(open_pains) - len(ripe)),  # wake condition
        "total_pending": total,
        "idle": total == 0,
    }


def format_block(pw: dict) -> str:
    """The preflight/CLI block. One line when working; a directive when idle."""
    if not pw["idle"]:
        parts = []
        if pw["board_open"] or pw["board_claimed"]:
            parts.append(f"board open:{pw['board_open']} claimed:{pw['board_claimed']}")
        if pw["ripe_pains"]:
            parts.append(f"ripe pains:{len(pw['ripe_pains'])}")
        if pw["observation_queue"]:
            parts.append(f"observation queue:{len(pw['observation_queue'])}")
        if pw["gate_approvals"]:
            parts.append(f"gate approvals:{len(pw['gate_approvals'])}")
        if pw["confirmed_followups"]:
            parts.append(f"confirmed pains needing follow-up:{len(pw['confirmed_followups'])}")
        line = f"[3.75] Horizon: WORK PENDING ({pw['total_pending']}) — " + " | ".join(parts)
        if pw["board_blocked"]:
            line += f"\n    ({pw['board_blocked']} blocked task(s) carry drafted fixes — solver/human lane)"
        return line
    lines = [
        f"[3.75] Horizon: IDLE (terminal) — board complete "
        f"({pw['board_done']}/{pw['board_total']} done), nothing ripens, "
        f"observation queue empty, no approvals pending.",
        "    -> END THE SHIFT CLEANLY: python -m core.horizon --summarize "
        "(writes docs/SESSION_SUMMARY.md), full close, HALT.",
        "    Do NOT loop duty cycles / floors / pipeline re-checks against an idle horizon.",
    ]
    if pw["open_pains_unripe"]:
        lines.append(f"    wake condition: {pw['open_pains_unripe']} open pain(s) "
                     f"younger than the ripener age gate will ripen in the coming days")
    return "\n".join(lines)


def write_session_summary(pw: dict = None, reason: str = "") -> Path:
    """Write docs/SESSION_SUMMARY.md — the clean-halt artifact. Regenerated
    each time (like TASK_BOARD.md); durable history stays in the DNA graph."""
    from core.task_board import get_state
    if pw is None:
        pw = pending_work()
    state = get_state()
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds") + "Z"
    recent_done = sorted((t for t in state.get("tasks", []) if t.get("status") == "done"),
                         key=lambda t: str((t.get("notes") or [{}])[-1].get("ts", "")),
                         reverse=True)[:8]
    lines = [
        "# SESSION SUMMARY — terminal idle state (the horizon)",
        f"reached: {stamp}",
        f"reason: {reason or 'no autonomous work on the horizon'}",
        "",
        "## Board at halt",
        f"- {pw['board_done']}/{pw['board_total']} done, {pw['board_open']} open, "
        f"{pw['board_claimed']} claimed, {pw['board_blocked']} blocked",
    ]
    for t in recent_done:
        lines.append(f"  - {t['id']} {str(t.get('title', ''))[:60]} — "
                     f"{str(t.get('result', ''))[:70]}")
    lines += [
        "",
        "## Outstanding (not autonomous work)",
        f"- blocked tasks awaiting solver/human: {pw['board_blocked']}",
        f"- open pains younger than the ripener age gate: {pw['open_pains_unripe']}",
        "",
        "## Wake conditions (any of these ends the idle state)",
        "- an open pain ages past the ripener gate -> nightly tend seeds a micro-task",
        "- a feature reaches 'verified' -> observation queue (duty branch B)",
        "- a pain verdict lands 'confirmed' -> postflight spawns a follow-up task",
        "- a gate-organ heuristic is approved -> capable cycle (duty branch A)",
        "- a human seeds the board: python -m core.task_board add/seed",
        "",
        "The halt was CLEAN: no unfinished claims, no dangling tunnel sessions.",
    ]
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:  # CAPCOM: the operator hears the studio go quiet on purpose
        from core.capcom import post_safe
        post_safe("horizon", f"IDLE-COMPLETE: session summary written "
                  f"({pw['board_done']}/{pw['board_total']} done) — clean halt",
                  level="info", source="horizon")
    except Exception:
        pass
    return SUMMARY_PATH


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--summarize", action="store_true",
                        help="if IDLE, also write docs/SESSION_SUMMARY.md")
    parser.add_argument("--json", action="store_true", help="machine-readable status")
    args = parser.parse_args(argv)
    pw = pending_work()
    if args.json:
        print(json.dumps(pw, indent=1))
    else:
        print(format_block(pw))
    if pw["idle"] and args.summarize:
        path = write_session_summary(pw)
        print(f"[horizon] session summary -> {path}")
    return IDLE_EXIT_CODE if pw["idle"] else 0


if __name__ == "__main__":
    sys.exit(main())
