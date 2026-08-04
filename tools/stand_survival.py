"""stand_survival.py -- HOW LONG DOES IT ACTUALLY STAND, AND IS THAT A FACT OR A COIN TOSS.

RULE 0, stated before the run:

    STATEMENT   The stand policy's failure is a DETERMINISTIC property of the policy and the
                body, not a lucky initial condition. A perturbation of the start state a million
                times smaller than any grain this world publishes -- 1 micrometre on the free
                joint, 1 microradian on every hinge -- changes the survival time by less than one
                control tick (20 ms).

    PREDICTION  Over 10 seeds x 20 s: survival min = median = max to within 20 ms, and the ten
                pelvis traces lie on one line to the width of the plot.

    FALSIFIER   If the spread in survival time exceeds ONE CONTROL TICK, the stand is
                Lyapunov-divergent and every single-rollout number this project has published
                about standing -- F3's PASS included -- is a coin toss. That is reported, not
                averaged away. (The precedent is measured and in CLAUDE.md: the celebrated
                13.52-body-length walker lost 5.5 body lengths to a ONE-MICRON nudge of its
                start height. This is that test, applied to standing.)

WHY THE PERTURBATION IS A MICRON AND NOT A TUNING KNOB. It is not chosen for effect: it is the
smallest nudge that is unambiguously physically meaningless. `theHuman`'s gait envelope has a
grain of 4.16 deg = 7.3e-2 rad; a microradian is 73,000x below the finest angle this world can
resolve. If a difference that small decides whether the body is standing at t = 12 s, the
difference was never in the initial condition -- it was in the dynamics.

THE PLANT IS THE JUDGE'S PLANT. Control comes through `tools/parser.py`, the same path
`f3_stand.py` drives, not through `train_stand.evaluate`'s inline formula. The two were proven
bit-identical over a 135-sample sweep, and this file still takes the judge's -- a number
optimised against a plant the judge does not run is dead at judgment, and so is a number
MEASURED against one.

    python tools/stand_survival.py                       # 10 seeds x 20 s, the saved theta
    python tools/stand_survival.py --secs 20 --seeds 10 --theta <path>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body                                       # noqa: E402
from stand_port import derive_stand_port, MYOBODY                 # noqa: E402
from train_stand import (joint_ids, seat_in_limits,               # noqa: E402
                         CTRL_EVERY, NUDGE)
from parser import Parser, default_registry                       # noqa: E402
from classify_fall import classify_trace                          # noqa: E402

OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"
LOGDIR = ROOT / "agent_logs"
THETA = OUTDIR / "stand_theta.npy"
# THE NUDGE IS IMPORTED FROM THE TRAINER, not declared here. Not a knob -- see the module
# docstring. Metres on the free joint's translation, radians on every hinge; both are the same
# number because both are 1e-6 of their own unit and the point is that the magnitude is beneath
# meaning in either. It lives in train_stand.py so the search and the instrument that judges it
# cannot perturb by two different amounts and call the disagreement a result (rule 19).


def rollout(m, d, mujoco, theta, P, secs, seed, jids, tgt, nu):
    """One life. `seed = 0` is the UNPERTURBED control; every other seed nudges qpos by NUDGE."""
    PARSER = Parser(default_registry(theta, tgt, nu))
    PARSER.set_verb("STAND", True)
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    seat_in_limits(m, d, mujoco, jids)
    if seed:
        rng = np.random.default_rng(seed)
        d.qpos[:] = d.qpos + rng.normal(0.0, NUDGE, size=d.qpos.shape)
        mujoco.mj_forward(m, d)
    steps = int(secs / m.opt.timestep)
    tr = {k: [] for k in ("t", "z", "comx", "comy", "polx", "poly")}
    _b = lambda n: d.xpos[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, n)]
    for k in range(steps):
        if k % CTRL_EVERY == 0:
            z = float(d.qpos[2])
            q = d.qpos[3:7]
            pitch = float(np.arctan2(2 * (q[0] * q[2] - q[3] * q[1]),
                                     1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            roll = float(np.arctan2(2 * (q[0] * q[1] + q[2] * q[3]),
                                    1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            u, _ = PARSER.command({"z": z, "pitch": pitch, "roll": roll})
            d.ctrl[:] = u if u is not None else 0.0
        mujoco.mj_step(m, d)
        if k % CTRL_EVERY == 0:
            com = d.subtree_com[0]
            foot = 0.25 * (_b("calcn_r") + _b("calcn_l") + _b("toes_r") + _b("toes_l"))
            px = [float(_b(n)[0]) for n in ("calcn_r", "calcn_l", "toes_r", "toes_l")]
            py = [float(_b(n)[1]) for n in ("calcn_r", "calcn_l", "toes_r", "toes_l")]
            tr["t"].append(k * m.opt.timestep)
            tr["z"].append(float(d.qpos[2]))
            tr["comx"].append(float(com[0] - foot[0]))
            tr["comy"].append(float(com[1] - foot[1]))
            tr["polx"].append(max(1e-9, 0.5 * (max(px) - min(px))))
            tr["poly"].append(max(1e-9, 0.5 * (max(py) - min(py))))
    return tr


def main() -> int:
    import mujoco
    a = sys.argv
    secs = float(a[a.index("--secs") + 1]) if "--secs" in a else 20.0
    nseeds = int(a[a.index("--seeds") + 1]) if "--seeds" in a else 10
    tpath = Path(a[a.index("--theta") + 1]) if "--theta" in a else THETA
    if not tpath.exists():
        raise SystemExit(f"no {tpath} -- run `python tools/train_stand.py` first. Refusing to "
                         f"measure the survival of a policy that does not exist (rule 20).")
    theta = np.load(tpath)
    P = derive_stand_port()
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    jids = joint_ids(m, mujoco)
    tgt, nu = P["OUT pelvis_target_m"], m.nu

    print(f"\nSTAND SURVIVAL -- {nseeds} seeds x {secs:.0f} s, theta {tpath.name} "
          f"({theta.size} numbers = {theta.size // nu} blocks x {nu})")
    print(f"  world g {g:.4f} m/s2, target pelvis {tgt:.4f} m, fall bar {0.5*tgt:.4f} m (50%)")
    print(f"  nudge {NUDGE:g} on every qpos for seeds 1..{nseeds-1}; seed 0 is UNPERTURBED")
    print("=" * 104)
    print(f"{'seed':>5}{'survived':>11}{'z_min':>9}{'z_end':>9}{'%tgt_min':>10}"
          f"{'fore_pk':>9}{'lat_pk':>8}{'label':>11}{'conf':>7}  t_fall")
    rows, traces = [], []
    for s in range(nseeds):
        tr = rollout(m, d, mujoco, theta, P, secs, s, jids, tgt, nu)
        cls = classify_trace(tr, tgt)
        surv = cls["t_fall"] if cls["t_fall"] is not None else float(tr["t"][-1])
        zmin = float(min(tr["z"]))
        rows.append(dict(seed=s, survived_s=float(surv), fell=cls["t_fall"] is not None,
                         z_min=zmin, z_end=float(tr["z"][-1]),
                         pct_target_min=100.0 * zmin / tgt, label=cls["label"],
                         confidence=cls["confidence"], t_fall=cls["t_fall"],
                         peak_fore_frac=cls.get("peak_fore_frac"),
                         peak_lat_frac=cls.get("peak_lat_frac"),
                         base_source=cls["base_source"]))
        traces.append(tr)
        tf = f"{cls['t_fall']:.2f}s" if cls["t_fall"] is not None else "-"
        print(f"{s:>5}{surv:>10.2f}s{zmin:>9.3f}{tr['z'][-1]:>9.3f}"
              f"{100*zmin/tgt:>9.1f}%{cls.get('peak_fore_frac', 0):>9.2f}"
              f"{cls.get('peak_lat_frac', 0):>8.2f}{cls['label']:>11}"
              f"{cls['confidence']:>7.2f}  {tf}")
    print("-" * 104)

    surv = np.array([r["survived_s"] for r in rows])
    spread = float(surv.max() - surv.min())
    tick = CTRL_EVERY * m.opt.timestep
    n_fell = sum(1 for r in rows if r["fell"])
    labels = {}
    for r in rows:
        labels[r["label"]] = labels.get(r["label"], 0) + 1
    print(f"  SURVIVAL   min {surv.min():.2f} s   median {float(np.median(surv)):.2f} s   "
          f"max {surv.max():.2f} s   SPREAD {spread:.3f} s")
    # ── THE TRAIN/TEST SPLIT, and the judge should be the one to say it ────────────────────
    # `train_stand --seeds N` scores the WORST of seeds 0..N-1, and this judge measures seeds
    # 0..nseeds-1. The overlap is not a bug -- seed 0 is the unperturbed start and belongs in
    # any judgment -- but a median taken across it mixes seeds the policy was SELECTED on with
    # seeds it has never seen, and those answer different questions. Declared by the caller,
    # never inferred: a judge that guessed how many seeds a trainer used would be inventing the
    # very fact that makes its number mean something (rule 20).
    trained = int(a[a.index("--trained-seeds") + 1]) if "--trained-seeds" in a else 0
    if 0 < trained < nseeds:
        held = surv[trained:]
        print(f"  HELD OUT   seeds {trained}..{nseeds-1} were NOT scored during training: "
              f"median {float(np.median(held)):.2f} s   min {held.min():.2f} s   "
              f"max {held.max():.2f} s")
        print(f"             seeds 0..{trained-1} (trained on): "
              f"median {float(np.median(surv[:trained])):.2f} s")
        print(f"             -> the gap is {float(np.median(surv[:trained]) - np.median(held)):+.2f} s. "
              f"A large positive gap is a policy fitted to its own starts.")
    elif trained >= nseeds:
        print(f"  HELD OUT   NONE -- every seed judged here was scored during training "
              f"({trained} >= {nseeds}). This number cannot distinguish a policy from a fit.")
    print(f"  FELL       {n_fell}/{nseeds} within {secs:.0f} s      labels: "
          + ", ".join(f"{k} x{v}" for k, v in sorted(labels.items())))
    zmins = np.array([r["pct_target_min"] for r in rows])
    print(f"  PELVIS MIN {zmins.min():.1f}%..{zmins.max():.1f}% of target "
          f"(spread {zmins.max()-zmins.min():.2f} points)")
    print("=" * 104)
    determ = spread <= tick + 1e-9
    print(f"  FALSIFIER (spread > one control tick = {tick*1000:.0f} ms): "
          + (f"DOES NOT FIRE -- spread {spread*1000:.1f} ms <= {tick*1000:.0f} ms. The outcome "
             f"is DETERMINISTIC; a single rollout is a measurement here, not a coin toss."
             if determ else
             f"FIRES -- spread {spread*1000:.1f} ms > {tick*1000:.0f} ms. A nudge of {NUDGE:g} "
             f"moves the outcome, so this stand is Lyapunov-divergent and every single-rollout "
             f"number about it (F3 included) is one sample of a distribution."))

    LOGDIR.mkdir(parents=True, exist_ok=True)
    # NAMED AFTER THE THETA UNLESS TOLD OTHERWISE. Three arms judged in one session all wrote
    # `stand_survival.json`, so each overwrote the last and the A/B had one surviving row --
    # the same collision the trainer's per-turn pictures had, one directory over.
    out = Path(a[a.index("--json") + 1]) if "--json" in a \
        else LOGDIR / f"stand_survival_{tpath.stem}.json"
    out.write_text(json.dumps(dict(
        theta=str(tpath.name), theta_size=int(theta.size), secs=secs, seeds=nseeds,
        nudge=NUDGE, g=g, pelvis_target_m=tgt, control_tick_s=tick,
        survival_min_s=float(surv.min()), survival_median_s=float(np.median(surv)),
        survival_max_s=float(surv.max()), survival_spread_s=spread,
        deterministic=bool(determ), n_fell=n_fell, labels=labels, rows=rows,
        trained_seeds=trained,
        survival_median_heldout_s=(float(np.median(surv[trained:]))
                                   if 0 < trained < nseeds else None),
        survival_median_trained_s=(float(np.median(surv[:trained]))
                                   if 0 < trained < nseeds else None),
        pelvis_trace_t=traces[0]["t"], pelvis_traces=[t["z"] for t in traces]), indent=1),
        encoding="utf8")
    print(f"  JSON: {out}")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(15.5, 4.6))
    for i, tr in enumerate(traces):
        ax[0].plot(tr["t"], tr["z"], lw=1.1, alpha=0.85, label=f"seed {i}" if i < 3 else None)
    ax[0].axhline(tgt, color="#1a7f37", lw=2.0, label=f"target {tgt:.3f} m")
    ax[0].axhline(0.5 * tgt, color="#c0392b", ls="--", lw=1.4, label="fall bar 50%")
    ax[0].set_xlabel("s"); ax[0].set_ylabel("pelvis m"); ax[0].legend(fontsize=7)
    ax[0].set_title(f"{nseeds} seeds, nudge {NUDGE:g} -- spread {spread*1000:.1f} ms", fontsize=9)
    for i, tr in enumerate(traces):
        ax[1].plot(tr["comy"], tr["comx"], lw=1.0, alpha=0.8)
    ax[1].add_patch(matplotlib.patches.Rectangle(
        (-P["OUT bos_half_lat_m"], -P["OUT bos_half_fore_m"]),
        2 * P["OUT bos_half_lat_m"], 2 * P["OUT bos_half_fore_m"],
        alpha=0.16, color="#1e8449", ec="#1e8449", lw=2))
    ax[1].set_aspect("equal"); ax[1].set_xlabel("lateral m"); ax[1].set_ylabel("fore-aft m")
    ax[1].set_title("CoM over the base -- which way it leaves", fontsize=9)
    ax[2].bar(range(nseeds), surv, color="#2471a3")
    ax[2].set_xlabel("seed"); ax[2].set_ylabel("survived s")
    ax[2].set_title(f"survival min {surv.min():.2f} / med {np.median(surv):.2f} / "
                    f"max {surv.max():.2f} s", fontsize=9)
    fig.suptitle(f"STAND SURVIVAL -- {tpath.name}, {nseeds}x{secs:.0f} s, g={g:.3f} m/s2   "
                 f"{'DETERMINISTIC' if determ else 'SEED-DEPENDENT'}", fontsize=11.5)
    png = OUTDIR / "stand_survival.png"
    fig.savefig(png, dpi=104, bbox_inches="tight"); plt.close(fig)
    print(f"  PICTURE: {png}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
