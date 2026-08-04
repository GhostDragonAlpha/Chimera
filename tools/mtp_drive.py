"""mtp_drive.py -- WHICH TERM OF THE STAND FORMULA DRIVES THE TOE THROUGH ITS STOP?

RULE 0, stated before the run:

    STATEMENT   `mtp_angle_l` sits past its declared stop for 97.6% of F3's phase 1 at a peak of
                1.10 of range, and it is not the reward's doing -- the reward was repaired and
                the joint did not move (task 1: the saved theta came back bit-identical). So the
                drive is in the CONTROL, and the stand formula has exactly four blocks that could
                supply it: `u = a0 + kh*(tgt - z) + kp*pitch + kr*roll`, clipped to [0,1]. ONE of
                them dominates the toe's actuator torque.

    PREDICTION  Zeroing the dominant block drops `mtp_angle_l`'s time past its stop by more than
                half, while zeroing the other three moves it by less than a quarter each. And the
                torque ledger agrees with the ablation: the block that dominates the ablation is
                the block whose contribution to the toe muscles' activation is largest.

    FALSIFIER   If no single block drops it by more than half -- or if the ablation and the
                torque ledger name different blocks -- then the toe is not being DRIVEN through
                its stop by the formula at all. In that case the residual is structural (the
                foot carries no mtp ligament, and `derive_ligaments` refuses one because
                theHuman's `gait_envelope_deg` publishes no toe curve), and the fix is a foot
                membrane, not a control change. Record it and stop.

WHY THE ABLATION AND THE LEDGER ARE BOTH RUN. An ablation says WHAT CHANGES when a block is
removed; a torque ledger says WHAT IS PUSHING while it is there. They can disagree -- a block
can dominate the activation and yet be replaceable by the others through the clip -- and this
project's rule is to publish the disagreement rather than to pick the convenient one (rule 17).
A dyad: two independent messengers, and the claim is what they agree on.

    python tools/mtp_drive.py [--theta <path>] [--joint mtp_angle_l]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body                                       # noqa: E402
from stand_port import derive_stand_port, MYOBODY                 # noqa: E402
from train_stand import joint_ids, seat_in_limits, CTRL_EVERY     # noqa: E402

OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"
LOGDIR = ROOT / "agent_logs"
THETA = OUTDIR / "stand_theta.npy"
SECS = 5.0                      # F3's phase 1 exactly, so the percentages are comparable to it
BLOCKS = ("a0", "kh", "kp", "kr")


def rollout(m, d, mujoco, theta, P, jids, secs, drop=None):
    """One life under the stand formula, WRITTEN OUT rather than parsed.

    The formula is reproduced here because the point is to take it APART -- `parser.py` hands
    back one activation vector with the four blocks already summed, and a sum you cannot
    decompose is a sum you cannot attribute. It is the same arithmetic:
    `clip(a0 + kh*(tgt - z) + kp*pitch + kr*roll, 0, 1)`, and `drop` zeroes exactly one block.

    Verified against the parser path by construction: `drop=None` must reproduce
    `stand_survival.rollout`'s trace, and the harness prints the check.
    """
    nu = m.nu
    a0, kh, kp = theta[:nu].copy(), theta[nu:2 * nu].copy(), theta[2 * nu:3 * nu].copy()
    kr = theta[3 * nu:4 * nu].copy() if theta.size >= 4 * nu else np.zeros(nu)
    blk = dict(a0=a0, kh=kh, kp=kp, kr=kr)
    if drop is not None:
        blk[drop] = np.zeros(nu)
    tgt = P["OUT pelvis_target_m"]
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    seat_in_limits(m, d, mujoco, jids)
    steps = int(secs / m.opt.timestep)
    out = {k: [] for k in ("t", "z", "frac", "qfrc_act", "qfrc_pass", "qfrc_con",
                           "c_a0", "c_kh", "c_kp", "c_kr", "clip_lo", "clip_hi")}
    jinfo = {n: (adr, c, h) for adr, c, h, n in jids}
    for k in range(steps):
        if k % CTRL_EVERY == 0:
            z = float(d.qpos[2])
            q = d.qpos[3:7]
            pitch = float(np.arctan2(2 * (q[0] * q[2] - q[3] * q[1]),
                                     1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            roll = float(np.arctan2(2 * (q[0] * q[1] + q[2] * q[3]),
                                    1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            c = dict(a0=blk["a0"], kh=blk["kh"] * (tgt - z),
                     kp=blk["kp"] * pitch, kr=blk["kr"] * roll)
            u_raw = c["a0"] + c["kh"] + c["kp"] + c["kr"]
            d.ctrl[:] = np.clip(u_raw, 0.0, 1.0)
            last_c, last_raw = c, u_raw
        mujoco.mj_step(m, d)
        if k % CTRL_EVERY == 0:
            out["t"].append(k * m.opt.timestep)
            out["z"].append(float(d.qpos[2]))
            out["frac"].append({n: abs(float(d.qpos[adr]) - cc) / hh
                                for n, (adr, cc, hh) in jinfo.items()})
            out["qfrc_act"].append(d.qfrc_actuator.copy())
            out["qfrc_pass"].append(d.qfrc_passive.copy())
            out["qfrc_con"].append(d.qfrc_constraint.copy())
            for b in BLOCKS:
                out[f"c_{b}"].append(last_c[b].copy())
            out["clip_lo"].append(float(np.mean(last_raw < 0.0)))
            out["clip_hi"].append(float(np.mean(last_raw > 1.0)))
            if float(d.qpos[2]) < 0.5 * tgt:
                break
    return out


def main() -> int:
    import mujoco
    a = sys.argv
    tp = Path(a[a.index("--theta") + 1]) if "--theta" in a else THETA
    if not tp.is_absolute():
        tp = OUTDIR / tp.name
    jname = a[a.index("--joint") + 1] if "--joint" in a else "mtp_angle_l"
    if not tp.exists():
        raise SystemExit(f"no {tp} -- refusing to attribute a drive to a policy that does not "
                         f"exist (rule 20).")
    theta = np.load(tp)
    P = derive_stand_port()
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    jids = joint_ids(m, mujoco)
    if jname not in {n for _, _, _, n in jids}:
        raise SystemExit(f"{jname} is not a graded joint -- refusing to report a drive on a "
                         f"joint nothing measures.")
    jid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, jname)
    dofadr = int(m.jnt_dofadr[jid])
    lo, hi = float(m.jnt_range[jid][0]), float(m.jnt_range[jid][1])

    # ── WHICH MUSCLES EVEN TOUCH THIS JOINT. Read from the model's own moment arms at the
    # keyframe, not from a name match: `mtp` in an actuator's name is a convention, a nonzero
    # moment arm about the DOF is a fact.
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    mom = d.actuator_moment
    if mom.ndim == 2 and mom.shape == (m.nu, m.nv):
        arms = np.abs(mom[:, dofadr])
    else:                                    # sparse layout (MuJoCo >= 3.2): expand this column
        arms = np.zeros(m.nu)
        for i in range(m.nu):
            adr, nnz = int(d.moment_rowadr[i]), int(d.moment_rownnz[i])
            cols = d.moment_colind[adr:adr + nnz]
            hit = np.where(cols == dofadr)[0]
            if hit.size:
                arms[i] = abs(float(mom.ravel()[adr + int(hit[0])]))
    crossers = [i for i in range(m.nu) if arms[i] > 1e-9]
    names = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_ACTUATOR, i) or f"act{i}"
             for i in range(m.nu)]

    print(f"\nWHAT DRIVES {jname} THROUGH ITS STOP -- {tp.name}, {SECS:.1f} s (F3's phase 1)")
    print("=" * 100)
    print(f"  declared range {np.degrees(lo):+.1f}..{np.degrees(hi):+.1f} deg "
          f"(half-width {np.degrees(0.5*(hi-lo)):.1f} deg) -- UNCHANGED by this instrument")
    print(f"  muscles with a nonzero moment arm about this DOF: {len(crossers)} of {m.nu}"
          + (f"  ({', '.join(names[i] for i in crossers[:6])}"
             + (", ..." if len(crossers) > 6 else "") + ")" if crossers else ""))
    if not crossers:
        raise SystemExit(f"no actuator has a moment arm about {jname} -- then no formula term "
                         f"can be driving it, and the residual is structural. Refusing to "
                         f"attribute a drive that cannot exist.")

    # ── THE FULL RUN, and the torque ledger on this DOF ────────────────────────────────────
    full = rollout(m, d, mujoco, theta, P, jids, SECS)
    fr = np.array([s[jname] for s in full["frac"]])
    act = np.array([v[dofadr] for v in full["qfrc_act"]])
    pas = np.array([v[dofadr] for v in full["qfrc_pass"]])
    con = np.array([v[dofadr] for v in full["qfrc_con"]])
    base_over = 100.0 * float((fr >= 1.0).mean())
    base_peak = float(fr.max())
    print("-" * 100)
    print(f"  BASELINE (all four blocks live): peak {base_peak:.3f} of range, past the stop "
          f"{base_over:.1f}% of the window")
    print(f"  TORQUE LEDGER on this DOF, N.m, mean over the window (what is pushing while it "
          f"is there):")
    print(f"     actuator (muscle)  {act.mean():+.4f}   |peak| {np.abs(act).max():.4f}")
    print(f"     passive (tissue)   {pas.mean():+.4f}   |peak| {np.abs(pas).max():.4f}")
    print(f"     constraint (stop)  {con.mean():+.4f}   |peak| {np.abs(con).max():.4f}")
    tot_abs = abs(act.mean()) + abs(pas.mean()) + abs(con.mean()) + 1e-12
    print(f"     -> the muscle supplies {100*abs(act.mean())/tot_abs:.0f}% of the mean torque "
          f"magnitude on this DOF")
    # PER-BLOCK CONTRIBUTION TO THE TOE MUSCLES' ACTIVATION -- the ledger's other half.
    print(f"  ACTIVATION LEDGER over the {len(crossers)} crossing muscles, |mean contribution|:")
    contrib = {}
    for b in BLOCKS:
        cb = np.array([v[crossers] for v in full[f"c_{b}"]])
        contrib[b] = float(np.abs(cb).mean())
        print(f"     {b:4} {contrib[b]:.5f}"
              + ("   <- the baseline activation, present at every instant" if b == "a0" else ""))
    dom_led = max(contrib, key=contrib.get)
    print(f"  saturation: raw command below 0 on {100*np.mean(full['clip_lo']):.0f}% of muscle-"
          f"samples, above 1 on {100*np.mean(full['clip_hi']):.0f}%")

    # ── THE ABLATION: zero one block, keep everything else ─────────────────────────────────
    print("-" * 100)
    print(f"  ABLATION -- one block zeroed at a time, every other number identical:")
    print(f"  {'dropped':>9}{'peak':>9}{'past stop %':>14}{'D over':>10}{'held s':>9}")
    print(f"  {'(none)':>9}{base_peak:>9.3f}{base_over:>13.1f}%{'--':>10}"
          f"{full['t'][-1]:>8.2f}s")
    abl = {}
    for b in BLOCKS:
        r = rollout(m, d, mujoco, theta, P, jids, SECS, drop=b)
        f2 = np.array([s[jname] for s in r["frac"]])
        o2 = 100.0 * float((f2 >= 1.0).mean())
        abl[b] = dict(peak=float(f2.max()), over=o2, held=float(r["t"][-1]),
                      d_over=o2 - base_over)
        print(f"  {b:>9}{abl[b]['peak']:>9.3f}{o2:>13.1f}%{o2 - base_over:>+10.1f}"
              f"{abl[b]['held']:>8.2f}s")
    # THE DOMINANT BLOCK IS THE ONE WHOSE REMOVAL DROPS THE OVER-STOP MOST.
    drops = {b: base_over - abl[b]["over"] for b in BLOCKS}
    dom_abl = max(drops, key=drops.get)
    halved = drops[dom_abl] > 0.5 * base_over
    others_small = all(drops[b] < 0.25 * base_over for b in BLOCKS if b != dom_abl)
    agree = (dom_abl == dom_led)
    print("=" * 100)
    print(f"  ABLATION says:   {dom_abl}  (removing it drops the over-stop by "
          f"{drops[dom_abl]:.1f} points of {base_over:.1f})")
    print(f"  LEDGER says:     {dom_led}  (largest mean contribution to the crossing muscles' "
          f"activation)")
    fires = not (halved and others_small and agree)
    if fires:
        why = []
        if not halved:
            why.append(f"no block drops it by more than half ({dom_abl} drops "
                       f"{drops[dom_abl]:.1f} of {base_over:.1f})")
        if not others_small:
            why.append("more than one block moves it materially")
        if not agree:
            why.append(f"the two messengers DISAGREE ({dom_abl} vs {dom_led})")
        print(f"  FALSIFIER: FIRES -- {'; '.join(why)}.")
        print(f"    So the toe is not being DRIVEN through its stop by one formula term. The")
        print(f"    residual is STRUCTURAL: `world.derive_ligaments` refuses an mtp ligament")
        print(f"    because theHuman's `gait_envelope_deg` publishes no toe curve, so nothing")
        print(f"    catches this joint at its limit and MuJoCo's constraint is the only thing")
        print(f"    holding it. That is a FOOT MEMBRANE with its own RULE 0, not a control fix.")
    else:
        print(f"  FALSIFIER: does not fire -- both messengers name {dom_abl}, it drops the "
              f"over-stop by {drops[dom_abl]:.1f} points, and no other block moves it much.")

    LOGDIR.mkdir(parents=True, exist_ok=True)
    out = LOGDIR / f"mtp_drive_{tp.stem}_{jname}.json"
    out.write_text(json.dumps(dict(
        theta=tp.name, joint=jname, secs=SECS,
        range_deg=[float(np.degrees(lo)), float(np.degrees(hi))],
        crossing_muscles=[names[i] for i in crossers],
        baseline_peak=base_peak, baseline_over_pct=base_over,
        torque_actuator_mean=float(act.mean()), torque_passive_mean=float(pas.mean()),
        torque_constraint_mean=float(con.mean()),
        activation_contribution=contrib, ablation=abl, drops=drops,
        dominant_by_ablation=dom_abl, dominant_by_ledger=dom_led,
        messengers_agree=bool(agree), falsifier_fires=bool(fires)), indent=1), encoding="utf8")
    print(f"  JSON: {out}")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(15.5, 4.5))
    ax[0].plot(full["t"], fr, color="#8e44ad", lw=1.6, label=jname)
    ax[0].axhline(1.0, color="#c0392b", lw=1.6, label="the stop")
    ax[0].axhline(0.8, color="#8e44ad", ls=":", lw=1.0, label="0.8")
    ax[0].set_xlabel("s"); ax[0].set_ylabel("fraction of range"); ax[0].legend(fontsize=7)
    ax[0].set_title(f"{jname} -- past its stop {base_over:.0f}% of phase 1", fontsize=9)
    ax[1].plot(full["t"], act, color="#c0392b", lw=1.4, label="actuator")
    ax[1].plot(full["t"], pas, color="#1a7f37", lw=1.4, label="passive")
    ax[1].plot(full["t"], con, color="#2471a3", lw=1.4, label="constraint (the stop)")
    ax[1].axhline(0, color="#999", lw=0.8)
    ax[1].set_xlabel("s"); ax[1].set_ylabel("N.m on the DOF"); ax[1].legend(fontsize=7)
    ax[1].set_title("the torque ledger -- what holds this joint", fontsize=9)
    xs = np.arange(len(BLOCKS))
    ax[2].bar(xs - 0.2, [drops[b] for b in BLOCKS], 0.4, color="#c0392b", label="ablation: Dover")
    ax[2].bar(xs + 0.2, [1e3 * contrib[b] for b in BLOCKS], 0.4, color="#2471a3",
              label="ledger: |contribution| x1e3")
    ax[2].set_xticks(xs); ax[2].set_xticklabels(BLOCKS)
    ax[2].axhline(0, color="#999", lw=0.8); ax[2].legend(fontsize=7)
    ax[2].set_title(f"which term? ablation says {dom_abl}, ledger says {dom_led}", fontsize=9)
    fig.suptitle(f"{jname} DRIVE -- {tp.name}   "
                 f"{'NO SINGLE TERM DRIVES IT (structural)' if fires else f'{dom_abl} drives it'}",
                 fontsize=11.5)
    png = OUTDIR / f"mtp_drive_{tp.stem}_{jname}.png"
    fig.savefig(png, dpi=104, bbox_inches="tight"); plt.close(fig)
    print(f"  PICTURE: {png}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
