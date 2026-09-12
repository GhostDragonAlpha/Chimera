"""mat01_reference_model.py -- independent reference model of catalogue card
MAT-01 "Typed material properties" (holodeck-mat-01).

Card contract (quoted from the card, preregistered in ../PREREGISTRATION.txt):
  STATEMENT:   Admitted parameter records distinct from raw data
  PREDICTION:  Invalid units, nonfinite values and missing basis refuse at
               the real caller
  FALSIFIER:   A legacy bypass reaches a calculation advertised as validated
  MATHEMATICS: dimensions; reference conditions; immutable snapshots

UNITS BACKBONE (citation duty, task packet): dimensional analysis defers to
MATH-01's integrated typed-quantity algebra
(docs/evidence/agent_fleet/HOLODECK/MATH/MATH-01/reference/
math01_reference_model.py -- exact Fraction (L,M,T) Dimension vectors,
Quantity with named `dimension_mismatch` refusals). Independence is claimed
from the AUDITED deployed code (tools/material_contract.py) — not from
MATH-01, which the packet designates this lane's units backbone. This model
adds the ADMISSION layer MATH-01 deliberately does not carry: raw data
becomes a parameter record ONLY through admit(); admitted records are
frozen; snapshots are immutable; the real caller (bulk_mass) consumes ONLY
admitted records and refuses every legacy input by name.
"""
from __future__ import annotations

import math
import sys
import types
from dataclasses import dataclass
from pathlib import Path

# MATH-01 integrated reference model: the units backbone (citation duty).
_MATH01_DIR = (Path(__file__).resolve().parents[3] / "MATH" / "MATH-01"
               / "reference")
sys.path.insert(0, str(_MATH01_DIR))
import math01_reference_model as m01  # noqa: E402

# ---- the one refusal type (named, machine-checkable) ------------------------

REASON_UNKNOWN_UNIT = "unknown_unit"
REASON_UNIT_DIMENSION_MISMATCH = "unit_dimension_mismatch"
REASON_NONFINITE = "nonfinite"
REASON_MISSING_BASIS = "missing_basis"
REASON_INVALID_VALUE = "invalid_value"
REASON_LEGACY_INPUT = "legacy_input"
REASON_DUPLICATE = "duplicate_admission"
REASON_NOT_A_SNAPSHOT = "not_a_snapshot_member"


class Mat01Refusal(ValueError):
    """Named refusal of the admission boundary."""

    def __init__(self, reason: str, message: str):
        super().__init__(message)
        self.reason = reason
        self.message = message

    def __repr__(self):
        return f"Mat01Refusal({self.reason!r}, {self.message!r})"


# ---- the closed property schema (family -> MATH-01 dimension) ---------------

# family -> {unit -> scale to canonical SI}. Conversions exist ONLY by this
# declaration; the family denotes ONE MATH-01 Dimension.
FAMILIES = {
    "density": {"kg/m^3": 1.0, "g/cm^3": 1e3},
    "pressure": {"pa": 1.0, "kpa": 1e3, "mpa": 1e6, "gpa": 1e9},
    "energy_area": {"j/m^2": 1.0},
    "dimensionless": {"1": 1.0, "ratio": 1.0, "sg": 1.0},
}

_FAMILY_DIM = {
    # (L, M, T) exponent vectors, exact per MATH-01's Dimension algebra
    "density": m01.Dimension((-3, 1, 0)),        # kg m^-3
    "pressure": m01.Dimension.PA,                # kg m^-1 s^-2
    "energy_area": m01.Dimension((0, 1, -2)),    # J/m^2 = kg s^-2
    "dimensionless": m01.Dimension.DIMENSIONLESS,
}

# property type -> (families allowed, positive, nonnegative, fraction)
# hint-match rule identical in spirit to a closed auditable table: exact
# name match on the hint, or prefix when the hint ends with '_'.
SCHEMA = {
    "density": {"hints": ("density", "rho", "derived:density"),
                "families": ("density",), "positive": True},
    "modulus": {"hints": ("e", "e_", "modulus"),
                "families": ("pressure",), "positive": True},
    "surface_energy": {"hints": ("gamma", "surface_energy"),
                       "families": ("energy_area",), "nonnegative": True},
    "fraction": {"hints": ("fraction",),
                 "families": ("dimensionless",), "fraction": True},
    "sg": {"hints": ("sg",), "families": ("dimensionless",), "positive": True},
}


def _norm(unit: str) -> str:
    return unit.strip().lower()


def property_type(name: str) -> str:
    n = name.strip().lower()
    for ptype, spec in SCHEMA.items():
        for hint in spec["hints"]:
            if n == hint or (hint.endswith("_") and n.startswith(hint)):
                return ptype
    return "fraction"  # closed default: the most constrained dimensionless


def _family_of(unit: str) -> str | None:
    u = _norm(unit)
    for fam, table in FAMILIES.items():
        if u in table:
            return fam
    return None


# ---- the admitted record (immutable snapshot of one parameter) --------------


class MaterialParameter:
    """A typed, frozen parameter record. Construction is gated: use admit();
    the constructor validates like everything else at the door."""

    __slots__ = ("name", "quantity", "unit_original", "provenance",
                 "source", "conditions", "derivation")

    def __init__(self, name, quantity, unit_original, provenance, source,
                 conditions, derivation=None):
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "quantity", quantity)
        object.__setattr__(self, "unit_original", unit_original)
        object.__setattr__(self, "provenance", provenance)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "conditions", conditions)
        object.__setattr__(self, "derivation", derivation)

    def __setattr__(self, key, value):
        raise Mat01Refusal("immutable_record",
                           f"attribute {key!r} of an admitted parameter is "
                           "frozen; admit a new record instead")

    def __repr__(self):
        return (f"MaterialParameter({self.name!r}, {self.quantity!r}, "
                f"{self.provenance!r})")


def admit(raw: dict) -> MaterialParameter:
    """The ONLY path from raw data to a parameter record (card statement)."""
    if not isinstance(raw, dict):
        raise Mat01Refusal(REASON_LEGACY_INPUT,
                           f"admit() takes the raw record dict, got "
                           f"{type(raw).__name__}")
    for key in ("name", "value", "unit", "source", "conditions", "provenance"):
        if key not in raw:
            raise Mat01Refusal(REASON_MISSING_BASIS,
                               f"raw record is missing required key {key!r}")
    name = raw["name"]
    if not isinstance(name, str) or not name.strip():
        raise Mat01Refusal(REASON_MISSING_BASIS,
                           "parameter name must be a nonblank string")
    # finiteness at the door (card prediction: nonfinite refuses)
    value = raw["value"]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise Mat01Refusal(REASON_NONFINITE,
                           f"{name}: value {value!r} is not a real number")
    if isinstance(value, float) and not math.isfinite(value):
        raise Mat01Refusal(REASON_NONFINITE,
                           f"{name}: value is not finite ({value})")
    # unit registered (card prediction: invalid units refuse)
    unit = _norm(raw["unit"])
    fam = _family_of(unit)
    if fam is None:
        raise Mat01Refusal(REASON_UNKNOWN_UNIT,
                           f"{name}: unit '{raw['unit']}' is not registered; "
                           "no conversion factor may be invented for it")
    # unit family must denote the property type's MATH-01 dimension
    ptype = property_type(name)
    want_fams = SCHEMA[ptype]["families"]
    if fam not in want_fams:
        have_dim = _FAMILY_DIM[fam]
        want_dim = _FAMILY_DIM[want_fams[0]]
        raise Mat01Refusal(
            REASON_UNIT_DIMENSION_MISMATCH,
            f"{name}: a {ptype} must carry a unit from families "
            f"{want_fams} (dimension {want_dim}); '{raw['unit']}' belongs "
            f"to family '{fam}' (dimension {have_dim}) -- refused, not "
            "converted on faith")
    # provenance hygiene (card mathematics: reference conditions)
    provenance = raw["provenance"]
    if provenance not in ("researched", "parent", "derived"):
        raise Mat01Refusal(REASON_MISSING_BASIS,
                           f"{name}: provenance must be researched | "
                           f"parent | derived, got {provenance!r}")
    derivation = raw.get("derivation")
    if provenance == "derived" and (
            not isinstance(derivation, str) or not derivation.strip()):
        raise Mat01Refusal(REASON_MISSING_BASIS,
                           f"{name}: declared derived but carries no "
                           "derivation (arithmetic + inputs)")
    for label in ("source", "conditions"):
        text = raw[label]
        if not isinstance(text, str) or not text.strip():
            raise Mat01Refusal(REASON_MISSING_BASIS,
                               f"{name}: {label} is blank; a parameter "
                               "without stated reference conditions is not "
                               "admissible")
    # sign / fraction gates
    spec = SCHEMA[ptype]
    if spec.get("positive") and not value > 0:
        raise Mat01Refusal(REASON_INVALID_VALUE,
                           f"{name} = {value} {raw['unit']}: a {ptype} must "
                           "be positive")
    if spec.get("nonnegative") and value < 0.0:
        raise Mat01Refusal(REASON_INVALID_VALUE,
                           f"{name} = {value} {raw['unit']}: a {ptype} must "
                           "be nonnegative")
    if spec.get("fraction") and not 0.0 <= value <= 1.0:
        raise Mat01Refusal(REASON_INVALID_VALUE,
                           f"{name} = {value}: a fraction must lie in [0,1]")
    # SI-scale the value into a MATH-01 Quantity (the units backbone)
    scale = FAMILIES[fam][unit]
    quantity = m01.Quantity(value * scale, _FAMILY_DIM[fam])
    return MaterialParameter(name, quantity, raw["unit"], provenance,
                             raw["source"], raw["conditions"], derivation)


# ---- immutable snapshots (card mathematics) ---------------------------------


def snapshot(params) -> types.MappingProxyType:
    """An immutable name -> record view. The underlying dict is copied
    first, so later admission into the source bag cannot rewrite history;
    the mapping itself refuses item assignment; serve() re-checks every
    member at the boundary."""
    data = dict(params)
    for k, v in data.items():
        if not isinstance(v, MaterialParameter):
            raise Mat01Refusal(REASON_NOT_A_SNAPSHOT,
                               f"snapshot member {k!r} is "
                               f"{type(v).__name__}, not an admitted "
                               "MaterialParameter -- hostile injection is "
                               "refused at the boundary")
    return types.MappingProxyType(data)


def serve(snap, name: str) -> MaterialParameter:
    """The serve boundary: membership + type re-check before any consumer
    sees the record (a frozen record cannot rot, but a bag can be lied
    about; the boundary trusts neither)."""
    try:
        rec = snap[name]
    except (KeyError, TypeError):
        raise Mat01Refusal(REASON_NOT_A_SNAPSHOT,
                           f"no admitted parameter {name!r} in this "
                           "snapshot") from None
    if not isinstance(rec, MaterialParameter):
        raise Mat01Refusal(REASON_NOT_A_SNAPSHOT,
                           f"{name!r} is {type(rec).__name__}, not an "
                           "admitted MaterialParameter")
    return rec


# ---- THE REAL CALLER (the card prediction's surface) ------------------------


def bulk_mass(density_parameter, volume_quantity):
    """mass = rho x V. Accepts ONLY an admitted MaterialParameter and a
    MATH-01 Quantity of Dimension L^3. Every legacy input is refused BEFORE
    any arithmetic; dimension mismatches refuse via MATH-01's
    `dimension_mismatch`."""
    if not isinstance(density_parameter, MaterialParameter):
        raise Mat01Refusal(
            REASON_LEGACY_INPUT,
            f"bulk_mass takes an admitted MaterialParameter, got "
            f"{type(density_parameter).__name__} -- a legacy bypass into a "
            "validated calculation is refused")
    if density_parameter.property_type() != "density":
        raise Mat01Refusal(
            "wrong_parameter_type",
            f"bulk_mass takes a density parameter, got "
            f"{density_parameter.name!r} "
            f"({density_parameter.property_type()})")
    if not isinstance(volume_quantity, m01.Quantity):
        raise Mat01Refusal(
            REASON_LEGACY_INPUT,
            f"bulk_mass takes a MATH-01 Quantity volume, got "
            f"{type(volume_quantity).__name__} -- raw numbers do not reach "
            "validated calculations")
    product = density_parameter.quantity * volume_quantity  # kg m^-3 * m^3
    return product


def density_from_sg(sg_parameter, basis_value, basis_conditions):
    """SG -> density REQUIRES the declared reference basis CONDITIONS and a
    positive finite basis; the derived record carries its arithmetic."""
    if not isinstance(sg_parameter, MaterialParameter):
        raise Mat01Refusal(REASON_LEGACY_INPUT,
                           "density_from_sg takes an admitted SG parameter")
    if sg_parameter.property_type() != "sg":
        raise Mat01Refusal("wrong_parameter_type",
                           f"density_from_sg takes an SG parameter, got "
                           f"{sg_parameter.name!r}")
    if not isinstance(basis_conditions, str) or not basis_conditions.strip():
        raise Mat01Refusal(
            REASON_MISSING_BASIS,
            "SG -> density requires the declared reference basis CONDITIONS "
            "(e.g. 'water at 4 C'); none were stated -- refused before any "
            "arithmetic")
    if isinstance(basis_value, bool) or not isinstance(basis_value,
                                                       (int, float)) or \
            isinstance(basis_value, float) and not math.isfinite(basis_value) \
            or basis_value <= 0:
        raise Mat01Refusal(REASON_INVALID_VALUE,
                           "reference basis density must be a positive "
                           "finite kg/m^3 value")
    val = sg_parameter.quantity.value * basis_value
    return admit({
        "name": "derived:density", "value": val, "unit": "kg/m^3",
        "source": (f"derived from {sg_parameter.name} = "
                   f"{sg_parameter.quantity.value} ({sg_parameter.source}) x "
                   f"declared basis {basis_value} kg/m^3 "
                   f"({basis_conditions})"),
        "conditions": f"{sg_parameter.conditions}; basis: {basis_conditions}",
        "provenance": "derived",
        "derivation": (f"rho = SG x rho_ref = {sg_parameter.quantity.value} "
                       f"x {basis_value} = {val} kg/m^3"),
    })


def admit_into(bag: dict, raw: dict) -> MaterialParameter:
    """Admit into a bag; a second admission of the same property name is
    refused with the first admission intact (immutable history)."""
    rec = admit(raw)
    if rec.name in bag:
        raise Mat01Refusal(REASON_DUPLICATE,
                           f"{rec.name!r} is already admitted in this bag; "
                           "re-admitting would rewrite admitted history")
    bag[rec.name] = rec
    return rec


def as_unit(param: MaterialParameter, unit: str) -> MaterialParameter:
    """Re-express an admitted parameter in another unit of the SAME family:
    returns a NEW record; the original is untouched (immutable snapshots)."""
    if not isinstance(param, MaterialParameter):
        raise Mat01Refusal(REASON_LEGACY_INPUT,
                           "as_unit takes an admitted MaterialParameter")
    u = _norm(unit)
    fam = _family_of(u)
    if fam is None:
        raise Mat01Refusal(REASON_UNKNOWN_UNIT,
                           f"unit '{unit}' is not registered")
    ptype = param.property_type()
    if fam not in SCHEMA[ptype]["families"]:
        raise Mat01Refusal(
            REASON_UNIT_DIMENSION_MISMATCH,
            f"cannot re-express {param.name!r} ({ptype}) in '{unit}': "
            f"family '{fam}' does not denote the parameter's dimension")
    si_scale = FAMILIES[_family_of(_norm(param.unit_original))][
        _norm(param.unit_original)]
    new_scale = FAMILIES[fam][u]
    new_value = param.quantity.value * si_scale / new_scale
    return admit({"name": param.name, "value": new_value, "unit": unit,
                  "source": param.source, "conditions": param.conditions,
                  "provenance": param.provenance,
                  "derivation": param.derivation})


# convenience: property-type inference lives on the record too ----------------


def _ptype(self):
    return property_type(self.name)


MaterialParameter.property_type = _ptype
