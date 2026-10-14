"""model.py -- MaterialModel: equations, internal-state spec, adjustable parameters.

A MaterialModel is a RECORD of what a material law IS: its constitutive
equations (usually implemented by an existing repo law named in `law_import`),
the internal state variables it owns, and the metadata of its adjustable
parameters. It holds NO numeric values -- values live in ParameterSet /
MaterialPreset records. This separation is deliberate: model identity, preset
values and state ownership are distinct concepts with distinct record types.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .parameters import ParameterMeta


class ModelRefusal(ValueError):
    def __init__(self, reason: str, message: str):
        super().__init__(f"[{reason}] {message}")
        self.reason = reason
        self.message = message


class ModelReason:
    DUPLICATE_PARAMETER = "duplicate_parameter_name"
    DUPLICATE_STATE_VAR = "duplicate_state_var"
    DECLARATION_ONLY = "declaration_only_no_equations"
    HISTORY_WITHOUT_STATE = "history_without_state"
    IMPLEMENTED_NEEDS_LAW = "implemented_model_needs_law_import"


@dataclass(frozen=True)
class StateVar:
    """One internal-state variable owned by a model's law."""
    name: str
    unit: str
    description: str


@dataclass(frozen=True)
class MaterialModel:
    model_id: str                                    # versioned identity
    equations: str                                   # declaration of the constitutive equations
    parameters: tuple[ParameterMeta, ...] = field(default=())
    state_spec: tuple[StateVar, ...] = field(default=())
    history: bool = False        # does the owner retain internal-state HISTORY
    law_import: str = ""         # dotted path of the existing repo law implementing it
    implemented: bool = False    # False => metadata-only declaration; evaluation refused
    version: int = 1

    def __post_init__(self):
        names = [m.name for m in self.parameters]
        if len(names) != len(set(names)):
            raise ModelRefusal(ModelReason.DUPLICATE_PARAMETER,
                               f"model {self.model_id!r}: duplicate parameter names")
        vars_ = [v.name for v in self.state_spec]
        if len(vars_) != len(set(vars_)):
            raise ModelRefusal(ModelReason.DUPLICATE_STATE_VAR,
                               f"model {self.model_id!r}: duplicate state variables")
        if self.history and not self.state_spec:
            raise ModelRefusal(ModelReason.HISTORY_WITHOUT_STATE,
                               f"model {self.model_id!r}: history without state vars")
        if self.implemented and not self.law_import:
            raise ModelRefusal(ModelReason.IMPLEMENTED_NEEDS_LAW,
                               f"model {self.model_id!r}: implemented=True needs "
                               f"law_import naming the existing repo law")

    def meta(self, name: str) -> ParameterMeta:
        for m in self.parameters:
            if m.name == name:
                return m
        raise ModelRefusal(
            "unknown_parameter",
            f"model {self.model_id!r} declares no parameter {name!r}")

    @property
    def families(self) -> tuple[str, ...]:
        """Distinct control families this model's metadata exposes."""
        return tuple(sorted({m.family for m in self.parameters}))

    def require_implemented(self) -> None:
        if not self.implemented:
            raise ModelRefusal(
                ModelReason.DECLARATION_ONLY,
                f"model {self.model_id!r} declares parameters/equations but no "
                f"equations are implemented in this lane (law_import={self.law_import!r}); "
                f"refusing to fabricate physics")
