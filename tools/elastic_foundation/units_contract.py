"""Versioned, dimensionally explicit CPU boundary for the legacy STVK kernel.

The unchanged kernel consumes surface Lamé coefficients through a historical
duck-typed material protocol.  Public callers never see that compatibility
view: they admit either E3d [Pa] with h [m], or E2 [N/m] with h [m], and receive
an evaluation that retains the admitted physical record and provenance.
"""
from __future__ import annotations

from dataclasses import InitVar, dataclass
import math
import numbers
import sys
from typing import ClassVar, Union

import numpy as np

try:  # Normal package import after this proposal is pasted into the worktree.
    from .law import Evaluation, evaluate_elastic
except ImportError:  # Isolated proposal execution with the slot-03 repo on sys.path.
    from tools.elastic_foundation.law import Evaluation, evaluate_elastic


CONTRACT_VERSION = "elastic-physical-cpu/v1"
EPS64 = 2.0 ** -52


def _gamma(operation_count: int) -> float:
    """Higham gamma_n roundoff bound for n sequential float64 operations."""
    neps = int(operation_count) * EPS64
    if operation_count < 0 or neps >= 1.0:
        raise ValueError("operation_count is outside the gamma_n domain")
    return neps / (1.0 - neps)


class UnitsReason:
    NUMERIC_MATERIAL_REQUIRED = "numeric_material_required"
    NONFINITE_MATERIAL = "nonfinite_material"
    NONPOSITIVE_YOUNG_MODULUS = "nonpositive_young_modulus"
    NONPOSITIVE_SURFACE_MODULUS = "nonpositive_surface_modulus"
    NONPOSITIVE_THICKNESS = "nonpositive_thickness"
    POISSON_OUT_OF_RANGE = "poisson_out_of_range"
    SURFACE_MODULUS_OVERFLOW = "surface_modulus_overflow"
    SURFACE_MODULUS_UNDERFLOW = "surface_modulus_underflow"
    LAME_COEFFICIENT_OVERFLOW = "lame_coefficient_overflow"
    LAME_COEFFICIENT_UNDERFLOW = "lame_coefficient_underflow"
    LAME_PRECISION_LOSS = "lame_precision_loss"
    STRUCTURED_PROVENANCE_REQUIRED = "structured_provenance_required"
    MATERIAL_NOT_ADMITTED = "material_not_admitted"
    MATERIAL_RECORD_INCONSISTENT = "material_record_inconsistent"
    DIRECT_CONSTRUCTION_FORBIDDEN = "direct_construction_forbidden"
    OUTPUT_MALFORMED = "output_malformed"
    OUTPUT_NONFINITE = "output_nonfinite"
    OUTPUT_DIMENSION_MISMATCH = "output_dimension_mismatch"


class UnitsRefusal(ValueError):
    """Named refusal at the dimensional boundary."""

    def __init__(self, reason: str, message: str):
        super().__init__(message)
        self.reason = reason
        self.message = message


def _nonempty_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise UnitsRefusal(
            UnitsReason.STRUCTURED_PROVENANCE_REQUIRED,
            f"{field_name} must be a non-empty string",
        )
    return value


@dataclass(frozen=True)
class SourceReference:
    """A source and an exact locator within it; both are mandatory."""

    uri: str
    locator: str

    def __post_init__(self) -> None:
        _nonempty_text(self.uri, "source uri")
        _nonempty_text(self.locator, "source locator")


@dataclass(frozen=True)
class SyntheticCoefficientProvenance:
    """Explicit declaration that all coefficients belong to a synthetic test."""

    declaration_id: str
    purpose: str
    kind: ClassVar[str] = "synthetic"

    def __post_init__(self) -> None:
        _nonempty_text(self.declaration_id, "synthetic declaration_id")
        _nonempty_text(self.purpose, "synthetic purpose")


@dataclass(frozen=True)
class SourcedCoefficientProvenance:
    """Independent references for every physical coefficient admitted."""

    modulus: SourceReference
    poisson_ratio: SourceReference
    thickness: SourceReference
    kind: ClassVar[str] = "sourced"

    def __post_init__(self) -> None:
        if not all(
            isinstance(ref, SourceReference)
            for ref in (self.modulus, self.poisson_ratio, self.thickness)
        ):
            raise UnitsRefusal(
                UnitsReason.STRUCTURED_PROVENANCE_REQUIRED,
                "sourced provenance requires SourceReference records for modulus, "
                "Poisson ratio, and thickness",
            )


CoefficientProvenance = Union[
    SyntheticCoefficientProvenance, SourcedCoefficientProvenance
]
_PROVENANCE_TYPES = (SyntheticCoefficientProvenance, SourcedCoefficientProvenance)
_ADMISSION_SEAL = object()
_MISSING_PROVENANCE = object()


@dataclass(frozen=True)
class AdmittedMaterialV1:
    """Validated public material record; create only through the two admitters.

    `input_modulus_value` retains what the caller supplied.  The explicit unit
    and representation prevent a surface coefficient from being labelled Pa.
    `surface_*` fields are the exact coefficients consumed by the membrane.
    """

    representation: str
    input_modulus_value: float
    input_modulus_unit: str
    thickness_m: float
    poisson_ratio: float
    surface_young_modulus_n_per_m: float
    lambda_surface_n_per_m: float
    mu_surface_n_per_m: float
    bulk_surface_n_per_m: float
    provenance: CoefficientProvenance
    contract_version: str = CONTRACT_VERSION
    _admission_seal: InitVar[object] = None

    def __post_init__(self, _admission_seal: object) -> None:
        if _admission_seal is not _ADMISSION_SEAL:
            raise UnitsRefusal(
                UnitsReason.DIRECT_CONSTRUCTION_FORBIDDEN,
                "AdmittedMaterialV1 must be created by admit_volumetric_v1() or "
                "admit_surface_v1()",
            )


@dataclass(frozen=True)
class _KernelMaterialView:
    """Private compatibility protocol for law.evaluate_elastic.

    The historical validator reads E/nu/h and the kernel reads
    lambda_bar/mu_bar/h.  Here, and only here, `E` means E2 [N/m].
    """

    E: float
    nu: float
    h: float

    @property
    def lambda_bar(self) -> float:
        return float(self.E * self.nu / (1.0 - self.nu * self.nu))

    @property
    def mu_bar(self) -> float:
        return float(self.E / (2.0 * (1.0 + self.nu)))


@dataclass(frozen=True)
class PhysicalEvaluationV1:
    """Unit-labelled result that retains the exact admitted material record."""

    material: AdmittedMaterialV1
    evaluation: Evaluation
    contract_version: str = CONTRACT_VERSION

    @property
    def energy_j(self) -> float:
        return self.evaluation.energy

    @property
    def corner_forces_n(self) -> np.ndarray:
        return self.evaluation.corner_forces

    @property
    def vertex_forces_n(self) -> np.ndarray:
        return self.evaluation.vertex_forces

    @property
    def surface_energy_j_per_m2(self) -> np.ndarray:
        return self.evaluation.per_face.Wbar

    @property
    def volume_energy_j_per_m3(self) -> np.ndarray:
        return self.evaluation.per_face.w_vol


def _number(value: object, label: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, numbers.Real):
        raise UnitsRefusal(
            UnitsReason.NUMERIC_MATERIAL_REQUIRED,
            f"{label} must be a real number, excluding bool",
        )
    result = float(value)
    if not math.isfinite(result):
        raise UnitsRefusal(
            UnitsReason.NONFINITE_MATERIAL, f"{label} must be finite; got {value!r}"
        )
    return result


def _provenance(value: object) -> CoefficientProvenance:
    if not isinstance(value, _PROVENANCE_TYPES):
        raise UnitsRefusal(
            UnitsReason.STRUCTURED_PROVENANCE_REQUIRED,
            "provenance must be SyntheticCoefficientProvenance or "
            "SourcedCoefficientProvenance; dictionaries and fabricated defaults "
            "are not admitted",
        )
    if isinstance(value, SyntheticCoefficientProvenance):
        _nonempty_text(value.declaration_id, "synthetic declaration_id")
        _nonempty_text(value.purpose, "synthetic purpose")
    else:
        if not all(
            isinstance(ref, SourceReference)
            for ref in (value.modulus, value.poisson_ratio, value.thickness)
        ):
            raise UnitsRefusal(
                UnitsReason.STRUCTURED_PROVENANCE_REQUIRED,
                "sourced provenance requires SourceReference records for modulus, "
                "Poisson ratio, and thickness",
            )
        for label, ref in (
            ("modulus", value.modulus),
            ("poisson_ratio", value.poisson_ratio),
            ("thickness", value.thickness),
        ):
            _nonempty_text(ref.uri, f"{label} source uri")
            _nonempty_text(ref.locator, f"{label} source locator")
    return value


def _derive_surface_lame(surface: float, nu: float) -> tuple[float, float, float]:
    """Return lambda2, mu2, and independently derived lambda2+mu2 [N/m]."""
    denominator = 1.0 - nu * nu
    shear_denominator = 2.0 * (1.0 + nu)
    lambda2 = surface * nu / denominator
    mu2 = surface / shear_denominator
    # Derive bulk independently.  Near nu=-1, lambda+mu cancellation can erase
    # this positive quantity even though each coefficient remains finite.
    bulk2 = surface / (2.0 * (1.0 - nu))
    if not all(math.isfinite(v) for v in (lambda2, mu2, bulk2)):
        raise UnitsRefusal(
            UnitsReason.LAME_COEFFICIENT_OVERFLOW,
            "surface Lamé reduction overflowed float64",
        )
    nonzero_required = (mu2, bulk2) + ((lambda2,) if nu != 0.0 else ())
    if any(value == 0.0 or abs(value) < sys.float_info.min for value in nonzero_required):
        raise UnitsRefusal(
            UnitsReason.LAME_COEFFICIENT_UNDERFLOW,
            "a mathematically nonzero surface coefficient is zero or subnormal; "
            "the admitted relative-error model requires normal float64 arithmetic",
        )
    summed_bulk = lambda2 + mu2
    if not math.isfinite(summed_bulk):
        raise UnitsRefusal(
            UnitsReason.LAME_COEFFICIENT_OVERFLOW,
            "lambda2 + mu2 overflowed float64",
        )
    if summed_bulk <= 0.0 or abs(summed_bulk - bulk2) > _gamma(8) * abs(bulk2):
        raise UnitsRefusal(
            UnitsReason.LAME_PRECISION_LOSS,
            "lambda2 + mu2 lost the positive effective bulk coefficient to "
            "floating-point cancellation",
        )
    return float(lambda2), float(mu2), float(bulk2)


def _admitted(
    *,
    representation: str,
    input_modulus_value: float,
    input_modulus_unit: str,
    surface: float,
    thickness: float,
    nu: float,
    provenance: CoefficientProvenance,
) -> AdmittedMaterialV1:
    lambda2, mu2, bulk2 = _derive_surface_lame(surface, nu)
    return AdmittedMaterialV1(
        representation=representation,
        input_modulus_value=input_modulus_value,
        input_modulus_unit=input_modulus_unit,
        thickness_m=thickness,
        poisson_ratio=nu,
        surface_young_modulus_n_per_m=surface,
        lambda_surface_n_per_m=lambda2,
        mu_surface_n_per_m=mu2,
        bulk_surface_n_per_m=bulk2,
        provenance=provenance,
        _admission_seal=_ADMISSION_SEAL,
    )


def admit_volumetric_v1(
    young_modulus_3d_pa: object,
    thickness_m: object,
    poisson_ratio: object,
    *,
    provenance: object = _MISSING_PROVENANCE,
) -> AdmittedMaterialV1:
    """Admit E3d [Pa] and h [m], reducing exactly once to E2=E3d*h [N/m]."""
    e3d = _number(young_modulus_3d_pa, "young_modulus_3d_pa")
    h = _number(thickness_m, "thickness_m")
    nu = _number(poisson_ratio, "poisson_ratio")
    if e3d <= 0.0:
        raise UnitsRefusal(
            UnitsReason.NONPOSITIVE_YOUNG_MODULUS,
            f"young_modulus_3d_pa must be > 0; got {e3d}",
        )
    if h <= 0.0:
        raise UnitsRefusal(
            UnitsReason.NONPOSITIVE_THICKNESS, f"thickness_m must be > 0; got {h}"
        )
    if not -1.0 < nu < 0.5:
        raise UnitsRefusal(
            UnitsReason.POISSON_OUT_OF_RANGE,
            f"poisson_ratio must be in (-1, 1/2); got {nu}",
        )
    prov = _provenance(provenance)
    surface = e3d * h
    if not math.isfinite(surface):
        raise UnitsRefusal(
            UnitsReason.SURFACE_MODULUS_OVERFLOW,
            "young_modulus_3d_pa * thickness_m overflowed float64",
        )
    if surface == 0.0:
        raise UnitsRefusal(
            UnitsReason.SURFACE_MODULUS_UNDERFLOW,
            "positive young_modulus_3d_pa * thickness_m underflowed to zero",
        )
    return _admitted(
        representation="volumetric_E3d_times_h",
        input_modulus_value=e3d,
        input_modulus_unit="Pa",
        surface=surface,
        thickness=h,
        nu=nu,
        provenance=prov,
    )


def admit_surface_v1(
    surface_young_modulus_n_per_m: object,
    thickness_m: object,
    poisson_ratio: object,
    *,
    provenance: object = _MISSING_PROVENANCE,
) -> AdmittedMaterialV1:
    """Admit an already reduced E2 [N/m]; h is retained for w_vol only."""
    surface = _number(surface_young_modulus_n_per_m, "surface_young_modulus_n_per_m")
    h = _number(thickness_m, "thickness_m")
    nu = _number(poisson_ratio, "poisson_ratio")
    if surface <= 0.0:
        raise UnitsRefusal(
            UnitsReason.NONPOSITIVE_SURFACE_MODULUS,
            f"surface_young_modulus_n_per_m must be > 0; got {surface}",
        )
    if h <= 0.0:
        raise UnitsRefusal(
            UnitsReason.NONPOSITIVE_THICKNESS, f"thickness_m must be > 0; got {h}"
        )
    if not -1.0 < nu < 0.5:
        raise UnitsRefusal(
            UnitsReason.POISSON_OUT_OF_RANGE,
            f"poisson_ratio must be in (-1, 1/2); got {nu}",
        )
    prov = _provenance(provenance)
    return _admitted(
        representation="explicit_surface_E2",
        input_modulus_value=surface,
        input_modulus_unit="N/m",
        surface=surface,
        thickness=h,
        nu=nu,
        provenance=prov,
    )


def _validate_admitted(material: object) -> AdmittedMaterialV1:
    if not isinstance(material, AdmittedMaterialV1):
        raise UnitsRefusal(
            UnitsReason.MATERIAL_NOT_ADMITTED,
            "evaluate_physical_v1 requires an AdmittedMaterialV1",
        )
    if material.contract_version != CONTRACT_VERSION:
        raise UnitsRefusal(
            UnitsReason.MATERIAL_RECORD_INCONSISTENT,
            f"unsupported material contract {material.contract_version!r}",
        )
    _provenance(material.provenance)
    expected_surface = (
        material.input_modulus_value * material.thickness_m
        if material.representation == "volumetric_E3d_times_h"
        else material.input_modulus_value
        if material.representation == "explicit_surface_E2"
        else math.nan
    )
    expected_unit = (
        "Pa"
        if material.representation == "volumetric_E3d_times_h"
        else "N/m"
        if material.representation == "explicit_surface_E2"
        else None
    )
    expected_lam, expected_mu, expected_bulk = _derive_surface_lame(
        material.surface_young_modulus_n_per_m, material.poisson_ratio
    )
    if (
        expected_unit is None
        or material.input_modulus_unit != expected_unit
        or not math.isfinite(expected_surface)
        or material.surface_young_modulus_n_per_m != expected_surface
        or material.lambda_surface_n_per_m != expected_lam
        or material.mu_surface_n_per_m != expected_mu
        or material.bulk_surface_n_per_m != expected_bulk
    ):
        raise UnitsRefusal(
            UnitsReason.MATERIAL_RECORD_INCONSISTENT,
            "admitted material fields no longer match their representation and "
            "derived surface coefficients",
        )
    return material


def _kernel_view(material: AdmittedMaterialV1) -> _KernelMaterialView:
    """Make the sole compatibility view accepted by the unchanged validator/kernel."""
    return _KernelMaterialView(
        E=material.surface_young_modulus_n_per_m,
        nu=material.poisson_ratio,
        h=material.thickness_m,
    )


def _evaluate_kernel(rest, material_view: _KernelMaterialView, positions) -> Evaluation:
    return evaluate_elastic(rest, material_view, positions)


def _bounded_close(actual, expected, operations: int, scale) -> bool:
    a = np.asarray(actual, dtype=np.float64)
    e = np.asarray(expected, dtype=np.float64)
    s = np.asarray(scale, dtype=np.float64)
    if a.shape != e.shape or not (np.isfinite(a).all() and np.isfinite(e).all()):
        return False
    if not np.isfinite(s).all() or np.any(s < 0.0):
        return False
    return bool(np.all(np.abs(a - e) <= _gamma(operations) * s))


def _validate_output(rest, material: AdmittedMaterialV1, result: object) -> Evaluation:
    if not isinstance(result, Evaluation):
        raise UnitsRefusal(
            UnitsReason.OUTPUT_MALFORMED,
            "kernel did not return an Evaluation record",
        )
    face = result.per_face
    expected_shapes = {
        "F": (rest.n_faces, 3, 2),
        "C": (rest.n_faces, 2, 2),
        "E": (rest.n_faces, 2, 2),
        "S": (rest.n_faces, 2, 2),
        "P": (rest.n_faces, 3, 2),
        "Wbar": (rest.n_faces,),
        "w_vol": (rest.n_faces,),
        "detF": (rest.n_faces,),
        "area_cur": (rest.n_faces,),
        "normals_cur": (rest.n_faces, 3),
        "corner_forces": (rest.n_faces, 3, 3),
        "vertex_forces": (rest.n_vertices, 3),
    }
    try:
        arrays = {
            "F": face.F,
            "C": face.C,
            "E": face.E,
            "S": face.S,
            "P": face.P,
            "Wbar": face.Wbar,
            "w_vol": face.w_vol,
            "detF": face.detF,
            "area_cur": face.area_cur,
            "normals_cur": face.normals_cur,
            "corner_forces": result.corner_forces,
            "vertex_forces": result.vertex_forces,
        }
    except (AttributeError, TypeError) as exc:
        raise UnitsRefusal(
            UnitsReason.OUTPUT_MALFORMED,
            "kernel Evaluation is missing a required face or force field",
        ) from exc
    for name, value in arrays.items():
        try:
            array = np.asarray(value, dtype=np.float64)
        except (TypeError, ValueError, OverflowError) as exc:
            raise UnitsRefusal(
                UnitsReason.OUTPUT_MALFORMED,
                f"kernel output {name} is not a numeric array",
            ) from exc
        if array.shape != expected_shapes[name]:
            raise UnitsRefusal(
                UnitsReason.OUTPUT_MALFORMED,
                f"kernel output {name} has shape {array.shape}; expected "
                f"{expected_shapes[name]}",
            )
        if not np.all(np.isfinite(array)):
            raise UnitsRefusal(
                UnitsReason.OUTPUT_NONFINITE, f"kernel output {name} is nonfinite"
            )
    scalars = (result.energy, result.max_abs_vertex_force, result.energy_scale)
    if not all(isinstance(v, numbers.Real) and math.isfinite(float(v)) for v in scalars):
        raise UnitsRefusal(
            UnitsReason.OUTPUT_NONFINITE, "kernel output contains a nonfinite scalar"
        )
    inverted = np.asarray(face.inverted)
    if inverted.shape != (rest.n_faces,) or inverted.dtype.kind != "b":
        raise UnitsRefusal(
            UnitsReason.OUTPUT_MALFORMED,
            "kernel output inverted must be one bool per face",
        )

    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        expected_w_vol = np.asarray(face.Wbar, dtype=np.float64) / material.thickness_m
    w_scale = np.maximum(np.abs(expected_w_vol), np.finfo(np.float64).tiny)
    if not np.all(np.isfinite(expected_w_vol)):
        raise UnitsRefusal(
            UnitsReason.OUTPUT_NONFINITE,
            "Wbar/thickness_m is not representable as finite float64",
        )
    if not _bounded_close(face.w_vol, expected_w_vol, 4, w_scale):
        raise UnitsRefusal(
            UnitsReason.OUTPUT_DIMENSION_MISMATCH,
            "w_vol does not equal Wbar/thickness_m within gamma(4)",
        )

    with np.errstate(over="ignore", invalid="ignore"):
        energy_terms = np.asarray(face.Wbar, dtype=np.float64) * np.asarray(
            rest.areas0, dtype=np.float64
        )
        expected_energy = float(np.sum(energy_terms))
        absolute_energy_sum = float(np.sum(np.abs(energy_terms)))
    if not (
        np.all(np.isfinite(energy_terms))
        and math.isfinite(expected_energy)
        and math.isfinite(absolute_energy_sum)
    ):
        raise UnitsRefusal(
            UnitsReason.OUTPUT_NONFINITE,
            "A0*Wbar or its energy reduction overflowed float64",
        )
    energy_scale = max(absolute_energy_sum, np.finfo(np.float64).tiny)
    if not _bounded_close(
        result.energy, expected_energy, 2 * rest.n_faces + 4, energy_scale
    ):
        raise UnitsRefusal(
            UnitsReason.OUTPUT_DIMENSION_MISMATCH,
            "energy does not equal sum(A0*Wbar) within its derived reduction bound",
        )
    expected_max = float(np.max(np.abs(result.vertex_forces)))
    max_scale = max(expected_max, np.finfo(np.float64).tiny)
    if not _bounded_close(result.max_abs_vertex_force, expected_max, 2, max_scale):
        raise UnitsRefusal(
            UnitsReason.OUTPUT_DIMENSION_MISMATCH,
            "max_abs_vertex_force does not match the full vertex-force array",
        )
    with np.errstate(over="ignore", invalid="ignore"):
        total_area = float(np.sum(np.asarray(rest.areas0, dtype=np.float64)))
        expected_scale = (
            material.lambda_surface_n_per_m + material.mu_surface_n_per_m
        ) * total_area
    if not (math.isfinite(total_area) and math.isfinite(expected_scale)):
        raise UnitsRefusal(
            UnitsReason.OUTPUT_NONFINITE,
            "surface coefficient times total reference area overflowed float64",
        )
    scale_unit = max(abs(expected_scale), np.finfo(np.float64).tiny)
    if not _bounded_close(result.energy_scale, expected_scale, rest.n_faces + 8, scale_unit):
        raise UnitsRefusal(
            UnitsReason.OUTPUT_DIMENSION_MISMATCH,
            "energy_scale does not use admitted surface Lamé coefficients",
        )
    return result


def evaluate_physical_v1(rest, material: AdmittedMaterialV1, positions) -> PhysicalEvaluationV1:
    """Evaluate U [J], forces [N], Wbar [J/m2], and w_vol [J/m3]."""
    admitted = _validate_admitted(material)
    result = _evaluate_kernel(rest, _kernel_view(admitted), positions)
    return PhysicalEvaluationV1(
        material=admitted,
        evaluation=_validate_output(rest, admitted, result),
    )


__all__ = [
    "CONTRACT_VERSION",
    "AdmittedMaterialV1",
    "PhysicalEvaluationV1",
    "SourceReference",
    "SourcedCoefficientProvenance",
    "SyntheticCoefficientProvenance",
    "UnitsReason",
    "UnitsRefusal",
    "admit_surface_v1",
    "admit_volumetric_v1",
    "evaluate_physical_v1",
]
