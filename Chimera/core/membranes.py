"""membranes — THE PRIMITIVE. A membrane is a boundary, and a boundary is a scale.

    THE MEMBRANE IS THE HIERARCHY. Each nested membrane is the next scale down.

        universe  >  system  >  planet  >  region  >  cell  >  object  >  material  > ...

    Those are not different constructs. They are one construct at different sizes, and
    crossing one inward is exactly what "one scale finer" means.

NOT core/membrane.py. That module seals a git worktree so a cause can be attributed to a
change. This module is the same IDEA -- no inside/outside means no individual, nothing
for selection to act on -- applied to space instead of to work. Kept separate because the
code has nothing in common; the concept has everything.

WHAT BEING A BOUNDARY SUPPLIES, for free, at every level:

    A FRAME       up is the membrane's local normal. A global +Z is wrong on a sphere,
                  wrong in a cave, wrong on a ship's hull. The parent decides what up
                  means for its children.
    A UNIT        coordinates are LOCAL to the membrane, so they can never exceed its own
                  extent. There is no far-from-origin case at any scale. The precision
                  problem does not get managed here; it stops existing.
    AN IDENTITY   the serial number attaches to the membrane. An address is the path of
                  membranes crossed to reach a thing.
    INSIDE/OUT    soil vs air, hull vs void, flesh vs skin. A thing can SPAN the boundary
                  -- a tree's roots are inside the ground membrane, its trunk outside.
    LOD           level of detail is how many membranes deep you have resolved. Approach
                  crosses inward and decompresses; retreat crosses outward and coalesces.
                  A membrane genuinely IS the average of what it contains, because that is
                  what containing something means.

IRREDUCIBLE means: there is always another membrane inside. The world does not bottom out
because containment does not.

VERBS. A verb is not animation and is not authored motion. Following DESIGN section 3 and
Construction/scene.py: an AXIS is two states that DIFFER, a DIAL is a scalar walking
between them, and you never describe an axis -- you exhibit its two ends. So a verb on a
membrane is two named STATES of that membrane plus a dial the game computes. Wind is
(at_rest, fully_bent) with the dial driven by wind speed. Grow is (seed, mature) driven by
time. Open is (closed, open) driven by input. The in-between is derived, never hand-made.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


# --- states and verbs ------------------------------------------------------


@dataclass
class State:
    """One END of a verb — a named point in a membrane's parameter space. Pure data."""
    name: str
    params: dict

    def lerp(self, other: 'State', t: float) -> dict:
        """Interpolate toward another state. Numeric fields blend; others switch at t>=0.5."""
        out = {}
        for k, a in self.params.items():
            b = other.params.get(k, a)
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                out[k] = a + (b - a) * t
            elif isinstance(a, (list, tuple, np.ndarray)) and np.shape(a) == np.shape(b):
                out[k] = (np.asarray(a, float) * (1 - t) + np.asarray(b, float) * t)
            else:
                out[k] = b if t >= 0.5 else a
        for k, b in other.params.items():
            out.setdefault(k, b)
        return out


@dataclass
class Verb:
    """Two states that DIFFER, plus the dial that walks between them.

    You do not describe a verb. You exhibit its ends and let the game compute the dial.
    Extrapolation past [0,1] is allowed -- a gust harder than 'fully bent' is meaningful.
    """
    name: str
    lo: State
    hi: State

    def at(self, t: float) -> dict:
        return self.lo.lerp(self.hi, float(t))

    def differs_in(self) -> list[str]:
        """Which parameters this verb actually moves. A verb whose ends do not differ is
        not a verb -- it is one state written twice, and that is worth catching."""
        return [k for k, a in self.lo.params.items()
                if not np.array_equal(np.asarray(a, dtype=object),
                                      np.asarray(self.hi.params.get(k, a), dtype=object))]


# --- the primitive ---------------------------------------------------------


# --- ports: the studs -----------------------------------------------------
#
# A Lego brick is not just a shape. It is a shape with STUDS, and the studs decide what
# can attach and where. The operator's "LEGO puzzle connection shapes" are physics
# interfaces -- the specific ways matter and energy pass between modules -- so a port is
# typed by WHAT FLOWS THROUGH IT, and two ports connect only if the same thing can flow.
#
# This is what makes composition checkable instead of hopeful: a fuel line does not
# attach to a light socket, and the system can say so before anything is built.

PORT_KINDS = {
    'structural':   'load and rigid attachment — bolts, mounts, foundations, sockets',
    'gravitational': 'mass coupling to a parent body — what makes a thing FALL toward it',
    'energy':       'radiant transfer — sunlight in, engine glow out, heat',
    'fluid':        'liquids — water uptake, coolant, hydraulics, buoyancy',
    'atmospheric':  'gas — breathing, lift, drag, pressure',
    'substrate':    'ground contact — friction, footing, root anchorage',
}


@dataclass
class Port:
    """A stud. Where a membrane can connect, facing which way, and what flows through."""
    name: str
    kind: str
    at: np.ndarray                                 # position in membrane-local coords
    facing: np.ndarray                             # outward normal — which way it points
    size: float = 1.0                              # must match within tolerance to mate

    def __post_init__(self):
        if self.kind not in PORT_KINDS:
            raise ValueError(f'unknown port kind {self.kind!r}; have {sorted(PORT_KINDS)}')
        self.at = np.asarray(self.at, dtype=np.float64)
        f = np.asarray(self.facing, dtype=np.float64)
        self.facing = f / (np.linalg.norm(f) + 1e-12)


@dataclass
class Membrane:
    """A boundary at a scale. Everything in the world is one of these.

    An animated Lego brick with physics properties:
        the BRICK      the boundary itself, at its scale, nested in a parent
        ANIMATED       states + verbs — two ends and a dial, never hand-authored motion
        PHYSICS        `properties`, carrying only what the game actually reads
        STUDS          `ports` — typed connection interfaces that decide what mates
    """
    name: str
    scale: float                                   # extent in metres, in PARENT units
    serial: str = ''                               # identity; the codebook plugs in here
    origin: np.ndarray = field(default_factory=lambda: np.zeros(3))   # in parent coords
    normal: np.ndarray = field(default_factory=lambda: np.array([0., 0., 1.]))
    parent: 'Membrane | None' = None
    children: list = field(default_factory=list)
    states: dict = field(default_factory=dict)     # name -> State
    verbs: dict = field(default_factory=dict)      # name -> Verb
    surface: object = None                         # callable(x,y)->height, or None if a shell
    properties: dict = field(default_factory=dict)  # PHYSICS the game reads: density, friction...
    ports: dict = field(default_factory=dict)      # name -> Port

    # --- nesting -----------------------------------------------------------

    def add(self, child: 'Membrane') -> 'Membrane':
        """Nest a membrane inside this one. The child is one scale finer, by definition."""
        child.parent = self
        self.children.append(child)
        return child

    def path(self) -> str:
        """The full containment path — the address, as a chain of membranes crossed."""
        node, parts = self, []
        while node is not None:
            parts.append(node.serial or node.name)
            node = node.parent
        return '/'.join(reversed(parts))

    def depth(self) -> int:
        """How many membranes deep. This IS the level of detail."""
        n, node = 0, self.parent
        while node is not None:
            n += 1
            node = node.parent
        return n

    # --- frame -------------------------------------------------------------

    def up_at(self, local_point=None) -> np.ndarray:
        """UP is the membrane's local normal — not a global axis.

        For a shell (a planet), up points away from the centre and therefore differs at
        every point on it. For a flat membrane it is constant. This is why declaring one
        global +Z was wrong: up is a property of the boundary you are standing on.
        """
        if local_point is None or self.surface is not None:
            n = np.asarray(self.normal, float)
        else:
            p = np.asarray(local_point, float)
            n = p if np.linalg.norm(p) > 1e-12 else np.asarray(self.normal, float)
        return n / (np.linalg.norm(n) + 1e-12)

    def to_local(self, parent_point) -> np.ndarray:
        return np.asarray(parent_point, dtype=np.float64) - np.asarray(self.origin, np.float64)

    def to_parent(self, local_point) -> np.ndarray:
        return np.asarray(local_point, dtype=np.float64) + np.asarray(self.origin, np.float64)

    def to_world(self, local_point) -> np.ndarray:
        """Walk out to the root, accumulating in float64 the whole way.

        Coordinates stay LOCAL at every level, so nothing is ever large relative to the
        membrane it lives in. The huge number only appears at the very end, if anyone
        actually asks for it -- which is why precision never degrades.
        """
        p = np.asarray(local_point, dtype=np.float64)
        node = self
        while node is not None:
            p = p + np.asarray(node.origin, dtype=np.float64)
            node = node.parent
        return p

    # --- inside / outside ---------------------------------------------------

    def side(self, local_point) -> str:
        """'inside', 'outside', or 'on'. A thing may SPAN the boundary."""
        p = np.asarray(local_point, dtype=np.float64)
        if self.surface is not None:                       # a height field membrane
            h = float(self.surface(p[0], p[1]))
            d = float(p[2]) - h
        else:                                              # a shell of radius `scale`
            d = float(np.linalg.norm(p)) - self.scale
        tol = 1e-6 * max(self.scale, 1.0)
        return 'on' if abs(d) <= tol else ('outside' if d > 0 else 'inside')

    def contains(self, local_point) -> bool:
        return self.side(local_point) in ('inside', 'on')

    # --- verbs --------------------------------------------------------------

    def state(self, name: str, **params) -> State:
        s = State(name, params)
        self.states[name] = s
        return s

    def verb(self, name: str, lo: str, hi: str) -> Verb:
        """Define a verb as two EXISTING states that differ. Refuses ends that do not."""
        if lo not in self.states or hi not in self.states:
            raise KeyError(f'{name}: both ends must be states of {self.name!r}; '
                           f'have {sorted(self.states)}')
        v = Verb(name, self.states[lo], self.states[hi])
        if not v.differs_in():
            raise ValueError(f'{name}: its two ends are identical — that is not a verb, '
                             f'it is one state written twice')
        self.verbs[name] = v
        return v

    def apply(self, verb_name: str, t: float) -> dict:
        """The derived state at dial position t. Never hand-animated."""
        return self.verbs[verb_name].at(t)

    # --- studs: physics properties and connection ---------------------------

    def port(self, name: str, kind: str, at, facing, size: float = 1.0) -> Port:
        p = Port(name, kind, at, facing, size)
        self.ports[name] = p
        return p

    def prop(self, **physics) -> dict:
        """Set the physics the game reads. A brick carries ONLY what is actually used —
        density, friction, restitution. Not a full material simulation."""
        self.properties.update(physics)
        return self.properties

    def can_mate(self, port_name: str, other: 'Membrane', other_port: str,
                 tol: float = 0.15) -> tuple[bool, str]:
        """Would these two studs connect? Returns (verdict, reason) — always a reason.

        Three conditions, and all are physical rather than conventional:
          SAME KIND     the same thing must be able to flow through both. A fuel line
                        does not attach to a light socket.
          OPPOSED       the ports must FACE each other. Two studs pointing the same way
                        cannot mate, which is exactly true of real Lego.
          MATCHED SIZE  the interface has a scale, and mismatched scales do not seat.
        """
        a, b = self.ports.get(port_name), other.ports.get(other_port)
        if a is None or b is None:
            return False, f'missing port ({port_name!r} / {other_port!r})'
        if a.kind != b.kind:
            return False, f'{a.kind} cannot carry {b.kind} — nothing flows through that joint'
        dot = float(np.dot(a.facing, b.facing))
        if dot > -0.5:
            return False, f'ports do not face each other (facing dot {dot:+.2f}, need < -0.5)'
        if abs(a.size - b.size) > tol * max(a.size, b.size):
            return False, f'size mismatch {a.size:g} vs {b.size:g}'
        return True, f'{a.kind} joint, facing dot {dot:+.2f}'

    def mate(self, port_name: str, other: 'Membrane', other_port: str) -> 'Membrane':
        """SNAP. Nest `other` and place it so the two studs meet.

        A stud fixes both WHERE and WHICH WAY, so connecting is placement, not a hint.
        """
        ok, why = self.can_mate(port_name, other, other_port)
        if not ok:
            raise ValueError(f'cannot mate {self.name}.{port_name} -> '
                             f'{other.name}.{other_port}: {why}')
        a, b = self.ports[port_name], other.ports[other_port]
        self.add(other)
        other.origin = np.asarray(a.at, dtype=np.float64) - np.asarray(b.at, dtype=np.float64)
        other.normal = -a.facing
        return other

    def open_ports(self) -> list:
        """Studs with nothing on them — where this brick can still take something.

        This is what makes a build enumerable: an unfilled port is a place the world is
        not finished, and the six directions are just the ports of a cell.
        """
        used = set()
        for c in self.children:
            for pn, p in self.ports.items():
                if np.allclose(np.asarray(c.origin, float) + 0.0, p.at - 0.0, atol=1e-9):
                    used.add(pn)
        return [p for n, p in self.ports.items() if n not in used]

    # --- reporting ----------------------------------------------------------

    def describe(self) -> str:
        v = ', '.join(f'{k}[{"/".join(x.differs_in())}]' for k, x in self.verbs.items())
        return (f'{self.path()}  scale={self.scale:g}m  depth={self.depth()}  '
                f'children={len(self.children)}' + (f'  verbs: {v}' if v else ''))

    def walk(self, _d: int = 0):
        yield _d, self
        for c in self.children:
            yield from c.walk(_d + 1)


def main() -> None:
    universe = Membrane('universe', scale=9.46e15, serial='U')
    planet = universe.add(Membrane('planet', scale=6.371e6, serial='P-earth',
                                   origin=np.array([1.5e11, 0.0, 0.0])))
    ground = planet.add(Membrane('ground', scale=1.0, serial='G',
                                 surface=lambda x, y: 0.4 * np.sin(x * 0.1) + 0.2 * np.cos(y * 0.13)))
    cell = ground.add(Membrane('cell', scale=1.83, serial='C+000024+000056'))
    rock = cell.add(Membrane('rock', scale=0.3, serial='M-0047',
                             origin=np.array([0.4, 0.2, 0.0])))

    print('=== the hierarchy IS nested membranes ===')
    for d, m in universe.walk():
        print('  ' + '  ' * d + m.describe())

    print('\n=== inside / outside a height-field membrane ===')
    for p in ([0.0, 0.0, 2.0], [0.0, 0.0, -2.0], [0.0, 0.0, 0.2]):
        print(f'  point {p} -> {ground.side(p)}')

    print('\n=== up is LOCAL, not a global axis ===')
    shell = Membrane('shell', scale=6.371e6)
    for p in ([6.371e6, 0, 0], [0, 6.371e6, 0], [0, 0, 6.371e6]):
        print(f'  on the shell at {np.round(np.asarray(p)/1e6,2)} Mm -> up = '
              f'{np.round(shell.up_at(p), 3)}')

    print('\n=== a VERB is two states that differ, and a dial ===')
    cell.state('at_rest', bend=0.0, height=1.0, sway=0.0)
    cell.state('fully_bent', bend=0.8, height=0.55, sway=1.0)
    cell.verb('wind', 'at_rest', 'fully_bent')
    for t in (0.0, 0.35, 1.0, 1.4):
        s = cell.apply('wind', t)
        print(f'  wind dial {t:>4} -> ' + '  '.join(f'{k}={v:.3f}' for k, v in s.items()))

    print('\n=== a verb whose ends do not differ is refused ===')
    cell.state('a', x=1.0)
    cell.state('b', x=1.0)
    try:
        cell.verb('nothing', 'a', 'b')
    except ValueError as e:
        print(f'  {e}')

    print('\n=== precision: coordinates stay local, the big number appears only at the end ===')
    p_local = np.array([0.05, 0.02, 0.01])
    print(f'  rock-local {p_local} -> world {rock.to_world(p_local)}')
    print(f'  largest number ever held inside a membrane: its own scale, never more')


if __name__ == '__main__':
    main()
