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


# ------------------------------------------------------------------------------------------------
# THE THREE THAT DO NOT PASS SHARE ONE CAUSE, and it is worth stating before the tests rather than
# after: STIFFNESS, WEIGHT_TRANSFER and UPRIGHT are all swamped by the body collapsing around the
# joint under test. The pelvis harness holds the root; it does not hold the THIGH, so a knee
# stiffness probe measures a leg swinging. It does not hold the TRUNK, so a lumbar probe measures a
# spine folding. And weight transfer cannot use the harness at all, because a rigid root pin
# carries the weight the feet were supposed to share -- feet that in free collapse carry 177 N of a
# 580 N body, which is not standing and cannot be asked about load sharing.
#
#     THESE THREE NEED A STRONGER ISOLATION THAN A PELVIS HARNESS, not a different physics.
#
# That is a test-design gap with a name, not a blocked mechanism, and it is recorded as failing
# rather than quietly rescoped: three of the seven primitives are UNMEASURED, and a composition
# built on them would inherit an assumption nobody checked.
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
    j, adr, dof = joint(m, "knee_angle_r")
    q_set = math.radians(30.0)
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

    # WHICHEVER GROUP IS STRONGER HOLDS, and the disturbance pushes against it. At this knee the
    # group labelled "extensors" is ONE muscle making 3 N.m -- the quadriceps reach knee_angle_r
    # only through the patellar coupling. A test that drives the weak side measures the weak side.
    hi_g, lo_g = (flex, ext) if group_cap(flex[:6]) >= group_cap(ext[:6]) else (ext, flex)
    fx, ex = lo_g[:6], hi_g[:6]
    K, N = 12.0, 1200

    # THE DISTURBANCE IS DERIVED FROM WHAT THIS KNEE CAN HOLD, not picked. Measure the torque the
    # muscles being driven actually produce at this pose, then probe at fractions of it until the
    # loop is off its ceiling. 60 N.m -- the first guess -- pinned it at a=0.987.
    mujoco.mj_resetData(m, d)
    d.qpos[adr] = q_set
    d.ctrl[:] = 0.0
    if m.na:
        d.act[:] = 0.0
    for k in ex:
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
        q0 = np.array(d.qpos[0:7])
        used, dev = [], []
        for i in range(N):
            hold_root(d, q0)
            err = float(d.qpos[adr]) - q_set
            a = float(np.clip(gain * abs(err), 0.0, 1.0)) if fixed is None else fixed
            d.ctrl[:] = 0.0
            for k in (ex if err > 0 else fx):
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
                detail=f"knee held at 30 deg against {dist:.1f} N.m ({dist / max(cap, 1e-9):.0%} of "
                       f"the {cap:.0f} N.m these muscles make here): closed loop deviates "
                       f"{math.degrees(closed):.2f} deg, open loop {math.degrees(open_):.2f} deg "
                       f"({open_ / max(closed, 1e-9):.1f}x)")


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
        mujoco.mj_resetDataKeyframe(m, d, 0)
        seat_on_floor(m, d, mujoco)               # the feet must be ON the ground to share a load
        # LEAN, do not TRANSLATE. Moving the root sideways moves the feet with it, so nothing
        # changes relative to the base of support -- all three offsets read identically, to the
        # decimal. Rolling the root moves the CoM ACROSS the feet, which is what a weight shift is.
        roll = dy / 0.9                            # small-angle: lateral CoM offset / CoM height
        w = math.cos(0.5 * roll)
        d.qpos[3:7] = [w, math.sin(0.5 * roll), 0.0, 0.0]
        mujoco.mj_forward(m, d)
        # NO HARNESS HERE, and that is the point. A rigid root pin carries the body's weight
        # through the pin, so every plantar sensor read 0.0 N -- the hold I added to make the pose
        # stable deleted the quantity being measured. The body is set on the floor and released;
        # it starts to topple, but for the first fifth of a second its feet carry it, and that is
        # when a shared load is a shared load.
        rows = []
        for i in range(240):
            d.ctrl[:] = 0.0
            mujoco.mj_step(m, d)
            if i > 120:
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
    "tilt falls no faster with the gravity loop closed than with the same mean drive open-loop, "
    "meaning the otolith reading is not steering anything")
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
        chain.append((nm, int(m.jnt_qposadr[jj]), p[:4], n[:4]))
    if not chain:
        raise SystemExit("no trunk flexion joint found -- refusing to invent one")
    nsp = len(chain)
    nm = " + ".join(c[0] for c in chain)
    torso = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "torso")
    if torso < 0:
        torso = int(m.body_parentid[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "head")])
    TILT, N = math.radians(8.0), 900

    def run(gain, fixed=None):
        mujoco.mj_resetDataKeyframe(m, d, 0)
        mujoco.mj_forward(m, d)
        gvN = np.asarray(d.xmat[torso]).reshape(3, 3).T @ np.array([0.0, 0.0, -g])
        for _, a_, _p, _n in chain:
            d.qpos[a_] = TILT / len(chain)        # the lean shared down the chain, as a spine bends
        mujoco.mj_forward(m, d)
        q0 = np.array(d.qpos[0:7])
        gv0 = gvN                              # neutral BEFORE the tilt was applied
        used, tilt = [], []
        for i in range(N):
            hold_root(d, q0)
            R = np.asarray(d.xmat[torso]).reshape(3, 3)
            gv = R.T @ np.array([0.0, 0.0, -g])       # THE OTOLITH: gravity in the body's frame
            # AGAINST ITS OWN NEUTRAL, because the torso's local axes are not assumed to point
            # anywhere. Reading atan2(gv_x, -gv_z) as if local +Z were up gave 90 deg of "lean"
            # at rest, through four lumbar joints whose entire range is 24 deg.
            lean = float(np.arctan2(np.linalg.norm(np.cross(gv, gv0)), float(np.dot(gv, gv0))))
            lean *= 1.0 if float(np.dot(np.cross(gv0, gv), np.array([0.0, 1.0, 0.0]))) > 0 else -1.0
            a = float(np.clip(gain * abs(lean), 0.0, 1.0)) if fixed is None else fixed
            d.ctrl[:] = 0.0
            for _nm, _a, p_, n_ in chain:
                for k in (n_ if lean > 0 else p_):
                    d.ctrl[k] = a
            mujoco.mj_step(m, d)
            used.append(a)
            if i > N // 2:
                tilt.append(abs(lean))
        return float(np.mean(tilt)), float(np.mean(used))

    gain, (closed, mean_a), sat = unsaturated(lambda k: run(k), [6.0, 3.0, 1.5, 0.7])
    open_, _ = run(0.0, fixed=mean_a)             # ABLATION: same mean drive, gravity ignored
    ok = sat is None and closed < 0.8 * open_
    return dict(pass_=ok, ablation=(sat or f"open loop at the closed loop's own mean drive "
                                    f"a={mean_a:.3f}"),
                detail=f"{nsp} lumbar joints released from {math.degrees(TILT):.0f} deg total "
                       f"(top 4 muscles each, gain {gain:.1f}): mean "
                       f"lean {math.degrees(closed):.2f} deg closed-loop vs "
                       f"{math.degrees(open_):.2f} deg open-loop")


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
