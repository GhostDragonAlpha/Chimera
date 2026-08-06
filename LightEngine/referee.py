"""
Independent NumPy (float64, CPU) referee for the LightEngine kernel.

Implements the SAME two declared force laws as the kernel, written from the
specification rather than copied from the implementation.  Used by the test
suite to verify agreement before the full seed run.

Pre-registered tolerance: EPS_REF = 1e-3 relative on accelerations.
"""

import numpy as np
from LightEngine.constants import (
    G, K_WALL, K_BOND, R_WALL, R_BOND, R_C, P_WALL, EPS,
)

EPS_REF = 1e-3


def _distance_vectors(pos: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return displacement vectors (i<-j) and squared distances for all pairs."""
    # pos: (N, 3) float64
    diff = pos[:, None, :] - pos[None, :, :]  # diff[i,j] = r_i - r_j
    r2 = np.einsum("ijk,ijk->ij", diff, diff)
    return diff, r2


def compute_draw_ref(positions: np.ndarray,
                     masses: np.ndarray | None = None) -> np.ndarray:
    """
    Reference DRAW acceleration.

    F_i = sum_{j != i} G * m^2 * (r_j - r_i) / (|r|^2 + eps^2)^(3/2)
    With m = 1 for all points.
    """
    pos = np.asarray(positions, dtype=np.float64)
    n = pos.shape[0]
    diff = pos[None, :, :] - pos[:, None, :]  # diff[i,j] = r_j - r_i
    r2 = np.einsum("ijk,ijk->ij", diff, diff) + EPS * EPS
    np.fill_diagonal(r2, np.inf)  # remove self-interaction
    inv_r3 = r2 ** (-1.5)
    acc = G * np.einsum("ij,ijk->ik", inv_r3, diff)
    return acc


def compute_resistance_ref(positions: np.ndarray) -> np.ndarray:
    """
    Reference RESISTANCE acceleration.

    Neighbor list with cutoff r_c.  Per neighbor j != i:
      |r| < r_wall          : strong repulsion  a_i += K_WALL*(r_wall/|r|)^p * (r_i-r_j)/|r|
      r_wall <= |r| <= r_bond: bond spring      a_i += K_BOND*(|r|-r_bond)/(r_bond*|r|) * (r_j-r_i)
      |r| > r_c             : zero
    """
    pos = np.asarray(positions, dtype=np.float64)
    n = pos.shape[0]
    diff, r2 = _distance_vectors(pos)  # diff[i,j] = r_i - r_j
    np.fill_diagonal(r2, np.inf)
    r = np.sqrt(r2)

    # masks
    wall_mask = r < R_WALL
    bond_mask = (r >= R_WALL) & (r <= R_BOND)
    cutoff_mask = r <= R_C

    acc = np.zeros_like(pos)

    # wall: repulsive, direction away from j (diff = r_i - r_j)
    if wall_mask.any():
        f_wall = np.zeros_like(r)
        f_wall[wall_mask] = K_WALL * (R_WALL / r[wall_mask]) ** P_WALL / r[wall_mask]
        acc += np.einsum("ij,ijk->ik", f_wall, diff)

    # bond: spring, direction toward j ( -diff = r_j - r_i )
    if bond_mask.any():
        f_bond = np.zeros_like(r)
        f_bond[bond_mask] = K_BOND * (r[bond_mask] - R_BOND) / (R_BOND * r[bond_mask])
        acc += np.einsum("ij,ijk->ik", f_bond, -diff)

    return acc


def compute_forces_ref(positions: np.ndarray) -> np.ndarray:
    """Total acceleration = DRAW + RESISTANCE."""
    return compute_draw_ref(positions) + compute_resistance_ref(positions)


def relative_error(a: np.ndarray, b: np.ndarray) -> float:
    """Maximum relative L2 error over particles."""
    denom = np.linalg.norm(b, axis=1)
    denom = np.where(denom == 0, 1.0, denom)
    errs = np.linalg.norm(a - b, axis=1) / denom
    return float(np.max(errs))
