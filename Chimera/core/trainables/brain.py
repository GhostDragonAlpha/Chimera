"""brain — FIX THE BODY, EVOLVE A BRAIN. Thousands of nervous systems, one GPU kernel.

    *** STATUS 2026-07-14: THE BODY STANDS ON THE GPU. THE BRAIN KERNELS DO NOT RUN. ***
    *** DO NOT TRAIN ON THIS YET. core.trainables.walker (CPU) is the working walker. ***

    WHAT WORKS, VERIFIED:
      The fixed body falls, settles and STANDS under MuJoCo-Warp on the 4090, in N
      separate worlds, built ONCE. That took five real bugs (all fixed, all documented
      at their site): add_body->add_link; 1,575 CPU<->GPU syncs -> a Warp kernel;
      self-collision -> negative collision_group; zero inertia -> mass from shape
      density; and SolverFeatherstone NaN-ing in FREE FALL at step 17 -> SolverMuJoCo
      with add_world() and separate_worlds=True.

    WHAT DOES NOT:
      Launching the three brain kernels (gather / layer1 / layer2) produces
      `CUDA error 700: an illegal memory access`. CUDA errors are ASYNCHRONOUS, so it
      surfaces during the next sync (in wp_free_device_async) and LOOKS like a teardown
      bug. It is not. It is an out-of-bounds write in one of these kernels, and the
      settle-only test never caught it because settling does not launch them.

      NEXT STEP: dump model.state().joint_q.shape, joint_qd.shape and
      control.joint_target_q.shape at n_env=1024 and check they are EXACTLY
      n_env * (7 + nj), n_env * (6 + nj), n_env * (6 + nj). The strides qs/qds/ts are
      computed by integer division from those shapes, so if MuJoCo's separate-worlds
      layout differs by even one element, every index in every kernel is wrong. Run
      once under `wp.config.verify_cuda = True` to get the fault at the launch that
      causes it rather than at the next sync.

      The weight indexing has been checked by hand and is in bounds
      (n_params = 1744 = 37*32 + 32 + 32*16 + 16; max index touched = 1743).

This is the regime where a GPU actually wins, and the previous run proved why it has to
be this one.

    MORPHOLOGY on GPU (core/trainables/walker_gpu.py):  9 evals/sec.  IT LOSES.
        Because the body changes every generation, the entire physics model must be
        REBUILT IN PYTHON every generation — 40,960 add_link/add_shape/add_joint calls
        for a population of 2048. No kernel can amortise a Python for-loop.

    CONTROL on GPU (this module):
        The body is FIXED, so the model is built ONCE at startup and reused for every
        generation forever. The only thing that differs between individuals is a flat
        vector of ~2,000 weights — one wp.array upload. Everything else lives on the
        device and never comes back.

        GPU FOR CONTROL. CPU FOR MORPHOLOGY. That is the rule, and it is measured.

THE CONTROLLER IS A NERVOUS SYSTEM, NOT A METRONOME
---------------------------------------------------
The CPG that walked before is an open loop: it plays the same rhythm whether the animal
is upright or face-down in the dirt. It cannot feel itself falling, so it cannot catch
itself. That is why the evolved gait was a scramble.

A brain closes the loop. It reads its own body every single step:

    19 joint angles      (proprioception — where are my limbs?)
    19 joint velocities  (how fast are they moving?)
     3 up-vector         (which way is up? am I falling?)
     2 clock (sin, cos)  (a rhythm to hang a gait on)
    ----
    43 inputs  ->  32 tanh hidden  ->  19 joint targets      = 2,035 weights

Two Warp kernels per step (input->hidden, hidden->output), each a 2D launch over
(environment, unit). Every creature's forward pass happens in the same kernel as every
other creature's. Nothing returns to the CPU inside the episode.

FACTS ONLY. What makes a gait GOOD lives in docs/objectives/brain.json.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

from core.terrarium import Genome, grow
from core.trainables.walker import (
    DT, SETTLE_STEPS, SIM_STEPS, EVAL_SEED, MIN_BONE_RAD,
)
from core.trainables.walker_gpu import _add_creature, SPACING, GRID, _init_warp

N_HID = 32
TARGET_AMP = 1.1                 # radians. The brain's output is tanh, so bounded.
SPRING_KE, SPRING_KD = 160.0, 9.0

ROOT = Path(__file__).resolve().parents[2]
BODY_FILE = ROOT / "docs" / "objectives" / "walker.trained.json"

_GYM = None                      # THE POINT: built once, reused for every generation.


# --- the fixed body -----------------------------------------------------------

def _body() -> dict:
    """The body we already evolved to move (core.trainables.walker). It is KNOWN
    VIABLE — 17 bones, honest mass, and it travels 6.8 body lengths on a CPG. Now we
    hold it still and grow a nervous system for it."""
    if BODY_FILE.exists():
        return json.loads(BODY_FILE.read_text(encoding="utf-8"))["genome"]["body"]
    from dataclasses import asdict
    return asdict(Genome.quadruped())


# --- the gym: ONE model, N identical bodies, N different brains ----------------

class Gym:
    def __init__(self, n_env: int):
        _init_warp()
        import warp as wp
        import newton
        import numpy as np
        from newton.solvers import SolverMuJoCo

        # SolverMuJoCo, NOT SolverFeatherstone. Featherstone NaN'd this articulation in
        # FREE FALL at step 17 — no ground, no control, just gravity — because the chain
        # has 100:1 mass ratios between links and it is inverting the articulated inertia.
        #
        # MuJoCo was ruled out for MORPHOLOGY because its batching demands every world be
        # STRUCTURALLY IDENTICAL, and evolving bodies means every creature differs. But
        # HERE THE BODY IS FIXED. Every one of the N worlds is the same body, identical by
        # construction. The constraint that disqualified MuJoCo is the exact thing this
        # experiment removes — so the solver we could not use is now both the most robust
        # AND the fastest one available.
        self.wp, self.np, self.n_env = wp, np, n_env
        bones = grow(Genome(**_body()), EVAL_SEED)
        self.bones = bones
        self.nj = len(bones) - 1                       # revolute joints

        pts = [b.p0 for b in bones] + [b.p1 for b in bones]
        self.size = max(max(q[i] for q in pts) - min(q[i] for q in pts)
                        for i in range(3))

        builder = newton.ModelBuilder()
        builder.add_ground_plane()
        one = newton.ModelBuilder()
        root, links, _ = _add_creature(newton, wp, one, bones)
        # add_world(), NOT add_builder(). SolverMuJoCo(separate_worlds=True) requires each
        # creature to live in its OWN world — add_builder drops them all into the global
        # world (-1), which MuJoCo rejects outright ("Global world (-1) cannot contain
        # bodies"). And separate worlds are strictly better here: creatures in different
        # worlds CANNOT collide with each other, so the 30 m spacing grid the morphology
        # run needed is simply unnecessary. Every brain runs the same body at the same
        # origin, in its own private universe.
        self.roots, self.links = [], []
        for e in range(n_env):
            base = builder.body_count
            builder.add_world(one)
            self.roots.append(base + root)
            self.links.append([base + x for x in links])

        self.model = builder.finalize(device="cuda:0")
        self.solver = SolverMuJoCo(self.model, separate_worlds=True)
        self.control = self.model.control()

        # per-env strides in the flat generalized-coordinate arrays
        s = self.model.state()
        self.qs = s.joint_q.shape[0] // n_env          # 7 (free) + nj
        self.qds = s.joint_qd.shape[0] // n_env        # 6 (free) + nj
        self.ts = self.control.joint_target_q.shape[0] // n_env

        self.n_in = 2 * self.nj + 5
        self.n_out = self.nj
        self.n_params = (self.n_in * N_HID + N_HID) + (N_HID * self.n_out + self.n_out)

        self.obs = wp.zeros((n_env, self.n_in), dtype=wp.float32, device="cuda:0")
        self.hid = wp.zeros((n_env, N_HID), dtype=wp.float32, device="cuda:0")
        self.w = wp.zeros((n_env, self.n_params), dtype=wp.float32, device="cuda:0")
        self._kernels()

    # --- the brain, on the device --------------------------------------------
    def _kernels(self):
        wp = self.wp

        @wp.kernel
        def gather(jq: wp.array(dtype=wp.float32), jqd: wp.array(dtype=wp.float32),
                   qs: wp.int32, qds: wp.int32, nj: wp.int32, t: wp.float32,
                   obs: wp.array2d(dtype=wp.float32)):
            e = wp.tid()
            bq = e * qs
            bd = e * qds
            for j in range(nj):
                obs[e, j] = jq[bq + 7 + j]                 # joint ANGLE
                obs[e, nj + j] = jqd[bd + 6 + j] * 0.1     # joint VELOCITY
            # the root quaternion -> which way is UP. This is what a CPG cannot know.
            qx = jq[bq + 3]
            qy = jq[bq + 4]
            qz = jq[bq + 5]
            qw = jq[bq + 6]
            obs[e, 2 * nj + 0] = 2.0 * (qx * qz + qw * qy)
            obs[e, 2 * nj + 1] = 2.0 * (qy * qz - qw * qx)
            obs[e, 2 * nj + 2] = 1.0 - 2.0 * (qx * qx + qy * qy)
            obs[e, 2 * nj + 3] = wp.sin(6.2831853 * t)     # a clock to hang a gait on
            obs[e, 2 * nj + 4] = wp.cos(6.2831853 * t)

        @wp.kernel
        def layer1(obs: wp.array2d(dtype=wp.float32), w: wp.array2d(dtype=wp.float32),
                   n_in: wp.int32, hid: wp.array2d(dtype=wp.float32)):
            e, h = wp.tid()
            acc = w[e, n_in * 32 + h]                      # bias
            for i in range(n_in):
                acc += w[e, h * n_in + i] * obs[e, i]
            hid[e, h] = wp.tanh(acc)

        @wp.kernel
        def layer2(hid: wp.array2d(dtype=wp.float32), w: wp.array2d(dtype=wp.float32),
                   n_in: wp.int32, n_out: wp.int32, ts: wp.int32, amp: wp.float32,
                   target: wp.array(dtype=wp.float32)):
            e, j = wp.tid()
            off = n_in * 32 + 32
            acc = w[e, off + n_out * 32 + j]               # bias
            for h in range(32):
                acc += w[e, off + j * 32 + h] * hid[e, h]
            target[e * ts + 6 + j] = amp * wp.tanh(acc)    # skip the free joint's dofs

        self.k_gather, self.k_l1, self.k_l2 = gather, layer1, layer2

    # --- one generation -------------------------------------------------------
    def run(self, weights):
        wp, np = self.wp, self.np
        self.w.assign(np.ascontiguousarray(weights, dtype=np.float32))

        s0, s1 = self.model.state(), self.model.state()
        self.control.clear()

        for _ in range(SETTLE_STEPS):
            self.solver.step(s0, s1, self.control, self.model.collide(s0), DT)
            s0, s1 = s1, s0

        q0 = s0.body_q.numpy()
        prev = q0
        path = np.zeros(self.n_env)
        air = np.zeros(self.n_env)
        zsum = np.zeros(self.n_env)
        samples = 0

        for step in range(SIM_STEPS):
            t = wp.float32(step * DT)
            wp.launch(self.k_gather, dim=self.n_env, device="cuda:0",
                      inputs=[s0.joint_q, s0.joint_qd, self.qs, self.qds, self.nj, t],
                      outputs=[self.obs])
            wp.launch(self.k_l1, dim=(self.n_env, N_HID), device="cuda:0",
                      inputs=[self.obs, self.w, self.n_in], outputs=[self.hid])
            wp.launch(self.k_l2, dim=(self.n_env, self.n_out), device="cuda:0",
                      inputs=[self.hid, self.w, self.n_in, self.n_out, self.ts,
                              wp.float32(TARGET_AMP)],
                      outputs=[self.control.joint_target_q])

            self.solver.step(s0, s1, self.control, self.model.collide(s0), DT)
            s0, s1 = s1, s0

            if step % 70 == 0:
                q = s0.body_q.numpy()
                for e in range(self.n_env):
                    r = self.roots[e]
                    path[e] += math.dist(q[r][:2], prev[r][:2])
                    zsum[e] += float(q[r][2])
                    if min(float(q[l][2]) for l in self.links[e]) > 0.35:
                        air[e] += 1
                prev = q
                samples += 1

        q1 = s0.body_q.numpy()
        out = []
        for e in range(self.n_env):
            r = self.roots[e]
            ex, sx = q1[r], q0[r]
            if not all(math.isfinite(float(v)) for v in ex[:3]) or abs(float(ex[2])) > 40:
                out.append({"exploded": 1.0, "distance": 0.0, "meters": 0.0,
                            "straightness": 0.0, "airborne_frac": 1.0,
                            "torso_z": 0.0, "bones": float(len(self.bones))})
                continue
            net = math.dist([float(ex[0]), float(ex[1])],
                            [float(sx[0]), float(sx[1])])
            out.append({
                "exploded": 0.0,
                "distance": net / self.size,
                "meters": net,
                "straightness": net / max(float(path[e]), 1e-6),
                "airborne_frac": float(air[e]) / max(samples, 1),
                "torso_z": (float(zsum[e]) / max(samples, 1)) / self.size,
                "bones": float(len(self.bones)),
            })
        return out


def _gym(n: int) -> Gym:
    """Built ONCE. This single line is why the GPU wins here and lost on morphology."""
    global _GYM
    if _GYM is None or _GYM.n_env != n:
        _GYM = Gym(n)
    return _GYM


# --- the trainable protocol ---------------------------------------------------

def shape() -> tuple:
    """(n_in, n_joints, n_params) — computed from the body, WITHOUT building a physics
    model. Standing up a whole Newton Model just to count weights would be absurd."""
    bones = grow(Genome(**_body()), EVAL_SEED)
    nj = len(bones) - 1
    n_in = 2 * nj + 5
    return n_in, nj, n_in * N_HID + N_HID + N_HID * nj + nj


def seed() -> dict:
    rng = random.Random(0)
    return {"w": [rng.gauss(0.0, 0.35) for _ in range(shape()[2])]}


def mutate(g: dict, rng: random.Random) -> dict:
    w = list(g["w"])
    sigma = rng.choice([0.02, 0.08, 0.25])       # multi-scale: fine tweaks and big jumps
    for i in range(len(w)):
        if rng.random() < 0.15:
            w[i] = max(-4.0, min(4.0, w[i] + rng.gauss(0.0, sigma)))
    return {"w": w}


def measure_batch(genomes: list) -> list:
    import numpy as np
    g = _gym(len(genomes))
    W = np.array([x["w"] for x in genomes], dtype=np.float32)
    return g.run(W)


def measure(g: dict) -> dict:
    return measure_batch([g])[0]
