"""f6_grab.py -- THE BODY FEELS THE STONE, or THE GRAB's falsifiers fire.

`docs/THE_GRAB.md`'s harness (M8a: the carried load). The stone is the slice's own (59.49 kg
of quartzite -- the FINDING: 63% of body mass, not the "5-10%" the prediction guessed; the
doc's arithmetic was corrected BEFORE the first run). GRAB is a parser Formula (OVERLAY):
held + inside the derived reach -> the weld engages and the stone's weight joins the body's
load path.

THE THREE PHASES, each a stated prediction:

    1. THE LOAD IS FELT     weld engaged at t=1.0 s; the plantar sum over the next 0.7 s must
                            exceed the pre-grab sum by weight_N (421.0 N) within the sensors'
                            own noise -- measured as a DELTA, so the zones' heel blind spot
                            (action_tests: the zones miss the stance heel) cancels.
    2. THE BODY STANDS      pelvis >= 80% of target through the carry. CONFOUND, stated: the
                            32-ligament world's UNLOADED stand fell at 6.24 s (c95131f); the
                            retrained theta holds 7.00 s (d15128e). This phase runs 3.0 s so
                            the read is the load's, not the foundation's.
                            Falsifier 2 (cannot stand at ANY trained setting) is NOT judged
                            until the stand repair lands -- THE_GRAB's NEXT item 2 said so.
    3. DROPPING IS FELT     weld released at t=4.0 s; the sum must return to the unloaded
                            band and the stone must fall ballistically to rest (a_throw's
                            gravity, already PROVEN) -- falsifier 3.

ZERO POSE-SCRIPTED FRAMES after reset, with ONE stated exception: THE PICK-UP (v4,
docs/THE_GRAB.md). At T_GRAB the stone's qpos is written ONCE to the weld-satisfied pose
-- a boundary condition at the event, the same discipline as `spawn_stone` at the reset --
and the weld engages SATISFIED. The earlier floor-snap was measured to be a 22 kN solver
artifact (52x the stone's weight; every candidate thrown airborne): the catch of an
artifact is M8b's pick-up motion, not this membrane's carried load. Every frame after the
event is mj_step under muscle control and this world's gravity.

    python tools/f6_grab.py           # exit 0 PASS, 1 FAIL
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
from grab_port import (derive_grab_port, stone_xml, spawn_stone,          # noqa: E402
                       snap_stone_to_carry, grab_formula_fn, STONE_BODY, WELD_NAME,
                       support_stone_weight, RAMP_S, T_DROP)               # noqa: E402
from train_walk import foot_contact, CTRL_EVERY                          # noqa: E402
from parser import Parser, default_registry, Formula, OVERLAY            # noqa: E402

OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"
STAND_THETA = OUTDIR / "stand_theta.npy"
CARRY_THETA = OUTDIR / "carry_theta.npy"
T_GRAB = 1.0                    # the weld engages here (held from t=0; inside reach by design)
SECS = 6.0                      # T_DROP lives in grab_port (v12): trainer and judge, one event
UPRIGHT_FRAC = 0.80
LOAD_TOL = 0.20                 # the delta must land within 20% of weight_N (zones' blind spot
                                # cancels in the delta; 20% is the membrane's own tolerance shape)


def run() -> int:
    import mujoco
    if not STAND_THETA.exists():
        raise SystemExit(f"no {STAND_THETA} -- carrying is composed over standing. Refusing.")
    # THE CARRY POLICY, when it exists. Phase 2 grades the body THROUGH the carry, and
    # train_carry.py exists precisely because the unloaded stand theta was measured dying
    # under the weld (f6 run 2: pelvis 4%, plantar sum 0). Phases 1 and 3 are DELTAS, so a
    # policy trained with the weld on still yields a clean pre-grab baseline. The theta in
    # use is printed -- an instrument that will not say which policy it graded is the
    # species this project keeps getting caught by.
    theta_path = CARRY_THETA if CARRY_THETA.exists() else STAND_THETA
    if len(sys.argv) > 1:
        theta_path = Path(sys.argv[1])   # e.g. the frontal stand_theta, NO retrain (v10's test)
    theta = np.load(theta_path)
    P, S = derive_grab_port(), derive_stand_port()
    path = stone_xml(MYOBODY, P)
    m, g = load_body(path, mujoco)
    d = mujoco.MjData(m)
    tgt, nu = S["OUT pelvis_target_m"], m.nu
    W = P["OUT weight_N"]

    reg = default_registry(theta, tgt, nu)
    reg["GRAB"] = Formula("GRAB", grab_formula_fn(m, d, P), OVERLAY)
    PARSER = Parser(reg)
    PARSER.set_verb("STAND", True)
    # GRAB is NOT held from t=0 -- the first f6 run did that, and the formula (held + inside
    # reach -> weld) engaged at the first parse, t=0, snapping 421 N onto a body still
    # settling from the spawn. The "fall before GRAB" in that run was the early weld, not the
    # carry. Held from T_GRAB, the pre-phase is a true unloaded baseline.

    jids = joint_ids(m, mujoco)
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    seat_in_limits(m, d, mujoco, jids)
    spawn_stone(m, d, mujoco, P)           # the spawn IS part of the reset (see grab_port)
    sb = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, STONE_BODY)
    eq = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_EQUALITY, WELD_NAME)

    steps = int(SECS / m.opt.timestep)
    grab = set(np.linspace(0, steps - 1, 8).astype(int))
    ren = mujoco.Renderer(m, height=240, width=320)
    tr = {k: [] for k in ("t", "z", "sum", "sz", "weld")}
    pics, dropped, grabbed = [], False, False
    grab_k = None                 # the sim step of the event; the v9 ramp counts from it
    drop_k = int(T_DROP / m.opt.timestep)           # v12: the set-down BEGINS here
    ramp_steps = int(RAMP_S / m.opt.timestep)
    release_k = drop_k + ramp_steps                 # the weld releases AFTER the handoff
    for k in range(steps):
        t = k * m.opt.timestep
        if grabbed:
            # v10/v12: FULL mass+inertia always; the giver's hands taper off over RAMP_S
            # on arrival (v10) and take the weight BACK over the same RAMP_S on the
            # set-down (v12) -- trainer and judge drive the same event (run-4/5 lesson),
            # and the bars judge the carry AFTER arrival completes (windows below).
            if k < drop_k:
                support_stone_weight(m, d, mujoco,
                                     min(1.0, (k - grab_k + 1) / ramp_steps))
            elif k < release_k:
                support_stone_weight(m, d, mujoco,
                                     1.0 - min(1.0, (k - drop_k + 1) / ramp_steps))
            elif k == release_k:
                d.eq_active[eq] = 0               # the giver HAS it -- zero residual
                support_stone_weight(m, d, mujoco, 1.0)   # support zero: free fall to rest
        if k % CTRL_EVERY == 0:
            if not grabbed and t >= T_GRAB:
                snap_stone_to_carry(m, d, mujoco)   # THE PICK-UP (v4): one write, the event
                PARSER.set_verb("GRAB", True)        # the formula then engages the weld SATISFIED
                grabbed = True
                grab_k = k
            if not dropped and t >= T_DROP:
                # v12: the INTENTION to release starts the set-down; the weld itself
                # releases at release_k, after the handoff (the step loop owns it).
                PARSER.set_verb("GRAB", False)
                dropped = True
            z = float(d.qpos[2])
            q = d.qpos[3:7]
            pitch = float(np.arctan2(2 * (q[0] * q[2] - q[3] * q[1]),
                                     1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            roll = float(np.arctan2(2 * (q[0] * q[1] + q[2] * q[3]),
                                    1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            # roll in obs (THE_GRAB v8): the parser prices a 4-block theta's kr term;
            # without it the judge would grade the frontal carry with its roll channel
            # deaf -- trainer and judge change together, the run-4/5 lesson.
            u, trace = PARSER.command({"z": z, "pitch": pitch, "roll": roll, "t": float(d.time)})
            if u is not None:
                d.ctrl[:] = u
        mujoco.mj_step(m, d)
        if k in grab:
            ren.update_scene(d); pics.append(ren.render().copy())
        if k % CTRL_EVERY == 0:
            cr, cl = foot_contact(m, d, mujoco)
            tr["t"].append(t); tr["z"].append(float(d.qpos[2]))
            tr["sum"].append(cr + cl); tr["sz"].append(float(d.xpos[sb][2]))
            tr["weld"].append(int(d.eq_active[eq]))
    ren.close()

    tt = np.array(tr["t"]); sums = np.array(tr["sum"])
    pre = sums[(tt >= T_GRAB - 0.6) & (tt < T_GRAB - 0.1)]
    # v9: the load window starts AFTER the arrival completes (T_GRAB + RAMP_S + 0.1);
    # the bar itself (+-20% of weight_N) does not move -- only the landmark of WHEN the
    # carry is judged, because the weight is no longer teleported.
    post = sums[(tt >= T_GRAB + RAMP_S + 0.1) & (tt < T_GRAB + RAMP_S + 0.8)]
    end = sums[tt >= SECS - 0.5]
    base, loaded, unloaded = float(np.mean(pre)), float(np.mean(post)), float(np.mean(end))
    delta_on, delta_off = loaded - base, unloaded - base
    z_carry = [z for t, z in zip(tr["t"], tr["z"]) if T_GRAB + RAMP_S + 0.1 <= t < T_DROP]
    stone_rest = float(tr["sz"][-1])

    ok_load = abs(delta_on - W) <= LOAD_TOL * W
    # v9 run-11 repair: a window containing a NON-FINITE or through-floor sample is not
    # a pass -- min() SKIPS NaN silently (comparisons are False), so an exploded sim
    # printed 0.9915 m while its own trace showed the body at -10 m. The species this
    # project keeps paying for: a number that moves for reasons you cannot attribute.
    carry_clean = bool(z_carry) and all(np.isfinite(z_carry)) and min(z_carry) > 0.0
    ok_stand = carry_clean and min(z_carry) >= UPRIGHT_FRAC * tgt
    ok_drop = abs(delta_off) <= LOAD_TOL * W and abs(stone_rest - P["OUT stone_radius_m"]) < 0.05

    print("\nF6 -- THE BODY FEELS THE STONE (M8a, the carried load)")
    print("=" * 78)
    print(f"  stone: {P['OUT stone_mass_kg']:.2f} kg quartzite = {W:.1f} N in g {g:.4f} "
          f"({100 * P['OUT load_frac_of_body']:.0f}% of body mass -- THE FINDING)")
    print(f"  weld: {WELD_NAME} -> torso at the stated carry pose; reach {P['OUT reach_m']:.3f} m")
    print(f"  policy: {theta_path.name}")
    print("-" * 78)
    print(f"  1. THE LOAD IS FELT   plantar sum {base:.1f} -> {loaded:.1f} N at the weld "
          f"(delta {delta_on:+.1f} N vs weight {W:.1f} N, tol {100 * LOAD_TOL:.0f}%)  ->  "
          f"{'PASS' if ok_load else 'FAIL -- the weld is decorative and the load is fake (falsifier 1)'}")
    z_show = min(z_carry) if carry_clean else float("nan")
    print(f"  2. THE BODY STANDS    pelvis MIN {z_show:.4f} m "
          f"{'' if carry_clean else '(window NOT CLEAN -- sim exploded/NaN; the old min() would have skipped it silently) '}"
          f"->  {'PASS' if ok_stand else 'FAIL'}  (confound stated: the UNLOADED stand holds 7.00 s retrained)")
    print(f"  3. DROPPING IS FELT   sum {loaded:.1f} -> {unloaded:.1f} N on release "
          f"(residual {delta_off:+.1f} N), stone rests at z {stone_rest:.3f} m "
          f"(radius {P['OUT stone_radius_m']:.3f})  ->  "
          f"{'PASS' if ok_drop else 'FAIL -- gravity is cheated in the carry path (falsifier 3)'}")
    print("=" * 78)
    ok = ok_load and ok_stand and ok_drop
    print(f"  F6 VERDICT: {'PASS -- the player touches the ledger' if ok else 'FAIL'}")

    # ---- THE PICTURE ------------------------------------------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(15.0, 7.2))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.05, 1], hspace=0.4, wspace=0.28)
    if pics:
        ax = fig.add_subplot(gs[0, :]); ax.imshow(np.concatenate(pics, axis=1))
        ax.axis("off")
        ax.set_title("eight frames: stand, GRAB at 1.0 s, carry, drop at 4.0 s", fontsize=10)
    ax = fig.add_subplot(gs[1, :2])
    ax.plot(tr["t"], tr["sum"], color="#c0392b", lw=1.8, label="plantar sum (N)")
    ax.axhline(base, color="#7f8c8d", ls=":", lw=1.2, label=f"baseline {base:.0f} N")
    ax.axhline(base + W, color="#1a7f37", ls="--", lw=1.4, label=f"baseline + weight {W:.0f} N")
    for x, lbl in ((T_GRAB, "GRAB"), (T_DROP, "DROP")):
        ax.axvline(x, color="#8e44ad", lw=1.2, ls="-."); ax.text(x + 0.05, ax.get_ylim()[0], lbl,
                                                                fontsize=8, color="#8e44ad")
    ax.set_xlabel("s"); ax.set_ylabel("N"); ax.legend(fontsize=7)
    ax.set_title(f"THE LOAD PATH -- delta {delta_on:+.0f} N on, {delta_off:+.0f} N off",
                 fontsize=9)
    ax = fig.add_subplot(gs[1, 2])
    ax.plot(tr["t"], tr["z"], color="#8e44ad", lw=1.6, label="pelvis")
    ax.axhline(UPRIGHT_FRAC * tgt, color="#1a7f37", ls="--", lw=1.2, label="80% -- the bar")
    ax2 = ax.twinx()
    ax2.plot(tr["t"], tr["sz"], color="#b7950b", lw=1.2, label="stone z")
    ax2.set_ylabel("stone z (m)", color="#b7950b", fontsize=7)
    ax.set_xlabel("s"); ax.set_ylabel("pelvis (m)"); ax.legend(fontsize=7, loc="lower left")
    ax.set_title("BODY + STONE", fontsize=9)
    fig.suptitle(f"F6 -- THE CARRIED LOAD   g={g:.3f} m/s2   "
                 f"{'PASS' if ok else 'FAIL'}   delta {delta_on:+.0f}/{W:.0f} N   "
                 f"pelvis {100 * min(z_carry) / tgt:.0f}%", fontsize=12)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    png = OUTDIR / "f6_grab.png"
    fig.savefig(png, dpi=100, bbox_inches="tight"); plt.close(fig)
    print(f"  PICTURE: {png}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
