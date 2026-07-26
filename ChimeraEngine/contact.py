"""contact.py — GROUND CONTACT (ROADMAP Track S, step S7).

The ground pushes back. That is the last piece: with it, a body can stand, stumble, fall and get
up, and none of those are authored -- they are the same equations producing different outcomes.

Contact enters through the SAME rule as everything else: a force at a point.

    thruster  force at a port, along its facing
    muscle    force at a port, toward another port
    CONTACT   force at a port, along the ground's normal (+ friction across it)

`PORT_KINDS` already reserved this: 'substrate' -- "ground contact - friction, footing, root
anchorage". A foot is a substrate port.

The model is a penalty (soft) contact: a spring-damper along the normal plus regularised Coulomb
friction across it. Soft contact is an honest choice here -- it is continuous, it needs no separate
solver, and it is close to what MuJoCo does. It also means penetration is never exactly zero, so
the witness measures HOW MUCH rather than asserting there is none.

A foot is DISCOVERED, not declared -- the same rule core/gait.py already uses: a foot is a point
that touches the ground some of the time. Nothing here is told which link is a leg.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


# ── the ground ────────────────────────────────────────────────────────────────────────────────
@dataclass
class Ground:
    """A height field. Flat by default; a slope, a step, or (later) a planet drops in here.

    `height(x, y)` and `normal(x, y)` are the whole interface -- which is exactly what
    PlanetOnion.elevation_grid() can provide, so a planet becomes ground with no new concepts.
    """
    slope: float = 0.0                     # rise per unit x (tan of the incline angle)
    step_at: float = None                  # x of a vertical step, or None
    step_height: float = 0.0

    def height(self, x: float, y: float = 0.0) -> float:
        h = self.slope * x
        if self.step_at is not None and x > self.step_at:
            h += self.step_height
        return float(h)

    def normal(self, x: float, y: float = 0.0) -> np.ndarray:
        n = np.array([-self.slope, 0.0, 1.0])
        return n / np.linalg.norm(n)

    def angle(self) -> float:
        return float(np.arctan(self.slope))


@dataclass
class ContactModel:
    """Penalty contact. `k` is stiffness, `zeta` damping, `mu` the Coulomb friction coefficient."""
    k: float = 4.0e5
    zeta: float = 6.0e3
    mu: float = 0.8
    # MEASURED BIAS (contact_witness C3): penalty contact under-delivers friction, because the
    # normal force OSCILLATES against the spring and friction is lost during the dips. A block on
    # four corners slid at 28 deg where atan(0.8) = 38.7; a single non-rocking contact at this
    # damping slides at ~36. The bias is always toward sliding EARLY, so effective mu is a little
    # below the nominal one -- worth knowing before tuning a character's footing.
    v_eps: float = 2e-5                    # the speed at which friction reaches HALF of mu*N.
                                           # Too large and static friction is silently capped:
                                           # at 1e-3 a block slid at 28 deg instead of atan(0.8)
                                           # = 38.7. Smaller = closer to true stiction.

    def force(self, p: np.ndarray, v: np.ndarray, radius: float, ground: Ground):
        """Force on a contact sphere of `radius` centred at world point `p` moving at `v`.
        Returns (force, penetration, is_touching)."""
        n = ground.normal(p[0], p[1])
        gap = float(np.dot(p - np.array([p[0], p[1], ground.height(p[0], p[1])]), n))
        pen = radius - gap
        if pen <= 0.0:
            return np.zeros(3), 0.0, False
        vn = float(np.dot(v, n))
        fn = self.k * pen - self.zeta * vn
        if fn <= 0.0:                       # the ground pulls on nothing -- it can only push
            return np.zeros(3), pen, False
        vt = v - vn * n
        sp = float(np.linalg.norm(vt))
        ft = -self.mu * fn * vt / (sp + self.v_eps)      # regularised Coulomb, opposes sliding
        return fn * n + ft, pen, True


# ── feet: contact spheres bolted to links ─────────────────────────────────────────────────────
@dataclass
class Foot:
    """A contact sphere on a link. `link < 0` means it rides on the BASE."""
    link: int
    at: np.ndarray                          # in link coordinates
    radius: float = 0.03
    name: str = 'foot'

    def __post_init__(self):
        self.at = np.asarray(self.at, float)


def tree_contacts(tree, feet: list[Foot], ground: Ground, model: ContactModel):
    """Contact forces for an articulated tree, in the SAME (link, world point, world force) form
    that muscle_forces() returns -- so they go through generalized_force() unchanged."""
    out, info = [], []
    for f in feet:
        R, o = tree.frame_of(f.link)
        p = o + R @ f.at
        v = tree.point_velocity(f.link, f.at)
        F, pen, touching = model.force(p, v, f.radius, ground)
        info.append({'name': f.name, 'p': p, 'pen': pen, 'touching': touching,
                     'Fn': float(np.dot(F, ground.normal(p[0], p[1])))})
        if touching:
            out.append((f.link, p, F))
    return out, info


def body_contacts(body, feet: list[Foot], ground: Ground, model: ContactModel):
    """The same, for a free-floating rigid Body (physics.py). Ships land with this."""
    from physics import quat_to_mat
    R = quat_to_mat(body.q)
    out, info = [], []
    for f in feet:
        r = R @ (f.at - body.com_local)
        p = body.x + r
        v = body.v + np.cross(R @ body.w, r)             # body-frame omega -> world
        F, pen, touching = model.force(p, v, f.radius, ground)
        info.append({'name': f.name, 'p': p, 'pen': pen, 'touching': touching,
                     'Fn': float(np.dot(F, ground.normal(p[0], p[1])))})
        if touching:
            out.append((p, F))
    return out, info


def step_body(body, dt: float, feet, ground, model, gravity=(0.0, 0.0, -9.80665)):
    """One step of a free body under gravity plus contact -- forces applied AT THEIR POINTS, so an
    off-centre contact torques the body exactly as an off-axis thruster does."""
    forces, info = body_contacts(body, feet, ground, model)
    from physics import quat_to_mat
    R = quat_to_mat(body.q)
    F_world = np.asarray(gravity, float) * body.mass
    T_body = np.zeros(3)
    for (p, F) in forces:
        F_world = F_world + F
        r_world = p - body.x
        T_body = T_body + R.T @ np.cross(r_world, F)     # torque about the COM, into the body frame
    body.v = body.v + (F_world / body.mass) * dt
    body.x = body.x + body.v * dt
    wdot = body._inv_I @ (T_body - np.cross(body.w, body.inertia @ body.w))
    body.w = body.w + wdot * dt
    from physics import quat_mul
    wq = np.array([body.w[0], body.w[1], body.w[2], 0.0])
    body.q = body.q + 0.5 * quat_mul(body.q, wq) * dt
    body.q = body.q / (np.linalg.norm(body.q) + 1e-15)
    return info
