"""mechanism.py -- the mechanism protocol and its SINGLE return record type.

Protocol: a mechanism DECLARES its inputs and returns a tuple of
MechanismContribution records. One record carries every protocol field:

  - the applicable stress-or-force contribution (channel, point, force, stress)
  - heat flux
  - stored energy
  - dissipation
  - a PROPOSED internal-state update (the Integrator is the only applier)
  - solver derivatives / numerical constraints

Channels separate superposable bulk force ("force", normal physics) from the
channels the campaign law forbids silently summing: "contact_force",
"stored_energy", "heat", "dissipation". Two mechanisms contributing at the
same (channel, point) in a flagged channel are DUPLICATES -- they are reported
and never summed (combination.py, integrator.py).

Contract: evaluate() receives frozen snapshots, must not mutate them, must not
touch integrator-owned state, and must be deterministic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math


CHANNELS = ("force", "contact_force", "stored_energy", "heat", "dissipation")
DUPLICATE_FLAGGED_CHANNELS = ("contact_force", "stored_energy", "heat", "dissipation")

KNOWN_INPUTS = (
    "positions",       # tuple[(x, y, z), ...] current positions, point order
    "velocities",      # tuple[(vx, vy, vz), ...]
    "time_s",          # float
    "temperature_K",   # float
    "geometry",        # Geometry record
    "presets",         # mapping model_id -> MaterialPreset
    "model_state",     # mapping model_id -> tuple[(var, value), ...]
)


class MechanismRefusal(ValueError):
    def __init__(self, reason: str, message: str):
        super().__init__(f"[{reason}] {message}")
        self.reason = reason
        self.message = message


class MechanismReason:
    UNRESOLVED_DEPENDENCY = "unresolved_dependency"
    UNKNOWN_INPUT = "unknown_input"
    BAD_RECORD = "bad_contribution_record"
    LAW_REFUSED = "law_refused"
    MODEL_MISMATCH = "mechanism_model_mismatch"


@dataclass(frozen=True)
class SolverConstraints:
    """Solver derivatives / numerical constraints declared by the mechanism."""
    analytic_force_jacobian: bool
    recommended_max_dt_s: float | None = None
    tolerance_energy_scale_j: float | None = None
    notes: str = ""


@dataclass(frozen=True)
class StateProposal:
    """A PROPOSED internal-state update. Data only: the Integrator applies it
    through its single ownership gate, or refuses it by name."""
    model_id: str
    var: str
    mode: str            # "set" | "add"
    value: float
    unit: str


@dataclass(frozen=True)
class MechanismContribution:
    """THE single return record type of the mechanism protocol."""
    mechanism_id: str
    channel: str                       # one of CHANNELS
    point: str                         # stable point key within the assembly
    force: tuple[float, float, float] | None
    stress_voigt: tuple[float, ...] | None
    heat_flux_w_per_m2: float
    stored_energy_j: float
    dissipated_power_w: float
    state_proposal: StateProposal | None
    solver: SolverConstraints | None
    applicable: bool
    inapplicable_reason: str | None = None

    def __post_init__(self):
        if self.channel not in CHANNELS:
            raise MechanismRefusal(MechanismReason.BAD_RECORD,
                                   f"channel {self.channel!r} not in {CHANNELS}")
        if not self.applicable and not (self.inapplicable_reason or "").strip():
            raise MechanismRefusal(
                MechanismReason.BAD_RECORD,
                f"record {self.mechanism_id}/{self.channel}/{self.point}: "
                f"an inapplicable contribution must carry its reason")
        for name, value in (("force", self.force), ("stress_voigt", self.stress_voigt)):
            if value is not None:
                if any(not math.isfinite(float(c)) for c in value):
                    raise MechanismRefusal(
                        MechanismReason.BAD_RECORD,
                        f"record {self.mechanism_id}/{self.channel}/{self.point}: "
                        f"{name} is non-finite")
        for name, value in (("heat_flux_w_per_m2", self.heat_flux_w_per_m2),
                            ("stored_energy_j", self.stored_energy_j),
                            ("dissipated_power_w", self.dissipated_power_w)):
            if not math.isfinite(float(value)):
                raise MechanismRefusal(
                    MechanismReason.BAD_RECORD,
                    f"record {self.mechanism_id}/{self.channel}/{self.point}: "
                    f"{name} is non-finite")
        if self.state_proposal is not None and not isinstance(self.state_proposal,
                                                              StateProposal):
            raise MechanismRefusal(MechanismReason.BAD_RECORD,
                                   "state_proposal must be a StateProposal record")
        if self.solver is not None and not isinstance(self.solver, SolverConstraints):
            raise MechanismRefusal(MechanismReason.BAD_RECORD,
                                   "solver must be a SolverConstraints record")


class Mechanism:
    """Base class. Subclasses set mechanism_id, model_id, declares and
    implement evaluate(inputs) -> tuple[MechanismContribution, ...]."""

    mechanism_id: str = ""
    model_id: str = ""
    declares: tuple[str, ...] = ()

    def __init__(self, mechanism_id: str, model_id: str,
                 declares: tuple[str, ...]):
        bad = [name for name in declares if name not in KNOWN_INPUTS]
        if bad:
            raise MechanismRefusal(
                MechanismReason.UNKNOWN_INPUT,
                f"{mechanism_id}: declares unknown input(s) {bad}; known "
                f"inputs are {KNOWN_INPUTS}")
        self.mechanism_id = mechanism_id
        self.model_id = model_id
        self.declares = tuple(declares)

    def evaluate(self, inputs) -> tuple[MechanismContribution, ...]:
        raise NotImplementedError(
            f"mechanism {self.mechanism_id!r} does not implement evaluate()")

    def require_inputs(self, inputs) -> None:
        # mapping membership is the authority
        missing = [name for name in self.declares if name not in inputs]
        if missing:
            raise MechanismRefusal(
                MechanismReason.UNRESOLVED_DEPENDENCY,
                f"{self.mechanism_id}: declared input(s) {missing} were not "
                f"provided by the assembly")
