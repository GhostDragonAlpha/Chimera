"""physics_floating.py — THE FLOATING BASE (ROADMAP Track S, step S8).

The last constraint removed. `Tree` pins its root to the world, which is why a leg with a fixed hip
and a planted foot is a stiff triangle that cannot be pushed over. A body that can FALL needs its
root free: six more degrees of freedom -- three of position, three of orientation -- solved
together with the joints rather than bolted on.

    generalized velocity  v = [ v_base(3, world) | omega_base(3, world) | qd(n joints) ]
    dynamics              M(q) a = Q_applied - C(q, v)          M is (6+n) x (6+n)

M and C come from the same recursive Newton-Euler used for the pinned tree, extended to carry base
motion through the forward pass and to collect the base's own reaction in the backward pass. The
mass matrix is built column-by-column from unit accelerations, which is the composite-rigid-body
idea done plainly.

External forces enter through the SAME Jacobian transpose as everywhere else -- now with the base
rows included:

    base linear   F
    base angular  (p - base_origin) x F
    joint j       [z_j x (p - o_j)] . F        (only for links below joint j)

so muscles, thrusters, gravity and contact all still arrive by one rule. Nothing new is invented
here; a constraint is simply released.

WHAT THIS BUYS: a body can now fall over, tumble, land, and -- with a nervous system driving its
muscles -- get itself up. None of those are states or clips. They are the same equations.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from physics_articulated import Tree, Link, Muscle, _rot          # noqa: E402
from physics import quat_to_mat, quat_mul, quat_identity          # noqa: E402


class FloatingTree(Tree):
    """A kinematic tree whose ROOT BODY floats free.

    The base is a real rigid body (mass, inertia, centre of mass) rather than a fixed frame; the
    links in `links` hinge off it exactly as before. So a creature is: one free body + a tree of
    hinged bones, which is what a torso with limbs actually is.
    """

    def __init__(self, base_mass: float, base_inertia, base_com=(0.0, 0.0, 0.0),
                 links: list[Link] = None, gravity=(0.0, 0.0, -9.80665),
                 base_pos=(0.0, 0.0, 0.0), base_quat=None):
        super().__init__(links or [], gravity=gravity, base_pos=base_pos)
        self.base_mass = float(base_mass)
        self.base_inertia = np.asarray(base_inertia, float)
        self.base_com = np.asarray(base_com, float)
        self.base_quat = quat_identity() if base_quat is None else np.asarray(base_quat, float)
        self.base_rot = quat_to_mat(self.base_quat)
        self.v_base = np.zeros(3)          # world linear velocity of the base ORIGIN
        self.w_base = np.zeros(3)          # world angular velocity
        self.nv = 6 + self.n

    # ── kinematics of the base body ──────────────────────────────────────────────────────────
    def base_com_world(self) -> np.ndarray:
        return self.base_pos + self.base_rot @ self.base_com

    def base_inertia_world(self) -> np.ndarray:
        R = self.base_rot
        return R @ self.base_inertia @ R.T

    def total_mass(self) -> float:
        return self.base_mass + sum(L.mass for L in self.links)

    def com_world(self) -> np.ndarray:
        """Centre of mass of the WHOLE creature -- what free fall moves on a clean parabola."""
        _, _, c, _ = self.fk()
        m = self.base_mass
        acc = self.base_mass * self.base_com_world()
        for i, L in enumerate(self.links):
            acc = acc + L.mass * c[i]
            m += L.mass
        return acc / m

    # ── recursive Newton-Euler, with the base free ───────────────────────────────────────────
    def _rnea_float(self, a_base, alpha_base, qdd, use_gravity: bool,
                    v_base=None, w_base=None, qd=None):
        """Inverse dynamics for the whole creature. Returns (F_base, T_base, Q_joints):
        the force and torque that would have to act ON THE BASE, and the joint torques, to produce
        the given accelerations. T_base is taken about the base ORIGIN."""
        qd = self.qd if qd is None else qd
        w_b = self.w_base if w_base is None else w_base
        R, o, c, z = self.fk()
        n = self.n
        g = self.gravity if use_gravity else np.zeros(3)

        # --- the base body itself ---
        r_bc = self.base_rot @ self.base_com
        a_bc = a_base + np.cross(alpha_base, r_bc) + np.cross(w_b, np.cross(w_b, r_bc))
        Iw_b = self.base_inertia_world()
        f_b = self.base_mass * (a_bc - g)
        t_b = Iw_b @ alpha_base + np.cross(w_b, Iw_b @ w_b)
        F_base = f_b.copy()
        T_base = t_b + np.cross(r_bc, f_b)

        # --- forward pass over the links ---
        w = [np.zeros(3)] * n; al = [np.zeros(3)] * n
        ao = [np.zeros(3)] * n; ac = [np.zeros(3)] * n
        for i, L in enumerate(self.links):
            p = L.parent
            wp = w_b if p < 0 else w[p]
            alp = alpha_base if p < 0 else al[p]
            aop = a_base if p < 0 else ao[p]
            op = self.base_pos if p < 0 else o[p]
            rp = o[i] - op
            ao[i] = aop + np.cross(alp, rp) + np.cross(wp, np.cross(wp, rp))
            w[i] = wp + z[i] * qd[i]
            al[i] = alp + z[i] * qdd[i] + np.cross(wp, z[i] * qd[i])
            rc = c[i] - o[i]
            ac[i] = ao[i] + np.cross(al[i], rc) + np.cross(w[i], np.cross(w[i], rc))

        # --- backward pass ---
        F = [np.zeros(3)] * n; T = [np.zeros(3)] * n
        Q = np.zeros(n)
        for i in range(n - 1, -1, -1):
            L = self.links[i]
            Iw = R[i] @ L.inertia @ R[i].T
            f = L.mass * (ac[i] - g)
            t = Iw @ al[i] + np.cross(w[i], Iw @ w[i])
            Fi = f.copy()
            Ti = t + np.cross(c[i] - o[i], f)
            for k in range(n):
                if self.links[k].parent == i:
                    Fi = Fi + F[k]
                    Ti = Ti + T[k] + np.cross(o[k] - o[i], F[k])
            F[i], T[i] = Fi, Ti
            Q[i] = float(np.dot(z[i], Ti))
        for i, L in enumerate(self.links):            # roots hang off the base
            if L.parent < 0:
                F_base = F_base + F[i]
                T_base = T_base + T[i] + np.cross(o[i] - self.base_pos, F[i])
        return F_base, T_base, Q

    def mass_matrix_f(self) -> np.ndarray:
        """(6+n) x (6+n). Column j = the generalized forces produced by a unit acceleration of
        coordinate j alone, at zero velocity and zero gravity."""
        nv = self.nv
        M = np.zeros((nv, nv))
        z3 = np.zeros(3)
        zq = np.zeros(self.n)
        for j in range(nv):
            a = np.zeros(3); al = np.zeros(3); qdd = np.zeros(self.n)
            if j < 3:
                a[j] = 1.0
            elif j < 6:
                al[j - 3] = 1.0
            else:
                qdd[j - 6] = 1.0
            Fb, Tb, Q = self._rnea_float(a, al, qdd, use_gravity=False,
                                         w_base=z3, qd=zq)
            M[:, j] = np.concatenate([Fb, Tb, Q])
        return M

    def bias_f(self) -> np.ndarray:
        """Coriolis + centrifugal + gravity, at the current velocities and zero acceleration."""
        Fb, Tb, Q = self._rnea_float(np.zeros(3), np.zeros(3), np.zeros(self.n),
                                     use_gravity=True)
        return np.concatenate([Fb, Tb, Q])

    def generalized_force_f(self, forces) -> np.ndarray:
        """[(link, world point, world force)] -> the (6+n) generalized force. link < 0 = the base.

        The base rows are just the total force and its moment about the base origin; the joint rows
        are the same Jacobian transpose as the pinned tree. One rule, six more slots."""
        _, o, _, z = self.fk()
        below = self._subtree()
        Q = np.zeros(self.nv)
        for (link, p, Fv) in forces:
            Q[0:3] += Fv
            Q[3:6] += np.cross(np.asarray(p, float) - self.base_pos, Fv)
            if link >= 0:
                for j in range(self.n):
                    if link in below[j]:
                        Q[6 + j] += np.dot(np.cross(z[j], p - o[j]), Fv)
        return Q

    def accel_f(self, extra_forces=None) -> np.ndarray:
        forces = list(self.muscle_forces())
        if extra_forces:
            forces += list(extra_forces)
        Q = self.generalized_force_f(forces) if forces else np.zeros(self.nv)
        return np.linalg.solve(self.mass_matrix_f(), Q - self.bias_f())

    def step(self, dt: float, extra_forces=None) -> None:
        a = self.accel_f(extra_forces)
        self.v_base = self.v_base + a[0:3] * dt
        self.w_base = self.w_base + a[3:6] * dt
        self.qd = self.qd + a[6:] * dt
        self.base_pos = self.base_pos + self.v_base * dt
        # w_base is in the WORLD frame (as RNEA and momentum() both use it), so the quaternion
        # derivative is qdot = 0.5 * (0, w_world) (x) q -- the omega goes on the LEFT. Using the
        # body-frame form quat_mul(q, w) instead rotates about the wrong axes: the orientation
        # error is systematic rather than a truncation, so it does NOT shrink with dt (measured:
        # identical 3.2e-3 m COM error at dt = 4e-4, 1e-4 and 2.5e-5, which is what exposed it).
        wq = np.array([self.w_base[0], self.w_base[1], self.w_base[2], 0.0])
        self.base_quat = self.base_quat + 0.5 * quat_mul(wq, self.base_quat) * dt
        self.base_quat = self.base_quat / (np.linalg.norm(self.base_quat) + 1e-15)
        self.base_rot = quat_to_mat(self.base_quat)
        self.q = self.q + self.qd * dt

    # ── conserved quantities: how a free body is actually checked ────────────────────────────
    def momentum(self):
        """(linear, angular-about-the-origin) for the WHOLE creature. With no external force these
        are conserved -- and the angular one is what makes a falling cat possible: internal joint
        motion can reorient the body while L stays exactly zero."""
        R, o, c, z = self.fk()
        n = self.n
        w = [np.zeros(3)] * n
        vo = [np.zeros(3)] * n
        P = self.base_mass * (self.v_base + np.cross(self.w_base, self.base_rot @ self.base_com))
        L = (self.base_inertia_world() @ self.w_base
             + self.base_mass * np.cross(self.base_com_world(),
                                         self.v_base + np.cross(self.w_base, self.base_rot @ self.base_com)))
        for i, Lk in enumerate(self.links):
            p = Lk.parent
            wp = self.w_base if p < 0 else w[p]
            vop = (self.v_base + np.cross(self.w_base, o[i] - self.base_pos)) if p < 0 else \
                  (vo[p] + np.cross(w[p], o[i] - o[p]))
            vo[i] = vop
            w[i] = wp + z[i] * self.qd[i]
            vc = vo[i] + np.cross(w[i], c[i] - o[i])
            Iw = R[i] @ Lk.inertia @ R[i].T
            P = P + Lk.mass * vc
            L = L + Iw @ w[i] + Lk.mass * np.cross(c[i], vc)
        return P, L

    def energy(self):
        """(kinetic, potential) for the whole creature."""
        R, o, c, z = self.fk()
        n = self.n
        w = [np.zeros(3)] * n
        vo = [np.zeros(3)] * n
        vbc = self.v_base + np.cross(self.w_base, self.base_rot @ self.base_com)
        K = 0.5 * self.base_mass * float(vbc @ vbc) \
            + 0.5 * float(self.w_base @ self.base_inertia_world() @ self.w_base)
        U = -self.base_mass * float(self.gravity @ self.base_com_world())
        for i, Lk in enumerate(self.links):
            p = Lk.parent
            wp = self.w_base if p < 0 else w[p]
            vop = (self.v_base + np.cross(self.w_base, o[i] - self.base_pos)) if p < 0 else \
                  (vo[p] + np.cross(w[p], o[i] - o[p]))
            vo[i] = vop
            w[i] = wp + z[i] * self.qd[i]
            vc = vo[i] + np.cross(w[i], c[i] - o[i])
            Iw = R[i] @ Lk.inertia @ R[i].T
            K += 0.5 * Lk.mass * float(vc @ vc) + 0.5 * float(w[i] @ Iw @ w[i])
            U += -Lk.mass * float(self.gravity @ c[i])
        return K, U

    def point_velocity(self, link: int, p_local) -> np.ndarray:
        """World velocity of a point on a link -- or on the BASE when link < 0."""
        if link < 0:
            r = self.base_rot @ np.asarray(p_local, float)
            return self.v_base + np.cross(self.w_base, r)
        R, o, _, z = self.fk()
        n = self.n
        w = [np.zeros(3)] * n
        vo = [np.zeros(3)] * n
        for i, Lk in enumerate(self.links):
            p = Lk.parent
            wp = self.w_base if p < 0 else w[p]
            vop = (self.v_base + np.cross(self.w_base, o[i] - self.base_pos)) if p < 0 else \
                  (vo[p] + np.cross(w[p], o[i] - o[p]))
            vo[i] = vop
            w[i] = wp + z[i] * self.qd[i]
        pw = o[link] + R[link] @ np.asarray(p_local, float)
        return vo[link] + np.cross(w[link], pw - o[link])

    def frame_of(self, link: int):
        if link < 0:
            return self.base_rot, self.base_pos
        R, o, _, _ = self.fk()
        return R[link], o[link]
