"""CHIMERA_VISION.py — THE ULTIMATE SINGLE-FILE PSEUDOSCRIPT OF A AAA GAME.

CHIMERA: a generational, wordless, embodied life on a regolith planetoid in
cislunar deep space. Earth and Moon both hang in the sky. Every finished life
becomes a star whose brightness equals what that life SACRIFICED. The bad
ending is not death — it is a COSTLESS LIFE: a dim star, and the Erisaid's
mirror showing nothing.

DESIGN LAWS
  1. The world answers the body — every verb has physical, audible, visible
     consequence (footprint, dust, sound, heat). No abstract clicks.
  2. The bad ending is a costless life. Meaning = what you gave up. The game
     NEVER explains this; it is taught only through consequence.
  3. Wordless. No dialogue text. Gestures, objects, sounds, and light.
  4. Nothing observed is lost. Footprints, pits, shelters, debts of kindness
     persist across generations. Unobserved space stays uncollapsed.
  5. The player is the trunk. All content generates outward from the player
     along the golden-angle spiral, at every scale.

ARCHITECTURE (single file == whole game; sections in dependency order)
  §1  Core math          — V3 / Quat / Mat4 / noise / splines      (FMath, FVector)
  §2  ECS kernel         — Entity / Component / System / EventBus  (UObject/AActor world)
  §3  Component catalog  — Transform, Mesh, Physics, Audio, ...    (UActorComponent zoo)
  §4  Assets & geometry  — vertex/index buffers, procedural meshes (UStaticMesh, PCG)
  §5  Rendering          — camera, frustum, shadows, GI, post, VFX (Lumen, Niagara, PP)
  §6  Physics            — sweeps, heightfield, gravity volumes    (Chaos, UCharacterMovement)
  §7  Spatial audio      — attenuation, reverb, mix, music, minigame (MetaSounds, Submixes)
  §8  AI                 — Behavior Trees, FSM, NavMesh A*, steering (UBehaviorTree, NavSystem)
  §9  Input & UI         — Enhanced Input, UMG widget tree, menus  (UInputMappingContext, UMG)
  §10 Save/Load          — versioned USaveGame-style serialization (USaveGame, SaveGameSystem)
  §11 Networking         — server-authoritative sim, replication, prediction (UNetDriver)
  §12 Game layer         — ground, suit, dots, economy, sacrifice, sky, travel, Erisaid,
                           generations, director (the game itself, on top of §1-§11)
  §13 Boot & proof       — headless two-lives demo through the FULL stack

Everything below is executable pseudocode: pure stdlib Python that RUNS, with
rich comments mapping each construct to its UE5.8 C++ equivalent. The numbers
are the tuning truth. A later AI ports this to Source/Chimera/ and debugs.
"""

from __future__ import annotations

import json
import math
import random
import struct
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, IntEnum, auto
from typing import Any, Callable, Iterator, Optional, Type, TypeVar

# =============================================================================
# §1. CORE MATH — FMath / FVector / FQuat / FMatrix, value noise, golden angle
# =============================================================================

GOLDEN_ANGLE_DEG = 137.50776405003785       # phyllotaxis; the generation law
TAU = math.tau
EPS = 1e-9


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * clamp(t, 0.0, 1.0)


def inv_lerp(a: float, b: float, v: float) -> float:
    return clamp((v - a) / (b - a + EPS), 0.0, 1.0)


def smoothstep(e0: float, e1: float, x: float) -> float:
    t = inv_lerp(e0, e1, x)
    return t * t * (3.0 - 2.0 * t)


def spring_damper(x: float, v: float, target: float, halflife: float,
                  dt: float) -> tuple[float, float]:
    """Critically-damped spring — UE5: FMath::CriticallyDampedSmoothing.
    Used for camera bob return, FOV kicks, UI needle easing."""
    y = 2.0 * 0.6931 / max(halflife, EPS)
    j = v + y * (x - target)
    e = math.exp(-y * dt)
    return target + (x - target + j * dt) * e, (v - y * j * dt) * e


@dataclass
class V3:
    """FVector. Right-handed, Z-up, meters."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def __add__(self, o: "V3") -> "V3": return V3(self.x + o.x, self.y + o.y, self.z + o.z)
    def __sub__(self, o: "V3") -> "V3": return V3(self.x - o.x, self.y - o.y, self.z - o.z)
    def __mul__(self, s: float) -> "V3": return V3(self.x * s, self.y * s, self.z * s)
    def __neg__(self) -> "V3": return V3(-self.x, -self.y, -self.z)

    def dot(self, o: "V3") -> float:
        return self.x * o.x + self.y * o.y + self.z * o.z

    def cross(self, o: "V3") -> "V3":
        return V3(self.y * o.z - self.z * o.y,
                  self.z * o.x - self.x * o.z,
                  self.x * o.y - self.y * o.x)

    def length(self) -> float: return math.sqrt(self.dot(self))
    def length2d(self) -> float: return math.hypot(self.x, self.y)

    def normalized(self) -> "V3":
        l = self.length()
        return V3(self.x / l, self.y / l, self.z / l) if l > EPS else V3()

    def dist(self, o: "V3") -> float: return (self - o).length()
    def dist2d(self, o: "V3") -> float: return (self - o).length2d()

    def to_tuple(self) -> tuple: return (self.x, self.y, self.z)


UP = V3(0.0, 0.0, 1.0)


@dataclass
class Quat:
    """FQuat — enough of one for cameras, ships, and skeletal joints."""
    w: float = 1.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    @staticmethod
    def from_axis_angle(axis: V3, rad: float) -> "Quat":
        a = axis.normalized()
        s = math.sin(rad * 0.5)
        return Quat(math.cos(rad * 0.5), a.x * s, a.y * s, a.z * s)

    @staticmethod
    def from_yaw_pitch(yaw: float, pitch: float) -> "Quat":
        return Quat.from_axis_angle(UP, yaw) @ Quat.from_axis_angle(V3(0, 1, 0), pitch)

    def __matmul__(self, o: "Quat") -> "Quat":
        return Quat(
            self.w * o.w - self.x * o.x - self.y * o.y - self.z * o.z,
            self.w * o.x + self.x * o.w + self.y * o.z - self.z * o.y,
            self.w * o.y - self.x * o.z + self.y * o.w + self.z * o.x,
            self.w * o.z + self.x * o.y - self.y * o.x + self.z * o.w)

    def rotate(self, v: V3) -> V3:
        q = V3(self.x, self.y, self.z)
        t = q.cross(v) * 2.0
        return v + t * self.w + q.cross(t)

    def forward(self) -> V3: return self.rotate(V3(1, 0, 0))
    def right(self) -> V3: return self.rotate(V3(0, 1, 0))


class Mat4:
    """FMatrix (row-major 4x4) — only what a renderer needs: perspective,
    look-at, multiply, point transform. Shadow maps use these directly."""

    def __init__(self, rows: Optional[list] = None):
        self.m = rows or [[1.0 if i == j else 0.0 for j in range(4)] for i in range(4)]

    @staticmethod
    def perspective(fov_y_deg: float, aspect: float, znear: float, zfar: float) -> "Mat4":
        f = 1.0 / math.tan(math.radians(fov_y_deg) * 0.5)
        m = Mat4()
        m.m = [[f / aspect, 0, 0, 0],
               [0, f, 0, 0],
               [0, 0, (zfar + znear) / (znear - zfar), (2 * zfar * znear) / (znear - zfar)],
               [0, 0, -1, 0]]
        return m

    @staticmethod
    def ortho(half_w: float, half_h: float, znear: float, zfar: float) -> "Mat4":
        m = Mat4()
        m.m = [[1.0 / half_w, 0, 0, 0],
               [0, 1.0 / half_h, 0, 0],
               [0, 0, -2.0 / (zfar - znear), -(zfar + znear) / (zfar - znear)],
               [0, 0, 0, 1]]
        return m

    @staticmethod
    def look_at(eye: V3, target: V3, up: V3 = UP) -> "Mat4":
        f = (target - eye).normalized()
        r = f.cross(up).normalized()
        u = r.cross(f)
        m = Mat4()
        m.m = [[r.x, r.y, r.z, -r.dot(eye)],
               [u.x, u.y, u.z, -u.dot(eye)],
               [-f.x, -f.y, -f.z, f.dot(eye)],
               [0, 0, 0, 1]]
        return m

    def __matmul__(self, o: "Mat4") -> "Mat4":
        r = Mat4()
        r.m = [[sum(self.m[i][k] * o.m[k][j] for k in range(4)) for j in range(4)]
               for i in range(4)]
        return r

    def transform(self, p: V3) -> tuple[float, float, float, float]:
        v = (p.x, p.y, p.z, 1.0)
        out = [sum(self.m[i][k] * v[k] for k in range(4)) for i in range(4)]
        return out[0], out[1], out[2], out[3]


def _hash2(ix: int, iy: int, seed: int) -> float:
    h = (ix * 374761393 + iy * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65536.0


def value_noise2(x: float, y: float, seed: int = 0) -> float:
    """UE5: Material 'Noise' node (Value mode) / FMath::PerlinNoise2D stand-in."""
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    a, b = _hash2(ix, iy, seed), _hash2(ix + 1, iy, seed)
    c, d = _hash2(ix, iy + 1, seed), _hash2(ix + 1, iy + 1, seed)
    ux, uy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    return lerp(lerp(a, b, ux), lerp(c, d, ux), uy)


def fbm2(x: float, y: float, octaves: int = 4, seed: int = 0) -> float:
    total, amp, freq, norm = 0.0, 1.0, 1.0, 0.0
    for i in range(octaves):
        total += amp * value_noise2(x * freq, y * freq, seed + i)
        norm += amp
        amp *= 0.5
        freq *= 2.0
    return total / norm


def spiral_point(index: int, spacing: float = 8.0) -> V3:
    """Golden-angle phyllotaxis — the i-th thing the world grows around the
    player-trunk: buried caches, stranger bearings, stations, asteroid belts."""
    r = spacing * math.sqrt(index + 1)
    a = math.radians(GOLDEN_ANGLE_DEG) * index
    return V3(r * math.cos(a), r * math.sin(a), 0.0)


def catmull_rom(p0: V3, p1: V3, p2: V3, p3: V3, t: float) -> V3:
    """Spline for rover paths, hopper arcs, cinematic cameras — FInterpCurve."""
    t2, t3 = t * t, t * t * t
    return (p1 * 2.0 + (p2 - p0) * t
            + (p0 * 2.0 - p1 * 5.0 + p2 * 4.0 - p3) * t2
            + (p3 - p0 + p1 * 3.0 - p2 * 3.0) * t3) * 0.5


# =============================================================================
# §2. ECS KERNEL — the engine object model
# UE5 mapping: World==UWorld, Entity==AActor id, Component==UActorComponent,
# System==tick-registered subsystem (UTickableWorldSubsystem), EventBus==
# multicast delegates (DECLARE_DYNAMIC_MULTICAST_DELEGATE).
# =============================================================================

EntityId = int
C = TypeVar("C", bound="Component")


class Component:
    """Base — UActorComponent. Subclasses are plain dataclasses; fields are
    UPROPERTY()s. Fields listed in REPLICATED are marked Replicated in C++."""
    REPLICATED: tuple = ()          # ~ DOREPLIFETIME(...) in GetLifetimeReplicatedProps
    SAVED: tuple = ()               # ~ UPROPERTY(SaveGame)


class TickGroup(IntEnum):
    """~ ETickingGroup: deterministic system order within one frame."""
    INPUT = 0          # gather & route input                (TG_PrePhysics)
    AI = 1             # behavior trees, nav following       (TG_PrePhysics)
    PRE_PHYSICS = 2    # gameplay logic writing to physics   (TG_PrePhysics)
    PHYSICS = 3        # movement solve, sweeps, gravity     (TG_DuringPhysics)
    POST_PHYSICS = 4   # ground reactions: prints, dust      (TG_PostPhysics)
    WORLD = 5          # sky, weather, economy, director
    AUDIO = 6          # spatialization, mixing, music
    UI = 7             # HUD state, menus
    NETWORK = 8        # snapshot build / reconcile
    RENDER = 9         # culling, draw list (conceptual)


class EventBus:
    """Typed pub/sub — the engine's multicast delegate table. ONE event stream
    per fact (e.g. FootstepEvent) so audio/VFX/UI can never desync (Law 1)."""

    def __init__(self) -> None:
        self._subs: dict[type, list[Callable]] = {}

    def subscribe(self, event_type: type, fn: Callable) -> None:
        self._subs.setdefault(event_type, []).append(fn)

    def emit(self, event: Any) -> None:
        for fn in self._subs.get(type(event), []):
            fn(event)


class World:
    """UWorld: entity/component storage + queries. Dense per-type dicts —
    the pseudocode analog of FActorIterator + GetComponentByClass."""

    def __init__(self) -> None:
        self._next: EntityId = 1
        self._store: dict[type, dict[EntityId, Component]] = {}
        self._alive: set[EntityId] = set()
        self.events = EventBus()

    def create(self, *components: Component) -> EntityId:      # ~ SpawnActor
        eid = self._next
        self._next += 1
        self._alive.add(eid)
        for c in components:
            self.add(eid, c)
        return eid

    def destroy(self, eid: EntityId) -> None:                  # ~ DestroyActor
        self._alive.discard(eid)
        for table in self._store.values():
            table.pop(eid, None)

    def add(self, eid: EntityId, comp: Component) -> None:
        self._store.setdefault(type(comp), {})[eid] = comp

    def get(self, eid: EntityId, ctype: Type[C]) -> C:
        return self._store[ctype][eid]                          # KeyError == checkf

    def try_get(self, eid: EntityId, ctype: Type[C]) -> Optional[C]:
        return self._store.get(ctype, {}).get(eid)

    def query(self, *ctypes: type) -> Iterator[tuple]:
        """Iterate (eid, comp0, comp1, ...) for entities having ALL ctypes."""
        if not ctypes:
            return
        primary = self._store.get(ctypes[0], {})
        for eid, c0 in list(primary.items()):
            if eid not in self._alive:
                continue
            comps = [c0]
            ok = True
            for ct in ctypes[1:]:
                c = self._store.get(ct, {}).get(eid)
                if c is None:
                    ok = False
                    break
                comps.append(c)
            if ok:
                yield (eid, *comps)

    def single(self, ctype: Type[C]) -> tuple[EntityId, C]:
        """The one-and-only (player, sky, ...) — ~ GetGameState/GetPawn."""
        for eid, c in self._store.get(ctype, {}).items():
            if eid in self._alive:
                return eid, c
        raise LookupError(ctype.__name__)


class System(ABC):
    """A ticking engine subsystem. Order = (group, order_in_group)."""
    GROUP: TickGroup = TickGroup.WORLD
    ORDER: int = 0

    @abstractmethod
    def tick(self, game: "ChimeraGame", dt: float) -> None: ...


# =============================================================================
# §3. COMPONENT CATALOG — the UActorComponent zoo (every field a UPROPERTY)
# =============================================================================

@dataclass
class Transform(Component):
    """~ USceneComponent root: UPROPERTY(Replicated) FVector/FRotator."""
    REPLICATED = ("pos", "yaw")
    SAVED = ("pos", "yaw", "pitch")
    pos: V3 = field(default_factory=V3)
    yaw: float = 0.0
    pitch: float = 0.0
    scale: float = 1.0

    def rotation(self) -> Quat:
        return Quat.from_yaw_pitch(self.yaw, self.pitch)

    def forward(self) -> V3:
        return V3(math.cos(self.yaw), math.sin(self.yaw), 0.0)


@dataclass
class PhysicsBody(Component):
    """~ UCharacterMovementComponent state + capsule (Chaos rigid for props)."""
    REPLICATED = ("vel", "grounded")
    vel: V3 = field(default_factory=V3)
    grounded: bool = True
    gravity_scale: float = 1.0
    capsule_radius: float = 0.35
    capsule_half_height: float = 0.9
    mass_kg: float = 90.0
    kinematic: bool = False        # true = script-driven (rover on spline)


@dataclass
class StaticMeshRef(Component):
    """~ UStaticMeshComponent: mesh + material + render flags."""
    mesh_id: str = "SM_Cube"
    material_id: str = "M_Default"
    casts_shadow: bool = True
    bounds_radius: float = 1.0     # local-space bounding sphere for culling
    lod_bias: int = 0


@dataclass
class SkeletalMeshRef(Component):
    """~ USkeletalMeshComponent + AnimInstance state machine variables.
    Animation here = pose params the anim graph would consume."""
    mesh_id: str = "SK_Astronaut"
    anim_state: str = "idle"       # idle|walk|jog|sprint|bend|dig|gesture_*
    playback_t: float = 0.0
    stride_phase: float = 0.0      # 0..1; foot contacts at 0.25 (L) and 0.75 (R)


@dataclass
class LightSource(Component):
    """~ ULightComponent (point/spot). The sun/Earthshine are §5 globals."""
    color: tuple = (1.0, 0.95, 0.9)
    intensity: float = 5000.0      # lumen-ish
    radius: float = 12.0
    casts_shadow: bool = False


@dataclass
class ParticleEmitterRef(Component):
    """~ UNiagaraComponent bound to a system asset (§5 EmitterSpec)."""
    spec_id: str = "FX_DustPuff"
    active: bool = True
    rate_scale: float = 1.0


@dataclass
class AudioSource(Component):
    """~ UAudioComponent: a positioned looping bed or one-shot channel."""
    cue: str = ""
    looping: bool = False
    gain: float = 1.0
    spatial: bool = True
    min_radius: float = 2.0        # full volume inside
    max_radius: float = 60.0       # silent beyond (attenuation curve in §7)
    playing: bool = False
    bus: str = "sfx"               # submix routing: sfx|ambience|music|ui


@dataclass
class Health(Component):
    REPLICATED = ("hp",)
    hp: float = 100.0
    hp_max: float = 100.0


@dataclass
class NavAgent(Component):
    """~ UNavMovementComponent + path-following state (§8 fills `path`)."""
    speed: float = 1.2
    goal: Optional[V3] = None
    path: list = field(default_factory=list)
    path_i: int = 0
    repath_cooldown: float = 0.0
    avoid_radius: float = 0.8      # RVO-lite separation ring


@dataclass
class PlayerTag(Component):
    """~ APawn possessed by APlayerController. client_id keys §11 prediction."""
    client_id: int = 0


@dataclass
class NetIdentity(Component):
    """~ replication bookkeeping per actor: role, priority, dirty mask."""
    net_id: int = 0
    role: str = "authority"        # authority|autonomous|simulated
    net_cull_distance: float = 400.0
    dirty: set = field(default_factory=set)


# --- game-layer components declared here so §12 systems can query them ------

class Gait(Enum):
    IDLE = auto(); WALK = auto(); JOG = auto(); SPRINT = auto(); BEND = auto()


@dataclass
class SuitComponent(Component):
    """~ USuitComponent (manual-lane C++). Diegetic survival state."""
    SAVED = ("o2", "battery", "dust_clog", "integrity")
    o2: float = 100.0
    battery: float = 100.0
    dust_clog: float = 0.0
    temperature_c: float = 20.0
    integrity: float = 100.0
    gait: Gait = Gait.IDLE


@dataclass
class CarryComponent(Component):
    """~ UCarryComponent: two hands + a 30 kg pack; mass slows honestly."""
    SAVED = ("hands", "pack")
    hands: Optional["Item"] = None
    pack: list = field(default_factory=list)
    pack_kg_max: float = 30.0


@dataclass
class DotBrain(Component):
    """~ UDotBrainComponent: blackboard + behavior tree + coarse FSM (§8)."""
    archetype: str = "stranger"    # trader|stranger|drifter|pirate|quiet
    bb: dict = field(default_factory=dict)      # ~ UBlackboardComponent
    tree_id: str = "BT_Stranger"
    fsm: str = "distant"           # distant|approaching|near|encounter|leaving|gone
    need: Optional[str] = None     # o2|water|parts|warmth|ride|burial
    can_pay: bool = True
    memory: dict = field(default_factory=dict)  # persists across GENERATIONS


@dataclass
class ItemComponent(Component):
    """World-dropped item pickup — ~ AItemActor with sphere overlap."""
    kind: str = "ORE_ILMENITE"
    quality: float = 1.0
    origin_generation: int = 0


@dataclass
class ReverbZoneComponent(Component):
    """~ AAudioVolume: box that recolors everything heard inside (§7)."""
    half_extents: V3 = field(default_factory=lambda: V3(6, 6, 3))
    wet: float = 0.35
    decay_s: float = 1.2
    preset: str = "habitat_shell"


# --- typed events (the delegate signatures) ---------------------------------

@dataclass
class FootstepEvent:
    """THE canonical body-fact. Audio, decals, particles, camera bob, and
    haptics all subscribe to THIS — one source, zero desync (Law 1)."""
    eid: EntityId
    pos: V3
    yaw: float
    surface: "Surface"
    left_foot: bool
    speed: float
    t: float
    landing: bool = False


@dataclass
class GestureEvent:
    frm: EntityId
    to: EntityId
    gesture: str            # wave|offer|refuse|point|kneel|beckon|warn|thank|grieve


@dataclass
class SacrificeEvent:
    kind: str
    weight: float
    note: str
    generation: int


@dataclass
class DeathEvent:
    eid: EntityId
    cause: str


@dataclass
class StormEvent:
    phase: str              # rising|passed
    erased_prints: int = 0


# =============================================================================
# §4. ASSETS & GEOMETRY — vertex/index buffers, procedural meshes, PBR materials
# UE5: UStaticMesh (FStaticMeshLODResources), UMaterialInstanceDynamic, PCG.
# =============================================================================

@dataclass
class Vertex:
    """One vertex of the vertex buffer — FStaticMeshBuildVertex."""
    px: float; py: float; pz: float          # position
    nx: float; ny: float; nz: float          # normal
    u: float; v: float                       # uv0
    tx: float = 1.0; ty: float = 0.0; tz: float = 0.0   # tangent


@dataclass
class MeshData:
    """CPU-side mesh: vertex buffer + index buffer + LOD chain.
    ~ FStaticMeshRenderData with LODResources[]."""
    name: str
    vertices: list = field(default_factory=list)     # list[Vertex]
    indices: list = field(default_factory=list)      # triangle list, CCW
    lods: list = field(default_factory=list)         # [(screen_size, index_count)]

    def triangle_count(self) -> int:
        return len(self.indices) // 3


def make_grid_mesh(name: str, size_m: float, cells: int,
                   height_fn: Callable[[float, float], float]) -> MeshData:
    """Terrain patch: displaced grid with analytic normals from central
    differences — UE5: Landscape component / PCG HeightField."""
    m = MeshData(name)
    step = size_m / cells
    h = 0.5 * size_m
    for iy in range(cells + 1):
        for ix in range(cells + 1):
            x, y = ix * step - h, iy * step - h
            z = height_fn(x, y)
            e = 0.25
            nx = height_fn(x - e, y) - height_fn(x + e, y)
            ny = height_fn(x, y - e) - height_fn(x, y + e)
            n = V3(nx, ny, 2.0 * e).normalized()
            m.vertices.append(Vertex(x, y, z, n.x, n.y, n.z, ix / cells, iy / cells))
    for iy in range(cells):
        for ix in range(cells):
            a = iy * (cells + 1) + ix
            b, c, d = a + 1, a + cells + 1, a + cells + 2
            m.indices += [a, c, b, b, c, d]
    full = len(m.indices)
    m.lods = [(1.0, full), (0.5, full // 4), (0.2, full // 16)]   # quadric-simplify
    return m


def make_icosphere(name: str, radius: float, subdiv: int = 1) -> MeshData:
    """Rocks, moonlets, the Erisaid fragments — ~ modeled asset stand-in."""
    t = (1.0 + math.sqrt(5.0)) / 2.0
    pts = [V3(-1, t, 0), V3(1, t, 0), V3(-1, -t, 0), V3(1, -t, 0),
           V3(0, -1, t), V3(0, 1, t), V3(0, -1, -t), V3(0, 1, -t),
           V3(t, 0, -1), V3(t, 0, 1), V3(-t, 0, -1), V3(-t, 0, 1)]
    faces = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
             (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
             (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
             (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    for _ in range(subdiv):
        new_faces, cache = [], {}
        def midpoint(i, j):
            key = (min(i, j), max(i, j))
            if key not in cache:
                cache[key] = len(pts)
                pts.append(((pts[i] + pts[j]) * 0.5).normalized() * pts[i].length())
            return cache[key]
        for (a, b, c) in faces:
            ab, bc, ca = midpoint(a, b), midpoint(b, c), midpoint(c, a)
            new_faces += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        faces = new_faces
    m = MeshData(name)
    for p in pts:
        n = p.normalized()
        u = 0.5 + math.atan2(n.y, n.x) / TAU
        v = 0.5 - math.asin(clamp(n.z, -1, 1)) / math.pi
        m.vertices.append(Vertex(n.x * radius, n.y * radius, n.z * radius,
                                 n.x, n.y, n.z, u, v))
    for f in faces:
        m.indices += list(f)
    m.lods = [(1.0, len(m.indices))]
    return m


def make_erisaid_shell(name: str = "SM_Erisaid") -> MeshData:
    """The half-buried leviathan shell: superellipse ridge-loft, 18 m long.
    The 'face' triangles (u in [0.42,0.58], v>0.65) get M_ErisaidMirror."""
    m = MeshData(name)
    rings, segs = 24, 32
    for i in range(rings + 1):
        v = i / rings
        rx = 9.0 * (math.sin(math.pi * v) ** 0.7)          # length profile
        rz = 4.0 * (math.sin(math.pi * v) ** 0.9)
        for j in range(segs + 1):
            u = j / segs
            a = math.pi * u                                # half-shell (buried below)
            x = (v - 0.5) * 18.0
            y = math.cos(a) * rx * 0.45
            z = math.sin(a) * rz
            ridge = 0.25 * math.sin(v * 34.0) * smoothstep(0.1, 0.9, v)
            n = V3(0.0, math.cos(a), math.sin(a)).normalized()
            m.vertices.append(Vertex(x, y, z + ridge, n.x, n.y, n.z, u, v))
    for i in range(rings):
        for j in range(segs):
            a = i * (segs + 1) + j
            b, c, d = a + 1, a + segs + 1, a + segs + 2
            m.indices += [a, c, b, b, c, d]
    m.lods = [(1.0, len(m.indices)), (0.3, len(m.indices) // 4)]
    return m


@dataclass
class MaterialPBR:
    """~ UMaterialInstanceDynamic parameters. Scalar/vector params by name —
    exactly what SetScalarParameterValue would drive at runtime."""
    name: str
    base_color: tuple = (0.5, 0.5, 0.5)
    metallic: float = 0.0
    roughness: float = 0.85
    normal_strength: float = 1.0
    emissive: tuple = (0.0, 0.0, 0.0)
    emissive_intensity: float = 0.0
    # dust layer (the researched accumulation mask — §12 GroundSystem feeds age)
    dust_mask_enabled: bool = False
    dust_tint: tuple = (0.72, 0.62, 0.50)

    def dust_mask(self, normal_z: float, wx: float, wy: float, age_h: float) -> float:
        """DustMask = saturate(N.z)^2 * crevice_fbm * saturate(age*rate).
        UE5: material function MF_DustAccumulation (vertex normal + world pos)."""
        up = clamp(normal_z, 0.0, 1.0) ** 2.0
        crev = fbm2(wx * 0.13, wy * 0.13, 4, seed=99)
        age = clamp(age_h * 0.02, 0.0, 1.0)
        return clamp(up * (0.4 + 0.6 * crev) * age, 0.0, 1.0)


class AssetRegistry:
    """~ FAssetRegistry + StreamableManager: everything procedural, no disk."""

    def __init__(self, seed: int):
        yard_height = lambda x, y: fbm2(x * 0.02, y * 0.02, 4, seed) * 2.2
        self.meshes: dict[str, MeshData] = {
            "SM_YardPatch": make_grid_mesh("SM_YardPatch", 64.0, 32, yard_height),
            "SM_Rock": make_icosphere("SM_Rock", 0.8, 1),
            "SM_Moonlet": make_icosphere("SM_Moonlet", 40.0, 2),
            "SM_Erisaid": make_erisaid_shell(),
            "SM_HabitatDome": make_icosphere("SM_HabitatDome", 4.0, 2),
            "SM_Rover": make_icosphere("SM_Rover", 1.4, 1),      # placeholder hull
            "SK_Astronaut": make_icosphere("SK_Astronaut", 0.5, 1),
            "SK_Dot": make_icosphere("SK_Dot", 0.5, 0),
        }
        self.materials: dict[str, MaterialPBR] = {
            "M_Sand": MaterialPBR("M_Sand", (0.62, 0.54, 0.42), 0.0, 0.95,
                                  dust_mask_enabled=True),
            "M_Rock": MaterialPBR("M_Rock", (0.35, 0.33, 0.31), 0.0, 0.9,
                                  dust_mask_enabled=True),
            "M_MetalPad": MaterialPBR("M_MetalPad", (0.6, 0.6, 0.62), 1.0, 0.4,
                                      dust_mask_enabled=True),
            "M_Suit": MaterialPBR("M_Suit", (0.85, 0.85, 0.88), 0.2, 0.6),
            "M_ErisaidShell": MaterialPBR("M_ErisaidShell", (0.18, 0.2, 0.22),
                                          0.7, 0.35, dust_mask_enabled=True),
            "M_ErisaidMirror": MaterialPBR("M_ErisaidMirror", (0.05, 0.05, 0.06),
                                           1.0, 0.05),   # planar-reflection face
            "M_HabGlass": MaterialPBR("M_HabGlass", (0.7, 0.8, 0.9), 0.0, 0.1),
            "M_StarBillboard": MaterialPBR("M_StarBillboard", (0, 0, 0), 0, 1,
                                           emissive=(1.0, 0.97, 0.9),
                                           emissive_intensity=1.0),
        }


# =============================================================================
# §5. RENDERING — camera, frustum culling, cascaded shadows, GI, post, VFX
# UE5: deferred renderer + Lumen + Niagara. Here: the exact math a frame runs.
# =============================================================================

@dataclass
class CameraState:
    """~ APlayerCameraManager output: the final view for this frame."""
    eye: V3 = field(default_factory=lambda: V3(0, 0, 1.62))
    yaw: float = 0.0
    pitch: float = 0.0
    fov_y: float = 92.0
    fov_velocity: float = 0.0      # spring toward sprint FOV
    bob_z: float = 0.0
    bob_velocity: float = 0.0

    def view_matrix(self) -> Mat4:
        f = Quat.from_yaw_pitch(self.yaw, self.pitch).forward()
        return Mat4.look_at(self.eye + V3(0, 0, self.bob_z),
                            self.eye + V3(0, 0, self.bob_z) + f)

    def proj_matrix(self, aspect: float = 16 / 9) -> Mat4:
        return Mat4.perspective(self.fov_y, aspect, 0.1, 20000.0)


class Frustum:
    """Six planes extracted from view*proj (Gribb–Hartmann) — exactly what
    UE's FConvexVolume does for primitive culling."""

    def __init__(self, vp: Mat4):
        m = vp.m
        self.planes = []
        for sign, row in ((1, 0), (-1, 0), (1, 1), (-1, 1), (1, 2), (-1, 2)):
            a = m[3][0] + sign * m[row][0]
            b = m[3][1] + sign * m[row][1]
            c = m[3][2] + sign * m[row][2]
            d = m[3][3] + sign * m[row][3]
            n = math.sqrt(a * a + b * b + c * c) + EPS
            self.planes.append((a / n, b / n, c / n, d / n))

    def sphere_visible(self, center: V3, radius: float) -> bool:
        for (a, b, c, d) in self.planes:
            if a * center.x + b * center.y + c * center.z + d < -radius:
                return False
        return True


class ShadowCascades:
    """Cascaded shadow maps for the sun: split the view range, fit an ortho
    light-space matrix per cascade — ~ r.Shadow.CSM settings + Lumen shadows."""
    SPLITS = (0.0, 12.0, 48.0, 200.0)      # meters; 3 cascades

    def build(self, cam: CameraState, sun_dir: V3) -> list[Mat4]:
        mats = []
        f = Quat.from_yaw_pitch(cam.yaw, cam.pitch).forward()
        for i in range(len(self.SPLITS) - 1):
            near, far = self.SPLITS[i], self.SPLITS[i + 1]
            center = cam.eye + f * ((near + far) * 0.5)
            half = (far - near) * 0.75
            eye = center - sun_dir * 500.0
            mats.append(Mat4.ortho(half, half, 1.0, 1500.0)
                        @ Mat4.look_at(eye, center))
        return mats


class IrradianceField:
    """Lumen stand-in: a coarse world-space irradiance probe grid. Each probe
    stores sky visibility + one ground bounce; sampling is trilinear-ish.
    UE5: Lumen radiance cache / screen probes — here, the honest math shape."""
    PROBE_SPACING = 16.0

    def __init__(self):
        self.probes: dict[tuple, float] = {}     # cell -> irradiance scalar

    def bake_region(self, center: V3, radius: float, sun_elev_deg: float,
                    albedo: float = 0.35, memorial_light: float = 0.0) -> None:
        sky = max(0.0, math.sin(math.radians(max(sun_elev_deg, 0.0))))
        c = int(radius / self.PROBE_SPACING)
        cx, cy = int(center.x / self.PROBE_SPACING), int(center.y / self.PROBE_SPACING)
        for dx in range(-c, c + 1):
            for dy in range(-c, c + 1):
                direct = sky
                bounce = direct * albedo * 0.5           # one diffuse bounce
                ancestors = memorial_light                # bright stars light night
                self.probes[(cx + dx, cy + dy)] = direct + bounce + ancestors

    def sample(self, p: V3) -> float:
        k = (int(p.x / self.PROBE_SPACING), int(p.y / self.PROBE_SPACING))
        return self.probes.get(k, 0.05)


@dataclass
class PostProcessSettings:
    """~ FPostProcessSettings on a global PostProcessVolume."""
    exposure_ev: float = 0.0            # auto-adapted below
    exposure_speed: float = 1.5         # EV/s adaptation
    bloom_threshold: float = 1.1
    bloom_intensity: float = 0.35
    vignette: float = 0.25
    grain: float = 0.04
    grade_shadows: tuple = (0.98, 0.99, 1.06)   # cold nights
    grade_highlights: tuple = (1.05, 1.0, 0.94)  # warm regolith days

    def adapt(self, scene_luminance: float, dt: float) -> None:
        target = clamp(-math.log2(max(scene_luminance, 0.01)), -2.0, 8.0)
        self.exposure_ev = lerp(self.exposure_ev, target,
                                clamp(self.exposure_speed * dt, 0, 1))


# --- Niagara: data-driven particle systems ----------------------------------

@dataclass
class EmitterSpec:
    """~ UNiagaraSystem asset: spawn + per-particle update curves."""
    name: str
    burst: int = 0
    rate_per_s: float = 0.0
    lifetime_s: tuple = (0.6, 1.2)
    speed: tuple = (0.5, 1.5)
    cone_deg: float = 40.0
    size_m: tuple = (0.05, 0.25)
    size_over_life: tuple = (1.0, 2.6)      # grows as it fades
    gravity_scale: float = 0.15             # regolith dust hangs in low-g
    drag: float = 1.2
    wind_influence: float = 0.0
    color: tuple = (0.72, 0.62, 0.5)
    fade_in: float = 0.05
    die_on_ground: bool = True


NIAGARA_LIBRARY: dict[str, EmitterSpec] = {
    "FX_DustPuff": EmitterSpec("FX_DustPuff", burst=14, speed=(0.4, 1.4),
                               cone_deg=70.0),
    "FX_SandDrift": EmitterSpec("FX_SandDrift", rate_per_s=60.0,
                                lifetime_s=(2.0, 5.0), speed=(0.0, 0.3),
                                wind_influence=1.0, gravity_scale=0.02,
                                size_m=(0.4, 1.6), die_on_ground=False),
    "FX_FootstepRing": EmitterSpec("FX_FootstepRing", burst=1,
                                   lifetime_s=(0.5, 0.5), speed=(0.0, 0.0),
                                   size_m=(0.3, 0.3), size_over_life=(1.0, 4.0),
                                   color=(0.9, 0.9, 1.0)),  # accessibility pulse
    "FX_StormWall": EmitterSpec("FX_StormWall", rate_per_s=400.0,
                                lifetime_s=(1.0, 2.0), speed=(6.0, 14.0),
                                wind_influence=1.0, size_m=(1.0, 3.0),
                                gravity_scale=0.0, die_on_ground=False),
    "FX_ThrusterPlume": EmitterSpec("FX_ThrusterPlume", rate_per_s=200.0,
                                    lifetime_s=(0.2, 0.5), speed=(8.0, 16.0),
                                    cone_deg=12.0, color=(1.0, 0.8, 0.4),
                                    gravity_scale=0.0),
    "FX_DigBurst": EmitterSpec("FX_DigBurst", burst=30, speed=(1.0, 3.0),
                               cone_deg=55.0, size_m=(0.08, 0.4)),
}


@dataclass
class Particle:
    pos: V3
    vel: V3
    age: float
    life: float
    size: float


class ParticleSimulator(System):
    """CPU Niagara: spawns from ParticleEmitterRef components + one-shot
    bursts requested via spawn_burst(). Wind advects; ground kills."""
    GROUP = TickGroup.RENDER
    ORDER = 0
    MAX_PARTICLES = 4000

    def __init__(self, rng: random.Random):
        self.rng = rng
        self.live: list[tuple[EmitterSpec, Particle]] = []
        self.wind = V3()

    def spawn_burst(self, spec_id: str, pos: V3, scale: float = 1.0) -> None:
        spec = NIAGARA_LIBRARY[spec_id]
        for _ in range(int(spec.burst * scale) or spec.burst):
            self._emit(spec, pos)

    def _emit(self, spec: EmitterSpec, pos: V3) -> None:
        if len(self.live) >= self.MAX_PARTICLES:
            return
        a = self.rng.uniform(0, TAU)
        tilt = math.radians(self.rng.uniform(0, spec.cone_deg))
        speed = self.rng.uniform(*spec.speed)
        vel = V3(math.cos(a) * math.sin(tilt), math.sin(a) * math.sin(tilt),
                 math.cos(tilt)) * speed
        self.live.append((spec, Particle(
            V3(pos.x, pos.y, pos.z), vel, 0.0,
            self.rng.uniform(*spec.lifetime_s), self.rng.uniform(*spec.size_m))))

    def tick(self, game: "ChimeraGame", dt: float) -> None:
        self.wind = game.weather.wind_vector()
        for eid, tr, em in game.world.query(Transform, ParticleEmitterRef):
            spec = NIAGARA_LIBRARY[em.spec_id]
            if em.active and spec.rate_per_s > 0:
                n = spec.rate_per_s * em.rate_scale * dt
                whole = int(n) + (1 if self.rng.random() < (n - int(n)) else 0)
                for _ in range(whole):
                    self._emit(spec, tr.pos)
        alive = []
        g = 1.62
        for spec, p in self.live:
            p.age += dt
            if p.age >= p.life:
                continue
            p.vel = p.vel + self.wind * (spec.wind_influence * dt)
            p.vel.z -= g * spec.gravity_scale * dt
            p.vel = p.vel * math.exp(-spec.drag * dt)
            p.pos = p.pos + p.vel * dt
            if spec.die_on_ground and p.pos.z <= 0.02:
                continue
            alive.append((spec, p))
        self.live = alive


class RenderPipeline(System):
    """One frame, deferred-style pass order — counts what a GPU would do:
      0 shadow cascades -> 1 opaque base pass (frustum-culled, LOD-picked)
      -> 2 lighting (irradiance sample) -> 3 translucent/particles
      -> 4 starfield memorial -> 5 post (exposure/bloom/grade).
    Runs headless: emits RenderStats instead of pixels."""
    GROUP = TickGroup.RENDER
    ORDER = 1

    def __init__(self, assets: AssetRegistry):
        self.assets = assets
        self.cascades = ShadowCascades()
        self.gi = IrradianceField()
        self.post = PostProcessSettings()
        self.stats = dict(frames=0, draws=0, culled=0, tris=0, particles=0,
                          shadow_views=0)

    def pick_lod(self, mesh: MeshData, dist: float) -> int:
        screen_size = clamp(4.0 / max(dist, 0.1), 0.0, 1.0)
        for li, (threshold, _count) in enumerate(mesh.lods):
            if screen_size >= threshold * 0.5:
                return li
        return len(mesh.lods) - 1

    def tick(self, game: "ChimeraGame", dt: float) -> None:
        cam = game.camera
        vp = cam.proj_matrix() @ cam.view_matrix()
        frustum = Frustum(vp)
        sun_dir = game.sky.sun_direction()
        self.stats["shadow_views"] += len(self.cascades.build(cam, sun_dir))
        # base pass with culling + LOD
        for eid, tr, mesh_ref in game.world.query(Transform, StaticMeshRef):
            mesh = self.assets.meshes.get(mesh_ref.mesh_id)
            if mesh is None:
                continue
            r = mesh_ref.bounds_radius * tr.scale
            if not frustum.sphere_visible(tr.pos, r):
                self.stats["culled"] += 1
                continue
            lod = self.pick_lod(mesh, cam.eye.dist(tr.pos))
            self.stats["draws"] += 1
            self.stats["tris"] += mesh.lods[lod][1] // 3
        for eid, tr, _sk in game.world.query(Transform, SkeletalMeshRef):
            if frustum.sphere_visible(tr.pos, 1.0):
                self.stats["draws"] += 1
        # lighting: sample GI at camera for exposure adaptation
        lum = self.gi.sample(cam.eye) + 0.05
        self.post.adapt(lum, dt)
        # translucency
        self.stats["particles"] += len(game.particles.live)
        # starfield memorial: one instanced draw, N stars
        if game.sky.is_night and game.memorial.stars:
            self.stats["draws"] += 1
        self.stats["frames"] += 1


# =============================================================================
# §6. PHYSICS — heightfield collision, capsule move, gravity volumes, traces
# UE5: Chaos scene queries + UCharacterMovementComponent::PerformMovement.
# =============================================================================

GRAVITY_YARD = 1.62            # m/s^2 — lunar-class planetoid
GRAVITY_TITAN_ZONE = 1.35      # Titan Run anomaly corridors

MOVE = dict(
    walk_speed=1.4, jog_speed=3.2, sprint_speed=5.6, bend_speed=0.7,
    accel=6.0, air_control=0.35,
    jump_height=1.1, coyote_time_s=0.12, jump_buffer_s=0.15,
    step_interval_walk_s=0.62, step_interval_sprint_s=0.38,
    slide_slope_deg=38.0,
)


@dataclass
class MoveInput:
    """One quantum of player intent — ~ FSavedMove_Character. seq numbers make
    §11 client prediction/reconciliation possible."""
    seq: int = 0
    move: V3 = field(default_factory=V3)       # stick, |v|<=1
    yaw: float = 0.0                           # absolute view yaw
    pitch: float = 0.0
    jump: bool = False
    bend: bool = False
    sprint: bool = False
    dt: float = 1.0 / 60.0


@dataclass
class MoveState:
    """Deterministic movement state — the thing the server owns and the
    client predicts. MUST stay plain-data (copyable) for rewind/replay."""
    pos: V3 = field(default_factory=V3)
    vel: V3 = field(default_factory=V3)
    grounded: bool = True
    gait: Gait = Gait.IDLE
    step_clock: float = 0.0
    left_foot_next: bool = True
    left_ground_at: float = -999.0
    jump_pressed_at: float = -999.0
    now: float = 0.0

    def copy(self) -> "MoveState":
        return MoveState(V3(*self.pos.to_tuple()), V3(*self.vel.to_tuple()),
                         self.grounded, self.gait, self.step_clock,
                         self.left_foot_next, self.left_ground_at,
                         self.jump_pressed_at, self.now)


class GravityField:
    """Stack of gravity volumes — ~ APhysicsVolume overrides. The Titan Run
    registers its alternating corridors here; transitions LERP (1.2 s) so the
    body can read the change (never snap)."""

    def __init__(self):
        self.zones: list[tuple[Callable[[V3], bool], float]] = []
        self._current = GRAVITY_YARD

    def add_zone(self, contains: Callable[[V3], bool], g: float) -> None:
        self.zones.append((contains, g))

    def sample(self, p: V3, dt: float) -> float:
        target = GRAVITY_YARD
        for contains, g in self.zones:
            if contains(p):
                target = g
                break
        self._current = lerp(self._current, target, clamp(dt / 1.2, 0, 1))
        return self._current


def movement_step(state: MoveState, inp: MoveInput, ground: "GroundField",
                  gravity: float, speed_scale: float,
                  footsteps_out: Optional[list] = None) -> MoveState:
    """THE pure movement solver — one function used by BOTH the server sim and
    client prediction (§11). UE5: UCharacterMovementComponent::PerformMovement;
    determinism here == smooth reconciliation there."""
    s = state.copy()
    s.now += inp.dt
    # --- gait selection
    mag = inp.move.length2d()
    if inp.bend:
        s.gait = Gait.BEND
    elif mag < 0.05:
        s.gait = Gait.IDLE
    elif inp.sprint and mag > 0.5:
        s.gait = Gait.SPRINT
    elif mag > 0.55:
        s.gait = Gait.JOG
    else:
        s.gait = Gait.WALK
    base = {Gait.IDLE: 0.0, Gait.WALK: MOVE["walk_speed"], Gait.JOG: MOVE["jog_speed"],
            Gait.SPRINT: MOVE["sprint_speed"], Gait.BEND: MOVE["bend_speed"]}[s.gait]
    surface = ground.surface_at(s.pos)
    basin_pen = 0.55 if surface == Surface.BASIN else 1.0
    max_speed = base * basin_pen * speed_scale
    # --- planar accelerate (stick is in view space; rotate by yaw)
    cy, sy = math.cos(inp.yaw), math.sin(inp.yaw)
    want = V3(inp.move.x * cy - inp.move.y * sy,
              inp.move.x * sy + inp.move.y * cy, 0.0) * max_speed
    control = 1.0 if s.grounded else MOVE["air_control"]
    blend = clamp(MOVE["accel"] * ground.traction_at(s.pos) * control * inp.dt, 0, 1)
    s.vel.x = lerp(s.vel.x, want.x, blend)
    s.vel.y = lerp(s.vel.y, want.y, blend)
    # --- jump with coyote + buffer (input forgiveness)
    if inp.jump:
        s.jump_pressed_at = s.now
    buffered = (s.now - s.jump_pressed_at) <= MOVE["jump_buffer_s"]
    coyote = (s.now - s.left_ground_at) <= MOVE["coyote_time_s"]
    if buffered and (s.grounded or coyote):
        s.vel.z = math.sqrt(2.0 * gravity * MOVE["jump_height"])
        s.grounded = False
        s.jump_pressed_at = -999.0
        s.left_ground_at = -999.0
    # --- integrate + heightfield resolve (capsule sweep in UE5)
    if not s.grounded:
        s.vel.z -= gravity * inp.dt
    s.pos = s.pos + s.vel * inp.dt
    floor = ground.height_at(s.pos)
    if s.pos.z <= floor:
        if not s.grounded and s.vel.z < -1.0 and footsteps_out is not None:
            footsteps_out.append(("land", s.pos, surface, s.left_foot_next,
                                  s.vel.length2d(), s.now))
        s.pos.z, s.vel.z, s.grounded = floor, 0.0, True
    elif s.grounded and s.pos.z > floor + 0.05:
        s.grounded = False
        s.left_ground_at = s.now
    # --- footstep cadence: contacts at stride phase; ONE event stream (Law 1)
    speed2d = s.vel.length2d()
    if s.grounded and speed2d > 0.2:
        interval = lerp(MOVE["step_interval_walk_s"], MOVE["step_interval_sprint_s"],
                        speed2d / MOVE["sprint_speed"])
        s.step_clock += inp.dt
        if s.step_clock >= interval:
            s.step_clock = 0.0
            if footsteps_out is not None:
                footsteps_out.append(("step", s.pos, surface, s.left_foot_next,
                                      speed2d, s.now))
            s.left_foot_next = not s.left_foot_next
    else:
        s.step_clock = 0.0
    return s


def line_trace(ground: "GroundField", start: V3, direction: V3,
               max_dist: float, step: float = 0.5) -> Optional[V3]:
    """Ray-march vs heightfield — ~ UWorld::LineTraceSingleByChannel.
    Used by dig target, scanner LOS, weapon fire, audio occlusion."""
    d = direction.normalized()
    t = 0.0
    while t <= max_dist:
        p = start + d * t
        if p.z <= ground.height_at(p):
            return p
        t += step
    return None


@dataclass
class Projectile:
    """~ AProjectileActor with UProjectileMovementComponent (ballistic)."""
    pos: V3
    vel: V3
    damage: float = 34.0
    alive: bool = True

    def step(self, dt: float, gravity: float, ground: "GroundField") -> Optional[V3]:
        self.vel.z -= gravity * dt
        self.pos = self.pos + self.vel * dt
        if self.pos.z <= ground.height_at(self.pos):
            self.alive = False
            return self.pos
        return None


# =============================================================================
# §7. SPATIAL AUDIO — attenuation, panning, occlusion, reverb, mix, music
# UE5: MetaSounds + Sound Attenuation assets + Audio Volumes + Submixes.
# =============================================================================

WIND = dict(calm=2.0, breeze=6.0, gust=12.0, storm=24.0,
            gust_period_s=(8.0, 30.0), storm_duration_min=(18.0, 45.0),
            storm_period_days=(5.0, 9.0))


@dataclass
class Listener:
    """~ the audio device listener: camera pos + orientation."""
    pos: V3 = field(default_factory=V3)
    yaw: float = 0.0

    def right(self) -> V3:
        return V3(-math.sin(self.yaw), math.cos(self.yaw), 0.0)

    def forward(self) -> V3:
        return V3(math.cos(self.yaw), math.sin(self.yaw), 0.0)


def spatialize(listener: Listener, src_pos: V3, min_r: float, max_r: float,
               occluded: bool) -> tuple[float, float, float]:
    """Return (gain, pan, lpf_cutoff_hz) — the whole 3D voice math.
    Attenuation: natural-sound curve (inverse-square inside knee, linear tail);
    Pan: dot with listener right vector; LPF: distance + occlusion darken."""
    d = listener.pos.dist(src_pos)
    if d <= min_r:
        gain = 1.0
    elif d >= max_r:
        gain = 0.0
    else:
        knee = min_r * 4.0
        if d <= knee:
            gain = (min_r / d) ** 2 * 0.5 + 0.5 * (1.0 - inv_lerp(min_r, knee, d))
        else:
            gain = 0.5 * (1.0 - inv_lerp(knee, max_r, d))
        gain = clamp(gain, 0.0, 1.0)
    to_src = (src_pos - listener.pos).normalized()
    pan = clamp(to_src.dot(listener.right()), -1.0, 1.0)
    lpf = lerp(18000.0, 2200.0, inv_lerp(min_r, max_r, d))
    if occluded:
        lpf = min(lpf, 900.0)          # ~ UE occlusion LPF
        gain *= 0.45
    return gain, pan, lpf


class SubmixGraph:
    """~ USoundSubmix tree with sidechain ducking:
       master
         ├─ music     (ducked by storm, by suit alarm)
         ├─ ambience  (wind layers, hums, thunder)
         ├─ sfx       (footsteps, tools, gestures)
         └─ ui        (menu ticks; never spatialized)"""

    def __init__(self):
        self.gains = dict(master=1.0, music=0.8, ambience=0.9, sfx=1.0, ui=0.7)
        self.duck = dict(music=1.0)

    def tick(self, storm_active: bool, o2_fraction: float, dt: float) -> None:
        duck_target = 0.35 if storm_active else 1.0
        if o2_fraction < 0.25:
            duck_target = min(duck_target, 0.25)   # emergency: hear your breath
        self.duck["music"] = lerp(self.duck["music"], duck_target,
                                  clamp(2.0 * dt, 0, 1))

    def bus_gain(self, bus: str) -> float:
        return self.gains["master"] * self.gains.get(bus, 1.0) * self.duck.get(bus, 1.0)


class DynamicMusicSystem(System):
    """Vertical-layer score — ~ MetaSounds stem mixer driven by game state.
    Stems fade on director phase + threat; harmonic key follows Earth phase
    (the sky is the conductor). Wordless game => music carries the narrative."""
    GROUP = TickGroup.AUDIO
    ORDER = 2
    STEMS = ("calm_pad", "day_pulse", "dusk_strings", "night_choir", "storm_drums")

    def __init__(self):
        self.levels = {s: 0.0 for s in self.STEMS}
        self.key_root_hz = 220.0

    def tick(self, game: "ChimeraGame", dt: float) -> None:
        phase = game.director.phase(game.sky)
        threat = 1.0 if any(b.archetype == "pirate" and b.fsm != "gone"
                            for _e, b in game.world.query(DotBrain)) else 0.0
        targets = {
            "calm_pad": 0.7 if phase in ("dawn", "day") else 0.3,
            "day_pulse": 0.6 if phase == "day" else 0.0,
            "dusk_strings": 0.8 if phase == "dusk" else 0.0,
            "night_choir": 0.7 if phase == "night" else 0.0,
            "storm_drums": 0.9 if game.weather.storm_active or threat > 0 else 0.0,
        }
        for stem, tgt in targets.items():
            rate = 0.5 if tgt > self.levels[stem] else 0.25     # slow releases
            self.levels[stem] = lerp(self.levels[stem], tgt, clamp(rate * dt, 0, 1))
        # key drifts a whole step across the Earth-phase month
        self.key_root_hz = 220.0 * (2.0 ** (game.sky.earth_phase * 2.0 / 12.0))


@dataclass
class FootstepAudioEvent:
    t: float
    surface: "Surface"
    latency_ms: float
    volume: float
    pan: float


class SandSoundSystem(System):
    """~ USandSoundComponent (manual-lane C++), attached AT RUNTIME by the
    movement component's BeginPlay if missing (the H-31/H-34 fix), so no
    Blueprint wiring can silently drop it. Subscribes to FootstepEvent and
    owns wind layers + the MCP-queried telemetry accessors (tb-0001)."""
    GROUP = TickGroup.AUDIO
    ORDER = 1

    BANKS = {
        "Fantozzi-Sand":  ["SandL1", "SandL2", "SandL3", "SandR1", "SandR2", "SandR3"],
        "Fantozzi-Stone": ["StoneL1", "StoneL2", "StoneL3", "StoneR1", "StoneR2", "StoneR3"],
        "Metal-Scuff":    ["MetalL1", "MetalR1"],
        "Ice-Crunch":     ["IceL1", "IceR1"],
        "Interior-Soft":  ["SoftL1", "SoftR1"],
    }

    def __init__(self, rng: random.Random):
        self.rng = rng
        self.events: list[FootstepAudioEvent] = []
        self.wind_speed = WIND["calm"]
        self.listener = Listener()

    def bind(self, bus: EventBus) -> None:
        bus.subscribe(FootstepEvent, self.on_footstep)

    def on_footstep(self, ev: FootstepEvent) -> None:
        bank_name = SURFACE_TABLE[ev.surface][4]
        cues = [c for c in self.BANKS.get(bank_name, ["SandL1"])
                if ("L" in c) == ev.left_foot]
        cue = self.rng.choice(cues)
        volume = 1.0 if ev.landing else clamp(
            0.35 + 0.65 * ev.speed / MOVE["sprint_speed"], 0.0, 1.0)
        gain, pan, _lpf = spatialize(self.listener, ev.pos, 1.0, 30.0, False)
        latency_ms = self.rng.uniform(2.0, 14.0)   # UE5: measured anim->audio gap
        self.events.append(FootstepAudioEvent(ev.t, ev.surface, latency_ms,
                                              volume, pan))
        _ = cue   # UE5: PlaySoundAtLocation(cue, pos, volume*gain, pitch 0.92..1.08)

    def wind_layers(self) -> dict:
        """3 MetaSound layers driven by wind speed — the ambience bed."""
        w = self.wind_speed
        return {"low_rumble": clamp(w / WIND["storm"], 0.05, 1.0),
                "mid_rush": clamp((w - 4.0) / (WIND["storm"] - 4.0), 0.0, 1.0),
                "high_whistle": clamp((w - 10.0) / (WIND["storm"] - 10.0), 0.0, 1.0),
                "pitch": lerp(0.9, 1.35, w / WIND["storm"])}

    def tick(self, game: "ChimeraGame", dt: float) -> None:
        self.wind_speed = game.weather.wind_speed
        ptr = game.world.get(game.player_eid, Transform)
        self.listener.pos = ptr.pos + V3(0, 0, 1.62)
        self.listener.yaw = ptr.yaw

    # ---- TELEMETRY ACCESSORS — names are the MCP bridge contract (tb-0001)
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
        return bool(slow and fast
                    and sum(fast) / len(fast) > sum(slow) / len(slow))

    def ClearFootstepSyncTelemetry(self) -> None:
        self.events.clear()


ERISAID = dict(
    hum_base_hz=41.0,
    harmonics=(1.0, 2.667, 4.333),
    dial_tolerance_hz=0.8,
    hold_to_lock_s=2.0,
    facing_cos_min=0.90,            # must FACE the emitter to isolate it
    attune_visits_min=3,            # across >= 3 distinct days
    deaf_days_after_gunfire=30,
    mirror_reveal_radius_m=3.0,
)


class AttunementMinigame(System):
    """THE AUDIO MINIGAME, fully spatial. Three hum emitters sit at different
    points on the Erisaid's shell, each sounding one harmonic of 41 Hz. To
    isolate a harmonic you must FACE its emitter (binaural isolation: the pan
    math above collapses the other two to the sides); then turn the suit-radio
    dial until the BEAT FREQUENCY — |dial - target| Hz, rendered as an audible
    wobble — slows to stillness. Hold stillness 2 s to lock. Three locks across
    three different days = attunement. Firing a weapon nearby deafens it 30
    days. UE5: MetaSound with two oscillators; wobble = their difference tone."""
    GROUP = TickGroup.AUDIO
    ORDER = 3

    def __init__(self):
        self.emitter_offsets = [V3(-6.0, 1.5, 2.0), V3(0.0, 2.2, 3.4),
                                V3(6.0, 1.8, 2.6)]
        self.matched: set[int] = set()
        self.visit_days: set[int] = set()
        self.deaf_until_day = -1
        self.dial_hz = 35.0
        self._hold_t = 0.0
        self._active_idx: Optional[int] = None

    def targets(self) -> list[float]:
        return [ERISAID["hum_base_hz"] * r for r in ERISAID["harmonics"]]

    @property
    def attuned(self) -> bool:
        return (len(self.matched) == len(ERISAID["harmonics"])
                and len(self.visit_days) >= ERISAID["attune_visits_min"])

    def beat_wobble_hz(self, idx: int) -> float:
        """The diegetic feedback: how fast the hum 'wobbles' at your dial."""
        return abs(self.dial_hz - self.targets()[idx])

    def tick(self, game: "ChimeraGame", dt: float) -> None:
        if game.sky.day < self.deaf_until_day:
            return                                  # silence: the cost of a shot
        ptr = game.world.get(game.player_eid, Transform)
        base = game.erisaid_pos
        if ptr.pos.dist2d(base) > 25.0:
            self._active_idx, self._hold_t = None, 0.0
            return
        self.visit_days.add(game.sky.day)
        fwd = ptr.forward()
        # which emitter is the player isolating? (facing gate)
        best, best_cos = None, ERISAID["facing_cos_min"]
        for i, off in enumerate(self.emitter_offsets):
            to_e = ((base + off) - ptr.pos).normalized()
            c = fwd.dot(V3(to_e.x, to_e.y, 0.0).normalized())
            if c > best_cos:
                best, best_cos = i, c
        if best is None or best in self.matched:
            self._active_idx, self._hold_t = None, 0.0
            return
        self._active_idx = best
        if self.beat_wobble_hz(best) <= ERISAID["dial_tolerance_hz"]:
            self._hold_t += dt
            if self._hold_t >= ERISAID["hold_to_lock_s"]:
                self.matched.add(best)               # a felt CLUNK in the chest
                self._hold_t = 0.0
        else:
            self._hold_t = 0.0

    def on_gunfire_nearby(self, day: int) -> None:
        self.deaf_until_day = day + ERISAID["deaf_days_after_gunfire"]


# =============================================================================
# §8. AI — Behavior Trees + coarse FSM + NavMesh A* + steering
# UE5: UBehaviorTreeComponent/UBlackboardComponent, NavMesh (RecastNavMesh),
# CrowdFollowingComponent (RVO). Trees below ARE the BT assets, as code.
# =============================================================================

class BTStatus(Enum):
    SUCCESS = auto(); FAILURE = auto(); RUNNING = auto()


class BTNode(ABC):
    """~ UBTNode. tick() gets the game, the entity, and its brain."""
    @abstractmethod
    def tick(self, game: "ChimeraGame", eid: EntityId, brain: DotBrain,
             dt: float) -> BTStatus: ...


class Selector(BTNode):
    """First child to not-FAIL wins — ~ UBTComposite_Selector."""
    def __init__(self, *children: BTNode): self.children = children
    def tick(self, game, eid, brain, dt) -> BTStatus:
        for c in self.children:
            st = c.tick(game, eid, brain, dt)
            if st != BTStatus.FAILURE:
                return st
        return BTStatus.FAILURE


class Sequence(BTNode):
    """All children must SUCCEED in order — ~ UBTComposite_Sequence.
    Stateless re-evaluation each tick (simple + robust for pseudocode)."""
    def __init__(self, *children: BTNode): self.children = children
    def tick(self, game, eid, brain, dt) -> BTStatus:
        for c in self.children:
            st = c.tick(game, eid, brain, dt)
            if st != BTStatus.SUCCESS:
                return st
        return BTStatus.SUCCESS


class Condition(BTNode):
    """~ UBTDecorator_Blackboard: SUCCESS iff predicate(bb) holds."""
    def __init__(self, fn: Callable): self.fn = fn
    def tick(self, game, eid, brain, dt) -> BTStatus:
        return BTStatus.SUCCESS if self.fn(game, eid, brain) else BTStatus.FAILURE


class Act(BTNode):
    """~ UBTTaskNode: run a function returning a BTStatus."""
    def __init__(self, fn: Callable): self.fn = fn
    def tick(self, game, eid, brain, dt) -> BTStatus:
        return self.fn(game, eid, brain, dt)


# ---- BT leaf library (the task nodes every archetype composes) --------------

def _player_dist(game: "ChimeraGame", eid: EntityId) -> float:
    return game.world.get(eid, Transform).pos.dist2d(
        game.world.get(game.player_eid, Transform).pos)


def task_seek_player(stop_at: float) -> Callable:
    """Path toward the player; SUCCESS when within stop_at meters."""
    def fn(game, eid, brain, dt) -> BTStatus:
        d = _player_dist(game, eid)
        if d <= stop_at:
            game.world.get(eid, NavAgent).goal = None
            return BTStatus.SUCCESS
        agent = game.world.get(eid, NavAgent)
        agent.goal = game.world.get(game.player_eid, Transform).pos
        brain.fsm = "approaching" if d > 25.0 else "near"
        return BTStatus.RUNNING
    return fn


def task_point_at_need(game, eid, brain, dt) -> BTStatus:
    """The stranger's whole vocabulary: point at what hurts (Law 3)."""
    if brain.need is None:
        return BTStatus.FAILURE
    if brain.fsm != "encounter":
        brain.fsm = "encounter"
        game.world.events.emit(GestureEvent(eid, game.player_eid, "point"))
    return BTStatus.RUNNING          # resolution arrives via GestureEvent


def task_leave(game, eid, brain, dt) -> BTStatus:
    ptr = game.world.get(game.player_eid, Transform).pos
    tr = game.world.get(eid, Transform)
    agent = game.world.get(eid, NavAgent)
    if brain.fsm != "leaving":
        brain.fsm = "leaving"
        away = (tr.pos - ptr).normalized()
        agent.goal = tr.pos + away * 320.0
    if tr.pos.dist2d(ptr) > 300.0:
        brain.fsm = "gone"
        return BTStatus.SUCCESS
    return BTStatus.RUNNING


def task_pirate_demand(game, eid, brain, dt) -> BTStatus:
    """WARN + point at the pack. Player armed & facing => nerve check fails."""
    if brain.bb.get("demanded") is None:
        brain.bb["demanded"] = 0.0
        brain.fsm = "encounter"
        game.flags["threatened_this_life"] = True
        game.world.events.emit(GestureEvent(eid, game.player_eid, "warn"))
    brain.bb["demanded"] += dt
    player_carry = game.world.get(game.player_eid, CarryComponent)
    if game.flags.get("weapon_drawn") and brain.bb["demanded"] > 2.0:
        brain.bb["flee"] = True               # they wanted cargo, not a grave
        return BTStatus.SUCCESS
    if brain.bb["demanded"] > 8.0:
        if player_carry.pack:                  # coerced loss is NOT sacrifice
            player_carry.pack.pop()
        brain.bb["flee"] = True
        return BTStatus.SUCCESS
    return BTStatus.RUNNING


def task_kneel_at_erisaid(game, eid, brain, dt) -> BTStatus:
    agent = game.world.get(eid, NavAgent)
    tr = game.world.get(eid, Transform)
    if tr.pos.dist2d(game.erisaid_pos) > 8.0:
        agent.goal = game.erisaid_pos + spiral_point(eid % 7, 3.0)
        return BTStatus.RUNNING
    brain.fsm = "encounter"                    # kneeling, forever listening
    return BTStatus.RUNNING


BT_LIBRARY: dict[str, BTNode] = {
    # ~ four UBehaviorTree assets, one per archetype
    "BT_Stranger": Selector(
        Sequence(Condition(lambda g, e, b: b.need is not None),
                 Act(task_seek_player(3.5)), Act(task_point_at_need)),
        Act(task_leave)),
    "BT_Trader": Selector(
        Sequence(Condition(lambda g, e, b: _player_dist(g, e) < 60.0
                           and b.bb.get("greeted") is None),
                 Act(task_seek_player(4.0)),
                 Act(lambda g, e, b, dt: (g.world.events.emit(
                     GestureEvent(e, g.player_eid, "wave")),
                     b.bb.__setitem__("greeted", True),
                     BTStatus.SUCCESS)[-1])),
        Act(task_leave)),
    "BT_Pirate": Selector(
        Sequence(Condition(lambda g, e, b: not b.bb.get("flee")),
                 Act(task_seek_player(6.0)), Act(task_pirate_demand)),
        Act(task_leave)),
    "BT_Quiet": Act(task_kneel_at_erisaid),
}


class NavGrid:
    """Recast stand-in: 2 m walkable grid over the Yard. Cost by surface;
    slopes over 38° and deep pits are unwalkable. Rebuilt lazily per region
    (~ navmesh tiles) when the DigGrid changes."""
    CELL = 2.0
    HALF_CELLS = 160          # covers ±320 m

    def __init__(self, ground: "GroundField"):
        self.ground = ground
        self._walk_cache: dict[tuple, bool] = {}    # ~ baked navmesh tiles;
        self._cost_cache: dict[tuple, float] = {}   # invalidated on dig rebuild

    def walkable(self, cx: int, cy: int) -> bool:
        k = (cx, cy)
        hit = self._walk_cache.get(k)
        if hit is not None:
            return hit
        x, y = cx * self.CELL, cy * self.CELL
        h0 = self.ground.height_at(V3(x, y, 0))
        hx = self.ground.height_at(V3(x + self.CELL, y, 0))
        hy = self.ground.height_at(V3(x, y + self.CELL, 0))
        slope = max(abs(hx - h0), abs(hy - h0)) / self.CELL
        ok = slope < math.tan(math.radians(MOVE["slide_slope_deg"]))
        self._walk_cache[k] = ok
        return ok

    def cost(self, cx: int, cy: int) -> float:
        k = (cx, cy)
        hit = self._cost_cache.get(k)
        if hit is not None:
            return hit
        s = self.ground.surface_at(V3(cx * self.CELL, cy * self.CELL, 0))
        c = {Surface.BASIN: 2.5, Surface.SAND: 1.0, Surface.ROCK: 1.2,
             Surface.METAL: 0.9}.get(s, 1.0)
        self._cost_cache[k] = c
        return c

    def astar(self, start: V3, goal: V3, max_expand: int = 4000) -> list:
        """A* with octile heuristic + string-pulling smoothing —
        ~ FindPathSync on RecastNavMesh."""
        import heapq
        s = (round(start.x / self.CELL), round(start.y / self.CELL))
        g = (round(goal.x / self.CELL), round(goal.y / self.CELL))
        if s == g:
            return [goal]
        def h(a, b):
            dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
            return (dx + dy) + (math.sqrt(2) - 2) * min(dx, dy)
        open_q = [(h(s, g), 0.0, s)]
        came: dict = {s: None}
        cost_so_far = {s: 0.0}
        found = False
        while open_q and max_expand > 0:
            max_expand -= 1
            _f, c, cur = heapq.heappop(open_q)
            if cur == g:
                found = True
                break
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nxt = (cur[0] + dx, cur[1] + dy)
                    if abs(nxt[0]) > self.HALF_CELLS or abs(nxt[1]) > self.HALF_CELLS:
                        continue
                    if not self.walkable(*nxt):
                        continue
                    step = math.sqrt(dx * dx + dy * dy) * self.cost(*nxt)
                    nc = c + step
                    if nc < cost_so_far.get(nxt, 1e18):
                        cost_so_far[nxt] = nc
                        came[nxt] = cur
                        heapq.heappush(open_q, (nc + h(nxt, g), nc, nxt))
        if not found:
            return [goal]                       # partial path: walk at it anyway
        cells = []
        cur = g
        while cur is not None:
            cells.append(cur)
            cur = came[cur]
        cells.reverse()
        pts = [V3(cx * self.CELL, cy * self.CELL, 0) for cx, cy in cells]
        # string pulling: drop waypoints with clear line-of-walk
        smoothed = [pts[0]]
        i = 0
        while i < len(pts) - 1:
            j = len(pts) - 1
            while j > i + 1:
                if self._line_walkable(pts[i], pts[j]):
                    break
                j -= 1
            smoothed.append(pts[j])
            i = j
        smoothed[-1] = goal
        return smoothed

    def _line_walkable(self, a: V3, b: V3) -> bool:
        n = max(2, int(a.dist2d(b) / self.CELL))
        for k in range(n + 1):
            p = a + (b - a) * (k / n)
            if not self.walkable(round(p.x / self.CELL), round(p.y / self.CELL)):
                return False
        return True


class AISystem(System):
    """Runs each brain's tree at 5 Hz (staggered) — ~ BrainComponent tick."""
    GROUP = TickGroup.AI
    ORDER = 0
    THINK_INTERVAL = 0.2

    def __init__(self):
        self._accum: dict[EntityId, float] = {}

    def tick(self, game: "ChimeraGame", dt: float) -> None:
        for eid, brain in list(game.world.query(DotBrain)):
            if brain.fsm == "gone":
                continue
            t = self._accum.get(eid, self.THINK_INTERVAL) + dt
            if t < self.THINK_INTERVAL:
                self._accum[eid] = t
                continue
            self._accum[eid] = 0.0
            BT_LIBRARY[brain.tree_id].tick(game, eid, brain, self.THINK_INTERVAL)


class NavFollowSystem(System):
    """Path request + follow + RVO-lite separation — ~ UCrowdFollowing."""
    GROUP = TickGroup.AI
    ORDER = 1

    def tick(self, game: "ChimeraGame", dt: float) -> None:
        others = [(e, game.world.get(e, Transform).pos)
                  for e, _b in game.world.query(DotBrain)]
        for eid, tr, agent in game.world.query(Transform, NavAgent):
            if agent.goal is None:
                continue
            agent.repath_cooldown -= dt
            if (not agent.path or agent.path_i >= len(agent.path)
                    or agent.repath_cooldown <= 0.0):
                agent.path = game.nav.astar(tr.pos, agent.goal)
                agent.path_i = 0
                agent.repath_cooldown = 2.0
            if agent.path_i >= len(agent.path):
                agent.goal = None
                continue
            wp = agent.path[agent.path_i]
            to_wp = wp - tr.pos
            if to_wp.length2d() < 1.0:
                agent.path_i += 1
                continue
            sep = V3()
            for oe, opos in others:              # separation steering
                if oe == eid:
                    continue
                d = tr.pos.dist2d(opos)
                if 0.01 < d < agent.avoid_radius * 2:
                    sep = sep + (tr.pos - opos) * (1.0 / d)
            step = (to_wp.normalized() + sep * 0.4).normalized() * (agent.speed * dt)
            tr.pos = tr.pos + step
            tr.pos.z = game.ground.height_at(tr.pos)
            tr.yaw = math.atan2(step.y, step.x)


# =============================================================================
# §9. INPUT & UI — Enhanced Input mapping + UMG widget tree + menu FSM
# UE5: UInputMappingContext/UInputAction with triggers & modifiers; UUserWidget.
# =============================================================================

class InputActionName(Enum):
    MOVE = auto(); LOOK = auto(); JUMP = auto(); BEND = auto(); SPRINT = auto()
    PICKUP = auto(); DIG = auto(); SCAN = auto(); FIRE = auto(); DRAW_WEAPON = auto()
    GESTURE_WHEEL = auto(); ATTUNE_DIAL = auto(); PAUSE = auto(); INTERACT = auto()


@dataclass
class InputBinding:
    """~ FEnhancedActionKeyMapping: key -> action with trigger + modifiers."""
    key: str
    action: InputActionName
    trigger: str = "pressed"        # pressed|released|held|tap|hold(0.3s)
    deadzone: float = 0.15
    exponent: float = 1.6           # response curve on axes


class InputMappingContext:
    """~ UInputMappingContext asset: the default suit-control layout.
    Remappable per ACCESSIBILITY (every verb, no exceptions)."""
    DEFAULT = [
        InputBinding("stick_l", InputActionName.MOVE, "axis"),
        InputBinding("stick_r", InputActionName.LOOK, "axis"),
        InputBinding("space", InputActionName.JUMP, "pressed"),
        InputBinding("ctrl", InputActionName.BEND, "held"),
        InputBinding("shift", InputActionName.SPRINT, "held"),
        InputBinding("e", InputActionName.PICKUP, "pressed"),
        InputBinding("lmb", InputActionName.DIG, "pressed"),
        InputBinding("q", InputActionName.SCAN, "pressed"),
        InputBinding("rmb", InputActionName.DRAW_WEAPON, "held"),
        InputBinding("f", InputActionName.FIRE, "pressed"),
        InputBinding("tab", InputActionName.GESTURE_WHEEL, "held"),
        InputBinding("wheel", InputActionName.ATTUNE_DIAL, "axis"),
        InputBinding("esc", InputActionName.PAUSE, "pressed"),
    ]

    def __init__(self, forgiveness_scale: float = 1.0):
        self.bindings = list(self.DEFAULT)
        self.forgiveness = forgiveness_scale     # multiplies coyote/buffer

    def apply_axis_curve(self, raw: V3, deadzone: float, exponent: float) -> V3:
        m = raw.length2d()
        if m < deadzone:
            return V3()
        shaped = ((m - deadzone) / (1.0 - deadzone)) ** exponent
        return raw.normalized() * clamp(shaped, 0.0, 1.0)


class PlayerController:
    """~ APlayerController + EnhancedInputComponent: turns device state into
    MoveInput quanta (for §11 prediction) + verb intents (routed to §12)."""

    def __init__(self, ctx: InputMappingContext):
        self.ctx = ctx
        self.raw_move = V3()
        self.raw_look = V3()
        self.held: set = set()
        self.pressed_once: set = set()
        self.yaw = 0.0
        self.pitch = 0.0
        self.dial_hz = 35.0
        self._seq = 0

    def press(self, action: InputActionName) -> None:
        self.pressed_once.add(action)
        self.held.add(action)

    def release(self, action: InputActionName) -> None:
        self.held.discard(action)

    def sample(self, dt: float) -> MoveInput:
        self.yaw += self.raw_look.x * 2.2 * dt
        self.pitch = clamp(self.pitch + self.raw_look.y * 1.6 * dt, -1.4, 1.4)
        move = self.ctx.apply_axis_curve(self.raw_move, 0.15, 1.6)
        self._seq += 1
        mi = MoveInput(seq=self._seq, move=move, yaw=self.yaw, pitch=self.pitch,
                       jump=InputActionName.JUMP in self.pressed_once,
                       bend=InputActionName.BEND in self.held,
                       sprint=InputActionName.SPRINT in self.held, dt=dt)
        verbs = set(self.pressed_once)
        self.pressed_once.clear()
        mi_verbs = verbs                          # returned alongside via attr
        mi.verbs = mi_verbs                       # type: ignore[attr-defined]
        return mi


# ---- UMG widget tree --------------------------------------------------------

class Widget:
    """~ UUserWidget: retained-mode node with children; draw == describe."""
    def __init__(self, name: str):
        self.name = name
        self.visible = True
        self.children: list[Widget] = []

    def add(self, w: "Widget") -> "Widget":
        self.children.append(w)
        return w

    def describe(self) -> dict:
        return {"widget": self.name, "visible": self.visible,
                "children": [c.describe() for c in self.children if c.visible]}


class SuitWristGauge(Widget):
    """O2 needle: the player GLANCES DOWN (bend micro-verb) to read it —
    diegetic, no floating bars (DIEGETIC_HUD law)."""
    def __init__(self):
        super().__init__("SuitWristGauge")
        self.needle_deg = 0.0

    def update(self, o2_fraction: float, dt: float) -> None:
        target = lerp(-80.0, 80.0, o2_fraction)
        self.needle_deg = lerp(self.needle_deg, target, clamp(3.0 * dt, 0, 1))


class CompassRim(Widget):
    """Helmet-rim tick lights; Earth itself is north. Bearing pips for the
    habitat, stations, and (once heard) the Erisaid."""
    def __init__(self):
        super().__init__("CompassRim")
        self.pips: list[tuple[str, float]] = []

    def update(self, yaw: float, marks: dict) -> None:
        self.pips = [(name, ((math.degrees(math.atan2(p.y, p.x)) -
                              math.degrees(yaw)) % 360.0))
                     for name, p in marks.items()]


class BatteryLEDBar(Widget):
    def __init__(self):
        super().__init__("BatteryLEDBar")
        self.segments_lit = 5

    def update(self, battery_fraction: float) -> None:
        self.segments_lit = int(round(battery_fraction * 5))


class GestureWheel(Widget):
    """Radial verb menu (hold TAB): the entire social interface (Law 3)."""
    GESTURES = ("wave", "offer", "refuse", "point", "kneel", "beckon", "thank")

    def __init__(self):
        super().__init__("GestureWheel")
        self.visible = False
        self.highlighted: Optional[str] = None

    def select_from_stick(self, stick: V3) -> Optional[str]:
        if stick.length2d() < 0.5:
            self.highlighted = None
            return None
        ang = math.atan2(stick.y, stick.x) % TAU
        idx = int(ang / TAU * len(self.GESTURES)) % len(self.GESTURES)
        self.highlighted = self.GESTURES[idx]
        return self.highlighted


class GlyphSubtitleStrip(Widget):
    """Accessibility: gestures & world sounds rendered as pictograms.
    Still wordless — glyphs, never sentences."""
    def __init__(self):
        super().__init__("GlyphSubtitleStrip")
        self.glyphs: list[str] = []

    def push(self, glyph: str) -> None:
        self.glyphs = (self.glyphs + [glyph])[-5:]


class MenuState(Enum):
    BOOT = auto(); TITLE = auto(); IN_GAME = auto(); PAUSED = auto()
    WILL_READING = auto()          # generation handoff: the inheritance screen


class UISystem(System):
    """~ a HUD AHUD + widget stack. Menu FSM + per-frame widget updates."""
    GROUP = TickGroup.UI
    ORDER = 0

    def __init__(self):
        self.state = MenuState.BOOT
        self.root = Widget("Root")
        self.hud = self.root.add(Widget("HUD"))
        self.wrist = self.hud.add(SuitWristGauge())
        self.compass = self.hud.add(CompassRim())
        self.battery = self.hud.add(BatteryLEDBar())
        self.wheel = self.hud.add(GestureWheel())
        self.glyphs = self.hud.add(GlyphSubtitleStrip())
        self.will_screen = self.root.add(Widget("WillScreen"))
        self.will_screen.visible = False

    def open_will(self) -> None:
        self.state = MenuState.WILL_READING
        self.will_screen.visible = True

    def close_will(self) -> None:
        self.state = MenuState.IN_GAME
        self.will_screen.visible = False

    def tick(self, game: "ChimeraGame", dt: float) -> None:
        if self.state == MenuState.BOOT:
            self.state = MenuState.IN_GAME
        suit = game.world.get(game.player_eid, SuitComponent)
        tr = game.world.get(game.player_eid, Transform)
        self.wrist.update(suit.o2 / 100.0, dt)
        self.battery.update(suit.battery / 100.0)
        marks = {"habitat": game.habitat_pos - tr.pos}
        if game.attunement.visit_days:
            marks["erisaid"] = game.erisaid_pos - tr.pos
        self.compass.update(tr.yaw, marks)


# =============================================================================
# §10. SAVE / LOAD — versioned serialization, migrations, autosave ring
# UE5: USaveGame subclass; UPROPERTY(SaveGame) fields; UGameplayStatics::
# SaveGameToSlot. Here: the exact capture/restore/migrate logic.
# =============================================================================

SAVE_VERSION = 4


class SaveGameSystem:
    """~ UChimeraSaveGame + async SaveGameToSlot. Captures every Component
    field named in SAVED plus the game-layer singleton state. Binary header
    packed with struct (magic/version/crc) to show the wire format."""
    MAGIC = 0x43484D52                      # 'CHMR'
    AUTOSAVE_SLOTS = 3

    def __init__(self):
        self.slots: dict[str, bytes] = {}
        self._auto_i = 0
        self.migrations: dict[int, Callable[[dict], dict]] = {
            3: self._migrate_v3_to_v4,
        }

    # ---- capture ------------------------------------------------------------
    def capture(self, game: "ChimeraGame") -> dict:
        comps: dict[str, dict] = {}
        for ctype, table in game.world._store.items():
            if not ctype.SAVED:
                continue
            rows = {}
            for eid, comp in table.items():
                rows[eid] = {f: self._encode(getattr(comp, f)) for f in ctype.SAVED}
            comps[ctype.__name__] = rows
        return dict(
            version=SAVE_VERSION,
            seed=game.seed,
            generation=game.generation,
            credits=game.credits,
            day=game.sky.day, time_h=game.sky.time_h,
            components=comps,
            dig_delta={f"{k[0]},{k[1]}": v for k, v in game.dig_delta.items()},
            buried={f"{k[0]},{k[1]}": v for k, v in game.buried.items()},
            footprints=[(fp[0].to_tuple(), fp[1], fp[2].name, fp[3], fp[4])
                        for fp in game.footprints],
            stars=[(s.life_name, s.generation, s.brightness, s.twinkle,
                    s.bearing_deg) for s in game.memorial.stars],
            sacrifices=[(e.kind, e.weight, e.note, e.generation)
                        for e in game.sacrifice.entries],
            dot_memories={str(e): b.memory for e, b in game.world.query(DotBrain)},
            attunement=dict(matched=sorted(game.attunement.matched),
                            visits=sorted(game.attunement.visit_days),
                            deaf_until=game.attunement.deaf_until_day),
            titan_best=game.titan_best,
            flags=game.flags,
        )

    @staticmethod
    def _encode(v: Any) -> Any:
        if isinstance(v, V3):
            return {"__v3__": v.to_tuple()}
        if isinstance(v, Enum):
            return {"__enum__": [type(v).__name__, v.name]}
        if hasattr(v, "kind"):                  # Item-like
            return {"__item__": [getattr(v, "kind"), getattr(v, "quality", 1.0)]}
        if isinstance(v, list):
            return [SaveGameSystem._encode(x) for x in v]
        return v

    # ---- wire format ----------------------------------------------------------
    def to_bytes(self, data: dict) -> bytes:
        import zlib
        payload = json.dumps(data, default=str).encode("utf-8")
        crc = zlib.crc32(payload) & 0xFFFFFFFF
        header = struct.pack("<III", self.MAGIC, data["version"], crc)
        return header + payload

    def from_bytes(self, blob: bytes) -> dict:
        import zlib
        magic, version, crc = struct.unpack("<III", blob[:12])
        payload = blob[12:]
        assert magic == self.MAGIC, "corrupt save: bad magic"
        assert zlib.crc32(payload) & 0xFFFFFFFF == crc, "corrupt save: bad crc"
        data = json.loads(payload.decode("utf-8"))
        while data["version"] < SAVE_VERSION:      # forward-migrate old saves
            data = self.migrations[data["version"]](data)
        return data

    @staticmethod
    def _migrate_v3_to_v4(data: dict) -> dict:
        data.setdefault("titan_best", {})          # v4 added Titan Run records
        data["version"] = 4
        return data

    def autosave(self, game: "ChimeraGame") -> str:
        slot = f"auto_{self._auto_i % self.AUTOSAVE_SLOTS}"
        self._auto_i += 1
        self.slots[slot] = self.to_bytes(self.capture(game))
        return slot


# =============================================================================
# §11. NETWORKING — server-authoritative movement, replication, prediction
# UE5: UNetDriver + character movement's ServerMove/ClientAdjustPosition
# dance. The SAME movement_step (§6) runs on both ends — that's the trick.
# =============================================================================

@dataclass
class NetPacket:
    deliver_at: float
    kind: str            # input|snapshot|rpc
    payload: Any


class NetChannel:
    """A latency+jitter pipe — ~ a UNetConnection with simulated lag.
    One instance per direction."""

    def __init__(self, rng: random.Random, one_way_ms: float = 45.0,
                 jitter_ms: float = 10.0, loss: float = 0.0):
        self.rng = rng
        self.one_way = one_way_ms / 1000.0
        self.jitter = jitter_ms / 1000.0
        self.loss = loss
        self.queue: list[NetPacket] = []
        self.sent = 0
        self.dropped = 0

    def send(self, now: float, kind: str, payload: Any) -> None:
        self.sent += 1
        if self.rng.random() < self.loss:
            self.dropped += 1
            return
        at = now + self.one_way + self.rng.uniform(0, self.jitter)
        self.queue.append(NetPacket(at, kind, payload))

    def drain(self, now: float) -> list[NetPacket]:
        ready = [p for p in self.queue if p.deliver_at <= now]
        self.queue = [p for p in self.queue if p.deliver_at > now]
        ready.sort(key=lambda p: p.deliver_at)
        return ready


class ServerAuthority:
    """The server's truth for one client pawn — ~ ACharacter on the server.
    Consumes MoveInput packets IN ORDER, steps the shared solver, and emits
    authoritative snapshots at 20 Hz. Gameplay facts (footsteps) are SERVER
    facts: clients only ever hear what the authority confirmed."""
    SNAPSHOT_HZ = 20.0

    def __init__(self, ground: "GroundField", gravity: GravityField):
        self.ground = ground
        self.gravity = gravity
        self.state = MoveState()
        self.last_seq = 0
        self._snap_accum = 0.0
        self.speed_scale = 1.0
        self.footstep_outbox: list = []

    def process(self, inputs: list[MoveInput], now: float, dt: float) -> Optional[dict]:
        for mi in sorted(inputs, key=lambda m: m.seq):
            if mi.seq <= self.last_seq:            # duplicate/reordered: drop
                continue
            g = self.gravity.sample(self.state.pos, mi.dt)
            steps: list = []
            self.state = movement_step(self.state, mi, self.ground, g,
                                       self.speed_scale, steps)
            self.footstep_outbox.extend(steps)
            self.last_seq = mi.seq
        self._snap_accum += dt
        if self._snap_accum >= 1.0 / self.SNAPSHOT_HZ:
            self._snap_accum = 0.0
            return dict(seq=self.last_seq, state=self.state.copy())
        return None


class ClientPrediction:
    """~ FSavedMove ring + ClientAdjustPosition reconciliation:
       1. sample input, apply LOCALLY at once (zero-latency feel),
       2. send to server,
       3. on snapshot: rewind to server state at acked seq, REPLAY unacked
          inputs; if the replayed result differs from our prediction beyond
          epsilon, we just corrected (count it — QA watches this number)."""
    EPSILON_M = 0.05

    def __init__(self, ground: "GroundField", gravity: GravityField):
        self.ground = ground
        self.gravity = gravity
        self.predicted = MoveState()
        self.history: list[MoveInput] = []
        self.corrections = 0
        self.speed_scale = 1.0

    def apply_local(self, mi: MoveInput) -> None:
        g = self.gravity.sample(self.predicted.pos, mi.dt)
        self.predicted = movement_step(self.predicted, mi, self.ground, g,
                                       self.speed_scale)
        self.history.append(mi)
        if len(self.history) > 256:
            self.history.pop(0)

    def reconcile(self, snapshot: dict) -> None:
        acked = snapshot["seq"]
        self.history = [m for m in self.history if m.seq > acked]
        replay = snapshot["state"].copy()
        for mi in self.history:
            g = self.gravity.sample(replay.pos, mi.dt)
            replay = movement_step(replay, mi, self.ground, g, self.speed_scale)
        if replay.pos.dist(self.predicted.pos) > self.EPSILON_M:
            self.corrections += 1
        self.predicted = replay                    # snap to truth + replayed intent


class InterpolationBuffer:
    """Simulated proxies (other players' pawns) render 100 ms in the past,
    lerping between the two snapshots that bracket render time —
    ~ FCharacterMovementComponentAsyncInput interpolation."""
    DELAY_S = 0.10

    def __init__(self):
        self.samples: list[tuple[float, V3, float]] = []   # (t, pos, yaw)

    def push(self, t: float, pos: V3, yaw: float) -> None:
        self.samples.append((t, pos, yaw))
        self.samples = self.samples[-64:]

    def sample(self, now: float) -> Optional[tuple[V3, float]]:
        t = now - self.DELAY_S
        for i in range(len(self.samples) - 1):
            t0, p0, y0 = self.samples[i]
            t1, p1, y1 = self.samples[i + 1]
            if t0 <= t <= t1:
                a = inv_lerp(t0, t1, t)
                return p0 + (p1 - p0) * a, lerp(y0, y1, a)
        return (self.samples[-1][1], self.samples[-1][2]) if self.samples else None


class ReplicationSystem(System):
    """Builds prioritized delta snapshots for every NetIdentity entity —
    ~ the property replication pass. Priority: player-distance over cull
    range; only REPLICATED fields marked dirty go on the wire."""
    GROUP = TickGroup.NETWORK
    ORDER = 1

    def __init__(self):
        self.bytes_estimate = 0
        self.actors_replicated = 0

    def tick(self, game: "ChimeraGame", dt: float) -> None:
        ptr = game.world.get(game.player_eid, Transform)
        for eid, net, tr in game.world.query(NetIdentity, Transform):
            d = ptr.pos.dist2d(tr.pos)
            if d > net.net_cull_distance:          # relevancy: skip far actors
                continue
            self.actors_replicated += 1
            self.bytes_estimate += 24              # pos+yaw quantized (~ FVector_NetQuantize)


# RPC classification (comment-spec — ~ UFUNCTION macros):
#   Server, Reliable   : gesture_send, trade_offer, dig_request  (intent up)
#   Client, Reliable   : will_reading_open, sacrifice_confirmed  (truth down)
#   NetMulticast, Unreliable: footstep_fx, dust_burst            (cosmetic fanout)


# =============================================================================
# §12. GAME LAYER — the Yard itself, running on §1-§11
# =============================================================================

class Surface(Enum):
    SAND = auto(); ROCK = auto(); METAL = auto(); BASIN = auto()
    ICE = auto(); INTERIOR = auto()


SURFACE_TABLE = {
    #                 traction  makes_print  print_life  dust_scale  audio_bank
    Surface.SAND:     (0.75,    True,        None,       1.00, "Fantozzi-Sand"),
    Surface.BASIN:    (0.45,    True,        None,       1.60, "Fantozzi-Sand"),
    Surface.ROCK:     (1.00,    False,       0.0,        0.15, "Fantozzi-Stone"),
    Surface.METAL:    (0.90,    True,        600.0,      0.05, "Metal-Scuff"),
    Surface.ICE:      (0.35,    False,       0.0,        0.02, "Ice-Crunch"),
    Surface.INTERIOR: (1.00,    False,       0.0,        0.00, "Interior-Soft"),
}
# print_life None => persists until a storm erases it (Design Law 4).

DIG = dict(radius=0.6, scoop_depth=0.15, durability_per_scoop=1.0,
           reach_m=1.8, cell=0.5)

SUIT = dict(
    o2_max=100.0, o2_drain_idle=0.6, o2_drain_walk=1.0, o2_drain_sprint=3.0,
    battery_max=100.0, battery_drain_night=1.8, battery_drain_scanner=0.5,
    dust_clog_per_storm_min=4.0, dust_clog_move_penalty=0.35,
    thermal_safe_lo=-20.0, night_temp_c=-140.0, day_temp_c=45.0,
)

ITEM_TABLE: dict[str, tuple] = {
    #                    mass_kg  base_price  sellable
    "ORE_ILMENITE":       (4.0,   12.0, True),
    "ICE_WATER":          (3.0,   18.0, True),
    "OXYGEN_CAN":         (2.0,   25.0, True),
    "MACHINE_PARTS":      (5.0,   40.0, True),
    "REGOLITH_GLASS":     (1.5,   30.0, True),
    "SEEDS":              (0.2,   55.0, True),
    "FUEL_CELL":          (6.0,   48.0, True),
    "RELIC_SHARD":        (0.8,  120.0, True),
    "ERISAID_FRAGMENT":   (0.3,    0.0, False),   # unsellable. period.
    "HEIRLOOM":           (0.5,    0.0, False),   # unsellable. period.
    "STORY":              (0.0,    8.0, True),    # traded around fires
}

NEED_FULFILLMENT: dict[str, Optional[str]] = {
    "o2": "OXYGEN_CAN", "water": "ICE_WATER", "parts": "MACHINE_PARTS",
    "warmth": "FUEL_CELL", "ride": None, "burial": None,   # some needs cost BODY
}

SACRIFICE_WEIGHTS = {
    "REFUSED_PROFIT": 1.0, "GAVE_CARGO": 1.5, "GAVE_O2": 3.0,
    "SPENT_TIME_UNPAYABLE": 2.0, "TOOK_RISK_FOR_OTHER": 2.5,
    "BURIED_STRANGER": 3.5, "WEAPON_NEVER_FIRED": 2.0, "HEIRLOOM_GIVEN": 5.0,
}

STAR = dict(brightness_k=6.0, dim_threshold=0.08, bright_lights_yard=0.75)

ACCESSIBILITY = dict(
    colorblind_palettes=("default", "deuteranopia", "protanopia", "tritanopia"),
    audio_muted_visual_pulses=True,      # FX_FootstepRing on every step
    gesture_glyph_subtitles=True,
    input_forgiveness_scale=1.0,          # multiplies coyote/buffer windows
    gravity_assist_mode=False,
)


@dataclass
class Item:
    kind: str
    quality: float = 1.0
    origin_generation: int = 0


class GroundField:
    """Authored pads + noise + LIVE dig deltas. The single ground-truth
    queried by physics, nav, audio, and the dust material.
    ~ Landscape + RVT height writes from the DigGrid."""

    def __init__(self, seed: int, dig_delta: dict):
        self.seed = seed
        self.dig_delta = dig_delta          # (ix,iy) -> dz (negative = pit)

    def surface_at(self, p: V3) -> Surface:
        if p.length2d() > 90.0 and fbm2(p.x * 0.01, p.y * 0.01, 3, self.seed) > 0.62:
            return Surface.ROCK
        for i in range(3):
            pad = spiral_point(i * 5 + 4, spacing=14.0)
            if p.dist2d(pad) < 6.0:
                return Surface.METAL
        if p.dist2d(V3(-42.0, -35.0, 0.0)) < 18.0:
            return Surface.BASIN
        return Surface.SAND

    def height_at(self, p: V3) -> float:
        dune = fbm2(p.x * 0.02, p.y * 0.02, 4, self.seed) * 2.2
        ridge = (fbm2(p.x * 0.05, p.y * 0.05, 5, self.seed + 7) * 6.0
                 if self.surface_at(p) == Surface.ROCK else 0.0)
        k = (math.floor(p.x / DIG["cell"]), math.floor(p.y / DIG["cell"]))
        return dune + ridge + self.dig_delta.get(k, 0.0)

    def traction_at(self, p: V3) -> float:
        return SURFACE_TABLE[self.surface_at(p)][0]


class SuitSystem(System):
    """~ USuitComponent tick: drains, thermal, clogging, death conditions."""
    GROUP = TickGroup.POST_PHYSICS
    ORDER = 0

    def tick(self, game: "ChimeraGame", dt: float) -> None:
        minutes = dt / 60.0
        suit = game.world.get(game.player_eid, SuitComponent)
        drain = {Gait.IDLE: SUIT["o2_drain_idle"], Gait.WALK: SUIT["o2_drain_walk"],
                 Gait.JOG: SUIT["o2_drain_walk"] * 1.6,
                 Gait.BEND: SUIT["o2_drain_walk"],
                 Gait.SPRINT: SUIT["o2_drain_sprint"]}[suit.gait]
        leak = 1.0 + (100.0 - suit.integrity) * 0.02
        suit.o2 = max(0.0, suit.o2 - drain * minutes * leak)
        if game.sky.is_night and not game.player_indoors:
            suit.battery = max(0.0, suit.battery
                               - SUIT["battery_drain_night"] * minutes)
        if game.weather.storm_active and not game.player_indoors:
            suit.dust_clog = min(100.0, suit.dust_clog
                                 + SUIT["dust_clog_per_storm_min"] * minutes)
        suit.temperature_c = (20.0 if game.player_indoors
                              else game.sky.temperature_c())
        if suit.o2 <= 0.0:
            game.world.events.emit(DeathEvent(game.player_eid, "suffocation"))
        elif suit.battery <= 0.0 and suit.temperature_c < SUIT["thermal_safe_lo"]:
            game.world.events.emit(DeathEvent(game.player_eid, "cold at night"))


class MovementNetSystem(System):
    """The §6+§11 bridge: controller -> local prediction (instant feel) ->
    input packet up -> server sim (authority) -> snapshot down -> reconcile.
    The player's Transform mirrors the PREDICTED state; gameplay facts
    (footsteps) come only from the SERVER outbox. ~ ACharacter's ServerMove."""
    GROUP = TickGroup.PHYSICS
    ORDER = 0

    def __init__(self, game: "ChimeraGame"):
        self.controller = PlayerController(InputMappingContext(
            ACCESSIBILITY["input_forgiveness_scale"]))
        self.server = ServerAuthority(game.ground, game.gravity)
        self.client = ClientPrediction(game.ground, game.gravity)
        self.up = NetChannel(game.rng)         # client -> server
        self.down = NetChannel(game.rng)       # server -> client

    def teleport(self, pos: V3) -> None:
        """Generation reset / beat-script reset_position (H-25): BOTH ends."""
        for st in (self.server.state, self.client.predicted):
            st.pos, st.vel, st.grounded = V3(*pos.to_tuple()), V3(), True

    def tick(self, game: "ChimeraGame", dt: float) -> None:
        suit = game.world.get(game.player_eid, SuitComponent)
        carry = game.world.get(game.player_eid, CarryComponent)
        mass = (ITEM_TABLE[carry.hands.kind][0] if carry.hands else 0.0) + sum(
            ITEM_TABLE[i.kind][0] for i in carry.pack)
        clog_pen = 1.0 - SUIT["dust_clog_move_penalty"] * (suit.dust_clog / 100.0)
        scale = clog_pen * (1.0 - 0.35 * clamp(mass / 30.0, 0, 1))
        self.server.speed_scale = self.client.speed_scale = scale
        # 1) sample intent; 2) predict locally; 3) send to server
        mi = self.controller.sample(dt)
        self.client.apply_local(mi)
        self.up.send(game.now_s, "input", mi)
        # 4) server consumes what has ARRIVED (latency!), steps authority
        arrived = [p.payload for p in self.up.drain(game.now_s)
                   if p.kind == "input"]
        snap = self.server.process(arrived, game.now_s, dt)
        if snap:
            self.down.send(game.now_s, "snapshot", snap)
        # 5) client reconciles whatever snapshots arrived
        for p in self.down.drain(game.now_s):
            self.client.reconcile(p.payload)
        # 6) predicted state IS the player's transform (what you see)
        tr = game.world.get(game.player_eid, Transform)
        tr.pos = self.client.predicted.pos
        tr.yaw = self.controller.yaw
        tr.pitch = self.controller.pitch
        suit.gait = self.client.predicted.gait
        sk = game.world.get(game.player_eid, SkeletalMeshRef)
        sk.anim_state = suit.gait.name.lower()
        # 7) SERVER footsteps are the one true event stream (Law 1)
        for kind, pos, surface, left, speed, t in self.server.footstep_outbox:
            game.world.events.emit(FootstepEvent(
                game.player_eid, pos, tr.yaw, surface, left, speed, t,
                landing=(kind == "land")))
        self.server.footstep_outbox.clear()
        # 8) route verb presses to the verb system
        game.pending_verbs |= getattr(mi, "verbs", set())
        game.flags["weapon_drawn"] = (InputActionName.DRAW_WEAPON
                                      in self.controller.held)
        game.attunement.dial_hz = self.controller.dial_hz


class GroundReactionSystem(System):
    """FootstepEvent -> footprint + dust + accessibility ring + camera kick.
    ~ AnimNotify_Footstep fanout, except the SOURCE is the movement solver."""
    GROUP = TickGroup.POST_PHYSICS
    ORDER = 1
    MAX_PRINTS = 4096

    def __init__(self, game: "ChimeraGame"):
        game.world.events.subscribe(FootstepEvent, lambda ev: self.on_step(game, ev))

    def on_step(self, game: "ChimeraGame", ev: FootstepEvent) -> None:
        traction, makes_print, _life, dust_scale, _bank = SURFACE_TABLE[ev.surface]
        if makes_print:
            game.footprints.append((ev.pos, ev.yaw, ev.surface, ev.left_foot,
                                    game.generation))
            if len(game.footprints) > self.MAX_PRINTS:
                game.footprints.pop(0)
        if dust_scale > 0.0:
            game.particles.spawn_burst(
                "FX_DustPuff", ev.pos,
                dust_scale * clamp(ev.speed / MOVE["sprint_speed"], 0.2, 1.0))
        if ACCESSIBILITY["audio_muted_visual_pulses"]:
            game.particles.spawn_burst("FX_FootstepRing", ev.pos, 1.0)
        game.camera.bob_velocity -= 0.35 if not ev.landing else 0.9

    def tick(self, game: "ChimeraGame", dt: float) -> None:
        pass                                   # purely event-driven


class CameraSystem(System):
    """First person: eye height by gait, FOV spring on sprint, bob springs
    back after each REAL footstep (same event the audio used — no desync)."""
    GROUP = TickGroup.POST_PHYSICS
    ORDER = 2

    def tick(self, game: "ChimeraGame", dt: float) -> None:
        cam = game.camera
        tr = game.world.get(game.player_eid, Transform)
        suit = game.world.get(game.player_eid, SuitComponent)
        drop = 0.55 if suit.gait == Gait.BEND else 0.0
        cam.eye = tr.pos + V3(0, 0, 1.62 - drop)
        cam.yaw, cam.pitch = tr.yaw, tr.pitch
        fov_target = 101.0 if suit.gait == Gait.SPRINT else 92.0
        cam.fov_y, cam.fov_velocity = spring_damper(cam.fov_y, cam.fov_velocity,
                                                    fov_target, 0.25, dt)
        cam.bob_z, cam.bob_velocity = spring_damper(cam.bob_z, cam.bob_velocity,
                                                    0.0, 0.18, dt)


DAY_LENGTH_HOURS = 27.0


@dataclass
class Star:
    life_name: str
    generation: int
    brightness: float
    twinkle: bool
    bearing_deg: float


class StarMemorial:
    """Finished lives, overhead. Bright ancestors literally light the night
    (fed into §5 IrradianceField). ~ StarMemorialComponent writing a texture."""

    def __init__(self):
        self.stars: list[Star] = []

    def add_life(self, name: str, generation: int, sacrifice_weight: float,
                 open_pains: int) -> Star:
        b = 1.0 - math.exp(-sacrifice_weight / STAR["brightness_k"])
        s = Star(name, generation, b, open_pains > 0,
                 (len(self.stars) * GOLDEN_ANGLE_DEG) % 360.0)
        self.stars.append(s)
        return s

    def night_light_level(self) -> float:
        return min(0.5, sum(s.brightness for s in self.stars
                            if s.brightness >= STAR["bright_lights_yard"]) * 0.18)


class SkyDome:
    """27 h day; Earth phase = week hand, Moon transit = hour hand.
    ~ SkyAtmosphere + DirectionalLight rig + custom sky material."""

    def __init__(self):
        self.time_h = 8.0
        self.day = 0
        self.earth_phase = 0.35
        self.moon_bearing_deg = 40.0

    def tick_hours(self, hours: float) -> None:
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
        return (math.sin((t - 0.20) / 0.60 * math.pi) * 62.0
                if 0.20 <= t <= 0.80 else -12.0)

    def sun_direction(self) -> V3:
        e = math.radians(self.sun_elevation_deg())
        return V3(math.cos(e), 0.0, -math.sin(e)).normalized()

    def temperature_c(self) -> float:
        e = max(0.0, self.sun_elevation_deg()) / 62.0
        return lerp(SUIT["night_temp_c"], SUIT["day_temp_c"], e)


class SkySystem(System):
    GROUP = TickGroup.WORLD
    ORDER = 0

    def __init__(self):
        self._gi_accum = 999.0

    def tick(self, game: "ChimeraGame", dt: float) -> None:
        game.sky.tick_hours(dt / 3600.0)
        self._gi_accum += dt
        if self._gi_accum > 120.0:             # rebake GI region every 2 sim-min
            self._gi_accum = 0.0
            mem = game.memorial.night_light_level() if game.sky.is_night else 0.0
            game.renderer.gi.bake_region(game.camera.eye, 64.0,
                                         game.sky.sun_elevation_deg(),
                                         memorial_light=mem)


class WeatherSystem(System):
    """Gusts and the ~weekly storm that erases sand prints, clogs suits, and
    fills the air (FX_StormWall). The memento mori. ~ a WorldSubsystem."""
    GROUP = TickGroup.WORLD
    ORDER = 1

    def __init__(self, rng: random.Random):
        self.rng = rng
        self.wind_speed = WIND["calm"]
        self.wind_dir = rng.uniform(0, TAU)
        self.storm_active = False
        self._storm_ends_h = 0.0
        self._next_storm_day = rng.uniform(*WIND["storm_period_days"])
        self._next_gust_s = rng.uniform(*WIND["gust_period_s"])
        self.dust_age_h = 0.0                  # feeds MaterialPBR.dust_mask

    def wind_vector(self) -> V3:
        return V3(math.cos(self.wind_dir), math.sin(self.wind_dir), 0.0) * (
            self.wind_speed * 0.3)

    def tick(self, game: "ChimeraGame", dt: float) -> None:
        hours = dt / 3600.0
        sky = game.sky
        if self.storm_active:
            self.wind_speed = WIND["storm"] * self.rng.uniform(0.85, 1.15)
            self._storm_ends_h -= hours
            self.dust_age_h = max(0.0, self.dust_age_h - 5.0 * hours)
            if self.rng.random() < 0.2:
                game.particles.spawn_burst("FX_StormWall",
                                           game.camera.eye + V3(10, 0, 2), 0.1)
            if self._storm_ends_h <= 0.0:
                self.storm_active = False
                before = len(game.footprints)
                game.footprints = [fp for fp in game.footprints
                                   if fp[2] == Surface.METAL]
                game.world.events.emit(StormEvent("passed",
                                                  before - len(game.footprints)))
        else:
            base = WIND["breeze"] if not sky.is_night else WIND["calm"]
            self._next_gust_s -= dt
            if self._next_gust_s <= 0.0:
                self._next_gust_s = self.rng.uniform(*WIND["gust_period_s"])
                base = WIND["gust"]
            self.wind_speed = lerp(self.wind_speed, base, clamp(0.4 * dt, 0, 1))
            self.wind_dir += self.rng.uniform(-0.1, 0.1) * dt
            self.dust_age_h += hours
            if sky.day + sky.time_h / DAY_LENGTH_HOURS >= self._next_storm_day:
                self.storm_active = True
                self._storm_ends_h = self.rng.uniform(*WIND["storm_duration_min"]) / 60.0
                self._next_storm_day += self.rng.uniform(*WIND["storm_period_days"])
                game.world.events.emit(StormEvent("rising"))


@dataclass
class SacrificeEntry:
    kind: str
    weight: float
    note: str
    generation: int
    day: int


class SacrificeLog:
    """The invisible score (Design Law 2). NO gauge, NO UI. Read twice ever:
    by the star at death, by the mirror. ~ USacrificeLogComponent."""

    def __init__(self):
        self.entries: list[SacrificeEntry] = []

    def record(self, kind: str, note: str, generation: int, day: int) -> None:
        self.entries.append(SacrificeEntry(kind, SACRIFICE_WEIGHTS[kind], note,
                                           generation, day))

    def weight_for_generation(self, generation: int) -> float:
        return sum(e.weight for e in self.entries if e.generation == generation)


@dataclass
class StationMarket:
    """~ generator-owned EconomyManager/StationTradingData: elastic prices."""
    station_id: str
    pos: V3
    stock: dict = field(default_factory=dict)
    demand: dict = field(default_factory=dict)     # kind -> 0.5..2.0
    ELASTICITY = 0.04

    def price(self, kind: str) -> float:
        return ITEM_TABLE[kind][1] * self.demand.get(kind, 1.0)

    def buy_from_player(self, kind: str, units: int) -> float:
        total = 0.0
        for _ in range(units):
            total += self.price(kind)
            self.demand[kind] = max(0.5, self.demand.get(kind, 1.0) - self.ELASTICITY)
            self.stock[kind] = self.stock.get(kind, 0) + 1
        return total

    def drift(self, rng: random.Random) -> None:
        for k in list(self.demand):
            self.demand[k] = clamp(self.demand[k] + rng.uniform(-0.03, 0.03),
                                   0.5, 2.0)


class FactionLedger:
    FACTIONS = ("yardfolk", "combine", "drifters", "the_quiet")

    def __init__(self):
        self.rep = {f: 0.0 for f in self.FACTIONS}

    def rep_delta(self, faction: str, amount: float) -> None:
        if faction in self.rep:
            self.rep[faction] = clamp(self.rep[faction] + amount, -100.0, 100.0)


class EconomySystem(System):
    GROUP = TickGroup.WORLD
    ORDER = 3

    def tick(self, game: "ChimeraGame", dt: float) -> None:
        if game.rng.random() < dt / 60.0:          # ~1 drift/min
            for st in game.stations:
                st.drift(game.rng)


class GestureProtocol:
    """The whole dialogue system: gesture in, gesture out, no words (Law 3).
    Subscribes to GestureEvent; resolves offers/refusals against DotBrains.
    ~ UGestureProtocolComponent + anim montages per gesture."""

    def __init__(self, game: "ChimeraGame"):
        self.game = game
        game.world.events.subscribe(GestureEvent, self.on_gesture)

    def on_gesture(self, ev: GestureEvent) -> None:
        g = self.game
        if ev.frm != g.player_eid:
            g.ui.glyphs.push(ev.gesture)            # dot -> player: subtitle glyph
            return
        brain = g.world.try_get(ev.to, DotBrain)
        if brain is None or brain.need is None:
            return
        if ev.gesture == "offer":
            self._resolve_offer(ev.to, brain)
        elif ev.gesture == "refuse":
            if not brain.can_pay:
                g.flags["refused_unpayable"] = g.flags.get("refused_unpayable", 0) + 1
                g.ui.glyphs.push("grieve")
            brain.need = None                       # refused people don't linger

    def _resolve_offer(self, dot_eid: EntityId, brain: DotBrain) -> None:
        g = self.game
        carry = g.world.get(g.player_eid, CarryComponent)
        wanted = NEED_FULFILLMENT[brain.need]
        if wanted is None:                          # body-payment needs
            if brain.need == "burial":
                g.tools["shovel_durability"] -= 6 * DIG["durability_per_scoop"]
                g.record_sacrifice("BURIED_STRANGER",
                                   f"dug a grave for {dot_eid}'s burden")
            else:                                    # ride
                g.record_sacrifice("TOOK_RISK_FOR_OTHER",
                                   f"walked {dot_eid} home before night")
            brain.memory["helped_by_generation"] = g.generation
            brain.need = None
            g.ui.glyphs.push("thank")
            return
        item = carry.hands if (carry.hands and carry.hands.kind == wanted) else None
        if item is None:
            item = next((i for i in carry.pack if i.kind == wanted), None)
            if item:
                carry.pack.remove(item)
        else:
            carry.hands = None
        if item is None:
            g.ui.glyphs.push("refuse")               # nothing to give: hands open
            return
        brain.memory["helped_by_generation"] = g.generation
        brain.need = None
        if brain.can_pay:
            g.credits += ITEM_TABLE[item.kind][1] * 1.2   # a fair trade, not a gift
        else:
            g.record_sacrifice("GAVE_CARGO",
                               f"gave {item.kind} to one who could not pay")
        g.ui.glyphs.push("thank")


class VerbSystem(System):
    """Every verb produces a physical consequence (Law 1) — ~ the input
    fanout that ATool_* actors implement (H-21: behavior, not metadata)."""
    GROUP = TickGroup.POST_PHYSICS
    ORDER = 3

    def tick(self, game: "ChimeraGame", dt: float) -> None:
        verbs, game.pending_verbs = game.pending_verbs, set()
        tr = game.world.get(game.player_eid, Transform)
        suit = game.world.get(game.player_eid, SuitComponent)
        carry = game.world.get(game.player_eid, CarryComponent)
        if InputActionName.DIG in verbs:
            self.dig(game, tr, suit)
        if InputActionName.PICKUP in verbs:
            self.pickup_or_drop(game, tr, carry)
        if InputActionName.SCAN in verbs:
            suit.battery = max(0.0, suit.battery - SUIT["battery_drain_scanner"])
            game.universe.observe_region(tr.pos, 40.0)
            game.scan_pips = [k for k, items in game.buried.items() if items and
                              V3(k[0] * DIG["cell"], k[1] * DIG["cell"], 0)
                              .dist2d(tr.pos) < 40.0]
        if InputActionName.FIRE in verbs and game.flags.get("weapon_drawn"):
            self.fire(game, tr)

    def dig(self, game: "ChimeraGame", tr: Transform, suit: SuitComponent) -> None:
        at = tr.pos + tr.forward() * 1.2
        surface = game.ground.surface_at(at)
        if (surface in (Surface.METAL, Surface.INTERIOR)
                or game.tools["shovel_durability"] <= 0):
            return                                   # sparks; the world says no
        game.tools["shovel_durability"] -= DIG["durability_per_scoop"]
        cells = int(DIG["radius"] / DIG["cell"]) + 1
        k0 = (math.floor(at.x / DIG["cell"]), math.floor(at.y / DIG["cell"]))
        for dx in range(-cells, cells + 1):
            for dy in range(-cells, cells + 1):
                k = (k0[0] + dx, k0[1] + dy)
                game.dig_delta[k] = game.dig_delta.get(k, 0.0) - DIG["scoop_depth"]
                depth_here = -game.dig_delta[k]
                for rec in list(game.buried.get(k, [])):
                    if rec["depth"] <= depth_here:    # uncovered!
                        game.buried[k].remove(rec)
                        game.world.create(
                            Transform(pos=V3(k[0] * DIG["cell"], k[1] * DIG["cell"],
                                             game.ground.height_at(at))),
                            StaticMeshRef("SM_Rock", "M_Rock", bounds_radius=0.3),
                            ItemComponent(rec["kind"], rec.get("quality", 1.0)))
        game.particles.spawn_burst("FX_DigBurst", at, 1.0)
        game.world.events.emit(FootstepEvent(game.player_eid, at, tr.yaw,
                                             surface, True, MOVE["jog_speed"],
                                             game.now_s, landing=True))

    def pickup_or_drop(self, game: "ChimeraGame", tr: Transform,
                       carry: CarryComponent) -> None:
        nearest, nd = None, 2.2
        for eid, itr, item in game.world.query(Transform, ItemComponent):
            d = tr.pos.dist2d(itr.pos)
            if d < nd:
                nearest, nd = (eid, item), d
        if nearest:
            eid, item = nearest
            obj = Item(item.kind, item.quality, item.origin_generation)
            mass = sum(ITEM_TABLE[i.kind][0] for i in carry.pack)
            if carry.hands is None:
                carry.hands = obj
            elif mass + ITEM_TABLE[obj.kind][0] <= carry.pack_kg_max:
                carry.pack.append(obj)
            else:
                return                               # hands and back both full
            game.world.destroy(eid)
        elif carry.hands is not None:                # drop what you hold
            game.world.create(
                Transform(pos=tr.pos + tr.forward() * 0.8),
                StaticMeshRef("SM_Rock", "M_Rock", bounds_radius=0.3),
                ItemComponent(carry.hands.kind, carry.hands.quality,
                              game.generation))
            carry.hands = None

    def fire(self, game: "ChimeraGame", tr: Transform) -> None:
        if game.tools["weapon_ammo"] <= 0:
            game.ui.glyphs.push("click")             # dry-fire is diegetic shame
            return
        game.tools["weapon_ammo"] -= 1
        game.flags["weapon_fired_this_life"] = True
        if tr.pos.dist2d(game.erisaid_pos) < 120.0:
            game.attunement.on_gunfire_nearby(game.sky.day)   # a season of silence
        fwd = tr.forward()
        for eid, dtr, brain, hp in game.world.query(Transform, DotBrain, Health):
            to = (dtr.pos - tr.pos)
            if to.length2d() < 60.0 and fwd.dot(to.normalized()) > 0.99:
                hp.hp -= 34.0
                brain.bb["flee"] = True
                game.factions.rep_delta("drifters", -25.0)
                break
        for _e, b in game.world.query(DotBrain):
            b.memory["saw_player_shoot"] = True       # everyone remembers


HABITAT_MODULES = {          # kind: (parts, glass, effect/min while inside)
    "AIRLOCK": (2, 1, "scrub 1.0 dust_clog"),
    "O2_GARDEN": (3, 4, "+0.8 o2"),
    "BATTERY_BANK": (2, 0, "+2.0 battery"),
    "WORKBENCH": (2, 1, "repair tools +40/use"),
    "BEACON_MAST": (1, 2, "strangers find YOU"),
}


class HabitatSystem(System):
    """Home: inherited, extended, life-support. ~ AShelterHabitat + AudioVolume."""
    GROUP = TickGroup.WORLD
    ORDER = 2
    RADIUS = 6.0

    def tick(self, game: "ChimeraGame", dt: float) -> None:
        minutes = dt / 60.0
        tr = game.world.get(game.player_eid, Transform)
        suit = game.world.get(game.player_eid, SuitComponent)
        game.player_indoors = tr.pos.dist2d(game.habitat_pos) <= self.RADIUS
        if not game.player_indoors:
            return
        if "O2_GARDEN" in game.habitat_modules:
            suit.o2 = min(SUIT["o2_max"], suit.o2 + 0.8 * minutes)
        if "BATTERY_BANK" in game.habitat_modules:
            suit.battery = min(SUIT["battery_max"], suit.battery + 2.0 * minutes)
        if "AIRLOCK" in game.habitat_modules:
            suit.dust_clog = max(0.0, suit.dust_clog - 1.0 * minutes)


class TitanRunTrack:
    """2.4 km of alternating gravity corridors; ancestor ghosts pace you.
    Registers its zones as gravity volumes (§6). ~ ATitanRunTrack + splines."""
    LENGTH = 2400.0
    ZONES = 7

    def __init__(self, start: V3, gravity: GravityField):
        self.start = start
        zone_len = self.LENGTH / self.ZONES
        for i in range(self.ZONES):
            if i % 2 == 1:
                x0 = start.x + i * zone_len
                gravity.add_zone(
                    lambda p, x0=x0, x1=x0 + zone_len, y=start.y:
                        x0 <= p.x <= x1 and abs(p.y - y) < 40.0,
                    GRAVITY_TITAN_ZONE)


class Hopper:
    """Suborbital dust-jumper — ~ generator-owned Flight spec."""
    FUEL_PER_KM = 5.0

    def __init__(self):
        self.fuel = 100.0

    def hop(self, frm: V3, to: V3) -> Optional[float]:
        km = frm.dist2d(to) / 1000.0
        cost = km * self.FUEL_PER_KM
        if cost > self.fuel:
            return None
        self.fuel -= cost
        return 8.0 + km * 30.0            # committed, hands-off ballistic arc


class Ship:
    """Orbit-capable trader hull — ~ generator-owned Ship/Docking/QuantumTravel."""
    QUANTUM_FUEL_PER_LS = 2.0

    def __init__(self):
        self.fuel = 200.0
        self.docked_at: Optional[str] = None

    def quantum_jump(self, dist_ls: float) -> bool:
        cost = dist_ls * self.QUANTUM_FUEL_PER_LS
        if cost > self.fuel:
            return False
        self.fuel -= cost
        return True


@dataclass
class UniverseBody:
    body_id: str
    kind: str                 # planetoid|moonlet|asteroid_field|debris_field|station
    pos: V3
    seed: int
    observed: bool = False


class Universe:
    """Bodies on the golden spiral; nothing finalizes until OBSERVED (Law 4 —
    the dev pipeline's observation-collapse, made playable). ~ world_store
    around() + World Partition streaming."""
    OBS_CELL = 50.0

    def __init__(self, seed: int):
        kinds = ["moonlet", "asteroid_field", "debris_field", "planetoid", "station"]
        self.bodies = [UniverseBody(f"body_{i}", kinds[i % 5],
                                    spiral_point(i, 5000.0), seed * 31 + i)
                       for i in range(24)]
        self.observed_cells: set = set()

    def observe_region(self, at: V3, radius: float) -> int:
        newly, c = 0, int(radius / self.OBS_CELL)
        cx, cy = int(at.x / self.OBS_CELL), int(at.y / self.OBS_CELL)
        for dx in range(-c, c + 1):
            for dy in range(-c, c + 1):
                k = (cx + dx, cy + dy)
                if k not in self.observed_cells:
                    self.observed_cells.add(k)
                    newly += 1
        return newly

    def around(self, pos: V3, radius: float) -> list:
        return [b for b in self.bodies if b.pos.dist(pos) <= radius]


class EndingKind(Enum):
    COSTLESS_LIFE = auto(); QUIET_STAR = auto(); BRIGHT_STAR = auto()
    MIRROR_KEEPER = auto()


@dataclass
class MirrorVision:
    empty: bool
    figures: list


@dataclass
class LifeRecord:
    name: str
    generation: int
    days_lived: float
    cause: str
    sacrifice_weight: float
    ending: EndingKind


class GenerationSystem:
    """Death/retirement -> star -> Will -> heir. ~ SaveGame + Will UI flow."""

    def __init__(self, game: "ChimeraGame"):
        self.game = game
        self.records: list[LifeRecord] = []
        game.world.events.subscribe(DeathEvent, lambda ev: self.end_life(ev.cause))

    def mirror(self, generation: int) -> MirrorVision:
        entries = [e for e in self.game.sacrifice.entries
                   if e.generation == generation]
        return MirrorVision(not entries, [e.note or e.kind for e in entries])

    def evaluate_ending(self) -> EndingKind:
        g = self.game
        w = g.sacrifice.weight_for_generation(g.generation)
        if w <= 0.0:
            return EndingKind.COSTLESS_LIFE
        if g.attunement.attuned:
            return EndingKind.MIRROR_KEEPER
        b = 1.0 - math.exp(-w / STAR["brightness_k"])
        return (EndingKind.BRIGHT_STAR if b >= STAR["bright_lights_yard"]
                else EndingKind.QUIET_STAR)

    def end_life(self, cause: str) -> LifeRecord:
        g = self.game
        if (g.flags.get("threatened_this_life")
                and not g.flags.get("weapon_fired_this_life")
                and g.tools["weapon_ammo"] > 0):
            g.record_sacrifice("WEAPON_NEVER_FIRED",
                               "was threatened; the weapon stayed cold")
        weight = g.sacrifice.weight_for_generation(g.generation)
        pains = g.flags.get("refused_unpayable", 0)
        ending = self.evaluate_ending()
        g.memorial.add_life(f"gen_{g.generation}", g.generation, weight, pains)
        rec = LifeRecord(f"gen_{g.generation}", g.generation,
                         g.sky.day + g.sky.time_h / DAY_LENGTH_HOURS,
                         cause, weight, ending)
        self.records.append(rec)
        # --- the heir wakes at the habitat (Will UI: open, read, close)
        g.ui.open_will()
        carry = g.world.get(g.player_eid, CarryComponent)
        heirloom = carry.hands if (carry.hands and carry.hands.kind == "HEIRLOOM"
                                   ) else None
        suit = g.world.get(g.player_eid, SuitComponent)
        suit.o2, suit.battery, suit.dust_clog, suit.integrity = 100.0, 100.0, 0.0, 100.0
        carry.hands, carry.pack = heirloom, []
        g.credits = round(g.credits * 0.5)           # estates leak
        g.generation += 1
        g.tools["weapon_ammo"] = 6
        g.tools["shovel_durability"] = 200.0
        for k in ("weapon_fired_this_life", "threatened_this_life"):
            g.flags.pop(k, None)
        g.movenet.teleport(g.habitat_pos + V3(2.0, 0.0, 0.0))
        g.saves.autosave(g)
        g.ui.close_will()
        return rec


class DirectorSystem(System):
    """The circadian dungeon master: dawn calm, day traffic, dusk wind,
    night hums — strangers on golden-angle bearings, pirates only for the
    visibly rich during storms. ~ a WorldSubsystem reading everything."""
    GROUP = TickGroup.WORLD
    ORDER = 4
    SCENARIOS = [("o2", "suit hissing"), ("parts", "rover dead 3 km out"),
                 ("water", "empty flask"), ("warmth", "battery flat at dusk"),
                 ("burial", "carries a body; asks with their eyes"),
                 ("ride", "points at the horizon, then at you")]

    def __init__(self, rng: random.Random):
        self.rng = rng
        self.stranger_cadence_days = (1.0, 2.2)      # real game; demos compress
        self._next_stranger_day = 0.5
        self._next_trader_day = 0.8
        self._spawned = 0
        self._gen_first_sent: set = set()   # DESIGN RULE: each generation's
        # FIRST stranger cannot pay — the Yard sends the lesson before the
        # trade (Law 2 must be met, never explained).

    def phase(self, sky: SkyDome) -> str:
        t = sky.time_h / DAY_LENGTH_HOURS
        if t < 0.20: return "night"
        if t < 0.30: return "dawn"
        if t < 0.70: return "day"
        if t < 0.80: return "dusk"
        return "night"

    def spawn_dot(self, game: "ChimeraGame", archetype: str, pos: V3,
                  tree: str, need: Optional[str] = None,
                  can_pay: bool = True) -> EntityId:
        return game.world.create(
            Transform(pos=pos),
            SkeletalMeshRef("SK_Dot"),
            NavAgent(speed=1.2),
            Health(),
            NetIdentity(net_id=game.rng.randrange(1 << 16), role="simulated"),
            DotBrain(archetype=archetype, tree_id=tree, need=need,
                     can_pay=can_pay))

    def tick(self, game: "ChimeraGame", dt: float) -> None:
        now_days = game.sky.day + game.sky.time_h / DAY_LENGTH_HOURS
        ptr = game.world.get(game.player_eid, Transform)
        if now_days >= self._next_stranger_day:
            self._next_stranger_day = now_days + self.rng.uniform(
                *self.stranger_cadence_days)
            need, _blurb = self.rng.choice(self.SCENARIOS)
            bearing = spiral_point(self._spawned, 30.0).normalized()
            self._spawned += 1
            first_of_gen = game.generation not in self._gen_first_sent
            self._gen_first_sent.add(game.generation)
            self.spawn_dot(game, "stranger", ptr.pos + bearing * 260.0,
                           "BT_Stranger", need,
                           can_pay=(False if first_of_gen
                                    else self.rng.random() < 0.35))
        if now_days >= self._next_trader_day:
            self._next_trader_day = now_days + self.rng.uniform(0.7, 1.5)
            st = game.stations[0]
            self.spawn_dot(game, "trader", st.pos + V3(
                self.rng.uniform(-30, 30), self.rng.uniform(-30, 30), 0),
                "BT_Trader")
        if (game.credits > 200 and game.weather.storm_active
                and self.rng.random() < 0.02 * dt):
            self.spawn_dot(game, "pirate", ptr.pos + V3(180, 40, 0), "BT_Pirate")
        for eid, brain in list(game.world.query(DotBrain)):
            if brain.fsm == "gone":
                game.world.destroy(eid)               # LOD0 of humanity, released


class AudioMixSystem(System):
    """Submix ducking + ambience gains — ~ the master submix tick."""
    GROUP = TickGroup.AUDIO
    ORDER = 0

    def __init__(self):
        self.submix = SubmixGraph()

    def tick(self, game: "ChimeraGame", dt: float) -> None:
        suit = game.world.get(game.player_eid, SuitComponent)
        self.submix.tick(game.weather.storm_active, suit.o2 / 100.0, dt)


# =============================================================================
# §13. BOOT — ChimeraGame assembles the whole machine; the proof runs it
# UE5: GameInstance -> GameMode::InitGame -> World load -> possess pawn.
# =============================================================================

class ChimeraGame:
    """~ UGameInstance + AGameModeBase + the loaded persistent level."""

    def __init__(self, seed: int = 7):
        self.seed = seed
        self.rng = random.Random(seed)
        self.now_s = 0.0
        self.generation = 1
        self.credits = 40.0
        self.flags: dict = {}
        self.pending_verbs: set = set()
        self.player_indoors = False
        self.scan_pips: list = []
        self.tools = dict(shovel_durability=200.0, weapon_ammo=6)
        self.titan_best: dict = {}
        # world state containers (owned here; systems mutate)
        self.dig_delta: dict = {}
        self.buried: dict = {}
        self.footprints: list = []
        # engine singletons
        self.world = World()
        self.assets = AssetRegistry(seed)
        self.camera = CameraState()
        self.ground = GroundField(seed, self.dig_delta)
        self.gravity = GravityField()
        self.nav = NavGrid(self.ground)
        self.sky = SkyDome()
        self.memorial = StarMemorial()
        self.universe = Universe(seed)
        self.sacrifice = SacrificeLog()
        self.factions = FactionLedger()
        self.saves = SaveGameSystem()
        self.habitat_pos = V3(8.0, 6.0, 0.0)
        self.habitat_modules = ["AIRLOCK", "O2_GARDEN", "BATTERY_BANK"]
        self.erisaid_pos = V3(310.0, -180.0, 0.0)
        self.titan = TitanRunTrack(V3(-200.0, 150.0, 0.0), self.gravity)
        self.hopper, self.ship = Hopper(), Ship()
        self.stations = [
            StationMarket("yard_gate", V3(60.0, 20.0, 0.0),
                          {"OXYGEN_CAN": 20, "MACHINE_PARTS": 8},
                          {"ORE_ILMENITE": 1.4, "ICE_WATER": 1.7}),
            StationMarket("far_pads", V3(-900.0, 400.0, 0.0),
                          {"FUEL_CELL": 12, "SEEDS": 6},
                          {"REGOLITH_GLASS": 1.8})]
        # --- level population (the persistent map)
        self._spawn_level()
        self.player_eid = self.world.create(
            Transform(pos=V3(0, 0, 0)), PhysicsBody(),
            SkeletalMeshRef("SK_Astronaut"), SuitComponent(), CarryComponent(),
            PlayerTag(client_id=1), NetIdentity(net_id=1, role="autonomous"))
        # --- systems, in tick order (~ ETickingGroup registration)
        self.weather = WeatherSystem(self.rng)
        self.director = DirectorSystem(random.Random(seed ^ 0x5EED))  # own dice
        self.particles = ParticleSimulator(self.rng)
        self.renderer = RenderPipeline(self.assets)
        self.sand = SandSoundSystem(self.rng)
        self.sand.bind(self.world.events)
        self.attunement = AttunementMinigame()
        self.ui = UISystem()
        self.movenet = MovementNetSystem(self)
        self.systems: list[System] = sorted([
            AISystem(), NavFollowSystem(), self.movenet,
            SuitSystem(), GroundReactionSystem(self), CameraSystem(),
            VerbSystem(), SkySystem(), self.weather, HabitatSystem(),
            EconomySystem(), self.director, AudioMixSystem(), self.sand,
            DynamicMusicSystem(), self.attunement, self.ui,
            ReplicationSystem(), self.particles, self.renderer,
        ], key=lambda s: (s.GROUP, s.ORDER))
        self.gestures = GestureProtocol(self)
        self.generations = GenerationSystem(self)

    def _spawn_level(self) -> None:
        w = self.world
        for tx in (-1, 0, 1):                       # 3x3 terrain tiles
            for ty in (-1, 0, 1):
                w.create(Transform(pos=V3(tx * 64.0, ty * 64.0, 0)),
                         StaticMeshRef("SM_YardPatch", "M_Sand",
                                       bounds_radius=46.0))
        for i in range(12):                          # rocks on the spiral
            p = spiral_point(i * 2 + 3, 13.0)
            w.create(Transform(pos=V3(p.x, p.y, self.ground.height_at(p))),
                     StaticMeshRef("SM_Rock", "M_Rock", bounds_radius=0.9))
        w.create(Transform(pos=self.habitat_pos),    # home
                 StaticMeshRef("SM_HabitatDome", "M_HabGlass", bounds_radius=4.5),
                 LightSource(intensity=800.0, radius=8.0),
                 ReverbZoneComponent())
        w.create(Transform(pos=self.erisaid_pos),    # the found thing
                 StaticMeshRef("SM_Erisaid", "M_ErisaidShell", bounds_radius=10.0))
        w.create(Transform(pos=V3(12.0, -4.0, 0.0)),  # rover, charged, waiting
                 StaticMeshRef("SM_Rover", "M_MetalPad", bounds_radius=1.6),
                 PhysicsBody(kinematic=True))
        w.create(Transform(pos=V3(0, 0, 0)),          # ambient sand drift bed
                 ParticleEmitterRef("FX_SandDrift", rate_scale=0.2),
                 AudioSource(cue="wind_bed", looping=True, bus="ambience",
                             max_radius=1e9, spatial=False))
        kinds = ["ORE_ILMENITE", "RELIC_SHARD", "ICE_WATER", "ERISAID_FRAGMENT"]
        for i in range(24):                           # buried history
            p = spiral_point(i * 3 + 2, 11.0)
            k = (math.floor(p.x / DIG["cell"]), math.floor(p.y / DIG["cell"]))
            self.buried.setdefault(k, []).append(
                dict(kind=kinds[i % 4], depth=0.15 + (i % 4) * 0.15, quality=1.0))

    def record_sacrifice(self, kind: str, note: str = "") -> None:
        self.sacrifice.record(kind, note, self.generation, self.sky.day)
        self.world.events.emit(SacrificeEvent(kind, SACRIFICE_WEIGHTS[kind],
                                              note, self.generation))

    def tick(self, dt: float) -> None:
        self.now_s += dt
        for system in self.systems:
            system.tick(self, dt)


# --- §13b. THE PROOF: two lives through the ENTIRE stack ---------------------

def _live_one_life(game: ChimeraGame, generous: bool, sim_minutes: float = 36.0,
                   dt: float = 0.25) -> None:
    """Scripted intent through the REAL controller: wander, dig, answer the
    horizon; give or refuse. Everything else — prediction, server authority,
    BTs, nav, audio, rendering — is the live machine."""
    ctl = game.movenet.controller
    carry = game.world.get(game.player_eid, CarryComponent)
    carry.pack = [Item("OXYGEN_CAN"), Item("ICE_WATER"),
                  Item("MACHINE_PARTS"), Item("FUEL_CELL")]
    responded: set = set()
    steps = int(sim_minutes * 60.0 / dt)
    for step in range(steps):
        needy = [(e, b) for e, b in game.world.query(DotBrain)
                 if b.need is not None and b.fsm != "gone"]
        ptr = game.world.get(game.player_eid, Transform)
        if needy:
            eid, brain = needy[0]
            dpos = game.world.get(eid, Transform).pos
            d = ptr.pos.dist2d(dpos)
            ctl.yaw = math.atan2(dpos.y - ptr.pos.y, dpos.x - ptr.pos.x)
            ctl.raw_move = V3(0.65, 0, 0) if d > 6.0 else V3()
            if brain.fsm == "encounter" and eid not in responded:
                responded.add(eid)
                game.world.events.emit(GestureEvent(
                    game.player_eid, eid, "offer" if generous else "refuse"))
        else:
            ctl.yaw += 0.15 * dt
            ctl.raw_move = V3(0.4, 0, 0) if (step // 240) % 2 == 0 else V3()
        if game.rng.random() < 0.002:
            ctl.press(InputActionName.DIG)
        if game.rng.random() < 0.001:
            ctl.press(InputActionName.SCAN)
        game.tick(dt)
    game.generations.end_life("retired under the memorial")


if __name__ == "__main__":
    g = ChimeraGame(seed=7)
    g.director.stranger_cadence_days = (0.004, 0.010)   # demo compression
    g.director._next_stranger_day = 0.002
    _live_one_life(g, generous=True)     # gen 1: gives to those who can't pay
    _live_one_life(g, generous=False)    # gen 2: profitable. costless.
    print("=== THE MEMORIAL ===")
    for rec, star in zip(g.generations.records, g.memorial.stars):
        vision = g.generations.mirror(rec.generation)
        print(f"gen {rec.generation}: ending={rec.ending.name:14s} "
              f"sacrifice={rec.sacrifice_weight:5.2f} "
              f"star={star.brightness:4.2f} twinkle={star.twinkle} "
              f"mirror={'EMPTY' if vision.empty else vision.figures}")
    print(f"night light from ancestors: {g.memorial.night_light_level():.3f}")
    print("=== ENGINE PROOF (the whole stack ran) ===")
    r = g.renderer.stats
    print(f"render: {r['frames']} frames, {r['draws']} draws, "
          f"{r['culled']} culled, {r['tris']} tris, "
          f"{r['shadow_views']} shadow views, "
          f"{r['particles']} particle-frames simmed")
    mn = g.movenet
    print(f"net: {mn.up.sent} input pkts up, {mn.down.sent} snapshots down, "
          f"{mn.client.corrections} prediction corrections")
    print(f"audio: {g.sand.GetFootstepSyncEventCount()} footstep events, "
          f"avg latency {g.sand.GetFootstepSyncAvgLatencyMs():.1f} ms, "
          f"volume-scales-with-speed={g.sand.GetVolumeScalesWithSpeed()}")
    print(f"world: {len(g.footprints)} footprints, "
          f"{sum(1 for v in g.dig_delta.values() if v < 0)} dug cells, "
          f"{len(g.universe.observed_cells)} observed universe cells")
    blob = g.saves.to_bytes(g.saves.capture(g))
    data = g.saves.from_bytes(blob)
    print(f"save: {len(blob)} bytes round-tripped OK "
          f"(v{data['version']}, gen {data['generation']})")
