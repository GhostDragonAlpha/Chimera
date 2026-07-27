"""mjcf — a bone tree becomes an MJCF model. The whole translation, in one place.

WHY MUJOCO AT ALL (this was not a performance decision)
-------------------------------------------------------
We proved, on 2026-07-14, that the gait evolved under pybullet was not a gait:

  * gait.py           periodicity 0.25 -> there is no repeating cycle
  * converge.py       start height +1 MICRON -> distance falls 13.52 -> 8.01
                      solver iterations 50 -> 800 -> distance wanders 13.5/5.4/4.0/10.5/14.2

That is Lyapunov divergence. There is no attractor, so there is no limit cycle, so there
is no gait — the GA had been selecting LUCKY DICE, because every genome got exactly one
rollout from one exact pose. The brain had learned to mine the numerical error of a
constraint solver that never converges (measured: 50/50 iterations used, residual 0.2).

The fix is not a better objective. The fix is a HONEST EVALUATION: score every genome from
MANY randomized starts and keep the WORST. A lucky roll cannot survive sixteen of them.
That costs 8-16x more compute per genome — which the CPU cannot afford and a GPU does not
notice. And pybullet CANNOT use a GPU: the Bullet forums have been promising OpenCL physics
since 2006, and the 2022 Quickstart Guide still says "We WILL expose Bullet 3.x running on
GPU using OpenCL as well." Sixteen years, future tense.

MEASURED on this box (RTX 4090), 1,400-step rollouts of this exact creature:

    pybullet CPU   ~70 evals/sec   30 processes, 8 P-cores pinned at thermal limit
    mujoco-warp  2,358 evals/sec   16,384 worlds in 6.95s, 1.5 of 24 GiB, GPU at 39C

    33.7x, and the P-cores go idle.

WHAT MUJOCO'S NESTING BUYS (the Newton bugs, deleted rather than fixed)
----------------------------------------------------------------------
MJCF's XML nesting IS the kinematic tree, so most of the six bugs that killed the Newton
attempt cannot be expressed here: there is no add_body-vs-add_link to confuse, MuJoCo
derives mass and inertia from each geom's own volume and density (no zero-inertia NaN),
and its solver does not explode in free fall. When this file was wrong, MuJoCo REFUSED TO
LOAD and named the missing joint. pybullet, given the same malformed tree, silently
dropped the links and simulated a floating capsule for hours.

THREE THINGS HERE ARE LOAD-BEARING. Change them and you change the physics:

  1. SELF-COLLISION IS OFF (contype=1/conaffinity=2 on bones, 2/1 on the floor).
     pybullet's createMultiBody has self-collision OFF by default and MuJoCo has it ON,
     so without this we would be simulating a DIFFERENT CREATURE — measured: 65 contacts
     on a flat plane for a body with about five feet, its own limbs grinding together.

  2. integrator="implicitfast". Plain Euler NaN'd this body at t=3.74s ("huge value in
     QACC at DOF 8"). 35-gram bones driven by stiff position servos is a stiff ODE, and
     explicit Euler is simply the wrong integrator for a stiff ODE. Not a tuning knob.

  3. The hinge axis is cross(parent_dir, own_dir) — the natural FLEXION plane. A knee does
     not hinge sideways. Same construction the pybullet build used, so the body is the
     same body.
"""

from __future__ import annotations

import math

import numpy as np

DENSITY = 800.0
MIN_BONE_RAD = 0.004
JOINT_RANGE = 2.4        # rad
FRICTION = "1.2 0.01 0.001"

# --- THE ACTUATORS -------------------------------------------------------------
# CORRECTED 2026-07-16. This section used to be headed "AND WHY THEY ARE NOT walker.py's"
# and to open "walker.py carries TORQUE = 22 N.m." Both were false, and the falsehood was
# load-bearing: walker.py has NO TORQUE constant — it evolves "torque" as a genome
# parameter (seed 14.0 -> trained 4.79). The 22.0 lived in core/trainables/brain_cpu.py.
#
# So this comment sent the 2026-07-14 audit to an innocent file. mjcf was fixed to 2.0,
# brain_cpu kept 22.0, and the two paths ran 11x apart for two days — until gait.py
# (which replays via brain_cpu) analysed a MuJoCo-trained brain at 11x its training
# torque and reported the studio's only real walker as "NOT A GAIT — thrashing that
# happens to travel". A comment that lies about provenance does not just misinform; it
# aims the repair.
#
# brain_cpu.py now IMPORTS TORQUE from here, so there is one number and it cannot drift.
#
# THE ORIGINAL LESSON STANDS: 22 N.m on this 0.622 kg creature is 35 N.m PER KG. A human
# hip manages about 3. Its 37-gram limbs were being driven by torques that could throw a
# housebrick, and it was never a decision — the number was inherited from the CPG walker
# and never questioned.
#
# MEASURED (actuator_sweep, 2026-07-14), seed brain, 1,400 steps:
#
#     torque  N.m/kg    kp  armature      z max      joint vel
#       22.0    35.4  30.0     0.000   3433.733       4972.15   <- the inherited setting
#       22.0    35.4  30.0     0.001     76.366        151.01
#       22.0    35.4  30.0     0.010      0.657         10.04
#        2.0     3.2   5.0     0.001      0.057          4.28   <- an animal
#
# THE CREATURE WAS BEING FLUNG 3.4 KILOMETRES INTO THE AIR with its joints spinning at
# 4,972 rad/s. This is very probably the DEEPEST cause of the chaos we proved in
# converge.py: pybullet's constraint-based servo merely CONTAINED that violence instead of
# NaN-ing, so instead of an honest explosion we got a body permanently in the BALLISTIC
# regime — and a body that is always in flight has no contact to build a limit cycle out
# of. It could not have walked. MuJoCo did not introduce this failure; it refused to hide
# it.
#
# READ THE UNITS ON THIS TABLE (added 2026-07-16). Every row above is MEASURED IN MUJOCO.
# It does NOT describe the pybullet path, and an agent (me) transposed it there and
# asserted brain_cpu "was running row 1". Measured, same settings, both engines:
#
#     torque 22.0, armature 0.000, MuJoCo   ->  z max 3433.733 m
#     torque 22.0, armature 0.000, pybullet ->  z max     0.271 m     <- 12,000x apart
#
# The "CONTAINED" sentence above is the whole explanation and it was already here. These
# are two different physics, not one physics with two settings — pybullet has no armature
# at all (changeDynamics REJECTS the keyword; verified by invocation). A number lifted out
# of the engine it was measured in is a rumour with a decimal point.
#
# ARMATURE is rotor inertia. Every real geared joint has it, and it is MuJoCo's standard
# cure for stiff servos on light links. Its absence was an omission, not a simplification.
TORQUE = 2.0             # N.m ceiling per joint -> 3.2 N.m/kg, about a human hip
KP = 5.0                 # position-servo gain
ARMATURE = 0.001         # kg.m^2 rotor inertia. Without it, a 37 g bone on a stiff
                         # spring is a numerically vicious object.
JOINT_DAMPING = 0.05


def from_bones(bones, lift: float, dt: float, visual: bool = False) -> str:
    """Bone tree -> MJCF XML. Total, deterministic, and it loses no bones.

    visual=False (the DEFAULT, and what training uses) emits the bare physics model.
    visual=True adds lights, a floor material and a skybox for RENDERING ONLY — MuJoCo
    ignores all of it in the dynamics, so a rendered creature is byte-for-byte the same
    creature that was trained. Kept behind a flag so the training model stays minimal and
    a stray visual asset can never quietly change the physics.
    """
    n = len(bones)

    # RE-PARENT ORPHANS TO THE ROOT, exactly as the pybullet build does with
    # `parents.append(par if par >= 1 else 0)`. A bone whose parent index is invalid is
    # not dropped — it hangs off the base. Miss this and MJCF becomes a FOREST where
    # pybullet had a TREE, and the unattached limbs simply cease to exist.
    raw = [(-1 if i == 0 else (b.parent if (0 <= b.parent < i) else -1))
           for i, b in enumerate(bones)]
    par_of = [(-1 if i == 0 else (raw[i] if raw[i] >= 1 else 0)) for i in range(n)]

    kids = {i: [] for i in range(n)}
    for i in range(1, n):
        kids[par_of[i]].append(i)

    def d_of(b):
        v = np.array([b.p1[0] - b.p0[0], b.p1[1] - b.p0[1], b.p1[2] - b.p0[2]])
        L = max(float(np.linalg.norm(v)), 1e-4)
        return v / L, L

    def emit(i: int, depth: int) -> str:
        b = bones[i]
        if i == 0:
            pos = (b.p0[0], b.p0[1], b.p0[2] + lift)
        else:
            a = bones[par_of[i]].p0
            pos = (b.p0[0] - a[0], b.p0[1] - a[1], b.p0[2] - a[2])
        di, L = d_of(b)
        r = max((b.r0 + b.r1) * 0.5, MIN_BONE_RAD)
        pad = "  " * depth

        if i > 0:
            pd = (d_of(bones[raw[i]])[0] if raw[i] >= 0
                  else np.array([0.0, 0.0, 1.0]))
            ax = np.cross(pd, di)
            m = float(np.linalg.norm(ax))
            ax = ax / m if m > 1e-6 else np.array([0.0, 1.0, 0.0])
        else:
            ax = np.array([0.0, 1.0, 0.0])

        s = f'{pad}<body name="b{i}" pos="{pos[0]:.6f} {pos[1]:.6f} {pos[2]:.6f}">\n'
        if i == 0:
            s += f'{pad}  <freejoint/>\n'
        else:
            s += (f'{pad}  <joint name="j{i}" type="hinge" pos="0 0 0" '
                  f'axis="{ax[0]:.6f} {ax[1]:.6f} {ax[2]:.6f}" '
                  f'range="-{JOINT_RANGE} {JOINT_RANGE}" '
                  f'armature="{ARMATURE}" damping="{JOINT_DAMPING}"/>\n')
        # contype=1/conaffinity=2 on bones, 2/1 on the floor. MuJoCo collides a pair iff
        # (t1 & a2) | (t2 & a1):  bone<->bone = (1&2)|(1&2) = 0  -> NO SELF-COLLISION
        #                         bone<->floor= (1&1)       = 1  -> collides
        s += (f'{pad}  <geom type="capsule" fromto="0 0 0 '
              f'{di[0]*L:.6f} {di[1]*L:.6f} {di[2]*L:.6f}" size="{r:.6f}" '
              f'density="{DENSITY}" friction="{FRICTION}" '
              f'contype="1" conaffinity="2"/>\n')
        for k in kids[i]:
            s += emit(k, depth + 1)
        return s + f'{pad}</body>\n'

    acts = "".join(
        f'    <position joint="j{i}" kp="{KP}" forcerange="-{TORQUE} {TORQUE}"/>\n'
        for i in range(1, n))

    # RENDER DRESSING — visual=True only. None of this touches the dynamics: MuJoCo does
    # not integrate lights or textures, so the rendered creature is the trained creature.
    assets = floor_geom = ""
    if visual:
        assets = (
            '  <asset>\n'
            '    <texture type="skybox" builtin="gradient" rgb1="0.5 0.7 0.9" '
            'rgb2="0.1 0.15 0.25" width="256" height="256"/>\n'
            '    <texture name="grid" type="2d" builtin="checker" '
            'rgb1="0.2 0.24 0.28" rgb2="0.28 0.32 0.36" width="512" height="512"/>\n'
            '    <material name="gridm" texture="grid" texrepeat="24 24" '
            'reflectance="0.1"/>\n'
            '    <material name="bone" rgba="0.85 0.78 0.62 1"/>\n'
            '  </asset>\n')
        lights = ('    <light pos="0 0 6" dir="0 0 -1" directional="true" '
                  'diffuse="0.6 0.6 0.6"/>\n'
                  '    <light pos="3 -3 5" dir="-0.5 0.5 -1" diffuse="0.5 0.5 0.5"/>\n')
        floor_geom = (
            '    <geom name="floor" type="plane" size="200 200 0.1" '
            'friction="1.0 0.01 0.001" contype="2" conaffinity="1" material="gridm"/>\n'
            + lights)
    else:
        floor_geom = (
            '    <geom name="floor" type="plane" size="200 200 0.1" '
            'friction="1.0 0.01 0.001" contype="2" conaffinity="1"/>\n')

    return f"""<mujoco model="creature">
  <option timestep="{dt:.8f}" gravity="0 0 -9.81" integrator="implicitfast"
          cone="pyramidal"/>
{assets}  <worldbody>
{floor_geom}{emit(0, 2)}  </worldbody>
  <actuator>
{acts}  </actuator>
</mujoco>
"""


def check(mjm, n_bones: int) -> None:
    """THE CHECK THAT CAN FAIL. A bad parent index once made pybullet silently drop 19 of
    20 links, and the 'creature' was one floating capsule that nobody noticed for hours.
    A model that loads is not a model that is right. COUNT THE BONES."""
    nu = n_bones - 1
    if mjm.nbody != n_bones + 1:
        raise AssertionError(f"LOST BONES: {mjm.nbody - 1} bodies, expected {n_bones}")
    if mjm.nu != nu:
        raise AssertionError(f"LOST JOINTS: {mjm.nu} actuators, expected {nu}")
    if mjm.nv != 6 + nu:
        raise AssertionError(f"WRONG DOF: nv={mjm.nv}, expected {6 + nu}")
    if not all(m > 0 for m in mjm.body_mass[1:]):
        raise AssertionError("A BONE HAS ZERO MASS")
