#!/usr/bin/env python3
"""THE WAVE-41 MINE (declared instrument .tmp/w41_receipt/mine_w41.py).
Reads THIS LANE'S INSTRUMENTED TRACE ONLY: .tmp/w41_receipt/instr_tr_stderr.txt
(the [dvfp]/[dvfs] plumbing build: stdout 8c537cdb EXACT, plain==trace byte-equal,
refusal 302, ledger 30.970714, 49/173; the trace fence GREEN -- the base trace
db275d0a... plus inserted [dvfp]/[dvfs] lines only). Parses the LAST walk run
(the wave-39/40 declared convention). [hindstep] event lines DEDUPED by full
line text (the census plumbing mirrors them byte-identically).

THE QUESTION (the wave-41 bank): WHERE DOES THE SWING'S RESIDUAL GO -- into the
carrier's hind column, into the FORE columns, or nowhere -- and is the wave-32
+1-class fire firing BEFORE the transfer finishes (the fire-tick load gate's
premise) -- with the SELECTION RULE deciding the law BEFORE any law build.

THE DECISION RULE (fixed in receipt_wave41.json BEFORE the numbers below were
read; restated verbatim):
For EVERY fire: dl off the line; TD_o = the other leg's last td at or before
the fire tick (t <= ft -- the machinery's own loop order: the completion
processing precedes the decision loop in the same tick, so a same-tick td IS
registered before the fire decision reads it); FORM = unload iff dl == TD_o
(kUnloadTicks=1: unload = TD_o + 0), fold iff dl == TD_o + kFoldBudgetTicks -
tair - 1 (= TD_o + 35; kFoldBudgetTicks=45, tair=9); rxnF = the fired leg's
[dvp] pair rxn sum at the fire's prior post-tick. Per era (fire -> completion):
  (a) THE CARRIER'S STANCE-DRAIN CURVE: the standing leg's hind pair rxn at
      the swing's fire (the f-1 post-tick), the first tick its pair sum reads
      <= kTouch (1e-5 N -- the trace's own rxn0 face), the mean drain rate
      N/tick over that span.
  (b) THE FORE-COLUMN TRAIL: the [dvfs] L/R sums at the swing's fire and at
      the era's completion, their min/max over the era, the era's fore rise
      against the era's hind decay (the swing's + the carrier's).
  (c) THE TRANSFER-COMPLETION FRACTION: L_i = rxnF / the era's carrier drain
      rate (the predicted ticks the FIRE-TICK LOAD GATE would hold that fire);
      INF iff the era's carrier never reached rxn0 within [f-1, c] OR the rate
      is zero (x/0 = INF by the formula itself); L_i = 0 when rxnF <= kTouch
      (the gate never engages -- no hold to predict).
THE SELECTION RULE (binding): the law is CANDIDATE 2 (THE FIRE-TICK LOAD GATE)
iff EVERY unload-form fire's L_i is finite AND sum(L_i) <= sum(held_i - 1) over
the unload-form eras (the held-tick saving the drained 1-tick releases buy, the
wave-33 replay convention: held at u iff pairmin(u-1) <= kTouch+kReleaseBand);
if ANY unload-form L_i is INF, candidate 2 is KILLED and the law is CANDIDATE 1
(THE CARRIER'S SHARE ACCEPTANCE), amended from the fore trail's named mechanism.
Output: mine_w41_out.txt (this run's preserved output).
"""
import re, collections

TRACE = ".tmp/w41_receipt/instr_tr_stderr.txt"
KT = 1e-5          # kTouch
KRB = 1e-6         # kReleaseBand
FOLD = 35          # kFoldBudgetTicks - tair - 1 = 45 - 9 - 1

lines = open(TRACE, encoding="utf-8", errors="replace").read().splitlines()
idx = [i for i, l in enumerate(lines) if l.startswith("WALK REFUSED")]
run = lines[idx[-2] + 1:idx[-1]]
mref = re.match(r"WALK REFUSED tick (\d+): (\S+)", lines[idx[-1]])
refus = (int(mref.group(1)), mref.group(2))

dvp = collections.defaultdict(dict)   # t -> k(0..3 hind) -> (gap,rxn,frc,slip,px,py)
dvfs = {}                             # t -> (sumL, sumR)
bx = {}
fires = []                            # (t, leg, cls, fx, fy, tx, ty, xoff, v, dl)
tds = []                              # (t, leg)
seen_ev = set()
for l in run:
    m = re.match(r"\[dvp\] t=(\d+) k=(\d) gap=(\S+) rxn=(\S+) frc=(\S+) slip=(\S+) pos=(\S+),(\S+)", l)
    if m:
        dvp[int(m.group(1))][int(m.group(2))] = tuple(float(m.group(x)) for x in (3, 4, 5, 6, 7, 8)); continue
    m = re.match(r"\[dvfs\] t=(\d+) sumL=(\S+) sumR=(\S+) n=(\d+)", l)
    if m:
        dvfs[int(m.group(1))] = (float(m.group(2)), float(m.group(3))); continue
    m = re.match(r"\[dv\] t=(\d+) .* bx=(\S+)\s*$", l)
    if m:
        bx[int(m.group(1))] = float(m.group(2)); continue
    if l.startswith("[hindstep]"):
        if l in seen_ev: continue
        seen_ev.add(l)
        m = re.match(r"\[hindstep\] fire leg=(\d) tick=(\d+) phi=\S+ class=(\S+) from=\((\S+),(\S+)\) to=\((\S+),(\S+)\) xoff=(\S+) v=(\S+) qerr=\S+ ap=\S+ br=\S+ dl=(\d+)", l)
        if m:
            fires.append((int(m.group(2)), int(m.group(1)), m.group(3),
                          float(m.group(4)), float(m.group(5)),
                          float(m.group(6)), float(m.group(7)),
                          float(m.group(8)), float(m.group(9)),
                          int(m.group(10)))); continue
        m = re.match(r"\[hindstep\] td leg=(\d) tick=(\d+)", l)
        if m: tds.append((int(m.group(2)), int(m.group(1)))); continue

def pair(t, leg):
    """(pairmin gap, rxn sum) of the leg's hind pads at post-tick t; None if absent."""
    a, b = dvp.get(t, {}).get(2*leg), dvp.get(t, {}).get(2*leg+1)
    if a is None or b is None: return None
    return (min(a[0], b[0]), a[1] + b[1])

out = open(".tmp/w41_receipt/mine_w41_out.txt", "w", encoding="utf-8")
def P(*a):
    s = " ".join(str(x) for x in a)
    out.write(s + "\n"); print(s)

P("refusal:", refus, " fires:", len(fires), " tds:", len(tds))
P("=" * 118)

rows = []
for (ft, leg, cls, fx, fy, tx, ty, xoff, v, dl) in fires:
    o = 1 - leg
    comp = next(((t, l) for (t, l) in tds if l == leg and t >= ft), None)
    ct = comp[0] if comp else max(t for t in dvp if pair(t, leg) is not None and t > ft)
    td_o = max((t for (t, l) in tds if l == o and t <= ft), default=0)
    form = "none" if dl == 0 else ("unload" if dl == td_o else ("fold" if dl == td_o + FOLD else "other(dl=%d,td_o=%d)" % (dl, td_o)))
    pf = pair(ft - 1, leg)
    rxnF = pf[1] if pf else float('nan')
    # (a) the carrier's stance-drain curve over the era [ft-1, ct]
    drain0 = pair(ft - 1, o)
    drain_tick = None
    if drain0:
        for u in range(ft - 1, ct + 1):
            pu = pair(u, o)
            if pu is None: continue
            if pu[1] <= KT: drain_tick = u; break
    if rxnF <= KT:
        rate = 0.0; L = 0.0   # the gate never engages on a drained fire
    elif drain0 and drain_tick is not None:
        span = max(1, drain_tick - (ft - 1))
        rate = drain0[1] / span
        L = rxnF / rate if rate > 1e-12 else float('inf')
    else:
        rate = 0.0; L = float('inf')
    # the held-tick replay (the wave-33 convention) over the era
    held = 0
    for u in range(ft + 1, ct + 1):
        pp = pair(u - 1, leg)
        if pp is not None and pp[0] <= KT + KRB: held += 1
    # (b) the fore-column trail over the era
    f0 = dvfs.get(ft - 1); f1 = dvfs.get(ct)
    fmin = [1e9, 1e9]; fmax = [-1e9, -1e9]
    for u in range(ft - 1, ct + 1):
        f = dvfs.get(u)
        if not f: continue
        for s_ in (0, 1):
            fmin[s_] = min(fmin[s_], f[s_]); fmax[s_] = max(fmax[s_], f[s_])
    frise = (f1[0] + f1[1] - f0[0] - f0[1]) if (f0 and f1) else float('nan')
    c0 = pair(ft - 1, leg); c1 = pair(ct, leg); co0 = pair(ft - 1, o); co1 = pair(ct, o)
    hind_decay = ((c0[1] if c0 else 0) + (co0[1] if co0 else 0) - (c1[1] if c1 else 0) - (co1[1] if co1 else 0)) if (c0 and c1 and co0 and co1) else float('nan')
    rows.append(dict(ft=ft, ct=ct, leg=leg, cls=cls, form=form, rxnF=rxnF, drain0=(drain0[1] if drain0 else float('nan')),
                     drain_tick=drain_tick, rate=rate, L=L, held=held,
                     fL0=(f0[0] if f0 else float('nan')), fR0=(f0[1] if f0 else float('nan')),
                     fL1=(f1[0] if f1 else float('nan')), fR1=(f1[1] if f1 else float('nan')),
                     fmin=fmin, fmax=fmax, frise=frise, hind_decay=hind_decay))

P("ERA TABLE: fire->compl leg class FORM rxnF drain0 drainTick drainRate L_pred held foreL(f->c) foreR(f->c) foreRise hindDecay")
for r in rows:
    P("  %4d->%4d leg=%d %-4s %-6s rxnF=%7.3f dr0=%6.3f drT=%4s rate=%6.3f L=%5s held=%d fL=%6.3f->%6.3f fR=%6.3f->%6.3f rise=%+7.3f decay=%+7.3f"
      % (r["ft"], r["ct"], r["leg"], r["cls"], r["form"], r["rxnF"], r["drain0"],
         str(r["drain_tick"]) if r["drain_tick"] is not None else "never",
         r["rate"], ("INF" if r["L"] == float('inf') else "%.1f" % r["L"]), r["held"],
         r["fL0"], r["fL1"], r["fR0"], r["fR1"], r["frise"], r["hind_decay"]))
P("-" * 118)

uf = [r for r in rows if r["form"] == "unload" and r["cls"] == "alt"]
inf = [r for r in uf if r["L"] == float('inf')]
sumL = sum(r["L"] for r in uf if r["L"] != float('inf'))
sumS = sum(max(0, r["held"] - 1) for r in uf)
P("UNLOAD-FORM ALT FIRES:", len(uf), " with INF latency:", len(inf),
  " [ticks:", ",".join(str(r["ft"]) for r in inf) or "none", "]")
P("SUM LATENCY (ticks): %.1f   SUM HELD-TICK SAVING (ticks): %d" % (sumL, sumS))
P("THE SELECTION RULE (fixed in receipt_wave41.json):",
  "CANDIDATE 2 THE FIRE-TICK LOAD GATE" if (not inf and sumL <= sumS) else "CANDIDATE 1 THE CARRIER'S SHARE ACCEPTANCE")
P("-" * 118)
tot_rise = sum(r["frise"] for r in rows if r["frise"] == r["frise"])
tot_dec = sum(r["hind_decay"] for r in rows if r["hind_decay"] == r["hind_decay"])
P("THE RESIDUAL TRAIL over all eras: total fore rise %+.3f N vs total hind decay %+.3f N (the fore absorbed %.1f%% of the decay)"
  % (tot_rise, tot_dec, 100.0 * tot_rise / tot_dec if abs(tot_dec) > 1e-9 else float('nan')))
out.close()
print("written .tmp/w41_receipt/mine_w41_out.txt")
