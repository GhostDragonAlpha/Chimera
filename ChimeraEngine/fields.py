"""fields.py — THE FIELDS: electromagnetism and light (operator, 2026-07-25).

    "What resists matter from merging into itself? It's the electromagnetic field. It prevents
     matter from falling through other matter -- collision is just another field."

That is correct physics. What stops a hand passing through a table is EM repulsion between electron
clouds (plus Pauli exclusion); solid matter is overwhelmingly empty space, and "solidity" is a
FORCE, not a substance. So contact is not a special case -- it is the EM field at short range.

ONE CURVE, TWO LOBES. Repulsive when boundaries overlap, attractive just outside: the Lennard-Jones
shape. That single profile gives SOLIDITY, COHESION, ADHESION and the normal load that friction is
bounded by. And the attractive lobe is already in this project under another name -- core/matter.py
grows tissue by DIFFERENTIAL ADHESION. Collision is the other end of the same dial.

    HONEST ENGINEERING CAVEAT, and it is load-bearing: conceptually EM, computationally NEVER.
    True pairwise repulsion between all particles is O(n^2) and hopeless at game scale. The
    repulsion is so short-ranged that it is effectively a SURFACE property -- it only matters where
    boundaries nearly touch. So the field is the MEANING and the boundary is the SHORTCUT. The
    penalty contact already in contact.py is exactly a linearised repulsive lobe evaluated at the
    boundary; it was simply named "contact" instead of "the short-range limit of the EM field".

THE TAXONOMY the operator asked for -- what a ship's computer tracks, what a body senses:

    FIELD     exists at every point, acts at a distance, and can be SENSED
              gravity (built) | electromagnetic (here) | light (here) | thermal | atmospheric |
              fluid | acoustic
    PROPERTY  belongs to a membrane, not to space:  mass, charge, hardness, albedo, area
    STATE     a membrane's own numbers over time:   position, velocity, angular velocity, fuel

Mass is NOT a field -- but the gravitational field is how mass makes itself felt, and charge is how
a membrane couples to EM. That is the pattern: a PROPERTY is what you have, a FIELD is how the
universe carries its consequence, and a PORT is where the two meet.
"""
from __future__ import annotations

from dataclasses import dataclass, field as dfield

import numpy as np

from gravity import Field


# ══════════════════════════════════════════════════════════════════════════════════════════════
#  ELECTROMAGNETIC — what holds matter apart
# ══════════════════════════════════════════════════════════════════════════════════════════════
@dataclass
class Coupling:
    """The short-range law between two boundaries, as a function of the GAP between them.

        gap < 0   the boundaries overlap      -> REPULSION (this is solidity)
        gap ~ 0+  just touching               -> ATTRACTION (adhesion, cohesion, surface tension)
        gap > reach                           -> nothing

    `stiffness` IS the material's hardness -- steel and rubber differ by this number and nothing
    else. `adhesion` is how hard it clings once in contact; `reach` is how far the cling extends.
    """
    stiffness: float = 4.0e5          # N/m -- the repulsive lobe. Hardness.
    adhesion: float = 0.0             # N    -- depth of the attractive well. Stickiness.
    reach: float = 1e-3               # m    -- how far the attraction reaches past contact
    damping: float = 6.0e3            # N.s/m -- energy lost in the collision

    def force(self, gap: float, gap_rate: float = 0.0) -> float:
        """Signed force along the outward normal: POSITIVE pushes apart, NEGATIVE pulls together.

        Deliberately not the literal 1/r^12 - 1/r^6: that blows up numerically and its exact shape
        is an atomic-scale detail no game reads. The SHAPE is what matters -- steep repulsion, a
        shallow attractive well, zero beyond reach -- and this reproduces it stably.
        """
        if gap < 0.0:                                  # overlapping: push apart, hard
            return self.stiffness * (-gap) - self.damping * gap_rate
        if self.adhesion > 0.0 and gap < self.reach:   # just outside: cling
            x = gap / self.reach                       # 0 at contact -> 1 at the edge of reach
            return -self.adhesion * (1.0 - x) * (1.0 - x)
        return 0.0

    def profile(self, gaps):
        return np.array([self.force(float(g)) for g in np.asarray(gaps, float)])

    def pull_off_force(self) -> float:
        """The force needed to separate two stuck surfaces -- the depth of the attractive well."""
        return float(self.adhesion)


# Materials are just numbers on that curve. This is the whole of "what is this made of", mechanically.
STEEL = Coupling(stiffness=2.0e7, adhesion=0.0, damping=3.0e4)
ROCK = Coupling(stiffness=5.0e6, adhesion=0.0, damping=2.0e4)
RUBBER = Coupling(stiffness=2.0e5, adhesion=0.0, damping=8.0e3)
FLESH = Coupling(stiffness=6.0e4, adhesion=20.0, reach=2e-3, damping=4.0e3)
TAPE = Coupling(stiffness=2.0e5, adhesion=400.0, reach=3e-3, damping=6.0e3)
REGOLITH = Coupling(stiffness=8.0e5, adhesion=6.0, reach=1e-3, damping=1.2e4)   # dust clings


@dataclass
class EMField(Field):
    """Electromagnetism as a FIELD sibling to gravity.

    Two faces. The SHORT-range face is `Coupling` above -- solidity and adhesion, evaluated at
    boundaries. The LONG-range face is the ordinary inverse-square law from net charge, which is
    what this `at()` returns so the class satisfies the same Field interface gravity does.

    Unlike gravity, charge comes in two signs and therefore CANCELS at large scale -- which is
    exactly why gravity rules planets and EM rules atoms, and why the long-range face is usually
    zero while the short-range face is what you feel all day.
    """
    sources: list = dfield(default_factory=list)       # [(position, charge)]
    k: float = 8.9875517923e9                          # Coulomb constant

    def at(self, p) -> np.ndarray:
        """Electric field at a point, per unit charge. Zero in a neutral world -- as it should be."""
        p = np.asarray(p, float)
        e = np.zeros(3)
        for (c_pos, q) in self.sources:
            d = p - np.asarray(c_pos, float)
            r = float(np.linalg.norm(d))
            if r < 1e-9:
                continue
            e = e + self.k * q * d / (r ** 3)
        return e

    def up_at(self, p) -> np.ndarray:
        """EM does not define an up. Gravity does. Returning +Z here would be a quiet lie, so this
        says so explicitly rather than pretending."""
        raise NotImplementedError("EM has no 'up' -- ask the gravity field")


# ══════════════════════════════════════════════════════════════════════════════════════════════
#  LIGHT — the field the renderer, the solar panel and the thermometer all read
# ══════════════════════════════════════════════════════════════════════════════════════════════
@dataclass
class Star:
    """A light source. `luminosity` in watts; irradiance falls as 1/r^2 by geometry alone."""
    center: np.ndarray = dfield(default_factory=lambda: np.zeros(3))
    luminosity: float = 3.828e26          # the Sun, W
    radius: float = 6.957e8

    def __post_init__(self):
        self.center = np.asarray(self.center, float)

    @classmethod
    def from_irradiance(cls, center, at_distance: float, irradiance: float, radius: float = 1.0):
        """Build from what you can measure: 'this bright, at this range'. (Earth sees 1361 W/m^2.)"""
        return cls(center=np.asarray(center, float),
                   luminosity=irradiance * 4.0 * np.pi * at_distance ** 2, radius=radius)

    def irradiance_at(self, p) -> float:
        r = float(np.linalg.norm(np.asarray(p, float) - self.center))
        return self.luminosity / (4.0 * np.pi * max(r, self.radius) ** 2)


@dataclass
class Occluder:
    """A body that casts a shadow. A planet eclipsing its own night side is the same object as a
    moon eclipsing a planet -- day/night and eclipse are ONE mechanism, not two."""
    center: np.ndarray = dfield(default_factory=lambda: np.zeros(3))
    radius: float = 1.0

    def __post_init__(self):
        self.center = np.asarray(self.center, float)

    def blocks(self, p, light_center) -> bool:
        """Does the segment from p to the light pass through this sphere?"""
        p = np.asarray(p, float)
        d = np.asarray(light_center, float) - p
        L = float(np.linalg.norm(d))
        if L < 1e-12:
            return False
        u = d / L
        m = p - self.center
        b = float(np.dot(m, u))
        c = float(np.dot(m, m)) - self.radius ** 2
        if c < 0.0 and b > 0.0:                       # inside the sphere, light outward
            return True
        disc = b * b - c
        if disc < 0.0:
            return False
        t = -b - np.sqrt(disc)                        # nearest intersection along the ray
        return 0.0 < t < L                            # blocked only if the body is BETWEEN


@dataclass
class LightField:
    """Irradiance and direction at any point, with shadows.

    ONE field, THREE consumers -- which is the argument for building it: the RENDERER needs the
    direction for N.L shading and the terminator; a SOLAR PANEL needs the irradiance; a THERMAL
    model needs the absorbed power. All three read the same numbers.
    """
    stars: list = dfield(default_factory=list)
    occluders: list = dfield(default_factory=list)

    def irradiance_at(self, p) -> float:
        total = 0.0
        for s in self.stars:
            if not any(o.blocks(p, s.center) for o in self.occluders):
                total += s.irradiance_at(p)
        return float(total)

    def direction_at(self, p):
        """Unit vector TOWARD the brightest visible star, or None in full shadow."""
        best, bi = None, 0.0
        p = np.asarray(p, float)
        for s in self.stars:
            if any(o.blocks(p, s.center) for o in self.occluders):
                continue
            i = s.irradiance_at(p)
            if i > bi:
                best, bi = s, i
        if best is None:
            return None
        d = best.center - p
        return d / (np.linalg.norm(d) + 1e-15)

    def lit_fraction(self, p, normal) -> float:
        """Lambert's cosine law: N.L, clamped. This is the terminator, and it is the renderer's
        missing lighting term (ROADMAP A3) arriving as a field rather than as a shader constant."""
        L = self.direction_at(p)
        if L is None:
            return 0.0
        return max(0.0, float(np.dot(np.asarray(normal, float), L)))

    def power_on(self, p, normal, area: float, efficiency: float = 1.0) -> float:
        """Watts collected by a panel of `area` facing `normal`. Solar power, exactly."""
        return self.irradiance_at(p) * self.lit_fraction(p, normal) * area * efficiency

    def equilibrium_temperature(self, p, albedo: float = 0.3) -> float:
        """The blackbody temperature a body settles at under this irradiance -- Stefan-Boltzmann.
        This is the number that decided the habitable zone in the project's own planet rung."""
        S = self.irradiance_at(p)
        sigma = 5.670374419e-8
        return float((S * (1.0 - albedo) / (4.0 * sigma)) ** 0.25)


# ══════════════════════════════════════════════════════════════════════════════════════════════
#  THERMAL — light that has been absorbed and not yet re-emitted
# ══════════════════════════════════════════════════════════════════════════════════════════════
SIGMA = 5.670374419e-8                     # Stefan-Boltzmann


@dataclass
class Thermal:
    """A material's thermal character. Four numbers, and they settle every temperature question.

    `capacity` is the one that surprises people: it is heat capacity PER SQUARE METRE of surface
    (J/m^2/K), because what matters for a day/night swing is how much heat the skin can bank before
    the sun goes down. It is why the Moon drops ~300 K at nightfall and the ocean drops almost none.
    """
    albedo: float = 0.3               # fraction of light reflected, never absorbed
    emissivity: float = 0.95          # how well it radiates -- near 1 for rock, low for polished metal
    capacity: float = 3.2e4           # J/m^2/K -- thermal inertia of the skin
    conductivity: float = 1.0         # W/m/K -- how fast heat moves INWARD


LUNAR_REGOLITH = Thermal(albedo=0.11, emissivity=0.95, capacity=3.2e4, conductivity=0.01)
ROCK_T = Thermal(albedo=0.25, emissivity=0.95, capacity=2.0e6, conductivity=2.5)
OCEAN = Thermal(albedo=0.06, emissivity=0.99, capacity=1.0e8, conductivity=0.6)
HULL = Thermal(albedo=0.20, emissivity=0.85, capacity=4.0e4, conductivity=200.0)
RADIATOR = Thermal(albedo=0.10, emissivity=0.92, capacity=1.0e4, conductivity=200.0)


@dataclass
class ThermalField:
    """Temperature, derived from the light field rather than authored.

    THE RULE, and it is the whole of spacecraft thermal engineering: in vacuum there is no
    convection and no conduction to anywhere. A body can shed heat ONLY by radiating it. That is
    why a spaceship's hardest problem is not staying warm -- it is getting RID of heat, and why
    radiators are the biggest surfaces on a real spacecraft.
    """
    light: LightField = dfield(default_factory=LightField)

    def absorbed(self, p, normal, mat: Thermal) -> float:
        """W/m^2 taken in from the star at this point, facing this way."""
        return self.light.irradiance_at(p) * self.light.lit_fraction(p, normal) * (1.0 - mat.albedo)

    def emitted(self, T: float, mat: Thermal) -> float:
        """W/m^2 radiated away at temperature T. The T^4 is the strongest lever in the game."""
        return mat.emissivity * SIGMA * max(T, 0.0) ** 4

    def equilibrium(self, p, normal, mat: Thermal, internal: float = 0.0) -> float:
        """The temperature where absorbed == emitted. Where a surface ENDS UP if you wait."""
        S = self.absorbed(p, normal, mat) + internal
        return float((S / (mat.emissivity * SIGMA)) ** 0.25) if S > 0 else 0.0

    def step(self, T: float, p, normal, mat: Thermal, dt: float, internal: float = 0.0) -> float:
        """One tick of C dT/dt = absorbed - emitted + internal. This is the DAY/NIGHT SWING: at
        night `absorbed` goes to zero, T^4 keeps radiating, and the surface plummets."""
        net = self.absorbed(p, normal, mat) + internal - self.emitted(T, mat)
        return float(T + net * dt / mat.capacity)

    # --- the numbers a ship's computer actually needs ---
    @staticmethod
    def radiator_area(power_W: float, T: float, emissivity: float = 0.92) -> float:
        """How much radiator to dump `power_W` at temperature T. Grows as 1/T^4 -- run the loop
        HOT and the radiator shrinks dramatically, which is why they glow."""
        return float(power_W / (emissivity * SIGMA * T ** 4))

    @staticmethod
    def conduction(mat: Thermal, dT: float, dx: float) -> float:
        """Fourier's law: W/m^2 flowing down a temperature gradient. This is the planet interior
        gradient, and it is also why a metal hull equalises and regolith does not."""
        return float(-mat.conductivity * dT / dx)


# ══════════════════════════════════════════════════════════════════════════════════════════════
#  THE SENSED REGISTER — "what does a ship's computer track? what does a body sense?"
# ══════════════════════════════════════════════════════════════════════════════════════════════
#
# The operator's observation, and it is the right one: a ship's instrument panel and a body's
# senses are THE SAME LIST. Both are readings of fields at a position. So there is no "instrument
# system" to build and no separate "senses system" -- there are FIELDS, and a sensor is a membrane
# port that samples one.
#
# That collapses two subsystems into one, and it means the HUD and the character's perception are
# the same code reading the same numbers. It also means a broken sensor is a real thing: the field
# is still there, you just stopped reading it.
#
# Two entries are NOT fields and are marked so on purpose -- proprioception and the inertial sense
# read the membrane's OWN state, not the universe. That is why you can be blindfolded and still
# know where your arm is, and why an IMU works in a sealed box. It is a genuine category split, and
# quietly filing them under "field" would have been the easy lie.
#
#   name              kind      ship instrument            body sense            status
SENSED = [
    ('gravity',       'field',  'accelerometer / down',    'inner ear (otolith)',    'BUILT gravity.py'),
    ('contact',       'field',  'hull strain / docking',   'touch, pressure, pain',  'BUILT contact.py+here'),
    ('light',         'field',  'star tracker / cameras',  'eyes',                   'BUILT here'),
    ('thermal',       'field',  'hull + reactor temp',     'skin heat and cold',     'BUILT here'),
    ('acoustic',      'field',  'hull vibration',          'ears',                   'DESIGN (sound doc)'),
    ('atmospheric',   'field',  'pressure / composition',  'breath, ear-popping',    'PLANNED'),
    ('fluid',         'field',  'drag / dynamic pressure', 'wind and water on skin', 'PLANNED'),
    ('radiation',     'field',  'dosimeter',               'none -- and that is WHY it is scary',
                                                                                     'PLANNED'),
    ('magnetic',      'field',  'magnetometer / compass',  'none (birds have it)',   'PLANNED (EMField)'),
    ('chemical',      'field',  'mass spectrometer',       'smell and taste',        'DEFERRED by operator'),
    # --- not fields: the membrane reading ITSELF ---
    ('inertial',      'state',  'gyro / IMU',              'vestibular canals',      'BUILT physics.py'),
    ('proprioception', 'state', 'joint / actuator encoders', 'where your limbs are', 'BUILT nervous.py'),
]


def sensed_table() -> str:
    """Print the register. `python -m fields` -- the roadmap for fields, kept next to the code."""
    w = [max(len(str(r[i])) for r in SENSED) for i in range(5)]
    head = ('FIELD/STATE', 'KIND', 'SHIP INSTRUMENT', 'BODY SENSE', 'STATUS')
    w = [max(w[i], len(head[i])) for i in range(5)]
    line = '  '.join('-' * n for n in w)
    out = ['  '.join(h.ljust(w[i]) for i, h in enumerate(head)), line]
    out += ['  '.join(str(c).ljust(w[i]) for i, c in enumerate(r)) for r in SENSED]
    return '\n'.join(out)


if __name__ == '__main__':
    print(sensed_table())
