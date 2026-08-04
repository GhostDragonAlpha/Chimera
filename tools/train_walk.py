"""train_walk.py -- TRAIN THE WALK PORT'S SIX FREE NUMBERS, and only those six.

The stand port's theta is LOADED AND FROZEN. That is what makes "walking is composed over
standing" a fact about this file rather than a claim in a document: the 870 numbers that hold the
body up are not re-searched, and the 6 that make it walk are the entire difference. If walking
required re-training the postural policy, the composition would be a fiction and this file would
be unable to hide it.

omega and the L/R antiphase are DERIVED (`walk_port.derive_walk_port`) and are NOT in the search.
If they were, the search would be answering "which cadence is best" -- rule 1's exact tell.

EVERY TURN ENDS IN A PICTURE (docs/THE_WORKFLOW.md section 0). A turn nobody looked at did not
end, and six hours of a converging curve once hid a body that was falling over.

TRAINED LONGER THAN JUDGED, and that is load-bearing -- earned on the stand port hours before
this file existed. `train_stand` optimised over exactly the 5.0 s `f3_stand` judged, and the
policy held for 5.0 s and began toppling at 4.68 s: if the reward integrates over exactly the
judged window, the optimiser is indifferent to everything past it and marginal stability scores
identically to real stability. So this trains at 8 s and `f4_walk` judges 6 s.

    python tools/train_walk.py --turns 20 --pop 24 --secs 8.0
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body                                              # noqa: E402
from stand_port import MYOBODY                                           # noqa: E402
from train_stand import joint_ids, seat_in_limits                        # noqa: E402
from walk_port import (derive_walk_port, muscle_groups, walk_formula,    # noqa: E402
                       walk_reward, score_walk, N_FREE, OSC_JOINTS, WalkOscillator)
from chimera_gait import _periodicity                                    # noqa: E402

OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"
STAND_THETA = OUTDIR / "stand_theta.npy"
WALK_THETA = OUTDIR / "walk_theta.npy"
CTRL_EVERY = 20                     # 40 ms at the model's 0.002 s timestep -- the parser's cadence


def foot_contact(m, d, mujoco):
    """Right and left foot contact from the MODEL'S OWN touch sensors, not from geometry.

    myobody defines exactly four: r_foot, r_toes, l_foot, l_toes -- the `plantar_pressure` port
    validated that they read nonzero resting and 0.000000 lifted. A foot is down if either of its
    two sensors is loaded, because heel-only and toe-only are both contact and a walk spends time
    in each.
    """
    if not hasattr(foot_contact, "_idx"):
        idx = {}
        for i in range(m.nsensor):
            n = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_SENSOR, i) or ""
            side = "r" if n.startswith("r_") else ("l" if n.startswith("l_") else None)
            if side:
                idx.setdefault(side, []).append(int(m.sensor_adr[i]))
        if set(idx) != {"r", "l"}:
            raise SystemExit(f"expected r_/l_ touch sensors, found {sorted(idx)} -- refusing to "
                             f"measure a gait's footfall from sensors this instrument cannot map.")
        foot_contact._idx = idx
    ix = foot_contact._idx
    return (float(sum(d.sensordata[a] for a in ix["r"])),
            float(sum(d.sensordata[a] for a in ix["l"])))


def evaluate(m, d, mujoco, theta_stand, theta_walk, groups, P, secs, frames=0, gain=1.0):
    """One life under a candidate. Returns (score, trace, pics).

    `gain=0.0` is THE ABLATION: the oscillator amplitudes are multiplied out and the body is left
    with the stand formula alone, every other number identical. It is a parameter of this function
    rather than a separate harness so the ablation cannot drift away from the thing it ablates.
    """
    nu = m.nu
    jids = joint_ids(m, mujoco)
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    seat_in_limits(m, d, mujoco, jids)      # the body may not START outside its own stops
    tgt = P["OUT pelvis_target_m"]
    omega = P["OUT omega_rad_s"]
    steps = int(secs / m.opt.timestep)
    grab = set(np.linspace(0, steps - 1, frames).astype(int)) if frames else set()
    ren = mujoco.Renderer(m, height=240, width=320) if frames else None
    tr = {k: [] for k in ("t", "x", "z", "vx", "cr", "cl", "sup", "r")}
    pics, tot, n, fell = [], 0.0, 0, False
    x0 = float(d.qpos[0])
    # THE TRAINER DRIVES WHAT THE JUDGE DRIVES: the clock phase (omega*t), exactly as f4's
    # parser path does -- no entrainment state, no swing gate, because the judge has neither.
    # The entrained WalkOscillator + interlock trained here for one session and was never
    # judged: numbers the judge cannot use are dead at judgment (walk_port LEDGER 2026-08-03).
    for k in range(steps):
        if k % CTRL_EVERY == 0:
            z = float(d.qpos[2])
            q = d.qpos[3:7]
            pitch = float(np.arctan2(2 * (q[0] * q[2] - q[3] * q[1]),
                                     1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            d.ctrl[:] = walk_formula(theta_stand, theta_walk, groups, z, pitch,
                                     omega * d.time, nu, tgt, gain=gain)
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
            tr["r"].append(r)
        if fell:
            break
    if ren is not None:
        ren.close()
    dt_s = CTRL_EVERY * m.opt.timestep
    per, period = _periodicity(np.array(tr["sup"]), dt_s) if len(tr["sup"]) > 16 else (0.0, 0.0)
    # SPEED IS DISPLACEMENT OVER TIME, not the mean of an instantaneous velocity. A body that
    # lurches forward and back can average a healthy vx while going nowhere; the two disagree
    # exactly when it matters.
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
    ax.set_ylim(-0.3, 1.8); ax.set_xlabel("s"); ax.legend(fontsize=7)
    ax.set_title(f"FOOTFALL -- periodicity {tr['periodicity']:.2f}, period {tr['period_s']:.2f} s "
                 f"(stride {P['OUT stride_s']:.2f})", fontsize=9)
    ax = fig.add_subplot(gs[1, 2])
    ax.plot([h[0] for h in hist], [h[1] for h in hist], "o-", color="#2471a3")
    ax.set_xlabel("turn"); ax.set_ylabel("best score")
    ax.set_title("what moved, turn by turn", fontsize=9)
    ax2 = ax.twinx()
    ax2.plot(tr["t"], tr["z"], color="#8e44ad", lw=1.0, alpha=0.6)
    ax2.axhline(P["OUT upright_floor_m"], color="#8e44ad", ls=":", lw=1.0)
    ax2.set_ylabel("pelvis m", color="#8e44ad", fontsize=7)
    fig.suptitle(f"WALK PORT -- turn {turn}   speed {tr['speed']:.3f} / {vt:.3f} m/s   "
                 f"periodicity {tr['periodicity']:.2f}   duty R/L "
                 f"{tr['duty_r']:.2f}/{tr['duty_l']:.2f} (derived {P['OUT duty_factor']:.2f})",
                 fontsize=11.5)
    fig.savefig(path, dpi=100, bbox_inches="tight"); plt.close(fig)


def main() -> int:
    import mujoco
    a = sys.argv
    turns = int(a[a.index("--turns") + 1]) if "--turns" in a else 20
    pop = int(a[a.index("--pop") + 1]) if "--pop" in a else 24
    secs = float(a[a.index("--secs") + 1]) if "--secs" in a else 8.0
    init = a[a.index("--init") + 1] if "--init" in a else None
    OUTDIR.mkdir(parents=True, exist_ok=True)

    if not STAND_THETA.exists():
        raise SystemExit(f"no {STAND_THETA} -- run `python tools/train_stand.py` first. Walking is "
                         f"composed over standing; refusing to compose over nothing (rule 20).")
    theta_stand = np.load(STAND_THETA)
    P = derive_walk_port()
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    groups = muscle_groups(m, d, mujoco)

    # THE SEARCH IS SIX NUMBERS WIDE. Amplitudes start at 0.20 with spread 0.15; phase offsets
    # start at 0 with spread 1.0 rad. Those are STARTING POINTS for a search, not settings -- the
    # elite mean replaces them on turn 0 and nothing downstream reads them.
    nj = len(OSC_JOINTS)
    # amplitudes | phase offsets -- SIX numbers, and only six. The entrainment gains
    # (eps, kappa) are out of the search: the judge drives the clock, so the trainer
    # trains the clock (walk_port LEDGER 2026-08-03).
    mu = np.concatenate([np.full(nj, 0.20), np.zeros(nj)])
    sd = np.concatenate([np.full(nj, 0.15), np.full(nj, 1.0)])
    if init:
        mu = np.load(init); sd = 0.5 * sd
        print(f"warm start from {init}")
    elite = max(3, pop // 5)
    rng = np.random.default_rng(0)
    hist, best_ever = [], (-np.inf, mu.copy())

    print(f"\nTRAINING THE WALK PORT -- {N_FREE} free numbers "
          f"(omega {P['OUT omega_rad_s']:.4f} rad/s and the antiphase are DERIVED, not searched)")
    print(f"  target {P['OUT target_speed_ms']:.4f} m/s, stride {P['OUT stride_s']:.4f} s, "
          f"duty {P['OUT duty_factor']:.4f}, g {g:.4f}, stand theta FROZEN ({theta_stand.size} numbers)")
    print(f"{'turn':>5}{'best':>9}{'mean':>9}{'speed':>9}{'% tgt':>7}{'period':>8}"
          f"{'dutyR':>7}{'dutyL':>7}{'held':>7}  verdict")
    for turn in range(turns):
        cand = rng.normal(mu, sd, size=(pop, N_FREE))
        cand[:, :nj] = np.clip(cand[:, :nj], 0.0, 1.0)          # an amplitude is an activation
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
        draw_turn(turn, P, tr, pics, hist, OUTDIR / f"walk_turn_{turn:02d}.png")
    np.save(WALK_THETA, best_ever[1])
    print(f"\nsaved the SESSION'S best (score {best_ever[0]:.3f}), not the last turn's -> {WALK_THETA}")
    print(f"PICTURES: {OUTDIR}/walk_turn_*.png")
    print("A TURN YOU HAVE NOT LOOKED AT DID NOT END.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
