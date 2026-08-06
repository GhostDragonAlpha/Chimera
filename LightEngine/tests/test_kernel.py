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
    G, R_WALL, R_BOND, R_C, P_WALL, K_WALL, K_BOND, EPS, DT, GAMMA_W, S_WALL,
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
def _wall_potential_antiderivative(r):
    """Antiderivative of (r^2 + S_WALL^2)^(-(P_WALL+1)/2) for P_WALL = 6."""
    r = np.asarray(r, dtype=np.float64)
    r_eff = np.sqrt(r * r + S_WALL * S_WALL)
    #  ∫ (r^2 + s^2)^(-7/2) dr  =
    #    r/(5 s^2 r_eff^5) + 4 r/(15 s^4 r_eff^3) + 8 r/(15 s^6 r_eff)
    return r * (1.0 / (5.0 * S_WALL**2 * r_eff**5) +
                4.0 / (15.0 * S_WALL**4 * r_eff**3) +
                8.0 / (15.0 * S_WALL**6 * r_eff))


# value of the antiderivative at infinity: 8/(15 S_WALL^6)
_WALL_POTENTIAL_AT_INF = K_WALL * (R_WALL ** P_WALL) * 8.0 / (15.0 * S_WALL**6)


def _potential_energy(pos):
    """
    Float64 potential energy of the two-force pair.

    Wall branch uses the softened potential consistent with the doc force law.
    For scalar f(r) = K_WALL (R_WALL / r_eff)^P_WALL / r_eff,
        U_wall(r) = K_WALL R_WALL^P_WALL ∫_r^∞ (r'^2 + S_WALL^2)^(-(P+1)/2) dr'.
    With P_WALL = 6 this has the closed form used above.
    """
    pos = np.asarray(pos, dtype=np.float64)
    diff = pos[None, :, :] - pos[:, None, :]
    r2 = np.einsum("ijk,ijk->ij", diff, diff)
    np.fill_diagonal(r2, np.inf)
    r = np.sqrt(r2)

    # softened gravity: U = -G / sqrt(r^2 + eps^2)
    u_draw = -0.5 * G * np.sum((r2 + EPS * EPS) ** (-0.5))

    # softened wall: pair potential, summed over unordered pairs
    wall = r < R_WALL
    u_wall = 0.0
    if wall.any():
        u_wall = 0.5 * np.sum(
            _WALL_POTENTIAL_AT_INF -
            K_WALL * (R_WALL ** P_WALL) * _wall_potential_antiderivative(r[wall])
        )

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


# ── (f) finite packet / softened wall tests ─────────────────────────
def test_softened_wall_potential_derivative():
    """
    The softened wall potential must satisfy -dU/dr = f_scalar(r), where
    f_scalar = K_WALL (R_WALL / r_eff)^P_WALL / r_eff is the doc's scalar
    repulsion magnitude.
    """
    # grid of separations inside the wall (including deep overlap)
    rs = np.logspace(-4, np.log10(R_WALL), 200, dtype=np.float64)
    dr = 1e-8

    def U_pair(r):
        return K_WALL * (R_WALL ** P_WALL) * (
            8.0 / (15.0 * S_WALL**6) - _wall_potential_antiderivative(r)
        )

    dU_dr = (U_pair(rs + dr) - U_pair(rs - dr)) / (2.0 * dr)
    r_eff = np.sqrt(rs * rs + S_WALL * S_WALL)
    f_scalar = K_WALL * (R_WALL / r_eff) ** P_WALL / r_eff
    rel_err = np.abs(-dU_dr - f_scalar) / (f_scalar + 1e-12)
    assert np.max(rel_err) < 1e-4


def test_deep_overlap_finite_acceleration():
    """Two points deeply overlapped feel the saturated wall, not infinity."""
    a_max = K_WALL * (2.0 ** (P_WALL + 1)) / R_WALL  # 2560

    for r_sep in [1e-4, 1e-3, 0.01, 0.03]:
        pos = np.array([[0.0, 0.0, 0.0],
                        [r_sep, 0.0, 0.0]], dtype=np.float32)
        vel = np.zeros_like(pos)

        a_cpu = kernel.compute_resistance(pos, vel, use_cuda=False)
        mag_cpu = float(np.linalg.norm(a_cpu[0]))

        if kernel.cuda_is_available():
            a_gpu = kernel.compute_resistance(pos, vel, use_cuda=True)
            mag_gpu = float(np.linalg.norm(a_gpu[0]))
            assert abs(mag_cpu - mag_gpu) <= 1e-4 * max(mag_cpu, 1.0), (
                f"CPU/GPU mismatch at r={r_sep}: {mag_cpu} vs {mag_gpu}")

        # scalar formula for the wall branch (unit-vector direction)
        r_eff = np.sqrt(r_sep * r_sep + S_WALL * S_WALL)
        f_scalar = K_WALL * (R_WALL / r_eff) ** P_WALL / r_eff
        assert abs(mag_cpu - f_scalar) <= 1e-3 * max(f_scalar, 1.0), (
            f"|a|={mag_cpu} vs scalar {f_scalar} at r={r_sep}")

        # must stay below the saturation cap
        assert mag_cpu <= a_max * 1.01, (
            f"|a|={mag_cpu} at r={r_sep} exceeds cap {a_max}")
        assert np.isfinite(mag_cpu)

    # deepest overlap must be within 1% of the cap
    pos = np.array([[0.0, 0.0, 0.0],
                    [1e-4, 0.0, 0.0]], dtype=np.float32)
    a_deep = kernel.compute_resistance(pos, np.zeros_like(pos), use_cuda=False)
    mag_deep = float(np.linalg.norm(a_deep[0]))
    assert mag_deep >= a_max * 0.99, (
        f"deep overlap |a|={mag_deep} not saturated near {a_max}")


def test_high_speed_wall_encounter_no_slingshot():
    """
    Regression for run-3 blow-up: a head-on pair at v_rel=100 starting just
    outside the wall must not be ejected faster than it arrived.  Total energy
    accounting (mechanical + radiated) must not show energy creation.
    """
    pos = np.array([[0.0, 0.0, 0.0],
                    [0.06, 0.0, 0.0]], dtype=np.float32)
    vel = np.array([[50.0, 0.0, 0.0],
                    [-50.0, 0.0, 0.0]], dtype=np.float32)
    v_rel0 = float(np.linalg.norm(vel[1] - vel[0]))

    vv = kernel.VelocityVerlet(2, use_cuda=False)
    vv.set_state(pos, vel)
    vv.compute_acceleration()
    e0 = _potential_energy(vv.pos) + 0.5 * np.sum(vv.vel.astype(np.float64) ** 2)

    for _ in range(600):
        vv.step(DT)

    v_rel1 = float(np.linalg.norm(vv.vel[1] - vv.vel[0]))
    e1 = _potential_energy(vv.pos) + 0.5 * np.sum(vv.vel.astype(np.float64) ** 2)

    # no slingshot amplification
    assert v_rel1 <= 1.2 * v_rel0, f"v_rel grew {v_rel0:.3f} -> {v_rel1:.3f}"

    # energy accounting: final mechanical + radiated must not exceed initial
    # by more than integration tolerance
    total_out = e1 + vv.radiated_energy
    assert total_out <= e0 + 1e-2 * (abs(e0) + 1.0), (
        f"energy created: E0={e0:.4f}, E1+rad={total_out:.4f}")
