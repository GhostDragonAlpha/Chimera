"""train_carry.py -- TRAIN THE CARRY, and only the carry (M8a). The weld is ON from the spawn.

`docs/THE_GRAB.md`'s own prescription, after f6 run 2 measured the finding: the weld is real
(the load destroyed the unloaded posture instantly -- combined CoM ~0.23 m ahead of origin),
so the stand theta cannot carry what it never trained against. This retrains the SAME 870
numbers (the stand formula, nothing added) with the weld ACTIVE FROM THE RESET: the body
learns the lean-back the 59.49 kg stone demands, or it does not and the membrane's falsifier
2 fires at any trained setting.

THE CONTRACT WITH THE JUDGE. f6_grab phase 2 grades pelvis >= 80% of target over the 3.0 s
carry window (T_GRAB+0.2 .. T_DROP). This trains at EXACTLY that horizon -- secs=3.0 -- not
a proxy. train_stand's own docstring records being burned by a 1.0 s proxy satisfying a 5 s
requirement; the carry does not repeat it.

THE EVENT IS THE SATISFIED SNAP (v4, THE_GRAB.md): at t=T_SNAP the stone is written ONCE to
the weld-satisfied pose (the pick-up -- a boundary condition at the event, the same discipline
as the spawn at the reset) and the weld engages with ZERO violation. The earlier versions are
the ledger's own record: born-carry (trained a different event than the judge), floor-snap
(measured a 22 kN solver-artifact spike -- 52x the stone's weight -- throwing every candidate
airborne; the catch of an artifact is M8b's pick-up motion, not this membrane's carried load).
What arrives at the body now is 421 N of stone weight: the physics under test.

Warm start from stand_theta.npy (incumbent always a candidate -- the correctness fix from
train_stand, MEASURED 2026-08-04). Output: carry_theta.npy, the session's best, never the
last turn's. Every turn ends in a picture.

    python tools/train_carry.py --turns 24 --pop 32
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body
from stand_port import derive_stand_port, stand_reward, MYOBODY
from train_stand import joint_ids, seat_in_limits, joint_frac
from grab_port import (derive_grab_port, stone_xml, spawn_stone, snap_stone_to_carry,
                       CARRY_RELPOS, STONE_BODY, WELD_NAME)
from train_walk import foot_contact

OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"
STAND_THETA = OUTDIR / "stand_theta.npy"
CARRY_THETA = OUTDIR / "carry_theta.npy"
T_SNAP = 1.0                    # the weld engages here -- f6's T_GRAB, the judged event
_STONE_LABEL = "59.49 kg"       # set from G in main() -- the dial-pricing runs measured the
                                # hardcoded title misinforming every picture (2026-08-04)


def evaluate(m, d, mujoco, theta, P, G, secs, eq, frames=0):
    """One carried life under a candidate, THE SNAP INCLUDED -- see module doc.

    theta, the reward, the seating, the bar: train_stand's, unchanged. The world: the stone
    spawns on the floor, the weld is INACTIVE, and at t = T_SNAP the weld engages exactly as
    f6's GRAB does -- 421 N arrives as an impulse the policy must catch, then hold. Training
    the catch, not the born-carry: f6 knocked the born-carry theta flat in one frame.
    """
    nu = m.nu
    jids = joint_ids(m, mujoco)
    if not hasattr(evaluate, "_wb"):
        # THE LOAD PATH, PRICED (THE_GRAB v2): the feet must carry what the world holds.
        # Derived from the model -- total mass minus the stone, times the world's own g;
        # the stone's weight from the same model. No chosen constant: the conservation law.
        sb = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, STONE_BODY)
        gm = float(np.linalg.norm(m.opt.gravity))
        evaluate._wb = float(m.body_mass.sum() - m.body_mass[sb]) * gm
        evaluate._wl = float(m.body_mass[sb]) * gm
        # THE SECOND PATH (v3): the stone-floor interface. The stone has exactly one geom
        # (grab_port writes it); the floor is every geom on the worldbody. A contact force
        # here in the carry is the load escaping -- floor-rest AND weld-hang both show it.
        evaluate._sg = int(m.body_geomadr[sb])
        evaluate._floors = {int(gi) for gi in range(m.ngeom) if int(m.geom_bodyid[gi]) == 0}
    wb, wl = evaluate._wb, evaluate._wl
    a0, kh, kp = theta[:nu], theta[nu:2 * nu], theta[2 * nu:]
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    seat_in_limits(m, d, mujoco, jids)      # the body may not START outside its own stops
    spawn_stone(m, d, mujoco, G)            # the stone ON THE FLOOR (part of the reset)
    snap_k = int(T_SNAP / m.opt.timestep)
    tgt = P["OUT pelvis_target_m"]
    steps = int(secs / m.opt.timestep)
    grab = set(np.linspace(0, steps - 1, frames).astype(int)) if frames else set()
    ren = mujoco.Renderer(m, height=240, width=320) if frames else None
    tr = {"t": [], "z": [], "comx": [], "comy": [], "r": [], "jf": [], "sum": [], "sfc": []}
    pics, tot, n, fell = [], 0.0, 0, False
    for k in range(steps):
        if k == snap_k:
            snap_stone_to_carry(m, d, mujoco)   # THE PICK-UP (v4): one write, the event
            d.eq_active[eq] = 1                 # the weld engages SATISFIED -- no artifact
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
            _b = lambda nm: d.xpos[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, nm)]
            foot = 0.25 * (_b("calcn_r") + _b("calcn_l") + _b("toes_r") + _b("toes_l"))
            dx, dy = float(com[0] - foot[0]), float(com[1] - foot[1])
            if z < 0.5 * tgt:
                fell = True
            jf = joint_frac(d, jids)
            r, _ = stand_reward(z, (dx, dy), jf, False, float(np.abs(d.ctrl).mean()), P)
            # THE LOAD FACTOR: the loophole-closer. Airborne prices 0; the floor-rest
            # crouch prices the fraction the feet actually carry; only a true carry ~= 1.
            cr, cl = foot_contact(m, d, mujoco)
            psum = cr + cl
            expect = wb + (wl if k >= snap_k else 0.0)
            lf = min(max(psum / expect, 0.0), 1.0)
            sfc = 0.0
            if k >= snap_k:
                # v3: the stone-floor interface must read ZERO in the carry -- the
                # weld-hang measured 2026-08-04 routes the body's weight through it.
                sg, floors = evaluate._sg, evaluate._floors
                f6 = np.zeros(6)
                for ci in range(d.ncon):
                    c = d.contact[ci]
                    if (c.geom1 == sg and c.geom2 in floors) or (c.geom2 == sg and c.geom1 in floors):
                        mujoco.mj_contactForce(m, d, ci, f6)
                        sfc += abs(float(f6[0]))
                lf *= min(max(1.0 - sfc / wl, 0.0), 1.0)
            r *= lf
            tot += r; n += 1
            tr["t"].append(k * m.opt.timestep); tr["z"].append(z)
            tr["comx"].append(dx); tr["comy"].append(dy); tr["r"].append(r); tr["jf"].append(jf)
            tr["sum"].append(psum); tr["sfc"].append(sfc)
        if fell:
            break
    if ren is not None:
        ren.close()
    # v5: the multiplicative score. Every factor is dimensionless and lives in
    # [0,1] -- mean reward x survived fraction -- so no constant is chosen and
    # no penalty cliff can outrank a load-bearing near-miss. Measured trigger
    # (run 8): a 65%-load carrier falling at 3.7 s scored -3.11, ranked BELOW
    # zero-load survivors at 0.000 -- the additive -3/-2 cliff again, the exact
    # form defect Claude measured on the walk (docs/THE_STEP.md). Falls price
    # themselves through (k+1)/steps; no fell term is needed at all.
    score = (tot / max(n, 1)) * ((k + 1) / steps)
    return float(score), tr, pics


def draw_turn(turn, P, tr, pics, hist, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(14.5, 7.4))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.15, 1], hspace=0.36, wspace=0.26)
    if pics:
        ax = fig.add_subplot(gs[0, :]); ax.imshow(np.concatenate(pics, axis=1)); ax.axis("off")
        ax.set_title(f"turn {turn} — the best candidate CARRYING, {len(pics)} frames", fontsize=10)
    tgt = P["OUT pelvis_target_m"]
    ax = fig.add_subplot(gs[1, 0])
    ax.plot(tr["t"], tr["z"], color="#c0392b", lw=1.9, label="pelvis")
    ax.axhline(tgt, color="#1a7f37", lw=2.2, label=f"derived target {tgt:.4f} m")
    ax.axhline(0.8 * tgt, color="#1a7f37", ls="--", lw=1.3, label="80% — f6's carry bar")
    ax.set_xlabel("s"); ax.set_ylabel("m"); ax.legend(fontsize=7, loc="upper right")
    ax.set_title("THE CARRY: pelvis height + THE LOAD PATH", fontsize=9)
    if tr.get("sum"):
        ax2 = ax.twinx()
        ax2.plot(tr["t"], tr["sum"], color="#7f8c8d", lw=1.0, alpha=0.7, label="plantar N")
        if tr.get("sfc"):
            ax2.plot(tr["t"], tr["sfc"], color="#e67e22", lw=1.0, ls="--", alpha=0.8,
                     label="stone-floor N")
        for y, c, lbl in ((evaluate._wb, "#b7950b", "body"), (evaluate._wb + evaluate._wl, "#1a7f37", "body+stone")):
            ax2.axhline(y, color=c, ls=":", lw=1.0)
            ax2.text(tr["t"][-1], y, f" {lbl}", color=c, fontsize=6, va="bottom")
        ax2.set_ylabel("plantar / stone-floor (N)", color="#7f8c8d", fontsize=7)
        ax2.set_ylim(0, 1.3 * (evaluate._wb + evaluate._wl))
    ax = fig.add_subplot(gs[1, 1])
    hw, hl = P["OUT bos_half_lat_m"], P["OUT bos_half_fore_m"]
    ax.add_patch(matplotlib.patches.Rectangle((-hw, -hl), 2 * hw, 2 * hl, alpha=0.18,
                                              color="#1e8449", ec="#1e8449", lw=2))
    ax.plot(tr["comy"], tr["comx"], color="#c0392b", lw=1.3)
    ax.scatter([0], [0], marker="X", s=110, color="#d35400")
    ax.set_xlim(-0.3, 0.3); ax.set_ylim(-0.3, 0.3); ax.set_aspect("equal")
    ax.set_title("CoM over the base of support (lean-back is the lesson)", fontsize=9)
    ax = fig.add_subplot(gs[1, 2])
    ax.plot([h[0] for h in hist], [h[1] for h in hist], "o-", color="#2471a3")
    ax.set_xlabel("turn"); ax.set_ylabel("best score")
    ax.set_title("what moved, turn by turn", fontsize=9)
    if tr.get("jf"):
        ax2 = ax.twinx(); ax2.plot(tr["t"], tr["jf"], color="#8e44ad", lw=1.0, alpha=0.55)
        ax2.set_ylabel("worst joint, frac of range", color="#8e44ad", fontsize=7)
        ax2.axhline(0.8, color="#8e44ad", ls=":", lw=1.0)
    hi = min(tr["z"]) if tr["z"] else 0.0
    fig.suptitle(f"CARRY PORT — training turn {turn}   pelvis MIN {hi:.3f} m / target {tgt:.3f} m "
                 f"= {100*hi/tgt:.0f}%   ({_STONE_LABEL} stone, the SNAP at {T_SNAP:.1f} s)", fontsize=11.5)
    fig.savefig(path, dpi=100, bbox_inches="tight"); plt.close(fig)


def main() -> int:
    import mujoco
    a = sys.argv
    turns = int(a[a.index("--turns") + 1]) if "--turns" in a else 24
    pop = int(a[a.index("--pop") + 1]) if "--pop" in a else 32
    secs = float(a[a.index("--secs") + 1]) if "--secs" in a else 4.0   # 1.0 s pre-snap + f6's 3.0 s carry window
    init = a[a.index("--init") + 1] if "--init" in a else str(STAND_THETA)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    if not Path(init).exists():
        raise SystemExit(f"no {init} -- carrying is composed over standing. Refusing.")

    P = derive_stand_port()
    G = derive_grab_port()
    global _STONE_LABEL
    _STONE_LABEL = f"{G['OUT stone_mass_kg']:.2f} kg"
    path = stone_xml(MYOBODY, G)
    m, g = load_body(path, mujoco)
    d = mujoco.MjData(m)
    eq = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_EQUALITY, WELD_NAME)
    if eq < 0:
        raise SystemExit(f"no equality {WELD_NAME!r} -- refusing to train a carry with no weld.")
    nu = m.nu
    dim = 3 * nu
    mu = np.load(init)
    sd = 0.5 * np.concatenate([np.full(nu, 0.15), np.full(nu, 0.6), np.full(nu, 0.6)])
    print(f"warm start from {init} (the stand's 870 numbers; the world adds {G['OUT weight_N']:.0f} N)")
    elite = max(3, pop // 5)
    rng = np.random.default_rng(0)
    hist = []
    best_ever = (-np.inf, mu.copy())

    print(f"\nTRAINING THE CARRY PORT — target pelvis {P['OUT pelvis_target_m']:.4f} m, g {g:.4f}, "
          f"stone {G['OUT stone_mass_kg']:.2f} kg on the floor, SNAP at {T_SNAP:.1f} s, "
          f"horizon {secs:.1f} s = 1.0 pre + f6's window")
    print(f"{'turn':>5}{'best':>10}{'mean':>10}{'pelvis MIN':>13}{'% of target':>13}{'held':>8}{'jmax':>7}{'load':>8}{'s-f':>8}  verdict")
    for turn in range(turns):
        cand = rng.normal(mu, sd, size=(pop, dim))
        cand[0] = mu                            # the incumbent is always a candidate (train_stand)
        cand[:, :nu] = np.clip(cand[:, :nu], 0.0, 1.0)
        scores = np.array([evaluate(m, d, mujoco, c, P, G, secs, eq)[0] for c in cand])
        order = np.argsort(-scores)
        el = cand[order[:elite]]
        mu, sd = el.mean(0), el.std(0) + 1e-3
        best_theta = cand[order[0]]
        s, tr, pics = evaluate(m, d, mujoco, best_theta, P, G, secs, eq, frames=6)
        held = min(tr["z"]) if tr["z"] else 0.0
        frac = 100 * held / P["OUT pelvis_target_m"]
        survived = len(tr["t"]) * 0.02
        carry = [s for t, s in zip(tr["t"], tr["sum"]) if t >= T_SNAP + 0.2]
        sfl = [s for t, s in zip(tr["t"], tr["sfc"]) if t >= T_SNAP + 0.2]
        ld = 100 * (float(np.mean(carry)) if carry else 0.0) / (evaluate._wb + evaluate._wl)
        sf = 100 * (float(np.mean(sfl)) if sfl else 0.0) / evaluate._wl
        ok = frac >= 80.0 and survived >= secs - 0.01 and ld >= 80.0 and sf <= 20.0
        hist.append((turn, float(scores[order[0]])))
        if float(scores[order[0]]) > best_ever[0]:
            best_ever = (float(scores[order[0]]), cand[order[0]].copy())
        print(f"{turn:>5}{scores[order[0]]:>10.3f}{scores.mean():>10.3f}{held:>12.3f}m"
              f"{frac:>12.0f}%{survived:>7.2f}s{max(tr['jf']) if tr['jf'] else 0:>7.2f}"
              f"{ld:>7.0f}%{sf:>7.0f}%  {'PROVEN' if ok else 'not yet'}")
        draw_turn(turn, P, tr, pics, hist, OUTDIR / f"carry_turn_{turn:02d}.png")
    np.save(CARRY_THETA, best_ever[1])
    print(f"\nsaved the SESSION'S best (score {best_ever[0]:.3f}) to {CARRY_THETA}")
    print(f"\nPICTURES: {OUTDIR}/carry_turn_*.png")
    print("A TURN YOU HAVE NOT LOOKED AT DID NOT END.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
