"""f5_step.py -- THE BODY WALKS BY OBSERVABLE EVENTS, or THE STEP's falsifiers fire.

`docs/THE_STEP.md`'s harness: the walk's SECOND theory, opened when the first theory's
falsifier 3 fired (STAND + one rhythm, 3,000+ rollouts, never travel AND upright in one body).
MOVE is still a formula registered in the real parser -- but its content is now the STAND port
plus a per-leg two-state machine whose transitions are events the body can observe (touch-sensor
rising edges), never clock ticks (`tools/step_port.py`).

f4'S BARS DO NOT MOVE, and two join them, because the membrane named them before the build:

    1. TRAVEL        mean forward speed within 25% of theHuman's comfortable_speed_ms (0.9924)
    2. PERIODICITY   footfall autocorrelation >= 0.60 -- an OUTPUT here, not an input
    3. UPRIGHT       pelvis >= 80% of the derived stand target for the whole run
    4. EFFORT ABLATION   swing efforts zeroed (gain=0, same code path) -> travel < 20%
    5. SENSOR ABLATION   contact obs zeroed (cr=cl=0, same code path) -> travel < 20%
    6. DUTY          both feet >= 0.50 -- falsifier 1: below it, both feet leave the ground
                     and the machine hops; the interlock is decorative

JUDGE FIVE IS THE THEORY. If travel survives with the sensors zeroed, the transitions are a
clock in disguise and this is the falsifier-3 program wearing a state machine's clothes -- the
machine's own construction makes that legible: a tie (cr == cl == 0) releases no first step, so
the honest outcome of the ablation is a body that simply STANDS.

ZERO POSE-SCRIPTED FRAMES, BY CONSTRUCTION. After `seat_in_limits` at reset, nothing here writes
`d.qpos`. Every frame is `mj_step` under muscle control and this world's gravity.

    python tools/f5_step.py           # exit 0 PASS, 1 FAIL
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body                                              # noqa: E402
from stand_port import derive_stand_port, MYOBODY                        # noqa: E402
from train_stand import joint_ids, seat_in_limits                        # noqa: E402
from step_port import (derive_step_port, muscle_groups, move_formula_fn,  # noqa: E402
                       N_FREE)
from train_walk import foot_contact, CTRL_EVERY                          # noqa: E402
from chimera_gait import _periodicity                                    # noqa: E402
from parser import Parser, default_registry, Formula, EXCLUSIVE          # noqa: E402

OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"
STAND_THETA = OUTDIR / "stand_theta.npy"
STEP_THETA = OUTDIR / "step_theta.npy"
SECS = 6.0                    # JUDGED at 6 s; train_step optimises 8 s -- train past what you judge
SPEED_TOL = 0.25              # the prediction's own 25%
PERIODICITY_BAR = 0.60
UPRIGHT_FRAC = 0.80
ABLATION_BAR = 0.20
DUTY_BAR = 0.50               # falsifier 1: below this, both feet leave the ground -- a hop


def run_one(m, d, mujoco, P, theta_stand, theta_step, groups, tgt, nu, gain,
            sensor_gain=1.0, frames=0):
    """One life THROUGH THE PARSER. `gain=0.0` is the effort ablation, `sensor_gain=0.0` the
    sensor ablation -- both multiply inside the SAME code path, so neither can drift away from
    the thing it ablates."""
    reg = default_registry(theta_stand, tgt, nu)
    reg["MOVE"] = Formula("MOVE", move_formula_fn(theta_stand, theta_step, groups, tgt, nu, P,
                                                  gain=gain), EXCLUSIVE)
    PARSER = Parser(reg)
    PARSER.set_verb("MOVE", True)

    jids = joint_ids(m, mujoco)
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    seat_in_limits(m, d, mujoco, jids)
    steps = int(SECS / m.opt.timestep)
    grab = set(np.linspace(0, steps - 1, frames).astype(int)) if frames else set()
    ren = mujoco.Renderer(m, height=240, width=320) if frames else None
    tr = {k: [] for k in ("t", "x", "z", "cr", "cl", "sup")}
    pics, fell_t, x0, driver = [], None, float(d.qpos[0]), None
    for k in range(steps):
        if k % CTRL_EVERY == 0:
            z = float(d.qpos[2])
            q = d.qpos[3:7]
            pitch = float(np.arctan2(2 * (q[0] * q[2] - q[3] * q[1]),
                                     1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            cr, cl = foot_contact(m, d, mujoco)
            u, trace = PARSER.command({"z": z, "pitch": pitch, "t": float(d.time),
                                       "cr": sensor_gain * cr, "cl": sensor_gain * cl})
            driver = trace.driver
            if u is not None:
                d.ctrl[:] = u
        mujoco.mj_step(m, d)
        if k in grab and ren is not None:
            ren.update_scene(d); pics.append(ren.render().copy())
        if k % CTRL_EVERY == 0:
            z = float(d.qpos[2])
            cr, cl = foot_contact(m, d, mujoco)
            tr["t"].append(k * m.opt.timestep); tr["x"].append(float(d.qpos[0]))
            tr["z"].append(z); tr["cr"].append(cr); tr["cl"].append(cl)
            tr["sup"].append((1.0 if cr > 0 else 0.0) + (1.0 if cl > 0 else 0.0))
            if z < 0.5 * tgt and fell_t is None:
                fell_t = k * m.opt.timestep
                break
    if ren is not None:
        ren.close()
    dt_s = CTRL_EVERY * m.opt.timestep
    per, period = _periodicity(np.array(tr["sup"]), dt_s) if len(tr["sup"]) > 16 else (0.0, 0.0)
    elapsed = max(tr["t"][-1], 1e-9) if tr["t"] else 1e-9
    return dict(speed=(float(tr["x"][-1]) - x0) / elapsed if tr["x"] else 0.0,
                periodicity=per, period_s=period, fell_t=fell_t, driver=driver,
                z_min=min(tr["z"]) if tr["z"] else 0.0, held=elapsed,
                duty_r=float(np.mean([c > 0 for c in tr["cr"]])) if tr["cr"] else 0.0,
                duty_l=float(np.mean([c > 0 for c in tr["cl"]])) if tr["cl"] else 0.0,
                tr=tr, pics=pics)


def run() -> int:
    import mujoco
    if not STEP_THETA.exists():
        raise SystemExit(f"no {STEP_THETA} -- run `python tools/train_step.py` first. Refusing to "
                         f"judge a step that was never trained (rule 20).")
    if not STAND_THETA.exists():
        raise SystemExit(f"no {STAND_THETA} -- walking is composed over standing. Refusing.")
    theta_stand, theta_step = np.load(STAND_THETA), np.load(STEP_THETA)
    P, S = derive_step_port(), derive_stand_port()
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    groups = muscle_groups(m, d, mujoco)
    tgt, nu = S["OUT pelvis_target_m"], m.nu
    vt = P["OUT target_speed_ms"]

    live = run_one(m, d, mujoco, P, theta_stand, theta_step, groups, tgt, nu, 1.0, frames=8)
    abl_e = run_one(m, d, mujoco, P, theta_stand, theta_step, groups, tgt, nu, 0.0)
    abl_s = run_one(m, d, mujoco, P, theta_stand, theta_step, groups, tgt, nu, 1.0,
                    sensor_gain=0.0)

    pct = 100.0 * live["speed"] / vt
    abl_e_pct = 100.0 * abl_e["speed"] / vt
    abl_s_pct = 100.0 * abl_s["speed"] / vt
    ok_travel = abs(live["speed"] - vt) <= SPEED_TOL * vt
    ok_cycle = live["periodicity"] >= PERIODICITY_BAR
    ok_up = live["z_min"] >= UPRIGHT_FRAC * tgt and live["fell_t"] is None
    ok_abl_e = abs(abl_e["speed"]) < ABLATION_BAR * vt
    ok_abl_s = abs(abl_s["speed"]) < ABLATION_BAR * vt
    ok_duty = live["duty_r"] >= DUTY_BAR and live["duty_l"] >= DUTY_BAR
    ok = ok_travel and ok_cycle and ok_up and ok_abl_e and ok_abl_s and ok_duty

    print("\nF5 -- THE BODY WALKS BY OBSERVABLE EVENTS (THE STEP)")
    print("=" * 78)
    print(f"  world: g = {g:.4f} m/s2 (theHuman, via load_body -- never assumed)")
    print(f"  parser driver: {live['driver']}   (MOVE was a named Refusal until this rung)")
    print(f"  DERIVED, not searched: swing window {P['OUT swing_window_s']:.4f} s "
          f"= (1 - {P['OUT duty_factor']:.4f}) x {P['OUT stride_s']:.4f}; "
          f"antiphase and interlock STRUCTURAL")
    print(f"  free numbers trained: {N_FREE} ({theta_step.size} on disk)  |  stand theta FROZEN "
          f"({theta_stand.size} numbers, reused unchanged)")
    if theta_step.size != N_FREE:
        raise SystemExit(f"step_theta.npy holds {theta_step.size} numbers, the port declares "
                         f"{N_FREE}. Refusing to judge a step against a theta of the wrong shape.")
    print("-" * 78)
    print(f"  1. TRAVEL       {live['speed']:+.4f} m/s = {pct:.0f}% of derived "
          f"(bar {100*(1-SPEED_TOL):.0f}-{100*(1+SPEED_TOL):.0f}%)  ->  "
          f"{'PASS' if ok_travel else 'FAIL'}")
    print(f"  2. PERIODICITY  {live['periodicity']:.2f} (bar >= {PERIODICITY_BAR:.2f}), "
          f"period {live['period_s']:.2f} s vs derived stride {P['OUT stride_s']:.2f} s  ->  "
          f"{'PASS' if ok_cycle else 'FAIL'}  (an OUTPUT: no sinusoid exists in this program)")
    print(f"  3. UPRIGHT      pelvis MIN {live['z_min']:.4f} m = "
          f"{100*live['z_min']/tgt:.0f}% of target (bar {100*UPRIGHT_FRAC:.0f}%), held "
          f"{live['held']:.2f}/{SECS:.1f} s  ->  {'PASS' if ok_up else 'FAIL'}")
    print(f"  4. EFFORT ABLATION   swing efforts OFF (gain=0, same code path): "
          f"{abl_e['speed']:+.4f} m/s = {abl_e_pct:.0f}% of derived  ->  "
          f"{'PASS' if ok_abl_e else 'FAIL -- it travels without the efforts; they are decorative'}")
    print(f"  5. SENSOR ABLATION   contact obs zeroed (cr=cl=0, same code path): "
          f"{abl_s['speed']:+.4f} m/s = {abl_s_pct:.0f}% of derived  ->  "
          f"{'PASS -- the sensors are the mechanism' if ok_abl_s else 'FAIL -- it walks blind; the transitions are a clock in disguise (falsifier 2)'}")
    print(f"  6. DUTY         R/L {live['duty_r']:.2f}/{live['duty_l']:.2f} "
          f"(bar >= {DUTY_BAR:.2f} each; theHuman publishes {P['OUT duty_factor']:.2f})  ->  "
          f"{'PASS' if ok_duty else 'FAIL -- both feet leave the ground: it hops (falsifier 1)'}")
    print(f"  qpos writes after reset: 0 (by construction -- the harness contains no write)")
    print("=" * 78)
    print(f"  F5 VERDICT: {'PASS -- the atoms compose: STEP + PLANT + STAND' if ok else 'FAIL'}")
    if not ok:
        which = [n for n, v in (("1 TRAVEL", ok_travel), ("2 PERIODICITY", ok_cycle),
                                ("3 UPRIGHT", ok_up), ("4 EFFORT ABLATION", ok_abl_e),
                                ("5 SENSOR ABLATION", ok_abl_s), ("6 DUTY", ok_duty)) if not v]
        print(f"  FIRED: {', '.join(which)}")
        if not ok_abl_s:
            print("    falsifier 2, verbatim: the sensor ablation still walks -- the transitions")
            print("    are a clock in disguise. This is the falsifier-3 program in a state")
            print("    machine's clothes.")
        if not ok_travel and not ok_cycle and not ok_up:
            print("    falsifier 3's shape: the atoms do not compose -- publish per Rule 17,")
            print("    do not patch with a joint-angle target.")

    # ---- THE PICTURE ------------------------------------------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(15.0, 7.4))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.05, 1], hspace=0.4, wspace=0.28)
    if live["pics"]:
        ax = fig.add_subplot(gs[0, :]); ax.imshow(np.concatenate(live["pics"], axis=1))
        ax.axis("off")
        ax.set_title("eight frames: MOVE held, walking on muscle control and sensor events",
                     fontsize=10)
    t = live["tr"]["t"]
    ax = fig.add_subplot(gs[1, 0])
    ax.plot(t, live["tr"]["x"], color="#c0392b", lw=2.0, label="walked")
    ax.plot(abl_e["tr"]["t"], abl_e["tr"]["x"], color="#7f8c8d", lw=1.6, ls="-.",
            label="efforts off")
    ax.plot(abl_s["tr"]["t"], abl_s["tr"]["x"], color="#b7950b", lw=1.6, ls=":",
            label="sensors zeroed")
    ax.plot(t, [vt * s for s in t], color="#1a7f37", ls="--", lw=1.4, label=f"derived {vt:.3f} m/s")
    ax.set_xlabel("s"); ax.set_ylabel("m"); ax.legend(fontsize=7)
    ax.set_title(f"TRAVEL -- {live['speed']:.3f} m/s ({pct:.0f}%) vs ablations "
                 f"{abl_e_pct:.0f}% / {abl_s_pct:.0f}%", fontsize=9)
    ax = fig.add_subplot(gs[1, 1])
    ax.step(t, [c > 0 for c in live["tr"]["cr"]], color="#c0392b", lw=1.4, where="post", label="R")
    ax.step(t, [1.3 if c > 0 else 0.3 for c in live["tr"]["cl"]], color="#2471a3", lw=1.4,
            where="post", label="L")
    ax.set_ylim(-0.3, 1.9); ax.set_xlabel("s"); ax.legend(fontsize=7)
    ax.set_title(f"FOOTFALL -- periodicity {live['periodicity']:.2f} "
                 f"(bar {PERIODICITY_BAR:.2f}), duty R/L {live['duty_r']:.2f}/{live['duty_l']:.2f}",
                 fontsize=9)
    ax = fig.add_subplot(gs[1, 2])
    ax.plot(t, live["tr"]["z"], color="#8e44ad", lw=1.6)
    ax.axhline(tgt, color="#1a7f37", lw=2.0, label=f"stand target {tgt:.3f} m")
    ax.axhline(UPRIGHT_FRAC * tgt, color="#1a7f37", ls="--", lw=1.2,
               label=f"{100*UPRIGHT_FRAC:.0f}% -- the bar")
    ax.set_xlabel("s"); ax.set_ylabel("m"); ax.legend(fontsize=7)
    ax.set_title(f"UPRIGHT -- pelvis MIN {100*live['z_min']/tgt:.0f}% of target", fontsize=9)
    fig.suptitle(f"F5 -- THE STEP THROUGH THE PARSER   g={g:.3f} m/s2   "
                 f"{'PASS' if ok else 'FAIL'}   speed {pct:.0f}%  periodicity "
                 f"{live['periodicity']:.2f}  ablations {abl_e_pct:.0f}%/{abl_s_pct:.0f}%",
                 fontsize=12)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    png = OUTDIR / "f5_step.png"
    fig.savefig(png, dpi=100, bbox_inches="tight"); plt.close(fig)
    print(f"  PICTURE: {png}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
