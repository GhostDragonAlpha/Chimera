#!/usr/bin/env python3
"""THE WAVE-43 MINE (declared instrument .tmp/w43_receipt/mine_w43.py).
Reads THIS LANE'S INSTRUMENTED TRACE ONLY: .tmp/w43_receipt/instr_tr_stderr.txt
(the [dvfj] plumbing build: stdout 8c537cdb EXACT, plain==trace byte-equal,
refusal 302, ledger 30.970714, 49/173; the trace fence GREEN -- the base trace
a307f7b0 [the wave-42 live-plumbing trace, [dvfa] counted as base] plus inserted
[dvfj] lines only). Parses the LAST walk run (the wave-39/40/41/42 declared
convention). [hindstep] event lines DEDUPED by full line text.

THE QUESTION (the wave-43 bank): WHERE INSIDE hind_step_ik DOES THE +8 mm
DEMAND GO -- (a) the ANNULUS CLAMP (the solved point itself never rises), (b)
THE CHAIN (the solved point rises and the PD-driven chain underdelivers it in
joint space), or (c) THE HELD DECLARATIONS (the frozen MP target / the fire's
branch pin absorbing the demand)?

THE DECISION RULE (fixed in receipt_wave43.json BEFORE the numbers below were
read; restated verbatim): the era convention is receipt_wave41.json's verbatim
as corrected at wave-42 (the [hindstep] fire/td lines deduped by full line
text; the fire's from=(fx,fy) the era's plant anchor; the era span [f, ct], ct
the fired leg's first td at t >= f or the trace's end; the [dvfa]/[dvfj] FIRST
sample per (t,leg) is the tick-start basis -- the wave-42 fire-anchor identity
carries). Per swing era, on the era leg's own [dvfj] first-sample series:
  SOL_bias_f  = sol_y(f) - fy (the solved-point model offset vs the pads'
              midpoint at the fire anchor, reported, never tuned);
  SOLVED_rise = max over t in [f,ct] of (sol_y(t) - sol_y(f)) -- the IK's OWN
              output rise, offset-free;
  BIAS_drift  = max over t of |(sol_y(t)-cmd_y(t)) - (sol_y(f)-cmd_y(f))| --
              the within-era drift of the model-vs-command offset (the
              contamination bound on SOLVED_rise; reported);
  SHORT_peak  = max over t of (cmd_y(t) - sol_y(t)) -- the shortfall the clamp
              ate (carries the documented model offset);
  CLMP_frac   = the clmp=1 fraction of the era's first samples;
  D_max/dmax  = the demanded wrist distance max vs the chain's own annulus;
  TRACK_max   = max over t of max(|qh-ah|,|qk-ak|,|qa-aa|) with the holding
              drive NAMED; per-drive maxes reported;
  MPDEV_max   = max over t of |amp - mp| (the held-MP face);
  the brn census; CMD_peak/DEL_peak carried from the [dvfa] series (the
  wave-42 verbatim); the [dvq] tau/cap demand face carried (the wave-42
  convention: demand-pinned iff some drive reads tau >= 0.999*cap at some era
  tick, else demand-flows; the tau at the TRACK argmax tick reported).
THE ERA CLASS faces carried VERBATIM: STALL-CLASS DEL_peak < 1 mm, LIFT-CLASS
DEL_peak >= 1 mm; ARCH-CLASS >= 4 mm. The 1 mm / 4 mm boundaries are mine-side
READING conventions in the measured gaps; the raw per-era numbers are reported.
THE SELECTION RULE (binding): (1) every stall-era SOLVED_rise < 1 mm with
SHORT_peak >= 4 mm -> VERDICT C-IK-ANNULUS; (2) every stall-era SOLVED_rise
>= 4 mm with DEL_peak < 1 mm -> VERDICT C-CHAIN; (3) otherwise THE SPLIT (the
per-era table IS the answer; no single-mechanism law; the amendment never
invents). In every verdict a law build happens ONLY on one lawful zero-new-
constant clause with the wave-33 pin untouched; else the wave-41/42 no-law
precedent. THE LIVE IDENTITY (P43_the_identity): |sol_y - cmd_y| <= 1e-6 m on
every clmp=0 sample of the declared trace (ALL samples, not just first).
Output: mine_w43_out.txt (this run's preserved output).
"""
import re, collections

TRACE = ".tmp/w43_receipt/instr_tr_stderr.txt"

lines = open(TRACE, encoding="utf-8", errors="replace").read().splitlines()
idx = [i for i, l in enumerate(lines) if l.startswith("WALK REFUSED")]
run = lines[idx[-2] + 1:idx[-1]]
mref = re.match(r"WALK REFUSED tick (\d+): (\S+)", lines[idx[-1]])
refus = (int(mref.group(1)), mref.group(2))

dvfa = collections.defaultdict(dict)   # t -> leg -> (br,held,sg,c,cmd_y,pad_y,plant_y) FIRST sample
dvfj = collections.defaultdict(dict)   # t -> leg -> dict FIRST sample
dvfj_all = []                          # EVERY [dvfj] sample (the live-identity census)
dvq = collections.defaultdict(dict)    # t -> k -> (tau, cap)
bx = {}
fires = []                             # (t, leg, cls, fx, fy, tx, ty, xoff, v, dl)
tds = []                               # (t, leg)
seen_ev = set()
for l in run:
    m = re.match(r"\[dvfa\] t=(\d+) leg=(\d) br=(\w) held=(\d) sg=(\S+) c=(\S+) cmd_y=(\S+) pad_y=(\S+) plant_y=(\S+)", l)
    if m:
        t, leg = int(m.group(1)), int(m.group(2))
        if leg not in dvfa[t]:
            dvfa[t][leg] = (m.group(3), int(m.group(4)), float(m.group(5)), float(m.group(6)),
                            float(m.group(7)), float(m.group(8)), float(m.group(9)))
        continue
    m = re.match(r"\[dvfj\] t=(\d+) leg=(\d) br=(\w) brn=(-?\d+) ap=(\S+) qh=(\S+) qk=(\S+) qa=(\S+) mp=(\S+) ah=(\S+) ak=(\S+) aa=(\S+) amp=(\S+) D=(\S+) Dc=(\S+) dmax=(\S+) clmp=(\d) sol_x=(\S+) sol_y=(\S+)", l)
    if m:
        t, leg = int(m.group(1)), int(m.group(2))
        rec = dict(br=m.group(3), brn=int(m.group(4)), ap=float(m.group(5)),
                   qh=float(m.group(6)), qk=float(m.group(7)), qa=float(m.group(8)),
                   mp=float(m.group(9)), ah=float(m.group(10)), ak=float(m.group(11)),
                   aa=float(m.group(12)), amp=float(m.group(13)), D=float(m.group(14)),
                   Dc=float(m.group(15)), dmax=float(m.group(16)), clmp=int(m.group(17)),
                   sol_x=float(m.group(18)), sol_y=float(m.group(19)))
        dvfj_all.append((t, leg, rec))
        if leg not in dvfj[t]: dvfj[t][leg] = rec
        continue
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

out = open(".tmp/w43_receipt/mine_w43_out.txt", "w", encoding="utf-8")
def P(*a):
    s = " ".join(str(x) for x in a)
    out.write(s + "\n"); print(s)

P("refusal:", refus, " fires:", len(fires), " tds:", len(tds),
  " dvfj (t,leg) first-sample series:", len(dvfj), " dvfj ALL samples:", len(dvfj_all))
# THE SAMPLING BASIS (wave-42 carry): the first [dvfj] sample at every fire tick must exist
missing = sum(1 for (ft, leg, *_r) in fires if leg not in dvfj.get(ft, {}))
P("SAMPLING BASIS: [dvfj] present at the fire tick (first sample) for %d/%d fires" % (len(fires) - missing, len(fires)))
# THE LIVE IDENTITY (P43_the_identity, ALL samples): unclamped |sol_y - cmd_y| <= 1e-6 m
viol = 0; worst = 0.0; wtick = None; nun = 0
for (t, leg, r) in dvfj_all:
    a = dvfa.get(t, {}).get(leg)
    if a is None or r["clmp"] != 0: continue
    nun += 1
    d = abs(r["sol_y"] - a[4])
    if d > worst: worst, wtick = d, (t, leg)
    if d > 1e-6: viol += 1
P("THE LIVE IDENTITY (P43_the_identity): unclamped samples checked:", nun,
  " violations beyond 1e-6 m:", viol, " worst |sol_y-cmd_y| %.6f m at" % worst, wtick)
cl_short = -1e9
for (t, leg, r) in dvfj_all:
    if r["clmp"] == 1 and leg in dvfa.get(t, {}):
        cl_short = max(cl_short, dvfa[t][leg][4] - r["sol_y"])
P("  clamped samples:", sum(1 for (_t, _l, r) in dvfj_all if r["clmp"] == 1),
  " max clamp shortfall (cmd_y-sol_y): %.6f m" % cl_short)
FOLD = 35  # kFoldBudgetTicks - tair - 1 = 45 - 9 - 1 (the machinery's own constants)
rows = []
for (ft, leg, cls, fx, fy, tx, ty, xoff, v, dl) in fires:
    o = 1 - leg
    comp = next(((t, l) for (t, l) in tds if l == leg and t >= ft), None)
    ct = comp[0] if comp else max(t for t in dvfj if leg in dvfj[t] and t > ft)
    td_o = max((t for (t, l) in tds if l == o and t <= ft), default=0)
    form = "none" if dl == 0 else ("unload" if dl == td_o else ("fold" if dl == td_o + FOLD else "other"))
    f0 = dvfj.get(ft, {}).get(leg)
    a0 = dvfa.get(ft, {}).get(leg)
    if f0 is None or a0 is None: continue
    bias_f = f0["sol_y"] - fy
    solved_rise = -1e9; short_peak = -1e9; clmp_n = 0; n = 0; D_max = -1e9
    track_max = -1e9; track_arg = None; track_hold = "?"
    per = {"hip": 0., "knee": 0., "ankle": 0.}
    mpdev = 0.; brns = set(); bias_drift = 0.
    cmd_peak = -1e9; del_peak = -1e9
    era_taus = []; era_caps = {}; tau_at_track = float("nan")
    eh0 = ek0 = float("nan"); eh1 = ek1 = float("nan"); tauk_f = float("nan")
    for t in range(ft, ct + 1):
        a = dvfa.get(t, {}).get(leg); f = dvfj.get(t, {}).get(leg)
        if a is None or f is None: continue
        n += 1
        if t == ft:
            eh0 = f["qh"] - f["ah"]; ek0 = f["qk"] - f["ak"]
            kk = dvq.get(ft, {}).get(1 if leg == 0 else 5)
            if kk: tauk_f = kk[0]
        eh1 = f["qh"] - f["ah"]; ek1 = f["qk"] - f["ak"]
        cmd_y, pad_y = a[4], a[5]
        cmd_peak = max(cmd_peak, (cmd_y - fy) * 1e3); del_peak = max(del_peak, (pad_y - fy) * 1e3)
        solved_rise = max(solved_rise, (f["sol_y"] - f0["sol_y"]) * 1e3)
        short_peak = max(short_peak, (cmd_y - f["sol_y"]) * 1e3)
        bias_drift = max(bias_drift, abs((f["sol_y"] - cmd_y) - (f0["sol_y"] - a0[4])) * 1e3)
        clmp_n += 1 if f["clmp"] else 0
        D_max = max(D_max, f["D"])
        tr = max(abs(f["qh"] - f["ah"]), abs(f["qk"] - f["ak"]), abs(f["qa"] - f["aa"]))
        for nm, qs, as_ in (("hip", f["qh"], f["ah"]), ("knee", f["qk"], f["ak"]), ("ankle", f["qa"], f["aa"])):
            per[nm] = max(per[nm], abs(qs - as_))
        if tr > track_max:
            track_max = tr; track_arg = t
            hold = max((("hip", abs(f["qh"] - f["ah"])), ("knee", abs(f["qk"] - f["ak"])), ("ankle", abs(f["qa"] - f["aa"]))), key=lambda x: x[1])
            track_hold = hold[0]
        mpdev = max(mpdev, abs(f["amp"] - f["mp"]))
        brns.add(f["brn"])
        dk = range(0, 4) if leg == 0 else range(4, 8)
        for k in dk:
            q = dvq.get(t, {}).get(k)
            if q is None: continue
            era_taus.append(q[0]); era_caps[k] = q[1]
    if track_arg is not None and dvq.get(track_arg):
        dk = range(0, 4) if leg == 0 else range(4, 8)
        tt = [dvq.get(track_arg, {}).get(k) for k in dk if dvq.get(track_arg, {}).get(k)]
        if tt: tau_at_track = max(x[0] for x in tt)
    b0 = bx.get(ft - 1); b1 = bx.get(ct)
    adv = (b1 - b0) * 1e3 if (b0 is not None and b1 is not None) else float("nan")
    capmax = max(era_caps.values()) if era_caps else float("nan")
    taumax = max(era_taus) if era_taus else float("nan")
    pinned = (era_taus and era_caps and taumax >= 0.999 * capmax)
    era_class = "STALL" if del_peak < 1.0 else "LIFT"
    rows.append(dict(ft=ft, ct=ct, leg=leg, form=form, era_class=era_class,
                     cmd_peak=cmd_peak, del_peak=del_peak, bias_f=bias_f * 1e3,
                     solved_rise=solved_rise, bias_drift=bias_drift, short_peak=short_peak,
                     clmp_frac=clmp_n / max(n, 1), n=n, D_max=D_max, dmax=f0["dmax"],
                     track_max=track_max, track_hold=track_hold, track_arg=track_arg,
                     per=per, mpdev=mpdev, brns=sorted(brns), adv=adv,
                     taumax=taumax, capmax=capmax, pinned=pinned, tau_at_track=tau_at_track,
                     eh0=eh0, ek0=ek0, eh1=eh1, ek1=ek1, tauk_f=tauk_f))

P("ERA TABLE: fire->compl leg form eraClass CMD_peak DEL_peak SOLbias_f SOLVED_rise BIASdrift SHORT_peak CLMPfrac D_max/dmax TRACK_max(hold@t) perDrive MPDEV brn tauAtTrack demandFace FIRE_GAP e0h/e0k->e1h/e1k tauK@fire bxAdv")
for r in rows:
    P("  %4d->%4d leg=%d %-6s %-5s CMD=%7.3f DEL=%7.3f b0=%+6.3f SOLV=%7.3f drift=%6.3f SHORT=%7.3f clmp=%4.2f D/dmax=%6.3f/%6.3f TRK=%.4f(%s@%s) [h%.4f k%.4f a%.4f] MP=%.2e br=%s tau=%6.3f %s GAP=%s adv=%6.2f"
      % (r["ft"], r["ct"], r["leg"], r["form"], r["era_class"], r["cmd_peak"], r["del_peak"],
         r["bias_f"], r["solved_rise"], r["bias_drift"], r["short_peak"], r["clmp_frac"],
         r["D_max"], r["dmax"], r["track_max"], r["track_hold"], r["track_arg"],
         r["per"]["hip"], r["per"]["knee"], r["per"]["ankle"], r["mpdev"],
         ",".join(str(b) for b in r["brns"]), r["tau_at_track"],
         "PINNED" if r["pinned"] else "flows",
         "%+.4f/%+.4f->%+.4f/%+.4f tauK=%6.3f" % (r["eh0"], r["ek0"], r["eh1"], r["ek1"], r["tauk_f"]),
         r["adv"]))
P("-" * 150)
stall = [r for r in rows if r["era_class"] == "STALL"]
lift = [r for r in rows if r["era_class"] == "LIFT"]
ann = sum(1 for r in stall if r["solved_rise"] < 1.0 and r["short_peak"] >= 4.0)
chn = sum(1 for r in stall if r["solved_rise"] >= 4.0)
P("STALL ERAS:", len(stall), " (DEL_peak < 1 mm)   annulus-die (SOLVED_rise<1 & SHORT>=4):", ann,
  "  chain-die (SOLVED_rise>=4):", chn, "  other:", len(stall) - ann - chn)
if stall:
    P("  stall bands: SOLVED_rise %.3f-%.3f mm  SHORT_peak %.3f-%.3f mm  CLMP_frac %.2f-%.2f  TRACK_max %.4f-%.4f rad  MPDEV_max %.2e rad"
      % (min(r["solved_rise"] for r in stall), max(r["solved_rise"] for r in stall),
         min(r["short_peak"] for r in stall), max(r["short_peak"] for r in stall),
         min(r["clmp_frac"] for r in stall), max(r["clmp_frac"] for r in stall),
         min(r["track_max"] for r in stall), max(r["track_max"] for r in stall),
         max(r["mpdev"] for r in stall)))
if stall:
    P("  stall FIRE GAP (the solve-vs-actual jump at the fire, rad): hip %.4f-%.4f  knee %.4f-%.4f   era-end gap: hip %.4f-%.4f  knee %.4f-%.4f  (tauK at fire %.3f-%.3f N.m)"
      % (min(abs(r["eh0"]) for r in stall), max(abs(r["eh0"]) for r in stall),
         min(abs(r["ek0"]) for r in stall), max(abs(r["ek0"]) for r in stall),
         min(abs(r["eh1"]) for r in stall), max(abs(r["eh1"]) for r in stall),
         min(abs(r["ek1"]) for r in stall), max(abs(r["ek1"]) for r in stall),
         min(r["tauk_f"] for r in stall), max(r["tauk_f"] for r in stall)))
if lift:
    P("  lift FIRE GAP (rad): hip %.4f-%.4f  knee %.4f-%.4f   era-end gap: hip %.4f-%.4f  knee %.4f-%.4f"
      % (min(abs(r["eh0"]) for r in lift), max(abs(r["eh0"]) for r in lift),
         min(abs(r["ek0"]) for r in lift), max(abs(r["ek0"]) for r in lift),
         min(abs(r["eh1"]) for r in lift), max(abs(r["eh1"]) for r in lift),
         min(abs(r["ek1"]) for r in lift), max(abs(r["ek1"]) for r in lift)))
if lift:
    P("LIFT ERAS:", len(lift), "  SOLVED_rise %.3f-%.3f mm  DEL_peak %.3f-%.3f mm  CLMP_frac %.2f-%.2f"
      % (min(r["solved_rise"] for r in lift), max(r["solved_rise"] for r in lift),
         min(r["del_peak"] for r in lift), max(r["del_peak"] for r in lift),
         min(r["clmp_frac"] for r in lift), max(r["clmp_frac"] for r in lift)))
P("-" * 150)
if stall and ann == len(stall):
    P("THE SELECTION RULE (fixed in receipt_wave43.json): VERDICT C-IK-ANNULUS (the +8 mm demand dies AT")
    P("the annulus clamp; the solved point itself never rises; law ONLY on a zero-new-constant clause, else no law).")
elif stall and chn == len(stall):
    P("THE SELECTION RULE (fixed in receipt_wave43.json): VERDICT C-CHAIN (the demand survives the IK -- the")
    P("solved point rises -- and the chain underdelivers it in joint space; the face is the TRACK decomposition).")
else:
    P("THE SELECTION RULE (fixed in receipt_wave43.json): THE SPLIT (no single-mechanism law derivable; the")
    P("per-era record IS the answer; the amendment never invents).")
out.close()
print("written .tmp/w43_receipt/mine_w43_out.txt")
