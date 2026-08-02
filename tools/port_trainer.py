"""port_trainer.py -- TRAIN ONE PORT. A connection holds its angle as the load arrives.

THE CORRECTION THIS IMPLEMENTS (operator, 2026-08-02): *"You cannot train stand. You can only
train the ports that make stand possible."* `train_stand.py` optimised the OUTCOME -- the fruit.
Stand is what emerges when the branches carry; it is measured, proven and rendered, never trained.

    A PORT IS WORKING WHEN THE JOINT HOLDS ITS ANGLE AS THE LOAD ARRIVES,
    AND BUCKLING IS THE CONNECTION FAILING.

That is per-branch, measurable, and independent of whether the body happens to stay up -- which
is exactly what the outcome-shaped reward was not.

WHAT MAKES THIS A PORT AND NOT A SLICE OF THE WHOLE BODY: a port's actuators are the muscles that
have a MOMENT ARM about that joint, read from the model (`actuator_moment`), never listed by hand.
Every other muscle is frozen at the pose's own equilibrium. So the search is over the connection
itself, and a result cannot be borrowed from somewhere else in the body.

THE REWARD, and every term is the joint's own:
    hold   -- |q(t) - q(0)| small. The angle the load found is the angle it must keep.
    inside -- the joint stays within the range the MODEL declares. Not a preference: past the
              stop the constraint solver is carrying the body, not the muscle.
    quiet  -- least activation that does it. A connection braced at full effort is a strut.

    python tools/port_trainer.py --port hip --turns 4 --pop 20
    python tools/port_trainer.py --port knee   # then ankle, then foot -- in that order
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body
from train_stand import joint_ids, seat_in_limits

MYOBODY = ROOT / "external" / "myo_sim" / "body" / "myobody.xml"
OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"

# Which joints belong to which port. Both sides: a connection that holds on one leg only is not
# a connection this body can stand on.
# THERE ARE THREE PORTS IN THE LEG, NOT FOUR -- and the moment-arm method found that, not I.
# `ankle` and `foot` were trained separately and returned IDENTICAL numbers to three decimals
# across four turns (-0.880, -0.888, -0.884, -0.880, best AND mean). Identical outputs are this
# project's signature of one system wearing two names, so it was checked rather than explained:
#
#     ankle vs foot   IDENTICAL MUSCLE SETS, all 22
#     hip   vs ankle  overlap 0 / 72
#     knee  vs ankle  overlap 4 / 44
#
# It is an anatomical fact, not a bug. Every muscle crossing the ankle also crosses the subtalar
# and MTP joints -- the shank muscles run one tendon past all three rows to the toes. There is no
# activation that turns the toe without turning the ankle, so "train the foot after the ankle" is
# not a sequence this body can perform. One actuator group, three joint rows, ONE PORT.
#
# Kept as separate keys because the JOINTS differ and are all graded; `foot` is an alias that
# trains the same muscles against a different subset of stops.
PORTS = {
    "hip":   ("hip_flexion_r", "hip_flexion_l", "hip_adduction_r", "hip_adduction_l"),
    "knee":  ("knee_angle_r", "knee_angle_l"),
    "ankle": ("ankle_angle_r", "ankle_angle_l", "subtalar_angle_r", "subtalar_angle_l",
              "mtp_angle_r", "mtp_angle_l"),      # the distal port, all three rows at once
    "foot":  ("subtalar_angle_r", "subtalar_angle_l", "mtp_angle_r", "mtp_angle_l"),
}


def port_muscles(m, d, mujoco, joint_names, thresh=1e-4):
    """The muscles that ACTUATE this port, found by moment arm rather than by name.

    `actuator_moment` is the (nu x nv) map from actuator force to joint torque. A muscle with a
    non-zero entry against this joint's DOF can turn it; one without cannot, whatever it is
    called. Reading the model instead of a hand-written list is the difference between training
    the connection and training whatever somebody remembered to type.
    """
    mujoco.mj_forward(m, d)
    # actuator_moment is SPARSE in this MuJoCo build (4850 entries, not nu*nv = 15080), so the
    # dense reshape this used to do raised rather than silently mis-indexing -- the good failure.
    # Expand it through the row index the model publishes; never assume a layout.
    mom = np.zeros((m.nu, m.nv))
    flat = np.asarray(d.actuator_moment).ravel()
    for u in range(m.nu):
        n0, adr = int(d.moment_rownnz[u]), int(d.moment_rowadr[u])
        for e in range(n0):
            mom[u, int(d.moment_colind[adr + e])] = flat[adr + e]
    dofs = []
    for jn in joint_names:
        j = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, jn)
        if j >= 0:
            dofs.append(int(m.jnt_dofadr[j]))
    if not dofs:
        raise SystemExit(f"no joints of {joint_names} in this model -- refusing to train nothing.")
    idx = np.where(np.abs(mom[:, dofs]).max(axis=1) > thresh)[0]
    return idx, dofs


def evaluate(m, d, mujoco, jids, mus, qadr, base_ctrl, theta, secs, frames=0):
    """Load the port and see whether it holds. Returns (score, trace, pics)."""
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    seat_in_limits(m, d, mujoco, jids)
    stand_z = float(m.key_qpos[0][2])
    q0 = np.array([float(d.qpos[a]) for a in qadr])
    lim = {a: (c - h, c + h) for a, c, h, _ in jids}
    ctrl = base_ctrl.copy()
    ctrl[mus] = np.clip(theta, 0.0, 1.0)
    steps = int(secs / m.opt.timestep)
    grab = set(np.linspace(0, steps - 1, frames).astype(int)) if frames else set()
    ren = mujoco.Renderer(m, height=240, width=320) if frames else None
    tr = {"t": [], "dq": [], "out": [], "z": []}
    pics, tot, n = [], 0.0, 0
    for k in range(steps):
        d.ctrl[:] = ctrl
        mujoco.mj_step(m, d)
        if k in grab and ren is not None:
            ren.update_scene(d); pics.append(ren.render().copy())
        if k % 20 == 0:
            # THE PORT MUST BE LOADED FOR THE MEASUREMENT TO MEAN ANYTHING.
            # Turn 2's picture: violent 35 deg oscillation for 1.5 s, then FLAT at 11 deg for the
            # remaining 3.5 s -- and the filmstrip shows why. The body is LYING ON THE FLOOR. A hip
            # on the ground carries nothing, so "it held steady" is a measurement of a corpse.
            #
            # Worse, it was an EXPLOIT: the hold term rewards not moving, so A CANDIDATE THAT FALLS
            # FASTER SCORED BETTER -- 70% of the rollout spent flat on the floor at low drift. The
            # optimiser found it immediately, which is what an optimiser is for (the exploit is the
            # product; iterate the objective, never the artifact).
            #
            # Same species as the ground branch closing at +0.7% while carrying a heap: technically
            # correct, about a body that is not doing the thing.
            if float(d.qpos[2]) < 0.75 * stand_z:
                break                      # unloaded from here on; stop scoring, do not reward it
            q = np.array([float(d.qpos[a]) for a in qadr])
            drift = float(np.abs(q - q0).max())
            out = max(0.0, max(max(lim[a][0] - float(d.qpos[a]),
                                   float(d.qpos[a]) - lim[a][1]) for a in qadr))
            hold = float(np.exp(-(drift / 0.15) ** 2))       # 0.15 rad ~ 8.6 deg of give
            inside = float(np.exp(-(out / 0.05) ** 2))
            quiet = 1.0 - 0.1 * float(np.mean(ctrl[mus]))
            tot += hold * inside * quiet
            n += 1
            tr["t"].append(k * m.opt.timestep); tr["dq"].append(np.degrees(drift))
            tr["out"].append(np.degrees(out)); tr["z"].append(float(d.qpos[2]))
    if ren is not None:
        ren.close()
    # SURVIVAL IS A PRECONDITION, NOT A DIVISOR -- and that distinction is the whole fix.
    #
    # This was `mean(hold) * frac_survived`. Eight turns later every column said progress: mean
    # monotonic, drift inside the 8.6 deg band three turns running. Then the picture: THE X-AXIS
    # ENDED AT 0.42 s of a 5.0 s rollout, and the filmstrip said "1 frames under load".
    #
    #     "WORST DRIFT 8.1 DEG" WAS THE DRIFT OVER 0.42 SECONDS.
    #
    # max(drift) IS NOT COMPARABLE ACROSS EPISODES OF DIFFERENT LENGTH: a short window has fewer
    # chances to exceed a bar. The drift never shrank -- the measurement window did. Having closed
    # the "lie on the floor and farm the hold term" exploit last turn by gating on load, the
    # optimiser simply moved to LEAVING the loaded state faster, and a multiplicative frac was
    # not enough to make that unprofitable. Two exploits, two turns, both found by looking.
    #
    # A weight lets a short episode BUY its way past the bar. A precondition does not. So the
    # score is the mean hold ONLY if the port carried for the whole episode; short of that it is
    # the survived fraction alone, which is strictly worse than any full-length run and orders
    # candidates by how long they carried -- the thing actually being asked for.
    full = steps // 20
    if n < full:
        return float(n) / max(full, 1) - 1.0, tr, pics       # always < 0; a full run is always > 0
    return float(tot / max(n, 1)), tr, pics


def draw(port, turn, tr, pics, hist, path, nmus):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(14, 6.8))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.2, 1], hspace=0.38, wspace=0.26)
    if pics:
        ax = fig.add_subplot(gs[0, :]); ax.imshow(np.concatenate(pics, axis=1)); ax.axis("off")
        ax.set_title(f"{port} port — turn {turn}, {len(pics)} frames under load", fontsize=10)
    ax = fig.add_subplot(gs[1, 0])
    ax.plot(tr["t"], tr["dq"], color="#c0392b", lw=1.9)
    ax.axhline(8.6, color="#1a7f37", ls="--", lw=1.4, label="the hold band (8.6 deg)")
    ax.set_xlabel("s"); ax.set_ylabel("deg"); ax.legend(fontsize=7)
    ax.set_title("THE PORT: how far the joint drifted from where the load found it", fontsize=9)
    ax = fig.add_subplot(gs[1, 1])
    ax.plot(tr["t"], tr["out"], color="#8e44ad", lw=1.7)
    ax.axhline(0, color="#1a7f37", lw=1.2)
    ax.set_xlabel("s"); ax.set_ylabel("deg past the stop")
    ax.set_title("buckling: past the stop the SOLVER carries the body", fontsize=9)
    ax = fig.add_subplot(gs[1, 2])
    ax.plot([h[0] for h in hist], [h[1] for h in hist], "o-", color="#2471a3")
    ax.set_xlabel("turn"); ax.set_ylabel("best score"); ax.set_title("what moved", fontsize=9)
    worst = max(tr["dq"]) if tr["dq"] else 0.0
    fig.suptitle(f"PORT {port.upper()} — {nmus} muscles found by moment arm   "
                 f"worst drift {worst:.1f} deg   PROVEN = < 8.6 deg for 5 s, never past a stop",
                 fontsize=11)
    fig.savefig(path, dpi=100, bbox_inches="tight"); plt.close(fig)


def main() -> int:
    import mujoco
    a = sys.argv
    port = a[a.index("--port") + 1] if "--port" in a else "hip"
    turns = int(a[a.index("--turns") + 1]) if "--turns" in a else 4
    pop = int(a[a.index("--pop") + 1]) if "--pop" in a else 20
    secs = float(a[a.index("--secs") + 1]) if "--secs" in a else 5.0
    if port not in PORTS:
        raise SystemExit(f"unknown port {port}; have {list(PORTS)}")
    OUTDIR.mkdir(parents=True, exist_ok=True)

    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    mujoco.mj_resetDataKeyframe(m, d, 0)
    jids = joint_ids(m, mujoco)
    seat_in_limits(m, d, mujoco, jids)
    mus, dofs = port_muscles(m, d, mujoco, PORTS[port])
    qadr = [int(m.jnt_qposadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, jn)])
            for jn in PORTS[port] if mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, jn) >= 0]
    base = np.full(m.nu, 0.05)

    print(f"\nPORT {port.upper()} — {len(mus)} of {m.nu} muscles actuate it "
          f"(found by moment arm, not by name)   g = {g:.4f}")
    print(f"{'turn':>5}{'best':>10}{'mean':>10}{'worst drift':>14}{'past stop':>12}  verdict")
    mu = np.full(len(mus), 0.10)
    sd = np.full(len(mus), 0.25)
    rng = np.random.default_rng(0)
    hist, best = [], mu.copy()
    for turn in range(turns):
        cand = np.clip(rng.normal(mu, sd, size=(pop, len(mus))), 0.0, 1.0)
        sc = np.array([evaluate(m, d, mujoco, jids, mus, qadr, base, c, secs)[0] for c in cand])
        o = np.argsort(-sc)
        el = cand[o[:max(3, pop // 5)]]
        mu, sd = el.mean(0), el.std(0) + 1e-3
        best = cand[o[0]]
        s, tr, pics = evaluate(m, d, mujoco, jids, mus, qadr, base, best, secs, frames=6)
        drift = max(tr["dq"]) if tr["dq"] else 999.0
        past = max(tr["out"]) if tr["out"] else 999.0
        hist.append((turn, float(sc[o[0]])))
        ok = drift < 8.6 and past <= 0.01
        print(f"{turn:>5}{sc[o[0]]:>10.3f}{sc.mean():>10.3f}{drift:>12.1f}deg{past:>10.1f}deg  "
              f"{'PROVEN' if ok else 'not yet'}")
        draw(port, turn, tr, pics, hist, OUTDIR / f"port_{port}_turn{turn:02d}.png", len(mus))
    np.save(OUTDIR / f"port_{port}_theta.npy", best)
    print(f"\nPICTURES: {OUTDIR}/port_{port}_turn*.png")
    print("A PORT YOU HAVE NOT LOOKED AT IS NOT PROVEN.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
