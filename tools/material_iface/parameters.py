"""parameters.py -- parameter metadata and validated parameter sets.

ParameterMeta is the single source of truth for controls: the control surface
is GENERATED from this metadata (controls.py), never hand-maintained.
ParameterSet binds a MaterialModel's metadata to actual unit-tagged values and
validates every value against its metadata.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math

from .units import Quantity, UnitRefusal, convert, family_of


CONTROL_FAMILIES = (
    "elasticity", "compression", "shear", "bending", "viscosity",
    "relaxation", "yielding", "thermal",
)


class ParameterRefusal(ValueError):
    def __init__(self, reason: str, message: str):
        super().__init__(f"[{reason}] {message}")
        self.reason = reason
        self.message = message


class ParameterReason:
    UNKNOWN_FAMILY = "unknown_control_family"
    UNKNOWN_UNIT = "unknown_unit"
    BAD_RANGE = "bad_parameter_range"
    RANGE_VIOLATION = "parameter_out_of_range"
    UNKNOWN_PARAMETER = "unknown_parameter"
    MISSING_PARAMETER = "missing_parameter"
    DUPLICATE = "duplicate_parameter"
    UNIT_MISMATCH = "parameter_unit_mismatch"
    NONFINITE = "nonfinite_parameter"
    BAD_SCALE = "bad_scale_kind"


SCALES = ("log", "linear")


@dataclass(frozen=True)
class ParameterMeta:
    """Declarative metadata for ONE adjustable parameter of a MaterialModel."""
    name: str
    unit: str
    family: str              # one of CONTROL_FAMILIES
    description: str
    lo: float                # bounds in `unit`
    hi: float
    default: float           # in `unit`
    scale: str = "log"       # "log" (decades spanning) or "linear"

    def __post_init__(self):
        if self.family not in CONTROL_FAMILIES:
            raise ParameterRefusal(
                ParameterReason.UNKNOWN_FAMILY,
                f"parameter {self.name!r} family {self.family!r} is not one of "
                f"{CONTROL_FAMILIES}")
        try:
            family_of(self.unit)
        except UnitRefusal as exc:
            raise ParameterRefusal(ParameterReason.UNKNOWN_UNIT,
                                   f"parameter {self.name!r}: {exc.message}") from None
        vals = (self.lo, self.hi, self.default)
        if not all(math.isfinite(v) for v in vals):
            raise ParameterRefusal(ParameterReason.NONFINITE,
                                   f"parameter {self.name!r}: bounds must be finite")
        if not (self.lo <= self.default <= self.hi):
            raise ParameterRefusal(
                ParameterReason.BAD_RANGE,
                f"parameter {self.name!r}: default {self.default!r} outside "
                f"[{self.lo!r}, {self.hi!r}] {self.unit}")
        if self.scale not in SCALES:
            raise ParameterRefusal(ParameterReason.BAD_SCALE,
                                   f"parameter {self.name!r}: scale {self.scale!r}")
        if self.scale == "log" and not (self.lo > 0.0):
            raise ParameterRefusal(
                ParameterReason.BAD_RANGE,
                f"parameter {self.name!r}: log-scale parameters need lo > 0")

    def accept(self, quantity: Quantity) -> float:
        """Validate a unit-tagged value against this metadata; return the value
        converted into the metadata's declared unit."""
        try:
            value = quantity.in_unit(self.unit)
        except UnitRefusal as exc:
            raise ParameterRefusal(
                ParameterReason.UNIT_MISMATCH,
                f"parameter {self.name!r} expects dimension "
                f"{family_of(self.unit)!r}: {exc.message}") from None
        if not (self.lo <= value <= self.hi):
            raise ParameterRefusal(
                ParameterReason.RANGE_VIOLATION,
                f"parameter {self.name!r}: {quantity} -> {value!r} {self.unit} "
                f"outside declared validity [{self.lo!r}, {self.hi!r}]")
        return value


@dataclass(frozen=True)
class ParameterSet:
    """Values for exactly one model's parameter metadata, units attached."""
    model_id: str
    values: dict[str, Quantity] = field(default_factory=dict)

    def __post_init__(self):
        seen = set()
        for name in self.values:
            if name in seen:
                raise ParameterRefusal(ParameterReason.DUPLICATE,
                                       f"duplicate parameter {name!r}")
            seen.add(name)

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self.values))

    def quantity(self, name: str) -> Quantity:
        try:
            return self.values[name]
        except KeyError:
            raise ParameterRefusal(
                ParameterReason.UNKNOWN_PARAMETER,
                f"parameter set for {self.model_id!r} has no {name!r}") from None

    def value(self, name: str, unit: str | None = None) -> float:
        q = self.quantity(name)
        return q.in_unit(unit) if unit else q.value

    def canonical_signature(self) -> tuple[tuple[str, float], ...]:
        """Deterministic, hashable canonical form (used in state/ledger hashes)."""
        sig = []
        for name in sorted(self.values):
            sig.append((name, self.values[name].canonical().value))
        return tuple(sig)


def build_parameter_set(model, quantities: dict[str, Quantity]) -> ParameterSet:
    """Bind unit-tagged values to a model's metadata; validate each against it."""
    metas = {m.name: m for m in model.parameters}
    unknown = sorted(set(quantities) - set(metas))
    if unknown:
        raise ParameterRefusal(
            ParameterReason.UNKNOWN_PARAMETER,
            f"model {model.model_id!r} declares no parameter(s) {unknown}; "
            f"refusing to store orphan values")
    missing = sorted(set(metas) - set(quantities))
    if missing:
        raise ParameterRefusal(
            ParameterReason.MISSING_PARAMETER,
            f"model {model.model_id!r} parameter(s) {missing} have no value; "
            f"an undefined parameter is never silently inferred from a name")
    accepted = {}
    for name, meta in metas.items():
        accepted[name] = Quantity(meta.accept(quantities[name]), meta.unit)
    return ParameterSet(model_id=model.model_id, values=accepted)
