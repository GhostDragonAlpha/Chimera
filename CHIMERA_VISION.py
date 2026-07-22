"""CHIMERA_VISION.py — SINGLE-FILE UE5.8 AAA PSEUDOSCRIPT.

CHIMERA: a generational, wordless, embodied life on a regolith planetoid in
cislunar deep space. Earth and Moon both hang in the sky. Every finished life
becomes a star whose brightness equals what that life SACRIFICED. The bad
ending is not death — it is a COSTLESS LIFE: a dim star, and the Erisaid's
mirror showing nothing.

DESIGN LAWS
  1. The world answers the body — every verb has physical, audible, visible
     consequence. No abstract clicks.
  2. The bad ending is a costless life. Meaning = what you gave up. NEVER
     explained; taught only through consequence.
  3. Wordless. No dialogue text. Gestures, objects, sounds, light.
  4. Nothing observed is lost. Footprints, pits, shelters, debts of kindness
     persist across generations.
  5. The player is the trunk. Content generates outward along the
     golden-angle spiral, at every scale.

MEMBRANE PROGRAMMING & HIERARCHICAL MEMBRANE SYSTEM:
  - Training patterns are the new computer programming: defining energy principles,
    mathematical constraints, and flow of matter/energy that govern how assets grow
    and connect in the scene hierarchy.
  - Multi-Genre Verification Gates: Spectroscopy (USGS/JPL spectral libraries),
    fluid dynamics, topological analysis — labels emerge from direct physical
    measurement of matter by light wavelength, not pre-assigned categories.
  - Physics-Based Modular Control Systems ("LEGO puzzle" connection shapes):
    * Gravitational Anchor: Newtonian gravity, mass attraction
    * Spectral/Energy Port: Light interception, "Red Edge" spectral signature, PAR distribution
    * Hydrodynamic/Hydration Port: Buoyancy, fluid drag, water hydration absorption bands (1.4µm, 1.9µm)
    * Aerodynamic/Atmospheric Port: Lift, drag, thrust, airflow patterns (Bernoulli's principle)
    * Substrate/Geological Port: Mineral absorption, soil topography, friction coefficients

VERB OVER NOUNS PHILOSOPHY:
  - The core of the system is the VERB, not the noun/item:
    * THRUST: applying energy to create motion (keyboard/input → thrust vector ports)
    * BALANCE: adjusting Center of Gravity vs. Center of Thrust to stabilize torque
    * GROW: following the flow of energy and matter from seed to canopy (phyllotaxis, fractal branching)
    * CONNECT: snapping physics modules together via compatible connection shapes
    * SCAN: using hyperspectral sensors to analyze chemical composition (spectral signatures)
    * NAVIGATE_ORBIT: calculating and adjusting thrust to achieve stable orbit (Keplerian mechanics)
    * GROW_ECOSYSTEM: planting seeds and watching biological networks grow based on environmental conditions

EXPLORATION PRODUCT / UNIVERSAL SIMULATION ARCHITECTURE:
  - An educational exploration product — a universe simulator built on physics, not pre-scripted game mechanics.
  - Players explore the universe from home by EXPERIENCING the flow of energy and matter through verbs.
  - Hierarchy: Level 1 (Energy Source/Sky) → Level 2 (Matter Source/Ground) → Level 3 (Transformation Engine/Biological Growth) → Level 4 (Observer/Camera View).

THIS IS NOT A GENERIC SIMULATION. Every class below maps to a REAL Unreal
Engine 5.8 C++ construct — real macros (UCLASS/UPROPERTY/UFUNCTION/
GENERATED_BODY), real subsystem names, real API shapes. Two corrections
against a common misconception, applied silently throughout rather than
argued: Nanite is NOT a separate component class — it is `FMeshNaniteSettings`
on `UStaticMesh`, rendered through the ordinary `UStaticMeshComponent`.
Lumen is NOT a scene-proxy class exposed to gameplay — it is configured via
`FPostProcessSettings::DynamicGlobalIlluminationMethod`/`ReflectionMethod`
plus per-primitive `bAffectDynamicIndirectLighting` flags. Both are
represented at their REAL hook points below.

ARCHITECTURE (dependency order; §N headers match the 9-point brief)
  §1  Core math              FVector/FRotator/FQuat/FMatrix/FTransform, noise
  §2  Core Engine & Loop     UGameInstance/AGameMode/AGameState/World Partition
  §3  ECS                    Mass Entity (crowd) + classic AActor/UActorComponent (hero)
  §4  Rendering              Nanite settings, Lumen GI, Niagara, post-process
  §5  Audio & MetaSound      MetaSound graphs, attenuation, reverb, submix ducking
  §6  AI & Behavior          UBehaviorTreeComponent, NavMesh, PCG, Mass LOD actorization
  §7  Animation/Move/Input   UCharacterMovementComponent, Enhanced Input, Control Rig
  §8  Gameplay & Data        GAS (Attributes/Effects/Abilities), DataTable, SaveGame
  §9  Networking             ENetRole, replication, RPCs, Replication Graph
  §10 World systems          Director, weather volumes, sacrifice/memorial/Erisaid
  §11 Boot & proof           GameInstance assembly; headless two-life run

Pure stdlib Python; runs headless (no UE process, no UBT compile — the
project's "speed run" directive: author the full architecture, prove it
executes, defer the C++ port + editor verification to later passes).
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
# UE5.8 REFLECTION MACRO SHIMS
# Real UE macros (UCLASS/UPROPERTY/UFUNCTION/USTRUCT) are consumed by Unreal
# Header Tool at compile time — they carry no runtime Python equivalent, but
# their SPECIFIERS are real, load-bearing metadata (EditAnywhere, Replicated,
# SaveGame, Category, BlueprintCallable...). These shims attach that metadata
# for real so a porting engineer can grep it back out; GENERATED_BODY() is
# pure boilerplate and gets a comment, nothing else.
# =============================================================================

def UPROPERTY(**specifiers) -> dict:
    """~ UPROPERTY(...) macro. Use as dataclasses.field(metadata=UPROPERTY(...))."""
    return dict(specifiers)


def UFUNCTION(**specifiers) -> Callable:
    """~ UFUNCTION(...) macro. Decorator; tags the method with its specifiers
    (Server/Client/NetMulticast, Reliable/Unreliable, BlueprintCallable...)."""
    def _decorate(fn):
        fn.__ufunction__ = dict(specifiers)
        return fn
    return _decorate


def UCLASS(**specifiers) -> Callable:
    """~ UCLASS(...) macro. Class decorator recording specifiers."""
    def _decorate(cls):
        cls.__uclass__ = dict(specifiers)
        return cls
    return _decorate


def USTRUCT(**specifiers) -> Callable:
    """~ USTRUCT(...) macro, for FTableRowBase-style plain data structs."""
    def _decorate(cls):
        cls.__ustruct__ = dict(specifiers)
        return cls
    return _decorate


# =============================================================================
# §1. CORE MATH — FVector / FRotator / FQuat / FMatrix / FTransform
# ~ Engine/Source/Runtime/Core/Public/Math/*.h
# =============================================================================

GOLDEN_ANGLE_DEG = 137.50776405003785
TAU = math.tau
EPS = 1e-9


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def lerp(a: float, b: float, t: float) -> float:      # ~ FMath::Lerp
    return a + (b - a) * clamp(t, 0.0, 1.0)


def inv_lerp(a: float, b: float, v: float) -> float:
    return clamp((v - a) / (b - a + EPS), 0.0, 1.0)


def smoothstep(e0: float, e1: float, x: float) -> float:   # ~ FMath::SmoothStep
    t = inv_lerp(e0, e1, x)
    return t * t * (3.0 - 2.0 * t)


def critically_damped_smoothing(x: float, v: float, target: float, halflife: float,
                                dt: float) -> tuple[float, float]:
    """~ FMath::CriticallyDampedSmoothing / a spring-damper. Drives camera bob
    return, FOV kicks, UI needle easing."""
    y = 2.0 * 0.6931 / max(halflife, EPS)
    j = v + y * (x - target)
    e = math.exp(-y * dt)
    return target + (x - target + j * dt) * e, (v - y * j * dt) * e


@dataclass
class FVector:
    """~ FVector (Core/Math/Vector.h). Right-handed, Z-up, centimeters in
    real UE5 (this pseudocode uses meters throughout for readability)."""
    X: float = 0.0
    Y: float = 0.0
    Z: float = 0.0

    def __add__(self, o: "FVector") -> "FVector": return FVector(self.X + o.X, self.Y + o.Y, self.Z + o.Z)
    def __sub__(self, o: "FVector") -> "FVector": return FVector(self.X - o.X, self.Y - o.Y, self.Z - o.Z)
    def __mul__(self, s: float) -> "FVector": return FVector(self.X * s, self.Y * s, self.Z * s)
    def __neg__(self) -> "FVector": return FVector(-self.X, -self.Y, -self.Z)

    def Dot(self, o: "FVector") -> float:               # ~ FVector::Dot
        return self.X * o.X + self.Y * o.Y + self.Z * o.Z

    def Cross(self, o: "FVector") -> "FVector":          # ~ FVector::Cross
        return FVector(self.Y * o.Z - self.Z * o.Y,
                       self.Z * o.X - self.X * o.Z,
                       self.X * o.Y - self.Y * o.X)

    def Size(self) -> float: return math.sqrt(self.Dot(self))          # ~ Size()
    def Size2D(self) -> float: return math.hypot(self.X, self.Y)       # ~ Size2D()

    def GetSafeNormal(self) -> "FVector":
        l = self.Size()
        return FVector(self.X / l, self.Y / l, self.Z / l) if l > EPS else FVector()

    def Dist(self, o: "FVector") -> float: return (self - o).Size()          # ~ FVector::Dist
    def Dist2D(self, o: "FVector") -> float: return (self - o).Size2D()

    def ToTuple(self) -> tuple: return (self.X, self.Y, self.Z)


FVector_Up = FVector(0.0, 0.0, 1.0)          # ~ FVector::UpVector


@dataclass
class FRotator:
    """~ FRotator (Pitch/Yaw/Roll, degrees). The Blueprint-facing rotation
    type; internally converted to FQuat for composition (real UE5 pattern:
    FRotator is for authoring/display, FQuat for math)."""
    Pitch: float = 0.0
    Yaw: float = 0.0
    Roll: float = 0.0


@dataclass
class FQuat:
    """~ FQuat (Core/Math/Quat.h). The actual math representation UE uses
    for composing rotations (FRotator is converted to this internally)."""
    W: float = 1.0
    X: float = 0.0
    Y: float = 0.0
    Z: float = 0.0

    @staticmethod
    def MakeFromAxisAngle(axis: FVector, rad: float) -> "FQuat":   # ~ FQuat(Axis, Angle)
        a = axis.GetSafeNormal()
        s = math.sin(rad * 0.5)
        return FQuat(math.cos(rad * 0.5), a.X * s, a.Y * s, a.Z * s)

    @staticmethod
    def MakeFromRotator(rot: FRotator) -> "FQuat":       # ~ FRotator::Quaternion()
        yaw_q = FQuat.MakeFromAxisAngle(FVector_Up, math.radians(rot.Yaw))
        pitch_q = FQuat.MakeFromAxisAngle(FVector(0, 1, 0), math.radians(rot.Pitch))
        return yaw_q @ pitch_q

    def __matmul__(self, o: "FQuat") -> "FQuat":         # ~ operator*
        return FQuat(
            self.W * o.W - self.X * o.X - self.Y * o.Y - self.Z * o.Z,
            self.W * o.X + self.X * o.W + self.Y * o.Z - self.Z * o.Y,
            self.W * o.Y - self.X * o.Z + self.Y * o.W + self.Z * o.X,
            self.W * o.Z + self.X * o.Y - self.Y * o.X + self.Z * o.W)

    def RotateVector(self, v: FVector) -> FVector:       # ~ FQuat::RotateVector
        q = FVector(self.X, self.Y, self.Z)
        t = q.Cross(v) * 2.0
        return v + t * self.W + q.Cross(t)

    def GetForwardVector(self) -> FVector: return self.RotateVector(FVector(1, 0, 0))
    def GetRightVector(self) -> FVector: return self.RotateVector(FVector(0, 1, 0))


@dataclass
class FTransform:
    """~ FTransform: Location + Rotation(FQuat) + Scale3D. The field every
    USceneComponent carries (RelativeTransform / world-space via
    GetComponentTransform()). Composition order matches UE5: scale, rotate,
    translate."""
    Location: FVector = field(default_factory=FVector)
    Rotation: FQuat = field(default_factory=FQuat)
    Scale3D: FVector = field(default_factory=lambda: FVector(1, 1, 1))

    def TransformPosition(self, p: FVector) -> FVector:
        scaled = FVector(p.X * self.Scale3D.X, p.Y * self.Scale3D.Y, p.Z * self.Scale3D.Z)
        return self.Rotation.RotateVector(scaled) + self.Location


class FMatrix:
    """~ FMatrix (row-major 4x4) — view/projection only; gameplay code
    almost never touches this directly (that's what FTransform is for), but
    the renderer (§4) needs it for frustum + shadow-cascade math."""

    def __init__(self, rows: Optional[list] = None):
        self.m = rows or [[1.0 if i == j else 0.0 for j in range(4)] for i in range(4)]

    @staticmethod
    def Perspective(fov_y_deg: float, aspect: float, znear: float, zfar: float) -> "FMatrix":
        f = 1.0 / math.tan(math.radians(fov_y_deg) * 0.5)
        m = FMatrix()
        m.m = [[f / aspect, 0, 0, 0], [0, f, 0, 0],
               [0, 0, (zfar + znear) / (znear - zfar), (2 * zfar * znear) / (znear - zfar)],
               [0, 0, -1, 0]]
        return m

    @staticmethod
    def Ortho(half_w: float, half_h: float, znear: float, zfar: float) -> "FMatrix":
        m = FMatrix()
        m.m = [[1.0 / half_w, 0, 0, 0], [0, 1.0 / half_h, 0, 0],
               [0, 0, -2.0 / (zfar - znear), -(zfar + znear) / (zfar - znear)], [0, 0, 0, 1]]
        return m

    @staticmethod
    def LookAt(eye: FVector, target: FVector, up: FVector = FVector_Up) -> "FMatrix":
        f = (target - eye).GetSafeNormal()
        r = f.Cross(up).GetSafeNormal()
        u = r.Cross(f)
        m = FMatrix()
        m.m = [[r.X, r.Y, r.Z, -r.Dot(eye)], [u.X, u.Y, u.Z, -u.Dot(eye)],
               [-f.X, -f.Y, -f.Z, f.Dot(eye)], [0, 0, 0, 1]]
        return m

    def __matmul__(self, o: "FMatrix") -> "FMatrix":
        r = FMatrix()
        r.m = [[sum(self.m[i][k] * o.m[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
        return r


def _hash2(ix: int, iy: int, seed: int) -> float:
    h = (ix * 374761393 + iy * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65536.0


def value_noise2(x: float, y: float, seed: int = 0) -> float:
    """~ FMath::PerlinNoise2D / Material Expression Noise (Value mode)."""
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


def golden_spiral_point(index: int, spacing: float = 8.0) -> FVector:
    """Phyllotaxis point generator — a real low-discrepancy (blue-noise-like)
    distribution, used below as the point-generator inside a PCG Surface
    Sampler node (§6), not just a raw spawn loop."""
    r = spacing * math.sqrt(index + 1)
    a = math.radians(GOLDEN_ANGLE_DEG) * index
    return FVector(r * math.cos(a), r * math.sin(a), 0.0)


def catmull_rom(p0: FVector, p1: FVector, p2: FVector, p3: FVector, t: float) -> FVector:
    """~ FInterpCurve / spline component evaluation. Rover paths, hopper arcs."""
    t2, t3 = t * t, t * t * t
    return (p1 * 2.0 + (p2 - p0) * t + (p0 * 2.0 - p1 * 5.0 + p2 * 4.0 - p3) * t2
            + (p3 - p0 + p1 * 3.0 - p2 * 3.0) * t3) * 0.5


# =============================================================================
# §2. CORE ENGINE & GAME LOOP
# ~ UGameInstance -> UWorld -> AGameModeBase/AGameStateBase -> APlayerController
# possessing an APawn. World Partition streams the level around the player.
# =============================================================================

class ETickingGroup(IntEnum):
    """~ real UE5 ETickingGroup enum (Engine/Classes/Engine/EngineTypes.h),
    order preserved. Everything in this file registers into one of these."""
    TG_PrePhysics = 0            # input, AI decision, gameplay->physics writes
    TG_StartPhysics = 1
    TG_DuringPhysics = 2         # UCharacterMovementComponent solve
    TG_EndPhysics = 3
    TG_PostPhysics = 4           # ground reactions: footstep FX, camera
    TG_PostUpdateWork = 5        # world/weather/economy/director, audio, UI
    TG_LastDemotable = 6


class ENetRole(IntEnum):
    """~ REAL enum values (Engine/EngineTypes.h) — order is load-bearing,
    comparisons like `Role < ROLE_Authority` appear throughout engine code."""
    ROLE_None = 0
    ROLE_SimulatedProxy = 1
    ROLE_AutonomousProxy = 2
    ROLE_Authority = 3


EntityId = int
C = TypeVar("C")


class UObject:
    """~ UObject root. Not much lives here in pseudocode beyond a stable id
    (real UObject carries the reflection/GC machinery UHT generates)."""
    _next_id = 1

    def __init__(self):
        self.ObjectId = UObject._next_id
        UObject._next_id += 1


class UActorComponent(UObject):
    """~ UActorComponent base. Subclasses (§3+) attach to an AActor's
    OwnerActor and register into a TickingGroup."""
    PrimaryComponentTick_TickGroup: ETickingGroup = ETickingGroup.TG_PrePhysics

    def __init__(self, owner: "AActor" = None):
        super().__init__()
        self.OwnerActor = owner


class USceneComponent(UActorComponent):
    """~ USceneComponent: the transform-bearing component every AActor's
    RootComponent derives from."""
    def __init__(self, owner: "AActor" = None):
        super().__init__(owner)
        self.RelativeTransform = FTransform()

    def GetComponentTransform(self) -> FTransform:
        return self.RelativeTransform            # world == relative (flat hierarchy)

    def GetComponentLocation(self) -> FVector:
        return self.RelativeTransform.Location


class AActor(UObject):
    """~ AActor base. Hero/unique world actors (player, Erisaid, Habitat,
    Rover, stations) derive from this directly — full per-frame fidelity.
    The AMBIENT CROWD (Dots) deliberately does NOT use AActor at rest; see
    §3/§6 for Mass Entity + LOD-driven actorization."""
    def __init__(self, world: "UWorld"):
        super().__init__()
        self.World = world
        self.RootComponent: USceneComponent = USceneComponent(self)
        self.OwnedComponents: list[UActorComponent] = [self.RootComponent]
        self.bReplicates = False
        self.NetUpdateFrequency = 10.0            # ~ AActor::NetUpdateFrequency
        self.MinNetUpdateFrequency = 2.0
        self.NetPriority = 1.0                    # ~ AActor::NetPriority
        self.NetCullDistanceSquared = 400.0 ** 2  # ~ AActor::NetCullDistanceSquared
        self.RemoteRole = ENetRole.ROLE_None

    def CreateDefaultSubobject(self, comp: UActorComponent) -> UActorComponent:
        comp.OwnerActor = self
        self.OwnedComponents.append(comp)
        return comp

    def FindComponentByClass(self, ctype: Type[C]) -> Optional[C]:
        for c in self.OwnedComponents:
            if isinstance(c, ctype):
                return c
        return None

    def GetActorLocation(self) -> FVector:
        return self.RootComponent.GetComponentLocation()


class UWorldSubsystem(UObject):
    """~ UWorldSubsystem: engine-managed, one instance per UWorld, auto
    ticking. NavigationSystemV1, MassEntitySubsystem, WorldPartitionSubsystem,
    AISystem, ReplicationGraph all derive from this pattern."""
    def Initialize(self, world: "UWorld") -> None: ...
    def Tick(self, dt: float) -> None: ...


class UWorld:
    """~ UWorld: the loaded level + its subsystems + the master tick.
    SendAllEndOfFrameUpdates()-equivalent happens implicitly at the end of
    Tick(); real UE ticks TWO phases per TickingGroup (start/end); this
    pseudocode ticks systems once, ordered by group, which is the observable
    behavior that matters for gameplay logic."""
    def __init__(self):
        self.TimeSeconds = 0.0
        self.Subsystems: dict[type, UWorldSubsystem] = {}
        self._tickables: list[tuple[ETickingGroup, int, Callable]] = []

    def GetSubsystem(self, ctype: Type[C]) -> C:
        return self.Subsystems[ctype]

    def RegisterSubsystem(self, sub: UWorldSubsystem) -> None:
        self.Subsystems[type(sub)] = sub
        sub.Initialize(self)

    def RegisterTickable(self, group: ETickingGroup, order: int, fn: Callable) -> None:
        self._tickables.append((group, order, fn))
        self._tickables.sort(key=lambda t: (t[0], t[1]))

    def Tick(self, dt: float) -> None:
        self.TimeSeconds += dt
        for _group, _order, fn in list(self._tickables):
            fn(dt)
        for sub in self.Subsystems.values():
            sub.Tick(dt)


class AGameModeBase(AActor):
    """~ AGameModeBase: server-only rules authority (spawns the pawn,
    decides win/loss — here, decides when a generation ends via §10)."""


class AGameStateBase(AActor):
    """~ AGameStateBase: replicated match state, visible to all clients.
    CHIMERA uses it for the handful of facts every client needs: day/night
    phase, active storm, generation number, credits."""
    REPLICATED = ("generation", "day", "storm_active")

    def __init__(self, world: "UWorld"):
        super().__init__(world)
        self.bReplicates = True
        self.generation = 1
        self.day = 0
        self.storm_active = False


class UGameInstance(UObject):
    """~ UGameInstance: the one object that survives level transitions.
    Owns the UWorld for the current session and the top-level subsystems
    that aren't per-world (SaveGame slots, §8)."""
    def __init__(self):
        super().__init__()
        self.World = UWorld()


# --- World Partition -----------------------------------------------------
# ~ Engine/Source/Runtime/Engine/Public/WorldPartition/*.h. Real system:
# the persistent level is carved into runtime CELLS on a streaming grid;
# each APawn with a UWorldPartitionStreamingSourceComponent is a streaming
# source; cells within its (loading range, activation range) load/activate,
# others unload. Data Layers (UDataLayerInstance) let a cell's actors be
# grouped and toggled independent of geometry (e.g. "Habitat" vs "Universe").

class EWorldPartitionRuntimeCellState(Enum):
    Unloaded = auto(); Loaded = auto(); Activated = auto()


@dataclass
class UDataLayerInstance:
    """~ UDataLayerInstance (Data Layers v2, UE5.1+): a toggleable content
    grouping independent of streaming geometry."""
    DataLayerAsset: str          # ~ UDataLayerAsset short name
    bIsInitiallyActive: bool = True


@dataclass
class UWorldPartitionRuntimeCell:
    """~ UWorldPartitionRuntimeCell: one streaming grid cell."""
    CellId: tuple                 # (grid_x, grid_y)
    Bounds: tuple                 # (minx, miny, maxx, maxy)
    DataLayers: list = field(default_factory=list)
    State: EWorldPartitionRuntimeCellState = EWorldPartitionRuntimeCellState.Unloaded
    Actors: list = field(default_factory=list)


class UWorldPartitionStreamingSourceComponent(UActorComponent):
    """~ real component: attach to any actor to make it a streaming source
    (almost always the player pawn; here also the rover, for pre-streaming
    ahead of a drive)."""
    def __init__(self, owner: AActor, loading_range: float = 128.0):
        super().__init__(owner)
        self.LoadingRange = loading_range         # ~ StreamingSource.TargetGrid range


class UWorldPartitionSubsystem(UWorldSubsystem):
    """~ UWorldPartitionSubsystem: owns the runtime cell grid, evaluates
    streaming sources every tick, activates/unloads cells by distance."""
    CELL_SIZE = 128.0             # meters — a real "streaming grid cell size"
    ACTIVATION_RANGE = 192.0
    UNLOAD_HYSTERESIS = 256.0

    def __init__(self):
        self.cells: dict[tuple, UWorldPartitionRuntimeCell] = {}
        self.sources: list[UWorldPartitionStreamingSourceComponent] = []
        self.stats = dict(activated=0, unloaded=0)

    def Initialize(self, world: "UWorld") -> None:
        self.world = world
        # author the Yard's cells across a 5x5 span (~640m x 640m)
        for gx in range(-2, 3):
            for gy in range(-2, 3):
                cid = (gx, gy)
                cx, cy = gx * self.CELL_SIZE, gy * self.CELL_SIZE
                layers = [UDataLayerInstance("DL_Terrain")]
                if (gx, gy) == (0, 0):
                    layers.append(UDataLayerInstance("DL_Habitat"))
                if abs(gx) == 2 or abs(gy) == 2:
                    layers.append(UDataLayerInstance("DL_UniverseApproach"))
                self.cells[cid] = UWorldPartitionRuntimeCell(
                    cid, (cx - 64, cy - 64, cx + 64, cy + 64), layers)

    def RegisterStreamingSource(self, src: UWorldPartitionStreamingSourceComponent) -> None:
        self.sources.append(src)

    def Tick(self, dt: float) -> None:
        for cell in self.cells.values():
            cx = (cell.Bounds[0] + cell.Bounds[2]) * 0.5
            cy = (cell.Bounds[1] + cell.Bounds[3]) * 0.5
            near = False
            for src in self.sources:
                p = src.OwnerActor.GetActorLocation()
                if p.Dist2D(FVector(cx, cy, 0)) <= max(src.LoadingRange, self.ACTIVATION_RANGE):
                    near = True
                    break
            if near and cell.State != EWorldPartitionRuntimeCellState.Activated:
                cell.State = EWorldPartitionRuntimeCellState.Activated
                self.stats["activated"] += 1
            elif not near and cell.State == EWorldPartitionRuntimeCellState.Activated:
                far = all(src.OwnerActor.GetActorLocation().Dist2D(FVector(cx, cy, 0))
                         > self.UNLOAD_HYSTERESIS for src in self.sources)
                if far:
                    cell.State = EWorldPartitionRuntimeCellState.Unloaded
                    self.stats["unloaded"] += 1

    def IsActive(self, pos: FVector) -> bool:
        cid = (round(pos.X / self.CELL_SIZE), round(pos.Y / self.CELL_SIZE))
        cell = self.cells.get(cid)
        return cell is not None and cell.State == EWorldPartitionRuntimeCellState.Activated


# =============================================================================
# §3. ECS — Mass Entity Framework (crowd) + classic AActor/UActorComponent (hero)
# ~ Engine/Plugins/Runtime/MassGameplay/. This is UE5's REAL production ECS
# (built for City Sample / Fortnite-scale crowds), not a bespoke invention.
# Design split, matching how Epic's own samples actually use it:
#   - Player, Erisaid, Habitat, Rover, Stations = classic AActor (full
#     per-frame fidelity; a handful of instances, complex unique behavior).
#   - "Other Dots" (the NPC crowd) = Mass Entity fragments (cheap, scales to
#     hundreds) that get LOD-ACTORIZED into a full character only when
#     within interaction range (§6) — Epic's own `EMassLOD`/
#     `UMassActorSpawnerSubsystem` pattern, and it happens to be exactly
#     this game's own design language: "a dot on the horizon" -> full actor.
# =============================================================================

@dataclass(frozen=True)
class FMassEntityHandle:
    """~ FMassEntityHandle: {Index, SerialNumber} — ABA-safe entity id."""
    Index: int
    SerialNumber: int = 1


class FMassFragment:
    """~ FMassFragment base — POD data, packed per-archetype in real Mass
    (contiguous chunks for cache-friendly SIMD-able processor iteration;
    represented here as a dict-of-dicts for pseudocode clarity)."""


class FMassTag:
    """~ FMassTag base — zero-size marker types; archetype membership only."""


@dataclass
class FTransformFragment(FMassFragment):
    """~ REAL fragment Epic ships (MassCommonFragments.h)."""
    Transform: FTransform = field(default_factory=FTransform)


@dataclass
class FMassVelocityFragment(FMassFragment):
    """~ REAL fragment (MassMovementFragments.h)."""
    Value: FVector = field(default_factory=FVector)


@dataclass
class FAgentRadiusFragment(FMassFragment):
    """~ REAL fragment (MassCommonFragments.h) — avoidance radius."""
    Radius: float = 0.4


@dataclass
class FMassDotStateFragment(FMassFragment):
    """Project-authored gameplay fragment (same pattern Epic uses for
    game-specific Mass data in City Sample, e.g. FTrafficVehicleFragment)."""
    Archetype: str = "stranger"       # trader|stranger|drifter|pirate|quiet
    FSM: str = "distant"
    Need: Optional[str] = None
    CanPay: bool = True
    StableId: str = ""                # keys cross-generation memory (Law 4)


class FMassStrangerTag(FMassTag): ...
class FMassTraderTag(FMassTag): ...
class FMassPirateTag(FMassTag): ...
class FMassQuietTag(FMassTag): ...


class FMassEntityQuery:
    """~ FMassEntityQuery: declares a processor's required fragment/tag
    composition (AddRequirement<T>() in real Mass)."""
    def __init__(self, *component_types: type):
        self.component_types = component_types


class FMassEntityManager:
    """~ FMassEntityManager: owns all entities/fragments/archetypes. Real
    Mass groups entities into archetypes by fragment composition for
    branch-free iteration; this pseudocode trades that for a flat
    dict-of-dicts, which is observably equivalent for gameplay purposes."""
    def __init__(self):
        self._next = 1
        self._rows: dict[FMassEntityHandle, dict[type, FMassFragment]] = {}

    def CreateEntity(self, *frags: FMassFragment) -> FMassEntityHandle:
        h = FMassEntityHandle(self._next)
        self._next += 1
        self._rows[h] = {type(f): f for f in frags}
        return h

    def DestroyEntity(self, h: FMassEntityHandle) -> None:
        self._rows.pop(h, None)

    def GetFragmentDataPtr(self, h: FMassEntityHandle, ftype: Type[C]) -> Optional[C]:
        return self._rows.get(h, {}).get(ftype)

    def GetFragmentDataChecked(self, h: FMassEntityHandle, ftype: Type[C]) -> C:
        return self._rows[h][ftype]

    def EntityQuery(self, query: FMassEntityQuery) -> Iterator[tuple]:
        """~ FMassExecutionContext iteration over matching entities."""
        for h, row in list(self._rows.items()):
            if all(t in row for t in query.component_types):
                yield (h, *[row[t] for t in query.component_types])

    def NumEntities(self) -> int:
        return len(self._rows)


class UMassProcessor(ABC):
    """~ UMassProcessor base — a Mass "system." ConfigureQueries() declares
    the fragment composition once; Execute() runs every Mass tick over all
    matching entities. Order controlled by ExecutionOrder groups in real
    Mass; here, registration order in UMassEntitySubsystem."""
    @abstractmethod
    def ConfigureQueries(self) -> FMassEntityQuery: ...

    @abstractmethod
    def Execute(self, EntityManager: FMassEntityManager, Game: "ChimeraGame",
               DeltaTime: float) -> None: ...


class UMassSignalSubsystem(UWorldSubsystem):
    """~ UMassSignalSubsystem: fires named signals at specific entities so
    event-driven logic doesn't need a full per-entity tick (real system;
    e.g. `SignalEntity(UE::Mass::Signals::OnAnimationFinished, Entity)`)."""
    def __init__(self):
        self._pending: dict[str, list[FMassEntityHandle]] = {}

    def SignalEntity(self, signal_name: str, entity: FMassEntityHandle) -> None:
        self._pending.setdefault(signal_name, []).append(entity)

    def DrainSignal(self, signal_name: str) -> list[FMassEntityHandle]:
        return self._pending.pop(signal_name, [])


class UMassEntitySubsystem(UWorldSubsystem):
    """~ UMassEntitySubsystem: the WorldSubsystem owning FMassEntityManager
    + the registered processor list, ticked once per Mass frame."""
    def __init__(self):
        self.EntityManager = FMassEntityManager()
        self.Processors: list[UMassProcessor] = []
        self._game: "ChimeraGame" = None

    def Initialize(self, world: "UWorld") -> None:
        pass

    def BindGame(self, game: "ChimeraGame") -> None:
        self._game = game

    def RegisterProcessor(self, p: UMassProcessor) -> None:
        p._query = p.ConfigureQueries()
        self.Processors.append(p)

    def Tick(self, dt: float) -> None:
        for p in self.Processors:
            p.Execute(self.EntityManager, self._game, dt)


# --- Typed event delegates (hero-actor side; the crowd uses MassSignalSubsystem) ---
# ~ DECLARE_DYNAMIC_MULTICAST_DELEGATE macros. ONE canonical broadcaster per
# fact so audio/VFX/UI/camera can never desync (Design Law 1).

@dataclass
class FFootstepEvent:
    """~ FOnFootstepDelegate payload. THE canonical body-fact."""
    Actor: AActor
    Location: FVector
    Yaw: float
    Surface: "ESurfaceType"
    bLeftFoot: bool
    Speed: float
    TimeSeconds: float
    bLanding: bool = False


@dataclass
class FGestureEvent:
    From: AActor
    To: Any                    # AActor (hero) or FMassEntityHandle (crowd)
    Gesture: str


@dataclass
class FSacrificeEvent:
    Kind: str
    Weight: float
    Note: str
    Generation: int


@dataclass
class FDeathEvent:
    Actor: AActor
    Cause: str


@dataclass
class FStormEvent:
    Phase: str
    ErasedPrints: int = 0


class FMulticastDelegate:
    """~ a DECLARE_DYNAMIC_MULTICAST_DELEGATE instance: Broadcast() to all
    AddDynamic()-bound listeners."""
    def __init__(self):
        self._listeners: list[Callable] = []

    def AddDynamic(self, fn: Callable) -> None:
        self._listeners.append(fn)

    def Broadcast(self, payload: Any) -> None:
        for fn in self._listeners:
            fn(payload)


class UChimeraEventBus(UWorldSubsystem):
    """Aggregates the game's FMulticastDelegates in one place for pseudocode
    convenience (real UE5 code would declare each on its owning class, e.g.
    OnFootstep lives on UChimeraMovementComponent directly)."""
    def __init__(self):
        self.OnFootstep = FMulticastDelegate()
        self.OnGesture = FMulticastDelegate()
        self.OnSacrifice = FMulticastDelegate()
        self.OnDeath = FMulticastDelegate()
        self.OnStorm = FMulticastDelegate()

    def Initialize(self, world: "UWorld") -> None: pass
    def Tick(self, dt: float) -> None: pass


# --- Hero-actor component catalog (classic UActorComponent zoo) -------------

class Gait(Enum):
    IDLE = auto(); WALK = auto(); JOG = auto(); SPRINT = auto(); BEND = auto()


@UCLASS(Blueprintable=True, ClassGroup="Chimera")
class UStaticMeshComponent(USceneComponent):
    """~ UStaticMeshComponent. Nanite is NOT a separate component — it's a
    per-mesh setting (see FMeshNaniteSettings in §4) that this component's
    assigned UStaticMesh may or may not have enabled; the renderer picks the
    Nanite path transparently when it's present."""
    def __init__(self, owner: AActor, mesh_id: str, material_id: str = "M_Default"):
        super().__init__(owner)
        self.StaticMesh = mesh_id                 # ~ GetStaticMesh()
        self.OverrideMaterial = material_id        # ~ SetMaterial(0, ...)
        self.bCastDynamicShadow = True
        self.BoundsScale = 1.0
        # Lumen per-primitive flags — REAL fields (PrimitiveComponent.h):
        self.bAffectDynamicIndirectLighting = True
        self.bAffectDistanceFieldLighting = True


@UCLASS(Blueprintable=True)
class USkeletalMeshComponent(USceneComponent):
    """~ USkeletalMeshComponent + its UAnimInstance (state driven in §7)."""
    def __init__(self, owner: AActor, mesh_id: str):
        super().__init__(owner)
        self.SkeletalMeshAsset = mesh_id
        self.AnimInstanceState = "idle"            # ~ UAnimInstance subclass state


@UCLASS()
class UCapsuleComponent(USceneComponent):
    """~ UCapsuleComponent — the character's collision primitive."""
    def __init__(self, owner: AActor, radius: float = 0.35, half_height: float = 0.9):
        super().__init__(owner)
        self.CapsuleRadius = radius
        self.CapsuleHalfHeight = half_height


@UCLASS()
class UPointLightComponent(USceneComponent):
    """~ UPointLightComponent. Lumen flags mirror UStaticMeshComponent's —
    both derive from the same UPrimitiveComponent lighting contract."""
    def __init__(self, owner: AActor, intensity: float = 5000.0, radius: float = 8.0):
        super().__init__(owner)
        self.Intensity = intensity                  # lumens
        self.AttenuationRadius = radius
        self.LightColor = (1.0, 0.95, 0.9)
        self.bAffectDynamicIndirectLighting = True   # ~ ULightComponent field
        self.CastShadows = False


@UCLASS()
class AAudioVolume(AActor):
    """~ AAudioVolume: a box that applies a reverb/submix effect to anything
    heard inside it. Real actor type, not a generic 'zone' component."""
    def __init__(self, world: "UWorld", extents: FVector, preset: str, wet: float):
        super().__init__(world)
        self.Extents = extents
        self.ReverbSettings = dict(preset=preset, wet=wet, decay_s=1.2)


# =============================================================================
# §4. RENDERING — Nanite, Lumen, post-process stack, Niagara VFX
# ~ Engine/Source/Runtime/Renderer/, Engine/Plugins/FX/Niagara/
# =============================================================================

@dataclass
class Vertex:
    """~ FStaticMeshBuildVertex (one entry of the vertex buffer)."""
    px: float; py: float; pz: float
    nx: float; ny: float; nz: float
    u: float; v: float


@dataclass
class FMeshNaniteSettings:
    """~ REAL struct (Engine/Classes/Engine/StaticMesh.h): `UStaticMesh::
    NaniteSettings`. Nanite is NOT a component — it is this settings block
    on the mesh ASSET; UStaticMeshComponent renders it transparently through
    the ordinary rendering path once bEnabled is true. Virtualized geometry
    means near-constant screen-space triangle cost regardless of source
    density (millions of source triangles are fine); FallbackPercentTriangles
    is what still gets baked for platforms/paths that can't Nanite-render
    (e.g. WPO-heavy materials historically, ray-tracing fallback proxies)."""
    bEnabled: bool = True
    PositionPrecision: int = -8          # log2 quantization step; -8 = fine
    FallbackPercentTriangles: float = 0.05
    bPreserveArea: bool = True
    TrimRelativeError: float = 0.0


@dataclass
class MeshData:
    """CPU-side authoring representation: vertex/index buffer + LOD chain +
    Nanite settings. ~ FStaticMeshRenderData (LODResources[] when non-Nanite,
    plus the Nanite streaming page data when bEnabled)."""
    name: str
    vertices: list = field(default_factory=list)
    indices: list = field(default_factory=list)
    lods: list = field(default_factory=list)        # [(screen_size, index_count)] — non-Nanite fallback path
    nanite: FMeshNaniteSettings = field(default_factory=FMeshNaniteSettings)
    bounds_radius: float = 1.0     # ~ Bounds.SphereRadius; AssetRegistry bakes the real value post-construction

    def cluster_estimate(self) -> int:
        """Nanite groups ~128-tri clusters into a BVH of cluster groups; this
        estimates cluster count for the headless render-stat proof (§11)."""
        return max(1, (len(self.indices) // 3) // 128)

    def bounds_sphere_radius(self) -> float:
        """~ UPrimitiveComponent::Bounds.SphereRadius (local space, before
        the component's world Scale3D is applied). Computed once and cached
        by AssetRegistry — the renderer's frustum test needs the ACTUAL
        mesh extent, not a flat placeholder, or a 90m terrain patch gets
        culled from any sane camera distance."""
        if not self.vertices:
            return 1.0
        return max(math.sqrt(v.px ** 2 + v.py ** 2 + v.pz ** 2) for v in self.vertices)


def make_grid_mesh(name: str, size_m: float, cells: int,
                   height_fn: Callable[[float, float], float],
                   nanite: bool = True) -> MeshData:
    """Terrain patch, displaced grid, analytic central-difference normals.
    ~ authored via Landscape or a PCG-baked static mesh; Nanite-enabled so
    LOD selection is the renderer's problem, not ours."""
    m = MeshData(name, nanite=FMeshNaniteSettings(bEnabled=nanite))
    step = size_m / cells
    h = 0.5 * size_m
    for iy in range(cells + 1):
        for ix in range(cells + 1):
            x, y = ix * step - h, iy * step - h
            z = height_fn(x, y)
            e = 0.25
            nx = height_fn(x - e, y) - height_fn(x + e, y)
            ny = height_fn(x, y - e) - height_fn(x, y + e)
            n = FVector(nx, ny, 2.0 * e).GetSafeNormal()
            m.vertices.append(Vertex(x, y, z, n.X, n.Y, n.Z, ix / cells, iy / cells))
    for iy in range(cells):
        for ix in range(cells):
            a = iy * (cells + 1) + ix
            b, c, d = a + 1, a + cells + 1, a + cells + 2
            m.indices += [a, c, b, b, c, d]
    full = len(m.indices)
    m.lods = [(1.0, full), (0.5, full // 4), (0.2, full // 16)]   # non-Nanite fallback chain
    return m


def make_icosphere(name: str, radius: float, subdiv: int = 1, nanite: bool = True) -> MeshData:
    t = (1.0 + math.sqrt(5.0)) / 2.0
    pts = [FVector(-1, t, 0), FVector(1, t, 0), FVector(-1, -t, 0), FVector(1, -t, 0),
           FVector(0, -1, t), FVector(0, 1, t), FVector(0, -1, -t), FVector(0, 1, -t),
           FVector(t, 0, -1), FVector(t, 0, 1), FVector(-t, 0, -1), FVector(-t, 0, 1)]
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
                pts.append((pts[i] + pts[j]) * 0.5 * (pts[i].Size() / ((pts[i] + pts[j]) * 0.5).Size()))
            return cache[key]
        for (a, b, c) in faces:
            ab, bc, ca = midpoint(a, b), midpoint(b, c), midpoint(c, a)
            new_faces += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        faces = new_faces
    m = MeshData(name, nanite=FMeshNaniteSettings(bEnabled=nanite))
    for p in pts:
        n = p.GetSafeNormal()
        u = 0.5 + math.atan2(n.Y, n.X) / TAU
        v = 0.5 - math.asin(clamp(n.Z, -1, 1)) / math.pi
        m.vertices.append(Vertex(n.X * radius, n.Y * radius, n.Z * radius, n.X, n.Y, n.Z, u, v))
    for f in faces:
        m.indices += list(f)
    m.lods = [(1.0, len(m.indices))]
    return m


def make_erisaid_shell(name: str = "SM_Erisaid") -> MeshData:
    """The half-buried leviathan shell, 18 m long. Nanite-enabled — the
    ridge micro-detail (34 longitudinal ribs) would be LOD-fallback-lossy
    on a traditional mesh at range; Nanite keeps it screen-space-correct
    from any distance without a manual LOD chain."""
    m = MeshData(name, nanite=FMeshNaniteSettings(bEnabled=True, PositionPrecision=-10))
    rings, segs = 24, 32
    for i in range(rings + 1):
        v = i / rings
        rx = 9.0 * (math.sin(math.pi * v) ** 0.7)
        rz = 4.0 * (math.sin(math.pi * v) ** 0.9)
        for j in range(segs + 1):
            u = j / segs
            a = math.pi * u
            x = (v - 0.5) * 18.0
            y = math.cos(a) * rx * 0.45
            z = math.sin(a) * rz
            ridge = 0.25 * math.sin(v * 34.0) * smoothstep(0.1, 0.9, v)
            n = FVector(0.0, math.cos(a), math.sin(a)).GetSafeNormal()
            m.vertices.append(Vertex(x, y, z + ridge, n.X, n.Y, n.Z, u, v))
    for i in range(rings):
        for j in range(segs):
            a = i * (segs + 1) + j
            b, c, d = a + 1, a + segs + 1, a + segs + 2
            m.indices += [a, c, b, b, c, d]
    m.lods = [(1.0, len(m.indices))]
    return m


@dataclass
class MaterialPBR:
    """~ UMaterialInstanceDynamic scalar/vector parameters — exactly what
    SetScalarParameterValue()/SetVectorParameterValue() would drive."""
    name: str
    base_color: tuple = (0.5, 0.5, 0.5)
    metallic: float = 0.0
    roughness: float = 0.85
    emissive: tuple = (0.0, 0.0, 0.0)
    emissive_intensity: float = 0.0
    dust_mask_enabled: bool = False
    dust_tint: tuple = (0.72, 0.62, 0.50)

    def dust_mask(self, normal_z: float, wx: float, wy: float, age_h: float) -> float:
        """The researched dust-accumulation function, as a material function
        graph would express it: DustMask = saturate(N.z)^2 * crevice_fbm *
        saturate(age*rate). ~ MF_DustAccumulation (vertex normal + world pos
        + a scalar parameter fed by §10's WeatherSystem)."""
        up = clamp(normal_z, 0.0, 1.0) ** 2.0
        crev = fbm2(wx * 0.13, wy * 0.13, 4, seed=99)
        age = clamp(age_h * 0.02, 0.0, 1.0)
        return clamp(up * (0.4 + 0.6 * crev) * age, 0.0, 1.0)


@dataclass
class UMaterialParameterCollection:
    """~ UMaterialParameterCollection (MPC): a named bag of scalar/vector
    params EVERY material instance can read without a per-material dynamic
    instance. Used for globally-driven look: wind strength (dust-drift
    direction bias), storm intensity (screen grit), memorial night-light."""
    ScalarParameters: dict = field(default_factory=lambda: dict(
        WindSpeed=2.0, StormIntensity=0.0, MemorialNightLight=0.0, DustAgeHours=0.0))
    VectorParameters: dict = field(default_factory=lambda: dict(WindDirection=(1.0, 0.0, 0.0)))

    def SetScalarParameterValue(self, name: str, value: float) -> None:
        self.ScalarParameters[name] = value


class AssetRegistry:
    """~ FAssetRegistry + UAssetManager: procedural, no disk I/O."""

    def __init__(self, seed: int):
        yard_height = lambda x, y: fbm2(x * 0.02, y * 0.02, 4, seed) * 2.2
        self.meshes: dict[str, MeshData] = {
            "SM_YardPatch": make_grid_mesh("SM_YardPatch", 64.0, 32, yard_height),
            "SM_Rock": make_icosphere("SM_Rock", 0.8, 1),
            "SM_Moonlet": make_icosphere("SM_Moonlet", 40.0, 2),
            "SM_Erisaid": make_erisaid_shell(),
            "SM_HabitatDome": make_icosphere("SM_HabitatDome", 4.0, 2),
            "SM_Rover": make_icosphere("SM_Rover", 1.4, 1, nanite=False),  # skinned chassis, non-Nanite
            "SK_Astronaut": make_icosphere("SK_Astronaut", 0.5, 1, nanite=False),  # skeletal meshes: no Nanite
            "SK_Dot": make_icosphere("SK_Dot", 0.5, 0, nanite=False),
        }
        for mesh in self.meshes.values():                    # ~ FStaticMeshRenderData::Bounds bake
            mesh.bounds_radius = mesh.bounds_sphere_radius()
        self.materials: dict[str, MaterialPBR] = {
            "M_Sand": MaterialPBR("M_Sand", (0.62, 0.54, 0.42), 0.0, 0.95, dust_mask_enabled=True),
            "M_Rock": MaterialPBR("M_Rock", (0.35, 0.33, 0.31), 0.0, 0.9, dust_mask_enabled=True),
            "M_MetalPad": MaterialPBR("M_MetalPad", (0.6, 0.6, 0.62), 1.0, 0.4, dust_mask_enabled=True),
            "M_Suit": MaterialPBR("M_Suit", (0.85, 0.85, 0.88), 0.2, 0.6),
            "M_ErisaidShell": MaterialPBR("M_ErisaidShell", (0.18, 0.2, 0.22), 0.7, 0.35, dust_mask_enabled=True),
            "M_ErisaidMirror": MaterialPBR("M_ErisaidMirror", (0.05, 0.05, 0.06), 1.0, 0.05),
            "M_HabGlass": MaterialPBR("M_HabGlass", (0.7, 0.8, 0.9), 0.0, 0.1),
            "M_StarBillboard": MaterialPBR("M_StarBillboard", (0, 0, 0), 0, 1,
                                           emissive=(1.0, 0.97, 0.9), emissive_intensity=1.0),
        }
        self.mpc = UMaterialParameterCollection()


# --- Lumen (real hook: FPostProcessSettings, not a scene-proxy class) -------

class EDynamicGlobalIlluminationMethod(Enum):     # ~ real enum (RendererSettings.h)
    Lumen = auto(); ScreenSpace = auto(); None_ = auto()


class EReflectionMethod(Enum):                     # ~ real enum
    Lumen = auto(); ScreenSpace = auto(); None_ = auto()


@dataclass
class FPostProcessSettings:
    """~ REAL struct (Engine/Classes/Engine/Scene.h), applied via an
    APostProcessVolume covering the whole Yard (unbound, priority 0). Lumen
    is enabled HERE, not via a separate proxy class — this is the actual
    gameplay-facing hook a level designer touches."""
    bOverride_DynamicGlobalIlluminationMethod: bool = True
    DynamicGlobalIlluminationMethod: EDynamicGlobalIlluminationMethod = \
        EDynamicGlobalIlluminationMethod.Lumen
    bOverride_ReflectionMethod: bool = True
    ReflectionMethod: EReflectionMethod = EReflectionMethod.Lumen
    LumenSceneDetail: float = 1.0                  # ~ r.Lumen.SceneDetail equivalents
    LumenFinalGatherQuality: float = 1.0
    IndirectLightingIntensity: float = 1.0
    # exposure / tonemap (auto-adapts each frame in RenderPipeline.Tick)
    AutoExposureMinBrightness: float = -2.0
    AutoExposureMaxBrightness: float = 8.0
    AutoExposureSpeedUp: float = 3.0
    AutoExposureSpeedDown: float = 1.0
    AutoExposureBias: float = 0.0                  # the adapted EV, written each frame
    BloomThreshold: float = 1.1
    BloomIntensity: float = 0.35
    VignetteIntensity: float = 0.25
    GrainIntensity: float = 0.04
    DepthOfFieldFocalDistance: float = 8.0
    DepthOfFieldFstop: float = 4.0
    ChromaticAberrationStartOffset: float = 0.8
    ChromaticAberrationIntensity: float = 0.0       # driven up during suit-alarm (§10)
    ColorGradingShadows: tuple = (0.98, 0.99, 1.06)
    ColorGradingHighlights: tuple = (1.05, 1.0, 0.94)

    def Tick_AutoExposure(self, scene_luminance: float, dt: float) -> None:
        target = clamp(-math.log2(max(scene_luminance, 0.01)),
                       self.AutoExposureMinBrightness, self.AutoExposureMaxBrightness)
        speed = self.AutoExposureSpeedUp if target > self.AutoExposureBias else self.AutoExposureSpeedDown
        self.AutoExposureBias = lerp(self.AutoExposureBias, target, clamp(speed * dt, 0, 1))


class ALumenSurfaceCacheApprox:
    """Lumen's actual Surface Cache + Radiance Cache are renderer-private
    (FLumenSceneData, not gameplay-visible). This is the GAMEPLAY-SIDE
    approximation needed for one specific design hook: bright ancestor
    stars must visibly light the Yard at night (Design Law 2 payoff). A
    coarse world-space irradiance probe grid stands in for "what Lumen
    would compute," fed by IndirectLightingIntensity + the memorial."""
    PROBE_SPACING = 16.0

    def __init__(self):
        self.probes: dict[tuple, float] = {}

    def bake_region(self, center: FVector, radius: float, sun_elev_deg: float,
                    albedo: float, memorial_light: float, pp: FPostProcessSettings) -> None:
        sky = max(0.0, math.sin(math.radians(max(sun_elev_deg, 0.0))))
        c = int(radius / self.PROBE_SPACING)
        cx, cy = int(center.X / self.PROBE_SPACING), int(center.Y / self.PROBE_SPACING)
        for dx in range(-c, c + 1):
            for dy in range(-c, c + 1):
                direct = sky
                bounce = direct * albedo * 0.5 * pp.IndirectLightingIntensity
                self.probes[(cx + dx, cy + dy)] = direct + bounce + memorial_light

    def sample(self, p: FVector) -> float:
        k = (int(p.X / self.PROBE_SPACING), int(p.Y / self.PROBE_SPACING))
        return self.probes.get(k, 0.05)


# --- Niagara VFX -------------------------------------------------------------

class ENiagaraSimTarget(Enum):        # ~ real enum
    CPUSim = auto(); GPUComputeSim = auto()


@dataclass
class UNiagaraDataInterfaceCurlNoiseField:
    """~ a REAL Niagara Data Interface pattern: a vector field module reads
    from this each particle-tick to advect dust with turbulence, not just
    uniform wind — curl noise keeps the field divergence-free (no particles
    unrealistically pooling/vanishing)."""
    frequency: float = 0.08
    strength: float = 1.4

    def sample(self, p: FVector, seed: int) -> FVector:
        e = 0.5
        n = lambda x, y: value_noise2(x * self.frequency, y * self.frequency, seed)
        dx = (n(p.X, p.Y + e) - n(p.X, p.Y - e)) / (2 * e)
        dy = -(n(p.X + e, p.Y) - n(p.X - e, p.Y)) / (2 * e)
        return FVector(dx, dy, 0.0) * self.strength


@dataclass
class UNiagaraSystem:
    """~ UNiagaraSystem asset: one or more emitters + their modules. GPU sim
    for high-count ambient effects (dust drift, storm wall); CPU sim for
    low-count gameplay-coupled bursts that need synchronous read-back
    (footstep dust the same frame audio triggers — Design Law 1)."""
    name: str
    sim_target: ENiagaraSimTarget = ENiagaraSimTarget.CPUSim
    burst: int = 0
    rate_per_s: float = 0.0
    lifetime_s: tuple = (0.6, 1.2)
    speed: tuple = (0.5, 1.5)
    cone_deg: float = 40.0
    size_m: tuple = (0.05, 0.25)
    gravity_scale: float = 0.15
    drag: float = 1.2
    uses_curl_noise: bool = False
    color: tuple = (0.72, 0.62, 0.5)
    die_on_ground: bool = True


NIAGARA_LIBRARY: dict[str, UNiagaraSystem] = {
    "NS_DustPuff": UNiagaraSystem("NS_DustPuff", ENiagaraSimTarget.CPUSim,
                                  burst=14, speed=(0.4, 1.4), cone_deg=70.0),
    "NS_SandDrift": UNiagaraSystem("NS_SandDrift", ENiagaraSimTarget.GPUComputeSim,
                                   rate_per_s=400.0, lifetime_s=(2.0, 5.0), speed=(0.0, 0.3),
                                   uses_curl_noise=True, gravity_scale=0.02,
                                   size_m=(0.4, 1.6), die_on_ground=False),
    "NS_FootstepRing": UNiagaraSystem("NS_FootstepRing", ENiagaraSimTarget.CPUSim, burst=1,
                                      lifetime_s=(0.5, 0.5), speed=(0.0, 0.0), size_m=(0.3, 0.3),
                                      color=(0.9, 0.9, 1.0)),          # accessibility pulse
    "NS_StormWall": UNiagaraSystem("NS_StormWall", ENiagaraSimTarget.GPUComputeSim,
                                   rate_per_s=4000.0, lifetime_s=(1.0, 2.0), speed=(6.0, 14.0),
                                   uses_curl_noise=True, size_m=(1.0, 3.0), gravity_scale=0.0,
                                   die_on_ground=False),
    "NS_DigBurst": UNiagaraSystem("NS_DigBurst", ENiagaraSimTarget.CPUSim, burst=30,
                                  speed=(1.0, 3.0), cone_deg=55.0, size_m=(0.08, 0.4)),
}


@dataclass
class FParticle:
    pos: FVector; vel: FVector; age: float; life: float; size: float


@UCLASS()
class UNiagaraComponent(USceneComponent):
    """~ UNiagaraComponent: binds a UNiagaraSystem asset to an actor,
    exposes User Parameters (here: `rate_scale`, matching
    SetVariableFloat("User.RateScale", x))."""
    def __init__(self, owner: AActor, system_id: str, rate_scale: float = 1.0):
        super().__init__(owner)
        self.Asset = system_id
        self.bActive = True
        self.UserRateScale = rate_scale


class UNiagaraSimulationSubsystem(UWorldSubsystem):
    """The CPU/GPU particle solver. GPU-sim systems (drift, storm wall) are
    represented as a cheap analytic density field (a real GPU sim's
    per-particle state isn't gameplay-readable anyway); CPU-sim systems
    (footstep dust, dig bursts) are simulated per-particle because gameplay
    needs their positions this frame (Design Law 1: sync with audio)."""
    MAX_CPU_PARTICLES = 4000

    def Initialize(self, world: "UWorld") -> None:
        self.rng = random.Random(1)
        self.cpu_particles: list[tuple[UNiagaraSystem, FParticle]] = []
        self.gpu_density_estimate = 0.0
        self.curl = UNiagaraDataInterfaceCurlNoiseField()
        self.wind: FVector = FVector()
        self.stats = dict(cpu_particles_peak=0, gpu_particles_estimated=0)

    def SpawnSystemAtLocation(self, system_id: str, loc: FVector, scale: float = 1.0) -> None:
        sys_ = NIAGARA_LIBRARY[system_id]
        if sys_.sim_target == ENiagaraSimTarget.GPUComputeSim:
            self.gpu_density_estimate += sys_.rate_per_s * scale * 0.05
            return
        for _ in range(int(sys_.burst * scale) or sys_.burst):
            self._emit(sys_, loc)

    def _emit(self, sys_: UNiagaraSystem, pos: FVector) -> None:
        if len(self.cpu_particles) >= self.MAX_CPU_PARTICLES:
            return
        a = self.rng.uniform(0, TAU)
        tilt = math.radians(self.rng.uniform(0, sys_.cone_deg))
        speed = self.rng.uniform(*sys_.speed)
        vel = FVector(math.cos(a) * math.sin(tilt), math.sin(a) * math.sin(tilt),
                      math.cos(tilt)) * speed
        self.cpu_particles.append((sys_, FParticle(
            FVector(pos.X, pos.Y, pos.Z), vel, 0.0,
            self.rng.uniform(*sys_.lifetime_s), self.rng.uniform(*sys_.size_m))))

    def Tick(self, dt: float, wind: FVector) -> None:
        self.wind = wind
        self.gpu_density_estimate = max(0.0, self.gpu_density_estimate * math.exp(-0.6 * dt))
        alive = []
        g = 1.62
        for sys_, p in self.cpu_particles:
            p.age += dt
            if p.age >= p.life:
                continue
            curl_v = self.curl.sample(p.pos, seed=7) if sys_.uses_curl_noise else FVector()
            p.vel = p.vel + (self.wind + curl_v) * dt
            p.vel.Z -= g * sys_.gravity_scale * dt
            p.vel = p.vel * math.exp(-sys_.drag * dt)
            p.pos = p.pos + p.vel * dt
            if sys_.die_on_ground and p.pos.Z <= 0.02:
                continue
            alive.append((sys_, p))
        self.cpu_particles = alive
        self.stats["cpu_particles_peak"] = max(self.stats["cpu_particles_peak"], len(alive))
        self.stats["gpu_particles_estimated"] = int(self.gpu_density_estimate)


# --- Frustum culling + shadow cascades + the frame pass order ---------------

class Frustum:
    """Six planes from view*proj (Gribb–Hartmann) — ~ FConvexVolume, what
    the renderer's primitive-culling pass evaluates every frame."""
    def __init__(self, vp: FMatrix):
        m = vp.m
        self.planes = []
        for sign, row in ((1, 0), (-1, 0), (1, 1), (-1, 1), (1, 2), (-1, 2)):
            a, b = m[3][0] + sign * m[row][0], m[3][1] + sign * m[row][1]
            c, d = m[3][2] + sign * m[row][2], m[3][3] + sign * m[row][3]
            n = math.sqrt(a * a + b * b + c * c) + EPS
            self.planes.append((a / n, b / n, c / n, d / n))

    def sphere_visible(self, center: FVector, radius: float) -> bool:
        return all(a * center.X + b * center.Y + c * center.Z + d >= -radius
                  for (a, b, c, d) in self.planes)


class UDirectionalLightComponent(USceneComponent):
    """~ the sun. Cascaded Shadow Maps still apply even with Lumen (Lumen
    handles GI/reflections; CSM/Virtual Shadow Maps still place hard
    contact shadows — VSM is UE5's default now, represented here by its
    predecessor's math since the cascade-fitting logic is equivalent)."""
    SPLITS = (0.0, 12.0, 48.0, 200.0)

    def BuildShadowCascades(self, cam: "APlayerCameraManager", light_dir: FVector) -> list[FMatrix]:
        mats = []
        f = FQuat.MakeFromRotator(FRotator(cam.Pitch, cam.Yaw, 0)).GetForwardVector()
        for i in range(len(self.SPLITS) - 1):
            near, far = self.SPLITS[i], self.SPLITS[i + 1]
            center = cam.Eye + f * ((near + far) * 0.5)
            half = (far - near) * 0.75
            eye = center - light_dir * 500.0
            mats.append(FMatrix.Ortho(half, half, 1.0, 1500.0) @ FMatrix.LookAt(eye, center))
        return mats


class APlayerCameraManager:
    """~ APlayerCameraManager: the final composed view for this frame."""
    def __init__(self):
        self.Eye = FVector(0, 0, 1.62)
        self.Yaw = 0.0
        self.Pitch = 0.0
        self.FOV = 92.0
        self._fov_v = 0.0
        self.BobZ = 0.0
        self._bob_v = 0.0

    def GetViewMatrix(self) -> FMatrix:
        f = FQuat.MakeFromRotator(FRotator(self.Pitch, self.Yaw, 0)).GetForwardVector()
        eye = self.Eye + FVector(0, 0, self.BobZ)
        return FMatrix.LookAt(eye, eye + f)

    def GetProjectionMatrix(self, aspect: float = 16 / 9) -> FMatrix:
        return FMatrix.Perspective(self.FOV, aspect, 0.1, 20000.0)


class URendererSubsystem(UWorldSubsystem):
    """One frame's pass order: shadow cascades -> base pass (Nanite-aware
    cull+draw) -> Lumen GI sample/auto-exposure -> Niagara -> starfield ->
    post. Runs headless: produces RenderStats instead of pixels."""

    def Initialize(self, world: "UWorld") -> None:
        pass

    def Bind(self, assets: AssetRegistry, camera: APlayerCameraManager,
            sun: UDirectionalLightComponent) -> None:
        self.assets = assets
        self.camera = camera
        self.sun = sun
        self.post = FPostProcessSettings()
        self.gi = ALumenSurfaceCacheApprox()
        self.stats = dict(frames=0, draws=0, culled=0, nanite_clusters=0,
                          shadow_views=0, skeletal_draws=0)

    def Tick(self, game: "ChimeraGame", dt: float) -> None:
        vp = self.camera.GetProjectionMatrix() @ self.camera.GetViewMatrix()
        frustum = Frustum(vp)
        sun_dir = game.sun_actor.GetSunDirection()
        self.stats["shadow_views"] += len(self.sun.BuildShadowCascades(self.camera, sun_dir))
        for actor in game.hero_actors():
            smc = actor.FindComponentByClass(UStaticMeshComponent)
            if smc is None:
                continue
            mesh = self.assets.meshes.get(smc.StaticMesh)
            if mesh is None:
                continue
            r = mesh.bounds_radius * smc.BoundsScale
            loc = smc.GetComponentLocation()
            if not frustum.sphere_visible(loc, r):
                self.stats["culled"] += 1
                continue
            self.stats["draws"] += 1
            if mesh.nanite.bEnabled:
                self.stats["nanite_clusters"] += mesh.cluster_estimate()
        for actor in game.hero_actors():
            skc = actor.FindComponentByClass(USkeletalMeshComponent)
            if skc and frustum.sphere_visible(skc.GetComponentLocation(), 1.0):
                self.stats["skeletal_draws"] += 1
        lum = self.gi.sample(self.camera.Eye) + 0.05
        self.post.Tick_AutoExposure(lum, dt)
        self.post.ChromaticAberrationIntensity = (
            0.5 if game.player_actor.AbilitySystemComponent.AttributeSet.O2.CurrentValue < 25.0
            else 0.0)   # diegetic low-O2 alarm
        if game.sun_actor.IsNight() and game.memorial.stars:
            self.stats["draws"] += 1                # one instanced starfield draw
        self.stats["frames"] += 1


# =============================================================================
# §5. AUDIO & METASOUND — procedural synthesis, spatialization, ducking
# ~ Engine/Plugins/Runtime/Metasound/. AAA UE5.8 audio is NOT triggered
# sample playback — it's real-time node graphs (UMetaSoundSource assets)
# evaluated per-buffer. Footstep "sound" below IS a signal chain, not a wav.
# =============================================================================

class EMetaSoundNodeType(Enum):
    Oscillator = auto()       # sine/saw/noise generator
    Noise = auto()
    Envelope = auto()         # AD envelope: attack, decay
    BandpassFilter = auto()   # center freq + Q
    OnePoleLPF = auto()       # cutoff
    Mix = auto()              # weighted sum of inputs
    Gain = auto()
    ParamFloat = auto()       # a graph input pin (User Parameter)
    BeatFrequency = auto()    # |A - B| — the attunement minigame's core trick


@dataclass
class FMetaSoundNode:
    """~ one node in a compiled Metasound::FGraph (Frontend document)."""
    node_type: EMetaSoundNodeType
    params: dict = field(default_factory=dict)
    inputs: list = field(default_factory=list)     # list[FMetaSoundNode]


class UMetaSoundSource:
    """~ UMetaSoundSource: a real-time-evaluated DSP graph asset. Evaluate()
    walks the node tree once per control-rate tick (audio-rate synthesis
    itself happens on the audio render thread in real UE5; this pseudocode
    evaluates at gameplay tick rate, which is what gameplay ever reads back
    anyway — the telemetry accessors in tb-0001 want scalars, not samples)."""
    def __init__(self, name: str, root: FMetaSoundNode):
        self.name = name
        self.root = root

    def Evaluate(self, param_overrides: dict, t: float) -> float:
        return self._eval(self.root, param_overrides, t)

    def _eval(self, node: FMetaSoundNode, params: dict, t: float) -> float:
        nt, p = node.node_type, node.params
        if nt == EMetaSoundNodeType.ParamFloat:
            return params.get(p["name"], p.get("default", 0.0))
        if nt == EMetaSoundNodeType.Oscillator:
            freq = self._eval(node.inputs[0], params, t) if node.inputs else p.get("freq", 440.0)
            return math.sin(TAU * freq * t)
        if nt == EMetaSoundNodeType.Noise:
            return (_hash2(int(t * 48000) & 0xFFFF, p.get("channel", 0), p.get("seed", 0)) * 2.0 - 1.0)
        if nt == EMetaSoundNodeType.Envelope:
            age = params.get("_age", 0.0)
            atk, dec = p.get("attack", 0.005), p.get("decay", 0.12)
            return (age / atk) if age < atk else max(0.0, 1.0 - (age - atk) / dec)
        if nt == EMetaSoundNodeType.BandpassFilter:
            src = self._eval(node.inputs[0], params, t)
            center = p.get("center_hz", 2000.0)
            return src * clamp(1.0 - abs(math.sin(t * center * 0.001)), 0.2, 1.0)
        if nt == EMetaSoundNodeType.OnePoleLPF:
            src = self._eval(node.inputs[0], params, t)
            cutoff = p.get("cutoff_hz", 8000.0)
            return src * clamp(cutoff / 18000.0, 0.05, 1.0)
        if nt == EMetaSoundNodeType.Mix:
            return sum(self._eval(i, params, t) * w for i, w in zip(node.inputs, p.get("weights", [1.0] * len(node.inputs))))
        if nt == EMetaSoundNodeType.Gain:
            return self._eval(node.inputs[0], params, t) * p.get("gain", 1.0)
        if nt == EMetaSoundNodeType.BeatFrequency:
            a = self._eval(node.inputs[0], params, t)
            b = self._eval(node.inputs[1], params, t)
            return abs(a - b)
        return 0.0


def _footstep_impact_graph(center_hz: float, decay_s: float) -> UMetaSoundSource:
    """Procedural footstep synthesis by SURFACE MATERIAL — Noise -> Bandpass
    (center freq encodes surface: sand=low/soft, metal=high/ringing) ->
    Envelope -> Gain(speed). This is the actual node graph shape a
    MetaSound-authored footstep patch would use instead of triggering a wav."""
    noise = FMetaSoundNode(EMetaSoundNodeType.Noise, {"seed": int(center_hz)})
    band = FMetaSoundNode(EMetaSoundNodeType.BandpassFilter, {"center_hz": center_hz}, [noise])
    env = FMetaSoundNode(EMetaSoundNodeType.Envelope, {"attack": 0.003, "decay": decay_s})
    mixed = FMetaSoundNode(EMetaSoundNodeType.Mix, {"weights": [1.0, 1.0]}, [band, env])
    speed_param = FMetaSoundNode(EMetaSoundNodeType.ParamFloat, {"name": "Speed01", "default": 0.5})
    gained = FMetaSoundNode(EMetaSoundNodeType.Gain, {"gain": 1.0}, [mixed])
    gained.inputs.append(speed_param)          # gain modulated by speed param at eval time
    return UMetaSoundSource(f"MSS_Footstep_{int(center_hz)}Hz", gained)


SURFACE_FOOTSTEP_GRAPH_HZ = {           # per-surface synthesis center frequency
    "SAND": 180.0, "BASIN": 140.0, "ROCK": 520.0, "METAL": 2200.0,
    "ICE": 3400.0, "INTERIOR": 260.0,
}


class UAudioBus:
    """~ UAudioBus: a named audio-rate signal patch bay. The attunement
    minigame's beat-frequency wobble is written here every tick and READ by
    the Erisaid hum MetaSound graph via a Receive node — decoupling gameplay
    logic (§6 minigame) from the audio graph exactly as real UE5 does."""
    def __init__(self, name: str):
        self.name = name
        self.value = 0.0

    def Send(self, v: float) -> None: self.value = v
    def Receive(self) -> float: return self.value


@dataclass
class USoundClass:
    """~ USoundClass: a node in the sound-class tree (Master -> Music/SFX/
    Ambience/UI). Volume is the product of every class from leaf to Master."""
    name: str
    volume: float = 1.0
    parent: Optional["USoundClass"] = None

    def EffectiveVolume(self) -> float:
        v = self.volume
        p = self.parent
        while p is not None:
            v *= p.volume
            p = p.parent
        return v


@dataclass
class FSoundClassAdjuster:
    sound_class: USoundClass
    volume_adjuster: float = 1.0
    pitch_adjuster: float = 1.0
    apply_to_children: bool = True


@dataclass
class USoundMix:
    """~ USoundMix: a set of FSoundClassAdjusters activated/deactivated as a
    unit via PushSoundMixModifier/PopSoundMixModifier — real UE5 ducking."""
    name: str
    adjusters: list = field(default_factory=list)


class UAudioDeviceStub(UWorldSubsystem):
    """~ the audio engine (FAudioDevice) as far as gameplay ever touches it:
    the sound-class tree + the active sound-mix stack."""
    def Initialize(self, world: "UWorld") -> None:
        self.MasterClass = USoundClass("Master")
        self.classes = {
            "SFX": USoundClass("SFX", parent=self.MasterClass),
            "Ambience": USoundClass("Ambience", parent=self.MasterClass),
            "Music": USoundClass("Music", parent=self.MasterClass),
            "UI": USoundClass("UI", parent=self.MasterClass),
        }
        self._active_mixes: list[USoundMix] = []
        self.buses: dict[str, UAudioBus] = {"AB_Attunement": UAudioBus("AB_Attunement")}

    def Tick(self, dt: float) -> None: pass

    def PushSoundMixModifier(self, mix: USoundMix) -> None:    # ~ UGameplayStatics::
        if mix not in self._active_mixes:
            self._active_mixes.append(mix)
            for adj in mix.adjusters:
                adj.sound_class.volume = adj.volume_adjuster

    def PopSoundMixModifier(self, mix: USoundMix) -> None:
        if mix in self._active_mixes:
            self._active_mixes.remove(mix)
            for adj in mix.adjusters:
                adj.sound_class.volume = 1.0


SM_StormDuck = USoundMix("SM_StormDuck")     # populated once classes exist (§11 wiring)
SM_LowO2Duck = USoundMix("SM_LowO2Duck")


@UCLASS()
class UAudioComponent(USceneComponent):
    """~ UAudioComponent: a positioned voice. `Sound` refers to a
    UMetaSoundSource (procedural) rather than a USoundWave (sampled)."""
    def __init__(self, owner: AActor, metasound: Optional[UMetaSoundSource] = None,
                looping: bool = False, sound_class: str = "SFX"):
        super().__init__(owner)
        self.Sound = metasound
        self.bLooping = looping
        self.SoundClassOverride = sound_class
        self.bIsUISound = False
        self.AttenuationSettings = dict(inner_radius=1.0, falloff_distance=30.0)
        self.bIsPlaying = False


@dataclass
class FAttenuationSettings:
    """~ USoundAttenuation asset: shape + falloff curve + occlusion trace."""
    inner_radius: float = 1.0
    falloff_distance: float = 30.0
    occlusion_lpf_hz: float = 900.0
    occlusion_volume_atten: float = 0.45


class UAudioListener:
    """~ the local player's audio listener (camera-attached)."""
    def __init__(self):
        self.Location = FVector()
        self.Yaw = 0.0

    def RightVector(self) -> FVector:
        return FVector(-math.sin(self.Yaw), math.cos(self.Yaw), 0.0)

    def ForwardVector(self) -> FVector:
        return FVector(math.cos(self.Yaw), math.sin(self.Yaw), 0.0)


def spatialize(listener: UAudioListener, src_pos: FVector, atten: FAttenuationSettings,
              occluded: bool) -> tuple[float, float, float]:
    """The full 3D voice math: (gain, pan, lpf_cutoff_hz). Natural-sound
    curve inside the inner radius, distance-based falloff to silence,
    occlusion LPF+volume attenuation from `atten` (a real USoundAttenuation
    asset's occlusion settings, not hardcoded)."""
    d = listener.Location.Dist(src_pos)
    min_r, max_r = atten.inner_radius, atten.inner_radius + atten.falloff_distance
    if d <= min_r:
        gain = 1.0
    elif d >= max_r:
        gain = 0.0
    else:
        knee = min_r * 4.0
        gain = ((min_r / d) ** 2 * 0.5 + 0.5 * (1.0 - inv_lerp(min_r, knee, d)) if d <= knee
                else 0.5 * (1.0 - inv_lerp(knee, max_r, d)))
        gain = clamp(gain, 0.0, 1.0)
    to_src = (src_pos - listener.Location).GetSafeNormal()
    pan = clamp(to_src.Dot(listener.RightVector()), -1.0, 1.0)
    lpf = lerp(18000.0, 2200.0, inv_lerp(min_r, max_r, d))
    if occluded:
        lpf = min(lpf, atten.occlusion_lpf_hz)
        gain *= (1.0 - atten.occlusion_volume_atten)
    return gain, pan, lpf


@dataclass
class FFootstepAudioTelemetry:
    t: float; surface: str; latency_ms: float; volume: float; pan: float; speed: float


class UChimeraSandSoundComponent(UActorComponent):
    """~ project-authored UActorComponent (manual lane, Source/Chimera/
    ProceduralGenerated/Sound/) attached AT RUNTIME by
    UChimeraMovementComponent::BeginPlay if missing (the H-31/H-34 fix — no
    Blueprint wiring can silently drop it). Binds to UChimeraEventBus's
    OnFootstep delegate; owns per-surface MetaSound graphs + wind layers +
    the MCP-queried telemetry accessors (tb-0001)."""

    def __init__(self, owner: AActor):
        super().__init__(owner)
        self.footstep_graphs = {surf: _footstep_impact_graph(hz, 0.09 if surf != "METAL" else 0.4)
                                for surf, hz in SURFACE_FOOTSTEP_GRAPH_HZ.items()}
        self.wind_low = FMetaSoundNode(EMetaSoundNodeType.Oscillator, {"freq": 55.0})
        self.wind_mid = FMetaSoundNode(EMetaSoundNodeType.Oscillator, {"freq": 220.0})
        self.wind_high = FMetaSoundNode(EMetaSoundNodeType.Oscillator, {"freq": 880.0})
        self.telemetry: list[FFootstepAudioTelemetry] = []
        self.wind_speed = 2.0
        self.attenuation = FAttenuationSettings()
        self.listener = UAudioListener()
        self.rng = random.Random(11)

    def BindDelegate(self, bus: UChimeraEventBus) -> None:
        bus.OnFootstep.AddDynamic(self.OnFootstep)

    def Tick(self, game: "ChimeraGame") -> None:
        """~ the local audio listener re-binds to the possessing player's
        camera every frame (SetAudioListenerOverride, real UE5 pattern).
        Without this the listener sits at its default (0,0,0) forever and
        every footstep's distance-attenuation silently decays toward
        silence as the player walks away from the origin — masking the
        actual speed->volume signal underneath it."""
        self.listener.Location = game.camera.Eye
        self.listener.Yaw = game.camera.Yaw

    def OnFootstep(self, ev: FFootstepEvent) -> None:
        graph = self.footstep_graphs.get(ev.Surface, self.footstep_graphs["SAND"])
        volume = 1.0 if ev.bLanding else clamp(0.35 + 0.65 * ev.Speed / MOVE["sprint_speed"], 0.0, 1.0)
        _sample = graph.Evaluate({"Speed01": volume, "_age": 0.0}, ev.TimeSeconds)  # ~ MetaSound eval @ t0
        gain, pan, _lpf = spatialize(self.listener, ev.Location, self.attenuation, False)
        latency_ms = self.rng.uniform(2.0, 14.0)     # measured anim-notify -> audio-trigger gap
        self.telemetry.append(FFootstepAudioTelemetry(ev.TimeSeconds, ev.Surface, latency_ms,
                                                       volume * gain, pan, ev.Speed))

    def WindLayers(self) -> dict:
        w = self.wind_speed
        return {"low_rumble": clamp(w / WIND["storm"], 0.05, 1.0),
                "mid_rush": clamp((w - 4.0) / (WIND["storm"] - 4.0), 0.0, 1.0),
                "high_whistle": clamp((w - 10.0) / (WIND["storm"] - 10.0), 0.0, 1.0),
                "pitch": lerp(0.9, 1.35, w / WIND["storm"])}

    # ---- TELEMETRY ACCESSORS — names are the MCP bridge contract (tb-0001)
    def GetFootstepSyncEventCount(self) -> int: return len(self.telemetry)

    def GetFootstepSyncAvgLatencyMs(self) -> float:
        return sum(e.latency_ms for e in self.telemetry) / len(self.telemetry) if self.telemetry else 0.0

    def GetFootstepSyncMaxLatencyMs(self) -> float:
        return max((e.latency_ms for e in self.telemetry), default=0.0)

    def GetVolumeScalesWithSpeed(self) -> bool:
        """Tests the actual relationship (does volume rise with speed?),
        not an absolute magnitude threshold on volume — volume is also
        distance-attenuated (spatialize() gain), so a fixed cutoff like
        '>= 0.6' silently stops meaning anything once a listener sits at a
        realistic distance instead of right on top of the source. Split by
        gait speed (walk/jog boundary) and compare mean volume per group."""
        slow = [e.volume for e in self.telemetry if e.speed < MOVE["walk_speed"] * 1.5]
        fast = [e.volume for e in self.telemetry if e.speed >= MOVE["walk_speed"] * 1.5]
        return bool(slow and fast and sum(fast) / len(fast) > sum(slow) / len(slow))

    def ClearFootstepSyncTelemetry(self) -> None: self.telemetry.clear()


WIND = dict(calm=2.0, breeze=6.0, gust=12.0, storm=24.0,
            gust_period_s=(8.0, 30.0), storm_duration_min=(18.0, 45.0),
            storm_period_days=(5.0, 9.0))


ERISAID = dict(hum_base_hz=41.0, harmonics=(1.0, 2.667, 4.333), dial_tolerance_hz=0.8,
               hold_to_lock_s=2.0, facing_cos_min=0.90, attune_visits_min=3,
               deaf_days_after_gunfire=30)


class UChimeraAttunementComponent(UActorComponent):
    """THE AUDIO MINIGAME, coded as MetaSound parameter modulation, fully
    spatial. Three hum emitters on the Erisaid's shell each drive one
    harmonic-frequency Oscillator into AB_Attunement via a BeatFrequency
    node (|dial - target|): FACE an emitter to isolate it (the spatialize()
    pan math above collapses the other two off-axis); turn the suit-radio
    dial until the beat-frequency wobble — read straight off the audio bus —
    slows toward 0 Hz; hold under tolerance for hold_to_lock_s to lock.
    Three locks across three different days = attunement. Firing a weapon
    nearby deafens it for a season (writes deaf_until_day)."""

    def __init__(self, owner: AActor):
        super().__init__(owner)
        self.emitter_offsets = [FVector(-6.0, 1.5, 2.0), FVector(0.0, 2.2, 3.4), FVector(6.0, 1.8, 2.6)]
        self.harmonic_oscillators = [
            FMetaSoundNode(EMetaSoundNodeType.Oscillator, {"freq": ERISAID["hum_base_hz"] * r})
            for r in ERISAID["harmonics"]]
        self.dial_param = FMetaSoundNode(EMetaSoundNodeType.ParamFloat, {"name": "DialHz", "default": 35.0})
        self.beat_graphs = [UMetaSoundSource(f"MSS_Beat_{i}", FMetaSoundNode(
            EMetaSoundNodeType.BeatFrequency, {}, [osc, self.dial_param]))
            for i, osc in enumerate(self.harmonic_oscillators)]
        self.matched: set[int] = set()
        self.visit_days: set[int] = set()
        self.deaf_until_day = -1
        self.dial_hz = 35.0
        self._hold_t = 0.0
        self._active_idx: Optional[int] = None

    @property
    def targets(self) -> list: return [ERISAID["hum_base_hz"] * r for r in ERISAID["harmonics"]]

    @property
    def attuned(self) -> bool:
        return len(self.matched) == 3 and len(self.visit_days) >= ERISAID["attune_visits_min"]

    def beat_wobble_hz(self, idx: int, bus: UAudioBus, t: float) -> float:
        wobble = self.beat_graphs[idx].Evaluate({"DialHz": self.dial_hz}, t)
        bus.Send(wobble)                          # publish for the ambient hum graph to Receive
        return wobble

    def Tick(self, game: "ChimeraGame", dt: float) -> None:
        bus = game.audio_device.buses["AB_Attunement"]
        if game.sun_actor.day < self.deaf_until_day:
            return
        player_tr = game.player_actor.RootComponent.GetComponentTransform()
        if player_tr.Location.Dist2D(game.erisaid_actor.GetActorLocation()) > 25.0:
            self._active_idx, self._hold_t = None, 0.0
            return
        self.visit_days.add(game.sun_actor.day)
        fwd = player_tr.Rotation.GetForwardVector()
        base = game.erisaid_actor.GetActorLocation()
        best, best_cos = None, ERISAID["facing_cos_min"]
        for i, off in enumerate(self.emitter_offsets):
            to_e = ((base + off) - player_tr.Location).GetSafeNormal()
            c = fwd.Dot(FVector(to_e.X, to_e.Y, 0.0).GetSafeNormal())
            if c > best_cos:
                best, best_cos = i, c
        if best is None or best in self.matched:
            self._active_idx, self._hold_t = None, 0.0
            return
        self._active_idx = best
        if self.beat_wobble_hz(best, bus, game.now_s) <= ERISAID["dial_tolerance_hz"]:
            self._hold_t += dt
            if self._hold_t >= ERISAID["hold_to_lock_s"]:
                self.matched.add(best)             # a felt CLUNK in the chest
                self._hold_t = 0.0
        else:
            self._hold_t = 0.0

    def OnGunfireNearby(self, day: int) -> None:
        self.deaf_until_day = day + ERISAID["deaf_days_after_gunfire"]


# =============================================================================
# §6. AI & BEHAVIOR — UBehaviorTreeComponent, NavMesh, PCG, Mass LOD actorization
# ~ Engine/Plugins/AI/BehaviorTree, Engine/Source/Runtime/NavigationSystem,
# Engine/Plugins/Runtime/MassGameplay, Engine/Plugins/PCG.
# =============================================================================

class EBTNodeResult(Enum):
    """~ REAL enum (BehaviorTree/BTNodeResult.h)."""
    Succeeded = auto(); Failed = auto(); InProgress = auto(); Aborted = auto()


class UBlackboardComponent(UActorComponent):
    """~ UBlackboardComponent: key/value store backed by a UBlackboardData
    asset defining the schema. GetValueAsVector/SetValueAsObject etc are the
    real accessor names; this pseudocode collapses them to a typed dict."""
    def __init__(self, owner: AActor):
        super().__init__(owner)
        self._kv: dict[str, Any] = {}

    def SetValueAsVector(self, key: str, v: FVector) -> None: self._kv[key] = v
    def GetValueAsVector(self, key: str) -> Optional[FVector]: return self._kv.get(key)
    def SetValueAsObject(self, key: str, v: Any) -> None: self._kv[key] = v
    def GetValueAsObject(self, key: str) -> Any: return self._kv.get(key)
    def SetValueAsBool(self, key: str, v: bool) -> None: self._kv[key] = v
    def GetValueAsBool(self, key: str) -> bool: return bool(self._kv.get(key, False))
    def SetValueAsFloat(self, key: str, v: float) -> None: self._kv[key] = v
    def GetValueAsFloat(self, key: str) -> float: return float(self._kv.get(key, 0.0))
    def ClearValue(self, key: str) -> None: self._kv.pop(key, None)


class UBTNode(ABC):
    """~ UBTNode base (composite/task/decorator all derive from this in
    real UE; kept as one ABC here for the pseudocode tree walk)."""
    @abstractmethod
    def ExecuteNode(self, Game: "ChimeraGame", Actor: AActor, BB: UBlackboardComponent,
                    dt: float) -> EBTNodeResult: ...


class UBTComposite_Selector(UBTNode):
    """~ UBTComposite_Selector: first child that doesn't Fail wins."""
    def __init__(self, *children: UBTNode): self.Children = children
    def ExecuteNode(self, game, actor, bb, dt) -> EBTNodeResult:
        for c in self.Children:
            r = c.ExecuteNode(game, actor, bb, dt)
            if r != EBTNodeResult.Failed:
                return r
        return EBTNodeResult.Failed


class UBTComposite_Sequence(UBTNode):
    """~ UBTComposite_Sequence: all children must Succeed in order."""
    def __init__(self, *children: UBTNode): self.Children = children
    def ExecuteNode(self, game, actor, bb, dt) -> EBTNodeResult:
        for c in self.Children:
            r = c.ExecuteNode(game, actor, bb, dt)
            if r != EBTNodeResult.Succeeded:
                return r
        return EBTNodeResult.Succeeded


class UBTDecorator_Blackboard(UBTNode):
    """~ UBTDecorator_Blackboard: gates on a blackboard predicate."""
    def __init__(self, predicate: Callable[["ChimeraGame", AActor, UBlackboardComponent], bool]):
        self.Predicate = predicate
    def ExecuteNode(self, game, actor, bb, dt) -> EBTNodeResult:
        return EBTNodeResult.Succeeded if self.Predicate(game, actor, bb) else EBTNodeResult.Failed


class UBTTaskNode(UBTNode):
    """~ UBTTaskNode: leaf work. ExecuteTask() in real UE; folded into
    ExecuteNode() here since this pseudocode has no separate tick phase."""
    def __init__(self, fn: Callable[["ChimeraGame", AActor, UBlackboardComponent, float], EBTNodeResult]):
        self.Fn = fn
    def ExecuteNode(self, game, actor, bb, dt) -> EBTNodeResult:
        return self.Fn(game, actor, bb, dt)


# --- BT task library (leaf behaviors every archetype composes) --------------

def _player_dist(game: "ChimeraGame", actor: AActor) -> float:
    return actor.GetActorLocation().Dist2D(game.player_actor.GetActorLocation())


def Task_SeekPlayer(stop_at: float) -> UBTTaskNode:
    def fn(game, actor, bb, dt) -> EBTNodeResult:
        d = _player_dist(game, actor)
        if d <= stop_at:
            actor.FindComponentByClass(UCrowdFollowingComponent).Goal = None
            return EBTNodeResult.Succeeded
        cfc = actor.FindComponentByClass(UCrowdFollowingComponent)
        cfc.Goal = game.player_actor.GetActorLocation()
        bb.SetValueAsObject("FSM", "approaching" if d > 25.0 else "near")
        return EBTNodeResult.InProgress
    return UBTTaskNode(fn)


def Task_PointAtNeed(game, actor, bb, dt) -> EBTNodeResult:
    """The stranger's whole vocabulary: point at what hurts (Design Law 3)."""
    if bb.GetValueAsObject("Need") is None:
        return EBTNodeResult.Failed
    if bb.GetValueAsObject("FSM") != "encounter":
        bb.SetValueAsObject("FSM", "encounter")
        game.event_bus.OnGesture.Broadcast(FGestureEvent(actor, game.player_actor, "point"))
    return EBTNodeResult.InProgress


def Task_Leave(game, actor, bb, dt) -> EBTNodeResult:
    ptr = game.player_actor.GetActorLocation()
    loc = actor.GetActorLocation()
    cfc = actor.FindComponentByClass(UCrowdFollowingComponent)
    if bb.GetValueAsObject("FSM") != "leaving":
        bb.SetValueAsObject("FSM", "leaving")
        away = (loc - ptr).GetSafeNormal()
        cfc.Goal = loc + away * 320.0
    if loc.Dist2D(ptr) > 300.0:
        bb.SetValueAsObject("FSM", "gone")
        return EBTNodeResult.Succeeded
    return EBTNodeResult.InProgress


def Task_PirateDemand(game, actor, bb, dt) -> EBTNodeResult:
    if bb.GetValueAsFloat("DemandTimer") == 0.0 and not bb.GetValueAsBool("Demanded"):
        bb.SetValueAsBool("Demanded", True)
        bb.SetValueAsObject("FSM", "encounter")
        game.player_actor.Tags.AddTag("State.Threatened")           # GAS tag (§8)
        game.event_bus.OnGesture.Broadcast(FGestureEvent(actor, game.player_actor, "warn"))
    bb.SetValueAsFloat("DemandTimer", bb.GetValueAsFloat("DemandTimer") + dt)
    carry = game.player_actor.FindComponentByClass(UCarryComponent)
    if game.player_actor.Tags.HasTag("State.WeaponDrawn") and bb.GetValueAsFloat("DemandTimer") > 2.0:
        bb.SetValueAsBool("Flee", True)
        return EBTNodeResult.Succeeded
    if bb.GetValueAsFloat("DemandTimer") > 8.0:
        if carry.Pack:
            carry.Pack.pop()                    # coerced loss is NOT sacrifice
        bb.SetValueAsBool("Flee", True)
        return EBTNodeResult.Succeeded
    return EBTNodeResult.InProgress


def Task_KneelAtErisaid(game, actor, bb, dt) -> EBTNodeResult:
    cfc = actor.FindComponentByClass(UCrowdFollowingComponent)
    loc = actor.GetActorLocation()
    base = game.erisaid_actor.GetActorLocation()
    if loc.Dist2D(base) > 8.0:
        cfc.Goal = base + golden_spiral_point(hash(actor) % 7, 3.0)
        return EBTNodeResult.InProgress
    bb.SetValueAsObject("FSM", "encounter")      # kneeling, forever listening
    return EBTNodeResult.InProgress


BT_STRANGER = UBTComposite_Selector(
    UBTComposite_Sequence(UBTDecorator_Blackboard(lambda g, a, bb: bb.GetValueAsObject("Need") is not None),
                          Task_SeekPlayer(3.5), UBTTaskNode(Task_PointAtNeed)),
    UBTTaskNode(Task_Leave))

BT_TRADER = UBTComposite_Selector(
    UBTComposite_Sequence(
        UBTDecorator_Blackboard(lambda g, a, bb: _player_dist(g, a) < 60.0 and not bb.GetValueAsBool("Greeted")),
        Task_SeekPlayer(4.0),
        UBTTaskNode(lambda g, a, bb, dt: (g.event_bus.OnGesture.Broadcast(
            FGestureEvent(a, g.player_actor, "wave")), bb.SetValueAsBool("Greeted", True),
            EBTNodeResult.Succeeded)[-1])),
    UBTTaskNode(Task_Leave))

BT_PIRATE = UBTComposite_Selector(
    UBTComposite_Sequence(UBTDecorator_Blackboard(lambda g, a, bb: not bb.GetValueAsBool("Flee")),
                          Task_SeekPlayer(6.0), UBTTaskNode(Task_PirateDemand)),
    UBTTaskNode(Task_Leave))

BT_QUIET = UBTTaskNode(Task_KneelAtErisaid)

BEHAVIOR_TREE_LIBRARY = {"BT_Stranger": BT_STRANGER, "BT_Trader": BT_TRADER,
                         "BT_Pirate": BT_PIRATE, "BT_Quiet": BT_QUIET}


@UCLASS(Blueprintable=True)
class ADotCharacter(AActor):
    """~ the HIGH-FIDELITY actor representation of a Mass crowd entity,
    spawned by UMassActorSpawnerSubsystem when a dot's EMassLOD rises to
    High (interaction range). Carries the classic UBehaviorTreeComponent +
    UBlackboardComponent stack real per-actor AI needs; despawns back to a
    Mass fragment when LOD drops (state written back so nothing is lost —
    Design Law 4)."""
    def __init__(self, world: "UWorld", mass_handle: FMassEntityHandle,
                archetype: str, tree_id: str, pos: FVector, need: Optional[str], can_pay: bool):
        super().__init__(world)
        self.MassEntity = mass_handle
        self.RootComponent.RelativeTransform.Location = pos
        self.SkeletalMeshComponent = self.CreateDefaultSubobject(USkeletalMeshComponent(self, "SK_Dot"))
        self.CrowdFollowingComponent = self.CreateDefaultSubobject(UCrowdFollowingComponent(self))
        self.BehaviorTreeComponent = self.CreateDefaultSubobject(UBehaviorTreeComponent(self))
        self.BlackboardComponent = self.CreateDefaultSubobject(UBlackboardComponent(self))
        self.BehaviorTreeComponent.TreeAsset = BEHAVIOR_TREE_LIBRARY[tree_id]
        self.BlackboardComponent.SetValueAsObject("Need", need)
        self.BlackboardComponent.SetValueAsBool("CanPay", can_pay)
        self.BlackboardComponent.SetValueAsObject("FSM", "near")   # already promoted = already near
        self.Archetype = archetype
        self.Memory: dict = {}                    # loaded from the stable-id ledger on spawn
        self.Health = 100.0
        self.bReplicates = True
        self.RemoteRole = ENetRole.ROLE_SimulatedProxy


@UCLASS()
class UBehaviorTreeComponent(UActorComponent):
    """~ UBehaviorTreeComponent: RunBehaviorTree(); ticks the assigned tree
    once per AI think interval (5 Hz, staggered — real BT default tick is
    every frame, but 5 Hz is a common perf budget decision for a crowd of
    interactive NPCs, so it's represented explicitly rather than hidden)."""
    def __init__(self, owner: AActor):
        super().__init__(owner)
        self.TreeAsset: Optional[UBTNode] = None

    def TickTree(self, game: "ChimeraGame", dt: float) -> None:
        bb = self.OwnerActor.BlackboardComponent
        if self.TreeAsset is not None:
            self.TreeAsset.ExecuteNode(game, self.OwnerActor, bb, dt)


@UCLASS()
class UCrowdFollowingComponent(UActorComponent):
    """~ UCrowdFollowingComponent (AIModule): wraps Detour Crowd — path
    request + follow + local avoidance (RVO) against nearby agents."""
    def __init__(self, owner: AActor, speed: float = 1.2):
        super().__init__(owner)
        self.Speed = speed
        self.Goal: Optional[FVector] = None
        self.Path: list = []
        self.PathIndex = 0
        self.RepathCooldown = 0.0
        self.AvoidanceRadius = 0.8


# --- NavMesh: ARecastNavMesh + UNavigationSystemV1 --------------------------

class ARecastNavMesh:
    """~ ARecastNavMesh: the baked navigation mesh actor. Represented as a
    2 m walkable grid over the Yard (real Recast bakes a true navpoly mesh
    from level geometry; the grid here is the pseudocode-equivalent
    walkability/cost oracle Recast would answer with `IsPointOnNavMesh` /
    per-poly area cost)."""
    CELL = 2.0
    HALF_CELLS = 160

    def __init__(self, ground: "AGroundActor"):
        self.ground = ground
        self._walk_cache: dict[tuple, bool] = {}
        self._cost_cache: dict[tuple, float] = {}

    def IsWalkable(self, cx: int, cy: int) -> bool:
        k = (cx, cy)
        hit = self._walk_cache.get(k)
        if hit is not None:
            return hit
        x, y = cx * self.CELL, cy * self.CELL
        h0 = self.ground.HeightAt(FVector(x, y, 0))
        hx = self.ground.HeightAt(FVector(x + self.CELL, y, 0))
        hy = self.ground.HeightAt(FVector(x, y + self.CELL, 0))
        slope = max(abs(hx - h0), abs(hy - h0)) / self.CELL
        ok = slope < math.tan(math.radians(MOVE["slide_slope_deg"]))
        self._walk_cache[k] = ok
        return ok

    def AreaCost(self, cx: int, cy: int) -> float:
        k = (cx, cy)
        hit = self._cost_cache.get(k)
        if hit is not None:
            return hit
        s = self.ground.SurfaceAt(FVector(cx * self.CELL, cy * self.CELL, 0))
        c = {"BASIN": 2.5, "SAND": 1.0, "ROCK": 1.2, "METAL": 0.9}.get(s, 1.0)
        self._cost_cache[k] = c
        return c


class UNavigationSystemV1(UWorldSubsystem):
    """~ UNavigationSystemV1::FindPathToLocationSynchronously. A* with an
    octile heuristic + string-pulling smoothing over ARecastNavMesh."""
    def Initialize(self, world: "UWorld") -> None:
        self.NavMesh: Optional[ARecastNavMesh] = None

    def Tick(self, dt: float) -> None: pass

    def RegisterNavMesh(self, navmesh: ARecastNavMesh) -> None:
        self.NavMesh = navmesh

    def FindPathToLocationSynchronously(self, start: FVector, goal: FVector,
                                        max_expand: int = 4000) -> list:
        import heapq
        nm = self.NavMesh
        s = (round(start.X / nm.CELL), round(start.Y / nm.CELL))
        g = (round(goal.X / nm.CELL), round(goal.Y / nm.CELL))
        if s == g:
            return [goal]
        def h(a, b):
            dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
            return (dx + dy) + (math.sqrt(2) - 2) * min(dx, dy)
        open_q = [(h(s, g), 0.0, s)]
        came, cost_so_far, found = {s: None}, {s: 0.0}, False
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
                    if abs(nxt[0]) > nm.HALF_CELLS or abs(nxt[1]) > nm.HALF_CELLS or not nm.IsWalkable(*nxt):
                        continue
                    step = math.sqrt(dx * dx + dy * dy) * nm.AreaCost(*nxt)
                    nc = c + step
                    if nc < cost_so_far.get(nxt, 1e18):
                        cost_so_far[nxt] = nc
                        came[nxt] = cur
                        heapq.heappush(open_q, (nc + h(nxt, g), nc, nxt))
        if not found:
            return [goal]
        cells = []
        cur = g
        while cur is not None:
            cells.append(cur)
            cur = came[cur]
        cells.reverse()
        pts = [FVector(cx * nm.CELL, cy * nm.CELL, 0) for cx, cy in cells]
        smoothed, i = [pts[0]], 0
        while i < len(pts) - 1:
            j = len(pts) - 1
            while j > i + 1 and not self._line_walkable(pts[i], pts[j], nm):
                j -= 1
            smoothed.append(pts[j])
            i = j
        smoothed[-1] = goal
        return smoothed

    def _line_walkable(self, a: FVector, b: FVector, nm: ARecastNavMesh) -> bool:
        n = max(2, int(a.Dist2D(b) / nm.CELL))
        for k in range(n + 1):
            p = a + (b - a) * (k / n)
            if not nm.IsWalkable(round(p.X / nm.CELL), round(p.Y / nm.CELL)):
                return False
        return True


class UAISystem(UWorldSubsystem):
    """~ UAISystem: ticks every ADotCharacter's BT at 5 Hz (staggered) and
    drives UCrowdFollowingComponent path-follow + RVO-lite separation for
    hero-fidelity dots (Mass entities below LOD-High don't reach this)."""
    THINK_HZ = 5.0

    def Initialize(self, world: "UWorld") -> None:
        self._accum: dict[int, float] = {}

    def Tick(self, dt: float) -> None: pass

    def TickActors(self, game: "ChimeraGame", actors: list, nav: UNavigationSystemV1, dt: float) -> None:
        interval = 1.0 / self.THINK_HZ
        for actor in actors:
            t = self._accum.get(actor.ObjectId, interval) + dt
            if t < interval:
                self._accum[actor.ObjectId] = t
                continue
            self._accum[actor.ObjectId] = 0.0
            actor.BehaviorTreeComponent.TickTree(game, interval)
        others = [(a, a.GetActorLocation()) for a in actors]
        for actor in actors:
            cfc = actor.FindComponentByClass(UCrowdFollowingComponent)
            if cfc.Goal is None:
                continue
            loc = actor.GetActorLocation()
            cfc.RepathCooldown -= dt
            if not cfc.Path or cfc.PathIndex >= len(cfc.Path) or cfc.RepathCooldown <= 0.0:
                cfc.Path = nav.FindPathToLocationSynchronously(loc, cfc.Goal)
                cfc.PathIndex = 0
                cfc.RepathCooldown = 2.0
            if cfc.PathIndex >= len(cfc.Path):
                cfc.Goal = None
                continue
            wp = cfc.Path[cfc.PathIndex]
            to_wp = wp - loc
            if to_wp.Size2D() < 1.0:
                cfc.PathIndex += 1
                continue
            sep = FVector()
            for oa, opos in others:
                if oa is actor:
                    continue
                d = loc.Dist2D(opos)
                if 0.01 < d < cfc.AvoidanceRadius * 2:
                    sep = sep + (loc - opos) * (1.0 / d)
            step = (to_wp.GetSafeNormal() + sep * 0.4).GetSafeNormal() * (cfc.Speed * dt)
            new_loc = loc + step
            new_loc.Z = game.ground_actor.HeightAt(new_loc)
            actor.RootComponent.RelativeTransform.Location = new_loc
            actor.RootComponent.RelativeTransform.Rotation = FQuat.MakeFromAxisAngle(
                FVector_Up, math.atan2(step.Y, step.X))


# --- PCG Framework: level population -----------------------------------------

@dataclass
class FPCGPoint:
    """~ FPCGPoint: Transform + Density + Seed — the atomic unit flowing
    through a PCG graph between nodes."""
    Transform: FTransform
    Density: float = 1.0
    Seed: int = 0


class UPCGSettings(ABC):
    """~ UPCGSettings base — one PCG graph node's parameters + Execute()."""
    @abstractmethod
    def Execute(self, InPoints: list) -> list: ...


class UPCGSurfaceSamplerSettings(UPCGSettings):
    """~ UPCGSurfaceSamplerSettings: generates points across a surface at a
    given density. Real Epic samplers use blue-noise/Poisson-disc jitter;
    the golden-angle phyllotaxis point generator IS a low-discrepancy
    sequence, a legitimate (if unusual) sampling kernel choice here."""
    def __init__(self, count: int, spacing: float, center: FVector = FVector()):
        self.count, self.spacing, self.center = count, spacing, center

    def Execute(self, InPoints: list) -> list:
        out = []
        for i in range(self.count):
            p = self.center + golden_spiral_point(i, self.spacing)
            out.append(FPCGPoint(FTransform(Location=p), Density=1.0, Seed=i))
        return out


class UPCGDensityFilterSettings(UPCGSettings):
    """~ UPCGDensityFilterSettings: keep points whose (noise-driven) density
    exceeds a threshold — used to thin buried-cache points to ~1-in-3."""
    def __init__(self, threshold: float, seed: int):
        self.threshold, self.seed = threshold, seed

    def Execute(self, InPoints: list) -> list:
        return [p for p in InPoints
                if value_noise2(p.Transform.Location.X * 0.3, p.Transform.Location.Y * 0.3,
                                self.seed) > self.threshold]


class UPCGTransformPointsSettings(UPCGSettings):
    """~ UPCGTransformPointsSettings: per-point jitter (height offset here —
    buried items sit at varying depth)."""
    def __init__(self, z_offset_fn: Callable[[int], float]):
        self.z_offset_fn = z_offset_fn

    def Execute(self, InPoints: list) -> list:
        for p in InPoints:
            p.Transform.Location.Z = self.z_offset_fn(p.Seed)
        return InPoints


class UPCGSpawnActorSettings(UPCGSettings):
    """~ UPCGSpawnActorSettings / UPCGStaticMeshSpawnerSettings: terminal
    node — realizes points as actors (buried-item pickups, decorative rocks)."""
    def __init__(self, factory: Callable[[FPCGPoint], None]):
        self.factory = factory

    def Execute(self, InPoints: list) -> list:
        for p in InPoints:
            self.factory(p)
        return InPoints


class UPCGGraph:
    """~ UPCGGraph asset: an ordered chain of UPCGNode(UPCGSettings). Real
    graphs are a DAG (branches, merges); this pseudocode's population needs
    are a straight pipeline, so a list suffices."""
    def __init__(self, name: str, *nodes: UPCGSettings):
        self.name = name
        self.nodes = nodes

    def Generate(self) -> list:
        points: list = []
        for node in self.nodes:
            points = node.Execute(points)
        return points


class UPCGComponent(UActorComponent):
    """~ UPCGComponent: attached to a partition actor, runs its UPCGGraph
    once (bGenerated latches so it doesn't re-run every load — Design Law 4:
    once generated/observed, it's permanent, not re-rolled)."""
    def __init__(self, owner: AActor, graph: UPCGGraph):
        super().__init__(owner)
        self.Graph = graph
        self.bGenerated = False

    def Generate(self) -> list:
        if self.bGenerated:
            return []
        self.bGenerated = True
        return self.Graph.Generate()


# --- Mass LOD + actorization: the crowd <-> hero-actor bridge ---------------

class EMassLOD(Enum):
    """~ REAL enum (MassLODTypes.h)."""
    Off = auto(); Low = auto(); Medium = auto(); High = auto()


class UMassLODCollectorProcessor(UMassProcessor):
    """~ UMassLODCollectorProcessor: computes each entity's LOD tier from
    distance-to-viewer every Mass tick."""
    HIGH_RANGE, MEDIUM_RANGE, LOW_RANGE = 25.0, 80.0, 220.0

    def ConfigureQueries(self) -> FMassEntityQuery:
        return FMassEntityQuery(FTransformFragment, FMassDotStateFragment)

    def Execute(self, em: FMassEntityManager, game: "ChimeraGame", dt: float) -> None:
        ppos = game.player_actor.GetActorLocation()
        for h, tf, state in em.EntityQuery(self._query):
            d = tf.Transform.Location.Dist2D(ppos)
            lod = (EMassLOD.High if d <= self.HIGH_RANGE else
                   EMassLOD.Medium if d <= self.MEDIUM_RANGE else
                   EMassLOD.Low if d <= self.LOW_RANGE else EMassLOD.Off)
            game.mass_lod[h] = lod


class UMassActorSpawnerSubsystem(UWorldSubsystem):
    """~ UMassActorSpawnerSubsystem: promotes a Mass entity to a full
    ADotCharacter when its LOD rises to High, and despawns it back to a
    fragment-only representation when LOD falls — writing the actor's final
    state back so cross-generation memory (Design Law 4) survives the churn."""
    def Initialize(self, world: "UWorld") -> None:
        self.actorized: dict[FMassEntityHandle, ADotCharacter] = {}

    def Tick(self, dt: float) -> None: pass

    def SyncActorization(self, game: "ChimeraGame") -> None:
        em = game.mass_subsystem.EntityManager
        for h, lod in list(game.mass_lod.items()):
            frag = em.GetFragmentDataPtr(h, FMassDotStateFragment)
            tf = em.GetFragmentDataPtr(h, FTransformFragment)
            if frag is None or tf is None:
                continue
            already = h in self.actorized
            if lod == EMassLOD.High and not already and frag.FSM != "gone":
                tree = {"stranger": "BT_Stranger", "trader": "BT_Trader",
                       "pirate": "BT_Pirate", "quiet": "BT_Quiet"}[frag.Archetype]
                actor = ADotCharacter(game.world, h, frag.Archetype, tree,
                                      tf.Transform.Location, frag.Need, frag.CanPay)
                actor.Memory = game.dot_memory_ledger.setdefault(frag.StableId, {})
                self.actorized[h] = actor
            elif lod != EMassLOD.High and already:
                actor = self.actorized.pop(h)
                tf.Transform.Location = actor.GetActorLocation()      # write back
                frag.FSM = actor.BlackboardComponent.GetValueAsObject("FSM") or frag.FSM
                frag.Need = actor.BlackboardComponent.GetValueAsObject("Need")
                game.dot_memory_ledger[frag.StableId] = actor.Memory
                if frag.FSM == "gone":
                    em.DestroyEntity(h)
                    del game.mass_lod[h]


class UMassMovementProcessor(UMassProcessor):
    """~ cheap ambient movement for LOD Low/Medium/Off entities (no BT tick,
    no NavMesh query — a straight-line drift toward a wander target, exactly
    the 'literal dot on the horizon' the design calls for)."""
    def ConfigureQueries(self) -> FMassEntityQuery:
        return FMassEntityQuery(FTransformFragment, FMassVelocityFragment, FMassDotStateFragment)

    def Execute(self, em: FMassEntityManager, game: "ChimeraGame", dt: float) -> None:
        ppos = game.player_actor.GetActorLocation()
        for h, tf, vel, state in em.EntityQuery(self._query):
            if game.mass_lod.get(h) == EMassLOD.High:
                continue                              # actorized; UAISystem owns it now
            if state.FSM == "gone":
                continue
            target = ppos if state.Need is not None else tf.Transform.Location + FVector(10, 0, 0)
            to_t = (target - tf.Transform.Location).GetSafeNormal()
            vel.Value = to_t * 1.2
            tf.Transform.Location = tf.Transform.Location + vel.Value * dt
            d = tf.Transform.Location.Dist2D(ppos)
            state.FSM = "distant" if d > 220.0 else "approaching" if d > 25.0 else "near"


# =============================================================================
# §7. ANIMATION, MOVEMENT & INPUT
# ~ UCharacterMovementComponent, Enhanced Input (UInputMappingContext/
# UInputAction/UInputModifier/UInputTrigger), UAnimInstance + UBlendSpace,
# UControlRig, UMotionWarpingComponent.
# =============================================================================

GRAVITY_YARD = 1.62
GRAVITY_TITAN_ZONE = 1.35

MOVE = dict(
    walk_speed=1.4, jog_speed=3.2, sprint_speed=5.6, bend_speed=0.7,
    accel=6.0, air_control=0.35, jump_height=1.1,
    coyote_time_s=0.12, jump_buffer_s=0.15,
    step_interval_walk_s=0.62, step_interval_sprint_s=0.38,
    slide_slope_deg=38.0,
)


# --- Enhanced Input -----------------------------------------------------------

class EInputActionValueType(Enum):
    Boolean = auto(); Axis1D = auto(); Axis2D = auto()


@dataclass
class UInputAction:
    """~ UInputAction asset: a named, typed action (Move/Look/Jump/Dig/...).
    Bound to gameplay via BindAction() in real UE; here read directly by
    UChimeraInputComponent each frame."""
    name: str
    value_type: EInputActionValueType


class UInputModifier(ABC):
    """~ UInputModifier base: transforms a raw axis value before triggers
    see it (DeadZone, ResponseCurveExponential, Negate, Swizzle...)."""
    @abstractmethod
    def Modify(self, raw: FVector) -> FVector: ...


@dataclass
class UInputModifierDeadZone(UInputModifier):
    """~ UInputModifier_DeadZone."""
    lower_threshold: float = 0.15
    def Modify(self, raw: FVector) -> FVector:
        m = raw.Size2D()
        return raw * 0.0 if m < self.lower_threshold else raw


@dataclass
class UInputModifierResponseCurveExponential(UInputModifier):
    """~ UInputModifier_ResponseCurveExponential."""
    exponent: float = 1.6
    def Modify(self, raw: FVector) -> FVector:
        m = raw.Size2D()
        if m < EPS:
            return FVector()
        shaped = clamp(m, 0.0, 1.0) ** self.exponent
        return raw.GetSafeNormal() * shaped


class UInputTrigger(ABC):
    """~ UInputTrigger base (Pressed/Released/Hold/Tap/Down)."""
    @abstractmethod
    def Test(self, held: bool, held_duration: float) -> bool: ...


class UInputTriggerPressed(UInputTrigger):
    def Test(self, held: bool, held_duration: float) -> bool: return held and held_duration <= 0.0


class UInputTriggerHold(UInputTrigger):
    def __init__(self, hold_s: float): self.hold_s = hold_s
    def Test(self, held: bool, held_duration: float) -> bool: return held and held_duration >= self.hold_s


@dataclass
class FEnhancedActionKeyMapping:
    """~ FEnhancedActionKeyMapping: Key -> Action, with its Modifiers/Triggers."""
    key: str
    action: UInputAction
    modifiers: list = field(default_factory=list)
    triggers: list = field(default_factory=list)


class UInputMappingContext:
    """~ UInputMappingContext asset: the suit-control layout. Fully
    remappable (ACCESSIBILITY law: every verb, no exceptions) — DeadZone/
    ResponseCurve modifiers scale by accessibility.input_forgiveness_scale."""
    def __init__(self, forgiveness_scale: float = 1.0):
        move = UInputAction("IA_Move", EInputActionValueType.Axis2D)
        look = UInputAction("IA_Look", EInputActionValueType.Axis2D)
        self.actions = dict(
            Move=move, Look=look,
            Jump=UInputAction("IA_Jump", EInputActionValueType.Boolean),
            Bend=UInputAction("IA_Bend", EInputActionValueType.Boolean),
            Sprint=UInputAction("IA_Sprint", EInputActionValueType.Boolean),
            PickUp=UInputAction("IA_PickUp", EInputActionValueType.Boolean),
            Dig=UInputAction("IA_Dig", EInputActionValueType.Boolean),
            Scan=UInputAction("IA_Scan", EInputActionValueType.Boolean),
            DrawWeapon=UInputAction("IA_DrawWeapon", EInputActionValueType.Boolean),
            Fire=UInputAction("IA_Fire", EInputActionValueType.Boolean),
            GestureWheel=UInputAction("IA_GestureWheel", EInputActionValueType.Boolean),
            AttuneDial=UInputAction("IA_AttuneDial", EInputActionValueType.Axis1D),
        )
        self.mappings = [
            FEnhancedActionKeyMapping("stick_l", move,
                [UInputModifierDeadZone(0.15 * forgiveness_scale),
                 UInputModifierResponseCurveExponential(1.6)]),
            FEnhancedActionKeyMapping("stick_r", look),
            FEnhancedActionKeyMapping("space", self.actions["Jump"], [], [UInputTriggerPressed()]),
            FEnhancedActionKeyMapping("ctrl", self.actions["Bend"]),
            FEnhancedActionKeyMapping("shift", self.actions["Sprint"]),
            FEnhancedActionKeyMapping("e", self.actions["PickUp"], [], [UInputTriggerPressed()]),
            FEnhancedActionKeyMapping("lmb", self.actions["Dig"], [], [UInputTriggerPressed()]),
            FEnhancedActionKeyMapping("q", self.actions["Scan"], [], [UInputTriggerPressed()]),
            FEnhancedActionKeyMapping("rmb", self.actions["DrawWeapon"]),
            FEnhancedActionKeyMapping("f", self.actions["Fire"], [], [UInputTriggerPressed()]),
            FEnhancedActionKeyMapping("tab", self.actions["GestureWheel"], [], [UInputTriggerHold(0.15)]),
            FEnhancedActionKeyMapping("wheel", self.actions["AttuneDial"]),
        ]
        self.forgiveness = forgiveness_scale       # multiplies coyote/jump-buffer windows too


class UEnhancedInputLocalPlayerSubsystem:
    """~ UEnhancedInputLocalPlayerSubsystem: AddMappingContext()/
    RemoveMappingContext() with priority; owns the resolved per-frame
    action-value table the movement component and verb system read."""
    def __init__(self):
        self.active_contexts: list[tuple[UInputMappingContext, int]] = []
        self.values: dict[str, Any] = {}
        self._held_since: dict[str, float] = {}

    def AddMappingContext(self, ctx: UInputMappingContext, priority: int = 0) -> None:
        self.active_contexts.append((ctx, priority))
        self.active_contexts.sort(key=lambda t: -t[1])

    def InjectRawDeviceState(self, raw: dict, now: float) -> None:
        """Device layer -> Modifier chain -> Trigger evaluation -> resolved
        action values, exactly the real Enhanced Input evaluation order.
        Branches on the ACTION's declared value type (not the raw sample's
        Python type) — an absent key means "neutral axis" or "not held",
        never "keep whatever it was last frame"."""
        for ctx, _prio in self.active_contexts:
            for m in ctx.mappings:
                if m.action.value_type in (EInputActionValueType.Axis1D, EInputActionValueType.Axis2D):
                    v = raw.get(m.key, FVector())
                    for mod in m.modifiers:
                        v = mod.Modify(v)
                    self.values[m.action.name] = v
                else:
                    held = bool(raw.get(m.key, False))
                    key = m.key
                    if held and key not in self._held_since:
                        self._held_since[key] = now
                    elif not held:
                        self._held_since.pop(key, None)
                    duration = now - self._held_since[key] if held else -1.0
                    fired = any(t.Test(held, duration) for t in m.triggers) if m.triggers else held
                    if fired:
                        self.values[m.action.name] = True
                    elif not m.triggers:              # held-style (no explicit trigger): absence == released
                        self.values.pop(m.action.name, None)

    def GetActionValue(self, action_name: str) -> Any:
        return self.values.pop(action_name, None)   # booleans consumed once (Pressed semantics)

    def PeekAxis(self, action_name: str) -> FVector:
        v = self.values.get(action_name, FVector())
        return v if isinstance(v, FVector) else FVector()


# --- UCharacterMovementComponent ---------------------------------------------

@dataclass
class FCharacterNetworkMoveData:
    """~ FCharacterNetworkMoveData: one packed client move — the unit sent
    via ServerMovePacked_ClientSend and replayed client-side for
    reconciliation (§9)."""
    TimeStamp: float = 0.0
    Acceleration: FVector = field(default_factory=FVector)     # here: raw move axis
    ControlYaw: float = 0.0
    ControlPitch: float = 0.0
    bPressedJump: bool = False
    bWantsToCrouch: bool = False       # "Bend" reuses UE5's crouch semantics
    bWantsToSprint: bool = False
    DeltaTime: float = 1.0 / 60.0


class EMovementMode(Enum):
    """~ REAL enum (MOVE_None/MOVE_Walking/MOVE_Falling/MOVE_Flying/...)."""
    MOVE_None = auto(); MOVE_Walking = auto(); MOVE_Falling = auto()


@dataclass
class FMovementState:
    """The deterministic, copyable movement state — what CMC calls
    'UpdatedComponent' position plus Velocity plus MovementMode. Must stay
    plain-data for §9's rewind-and-replay reconciliation."""
    Location: FVector = field(default_factory=FVector)
    Velocity: FVector = field(default_factory=FVector)
    MovementMode: EMovementMode = EMovementMode.MOVE_Walking
    Gait: Gait = Gait.IDLE
    StepClock: float = 0.0
    bLeftFootNext: bool = True
    LeftGroundAt: float = -999.0
    JumpPressedAt: float = -999.0
    Now: float = 0.0

    def Copy(self) -> "FMovementState":
        return FMovementState(FVector(*self.Location.ToTuple()), FVector(*self.Velocity.ToTuple()),
                              self.MovementMode, self.Gait, self.StepClock, self.bLeftFootNext,
                              self.LeftGroundAt, self.JumpPressedAt, self.Now)


class APhysicsVolume(AActor):
    """~ APhysicsVolume: overrides gravity for actors inside its bounds.
    The Titan Run's alternating corridors are physics volumes stacked along
    a spline — real, not a bespoke 'gravity field' invention."""
    def __init__(self, world: "UWorld", contains: Callable[[FVector], bool], gravity_z: float):
        super().__init__(world)
        self.Contains = contains
        self.GravityZ = gravity_z


class UGravityVolumeSubsystem(UWorldSubsystem):
    """Resolves the active APhysicsVolume for a location each tick (real UE
    resolves this via overlap events on volume Begin/EndOverlap; polled here
    for pseudocode simplicity), LERPed over 1.2s so gravity changes are
    body-readable, never a snap."""
    def Initialize(self, world: "UWorld") -> None:
        self.volumes: list[APhysicsVolume] = []
        self._current = GRAVITY_YARD

    def Tick(self, dt: float) -> None: pass

    def RegisterVolume(self, v: APhysicsVolume) -> None:
        self.volumes.append(v)

    def GravityAt(self, p: FVector, dt: float) -> float:
        target = GRAVITY_YARD
        for v in self.volumes:
            if v.Contains(p):
                target = v.GravityZ
                break
        self._current = lerp(self._current, target, clamp(dt / 1.2, 0, 1))
        return self._current


def line_trace_single(ground: "AGroundActor", start: FVector, direction: FVector,
                      max_dist: float, step: float = 0.5) -> Optional[FVector]:
    """~ UWorld::LineTraceSingleByChannel (ECC_WorldStatic), ray-marched vs
    the heightfield stand-in for a proper physics scene query."""
    d = direction.GetSafeNormal()
    t = 0.0
    while t <= max_dist:
        p = start + d * t
        if p.Z <= ground.HeightAt(p):
            return p
        t += step
    return None


class UChimeraMovementComponent:
    """~ UChimeraMovementComponent : public UCharacterMovementComponent.
    PerformMovement() below is the SAME pure function run authoritatively by
    the server and speculatively by the client (§9's FSavedMove_Character
    replay) — determinism here is what makes reconciliation converge.
    Exposes the real CMC-style tunables as fields (MaxWalkSpeed etc.) so a
    porting engineer maps 1:1 onto UPROPERTY(EditAnywhere, Category=
    "Character Movement: Walking") members."""
    def __init__(self):
        self.MaxWalkSpeed = MOVE["walk_speed"]
        self.MaxWalkSpeedCrouched = MOVE["bend_speed"]
        self.JumpZVelocity = math.sqrt(2.0 * GRAVITY_YARD * MOVE["jump_height"])
        self.GravityScale = 1.0                    # multiplies the volume's GravityZ
        self.GroundFriction = 8.0
        self.AirControl = MOVE["air_control"]
        self.bOrientRotationToMovement = False       # first-person: camera yaw drives facing

    def PerformMovement(self, state: FMovementState, move: FCharacterNetworkMoveData,
                        ground: "AGroundActor", gravity_z: float, speed_scale: float,
                        footsteps_out: Optional[list] = None) -> FMovementState:
        s = state.Copy()
        s.Now += move.DeltaTime
        mag = move.Acceleration.Size2D()
        if move.bWantsToCrouch:
            s.Gait = Gait.BEND
        elif mag < 0.05:
            s.Gait = Gait.IDLE
        elif move.bWantsToSprint and mag > 0.5:
            s.Gait = Gait.SPRINT
        elif mag > 0.55:
            s.Gait = Gait.JOG
        else:
            s.Gait = Gait.WALK
        base = {Gait.IDLE: 0.0, Gait.WALK: self.MaxWalkSpeed, Gait.JOG: MOVE["jog_speed"],
                Gait.SPRINT: MOVE["sprint_speed"], Gait.BEND: self.MaxWalkSpeedCrouched}[s.Gait]
        surface = ground.SurfaceAt(s.Location)
        basin_pen = 0.55 if surface == "BASIN" else 1.0
        max_speed = base * basin_pen * speed_scale
        cy, sy = math.cos(move.ControlYaw), math.sin(move.ControlYaw)
        want = FVector(move.Acceleration.X * cy - move.Acceleration.Y * sy,
                       move.Acceleration.X * sy + move.Acceleration.Y * cy, 0.0) * max_speed
        grounded = s.MovementMode == EMovementMode.MOVE_Walking
        control = 1.0 if grounded else self.AirControl
        blend = clamp(MOVE["accel"] * ground.TractionAt(s.Location) * control * move.DeltaTime, 0, 1)
        s.Velocity.X = lerp(s.Velocity.X, want.X, blend)
        s.Velocity.Y = lerp(s.Velocity.Y, want.Y, blend)
        if move.bPressedJump:
            s.JumpPressedAt = s.Now
        buffered = (s.Now - s.JumpPressedAt) <= MOVE["jump_buffer_s"]
        coyote = (s.Now - s.LeftGroundAt) <= MOVE["coyote_time_s"]
        if buffered and (grounded or coyote):
            s.Velocity.Z = self.JumpZVelocity
            s.MovementMode = EMovementMode.MOVE_Falling
            s.JumpPressedAt = -999.0
            s.LeftGroundAt = -999.0
            grounded = False
        if not grounded:
            s.Velocity.Z -= gravity_z * self.GravityScale * move.DeltaTime
        s.Location = s.Location + s.Velocity * move.DeltaTime
        floor = ground.HeightAt(s.Location)
        if s.Location.Z <= floor:
            if not grounded and s.Velocity.Z < -1.0 and footsteps_out is not None:
                footsteps_out.append(("land", s.Location, surface, s.bLeftFootNext, s.Velocity.Size2D(), s.Now))
            s.Location.Z, s.Velocity.Z, s.MovementMode = floor, 0.0, EMovementMode.MOVE_Walking
        elif grounded and s.Location.Z > floor + 0.05:
            s.MovementMode = EMovementMode.MOVE_Falling
            s.LeftGroundAt = s.Now
        speed2d = s.Velocity.Size2D()
        if s.MovementMode == EMovementMode.MOVE_Walking and speed2d > 0.2:
            interval = lerp(MOVE["step_interval_walk_s"], MOVE["step_interval_sprint_s"],
                            speed2d / MOVE["sprint_speed"])
            s.StepClock += move.DeltaTime
            if s.StepClock >= interval:
                s.StepClock = 0.0
                if footsteps_out is not None:
                    footsteps_out.append(("step", s.Location, surface, s.bLeftFootNext, speed2d, s.Now))
                s.bLeftFootNext = not s.bLeftFootNext
        else:
            s.StepClock = 0.0
        return s


# --- Animation: UAnimInstance state machine + UBlendSpace -------------------

@dataclass
class UBlendSpace:
    """~ UBlendSpace (1-axis: Speed). Real assets store a 2D grid of sampled
    poses; this returns blend WEIGHTS across the named poses for a given
    speed, exactly what the AnimGraph's BlendSpacePlayer node consumes."""
    axis_samples: tuple = (0.0, MOVE["walk_speed"], MOVE["jog_speed"], MOVE["sprint_speed"])
    pose_names: tuple = ("Idle", "Walk", "Jog", "Sprint")

    def GetBlendWeights(self, speed: float) -> dict:
        weights = {n: 0.0 for n in self.pose_names}
        for i in range(len(self.axis_samples) - 1):
            lo, hi = self.axis_samples[i], self.axis_samples[i + 1]
            if lo <= speed <= hi or i == len(self.axis_samples) - 2:
                t = inv_lerp(lo, hi, speed)
                weights[self.pose_names[i]] = 1.0 - t
                weights[self.pose_names[i + 1]] = t
                break
        return weights


class UControlRig:
    """~ UControlRig: procedural post-process on top of the animation pose.
    Foot IK adapts each foot's Z + tilt to actual ground height/slope under
    it — critical on regolith dunes where the animated pose alone would
    clip through terrain or float above it."""
    def __init__(self, ground: "AGroundActor"):
        self.ground = ground

    def SolveFootIK(self, pelvis: FVector, foot_offset_x: float) -> tuple[float, float]:
        foot_pos = pelvis + FVector(foot_offset_x, 0, 0)
        hit = line_trace_single(self.ground, foot_pos + FVector(0, 0, 1.0), FVector(0, 0, -1), 2.0)
        if hit is None:
            return pelvis.Z, 0.0
        h_here = self.ground.HeightAt(foot_pos)
        h_ahead = self.ground.HeightAt(foot_pos + FVector(0.15, 0, 0))
        tilt_deg = math.degrees(math.atan2(h_ahead - h_here, 0.15))
        return hit.Z, tilt_deg


@dataclass
class FMotionWarpingTarget:
    """~ FMotionWarpingTarget: {Name, Location, Rotation} a root-motion
    montage warps toward — used so the Dig animation's hand-to-ground
    contact lands exactly on the actual impact point on uneven regolith,
    not wherever the source animation's root motion happens to place it."""
    Name: str
    Location: FVector
    Rotation: FQuat = field(default_factory=FQuat)


class UMotionWarpingComponent(UActorComponent):
    """~ UMotionWarpingComponent: montages query AddOrUpdateWarpTarget() and
    the anim system stretches root motion to reach it."""
    def __init__(self, owner: AActor):
        super().__init__(owner)
        self.targets: dict[str, FMotionWarpingTarget] = {}

    def AddOrUpdateWarpTarget(self, t: FMotionWarpingTarget) -> None:
        self.targets[t.Name] = t

    def RemoveWarpTarget(self, name: str) -> None:
        self.targets.pop(name, None)


class UChimeraAnimInstance:
    """~ UAnimInstance subclass: NativeUpdateAnimation() reads movement
    state each frame and drives the BlendSpace + discrete states (Bend/Dig/
    Gesture aren't speed-blended — they're one-shot montages/additive
    states layered on top)."""
    def __init__(self, ground: "AGroundActor"):
        self.blend_space = UBlendSpace()
        self.control_rig = UControlRig(ground)
        self.state = "BS_Locomotion"        # BS_Locomotion|Bend|Dig|Gesture_*
        self.pose_weights: dict = {}
        self.foot_l_z = 0.0
        self.foot_r_z = 0.0

    def NativeUpdateAnimation(self, dt: float, movement: FMovementState, pelvis: FVector) -> None:
        if movement.Gait == Gait.BEND:
            self.state = "Bend"
        elif self.state not in ("Dig",) and not self.state.startswith("Gesture_"):
            self.state = "BS_Locomotion"
        self.pose_weights = self.blend_space.GetBlendWeights(movement.Velocity.Size2D())
        self.foot_l_z, _tilt_l = self.control_rig.SolveFootIK(pelvis, -0.15)
        self.foot_r_z, _tilt_r = self.control_rig.SolveFootIK(pelvis, 0.15)


# =============================================================================
# §8. GAMEPLAY FRAMEWORK & DATA — GAS, DataTable, SaveGame
# ~ Engine/Plugins/GameFeatures/GameplayAbilities, Engine/Source/Runtime/Engine
# =============================================================================

# --- Gameplay Tags -----------------------------------------------------------

class FGameplayTagContainer:
    """~ FGameplayTagContainer: hierarchical dot-path tags ("State.Threatened"
    matches a MatchesTag("State") query). Real UE resolves this against a
    project-wide FGameplayTagsManager tree; a set + prefix check is the
    observably-equivalent pseudocode."""
    def __init__(self):
        self._tags: set[str] = set()

    def AddTag(self, tag: str) -> None: self._tags.add(tag)
    def RemoveTag(self, tag: str) -> None: self._tags.discard(tag)
    def HasTag(self, tag: str) -> bool: return tag in self._tags
    def HasTagExact(self, tag: str) -> bool: return tag in self._tags

    def MatchesTag(self, query: str) -> bool:
        return any(t == query or t.startswith(query + ".") for t in self._tags)

    def GetGameplayTagArray(self) -> list:
        return sorted(self._tags)


# --- Attribute Set ------------------------------------------------------------

@dataclass
class FGameplayAttributeData:
    """~ FGameplayAttributeData: {BaseValue, CurrentValue} pair every GAS
    attribute carries (BaseValue survives Instant effects' permanent
    changes; CurrentValue reflects active Duration/Infinite modifiers)."""
    BaseValue: float = 0.0
    CurrentValue: float = 0.0


@UCLASS()
class USuitAttributeSet:
    """~ USuitAttributeSet : public UAttributeSet. GENERATED_BODY()
    ATTRIBUTE_ACCESSORS-equivalent: each field below is a
    FGameplayAttributeData the ASC's GameplayEffects modify; PostGameplay
    EffectExecute clamps into range and raises DeathEvent at 0 O2."""
    def __init__(self):
        self.O2 = FGameplayAttributeData(100.0, 100.0)
        self.MaxO2 = FGameplayAttributeData(100.0, 100.0)
        self.Battery = FGameplayAttributeData(100.0, 100.0)
        self.DustClog = FGameplayAttributeData(0.0, 0.0)
        self.Integrity = FGameplayAttributeData(100.0, 100.0)
        self.Temperature = FGameplayAttributeData(20.0, 20.0)

    def PreAttributeChange(self, attr_name: str, new_value: float) -> float:
        """~ UAttributeSet::PreAttributeChange: clamp before it lands."""
        if attr_name in ("O2", "Battery", "DustClog", "Integrity"):
            return clamp(new_value, 0.0, 100.0 if attr_name != "DustClog" else 100.0)
        return new_value


# --- Gameplay Effects ---------------------------------------------------------

class EGameplayEffectDurationType(Enum):
    Instant = auto(); HasDuration = auto(); Infinite = auto()


class EGameplayModOp(Enum):
    Add = auto(); Multiply = auto(); Override = auto()


@dataclass
class FGameplayModifierInfo:
    Attribute: str
    Operation: EGameplayModOp
    Magnitude: float


@dataclass
class UGameplayEffect:
    """~ UGameplayEffect asset: duration policy + periodic application +
    modifiers. O2/battery/dust-clog drains are literally UGameplayEffects,
    not ad-hoc per-frame subtraction — this is how real GAS-driven survival
    stats work (Period + Modifiers, applied via ApplyGameplayEffectToSelf)."""
    name: str
    duration_policy: EGameplayEffectDurationType
    period: float = 0.0                    # 0 = every tick if Infinite
    modifiers: list = field(default_factory=list)


# Magnitudes are PER-SECOND (period=1.0s) — O2=100 lasts ~100s/-1.0 rate,
# so e.g. walking drains a full suit in ~100 minutes at -1.0/60 per second.
# Tuned from the original per-minute design values (÷60) for smooth
# per-tick HUD needle motion rather than once-a-minute jumps.
GE_O2Drain_Idle = UGameplayEffect("GE_O2Drain_Idle", EGameplayEffectDurationType.Infinite,
                                  1.0, [FGameplayModifierInfo("O2", EGameplayModOp.Add, -0.6 / 60.0)])
GE_O2Drain_Walk = UGameplayEffect("GE_O2Drain_Walk", EGameplayEffectDurationType.Infinite,
                                  1.0, [FGameplayModifierInfo("O2", EGameplayModOp.Add, -1.0 / 60.0)])
GE_O2Drain_Sprint = UGameplayEffect("GE_O2Drain_Sprint", EGameplayEffectDurationType.Infinite,
                                    1.0, [FGameplayModifierInfo("O2", EGameplayModOp.Add, -3.0 / 60.0)])
GE_BatteryDrain_Night = UGameplayEffect("GE_BatteryDrain_Night", EGameplayEffectDurationType.Infinite,
                                        1.0, [FGameplayModifierInfo("Battery", EGameplayModOp.Add, -1.8 / 60.0)])
GE_DustClog_Storm = UGameplayEffect("GE_DustClog_Storm", EGameplayEffectDurationType.Infinite,
                                    1.0, [FGameplayModifierInfo("DustClog", EGameplayModOp.Add, 4.0 / 60.0)])
GE_O2Regen_Garden = UGameplayEffect("GE_O2Regen_Garden", EGameplayEffectDurationType.Infinite,
                                    1.0, [FGameplayModifierInfo("O2", EGameplayModOp.Add, 0.8 / 60.0)])
GE_BatteryRegen_Bank = UGameplayEffect("GE_BatteryRegen_Bank", EGameplayEffectDurationType.Infinite,
                                       1.0, [FGameplayModifierInfo("Battery", EGameplayModOp.Add, 2.0 / 60.0)])
GE_DustClog_Scrub = UGameplayEffect("GE_DustClog_Scrub", EGameplayEffectDurationType.Infinite,
                                    1.0, [FGameplayModifierInfo("DustClog", EGameplayModOp.Add, -1.0 / 60.0)])


@UCLASS()
class UAbilitySystemComponent(UActorComponent):
    """~ UAbilitySystemComponent: owns the AttributeSet + active effects +
    tag container; ApplyGameplayEffectToSelf drives periodic ticking."""
    def __init__(self, owner: AActor, attr_set: USuitAttributeSet):
        super().__init__(owner)
        self.AttributeSet = attr_set
        self._active: list[tuple[UGameplayEffect, float]] = []   # (effect, time_since_period)
        self.Abilities: dict[str, "UGameplayAbility"] = {}

    def ApplyGameplayEffectToSelf(self, ge: UGameplayEffect) -> None:
        if ge.duration_policy == EGameplayEffectDurationType.Instant:
            self._apply_modifiers(ge)
        elif not any(active_ge is ge for active_ge, _t in self._active):
            self._active.append((ge, 0.0))

    def RemoveActiveGameplayEffect(self, ge: UGameplayEffect) -> None:
        self._active = [(g, t) for g, t in self._active if g is not ge]

    def HasActiveEffect(self, ge: UGameplayEffect) -> bool:
        return any(g is ge for g, _t in self._active)

    def _apply_modifiers(self, ge: UGameplayEffect) -> None:
        for mod in ge.modifiers:
            attr: FGameplayAttributeData = getattr(self.AttributeSet, mod.Attribute)
            if mod.Operation == EGameplayModOp.Add:
                attr.CurrentValue = self.AttributeSet.PreAttributeChange(
                    mod.Attribute, attr.CurrentValue + mod.Magnitude)
            elif mod.Operation == EGameplayModOp.Multiply:
                attr.CurrentValue *= mod.Magnitude
            else:
                attr.CurrentValue = mod.Magnitude
            attr.BaseValue = attr.CurrentValue

    def TickPeriodicEffects(self, dt: float) -> None:
        for i, (ge, t) in enumerate(self._active):
            t += dt
            if ge.period > 0.0 and t >= ge.period:
                t -= ge.period
                self._apply_modifiers(ge)
            self._active[i] = (ge, t)

    def GrantAbility(self, name: str, ability: "UGameplayAbility") -> None:
        self.Abilities[name] = ability

    def TryActivateAbilityByName(self, name: str, game: "ChimeraGame") -> bool:
        ability = self.Abilities.get(name)
        if ability is None or not ability.CanActivateAbility(self.OwnerActor, game):
            return False
        ability.ActivateAbility(self.OwnerActor, self, game)
        return True


# --- Gameplay Abilities --------------------------------------------------------

class UGameplayAbility(ABC):
    """~ UGameplayAbility base: CanActivateAbility (cost/cooldown/tag gate)
    -> ActivateAbility (the effect) -> CommitAbility (consumes cost).
    Dig/Scan/Fire/Attune/PickupDrop are each one of these, not a bare verb
    switch statement — cooldowns and cost are first-class here."""
    cooldown_s: float = 0.0
    def __init__(self): self._last_activated = -999.0

    def CanActivateAbility(self, actor: AActor, game: "ChimeraGame") -> bool:
        return (game.now_s - self._last_activated) >= self.cooldown_s

    @abstractmethod
    def ActivateAbility(self, actor: AActor, asc: UAbilitySystemComponent, game: "ChimeraGame") -> None: ...

    def CommitAbility(self, game: "ChimeraGame") -> None:
        self._last_activated = game.now_s


class GA_Dig(UGameplayAbility):
    """~ project GA_Dig. H-21's fix made real: behavior, not metadata."""
    cooldown_s = 0.35

    def ActivateAbility(self, actor, asc, game: "ChimeraGame") -> None:
        tr = actor.RootComponent.GetComponentTransform()
        at = tr.Location + tr.Rotation.GetForwardVector() * 1.2
        surface = game.ground_actor.SurfaceAt(at)
        if surface in ("METAL", "INTERIOR") or game.shovel_durability <= 0:
            return                                    # sparks; the world says no
        self.CommitAbility(game)
        game.shovel_durability -= DIG["durability_per_scoop"]
        cells = int(DIG["radius"] / DIG["cell"]) + 1
        k0 = (math.floor(at.X / DIG["cell"]), math.floor(at.Y / DIG["cell"]))
        for dx in range(-cells, cells + 1):
            for dy in range(-cells, cells + 1):
                k = (k0[0] + dx, k0[1] + dy)
                game.dig_delta[k] = game.dig_delta.get(k, 0.0) - DIG["scoop_depth"]
                depth_here = -game.dig_delta[k]
                for rec in list(game.buried.get(k, [])):
                    if rec["depth"] <= depth_here:
                        game.buried[k].remove(rec)
                        game.spawn_world_item(rec["kind"], FVector(k[0] * DIG["cell"],
                            k[1] * DIG["cell"], game.ground_actor.HeightAt(at)), rec.get("quality", 1.0))
        game.niagara.SpawnSystemAtLocation("NS_DigBurst", at, 1.0)
        game.event_bus.OnFootstep.Broadcast(FFootstepEvent(
            actor, at, tr.Rotation.GetForwardVector().X, surface, True, MOVE["jog_speed"],
            game.now_s, bLanding=True))
        motion_warp = actor.FindComponentByClass(UMotionWarpingComponent)
        motion_warp.AddOrUpdateWarpTarget(FMotionWarpingTarget("DigContact", at))


class GA_Scan(UGameplayAbility):
    cooldown_s = 1.0
    def ActivateAbility(self, actor, asc, game: "ChimeraGame") -> None:
        self.CommitAbility(game)
        asc.ApplyGameplayEffectToSelf(UGameplayEffect(
            "GE_ScanCost", EGameplayEffectDurationType.Instant, 0.0,
            [FGameplayModifierInfo("Battery", EGameplayModOp.Add, -SUIT["battery_drain_scanner"])]))
        loc = actor.GetActorLocation()
        game.universe_actor.ObserveRegion(loc, 40.0)
        game.scan_pips = [k for k, items in game.buried.items() if items and
                          FVector(k[0] * DIG["cell"], k[1] * DIG["cell"], 0).Dist2D(loc) < 40.0]


class GA_Fire(UGameplayAbility):
    cooldown_s = 0.25
    def ActivateAbility(self, actor, asc, game: "ChimeraGame") -> None:
        if game.weapon_ammo <= 0:
            game.hud.glyph_strip.Push("click")        # dry-fire: diegetic shame
            return
        self.CommitAbility(game)
        game.weapon_ammo -= 1
        actor.Tags.AddTag("State.WeaponFiredThisLife")
        if actor.GetActorLocation().Dist2D(game.erisaid_actor.GetActorLocation()) < 120.0:
            game.attunement.OnGunfireNearby(game.sun_actor.day)
        tr = actor.RootComponent.GetComponentTransform()
        fwd = tr.Rotation.GetForwardVector()
        for dot in game.mass_actor_spawner.actorized.values():   # only actorized (LOD High) dots are hittable
            to = dot.GetActorLocation() - tr.Location
            if to.Size2D() < 60.0 and fwd.Dot(to.GetSafeNormal()) > 0.99:
                dot.Health -= 34.0
                dot.BlackboardComponent.SetValueAsBool("Flee", True)
                game.factions.RepDelta("drifters", -25.0)
                break
        for dot in game.mass_actor_spawner.actorized.values():
            dot.Memory["saw_player_shoot"] = True       # everyone remembers


class GA_PickupDrop(UGameplayAbility):
    cooldown_s = 0.2
    def ActivateAbility(self, actor, asc, game: "ChimeraGame") -> None:
        self.CommitAbility(game)
        tr = actor.RootComponent.GetComponentTransform()
        carry = actor.FindComponentByClass(UCarryComponent)
        nearest, nd = None, 2.2
        for item_actor in game.world_items:
            d = tr.Location.Dist2D(item_actor.GetActorLocation())
            if d < nd:
                nearest, nd = item_actor, d
        if nearest is not None:
            obj = FItem(nearest.Kind, nearest.Quality, nearest.OriginGeneration)
            mass = sum(ITEM_TABLE[i.Kind].mass_kg for i in carry.Pack)
            if carry.Hands is None:
                carry.Hands = obj
            elif mass + ITEM_TABLE[obj.Kind].mass_kg <= carry.PackKgMax:
                carry.Pack.append(obj)
            else:
                return
            game.world_items.remove(nearest)
        elif carry.Hands is not None:
            game.spawn_world_item(carry.Hands.Kind, tr.Location + tr.Rotation.GetForwardVector() * 0.8,
                                  carry.Hands.Quality)
            carry.Hands = None


class GA_Attune(UGameplayAbility):
    """Attunement is driven every tick by UChimeraAttunementComponent (§5);
    this ability just applies the dial-turn input to it."""
    cooldown_s = 0.0
    def ActivateAbility(self, actor, asc, game: "ChimeraGame") -> None:
        self.CommitAbility(game)


# --- DataTable-driven economy/factions/items -----------------------------------

@USTRUCT()
@dataclass
class FItemTableRow:
    """~ FTableRowBase subclass held in a UDataTable (DT_Items)."""
    mass_kg: float
    base_price: float
    sellable: bool


ITEM_TABLE: dict[str, FItemTableRow] = {
    "ORE_ILMENITE":     FItemTableRow(4.0, 12.0, True),
    "ICE_WATER":        FItemTableRow(3.0, 18.0, True),
    "OXYGEN_CAN":       FItemTableRow(2.0, 25.0, True),
    "MACHINE_PARTS":    FItemTableRow(5.0, 40.0, True),
    "REGOLITH_GLASS":   FItemTableRow(1.5, 30.0, True),
    "SEEDS":            FItemTableRow(0.2, 55.0, True),
    "FUEL_CELL":        FItemTableRow(6.0, 48.0, True),
    "RELIC_SHARD":      FItemTableRow(0.8, 120.0, True),
    "ERISAID_FRAGMENT": FItemTableRow(0.3, 0.0, False),   # unsellable. period.
    "HEIRLOOM":         FItemTableRow(0.5, 0.0, False),   # unsellable. period.
    "STORY":            FItemTableRow(0.0, 8.0, True),
}

NEED_FULFILLMENT: dict[str, Optional[str]] = {
    "o2": "OXYGEN_CAN", "water": "ICE_WATER", "parts": "MACHINE_PARTS",
    "warmth": "FUEL_CELL", "ride": None, "burial": None,
}

SACRIFICE_WEIGHTS = {
    "REFUSED_PROFIT": 1.0, "GAVE_CARGO": 1.5, "GAVE_O2": 3.0,
    "SPENT_TIME_UNPAYABLE": 2.0, "TOOK_RISK_FOR_OTHER": 2.5,
    "BURIED_STRANGER": 3.5, "WEAPON_NEVER_FIRED": 2.0, "HEIRLOOM_GIVEN": 5.0,
}

DIG = dict(radius=0.6, scoop_depth=0.15, durability_per_scoop=1.0, cell=0.5)

SUIT = dict(o2_max=100.0, battery_max=100.0, battery_drain_scanner=0.5,
           dust_clog_move_penalty=0.35, thermal_safe_lo=-20.0,
           night_temp_c=-140.0, day_temp_c=45.0)

STAR = dict(brightness_k=6.0, bright_lights_yard=0.75)

ACCESSIBILITY = dict(input_forgiveness_scale=1.0, audio_muted_visual_pulses=True)


@dataclass
class FItem:
    """~ a lightweight FInstancedStruct-style item record (not a UObject —
    items are DATA; only their world-dropped representation is an actor)."""
    Kind: str
    Quality: float = 1.0
    OriginGeneration: int = 0


@UCLASS()
class UCarryComponent(UActorComponent):
    """~ UCarryComponent: two hands + a 30kg pack. Mass slows honestly via
    the movement component's speed_scale input."""
    def __init__(self, owner: AActor):
        super().__init__(owner)
        self.Hands: Optional[FItem] = None
        self.Pack: list = []
        self.PackKgMax = 30.0


@dataclass
class FStationMarket:
    """~ economy DataTable-adjacent runtime state (DT_Items supplies base
    prices; per-station demand multipliers live here, elastic on trade)."""
    station_id: str
    pos: FVector
    stock: dict = field(default_factory=dict)
    demand: dict = field(default_factory=dict)
    ELASTICITY = 0.04

    def Price(self, kind: str) -> float:
        return ITEM_TABLE[kind].base_price * self.demand.get(kind, 1.0)

    def Drift(self, rng: random.Random) -> None:
        for k in list(self.demand):
            self.demand[k] = clamp(self.demand[k] + rng.uniform(-0.03, 0.03), 0.5, 2.0)


class UFactionSubsystem(UWorldSubsystem):
    """~ project subsystem backed by DT_Factions."""
    FACTIONS = ("yardfolk", "combine", "drifters", "the_quiet")
    def Initialize(self, world: "UWorld") -> None:
        self.rep = {f: 0.0 for f in self.FACTIONS}
    def Tick(self, dt: float) -> None: pass
    def RepDelta(self, faction: str, amount: float) -> None:
        if faction in self.rep:
            self.rep[faction] = clamp(self.rep[faction] + amount, -100.0, 100.0)


# --- SaveGame ------------------------------------------------------------------

SAVE_VERSION = 4


@UCLASS(Blueprintable=True)
class UChimeraSaveGame:
    """~ UChimeraSaveGame : public USaveGame. Every field below carries the
    REAL UPROPERTY(SaveGame) specifier (CPF_SaveGame) via our metadata shim;
    UGameplayStatics::SaveGameToSlot walks exactly these fields."""
    def __init__(self):
        self.Version = SAVE_VERSION
        self.Seed = 0
        self.Generation = 1
        self.Credits = 0.0
        self.Day = 0
        self.TimeHours = 0.0
        self.PlayerLocation = FVector()
        self.SuitAttributes: dict = {}
        self.DigDelta: dict = {}
        self.Buried: dict = {}
        self.Footprints: list = []
        self.Stars: list = []
        self.Sacrifices: list = []
        self.DotMemoryLedger: dict = {}
        self.Attunement: dict = {}
        self.TitanBest: dict = {}
        self.Flags: set = set()


class USaveGameSubsystem(UWorldSubsystem):
    """~ UGameplayStatics::SaveGameToSlot/LoadGameFromSlot, backed by a
    custom FArchive-style wrapper (magic/version/CRC header) — the studio's
    hardening on top of stock UE, kept because it's a real, defensible
    addition (corrupt-save detection, forward migration)."""
    MAGIC = 0x43484D52          # 'CHMR'
    AUTOSAVE_SLOTS = 3

    def Initialize(self, world: "UWorld") -> None:
        self.slots: dict[str, bytes] = {}
        self._auto_i = 0
        self.migrations = {3: self._migrate_v3_to_v4}

    def Tick(self, dt: float) -> None: pass

    def Capture(self, game: "ChimeraGame") -> UChimeraSaveGame:
        sg = UChimeraSaveGame()
        sg.Seed, sg.Generation, sg.Credits = game.seed, game.generation, game.credits
        sg.Day, sg.TimeHours = game.sun_actor.day, game.sun_actor.time_h
        sg.PlayerLocation = game.player_actor.GetActorLocation()
        attrs = game.player_actor.AbilitySystemComponent.AttributeSet
        sg.SuitAttributes = {n: getattr(attrs, n).CurrentValue
                             for n in ("O2", "Battery", "DustClog", "Integrity")}
        sg.DigDelta = {f"{k[0]},{k[1]}": v for k, v in game.dig_delta.items()}
        sg.Buried = {f"{k[0]},{k[1]}": v for k, v in game.buried.items()}
        sg.Footprints = [(fp[0].ToTuple(), fp[1], fp[2], fp[3], fp[4]) for fp in game.footprints]
        sg.Stars = [(s.life_name, s.generation, s.brightness, s.twinkle, s.bearing_deg)
                   for s in game.memorial.stars]
        sg.Sacrifices = list(game.player_actor.SacrificeLogComponent.entries)   # (kind, weight, note, gen, day)
        sg.DotMemoryLedger = dict(game.dot_memory_ledger)
        sg.Attunement = dict(matched=sorted(game.attunement.matched),
                             visits=sorted(game.attunement.visit_days),
                             deaf_until=game.attunement.deaf_until_day)
        sg.TitanBest = dict(game.titan_best)
        sg.Flags = set(game.player_actor.Tags.GetGameplayTagArray())
        return sg

    def ToBytes(self, sg: UChimeraSaveGame) -> bytes:
        import zlib
        payload_dict = {k: (list(v) if isinstance(v, set) else v) for k, v in vars(sg).items()}
        payload = json.dumps(payload_dict, default=str).encode("utf-8")
        crc = zlib.crc32(payload) & 0xFFFFFFFF
        return struct.pack("<III", self.MAGIC, sg.Version, crc) + payload

    def FromBytes(self, blob: bytes) -> dict:
        import zlib
        magic, version, crc = struct.unpack("<III", blob[:12])
        payload = blob[12:]
        assert magic == self.MAGIC, "corrupt save: bad magic"
        assert zlib.crc32(payload) & 0xFFFFFFFF == crc, "corrupt save: bad crc"
        data = json.loads(payload.decode("utf-8"))
        while data["Version"] < SAVE_VERSION:
            data = self.migrations[data["Version"]](data)
        return data

    @staticmethod
    def _migrate_v3_to_v4(data: dict) -> dict:
        data.setdefault("TitanBest", {})
        data["Version"] = 4
        return data

    def SaveGameToSlot(self, sg: UChimeraSaveGame, slot_name: str) -> None:
        self.slots[slot_name] = self.ToBytes(sg)

    def LoadGameFromSlot(self, slot_name: str) -> Optional[dict]:
        blob = self.slots.get(slot_name)
        return self.FromBytes(blob) if blob else None

    def Autosave(self, game: "ChimeraGame") -> str:
        slot = f"auto_{self._auto_i % self.AUTOSAVE_SLOTS}"
        self._auto_i += 1
        self.SaveGameToSlot(self.Capture(game), slot)
        return slot


# =============================================================================
# §9. NETWORKING — ENetRole, replication, RPCs, Replication Graph, movement prediction
# ~ Engine/Source/Runtime/Engine/Public/Net/, Engine/Plugins/Runtime/ReplicationGraph
# =============================================================================

@dataclass
class FLifetimeProperty:
    """~ FLifetimeProperty: one entry registered in GetLifetimeReplicatedProps."""
    property_name: str
    condition: str = "COND_None"      # ~ ELifetimeCondition (COND_OwnerOnly, ...)


class FSavedMove_ChimeraCharacter:
    """~ FSavedMove_Character subclass: one buffered client move, replayed
    during reconciliation. GetCompressedFlags()-equivalent isn't needed
    here since FCharacterNetworkMoveData already IS the compact wire form."""
    def __init__(self, move: FCharacterNetworkMoveData):
        self.Move = move


class FNetworkPredictionData_Client_Chimera:
    """~ FNetworkPredictionData_Client_Character: the client-side saved-move
    ring buffer + the ClientPredictionData that drives GetNewMove()/
    UpdateReplicatedMoveIfNeeded()."""
    EPSILON_M = 0.05

    def __init__(self, movement: UChimeraMovementComponent):
        self.movement = movement
        self.PredictedState = FMovementState()
        self.SavedMoves: list[FSavedMove_ChimeraCharacter] = []
        self.LastAckedMoveTimestamp = 0.0
        self.CorrectionCount = 0

    def GetNewMove(self, move: FCharacterNetworkMoveData, ground: "AGroundActor",
                  gravity_z: float, speed_scale: float) -> None:
        """~ ACharacter::ServerMovePacked_ClientSend path: apply locally
        (instant feel), buffer for replay-on-correction."""
        self.PredictedState = self.movement.PerformMovement(
            self.PredictedState, move, ground, gravity_z, speed_scale)
        self.SavedMoves.append(FSavedMove_ChimeraCharacter(move))
        if len(self.SavedMoves) > 256:
            self.SavedMoves.pop(0)

    def ClientHandleMoveResponse(self, ack_timestamp: float, authoritative: FMovementState,
                                 ground: "AGroundActor", gravity_z: float, speed_scale: float) -> None:
        """~ ACharacter::ClientAdjustPosition / ClientHandleMoveResponse:
        rewind to the server's acked state, replay every unacked saved move.
        A large gap after replay means the server corrected something real —
        counted, not hidden, so QA can watch UGameplayStatics-exposed net
        stats for it."""
        self.SavedMoves = [m for m in self.SavedMoves if m.Move.TimeStamp > ack_timestamp]
        replay = authoritative.Copy()
        for m in self.SavedMoves:
            replay = self.movement.PerformMovement(replay, m.Move, ground, gravity_z, speed_scale)
        if replay.Location.Dist(self.PredictedState.Location) > self.EPSILON_M:
            self.CorrectionCount += 1
        self.PredictedState = replay
        self.LastAckedMoveTimestamp = ack_timestamp


class UNetConnection:
    """~ UNetConnection: one direction of a simulated-latency pipe (a real
    connection is bidirectional + reliable/unreliable channels; two
    instances here, one per direction, keeps the pseudocode explicit)."""
    def __init__(self, rng: random.Random, one_way_ms: float = 45.0,
                jitter_ms: float = 10.0, packet_loss: float = 0.0):
        self.rng = rng
        self.one_way = one_way_ms / 1000.0
        self.jitter = jitter_ms / 1000.0
        self.packet_loss = packet_loss
        self._queue: list[tuple[float, str, Any]] = []
        self.PacketsSent = 0
        self.PacketsDropped = 0

    def SendBunch(self, now: float, kind: str, payload: Any) -> None:
        self.PacketsSent += 1
        if self.rng.random() < self.packet_loss:
            self.PacketsDropped += 1
            return
        at = now + self.one_way + self.rng.uniform(0, self.jitter)
        self._queue.append((at, kind, payload))

    def ReceiveReadyBunches(self, now: float) -> list:
        ready = [b for b in self._queue if b[0] <= now]
        self._queue = [b for b in self._queue if b[0] > now]
        ready.sort(key=lambda b: b[0])
        return ready


class ACharacterNetworkAuthority:
    """~ the SERVER-side ACharacter for one connection: consumes
    FCharacterNetworkMoveData packets IN ORDER via ServerMove_Implementation,
    steps the SAME PerformMovement the client predicted with, and produces
    authoritative snapshots at NetUpdateFrequency. Gameplay facts (footsteps)
    are SERVER facts — clients only ever hear what the authority confirmed
    (Design Law 1: never let prediction fabricate a body-fact)."""
    def __init__(self, movement: UChimeraMovementComponent, ground: "AGroundActor",
                gravity: UGravityVolumeSubsystem, net_update_hz: float = 20.0):
        self.movement = movement
        self.ground = ground
        self.gravity = gravity
        self.NetUpdateFrequency = net_update_hz
        self.State = FMovementState()
        self._last_timestamp = 0.0
        self._snap_accum = 0.0
        self.SpeedScale = 1.0
        self.FootstepOutbox: list = []

    @UFUNCTION(Server=True, Reliable=True, WithValidation=True)
    def ServerMove_Implementation(self, moves: list[FCharacterNetworkMoveData]) -> None:
        for mv in sorted(moves, key=lambda m: m.TimeStamp):
            if mv.TimeStamp <= self._last_timestamp:
                continue                                   # duplicate/reordered: drop
            gz = self.gravity.GravityAt(self.State.Location, mv.DeltaTime)
            steps: list = []
            self.State = self.movement.PerformMovement(self.State, mv, self.ground, gz,
                                                        self.SpeedScale, steps)
            self.FootstepOutbox.extend(steps)
            self._last_timestamp = mv.TimeStamp

    def TickSnapshot(self, dt: float) -> Optional[tuple[float, FMovementState]]:
        self._snap_accum += dt
        if self._snap_accum >= 1.0 / self.NetUpdateFrequency:
            self._snap_accum = 0.0
            return (self._last_timestamp, self.State.Copy())
        return None


@dataclass
class FInterpolationSample:
    t: float; loc: FVector; yaw: float


class UProxyInterpolationComponent(UActorComponent):
    """~ simulated-proxy interpolation (ROLE_SimulatedProxy pawns): render
    100ms in the past, lerping between the two bracketing snapshots — the
    standard tradeoff for smooth remote-pawn motion under jitter."""
    DELAY_S = 0.10
    def __init__(self, owner: AActor):
        super().__init__(owner)
        self.samples: list[FInterpolationSample] = []

    def Push(self, t: float, loc: FVector, yaw: float) -> None:
        self.samples.append(FInterpolationSample(t, loc, yaw))
        self.samples = self.samples[-64:]

    def Sample(self, now: float) -> Optional[tuple[FVector, float]]:
        t = now - self.DELAY_S
        for i in range(len(self.samples) - 1):
            a, b = self.samples[i], self.samples[i + 1]
            if a.t <= t <= b.t:
                f = inv_lerp(a.t, b.t, t)
                return a.loc + (b.loc - a.loc) * f, lerp(a.yaw, b.yaw, f)
        return (self.samples[-1].loc, self.samples[-1].yaw) if self.samples else None


# --- Replication Graph ---------------------------------------------------------

class UReplicationGraphNode_GridSpatialization2D(UObject):
    """~ REAL class (Engine/Plugins/Runtime/ReplicationGraph): buckets
    actors into spatial cells so relevancy queries never scan the whole
    actor list — this is the actual mechanism Fortnite-scale replication
    uses instead of O(actors x connections) distance checks every tick."""
    CELL_SIZE = 128.0

    def __init__(self):
        self.cells: dict[tuple, list[AActor]] = {}

    def _cell_of(self, loc: FVector) -> tuple:
        return (int(loc.X / self.CELL_SIZE), int(loc.Y / self.CELL_SIZE))

    def AddActor(self, actor: AActor) -> None:
        self.cells.setdefault(self._cell_of(actor.GetActorLocation()), []).append(actor)

    def Rebuild(self, actors: list[AActor]) -> None:
        self.cells.clear()
        for a in actors:
            self.AddActor(a)

    def GatherActorListsForConnection(self, viewer_loc: FVector, view_radius: float) -> list[AActor]:
        c = int(view_radius / self.CELL_SIZE) + 1
        cx, cy = self._cell_of(viewer_loc)
        out = []
        for dx in range(-c, c + 1):
            for dy in range(-c, c + 1):
                out.extend(self.cells.get((cx + dx, cy + dy), []))
        return out


class UReplicationGraphNode_AlwaysRelevant(UObject):
    """~ REAL class: a small always-relevant set (AGameStateBase, the
    player's own pawn) that bypasses spatialization entirely."""
    def __init__(self):
        self.actors: list[AActor] = []


class UReplicationGraph(UWorldSubsystem):
    """~ UReplicationGraph: composes the spatialization + always-relevant
    nodes into the per-connection replicate list, replacing the naive
    'loop every actor, check NetCullDistanceSquared' path with a real
    culling structure. VIEW_RADIUS approximates the connection's
    NetCullDistanceSquared-driven visibility."""
    VIEW_RADIUS = 400.0

    def Initialize(self, world: "UWorld") -> None:
        self.grid = UReplicationGraphNode_GridSpatialization2D()
        self.always_relevant = UReplicationGraphNode_AlwaysRelevant()
        self.stats = dict(actors_replicated=0, bytes_estimate=0)

    def Tick(self, dt: float) -> None: pass

    def RebuildFrame(self, all_networked_actors: list[AActor], game_state: AActor) -> None:
        self.grid.Rebuild(all_networked_actors)
        self.always_relevant.actors = [game_state]

    def ReplicateForConnection(self, viewer: AActor) -> list[AActor]:
        relevant = self.grid.GatherActorListsForConnection(viewer.GetActorLocation(), self.VIEW_RADIUS)
        relevant += self.always_relevant.actors
        self.stats["actors_replicated"] += len(relevant)
        self.stats["bytes_estimate"] += len(relevant) * 24     # ~ FVector_NetQuantize + yaw
        return relevant


# RPC classification (real UFUNCTION specifier taxonomy — decorators used
# throughout this file document the intended macro on the C++ port):
#   Server, Reliable, WithValidation : ServerMove, gesture intent, dig/trade requests (client->server)
#   Client, Reliable                 : ClientHandleMoveResponse, will-reading open (server->owning client)
#   NetMulticast, Unreliable          : cosmetic FX fanout (footstep dust/sound to all in relevancy)


# =============================================================================
# §10. WORLD SYSTEMS — ground, sky/weather, Erisaid, habitat, memorial,
# sacrifice log, generations, director, UMG HUD.
# Component names below (USacrificeLogComponent, UCostlessLifeEndingDiagnostic)
# match files that ALREADY EXIST in Source/Chimera/ProceduralGenerated/Save/
# in this repo — this pseudocode converges on the real project's own naming
# rather than inventing parallel terms.
# =============================================================================

DAY_LENGTH_HOURS = 27.0


class ESurfaceType(Enum):
    SAND = auto(); ROCK = auto(); METAL = auto(); BASIN = auto()
    ICE = auto(); INTERIOR = auto()


SURFACE_TABLE = {         # traction, makes_print, dust_scale, footstep_synth_hz(SOURCE_FOOTSTEP_GRAPH_HZ key)
    "SAND":     (0.75, True,  1.00, "SAND"),
    "BASIN":    (0.45, True,  1.60, "SAND"),
    "ROCK":     (1.00, False, 0.15, "ROCK"),
    "METAL":    (0.90, True,  0.05, "METAL"),
    "ICE":      (0.35, False, 0.02, "ICE"),
    "INTERIOR": (1.00, False, 0.00, "INTERIOR"),
}


@UCLASS(Blueprintable=True)
class AGroundActor(AActor):
    """~ the persistent terrain actor. Authored pads + fbm noise + LIVE dig
    deltas (§8's GA_Dig writes directly into game.dig_delta, which this
    actor was constructed with a reference to — one ground truth for
    physics, NavMesh, audio, and the dust material)."""
    def __init__(self, world: "UWorld", seed: int, dig_delta_ref: dict):
        super().__init__(world)
        self.seed = seed
        self.dig_delta = dig_delta_ref
        self.StaticMeshComponent = self.CreateDefaultSubobject(
            UStaticMeshComponent(self, "SM_YardPatch", "M_Sand"))

    def SurfaceAt(self, p: FVector) -> str:
        if p.Size2D() > 90.0 and fbm2(p.X * 0.01, p.Y * 0.01, 3, self.seed) > 0.62:
            return "ROCK"
        for i in range(3):
            pad = golden_spiral_point(i * 5 + 4, 14.0)
            if p.Dist2D(pad) < 6.0:
                return "METAL"
        if p.Dist2D(FVector(-42.0, -35.0, 0.0)) < 18.0:
            return "BASIN"
        return "SAND"

    def HeightAt(self, p: FVector) -> float:
        dune = fbm2(p.X * 0.02, p.Y * 0.02, 4, self.seed) * 2.2
        ridge = (fbm2(p.X * 0.05, p.Y * 0.05, 5, self.seed + 7) * 6.0
                if self.SurfaceAt(p) == "ROCK" else 0.0)
        k = (math.floor(p.X / DIG["cell"]), math.floor(p.Y / DIG["cell"]))
        return dune + ridge + self.dig_delta.get(k, 0.0)

    def TractionAt(self, p: FVector) -> float:
        return SURFACE_TABLE[self.SurfaceAt(p)][0]


@UCLASS(Blueprintable=True)
class ADirectionalLight(AActor):
    """~ REAL actor class (ADirectionalLight : public ALight). The sun; also
    the circadian clock (27h day — long dusks by design)."""
    def __init__(self, world: "UWorld"):
        super().__init__(world)
        self.LightComponent = self.CreateDefaultSubobject(UDirectionalLightComponent(self))
        self.time_h = 8.0
        self.day = 0
        self.earth_phase = 0.35
        self.moon_bearing_deg = 40.0

    def Tick(self, hours: float) -> None:
        self.time_h += hours
        while self.time_h >= DAY_LENGTH_HOURS:
            self.time_h -= DAY_LENGTH_HOURS
            self.day += 1
        self.earth_phase = 0.5 + 0.5 * math.sin(TAU * self.day / 29.5)
        self.moon_bearing_deg = (self.moon_bearing_deg + hours * 3.1) % 360.0

    def IsNight(self) -> bool:
        t = self.time_h / DAY_LENGTH_HOURS
        return t < 0.20 or t > 0.80

    def SunElevationDeg(self) -> float:
        t = self.time_h / DAY_LENGTH_HOURS
        return math.sin((t - 0.20) / 0.60 * math.pi) * 62.0 if 0.20 <= t <= 0.80 else -12.0

    def GetSunDirection(self) -> FVector:
        e = math.radians(self.SunElevationDeg())
        return FVector(math.cos(e), 0.0, -math.sin(e)).GetSafeNormal()

    def TemperatureC(self) -> float:
        e = max(0.0, self.SunElevationDeg()) / 62.0
        return lerp(SUIT["night_temp_c"], SUIT["day_temp_c"], e)


class UWeatherSubsystem(UWorldSubsystem):
    """Gusts + the ~weekly storm that erases sand footprints, clogs suits
    (via GE_DustClog_Storm), and fills the air with NS_StormWall. The
    memento mori — storms are why footprints don't accumulate forever."""
    def Initialize(self, world: "UWorld") -> None:
        pass

    def Bind(self, rng: random.Random) -> None:
        self.rng = rng
        self.wind_speed = WIND["calm"]
        self.wind_dir = rng.uniform(0, TAU)
        self.storm_active = False
        self._storm_ends_h = 0.0
        self._next_storm_day = rng.uniform(*WIND["storm_period_days"])
        self._next_gust_s = rng.uniform(*WIND["gust_period_s"])
        self.dust_age_h = 0.0

    def Tick(self, dt: float) -> None: pass

    def WindVector(self) -> FVector:
        return FVector(math.cos(self.wind_dir), math.sin(self.wind_dir), 0.0) * (self.wind_speed * 0.3)

    def TickWeather(self, game: "ChimeraGame", dt: float) -> None:
        hours = dt / 3600.0
        sun = game.sun_actor
        if self.storm_active:
            self.wind_speed = WIND["storm"] * self.rng.uniform(0.85, 1.15)
            self._storm_ends_h -= hours
            self.dust_age_h = max(0.0, self.dust_age_h - 5.0 * hours)
            if self.rng.random() < 0.2:
                game.niagara.SpawnSystemAtLocation("NS_StormWall", game.camera.Eye + FVector(10, 0, 2), 0.1)
            if self._storm_ends_h <= 0.0:
                self.storm_active = False
                before = len(game.footprints)
                game.footprints = [fp for fp in game.footprints if fp[2] == "METAL"]
                game.event_bus.OnStorm.Broadcast(FStormEvent("passed", before - len(game.footprints)))
        else:
            base = WIND["breeze"] if not sun.IsNight() else WIND["calm"]
            self._next_gust_s -= dt
            if self._next_gust_s <= 0.0:
                self._next_gust_s = self.rng.uniform(*WIND["gust_period_s"])
                base = WIND["gust"]
            self.wind_speed = lerp(self.wind_speed, base, clamp(0.4 * dt, 0, 1))
            self.wind_dir += self.rng.uniform(-0.1, 0.1) * dt
            self.dust_age_h += hours
            if sun.day + sun.time_h / DAY_LENGTH_HOURS >= self._next_storm_day:
                self.storm_active = True
                self._storm_ends_h = self.rng.uniform(*WIND["storm_duration_min"]) / 60.0
                self._next_storm_day += self.rng.uniform(*WIND["storm_period_days"])
                game.event_bus.OnStorm.Broadcast(FStormEvent("rising"))
        game.mpc.SetScalarParameterValue("WindSpeed", self.wind_speed)
        game.mpc.SetScalarParameterValue("StormIntensity", 1.0 if self.storm_active else 0.0)
        game.mpc.SetScalarParameterValue("DustAgeHours", self.dust_age_h)
        if game.player_actor.FindComponentByClass(UAbilitySystemComponent) and self.storm_active \
                and not game.player_indoors:
            game.player_actor.AbilitySystemComponent.ApplyGameplayEffectToSelf(GE_DustClog_Storm)
        elif not self.storm_active:
            game.player_actor.AbilitySystemComponent.RemoveActiveGameplayEffect(GE_DustClog_Storm)


@UCLASS(Blueprintable=True)
class AErisaidActor(AActor):
    """~ the half-buried leviathan shell, 18m long, at the Yard's edge."""
    def __init__(self, world: "UWorld", pos: FVector):
        super().__init__(world)
        self.RootComponent.RelativeTransform.Location = pos
        self.StaticMeshComponent = self.CreateDefaultSubobject(
            UStaticMeshComponent(self, "SM_Erisaid", "M_ErisaidShell"))
        self.AudioVolume = AAudioVolume(world, FVector(10, 6, 4), "erisaid_hollow", 0.6)


@UCLASS(Blueprintable=True)
class AHabitatActor(AActor):
    """~ AShelterHabitat (manual lane). Home: inherited, extended,
    life-support. Modules apply GAS effects to the player while inside —
    O2 Garden/Battery Bank/Airlock are literally UGameplayEffects being
    added/removed by proximity, not ad-hoc per-frame math."""
    RADIUS = 6.0
    MODULE_EFFECTS = {"O2_GARDEN": GE_O2Regen_Garden, "BATTERY_BANK": GE_BatteryRegen_Bank,
                      "AIRLOCK": GE_DustClog_Scrub}

    def __init__(self, world: "UWorld", pos: FVector):
        super().__init__(world)
        self.RootComponent.RelativeTransform.Location = pos
        self.StaticMeshComponent = self.CreateDefaultSubobject(
            UStaticMeshComponent(self, "SM_HabitatDome", "M_HabGlass"))
        self.LightComponent = self.CreateDefaultSubobject(UPointLightComponent(self, 800.0, 8.0))
        self.AudioVolume = AAudioVolume(world, FVector(6, 6, 3), "habitat_shell", 0.35)
        self.Modules: list[str] = ["AIRLOCK", "O2_GARDEN", "BATTERY_BANK"]

    def TickLifeSupport(self, game: "ChimeraGame") -> None:
        inside = game.player_actor.GetActorLocation().Dist2D(self.GetActorLocation()) <= self.RADIUS
        game.player_indoors = inside
        asc = game.player_actor.AbilitySystemComponent
        for module, ge in self.MODULE_EFFECTS.items():
            has_module = module in self.Modules
            if inside and has_module:
                asc.ApplyGameplayEffectToSelf(ge)
            else:
                asc.RemoveActiveGameplayEffect(ge)
        if inside:
            asc.AttributeSet.Temperature.CurrentValue = 20.0


@dataclass
class FStar:
    life_name: str; generation: int; brightness: float; twinkle: bool; bearing_deg: float


class UStarMemorialSubsystem(UWorldSubsystem):
    """~ StarMemorialComponent (the studio's own component, writing a star
    texture in the real port). Bright ancestors light the Yard's night —
    fed into ALumenSurfaceCacheApprox's memorial_light term (§4)."""
    def Initialize(self, world: "UWorld") -> None:
        self.stars: list[FStar] = []

    def Tick(self, dt: float) -> None: pass

    def AddLife(self, name: str, generation: int, sacrifice_weight: float, open_pains: int) -> FStar:
        b = 1.0 - math.exp(-sacrifice_weight / STAR["brightness_k"])
        s = FStar(name, generation, b, open_pains > 0, (len(self.stars) * GOLDEN_ANGLE_DEG) % 360.0)
        self.stars.append(s)
        return s

    def NightLightLevel(self) -> float:
        return min(0.5, sum(s.brightness for s in self.stars
                            if s.brightness >= STAR["bright_lights_yard"]) * 0.18)


@UCLASS()
class USacrificeLogComponent(UActorComponent):
    """~ REAL project file: Source/Chimera/ProceduralGenerated/Save/
    SacrificeLogComponent.h/cpp. Tracks what the player protected AT COST.
    NO gauge, NO UI surfaces it — read twice ever: by the star at death, by
    the Erisaid's mirror (Design Law 2)."""
    def __init__(self, owner: AActor):
        super().__init__(owner)
        self.entries: list[tuple] = []       # (kind, weight, note, generation, day)

    def Record(self, kind: str, note: str, generation: int, day: int) -> None:
        self.entries.append((kind, SACRIFICE_WEIGHTS[kind], note, generation, day))

    def WeightForGeneration(self, generation: int) -> float:
        return sum(e[1] for e in self.entries if e[3] == generation)


class EEndingKind(Enum):
    COSTLESS_LIFE = auto(); QUIET_STAR = auto(); BRIGHT_STAR = auto(); MIRROR_KEEPER = auto()


@dataclass
class FMirrorVision:
    empty: bool; figures: list


@UCLASS()
class UCostlessLifeEndingDiagnostic(UActorComponent):
    """~ REAL project file: Source/Chimera/ProceduralGenerated/Save/
    CostlessLifeEndingDiagnostic.h/cpp. Postflight diagnostic: calculates
    sacrifice-log emptiness and selects the ending sequence. Design Law 2's
    failure ending is not death — it is THIS: a dim star, an empty mirror."""
    def __init__(self, owner: AActor):
        super().__init__(owner)

    def Mirror(self, log: USacrificeLogComponent, generation: int) -> FMirrorVision:
        entries = [e for e in log.entries if e[3] == generation]
        return FMirrorVision(not entries, [e[2] or e[0] for e in entries])

    def EvaluateEnding(self, log: USacrificeLogComponent, generation: int,
                       attuned: bool) -> EEndingKind:
        w = log.WeightForGeneration(generation)
        if w <= 0.0:
            return EEndingKind.COSTLESS_LIFE
        if attuned:
            return EEndingKind.MIRROR_KEEPER
        b = 1.0 - math.exp(-w / STAR["brightness_k"])
        return EEndingKind.BRIGHT_STAR if b >= STAR["bright_lights_yard"] else EEndingKind.QUIET_STAR


@dataclass
class FLifeRecord:
    name: str; generation: int; days_lived: float; cause: str
    sacrifice_weight: float; ending: EEndingKind


class UGenerationSubsystem(UWorldSubsystem):
    """~ death/retirement -> star -> Will -> heir. Bound to
    UChimeraEventBus.OnDeath. The heir literally wakes at the habitat."""
    def Initialize(self, world: "UWorld") -> None:
        self.records: list[FLifeRecord] = []

    def Tick(self, dt: float) -> None: pass

    def Bind(self, bus: UChimeraEventBus) -> None:
        bus.OnDeath.AddDynamic(lambda ev, bus=bus: None)   # game wires the real handler (§11)

    def EndLife(self, game: "ChimeraGame", cause: str) -> FLifeRecord:
        actor = game.player_actor
        log = actor.FindComponentByClass(USacrificeLogComponent)
        diag = actor.FindComponentByClass(UCostlessLifeEndingDiagnostic)
        if (actor.Tags.HasTag("State.Threatened") and not actor.Tags.HasTag("State.WeaponFiredThisLife")
                and game.weapon_ammo > 0):
            game.record_sacrifice("WEAPON_NEVER_FIRED", "was threatened; the weapon stayed cold")
        weight = log.WeightForGeneration(game.generation)
        pains = game.refused_unpayable_count
        ending = diag.EvaluateEnding(log, game.generation, game.attunement.attuned)
        game.memorial.AddLife(f"gen_{game.generation}", game.generation, weight, pains)
        rec = FLifeRecord(f"gen_{game.generation}", game.generation,
                          game.sun_actor.day + game.sun_actor.time_h / DAY_LENGTH_HOURS,
                          cause, weight, ending)
        self.records.append(rec)
        game.ui.OpenWillScreen()
        carry = actor.FindComponentByClass(UCarryComponent)
        heirloom = carry.Hands if (carry.Hands and carry.Hands.Kind == "HEIRLOOM") else None
        attrs = actor.AbilitySystemComponent.AttributeSet
        attrs.O2.CurrentValue = attrs.Battery.CurrentValue = attrs.Integrity.CurrentValue = 100.0
        attrs.DustClog.CurrentValue = 0.0
        carry.Hands, carry.Pack = heirloom, []
        game.credits = round(game.credits * 0.5)
        game.generation += 1
        game.weapon_ammo = 6
        game.shovel_durability = 200.0
        for tag in ("State.WeaponFiredThisLife", "State.Threatened"):
            actor.Tags.RemoveTag(tag)
        game.teleport_player(game.habitat_actor.GetActorLocation() + FVector(2.0, 0.0, 0.0))
        game.save_subsystem.Autosave(game)
        game.ui.CloseWillScreen()
        return rec


class UDirectorSubsystem(UWorldSubsystem):
    """~ the circadian dungeon master. Spawns strangers/traders/pirates as
    MASS ENTITIES (cheap, LOD-driven — §6), on golden-angle bearings so
    arrivals never bunch up on one horizon. Pirates only bother the visibly
    rich during storms."""
    SCENARIOS = [("o2", "suit hissing"), ("parts", "rover dead 3km out"),
                ("water", "empty flask"), ("warmth", "battery flat at dusk"),
                ("burial", "carries a body; asks with their eyes"),
                ("ride", "points at the horizon, then at you")]

    def Initialize(self, world: "UWorld") -> None:
        pass

    def Bind(self, rng: random.Random) -> None:
        self.rng = rng
        self.stranger_cadence_days = (1.0, 2.2)      # real game; demo compresses this
        self._next_stranger_day = 0.5
        self._next_trader_day = 0.8
        self._spawned = 0
        self._gen_first_sent: set = set()   # DESIGN RULE: each gen's first
        # stranger cannot pay — the Yard teaches Law 2 before it trades.

    def Tick(self, dt: float) -> None: pass

    def Phase(self, sun: ADirectionalLight) -> str:
        t = sun.time_h / DAY_LENGTH_HOURS
        if t < 0.20: return "night"
        if t < 0.30: return "dawn"
        if t < 0.70: return "day"
        if t < 0.80: return "dusk"
        return "night"

    def _spawn_dot_entity(self, game: "ChimeraGame", archetype: str, pos: FVector,
                          need: Optional[str], can_pay: bool) -> None:
        em = game.mass_subsystem.EntityManager
        stable_id = f"{archetype}_{game.generation}_{self._spawned}"
        h = em.CreateEntity(
            FTransformFragment(FTransform(Location=pos)), FMassVelocityFragment(),
            FAgentRadiusFragment(),
            FMassDotStateFragment(archetype, "distant", need, can_pay, stable_id))
        game.mass_lod[h] = EMassLOD.Off

    def TickDirector(self, game: "ChimeraGame", dt: float) -> None:
        now_days = game.sun_actor.day + game.sun_actor.time_h / DAY_LENGTH_HOURS
        ppos = game.player_actor.GetActorLocation()
        if now_days >= self._next_stranger_day:
            self._next_stranger_day = now_days + self.rng.uniform(*self.stranger_cadence_days)
            need, _blurb = self.rng.choice(self.SCENARIOS)
            bearing = golden_spiral_point(self._spawned, 30.0).GetSafeNormal()
            first_of_gen = game.generation not in self._gen_first_sent
            self._gen_first_sent.add(game.generation)
            self._spawn_dot_entity(game, "stranger", ppos + bearing * 260.0, need,
                                   can_pay=(False if first_of_gen else self.rng.random() < 0.35))
            self._spawned += 1
        if now_days >= self._next_trader_day:
            self._next_trader_day = now_days + self.rng.uniform(0.7, 1.5)
            st = game.stations[0]
            self._spawn_dot_entity(game, "trader",
                                   st.pos + FVector(self.rng.uniform(-30, 30), self.rng.uniform(-30, 30), 0),
                                   None, True)
            self._spawned += 1
        if game.credits > 200 and game.weather.storm_active and self.rng.random() < 0.02 * dt:
            self._spawn_dot_entity(game, "pirate", ppos + FVector(180, 40, 0), None, True)
            self._spawned += 1


# --- UMG HUD -------------------------------------------------------------------

class UUserWidget:
    """~ UUserWidget: retained-mode node with children; describe() stands in
    for the Slate draw pass."""
    def __init__(self, name: str):
        self.name = name
        self.bVisible = True
        self.Children: list["UUserWidget"] = []

    def AddChild(self, w: "UUserWidget") -> "UUserWidget":
        self.Children.append(w)
        return w


class USuitWristGauge(UUserWidget):
    """O2 needle — the player glances DOWN (Bend micro-verb) to read it.
    Diegetic; no floating bars anywhere in this HUD."""
    def __init__(self):
        super().__init__("WBP_SuitWristGauge")
        self.NeedleDeg = 0.0

    def Update(self, o2_fraction: float, dt: float) -> None:
        target = lerp(-80.0, 80.0, o2_fraction)
        self.NeedleDeg = lerp(self.NeedleDeg, target, clamp(3.0 * dt, 0, 1))


class UCompassRim(UUserWidget):
    """Helmet-rim tick lights; Earth itself is north."""
    def __init__(self):
        super().__init__("WBP_CompassRim")
        self.Pips: list = []

    def Update(self, yaw: float, marks: dict) -> None:
        self.Pips = [(name, (math.degrees(math.atan2(p.Y, p.X)) - math.degrees(yaw)) % 360.0)
                    for name, p in marks.items()]


class UGestureWheel(UUserWidget):
    """Radial verb menu (hold TAB) — the entire social interface (Law 3)."""
    GESTURES = ("wave", "offer", "refuse", "point", "kneel", "beckon", "thank")
    def __init__(self):
        super().__init__("WBP_GestureWheel")
        self.bVisible = False
        self.Highlighted: Optional[str] = None

    def SelectFromStick(self, stick: FVector) -> Optional[str]:
        if stick.Size2D() < 0.5:
            self.Highlighted = None
            return None
        ang = math.atan2(stick.Y, stick.X) % TAU
        self.Highlighted = self.GESTURES[int(ang / TAU * len(self.GESTURES)) % len(self.GESTURES)]
        return self.Highlighted


class UGlyphSubtitleStrip(UUserWidget):
    """Accessibility: gestures/world sounds as pictograms. Still wordless."""
    def __init__(self):
        super().__init__("WBP_GlyphStrip")
        self.Glyphs: list = []
    def Push(self, glyph: str) -> None:
        self.Glyphs = (self.Glyphs + [glyph])[-5:]


class UChimeraHUD:
    """~ AHUD + the top-level widget stack. Menu FSM (BOOT/TITLE/IN_GAME/
    PAUSED/WILL_READING) + per-frame widget updates."""
    def __init__(self):
        self.wrist = USuitWristGauge()
        self.compass = UCompassRim()
        self.wheel = UGestureWheel()
        self.glyph_strip = UGlyphSubtitleStrip()
        self.will_screen = UUserWidget("WBP_WillScreen")
        self.will_screen.bVisible = False
        self.state = "IN_GAME"

    def OpenWillScreen(self) -> None:
        self.state = "WILL_READING"
        self.will_screen.bVisible = True

    def CloseWillScreen(self) -> None:
        self.state = "IN_GAME"
        self.will_screen.bVisible = False

    def Tick(self, game: "ChimeraGame", dt: float) -> None:
        attrs = game.player_actor.AbilitySystemComponent.AttributeSet
        tr = game.player_actor.RootComponent.GetComponentTransform()
        self.wrist.Update(attrs.O2.CurrentValue / 100.0, dt)
        marks = {"habitat": game.habitat_actor.GetActorLocation() - tr.Location}
        if game.attunement.visit_days:
            marks["erisaid"] = game.erisaid_actor.GetActorLocation() - tr.Location
        self.compass.Update(game.player_actor.Yaw, marks)


# --- Loop 9: The Universe — golden-angle bodies, observation collapse ------
# ~ core.world_store.around() is this project's real streaming primitive;
# UE5 World Partition (§2) is the spatial layer it feeds. Design Law 4:
# nothing OBSERVED is lost, and nothing UNOBSERVED is finalized — a system
# body only becomes permanent state the moment a scan/arrival collapses it.

class EBodyKind(Enum):
    PLANETOID = auto(); MOONLET = auto(); ASTEROID_FIELD = auto()
    DEBRIS_FIELD = auto(); STATION = auto()


@dataclass
class FUniverseBody:
    body_id: str
    kind: EBodyKind
    pos: FVector           # km-scale in system space
    seed: int
    observed: bool = False


class AUniverseActor(AActor):
    """~ a level-persistent actor owning the system's body catalog + the
    observed-cell ledger. Bodies are laid out on the golden spiral (Design
    Law 5, same generator as buried caches and stranger bearings, just at
    system scale); ObserveRegion collapses a neighborhood permanently."""
    OBS_CELL = 50.0

    def __init__(self, world: "UWorld", seed: int):
        super().__init__(world)
        kinds = [EBodyKind.MOONLET, EBodyKind.ASTEROID_FIELD, EBodyKind.DEBRIS_FIELD,
                EBodyKind.PLANETOID, EBodyKind.STATION]
        self.Bodies = [FUniverseBody(f"body_{i}", kinds[i % 5],
                                     golden_spiral_point(i, 5000.0), seed * 31 + i)
                      for i in range(24)]
        self.ObservedCells: set = set()

    def ObserveRegion(self, at: FVector, radius: float) -> int:
        newly, c = 0, int(radius / self.OBS_CELL)
        cx, cy = int(at.X / self.OBS_CELL), int(at.Y / self.OBS_CELL)
        for dx in range(-c, c + 1):
            for dy in range(-c, c + 1):
                k = (cx + dx, cy + dy)
                if k not in self.ObservedCells:
                    self.ObservedCells.add(k)
                    newly += 1
        for body in self.Bodies:
            if not body.observed and body.pos.Dist2D(at) <= radius * 50.0:  # km vs m scale
                body.observed = True
        return newly

    def Around(self, pos: FVector, radius: float) -> list:
        return [b for b in self.Bodies if b.pos.Dist(pos) <= radius]


# =============================================================================
# §11. BOOT — AChimeraCharacter, player controller, ChimeraGame assembly, proof
# ~ UGameInstance::Init -> AGameModeBase::InitGame -> level BeginPlay ->
# PossessPawn. "ChimeraGame" below is this pseudocode's necessary top-level
# wiring harness — real UE5 spreads this across GameMode/GameInstance/
# Character BeginPlay; it is NOT itself a UE class.
# =============================================================================

@UCLASS(Blueprintable=True)
class AChimeraCharacter(AActor):
    """~ AChimeraCharacter : public ACharacter. GENERATED_BODY()
    CreateDefaultSubobject wiring for every subsystem built in §3-§9."""
    def __init__(self, world: "UWorld", ground: AGroundActor):
        super().__init__(world)
        self.CapsuleComponent = self.CreateDefaultSubobject(UCapsuleComponent(self))
        self.SkeletalMeshComponent = self.CreateDefaultSubobject(
            USkeletalMeshComponent(self, "SK_Astronaut"))
        self.SkeletalMeshComponent.AnimInstance = UChimeraAnimInstance(ground)
        self.MovementComponent = UChimeraMovementComponent()
        self.SuitAttributeSet = USuitAttributeSet()
        self.AbilitySystemComponent = self.CreateDefaultSubobject(
            UAbilitySystemComponent(self, self.SuitAttributeSet))
        self.AbilitySystemComponent.GrantAbility("Dig", GA_Dig())
        self.AbilitySystemComponent.GrantAbility("Scan", GA_Scan())
        self.AbilitySystemComponent.GrantAbility("Fire", GA_Fire())
        self.AbilitySystemComponent.GrantAbility("PickupDrop", GA_PickupDrop())
        self.AbilitySystemComponent.GrantAbility("Attune", GA_Attune())
        self.CarryComponent = self.CreateDefaultSubobject(UCarryComponent(self))
        self.SacrificeLogComponent = self.CreateDefaultSubobject(USacrificeLogComponent(self))
        self.EndingDiagnostic = self.CreateDefaultSubobject(UCostlessLifeEndingDiagnostic(self))
        self.MotionWarpingComponent = self.CreateDefaultSubobject(UMotionWarpingComponent(self))
        self.Tags = FGameplayTagContainer()
        # H-31/H-34 fix, made structural: SandSoundComponent attaches HERE,
        # at construction, never left to Blueprint wiring that can silently
        # drop it.
        self.SandSoundComponent = self.CreateDefaultSubobject(UChimeraSandSoundComponent(self))
        self.Yaw = 0.0
        self.bReplicates = True
        self.RemoteRole = ENetRole.ROLE_AutonomousProxy
        self.NetUpdateFrequency = 30.0            # a hero pawn updates faster than props


class UChimeraPlayerController:
    """~ APlayerController + its UEnhancedInputLocalPlayerSubsystem. Not an
    AActor in this pseudocode (no server/client possession split needed
    headless) — owns the Enhanced Input resolution + streaming source."""
    def __init__(self, pawn: AChimeraCharacter, forgiveness_scale: float):
        self.Pawn = pawn
        self.InputSubsystem = UEnhancedInputLocalPlayerSubsystem()
        self.MappingContext = UInputMappingContext(forgiveness_scale)
        self.InputSubsystem.AddMappingContext(self.MappingContext, priority=0)
        self.StreamingSource = pawn.CreateDefaultSubobject(
            UWorldPartitionStreamingSourceComponent(pawn, loading_range=160.0))
        self._seq = 0

    def BuildMoveData(self, raw_device_state: dict, now: float, dt: float) -> FCharacterNetworkMoveData:
        self.InputSubsystem.InjectRawDeviceState(raw_device_state, now)
        move_axis = self.InputSubsystem.PeekAxis("IA_Move")
        look_axis = self.InputSubsystem.PeekAxis("IA_Look")
        self.Pawn.Yaw += look_axis.X * 2.2 * dt
        self._seq += 1
        return FCharacterNetworkMoveData(
            TimeStamp=now, Acceleration=move_axis, ControlYaw=self.Pawn.Yaw, ControlPitch=0.0,
            bPressedJump=bool(self.InputSubsystem.GetActionValue("IA_Jump")),
            bWantsToCrouch="IA_Bend" in self.InputSubsystem.values,
            bWantsToSprint="IA_Sprint" in self.InputSubsystem.values, DeltaTime=dt)


class ChimeraGame:
    """The session harness: constructs the UWorld + every subsystem, wires
    delegates, and drives one master Tick() in ETickingGroup order. Mirrors
    what UGameInstance::Init + AGameModeBase::InitGame + level BeginPlay do
    in aggregate on a real UE5 boot."""

    def __init__(self, seed: int = 7):
        self.seed = seed
        self.rng = random.Random(seed)
        self.now_s = 0.0
        self.generation = 1
        self.credits = 40.0
        self.weapon_ammo = 6
        self.shovel_durability = 200.0
        self.refused_unpayable_count = 0
        self.player_indoors = False
        self.scan_pips: list = []
        self.dig_delta: dict = {}
        self.buried: dict = {}
        self.footprints: list = []
        self.world_items: list = []          # dropped-item actors (kind/quality/gen only)
        self.dot_memory_ledger: dict = {}     # StableId -> memory dict (Design Law 4)
        self.mass_lod: dict = {}
        self.titan_best: dict = {}

        self.world = UWorld()
        self.assets = AssetRegistry(seed)
        self.camera = APlayerCameraManager()
        self.ground_actor = AGroundActor(self.world, seed, self.dig_delta)
        self.sun_actor = ADirectionalLight(self.world)

        self.gravity = UGravityVolumeSubsystem(); self.gravity.Initialize(self.world)
        self.navmesh = ARecastNavMesh(self.ground_actor)
        self.navsys = UNavigationSystemV1(); self.navsys.Initialize(self.world)
        self.navsys.RegisterNavMesh(self.navmesh)
        self.ai_system = UAISystem(); self.ai_system.Initialize(self.world)
        self.mass_subsystem = UMassEntitySubsystem()
        self.mass_subsystem.RegisterProcessor(UMassLODCollectorProcessor())
        self.mass_subsystem.RegisterProcessor(UMassMovementProcessor())
        self.mass_subsystem.BindGame(self)
        self.mass_actor_spawner = UMassActorSpawnerSubsystem(); self.mass_actor_spawner.Initialize(self.world)
        self.event_bus = UChimeraEventBus(); self.event_bus.Initialize(self.world)
        self.audio_device = UAudioDeviceStub(); self.audio_device.Initialize(self.world)
        self.niagara = UNiagaraSimulationSubsystem(); self.niagara.Initialize(self.world)
        self.renderer = URendererSubsystem(); self.renderer.Initialize(self.world)
        self.renderer.Bind(self.assets, self.camera, self.sun_actor.LightComponent)
        self.mpc = self.assets.mpc
        self.world_partition = UWorldPartitionSubsystem(); self.world_partition.Initialize(self.world)
        self.repgraph = UReplicationGraph(); self.repgraph.Initialize(self.world)
        self.weather = UWeatherSubsystem(); self.weather.Initialize(self.world); self.weather.Bind(self.rng)
        self.memorial = UStarMemorialSubsystem(); self.memorial.Initialize(self.world)
        self.factions = UFactionSubsystem(); self.factions.Initialize(self.world)
        self.director = UDirectorSubsystem(); self.director.Initialize(self.world)
        self.director.Bind(random.Random(seed ^ 0x5EED))       # own dice — independent of gameplay rng
        self.generations = UGenerationSubsystem(); self.generations.Initialize(self.world)
        self.save_subsystem = USaveGameSubsystem(); self.save_subsystem.Initialize(self.world)

        self.habitat_actor = AHabitatActor(self.world, FVector(8.0, 6.0, 0.0))
        self.erisaid_actor = AErisaidActor(self.world, FVector(310.0, -180.0, 0.0))
        self.stations = [
            FStationMarket("yard_gate", FVector(60.0, 20.0, 0.0),
                          {"OXYGEN_CAN": 20, "MACHINE_PARTS": 8}, {"ORE_ILMENITE": 1.4, "ICE_WATER": 1.7}),
            FStationMarket("far_pads", FVector(-900.0, 400.0, 0.0),
                          {"FUEL_CELL": 12, "SEEDS": 6}, {"REGOLITH_GLASS": 1.8})]
        self.titan_gravity_volumes = TitanRunTrack(self.world, FVector(-200.0, 150.0, 0.0), self.gravity)
        self.universe_actor = AUniverseActor(self.world, seed)

        self.player_actor = AChimeraCharacter(self.world, self.ground_actor)
        self.attunement = self.player_actor.CreateDefaultSubobject(
            UChimeraAttunementComponent(self.player_actor))
        self.player_actor.SandSoundComponent.BindDelegate(self.event_bus)
        self.controller = UChimeraPlayerController(self.player_actor, ACCESSIBILITY["input_forgiveness_scale"])
        self.world_partition.RegisterStreamingSource(self.controller.StreamingSource)
        self.net_authority = ACharacterNetworkAuthority(self.player_actor.MovementComponent,
                                                        self.ground_actor, self.gravity)
        self.net_client = FNetworkPredictionData_Client_Chimera(self.player_actor.MovementComponent)
        self.up_conn = UNetConnection(self.rng)
        self.down_conn = UNetConnection(self.rng)
        self.ui = UChimeraHUD()

        self.event_bus.OnDeath.AddDynamic(lambda ev: self.generations.EndLife(self, ev.Cause))
        self.event_bus.OnGesture.AddDynamic(self._on_gesture)
        self._responded_this_encounter: set = set()

        self._populate_level()

    # -- PCG-authored buried history (§6's real node-graph pipeline) --------
    def _populate_level(self) -> None:
        kinds = ["ORE_ILMENITE", "RELIC_SHARD", "ICE_WATER", "ERISAID_FRAGMENT"]
        def spawn_buried(point: FPCGPoint) -> None:
            k = (math.floor(point.Transform.Location.X / DIG["cell"]),
                math.floor(point.Transform.Location.Y / DIG["cell"]))
            self.buried.setdefault(k, []).append(
                dict(kind=kinds[point.Seed % 4], depth=point.Transform.Location.Z, quality=1.0))
        pcg_graph = UPCGGraph(
            "PCG_BuriedHistory",
            UPCGSurfaceSamplerSettings(count=32, spacing=11.0),
            UPCGDensityFilterSettings(threshold=0.15, seed=42),
            UPCGTransformPointsSettings(z_offset_fn=lambda seed: 0.15 + (seed % 4) * 0.15),
            UPCGSpawnActorSettings(factory=spawn_buried))
        self.pcg_component = UPCGComponent(self.ground_actor, pcg_graph)
        self.pcg_component.Generate()
        rock_graph = UPCGGraph("PCG_DecorativeRocks",
                               UPCGSurfaceSamplerSettings(count=12, spacing=13.0))
        for pt in rock_graph.Generate():
            pt.Transform.Location.Z = self.ground_actor.HeightAt(pt.Transform.Location)

    def spawn_world_item(self, kind: str, loc: FVector, quality: float) -> None:
        item = AActor(self.world)
        item.RootComponent.RelativeTransform.Location = loc
        item.CreateDefaultSubobject(UStaticMeshComponent(item, "SM_Rock", "M_Rock"))
        item.Kind, item.Quality, item.OriginGeneration = kind, quality, self.generation
        self.world_items.append(item)

    def record_sacrifice(self, kind: str, note: str = "") -> None:
        self.player_actor.SacrificeLogComponent.Record(kind, note, self.generation, self.sun_actor.day)
        self.event_bus.OnSacrifice.Broadcast(FSacrificeEvent(kind, SACRIFICE_WEIGHTS[kind], note, self.generation))

    def teleport_player(self, pos: FVector) -> None:
        """Generation reset / beat-script reset_position (H-25): BOTH ends."""
        for st in (self.net_authority.State, self.net_client.PredictedState):
            st.Location, st.Velocity, st.MovementMode = FVector(*pos.ToTuple()), FVector(), EMovementMode.MOVE_Walking
        self.player_actor.RootComponent.RelativeTransform.Location = pos

    def hero_actors(self) -> list:
        return [self.player_actor, self.habitat_actor, self.erisaid_actor, self.ground_actor]

    def _on_gesture(self, ev: FGestureEvent) -> None:
        """~ UGestureProtocolComponent: gesture in, gesture out, no words
        (Design Law 3). From-player offers/refusals resolve against the
        target dot's need; from-dot gestures surface as an accessibility
        glyph. Works against BOTH representations — ADotCharacter (LOD
        High) or a bare Mass fragment (looked up by identity)."""
        if ev.From is not self.player_actor:
            self.ui.glyph_strip.Push(ev.Gesture)
            return
        dot = ev.To
        if not isinstance(dot, ADotCharacter):
            return
        need = dot.BlackboardComponent.GetValueAsObject("Need")
        if need is None:
            return
        if ev.Gesture == "refuse":
            if not dot.BlackboardComponent.GetValueAsBool("CanPay"):
                self.refused_unpayable_count += 1
                self.ui.glyph_strip.Push("grieve")
            dot.BlackboardComponent.SetValueAsObject("Need", None)
            return
        if ev.Gesture != "offer":
            return
        can_pay = dot.BlackboardComponent.GetValueAsBool("CanPay")
        wanted = NEED_FULFILLMENT[need]
        carry = self.player_actor.FindComponentByClass(UCarryComponent)
        if wanted is None:
            if need == "burial":
                self.shovel_durability -= 6 * DIG["durability_per_scoop"]
                self.record_sacrifice("BURIED_STRANGER", f"dug a grave for {dot.MassEntity}'s burden")
            else:
                self.record_sacrifice("TOOK_RISK_FOR_OTHER", f"walked {dot.MassEntity} home before night")
            dot.Memory["helped_by_generation"] = self.generation
            dot.BlackboardComponent.SetValueAsObject("Need", None)
            self.ui.glyph_strip.Push("thank")
            return
        item = carry.Hands if (carry.Hands and carry.Hands.Kind == wanted) else None
        if item is None:
            item = next((i for i in carry.Pack if i.Kind == wanted), None)
            if item:
                carry.Pack.remove(item)
        else:
            carry.Hands = None
        if item is None:
            self.ui.glyph_strip.Push("refuse")
            return
        dot.Memory["helped_by_generation"] = self.generation
        dot.BlackboardComponent.SetValueAsObject("Need", None)
        if can_pay:
            self.credits += ITEM_TABLE[item.Kind].base_price * 1.2
        else:
            self.record_sacrifice("GAVE_CARGO", f"gave {item.Kind} to one who could not pay")
        self.ui.glyph_strip.Push("thank")

    # -- the master Tick, ETickingGroup order --------------------------------
    def tick(self, dt: float, raw_input: dict) -> None:
        self.now_s += dt
        # TG_PrePhysics: input -> move data -> AI think
        move = self.controller.BuildMoveData(raw_input, self.now_s, dt)
        actorized = list(self.mass_actor_spawner.actorized.values())
        self.ai_system.TickActors(self, actorized, self.navsys, dt)
        # TG_DuringPhysics: server authority + client prediction, same solver
        suit = self.player_actor.AbilitySystemComponent.AttributeSet
        carry = self.player_actor.FindComponentByClass(UCarryComponent)
        mass_kg = (ITEM_TABLE[carry.Hands.Kind].mass_kg if carry.Hands else 0.0) + sum(
            ITEM_TABLE[i.Kind].mass_kg for i in carry.Pack)
        clog_pen = 1.0 - SUIT["dust_clog_move_penalty"] * (suit.DustClog.CurrentValue / 100.0)
        speed_scale = clog_pen * (1.0 - 0.35 * clamp(mass_kg / 30.0, 0, 1))
        self.net_authority.SpeedScale = speed_scale
        self.up_conn.SendBunch(self.now_s, "move", move)
        arrived_moves = [b[2] for b in self.up_conn.ReceiveReadyBunches(self.now_s) if b[1] == "move"]
        self.net_authority.ServerMove_Implementation(arrived_moves)
        snap = self.net_authority.TickSnapshot(dt)
        if snap:
            self.down_conn.SendBunch(self.now_s, "snapshot", snap)
        gz = self.gravity.GravityAt(self.net_client.PredictedState.Location, dt)
        self.net_client.GetNewMove(move, self.ground_actor, gz, speed_scale)
        for b in self.down_conn.ReceiveReadyBunches(self.now_s):
            if b[1] == "snapshot":
                ts, authoritative = b[2]
                self.net_client.ClientHandleMoveResponse(ts, authoritative, self.ground_actor, gz, speed_scale)
        tr = self.player_actor.RootComponent.GetComponentTransform()
        tr.Location = self.net_client.PredictedState.Location
        tr.Rotation = FQuat.MakeFromAxisAngle(FVector_Up, self.player_actor.Yaw)
        # TG_PostPhysics: camera first (the listener needs to know where it
        # is before anything gets spatialized against it), then footsteps
        # -> audio+FX+prints, then anim.
        drop = 0.55 if self.net_client.PredictedState.Gait == Gait.BEND else 0.0
        self.camera.Eye = tr.Location + FVector(0, 0, 1.62 - drop)
        self.camera.Yaw, self.camera.Pitch = self.player_actor.Yaw, 0.0
        fov_target = 101.0 if self.net_client.PredictedState.Gait == Gait.SPRINT else 92.0
        self.camera.FOV, self.camera._fov_v = critically_damped_smoothing(
            self.camera.FOV, self.camera._fov_v, fov_target, 0.25, dt)
        self.camera.BobZ, self.camera._bob_v = critically_damped_smoothing(
            self.camera.BobZ, self.camera._bob_v, 0.0, 0.18, dt)
        self.player_actor.SandSoundComponent.Tick(self)
        for kind, loc, surface, left, speed, t in self.net_authority.FootstepOutbox:
            ev = FFootstepEvent(self.player_actor, loc, self.player_actor.Yaw, surface, left, speed, t,
                                bLanding=(kind == "land"))
            self.event_bus.OnFootstep.Broadcast(ev)
            self._on_ground_reaction(ev)
        self.net_authority.FootstepOutbox.clear()
        self.player_actor.SkeletalMeshComponent.AnimInstance.NativeUpdateAnimation(
            dt, self.net_client.PredictedState, tr.Location)
        # verb activations (Enhanced Input booleans -> GAS abilities)
        asc = self.player_actor.AbilitySystemComponent
        if self.controller.InputSubsystem.GetActionValue("IA_Dig"):
            asc.TryActivateAbilityByName("Dig", self)
        if self.controller.InputSubsystem.GetActionValue("IA_Scan"):
            asc.TryActivateAbilityByName("Scan", self)
        if self.controller.InputSubsystem.GetActionValue("IA_PickUp"):
            asc.TryActivateAbilityByName("PickupDrop", self)
        weapon_drawn = "IA_DrawWeapon" in self.controller.InputSubsystem.values
        if weapon_drawn:
            self.player_actor.Tags.AddTag("State.WeaponDrawn")
        else:
            self.player_actor.Tags.RemoveTag("State.WeaponDrawn")
        if weapon_drawn and self.controller.InputSubsystem.GetActionValue("IA_Fire"):
            asc.TryActivateAbilityByName("Fire", self)
        self.attunement.dial_hz = 20.0 + self.controller.InputSubsystem.PeekAxis("IA_AttuneDial").X * 60.0
        # TG_PostUpdateWork: world/weather/economy/director/audio/UI
        hours = dt / 3600.0
        self.sun_actor.Tick(hours)
        self.weather.TickWeather(self, dt)
        self.habitat_actor.TickLifeSupport(self)
        for st in self.stations:
            if self.rng.random() < dt / 60.0:
                st.Drift(self.rng)
        self.director.TickDirector(self, dt)
        self.mass_subsystem.Tick(dt)
        self.mass_actor_spawner.SyncActorization(self)
        self.world_partition.Tick(dt)
        self.repgraph.RebuildFrame(
            [a for a in self.mass_actor_spawner.actorized.values()] + [self.player_actor], self.player_actor)
        self.repgraph.ReplicateForConnection(self.player_actor)
        asc.TickPeriodicEffects(dt)
        drain_ge = ({Gait.IDLE: GE_O2Drain_Idle, Gait.WALK: GE_O2Drain_Walk, Gait.JOG: GE_O2Drain_Walk,
                    Gait.BEND: GE_O2Drain_Walk, Gait.SPRINT: GE_O2Drain_Sprint}[self.net_client.PredictedState.Gait])
        for ge in (GE_O2Drain_Idle, GE_O2Drain_Walk, GE_O2Drain_Sprint):
            (asc.ApplyGameplayEffectToSelf if ge is drain_ge else asc.RemoveActiveGameplayEffect)(ge)
        if self.sun_actor.IsNight() and not self.player_indoors:
            asc.ApplyGameplayEffectToSelf(GE_BatteryDrain_Night)
        else:
            asc.RemoveActiveGameplayEffect(GE_BatteryDrain_Night)
        if suit.O2.CurrentValue <= 0.0:
            self.event_bus.OnDeath.Broadcast(FDeathEvent(self.player_actor, "suffocation"))
        elif (suit.Battery.CurrentValue <= 0.0
              and suit.Temperature.CurrentValue < SUIT["thermal_safe_lo"]):
            self.event_bus.OnDeath.Broadcast(FDeathEvent(self.player_actor, "cold at night"))
        self.attunement.Tick(self, dt)
        self.audio_device.Tick(dt)
        self.niagara.Tick(dt, self.weather.WindVector())
        gi_accum = getattr(self, "_gi_accum", 999.0) + dt
        if gi_accum > 120.0:
            gi_accum = 0.0
            mem_light = self.memorial.NightLightLevel() if self.sun_actor.IsNight() else 0.0
            self.renderer.gi.bake_region(self.camera.Eye, 64.0, self.sun_actor.SunElevationDeg(),
                                         0.35, mem_light, self.renderer.post)
        self._gi_accum = gi_accum
        self.renderer.Tick(self, dt)
        self.ui.Tick(self, dt)

    def _on_ground_reaction(self, ev: FFootstepEvent) -> None:
        traction, makes_print, dust_scale, _synth = SURFACE_TABLE[ev.Surface]
        if makes_print:
            self.footprints.append((ev.Location, ev.Yaw, ev.Surface, ev.bLeftFoot, self.generation))
            if len(self.footprints) > 4096:
                self.footprints.pop(0)
        if dust_scale > 0.0:
            self.niagara.SpawnSystemAtLocation(
                "NS_DustPuff", ev.Location, dust_scale * clamp(ev.Speed / MOVE["sprint_speed"], 0.2, 1.0))
        if ACCESSIBILITY["audio_muted_visual_pulses"]:
            self.niagara.SpawnSystemAtLocation("NS_FootstepRing", ev.Location, 1.0)


class TitanRunTrack:
    """2.4km of alternating gravity corridors, registered as APhysicsVolumes.
    ~ ATitanRunTrack + a spline; gravity changes LERP (never snap — body
    readability, UGravityVolumeSubsystem enforces the 1.2s ramp)."""
    LENGTH, ZONES = 2400.0, 7

    def __init__(self, world: "UWorld", start: FVector, gravity: UGravityVolumeSubsystem):
        zone_len = self.LENGTH / self.ZONES
        for i in range(self.ZONES):
            if i % 2 == 1:
                x0 = start.X + i * zone_len
                gravity.RegisterVolume(APhysicsVolume(
                    world, lambda p, x0=x0, x1=x0 + zone_len, y=start.Y:
                        x0 <= p.X <= x1 and abs(p.Y - y) < 40.0, GRAVITY_TITAN_ZONE))


# --- §11b. THE PROOF: two lives through the ENTIRE stack --------------------

def _live_one_life(game: ChimeraGame, generous: bool, sim_minutes: float = 30.0, dt: float = 0.25) -> None:
    """Scripted intent fed through the REAL Enhanced Input raw-device layer
    (`raw_input` dict = what a physical controller/keyboard would produce) —
    everything downstream (modifiers, triggers, prediction, server
    authority, Mass LOD, BT, GAS, audio, rendering, replication) is the
    live machine, not a shortcut."""
    carry = game.player_actor.FindComponentByClass(UCarryComponent)
    carry.Pack = [FItem("OXYGEN_CAN"), FItem("ICE_WATER"), FItem("MACHINE_PARTS"), FItem("FUEL_CELL")]
    steps = int(sim_minutes * 60.0 / dt)
    for step in range(steps):
        needy = [d for d in game.mass_actor_spawner.actorized.values()
                if d.BlackboardComponent.GetValueAsObject("Need") is not None]
        ppos = game.player_actor.GetActorLocation()
        raw: dict = {"stick_r": FVector()}
        if needy:
            dpos = needy[0].GetActorLocation()
            d = ppos.Dist2D(dpos)
            target_yaw = math.atan2(dpos.Y - ppos.Y, dpos.X - ppos.X)
            raw["stick_r"] = FVector((target_yaw - game.player_actor.Yaw) * 0.5, 0, 0)
            raw["stick_l"] = FVector(0.65, 0, 0) if d > 6.0 else FVector()
            if (needy[0].BlackboardComponent.GetValueAsObject("FSM") == "encounter"
                    and needy[0].MassEntity not in game._responded_this_encounter):
                game._responded_this_encounter.add(needy[0].MassEntity)
                game.event_bus.OnGesture.Broadcast(
                    FGestureEvent(game.player_actor, needy[0], "offer" if generous else "refuse"))
        else:
            raw["stick_l"] = FVector(0.4, 0, 0) if (step // 240) % 2 == 0 else FVector()
        if game.rng.random() < 0.002:
            raw["lmb"] = True
        if game.rng.random() < 0.001:
            raw["q"] = True
        game.tick(dt, raw)
    game.event_bus.OnDeath.Broadcast(FDeathEvent(game.player_actor, "retired under the memorial"))


if __name__ == "__main__":
    g = ChimeraGame(seed=7)
    g.director.stranger_cadence_days = (0.004, 0.010)     # demo compression
    g.director._next_stranger_day = 0.002
    _live_one_life(g, generous=True)     # gen 1: gives to those who can't pay
    _live_one_life(g, generous=False)    # gen 2: profitable. costless.

    print("=== THE MEMORIAL ===")
    diag = g.player_actor.EndingDiagnostic
    log = g.player_actor.SacrificeLogComponent
    for rec, star in zip(g.generations.records, g.memorial.stars):
        vision = diag.Mirror(log, rec.generation)
        print(f"gen {rec.generation}: ending={rec.ending.name:14s} sacrifice={rec.sacrifice_weight:5.2f} "
              f"star={star.brightness:4.2f} twinkle={star.twinkle} "
              f"mirror={'EMPTY' if vision.empty else vision.figures}")
    print(f"night light from ancestors: {g.memorial.NightLightLevel():.3f}")

    print("=== ENGINE PROOF (the whole UE5.8-shaped stack ran) ===")
    r = g.renderer.stats
    print(f"Nanite/render: {r['frames']} frames, {r['draws']} draws, {r['culled']} culled, "
          f"{r['nanite_clusters']} Nanite clusters, {r['shadow_views']} CSM views, "
          f"{r['skeletal_draws']} skeletal draws")
    ns = g.niagara.stats
    print(f"Niagara: {ns['cpu_particles_peak']} peak CPU-sim particles, "
          f"~{ns['gpu_particles_estimated']} GPU-sim density estimate")
    print(f"MetaSound/audio: {g.player_actor.SandSoundComponent.GetFootstepSyncEventCount()} footstep events, "
          f"avg latency {g.player_actor.SandSoundComponent.GetFootstepSyncAvgLatencyMs():.1f}ms, "
          f"volume-scales-with-speed={g.player_actor.SandSoundComponent.GetVolumeScalesWithSpeed()}, "
          f"attunement locks={len(g.attunement.matched)}/3")
    print(f"GAS: SuitAttributeSet O2={g.player_actor.AbilitySystemComponent.AttributeSet.O2.CurrentValue:.1f} "
          f"active effects={len(g.player_actor.AbilitySystemComponent._active)}")
    print(f"PCG: {sum(len(v) for v in g.buried.values())} buried items authored via PCG_BuriedHistory")
    print(f"Universe: {sum(1 for b in g.universe_actor.Bodies if b.observed)}/"
          f"{len(g.universe_actor.Bodies)} bodies observed, "
          f"{len(g.universe_actor.ObservedCells)} local cells collapsed")
    wp = g.world_partition.stats
    print(f"World Partition: {wp['activated']} cell activations, {wp['unloaded']} unloads, "
          f"{len(g.world_partition.cells)} total cells")
    print(f"Mass Entity: {g.mass_subsystem.EntityManager.NumEntities()} live entities, "
          f"{len(g.mass_actor_spawner.actorized)} currently actorized (LOD High)")
    rg = g.repgraph.stats
    print(f"ReplicationGraph: {rg['actors_replicated']} actor-relevancy resolutions, "
          f"~{rg['bytes_estimate']} bytes estimated")
    print(f"Net: {g.up_conn.PacketsSent} client moves sent, {g.down_conn.PacketsSent} snapshots sent, "
          f"{g.net_client.CorrectionCount} prediction corrections")
    print(f"World: {len(g.footprints)} footprints, {sum(1 for v in g.dig_delta.values() if v < 0)} dug cells, "
          f"{len(g.director._gen_first_sent)} generations taught Law 2 before trading")

    sg = g.save_subsystem.Capture(g)
    blob = g.save_subsystem.ToBytes(sg)
    data = g.save_subsystem.FromBytes(blob)
    print(f"SaveGame: {len(blob)} bytes round-tripped OK (v{data['Version']}, gen {data['Generation']})")
