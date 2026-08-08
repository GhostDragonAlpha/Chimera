"""
Forward kinematics for the 77-link StandingHuman tree (Lane K1).

Positions are returned in light units (lu) to match the source joint dictionary.
The recursive transform follows the general parent-child attachment:

    T_child = T_parent * translate(J_parent) * R_joint * translate(-J_child)

where J_parent is the joint center in the parent local frame and J_child is the
same joint center in the child local frame.  This handles both the usual
"child-prox-attaches-to-parent-dist" case and the spine case where the child
attaches by its distal end.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from LightEngine.kinematic import transforms
from LightEngine.kinematic.skeleton_spec import (
    BALL_CUP, SADDLE, HINGE, SUTURE, _DOF_COUNT,
)


def _joint_rotation(joint: dict[str, Any],
                    angle_input: Any | None) -> np.ndarray:
    """Return the unit quaternion for a joint's angle input.

    DERIVED-GEOMETRY: the rotation is expressed in the parent link's local frame
    (the joint rotation frame).  Input formats:
      - hinge: scalar float
      - saddle: array-like of two floats
      - ball-cup: unit quaternion [w,x,y,z] OR axis-angle 3-vector
      - suture: ignored (identity)
    """
    dof = joint["dof_class"]
    if dof == SUTURE:
        return np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)

    if angle_input is None:
        return np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)

    if dof == HINGE:
        try:
            angle = float(angle_input)
        except Exception as exc:
            raise ValueError(
                f"Hinge joint {joint['name']!r} expects a scalar angle"
            ) from exc
        axis = np.asarray(joint["axes"][0], dtype=np.float64)
        return transforms.from_axis_angle(axis, angle)

    if dof == SADDLE:
        arr = np.asarray(angle_input, dtype=np.float64)
        if arr.shape != (2,):
            raise ValueError(
                f"Saddle joint {joint['name']!r} expects a 2-element angle vector"
            )
        ax1 = np.asarray(joint["axes"][0], dtype=np.float64)
        ax2 = np.asarray(joint["axes"][1], dtype=np.float64)
        q1 = transforms.from_axis_angle(ax1, float(arr[0]))
        q2 = transforms.from_axis_angle(ax2, float(arr[1]))
        # Rotate about axis 1 first, then axis 2.
        return transforms.multiply(q2, q1)

    if dof == BALL_CUP:
        arr = np.asarray(angle_input, dtype=np.float64)
        if arr.shape == (4,):
            return transforms.normalize(arr)
        if arr.shape == (3,):
            angle = float(np.linalg.norm(arr))
            if angle < 1e-12:
                return np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
            axis = arr / angle
            return transforms.from_axis_angle(axis, angle)
        raise ValueError(
            f"Ball-cup joint {joint['name']!r} expects a 4-element quaternion "
            f"or a 3-element axis-angle vector, got shape {arr.shape}"
        )

    raise ValueError(f"Unknown DoF class {dof!r}")


def _topological_order(spec: dict[str, Any]) -> list[str]:
    """Return links in parent-before-child order."""
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
        # Deterministic child order for reproducibility.
        for child in sorted(children_of[node]):
            if child not in visited:
                stack.append(child)

    if len(order) != len(links):
        raise RuntimeError("Tree traversal did not reach all links")
    return order


def forward_kinematics(
    spec: dict[str, Any],
    joint_angles: dict[str, Any] | None = None,
) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Compute the world pose of every link.

    Parameters
    ----------
    spec : dict
        Output of LightEngine.kinematic.build_spec().
    joint_angles : dict[str, Any] | None
        Mapping joint_name -> angle(s).  Missing joints are treated as zero.
        Format per DoF class:
          - hinge: scalar float
          - saddle: 2-element array
          - ball-cup: unit quaternion [w,x,y,z] or axis-angle 3-vector
          - suture: ignored

    Returns
    -------
    poses : dict[str, (position_lu, quaternion)]
        position_lu is the link's proximal endpoint in lu.
        quaternion is a unit [w,x,y,z] quaternion mapping local vectors to world.
    """
    if joint_angles is None:
        joint_angles = {}

    links = spec["links"]
    joints = spec["joints"]
    order = _topological_order(spec)

    # Zero-pose transforms are derived from the anatomical basis of each link.
    p_zero: dict[str, np.ndarray] = {}
    q_zero: dict[str, np.ndarray] = {}
    for name, link in links.items():
        p_zero[name] = link["prox_lu"].copy()
        q_zero[name] = transforms.from_basis(
            link["basis_x"], link["basis_y"], link["basis_z"]
        )

    poses: dict[str, tuple[np.ndarray, np.ndarray]] = {}

    for name in order:
        link = links[name]
        if link["parent_name"] is None:
            poses[name] = (p_zero[name].copy(), q_zero[name].copy())
        else:
            joint = joints[link["joint_name"]]
            parent_name = joint["parent_link"]
            parent_p, parent_q = poses[parent_name]
            angle_input = joint_angles.get(joint["name"])
            q_joint = _joint_rotation(joint, angle_input)

            # Relative zero-pose transform of child w.r.t. parent:
            #   A = (T_parent^0)^-1 * T_child^0
            q_A = transforms.multiply(transforms.conjugate(q_zero[parent_name]),
                                      q_zero[name])
            p_A = transforms.rotate(
                transforms.conjugate(q_zero[parent_name]),
                p_zero[name] - p_zero[parent_name],
            )

            # Joint center in parent local frame; rotation is applied around it.
            J_parent = joint["center_parent_local_lu"]

            # T_child = T_parent * translate(J_parent) * R_joint *
            #           translate(-J_parent) * A
            q_child = transforms.multiply(
                transforms.multiply(parent_q, q_joint), q_A
            )
            p_child = parent_p + transforms.rotate(
                parent_q,
                J_parent + transforms.rotate(q_joint, p_A - J_parent),
            )
            poses[name] = (p_child, q_child)

    return poses


# Convenience alias used by tests and the IK lane.
FK_LU = "lu"
FK_M = "m"
