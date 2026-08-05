"""search_landscape.py -- HOW FAR CAN THE SEARCH STEP FROM THE INCUMBENT BEFORE IT BREAKS?

RULE 0, stated before the run:

    STATEMENT   The elite-mean guard stops the search's centre being DESTROYED. It cannot help
                if the sampler never proposes an improvement in the first place, and those are
                two different walls. At 1160 dimensions an isotropic Gaussian perturbation of
                sd = 0.075 changes every one of 1160 numbers at once; if the incumbent sits in a
                basin narrower than that, essentially every sample is worse and no update rule
                can rescue a population with nothing good in it.

    PREDICTION  The fraction of samples that BEAT the incumbent falls monotonically with the
                perturbation scale, and at the trainer's own warm-start sd it is under 5%. The
                scale at which half the samples still beat it is at least an order of magnitude
                smaller.

    FALSIFIER   If a substantial fraction (>= 25%) of samples beat the incumbent at the
                trainer's own sd, the sampler is fine, the population was never the problem, and
                the warm-start failure is entirely the update rule -- in which case the guard
                alone should have been enough and this instrument says so.

THIS IS A RESPONSE CURVE, NOT A SWEEP (rule 1). Nothing here is chosen and no number is being
selected: it measures the SHAPE of the fitness landscape around a known point -- how the
probability of improvement decays with step size -- which is a property of the body and the
policy, not a setting. The same distinction `tools/grab_load_path.py` draws for its mass curve.

THE INCUMBENT'S SCORE IS THE REFERENCE AND IT IS MEASURED ONCE, through the trainer's own
`score_theta` at the trainer's own seeds and window, so "beats the incumbent" means exactly what
it means inside the search and not something adjacent to it.

    python tools/search_landscape.py [--theta stand_theta.npy] [--samples 12] [--secs 12]
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
from train_stand import score_theta                               # noqa: E402
import policy_classes as PC                                       # noqa: E402

OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"
LOGDIR = ROOT / "agent_logs"
THETA = OUTDIR / "stand_theta.npy"
# THE SEARCH'S OWN ELITE FRACTION, which is the criterion `derive_step` uses and the one task 10
# names ("at what scale do > 4/24 samples beat the incumbent"). It is not a bar chosen here: it
# is `max(3, pop//5) / pop` at the trainer's own pop = 24. A step is useful exactly when at least
# the fraction of samples the search will KEEP are improvements; asking for more than that is
# asking for a property the algorithm does not use.
ELITE_FRAC = max(3, 24 // 5) / 24.0
# THE TRAINER'S OWN WARM-START SCALE, not a number invented here: `train_stand.main()` builds
# sd = concat([full(nu, 0.15)] + [full(nu, 0.6)] * 3) and a warm start halves it, so the a0
# block is perturbed at 0.075 and the gain blocks at 0.30. Read from that construction so the
# curve is anchored to the search it is describing (rule 19: one landmark).
WARM_A0_SD = 0.5 * 0.15
WARM_GAIN_SD = 0.5 * 0.6
# The decades either side of it. Powers of ten, so the curve spans the question rather than
# sampling near an answer somebody hoped for.
#
# EXTENDED DOWN TO 1e-6 ON 2026-08-04, and the extension is a measurement, not a tuning. Task 10
# asked whether rate feedback WIDENS the basin; the PD policy returned 0% at every rung including
# the smallest, so the honest report was "below 1e-4" -- a bound, not a number. This file's own
# rule is that a value off the end of a measured curve is not a measurement, so the curve was
# lengthened until the answer is inside it. The grid stays powers of ten and nothing about it is
# selected for an outcome.
#
# THE LARGEST QUALIFYING RUNG IS THE ANSWER, so adding rungs BELOW cannot change a result that
# already qualified above them: `p_only` reaches 58.3% at 1e-4 on both grids and its basin is
# 1e-4 either way. The extension can only resolve arms that were pinned at the old floor.
SCALES = (0.0, 1e-6, 3e-6, 1e-5, 3e-5, 1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2, 1e-1, 3e-1, 1.0)


def main() -> int:
    import mujoco
    a = sys.argv
    tp = Path(a[a.index("--theta") + 1]) if "--theta" in a else THETA
    if not tp.is_absolute():
        tp = OUTDIR / tp.name
    nsamp = int(a[a.index("--samples") + 1]) if "--samples" in a else 12
    secs = float(a[a.index("--secs") + 1]) if "--secs" in a else 12.0
    seeds = int(a[a.index("--seeds") + 1]) if "--seeds" in a else 3
    if not tp.exists():
        raise SystemExit(f"no {tp} -- refusing to measure the landscape around a policy that "
                         f"does not exist (rule 20).")
    # --class NAMES THE POLICY CLASS (2026-08-04, task 10). Absent, this file behaves exactly as
    # it did: `train_stand.score_theta`'s inline a0|kh|kp|kr formula on a 4-block theta. Present,
    # it scores through `benchmark_policies.score_theta` with that class -- which is how the same
    # instrument can measure the basin of a P-only and a PD policy WITHOUT two implementations of
    # "score a candidate", the difference between which would be indistinguishable from a
    # difference between the two basins.
    cls_name = a[a.index("--class") + 1] if "--class" in a else None
    pc = PC.get(cls_name) if cls_name else None
    theta = np.load(tp)
    P = derive_stand_port()
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    nu = m.nu
    blocks = theta.size // nu
    if pc is not None:
        import benchmark_policies as BP
        from train_stand import joint_ids as _joint_ids
        _J = _joint_ids(m, mujoco)
        pc.decode_theta(theta, nu)          # refuse a theta this class cannot be, before paying

        def score(mm, dd, mj, th, PP, ss, sd_):
            """train_stand.score_theta's shape, through the class. Returns a 1-tuple because
            that is what the caller below indexes -- one call site, two implementations, and
            the difference between them must not be able to look like a difference in basins."""
            return (BP.score_theta(mj, mm, dd, _J, PP, pc, th, ss, sd_),)
    else:
        score = score_theta

    inc = score(m, d, mujoco, theta, P, secs, seeds)[0]
    print(f"\nTHE SEARCH LANDSCAPE AROUND {tp.name} -- {theta.size} numbers = {blocks} x {nu}")
    print("=" * 104)
    print(f"  scored the trainer's way: WORST of {seeds} starts x {secs:.0f} s. "
          f"INCUMBENT = {inc:.4f}")
    print(f"  the trainer's own warm-start scale: a0 block {WARM_A0_SD:g}, gain blocks "
          f"{WARM_GAIN_SD:g} (= 0.5 x its cold sd)")
    print(f"  {nsamp} samples per scale; the perturbation keeps the trainer's own SHAPE "
          f"(a0 : gains = 0.15 : 0.6) and only its magnitude moves")
    print("-" * 104)
    print(f"  {'scale x trainer':>17}{'a0 sd':>10}{'best':>10}{'median':>10}{'worst':>10}"
          f"{'beat inc':>11}{'|dtheta|':>11}")
    rng = np.random.default_rng(0)
    rows = []
    for s in SCALES:
        # THE SHAPE IS THE TRAINER'S, THE MAGNITUDE IS THE VARIABLE. Perturbing every block by
        # one scalar would ask a different question -- the trainer never does that, and a
        # landscape measured along a direction the search cannot take describes nothing it does.
        # THE CLASS SUPPLIES ITS OWN SPREAD SHAPE when one is named -- `pc.build_sd(nu) * 0.5` is
        # literally what `benchmark_policies.train` starts from, so "x1 = the trainer's own
        # scale" stays true for a 7-block PD policy exactly as it was for a 4-block P-only one.
        # Without this the a0 spread would be applied to whatever block happens to be first,
        # which for `pd_no_a0` is a GAIN block -- a landscape measured along a direction the
        # search cannot take describes nothing it does.
        sd = ((pc.build_sd(nu) * 0.5) if pc is not None
              else np.concatenate([np.full(nu, WARM_A0_SD)]
                                  + [np.full(nu, WARM_GAIN_SD)] * (blocks - 1))) * s
        sc, dists = [], []
        for i in range(nsamp):
            cand = theta + rng.normal(0.0, 1.0, size=theta.shape) * sd
            if pc is None or pc.has_a0:
                cand[:nu] = np.clip(cand[:nu], 0.0, 1.0)  # an activation, as the trainer clips
            sc.append(score(m, d, mujoco, cand, P, secs, seeds)[0])
            dists.append(float(np.linalg.norm(cand - theta)))
            if s == 0.0:
                break                                    # every sample is the incumbent itself
        sc = np.array(sc)
        beat = 100.0 * float((sc > inc).mean())
        rows.append(dict(scale=s, a0_sd=float(WARM_A0_SD * s), n=len(sc),
                         best=float(sc.max()), median=float(np.median(sc)),
                         worst=float(sc.min()), pct_beat=beat,
                         mean_step=float(np.mean(dists))))
        mark = "   <- THE TRAINER'S OWN SCALE" if abs(s - 1.0) < 1e-12 else (
            "   <- no perturbation: the control" if s == 0.0 else "")
        print(f"  {s:>17g}{WARM_A0_SD*s:>10.5f}{sc.max():>10.4f}{np.median(sc):>10.4f}"
              f"{sc.min():>10.4f}{beat:>10.1f}%{np.mean(dists):>11.3f}{mark}")
    print("=" * 104)

    at_one = [r for r in rows if abs(r["scale"] - 1.0) < 1e-12][0]
    # THE HALF-POINT: the largest scale at which at least half the samples still beat the
    # incumbent. Reported as "below the smallest scale tried" when even that fails, rather than
    # extrapolated -- a number off the end of a measured curve is not a measurement.
    good = [r for r in rows if r["scale"] > 0 and r["pct_beat"] >= 50.0]
    half = max((r["scale"] for r in good), default=None)
    # THE BASIN WIDTH, at the criterion the SEARCH ITSELF uses (task 10's question): the largest
    # scale at which at least the elite fraction of samples beat the incumbent. This is the
    # number `derive_step` selects on, so it is the one that says whether a search can find an
    # improvement at its natural step -- not the 50% point, which no part of the algorithm reads.
    elite_good = [r for r in rows if r["scale"] > 0 and r["pct_beat"] >= 100.0 * ELITE_FRAC]
    basin = max((r["scale"] for r in elite_good), default=None)
    zero = [r for r in rows if r["scale"] == 0.0][0]
    print(f"  CONTROL (scale 0): {zero['best']:.4f} vs the incumbent's {inc:.4f} -- "
          + ("identical, as it must be." if abs(zero["best"] - inc) < 1e-9 else
             "THESE MUST MATCH. They do not, so the scoring is not deterministic and every "
             "row above is suspect."))
    # THE DIMENSION IS READ FROM THE THETA, never a literal. It said "1160-dim space" for every
    # policy, which is true only of a 4-block one -- a PD theta is 2030 and the sentence would
    # have reported the wrong space while the number beside it was right. An instrument that
    # recomputes a fact instead of reading it disagrees with the thing it measures the moment
    # the thing changes (f4_walk's own note, same species).
    print(f"  AT THE TRAINER'S OWN SCALE: {at_one['pct_beat']:.1f}% of samples beat the "
          f"incumbent (mean step {at_one['mean_step']:.3f} in {theta.size}-dim space)")
    print(f"  HALF THE SAMPLES STILL BEAT IT AT: "
          + (f"{half:g} x the trainer's scale (a0 sd {WARM_A0_SD*half:.5f})" if half else
             f"NO SCALE TRIED -- not even {min(r['scale'] for r in rows if r['scale']>0):g}x."))
    print(f"  BASIN WIDTH at the SEARCH'S OWN criterion (>= {100*ELITE_FRAC:.1f}% = the elite "
          f"fraction 4/24): "
          + (f"{basin:g} x the trainer's scale" if basin else
             f"NO SCALE TRIED -- not even "
             f"{min(r['scale'] for r in rows if r['scale']>0):g}x."))
    print(f"    This is the number task 10 asks for, and the one `derive_step` selects on. The "
          f"P-only incumbent measures 1e-4\n    (70% beat it there, 10% at 3e-4, 0% beyond) -- so "
          f"a wider basin here means the derivative changed the\n    LANDSCAPE the search "
          f"navigates, not only the survival it reaches.")
    fires = at_one["pct_beat"] >= 25.0
    print(f"  FALSIFIER (>= 25% of samples beat the incumbent at the trainer's own sd): "
          + ("FIRES -- the sampler is fine and the population was never the problem; the "
             "warm-start\n    failure is entirely the update rule, and the elite-mean guard "
             "alone should have been enough."
             if fires else
             f"does not fire -- {at_one['pct_beat']:.1f}% beat it. The population itself is "
             f"almost all worse than\n    the incumbent, so NO update rule can rescue it: the "
             f"step size is the second wall, and it is\n    a property of the landscape, not of "
             f"the trainer's taste."))

    LOGDIR.mkdir(parents=True, exist_ok=True)
    out = LOGDIR / f"search_landscape_{tp.stem}.json"
    out.write_text(json.dumps(dict(
        theta=tp.name, theta_size=int(theta.size), blocks=blocks, nu=nu, g=g,
        policy_class=cls_name or "p_only (the inline formula)",
        secs=secs, seeds=seeds, samples_per_scale=nsamp,
        incumbent_score=float(inc), warm_a0_sd=WARM_A0_SD, warm_gain_sd=WARM_GAIN_SD,
        rows=rows, pct_beat_at_trainer_scale=at_one["pct_beat"],
        half_point_scale=half, basin_scale_at_elite_frac=basin, elite_frac=ELITE_FRAC,
        falsifier_fires=bool(fires)), indent=1), encoding="utf8")
    print(f"  JSON: {out}")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    xs = [r["scale"] for r in rows if r["scale"] > 0]
    fig, ax = plt.subplots(1, 2, figsize=(13.5, 4.6))
    ax[0].semilogx(xs, [r["pct_beat"] for r in rows if r["scale"] > 0], "o-",
                   color="#c0392b", lw=1.8)
    ax[0].axvline(1.0, color="#1a7f37", lw=1.8, label="the trainer's own scale")
    ax[0].axhline(50.0, color="#8e44ad", ls=":", lw=1.2, label="half the samples")
    ax[0].set_xlabel("perturbation scale (x the trainer's warm-start sd)")
    ax[0].set_ylabel("% of samples beating the incumbent"); ax[0].legend(fontsize=7)
    ax[0].set_title("does the sampler propose anything good?", fontsize=9)
    ax[1].semilogx(xs, [r["median"] for r in rows if r["scale"] > 0], "o-",
                   color="#2471a3", lw=1.8, label="median sample")
    ax[1].semilogx(xs, [r["best"] for r in rows if r["scale"] > 0], "o--",
                   color="#7f8c8d", lw=1.2, label="best sample")
    ax[1].axhline(inc, color="#1a7f37", lw=1.8, label=f"incumbent {inc:.3f}")
    ax[1].axvline(1.0, color="#1a7f37", lw=1.0)
    ax[1].set_xlabel("perturbation scale (x the trainer's warm-start sd)")
    ax[1].set_ylabel("score"); ax[1].legend(fontsize=7)
    ax[1].set_title("and how far does the score fall?", fontsize=9)
    fig.suptitle(f"SEARCH LANDSCAPE around {tp.name} -- {at_one['pct_beat']:.0f}% of samples "
                 f"beat the incumbent at the trainer's own step size", fontsize=11.5)
    png = OUTDIR / f"search_landscape_{tp.stem}.png"
    fig.savefig(png, dpi=104, bbox_inches="tight"); plt.close(fig)
    print(f"  PICTURE: {png}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
