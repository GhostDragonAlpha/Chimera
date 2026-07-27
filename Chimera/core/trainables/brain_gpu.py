"""brain_gpu — the SAME brain, the SAME body, but evaluated HONESTLY.

WHY THIS FILE EXISTS (it is not "brain_cpu but faster")
------------------------------------------------------
On 2026-07-14 we proved the pybullet result was not a gait at all:

    gait.py       periodicity 0.25  -> no repeating cycle exists
    converge.py   start z + 1 MICRON -> 13.52 body lengths becomes 8.01
                  solver iters 50->800 -> 13.5 / 5.4 / 4.0 / 10.5 / 14.2, never settling

That is chaos. There is no attractor, therefore no limit cycle, therefore NO GAIT. The GA
had been selecting LUCKY DICE: every genome got exactly ONE rollout from ONE exact pose,
so "fitness" was decided by which side of a chaotic bifurcation the creature fell on. The
13.52 body lengths was a coin that came up heads once, and the brain had learned to mine
the numerical mush of a solver that never converges (50/50 iterations used, residual 0.2).

THE FIX IS NOT A BETTER OBJECTIVE. IT IS AN HONEST EVALUATION:

    Score every genome from N_RESTARTS randomized starts. Keep the WORST.
    A lucky roll cannot survive sixteen of them.

That costs 16x the compute per genome. The CPU cannot afford it (32 hours/run, 8 P-cores
at thermal limit). A GPU does not notice (58 minutes, 1.5 of 24 GiB, card idling at 39C).
And pybullet CANNOT use a GPU — Bullet has been promising OpenCL physics on its own forums
since 2006, and the 2022 Quickstart Guide still writes it in the future tense.

    THE CORRECT EVALUATION IS WHAT THE CPU CANNOT AFFORD AND THE GPU DOES FOR FREE.
    That is a CORRECTNESS argument. The 33.7x is a side effect.

MEASURED, RTX 4090, 1,400-step rollouts of this exact 17-bone creature:

    pybullet CPU      70 evals/sec   (30 processes, 8 P-cores pinned)
    mujoco-warp    2,358 evals/sec   (16,384 worlds in 6.95 s)

THE ONE RULE OF THIS FILE
-------------------------
NOTHING READS BACK FROM THE GPU INSIDE THE ROLLOUT LOOP. Not the observation, not the
brain, not the accumulators. The previous GPU attempt did 1,575 CPU<->GPU syncs per batch
and came out 300x SLOWER THAN THE CPU. The brain is three Warp kernels; every measurement
is accumulated into device arrays; there is exactly ONE transfer, after the last step.

The genome is IDENTICAL to brain_cpu's (imported, not re-declared), so a brain can be
carried between the two backends and cross-examined. They are not the same physics — they
are two different witnesses to the same creature, and disagreement between them is
information, not a bug.

FACTS ONLY. What makes a gait GOOD lives in docs/objectives/brain_gpu.json.
"""

from __future__ import annotations

import math
import random

import numpy as np

from core import mjcf
from core.trainables.brain_cpu import N_HID, TARGET_AMP, _bones, mutate, seed, shape
from core.trainables.walker import DT, SETTLE_STEPS, SIM_STEPS

# --- the honest-evaluation dial -----------------------------------------------
N_RESTARTS = 16          # randomized initial conditions per genome. THE ANTI-LOTTERY.
SAMPLE_EVERY = 2         # contact sampling stride; 8 was far too coarse to see a stride
CONTACT_EPS = 0.006      # m. A bone is "down" if its lowest point is within 6 mm.

NJMAX, NCONMAX = 192, 64  # PER WORLD. Measured max: 48 rows, 9 contacts. Not a guess.

# Perturbations. We PROVED 1e-6 m matters, so these are enormous by comparison — any
# genome that survives them is not surviving on luck.
P_Z = 0.02               # m, uniform  [0, P_Z]
P_JOINT = 0.03           # rad, gaussian, per joint
P_TILT = 0.02            # rad, gaussian, roll/pitch/yaw

_MODEL = None
_wp = None


def _warp():
    global _wp
    if _wp is None:
        import warp as wp
        wp.init()
        _wp = wp
    return _wp


def _model():
    """The fixed body, as MuJoCo sees it. Built once, reused for every brain forever."""
    global _MODEL
    if _MODEL is None:
        import mujoco
        bones, size = _bones()
        zmin = min(min(b.p0[2], b.p1[2]) for b in bones)
        xml = mjcf.from_bones(bones, lift=-zmin + 0.05, dt=DT)
        mjm = mujoco.MjModel.from_xml_string(xml)
        mjcf.check(mjm, len(bones))          # THE CHECK THAT CAN FAIL
        mjd = mujoco.MjData(mjm)
        mujoco.mj_forward(mjm, mjd)
        _MODEL = (mjm, mjd, size, len(bones))
    return _MODEL


# ---------------------------------------------------------------------------
# The brain, as three Warp kernels. One thread per (world, unit) — 16,384 worlds
# x 32 hidden units is half a million threads, which is the only shape a GPU wants.
# ---------------------------------------------------------------------------

def _kernels():
    wp = _warp()
    if getattr(_kernels, "_built", None):
        return _kernels._built

    @wp.kernel
    def k_obs(qpos: wp.array2d(dtype=wp.float32),
              qvel: wp.array2d(dtype=wp.float32),
              xmat: wp.array2d(dtype=wp.mat33f),
              obs: wp.array2d(dtype=wp.float32),
              nj: int, t: float):
        w = wp.tid()
        for j in range(nj):
            obs[w, j] = qpos[w, 7 + j]              # 7 = 3 pos + 4 quat (freejoint)
            obs[w, nj + j] = qvel[w, 6 + j] * 0.1   # 6 = 3 lin + 3 ang
        # The body's own up-vector: the THIRD COLUMN of the root body's rotation.
        # This is what a CPG cannot know, and why it cannot catch itself falling.
        R = xmat[w, 1]                              # body 0 is the world; body 1 is us
        obs[w, 2 * nj + 0] = R[0, 2]
        obs[w, 2 * nj + 1] = R[1, 2]
        obs[w, 2 * nj + 2] = R[2, 2]
        obs[w, 2 * nj + 3] = wp.sin(6.2831853 * t)
        obs[w, 2 * nj + 4] = wp.cos(6.2831853 * t)

    # gidx maps world -> genome EXPLICITLY. Warp's integer-division semantics are not
    # something I am willing to assume in a kernel that silently computes the wrong
    # brain if I get it wrong — a wrong `w / n_restarts` would not raise, it would just
    # drive every creature with somebody else's nervous system.
    @wp.kernel
    def k_hidden(W: wp.array2d(dtype=wp.float32),      # (npop, NPARAM)
                 gidx: wp.array(dtype=wp.int32),
                 obs: wp.array2d(dtype=wp.float32),
                 hid: wp.array2d(dtype=wp.float32),
                 n_in: int):
        w, h = wp.tid()
        g = gidx[w]
        acc = W[g, n_in * N_HID + h]                   # b1[h]
        base = h * n_in
        for i in range(n_in):
            acc += W[g, base + i] * obs[w, i]
        hid[w, h] = wp.tanh(acc)

    @wp.kernel
    def k_out(W: wp.array2d(dtype=wp.float32),
              gidx: wp.array(dtype=wp.int32),
              hid: wp.array2d(dtype=wp.float32),
              ctrl: wp.array2d(dtype=wp.float32),
              n_in: int, nj: int):
        w, j = wp.tid()
        g = gidx[w]
        o2 = n_in * N_HID + N_HID                      # start of W2
        acc = W[g, o2 + N_HID * nj + j]                # b2[j]
        base = o2 + j * N_HID
        for h in range(N_HID):
            acc += W[g, base + h] * hid[w, h]
        ctrl[w, j] = wp.tanh(acc) * TARGET_AMP

    @wp.kernel
    def k_contact(geom_xpos: wp.array2d(dtype=wp.vec3f),
                  geom_xmat: wp.array2d(dtype=wp.mat33f),
                  geom_size: wp.array2d(dtype=wp.vec3f),
                  duty: wp.array2d(dtype=wp.int32),
                  support: wp.array2d(dtype=wp.int32),
                  samp: int, eps: float):
        w, b = wp.tid()                                # b = bone index; geom = b + 1
        g = b + 1
        p = geom_xpos[w, g]
        R = geom_xmat[w, g]
        sz = geom_size[0, g]
        # A MuJoCo capsule's axis is its LOCAL Z, so its world axis is R's third column
        # and the axis's z-component is R[2,2]. The lowest point of the capsule is then
        # centre_z - |axis_z| * half_length - radius. This gives PER-BONE contact for
        # free — which is precisely the footfall matrix a gait diagram is made of.
        low = p[2] - wp.abs(R[2, 2]) * sz[1] - sz[0]
        if low < eps:
            wp.atomic_add(duty, w, b, 1)
            wp.atomic_add(support, w, samp, 1)

    @wp.kernel
    def k_scalar(qpos: wp.array2d(dtype=wp.float32),
                 force: wp.array2d(dtype=wp.float32),
                 vel: wp.array2d(dtype=wp.float32),
                 prev: wp.array2d(dtype=wp.float32),
                 acc: wp.array2d(dtype=wp.float32),   # (nworld,4) path, zsum, energy, dead
                 nj: int, dt: float):
        w = wp.tid()
        x = qpos[w, 0]
        y = qpos[w, 1]
        z = qpos[w, 2]
        # NaN != NaN. Written as three explicit tests rather than one compound `or`,
        # because a mis-parsed short-circuit here would silently stop flagging dead
        # creatures and a NaN body would score like a healthy one.
        bad = float(0.0)
        if x != x:
            bad = 1.0
        if y != y:
            bad = 1.0
        if z != z:
            bad = 1.0
        if wp.abs(z) > 40.0:
            bad = 1.0
        if bad > 0.5:
            acc[w, 3] = 1.0                            # exploded: NaN, or flung to orbit
            return
        dx = x - prev[w, 0]
        dy = y - prev[w, 1]
        acc[w, 0] += wp.sqrt(dx * dx + dy * dy)
        acc[w, 1] += z
        e = float(0.0)
        for j in range(nj):
            e += wp.abs(force[w, j] * vel[w, j])
        acc[w, 2] += e * dt
        prev[w, 0] = x
        prev[w, 1] = y

    _kernels._built = (k_obs, k_hidden, k_out, k_contact, k_scalar)
    return _kernels._built


def _periodicity(support: np.ndarray, dt_s: float, lo=0.15, hi=2.0) -> np.ndarray:
    """Is there a CYCLE in the footfall, or is this noise that happens to travel?

    Batched autocorrelation of the support signal, one row per world. ~1.0 is a
    metronome; ~0.0 is a seizure. THIS IS THE MEASURE THE OBJECTIVE NEVER HAD — nothing
    in brain.json ever rewarded rhythm, so nothing ever stopped the brain from being a
    convulsion with good PR. It scored 0.25.
    """
    x = support.astype(np.float64)
    x -= x.mean(axis=1, keepdims=True)
    n = x.shape[1]
    F = np.fft.rfft(x, n=2 * n, axis=1)
    ac = np.fft.irfft(F * np.conj(F), n=2 * n, axis=1)[:, :n]
    z = ac[:, :1].copy()
    z[z <= 0] = 1e-12
    ac /= z
    klo, khi = max(2, int(lo / dt_s)), min(n - 1, int(hi / dt_s))
    if khi <= klo:
        return np.zeros(len(x))
    return np.clip(ac[:, klo:khi].max(axis=1), 0.0, 1.0)


def measure_batch(genomes: list) -> list:
    """The WHOLE population, every genome from N_RESTARTS starts, in ONE batched rollout.

    Returns one dict of FACTS per genome. Worst-case and mean are BOTH reported — the
    domain does not decide which one matters. That is the objective's job.
    """
    import mujoco
    import mujoco_warp as mjw
    wp = _warp()
    k_obs, k_hidden, k_out, k_contact, k_scalar = _kernels()

    mjm, mjd, size, n_bones = _model()
    npop = len(genomes)
    R = N_RESTARTS
    nworld = npop * R
    nj, nq, nv = mjm.nu, mjm.nq, mjm.nv
    n_in, _, nparam = shape()
    nsamp = SIM_STEPS // SAMPLE_EVERY

    W = np.asarray([g["w"] for g in genomes], dtype=np.float32)     # (npop, nparam)

    # --- the randomized starts. THE ANTI-LOTTERY. -----------------------------
    # Restart 0 of every genome is the CANONICAL pose, so the old single-shot number
    # remains readable and comparable. Restarts 1..R-1 are perturbed by amounts that are
    # gigantic next to the 1e-6 m we proved is already decisive.
    rng = np.random.RandomState(12345)
    q0 = np.tile(np.asarray(mjd.qpos, dtype=np.float32), (nworld, 1))
    for w in range(nworld):
        if w % R == 0:
            continue
        q0[w, 2] += rng.uniform(0.0, P_Z)
        q0[w, 7:7 + nj] += rng.normal(0.0, P_JOINT, size=nj)
        rx, ry, rz = rng.normal(0.0, P_TILT, size=3)
        cx, sx = math.cos(rx / 2), math.sin(rx / 2)
        cy, sy = math.cos(ry / 2), math.sin(ry / 2)
        cz, sz = math.cos(rz / 2), math.sin(rz / 2)
        # MuJoCo quaternion order is (w, x, y, z) — NOT pybullet's (x, y, z, w).
        q0[w, 3] = cx * cy * cz + sx * sy * sz
        q0[w, 4] = sx * cy * cz - cx * sy * sz
        q0[w, 5] = cx * sy * cz + sx * cy * sz
        q0[w, 6] = cx * cy * sz - sx * sy * cz

    m = mjw.put_model(mjm)
    d = mjw.put_data(mjm, mjd, nworld=nworld, njmax=NJMAX, nconmax=NCONMAX)

    d.qpos = wp.array(q0, dtype=wp.float32, ndim=2)
    d.qvel = wp.zeros((nworld, nv), dtype=wp.float32)
    d.ctrl = wp.zeros((nworld, nj), dtype=wp.float32)

    Wd = wp.array(W, dtype=wp.float32, ndim=2)
    gidx = wp.array(np.repeat(np.arange(npop, dtype=np.int32), R), dtype=wp.int32)
    obs = wp.zeros((nworld, n_in), dtype=wp.float32)
    hid = wp.zeros((nworld, N_HID), dtype=wp.float32)
    duty = wp.zeros((nworld, n_bones), dtype=wp.int32)
    support = wp.zeros((nworld, nsamp), dtype=wp.int32)
    prev = wp.zeros((nworld, 2), dtype=wp.float32)
    acc = wp.zeros((nworld, 4), dtype=wp.float32)

    # SETTLE with zero control — the body drops and comes to rest, exactly as it does on
    # the CPU. (Verified: it lands at z=0.011 with 7 stable floor contacts.)
    for _ in range(SETTLE_STEPS):
        mjw.step(m, d)

    start = wp.zeros((nworld, 2), dtype=wp.float32)
    wp.launch(_k_snap(), dim=nworld, inputs=[d.qpos, start])
    wp.launch(_k_snap(), dim=nworld, inputs=[d.qpos, prev])

    dt_s = DT * SAMPLE_EVERY
    for step in range(SIM_STEPS):
        t = step * DT
        wp.launch(k_obs, dim=nworld, inputs=[d.qpos, d.qvel, d.xmat, obs, nj, t])
        wp.launch(k_hidden, dim=(nworld, N_HID), inputs=[Wd, gidx, obs, hid, n_in])
        wp.launch(k_out, dim=(nworld, nj), inputs=[Wd, gidx, hid, d.ctrl, n_in, nj])
        mjw.step(m, d)
        if step % SAMPLE_EVERY == 0:
            s = step // SAMPLE_EVERY
            wp.launch(k_contact, dim=(nworld, n_bones),
                      inputs=[d.geom_xpos, d.geom_xmat, m.geom_size, duty, support,
                              s, CONTACT_EPS])
            wp.launch(k_scalar, dim=nworld,
                      inputs=[d.qpos, d.actuator_force, d.actuator_velocity,
                              prev, acc, nj, dt_s])

    end = wp.zeros((nworld, 2), dtype=wp.float32)
    wp.launch(_k_snap(), dim=nworld, inputs=[d.qpos, end])

    # THE ONLY TRANSFER. One sync, after the last step.
    wp.synchronize()
    A = acc.numpy(); S = support.numpy(); D = duty.numpy()
    st = start.numpy(); en = end.numpy()

    del d, m, Wd, gidx, obs, hid, duty, support, prev, acc, start, end

    # --- per-world facts ------------------------------------------------------
    dead = A[:, 3] > 0.5
    net = np.linalg.norm(en - st, axis=1)
    path = np.maximum(A[:, 0], 1e-6)
    per = _periodicity(S, dt_s)

    dist = net / size
    straight = net / path
    torso = (A[:, 1] / nsamp) / size
    energy = A[:, 2] / max(size, 1e-6)
    airborne = (S == 0).mean(axis=1)
    dutyf = D / float(nsamp)
    feet = (dutyf > 0.03) & (dutyf < 0.92)
    n_feet = feet.sum(axis=1)
    duty_mean = np.where(n_feet > 0, (dutyf * feet).sum(axis=1) / np.maximum(n_feet, 1), 0.0)
    sled = (dutyf >= 0.92).sum(axis=1)
    support_mean = S.mean(axis=1)

    for arr, bad in ((dist, 0.0), (straight, 0.0), (torso, 0.0), (per, 0.0),
                     (duty_mean, 0.0), (support_mean, 0.0)):
        arr[dead] = bad
    airborne[dead] = 1.0
    energy[dead] = 999.0

    # --- fold N_RESTARTS down to ONE verdict per genome -----------------------
    def bad(a):   # worst case: for things we want LOW
        return a.reshape(npop, R).max(axis=1)

    def good(a):  # worst case: for things we want HIGH
        return a.reshape(npop, R).min(axis=1)

    def avg(a):
        return a.reshape(npop, R).mean(axis=1)

    d_mean, d_worst = avg(dist), good(dist)
    out = []
    for i in range(npop):
        out.append({
            "exploded": float(dead.reshape(npop, R)[i].any()),
            # THE HEADLINE, and it is the MEAN over sixteen different starting poses —
            # not one lucky roll.
            "distance": float(d_mean[i]),
            "distance_worst": float(d_worst[i]),
            # ROBUSTNESS: worst / mean. A real limit cycle is ~1.0 (every start converges
            # onto the same gait). A lottery ticket is ~0.0. THIS is the measure that
            # makes chaos unprofitable, and it is the reason this file exists.
            "robustness": float(d_worst[i] / max(d_mean[i], 1e-6)),
            "periodicity": float(good(per)[i]),
            "straightness": float(good(straight)[i]),
            "airborne_frac": float(bad(airborne)[i]),
            "torso_z": float(good(torso)[i]),
            "energy": float(bad(energy)[i]),
            "duty_factor": float(good(duty_mean)[i]),
            "support_mean": float(avg(support_mean)[i]),
            "sleds": float(bad(sled.astype(np.float64))[i]),
            "bones": float(n_bones),
        })
    return out


def _k_snap():
    wp = _warp()
    if getattr(_k_snap, "_k", None) is None:
        @wp.kernel
        def k(qpos: wp.array2d(dtype=wp.float32), out: wp.array2d(dtype=wp.float32)):
            w = wp.tid()
            out[w, 0] = qpos[w, 0]
            out[w, 1] = qpos[w, 1]
        _k_snap._k = k
    return _k_snap._k


def measure(g: dict) -> dict:
    """Single-genome fallback so the trainer's spec-bind probe works. The GPU path is
    measure_batch; this exists so `trainer` can ask the domain what it reports."""
    return measure_batch([g])[0]
