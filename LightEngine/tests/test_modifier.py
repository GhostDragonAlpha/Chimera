"""
Tests for LightEngine.modifier — THE MODIFIER, the two-force fold.

Validates that ONE modified Barnes-Hut tree walk reproduces the two-pass
kernel (DRAW + RESISTANCE) within the pre-registered referee tolerance
(EPS_REF = 1e-3 relative), that the resistance stays EXACT within the cutoff
(the tree is descended wherever a resistance partner could hide), that the
CUDA walk agrees with the CPU walk, and that VelocityVerlet(use_modifier=True)
produces the same physics as the two-pass integrator.
"""

import math
import numpy as np
import pytest

from LightEngine import bh_draw, kernel, modifier, referee
from LightEngine.constants import R_WALL, R_BOND, R_C

TOL = referee.EPS_REF


def _jittered_lattice(n: int, spacing: float = 0.05,
                      jitter_frac: float = 0.2, seed: int = 42) -> np.ndarray:
    """Non-overlapping grains: cubic lattice plus small jitter."""
    rng = np.random.default_rng(seed)
    side = int(math.ceil(n ** (1.0 / 3.0)))
    pos = []
    for idx in range(n):
        ix = idx % side
        iy = (idx // side) % side
        iz = idx // (side * side)
        p = np.array([ix - side / 2.0, iy - side / 2.0, iz - side / 2.0],
                     dtype=np.float32)
        p += rng.uniform(-jitter_frac, jitter_frac, size=3)
        pos.append(p)
    pos = np.array(pos, dtype=np.float32) * spacing
    pos -= pos.mean(axis=0)
    return pos


def _rel_max(a: np.ndarray, b: np.ndarray) -> float:
    """Max relative L2 error over particles."""
    denom = np.linalg.norm(b, axis=1)
    denom = np.where(denom == 0, 1.0, denom)
    errs = np.linalg.norm(a - b, axis=1) / denom
    return float(np.max(errs))


def _modifier_agreement(n, seed, spacing=0.05, theta=None):
    """Return (rel_err_mod, rel_err_resistance) vs the two-pass kernel."""
    pos = _jittered_lattice(n, spacing=spacing, seed=seed)
    rng = np.random.default_rng(seed + 1)
    vel = rng.uniform(-0.05, 0.05, size=pos.shape).astype(np.float32)
    a_two = kernel.compute_forces(pos, vel, use_cuda=False)
    a_mod, power_mod = modifier.compute_forces_mod(
        pos, vel, theta=theta, use_cuda=False)
    rel = _rel_max(a_mod, a_two)

    # Resistance must be EXACT within the cutoff: isolate it by scaling the
    # velocity by 2.  Damping is linear in v_rad (damp = gamma_w * v_rad), so
    # a(2v) - a(v) = F_damping exactly: the velocity-independent draw cancels
    # bit-exactly (same positions, same tree walk) and only damping remains.
    a_two2 = kernel.compute_forces(pos, 2 * vel, use_cuda=False)
    a_mod2, _ = modifier.compute_forces_mod(pos, 2 * vel, theta=theta,
                                            use_cuda=False)
    d_res_two = a_two2 - a_two
    d_res_mod = a_mod2 - a_mod
    # Scale-normalized damping error: max abs error over the max damping
    # magnitude.  (Per-particle max-relative is pathological here: damping is
    # exactly zero for the majority of bulk particles, so their denominators
    # would be replaced by 1 and any float32 noise inflated to "100%".)
    scale_res = float(np.max(np.linalg.norm(d_res_two, axis=1)))
    rel_res = (float(np.max(np.linalg.norm(d_res_mod - d_res_two, axis=1)))
               / max(scale_res, 1e-9))
    return rel, rel_res, power_mod


# ── (a) merged walk vs two-pass kernel ─────────────────────────────
def test_modifier_matches_two_pass_lattice():
    """The one walk reproduces DRAW + RESISTANCE within EPS_REF."""
    rel, rel_res, _ = _modifier_agreement(4096, seed=20260807)
    assert rel <= TOL, f"total rel_err={rel:.6e} > {TOL}"
    assert rel_res <= TOL, f"resistance rel_err={rel_res:.6e} > {TOL}"


def test_modifier_matches_across_sizes_and_seeds():
    """
    The fold is EXACT at scale: at theta small enough that the tree fully
    descends (draw becomes pairwise), the one walk reproduces the two-pass
    kernel to float precision across system sizes and seeds.  The residual
    floor is float noise, proving both DRAW and RESISTANCE live in ONE walk.
    """
    for n, seed in ((1024, 3), (2048, 11), (4096, 99)):
        rel, rel_res, _ = _modifier_agreement(n, seed=seed, theta=0.15)
        assert rel <= 1e-4, f"N={n} seed={seed} total rel_err={rel:.6e}"
        assert rel_res <= 1e-4, f"N={n} seed={seed} resist rel_err={rel_res:.6e}"


def test_modifier_theta_accuracy_budget():
    """At the validated default theta the merged walk is within the budget."""
    pos = _jittered_lattice(4096, seed=20260807)
    rng = np.random.default_rng(5)
    vel = rng.uniform(-0.05, 0.05, size=pos.shape).astype(np.float32)
    a_two = kernel.compute_forces(pos, vel, use_cuda=False)
    a_mod, _ = modifier.compute_forces_mod(pos, vel, use_cuda=False)
    assert _rel_max(a_mod, a_two) <= TOL


# ── (b) resistance exactness within the cutoff ─────────────────────
def test_resistance_pairs_are_exact_within_cutoff():
    """
    Every pair within R_C is found: the tree descends any node whose box can
    hold a resistance partner, so the short-range force is exact, not
    approximated.  Two grains at r = 1.5 * R_WALL (inside the wall, strong
    damping) must match the pairwise referee to float precision.
    """
    dx = 1.5 * R_WALL
    pos = np.array([[0, 0, 0], [dx, 0, 0]], dtype=np.float32)
    vel = np.array([[0.1, 0, 0], [-0.1, 0, 0]], dtype=np.float32)  # closing
    a_two = kernel.compute_forces(pos, vel, use_cuda=False)
    a_mod, _ = modifier.compute_forces_mod(pos, vel, theta=0.5, use_cuda=False)
    np.testing.assert_allclose(a_mod, a_two, rtol=1e-5, atol=1e-6)


def test_resistance_zero_beyond_cutoff():
    """A pair beyond R_C feels draw only — M -> 1, no modifier."""
    dx = 1.5 * R_C
    pos = np.array([[0, 0, 0], [dx, 0, 0]], dtype=np.float32)
    vel = np.zeros_like(pos)
    a_two = kernel.compute_forces(pos, vel, use_cuda=False)
    a_mod, _ = modifier.compute_forces_mod(pos, vel, theta=0.5, use_cuda=False)
    np.testing.assert_allclose(a_mod, a_two, rtol=1e-5, atol=1e-6)


# ── (c) radiated power bookkeeping ─────────────────────────────────
def test_radiated_power_matches_kernel():
    """The merged walk reports the same wall radiation as the two-pass CPU."""
    pos = _jittered_lattice(2048, seed=7, spacing=0.03)  # dense: wall contacts
    rng = np.random.default_rng(8)
    vel = rng.uniform(-0.2, 0.2, size=pos.shape).astype(np.float32)
    _, power_mod = modifier.compute_forces_mod(pos, vel, use_cuda=False)
    resist_acc = np.empty_like(pos)
    power_two = kernel._resist_cpu(
        pos, vel, float(R_WALL), float(R_BOND), float(R_C),
        float(kernel.P_WALL), float(kernel.K_WALL), float(kernel.K_BOND),
        float(kernel.GAMMA_W), float(kernel.S_WALL), resist_acc)
    assert power_mod == pytest.approx(float(power_two), rel=1e-4)


# ── (d) CUDA walk vs CPU walk ──────────────────────────────────────
@pytest.mark.skipif(not modifier._cuda_available,
                    reason="CUDA not available")
def test_cuda_matches_cpu_reference():
    """GPU merged walk agrees with the CPU merged walk."""
    pos = _jittered_lattice(1024, seed=13)
    rng = np.random.default_rng(14)
    vel = rng.uniform(-0.05, 0.05, size=pos.shape).astype(np.float32)
    for theta in (0.1, 0.3):
        a_cpu, p_cpu = modifier.compute_forces_mod(pos, vel, theta=theta,
                                                   use_cuda=False)
        a_gpu, p_gpu = modifier.compute_forces_mod(pos, vel, theta=theta,
                                                   use_cuda=True)
        assert _rel_max(a_gpu, a_cpu) <= 1e-5, f"theta={theta} GPU/CPU err"
        assert p_gpu == pytest.approx(p_cpu, rel=1e-3)


def test_determinism():
    """Same inputs produce identical output."""
    pos = _jittered_lattice(2048, seed=99)
    rng = np.random.default_rng(100)
    vel = rng.uniform(-0.05, 0.05, size=pos.shape).astype(np.float32)
    a1, p1 = modifier.compute_forces_mod(pos, vel, theta=0.1, use_cuda=False)
    a2, p2 = modifier.compute_forces_mod(pos, vel, theta=0.1, use_cuda=False)
    np.testing.assert_array_equal(a1, a2)
    assert p1 == p2


# ── (e) integrator integration ─────────────────────────────────────
def test_velocity_verlet_modifier_matches_two_pass():
    """
    VelocityVerlet(use_modifier=True) reproduces the two-pass integrator's
    physics over many ticks within the BH accuracy budget.
    """
    n = 1024
    pos = _jittered_lattice(n, seed=21)
    rng = np.random.default_rng(22)
    vel = rng.uniform(-0.02, 0.02, size=pos.shape).astype(np.float32)
    vel -= vel.mean(axis=0)

    a = kernel.VelocityVerlet(n, use_cuda=False, use_modifier=False)
    b = kernel.VelocityVerlet(n, use_cuda=False, use_modifier=True)
    a.set_state(pos, vel)
    b.set_state(pos, vel)
    for _ in range(50):
        a.step()
        b.step()

    # Position drift over 50 ticks stays within the BH accuracy budget.
    drift = float(np.max(np.linalg.norm(b.pos - a.pos, axis=1)))
    scale = float(np.max(np.linalg.norm(a.pos, axis=1)))
    assert drift <= TOL * max(scale, 1.0), f"drift={drift:.6e}"

    # Radiated energy agrees to the same order.
    rel_rad = (b.radiated_energy - a.radiated_energy) / max(a.radiated_energy, 1e-12)
    assert abs(rel_rad) <= 1e-3, f"radiated rel diff={rel_rad:.6e}"


def test_one_tree_share():
    """THE MODIFIER is ONE walk: the same octree serves both forces."""
    pos = _jittered_lattice(1024, seed=31)
    tree = bh_draw.build_octree(pos, leaf_size=16)
    a_tree, _ = modifier.compute_forces_mod(pos, pos * 0, theta=0.3,
                                            tree=tree, use_cuda=False)
    a_fresh, _ = modifier.compute_forces_mod(pos, pos * 0, theta=0.3,
                                             use_cuda=False)
    np.testing.assert_allclose(a_tree, a_fresh, rtol=1e-6, atol=1e-8)
