"""
Core particle simulator — the engine's heartbeat.

Particle state is a contiguous NumPy float32 array (N particles × D columns).
Column layout (28 floats per particle):

  idx  name          description
  ───  ────          ───────────
  0-2  pos (x,y,z)   world position
  3-5  vel (vx,vy,vz) velocity
  6-8  acc (ax,ay,az) acceleration (cleared each frame)
  9    mass           particle mass
  10   life           remaining lifetime (seconds), -1 = immortal
  11   type           particle type (uint8 packed as float32)
  12-15 props[0-3]   writable control variables
  16-18 color (r,g,b) 0-1
  19   alpha          opacity 0-1
  20   size           particle render size
  21-27 reserved      future expansion

Kernels are functions that receive (state array, control_vars dict, dt)
and modify state in-place. They compose: each kernel reads and writes
specific columns, enabling a dataflow pipeline.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Callable, Optional
import time

# ── Column indices ──────────────────────────────────────────────
# Use meaningful names so kernels don't hardcode numbers.
COL = {
    "px": 0,  "py": 1,  "pz": 2,
    "vx": 3,  "vy": 4,  "vz": 5,
    "ax": 6,  "ay": 7,  "az": 8,
    "mass": 9,
    "life": 10,
    "type": 11,
    "prop0": 12, "prop1": 13, "prop2": 14, "prop3": 15,
    "cr": 16,  "cg": 17,  "cb": 18,
    "alpha": 19,
    "size": 20,
    # 21-27 reserved
}

NUM_COLS = 28

C_POS  = slice(0, 3)    # px, py, pz
C_VEL  = slice(3, 6)    # vx, vy, vz
C_ACC  = slice(6, 9)    # ax, ay, az
C_COLOR = slice(16, 20)  # cr, cg, cb, alpha
C_PROPS = slice(12, 16)  # prop0-3

# Particle type constants
PARTICLE_TYPES = {
    "dust":       0,
    "sand":       1,
    "water":      2,
    "social":     3,   # NPC social intent / relationship particles
    "resource":   4,   # trade flow / economy particles
    "atmosphere": 5,   # volumetric fog / clouds
    "shellmite":  6,   # erisaid specimen particles
    "weapon_glint": 7, # weapon material glints
}

TYPE_NAMES = {v: k for k, v in PARTICLE_TYPES.items()}


@dataclass
class ParticleState:
    """Immutable snapshot of the particle buffer at a point in time."""
    data: np.ndarray          # float32 N×28
    active_mask: np.ndarray   # bool[N] — which particles are "alive"
    timestamp: float
    particle_count: int
    active_count: int


class ParticleSimulator:
    """
    The engine's heartbeat. Holds a writeable particle buffer and runs
    a pipeline of kernels each frame. Designed for NumPy vectorization —
    a single array op touches every particle simultaneously.

    Usage:
        sim = ParticleSimulator(max_particles=500_000)
        sim.spawn(count=1000, type="dust", position=(0,0,0), spread=50.0)
        sim.add_kernel(gravity_kernel, "gravity")
        sim.add_kernel(wind_kernel, "wind")
        for _ in range(frames):
            sim.step(dt=1/60, control_vars={"wind_vector": (1.0, 0, 0)})
            state: ParticleState = sim.snapshot()
    """

    def __init__(self, max_particles: int = 500_000):
        self.max_particles = max_particles
        # Pre-allocate the entire buffer — zero allocs during runtime
        self._data = np.zeros((max_particles, NUM_COLS), dtype=np.float32)
        self._active = np.zeros(max_particles, dtype=bool)
        self._count = 0
        self._kernels: list[tuple[Callable, str]] = []  # (fn, name)
        self._frame = 0
        self._start_time = time.time()

    # ── Particle management ─────────────────────────────────────

    def spawn(
        self,
        count: int,
        type_name: str,
        position: tuple[float, float, float] = (0, 0, 0),
        spread: float = 0.0,
        velocity: tuple[float, float, float] = (0, 0, 0),
        mass: float = 1.0,
        life: float = -1.0,         # -1 = immortal
        color: tuple[float, float, float, float] = (1, 1, 1, 1),
        size: float = 1.0,
        props: tuple[float, float, float, float] = (0, 0, 0, 0),
    ) -> int:
        """Spawn `count` particles. Returns the actual number spawned."""
        type_code = PARTICLE_TYPES.get(type_name, 0)
        available = self.max_particles - self._count
        n = min(count, available)
        if n <= 0:
            return 0

        start = self._count
        end = start + n
        self._count += n
        self._active[start:end] = True

        px, py, pz = float(position[0]), float(position[1]), float(position[2])
        vx, vy, vz = float(velocity[0]), float(velocity[1]), float(velocity[2])

        if spread > 0:
            self._data[start:end, C_POS] = np.random.normal(
                (px, py, pz), spread / 3, (n, 3)
            )
        else:
            self._data[start:end, C_POS] = (px, py, pz)

        self._data[start:end, C_VEL] = (vx, vy, vz)
        self._data[start:end, C_ACC] = (0, 0, 0)
        self._data[start:end, COL["mass"]]  = mass
        self._data[start:end, COL["life"]]  = life
        self._data[start:end, COL["type"]]  = float(type_code)
        self._data[start:end, COL["cr"]]    = color[0]
        self._data[start:end, COL["cg"]]    = color[1]
        self._data[start:end, COL["cb"]]    = color[2]
        self._data[start:end, COL["alpha"]] = color[3]
        self._data[start:end, COL["size"]]  = size
        self._data[start:end, C_PROPS]      = props

        return n

    def kill(self, indices: np.ndarray):
        """Remove particles by index (compacts buffer)."""
        if len(indices) == 0:
            return
        keep = ~np.isin(np.arange(self._count), indices)
        n_keep = keep.sum()
        if n_keep < self._count:
            self._data[:n_keep] = self._data[keep]
            self._active[:n_keep] = self._active[keep]
            self._count = int(n_keep)

    def compact(self):
        """Remove dead particles (life <= 0 and life != -1)."""
        mortal = self._active[:self._count].copy()
        mortal &= (self._data[:self._count, COL["life"]] >= 0)
        dead = mortal & (self._data[:self._count, COL["life"]] <= 0)
        if dead.any():
            self.kill(np.where(dead)[0])

    # ── Kernel pipeline ─────────────────────────────────────────

    def add_kernel(self, fn: Callable, name: str):
        """Register a kernel function. Called in order each step()."""
        self._kernels.append((fn, name))

    def remove_kernel(self, name: str):
        self._kernels = [(f, n) for f, n in self._kernels if n != name]

    def step(self, dt: float, control_vars: dict | None = None):
        """
        Execute one simulation tick.
        1. Clear accelerations.
        2. Run each kernel in order against active particles.
        3. Update positions (semi-implicit Euler).
        4. Tick lifetimes.
        5. Compact dead particles.
        """
        if control_vars is None:
            control_vars = {}

        active = self._active[:self._count]
        data_slice = self._data[:self._count]

        # Clear accelerations
        data_slice[active, C_ACC] = (0, 0, 0)

        # Run kernels
        for kernel_fn, name in self._kernels:
            try:
                kernel_fn(data_slice, active, control_vars, dt)
            except Exception as e:
                # A kernel failing should not kill the entire pipeline.
                print(f"[ParticleEngine] kernel '{name}' failed: {e}")

        # Semi-implicit Euler: v += a*dt, p += v*dt
        data_slice[active, C_VEL] += data_slice[active, C_ACC] * dt
        data_slice[active, C_POS] += data_slice[active, C_VEL] * dt

        # Tick lifetimes (skip immortal, life < 0)
        mortal = active & (data_slice[:, COL["life"]] >= 0)
        data_slice[mortal, COL["life"]] -= dt

        # Compact dead particles
        self.compact()
        self._frame += 1

    def snapshot(self) -> ParticleState:
        """Return a read-only copy of current simulation state."""
        active = self._active[:self._count]
        return ParticleState(
            data=self._data[:self._count].copy(),
            active_mask=active.copy(),
            timestamp=time.time() - self._start_time,
            particle_count=self._count,
            active_count=int(active.sum()),
        )

    @property
    def count(self) -> int:
        return self._count

    @property
    def frame(self) -> int:
        return self._frame

    # ── Convenience queries (zero-copy views) ───────────────────

    def positions(self) -> np.ndarray:
        """Return position view (no copy) for active particles."""
        return self._data[:self._count, C_POS]

    def velocities(self) -> np.ndarray:
        return self._data[:self._count, C_VEL]

    def types(self) -> np.ndarray:
        return self._data[:self._count, COL["type"]].astype(np.int32)

    def query_type(self, type_name: str) -> np.ndarray:
        """Return data slice for particles of a given type (view)."""
        code = PARTICLE_TYPES.get(type_name, -1)
        if code < 0:
            return self._data[0:0]
        mask = self.types() == code
        return self._data[:self._count][mask]

    def stats(self) -> dict:
        """Summary statistics for the current frame."""
        active = self._active[:self._count]
        types = self.types()
        type_counts = {}
        for tname, tcode in PARTICLE_TYPES.items():
            cnt = int((types == tcode).sum())
            if cnt:
                type_counts[tname] = cnt
        return {
            "total": self._count,
            "active": int(active.sum()),
            "frame": self._frame,
            "by_type": type_counts,
            "max_particles": self.max_particles,
        }
