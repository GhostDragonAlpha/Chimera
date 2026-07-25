"""
Chimera world configuration — spawn zones, attractors, physics params.

Defines the initial state of a Chimera world: where particles spawn,
what forces govern them, and what emergent behaviors are possible.
"""

import numpy as np
from dataclasses import dataclass, field


@dataclass
class Attractor:
    """A point in space that attracts certain particle types."""
    position: tuple[float, float, float]
    type_affinity: dict[str, float]  # type_name -> attraction strength
    radius: float = 500.0
    label: str = ""

    @property
    def pos(self) -> np.ndarray:
        return np.array(self.position, dtype=np.float32)


@dataclass
class SpawnZone:
    """Region where particles of a given type spawn."""
    type_name: str
    center: tuple[float, float, float]
    spread: float
    count: int
    mass: float = 0.01
    life: float = -1.0
    color: tuple[float, float, float, float] = (1, 1, 1, 1)
    size: float = 0.5


@dataclass
class WorldConfig:
    """Complete Chimera world definition."""
    name: str
    boundary_min: tuple = (-5000, -5000, -1000)
    boundary_max: tuple = (5000, 5000, 5000)
    gravity: tuple = (0, 0, -981)
    ambient_wind: tuple = (10, 5, 2)
    ambient_temperature: float = 20.0
    attractors: list[Attractor] = field(default_factory=list)
    spawn_zones: list[SpawnZone] = field(default_factory=list)
    cvars: dict = field(default_factory=dict)

    def to_sim(self, simulator, registry):
        """Configure a ParticleSimulator + VarRegistry from this world."""
        reg = registry
        reg.set("gravity", self.gravity)
        reg.set("wind_vector", self.ambient_wind)
        reg.set("ambient_temperature", self.ambient_temperature)
        reg.set("boundary_min", self.boundary_min)
        reg.set("boundary_max", self.boundary_max)

        for sz in self.spawn_zones:
            simulator.spawn(
                sz.count, sz.type_name, sz.center, sz.spread,
                mass=sz.mass, life=sz.life, color=sz.color, size=sz.size,
            )


def chimera_survival_world() -> WorldConfig:
    """Default Chimera world: dust, sand, atmosphere, social NPCs, trade resources."""
    return WorldConfig(
        name="Chimera Survival",
        gravity=(0, 0, -300),
        ambient_wind=(15, 8, 3),
        ambient_temperature=18.0,
        boundary_min=(-5000, -5000, -500),
        boundary_max=(5000, 5000, 5000),
        cvars={
            "wind_strength": 0.3,
            "boundary_restitution": 0.4,
            "accumulation_threshold": 5.0,
            "accumulation_rate": 0.05,
            "surface_roughness": 0.1,
        },
        spawn_zones=[
            SpawnZone("dust", (-400, -200, 400), 400, 8000,
                      mass=0.005, color=(0.75, 0.68, 0.55, 0.7), size=0.5),
            SpawnZone("sand", (200, 100, 500), 350, 5000,
                      mass=0.02, color=(0.9, 0.72, 0.35, 0.85), size=0.35),
            SpawnZone("atmosphere", (0, 0, 2000), 1500, 3000,
                      mass=0.001, color=(0.5, 0.6, 0.85, 0.06), size=15.0),
            SpawnZone("social", (0, 0, 300), 500, 500,
                      mass=0.1, color=(0.3, 0.9, 0.3, 0.7), size=1.0),
            SpawnZone("resource", (-300, 200, 400), 300, 300,
                      mass=0.08, color=(0.9, 0.8, 0.2, 0.8), size=0.8),
        ],
        attractors=[
            Attractor((0, 0, 100), {"social": 500.0, "resource": 300.0},
                      radius=800, label="habitat_center"),
            Attractor((1000, 500, 50), {"resource": 200.0},
                      radius=400, label="trade_post_alpha"),
            Attractor((-800, 300, 80), {"social": 300.0},
                      radius=500, label="npc_village"),
        ],
    )
