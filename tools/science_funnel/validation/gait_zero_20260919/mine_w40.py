#!/usr/bin/env python3
"""THE WAVE-40 MINE (declared instrument .tmp/w40_receipt/mine_w40.py).
Reads THIS LANE'S REPRODUCTION TRACE ONLY: .tmp/w40_receipt/base_tr_stderr.txt
(the byte-exact 8b2177c9 ship state: stdout c8cd35bc..., refusal 302, ledger
30.970714, 49/173; trace stderr byte-identical to the parent lane's preserved
ship trace db275d0a...). Parses the LAST walk run (the wave-39 declared
convention: the run the stdout corresponds to). NOTE: in the ship trace the
[hindstep] event lines print TWICE per event in the last run (the read-only
F-G39 census plumbing mirrors the controller's GAIT_EVENT_TRACE lines
byte-identically) -- events are DEDUPED by their full line text.

THE QUESTION (the wave-40 bank): WHERE DOES THE HAUL DIE -- the mined
under-delivery's owner among the declared candidates -- and what does the
LOAD BOOK (the share at the pin eras) say owns the stay class.

THE DECISION RULE (fixed BEFORE the numbers below were read):
For EVERY hind era (fire tick f -> completion tick c) take
  C  = to_x - from_x                      (the commanded haul, the fire line)
  D  = pad_x(c) - from_x                  (the delivered advance, [dvp] pos)
and decompose the deficit (C - D) over the era's ticks into exactly the
declared candidates:
  (A) THE UNLOAD-HELD SPAN (the load book): the replayed held ticks -- the
      hold release is REPLAYED with the wave-33 convention (the trace series
      is the post-tick state; the decision at t reads t-1): held stays true
      while pairmin_post(t-1) <= kTouch+kReleaseBand. The haul never
      commands on a held tick; its share of the deficit is charged to
      THE UNLOAD (the load book: the fired pads never unloaded).
  (B) THE COMMANDED SPAN: the released ticks. The commanded line rate is
      C/(tair - held_ticks); the realized rate is D over the released span.
      If the realized rate < 50% of commanded, the span's deficit is split:
      (B1) THE TORQUE ALLOCATION: the swing hip or knee drive at >= 0.9*cap
           on >= 2/3 of the span's decision ticks (the [dvq] read at the
           prior post-tick) -- the cap eats the haul;
      (B2) THE SERVO TRACK: otherwise -- headroom existed and the servo
           under-tracked the commanded advance.
  (C) THE PLANT-AIM: at the completion, the aim error |to_x - (bx(c)+xoff)|.
      If the aim error >= 20% of C, its share (C-D) is charged to
      THE PLANT-AIM instead of (A)/(B).
THE OWNER = the candidate with the LARGEST TOTAL charged deficit summed over
the eras (ties: the earlier first-engagement era wins). The per-era
decomposition is recorded verbatim whatever the verdict.

THE LOAD-BOOK CENSUS (independent of the owner rule; the F-G40 basis):
per era -- the fired leg's rxn at its own fire (the heel+mp sum at the fire's
prior post-tick), the arch peak (the max pad rise above the fire-tick pad
height, the [dvp] pos frame), the HELD-SPAN SATURATION (the fraction of held
ticks with the swing hip or knee at >= 0.9*cap -- the lift's own torque
face), and the standhold spans' carrier/swing hind-rxn series. THE STANCE
CREEP-X CENSUS: per stance span (the leg's span between its completion and
its next fire) the pad-x world drift vs the bx advance -- the designed
columns' advance term vs the body's actual speed.
Output: mine_w40_out.txt (this run's preserved output).
"""
import re, collections

TRACE = ".tmp/w40_receipt/base_tr_stderr.txt"
KT = 1e-5          # kTouch
KRB = 1e-6         # kReleaseBand (release quantum kTouch+kReleaseBand)
TAIR = 9           # the machinery's own air time (ticks)

lines = open(TRACE, encoding="utf-8", errors="replace").read().splitlines()
idx = [i for i, l in enumerate(lines) if l.startswith("WALK REFUSED")]
run = lines[idx[-2] + 1:idx[-1]]
mref = re.match(r"WALK REFUSED tick (\d+): (\S+)", lines[idx[-1]])
refus = (int(mref.group(1)), mref.group(2))

dvp = collections.defaultdict(dict)   # t -> k -> (gap,rxn,frc,slip,px,py)
dvq = collections.defaultdict(dict)   # t -> k -> (tau,cap)
bx = {}                               # t -> base x
fires = []                            # (t, leg, cls, fx, fy, tx, ty, xoff, v)
tds = []                              # (t, leg)
holdret = []                          # (t, leg, pairmin)
stand = []                            # (t, leg)
seen_ev = set()
for l in run:
    m = re.match(r"\[dvp\] t=(\d+) k=(\d) gap=(\S+) rxn=(\S+) frc=(\S+) slip=(\S+) pos=(\S+),(\S+)", l)
    if m:
        dvp[int(m.group(1))][int(m.group(2))] = tuple(float(m.group(x)) for x in (3,4,5,6,7,8)); continue
    m = re.match(r"\[dvq\] t=(\d+) k=(\d) tau=(\S+) cap=(\S+)", l)
    if m:
        dvq[int(m.group(1))][int(m.group(2))] = (float(m.group(3)), float(m.group(4))); continue
    m = re.match(r"\[dv\] t=(\d+) .* bx=(\S+)\s*$", l)
    if m:
        bx[int(m.group(1))] = float(m.group(2)); continue
    if l.startswith("[hindstep]"):
        if l in seen_ev: continue          # the census plumbing's byte-identical mirror
        seen_ev.add(l)
        m = re.match(r"\[hindstep\] fire leg=(\d) tick=(\d+) phi=\S+ class=(\S+) from=\((\S+),(\S+)\) to=\((\S+),(\S+)\) xoff=(\S+) v=(\S+)", l)
        if m:
            fires.append((int(m.group(2)), int(m.group(1)), m.group(3),
                          float(m.group(4)), float(m.group(5)),
                          float(m.group(6)), float(m.group(7)),
                          float(m.group(8)), float(m.group(9)))); continue
        m = re.match(r"\[hindstep\] td leg=(\d) tick=(\d+)", l)
        if m: tds.append((int(m.group(2)), int(m.group(1)))); continue
        m = re.match(r"\[hindstep\] holdreturn leg=(\d) tick=(\d+) t=(-?\d+) pairmin=(\S+)", l)
        if m: holdret.append((int(m.group(2)), int(m.group(1)), float(m.group(4)))); continue
        m = re.match(r"\[hindstep\] standhold leg=(\d) tick=(\d+) swing_stall=(\d+)", l)
        if m: stand.append((int(m.group(2)), int(m.group(1)))); continue

def pad(t, leg):
    """(pairmin, rxn_sum, px_mean, py_mean) at post-tick t; None if absent."""
    a, b = dvp.get(t, {}).get(2*leg), dvp.get(t, {}).get(2*leg+1)
    if a is None or b is None: return None
    return (min(a[0], b[0]), a[1]+b[1], (a[4]+b[4])/2., (a[5]+b[5])/2.)

def sat_at(t, leg):
    """1 if the swing hip or knee drive read >= 0.9*cap at the prior post-tick."""
    q = dvq.get(t - 1, {})
    for k in (4*leg, 4*leg + 1):
        tau, cap = q.get(k, (0., 1.))
        if cap > 0 and abs(tau) >= 0.9 * cap: return 1
    return 0

out = open(".tmp/w40_receipt/mine_w40_out.txt", "w", encoding="utf-8")
def P(*a):
    s = " ".join(str(x) for x in a)
    out.write(s + "\n"); print(s)

P("refusal:", refus, " fires:", len(fires), " tds:", len(tds))
P("=" * 112)

charge = collections.defaultdict(float)
rows = []
for (ft, leg, cls, fx, fy, tx, ty, xoff, v) in fires:
    comp = next(((t, l) for (t, l) in tds if l == leg and t > ft), None)
    if comp is None:
        ct = max(t for t in dvp if pad(t, leg) is not None and t > ft)
    else:
        ct = comp[0]
    C = tx - fx
    pc = pad(ct, leg)
    D = pc[2] - fx
    # ── the replayed hold state per decision tick u in (ft, ct] ──
    held = {}
    for u in range(ft + 1, ct + 1):
        p_prev = pad(u - 1, leg)
        held[u] = (p_prev is not None) and (p_prev[0] <= KT + KRB)
    hticks = sum(1 for u in held if held[u])
    # ── the commanded-span under-track ──
    released = [u for u in sorted(held) if not held[u]]
    und_track = 0.0; alloc = 0.0
    if released:
        span = len(released)
        cmd_rate = C / max(1, (TAIR - hticks))
        realized = (pad(released[-1], leg)[2] - pad(released[0] - 1, leg)[2]) / max(1, span)
        sat_ticks = sum(sat_at(u, leg) for u in released)
        if realized < 0.5 * cmd_rate and span > 0:
            und_track = C - D
            if sat_ticks >= (2 * span) // 3: alloc = und_track; und_track = 0.0
    # ── the plant-aim error at the completion ──
    aim = abs(tx - (bx.get(ct, float('nan')) + xoff)) if ct in bx else 0.0
    aim_chg = (C - D) if (abs(C) > 1e-12 and aim >= 0.2 * abs(C)) else 0.0
    if aim_chg > 0: und_track = alloc = 0.0
    # ── the load book at the fire + the held-span saturation ──
    pf = pad(ft - 1, leg)
    rxn_at_fire = pf[1] if pf else float('nan')
    py0 = pad(ft, leg)
    arch = max((pad(u, leg)[3] - py0[3] for u in range(ft, ct + 1)
                if pad(u, leg) is not None), default=0.0)
    sat_held = (sum(sat_at(u, leg) for u in held if held[u]) / hticks) if hticks else 0.0
    chg_unload = 0.0 if aim_chg > 0 else (C - D) * (hticks / max(1, ct - ft))
    charge["unload"] += chg_unload
    charge["track"] += und_track
    charge["alloc"] += alloc
    charge["aim"] += aim_chg
    rows.append((ft, ct, leg, cls, C, D, D / C if abs(C) > 1e-12 else 0., hticks,
                 rxn_at_fire, arch * 1e3, sat_held, chg_unload, und_track, alloc, aim, aim_chg))
P("ERA TABLE: fire->complete leg class C_del_frac heldTicks rxnAtFire_N archPeak_mm heldSat heldCharge trackCharge allocCharge aimErr aimCharge")
for r in rows:
    P("  %4d->%3d leg=%d %-4s f=%.3f ht=%d rxnF=%7.3f arch=%+8.3f sat=%.2f u=%+.3f trk=%+.3f alc=%+.3f aim=%.4f ac=%+.2f"
      % (r[0], r[1], r[2], r[3], r[5], r[7], r[8], r[9], r[10], r[11], r[12], r[13], r[14], r[15]))
P("-" * 112)
P("TOTAL CHARGED DEFICIT BY CANDIDATE (m):",
  {k: round(v, 4) for k, v in sorted(charge.items())})
order = ["unload", "alloc", "track", "aim"]
owner = max(order, key=lambda k: charge[k])
P("THE OWNER (largest total charged deficit):", owner.upper())
P("-" * 112)

P("THE PIN ERAS (the standhold spans): span, leg, carrier hind-rxn, swing hind-rxn")
std = sorted(stand)
if std:
    spans = []
    s0 = std[0]; prev = std[0]
    for x in std[1:]:
        if x[1] != s0[1] or x[0] != prev[0] + 1:
            spans.append((s0, prev)); s0 = x
        prev = x
    spans.append((s0, prev))
    for (a, b) in spans:
        leg = a[1]
        cr = [pad(t, leg)[1] for t in range(a[0], b[0] + 1) if pad(t, leg)]
        orr = [pad(t, 1 - leg)[1] for t in range(a[0], b[0] + 1) if pad(t, 1 - leg)]
        P("  [%d,%d] leg=%d carrier mean=%.3f min=%.3f max=%.3f | swing mean=%.3f min=%.3f max=%.3f"
          % (a[0], b[0], leg, sum(cr)/len(cr), min(cr), max(cr),
             sum(orr)/len(orr), min(orr), max(orr)))
P("-" * 112)
P("THE STANCE CREEP-X CENSUS: leg [t0,t1) pad_drift_m bx_adv_m relative_m (mm/tick pad vs body)")
for leg in (0, 1):
    my_tds = [t for (t, l) in tds if l == leg]
    my_fires = [ft for (ft, l, *_ ) in fires if l == leg]
    for td in my_tds:
        nf = next((ft for ft in my_fires if ft > td), refus[0])
        if nf <= td: continue
        p0 = pad(td, leg); p1 = pad(nf - 1, leg)
        b0 = bx.get(td); b1 = bx.get(nf - 1)
        if p0 is None or p1 is None or b0 is None or b1 is None: continue
        P("  leg=%d [%4d,%4d) pad=%+.4f body=%+.4f rel=%+.4f (%+.1f vs %+.1f mm/tick)"
          % (leg, td, nf, p1[2]-p0[2], b1-b0, (p1[2]-p0[2])-(b1-b0),
             (p1[2]-p0[2])*1000./(nf-td), (b1-b0)*1000./(nf-td)))
out.close()
print("written .tmp/w40_receipt/mine_w40_out.txt")
