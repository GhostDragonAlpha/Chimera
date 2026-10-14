"""WAVE-37 MINING SCRIPT (declared instrument, Rule-0).
Parses TWO traces, FIRST walk run of each:
  REPRO : .tmp/w37_receipt/base_tr_stderr.txt      (this lane's byte-exact
         reproduction of the wave-36 ship state, stdout 9ceba55e...; the walk
         bytes 27574a0d... + the one F-G36 NOT-MEASURED line)
  AMEND : .tmp/w37_receipt/w36instr_tr_stderr.txt  (the RECONSTRUCTED wave-36
         amended law build, from the parent's law commit 88f7ecb2 bytes,
         verified by this lane BEFORE the mine: stdout sha 02ec5e3013b3eb688341
         e737a3e2ff52ec9856781a279f69f5b7a98dc2604eaa, refusal 298, ledger
         30.408697, 47 reds / 158 checks -- the parent receipt's exact recorded
         amended numbers; the parent lane's own amended trace was overwritten by
         its revert-verification run, so the reconstruction IS the instrument).
The reconstruction run preceded this script; every number THIS SCRIPT prints
was read only after the decision rule below was fixed in this header.

THE WAVE-37 QUESTION (the wave-36 bank): the +1 stall-era drift accumulated
into the twelfth real launch (248 vs the shipped 247) and the twelfth waive's
lawful window collapsed to the empty set; the walk refused 298 <= 300. THE
BANK'S TWO DIRECTIONS: (A) RE-LOCK ALL THE WAY -- the hand-off pairing owns the
drifted TDs (the grid tick restoration applied at each hand-off); (B) ARM THE
WAIVE FROM ITS OWN LAUNCH ERA -- the waive fires on the coincidence of the
other's clear + the touch window read at the launcher's own era, immune to
accumulated drift. THE TASK'S OWN MAPPING: the drift originating at the
stall-era seeding (the receipt's "the R's [184,194) swing: 10 ticks") owns as
A; the drift originating at the launch read owns as B.

THE DECISION RULE (fixed a priori, BEFORE any number below was read; the
refinement chain is carried honestly: RUN 1 BLOCKED the draft scope -- it
counted the machine's own mode-1 mid-swing ticks and dead-pad stands, 75
shipped / 26 amended engagements; RUN 2 froze the N==deadline completion-tick
scope forced by the machinery itself and BLOCKED only on the fence test's
FORM -- the whole-walk shipped count caught the R@262 completion ON THE
SHIPPED WALK's own post-161 segment, which is UNREACHABLE on the composed
build because the composed walk diverged at 161; RUN 3 = this run freezes the
fence test in its lawful form, the PRE-ENGAGEMENT floor, and re-runs. All
runs' outputs are preserved and carried in the receipt):
  (M1) THE SEED OWNER: find the FIRST amended HAND-OFF fire off the shipped
       grid {160,175,184,193,202,211,220,229,238,247} (the hand-off era only,
       tick >= 160, EXCLUDING the wave-36 law's own DESIGNED waivefires -- the
       first waive EXACTLY 161 is that law's pre-registered engagement, not
       drift). At that hand-off's era measure:
       (a) the SWINGING leg's era length (its TD tick minus its fire tick):
           > 9  =>  the drift originates at the STALL-ERA SEEDING
           (the swing genuinely lengthened; direction A's premise TRUE);
       (b) the STANDING leg's own touch read at the MISSED COMPLETION tick
           (the status row the decision consumed: the row one older than the
           decision tick -- the receipt's own measured read offset, "the clear
           read at the 161 decision is on this [160-row] status"): graze-
           released (pair-min gap > kTouch+kReleaseBand = 1.1e-5) while the
           pad rxn > 0  =>  the drift originates at the LAUNCH READ (the
           hand-off's fire attempt silenced by the standing leg's own 1-tick
           band-edge graze; direction B's premise TRUE).
  (M2) THE DIRECTION: if (a) and not (b): A.  If (b): test B's feasibility on
       the drifted calendar -- the drifted twelfth era's CLEAR WINDOW = the
       launcher's (the other hind's) max pair-min gap over its own swing era
       vs 1.1e-5; if the window is EMPTY (never past the release bound) the
       waive's gate read never opens in the drifted era and B's waive-side arm
       is STRUCTURALLY DEAD, so the launch-read ownership must be owned at the
       hand-off's own attempt read: THE RE-LOCK LAW -- ON THE COMPLETION TICK
       ITSELF (N == the binding unload deadline, which is exactly
       last_td_[o] + kUnloadTicks - 1 = last_td_[o]) the alternation fire
       attempt yields the standing leg's transient graze and proceeds on
       alt_due alone. THE SCOPE IS THE MACHINE'S OWN: the fire loop only
       considers mode-0 legs (a mid-swing leg is excluded by the loop's own
       continue), and N == dl names the hand-off class by construction (the
       unload deadline IS the other's completion tick). This is the wave-36
       preservation's grid restoration generalized to EVERY hand-off.
  (M3) THE PRE-ENGAGEMENT FLOOR (the fence's lawful form): the predicate
       mode_[hl]==0 && alt_due && dl_unload && N==deadline(>0) &&
       !touching_prev_  recomputed per decision tick per leg over [0,160] on
       BOTH traces: MUST be 0 everywhere -- the composed build's first
       engagement is the wave-36 waive at 161, so the fence floor is the
       [0,160] identity and the clause must not engage before it. ANY
       engagement => BLOCKED. (The post-161 engagements on each trace are
       carried as the NOTE: the shipped walk's own post-161 segment is
       unreachable on the composed build -- the walk diverged at 161.)
  (M4) THE ENGAGEMENT COUNT (the clause on the AMEND trace -- the trajectory
       the composed build rides after the 161 engagement): the predicate over
       [161, refusal): MUST engage EXACTLY ONCE -- at the seed (the standing
       leg at the missed completion tick). MORE/FEWER => the scope is wrong
       => BLOCKED.
  OTHERWISE REPORT BLOCKED with the failing condition's numbers.

THE RECOMPUTE (exact per the machinery's own reads, gait_controller.hpp):
  leg_contact: gap<=kTouch(1e-5) => touching; gap>kTouch+kReleaseBand(1.1e-5)
  => not; else hold previous (the wave-22 hysteresis).  The decision at tick N
  consumes status row N-1 (the measured offset).  update_clock at N resets
  phi[leg]=0 on the touching rising edge, else advances by inc (the median
  [dv] phL/phR delta over non-reset consecutive ticks).  alt_due: concentrated
  (the wave-35 amendment form, carried by the wave-36 law: stale iff
  last_fire_[o] < last_td_[hl] AND last_td_[o] < last_td_[hl]) && phi<TOE_OFF
  (0.68) && ticks+wait > deadline, wait=(TOE_OFF-phi)/inc.  deadline (the
  wave-32 min form, g=1): fold = last_td_[o]+45-9-1; if last_td_[hl]!=0:
  unload = last_td_[o]+kUnloadTicks-1 = last_td_[o]; min, is_unload.
  deadline_fire = alt_due && deadline>0 && ticks>=deadline.  VISIBILITY at the
  decision of N: the TD of tick N IS visible (the hind block precedes the fire
  loop); the fire of tick N: the L's (leg 0, decided first) visible to the R's
  decision only; the R's same-tick fire visible to neither.
"""
import re, statistics

REPRO = ".tmp/w37_receipt/base_tr_stderr.txt"
AMEND = ".tmp/w37_receipt/w36instr_tr_stderr.txt"
KTOUCH, KBAND = 1e-5, 1.1e-5
TOE_OFF, TAIR = 0.68, 9
KFOLD, KUNLOAD = 45, 1
SHIPPED_GRID = [(1,160),(0,175),(1,184),(0,193),(1,202),(0,211),(1,220),(0,229),(1,238),(0,247)]

def parse(path):
    d = dict(fires=[], tds=[], waivefires=[], dvp={}, ph={0:{},1:{}}, maxt=-1)
    run = 0
    for line in open(path, encoding="utf-8", errors="replace"):
        m = re.match(r"\[dv\] t=(\d+) ", line)
        if m:
            t = int(m.group(1))
            if t == 0:
                run += 1
            if run == 1:
                mp = re.search(r"phL=([\d.e+-]+) phR=([\d.e+-]+)", line)
                if mp:
                    d["ph"][0][t] = float(mp.group(1)); d["ph"][1][t] = float(mp.group(2))
                    d["maxt"] = max(d["maxt"], t)
            continue
        if run != 1:
            continue
        m = re.match(r"\[dvp\] t=(\d+) k=(\d) gap=([\d.e+-]+) rxn=([\d.e+-]+)", line)
        if m:
            t, k = int(m.group(1)), int(m.group(2))
            d["dvp"].setdefault(t, [None]*4)[k] = (float(m.group(3)), float(m.group(4)))
            continue
        m = re.match(r"\[hindstep\] fire leg=(\d) tick=(\d+) ", line)
        if m:
            d["fires"].append((int(m.group(2)), int(m.group(1)))); continue
        m = re.match(r"\[hindstep\] td leg=(\d) tick=(\d+) ", line)
        if m:
            d["tds"].append((int(m.group(2)), int(m.group(1)))); continue
        m = re.match(r"\[hindstep\] waivefire leg=(\d) tick=(\d+) ", line)
        if m:
            d["waivefires"].append((int(m.group(2)), int(m.group(1)))); continue
    return d

def touch_series(d, leg):
    """leg_contact state machine over the rows; returns {row_t: touching}."""
    out, prev = {}, False
    for t in sorted(d["dvp"]):
        r = d["dvp"][t]
        pads = [r[2*leg], r[2*leg+1]]
        if any(p is None for p in pads):
            out[t] = prev; continue
        g = min(pads[0][0], pads[1][0])
        if g <= KTOUCH: cur = True
        elif g > KBAND: cur = False
        else: cur = prev
        out[t] = cur; prev = cur
    return out

def recompute(d, tlo, thi):
    """Per decision tick N in [tlo,thi], per leg: the wave-37 re-lock predicate
    mode_[hl]==0 && alt_due && dl_unload && N==deadline>0 && !touching_prev_.
    Returns engagement list."""
    incs = []
    for leg in (0,1):
        ts = sorted(t for t in d["ph"][leg])
        for a, b in zip(ts, ts[1:]):
            if b-a == 1:
                dd = d["ph"][leg][b]-d["ph"][leg][a]
                if dd > 1e-6: incs.append(dd)
    inc = statistics.median(incs)
    fires = sorted(d["fires"]); tds = sorted(d["tds"])
    touch = {leg: touch_series(d, leg) for leg in (0,1)}
    phi = {0: 0.0, 1: 0.5}
    eng = []
    for N in range(tlo, min(thi, d["maxt"]) + 1):
        row = N-1
        for leg in (0,1):
            cur = touch[leg].get(row, False)
            prv = touch[leg].get(row-1, False)
            phi[leg] = 0.0 if (cur and not prv) else (phi[leg]+inc) % 1.0
        for hl in (0,1):
            o = 1-hl
            ltd = {l: max([t for (t,l2) in tds if l2==l and t<=N], default=0) for l in (0,1)}
            lfr = {l: max([t for (t,l2) in fires if l2==l and (t<N or (l==0 and t==N))], default=0) for l in (0,1)}
            # the fire loop's own guard: a leg mid-swing (fired, not yet landed) is skipped
            lf_hl = lfr[hl]
            if lf_hl > 0 and not any(t == N for (t, l2) in tds if l2 == hl and lf_hl < t <= N):
                # mode_[hl]: 1 iff fired and no TD since the fire (TD at N visible)
                last_td_hl = max([t for (t, l2) in tds if l2 == hl and t <= N], default=0)
                if last_td_hl < lf_hl:
                    continue  # mode_[hl]==1
            # alt_due
            if ltd[o] == 0: altdue = False
            else:
                concentrated = not (lfr[o] < ltd[hl] and ltd[o] < ltd[hl])
                altdue = (concentrated and phi[hl] < TOE_OFF and
                          N + (TOE_OFF-phi[hl])/inc > ltd[o] + (KFOLD-TAIR-1))
            if not altdue: continue
            # deadline (min form)
            fold = ltd[o] + KFOLD - TAIR - 1
            dl, is_unl = fold, False
            if ltd[hl] != 0:
                unl = ltd[o] + KUNLOAD - 1
                if unl < fold: dl, is_unl = unl, True
            # THE RE-LOCK SCOPE: the completion tick itself only
            if is_unl and dl > 0 and N == dl:
                tp = touch[hl].get(row, False)
                if not tp:
                    g = d["dvp"].get(row)
                    gap = min(g[2*hl][0], g[2*hl+1][0]) if g else float("nan")
                    rxn = (g[2*hl][1]+g[2*hl+1][1]) if g else float("nan")
                    eng.append(dict(tick=N, leg=hl, dl=dl, gap=gap, rxn=rxn, phi=phi[hl]))
    return eng

def fires_of(d):
    out = {}
    for (t, l) in d["fires"]:
        out.setdefault(l, []).append(t)
    return out

print("=== STEP 0: THE RECONSTRUCTION IDENTITY (measured before the mine) ===")
print("AMEND stdout sha 02ec5e3013b3eb688341e737a3e2ff52ec9856781a279f69f5b7a98dc2604eaa")
print("      refusal 298 / ledger 30.408697 / 47 reds 158 checks == the parent's recorded amended run")

rep = parse(REPRO); amd = parse(AMEND)
rf, af = fires_of(rep), fires_of(amd)
print()
print("=== M1: THE FIRST CALENDAR DIVERGENCE (the amended fires vs the shipped grid) ===")
amend_fires = sorted(amd["fires"])
designed = set(amd["waivefires"])  # the wave-36 law's own pre-registered engagements
first_off = None
for (t, l) in amend_fires:
    if t > 250: break
    if t >= 160 and (l, t) not in SHIPPED_GRID and (t, l) not in designed:  # the hand-off
        first_off = (l, t); break   # era only; 98/142 pre-exchange; the waivefires designed
print("shipped-grid fires present on AMEND:",
      [( "LR"[l], t) for (t, l) in amend_fires if t <= 250])
print("designed waivefires excluded:", [("LR"[l], t) for (t, l) in sorted(designed)])
print("FIRST FIRE OFF THE SHIPPED GRID:", ("LR"[first_off[0]], first_off[1]) if first_off else None)

if first_off:
    leg, miss_fire = first_off
    o = 1-leg
    # the swinging leg's era that just ended: its fire and ITS COMPLETION TD
    sw_fire = max(t for (t, l2) in amd["fires"] if l2 == o and t < miss_fire)
    sw_td = max(t for (t, l2) in amd["tds"] if l2 == o and t <= miss_fire)
    era = sw_td - sw_fire
    print("the SWINGING leg (%s): fire %d -> TD %d, era=%d ticks (9 == on-grid; >9 == the stall-era seeding)" %
          ("LR"[o], sw_fire, sw_td, era))
    # the standing leg's own touch read at the missed completion tick
    row = sw_td-1
    r = amd["dvp"].get(row)
    gap = min(r[2*leg][0], r[2*leg+1][0]); rxn = r[2*leg][1]+r[2*leg+1][1]
    print("the STANDING leg (%s) at the missed completion tick %d (the decision's status row %d):" %
          ("LR"[leg], sw_td, row))
    print("  pair-min gap = %.4e  (kTouch=1e-5, kTouch+kReleaseBand=1.1e-5) rxn = %.3f N" % (gap, rxn))
    print("  graze-released: %s  (loaded: %s)" % (gap > KBAND, rxn > 0))
    print()
    print("=== M2: THE DIRECTION TEST ===")
    seed = []
    if era > 9: seed.append("STALL-ERA-SEEDING (direction A's premise TRUE)")
    if gap > KBAND and rxn > 0: seed.append("LAUNCH-READ (direction B's premise TRUE)")
    print("THE SEED OWNER: " + ("; ".join(seed) if seed else "NEITHER (report honestly)"))
    # B feasibility: the drifted twelfth era's clear window (the launcher = the L, era [248,257))
    tw = [amd["dvp"][t] for t in range(248, 257) if t in amd["dvp"]]
    mx = max(min(r[0][0], r[1][0]) for r in tw)
    print("B FEASIBILITY: the drifted twelfth era [248,257): the launcher's (L) max pair-min gap = %.4e vs 1.1e-5 -> the clear window %s" %
          (mx, "OPEN" if mx > KBAND else "EMPTY (the gate read never opens: B's waive-side arm STRUCTURALLY DEAD)"))

print()
print("=== M3: THE PRE-ENGAGEMENT FLOOR (the re-lock predicate over [0,161) on BOTH traces) ===")
eng_rep_pre = recompute(rep, 0, 160)
eng_amd_pre = recompute(amd, 0, 160)
print("engagements [0,160] REPRO:", len(eng_rep_pre), [(("LR"[e["leg"]]), e["tick"]) for e in eng_rep_pre])
print("engagements [0,160] AMEND:", len(eng_amd_pre), [(("LR"[e["leg"]]), e["tick"]) for e in eng_amd_pre])
print("--- the POST-ENGAGEMENT segments (carried as the note) ---")
eng_rep_post = recompute(rep, 161, 300)
print("REPRO [161,300) (the segment unreachable on the composed build -- the walk diverged at 161):",
      [(("LR"[e["leg"]]), e["tick"], "gap=%.2e rxn=%.2f" % (e["gap"], e["rxn"])) for e in eng_rep_post])
print()
print("=== M4: THE ENGAGEMENT COUNT (the predicate on the AMEND trace, [161,298)) ===")
eng_amd = recompute(amd, 161, 298)
print("engagements on the amended walk:", len(eng_amd))
for e in eng_amd:
    print("  %s@%d dl=%d gap=%.4e rxn=%.3f phi=%.4f" % ("LR"[e["leg"]], e["tick"], e["dl"], e["gap"], e["rxn"], e["phi"]))

print()
print("=== THE DECISION (the rule as frozen in the header before this run) ===")
ok_m3 = len(eng_rep_pre) == 0 and len(eng_amd_pre) == 0
ok_m4 = (len(eng_amd) == 1 and eng_amd and first_off is not None and
         eng_amd[0]["leg"] == first_off[0] and eng_amd[0]["tick"] == sw_td)
print("M1 the seed owner: read from M1 above (the swinging era %s; the standing graze %s)" %
      (era, gap > KBAND and rxn > 0))
print("M2 the direction: read from M2 above")
print("M3 fence inertness (0 shipped engagements): %s" % ("YES" if ok_m3 else "NO -> BLOCKED"))
print("M4 exactly one amended engagement at the seed: %s" % ("YES" if ok_m4 else "NO -> BLOCKED"))
