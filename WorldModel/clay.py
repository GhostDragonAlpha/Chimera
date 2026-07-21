"""
Moldable parameter system — clay for every game object.

Every object is defined by a parameter vector. Physics fills in the
details. The VAE learns parameter distributions, not pixel values.

Tree = 17 params → Physics → Splats → GPU Render
Ship = 24 params → Physics → Splats → GPU Render
Planet = 12 params → Physics → Splats → GPU Render
"""

import numpy as np
import math
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class ParamDef:
    """Definition of a single moldable parameter."""
    name: str
    min_val: float
    max_val: float
    default: float
    description: str = ""


class MoldableObject:
    """
    A moldable game object defined by parameters. Physics generates
    the actual geometry from parameters. VAE learns parameter distributions.
    
    Clay = parameters. Kiln = physics. Result = splats.
    """

    def __init__(self, name: str, params: list[ParamDef], generator: Callable):
        self.name = name
        self.params = {p.name: p for p in params}
        self.generator = generator  # fn(params_dict) -> SplatCloud
        self._values = {p.name: p.default for p in params}

    @property
    def dim(self) -> int:
        return len(self.params)

    def set(self, **kwargs):
        """Mold the parameters like clay."""
        for k, v in kwargs.items():
            if k in self.params:
                p = self.params[k]
                self._values[k] = max(p.min_val, min(p.max_val, v))

    def randomize(self):
        """Random mold within valid ranges."""
        for name, p in self.params.items():
            self._values[name] = np.random.uniform(p.min_val, p.max_val)

    def vectorize(self) -> np.ndarray:
        """Convert current parameter values to a training vector."""
        return np.array([self._values[name] for name in self.params], dtype=np.float32)

    def from_vector(self, vec: np.ndarray):
        """Set parameters from a VAE-generated vector."""
        for i, name in enumerate(self.params):
            if i < len(vec):
                self.set(**{name: float(vec[i])})

    def generate(self):
        """Run physics generator with current parameters. Returns SplatCloud."""
        return self.generator(dict(self._values))

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "dim": self.dim,
            "params": [
                {"name": p.name, "min": p.min_val, "max": p.max_val, "default": self._values[p.name]}
                for p in self.params.values()
            ],
        }


# ═══════════════════════════════════════════════════════════════════
#  Tree clay — 17 moldable parameters
# ═══════════════════════════════════════════════════════════════════

TREE_PARAMS = [
    ParamDef("trunk_height",     150,  500,  280,  "Total trunk height"),
    ParamDef("trunk_radius",     6,    22,   12,   "Trunk radius at base"),
    ParamDef("trunk_gnarl",      0.02, 0.35, 0.15, "How twisted the trunk is"),
    ParamDef("num_branches",     3,    7,    4,    "Number of main branches"),
    ParamDef("branch_length",    60,   200,  120,  "Length of main branches"),
    ParamDef("branch_angle_min", 0.2,  0.8,  0.4,  "Minimum branch angle (rad)"),
    ParamDef("branch_angle_max", 0.5,  1.5,  0.9,  "Maximum branch angle (rad)"),
    ParamDef("branch_spread",    0.2,  0.9,  0.5,  "Horizontal spread of branches"),
    ParamDef("branch_depth",     2,    5,    3,    "Recursion depth of branching"),
    ParamDef("branch_taper",     0.3,  0.8,  0.55, "How fast branches thin out"),
    ParamDef("leaf_density",     10,   80,   30,   "Number of leaf clusters"),
    ParamDef("leaf_size_min",    1.5,  6.0,  3.0,  "Minimum leaf size"),
    ParamDef("leaf_size_max",    4.0,  15.0, 8.0,  "Maximum leaf size"),
    ParamDef("canopy_roundness", 0.3,  1.0,  0.7,  "How round the canopy is"),
    ParamDef("root_spread",      0.2,  1.0,  0.5,  "How far roots spread"),
    ParamDef("wind_response",    0.0,  0.5,  0.1,  "Asymmetry from prevailing wind"),
    ParamDef("light_seeking",    0.3,  1.0,  0.7,  "Strength of phototropism"),
]


def tree_generator(params: dict) -> "SplatCloud":
    """Physics tree generator from moldable parameters."""
    from WorldModel.physics_tree import grow_tree, segments_to_splats

    segs = grow_tree(
        trunk_height=params["trunk_height"],
        trunk_radius=params["trunk_radius"],
        max_depth=int(params["branch_depth"]),
        seed=int(np.random.randint(0, 2**31)),
    )
    data = segments_to_splats(segs, target_count=4096)

    from WorldModel.splat_io import SplatCloud
    return SplatCloud(
        positions=data["positions"].astype(np.float32),
        colors=data["colors"].astype(np.float32),
        opacities=data["opacities"].astype(np.float32),
        scales=data["scales"].astype(np.float32),
        rotations=data["rotations"].astype(np.float32),
    )


# ═══════════════════════════════════════════════════════════════════
#  Spaceship clay — 24 moldable parameters
# ═══════════════════════════════════════════════════════════════════

SHIP_PARAMS = [
    ParamDef("hull_length",      20,   500,  150,  "Length of main hull"),
    ParamDef("hull_width",       8,    150,  40,   "Width of main hull"),
    ParamDef("hull_height",      5,    80,   20,   "Height of main hull"),
    ParamDef("hull_taper",       0.1,  1.0,  0.4,  "How much hull tapers aft"),
    ParamDef("nose_sharpness",   0.1,  3.0,  1.5,  "Pointiness of bow"),
    ParamDef("engine_count",     1,    6,    2,    "Number of main engines"),
    ParamDef("engine_size",      3,    40,   15,   "Radius of each engine"),
    ParamDef("engine_length",    5,    60,   25,   "Length of engine nacelles"),
    ParamDef("wing_count",       0,    4,    2,    "Number of wings/fins"),
    ParamDef("wing_span",        10,   200,  80,   "Wingspan"),
    ParamDef("wing_sweep",       0.0,  1.0,  0.5,  "How swept the wings are"),
    ParamDef("bridge_position",  0.1,  0.9,  0.3,  "Bridge position along hull"),
    ParamDef("bridge_height",    1,    20,   5,    "Bridge height above hull"),
    ParamDef("hull_texture",     0.0,  1.0,  0.5,  "Panel/greeble density"),
    ParamDef("color_hue",        0.0,  1.0,  0.6,  "Base hull color hue"),
    ParamDef("color_saturation", 0.1,  0.9,  0.3,  "Color saturation"),
    ParamDef("color_value",      0.2,  0.9,  0.6,  "Color brightness"),
    ParamDef("weapon_count",     0,    8,    4,    "Number of weapon hardpoints"),
    ParamDef("radiator_size",    0,    30,   10,   "Size of heat radiators"),
    ParamDef("cargo_bay_size",   0,    0.5,  0.2,  "Cargo bay as fraction of hull"),
    ParamDef("antenna_count",    0,    10,   3,    "Number of antennas/sensors"),
    ParamDef("asymmetry",        0.0,  0.3,  0.05, "How asymmetric the design is"),
    ParamDef("age_wear",         0.0,  1.0,  0.3,  "Amount of wear and tear"),
    ParamDef("expanse_style",    0.0,  1.0,  0.8,  "How Expanse-like (vertical, utilitarian)"),
]


def ship_generator(params: dict) -> "SplatCloud":
    """Physics-based spaceship generator from moldable parameters."""
    hull_l = params["hull_length"]
    hull_w = params["hull_width"]
    hull_h = params["hull_height"]
    engine_count = int(params["engine_count"])
    weapon_count = int(params["weapon_count"])
    wing_count = int(params["wing_count"])

    positions = []
    colors = []

    # Hull: elongated box with taper
    n_hull = 2000
    for i in range(n_hull):
        t = i / (n_hull - 1)
        x = (t - 0.5) * hull_l
        r_w = hull_w * (1 - t * params["hull_taper"])
        r_h = hull_h * (1 - t * params["hull_taper"])
        # Nose sharpness at front
        if t > 0.8:
            nose_t = (t - 0.8) / 0.2
            r_w *= (1 - nose_t ** params["nose_sharpness"])
            r_h *= (1 - nose_t ** params["nose_sharpness"])
        ox = np.random.normal(0, r_w/3)
        oy = np.random.normal(0, r_h/3)
        oz = np.random.normal(0, r_w/3)
        positions.append([x + ox, oy, oz])
        # Expanse style: vertical orientation, gray/white hull
        gray = params["color_value"] + np.random.uniform(-0.05, 0.05)
        colors.append([gray * 0.7, gray * 0.75, gray * 0.85])

    # Engines at rear
    for e in range(engine_count):
        angle = 2 * math.pi * e / engine_count + np.random.uniform(-0.2, 0.2)
        er = params["engine_size"]
        el = params["engine_length"]
        ex = -hull_l/2 - el
        ey = math.cos(angle) * hull_h * 0.6
        ez = math.sin(angle) * hull_w * 0.6
        for i in range(500):
            t = i / 499
            px = ex + t * el
            r = er * (1 - t * 0.8)
            positions.append([px + np.random.normal(0, r/3), ey + np.random.normal(0, r/3), ez + np.random.normal(0, r/3)])
            colors.append([0.1, 0.3, 0.9])  # blue engine glow

    # Wings/fins
    for w in range(wing_count):
        angle = math.pi + 2 * math.pi * w / max(wing_count, 1)
        ws = params["wing_span"]
        sweep = params["wing_sweep"]
        for i in range(400):
            t = i / 399
            wx = -hull_l * 0.2 + sweep * hull_l * 0.3 * t
            wy = math.cos(angle) * t * ws
            wz = math.sin(angle) * t * ws
            positions.append([wx, wy + np.random.normal(0, 1), wz + np.random.normal(0, 1)])
            colors.append([gray * 0.6, gray * 0.65, gray * 0.75])

    # Bridge
    bx = -hull_l/2 + params["bridge_position"] * hull_l
    bh = params["bridge_height"]
    for i in range(200):
        t = i / 199
        by = bh * (1 - t)
        r = 3 * (1 - t)
        positions.append([bx + np.random.normal(0, r), by, np.random.normal(0, r)])
        colors.append([0.2, 0.4, 0.9])  # blue-tinted bridge windows

    pos = np.array(positions[:4096], dtype=np.float32)
    col = np.clip(np.array(colors[:4096], dtype=np.float32), 0, 1)

    from WorldModel.splat_io import SplatCloud
    return SplatCloud(
        positions=pos, colors=col,
        opacities=np.ones(len(pos), dtype=np.float32) * 0.9,
        scales=np.ones((len(pos), 3), dtype=np.float32) * 2,
        rotations=np.tile(np.array([0., 0., 0., 1.], dtype=np.float32), (len(pos), 1)),
    )


# ═══════════════════════════════════════════════════════════════════
#  Factory
# ═══════════════════════════════════════════════════════════════════

OAK_TREE = MoldableObject("Oak Tree", TREE_PARAMS, tree_generator)
EXPANSE_SHIP = MoldableObject("Expanse Ship", SHIP_PARAMS, ship_generator)

ALL_OBJECTS = {"oak": OAK_TREE, "ship": EXPANSE_SHIP}
