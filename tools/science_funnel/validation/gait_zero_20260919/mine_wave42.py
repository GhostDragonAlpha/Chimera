#!/usr/bin/env python3
"""THE WAVE-42 MINE (declared instrument .tmp/w42_receipt/mine_w42.py).
Reads THIS LANE'S INSTRUMENTED TRACE ONLY: .tmp/w42_receipt/instr_tr_stderr.txt
(the [dvfa] plumbing build: stdout 8c537cdb EXACT, plain==trace byte-equal,
refusal 302, ledger 30.970714, 49/173; the trace fence GREEN -- the base trace
322855ec... plus inserted [dvfa] lines only). Parses the LAST walk run (the
wave-39/40/41 declared convention). [hindstep] event lines DEDUPED by full
line text (the census plumbing mirrors them byte-identically).

THE QUESTION (the wave-42 bank): WHERE DOES THE ARCH DIE -- is the commanded
hold height itself stall-class in the stall eras (VERDICT A COMMAND-STALL) or
does the command rise to the full-arch class while the pads fail to follow
(VERDICT B SERVO-UNDERDELIVERY)?

THE DECISION RULE (fixed in receipt_wave42.json BEFORE the numbers below were
read; restated verbatim): the era convention is receipt_wave41.json's verbatim
(the [hindstep] fire/td lines deduped by full line text; the fire's from=(fx,fy)
the era's plant anchor; the era span [f, ct], ct the fired leg's first td at
t >= f or the trace's end). Per swing era:
  CMD_peak = max over t in [f,ct] of (cmd_y(t) - fy), EVERY [dvfa] line of the
             era's leg counted (a br=t/br=d line mid-era IS a command death);
  DEL_peak = max over t in [f,ct] of (pad_y(t) - fy)  (the [dvfa] pad_y series,
             the servo's own tick-start evaluation -- the same two pads the
             fire's from averaged);
  the branch census over the era; the death tick = the first t in [f,ct] with
  cmd_y - fy < 1 mm after a tick with cmd_y - fy >= 4 mm;
  the body advance = the [dv] bx delta over the span;
  the demand face = the live [dvq] tau/cap reads of the ERA LEG's own four
  hind drives over the era (READ CORRECTION documented at append: the declared
  "k=4..7 = the LEFT hind drives" mapping was wrong -- the recipe's own drive
  order is k=0..3 LEFT hind hip/knee/ankle/MP, k=4..7 RIGHT hind; the mine
  reads the era leg's own four drives, MORE coverage than declared, zero
  plumbing; demand-pinned iff some drive reads tau >= 0.999*cap at some era
  tick, else demand-flows).
THE ERA CLASS faces (receipt_wave41.json verbatim): STALL-CLASS DEL_peak < 1 mm
(the measured stall band 0.000-0.087 mm), LIFT-CLASS DEL_peak >= 1 mm (the
measured lift band 1.280-12.127 mm); ARCH-CLASS command >= 4 mm (half the
machinery's own full arch c = 8.000 mm). The 1 mm boundary is a mine-side
READING convention in the measured order-of-magnitude gap.
THE SELECTION RULE (binding): every stall-era CMD_peak < 1 mm -> VERDICT A
COMMAND-STALL (the law candidate is bank item 2, the arch command's coupling to
the body's advance rate, ZERO new constants, the amendment freezes its clause);
every stall-era CMD_peak >= 4 mm with DEL_peak < 1 mm -> VERDICT B
SERVO-UNDERDELIVERY (the command is NOT the lever, the premise is KILLED, NO
law, the gate face named from the [dvq] reads); otherwise THE SPLIT (no single
mechanism law derivable; the per-era record IS the answer).
Output: mine_w42_out.txt (this run's preserved output).
"""
import re, collections

TRACE = ".tmp/w42_receipt/instr_tr_stderr.txt"

lines = open(TRACE, encoding="utf-8", errors="replace").read().splitlines()
idx = [i for i, l in enumerate(lines) if l.startswith("WALK REFUSED")]
run = lines[idx[-2] + 1:idx[-1]]
mref = re.match(r"WALK REFUSED tick (\d+): (\S+)", lines[idx[-1]])
refus = (int(mref.group(1)), mref.group(2))

dvfa = collections.defaultdict(dict)   # t -> leg -> (br, held, sg, c, cmd_y, pad_y, plant_y) FIRST sample per (t,leg)
dvfa_raw = collections.defaultdict(list)  # (t,leg) -> ALL samples (the substep census; the servo is called
dvfa_dup = 0                           # 8x per tick (4 substeps x 2 evaluations), the FIRST call is the
dvq = collections.defaultdict(dict)    # tick-start evaluation -- VERIFIED: at every fire tick the first
bx = {}                                # sample's pad_y EQUALS the fire line's fy to <1e-9 m, the fire
fires = []                             # decision's own basis; the declared pad_y basis is tick-start)
tds = []                               # (t, leg)
dvp = collections.defaultdict(dict)    # t -> k -> (gap,rxn,frc,slip,px,py)  (the status snapshot)
seen_ev = set()
for l in run:
    m = re.match(r"\[dvfa\] t=(\d+) leg=(\d) br=(\w) held=(\d) sg=(\S+) c=(\S+) cmd_y=(\S+) pad_y=(\S+) plant_y=(\S+)", l)
    if m:
        t, leg = int(m.group(1)), int(m.group(2))
        rec = (m.group(3), int(m.group(4)), float(m.group(5)), float(m.group(6)),
               float(m.group(7)), float(m.group(8)), float(m.group(9)))
        dvfa_raw[(t, leg)].append(rec)
        if leg in dvfa[t]: dvfa_dup += 1
        else: dvfa[t][leg] = rec
        continue
    m = re.match(r"\[dvp\] t=(\d+) k=(\d) gap=(\S+) rxn=(\S+) frc=(\S+) slip=(\S+) pos=(\S+),(\S+)", l)
    if m:
        dvp[int(m.group(1))][int(m.group(2))] = tuple(float(m.group(x)) for x in (3, 4, 5, 6, 7, 8)); continue
    m = re.match(r"\[dvq\] t=(\d+) k=(\d+) tau=(\S+) cap=(\S+)", l)
    if m:
        dvq[int(m.group(1))][int(m.group(2))] = (float(m.group(3)), float(m.group(4))); continue
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

out = open(".tmp/w42_receipt/mine_w42_out.txt", "w", encoding="utf-8")
def P(*a):
    s = " ".join(str(x) for x in a)
    out.write(s + "\n"); print(s)

P("refusal:", refus, " fires:", len(fires), " tds:", len(tds),
  " dvfa ticks:", len(dvfa), " dvfa dup (t,leg) beyond first:", dvfa_dup)
# THE SAMPLING-BASIS PROOF: the servo is called 8x per tick (4 substeps x 2 evaluations); the FIRST
# call is the tick-start evaluation (the fire decision's own basis). Verify at every fire tick:
# (the tolerance is the fire line's own %.6f print quantum for fy: 5e-7 m half-ulp, plus pad_y's 1e-9)
bad = 0; dmax = 0.0
for (ft, leg, cls, fx, fy, tx, ty, xoff, v, dl) in fires:
    a = dvfa.get(ft, {}).get(leg)
    if a is None: bad += 1; continue
    d = abs(a[5] - fy); dmax = max(dmax, d)
    if d > 2e-6: bad += 1
P("SAMPLING BASIS: first-sample pad_y == the fire's fy at every fire tick:", "PASS" if bad == 0 else "FAIL(%d)" % bad,
  " max |diff| %.3e m (the %.6f print quantum)" % (dmax, 1e-6),
  " (the substep census: %d (t,leg) series, cmd_y within-tick drift %d, pad_y within-tick drift %d)"
  % (len(dvfa_raw),
     sum(1 for v in dvfa_raw.values() if len(set(x[4] for x in v)) > 1),
     sum(1 for v in dvfa_raw.values() if len(set(x[5] for x in v)) > 1)))
# THE [dvp] CROSS-CHECK (declared; MEASURED-DIFFERENT, recorded honestly): the status snapshot's
# pos y mean is NOT the pad-center height -- it is the contact-solver's own point series (a
# different physical point: even pairmin-gap <= kTouch pads sit median 1.4e-2 m off the [dvfa]
# pad center, and separated pads' pos hugs the plane while the pad is airborne). The wave-42
# verdict rests on the [dvfa] series alone (its basis proven by the SAMPLING BASIS line above);
# the [dvp] pos relation is recorded so no later mine re-uses it as a height series.
dd = []; dtouch = []
for (t, leg), v in dvfa_raw.items():
    a, b = dvp.get(t, {}).get(2 * leg), dvp.get(t, {}).get(2 * leg + 1)
    if a and b:
        dd.append(abs(0.5 * (a[5] + b[5]) - v[-1][5]))
        if min(a[0], b[0]) <= 1e-5: dtouch.append(dd[-1])
dtouch.sort()
P("[dvp] CROSS-CHECK: |status pos y mean - last-sample pad_y| over %d (t,leg): max %.3e m;"
  % (len(dd), max(dd) if dd else float('nan')))
P("  in-contact (pairmin gap <= kTouch): n=%d median %.3e m -- MEASURED-DIFFERENT (the [dvp] pos is the"
  % (len(dtouch), dtouch[len(dtouch) // 2] if dtouch else float('nan')))
P("  contact point, NOT the pad center; NOT a height series for airborne pads; the verdict rests on [dvfa].")
FOLD = 35  # kFoldBudgetTicks - tair - 1 = 45 - 9 - 1 (the machinery's own constants)
rows = []
for (ft, leg, cls, fx, fy, tx, ty, xoff, v, dl) in fires:
    o = 1 - leg
    comp = next(((t, l) for (t, l) in tds if l == leg and t >= ft), None)
    ct = comp[0] if comp else max(t for t in dvfa if leg in dvfa[t] and t > ft)
    td_o = max((t for (t, l) in tds if l == o and t <= ft), default=0)
    form = "none" if dl == 0 else ("unload" if dl == td_o else ("fold" if dl == td_o + FOLD else "other"))
    # the era series
    cmd_peak = -1e9; del_peak = -1e9; brs = []; death = None; had_arch = False
    era_taus = []; era_caps = {}
    for t in range(ft, ct + 1):
        a = dvfa.get(t, {}).get(leg)
        if a is None: continue
        br, held, sg, c, cmd_y, pad_y, plant_y = a
        cr = (cmd_y - fy) * 1e3   # mm; cmd_y == -1 (the br=t sentinel) goes very negative -- a death read
        dr = (pad_y - fy) * 1e3
        cmd_peak = max(cmd_peak, cr); del_peak = max(del_peak, dr)
        brs.append(br)
        if cr >= 4.0: had_arch = True
        if had_arch and death is None and cr < 1.0: death = (t, br)
        # the demand face: the era leg's own four hind drives
        dk = range(0, 4) if leg == 0 else range(4, 8)
        for k in dk:
            q = dvq.get(t, {}).get(k)
            if q is None: continue
            era_taus.append(q[0]); era_caps[k] = q[1]
    span = ct - ft
    b0 = bx.get(ft - 1); b1 = bx.get(ct)
    adv = (b1 - b0) * 1e3 if (b0 is not None and b1 is not None) else float('nan')
    adv_rate = adv / span if span > 0 and adv == adv else float('nan')
    capmax = max(era_caps.values()) if era_caps else float('nan')
    taumax = max(era_taus) if era_taus else float('nan')
    pinned = (era_taus and era_caps and taumax >= 0.999 * capmax)
    era_class = "STALL" if del_peak < 1.0 else "LIFT"
    cmd_class = "cmd-stall" if cmd_peak < 1.0 else ("arch-class" if cmd_peak >= 4.0 else "GAP-ZONE")
    rows.append(dict(ft=ft, ct=ct, leg=leg, cls=cls, form=form, era_class=era_class,
                     cmd_peak=cmd_peak, del_peak=del_peak, cmd_class=cmd_class,
                     brs="".join(brs), death=death, adv=adv, adv_rate=adv_rate,
                     taumax=taumax, capmax=capmax, pinned=pinned))

P("ERA TABLE: fire->compl leg class FORM eraClass CMD_peak(mm) DEL_peak(mm) cmdClass branches deathTick bxAdv(mm) advRate(mm/t) tauMax capMax demandFace")
for r in rows:
    P("  %4d->%4d leg=%d %-4s %-6s %-5s CMD=%7.3f DEL=%7.3f %-10s %-9s death=%-10s adv=%6.2f rate=%5.2f tau=%6.3f cap=%5.3f %s"
      % (r["ft"], r["ct"], r["leg"], r["cls"], r["form"], r["era_class"], r["cmd_peak"], r["del_peak"],
         r["cmd_class"], r["brs"], str(r["death"]) if r["death"] else "none",
         r["adv"], r["adv_rate"], r["taumax"], r["capmax"],
         "PINNED" if r["pinned"] else "flows"))
P("-" * 118)
stall = [r for r in rows if r["era_class"] == "STALL"]
lift = [r for r in rows if r["era_class"] == "LIFT"]
a_cnt = sum(1 for r in stall if r["cmd_peak"] < 1.0)
b_cnt = sum(1 for r in stall if r["cmd_peak"] >= 4.0)
g_cnt = len(stall) - a_cnt - b_cnt
P("STALL ERAS:", len(stall), " (DEL_peak < 1 mm)  command-stall:", a_cnt,
  "  arch-class-command (servo-dead):", b_cnt, "  gap-zone:", g_cnt)
if stall:
    P("  stall CMD_peak band: %.3f - %.3f mm   stall DEL_peak band: %.3f - %.3f mm"
      % (min(r["cmd_peak"] for r in stall), max(r["cmd_peak"] for r in stall),
         min(r["del_peak"] for r in stall), max(r["del_peak"] for r in stall)))
if lift:
    P("LIFT ERAS:", len(lift), "  CMD_peak band: %.3f - %.3f mm   DEL_peak band: %.3f - %.3f mm"
      % (min(r["cmd_peak"] for r in lift), max(r["cmd_peak"] for r in lift),
         min(r["del_peak"] for r in lift), max(r["del_peak"] for r in lift)))
P("-" * 118)
if stall and a_cnt == len(stall):
    P("THE SELECTION RULE (fixed in receipt_wave42.json): VERDICT A -- COMMAND-STALL (bank item 2: the arch")
    P("command's coupling to the body's advance rate; the amendment freezes its clause from the mine).")
elif stall and b_cnt == len(stall):
    P("THE SELECTION RULE (fixed in receipt_wave42.json): VERDICT B -- SERVO-UNDERDELIVERY (the command is NOT")
    P("the lever; the premise is KILLED; NO law; the gate face names itself from the [dvq] demand reads).")
else:
    P("THE SELECTION RULE (fixed in receipt_wave42.json): THE SPLIT (no single-mechanism law derivable; the")
    P("per-era record IS the answer; the amendment never invents).")
pin = sum(1 for r in stall if r["pinned"])
P("THE DEMAND FACE over the stall eras: tau pinned at cap in %d of %d (tauMax %.3f vs capMax %.3f over all)"
  % (pin, len(stall), max((r["taumax"] for r in stall), default=float('nan')),
     max((r["capmax"] for r in stall), default=float('nan'))))
P("THE BODY ADVANCE (the wave-41 creep census, this lane's faces): stall eras %.2f-%.2f mm at %.2f-%.2f mm/tick; lift eras %.2f-%.2f mm at %.2f-%.2f mm/tick"
  % (min((r["adv"] for r in stall), default=float('nan')), max((r["adv"] for r in stall), default=float('nan')),
     min((r["adv_rate"] for r in stall), default=float('nan')), max((r["adv_rate"] for r in stall), default=float('nan')),
     min((r["adv"] for r in lift), default=float('nan')), max((r["adv"] for r in lift), default=float('nan')),
     min((r["adv_rate"] for r in lift), default=float('nan')), max((r["adv_rate"] for r in lift), default=float('nan'))))
out.close()
print("written .tmp/w42_receipt/mine_w42_out.txt")
