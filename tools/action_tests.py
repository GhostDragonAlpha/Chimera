"""action_tests.py -- THE TWELVE ACTION PRIMITIVES the operator named.

    Stance · Swing · Balance · Lift · Push · Pull · Grip · Throw · Land · Step · Turn · Crouch

A PORT is one instruction. A MECHANISM PRIMITIVE (`primitive_tests.py`) is what two ports do that
neither does alone. An ACTION PRIMITIVE is one thing the BODY DOES -- a program over that
instruction set -- and it is the layer compositions are built from.

RULE 0 HAS THREE PARTS AND THE REGISTRY ONLY ENFORCED TWO. `port_test` and `primitive_test` demand
a STATEMENT and a FALSIFIER; the PREDICTION lived wherever the author put it, which means the
number could be written after the run and nobody could tell. `action_test` makes PREDICTION a
required registration argument -- declared at import, which is necessarily before the test can have
run. A prediction produced after the measurement is a description, and a description survives any
result.

EVERY PREDICTION HERE IS A LAW, NOT A TOLERANCE. Each one is a closed-form quantity computed from
the model's own mass, inertia and this world's gravity BEFORE the simulation:

    SWING     T = 2*pi*sqrt(I/(m g d))   the leg as a compound pendulum
    BALANCE   omega0 = sqrt(g/H)          the body as an inverted pendulum
    LAND      J = m*sqrt(2 g h)           impulse, from momentum -- needs no stiffness
    THROW     R = v^2 sin(2*theta) / g    ballistic range
    TURN      dL_z = 0                    internal torques cannot change total angular momentum
    STANCE    sum(plantar) = (1-s) W      what the harness does not carry, the feet do
    CROUCH    tau_knee = W_above * lever  measured two ways, and they must agree

    A PREDICTION YOU CAN ONLY CHECK LOOSELY IS A PREDICTION YOU CHOSE.

THE INSTRUMENTS. Two, both of which exist in real biomechanics labs, and both DECLARED rather than
hidden inside a test:

  CLAMP      restore named joints to their start every step. A dynamometer chair clamps the thigh
             so a knee can be measured; this is that, in software.
  HARNESS    hold the root's ORIENTATION and horizontal position, leave z FREE, and apply an
             upward force of `s` x body weight. That is body-weight-support treadmill training,
             and it makes STANCE a conservation law: the feet must carry exactly (1-s)W. It is run
             at three values of s, so the test is a LINE rather than a single agreeing number.

             The harness of `primitive_tests.py` pinned z as well, and therefore carried the whole
             weight -- every plantar sensor read 0.0 N. A support that takes all the load cannot be
             used to measure load sharing.

    python tools/action_tests.py
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import mujoco
import numpy as np

import port_tests                                   # noqa: F401  ports 1-4
import port_tests_more                              # noqa: F401  ports 5-12
import primitive_tests                              # noqa: F401  the 7 mechanism primitives
from port_registry import ACTIONS, MYOBODY, action_test, expect_actions
from primitive_tests import seat_on_floor, spanning
from world import load_body


# ------------------------------------------------------------------------------------------------
# instruments
# ------------------------------------------------------------------------------------------------
def body_facts(m, d, g):
    mujoco.mj_forward(m, d)
    M = float(np.sum(m.body_mass))
    return M, M * g, np.array(d.subtree_com[1])


BRACE_TOL_DEG = 1.0


def brace(m, d, q0, g, free=()):
    """An ORTHOSIS. Hold every joint but `free` at q0, using the model's OWN passive spring.

    THREE WAYS TO BRACE A JOINT, AND ONLY THE THIRD WORKS.

      RESTORE qpos EVERY STEP -- teleportation. It reaches a stable pose and reports 8344 N of
      plantar load against a predicted 290, because the contact solver answers a body
      teleported into the floor with whatever force that takes. Stable, repeatable, 28x wrong.

      qfrc_applied WITH A PD LOOP -- a real force, but explicit, and it NaN'd at t = 0.006 s.
      The gains that hold an 82 kg body are past what an explicit integrator can carry, and
      shrinking them until it survives is a parameter sweep standing in for a derivation.

      jnt_stiffness + dof_damping -- the model's own passive spring, integrated IMPLICITLY by
      `implicitfast`, which is stable exactly where the explicit force is not. This one.

    K IS DERIVED, not chosen: stiff enough that the largest static moment this body can apply
    -- its whole weight on its whole leg -- deflects the joint less than BRACE_TOL_DEG. And it
    is VERIFIED rather than assumed: brace_dev() reports what it actually held to, so a test
    whose brace slipped says so instead of publishing the number it produced.
    """
    W = float(np.sum(m.body_mass)) * g
    K = W * 0.9201 / math.radians(BRACE_TOL_DEG)
    C = 2.0 * math.sqrt(K * 3.0)
    skip = {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, x) for x in free}
    for j in range(m.njnt):
        if m.jnt_type[j] in (2, 3) and j not in skip:
            a, f = int(m.jnt_qposadr[j]), int(m.jnt_dofadr[j])
            m.jnt_stiffness[j] = K
            m.qpos_spring[a] = q0[a]
            m.dof_damping[f] = C
    return K


def brace_dev(m, d, q0, free=()):
    """How far the orthosis actually let each joint move -- and NOT counting the ones it
    could never have held.

    13 joints of this keyframe sit OUTSIDE their own published range (the lumbar chain and the
    knee's coupled dofs, which `world.py` names and deliberately leaves alone). A spring whose
    set point is outside the joint's limit can never reach it, so those joints show a
    permanent offset -- 20.89 deg of it -- that is the keyframe's pre-existing defect wearing
    the brace's name. Reported separately instead of blamed on the instrument.
    """
    skip = {mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, x) for x in free}
    out, unreachable = 0.0, 0
    for j in range(m.njnt):
        if m.jnt_type[j] not in (2, 3) or j in skip:
            continue
        a = int(m.jnt_qposadr[j])
        if m.jnt_limited[j] and not (m.jnt_range[j][0] <= q0[a] <= m.jnt_range[j][1]):
            unreachable += 1
            continue
        out = max(out, abs(math.degrees(float(d.qpos[a]) - q0[a])))
    return out, unreachable


def clamp(m, d, q0, free_adr=()):
    """A dynamometer. Restore every joint but the named ones -- what a chair does to a thigh."""
    keep = {int(a): float(d.qpos[int(a)]) for a in free_adr}
    d.qpos[:] = q0
    d.qvel[:] = 0.0
    for a, v in keep.items():
        d.qpos[a] = v


def harness(m, d, q0, support, W, lock_xy=True):
    """Body-weight support. Orientation and x,y held; z FREE; `support` x W carried from above.

    z is left free ON PURPOSE. A harness that pins the height carries the whole weight, and the
    feet -- the thing being measured -- then carry nothing.
    """
    if lock_xy:
        d.qpos[0:2] = q0[0:2]
        d.qvel[0:2] = 0.0
    d.qpos[3:7] = q0[3:7]
    d.qvel[3:6] = 0.0
    d.xfrc_applied[:] = 0.0
    d.xfrc_applied[1][2] = support * W


def plantar(m, d):
    l = r = 0.0
    for s in range(m.nsensor):
        nm = (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_SENSOR, s) or "").lower()
        v = abs(float(d.sensordata[s]))
        if nm.startswith("l"):
            l += v
        else:
            r += v
    return l, r


def angmom_z(m, d):
    mujoco.mj_subtreeVel(m, d)
    return float(d.subtree_angmom[1][2])


def settle(m, d, n, fn=None):
    for i in range(n):
        d.ctrl[:] = 0.0
        if fn:
            fn(i)
        mujoco.mj_step(m, d)


# ------------------------------------------------------------------------------------------------
@action_test(
    "stance", ["contact", "plantar_pressure", "rigid_body"],
    "a supported body puts on its feet exactly the weight nothing else is carrying -- stance is a "
    "CONSERVATION statement before it is a postural one",
    "sum(plantar) = (1 - s) x 580.5 N across three harness settings s = 0.25 / 0.40 / 0.55, i.e. "
    "a LINE of slope -W through the three points, not one agreeing number",
    "the feet carry an amount unrelated to what the harness leaves them, or the three points do "
    "not fall on the predicted line")
def a_stance(_):
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    M, W, _ = body_facts(m, d, g)
    got, want, devs = [], [], []
    for s in (0.25, 0.40, 0.55):
        # A FRESH MODEL EACH TIME: brace() edits the model, not the data.
        m, g = load_body(MYOBODY, mujoco)
        d = mujoco.MjData(m)
        mujoco.mj_resetDataKeyframe(m, d, 0)
        seat_on_floor(m, d, mujoco)
        mujoco.mj_forward(m, d)
        q0 = np.array(d.qpos)
        brace(m, d, q0, g)     # no controller exists, so unbraced legs fold and carry nothing
        settle(m, d, 1500, lambda i: harness(m, d, q0, s, W))
        l, r = plantar(m, d)
        got.append(l + r)
        want.append((1.0 - s) * W)
        devs.append(brace_dev(m, d, q0))
    err = [abs(a - b) / max(b, 1e-9) for a, b in zip(got, want)]
    slope = np.polyfit((0.25, 0.40, 0.55), got, 1)[0]
    ok = max(err) < 0.25 and abs(slope + W) / W < 0.35
    return dict(pass_=ok, got=f"{got[0]:.1f} / {got[1]:.1f} / {got[2]:.1f} N",
                detail=f"feet carry {got[0]:.1f}/{got[1]:.1f}/{got[2]:.1f} N against a predicted "
                       f"{want[0]:.1f}/{want[1]:.1f}/{want[2]:.1f}; worst {100*max(err):.1f}% off, "
                       f"fitted slope {slope:+.1f} N vs -W = {-W:.1f}; brace held to "
                       f"{max(x[0] for x in devs):.2f} deg on the joints it could hold "
                       f"({devs[0][1]} more start outside their own published range, where "
                       f"no spring can reach them)")


# ------------------------------------------------------------------------------------------------
@action_test(
    "swing", ["rigid_body", "spindle"],
    "an unloaded leg is a COMPOUND PENDULUM and its natural period is a property of the body, not "
    "a number anyone selects -- which is why cadence is derived and never tuned",
    "T = 2*pi*sqrt(I/(m g d)), with I from the model's own joint-space inertia at the hip, m and d "
    "from the leg's mass and CoM. Computed before the run; the measured period must match it",
    "the measured free-swing period differs from the derived pendulum period by more than 15%, "
    "which would mean cadence cannot be derived from the body at all")
def a_swing(_):
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    j = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, "hip_flexion_r")
    adr, dof = int(m.jnt_qposadr[j]), int(m.jnt_dofadr[j])
    mujoco.mj_resetDataKeyframe(m, d, 0)
    d.qpos[2] += 1.5                                   # hang it clear of the floor
    mujoco.mj_forward(m, d)

    # THE PREDICTION, from the model and nothing else.
    # COMPOSITE RIGID BODY about the hip axis, from the model's own inertia tensors:
    #     I = sum_b [ a . (R_b I_b R_b^T) . a  +  m_b * r_perp^2 ]
    # Both mj_fullM signatures the binding accepts were rejected here, and fighting a wrapper
    # is the wrong move anyway: this is the derivation written out, so what it rests on is
    # visible rather than delegated.
    fem = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "femur_r")
    hip = np.array(d.xanchor[j])
    axis = np.array(d.xaxis[j]) / np.linalg.norm(d.xaxis[j])
    leg = [b for b in range(m.nbody)
           if any(k in (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, b) or "")
                  for k in ("femur_r", "patella_r", "tibia_r", "talus_r", "calcn_r", "toes_r"))]
    I, m_leg, msum = 0.0, 0.0, np.zeros(3)
    for b in leg:
        R = np.asarray(d.ximat[b]).reshape(3, 3)
        Ib = R @ np.diag(np.asarray(m.body_inertia[b])) @ R.T
        rp = np.array(d.xipos[b]) - hip
        rp = rp - np.dot(rp, axis) * axis           # perpendicular to the axis
        mb = float(m.body_mass[b])
        I += float(axis @ Ib @ axis) + mb * float(np.dot(rp, rp))
        m_leg += mb
        msum += mb * np.array(d.xipos[b])
    com_leg = msum / m_leg
    rc = com_leg - hip
    dcm = float(np.linalg.norm(rc - np.dot(rc, axis) * axis))
    T_pred = 2.0 * math.pi * math.sqrt(I / (m_leg * g * dcm))

    q0 = np.array(d.qpos)
    # BRACED, NOT CLAMPED. Restoring qpos for every other joint each step teleports the body,
    # and a teleported pendulum has no period at all -- the first run found 0 zero-crossings
    # and returned nan. The orthosis holds the rest of the body with force; the hip is free.
    brace(m, d, q0, g, free=('hip_flexion_r',))
    d.qpos[adr] = q0[adr] + math.radians(12.0)
    mujoco.mj_forward(m, d)
    ts, qs = [], []
    for i in range(6000):
        d.ctrl[:] = 0.0
        d.qpos[0:7] = q0[0:7]
        d.qvel[0:6] = 0.0                              # hung from a fixed point
        mujoco.mj_step(m, d)
        ts.append(d.time)
        qs.append(float(d.qpos[adr]))
    qs = np.array(qs) - np.mean(qs)
    zc = [ts[i] for i in range(1, len(qs)) if qs[i - 1] < 0 <= qs[i]]
    T_got = float(np.mean(np.diff(zc))) if len(zc) > 2 else float("nan")
    err = abs(T_got - T_pred) / T_pred if T_pred > 0 else 1.0
    return dict(pass_=err < 0.15, got=f"T = {T_got:.4f} s",
                detail=f"I {I:.4f} kg.m2, leg {m_leg:.3f} kg, pivot->CoM {dcm:.4f} m -> predicted "
                       f"T = {T_pred:.4f} s; measured {T_got:.4f} s over {max(len(zc)-1,0)} cycles "
                       f"({100*err:.1f}% off)")


# ------------------------------------------------------------------------------------------------
@action_test(
    "balance", ["rigid_body", "contact", "otolith"],
    "a body standing is an INVERTED PENDULUM: released off vertical it diverges exponentially at "
    "a rate fixed by gravity and its own CoM height, and that rate is the clock every postural "
    "loop must beat",
    "the horizontal CoM displacement grows as cosh(omega0 t) with omega0 = sqrt(g/H) -- "
    "sqrt(7.0761/H) rad/s, computed from the model's own CoM before the run",
    "the measured divergence rate differs from sqrt(g/H) by more than 20%, which would mean the "
    "0.4066 s time-to-fall every control-rate argument rests on is not this body's number")
def a_balance(_):
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    mujoco.mj_resetDataKeyframe(m, d, 0)
    seat_on_floor(m, d, mujoco)
    mujoco.mj_forward(m, d)
    q0 = np.array(d.qpos)
    brace(m, d, q0, g)          # rigid: this tests the PENDULUM, not the spine
    foot = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, 'calcn_r')
    pivot = np.array(d.xpos[foot])
    com0 = np.array(d.subtree_com[1])
    H = float(np.linalg.norm(com0 - pivot))
    w_pred = math.sqrt(g / H)

    # THE PIVOT IS PINNED. Leaving contact to supply it lets the body slide and bounce rather
    # than rotate, and the fit then reads 15.46 rad/s off a transient -- 457% out. An inverted
    # pendulum is a body turning about a FIXED point; pinning it is what makes the measurement
    # the same experiment as the prediction.
    d.qvel[:] = 0.0
    d.qvel[4] = 0.05
    ts, xs = [], []
    for i in range(2500):
        d.ctrl[:] = 0.0
        d.qpos[0:3] = q0[0:3]
        d.qvel[0:3] = 0.0
        mujoco.mj_step(m, d)
        ts.append(d.time)
        xs.append(abs(float(d.subtree_com[1][0] - com0[0])))
    ts, xs = np.array(ts), np.array(xs)
    sel = (xs > 2e-3) & (xs < 0.35 * H)
    w_got = float(np.polyfit(ts[sel], np.log(xs[sel]), 1)[0]) if sel.sum() > 30 else float('nan')
    err = abs(w_got - w_pred) / w_pred
    return dict(pass_=err < 0.20, got=f'omega0 = {w_got:.4f} rad/s',
                detail=f'CoM {H:.4f} m from the pinned pivot -> predicted sqrt(g/H) = '
                       f'{w_pred:.4f} rad/s (time to fall {1/w_pred:.4f} s); measured '
                       f'divergence {w_got:.4f} rad/s over {int(sel.sum())} samples '
                       f'({100*err:.1f}% off)')


# ------------------------------------------------------------------------------------------------
@action_test(
    "lift", ["hill_muscle", "rigid_body", "damping"],
    "raising mass costs work, and the muscles must SUPPLY it -- the energy budget of an action is "
    "checkable independently of whether the action looks right",
    "muscle work >= m g dh with efficiency = m g dh / W_muscle strictly in (0, 1]. Any part of the "
    "rise not paid for by a muscle is energy this simulator invented",
    "measured efficiency exceeds 1.0 -- the body gained more potential energy than its muscles "
    "did work, which is energy from nowhere and would invalidate every energetic claim built on it")
def a_lift(_):
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    j = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, 'hip_flexion_r')
    adr, dof = int(m.jnt_qposadr[j]), int(m.jnt_dofadr[j])
    mujoco.mj_resetDataKeyframe(m, d, 0)
    d.qpos[2] += 1.5            # HUNG CLEAR. A body collapsing onto the floor lowers its CoM
    mujoco.mj_forward(m, d)     # and lifts nothing: the first run measured -207 mm and a
    q0 = np.array(d.qpos)       # negative efficiency, which is a fall, not a lift.
    brace(m, d, q0, g, free=('hip_flexion_r',))
    fem = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, 'femur_r')
    m_leg = float(m.body_subtreemass[fem])
    z0 = float(d.subtree_com[fem][2])
    up, dn = spanning(m, d, dof)
    drive = up[:8]

    Wm = 0.0
    for i in range(1200):
        d.qpos[0:7] = q0[0:7]
        d.qvel[0:6] = 0.0       # the harness, at full support
        d.ctrl[:] = 0.0
        for k in drive:
            d.ctrl[k] = 1.0
        mujoco.mj_step(m, d)
        Wm += float(np.sum(np.abs(np.asarray(d.actuator_force) *
                                  np.asarray(d.actuator_velocity)))) * m.opt.timestep
    dh = float(d.subtree_com[fem][2]) - z0
    dPE = m_leg * g * dh
    eff = dPE / Wm if Wm > 1e-9 else float('nan')
    return dict(pass_=(0.0 < eff <= 1.0), got=f'efficiency {eff:.4f}',
                detail=f'leg {m_leg:.3f} kg raised {1000*dh:+.2f} mm -> dPE {dPE:+.3f} J '
                       f'against {Wm:.2f} J of muscle work; efficiency {eff:.4f}, '
                       + ('inside (0,1]' if 0 < eff <= 1 else 'OUTSIDE (0,1]')
                       + '. A WEAK TEST BY CONSTRUCTION: its falsifier only catches energy '
                         'created from nothing, and most of the work here goes to co-'
                         'contraction rather than to the load.')


# ------------------------------------------------------------------------------------------------
def _slip(m, d, g, sign):
    """Ramp a horizontal force at the trunk until the feet slide. Returns (F_slip, mu*N)."""
    M, W, _ = body_facts(m, d, g)
    mujoco.mj_resetDataKeyframe(m, d, 0)
    seat_on_floor(m, d, mujoco)
    mujoco.mj_forward(m, d)
    q0 = np.array(d.qpos)
    brace(m, d, q0, g)
    S = 0.40
    settle(m, d, 1200, lambda i: harness(m, d, q0, S, W))   # take the load BEFORE pushing
    foot = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "calcn_r")
    x0 = float(d.xpos[foot][0])
    mu = float(m.geom_friction[0][0])
    N = None
    F = 0.0
    # x,y RELEASED for the ramp. Held, the body cannot slide however hard it is pushed, and the
    # ramp runs to its ceiling and reports 696.4 N as a slip threshold -- which is the harness's
    # number, not friction's. The fourth time an instrument deleted its own measurement.
    slipped = False
    for i in range(2500):
        harness(m, d, q0, S, W, lock_xy=False)
        F = 1.2 * W * i / 2500.0
        d.xfrc_applied[1][0] = sign * F
        d.ctrl[:] = 0.0
        mujoco.mj_step(m, d)
        if N is None and i == 200:
            N = sum(plantar(m, d))
        if abs(float(d.xpos[foot][0]) - x0) > 0.02:
            slipped = True
            break
    return F, mu * (1.0 - S) * W, mu, (N or 0.0), slipped


@action_test(
    "push", ["contact", "plantar_pressure", "rigid_body"],
    "how hard a body can push on the world is set by the FRICTION UNDER ITS FEET, not by its "
    "muscles -- which is why you cannot push a car on ice however strong you are",
    "slip begins at F = mu x N with mu = 1.0 read from the model's own geoms and N the load the "
    "harness leaves on the feet: F_slip = 1.0 x 0.60 x 580.5 = 348.3 N",
    "the body sustains a push far beyond mu x N without sliding -- force from nowhere -- or slips "
    "far below it, meaning something other than friction is setting the bound")
def a_push(_):
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    F, bound, mu, N, slipped = _slip(m, d, g, +1.0)
    err = abs(F - bound) / bound
    return dict(pass_=slipped and err < 0.50, got=f"slip at {F:.1f} N",
                detail=f"mu {mu:.2f}, feet loaded {N:.1f} N -> Coulomb bound {bound:.1f} N; "
                       + (f"slid at {F:.1f} N ({100*err:.1f}% off)" if slipped else
                          f"NEVER SLID up to {F:.1f} N -- no threshold was observed, so there "
                          f"is nothing here to compare with the bound"))


@action_test(
    "pull", ["contact", "plantar_pressure", "rigid_body"],
    "pulling is bounded by the same friction as pushing -- Coulomb friction is ISOTROPIC, so the "
    "two thresholds are one number measured twice, and any difference is anatomy, not physics",
    "F_slip(pull) = F_slip(push) to within 25%, both landing on mu x N = 348.3 N",
    "the two directions differ by more than 25%, which would mean the bound is being set by "
    "something directional -- foot geometry or the harness -- and not by friction")
def a_pull(_):
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    Fp, bound, mu, _, sp = _slip(m, d, g, +1.0)
    Fm, _, _, _, sm = _slip(m, d, g, -1.0)
    asym = abs(Fp - Fm) / max(Fp, Fm, 1e-9)
    # BOTH MUST ACTUALLY SLIP. When neither did, the two runs ended at the same RAMP CEILING
    # and the symmetry test reported 0.0% asymmetry -- a pass that compared two non-events.
    return dict(pass_=sp and sm and asym < 0.25, got=f"push {Fp:.1f} N / pull {Fm:.1f} N",
                detail=f"push {Fp:.1f} N ({'slid' if sp else 'NEVER SLID'}), pull {Fm:.1f} N "
                       f"({'slid' if sm else 'NEVER SLID'}) against one Coulomb bound of "
                       f"{bound:.1f} N -- asymmetry {100*asym:.1f}%"
                       + ("" if (sp and sm) else "  [VACUOUS: two ramp ceilings are equal "
                          "whether or not friction is isotropic]"))


# ------------------------------------------------------------------------------------------------
@action_test(
    "grip", ["contact", "hill_muscle"],
    "a grip closes until it cannot and the OBJECT decides where the fingers land; holding force is "
    "bounded by friction at the contact, F_hold <= mu x F_grip",
    "REFUSED BEFORE IT IS RUN: this test predicts nothing, because the structure it would measure "
    "is not in the body. myobody has 47 joints and none of them is a shoulder, elbow, wrist, "
    "thumb or finger",
    "a grip force is reported at all -- there is no hand here, so any number would be measuring "
    "something else and calling it a grip")
def a_grip(_):
    m, g = load_body(MYOBODY, mujoco)
    names = [(mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, j) or "").lower()
             for j in range(m.njnt)]
    hand = [n for n in names if any(k in n for k in
                                    ("finger", "thumb", "wrist", "hand", "mcp", "elbow", "shoulder"))]
    return dict(pass_=False, refused=not hand, got="no hand in the model",
                detail=f"searched {len(names)} joints for finger/thumb/wrist/hand/elbow/shoulder "
                       f"and found {len(hand)}. REFUSING to report a grip force from a body with "
                       f"no arm. This is an ABSENT STRUCTURE, not a failed action -- the test "
                       f"stays registered so the gap is counted instead of forgotten.")


# ------------------------------------------------------------------------------------------------
@action_test(
    "throw", ["rigid_body"],
    "once released, a thrown mass is BALLISTIC -- the body's only influence is the velocity at "
    "release, and everything after it belongs to the world",
    "R = v^2 sin(2 theta) / g. At v = 6 m/s and theta = 40 deg in this world's g = 7.0761: "
    "R = 36 x sin(80 deg) / 7.0761 = 5.0104 m",
    "the measured range differs from the ballistic prediction by more than the integrator's own "
    "discretisation -- which would mean this world's gravity is not what the membrane publishes")
def a_throw(_):
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    V, TH = 6.0, math.radians(40.0)
    R_pred = V * V * math.sin(2 * TH) / g
    mujoco.mj_resetDataKeyframe(m, d, 0)
    d.qpos[2] += 6.0
    d.qvel[:] = 0.0
    d.qvel[0], d.qvel[2] = V * math.cos(TH), V * math.sin(TH)
    mujoco.mj_forward(m, d)
    c0 = np.array(d.subtree_com[1])
    x = z = 0.0
    for _ in range(4000):
        d.ctrl[:] = 0.0
        mujoco.mj_step(m, d)
        c = np.array(d.subtree_com[1])
        x, z = float(c[0] - c0[0]), float(c[2] - c0[2])
        if z < 0.0:
            break
    R_got = x
    err = abs(R_got - R_pred) / R_pred
    return dict(pass_=err < 0.05, got=f"R = {R_got:.4f} m",
                detail=f"v {V:.1f} m/s at {math.degrees(TH):.0f} deg in g {g:.4f} -> predicted "
                       f"R = {R_pred:.4f} m; measured {R_got:.4f} m ({100*err:.2f}% off). "
                       f"Earth would give {V*V*math.sin(2*TH)/9.80665:.4f} m")


# ------------------------------------------------------------------------------------------------
@action_test(
    "land", ["contact", "plantar_pressure", "damping", "end_stop"],
    "landing is an IMPULSE problem before it is a force problem: whatever the legs do, the ground "
    "must remove all the momentum the fall built, and that total is fixed by the drop alone",
    "J = integral(F dt) = m sqrt(2 g h). Dropping 82.041 kg from 0.20 m at g = 7.0761: "
    "J = 82.041 x sqrt(2 x 7.0761 x 0.20) = 137.98 N.s -- independent of how stiff the legs are",
    "the measured contact impulse differs from m sqrt(2gh) by more than 20%, which would mean "
    "momentum is not conserved through the contact and no landing model can be trusted")
def a_land(_):
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    M = float(np.sum(m.body_mass))
    H = 0.20
    J_pred = M * math.sqrt(2.0 * g * H)
    mujoco.mj_resetDataKeyframe(m, d, 0)
    seat_on_floor(m, d, mujoco)
    d.qpos[2] += H
    d.qvel[:] = 0.0
    mujoco.mj_forward(m, d)
    dt, J, touched, vmax = m.opt.timestep, 0.0, False, 0.0
    for _ in range(1600):
        d.ctrl[:] = 0.0
        mujoco.mj_step(m, d)
        vmax = max(vmax, abs(float(d.qvel[2])))
        f = sum(plantar(m, d))
        if f > 1.0:
            touched = True
        if touched:
            J += f * dt
        if touched and abs(float(d.qvel[2])) < 0.02 and J > 0.5 * J_pred:
            break
    err = abs(J - J_pred) / J_pred
    return dict(pass_=err < 0.20, got=f"J = {J:.2f} N.s",
                detail=f"dropped {1000*H:.0f} mm, impact speed {vmax:.4f} m/s "
                       f"(sqrt(2gh) = {math.sqrt(2*g*H):.4f}) -> predicted impulse "
                       f"{J_pred:.2f} N.s; measured {J:.2f} N.s ({100*err:.1f}% off)")


# ------------------------------------------------------------------------------------------------
@action_test(
    "step", ["plantar_pressure", "contact", "hill_muscle"],
    "a step is a TRANSFER: one foot leaves the ground and the other takes everything it was "
    "carrying. Single support is the moment the whole load lives on one leg, and it is what a "
    "gait is made of",
    "with one foot lifted, the lifted foot reads 0 N and the stance foot reads the entire load the "
    "harness leaves, (1-s) W = 348.3 N -- the total unchanged from double support",
    "the lifted foot still reports load, or the total changes when the load moves, either of which "
    "means the sensors are not measuring a transfer")
def a_step(_):
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    M, W, _ = body_facts(m, d, g)
    S = 0.40
    j = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, "hip_flexion_l")
    adr = int(m.jnt_qposadr[j])
    mujoco.mj_resetDataKeyframe(m, d, 0)
    seat_on_floor(m, d, mujoco)
    mujoco.mj_forward(m, d)
    q0 = np.array(d.qpos)
    K = brace(m, d, q0, g)
    settle(m, d, 1200, lambda i: harness(m, d, q0, S, W))
    l0, r0 = plantar(m, d)
    # WALK THE BRACE'S SET POINT, do not write qpos. Teleporting the leg upward drives it
    # through the floor and the contact solver answers with force that is not a load.
    for i in range(1600):
        harness(m, d, q0, S, W)
        m.qpos_spring[adr] = q0[adr] + math.radians(min(35.0, 35.0 * i / 600.0))
        d.ctrl[:] = 0.0
        mujoco.mj_step(m, d)
    l1, r1 = plantar(m, d)
    tot0, tot1 = l0 + r0, l1 + r1
    lifted_clean = l1 < max(0.05 * tot1, 1.0)
    kept = abs(tot1 - tot0) / max(tot0, 1e-9)
    # BOTH FEET MUST CARRY LOAD FIRST. The previous run passed with L already at 0.0 N in
    # 'double support' -- lifting a foot that was carrying nothing transfers nothing, and the
    # test scored the absence of a load as a clean unload. A vacuous pass, like PULL's.
    shared = min(l0, r0) > 0.10 * tot0
    ok = shared and lifted_clean and kept < 0.30 and tot1 > 1.0
    return dict(pass_=ok, got=f"L {l1:.1f} / R {r1:.1f} N",
                detail=f"double support L {l0:.1f}/R {r0:.1f} (total {tot0:.1f}) -> left lifted: "
                       f"L {l1:.1f}/R {r1:.1f} (total {tot1:.1f}, {100*kept:.1f}% change) against "
                       f"a predicted {(1-S)*W:.1f} N on one foot"
                       + ("" if shared else "  [VACUOUS: the lifted foot was already carrying "
                          "nothing in double support, so nothing was transferred]"))


# ------------------------------------------------------------------------------------------------
@action_test(
    "turn", ["rigid_body", "hill_muscle", "otolith"],
    "a body in the air cannot turn itself by pushing -- INTERNAL torques cannot change total "
    "angular momentum. Turning needs the ground, and that is why a cat's twist rearranges shape "
    "rather than adding spin",
    "with every muscle firing and no contact, dL_z = 0 to integrator drift. The CONTROL is the "
    "same flight with an EXTERNAL torque applied, which must change L_z -- otherwise the "
    "instrument is blind and the null result means nothing",
    "L_z changes measurably during free flight under internal drive, or the external-torque "
    "control fails to change it")
def a_turn(_):
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)

    def flight(external):
        mujoco.mj_resetDataKeyframe(m, d, 0)
        d.qpos[2] += 8.0
        d.qvel[:] = 0.0
        mujoco.mj_forward(m, d)
        L0 = angmom_z(m, d)
        for i in range(700):
            d.ctrl[:] = 0.0
            for k in range(0, m.nu, 3):
                d.ctrl[k] = 0.5 + 0.5 * math.sin(6.0 * d.time + k)
            d.xfrc_applied[:] = 0.0
            if external:
                d.xfrc_applied[1][5] = 60.0            # a torque about z from OUTSIDE
            mujoco.mj_step(m, d)
        return L0, angmom_z(m, d)

    a0, a1 = flight(False)
    b0, b1 = flight(True)
    drift, forced = abs(a1 - a0), abs(b1 - b0)
    ok = drift < 0.5 and forced > 5.0 * max(drift, 1e-6)
    return dict(pass_=ok, got=f"dL_z = {a1-a0:+.4f} kg.m2/s",
                detail=f"290 muscles driven in free flight: L_z {a0:+.4f} -> {a1:+.4f} "
                       f"(|dL_z| {drift:.4f}); external-torque control {b0:+.4f} -> {b1:+.4f} "
                       f"(|dL_z| {forced:.4f}, {forced/max(drift,1e-9):.0f}x the internal case)")


# ------------------------------------------------------------------------------------------------
@action_test(
    "crouch", ["rigid_body", "contact", "joint_limit"],
    "a held crouch is a STATIC MOMENT problem, and the torque it demands can be computed two ways "
    "-- from the simulator's own inverse dynamics, and from the weight above the knee times its "
    "lever. Two routes to one number is what makes it a measurement rather than a reading",
    "the torque the orthosis supplies, K x (q - q_spring), equals W_above x lever computed from "
    "the model's geometry, to within 25%. Neither route is fitted to the other",
    "the two routes disagree by more than 25%, which would mean the joint torques the trainer "
    "reads are not the torques the body's own geometry demands")
def a_crouch(_):
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    j = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, "knee_angle_r")
    adr, dof = int(m.jnt_qposadr[j]), int(m.jnt_dofadr[j])
    M, W, _ = body_facts(m, d, g)
    mujoco.mj_resetDataKeyframe(m, d, 0)
    seat_on_floor(m, d, mujoco)
    d.qpos[adr] = math.radians(45.0)
    mujoco.mj_forward(m, d)
    q0 = np.array(d.qpos)
    brace(m, d, q0, g)
    # REACH EQUILIBRIUM FIRST. Inverse dynamics at a pose the body is not actually holding
    # returns the torque for that instant, with the ground not yet carrying its share -- it
    # read 0.60 N.m against a 54.17 N.m static requirement, which is what 'not in equilibrium'
    # looks like when you mistake it for a disagreement between two routes.
    settle(m, d, 1500, lambda i: harness(m, d, q0, 0.0, W))
    d.qvel[:] = 0.0
    d.qacc[:] = 0.0
    d.ctrl[:] = 0.0
    if m.na:
        d.act[:] = 0.0
    mujoco.mj_forward(m, d)

    # ROUTE A -- what the ORTHOSIS is actually supplying. tau = K x (q - q_spring), read off a
    # brace that is visibly holding the crouch. This replaces mj_inverse, which returned
    # 5100.8 N.m because qfrc_inverse carries the brace spring itself -- asking the simulator
    # for the torque needed to hold a pose it is already being held in double-counts the hold.
    K = W * 0.9201 / math.radians(BRACE_TOL_DEG)
    tau_inv = abs(K * (float(d.qpos[adr]) - float(m.qpos_spring[adr])))
    # WHY THIS IS NOT 60 N.m. Writing knee_angle_r = 45 deg does NOT pose the knee: this is an
    # OpenSim patellar mechanism whose translations and rotations are driven from that angle by
    # EQUALITY CONSTRAINTS, and they were left where the keyframe put them. The configuration
    # is internally inconsistent, so the constraint solver fights the brace and the brace wins
    # by 5100 N.m. The number is real; it is the torque needed to hold a knee against its own
    # coupling, which is not the torque needed to hold a crouch. Posing this joint requires
    # solving the coupled dofs, which nothing here does yet.
    coupled = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, jj)
               for jj in range(m.njnt)
               if 'knee_angle_r_' in (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, jj) or '')]

    # ROUTE B -- the weight above the knee, times its lever. Independent geometry.
    fem = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "femur_r")
    M_above = float(np.sum(m.body_mass)) - float(m.body_subtreemass[fem])
    knee = np.array(d.xanchor[j])
    com = np.array(d.subtree_com[1])
    lever = abs(float(com[0] - knee[0]))
    tau_geo = M_above * g * lever
    err = abs(tau_inv - tau_geo) / max(tau_geo, 1e-9)
    return dict(pass_=err < 0.25, got=f"{tau_inv:.2f} vs {tau_geo:.2f} N.m",
                detail=f"knee held at 45 deg: the brace supplies {tau_inv:.2f} N.m, geometry "
                       f"{M_above:.2f} kg x g x {1000*lever:.1f} mm lever = {tau_geo:.2f} N.m "
                       f"({100*err:.1f}% apart). CAUSE: knee_angle_r drives {len(coupled)} "
                       f"coupled dofs by equality constraint and they were not re-solved, so "
                       f"the brace is holding the knee against its own coupling, not against "
                       f"the crouch")


# ------------------------------------------------------------------------------------------------
def main():
    expect_actions(12)
    print("=" * 100)
    print(f"  {len(ACTIONS)} ACTION PRIMITIVES -- one thing the body DOES, as a program over "
          f"validated ports")
    print("  Every PREDICTION below was declared at REGISTRATION, which is before any of them ran.")
    print("=" * 100)
    good = refused = 0
    for name, t in ACTIONS.items():
        try:
            r = t["fn"](mujoco)
        except Exception as exc:                       # noqa: BLE001 -- a crash is a result
            print(f"\n  {name.upper():10} ERROR  {type(exc).__name__}: {exc}")
            continue
        if r.get("refused"):
            refused += 1
            tag = "REFUSED"
        else:
            tag = "PASS" if r["pass_"] else "FAIL"
            good += bool(r["pass_"])
        print(f"\n  {name.upper():10} {tag:8} rests on {' + '.join(t['rests_on'])}")
        print(f"    claims     {t['statement']}")
        print(f"    PREDICTED  {t['prediction']}")
        print(f"    measured   {r['detail']}")
        if tag == "FAIL":
            print(f"    FALSIFIER  {t['falsifier']}")
    n = len(ACTIONS)
    print("\n" + "=" * 100)
    print(f"  {good}/{n - refused} action primitives validated, {refused} REFUSED as absent "
          f"structure.\n  A refusal is not a failure of the body -- it is a gap that is COUNTED "
          f"rather than forgotten.")


if __name__ == "__main__":
    main()
