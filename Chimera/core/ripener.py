"""ripener — phantom pains ripen into work instead of rotting.

101 open pains and counting. Every pain is ALREADY a falsifiable claim
("tri-pad materials will read dark at walk height") — which makes each one a
ready-made micro-task: confirm or refute with evidence, then disposition it
via `postflight --pain-verdict`. Pains unvisited for AGE_DAYS auto-ripen into
claimable board tasks; the conveyor does the rest.

CONFIRMED verdicts ripen too (2026-07-15): a confirmed pain is a PROVEN real
problem, and the confirmation used to be the end of the line (tb-0056
confirmed WeightShiftAnimationTests has zero callers — and nothing spawned
the "wire a caller" task). `spawn_followups` turns each confirmed verdict
into a fix task; postflight calls it at verdict time, and `tend` backfills
recent confirmations nightly so nothing slips between the boards.

Guards: caps per tend (respects the container's open_board_tasks wall via
malcolm.admit), dedupes against tasks already citing the pain id, and never
ripens a pain younger than the age gate (fresh pains belong to their session).

CLI: python -m core.ripener tend [--max N] [--age-days D] [--dry-run]
     python -m core.ripener followups [--since-days D] [--max N] [--dry-run]
Runs nightly inside dream_loop.
"""

from __future__ import annotations

import argparse

AGE_DAYS = 5
MAX_PER_TEND = 3
FOLLOWUP_SINCE_DAYS = 7
FOLLOWUP_MARKER = "follow-up:"   # recipe tag that dedupes fix tasks per pain id


def ripe_pains(nodes: list, age_days: int = AGE_DAYS) -> list:
    """Open pains old enough to ripen: [{id, text, age_days}]."""
    from core.graphify_interface import collect_inheritance
    pains = collect_inheritance(nodes).get("open_pains", [])
    return [p for p in pains if (p.get("age_days") or 0) >= age_days]


def already_cited(pain_id: str, tasks: list) -> bool:
    return any(pain_id in (t.get("recipe") or "") and t.get("status") != "abandoned"
               for t in tasks)


def _pain_text(nodes: list, pain_id: str) -> str:
    """Recover a pain's claim text from its PhaseComplete node ('<node_id>:P<n>')."""
    node_id, _, pn = pain_id.partition(":P")
    for n in nodes:
        if n.get("id") == node_id:
            pains = n.get("phantom_pains") or []
            try:
                return str(pains[int(pn) - 1])
            except (ValueError, IndexError):
                return ""
    return ""


def confirmed_unaddressed(nodes: list, tasks: list,
                          since_days: int = FOLLOWUP_SINCE_DAYS) -> list:
    """Pain verdicts recorded 'confirmed' in the last since_days with no
    follow-up task on the board yet: [{id, text, verdict_ts}]. The dedupe key
    is the FOLLOWUP_MARKER tag in a task's recipe (the verdict micro-task
    itself cites the bare pain id, so a plain substring test would false-hit)."""
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(days=since_days)
    latest = {}   # pain_id -> (verdict_ts, verdict)
    for n in nodes:
        if n.get("type") != "PhaseComplete":
            continue
        ts = str(n.get("timestamp", ""))
        for pid, verdict in (n.get("pain_verdicts") or {}).items():
            if ts > latest.get(pid, ("", ""))[0]:
                latest[pid] = (ts, verdict)
    out = []
    for pid, (ts, verdict) in latest.items():
        if verdict != "confirmed":
            continue
        try:
            if datetime.fromisoformat(ts[:19]) < cutoff:
                continue
        except ValueError:
            continue
        if any(f"{FOLLOWUP_MARKER}{pid}" in (t.get("recipe") or "")
               and t.get("status") != "abandoned" for t in tasks):
            continue
        out.append({"id": pid, "text": _pain_text(nodes, pid), "verdict_ts": ts[:19]})
    out.sort(key=lambda f: f["verdict_ts"])
    return out


def spawn_followups(pain_ids: list = None, since_days: int = FOLLOWUP_SINCE_DAYS,
                    max_new: int = MAX_PER_TEND, dry_run: bool = False) -> list:
    """Turn confirmed pain verdicts into board FIX tasks. pain_ids given
    (postflight, at verdict time) restricts to those; otherwise (nightly
    backfill) every recent unaddressed confirmation is a candidate. Respects
    the container's open_board_tasks wall; dedupes via FOLLOWUP_MARKER."""
    from core.graphify_interface import load_dna_graph
    from core.task_board import _read_state, add_task
    nodes = load_dna_graph().get("nodes", [])
    tasks = _read_state().get("tasks", [])
    candidates = confirmed_unaddressed(nodes, tasks, since_days=since_days)
    if pain_ids is not None:
        wanted = set(pain_ids)
        candidates = [c for c in candidates if c["id"] in wanted]
    seeded = []
    for c in candidates[:max_new]:
        try:
            from core.malcolm import admit
            ok, reason = admit("open_board_tasks", 1)
            if not ok:
                print(f"[ripener] container refused follow-up spawning: {reason[:100]}")
                break
        except Exception:
            pass
        if dry_run:
            seeded.append(f"(dry) {c['id']}")
            continue
        text = str(c["text"]) or "(pain text unrecoverable — see the verdict's PhaseComplete node)"
        t = add_task(
            f"Fix confirmed pain: {text[:50]}",
            f"{FOLLOWUP_MARKER}{c['id']} — this claim was CONFIRMED with evidence "
            f"({c['verdict_ts']}); the pain is real. FIX the underlying issue, verify "
            f"with evidence (build/sim/telemetry — never a bare compile), then close via "
            f"postflight. The confirmed claim: {text[:400]}",
            files=["Source/Chimera/**"], editor="none",
            feature=None, priority=0.75, created_by="pain-verdict")
        seeded.append(t["id"])
    if seeded:
        print(f"[ripener] {len(seeded)} confirmed pain(s) -> follow-up fix task(s): "
              f"{', '.join(seeded)}")
    return seeded


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
    # Confirmed-verdict backfill (2026-07-15): postflight spawns follow-ups at
    # verdict time; this nightly pass catches any confirmation that slipped
    # through (older harnesses, manual graph records). Guarded — the backfill
    # must never wedge the ripen pass.
    try:
        seeded += spawn_followups(since_days=FOLLOWUP_SINCE_DAYS,
                                  max_new=max_new, dry_run=dry_run)
    except Exception as ex:
        print(f"[ripener] follow-up backfill FAILED: {ex}")
    return seeded


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("tend")
    t.add_argument("--max", type=int, default=MAX_PER_TEND)
    t.add_argument("--age-days", type=int, default=AGE_DAYS)
    t.add_argument("--dry-run", action="store_true")
    f = sub.add_parser("followups", help="spawn fix tasks from confirmed pain verdicts")
    f.add_argument("--since-days", type=int, default=FOLLOWUP_SINCE_DAYS)
    f.add_argument("--max", type=int, default=MAX_PER_TEND)
    f.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    if a.cmd == "followups":
        spawned = spawn_followups(since_days=a.since_days, max_new=a.max,
                                  dry_run=a.dry_run)
        if not spawned:
            print(f"[ripener] no unaddressed confirmed verdicts in the last "
                  f"{a.since_days}d (or board full)")
    else:
        tend(a.max, a.age_days, a.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
