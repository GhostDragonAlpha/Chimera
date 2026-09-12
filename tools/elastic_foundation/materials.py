"""materials.py -- elastic sheet material parameters, admissibility, named refusals.

Isotropic plane-stress pair (lambda_bar, mu_bar) derived from (E, nu): the standard thin-plate
plane-stress reduction (DERIVATION.md section 3). Admissible: E > 0, h > 0, nu in (-1, 1/2).
Anything else is a named refusal. Orthotropic requests are refused by name because the repo has
no material-direction transport and no measured E11/E22/nu12/G12 (AUDIT.md sections 2,3).
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path

import numpy as np


class InvalidMaterial(ValueError):
    """Named refusal for an inadmissible or unsupported material request."""

    def __init__(self, reason: str, message: str):
        super().__init__(message)
        self.reason = reason
        self.message = message


class MaterialReason:
    NONPOSITIVE_E = "nonpositive_young_modulus"
    NONFINITE = "nonfinite_material"
    NU_OUT_OF_RANGE = "poisson_out_of_range"
    NONPOSITIVE_THICKNESS = "nonpositive_thickness"
    ORTHOTROPIC_UNSUPPORTED = "orthotropic_unsupported"
    POISSON_RATIO_NOT_MEASURED = "poisson_ratio_not_measured"
    UNKNOWN_MATERIAL = "unknown_material"
    LIBRARY_MISSING = "library_missing"


@dataclass(frozen=True)
class ElasticMaterial2D:
    """Immutable isotropic plane-stress sheet material. Units: E Pa, nu dimless, h m."""
    E: float
    nu: float
    h: float
    name: str = "synthetic"
    provenance: str = "synthetic-test"
    build_info: dict = field(default_factory=dict)

    @property
    def lambda_bar(self) -> float:
        return float(self.E * self.nu / (1.0 - self.nu * self.nu))

    @property
    def mu_bar(self) -> float:
        return float(self.E / (2.0 * (1.0 + self.nu)))

    @property
    def bulk2d(self) -> float:
        return self.lambda_bar + self.mu_bar

    @property
    def stiffness_scale(self) -> float:
        return self.lambda_bar + self.mu_bar   # O(W_bar/E-strain^2) prefactor, for budgets


def validate_material(m: ElasticMaterial2D) -> None:
    """Admissibility gate (DERIVATION.md section 3). A violation is a named refusal."""
    if not (np.isfinite(m.E) and np.isfinite(m.nu) and np.isfinite(m.h)):
        raise InvalidMaterial(MaterialReason.NONFINITE,
                              "E/nu/h must all be finite")
    if not m.E > 0.0:
        raise InvalidMaterial(MaterialReason.NONPOSITIVE_E,
                              f"Young modulus must be > 0; got {m.E}")
    if not (-1.0 < m.nu < 0.5):
        raise InvalidMaterial(
            MaterialReason.NU_OUT_OF_RANGE,
            f"nu must be in (-1, 1/2) for a positive-definite 2D quadratic form; got {m.nu}")
    if not m.h > 0.0:
        raise InvalidMaterial(MaterialReason.NONPOSITIVE_THICKNESS,
                              f"thickness must be > 0; got {m.h}")


def require_isotropic(m) -> None:
    """The named orthotropic refusal. Lists what a defensible anisotropic port needs."""
    raise InvalidMaterial(
        MaterialReason.ORTHOTROPIC_UNSUPPORTED,
        "isotropic law only. An orthotropic extension needs, per face: material axes and their "
        "transport rule (the geometric rest basis (t1,t2) is a computational frame, not a "
        "material frame); E11, E22, nu12, G12; and a thickness-direction convention. None of "
        "these exist in the repo's measured data, so the parameter set would be invented -- "
        "refusing by name instead (DERIVATION.md section 7).")


def material_from_library(name: str, h: float = 1.0, repo_root="") -> ElasticMaterial2D:
    """Read a real material's Young modulus from the repo's researched library.

    The library measures E for some materials but no Poisson ratio anywhere (AUDIT.md section 3).
    A real-material port therefore refuses by name rather than invent nu. Only a synthetic
    material may carry a declared (test) nu.
    """
    root = Path(repo_root) if repo_root else Path(__file__).resolve().parent.parent.parent
    lib_path = root / "Chimera" / "docs" / "matter" / "matter_library.json"
    if not lib_path.exists():
        raise InvalidMaterial(MaterialReason.LIBRARY_MISSING,
                              f"materials library missing at {lib_path}; cannot port a real "
                              f"material -- refusing rather than inventing parameters")
    lib = json.loads(lib_path.read_text(encoding="utf8"))
    mat = (lib.get("materials") or {}).get(name)
    if mat is None:
        raise InvalidMaterial(MaterialReason.UNKNOWN_MATERIAL,
                              f"library holds no material {name!r}")
    ent = (mat.get("physical") or {}).get("youngs_modulus_gpa")
    if not ent:
        raise InvalidMaterial(MaterialReason.UNKNOWN_MATERIAL,
                              f"material {name!r} publishes no youngs_modulus_gpa")
    E = float(ent["mean"]) * 1e9 if str(ent.get("unit", "gpa")).lower() == "gpa" else float(ent["mean"])
    raise InvalidMaterial(
        MaterialReason.POISSON_RATIO_NOT_MEASURED,
        f"material {name!r} measures E={E:.6g} Pa but the library holds no poisson ratio for it; "
        f"an isotropic plane-stress sheet needs nu in (-1, 1/2). Refusing by name instead of "
        f"inventing a Poisson ratio or an empirical shear relationship.")


def synthetic(name="synthetic", E=1.0, nu=0.3, h=1.0) -> ElasticMaterial2D:
    """A declared synthetic test material; the only sanctioned source of arbitrary (E, nu, h)."""
    return ElasticMaterial2D(E=E, nu=nu, h=h, name=name, provenance="synthetic-test")