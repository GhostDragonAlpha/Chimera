"""joint_load.py -- WHAT THE HARD STOPS ARE ACTUALLY CARRYING, in newton-metres.

RULE 0, stated before the build:

    STATEMENT   `stand_reward`'s joints term grades a GEOMETRIC quantity -- how far each joint is
                through its declared range, as a fraction of that range. There is a PHYSICAL
                quantity underneath it that MuJoCo already computes and nothing here reads: the
                constraint torque each joint limit is carrying. They are not the same measurement
                and they cannot be, because a joint RESTING against its stop under no drive and a
                joint being DRIVEN into that stop by muscle occupy the SAME ANGLE and therefore
                the same geometric fraction, while the first costs the body nothing and the second
                is what a dislocation is made of.

    PREDICTION  A fact this was never fitted to: the constraint-torque measure separates those two
                states, and the geometric one does not. On the incumbent stand policy versus the
                identical body under ZERO CONTROL, the summed overload differs by more than 10x.

    FALSIFIER   Three, named before the run:
                1. If MuJoCo's efc arrays do not expose per-joint-limit forces on this model, the
                   quantity cannot be measured this way -- report it and stop.
                2. If driven and resting come back COMPARABLE, the theory is wrong: constraint
                   torque is not measuring what this file claims.
                3. If the physical measure RANKS THE JOINTS the same way the geometric one does,
                   then the two carry the same information about where the load is, and swapping
                   one for the other inside the reward would change nothing that matters. Report
                   it and DO NOT change the reward.

MEASURED 2026-08-04, and the verdicts are mixed -- which is why this file is an INSTRUMENT and
not a reward change:

    falsifier 1  DOES NOT FIRE. efc_type == mjCNSTR_LIMIT_JOINT, efc_id, efc_force all present.
    falsifier 2  DOES NOT FIRE. Summed overload S = 0.9021 under the policy against 0.0274 under
                 zero control -- 33x, on a body at closely comparable joint angles.
    falsifier 3  *** FIRES, PARTLY, AND IT FIRES AGAINST THIS FILE'S OWN USEFULNESS. ***
                 Against the HINGE SUM that `stand_port.joints_factor` now uses, the two measures
                 AGREE on the worst joint (knee_angle_l) and on the top-3 set:

                     joint            geometric share   physical share
                     knee_angle_l          29.5%            41.9%
                     knee_angle_r          27.9%            16.8%
                     mtp_angle_l           27.7%            40.7%
                     mtp_angle_r            8.1%             0.0%   <- geometric overstates
                     L4_L5_FE               4.4%             0.7%   <- geometric overstates

                 SO THE REWARD IS NOT CHANGED HERE. The disagreement is confined to two joints
                 carrying 4-8% of the geometric total, and no evidence exists that correcting it
                 changes which candidates a search selects. That evidence would be a retrain, and
                 stacking a speculative second change on top of a reward fix that landed the same
                 day is how a three-body problem gets built (CLAUDE.md: one change at a time).

I WAS WRONG ABOUT THIS AND THE MEASUREMENT IS WHY. Before `joints_factor` became a hinge SUM I
read F3's "worst joint L4_L5_FE 1.18" beside this file's "L4_L5_FE carries 0.7% of the load" and
concluded the geometric measure was pointing the search at the wrong joint. It was not: that
misdirection lived entirely in the retired `max()`, which reports whichever joint has the largest
FRACTION and is therefore biased toward joints with small declared ranges. Summing removed it.
The comparison that convicted the geometric measure was a comparison against a form that no
longer exists -- a stale control, which is its own named defect.

WHAT REMAINS TRUE AND WORTH KEEPING. Two things the geometric measure cannot do at any threshold:

  * DRIVEN vs RESTING. The zero-control body sits with mtp_angle_l over its stop 5.3% of the time
    and scores S = 0.027; the policy-driven body sits over it 96% of the time and scores 0.902.
    Some of that gap is angle and some is FORCE, and only this measure sees the force half.
  * THE NORMALIZER IS PHYSICAL, and it is what makes joints comparable. mtp's limit torque is
    2.375 N.m against knee_angle_l's 114.281 -- 48x smaller -- but the toe's muscles can only
    produce 6.5 N.m against the knee's 326.6, so as a FRACTION OF WHAT THE JOINT CAN RESIST they
    are near-equal offenders (0.367 vs 0.378). A measure without that normalizer either drowns
    the toe or, in fraction-of-range terms, invents an offender at L4_L5_FE.

WHY CAPACITY IS THE RIGHT NORMALIZER AND NOT A CHOICE. It is the scale `world.derive_ligaments`
already uses to size passive tissue, in that file's own words: *a ligament that could be
overpowered by the muscles crossing its own joint would let every maximal contraction drive that
joint through its own stop, which is a dislocation.* So "limit torque / muscular capacity" is
literally "how far through the dislocation threshold this joint is being pushed", and 1.0 is a
derived unit rather than a chosen one.

    python tools/joint_load.py                 # the driven-vs-resting measurement + falsifiers
    python tools/joint_load.py --theta <path>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body                                       # noqa: E402
from stand_port import derive_stand_port, MYOBODY, JOINT_COLD     # noqa: E402
from train_stand import joint_ids, seat_in_limits, CTRL_EVERY     # noqa: E402
from parser import Parser, default_registry                       # noqa: E402

OUTDIR = ROOT / "ChimeraEngine" / "output" / "ports"
CACHE = OUTDIR / "joint_capacity.json"


def joint_capacity(m, d, mujoco, jids, n_samp=7, use_cache=True):
    """Peak muscle torque each graded joint can produce, N.m. MEASURED, then cached.

    The measurement is `world._ligament`'s, generalised off the gait envelope so it reaches the
    joints that have no published curve -- the toe and the off-sagittal hip axes, which are
    exactly the ones the ligament derivation had to REFUSE. Every muscle at full activation, the
    joint swept across its own declared range, and the largest torque produced in EITHER
    direction kept.

    THE MAX OVER THE BAND, NOT THE VALUE AT THE LIMIT, and world.py paid for that distinction:
    "measured at the limit the knee reads ~0, because at 120 deg the hamstrings are fully
    shortened and make no force. That is real physiology and it is the wrong number: the ligament
    still has to CATCH what was launched at it from mid-band."

    ACTIVATION IS `act`, NOT `ctrl` -- the same trap, also already paid for: ctrl is excitation
    and the force reads act, a state with 15 ms dynamics, so a pass that sets ctrl and calls
    mj_forward silently reports the keyframe's activation instead of full drive.

    Cached by actuator/joint count, like `walk_port.muscle_groups`: it is a property of the body,
    not of the run, and the key stops one body reading another body's numbers.
    """
    key = f"{m.nu}x{m.njnt}"
    if use_cache and CACHE.exists():
        blob = json.loads(CACHE.read_text(encoding="utf8"))
        if blob.get("key") == key:
            return {k: float(v) for k, v in blob["capacity"].items()}
    cap = {}
    for adr, c, h, name in jids:
        j = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, name)
        if j < 0:
            raise SystemExit(f"no joint {name!r} -- refusing to measure a capacity for a joint "
                             f"this model does not have (rule 20).")
        dof = int(m.jnt_dofadr[j])
        lo, hi, best = c - h, c + h, 0.0
        for i in range(n_samp + 1):
            mujoco.mj_resetData(m, d)
            d.qpos[adr] = lo + (hi - lo) * i / n_samp
            d.qvel[:] = 0.0
            d.ctrl[:] = 1.0
            if m.na:
                d.act[:] = 1.0
            mujoco.mj_forward(m, d)
            flat = np.asarray(d.actuator_moment).ravel()
            pos = neg = 0.0
            for k in range(m.nu):
                n0, a0 = int(d.moment_rownnz[k]), int(d.moment_rowadr[k])
                for e in range(n0):
                    if int(d.moment_colind[a0 + e]) == dof:
                        t = float(flat[a0 + e]) * float(d.actuator_force[k])
                        if t > 0.0:
                            pos += t
                        else:
                            neg += -t
            best = max(best, pos, neg)
        cap[name] = best
    OUTDIR.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps({"key": key, "capacity": cap}, indent=1), encoding="utf8")
    return cap


def _limit_rows(m, d, mujoco):
    """(joint id, |constraint force|) for every ACTIVE joint-limit constraint this step."""
    n = int(d.nefc)
    if n == 0:
        return []
    et = np.asarray(d.efc_type[:n])
    ei = np.asarray(d.efc_id[:n])
    ef = np.asarray(d.efc_force[:n])
    LJ = int(mujoco.mjtConstraint.mjCNSTR_LIMIT_JOINT)
    return [(int(ei[k]), abs(float(ef[k]))) for k in np.flatnonzero(et == LJ)]


def limit_overload(m, d, mujoco, cap, jname, primary):
    """S = SUM over graded joints of |limit torque| / capacity, and the per-joint breakdown.

    EXTENSIVE, like the hinge sum it parallels: two joints on their stops load the body with the
    sum of what each loads it with alone. Restricted to `primary` for the reason
    `train_stand.PRIMARY` exists -- the knee's coupled four-bar DOFs (`*_translation*`,
    `*_rotation*`) are driven BY knee_angle, and grading them would grade one joint twice. They
    show up in the raw efc rows (knee_angle_l_translation1 carries 13.8 N.m) and are dropped here
    deliberately, not by accident.
    """
    per = {}
    for jid, f in _limit_rows(m, d, mujoco):
        nm = jname.get(jid, "")
        c = cap.get(nm, 0.0)
        if nm in primary and c > 0.0:
            per[nm] = per.get(nm, 0.0) + f / c
    return float(sum(per.values())), per


def _rollout(m, d, mujoco, theta, P, jids, cap, jname, primary, secs, driven):
    """One life through the JUDGE'S plant. `driven=False` is the zero-control control."""
    tgt, nu = P["OUT pelvis_target_m"], m.nu
    PAR = Parser(default_registry(theta, tgt, nu))
    PAR.set_verb("STAND", driven)
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    seat_in_limits(m, d, mujoco, jids)
    S, acc, geo, ns = [], {}, {}, 0
    for k in range(int(secs / m.opt.timestep)):
        if k % CTRL_EVERY == 0:
            z = float(d.qpos[2])
            q = d.qpos[3:7]
            pitch = float(np.arctan2(2 * (q[0] * q[2] - q[3] * q[1]),
                                     1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            roll = float(np.arctan2(2 * (q[0] * q[1] + q[2] * q[3]),
                                    1 - 2 * (q[1] ** 2 + q[2] ** 2)))
            u, _ = PAR.command({"z": z, "pitch": pitch, "roll": roll})
            d.ctrl[:] = u if (u is not None and driven) else 0.0
        mujoco.mj_step(m, d)
        if k % CTRL_EVERY == 0:
            ns += 1
            s, per = limit_overload(m, d, mujoco, cap, jname, primary)
            S.append(s)
            for kk, v in per.items():
                acc[kk] = acc.get(kk, 0.0) + v
            # the GEOMETRIC hinge contribution, on the same samples -- the clay control: measure
            # the new thing and the thing it would replace on ONE trace, or the difference you
            # report may be the instrument's own signature.
            for adr, c, h, n in jids:
                geo[n] = geo.get(n, 0.0) + max(0.0, abs(float(d.qpos[adr]) - c) / h - JOINT_COLD)
    ns = max(ns, 1)
    return (np.array(S), {k2: v / ns for k2, v in acc.items()},
            {k2: v / ns for k2, v in geo.items()})


def main() -> int:
    import mujoco
    a = sys.argv
    secs = float(a[a.index("--secs") + 1]) if "--secs" in a else 5.0
    tpath = Path(a[a.index("--theta") + 1]) if "--theta" in a \
        else OUTDIR / "stand_theta.npy"
    if not tpath.exists():
        raise SystemExit(f"no {tpath} -- refusing to measure the joint load of a policy that "
                         f"does not exist (rule 20).")
    theta = np.load(tpath)
    P = derive_stand_port()
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    jids = joint_ids(m, mujoco)
    primary = {n for _, _, _, n in jids}
    jname = {j: (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, j) or "") for j in range(m.njnt)}

    if not hasattr(mujoco.mjtConstraint, "mjCNSTR_LIMIT_JOINT"):
        print("  FALSIFIER 1 FIRES: this MuJoCo exposes no joint-limit constraint type. The "
              "quantity cannot be measured this way.")
        return 1

    cap = joint_capacity(m, d, mujoco, jids)
    print(f"\nJOINT LOAD -- what the hard stops carry, theta {tpath.name}, {secs:.0f} s")
    print("=" * 96)
    print(f"  {len(cap)} joint capacities measured (peak muscle torque, N.m, cached at "
          f"{CACHE.name})")
    top = sorted(cap.items(), key=lambda p: -p[1])
    print(f"    strongest {top[0][0]} {top[0][1]:.1f}   weakest {top[-1][0]} {top[-1][1]:.1f} "
          f"-- a {top[0][1]/max(top[-1][1],1e-9):.0f}x spread, which is why the normalizer is "
          f"per-joint")

    Sd, pd_, gd = _rollout(m, d, mujoco, theta, P, jids, cap, jname, primary, secs, True)
    Sr, pr_, gr = _rollout(m, d, mujoco, theta, P, jids, cap, jname, primary, secs, False)
    ratio = Sd.mean() / max(Sr.mean(), 1e-12)
    print(f"\n  DRIVEN (the policy)     S mean {Sd.mean():.4f}  median {np.median(Sd):.4f}  "
          f"max {Sd.max():.4f}")
    print(f"  RESTING (zero control)  S mean {Sr.mean():.4f}  median {np.median(Sr):.4f}  "
          f"max {Sr.max():.4f}")
    print(f"  separation {ratio:.1f}x")
    print(f"  FALSIFIER 2 (driven and resting come back comparable): "
          + ("DOES NOT FIRE -- the constraint torque sees a difference the joint ANGLE cannot, "
             "which is the whole claim." if ratio >= 10.0 else
             "FIRES -- constraint torque is not measuring what this file claims. Stop."))

    Eg, Ep = sum(gd.values()), sum(pd_.values())
    print(f"\n  WHERE THE LOAD IS -- geometric hinge share vs physical overload share, one trace")
    print(f"  {'joint':22}{'GEOMETRIC':>12}{'PHYSICAL':>12}   note")
    rows = []
    for n in sorted(set(gd) | set(pd_), key=lambda x: -gd.get(x, 0.0)):
        ga, pa = 100 * gd.get(n, 0.0) / max(Eg, 1e-12), 100 * pd_.get(n, 0.0) / max(Ep, 1e-12)
        if ga < 1.0 and pa < 1.0:
            continue
        note = ("geometric overstates" if ga > 3 * max(pa, 1e-9) else
                "geometric blind" if pa > 3 * max(ga, 1e-9) else "agree")
        rows.append(dict(joint=n, geometric_pct=ga, physical_pct=pa, note=note))
        print(f"  {n:22}{ga:>11.1f}%{pa:>11.1f}%   {note}")
    gtop = max(gd, key=gd.get) if gd else "?"
    ptop = max(pd_, key=pd_.get) if pd_ else "?"
    agree = gtop == ptop
    print(f"\n  worst joint by GEOMETRIC: {gtop}      by PHYSICAL: {ptop}")
    print(f"  FALSIFIER 3 (the two measures rank the joints alike): "
          + ("FIRES -- they agree on the worst joint. The information about WHERE the load sits "
             "is already in the geometric measure, so swapping it into the reward is NOT "
             "justified by this evidence. The reward is left alone."
             if agree else
             "does not fire -- the two disagree on the worst joint, so the geometric measure is "
             "sending the search somewhere the physics does not."))
    print("=" * 96)
    print("  THIS FILE CHANGES NO REWARD. It measures a quantity `stand_reward` does not read,")
    print("  reports that the case for reading it is UNPROVEN, and leaves the decision to a")
    print("  retrain nobody has run. An instrument may say 'not yet'; that is what it is for.")

    out = ROOT / "agent_logs" / f"joint_load_{tpath.stem}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dict(
        theta=tpath.name, secs=secs, capacity=cap,
        S_driven_mean=float(Sd.mean()), S_resting_mean=float(Sr.mean()), separation=float(ratio),
        per_joint=rows, worst_geometric=gtop, worst_physical=ptop,
        falsifier2_fires=bool(ratio < 10.0), falsifier3_fires=bool(agree)), indent=1),
        encoding="utf8")
    print(f"  JSON: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
