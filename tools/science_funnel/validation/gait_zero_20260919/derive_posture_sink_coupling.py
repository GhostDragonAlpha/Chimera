"""THE WAVE-27b POSTURE/SINK COUPLING DERIVATION (candidate (b), the racing lane
agent/gait-wave27b-posture-sink at 6efb3ef0).

Question (the wave-26 bank, candidate (b) only): does the posture target's slow
trajectory (the theta*(phi) trunk-vault table at the walk phases) own the sinking
shoulder -- i.e., does a feed-forward posture compensation derived from the load
book (a table/target law change, NEVER a gain change) have the authority to hold
the shoulder up?

Method (all numbers from the byte-reproduced 6efb3ef0 baseline; the runs live in
.tmp/runs/, the traces mined tick by tick through [60,105]):

  1. THE EXACT KINEMATICS from the scene's own model tree: the fore shoulders
     mount on the PELVIS at local (+0.2689, -0.1331, +/-0.02) m; the posture
     drive IS base_rot_z (coordinate 2, about the pelvis origin).  Therefore
        sh_y = base_y + 0.2689*sin(theta) - 0.1331*cos(theta)   (theta = pang)
     and the LEVER dsh_y/dtheta = 0.2689*cos(theta) + 0.1331*sin(theta).
     The shoulder height is a function of exactly TWO arguments: the free base
     height base_trans_y (UNDRIVEN -- gravity and contact only) and the pitch.

  2. THE DECOMPOSITION dsh_y = dbase_y + d(pitch term), closed against the
     measured base_y (the [body] 10-tick marks) and the measured pang ([dv]).

  3. THE COMMAND CHANNEL: lever x (dtheta_actual/dtheta*) x dtheta* -- the
     posture-command-attributable shoulder motion -- against the measured sink.

  4. THE INTERVENTIONS (the causal seal):
       - blunt: strip recipe.trunk_vault_rad (the documented absent-key path).
         VOID: the ENTRY consumes the table (the reset's v[2] injection reads
         nodes 1/19 through the phase wrap; the settle's amp ramp consumes node
         0) -- the run refuses at tick 40, the window is never reached.
       - refined: freeze nodes 3..18 at node 3's value (+0.0171 rad), keep the
         entry-consuming nodes 0,1,2,19,20 byte-exact.  [0,90] stays
         line-identical; the walk-window command climb (+0.178 rad through
         [88,104]) is removed; the frozen receipt's retraction criterion
         (sink <= 0.5 mm/tick on either leg RETRACTS) is applied unchanged.

Verdict (measured, see receipt_wave27b.json): the coupling is FALSIFIED and the
negative is SEALED -- the refined intervention's dynamics are BYTE-IDENTICAL to
the baseline (an 8.57-degree command change, 0.000 mm of dynamics change; the
posture torque railed at the law cap in both runs), and the passive
decomposition had already bounded the command channel at +3.3% of the sink,
wrong sign.  The sink is the BASE height -- the hind chain's loaded fold.

Usage:  python derive_posture_sink_coupling.py <baseline_trace.err> <flatwalk_trace.err>
Writes: mined_posture_sink_coupling.json next to this script.
"""
import json, math, re, sys
from pathlib import Path

A_SH, B_SH = 0.2689, -0.1331  # the pelvis-local shoulder mount (m), from the scene model tree

DV = re.compile(r"\[dv\] t=(\d+) ptq=([-\d.]+) ptgt=([-\d.]+) pang=([-\d.]+) pspd=([-\d.]+)"
                r" ev=(\d+) phL=([-\d.]+) phR=([-\d.]+) com=\(([-\d.e]+),([-\d.e]+)\)"
                r" hull=(\d+) in=(\d+) bx=([-\d.]+)")
DVF = re.compile(r"\[dvf\] t=(\d+) leg=(\d) mode=(\d) tgt=\(([-\d.]+),([-\d.]+)\)"
                 r" sh=\(([-\d.]+),([-\d.]+)\) D=([-\d.]+) off=([+-][\d.]+) hr=([-\d.]+)")
BODY = re.compile(r"\[body\] tick=(\d+) x=([-\d.]+) y=([-\d.]+)")


def mine(path):
    dv, dvf, body = {}, {}, {}
    with open(path) as f:
        for line in f:
            m = DV.match(line)
            if m:
                dv[int(m.group(1))] = dict(ptq=float(m.group(2)), ptgt=float(m.group(3)),
                                           pang=float(m.group(4)), phL=float(m.group(7)))
                continue
            m = DVF.match(line)
            if m:
                dvf.setdefault(int(m.group(1)), {})[int(m.group(2))] = float(m.group(7))
                continue
            m = BODY.match(line)
            if m:
                body[int(m.group(1))] = (float(m.group(2)), float(m.group(3)))
    return dv, dvf, body


def pitch_term(theta_deg):
    t = math.radians(theta_deg)
    return A_SH * math.sin(t) + B_SH * math.cos(t)


def lever(theta_deg):
    t = math.radians(theta_deg)
    # d/dtheta [A*sin + B*cos] = A*cos - B*sin ; with B = -0.1331 this is
    # 0.2689*cos + 0.1331*sin = +0.2520 m/rad at the sink-window pitch.
    return A_SH * math.cos(t) - B_SH * math.sin(t)


def main():
    base_trace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".tmp/runs/baseline_trace.err")
    flat_trace = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(".tmp/runs/flatwalk_trace.err")
    bdv, bdvf, bbody = mine(base_trace)
    fdv, fdvf, fbody = mine(flat_trace)
    out = {"lever_m_per_rad": {str(t): round(lever(bdv[t]["pang"]), 6) for t in (60, 88, 96, 104)},
           "baseline": {}, "intervention_flatwalk": {}, "verdict": {}}

    # the empirical lever check: sh_y - base_y vs the closed form
    check = {}
    for t in sorted(bbody):
        if 50 <= t <= 100:
            pred = pitch_term(bdv[t]["pang"])
            meas = bdvf[t][1] - bbody[t][1]
            check[str(t)] = {"measured_m": round(meas, 6), "formula_m": round(pred, 6),
                             "residual_mm": round(1000 * (meas - pred), 4)}
    out["empirical_lever_check"] = check

    for name, dv, dvf, body in (("baseline", bdv, bdvf, bbody), ("intervention_flatwalk", fdv, fdvf, fbody)):
        blk = {}
        for leg in (0, 1):
            for (a, b) in ((60, 104), (88, 104), (91, 104)):
                s = [dvf[t][leg] for t in range(a, b + 1)]
                blk[f"shy_sink_mm_per_tick_leg{leg}_{a}_{b}"] = round(1000 * (s[-1] - s[0]) / (b - a), 5)
        blk["pang_deg_60_104"] = [dv[60]["pang"], dv[104]["pang"]]
        blk["ptgt_deg_88_104"] = [dv[88]["ptgt"], dv[104]["ptgt"]]
        blk["posture_term_delta_mm_60_104"] = round(1000 * (pitch_term(dv[104]["pang"]) - pitch_term(dv[60]["pang"])), 4)
        blk["posture_term_delta_mm_88_104"] = round(1000 * (pitch_term(dv[104]["pang"]) - pitch_term(dv[88]["pang"])), 4)
        blk["base_y"] = {str(t): body[t][1] for t in sorted(body)}
        out[name] = blk

    # the decomposition and the command channel (baseline)
    shy0, shy1 = bdvf[60][1], bdvf[104][1]
    slope = (bbody[100][1] - bbody[90][1]) / 10.0
    base104 = bbody[100][1] + 4 * slope
    dbase = 1000 * (base104 - bbody[60][1])
    dpost = 1000 * (pitch_term(bdv[104]["pang"]) - pitch_term(bdv[60]["pang"]))
    dshy = 1000 * (shy1 - shy0)
    out["verdict"] = {
        "whole_window_60_104": {"d_shy_mm": round(dshy, 3), "d_base_mm_extrapolated": round(dbase, 3),
                                "d_posture_mm": round(dpost, 3),
                                "closure_residual_mm": round(dshy - dbase - dpost, 3)},
        "tracking_gain_88_104": round(math.radians(bdv[104]["pang"] - bdv[88]["pang"]) /
                                      math.radians(bdv[104]["ptgt"] - bdv[88]["ptgt"]), 5),
        "command_attributable_mm_88_104": round(1000 * lever(bdv[88]["pang"]) *
                                                math.radians(bdv[104]["pang"] - bdv[88]["pang"]), 4),
        "intervention_shoulder_bit_identical": all(abs(fdvf[t][l] - bdvf[t][l]) < 1e-12
                                                   for t in range(60, 105) for l in (0, 1)),
    }
    dst = Path(__file__).resolve().parent / "mined_posture_sink_coupling.json"
    dst.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out["verdict"], indent=1))
    print("mined numbers written:", dst)


if __name__ == "__main__":
    main()
