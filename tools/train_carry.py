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

THE SPAWN IS THE WELD'S TARGET, not the floor. spawn_stone puts the stone on the floor for
the GRAB event's sake; here the weld is already on, so the stone is written AT the pose the
weld will hold it in (the torso frame at the keyframe, rotated by the stated carry relpose).
Zero constraint transient, zero qpos writes after the reset -- the spawn IS part of the
reset, same discipline as seat_in_limits and spawn_stone.

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
from grab_port import derive_grab_port, stone_xml, CARRY_RELPOS, STONE_BODY, WELD_NAME

OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"
STAND_THETA = OUTDIR / "stand_theta.npy"
CARRY_THETA = OUTDIR / "carry_theta.npy"


def spawn_carried(m, d, mujoco):
    """Write the stone's freejoint qpos AT the weld's target pose, once, at reset.

    The weld's relpose is the stone's pose in the TORSO frame (stated in grab_port). With
    the weld active from the spawn, placing the stone anywhere else buys a constraint
    transient as the first physics -- a fall the training would then have to unlearn, paid
    for by every candidate. Compute the target from the torso's frame at the seated
    keyframe and write it. Same rule as spawn_stone: a spawn is a reset, not a script.
    """
    torso = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "torso")
    body = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, STONE_BODY)
    if torso < 0 or body < 0:
        raise SystemExit("no torso / no stone -- run stone_xml first (rule 20).")
    rot = np.zeros(9)
    mujoco.mju_quat2Mat(rot, np.array(d.xquat[torso], dtype=np.float64))
    world = np.array(d.xpos[torso], dtype=np.float64) + rot.reshape(3, 3) @ np.array(CARRY_RELPOS)
    wq = np.zeros(4)
    mujoco.mju_mulQuat(wq, np.array(d.xquat[torso], dtype=np.float64), np.array([1.0, 0, 0, 0]))
    a = int(m.jnt_qposadr[int(m.body_jntadr[body])])
    d.qpos[a:a + 7] = np.concatenate([world, wq])
    mujoco.mj_forward(m, d)


def evaluate(m, d, mujoco, theta, P, secs, eq, frames=0):
    """One carried life under a candidate. The weld is ON from the reset -- see module doc.

    theta, the reward, the seating, the bar: train_stand's, unchanged. What changed is the
    world the rollout happens in: 421 N rides at the stated carry pose from t=0, and the
    reward's CoM-over-the-foot-polygon term now prices the lean-back for free -- the body's
    own subtree CoM must stay in the box WHILE the stone pulls it forward-right.
    """
    nu = m.nu
    jids = joint_ids(m, mujoco)
    a0, kh, kp = theta[:nu], theta[nu:2 * nu], theta[2 * nu:]
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    seat_in_limits(m, d, mujoco, jids)      # the body may not START outside its own stops
    spawn_carried(m, d, mujoco)             # the stone AT the weld's target (part of the reset)
    d.eq_active[eq] = 1                     # the weld is ON from t=0 -- this is the carry
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
        ax.set_title(f"turn {turn} — the best candidate CARRYING, {len(pics)} frames", fontsize=10)
    tgt = P["OUT pelvis_target_m"]
    ax = fig.add_subplot(gs[1, 0])
    ax.plot(tr["t"], tr["z"], color="#c0392b", lw=1.9, label="pelvis")
    ax.axhline(tgt, color="#1a7f37", lw=2.2, label=f"derived target {tgt:.4f} m")
    ax.axhline(0.8 * tgt, color="#1a7f37", ls="--", lw=1.3, label="80% — f6's carry bar")
    ax.set_xlabel("s"); ax.set_ylabel("m"); ax.legend(fontsize=7)
    ax.set_title("THE CARRY: pelvis height", fontsize=9)
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
                 f"= {100*hi/tgt:.0f}%   (59.49 kg stone welded ON from the spawn)", fontsize=11.5)
    fig.savefig(path, dpi=100, bbox_inches="tight"); plt.close(fig)


def main() -> int:
    import mujoco
    a = sys.argv
    turns = int(a[a.index("--turns") + 1]) if "--turns" in a else 24
    pop = int(a[a.index("--pop") + 1]) if "--pop" in a else 32
    secs = float(a[a.index("--secs") + 1]) if "--secs" in a else 3.0   # f6's carry window
    init = a[a.index("--init") + 1] if "--init" in a else str(STAND_THETA)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    if not Path(init).exists():
        raise SystemExit(f"no {init} -- carrying is composed over standing. Refusing.")

    P = derive_stand_port()
    G = derive_grab_port()
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
          f"stone {G['OUT stone_mass_kg']:.2f} kg ON from the spawn, horizon {secs:.1f} s = f6's window")
    print(f"{'turn':>5}{'best':>10}{'mean':>10}{'pelvis MIN':>13}{'% of target':>13}{'held':>8}{'jmax':>7}  verdict")
    for turn in range(turns):
        cand = rng.normal(mu, sd, size=(pop, dim))
        cand[0] = mu                            # the incumbent is always a candidate (train_stand)
        cand[:, :nu] = np.clip(cand[:, :nu], 0.0, 1.0)
        scores = np.array([evaluate(m, d, mujoco, c, P, secs, eq)[0] for c in cand])
        order = np.argsort(-scores)
        el = cand[order[:elite]]
        mu, sd = el.mean(0), el.std(0) + 1e-3
        best_theta = cand[order[0]]
        s, tr, pics = evaluate(m, d, mujoco, best_theta, P, secs, eq, frames=6)
        held = min(tr["z"]) if tr["z"] else 0.0
        frac = 100 * held / P["OUT pelvis_target_m"]
        survived = len(tr["t"]) * 0.02
        ok = frac >= 80.0 and survived >= secs - 0.01     # f6's bar, f6's horizon
        hist.append((turn, float(scores[order[0]])))
        if float(scores[order[0]]) > best_ever[0]:
            best_ever = (float(scores[order[0]]), cand[order[0]].copy())
        print(f"{turn:>5}{scores[order[0]]:>10.3f}{scores.mean():>10.3f}{held:>12.3f}m"
              f"{frac:>12.0f}%{survived:>7.2f}s{max(tr['jf']) if tr['jf'] else 0:>7.2f}  "
              f"{'PROVEN' if ok else 'not yet'}")
        draw_turn(turn, P, tr, pics, hist, OUTDIR / f"carry_turn_{turn:02d}.png")
    np.save(CARRY_THETA, best_ever[1])
    print(f"\nsaved the SESSION'S best (score {best_ever[0]:.3f}) to {CARRY_THETA}")
    print(f"\nPICTURES: {OUTDIR}/carry_turn_*.png")
    print("A TURN YOU HAVE NOT LOOKED AT DID NOT END.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
