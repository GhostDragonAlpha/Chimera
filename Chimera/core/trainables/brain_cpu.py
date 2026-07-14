"""brain_cpu — FIX THE BODY, EVOLVE A BRAIN. On the CPU, because the CPU is enough.

THE ARITHMETIC I SHOULD HAVE DONE BEFORE REACHING FOR A GPU
-----------------------------------------------------------
I claimed a neural controller was "~10^6-10^7 evals and simply out of reach on a CPU".
I never checked. The human did, in effect, by asking whether the GPU was worth it:

    CPU walker, MEASURED:   190 evals/sec
    A 1,744-weight brain needs ~10^5-10^6 evaluations for a GA to converge.

        10^5 evals / 190 per sec  =    9 MINUTES
        10^6 evals / 190 per sec  =  1.5 HOURS      <- an overnight job. There is a Night.

The MLP forward pass (43 -> 32 -> 19, about 2,000 FLOPs) is nothing beside 1,400 steps
of rigid-body physics. It does not measurably slow the sim.

THE NEURAL CONTROLLER WAS ALWAYS AFFORDABLE ON THE CPU. I was solving a throughput
problem that did not exist.

WHAT THE GPU COST, FOR THE RECORD (core/trainables/brain.py + walker_gpu.py)
---------------------------------------------------------------------------
SIX bugs, every one of which presented as an ASYNCHRONOUS CUDA fault rather than an
error that points at itself: add_body-vs-add_link (silently dropped 19 of 20 links);
1,575 CPU<->GPU syncs per batch (300x SLOWER than CPU); self-collision (NaN); a zero
inertia tensor (NaN); SolverFeatherstone NaN-ing in FREE FALL at step 17; and njmax
hard-defaulted to 384 regardless of world count ("illegal memory access" past ~128
worlds). On pybullet NOT ONE of those exists: multibody links do not self-collide,
inertia comes from the shapes, the solver is stable, contacts are managed for you, and
errors are synchronous and in Python where you can read them.

    THE GPU IS A PRODUCTION TOOL, NOT A DEVELOPMENT TOOL.

Development needs fast iteration, legible errors, and the freedom to change everything.
And throughput is NOT the bottleneck here — the OBJECTIVE is. Four exploits in a row
(lollipop, satisficer, outriggers, bristlebot) says so. More compute on a wrong
objective just finds the exploit faster.

WHY A BRAIN AT ALL, THEN
------------------------
The CPG that walked before is an OPEN LOOP. It plays the same rhythm whether the animal
is upright or face-down in the dirt: it cannot feel itself falling, so it cannot catch
itself. That is exactly why the evolved gait was a scramble.

A brain closes the loop. It reads its own body every step:

    16 joint angles      (proprioception — where are my limbs?)
    16 joint velocities  (how fast are they moving?)
     3 up-vector         (which way is up? AM I FALLING?)
     2 clock (sin, cos)  (a rhythm to hang a gait on)
    ----
    37 inputs  ->  32 tanh hidden  ->  16 joint targets      = 1,744 weights

The body is FIXED — the one core.trainables.walker already evolved to move. Only the
nervous system is being asked to exist.

FACTS ONLY. What makes a gait GOOD lives in docs/objectives/brain.json.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

import numpy as np

from core.terrarium import Genome, grow
from core.trainables.walker import (
    DT, SETTLE_STEPS, SIM_STEPS, EVAL_SEED, MAX_LINKS,
    MIN_BONE_LEN, MIN_BONE_RAD, BODY_SIZE_MIN, BODY_SIZE_MAX,
    _build, _client,
)

N_HID = 32
TARGET_AMP = 1.1                 # radians; the brain's output is tanh, so bounded
TORQUE = 22.0                    # N.m ceiling per joint — pybullet caps it for us

ROOT = Path(__file__).resolve().parents[2]
BODY_FILE = ROOT / "docs" / "objectives" / "walker.trained.json"

_BODY = None                     # the fixed skeleton, grown once


def _body_genome() -> dict:
    if BODY_FILE.exists():
        return json.loads(BODY_FILE.read_text(encoding="utf-8"))["genome"]["body"]
    from dataclasses import asdict
    return asdict(Genome.quadruped())


def _bones():
    """The FIXED body. Grown once, reused for every brain, forever."""
    global _BODY
    if _BODY is None:
        b = grow(Genome(**_body_genome()), EVAL_SEED)
        pts = [x.p0 for x in b] + [x.p1 for x in b]
        size = max(max(q[i] for q in pts) - min(q[i] for q in pts) for i in range(3))
        _BODY = (b, size)
    return _BODY


def shape() -> tuple:
    bones, _ = _bones()
    nj = len(bones) - 1
    n_in = 2 * nj + 5
    return n_in, nj, n_in * N_HID + N_HID + N_HID * nj + nj


# --- genome: a nervous system -------------------------------------------------

def seed() -> dict:
    rng = random.Random(0)
    return {"w": [rng.gauss(0.0, 0.4) for _ in range(shape()[2])]}


def mutate(g: dict, rng: random.Random) -> dict:
    w = list(g["w"])
    # MULTI-SCALE mutation: mostly fine tuning, occasionally a real jump. A single fixed
    # sigma either crawls forever or never converges.
    sigma = rng.choice([0.02, 0.02, 0.06, 0.20])
    rate = rng.choice([0.05, 0.15, 0.40])
    for i in range(len(w)):
        if rng.random() < rate:
            w[i] = max(-5.0, min(5.0, w[i] + rng.gauss(0.0, sigma)))
    return {"w": w}


# --- measure: FACTS about a body that was asked to move -----------------------

def measure(g: dict) -> dict:
    import pybullet as p

    bones, size = _bones()
    nj = len(bones) - 1
    n_in, _, n_params = shape()

    w = np.asarray(g["w"], dtype=np.float64)
    o1 = n_in * N_HID
    W1 = w[:o1].reshape(N_HID, n_in)
    b1 = w[o1:o1 + N_HID]
    o2 = o1 + N_HID
    W2 = w[o2:o2 + N_HID * nj].reshape(nj, N_HID)
    b2 = w[o2 + N_HID * nj:]

    dead = {"exploded": 1.0, "distance": 0.0, "meters": 0.0, "speed": 0.0,
            "straightness": 0.0, "airborne_frac": 1.0, "torso_z": 0.0,
            "energy": 999.0, "bones": float(len(bones))}

    c = _client()
    p.resetSimulation(physicsClientId=c)
    p.setGravity(0, 0, -9.81, physicsClientId=c)
    p.setTimeStep(DT, physicsClientId=c)
    gid = p.createMultiBody(0, p.createCollisionShape(p.GEOM_PLANE, physicsClientId=c),
                            physicsClientId=c)
    p.changeDynamics(gid, -1, lateralFriction=1.0, physicsClientId=c)

    zmin = min(min(b.p0[2], b.p1[2]) for b in bones)
    try:
        uid = _build(p, c, bones, lift=-zmin + 0.05)
    except Exception:
        return dead
    if p.getNumJoints(uid, physicsClientId=c) != nj:
        return dead
    for j in range(nj):
        p.changeDynamics(uid, j, lateralFriction=1.2, physicsClientId=c)
    p.changeDynamics(uid, -1, lateralFriction=1.2, physicsClientId=c)

    for _ in range(SETTLE_STEPS):
        p.stepSimulation(physicsClientId=c)

    start = p.getBasePositionAndOrientation(uid, physicsClientId=c)[0]
    if not all(math.isfinite(x) for x in start):
        return dead

    prev, path, airborne, zsum, energy, samples = start, 0.0, 0, 0.0, 0.0, 0
    obs = np.empty(n_in)
    JOINTS = list(range(nj))
    FORCES = [TORQUE] * nj

    for step in range(SIM_STEPS):
        # ---- PROPRIOCEPTION: the animal reads its own body -------------------
        st = p.getJointStates(uid, list(range(nj)), physicsClientId=c)
        for j in range(nj):
            obs[j] = st[j][0]                       # joint angle
            obs[nj + j] = st[j][1] * 0.1            # joint velocity
        _, orn = p.getBasePositionAndOrientation(uid, physicsClientId=c)
        m = p.getMatrixFromQuaternion(orn)
        obs[2 * nj + 0] = m[2]                      # the body's own up-vector:
        obs[2 * nj + 1] = m[5]                      # THIS is what a CPG cannot know,
        obs[2 * nj + 2] = m[8]                      # and why it cannot catch itself
        t = step * DT
        obs[2 * nj + 3] = math.sin(6.2831853 * t)
        obs[2 * nj + 4] = math.cos(6.2831853 * t)

        # ---- THE BRAIN -------------------------------------------------------
        act = np.tanh(W2 @ np.tanh(W1 @ obs + b1) + b2) * TARGET_AMP

        # ONE call, not nj of them. setJointMotorControl2 per joint costs 33.9 us/step;
        # setJointMotorControlArray costs 3.6 us — 9x cheaper on that line, and the
        # trained brain replays to 13.50 body lengths either way, so it is FREE.
        #
        # It is the ONLY free win here. I also tried halving the physics rate (240 -> 120
        # Hz), which looked like a 2-5x saving — and it DESTROYED the result: the same
        # brain drops from 13.50 body lengths to 4.62. A coarser timestep changes contact
        # and friction, AND the brain's control loop runs at the physics rate, so at 120 Hz
        # it makes half as many decisions per second and its control bandwidth halves.
        # THE 240 Hz BUDGET IS NOT WASTE. IT IS LOAD-BEARING. Shipping that "optimisation"
        # would have silently changed the science and cost a week of confusion.
        p.setJointMotorControlArray(uid, JOINTS, p.POSITION_CONTROL,
                                    targetPositions=[float(x) for x in act],
                                    forces=FORCES, physicsClientId=c)
        p.stepSimulation(physicsClientId=c)

        if step % 8 == 0:
            pos = p.getBasePositionAndOrientation(uid, physicsClientId=c)[0]
            if not all(math.isfinite(x) for x in pos) or abs(pos[2]) > 40.0:
                return dead
            path += math.dist(pos[:2], prev[:2])
            prev = pos
            zsum += pos[2]
            if not p.getContactPoints(bodyA=uid, bodyB=gid, physicsClientId=c):
                airborne += 1
            for j in range(nj):
                energy += abs(st[j][3] * st[j][1]) * DT * 8
            samples += 1

    end = p.getBasePositionAndOrientation(uid, physicsClientId=c)[0]
    if not all(math.isfinite(x) for x in end):
        return dead

    net = math.dist(end[:2], start[:2])
    return {
        "exploded": 0.0,
        "distance": net / size,
        "meters": net,
        "speed": (net / size) / (SIM_STEPS * DT),
        "straightness": net / max(path, 1e-6),
        "airborne_frac": airborne / max(samples, 1),
        "torso_z": (zsum / max(samples, 1)) / size,
        "energy": energy / max(size, 1e-6),
        "bones": float(len(bones)),
    }
