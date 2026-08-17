"""gravity_transfer.py -- IS IT A POLICY, OR DID IT MEMORISE ONE GRAVITY?

RULE 0, stated before the run:

    STATEMENT   The stand policy was trained at this world's g = 7.076 m/s^2 and nowhere else.
                Every derivation beneath it scales with g -- the fall rate, the capture point,
                `omega_0 = sqrt(g/H)` -- so a controller that learned the STRUCTURE of standing
                should still stand at Earth's 9.81, worse but not helplessly. One that memorised
                a single operating point should collapse.

    PREDICTION  Transfer ratio (held-out survival at Earth g / held-out survival at this world's
                g) > 0.5 for a policy, < 0.3 for a fit.

    FALSIFIER   All thetas transfer above 0.5 -- the policy class already generalises across
                gravity, and "it memorised the training condition" is not the explanation for
                anything.

IT DOES NOT REGROW THE STORY, and that is deliberate. `Chimera/core/grow.py` with a different `g` would
re-derive every membrane from theZero down -- the star, the planet, the terrain, theHuman's own
mass and leg length -- so the body, the target height and the base of support would ALL move
together and the experiment would no longer be about gravity. It would be about a different
world containing a different person, and the comparison would have no fixed quantity in it.

    `world.load_body` overrides the model's gravity from theHuman AFTER the body is built.
    Setting `m.opt.gravity[2]` directly is the SAME intervention, one number, everything else
    held -- and it touches no membrane and no other lane's shared state.

THE TARGET HEIGHT IS HELD AT THIS WORLD'S VALUE. It is a property of the BODY's geometry
(hip_to_ankle + ankle_height), not of gravity, so it does not move when g does. Naming that,
because a transfer test that also moved the target would be scoring the policy against a bar it
had never been given.

    python tools/gravity_transfer.py [--g 9.81] [--seeds 10]
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

OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"
LOGDIR = ROOT / "agent_logs"
TRAINED_SEEDS = (0, 1, 2)
THETAS = ("stand_theta", "stand_theta_derived", "stand_theta_guard")
# --arms TAKES `theta[:class]` PAIRS (2026-08-04, task 5). A policy class is not recoverable from
# a theta's length -- `pd` and `pd_windowed` are both 7 blocks and differ only in the derivative
# baseline -- so the class is DECLARED beside the file and never inferred (story/folding.py's
# rule, and the substitution that left parser_tests falsifier 1 dead for several commits).
# Absent, this file runs exactly as it did: the three named thetas through the inline formula.


def survive(m, d, mujoco, theta, P, jids, secs, seeds):
    tgt, nu = P["OUT pelvis_target_m"], m.nu
    out = []
    for s in seeds:
        PARSER = Parser(default_registry(theta, tgt, nu))
        PARSER.set_verb("STAND", True)
        mujoco.mj_resetDataKeyframe(m, d, 0)
        mujoco.mj_forward(m, d)
        seat_in_limits(m, d, mujoco, jids)
        if s:
            d.qpos[:] = d.qpos + np.random.default_rng(s).normal(0.0, NUDGE, size=d.qpos.shape)
            mujoco.mj_forward(m, d)
        steps, t_end = int(secs / m.opt.timestep), secs
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
            if k % CTRL_EVERY == 0 and float(d.qpos[2]) < 0.5 * tgt:
                t_end = k * m.opt.timestep
                break
        out.append(t_end)
    return float(np.median(out)), out


def main() -> int:
    import mujoco
    a = sys.argv
    g_new = float(a[a.index("--g") + 1]) if "--g" in a else 9.81
    nseeds = int(a[a.index("--seeds") + 1]) if "--seeds" in a else 10
    secs = float(a[a.index("--secs") + 1]) if "--secs" in a else 20.0
    P = derive_stand_port()
    m, g_home = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    jids = joint_ids(m, mujoco)
    held = [i for i in range(nseeds) if i not in TRAINED_SEEDS]

    print(f"\nGRAVITY TRANSFER -- trained at g = {g_home:.4f}, tested at g = {g_new:.4f} "
          f"({g_new/g_home:.2f}x)")
    print("=" * 100)
    print(f"  ONE NUMBER MOVES. The body, the target pelvis {P['OUT pelvis_target_m']:.4f} m "
          f"(geometry, not gravity), the base of")
    print(f"  support, the keyframe and the seat are all held. The story is NOT regrown -- that "
          f"would move theHuman's")
    print(f"  own mass and leg length too, and the comparison would have no fixed quantity in it.")
    print(f"  survival = median over HELD-OUT seeds {held} at {secs:.0f} s")
    print("-" * 100)
    # THE ARMS. `name` alone -> the inline formula (what this file has always run); `name:class`
    # -> `benchmark_policies.survive` with that class, which is the SAME judge the policy-class
    # benchmark ranks on. One judge, two shapes -- never two implementations of "how long did it
    # stand", because the difference between those would be indistinguishable from a difference
    # in transfer.
    arms = ([s.strip() for s in a[a.index("--arms") + 1].split(",") if s.strip()]
            if "--arms" in a else list(THETAS))
    import policy_classes as PC                                       # noqa: E402
    import benchmark_policies as BP                                   # noqa: E402
    print(f"  {'theta':26}{'class':>13}{'home g':>10}{'Earth g':>10}{'ratio':>9}   verdict")
    rows = []
    for spec in arms:
        name, _, cls_name = spec.partition(":")
        pc = PC.get(cls_name) if cls_name else None
        p = OUTDIR / f"{name}.npy"
        if not p.exists():
            print(f"  {name:26}  -- not on disk, skipped")
            continue
        th = np.load(p)
        if pc is not None:
            pc.decode_theta(th, m.nu)
        _sv = ((lambda: BP.survive(mujoco, m, d, jids, P, pc, th, secs, held))
               if pc is not None else
               (lambda: survive(m, d, mujoco, th, P, jids, secs, held)))
        m.opt.gravity[2] = -abs(g_home)
        s_home, _ = _sv()
        m.opt.gravity[2] = -abs(g_new)
        s_new, per = _sv()
        m.opt.gravity[2] = -abs(g_home)          # restored, always
        ratio = s_new / max(s_home, 1e-9)
        verdict = ("GENERALISES (>0.5)" if ratio > 0.5 else
                   "partial" if ratio >= 0.3 else "OVERFIT (<0.3)")
        rows.append(dict(theta=name, policy_class=cls_name or "p_only (inline)",
                         home_s=s_home, new_s=s_new, ratio=ratio,
                         verdict=verdict, per_seed_new=per))
        print(f"  {name:26}{(cls_name or 'inline'):>13}{s_home:>9.2f}s{s_new:>9.2f}s"
              f"{ratio:>9.2f}   {verdict}")
    print("=" * 100)
    if not rows:
        raise SystemExit("no theta on disk -- refusing to report a transfer nothing was measured "
                         "on (rule 20).")
    ratios = [r["ratio"] for r in rows]
    fires = all(r > 0.5 for r in ratios)
    print(f"  FALSIFIER (every theta transfers above 0.5): "
          + (f"FIRES -- min ratio {min(ratios):.2f}. The policy class already generalises across "
             f"gravity,\n    and 'it memorised the training condition' explains nothing."
             if fires else
             f"does not fire -- min ratio {min(ratios):.2f}, "
             f"{sum(1 for r in ratios if r < 0.3)}/{len(ratios)} below 0.3."))
    # THE CONTROL THAT SAYS THE TEST DID ANYTHING: home-g survival must reproduce the judge's
    # own numbers, or the harness has moved something it did not mean to.
    # THE CONTROL IS THE INCUMBENT, NAMED -- not "whatever row came first". With `--arms` the
    # first row can be any policy, and comparing an arbitrary arm against the incumbent's
    # published 6.82 s would report a DISAGREEMENT that is only a mismatch of subjects.
    _ctl = next((r for r in rows if r["theta"] == "stand_theta"), None)
    if _ctl is None:
        print(f"  CONTROL: the incumbent (`stand_theta`) is not among the arms, so this run has "
              f"no anchor to\n           stand_survival's published 6.82 s. Include it to keep "
              f"one -- an unanchored ratio is a\n           number this harness cannot check "
              f"against another instrument.")
    else:
        print(f"  CONTROL: home-g survival here should reproduce stand_survival's held-out "
              f"medians (incumbent 6.82 s).")
        print(f"           measured {_ctl['home_s']:.2f} s for stand_theta -> "
              + ("agrees." if abs(_ctl["home_s"] - 6.82) < 0.05 else
                 "DISAGREES, so read the ratios with suspicion: this harness is not the judge's."))

    LOGDIR.mkdir(parents=True, exist_ok=True)
    out = LOGDIR / "gravity_transfer.json"
    out.write_text(json.dumps(dict(g_home=g_home, g_new=g_new, seeds=nseeds,
                                   held_out_seeds=held, secs=secs, rows=rows,
                                   falsifier_fires=bool(fires)), indent=1), encoding="utf8")
    print(f"  JSON: {out}")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.4))
    x = np.arange(len(rows))
    ax[0].bar(x - 0.2, [r["home_s"] for r in rows], 0.4, color="#2471a3",
              label=f"g = {g_home:.3f} (trained)")
    ax[0].bar(x + 0.2, [r["new_s"] for r in rows], 0.4, color="#c0392b",
              label=f"g = {g_new:.2f} (Earth)")
    ax[0].set_xticks(x); ax[0].set_xticklabels([r["theta"].replace("stand_theta", "θ")
                                                for r in rows], fontsize=8)
    ax[0].set_ylabel("held-out survival s"); ax[0].legend(fontsize=7)
    ax[0].set_title("does it still stand when gravity changes?", fontsize=9)
    ax[1].bar(x, ratios, color=["#1a7f37" if r > 0.5 else "#e67e22" if r >= 0.3 else "#c0392b"
                                for r in ratios])
    ax[1].axhline(0.5, color="#1a7f37", ls="--", lw=1.4, label="0.5 -- generalises")
    ax[1].axhline(0.3, color="#c0392b", ls="--", lw=1.4, label="0.3 -- overfit")
    ax[1].set_xticks(x); ax[1].set_xticklabels([r["theta"].replace("stand_theta", "θ")
                                                for r in rows], fontsize=8)
    ax[1].set_ylabel("transfer ratio"); ax[1].legend(fontsize=7)
    ax[1].set_title("policy or fit?", fontsize=9)
    fig.suptitle(f"GRAVITY TRANSFER {g_home:.3f} -> {g_new:.2f} m/s2 -- min ratio "
                 f"{min(ratios):.2f}", fontsize=11.5)
    png = OUTDIR / "gravity_transfer.png"
    fig.savefig(png, dpi=104, bbox_inches="tight"); plt.close(fig)
    print(f"  PICTURE: {png}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
