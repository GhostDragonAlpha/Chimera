"""gravity.py — UP IS DECIDED BY THE PULL OF GRAVITY (operator's ruling, 2026-07-25).

Gravity stops being the constant `(0, 0, -9.81)` and becomes a FIELD: `g(position)`. Then "up" is
never stored anywhere -- it is DERIVED, `-normalize(g(p))`, wherever you happen to be standing.

This is not a flourish. On a sphere a global +Z is simply WRONG, and `core/membranes.py` already
said so: a boundary supplies its own local frame, and up is its normal. Making gravity a field is
what makes that true for the physics as well as the geometry:

  * walk over the horizon and your up rotates with you, with nothing special-cased
  * a ship far from a planet has NO meaningful up, which is correct
  * orbit falls out of the same equation as standing on the ground -- one law, not two
  * a long structure near a planet feels a GRADIENT across its length (tidal), for free, because
    each part is asked what gravity is where IT is

PORT_KINDS already reserved 'gravitational' -- "mass coupling to a parent body; what makes a thing
FALL toward it". This is that port, made real.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


class Field:
    """Anything that can say what gravity is at a point."""

    def at(self, p) -> np.ndarray:
        raise NotImplementedError

    def up_at(self, p) -> np.ndarray:
        """Local UP: straight away from the pull. Falls back to +Z where there is no field at all,
        because a body in deep space has no up and the caller still needs an axis to draw."""
        g = self.at(p)
        n = float(np.linalg.norm(g))
        if n < 1e-12:
            return np.array([0.0, 0.0, 1.0])
        return -g / n

    def strength_at(self, p) -> float:
        return float(np.linalg.norm(self.at(p)))


@dataclass
class Uniform(Field):
    """A flat world. Correct only when you are small compared to the body you are standing on --
    which is exactly when a flat-earth approximation is fine."""
    g: np.ndarray = field(default_factory=lambda: np.array([0.0, 0.0, -9.80665]))

    def __post_init__(self):
        self.g = np.asarray(self.g, float)

    def at(self, p) -> np.ndarray:
        return self.g


@dataclass
class PointMass(Field):
    """A planet, moon or star: g = -mu * r_hat / r^2, softened inside `radius` so a body that ends
    up under the surface is pulled sensibly toward the centre instead of to infinity.

    `mu` is the standard gravitational parameter GM. Giving mu directly rather than G and M keeps
    the number that actually matters -- and it is the number orbital mechanics is written in.
    """
    center: np.ndarray = field(default_factory=lambda: np.zeros(3))
    mu: float = 3.986e14                       # Earth, m^3/s^2
    radius: float = 6.371e6                    # surface radius, m

    def __post_init__(self):
        self.center = np.asarray(self.center, float)

    @classmethod
    def from_surface_g(cls, center, radius: float, g_surface: float = 9.80665) -> 'PointMass':
        """Build from what you can actually measure: the radius, and g at the surface."""
        return cls(center=np.asarray(center, float), mu=g_surface * radius * radius, radius=radius)

    def at(self, p) -> np.ndarray:
        d = np.asarray(p, float) - self.center
        r = float(np.linalg.norm(d))
        if r < 1e-9:
            return np.zeros(3)
        if r < self.radius:                     # inside: linear to zero at the centre (uniform sphere)
            return -(self.mu / self.radius ** 3) * d
        return -(self.mu / (r * r * r)) * d

    # --- the numbers a space game actually needs ---
    def surface_g(self) -> float:
        return self.mu / (self.radius ** 2)

    def circular_speed(self, r: float) -> float:
        """v = sqrt(mu / r) -- the speed that turns falling into orbiting."""
        return float(np.sqrt(self.mu / r))

    def escape_speed(self, r: float) -> float:
        return float(np.sqrt(2.0 * self.mu / r))

    def altitude(self, p) -> float:
        return float(np.linalg.norm(np.asarray(p, float) - self.center)) - self.radius


@dataclass
class Composite(Field):
    """Several bodies at once -- a solar system. Gravity superposes, so this is just a sum, and it
    is what makes Lagrange points and slingshots real rather than scripted."""
    fields: list = field(default_factory=list)

    def at(self, p) -> np.ndarray:
        g = np.zeros(3)
        for f in self.fields:
            g = g + f.at(p)
        return g

    def dominant(self, p):
        """Which body is currently in charge -- what a HUD should name as 'you are near X', and
        which membrane the camera should call its parent."""
        best, bg = None, -1.0
        for f in self.fields:
            s = float(np.linalg.norm(f.at(p)))
            if s > bg:
                best, bg = f, s
        return best, bg


def as_field(g) -> Field:
    """Accept a plain vector (the old constant) or a Field -- so nothing that already worked breaks."""
    if isinstance(g, Field):
        return g
    return Uniform(np.asarray(g, float))


def local_frame(fieldlike, p):
    """An orthonormal (right, forward, up) at a point, with UP from gravity.

    This is the frame a character controller, a HUD horizon and a terrain patch all need, and it is
    the only place 'which way is up' should ever be answered.
    """
    f = as_field(fieldlike)
    up = f.up_at(p)
    ref = np.array([0.0, 0.0, 1.0])
    if abs(float(np.dot(ref, up))) > 0.95:      # degenerate near the poles of the reference axis
        ref = np.array([1.0, 0.0, 0.0])
    right = np.cross(ref, up)
    right /= (np.linalg.norm(right) + 1e-15)
    fwd = np.cross(up, right)
    return right, fwd, up


# ── A GRAVITATIONAL BODY IS A MEMBRANE (operator, 2026-07-25) ─────────────────────────────────
def membrane_world_origin(m) -> np.ndarray:
    """A membrane's origin in world coordinates -- the chain of origins crossed to reach it.
    The same walk `Membrane.path()` makes for the ADDRESS; here it makes the POSITION."""
    p = np.zeros(3)
    node = m
    while node is not None:
        p = p + np.asarray(node.origin, float)
        node = node.parent
    return p


@dataclass
class MembraneField(Field):
    """Gravity DERIVED FROM THE MEMBRANE TREE. A gravitational body is not a special object -- it
    is a membrane carrying a `gravitational` port, which PORT_KINDS already defines as "mass
    coupling to a parent body; what makes a thing FALL toward it".

    A membrane contributes a well if it declares either:
        properties['mu']        the standard gravitational parameter GM, or
        properties['surface_g'] gravity at its own boundary -- with `scale` as the radius, which is
                                how a designer actually thinks ("this planet is 1 g")

    So the hierarchy that already gives ADDRESS, LEVEL OF DETAIL and CLOCK RATE now also gives
    WHICH WAY IS DOWN -- and `dominant()` returns the membrane whose pull currently wins, which is
    the sphere of influence, the parent frame, and the thing a HUD should name, all at once.
    """
    root: object = None
    wells: list = field(default_factory=list)          # [(membrane, PointMass)]

    def __post_init__(self):
        if self.root is not None and not self.wells:
            self.wells = self._collect(self.root)

    @staticmethod
    def _collect(root) -> list:
        out, stack = [], [root]
        while stack:
            m = stack.pop()
            stack.extend(getattr(m, 'children', []))
            props = getattr(m, 'properties', {}) or {}
            has_port = any(getattr(pt, 'kind', '') == 'gravitational'
                           for pt in (getattr(m, 'ports', {}) or {}).values())
            mu = props.get('mu')
            if mu is None and props.get('surface_g') is not None:
                r = float(getattr(m, 'scale', 1.0))
                mu = float(props['surface_g']) * r * r
            if mu is None and not has_port:
                continue
            if mu is None:
                continue
            out.append((m, PointMass(center=membrane_world_origin(m), mu=float(mu),
                                     radius=float(getattr(m, 'scale', 1.0)))))
        return out

    def at(self, p) -> np.ndarray:
        g = np.zeros(3)
        for _, w in self.wells:
            g = g + w.at(p)
        return g

    def dominant(self, p):
        """(membrane, PointMass, strength) whose pull is strongest here -- the sphere of influence.
        This is also the membrane the camera should treat as its parent frame."""
        best, bw, bs = None, None, -1.0
        for m, w in self.wells:
            s = float(np.linalg.norm(w.at(p)))
            if s > bs:
                best, bw, bs = m, w, s
        return best, bw, bs

    def down_path(self, p) -> str:
        """The ADDRESS of whatever is pulling you -- 'you are falling toward THIS'."""
        m, _, _ = self.dominant(p)
        return m.path() if m is not None and hasattr(m, 'path') else '(nothing)'
