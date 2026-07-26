"""physics.py — THE ACTUATED MEMBRANE at runtime (ROADMAP Track S, steps S1–S3).

A membrane floats free. Matter inside it can ATTAIN A STATE, and that state pushes at a PORT —
at the port's position, along the port's facing, in the frame of the body it is bolted to.
Nothing here is animated: motion is what the forces produce.

    thruster  = Verb(off -> full)  at a port on a hull
    muscle    = Verb(relaxed -> contracted)  at a port across a joint

THEY ARE THE SAME OBJECT. Only what decides the dial differs — pilot input, or a nervous system.
If these ever become two systems, the architecture was got wrong.

Built on the EXISTING primitives (core/membranes.py), not beside them: `Port` already knows where
it is, which way it faces and what flows through it; `Verb` is already two states and a dial.

The dynamics are ordinary rigid-body mechanics, done honestly:
    linear    a = F/m                      -- and F/m REGARDLESS of where the force is applied
    angular   I w' + w x (I w) = tau       -- Euler's equations, integrated in the BODY frame
    torque    tau = r x F                  -- r from the centre of mass to the port
Quaternions are (x, y, z, w), matching bake_splats and the WGSL renderer.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

_REPO = Path(__file__).resolve().parents[1]
for _p in (str(_REPO), str(_REPO / "Chimera")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from core.membranes import Membrane, Port, State, Verb   # noqa: E402  (the real primitives)


# ── quaternion helpers, (x, y, z, w) ──────────────────────────────────────────────────────────
def quat_identity() -> np.ndarray:
    return np.array([0.0, 0.0, 0.0, 1.0])


def quat_mul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return np.array([
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
        aw * bw - ax * bx - ay * by - az * bz,
    ])


def quat_to_mat(q: np.ndarray) -> np.ndarray:
    """Rotation matrix taking BODY coordinates to WORLD (columns are the body axes in world)."""
    x, y, z, w = q / (np.linalg.norm(q) + 1e-15)
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - w * z),     2 * (x * z + w * y)],
        [2 * (x * y + w * z),     1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
        [2 * (x * z - w * y),     2 * (y * z + w * x),     1 - 2 * (x * x + y * y)],
    ])


# ── inertia for the simple shapes a membrane can be ───────────────────────────────────────────
def inertia_sphere(mass: float, radius: float) -> np.ndarray:
    return np.eye(3) * (0.4 * mass * radius * radius)


def inertia_box(mass: float, extents: np.ndarray) -> np.ndarray:
    x, y, z = np.asarray(extents, float)
    return np.diag([mass * (y * y + z * z) / 12.0,
                    mass * (x * x + z * z) / 12.0,
                    mass * (x * x + y * y) / 12.0])


# ── the actuator: a VERB bound to a PORT ──────────────────────────────────────────────────────
@dataclass
class Actuator:
    """Matter that DOES something. A `Verb` whose dial produces force at a `Port`.

    `gain` converts the verb's readout (whatever the state parameter means — throttle, activation)
    into newtons. `param` names which number in the state to read. The force acts along the port's
    facing, applied at the port's position, both in the body's own coordinates — which is exactly
    what "relative to what it is attached to" means.
    """
    name: str
    port: Port
    verb: Verb
    gain: float = 1.0
    param: str = 'throttle'
    dial: float = 0.0                     # 0..1 (extrapolation past the ends is allowed)

    def magnitude(self) -> float:
        return float(self.verb.at(self.dial).get(self.param, 0.0)) * self.gain

    def local_force(self) -> np.ndarray:
        """Force vector in BODY coordinates: along the port's facing."""
        return self.port.facing * self.magnitude()


def thruster(name: str, at, facing, max_force: float, kind: str = 'structural') -> Actuator:
    """A thruster: off -> full. The canonical actuator, and the simplest to witness."""
    return Actuator(
        name=name,
        port=Port(name=name, kind=kind, at=np.asarray(at, float), facing=np.asarray(facing, float)),
        verb=Verb(name=name, lo=State('off', {'throttle': 0.0}), hi=State('full', {'throttle': 1.0})),
        gain=float(max_force),
    )


# ── a free-floating body ──────────────────────────────────────────────────────────────────────
@dataclass
class Body:
    """A membrane with mass and inertia, floating free. Pose in world, spin in the body frame."""
    membrane: Membrane
    mass: float
    inertia: np.ndarray                                   # 3x3, body frame, about the COM
    com_local: np.ndarray = field(default_factory=lambda: np.zeros(3))
    x: np.ndarray = field(default_factory=lambda: np.zeros(3))         # world position of the COM
    q: np.ndarray = field(default_factory=quat_identity)               # body -> world
    v: np.ndarray = field(default_factory=lambda: np.zeros(3))         # world linear velocity
    w: np.ndarray = field(default_factory=lambda: np.zeros(3))         # BODY-frame angular velocity
    actuators: list = field(default_factory=list)

    def __post_init__(self):
        self.inertia = np.asarray(self.inertia, float)
        self._inv_I = np.linalg.inv(self.inertia)

    def add(self, act: Actuator) -> Actuator:
        self.actuators.append(act)
        self.membrane.ports[act.port.name] = act.port     # the port lives on the MEMBRANE
        self.membrane.verbs[act.name] = act.verb          # so does the verb
        return act

    # --- what the actuators are doing right now, in the body frame ---
    def net_local(self) -> tuple[np.ndarray, np.ndarray]:
        """(force, torque) in BODY coordinates. Torque is taken about the CENTRE OF MASS."""
        F = np.zeros(3)
        T = np.zeros(3)
        for a in self.actuators:
            f = a.local_force()
            r = a.port.at - self.com_local                # lever arm, COM -> port
            F += f
            T += np.cross(r, f)                           # tau = r x F
        return F, T

    def step(self, dt: float, gravity: np.ndarray | None = None) -> None:
        R = quat_to_mat(self.q)
        F_body, T_body = self.net_local()

        # LINEAR: a = F/m. Note the application point does NOT reduce this -- an off-axis push
        # accelerates the centre of mass exactly as hard as an on-axis one, and additionally spins
        # the body. Getting this wrong is the classic thruster bug.
        F_world = R @ F_body
        if gravity is not None:
            F_world = F_world + np.asarray(gravity, float) * self.mass
        self.v = self.v + (F_world / self.mass) * dt
        self.x = self.x + self.v * dt

        # ANGULAR: Euler's equations in the body frame. The gyroscopic term vanishes at w = 0,
        # which is what makes the balance witness exact on the first step.
        wdot = self._inv_I @ (T_body - np.cross(self.w, self.inertia @ self.w))
        self.w = self.w + wdot * dt
        wq = np.array([self.w[0], self.w[1], self.w[2], 0.0])
        self.q = self.q + 0.5 * quat_mul(self.q, wq) * dt
        self.q = self.q / (np.linalg.norm(self.q) + 1e-15)

    # --- readouts ---
    def angular_accel(self) -> np.ndarray:
        """Current body-frame angular acceleration, from the current actuator states."""
        _, T = self.net_local()
        return self._inv_I @ (T - np.cross(self.w, self.inertia @ self.w))

    def linear_accel_world(self) -> np.ndarray:
        F, _ = self.net_local()
        return (quat_to_mat(self.q) @ F) / self.mass

    def port_world(self, name: str) -> tuple[np.ndarray, np.ndarray]:
        """A port's (position, facing) in WORLD coordinates -- for rendering and for contact."""
        p = self.membrane.ports[name]
        R = quat_to_mat(self.q)
        return self.x + R @ (p.at - self.com_local), R @ p.facing


class World:
    """Bodies float free; step them together. (Joints and contact arrive in S4/S7.)"""

    def __init__(self, gravity=None):
        self.bodies: list[Body] = []
        self.gravity = None if gravity is None else np.asarray(gravity, float)
        self.t = 0.0

    def add(self, b: Body) -> Body:
        self.bodies.append(b)
        return b

    def step(self, dt: float) -> None:
        for b in self.bodies:
            b.step(dt, self.gravity)
        self.t += dt

    def momentum(self) -> tuple[np.ndarray, np.ndarray]:
        """Total linear and (world-frame) angular momentum -- conserved when nothing is firing."""
        P = np.zeros(3)
        L = np.zeros(3)
        for b in self.bodies:
            R = quat_to_mat(b.q)
            P += b.mass * b.v
            L += R @ (b.inertia @ b.w) + b.mass * np.cross(b.x, b.v)
        return P, L
