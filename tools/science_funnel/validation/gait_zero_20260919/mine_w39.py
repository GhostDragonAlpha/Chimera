"""THE WAVE-39 MINE (declared instrument; decision rule fixed in this header
BEFORE the numbers below the rule are read).

DECISION RULE (fixed before measurement). The 302 death's owner is whichever
candidate's SIGNATURE the traces show ENGAGING in the death window:
  (A) HAUL-STARVED CORRECTIONS: the sink (the poscorr blowup) tracks the
      twelfth-era replants' under-delivery -- the fire from/to hauls drift
      monotonically short across the walk's replants, and the death-window
      penetration is owned by a replant landed short (the plant geometry
      drift, the stance pad carried behind its designed position).
  (B) RE-ARM-STARVED ALTERNATION: the sink tracks the CARRIER's continuous
      duty age -- a leg bearing load without its own era change past the
      mined pin life (9-10 ticks), forced by the guard holding the waive
      closed (the alternation starved), the stance sinking under the carried
      share; the penetrating points belong to the CARRIER leg's stance pads
      DURING the other's swing.
The rule reads three declared traces on the SAME harness:
  T1 = the wave-38 guarded reproduction (this lane's base_tr_stderr.txt,
       refusal 302),
  T2 = the wave-37 composed reconstruction (w37comp_tr_stderr.txt, refusal
       304, guard-free -- the control that separates the guard's effect),
  T3 = the wave-37 ship state (the parent lane's base_stderr.txt, refusal
       295, no waive gate at all -- the shipped strand).
For each: the era table (fire/td/length per leg, from/to hauls), the poscorr
per-tick profile (count, max dq, sum du, the worst penetrating point), the
death window's event sequence. Whichever signature (A) or (B) the traces show
in the ticks immediately preceding each walk's refusal names the owner; if
BOTH signatures are absent in the pre-death window, the mine reports the
window's own face and the owner is neither.
Output: mine_w39_out.txt (this run's preserved output).
"""
import re, sys, collections

def parse(path):
    # the trace binaries concatenate 4 identical suite runs; parse the LAST
    # block only (the run the stdout corresponds to).
    all_lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    idx = [i for i, l in enumerate(all_lines) if l.startswith('WALK REFUSED')]
    if len(idx) >= 2:
        all_lines = all_lines[idx[-2] + 1:idx[-1]]
    eras = []            # (leg, fire_tick, td_tick, length, frm, to, haul_m, cls)
    fires = {}           # leg -> last fire tick
    holdret = []         # (leg, tick, t, pairmin)
    guard = []           # (leg, tick, dl, link_td, link_fire)
    waive = []           # (leg, tick, dl)
    unload = []          # (leg, tick, dl)
    stand = []           # (leg, tick, stall_other)
    posc = collections.defaultdict(lambda: [0, 0.0, 0.0])  # tick -> [n, maxdq, sumdu]
    pts = {}             # (tick) -> list of (name, gap)
    refus = None
    lastfire = {0: None, 1: None}
    for ln in all_lines:
        m = re.match(r"\[hindstep\] fire leg=(\d) tick=(\d+) phi=\S+ class=(\S+) from=\((\S+),(\S+)\) to=\((\S+),(\S+)\)", ln)
        if m:
            leg = int(m.group(1)); t = int(m.group(2)); cls = m.group(3)
            frm = (float(m.group(4)), float(m.group(5))); to = (float(m.group(6)), float(m.group(7)))
            lastfire[leg] = t
            fires[t] = (leg, cls, frm, to)
            continue
        m = re.match(r"\[hindstep\] td leg=(\d) tick=(\d+) tds=(\d+)", ln)
        if m:
            leg = int(m.group(1)); t = int(m.group(2))
            f = lastfire[leg]
            if f is not None:
                fr = fires[f]
                eras.append((leg, f, t, t - f, fr[2], fr[3], (fr[3][0] - fr[2][0]), fr[1]))
            continue
        m = re.match(r"\[hindstep\] holdreturn leg=(\d) tick=(\d+) t=(-?\d+) pairmin=(\S+)", ln)
        if m:
            holdret.append((int(m.group(1)), int(m.group(2)), int(m.group(3)), float(m.group(4)))); continue
        m = re.match(r"\[hindstep\] guardblock leg=(\d) tick=(\d+) dl=(\d+) link_td=(\d+) link_fire=(\d+)", ln)
        if m:
            guard.append((int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)))); continue
        m = re.match(r"\[hindstep\] waivefire leg=(\d) tick=(\d+) dl=(\d+)", ln)
        if m:
            waive.append((int(m.group(1)), int(m.group(2)), int(m.group(3)))); continue
        m = re.match(r"\[hindstep\] unloadgate leg=(\d) tick=(\d+) dl=(\d+) class=(\S+)", ln)
        if m:
            unload.append((int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4))); continue
        m = re.match(r"\[hindstep\] standhold leg=(\d) tick=(\d+) swing_stall=(\d+)", ln)
        if m:
            stand.append((int(m.group(1)), int(m.group(2)), int(m.group(3)))); continue
        m = re.match(r"\[poscorr\] tick=(\d+) points=(\d+) dq_max=(\S+) du=(\S+)", ln)
        if m:
            t = int(m.group(1)); e = posc[t]
            e[0] += 1; e[1] = max(e[1], float(m.group(3))); e[2] += float(m.group(4)); continue
        m = re.match(r"\[poscorr-pt\] tick=(\d+) pt=(\S+) gap=(\S+)", ln)
        if m:
            pts.setdefault(int(m.group(1)), []).append((m.group(2), float(m.group(3)))); continue
        m = re.match(r"WALK REFUSED tick (\d+): (\S+)", ln)
        if m:
            refus = (int(m.group(1)), m.group(2)); continue
    return dict(eras=eras, holdret=holdret, guard=guard, waive=waive,
                unload=unload, stand=stand, posc=posc, pts=pts, refus=refus)

def posc_profile(d, lo, hi):
    rows = []
    for t in sorted(d["posc"]):
        if lo <= t <= hi:
            n, mx, du = d["posc"][t]
            worst = max(d["pts"].get(t, []), key=lambda p: -p[1], default=("none", 0.0))
            worst = min(((n2, g) for n2, g in d["pts"].get(t, [])), key=lambda p: p[1], default=("none", 0.0))
            rows.append((t, n, mx, du, worst[0], worst[1]))
    return rows

def eras_str(d, lo, hi):
    return [(e[0], e[1], e[2], e[3], e[7], "%.4f" % e[6]) for e in d["eras"] if lo <= e[1] <= hi]

TRACES = [
    ("T1_guarded302", ".tmp/w39_receipt/base_tr_stderr.txt"),
    ("T2_composed304", None),  # filled from w38 lane's preserved composed trace
    ("T3_ship295", None),      # filled from w38 lane's preserved base (the wave-37 ship) trace
]
import os
TRACES[1] = ("T2_composed304", r"E:/ChimeraWork/w38-agent/.tmp/w38_receipt/w37comp_tr_stderr.txt")
TRACES[2] = ("T3_ship295", r"E:/ChimeraWork/w38-agent/.tmp/w38_receipt/base_stderr.txt")

out = open(".tmp/w39_receipt/mine_w39_out.txt", "w", encoding="utf-8")
def P(*a):
    s = " ".join(str(x) for x in a)
    out.write(s + "\n"); print(s)

for name, path in TRACES:
    d = parse(path)
    P("=" * 100)
    P("TRACE", name, path)
    P("refusal:", d["refus"])
    P("-- era table from tick 240 (leg, fire, td, len, class, haul_x_m):")
    for e in eras_str(d, 240, 10**6):
        P("   ", e)
    P("-- poscorr profile, the death window (tick n maxdq sumdu worst_pt gap):")
    death = d["refus"][0] if d["refus"] else 0
    for r in posc_profile(d, death - 12, death):
        P("   ", r)
    P("-- poscorr: ticks with NO events in [death-16, death):",
      [t for t in range(death - 16, death) if t not in d["posc"]])
    P("-- guard blocks by (leg,tick):", d["guard"])
    P("-- waive fires:", d["waive"])
    P("-- unloadgates:", d["unload"])
    P("-- standholds:", d["stand"])
    P("-- holdreturns:", d["holdret"])
    P("-- continuous duty at the death window: for each leg the tick span since")
    P("   its last era CHANGE (fire or td) before the sink onset:")
    sink = min((t for t in d["posc"] if t >= death - 8), default=death)
    P("   sink onset tick (first poscorr in [death-8,death)):", sink)
    for leg in (0, 1):
        chg = [e[1] for e in d["eras"] if e[0] == leg and e[1] <= sink] + \
              [e[2] for e in d["eras"] if e[0] == leg and e[2] <= sink]
        last_chg = max(chg) if chg else None
        P("    leg=%d last era-change tick before sink=%s sink-last=%s" %
          (leg, last_chg, (sink - last_chg) if last_chg else None))
out.close()
print("written .tmp/w39_receipt/mine_w39_out.txt")
