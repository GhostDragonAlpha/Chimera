"""contact.py -- ContactModel: the PAIR-level interaction between two materials.

A ContactModel is deliberately distinct from the bulk MaterialModel records:
it is defined for an (a, b) pair of model ids, carries its own parameter
metadata, and is exercised through the same single mechanism return record.

SyntheticPenaltyContactMechanism is a DECLARED SYNTHETIC interface
demonstration (provenance "synthetic-interface-demo"): it exists so pair-level
records and duplicate detection are testable without writing a new qualified
contact law. It is not part of the qualified M-law stack.
"""
from __future__ import annotations

import math

from .mechanism import (Mechanism, MechanismContribution, MechanismRefusal,
                        SolverConstraints)
from .parameters import ParameterMeta, build_parameter_set
from .units import Quantity


class ContactModel:
    """Pair-level record: parameters for how two material models interact."""

    def __init__(self, contact_id: str, model_a: str, model_b: str,
                 metas: tuple[ParameterMeta, ...], quantities: dict[str, Quantity],
                 law: str = "", provenance: str = "undeclared"):
        if model_a == model_b:
            # same-material contact is a legal special case, but record it as such
            pair_note = "self-pair"
        else:
            pair_note = ""
        self.contact_id = contact_id
        self.pair = tuple(sorted((model_a, model_b)))
        self.pair_note = pair_note
        self.metas = metas
        self.law = law
        self.provenance = provenance
        self.values = build_parameter_set(_PairModelShim(contact_id, metas),
                                          quantities)

    def pair_key(self) -> tuple[str, str]:
        return self.pair


class _PairModelShim:
    """Minimal metadata host so ContactModel can reuse ParameterSet validation."""

    def __init__(self, contact_id: str, metas: tuple[ParameterMeta, ...]):
        self.model_id = f"contact:{contact_id}"
        self.parameters = metas


class SyntheticPenaltyContactMechanism(Mechanism):
    """Synthetic demo contact: linear penalty + damping along one direction at
    one fixed point. DECLARED SYNTHETIC -- exercises the pair-level protocol
    and duplicate detection; not a qualified contact law."""

    def __init__(self, contact: ContactModel, point: str, direction=(0.0, 0.0, -1.0),
                 penetration_m: float = 0.0):
        super().__init__(mechanism_id=f"adapter.synthetic_penalty_contact:"
                                      f"{contact.contact_id}",
                         model_id=contact.pair[0],
                         declares=("positions", "velocities"))
        self.contact = contact
        self.point = point
        d = tuple(float(c) for c in direction)
        norm = math.sqrt(sum(c * c for c in d))
        if norm <= 0.0 or not math.isfinite(norm):
            raise MechanismRefusal("bad_direction", "direction must be a nonzero vector")
        self.direction = tuple(c / norm for c in d)
        self.penetration_m = float(penetration_m)

    def evaluate(self, inputs) -> tuple[MechanismContribution, ...]:
        positions = inputs.get("positions")
        velocities = inputs.get("velocities")
        if positions is None or velocities is None:
            raise MechanismRefusal(
                "unresolved_dependency",
                f"{self.mechanism_id}: declared inputs positions/velocities missing")
        idx = _point_index(self.point, positions)
        k = self.contact.values.value("penalty_stiffness", "N/m")
        c_damp = self.contact.values.value("normal_damping", "N*s/m")
        dirn = self.direction
        pen = self.penetration_m
        vel_n = sum(velocities[idx][i] * dirn[i] for i in range(3))
        magnitude = -(k * pen + c_damp * vel_n)
        force = tuple(magnitude * dirn[i] for i in range(3))
        return (MechanismContribution(
            mechanism_id=self.mechanism_id,
            channel="contact_force",
            point=self.point,
            force=force,
            stress_voigt=None,
            heat_flux_w_per_m2=0.0,
            stored_energy_j=0.0,
            dissipated_power_w=max(0.0, -magnitude * vel_n),
            state_proposal=None,
            solver=SolverConstraints(
                analytic_force_jacobian=True,
                recommended_max_dt_s=None,
                tolerance_energy_scale_j=abs(k * pen) + 1.0,
                notes="synthetic penalty contact; damping is not energy "
                      "conservative by construction"),
            applicable=True,
            inapplicable_reason=None),)


def _point_index(point: str, positions) -> int:
    # point keys are "v<i>"/"p<i>"; index from the tail
    try:
        return int(point[1:])
    except (ValueError, IndexError):
        raise MechanismRefusal("unknown_point",
                               f"point key {point!r} is not a v<i>/p<i> key") from None
