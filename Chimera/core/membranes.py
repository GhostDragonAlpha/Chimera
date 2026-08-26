# TWIN: kept byte-equal with the same-named module in the sibling core/ tree; edit both or consolidate deliberately -- see docs/THE_TWIN_TABLE.md.
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

# The system's speed of light: the ceiling on any membrane's clock. A membrane cannot tick
# faster than light crosses it (rate <= C_LIGHT / scale). Where the density clock (sqrt(density))
# would exceed that ceiling, the region can no longer talk to itself fast enough to hold together
# as ONE object -- it TEARS into a black hole. This is the density clock meeting the light limit,
# which is exactly the Schwarzschild condition (sqrt(G*rho) = c/R  <=>  R = GM/c^2). Set large so
# ordinary membranes -- verbs, ships, tissue -- never approach it; only extreme density x size do.
C_LIGHT = 1.0e4


def schwarzschild_scale(mass: float) -> float:
    """The scale below which a mass tears into a black hole: R_s = mass / C_LIGHT^2 (= GM/c^2 with
    G folded into the units). Compress a mass past this and the density clock passes the light
    ceiling -- the event horizon, out of the same clock the verbs run on."""
    return mass / C_LIGHT ** 2


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
class Gate:
    """A checkpoint on a dial: it cannot advance past `at` until `holds` is true.

    This is the whole of game progression. A player does not slide smoothly from the
    first frame to the end -- they are held at a point until something measurable is
    true, and then released. Open-world included: grinding reputation to upgrade a gun
    is a 0..1 dial with a gate on it. So progression is not a separate system, it is a
    dial with conditions, and the condition is MEASURED rather than declared.
    """
    at: float
    name: str
    holds: object = None                 # callable(state)->bool; None means always open

    def open_for(self, state) -> bool:
        return True if self.holds is None else bool(self.holds(state))


@dataclass
class Verb:
    """Two states that DIFFER, plus the dial that walks between them.

    You do not describe a verb. You exhibit its ends and let the game compute the dial.
    Extrapolation past [0,1] is allowed -- a gust harder than 'fully bent' is meaningful.
    """
    name: str
    lo: State
    hi: State
    gates: list = field(default_factory=list)      # checkpoints, in dial order

    def at(self, t: float) -> dict:
        return self.lo.lerp(self.hi, float(t))

    def gate(self, at: float, name: str, holds=None) -> 'Gate':
        g = Gate(at, name, holds)
        self.gates.append(g)
        self.gates.sort(key=lambda x: x.at)
        return g

    def reachable(self, t: float, state=None) -> float:
        """How far the dial may actually advance, given the gates.

        Requested t is a WISH; this returns what the world permits. The first closed
        gate below t is the wall, and the dial stops there.
        """
        t = float(t)
        for g in self.gates:
            if g.at <= t and not g.open_for(state):
                return g.at
        return t

    def advance(self, t: float, state=None) -> tuple:
        """(derived state, dial actually reached, name of the gate that stopped it)."""
        r = self.reachable(t, state)
        blocked = next((g.name for g in self.gates if abs(g.at - r) < 1e-12
                        and not g.open_for(state)), None)
        return self.at(r), r, blocked

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
    skin: float = 1e-3                             # thickness of "on the boundary", metres
    attached_via: str = ''                         # the parent's port this mated onto

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

    # --- density and the clock: everything here is RELATIVE -----------------
    #
    # The operator's identities, folded into one: "density and relative scale are the same
    # term", "density is a compression of relative mass", "it's all relativity". Density is
    # mass per volume -- mass RELATIVE to the space it fills -- and in a self-similar nesting
    # that ratio IS the relative scale. So a membrane is never GIVEN a density; density exists
    # only in RELATION to the parent, and you cannot read it from inside the membrane -- you
    # have to look outside it. (The same reason a relative velocity, or love, is meaningless
    # from one frame: it lives in the relationship, not the thing. You think outside yourself
    # to see it.)
    #
    # The clock follows from the density. The dynamical / free-fall time of a gravitating system
    # is t ~ 1/sqrt(G*rho), and the SIZE CANCELS (T = sqrt(3*pi / (G*rho)) has no radius in it).
    # So the natural rate goes as sqrt(density): denser (finer) membranes tick faster, and two
    # membranes of equal density tick alike whatever their size. This is the gravitational /
    # self-similar clock; a real atom runs faster still on a stronger (electromagnetic, quantum)
    # clock -- the forces take turns as you cross scales.

    def density(self) -> float:
        """Density = relative mass = relative scale: how much finer this membrane is than its
        parent. RELATIONAL -- the root is 1, and a child has no density of its own; it only has
        one relative to the parent it is nested in. One term, and it is read from OUTSIDE.

        If the membrane is made of a KNOWN material it carries that material's density (a RATIO
        to a reference material) in properties['density']; otherwise density DEFAULTS to the
        relative scale -- the self-similar assumption that a child is as dense as it is small.
        Either way it is a dimensionless ratio: relative mass and relative scale, one term."""
        d = self.properties.get('density')
        if d is not None:
            return float(d)
        if self.parent is None:
            return 1.0
        return float(self.parent.scale) / max(float(self.scale), 1e-30)

    def clock_rate(self) -> float:
        """How fast this membrane's dynamics tick, relative to its parent: sqrt(density), from
        t ~ 1/sqrt(G*rho). The size drops out -- only the density (relative scale) sets it."""
        return float(np.sqrt(self.density()))

    def tick(self) -> float:
        """The natural timestep relative to the parent -- 1/clock_rate. Finer = denser = shorter
        step = faster. A planet-scale membrane crawls; an atom-scale one blurs."""
        return 1.0 / self.clock_rate()

    def clock_rate_from_root(self) -> float:
        """Cumulative clock rate from the root down to here: sqrt(total refinement). Because
        sqrt is multiplicative, this equals the product of clock_rate() at every level crossed."""
        root = self
        while root.parent is not None:
            root = root.parent
        return float(np.sqrt(float(root.scale) / max(float(self.scale), 1e-30)))

    # --- the ceiling: where the clock meets light, matter tears (a black hole) ---

    def light_ceiling_rate(self) -> float:
        """The fastest this membrane can possibly tick: the light-crossing rate C_LIGHT / scale.
        Nothing internal can cycle faster than light crosses the region."""
        return C_LIGHT / max(float(self.scale), 1e-30)

    def black_hole_ratio(self) -> float:
        """How close to tearing: the density clock over the light ceiling = sqrt(density)*scale
        / C_LIGHT. At 1.0 the dynamical clock equals the light-crossing rate -- the event
        horizon. This is the Schwarzschild condition rho*R^2 ~ c^2/G, written in the clock."""
        return self.clock_rate() * float(self.scale) / C_LIGHT

    def tears(self) -> bool:
        """True if the density clock would exceed the light ceiling -- the region cannot hold
        together as one object and collapses. A BLACK HOLE, out of the same clock the verbs run
        on. Everything below this membrane is causally sealed: this is why you cannot see in."""
        return self.black_hole_ratio() >= 1.0

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
        # A BOUNDARY IS THIN, and its thickness is its own, not its parent's. This was
        # 1e-6 * scale, so a ground membrane on a 6371 km planet called anything within
        # +/-6.4 m "on the surface" -- a man standing up and a man buried both read as
        # touching it. `skin` is absolute (default 1 mm) because a surface does not get
        # thicker just because the world it wraps is large.
        return 'on' if abs(d) <= self.skin else ('outside' if d > 0 else 'inside')

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
        other.attached_via = port_name          # recorded, so occupancy is a fact
        return other

    def open_ports(self) -> list:
        """Studs with nothing on them — where this brick can still take something.

        This is what makes a build enumerable: an unfilled port is a place the world is
        not finished, and the six directions are just the ports of a cell.

        Occupancy is RECORDED by mate(), not inferred from geometry. It was inferred at
        first -- by testing whether a child's origin equalled a port's position -- which
        silently failed for every brick whose own stud was not at its centre, i.e. all of
        them. State that can be recorded should never be reconstructed from coordinates.
        """
        used = {c.attached_via for c in self.children if c.attached_via}
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


# ---------------------------------------------------------------------------
# THE WORLD AS MEMBRANES
#
# core/sections.py, progeny's tiles and membrane_shapes were three parallel systems
# doing what one construct does. These constructors express them AS membranes without
# touching their internals -- the verified seam, tiling and render behaviour keeps
# running underneath, and the duplication becomes a single hierarchy above it.
#
# THE SIX DIRECTIONS ARE THE SIX PORTS OF A CELL. That is not an analogy: a direction
# is a face you can attach through, an unfilled port is somewhere the world is not
# finished, and open_ports() is therefore the work queue. Fill six, migrate.
# ---------------------------------------------------------------------------

SIX = (('down', (0., 0., -1.)), ('up', (0., 0., 1.)),
       ('north', (0., 1., 0.)), ('south', (0., -1., 0.)),
       ('east', (1., 0., 0.)), ('west', (-1., 0., 0.)))

HUMAN_CELL = 1.83          # 6 ft: a person and their arm span


def universe(name: str = 'universe', extent: float = 9.46e15) -> Membrane:
    """The root. Everything else nests inside it."""
    return Membrane(name, scale=extent, serial='U')


def planet(parent: Membrane, name: str, radius: float = 6.371e6,
           origin=(0., 0., 0.), relief: float = 1.5) -> Membrane:
    """A planet, whose GROUND MEMBRANE is the height field.

    The heightmap is not terrain-as-a-thing. It is the boundary that decides inside
    (soil, roots, caves) from outside (air, things resting on the surface), which is why
    a tree can span it.
    """
    from core.progeny import world_height
    p = parent.add(Membrane(name, scale=radius, serial=f'P-{name}',
                            origin=np.asarray(origin, dtype=np.float64)))
    p.prop(radius_m=radius, gravity_m_s2=9.81)
    ground = p.add(Membrane('ground', scale=radius, serial='G',
                            surface=lambda x, y: float(world_height(x, y, amplitude=relief))))
    ground.prop(relief_amplitude=relief)
    ground.port('surface', 'substrate', at=[0., 0., 0.], facing=[0., 0., 1.], size=radius)
    return ground


def section(ground: Membrane, world_x: float, world_y: float) -> Membrane:
    """A section — one session's worth of work — with its four lateral neighbours as ports."""
    from core.sections import section_at, SECTION_SPAN
    s = section_at(world_x, world_y)
    ox, oy = s['origin']
    m = ground.add(Membrane('section', scale=SECTION_SPAN, serial=s['serial'],
                            origin=np.array([ox, oy, 0.0], dtype=np.float64)))
    h = SECTION_SPAN * 0.5
    for nm, d in (('east', (1., 0., 0.)), ('west', (-1., 0., 0.)),
                  ('north', (0., 1., 0.)), ('south', (0., -1., 0.))):
        m.port(nm, 'structural', at=np.asarray(d) * h, facing=d, size=SECTION_SPAN)
    return m


def cell(parent: Membrane, i: int, j: int, k: int = 0,
         size: float = HUMAN_CELL) -> Membrane:
    """A human-scale cell — the placement slot — with the SIX DIRECTIONS as its ports.

    Six studs, one per direction. Filling one attaches a membrane through that face;
    when none remain open the cell is saturated and you migrate. The work queue is not
    a list someone maintains — it is the set of unfilled studs.
    """
    from core.progeny import tile_seed
    c = parent.add(Membrane(f'cell', scale=size, serial=f'C{i:+06d}{j:+06d}{k:+04d}',
                            origin=np.array([i * size, j * size, k * size], dtype=np.float64)))
    c.prop(seed=tile_seed(i, j, salt=k))
    for nm, d in SIX:
        c.port(nm, 'structural', at=np.asarray(d) * (size * 0.5), facing=d, size=size)
    return c


def work_queue(root: Membrane) -> list:
    """Every unfilled stud in the tree — the world's to-do list, enumerated not authored."""
    out = []
    for _, m in root.walk():
        for p in m.open_ports():
            out.append((m.path(), p.name, p.kind))
    return out


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

    print('\n=== density IS relative scale, and the clock follows sqrt(density) ===')
    print('  (a membrane has no density of its own -- only relative to its parent: relativity)')
    tower = Membrane('L0', scale=1.0e6)
    node = tower
    for k in range(1, 5):
        node = node.add(Membrane(f'L{k}', scale=1.0e6 / (100 ** k)))     # each level 100x finer
    for _, m in tower.walk():
        print(f'  {m.name}  scale={m.scale:.2e} m  density(vs parent)={m.density():7.1f}  '
              f'clock x{m.clock_rate_from_root():.2e} vs root')

    print('\n=== size-independence: equal density -> equal clock, whatever the size ===')
    ac = Membrane('a', scale=1000.0).add(Membrane('ac', scale=10.0))       # density 100
    bc = Membrane('b', scale=2.0).add(Membrane('bc', scale=0.02))          # density 100
    print(f'  a 100x-finer child of a 1 km membrane and of a 2 m membrane tick IDENTICALLY:')
    print(f'  clock_rate {ac.clock_rate():.2f} vs {bc.clock_rate():.2f}  '
          f'(density 100 both -> sqrt(100) = 10). The size cancels; density is the clock.')

    print('\n=== the clock has a CEILING: compress a mass and it TEARS into a black hole ===')
    print(f'  no membrane can tick faster than light crosses it (C_LIGHT/scale). Where the')
    print(f'  density clock would pass that, it tears -- the Schwarzschild condition.')
    MASS = 1.0e10
    print(f'  compress a fixed mass {MASS:.0e}; predicted event horizon R_s = mass/C_LIGHT^2 '
          f'= {schwarzschild_scale(MASS):.0f}\n')
    print(f'  {"scale R":>9} {"density":>12} {"clock":>10} {"ceiling c/R":>12} {"ratio":>7}   verdict')
    for sc in (1000.0, 300.0, 100.0, 30.0):
        bh = Membrane('m', scale=sc)
        bh.prop(density=MASS / sc ** 3)                    # rho = M / R^3
        verdict = 'TORN -> black hole' if bh.tears() else 'holds together'
        print(f'  {sc:>9.0f} {bh.density():>12.0f} {bh.clock_rate():>10.0f} '
              f'{bh.light_ceiling_rate():>12.0f} {bh.black_hole_ratio():>7.2f}   {verdict}')
    print(f'\n  it tears at exactly R_s = {schwarzschild_scale(MASS):.0f}: the density clock meeting')
    print(f'  the speed of light IS the event horizon (R ~ GM/c^2), out of the verbs own clock.')


if __name__ == '__main__':
    main()
