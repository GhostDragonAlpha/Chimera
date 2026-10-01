"""eras.py -- the era table, the two stall classifiers, and the death classes.

An ERA is one hind swing: [launch fire tick, touchdown tick) of one leg, built
from the [hindstep] fire/td stream, with contact facts from the [dvp] rows (the
decision at tick N consumes the tick-start row N-1 -- the wave mines' convention).

Constants are the campaign's banked laws, not fit numbers:
  kTouch = 1e-5 (the contact solver's touch quantum, gait_controller.hpp:36)
  kReleaseBand = 1e-6 (the release band, gait_controller.hpp:52)
  tair = 9 (the on-grid air time, the wave-20 minimal-air-time law)
"""
from __future__ import annotations

KTOUCH = 1e-5
KBAND = KTOUCH + 1e-6     # kTouch + kReleaseBand = 1.1e-5
TAIR = 9
ON_GRID = (9, 15, 18)     # the shipped calendar's era lengths (slot 9; alt 9/15/18)
DRAIN_RXN_N = 0.5         # the carrier "unloaded" reading (the wave-32/35 mines' 0.5 N)
DRAIN_PEAK_N = 4.0        # a collapse needs carried load first (the wave-35 mine's peak rxn0)
GRAZE_FACTOR = 10.0       # graze-fight: era max pair-min <= GRAZE_FACTOR * kTouch


def build_era_table(tr) -> list:
    """The wave mine's era table, verbatim conventions."""
    tds_by_leg = {0: sorted(t for l, t in tr.tds if l == 0),
                  1: sorted(t for l, t in tr.tds if l == 1)}
    eras = []
    last_fire = {0: None, 1: None}
    for (leg, t0, phi, cls, raw) in tr.fires:
        td_next = next((t for t in tds_by_leg[leg] if t > t0), None)
        other = 1 - leg
        prev_other_fire = last_fire[other]
        clear_tick = None
        mx = 0.0
        if td_next:
            for n in range(t0 + 1, td_next + 1):
                pm = tr.pairmin(n - 1, leg)
                if pm is None:
                    continue
                mx = max(mx, pm)
                if pm > KBAND and clear_tick is None:
                    clear_tick = n
        stall_arith = (prev_other_fire is not None and (t0 - prev_other_fire) == TAIR)
        eras.append(dict(leg=leg, t0=t0, td=td_next, phi=phi, cls=cls, raw_fire=raw,
                         length=(td_next - t0) if td_next else None,
                         on_grid=(td_next - t0) in ON_GRID if td_next else None,
                         clear_tick=clear_tick, era_max_pm=mx,
                         prev_other_fire=prev_other_fire,
                         stall_arith=stall_arith,
                         stall_pose=(clear_tick is None)))
        last_fire[leg] = t0
    return eras


def era_graze_class(e: dict) -> str:
    """GRAZE if the era's pads lived marginally in/out of the release band."""
    if e["era_max_pm"] <= 0.0:
        return "no-contact"
    if e["era_max_pm"] <= KBAND:
        return "held"           # never cleared by the pose read
    if e["era_max_pm"] <= GRAZE_FACTOR * KTOUCH:
        return "GRAZE"          # the band-edge fight (one quantum past the band)
    return "clear-air"          # genuinely away from the band


def find_unload_drains(tr, eras: list) -> list:
    """Carrier rxn collapse mid-era (the wave-32/35 drain face).

    carrier = the leg NOT swinging in the era; drain onset = first in-era tick
    whose carrier rxn < DRAIN_RXN_N with the onset EARLY in the era (era-relative
    <= 5, the named faces' shape: an unload well before the partner's band
    entry -- the scheduled end-of-era unload is not a drain).
    A carrier that is itself MID-SWING at the onset is not a carrier (its pads
    are airborne by design -- the waive-era overlapping swings), so the era is
    skipped: only a standing carrier's collapse is a drain.
    """
    drains = []
    fires_by_leg = {0: sorted(t for (l, t, *_r) in tr.fires if l == 0),
                    1: sorted(t for (l, t, *_r) in tr.fires if l == 1)}
    tds_by_leg = {0: sorted(t for l, t in tr.tds if l == 0),
                  1: sorted(t for l, t in tr.tds if l == 1)}
    for e in eras:
        if not e["td"]:
            continue
        carrier = 1 - e["leg"]
        onset = None
        peak = 0.0
        peak_upto = 0.0
        for t in range(e["t0"], e["td"]):
            r = tr.carrier_rxn(t, carrier)
            if r is None:
                continue
            peak = max(peak, r)
            if onset is None:
                # a collapse needs a carried load first: the touchdown transient
                # (a carrier that landed the same tick) is not a drain
                if r < DRAIN_RXN_N and (t - e["t0"]) <= 5 and peak_upto >= DRAIN_PEAK_N:
                    onset = t
                peak_upto = max(peak_upto, r)
        standing = True
        if onset is not None:
            f = [x for x in fires_by_leg[carrier] if x <= onset]
            if f:
                launch = f[-1]
                td = next((t for t in tds_by_leg[carrier] if t > launch), None)
                standing = not (td is None or td > onset)
        e["carrier_peak_rxn"] = peak
        e["carrier_drain_onset"] = onset
        if onset is not None and standing:
            drains.append(dict(era=e, carrier=carrier, onset=onset, peak=peak))
    return drains


def find_capacity_folds(tr, eras: list, tol_deg: float = 5.0, min_ticks: int = 5) -> list:
    """Drives pinned at cap with the target unmet, sustained across the era
    (the wave-29/30 joint-capacity face: the era's OWN demand, not a transient).
    A fold is a seed only when the drive is pinned for >= 80% of the era's ticks."""
    folds = []
    for e in eras:
        if not e["td"]:
            continue
        era_len = e["td"] - e["t0"]
        best = None
        for k in range(8):
            run = 0
            run_max = 0
            pinned_ticks = 0
            for t in range(e["t0"], e["td"]):
                q = tr.dvq.get((t, k))
                j = tr.dvj.get((t, k))
                if q is None or j is None:
                    run = 0
                    continue
                tau, cap = q
                ang, tgt, _spd = j
                pinned = cap > 0 and tau >= cap - 1e-9
                if pinned:
                    pinned_ticks += 1
                unmet = abs(tgt - ang) * (180.0 / 3.141592653589793) > tol_deg if abs(tgt - ang) < 6.283 else abs(tgt - ang) > tol_deg
                if pinned and unmet:
                    run += 1
                    run_max = max(run_max, run)
                else:
                    run = 0
            if run_max >= min_ticks and run_max >= era_len - 1 and pinned_ticks >= 0.8 * era_len and \
                    (best is None or run_max > best["ticks"]):
                best = dict(drive=k, ticks=run_max)
        e["capacity_fold"] = best
        if best:
            folds.append(dict(era=e, **best))
    return folds


def find_launch_drift(fail, ref):
    """The launch-grid divergence vs the reference run: per leg, the first fire
    whose tick deviates from the reference's corresponding fire (greedy
    two-pointer alignment; designed inserts on either side are skipped, not
    mismatches).  Returns the drift + its evidence: the launcher's own stance
    read at the completion rows (the graze-at-handoff seed the wave mines read
    by hand), and how many later same-leg launches carry a nonzero delta (a
    drift PROPAGATES; a one-tick re-anchor does not)."""
    if ref is None:
        return None
    for leg in (0, 1):
        fa = [(t, p, c) for (l, t, p, c, *_r) in fail.fires if l == leg]
        fb = [(t, p, c) for (l, t, p, c, *_r) in ref.fires if l == leg]
        i = j = 0
        while i < len(fa) and j < len(fb):
            ta, tb = fa[i][0], fb[j][0]
            if abs(ta - tb) <= 3:
                if ta != tb:
                    # the first real deviation: gather evidence + propagation
                    launch_row = ta - 1
                    pm_a = fail.pairmin(launch_row, leg)
                    rxn_a = fail.carrier_rxn(launch_row, leg)
                    pm_b = fail.pairmin(ta - 2, leg)
                    rxn_b = fail.carrier_rxn(ta - 2, leg)
                    def _graze(pm, rx):
                        return pm is not None and KBAND < pm <= GRAZE_FACTOR * KTOUCH and (rx or 0) > 0
                    evidence = [dict(row=r, pairmin=fail.pairmin(r, leg), rxn=fail.carrier_rxn(r, leg),
                                     graze_released=_graze(fail.pairmin(r, leg), fail.carrier_rxn(r, leg)))
                                for r in (ta - 2, ta - 1)]
                    propagation = 0
                    k = i
                    m = j
                    while k < len(fa) and m < len(fb) and abs(fa[k][0] - fb[m][0]) <= 3:
                        if fa[k][0] != fb[m][0]:
                            propagation += 1
                        k += 1
                        m += 1
                    return dict(leg=leg, launch_tick=ta, reference_tick=tb, delta=ta - tb,
                                propagation=propagation, launch_row=launch_row,
                                pairmin_at_row=pm_a, rxn_at_row=rxn_a,
                                graze_at_completion=bool(_graze(pm_a, rxn_a) or _graze(pm_b, rxn_b)),
                                evidence_rows=evidence)
                i += 1
                j += 1
            elif ta < tb:
                i += 1  # an insert on the failed run (e.g. a designed waive) -- skip, not a drift
            else:
                j += 1  # a missing fire -- skip the reference's
        break
    return None


def classify_death(tr, census: dict, fired: list, eras: list, drains: list, folds: list,
                   chain_start_tick=None, launch_drift=None) -> dict:
    """The death class = the fired letters' classes + the ranked mechanism seeds.

    Seeds (mechanism owners) sit ON THE CAUSAL CHAIN: only eras launched at or
    after the chain's start (the earliest relevant divergence vs the reference
    when one is supplied, else the first calendar anomaly) are eligible -- a
    collapsing walk's late drains and pinned drives are SYMPTOMS of the death,
    not its mechanism, and are excluded by the chain rule, not by taste.

    Seeds, ranked in causal order (the slices' order):
      CALENDAR_DRIFT  a launch off the reference baseline's grid (the +1 drift
                      face; only vs a BASELINE reference -- vs a parent law the
                      calendar changes are the hypothesis under test, not a death)
      GRAZE_MISFIRE   a waive fired inside a stall-by-arithmetic graze era
      CALENDAR_SCATTER an era that ran long past its on-grid length (missed completion)
      UNLOAD_DRAIN    a carrier reaction collapse early in an era
      CAPACITY_FOLD   a drive pinned at cap with its target unmet across the era
    Letter classes: LEDGER_BREACH (worst ledger over its bound), RUNG_DEATH
    (refusal at/below the rung bar), NONE (a passing run).
    """
    fired_classes = []
    for f in fired:
        if f["kind"] == "ledger" and f["verdict"] == "FIRED":
            fired_classes.append("LEDGER_BREACH")
        if f["kind"] == "rung" and f["verdict"] == "FIRED":
            fired_classes.append("RUNG_DEATH")
    off_grid = [e for e in eras if e["td"] and not e["on_grid"] and e["t0"] >= 90]
    # the chain's start: divergence tick (reference supplied) or the first anomaly
    anomalies = [e["t0"] for e in off_grid]
    for w in tr.waivefires:
        anomalies.append(w[1])
    if launch_drift:
        anomalies.append(launch_drift["launch_tick"])
    chain_start = chain_start_tick if chain_start_tick is not None else \
        (min(anomalies) if anomalies else 0)
    chain_lo = max(90, chain_start - TAIR)
    seeds = []
    if launch_drift and launch_drift["launch_tick"] >= chain_lo:
        seeds.append(dict(seed="CALENDAR_DRIFT", era=None, waive=None, drift=launch_drift))
    misfires = []
    for w in tr.waivefires:
        wl, wt, dl = w[0], w[1], w[2]
        host = next((e for e in eras if e["leg"] == 1 - wl and e["t0"] < wt and (e["td"] or 10 ** 9) > wt), None)
        if host is not None and host["stall_arith"] and era_graze_class(host) == "GRAZE":
            misfires.append(dict(waive=(wl, wt, dl), host=host))
    for m in misfires:
        if m["host"]["t0"] >= chain_lo and not any(s["era"] is m["host"] for s in seeds):
            seeds.append(dict(seed="GRAZE_MISFIRE", era=m["host"], waive=m["waive"]))
    long_eras = [e for e in eras if e["td"] and e["length"] > max(ON_GRID) and e["t0"] >= chain_lo]
    for e in sorted(long_eras, key=lambda e: e["t0"]):
        if not any(s["era"] is e for s in seeds):
            seeds.append(dict(seed="CALENDAR_SCATTER", era=e, waive=None))
    for d in drains:
        if d["era"]["t0"] >= chain_lo and not any(s["era"] is d["era"] for s in seeds):
            seeds.append(dict(seed="UNLOAD_DRAIN", era=d["era"], waive=None,
                              onset=d["onset"], carrier=d["carrier"]))
    for f in folds:
        if f["era"]["t0"] >= chain_lo and not any(s["era"] is f["era"] for s in seeds):
            seeds.append(dict(seed="CAPACITY_FOLD", era=f["era"], waive=None, drive=f["drive"]))
    # a seed whose era launches INSIDE an earlier seed's era span is that
    # seed's symptom (the same perturbed regime), not an independent owner
    cleaned = []
    for s in sorted(seeds, key=lambda s: (s["era"]["t0"] if s["era"] else
                                          (s["drift"]["launch_tick"] if s.get("drift") else 0))):
        t0 = s["era"]["t0"] if s["era"] else s["drift"]["launch_tick"]
        nested = any(c["era"] is not None and c["era"]["t0"] < t0 < (c["era"]["td"] or 10 ** 9)
                     for c in cleaned)
        if not nested:
            cleaned.append(s)
    seeds = cleaned
    first_off_grid = next((e for e in off_grid if e["t0"] >= chain_lo), None)
    seed_names = [s["seed"] for s in seeds]
    letter_names = sorted(set(c for c in fired_classes))
    if seed_names or letter_names:
        death_class = ("+".join(seed_names) if seed_names else "UNEXPLAINED") + \
                      ("->" + "+".join(letter_names) if letter_names else "")
    else:
        death_class = None
    return dict(death_class=death_class, seeds=seeds, misfires=misfires,
                off_grid_eras=off_grid, first_off_grid_era=first_off_grid,
                drains=drains, folds=folds, fired_classes=letter_names,
                launch_drift=launch_drift,
                chain_start_tick=chain_start, chain_lo=chain_lo)
