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

MYOBODY = ROOT / "external" / "myo_sim" / "body" / "myobody.xml"
OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"

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


def evaluate(m, d, mujoco, theta, P, secs, seed=0, frames=0):
    """One life under a candidate. Returns (score, trace, pics).

    theta = [a0 (nu), k_h (nu), k_p (nu)] -- a baseline activation plus proportional feedback on
    pelvis HEIGHT ERROR and PITCH. Those two are not chosen: they are what an inverted pendulum
    has (a height it must hold and a lean that will topple it), and theStance publishes the
    fall rate that makes the second one urgent.
    """
    nu = m.nu
    jids = joint_ids(m, mujoco)
    # FOUR BLOCKS: baseline, height gain, pitch gain, ROLL gain. The roll block is new
    # (2026-08-04) and the trainer gained it in the SAME commit as the parser formula --
    # the lesson this session paid for twice, in the walk port: a number optimised against
    # a plant the judge does not run is dead at judgment. A 3-block theta still works and
    # is bit-identical to the old formula, because kr is then zeros.
    a0, kh, kp = theta[:nu], theta[nu:2 * nu], theta[2 * nu:3 * nu]
    kr = theta[3 * nu:4 * nu] if theta.size >= 4 * nu else np.zeros(nu)
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    seat_in_limits(m, d, mujoco, jids)      # the body may not START outside its own stops
    tgt = P["OUT pelvis_target_m"]
    steps = int(secs / m.opt.timestep)
    grab = set(np.linspace(0, steps - 1, frames).astype(int)) if frames else set()
    ren = mujoco.Renderer(m, height=240, width=320) if frames else None
    tr = {"t": [], "z": [], "comx": [], "comy": [], "r": [], "jf": []}
    pics, tot, n, fell = [], 0.0, 0, False
    for k in range(steps):
        if k % 20 == 0:
            z = float(d.qpos[2])
            q = d.qpos[3:7]
            pitch = float(np.arctan2(2 * (q[0] * q[2] - q[3] * q[1]), 1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            roll = float(np.arctan2(2 * (q[0] * q[1] + q[2] * q[3]),
                                     1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            u = a0 + kh * (tgt - z) + kp * pitch + kr * roll
            d.ctrl[:] = np.clip(u, 0.0, 1.0)
        mujoco.mj_step(m, d)
        if k in grab and ren is not None:
            ren.update_scene(d); pics.append(ren.render().copy())
        if k % 20 == 0:
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
            jf = joint_frac(d, jids)
            r, _ = stand_reward(z, (dx, dy), jf, False, float(np.abs(d.ctrl).mean()), P)
            tot += r; n += 1
            tr["t"].append(k * m.opt.timestep); tr["z"].append(z)
            tr["comx"].append(dx); tr["comy"].append(dy); tr["r"].append(r); tr["jf"].append(jf)
        if fell:
            break
    if ren is not None:
        ren.close()
    score = tot / max(n, 1) - (3.0 if fell else 0.0) - 2.0 * (1.0 - (k + 1) / steps)
    return float(score), tr, pics


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
    OUTDIR.mkdir(parents=True, exist_ok=True)

    P = derive_stand_port()
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    nu = m.nu
    dim = 4 * nu        # a0 | kh | kp | kr -- the roll block, 2026-08-04
    mu = np.concatenate([np.full(nu, 0.15), np.zeros(nu), np.zeros(nu), np.zeros(nu)])
    sd = np.concatenate([np.full(nu, 0.15), np.full(nu, 0.6), np.full(nu, 0.6),
                         np.full(nu, 0.6)])
    if init:
        # WARM START: continue from a saved theta instead of re-paying for the search from zero.
        # The spread is halved -- the question is now "what is near the best known", not "what
        # is anywhere" (same derivation, finer measurement).
        mu = np.load(init)
        if mu.size == 3 * nu:      # an old 3-block checkpoint: adopt it with kr = 0, so the
            mu = np.concatenate([mu, np.zeros(nu)])   # warm start is the old policy exactly
        sd = 0.5 * sd
        print(f"warm start from {init}")
    elite = max(3, pop // 5)
    rng = np.random.default_rng(0)
    hist = []
    best_ever = (-np.inf, mu.copy())     # the SAVE is the session's best, not the last turn's

    print(f"\nTRAINING THE STAND PORT — target pelvis {P['OUT pelvis_target_m']:.4f} m, "
          f"g {g:.4f}, {nu} muscles, {dim}-dim search")
    print(f"{'turn':>5}{'best':>10}{'mean':>10}{'pelvis MIN':>13}{'% of target':>13}{'held':>8}{'jmax':>7}  verdict")
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
        scores = np.array([evaluate(m, d, mujoco, c, P, secs)[0] for c in cand])
        order = np.argsort(-scores)
        el = cand[order[:elite]]
        mu, sd = el.mean(0), el.std(0) + 1e-3
        best_theta = cand[order[0]]
        s, tr, pics = evaluate(m, d, mujoco, best_theta, P, secs, frames=6)
        # THE BAR IS THE MINIMUM OVER THE FULL FIVE SECONDS, NOT THE PEAK OVER ONE.
        # The first version printed PROVEN on turn 0 because the KEYFRAME starts at 0.98 m: the
        # "peak" was the starting height, and a 1.0 s rollout satisfied a 5 s requirement. That is
        # an instrument reporting success by measuring the wrong thing -- the same species as
        # `surv% = 92.8` over a body that was toppling. Minimum, full duration, or it is not proven.
        held = min(tr["z"]) if tr["z"] else 0.0
        frac = 100 * held / P["OUT pelvis_target_m"]
        survived = len(tr["t"]) * 0.02
        ok = frac >= 90.0 and survived >= 4.99
        hist.append((turn, float(scores[order[0]])))
        if float(scores[order[0]]) > best_ever[0]:
            # The last version saved the LAST turn's winner: a session whose best came at turn 12
            # of 14 wrote turn 13's worse theta over it, and the harness downstream then graded a
            # body the training had already beaten. An instrument reporting the wrong candidate is
            # the same species as the peak-vs-minimum bar.
            best_ever = (float(scores[order[0]]), cand[order[0]].copy())
        print(f"{turn:>5}{scores[order[0]]:>10.3f}{scores.mean():>10.3f}{held:>12.3f}m"
              f"{frac:>12.0f}%{survived:>7.2f}s{max(tr['jf']) if tr['jf'] else 0:>7.2f}  "
              f"{'PROVEN' if ok else 'not yet'}")
        draw_turn(turn, P, tr, pics, hist, OUTDIR / f"stand_turn_{turn:02d}.png")
    np.save(OUTDIR / "stand_theta.npy", best_ever[1])
    print(f"\nsaved the SESSION'S best (score {best_ever[0]:.3f}), not the last turn's")
    print(f"\nPICTURES: {OUTDIR}/stand_turn_*.png")
    print("A TURN YOU HAVE NOT LOOKED AT DID NOT END.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
