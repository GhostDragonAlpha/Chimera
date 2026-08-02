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


def evaluate(m, d, mujoco, theta, P, secs, seed=0, frames=0):
    """One life under a candidate. Returns (score, trace, pics).

    theta = [a0 (nu), k_h (nu), k_p (nu)] -- a baseline activation plus proportional feedback on
    pelvis HEIGHT ERROR and PITCH. Those two are not chosen: they are what an inverted pendulum
    has (a height it must hold and a lean that will topple it), and theStance publishes the
    fall rate that makes the second one urgent.
    """
    nu = m.nu
    a0, kh, kp = theta[:nu], theta[nu:2 * nu], theta[2 * nu:]
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    tgt = P["OUT pelvis_target_m"]
    steps = int(secs / m.opt.timestep)
    grab = set(np.linspace(0, steps - 1, frames).astype(int)) if frames else set()
    ren = mujoco.Renderer(m, height=240, width=320) if frames else None
    tr = {"t": [], "z": [], "comx": [], "comy": [], "r": []}
    pics, tot, n, fell = [], 0.0, 0, False
    for k in range(steps):
        if k % 20 == 0:
            z = float(d.qpos[2])
            q = d.qpos[3:7]
            pitch = float(np.arctan2(2 * (q[0] * q[2] - q[3] * q[1]), 1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            u = a0 + kh * (tgt - z) + kp * pitch
            d.ctrl[:] = np.clip(u, 0.0, 1.0)
        mujoco.mj_step(m, d)
        if k in grab and ren is not None:
            ren.update_scene(d); pics.append(ren.render().copy())
        if k % 20 == 0:
            z = float(d.qpos[2])
            com = d.subtree_com[0]
            foot = 0.5 * (d.xpos[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "calcn_r")] +
                          d.xpos[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "calcn_l")])
            dx, dy = float(com[0] - foot[0]), float(com[1] - foot[1])
            if z < 0.5 * tgt:
                fell = True
            r, _ = stand_reward(z, (dx, dy), 0.0, False, float(np.abs(d.ctrl).mean()), P)
            tot += r; n += 1
            tr["t"].append(k * m.opt.timestep); tr["z"].append(z)
            tr["comx"].append(dx); tr["comy"].append(dy); tr["r"].append(r)
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
    OUTDIR.mkdir(parents=True, exist_ok=True)

    P = derive_stand_port()
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    nu = m.nu
    dim = 3 * nu
    mu = np.concatenate([np.full(nu, 0.15), np.zeros(nu), np.zeros(nu)])
    sd = np.concatenate([np.full(nu, 0.15), np.full(nu, 0.6), np.full(nu, 0.6)])
    elite = max(3, pop // 5)
    rng = np.random.default_rng(0)
    hist = []

    print(f"\nTRAINING THE STAND PORT — target pelvis {P['OUT pelvis_target_m']:.4f} m, "
          f"g {g:.4f}, {nu} muscles, {dim}-dim search")
    print(f"{'turn':>5}{'best':>10}{'mean':>10}{'pelvis MIN':>13}{'% of target':>13}{'held':>8}  verdict")
    best_theta = mu.copy()
    for turn in range(turns):
        cand = rng.normal(mu, sd, size=(pop, dim))
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
        print(f"{turn:>5}{scores[order[0]]:>10.3f}{scores.mean():>10.3f}{held:>12.3f}m"
              f"{frac:>12.0f}%{survived:>8.2f}s  {'PROVEN' if ok else 'not yet'}")
        draw_turn(turn, P, tr, pics, hist, OUTDIR / f"stand_turn_{turn:02d}.png")
    np.save(OUTDIR / "stand_theta.npy", best_theta)
    print(f"\nPICTURES: {OUTDIR}/stand_turn_*.png")
    print("A TURN YOU HAVE NOT LOOKED AT DID NOT END.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
