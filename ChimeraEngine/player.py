"""player.py — SOMETHING THAT STANDS ON A WORLD.

The first thing in this engine that is a PLACE rather than an experiment. It stands on a sphere,
asks gravity which way is up, warms on the sunlit side, and falls over when shoved -- and every one
of those comes from a field that was already built and witnessed, not from new code invented here.

    THE POINT: there is no "player physics". A player is a FloatingTree (S8) with feet (S7) in a
    gravity field (gravity.py) on a body carrying the light, thermal and atmospheric fields
    (fields.py). If standing needed its own special-cased solver, the fields would be wrong.

`World` is a body you can stand on -- ONE membrane carrying every field at once, so "where am I"
answers "what is it like here" without asking six different systems.

`Player.sense()` is the SENSED register (fields.py) made real. The operator's observation was that
a ship's instrument panel and a body's senses are the same list, because both are readings of
fields at a position. This is that list, returned by one call -- so the HUD and the character's
perception are not two systems, they are one function with two consumers.

HONEST SCOPE: this stands, leans, senses and topples. It does NOT walk. Walking is a CONTROLLER
problem, not a physics one -- the body is ready (nervous.py has the machinery, and F6 proved a free
base can be pushed over), but a gait has to be TRAINED against this morphology and this gravity,
and one rollout of one start would be a coin toss. That is the next piece, and it is a training
run, not an afternoon of authoring.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field as dfield
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from contact import ContactModel, Foot, SphereGround, tree_contacts               # noqa: E402
from fields import (SIGMA, Atmosphere, LightField, Occluder, Star, Thermal,       # noqa: E402
                    ThermalField, EARTH_AIR)
from gravity import PointMass                                                     # noqa: E402
from physics import inertia_box, quat_to_mat                                      # noqa: E402
from physics_articulated import rod                                               # noqa: E402
from physics_floating import FloatingTree                                         # noqa: E402


def quat_aligning(a, b) -> np.ndarray:
    """Shortest-arc quaternion (x,y,z,w) rotating unit vector `a` onto unit vector `b`.

    Used to stand a body up in its LOCAL frame. On a sphere there is no global 'upright' to snap
    to -- upright is different at every point, so it has to be built from the two vectors that
    actually matter: the body's own axis, and the up that gravity reports where it is standing.
    """
    a = np.asarray(a, float); a = a / (np.linalg.norm(a) + 1e-15)
    b = np.asarray(b, float); b = b / (np.linalg.norm(b) + 1e-15)
    d = float(np.dot(a, b))
    if d > 1.0 - 1e-12:
        return np.array([0.0, 0.0, 0.0, 1.0])
    if d < -1.0 + 1e-12:                        # antipodal: any perpendicular axis, half turn
        axis = np.cross(a, np.array([1.0, 0.0, 0.0]))
        if np.linalg.norm(axis) < 1e-9:
            axis = np.cross(a, np.array([0.0, 1.0, 0.0]))
        axis /= np.linalg.norm(axis)
        return np.array([axis[0], axis[1], axis[2], 0.0])
    v = np.cross(a, b)
    s = np.sqrt((1.0 + d) * 2.0)
    q = np.array([v[0] / s, v[1] / s, v[2] / s, s * 0.5])
    return q / np.linalg.norm(q)


@dataclass
class World:
    """A body you can stand on: one membrane carrying every field at once.

    This is what `core/membranes.py` means by a boundary supplying a LOCAL frame. Ask it anything
    positional -- up, altitude, sunlight, pressure, ground temperature -- and it answers in terms
    of its own centre, because on a sphere every one of those is different at every point.
    """
    name: str = 'aWorld'
    center: np.ndarray = dfield(default_factory=lambda: np.zeros(3))
    radius: float = 6.371e6
    surface_g: float = 9.80665
    air: Atmosphere = None                       # None == vacuum, and that is a real answer
    surface: Thermal = dfield(default_factory=Thermal)
    star: Star = None
    night_temperature: float = 95.0     # K -- what the DEPTH model holds overnight (D2: the
                                        # Moon sits at ~95 K, not at 0 K as the skin model says)
    _gfield: PointMass = None
    _ground: SphereGround = None
    _light: LightField = None

    def __post_init__(self):
        self.center = np.asarray(self.center, float)
        self._gfield = PointMass.from_surface_g(self.center, self.radius, self.surface_g)
        self._ground = SphereGround(center=self.center, radius=self.radius)
        occ = Occluder(center=self.center, radius=self.radius,
                       albedo=self.surface.albedo, temperature=0.0,
                       emissivity=self.surface.emissivity)
        self._light = LightField(stars=[self.star] if self.star else [], occluders=[occ])

    # --- the fields, answered in world coordinates ---
    def gravity(self) -> PointMass:
        return self._gfield

    def ground(self) -> SphereGround:
        return self._ground

    def light(self) -> LightField:
        return self._light

    def up_at(self, p) -> np.ndarray:
        return self._gfield.up_at(p)

    def altitude(self, p) -> float:
        return float(np.linalg.norm(np.asarray(p, float) - self.center)) - self.radius

    def surface_point(self, lat_deg: float, lon_deg: float, altitude: float = 0.0) -> np.ndarray:
        la, lo = np.radians(lat_deg), np.radians(lon_deg)
        n = np.array([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)])
        return self.center + n * (self.radius + altitude)

    def pressure_at(self, p) -> float:
        return 0.0 if self.air is None else self.air.pressure_at(max(self.altitude(p), 0.0))

    def ground_temperature_at(self, p) -> float:
        """The regolith/soil temperature under a point -- absorbed sunlight balanced against T^4.

        A SKIN model on purpose; `Column` is what you reach for when the DEPTH matters. But the
        skin model's known failure (fields_witness D2) is that with no sun it returns 0 K, and
        nothing in the universe is at absolute zero. `night_temperature` stands in for what the
        depth model gives -- heat conducting up from below all night -- so a point in shadow is
        cold rather than impossible.
        """
        n = np.asarray(p, float) - self.center
        n = n / (np.linalg.norm(n) + 1e-15)
        tf = ThermalField(light=self._light)
        T = tf.equilibrium(p, n, self.surface)
        return T if T > self.night_temperature else self.night_temperature

    def is_sunlit(self, p) -> bool:
        return self._light.irradiance_at(np.asarray(p, float)) > 1.0

    def sunlit_longitude(self, lat_deg: float = 0.0) -> float:
        """WHICH WAY IS THE SUN, in this world's own lat/lon. Ask, never assume.

        I assumed it, got it backwards (the star is at the origin and the world is at +x, so the
        SUNWARD face is lon 180, not lon 0), and a witness confidently reported a suit warming in
        the dark. Same failure as asserting a shadow without building one -- so the code that
        needs a sunlit point now derives it.
        """
        best, bi = 0.0, -1.0
        for lon in range(0, 360, 5):
            i = self._light.irradiance_at(self.surface_point(lat_deg, float(lon), 1.0))
            if i > bi:
                best, bi = float(lon), i
        return best

    @classmethod
    def earth_like(cls, star: Star, center=(0, 0, 0)) -> 'World':
        return cls(name='anEarth', center=center, radius=6.371e6, surface_g=9.80665,
                   air=EARTH_AIR, star=star, night_temperature=275.0,
                   surface=Thermal(albedo=0.30, emissivity=0.95, capacity=2.0e6,
                                   conductivity=2.5, density=2700.0, specific_heat=800.0))

    @classmethod
    def moon_like(cls, star: Star, center=(0, 0, 0)) -> 'World':
        from fields import LUNAR_REGOLITH
        return cls(name='aMoon', center=center, radius=1.737e6, surface_g=1.62,
                   air=None, star=star, surface=LUNAR_REGOLITH, night_temperature=95.0)

    @classmethod
    def asteroid(cls, star: Star, center=(0, 0, 0), radius=500.0, g=0.0028) -> 'World':
        from fields import LUNAR_REGOLITH
        return cls(name='aRock', center=center, radius=radius, surface_g=g,
                   air=None, star=star, surface=LUNAR_REGOLITH)


# Suit: what a person is wearing, thermally. High capacity so it does not track the ground
# instantly -- a body has thermal inertia, which is why you can cross a terminator and survive it.
SUIT = Thermal(albedo=0.20, emissivity=0.88, capacity=6.0e4, conductivity=0.05)


@dataclass
class Player:
    """A body standing on a World. Composition, not a new physics."""
    world: World
    body: FloatingTree
    feet: list = dfield(default_factory=list)
    contact: ContactModel = None
    skin_T: float = 293.15                 # K, the suit's outer surface
    suit: Thermal = dfield(default_factory=lambda: SUIT)
    metabolic_W: float = 120.0             # a resting human, W/m^2 of suit -- you are a heater

    STAND_H = 0.28                         # base origin height when the pads are resting

    @classmethod
    def build(cls, world: World, lat_deg=0.0, lon_deg=0.0, altitude=0.0,
              mass=70.0) -> 'Player':
        """Stand a body on the world at a latitude and longitude, upright in the LOCAL frame."""
        ext = np.array([0.30, 0.20, 0.50])
        links = [rod('armL', 2.0, 0.34, anchor=(0.0, 0.10, 0.20), axis=(0, 1, 0), parent=-1),
                 rod('armR', 2.0, 0.34, anchor=(0.0, -0.10, 0.20), axis=(0, 1, 0), parent=-1)]
        torso = mass - sum(L.mass for L in links)
        p = world.surface_point(lat_deg, lon_deg, altitude + cls.STAND_H)
        up = world.up_at(p)
        b = FloatingTree(base_mass=torso, base_inertia=inertia_box(torso, ext),
                         base_com=(0.0, 0.0, 0.0), links=links,
                         gravity=world.gravity(), base_pos=p,
                         base_quat=quat_aligning(np.array([0.0, 0.0, 1.0]), up))
        b.base_rot = quat_to_mat(b.base_quat)
        feet = [Foot(link=-1, at=(sx * 0.12, sy * 0.09, -0.25), radius=0.03, name=f'pad{i}')
                for i, (sx, sy) in enumerate([(1, 1), (1, -1), (-1, 1), (-1, -1)])]
        model = ContactModel(k=3.0e5, zeta=5.0e3, mu=0.9, v_eps=2e-5)
        return cls(world=world, body=b, feet=feet, contact=model)

    # ── state ────────────────────────────────────────────────────────────────────────────────
    def position(self) -> np.ndarray:
        return self.body.base_pos

    def up(self) -> np.ndarray:
        return self.body.up()

    def tilt_deg(self) -> float:
        return self.body.tilt_deg()

    def altitude(self) -> float:
        return self.world.altitude(self.body.base_pos)

    def local_frame(self):
        """(east, north, up) where the player is standing -- the frame a HUD horizon needs."""
        up = self.up()
        ref = np.array([0.0, 0.0, 1.0])
        if abs(float(np.dot(ref, up))) > 0.95:
            ref = np.array([1.0, 0.0, 0.0])
        east = np.cross(ref, up); east /= (np.linalg.norm(east) + 1e-15)
        north = np.cross(up, east)
        return east, north, up

    # ── the loop ─────────────────────────────────────────────────────────────────────────────
    def step(self, dt: float, extra_forces=None, thermal_dt: float = None) -> list:
        f, info = tree_contacts(self.body, self.feet, self.world.ground(), self.contact)
        if extra_forces:
            f = f + list(extra_forces)
        self.body.step(dt, extra_forces=f)
        self.step_thermal(thermal_dt if thermal_dt is not None else dt)
        return info

    def step_thermal(self, dt: float) -> float:
        """The suit's own heat balance: sun in, ground glow in, your own metabolism in, sigma T^4
        out. All three inputs come from the light field -- none of them are a player stat."""
        p = self.body.base_pos
        n = self.up()
        lf = self.world.light()
        tf = ThermalField(light=lf)
        solar = tf.absorbed(p, n, self.suit)
        Tg = self.world.ground_temperature_at(p)
        ground = self.suit.emissivity * SIGMA * Tg ** 4 * 0.5      # half your sky is ground
        out = self.suit.emissivity * SIGMA * max(self.skin_T, 0.0) ** 4
        net = solar + ground + self.metabolic_W - out
        self.skin_T = float(self.skin_T + net * dt / self.suit.capacity)
        return self.skin_T

    def footing(self) -> int:
        _, info = tree_contacts(self.body, self.feet, self.world.ground(), self.contact)
        return sum(1 for c in info if c['touching'])

    def load_N(self) -> float:
        _, info = tree_contacts(self.body, self.feet, self.world.ground(), self.contact)
        return float(sum(c['Fn'] for c in info if c['touching']))

    # ── THE SENSED REGISTER, made real ───────────────────────────────────────────────────────
    def sense(self) -> dict:
        """Every field this body can read, at one position, from one call.

        A ship's instrument panel and a body's senses are the same list -- so the HUD and the
        character's perception are not two systems. Note what is NOT a field here: `inertial` and
        `proprioception` read the body's OWN state, which is why you know where your arm is with
        your eyes shut and why an IMU works in a sealed box.
        """
        p, up = self.body.base_pos, self.up()
        lf = self.world.light()
        g = self.world.gravity().at(p)
        _, info = tree_contacts(self.body, self.feet, self.world.ground(), self.contact)
        irr = lf.irradiance_at(p)
        sun = lf.direction_at(p)
        press = self.world.pressure_at(p)
        return {
            'gravity': {'up': up, 'strength': float(np.linalg.norm(g)),
                        'weight_N': float(np.linalg.norm(g)) * self.body.total_mass()},
            'contact': {'feet_down': sum(1 for c in info if c['touching']),
                        'load_N': float(sum(c['Fn'] for c in info if c['touching'])),
                        'grounded': any(c['touching'] for c in info)},
            'light': {'irradiance': float(irr), 'is_day': bool(irr > 1.0),
                      'sun_elevation_deg': (float(np.degrees(np.arcsin(
                          np.clip(float(np.dot(up, sun)), -1, 1)))) if sun is not None else None)},
            'thermal': {'skin_K': float(self.skin_T),
                        'ground_K': float(self.world.ground_temperature_at(p))},
            'atmospheric': {'pressure_Pa': float(press),
                            'breathable': bool(self.world.air is not None
                                               and press * self.world.air.o2_fraction > 16000.0)},
            'inertial': {'speed': float(np.linalg.norm(self.body.v_base)),
                         'tilt_deg': self.tilt_deg(),
                         'spin_rate': float(np.linalg.norm(self.body.w_base))},
            'proprioception': {'joints_rad': self.body.q.copy(),
                               'joint_rates': self.body.qd.copy()},
        }
