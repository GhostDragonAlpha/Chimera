"""walker_gpu — the SAME walker, but the WHOLE POPULATION in ONE GPU kernel.

NVIDIA Newton (github.com/newton-physics/newton, warp-python@nvidia.com) on top of
NVIDIA Warp. CUDA 12.8, RTX 4090, sm_89.

    *** STATUS 2026-07-14: RUNS ON THE GPU. NOT YET CORRECT, NOT YET FAST. ***
    *** DO NOT TRAIN ON THIS. Use core.trainables.walker (CPU) until fixed.  ***

Measured on the first run: 27.4 s for 16 creatures = 0.6 evals/sec — THREE HUNDRED
TIMES SLOWER than the 190/sec CPU path. Two known, named blockers, in priority order:

 1. THE JOINT TOPOLOGY IS WRONG. A 20-bone creature finalises with joint_count=40 and
    joint_dof_count=145. That decomposes as 21 FREE joints (6 dof) + 19 revolute (1 dof)
    = 145. It should be ONE free joint (the root) + 19 revolute = 25 dof. Newton is
    auto-adding a free joint per body somewhere across add_builder/finalize, so the
    creature is NOT articulated the way this module thinks it is. Every number the first
    run produced is therefore meaningless, and reporting a speed-up from it would have
    been exactly the overclaiming this studio exists to catch.

 2. THE CONTROL LOOP IS SYNCHRONISING 1,575 TIMES PER BATCH. Every step this module
    pulls joint_target to numpy, fills it in a PYTHON loop, and pushes it back; every 8
    steps it yanks body_q back to read positions. Each of those is a full CPU<->GPU
    device sync. The physics is fast — the TRANSFERS are strangling it. This is the
    classic GPU anti-pattern and it defeats the entire point.

    THE FIX: the CPG must live ON THE DEVICE. Upload (offset, amp, phase, freq) per
    joint ONCE as wp.arrays, then each step launch a single Warp kernel:

        @wp.kernel
        def cpg(t: float, o: wp.array(dtype=float), a: wp.array(dtype=float),
                ph: wp.array(dtype=float), f: wp.array(dtype=float),
                target: wp.array(dtype=float)):
            j = wp.tid()
            target[j] = o[j] + a[j] * wp.sin(6.2831853 * f[j] * t + ph[j])

    (the antiphase pi is baked into ph at upload). Read body_q back ONLY at start and
    end. Zero per-step transfers.

 3. airborne_frac and energy are STUBBED TO ZERO here. That means the HARD ballistic-
    launch gate (airborne_frac <= 0.40) is UNGATED on this path — a launcher would win.
    Contact read-back from newton.Contacts must be wired before this domain is trusted.

WHY IT IS STILL WORTH FINISHING: see below. The GPU does not make one creature faster;
it makes 50,000 cost what 200 cost. That is the only way a NEURAL controller (~10^6-10^7
evals) ever becomes affordable.

WHAT A GPU IS ACTUALLY FOR HERE
-------------------------------
It does NOT make one creature faster. A 20-link body is tiny; a kernel launch costs
more than the physics. What it does is make FIFTY THOUSAND creatures cost about what
two hundred cost. The parallelism that matters is not INSIDE a creature — it is ACROSS
the population.

    CPU (pybullet, 22 procs)   ~190 evals/sec    ->  200 creatures in ~1.1 s
    GPU (one flat kernel)      the same wall-clock whether it is 200 or 20,000

So you do not use this to run the same experiment faster. You use it to run an
experiment that was previously unaffordable: enormous populations, longer episodes,
and eventually a NEURAL controller instead of a CPG (which needs ~10^6-10^7 evals and
is simply out of reach on a CPU).

WHY NOT SolverMuJoCo
--------------------
Newton wraps MuJoCo-Warp, which is the fastest thing here — but MuJoCo-style batching
requires every world to be STRUCTURALLY IDENTICAL (same nbody, same njnt). Our
creatures have different MORPHOLOGIES; that is the entire point of evolving bodies. So
MuJoCo would force a fixed topology.

Newton's Warp-native solvers (Featherstone, XPBD) run their kernels over FLAT ARRAYS of
bodies, joints and contacts. They do not care that world 7 has 20 links and world 8 has
11. So the whole heterogeneous population goes into ONE Model, spaced out on the ground
so they cannot touch each other, and steps as one kernel.

FACTS ONLY. What makes a walk GOOD lives in docs/objectives/walker.json — the same
objective file the CPU domain uses. The physics backend is an implementation detail;
the SPEC is not.
"""

from __future__ import annotations

import math
import random

from core.terrarium import Genome, grow
from core.trainables.walker import (            # one source of truth for the rules
    DT, SETTLE_STEPS, SIM_STEPS, DENSITY, MAX_LINKS, EVAL_SEED,
    MASS_FLOOR, MIN_BONE_LEN, MIN_BONE_RAD, BODY_SIZE_MIN, BODY_SIZE_MAX,
    seed, mutate, _quat_from_z_to, _perp, _target,
)

SPACING = 30.0          # metres between creatures. Bodies are <= 8 m, so they cannot meet.
GRID = 64               # creatures per row
_READY = False


def _init_warp():
    global _READY
    if not _READY:
        import warp as wp
        wp.init()
        wp.config.quiet = True
        _READY = True


def _skeleton(g: dict):
    """Grow, and reject the degenerate bodies for exactly the reasons walker.py does."""
    bones = grow(Genome(**g["body"]), EVAL_SEED)
    if not (5 <= len(bones) <= MAX_LINKS):
        return None, 0.0
    for b in bones:
        if (math.dist(b.p0, b.p1) < MIN_BONE_LEN
                or (b.r0 + b.r1) * 0.5 < MIN_BONE_RAD):
            return None, 0.0
    pts = [b.p0 for b in bones] + [b.p1 for b in bones]
    size = max(max(q[i] for q in pts) - min(q[i] for q in pts) for i in range(3))
    if not (BODY_SIZE_MIN <= size <= BODY_SIZE_MAX):
        return None, 0.0
    return bones, size


def _add_creature(nt, wp, builder, bones):
    """One bone -> one LINK. One parent -> one revolute joint. One articulation.

    add_link(), NOT add_body(). Newton's own docs: add_body "adds a STAND-ALONE
    FREE-FLOATING rigid body... a single-body articulation WITH A FREE JOINT", while
    add_link "creates a link WITHOUT automatically adding a joint". Using add_body gave
    every bone its own free joint on top of the revolute — a 20-bone creature finalised
    with 21 free joints and 145 dof, so it was not an articulated animal at all. It was
    a bag of loose parts that happened to have hinges.

    Returns (root_link, [link ids], [revolute joint ids])."""
    zmin = min(min(b.p0[2], b.p1[2]) for b in bones)
    lift = -zmin + 0.05

    # NO SELF-COLLISION. Newton's default collision_group is 1 (positive), so every link
    # of a creature collides with every other link of that creature — and adjacent bones
    # OVERLAP AT THE JOINT BY CONSTRUCTION. That is an infinite penetration force on
    # frame one: the whole population NaN'd during SETTLE, before a controller ever ran.
    # A NEGATIVE group does not collide with itself (Bullet convention, which Newton
    # inherits) but still collides with the positive-group ground plane. pybullet gives
    # you this for free on a multibody; Newton does not.
    # MASS COMES FROM THE SHAPE'S DENSITY, NOT FROM mass=. Passing mass= explicitly gave
    # every link a mass and a ZERO INERTIA TENSOR — and Featherstone INVERTS the
    # articulated inertia, so that is a division by zero. The whole population NaN'd
    # during SETTLE, with no controller running at all. Let the capsule compute both its
    # mass and its inertia from its own geometry, which is the only way they can agree.
    # `armature` is the other Featherstone staple: light links on stiff joints are
    # numerically fragile without it.
    cfg = nt.ModelBuilder.ShapeConfig(density=DENSITY, collision_group=-1)

    ids, dirs, lens = [], [], []
    for b in bones:
        v = (b.p1[0] - b.p0[0], b.p1[1] - b.p0[1], b.p1[2] - b.p0[2])
        L = max(math.sqrt(sum(x * x for x in v)), 1e-4)
        d = (v[0] / L, v[1] / L, v[2] / L)
        r = max((b.r0 + b.r1) * 0.5, MIN_BONE_RAD)
        dirs.append(d)
        lens.append(L)

        mid = ((b.p0[0] + b.p1[0]) * 0.5, (b.p0[1] + b.p1[1]) * 0.5,
               (b.p0[2] + b.p1[2]) * 0.5 + lift)
        link = builder.add_link(                       # <-- NOT add_body
            xform=wp.transform(mid, wp.quat_identity()), armature=0.02)
        builder.add_shape_capsule(
            body=link, radius=r, half_height=L * 0.5, cfg=cfg,
            xform=wp.transform((0.0, 0.0, 0.0), wp.quat(*_quat_from_z_to(d))))
        ids.append(link)

    joints = [builder.add_joint_free(child=ids[0])]     # ONE free joint: the root

    for i in range(1, len(bones)):
        b = bones[i]
        par = b.parent if 0 <= b.parent < i else 0
        # the joint sits at this bone's p0, expressed in each link's own COM frame
        pmid = ((bones[par].p0[0] + bones[par].p1[0]) * 0.5,
                (bones[par].p0[1] + bones[par].p1[1]) * 0.5,
                (bones[par].p0[2] + bones[par].p1[2]) * 0.5)
        cmid = ((b.p0[0] + b.p1[0]) * 0.5, (b.p0[1] + b.p1[1]) * 0.5,
                (b.p0[2] + b.p1[2]) * 0.5)
        px = (b.p0[0] - pmid[0], b.p0[1] - pmid[1], b.p0[2] - pmid[2])
        cx = (b.p0[0] - cmid[0], b.p0[1] - cmid[1], b.p0[2] - cmid[2])

        pd, di = dirs[par], dirs[i]
        ax = (pd[1] * di[2] - pd[2] * di[1], pd[2] * di[0] - pd[0] * di[2],
              pd[0] * di[1] - pd[1] * di[0])
        m = math.sqrt(ax[0] ** 2 + ax[1] ** 2 + ax[2] ** 2)
        axis = (ax[0] / m, ax[1] / m, ax[2] / m) if m > 1e-6 else _perp(di)

        joints.append(builder.add_joint_revolute(
            parent=ids[par], child=ids[i],
            parent_xform=wp.transform(px, wp.quat_identity()),
            child_xform=wp.transform(cx, wp.quat_identity()),
            axis=axis, target_ke=140.0, target_kd=8.0))

    builder.add_articulation(joints=joints)            # one creature = one articulation
    return ids[0], ids, joints[1:]                     # root, links, revolute joints


_CPG_KERNEL = None


def _cpg_kernel(wp):
    """THE CONTROL LOOP, ON THE DEVICE. This is the whole difference between a GPU that
    works and a GPU that is strangled by transfers: upload (offset, amp, phase, freq)
    ONCE, then every step is a single kernel launch with a float. Zero per-step
    CPU<->GPU sync. (The antiphase pi for right-side limbs is baked into `ph` at
    upload — the kernel does not need to know an animal has two sides.)"""
    global _CPG_KERNEL
    if _CPG_KERNEL is None:
        @wp.kernel
        def cpg(t: wp.float32,
                dof: wp.array(dtype=wp.int32),
                o: wp.array(dtype=wp.float32), a: wp.array(dtype=wp.float32),
                ph: wp.array(dtype=wp.float32), f: wp.array(dtype=wp.float32),
                target: wp.array(dtype=wp.float32)):
            k = wp.tid()
            target[dof[k]] = o[k] + a[k] * wp.sin(6.2831853 * f[k] * t + ph[k])
        _CPG_KERNEL = cpg
    return _CPG_KERNEL


def measure_batch(genomes: list) -> list:
    """THE WHOLE POPULATION, one Model, one kernel."""
    _init_warp()
    import warp as wp
    import newton
    import numpy as np
    from newton.solvers import SolverFeatherstone

    dead = {"exploded": 1.0, "degenerate": 1.0, "body_size": 0.0, "distance": 0.0,
            "meters": 0.0, "speed": 0.0, "straightness": 0.0, "airborne_frac": 1.0,
            "energy": 0.0, "torso_z": 0.0, "bones": 0.0}

    out = [dict(dead) for _ in genomes]
    builder = newton.ModelBuilder()
    builder.add_ground_plane()

    live = []                       # (gi, root, links, bones, size, genome)
    for gi, g in enumerate(genomes):
        bones, size = _skeleton(g)
        if bones is None:
            continue
        sub = newton.ModelBuilder()
        root, links, _ = _add_creature(newton, wp, sub, bones)
        k = len(live)
        base = builder.body_count
        builder.add_builder(sub, xform=wp.transform(
            ((k % GRID) * SPACING, (k // GRID) * SPACING, 0.0), wp.quat_identity()))
        live.append((gi, base + root, [base + x for x in links], bones, size, g))

    if not live:
        return out

    model = builder.finalize(device="cuda:0")
    solver = SolverFeatherstone(model)
    s0, s1 = model.state(), model.state()
    control = model.control()

    # --- map each revolute joint to its DOF slot in joint_target -----------------
    jtype = model.joint_type.numpy()
    jstart = model.joint_qd_start.numpy()
    rev = [j for j in range(len(jtype))
           if int(jtype[j]) == int(newton.JointType.REVOLUTE)]

    o, a, ph, f, dof = [], [], [], [], []
    r = 0
    for (_, _, _, bones, _, g) in live:
        for j in range(1, len(bones)):
            b = bones[j]
            off, amp, phase = g["cpg"][min(b.depth, len(g["cpg"]) - 1)]
            o.append(off)
            amp_ = amp
            a.append(amp_)
            ph.append(phase + (math.pi if b.p0[0] < 0.0 else 0.0))   # ANTIPHASE, baked in
            f.append(g["freq"])
            dof.append(int(jstart[rev[r]]))
            r += 1

    dev = "cuda:0"
    a_dof = wp.array(np.asarray(dof, dtype=np.int32), dtype=wp.int32, device=dev)
    a_o = wp.array(np.asarray(o, dtype=np.float32), dtype=wp.float32, device=dev)
    a_a = wp.array(np.asarray(a, dtype=np.float32), dtype=wp.float32, device=dev)
    a_ph = wp.array(np.asarray(ph, dtype=np.float32), dtype=wp.float32, device=dev)
    a_f = wp.array(np.asarray(f, dtype=np.float32), dtype=wp.float32, device=dev)
    kern = _cpg_kernel(wp)
    n_rev = len(dof)

    for _ in range(SETTLE_STEPS):
        solver.step(s0, s1, control, model.collide(s0), DT)
        s0, s1 = s1, s0

    def snap():
        return s0.body_q.numpy()

    q0 = snap()
    prev = q0
    path = [0.0] * len(live)
    air = [0] * len(live)
    zsum = [0.0] * len(live)
    samples = 0

    for step in range(SIM_STEPS):
        wp.launch(kern, dim=n_rev, device=dev,
                  inputs=[wp.float32(step * DT), a_dof, a_o, a_a, a_ph, a_f],
                  outputs=[control.joint_target_q])   # Newton 1.3 name
        solver.step(s0, s1, control, model.collide(s0), DT)
        s0, s1 = s1, s0

        if step % 70 == 0:                     # 20 read-backs, not 175
            q = snap()
            for i, (_, root, links, _, _, _) in enumerate(live):
                path[i] += math.dist(q[root][:2], prev[root][:2])
                zsum[i] += float(q[root][2])
                if min(float(q[l][2]) for l in links) > 0.35:
                    air[i] += 1                # every link clear of the floor: airborne
            prev = q
            samples += 1

    q1 = snap()
    for i, (gi, root, links, bones, size, g) in enumerate(live):
        e, s = q1[root], q0[root]
        if not (all(math.isfinite(float(x)) for x in e[:3])
                and abs(float(e[2])) < 40.0):
            continue                                    # exploded: leave it dead
        net = math.dist([float(e[0]), float(e[1])], [float(s[0]), float(s[1])])
        out[gi] = {
            "exploded": 0.0, "degenerate": 0.0,
            "body_size": size,
            "distance": net / size,
            "meters": net,
            "speed": (net / size) / (SIM_STEPS * DT),
            "straightness": net / max(path[i], 1e-6),
            "airborne_frac": air[i] / max(samples, 1),
            "energy": 0.0,                    # not yet read back; the objective's energy
            "torso_z": (zsum[i] / max(samples, 1)) / size,   # term is soft, not a gate
            "bones": float(len(bones)),
        }
    return out


def measure(g: dict) -> dict:
    """Single-genome path, so this domain still satisfies the plain protocol."""
    return measure_batch([g])[0]
