"""benchmark_policies.py -- ONE RUNNER, N POLICY CLASSES, ONE JUDGE.

RULE 0, stated before the build, because a benchmark runner is a theory about comparison:

    STATEMENT   The PD, windowed-PD, PD+phase, ablation and support-only experiments differ ONLY
                in their channel list and their objective. Everything else -- budget, warm start,
                training seeds, RNG seed, control cadence, plant, judge, held-out seeds -- can be
                held identical by construction, so that the named difference is the only variable
                between any two arms.

    PREDICTION  Two runs of the same class with the same settings produce the SAME held-out
                survival, to the last digit, and `p_only` reproduces `train_stand.evaluate`'s
                score on the incumbent theta bit-identically.

    FALSIFIER   (task 9's, verbatim) Two runs of the same policy class with identical settings
                produce different held-out survival -- the runner is not deterministic and no
                comparison it prints means anything. Checked by `--selftest`, which RUNS it twice
                rather than reasoning about the RNG.

WHY THIS EXISTS RATHER THAN SIX COPIES OF `train_stand.py`. Each experiment needs a trainer, a
judge, a warm start, a derived step, an elite guard and a held-out survival number. Written six
times they agree until one is edited -- the species `tools/timestep_audit.py` found with
`CTRL_EVERY` declared in three files, and the species that killed the walk port for a session
when the trainer drove an entrained oscillator the judge did not run. Numbers optimised against a
plant the judge does not run are dead at judgment.

    THE ARMS SHARE ONE PLANT, ONE TRAINER AND ONE JUDGE, OR THE COMPARISON IS NOT ONE.

THE JUDGE IS HELD-OUT SURVIVAL AND THAT IS MANDATORY, NOT PREFERABLE.
`docs/LOCOMOTION_POLICY_DESIGN.md` section 6, from `agent_logs/objective_survival.json`: near the
incumbent -- the only regime a warm-started search lives in -- the trainer's objective correlates
with survival at r = -0.162. It ranks wreckage at r = 1.000 and cannot rank two working policies
at all. So `--judge held_out` is the default and the objective is reported beside it as a
DIAGNOSTIC, never as the ranking.

    python tools/benchmark_policies.py --classes p_only,pd --budget 24x30 --seeds 3
    python tools/benchmark_policies.py --selftest
    python tools/benchmark_policies.py --classes p_only --objective support_only --tag v2
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

import policy_classes as PC                                        # noqa: E402

OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"
LOGDIR = ROOT / "agent_logs"
INCUMBENT = OUTDIR / "stand_theta.npy"
TRAINED_SEEDS = (0, 1, 2)          # what the search selects on
HELD_OUT = (3, 4, 5, 6, 7, 8, 9)   # what every comparison is judged on
JUDGE_SECS = 20.0                  # `stand_survival`'s window: long enough to see the fall


# ── THE PLANT ─────────────────────────────────────────────────────────────────────────────────
def open_world():
    """The model, the data, the port and the joint ids -- once per process."""
    import mujoco
    from world import load_body
    from stand_port import derive_stand_port, MYOBODY
    from train_stand import joint_ids
    P = derive_stand_port()
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    return mujoco, m, d, g, P, joint_ids(m, mujoco)


def _reset(m, d, mujoco, jids, seed):
    """The judge's reset, and it is the trainer's: keyframe -> seat -> nudge, in that order.

    The nudge comes AFTER the seat so a seed cannot push the body back outside the limits the
    seat just enforced -- the same order `train_stand.evaluate`, `stand_survival` and `f3_stand`
    use, from the same constant (rule 19: one perturbation, one landmark).
    """
    from train_stand import seat_in_limits, NUDGE
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    seat_in_limits(m, d, mujoco, jids)
    if seed:
        d.qpos[:] = d.qpos + np.random.default_rng(seed).normal(0.0, NUDGE, size=d.qpos.shape)
        mujoco.mj_forward(m, d)


def _angles(d):
    """pitch and roll from the free joint's quaternion -- the identical arithmetic every harness
    in this lane uses. Copied nowhere else: this is the one place it lives for this runner."""
    q = d.qpos[3:7]
    pitch = float(np.arctan2(2 * (q[0] * q[2] - q[3] * q[1]), 1 - 2 * (q[1] ** 2 + q[2] ** 2)))
    roll = float(np.arctan2(2 * (q[0] * q[1] + q[2] * q[3]), 1 - 2 * (q[1] ** 2 + q[2] ** 2)))
    return pitch, roll


def evaluate(mujoco, m, d, jids, P, pc, theta, secs, seed=0, objective="full", trace=False):
    """ONE LIFE under one policy class. Returns (score, info).

    The reward is `stand_port.stand_reward` for `full` and its support factor alone for
    `support_only`; the rollout composition is `policy_classes.rollout_score` for both, so the
    objective is the single variable between T6's two arms.
    """
    from stand_port import stand_reward
    from train_stand import joint_fracs, CTRL_EVERY
    nu = m.nu
    tgt = P["OUT pelvis_target_m"]
    obs = PC.Observer(tgt, PC.omega0(P), pc.window, CTRL_EVERY * m.opt.timestep)
    _reset(m, d, mujoco, jids, seed)
    steps = int(secs / m.opt.timestep)
    _b = lambda n: d.xpos[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, n)]
    tot, n, fell = 0.0, 0, False
    tr = {k: [] for k in ("t", "z", "comx", "comy", "jf", "r")} if trace else None
    k = 0
    for k in range(steps):
        if k % CTRL_EVERY == 0:
            z = float(d.qpos[2])
            pitch, roll = _angles(d)
            obs.push(z, pitch, roll)
            d.ctrl[:] = pc.control(theta, nu, obs.channels())
        mujoco.mj_step(m, d)
        if k % CTRL_EVERY == 0:
            z = float(d.qpos[2])
            com = d.subtree_com[0]
            foot = 0.25 * (_b("calcn_r") + _b("calcn_l") + _b("toes_r") + _b("toes_l"))
            dx, dy = float(com[0] - foot[0]), float(com[1] - foot[1])
            if z < 0.5 * tgt:
                fell = True
            fr = joint_fracs(d, jids)
            r, parts = stand_reward(z, (dx, dy), fr, False, float(np.abs(d.ctrl).mean()), P)
            # THE OBJECTIVE'S ONE VARIABLE. `support` is the only component measured to track
            # survival (+0.891 within-rung); `height` x `joints` are anti-correlated at -0.943
            # and neither relates to it. v2 keeps the informative factor and drops the gate.
            r = r if objective == "full" else parts["support"]
            tot += r
            n += 1
            if trace:
                tr["t"].append(k * m.opt.timestep); tr["z"].append(z)
                tr["comx"].append(dx); tr["comy"].append(dy)
                tr["jf"].append(float(fr.max())); tr["r"].append(r)
        if fell:
            break
    score = PC.rollout_score(tot / max(n, 1), fell, (k + 1) / steps)
    return float(score), dict(fell=fell, samples=n, trace=tr)


def score_theta(mujoco, m, d, jids, P, pc, theta, secs, seeds, objective="full"):
    """A candidate's score is the WORST of `seeds` randomized starts (CLAUDE.md: one rollout is
    a coin toss; on this exact body a 1e-6 nudge spans 6.30-9.08 s and seed 0 is the luckiest)."""
    if seeds <= 1:
        return evaluate(mujoco, m, d, jids, P, pc, theta, secs, 0, objective)[0]
    return float(min(evaluate(mujoco, m, d, jids, P, pc, theta, secs, i, objective)[0]
                     for i in range(seeds)))


def survive(mujoco, m, d, jids, P, pc, theta, secs=JUDGE_SECS, seeds=HELD_OUT):
    """HELD-OUT SURVIVAL: how long the pelvis stays above the fall bar, median over `seeds`.

    This is the same quantity `stand_survival.py` and `gravity_transfer.py` report, computed the
    same way, so a number here can be compared with one there without either re-deriving the
    other's (rule 19). It is the ONLY ranking this runner prints.
    """
    from train_stand import CTRL_EVERY
    nu, tgt = m.nu, P["OUT pelvis_target_m"]
    out = []
    for s in seeds:
        obs = PC.Observer(tgt, PC.omega0(P), pc.window, CTRL_EVERY * m.opt.timestep)
        _reset(m, d, mujoco, jids, s)
        steps, t_end = int(secs / m.opt.timestep), secs
        for k in range(steps):
            if k % CTRL_EVERY == 0:
                z = float(d.qpos[2])
                pitch, roll = _angles(d)
                obs.push(z, pitch, roll)
                d.ctrl[:] = pc.control(theta, nu, obs.channels())
            mujoco.mj_step(m, d)
            if k % CTRL_EVERY == 0 and float(d.qpos[2]) < 0.5 * tgt:
                t_end = k * m.opt.timestep
                break
        out.append(t_end)
    return float(np.median(out)), [float(v) for v in out]


# ── THE SEARCH: train_stand's CEM, with the class as a parameter ──────────────────────────────
def derive_step(mujoco, m, d, jids, P, pc, mu, sd, secs, seeds, elite_frac, rng, objective,
                k=None, pop=24):
    """MEASURE the step this policy's own landscape supports (train_stand.derive_step, verbatim
    in its logic and generalised over the class).

    Nothing is chosen: the LADDER is powers of ten, the CRITERION is the search's own elite
    fraction, and if no rung meets it the smallest is used WITH A REFUSAL PRINTED rather than an
    extrapolation off the end of a measured curve.

    THE SAMPLE COUNT IS THE SEARCH'S OWN POPULATION, NOT `train_stand`'s k = 6, AND THAT IS A
    REPAIR RATHER THAN A PREFERENCE. The criterion is `elite/pop` = 4/24 = 0.167; at k = 6 the
    finest fraction measurable is 1/6 = 0.167, so a rung is selected or rejected BY ONE SAMPLE
    and the ladder is a coin toss at exactly the resolution the decision needs. Measured on the
    smoke run: pd_phase's ladder came back 0%, 0%, 50%, 17%, 83%, 67% -- non-monotonic, and the
    rule (largest rung meeting the criterion) then chose x0.01, two decades above where the
    improvements actually are. Taking k = pop measures the fraction at the sample size the search
    itself draws each turn, so the criterion is evaluated at its own resolution. That is read off
    the search's structure, not chosen -- and it is the same species of defect as thresholding on
    a quantile of the population you measure.
    """
    k = int(pop) if k is None else int(k)
    ladder = (1.0, 1e-1, 1e-2, 1e-3, 1e-4, 1e-5)
    nu = m.nu
    inc = score_theta(mujoco, m, d, jids, P, pc, mu, secs, seeds, objective)
    report, chosen = [], None
    for s in ladder:
        hits = 0
        for _ in range(k):
            cand = mu + rng.normal(0.0, 1.0, size=mu.shape) * sd * s
            if pc.has_a0:
                cand[:nu] = np.clip(cand[:nu], 0.0, 1.0)
            if score_theta(mujoco, m, d, jids, P, pc, cand, secs, seeds, objective) > inc:
                hits += 1
        report.append((s, hits / k))
        if chosen is None and hits / k >= elite_frac:
            chosen = s
    return (sd * (chosen if chosen is not None else ladder[-1]),
            dict(incumbent=float(inc), ladder=report, chosen=chosen,
                 elite_frac=float(elite_frac), refused=chosen is None))


def train(mujoco, m, d, jids, P, pc, mu, secs, turns, pop, seeds, objective, log=print):
    """CEM with the three repairs that opened the search wall, all ON:

      * THE INCUMBENT IS ALWAYS A CANDIDATE (`cand[0] = mu`) -- without it a warm start can end
        strictly worse than not training, and did: seeded with a theta standing at 101.9% of
        target, turn 0 of a 24-turn run opened at 48%.
      * THE ELITE-MEAN GUARD -- the centre may not move downhill. Without it the elite is
        {mu, three worse samples} and `el.mean(0)` destroys the distribution on turn 0.
      * THE DERIVED STEP + a spread floor expressed as a FRACTION of the spread actually used.
        A flat 1e-3 floor swamps a derived sd of 7.5e-6 by 133x.

    They are not flags here. `train_stand` keeps them optional so its historical arms remain
    valid controls; this runner has no history to preserve and every arm it runs is new, so
    running any of them off would be running an arm nobody asked a question about.
    """
    nu = m.nu
    sd = pc.build_sd(nu) * 0.5          # the warm-start halving: "what is near the best known"
    elite = max(3, pop // 5)
    rng = np.random.default_rng(0)      # THE SAME STREAM FOR EVERY CLASS
    log(f"  deriving the step (criterion: >= {elite}/{pop} = {elite/pop:.2f} of samples must "
        f"beat the incumbent)")
    sd, step_report = derive_step(mujoco, m, d, jids, P, pc, mu, sd, secs, seeds,
                                  elite / pop, rng, objective, pop=pop)
    for s, frac in step_report["ladder"]:
        log(f"     x{s:<8g} {100*frac:>5.0f}% beat the incumbent"
            + ("   <- CHOSEN" if s == step_report["chosen"] else ""))
    if step_report["refused"]:
        log("     NO RUNG MET THE CRITERION -- the smallest tried is used and this line is the "
            "refusal.\n     The basin is narrower than 1e-5 x the cold sd: a finding about the "
            "policy, not a step to trust.")
    sd_floor = 1e-3 * sd.copy()
    dim = mu.size
    hist, best = [], (-np.inf, mu.copy())
    # THE JUDGE IS READ EVERY TURN, AND IT IS NEVER THE SELECTION. Two different numbers get
    # confused constantly in this lane and they are separated here on purpose:
    #
    #   `best`  -- the theta with the best OBJECTIVE. This is what the pipeline DELIVERS, so it
    #              is what the arms are ranked on. Selected on the training seeds only.
    #   `ceil`  -- the best held-out survival seen at ANY turn. This is a CAPABILITY CEILING and
    #              it is SELECTED ON THE JUDGE, so it is biased upward and may never be used to
    #              rank an arm. It exists to separate two very different failures: "this class
    #              cannot stand longer" from "this class can, and the objective cannot find it".
    #              The design doc already measured that the objective's correlation with survival
    #              near the incumbent is -0.162, so the second failure is the one to expect.
    ceil = (-np.inf, None, -1)
    log(f"{'turn':>5}{'best':>10}{'mean':>10}{'elmean':>10}{'mu':>7}{'bestobj':>9}{'surv':>8}")
    for turn in range(turns):
        cand = rng.normal(mu, sd, size=(pop, dim))
        cand[0] = mu
        if pc.has_a0:
            cand[:, :nu] = np.clip(cand[:, :nu], 0.0, 1.0)
        scores = np.array([score_theta(mujoco, m, d, jids, P, pc, c, secs, seeds, objective)
                           for c in cand])
        order = np.argsort(-scores)
        el = cand[order[:elite]]
        el_mean = el.mean(0)
        em_score = score_theta(mujoco, m, d, jids, P, pc, el_mean, secs, seeds, objective)
        moved = em_score > scores[0]        # scores[0] IS the incumbent's -- read, never re-run
        mu = el_mean if moved else mu
        sd = el.std(0) + sd_floor
        if float(scores[order[0]]) > best[0]:
            best = (float(scores[order[0]]), cand[order[0]].copy())
        sv, _ = survive(mujoco, m, d, jids, P, pc, cand[order[0]])
        if sv > ceil[0]:
            ceil = (float(sv), cand[order[0]].copy(), turn)
        hist.append(dict(turn=turn, best=float(scores[order[0]]), mean=float(scores.mean()),
                         elite_mean=float(em_score), moved=bool(moved), survival=float(sv)))
        log(f"{turn:>5}{scores[order[0]]:>10.3f}{scores.mean():>10.3f}{em_score:>10.3f}"
            f"{'moved' if moved else 'HELD':>7}{best[0]:>9.3f}{sv:>7.2f}s")
    return best[1], best[0], hist, step_report, ceil


# ── ONE ARM, END TO END ───────────────────────────────────────────────────────────────────────
def run_class(spec):
    """Train and judge ONE class. Runs in its own process; returns a plain dict."""
    name, objective, budget, seeds, secs, tag, warm = (
        spec["name"], spec["objective"], spec["budget"], spec["seeds"], spec["secs"],
        spec["tag"], spec["warm"])
    pop, turns = budget
    lines = []
    log = lines.append
    t0 = time.time()
    mujoco, m, d, g, P, jids = open_world()
    nu = m.nu
    pc = PC.get(name)
    src = np.load(INCUMBENT) if warm else None
    src_class = PC.get("p_only") if warm else None
    mu = pc.build_theta(nu, src, src_class)
    pc.decode_theta(mu, nu)              # the shape guard, at the point the artifact is minted

    log(f"\n=== {name}  [{objective}]  {pc.note}")
    log(f"  channels {pc.channels}  a0={pc.has_a0}  window={pc.window} tick(s) = "
        f"{pc.window * 20 * m.opt.timestep * 1000:.0f} ms")
    log(f"  theta {mu.size} numbers = {pc.n_blocks()} blocks x {nu} muscles")
    log(f"  warm start: " + ("the incumbent, matched by channel NAME; every channel this class "
                             "adds starts at ZERO gain" if warm else "COLD"))
    log(f"  budget {pop}x{turns} = {pop*turns} candidates x worst-of-{seeds} starts x {secs:g} s")

    surv_before, per_before = survive(mujoco, m, d, jids, P, pc, mu)
    obj_before = score_theta(mujoco, m, d, jids, P, pc, mu, secs, seeds, objective)
    log(f"  AT THE WARM START: held-out survival {surv_before:.2f} s, objective {obj_before:.4f}")

    theta, obj_after, hist, step_report, ceil = train(mujoco, m, d, jids, P, pc, mu, secs, turns,
                                                      pop, seeds, objective, log)
    surv_after, per_after = survive(mujoco, m, d, jids, P, pc, theta)
    # THE TRAINED-SEED NUMBER TOO, so the train/test gap is visible per arm rather than inferred.
    surv_train, _ = survive(mujoco, m, d, jids, P, pc, theta, seeds=TRAINED_SEEDS)
    log(f"  AFTER {turns} turns: held-out survival {surv_after:.2f} s "
        f"({surv_after - surv_before:+.2f} s), objective {obj_after:.4f} "
        f"({obj_after - obj_before:+.4f})")
    log(f"  train/test gap: trained seeds {surv_train:.2f} s vs held-out {surv_after:.2f} s "
        f"= {surv_train - surv_after:+.2f} s")
    log(f"  CAPABILITY CEILING (best held-out survival at ANY turn, turn {ceil[2]}): "
        f"{ceil[0]:.2f} s -- SELECTED ON THE JUDGE, so it is biased upward and ranks nothing. "
        f"It separates 'this class cannot stand longer' from 'the objective cannot find it'.")

    out = OUTDIR / f"bench_{tag}_{name}.npy"
    np.save(out, theta)
    if ceil[1] is not None:
        np.save(OUTDIR / f"bench_{tag}_{name}_ceiling.npy", ceil[1])
    row = dict(name=name, objective=objective, channels=list(pc.channels), has_a0=pc.has_a0,
               window=pc.window, obs_dim=pc.obs_dim(), n_blocks=pc.n_blocks(),
               theta_numbers=int(mu.size), pop=pop, turns=turns, train_seeds=seeds, secs=secs,
               warm=warm, theta_path=str(out),
               survival_before=surv_before, survival_after=surv_after,
               survival_per_seed_before=per_before, survival_per_seed_after=per_after,
               survival_trained_seeds=surv_train,
               survival_ceiling=float(ceil[0]), survival_ceiling_turn=int(ceil[2]),
               objective_before=obj_before, objective_after=obj_after,
               step_chosen=step_report["chosen"], step_refused=step_report["refused"],
               step_ladder=[[float(s), float(f)] for s, f in step_report["ladder"]],
               history=hist, wall_s=time.time() - t0, log="\n".join(lines))
    (LOGDIR / f"bench_{tag}_{name}.json").write_text(json.dumps(row, indent=1), encoding="utf8")
    return row


# ── THE RUNNER'S OWN FALSIFIERS ───────────────────────────────────────────────────────────────
def selftest() -> int:
    """THREE CHECKS, and the runner has no standing until all three pass.

    1. `p_only` + the incumbent theta reproduces `train_stand.evaluate` BIT-IDENTICALLY. If it
       does not, this file is a reimplementation of the policy rather than the policy, and every
       arm below is being compared against something the judge never ran.
    2. `pd` with its rate gains at zero reproduces `p_only` bit-identically -- which is what
       licenses the warm start to be called "the same point".
    3. TASK 9'S FALSIFIER, RUN RATHER THAN REASONED ABOUT: the same class trained twice with the
       same settings gives the same held-out survival. A tiny budget, because determinism does
       not need a long run to show and a long run would hide the answer behind an hour.
    """
    mujoco, m, d, g, P, jids = open_world()
    nu = m.nu
    from train_stand import evaluate as train_eval
    theta = np.load(INCUMBENT)
    p_only, pd = PC.get("p_only"), PC.get("pd")
    print("\nBENCHMARK RUNNER -- SELFTEST")
    print("=" * 92)

    ok = True
    print("  1. p_only == train_stand.evaluate (the incumbent's own plant), 3 seeds x 3.0 s")
    for s in (0, 1, 2):
        a = train_eval(m, d, mujoco, theta, P, 3.0, seed=s)[0]
        b = evaluate(mujoco, m, d, jids, P, p_only, theta, 3.0, s)[0]
        same = abs(a - b) < 1e-12
        ok &= same
        print(f"     seed {s}: train_stand {a:.12f}   runner {b:.12f}   "
              + ("identical" if same else f"DIFFER by {abs(a-b):.3e}  <- FALSIFIER 1 FIRES"))

    print("  2. pd with ZERO rate gains == p_only (what makes the warm start one point)")
    pd_theta = pd.build_theta(nu, theta, p_only)
    added = [c for c in pd.channels if c not in p_only.channels]
    blk = pd.blocks(pd_theta, nu)
    print(f"     pd theta {pd_theta.size} numbers vs p_only {theta.size}. The added channels "
          f"{added} are all zero: {all(bool(np.all(blk[c] == 0.0)) for c in added)}")
    for s in (0, 2):
        a = evaluate(mujoco, m, d, jids, P, p_only, theta, 3.0, s)[0]
        b = evaluate(mujoco, m, d, jids, P, pd, pd_theta, 3.0, s)[0]
        same = abs(a - b) < 1e-12
        ok &= same
        print(f"     seed {s}: p_only {a:.12f}   pd(zeroed) {b:.12f}   "
              + ("identical" if same else f"DIFFER by {abs(a-b):.3e}  <- FALSIFIER 2 FIRES"))

    print("  3. TASK 9'S FALSIFIER: the same class trained twice must judge the same")
    runs = []
    for i in range(2):
        mu = pd.build_theta(nu, theta, p_only)
        th, sc, _h, _r, _c = train(mujoco, m, d, jids, P, pd, mu, 1.0, 2, 6, 1, "full",
                                   log=lambda *_a, **_k: None)
        sv, _ = survive(mujoco, m, d, jids, P, pd, th, secs=6.0, seeds=(3, 4, 5))
        runs.append((sc, sv, float(np.abs(th).sum())))
        print(f"     run {i}: objective {sc:.12f}   held-out survival {sv:.4f} s   "
              f"|theta|_1 {runs[-1][2]:.9f}")
    det = runs[0] == runs[1]
    ok &= det
    print("     -> " + ("identical: the runner is deterministic and task 9's falsifier does NOT "
                        "fire." if det else
                        "DIFFERENT -- TASK 9'S FALSIFIER FIRES. The runner is not deterministic "
                        "and no comparison it prints means anything."))
    print("=" * 92)
    print("  SELFTEST " + ("PASS -- the runner is the policy, not a copy of it." if ok else
                           "FAIL. Nothing below this line may be believed."))
    return 0 if ok else 1


def draw(rows, tag, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rows = sorted(rows, key=lambda r: -r["survival_after"])
    n = len(rows)
    fig, ax = plt.subplots(1, 3, figsize=(16.5, 0.30 * max(n, 8) + 3.6))
    y = np.arange(n)
    base = [r["survival_before"] for r in rows]
    after = [r["survival_after"] for r in rows]
    ax[0].barh(y, after, 0.52, color="#2471a3", label="trained (the ranking)")
    ax[0].barh(y, [r["survival_ceiling"] for r in rows], 0.52, color="#2471a3", alpha=0.22,
               label="ceiling (selected on the judge)")
    ax[0].axvline(base[0] if base else 0.0, color="#c0392b", lw=1.8,
                  label=f"warm start {base[0]:.2f} s -- every arm")
    ax[0].set_yticks(y)
    ax[0].set_yticklabels([f"{r['name']}" for r in rows], fontsize=7.5)
    ax[0].invert_yaxis(); ax[0].set_xlabel("held-out survival (s)"); ax[0].legend(fontsize=6.5)
    ax[0].set_title("THE ONLY RANKING: held-out survival", fontsize=9)
    for r in rows:
        h = r["history"]
        ax[1].plot([x["turn"] for x in h], [x.get("survival", np.nan) for x in h], lw=1.2,
                   label=r["name"])
    ax[1].axhline(base[0] if base else 0.0, color="#c0392b", lw=1.6, ls="--")
    ax[1].set_xlabel("turn"); ax[1].set_ylabel("held-out survival of the turn's best (s)")
    ax[1].legend(fontsize=6, ncol=2)
    ax[1].set_title("does the search ever find a longer stand?", fontsize=9)
    ax[2].scatter([r["objective_after"] for r in rows], after, s=40, color="#c0392b")
    for r in rows:
        ax[2].annotate(r["name"], (r["objective_after"], r["survival_after"]), fontsize=6,
                       xytext=(3, 3), textcoords="offset points")
    ax[2].set_xlabel("trainer objective"); ax[2].set_ylabel("held-out survival (s)")
    ax[2].set_title("objective vs the judge -- near the incumbent r was -0.162", fontsize=9)
    fig.suptitle(f"POLICY-CLASS BENCHMARK [{tag}] -- {n} arms, one plant, one trainer, "
                 f"one judge (held-out seeds {HELD_OUT[0]}..{HELD_OUT[-1]}, {JUDGE_SECS:.0f} s)",
                 fontsize=11.5)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(path, dpi=104, bbox_inches="tight"); plt.close(fig)


def main() -> int:
    a = sys.argv
    if "--selftest" in a:
        return selftest()
    names = [s.strip() for s in
             (a[a.index("--classes") + 1] if "--classes" in a else "p_only,pd").split(",")
             if s.strip()]
    budget = a[a.index("--budget") + 1] if "--budget" in a else "24x30"
    pop, turns = (int(v) for v in budget.lower().split("x"))
    seeds = int(a[a.index("--seeds") + 1]) if "--seeds" in a else len(TRAINED_SEEDS)
    secs = float(a[a.index("--secs") + 1]) if "--secs" in a else 12.0
    objective = a[a.index("--objective") + 1] if "--objective" in a else "full"
    tag = a[a.index("--tag") + 1] if "--tag" in a else "b1"
    jobs = int(a[a.index("--jobs") + 1]) if "--jobs" in a else min(len(names), 12)
    cold = "--cold" in a
    if objective not in PC.OBJECTIVES:
        raise SystemExit(f"--objective must be one of {PC.OBJECTIVES}. A third would be a sweep "
                         f"where a derivation belongs (rule 1). Refusing.")
    judge = a[a.index("--judge") + 1] if "--judge" in a else "held_out"
    if judge != "held_out":
        raise SystemExit(
            "--judge held_out is the only judge this runner has, and that is not an omission. "
            "Near the incumbent the trainer's objective correlates with survival at r = -0.162 "
            "(agent_logs/objective_survival.json), so ranking policy classes by it is ranking "
            "them by a number that does not track standing where the comparison happens. "
            "Refusing.")
    for n in names:
        PC.get(n)                       # refuse an unknown arm BEFORE paying for a single rollout
    if not INCUMBENT.exists() and not cold:
        raise SystemExit(f"no {INCUMBENT} -- a warm start needs an incumbent. Refusing to warm-"
                         f"start from nothing (rule 20).")

    specs = [dict(name=n, objective=objective, budget=(pop, turns), seeds=seeds, secs=secs,
                  tag=tag, warm=not cold) for n in names]
    print(f"\nPOLICY-CLASS BENCHMARK [{tag}] -- {len(names)} arm(s), objective {objective}")
    print("=" * 92)
    print(f"  budget {pop}x{turns} per arm, worst-of-{seeds} starts x {secs:g} s, "
          f"warm start {'OFF (cold)' if cold else 'the incumbent'}")
    print(f"  judged on HELD-OUT seeds {HELD_OUT} at {JUDGE_SECS:.0f} s -- the objective is "
          f"printed as a diagnostic and ranks nothing")
    print(f"  arms: {', '.join(names)}")
    print(f"  {jobs} process(es); every arm shares the RNG seed, the warm start, the plant, the "
          f"trainer and the judge")
    t0 = time.time()
    if jobs > 1 and len(specs) > 1:
        import multiprocessing as mp
        ctx = mp.get_context("spawn")
        with ctx.Pool(processes=min(jobs, len(specs))) as pool:
            rows = pool.map(run_class, specs)
    else:
        rows = [run_class(s) for s in specs]
    for r in rows:
        print(r["log"])

    rows = sorted(rows, key=lambda r: -r["survival_after"])
    print("\n" + "=" * 118)
    print(f"  {'class':<18}{'obs':>5}{'theta':>8}{'warm s':>9}{'held-out s':>12}{'delta':>9}"
          f"{'gap':>8}{'ceiling s':>11}{'@turn':>7}{'objective':>12}{'wall':>8}")
    print("-" * 118)
    for r in rows:
        print(f"  {r['name']:<18}{r['obs_dim']:>5}{r['theta_numbers']:>8}"
              f"{r['survival_before']:>8.2f}s{r['survival_after']:>11.2f}s"
              f"{r['survival_after']-r['survival_before']:>+9.2f}"
              f"{r['survival_trained_seeds']-r['survival_after']:>+8.2f}"
              f"{r['survival_ceiling']:>10.2f}s{r['survival_ceiling_turn']:>7}"
              f"{r['objective_after']:>12.4f}{r['wall_s']/60:>7.1f}m")
    print("=" * 118)
    print(f"  'held-out s' RANKS THE ARMS: the survival of the theta the search DELIVERS "
          f"(selected on the objective, seeds {TRAINED_SEEDS}).")
    print(f"  'ceiling s' is the best held-out survival seen at ANY turn -- SELECTED ON THE "
          f"JUDGE, biased upward, ranks nothing.")
    print(f"  A large ceiling over a small delta means the class CAN stand longer and the "
          f"objective cannot find it.")
    best = rows[0]
    print(f"  BEST HELD-OUT: {best['name']} at {best['survival_after']:.2f} s "
          f"(warm start {best['survival_before']:.2f} s for every arm)")
    out = LOGDIR / f"benchmark_{tag}.json"
    LOGDIR.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dict(
        tag=tag, objective=objective, pop=pop, turns=turns, train_seeds=seeds, secs=secs,
        held_out_seeds=list(HELD_OUT), judge_secs=JUDGE_SECS, warm=not cold,
        wall_s=time.time() - t0,
        rows=[{k: v for k, v in r.items() if k != "log"} for r in rows]), indent=1),
        encoding="utf8")
    print(f"  JSON: {out}")
    png = OUTDIR / f"benchmark_{tag}.png"
    draw(rows, tag, png)
    print(f"  PICTURE: {png}")
    print(f"  TOTAL WALL: {(time.time()-t0)/60:.1f} min")
    return 0


if __name__ == "__main__":
    sys.exit(main())
