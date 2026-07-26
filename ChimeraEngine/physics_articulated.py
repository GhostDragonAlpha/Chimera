"""physics_articulated.py — JOINTS AND MUSCLES (ROADMAP Track S, steps S4–S5).

S4: a port that CONSTRAINS instead of only transmitting. Bodies stop floating free and form a
    TREE — the kinematic tree, exactly what mjcf.py already expresses as XML nesting.
S5: a MUSCLE is the same object as a thruster. Not a motor torque bolted to a joint: a muscle
    spans from an ORIGIN port on one bone to an INSERTION port on the next, pulls along that line,
    and the torque about the joint is whatever `r x F` gives. Nature does it that way, and it is
    what makes the moment arm real rather than a number someone typed.

    thruster:  force at a port, along the port's facing
    muscle:    force at a port, toward another port
    -> SAME MECHANISM. If these needed different code, the architecture was got wrong.

Dynamics are exact, not iterative: reduced coordinates over a hinge tree, solved as
    M(q) qdd = Q_applied - C(q, qd)
with the mass matrix M and the bias term C both from RECURSIVE NEWTON-EULER (the standard method,
and what MuJoCo uses). Joints therefore cannot drift apart — the constraint is built into the
coordinates rather than restored by a solver, which is what a character needs.

Generalized forces from point forces use the Jacobian transpose, which is the one rule that makes
muscles, thrusters, gravity and contact all enter the same way:
    Q_j = sum over forces  [ axis_j x (p_force - anchor_j) ] . F      (for bodies below joint j)
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from physics import quat_to_mat, Actuator                      # noqa: E402
_REPO = Path(__file__).resolve().parents[1]
for _p in (str(_REPO), str(_REPO / "Chimera")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from core.membranes import Membrane, Port, State, Verb          # noqa: E402


def _rot(axis: np.ndarray, ang: float) -> np.ndarray:
    """Rodrigues rotation about a unit axis."""
    a = np.asarray(axis, float)
    a = a / (np.linalg.norm(a) + 1e-15)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + np.sin(ang) * K + (1 - np.cos(ang)) * (K @ K)


@dataclass
class Link:
    """One rigid segment, hinged to its parent. A bone.

    `anchor` and `axis` are in the PARENT's coordinates: where this link pivots, and about what.
    `com` and `inertia` are in this link's OWN coordinates -- relative to its own joint, which is
    exactly the 'relative to what it is attached to' the operator asked for.
    """
    name: str
    mass: float
    inertia: np.ndarray                                   # 3x3 about the COM, LINK frame
    com: np.ndarray                                       # COM in link coords (origin = its joint)
    anchor: np.ndarray                                    # pivot, in PARENT coords
    axis: np.ndarray                                      # hinge axis, in PARENT coords
    parent: int = -1                                      # index of the parent link, -1 = ground
    ports: dict = field(default_factory=dict)             # name -> Port, in LINK coords

    def __post_init__(self):
        self.inertia = np.asarray(self.inertia, float)
        self.com = np.asarray(self.com, float)
        self.anchor = np.asarray(self.anchor, float)
        a = np.asarray(self.axis, float)
        self.axis = a / (np.linalg.norm(a) + 1e-15)


@dataclass
class Muscle:
    """A Verb that PULLS between two ports. `dial` 0 = relaxed, 1 = fully contracted.

    Tension acts along the line from origin to insertion, applied at BOTH ports, equal and
    opposite -- Newton's third law, so the pair exerts no net force on the body as a whole and
    only ever produces the torque its moment arm earns.
    """
    name: str
    origin_link: int
    origin: np.ndarray                                    # in origin_link coords
    insert_link: int
    insert: np.ndarray                                    # in insert_link coords
    verb: Verb
    max_tension: float = 1.0
    dial: float = 0.0
    param: str = 'activation'
    rest_length: float = 0.0        # optimal length; 0 disables the force-length curve
    width: float = 0.55             # how broad the curve is (fraction of rest length)

    def force_length(self, length: float) -> float:
        """The Hill force-length curve: a muscle pulls hardest near its optimal length, and the
        further it is stretched or shortened the less it can give.

        THIS IS WHAT MAKES A MUSCLE A SPRING. With constant tension, co-contracting a pair does not
        stiffen a joint at all -- it only supplies the destabilising half (as the joint deviates the
        two moment arms stop being equal, and near-max tensions then drive it further). With the
        curve, a stretched muscle pulls HARDER and its shortened antagonist pulls LESS, which is a
        restoring torque. Bracing works in a real body for this reason and no other.
        """
        if self.rest_length <= 0.0:
            return 1.0
        e = (length / self.rest_length - 1.0) / max(self.width, 1e-6)
        return float(np.exp(-e * e))

    def tension(self, length: float = 0.0) -> float:
        """A MUSCLE CAN ONLY PULL. Tension is clamped at zero: a negative activation must not turn
        the muscle into a strut that pushes. This is not a detail -- it is WHY nature builds
        ANTAGONISTIC PAIRS. One muscle can drive a joint one way and then only go slack; to drive
        it back you need a second muscle on the other side. Every limb therefore needs at least two
        actuators per degree of freedom, and the nervous system's job is choosing between them."""
        a = max(0.0, float(self.verb.at(self.dial).get(self.param, 0.0)))
        return a * self.max_tension * (self.force_length(length) if length > 0.0 else 1.0)


def make_muscle(name: str, origin_link: int, origin, insert_link: int, insert,
                max_tension: float) -> Muscle:
    return Muscle(name=name, origin_link=origin_link, origin=np.asarray(origin, float),
                  insert_link=insert_link, insert=np.asarray(insert, float),
                  verb=Verb(name=name, lo=State('relaxed', {'activation': 0.0}),
                            hi=State('contracted', {'activation': 1.0})),
                  max_tension=float(max_tension))


class Tree:
    """A kinematic tree of hinges: a body, a limb, a robot arm, a landing leg."""

    def __init__(self, links: list[Link], gravity=(0.0, 0.0, -9.80665),
                 base_pos=(0.0, 0.0, 0.0), base_rot=None):
        self.links = links
        self.n = len(links)
        self.q = np.zeros(self.n)
        self.qd = np.zeros(self.n)
        self.gravity = np.asarray(gravity, float)
        self.base_pos = np.asarray(base_pos, float)
        self.base_rot = np.eye(3) if base_rot is None else np.asarray(base_rot, float)
        self.muscles: list[Muscle] = []
        self.membrane = Membrane(name='tree', scale=1.0, serial='tree-0')
        for L in links:                                    # ports live on the membrane
            for pn, p in L.ports.items():
                self.membrane.ports[f'{L.name}.{pn}'] = p

    def muscle_length(self, m: Muscle) -> float:
        Ra, oa = self.frame_of(m.origin_link)
        Rb, ob = self.frame_of(m.insert_link)
        return float(np.linalg.norm((ob + Rb @ m.insert) - (oa + Ra @ m.origin)))

    def set_rest_lengths(self, width: float = 0.55) -> None:
        """Take each muscle's optimal length to be its length in the CURRENT pose -- i.e. the body
        is strongest around the posture it is built for, which is what an organism's geometry does."""
        for m in self.muscles:
            m.rest_length = self.muscle_length(m)
            m.width = width

    def add_muscle(self, m: Muscle) -> Muscle:
        self.muscles.append(m)
        self.membrane.verbs[m.name] = m.verb
        return m

    # ── kinematics ───────────────────────────────────────────────────────────────────────────
    def fk(self, q=None):
        """World rotation R_i, joint anchor o_i, COM c_i, and world hinge axis z_i per link."""
        q = self.q if q is None else q
        R = [None] * self.n
        o = [None] * self.n
        c = [None] * self.n
        z = [None] * self.n
        for i, L in enumerate(self.links):
            Rp = self.base_rot if L.parent < 0 else R[L.parent]
            op = self.base_pos if L.parent < 0 else o[L.parent]
            z[i] = Rp @ L.axis                              # the hinge axis, in the world
            o[i] = op + Rp @ L.anchor                       # the pivot, in the world
            R[i] = Rp @ _rot(L.axis, q[i])                  # child frame = parent, then the hinge
            c[i] = o[i] + R[i] @ L.com
        return R, o, c, z

    def frame_of(self, link: int):
        """(R, origin) for a link, or the BASE when link < 0. Without this, an index of -1 would
        silently wrap to the LAST link in the list -- a muscle anchored to the ground would quietly
        attach itself to the far end of the body instead."""
        if link < 0:
            return self.base_rot, self.base_pos
        R, o, _, _ = self.fk()
        return R[link], o[link]

    def point_world(self, link: int, p_local) -> np.ndarray:
        R, o, _, _ = self.fk()
        return o[link] + R[link] @ np.asarray(p_local, float)

    def point_velocity(self, link: int, p_local) -> np.ndarray:
        """World velocity of a point fixed in a link -- what contact damping and friction need.
        Built by walking the chain: each link inherits its parent's motion and adds its own hinge."""
        if link < 0:
            return np.zeros(3)
        R, o, _, z = self.fk()
        w = [np.zeros(3)] * self.n
        vo = [np.zeros(3)] * self.n
        for i, L in enumerate(self.links):
            p = L.parent
            wp = np.zeros(3) if p < 0 else w[p]
            vop = np.zeros(3) if p < 0 else vo[p]
            op = self.base_pos if p < 0 else o[p]
            vo[i] = vop + np.cross(wp, o[i] - op)
            w[i] = wp + z[i] * self.qd[i]
        pw = o[link] + R[link] @ np.asarray(p_local, float)
        return vo[link] + np.cross(w[link], pw - o[link])

    def _subtree(self) -> list[set]:
        """Which links lie below each joint -- a force only torques the joints it hangs from."""
        below = [set([i]) for i in range(self.n)]
        for i in range(self.n - 1, -1, -1):
            p = self.links[i].parent
            if p >= 0:
                below[p] |= below[i]
        return below

    # ── forces -> generalized forces (the ONE rule everything enters through) ────────────────
    def generalized_force(self, forces: list[tuple[int, np.ndarray, np.ndarray]]) -> np.ndarray:
        """forces = [(link, world point, world force)] -> Q, via the Jacobian transpose.

        Q_j = [ z_j x (p - o_j) ] . F   when the force acts on a link BELOW joint j; zero if not
        (pulling on your forearm cannot torque a joint it does not hang from). Muscles, thrusters,
        gravity and contact all arrive here, which is why they need no separate code paths.
        """
        _, o, _, z = self.fk()
        below = self._subtree()
        Q = np.zeros(self.n)
        for (link, p, F) in forces:
            for j in range(self.n):
                if link in below[j]:
                    Q[j] += np.dot(np.cross(z[j], p - o[j]), F)
        return Q

    def muscle_forces(self) -> list[tuple[int, np.ndarray, np.ndarray]]:
        """Each muscle's tension as a pair of equal-and-opposite forces at its two ports."""
        out = []
        for m in self.muscles:
            Ra, oa = self.frame_of(m.origin_link)
            Rb, ob = self.frame_of(m.insert_link)
            pa = oa + Ra @ m.origin
            pb = ob + Rb @ m.insert
            d = pb - pa
            L = float(np.linalg.norm(d))
            if L < 1e-12:
                continue
            u = d / L
            T = m.tension(L)
            out.append((m.insert_link, pb, -u * T))         # insertion pulled toward the origin
            out.append((m.origin_link, pa, u * T))          # equal and opposite
        return out

    def moment_arm(self, m: Muscle, joint: int) -> float:
        """The muscle's LEVER about a joint: dTorque/dTension. Real biomechanics, measurable."""
        forces = []
        Ra, oa = self.frame_of(m.origin_link)
        Rb, ob = self.frame_of(m.insert_link)
        pa = oa + Ra @ m.origin
        pb = ob + Rb @ m.insert
        u = (pb - pa) / (np.linalg.norm(pb - pa) + 1e-15)
        forces.append((m.insert_link, pb, -u))
        forces.append((m.origin_link, pa, u))
        return float(self.generalized_force(forces)[joint])

    # ── dynamics: recursive Newton-Euler ─────────────────────────────────────────────────────
    def _rnea(self, qdd: np.ndarray, use_gravity: bool, qd=None) -> np.ndarray:
        """Inverse dynamics: the joint forces required to produce qdd, in world coordinates."""
        qd = self.qd if qd is None else qd
        R, o, c, z = self.fk()
        n = self.n
        w = [np.zeros(3)] * n; al = [np.zeros(3)] * n
        ao = [np.zeros(3)] * n; ac = [np.zeros(3)] * n

        for i, L in enumerate(self.links):                  # base -> tip
            p = L.parent
            wp = np.zeros(3) if p < 0 else w[p]
            alp = np.zeros(3) if p < 0 else al[p]
            aop = np.zeros(3) if p < 0 else ao[p]
            op = self.base_pos if p < 0 else o[p]
            rp = o[i] - op                                  # the pivot is a point of the PARENT
            ao[i] = aop + np.cross(alp, rp) + np.cross(wp, np.cross(wp, rp))
            w[i] = wp + z[i] * qd[i]
            al[i] = alp + z[i] * qdd[i] + np.cross(wp, z[i] * qd[i])
            rc = c[i] - o[i]
            ac[i] = ao[i] + np.cross(al[i], rc) + np.cross(w[i], np.cross(w[i], rc))

        F = [np.zeros(3)] * n; T = [np.zeros(3)] * n
        Q = np.zeros(n)
        for i in range(n - 1, -1, -1):                      # tip -> base
            L = self.links[i]
            Iw = R[i] @ L.inertia @ R[i].T                  # inertia, rotated into the world
            g = self.gravity if use_gravity else np.zeros(3)
            f = L.mass * (ac[i] - g)
            t = Iw @ al[i] + np.cross(w[i], Iw @ w[i])
            Fi = f.copy()
            Ti = t + np.cross(c[i] - o[i], f)
            for k in range(n):                              # add up the children hanging off i
                if self.links[k].parent == i:
                    Fi = Fi + F[k]
                    Ti = Ti + T[k] + np.cross(o[k] - o[i], F[k])
            F[i], T[i] = Fi, Ti
            Q[i] = float(np.dot(z[i], Ti))
        return Q

    def mass_matrix(self) -> np.ndarray:
        """Column j = the joint forces produced by a unit acceleration of joint j alone."""
        M = np.zeros((self.n, self.n))
        zero = np.zeros(self.n)
        for j in range(self.n):
            e = np.zeros(self.n); e[j] = 1.0
            M[:, j] = self._rnea(e, use_gravity=False, qd=zero)
        return M

    def bias(self) -> np.ndarray:
        """Coriolis + centrifugal + gravity: what the joints feel at zero acceleration."""
        return self._rnea(np.zeros(self.n), use_gravity=True)

    def accel(self, extra_forces=None) -> np.ndarray:
        forces = list(self.muscle_forces())
        if extra_forces:
            forces += list(extra_forces)
        Q = self.generalized_force(forces) if forces else np.zeros(self.n)
        return np.linalg.solve(self.mass_matrix(), Q - self.bias())

    def step(self, dt: float, extra_forces=None) -> None:
        """Semi-implicit Euler -- stable for the stiff, oscillatory systems limbs actually are."""
        qdd = self.accel(extra_forces)
        self.qd = self.qd + qdd * dt
        self.q = self.q + self.qd * dt

    # ── readouts ─────────────────────────────────────────────────────────────────────────────
    def energy(self) -> tuple[float, float]:
        """(kinetic, potential). Conserved when nothing is actuated -- the honest integrator test."""
        R, o, c, z = self.fk()
        n = self.n
        w = [np.zeros(3)] * n; vo = [np.zeros(3)] * n
        K = 0.0; U = 0.0
        for i, L in enumerate(self.links):
            p = L.parent
            wp = np.zeros(3) if p < 0 else w[p]
            vop = np.zeros(3) if p < 0 else vo[p]
            op = self.base_pos if p < 0 else o[p]
            vo[i] = vop + np.cross(wp, o[i] - op)
            w[i] = wp + z[i] * self.qd[i]
            vc = vo[i] + np.cross(w[i], c[i] - o[i])
            Iw = R[i] @ L.inertia @ R[i].T
            K += 0.5 * L.mass * float(vc @ vc) + 0.5 * float(w[i] @ Iw @ w[i])
            U += -L.mass * float(self.gravity @ c[i])
        return K, U


def rod(name: str, mass: float, length: float, anchor=(0, 0, 0), axis=(0, 1, 0),
        parent: int = -1) -> Link:
    """A uniform rod hinged at one END, hanging along -z. I_com = m L^2 / 12."""
    I = np.diag([mass * length ** 2 / 12.0, mass * length ** 2 / 12.0, 1e-9])
    return Link(name=name, mass=mass, inertia=I, com=np.array([0.0, 0.0, -length / 2.0]),
                anchor=np.asarray(anchor, float), axis=np.asarray(axis, float), parent=parent)
