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

    def surface_temperature(self) -> float:
        """The star's own surface temperature, from L = 4 pi R^2 sigma T^4.

        THE UNIFICATION, in one line: a star is not a special kind of object, it is a body at a
        temperature. Run the Sun's luminosity and radius through the SAME Stefan-Boltzmann law that
        settles a patch of regolith and you get 5772 K -- its measured effective temperature. Star
        and dirt are the same equation at different arguments."""
        return float((self.luminosity / (4.0 * np.pi * self.radius ** 2 * SIGMA)) ** 0.25)


@dataclass
class Occluder:
    """A body that casts a shadow -- and REFLECTS, and GLOWS.

    A planet eclipsing its own night side is the same object as a moon eclipsing a planet:
    day/night and eclipse are ONE mechanism. And the same body is also a light SOURCE twice over:

      REFLECTED   the `albedo` fraction of starlight it bounces back out. My first version threw
                  this away -- `absorbed = S (1-albedo)` used the absorbed part and let the
                  reflected part vanish. It does not vanish. It lands on you. (Operator, 2026-07-26:
                  "light reflecting off an object has property of thermal".)
      EMITTED     everything above 0 K radiates at sigma T^4. That IS light -- just further down
                  the spectrum. A star is a body at 5772 K; regolith at noon is a body at 390 K;
                  the law does not care which.

    So `temperature` is not bookkeeping here, it is what makes the body shine.
    """
    center: np.ndarray = dfield(default_factory=lambda: np.zeros(3))
    radius: float = 1.0
    albedo: float = 0.0                # 0 => a black body that only blocks (the old behaviour)
    temperature: float = 0.0           # K; 0 => emits nothing
    emissivity: float = 0.95

    def __post_init__(self):
        self.center = np.asarray(self.center, float)

    def view_factor(self, p) -> float:
        """How much of your sky this body FILLS, from a point facing it.

        For a flat element facing a sphere's centre this is exactly (R/r)^2 -- the sphere subtends
        a half-angle with sin(theta) = R/r, and the view factor is sin^2(theta). It goes to 1 on
        the surface (lying on the ground, the ground is your whole sky) and falls off with altitude,
        which is why a low orbit is thermally a completely different place from a high one.
        """
        r = float(np.linalg.norm(np.asarray(p, float) - self.center))
        if r <= self.radius:
            return 1.0
        return float((self.radius / r) ** 2)

    def emitted_flux_at(self, p) -> float:
        """W/m^2 of the body's OWN thermal radiation arriving at p. Never zero on the night side --
        which is exactly why it is the term you cannot hide from."""
        if self.temperature <= 0.0:
            return 0.0
        return float(self.emissivity * SIGMA * self.temperature ** 4 * self.view_factor(p))

    def reflected_flux_at(self, p, star) -> float:
        """W/m^2 of STARLIGHT this body bounces up at p. Zero over the night side, peak over the
        sub-stellar point -- planetshine, and a real term in every spacecraft's heat budget."""
        if self.albedo <= 0.0:
            return 0.0
        d = np.asarray(p, float) - self.center
        r = float(np.linalg.norm(d))
        if r < 1e-9:
            return 0.0
        to_star = star.center - self.center
        n = float(np.linalg.norm(to_star))
        if n < 1e-9:
            return 0.0
        lit = max(0.0, float(np.dot(d / r, to_star / n)))       # 1 sub-stellar, 0 at the terminator
        return float(self.albedo * star.irradiance_at(self.center) * lit * self.view_factor(p))

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

    def budget_at(self, p, facing_body=True) -> dict:
        """THE FULL RADIATIVE BUDGET at a point -- every watt arriving, and where it came from.

        Three terms, and a real spacecraft's thermal design is the argument between them:
            direct    starlight, if you can see the star
            albedo    starlight the body below bounced up at you. Dies on the night side.
            planetary the body's OWN glow at sigma T^4. Does NOT die on the night side, which is
                      why you can never fully cool by hiding -- you have to point AWAY.

        `facing_body=False` is a surface pointed at deep space instead of down: it drops both
        surface terms, which is exactly what a radiator is for and why they are mounted where they
        are. Deep space is 2.7 K -- effectively a perfect heat sink, and the only one there is.

        DO NOT feed this to a Column for the ground it is standing on. This is what arrives at a
        body ABOVE a surface -- a suit, a rover, a ship. A patch of ground would be counting its
        own glow as incoming and heating itself forever.
        """
        direct = self.irradiance_at(p)
        alb = ir = 0.0
        if facing_body:
            for o in self.occluders:
                ir += o.emitted_flux_at(p)
                for s in self.stars:
                    if not any(q.blocks(o.center, s.center) for q in self.occluders if q is not o):
                        alb += o.reflected_flux_at(p, s)
        return {'direct': float(direct), 'albedo': float(alb), 'planetary': float(ir),
                'total': float(direct + alb + ir)}

    def total_irradiance_at(self, p, facing_body=True) -> float:
        return self.budget_at(p, facing_body)['total']

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
    """A material's thermal character.

    `capacity` (J/m^2/K) is the SKIN model: how much heat one square metre of surface can bank
    before the sun goes down. It is enough for a hull or a radiator, and it is what T2/T3 use.

    `density` / `specific_heat` / `conductivity` are the DEPTH model: with those three a material
    stops being a surface and becomes a COLUMN, heat diffuses down and comes back, and the night
    side stops being wrong. See `Column` below for why that matters.

    `radiative_chi` is the piece that makes regolith regolith: in a vacuum, powder conducts partly
    by INFRARED EXCHANGE ACROSS THE PORES between grains, which scales as T^3. So lunar soil
    conducts several times better at noon than at midnight -- k(T) = k_c * (1 + chi (T/350)^3),
    the Diviner/Hayne form. Set it to 0 for a solid.
    """
    albedo: float = 0.3               # fraction of light reflected, never absorbed
    emissivity: float = 0.95          # how well it radiates -- near 1 for rock, low for polished metal
    capacity: float = 3.2e4           # J/m^2/K -- skin model only
    conductivity: float = 1.0         # W/m/K  -- k_c, the CONTACT conductivity at 350 K
    density: float = 1500.0           # kg/m^3
    specific_heat: float = 600.0      # J/kg/K
    radiative_chi: float = 0.0        # T^3 pore-radiation term; ~2.7 for lunar regolith

    def volumetric_capacity(self) -> float:
        return self.density * self.specific_heat            # J/m^3/K

    def conductivity_at(self, T):
        """k(T). Constant for a solid; strongly temperature-dependent for a vacuum powder."""
        if self.radiative_chi == 0.0:
            return self.conductivity
        return self.conductivity * (1.0 + self.radiative_chi * (np.asarray(T) / 350.0) ** 3)

    def diffusivity(self, T: float = 250.0) -> float:
        """alpha = k / (rho c), m^2/s. How fast a temperature CHANGE travels, not how much heat."""
        return float(np.mean(self.conductivity_at(T))) / self.volumetric_capacity()

    def skin_depth(self, period: float, T: float = 250.0) -> float:
        """delta = sqrt(alpha P / pi) -- the depth where the daily swing has fallen to 1/e.

        THE NUMBER A GAME WANTS. Below a few of these the temperature simply stops changing, which
        is why you bury a habitat, why lunar cold traps hold ice, and why 'dig down' is a real
        strategy rather than a flavour text."""
        return float(np.sqrt(self.diffusivity(T) * period / np.pi))

    def inertia(self, T: float = 250.0) -> float:
        """I = sqrt(k rho c) -- the standard thermophysical measure, J m^-2 K^-1 s^-1/2. It is what
        remote sensing actually retrieves, and it sorts every surface in the solar system."""
        return float(np.sqrt(np.mean(self.conductivity_at(T)) * self.volumetric_capacity()))


# k_c, rho, c, chi for regolith follow Hayne et al. 2017 (Diviner) to within the single-layer
# approximation this makes -- the real Moon's density and conductivity both rise with depth.
LUNAR_REGOLITH = Thermal(albedo=0.11, emissivity=0.95, capacity=3.2e4,
                         conductivity=7.4e-4, density=1300.0, specific_heat=600.0,
                         radiative_chi=2.7)
ROCK_T = Thermal(albedo=0.25, emissivity=0.95, capacity=2.0e6,
                 conductivity=2.5, density=2700.0, specific_heat=800.0)
OCEAN = Thermal(albedo=0.06, emissivity=0.99, capacity=1.0e8,
                conductivity=0.6, density=1000.0, specific_heat=4184.0)
HULL = Thermal(albedo=0.20, emissivity=0.85, capacity=4.0e4,
               conductivity=200.0, density=2700.0, specific_heat=900.0)
RADIATOR = Thermal(albedo=0.10, emissivity=0.92, capacity=1.0e4,
                   conductivity=200.0, density=2700.0, specific_heat=900.0)
ICE = Thermal(albedo=0.60, emissivity=0.97, capacity=1.0e6,
              conductivity=2.2, density=920.0, specific_heat=2050.0)


@dataclass
class Column:
    """A stack of layers under one square metre of ground -- the DEPTH DIMENSION.

    The skin model gets the day side right and the night side badly wrong, because it lets the
    surface radiate into space with nothing underneath to resupply it. Real ground has a reservoir:
    heat soaks DOWN through the day and comes back UP all night. That is the whole difference, and
    it is why the Moon holds ~95 K at midnight instead of collapsing toward zero.

    Layers grow geometrically -- fine at the top where the gradient is steep, coarse below where
    nothing happens. That is not an optimisation, it is the only way to resolve a 2 mm skin and a
    2 m reservoir in the same array.
    """
    mat: Thermal
    dz: np.ndarray                      # layer thicknesses, m (top first)
    T: np.ndarray                       # layer temperatures, K
    geothermal: float = 0.018           # W/m^2 from below. The Moon's own, measured by the Apollo
                                        # 15/17 heat flow experiments (~16-21 mW/m^2).

    @classmethod
    def build(cls, mat: Thermal, n: int = 24, dz0: float = 0.002, growth: float = 1.25,
              T0: float = 250.0, geothermal: float = 0.018) -> 'Column':
        """`T0` is the MEAN SURFACE temperature; the deep layers start on the steady-state
        geothermal gradient rather than uniform.

        That is not a nicety. Heat from below takes L^2/alpha to establish its gradient -- through
        2.6 m of regolith that is about 117 YEARS, so a column started uniform still has its
        initial condition sitting in the deep layers after any simulation you would actually run,
        and Fourier's law cannot be read out of it. Real ground has had four billion years.
        """
        dz = dz0 * growth ** np.arange(n)
        T = np.full(n, float(T0))
        for i in range(1, n):
            k_i = float(np.mean(np.atleast_1d(mat.conductivity_at(T[i - 1]))))
            T[i] = T[i - 1] + geothermal * 0.5 * (dz[i - 1] + dz[i]) / k_i
        return cls(mat=mat, dz=dz, T=T, geothermal=geothermal)

    def depth(self) -> float:
        return float(self.dz.sum())

    def depths(self) -> np.ndarray:
        """Depth of each layer's CENTRE, m."""
        return np.cumsum(self.dz) - self.dz * 0.5

    def max_dt(self) -> float:
        """The explicit-diffusion stability limit, dz^2 / (2 alpha), on the THINNEST layer. Exceed
        it and the column oscillates and blows up -- silently, and looking like weather."""
        a = float(np.max(self.mat.conductivity_at(self.T))) / self.mat.volumetric_capacity()
        return float(self.dz[0] ** 2 / (2.0 * a))

    def step(self, dt: float, absorbed: float, internal: float = 0.0) -> float:
        """Advance one tick. `absorbed` is W/m^2 arriving at the surface. Returns surface T."""
        k = np.atleast_1d(self.mat.conductivity_at(self.T))
        if k.size == 1:
            k = np.full(self.T.shape, float(k))
        # Conductance across each interface: harmonic mean over the two half-thicknesses. The
        # harmonic mean is not fussiness -- an arithmetic one lets a thin conductive layer
        # short-circuit a thick insulating one, which is exactly backwards.
        h = 2.0 * k[:-1] * k[1:] / (k[:-1] * self.dz[1:] + k[1:] * self.dz[:-1])
        q = h * (self.T[:-1] - self.T[1:])                  # W/m^2, positive = flowing DOWN
        net = np.empty_like(self.T)
        surf_out = self.mat.emissivity * SIGMA * max(self.T[0], 0.0) ** 4
        net[0] = absorbed + internal - surf_out - q[0]
        net[1:-1] = q[:-1] - q[1:]
        net[-1] = q[-1] + self.geothermal                   # the deep boundary is a FLUX, not a
        self.T = self.T + net * dt / (self.mat.volumetric_capacity() * self.dz)   # pinned value
        return float(self.T[0])


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
