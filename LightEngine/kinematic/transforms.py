"""
Quaternion and homogeneous-transform helpers for Lane K1.

All functions are numpy-only and use float64.  Quaternions are stored as
[w, x, y, z] and represent an active rotation:  q.rotate(v) returns the
vector v rotated by q.

All numbers are either derived from the input quaternion or are constants
with cited sources; no free parameters are introduced.
"""

from __future__ import annotations

import numpy as np


# ---------------------------------------------------------------------------
# Quaternion basics
# ---------------------------------------------------------------------------
def normalize(q: np.ndarray) -> np.ndarray:
    """Return a unit quaternion in [w, x, y, z] form.

    DERIVED-GEOMETRY: normalization is required so that repeated composition
    of rotations does not drift.  Tolerance prevents division by zero for the
    identity quaternion input.
    """
    q = np.asarray(q, dtype=np.float64).reshape(4)
    n = float(np.linalg.norm(q))
    if n < 1e-12:
        return np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
    return q / n


def multiply(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Return the Hamilton product a * b (apply b first, then a).

    DERIVED-GEOMETRY: Hamilton product is the standard quaternion composition
    that matches rotation-matrix multiplication order.
    """
    a = normalize(a)
    b = normalize(b)
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return normalize(np.array([
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    ], dtype=np.float64))


def conjugate(q: np.ndarray) -> np.ndarray:
    """Return the conjugate (inverse for unit quaternions)."""
    q = normalize(q)
    return np.array([q[0], -q[1], -q[2], -q[3]], dtype=np.float64)


def rotate(q: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Rotate vector v by unit quaternion q using q * [0,v] * q^-1.

    DERIVED-GEOMETRY: this is the active rotation formula; it is equivalent to
    the rotation matrix form but avoids explicit matrix construction.
    """
    q = normalize(q)
    v = np.asarray(v, dtype=np.float64).reshape(3)
    qw, qx, qy, qz = q
    t = 2.0 * np.cross(q[1:], v)
    return v + qw * t + np.cross(q[1:], t)


# ---------------------------------------------------------------------------
# Axis-angle and matrix conversions
# ---------------------------------------------------------------------------
def from_axis_angle(axis: np.ndarray, angle: float) -> np.ndarray:
    """Return the unit quaternion for a right-handed rotation around axis.

    DERIVED-GEOMETRY: q = [cos(theta/2), sin(theta/2) * axis_hat].  Axis is
    normalized inside this function so callers may pass unnormalized axes.
    """
    axis = np.asarray(axis, dtype=np.float64).reshape(3)
    n = float(np.linalg.norm(axis))
    if n < 1e-12:
        return np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
    axis = axis / n
    half = 0.5 * float(angle)
    c = np.cos(half)
    s = np.sin(half)
    return np.array([c, s * axis[0], s * axis[1], s * axis[2]], dtype=np.float64)


def to_matrix(q: np.ndarray) -> np.ndarray:
    """Return the 3x3 rotation matrix for quaternion q (columns are image of
    the world basis vectors under the rotation).

    DERIVED-GEOMETRY: direct algebraic expansion of q * [0,v] * q^-1.
    """
    q = normalize(q)
    w, x, y, z = q
    return np.array([
        [1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - z * w), 2.0 * (x * z + y * w)],
        [2.0 * (x * y + z * w), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - x * w)],
        [2.0 * (x * z - y * w), 2.0 * (y * z + x * w), 1.0 - 2.0 * (x * x + y * y)],
    ], dtype=np.float64)


def from_matrix(R: np.ndarray) -> np.ndarray:
    """Return a unit quaternion from a 3x3 rotation matrix.

    DERIVED-GEOMETRY: Shepperd's method (trace branch) with a small epsilon to
    avoid numerical issues near the identity rotation.
    """
    R = np.asarray(R, dtype=np.float64).reshape(3, 3)
    trace = float(R[0, 0] + R[1, 1] + R[2, 2])
    eps = 1e-12
    if trace > eps:
        s = 0.5 / np.sqrt(trace + 1.0)
        w = 0.25 / s
        x = (R[2, 1] - R[1, 2]) * s
        y = (R[0, 2] - R[2, 0]) * s
        z = (R[1, 0] - R[0, 1]) * s
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = 2.0 * np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2])
        w = (R[2, 1] - R[1, 2]) / s
        x = 0.25 * s
        y = (R[0, 1] + R[1, 0]) / s
        z = (R[0, 2] + R[2, 0]) / s
    elif R[1, 1] > R[2, 2]:
        s = 2.0 * np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2])
        w = (R[0, 2] - R[2, 0]) / s
        x = (R[0, 1] + R[1, 0]) / s
        y = 0.25 * s
        z = (R[1, 2] + R[2, 1]) / s
    else:
        s = 2.0 * np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1])
        w = (R[1, 0] - R[0, 1]) / s
        x = (R[0, 2] + R[2, 0]) / s
        y = (R[1, 2] + R[2, 1]) / s
        z = 0.25 * s
    return normalize(np.array([w, x, y, z], dtype=np.float64))


def from_basis(x: np.ndarray, y: np.ndarray, z: np.ndarray) -> np.ndarray:
    """Return the quaternion whose rotation matrix has columns x, y, z.

    DERIVED-GEOMETRY: the input vectors are assumed orthonormal right-handed.
    """
    R = np.column_stack([
        np.asarray(x, dtype=np.float64).reshape(3),
        np.asarray(y, dtype=np.float64).reshape(3),
        np.asarray(z, dtype=np.float64).reshape(3),
    ])
    return from_matrix(R)


# ---------------------------------------------------------------------------
# Homogeneous transforms
# ---------------------------------------------------------------------------
def compose(T_a: np.ndarray, T_b: np.ndarray) -> np.ndarray:
    """Return the homogeneous matrix product T_a @ T_b.

    DERIVED-GEOMETRY: standard 4x4 matrix composition for SE(3).
    """
    return np.asarray(T_a, dtype=np.float64) @ np.asarray(T_b, dtype=np.float64)


def invert(T: np.ndarray) -> np.ndarray:
    """Return the inverse of a homogeneous transform.

    DERIVED-GEOMETRY: for T = [[R, p], [0, 1]], T^-1 = [[R^T, -R^T p], [0, 1]].
    """
    T = np.asarray(T, dtype=np.float64).reshape(4, 4)
    R = T[:3, :3]
    p = T[:3, 3]
    T_inv = np.eye(4, dtype=np.float64)
    T_inv[:3, :3] = R.T
    T_inv[:3, 3] = -R.T @ p
    return T_inv


def skew(v: np.ndarray) -> np.ndarray:
    """Return the 3x3 skew-symmetric matrix for vector v.

    DERIVED-GEOMETRY: [v]_x w = v x w for all vectors w.
    """
    v = np.asarray(v, dtype=np.float64).reshape(3)
    return np.array([
        [0.0, -v[2], v[1]],
        [v[2], 0.0, -v[0]],
        [-v[1], v[0], 0.0],
    ], dtype=np.float64)
