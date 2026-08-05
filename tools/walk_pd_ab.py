"""walk_pd_ab.py -- DOES THE STAND SUBSTRATE BECOMING A PARAMETER CHANGE ANY EXISTING ARM?

RULE 0, stated before the run:

    STATEMENT   `walk_port.walk_formula` gained a `stand_class` / `chan` path so that task 7 can
                compose a walk over a PD stand policy instead of a P-only one. Its inline path is
                unedited, and `policy_classes.get("p_only")` is the incumbent's own form -- the
                same slices, the same order, over the same theta. So the two paths must produce
                the SAME control vector for every state, to the last bit.

    PREDICTION  Over a sweep of states spanning the rollout's real range, max |u_inline - u_class|
                = 0.0 exactly, and a full 6 s rollout under each gives an identical trace.

    FALSIFIER   Any difference at all. Then the class path is a REIMPLEMENTATION of the walk's
                substrate rather than the substrate, every arm judged through it is being compared
                against something no previous arm ran, and task 7's A/B has two variables in it.

WHY THIS FILE EXISTS AT ALL. The walk port's own LEDGER (2026-08-03) records the cost of a
trainer and a judge running different plants: two of eight trained numbers were dead at judgment
and the entrained variant was never tested. `tools/walk_roll_probe.py` then found the same species
a second time on 2026-08-04 -- f4_walk built its obs without `roll`, so 290 of the frozen stand
policy's 1160 numbers were multiplied by zero at judgment while train_walk trained against them
(travel 0.3495 -> 0.4603 m/s, +32%). A third instance would not be bad luck. The identity is
MEASURED before the parameter is used, not asserted in a docstring.

    python tools/walk_pd_ab.py --selftest
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import policy_classes as PC                                              # noqa: E402
from world import load_body                                              # noqa: E402
from stand_port import derive_stand_port, MYOBODY                        # noqa: E402
from train_stand import joint_ids, seat_in_limits, NUDGE, CTRL_EVERY     # noqa: E402
from walk_port import derive_walk_port, muscle_groups, walk_formula      # noqa: E402
from train_walk import evaluate as walk_evaluate                         # noqa: E402

OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"
LOGDIR = ROOT / "agent_logs"


def main() -> int:
    import mujoco
    S, P = derive_stand_port(), derive_walk_port()
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    groups = muscle_groups(m, d, mujoco)
    nu, tgt = m.nu, S["OUT pelvis_target_m"]
    ts = np.load(OUTDIR / "stand_theta.npy")
    tw = np.load(OUTDIR / "walk_theta_entrained.npy")
    p_only = PC.get("p_only")
    w0 = PC.omega0(S)

    print("\nWALK SUBSTRATE PARAMETER -- SELFTEST")
    print("=" * 100)
    print(f"  stand theta {ts.size} numbers = {ts.size//nu} x {nu}; walk theta {tw.size}; "
          f"omega_0 {w0:.4f} rad/s")
    ok = True

    # ── 1. THE FORMULA, over a state sweep that spans the rollout's real range ───────────────
    # The states are a GRID, not samples of one trajectory: a trajectory visits a correlated
    # sliver of the space and an identity that holds only there is not an identity.
    print("  1. walk_formula(inline) == walk_formula(stand_class=p_only) over a 5x5x5 state grid")
    worst, n = 0.0, 0
    rng = np.random.default_rng(0)
    for z in np.linspace(0.40, 1.05, 5):
        for pitch in np.linspace(-0.35, 0.35, 5):
            for roll in np.linspace(-0.30, 0.30, 5):
                phase = float(rng.uniform(0.0, 2 * np.pi))
                a = walk_formula(ts, tw, groups, z, pitch, phase, nu, tgt, roll=roll)
                chan = {"z_err": tgt - z, "pitch": pitch, "roll": roll}
                b = walk_formula(ts, tw, groups, z, pitch, phase, nu, tgt, roll=roll,
                                 stand_class=p_only, chan=chan)
                worst = max(worst, float(np.max(np.abs(a - b))))
                n += 1
    ok &= worst == 0.0
    print(f"     {n} states, max |u_inline - u_class| = {worst:.3e}   "
          + ("identical." if worst == 0.0 else "DIFFER  <- FALSIFIER FIRES"))

    # ── 2. A FULL ROLLOUT through the trainer's own evaluate, both ways ───────────────────────
    print("  2. train_walk.evaluate, 6 s x 3 seeds, inline vs stand_class=p_only")
    for seed in (0, 1, 2):
        a = walk_evaluate(m, d, mujoco, ts, tw, groups, P, 6.0, entrained=True, seed=seed)[0]
        b = walk_evaluate(m, d, mujoco, ts, tw, groups, P, 6.0, entrained=True, seed=seed,
                          stand_class=p_only)[0]
        same = a == b
        ok &= same
        print(f"     seed {seed}: inline {a:.12f}   class {b:.12f}   "
              + ("identical." if same else f"DIFFER by {abs(a-b):.3e}  <- FALSIFIER FIRES"))

    # ── 3. AND THE PD SUBSTRATE MUST NOT BE THE SAME, or the parameter does nothing ──────────
    # A selftest that only proves "nothing changed" cannot tell a correct passthrough from a
    # parameter that is being ignored. This is the positive control: with the rate channels at
    # ZERO gain a PD theta is p_only exactly (identical), and with them nonzero it must differ.
    print("  3. POSITIVE CONTROL: a pd substrate must be identical at zero rate gain and "
          "DIFFERENT once the gains are not zero")
    pd = PC.get("pd")
    pd_zero = pd.build_theta(nu, ts, p_only)
    a = walk_evaluate(m, d, mujoco, ts, tw, groups, P, 6.0, entrained=True, seed=0)[0]
    b = walk_evaluate(m, d, mujoco, pd_zero, tw, groups, P, 6.0, entrained=True, seed=0,
                      stand_class=pd)[0]
    same0 = a == b
    ok &= same0
    print(f"     pd @ zero rate gain: inline {a:.12f}   pd {b:.12f}   "
          + ("identical -- the warm start is one point." if same0 else
             f"DIFFER by {abs(a-b):.3e}  <- FALSIFIER FIRES"))
    pd_live = pd_zero.copy()
    blk = pd.blocks(pd_live, nu)
    # a deliberately small, deliberately nonzero rate gain: this is a CONTROL, not a candidate
    for cname in ("zdot", "pitch_rate", "roll_rate"):
        i = pd.channels.index(cname)
        pd_live[nu + i * nu: nu + (i + 1) * nu] = 0.05
    c = walk_evaluate(m, d, mujoco, pd_live, tw, groups, P, 6.0, entrained=True, seed=0,
                      stand_class=pd)[0]
    diff = c != b
    ok &= diff
    print(f"     pd @ rate gain 0.05: {c:.12f} vs {b:.12f}   "
          + ("DIFFERENT -- the rate channels reach the muscles." if diff else
             "IDENTICAL  <- the substrate parameter is being IGNORED. FALSIFIER FIRES."))

    print("=" * 100)
    print("  SELFTEST " + ("PASS -- the class path IS the walk's substrate, and the PD channels "
                           "are live." if ok else
                           "FAIL. Task 7's A/B would have two variables in it; do not run it."))
    LOGDIR.mkdir(parents=True, exist_ok=True)
    (LOGDIR / "walk_pd_ab_selftest.json").write_text(json.dumps(dict(
        grid_states=n, max_abs_diff=worst, pass_=bool(ok)), indent=1), encoding="utf8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
