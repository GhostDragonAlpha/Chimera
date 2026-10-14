"""controls.py -- control surface GENERATED from parameter metadata.

There is no hand-maintained slider table anywhere in this lane. A control
exists because a ParameterMeta exists; its kind, range, unit and default are
derived from that metadata. verify_controls() is the consistency self-test:
every parameter in metadata has exactly one generated control, and every
control traces back to metadata with matching unit/range/default/kind.
"""
from __future__ import annotations

from dataclasses import dataclass

from .model import MaterialModel


class ControlConsistencyRefusal(ValueError):
    def __init__(self, reason: str, message: str):
        super().__init__(f"[{reason}] {message}")
        self.reason = reason
        self.message = message


class ControlReason:
    MISSING_CONTROL = "parameter_without_control"
    ORPHAN_CONTROL = "control_without_parameter"
    DUPLICATE_CONTROL = "duplicate_control"
    RANGE_MISMATCH = "control_range_mismatch"
    UNIT_MISMATCH = "control_unit_mismatch"
    DEFAULT_MISMATCH = "control_default_mismatch"
    KIND_MISMATCH = "control_kind_mismatch"


@dataclass(frozen=True)
class Control:
    """One GENERATED control. `name` is the trace key back to metadata."""
    name: str
    family: str
    kind: str                 # "log_slider" | "linear_slider" (derived from metadata)
    unit: str
    lo: float
    hi: float
    default: float
    source_model_id: str
    source_description: str


def _kind_for(scale: str) -> str:
    return {"log": "log_slider", "linear": "linear_slider"}[scale]


def generate_controls(model: MaterialModel) -> tuple[Control, ...]:
    """Generate the control surface from parameter metadata ONLY."""
    controls = []
    for meta in model.parameters:
        controls.append(Control(
            name=meta.name,
            family=meta.family,
            kind=_kind_for(meta.scale),
            unit=meta.unit,
            lo=meta.lo,
            hi=meta.hi,
            default=meta.default,
            source_model_id=model.model_id,
            source_description=meta.description,
        ))
    return tuple(controls)


def verify_controls(model: MaterialModel, controls) -> None:
    """Consistency self-test: bijection parameter <-> control, values traced."""
    meta_by_name = {m.name: m for m in model.parameters}
    seen = {}
    for control in controls:
        if control.name in seen:
            raise ControlConsistencyRefusal(
                ControlReason.DUPLICATE_CONTROL,
                f"two controls claim parameter {control.name!r}")
        seen[control.name] = control
        meta = meta_by_name.get(control.name)
        if meta is None:
            raise ControlConsistencyRefusal(
                ControlReason.ORPHAN_CONTROL,
                f"control {control.name!r} traces to no parameter of "
                f"{model.model_id!r}: no hand-maintained controls")
        if control.source_model_id != model.model_id:
            raise ControlConsistencyRefusal(
                ControlReason.ORPHAN_CONTROL,
                f"control {control.name!r} names source model "
                f"{control.source_model_id!r}, not {model.model_id!r}")
        if control.kind != _kind_for(meta.scale):
            raise ControlConsistencyRefusal(
                ControlReason.KIND_MISMATCH,
                f"control {control.name!r}: kind {control.kind!r} does not match "
                f"metadata scale {meta.scale!r}")
        if (control.unit != meta.unit or control.lo != meta.lo
                or control.hi != meta.hi):
            raise ControlConsistencyRefusal(
                ControlReason.RANGE_MISMATCH if control.unit == meta.unit
                else ControlReason.UNIT_MISMATCH,
                f"control {control.name!r}: unit/range "
                f"({control.lo!r}..{control.hi!r} {control.unit}) does not match "
                f"metadata ({meta.lo!r}..{meta.hi!r} {meta.unit})")
        if control.default != meta.default:
            raise ControlConsistencyRefusal(
                ControlReason.DEFAULT_MISMATCH,
                f"control {control.name!r}: default {control.default!r} does not "
                f"match metadata default {meta.default!r}")
    missing = sorted(set(meta_by_name) - set(seen))
    if missing:
        raise ControlConsistencyRefusal(
            ControlReason.MISSING_CONTROL,
            f"parameters {missing} of {model.model_id!r} have no generated "
            f"control")


def self_test(model: MaterialModel) -> dict:
    """Generate + verify; return a summary suitable for test receipts."""
    controls = generate_controls(model)
    verify_controls(model, controls)
    return {
        "model_id": model.model_id,
        "parameters": len(model.parameters),
        "controls_generated": len(controls),
        "families": list(model.families),
        "consistent": True,
    }
