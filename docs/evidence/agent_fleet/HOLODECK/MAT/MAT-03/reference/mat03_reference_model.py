"""mat03_reference_model.py -- independent reference model of catalogue card
MAT-03 "Measured-data import" (holodeck-mat-03).

Card contract (quoted from the card, preregistered in ../PREREGISTRATION.txt):
  STATEMENT: Versioned datasets with temperature, moisture and strain-rate
             conditions
  PREDICTION: Imports retain source identity and reject missing physical
              context
  FALSIFIER: Provenance membership is represented as proof of authentic
             measurement
  MATHEMATICS: uncertainty propagation; citations; interpolation

STDLIB ONLY (+ the MATH-01 units backbone, cited per the task packet: the
integrated typed-quantity algebra at
docs/evidence/agent_fleet/HOLODECK/MATH/MATH-01/reference/
math01_reference_model.py supplies Dimension/Quantity/unit-scale discipline
at every dimensional touchpoint). This is an independent model of the
INTENDED import contract, NOT the deployed material plane
(tools/matter_data.py, tools/material_contract.py -- audited separately in
checks/r5_source_trace.txt and checks/r6_findings.txt).

THE CARD FALSIFIER LIVES HERE STRUCTURALLY: SourceRegistry is a metadata
registry. NO admission gate consults it (see GATE_ORDER -- membership does
no admission work). Authenticity is gated on content (identity_mismatch:
a declared content_sha256 must match the recomputed hash of the payload)
and on COMPLETE PHYSICAL CONTEXT (conditions + uncertainty + units + source
identity), never on being a known source.

Condition axes carry an AFFINE temperature family (K canonical; degC offset
+273.15), which is deliberately outside MATH-01's scale-only registry: a
scale-only degC conversion would map 0 degC to 0 K. The offset is applied
exactly (26.85 degC -> 300.0 K).
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

_MATH01 = Path(__file__).resolve().parents[3] / "MATH" / "MATH-01" / "reference"
sys.path.insert(0, str(_MATH01))
from math01_reference_model import (Dimension, Math01Refusal,  # noqa: E402
                                    Quantity, UnitRegistry)

AXES = ("temperature", "moisture", "strain_rate")

# axis -> {unit: (scale, offset_to_canonical)}; canonical unit first.
CONDITION_FAMILIES = {
    "temperature": {"k": (1.0, 0.0), "degc": (1.0, 273.15)},
    "moisture": {"fraction": (1.0, 0.0), "percent": (0.01, 0.0)},
    "strain_rate": {"1/s": (1.0, 0.0)},
}

# property -> ({unit: (Dimension, scale_to_canonical)}, sign gate)
_PROPERTY_UNITS = {
    "modulus": ({"Pa": (Dimension.PA, 1.0), "kPa": (Dimension.PA, 1e3),
                 "MPa": (Dimension.PA, 1e6), "GPa": (Dimension.PA, 1e9)},
                "positive"),
    "density": ({"kg/m^3": (Dimension((-3, 1, 0)), 1.0),
                 "g/cm^3": (Dimension((-3, 1, 0)), 1e3)}, "positive"),
    "surface_energy": ({"J/m^2": (Dimension((0, 1, -2)), 1.0)},
                       "nonnegative"),
    "strain": ({"1": (Dimension.DIMENSIONLESS, 1.0)}, "nonnegative"),
}
REGISTRY = UnitRegistry()
for _fam, _sign in _PROPERTY_UNITS.values():
    for _unit, (_dim, _scale) in _fam.items():
        REGISTRY.declare_unit(_unit, _dim, _scale)
_CANONICAL_PROPERTY_UNIT = {}
for _fam, (units, _sign) in _PROPERTY_UNITS.items():
    for _unit, (_dim, _scale) in units.items():
        if _scale == 1.0:
            _CANONICAL_PROPERTY_UNIT[_fam] = _unit

# The admission gates, in the order they can fire (the R3(e) audit object):
# NO membership / known-source gate exists.
GATE_ORDER = ("missing_source_identity", "identity_mismatch", "nonfinite",
              "bad_value", "missing_uncertainty", "unknown_unit",
              "unknown_condition_unit", "missing_condition",
              "condition_outside_envelope", "duplicate_version",
              "version_regression", "bad_version")


class Mat03Refusal(ValueError):
    """A NAMED refusal. reason is machine-checkable; message names the exact
    missing/invalid thing. Never a default, never a silent repair."""

    def __init__(self, reason: str, message: str):
        super().__init__(f"{reason}: {message}")
        self.reason = reason
        self.message = message

    def __repr__(self):
        return f"Mat03Refusal({self.reason!r}, {self.message!r})"


class SourceRegistry:
    """Known sources -- METADATA ONLY. Membership here is bookkeeping about
    what the fleet has seen before; it is never proof of authentic
    measurement and never an admission gate (the card falsifier)."""

    def __init__(self):
        self._sources = {}

    def register(self, source_id, locator):
        self._sources[source_id] = locator

    def knows(self, source_id):
        return source_id in self._sources


def _number(value, what):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise Mat03Refusal("nonfinite", f"{what} must be a real number, got "
                          f"{type(value).__name__}")
    if isinstance(value, float) and not math.isfinite(value):
        raise Mat03Refusal("nonfinite", f"{what} must be finite, got {value}")
    return float(value)


def _text(value, what):
    if not isinstance(value, str) or not value.strip():
        raise Mat03Refusal("missing_source_identity",
                           f"{what} is missing or blank")
    return value


def _canonical_hash(payload):
    body = {k: v for k, v in payload.items() if k != "content_sha256"}
    blob = json.dumps(body, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _to_canonical(value, unit, axis, what):
    fam = CONDITION_FAMILIES[axis]
    if unit not in fam:
        raise Mat03Refusal("unknown_condition_unit",
                           f"{axis} unit {unit!r} is not declared for "
                           f"{what}; no conversion is invented")
    scale, offset = fam[unit]
    return _number(value, f"{axis} {what}") * scale + offset


@dataclass(frozen=True)
class Citation:
    source_id: str
    locator: str
    note: str


@dataclass(frozen=True)
class MeasuredRecord:
    """One measured point: typed value (MATH-01 Quantity), positive
    uncertainty in the same unit, the FULL condition context (canonical),
    and the verbatim citation."""
    name: str
    quantity: Quantity
    unit: str
    uncertainty: float
    conditions: dict
    citation: Citation


@dataclass(frozen=True)
class MeasuredDataset:
    id: str
    version: int
    citation: Citation
    content_sha256: str
    envelope: dict          # axis -> (lo, hi) in canonical units
    records: tuple


@dataclass(frozen=True)
class InterpolatedRecord:
    name: str
    quantity: Quantity
    unit: str
    uncertainty: float
    conditions: dict
    citations: tuple
    interpolated: bool = True


class DatasetStore:
    """Append-only versioned store. import_dataset is the ONLY path from raw
    data to a stored dataset; admitted datasets are never mutated."""

    def __init__(self):
        self._datasets = {}     # id -> {version: MeasuredDataset}

    # -- the import gates (see GATE_ORDER) --------------------------------

    def import_dataset(self, payload, citation, known_sources=None):
        # known_sources is accepted and deliberately UNUSED for admission:
        # provenance membership is metadata, never proof (card falsifier).
        if not isinstance(citation, dict):
            raise Mat03Refusal("missing_source_identity",
                               "citation must be a {source_id, locator, "
                               "note} mapping")
        cit = Citation(_text(citation.get("source_id"), "citation.source_id"),
                       _text(citation.get("locator"), "citation.locator"),
                       _text(citation.get("note"), "citation.note"))
        # identity_mismatch: declared content identity must match content
        computed = _canonical_hash(payload)
        declared = payload.get("content_sha256")
        if declared is not None and declared != computed:
            raise Mat03Refusal(
                "identity_mismatch",
                f"payload declares content_sha256 {declared!r} but its "
                f"content hashes to {computed!r}; a declared identity that "
                f"disagrees with the content is refused, however complete "
                f"its citation and however known its source")
        ds_id = _text(payload.get("id"), "payload.id")
        envelope = self._admit_envelope(payload.get("envelope"))
        records = tuple(self._admit_record(r, cit, envelope)
                        for r in (payload.get("records") or []))
        if not records:
            raise Mat03Refusal("missing_condition",
                               "payload carries no measured records")
        # version gates (last: they guard the STORE, after content gates)
        version = payload.get("version")
        if isinstance(version, bool) or not isinstance(version, int) \
                or version < 1:
            raise Mat03Refusal("bad_version",
                               f"dataset version must be an integer >= 1, "
                               f"got {version!r}")
        history = self._datasets.get(ds_id, {})
        if history and version < max(history):
            raise Mat03Refusal("version_regression",
                               f"{ds_id} is at v{max(history)}; importing "
                               f"v{version} would replace newer data with "
                               f"older")
        if version in history:
            raise Mat03Refusal("duplicate_version",
                               f"{ds_id} v{version} is already stored; no "
                               f"silent overwrite, no idempotent second row")
        dataset = MeasuredDataset(id=ds_id, version=version, citation=cit,
                                  content_sha256=computed, envelope=envelope,
                                  records=records)
        self._datasets.setdefault(ds_id, {})[version] = dataset
        return dataset

    def _admit_envelope(self, env):
        if not isinstance(env, dict):
            raise Mat03Refusal("missing_condition",
                               "payload declares no condition envelope")
        out = {}
        for axis in AXES:
            spec = env.get(axis)
            if not isinstance(spec, dict) or "lo" not in spec \
                    or "hi" not in spec or "unit" not in spec:
                raise Mat03Refusal("missing_condition",
                                   f"envelope omits the {axis} axis")
            lo = _to_canonical(spec["lo"], spec["unit"], axis, "envelope lo")
            hi = _to_canonical(spec["hi"], spec["unit"], axis, "envelope hi")
            out[axis] = (min(lo, hi), max(lo, hi))
        return out

    def _admit_record(self, raw, cit, envelope):
        if not isinstance(raw, dict):
            raise Mat03Refusal("nonfinite", "record must be a mapping")
        name = raw.get("property")
        if name not in _PROPERTY_UNITS:
            raise Mat03Refusal("unknown_unit",
                               f"property {name!r} has no declared unit "
                               f"family")
        fam, sign = _PROPERTY_UNITS[name]
        value = _number(raw.get("value"), f"{name} value")
        if (sign == "positive" and value <= 0) or (sign == "nonnegative"
                                                   and value < 0):
            raise Mat03Refusal("bad_value",
                               f"{name}={value} violates its own physics "
                               f"({sign})")
        unit = raw.get("unit")
        if unit not in fam:
            raise Mat03Refusal("unknown_unit",
                               f"unit {unit!r} is not registered for "
                               f"{name}; no conversion factor is invented")
        unc = raw.get("uncertainty")
        if unc is None or (isinstance(unc, str) and not unc.strip()):
            raise Mat03Refusal("missing_uncertainty",
                               f"{name} carries no stated uncertainty; a "
                               f"measurement without a band is not "
                               f"importable")
        unc = _number(unc, f"{name} uncertainty")
        if unc <= 0:
            raise Mat03Refusal("missing_uncertainty",
                               f"{name} carries uncertainty {unc}; the band "
                               f"must be positive")
        canonical_unit = _CANONICAL_PROPERTY_UNIT[name]
        quantity = REGISTRY.convert(value, unit, canonical_unit)
        # the band converts WITH the value: a MPa uncertainty on a Pa value
        # would corrupt every propagation
        unc = REGISTRY.convert(unc, unit, canonical_unit).value
        conditions = {}
        for axis in AXES:
            spec = (raw.get("conditions") or {}).get(axis)
            if spec is None:
                raise Mat03Refusal("missing_condition",
                                   f"record omits the {axis} condition -- "
                                   f"physical context is incomplete")
            canonical = _to_canonical(spec.get("value"), spec.get("unit"),
                                      axis, "condition")
            lo, hi = envelope[axis]
            if not (lo <= canonical <= hi):
                raise Mat03Refusal("condition_outside_envelope",
                                   f"{axis}={canonical} (canonical) is "
                                   f"outside the declared envelope "
                                   f"[{lo}, {hi}]")
            conditions[axis] = canonical
        return MeasuredRecord(name=name, quantity=quantity,
                              unit=canonical_unit, uncertainty=unc,
                              conditions=conditions, citation=cit)

    # -- read paths --------------------------------------------------------

    def get(self, ds_id, version=None):
        history = self._datasets.get(ds_id)
        if history is None:
            raise Mat03Refusal("version_regression",
                               f"no dataset {ds_id!r} stored")
        if version is None:
            version = max(history)
        if version not in history:
            raise Mat03Refusal("version_regression",
                               f"{ds_id} has no v{version}")
        return history[version]

    def listing(self):
        return {ds_id: sorted(h) for ds_id, h in
                sorted(self._datasets.items())}


def interpolate(dataset, name, query_conditions):
    """Linear interpolation along the ONE axis that varies across the
    measured records of `name`; the query must lie inside the MEASURED
    envelope (no extrapolation -- extrapolation is inventing measurement)."""
    pts = [r for r in dataset.records if r.name == name]
    if not pts:
        raise Mat03Refusal("unknown_unit", f"dataset carries no {name!r}")
    varying = [a for a in AXES if len({r.conditions[a] for r in pts}) > 1]
    if len(varying) != 1:
        raise Mat03Refusal("missing_condition",
                           "records must vary in exactly one condition axis")
    axis = varying[0]
    q = {}
    for a in AXES:
        spec = (query_conditions or {}).get(a)
        if spec is None:
            raise Mat03Refusal("missing_condition",
                               f"query omits the {a} condition")
        q[a] = _to_canonical(spec.get("value"), spec.get("unit"), a,
                             "query condition")
    for a in AXES:
        vals = [r.conditions[a] for r in pts]
        if a == axis:
            inside = min(vals) <= q[a] <= max(vals)
        else:
            inside = q[a] == vals[0]
        if not inside:
            raise Mat03Refusal(
                "condition_outside_envelope",
                f"{a}={q[a]} is outside the MEASURED envelope of the "
                f"{name} grid (interpolation never extrapolates)")
    r1, r2 = sorted(pts, key=lambda r: r.conditions[axis])
    x1, x2 = r1.conditions[axis], r2.conditions[axis]
    t = (q[axis] - x1) / (x2 - x1)
    value = r1.quantity.value + t * (r2.quantity.value - r1.quantity.value)
    unc = (1 - t) * r1.uncertainty + t * r2.uncertainty
    return InterpolatedRecord(
        name=name, quantity=Quantity(value, r1.quantity.dimension),
        unit=r1.unit, uncertainty=unc, conditions=q,
        citations=(r1.citation, r2.citation))


def _two_records(a, b, label):
    for r, tag in ((a, "a"), (b, "b")):
        if not isinstance(r, MeasuredRecord):
            raise Mat03Refusal("not_a_measured_record",
                               f"{tag} of {label} is not an admitted "
                               f"MeasuredRecord")


def propagate_sum(a, b):
    """Independent-uncertainty propagation through a + b (same property)."""
    _two_records(a, b, "propagate_sum")
    if a.name != b.name:
        raise Mat03Refusal("unknown_unit",
                           f"propagate_sum needs one property, got "
                           f"{a.name!r} and {b.name!r}")
    total = a.quantity + b.quantity           # MATH-01 composition (cited)
    u = math.sqrt(a.uncertainty ** 2 + b.uncertainty ** 2)
    return _derived(a, b, total, u, "a + b; u = sqrt(ua^2 + ub^2)")


def propagate_product(a, b):
    """Independent-uncertainty propagation through a * b (relative form)."""
    _two_records(a, b, "propagate_product")
    if a.quantity.value == 0.0 or b.quantity.value == 0.0:
        raise Mat03Refusal("bad_value",
                           "relative propagation needs nonzero factors")
    total = a.quantity * b.quantity           # MATH-01 composition (cited)
    rel = math.sqrt((a.uncertainty / a.quantity.value) ** 2
                    + (b.uncertainty / b.quantity.value) ** 2)
    return _derived(a, b, total, abs(total.value) * rel,
                    "a * b; u = |ab| * sqrt((ua/a)^2 + (ub/b)^2)")


def _derived(a, b, total, u, arithmetic):
    return MeasuredRecord(
        name=f"derived({a.name},{b.name})", quantity=total, unit="SI",
        uncertainty=u, conditions=dict(a.conditions),
        citation=Citation(source_id=f"{a.citation.source_id}+"
                          f"{b.citation.source_id}",
                          locator=f"{a.citation.locator}; "
                          f"{b.citation.locator}",
                          note=f"derived: {arithmetic}; inputs cited"))
