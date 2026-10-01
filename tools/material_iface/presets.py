"""presets.py -- MaterialPreset: parameter values WITH units, provenance, validity.

Campaign law implemented here:
  - A MEASURED preset exists only when every parameter carries a citation and a
    species label and a declared validity range.
  - Arbitrary combinations (values drawn from distinct measured sources, or any
    uncited value) are AUTO-DECLARED synthetic. They never inherit a measured
    label.
  - A runtime-adjusted measured preset stops being measured: the adjustment is
    recorded and the preset is relabeled synthetic with the original citation
    preserved in the note.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .model import MaterialModel
from .parameters import ParameterRefusal, build_parameter_set
from .units import Quantity, family_of


class PresetRefusal(ValueError):
    def __init__(self, reason: str, message: str):
        super().__init__(f"[{reason}] {message}")
        self.reason = reason
        self.message = message


class PresetReason:
    MISSING_CITATION = "missing_citation"
    MISSING_SPECIES = "missing_species"
    MISSING_VALIDITY = "missing_validity_range"
    MODEL_MISMATCH = "preset_model_mismatch"
    INCOMPLETE_COMBINATION = "incomplete_combination"


MEASURED = "measured"
SYNTHETIC = "synthetic"


@dataclass(frozen=True)
class CitedValue:
    """One parameter value with the provenance needed to call it measured."""
    quantity: Quantity
    citation: str = ""    # source locator (nonempty required for measured)
    species: str = ""     # species label (nonempty required for measured)
    source_id: str = ""   # identity of the measured source preset


@dataclass(frozen=True)
class ValidityRange:
    """Declared validity of a preset, e.g. temperature 250..350 K."""
    unit: str
    lo: float
    hi: float
    dimension: str = ""   # e.g. "temperature"; empty = same as unit family

    def __post_init__(self):
        if not (self.lo <= self.hi):
            raise PresetRefusal("bad_validity_range",
                                f"validity lo {self.lo!r} > hi {self.hi!r}")
        family_of(self.unit)
        object.__setattr__(self, "dimension",
                           self.dimension or family_of(self.unit))

    def check(self, quantity: Quantity) -> tuple[bool, str]:
        try:
            value = quantity.in_unit(self.unit)
        except Exception as exc:  # dimension family mismatch -> not applicable
            return False, f"condition not comparable with validity {self!r}: {exc}"
        if not (self.lo <= value <= self.hi):
            return False, f"{quantity} outside declared validity " \
                          f"[{self.lo!r}, {self.hi!r}] {self.unit}"
        return True, ""


@dataclass(frozen=True)
class Provenance:
    kind: str               # "measured" | "synthetic"
    citation: str
    species: str
    validity: ValidityRange | None = None
    note: str = ""


@dataclass(frozen=True)
class MaterialPreset:
    """Values + provenance for one model. Distinct record type from the model."""
    preset_id: str
    model_id: str
    values: object = None            # ParameterSet (loose typing avoids a cycle)
    provenance: Provenance = None

    @property
    def kind(self) -> str:
        return self.provenance.kind

    def applicability(self, conditions: dict[str, Quantity]) -> tuple[bool, str]:
        v = self.provenance.validity
        if v is None:
            return True, ""
        for name, quantity in conditions.items():
            if family_of(quantity.unit) == v.dimension:
                return v.check(quantity)
        return True, ""  # no condition of the validity dimension was supplied

    # -- constructors ---------------------------------------------------------

    @classmethod
    def measured(cls, preset_id: str, model: MaterialModel,
                 cited: dict[str, CitedValue], validity: ValidityRange) -> "MaterialPreset":
        metas = {m.name for m in model.parameters}
        missing = sorted(metas - set(cited))
        if missing:
            raise PresetRefusal(
                PresetReason.MISSING_CITATION,
                f"measured preset {preset_id!r}: model {model.model_id!r} "
                f"parameter(s) {missing} carry no citation; the repo holds no "
                f"measured value for them, so the preset cannot claim 'measured'")
        for name in sorted(metas & set(cited)):
            c = cited[name]
            if not c.citation.strip():
                raise PresetRefusal(PresetReason.MISSING_CITATION,
                                    f"measured preset {preset_id!r}: {name!r} has "
                                    f"no source locator")
            if not c.species.strip():
                raise PresetRefusal(PresetReason.MISSING_SPECIES,
                                    f"measured preset {preset_id!r}: {name!r} has "
                                    f"no species label")
        if validity is None:
            raise PresetRefusal(PresetReason.MISSING_VALIDITY,
                                f"measured preset {preset_id!r}: a measured preset "
                                f"declares its validity range")
        values = build_parameter_set(
            model, {name: cited[name].quantity for name in metas})
        sources = sorted({cited[n].source_id or cited[n].citation
                          for n in metas})
        citation = "; ".join(sources)
        species = sorted({cited[n].species for n in metas})
        return cls(preset_id=preset_id, model_id=model.model_id, values=values,
                   provenance=Provenance(kind=MEASURED, citation=citation,
                                         species=", ".join(species),
                                         validity=validity))

    @classmethod
    def synthetic(cls, preset_id: str, model: MaterialModel,
                  quantities: dict[str, Quantity], note: str = "",
                  validity: ValidityRange | None = None) -> "MaterialPreset":
        values = build_parameter_set(model, quantities)
        return cls(preset_id=preset_id, model_id=model.model_id, values=values,
                   provenance=Provenance(kind=SYNTHETIC,
                                         citation="synthetic: values declared for "
                                                  "interface exercise, no measured source",
                                         species="synthetic",
                                         validity=validity, note=note))

    @classmethod
    def combine_values(cls, preset_id: str, model: MaterialModel,
                       parts: dict[str, CitedValue],
                       validity: ValidityRange | None = None) -> "MaterialPreset":
        """Build a preset from per-parameter cited values.

        Auto-labeling law: the result is MEASURED only when every parameter
        carries a nonempty citation AND species AND all values trace to ONE
        single source identity. Any arbitrary combination (>=2 distinct
        sources, or any uncited value) is AUTO-DECLARED synthetic -- never
        silently measured.
        """
        metas = {m.name for m in model.parameters}
        missing = sorted(metas - set(parts))
        if missing:
            raise PresetRefusal(PresetReason.INCOMPLETE_COMBINATION,
                                f"combination {preset_id!r}: parameters {missing} "
                                f"have no contribution")
        uncited = sorted(n for n in metas
                         if not parts[n].citation.strip()
                         or not parts[n].species.strip())
        sources = {n: (parts[n].source_id or parts[n].citation)
                   for n in metas if parts[n].citation.strip()}
        single_source = len(set(sources.values())) == 1 and len(sources) == len(metas)
        if uncited or not single_source:
            origin = (f"synthetic combination of "
                      f"{sorted(set(sources.values())) or ['uncited values']}")
            if uncited:
                origin += f"; uncited: {uncited}"
            note_bits = [f"{n} <- {parts[n].species or 'unlabeled'}"
                         f" ({parts[n].citation or 'no citation'})" for n in sorted(metas)]
            values = build_parameter_set(
                model, {n: parts[n].quantity for n in metas})
            return cls(preset_id=preset_id, model_id=model.model_id, values=values,
                       provenance=Provenance(kind=SYNTHETIC, citation=origin,
                                             species="synthetic", validity=validity,
                                             note="; ".join(note_bits)))
        values = build_parameter_set(model, {n: parts[n].quantity for n in metas})
        return cls(preset_id=preset_id, model_id=model.model_id, values=values,
                   provenance=Provenance(
                       kind=MEASURED,
                       citation=next(iter(set(sources.values()))),
                       species=sorted({parts[n].species for n in metas})[0],
                       validity=validity))

    def runtime_adjusted(self, parameter: str, quantity: Quantity,
                         step: int) -> "MaterialPreset":
        """A runtime parameter change re-labels the preset: a hand-adjusted
        measured value is no longer measured. The original citation survives
        in the note so the change is auditable, never absorbed."""
        if parameter not in self.values.values:
            raise PresetRefusal("unknown_parameter",
                                f"preset {self.preset_id!r} has no {parameter!r}")
        metas_accepted = quantity.to(self.values.quantity(parameter).unit)
        new_values = dict(self.values.values)
        new_values[parameter] = metas_accepted
        note = (self.provenance.note +
                ("" if not self.provenance.note else "; ") +
                f"step {step}: {parameter} adjusted at runtime "
                f"({self.values.quantity(parameter)} -> {metas_accepted}); "
                f"originally {self.provenance.kind} "
                f"[{self.provenance.citation}] species={self.provenance.species}")
        return MaterialPreset(
            preset_id=self.preset_id + f"@adjust{step}",
            model_id=self.model_id,
            values=type(self.values)(model_id=self.values.model_id,
                                     values=new_values),
            provenance=Provenance(
                kind=SYNTHETIC,
                citation=f"runtime adjustment at step {step} of "
                         f"{self.preset_id} [{self.provenance.kind}: "
                         f"{self.provenance.citation}]",
                species=self.provenance.species,
                validity=self.provenance.validity,
                note=note))
