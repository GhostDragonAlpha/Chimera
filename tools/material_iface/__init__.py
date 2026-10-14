"""tools.material_iface -- the material interface as SEPARATE concepts.

Lane: monkey-coordination/material-iface (wk-matiface).

Distinct record types, no god object:
  MaterialModel   equations + internal-state spec + adjustable-parameter
                  metadata (no numeric values; model.py)
  MaterialPreset  parameter values WITH units, provenance citation, validity
                  range; measured vs auto-declared synthetic (presets.py)
  Geometry        surface / volume / particle representation binding
                  (geometry.py)
  ContactModel    PAIR-level interaction between two materials (contact.py)
  Integrator      the SOLE authority advancing owned physical state
                  (integrator.py)

Mechanism protocol: mechanisms declare inputs and return tuples of the single
record type MechanismContribution (stress-or-force, heat flux, stored energy,
dissipation, proposed internal-state update, solver constraints).
adapter_stvk.py is the reference adapter over the EXISTING repo law
tools/elastic_foundation (STVK membrane), imported and never edited.
"""
from .units import Quantity, UnitRefusal, convert, family_of
from .parameters import (CONTROL_FAMILIES, ParameterMeta, ParameterRefusal,
                         ParameterSet, build_parameter_set)
from .model import MaterialModel, ModelRefusal, StateVar
from .presets import (CitedValue, MaterialPreset, PresetRefusal, Provenance,
                      ValidityRange, MEASURED, SYNTHETIC)
from .geometry import Geometry, GeometryRefusal, PARTICLE, SURFACE, VOLUME
from .contact import ContactModel, SyntheticPenaltyContactMechanism
from .mechanism import (CHANNELS, DUPLICATE_FLAGGED_CHANNELS, KNOWN_INPUTS,
                        Mechanism, MechanismContribution, MechanismRefusal,
                        SolverConstraints, StateProposal)
from .controls import (Control, ControlConsistencyRefusal, generate_controls,
                       self_test as controls_self_test, verify_controls)
from .combination import (Assembly, CombinationIssue, CombinationRefusal,
                          CombinationReport, CombinationValidator,
                          POLICY_FLAG, POLICY_REJECT)
from .integrator import (Integrator, IntegratorRefusal, LedgerEntry,
                         ParameterChangeRecord, Snapshot)
from .adapter_stvk import (DECLARATION_ONLY_MODEL, STVK_MODEL,
                           StvkMembraneMechanism, bind_surface_to_stvk)

__all__ = [
    "Quantity", "UnitRefusal", "convert", "family_of",
    "CONTROL_FAMILIES", "ParameterMeta", "ParameterRefusal", "ParameterSet",
    "build_parameter_set",
    "MaterialModel", "ModelRefusal", "StateVar",
    "CitedValue", "MaterialPreset", "PresetRefusal", "Provenance",
    "ValidityRange", "MEASURED", "SYNTHETIC",
    "Geometry", "GeometryRefusal", "PARTICLE", "SURFACE", "VOLUME",
    "ContactModel", "SyntheticPenaltyContactMechanism",
    "CHANNELS", "DUPLICATE_FLAGGED_CHANNELS", "KNOWN_INPUTS", "Mechanism",
    "MechanismContribution", "MechanismRefusal", "SolverConstraints",
    "StateProposal",
    "Control", "ControlConsistencyRefusal", "generate_controls",
    "controls_self_test", "verify_controls",
    "Assembly", "CombinationIssue", "CombinationRefusal",
    "CombinationReport", "CombinationValidator", "POLICY_FLAG",
    "POLICY_REJECT",
    "Integrator", "IntegratorRefusal", "LedgerEntry",
    "ParameterChangeRecord", "Snapshot",
    "DECLARATION_ONLY_MODEL", "STVK_MODEL", "StvkMembraneMechanism",
    "bind_surface_to_stvk",
]
