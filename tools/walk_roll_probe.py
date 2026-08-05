"""walk_roll_probe.py -- IS THE WALK JUDGE ZEROING A CHANNEL THE WALK TRAINER FEEDS?

RULE 0, stated before the run:

    STATEMENT   `tools/f4_walk.py` builds its parser obs as `{"z", "pitch", "t"}` and
                `walk_port.move_formula_fn` reads `obs.get("roll", 0.0)`. `train_walk.evaluate`
                computes roll and passes it. If both readings are right, the walk TRAINER drives
                the frozen stand policy's 290-number `kr` block and the walk JUDGE multiplies
                that same block by zero -- 290 of the 1160 frozen numbers dead at judgment.

    PREDICTION  Judging one walk theta with roll present and roll absent gives DIFFERENT travel,
                periodicity and upright time. The stand port measured the roll block as worth
                7.60 -> 9.08 s of survival, CoM peak 1.65 -> 0.49, so its absence is not small.

    FALSIFIER   The two judgments agree to the last digit -- `kr` contributes nothing through
                the walk formula, the reading above is wrong, and there is no defect here.

WHY THIS IS RUN BEFORE THE WALK'S RATE-FEEDBACK ARM IS BUILT. Task 7 compares a PD walk against
a P-only walk. A comparison is only attributable if the judge runs the plant the trainer trained
against; the walk port's own LEDGER (2026-08-03) records this exact species costing a session --
the trainer drove an entrained oscillator the judge did not run, so two of eight trained numbers
were dead at judgment and the variant was never tested at all. Measure it, then repair it, then
compare -- in that order, and publish the size of the disagreement (rule 17).

    python tools/walk_roll_probe.py [--theta walk_theta_entrained.npy] [--seeds 3 4 5 6 7 8 9]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body                                              # noqa: E402
from stand_port import derive_stand_port, MYOBODY                        # noqa: E402
from train_stand import joint_ids, seat_in_limits, NUDGE                 # noqa: E402
from walk_port import (derive_walk_port, muscle_groups, walk_formula,    # noqa: E402
                       WalkOscillator)
from train_walk import foot_contact, CTRL_EVERY                          # noqa: E402
from chimera_gait import _periodicity                                    # noqa: E402

OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"
LOGDIR = ROOT / "agent_logs"
SECS = 6.0                       # f4_walk's own judging window
HELD_OUT = (3, 4, 5, 6, 7, 8, 9)


def run(m, d, mujoco, P, ts, tw, groups, tgt, nu, seed, feed_roll, entrained):
    """One life, driving `walk_formula` DIRECTLY -- the same function f4 reaches through the
    parser and train_walk reaches inline. `feed_roll` is the single variable."""
    jids = joint_ids(m, mujoco)
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    seat_in_limits(m, d, mujoco, jids)
    if seed:
        d.qpos[:] = d.qpos + np.random.default_rng(seed).normal(0.0, NUDGE, size=d.qpos.shape)
        mujoco.mj_forward(m, d)
    osc = WalkOscillator(P["OUT omega_rad_s"],
                         eps=float(tw[6]) if tw.size > 6 else 2.0,
                         kappa=float(tw[7]) if tw.size > 7 else 4.0) if entrained else None
    ctrl_dt = CTRL_EVERY * m.opt.timestep
    steps = int(SECS / m.opt.timestep)
    x0, sup, xs, zs, held = float(d.qpos[0]), [], [], [], SECS
    for k in range(steps):
        if k % CTRL_EVERY == 0:
            z = float(d.qpos[2])
            q = d.qpos[3:7]
            pitch = float(np.arctan2(2 * (q[0] * q[2] - q[3] * q[1]),
                                     1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            roll = float(np.arctan2(2 * (q[0] * q[1] + q[2] * q[3]),
                                    1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            ph, gate = None, None
            if osc is not None:
                _cr, _cl = foot_contact(m, d, mujoco)
                ph = osc.step(ctrl_dt, _cr, _cl)
                gate = {s: osc.swing_allowed(s, _cr, _cl) for s in ("r", "l")}
            d.ctrl[:] = walk_formula(ts, tw, groups, z, pitch,
                                     P["OUT omega_rad_s"] * d.time, nu, tgt,
                                     phases=ph, swing_gate=gate,
                                     roll=(roll if feed_roll else 0.0))
        mujoco.mj_step(m, d)
        if k % CTRL_EVERY == 0:
            z = float(d.qpos[2])
            cr, cl = foot_contact(m, d, mujoco)
            sup.append((1.0 if cr > 0 else 0.0) + (1.0 if cl > 0 else 0.0))
            xs.append(float(d.qpos[0])); zs.append(z)
            if z < 0.5 * tgt:
                held = k * m.opt.timestep
                break
    dt_s = CTRL_EVERY * m.opt.timestep
    per, period = _periodicity(np.array(sup), dt_s) if len(sup) > 16 else (0.0, 0.0)
    el = max(held, 1e-9)
    return dict(speed=(xs[-1] - x0) / el if xs else 0.0, periodicity=float(per),
                period_s=float(period), held=float(held),
                z_min=float(min(zs)) if zs else 0.0)


def main() -> int:
    import mujoco
    a = sys.argv
    names = (a[a.index("--theta") + 1].split(",") if "--theta" in a
             else ["walk_theta_entrained.npy", "walk_theta_entrained2.npy", "walk_theta_mult.npy"])
    P = derive_walk_port()
    S = derive_stand_port()
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    groups = muscle_groups(m, d, mujoco)
    nu, tgt = m.nu, S["OUT pelvis_target_m"]
    ts = np.load(OUTDIR / "stand_theta.npy")

    print(f"\nDOES THE WALK JUDGE ZERO THE STAND POLICY'S ROLL BLOCK?")
    print("=" * 106)
    print(f"  f4_walk builds obs = {{z, pitch, t}}; move_formula_fn reads obs.get('roll', 0.0). "
          f"train_walk passes roll.")
    print(f"  ONE VARIABLE: roll fed / roll zeroed. Same theta, same seeds, same plant, same "
          f"oscillator path.")
    print(f"  stand theta FROZEN ({ts.size} numbers = {ts.size//nu} blocks x {nu}); the kr block "
          f"is {nu} of them.")
    print(f"  judged on HELD-OUT seeds {HELD_OUT} x {SECS:.0f} s -- medians.")
    print("-" * 106)
    print(f"  {'theta':28}{'roll':>7}{'speed m/s':>11}{'period''ty':>11}{'period s':>10}"
          f"{'held s':>9}{'pelvis min':>12}")
    rows = []
    for name in names:
        p = OUTDIR / name
        if not p.exists():
            print(f"  {name:28}  -- not on disk, skipped")
            continue
        tw = np.load(p)
        ent = tw.size > 6
        for feed in (False, True):
            rs = [run(m, d, mujoco, P, ts, tw, groups, tgt, nu, s, feed, ent) for s in HELD_OUT]
            med = {k: float(np.median([r[k] for r in rs])) for k in rs[0]}
            rows.append(dict(theta=name, feed_roll=feed, entrained=ent, **med))
            print(f"  {name if not feed else '':28}{'FED' if feed else 'ZERO':>7}"
                  f"{med['speed']:>11.4f}{med['periodicity']:>11.3f}{med['period_s']:>10.3f}"
                  f"{med['held']:>9.2f}{med['z_min']:>12.4f}")
    print("=" * 106)
    same = all(abs(rows[i]["speed"] - rows[i + 1]["speed"]) < 1e-12
               and abs(rows[i]["held"] - rows[i + 1]["held"]) < 1e-12
               for i in range(0, len(rows) - 1, 2))
    print(f"  FALSIFIER (the two judgments are identical -- kr contributes nothing here): "
          + ("FIRES -- there is no defect: the roll block does not reach the walk's control at "
             "all." if same else
             "does not fire. The judgments DIFFER, so f4_walk has been judging every walk arm "
             "with 290 of the\n    frozen stand policy's 1160 numbers multiplied by zero, while "
             "train_walk trained against them.\n    Same species as the walk port's 2026-08-03 "
             "LEDGER entry, in a new place."))
    LOGDIR.mkdir(parents=True, exist_ok=True)
    out = LOGDIR / "walk_roll_probe.json"
    out.write_text(json.dumps(dict(secs=SECS, held_out_seeds=list(HELD_OUT), g=g,
                                   stand_theta_numbers=int(ts.size), nu=int(nu),
                                   identical=bool(same), rows=rows), indent=1), encoding="utf8")
    print(f"  JSON: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
