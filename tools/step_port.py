"""step_port.py -- THE STEP: MOVE as STEP + PLANT + STAND, the walk's second theory.

RULE 0 lives in `docs/THE_STEP.md`, stated 2026-08-04 before this file was built, after the
first theory's falsifier 3 FIRED (`walk_port.py` LEDGER, third entry: STAND + one rhythm, six
numbers, 3,000+ rollouts, never travel AND upright in one body). This module is that membrane's
program:

    STANCE -- the leg carries; the FROZEN stand formula cages the inverted pendulum over it.
    SWING  -- the leg unloads and is driven by effort at hip/knee/ankle through the measured
              muscle groups, never a commanded angle (the operator's control law: command the
              process and its stop condition, never the final position).
    PLANT  -- the touch sensor's rising edge IS stance onset (`plantar_pressure` validated those
              sensors read 0.000000 lifted).

NO SINUSOID IS INJECTED. The limit cycle is PLANT -> unload -> SWING -> PLANT through the
sensors; periodicity is an OUTPUT the judge measures, not an input this program plays back.

THE INTERLOCK IS THE DOOR, NOT A CHECK. The only way into swing is the CONTRALATERAL foot's
contact rising edge. A leg therefore cannot swing while the other foot is airborne -- duty
factor > 0.5 (theHuman publishes 0.6027) is the mechanism's output, not a rule bolted on.

THE ONLY TRAINED NUMBERS ARE SIX SWING EFFORTS: an A (early-swing, flexion) and a B (late-swing,
extension) amplitude for hip, knee, ankle. The switch from A to B happens at half of the DERIVED
swing window -- (1 - duty_factor) * stride, theHuman's own numbers, closure-checked here against
the compound pendulum `a_swing` validated. Cadence, antiphase and the interlock are derived and
are NOT in the search (rule 1: a searched cadence is the question "which number is best").

LEDGER -- this module's own record, newest last. Each entry states what was measured.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from world import load_body                                   # noqa: E402
from stand_port import derive_stand_port, MYOBODY             # noqa: E402
from walk_port import derive_walk_port, muscle_groups, OSC_JOINTS  # noqa: E402

# SIX FREE NUMBERS, and only six: [A_hip, A_knee, A_ankle, B_hip, B_knee, B_ankle].
# A is early-swing flexion effort, B is late-swing extension (reach-and-prepare-to-plant).
# Everything else -- the window, the antiphase, the interlock -- is derived below.
N_FREE = 2 * len(OSC_JOINTS)


def derive_step_port() -> dict:
    """TheHuman's gait numbers in (via the walk port, whose speed closure already ran);
    the swing window out. Nothing chosen.

    THE WINDOW IS NOT THE CADENCE -- that is why no gate sits on the pendulum comparison.
    Transitions in this port are sensor events, so the gait's timing comes from the body and
    the ground. The window decides only when the effort profile switches from A to B inside a
    swing; a mis-set window shifts that switch, which the six efforts can partly absorb. So the
    pendulum half-period is REPORTED beside the duty-derived window (closure, the way walk_port
    closure-checks speed) as a published cross-check between two membranes -- theHuman's duty
    factor and the body's own inertia -- not as a refusal condition. If they ever disagree by an
    order of magnitude, the discrepancy is the finding, and it will be visible in the printout.
    """
    P = derive_walk_port()
    port = dict(P)
    port["OUT swing_window_s"] = (1.0 - float(P["OUT duty_factor"])) * float(P["OUT stride_s"])
    return port


def pendulum_half_period(m, d, mujoco, g, side="r") -> float:
    """The unloaded leg's passive swing duration, from the model's own inertia tensors.

    This is the PREDICTION half of `tools/action_tests.py:a_swing` (whose measured half, the
    braced free-swing run, matched it within that membrane's 15% bar). Copied, not imported,
    because a_swing's prediction lives inside a test harness and reaching into it would couple
    this port to a harness's internals; the derivation is restated here so what it rests on --
    composite rigid body inertia about the hip axis, I = sum_b[a.(R I R').a + m r_perp^2] --
    stays visible.
    """
    j = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, f"hip_flexion_{side}")
    if j < 0:
        raise SystemExit(f"no hip_flexion_{side} in this body -- refusing to derive a swing "
                         f"window for a leg that is absent (rule 20).")
    mujoco.mj_resetDataKeyframe(m, d, 0)
    d.qpos[2] += 1.5                                   # hang it clear of the floor, as a_swing does
    mujoco.mj_forward(m, d)
    hip = np.array(d.xanchor[j])
    axis = np.array(d.xaxis[j]) / np.linalg.norm(d.xaxis[j])
    frag = ("femur_", "patella_", "tibia_", "talus_", "calcn_", "toes_")
    leg = [b for b in range(m.nbody)
           if any(k in (mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, b) or "")
                  for k in [f + side for f in frag])]
    I, m_leg, msum = 0.0, 0.0, np.zeros(3)
    for b in leg:
        R = np.asarray(d.ximat[b]).reshape(3, 3)
        Ib = R @ np.diag(np.asarray(m.body_inertia[b])) @ R.T
        rp = np.array(d.xipos[b]) - hip
        rp = rp - np.dot(rp, axis) * axis
        mb = float(m.body_mass[b])
        I += float(axis @ Ib @ axis) + mb * float(np.dot(rp, rp))
        m_leg += mb
        msum += mb * np.array(d.xipos[b])
    rc = msum / m_leg - hip
    dcm = float(np.linalg.norm(rc - np.dot(rc, axis) * axis))
    T = 2.0 * math.pi * math.sqrt(I / (m_leg * g * dcm))
    return 0.5 * T          # a swing is the pendulum's forward half-cycle


class StepMachine:
    """THE PER-LEG TWO-STATE MACHINE. Its transitions are events the body can OBSERVE.

    A leg enters SWING on exactly one event: the contralateral foot's contact rising edge
    (that foot's PLANT -- it just took the load). A leg enters STANCE on exactly one event: its
    own contact rising edge. There is no clock anywhere in this class; `t` enters only so the
    effort profile knows how far through the DERIVED window the current swing is.

    THE FIRST STEP. Standing, both feet down, somebody must go first and the body decides: the
    leg carrying LESS unloads more easily, so it is released. A tie -- including the sensor
    ablation's cr == cl == 0 -- releases NOTHING: no observable asymmetry, no step. That is not
    a corner case; it is falsifier 2's expected behaviour, built into the mechanism.
    """

    def __init__(self, window_s):
        self.window_s = float(window_s)
        self.state = {"r": "stance", "l": "stance"}
        self.t_in = {"r": 0.0, "l": 0.0}
        self._was = {"r": False, "l": False}
        self._t_last = None
        self._primed = False

    def _enter(self, side, state):
        self.state[side] = state
        self.t_in[side] = 0.0

    def step(self, t, cr, cl):
        """Advance one control tick. Returns (state, phase): phase is t_in/window for a leg in
        swing (it may exceed 1.0 -- a swing that has not landed keeps reaching for the floor;
        the SENSOR ends it, never the window)."""
        dt = 0.0 if self._t_last is None else max(0.0, float(t) - self._t_last)
        self._t_last = float(t)
        loaded = {"r": cr > 0.0, "l": cl > 0.0}
        for s in ("r", "l"):
            self.t_in[s] += dt

        if not self._primed:
            if cr < cl:
                self._enter("r", "swing")
            elif cl < cr:
                self._enter("l", "swing")
            self._primed = self.state["r"] == "swing" or self.state["l"] == "swing"
            self._was = loaded
        else:
            for side, other in (("r", "l"), ("l", "r")):
                edge_own = loaded[side] and not self._was[side]
                edge_other = loaded[other] and not self._was[other]
                if edge_own and self.state[side] == "swing":
                    self._enter(side, "stance")                    # PLANT: the rising edge IS it
                if edge_other and self.state[side] == "stance":
                    # THE INTERLOCK, STRUCTURAL: this branch is the ONLY door into swing, and it
                    # requires the other foot to have just loaded. Both feet airborne -> nobody
                    # can leave stance. Duty > 0.5 is an output; the judge measures it.
                    self._enter(side, "swing")
            self._was = loaded
        phase = {s: (self.t_in[s] / self.window_s if self.state[s] == "swing" else 0.0)
                 for s in ("r", "l")}
        return dict(self.state), phase


def step_formula(theta_stand, theta_step, groups, z, pitch, nu, tgt, state, phase, gain=1.0):
    """THE BUTTON'S CONTENT, v2: the stand formula, plus swing effort where the machine says SWING.

    The stand theta is FROZEN -- composition, not retraining: the 870 numbers that hold the body
    up are reused unchanged and the six swing efforts are the entire difference between standing
    and walking. A stance leg gets the stand formula ALONE (no push-off term in v1: if no travel
    results, that is a measured finding, not a patch opportunity).

    RECIPROCAL BY CONSTRUCTION, same pattern as `walk_formula`: early swing drives a joint's
    flexors +A and its extensors -A (lift and carry); late swing drives flexors -B and extensors
    +B (reach and prepare to plant). A co-contracting pair with the same sign stiffens the joint
    instead of moving it -- the "flailing while rigid" failure the stand port already paid for.
    """
    u = np.clip(theta_stand[:nu] + theta_stand[nu:2 * nu] * (tgt - z)
                + theta_stand[2 * nu:] * pitch, 0.0, 1.0)
    nj = len(OSC_JOINTS)
    for side in ("r", "l"):
        if state[side] != "swing":
            continue
        early = phase[side] < 0.5
        for i, base in enumerate(OSC_JOINTS):
            a = gain * float(theta_step[i if early else nj + i])
            if a == 0.0:
                continue                                   # the ABLATION path, exactly
            flex, ext = groups[f"{base}_{side}"]
            if early:
                u[flex] = np.clip(u[flex] + a, 0.0, 1.0)
                u[ext] = np.clip(u[ext] - a, 0.0, 1.0)
            else:
                u[flex] = np.clip(u[flex] - a, 0.0, 1.0)
                u[ext] = np.clip(u[ext] + a, 0.0, 1.0)
    return u


def move_formula_fn(theta_stand, theta_step, groups, tgt, nu, P, gain=1.0):
    """MOVE, AS A PARSER FORMULA REGISTRATION -- the state machine OWNED by the formula.

    The machine lives in the closure: it is per-parse state, exactly like the phase the v1
    formula derived from obs["t"], except this one's advance is driven by obs["cr"]/obs["cl"] --
    foot contact entering the parse as two more keys in a dict that was free-form by design
    (`tools/parser.py:143`). No grammar change. `sensor_gain` is NOT a parameter of this
    function: the ablation belongs to the harness that feeds obs (zero the keys), so the ablated
    code path and the live code path are the same path.
    """
    machine = StepMachine(P["OUT swing_window_s"])

    def fn(obs, value):
        state, phase = machine.step(obs["t"], float(obs.get("cr", 0.0)),
                                    float(obs.get("cl", 0.0)))
        return step_formula(theta_stand, theta_step, groups, obs["z"], obs["pitch"], nu, tgt,
                            state, phase, gain=gain * float(value))
    fn.machine = machine      # the harness may inspect state; it may not write it
    return fn


if __name__ == "__main__":
    import mujoco
    P = derive_step_port()
    print("\nTHE STEP PORT -- the walk's second theory, derived, nothing chosen")
    print("=" * 78)
    for k in ("OUT stride_s", "OUT duty_factor", "OUT swing_window_s", "OUT target_speed_ms"):
        print(f"  {k:26} {P[k]:.6f}")
    m, g = load_body(MYOBODY, mujoco)
    d = mujoco.MjData(m)
    half = pendulum_half_period(m, d, mujoco, g)
    win = P["OUT swing_window_s"]
    print(f"\n  CLOSURE -- swing window, two membranes cross-checked:")
    print(f"    duty-derived (theHuman):      {win:.4f} s = (1 - {P['OUT duty_factor']:.4f}) "
          f"x {P['OUT stride_s']:.4f}")
    print(f"    pendulum half-period (body):  {half:.4f} s (a_swing's prediction half)")
    print(f"    difference: {100 * abs(half - win) / win:+.1f}% -- REPORTED, not gated: the "
          f"sensors own the cadence, the window only splits the effort profile")
    print(f"\n  {N_FREE} free numbers to train (six swing efforts). The window, the antiphase "
          f"and the interlock are DERIVED and are not among them.")
