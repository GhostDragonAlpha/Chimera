"""
theStandingHuman v2-rigid: the muscle controller (Lane M3, motor-row form).

A tick-level servo over the actuator table of
LightEngine/kinematic/muscles.py.  Every number is derived there; this module
contains NO constants of its own -- only the measurement and command math.

Per tick, per free axis of each actuated joint, the controller fills one
MOTOR ROW for the direct solve (kinematic/_dynamics_numba.step_core_direct):
  theta_err = rotation vector of (q_rel * q_rel0^-1), projected on the free
              axis in the parent's frame (bind pose: q_rel0).
  axis_w    = the free axis rotated to world by the parent's orientation.
  target    = -omega_n * (theta_err - target_offset)   (rad/s) -- a
              first-order servo whose bandwidth is the joint's own fall rate
              omega_n: "the body responds at the rate the body falls"; the
              target_offset is the balanced-reference lean derived below.
              The implicit solve then
              drives the relative angular velocity to target, so the pose
              error decays with time constant 1/omega_n -- no overshoot by
              construction, and no explicit-integration stability cap (the
              muscle impulse is solved TOGETHER with the joint coincidence
              rows, not kicked in before them; measured 2026-08-08: the
              pre-solve couple form whipped light links to 2000 rad/s).
  lmax      = torque_limit_Nm * dt   (N s) -- the physiology force cap as an
              impulse bound; the solve hard-clamps |lambda| to it.

Motor rows apply equal-and-opposite angular impulses on child and parent
inside the constrained system: the net external wrench is zero by
construction, and the trunk receives the correction through the SAME solve
that carries its weight -- the impedance mismatch of the external-couple
form is gone.

Pose reference (DERIVED, not tuned): the raw bind pose is NOT balanced --
measured 2026-08-08, the bind-pose COM projects 7.75 cm behind the support
polygon centroid (1.25 cm inside the heel edge), a constant ~60 N m backward
moment from tick 0 (the K3 FRAME failure's geometry, unfixable by any muscle
law).  The controller therefore derives a BALANCED reference: a rigid lean
of the whole body about the ankle axes that puts the COM over the polygon
centroid -- the "ankle strategy" of standing biomechanics.  The lean angle
comes from the geometry (offset / COM height), the sign from the world-frame
lever a x r_com; nothing is chosen.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from LightEngine.kinematic import transforms
from LightEngine.kinematic.muscles import build_actuator_table


def _support_centroid_xy(state: dict[str, Any]) -> np.ndarray:
    """Centroid (world xy) of the foot contact points at the current pose."""
    pts = []
    for rec in state["contact_records"]:
        li = rec["link_idx"]
        R = transforms.to_matrix(state["quat"][li])
        p = state["pos"][li] + R @ rec["offset_local"]
        pts.append(p[:2])
    return np.mean(np.asarray(pts, dtype=np.float64), axis=0)


def _com_xy(state: dict[str, Any]) -> np.ndarray:
    """Whole-body COM (world xy) from the state arrays."""
    mass = state["mass"]
    total = float(np.sum(mass))
    if total <= 0.0:
        return np.zeros(2, dtype=np.float64)
    return (state["pos"][:, :2] * mass[:, None]).sum(axis=0) / total


class MuscleController:
    """Derived-bandwidth posture servo over the free dofs of the tree."""

    def __init__(self, spec: dict[str, Any], state: dict[str, Any],
                 physiology: dict[str, tuple[float, float]] | None = None,
                 dt: float = 1e-3) -> None:
        self.actuators = build_actuator_table(spec, state, physiology=physiology,
                                              dt=dt)
        self.dt = float(dt)
        self.enabled = True
        n = len(self.actuators)

        # Balanced reference: the rigid ankle lean that puts the COM over the
        # support centroid (module docstring: the derivation).  One offset
        # per actuator, nonzero only for joints whose CHILD LINK carries the
        # ground contacts (the ankles): the lean pivots the body there.
        contact_links = {int(r["link_idx"]) for r in state["contact_records"]}
        centroid = _support_centroid_xy(state)
        com = _com_xy(state)
        offset_vec = centroid - com
        for a in self.actuators:
            a["target_offset"] = 0.0
            if a["child_idx"] not in contact_links:
                continue
            q_p = state["quat"][a["parent_idx"]]
            axis_w = transforms.rotate(q_p, a["axis_local_parent"])
            # Joint center (world): child attachment point at the bind pose.
            R_c = transforms.to_matrix(state["quat"][a["child_idx"]])
            jc = state["pos"][a["child_idx"]] \
                + R_c @ state["r_joint_child_local"][a["joint_index"]]
            mass = state["mass"]
            com3 = (state["pos"] * mass[:, None]).sum(axis=0) / mass.sum()
            r = com3 - jc
            lever = np.cross(axis_w, r)
            lever_xy = np.linalg.norm(lever[:2])
            if lever_xy < 1e-9:
                continue
            # The measured relative angle theta counts child(foot)-in-parent
            # (shank); leaning the PARENT side by phi shifts theta by -phi.
            phi = float(np.dot(offset_vec, lever[:2]) / (lever_xy ** 2))
            a["target_offset"] = -phi

        # The motor channel: one row per actuated dof.  Arrays live in the
        # state so dynamics.step() picks them up; apply() rewrites the
        # per-tick fields (axis, target, lmax) each tick.
        state["motor_parent"] = np.array(
            [a["parent_idx"] for a in self.actuators], dtype=np.int64)
        state["motor_child"] = np.array(
            [a["child_idx"] for a in self.actuators], dtype=np.int64)
        state["motor_joint"] = np.array(
            [a["joint_index"] for a in self.actuators], dtype=np.int64)
        state["motor_axis"] = np.zeros((n, 3), dtype=np.float64)
        state["motor_target"] = np.zeros(n, dtype=np.float64)
        state["motor_lmax"] = np.array(
            [a["torque_limit_Nm"] * self.dt for a in self.actuators],
            dtype=np.float64)

    def apply(self, state: dict[str, Any]) -> None:
        """Compute this tick's motor rows (axis, target, lmax) in the state."""
        motor_axis = state["motor_axis"]
        motor_target = state["motor_target"]
        motor_lmax = state["motor_lmax"]

        if not self.enabled:
            # Muscle relax: no impulse authority at all (the CONTROL cut).
            motor_target[:] = 0.0
            motor_lmax[:] = 0.0
            return

        quat = state["quat"]
        q_rel0_all = state["joint_q_rel0"]

        for mi, a in enumerate(self.actuators):
            p = a["parent_idx"]
            c = a["child_idx"]
            q_p = quat[p]
            q_c = quat[c]

            # Relative orientation, child in the parent's frame, and its error
            # against the bind pose.  rv(q_err).axis_local is the angle error
            # about this free axis.
            q_rel = transforms.multiply(transforms.conjugate(q_p), q_c)
            q_err = transforms.multiply(
                q_rel, transforms.conjugate(q_rel0_all[a["joint_index"]])
            )
            if q_err[0] < 0.0:
                q_err = -q_err
            sin_half = float(np.linalg.norm(q_err[1:]))
            theta_err = 0.0
            axis_local = a["axis_local_parent"]
            if sin_half > 1e-14:
                angle = 2.0 * math.atan2(sin_half, float(q_err[0]))
                rv = q_err[1:] / sin_half * angle
                theta_err = float(rv @ axis_local)

            motor_axis[mi] = transforms.rotate(q_p, axis_local)
            motor_target[mi] = -a["omega_n"] * (theta_err - a["target_offset"])
            motor_lmax[mi] = a["torque_limit_Nm"] * self.dt
