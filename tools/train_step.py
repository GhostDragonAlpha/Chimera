"""train_step.py -- TRAIN THE STEP PORT'S SEVEN EFFORTS, and only those seven.

The stand port's theta is LOADED AND FROZEN, exactly as in train_walk: the 870 numbers that hold
the body up are not re-searched, and the 7 that swing the legs and push off are the entire
difference. The machine, the window, the antiphase and the interlock are DERIVED
(`step_port.derive_step_port`) and are NOT in the search.

v2 (docs/THE_STEP.md amendment): the seventh number is P_push, the terminal-stance ankle
push-off -- added after v1's measured verdict (no stance propulsion -> travel is toppling).

TRAIN WHAT YOU JUDGE -- the lesson this project paid for twice in one day (walk_port LEDGER
2026-08-03, 7376a54): the trainer drives THE SAME `StepMachine` through THE SAME `step_formula`
the judge's parser path drives. Foot contact is read from the model's own touch sensors every
control tick and fed to the machine, exactly as f5_step's obs feed does.

EVERY TURN ENDS IN A PICTURE (docs/THE_WORKFLOW.md section 0).

TRAINED LONGER THAN JUDGED, load-bearing for the same reason as train_walk: this trains at 8 s
and `f5_step` judges 6 s, so the optimiser cannot be indifferent to the judged window's edge.

    python tools/train_step.py --turns 24 --pop 32 --secs 8.0
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body                                              # noqa: E402
from stand_port import MYOBODY                                           # noqa: E402
from train_stand import joint_ids, seat_in_limits                        # noqa: E402
from step_port import (derive_step_port, muscle_groups, step_formula,    # noqa: E402
                       StepMachine, N_FREE, OSC_JOINTS)
from walk_port import walk_reward, score_walk                            # noqa: E402
from train_walk import foot_contact, CTRL_EVERY                          # noqa: E402
from chimera_gait import _periodicity                                    # noqa: E402

OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"
STAND_THETA = OUTDIR / "stand_theta.npy"
STEP_THETA = OUTDIR / "step_theta.npy"


def evaluate(m, d, mujoco, theta_stand, theta_step, groups, P, secs, frames=0, gain=1.0):
    """One life under a candidate, driven by the StepMachine. Returns (score, trace, pics).

    `gain=0.0` is THE EFFORT ABLATION: the six swing efforts are multiplied out inside
    `step_formula` and the body is left with the stand formula alone -- a parameter of this
    function, not a separate harness, so the ablation cannot drift away from the thing it
    ablates. The SENSOR ablation is the judge's business (it zeroes obs); the trainer always
    trains with live sensors, because the judge judges with live sensors.
    """
    nu = m.nu
    jids = joint_ids(m, mujoco)
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    seat_in_limits(m, d, mujoco, jids)      # the body may not START outside its own stops
    tgt = P["OUT pelvis_target_m"]
    steps = int(secs / m.opt.timestep)
    grab = set(np.linspace(0, steps - 1, frames).astype(int)) if frames else set()
    ren = mujoco.Renderer(m, height=240, width=320) if frames else None
    machine = StepMachine(P["OUT swing_window_s"])
    tr = {k: [] for k in ("t", "x", "z", "vx", "cr", "cl", "sup", "r", "st_r", "st_l")}
    pics, tot, n, fell = [], 0.0, 0, False
    x0 = float(d.qpos[0])
    for k in range(steps):
        if k % CTRL_EVERY == 0:
            z = float(d.qpos[2])
            q = d.qpos[3:7]
            pitch = float(np.arctan2(2 * (q[0] * q[2] - q[3] * q[1]),
                                     1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            cr, cl = foot_contact(m, d, mujoco)
            state, phase = machine.step(float(d.time), cr, cl)
            d.ctrl[:] = step_formula(theta_stand, theta_step, groups, z, pitch, nu, tgt,
                                     state, phase, gain=gain)
        mujoco.mj_step(m, d)
        if k in grab and ren is not None:
            ren.update_scene(d); pics.append(ren.render().copy())
        if k % CTRL_EVERY == 0:
            z = float(d.qpos[2])
            cr, cl = foot_contact(m, d, mujoco)
            if z < 0.5 * tgt:
                fell = True
            r = walk_reward(float(d.qvel[0]), z, False, P)
            tot += r; n += 1
            tr["t"].append(k * m.opt.timestep); tr["x"].append(float(d.qpos[0]))
            tr["z"].append(z); tr["vx"].append(float(d.qvel[0]))
            tr["cr"].append(cr); tr["cl"].append(cl)
            tr["sup"].append((1.0 if cr > 0 else 0.0) + (1.0 if cl > 0 else 0.0))
            tr["st_r"].append(0.0 if machine.state["r"] == "stance" else 1.0)
            tr["st_l"].append(0.0 if machine.state["l"] == "stance" else 1.0)
            tr["r"].append(r)
        if fell:
            break
    if ren is not None:
        ren.close()
    dt_s = CTRL_EVERY * m.opt.timestep
    per, period = _periodicity(np.array(tr["sup"]), dt_s) if len(tr["sup"]) > 16 else (0.0, 0.0)
    # SPEED IS DISPLACEMENT OVER TIME (train_walk's note, carried): an instantaneous-velocity
    # mean can look healthy on a body that lurches forward and back and goes nowhere.
    elapsed = max(tr["t"][-1], 1e-9) if tr["t"] else 1e-9
    speed = (float(tr["x"][-1]) - x0) / elapsed if tr["x"] else 0.0
    frac = (k + 1) / steps
    sc = score_walk(tot / max(n, 1), per, frac) - (3.0 if fell else 0.0)
    tr["speed"], tr["periodicity"], tr["period_s"], tr["fell"] = speed, per, period, fell
    tr["duty_r"] = float(np.mean([c > 0 for c in tr["cr"]])) if tr["cr"] else 0.0
    tr["duty_l"] = float(np.mean([c > 0 for c in tr["cl"]])) if tr["cl"] else 0.0
    return float(sc), tr, pics


def draw_turn(turn, P, tr, pics, hist, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(14.5, 7.6))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.1, 1], hspace=0.38, wspace=0.28)
    if pics:
        ax = fig.add_subplot(gs[0, :]); ax.imshow(np.concatenate(pics, axis=1)); ax.axis("off")
        ax.set_title(f"turn {turn} -- the best candidate, {len(pics)} frames", fontsize=10)
    vt = P["OUT target_speed_ms"]
    ax = fig.add_subplot(gs[1, 0])
    ax.plot(tr["t"], tr["x"], color="#c0392b", lw=1.9, label="travelled")
    ax.plot(tr["t"], [vt * t for t in tr["t"]], color="#1a7f37", ls="--", lw=1.5,
            label=f"derived {vt:.3f} m/s")
    ax.set_xlabel("s"); ax.set_ylabel("m"); ax.legend(fontsize=7)
    ax.set_title(f"TRAVEL -- {tr['speed']:.3f} m/s = {100*tr['speed']/vt:.0f}% of derived",
                 fontsize=9)
    ax = fig.add_subplot(gs[1, 1])
    ax.step(tr["t"], [c > 0 for c in tr["cr"]], color="#c0392b", lw=1.3, where="post", label="R")
    ax.step(tr["t"], [1.2 if c > 0 else 0.2 for c in tr["cl"]], color="#2471a3", lw=1.3,
            where="post", label="L")
    ax.step(tr["t"], [2.4 if s > 0 else 1.8 for s in tr["st_r"]], color="#c0392b", lw=1.0,
            ls=":", where="post", label="R machine=SWING")
    ax.step(tr["t"], [2.6 if s > 0 else 2.0 for s in tr["st_l"]], color="#2471a3", lw=1.0,
            ls=":", where="post", label="L machine=SWING")
    ax.set_ylim(-0.3, 3.0); ax.set_xlabel("s"); ax.legend(fontsize=6)
    ax.set_title(f"FOOTFALL + MACHINE -- periodicity {tr['periodicity']:.2f}, "
                 f"period {tr['period_s']:.2f} s (stride {P['OUT stride_s']:.2f})", fontsize=9)
    ax = fig.add_subplot(gs[1, 2])
    ax.plot([h[0] for h in hist], [h[1] for h in hist], "o-", color="#2471a3")
    ax.set_xlabel("turn"); ax.set_ylabel("best score")
    ax.set_title("what moved, turn by turn", fontsize=9)
    ax2 = ax.twinx()
    ax2.plot(tr["t"], tr["z"], color="#8e44ad", lw=1.0, alpha=0.6)
    ax2.axhline(P["OUT upright_floor_m"], color="#8e44ad", ls=":", lw=1.0)
    ax2.set_ylabel("pelvis m", color="#8e44ad", fontsize=7)
    fig.suptitle(f"STEP PORT -- turn {turn}   speed {tr['speed']:.3f} / {vt:.3f} m/s   "
                 f"periodicity {tr['periodicity']:.2f}   duty R/L "
                 f"{tr['duty_r']:.2f}/{tr['duty_l']:.2f} (derived {P['OUT duty_factor']:.2f})",
                 fontsize=11.5)
    fig.savefig(path, dpi=100, bbox_inches="tight"); plt.close(fig)


def main() -> int:
    import mujoco
    a = sys.argv
    turns = int(a[a.index("--turns") + 1]) if "--turns" in a else 24
    pop = int(a[a.index("--pop") + 1]) if "--pop" in a else 32
    secs = float(a[a.index("--secs") + 1]) if "--secs" in a else 8.0
    init = a[a.index("--init") + 1] if "--init" in a else None
    OUTDIR.mkdir(parents=True, exist_ok=True)

    if not STAND_THETA.exists():
        raise SystemExit(f"no {STAND_THETA} -- run `python tools/train_stand.py` first. Walking is "
                         f"composed over standing; refusing to compose over nothing (rule 20).")
    theta_stand = np.load(STAND_THETA)
    P = derive_step_port()
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    groups = muscle_groups(m, d, mujoco)

    # SEVEN NUMBERS WIDE (v2: six swing efforts + P_push), all amplitudes (an amplitude is an
    # activation: clipped to [0,1]). Starts at 0.20 with spread 0.15 -- STARTING POINTS for a
    # search, not settings; the elite mean replaces them on turn 0 and nothing downstream reads
    # them.
    mu = np.full(N_FREE, 0.20)
    sd = np.full(N_FREE, 0.15)
    if init:
        mu = np.load(init); sd = 0.5 * sd
        print(f"warm start from {init}")
    elite = max(3, pop // 5)
    rng = np.random.default_rng(0)
    hist, best_ever = [], (-np.inf, mu.copy())

    print(f"\nTRAINING THE STEP PORT -- {N_FREE} free numbers (six swing efforts; the window "
          f"{P['OUT swing_window_s']:.4f} s, the antiphase and the interlock are DERIVED)")
    print(f"  target {P['OUT target_speed_ms']:.4f} m/s, stride {P['OUT stride_s']:.4f} s, "
          f"duty {P['OUT duty_factor']:.4f}, g {g:.4f}, stand theta FROZEN ({theta_stand.size} numbers)")
    print(f"{'turn':>5}{'best':>9}{'mean':>9}{'speed':>9}{'% tgt':>7}{'period':>8}"
          f"{'dutyR':>7}{'dutyL':>7}{'held':>7}  verdict")
    for turn in range(turns):
        cand = np.clip(rng.normal(mu, sd, size=(pop, N_FREE)), 0.0, 1.0)
        # THE INCUMBENT IS ALWAYS A CANDIDATE (train_stand.py's correctness fix, swept here by
        # tools/elitism_audit.py 2026-08-04 -- this file and port_trainer.py were the two that
        # never got it). Without this line CEM scores only PERTURBED samples and never the mean,
        # so a warm start can end strictly WORSE than not training at all. MEASURED at this
        # file's own dimensionality: the loss is sd^2 * N_FREE, which at N_FREE = 6 is small --
        # but "small at this size" is not a reason to omit a correctness property, and N_FREE
        # grows every time the port gains a number.
        cand[0] = np.clip(mu, 0.0, 1.0)
        scores = np.array([evaluate(m, d, mujoco, theta_stand, c, groups, P, secs)[0]
                           for c in cand])
        order = np.argsort(-scores)
        el = cand[order[:elite]]
        mu, sd = el.mean(0), el.std(0) + 1e-3
        s, tr, pics = evaluate(m, d, mujoco, theta_stand, cand[order[0]], groups, P, secs, frames=6)
        held = tr["t"][-1] if tr["t"] else 0.0
        pct = 100.0 * tr["speed"] / P["OUT target_speed_ms"]
        ok = pct >= 75.0 and tr["periodicity"] >= 0.60 and not tr["fell"]
        hist.append((turn, float(scores[order[0]])))
        if float(scores[order[0]]) > best_ever[0]:
            best_ever = (float(scores[order[0]]), cand[order[0]].copy())
        print(f"{turn:>5}{scores[order[0]]:>9.3f}{scores.mean():>9.3f}{tr['speed']:>9.3f}"
              f"{pct:>6.0f}%{tr['periodicity']:>8.2f}{tr['duty_r']:>7.2f}{tr['duty_l']:>7.2f}"
              f"{held:>6.1f}s  {'WALKS' if ok else 'not yet'}")
        draw_turn(turn, P, tr, pics, hist, OUTDIR / f"step_turn_{turn:02d}.png")
    np.save(STEP_THETA, best_ever[1])
    print(f"\nsaved the SESSION'S best (score {best_ever[0]:.3f}), not the last turn's -> {STEP_THETA}")
    print(f"PICTURES: {OUTDIR}/step_turn_*.png")
    print("A TURN YOU HAVE NOT LOOKED AT DID NOT END.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
