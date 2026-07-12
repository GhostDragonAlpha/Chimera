"""ripener — phantom pains ripen into work instead of rotting.

101 open pains and counting. Every pain is ALREADY a falsifiable claim
("tri-pad materials will read dark at walk height") — which makes each one a
ready-made micro-task: confirm or refute with evidence, then disposition it
via `postflight --pain-verdict`. Pains unvisited for AGE_DAYS auto-ripen into
claimable board tasks; the conveyor does the rest.

Guards: caps per tend (respects the container's open_board_tasks wall via
malcolm.admit), dedupes against tasks already citing the pain id, and never
ripens a pain younger than the age gate (fresh pains belong to their session).

CLI: python -m core.ripener tend [--max N] [--age-days D] [--dry-run]
Runs nightly inside dream_loop.
"""

from __future__ import annotations

import argparse

AGE_DAYS = 5
MAX_PER_TEND = 3


def ripe_pains(nodes: list, age_days: int = AGE_DAYS) -> list:
    """Open pains old enough to ripen: [{id, text, age_days}]."""
    from core.graphify_interface import collect_inheritance
    pains = collect_inheritance(nodes).get("open_pains", [])
    return [p for p in pains if (p.get("age_days") or 0) >= age_days]


def already_cited(pain_id: str, tasks: list) -> bool:
    return any(pain_id in (t.get("recipe") or "") and t.get("status") != "abandoned"
               for t in tasks)


def tend(max_new: int = MAX_PER_TEND, age_days: int = AGE_DAYS,
         dry_run: bool = False) -> list:
    """Ripen up to max_new pains into board micro-tasks. Returns seeded ids."""
    from core.graphify_interface import load_dna_graph
    from core.task_board import _read_state, add_task
    nodes = load_dna_graph().get("nodes", [])
    tasks = _read_state().get("tasks", [])
    seeded = []
    candidates = [p for p in ripe_pains(nodes, age_days)
                  if not already_cited(p["id"], tasks)]
    for pain in candidates[:max_new]:
        try:
            from core.malcolm import admit
            ok, reason = admit("open_board_tasks", 1)
            if not ok:
                print(f"[ripener] container refused further ripening: {reason[:100]}")
                break
        except Exception:
            pass
        if dry_run:
            seeded.append(f"(dry) {pain['id']}")
            continue
        t = add_task(
            f"Pain verdict: {str(pain['text'])[:52]}",
            f"CONFIRM OR REFUTE with evidence, then disposition: "
            f"python -m core.postflight --phase ... --pain-verdict "
            f"\"{pain['id']}:confirmed|refuted|still-open\". The claim "
            f"({pain['id']}, aged {pain['age_days']}d): {str(pain['text'])[:400]}",
            files=["docs/research/**"], editor="none",
            feature=None, priority=0.6, created_by="ripener")
        seeded.append(t["id"])
    if seeded:
        print(f"[ripener] ripened {len(seeded)} pain(s) into micro-tasks: "
              f"{', '.join(seeded)}")
    else:
        print(f"[ripener] nothing ripe (age>={age_days}d, uncited) or board full")
    return seeded


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("tend")
    t.add_argument("--max", type=int, default=MAX_PER_TEND)
    t.add_argument("--age-days", type=int, default=AGE_DAYS)
    t.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    tend(a.max, a.age_days, a.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
