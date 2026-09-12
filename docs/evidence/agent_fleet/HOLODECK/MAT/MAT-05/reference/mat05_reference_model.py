"""mat05_reference_model.py -- independent reference model of catalogue card
MAT-05 "Synthetic materials and authorship" (holodeck-mat-05).

Card contract (quoted from the card, preregistered in ../PREREGISTRATION.txt):
  STATEMENT:   Synthetic presets clearly separated from calibrated materials
  PREDICTION:  Authoring remains in supported domains or gives explicit
               refusals
  FALSIFIER:   A fictional preset is presented as measured wood, metal or
               water
  MATHEMATICS: admissible domains; nondimensional controls

UNITS BACKBONE (citation duty, task packet): dimensional analysis defers
to MATH-01's integrated typed-quantity algebra (../../MATH/MATH-01/
reference/math01_reference_model.py -- exact (L,M,T) Dimensions, Quantity
with named dimension_mismatch refusals, DIMENSIONLESS=(0,0,0)). Independence
is claimed from the AUDITED deployed code (tools/materials.py,
material_contract.py, matter_data.py), not from MATH-01 (the designated
backbone). This model adds the SEPARATION + AUTHORING layer: two partitioned
stores, domain-confined synthetic authoring with named refusals, and a named
refusal on every path from a fictional preset to a measured claim.

DERIVED BOUND (preregistered, never widened): the nondimensional SG control
is admissible on 0 < SG <= 22.59 -- strictly positive (a nonpositive SG is a
nonpositive density, refused by the calibrated plane's own physics gate) and
bounded by osmium 22.59 g/cm^3, the densest natural elemental solid (an
absolute ceiling for any real-material claim). Fractions live in [0, 1).
"""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

# MATH-01 integrated reference model: the units backbone (citation duty).
_MATH01_DIR = (Path(__file__).resolve().parents[3] / "MATH" / "MATH-01"
               / "reference")
sys.path.insert(0, str(_MATH01_DIR))
import math01_reference_model as m01  # noqa: E402

# ---- named refusal reasons -------------------------------------------------

(REASON_MISSING_LABEL, REASON_NONFINITE, REASON_UNSUPPORTED_DOMAIN,
 REASON_SG_OUT_OF_DOMAIN, REASON_FRACTION_OUT_OF_DOMAIN, REASON_MISSING_BASIS,
 REASON_FICTIONAL_CLAIM, REASON_SYNTHETIC_NOT_CALIBRATED, REASON_DUPLICATE,
 REASON_NOT_A_STORE_MEMBER, REASON_UNKNOWN_MATERIAL, REASON_INVALID_BASIS) = (
 "missing_label", "nonfinite", "unsupported_domain", "sg_out_of_domain",
 "fraction_out_of_domain", "missing_basis", "fictional_claim",
 "synthetic_not_calibrated", "duplicate_authoring", "not_a_store_member",
 "unknown_material", "invalid_basis")

# The declared SG admissible domain (see module docstring; DERIVED, fixed).
SG_MIN = 0.0            # exclusive
SG_MAX = 22.59          # inclusive (osmium ceiling)

# Supported SYNTHETIC authoring domains: the closed set the deployed
# preset plane actually serves (materials.py DENSITY keys).
SUPPORTED_PRESET_DOMAINS = frozenset({"plush_stuffed", "knit", "acrylic"})

# Measured provenance (the calibrated plane's closed set).
MEASURED_PROVENANCE = frozenset({"researched", "parent", "derived"})

PROVENANCE_SYNTHETIC = "synthetic"

class Mat05Refusal(ValueError):
    """A NAMED refusal of the separation/authoring boundary."""

    def __init__(self, reason: str, message: str):
        super().__init__(message)
        self.reason = reason
        self.message = message

    def __repr__(self):
        return f"Mat05Refusal({self.reason!r}, {self.message!r})"


def _finite(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise Mat05Refusal(REASON_NONFINITE,
                           f"non-numeric value {value!r} refused")
    v = float(value)
    if not math.isfinite(v):
        raise Mat05Refusal(REASON_NONFINITE,
                           f"nonfinite value {value!r} refused at the door")
    return v


# ---- frozen record types (one per plane) ------------------------------------

@dataclass(frozen=True)
class PresetRecord:
    """A SYNTHETIC preset: declared fiction, labeled, forever."""
    name: str
    domain: str
    prop: str
    quantity: object          # a MATH-01 Quantity
    unit: str
    synthetic_label: str
    provenance: str = PROVENANCE_SYNTHETIC
    synthetic: bool = True


@dataclass(frozen=True)
class CalibratedRecord:
    """A CALIBRATED record: measured provenance with locator."""
    name: str
    prop: str
    quantity: object          # a MATH-01 Quantity
    unit: str
    source: str
    conditions: str
    provenance: str           # researched | parent | derived


# ---- separated stores (no shared mutable state) -----------------------------

class _Store:
    """Record bag. serve() re-checks membership AND type at the boundary: a
    hostile non-record slipped in is refused at serve time (A1-3 analog)."""
    _plane = None
    _record_type = None

    def __init__(self):
        self._records = {}

    def _put(self, key, record):
        if key in self._records:
            raise Mat05Refusal(REASON_DUPLICATE,
                               f"{key!r} already exists on the "
                               f"{self._plane} plane; first record intact")
        self._records[key] = record

    def serve(self, key):
        rec = self._records.get(key)
        if rec is None:
            return None
        if not isinstance(rec, self._record_type):
            raise Mat05Refusal(REASON_NOT_A_STORE_MEMBER,
                               f"{key!r} on the {self._plane} plane is not "
                               f"a {self._record_type.__name__}: boundary "
                               f"re-check refuses at serve time")
        return rec

    def snapshot(self):
        return MappingProxyType(dict(self._records))

    def __len__(self):
        return len(self._records)

    def get(self, name, prop):
        rec = self.serve((name, prop))
        if rec is None:
            raise Mat05Refusal(REASON_UNKNOWN_MATERIAL,
                               f"no {self._plane} material {name!r}.{prop}")
        return rec


class PresetStore(_Store):
    _plane = "preset"
    _record_type = PresetRecord

    def author(self, name, domain, prop, value, unit, label, sg=None,
               fraction=None):
        """THE AUTHORING DOOR (card prediction's surface). Fixed gate order:
        label -> finite -> supported domain -> SG domain -> fraction domain."""
        if not isinstance(label, str) or not label.strip():
            raise Mat05Refusal(REASON_MISSING_LABEL,
                               "a synthetic preset without a nonblank "
                               "synthetic_label is inadmissible")
        v = _finite(value)
        if domain not in SUPPORTED_PRESET_DOMAINS:
            raise Mat05Refusal(
                REASON_UNSUPPORTED_DOMAIN,
                f"domain {domain!r} is not supported for synthetic presets "
                f"(supported: {sorted(SUPPORTED_PRESET_DOMAINS)}); measured "
                f"wood/metal/water lives on the calibrated plane only")
        if sg is not None:
            sgv = _finite(sg)
            if not (SG_MIN < sgv <= SG_MAX):
                raise Mat05Refusal(
                    REASON_SG_OUT_OF_DOMAIN,
                    f"SG {sgv} outside the derived domain "
                    f"(0 exclusive, {SG_MAX}]: fiction may not claim "
                    f"nonphysical matter")
        if fraction is not None:
            fv = _finite(fraction)
            if not (0.0 <= fv < 1.0):
                raise Mat05Refusal(
                    REASON_FRACTION_OUT_OF_DOMAIN,
                    f"fraction control {fv} outside [0, 1)")
        qty = m01.Quantity(v, _dimension_of(unit))
        rec = PresetRecord(name=name, domain=domain, prop=prop,
                           quantity=qty, unit=unit, synthetic_label=label)
        self._put((name, prop), rec)
        return rec


class CalibratedStore(_Store):
    _plane = "calibrated"
    _record_type = CalibratedRecord

    def admit(self, name, prop, value, unit, source, conditions, provenance):
        """THE CALIBRATED DOOR: blank source/conditions -> missing_basis;
        provenance outside the measured set (incl. 'synthetic', i.e. a
        preset record offered as-is) -> fictional_claim."""
        if not isinstance(source, str) or not source.strip() \
                or not isinstance(conditions, str) or not conditions.strip():
            raise Mat05Refusal(REASON_MISSING_BASIS,
                               "no nonblank source locator AND conditions: "
                               "no basis, no calibrated record")
        v = _finite(value)
        if provenance == PROVENANCE_SYNTHETIC or provenance not in MEASURED_PROVENANCE:
            raise Mat05Refusal(
                REASON_FICTIONAL_CLAIM,
                f"provenance {provenance!r} outside the measured set "
                f"{sorted(MEASURED_PROVENANCE)}: fiction is not admitted")
        qty = m01.Quantity(v, _dimension_of(unit))
        rec = CalibratedRecord(name=name, prop=prop, quantity=qty, unit=unit,
                               source=source, conditions=conditions,
                               provenance=provenance)
        self._put((name, prop), rec)
        return rec


def _dimension_of(unit):
    """Unit -> MATH-01 Dimension. Declared-only, like the backbone."""
    table = {
        "kg/m^3": m01.Dimension((-3, 1, 0)), "g/cm^3": m01.Dimension((-3, 1, 0)),
        "1": m01.Dimension.DIMENSIONLESS, "sg": m01.Dimension.DIMENSIONLESS,
        "ratio": m01.Dimension.DIMENSIONLESS,
    }
    if unit not in table:
        raise Mat05Refusal(REASON_NONFINITE,
                           f"unit {unit!r} is not declared in this model")
    return table[unit]


class MaterialPartition:
    """THE SEPARATION (card statement's surface): both planes under one
    roof, with the partition doors. calibrated_get refuses a preset-only
    name."""

    def __init__(self):
        self.presets = PresetStore()
        self.calibrated = CalibratedStore()

    def preset_get(self, name, prop):
        return self.presets.get(name, prop)

    def calibrated_get(self, name, prop):
        """Serving a preset name through the calibrated door is exactly the
        card falsifier's shape: refused by name."""
        if self.presets.serve((name, prop)) is not None \
                and self.calibrated.serve((name, prop)) is None:
            raise Mat05Refusal(
                REASON_SYNTHETIC_NOT_CALIBRATED,
                f"{name!r}.{prop} exists only as a SYNTHETIC preset; the "
                f"calibrated door does not serve it")
        return self.calibrated.get(name, prop)

    def admit_calibrated(self, name, prop, value, unit, source, conditions,
                         provenance):
        """Calibrated door + fabricated-citation guard: a preset's exact
        values re-claimed as measured under its name is the card-falsifier
        path -- refused BEFORE admission. A different measured value under
        the same name admits (separate namespaces, no aliasing)."""
        prior = self.presets.serve((name, prop))
        if prior is not None and provenance in MEASURED_PROVENANCE:
            try:
                v = float(value)
            except (TypeError, ValueError):
                v = None
            if v is not None and v == prior.quantity.value:
                raise Mat05Refusal(
                    REASON_FICTIONAL_CLAIM,
                    f"values identical to synthetic preset {name!r}.{prop} "
                    f"re-claimed as {provenance!r}: fabricated citation; "
                    f"fiction cannot be converted to measurement")
        return self.calibrated.admit(name, prop, value, unit, source,
                                     conditions, provenance)


# ---- the nondimensional control's real caller ------------------------------
def sg_to_density(sg, basis_kg_m3):
    """density = SG x basis THROUGH MATH-01's algebra (dimensionless SG
    Quantity x (L^-3 M) basis Quantity). Domain gate BEFORE arithmetic."""
    sgv = _finite(sg)
    if not (SG_MIN < sgv <= SG_MAX):
        raise Mat05Refusal(REASON_SG_OUT_OF_DOMAIN,
                           f"SG {sgv} outside ({SG_MIN} exclusive, "
                           f"{SG_MAX}] before any arithmetic")
    basis = _finite(basis_kg_m3)
    if basis <= 0.0:
        raise Mat05Refusal(REASON_INVALID_BASIS,
                           f"nonpositive basis density {basis} refused")
    sg_q = m01.Quantity(sgv, m01.Dimension.DIMENSIONLESS)
    basis_q = m01.Quantity(basis, m01.Dimension((-3, 1, 0)))
    return sg_q * basis_q
