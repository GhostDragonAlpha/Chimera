"""Numba-JIT core for LightEngine.kinematic.dynamics (performance lane).

This module is the compiled tick for the 77-link rigid skeleton, compiled with
numba @njit(cache=True).  The operator's directive: these operations repeat for
every tick of every run of every membrane, so the inner loop is machine code,
not Python bytecode.

TWO VELOCITY SOLVERS, one position pass:

  * step_core        -- velocity-level SEQUENTIAL impulses (Gauss-Seidel,
                        Box2D lineage).  Kept as the reference/fallback scheme.
  * step_core_direct -- velocity-level DIRECT solve: assemble the full
                        constraint Jacobian for the tick, build K = J M^-1 J^T,
                        solve (K + eps I) lambda = -v_rel in ONE linear solve,
                        with an active-set pass for the unilateral rows
                        (ligaments, contact normals) and a Coulomb clamp on the
                        friction rows.

Why the direct solve exists (measured 2026-08-07, experiments at 85 ticks/s):
  Gauss-Seidel DIVERGES on this skeleton.  The mass ratio trunk:vertebra is
  ~2000:1 and slender-link axial inertia is ~1e-7 kg m^2 (I_inv ~ 1e7); with
  contacts in the system the iteration amplified instead of contracting --
  tick 1 fibula_L omega = 11.5 rad/s, tick 2 scapula_R omega = 2597, tick 3
  dead.  dt = 1e-4 blew up identically (not a CFL effect); 50 iterations blew
  up on tick 1 while 5 survived to tick 10 -- more iterations, faster
  divergence, the signature of a non-contracting Gauss-Seidel split.  Even
  Box2D-class iterative solvers are documented to fail beyond ~10:1 mass
  ratios.  A direct solve has no iteration to diverge: K is symmetric
  positive semidefinite by construction (K = J M^-1 J^T), and a small
  min-norm regularizer (eps = 1e-9 * trace(K)/m) handles the redundant rows
  that over-constrained bodies produce.

Both schemes share:
  1. integrate forces into velocities,
  2. solve constraints at VELOCITY level,
  3. integrate positions,
  4. a Baumgarte-style position stabilization pass that NEVER touches
     velocities (beta = 0.2, with the measured joint-play length d_eq as the
     slop band; full-strength projection was measured 2026-08-07 to over-damp
     the hinge pendulum -- the position pass exists to kill integration
     drift, not to do dynamics).

Design constraints:
  * fastmath is OFF: determinism beats a few percent.
  * Row ordering is fixed every tick (joints, rotation locks, ligaments,
    contacts), so the direct solve is bit-deterministic run to run.
  * Quaternion helpers mirror LightEngine.kinematic.transforms exactly,
    including the normalize() calls inside multiply/conjugate.

Fallback: dynamics.py dispatches here only when numba imports cleanly.
"""

from __future__ import annotations

import math

import numpy as np

try:
    from numba import njit
    _HAS_NUMBA = True
except Exception:  # pragma: no cover - numba is a project dependency
    _HAS_NUMBA = False

    def njit(*args, **kwargs):  # type: ignore
        def deco(fn):
            return fn
        return deco


GRAVITY = 9.80665   # ANATOMY-DATUM: standard gravity (matches dynamics.py).
MU = 0.70           # ANATOMY-DATUM: midpoint of skin-floor dry range [0.5, 0.9].
# Position-pass stiffness (Baumgarte beta).  DERIVED: matches BAUMGARTE_BETA
# in dynamics.py -- the standard drift-stabilization fraction.  The velocity
# solve does the dynamics; this pass removes only integration drift.
# beta = 1.0 measured 2026-08-07 to over-damp the hinge pendulum (one peak,
# never completed an oscillation); beta = 0.2 keeps drift below the slop band
# while leaving the dynamics untouched.
BETA = 0.2
# Angular-correction clamp, DERIVED: the position-pass rotations are
# linearizations that assume sin(theta) ~ theta.  Requiring |sin t - t| / t
# <= 1% gives t <= 0.244.  Beyond the clamp the linearized correction is wrong
# in kind, not in degree (measured 2026-08-07: unclamped corrections scrambled
# small-link orientations into pi-flips, omega saturating at pi/dt).
THETA_CLAMP = 0.24

# Active-set bookkeeping for step_core_direct rows.
_BILATERAL = 0
_UNILATERAL = 1     # lambda >= 0 required (ligament tension, contact normal)
_FRICTION = 2       # |lambda| <= MU * lambda of the paired normal row
_MOTOR = 3          # muscle row: target relative velocity, |lambda| <= lmax

_REC_JOINT_LIN = 0
_REC_JOINT_ANG = 1
_REC_LIGAMENT = 2
_REC_CONTACT = 3


# ---------------------------------------------------------------------------
# Quaternion helpers (exact ports of transforms.py, scalar math)
# ---------------------------------------------------------------------------
@njit(cache=True)
def _qnorm(q):
    n = math.sqrt(q[0] * q[0] + q[1] * q[1] + q[2] * q[2] + q[3] * q[3])
    if n < 1e-12:
        out = np.zeros(4, dtype=np.float64)
        out[0] = 1.0
        return out
    return q / n


@njit(cache=True)
def _qmul(a, b):
    a = _qnorm(a)
    b = _qnorm(b)
    aw, ax, ay, az = a[0], a[1], a[2], a[3]
    bw, bx, by, bz = b[0], b[1], b[2], b[3]
    out = np.empty(4, dtype=np.float64)
    out[0] = aw * bw - ax * bx - ay * by - az * bz
    out[1] = aw * bx + ax * bw + ay * bz - az * by
    out[2] = aw * by - ax * bz + ay * bw + az * bx
    out[3] = aw * bz + ax * by - ay * bx + az * bw
    return _qnorm(out)


@njit(cache=True)
def _qconj(q):
    q = _qnorm(q)
    out = np.empty(4, dtype=np.float64)
    out[0] = q[0]
    out[1] = -q[1]
    out[2] = -q[2]
    out[3] = -q[3]
    return out


@njit(cache=True)
def _qmat(q):
    q = _qnorm(q)
    w, x, y, z = q[0], q[1], q[2], q[3]
    R = np.empty((3, 3), dtype=np.float64)
    R[0, 0] = 1.0 - 2.0 * (y * y + z * z)
    R[0, 1] = 2.0 * (x * y - z * w)
    R[0, 2] = 2.0 * (x * z + y * w)
    R[1, 0] = 2.0 * (x * y + z * w)
    R[1, 1] = 1.0 - 2.0 * (x * x + z * z)
    R[1, 2] = 2.0 * (y * z - x * w)
    R[2, 0] = 2.0 * (x * z - y * w)
    R[2, 1] = 2.0 * (y * z + x * w)
    R[2, 2] = 1.0 - 2.0 * (x * x + y * y)
    return R


@njit(cache=True)
def _qfrom_axis_angle(axis, angle):
    n = math.sqrt(axis[0] * axis[0] + axis[1] * axis[1] + axis[2] * axis[2])
    out = np.zeros(4, dtype=np.float64)
    out[0] = 1.0
    if n < 1e-12:
        return out
    half = 0.5 * angle
    s = math.sin(half) / n
    out[0] = math.cos(half)
    out[1] = s * axis[0]
    out[2] = s * axis[1]
    out[3] = s * axis[2]
    return out


@njit(cache=True)
def _cross3(a, b):
    out = np.empty(3, dtype=np.float64)
    out[0] = a[1] * b[2] - a[2] * b[1]
    out[1] = a[2] * b[0] - a[0] * b[2]
    out[2] = a[0] * b[1] - a[1] * b[0]
    return out


@njit(cache=True)
def _norm3(v):
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


@njit(cache=True)
def _quat_derivative(q, omega):
    qw, qx, qy, qz = q[0], q[1], q[2], q[3]
    wx, wy, wz = omega[0], omega[1], omega[2]
    out = np.empty(4, dtype=np.float64)
    out[0] = 0.5 * (-wx * qx - wy * qy - wz * qz)
    out[1] = 0.5 * (wx * qw + wy * qz - wz * qy)
    out[2] = 0.5 * (wy * qw - wx * qz + wz * qx)
    out[3] = 0.5 * (wz * qw + wx * qy - wy * qx)
    return out


@njit(cache=True)
def _world_inertia_inv(q, inv_diag):
    R = _qmat(q)
    D = np.zeros((3, 3), dtype=np.float64)
    D[0, 0] = inv_diag[0]
    D[1, 1] = inv_diag[1]
    D[2, 2] = inv_diag[2]
    return R @ D @ R.T


@njit(cache=True)
def _premult_rotate(quat_i, axis, angle):
    """quat <- from_axis_angle(axis, angle) * quat (rotation about own COM).

    The angle is clamped to THETA_CLAMP: the position-pass correction is a
    linearization and is only valid inside the small-angle band.
    """
    if _norm3(axis) < 1e-12 or abs(angle) < 1e-12:
        return quat_i
    if angle > THETA_CLAMP:
        angle = THETA_CLAMP
    elif angle < -THETA_CLAMP:
        angle = -THETA_CLAMP
    dq = _qfrom_axis_angle(axis, angle)
    return _qmul(dq, quat_i)


@njit(cache=True)
def _locked_axes(dof, R_p, axes_ji, z_hat):
    """World-frame locked rotation axes for a joint (mirror of the sequential
    solver's convention).  Returns (la[3,3], n_locked)."""
    la = np.zeros((3, 3), dtype=np.float64)
    n_locked = 0
    if dof == 0:
        for ax in range(3):
            la[ax, ax] = 1.0
        n_locked = 3
    elif dof == 1:
        axis = R_p @ axes_ji[0]
        axis = axis / (_norm3(axis) + 1e-15)
        if abs(axis[2]) < 0.9:
            ref = z_hat
        else:
            ref = np.array([1.0, 0.0, 0.0], dtype=np.float64)
        u = _cross3(axis, ref)
        u = u / (_norm3(u) + 1e-15)
        la[0] = u
        la[1] = _cross3(axis, u)
        n_locked = 2
    elif dof == 2:
        ax1 = R_p @ axes_ji[0]
        ax2 = R_p @ axes_ji[1]
        lk = _cross3(ax1, ax2)
        nl = _norm3(lk)
        if nl < 1e-12:
            lk = _cross3(ax1, z_hat)
            nl = _norm3(lk)
        la[0] = lk / (nl + 1e-15)
        n_locked = 1
    return la, n_locked


@njit(cache=True)
def _lock_err_theta(q_p, q_c, q_rel0, R_p):
    """World-frame locked-axis error rotation vector of a joint (mode 4).

    Controller convention: q_err = q_rel * q_rel0^-1, axis in the parent's
    CURRENT local frame, rotated to world by R_p.  Projecting the result
    onto a locked axis L (from _locked_axes) gives the signed error the
    Baumgarte bias corrects; L is orthogonal to the free axes by
    construction, so no per-dof masking is needed at the call sites."""
    q_rel = _qmul(_qconj(q_p), q_c)
    if q_rel[0] < 0.0:
        q_rel = -q_rel
    q_err = _qmul(q_rel, _qconj(q_rel0))
    if q_err[0] < 0.0:
        q_err = -q_err
    s = _norm3(q_err[1:])
    if s < 1e-12:
        return np.zeros(3, dtype=np.float64)
    ang = 2.0 * math.atan2(s, q_err[0])
    return ang * (R_p @ (q_err[1:] / s))


# ---------------------------------------------------------------------------
# Position stabilization pass (shared by both velocity solvers).
# NEVER touches velocities: it exists to kill integration drift only.
#
# NOTE (measured 2026-08-08): there is deliberately NO contact penetration
# projection here.  The velocity solve holds the contact normal at vn = 0,
# so contacts do not drift; a position-level contact projection fought the
# joint projection over the slop band and pumped the full skeleton from
# vmax ~ 1 m/s to vmax ~ 220 m/s in 100 ticks (iters=0 stable, iters=20
# exploded; forefoot_R first).  Joints/locks/ligaments keep their gentle
# BETA projections: those were measured stable on every rig.
# ---------------------------------------------------------------------------
@njit(cache=True)
def position_pass(
    pos, quat, mass, inv_mass, inv_inertia_diag_local,
    joint_parent, joint_child, joint_dof, joint_axes,
    r_joint_parent_local, r_joint_child_local, joint_q_rel0,
    lig_idx_a, lig_idx_b, lig_off_a, lig_off_b, lig_rest,
    contact_link_idx, contact_off_local,
    contact_slop, n_proj_iters, do_rotation_locks,
    ghost_coinc, ghost_lig, ghost_lock,
    pos_pass_mode,
):
    # ghost_* are instrumentation accumulators (ghost-source probe,
    # 2026-08-08): every position-level ROTATION this pass applies to a
    # link's quat -- invisible in ang_vel -- is added to the block's
    # array.  Pure accounting: the physics is unchanged.
    #
    # pos_pass_mode 0 = legacy, 1 = GHOST-FREE (2026-08-08): joint
    # coincidence corrected by TRANSLATION ONLY (two meeting points
    # need no link rotation), and the ligament position projection
    # retired -- the ligaments already have their velocity-level sweep
    # (step section 5b); the position copy was a second, ghosting
    # application of the same constraint (ghost-source verdict:
    # coincidence<->ligament tug-of-war, 86% self-cancelling, the
    # residue folds the standing ankle).
    n_joints = joint_parent.shape[0]
    n_lig = lig_idx_a.shape[0]
    n_contacts = contact_link_idx.shape[0]
    z_hat = np.array([0.0, 0.0, 1.0], dtype=np.float64)

    for _it in range(n_proj_iters):
        # joint point coincidence (slop = d_eq joint play, same length scale
        # as contact_slop: both are lam * D_EQ_LU, the measured play length)
        for ji in range(n_joints):
            pa = joint_parent[ji]
            cb = joint_child[ji]
            if mass[pa] <= 0.0 and mass[cb] <= 0.0:
                continue
            R_p = _qmat(quat[pa])
            R_c = _qmat(quat[cb])
            r_p = R_p @ r_joint_parent_local[ji]
            r_c = R_c @ r_joint_child_local[ji]
            p_p = pos[pa] + r_p
            p_c = pos[cb] + r_c
            delta = p_c - p_p
            err = _norm3(delta)
            if err <= contact_slop:
                continue
            n = delta / err
            I_inv_p = _world_inertia_inv(quat[pa], inv_inertia_diag_local[pa])
            I_inv_c = _world_inertia_inv(quat[cb], inv_inertia_diag_local[cb])
            rn_p = _cross3(r_p, n)
            rn_c = _cross3(r_c, n)
            w_p = inv_mass[pa] + rn_p @ (I_inv_p @ rn_p)
            w_c = inv_mass[cb] + rn_c @ (I_inv_c @ rn_c)
            denom = w_p + w_c
            if denom <= 1e-15:
                continue
            if pos_pass_mode == 1:
                # GHOST-FREE: translation only, inverse-mass split --
                # no quat is touched, so no ghost rotation can exist.
                denom_m = inv_mass[pa] + inv_mass[cb]
                if denom_m <= 1e-15:
                    continue
                c_mag = BETA * (err - contact_slop) / denom_m
                if mass[pa] > 0.0:
                    pos[pa] = pos[pa] + inv_mass[pa] * c_mag * n
                if mass[cb] > 0.0:
                    pos[cb] = pos[cb] - inv_mass[cb] * c_mag * n
                continue
            c_mag = BETA * (err - contact_slop) / denom
            if mass[pa] > 0.0:
                pos[pa] = pos[pa] + inv_mass[pa] * c_mag * n
                dtheta_p = I_inv_p @ (c_mag * rn_p)
                if _norm3(dtheta_p) > 1e-15:
                    quat[pa] = _premult_rotate(quat[pa], dtheta_p, _norm3(dtheta_p))
                    ghost_coinc[pa] = ghost_coinc[pa] + dtheta_p
            if mass[cb] > 0.0:
                pos[cb] = pos[cb] - inv_mass[cb] * c_mag * n
                dtheta_c = I_inv_c @ (c_mag * rn_c)
                if _norm3(dtheta_c) > 1e-15:
                    quat[cb] = _premult_rotate(quat[cb], -dtheta_c, _norm3(dtheta_c))
                    ghost_coinc[cb] = ghost_coinc[cb] - dtheta_c

        # rotation-lock position stabilization (small-angle, frame-fixed)
        # lock modes: 0=off, 1=both (legacy), 2=velocity rows only,
        # 3=position stabilization only (toxic-component A/B, 2026-08-08).
        if do_rotation_locks == 1 or do_rotation_locks == 3:
            for ji in range(n_joints):
                pa = joint_parent[ji]
                cb = joint_child[ji]
                if mass[pa] <= 0.0 and mass[cb] <= 0.0:
                    continue
                dof = joint_dof[ji]
                if dof == 3:
                    continue
                q_p = quat[pa]
                q_c = quat[cb]
                R_p = _qmat(q_p)
                q_rel = _qmul(_qconj(q_p), q_c)
                if q_rel[0] < 0.0:
                    q_rel = -q_rel
                q_rel0 = joint_q_rel0[ji]
                q_err = _qmul(_qconj(q_rel0), q_rel)
                if q_err[0] < 0.0:
                    q_err = -q_err
                sin_half = _norm3(q_err[1:])
                if sin_half < 1e-12:
                    continue
                rel_axis = q_err[1:] / sin_half
                rel_angle = 2.0 * math.atan2(sin_half, q_err[0])
                # FRAME FIX: q_rel/q_err live in the parent's LOCAL frame.
                theta = rel_angle * (R_p @ rel_axis)
                if dof == 0:
                    theta_locked = theta.copy()
                elif dof == 1:
                    axis = R_p @ joint_axes[ji, 0]
                    axis = axis / (_norm3(axis) + 1e-15)
                    theta_locked = theta - (theta @ axis) * axis
                elif dof == 2:
                    ax1 = R_p @ joint_axes[ji, 0]
                    ax2 = R_p @ joint_axes[ji, 1]
                    locked_axis = _cross3(ax1, ax2)
                    n_lk = _norm3(locked_axis)
                    if n_lk < 1e-12:
                        locked_axis = _cross3(ax1, z_hat)
                        n_lk = _norm3(locked_axis)
                    locked_axis = locked_axis / (n_lk + 1e-15)
                    theta_locked = (theta @ locked_axis) * locked_axis
                else:
                    continue
                err_angle = _norm3(theta_locked)
                if err_angle < 1e-12:
                    continue
                err_axis = theta_locked / err_angle
                I_inv_p = _world_inertia_inv(q_p, inv_inertia_diag_local[pa])
                I_inv_c = _world_inertia_inv(q_c, inv_inertia_diag_local[cb])
                ia = err_axis @ (I_inv_p @ err_axis)
                ib = err_axis @ (I_inv_c @ err_axis)
                denom = ia + ib
                if denom <= 1e-15:
                    continue
                alpha_p = BETA * ia / denom
                alpha_c = BETA * ib / denom
                if mass[pa] > 0.0:
                    quat[pa] = _premult_rotate(quat[pa], err_axis, alpha_p * err_angle)
                    ghost_lock[pa] = ghost_lock[pa] + err_axis * (alpha_p * err_angle)
                if mass[cb] > 0.0:
                    quat[cb] = _premult_rotate(quat[cb], err_axis, -alpha_c * err_angle)
                    ghost_lock[cb] = ghost_lock[cb] - err_axis * (alpha_c * err_angle)

        # ligament unilateral distance projection (positions only)
        # GHOST-FREE mode retires this block: the velocity sweep (step
        # section 5b) already enforces the ligaments; this copy ghosts.
        if pos_pass_mode == 0:
            n_lig_eff = n_lig
        else:
            n_lig_eff = 0
        for li in range(n_lig_eff):
            ia = lig_idx_a[li]
            ib = lig_idx_b[li]
            if mass[ia] <= 0.0 and mass[ib] <= 0.0:
                continue
            Ra = _qmat(quat[ia])
            Rb = _qmat(quat[ib])
            r_a = Ra @ lig_off_a[li]
            r_b = Rb @ lig_off_b[li]
            pa_v = pos[ia] + r_a
            pb_v = pos[ib] + r_b
            vec = pb_v - pa_v
            Llen = _norm3(vec)
            if Llen <= lig_rest[li] + 1e-15:
                continue
            n = vec / Llen
            delta = Llen - lig_rest[li]
            I_inv_a = _world_inertia_inv(quat[ia], inv_inertia_diag_local[ia])
            I_inv_b = _world_inertia_inv(quat[ib], inv_inertia_diag_local[ib])
            rn_a = _cross3(r_a, n)
            rn_b = _cross3(r_b, n)
            w_a = inv_mass[ia] + rn_a @ (I_inv_a @ rn_a)
            w_b = inv_mass[ib] + rn_b @ (I_inv_b @ rn_b)
            denom = w_a + w_b
            if denom <= 1e-15:
                continue
            c_mag = BETA * delta / denom
            if mass[ia] > 0.0:
                pos[ia] = pos[ia] + inv_mass[ia] * c_mag * n
                dtheta_a = I_inv_a @ (c_mag * rn_a)
                if _norm3(dtheta_a) > 1e-15:
                    quat[ia] = _premult_rotate(quat[ia], dtheta_a, _norm3(dtheta_a))
                    ghost_lig[ia] = ghost_lig[ia] + dtheta_a
            if mass[ib] > 0.0:
                pos[ib] = pos[ib] - inv_mass[ib] * c_mag * n
                dtheta_b = I_inv_b @ (c_mag * rn_b)
                if _norm3(dtheta_b) > 1e-15:
                    quat[ib] = _premult_rotate(quat[ib], -dtheta_b, _norm3(dtheta_b))
                    ghost_lig[ib] = ghost_lig[ib] - dtheta_b

        # (no contact projection here -- see the position_pass docstring:
        # contacts are held by the velocity solve, and a position-level
        # projection was measured to pump energy into the joint chain)


@njit(cache=True)
def _chol_solve(A, b):
    """Solve A x = b for SPD A via Cholesky (L L^T), pure numba loops.

    Why not np.linalg.solve: the LAPACK path natively HEAP-CORRUPTED on this
    platform (Windows, Python 3.14) when called per tick on the ~500x500
    skeleton K -- crash reproduced deterministically under pytest, absent
    under NUMBA_BOUNDSCHECK=1 (2026-08-08).  A hand-rolled Cholesky has no
    external library in the loop, is ~2x faster than LU for SPD systems, and
    is bit-deterministic.  A is assumed already regularized (K + eps I);
    the diagonal floor below guards pure numerical dust only.
    """
    n = b.shape[0]
    L = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(i + 1):
            s = A[i, j]
            for k in range(j):
                s = s - L[i, k] * L[j, k]
            if i == j:
                if s < 1e-30:
                    s = 1e-30
                L[i, i] = math.sqrt(s)
            else:
                L[i, j] = s / L[j, j]
    y = np.zeros(n, dtype=np.float64)
    for i in range(n):
        s = b[i]
        for k in range(i):
            s = s - L[i, k] * y[k]
        y[i] = s / L[i, i]
    x = np.zeros(n, dtype=np.float64)
    for i in range(n - 1, -1, -1):
        s = y[i]
        for k in range(i + 1, n):
            s = s - L[k, i] * x[k]
        x[i] = s / L[i, i]
    return x


# ---------------------------------------------------------------------------
# Velocity solver A: sequential impulses (Gauss-Seidel, Box2D lineage).
# Reference/fallback scheme; DIVERGES at this skeleton's mass ratios -- see
# the module docstring.  Kept for comparison experiments (state["solver"]).
# ---------------------------------------------------------------------------
@njit(cache=True)
def step_core(
    pos, quat, lin_vel, ang_vel,
    mass, inv_mass, inertia_diag_local, inv_inertia_diag_local,
    joint_parent, joint_child, joint_dof, joint_axes,
    r_joint_parent_local, r_joint_child_local, joint_q_rel0,
    lig_idx_a, lig_idx_b, lig_off_a, lig_off_b, lig_rest, lig_fmax,
    contact_link_idx, contact_off_local,
    contact_slop, dt, n_proj_iters,
    do_rotation_locks,
    ext_force, ext_torque,
    motor_parent, motor_child, motor_joint, motor_axis, motor_target,
    motor_lmax, motor_impulses,
    joint_impulses_lin, joint_impulses_ang,
    lig_impulses_lin, lig_impulses_ang,
    contact_impulses,
    ghost_coinc, ghost_lig, ghost_lock,
    pos_pass_mode,
):
    """One tick, in place.  Impulse arrays are zeroed by the caller and
    accumulated from the velocity pass (that is where the physics is).

    Motor rows are NOT implemented in this scheme (it diverges at this
    skeleton's mass ratios anyway -- module docstring); the muscle lane
    runs on the direct solve.  The parameters are accepted and ignored."""
    n_links = pos.shape[0]
    n_joints = joint_parent.shape[0]
    n_lig = lig_idx_a.shape[0]
    n_contacts = contact_link_idx.shape[0]

    z_hat = np.array([0.0, 0.0, 1.0], dtype=np.float64)

    # ---- 1. integrate external forces (gravity + caller-supplied) ----
    for i in range(n_links):
        if mass[i] <= 0.0:
            continue
        lin_vel[i, 2] = lin_vel[i, 2] - dt * GRAVITY
        lin_vel[i] = lin_vel[i] + dt * inv_mass[i] * ext_force[i]
        I_inv_i = _world_inertia_inv(quat[i], inv_inertia_diag_local[i])
        ang_vel[i] = ang_vel[i] + dt * (I_inv_i @ ext_torque[i])

    # ---- 2. velocity-level sequential impulses ----
    for _it in range(n_proj_iters):
        # joints: point coincidence along all 3 world axes
        for ji in range(n_joints):
            pa = joint_parent[ji]
            cb = joint_child[ji]
            R_p = _qmat(quat[pa])
            R_c = _qmat(quat[cb])
            r_p = R_p @ r_joint_parent_local[ji]
            r_c = R_c @ r_joint_child_local[ji]
            I_inv_p = _world_inertia_inv(quat[pa], inv_inertia_diag_local[pa])
            I_inv_c = _world_inertia_inv(quat[cb], inv_inertia_diag_local[cb])
            v_rel = (lin_vel[cb] + _cross3(ang_vel[cb], r_c)) - (
                lin_vel[pa] + _cross3(ang_vel[pa], r_p))
            for ax in range(3):
                a = np.zeros(3, dtype=np.float64)
                a[ax] = 1.0
                rn_p = _cross3(r_p, a)
                rn_c = _cross3(r_c, a)
                K = inv_mass[pa] + inv_mass[cb] \
                    + rn_p @ (I_inv_p @ rn_p) + rn_c @ (I_inv_c @ rn_c)
                if K <= 1e-15:
                    continue
                j = -v_rel[ax] / K
                jv = j * a
                lin_vel[cb] = lin_vel[cb] + inv_mass[cb] * jv
                ang_vel[cb] = ang_vel[cb] + I_inv_c @ _cross3(r_c, jv)
                lin_vel[pa] = lin_vel[pa] - inv_mass[pa] * jv
                ang_vel[pa] = ang_vel[pa] - I_inv_p @ _cross3(r_p, jv)
                joint_impulses_lin[ji] = joint_impulses_lin[ji] + jv
                joint_impulses_ang[ji] = joint_impulses_ang[ji] + _cross3(r_c, jv)

        # rotation locks at velocity level
        # lock modes: 0=off, 1=both (legacy), 2=velocity rows only,
        # 3=position stabilization only, 4=velocity rows with a Baumgarte
        # bias (position error carried INSIDE the velocity row: mode 2
        # measured drifting, mode 3 measured pumping, 2026-08-08).
        if do_rotation_locks != 0 and do_rotation_locks != 3:
            for ji in range(n_joints):
                pa = joint_parent[ji]
                cb = joint_child[ji]
                dof = joint_dof[ji]
                if dof == 3:
                    continue
                R_p = _qmat(quat[pa])
                I_inv_p = _world_inertia_inv(quat[pa], inv_inertia_diag_local[pa])
                I_inv_c = _world_inertia_inv(quat[cb], inv_inertia_diag_local[cb])
                w_rel = ang_vel[cb] - ang_vel[pa]
                la, n_locked = _locked_axes(dof, R_p, joint_axes[ji], z_hat)
                if do_rotation_locks == 4:
                    theta = _lock_err_theta(quat[pa], quat[cb],
                                            joint_q_rel0[ji], R_p)
                else:
                    theta = np.zeros(3, dtype=np.float64)
                for k in range(n_locked):
                    L = la[k]
                    K = L @ ((I_inv_p + I_inv_c) @ L)
                    if K <= 1e-15:
                        continue
                    j = (-(w_rel @ L) - BETA * (theta @ L) / dt) / K
                    jv = j * L
                    ang_vel[cb] = ang_vel[cb] + I_inv_c @ jv
                    ang_vel[pa] = ang_vel[pa] - I_inv_p @ jv
                    joint_impulses_ang[ji] = joint_impulses_ang[ji] + jv

        # ligaments: unilateral, only when taut and separating
        for li in range(n_lig):
            ia = lig_idx_a[li]
            ib = lig_idx_b[li]
            Ra = _qmat(quat[ia])
            Rb = _qmat(quat[ib])
            r_a = Ra @ lig_off_a[li]
            r_b = Rb @ lig_off_b[li]
            pa_v = pos[ia] + r_a
            pb_v = pos[ib] + r_b
            vec = pb_v - pa_v
            Llen = _norm3(vec)
            if Llen <= lig_rest[li] or Llen < 1e-15:
                continue
            n = vec / Llen
            I_inv_a = _world_inertia_inv(quat[ia], inv_inertia_diag_local[ia])
            I_inv_b = _world_inertia_inv(quat[ib], inv_inertia_diag_local[ib])
            rn_a = _cross3(r_a, n)
            rn_b = _cross3(r_b, n)
            K = inv_mass[ia] + inv_mass[ib] \
                + rn_a @ (I_inv_a @ rn_a) + rn_b @ (I_inv_b @ rn_b)
            if K <= 1e-15:
                continue
            v_sep = ((lin_vel[ib] + _cross3(ang_vel[ib], r_b)) - (
                lin_vel[ia] + _cross3(ang_vel[ia], r_a))) @ n
            if v_sep <= 0.0:
                continue
            j = -v_sep / K
            # force-limit membrane: an overstretched ligament YIELDS at
            # its physiological ceiling (f_max * dt per tick, counting
            # what earlier iterations already applied); f_max <= 0 is
            # the legacy unlimited row.
            if lig_fmax[li] > 0.0:
                used = lig_impulses_lin[li] @ n
                avail = lig_fmax[li] * dt - used
                if avail <= 0.0:
                    continue
                if -j > avail:
                    j = -avail
            jv = j * n
            lin_vel[ib] = lin_vel[ib] + inv_mass[ib] * jv
            ang_vel[ib] = ang_vel[ib] + I_inv_b @ _cross3(r_b, jv)
            lin_vel[ia] = lin_vel[ia] - inv_mass[ia] * jv
            ang_vel[ia] = ang_vel[ia] - I_inv_a @ _cross3(r_a, jv)
            # reaction ON body A is -jv (A pulled toward B when taut)
            lig_impulses_lin[li] = lig_impulses_lin[li] - jv
            lig_impulses_ang[li] = lig_impulses_ang[li] - _cross3(r_a, jv)

        # contacts: unilateral normal + Coulomb friction, inelastic
        for ci in range(n_contacts):
            li = contact_link_idx[ci]
            if mass[li] <= 0.0:
                continue
            R = _qmat(quat[li])
            r = R @ contact_off_local[ci]
            p_w = pos[li] + r
            if p_w[2] >= contact_slop:
                continue
            I_inv = _world_inertia_inv(quat[li], inv_inertia_diag_local[li])
            v_p = lin_vel[li] + _cross3(ang_vel[li], r)
            rn = _cross3(r, z_hat)
            K_n = inv_mass[li] + rn @ (I_inv @ rn)
            if K_n <= 1e-15:
                continue
            vn = v_p @ z_hat
            j_n = 0.0
            if vn < 0.0:
                j_n = -vn / K_n
                jv = j_n * z_hat
                lin_vel[li] = lin_vel[li] + inv_mass[li] * jv
                ang_vel[li] = ang_vel[li] + I_inv @ _cross3(r, jv)
                contact_impulses[ci] = contact_impulses[ci] + jv
            v_t = v_p - vn * z_hat
            vt_mag = _norm3(v_t)
            if vt_mag > 1e-12:
                t_dir = v_t / vt_mag
                rn_t = _cross3(r, t_dir)
                K_t = inv_mass[li] + rn_t @ (I_inv @ rn_t)
                if K_t > 1e-15:
                    j_t = min(vt_mag / K_t, MU * j_n)
                    jv_t = -j_t * t_dir
                    lin_vel[li] = lin_vel[li] + inv_mass[li] * jv_t
                    ang_vel[li] = ang_vel[li] + I_inv @ _cross3(r, jv_t)
                    contact_impulses[ci] = contact_impulses[ci] + jv_t

    # ---- 3. integrate positions ----
    for i in range(n_links):
        if mass[i] <= 0.0:
            continue
        pos[i] = pos[i] + dt * lin_vel[i]
        quat[i] = _qnorm(quat[i] + dt * _quat_derivative(quat[i], ang_vel[i]))

    # ---- 4. position stabilization (NEVER touches velocities) ----
    position_pass(
        pos, quat, mass, inv_mass, inv_inertia_diag_local,
        joint_parent, joint_child, joint_dof, joint_axes,
        r_joint_parent_local, r_joint_child_local, joint_q_rel0,
        lig_idx_a, lig_idx_b, lig_off_a, lig_off_b, lig_rest,
        contact_link_idx, contact_off_local,
        contact_slop, n_proj_iters, do_rotation_locks,
        ghost_coinc, ghost_lig, ghost_lock,
        pos_pass_mode,
    )


# ---------------------------------------------------------------------------
# Velocity solver B: the direct solve.  One K = J M^-1 J^T assembly + one
# dense linear solve per tick (+ up to 3 active-set re-solves).  No
# iteration, so no Gauss-Seidel divergence at extreme mass ratios.
# ---------------------------------------------------------------------------
@njit(cache=True)
def step_core_direct(
    pos, quat, lin_vel, ang_vel,
    mass, inv_mass, inertia_diag_local, inv_inertia_diag_local,
    joint_parent, joint_child, joint_dof, joint_axes,
    r_joint_parent_local, r_joint_child_local, joint_q_rel0,
    lig_idx_a, lig_idx_b, lig_off_a, lig_off_b, lig_rest, lig_fmax,
    contact_link_idx, contact_off_local,
    contact_slop, dt, n_proj_iters,
    do_rotation_locks,
    ext_force, ext_torque,
    motor_parent, motor_child, motor_joint, motor_axis, motor_target,
    motor_lmax, motor_impulses,
    joint_impulses_lin, joint_impulses_ang,
    lig_impulses_lin, lig_impulses_ang,
    contact_impulses,
    ghost_coinc, ghost_lig, ghost_lock,
    contacts_in_solve,
    contact_friction,
    pos_pass_mode,
    contact_prev_n,
):
    """One tick, in place.  Impulse arrays are zeroed by the caller and filled
    from the solved lambdas (lambda IS the impulse along its row).

    Motor rows are the muscle channel: pure angular rows with a target
    relative velocity (rad/s) and a hard impulse bound |lambda| <= lmax
    (the physiology torque cap x dt).  They are solved INSIDE the same
    K system as the joint coincidence rows, so the muscle impulse and the
    joint reaction are consistent -- an external pre-solve torque kick is
    not (measured 2026-08-08: ext-couple actuation whipped light links,
    wmax 2000 rad/s, while the supported trunk barely moved).

    contacts_in_solve != 0 (v3a): ground-contact normal rows and their
    two pyramid friction rows are assembled into the SAME K system as the
    joints and motors, so the ground reaction is decided simultaneously
    with the joint coincidence and the muscle impulse -- not one phase
    later in a sweep.  Both inequalities are enforced INSIDE the active-set
    re-solve: lift-off by the unilateral rule (lambda_n < 0 drops the row),
    the friction cone (|lambda_t| <= MU * lambda_n) by fix-at-bound, apply,
    remove -- exactly the motor-row idiom, never a post-solve lambda clamp
    (the K2 pump, +10.5 kJ / 2000 ticks).  A dropped normal row takes its
    friction rows to zero with it.  With the flag off (default) the feet
    are grounded by the post-solve sequential sweep, the pre-v3a path.

    contact_friction == 0 (v3d instrumentation): skip the pyramid friction
    rows (normals only).  contact_friction == 2 (v3e hybrid): normals in
    the solve, friction back in the post-solve sweep with the cone bound
    MU x the solve's normal impulse -- sweep clamping is dissipative by
    construction, which the in-solve cone fix was measured not to be
    (v3d: simmer pump, supercritical at tick 7 713).  Default 1: the full
    cone in-solve (v3a), kept for A/B.  contact_friction == 3 (warm-start
    cone, the friction-placement membrane 2026-08-08): friction rows in
    the solve like mode 1, but the cone bound is contact_prev_n -- the
    PREVIOUS TICK's solved normal impulse per contact, fixed all tick,
    so the bound is never revised intra-tick (the v3d pump's address)
    while friction stays simultaneous with the motors (the friction-fork
    verdict: the post-solve sweep overwrites the ankle servo's booked
    rotation, wrong-way at 100% of samples).  FALSIFIED 2026-08-08: the
    staleness starves friction while the normals load (MAIN falls @434
    with muscles on).  contact_friction == 4 (frozen first-solve cone):
    friction rows in the solve, bound = MU x the FIRST attempt's solved
    lambda_n per contact, frozen for the rest of the tick --
    simultaneous (this tick, the warm-start falsifier) and unrevised
    (the v3d pump's address) at once.  FALSIFIED 2026-08-08: not a
    simmer, a launch (KE 1.05e8 J) -- fix-at-bound with ANY
    pre-computed bound mismatches the final lambda_n with systematic
    sign.  contact_friction == 5 (muscle-exclusion membrane): the
    v3e hybrid sweep (dissipative, long-protocol stable) with the
    muscle channel's own contribution to the contact-point velocity
    EXCLUDED from the tangential kill -- friction opposes the
    world's sliding, not the muscle's command (the friction-fork
    verdict: the mode-2 sweep overwrites the ankle servo's booked
    rotation, wrong-way at 100% of samples)."""
    n_links = pos.shape[0]
    n_joints = joint_parent.shape[0]
    n_lig = lig_idx_a.shape[0]
    n_contacts = contact_link_idx.shape[0]
    n_motors = motor_parent.shape[0]

    z_hat = np.array([0.0, 0.0, 1.0], dtype=np.float64)

    # ---- 1. integrate external forces (gravity + caller-supplied) ----
    for i in range(n_links):
        if mass[i] <= 0.0:
            continue
        lin_vel[i, 2] = lin_vel[i, 2] - dt * GRAVITY
        lin_vel[i] = lin_vel[i] + dt * inv_mass[i] * ext_force[i]

    # World inverse inertia per body (needed by assembly and application).
    I_inv = np.zeros((n_links, 3, 3), dtype=np.float64)
    for i in range(n_links):
        if mass[i] > 0.0:
            I_inv[i] = _world_inertia_inv(quat[i], inv_inertia_diag_local[i])

    # Caller-supplied torques: dw = dt * I_world^-1 @ tau (muscle channel).
    for i in range(n_links):
        if mass[i] <= 0.0:
            continue
        ang_vel[i] = ang_vel[i] + dt * (I_inv[i] @ ext_torque[i])

    # ---- 2. assemble constraint rows (joints, locks, motors, contacts) ----
    # Ligaments stay OUT of the direct solve: clamping their lambdas after
    # the equality solve breaks K lambda = -v_rel and pumps energy (measured
    # 2026-08-08: +10.5 kJ over 2000 ticks on the full skeleton).  They run
    # as sequential sweeps AFTER the direct solve, where per-iteration
    # clamping is dissipative.  Ground contacts enter the solve ONLY when
    # contacts_in_solve != 0 (v3a): both inequalities are resolved INSIDE
    # the active-set re-solve below (lift-off by the unilateral rule, the
    # friction cone by fix-at-bound), never by a post-solve lambda clamp.
    # Each row: constraint  J_a . V_a + J_b . V_b = 0  where V is the
    # generalized velocity (v, w) and J the (lin, ang) pair.  Sign
    # convention: relative velocity of the B side minus the A side along the
    # row direction, so J_b = (n, r_b x n), J_a = (-n, -r_a x n).
    rows_max = 6 * n_joints + n_motors + 3 * n_contacts + 1
    rb_a = np.full(rows_max, -1, dtype=np.int64)
    rb_b = np.full(rows_max, -1, dtype=np.int64)
    jla = np.zeros((rows_max, 3), dtype=np.float64)
    jaa = np.zeros((rows_max, 3), dtype=np.float64)
    jlb = np.zeros((rows_max, 3), dtype=np.float64)
    jab = np.zeros((rows_max, 3), dtype=np.float64)
    kind = np.zeros(rows_max, dtype=np.int64)
    pair = np.full(rows_max, -1, dtype=np.int64)
    rec_t = np.zeros(rows_max, dtype=np.int64)
    rec_i = np.zeros(rows_max, dtype=np.int64)
    mid = np.full(rows_max, -1, dtype=np.int64)
    # per-row velocity targets for the rhs (0 everywhere except mode-4
    # Baumgarte lock rows; motor rows override via motor_target below)
    row_bias = np.zeros(rows_max, dtype=np.float64)
    n_rows = 0

    # joints: point coincidence along all 3 world axes
    for ji in range(n_joints):
        pa = joint_parent[ji]
        cb = joint_child[ji]
        R_p = _qmat(quat[pa])
        R_c = _qmat(quat[cb])
        r_p = R_p @ r_joint_parent_local[ji]
        r_c = R_c @ r_joint_child_local[ji]
        for ax in range(3):
            n = np.zeros(3, dtype=np.float64)
            n[ax] = 1.0
            rb_a[n_rows] = pa
            rb_b[n_rows] = cb
            jla[n_rows] = -n
            jaa[n_rows] = -_cross3(r_p, n)
            jlb[n_rows] = n
            jab[n_rows] = _cross3(r_c, n)
            kind[n_rows] = _BILATERAL
            rec_t[n_rows] = _REC_JOINT_LIN
            rec_i[n_rows] = ji
            n_rows += 1

    # rotation locks: pure angular rows on the locked axes
    # lock modes: 0=off, 1=both (legacy), 2=velocity rows only,
    # 3=position stabilization only, 4=velocity rows with a Baumgarte
    # bias (position error carried INSIDE the row's rhs: mode 2 measured
    # drifting, mode 3 measured pumping, 2026-08-08).
    if do_rotation_locks != 0 and do_rotation_locks != 3:
        for ji in range(n_joints):
            pa = joint_parent[ji]
            cb = joint_child[ji]
            dof = joint_dof[ji]
            if dof == 3:
                continue
            R_p = _qmat(quat[pa])
            la, n_locked = _locked_axes(dof, R_p, joint_axes[ji], z_hat)
            theta = np.zeros(3, dtype=np.float64)
            if do_rotation_locks == 4:
                theta = _lock_err_theta(quat[pa], quat[cb],
                                        joint_q_rel0[ji], R_p)
            for k in range(n_locked):
                L = la[k]
                rb_a[n_rows] = pa
                rb_b[n_rows] = cb
                jaa[n_rows] = -L
                jab[n_rows] = L
                kind[n_rows] = _BILATERAL
                if do_rotation_locks == 4:
                    row_bias[n_rows] = -BETA * (theta @ L) / dt
                rec_t[n_rows] = _REC_JOINT_ANG
                rec_i[n_rows] = ji
                n_rows += 1

    # muscle motors: pure angular rows on the actuated free axes, with a
    # target relative velocity and a hard impulse bound (applied below).
    # rec_t is _REC_JOINT_ANG so the LIMIT meter reads the muscle's share of
    # the bone load; mid carries the motor index for the target/bound lookup.
    for mi in range(n_motors):
        L = motor_axis[mi]
        rb_a[n_rows] = motor_parent[mi]
        rb_b[n_rows] = motor_child[mi]
        jaa[n_rows] = -L
        jab[n_rows] = L
        kind[n_rows] = _MOTOR
        rec_t[n_rows] = _REC_JOINT_ANG
        rec_i[n_rows] = motor_joint[mi]
        mid[n_rows] = mi
        n_rows += 1

    # ground contacts (v3a, only when contacts_in_solve != 0): one
    # unilateral normal row + two pyramid friction rows per active contact
    # point, solved INSIDE the same K system as joints and motors.  The
    # ground is immovable, so each row is single-body (B side only).
    # Friction rows pair to their normal row; the cone bound is enforced
    # inside the active-set re-solve below.
    if contacts_in_solve != 0:
        for ci in range(n_contacts):
            li = contact_link_idx[ci]
            if mass[li] <= 0.0:
                continue
            R = _qmat(quat[li])
            r = R @ contact_off_local[ci]
            p_w = pos[li] + r
            if p_w[2] >= contact_slop:
                continue
            normal_row = n_rows
            rb_b[n_rows] = li
            jlb[n_rows] = z_hat
            jab[n_rows] = _cross3(r, z_hat)
            kind[n_rows] = _UNILATERAL
            rec_t[n_rows] = _REC_CONTACT
            rec_i[n_rows] = ci
            n_rows += 1
            # friction rows enter the solve in mode 1 (full cone
            # in-solve, v3a -- measured leaky on the long protocol, kept
            # for A/B), mode 3 (warm-start cone: bound fixed from the
            # previous tick's normal impulse -- FALSIFIED 2026-08-08,
            # staleness starves the settle), and mode 4 (frozen
            # first-solve cone: bound = MU x the first attempt's
            # lambda_n, never recomputed intra-tick).  Mode 0: no
            # friction anywhere (v3d instrument).  Mode 2 (hybrid,
            # v3e): friction runs in the sweep below.
            if contact_friction not in (1, 3, 4):
                continue
            for t_ax in range(2):
                t = np.zeros(3, dtype=np.float64)
                t[t_ax] = 1.0
                rb_b[n_rows] = li
                jlb[n_rows] = t
                jab[n_rows] = _cross3(r, t)
                kind[n_rows] = _FRICTION
                pair[n_rows] = normal_row
                rec_t[n_rows] = _REC_CONTACT
                rec_i[n_rows] = ci
                n_rows += 1

    # ---- 3. body->rows incidence (CSR) ----
    counts = np.zeros(n_links, dtype=np.int64)
    for r in range(n_rows):
        if rb_a[r] >= 0:
            counts[rb_a[r]] += 1
        if rb_b[r] >= 0:
            counts[rb_b[r]] += 1
    starts = np.zeros(n_links + 1, dtype=np.int64)
    for b in range(n_links):
        starts[b + 1] = starts[b] + counts[b]
    body_rows = np.empty(starts[n_links], dtype=np.int64)
    cursor = starts[:n_links].copy()
    for r in range(n_rows):
        if rb_a[r] >= 0:
            body_rows[cursor[rb_a[r]]] = r
            cursor[rb_a[r]] += 1
        if rb_b[r] >= 0:
            body_rows[cursor[rb_b[r]]] = r
            cursor[rb_b[r]] += 1

    # ---- 4. active-set direct solve ----
    active = np.ones(rows_max, dtype=np.bool_)
    lam_full = np.zeros(rows_max, dtype=np.float64)
    # Frozen first-solve cone (contact_friction == 4): the FIRST
    # attempt's solved normal impulse per contact, captured once and
    # never recomputed intra-tick -- simultaneous (this tick) and
    # unrevised (no pump) at once.
    frozen_n = np.zeros(n_contacts, dtype=np.float64)
    for _attempt in range(4):
        # compact active-row map
        cmap = np.full(rows_max, -1, dtype=np.int64)
        m = 0
        for r in range(n_rows):
            if active[r]:
                cmap[r] = m
                m += 1
        lam_full[:] = 0.0
        if m == 0:
            break
        K = np.zeros((m, m), dtype=np.float64)
        rhs = np.zeros(m, dtype=np.float64)
        # right-hand side: -v_rel per row
        for r in range(n_rows):
            if not active[r]:
                continue
            vr = 0.0
            ba = rb_a[r]
            if ba >= 0:
                vr += jla[r] @ lin_vel[ba] + jaa[r] @ ang_vel[ba]
            bb = rb_b[r]
            if bb >= 0:
                vr += jlb[r] @ lin_vel[bb] + jab[r] @ ang_vel[bb]
            if kind[r] == _MOTOR:
                # drive relative velocity to the muscle target, not to zero
                rhs[cmap[r]] = motor_target[mid[r]] - vr
            else:
                # row_bias is 0 except for mode-4 Baumgarte lock rows
                rhs[cmap[r]] = row_bias[r] - vr
        # K = J M^-1 J^T via body incidence (K is SPD by construction)
        for b in range(n_links):
            s0 = starts[b]
            s1 = starts[b + 1]
            for ii in range(s0, s1):
                ri = body_rows[ii]
                if not active[ri]:
                    continue
                if rb_a[ri] == b:
                    jli = jla[ri]
                    jai = jaa[ri]
                else:
                    jli = jlb[ri]
                    jai = jab[ri]
                jaiI = I_inv[b] @ jai
                ci_ = cmap[ri]
                for jj in range(ii, s1):
                    rj = body_rows[jj]
                    if not active[rj]:
                        continue
                    if rb_a[rj] == b:
                        jlj = jla[rj]
                        jaj = jaa[rj]
                    else:
                        jlj = jlb[rj]
                        jaj = jab[rj]
                    c = inv_mass[b] * (jli @ jlj) + jaiI @ jaj
                    cj_ = cmap[rj]
                    K[ci_, cj_] = K[ci_, cj_] + c
                    if cj_ != ci_:
                        K[cj_, ci_] = K[cj_, ci_] + c
        # min-norm regularizer for redundant rows (over-constrained bodies
        # make K singular; eps scales with the system, 1e-9 of the mean
        # diagonal)
        tr = 0.0
        for i in range(m):
            tr = tr + K[i, i]
        eps = 1e-9 * tr / m
        if eps <= 0.0:
            eps = 1e-12
        for i in range(m):
            K[i, i] = K[i, i] + eps
        lam = _chol_solve(K, rhs)
        # Frozen first-solve cone (mode 4): capture the FIRST attempt's
        # solved normal impulses -- the cone bound for the rest of the
        # tick.  Attempt 1's friction fixing below reads the same
        # just-solved lambdas mode 1 would use; the modes diverge from
        # attempt 2, where mode 1 recomputes and mode 4 stays frozen.
        if contact_friction == 4 and _attempt == 0:
            for r in range(n_rows):
                if kind[r] == _UNILATERAL and rec_t[r] == _REC_CONTACT:
                    ln0 = lam[cmap[r]]
                    frozen_n[rec_i[r]] = ln0 if ln0 > 0.0 else 0.0
        # Active-set bookkeeping.  Unilateral rows with lambda < 0 leave the
        # set.  Motor rows that exceed their impulse bound are FIXED at the
        # bound: the bounded impulse is applied to the bodies NOW (so the
        # next attempt's rhs sees it) and the row leaves the set.  Clamping
        # a solved lambda post-solve instead would break K lambda = rhs and
        # pump energy -- the K2 measurement (+10.5 kJ / 2000 ticks) that
        # moved the unilaterals out of this solve in the first place; the
        # motor lane gets the correct box-constraint active set instead.
        violated = False
        for r in range(n_rows):
            if not active[r]:
                continue
            lam_full[r] = lam[cmap[r]]
            if kind[r] == _UNILATERAL and lam[cmap[r]] < -1e-9:
                active[r] = False
                lam_full[r] = 0.0
                violated = True
            elif kind[r] == _MOTOR:
                lim = motor_lmax[mid[r]]
                lc = lam[cmap[r]]
                if lc > lim or lc < -lim:
                    if lc > lim:
                        lc = lim
                    else:
                        lc = -lim
                    ba = rb_a[r]
                    bb = rb_b[r]
                    if ba >= 0 and mass[ba] > 0.0:
                        ang_vel[ba] = ang_vel[ba] + I_inv[ba] @ (lc * jaa[r])
                    if bb >= 0 and mass[bb] > 0.0:
                        ang_vel[bb] = ang_vel[bb] + I_inv[bb] @ (lc * jab[r])
                    motor_impulses[mid[r]] = motor_impulses[mid[r]] + lc
                    joint_impulses_ang[rec_i[r]] = \
                        joint_impulses_ang[rec_i[r]] + lc * jab[r]
                    active[r] = False
                    lam_full[r] = 0.0
                    violated = True
            elif kind[r] == _FRICTION:
                # cone bound: mode 1 from THIS attempt's solved normal
                # lambda (a normal row dropped earlier in this pass
                # leaves lim = 0, so its friction rows go to zero with
                # it); mode 3 from the PREVIOUS TICK's normal impulse
                # (contact_prev_n), fixed all tick -- the warm start
                # that removes the intra-tick bound revision (the v3d
                # simmer pump's address).  A row past the cone is FIXED
                # at the bound: the bounded impulse is applied NOW
                # (next attempt's rhs sees it) and the row leaves the
                # set -- the motor-row idiom, never a post-solve clamp.
                if contact_friction == 4:
                    # frozen first-solve cone: the bound NEVER revises
                    # intra-tick (the v3d pump's address) and never goes
                    # stale (this tick, the warm-start falsifier).
                    lam_n = frozen_n[rec_i[r]]
                elif contact_friction == 3:
                    lam_n = contact_prev_n[rec_i[r]]
                else:
                    pn = pair[r]
                    lam_n = 0.0
                    if pn >= 0 and active[pn]:
                        lam_n = lam[cmap[pn]]
                lim = MU * lam_n
                if lim < 0.0:
                    lim = 0.0
                lc = lam[cmap[r]]
                if lc > lim or lc < -lim:
                    if lc > lim:
                        lc = lim
                    else:
                        lc = -lim
                    bb = rb_b[r]
                    if bb >= 0 and mass[bb] > 0.0:
                        lin_vel[bb] = lin_vel[bb] + inv_mass[bb] * lc * jlb[r]
                        ang_vel[bb] = ang_vel[bb] + I_inv[bb] @ (lc * jab[r])
                    contact_impulses[rec_i[r]] = \
                        contact_impulses[rec_i[r]] + lc * jlb[r]
                    active[r] = False
                    lam_full[r] = 0.0
                    violated = True
        if not violated:
            break

    # friction clamp: |lambda_t| <= MU * lambda_normal of the paired row.
    # First HARD-CLAMP any unilateral row still negative after the active-set
    # attempts: a contact or rope must NEVER pull (measured 2026-08-08: rows
    # that stayed negative after 4 attempts acted as suction and dragged the
    # feet through the floor, com_dz reaching -2 m before the explosion).
    for r in range(n_rows):
        if not active[r]:
            lam_full[r] = 0.0
            continue
        if kind[r] == _UNILATERAL and lam_full[r] < 0.0:
            lam_full[r] = 0.0
        if kind[r] == _FRICTION:
            if contact_friction == 4:
                # frozen first-solve cone: the final clamp reads the
                # same frozen bound the active set used.
                lim = MU * frozen_n[rec_i[r]]
                if lim < 0.0:
                    lim = 0.0
            elif contact_friction == 3:
                # warm-start cone: the bound never revises intra-tick,
                # so the final clamp reads the same fixed bound.
                lim = MU * contact_prev_n[rec_i[r]]
                if lim < 0.0:
                    lim = 0.0
            else:
                pn = pair[r]
                lim = 0.0
                if pn >= 0 and active[pn]:
                    lim = MU * lam_full[pn]
            if lam_full[r] > lim:
                lam_full[r] = lim
            elif lam_full[r] < -lim:
                lam_full[r] = -lim
        # motor bounds are handled INSIDE the active-set loop above (fix at
        # the bound and re-solve); nothing to clamp here.

    # ---- 5. apply impulses and record reactions ----
    for r in range(n_rows):
        l = lam_full[r]
        if l == 0.0:
            continue
        ba = rb_a[r]
        if ba >= 0 and mass[ba] > 0.0:
            lin_vel[ba] = lin_vel[ba] + inv_mass[ba] * l * jla[r]
            ang_vel[ba] = ang_vel[ba] + I_inv[ba] @ (l * jaa[r])
        bb = rb_b[r]
        if bb >= 0 and mass[bb] > 0.0:
            lin_vel[bb] = lin_vel[bb] + inv_mass[bb] * l * jlb[r]
            ang_vel[bb] = ang_vel[bb] + I_inv[bb] @ (l * jab[r])
        rt = rec_t[r]
        ri = rec_i[r]
        if rt == _REC_JOINT_LIN:
            joint_impulses_lin[ri] = joint_impulses_lin[ri] + l * jlb[r]
            joint_impulses_ang[ri] = joint_impulses_ang[ri] + l * jab[r]
        elif rt == _REC_JOINT_ANG:
            joint_impulses_ang[ri] = joint_impulses_ang[ri] + l * jab[r]
        elif rt == _REC_LIGAMENT:
            # reaction ON body A (A pulled toward B when taut)
            lig_impulses_lin[ri] = lig_impulses_lin[ri] + l * jla[r]
            lig_impulses_ang[ri] = lig_impulses_ang[ri] + l * jaa[r]
        elif rt == _REC_CONTACT:
            contact_impulses[ri] = contact_impulses[ri] + l * jlb[r]
        if kind[r] == _MOTOR and mid[r] >= 0:
            motor_impulses[mid[r]] = motor_impulses[mid[r]] + l

    # ---- 5b. unilateral sweeps: sequential impulses with per-iteration
    # clamping -- dissipative by construction.  Ligaments ALWAYS sweep
    # here.  Contacts sweep here when contacts_in_solve == 0 (the full
    # sweep, pre-v3a path), or when contact_friction == 2 (v3e hybrid:
    # FRICTION ONLY -- the normals live in the direct solve above and
    # sweeping them again would double-apply the ground reaction).  (Measured
    # 2026-08-08: a first contacts-in-solve attempt that clamped contact
    # lambdas POST-solve re-introduced the K2 active-set energy pump --
    # wmax 1.2e7 rad/s in 300 ticks.  v3a keeps lift-off AND the friction
    # cone inside the re-solve instead; the sweep remains the fallback.)
    # mode 5 (muscle-exclusion membrane): per-link angular velocity
    # contributed by the muscle channel THIS tick -- the exclusion the
    # friction sweep subtracts before its tangential kill.  Filled on
    # the sweep's first iteration from motor_impulses (angular rows).
    motor_dw = np.zeros((n_links, 3), dtype=np.float64)
    # mode 7 (DERIVED-MU) bookkeeping: per-link ground-shear demand
    # (impulse units) from the solved muscle impulses, and the number
    # of contact points per link to split it.  Filled on the sweep's
    # first iteration.
    shear_demand = np.zeros(n_links, dtype=np.float64)
    contacts_per_link = np.zeros(n_links, dtype=np.float64)
    for _it in range(n_proj_iters):
        # ligaments: unilateral, only when taut and separating
        for li in range(n_lig):
            ia = lig_idx_a[li]
            ib = lig_idx_b[li]
            Ra = _qmat(quat[ia])
            Rb = _qmat(quat[ib])
            r_a = Ra @ lig_off_a[li]
            r_b = Rb @ lig_off_b[li]
            pa_v = pos[ia] + r_a
            pb_v = pos[ib] + r_b
            vec = pb_v - pa_v
            Llen = _norm3(vec)
            if Llen <= lig_rest[li] or Llen < 1e-15:
                continue
            n = vec / Llen
            I_inv_a = I_inv[ia]
            I_inv_b = I_inv[ib]
            rn_a = _cross3(r_a, n)
            rn_b = _cross3(r_b, n)
            K = inv_mass[ia] + inv_mass[ib] \
                + rn_a @ (I_inv_a @ rn_a) + rn_b @ (I_inv_b @ rn_b)
            if K <= 1e-15:
                continue
            v_sep = ((lin_vel[ib] + _cross3(ang_vel[ib], r_b)) - (
                lin_vel[ia] + _cross3(ang_vel[ia], r_a))) @ n
            if v_sep <= 0.0:
                continue
            j = -v_sep / K
            # force-limit membrane: an overstretched ligament YIELDS at
            # its physiological ceiling (f_max * dt per tick, counting
            # what earlier iterations already applied); f_max <= 0 is
            # the legacy unlimited row.
            if lig_fmax[li] > 0.0:
                used = lig_impulses_lin[li] @ n
                avail = lig_fmax[li] * dt - used
                if avail <= 0.0:
                    continue
                if -j > avail:
                    j = -avail
            jv = j * n
            lin_vel[ib] = lin_vel[ib] + inv_mass[ib] * jv
            ang_vel[ib] = ang_vel[ib] + I_inv_b @ _cross3(r_b, jv)
            lin_vel[ia] = lin_vel[ia] - inv_mass[ia] * jv
            ang_vel[ia] = ang_vel[ia] - I_inv_a @ _cross3(r_a, jv)
            # reaction ON body A is -jv (A pulled toward B when taut)
            lig_impulses_lin[li] = lig_impulses_lin[li] - jv
            lig_impulses_ang[li] = lig_impulses_ang[li] - _cross3(r_a, jv)

        # contacts: unilateral normal + Coulomb friction, inelastic.
        # contacts_in_solve == 0: full sweep (normals + friction), the
        # pre-v3a path.  contacts_in_solve with contact_friction == 2
        # (v3e hybrid): the normals were decided by the direct solve
        # above; this sweep applies FRICTION ONLY, with the cone bound
        # MU x the solve's normal impulse (contact_impulses[ci][2]) --
        # per-iteration sweep clamping is dissipative by construction,
        # which the in-solve cone fix was measured not to be (v3d:
        # simmer pump, supercritical at tick 7 713).  Friction modes 0
        # (none), 1 (full cone in-solve), 3 (warm-start) and 4 (frozen
        # first-solve) skip this sweep.  contact_friction == 5 (the
        # muscle-exclusion membrane, 2026-08-08): the same hybrid sweep,
        # but the tangential kill acts on (v_t - v_t_motor) -- the
        # muscle channel's own contribution to the contact-point
        # velocity, computed exactly from motor_impulses (angular rows,
        # jab = L), is EXCLUDED.  The friction-fork verdict: the mode-2
        # sweep kills the contact-point velocity the servo just booked
        # and back-drives the tarsals, wrong-way at 100% of samples.
        # Friction opposes the world's sliding, not the muscle's
        # command.  contact_friction == 6 (the rolling-blind sweep,
        # 2026-08-08): the tangential kill is sized on the contact
        # link's LINEAR tangential velocity (the sliding channel);
        # the rotational surface velocity omega x r at the point is
        # the joint's business.  Friction kills sliding, not rolling.
        # contact_friction == 7 (DERIVED-MU, 2026-08-08): the
        # rolling-blind sliding-channel kill with the cone cap sized
        # from the SERVO REACTION SHEAR itself -- the rolling-blind
        # falsifier fired: the ratchet is the lean torque's ground
        # reaction overflowing the datum cone MU*j_n.  Per tick the
        # muscle impulse l about a joint at height h demands ground
        # shear |l|/h (moment balance about the joint); a cone that
        # holds exactly what the muscle can demand is DERIVED, not
        # tuned.  The datum cone stays as the floor.
        if contacts_in_solve != 0 and contact_friction != 2 \
                and contact_friction != 5 and contact_friction != 6 \
                and contact_friction != 7:
            continue
        # mode 5: the muscle channel's angular-velocity contribution
        # per link, computed once per tick before the first iteration.
        if contact_friction == 5 and _it == 0:
            for mi in range(n_motors):
                l_mi = motor_impulses[mi]
                if l_mi == 0.0:
                    continue
                mpa = motor_parent[mi]
                mcb = motor_child[mi]
                Lmi = motor_axis[mi]
                if mcb >= 0 and mass[mcb] > 0.0:
                    motor_dw[mcb] = motor_dw[mcb] + I_inv[mcb] @ (
                        l_mi * Lmi)
                if mpa >= 0 and mass[mpa] > 0.0:
                    motor_dw[mpa] = motor_dw[mpa] - I_inv[mpa] @ (
                        l_mi * Lmi)
        # mode 7 (DERIVED-MU): per-link ground-shear demand from this
        # tick's solved muscle impulses, and the contact count per
        # link to split it across the link's contact points.  The
        # demand: a muscle impulse |l| about a joint at height h
        # above the contact plane requires ground shear |l|/h
        # (moment balance about the joint).  Only the contact-
        # carrying side of the joint transmits it to the ground;
        # internal joints (neither side grounded) demand nothing.
        if contact_friction == 7 and _it == 0:
            for ci in range(n_contacts):
                li = contact_link_idx[ci]
                if mass[li] > 0.0:
                    contacts_per_link[li] = contacts_per_link[li] + 1.0
            for mi in range(n_motors):
                l_mi = motor_impulses[mi]
                if l_mi == 0.0:
                    continue
                mpa = motor_parent[mi]
                mcb = motor_child[mi]
                ji = motor_joint[mi]
                side = -1
                if mcb >= 0 and contacts_per_link[mcb] > 0.0:
                    side = mcb
                elif mpa >= 0 and contacts_per_link[mpa] > 0.0:
                    side = mpa
                if side < 0:
                    continue
                if side == mcb:
                    r_off = r_joint_child_local[ji]
                else:
                    r_off = r_joint_parent_local[ji]
                jw = pos[side] + _qmat(quat[side]) @ r_off
                h = jw[2]
                if h < 1e-3:
                    h = 1e-3
                shear_demand[side] = shear_demand[side] + abs(l_mi) / h
        for ci in range(n_contacts):
            li = contact_link_idx[ci]
            if mass[li] <= 0.0:
                continue
            R = _qmat(quat[li])
            r = R @ contact_off_local[ci]
            p_w = pos[li] + r
            if p_w[2] >= contact_slop:
                continue
            I_inv_l = I_inv[li]
            v_p = lin_vel[li] + _cross3(ang_vel[li], r)
            rn = _cross3(r, z_hat)
            K_n = inv_mass[li] + rn @ (I_inv_l @ rn)
            if K_n <= 1e-15:
                continue
            vn = v_p @ z_hat
            if contacts_in_solve == 0:
                j_n = 0.0
                if vn < 0.0:
                    j_n = -vn / K_n
                    jv = j_n * z_hat
                    lin_vel[li] = lin_vel[li] + inv_mass[li] * jv
                    ang_vel[li] = ang_vel[li] + I_inv_l @ _cross3(r, jv)
                    contact_impulses[ci] = contact_impulses[ci] + jv
            else:
                # hybrid: the direct solve already applied this tick's
                # normal impulse; its z component is the cone bound.
                j_n = contact_impulses[ci][2]
                if j_n < 0.0:
                    j_n = 0.0
            v_t = v_p - vn * z_hat
            if contact_friction == 5:
                # muscle-exclusion membrane: remove the muscle
                # channel's own contribution to the contact-point
                # velocity before the tangential kill; friction
                # opposes the world's sliding, not the muscle's
                # command.  The exclusion is tangential-only (the
                # normal channel is untouched).
                v_t = v_t - _cross3(motor_dw[li], r)
                v_t = v_t - (v_t @ z_hat) * z_hat
            if contact_friction == 6 or contact_friction == 7:
                # rolling-blind sweep: size the kill on the link's
                # LINEAR tangential velocity -- the sliding channel.
                # A rolling foot (omega x r large, lin_vel small)
                # draws almost no tangential impulse; a skating foot
                # draws the full cone.  The impulse still torques the
                # link through cross(r, jv_t), as a physical friction
                # impulse at a contact point does.
                v_lin = lin_vel[li]
                v_t = v_lin - (v_lin @ z_hat) * z_hat
            vt_mag = _norm3(v_t)
            if vt_mag > 1e-12:
                t_dir = v_t / vt_mag
                rn_t = _cross3(r, t_dir)
                K_t = inv_mass[li] + rn_t @ (I_inv_l @ rn_t)
                if contact_friction == 6 or contact_friction == 7:
                    # linear-channel effective mass only: the kill
                    # cancels lin_vel exactly (inv_mass * j = v_t),
                    # the angular reaction rides along at the joint.
                    K_t = inv_mass[li]
                if K_t > 1e-15:
                    j_cap = MU * j_n
                    if contact_friction == 7 and \
                            contacts_per_link[li] > 0.0:
                        # DERIVED-MU: the cone holds the datum shear
                        # PLUS this tick's servo reaction shear,
                        # split across the link's contact points.
                        j_cap = j_cap + shear_demand[li] \
                            / contacts_per_link[li]
                    j_t = min(vt_mag / K_t, j_cap)
                    jv_t = -j_t * t_dir
                    lin_vel[li] = lin_vel[li] + inv_mass[li] * jv_t
                    ang_vel[li] = ang_vel[li] + I_inv_l @ _cross3(r, jv_t)
                    contact_impulses[ci] = contact_impulses[ci] + jv_t

    # ---- 6. integrate positions ----
    for i in range(n_links):
        if mass[i] <= 0.0:
            continue
        pos[i] = pos[i] + dt * lin_vel[i]
        quat[i] = _qnorm(quat[i] + dt * _quat_derivative(quat[i], ang_vel[i]))

    # ---- 7. position stabilization (NEVER touches velocities) ----
    position_pass(
        pos, quat, mass, inv_mass, inv_inertia_diag_local,
        joint_parent, joint_child, joint_dof, joint_axes,
        r_joint_parent_local, r_joint_child_local, joint_q_rel0,
        lig_idx_a, lig_idx_b, lig_off_a, lig_off_b, lig_rest,
        contact_link_idx, contact_off_local,
        contact_slop, n_proj_iters, do_rotation_locks,
        ghost_coinc, ghost_lig, ghost_lock,
        pos_pass_mode,
    )
