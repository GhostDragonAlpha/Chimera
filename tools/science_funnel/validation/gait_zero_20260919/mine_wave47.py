#!/usr/bin/env python3
"""THE WAVE-47 MINE (declared instrument receipt_wave47.json, committed BEFORE
this run -- freeze 56173bc3, freeze sha 71e32e552812f2da1040a9f00958e588b4e0ab
df8934f6cdf6c79ce3ad7f9626). Reads THIS LANE'S SHIP TRACE ONLY:
.tmp/w47_receipt/base_tr_stderr.txt (the f106fc54 reproduction trace: stdout
8c537cdb EXACT, plain==trace byte-equal, refusal 302, ledger 30.970714, 49/173;
the trace c6f9b6c0, 65870 lines). Parses the LAST walk run (the wave-39..46
declared convention). [hindstep]/[dvfl] event lines DEDUPED by full line text.

THE QUESTION (the wave-46 bank): does a DERIVATION exist for a rate-side hold
clause from the machinery's own scales -- or does the record stand?

THE WAVE-46 CALIBRATION (verbatim): plane_model_y_ = contact_plane_height_m =
0.004 (the construction shift V{0,0,0} at every GaitWalker site), pad radius
= 0.004, so split_abs(t) = 2*(pad_y(t) - gmin(t)); the [dvfa]/[dvfl] FIRST
sample per (t,leg) is the tick-start basis; the era span [f, ct]. The wave-45
lever lever(t) = split_abs(t) - sref with sref = 2*(pad_y(f) - gmin(f+1)).

NEW THIS WAVE (the declared extension): THE PER-TICK INCREMENT CENSUS -- per
era the split increment series inc(t) between consecutive band samples (the
RATE the clause would threshold), plus the per-era era-rate (max lever over
the era's tick span).

THE CANDIDATE TABLE (the frozen receipt list, recorded chains ONLY) and the
frozen R1 rulings are applied mechanically; R2/R3 are measured HERE. Output:
mine_wave47_out.txt (this run's preserved output).
"""
import re, collections

TRACE = ".tmp/w47_receipt/base_tr_stderr.txt"

# ---- the frozen machinery inventory (receipt_wave47.json, citations there) ----
G = 9.80665
DT = 1.0 / 300.0
KTOUCH, KSLIP, KREL = 1e-5, 1e-9, 1e-6
EDGE = KTOUCH + KREL                      # 1.1e-5 m
T_CYCLE, DUTY, TOE_OFF = 0.71, 0.683, 0.68
FS_HZ, ZETA, CAP_PHI = 4.0, 0.8, 0.95
import math
TAIR = math.ceil((T_CYCLE - DUTY) / DT)   # 9 ticks
TAU_SETTLE_TICKS = (1.0 / (ZETA * 2 * math.pi * FS_HZ)) / DT  # 14.92
MU = 0.6
C_ARCH = 2 * 0.004                        # 0.008 m (wave-42)
GDT2 = G * DT * DT                        # 1.089628e-4 m/tick
KSINK = 0.002349                          # m/tick (wave-27 mining pattern)
VDIV = MU * G * (1 - CAP_PHI) * T_CYCLE   # v_bound m/s
VBDT = VDIV * DT                          # m/tick
ENGAGE = 1e-3 * DT                        # plane-engagement gate m/tick

# (name, rate m/tick, level mm = rate*TAIR*1e3, R1 frozen ruling, R1 chain)
CANDIDATES = [
    ("edge/tair (the release law's own)", EDGE / TAIR, "PASS",
     "the release law's own distance over the hold's own nominal air time"),
    ("kTouch/tair", KTOUCH / TAIR, "PASS", "the release law's own constant"),
    ("kReleaseBand/tair", KREL / TAIR, "PASS", "the solver's own gap quantum"),
    ("kSlip/tair", KSLIP / TAIR, "PASS", "the release law's own constant"),
    ("g*dt^2 (the wave-22 free-fall quantum)", GDT2, "FAIL",
     "translational unconstrained fall; a rigid sole in free fall keeps its "
     "split CONSTANT (both pads fall equally) -- no handle on the rotational DOF"),
    ("kSinkRateMax (the wave-27 mining pattern)", KSINK, "FAIL",
     "the worst measured rate of a MACHINERY-SEMANTIC quantity (sh_min); the "
     "lift/stall split-rate classes have NO machinery-side semantic to mine "
     "(the split is erased from every machinery read)"),
    ("v_bound*dt (the capture slip budget)", VBDT, "FAIL",
     "horizontal body-slip budget under friction vs the capture step window; "
     "no chain to sole rotation or the hold's release"),
    ("c/tair (the commanded swing rise)", C_ARCH / TAIR, "FAIL",
     "the glide's COMMANDED rise; the commanded SPLIT rate is zero (the glide "
     "preserves the paw's presentation)"),
    ("c*pi/(2*tair) (the glide arch max slope)", C_ARCH * math.pi / (2 * TAIR), "FAIL",
     "commanded translation, not split rotation"),
    ("kDiveRateMax (joint-space, rad/tick)", 0.004020, "FAIL",
     "rad/tick, not a pad quantity; the wave-44 verdict: the joint-space image "
     "is a pure pose function, class-blind"),
    ("dt/T_CYCLE (the clock rate, 1/tick)", DT / T_CYCLE, "FAIL",
     "dimensionless phase, not a pad distance"),
    ("the plane-engagement gate*dt", ENGAGE, "FAIL",
     "solver engagement, translational approach velocity"),
]

lines = open(TRACE, encoding="utf-8", errors="replace").read().splitlines()
idx = [i for i, l in enumerate(lines) if l.startswith("WALK REFUSED")]
run = lines[idx[-2] + 1:idx[-1]]
mref = re.match(r"WALK REFUSED tick (\d+): (\S+)", lines[idx[-1]])
refus = (int(mref.group(1)), mref.group(2))

dvfa = collections.defaultdict(dict)
fires = []
tds = []
dvfl = collections.defaultdict(dict)
seen_ev = set()
for l in run:
    m = re.match(r"\[dvfa\] t=(\d+) leg=(\d) br=(\w) held=(\d) sg=(\S+) c=(\S+) cmd_y=(\S+) pad_y=(\S+) plant_y=(\S+)", l)
    if m:
        t, leg = int(m.group(1)), int(m.group(2))
        if leg not in dvfa[t]:
            dvfa[t][leg] = (m.group(3), int(m.group(4)), float(m.group(5)), float(m.group(6)),
                            float(m.group(7)), float(m.group(8)), float(m.group(9)))
        continue
    m = re.match(r"\[dvfl\] t=(\d+) leg=(\d) g1=(\S+) g2=(\S+) edge=(\S+) hd=(\d) ht=(\d+) tm=(\S+) clr=(-?\d+) oth=(\d) dl=(\d+)", l)
    if m:
        t, leg = int(m.group(1)), int(m.group(2))
        rec = dict(g1=float(m.group(3)), g2=float(m.group(4)), edge=float(m.group(5)),
                   hd=int(m.group(6)), ht=int(m.group(7)), tm=float(m.group(8)),
                   clr=int(m.group(9)), oth=int(m.group(10)), dl=int(m.group(11)))
        if leg not in dvfl[t]: dvfl[t][leg] = rec
        continue
    if l.startswith("[hindstep]"):
        if l in seen_ev: continue
        seen_ev.add(l)
        m = re.match(r"\[hindstep\] fire leg=(\d) tick=(\d+) phi=\S+ class=(\S+) from=\((\S+),(\S+)\) to=\((\S+),(\S+)\) xoff=(\S+) v=(\S+) qerr=(\S+) ap=\S+ br=\S+ dl=(\d+)", l)
        if m:
            fires.append((int(m.group(2)), int(m.group(1)), m.group(3),
                          float(m.group(5)), float(m.group(10)), int(m.group(11)))); continue
        m = re.match(r"\[hindstep\] td leg=(\d) tick=(\d+)", l)
        if m: tds.append((int(m.group(2)), int(m.group(1)))); continue

out = open(".tmp/w47_receipt/mine_wave47_out.txt", "w", encoding="utf-8")
def P(*a):
    s = " ".join(str(x) for x in a)
    out.write(s + "\n"); print(s)

P("refusal:", refus, " fires:", len(fires), " tds:", len(tds),
  " dvfl (t,leg) first-sample series:", len(dvfl), " dvfa series:", len(dvfa))
P("THE WAVE-46 CALIBRATION (verbatim): plane_model_y_=0.004, pad radius=0.004, shift V{0,0,0} =>"
  " split_abs=2*(pad_y-gmin); sref=2*(pad_y(fire)-gmin(fire+1)); lever(t)=split_abs(t)-sref.")
P("-" * 150)

# ---- per-era series + the increment census ----
rows = []
for (ft, leg, cls, fy, qerr, dl) in fires:
    comp = next(((t, l) for (t, l) in tds if l == leg and t >= ft), None)
    ct = comp[0] if comp else max(t for t in dvfa if leg in dvfa[t] and t > ft)
    a0 = dvfa.get(ft, {}).get(leg)
    if a0 is None: continue
    ser = []  # (t, gmin, pad_y, split_abs, lever)
    fy_pad = a0[5]
    g0 = min(dvfl[ft + 1][leg]["g1"], dvfl[ft + 1][leg]["g2"]) if dvfl.get(ft + 1, {}).get(leg) else float("nan")
    sref = 2.0 * (fy_pad - g0)
    for t in range(ft + 1, ct + 1):
        a = dvfa.get(t, {}).get(leg); b = dvfl.get(t, {}).get(leg)
        if a is None or b is None: continue
        gmin = min(b["g1"], b["g2"]); py = a[5]
        sa = 2.0 * (py - gmin)
        ser.append((t, gmin, py, sa, sa - sref))
    if not ser: continue
    maxlev = max(s[4] for s in ser)
    span = ct - ft
    # the per-tick increment census: inc(f+1) vs sref, then consecutive samples
    incs = [(ser[0][0], ser[0][4])]
    for i in range(1, len(ser)):
        incs.append((ser[i][0], ser[i][4] - ser[i - 1][4]))
    maxinc = max(s[1] for s in incs)
    # era class by the wave-41..46 DEL convention (DEL = the delivered descent)
    cmd_peak = -1e9; del_peak = -1e9
    for t in range(ft, ct + 1):
        a = dvfa.get(t, {}).get(leg)
        if a is None: continue
        cmd_y, pad_y = a[4], a[5]
        cmd_peak = max(cmd_peak, (cmd_y - fy) * 1e3)
        del_peak = max(del_peak, (pad_y - fy) * 1e3)
    era_class = "STALL" if del_peak < 1.0 else "LIFT"
    bser = [dvfl[t][leg] for t in range(ft + 1, ct + 1) if leg in dvfl.get(t, {})]
    cross = next((ft + 1 + i for i, b in enumerate(bser) if b["hd"] == 0), None)
    rows.append(dict(ft=ft, ct=ct, leg=leg, era_class=era_class, cls=cls,
                     span=span, n=len(ser), maxlev=maxlev, maxinc=maxinc,
                     rate_span=maxlev / span, cross=cross, ser=ser, incs=incs,
                     del_peak=del_peak))

never = [r for r in rows if r["cross"] is None]
P("ERA RATE CENSUS (F-G47a): fire->ct leg class span nSamp maxLever leverRate(maxLever/span) maxInc eraClassLabels=wave-45/46")
for r in rows:
    P("  %4d->%4d leg=%d %-5s(%-3s) span=%2d nB=%2d leverMax=%+8.3f mm rate=%+7.3f mm/tick maxInc=%+7.3f mm/tick cross=%s"
      % (r["ft"], r["ct"], r["leg"], r["era_class"], r["cls"], r["span"], r["n"],
         r["maxlev"] * 1e3, r["rate_span"] * 1e3, r["maxinc"] * 1e3,
         r["cross"] if r["cross"] is not None else "never"))
P("-" * 150)
P("THE PER-TICK INCREMENT SERIES (never-crossed eras; mm/tick):")
for r in never:
    ser_s = " ".join("%d:%+.4f" % (t, v * 1e3) for (t, v) in r["incs"])
    P("  fire %d %s: %s" % (r["ft"], r["era_class"], ser_s))
P("-" * 150)

# ---- the cross-check vs the wave-45 printed maxima ----
P("THE CALIBRATION CROSS-CHECK (the era-total levers vs mine_wave45_out.txt's printed maxima):")
w45 = {161: -3.142, 175: -0.003, 184: 0.151, 193: -0.497, 220: 6.902, 229: 9.125,
       238: 7.476, 247: 11.577, 256: 0.468, 265: 16.426, 291: -6.416, 300: 0.551}
ok = True
for r in rows:
    if r["ft"] in w45:
        got = r["maxlev"] * 1e3
        match = abs(got - w45[r["ft"]]) <= 0.001 + 1e-9
        ok = ok and match
        P("  fire %d %s: mine=%+.3f mm  wave45=%+.3f mm  %s"
          % (r["ft"], r["era_class"], got, w45[r["ft"]], "MATCH" if match else "MISMATCH"))
P("  CROSS-CHECK: %s" % ("GREEN (all 12 never-crossed eras match to the printed precision)" if ok else "FIRED"))
P("-" * 150)

# ---- the class envelopes ----
lift = [r for r in never if r["era_class"] == "LIFT"]
stall = [r for r in never if r["era_class"] == "STALL"]
P("THE CLASS ENVELOPES (never-crossed eras, the wave-45/46 labels):")
P("  LIFT  n=%d  leverMax mm: %s  -> %.3f .. %.3f" % (len(lift),
  [round(r["maxlev"] * 1e3, 3) for r in lift],
  min(r["maxlev"] for r in lift) * 1e3, max(r["maxlev"] for r in lift) * 1e3))
P("  LIFT  era-rate mm/tick: %.3f .. %.3f   per-tick maxInc mm/tick: %.3f .. %.3f"
  % (min(r["rate_span"] for r in lift) * 1e3, max(r["rate_span"] for r in lift) * 1e3,
     min(r["maxinc"] for r in lift) * 1e3, max(r["maxinc"] for r in lift) * 1e3))
P("  STALL n=%d  leverMax mm: %s  -> %.3f .. %.3f" % (len(stall),
  [round(r["maxlev"] * 1e3, 3) for r in stall],
  min(r["maxlev"] for r in stall) * 1e3, max(r["maxlev"] for r in stall) * 1e3))
P("  STALL era-rate mm/tick: %.3f .. %.3f   per-tick maxInc mm/tick: %.3f .. %.3f"
  % (min(r["rate_span"] for r in stall) * 1e3, max(r["rate_span"] for r in stall) * 1e3,
     min(r["maxinc"] for r in stall) * 1e3, max(r["maxinc"] for r in stall) * 1e3))
P("  THE SEPARATING WINDOWS: LEVEL form (%.3f, %.3f) mm; era-RATE form (%.3f, %.3f) mm/tick; per-tick INC form (%.3f, %.3f) mm/tick"
  % (max(r["maxlev"] for r in stall) * 1e3, min(r["maxlev"] for r in lift) * 1e3,
     max(r["rate_span"] for r in stall) * 1e3, min(r["rate_span"] for r in lift) * 1e3,
     max(r["maxinc"] for r in stall) * 1e3, min(r["maxinc"] for r in lift) * 1e3))
P("-" * 150)

# ---- the candidate application table (R1 frozen; R2/R3 measured HERE) ----
P("THE CANDIDATE APPLICATION TABLE (F-G47b): rate mm/tick, level mm (=rate*tair=%d), R1 frozen, R2 LEVEL, R2 RATE, R3" % TAIR)
P("  R2 LEVEL  = every never-crossed LIFT era has a tick with lever > D_level AND no STALL era does")
P("  R2 RATE   = every never-crossed LIFT era has a tick with inc  > D_rate  AND no STALL era does")
P("  R3        = the clause engages inside the ship walk (any era, either form)")
verdict_exists = False
for (name, rate, r1, chain) in CANDIDATES:
    dl = rate * TAIR * 1e3          # level mm
    dr = rate * 1e3                 # mm/tick
    lvl_lift = all(any(s[4] * 1e3 > dl for s in r["ser"]) for r in lift)
    lvl_stall = not any(any(s[4] * 1e3 > dl for s in r["ser"]) for r in stall)
    rat_lift = all(any(v * 1e3 > dr for (_, v) in r["incs"]) for r in lift)
    rat_stall = not any(any(v * 1e3 > dr for (_, v) in r["incs"]) for r in stall)
    engage = any(any(s[4] * 1e3 > dl for s in r["ser"]) or any(v * 1e3 > dr for (_, v) in r["incs"])
                 for r in rows)
    r2l = lvl_lift and lvl_stall
    r2r = rat_lift and rat_stall
    r3 = engage
    passed = (r1 == "PASS") and (r2l or r2r) and r3
    if passed: verdict_exists = True
    # the measured engagement details
    if lvl_lift:
        firsts = []
        for r in lift:
            t = next((s[0] for s in r["ser"] if s[4] * 1e3 > dl), None)
            firsts.append((r["ft"], t))
    else:
        firsts = []
    stall_fires = [(r["ft"], "L") if any(s[4] * 1e3 > dl for s in r["ser"]) else (r["ft"], "R")
                   for r in stall if (any(s[4] * 1e3 > dl for s in r["ser"]) or any(v * 1e3 > dr for (_, v) in r["incs"]))]
    P("  %-42s rate=%9.4f level=%9.4f | R1=%s | R2L=%s R2R=%s | R3=%s | %s"
      % (name, dr, dl, r1, "PASS" if r2l else "fail", "PASS" if r2r else "fail",
         "yes" if r3 else "NO(vacuous)",
         "CANDIDATE PASSES ALL THREE" if passed else "fails"))
    if r1 == "PASS" and not (r2l or r2r):
        detail = []
        for r in stall:
            lv = any(s[4] * 1e3 > dl for s in r["ser"])
            rt = any(v * 1e3 > dr for (_, v) in r["incs"])
            if lv or rt: detail.append("%d:%s%s" % (r["ft"], "L" if lv else "", "R" if rt else ""))
        P("      R2 fail detail: fires in STALL eras %s (the band-scale degeneracy)" % ",".join(detail))
    if r1 == "FAIL" and (r2l or r2r):
        P("      the numerology trap: separates measurably, DEAD AT R1 (%s)" % chain[:110])
P("-" * 150)
P("THE VERDICT (frozen rule receipt_wave47.json): DERIVATION EXISTS iff some candidate passes R1 AND (R2L or R2R) AND R3")
P("  VERDICT: %s" % ("DERIVATION EXISTS -- the amendment freezes clause+D+census; the law builds dual-gated"
                     if verdict_exists else
                     "NO DERIVATION EXISTS -- R1 INTERSECT R2 IS EMPTY; THE RECORD SHIPS; "
                     "the controller chapter closes formally; the wave-48 bank = the TYPE-B convergence + the PD-authority face"))
P("  the structural reading: the reflex band owns LEVELS against the solver's contact quantum; the split and")
P("  its rate are ROTATIONAL DOFs the machinery never reads; every rate-side clause needs a threshold no")
P("  derivation supplies -- the pad split and its rate are exactly the new sensing the TYPE-B policy layer owns.")
out.close()
print("written .tmp/w47_receipt/mine_wave47_out.txt")
