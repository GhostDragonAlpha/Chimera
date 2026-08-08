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

        # Stacked per-actuator constants for the vectorized apply (the scalar
        # loop cost 6.2 ms/tick in Python-call overhead, measured 2026-08-08;
        # the math below is the SAME per-element arithmetic, batched).
        self._P = state["motor_parent"]
        self._C = state["motor_child"]
        self._J = state["motor_joint"]
        self._axis_local = np.array(
            [a["axis_local_parent"] for a in self.actuators], dtype=np.float64)
        self._omega_n = np.array(
            [a["omega_n"] for a in self.actuators], dtype=np.float64)
        self._t_off = np.array(
            [a["target_offset"] for a in self.actuators], dtype=np.float64)
        self._lmax = state["motor_lmax"].copy()

    @staticmethod
    def _normalize_rows(q: np.ndarray) -> np.ndarray:
        """transforms.normalize, batched over rows of (n, 4)."""
        n = np.linalg.norm(q, axis=1)
        n = np.where(n < 1e-12, 1.0, n)
        return q / n[:, None]

    @classmethod
    def _multiply_rows(cls, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """transforms.multiply, batched (Hamilton product, normalized)."""
        a = cls._normalize_rows(a)
        b = cls._normalize_rows(b)
        aw, ax, ay, az = a[:, 0], a[:, 1], a[:, 2], a[:, 3]
        bw, bx, by, bz = b[:, 0], b[:, 1], b[:, 2], b[:, 3]
        out = np.stack([
            aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
        ], axis=1)
        return cls._normalize_rows(out)

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

        # Relative orientation, child in the parent's frame, and its error
        # against the bind pose -- the scalar reference is in the module
        # history (git); identical per-element arithmetic, batched over the
        # 121 actuators.
        q_p = self._normalize_rows(quat[self._P])
        q_c = quat[self._C]
        q_rel = self._multiply_rows(
            np.column_stack([q_p[:, 0], -q_p[:, 1], -q_p[:, 2], -q_p[:, 3]]),
            q_c)
        q_rel0_conj = np.column_stack([
            state["joint_q_rel0"][self._J, 0],
            -state["joint_q_rel0"][self._J, 1],
            -state["joint_q_rel0"][self._J, 2],
            -state["joint_q_rel0"][self._J, 3]])
        q_err = self._multiply_rows(q_rel, q_rel0_conj)
        q_err = np.where(q_err[:, :1] < 0.0, -q_err, q_err)

        sin_half = np.linalg.norm(q_err[:, 1:], axis=1)
        live = sin_half > 1e-14
        angle = np.zeros(len(q_err), dtype=np.float64)
        angle[live] = 2.0 * np.arctan2(sin_half[live], q_err[live, 0])
        rv = np.zeros((len(q_err), 3), dtype=np.float64)
        rv[live] = q_err[live, 1:] / sin_half[live, None] * angle[live, None]
        theta_err = (rv * self._axis_local).sum(axis=1)

        # transforms.rotate(q_p, axis_local), batched: t = 2*cross(xyz, v).
        t = 2.0 * np.cross(q_p[:, 1:], self._axis_local)
        motor_axis[:] = self._axis_local + q_p[:, :1] * t \
            + np.cross(q_p[:, 1:], t)
        motor_target[:] = -self._omega_n * (theta_err - self._t_off)
        motor_lmax[:] = self._lmax
