"""objective_survival.py -- DOES THE OBJECTIVE PREDICT THE THING IT IS A PROXY FOR?

RULE 0, stated before the run:

    STATEMENT   `stand_reward` is optimised; SURVIVAL is what every judge reports. Nobody has
                plotted one against the other. A proxy that does not correlate with its target
                is a random number generator with a physics-shaped docstring, and the one datum
                available is discouraging: repairing the search moved the objective by 0.227 and
                held-out survival by 0.08 s.

    PREDICTION  Over a population spanning good-to-useless policies, the objective correlates
                with held-out survival at Pearson r > 0.7, and each of its three multiplied
                components correlates positively on its own.

    FALSIFIER   r <= 0.7 -- the proxy does not measure what it claims, every training run in
                this lane optimised a number whose name is wrong, and NO policy class can be
                ranked by it. (The task set this as the falsifier in the other direction; it is
                written here as the prediction so that the interesting outcome is the one that
                fires.)

TWO PREMISE CORRECTIONS, both checked against `stand_port.stand_reward` rather than against a
summary of it:

  * THE OBJECTIVE HAS NO ROLL TERM. It is `height x support x joints - 3*fell - 0.01*effort`.
    `kr * roll` is a POLICY channel -- an input the controller feeds back -- not a component of
    the reward. Asking "roll vs survival" would be asking a question about the controller while
    calling it a question about the objective. The fourth term is EFFORT, and it is measured
    here in roll's place.
  * A POPULATION OF UNIFORMLY-RANDOM THETAS IS DEGENERATE. 1160 numbers drawn uniformly inside
    the trainer's bounds produce a body that falls in well under a second, every time: survival
    has no variance, and a correlation computed over it measures nothing. `tools/search_landscape.py`
    already established how to draw a SPANNING population -- a scale ladder around a known-good
    point -- and that is what is used, with the ladder stated in the open.

THE OBJECTIVE IS THE TRAINER'S OWN NUMBER, from `train_stand.score_theta` at the trainer's own
window and seeds. Not a reimplementation: the question is whether THE THING THAT WAS OPTIMISED
predicts survival, so it has to be that thing and not something adjacent to it.

SURVIVAL IS THE HELD-OUT MEDIAN, seeds 3..9, because seeds 0..2 are what the objective's own
optimiser selects on and a correlation across them would be partly self-fulfilling.

    python tools/objective_survival.py [--n 200] [--secs 12] [--surv-secs 20]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body                                       # noqa: E402
from stand_port import derive_stand_port, MYOBODY, stand_reward   # noqa: E402
from train_stand import (joint_ids, seat_in_limits, joint_fracs,  # noqa: E402
                         score_theta, CTRL_EVERY, NUDGE)
from parser import Parser, default_registry                       # noqa: E402

OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"
LOGDIR = ROOT / "agent_logs"
THETA = OUTDIR / "stand_theta.npy"
TRAINED_SEEDS = (0, 1, 2)          # what the trainer selects on -- excluded from survival
# The ladder that makes the population span. Powers of ten x the trainer's own warm-start sd,
# the same grid `search_landscape.py` uses and for the same reason: at 1 every sample is
# useless and at 1e-5 every sample is the incumbent, so the interesting policies are between.
SCALES = (1e-5, 3e-5, 1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2, 1e-1, 1.0)
WARM_SD_SHAPE = (0.15, 0.6)        # a0 block, gain blocks -- train_stand.main()'s own numbers


def components(m, d, mujoco, theta, P, jids, secs, seed=0):
    """The objective's parts, accumulated over one rollout through the JUDGE'S plant.

    Returns the mean of each factor over the samples, plus effort. These are the terms
    `stand_reward` multiplies; the scalar it returns is `score_theta`'s business and is taken
    from there rather than recomputed here (one quantity, one landmark).
    """
    tgt, nu = P["OUT pelvis_target_m"], m.nu
    PARSER = Parser(default_registry(theta, tgt, nu))
    PARSER.set_verb("STAND", True)
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    seat_in_limits(m, d, mujoco, jids)
    if seed:
        d.qpos[:] = d.qpos + np.random.default_rng(seed).normal(0.0, NUDGE, size=d.qpos.shape)
        mujoco.mj_forward(m, d)
    acc = {"height": [], "support": [], "joints": [], "effort": []}
    steps = int(secs / m.opt.timestep)
    _b = lambda n: d.xpos[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, n)]
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
            z = float(d.qpos[2])
            com = d.subtree_com[0]
            foot = 0.25 * (_b("calcn_r") + _b("calcn_l") + _b("toes_r") + _b("toes_l"))
            _, parts = stand_reward(z, (float(com[0] - foot[0]), float(com[1] - foot[1])),
                                    joint_fracs(d, jids), False,
                                    float(np.abs(d.ctrl).mean()), P)
            acc["height"].append(parts["height"])
            acc["support"].append(parts["support"])
            acc["joints"].append(parts["joints"])
            acc["effort"].append(float(np.abs(d.ctrl).mean()))
            if z < 0.5 * tgt:
                break
    return {k: (float(np.mean(v)) if v else 0.0) for k, v in acc.items()}


def survival(m, d, mujoco, theta, P, jids, secs, seeds):
    """Held-out survival: the median over `seeds`, each a 1e-6-nudged start, at `secs`."""
    tgt, nu = P["OUT pelvis_target_m"], m.nu
    out = []
    for s in seeds:
        PARSER = Parser(default_registry(theta, tgt, nu))
        PARSER.set_verb("STAND", True)
        mujoco.mj_resetDataKeyframe(m, d, 0)
        mujoco.mj_forward(m, d)
        seat_in_limits(m, d, mujoco, jids)
        if s:
            d.qpos[:] = d.qpos + np.random.default_rng(s).normal(0.0, NUDGE, size=d.qpos.shape)
            mujoco.mj_forward(m, d)
        steps = int(secs / m.opt.timestep)
        t_end = secs
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
            if k % CTRL_EVERY == 0 and float(d.qpos[2]) < 0.5 * tgt:
                t_end = k * m.opt.timestep
                break
        out.append(t_end)
    return float(np.median(out)), out


def _pearson(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.std() < 1e-12 or y.std() < 1e-12:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def _spearman(x, y):
    rx = np.argsort(np.argsort(np.asarray(x, float)))
    ry = np.argsort(np.argsort(np.asarray(y, float)))
    return _pearson(rx, ry)


def main() -> int:
    import mujoco
    a = sys.argv
    n = int(a[a.index("--n") + 1]) if "--n" in a else 200
    secs = float(a[a.index("--secs") + 1]) if "--secs" in a else 12.0
    ssecs = float(a[a.index("--surv-secs") + 1]) if "--surv-secs" in a else 20.0
    tp = Path(a[a.index("--theta") + 1]) if "--theta" in a else THETA
    if not tp.is_absolute():
        tp = OUTDIR / tp.name
    theta0 = np.load(tp)
    P = derive_stand_port()
    m, d = (lambda mm: (mm[0], mujoco.MjData(mm[0])))(load_body(MYOBODY, mujoco))
    jids = joint_ids(m, mujoco)
    nu = m.nu
    blocks = theta0.size // nu
    held_ids = [i for i in range(10) if i not in TRAINED_SEEDS]
    sd_unit = np.concatenate([np.full(nu, 0.5 * WARM_SD_SHAPE[0])]
                             + [np.full(nu, 0.5 * WARM_SD_SHAPE[1])] * (blocks - 1))

    print(f"\nOBJECTIVE vs SURVIVAL -- {n} policies around {tp.name}")
    print("=" * 104)
    print(f"  the objective is `height x support x joints - 3*fell - 0.01*effort`. THERE IS NO "
          f"ROLL TERM in it:")
    print(f"  kr*roll is a POLICY channel, not a reward component. The fourth term is EFFORT and "
          f"it is measured here.")
    print(f"  population: a SCALE LADDER around the incumbent ({len(SCALES)} rungs x "
          f"{n//len(SCALES)} draws) -- uniform random thetas")
    print(f"  fall in under a second with no variance, and a correlation over them measures "
          f"nothing.")
    print(f"  objective = train_stand.score_theta (the trainer's own number, {secs:.0f} s, worst "
          f"of seeds {TRAINED_SEEDS})")
    print(f"  survival  = MEDIAN over HELD-OUT seeds {held_ids} at {ssecs:.0f} s")
    print("-" * 104)

    rng = np.random.default_rng(0)
    rows = []
    per_rung = max(1, n // len(SCALES))
    for si, s in enumerate(SCALES):
        for j in range(per_rung):
            th = theta0 + rng.normal(0.0, 1.0, size=theta0.shape) * sd_unit * s
            th[:nu] = np.clip(th[:nu], 0.0, 1.0)
            obj = score_theta(m, d, mujoco, th, P, secs, len(TRAINED_SEEDS))[0]
            comp = components(m, d, mujoco, th, P, jids, secs)
            sv, _ = survival(m, d, mujoco, th, P, jids, ssecs, held_ids)
            rows.append(dict(scale=s, objective=float(obj), survival=float(sv), **comp))
        done = (si + 1) * per_rung
        sub = [r for r in rows if r["scale"] == s]
        print(f"  rung x{s:<8g} {len(sub):>3} draws   objective "
              f"{np.median([r['objective'] for r in sub]):>8.3f}   survival "
              f"{np.median([r['survival'] for r in sub]):>6.2f} s   ({done}/{per_rung*len(SCALES)})")
    # the incumbent itself, as the population's anchor and a control
    obj0 = score_theta(m, d, mujoco, theta0, P, secs, len(TRAINED_SEEDS))[0]
    sv0, _ = survival(m, d, mujoco, theta0, P, jids, ssecs, held_ids)
    print(f"  INCUMBENT              objective {obj0:>8.3f}   survival {sv0:>6.2f} s")

    O = np.array([r["objective"] for r in rows])
    S = np.array([r["survival"] for r in rows])
    print("=" * 104)
    print(f"  {'quantity':<14}{'Pearson r':>12}{'Spearman rho':>15}   n={len(rows)}")
    corr = {}
    for name, v in (("OBJECTIVE", O),
                    ("height", np.array([r["height"] for r in rows])),
                    ("support", np.array([r["support"] for r in rows])),
                    ("joints", np.array([r["joints"] for r in rows])),
                    ("effort", np.array([r["effort"] for r in rows]))):
        pr, sp = _pearson(v, S), _spearman(v, S)
        corr[name] = dict(pearson=pr, spearman=sp)
        tag = "   <- the thing being optimised" if name == "OBJECTIVE" else ""
        print(f"  {name:<14}{pr:>12.3f}{sp:>15.3f}{tag}")
    # ── THE CONFOUND, AND IT WOULD HAVE MANUFACTURED THE WHOLE RESULT ──────────────────────
    # The population is a SCALE LADDER: objective and survival both fall monotonically as the
    # perturbation grows, so a strong pooled correlation can be produced entirely by that
    # common cause without the two quantities being related at fixed scale at all. This is the
    # same species as "never threshold on a quantile of the population you measure" -- a
    # structure in the sampling masquerading as a structure in the body.
    #
    # THE CONTROL IS WITHIN-RUNG: at fixed scale the confound is constant, so a correlation
    # that survives there is a real one. Reported per rung and as the median across rungs; the
    # pooled number is kept beside it, never instead of it (rule 17).
    print("-" * 104)
    print(f"  WITHIN-RUNG CONTROL -- at fixed scale the ladder cannot manufacture a correlation:")
    print(f"  {'rung':>10}{'n':>5}{'obj spread':>13}{'surv spread':>13}{'Pearson r':>12}")
    within = []
    for s in SCALES:
        sub = [r for r in rows if r["scale"] == s]
        if len(sub) < 4:
            continue
        o, v = np.array([r["objective"] for r in sub]), np.array([r["survival"] for r in sub])
        rr = _pearson(o, v)
        within.append(rr)
        print(f"  {s:>10g}{len(sub):>5}{o.max()-o.min():>13.3f}{v.max()-v.min():>12.2f}s"
              f"{rr:>12.3f}")
    r_within = float(np.nanmedian(within)) if within else float("nan")
    print(f"  -> MEDIAN WITHIN-RUNG r = {r_within:.3f}"
          + ("   (too few draws per rung to say -- raise --n)" if not within else ""))
    corr["OBJECTIVE"]["within_rung_median"] = r_within
    print("-" * 104)
    r_obj = corr["OBJECTIVE"]["pearson"]
    fires = not (np.isfinite(r_obj) and r_obj > 0.7)
    print(f"  FALSIFIER (the objective correlates with survival at Pearson r > 0.7): "
          + (f"FIRES -- r = {r_obj:.3f}.\n    The proxy does not measure what it claims. Every "
             f"training run in this lane optimised a number\n    whose name is wrong, and NO "
             f"policy class can be ranked by it -- comparisons must be judged on\n    held-out "
             f"survival directly."
             if fires else
             f"does not fire -- r = {r_obj:.3f}. The proxy tracks its target and ranking "
             f"policies by it is sound."))
    if not fires and np.isfinite(r_within):
        print(f"  BUT READ THE CONTROL BEFORE BELIEVING IT: pooled r {r_obj:.3f} vs "
              f"WITHIN-RUNG median r {r_within:.3f}.")
        print("    " + ("The correlation SURVIVES at fixed scale, so it is a property of the "
                        "policies and not of the ladder."
                        if r_within > 0.5 else
                        "The correlation COLLAPSES at fixed scale. The pooled number is the "
                        "sampling ladder, not the body:\n    the objective ranks a badly-broken "
                        "policy below a mildly-broken one, and says little about which of two\n"
                        "    comparable policies survives longer -- which is the only comparison "
                        "a search ever makes."))

    LOGDIR.mkdir(parents=True, exist_ok=True)
    out = LOGDIR / "objective_survival.json"
    out.write_text(json.dumps(dict(
        theta=tp.name, n=len(rows), secs=secs, surv_secs=ssecs,
        trained_seeds=list(TRAINED_SEEDS), held_out_seeds=held_ids,
        scales=list(SCALES), incumbent_objective=float(obj0), incumbent_survival=float(sv0),
        correlations=corr, falsifier_fires=bool(fires), rows=rows), indent=1), encoding="utf8")
    print(f"  JSON: {out}")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(15.5, 4.6))
    sc = ax[0].scatter(O, S, c=np.log10([r["scale"] for r in rows]), cmap="viridis", s=22,
                       alpha=0.85)
    ax[0].scatter([obj0], [sv0], marker="X", s=140, color="#c0392b", zorder=5,
                  label="the incumbent")
    ax[0].set_xlabel("objective (the trainer's own score)")
    ax[0].set_ylabel(f"held-out survival, median of seeds {held_ids[0]}..{held_ids[-1]} (s)")
    ax[0].legend(fontsize=7)
    ax[0].set_title(f"r = {r_obj:.3f}   rho = {corr['OBJECTIVE']['spearman']:.3f}", fontsize=9)
    plt.colorbar(sc, ax=ax[0], label="log10 perturbation scale")
    for name, c in (("height", "#c0392b"), ("support", "#2471a3"), ("joints", "#1a7f37"))[:3]:
        ax[1].scatter([r[name] for r in rows], S, s=14, alpha=0.6, color=c,
                      label=f"{name}  r={corr[name]['pearson']:.2f}")
    ax[1].set_xlabel("component value"); ax[1].set_ylabel("held-out survival (s)")
    ax[1].legend(fontsize=7)
    ax[1].set_title("each multiplied component against survival", fontsize=9)
    xs = sorted(set(r["scale"] for r in rows))
    ax[2].semilogx(xs, [np.median([r["survival"] for r in rows if r["scale"] == x]) for x in xs],
                   "o-", color="#8e44ad", lw=1.6, label="survival")
    ax2 = ax[2].twinx()
    ax2.semilogx(xs, [np.median([r["objective"] for r in rows if r["scale"] == x]) for x in xs],
                 "s--", color="#e67e22", lw=1.4, label="objective")
    ax[2].set_xlabel("perturbation scale"); ax[2].set_ylabel("survival s", color="#8e44ad")
    ax2.set_ylabel("objective", color="#e67e22")
    ax[2].set_title("do they fall together as the policy degrades?", fontsize=9)
    fig.suptitle(f"OBJECTIVE vs SURVIVAL -- {len(rows)} policies, Pearson r = {r_obj:.3f} "
                 f"({'PROXY FAILS' if fires else 'proxy holds'})", fontsize=11.5)
    png = OUTDIR / "objective_survival.png"
    fig.savefig(png, dpi=104, bbox_inches="tight"); plt.close(fig)
    print(f"  PICTURE: {png}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
