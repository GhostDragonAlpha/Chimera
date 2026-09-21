#!/usr/bin/env python3
"""THE WAVE-45 MINE (declared instrument receipt_wave45.json).
Reads THIS LANE'S INSTRUMENTED TRACE ONLY: .tmp/w45_receipt/instr_tr_stderr.txt
(the [dvfl] band-view plumbing build: stdout 8c537cdb EXACT, plain==trace
byte-equal, refusal 302, ledger 30.970714, 49/173; the trace fence GREEN -- the
base trace 69e1273b [the wave-44 live-plumbing ship trace, [dvfa]+[dvfj]+[dvfk]
counted as base] plus inserted [dvfl] lines only). Parses the LAST walk run
(the wave-39..44 declared convention). [hindstep]/[dvfl] event lines DEDUPED by
full line text.

THE QUESTION (the wave-45 bank): WHAT does the release band's OWN decision view
read at fire+1..fire+9 that a delivering era's does not -- and is there a
ZERO-NEW-CONSTANT clause in the band machinery (the wave-32 due-date/state read
class) that could make a stalling hold deliver?

THE DECISION RULE (fixed in receipt_wave45.json BEFORE the numbers below were
read; restated verbatim): the era convention is receipt_wave41.json's verbatim
as corrected at wave-42/43/44 (event lines deduped by full line text; the era
span [f, ct], ct the fired leg's first td at t >= f or the trace's end; the
[dvfa]/[dvfj]/[dvfk]/[dvfl] FIRST sample per (t,leg) the tick-start basis).
Per fire (ALL 18 eras), on the era leg's own series:
  CMD_peak/DEL_peak (the wave-42/43/44 verbatim; the 8 STALL / 10 LIFT classes
            must reproduce -- DEL < 1.0 mm is STALL, a mine-side threshold read).
  THE [dvfl] BAND VIEW: the held-period series g1/g2/hd/ht/tm per tick
            fire+1..release-or-td (the lines exist ONLY while held; hd=0 marks
            THE CROSSING TICK -- the hold released this tick; tm is the glide
            clock PRE-increment, the td test evaluates tm+1 >= tair);
            THE CROSSING TICK; the binding pad at each tick (heel = g1 < g2,
            MP = g2 <= g1); the held-period max gmin (the R5 graze read);
            maxheld gmax = max over held ticks of max(g1,g2) -- THE LEVER read
            (a pad whose gap left the band while the pair-min pinned it: the
            foot TIPS about the pinned pad); the lever tick (first gmax > edge);
            the first-read values (R2/R3/R4 at f+1); ht at the era's last
            [dvfl] tick.
THE F-G45 CENSUS (frozen faces; a face SEPARATES iff all 8 stall fires lie on
one side and all 10 lift fires on the other):
  (R1) release timing: instant (cross at fire+1) / mid (fire+2..fire+8) / never
       (held to the era td).
  (R2) the first read gmin(f+1) vs the edge: over / in.
  (R3) the first-read binding pad: heel vs MP.
  (R4) the first-read pair split: g1>g2 vs g2>=g1.
  (R5) the graze: maxheld gmin > edge/2 (hovered within 2x of the edge -- a
       MINE-SIDE reading convention, no shipped constant) vs never approached.
THE PAIR-SPLIT TEST (P45_the_pairsplit): in a never-crossed era the lever read
  maxheld gmax > edge while the pair-min never crossed = the foot tipped about
  a pinned pad (the DEL lives in the heel rise the pair-min hid). FALSIFIER:
  (a) a STALL era with maxheld gmax > edge (a hidden lever the DEL missed), or
  (b) a never-crossed LIFT era with maxheld gmax <= edge (DEL without a lever).
THE FIRST-READ TEST (P45_the_firstread): the fire+1 gmin per class; the class
  decision ARRIVES AT THE FIRE iff the never-crossed LIFT eras' first reads or
  first-read splits already differ from the STALL eras' (the lever present at
  the first read); FALSIFIER: overlapping first reads with the lever first
  appearing MID-HOLD (a development the band's own reads expose but never
  decide on).
THE C-CONTACT-POSE CHECK (the frozen rule's branch 2): every STALL era has both
  pads pinned flat (never crossed AND maxheld gmax <= edge) AND every LIFT era
  either crossed or carried the lever (maxheld gmax > edge) -- the class
  decision then arrives IN THE CONTACT STATE the band reads.
THE SELECTION RULE (binding): (1) C-HOLDGATE iff at least one R face separates
AND the face names a constructible zero-new-constant clause in the band
machinery (a due-date/state read on the machinery's own clocks); a law build
ONLY with the wave-33 stand-first pin untouched and BOTH dual-gate letters,
else NO law and the face recorded. (2) else C-CONTACT-POSE iff the C-CONTACT-
POSE check holds -- the record ships, the wave-46 bank names the structural
successor. (3) else THE RECORD. In EVERY verdict the amendment NEVER invents.
Output: mine_wave45_out.txt (this run's preserved output).
"""
import re, collections

TRACE = ".tmp/w45_receipt/instr_tr_stderr.txt"

lines = open(TRACE, encoding="utf-8", errors="replace").read().splitlines()
idx = [i for i, l in enumerate(lines) if l.startswith("WALK REFUSED")]
run = lines[idx[-2] + 1:idx[-1]]
mref = re.match(r"WALK REFUSED tick (\d+): (\S+)", lines[idx[-1]])
refus = (int(mref.group(1)), mref.group(2))

dvfa = collections.defaultdict(dict)   # t -> leg -> (br,held,sg,c,cmd_y,pad_y,plant_y) FIRST sample
dvfj = collections.defaultdict(dict)   # t -> leg -> dict FIRST sample
dvq = collections.defaultdict(dict)    # t -> k -> (tau, cap)
fires = []                             # (t, leg, cls, fy, qerr, dl)
tds = []                               # (t, leg)
dvfl = collections.defaultdict(dict)   # t -> leg -> dict FIRST sample (dedupe = first sample)
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
    m = re.match(r"\[dvfl\] t=(\d+) leg=(\d) g1=(\S+) g2=(\S+) edge=(\S+) hd=(\d) ht=(\d+) tm=(\S+) clr=(-?\d+) oth=(\d) dl=(\d+)", l)
    if m:
        t, leg = int(m.group(1)), int(m.group(2))
        rec = dict(g1=float(m.group(3)), g2=float(m.group(4)), edge=float(m.group(5)),
                   hd=int(m.group(6)), ht=int(m.group(7)), tm=float(m.group(8)),
                   clr=int(m.group(9)), oth=int(m.group(10)), dl=int(m.group(11)))
        if leg not in dvfl[t]: dvfl[t][leg] = rec
        continue
    m = re.match(r"\[dvq\] t=(\d+) k=(\d+) tau=(\S+) cap=(\S+)", l)
    if m:
        dvq[int(m.group(1))][int(m.group(2))] = (float(m.group(3)), float(m.group(4))); continue
    if l.startswith("[hindstep]"):
        if l in seen_ev: continue
        seen_ev.add(l)
        m = re.match(r"\[hindstep\] fire leg=(\d) tick=(\d+) phi=\S+ class=(\S+) from=\((\S+),(\S+)\) to=\((\S+),(\S+)\) xoff=(\S+) v=(\S+) qerr=(\S+) ap=\S+ br=\S+ dl=(\d+)", l)
        if m:
            fires.append((int(m.group(2)), int(m.group(1)), m.group(3),
                          float(m.group(5)), float(m.group(10)), int(m.group(11)))); continue
        m = re.match(r"\[hindstep\] td leg=(\d) tick=(\d+)", l)
        if m: tds.append((int(m.group(2)), int(m.group(1)))); continue

out = open(".tmp/w45_receipt/mine_wave45_out.txt", "w", encoding="utf-8")
def P(*a):
    s = " ".join(str(x) for x in a)
    out.write(s + "\n"); print(s)

P("refusal:", refus, " fires:", len(fires), " tds:", len(tds),
  " dvfl (t,leg) first-sample series:", len(dvfl),
  " dvfa series:", len(dvfa), " dvfj series:", len(dvfj))
P("SAMPLING BASIS: [dvfl] present on at least one held tick (f+1..) for %d/%d fires"
  % (sum(1 for (ft, leg, *_r) in fires if any(leg in dvfl.get(t, {}) for t in range(ft + 1, ft + 12))), len(fires)))
EDGE = None
rows = []
for (ft, leg, cls, fy, qerr, dl) in fires:
    comp = next(((t, l) for (t, l) in tds if l == leg and t >= ft), None)
    ct = comp[0] if comp else max(t for t in dvfj if leg in dvfj[t] and t > ft)
    f0 = dvfj.get(ft, {}).get(leg)
    a0 = dvfa.get(ft, {}).get(leg)
    if f0 is None or a0 is None: continue
    cmd_peak = -1e9; del_peak = -1e9; clmp_n = 0; n = 0
    tauk_f = float("nan"); tauh_f = float("nan")
    kk = dvq.get(ft, {}).get(1 if leg == 0 else 5)
    if kk: tauk_f = kk[0]
    kh = dvq.get(ft, {}).get(0 if leg == 0 else 4)
    if kh: tauh_f = kh[0]
    era_taus = []; era_caps = {}
    for t in range(ft, ct + 1):
        a = dvfa.get(t, {}).get(leg); f = dvfj.get(t, {}).get(leg)
        if a is None or f is None: continue  # the wave-43/44 verbatim: BOTH the tick-start samples required
        n += 1
        cmd_y, pad_y = a[4], a[5]
        cmd_peak = max(cmd_peak, (cmd_y - fy) * 1e3)
        del_peak = max(del_peak, (pad_y - fy) * 1e3)
        clmp_n += 1 if f["clmp"] else 0
        dk2 = range(0, 4) if leg == 0 else range(4, 8)
        for k in dk2:
            q = dvq.get(t, {}).get(k)
            if q is None: continue
            era_taus.append(q[0]); era_caps[k] = q[1]
    # THE [dvfl] BAND VIEW: the held-period series on (ft, ct]
    bser = [dvfl[t][leg] for t in range(ft + 1, ct + 1) if leg in dvfl.get(t, {})]
    cross = next((ft + 1 + i for i, b in enumerate(bser) if b["hd"] == 0), None)
    edge = bser[0]["edge"] if bser else float("nan")
    EDGE = edge
    gmin_series = [min(b["g1"], b["g2"]) for b in bser]
    gmax_series = [max(b["g1"], b["g2"]) for b in bser]
    maxgmin = max(gmin_series) if gmin_series else float("nan")
    maxgmax = max(gmax_series) if gmax_series else float("nan")
    lever_tick = next((ft + 1 + i for i, g in enumerate(gmax_series) if g > edge), None)
    if bser:
        f1 = bser[0]
        r2 = "over" if min(f1["g1"], f1["g2"]) > edge else "in"
        r3 = "heel" if f1["g1"] < f1["g2"] else "MP"
        r4 = "g1>g2" if f1["g1"] > f1["g2"] else "g2>=g1"
        ht_end = bser[-1]["ht"]
    else:
        r2 = r3 = r4 = "NO-BAND-LINES"; ht_end = -1
    r1 = ("instant" if cross == ft + 1 else ("mid" if cross is not None else "never")) if bser else "no-lines"
    r5 = ("hover" if maxgmin > edge / 2 else "never-approach") if bser else "no-lines"
    taumax = max(era_taus) if era_taus else float("nan")
    capmax = max(era_caps.values()) if era_caps else float("nan")
    pinned = (era_taus and era_caps and taumax >= 0.999 * capmax)
    era_class = "STALL" if del_peak < 1.0 else "LIFT"
    rows.append(dict(ft=ft, ct=ct, leg=leg, era_class=era_class, cls=cls,
                     cmd_peak=cmd_peak, del_peak=del_peak, qerr=qerr, dl=dl,
                     nband=len(bser), cross=cross, r1=r1, r2=r2, r3=r3, r4=r4, r5=r5,
                     maxgmin=maxgmin, maxgmax=maxgmax, lever_tick=lever_tick,
                     split1=(bser[0]["g1"] - bser[0]["g2"]) if bser else float("nan"),
                     ht_end=ht_end, clmp_frac=clmp_n / max(n, 1),
                     tauk_f=tauk_f, tauh_f=tauh_f, pinned=pinned))

P("ERA TABLE: fire->ct leg eraClass(fireCls) CMD DEL cross R1 nBand f+1g1/f+1g2 (R2/R3/R4) maxgmin R5 maxgmax leverTick htEnd tauH/tauK@fire PINNED CLMPfrac")
for r in rows:
    b0 = dvfl.get(r["ft"] + 1, {}).get(r["leg"])
    g0 = "%.2e/%.2e" % (b0["g1"], b0["g2"]) if b0 else "none"
    P("  %4d->%4d leg=%d %-5s(%-3s) CMD=%7.3f DEL=%7.3f cross=%4s %-6s nB=%2d %s (%s/%s/%s) maxgmin=%.2e %-14s maxgmax=%.2e lever=%4s ht=%2d tauH=%6.3f tauK=%6.3f %s clmp=%4.2f"
      % (r["ft"], r["ct"], r["leg"], r["era_class"], r["cls"], r["cmd_peak"], r["del_peak"],
         r["cross"] if r["cross"] is not None else "none", r["r1"], r["nband"], g0,
         r["r2"], r["r3"], r["r4"], r["maxgmin"], r["r5"], r["maxgmax"],
         r["lever_tick"] if r["lever_tick"] is not None else "none", r["ht_end"],
         r["tauh_f"], r["tauk_f"], "PINNED" if r["pinned"] else "flows", r["clmp_frac"]))
P("-" * 150)
stall = [r for r in rows if r["era_class"] == "STALL"]
lift = [r for r in rows if r["era_class"] == "LIFT"]
P("ERA CLASSES: %d STALL (fires %s) / %d LIFT (fires %s)"
  % (len(stall), [r["ft"] for r in stall], len(lift), [r["ft"] for r in lift]))
P("THE BAND EDGE (the machinery's own kTouch+kReleaseBand, printed by [dvfl]): %.1e" % EDGE)

# ---- THE F-G45 CENSUS (frozen faces R1..R5) ----
P("THE F-G45 CENSUS (R1..R5, the band's own reads):")
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
        P("    %-14s: fires %s  (stall %d / lift %d)" % (k, [x["ft"] for x in v],
          sum(1 for x in v if x["era_class"] == "STALL"), sum(1 for x in v if x["era_class"] == "LIFT")))
    P("  %s -> %s" % (name, "SEPARATING" if sep else "not separating"))
    return sep
r1 = face_rows(lambda r: r["r1"], "R1 release timing")
r2 = face_rows(lambda r: r["r2"], "R2 first read vs edge")
r3 = face_rows(lambda r: r["r3"], "R3 first-read binding pad")
r4 = face_rows(lambda r: r["r4"], "R4 first-read pair split")
r5 = face_rows(lambda r: r["r5"], "R5 the graze (edge/2)")
nsep = sum(1 for x in (r1, r2, r3, r4, r5) if x)
P("SEPARATING FACES: %d of 5" % nsep)

# ---- THE PAIR-SPLIT TEST (P45_the_pairsplit) ----
P("THE PAIR-SPLIT TEST (the hidden lever: maxheld gmax = max over held ticks of max(g1,g2) vs the edge):")
P("  [INSTRUMENT FINDING, first mine run: g1==g2 to machine precision in EVERY [dvfl] line -- gap_of() is defined on")
P("   the (heel,MP) PAIR and returns min(gh,gm) for BOTH indexes (gait_controller.hpp:612). The band's read site")
P("   structurally erases the heel/MP identity: R3/R4 are degenerate BY CONSTRUCTION, and maxgmax below is the pair-min")
P("   read twice, NOT a heel/MP split. The split is recovered on the declared plumbing's own world heights: THE LEVER")
P("   READ (mine-side derivation, both live-plumbing columns, no new bytes): split(t)-split(fire) =")
P("   2*[(pad_y(t)-pad_y(fire)) - (gmin(t)-gmin(fire))] over the held ticks, split(fire) bounded by the band (~2e-5 m).]")
ps_a = ps_b = 0; nver = 0
for r in rows:
    if r["r1"] != "never":
        continue
    tag = "STALL" if r["era_class"] == "STALL" else "LIFT"
    over = r["maxgmax"] > EDGE
    if r["era_class"] == "STALL" and over: ps_a += 1
    if r["era_class"] == "LIFT" and not over: ps_b += 1
    nver += 1
    # THE LEVER READ: the pair-split delta from the [dvfa] world heights + the [dvfl] pair-min
    fy = dvfa[r["ft"]][r["leg"]][5]
    g0 = min(dvfl[r["ft"] + 1][r["leg"]]["g1"], dvfl[r["ft"] + 1][r["leg"]]["g2"])
    best = -1e9
    for t in range(r["ft"] + 1, r["ct"] + 1):
        a = dvfa.get(t, {}).get(r["leg"]); b = dvfl.get(t, {}).get(r["leg"])
        if a is None or b is None: continue
        gmin = min(b["g1"], b["g2"])
        best = max(best, 2.0 * ((a[5] - fy) - (gmin - g0)))
    P("  never-crossed fire %d leg=%d %s: pair-min maxgmax=%.3e %s the edge; maxgmin=%.3e; LEVER READ split-delta max=%+.3f mm"
      % (r["ft"], r["leg"], tag, r["maxgmax"], "OVER" if over else "under", r["maxgmin"], best * 1e3))
P("  STALL eras with a pad OVER the edge under an in-band pair-min (hidden lever, on the band's own pair-min): %d" % ps_a)
P("  never-crossed LIFT eras flagged flat ON THE BAND'S OWN READ (the pair-min cannot see the lever): %d" % ps_b)
P("  THE LEVER READ (the declared recovery): never-crossed LIFT eras carry split-delta %s mm; never-crossed STALL eras %s mm"
  % ([round(2.0 * 1e3 * max((dvfa[t][r["leg"]][5] - dvfa[r["ft"]][r["leg"]][5]) for t in range(r["ft"] + 1, r["ct"] + 1) if t in dvfa and r["leg"] in dvfa[t]), 3)
      for r in rows if r["r1"] == "never" and r["era_class"] == "LIFT"],
     [round(2.0 * 1e3 * max((dvfa[t][r["leg"]][5] - dvfa[r["ft"]][r["leg"]][5]) for t in range(r["ft"] + 1, r["ct"] + 1) if t in dvfa and r["leg"] in dvfa[t]), 3)
      for r in rows if r["r1"] == "never" and r["era_class"] == "STALL"]))

# ---- THE FIRST-READ TEST (P45_the_firstread) ----
P("THE FIRST-READ TEST (fire+1: the band's first read of the anchor pose):")
for tag, grp in (("STALL", stall), ("LIFT", lift)):
    vals = [(r["ft"], dvfl[r["ft"] + 1][r["leg"]]["g1"], dvfl[r["ft"] + 1][r["leg"]]["g2"],
             dvfl[r["ft"] + 1][r["leg"]]["hd"]) for r in grp if dvfl.get(r["ft"] + 1, {}).get(r["leg"])]
    if vals:
        P("  %s fire+1 gmin range: %.3e .. %.3e (n=%d)" % (tag, min(min(a, b) for _, a, b, _ in vals),
          max(min(a, b) for _, a, b, _ in vals), len(vals)))
lever_at_first = [r["ft"] for r in rows if r["lever_tick"] == r["ft"] + 1 and r["r1"] == "never"]
lever_mid = [r["ft"] for r in rows if r["lever_tick"] is not None and r["lever_tick"] > r["ft"] + 1 and r["r1"] == "never"]
P("  never-crossed eras with the lever ALREADY OVER the edge at fire+1: %s" % (lever_at_first or "none"))
P("  never-crossed eras with the lever crossing MID-HOLD (fire+2..): %s" % (lever_mid or "none"))
P("  THE SPLIT's own clock (the lever read per tick -- WHERE the split opens on the band's own window):")
for r in rows:
    if r["r1"] != "never": continue
    fy = dvfa[r["ft"]][r["leg"]][5]
    g0 = min(dvfl[r["ft"] + 1][r["leg"]]["g1"], dvfl[r["ft"] + 1][r["leg"]]["g2"])
    ser = []
    for t in range(r["ft"] + 1, r["ct"] + 1):
        a = dvfa.get(t, {}).get(r["leg"]); b = dvfl.get(t, {}).get(r["leg"])
        if a is None or b is None: continue
        ser.append((t, 2.0 * ((a[5] - fy) - (min(b["g1"], b["g2"]) - g0)) * 1e3))
    if ser:
        P("    fire %d %s: split-delta mm %s" % (r["ft"], "STALL" if r["era_class"] == "STALL" else "LIFT",
          " ".join("%+.2f" % v for _, v in ser)))

# ---- THE C-CONTACT-POSE CHECK (the frozen rule's branch 2) ----
stall_flat = all(r["r1"] == "never" and r["maxgmax"] <= EDGE for r in stall)
lift_carries = all((r["cross"] is not None) or (r["maxgmax"] > EDGE) for r in lift)
P("THE C-CONTACT-POSE CHECK (on the band's OWN reads -- the only state the band machinery can act on):")
P("  every STALL era both-pads-pinned flat ON THE PAIR-MIN: %s; every LIFT era crossed or pair-min-over-edge: %s"
  % (stall_flat, lift_carries))
P("  (the lever lives in the pad WORLD HEIGHTS the pair-min erases: the never-crossed LIFT eras' pair-min reads are")
P("   indistinguishable from the STALL eras' [all in-band, hover] -- the class signal is ABSENT from the band's read.)")

P("-" * 150)
if nsep > 0:
    P("THE SELECTION RULE (fixed in receipt_wave45.json): at least one R face separates -> VERDICT C-HOLDGATE only if")
    P("the face names a constructible ZERO-NEW-CONSTANT clause in the band machinery (the wave-32 due-date/state read")
    P("class); a law build ONLY with the wave-33 pin untouched and BOTH dual-gate letters, else NO law and the face recorded.")
else:
    P("THE SELECTION RULE (fixed in receipt_wave45.json): NO R face separates -> VERDICT C-CONTACT-POSE iff the")
    P("C-CONTACT-POSE check holds (the class decision arrives IN the contact state the band reads; the record ships and")
    P("the wave-46 bank names the structural successor); else THE RECORD. (the amendment never invents).")
out.close()
print("written .tmp/w45_receipt/mine_wave45_out.txt")
