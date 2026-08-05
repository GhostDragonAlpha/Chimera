"""train_stand.py -- TRAIN THE STAND PORT, and only the stand port. A picture every turn.

The root branch closes at rest (+0.7%): the ground faithfully carries a HEAP. This trains it to
carry something UPRIGHT. Nothing else is optimised -- no travel, no tracking, no speed. The reward
is `stand_port.stand_reward`, whose every term traces to a published number.

WHY CEM AND NOT PPO. The question here is not "what policy" but "does a policy exist that holds
this body up". CEM answers that with a few hundred rollouts and no gradient, no value function and
no hyper-parameters to sweep -- which matters, because a sweep is an admission the derivation was
not done (rule 1). The search space is DERIVED from the body: one activation per muscle, plus a
proportional feedback on the two quantities standing is actually about (pelvis height error and
lean). That is not a guess at an architecture; it is the inverted pendulum written down.

EVERY TURN ENDS IN A PICTURE. `docs/THE_WORKFLOW.md` section 0: a turn that ends in "it is still
running" is not a turn. Six hours of a converging curve hid a body that was falling over.

    python tools/train_stand.py --turns 6 --pop 24 --secs 1.2
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body
from stand_port import derive_stand_port, stand_reward
# `joint_load` is imported LAZILY inside `_load_tables`, not here: it imports joint_ids and
# seat_in_limits from THIS module, so a top-level import either way is a cycle. Python reports
# it as "cannot import name 'joint_ids' from partially initialized module", which names the
# symbol and not the loop -- worth the comment so the next person does not re-add the line.

MYOBODY = ROOT / "external" / "myo_sim" / "body" / "myobody.xml"
OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"
# ONE QUANTITY, ONE LANDMARK (rule 19). The randomized-start nudge lives HERE and
# `tools/stand_survival.py` imports it, so the trainer and the instrument that judges it cannot
# perturb by two different amounts and call the disagreement a result.
NUDGE = 1e-6
# THE CONTROL CADENCE, and this is its ONE home. `tools/timestep_audit.py` found the same
# constant declared three times -- here as a bare `k % 20` literal, in f3_stand.py, and in
# train_walk.py -- across files that must agree or the trainer and the judge are running
# different plants. They all said 20 and the audit found no mismatch, which is the good case
# and is also exactly how this rots: three copies agree until one is edited. `f3_stand` and
# `train_walk` now import it from here (both already import from this module, so no cycle).
# THE CADENCE IS DECLARED, NOT DESCRIBED. `tools/timestep_audit.py` reads the line below and
# checks it against `CTRL_EVERY * m.opt.timestep` for the model this file loads. It arrived at
# that design the hard way -- four runs of inferring the subject from English, four different
# misattributions, every one caught by its control -- and the rule it settled on is the one
# `story/folding.py` already states: DECLARED, never inferred, because a subject you infer is
# a subject that can be wrong. Prose beside a constant is now reported and never judged.
# cadence: 20 ms, 50 Hz
CTRL_EVERY = 20

# THE PRIMARY LEG JOINTS. The model also carries `knee_angle_*_beta_*`, `*_translation*` and
# `*_rotation*` -- the coupled DOFs of the knee's four-bar mechanism, driven by knee_angle, not
# independently actuated. Grading the body on those would be grading it on the consequences of a
# joint it already has, twice. One quantity, one landmark (rule 19).
PRIMARY = ("hip_flexion", "hip_adduction", "hip_rotation", "knee_angle",
           "ankle_angle", "subtalar_angle", "mtp_angle",
           # THE TRUNK, added when the legs plateaued at 36%. Its joints were never in the
           # PRIMARY list, so `joint_frac` never graded them and `seat_in_limits` never seated
           # them: 47 kg of body above the pelvis, ungraded and unseated, for this entire session.
           "flex_extension", "axial_rotation", "lat_bending",
           "L1_L2_FE", "L1_L2_LB", "L1_L2_AR", "L2_L3_FE", "L2_L3_LB", "L2_L3_AR",
           "L3_L4_FE", "L3_L4_LB", "L3_L4_AR", "L4_L5_FE", "L4_L5_LB", "L4_L5_AR")


def joint_ids(m, mujoco):
    """Every primary leg joint and its published range, read from the model. No defaults."""
    out = []
    for j in range(m.njnt):
        n = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, j) or ""
        base = n.rsplit("_", 1)[0] if n.endswith(("_r", "_l")) else n
        if base in PRIMARY and m.jnt_limited[j]:
            lo, hi = float(m.jnt_range[j][0]), float(m.jnt_range[j][1])
            out.append((int(m.jnt_qposadr[j]), 0.5 * (lo + hi), max(0.5 * (hi - lo), 1e-6), n))
    if not out:
        raise SystemExit("no primary leg joints found -- refusing to grade joints on nothing.")
    return out


def seat_in_limits(m, d, mujoco, jids):
    """Project the keyframe into the body's OWN declared joint ranges. Measured, not invented.

    THE DEFECT THIS FIXES, found 2026-08-02 by measuring the keyframe instead of theorising about
    the reward. At `mj_resetDataKeyframe` -- no control, no load, nothing applied -- the pose is
    ALREADY OUTSIDE the limits the same file declares:

        hip_flexion_l   -40.4 deg  against  -30..+120   -> 10.4 deg BEYOND the extension stop
        knee_angle_l     -3.6 deg  against    0..+120   -> hyperextended
        knee_angle_r     -1.3 deg  against    0..+120   -> hyperextended
        jmax = 1.139

    Every run in this project has started in violation of the body's own constraints. The joints
    term was not too sharp; it was correctly reporting that the body begins broken, and no policy
    could reach a state where the term is not near-zero. THE REWARD WAS NEVER THE DEFECT.

    This is not tuning a tolerance until a check passes -- the forbidden move. It changes nothing
    about the limits and nothing about the reward. It enforces a constraint `myobody.xml` already
    declares and its own keyframe violates, which is the narrowest possible correction: the pose
    moves by 10.4 deg at one hip and under 4 deg at two knees, and every other joint is untouched.
    """
    for adr, c, h, _ in jids:
        d.qpos[adr] = float(np.clip(d.qpos[adr], c - h, c + h))
    mujoco.mj_forward(m, d)


def joint_frac(d, jids):
    """How close the worst joint is to its limit. 0 = mid-range, 1 = at the stop.

    THIS WAS HARDCODED 0.0 FOR THE FIRST THREE TURNS, so the `joints` factor of stand_reward was
    exp(0) = 1.0 always: a term in a derived reward silently doing nothing, and the body was free
    to fling a limb to its stop at no cost. Named in the previous commit rather than found later.
    """
    return max(abs(float(d.qpos[adr]) - c) / h for adr, c, h, _ in jids)


def joint_fracs(d, jids):
    """EVERY graded joint's fraction of its range, in `jids` order. No max, nothing thrown away.

    `joint_frac` above returns the max of exactly this vector. The max is the right number for a
    HEADLINE ("how bad is the worst joint") and the wrong number for a REWARD: it reports nothing
    about the other 28 joints, so a candidate that pulls five of them off their stops scores
    identically to one that does not. `stand_port.joints_factor` consumes this vector; the
    derivation of why a sum and not a max is in that docstring.
    """
    return np.array([abs(float(d.qpos[adr]) - c) / h for adr, c, h, _ in jids], dtype=float)


def joint_frac_named(d, jids):
    """The same number, and WHICH JOINT IT IS. Returns `(frac, name)`.

    `joint_frac` maxes over 30-odd joints and returns a scalar -- and a scalar that moves for
    reasons you cannot attribute is the shape of measurement this project keeps getting caught
    by (rule 19, one quantity one landmark). With the trunk ligaments in, `jmax` alone cannot
    distinguish the trunk membrane's falsifier 1 (the LUMBAR still goes through its stop, the
    derived structure is insufficient) from a completely different joint taking the load. The
    name was always in `jids`; it was being thrown away at the `max()`.
    """
    return max(((abs(float(d.qpos[adr]) - c) / h, n) for adr, c, h, n in jids),
               key=lambda p: p[0])


_LOAD_TABLES = {}


def _load_tables(m, d, mujoco, jids):
    """(limit_overload, capacity, joint-id -> name, primary set) for the `load` arm. Measured ONCE per process.

    `joint_capacity` sweeps every graded joint at full activation -- ~0.5 s and a full
    `mj_resetData` per sample, which is fine once and ruinous inside a rollout that runs 24
    candidates x 3 seeds x 40 turns. Cached on the model's own shape key, the same discipline
    `walk_port.muscle_groups` uses, so two bodies cannot read one another's numbers.
    """
    key = f"{m.nu}x{m.njnt}"
    if key not in _LOAD_TABLES:
        from joint_load import joint_capacity, limit_overload
        _LOAD_TABLES[key] = (
            limit_overload,                       # bound once, not imported in the hot loop
            joint_capacity(m, d, mujoco, jids),
            {j: (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, j) or "")
             for j in range(m.njnt)},
            {n for _, _, _, n in jids})
    return _LOAD_TABLES[key]


def evaluate(m, d, mujoco, theta, P, secs, seed=0, frames=0, joints="hinge"):
    """One life under a candidate. Returns (score, trace, pics).

    `joints` selects the JOINTS TERM'S SHAPE and exists so the change to it has a control:
    "hinge" is the derived per-joint sum (`stand_port.joints_factor`), "retired" is the
    max-then-gaussian it replaced (`stand_port.retired_joints_factor`). Everything else about
    the two arms -- budget, warm start, seeds, window, RNG stream, plant -- is identical, so the
    shape is the single variable. Three coupled changes is a three-body problem with no
    attributable answer (CLAUDE.md); this is the same discipline `--blocks 3|4` bought for the
    roll term one commit earlier.

    theta = [a0 (nu), k_h (nu), k_p (nu)] -- a baseline activation plus proportional feedback on
    pelvis HEIGHT ERROR and PITCH. Those two are not chosen: they are what an inverted pendulum
    has (a height it must hold and a lean that will topple it), and theStance publishes the
    fall rate that makes the second one urgent.


    `seed` WAS A DEAD PARAMETER UNTIL 2026-08-04, and that is the defect this docstring exists
    to name. It sat in the signature and appeared NOWHERE in the body: every caller that passed
    a seed got the identical deterministic rollout, so an interface that reads as "N randomized
    starts" delivered one. `tools/stand_survival.py` then measured what that cost -- a nudge of
    1e-6 on qpos moves survival from 6.30 s to 9.08 s (SPREAD 2.780 s over 10 seeds), and the
    UNPERTURBED start is the LUCKIEST of the ten. So the trainer was scoring every candidate on
    the single most flattering initial condition available, which is the exact shape of the
    fraud CLAUDE.md already records: the 13.52-body-length champion that lost 5.5 body lengths
    to a one-micron nudge. One rollout is a coin toss; a dead seed parameter is a coin toss
    wearing the costume of a measurement.
    """
    nu = m.nu
    jids = joint_ids(m, mujoco)
    if joints == "load":
        _OVL_FN, _CAP, _JNAME, _PRIM = _load_tables(m, d, mujoco, jids)
    # FOUR BLOCKS: baseline, height gain, pitch gain, ROLL gain. The roll block is new
    # (2026-08-04) and the trainer gained it in the SAME commit as the parser formula --
    # the lesson this session paid for twice, in the walk port: a number optimised against
    # a plant the judge does not run is dead at judgment. A 3-block theta still works and
    # is bit-identical to the old formula, because kr is then zeros.
    a0, kh, kp = theta[:nu], theta[nu:2 * nu], theta[2 * nu:3 * nu]
    kr = theta[3 * nu:4 * nu] if theta.size >= 4 * nu else np.zeros(nu)
    # SIX BLOCKS: the CoM feedback arm (2026-08-04). kx, ky multiply the CoM offset from the
    # foot-polygon centre -- the base-of-support margins lateral stability is about. The arm is
    # trained with `--blocks 6` and the 4-block incumbent as init; a 4-block theta never enters
    # this branch, so the P-only control stays bit-identical (the same discipline `--blocks 3|4`
    # bought for the roll term).
    kx = theta[4 * nu:5 * nu] if theta.size >= 5 * nu else np.zeros(nu)
    ky = theta[5 * nu:6 * nu] if theta.size >= 6 * nu else np.zeros(nu)
    n_com = theta.size >= 5 * nu
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    seat_in_limits(m, d, mujoco, jids)      # the body may not START outside its own stops
    tgt = P["OUT pelvis_target_m"]
    dt = CTRL_EVERY * m.opt.timestep      # control period: 20 ms at 50 Hz
    prev = None
    if seed:
        # THE NUDGE, and it is not a knob: 1e-6 is the smallest perturbation that is
        # unambiguously beneath meaning. theHuman's gait envelope has a grain of 4.16 deg
        # = 7.3e-2 rad, so a microradian is 73,000x below the finest angle this world can
        # resolve. Applied AFTER the seat, so a seed cannot push the body back outside the
        # limits the line above just enforced.
        d.qpos[:] = d.qpos + np.random.default_rng(seed).normal(0.0, NUDGE, size=d.qpos.shape)
        mujoco.mj_forward(m, d)
    steps = int(secs / m.opt.timestep)
    grab = set(np.linspace(0, steps - 1, frames).astype(int)) if frames else set()
    ren = mujoco.Renderer(m, height=240, width=320) if frames else None
    tr = {"t": [], "z": [], "comx": [], "comy": [], "r": [], "jf": []}
    pics, tot, n, fell = [], 0.0, 0, False
    for k in range(steps):
        if k % CTRL_EVERY == 0:
            z = float(d.qpos[2])
            q = d.qpos[3:7]
            pitch = float(np.arctan2(2 * (q[0] * q[2] - q[3] * q[1]), 1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            roll = float(np.arctan2(2 * (q[0] * q[1] + q[2] * q[3]),
                                     1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            z_err = tgt - z
            u = a0 + kh * z_err + kp * pitch + kr * roll
            if n_com:
                # CoM BoS feedback, read at CONTROL time: xpos/subtree_com are consistent with
                # the qpos the controller is about to act on (the same convention the reward
                # branch uses one step later -- a plot's origin is a measurement, rule 19).
                _b = lambda n: d.xpos[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, n)]
                _foot = 0.25 * (_b("calcn_r") + _b("calcn_l") + _b("toes_r") + _b("toes_l"))
                cdx = float(d.subtree_com[0][0] - _foot[0])
                cdy = float(d.subtree_com[0][1] - _foot[1])
                u = u + kx * cdx + ky * cdy
            d.ctrl[:] = np.clip(u, 0.0, 1.0)
            prev = {"z": z, "pitch": pitch, "roll": roll}
        mujoco.mj_step(m, d)
        if k in grab and ren is not None:
            ren.update_scene(d); pics.append(ren.render().copy())
        if k % CTRL_EVERY == 0:
            z = float(d.qpos[2])
            com = d.subtree_com[0]
            # THE FOOT CENTRE IS THE FOOT POLYGON, NOT THE HEELS. This was the mean of calcn_r
            # and calcn_l -- the HEEL midpoint -- and the CoM was then plotted against it and read
            # as "position within the base of support". Measured 2026-08-02: against heels alone
            # the CoM reads ~15 cm forward and OUTSIDE the box; against heels AND toes it is
            # 4.8 mm forward and comfortably inside. I read a real trace off a wrongly-centred
            # axis and concluded the body starts outside its base. It does not.
            #
            # A PLOT'S ORIGIN IS A MEASUREMENT LIKE ANY OTHER, and this one was undeclared.
            _b = lambda n: d.xpos[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, n)]
            foot = 0.25 * (_b("calcn_r") + _b("calcn_l") + _b("toes_r") + _b("toes_l"))
            dx, dy = float(com[0] - foot[0]), float(com[1] - foot[1])
            if z < 0.5 * tgt:
                fell = True
            fr = joint_fracs(d, jids)                    # every graded joint, not the worst one
            jf = float(fr.max())                         # the HEADLINE, still the max: it is what
                                                         # the picture and the log column report
            # THE PHYSICAL OVERLOAD, measured only when the arm asks for it. `limit_overload`
            # reads the ACTIVE constraint rows this step, so it must be called here inside the
            # loop and cannot be hoisted -- and it costs nothing on the hinge/retired arms,
            # which never enter the branch.
            _ovl = (_OVL_FN(m, d, mujoco, _CAP, _JNAME, _PRIM)[0]
                    if joints == "load" else None)
            r, _ = stand_reward(z, (dx, dy), fr, False, float(np.abs(d.ctrl).mean()), P,
                                joints_form=joints, overload=_ovl)
            tot += r; n += 1
            tr["t"].append(k * m.opt.timestep); tr["z"].append(z)
            tr["comx"].append(dx); tr["comy"].append(dy); tr["r"].append(r); tr["jf"].append(jf)
        if fell:
            break
    if ren is not None:
        ren.close()
    score = tot / max(n, 1) - (3.0 if fell else 0.0) - 2.0 * (1.0 - (k + 1) / steps)
    return float(score), tr, pics

def score_theta(m, d, mujoco, theta, P, secs, seeds=1, frames=0, joints="hinge"):
    """A candidate's score is the WORST of `seeds` randomized starts, and the trace is that
    worst one. Returns `(score, trace, pics, per_seed_scores)`.

    THE RULE THIS ENFORCES IS ALREADY IN CLAUDE.md AND WAS NOT IN THIS TRAINER: score every
    genome from N randomized starts and keep the WORST, because one rollout from one initial
    condition is not a measurement, it is a coin toss. MEASURED on this exact body and this
    exact saved policy (`tools/stand_survival.py`, 2026-08-04): a 1e-6 nudge spans 6.30 s to
    9.08 s of survival, and the unperturbed start is the LUCKIEST of ten. A search scored on
    seed 0 alone is therefore selecting for initial conditions, not for policies.

    `seeds=1` REPRODUCES THE OLD BEHAVIOUR EXACTLY -- seed 0, unperturbed, one rollout -- so
    this is an option the caller opens, not a silent change to every past number.

    The worst-case trace is the one drawn, deliberately. A picture of the best seed under a
    worst-seed score is an instrument showing you a different rollout from the one it graded.
    """
    if seeds <= 1:
        s, tr, pics = evaluate(m, d, mujoco, theta, P, secs, seed=0, frames=frames,
                               joints=joints)
        return s, tr, pics, [s]
    runs = [evaluate(m, d, mujoco, theta, P, secs, seed=i, joints=joints)
            for i in range(seeds)]
    scores = [r[0] for r in runs]
    w = int(np.argmin(scores))
    # the worst seed is re-run WITH frames only when frames are asked for, so the common path
    # (scoring a population) never pays for a renderer it will not look at
    if frames:
        _, tr, pics = evaluate(m, d, mujoco, theta, P, secs, seed=w, frames=frames,
                               joints=joints)
    else:
        tr, pics = runs[w][1], runs[w][2]
    return float(scores[w]), tr, pics, [float(s) for s in scores]


def derive_step(m, d, mujoco, mu, sd, P, secs, seeds, joints, elite_frac, rng, k=6):
    """MEASURE the step this policy's own landscape supports, instead of halving a cold guess.

    RULE 1 APPLIED TO THE SEARCH ITSELF. `train_stand`'s warm start set `sd = 0.5 * sd` -- half
    of the COLD spread, a number that describes a space in which the incumbent does not yet
    exist. `tools/search_landscape.py` measured what that costs on the real policy:

        scale x the trainer's warm sd   |  % of samples that BEAT the incumbent
        -------------------------------|--------------------------------------
        0.0001                          |  70%
        0.0003                          |  10%
        0.001 .. 1.0                    |   0%

    The incumbent sits in a basin about FOUR ORDERS OF MAGNITUDE narrower than the step the
    trainer takes, so at its own scale the population contains nothing better -- 0 of 10 -- and
    NO update rule can rescue a population with nothing good in it. The elite-mean guard fixes
    the centre being destroyed; this fixes there being nothing to move toward.

    NOTHING IS CHOSEN HERE, and that is the whole point:

    * the LADDER is powers of ten, a measurement grid stated in the open, not a search for a
      best value -- the same distinction `grab_load_path`'s mass curve draws;
    * the CRITERION is the search's OWN elite fraction (`elite/pop`). A step is useful exactly
      when at least the fraction of samples the search will KEEP are improvements; asking for
      more than that is asking for a property the algorithm does not use. No free number
      appears anywhere in it;
    * the OUTPUT is the largest ladder rung meeting that criterion, and if none does the
      smallest rung is returned WITH A REFUSAL PRINTED, never an extrapolation off the end of a
      measured curve.

    Returns `(sd_scaled, report)`. Costs `len(ladder) * k` evaluations, once.
    """
    ladder = (1.0, 1e-1, 1e-2, 1e-3, 1e-4, 1e-5)
    inc = score_theta(m, d, mujoco, mu, P, secs, seeds, joints=joints)[0]
    report = []
    chosen = None
    for s in ladder:
        hits = 0
        for _ in range(k):
            cand = mu + rng.normal(0.0, 1.0, size=mu.shape) * sd * s
            cand[:m.nu] = np.clip(cand[:m.nu], 0.0, 1.0)
            if score_theta(m, d, mujoco, cand, P, secs, seeds, joints=joints)[0] > inc:
                hits += 1
        frac = hits / k
        report.append((s, frac))
        if chosen is None and frac >= elite_frac:
            chosen = s          # the ladder descends, so the FIRST hit is the LARGEST rung
    return (sd * (chosen if chosen is not None else ladder[-1]),
            dict(incumbent=float(inc), ladder=report, chosen=chosen,
                 elite_frac=float(elite_frac), refused=chosen is None))


def draw_turn(turn, P, tr, pics, hist, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(14.5, 7.4))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.15, 1], hspace=0.36, wspace=0.26)
    if pics:
        ax = fig.add_subplot(gs[0, :]); ax.imshow(np.concatenate(pics, axis=1)); ax.axis("off")
        ax.set_title(f"turn {turn} — the best candidate, {len(pics)} frames", fontsize=10)
    tgt = P["OUT pelvis_target_m"]
    ax = fig.add_subplot(gs[1, 0])
    ax.plot(tr["t"], tr["z"], color="#c0392b", lw=1.9, label="pelvis")
    ax.axhline(tgt, color="#1a7f37", lw=2.2, label=f"derived target {tgt:.4f} m")
    ax.axhline(0.9 * tgt, color="#1a7f37", ls="--", lw=1.3, label="90% — the proof bar")
    ax.set_xlabel("s"); ax.set_ylabel("m"); ax.legend(fontsize=7); ax.set_title("THE BRANCH: pelvis height", fontsize=9)
    ax = fig.add_subplot(gs[1, 1])
    hw, hl = P["OUT bos_half_lat_m"], P["OUT bos_half_fore_m"]
    ax.add_patch(matplotlib.patches.Rectangle((-hw, -hl), 2 * hw, 2 * hl, alpha=0.18,
                                              color="#1e8449", ec="#1e8449", lw=2))
    ax.plot(tr["comy"], tr["comx"], color="#c0392b", lw=1.3)
    ax.scatter([0], [0], marker="X", s=110, color="#d35400")
    ax.set_xlim(-0.3, 0.3); ax.set_ylim(-0.3, 0.3); ax.set_aspect("equal")
    ax.set_title("CoM over the base of support", fontsize=9)
    ax = fig.add_subplot(gs[1, 2])
    ax.plot([h[0] for h in hist], [h[1] for h in hist], "o-", color="#2471a3")
    ax.set_xlabel("turn"); ax.set_ylabel("best score")
    ax.set_title("what moved, turn by turn", fontsize=9)
    if tr.get("jf"):
        ax2 = ax.twinx(); ax2.plot(tr["t"], tr["jf"], color="#8e44ad", lw=1.0, alpha=0.55)
        ax2.set_ylabel("worst joint, frac of range", color="#8e44ad", fontsize=7)
        ax2.axhline(0.8, color="#8e44ad", ls=":", lw=1.0)
    hi = min(tr["z"]) if tr["z"] else 0.0
    fig.suptitle(f"STAND PORT — training turn {turn}   pelvis peak {hi:.3f} m / target {tgt:.3f} m "
                 f"= {100*hi/tgt:.0f}%", fontsize=11.5)
    fig.savefig(path, dpi=100, bbox_inches="tight"); plt.close(fig)


def main() -> int:
    import mujoco
    a = sys.argv
    turns = int(a[a.index("--turns") + 1]) if "--turns" in a else 5
    pop = int(a[a.index("--pop") + 1]) if "--pop" in a else 24
    secs = float(a[a.index("--secs") + 1]) if "--secs" in a else 1.2
    init = a[a.index("--init") + 1] if "--init" in a else None
    seeds = int(a[a.index("--seeds") + 1]) if "--seeds" in a else 1
    out_name = a[a.index("--out") + 1] if "--out" in a else "stand_theta.npy"
    # BLOCKS: 4 = a0|kh|kp|kr (with the frontal-plane roll term), 3 = a0|kh|kp (without it).
    # THIS EXISTS TO MAKE AN A/B POSSIBLE, and without it the roll experiment has no control.
    # Training a 4-block policy from scratch and comparing it to the SAVED incumbent compares
    # two things that differ in the policy form AND the training history AND the scoring rule --
    # three coupled changes, which is a three-body problem with no attributable answer. With
    # `--blocks 3` the identical trainer, budget, seeds, window and RNG stream produce the
    # without-roll arm, and the roll term is the only variable between them.
    #
    # 6 = a0|kh|kp|kr|kx|ky: the CoM-BoS feedback arm (2026-08-04). Same single-variable
    # discipline: warm-started from the 4-block incumbent (kx=ky=0), the ONLY difference from
    # the P-only control is the kx*com_x + ky*com_y term. 9-block PD+CoM is NOT trained here:
    # the velocity arm was falsified on this body (any non-zero kdz/kdp/kdr drops survival from
    # ~9 s to 3-5 s), and adding it back would couple two variables into one experiment.
    blocks = int(a[a.index("--blocks") + 1]) if "--blocks" in a else 4
    if blocks not in (3, 4, 6):
        raise SystemExit("--blocks must be 3 (no roll term), 4 (with it) or 6 (with the CoM "
                         "BoS arm). Refusing.")
    # THE JOINTS TERM'S SHAPE, and its control. "hinge" = the derived per-joint sum; "retired" =
    # the max-then-gaussian, executable so the A/B has an arm that is the old reward exactly.
    # Measured before the change (tools/joints_gradient.py): the retired form sees ONE joint per
    # sample of the 29 graded, at a slope of ~1e-5, so it is a term in a derived reward that is
    # doing nothing -- the same species of defect as `joint_frac` returning a hardcoded 0.0 for
    # this trainer's first three turns, found the same way and named the same way.
    joints = a[a.index("--joints") + 1] if "--joints" in a else "hinge"
    if joints not in ("hinge", "retired", "load"):
        raise SystemExit(
            "--joints must be 'hinge' (derived), 'retired' (the control) or 'load' (the same "
            "shape and the same constants on the MEASURED constraint torque -- see "
            "stand_port.load_joints_factor). 'load' is not a third SHAPE, which rule 1 would "
            "forbid as a sweep: the aggregation, the lorentzian and both constants are held "
            "fixed and the QUANTITY is the single variable. Refusing.")
    # THE ELITE-MEAN GUARD, off by default so every existing invocation reproduces its history
    # bit-for-bit and the arms already run remain valid controls. It becomes the default when
    # it is PROVEN, not when it is written -- the same sequence `--blocks` and `--joints`
    # followed. See the Rule 0 beside the guard itself.
    elite_guard = "--elite-guard" in a
    # DERIVE THE STEP instead of halving the cold spread. Off by default for the same reason
    # the guard is: every arm already run stays a valid control until this is proven.
    derive_step_flag = "--derive-step" in a
    OUTDIR.mkdir(parents=True, exist_ok=True)

    P = derive_stand_port()
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    nu = m.nu
    dim = blocks * nu   # a0 | kh | kp [| kr -- the roll block, 2026-08-04]
    # INITIALIZATION. a0 starts at 0.15 (mid-range activation); every gain starts at 0.
    mu = np.concatenate([np.full(nu, 0.15)] + [np.zeros(nu)] * (blocks - 1))
    sd = np.concatenate([np.full(nu, 0.15)] + [np.full(nu, 0.6)] * (blocks - 1))
    if init:
        # WARM START: continue from a saved theta instead of re-paying for the search from zero.
        # The spread is halved -- the question is now "what is near the best known", not "what
        # is anywhere" (same derivation, finer measurement).
        mu = np.load(init)
        if mu.size == 3 * nu and blocks == 4:   # an old 3-block checkpoint: adopt it with kr = 0,
            mu = np.concatenate([mu, np.zeros(nu)])   # so the warm start is the old policy exactly
        if mu.size == 3 * nu and blocks == 6:   # 3-block into the CoM arm: kh|kp kept, kr|kx|ky = 0
            mu = np.concatenate([mu, np.zeros(3 * nu)])
        if mu.size == 4 * nu and blocks == 3:   # a 4-block checkpoint into a 3-block search: the
            mu = mu[:3 * nu]                    # roll block is DROPPED, and the arm says so
        if mu.size == 4 * nu and blocks == 6:   # THE CoM ARM'S WARM START: the 4-block incumbent
            mu = np.concatenate([mu, np.zeros(2 * nu)])  # plus kx = ky = 0. The P-only policy is
            # then the initial candidate exactly (kx*0 + ky*0 = 0), so turn 0 CANNOT be worse
            # than the incumbent -- the same correctness property `cand[0] = mu` enforces per turn.
        sd = 0.5 * sd
        print(f"warm start from {init}")
    elite = max(3, pop // 5)
    rng = np.random.default_rng(0)
    step_report = None
    # THE SPREAD FLOOR, AND IT WAS AN ABSOLUTE NUMBER STANDING IN FOR A RELATIVE ONE.
    # The update has always read `sd = el.std(0) + 1e-3`. The `1e-3` is there to stop the
    # sampler degenerating to a point, and it was invisible for as long as `sd` happened to be
    # O(0.1) -- a thousandth of the spread, which is what it was meant to be. MEASURED the
    # moment the step was derived (2026-08-04): a derived sd of 7.5e-6 on the a0 block is
    # swamped 133x by a 1e-3 floor, so turn 0 searched the basin, found -3.808 against the
    # incumbent's -3.864, and every turn after it was thrown straight back to a scale the
    # landscape measures at 0% improvement. The trace says it plainly -- best frozen at -3.808
    # while the population mean sat at -4.3.
    #
    # ONE QUANTITY, TWO LANDMARKS (rule 19), in units: the floor is a FRACTION OF A SPREAD and
    # was written as a spread. It is expressed as the fraction it always was -- and only on the
    # derived path, so every run already made keeps the absolute floor it was made with and
    # remains a control. Assigned AFTER the derivation below, because a floor taken from the
    # spread the derivation REPLACES is the same defect one step removed.
    sd_floor = 1e-3
    if derive_step_flag:
        if not init:
            raise SystemExit("--derive-step needs --init: it measures the basin around a KNOWN "
                             "policy, and a cold search has no incumbent to measure around. "
                             "Refusing to measure a landscape that has no centre (rule 20).")
        print(f"  DERIVING THE STEP from this policy's own landscape "
              f"(criterion: >= the search's own elite fraction {elite}/{pop} = "
              f"{elite/pop:.2f} of samples must beat the incumbent)")
        sd, step_report = derive_step(m, d, mujoco, mu, sd, P, secs, seeds, joints,
                                      elite / pop, rng)
        for s, frac in step_report["ladder"]:
            print(f"     x{s:<8g} {100*frac:>5.0f}% beat the incumbent"
                  + ("   <- CHOSEN" if s == step_report["chosen"] else ""))
        if step_report["refused"]:
            print(f"     NO RUNG MET THE CRITERION -- the smallest tried is used and this line "
                  f"is the refusal.\n     The basin is narrower than 1e-5 x the cold sd, and "
                  f"that is a finding about the policy,\n     not a step to trust.")
        print(f"     warm sd was 0.5 x cold; it is now {step_report['chosen'] or 1e-5:g} x that")
        sd_floor = 1e-3 * sd.copy()      # the same thousandth, now of the spread actually used
        print(f"     spread floor follows it: {float(np.min(sd_floor)):.3g}.."
              f"{float(np.max(sd_floor)):.3g} (was a flat 1e-3, which would swamp this step "
              f"{1e-3/max(float(np.min(sd)), 1e-30):.0f}x)")
    hist = []
    best_ever = (-np.inf, mu.copy())     # the SAVE is the session's best, not the last turn's

    print(f"\nTRAINING THE STAND PORT — target pelvis {P['OUT pelvis_target_m']:.4f} m, "
          f"g {g:.4f}, {nu} muscles, {dim}-dim search "
          f"({blocks} blocks: "
          f"{'a0|kh|kp' if blocks == 3 else 'a0|kh|kp|kr' if blocks == 4 else 'a0|kh|kp|kr|kx|ky COM'}"
          f"{'  -- NO ROLL TERM, the control arm' if blocks == 3 else ''})",
          end="")
    print()
    # ONE DESCRIPTION PER ARM, LOOKED UP -- not an if/else with a catch-all. The two-branch
    # version printed "THE CONTROL ARM: max-then-gaussian, the retired form exactly" for
    # `--joints load`, because anything that was not "hinge" fell into the else. The run was
    # correct and its own log described it as a different experiment; a log published as
    # evidence would have claimed the physical arm was the retired geometric one. A catch-all
    # branch is a claim about every value the author did not think of.
    _JOINTS_DESC = {
        "hinge":   "(per-joint hinge summed over every graded joint -- the derived form)",
        "retired": "-- THE CONTROL ARM: max-then-gaussian, the retired form exactly",
        "load":    "(the SAME hinge shape and constants, on the MEASURED constraint torque "
                   "normalised per joint by muscular capacity -- stand_port.load_joints_factor)",
    }
    if joints not in _JOINTS_DESC:
        raise SystemExit(f"no printed description for --joints {joints!r}. Refusing to run an "
                         f"arm whose log cannot say what it is.")
    print(f"  joints term: {joints.upper()}  {_JOINTS_DESC[joints]}")
    print(f"  scoring: WORST of {seeds} randomized start(s) x {secs:.1f} s"
          + ("  (seeds=1 -- the old single-rollout behaviour, reproduced exactly)" if seeds <= 1
             else f"  (nudge {NUDGE:g} on qpos; seed 0 unperturbed)"))
    print(f"  ELITE-MEAN GUARD: "
          + ("ON -- the search centre may not move downhill (one extra eval per turn)"
             if elite_guard else
             "off -- the centre follows the elite mean wherever it goes (the historical rule)"))
    print(f"  saving to {out_name}")
    print(f"{'turn':>5}{'best':>10}{'mean':>10}{'elmean':>10}{'mu':>7}{'pelvis MIN':>13}"
          f"{'% of target':>13}{'held':>8}{'jmax':>7}{'seedspr':>9}  verdict")
    best_theta = mu.copy()
    for turn in range(turns):
        cand = rng.normal(mu, sd, size=(pop, dim))
        # THE INCUMBENT IS ALWAYS A CANDIDATE. Without this line CEM scores only PERTURBED
        # samples and never the mean itself, so a warm start can end strictly WORSE than not
        # training at all -- and did, MEASURED 2026-08-04: seeded with the theta that stands at
        # 101.9% of target, turn 0 of a 24-turn warm start opened at 48% and never recovered,
        # because at 870 dimensions every sample of `normal(mu, 0.075)` is a long way from mu.
        # This is not a tuning knob; it is a correctness property of the search (the best known
        # policy cannot be lost by looking for a better one), and it costs one evaluation.
        cand[0] = mu
        cand[:, :nu] = np.clip(cand[:, :nu], 0.0, 1.0)
        scores = np.array([score_theta(m, d, mujoco, c, P, secs, seeds, joints=joints)[0]
                           for c in cand])
        order = np.argsort(-scores)
        el = cand[order[:elite]]
        # ── THE ELITE-MEAN GUARD (2026-08-04). CEM's centre may not move DOWNHILL. ────────────
        # RULE 0, stated before it was built:
        #
        #   STATEMENT   `cand[0] = mu` guarantees the best policy cannot be LOST. It does not
        #               guarantee the search can still FIND anything, and those are different
        #               properties. When `mu` is the best point and every sample is worse -- the
        #               normal case at 1160 dimensions with sd 0.075 -- the elite is `{mu, three
        #               worse samples}` and `el.mean(0)` moves the centre three-quarters of the
        #               way toward the worse ones. The distribution the search draws from is
        #               destroyed on turn 0 and never recovers, so `best_ever` saves the warm
        #               start and the run reports "no improvement" whatever was changed.
        #               MEASURED: two 30-turn warm A/B arms, 2,160 evaluations each, ZERO turns
        #               beating turn 0, both saving a theta bit-identical to their init.
        #   PREDICTION  With the centre refused permission to move downhill, the same budget from
        #               the same init produces a theta that is NOT bit-identical to it.
        #   FALSIFIER   Still bit-identical after the same budget -> the elite mean was not the
        #               wall; the sampling distribution at this dimensionality cannot produce an
        #               improvement at all, and the answer is a different SEARCH, not a guard.
        #
        # NO NEW CONSTANT. The elite mean is scored (one extra evaluation per turn, the same
        # price `cand[0] = mu` already pays) and adopted only if it beats the incumbent's own
        # score. `scores[0]` IS the incumbent's, because `cand[0] = mu` -- read, never re-run.
        # `sd` comes from the elite either way: the spread is a different quantity from the
        # centre, and freezing it too would stop the search refining.
        el_mean = el.mean(0)
        if elite_guard:
            em_score = score_theta(m, d, mujoco, el_mean, P, secs, seeds, joints=joints)[0]
            moved = em_score > scores[0]
            mu = el_mean if moved else mu
        else:
            em_score, moved = float("nan"), True
            mu = el_mean
        sd = el.std(0) + sd_floor
        best_theta = cand[order[0]]
        s, tr, pics, per_seed = score_theta(m, d, mujoco, best_theta, P, secs, seeds, frames=6,
                                             joints=joints)
        # THE BAR IS THE MINIMUM OVER THE FULL FIVE SECONDS, NOT THE PEAK OVER ONE.
        # The first version printed PROVEN on turn 0 because the KEYFRAME starts at 0.98 m: the
        # "peak" was the starting height, and a 1.0 s rollout satisfied a 5 s requirement. That is
        # an instrument reporting success by measuring the wrong thing -- the same species as
        # `surv% = 92.8` over a body that was toppling. Minimum, full duration, or it is not proven.
        held = min(tr["z"]) if tr["z"] else 0.0
        frac = 100 * held / P["OUT pelvis_target_m"]
        survived = len(tr["t"]) * CTRL_EVERY * m.opt.timestep
        # THE BAR IS f3's FIVE SECONDS, or the whole training window if it is shorter -- so a
        # 1.2 s smoke run cannot print PROVEN for surviving its own duration. `0.02` was
        # hardcoded here and is the control period; read from the model instead, because a
        # literal that happens to equal CTRL_EVERY * timestep is a coincidence waiting to rot.
        ok = frac >= 90.0 and survived >= min(secs, 5.0) - 0.01
        # THE SEED SPREAD, max - min over the seeds, and NOT the worst/mean ratio CLAUDE.md
        # names. That ratio is only meaningful for a positive fitness: this score is negative
        # almost everywhere (fall penalty -3, duration penalty -2), and worst/mean on negatives
        # is greater than 1 and gets LARGER as the policy gets more fragile -- a robustness
        # number that improves when robustness falls. MEASURED on the first smoke run: every
        # candidate scored about -3.8 and the guard `mean > 0` silently printed n/a for all of
        # them, which is the guard correctly refusing to report a quantity that was undefined.
        # The spread is sign-agnostic and answers the question the ratio was reaching for:
        # HOW MUCH DOES THE SEED DECIDE? 0 = the policy decides; large = the coin does.
        rb = (max(per_seed) - min(per_seed)) if seeds > 1 else None
        rb_txt = f"{rb:.2f}" if rb is not None else "n/a"
        hist.append((turn, float(scores[order[0]])))
        if float(scores[order[0]]) > best_ever[0]:
            # The last version saved the LAST turn's winner: a session whose best came at turn 12
            # of 14 wrote turn 13's worse theta over it, and the harness downstream then graded a
            # body the training had already beaten. An instrument reporting the wrong candidate is
            # the same species as the peak-vs-minimum bar.
            best_ever = (float(scores[order[0]]), cand[order[0]].copy())
        # `elmean` is the elite mean's own score and `mu` says whether the centre was allowed to
        # move to it. Printed every turn because the whole warm-start failure was invisible: the
        # log showed a best score that never improved and said nothing about WHY, and the answer
        # was that the centre had already left the incumbent on turn 0.
        em_txt = f"{em_score:>10.3f}" if np.isfinite(em_score) else f"{'n/a':>10}"
        mv_txt = ("moved" if moved else "HELD") if elite_guard else "free"
        print(f"{turn:>5}{scores[order[0]]:>10.3f}{scores.mean():>10.3f}{em_txt}{mv_txt:>7}"
              f"{held:>12.3f}m{frac:>12.0f}%{survived:>7.2f}s"
              f"{max(tr['jf']) if tr['jf'] else 0:>7.2f}"
              f"{rb_txt:>9}  {'PROVEN' if ok else 'not yet'}")
        # THE PICTURE IS NAMED AFTER THE ARM. Two arms of an A/B run concurrently -- that is the
        # point of an A/B -- and both used to write `stand_turn_NN.png`, so each turn's picture
        # was whichever process got there last. The numbers in the two logs stayed independent
        # and correct, which is exactly what makes this the dangerous kind: the evidence you
        # LOOK at silently belongs to the other arm while the evidence you compute does not.
        # "A turn you have not looked at did not end" is worth nothing if the turn you looked
        # at was someone else's.
        draw_turn(turn, P, tr, pics, hist, OUTDIR / f"{Path(out_name).stem}_turn_{turn:02d}.png")
    # SAVED AT dim NUMBERS WHATEVER THE ARM. A 3-block winner is padded with an explicit zero roll
    # block, so both arms hand the judge the identical shape and `walk_formula`/`parser` need no
    # branch. The zeros are the without-roll policy exactly -- kr * roll = 0 for every roll.
    saved = best_ever[1]
    if saved.size == 3 * nu and blocks == 4:
        saved = np.concatenate([saved, np.zeros(nu)])
    if blocks == 6:
        # THE 6-BLOCK LAYOUT IS A SYNERGY CONTRACT, NOT A PARSER ONE. parser.check_theta_shape
        # caps at 5 blocks (a0|kh|kp|kr|kw) on purpose -- a 6-block checkpoint fed to the parser's
        # formula would be silently truncated, which is exactly the silent-degradation that guard
        # exists to refuse. The decoder (SynergyDecoder) validates 6/7/9 layouts itself, so the
        # guard here is only that the CoM arm produced the shape it was asked for.
        if saved.size != 6 * nu:
            raise SystemExit(f"6-block arm produced {saved.size // nu} blocks of {nu} -- the "
                             f"CoM layout is broken. Refusing to save.")
    else:
        from parser import check_theta_shape
        check_theta_shape(saved, nu, where=f"train_stand --out {out_name}")
    np.save(OUTDIR / out_name, saved)
    print(f"\nsaved the SESSION'S best (score {best_ever[0]:.3f}), not the last turn's")
    print(f"\nPICTURES: {OUTDIR}/stand_turn_*.png")
    print("A TURN YOU HAVE NOT LOOKED AT DID NOT END.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
