"""
Cyclic Coordinate Descent inverse kinematics for Lane K1.

Only revolute-capable joints move (hinge, saddle, ball-cup); sutures are frozen.
The algorithm walks the chain from end effector toward the root and updates
each joint angle to reduce the distance to the target.  Updates are expressed
in the parent link's local frame to match the forward-kinematics convention.
"""

from __future__ import annotations

from typing import Any

import math

import numpy as np

from LightEngine.kinematic import transforms
from LightEngine.kinematic.fk import forward_kinematics
from LightEngine.kinematic.skeleton_spec import HINGE, SADDLE, BALL_CUP, SUTURE


def _chain_to_root(spec: dict[str, Any], end_link: str) -> list[str]:
    """Return [end_link, ..., root] by following parent pointers."""
    links = spec["links"]
    chain: list[str] = []
    node = end_link
    while node is not None:
        chain.append(node)
        parent = links[node]["parent_name"]
        node = parent
    return chain


def _hinge_update(r: np.ndarray, t: np.ndarray,
                  axis_world: np.ndarray) -> float:
    """Return the scalar angle update that swings r toward t around axis_world.

    DERIVED-GEOMETRY: project r and t onto the plane perpendicular to the hinge
    axis and use atan2 of the perpendicular component and the dot product.
    """
    r = np.asarray(r, dtype=np.float64).reshape(3)
    t = np.asarray(t, dtype=np.float64).reshape(3)
    axis = np.asarray(axis_world, dtype=np.float64).reshape(3)
    n = float(np.linalg.norm(axis))
    if n < 1e-12:
        return 0.0
    axis = axis / n

    r_proj = r - np.dot(r, axis) * axis
    t_proj = t - np.dot(t, axis) * axis
    r_n = float(np.linalg.norm(r_proj))
    t_n = float(np.linalg.norm(t_proj))
    if r_n < 1e-12 or t_n < 1e-12:
        return 0.0

    cross = np.cross(r_proj, t_proj)
    sin_a = float(np.dot(cross, axis))
    cos_a = float(np.dot(r_proj, t_proj))
    return float(math.atan2(sin_a, cos_a))


def _ball_cup_update(r: np.ndarray, t: np.ndarray) -> np.ndarray:
    """Return the world-frame minimal rotation quaternion aligning r to t."""
    r = np.asarray(r, dtype=np.float64).reshape(3)
    t = np.asarray(t, dtype=np.float64).reshape(3)
    r_n = float(np.linalg.norm(r))
    t_n = float(np.linalg.norm(t))
    if r_n < 1e-12 or t_n < 1e-12:
        return np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)

    r_u = r / r_n
    t_u = t / t_n
    dot = float(np.clip(np.dot(r_u, t_u), -1.0, 1.0))
    angle = math.acos(dot)
    axis = np.cross(r_u, t_u)
    a_n = float(np.linalg.norm(axis))
    if a_n < 1e-12:
        return np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
    axis = axis / a_n
    return transforms.from_axis_angle(axis, angle)


def _slerp(q0: np.ndarray, q1: np.ndarray, t: float) -> np.ndarray:
    """Spherical linear interpolation between two unit quaternions.

    DERIVED-GEOMETRY: used by the ball-cup CCD step to scale a world-frame
    rotation by the gain without breaking the quaternion normalization.
    """
    q0 = transforms.normalize(q0)
    q1 = transforms.normalize(q1)
    dot = float(np.clip(np.dot(q0, q1), -1.0, 1.0))
    if dot < 0.0:
        q1 = -q1
        dot = -dot
    if dot > 0.9995:
        result = q0 + t * (q1 - q0)
        return transforms.normalize(result)
    theta_0 = math.acos(dot)
    theta = theta_0 * t
    sin_theta = math.sin(theta)
    sin_theta_0 = math.sin(theta_0)
    s0 = math.cos(theta) - dot * sin_theta / sin_theta_0
    s1 = sin_theta / sin_theta_0
    return transforms.normalize(s0 * q0 + s1 * q1)


def ik(
    spec: dict[str, Any],
    joint_angles: dict[str, Any],
    end_link: str,
    target_pos: np.ndarray,
    max_iter: int = 50,
    tol: float = 1e-6,
    gain: float = 0.5,
) -> dict[str, Any]:
    """Solve for joint angles that bring end_link near target_pos.

    Parameters
    ----------
    spec : dict
        Kinematic spec from LightEngine.kinematic.build_spec().
    joint_angles : dict[str, Any]
        Starting angles; the returned dict is a copy updated by CCD.
    end_link : str
        Link whose proximal endpoint is the end effector.
    target_pos : array-like
        Target position in lu.
    max_iter : int
        Maximum CCD iterations.
    tol : float
        Distance tolerance in lu.

    Returns
    -------
    angles : dict[str, Any]
        Updated joint angles.  Same format as forward_kinematics().
    """
    links = spec["links"]
    joints = spec["joints"]
    target = np.asarray(target_pos, dtype=np.float64).reshape(3)

    if end_link not in links:
        raise KeyError(f"End link {end_link!r} not in spec")

    # Work on a shallow copy so the caller's input is not mutated.
    angles = {k: v for k, v in joint_angles.items()}

    chain = _chain_to_root(spec, end_link)
    if len(chain) < 2:
        return angles

    for _ in range(max_iter):
        poses = forward_kinematics(spec, angles)
        end_p, end_q = poses[end_link]
        end_length = links[end_link]["length_lu"]
        # End effector is the link's distal endpoint.
        end_pos = end_p + transforms.rotate(end_q, np.array([0.0, 0.0, end_length]))
        err = float(np.linalg.norm(end_pos - target))
        if err < tol:
            break

        # Walk from end effector toward root, skipping the root itself.
        for link_name in chain[:-1]:
            link = links[link_name]
            joint = joints[link["joint_name"]]
            dof = joint["dof_class"]
            if dof == SUTURE:
                continue

            # Joint center in world, using the current link pose.
            p_link, q_link = poses[link_name]
            J_child_lu = joint["center_child_local_lu"]
            j_world = p_link + transforms.rotate(q_link, J_child_lu)

            parent_name = joint["parent_link"]
            parent_p, parent_q = poses[parent_name]

            r = end_pos - j_world
            t = target - j_world

            if dof == HINGE:
                axis_parent_local = np.asarray(joint["axes"][0], dtype=np.float64)
                axis_world = transforms.rotate(parent_q, axis_parent_local)
                delta = _hinge_update(r, t, axis_world)
                current = float(angles.get(joint["name"], 0.0))
                angles[joint["name"]] = current + gain * delta

            elif dof == SADDLE:
                current = np.asarray(angles.get(joint["name"], np.zeros(2)),
                                     dtype=np.float64).copy()
                for idx, ax in enumerate(joint["axes"]):
                    axis_parent_local = np.asarray(ax, dtype=np.float64)
                    axis_world = transforms.rotate(parent_q, axis_parent_local)
                    delta = _hinge_update(r, t, axis_world)
                    current[idx] += gain * delta
                angles[joint["name"]] = current

            elif dof == BALL_CUP:
                q_world_update = _ball_cup_update(r, t)
                # Scale the world update by gain by interpolating toward identity.
                q_identity = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
                q_world_update = _slerp(q_identity, q_world_update, gain)
                # Convert world update to parent-local joint update:
                # q_joint_new = parent_q^-1 * q_world_update * parent_q * q_joint
                q_update_parent = transforms.multiply(
                    transforms.multiply(transforms.conjugate(parent_q), q_world_update),
                    parent_q,
                )
                current_q = transforms.normalize(
                    np.asarray(angles.get(joint["name"], [1.0, 0.0, 0.0, 0.0]),
                               dtype=np.float64)
                )
                angles[joint["name"]] = transforms.multiply(q_update_parent, current_q)

    return angles
