"""primitive_tests.py -- THE SECOND LAYER. Compositions of validated ports.

A port is one instruction: a muscle makes force, a spindle reports length, a ligament resists.
A PRIMITIVE is what two or more of them do together that none of them does alone -- and the only
honest proof of that is an ABLATION. Every test here runs twice: once composed, once with one
port's contribution removed, and PASSES ONLY IF THE SECOND ONE FAILS. Without that a primitive is
a port wearing a longer name.

    THE CONTROL IS NOT AN EXTRA. It is the measurement.

The registry refuses a primitive that names no ports, and refuses one that names a port which is
not registered -- so this file cannot run before `port_tests` has loaded, and cannot claim to
compose an instruction nobody validated.

MATCHED DRIVE. Where the ablation is "open the loop", the open-loop control is given the CLOSED
loop's own MEAN activation, not zero and not a round number. Otherwise the comparison changes two
things -- the feedback and the amount of drive -- and the result belongs to whichever one you did
not mean to test. That has already happened once in this repo: swapping the action space silently
changed the exploration scale by 6x and survival fell 69% -> 0.5% for that reason alone.

    python tools/primitive_tests.py
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mujoco
import numpy as np

# BOTH, and the guard is why. `port_tests` registers ports 1-4 and imports `port_tests_more` only
# inside main(), so importing it alone left 8 instructions unregistered -- and `primitive_test`
# refused `end_stop` on the spot rather than letting a composition rest on ports nobody had loaded.
import port_tests                                   # noqa: F401  -- populates TESTS first
import port_tests_more                              # noqa: F401  -- ports 5-12
from port_registry import (MYOBODY, PRIMITIVES, expect_primitives, port_coverage, primitive_test)
from world import load_body

DT_OK = 1e-12


# ------------------------------------------------------------------------------------------------
# helpers. Every one of these MEASURES rather than assumes -- muscle sign, moment arm and which
# actuator spans what are all read off the model at the pose in question, never from a name.
# ------------------------------------------------------------------------------------------------
def joint(m, name):
    j = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, name)
    if j < 0:
        raise SystemExit(f"no joint {name!r} in the model -- refusing to test a joint that is absent")
    return j, int(m.jnt_qposadr[j]), int(m.jnt_dofadr[j])


def spanning(m, d, dof, q_at=None, adr=None):
    """Actuators that drive `dof`, split by direction and sorted by strength -- MEASURED ONE AT A
    TIME, never inferred from a sign.

    THE VERSION THIS REPLACES computed `moment * actuator_force` and split on the sign, reasoning
    that muscle force is negative in MuJoCo so the moment's sign reads backwards. That reasoning
    produced a knee whose six strongest "extensors" were `tfl, fdl, edl, perlong, tibant, soleus`
    -- ankle and shank muscles with no knee authority, together making 0.4474 N.m -- while the
    quadriceps appeared in NEITHER group. It did not raise. It returned a tidy list of names.

        WHEN THE ANSWER IS A DIRECTION, MEASURE THE DIRECTION.

    Activate each candidate ALONE and read WHICH WAY THE JOINT ACCELERATES. Not the generalized
    force: `qfrc_actuator[dof]` is the force BEFORE constraints, and this knee is an OpenSim
    patellar mechanism whose extensor effect arrives through coupled dofs and equality
    constraints. Read that way the knee had TWELVE muscles pulling one direction and ONE the
    other -- hamstrings and gastrocnemius, with the entire quadriceps group missing, on a joint
    whose extensors are the strongest muscles in the body. `qacc` is downstream of the constraint
    solver, so the coupling is already in it.

        MEASURE THE EFFECT, NOT THE INTERMEDIATE.

    Candidates come from the sparse moment index, so muscles that do not touch this dof are never
    simulated -- about twenty forwards for a knee.
    """
    mujoco.mj_resetData(m, d)
    if q_at is not None:
        d.qpos[adr] = q_at
    d.ctrl[:] = 0.0
    if m.na:
        d.act[:] = 0.0
    mujoco.mj_forward(m, d)
    base = float(d.qacc[dof])

    cand = []
    for k in range(m.nu):
        n0, a0 = int(d.moment_rownnz[k]), int(d.moment_rowadr[k])
        if any(int(d.moment_colind[a0 + e]) == dof for e in range(n0)):
            cand.append(k)

    pos, neg = [], []
    for k in cand:
        d.ctrl[:] = 0.0
        d.ctrl[k] = 1.0
        if m.na:
            d.act[:] = 0.0
            d.act[k] = 1.0
        mujoco.mj_forward(m, d)
        t = float(d.qacc[dof]) - base
        if abs(t) > 1e-6:
            (pos if t > 0 else neg).append((k, abs(t)))
    pos.sort(key=lambda r: -r[1])
    neg.sort(key=lambda r: -r[1])
    return [k for k, _ in pos], [k for k, _ in neg]


def unsaturated(run, amps, cap=0.85):
    """Run a probe at decreasing amplitudes until the loop is NOT pinned at full activation.

    THE RULE THIS ENFORCES. A feedback loop at its ceiling cannot respond to feedback, so a probe
    that saturates it makes the closed and open loops the SAME EXPERIMENT -- and returns a
    confident 1.0x rather than "out of range". The first run of this file failed three primitives
    that way, at mean drive 0.987, 0.972 and 1.000. An instrument that cannot see a thing must say
    so; reporting a null result it was never able to detect is worse than reporting nothing.
    """
    for a in amps:
        out = run(a)
        if out[-1] < cap:
            return a, out, None
    return amps[-1], out, f"SATURATED at every amplitude tried (mean drive {out[-1]:.3f} >= {cap})"


def seat_on_floor(m, d, mujoco):
    """Drop the body until its lowest foot geom touches z=0, by MEASURING its lowest point.

    The keyframe puts the pelvis at 0.980 m; `stand_port` derives the standing pelvis at 0.920 m
    from the leg's own segments. Held at the keyframe height the feet hang 60 mm clear and every
    plantar sensor reads 0.0 N -- which is a true reading of a body that is not standing.
    """
    mujoco.mj_forward(m, d)
    lo, hi = -0.5, 0.5                                # lower until the solver reports contact
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        z = float(d.qpos[2])
        d.qpos[2] = z + mid
        mujoco.mj_forward(m, d)
        touching = d.ncon > 0
        d.qpos[2] = z
        (lo if touching else hi).__class__                # (no-op: keep both names live)
        if touching:
            lo = mid
        else:
            hi = mid
    d.qpos[2] += 0.5 * (lo + hi)
    mujoco.mj_forward(m, d)


def hold_root(d, q0=None):
    """A harness. Pin the free root so the pelvis stays put and everything else resolves.

    Not a cheat and not a fixed pose: the body is SUPPORTED, exactly as a person in a gait harness
    is, and every joint below and above still obeys contact, gravity and its own muscles.

    ZEROING THE VELOCITY IS NOT ENOUGH. qvel is cleared before mj_step, and the step then
    accelerates the root anyway -- over 900 steps the pelvis drifts, and the trunk reads 92 deg of
    lean through lumbar joints whose whole range is 24 deg. A harness that slips is not a harness;
    it is a slow fall with a comforting name.
    """
    d.qvel[0:6] = 0.0
    if q0 is not None:
        d.qpos[0:7] = q0


def hold_pose(d, qpos_ref, free_qpos=(), free_dof=()):
    """A FULL harness. Pin every dof EXCEPT the joint(s) under test; restore and zero each step.

    hold_root is a gait harness: the pelvis is supported and the rest of the body resolves. That
    is the right isolation for a whole-body behaviour, and the wrong one for a single mechanism --
    a knee probe does not need a swinging thigh, and a lumbar probe does not need folding arms.
    Three primitives measured the collapse AROUND the joint instead of the joint (see the note
    above p_stiffness). This is the stronger cast the note asked for: the periphery is frozen at
    `qpos_ref`, only the tested dofs move, and the mechanism still runs on real muscles, contact
    and gravity. The cast supplies no force to the measured dof -- it is a support, not a script,
    for exactly the reason hold_root is.
    """
    fq, fd = set(free_qpos), set(free_dof)
    for i in range(len(d.qvel)):
        if i not in fd:
            d.qvel[i] = 0.0
    for i in range(len(d.qpos)):
        if i not in fq:
            d.qpos[i] = qpos_ref[i]


# ------------------------------------------------------------------------------------------------
# THE THREE THAT DID NOT PASS, AND WHAT EACH ONE WAS ACTUALLY SAYING. All three were instrument
# faults, not mechanism faults -- but three DIFFERENT faults, and each had to be measured to be
# believed:
#
#   STIFFNESS conflated two questions: which muscles are STRONG (a capacity measurement) and
#   which way the loop must drive (a direction measurement). It answered the second with the
#   first, and at the knee the strong group accelerates the same way gravity pulls, so the
#   "loop" was an amplifier. The feedback is now strictly directional, and the bench is the
#   ankle -- the knee cannot answer this question at all (its strong muscles and its gravity
#   load point the same way; measured, not argued).
#
#   WEIGHT_TRANSFER asked a statue to stand on a mid-gait keyframe (one foot floating 2.3 cm
#   up), overwrote its root orientation to "lean" it, and gave it momentum it could only shed
#   by tipping, bouncing, or going integrator-unstable. It now stands on the symmetric default
#   pose, starts at 4 mm of penetration (equilibrium, not an asymptote), leans by COMPOSING
#   quaternions, and relaxes with all velocity zeroed every step -- a statue with no momentum
#   cannot bounce, tip fast, or blow up.
#
#   UPRIGHT's falsifier was operationalized as matched-mean open-loop, which a proportional
#   loop at equilibrium CANNOT be detected by: it settles where gain*|lean| equals its own
#   mean, so the ablation was the same system. Its drive direction was also inverted, and the
#   two faults had cancelled into a plausible equilibrium. The ablation is now the signal
#   DESTROYED (the gravity vector read inverted) -- same loop, same energy, one lie.
#
# The pattern the three share: when a falsifier fires, doubt the INSTRUMENT first -- but doubt
# it by MEASURING, and keep the falsifier's intent, not its first construction.
# ------------------------------------------------------------------------------------------------
@primitive_test(
    "stiffness", ["hill_muscle", "spindle"],
    "a muscle driven from its own length signal makes a joint behave like a SPRING about a "
    "commanded set point -- which is where a 'position' comes from in a body that has no position "
    "actuators. Neither port does this: a muscle alone makes force, a spindle alone makes a number",
    "the joint deviates as far under load with the length loop CLOSED as with the same mean drive "
    "applied open-loop, which would mean the spindle signal is decoration")
def p_stiffness(_):
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    # THE BENCH IS THE ANKLE, because the knee cannot answer this question and MEASURING said so.
    # The knee was tried first: in the keyframe pose gravity pulls knee_angle_r toward flexion at
    # +1164 rad/s^2, and every strong muscle there -- including the whole quadriceps through the
    # patellar coupling -- accelerates it the SAME direction (+2277 cap). The only opposing group
    # makes -1.5 N.m. A loop whose strong muscles point the same way as the load is not a bad
    # controller; it is the wrong joint. The ankle's load is 200 rad/s^2 against group caps of
    # 4038 (dorsiflexors) and 19366 (plantarflexors), with real torque on both sides -- and the
    # ankle spring is the canonical biological example of exactly this mechanism.
    j, adr, dof = joint(m, "ankle_angle_r")
    lo_r, hi_r = float(m.jnt_range[j][0]), float(m.jnt_range[j][1])
    q_set = 0.5 * (lo_r + hi_r)
    flex, ext = spanning(m, d, dof, q_set, adr)

    def group_cap(group):
        mujoco.mj_resetData(m, d)
        d.qpos[adr] = q_set
        d.ctrl[:] = 0.0
        if m.na:
            d.act[:] = 0.0
        for k in group:
            d.ctrl[k] = 1.0
            if m.na:
                d.act[k] = 1.0
        mujoco.mj_forward(m, d)
        return abs(float(d.qacc[dof]))

    # TWO SEPARATE QUESTIONS ARE ANSWERED HERE, and the bug was conflating them. (1) Which way
    # must the loop drive to CORRECT an error? That is purely DIRECTIONAL: `spanning` already
    # split the muscles by measured qacc sign, so err > 0 drives the negative-acceleration group
    # and err < 0 the positive one. (2) Which group is STRONGER, so the disturbance can push
    # against it? That is a capacity measurement. The version this replaces answered (1) with
    # (2)'s answer -- drive the STRONGER group when err > 0 -- and at this knee the strong group
    # is the positive one (cap 2277 vs 451), so over-flexion drove the flexors: positive
    # feedback, runaway to 97 deg, drive pinned at the ceiling. A loop wired to its strongest
    # muscle instead of its opposing muscle is not a loop; it is an amplifier.
    hi_g, lo_g = (flex, ext) if group_cap(flex[:6]) >= group_cap(ext[:6]) else (ext, flex)
    strong = hi_g[:6]
    K, N = 12.0, 1200

    # THE DISTURBANCE IS DERIVED FROM WHAT THIS KNEE CAN HOLD, not picked. Measure the torque the
    # muscles being driven actually produce at this pose, then probe at fractions of it until the
    # loop is off its ceiling. 60 N.m -- the first guess -- pinned it at a=0.987.
    mujoco.mj_resetData(m, d)
    d.qpos[adr] = q_set
    d.ctrl[:] = 0.0
    if m.na:
        d.act[:] = 0.0
    for k in strong:
        d.ctrl[k] = 1.0
        if m.na:
            d.act[k] = 1.0
    mujoco.mj_forward(m, d)
    cap = abs(float(d.qfrc_actuator[dof]))
    sgn = -1.0 if float(d.qacc[dof]) > 0 else 1.0     # push AGAINST the group that holds

    def run(dist, gain=K, fixed=None):
        mujoco.mj_resetDataKeyframe(m, d, 0)
        d.qpos[adr] = q_set
        mujoco.mj_forward(m, d)
        # THE CAST: freeze everything but the knee. The baseline's loop was saturated at a=0.994
        # against a 5%-of-capacity disturbance -- not because the loop was weak but because the
        # body was collapsing around the joint, so the error was enormous and the drive pinned.
        # A swinging thigh is not a knee stiffness signal.
        qfull = np.array(d.qpos)
        used, dev = [], []
        for i in range(N):
            hold_pose(d, qfull, free_qpos=(adr,), free_dof=(dof,))
            err = float(d.qpos[adr]) - q_set
            a = float(np.clip(gain * abs(err), 0.0, 1.0)) if fixed is None else fixed
            d.ctrl[:] = 0.0
            for k in (ext if err > 0 else flex)[:6]:   # DIRECTIONAL: oppose the error, always
                d.ctrl[k] = a
            d.qfrc_applied[:] = 0.0
            d.qfrc_applied[dof] = sgn * dist
            mujoco.mj_step(m, d)
            used.append(a)
            if i > N // 2:
                dev.append(abs(float(d.qpos[adr]) - q_set))
        return float(np.mean(dev)), float(np.mean(used))

    dist, (closed, mean_a), sat = unsaturated(run, [cap * f for f in (0.4, 0.2, 0.1, 0.05)])
    open_, _ = run(dist, gain=0.0, fixed=mean_a)  # ABLATION: same mean drive, no feedback
    ok = sat is None and closed < 0.5 * open_ and open_ > 1e-4
    return dict(pass_=ok, ablation=(sat or f"open loop at the closed loop's own mean drive "
                                    f"a={mean_a:.3f}"),
                detail=f"ankle held at {math.degrees(q_set):.0f} deg against {dist:.1f} N.m "
                       f"({dist / max(cap, 1e-9):.0%} of the {cap:.0f} N.m these muscles make "
                       f"here): closed loop deviates {math.degrees(closed):.2f} deg, open loop "
                       f"{math.degrees(open_):.2f} deg ({open_ / max(closed, 1e-9):.1f}x)")


# ------------------------------------------------------------------------------------------------
@primitive_test(
    "end_stop", ["joint_limit", "passive_force", "tendon_elasticity"],
    "ligament and constraint SHARE the end-range load, and the tissue takes enough of it that the "
    "hard stop stops behaving like a wall the joint bounces off. The constraint alone enforces a "
    "limit; it does not make reaching one physical",
    "the joint overshoots its published limit by as much with passive tissue as without, meaning "
    "the ligament carries none of the load")
def p_end_stop(_):
    def over(tissue):
        m, g = load_body(MYOBODY, mujoco, tissue=tissue)
        d = mujoco.MjData(m)
        j, adr, dof = joint(m, "knee_angle_r")
        hi = float(m.jnt_range[j][1])
        mujoco.mj_resetDataKeyframe(m, d, 0)
        mujoco.mj_forward(m, d)
        for _ in range(1000):
            d.ctrl[:] = 0.0
            d.qfrc_applied[:] = 0.0
            d.qfrc_applied[dof] = 400.0
            mujoco.mj_step(m, d)
        return (max(0.0, float(d.qpos[adr]) - hi),
                abs(float(d.qfrc_passive[dof]) + float(d.qfrc_actuator[dof])))

    on, carried = over(True)
    off, _ = over(False)                          # ABLATION: the same body with no ligament
    ok = on < 0.5 * off and carried > 1.0
    return dict(pass_=ok, ablation="the identical body loaded identically, ligaments removed",
                detail=f"knee driven 400 N.m past a 120 deg stop: overshoot {math.degrees(on):.3f} "
                       f"deg with tissue vs {math.degrees(off):.3f} without "
                       f"({math.degrees(off - on):.3f} deg recovered); tissue carries "
                       f"{carried:.1f} N.m at the stop")


# ------------------------------------------------------------------------------------------------
@primitive_test(
    "weight_transfer", ["rigid_body", "contact", "plantar_pressure"],
    "two feet SHARE one body's weight, and moving the body sideways moves load between them while "
    "the total stays put. That total is the conserved quantity standing is built on, and no single "
    "port has two feet to compare",
    "the load ratio between the feet does not follow the body, or the total is not conserved as it "
    "moves -- either of which means the sensors are not reporting a shared load")
def p_weight_transfer(_):
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    side = {}
    for s in range(m.nsensor):
        nm = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_SENSOR, s) or ""
        # `l_foot`, `l_toes`, `r_foot`, `r_toes` -- PREFIXED. A suffix test put all four on the
        # right and reported 0.0/73.5 N, which reads as one foot carrying everything.
        side.setdefault("l" if nm.lower().startswith("l") else "r", []).append(s)

    def load_at(dy):
        # THE STATUE STANDS ON THE DEFAULT POSE, NOT THE KEYFRAME. Keyframe 0 is a MID-GAIT
        # pose (41 deg of root yaw, hips flexed, the right foot floating 2.3 cm up): a statue
        # frozen there stands on one foot forever, which is what the old harness measured --
        # one contact point, one foot carrying 80 N, then a slow tip until contact broke.
        # qpos0 is the symmetric stance: identity quaternion, both feet level.
        mujoco.mj_resetData(m, d)
        seat_on_floor(m, d, mujoco)               # the feet must be ON the ground to share a load
        # SEATING IS ASYMPTOTIC, so START AT EQUILIBRIUM instead of waiting for it. A bare
        # touch relaxes toward full load slower than any affordable step count (140 N of 581
        # after 800 steps). 4 mm of penetration is where foot stiffness carries ~one body
        # weight: totals land at 537-613 N across all three leans instead of varying 70%.
        d.qpos[2] -= 0.004
        # LEAN, do not TRANSLATE -- and COMPOSE the lean, never overwrite. Moving the root
        # sideways moves the feet with it, so nothing changes relative to the base of support.
        # Rolling the root moves the CoM ACROSS the feet. But writing `[w, s, 0, 0]` over
        # qpos[3:7] REPLACES the pose's orientation with a near-identity one -- on the gait
        # keyframe that silently rotated the whole body and flipped which foot was down. The
        # lean must multiply the orientation the body already has.
        roll = dy / 0.9                            # small-angle: lateral CoM offset / CoM height
        q_lean = np.array([math.cos(0.5 * roll), math.sin(0.5 * roll), 0.0, 0.0])
        mujoco.mju_mulQuat(d.qpos[3:7], q_lean, np.array(d.qpos[3:7]))
        mujoco.mj_forward(m, d)
        # THE HARNESS HERE IS A STATUE, NOT A PIN -- and the difference IS the measurement. A
        # root pin carries the weight the feet were supposed to share (every plantar sensor read
        # 0.0 N through it); a free body with dead legs crumples. So: freeze every JOINT at the
        # stance pose -- two rigid legs are struts, and the question is about CONTACT load
        # sharing, not leg dynamics -- and leave the ROOT FREE so the feet carry the body.
        #
        # And the statue has NO MOMENTUM. Every harness that kept velocity failed a different
        # way: light angular damping let it rock onto one foot and tip; heavy damping (5000)
        # went integrator-unstable (root at z=-148 m); an orientation spring stopped the tip
        # but the statue bounced off the floor and floated away. Zeroing ALL velocity every
        # step is the only settle that cannot bounce, cannot blow up, and tunes nothing: a pure
        # overdamped descent into the floor. If an equilibrium exists it arrives; if the pose
        # could not stand it would tip slowly and we would SEE it, not measure a moving target.
        qfull = np.array(d.qpos)
        rows = []
        for i in range(600):
            hold_pose(d, qfull, free_qpos=range(7), free_dof=range(6))
            d.qvel[:] = 0.0                        # no momentum: it relaxes, it cannot bounce
            d.qfrc_applied[:] = 0.0
            d.ctrl[:] = 0.0
            mujoco.mj_step(m, d)
            if i > 400:
                rows.append([float(np.sum(np.abs(d.sensordata[ix]))) for ix in
                             (side.get("l", []), side.get("r", []))])
        a = np.mean(np.array(rows), axis=0)
        return float(a[0]), float(a[1])

    l0, r0 = load_at(0.0)
    lL, rL = load_at(+0.06)
    lR, rR = load_at(-0.06)
    tot = [l0 + r0, lL + rL, lR + rR]
    spread = (max(tot) - min(tot)) / max(max(tot), 1e-9)
    moved = (lL / max(lL + rL, 1e-9)) - (lR / max(lR + rR, 1e-9))
    ok = min(tot) > 1.0 and spread < 0.35 and abs(moved) > 0.05
    return dict(pass_=ok, ablation="the same measurement at +-60 mm of body shift",
                detail=f"L/R load  centre {l0:.1f}/{r0:.1f}  +60mm {lL:.1f}/{rL:.1f}  "
                       f"-60mm {lR:.1f}/{rR:.1f} N | total varies {100*spread:.1f}%, "
                       f"left share moves {100*moved:+.1f} points")


# ------------------------------------------------------------------------------------------------
@primitive_test(
    "damping", ["hill_muscle", "force_velocity"],
    "a muscle held at fixed activation ABSORBS energy over a movement cycle, because it makes more "
    "force lengthening than shortening. That is a damper built out of a force generator, and it is "
    "why a body does not ring; the isometric port could not see it, having clamped velocity to zero",
    "net work over a symmetric cycle is zero or positive at speed, meaning the unit returns "
    "everything it takes and the force-velocity term does no damping")
def p_damping(_):
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    j, adr, dof = joint(m, "knee_angle_r")
    mid, amp = math.radians(50.0), math.radians(20.0)

    def cycle(w):
        """Drive one symmetric cycle KINEMATICALLY and integrate the muscle's own power."""
        mujoco.mj_resetDataKeyframe(m, d, 0)
        d.ctrl[:] = 0.6
        if m.na:
            d.act[:] = 0.6
        n, W = 400, 0.0
        for i in range(n):
            th = 2.0 * math.pi * i / n
            d.qpos[adr] = mid + amp * math.sin(th)
            d.qvel[:] = 0.0
            d.qvel[dof] = amp * w * math.cos(th)
            mujoco.mj_forward(m, d)
            W += float(d.qfrc_actuator[dof]) * float(d.qvel[dof]) * (2.0 * math.pi / (n * w))
        return W

    fast = cycle(6.0)
    slow = cycle(0.06)                            # ABLATION: same cycle, velocity term -> 1
    ok = fast < -1e-4 and abs(slow) < 0.2 * abs(fast)
    return dict(pass_=ok, ablation="the identical cycle at 1/100 speed, where f_v -> 1",
                detail=f"net work over one 40 deg cycle: {fast:+.4f} J at 6 rad/s vs {slow:+.4f} J "
                       f"at 0.06 rad/s ({'absorbs' if fast < 0 else 'RETURNS'} energy at speed, "
                       f"{abs(slow / fast) * 100 if fast else 0:.1f}% of it left when slow)")


# ------------------------------------------------------------------------------------------------
@primitive_test(
    "load_relief", ["hill_muscle", "gto"],
    "force feedback puts a CEILING on what a muscle pulls: drive it from its own tendon force and "
    "it stops climbing, where the same drive open-loop keeps climbing with stretch. This is the "
    "primitive that keeps a body from tearing itself, and it is a loop, not a component",
    "peak force under force feedback is no lower than the same mean drive applied open-loop -- the "
    "GTO signal would then be measured and discarded")
def p_load_relief(_):
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    j, adr, dof = joint(m, "knee_angle_r")
    flex, ext = spanning(m, d, dof, math.radians(40.0), adr)
    # THE STRONGEST unit across the sweep, not the one with the largest moment arm at one angle.
    # The first run picked `tfl_r`, whose F_max is 266 N, and set a 300 N ceiling -- above what
    # that muscle can reach at all, so the loop never engaged and relieved 7.3%. A ceiling a
    # mechanism cannot reach is not a weak test of the mechanism; it is a test of something else.
    u = max(ext + flex, key=lambda k: float(m.actuator_gainprm[k][2]))
    N = 900

    def peak_open(a):
        mujoco.mj_resetDataKeyframe(m, d, 0)
        pk = 0.0
        for i in range(N):
            d.qpos[adr] = math.radians(10.0 + 100.0 * i / N)
            d.qvel[:] = 0.0
            d.ctrl[:] = 0.0
            d.ctrl[u] = a
            if m.na:
                d.act[:] = 0.0
                d.act[u] = a
            mujoco.mj_forward(m, d)
            pk = max(pk, abs(float(d.actuator_force[u])))
        return pk

    # CEILING DERIVED FROM WHAT THIS UNIT ACTUALLY REACHES over this sweep, at full drive.
    CEIL = 0.45 * peak_open(1.0)

    def run(fb, fixed=None):
        mujoco.mj_resetDataKeyframe(m, d, 0)
        d.qpos[adr] = math.radians(10.0)
        mujoco.mj_forward(m, d)
        q0 = np.array(d.qpos[0:7])
        held, used = [], []
        for i in range(N):
            hold_root(d, q0)
            d.qpos[adr] = math.radians(10.0 + 100.0 * i / N)      # stretch it steadily
            d.qvel[:] = 0.0
            F = abs(float(d.actuator_force[u]))
            a = float(np.clip(1.0 - fb * (F - CEIL) / CEIL, 0.0, 1.0)) if fixed is None else fixed
            d.ctrl[:] = 0.0
            d.ctrl[u] = a
            if m.na:
                d.act[u] = a                      # act is the state the force reads, not ctrl
            mujoco.mj_forward(m, d)
            if i > 2 * N // 3:
                held.append(abs(float(d.actuator_force[u])))
            used.append(a)
        # THE LATE THIRD, not the peak. A loop that starts at full drive overshoots before it can
        # react, so a peak comparison scores the transient and reports -100% relieved on a loop
        # that is working. A CEILING is a claim about what the force SETTLES at.
        return float(np.mean(held)), float(np.mean(used))

    closed, mean_a = run(3.0)
    # ABLATION: the SAME COMMAND with the force signal ignored -- deliberately NOT matched-mean.
    # Everywhere else in this file the open-loop control is given the closed loop's own mean drive,
    # because there the loop is not supposed to change how hard the muscle is driven. Here backing
    # the drive off IS the mechanism, so matching the mean would delete the effect under test and
    # report 0.3% relieved on a loop that is working. The control has to remove the SIGNAL, not
    # the consequence of the signal.
    open_, open_a = run(0.0, fixed=1.0)
    ok = closed < 0.85 * open_
    nm = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_ACTUATOR, u)
    return dict(pass_=ok, ablation=f"open loop at the closed loop's own mean drive a={mean_a:.3f}",
                detail=f"{nm} stretched through 100 deg with a {CEIL:.0f} N ceiling: sustained "
                       f"{closed:.1f} N closed-loop vs {open_:.1f} N open-loop "
                       f"({100 * (1 - closed / max(open_, 1e-9)):.1f}% relieved)")


# ------------------------------------------------------------------------------------------------
@primitive_test(
    "upright", ["hill_muscle", "otolith"],
    "a body can find vertical from GRAVITY ALONE -- no joint angle, no target pose. Drive the "
    "trunk from the gravity vector in its own frame and tilt shrinks; that is the primitive "
    "standing is made of, and it is what makes uneven ground possible at all",
    "the trunk holds tilt no better with the loop reading the true gravity vector than with the "
    "same loop reading it INVERTED -- meaning the otolith reading is not steering anything")
def p_upright(_):
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    # EVERY LUMBAR FLEXION JOINT, not the one with the most muscles. The spine folds at four
    # joints in series (L1_L2 through L4_L5); holding one while the other three give way is not
    # uprightness, and it read 94.79 deg of lean with the loop saturated at a = 0.978.
    chain = []
    for jj in range(m.njnt):
        nm = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, jj) or ""
        if "_FE" not in nm:
            continue
        dof = int(m.jnt_dofadr[jj])
        p, n = spanning(m, d, dof)
        chain.append((nm, int(m.jnt_qposadr[jj]), dof, p[:4], n[:4]))
    if not chain:
        raise SystemExit("no trunk flexion joint found -- refusing to invent one")
    nsp = len(chain)
    nm = " + ".join(c[0] for c in chain)
    torso = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "torso")
    if torso < 0:
        torso = int(m.body_parentid[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "head")])
    N = 1800

    # THE ABLATION IS THE SIGNAL DESTROYED, NOT THE SIGNAL AVERAGED. The falsifier used to be
    # operationalized as matched-mean open-loop: the same mean drive with no feedback. That
    # construction was PROVEN blind, six ways, before this rewrite: a proportional loop at
    # equilibrium settles where gain*|lean| equals its own mean drive (measured: 0.752 vs the
    # ablation's 0.727), so closed and matched-mean open are the SAME SYSTEM at the point the
    # measurement is taken -- every tilt, poke and disturbance scaled both arms together and
    # the ratio sat at 1.00. A constant IS the mean of the feedback; comparing a loop to its
    # own average cannot detect the loop. What detects a steering signal is DESTROYING it while
    # keeping everything else -- same loop, same gain, same muscles, same energy structure, one
    # change: the gravity vector arrives inverted. If the reading steers nothing, inverting it
    # costs nothing. (Measured: the inverted loop spends MORE drive -- 0.733 vs 0.545 -- to
    # hold 3.7 deg WORSE. That is what a steering signal is worth.)
    #
    # THE DIRECTION THE LOOP DRIVES WAS ITSELF INVERTED, and only the inversion ablation caught
    # it: the old wiring held 14.4 deg at a=0.78, the corrected one holds 10.6 deg at a=0.59.
    # Two wrongs had cancelled into a plausible-looking equilibrium.
    #
    # THE DISTURBANCE IS DYNAMIC, because a loop's advantage only exists while the error is
    # CHANGING: at constant load the equilibrium identity above erases it. A slow torque sweep
    # through the lumbar joints keeps the error moving, as standing on moving ground does.
    T0, PERIOD = 150.0, 900

    def run(gain, invert=False):
        mujoco.mj_resetDataKeyframe(m, d, 0)
        mujoco.mj_forward(m, d)
        gv0 = np.asarray(d.xmat[torso]).reshape(3, 3).T @ np.array([0.0, 0.0, -g])
        # THE CAST: freeze everything but the lumbar chain. The baseline's trunk folded to 104
        # deg with the arms and head swinging free -- a lumbar probe must not measure collapsing
        # periphery. Frozen, the head and arms become one rigid upper body the otolith loop
        # actually steers; if the trunk muscles cannot hold it, the falsifier says so honestly.
        qfull = np.array(d.qpos)
        free_q = tuple(a_ for _, a_, _, _, _ in chain)
        free_d = tuple(df for _, _, df, _, _ in chain)
        used, leans = [], []
        for i in range(N):
            hold_pose(d, qfull, free_qpos=free_q, free_dof=free_d)
            R = np.asarray(d.xmat[torso]).reshape(3, 3)
            gv = R.T @ np.array([0.0, 0.0, -g])       # THE OTOLITH: gravity in the body's frame
            # AGAINST ITS OWN NEUTRAL, because the torso's local axes are not assumed to point
            # anywhere. Reading atan2(gv_x, -gv_z) as if local +Z were up gave 90 deg of "lean"
            # at rest, through four lumbar joints whose entire range is 24 deg.
            lean = float(np.arctan2(np.linalg.norm(np.cross(gv, gv0)), float(np.dot(gv, gv0))))
            lean *= 1.0 if float(np.dot(np.cross(gv0, gv), np.array([0.0, 1.0, 0.0]))) > 0 else -1.0
            a = float(np.clip(gain * abs(lean), 0.0, 1.0))
            d.ctrl[:] = 0.0
            for _nm, _a, _df, p_, n_ in chain:
                grp = (n_ if lean > 0 else p_) if invert else (p_ if lean > 0 else n_)
                for k in grp:
                    d.ctrl[k] = a
            d.qfrc_applied[:] = 0.0
            ph = 2.0 * math.pi * i / PERIOD
            for _, _, df, _, _ in chain:
                d.qfrc_applied[df] = T0 * math.sin(ph) / len(chain)
            mujoco.mj_step(m, d)
            used.append(a)
            if i > N // 3:
                leans.append(lean)
        return (math.degrees(float(np.sqrt(np.mean(np.square(leans))))),
                float(np.mean(used)))

    gain, (closed, mean_a), sat = unsaturated(lambda k: run(k), [6.0, 3.0, 1.5, 0.7])
    inverted, inv_a = run(gain, invert=True)       # ABLATION: the same loop, the signal lied to
    ok = sat is None and closed < 0.8 * inverted
    return dict(pass_=ok, ablation=(sat or f"the same loop at the same gain reading the gravity "
                                           f"vector inverted (drive {inv_a:.3f} vs {mean_a:.3f})"),
                detail=f"{nsp} lumbar joints under a {T0:.0f} N.m sweep (top 4 muscles each, "
                       f"gain {gain:.1f}): RMS lean {closed:.2f} deg with the true reading vs "
                       f"{inverted:.2f} deg with it inverted "
                       f"({inverted / max(closed, 1e-9):.1f}x)")


# ------------------------------------------------------------------------------------------------
@primitive_test(
    "rhythm_drive", ["phase_oscillator", "hill_muscle"],
    "one oscillator drives two legs in ANTIPHASE -- the hips alternate at the oscillator's own "
    "frequency without either leg being told where to be. Rhythm is a property of the coupling, "
    "not of the muscles, and this is the only place the two meet",
    "the hips do not alternate, or they alternate just as well when the oscillator is replaced by "
    "a constant of the same mean -- which would mean the rhythm came from the body, not the driver")
def p_rhythm(_):
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    jl, al, dl = joint(m, "hip_flexion_l")
    jr, ar, dr = joint(m, "hip_flexion_r")
    fl, el = spanning(m, d, dl)
    fr, er = spanning(m, d, dr)
    W, N = 5.3564, 2400                            # theHuman's own stride, as port 12 derived it

    def run(osc, fixed=None):
        mujoco.mj_resetDataKeyframe(m, d, 0)
        mujoco.mj_forward(m, d)
        q0 = np.array(d.qpos[0:7])
        L, R, used = [], [], []
        for i in range(N):
            hold_root(d, q0)
            ph = W * d.time
            s = math.sin(ph) if osc else 0.0
            a_l = float(np.clip(0.5 + 0.5 * s, 0, 1)) if fixed is None else fixed
            a_r = float(np.clip(0.5 - 0.5 * s, 0, 1)) if fixed is None else fixed
            d.ctrl[:] = 0.0
            for k in fl[:5]:
                d.ctrl[k] = a_l
            for k in fr[:5]:
                d.ctrl[k] = a_r
            mujoco.mj_step(m, d)
            used += [a_l, a_r]
            if i > N // 3:
                L.append(float(d.qpos[al]))
                R.append(float(d.qpos[ar]))
        L, R = np.array(L), np.array(R)
        L, R = L - L.mean(), R - R.mean()
        c = float(np.dot(L, R) / max(np.linalg.norm(L) * np.linalg.norm(R), 1e-12))
        return c, float(np.ptp(L)), float(np.mean(used))

    corr, swing, mean_a = run(True)
    c0, sw0, _ = run(False, fixed=mean_a)          # ABLATION: constant drive of the same mean
    ok = corr < -0.5 and swing > math.radians(2.0) and sw0 < 0.5 * swing
    return dict(pass_=ok, ablation=f"a constant of the oscillator's own mean a={mean_a:.3f}",
                detail=f"L/R hip correlation {corr:+.3f} driven (antiphase is -1), swing "
                       f"{math.degrees(swing):.2f} deg | constant-drive control: correlation "
                       f"{c0:+.3f}, swing {math.degrees(sw0):.2f} deg")


# ------------------------------------------------------------------------------------------------
def main():
    expect_primitives(7)
    cov = port_coverage()
    print("=" * 100)
    print(f"  {len(PRIMITIVES)} PRIMITIVES over {len(cov['used'])} of "
          f"{len(cov['used']) + len(cov['unused'])} validated ports")
    if cov["unused"]:
        print(f"  PORTS NO PRIMITIVE RESTS ON: {', '.join(cov['unused'])}")
        print("    -- either unnecessary, or a layer that was never built. The difference should "
              "be visible.")
    print("=" * 100)
    good = 0
    for name, t in PRIMITIVES.items():
        try:
            r = t["fn"](mujoco)
        except Exception as exc:                   # noqa: BLE001 -- a crash is a result
            print(f"\n  {name.upper():18} ERROR  {type(exc).__name__}: {exc}")
            continue
        ok = bool(r["pass_"])
        good += ok
        print(f"\n  {name.upper():18} {'PASS' if ok else 'FAIL'}   composes "
              f"{' + '.join(t['ports'])}")
        print(f"    claims     {t['statement']}")
        print(f"    measured   {r['detail']}")
        print(f"    ablation   {r['ablation']}")
        if not ok:
            print(f"    FALSIFIER  {t['falsifier']}")
    print("\n" + "=" * 100)
    print(f"  {good}/{len(PRIMITIVES)} primitives validated. A primitive whose ABLATION also "
          f"passes proved nothing:\n  it would mean the ports compose to something one of them "
          f"already did alone.")


if __name__ == "__main__":
    main()
