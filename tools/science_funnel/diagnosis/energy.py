"""energy.py -- the phase/force/work/energy bookkeeping (the ledger decomposition).

What the wave mines do by hand today, mechanized:
  - the worst |balance_error_J| tick + value from the [ledger10] dumps
  - matched-tick component deltas (failed vs reference) at the divergence's ticks
  - per-era per-drive work  integral tau*spd*dt  from the [dvq]/[dvj] rows
"""
from __future__ import annotations

COMPONENTS = ("actuator_work_J", "friction_heat_J", "impact_heat_J", "brake_heat_J",
              "damping_heat_J", "kinetic_J", "gravitational_J")


def worst_balance(tr) -> dict:
    if not tr.ledger10:
        return dict(tick=None, value=None)
    t = max(tr.ledger10, key=lambda k: abs(tr.ledger10[k]["balance_error_J"]))
    return dict(tick=t, value=tr.ledger10[t]["balance_error_J"])


def matched_component_deltas(fail, ref, ticks=None, every: int = 10) -> list:
    """Component deltas at matched [ledger10] ticks (default: every 10 from the
    first shared tick) -- WHICH component carries the extra energy."""
    shared = sorted(set(fail.ledger10) & set(ref.ledger10))
    if not shared:
        return []
    if ticks is None:
        first = shared[0] + (every - shared[0] % every) % every
        ticks = [t for t in shared if t >= first]
    rows = []
    for t in ticks:
        a, b = fail.ledger10[t], ref.ledger10[t]
        rows.append(dict(tick=t,
                         bal_ref=b["balance_error_J"], bal_fail=a["balance_error_J"],
                         delta_bal=a["balance_error_J"] - b["balance_error_J"],
                         components={k: a[k] - b[k] for k in COMPONENTS if k in a and k in b}))
    return rows


def drive_era_work(tr, t0: int, t1: int, drive: int, dt: float) -> float:
    s = 0.0
    for t in range(t0, t1):
        q = tr.dvq.get((t, drive))
        j = tr.dvj.get((t, drive))
        if q is not None and j is not None:
            s += q[0] * j[2] * dt
    return s


def era_work_table(fail, ref, eras: list, dt: float, drives=range(8), min_t0: int = 90) -> list:
    """Per-era per-drive work on the failed run, matched to the reference era
    (same leg, |launch delta| <= 3 -- the wave-38 mine's rule), ranked by the
    biggest |work delta| any drive shows."""
    ref_fires = [(l, t) for (l, t, _p, _c, _r) in ref.fires] if ref is not None else []
    ref_tds = {0: sorted(t for l, t in ref.tds if l == 0),
               1: sorted(t for l, t in ref.tds if l == 1)} if ref is not None else {}
    rows = []
    for e in eras:
        if e["td"] is None or e["t0"] < min_t0:
            continue
        works = {k: drive_era_work(fail, e["t0"], e["td"], k, dt) for k in drives}
        ref_works, match = None, None
        cand = [t for (l, t) in ref_fires if l == e["leg"] and abs(t - e["t0"]) <= 3]
        if cand:
            a0 = cand[0]
            a1 = next((t for t in ref_tds[e["leg"]] if t > a0), a0 + (e["td"] - e["t0"]))
            match = (a0, a1)
            ref_works = {k: drive_era_work(ref, a0, a1, k, dt) for k in drives}
        deltas = ({k: works[k] - ref_works[k] for k in works} if ref_works is not None else None)
        top = (max(deltas, key=lambda k: abs(deltas[k])) if deltas else None)
        rows.append(dict(leg=e["leg"], t0=e["t0"], td=e["td"], length=e["length"],
                         era_max_pm=e["era_max_pm"], stall_arith=e["stall_arith"],
                         stall_pose=e["stall_pose"], clear_tick=e["clear_tick"],
                         work_J=works, ref_work_J=ref_works,
                         delta_J=deltas, match_era=match,
                         top_delta_drive=top, top_delta=(deltas[top] if top is not None else None)))
    rows.sort(key=lambda r: abs(r["top_delta"]) if r["top_delta"] is not None else
              abs(max(r["work_J"].values(), key=abs)), reverse=True)
    return rows
