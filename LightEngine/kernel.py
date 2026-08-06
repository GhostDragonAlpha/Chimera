"""
LightEngine kernel — the two-force physics of the light era.

The world contains one kind of point: identical electrons (mass = 1,
charge = 1, no authored properties).  Two passes act on the same point set
every tick:

  1. DRAW   — long-range, blind gravity.  Direct O(N^2) softened inverse-square
              in this first build.  The public interface is
              ``compute_draw(positions, masses) -> accelerations`` so a
              Barnes-Hut tree can drop in as v2 without changing callers.

  2. RESISTANCE — short-range electromagnetism.  Neighbor list with cutoff r_c;
                  wall at |r| < r_wall (with contact radiation / radial damping),
                  bond at r_wall <= |r| <= r_bond, zero beyond r_c.
                  The public interface is
                  ``compute_resistance(positions, velocities) -> accelerations``.

  3. INTEGRATE  — velocity Verlet with the fixed dt declared in constants.py.

A CPU/Numba path is always available; a CUDA path is used when numba.cuda
reports a device.  Both implement the same force laws bit-for-bit in intent;
only summation order differs.
"""

from __future__ import annotations

import math
import numpy as np
from numba import njit, prange, cuda
from numba.core.errors import NumbaPerformanceWarning
import warnings

from LightEngine.constants import (
    G, K_WALL, K_BOND, R_WALL, R_BOND, R_C, P_WALL, EPS, DT, GAMMA_W, S_WALL,
)

warnings.filterwarnings("ignore", category=NumbaPerformanceWarning)

# ── CUDA availability probe ───────────────────────────────────────
try:
    if cuda.is_available():
        _cuda_available = True
        _cuda_device = cuda.get_current_device()
    else:
        _cuda_available = False
        _cuda_device = None
except Exception:  # pragma: no cover
    _cuda_available = False
    _cuda_device = None


def cuda_is_available() -> bool:
    """Return True if a CUDA device is present and usable."""
    return _cuda_available


# ═══════════════════════════════════════════════════════════════════
#  CPU / Numba paths
# ═══════════════════════════════════════════════════════════════════
@njit(parallel=True, cache=True)
def _draw_cpu(pos: np.ndarray, G: float, eps2: float, out: np.ndarray):
    """Direct O(N^2) softened inverse-square draw on the CPU."""
    n = pos.shape[0]
    for i in prange(n):
        xi = pos[i, 0]
        yi = pos[i, 1]
        zi = pos[i, 2]
        ax = 0.0
        ay = 0.0
        az = 0.0
        for j in range(n):
            if i == j:
                continue
            dx = pos[j, 0] - xi
            dy = pos[j, 1] - yi
            dz = pos[j, 2] - zi
            r2 = dx * dx + dy * dy + dz * dz + eps2
            inv_r3 = 1.0 / (r2 * math.sqrt(r2))
            f = G * inv_r3
            ax += f * dx
            ay += f * dy
            az += f * dz
        out[i, 0] = ax
        out[i, 1] = ay
        out[i, 2] = az


@njit(parallel=True, cache=True)
def _resist_cpu(pos: np.ndarray, vel: np.ndarray, rw: float, rb: float, rc: float,
                p: float, kw: float, kb: float, gamma_w: float, s_wall: float,
                out: np.ndarray):
    """
    Direct O(N^2) resistance pass with cutoff on the CPU.

    Returns the total radiated power in the wall branch (sum over unordered
    pairs of gamma_w * v_rad^2) via the 1-element ``power`` array.
    """
    n = pos.shape[0]
    rc2 = rc * rc
    power = 0.0
    for i in prange(n):
        xi = pos[i, 0]
        yi = pos[i, 1]
        zi = pos[i, 2]
        vxi = vel[i, 0]
        vyi = vel[i, 1]
        vzi = vel[i, 2]
        ax = 0.0
        ay = 0.0
        az = 0.0
        for j in range(n):
            if i == j:
                continue
            dx = pos[j, 0] - xi
            dy = pos[j, 1] - yi
            dz = pos[j, 2] - zi
            r2 = dx * dx + dy * dy + dz * dz
            if r2 > rc2:
                continue
            if r2 < 1e-18:
                continue
            r = math.sqrt(r2)
            if r < rw:
                # strong short-range wall: push away from j.
                # r_eff softens the packet core; the scalar is evaluated with r_eff
                # but the direction stays along the true unit vector (r_i - r_j)/r.
                inv_r = 1.0 / r
                ux_ij = dx * inv_r
                uy_ij = dy * inv_r
                uz_ij = dz * inv_r
                r_eff = math.sqrt(r2 + s_wall * s_wall)
                f = kw * ((rw / r_eff) ** p) / r_eff
                # repulsive force on i is along (r_i - r_j)/r = -u_ij
                ax += f * (-ux_ij)
                ay += f * (-uy_ij)
                az += f * (-uz_ij)
                # contact radiation: radial damping, equal and opposite
                dvx = vel[j, 0] - vxi
                dvy = vel[j, 1] - vyi
                dvz = vel[j, 2] - vzi
                v_rad = dvx * ux_ij + dvy * uy_ij + dvz * uz_ij
                # F_i damps the relative radial motion: F_i = +gamma_w * v_rad * u
                damp = gamma_w * v_rad
                ax += damp * ux_ij
                ay += damp * uy_ij
                az += damp * uz_ij
                # each unordered pair is visited twice; accumulate half each time
                power += 0.5 * gamma_w * v_rad * v_rad
            elif r <= rb:
                # bond spring: attractive when stretched, repulsive when compressed
                f = kb * (r - rb) / (rb * r)
                ax += f * dx
                ay += f * dy
                az += f * dz
        out[i, 0] = ax
        out[i, 1] = ay
        out[i, 2] = az
    return power


# ═══════════════════════════════════════════════════════════════════
#  CUDA paths
# ═══════════════════════════════════════════════════════════════════
if _cuda_available:
    @cuda.jit(cache=True)
    def _draw_cuda(pos, out, G, eps2, n):
        """Direct O(N^2) softened inverse-square draw on the GPU."""
        i = cuda.grid(1)
        if i >= n:
            return
        xi = pos[i, 0]
        yi = pos[i, 1]
        zi = pos[i, 2]
        ax = 0.0
        ay = 0.0
        az = 0.0
        for j in range(n):
            if i == j:
                continue
            dx = pos[j, 0] - xi
            dy = pos[j, 1] - yi
            dz = pos[j, 2] - zi
            r2 = dx * dx + dy * dy + dz * dz + eps2
            inv_r3 = 1.0 / (r2 * math.sqrt(r2))
            f = G * inv_r3
            ax += f * dx
            ay += f * dy
            az += f * dz
        out[i, 0] = ax
        out[i, 1] = ay
        out[i, 2] = az

    @cuda.jit(cache=True)
    def _resist_cuda(pos, vel, out, rw, rb, rc, p, kw, kb, gamma_w, s_wall,
                     power_out, n):
        """Direct O(N^2) resistance pass with cutoff on the GPU."""
        i = cuda.grid(1)
        if i >= n:
            return
        xi = pos[i, 0]
        yi = pos[i, 1]
        zi = pos[i, 2]
        vxi = vel[i, 0]
        vyi = vel[i, 1]
        vzi = vel[i, 2]
        ax = 0.0
        ay = 0.0
        az = 0.0
        rc2 = rc * rc
        for j in range(n):
            if i == j:
                continue
            dx = pos[j, 0] - xi
            dy = pos[j, 1] - yi
            dz = pos[j, 2] - zi
            r2 = dx * dx + dy * dy + dz * dz
            if r2 > rc2:
                continue
            if r2 < 1e-18:
                continue
            r = math.sqrt(r2)
            if r < rw:
                # strong short-range wall: push away from j.
                # r_eff softens the packet core; the scalar is evaluated with r_eff
                # but the direction stays along the true unit vector (r_i - r_j)/r.
                inv_r = 1.0 / r
                ux_ij = dx * inv_r
                uy_ij = dy * inv_r
                uz_ij = dz * inv_r
                r_eff = math.sqrt(r2 + s_wall * s_wall)
                f = kw * ((rw / r_eff) ** p) / r_eff
                # repulsive force on i is along (r_i - r_j)/r = -u_ij
                ax += f * (-ux_ij)
                ay += f * (-uy_ij)
                az += f * (-uz_ij)
                # contact radiation: radial damping, equal and opposite
                dvx = vel[j, 0] - vxi
                dvy = vel[j, 1] - vyi
                dvz = vel[j, 2] - vzi
                v_rad = dvx * ux_ij + dvy * uy_ij + dvz * uz_ij
                damp = gamma_w * v_rad
                ax += damp * ux_ij
                ay += damp * uy_ij
                az += damp * uz_ij
                # each unordered pair is visited twice; accumulate half each time
                if power_out is not None:
                    cuda.atomic.add(power_out, 0, 0.5 * gamma_w * v_rad * v_rad)
            elif r <= rb:
                f = kb * (r - rb) / (rb * r)
                ax += f * dx
                ay += f * dy
                az += f * dz
        out[i, 0] = ax
        out[i, 1] = ay
        out[i, 2] = az

    @cuda.jit(cache=True)
    def _verlet_kick_drift(pos, vel, acc, dt, n):
        """Velocity Verlet half-kick + drift on device."""
        i = cuda.grid(1)
        if i >= n:
            return
        half = 0.5 * dt
        vel[i, 0] += acc[i, 0] * half
        vel[i, 1] += acc[i, 1] * half
        vel[i, 2] += acc[i, 2] * half
        pos[i, 0] += vel[i, 0] * dt
        pos[i, 1] += vel[i, 1] * dt
        pos[i, 2] += vel[i, 2] * dt

    @cuda.jit(cache=True)
    def _verlet_final_kick(vel, acc, dt, n):
        """Velocity Verlet final half-kick on device."""
        i = cuda.grid(1)
        if i >= n:
            return
        half = 0.5 * dt
        vel[i, 0] += acc[i, 0] * half
        vel[i, 1] += acc[i, 1] * half
        vel[i, 2] += acc[i, 2] * half


# ═══════════════════════════════════════════════════════════════════
#  Public force interfaces
# ═══════════════════════════════════════════════════════════════════
def compute_draw(positions: np.ndarray,
                 masses: np.ndarray | None = None,
                 out: np.ndarray | None = None,
                 use_cuda: bool | None = None) -> np.ndarray:
    """
    Compute the DRAW acceleration for every point.

    Interface: ``compute_draw(positions, masses) -> accelerations``.
    This first build uses direct O(N^2) summation; a Barnes-Hut tree
    implementing the same interface is planned as v2.

    Parameters
    ----------
    positions : (N, 3) float array
    masses : ignored — all points have mass 1, kept for the v2 interface
    out : optional (N, 3) float array to fill
    use_cuda : if True, require GPU; if False, force CPU; if None, auto

    Returns
    -------
    out : (N, 3) float array of accelerations
    """
    positions = np.asarray(positions, dtype=np.float32)
    n = positions.shape[0]
    if out is None:
        out = np.empty((n, 3), dtype=np.float32)
    else:
        out = np.asarray(out, dtype=np.float32)

    gpu = (use_cuda is True) or (use_cuda is None and _cuda_available)
    if gpu:
        d_pos = cuda.to_device(positions)
        d_out = cuda.to_device(out)
        threads = 256
        blocks = (n + threads - 1) // threads
        _draw_cuda[blocks, threads](d_pos, d_out, float(G), float(EPS * EPS), n)
        d_out.copy_to_host(out)
    else:
        _draw_cpu(positions, float(G), float(EPS * EPS), out)
    return out


def compute_resistance(positions: np.ndarray,
                       velocities: np.ndarray,
                       out: np.ndarray | None = None,
                       use_cuda: bool | None = None) -> np.ndarray:
    """
    Compute the RESISTANCE acceleration for every point.

    Interface: ``compute_resistance(positions, velocities) -> accelerations``.
    This build evaluates every pair and skips beyond r_c.  Inside the wall
    a radial damping term removes relative radial kinetic energy as light.
    A uniform-grid cell-hash acceleration is available in
    ``build_neighbor_list_grid`` for metrics and tests.

    Parameters
    ----------
    positions : (N, 3) float array
    velocities : (N, 3) float array
    out : optional (N, 3) float array to fill
    use_cuda : if True, require GPU; if False, force CPU; if None, auto

    Returns
    -------
    out : (N, 3) float array of accelerations
    """
    positions = np.asarray(positions, dtype=np.float32)
    velocities = np.asarray(velocities, dtype=np.float32)
    n = positions.shape[0]
    if out is None:
        out = np.empty((n, 3), dtype=np.float32)
    else:
        out = np.asarray(out, dtype=np.float32)

    gpu = (use_cuda is True) or (use_cuda is None and _cuda_available)
    if gpu:
        d_pos = cuda.to_device(positions)
        d_vel = cuda.to_device(velocities)
        d_out = cuda.to_device(out)
        # dummy power sink (not read back)
        d_power = cuda.to_device(np.zeros(1, dtype=np.float32))
        threads = 256
        blocks = (n + threads - 1) // threads
        _resist_cuda[blocks, threads](
            d_pos, d_vel, d_out, float(R_WALL), float(R_BOND), float(R_C),
            float(P_WALL), float(K_WALL), float(K_BOND), float(GAMMA_W),
            float(S_WALL), d_power, n,
        )
        d_out.copy_to_host(out)
    else:
        _resist_cpu(positions, velocities, float(R_WALL), float(R_BOND), float(R_C),
                    float(P_WALL), float(K_WALL), float(K_BOND), float(GAMMA_W),
                    float(S_WALL), out)
    return out


def compute_forces(positions: np.ndarray,
                   velocities: np.ndarray,
                   out: np.ndarray | None = None,
                   use_cuda: bool | None = None) -> np.ndarray:
    """Compute DRAW + RESISTANCE into one acceleration array."""
    positions = np.asarray(positions, dtype=np.float32)
    velocities = np.asarray(velocities, dtype=np.float32)
    n = positions.shape[0]
    if out is None:
        out = np.empty((n, 3), dtype=np.float32)
    else:
        out = np.asarray(out, dtype=np.float32)
    compute_draw(positions, out=out, use_cuda=use_cuda)
    tmp = np.empty_like(out)
    compute_resistance(positions, velocities, out=tmp, use_cuda=use_cuda)
    out += tmp
    return out


# ═══════════════════════════════════════════════════════════════════
#  Neighbor list (uniform grid, CPU) — used by tests and metrics
@njit(cache=True)
def _brute_neighbors(pos, r_cut, counts):
    """Reference neighbor counts by brute force (testing only)."""
    n = pos.shape[0]
    rc2 = r_cut * r_cut
    for i in range(n):
        c = 0
        xi = pos[i, 0]
        yi = pos[i, 1]
        zi = pos[i, 2]
        for j in range(n):
            if i == j:
                continue
            dx = pos[j, 0] - xi
            dy = pos[j, 1] - yi
            dz = pos[j, 2] - zi
            r2 = dx * dx + dy * dy + dz * dz
            if r2 <= rc2:
                c += 1
        counts[i] = c


@njit(cache=True)
def _grid_neighbors(pos, r_cut, counts):
    """
    Exact uniform-grid neighbor counts over a dense bounding-box grid.

    For each particle scans the 27 neighbouring cells.  The result matches
    the brute-force definition: number of distinct other particles within
    ``r_cut``.
    """
    n = pos.shape[0]
    if n == 0:
        return
    cell_size = r_cut

    # bounding box (with a small pad so border particles have a cell)
    xmin = ymin = zmin = float("inf")
    xmax = ymax = zmax = float("-inf")
    for i in range(n):
        x = pos[i, 0]
        y = pos[i, 1]
        z = pos[i, 2]
        if x < xmin:
            xmin = x
        if x > xmax:
            xmax = x
        if y < ymin:
            ymin = y
        if y > ymax:
            ymax = y
        if z < zmin:
            zmin = z
        if z > zmax:
            zmax = z

    nx = int(math.ceil((xmax - xmin) / cell_size)) + 1
    ny = int(math.ceil((ymax - ymin) / cell_size)) + 1
    nz = int(math.ceil((zmax - zmin) / cell_size)) + 1
    n_cells = nx * ny * nz

    # first pass: count particles per cell
    cell_pop = np.zeros(n_cells, dtype=np.int32)
    cell_idx = np.empty(n, dtype=np.int32)
    for i in range(n):
        ix = int(math.floor((pos[i, 0] - xmin) / cell_size))
        iy = int(math.floor((pos[i, 1] - ymin) / cell_size))
        iz = int(math.floor((pos[i, 2] - zmin) / cell_size))
        key = (ix * ny + iy) * nz + iz
        cell_idx[i] = key
        cell_pop[key] += 1

    # prefix sum to place particles in cell-sorted order
    cell_start = np.zeros(n_cells + 1, dtype=np.int32)
    s = 0
    for k in range(n_cells):
        cell_start[k] = s
        s += cell_pop[k]
    cell_start[n_cells] = s

    cursor = cell_start.copy()
    order = np.empty(n, dtype=np.int32)
    for i in range(n):
        key = cell_idx[i]
        idx = cursor[key]
        order[idx] = i
        cursor[key] = idx + 1

    rc2 = r_cut * r_cut
    for i in range(n):
        xi = pos[i, 0]
        yi = pos[i, 1]
        zi = pos[i, 2]
        c = 0
        ci = int(math.floor((xi - xmin) / cell_size))
        cj = int(math.floor((yi - ymin) / cell_size))
        ck = int(math.floor((zi - zmin) / cell_size))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    nxi = ci + dx
                    nyi = cj + dy
                    nzi = ck + dz
                    if nxi < 0 or nxi >= nx:
                        continue
                    if nyi < 0 or nyi >= ny:
                        continue
                    if nzi < 0 or nzi >= nz:
                        continue
                    key = (nxi * ny + nyi) * nz + nzi
                    start = cell_start[key]
                    end = cell_start[key + 1]
                    for t in range(start, end):
                        j = order[t]
                        if i == j:
                            continue
                        ddx = pos[j, 0] - xi
                        ddy = pos[j, 1] - yi
                        ddz = pos[j, 2] - zi
                        r2 = ddx * ddx + ddy * ddy + ddz * ddz
                        if r2 <= rc2:
                            c += 1
        counts[i] = c


def build_neighbor_list_grid(positions: np.ndarray, r_cut: float) -> np.ndarray:
    """
    Return neighbor counts for every particle using a uniform grid hash.

    Counts match the brute-force definition: number of distinct other
    particles within ``r_cut``.
    """
    positions = np.asarray(positions, dtype=np.float32)
    counts = np.empty(positions.shape[0], dtype=np.int32)
    _grid_neighbors(positions, float(r_cut), counts)
    return counts


def brute_neighbor_counts(positions: np.ndarray, r_cut: float) -> np.ndarray:
    """Brute-force neighbor counts (test reference)."""
    positions = np.asarray(positions, dtype=np.float32)
    counts = np.empty(positions.shape[0], dtype=np.int32)
    _brute_neighbors(positions, float(r_cut), counts)
    return counts


# ═══════════════════════════════════════════════════════════════════
#  Velocity Verlet integrator
# ═══════════════════════════════════════════════════════════════════
class VelocityVerlet:
    """
    Velocity Verlet integrator for the two-force point set with contact
    radiation bookkeeping.

    Holds positions, velocities, current acceleration, and cumulative radiated
    energy on either host or device.  ``step(dt)`` advances one tick:

        v_{n+1/2} = v_n + a_n * dt/2
        x_{n+1}   = x_n + v_{n+1/2} * dt
        a_{n+1}   = F(x_{n+1}, v_{n+1/2}) / m
        v_{n+1}   = v_{n+1/2} + a_{n+1} * dt/2

    The damping term is evaluated with the velocities held at force-evaluation
    time; radiated power is accumulated as gamma_w * v_rad^2 per unordered
    wall pair.
    """

    def __init__(self, n: int, use_cuda: bool | None = None):
        self.n = int(n)
        self.use_cuda = (use_cuda if use_cuda is not None else _cuda_available)
        self.pos = np.zeros((n, 3), dtype=np.float32)
        self.vel = np.zeros((n, 3), dtype=np.float32)
        self.acc = np.zeros((n, 3), dtype=np.float32)
        self.radiated_energy = 0.0  # float64, cumulative
        self.last_radiated_power = 0.0  # float64, most recent tick
        if self.use_cuda:
            self.d_pos = cuda.to_device(self.pos)
            self.d_vel = cuda.to_device(self.vel)
            self.d_acc = cuda.to_device(self.acc)

    def set_state(self, positions: np.ndarray, velocities: np.ndarray):
        """Replace host state; upload to device if using CUDA."""
        self.pos[:] = np.asarray(positions, dtype=np.float32)[:self.n]
        self.vel[:] = np.asarray(velocities, dtype=np.float32)[:self.n]
        if self.use_cuda:
            self.d_pos.copy_to_device(self.pos)
            self.d_vel.copy_to_device(self.vel)

    def compute_acceleration(self):
        """Compute a = F(x, v) at the current state."""
        if self.use_cuda:
            threads = 256
            blocks = (self.n + threads - 1) // threads
            _draw_cuda[blocks, threads](
                self.d_pos, self.d_acc, float(G), float(EPS * EPS), self.n)
            if not hasattr(self, "_d_tmp") or self._d_tmp.shape[0] < self.n:
                self._d_tmp = cuda.device_array((self.n, 3), dtype=np.float32)
            if not hasattr(self, "_d_power"):
                self._d_power = cuda.device_array(1, dtype=np.float32)
            self._d_power[0] = 0.0
            _resist_cuda[blocks, threads](
                self.d_pos, self.d_vel, self._d_tmp, float(R_WALL), float(R_BOND), float(R_C),
                float(P_WALL), float(K_WALL), float(K_BOND), float(GAMMA_W),
                float(S_WALL), self._d_power, self.n)
            _add_acc[blocks, threads](self.d_acc, self._d_tmp, self.n)
            cuda.synchronize()
            self.d_acc.copy_to_host(self.acc)
        else:
            compute_forces(self.pos, self.vel, out=self.acc, use_cuda=False)
        return self.acc

    def step(self, dt: float = DT):
        """Advance one velocity-Verlet tick and account for radiated energy."""
        dt = float(dt)
        if self.use_cuda:
            threads = 256
            blocks = (self.n + threads - 1) // threads
            # 1. half-kick + drift using a(t)
            _verlet_kick_drift[blocks, threads](
                self.d_pos, self.d_vel, self.d_acc, dt, self.n)
            cuda.synchronize()
            # 2. recompute total acceleration at the new positions and current v
            _draw_cuda[blocks, threads](
                self.d_pos, self.d_acc, float(G), float(EPS * EPS), self.n)
            if not hasattr(self, "_d_tmp") or self._d_tmp.shape[0] < self.n:
                self._d_tmp = cuda.device_array((self.n, 3), dtype=np.float32)
            if not hasattr(self, "_d_power"):
                self._d_power = cuda.device_array(1, dtype=np.float32)
            self._d_power[0] = 0.0
            _resist_cuda[blocks, threads](
                self.d_pos, self.d_vel, self._d_tmp, float(R_WALL), float(R_BOND), float(R_C),
                float(P_WALL), float(K_WALL), float(K_BOND), float(GAMMA_W),
                float(S_WALL), self._d_power, self.n)
            _add_acc[blocks, threads](self.d_acc, self._d_tmp, self.n)
            cuda.synchronize()
            # 3. final half-kick using a(t+dt)
            _verlet_final_kick[blocks, threads](self.d_vel, self.d_acc, dt, self.n)
            cuda.synchronize()
            self.d_pos.copy_to_host(self.pos)
            self.d_vel.copy_to_host(self.vel)
            self.d_acc.copy_to_host(self.acc)
            power = float(self._d_power.copy_to_host()[0])
            self.last_radiated_power = power
            self.radiated_energy += power * dt
        else:
            self.vel += 0.5 * dt * self.acc
            self.pos += dt * self.vel
            # compute resistance + draw; resistance returns radiated power
            draw_acc = np.empty_like(self.acc)
            _draw_cpu(self.pos, float(G), float(EPS * EPS), draw_acc)
            resist_acc = np.empty_like(self.acc)
            power = _resist_cpu(
                self.pos, self.vel, float(R_WALL), float(R_BOND), float(R_C),
                float(P_WALL), float(K_WALL), float(K_BOND), float(GAMMA_W),
                float(S_WALL), resist_acc)
            self.acc[:] = draw_acc + resist_acc
            self.vel += 0.5 * dt * self.acc
            self.last_radiated_power = float(power)
            self.radiated_energy += float(power) * dt

    def sync_from_device(self):
        """Copy device state back to host (CUDA only)."""
        if self.use_cuda:
            self.d_pos.copy_to_host(self.pos)
            self.d_vel.copy_to_host(self.vel)
            self.d_acc.copy_to_host(self.acc)


if _cuda_available:
    @cuda.jit(cache=True)
    def _add_acc(a, b, n):
        i = cuda.grid(1)
        if i >= n:
            return
        a[i, 0] += b[i, 0]
        a[i, 1] += b[i, 1]
        a[i, 2] += b[i, 2]
