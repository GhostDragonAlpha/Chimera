"""train_return.py -- v14 THE RETURN: the recovery curriculum over REAL post-release states.

docs/THE_GRAB.md v14. Runs 14-15 measured the deficit to the state, not the event and not
a policy: the carry equilibrium lies outside every proven policy's recovery basin, and
end-to-end cycle training cannot fix that because its candidates reach the post-release
state already committed (and usually already falling). This trains the recovery FROM the
recorded states: each candidate is reset into snapshots drawn from release_states.npz
(collect_release_states.py -- the actual full-cycle trajectory, muscle activations
included) and asked to STAND from there for 3.0 s, F3's own bar.

The policy class is the stand formula (a0 | kh | kp | kr) -- NOTHING ADDED by default.
With --rates (v15, THE SPINDLE): the three rate blocks (z-dot, pitch-rate, roll-rate --
the time-derivatives of the SAME sensed quantities) join the search; a 4-block init is
zero-padded onto them, which preserves the incumbent's behavior exactly.

Warm start from stand_theta.npy. Output: return_theta.npy, the session's best, never the
last turn's. Every turn ends in a picture.

    python tools/train_return.py --turns 48 --pop 32
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body
from stand_port import derive_stand_port, stand_reward, MYOBODY
from train_stand import joint_ids, joint_frac
from grab_port import derive_grab_port, stone_xml, support_stone_weight, WELD_NAME, STONE_BODY
from train_walk import foot_contact
from train_carry import evaluate as _carry_eval  # for the derived _wb/_wl one landmark

OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"
STAND_THETA = OUTDIR / "stand_theta.npy"
RETURN_THETA = OUTDIR / "return_theta.npy"
STATES_NPZ = OUTDIR / "release_states.npz"
SECS = 3.0            # the membrane's bar: hold F3's 80% for 3.0 s from EVERY state
N_PER_CAND = 3        # snapshots drawn per candidate per evaluation


def _restore(m, d, mujoco, st, spec, eq):
    """Reset INTO a recorded post-release state -- the state the full cycle produced."""
    mujoco.mj_setState(m, d, st, spec)          # time, qpos, qvel, act (activations too)
    d.eq_active[eq] = 0                         # the weld stays released
    support_stone_weight(m, d, mujoco, 1.0)     # the giver HAS the stone -- xfrc, not mass
    mujoco.mj_forward(m, d)


def evaluate(m, d, mujoco, theta, P, states, spec, eq, jids, rng, secs=SECS, frames=0,
             fixed=None):
    """One recovery under a candidate, from N_PER_CAND drawn snapshots. Score: the mean of
    per-snapshot (mean gaussian reward x survived fraction) -- the multiplicative form, no
    chosen constant, falls priced by the survived fraction alone."""
    nu = m.nu
    a0, kh, kp = theta[:nu], theta[nu:2 * nu], theta[2 * nu:3 * nu]
    kr = theta[3 * nu:4 * nu] if theta.size >= 4 * nu else np.zeros(nu)
    # v15 (THE SPINDLE, THE_GRAB.md): the rates of the SAME three sensed quantities --
    # zeros for a 4-block checkpoint, so the position-only incumbent runs unchanged
    kv = theta[4 * nu:5 * nu] if theta.size >= 7 * nu else np.zeros(nu)
    kpv = theta[5 * nu:6 * nu] if theta.size >= 7 * nu else np.zeros(nu)
    krv = theta[6 * nu:7 * nu] if theta.size >= 7 * nu else np.zeros(nu)
    wb = _carry_eval._wb if hasattr(_carry_eval, "_wb") else None
    if wb is None:
        # derive the one landmark exactly as train_carry does (body mass x the world's g)
        sb = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, STONE_BODY)
        gm = float(np.linalg.norm(m.opt.gravity))
        wb = float(m.body_mass.sum() - m.body_mass[sb]) * gm
    tgt = P["OUT pelvis_target_m"]
    idxs = fixed if fixed is not None else rng.choice(len(states), size=min(N_PER_CAND, len(states)),
                                                      replace=False)
    steps = int(secs / m.opt.timestep)
    per_state, traces, all_pics = [], [], []
    ren = mujoco.Renderer(m, height=240, width=320) if frames else None
    for si in idxs:
        _restore(m, d, mujoco, states[si], spec, eq)
        grab = set(np.linspace(0, steps - 1, frames).astype(int)) if frames else set()
        tr = {"t": [], "z": [], "jf": []}
        pics, tot, n, fell = [], 0.0, 0, False
        for k in range(steps):
            if k % 20 == 0:
                z = float(d.qpos[2])
                q = d.qpos[3:7]
                pitch = float(np.arctan2(2 * (q[0] * q[2] - q[3] * q[1]),
                                         1 - 2 * (q[1] ** 2 + q[2] ** 2)))
                roll = float(np.arctan2(2 * (q[0] * q[1] + q[2] * q[3]),
                                        1 - 2 * (q[1] ** 2 + q[2] ** 2)))
                u = a0 + kh * (tgt - z) + kp * pitch + kr * roll
                if theta.size >= 7 * nu:
                    # the SPINDLE channels: z-dot from the free joint, and the body's
                    # world-frame angular velocity projected on the roll (x) / pitch (y)
                    # axes -- the rates of roll and pitch themselves, not new quantities
                    rot = np.zeros(9)
                    mujoco.mju_quat2Mat(rot, np.array(q, dtype=np.float64))
                    om = rot.reshape(3, 3) @ np.array(d.qvel[3:6])
                    u = u + kv * float(d.qvel[2]) + kpv * float(om[1]) + krv * float(om[0])
                d.ctrl[:] = np.clip(u, 0.0, 1.0)
            mujoco.mj_step(m, d)
            if k in grab and ren is not None:
                ren.update_scene(d); pics.append(ren.render().copy())
            if k % 20 == 0:
                z = float(d.qpos[2])
                if not np.isfinite(z):
                    fell = True
                    break
                com = d.subtree_com[0]
                _b = lambda nm: d.xpos[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, nm)]
                foot = 0.25 * (_b("calcn_r") + _b("calcn_l") + _b("toes_r") + _b("toes_l"))
                dx, dy = float(com[0] - foot[0]), float(com[1] - foot[1])
                if z < 0.5 * tgt:
                    fell = True
                jf = joint_frac(d, jids)
                _, parts = stand_reward(z, (dx, dy), jf, False, float(np.abs(d.ctrl).mean()), P)
                # v11's one-sided joints term (THE_GRAB.md): the tissue owns the stop
                r_joints = float(np.exp(-((max(jf - 1.0, 0.0) / 0.1) ** 2)))
                r = parts["height"] * parts["support"] * r_joints
                # THE LOAD FACTOR at expect = body weight alone: the feet carry the body,
                # the stone is on the floor (the giver's). A state restored mid-collapse
                # reads what it is; nothing to exploit -- sfc is scoped to the weld, and
                # there is no weld here.
                cr, cl = foot_contact(m, d, mujoco)
                lf = min(max((cr + cl) / wb, 0.0), 1.0)
                r *= lf
                tot += r; n += 1
                tr["t"].append(k * m.opt.timestep); tr["z"].append(z); tr["jf"].append(jf)
            if fell:
                break
        per_state.append((tot / max(n, 1)) * ((k + 1) / steps))
        traces.append(tr)
        if pics:
            all_pics.append(np.concatenate(pics, axis=1))
    if ren is not None:
        ren.close()
    return float(np.mean(per_state)), per_state, traces, all_pics, idxs


def judge_all(m, d, mujoco, theta, P, states, spec, eq, jids, secs=SECS):
    """F3's bar from EVERY state -- the prediction's first clause. Returns per-state
    (pelvis min, fraction of target, worst jf, survived s)."""
    rows = []
    tgt = P["OUT pelvis_target_m"]
    for si in range(len(states)):
        _, _, traces, _, _ = evaluate(m, d, mujoco, theta, P, states, spec, eq, jids,
                                      np.random.default_rng(0), secs=secs, fixed=[si])
        tr = traces[0]
        zmin = min(tr["z"]) if tr["z"] else 0.0
        jmax = max(tr["jf"]) if tr["jf"] else 0.0
        held = len(tr["t"]) * 0.02
        rows.append((si, zmin, 100 * zmin / tgt, jmax, held))
    return rows


def draw_turn(turn, P, per_state, traces, pics, hist, path, idxs):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(14.5, 7.4))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.1, 1], hspace=0.36, wspace=0.24)
    if pics:
        ax = fig.add_subplot(gs[0, :])
        # a state the body falls from early renders FEWER frames -- pad each strip to the
        # widest so the stack is rectangular (a short strip IS the picture of the fall)
        w = max(p.shape[1] for p in pics)
        pics = [np.pad(p, ((0, 0), (0, w - p.shape[1]), (0, 0)), constant_values=255)
                for p in pics]
        ax.imshow(np.concatenate(pics, axis=0)); ax.axis("off")
        ax.set_title(f"turn {turn} — the best candidate RECOVERING from states "
                     f"{list(idxs)} (one strip per state)", fontsize=10)
    tgt = P["OUT pelvis_target_m"]
    ax = fig.add_subplot(gs[1, 0])
    for tr, si in zip(traces, idxs):
        ax.plot(tr["t"], tr["z"], lw=1.6, label=f"state {si}")
    ax.axhline(tgt, color="#1a7f37", lw=2.2, label=f"derived target {tgt:.4f} m")
    ax.axhline(0.8 * tgt, color="#1a7f37", ls="--", lw=1.3, label="80% — F3's bar")
    ax.set_xlabel("s"); ax.set_ylabel("m"); ax.legend(fontsize=7, loc="lower left")
    ax.set_title("THE RETURN: pelvis from each reset state", fontsize=9)
    ax = fig.add_subplot(gs[1, 1])
    ax.plot([h[0] for h in hist], [h[1] for h in hist], "o-", color="#2471a3")
    ax.set_xlabel("turn"); ax.set_ylabel("best score")
    ax.set_title("what moved, turn by turn", fontsize=9)
    if traces and traces[0]["jf"]:
        ax2 = ax.twinx()
        for tr in traces:
            ax2.plot(tr["t"], tr["jf"], color="#8e44ad", lw=0.9, alpha=0.45)
        ax2.set_ylabel("worst joint, frac of range", color="#8e44ad", fontsize=7)
        ax2.axhline(1.0, color="#8e44ad", ls=":", lw=1.0)
    zmin = min((min(tr["z"]) for tr in traces if tr["z"]), default=0.0)
    fig.suptitle(f"RETURN PORT — training turn {turn}   pelvis MIN {zmin:.3f} m / target "
                 f"{tgt:.3f} m = {100*zmin/tgt:.0f}%   per-state scores "
                 f"{['%.3f' % s for s in per_state]}", fontsize=11.5)
    fig.savefig(path, dpi=100, bbox_inches="tight"); plt.close(fig)


def main() -> int:
    import mujoco
    a = sys.argv
    turns = int(a[a.index("--turns") + 1]) if "--turns" in a else 48
    pop = int(a[a.index("--pop") + 1]) if "--pop" in a else 32
    secs = float(a[a.index("--secs") + 1]) if "--secs" in a else SECS
    init = a[a.index("--init") + 1] if "--init" in a else str(STAND_THETA)
    out = Path(a[a.index("--out") + 1]) if "--out" in a else RETURN_THETA
    OUTDIR.mkdir(parents=True, exist_ok=True)
    if not Path(init).exists():
        raise SystemExit(f"no {init} -- the return is composed over standing. Refusing.")
    if not STATES_NPZ.exists():
        raise SystemExit(f"no {STATES_NPZ} -- run tools/collect_release_states.py first.")

    z = np.load(STATES_NPZ)
    states_all, times, spec = z["states"], z["times"], int(z["spec"])
    P = derive_stand_port()
    G = derive_grab_port()
    path = stone_xml(MYOBODY, G)
    m, g = load_body(path, mujoco)
    d = mujoco.MjData(m)
    eq = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_EQUALITY, WELD_NAME)
    jids = joint_ids(m, mujoco)
    # THE CURRICULUM'S EDGE: only states the body is still UP in. Past the fell line
    # (pelvis < 50% of target -- the trainer's own line) is a get-up task, not this
    # membrane; those states are the carry policy's failure, not the recovery's job.
    # FULLPHYSICS layout is [time, qpos, qvel, act], so pelvis z sits at st[1 + 2].
    keep = [i for i, st in enumerate(states_all)
            if float(st[1 + 2]) >= 0.5 * P["OUT pelvis_target_m"]]
    if "--only" in a:
        # THE SPECIALIST VARIANT (v14 addendum): the real cycle is DETERMINISTIC -- the
        # recovery only ever faces the ONE state the carry policy produces at the release
        # and its immediate neighborhood. --only 0,1,2 restricts the curriculum to those
        # recorded states (indices into the STANDING set). Not an exploit: the two-stage
        # full-cycle audit is the judge, and it produces exactly these states.
        only = [int(x) for x in a[a.index("--only") + 1].split(",")]
        keep = [keep[i] for i in only if i < len(keep)]
    states = states_all[keep]
    print(f"curriculum: {len(states)} of {len(states_all)} states are above the fell line "
          f"(t = {['%.2f' % times[i] for i in keep]})")
    if len(states) < 1:
        raise SystemExit("the curriculum is empty. Refusing.")

    nu = m.nu
    dim = 7 * nu if "--rates" in a else 4 * nu   # v15: the SPINDLE blocks join the search
    mu = np.load(init)
    if mu.size == 4 * nu and dim == 7 * nu:
        # v15's STATED pad (v13's precedent): the rate blocks are new; zeros reproduce the
        # incumbent's behavior EXACTLY (every rate term vanishes) -- verified at turn 0
        mu = np.concatenate([mu, np.zeros(3 * nu)])
        print(f"rate blocks zero-padded ({4 * nu} -> {dim}): the incumbent's behavior is preserved")
    if mu.size != dim:
        raise SystemExit(f"{init} is {mu.size} numbers, the search is {dim} -- refusing to "
                         f"pad or truncate a foundation (the theta-pair lesson, THE_GRAB v8).")
    sd = 0.5 * np.concatenate([np.full(nu, 0.15)] + [np.full(nu, 0.6)] * (dim // nu - 1))
    print(f"warm start from {init} ({dim} numbers) over {len(states)} REAL post-release states")
    elite = max(3, pop // 5)
    rng = np.random.default_rng(0)
    hist = []
    best_ever = (-np.inf, mu.copy())

    # THE CONTROL: the incumbent (the F3-proven stand) from every state, BEFORE training --
    # the swap test said it falls; this numbers it per state so the training's debt is exact.
    rows = judge_all(m, d, mujoco, mu, P, states, spec, eq, jids, secs=secs)
    print(f"\nCONTROL (the stand theta, untrained) from every state:")
    for si, zmin, frac, jmax, held in rows:
        print(f"  state {si:2d}: pelvis MIN {zmin:.3f} m = {frac:5.1f}%  jmax {jmax:.2f}  "
              f"held {held:.2f}s  {'PASS' if frac >= 80 and held >= secs - 0.01 else 'falls'}")

    print(f"\nTRAINING THE RETURN — F3's bar (80% of {P['OUT pelvis_target_m']:.4f} m) for "
          f"{secs:.1f} s from EVERY state, g {g:.4f}")
    print(f"{'turn':>5}{'best':>10}{'mean':>10}{'worst-state':>13}{'pelvis MIN':>13}{'% of target':>13}{'held':>8}{'jmax':>7}  verdict")
    for turn in range(turns):
        cand = rng.normal(mu, sd, size=(pop, dim))
        cand[0] = mu                            # the incumbent is always a candidate
        cand[:, :nu] = np.clip(cand[:, :nu], 0.0, 1.0)
        scores = np.array([evaluate(m, d, mujoco, c, P, states, spec, eq, jids, rng, secs)[0]
                           for c in cand])
        order = np.argsort(-scores)
        el = cand[order[:elite]]
        mu, sd = el.mean(0), el.std(0) + 1e-3
        best_theta = cand[order[0]]
        # the turn's picture + numbers: judge the best from a FIXED trio (first, middle,
        # last standing state) so turns are comparable, not the rng's draw
        trio = [0, len(states) // 2, len(states) - 1]
        s, per_state, traces, pics, idxs = evaluate(m, d, mujoco, best_theta, P, states,
                                                    spec, eq, jids, rng, secs, frames=3,
                                                    fixed=trio)
        held_min = min(min(tr["z"]) for tr in traces if tr["z"]) if traces else 0.0
        frac = 100 * held_min / P["OUT pelvis_target_m"]
        survived = min(len(tr["t"]) for tr in traces) * 0.02
        worst_j = max((max(tr["jf"]) for tr in traces if tr["jf"]), default=0.0)
        ok = frac >= 80.0 and survived >= secs - 0.01
        hist.append((turn, float(scores[order[0]])))
        if float(scores[order[0]]) > best_ever[0]:
            best_ever = (float(scores[order[0]]), cand[order[0]].copy())
        print(f"{turn:>5}{scores[order[0]]:>10.3f}{scores.mean():>10.3f}{min(per_state):>13.3f}"
              f"{held_min:>12.3f}m{frac:>12.0f}%{survived:>7.2f}s{worst_j:>7.2f}"
              f"  {'PROVEN(trio)' if ok else 'not yet'}")
        draw_turn(turn, P, per_state, traces, pics, hist, OUTDIR / f"return_turn_{turn:02d}.png", idxs)
    np.save(out, best_ever[1])
    print(f"\nsaved the SESSION'S best (score {best_ever[0]:.3f}) to {out}")

    # THE PREDICTION'S FIRST CLAUSE, JUDGED: the session's best from EVERY state.
    rows = judge_all(m, d, mujoco, best_ever[1], P, states, spec, eq, jids, secs=secs)
    npass = 0
    print(f"\nVERDICT (the session's best) from every state:")
    for si, zmin, frac, jmax, held in rows:
        ok = frac >= 80.0 and held >= secs - 0.01
        npass += ok
        print(f"  state {si:2d}: pelvis MIN {zmin:.3f} m = {frac:5.1f}%  jmax {jmax:.2f}  "
              f"held {held:.2f}s  {'PASS' if ok else 'FALLS'}")
    print(f"\n{npass}/{len(rows)} states PASS F3's bar. "
          f"{'The prediction holds from the curriculum.' if npass == len(rows) else 'FALSIFIER 1 CHECK: which states fall, and are they the deep ones?'}")
    print(f"\nPICTURES: {OUTDIR}/return_turn_*.png")
    print("A TURN YOU HAVE NOT LOOKED AT DID NOT END.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
