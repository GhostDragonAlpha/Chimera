"""CHIMERA_VISION.py — THE ULTIMATE PSEUDOCODE. One file. The entire game.

CHIMERA: a generational, wordless, embodied life on a regolith planetoid in
cislunar deep space, where Earth and Moon both hang in the sky, every finished
life becomes a star whose brightness equals what that life SACRIFICED, and the
bad ending is not death — it is a COSTLESS LIFE (a dim star, and the Erisaid's
mirror showing nothing).

DESIGN LAWS
  1. The world answers the body. Every verb produces a physical, audible,
     visible change (footprint, dust, sound, heat). No abstract clicks.
  2. The bad ending is a costless life. Meaning = what you gave up. The game
     NEVER explains this; it is taught only through consequence.
  3. Wordless. No dialogue text. Gestures, objects, sounds, and light.
  4. Nothing observed is lost. Footprints, dug pits, shelters, and debts of
     kindness persist across generations. Unobserved space stays uncollapsed.
  5. The player is the trunk. All content generates outward from the player
     along the golden-angle spiral, at every scale.

This file is executable pseudocode: pure stdlib Python, headless-simulatable.
Every class maps 1:1 onto a UE5.8 C++ class under Source/Chimera/ (comments
mark the mapping). A later, smaller AI ports and debugs it. Numbers here are
the tuning truth.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Optional

# =============================================================================
# 0. MATH & NOISE (UE5: FMath / FVector / material noise nodes)
# =============================================================================

GOLDEN_ANGLE_DEG = 137.50776405003785  # phyllotaxis; the generation law
TAU = math.tau


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * clamp(t, 0.0, 1.0)


def smoothstep(e0: float, e1: float, x: float) -> float:
    t = clamp((x - e0) / (e1 - e0 + 1e-9), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _hash2(ix: int, iy: int, seed: int) -> float:
    """Deterministic value in [0,1) for integer lattice point."""
    h = (ix * 374761393 + iy * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65536.0


def value_noise2(x: float, y: float, seed: int = 0) -> float:
    """Bilinear value noise in [0,1). UE5: Material 'Noise' node, Value mode."""
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    a = _hash2(ix, iy, seed)
    b = _hash2(ix + 1, iy, seed)
    c = _hash2(ix, iy + 1, seed)
    d = _hash2(ix + 1, iy + 1, seed)
    ux, uy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    return lerp(lerp(a, b, ux), lerp(c, d, ux), uy)


def fbm2(x: float, y: float, octaves: int = 4, seed: int = 0) -> float:
    """Fractal Brownian motion, [0,1)."""
    total, amp, freq, norm = 0.0, 1.0, 1.0, 0.0
    for i in range(octaves):
        total += amp * value_noise2(x * freq, y * freq, seed + i)
        norm += amp
        amp *= 0.5
        freq *= 2.0
    return total / norm


@dataclass
class V3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __add__(self, o: "V3") -> "V3":
        return V3(self.x + o.x, self.y + o.y, self.z + o.z)

    def __sub__(self, o: "V3") -> "V3":
        return V3(self.x - o.x, self.y - o.y, self.z - o.z)

    def __mul__(self, s: float) -> "V3":
        return V3(self.x * s, self.y * s, self.z * s)

    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def length2d(self) -> float:
        return math.hypot(self.x, self.y)

    def normalized(self) -> "V3":
        l = self.length()
        return V3(self.x / l, self.y / l, self.z / l) if l > 1e-9 else V3()


def spiral_point(index: int, spacing: float = 8.0) -> V3:
    """Golden-angle phyllotaxis: the i-th thing the world grows around the
    player-trunk. Used for buried caches, dots' arrival bearings, station
    layout, asteroid fields — EVERY scale (Design Law 5)."""
    r = spacing * math.sqrt(index + 1)
    a = math.radians(GOLDEN_ANGLE_DEG) * index
    return V3(r * math.cos(a), r * math.sin(a), 0.0)


# =============================================================================
# 1. GLOBAL TUNING TABLES (the numbers are the design)
# =============================================================================

GRAVITY_YARD = 1.62          # m/s^2 — lunar-class planetoid (the Yard)
GRAVITY_TITAN_ZONE = 1.35    # m/s^2 — Titan Run anomaly corridors
GRAVITY_EARTH = 9.81         # reference only (heirloom gyroscope points home)

DAY_LENGTH_HOURS = 27.0      # one Yard day; long dusks
NIGHT_TEMP_C = -140.0
DAY_TEMP_C = 45.0

MOVE = dict(
    walk_speed=1.4,          # m/s
    jog_speed=3.2,
    sprint_speed=5.6,        # bounding low-g lope
    bend_speed=0.7,          # crouched shuffle
    accel=6.0,               # m/s^2 ground accel
    friction_sand=4.5,
    friction_rock=8.0,
    friction_metal=6.5,
    jump_height=1.1,         # m (low-g: slow, floaty apex)
    air_control=0.35,
    coyote_time_s=0.12,      # input forgiveness (curriculum: middle school)
    jump_buffer_s=0.15,
    step_interval_walk_s=0.62,   # cadence — drives footstep AV sync
    step_interval_sprint_s=0.38,
    basin_sink_depth=0.22,   # m — soft sand basins swallow boots
    slide_slope_deg=38.0,
)

SUIT = dict(
    o2_max=100.0,            # units; 1u ≈ 1 min calm breathing
    o2_drain_idle=0.6,       # u/min
    o2_drain_walk=1.0,
    o2_drain_sprint=3.0,
    o2_drain_dig=2.2,
    battery_max=100.0,
    battery_drain_night=1.8,     # u/min heater load at night
    battery_drain_scanner=0.5,   # per ping
    thermal_safe_lo=-20.0,
    thermal_safe_hi=60.0,
    dust_clog_max=100.0,     # visor+joint clogging; cleaned at shelter
    dust_clog_per_storm_min=4.0,
    dust_clog_move_penalty=0.35,  # max speed penalty at full clog
    low_o2_warning=25.0,     # suit hum changes pitch — diegetic warning
)

# Dust accumulation mask (the researched material): accumulation grows on
# up-facing, sheltered surfaces over time; wind scours exposed ones.
# UE5: material function DustMask = saturate(normal.z) * crevice_noise * age
DUST_MASK = dict(
    normal_up_power=2.0,       # saturate(dot(N, up))^power
    crevice_noise_scale=0.13,  # fbm2 world-space scale (1/m)
    crevice_octaves=4,
    growth_per_hour=0.02,      # mask units/hour on still surfaces
    wind_scour_per_hour=0.10,  # removal at wind > scour threshold
    scour_wind_threshold=9.0,  # m/s
    max_accumulation=1.0,
)

WIND = dict(
    calm=2.0, breeze=6.0, gust=12.0, storm=24.0,   # m/s bands
    gust_period_s=(8.0, 30.0),                      # random gust cadence
    storm_duration_min=(18.0, 45.0),
    storm_period_days=(5.0, 9.0),                   # ~weekly memento mori
    storm_erases_footprints=True,
    storm_buries_shallow_items=True,
)

STAR = dict(
    brightness_k=6.0,         # brightness = 1 - exp(-sacrifice_weight / k)
    dim_threshold=0.08,       # below this the star "barely registers"
    bright_lights_yard=0.75,  # above this: star literally lights the night
    twinkle_from_open_pains=True,   # unresolved regrets make the star flicker
)

ERISAID = dict(
    hum_base_hz=41.0,                     # felt more than heard
    harmonics=(1.0, 2.667, 4.333),        # ratios; dial must match all three
    dial_tolerance_hz=0.8,
    attune_visits_min=3,                  # cannot be done in one sitting
    deaf_seasons_after_gunfire=1,         # firing a weapon nearby silences it
    mirror_reveal_radius_m=3.0,
)

TITAN_RUN = dict(
    length_m=2400.0,
    gravity_zones=7,           # alternating 1.62 <-> 1.35 m/s^2 corridors
    zone_transition_s=1.2,     # gravity lerps, never snaps (body readability)
    record_board_at_finish=True,
)


class Surface(Enum):
    SAND = auto()
    ROCK = auto()
    METAL = auto()
    BASIN = auto()     # deep soft sand — sinks, slows, swallows
    ICE = auto()       # polar digs only
    INTERIOR = auto()  # habitat/station floors


SURFACE_TABLE = {
    #             traction  footprint  print_life_s   dust_puff  step_sounds
    Surface.SAND:    (0.75,  True,      None,           1.00, "Fantozzi-Sand"),
    Surface.BASIN:   (0.45,  True,      None,           1.60, "Fantozzi-Sand"),
    Surface.ROCK:    (1.00,  False,     0.0,            0.15, "Fantozzi-Stone"),
    Surface.METAL:   (0.90,  True,      600.0,          0.05, "Metal-Scuff"),
    Surface.ICE:     (0.35,  False,     0.0,            0.02, "Ice-Crunch"),
    Surface.INTERIOR:(1.00,  False,     0.0,            0.00, "Interior-Soft"),
}
# print_life_s None = persists until a storm erases it (Design Law 4).


# =============================================================================
# 2. INPUT & FORGIVENESS (UE5: EnhancedInput; ChimeraMovementComponent)
# =============================================================================

class Verb(Enum):
    LOOK = auto(); STEP = auto(); BEND = auto(); JUMP = auto()
    PICKUP = auto(); DROP = auto(); DIG = auto(); SCAN = auto()
    USE = auto(); PLACE = auto(); GESTURE = auto(); FIRE = auto()
    ATTUNE = auto()   # radio dial — the Erisaid minigame


@dataclass
class InputState:
    """Buffered, forgiving input. Every press is timestamped so late/early
    presses inside the buffer window still count (coyote + jump buffer)."""
    move: V3 = field(default_factory=V3)          # stick, |v|<=1
    look_yaw: float = 0.0
    look_pitch: float = 0.0
    pressed: dict = field(default_factory=dict)   # Verb -> press time
    held: set = field(default_factory=set)

    def press(self, verb: Verb, now: float) -> None:
        self.pressed[verb] = now
        self.held.add(verb)

    def release(self, verb: Verb) -> None:
        self.held.discard(verb)

    def consume(self, verb: Verb, now: float, buffer_s: float) -> bool:
        t = self.pressed.get(verb)
        if t is not None and now - t <= buffer_s:
            del self.pressed[verb]
            return True
        return False


# =============================================================================
# 3. THE GROUND (Loop 1) — surfaces, footprints, dust, digging heightfield
# UE5: GroundField -> landscape layers; Footprints -> decal pool;
#      DustFX -> Niagara (SandDrift_FX, DustPuff_FX); DigGrid -> RVT height
# =============================================================================

@dataclass
class Footprint:
    pos: V3
    yaw: float
    surface: Surface
    left_foot: bool
    born_at: float
    generation: int      # WHOSE life left it — prints outlive their maker


class GroundField:
    """Authored pads + noise: sand yard around origin, rock ridge NE,
    three metal work-pads, a soft basin SW, ice at the far pole dig."""

    def __init__(self, seed: int):
        self.seed = seed

    def surface_at(self, p: V3) -> Surface:
        if p.length2d() > 90.0 and fbm2(p.x * 0.01, p.y * 0.01, 3, self.seed) > 0.62:
            return Surface.ROCK                       # ridge country
        for i in range(3):                            # metal pads on spiral
            pad = spiral_point(i * 5 + 4, spacing=14.0)
            if (p - pad).length2d() < 6.0:
                return Surface.METAL
        basin = V3(-42.0, -35.0, 0.0)
        if (p - basin).length2d() < 18.0:
            return Surface.BASIN
        return Surface.SAND

    def height_at(self, p: V3) -> float:
        dune = fbm2(p.x * 0.02, p.y * 0.02, 4, self.seed) * 2.2
        ridge = 0.0
        if self.surface_at(p) == Surface.ROCK:
            ridge = fbm2(p.x * 0.05, p.y * 0.05, 5, self.seed + 7) * 6.0
        return dune + ridge

    def traction_at(self, p: V3) -> float:
        return SURFACE_TABLE[self.surface_at(p)][0]


class FootprintLedger:
    """Persistent across generations. Storms erase sand prints (only sand)."""
    MAX_PRINTS = 4096

    def __init__(self):
        self.prints: list[Footprint] = []

    def stamp(self, pos: V3, yaw: float, surface: Surface, left: bool,
              now: float, generation: int) -> Optional[Footprint]:
        makes_print = SURFACE_TABLE[surface][1]
        if not makes_print:
            return None
        fp = Footprint(pos, yaw, surface, left, now, generation)
        self.prints.append(fp)
        if len(self.prints) > self.MAX_PRINTS:
            self.prints.pop(0)
        return fp

    def storm_erase(self) -> int:
        before = len(self.prints)
        self.prints = [f for f in self.prints if f.surface == Surface.METAL]
        return before - len(self.prints)   # metal scuffs survive weather


@dataclass
class DustPuff:
    pos: V3
    scale: float     # from SURFACE_TABLE puff * speed
    born_at: float


class DustFX:
    """Every footfall and every dig emits a puff; wind advects a drift field.
    UE5: Niagara DustPuff_FX (burst), SandDrift_FX (ambient, wind-driven)."""

    def __init__(self):
        self.puffs: list[DustPuff] = []
        self.accumulation_age_h: float = 0.0   # feeds DUST_MASK age term

    def footfall(self, pos: V3, surface: Surface, speed: float, now: float) -> DustPuff:
        base = SURFACE_TABLE[surface][3]
        puff = DustPuff(pos, base * clamp(speed / MOVE["sprint_speed"], 0.2, 1.0), now)
        self.puffs.append(puff)
        return puff

    def tick(self, hours: float, wind_speed: float) -> None:
        if wind_speed >= DUST_MASK["scour_wind_threshold"]:
            self.accumulation_age_h = max(
                0.0, self.accumulation_age_h
                - DUST_MASK["wind_scour_per_hour"] / DUST_MASK["growth_per_hour"] * hours)
        else:
            self.accumulation_age_h += hours
        self.puffs = self.puffs[-256:]

    def mask_value(self, normal_z: float, world_x: float, world_y: float) -> float:
        """THE dust-accumulation material, as math (port to material graph)."""
        up = clamp(normal_z, 0.0, 1.0) ** DUST_MASK["normal_up_power"]
        crev = fbm2(world_x * DUST_MASK["crevice_noise_scale"],
                    world_y * DUST_MASK["crevice_noise_scale"],
                    DUST_MASK["crevice_octaves"], seed=99)
        age = clamp(self.accumulation_age_h * DUST_MASK["growth_per_hour"], 0.0,
                    DUST_MASK["max_accumulation"])
        return clamp(up * (0.4 + 0.6 * crev) * age, 0.0, 1.0)


class DigGrid:
    """Sparse heightfield deltas from shovel work. Pits persist forever
    (Design Law 4) — a generation can dig a trench its heirs inherit."""
    CELL = 0.5   # m

    def __init__(self):
        self.delta: dict[tuple, float] = {}     # (ix,iy) -> dz (negative=pit)
        self.buried: dict[tuple, list] = {}     # (ix,iy) -> [BuriedItem]

    def key(self, p: V3) -> tuple:
        return (math.floor(p.x / self.CELL), math.floor(p.y / self.CELL))

    def dig(self, p: V3, radius: float, scoop_depth: float) -> list:
        """Lower terrain, return anything uncovered."""
        found = []
        cells = int(radius / self.CELL) + 1
        k0 = self.key(p)
        for dx in range(-cells, cells + 1):
            for dy in range(-cells, cells + 1):
                k = (k0[0] + dx, k0[1] + dy)
                self.delta[k] = self.delta.get(k, 0.0) - scoop_depth
                depth_here = -self.delta[k]
                for item in list(self.buried.get(k, [])):
                    if item.depth <= depth_here:
                        self.buried[k].remove(item)
                        found.append(item)
        return found

    def bury(self, p: V3, item: "BuriedItem") -> None:
        self.buried.setdefault(self.key(p), []).append(item)

    def depth_at(self, p: V3) -> float:
        return -self.delta.get(self.key(p), 0.0)


# =============================================================================
# 4. THE PLAYER (Loop 0) — body, suit, movement, camera
# UE5: AChimeraCharacter + ChimeraMovementComponent + USuitComponent
# =============================================================================

class Gait(Enum):
    IDLE = auto(); WALK = auto(); JOG = auto(); SPRINT = auto(); BEND = auto()


@dataclass
class SuitState:
    o2: float = SUIT["o2_max"]
    battery: float = SUIT["battery_max"]
    dust_clog: float = 0.0
    temperature_c: float = 20.0
    integrity: float = 100.0     # punctures leak o2

    def o2_drain_rate(self, gait: Gait, digging: bool) -> float:
        if digging:
            return SUIT["o2_drain_dig"]
        return {Gait.IDLE: SUIT["o2_drain_idle"], Gait.WALK: SUIT["o2_drain_walk"],
                Gait.JOG: SUIT["o2_drain_walk"] * 1.6, Gait.BEND: SUIT["o2_drain_walk"],
                Gait.SPRINT: SUIT["o2_drain_sprint"]}[gait]

    def tick(self, minutes: float, gait: Gait, is_night: bool, digging: bool,
             in_storm: bool) -> None:
        leak = 1.0 + (100.0 - self.integrity) * 0.02
        self.o2 = max(0.0, self.o2 - self.o2_drain_rate(gait, digging) * minutes * leak)
        if is_night:
            self.battery = max(0.0, self.battery - SUIT["battery_drain_night"] * minutes)
        if in_storm:
            self.dust_clog = min(SUIT["dust_clog_max"],
                                 self.dust_clog + SUIT["dust_clog_per_storm_min"] * minutes)

    @property
    def suffocating(self) -> bool:
        return self.o2 <= 0.0

    @property
    def frozen(self) -> bool:
        return self.battery <= 0.0 and self.temperature_c < SUIT["thermal_safe_lo"]


class Movement:
    """Low-gravity locomotion. Mirrors ChimeraMovementComponent 1:1.
    Emits a footstep event at gait cadence — THE audio-visual sync source."""

    def __init__(self, ground: GroundField):
        self.ground = ground
        self.pos = V3(0.0, 0.0, 0.0)
        self.vel = V3()
        self.yaw = 0.0
        self.gait = Gait.IDLE
        self.grounded = True
        self.left_foot_next = True
        self._step_clock = 0.0
        self._left_ground_at = -999.0
        self.gravity = GRAVITY_YARD
        self.on_footstep: list[Callable] = []   # subscribers: audio, dust, prints

    def max_speed(self, clog: float) -> float:
        base = {Gait.IDLE: 0.0, Gait.WALK: MOVE["walk_speed"],
                Gait.JOG: MOVE["jog_speed"], Gait.SPRINT: MOVE["sprint_speed"],
                Gait.BEND: MOVE["bend_speed"]}[self.gait]
        clog_pen = 1.0 - SUIT["dust_clog_move_penalty"] * (clog / SUIT["dust_clog_max"])
        surf = self.ground.surface_at(self.pos)
        basin_pen = 0.55 if surf == Surface.BASIN else 1.0
        return base * clog_pen * basin_pen

    def choose_gait(self, inp: InputState) -> None:
        mag = inp.move.length2d()
        if Verb.BEND in inp.held:
            self.gait = Gait.BEND
        elif mag < 0.05:
            self.gait = Gait.IDLE
        elif Verb.STEP in inp.held and mag > 0.8:   # STEP held = sprint intent
            self.gait = Gait.SPRINT
        elif mag > 0.55:
            self.gait = Gait.JOG
        else:
            self.gait = Gait.WALK

    def tick(self, dt: float, now: float, inp: InputState, suit: SuitState) -> None:
        self.choose_gait(inp)
        self.yaw += inp.look_yaw * dt
        # --- planar accel toward stick, surface-scaled friction
        want = inp.move * self.max_speed(suit.dust_clog)
        traction = self.ground.traction_at(self.pos)
        blend = clamp(MOVE["accel"] * traction * dt, 0.0, 1.0)
        self.vel.x = lerp(self.vel.x, want.x, blend)
        self.vel.y = lerp(self.vel.y, want.y, blend)
        # --- jump: buffered press + coyote window (forgiveness)
        can_coyote = (now - self._left_ground_at) <= MOVE["coyote_time_s"]
        if (self.grounded or can_coyote) and inp.consume(Verb.JUMP, now, MOVE["jump_buffer_s"]):
            self.vel.z = math.sqrt(2.0 * self.gravity * MOVE["jump_height"])
            self.grounded = False
            self._left_ground_at = -999.0
        # --- gravity & ground snap
        if not self.grounded:
            self.vel.z -= self.gravity * dt
        self.pos = self.pos + self.vel * dt
        floor = self.ground.height_at(self.pos)   # UE5: capsule sweep, not sample
        if self.pos.z <= floor:
            if not self.grounded and self.vel.z < -1.0:
                self._emit_footstep(now, landing=True)
            self.pos.z, self.vel.z, self.grounded = floor, 0.0, True
        elif self.grounded and self.pos.z > floor + 0.05:
            self.grounded = False
            self._left_ground_at = now
        # --- footstep cadence
        speed2d = self.vel.length2d()
        if self.grounded and speed2d > 0.2:
            interval = lerp(MOVE["step_interval_walk_s"], MOVE["step_interval_sprint_s"],
                            speed2d / MOVE["sprint_speed"])
            self._step_clock += dt
            if self._step_clock >= interval:
                self._step_clock = 0.0
                self._emit_footstep(now)
        else:
            self._step_clock = 0.0

    def _emit_footstep(self, now: float, landing: bool = False) -> None:
        surface = self.ground.surface_at(self.pos)
        speed = self.vel.length2d()
        for fn in self.on_footstep:
            fn(self.pos, self.yaw, surface, self.left_foot_next, speed, now, landing)
        self.left_foot_next = not self.left_foot_next

    def reset_position(self, p: V3) -> None:
        """Beat-script primitive (H-25): every position-expect resets first."""
        self.pos, self.vel = p, V3()
        self.grounded = True


@dataclass
class CameraRig:
    """First-person. FOV kicks with sprint; bob follows real footstep events
    (never a sine fake — the SAME event stream the audio uses, so eye and ear
    can never desync)."""
    fov_base: float = 92.0
    fov_sprint: float = 101.0
    bob_amplitude_m: float = 0.045
    bend_eye_drop_m: float = 0.55
    eye_height_m: float = 1.62

    def eye_pos(self, move: Movement) -> V3:
        drop = self.bend_eye_drop_m if move.gait == Gait.BEND else 0.0
        return move.pos + V3(0, 0, self.eye_height_m - drop)


# =============================================================================
# 5. AUDIO (the audio_visual_sync feature, wind, ambient, Erisaid hum)
# UE5: USandSoundComponent (attach at BeginPlay if missing — H-31/H-34),
#      MetaSounds for wind layers; telemetry accessors exposed to MCP bridge
# =============================================================================

@dataclass
class FootstepAudioEvent:
    t: float
    surface: Surface
    latency_ms: float       # audio trigger minus animation contact
    volume: float           # must scale with speed (beat expect)


class SandSoundComponent:
    """THE component the sleepwalker kept catching unattached (H-31/32/34).
    Owns: per-surface footstep banks, wind layers, AV-sync telemetry.
    UE5 rule: ChimeraMovementComponent::BeginPlay does
      if (!Owner->FindComponentByClass<USandSoundComponent>()) { NewObject +
      RegisterComponent } — runtime attach so no Blueprint wiring can be missed."""

    BANKS = {
        "Fantozzi-Sand":  ["SandL1", "SandL2", "SandL3", "SandR1", "SandR2", "SandR3"],
        "Fantozzi-Stone": ["StoneL1", "StoneL2", "StoneL3", "StoneR1", "StoneR2", "StoneR3"],
        "Metal-Scuff":    ["MetalL1", "MetalR1"],
        "Ice-Crunch":     ["IceL1", "IceR1"],
        "Interior-Soft":  ["SoftL1", "SoftR1"],
    }

    def __init__(self):
        self.events: list[FootstepAudioEvent] = []
        self.wind_speed = WIND["calm"]
        self.attached = True     # the fix: constructed == attached == true

    # ---- the verb->sound path (subscribed to Movement.on_footstep)
    def on_footstep(self, pos: V3, yaw: float, surface: Surface, left: bool,
                    speed: float, now: float, landing: bool) -> None:
        bank = SURFACE_TABLE[surface][4]
        cue = random.choice([c for c in self.BANKS.get(bank, ["SandL1"])
                             if ("L" in c) == left])
        volume = clamp(0.35 + 0.65 * speed / MOVE["sprint_speed"], 0.0, 1.0)
        if landing:
            volume = 1.0
        latency_ms = random.uniform(2.0, 14.0)   # UE5: measured, not simulated
        self.events.append(FootstepAudioEvent(now, surface, latency_ms, volume))
        _ = cue  # UE5: PlaySoundAtLocation(cue, pos, volume, pitch=0.92..1.08)

    # ---- wind: 3 MetaSound layers, speed-driven
    def wind_layers(self) -> dict:
        w = self.wind_speed
        return {
            "low_rumble":   clamp(w / WIND["storm"], 0.05, 1.0),           # 40-120 Hz
            "mid_rush":     clamp((w - 4.0) / (WIND["storm"] - 4.0), 0.0, 1.0),
            "high_whistle": clamp((w - 10.0) / (WIND["storm"] - 10.0), 0.0, 1.0),
            "pitch":        lerp(0.9, 1.35, w / WIND["storm"]),
        }

    # ---- TELEMETRY ACCESSORS (tb-0001: exactly what the MCP bridge queries)
    def GetFootstepSyncEventCount(self) -> int:
        return len(self.events)

    def GetFootstepSyncAvgLatencyMs(self) -> float:
        return (sum(e.latency_ms for e in self.events) / len(self.events)
                if self.events else 0.0)

    def GetFootstepSyncMaxLatencyMs(self) -> float:
        return max((e.latency_ms for e in self.events), default=0.0)

    def GetVolumeScalesWithSpeed(self) -> bool:
        slow = [e.volume for e in self.events if e.volume < 0.6]
        fast = [e.volume for e in self.events if e.volume >= 0.6]
        if not slow or not fast:
            return False
        return (sum(fast) / len(fast)) > (sum(slow) / len(slow))

    def ClearFootstepSyncTelemetry(self) -> None:
        self.events.clear()


class AmbientAudio:
    """Diegetic environment bed. Everything has a source in the world."""

    def __init__(self):
        self.layers = {
            "dry_thunder":      dict(active=False, distance_km=8.0),  # electric storms
            "biolum_hum":       dict(active=True, gain=0.12),         # night vents glow+hum
            "seismic_sub":      dict(active=True, gain=0.06),         # 8-16 Hz felt floor
            "habitat_air":      dict(active=False, gain=0.2),         # only indoors
            "suit_breath":      dict(active=True, gain=0.3),          # rises as O2 falls
            "erisaid_hum":      dict(active=False, gain=0.0),         # grows near it
        }

    def tick(self, suit: SuitState, dist_to_erisaid: float, indoors: bool,
             storm: bool) -> None:
        self.layers["suit_breath"]["gain"] = lerp(
            0.3, 0.9, 1.0 - suit.o2 / SUIT["o2_max"])          # diegetic O2 warning
        self.layers["habitat_air"]["active"] = indoors
        self.layers["dry_thunder"]["active"] = storm
        near = smoothstep(120.0, 15.0, dist_to_erisaid)
        self.layers["erisaid_hum"]["gain"] = 0.5 * near
        self.layers["erisaid_hum"]["active"] = near > 0.01


# =============================================================================
# 6. THE SKY (Loop 3) — sun, Earth, Moon, weather, and the STAR MEMORIAL
# UE5: SkyAtmosphere + custom StarMemorialComponent writing to a star texture
# =============================================================================

@dataclass
class Star:
    """One finished life. Brightness = sacrifice. Twinkle = unresolved regret.
    A bright enough star LIGHTS THE YARD AT NIGHT for every later generation."""
    life_name: str
    generation: int
    brightness: float          # 0..1, from SacrificeLog at death
    twinkle: bool              # open phantom pains at death
    bearing_deg: float         # placed on the memorial band by golden angle


class StarMemorial:
    def __init__(self):
        self.stars: list[Star] = []

    def add_life(self, life_name: str, generation: int, sacrifice_weight: float,
                 open_pains: int) -> Star:
        brightness = 1.0 - math.exp(-sacrifice_weight / STAR["brightness_k"])
        star = Star(life_name, generation, brightness,
                    twinkle=open_pains > 0 and STAR["twinkle_from_open_pains"],
                    bearing_deg=(len(self.stars) * GOLDEN_ANGLE_DEG) % 360.0)
        self.stars.append(star)
        return star

    def night_light_level(self) -> float:
        """Ancestors literally light your night. Costless ancestors don't."""
        return min(0.5, sum(s.brightness for s in self.stars
                            if s.brightness >= STAR["bright_lights_yard"]) * 0.18)


class SkyDome:
    """Earth AND Moon both hang low — the Yard sits in cislunar deep space.
    They are calendars: Earth phase = week hand, Moon transit = hour hand."""

    def __init__(self):
        self.time_h = 8.0            # hour within the 27h day
        self.day = 0
        self.earth_phase = 0.35      # 0..1 illuminated fraction
        self.moon_bearing_deg = 40.0

    def tick(self, hours: float) -> None:
        self.time_h += hours
        while self.time_h >= DAY_LENGTH_HOURS:
            self.time_h -= DAY_LENGTH_HOURS
            self.day += 1
        self.earth_phase = 0.5 + 0.5 * math.sin(TAU * self.day / 29.5)
        self.moon_bearing_deg = (self.moon_bearing_deg + hours * 3.1) % 360.0

    @property
    def is_night(self) -> bool:
        t = self.time_h / DAY_LENGTH_HOURS
        return t < 0.20 or t > 0.80

    def sun_elevation_deg(self) -> float:
        t = self.time_h / DAY_LENGTH_HOURS
        return math.sin((t - 0.20) / 0.60 * math.pi) * 62.0 if 0.20 <= t <= 0.80 else -12.0

    def temperature_c(self) -> float:
        e = max(0.0, self.sun_elevation_deg()) / 62.0
        return lerp(NIGHT_TEMP_C, DAY_TEMP_C, e)


class WeatherSystem:
    """Calm -> gusts -> the ~weekly storm that ERASES footprints and buries
    shallow things. The storm is the memento mori; the world forgets sand,
    remembers metal, and keeps everything you dug."""

    def __init__(self, rng: random.Random):
        self.rng = rng
        self.wind_speed = WIND["calm"]
        self.storm_active = False
        self._storm_ends_h = 0.0
        self._next_storm_day = rng.uniform(*WIND["storm_period_days"])
        self._next_gust_s = rng.uniform(*WIND["gust_period_s"])

    def tick(self, sky: SkyDome, hours: float, prints: FootprintLedger,
             dust: DustFX) -> Optional[str]:
        event = None
        if self.storm_active:
            self.wind_speed = WIND["storm"] * self.rng.uniform(0.8, 1.15)
            self._storm_ends_h -= hours
            if self._storm_ends_h <= 0.0:
                self.storm_active = False
                erased = prints.storm_erase() if WIND["storm_erases_footprints"] else 0
                event = f"storm_passed(erased_prints={erased})"
        else:
            base = WIND["breeze"] if not sky.is_night else WIND["calm"]
            self._next_gust_s -= hours * 3600.0
            if self._next_gust_s <= 0.0:
                self._next_gust_s = self.rng.uniform(*WIND["gust_period_s"])
                base = WIND["gust"]
            self.wind_speed = lerp(self.wind_speed, base, 0.4)
            if sky.day + sky.time_h / DAY_LENGTH_HOURS >= self._next_storm_day:
                self.storm_active = True
                self._storm_ends_h = self.rng.uniform(*WIND["storm_duration_min"]) / 60.0
                self._next_storm_day += self.rng.uniform(*WIND["storm_period_days"])
                event = "storm_rising"
        dust.tick(hours, self.wind_speed)
        return event


# =============================================================================
# 7. ITEMS, BURIED THINGS, CARRYING
# UE5: UChimeraItem (data asset) + UCarryComponent (mass affects gait)
# =============================================================================

class ItemKind(Enum):
    ORE_ILMENITE = auto(); ICE_WATER = auto(); OXYGEN_CAN = auto()
    MACHINE_PARTS = auto(); REGOLITH_GLASS = auto(); SEEDS = auto()
    FUEL_CELL = auto(); RELIC_SHARD = auto(); ERISAID_FRAGMENT = auto()
    HEIRLOOM = auto(); BEACON = auto(); STORY = auto()   # stories are cargo too


ITEM_TABLE = {
    #                       mass_kg  base_price  stackable
    ItemKind.ORE_ILMENITE:    (4.0,     12.0,      True),
    ItemKind.ICE_WATER:       (3.0,     18.0,      True),
    ItemKind.OXYGEN_CAN:      (2.0,     25.0,      True),
    ItemKind.MACHINE_PARTS:   (5.0,     40.0,      True),
    ItemKind.REGOLITH_GLASS:  (1.5,     30.0,      True),
    ItemKind.SEEDS:           (0.2,     55.0,      True),
    ItemKind.FUEL_CELL:       (6.0,     48.0,      True),
    ItemKind.RELIC_SHARD:     (0.8,    120.0,      False),
    ItemKind.ERISAID_FRAGMENT:(0.3,      0.0,      False),  # unsellable. period.
    ItemKind.HEIRLOOM:        (0.5,      0.0,      False),  # unsellable. period.
    ItemKind.BEACON:          (1.0,     15.0,      True),
    ItemKind.STORY:           (0.0,      8.0,      True),   # traded around fires
}


@dataclass
class Item:
    kind: ItemKind
    quality: float = 1.0
    origin_generation: int = 0    # provenance travels with things


@dataclass
class BuriedItem:
    item: Item
    depth: float                  # m below original grade


class CarrySystem:
    """Two hands + one backpack. Mass slows you honestly."""
    BACKPACK_KG = 30.0

    def __init__(self):
        self.hands: Optional[Item] = None
        self.pack: list[Item] = []

    def mass(self) -> float:
        m = ITEM_TABLE[self.hands.kind][0] if self.hands else 0.0
        return m + sum(ITEM_TABLE[i.kind][0] for i in self.pack)

    def can_stow(self, item: Item) -> bool:
        return self.mass() + ITEM_TABLE[item.kind][0] <= self.BACKPACK_KG

    def pick_up(self, item: Item) -> bool:
        if self.hands is None:
            self.hands = item
            return True
        if self.can_stow(item):
            self.pack.append(item)
            return True
        return False

    def drop(self) -> Optional[Item]:
        it, self.hands = self.hands, None
        return it

    def speed_penalty(self) -> float:
        return 1.0 - 0.35 * clamp(self.mass() / self.BACKPACK_KG, 0.0, 1.0)


# =============================================================================
# 8. TOOLS (Loop 4) — shovel, scanner, weapon, beacon, repair
# UE5: ATool_* actors under ProceduralGenerated/Tools; verbs have BEHAVIOR (H-21)
# =============================================================================

class ToolKind(Enum):
    SHOVEL = auto(); SCANNER = auto(); WEAPON = auto(); BEACON = auto(); REPAIR = auto()


@dataclass
class Tool:
    kind: ToolKind
    durability: float = 200.0
    ammo: int = 0

    @property
    def broken(self) -> bool:
        return self.durability <= 0.0


class Shovel:
    """Dig(): line-trace down, lower DigGrid, burst dust, play sand sound,
    stamp tool-mark decal, cost durability + O2. Returns uncovered items."""
    DIG_RADIUS = 0.6
    SCOOP_DEPTH = 0.15
    DURABILITY_PER_SCOOP = 1.0

    @staticmethod
    def dig(tool: Tool, at: V3, grid: DigGrid, dust: DustFX, sand: SandSoundComponent,
            surface: Surface, now: float) -> list:
        if tool.broken or surface in (Surface.METAL, Surface.INTERIOR):
            return []   # sparks + refusal thunk on metal; the world says no
        tool.durability -= Shovel.DURABILITY_PER_SCOOP
        found = grid.dig(at, Shovel.DIG_RADIUS, Shovel.SCOOP_DEPTH)
        dust.footfall(at, surface, MOVE["sprint_speed"], now)   # big burst
        sand.on_footstep(at, 0.0, surface, True, MOVE["jog_speed"], now, landing=True)
        return found


class Scanner:
    """Ping: 40 m sphere. Highlights buried items, dots, ore veins — and OBSERVES
    the region (collapse: procedural content is finalized on first observation,
    Design Law 4 / the quantum theme made playable)."""
    RANGE_M = 40.0

    @staticmethod
    def ping(tool: Tool, at: V3, world: "GameWorld") -> dict:
        world.player_suit.battery = max(
            0.0, world.player_suit.battery - SUIT["battery_drain_scanner"])
        world.universe.observe_region(at, Scanner.RANGE_M)
        hits = {
            "buried": [k for k, items in world.dig_grid.buried.items() if items
                       and V3(k[0] * DigGrid.CELL, k[1] * DigGrid.CELL, 0.0)
                       .__sub__(at).length2d() < Scanner.RANGE_M],
            "dots": [d.name for d in world.dots
                     if (d.pos - at).length2d() < Scanner.RANGE_M],
            "erisaid_bearing_deg": math.degrees(math.atan2(
                world.erisaid.pos.y - at.y, world.erisaid.pos.x - at.x)) % 360.0,
        }
        return hits


class Weapon:
    """Exists. Works. Costs. Firing it near the Erisaid deafens it for a season;
    firing it at a dot is remembered by every dot and every heir. The richest
    sacrifice entry is WEAPON_NEVER_FIRED at a life's end despite real threats."""
    DAMAGE = 34.0
    RANGE_M = 60.0

    @staticmethod
    def fire(tool: Tool, at_target: Optional["Dot"], world: "GameWorld") -> str:
        if tool.ammo <= 0:
            return "click"       # dry-fire is diegetic shame
        tool.ammo -= 1
        world.flags["weapon_fired_this_life"] = True
        if (world.movement.pos - world.erisaid.pos).length2d() < 120.0:
            world.erisaid.deaf_until_day = world.sky.day + 30 * ERISAID[
                "deaf_seasons_after_gunfire"]
        if at_target is not None:
            at_target.health -= Weapon.DAMAGE
            for d in world.dots:
                d.memory["saw_player_shoot"] = True
            world.factions.rep_delta(at_target.faction, -25.0)
            return "hit" if at_target.health > 0 else "killed"
        return "warning_shot"


# =============================================================================
# 9. OTHER DOTS (Loop 5) — wordless people. Gestures, needs, memory, strangers
# UE5: ANPCDotCharacter + UDotBrainComponent (state machine, no BT asset dep)
# =============================================================================

class DotState(Enum):
    DISTANT = auto()      # a literal dot on the horizon (LOD0 of humanity)
    APPROACHING = auto()
    NEAR = auto()
    ENCOUNTER = auto()    # gesture-range interaction
    LEAVING = auto()
    GONE = auto()


class DotArchetype(Enum):
    TRADER = auto(); STRANGER = auto(); DRIFTER = auto(); PIRATE = auto()
    QUIET_LISTENER = auto()   # they kneel at the Erisaid; they never trade


class Gesture(Enum):
    WAVE = auto(); OFFER = auto(); REFUSE = auto(); POINT = auto()
    KNEEL = auto(); BECKON = auto(); WARN = auto(); THANK = auto()
    GRIEVE = auto()


class NeedKind(Enum):
    O2 = auto(); WATER = auto(); PARTS = auto(); WARMTH = auto()
    RIDE = auto(); BURIAL = auto()    # some needs cannot be paid for


NEED_FULFILLMENT = {
    NeedKind.O2: ItemKind.OXYGEN_CAN,
    NeedKind.WATER: ItemKind.ICE_WATER,
    NeedKind.PARTS: ItemKind.MACHINE_PARTS,
    NeedKind.WARMTH: ItemKind.FUEL_CELL,
    NeedKind.RIDE: None,
    NeedKind.BURIAL: None,
}


@dataclass
class Dot:
    name: str
    archetype: DotArchetype
    pos: V3
    faction: str = "yardfolk"
    state: DotState = DotState.DISTANT
    health: float = 100.0
    need: Optional[NeedKind] = None
    can_pay: bool = True
    inventory: list = field(default_factory=list)
    memory: dict = field(default_factory=dict)   # persists ACROSS GENERATIONS
    walk_speed: float = 1.2

    def tick(self, dt: float, player_pos: V3, world: "GameWorld") -> None:
        d = (self.pos - player_pos).length2d()
        if self.state == DotState.DISTANT and d < 220.0:
            self.state = DotState.APPROACHING
        elif self.state == DotState.APPROACHING:
            step = (player_pos - self.pos).normalized() * (self.walk_speed * dt)
            self.pos = self.pos + step
            if d < 25.0:
                self.state = DotState.NEAR
        elif self.state == DotState.NEAR and d < 4.0:
            self.state = DotState.ENCOUNTER
            self.on_meet(world)
        elif self.state == DotState.LEAVING:
            away = (self.pos - player_pos).normalized() * (self.walk_speed * dt)
            self.pos = self.pos + away
            if d > 300.0:
                self.state = DotState.GONE

    def on_meet(self, world: "GameWorld") -> None:
        # Recognition across lives: dots remember your ANCESTORS.
        helped_gen = self.memory.get("helped_by_generation")
        if helped_gen is not None and helped_gen < world.generation:
            self.gesture_out = Gesture.KNEEL      # they honor the family debt
        elif self.memory.get("saw_player_shoot"):
            self.gesture_out = Gesture.WARN
        elif self.need is not None:
            self.gesture_out = Gesture.POINT      # points at what hurts
        else:
            self.gesture_out = Gesture.WAVE

    def receive_gesture(self, g: Gesture, world: "GameWorld") -> Gesture:
        """The whole dialogue system. Gesture in, gesture out. No words ever."""
        if g == Gesture.OFFER and self.need is not None:
            given = world.carry.drop()
            wanted = NEED_FULFILLMENT[self.need]
            if given is not None and wanted is not None and given.kind == wanted:
                self.memory["helped_by_generation"] = world.generation
                self.need = None
                if not self.can_pay:
                    world.sacrifice.record(SacrificeKind.GAVE_CARGO,
                                           note=f"gave {given.kind.name} to {self.name}"
                                           " who could not pay")
                else:
                    world.credits += ITEM_TABLE[given.kind][1] * 1.2
                self.state = DotState.LEAVING
                return Gesture.THANK
            if given is not None:
                world.carry.pick_up(given)   # wrong item — handed back gently
            return Gesture.REFUSE
        if g == Gesture.REFUSE and self.need is not None and not self.can_pay:
            self.state = DotState.LEAVING
            world.flags["refused_unpayable"] = world.flags.get(
                "refused_unpayable", 0) + 1   # the world keeps quiet score
            return Gesture.GRIEVE
        if g == Gesture.WAVE:
            return Gesture.WAVE
        return Gesture.REFUSE


class StrangerForge:
    """Generates the can't-pay scenarios — the sacrifice hooks. Cadence is
    director-controlled; arrival bearings follow the golden angle so strangers
    never bunch up on one horizon."""
    SCENARIOS = [
        (NeedKind.O2,     "stranded, suit hissing, no credits"),
        (NeedKind.PARTS,  "rover dead 3 km out, storm coming"),
        (NeedKind.WATER,  "walked from the far pads, empty flask"),
        (NeedKind.WARMTH, "night caught them, battery flat"),
        (NeedKind.BURIAL, "carries a body; asks with their eyes"),
        (NeedKind.RIDE,   "points at the horizon, then at your rover"),
    ]

    def __init__(self, rng: random.Random):
        self.rng = rng
        self.spawned = 0

    def maybe_spawn(self, world: "GameWorld") -> Optional[Dot]:
        need, blurb = self.rng.choice(self.SCENARIOS)
        bearing = spiral_point(self.spawned, spacing=30.0)
        self.spawned += 1
        dot = Dot(name=f"stranger_{world.generation}_{self.spawned}",
                  archetype=DotArchetype.STRANGER,
                  pos=world.movement.pos + bearing.normalized() * 260.0,
                  need=need, can_pay=self.rng.random() < 0.35)
        dot.memory["blurb"] = blurb
        return dot


# =============================================================================
# 10. ECONOMY & TRADE (System_Economy) — every profitable route has a face
# UE5: generator-owned EconomyManager/CommodityData/StationTradingData — this
#      pseudocode IS the template spec for core/game_code_generator.py
# =============================================================================

@dataclass
class StationMarket:
    station_id: str
    pos: V3
    stock: dict = field(default_factory=dict)      # ItemKind -> units
    demand: dict = field(default_factory=dict)     # ItemKind -> 0.5..2.0 multiplier

    ELASTICITY = 0.04    # price move per unit traded

    def price(self, kind: ItemKind) -> float:
        return ITEM_TABLE[kind][1] * self.demand.get(kind, 1.0)

    def buy_from_player(self, kind: ItemKind, units: int) -> float:
        total = 0.0
        for _ in range(units):
            total += self.price(kind)
            self.demand[kind] = max(0.5, self.demand.get(kind, 1.0)
                                    - self.ELASTICITY)
            self.stock[kind] = self.stock.get(kind, 0) + 1
        return total

    def sell_to_player(self, kind: ItemKind, units: int) -> Optional[float]:
        if self.stock.get(kind, 0) < units:
            return None
        total = 0.0
        for _ in range(units):
            total += self.price(kind) * 1.1
            self.demand[kind] = min(2.0, self.demand.get(kind, 1.0)
                                    + self.ELASTICITY)
            self.stock[kind] -= 1
        return total

    def drift(self, rng: random.Random) -> None:
        for k in list(self.demand):
            self.demand[k] = clamp(self.demand[k] + rng.uniform(-0.03, 0.03),
                                   0.5, 2.0)


class FactionLedger:
    FACTIONS = {
        "yardfolk": "settlers of the Yard — the memorial is theirs",
        "combine":  "corporate haulers — pay well, remember nothing",
        "drifters": "nomads; some slide into piracy when the storms are long",
        "the_quiet": "Erisaid-listeners; trade only in stories",
    }

    def __init__(self):
        self.rep = {f: 0.0 for f in self.FACTIONS}

    def rep_delta(self, faction: str, amount: float) -> None:
        if faction in self.rep:
            self.rep[faction] = clamp(self.rep[faction] + amount, -100.0, 100.0)


# =============================================================================
# 11. THE SACRIFICE LOG — the invisible score (Design Law 2)
# NEVER shown in any UI. Read only twice: by the star at death, by the mirror.
# UE5: USacrificeLogComponent (exists) + SaveGame serialization
# =============================================================================

class SacrificeKind(Enum):
    REFUSED_PROFIT = auto()        # walked away from a cruel-but-legal deal
    GAVE_CARGO = auto()            # handed real goods to someone who can't pay
    GAVE_O2 = auto()               # shared your own air
    SPENT_TIME_UNPAYABLE = auto()  # hours on someone with nothing to give
    TOOK_RISK_FOR_OTHER = auto()   # entered the storm for a stranger's beacon
    BURIED_STRANGER = auto()       # dug a grave with your own durability
    WEAPON_NEVER_FIRED = auto()    # threatened, armed, and held
    HEIRLOOM_GIVEN = auto()        # gave away the one unsellable thing


SACRIFICE_WEIGHTS = {
    SacrificeKind.REFUSED_PROFIT: 1.0,
    SacrificeKind.GAVE_CARGO: 1.5,
    SacrificeKind.GAVE_O2: 3.0,
    SacrificeKind.SPENT_TIME_UNPAYABLE: 2.0,
    SacrificeKind.TOOK_RISK_FOR_OTHER: 2.5,
    SacrificeKind.BURIED_STRANGER: 3.5,
    SacrificeKind.WEAPON_NEVER_FIRED: 2.0,
    SacrificeKind.HEIRLOOM_GIVEN: 5.0,
}


@dataclass
class SacrificeEntry:
    kind: SacrificeKind
    weight: float
    note: str
    generation: int
    day: int


class SacrificeLog:
    def __init__(self):
        self.entries: list[SacrificeEntry] = []

    def record(self, kind: SacrificeKind, note: str = "", generation: int = 0,
               day: int = 0) -> None:
        self.entries.append(SacrificeEntry(
            kind, SACRIFICE_WEIGHTS[kind], note, generation, day))

    def weight_for_generation(self, generation: int) -> float:
        return sum(e.weight for e in self.entries if e.generation == generation)

    def is_costless(self, generation: int) -> bool:
        return self.weight_for_generation(generation) <= 0.0


# === CONTINUED IN PART 3 (shelter, travel, universe, generations, endings, director, main) ===
