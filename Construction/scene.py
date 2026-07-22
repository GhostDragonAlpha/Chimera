"""The renderer-agnostic scene model + the anchor / axis / dial mechanism.

difference = dimension (DESIGN §3):
    an Axis is two Anchors that *differ*; a Dial is a scalar that walks between
    them; fill() is the interpolation.  Nothing in this file knows how a thing is
    drawn — that is a backend's job.  This is the single source of truth that
    both backends (backend_3d, backend_html) project.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Anchor:
    """A named point in parameter space — one END of an axis.  Pure data.

    You do not describe an axis; you exhibit its two ends.  The human authors
    these (DESIGN §2)."""
    name: str
    params: dict


@dataclass
class Axis:
    """A controllable dimension, exhibited by its two ends (not described)."""
    name: str
    lo: Anchor
    hi: Anchor

    def fill(self, t: float) -> dict:
        """Walk the axis.  t in [0,1] canonically; extrapolation is allowed.

        Direct-parameter lerp — valid only where the parameter space is
        convex (every blend of two valid points is valid).  The wind axis is;
        an arbitrary axis is not, and would go through the VAE manifold instead
        (DESIGN §3, §F — not yet wired)."""
        a, b = self.lo.params, self.hi.params
        keys = set(a) | set(b)
        return {k: a.get(k, 0.0) * (1.0 - t) + b.get(k, 0.0) * t for k in keys}


@dataclass
class Dial:
    """A scalar bound to an axis.  Settable directly, or driven by game state."""
    axis: Axis
    value: float = 0.0

    def state(self) -> dict:
        return self.axis.fill(self.value)


@dataclass
class PlacedObject:
    """A thing placed in the world.  `world_pos` is direct placement — the
    identity case of the map-lift (DESIGN §4)."""
    kind: str                                   # "tree"
    generator: str                              # "physics_tree"
    seed: int
    world_pos: tuple = (0.0, 0.0, 0.0)
    params: dict = field(default_factory=dict)  # generator params


@dataclass
class Scene:
    """A scene = placed objects + named dials.  Renderer-agnostic."""
    objects: list = field(default_factory=list)
    dials: dict = field(default_factory=dict)   # name -> Dial

    def add(self, obj: PlacedObject) -> PlacedObject:
        self.objects.append(obj)
        return obj

    def add_dial(self, name: str, dial: Dial) -> Dial:
        self.dials[name] = dial
        return dial

    def dial(self, name: str) -> Dial:
        return self.dials[name]
