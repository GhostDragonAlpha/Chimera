#!/usr/bin/env python3
"""THE WAVE-44 MINE (declared instrument receipt_wave44.json).
Reads THIS LANE'S INSTRUMENTED TRACE ONLY: .tmp/w44_receipt/instr_tr_stderr.txt
(the [dvfk] plumbing build: stdout 8c537cdb EXACT, plain==trace byte-equal,
refusal 302, ledger 30.970714, 49/173; the trace fence GREEN -- the base trace
5f170542 [the wave-43 live-plumbing trace, [dvfa]+[dvfj] counted as base] plus
inserted [dvfk] lines only). Parses the LAST walk run (the wave-39..43 declared
convention). [hindstep] event lines DEDUPED by full line text.

THE QUESTION (the wave-44 bank): WHAT SETS THE FIRE GAP -- (a) the FIRE-TIME
STATE of the chain, readable by the walk's own clocks/conditions (a fire-gate
condition on the wave-32 deadline family's pattern could defer the fire until
the gap is lift-class -- zero new constants), or (b) the PRECEDING ERA'S
LANDING GEOMETRY (the gap built stance-side; the law moves to the landing side).

THE DECISION RULE (fixed in receipt_wave44.json BEFORE the numbers below were
read; restated verbatim): the era convention is receipt_wave41.json's verbatim
as corrected at wave-42/43 (the [hindstep] fire/td lines deduped by full line
text; the fire's from=(fx,fy) the era's plant anchor; the era span [f, ct], ct
the fired leg's first td at t >= f or the trace's end; the [dvfa]/[dvfj]/[dvfk]
FIRST sample per (t,leg) is the tick-start basis). Per fire (ALL 18 eras), on
the era leg's own series:
  FIRE_GAP  e0h/e0k = qh-ah / qk-ak at the fire ([dvfj] first sample, the
            wave-43 verbatim); qerr the fire line's ANCHOR-ONLY distance (the
            solve of `from` WITHOUT the arch).
  ERA-END   e1h/e1k at the era's last sampled tick (the wave-43 convention).
  SWING DECAY per drive = (e1-e0)/(ct-f) rad/tick.
            STANCE BUILD over the leg's OWN stance interval [prev_td, f) -- the
            td tick itself is stance-sampled (the mode flips before servo) --
            from the [dvfk] first-sample
            series: g_h=qh-ah, g_k=qk-ak per branch letter (br=d the
            stand-first hold's pinned solve, br=t the stance tables' pose);
            BUILD dh/dk = g(f-)-g(td+) per drive; the d/t sub-span line
            counts; the fire jump jh/jk = e0 - g(f-).
  THE CLOCKS AT THE FIRE: class (alt/slot, the fire line's own field), the
            deadline form (the wave-43 verbatim: dl==0 none; dl==other's last
            td unload; dl==td_o+FOLD fold, FOLD=35 = kFoldBudgetTicks-tair-1,
            the machinery's own constants), stance span f - the leg's own last
            td (entry if none), the census events (waivefire/unloadgate/
            guardblock) at the fire tick, CMD_peak/DEL_peak ([dvfa] vs the
            fire anchor fy, the wave-42/43 verbatim), CLMP_frac, tauH/tauK@fire
            + the era PINNED/flows census ([dvq], the wave-43 verbatim; the
            PD-authority face, mine-only).
THE SEPARABILITY CENSUS (frozen): the faces, each the machinery's OWN discrete
read -- (F1) fire class alt vs slot; (F2) deadline form unload vs fold; (F3)
stance span in {=1 (the clause-(b) g-window), =tair, other}; (F4) a
waivefire/unloadgate/guardblock census event at the fire tick; (F5) the era's
clamp regime (CLMP_frac 0 vs >0). A face SEPARATES iff SOME value group holds
ALL 8 stall fires and no lift fire, or ALL 10 lift fires and no stall fire
(a clean 8-vs-10 split on one side of one face).
THE DRIFT TEST (P44_the_drift): the signed e0h/e0k series in era order; the
step direction census vs the era index; the least-squares slope vs the
cumulative body advance bx (the [dv] bx series, the machinery's own read; the
slope is a mine-side READING convention, no shipped constants); the detrended
class residual ranges; the classes "separate beyond the within-class spread"
iff the detrended residual ranges are disjoint.
THE REACHABILITY TEST (P44_the_reachability): per stall fire, the stance
|g| trajectory over (prev_td, f): PERSIST/GROW iff |g(f-)| >= |g(td+)|; a
deferral window exists iff some stall fire's stance hip series decays MONOTONE
into the lift band (the lift band read as |e0h| <= the max lift |e0h| -- a
mine-side READING convention in the measured gaps).
THE SELECTION RULE (binding): (1) C-FIREGATE iff at least one face separates;
a law build ONLY on a zero-new-constant clause with the wave-33 pin untouched
and BOTH dual-gate letters, else NO law and the face recorded; (2) C-LANDING
iff NO face separates AND the stance-side build / preceding-close series
predicts the fire gap; (3) else THE RECORD. In EVERY verdict the amendment
NEVER invents. Output: mine_wave44_out.txt (this run's preserved output).
"""
import re, collections

TRACE = ".tmp/w44_receipt/instr_tr_stderr.txt"

lines = open(TRACE, encoding="utf-8", errors="replace").read().splitlines()
idx = [i for i, l in enumerate(lines) if l.startswith("WALK REFUSED")]
run = lines[idx[-2] + 1:idx[-1]]
mref = re.match(r"WALK REFUSED tick (\d+): (\S+)", lines[idx[-1]])
refus = (int(mref.group(1)), mref.group(2))

dvfa = collections.defaultdict(dict)   # t -> leg -> (br,held,sg,c,cmd_y,pad_y,plant_y) FIRST sample
dvfj = collections.defaultdict(dict)   # t -> leg -> dict FIRST sample
dvfk = collections.defaultdict(dict)   # t -> leg -> dict FIRST sample
dvq = collections.defaultdict(dict)    # t -> k -> (tau, cap)
bx = {}
fires = []                             # (t, leg, cls, fy, qerr, dl)
tds = []                               # (t, leg)
events = collections.defaultdict(list) # t -> [event names at t]
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
        rec = dict(qh=float(m.group(6)), qk=float(m.group(7)), qa=float(m.group(8)),
                   ah=float(m.group(10)), ak=float(m.group(11)), aa=float(m.group(12)),
                   clmp=int(m.group(17)))
        if leg not in dvfj[t]: dvfj[t][leg] = rec
        continue
    m = re.match(r"\[dvfk\] t=(\d+) leg=(\d) br=([dt]) phi=(\S+) qh=(\S+) qk=(\S+) qa=(\S+) ah=(\S+) ak=(\S+) aa=(\S+) stag=(\d+) oth=(\d) dl=(\d+)", l)
    if m:
        t, leg = int(m.group(1)), int(m.group(2))
        rec = dict(br=m.group(3), phi=float(m.group(4)),
                   qh=float(m.group(5)), qk=float(m.group(6)), qa=float(m.group(7)),
                   ah=float(m.group(8)), ak=float(m.group(9)), aa=float(m.group(10)),
                   stag=int(m.group(11)), oth=int(m.group(12)), dl=int(m.group(13)))
        if leg not in dvfk[t]: dvfk[t][leg] = rec
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
        m = re.match(r"\[hindstep\] fire leg=(\d) tick=(\d+) phi=\S+ class=(\S+) from=\((\S+),(\S+)\) to=\((\S+),(\S+)\) xoff=(\S+) v=(\S+) qerr=(\S+) ap=\S+ br=\S+ dl=(\d+)", l)
        if m:
            fires.append((int(m.group(2)), int(m.group(1)), m.group(3),
                          float(m.group(5)), float(m.group(10)), int(m.group(11)))); continue
        m = re.match(r"\[hindstep\] td leg=(\d) tick=(\d+)", l)
        if m: tds.append((int(m.group(2)), int(m.group(1)))); continue
        m = re.match(r"\[hindstep\] (\w+) leg=\d tick=(\d+)", l)
        if m and m.group(1) in ("waivefire", "unloadgate", "guardblock"):
            events[int(m.group(2))].append(m.group(1)); continue

out = open(".tmp/w44_receipt/mine_wave44_out.txt", "w", encoding="utf-8")
def P(*a):
    s = " ".join(str(x) for x in a)
    out.write(s + "\n"); print(s)

P("refusal:", refus, " fires:", len(fires), " tds:", len(tds),
  " dvfk (t,leg) first-sample series:", len(dvfk),
  " dvfj series:", len(dvfj), " dvfa series:", len(dvfa))
P("SAMPLING BASIS: [dvfj] present at the fire tick (first sample) for %d/%d fires"
  % (sum(1 for (ft, leg, *_r) in fires if leg in dvfj.get(ft, {})), len(fires)))
FOLD = 35  # kFoldBudgetTicks - tair - 1 = 45 - 9 - 1 (the machinery's own constants)
TAIR = 9
rows = []
for (ft, leg, cls, fy, qerr, dl) in fires:
    o = 1 - leg
    comp = next(((t, l) for (t, l) in tds if l == leg and t >= ft), None)
    ct = comp[0] if comp else max(t for t in dvfj if leg in dvfj[t] and t > ft)
    td_o = max((t for (t, l) in tds if l == o and t <= ft), default=0)
    form = "none" if dl == 0 else ("unload" if dl == td_o else ("fold" if dl == td_o + FOLD else "other"))
    td_self = max((t for (t, l) in tds if l == leg and t <= ft), default=None)
    span = None if td_self is None else ft - td_self
    f0 = dvfj.get(ft, {}).get(leg)
    a0 = dvfa.get(ft, {}).get(leg)
    if f0 is None or a0 is None: continue
    e0h = f0["qh"] - f0["ah"]; e0k = f0["qk"] - f0["ak"]
    e1h = e0h; e1k = e0k; clmp_n = 0; n = 0
    cmd_peak = -1e9; del_peak = -1e9
    era_taus = []; era_caps = {}; tauk_f = float("nan"); tauh_f = float("nan")
    kk = dvq.get(ft, {}).get(1 if leg == 0 else 5)
    if kk: tauk_f = kk[0]
    kh = dvq.get(ft, {}).get(0 if leg == 0 else 4)
    if kh: tauh_f = kh[0]
    for t in range(ft, ct + 1):
        a = dvfa.get(t, {}).get(leg); f = dvfj.get(t, {}).get(leg)
        if a is None or f is None: continue  # the wave-43 verbatim: BOTH the tick-start samples required
        n += 1
        e1h = f["qh"] - f["ah"]; e1k = f["qk"] - f["ak"]
        cmd_y, pad_y = a[4], a[5]
        cmd_peak = max(cmd_peak, (cmd_y - fy) * 1e3)
        del_peak = max(del_peak, (pad_y - fy) * 1e3)
        clmp_n += 1 if f["clmp"] else 0
        dk2 = range(0, 4) if leg == 0 else range(4, 8)
        for k in dk2:
            q = dvq.get(t, {}).get(k)
            if q is None: continue
            era_taus.append(q[0]); era_caps[k] = q[1]
    # THE STANCE BUILD: the [dvfk] series over [prev_td, ft) -- the td tick itself
    # is stance-sampled (the mode flips before servo; [dvfk] prints at prev_td)
    s_ticks = [t for t in range(td_self, ft) if td_self is not None and leg in dvfk.get(t, {})] if td_self is not None else []
    gh0 = gk0 = gh1 = gk1 = float("nan")
    dsub = collections.Counter()
    for t in s_ticks:
        r = dvfk[t][leg]
        dsub[r["br"]] += 1
        if t == s_ticks[0]: gh0 = r["qh"] - r["ah"]; gk0 = r["qk"] - r["ak"]
        gh1 = r["qh"] - r["ah"]; gk1 = r["qk"] - r["ak"]
    dh = (gh1 - gh0) if s_ticks else 0.0
    dk = (gk1 - gk0) if s_ticks else 0.0
    jh = (e0h - gh1) if s_ticks else float("nan")
    jk = (e0k - gk1) if s_ticks else float("nan")
    capmax = max(era_caps.values()) if era_caps else float("nan")
    taumax = max(era_taus) if era_taus else float("nan")
    pinned = (era_taus and era_caps and taumax >= 0.999 * capmax)
    era_class = "STALL" if del_peak < 1.0 else "LIFT"
    rows.append(dict(ft=ft, ct=ct, leg=leg, form=form, era_class=era_class, cls=cls,
                     cmd_peak=cmd_peak, del_peak=del_peak, e0h=e0h, e0k=e0k, e1h=e1h, e1k=e1k,
                     qerr=qerr, span=span, td_self=td_self, dl=dl, ev=sorted(set(events.get(ft, []))),
                     nstance=len(s_ticks), dsub=dict(dsub), dh=dh, dk=dk, jh=jh, jk=jk,
                     gh_f=gh1, gk_f=gk1,
                     decayh=(e1h - e0h) / max(ct - ft, 1), decayk=(e1k - e0k) / max(ct - ft, 1),
                     clmp_frac=clmp_n / max(n, 1), tauk_f=tauk_f, tauh_f=tauh_f, pinned=pinned,
                     bx=bx.get(ft - 1)))

P("ERA TABLE: fire->compl leg fireCls eraClass form dl STANCEspan CMD DEL e0h/e0k qerr(anchor) stanceBuild dh/dk(d/t ticks) fireJump jh/jk ERA-END e1h/e1k swingDecay dh/dk tauH/tauK@fire demand CLMPfrac")
for r in rows:
    P("  %4d->%4d leg=%d %-3s %-5s %-6s dl=%4d span=%4s CMD=%7.3f DEL=%7.3f e0=%+.4f/%+.4f qerr=%.2e build=%+.4f/%+.4f(%dd/%dt n=%d) jump=%+.4f/%+.4f e1=%+.4f/%+.4f dec=%+.4f/%+.4f tauH=%6.3f tauK=%6.3f %s clmp=%4.2f"
      % (r["ft"], r["ct"], r["leg"], r["cls"], r["era_class"], r["form"], r["dl"],
         ("entry" if r["span"] is None else r["span"]), r["cmd_peak"], r["del_peak"],
         r["e0h"], r["e0k"], r["qerr"], r["dh"], r["dk"],
         r["dsub"].get("d", 0), r["dsub"].get("t", 0), r["nstance"],
         r["jh"], r["jk"], r["e1h"], r["e1k"], r["decayh"], r["decayk"],
         r["tauh_f"], r["tauk_f"], "PINNED" if r["pinned"] else "flows", r["clmp_frac"]))
P("-" * 150)
stall = [r for r in rows if r["era_class"] == "STALL"]
lift = [r for r in rows if r["era_class"] == "LIFT"]
P("ERA CLASSES: %d STALL (fires %s) / %d LIFT (fires %s)"
  % (len(stall), [r["ft"] for r in stall], len(lift), [r["ft"] for r in lift]))

# ---- THE SEPARABILITY CENSUS (frozen faces F1..F5) ----
P("THE SEPARABILITY CENSUS (F1..F5, the machinery's own discrete reads):")
def face_rows(face_fn, name):
    vals = collections.OrderedDict()
    for r in rows:
        vals.setdefault(face_fn(r), []).append(r)
    sep = False
    for v in vals.values():
        s_ = sum(1 for x in v if x["era_class"] == "STALL")
        l_ = sum(1 for x in v if x["era_class"] == "LIFT")
        if (s_ == len(stall) and l_ == 0) or (l_ == len(lift) and s_ == 0):
            sep = True
    for k, v in vals.items():
        P("    %-8s: fires %s  (stall %d / lift %d)" % (k, [x["ft"] for x in v],
          sum(1 for x in v if x["era_class"] == "STALL"), sum(1 for x in v if x["era_class"] == "LIFT")))
    P("  %s -> %s" % (name, "SEPARATING" if sep else "not separating"))
    return sep
f1 = face_rows(lambda r: r["cls"], "F1 fire class alt/slot")
f2 = face_rows(lambda r: r["form"], "F2 deadline form (unload/fold/none/other)")
def f3v(r):
    if r["span"] is None: return "entry"
    return "g=1" if r["span"] == 1 else ("tair" if r["span"] == TAIR else "other")
f3 = face_rows(f3v, "F3 stance span {entry,1,tair,other}")
f4 = face_rows(lambda r: "event" if r["ev"] else "clean", "F4 waive/unload/guard census event at the fire tick")
f5 = face_rows(lambda r: "clmp>0" if r["clmp_frac"] > 0 else "clmp=0", "F5 clamp regime CLMP_frac>0")
nsep = sum(1 for x in (f1, f2, f3, f4, f5) if x)
P("SEPARATING FACES: %d of 5" % nsep)

# ---- THE DRIFT TEST (P44_the_drift) ----
P("THE DRIFT TEST (the signed fire-gap series in era order vs the walk's own advance):")
P("  era order e0h: " + " ".join("%+.4f" % r["e0h"] for r in rows))
P("  era order e0k: " + " ".join("%+.4f" % r["e0k"] for r in rows))
P("  era order bx (tick-1, mm): " + " ".join(("%.1f" % (r["bx"] * 1e3)) if r["bx"] is not None else "nan" for r in rows))
def rankdir(series):
    inc = sum(1 for a, b in zip(series, series[1:]) if b > a)
    dec = sum(1 for a, b in zip(series, series[1:]) if b < a)
    return inc, dec, len(series) - 1
ih, ihd, nh = rankdir([r["e0h"] for r in rows])
ik_, ikd, nk = rankdir([r["e0k"] for r in rows])
P("  e0h era-order steps: %d up / %d down of %d;  e0k: %d up / %d down of %d"
  % (ih, ihd, nh, ik_, ikd, nk))
bxv = [r["bx"] for r in rows if r["bx"] is not None]
e0v = [r["e0h"] for r in rows if r["bx"] is not None]
e0kv = [r["e0k"] for r in rows if r["bx"] is not None]
if len(bxv) > 2:
    nb = len(bxv)
    mb = sum(bxv) / nb
    mh = sum(e0v) / nb; mk = sum(e0kv) / nb
    covh = sum((b - mb) * (e - mh) for b, e in zip(bxv, e0v))
    covk = sum((b - mb) * (e - mk) for b, e in zip(bxv, e0kv))
    varb = sum((b - mb) ** 2 for b in bxv)
    slh = covh / varb; slk = covk / varb
    P("  vs cumulative bx: slope(e0h,bx) %+.6f rad/m  slope(e0k,bx) %+.6f rad/m (least-squares, mine-side reading)"
      % (slh, slk))
    res = {}
    for r, b, e, ek in zip([x for x in rows if x["bx"] is not None], bxv, e0v, e0kv):
        res.setdefault(r["era_class"], []).append((e - (mh + slh * (b - mb)), ek - (mk + slk * (b - mb))))
    for c, v in sorted(res.items()):
        hs = [x[0] for x in v]; ks = [x[1] for x in v]
        P("  detrended residual %s: hip %+.4f..%+.4f  knee %+.4f..%+.4f (n=%d)"
          % (c, min(hs), max(hs), min(ks), max(ks), len(v)))
    if "STALL" in res and "LIFT" in res:
        sh = [x[0] for x in res["STALL"]]; lh = [x[0] for x in res["LIFT"]]
        sk = [x[1] for x in res["STALL"]]; lk = [x[1] for x in res["LIFT"]]
        sep_h = (max(sh) < min(lh)) or (max(lh) < min(sh))
        sep_k = (max(sk) < min(lk)) or (max(lk) < min(sk))
        P("  DETRENDED CLASS RANGES disjoint: hip %s (stall %+.4f..%+.4f vs lift %+.4f..%+.4f); knee %s (stall %+.4f..%+.4f vs lift %+.4f..%+.4f)"
          % (sep_h, min(sh), max(sh), min(lh), max(lh), sep_k, min(sk), max(sk), min(lk), max(lk)))

# ---- THE REACHABILITY TEST (P44_the_reachability) ----
P("THE REACHABILITY TEST (the stall fires' stance-side gap trajectories, [dvfk] over (prev_td,ft)):")
LIFT_BAND = max(abs(r["e0h"]) for r in lift)
grow = 0; ntest = 0
for r in stall:
    if r["td_self"] is None:
        P("  stall fire %d leg=%d: entry (no stance interval)" % (r["ft"], r["leg"]))
        continue
    ntest += 1
    traj = [(t, dvfk[t][r["leg"]]["qh"] - dvfk[t][r["leg"]]["ah"],
             dvfk[t][r["leg"]]["qk"] - dvfk[t][r["leg"]]["ak"])
            for t in range(r["td_self"] + 1, r["ft"]) if r["leg"] in dvfk.get(t, {})]
    if not traj:
        P("  stall fire %d leg=%d span=%s: NO [dvfk] stance samples" % (r["ft"], r["leg"], r["span"]))
        continue
    hs = [abs(x[1]) for x in traj]; ks = [abs(x[2]) for x in traj]
    g0 = hs[0] + ks[0]; g1 = hs[-1] + ks[-1]
    grew = g1 >= g0
    grow += 1 if grew else 0
    mono_dec = all(hs[i + 1] <= hs[i] for i in range(len(hs) - 1)) and hs[-1] <= LIFT_BAND
    P("  stall fire %d leg=%d span=%s: |g| hip %.4f->%.4f knee %.4f->%.4f (sum %.4f->%.4f %s); hip min %.4f; monotone-decay-into-lift-band %s"
      % (r["ft"], r["leg"], r["span"], hs[0], hs[-1], ks[0], ks[-1], g0, g1,
         "GREW" if grew else "shrank", min(hs), mono_dec))
P("  stall fires whose stance gap GREW (|g| at f- >= at td+): %d of %d measured" % (grow, ntest))

P("-" * 150)
if nsep > 0:
    P("THE SELECTION RULE (fixed in receipt_wave44.json): VERDICT C-FIREGATE (a machinery-owned clock face separates the")
    P("stall from the lift fires; a law build ONLY on a zero-new-constant clause with the wave-33 pin untouched and BOTH")
    P("dual-gate letters, else NO law and the face recorded).")
else:
    P("THE SELECTION RULE (fixed in receipt_wave44.json): NO face separates -> VERDICT C-LANDING iff the stance-side build /")
    P("preceding-close series predicts the fire gap (the law moves to the LANDING side; no fire-side law bytes); else THE")
    P("RECORD. (the reachability + drift tests above carry the C-LANDING vs THE RECORD read; the amendment never invents).")
out.close()
print("written .tmp/w44_receipt/mine_wave44_out.txt")
