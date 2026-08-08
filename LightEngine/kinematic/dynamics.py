"""
Rigid-body dynamics for the 77-link StandingHuman kinematic skeleton (Lane K2).

This module is SI-only (meters, kilograms, seconds).  It implements:

  * uniform gravity,
  * tension-only ligament constraints (unilateral distance projection),
  * unilateral ground contact as spring-damper pads with Coulomb friction,
  * articulated joint constraints (point coincidence + rotational locks),

integrated with ONE iterated position-based constraint-projection loop per tick.

Coordinate convention
---------------------
The per-link state tracks the link center of mass (COM).  This makes the
rigid-body equations diagonal in the local frame and keeps the joint-center
offsets constant in the link local frame.  Telemetry helpers convert back to
the FK convention (proximal endpoint) on demand.

Quaternion convention follows LightEngine.kinematic.transforms: active
rotation, [w, x, y, z].

Derived constants
-----------------
# ANATOMY-DATUM: standard gravity.
    g = 9.80665 m/s^2

# ANATOMY-DATUM: dry skin-floor static-friction coefficient.
    MU_CONTACT = 0.70
    Source: measured range for skin-floor dry contact is ~0.5-0.9.
    We use the midpoint of that measured band as the representative value.

# ANATOMY-DATUM: joint-play / grain-spacing tolerance.
    d_eq_lu = 0.0484 lu  (from LightEngine.skeleton_scaling.D_EQ_LU)
    d_eq_m  = spec["lam"] * d_eq_lu

Ligament model: unilateral distance constraint
----------------------------------------------
A ligament is a rope in tension.  The measured rope law says a rope in tension
is near-rigid: it stretches negligibly until it unseats.  The correct rigid-body
compilation is therefore NOT a stiff spring but a UNILATERAL DISTANCE CONSTRAINT
inside the position-projection loop:

    if current_length > rest_length:
        project the two attachment points back to rest_length
    else:
        do nothing

The correction is split by generalized inverse mass (linear + angular) exactly
like the joint point constraints.  This is unconditionally stable at any dt for
the ligament itself, because it directly enforces length <= rest_length each
iteration.  Tension is recoverable from the accumulated projection impulse.

The old spring derivation is preserved in derive_ligament_stiffness() as
DOCUMENTATION of why the spring formulation fails (see Stability note below).
The function still fills ligament["stiffness"] so existing callers do not break,
but the value is no longer used by step().

Load-path estimate (now historical/documentary): a ligament joining links A and
B must support at least the weight of the heavier subtree it attaches to, so

    F_max(link_a, link_b) = g * max(subtree_mass(A), subtree_mass(B))
    k_ligament             = F_max / d_eq_m

Stability note: why the spring exploded
---------------------------------------
The derived spring stiffness is k ~ F_max / d_eq_m.  For a cervical vertebra
(m ~ 0.02 kg) and a ligament asked to carry even a small subtree (F_max ~ 1 N),
k ~ 1e5 N/m.  The undamped angular frequency is omega = sqrt(k/m) ~ 2000 rad/s.
Semi-implicit Euler is stable only for dt * omega < 2, but here dt = 1e-3 s
gives dt * omega ~ 2, and real loads are larger.  The ligament spring on small
links therefore injects energy and explodes the assembly.  The projection
constraint has no oscillatory mode: it directly removes the excess length each
iteration, so its stability does not depend on k/m.

Contact stiffness derivation
----------------------------
The foot contacts are modeled as independent spring-damper pads attached to the
tarsals link.  The criterion: full body weight, carried by one foot, compresses
the n contact points of that foot by no more than d_eq_m in total.  Because the
foot is treated as rigid for this first dynamics approximation, all n points on
one foot share a single penetration d, giving total upward force n*k*d.  We set
n*k*d_eq_m = M*g, hence

    k_contact = M * g / (n * d_eq_m)

where n = len(spec["contacts"]["L"]) (5 points per foot from the support
polygon).

Contact damping is derived for a critically damped response of the contact
oscillator.  Using the conservative upper-bound m_eff = M for the effective mass
seen by a foot contact,

    c_contact = 2 * sqrt(m_eff * k_contact)
              = 2 * sqrt(M * k_contact)

This guarantees the contact is non-oscillatory.  If the explicit spring-damper
still proves unstable, contacts are converted to the same unilateral projection
used for ligaments.

Integration
-----------
Semi-implicit Euler for the unconstrained prediction:

    v^{*}    = v^n + dt * M^{-1} * f_gravity
    omega^{*}= omega^n

Then ALL constraints (joint point coincidence, rotational locks per
dof_class, ligament tension-only, contact normal + Coulomb friction) are
solved at VELOCITY level, positions are integrated,

    x'       = x^n + dt * v
    q'       = normalize(q^n + dt * 0.5 * [0, omega] * q)

and a Baumgarte-style position stabilization pass (beta = 0.2, slop = the
measured d_eq joint play) removes integration drift WITHOUT touching
velocities.  The velocity solve is where the physics is; the position pass
has no kick channel (the two predecessor schemes derived velocity from
projected positions and exploded under sustained load -- measured launches
of 700 m/s -> 1e23 m/s, 2026-08-07).

Two velocity solvers are compiled in _dynamics_numba.py:

    * "direct" (default): assemble K = J M^-1 J^T for the tick's constraint
      rows and solve (K + eps I) lambda = -v_rel in one dense linear solve,
      with an active-set pass for unilateral rows and a Coulomb clamp on
      friction.  The sequential (Gauss-Seidel) solver DIVERGES at this
      skeleton's mass ratios (trunk:vertebra ~ 2000:1, slender-link axial
      I_inv ~ 1e7; contacts blew up at tick 2-3 at any dt, more iterations
      diverged faster -- 2026-08-07 experiment chain); a direct solve has no
      iteration to diverge.
    * "sequential": Box2D-lineage sequential impulses, kept as the
      reference/fallback (state["solver"] = "sequential").

Contacts carry the whole normal/friction load as impulses (the spring-damper
channel is retired); ligaments are tension-only unilateral rows: no explicit
spring anywhere.

The loop is deterministic: no RNG, fixed row ordering.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from LightEngine.kinematic import transforms
from LightEngine.kinematic.fk import forward_kinematics
from LightEngine.kinematic.skeleton_spec import (
    BALL_CUP,
    SADDLE,
    HINGE,
    SUTURE,
    D_EQ_LU,
)
from LightEngine import skeleton_scaling
from LightEngine.kinematic._dynamics_numba import (
    _HAS_NUMBA,
    step_core as _numba_step_core,
    step_core_direct as _numba_step_core_direct,
)


# ---------------------------------------------------------------------------
# Settled physical constants
# ---------------------------------------------------------------------------
GRAVITY_MPS2 = 9.80665  # ANATOMY-DATUM: standard gravity.
MU_CONTACT = 0.70       # ANATOMY-DATUM: midpoint of skin-floor dry range [0.5, 0.9].
BAUMGARTE_BETA = 0.2    # Constraint stabilization fraction (dimensionless).
# Angular-correction clamp, DERIVED: PBD rotations are linearizations valid only
# while sin(theta) ~ theta; |sin t - t|/t <= 1% gives t <= 0.244 rad.
THETA_CLAMP = 0.24


def _topological_order(spec: dict[str, Any]) -> list[str]:
    """Return links in parent-before-child order (deterministic)."""
    links = spec["links"]
    joints = spec["joints"]
    children_of: dict[str, list[str]] = {name: [] for name in links}
    for joint in joints.values():
        children_of[joint["parent_link"]].append(joint["child_link"])
    order: list[str] = []
    roots = [name for name, link in links.items() if link["parent_name"] is None]
    if len(roots) != 1:
        raise RuntimeError(f"Expected exactly one root, found {roots!r}")
    stack = [roots[0]]
    visited: set[str] = set()
    while stack:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        order.append(node)
        for child in sorted(children_of[node]):
            if child not in visited:
                stack.append(child)
    if len(order) != len(links):
        raise RuntimeError("Tree traversal did not reach all links")
    return order


def _subtree_masses(spec: dict[str, Any]) -> dict[str, float]:
    """Return total mass of each link plus all descendants."""
    links = spec["links"]
    children_of: dict[str, list[str]] = {name: [] for name in links}
    for name, link in links.items():
        parent = link["parent_name"]
        if parent is not None:
            children_of[parent].append(name)
    order = _topological_order(spec)
    subtree: dict[str, float] = {}
    for name in reversed(order):
        subtree[name] = float(links[name]["mass_kg"]) + sum(
            subtree[c] for c in children_of[name]
        )
    return subtree


def derive_ligament_stiffness(spec: dict[str, Any]) -> None:
    """Fill ligament["stiffness"] in N/m using the static load-path criterion.

    Criterion: under the largest static load the ligament can be asked to carry,
    its elongation must not exceed d_eq_m = spec["lam"] * D_EQ_LU.

    The load estimate is the weight of the heavier subtree attached to the
    ligament (see module docstring for derivation).
    """
    g = GRAVITY_MPS2
    d_eq_m = float(spec["lam"]) * D_EQ_LU
    if d_eq_m <= 0.0:
        raise ValueError("d_eq_m must be positive")
    subtree = _subtree_masses(spec)
    for lig in spec["ligaments"]:
        link_a = lig["anchor_a"]["link"]
        link_b = lig["anchor_b"]["link"]
        F_max = g * max(subtree[link_a], subtree[link_b])
        lig["stiffness"] = F_max / d_eq_m
        # The physiological tension ceiling: the force-limit membrane
        # (2026-08-08) clamps the ligament row's impulse to f_max * dt
        # when state["lig_force_limit"] is on -- an overstretched
        # ligament YIELDS instead of applying unlimited rigid tension.
        lig["f_max"] = F_max


def _contact_constants(spec: dict[str, Any]) -> tuple[float, float]:
    """Return (k_contact, c_contact) derived from the body-weight criterion."""
    M = float(spec["mass_kg"])
    g = GRAVITY_MPS2
    d_eq_m = float(spec["lam"]) * D_EQ_LU
    contacts = spec["contacts"]
    n = len(contacts["L"])
    if n == 0 or d_eq_m <= 0.0:
        return 0.0, 0.0
    k_contact = M * g / (n * d_eq_m)
    m_eff = M  # conservative upper bound for effective mass at foot contact
    c_contact = 2.0 * math.sqrt(m_eff * k_contact)
    return k_contact, c_contact


# ---------------------------------------------------------------------------
# State construction
# ---------------------------------------------------------------------------
def init_state(spec: dict[str, Any], joint_angles: dict[str, Any] | None = None) -> dict[str, Any]:
    """Initialize a dynamics state from the kinematic spec.

    Returns an opaque state dict.  Per-link COM pose/velocity are stored as
    numpy arrays keyed by link name.  Ligament stiffness is derived if still
    None.
    """
    if joint_angles is None:
        joint_angles = {}

    # Ensure derived stiffness is present.
    if any(lig.get("stiffness") is None for lig in spec["ligaments"]):
        derive_ligament_stiffness(spec)

    links = spec["links"]
    joints = spec["joints"]
    link_names = list(links.keys())
    name_to_idx = {name: i for i, name in enumerate(link_names)}
    n_links = len(link_names)

    # FK at requested joint angles; convert positions to meters.
    poses_lu = forward_kinematics(spec, joint_angles)
    pos_com = np.zeros((n_links, 3), dtype=np.float64)
    quat = np.zeros((n_links, 4), dtype=np.float64)
    for name, i in name_to_idx.items():
        p_lu, q = poses_lu[name]
        p_m = np.asarray(p_lu, dtype=np.float64).reshape(3) * float(spec["lam"])
        R = transforms.to_matrix(q)
        com_offset_m = links[name]["com_offset_m"]
        pos_com[i] = p_m + R @ com_offset_m
        quat[i] = q

    mass = np.array([links[name]["mass_kg"] for name in link_names], dtype=np.float64)
    inv_mass = np.zeros_like(mass)
    nonzero_mass = mass > 0.0
    inv_mass[nonzero_mass] = 1.0 / mass[nonzero_mass]

    inertia_diag_local = np.array(
        [links[name]["inertia_diag_m"] for name in link_names], dtype=np.float64
    )
    inv_inertia_diag_local = np.zeros_like(inertia_diag_local)
    nonzero_inertia = inertia_diag_local > 0.0
    inv_inertia_diag_local[nonzero_inertia] = 1.0 / inertia_diag_local[nonzero_inertia]

    # Build joint arrays in parent-before-child order.
    order = _topological_order(spec)
    order_index = {name: i for i, name in enumerate(order)}
    joint_items = sorted(
        joints.items(), key=lambda kv: order_index[kv[1]["child_link"]]
    )
    joint_names = [name for name, _ in joint_items]
    joint_parent = np.array(
        [name_to_idx[j["parent_link"]] for _, j in joint_items], dtype=np.int64
    )
    joint_child = np.array(
        [name_to_idx[j["child_link"]] for _, j in joint_items], dtype=np.int64
    )
    dof_map = {BALL_CUP: 3, SADDLE: 2, HINGE: 1, SUTURE: 0}
    joint_dof = np.array([dof_map[j["dof_class"]] for _, j in joint_items], dtype=np.int64)
    joint_axes_local = [
        [np.asarray(ax, dtype=np.float64).reshape(3) for ax in j["axes"]]
        for _, j in joint_items
    ]

    # Joint center relative to COM, in each body's local frame, PER JOINT.
    r_joint_parent_local = np.zeros((len(joint_items), 3), dtype=np.float64)
    r_joint_child_local = np.zeros((len(joint_items), 3), dtype=np.float64)
    # Desired relative rotation at the zero pose: q_rel0 = q_parent^{-1} * q_child.
    joint_q_rel0 = np.zeros((len(joint_items), 4), dtype=np.float64)
    for ji, (_, j) in enumerate(joint_items):
        parent_name = j["parent_link"]
        child_name = j["child_link"]
        r_joint_parent_local[ji] = (
            np.asarray(j["center_parent_local_m"], dtype=np.float64).reshape(3)
            - links[parent_name]["com_offset_m"]
        )
        r_joint_child_local[ji] = (
            np.asarray(j["center_child_local_m"], dtype=np.float64).reshape(3)
            - links[child_name]["com_offset_m"]
        )
        q_rel0 = transforms.multiply(
            transforms.conjugate(quat[name_to_idx[parent_name]]),
            quat[name_to_idx[child_name]],
        )
        if q_rel0[0] < 0.0:
            q_rel0 = -q_rel0
        joint_q_rel0[ji] = q_rel0

    # Ligament records with precomputed local attachment offsets relative to COM.
    lig_records: list[dict[str, Any]] = []
    for lig in spec["ligaments"]:
        att_a = lig["anchor_a"]
        att_b = lig["anchor_b"]
        link_a = att_a["link"]
        link_b = att_b["link"]
        offset_a_local = (
            np.asarray(att_a["offset_m"], dtype=np.float64).reshape(3)
            - links[link_a]["com_offset_m"]
        )
        offset_b_local = (
            np.asarray(att_b["offset_m"], dtype=np.float64).reshape(3)
            - links[link_b]["com_offset_m"]
        )
        lig_records.append({
            "idx_a": name_to_idx[link_a],
            "idx_b": name_to_idx[link_b],
            "offset_a_local": offset_a_local,
            "offset_b_local": offset_b_local,
            "rest_length_m": float(lig["rest_length_m"]),
            "stiffness": float(lig["stiffness"]),
            "f_max": float(lig["f_max"]),
            "name": lig["name"],
        })

    # Contact records: attach all foot contact points to the tarsals link.
    # This is a first approximation; a later lane may distribute them across
    # tarsals/metatarsals/forefoot.
    k_contact, c_contact = _contact_constants(spec)
    contact_records: list[dict[str, Any]] = []
    for side in ("L", "R"):
        link_name = f"tarsals_{side}"
        if link_name not in name_to_idx:
            continue
        link_idx = name_to_idx[link_name]
        for cp in spec["contacts"][side]:
            p_world_m = np.asarray(cp["point_m"], dtype=np.float64).reshape(3)
            # Compute local offset at zero pose (state is already built).
            R = transforms.to_matrix(quat[link_idx])
            offset_local = R.T @ (p_world_m - pos_com[link_idx])
            contact_records.append({
                "link_idx": link_idx,
                "offset_local": offset_local,
                "side": side,
            })

    # Flat arrays for the numba core (_dynamics_numba.step_core).  The dict
    # records above stay for the Python fallback and the reaction queries.
    lig_idx_a = np.array([r["idx_a"] for r in lig_records], dtype=np.int64)
    lig_idx_b = np.array([r["idx_b"] for r in lig_records], dtype=np.int64)
    lig_off_a = np.array([r["offset_a_local"] for r in lig_records], dtype=np.float64) \
        if lig_records else np.zeros((0, 3), dtype=np.float64)
    lig_off_b = np.array([r["offset_b_local"] for r in lig_records], dtype=np.float64) \
        if lig_records else np.zeros((0, 3), dtype=np.float64)
    lig_rest = np.array([r["rest_length_m"] for r in lig_records], dtype=np.float64)
    contact_link_idx = np.array([r["link_idx"] for r in contact_records], dtype=np.int64)
    contact_off_local = np.array([r["offset_local"] for r in contact_records], dtype=np.float64) \
        if contact_records else np.zeros((0, 3), dtype=np.float64)
    joint_axes_arr = np.zeros((len(joint_items), 2, 3), dtype=np.float64)
    for ji, axes in enumerate(joint_axes_local):
        for ai in range(min(2, len(axes))):
            joint_axes_arr[ji, ai] = axes[ai]

    state: dict[str, Any] = {
        "link_names": link_names,
        "name_to_idx": name_to_idx,
        "pos": pos_com,
        "quat": quat,
        "lin_vel": np.zeros((n_links, 3), dtype=np.float64),
        "ang_vel": np.zeros((n_links, 3), dtype=np.float64),
        "mass": mass,
        "inv_mass": inv_mass,
        "inertia_diag_local": inertia_diag_local,
        "inv_inertia_diag_local": inv_inertia_diag_local,
        "r_joint_parent_local": r_joint_parent_local,
        "r_joint_child_local": r_joint_child_local,
        "joint_q_rel0": joint_q_rel0,
        "joint_names": joint_names,
        "joint_parent": joint_parent,
        "joint_child": joint_child,
        "joint_dof": joint_dof,
        "joint_axes_local": joint_axes_local,
        "lig_records": lig_records,
        "contact_records": contact_records,
        "lig_idx_a": lig_idx_a,
        "lig_idx_b": lig_idx_b,
        "lig_off_a": lig_off_a,
        "lig_off_b": lig_off_b,
        "lig_rest": lig_rest,
        "lig_fmax": np.array([r["f_max"] for r in lig_records],
                             dtype=np.float64),
        "contact_link_idx": contact_link_idx,
        "contact_off_local": contact_off_local,
        "joint_axes_arr": joint_axes_arr,
        "k_contact": k_contact,
        "c_contact": c_contact,
        "joint_impulses_lin": np.zeros((len(joint_items), 3), dtype=np.float64),
        "joint_impulses_ang": np.zeros((len(joint_items), 3), dtype=np.float64),
        "lig_impulses_lin": np.zeros((len(lig_records), 3), dtype=np.float64),
        "lig_impulses_ang": np.zeros((len(lig_records), 3), dtype=np.float64),
        "contact_impulses": np.zeros((len(contact_records), 3), dtype=np.float64),
        "contact_forces_ext": np.zeros((len(contact_records), 3), dtype=np.float64),
        "dt": 0.0,
    }
    return state


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _quat_derivative(q: np.ndarray, omega: np.ndarray) -> np.ndarray:
    """Return dq/dt = 0.5 * [0, omega] * q (world-frame angular velocity)."""
    qw, qx, qy, qz = q
    wx, wy, wz = omega
    return 0.5 * np.array([
        -wx * qx - wy * qy - wz * qz,
        wx * qw + wy * qz - wz * qy,
        wy * qw - wx * qz + wz * qx,
        wz * qw + wx * qy - wy * qx,
    ], dtype=np.float64)


def _rotate_vector(q: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Rotate vector v by unit quaternion q."""
    return transforms.rotate(q, v)


def _rotate_vectors_batch(q: np.ndarray, vs: np.ndarray) -> np.ndarray:
    """Rotate many vectors by the same quaternion q."""
    R = transforms.to_matrix(q)
    return vs @ R.T


def _world_inertia_inv(q: np.ndarray, inv_diag_local: np.ndarray) -> np.ndarray:
    """Return I_world^{-1} = R * diag(inv_diag) * R^T."""
    R = transforms.to_matrix(q)
    return R @ np.diag(inv_diag_local) @ R.T


def _derive_angular_velocity(q_old: np.ndarray, q_new: np.ndarray, dt: float) -> np.ndarray:
    """Return world-frame angular velocity implied by quaternion change over dt.

    dq = q_new * q_old^{-1}; omega = axis * angle / dt.
    """
    dq = transforms.multiply(q_new, transforms.conjugate(q_old))
    if dq[0] < 0.0:
        dq = -dq
    sin_half = float(np.linalg.norm(dq[1:]))
    if sin_half < 1e-14:
        return np.zeros(3, dtype=np.float64)
    axis = dq[1:] / sin_half
    angle = 2.0 * math.atan2(sin_half, float(dq[0]))
    return axis * angle / dt


def _skew(v: np.ndarray) -> np.ndarray:
    """Return 3x3 skew-symmetric matrix for vector v."""
    x, y, z = v
    return np.array([
        [0.0, -z, y],
        [z, 0.0, -x],
        [-y, x, 0.0],
    ], dtype=np.float64)


def _effective_mass_matrix(
    inv_m_a: float,
    inv_m_b: float,
    r_a: np.ndarray,
    r_b: np.ndarray,
    I_inv_a: np.ndarray,
    I_inv_b: np.ndarray,
) -> np.ndarray:
    """Return 3x3 K such that K @ j = delta_v_rel for impulse j on child, -j on parent."""
    K = (inv_m_a + inv_m_b) * np.eye(3, dtype=np.float64)
    K -= _skew(r_a) @ I_inv_a @ _skew(r_a)
    K -= _skew(r_b) @ I_inv_b @ _skew(r_b)
    return K


def _rotate_body_around_point(
    pos: np.ndarray,
    quat: np.ndarray,
    point: np.ndarray,
    axis: np.ndarray,
    angle: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Rotate a rigid body around a world-space point and return new (pos, quat).

    DERIVED-GEOMETRY: a right-handed rotation of angle around axis leaves the
    point fixed; the COM orbits the point and the orientation quaternion is
    pre-multiplied by the rotation quaternion.
    """
    axis = np.asarray(axis, dtype=np.float64).reshape(3)
    n = float(np.linalg.norm(axis))
    if n < 1e-12 or abs(angle) < 1e-12:
        return pos.copy(), quat.copy()
    axis = axis / n
    # Angular corrections are linearizations valid only in the small-angle
    # band (|sin t - t|/t <= 1% -> t <= 0.244).  Clamp: beyond it the
    # linearized correction is wrong in kind, not degree (measured 2026-08-07:
    # unclamped corrections scrambled small-link orientations into pi-flips).
    if angle > THETA_CLAMP:
        angle = THETA_CLAMP
    elif angle < -THETA_CLAMP:
        angle = -THETA_CLAMP
    dq = transforms.from_axis_angle(axis, angle)
    new_quat = transforms.multiply(dq, quat)
    offset = pos - point
    new_pos = point + transforms.rotate(dq, offset)
    return new_pos, new_quat


# ---------------------------------------------------------------------------
# Main integration step
# ---------------------------------------------------------------------------
def step(spec: dict[str, Any], state: dict[str, Any], dt: float,
         n_proj_iters: int = 20) -> dict[str, Any]:
    """Advance the dynamics state by dt.

    Dispatches to the compiled numba cores (LightEngine.kinematic._dynamics_numba)
    when numba is available: the direct linear solve by default, the sequential
    Gauss-Seidel scheme when state["solver"] == "sequential".  The Python path
    below is kept as the fallback and the readable reference for the semantics.
    """
    if dt <= 0.0:
        raise ValueError("dt must be positive")

    if _HAS_NUMBA:
        n_links = len(state["link_names"])
        n_joints = len(state["joint_names"])
        n_lig = len(state["lig_records"])
        n_contacts = len(state["contact_records"])
        contact_slop = float(spec["lam"]) * D_EQ_LU
        # Caller-supplied external channel (the muscle lane writes these in
        # place each tick; zero-filled here when absent).
        ext_force = state.get("ext_force")
        if ext_force is None:
            ext_force = np.zeros((n_links, 3), dtype=np.float64)
        ext_torque = state.get("ext_torque")
        if ext_torque is None:
            ext_torque = np.zeros((n_links, 3), dtype=np.float64)
        # Muscle motor channel (the controller writes these each tick).
        motor_parent = state.get("motor_parent")
        if motor_parent is None:
            motor_parent = np.zeros(0, dtype=np.int64)
            motor_child = np.zeros(0, dtype=np.int64)
            motor_joint = np.zeros(0, dtype=np.int64)
            motor_axis = np.zeros((0, 3), dtype=np.float64)
            motor_target = np.zeros(0, dtype=np.float64)
            motor_lmax = np.zeros(0, dtype=np.float64)
        else:
            motor_child = state["motor_child"]
            motor_joint = state["motor_joint"]
            motor_axis = state["motor_axis"]
            motor_target = state["motor_target"]
            motor_lmax = state["motor_lmax"]
        motor_impulses = np.zeros(motor_parent.shape[0], dtype=np.float64)
        joint_impulses_lin = np.zeros((n_joints, 3), dtype=np.float64)
        joint_impulses_ang = np.zeros((n_joints, 3), dtype=np.float64)
        lig_impulses_lin = np.zeros((n_lig, 3), dtype=np.float64)
        lig_impulses_ang = np.zeros((n_lig, 3), dtype=np.float64)
        # Passive-play membrane (2026-08-08, forensics: the sweep
        # ligaments hold 1.67x body weight with every muscle cut --
        # no relaxed body does that).  Anatomy: a ligament is SLACK
        # through the joint's play band and stiffens at its end.  The
        # play is the measured d_eq_m = lam * D_EQ_LU, added to the
        # effective rest length; zero inside the band by construction.
        # Default off: legacy path stays bit-identical.
        lig_rest_eff = state["lig_rest"]
        if state.get("lig_play_band", False):
            lig_rest_eff = lig_rest_eff + float(spec["lam"]) * D_EQ_LU
        # Ligament force limit (the toe-chain membrane, 2026-08-08):
        # rows clamped to f_max * dt so taut ligaments cannot overrule
        # the muscles 30:1 post-solve.  Entries of zero = no limit
        # (legacy default, bit-identical).
        lig_fmax_eff = state["lig_fmax"] \
            if state.get("lig_force_limit", False) \
            else np.zeros(n_lig, dtype=np.float64)
        contact_impulses = np.zeros((n_contacts, 3), dtype=np.float64)
        # Position-pass ghost instrumentation (ghost-source probe,
        # 2026-08-08): per-link rotations applied at position level,
        # invisible in ang_vel, split by block.  Accounting only.
        ghost_coinc = np.zeros((n_links, 3), dtype=np.float64)
        ghost_lig = np.zeros((n_links, 3), dtype=np.float64)
        ghost_lock = np.zeros((n_links, 3), dtype=np.float64)
        # The direct solve is the default: the sequential (Gauss-Seidel)
        # solver diverges at this skeleton's mass ratios (module docstring).
        # state["solver"] = "sequential" keeps the old scheme for comparison.
        # state["contacts_in_solve"] = True (v3a) moves the ground-contact
        # rows into the direct solve; default off, the feet are grounded by
        # the post-solve sequential sweep (pre-v3a path).
        args = (
            state["pos"], state["quat"], state["lin_vel"], state["ang_vel"],
            state["mass"], state["inv_mass"],
            state["inertia_diag_local"], state["inv_inertia_diag_local"],
            state["joint_parent"], state["joint_child"], state["joint_dof"],
            state["joint_axes_arr"],
            state["r_joint_parent_local"], state["r_joint_child_local"],
            state["joint_q_rel0"],
            state["lig_idx_a"], state["lig_idx_b"],
            state["lig_off_a"], state["lig_off_b"], lig_rest_eff,
            lig_fmax_eff,
            state["contact_link_idx"], state["contact_off_local"],
            contact_slop, float(dt), int(n_proj_iters),
            int(state.get("rotation_locks", True)),
            ext_force, ext_torque,
            motor_parent, motor_child, motor_joint, motor_axis,
            motor_target, motor_lmax, motor_impulses,
            joint_impulses_lin, joint_impulses_ang,
            lig_impulses_lin, lig_impulses_ang,
            contact_impulses,
            ghost_coinc, ghost_lig, ghost_lock,
        )
        if state.get("solver", "direct") == "direct":
            _numba_step_core_direct(
                *args, int(state.get("contacts_in_solve", False)),
                int(state.get("contact_friction", True)),
                int(state.get("pos_pass_mode", 0)))
        else:
            _numba_step_core(*args, int(state.get("pos_pass_mode", 0)))
        state["joint_impulses_lin"] = joint_impulses_lin
        state["joint_impulses_ang"] = joint_impulses_ang
        state["motor_impulses"] = motor_impulses
        state["lig_impulses_lin"] = lig_impulses_lin
        state["lig_impulses_ang"] = lig_impulses_ang
        state["contact_impulses"] = contact_impulses
        state["ghost_coinc"] = ghost_coinc
        state["ghost_lig"] = ghost_lig
        state["ghost_lock"] = ghost_lock
        # Spring channel is retired: external contact force is identically zero;
        # the whole normal/friction load flows through contact_impulses now.
        state["contact_forces_ext"] = np.zeros((n_contacts, 3), dtype=np.float64)
        state["dt"] = float(dt)
        return state

    return _step_python(spec, state, dt, n_proj_iters)


def _step_python(spec: dict[str, Any], state: dict[str, Any], dt: float,
                 n_proj_iters: int = 20) -> dict[str, Any]:
    """Pure-Python reference implementation of step() (fallback).

    The constraint loop is position-based (PBD): each iteration projects joint
    centers together and corrects relative orientation according to dof_class,
    then projects penetrating foot contacts to the ground plane.  Velocities are
    derived from the corrected positions at the end of the step, which keeps the
    77-link tree stable where a pure velocity-impulse solver diverges.

    Parameters
    ----------
    spec : dict
        Kinematic spec from LightEngine.kinematic.build_spec().
    state : dict
        State dict from init_state().
    dt : float
        Time step in seconds.
    n_proj_iters : int
        Number of position-projection iterations per tick.

    Returns
    -------
    state : dict
        The same state dict, updated in place.
    """
    if dt <= 0.0:
        raise ValueError("dt must be positive")

    if state.get("motor_parent") is not None and \
            len(state.get("motor_target", ())) > 0:
        raise RuntimeError(
            "The Python fallback does not implement muscle motor rows; "
            "the muscle lane requires the numba direct solve."
        )
    if state.get("contacts_in_solve"):
        raise RuntimeError(
            "The Python fallback does not implement contacts_in_solve; "
            "the v3a contact rows require the numba direct solve."
        )

    n_links = len(state["link_names"])
    n_contacts = len(state["contact_records"])
    pos = state["pos"]
    quat = state["quat"]
    lin_vel = state["lin_vel"]
    ang_vel = state["ang_vel"]
    mass = state["mass"]
    inv_mass = state["inv_mass"]
    inv_inertia_diag_local = state["inv_inertia_diag_local"]

    g_vec = np.array([0.0, 0.0, -GRAVITY_MPS2], dtype=np.float64)
    k_contact = state["k_contact"]
    c_contact = state["c_contact"]
    mu = MU_CONTACT

    # ------------------------------------------------------------------
    # 1. External forces: gravity + contact penalty.
    # ------------------------------------------------------------------
    forces = np.zeros((n_links, 3), dtype=np.float64)
    torques = np.zeros((n_links, 3), dtype=np.float64)

    # Gravity.
    for i in range(n_links):
        forces[i] = mass[i] * g_vec

    # Caller-supplied external channel (the muscle lane; zero when unused).
    ext_force = state.get("ext_force")
    ext_torque = state.get("ext_torque")
    if ext_force is not None:
        forces += ext_force
    if ext_torque is not None:
        torques += ext_torque

    # Ligaments are handled as unilateral distance constraints inside the PBD
    # projection loop below, NOT as explicit springs.  Explicit ligament springs
    # with the derived stiffness k ~ F_max / d_eq_m produce dt*omega >> 2 on the
    # small vertebrae and explode the assembly (see module docstring).

    # Contact penalty + friction (repulsion-only, unilateral).
    contact_forces_ext = np.zeros((n_contacts, 3), dtype=np.float64)
    for ci in range(n_contacts):
        rec = state["contact_records"][ci]
        li = rec["link_idx"]
        if mass[li] <= 0.0:
            continue
        q = quat[li]
        R = transforms.to_matrix(q)
        r = R @ rec["offset_local"]
        p_world = pos[li] + r
        if p_world[2] >= 0.0:
            continue

        v_contact = lin_vel[li] + np.cross(ang_vel[li], r)
        v_z = v_contact[2]
        penetration = -p_world[2]

        I_inv = _world_inertia_inv(q, inv_inertia_diag_local[li])
        rn = np.cross(r, np.array([0.0, 0.0, 1.0]))
        denom_t_base = inv_mass[li] + float(rn @ (I_inv @ rn))
        if denom_t_base > 1e-15:
            m_eff_t = 1.0 / denom_t_base
        else:
            m_eff_t = mass[li]

        f_n = k_contact * penetration + c_contact * max(0.0, -v_z)
        if f_n < 0.0:
            f_n = 0.0
        f_contact = f_n * np.array([0.0, 0.0, 1.0], dtype=np.float64)

        v_tan = v_contact - v_z * np.array([0.0, 0.0, 1.0], dtype=np.float64)
        v_tan_mag = float(np.linalg.norm(v_tan))
        if v_tan_mag > 1e-12:
            t_dir = v_tan / v_tan_mag
            f_t_max = mu * f_n
            f_t_dv = m_eff_t * v_tan_mag / dt
            f_t_mag = min(f_t_max, f_t_dv)
            f_contact -= f_t_mag * t_dir

        forces[li] += f_contact
        torques[li] += np.cross(r, f_contact)
        contact_forces_ext[ci] = f_contact

    # ------------------------------------------------------------------
    # 2. Semi-implicit Euler velocity update.
    # ------------------------------------------------------------------
    for i in range(n_links):
        if mass[i] <= 0.0:
            continue
        lin_vel[i] += dt * forces[i] / mass[i]
        I_inv = _world_inertia_inv(quat[i], inv_inertia_diag_local[i])
        ang_vel[i] += dt * (I_inv @ torques[i])

    # ------------------------------------------------------------------
    # 3. Predicted positions.
    # ------------------------------------------------------------------
    pos_old = pos.copy()
    quat_old = quat.copy()
    for i in range(n_links):
        if mass[i] <= 0.0:
            continue
        pos[i] += dt * lin_vel[i]
        quat[i] += dt * _quat_derivative(quat[i], ang_vel[i])
        quat[i] = transforms.normalize(quat[i])

    # ------------------------------------------------------------------
    # 4. Iterated position-projection loop (PBD).
    # ------------------------------------------------------------------
    n_joints = len(state["joint_names"])
    contact_impulses = np.zeros((n_contacts, 3), dtype=np.float64)

    # Accumulate constraint impulses per joint so joint_reactions() can report
    # the reaction exerted by the parent on the child.  Values stored here are
    # impulses (N*s and Nm*s); joint_reactions() divides by dt to obtain forces.
    joint_impulses_lin = np.zeros((n_joints, 3), dtype=np.float64)
    joint_impulses_ang = np.zeros((n_joints, 3), dtype=np.float64)
    lig_impulses_lin = np.zeros((len(state["lig_records"]), 3), dtype=np.float64)
    lig_impulses_ang = np.zeros((len(state["lig_records"]), 3), dtype=np.float64)
    inv_dt = 1.0 / dt

    RELAX = 1.0  # PBD stiffness: full correction per projection (standard PBD).
    # 0.02 under-relaxation was measured 2026-08-07 to let joint errors grow
    # to meters, at which point err/r angular corrections left the small-angle
    # band and scrambled orientations (see _dynamics_numba constants).

    for _iteration in range(n_proj_iters):
        # ---- joint point constraints ----
        # Position-based correction that moves joint centers together while also
        # rotating the attached bodies (standard rigid-body PBD).  This is what
        # lets a hinged body swing under gravity instead of just translating.
        for ji in range(n_joints):
            pa_idx = int(state["joint_parent"][ji])
            cb_idx = int(state["joint_child"][ji])
            if mass[pa_idx] <= 0.0 and mass[cb_idx] <= 0.0:
                continue

            R_p = transforms.to_matrix(quat[pa_idx])
            R_c = transforms.to_matrix(quat[cb_idx])
            r_p = R_p @ state["r_joint_parent_local"][ji]
            r_c = R_c @ state["r_joint_child_local"][ji]
            p_p = pos[pa_idx] + r_p
            p_c = pos[cb_idx] + r_c
            delta = p_c - p_p
            err = float(np.linalg.norm(delta))
            if err < 1e-12:
                continue
            n = delta / err

            # Generalized inverse masses along direction n.
            I_inv_p = _world_inertia_inv(quat[pa_idx], inv_inertia_diag_local[pa_idx])
            I_inv_c = _world_inertia_inv(quat[cb_idx], inv_inertia_diag_local[cb_idx])
            rn_p = np.cross(r_p, n)
            rn_c = np.cross(r_c, n)
            w_p = inv_mass[pa_idx] + float(rn_p @ (I_inv_p @ rn_p))
            w_c = inv_mass[cb_idx] + float(rn_c @ (I_inv_c @ rn_c))
            denom = w_p + w_c
            if denom <= 1e-15:
                continue
            c_mag = RELAX * err / denom

            # Point-constraint impulse on the child (linear + moment about COM).
            j_point_child = -c_mag * n * inv_dt
            joint_impulses_lin[ji] += j_point_child
            joint_impulses_ang[ji] += np.cross(r_c, j_point_child)

            if mass[pa_idx] > 0.0:
                # Translation of COM.
                pos[pa_idx] += inv_mass[pa_idx] * c_mag * n
                # Rotation around COM from the impulse at the joint.
                dtheta_p = I_inv_p @ (c_mag * rn_p)
                if np.linalg.norm(dtheta_p) > 1e-15:
                    _, quat[pa_idx] = _rotate_body_around_point(
                        pos[pa_idx], quat[pa_idx], pos[pa_idx],
                        dtheta_p, float(np.linalg.norm(dtheta_p))
                    )
            if mass[cb_idx] > 0.0:
                pos[cb_idx] -= inv_mass[cb_idx] * c_mag * n
                dtheta_c = I_inv_c @ (c_mag * rn_c)
                if np.linalg.norm(dtheta_c) > 1e-15:
                    _, quat[cb_idx] = _rotate_body_around_point(
                        pos[cb_idx], quat[cb_idx], pos[cb_idx],
                        -dtheta_c, float(np.linalg.norm(dtheta_c))
                    )

        # ---- joint rotation constraints ----
        for ji in range(n_joints):
            pa_idx = int(state["joint_parent"][ji])
            cb_idx = int(state["joint_child"][ji])
            if mass[pa_idx] <= 0.0 and mass[cb_idx] <= 0.0:
                continue

            dof = int(state["joint_dof"][ji])
            if dof == 3:
                continue  # ball-cup: no rotational lock

            q_p = quat[pa_idx]
            q_c = quat[cb_idx]
            R_p = transforms.to_matrix(q_p)

            # Relative rotation parent -> child.
            q_rel = transforms.multiply(transforms.conjugate(q_p), q_c)
            if q_rel[0] < 0.0:
                q_rel = -q_rel

            # Deviation from the zero-pose relative orientation.
            q_rel0 = state["joint_q_rel0"][ji]
            q_err = transforms.multiply(transforms.conjugate(q_rel0), q_rel)
            if q_err[0] < 0.0:
                q_err = -q_err

            # Rotation vector of the error.  NOTE: q_rel / q_err live in the
            # parent's LOCAL frame (q_rel = q_p^-1 * q_c); the rotation vector
            # must be transformed to world before use (frame bug fixed
            # 2026-08-07, verified experimentally).
            sin_half = float(np.linalg.norm(q_err[1:]))
            if sin_half < 1e-12:
                continue
            rel_axis = q_err[1:] / sin_half
            rel_angle = 2.0 * math.atan2(sin_half, float(q_err[0]))
            theta = rel_angle * (R_p @ rel_axis)

            # Determine locked components in parent world frame.
            axes_local = state["joint_axes_local"][ji]
            if dof == 0:
                # Suture: lock all three axes.
                theta_locked = theta.copy()
            elif dof == 1:
                # Hinge: lock components perpendicular to hinge axis.
                axis = R_p @ axes_local[0]
                axis = axis / (np.linalg.norm(axis) + 1e-15)
                theta_parallel = np.dot(theta, axis) * axis
                theta_locked = theta - theta_parallel
            elif dof == 2:
                # Saddle: lock component perpendicular to both allowed axes.
                ax1 = R_p @ axes_local[0]
                ax2 = R_p @ axes_local[1]
                locked_axis = np.cross(ax1, ax2)
                n_locked = np.linalg.norm(locked_axis)
                if n_locked < 1e-12:
                    locked_axis = np.cross(ax1, np.array([0.0, 0.0, 1.0]))
                    n_locked = np.linalg.norm(locked_axis)
                locked_axis = locked_axis / (n_locked + 1e-15)
                theta_locked = np.dot(theta, locked_axis) * locked_axis
            else:
                raise RuntimeError(f"Unknown DoF value {dof}")

            err_angle = float(np.linalg.norm(theta_locked))
            if err_angle < 1e-12:
                continue
            err_axis = theta_locked / err_angle

            I_inv_p = _world_inertia_inv(q_p, inv_inertia_diag_local[pa_idx])
            I_inv_c = _world_inertia_inv(q_c, inv_inertia_diag_local[cb_idx])
            ia = float(err_axis @ (I_inv_p @ err_axis))
            ib = float(err_axis @ (I_inv_c @ err_axis))
            denom = ia + ib
            if denom <= 1e-15:
                continue

            # Correction angles: split proportional to inverse inertia so the
            # lighter body does most of the rotating.
            alpha_p = RELAX * ia / denom
            alpha_c = RELAX * ib / denom

            # Pure torque constraint: rotate each body around its own COM so the
            # joint does not introduce spurious linear reaction components.
            dtheta_p_vec = alpha_p * err_angle * err_axis
            dtheta_c_vec = -alpha_c * err_angle * err_axis

            # Angular impulse on child from this rotational correction (about COM).
            I_c_world = transforms.to_matrix(q_c).T @ np.diag(
                state["inertia_diag_local"][cb_idx]
            ) @ transforms.to_matrix(q_c)
            joint_impulses_ang[ji] += I_c_world @ dtheta_c_vec * inv_dt

            if mass[pa_idx] > 0.0:
                _, quat[pa_idx] = _rotate_body_around_point(
                    pos[pa_idx], quat[pa_idx], pos[pa_idx], err_axis, alpha_p * err_angle
                )
            if mass[cb_idx] > 0.0:
                _, quat[cb_idx] = _rotate_body_around_point(
                    pos[cb_idx], quat[cb_idx], pos[cb_idx], err_axis, -alpha_c * err_angle
                )

        # ---- ligament unilateral distance constraints ----
        # Tension-only: if the attachment separation exceeds rest_length, project
        # the two points back to rest_length.  This is the rope-law compilation:
        # near-rigid in tension, zero force when slack.  Splitting the correction
        # by generalized inverse mass keeps angular effects correct.
        # Passive-play membrane (mirrors the numba path): with
        # state["lig_play_band"] the effective rest gains the measured
        # joint play d_eq_m -- slack through the band, stiff at its end.
        lig_play = float(spec["lam"]) * D_EQ_LU \
            if state.get("lig_play_band", False) else 0.0
        for li, lig in enumerate(state["lig_records"]):
            ia = lig["idx_a"]
            ib = lig["idx_b"]
            if mass[ia] <= 0.0 and mass[ib] <= 0.0:
                continue

            Ra = transforms.to_matrix(quat[ia])
            Rb = transforms.to_matrix(quat[ib])
            r_a = Ra @ lig["offset_a_local"]
            r_b = Rb @ lig["offset_b_local"]
            pa = pos[ia] + r_a
            pb = pos[ib] + r_b
            vec = pb - pa
            L = float(np.linalg.norm(vec))
            if L <= lig["rest_length_m"] + lig_play + 1e-15:
                continue

            n = vec / L
            delta = L - lig["rest_length_m"] - lig_play

            I_inv_a = _world_inertia_inv(quat[ia], inv_inertia_diag_local[ia])
            I_inv_b = _world_inertia_inv(quat[ib], inv_inertia_diag_local[ib])
            rn_a = np.cross(r_a, n)
            rn_b = np.cross(r_b, n)
            w_a = inv_mass[ia] + float(rn_a @ (I_inv_a @ rn_a))
            w_b = inv_mass[ib] + float(rn_b @ (I_inv_b @ rn_b))
            denom = w_a + w_b
            if denom <= 1e-15:
                continue
            c_mag = RELAX * delta / denom
            # Force-limit membrane (mirrors the numba sweeps): the
            # correction impulse is capped at f_max * dt per tick.
            if state.get("lig_force_limit", False):
                cap = float(lig["f_max"]) * dt * dt
                used = float(lig_impulses_lin[li] @ n) * dt
                avail = cap - used
                if avail <= 0.0:
                    continue
                c_mag = min(c_mag, avail)

            # Impulse on body A (toward B) and the corresponding moment.
            j_a = c_mag * n * inv_dt
            lig_impulses_lin[li] += j_a
            lig_impulses_ang[li] += np.cross(r_a, j_a)

            if mass[ia] > 0.0:
                pos[ia] += inv_mass[ia] * c_mag * n
                dtheta_a = I_inv_a @ (c_mag * rn_a)
                if np.linalg.norm(dtheta_a) > 1e-15:
                    _, quat[ia] = _rotate_body_around_point(
                        pos[ia], quat[ia], pos[ia],
                        dtheta_a, float(np.linalg.norm(dtheta_a))
                    )
            if mass[ib] > 0.0:
                pos[ib] -= inv_mass[ib] * c_mag * n
                dtheta_b = I_inv_b @ (c_mag * rn_b)
                if np.linalg.norm(dtheta_b) > 1e-15:
                    _, quat[ib] = _rotate_body_around_point(
                        pos[ib], quat[ib], pos[ib],
                        -dtheta_b, float(np.linalg.norm(dtheta_b))
                    )

    # ------------------------------------------------------------------
    # 5. Derive linear and angular velocity from corrected poses.
    #
    #    In PBD the position projections encode the constraint impulses.
    #    Deriving velocity from the corrected positions/quaternions lets
    #    those impulses enter the dynamics.  This is essential for hinged
    #    bodies: without it the angular velocity would stay zero and the
    #    rod would not swing.
    # ------------------------------------------------------------------
    for i in range(n_links):
        if mass[i] <= 0.0:
            continue
        lin_vel[i] = (pos[i] - pos_old[i]) / dt
        ang_vel[i] = _derive_angular_velocity(quat_old[i], quat[i], dt)

    # Store external forces and accumulated constraint impulses.
    state["joint_impulses_lin"] = joint_impulses_lin
    state["joint_impulses_ang"] = joint_impulses_ang
    state["lig_impulses_lin"] = lig_impulses_lin
    state["lig_impulses_ang"] = lig_impulses_ang
    state["contact_impulses"] = contact_impulses
    state["contact_forces_ext"] = contact_forces_ext
    state["dt"] = float(dt)

    return state


# ---------------------------------------------------------------------------
# Telemetry / reaction queries
# ---------------------------------------------------------------------------
def state_poses(spec: dict[str, Any], state: dict[str, Any]) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Return {link: (pos_m, quat)} for the current state.

    pos_m is the proximal endpoint in meters, matching the FK convention.
    """
    links = spec["links"]
    poses: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for name, i in state["name_to_idx"].items():
        q = state["quat"][i]
        pos_com = state["pos"][i]
        pos_prox = pos_com - transforms.rotate(q, links[name]["com_offset_m"])
        poses[name] = (pos_prox, q.copy())
    return poses


def center_of_mass(spec: dict[str, Any], state: dict[str, Any]) -> np.ndarray:
    """Return whole-body COM in meters."""
    total_mass = 0.0
    com = np.zeros(3, dtype=np.float64)
    for name, i in state["name_to_idx"].items():
        m = state["mass"][i]
        com += m * state["pos"][i]
        total_mass += m
    if total_mass <= 0.0:
        return com
    return com / total_mass


def joint_reactions(spec: dict[str, Any], state: dict[str, Any]) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Return {joint_name: (force_xyz_N, torque_xyz_Nm)} at the joint center.

    The force/torque is the reaction exerted BY the parent ON the child during
    the last step, averaged over the timestep.
    """
    dt = float(state.get("dt", 0.0))
    if dt <= 0.0:
        raise RuntimeError("joint_reactions called before a step with positive dt")
    inv_dt = 1.0 / dt

    reactions: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for ji, jname in enumerate(state["joint_names"]):
        cb_idx = int(state["joint_child"][ji])
        q_c = state["quat"][cb_idx]
        R_c = transforms.to_matrix(q_c)
        r_c = R_c @ state["r_joint_child_local"][ji]

        j_lin = state["joint_impulses_lin"][ji] * inv_dt
        j_ang = state["joint_impulses_ang"][ji] * inv_dt

        force_on_child = j_lin
        torque_on_child = np.cross(r_c, j_lin) + j_ang
        reactions[jname] = (force_on_child, torque_on_child)
    return reactions


def ligament_reactions(spec: dict[str, Any], state: dict[str, Any]) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Return {ligament_name: (force_xyz_N, torque_xyz_Nm)} at attachment A.

    The force/torque is the tension exerted BY the ligament ON body A (the link
    named anchor_a) during the last step, averaged over the timestep.  Because
    the ligament is a unilateral distance constraint, the force is zero when the
    ligament is slack (length <= rest_length); when taut it pulls A toward B.
    """
    dt = float(state.get("dt", 0.0))
    if dt <= 0.0:
        raise RuntimeError("ligament_reactions called before a step with positive dt")
    inv_dt = 1.0 / dt

    reactions: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for li, lig in enumerate(state["lig_records"]):
        ia = lig["idx_a"]
        q_a = state["quat"][ia]
        R_a = transforms.to_matrix(q_a)
        r_a = R_a @ lig["offset_a_local"]

        j_lin = state["lig_impulses_lin"][li] * inv_dt
        j_ang = state["lig_impulses_ang"][li] * inv_dt

        force_on_a = j_lin
        torque_on_a = np.cross(r_a, j_lin) + j_ang
        reactions[lig["name"]] = (force_on_a, torque_on_a)
    return reactions


def contact_forces(spec: dict[str, Any], state: dict[str, Any]) -> dict[str, np.ndarray]:
    """Return {contact_record_name: force_vector_N} for each active contact.

    The returned force is the sum of the external spring-damper penalty and the
    hard velocity-constraint impulse accumulated during the last step, divided
    by dt.
    """
    dt = float(state.get("dt", 0.0))
    if dt <= 0.0:
        raise RuntimeError("contact_forces called before a step with positive dt")
    inv_dt = 1.0 / dt
    forces: dict[str, np.ndarray] = {}
    for ci, rec in enumerate(state["contact_records"]):
        f_ext = state["contact_forces_ext"][ci]
        f_impulse = state["contact_impulses"][ci] * inv_dt
        f_total = f_ext + f_impulse
        if np.linalg.norm(f_total) > 1e-18:
            forces[f"{rec['side']}_{ci}"] = f_total
    return forces
