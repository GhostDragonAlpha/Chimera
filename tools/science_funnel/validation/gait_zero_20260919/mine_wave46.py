#!/usr/bin/env python3
"""THE WAVE-46 MINE (declared instrument receipt_wave46.json, committed BEFORE
this run). Reads THIS LANE'S SHIP TRACE ONLY: .tmp/w46_receipt/base_tr_stderr.txt
(the b1ea6717 reproduction trace: stdout 8c537cdb EXACT, plain==trace byte-equal,
refusal 302, ledger 30.970714, 49/173; the trace c6f9b6c0 = the 69e1273b wave-44
base + 452 [dvfl] lines, fenced GREEN). Parses the LAST walk run (the wave-39..45
declared convention). [hindstep]/[dvfl] event lines DEDUPED by full line text.

THE QUESTION (the wave-45 bank): does a DERIVATION exist for un-minning the
touch law's pair read -- and does the split-read release clause open?

THE ABSOLUTE-SPLIT CALIBRATION (declared in receipt_wave46.json BEFORE this
run): plane_model_y_ = contact_plane_height_m = 0.004 m (the GaitWalker
construction shift is V{0,0,0} at EVERY site in gait_unit.cpp) and the heel/MP
pad radius = 0.004 m (the recipe's contact points; [dvfa]'s own c=2r field
verifies), so the mean pad gap (gh+gm)/2 = pad_y + radius - plane_model_y_ =
pad_y EXACTLY, and with gmin = the [dvfl] pair-min:
    split_abs(t)  = |gh-gm|   = 2*(pad_y(t) - gmin(t))
    maxpad(t)     = max(gh,gm) = 2*pad_y(t) - gmin(t)
The [dvfa]/[dvfl] FIRST sample per (t,leg) is the tick-start basis (the
wave-41..45 convention); the era span [f, ct], ct the fired leg's first td at
t >= f or the trace's end.

OUTPUTS:
  THE CALIBRATION CROSS-CHECK: the wave-45-verbatim lever-read delta (from the
  fire pad_y and the fire+1 gmin) must reproduce mine_wave45_out.txt's printed
  split-delta maxima era for era.
  THE FLIP CENSUS: per era, the first held tick where maxpad > edge (the law's
  release decision) vs the baseline crossing (hd=0) -- the law diverges from
  the ship bytes exactly where the flip precedes the baseline crossing.
  F = the first such divergence tick.
  The heel/MP identity per tick is NOT recoverable from (mean, min) alone and
  is reported as such: the registered max-clause is identity-agnostic.
Output: mine_wave46_out.txt (this run's preserved output).
"""
import re, collections, os

TRACE = ".tmp/w46_receipt/base_tr_stderr.txt"
W45_OUT = "tools/science_funnel/validation/gait_zero_20260919/mine_wave45_out.txt"

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

out = open(".tmp/w46_receipt/mine_wave46_out.txt", "w", encoding="utf-8")
def P(*a):
    s = " ".join(str(x) for x in a)
    out.write(s + "\n"); print(s)

P("refusal:", refus, " fires:", len(fires), " tds:", len(tds),
  " dvfl (t,leg) first-sample series:", len(dvfl), " dvfa series:", len(dvfa))

EDGE = None
rows = []
for (ft, leg, cls, fy, qerr, dl) in fires:
    comp = next(((t, l) for (t, l) in tds if l == leg and t >= ft), None)
    ct = comp[0] if comp else max(t for t in dvfa if leg in dvfa[t] and t > ft)
    a0 = dvfa.get(ft, {}).get(leg)
    if a0 is None: continue
    era_class = None  # filled from the DEL convention after the series walk
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
    edge = bser[0]["edge"] if bser else float("nan")
    EDGE = edge
    gmin_series = [min(b["g1"], b["g2"]) for b in bser]
    maxgmin = max(gmin_series) if gmin_series else float("nan")
    # THE ABSOLUTE SPLIT (the declared calibration)
    ser = []  # (t, gmin, pad_y, split_abs, maxpad)
    for t in range(ft + 1, ct + 1):
        a = dvfa.get(t, {}).get(leg); b = dvfl.get(t, {}).get(leg)
        if a is None or b is None: continue
        gmin = min(b["g1"], b["g2"]); py = a[5]
        ser.append((t, gmin, py, 2.0 * (py - gmin), 2.0 * py - gmin))
    flip = next((t for (t, g, py, sp, mp) in ser if mp > edge), None)
    r1 = ("instant" if cross == ft + 1 else ("mid" if cross is not None else "never")) if bser else "no-lines"
    # THE WAVE-45-VERBATIM LEVER DELTA (the cross-check series, from the fire)
    fy_pad = dvfa[ft][leg][5]
    g0 = min(dvfl[ft + 1][leg]["g1"], dvfl[ft + 1][leg]["g2"]) if dvfl.get(ft + 1, {}).get(leg) else float("nan")
    w45_max = -1e9
    for t in range(ft + 1, ct + 1):
        a = dvfa.get(t, {}).get(leg); b = dvfl.get(t, {}).get(leg)
        if a is None or b is None: continue
        w45_max = max(w45_max, 2.0 * ((a[5] - fy_pad) - (min(b["g1"], b["g2"]) - g0)))
    rows.append(dict(ft=ft, ct=ct, leg=leg, era_class=era_class, cls=cls,
                     cmd_peak=cmd_peak, del_peak=del_peak, nband=len(bser),
                     cross=cross, r1=r1, maxgmin=maxgmin, edge=edge,
                     ser=ser, flip=flip, w45_max=w45_max))

P("THE ABSOLUTE-SPLIT CALIBRATION (declared): plane_model_y_=0.004 (shift V{0,0,0}), pad radius=0.004 =>"
  " mean_gap=pad_y, split_abs=2*(pad_y-gmin), maxpad=2*pad_y-gmin; the heel/MP identity per tick is NOT")
P("  recoverable from (mean,min) alone -- the registered max-clause is identity-agnostic (reported honestly).")
P("THE BAND EDGE (the machinery's own kTouch+kReleaseBand, printed by [dvfl]): %.1e" % EDGE)
P("-" * 150)
P("ERA TABLE: fire->ct leg eraClass(fireCls) CMD DEL R1 nBand cross(flip) maxpad>edge FLIP maxgmin maxsplit_abs")
fliprows = []
for r in rows:
    maxsplit = max((s[3] for s in r["ser"]), default=float("nan"))
    P("  %4d->%4d leg=%d %-5s(%-3s) CMD=%7.3f DEL=%7.3f %-6s nB=%2d cross=%4s FLIP=%4s %s maxgmin=%.2e maxsplit=%+.4f mm"
      % (r["ft"], r["ct"], r["leg"], r["era_class"], r["cls"], r["cmd_peak"], r["del_peak"],
         r["r1"], r["nband"], r["cross"] if r["cross"] is not None else "none",
         r["flip"] if r["flip"] is not None else "none",
         "SAME-TICK" if (r["flip"] is not None and r["cross"] == r["flip"]) else
         ("DIVERGES" if r["flip"] is not None else "no-flip"),
         r["maxgmin"], maxsplit * 1e3))
    if r["flip"] is not None and (r["cross"] is None or r["flip"] < r["cross"]):
        fliprows.append((r["flip"], r["ft"], r["leg"], r["era_class"]))
P("-" * 150)
P("THE CALIBRATION CROSS-CHECK (my wave-45-verbatim lever delta vs mine_wave45_out.txt's printed maxima):")
w45 = {161: -3.142, 175: -0.003, 184: 0.151, 193: -0.497, 220: 6.902, 229: 9.125,
       238: 7.476, 247: 11.577, 256: 0.468, 265: 16.426, 291: -6.416, 300: 0.551}
ok = True
for r in rows:
    if r["ft"] in w45:
        got = r["w45_max"] * 1e3
        match = abs(got - w45[r["ft"]]) <= 0.001 + 1e-9
        ok = ok and match
        P("  fire %d %s: mine=%+.3f mm  wave45=%+.3f mm  %s"
          % (r["ft"], r["era_class"], got, w45[r["ft"]], "MATCH" if match else "MISMATCH"))
P("  CROSS-CHECK: %s" % ("GREEN (all 12 never-crossed eras match to the printed precision)" if ok else "FIRED"))
P("-" * 150)
P("THE FLIP CENSUS (the law's release decision max(gh,gm) > edge, per era, first held tick):")
for r in rows:
    ser_s = " ".join("%d:%s" % (t, ("%+.4f" % (mp * 1e3))) for (t, g, py, sp, mp) in r["ser"])
    P("  fire %d %s maxpad mm/tick: %s" % (r["ft"], r["era_class"], ser_s))
P("-" * 150)
if fliprows:
    fliprows.sort()
    F = fliprows[0][0]
    P("THE FIRST DIVERGENCE: F = %d (era fire %d leg %d %s)" % (F, fliprows[0][1], fliprows[0][2], fliprows[0][3]))
    P("DIVERGENCE TICKS (law flip < baseline crossing): %s" % [(f, e) for (f, e, l, c) in fliprows])
    lift_flip_ok = all(r["flip"] is not None and r["flip"] <= r["ft"] + 2 for r in rows if r["era_class"] == "LIFT")
    P("SELECTION (receipt_wave46.json): lineage DERIVED (receipt L1/L2/L3) + every LIFT era flips within 2 held ticks: %s + F=%d < 302: %s"
      % (lift_flip_ok, F, F < 302))
    P("VERDICT: %s" % ("C-SPLITLAW (the amendment freezes clause+F+census; the law builds, dual-gated)" if (lift_flip_ok and F < 302) else "THE RECORD"))
else:
    P("NO FLIP ANYWHERE -- VERDICT: THE RECORD (the clause never engages inside the ship walk)")
P("  per-era first-held-tick maxpad (the fire+1 face): %s"
  % {r["ft"]: (("%.4f mm" % (r["ser"][0][4] * 1e3)) if r["ser"] else "none") for r in rows})
out.close()
print("written .tmp/w46_receipt/mine_wave46_out.txt")
