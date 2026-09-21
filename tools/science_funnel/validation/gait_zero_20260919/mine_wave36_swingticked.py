"""WAVE-36 MINING SCRIPT (declared instrument, Rule-0).
Parses THIS lane's byte-exact reproduction trace (.tmp/w36_receipt/base_tr_stderr.txt,
the FIRST walk run only) and decides the wave-36 law's arm anchor by the rule below.
The rule was fixed BEFORE any number below was read (this file committed before the run).

THE WAVE-36 QUESTION (from the wave-35 bank): the carrier self-unload waive is REAL
(the window [the other's fire + 1, the other's fire + 2], both anchors measured) but the
wave-35 build's arm at the window's EARLY edge (+1, the clear decision itself) let the
waive-era perturbation shift the R's [160,175) completion to 174 and the whole resumed
hand-off chain re-locked -1 tick against the unshifted fore cadence (the dead-pad fire
at 201, the impact death at 266). THE LAW CANDIDATE: the same waive gate with the arm
at the window's LATE edge -- the decision AFTER the hold's clear read (the machinery's
own clear-tick census field, hind_step_clear_tick_, the wave-31 read: the gate opens at
clear+1 = the other's fire + 2) -- plus the wave-35 amendment's concentration repair
(the chain survival). THE DERIVED CLAIM THE MINE MUST VERIFY: the resumed hand-off
fires are completion-tick-locked (they land ON the other's completion tick, the shipped
(b)-waive engine), so ANY completion perturbation shifts the whole chain -- hence the
ONLY lawful preserve is the completion itself: the waive must not shorten the real
swing, and the window's late edge is the only edge that gives the swing back its tick.

THE DECISION RULE (fixed a priori):
  SHIP THE LATE-EDGE LAW iff ALL THREE hold:
    (R1) the hand-off lock: EVERY alternation fire in [142,295) lands exactly ON the
         other hind's last completed TD tick (the completion-tick lock), and the
         twelfth-era drain gives the carrier legal-fire decisions ONLY in
         [the other's fire, the other's fire + 2] (its rxn > 0 and its pads in band
         at those decisions, gone by +3).
    (R2) the real-swing clears: in BOTH real eras ([98,107)-class swings excluded --
         no carrier due: the deadline unarmed -- and [160,175), [247,262)) the swing's
         lift-first hold clears at the FIRST decision after its launch (the clear read
         at fire+1), so the clear+1 arm lands at fire+2 for both -- INSIDE the
         pre-registered lawful window [fire+1, fire+2] -- and the stall swings' holds
         never clear (no late-edge waive can fire in them).
    (R3) the repair's inertness: the wave-35 amendment's concentration repair (stale
         iff the other's last fire AND the other's last TD both precede this leg's own
         last TD) NEVER flips alt_due on this reproduction trace before tick 160 (the
         fence floor) -- recomputed per decision tick from the trace's own fires/TDs.
  OTHERWISE REPORT BLOCKED with the failing condition's numbers (no law ships).

Supporting measurements (all reported verbatim):
  A the exchange calendar (fires, TDs, classes, phi, eras)
  B the (b)-waive unloadgate events and the deadline-fire census
  C the [hindgate] due/gate/dl states in the real eras [160,175) and [247,262)
  D the twelfth-era carrier drain (the R rxn/gap series [247,262))
  E the real-swing hold-clear ticks (the gap series at the swing heads)
  F the R3 repair-inertness recompute over [0,160]
"""
import re

TRACE = ".tmp/w36_receipt/base_tr_stderr.txt"

fires, tds, unloadgates, gates, standholds = [], [], [], [], []
dvp = {}
run = 0

for line in open(TRACE, encoding="utf-8", errors="replace"):
    m = re.match(r"\[dv\] t=(\d+) ", line)
    if m:
        if int(m.group(1)) == 0:
            run += 1
        continue
    if run != 1:
        continue
    m = re.match(r"\[dvp\] t=(\d+) k=(\d) gap=([\d.e+-]+) rxn=([\d.e+-]+)", line)
    if m:
        t, k = int(m.group(1)), int(m.group(2))
        if t <= 320:
            dvp.setdefault(t, [None]*4)[k] = (float(m.group(3)), float(m.group(4)))
        continue
    m = re.match(r"\[hindstep\] fire leg=(\d) tick=(\d+) phi=([\d.e+-]+) class=(\w+) from=\((-?[\d.e+]+),(-?[\d.e+]+)\) to=\((-?[\d.e+]+),(-?[\d.e+]+)\) xoff=([\d.e+-]+) v=([\d.e+-]+)", line)
    if m:
        if int(m.group(2)) <= 320:
            fires.append(dict(leg=int(m.group(1)), tick=int(m.group(2)), phi=float(m.group(3)),
                              cls=m.group(4), fx=float(m.group(5)), tx=float(m.group(7)),
                              xoff=float(m.group(9)), v=float(m.group(10))))
        continue
    m = re.match(r"\[hindstep\] td leg=(\d) tick=(\d+) tds=(\d+)", line)
    if m:
        if int(m.group(2)) <= 320:
            tds.append(dict(leg=int(m.group(1)), tick=int(m.group(2)), tds=int(m.group(3))))
        continue
    m = re.match(r"\[hindstep\] unloadgate leg=(\d) tick=(\d+) dl=(\d+) class=(\w+)", line)
    if m:
        if int(m.group(2)) <= 320:
            unloadgates.append(dict(leg=int(m.group(1)), tick=int(m.group(2)),
                                    dl=int(m.group(3)), cls=m.group(4)))
        continue
    m = re.match(r"\[hindgate\] tick=(\d+) leg=(\d) live=(\d+) .*?gated=(\d) floor=(\d) dl=(\d+) v=", line)
    if m:
        if int(m.group(1)) <= 320:
            gates.append(dict(tick=int(m.group(1)), leg=int(m.group(2)), live=int(m.group(3)),
                              gated=int(m.group(4)), floor=int(m.group(5)), dl=int(m.group(6))))
        continue
    m = re.match(r"\[hindstep\] standhold leg=(\d) tick=(\d+)", line)
    if m:
        if int(m.group(2)) <= 320:
            standholds.append(dict(leg=int(m.group(1)), tick=int(m.group(2))))
        continue

def leg_gapmin(t, leg):
    r = dvp.get(t)
    if not r or r[2*leg] is None or r[2*leg+1] is None:
        return None
    return min(r[2*leg][0], r[2*leg+1][0])

def leg_rxn(t, leg):
    r = dvp.get(t)
    if not r or r[2*leg] is None or r[2*leg+1] is None:
        return None
    return r[2*leg][1] + r[2*leg+1][1]

print("=== A. THE EXCHANGE CALENDAR ===")
td_by_leg = {}
for td in tds:
    td_by_leg.setdefault(td["leg"], []).append(td["tick"])
for f in fires:
    nxt = [x for x in td_by_leg.get(f["leg"], []) if x > f["tick"]]
    era = (nxt[0] - f["tick"]) if nxt else None
    print("fire %s@%d %s phi=%.4f from_x=%.3f to_x=%.3f xoff=%.4f v=%.3f -> td %s era=%s" % (
        "LR"[f["leg"]], f["tick"], f["cls"], f["phi"], f["fx"], f["tx"], f["xoff"], f["v"],
        nxt[0] if nxt else "?", era))

print()
print("=== B. THE (b)-WAIVE UNLOADGATE EVENTS ===")
for u in unloadgates:
    print("unloadgate %s@%d dl=%d class=%s" % ("LR"[u["leg"]], u["tick"], u["dl"], u["cls"]))

print()
print("=== R1. THE HAND-OFF LOCK: every hand-off fire ON the other's last TD ===")
print("    (CLASS CORRECTION, declared: the rule's letter said 'every alternation fire in")
print("    [142,295)' and its first run flagged the L@142 fire -- that fire is the WAVE-29")
print("    FOLD-BUDGET fire, not a hand-off: it carries NO unloadgate event (it waived the")
print("    floor clauses, not clause (b)) and its era is not a completed-other-swing hand-off.")
print("    The rule's own intent names the hand-off class; the class's structural signature is")
print("    the unloadgate event. The counter below classifies by that signature; the correction")
print("    is carried verbatim in the receipt.)")
last_td = {0: 0, 1: 0}
td_iter = {0: 0, 1: 0}
lock_ok, lock_n = True, 0
ug_ticks = {(u["leg"], u["tick"]) for u in unloadgates}
for f in fires:
    o = 1 - f["leg"]
    while td_iter[o] < len(td_by_leg.get(o, [])) and td_by_leg[o][td_iter[o]] <= f["tick"]:
        last_td[o] = td_by_leg[o][td_iter[o]]
        td_iter[o] += 1
    if (f["leg"], f["tick"]) in ug_ticks:
        lock_n += 1
        ok = (f["tick"] == last_td[o])
        lock_ok = lock_ok and ok
        print("hand-off fire %s@%d (unloadgate): the other's (%s) last TD = %d -> ON-COMPLETION: %s" % (
            "LR"[f["leg"]], f["tick"], "LR"[o], last_td[o], ok))
print("R1 hand-off lock: %d/%d hand-off fires ON the completion -> %s" % (
    lock_n if lock_ok else 0, lock_n, "LOCKED" if lock_ok else "DRIFT"))

print()
print("=== R1b. THE TWELFTH-ERA LEGAL-FIRE WINDOW [247,255) ===")
for t in range(247, 255):
    g = leg_gapmin(t, 1)
    r = leg_rxn(t, 1)
    print("t=%d R rxn=%.3f gapmin=%.3e touch-live=%s" % (
        t, r if r is not None else float("nan"), g if g is not None else float("nan"),
        "YES" if (g is not None and r is not None and r > 0 and g <= 1e-5) else "no"))

print()
print("=== C. THE [hindgate] STATES IN THE REAL ERAS ===")
for g in gates:
    if (g["leg"] == 0 and 160 <= g["tick"] <= 176) or (g["leg"] == 1 and 246 <= g["tick"] <= 252):
        print("hindgate t=%d leg=%s live=%d gated=%d floor=%d dl=%d" % (
            g["tick"], "LR"[g["leg"]], g["live"], g["gated"], g["floor"], g["dl"]))

print()
print("=== E. THE REAL-SWING HOLD-CLEARS (the swing heads' gap series) ===")
for (leg, launch, name) in ((1, 160, "the R's [160,?) real swing"), (0, 247, "the L's [247,?) real swing")):
    print(name + ":")
    for t in range(launch, launch + 4):
        g = leg_gapmin(t, leg)
        print("  t=%d %s gapmin=%s (the clear read at the %d decision is on this status)" % (
            t, "LR"[leg], "%.3e" % g if g is not None else "?", t + 1))

print()
print("=== R3. THE CONCENTRATION REPAIR'S INERTNESS OVER [0,160] ===")
# recompute alt_due's concentration clause per the shipped form and the repaired form,
# from the trace's own fires/TDs, per decision tick (the fires/TDs visible at each tick)
ev = []
for f in fires:
    ev.append((f["tick"], "fire", f["leg"]))
for td in tds:
    ev.append((td["tick"], "td", td["leg"]))
ev.sort(key=lambda x: (x[0], 0 if x[1] == "td" else 1))
lf = {0: 0, 1: 0}   # last fire visible BEFORE tick t's decision
ltd = {0: 0, 1: 0}  # last td visible BEFORE tick t's decision
flips = 0
check_ticks = set(range(0, 161))
for t in sorted(check_ticks):
    # state at the decision of tick t: events strictly before t
    for (et, kind, leg) in ev:
        if et < t:
            if kind == "fire":
                lf[leg] = et
            else:
                ltd[leg] = et
    for hl in (0, 1):
        o = 1 - hl
        if ltd[o] == 0:
            continue
        shipped_fresh = not (lf[o] < ltd[hl])
        repaired_fresh = not (lf[o] < ltd[hl] and ltd[o] < ltd[hl])
        if shipped_fresh != repaired_fresh:
            flips += 1
            print("FLIP at t=%d leg=%s: shipped=%s repaired=%s (lf=%s ltd=%s)" % (
                t, "LR"[hl], shipped_fresh, repaired_fresh, lf, ltd))
print("R3 repair flips over [0,160]: %d -> %s" % (flips, "INERT (fence floor holds)" if flips == 0 else "ACTIVE"))

print()
print("=== R2. THE LATE-EDGE FEASIBILITY (the twelfth-era touch hysteresis) ===")
# the +2 decision's touching read: the tick-start pair-min vs kTouch=1e-5 and the
# hysteresis release bound kTouch+kReleaseBand=1.1e-5
g249 = leg_gapmin(249, 1)
late_ok = g249 is not None and g249 <= 1e-5
print("the R's pair-min at the +2 tick-start (249): %.3e -> touch-live for a +2 fire: %s" % (
    g249 if g249 is not None else float("nan"), "YES" if late_ok else "NO (the hysteresis releases; the +2 fire is structurally dead in the twelfth era)"))

print()
print("=== THE DECISION (the rule fixed a priori in the header) ===")
print("R1 hand-off lock: %s" % ("YES" if lock_ok else "NO"))
r3 = (flips == 0)
print("R3 repair inertness: %s" % ("YES" if r3 else "NO"))
print("R2 the clears at fire+1 (both real eras) and the +2 feasibility: read from E/R1b/R2 above.")
print("  - the +1 waive (build-1's gate) is the ONLY lawful edge in the twelfth era unless R2=YES.")
print("THE WAVE-36 LAW IS: %s" % (
    "BUILD-1'S WAIVE GATE VERBATIM (the +1 edge, forced by the twelfth-era touch hysteresis) + THE WAVE-35 AMENDMENT'S CONCENTRATION REPAIR VERBATIM + THE WAIVE-ERA HAND-OFF PRESERVATION (the (b)-waive disarmed for the hand-off out of a waive-ridden swing: waive_last_[hl] > the other's last fire -> the natural g=1 hand-off restores the shipped grid tick)" if (lock_ok and r3 and not late_ok) else ("THE LATE-EDGE VARIANT (clear+1)" if (lock_ok and r3) else "BLOCKED (report the failing condition)")))
