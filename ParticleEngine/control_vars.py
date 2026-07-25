"""
Control Variable DSL — the interface between Chimera's dialectical design
engine and the particle simulation.

Control variables are named, typed, bounded parameters that kernels read.
They are the "dials" that the Council, beat scripts, and emergent workflows
can tune to observe system behavior.

Design principles:
  - Every variable has a name, type, bounds, and default.
  - Variables are registered in a VarRegistry (singleton per simulation).
  - Beat scripts mutate variables via the registry.
  - The dialectical design engine (Council Q&A → Bridge → Workshop) can
    auto-discover variables and their valid ranges.
"""

from dataclasses import dataclass, field
from typing import Any
import json


@dataclass
class ControlVariable:
    """A named, bounded parameter that kernels can read."""
    name: str
    type: str            # "float", "vec3", "bool", "int"
    default: Any
    min_val: Any = None   # optional bounds
    max_val: Any = None
    description: str = ""
    tags: list[str] = field(default_factory=list)  # e.g. ["physics", "visual", "emergent"]

    def clamp(self, value):
        """Clamp value to bounds if bounds are set."""
        if self.type in ("float", "int"):
            if self.min_val is not None:
                value = max(self.min_val, value)
            if self.max_val is not None:
                value = min(self.max_val, value)
        elif self.type == "vec3":
            if isinstance(value, (list, tuple)):
                value = tuple(
                    max(self.min_val[i], min(self.max_val[i], value[i]))
                    if self.min_val and self.max_val and i < len(value)
                    else value[i]
                    for i in range(3)
                )
        return value

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "default": self.default if not isinstance(self.default, tuple) else list(self.default),
            "min": self.min_val if not isinstance(self.min_val, tuple) else list(self.min_val) if self.min_val else None,
            "max": self.max_val if not isinstance(self.max_val, tuple) else list(self.max_val) if self.max_val else None,
            "description": self.description,
            "tags": self.tags,
        }


class VarRegistry:
    """
    Central registry of all control variables for a simulation.

    Usage:
        reg = VarRegistry()
        reg.register("gravity", "vec3", (0, 0, -981), (-2000,-2000,-2000), (2000,2000,0), "Gravity vector (cm/s²)")
        reg.set("gravity", (0, 0, -162))   # Moon gravity
        cvars = reg.snapshot()             # Pass to sim.step(dt, cvars)
    """

    def __init__(self):
        self._vars: dict[str, ControlVariable] = {}
        self._values: dict[str, Any] = {}

    def register(
        self,
        name: str,
        var_type: str,
        default: Any,
        min_val: Any = None,
        max_val: Any = None,
        description: str = "",
        tags: list[str] | None = None,
    ):
        cv = ControlVariable(
            name=name,
            type=var_type,
            default=default,
            min_val=min_val,
            max_val=max_val,
            description=description,
            tags=tags or [],
        )
        self._vars[name] = cv
        self._values[name] = default

    def set(self, name: str, value: Any) -> bool:
        """Set a control variable. Returns False if unknown name."""
        if name not in self._vars:
            return False
        self._values[name] = self._vars[name].clamp(value)
        return True

    def get(self, name: str) -> Any:
        """Get current value, or None if unknown."""
        return self._values.get(name)

    def snapshot(self) -> dict[str, Any]:
        """Return a dict of all current values (pass to sim.step())."""
        return dict(self._values)

    def list_variables(self) -> list[dict]:
        """Export all registered variables (for Council/discovery)."""
        return [self._vars[name].to_dict() for name in sorted(self._vars)]

    def to_json(self) -> str:
        """Serialise the entire registry for persistence."""
        return json.dumps(
            {
                "variables": self.list_variables(),
                "current_values": {k: v if not isinstance(v, tuple) else list(v)
                                   for k, v in self._values.items()},
            },
            indent=2,
        )

    def from_dict(self, d: dict):
        """Restore from a serialised dict."""
        for var_data in d.get("variables", []):
            cv = ControlVariable(**{k: v for k, v in var_data.items() if k in ControlVariable.__dataclass_fields__})
            self._vars[cv.name] = cv
        for k, v in d.get("current_values", {}).items():
            if k in self._vars:
                self._values[k] = v

    def __len__(self):
        return len(self._vars)

    def __contains__(self, name: str) -> bool:
        return name in self._vars


# ── Default registry for physics simulation ─────────────────────

def default_physics_registry() -> VarRegistry:
    """Create a VarRegistry pre-populated with standard physics variables."""
    r = VarRegistry()

    # Gravity
    r.register("gravity", "vec3", (0.0, 0.0, -981.0),
               (-5000, -5000, -5000), (5000, 5000, 5000),
               "Gravity vector (cm/s²). Earth = (0,0,-981). Moon = (0,0,-162).",
               tags=["physics"])

    # Wind
    r.register("wind_vector", "vec3", (0.0, 0.0, 0.0),
               (-10000, -10000, -10000), (10000, 10000, 10000),
               "Wind force direction and magnitude (cm/s²).",
               tags=["physics", "environment"])
    r.register("wind_strength", "float", 1.0, 0.0, 10.0,
               "Multiplier on wind force.",
               tags=["physics", "environment"])

    # Ground collision
    r.register("ground_level", "float", 0.0, -10000.0, 100000.0,
               "Z-coordinate of the ground plane.",
               tags=["physics", "collision"])
    r.register("restitution", "float", 0.3, 0.0, 1.0,
               "Bounce restitution (0=stick, 1=perfect bounce).",
               tags=["physics", "collision"])
    r.register("friction", "float", 0.5, 0.0, 1.0,
               "Horizontal friction on ground contact.",
               tags=["physics", "collision"])

    # Boundaries
    r.register("boundary_min", "vec3", (-10000.0, -10000.0, -1000.0),
               None, None,
               "Minimum world boundary for particles.",
               tags=["physics", "boundary"])
    r.register("boundary_max", "vec3", (10000.0, 10000.0, 10000.0),
               None, None,
               "Maximum world boundary for particles.",
               tags=["physics", "boundary"])
    r.register("boundary_restitution", "float", 0.3, 0.0, 1.0,
               "Restitution at boundaries.",
               tags=["physics", "boundary"])

    # Accumulation / surface settling
    r.register("accumulation_threshold", "float", 5.0, 0.0, 100.0,
               "Max speed for a particle to be considered 'settled' (cm/s).",
               tags=["physics", "visual", "emergent"])
    r.register("accumulation_rate", "float", 0.05, 0.0, 1.0,
               "Rate at which settled particles accumulate per second.",
               tags=["physics", "visual", "emergent"])

    # Temperature
    r.register("ambient_temperature", "float", 20.0, -273.0, 10000.0,
               "Ambient temperature particles drift toward (℃/arbitrary).",
               tags=["physics", "environment"])
    r.register("cooling_rate", "float", 0.5, 0.0, 10.0,
               "Rate of temperature equalisation.",
               tags=["physics"])

    return r
