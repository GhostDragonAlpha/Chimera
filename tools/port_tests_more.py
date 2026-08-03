"""port_tests_more.py -- ports 5-12, registering into the same harness as port_tests.py.

A separate module rather than a longer file, and the split is architectural rather than tidy:
adding an instruction to the set must not touch the file that runs them. `@port_test` registers
into the shared TESTS registry and refuses anything without a statement, a prediction and a
falsifier.

    5  joint limit        q_min <= q <= q_max, enforced not advisory
    6  passive force      tau_passive grows toward the stop
    7  tendon elasticity  F_t = k_t*(l_t - l_slack), at ZERO activation
    8  force-velocity     f_v(v) < 1 shortening -- the half the isometric test could not see
    9  GTO                Signal = f(force), monotone
    10 otolith            g in HEAD coordinates: g*sin(theta), g*cos(theta)
    11 plantar pressure   the four sensors myobody actually has
    12 phase oscillator   dphi/dt = omega + eps*sin(phi_other - phi), omega DERIVED

Run through the harness: `python tools/port_tests.py`
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body, gravity
from port_registry import port_test, MYOBODY


def _muscle_at(m, d, mujoco, joint_name):
    """The actuator with the largest moment arm about a joint, read through the SPARSE index.

    Written once because doing it inline is where the dense-reshape bug got in: it returned 0.0
    for a trunk muscle and was reported as a spindle failure. This REFUSES rather than defaulting.
    """
    j = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, joint_name)
    dof = int(m.jnt_dofadr[j])
    mujoco.mj_forward(m, d)
    flat = np.asarray(d.actuator_moment).ravel()
    u, best = None, 0.0
    for k in range(m.nu):
        n0, adr0 = int(d.moment_rownnz[k]), int(d.moment_rowadr[k])
        for e in range(n0):
            if int(d.moment_colind[adr0 + e]) == dof and abs(flat[adr0 + e]) > best:
                best, u = abs(flat[adr0 + e]), k
    if u is None:
        raise SystemExit(f"no actuator has a moment arm about {joint_name} -- refusing to test "
                         f"a muscle port on a muscle that cannot feel the joint")
    return j, int(m.jnt_qposadr[j]), dof, u, best


@port_test(
    "joint_limit",
    "a joint driven hard past its published range stops AT the range -- q_min <= q <= q_max is "
    "enforced by the constraint solver, not advisory",
    "the joint exceeds its published limit by more than 2 degrees under sustained drive")
def t_joint_limit(mujoco):
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    j, adr, dof, _, _ = _muscle_at(m, d, mujoco, "knee_angle_r")
    hi = float(m.jnt_range[j][1])
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    for _ in range(1000):
        d.ctrl[:] = 0.0
        d.qfrc_applied[:] = 0.0
        d.qfrc_applied[dof] = 400.0
        mujoco.mj_step(m, d)
    q = float(d.qpos[adr])
    over = max(0.0, q - hi)
    return dict(pass_=math.degrees(over) < 2.0, pred=hi, got=q,
                detail=f"knee driven at 400 N.m for 1 s: limit {math.degrees(hi):+.1f} deg, "
                       f"reached {math.degrees(q):+.1f} deg, overshoot {math.degrees(over):.3f} deg")


@port_test(
    "passive_force",
    "with every actuator silent the body still generates passive joint force -- ligament and "
    "tissue resistance -- and it GROWS as the joint is pushed toward its stop",
    "passive force is identically zero, or does not grow between 10% and 90% of the range")
def t_passive_force(mujoco):
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    j, adr, dof, _, _ = _muscle_at(m, d, mujoco, "knee_angle_r")
    lo, hi = float(m.jnt_range[j][0]), float(m.jnt_range[j][1])
    # READ BOTH ARRAYS. `qfrc_passive` carries joint springs, dampers and TENDON springs; MuJoCo
    # files a MUSCLE's passive force under `qfrc_actuator`. Reading only the first, this test could
    # not have seen tissue the body already had -- it happened to be right that myobody has no
    # ligament, but it was right for a reason it could not check. The measured muscle passive term
    # is 1.8 / -1.9 / 3.2 N.m and non-monotone, where a knee gives tens of N.m rising to the stop.
    #
    # `act` is zeroed as well as `ctrl` because ctrl is EXCITATION and the force reads `act`, a
    # state with 15 ms dynamics (port 3). This keyframe happens to store act = 0 so it changes
    # nothing here -- it is a guard against the day a test forwards once on a LOADED pose.
    out = []
    for frac in (0.1, 0.5, 0.9):
        mujoco.mj_resetDataKeyframe(m, d, 0)
        d.ctrl[:] = 0.0
        if m.na:
            d.act[:] = 0.0
        d.qpos[adr] = lo + frac * (hi - lo)
        d.qvel[:] = 0.0
        mujoco.mj_forward(m, d)
        out.append(abs(float(d.qfrc_passive[dof]) + float(d.qfrc_actuator[dof])))
    grows = out[2] > out[0] and max(out) > 1e-9
    return dict(pass_=grows, pred=0.0, got=out[2],
                detail=f"knee passive force at 10/50/90% of range: {out[0]:.5f} / {out[1]:.5f} / "
                       f"{out[2]:.5f} N.m ({'grows toward the stop' if grows else 'DOES NOT GROW'})")


@port_test(
    "tendon_elasticity",
    "a muscle-tendon unit stretched with NO activation develops force -- the series elastic "
    "element, F_t = k_t*(l_t - l_slack)",
    "a fully stretched, completely unactivated unit develops no force, meaning no series elastic")
def t_tendon(mujoco):
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    j, adr, dof, u, _ = _muscle_at(m, d, mujoco, "knee_angle_r")
    lo, hi = float(m.jnt_range[j][0]), float(m.jnt_range[j][1])
    F, L = [], []
    for frac in (0.05, 0.95):
        mujoco.mj_resetDataKeyframe(m, d, 0)
        d.ctrl[:] = 0.0                                   # ZERO ACTIVATION throughout
        d.qpos[adr] = lo + frac * (hi - lo)
        d.qvel[:] = 0.0
        mujoco.mj_forward(m, d)
        L.append(float(d.actuator_length[u]))
        F.append(abs(float(d.actuator_force[u])))
    dl, dF = abs(L[1] - L[0]), abs(F[1] - F[0])
    nm = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_ACTUATOR, u) or f"act{u}"
    return dict(pass_=dF > 1e-6 and dl > 1e-6, pred=0.0, got=dF,
                detail=f"{nm} at ZERO activation: length {L[0]*1000:.2f} -> {L[1]*1000:.2f} mm "
                       f"(d {dl*1000:.2f} mm), force {F[0]:.5f} -> {F[1]:.5f} N "
                       f"({'series elastic present' if dF > 1e-6 else 'NO SERIES ELASTIC'})")


@port_test(
    "force_velocity",
    "a SHORTENING muscle makes less force than an isometric one at the same activation, f_v < 1. "
    "The isometric test clamped qvel and so set f_v = 1 BY CONSTRUCTION -- it could not have seen "
    "this term at all",
    "a shortening muscle makes the same or more force than isometric, meaning f_v is absent")
def t_force_velocity(mujoco):
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    j, adr, dof, u, arm = _muscle_at(m, d, mujoco, "knee_angle_r")

    def force_at(rate):
        mujoco.mj_resetDataKeyframe(m, d, 0)
        mujoco.mj_forward(m, d)
        f = []
        for k in range(160):
            d.ctrl[:] = 0.0
            d.ctrl[u] = 1.0
            d.qvel[:] = 0.0
            d.qvel[dof] = rate
            mujoco.mj_step(m, d)
            if k > 110:
                f.append(abs(float(d.actuator_force[u])))
        return float(np.mean(f))

    iso = force_at(0.0)
    a = force_at(+3.0)
    b = force_at(-3.0)
    short = min(a, b)                                     # whichever direction SHORTENS it
    nm = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_ACTUATOR, u) or f"act{u}"
    return dict(pass_=short < iso * 0.98, pred=iso, got=short,
                detail=f"{nm} at A=1.0: isometric {iso:.3f} N | +3 rad/s {a:.3f} | -3 rad/s "
                       f"{b:.3f} -> f_v = {short/max(iso,1e-9):.4f} "
                       f"({'force-velocity present' if short < iso*0.98 else 'NO f_v TERM'})")


@port_test(
    "gto",
    "a Golgi tendon organ measures muscle-tendon FORCE: its signal is monotone in activation",
    "the signal is not monotone in the force it exists to measure")
def t_gto(mujoco):
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    _, _, _, u, _ = _muscle_at(m, d, mujoco, "knee_angle_r")
    sig = []
    for A in (0.0, 0.25, 0.5, 0.75, 1.0):
        mujoco.mj_resetDataKeyframe(m, d, 0)
        mujoco.mj_forward(m, d)
        for _ in range(400):
            d.ctrl[:] = 0.0
            d.ctrl[u] = A
            d.qvel[:] = 0.0
            mujoco.mj_step(m, d)
        sig.append(abs(float(d.actuator_force[u])))
    mono = all(sig[i + 1] >= sig[i] - 1e-9 for i in range(len(sig) - 1))
    span = sig[-1] - sig[0]
    nm = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_ACTUATOR, u) or f"act{u}"
    return dict(pass_=mono and span > 1e-3, pred=0.0, got=span,
                detail=f"{nm} GTO across A = 0/.25/.5/.75/1: "
                       + " ".join(f"{s:.2f}" for s in sig)
                       + f" N ({'monotone' if mono else 'NOT MONOTONE'})")


@port_test(
    "otolith",
    "an otolith measures the GRAVITY VECTOR IN HEAD COORDINATES: tilt by theta and the lateral "
    "component reads g*sin(theta), the vertical g*cos(theta). Derived from the head's own "
    "rotation, which is the only thing an organ could have access to",
    "the components do not match g*sin/g*cos to 1%, or the reading is in the WORLD frame -- which "
    "would be a god's-eye view rather than an organ")
def t_otolith(mujoco):
    g = gravity()
    THETA = math.radians(20.0)
    pred_lat, pred_up = g * math.sin(THETA), g * math.cos(THETA)   # BEFORE the model is built
    xml = (f'<mujoco><option timestep="0.001" gravity="0 0 -{g}"/><worldbody>'
           f'<body name="head" pos="0 0 1" euler="0 {math.degrees(THETA)} 0">'
           f'<geom type="sphere" size="0.1" density="1000"/></body></worldbody></mujoco>')
    m = mujoco.MjModel.from_xml_string(xml)
    d = mujoco.MjData(m)
    mujoco.mj_forward(m, d)
    i = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "head")
    R = np.array(d.xmat[i]).reshape(3, 3)
    g_head = R.T @ np.array([0.0, 0.0, -g])               # THE OTOLITH SIGNAL
    lat, up = abs(float(g_head[0])), abs(float(g_head[2]))
    e1 = abs(lat - pred_lat) / max(pred_lat, 1e-9)
    e2 = abs(up - pred_up) / max(pred_up, 1e-9)
    return dict(pass_=e1 < 0.01 and e2 < 0.01, pred=pred_lat, got=lat,
                detail=f"head tilted {math.degrees(THETA):.0f} deg: lateral {lat:.4f} m/s2 "
                       f"(predicted {pred_lat:.4f}, {100*e1:.4f}% off), vertical {up:.4f} "
                       f"(predicted {pred_up:.4f}, {100*e2:.4f}% off)")


@port_test(
    "plantar_pressure",
    "the touch sensors under the feet -- the ONLY sensors myobody defines -- read nonzero when "
    "the body rests on the ground and zero when it is lifted clear",
    "the sensors read the same airborne as loaded, i.e. they discriminate nothing")
def t_plantar(mujoco):
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    if m.nsensor == 0:
        raise SystemExit("no sensors in the model -- refusing to test a transducer that is absent")
    mujoco.mj_resetDataKeyframe(m, d, 0)
    mujoco.mj_forward(m, d)
    for _ in range(4000):
        d.ctrl[:] = 0.0
        mujoco.mj_step(m, d)
    loaded = float(np.sum(np.abs(d.sensordata)))
    d.qpos[2] += 3.0
    d.qvel[:] = 0.0
    mujoco.mj_forward(m, d)
    airborne = float(np.sum(np.abs(d.sensordata)))
    weight = float(sum(m.body_mass)) * g
    ok = loaded > 1e-9 and airborne < max(loaded * 0.01, 1e-12)
    return dict(pass_=ok, pred=weight, got=loaded,
                detail=f"{m.nsensor} touch sensors: resting total {loaded:.4f}, lifted "
                       f"{airborne:.6f} (body weight {weight:.1f} N) "
                       f"({'discriminates contact' if ok else 'NO DISCRIMINATION'})")


@port_test(
    "phase_oscillator",
    "two coupled oscillators started in ANTIPHASE converge; an uncoupled pair does not. "
    "omega is DERIVED from theHuman's own stride, not chosen",
    "the coupled pair fails to converge, or the UNCOUPLED control converges anyway -- which would "
    "mean the coupling term is doing nothing and the test proves nothing")
def t_phase_oscillator(mujoco):
    L = json.loads([q for q in (ROOT / "story").rglob("numbers.json")
                    if q.parent.name == "theHuman"][0].read_text(encoding="utf8"))
    stride = 2.0 * float(L["step_time_s"])
    omega = 2.0 * math.pi / stride
    dt, T = 0.001, 20.0

    def run(eps):
        a, b = 0.0, math.pi                               # ANTIPHASE start
        for _ in range(int(T / dt)):
            da = omega + eps * math.sin(b - a)
            db = omega + eps * math.sin(a - b)
            a, b = a + da * dt, b + db * dt
        return abs((b - a + math.pi) % (2 * math.pi) - math.pi)

    coupled, uncoupled = run(2.0), run(0.0)
    return dict(pass_=coupled < 0.05 and uncoupled > 3.0, pred=0.0, got=coupled,
                detail=f"omega {omega:.4f} rad/s from theHuman's {stride:.4f} s stride | antiphase "
                       f"start: coupled(eps=2) -> {coupled:.2e} rad, uncoupled(eps=0) -> "
                       f"{uncoupled:.4f} rad "
                       f"({'coupling does the work' if uncoupled > 3.0 else 'CONTROL FAILED'})")
