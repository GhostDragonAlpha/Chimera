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
        # G0: world-floor endpoints (side "W") are never support polygon.
        if rec.get("side") == "W":
            continue
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
        # per actuator, nonzero only for the joint that PIVOTS the body on
        # the ground -- the ankle.  Derived membership test: the child link
        # carries ground contacts AND the parent link does not (the pivot is
        # where the contact-carrying chain meets the free chain).  The plain
        # "child carries contacts" test is WRONG under the anatomic contact
        # spec (CONTACT_LINKS=1): there the tarsal/mtp joints also carry
        # contacts, and handing them the lean distributes the ankle strategy
        # across the foot joints -- not the derived design.  Under the legacy
        # spec the parent test changes nothing (tibia never carries
        # contacts), so legacy stays bit-identical.  G0: world-floor
        # endpoints (side "W") ride EVERY link -- counting them would leave
        # no pivot at all -- so the membership test reads feet only.
        contact_links = {int(r["link_idx"]) for r in state["contact_records"]
                         if r.get("side") != "W"}
        centroid = _support_centroid_xy(state)
        com = _com_xy(state)
        offset_vec = centroid - com
        # BALANCE-BY-COP (2026-08-08, VERDICT 2 membrane, opt-in via
        # state["balance_cop"]): the pivot actuators identified by the
        # SAME membership test, re-listed so apply() can re-derive their
        # lean offset PER TICK from the capture point (Pratt 2006:
        # xi = x + xdot/omega, omega = sqrt(g/h)) instead of the bind-
        # pose COM.  Legacy default off: the static offset below is
        # bit-identical.
        self._bal_idx = [i for i, a in enumerate(self.actuators)
                         if a["child_idx"] in contact_links
                         and a["parent_idx"] not in contact_links]
        for a in self.actuators:
            a["target_offset"] = 0.0
            if a["child_idx"] not in contact_links \
                    or a["parent_idx"] in contact_links:
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

        # SERVO DOMAIN REFUSAL (2026-08-08, opt-in via
        # state["servo_domain_refusal"]): the standing program has a
        # domain -- the COM projects inside the foot support polygon,
        # the same derived frame the push path uses
        # (serve_standing_demo.py: h > 0 and margin > 0, refused instead
        # of lying).  Outside that frame a standing servo has no
        # meaning: measured 2026-08-08 (run-4 STAND arm + the
        # ejected-vs-outpaced diag) the live servo shoved endpoints to
        # -0.359 m under a fallen body -- 62% of the buried floor rows
        # ejected by the muscle crush, the rest outpaced by it.  A body
        # does not stand-serve a fall; the program TERMINATES (latched
        # via self.enabled -- getting up is a different program), and
        # the body enters the proven dead-body floor regime (run-4
        # DROP arm, all legs pass).  Default off: legacy bit-identical.
        if state.get("servo_domain_refusal"):
            xs, ys = [], []
            for rec in state["contact_records"]:
                # G0: world-floor endpoints (side "W") are not the
                # support polygon.
                if rec.get("side") == "W":
                    continue
                li = rec["link_idx"]
                R = transforms.to_matrix(state["quat"][li])
                p = state["pos"][li] + R @ rec["offset_local"]
                xs.append(float(p[0]))
                ys.append(float(p[1]))
            if xs:
                mass = state["mass"]
                com3 = (state["pos"] * mass[:, None]).sum(axis=0) / mass.sum()
                if com3[2] <= 0.0 or com3[0] < min(xs) \
                        or com3[0] > max(xs) or com3[1] < min(ys) \
                        or com3[1] > max(ys):
                    self.enabled = False
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

        # BALANCE-BY-COP (VERDICT 2/13 membrane, opt-in): re-derive the
        # ankle pivots' reference PER TICK.  Pratt 2006 / Koolen 2012: the
        # LIPM capture point xi = x + xdot/omega with omega = sqrt(g/h);
        # balance control = place the COP at p* = x + (1+kd)*xdot/omega
        # (VERDICT 2's own design note; kd = 1 is critical damping of the
        # xi error dynamics).  VERDICT 22 measured the ankle-PD phi drive
        # cannot steer the physical COP (|p_now-p*| 0.0293 m driven vs
        # 0.0269 m pinned -- worse than dead): the pose-PD suppresses the
        # sway the balance law needs.  VERDICT 23 frees the ankles.
        if state.get("balance_cop") and self._bal_idx:
            mass = state["mass"]
            M = float(mass.sum())
            com3 = (state["pos"] * mass[:, None]).sum(axis=0) / M
            comv = (state["lin_vel"] * mass[:, None]).sum(axis=0) / M
            h = float(com3[2])
            if h > 1e-6:
                # ANATOMY-DATUM: standard gravity, same constant as dynamics.
                omega = float(np.sqrt(9.80665 / h))
                kd = 1.0  # derived: critical damping (VERDICT 2 notes)
                p_star = com3[:2] + (1.0 + kd) * comv[:2] / omega

                # VERDICT 23 FREE SWAY (2026-08-09): quiet standing is a FREE
                # inverted pendulum caught by the balance law, not a pose held
                # by a PD.  The ankle pivot rows hold ZERO stiffness: motor
                # target = 0 (the solve drives the ankle's relative angular
                # velocity to zero -- a velocity damper, not a pose clamp) with
                # motor_lmax KEPT at the derived torque cap (a live muscle, not
                # a dead motor).  The other 119 actuators keep the pose-PD from
                # the vectorized apply above untouched.
                # The ONLY ankle drive is the VERDICT 20 true-normal external
                # torque channel, restored: N_a = M*g/2 per foot (the statics
                # share, VERDICT 20 symmetric limit), p* = com + (1+kd)*comv/omega
                # (capture point, kd = 1.0), delta_p3 = p_star - ankle_xy,
                # tau_scalar = N_a * dot(cross(delta_p3, z_hat), axis_w), SET
                # on the tibia parent and -tau on the tarsals child.  The
                # VERDICT 22 phi modulation is REMOVED -- COP steering through
                # the ext_torque couple, not through the ankle PD rows.
                z_hat = np.array([0.0, 0.0, 1.0])
                n_a = 0.5 * M * 9.80665  # statics share per foot (VERDICT 20)
                ext_torque = state.get("ext_torque")
                if ext_torque is None:
                    ext_torque = np.zeros((len(state["link_names"]), 3),
                                          dtype=np.float64)
                    state["ext_torque"] = ext_torque
                else:
                    ext_torque[:] = 0.0
                for a in self._bal_idx:
                    act = self.actuators[a]
                    motor_target[a] = 0.0
                    motor_lmax[a] = float(self._lmax[a])
                    cb = act["child_idx"]
                    R_c = transforms.to_matrix(state["quat"][cb])
                    jc = state["pos"][cb] \
                        + R_c @ state["r_joint_child_local"][act["joint_index"]]
                    ankle_xy = jc[:2]
                    delta_p3 = np.array([p_star[0] - ankle_xy[0],
                                         p_star[1] - ankle_xy[1], 0.0])
                    axis_w = transforms.rotate(
                        state["quat"][act["parent_idx"]],
                        act["axis_local_parent"])
                    tau_scalar = n_a * float(
                        np.dot(np.cross(delta_p3, z_hat), axis_w))
                    ext_torque[act["parent_idx"]] = tau_scalar * axis_w
                    ext_torque[cb] = -tau_scalar * axis_w
