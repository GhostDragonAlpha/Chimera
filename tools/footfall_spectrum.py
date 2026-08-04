"""footfall_spectrum.py -- IS THE 0.14 s FOOTFALL A MEASUREMENT, OR THE INSTRUMENT'S OWN FLOOR?

RULE 0, stated before the run:

    STATEMENT   Every walk arm reports `period_s = 0.14`. `chimera_gait._periodicity` searches
                lags in [lo=0.15 s, hi=2.0 s] and this harness samples at dt = 0.02 s, so its
                smallest admissible lag is `max(2, int(0.15/0.02)) * dt` = 7 * 0.02 = **0.14 s
                exactly**. A reported period equal to a search window's edge is the shape of a
                number that was CLAMPED, not measured -- and this project has already been caught
                once by an instrument reporting its own construction (the cross-hatch that was the
                canvas's, 27.8x).

    PREDICTION  The support signal's autocorrelation has a genuine INTERIOR peak at 0.14 s --
                i.e. it rises to a local maximum there and falls away on both sides -- so 0.14 s
                is a real cadence and the body really is shuffling at ~7 Hz footfall.

    FALSIFIER   If the autocorrelation is monotonically DECREASING out of lag 0 across the whole
                window, then `argmax` returns the leftmost admissible lag whatever the signal
                does, "0.14 s" is the clamp speaking, and the correct statement is NOT "it
                shuffles at 0.14 s" but "there is no cycle at any lag this instrument can see".
                Those two demand different fixes: the first is a cadence the reward can push on,
                the second is a plant that never establishes a rhythm at all.

WHY THIS RUNS BEFORE THE CADENCE TERM. A reward term that penalises "period < 0.6 * step_time"
is correct in DIRECTION under either answer -- 0.14 and "nothing" are both under the bar. But the
two answers predict different outcomes for it, and a term added against a misdiagnosed signal is
how a score gets tuned for six turns against a plant that was never listening.

    python tools/footfall_spectrum.py --theta walk_theta_mult.npy
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body                                              # noqa: E402
from stand_port import derive_stand_port, MYOBODY                        # noqa: E402
from train_stand import joint_ids, seat_in_limits, CTRL_EVERY            # noqa: E402
from walk_port import derive_walk_port, muscle_groups, walk_formula      # noqa: E402
from train_walk import foot_contact                                      # noqa: E402
from chimera_gait import _periodicity                                    # noqa: E402

OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"
LOGDIR = ROOT / "agent_logs"
STAND_THETA = OUTDIR / "stand_theta.npy"
SECS = 6.0          # f4's judged window, so this describes the rollout f4 judges


def support_trace(m, d, mujoco, theta_stand, theta_walk, groups, P, secs):
    """The support signal f4 and the trainer both feed to `_periodicity`, and nothing else."""
    nu = m.nu
    jids = joint_ids(m, mujoco)
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    seat_in_limits(m, d, mujoco, jids)
    tgt, omega = P["OUT pelvis_target_m"], P["OUT omega_rad_s"]
    steps = int(secs / m.opt.timestep)
    sup, t, cr_s, cl_s = [], [], [], []
    for k in range(steps):
        if k % CTRL_EVERY == 0:
            z = float(d.qpos[2])
            q = d.qpos[3:7]
            pitch = float(np.arctan2(2 * (q[0] * q[2] - q[3] * q[1]),
                                     1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            roll = float(np.arctan2(2 * (q[0] * q[1] + q[2] * q[3]),
                                    1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            d.ctrl[:] = walk_formula(theta_stand, theta_walk, groups, z, pitch,
                                     omega * d.time, nu, tgt, gain=1.0, roll=roll)
        mujoco.mj_step(m, d)
        if k % CTRL_EVERY == 0:
            cr, cl = foot_contact(m, d, mujoco)
            t.append(k * m.opt.timestep)
            cr_s.append(cr); cl_s.append(cl)
            sup.append((1.0 if cr > 0 else 0.0) + (1.0 if cl > 0 else 0.0))
            if float(d.qpos[2]) < 0.5 * tgt:
                break
    return np.array(t), np.array(sup), np.array(cr_s), np.array(cl_s)


def main() -> int:
    import mujoco
    a = sys.argv
    tp = Path(a[a.index("--theta") + 1]) if "--theta" in a else OUTDIR / "walk_theta_mult.npy"
    if not tp.is_absolute():
        tp = OUTDIR / tp.name
    if not tp.exists():
        raise SystemExit(f"no {tp} -- refusing to measure the cadence of a walk that does not "
                         f"exist (rule 20).")
    theta_stand, theta_walk = np.load(STAND_THETA), np.load(tp)
    P = derive_walk_port()
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    groups = muscle_groups(m, d, mujoco)
    t, sup, cr, cl = support_trace(m, d, mujoco, theta_stand, theta_walk, groups, P, SECS)

    dt = CTRL_EVERY * m.opt.timestep
    # THE INSTRUMENT'S OWN EDGES, computed the way `_periodicity` computes them, so the two
    # cannot disagree. `lo`/`hi` are that function's defaults; read here, never re-chosen.
    lo, hi = 0.15, 2.0
    n = len(sup)
    x = sup.astype(np.float64) - sup.mean()
    klo, khi = max(2, int(lo / dt)), min(n - 1, int(hi / dt))
    ac = np.correlate(x, x, mode="full")[n - 1:]
    ac = ac / ac[0] if ac[0] > 0 else ac
    per, period = _periodicity(sup, dt)
    k_arg = klo + int(np.argmax(ac[klo:khi])) if khi > klo else -1

    # IS IT AN INTERIOR PEAK? A genuine cadence rises to a local max and falls away on both
    # sides. The leftmost admissible lag being the argmax proves nothing on its own -- it is
    # what a monotonically decaying autocorrelation ALWAYS returns.
    at_edge = (k_arg == klo)
    interior = (0 < k_arg < len(ac) - 1
                and ac[k_arg] >= ac[k_arg - 1] and ac[k_arg] >= ac[k_arg + 1])
    # The unrestricted argmax over EVERY lag from 1 up: where the correlation actually peaks
    # when the window is not allowed to decide.
    k_free = 1 + int(np.argmax(ac[1:khi])) if khi > 1 else -1

    print(f"\nFOOTFALL SPECTRUM -- {tp.name}, {SECS:.0f} s judged window, dt {dt*1000:.0f} ms")
    print("=" * 96)
    print(f"  theHuman: step_time {P['IN  step_time_s']:.4f} s, stride {P['OUT stride_s']:.4f} s, "
          f"duty {P['OUT duty_factor']:.4f}")
    print(f"  the support signal ran {t[-1]:.2f} s ({n} samples); values seen: "
          f"{sorted(set(sup.tolist()))}")
    print(f"  _periodicity's window: lo {lo:.2f} s -> lag {klo} = {klo*dt:.3f} s   "
          f"hi {hi:.2f} s -> lag {khi} = {khi*dt:.3f} s")
    print(f"  _periodicity RETURNS: strength {per:.3f}, period {period:.3f} s "
          f"(lag {k_arg})")
    print("-" * 96)
    print(f"  {'lag s':>8}{'autocorr':>11}   {'':<40}")
    for kk in range(1, min(khi, klo + 26)):
        bar = "#" * max(0, int(round(38 * max(0.0, ac[kk]))))
        mark = ""
        if kk == klo:
            mark = "  <- WINDOW FLOOR (lo=0.15 s)"
        if kk == k_arg:
            mark += "  <- argmax, the reported period"
        print(f"  {kk*dt:>8.2f}{ac[kk]:>11.3f}   {bar:<40}{mark}")
    print("-" * 96)
    print(f"  unrestricted argmax over ALL lags >= 1: lag {k_free} = {k_free*dt:.3f} s, "
          f"ac {ac[k_free]:.3f}"
          + ("   (the window is NOT what chose the answer)" if k_free >= klo else
             "   (the true peak is BELOW the window -- the window clamped it up)"))
    print(f"  reported lag sits at the window floor: {'YES' if at_edge else 'no'}")
    print(f"  reported lag is an INTERIOR local maximum: {'YES' if interior else 'NO'}")
    print("=" * 96)
    fires = at_edge and not interior
    print(f"  FALSIFIER (the autocorrelation only decays; 0.14 s is the clamp, not a cadence): "
          + ("FIRES -- there is NO cycle at any lag this instrument can see. The correct "
             "statement is\n    'no rhythm', not 'a 0.14 s rhythm', and a cadence term is "
             "pushing on a signal that does not exist."
             if fires else
             "does not fire -- the peak is real and interior, so the body genuinely repeats at "
             f"{period:.3f} s.\n    A cadence term has something to push on."))
    print(f"  EITHER WAY the derived bar is unmet: {period:.3f} s vs 0.6 x step_time = "
          f"{0.6*P['IN  step_time_s']:.3f} s "
          f"({100*period/P['IN  step_time_s']:.0f}% of step_time, bar 60%).")

    LOGDIR.mkdir(parents=True, exist_ok=True)
    out = LOGDIR / f"footfall_spectrum_{tp.stem}.json"
    out.write_text(json.dumps(dict(
        theta=tp.name, secs=float(t[-1]), dt=dt, samples=n,
        step_time_s=P["IN  step_time_s"], stride_s=P["OUT stride_s"],
        periodicity=per, period_s=period, lag=int(k_arg), window_floor_lag=int(klo),
        window_floor_s=klo * dt, at_window_floor=bool(at_edge), interior_peak=bool(interior),
        free_argmax_lag=int(k_free), free_argmax_s=k_free * dt,
        falsifier_fires=bool(fires),
        autocorr=[float(v) for v in ac[:khi]]), indent=1), encoding="utf8")
    print(f"  JSON: {out}")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(13.5, 4.4))
    lags = np.arange(khi) * dt
    ax[0].plot(lags, ac[:khi], color="#2471a3", lw=1.6)
    ax[0].axvline(klo * dt, color="#c0392b", ls="--", lw=1.4,
                  label=f"window floor {klo*dt:.2f} s")
    ax[0].axvline(period, color="#8e44ad", lw=1.8, label=f"reported period {period:.2f} s")
    ax[0].axvline(P["IN  step_time_s"], color="#1a7f37", lw=1.8,
                  label=f"derived step_time {P['IN  step_time_s']:.2f} s")
    ax[0].axhline(0, color="#999", lw=0.8)
    ax[0].set_xlabel("lag s"); ax[0].set_ylabel("autocorrelation"); ax[0].legend(fontsize=7)
    ax[0].set_title("support-signal autocorrelation -- is the peak real or the edge?",
                    fontsize=9)
    ax[1].step(t, cr > 0, color="#c0392b", lw=1.3, where="post", label="R down")
    ax[1].step(t, [1.3 if v else 0.3 for v in (cl > 0)], color="#2471a3", lw=1.3,
               where="post", label="L down")
    ax[1].set_ylim(-0.3, 1.9); ax[1].set_xlabel("s"); ax[1].legend(fontsize=7)
    ax[1].set_title(f"the footfall itself -- {tp.stem}", fontsize=9)
    fig.suptitle(f"FOOTFALL SPECTRUM -- {tp.name}: reported {period:.3f} s, window floor "
                 f"{klo*dt:.3f} s, {'CLAMPED' if fires else 'a real interior peak'}",
                 fontsize=11.5)
    png = OUTDIR / f"footfall_spectrum_{tp.stem}.png"
    fig.savefig(png, dpi=104, bbox_inches="tight"); plt.close(fig)
    print(f"  PICTURE: {png}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
