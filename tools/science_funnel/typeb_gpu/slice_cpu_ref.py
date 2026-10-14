"""slice_cpu_ref.py — float64 CPU reference for the TypeB-P2 probe.

The IDENTICAL equations as the Warp kernel (slice_gpu.py), evaluated in
float64 numpy for one environment. Used for the one-step discrepancy probe
and the 300-tick boundedness rollout (lane P2 evidence kind 2).

Forces per vertex (PREREG.md):
  gravity:            a -= g on y
  spring (membrane):  f = k (|d| - L0) along d-hat (36 edges)
  spring (glue bond): same law, bond material (6 bonds)
  ground contact:     depth = max(0,-y); F = k_g*depth + c_g*max(0,-vy);
                      F = min(F, 50 m g); along +y   (membrane_tick.cpp:842-860)
Integrator: semi-implicit Euler, v then x (membrane_tick.cpp:865-867).
"""
from __future__ import annotations

import numpy as np

from tools.science_funnel.typeb_gpu.slice_model import (
    build_topology, DT, N_SUB, F_CAP_MULT, G_EARTH, K_GROUND, C_GROUND, M_VERT, NV,
)


class CpuReference:
    """One environment, float64, vectorized over springs."""

    def __init__(self, pos0: np.ndarray, vel0: np.ndarray):
        topo = build_topology()
        self.si = topo["spring_i"].astype(np.int64)
        self.sj = topo["spring_j"].astype(np.int64)
        self.rest = topo["spring_rest"]
        self.k = topo["spring_k"]
        self.pos = pos0.astype(np.float64).copy()
        self.vel = vel0.astype(np.float64).copy()
        self.contact_fired = False

    def step(self, dt: float = float(DT), n_sub: int = N_SUB) -> None:
        for _ in range(n_sub):
            self._substep(dt / n_sub)

    def _substep(self, h: float) -> None:
        p, v = self.pos, self.vel
        f = np.zeros_like(p)
        # gravity (explicit, as the engine: -g on the vertical axis)
        f[:, 1] -= float(G_EARTH) * M_VERT

        d = p[self.sj] - p[self.si]
        length = np.sqrt((d * d).sum(axis=1))
        stretch = (length - self.rest) * self.k
        dirv = d / np.maximum(length, 1e-300)[:, None]
        fs = dirv * stretch[:, None]
        np.add.at(f, self.si, fs)
        np.add.at(f, self.sj, -fs)

        # ground contact per vertex (engine law, capped)
        depth = np.maximum(0.0, -p[:, 1])
        f_contact = K_GROUND * depth + C_GROUND * np.maximum(0.0, -v[:, 1])
        f_contact = np.minimum(f_contact, F_CAP_MULT * M_VERT * float(G_EARTH))
        self.contact_fired |= bool((f_contact > 0.0).any())
        f[:, 1] += f_contact

        # semi-implicit Euler: v then x
        v += (f / M_VERT) * h
        p += v * h

    def state(self) -> tuple[np.ndarray, np.ndarray]:
        return self.pos.copy(), self.vel.copy()
