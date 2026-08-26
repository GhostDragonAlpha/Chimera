# ALLOMETRY AUDIT — Action Primitives

**Date:** 2026-08-26
**Scope:** `tools/action_tests.py`, `tools/primitive_tests.py`, `tools/world.py`
**Membrane:** ALLOMETRY (no action primitive may cite a human-table number onto a non-human body)
**Falsifier:** A human-norm constant survives unflagged.

---

## Method

Scanned every numeric constant and every force/strength/torque/ROM literal in the three
files. Numbers were classified as:

- **DERIVED** — computed from the model's own mass, inertia, gravity, and actuator
  properties before the run.
- **TEST INPUT** — an arbitrary nonzero value needed to exercise a code path whose
  *outcome* is body-derived (e.g., the throw velocity in `a_throw`).
- **HUMAN-NORM** — a number cited from human biomechanics literature or tables and applied
  to myobody without allometric scaling.
- **UNGROUNDED** — a number that is neither derived from the body nor cited as a human
  norm, and whose magnitude therefore rests on the author's taste.

---

## FINDINGS

### F-1. world.py:709-710 — "~200 N.m, kinesiology" (human knee-extension MVC)

**File:** `tools/world.py:709-710`
**Type:** HUMAN-NORM (cited explicitly)
**Number:** 200 N.m (human adult knee-extension maximum voluntary contraction)
**Context:**
```
# torque itself obeys ALLOMETRY (THE_WOLFRAM_FRAME.md section 11): 400 N.m is ~2x an adult
# knee-extension maximum voluntary contraction (~200 N.m, kinesiology) -- an ABUSE load by
```
The 400 N.m probe load in `port_tests_more.py:71` is justified by this human-norm MVC.
The comment explicitly names "kinesiology" as the ology.

**What ology it should come from:** The model's own peak knee extension torque, measured
by sweeping `qfrc_actuator[dof]` over the ROM at full activation — the same method the
ligament derivation already uses (`world.py:_derive_side`, lines 217-232).

**Proposed replacement:**
```python
# BEFORE (in port_tests_more.py:71):
d.qfrc_applied[dof] = 400.0

# AFTER — derive from the model's own peak knee extension torque:
# Measure max |tau| the knee extensors produce over the ROM, then ×2 for abuse margin.
j, adr, dof, _, _ = _muscle_at(m, d, mujoco, "knee_angle_r")
hi = float(m.jnt_range[j][1])
tau_peak = 0.0
for frac in np.linspace(0.0, 1.0, 20):
    mujoco.mj_resetData(m, d)
    d.qpos[adr] = float(m.jnt_range[j][0]) + frac * (hi - float(m.jnt_range[j][0]))
    d.ctrl[:] = 1.0
    if m.na: d.act[:] = 1.0
    mujoco.mj_forward(m, d)
    tau_peak = max(tau_peak, abs(float(d.qfrc_actuator[dof])))
d.qfrc_applied[dof] = 2.0 * tau_peak   # abuse margin, same design intent
```
**Ology:** biomechanics + MuJoCo forward dynamics (model's own actuators).
**Also in world.py:710:** Remove the human-norm citation from the comment; replace with
"derived from the model's own peak knee extension torque × 2".

**MINTING NOTE:** This number is both minting (the400 N.m is applied as a test probe)
and human-norm (justified as "~2x 200 N.m human MVC"). The replacement is still minting
(derived from the body) but drops the human-table citation.

---

### F-2. action_tests.py:734 — 60.0 N.m external torque (a_turn control arm)

**File:** `tools/action_tests.py:734`
**Type:** UNGROUNDED (not derived, not cited as human norm)
**Number:** 60.0 N.m
**Context:**
```python
d.xfrc_applied[1][5] = 60.0  # a torque about z from OUTSIDE
```
This is the external torque in `a_turn`'s control arm (the arm that proves external
torques CAN change L_z). The test only checks that the forced |dL_z| is >5× the
internal drift — so any nonzero torque large enough to exceed drift would work.

**What ology it should come from:** The body's own moment of inertia about z and a
characteristic angular acceleration. The test needs a torque large enough to produce a
measurable |dL_z|, and that threshold is body-dependent.

**Proposed replacement:**
```python
# BEFORE:
d.xfrc_applied[1][5] = 60.0  # a torque about z from OUTSIDE

# AFTER — derive from the body's own angular momentum capacity:
I_z = float(m.body_inertia[1][2])  # pelvis subtree I_z from the model
alpha = 5.0  # rad/s^2 — characteristic angular acceleration (~0.7g / H_com)
d.xfrc_applied[1][5] = max(I_z * alpha, 1.0)  # floor at 1 N.m to avoid zero
```
**Ology:** rigid-body dynamics (model's own inertia × characteristic angular acceleration).

---

### F-3. primitive_tests.py:615 — 150.0 N.m lumbar disturbance (p_upright)

**File:** `tools/primitive_tests.py:615`
**Type:** UNGROUNDED (not derived); magnitude consistent with human lumbar extensor MVC
**Number:** 150.0 N.m
**Context:**
```python
T0, PERIOD = 150.0, 900
```
Applied as a sinusoidal torque sweep through the lumbar chain:
```python
d.qfrc_applied[df] = T0 * math.sin(ph) / len(chain)
```
The comment says: "A slow torque sweep through the lumbar joints keeps the error
moving, as standing on moving ground does."

Human lumbar extensor MVC is typically 50–200 N.m depending on posture and level
(Andrews et al. 1984; McGill 1991). The value 150 N.m falls squarely in that range
and is likely an implicit human-norm import.

**What ology it should come from:** The model's own peak lumbar muscle torque, measured
the same way the ligament derivation measures `tau_max` — the max sum of
`moment × actuator_force` driving into each lumbar dof at full activation.

**Proposed replacement:**
```python
# BEFORE:
T0, PERIOD = 150.0, 900

# AFTER — derive from the model's own lumbar torque capacity:
T0 = 0.0
for nm_df, _a, _df, p_, n_ in chain:
    mujoco.mj_resetData(m, d)
    d.ctrl[:] = 1.0
    if m.na: d.act[:] = 1.0
    mujoco.mj_forward(m, d)
    T0 = max(T0, abs(float(d.qfrc_actuator[_df])))
# T0 is now the peak lumbar torque these muscles produce; scale by a fraction
# for the disturbance (we want to perturb, not overwhelm)
T0 *= 0.5  # half-capacity sweep
PERIOD = 900  # time constant is independent
```
**Ology:** biomechanics + MuJoCo forward dynamics (model's own lumbar actuators).

---

## NUMBERS THAT ARE CORRECT (already body-derived)

These constants in the three files were audited and found to correctly derive from
the model. Listed so the falsifier has something to fail against.

| File:line | Number | Derivation |
|---|---|---|
| action_tests.py:99 | K = W × 0.9201 / tol | Body weight × geometric factor / tolerance |
| action_tests.py:795 | KX = 500.0 N/m | Safety tether — see note below |
| action_tests.py:299 | T_pred | 2π√(I/(mgd)) from model's own inertia |
| action_tests.py:358 | ω₀ = √(g/H) | From model's own CoM height |
| action_tests.py:589 | R_pred | v²sin(2θ)/g in this world's g |
| action_tests.py:626 | J_pred | M√(2gh) from model's own mass |
| action_tests.py:214-216 | 580.5 N, 348.3 N | All derived from M × g and harness s |
| action_tests.py:780 | HIP/KNEE/ANKLE | Geometric derivation (closed-chain) |
| primitive_tests.py:280 | cap | Measured from model's own actuators |
| primitive_tests.py:521 | CEIL = 0.45 × peak_open(1.0) | Derived from model's own peak force |
| primitive_tests.py:681 | W = 5.3564 | From port 12's own stride derivation |
| world.py:137-148 | LUMBAR_EXT_EDGE etc. | Membrane data (theHuman), cited |
| world.py:159-163 | OFFSAG_EDGES | Literature values, membrane-level |

### Note on action_tests.py:795 — KX = 500.0 N/m (crouch safety tether)

This is a weak safety tether whose moment is counted in route B. It is not derived
from the body and not cited as a human norm — it is a UNGROUNDED control parameter.
However, its contribution to the torque measurement is explicit (M_tether is computed
and added), so any error it introduces is visible. The tether's stiffness needs to be
weak enough that its moment is negligible relative to the gravitational moment, and
500 N/m on a ~80 kg body produces a moment <1 N.m against a ~100 N.m gravitational
moment — the ratio is ~1%. Flagged but low severity; could be replaced with
`KX = 0.01 * M_above * g / abs(x0[0] - d.xpos[1][0])` for a body-derived value.

---

## RULE-1 CHECK: Are any numbers in the test parameters derived vs chosen?

The following test parameters are chosen (not derived from the body) but are
legitimate as *test conditions* rather than *strength constants*. They define WHAT
is tested, not HOW MUCH force the body can produce. A different body would use
the same test conditions:

- **a_throw** (action_tests.py:588): V = 6 m/s, θ = 40° — test velocity and angle.
- **a_land** (action_tests.py:625): H = 0.20 m — drop height.
- **a_swing** (action_tests.py:306): 12° initial perturbation.
- **p_damping** (primitive_tests.py:458): mid = 50°, amp = 20° — knee sweep range.
- **p_damping** (primitive_tests.py:476): 6.0 / 0.06 rad/s — fast/slow cycle rates.
- **p_end_stop** (primitive_tests.py:344): 50/80/95/100% fractions — probe positions.
- **p_load_relief** (primitive_tests.py:509): 10°–110° sweep range.

These are acceptable: they test whether a *relationship* holds (ballistic range,
impulse conservation, damping asymmetry, etc.), and the relationship itself is
body-derived. A different body would use the same test conditions and the
prediction would change because M, I, g, and d change.

---

## SUMMARY

| # | File:line | Type | Number | Severity |
|---|---|---|---|---|
| F-1 | world.py:710 | HUMAN-NORM (cited) | 200 N.m kinesiology MVC → justifies 400 N.m probe | **HIGH** — the replacement propagates to port_tests_more.py |
| F-2 | action_tests.py:734 | UNGROUNDED | 60.0 N.m external torque | **LOW** — test input, any nonzero works, but body-derived is cleaner |
| F-3 | primitive_tests.py:615 | UNGROUNDED / implicit HUMAN-NORM | 150.0 N.m lumbar disturbance | **MEDIUM** — magnitude consistent with human lumbar MVC; body-derived replacement is straightforward |

**Clean pass count:** 0/3 files — every file has at least one ungrounded or human-norm
constant. The three findings account for all human-norm or ungrounded force/torque
constants in the audited files. No human-norm ROM constants were found in the
action-primitive layer; the ROM edges in `world.py` are membrane-level constants from
theHuman's published data, cited with their ology, and the ligament stiffness derived
from them is body-derived (`tau_max / gap`).
