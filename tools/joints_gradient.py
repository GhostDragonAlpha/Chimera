"""joints_gradient.py -- DOES THE JOINTS TERM STILL HAVE A GRADIENT, OR HAS IT SATURATED?

RULE 0, stated before the run:

    STATEMENT   `stand_reward`'s joints factor is `exp(-(max(0, jmax - 0.8)/0.1)^2)` where `jmax`
                is the MAXIMUM over 29 graded joints. Two properties follow, and neither is a
                preference: (a) the max() discards 28 of the 29 joints, so their excursions are
                invisible to the search; (b) the gaussian is flat at BOTH ends -- quadratically
                flat at the threshold, exponentially flat past it -- so once ONE joint is through
                its stop the whole factor is ~0 with ~0 slope, and the height and support terms
                it MULTIPLIES are annihilated with it. The reward stops being a reward.

    PREDICTION  On the incumbent stand policy, over the whole rollout: the retired form's
                sensitivity |d r_j / d f_j| is EXACTLY ZERO for at least 28 of 29 joints at every
                sample, and below 1e-3 even for the one joint it does see. The hinge-sum form is
                nonzero for every joint that is past the threshold, at the same magnitude for
                each.

    FALSIFIER   If the retired form carries comparable per-joint sensitivity -- more than one
                joint with nonzero slope, or the argmax joint's slope within 10x of the hinge
                form's -- then saturation is not the defect and the penalty was never what was
                stopping the search. Record it and stop; do not change the reward.

THE PLANT IS THE JUDGE'S PLANT (`tools/parser.py`), the same path `f3_stand.py` and
`stand_survival.py` drive. Measuring the gradient of a reward on a rollout the judge would not
produce is measuring a different body.

BOTH FORMS ON ONE TRACE. The retired gaussian is recomputed here, beside the hinge, from the
identical joint angles -- the clay-control pattern (CLAUDE.md, 2026-08-01): run the measurement
on the new thing AND on the thing it replaced, or the difference you report may be the
instrument's own signature.

    python tools/joints_gradient.py [--theta <path>] [--secs 8]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body                                       # noqa: E402
from stand_port import (derive_stand_port, MYOBODY,               # noqa: E402
                        JOINT_COLD, JOINT_WIDTH, joints_factor,
                        retired_joints_factor)
from train_stand import joint_ids, seat_in_limits, CTRL_EVERY     # noqa: E402
from parser import Parser, default_registry                       # noqa: E402

OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"
LOGDIR = ROOT / "agent_logs"
THETA = OUTDIR / "stand_theta.npy"


# ── THE RETIRED FORM, kept ONLY as the control ────────────────────────────────────────────────
def retired_max_gaussian(fracs):
    """The retired factor and its slope w.r.t. EACH joint.

    The FACTOR comes from `stand_port.retired_joints_factor` -- one definition, so the control
    arm of the trainer and this instrument cannot drift apart. Only the derivative is written
    here, because a slope is not something the reward itself ever computes.

    Returns `(r, dr)` where `dr[j]` is d r / d f_j. Every joint that is not the argmax has
    slope exactly 0 -- that is the finding, written as arithmetic rather than asserted.
    """
    f = np.asarray(fracs, dtype=float)
    j = int(np.argmax(f))
    e = max(0.0, f[j] - JOINT_COLD)
    r = retired_joints_factor(f)
    dr = np.zeros_like(f)
    if e > 0.0:
        dr[j] = -2.0 * (e / JOINT_WIDTH ** 2) * r     # the chain rule; every other entry stays 0
    return r, dr


def hinge_sum(fracs):
    """The replacement, and its slope w.r.t. each joint. `joints_factor` is the live one."""
    f = np.asarray(fracs, dtype=float)
    e = np.maximum(0.0, f - JOINT_COLD)
    r = joints_factor(f)
    dr = np.where(e > 0.0, -(1.0 / JOINT_WIDTH) * r * r, 0.0)
    return float(r), dr


def main() -> int:
    import mujoco
    a = sys.argv
    secs = float(a[a.index("--secs") + 1]) if "--secs" in a else 8.0
    tpath = Path(a[a.index("--theta") + 1]) if "--theta" in a else THETA
    if not tpath.exists():
        raise SystemExit(f"no {tpath} -- refusing to measure the gradient of a reward on a "
                         f"policy that does not exist (rule 20).")
    theta = np.load(tpath)
    P = derive_stand_port()
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    jids = joint_ids(m, mujoco)
    names = [n for _, _, _, n in jids]
    tgt, nu = P["OUT pelvis_target_m"], m.nu

    PARSER = Parser(default_registry(theta, tgt, nu))
    PARSER.set_verb("STAND", True)
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    seat_in_limits(m, d, mujoco, jids)

    steps = int(secs / m.opt.timestep)
    F, R_old, R_new, D_old, D_new, T = [], [], [], [], [], []
    for k in range(steps):
        if k % CTRL_EVERY == 0:
            z = float(d.qpos[2])
            q = d.qpos[3:7]
            pitch = float(np.arctan2(2 * (q[0] * q[2] - q[3] * q[1]),
                                     1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            roll = float(np.arctan2(2 * (q[0] * q[1] + q[2] * q[3]),
                                    1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            u, _ = PARSER.command({"z": z, "pitch": pitch, "roll": roll})
            d.ctrl[:] = u if u is not None else 0.0
        mujoco.mj_step(m, d)
        if k % CTRL_EVERY == 0:
            fr = np.array([abs(float(d.qpos[adr]) - c) / h for adr, c, h, _ in jids])
            ro, do = retired_max_gaussian(fr)
            rn, dn = hinge_sum(fr)
            T.append(k * m.opt.timestep)
            F.append(fr); R_old.append(ro); R_new.append(rn)
            D_old.append(np.abs(do)); D_new.append(np.abs(dn))
    F = np.array(F); D_old = np.array(D_old); D_new = np.array(D_new)
    R_old = np.array(R_old); R_new = np.array(R_new)

    over_cold = (F > JOINT_COLD)
    over_stop = (F >= 1.0)
    live_old = (D_old > 0.0).sum(axis=1)      # joints with ANY slope, per sample
    live_new = (D_new > 0.0).sum(axis=1)

    print(f"\nJOINTS TERM -- GRADIENT, MEASURED    theta {tpath.name}, {secs:.0f} s, "
          f"{len(T)} control samples, {len(names)} graded joints")
    print("=" * 100)
    print(f"  cold threshold {JOINT_COLD}   width {JOINT_WIDTH}   (both unchanged: this "
          f"measures the FORM, not the constants)")
    print(f"  joints past the threshold {JOINT_COLD}: mean {over_cold.sum(1).mean():.1f} of "
          f"{len(names)}   past their STOP (1.0): mean {over_stop.sum(1).mean():.1f}")
    print(f"  RETIRED  max-then-gaussian   factor: min {R_old.min():.3e}  median "
          f"{np.median(R_old):.3e}  max {R_old.max():.3e}")
    print(f"  HINGE    sum-then-lorentzian factor: min {R_new.min():.3e}  median "
          f"{np.median(R_new):.3e}  max {R_new.max():.3e}")
    print(f"  JOINTS CARRYING ANY SLOPE, per sample:  retired mean {live_old.mean():.2f} "
          f"(max {live_old.max()})   hinge mean {live_new.mean():.2f} (max {live_new.max()})")
    print(f"  |d r / d f| over all (sample, joint) pairs where f > {JOINT_COLD}:")
    sel = over_cold
    if sel.any():
        print(f"     retired  median {np.median(D_old[sel]):.3e}   max {D_old[sel].max():.3e}   "
              f"exactly-zero {100.0*(D_old[sel] == 0).mean():.1f}% of them")
        print(f"     hinge    median {np.median(D_new[sel]):.3e}   max {D_new[sel].max():.3e}   "
              f"exactly-zero {100.0*(D_new[sel] == 0).mean():.1f}% of them")
    print("-" * 100)
    print(f"  {'joint':24}{'peak frac':>11}{'% past stop':>13}{'retired |dr|':>15}"
          f"{'hinge |dr|':>13}")
    order = np.argsort(-F.max(axis=0))
    for j in order[:12]:
        pk = F[:, j].max()
        pct = 100.0 * over_stop[:, j].mean()
        print(f"  {names[j]:24}{pk:>11.3f}{pct:>12.0f}%{D_old[:, j].max():>15.3e}"
              f"{D_new[:, j].max():>13.3e}")
    print("=" * 100)

    # ---- THE FALSIFIER --------------------------------------------------------------------
    n_live_retired = float(live_old.mean())
    med_old = float(np.median(D_old[sel])) if sel.any() else 0.0
    med_new = float(np.median(D_new[sel])) if sel.any() else 0.0
    # A RATIO AGAINST ZERO IS THE GUARD SPEAKING, NOT THE DATA. The first version divided by
    # `max(med_old, 1e-300)` and printed "1.22e+299x larger", which is a fact about 1e-300 and
    # about nothing in this body. When the denominator is exactly zero the honest report is that
    # it is exactly zero -- the strongest form of the finding, and the one a reader can check.
    ratio = (med_new / med_old) if med_old > 0.0 else None
    fires = (n_live_retired > 1.0 + 1e-9) or (ratio is not None and ratio < 10.0)
    if fires:
        verdict = "FIRES -- saturation is NOT the defect. Do not change the reward."
    elif ratio is None:
        verdict = (f"DOES NOT FIRE -- the retired form sees {n_live_retired:.2f} of "
                   f"{len(names)} joints per sample and its MEDIAN per-joint slope is EXACTLY "
                   f"ZERO (undefined ratio). The hinge's is {med_new:.3e}. Saturation is real.")
    else:
        verdict = (f"DOES NOT FIRE -- the retired form sees {n_live_retired:.2f} of "
                   f"{len(names)} joints per sample and the hinge's median slope is "
                   f"{ratio:.3g}x larger. Saturation is real.")
    print(f"  FALSIFIER (retired form carries comparable per-joint gradient): " + verdict)
    LOGDIR.mkdir(parents=True, exist_ok=True)
    out = LOGDIR / f"joints_gradient_{tpath.stem}.json"
    out.write_text(json.dumps(dict(
        theta=tpath.name, secs=secs, samples=len(T), n_joints=len(names),
        cold=JOINT_COLD, width=JOINT_WIDTH,
        mean_joints_past_cold=float(over_cold.sum(1).mean()),
        mean_joints_past_stop=float(over_stop.sum(1).mean()),
        retired_factor_median=float(np.median(R_old)), hinge_factor_median=float(np.median(R_new)),
        retired_live_joints_mean=n_live_retired, hinge_live_joints_mean=float(live_new.mean()),
        retired_slope_median=med_old, hinge_slope_median=med_new,
        slope_ratio=(float(ratio) if ratio is not None else None),
        falsifier_fires=bool(fires),
        peak_frac={names[j]: float(F[:, j].max()) for j in range(len(names))},
        pct_past_stop={names[j]: float(100.0 * over_stop[:, j].mean())
                       for j in range(len(names))}), indent=1), encoding="utf8")
    print(f"  JSON: {out}")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(15.5, 4.5))
    ax[0].semilogy(T, np.maximum(R_old, 1e-16), color="#c0392b", lw=1.5, label="retired: max→gauss")
    ax[0].semilogy(T, np.maximum(R_new, 1e-16), color="#1a7f37", lw=1.5, label="hinge: sum→lorentz")
    ax[0].set_xlabel("s"); ax[0].set_ylabel("joints factor (log)"); ax[0].legend(fontsize=7.5)
    ax[0].set_title("the factor that MULTIPLIES height and support", fontsize=9)
    ax[1].plot(T, live_old, color="#c0392b", lw=1.5, label="retired")
    ax[1].plot(T, live_new, color="#1a7f37", lw=1.5, label="hinge")
    ax[1].set_xlabel("s"); ax[1].set_ylabel("joints with nonzero slope")
    ax[1].set_ylim(-0.5, len(names) + 0.5); ax[1].legend(fontsize=7.5)
    ax[1].set_title(f"how many of {len(names)} joints the term can SEE", fontsize=9)
    ff = np.linspace(0.6, 1.6, 400)
    ax[2].plot(ff, [np.exp(-((max(0.0, v - JOINT_COLD) / JOINT_WIDTH) ** 2)) for v in ff],
               color="#c0392b", lw=1.8, label="retired (one joint)")
    ax[2].plot(ff, [1.0 / (1.0 + max(0.0, v - JOINT_COLD) / JOINT_WIDTH) for v in ff],
               color="#1a7f37", lw=1.8, label="hinge (one joint)")
    ax[2].axvline(1.0, color="#555", ls="--", lw=1.0)
    ax[2].text(1.005, 0.6, "the stop", fontsize=7, color="#555")
    ax[2].set_xlabel("joint fraction of range"); ax[2].set_ylabel("factor")
    ax[2].legend(fontsize=7.5); ax[2].set_title("the two shapes, one joint", fontsize=9)
    fig.suptitle(f"JOINTS TERM GRADIENT -- {tpath.name}   retired sees "
                 f"{n_live_retired:.2f} joints/sample, hinge sees {live_new.mean():.2f}",
                 fontsize=11.5)
    png = OUTDIR / f"joints_gradient_{tpath.stem}.png"
    fig.savefig(png, dpi=104, bbox_inches="tight"); plt.close(fig)
    print(f"  PICTURE: {png}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
