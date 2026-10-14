"""slice_gpu.py — batched Warp GPU port of the TypeB-P2 representative slice.

N independent environments stepped in parallel on one CUDA device. State is
device-resident; the loop performs zero CPU transfers (lane P1 requirement).

Equations are IDENTICAL to slice_cpu_ref.py; every constant comes from
slice_model.py. float32 on device (the tier's training precision); the CPU
float64 reference judges fidelity (probe.py).

Per tick, three kernel launches (forces, springs, integrate) — the plainest
correct batching; kernel-fusion is a later optimization, not a correctness one.
"""
from __future__ import annotations

import numpy as np
import warp as wp

from tools.science_funnel.typeb_gpu.slice_model import (
    DT_F32, N_SUB, F_CAP_MULT_F32, G_EARTH_F32, K_GROUND_F32, C_GROUND_F32,
    M_VERT_F32, INV_M_F32,
)

wp.init()

# kernel-visible constants (Warp cannot close over raw numpy scalars);
# values are the float32 twins from slice_model so both backends agree
_G = wp.constant(wp.float32(float(G_EARTH_F32)))
_FCAP = wp.constant(wp.float32(float(F_CAP_MULT_F32)))
_MV = wp.constant(wp.float32(float(M_VERT_F32)))
_INVM = wp.constant(wp.float32(float(INV_M_F32)))
_KG = wp.constant(wp.float32(float(K_GROUND_F32)))
_CG = wp.constant(wp.float32(float(C_GROUND_F32)))


@wp.kernel
def _forces_contact(
    pos: wp.array(dtype=wp.vec3),
    vel: wp.array(dtype=wp.vec3),
    fx: wp.array(dtype=wp.float32),
    fy: wp.array(dtype=wp.float32),
    fz: wp.array(dtype=wp.float32),
    nv: int,
):
    """Gravity + the engine's penalty ground contact, per vertex."""
    idx = wp.tid()
    p = pos[idx]
    v = vel[idx]
    fy[idx] = -_G * _MV  # gravity
    fx[idx] = wp.float32(0.0)
    fz[idx] = wp.float32(0.0)

    depth = wp.max(wp.float32(0.0), -p[1])
    fc = _KG * depth + _CG * wp.max(wp.float32(0.0), -v[1])
    cap = _FCAP * _MV * _G
    fy[idx] += wp.min(fc, cap)


@wp.kernel
def _springs(
    pos: wp.array(dtype=wp.vec3),
    fx: wp.array(dtype=wp.float32),
    fy: wp.array(dtype=wp.float32),
    fz: wp.array(dtype=wp.float32),
    si: wp.array(dtype=wp.int32),
    sj: wp.array(dtype=wp.int32),
    rest: wp.array(dtype=wp.float32),
    k: wp.array(dtype=wp.float32),
    nv: int,
    ns: int,
):
    """Mass-spring bond forces (membrane edges + glue bonds), atomic per slot."""
    tid = wp.tid()
    env = tid // ns
    s = tid % ns
    i = env * nv + si[s]
    j = env * nv + sj[s]
    d = pos[j] - pos[i]
    ln = wp.length(d)
    if ln > wp.float32(0.0):
        fs = (ln - rest[s]) * k[s] / ln
        wp.atomic_add(fx, i, d[0] * fs)
        wp.atomic_add(fy, i, d[1] * fs)
        wp.atomic_add(fz, i, d[2] * fs)
        wp.atomic_add(fx, j, -d[0] * fs)
        wp.atomic_add(fy, j, -d[1] * fs)
        wp.atomic_add(fz, j, -d[2] * fs)


@wp.kernel
def _integrate(
    pos: wp.array(dtype=wp.vec3),
    vel: wp.array(dtype=wp.vec3),
    fx: wp.array(dtype=wp.float32),
    fy: wp.array(dtype=wp.float32),
    fz: wp.array(dtype=wp.float32),
    dt: wp.float32,
    nv: int,
):
    """Semi-implicit Euler (membrane_tick.cpp:865-867), then zero forces."""
    idx = wp.tid()
    v = vel[idx]
    a = wp.vec3(fx[idx] * _INVM, fy[idx] * _INVM, fz[idx] * _INVM)
    v = v + a * dt
    vel[idx] = v
    pos[idx] = pos[idx] + v * dt
    fx[idx] = wp.float32(0.0)
    fy[idx] = wp.float32(0.0)
    fz[idx] = wp.float32(0.0)


class BatchedSliceSim:
    """Device-resident batched simulator over N environments."""

    def __init__(self, n_envs: int, device: str = "cuda:0"):
        from tools.science_funnel.typeb_gpu.slice_model import build_topology

        topo = build_topology()
        self.n = n_envs
        self.nv = topo["rest_layout"].shape[0]
        self.ns = topo["n_springs"]
        self.device = device

        def dev(a, dtype):
            return wp.array(np.ascontiguousarray(a), dtype=dtype, device=device)

        # shared topology (device-resident once, read by all envs)
        self.si = dev(topo["spring_i"], wp.int32)
        self.sj = dev(topo["spring_j"], wp.int32)
        self.rest = dev(topo["spring_rest"].astype(np.float32), wp.float32)
        self.k = dev(topo["spring_k"].astype(np.float32), wp.float32)

        n = n_envs * self.nv
        self.pos = wp.empty(n, dtype=wp.vec3, device=device)
        self.vel = wp.empty(n, dtype=wp.vec3, device=device)
        self.fx = wp.empty(n, dtype=wp.float32, device=device)
        self.fy = wp.empty(n, dtype=wp.float32, device=device)
        self.fz = wp.empty(n, dtype=wp.float32, device=device)

    def set_state(self, pos: np.ndarray, vel: np.ndarray) -> None:
        """Scatter one (nv,3) init to every env: per-env seeded perturbation is
        applied by the caller over an (N, nv, 3) stack."""
        self.pos.assign(np.ascontiguousarray(pos.reshape(-1, 3).astype(np.float32)))
        self.vel.assign(np.ascontiguousarray(vel.reshape(-1, 3).astype(np.float32)))

    def step(self, dt: float = float(DT_F32), n_sub: int = N_SUB) -> None:
        """One engine tick = n_sub substeps of dt/n_sub (PREREG addendum:
        the bond stiffness requires it; count derived, not tuned)."""
        n, nv, ns = self.n, self.nv, self.ns
        h = np.float32(dt / n_sub)
        for _ in range(n_sub):
            wp.launch(_forces_contact, dim=n * nv,
                      inputs=[self.pos, self.vel, self.fx, self.fy, self.fz, nv],
                      device=self.device)
            wp.launch(_springs, dim=n * ns,
                      inputs=[self.pos, self.fx, self.fy, self.fz,
                              self.si, self.sj, self.rest, self.k, nv, ns],
                      device=self.device)
            wp.launch(_integrate, dim=n * nv,
                      inputs=[self.pos, self.vel, self.fx, self.fy, self.fz, h, nv],
                      device=self.device)

    def run(self, steps: int, dt: float = float(DT_F32)) -> None:
        for _ in range(steps):
            self.step(dt)

    def read_env(self, env: int) -> tuple[np.ndarray, np.ndarray]:
        p = self.pos.numpy()[env * self.nv:(env + 1) * self.nv]
        v = self.vel.numpy()[env * self.nv:(env + 1) * self.nv]
        return p.astype(np.float64), v.astype(np.float64)

    def contact_ever_fired(self) -> bool:
        """A contact fires iff some vertex sat below y=0 during the run is NOT
        recoverable post-hoc; probes re-check via state instead. Kept for API
        parity with the CPU reference."""
        return bool((self.pos.numpy().reshape(self.n, self.nv, 3)[:, :, 1] < 0.0).any())
