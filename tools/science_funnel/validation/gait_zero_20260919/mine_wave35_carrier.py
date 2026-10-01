"""WAVE-35 MINING SCRIPT (declared instrument, Rule-0).
Parses THIS lane's byte-exact reproduction trace (.tmp/w35_receipt/base_tr_stderr.txt,
the FIRST walk run only) and decides the wave-35 front by the rule below.
The rule was fixed BEFORE any number below was read (this file committed before the run).

THE DECISION RULE (fixed a priori):
  FRONT 2 (the step-length disease) owns the 250-262 death iff BOTH:
    (R1) the era length (fire->TD ticks) scales with the plant lead xoff across the
         exchange eras: Pearson r >= 0.70 over all eras;
    (R2) the carrier-drain onset inside the two REAL eras aligns GEOMETRICALLY:
         the com_x - carrier_pad_x offset at the onset tick (the first tick the
         carrier's total pad rxn drops below 50% of its value at the era's first
         tick) agrees between the two real eras within 15% (of the larger), while
         the era-relative onset ticks differ by more than 2 ticks.
  Otherwise FRONT 1 (the carrier self-unload fire deadline) owns the death.

Supporting measurements (all reported verbatim):
  A the exchange calendar (fires, TDs, classes, from/to/xoff, v, era lengths)
  B per-era carrier rxn summary (era-start, peak, the <0.5 N tick, the rxn0 tick)
  C the haul delivery: the pad x at the TD vs the to_x target (the under-delivery)
  D the twelfth-era deep dive [247,295): the R rxn/gap/x series, com_x, the gates
  E the FRONT-1 feasibility: the candidate carrier-fire ticks, their pad state
"""
import re, math

TRACE = ".tmp/w35_receipt/base_tr_stderr.txt"

dv = {}      # tick -> (comx, comz, bx)
dvp = {}     # tick -> [4x (gap, rxn, frc, slip, x, y)]
fires, tds, holdret, gates, refusal_lines = [], [], [], [], []
run = 0      # the first walk run is run 1

for line in open(TRACE, encoding="utf-8", errors="replace"):
    m = re.match(r"\[dv\] t=(\d+) ", line)
    if m:
        t = int(m.group(1))
        if t == 0:
            run += 1
        if run == 1:
            mm = re.search(r"com=\((-?[\d.e+]+),(-?[\d.e+]+)\) hull=(\d+) in=(\d+) bx=(-?[\d.e+]+)", line)
            if mm:
                dv[t] = (float(mm.group(1)), float(mm.group(2)), float(mm.group(5)))
        continue
    if run != 1:
        continue
    m = re.match(r"\[dvp\] t=(\d+) k=(\d) gap=([\d.e+-]+) rxn=([\d.e+-]+) frc=([\d.e+-]+) slip=([\d.e+-]+) pos=(-?[\d.e+]+),(-?[\d.e+]+)", line)
    if m:
        t, k = int(m.group(1)), int(m.group(2))
        if t <= 300:
            dvp.setdefault(t, [None]*4)[k] = tuple(float(m.group(i)) for i in range(3, 9))
        continue
    m = re.match(r"\[hindstep\] fire leg=(\d) tick=(\d+) phi=([\d.e+-]+) class=(\w+) from=\((-?[\d.e+]+),(-?[\d.e+]+)\) to=\((-?[\d.e+]+),(-?[\d.e+]+)\) xoff=([\d.e+-]+) v=([\d.e+-]+)", line)
    if m:
        if int(m.group(2)) <= 300:
            fires.append(dict(leg=int(m.group(1)), tick=int(m.group(2)), phi=float(m.group(3)),
                              cls=m.group(4), fx=float(m.group(5)), fy=float(m.group(6)),
                              tx=float(m.group(7)), ty=float(m.group(8)),
                              xoff=float(m.group(9)), v=float(m.group(10))))
        continue
    m = re.match(r"\[hindstep\] td leg=(\d) tick=(\d+) tds=(\d+)", line)
    if m:
        if int(m.group(2)) <= 300:
            tds.append(dict(leg=int(m.group(1)), tick=int(m.group(2)), tds=int(m.group(3))))
        continue
    m = re.match(r"\[hindstep\] holdreturn leg=(\d) tick=(\d+) t=(\d+) pairmin=([\d.e+-]+)", line)
    if m:
        if int(m.group(2)) <= 300:
            holdret.append(dict(leg=int(m.group(1)), tick=int(m.group(2)), t=int(m.group(3)), pm=float(m.group(4))))
        continue
    m = re.match(r"\[hindgate\] tick=(\d+) leg=(\d) live=(\d+) .*?gated=(\d) floor=(\d) dl=(\d+) v=([\d.e+-]+)", line)
    if m:
        if int(m.group(1)) <= 300:
            gates.append(dict(tick=int(m.group(1)), leg=int(m.group(2)), live=int(m.group(3)),
                              gated=int(m.group(4)), floor=int(m.group(5)), dl=int(m.group(6)),
                              v=float(m.group(7))))
        continue
    if line.startswith("[refusal]") or line.startswith("WALK REFUSED"):
        refusal_lines.append(line.strip())

# hind point order: 0=left heel 1=left mp 2=right heel 3=right mp; leg0=L, leg1=R
def leg_rxn(t, leg):
    r = dvp.get(t)
    if not r or r[2*leg] is None or r[2*leg+1] is None:
        return None
    return r[2*leg][1] + r[2*leg+1][1]

def leg_gapmin(t, leg):
    r = dvp.get(t)
    if not r or r[2*leg] is None or r[2*leg+1] is None:
        return None
    return min(r[2*leg][0], r[2*leg+1][0])

def leg_padx(t, leg):
    r = dvp.get(t)
    if not r or r[2*leg] is None or r[2*leg+1] is None:
        return None
    return (r[2*leg][4] + r[2*leg+1][4]) / 2.0

print("=== A. THE EXCHANGE CALENDAR (first walk run) ===")
td_by_leg = {}
for td in tds:
    td_by_leg.setdefault(td["leg"], []).append(td["tick"])
eras = []
for f in fires:
    nxt = [x for x in td_by_leg.get(f["leg"], []) if x > f["tick"]]
    era = (nxt[0] - f["tick"]) if nxt else None
    eras.append((f, era))
    print("fire %s@%d %s phi=%.3f from_x=%.3f to_x=%.3f xoff=%.4f v=%.3f -> td %s era=%s" % (
        "LR"[f["leg"]], f["tick"], f["cls"], f["phi"], f["fx"], f["tx"], f["xoff"], f["v"],
        nxt[0] if nxt else "?", era))

print()
print("=== R1. era length vs xoff (Pearson) ===")
pts = [(f["xoff"], e) for f, e in eras if e]
n = len(pts)
if n >= 3:
    mx = sum(p[0] for p in pts)/n; my = sum(p[1] for p in pts)/n
    sxy = sum((p[0]-mx)*(p[1]-my) for p in pts)
    sxx = math.sqrt(sum((p[0]-mx)**2 for p in pts)); syy = math.sqrt(sum((p[1]-my)**2 for p in pts))
    r = sxy/(sxx*syy) if sxx > 0 and syy > 0 else float("nan")
    print("n=%d Pearson r(era,xoff)=%.4f   (FRONT-2 R1 threshold >= 0.70)" % (n, r))
    for xoff, e in pts:
        print("   xoff=%.4f era=%d" % (xoff, e))
else:
    r = float("nan")
    print("n=%d too few eras" % n)

print()
print("=== B. per-era CARRIER share (the other leg) ===")
carrier_rows = []
for f, era in eras:
    if not era:
        continue
    o = 1 - f["leg"]
    r0 = leg_rxn(f["tick"], o)
    peak, r05, r00 = None, None, None
    for t in range(f["tick"], min(f["tick"]+era+6, 295)):
        rr = leg_rxn(t, o)
        if rr is None:
            continue
        if peak is None or rr > peak:
            peak = rr
        if r05 is None and rr < 0.5:
            r05 = t
        if r00 is None and rr <= 0.0:
            r00 = t
    carrier_rows.append(dict(f=f, era=era, o=o, r0=r0, peak=peak, r05=r05, r00=r00))
    print("era %s@%d [%d,%d) carrier=%s rxn0=%.3f peak=%.3f rxn<0.5@%s rxn0@%s" % (
        "LR"[f["leg"]], f["tick"], f["tick"], f["tick"]+era, "LR"[o],
        r0 if r0 is not None else float("nan"), peak if peak is not None else float("nan"),
        r05, r00))

print()
print("=== R2. the REAL eras: the drain onset, geometric vs era-relative ===")
real = [cr for cr in carrier_rows if cr["era"] > 9]
geom, rel = [], []
for cr in real:
    f, era, o = cr["f"], cr["era"], cr["o"]
    r0 = cr["r0"]
    onset = None
    for t in range(f["tick"], f["tick"]+era):
        rr = leg_rxn(t, o)
        if rr is not None and r0 and rr < 0.5*r0:
            onset = t
            break
    if onset is None:
        print("era %s@%d: no onset (carrier held)" % ("LR"[f["leg"]], f["tick"]))
        continue
    cx = dv.get(onset, (None,))[0]
    px = leg_padx(onset, o)
    off = (cx - px) if (cx is not None and px is not None) else None
    geom.append(off)
    rel.append(onset - f["tick"])
    print("era %s@%d [%d,%d): onset t=%d (era-rel %d) com_x=%.4f carrier_pad_x=%.4f com-pad=%.4f" % (
        "LR"[f["leg"]], f["tick"], f["tick"], f["tick"]+era, onset, onset-f["tick"],
        cx if cx is not None else float("nan"), px if px is not None else float("nan"),
        off if off is not None else float("nan")))
r2 = False
if len(geom) == 2 and all(g is not None for g in geom):
    big = max(abs(geom[0]), abs(geom[1]))
    geom_ok = big > 0 and abs(geom[0]-geom[1])/big <= 0.15
    rel_ok = abs(rel[0]-rel[1]) > 2
    r2 = geom_ok and rel_ok
    print("geometric agreement |%.4f vs %.4f| within 15%%: %s; era-rel %d vs %d differ>2: %s => R2=%s" % (
        geom[0], geom[1], geom_ok, rel[0], rel[1], rel_ok, r2))

print()
print("=== C. haul delivery: pad x at TD vs to_x (the under-delivery) ===")
for f, era in eras:
    if not era:
        continue
    td = f["tick"] + era
    px = leg_padx(td, f["leg"])
    print("era %s@%d to_x=%.3f pad_x@td=%.3f under=%.4f m" % (
        "LR"[f["leg"]], f["tick"], f["tx"], px if px is not None else float("nan"),
        (f["tx"]-px) if px is not None else float("nan")))

print()
print("=== D. the twelfth era deep dive [247,295) ===")
print("t com_x bx Rpad_x Rrxn Rgapmin Lrxn Rtouching")
for t in range(247, 295):
    if t not in dvp:
        continue
    cx, cz, bx = dv.get(t, (float("nan"),)*3)
    print("%d %.4f %.4f %.4f %.3f %.3e %.3f %d" % (
        t, cx, bx, leg_padx(t, 1), leg_rxn(t, 1), leg_gapmin(t, 1), leg_rxn(t, 0),
        1 if (leg_gapmin(t, 1) or 1) <= 1e-5 else 0))
print()
print("=== D2. the R candidate-fire ticks [248,262): the gates ===")
for g in gates:
    if g["leg"] == 1 and 247 <= g["tick"] <= 262:
        print("hindgate t=%d leg=1 live=%d gated=%d floor=%d dl=%d v=%.3f rxnR=%.3f gapR=%.3e" % (
            g["tick"], g["live"], g["gated"], g["floor"], g["dl"], g["v"],
            leg_rxn(g["tick"], 1) if leg_rxn(g["tick"], 1) is not None else float("nan"),
            leg_gapmin(g["tick"], 1) if leg_gapmin(g["tick"], 1) is not None else float("nan")))

print()
print("=== E. refusals seen ===")
for rl in refusal_lines:
    print(rl)

print()
print("=== THE DECISION (rule fixed a priori in the header) ===")
r1 = (r == r) and (r >= 0.70)
print("R1 haul~lead r=%.4f -> %s" % (r, "FRONT-2" if r1 else "FRONT-1"))
print("R2 geometric-onset -> %s" % ("FRONT-2" if r2 else "FRONT-1"))
print("THE WAVE-35 FRONT IS: %s" % ("FRONT 2 (the step-length law)" if (r1 and r2) else "FRONT 1 (the carrier self-unload fire deadline)"))
