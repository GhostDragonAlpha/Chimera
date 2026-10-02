"""units.py -- dimensionally explicit quantities for the material interface.

MaterialPreset values carry units. Conversion happens only inside a registered
dimension family; anything outside is refused by name (never converted on
faith). This mirrors the repo's existing law (tools/material_contract.py,
tools/elastic_foundation/units_contract.py) at the scale this lane needs.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

# family -> {unit: factor to canonical unit of the family}
FAMILIES: dict[str, dict[str, float]] = {
    "pressure": {"Pa": 1.0, "kPa": 1e3, "MPa": 1e6, "GPa": 1e9},
    "length": {"m": 1.0, "mm": 1e-3, "um": 1e-6, "cm": 1e-2},
    "time": {"s": 1.0, "ms": 1e-3, "us": 1e-6},
    "dimensionless": {"1": 1.0},
    "temperature": {"K": 1.0, "degC": 1.0},   # degC carries an exact offset
    "energy": {"J": 1.0, "mJ": 1e-3, "kJ": 1e3},
    "power": {"W": 1.0, "mW": 1e-3, "kW": 1e3},
    "force": {"N": 1.0, "mN": 1e-3, "kN": 1e3},
    "density": {"kg/m^3": 1.0, "g/cm^3": 1e3},
    "viscosity": {"Pa*s": 1.0, "mPa*s": 1e-3},
    "damping": {"N*s/m": 1.0, "kN*s/m": 1e3},
    "thermal_conductivity": {"W/(m*K)": 1.0},
    "specific_heat": {"J/(kg*K)": 1.0},
    "thermal_expansion": {"1/K": 1.0},
    "area": {"m^2": 1.0, "mm^2": 1e-6, "cm^2": 1e-4},
    "rate": {"1/s": 1.0, "Hz": 1.0},
    "stiffness": {"N/m": 1.0, "kN/m": 1e3},
    "mass": {"kg": 1.0, "g": 1e-3},
}
_UNIT_INDEX: dict[str, tuple[str, float]] = {
    u: (fam, f) for fam, units in FAMILIES.items() for u, f in units.items()
}
DEGC_OFFSET_K = 273.15


class UnitRefusal(ValueError):
    """Named refusal at the unit boundary."""

    def __init__(self, reason: str, message: str):
        super().__init__(f"[{reason}] {message}")
        self.reason = reason
        self.message = message


class UnitReason:
    UNKNOWN_UNIT = "unknown_unit"
    DIMENSION_MISMATCH = "dimension_mismatch"
    NONFINITE = "nonfinite_quantity"


def family_of(unit: str) -> str:
    hit = _UNIT_INDEX.get(unit)
    if hit is None:
        raise UnitRefusal(
            UnitReason.UNKNOWN_UNIT,
            f"unit {unit!r} is not in the registry; add it with its dimension "
            f"family instead of converting on faith")
    return hit[0]


def canonical_unit(unit: str) -> str:
    fam = family_of(unit)
    for cand, factor in FAMILIES[fam].items():
        if factor == 1.0:
            return cand
    raise UnitRefusal("no_canonical_unit", f"family {fam!r} has no canonical unit")


def convert(value: float, unit_from: str, unit_to: str) -> float:
    if not (math.isfinite(value)):
        raise UnitRefusal(UnitReason.NONFINITE, f"value {value!r} is not finite")
    fam_from = family_of(unit_from)
    fam_to = family_of(unit_to)
    if fam_from != fam_to:
        raise UnitRefusal(
            UnitReason.DIMENSION_MISMATCH,
            f"{unit_from!r} ({fam_from}) and {unit_to!r} ({fam_to}) are different "
            f"dimensions; refusing")
    if fam_from == "temperature":
        # exact offset handling; only K <-> degC registered
        kelvin = value + (DEGC_OFFSET_K if unit_from == "degC" else 0.0)
        return kelvin - (DEGC_OFFSET_K if unit_to == "degC" else 0.0)
    return value * _UNIT_INDEX[unit_from][1] / _UNIT_INDEX[unit_to][1]


@dataclass(frozen=True)
class Quantity:
    """A value WITH its unit. The atom of every parameter and preset."""
    value: float
    unit: str

    def __post_init__(self):
        family_of(self.unit)  # raises UNKNOWN_UNIT for unregistered units
        if not math.isfinite(float(self.value)):
            raise UnitRefusal(UnitReason.NONFINITE,
                              f"quantity value {self.value!r} is not finite")

    @property
    def family(self) -> str:
        return family_of(self.unit)

    def to(self, unit: str) -> "Quantity":
        return Quantity(convert(self.value, self.unit, unit), unit)

    def in_unit(self, unit: str) -> float:
        return convert(self.value, self.unit, unit)

    def canonical(self) -> "Quantity":
        return self.to(canonical_unit(self.unit))

    def __str__(self):
        return f"{self.value!r} {self.unit}"
