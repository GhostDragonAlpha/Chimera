"""
LightEngine kernel tests.

(a) kernel vs referee agreement on 2-point, 3-point, and wall-collision scenarios
(b) energy bookkeeping sanity on a free-fall pair
(c) determinism: same seed -> identical positions after 50 ticks
(d) neighbor list completeness vs brute force on a random cloud
(e) contact radiation: damping agreement, energy removal, momentum conservation,
    and free-flight energy conservation
"""

import numpy as np
import pytest

from LightEngine import kernel, referee
from LightEngine.constants import (
    G, R_WALL, R_BOND, R_C, P_WALL, K_WALL, K_BOND, EPS, DT, GAMMA_W,
)

TOL = referee.EPS_REF


def _two_points():
    """Two points separated along x, sitting in the bond zone."""
    pos = np.array([[0.0, 0.0, 0.0],
                    [0.12, 0.0, 0.0]], dtype=np.float32)
    return pos


def _three_points():
    """Three points forming an isoceles triangle; two in bond zone, one far."""
    pos = np.array([[0.0, 0.0, 0.0],
                    [0.12, 0.0, 0.0],
                    [0.0, 0.50, 0.0]], dtype=np.float32)
    return pos


def _wall_collision():
    """Two points closer than R_WALL — the wall must dominate."""
    pos = np.array([[0.0, 0.0, 0.0],
                    [0.02, 0.0, 0.0]], dtype=np.float32)
    return pos


# ── (a) kernel vs referee agreement (zero velocity -> no damping) ───
def test_draw_two_points():
    pos = _two_points()
    a_ker = kernel.compute_draw(pos, use_cuda=False)
    a_ref = referee.compute_draw_ref(pos)
    assert referee.relative_error(a_ker, a_ref) < TOL


def test_resistance_two_points():
    pos = _two_points()
    vel = np.zeros_like(pos)
    a_ker = kernel.compute_resistance(pos, vel, use_cuda=False)
    a_ref = referee.compute_resistance_ref(pos, vel)
    assert referee.relative_error(a_ker, a_ref) < TOL


def test_total_three_points():
    pos = _three_points()
    vel = np.zeros_like(pos)
    a_ker = kernel.compute_forces(pos, vel, use_cuda=False)
    a_ref = referee.compute_forces_ref(pos, vel)
    assert referee.relative_error(a_ker, a_ref) < TOL


def test_wall_collision():
    pos = _wall_collision()
    vel = np.zeros_like(pos)
    a_ker = kernel.compute_forces(pos, vel, use_cuda=False)
    a_ref = referee.compute_forces_ref(pos, vel)
    assert referee.relative_error(a_ker, a_ref) < TOL
    # sanity: net relative acceleration should push them apart
    net = a_ker[1] - a_ker[0]
    assert net[0] > 0.0, "wall should repel along x"


# ── (b) energy bookkeeping on a free-fall pair ──────────────────────
def _potential_energy(pos):
    """Float64 potential energy of the two-force pair."""
    pos = np.asarray(pos, dtype=np.float64)
    diff = pos[None, :, :] - pos[:, None, :]
    r2 = np.einsum("ijk,ijk->ij", diff, diff)
    np.fill_diagonal(r2, np.inf)
    r = np.sqrt(r2)

    # softened gravity: U = -G / sqrt(r^2 + eps^2)
    u_draw = -0.5 * G * np.sum((r2 + EPS * EPS) ** (-0.5))

    # wall: U = K_WALL * r_wall^P * r^(1-P) / (P-1)
    wall = r < R_WALL
    u_wall = 0.0
    if wall.any():
        u_wall = 0.5 * K_WALL * (R_WALL ** P_WALL) * np.sum(
            r[wall] ** (1 - P_WALL)) / (P_WALL - 1)

    # bond: U = 0.5 * K_BOND / R_BOND * (r - R_BOND)^2
    bond = (r >= R_WALL) & (r <= R_BOND)
    u_bond = 0.0
    if bond.any():
        u_bond = 0.5 * (K_BOND / R_BOND) * np.sum((r[bond] - R_BOND) ** 2)

    return u_draw + u_wall + u_bond


def test_energy_free_fall_pair():
    """
    A pair starting at rest in the bond zone should keep total energy finite
    and non-NaN over a short integration.
    """
    pos = np.array([[0.0, 0.0, 0.0],
                    [0.14, 0.01, -0.01]], dtype=np.float32)
    vel = np.zeros((2, 3), dtype=np.float32)

    vv = kernel.VelocityVerlet(2, use_cuda=False)
    vv.set_state(pos, vel)
    vv.compute_acceleration()

    e0 = _potential_energy(vv.pos) + 0.5 * np.sum(vv.vel.astype(np.float64) ** 2)
    energies = [e0]
    for _ in range(200):
        vv.step(DT)
        e = _potential_energy(vv.pos) + 0.5 * np.sum(vv.vel.astype(np.float64) ** 2)
        energies.append(e)

    e_arr = np.array(energies)
    assert np.all(np.isfinite(e_arr)), "energy became non-finite"
    e_range = e_arr.max() - e_arr.min()
    assert e_range < 1000.0 * (np.abs(e0) + 1.0), "energy range unbounded"


# ── (c) determinism ─────────────────────────────────────────────────
def test_determinism_50_ticks():
    """Same seed must produce identical positions after 50 ticks."""
    def run(seed):
        rng = np.random.default_rng(seed)
        n = 64
        pos = rng.normal(0, 1, (n, 3)).astype(np.float32)
        vel = rng.normal(0, 0.1, (n, 3)).astype(np.float32)
        vv = kernel.VelocityVerlet(n, use_cuda=False)
        vv.set_state(pos, vel)
        vv.compute_acceleration()
        for _ in range(50):
            vv.step(DT)
        return vv.pos.copy()

    p1 = run(12345)
    p2 = run(12345)
    np.testing.assert_allclose(p1, p2, atol=1e-6)


# ── (d) neighbor list completeness ──────────────────────────────────
def test_neighbor_grid_completeness():
    """Uniform-grid neighbor counts must equal brute-force counts."""
    rng = np.random.default_rng(99)
    n = 500
    pos = rng.uniform(-2.0, 2.0, (n, 3)).astype(np.float32)
    grid_counts = kernel.build_neighbor_list_grid(pos, R_C)
    brute_counts = kernel.brute_neighbor_counts(pos, R_C)
    np.testing.assert_array_equal(grid_counts, brute_counts)


def test_neighbor_grid_wall_cutoff():
    """Grid must be correct near the wall/bond boundary."""
    rng = np.random.default_rng(7)
    n = 200
    pos = rng.normal(0, R_WALL * 2, (n, 3)).astype(np.float32)
    grid_counts = kernel.build_neighbor_list_grid(pos, R_C)
    brute_counts = kernel.brute_neighbor_counts(pos, R_C)
    np.testing.assert_array_equal(grid_counts, brute_counts)


# ── (e) contact radiation tests ─────────────────────────────────────
def _wall_pair_approaching():
    """Pair inside the wall, moving toward each other along x."""
    pos = np.array([[0.0, 0.0, 0.0],
                    [0.04, 0.0, 0.0]], dtype=np.float32)
    vel = np.array([[0.5, 0.0, 0.0],
                    [-0.5, 0.0, 0.0]], dtype=np.float32)
    return pos, vel


def _wall_pair_separating():
    """Pair inside the wall, moving away from each other along x."""
    pos = np.array([[0.0, 0.0, 0.0],
                    [0.04, 0.0, 0.0]], dtype=np.float32)
    vel = np.array([[-0.5, 0.0, 0.0],
                    [0.5, 0.0, 0.0]], dtype=np.float32)
    return pos, vel


def _damping_only_ref(pos, vel):
    """Reference damping acceleration only (for sign checks)."""
    pos64 = np.asarray(pos, dtype=np.float64)
    vel64 = np.asarray(vel, dtype=np.float64)
    diff = pos64[:, None, :] - pos64[None, :, :]
    r2 = np.einsum("ijk,ijk->ij", diff, diff)
    np.fill_diagonal(r2, np.inf)
    r = np.sqrt(r2)
    wall = r < R_WALL
    u = -diff / r[:, :, None]
    dv = vel64[None, :, :] - vel64[:, None, :]
    v_rad = np.einsum("ijk,ijk->ij", dv, u)
    f_damp = np.zeros_like(r)
    f_damp[wall] = GAMMA_W * v_rad[wall]
    acc = np.einsum("ij,ijk->ik", f_damp, u)
    return acc


def test_damping_approaching_agreement():
    pos, vel = _wall_pair_approaching()
    a_ker = kernel.compute_resistance(pos, vel, use_cuda=False)
    a_ref = referee.compute_resistance_ref(pos, vel)
    assert referee.relative_error(a_ker, a_ref) < TOL
    # sign check: each particle must be damped toward zero relative motion
    damp = _damping_only_ref(pos, vel)
    # particle 0 moves right (+x) toward j; damping on 0 should be left (-x)
    assert damp[0, 0] < 0.0
    # particle 1 moves left (-x); damping on 1 should be right (+x)
    assert damp[1, 0] > 0.0


def test_damping_separating_agreement():
    pos, vel = _wall_pair_separating()
    a_ker = kernel.compute_resistance(pos, vel, use_cuda=False)
    a_ref = referee.compute_resistance_ref(pos, vel)
    assert referee.relative_error(a_ker, a_ref) < TOL
    damp = _damping_only_ref(pos, vel)
    # particle 0 moves left (-x) away from j; damping on 0 should be right (+x)
    assert damp[0, 0] > 0.0
    # particle 1 moves right (+x); damping on 1 should be left (-x)
    assert damp[1, 0] < 0.0


def test_energy_removal_wall_encounter():
    """
    A head-on pair entering the wall must lose total mechanical energy,
    and the loss must match the integrator's radiated_energy accumulator.
    """
    pos = np.array([[0.0, 0.0, 0.0],
                    [0.10, 0.0, 0.0]], dtype=np.float32)
    # inward velocity large enough to reach the wall
    vel = np.array([[1.0, 0.0, 0.0],
                    [-1.0, 0.0, 0.0]], dtype=np.float32)

    vv = kernel.VelocityVerlet(2, use_cuda=False)
    vv.set_state(pos, vel)
    vv.compute_acceleration()

    e0 = _potential_energy(vv.pos) + 0.5 * np.sum(vv.vel.astype(np.float64) ** 2)
    for _ in range(400):
        vv.step(DT)
    e_final = _potential_energy(vv.pos) + 0.5 * np.sum(vv.vel.astype(np.float64) ** 2)

    delta_e = e_final - e0
    # energy must have left the pair
    assert delta_e < 0.0, f"energy increased: {delta_e}"
    # radiated_energy tracks the loss
    loss = -delta_e
    rad = vv.radiated_energy
    rel_diff = abs(rad - loss) / (abs(loss) + 1e-12)
    # Allow a few-percent integration error for velocity-dependent forces
    # under velocity Verlet.
    assert rel_diff < 5e-2, f"radiated_energy {rad} vs analytic loss {loss}, rel_diff {rel_diff}"


def test_momentum_conservation_damped_pair():
    """Total momentum of an isolated damped pair is conserved."""
    pos, vel = _wall_pair_approaching()
    vv = kernel.VelocityVerlet(2, use_cuda=False)
    vv.set_state(pos, vel)
    vv.compute_acceleration()
    p0 = vv.vel.sum(axis=0).astype(np.float64)
    for _ in range(200):
        vv.step(DT)
    p1 = vv.vel.sum(axis=0).astype(np.float64)
    np.testing.assert_allclose(p0, p1, atol=1e-4)


def test_free_flight_conserves_energy():
    """A pair outside r_c feels no resistance and conserves energy."""
    pos = np.array([[0.0, 0.0, 0.0],
                    [0.50, 0.0, 0.0]], dtype=np.float32)
    vel = np.array([[0.1, 0.0, 0.0],
                    [-0.1, 0.0, 0.0]], dtype=np.float32)

    vv = kernel.VelocityVerlet(2, use_cuda=False)
    vv.set_state(pos, vel)
    vv.compute_acceleration()
    e0 = _potential_energy(vv.pos) + 0.5 * np.sum(vv.vel.astype(np.float64) ** 2)
    for _ in range(200):
        vv.step(DT)
    e1 = _potential_energy(vv.pos) + 0.5 * np.sum(vv.vel.astype(np.float64) ** 2)
    # no damping outside the wall: energy conserved to integration accuracy
    assert abs(e1 - e0) < 1e-3 * (abs(e0) + 1.0)
    assert vv.radiated_energy == 0.0
