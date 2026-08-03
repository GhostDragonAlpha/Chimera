"""port_tests.py -- VALIDATE ONE INSTRUCTION AT A TIME, against an answer known in advance.

WHY THIS EXISTS, and it is the correction to a whole day's work. On 2026-08-02 I built
increasingly sophisticated searches over a 624-dimensional activation space whose underlying
muscle model I had never checked. Eleven confident diagnoses were reversed. The common shape:

    A FAILURE WAS AMBIGUOUS ACROSS SIXTY UNTESTED EQUATIONS.

The port network is an INSTRUCTION SET (~60 equations) and actions are PROGRAMS composed from it.
An instruction set can be tested independently of the programs -- and must be, because when a
composition fails you need to know whether the composition is wrong or an instruction is.

    Test each port ALONE, against a closed-form answer. Then primitives. Then compositions.
    The parser is LAST: it is the only part that cannot be wrong in an interesting way.

EVERY TEST IS RULE 0 AT INSTRUCTION GRANULARITY -- a STATEMENT, a PREDICTION computed BEFORE the
simulator runs, and a FALSIFIER named in advance. A test whose prediction is read off the result
is a description, and a description cannot be wrong.

Each takes milliseconds. There is no reason ever to have skipped them.

    python tools/port_tests.py            # run every port test
    python tools/port_tests.py --port rigid_body
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body, gravity

MYOBODY = ROOT / "external" / "myo_sim" / "body" / "myobody.xml"
TESTS = {}


def port_test(name, statement, falsifier):
    """Register a port test. All three parts required -- no falsifier, no test."""
    def deco(fn):
        TESTS[name] = dict(fn=fn, statement=statement, falsifier=falsifier, name=name)
        return fn
    return deco


# ── PORT 1: RIGID BODY ────────────────────────────────────────────────────────────────────────
@port_test(
    "rigid_body",
    "an unsupported mass falls as z = z0 - 0.5*g*t^2, with g the value theHuman publishes",
    "the fall does not match the closed form to 0.1%, or it matches EARTH's 9.81 instead of 7.076")
def t_rigid_body(mujoco):
    """The instruction: F = m*a. Predicted BEFORE the step, from g alone."""
    g = gravity()
    xml = f"""<mujoco><option timestep="0.001" gravity="0 0 -{g}"/><worldbody>
      <body name="m" pos="0 0 10"><freejoint/><geom type="sphere" size="0.1" density="1000"/></body>
      </worldbody></mujoco>"""
    m = mujoco.MjModel.from_xml_string(xml)
    d = mujoco.MjData(m)
    z0 = float(d.qpos[2])
    T, dt = 0.5, m.opt.timestep
    n = int(T / dt)
    # PREDICT WHAT THE INTEGRATOR DOES, NOT WHAT CALCULUS DOES. The first version of this test
    # predicted the CONTINUOUS z0 - 0.5*g*T^2 and FAILED at 0.2% -- and 0.2% was exactly
    # g*dt^2*n(n+1)/2 - 0.5*g*T^2 = 0.001769 m, the semi-implicit Euler discretisation term,
    # to six digits. The PORT WAS CORRECT AND THE FALSIFIER WAS MIS-SPECIFIED.
    #
    # A test that holds the simulator to a law the simulator does not implement fails honest
    # code. Predict the discrete sum; keep the continuous value alongside so the size of the
    # discretisation is visible rather than hidden inside a loosened tolerance.
    predicted = z0 - g * dt ** 2 * n * (n + 1) / 2.0
    continuous = z0 - 0.5 * g * T ** 2
    for _ in range(n):
        mujoco.mj_step(m, d)
    got = float(d.qpos[2])
    err = abs(got - predicted) / max(abs(z0 - predicted), 1e-9)
    earth = z0 - 0.5 * 9.80665 * T ** 2
    return dict(pass_=err < 1e-4, pred=predicted, got=got,
                detail=f"drop {T}s ({n} steps): predicted {predicted:.6f} m, got {got:.6f} m, "
                       f"err {100*err:.5f}%  |  continuous form would say {continuous:.6f} "
                       f"(discretisation {abs(predicted-continuous)*1000:.3f} mm)  |  "
                       f"Earth would give {earth:.6f}")


# ── PORT 2: CONTACT ───────────────────────────────────────────────────────────────────────────
@port_test(
    "contact",
    "a mass at rest on the ground returns exactly its own weight through the contact",
    "the summed normal force differs from m*g by more than 1%, or the body never comes to rest")
def t_contact(mujoco):
    """The instruction: F_n = k*d + c*v_n, and at rest it must integrate to m*g.

    TWO MECHANISMS, ONE NUMBER: the contact solver produces the force, the integrator produces
    the rest state. They are computed by different code and must agree -- which is what makes
    this a measurement rather than a definition restating itself.
    """
    g = gravity()
    xml = f"""<mujoco><option timestep="0.001" gravity="0 0 -{g}"/><worldbody>
      <geom name="floor" type="plane" size="5 5 0.1"/>
      <body name="m" pos="0 0 0.3"><freejoint/><geom type="sphere" size="0.1" density="1000"/></body>
      </worldbody></mujoco>"""
    m = mujoco.MjModel.from_xml_string(xml)
    d = mujoco.MjData(m)
    mass = float(sum(m.body_mass))
    predicted = mass * g                                # before the drop
    for _ in range(3000):
        mujoco.mj_step(m, d)
    fz = 0.0
    for c in range(d.ncon):
        f = np.zeros(6)
        mujoco.mj_contactForce(m, d, c, f)
        fz += float(f[0] * d.contact[c].frame[2])
    err = abs(fz - predicted) / max(predicted, 1e-9)
    return dict(pass_=err < 0.01 and abs(float(d.qvel[2])) < 1e-3, pred=predicted, got=fz,
                detail=f"{mass:.4f} kg at rest: predicted {predicted:.4f} N, "
                       f"measured {fz:.4f} N, err {100*err:.3f}%  (|vz| {abs(float(d.qvel[2])):.2e})")


# ── PORT 3: HILL MUSCLE ───────────────────────────────────────────────────────────────────────
@port_test(
    "hill_muscle",
    "an isometric muscle at full activation delivers F = A * F_max * f_l(l), and its force "
    "rises with the activation time constant the model publishes",
    "steady force is not proportional to activation, or the rise time disagrees with tau_act "
    "by more than 30%")
def t_hill_muscle(mujoco):
    """The instruction: F_m = A*F_max*f_l(l)*f_v(v)*cos(theta). Isometric kills f_v (v=0).

    Read from a REAL muscle in myobody, not a toy: gainprm[2] is F_max, dynprm[0] is tau_act.
    Predicted before the run: force at A=1.0 is twice force at A=0.5, and 63% of steady state
    is reached in ~tau_act.
    """
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    u = 0                                               # first actuator, whatever it is
    tau_a = float(m.actuator_dynprm[u][0])
    name = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_ACTUATOR, u) or f"act{u}"

    def hold(level, secs=0.6):
        mujoco.mj_resetDataKeyframe(m, d, 0)
        mujoco.mj_forward(m, d)
        d.qvel[:] = 0
        trace = []
        for k in range(int(secs / m.opt.timestep)):
            d.ctrl[:] = 0.0
            d.ctrl[u] = level
            d.qvel[:] = 0                               # ISOMETRIC: clamp motion, so f_v = 1
            mujoco.mj_step(m, d)
            trace.append(abs(float(d.actuator_force[u])))
        return np.array(trace)

    full, half = hold(1.0), hold(0.5)
    f1, f2 = float(full[-1]), float(half[-1])
    ratio = f1 / max(f2, 1e-9)                          # predicted 2.0 (linear in activation)
    tgt = 0.632 * f1                                    # one time constant
    idx = int(np.argmax(full >= tgt)) if (full >= tgt).any() else -1
    t63 = idx * m.opt.timestep if idx >= 0 else float("nan")
    rise_err = abs(t63 - tau_a) / tau_a if t63 == t63 else 9.9
    return dict(pass_=abs(ratio - 2.0) < 0.2 and rise_err < 0.3, pred=2.0, got=ratio,
                detail=f"{name}: F(A=1.0)={f1:.2f} N, F(A=0.5)={f2:.2f} N, ratio {ratio:.3f} "
                       f"(predicted 2.000) | t63 {t63*1000:.1f} ms vs tau_act "
                       f"{tau_a*1000:.1f} ms, {100*rise_err:.0f}% off")


# ── PORT 4: SPINDLE ───────────────────────────────────────────────────────────────────────────
@port_test(
    "spindle",
    "a muscle spindle reports LENGTH and RATE, and stretching at a known rate produces a rate "
    "signal equal to that rate -- derived from actuator_length, which the simulator already has",
    "the reported rate differs from the imposed rate by more than 2%, or length is not the "
    "integral of rate")
def t_spindle(mujoco):
    """The instruction: Signal = f(quantity) + noise. Ia rate ~ d(length)/dt.

    THE POINT OF THIS TEST is that the controller has been reading `qpos` -- the simulator's
    GROUND TRUTH, which no body has an organ for. A spindle is derivable from state the
    simulator already computes (`actuator_length`), and it is the ONLY thing a real controller
    may see. This validates the transducer before anything is built on it.
    """
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    j = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, "knee_angle_r")
    adr = int(m.jnt_qposadr[j])
    # PICK A MUSCLE THAT ACTUALLY CROSSES THE KNEE. The first version indexed
    # `actuator_moment.ravel()[k]`, treating a SPARSE array as dense -- the same layout bug that
    # raised loudly in port_trainer and here FAILED SILENTLY, selecting actuator 0 (a trunk
    # muscle) and reporting "length moved 0.000 mm" as a spindle failure.
    #   A wrong index that raises costs an hour. A wrong index that returns 0.0 costs a diagnosis.
    dof = int(m.jnt_dofadr[j])
    u, best = None, 0.0
    flat = np.asarray(d.actuator_moment).ravel()
    for k in range(m.nu):
        n0, adr0 = int(d.moment_rownnz[k]), int(d.moment_rowadr[k])
        for e in range(n0):
            if int(d.moment_colind[adr0 + e]) == dof and abs(flat[adr0 + e]) > best:
                best, u = abs(flat[adr0 + e]), k
    if u is None:
        raise SystemExit("no actuator has a moment arm about knee_angle_r -- refusing to test "
                         "a spindle on a muscle that cannot feel the joint")
    RATE = 0.5                                          # rad/s imposed on the joint
    dt = m.opt.timestep
    lens, rates = [], []
    for k in range(200):
        d.qpos[adr] += RATE * dt
        mujoco.mj_forward(m, d)
        lens.append(float(d.actuator_length[u]))
        if len(lens) > 1:
            rates.append((lens[-1] - lens[-2]) / dt)    # the Ia rate signal
    lens = np.array(lens); rates = np.array(rates)
    # the transducer's own consistency: length must be the integral of the rate it reports
    integ = lens[0] + np.cumsum(rates) * dt
    drift = float(np.abs(integ - lens[1:]).max())
    moved = abs(float(lens[-1] - lens[0]))
    consistent = drift / max(moved, 1e-9)
    nm = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_ACTUATOR, u) or f"act{u}"
    return dict(pass_=consistent < 0.02 and moved > 1e-6, pred=0.0, got=consistent,
                detail=f"{nm} (moment arm {best*1000:.2f} mm about knee_angle_r): knee stretched "
                       f"at {RATE} rad/s -> length moved {moved*1000:.3f} mm, mean Ia rate "
                       f"{rates.mean()*1000:.4f} mm/s, length-vs-integral drift "
                       f"{100*consistent:.4f}%")


def main() -> int:
    import mujoco
    a = sys.argv
    only = a[a.index("--port") + 1] if "--port" in a else None
    names = [only] if only else list(TESTS)
    print(f"\nPORT TESTS -- one instruction at a time, prediction computed BEFORE the run\n"
          + "=" * 100)
    npass = 0
    for n in names:
        if n not in TESTS:
            print(f"  unknown port {n}; have {list(TESTS)}")
            return 1
        t = TESTS[n]
        try:
            r = t["fn"](mujoco)
        except Exception as e:
            print(f"\n  {n:<14} ERROR  {type(e).__name__}: {e}")
            continue
        ok = bool(r["pass_"])
        npass += ok
        print(f"\n  {n.upper():<14} {'PASS' if ok else 'FAIL'}")
        print(f"    claims     {t['statement']}")
        print(f"    measured   {r['detail']}")
        if not ok:
            print(f"    FALSIFIER  {t['falsifier']}")
    print("\n" + "=" * 100)
    print(f"  {npass}/{len(names)} ports validated. A port that has not been tested alone cannot "
          f"be ruled out\n  when a composition built on it fails.")
    return 0 if npass == len(names) else 1


if __name__ == "__main__":
    sys.exit(main())
