"""material_contract.py — THE MATERIAL CONTRACT (G01, 2026-09-06).

The law this module implements is registered in docs/FOUNDATION_G01_REPORT.md
prediction P-8 (a..j), written BEFORE this file existed:

  Every material property carries: value, unit, source locator, validity
  domain/conditions, and provenance class (researched | parent | derived).
  Missing information produces a NAMED refusal -- never a zero, never a
  default, never an invented constant. Unit conversions happen only inside
  the registered families; anything outside is refused, not converted on
  faith. Derived values carry their arithmetic and the inputs that close it.

Refusal kinds (each check asserts the exact kind):
  MISSING_INPUT       the property is not published in any ingested source
  MISSING_BASIS       a derivation is possible but its required basis was
                      not declared (e.g. SG -> kg/m^3 needs the reference
                      density + conditioning basis)
  UNKNOWN_UNIT        the unit is not in the registry; no conversion is
                      invented for it
  PHYSICALLY_INVALID  the value violates its own physics (negative density,
                      nonpositive modulus, fraction outside [0, 1])
  NONFINITE           NaN/inf values are refused at the door
  UNSUPPORTED_MODEL   the requested material model is outside what the
                      record's sources support
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum


# ── provenance and refusals ──────────────────────────────────────────────────

class Provenance(Enum):
    RESEARCHED = "researched"   # published value, locator attached
    PARENT = "parent"           # read through from a parent store, never copied
    DERIVED = "derived"         # computed by THIS contract; arithmetic attached


class RefusalKind(Enum):
    MISSING_INPUT = "missing_input"
    MISSING_BASIS = "missing_basis"
    UNKNOWN_UNIT = "unknown_unit"
    PHYSICALLY_INVALID = "physically_invalid"
    NONFINITE = "nonfinite"
    UNSUPPORTED_MODEL = "unsupported_model"


class ContractRefusal(Exception):
    """A NAMED refusal. kind is machine-checkable; detail names the exact
    missing/invalid thing (a property name, a unit, a basis requirement)."""

    def __init__(self, kind: RefusalKind, detail: str):
        super().__init__(f"{kind.value}: {detail}")
        self.kind = kind
        self.detail = detail


# ── the unit registry: conversions exist ONLY here ───────────────────────────

# family -> {unit -> scale to the family's canonical unit}. A conversion is
# legal iff both units are registered in the SAME family. Anything else is
# UNKNOWN_UNIT -- the contract never invents a factor (P-8c).
_UNIT_FAMILIES: dict[str, dict[str, float]] = {
    "pressure":    {"pa": 1.0, "kpa": 1e3, "mpa": 1e6, "gpa": 1e9},
    "density":     {"kg/m^3": 1.0, "g/cm^3": 1e3},
    "length":      {"m": 1.0, "mm": 1e-3, "cm": 1e-2},
    "energy_area": {"j/m^2": 1.0},
    "stiffness":   {"n/m^3": 1.0},
    "dimensionless": {"1": 1.0, "ratio": 1.0, "sg": 1.0},
}


def _norm_unit(unit: str) -> str:
    return unit.strip().lower()


def convert(value: float, unit_from: str, unit_to: str) -> float:
    u, v = _norm_unit(unit_from), _norm_unit(unit_to)
    if u == v:
        return value
    fam_from = fam_to = None
    for fam, table in _UNIT_FAMILIES.items():
        if u in table:
            fam_from = fam
        if v in table:
            fam_to = fam
    if fam_from is None:
        raise ContractRefusal(RefusalKind.UNKNOWN_UNIT,
                              f"unit '{unit_from}' is not registered; no "
                              f"conversion factor may be invented for it")
    if fam_to is None:
        raise ContractRefusal(RefusalKind.UNKNOWN_UNIT,
                              f"unit '{unit_to}' is not registered; no "
                              f"conversion factor may be invented for it")
    if fam_from != fam_to:
        raise ContractRefusal(RefusalKind.UNKNOWN_UNIT,
                              f"'{unit_from}' and '{unit_to}' are in different "
                              f"unit families ({fam_from} vs {fam_to}); "
                              f"cross-family conversion is not registered")
    return value * _UNIT_FAMILIES[fam_from][u] / _UNIT_FAMILIES[fam_to][v]


# ── records ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class MaterialProperty:
    name: str
    value: float
    unit: str
    source: str                 # exact locator (table/figure/DOI-ish string)
    conditions: str             # validity domain, stated by the source
    provenance: Provenance
    derivation: str | None = None   # required when provenance is DERIVED

    def __post_init__(self) -> None:
        # THE DOOR (2026-09-06, found by P-8c/d/e): validation happens at
        # CONSTRUCTION, not only at add() -- the 2026-09-06 run showed a bare
        # MaterialProperty(psi / negative / NaN) bypassed the record gate.
        # A property cannot exist unvalidated in this contract.
        _validate_property(self)


def _validate_property(p: MaterialProperty) -> None:
    """Physics and hygiene gates at the door (P-8d, P-8e, P-8c)."""
    if isinstance(p.value, float) and (math.isnan(p.value) or math.isinf(p.value)):
        raise ContractRefusal(RefusalKind.NONFINITE,
                              f"{p.name} value is not finite ({p.value})")
    if p.provenance is Provenance.DERIVED and not p.derivation:
        raise ContractRefusal(RefusalKind.MISSING_BASIS,
                              f"{p.name} is declared derived but carries no "
                              f"derivation (arithmetic + inputs)")
    if _norm_unit(p.unit) not in {u for t in _UNIT_FAMILIES.values() for u in t}:
        raise ContractRefusal(RefusalKind.UNKNOWN_UNIT,
                              f"{p.name} unit '{p.unit}' is not registered; "
                              f"register it with a family or do not ship it")
    # physical validity by property class
    n = p.name.lower()
    if "density" in n and p.value <= 0:
        raise ContractRefusal(RefusalKind.PHYSICALLY_INVALID,
                              f"{p.name} = {p.value} {p.unit}: density must "
                              f"be positive")
    if n.startswith("e_") or n.startswith("g_") or n in ("E", "K_IC") or "modulus" in n:
        if p.value <= 0:
            raise ContractRefusal(RefusalKind.PHYSICALLY_INVALID,
                                  f"{p.name} = {p.value} {p.unit}: a modulus/"
                                  f"stiffness must be positive")
    if ("fraction" in n or n.startswith("v_")) and not (0.0 <= p.value <= 1.0):
        raise ContractRefusal(RefusalKind.PHYSICALLY_INVALID,
                              f"{p.name} = {p.value}: a fraction must lie in [0, 1]")


@dataclass
class MaterialRecord:
    name: str
    models: frozenset[str]              # model claims the sources support
    properties: dict[str, MaterialProperty] = field(default_factory=dict)
    notes: str = ""

    def add(self, prop: MaterialProperty) -> None:
        _validate_property(prop)
        self.properties[prop.name] = prop


# ── the contract ─────────────────────────────────────────────────────────────

class MaterialContract:
    """One store of records; bindings REFERENCE records (no per-geometry
    copies), so a mutation of a shared record propagates to every binding."""

    def __init__(self) -> None:
        self._materials: dict[str, MaterialRecord] = {}

    def register(self, record: MaterialRecord) -> None:
        if record.name in self._materials:
            raise ContractRefusal(RefusalKind.MISSING_INPUT,
                                  f"material '{record.name}' already registered")
        self._materials[record.name] = record

    def record(self, name: str) -> MaterialRecord:
        rec = self._materials.get(name)
        if rec is None:
            raise ContractRefusal(RefusalKind.MISSING_INPUT,
                                  f"no material named '{name}' is registered")
        return rec

    # -- property access -----------------------------------------------------

    def get(self, material: str, prop: str, as_unit: str | None = None) -> MaterialProperty:
        rec = self.record(material)
        p = rec.properties.get(prop)
        if p is None:
            raise ContractRefusal(
                RefusalKind.MISSING_INPUT,
                f"'{material}' has no published '{prop}' in any ingested "
                f"source; the contract refuses to default it")
        if as_unit is not None:
            converted = convert(p.value, p.unit, as_unit)
            return MaterialProperty(name=p.name, value=converted, unit=as_unit,
                                    source=p.source, conditions=p.conditions,
                                    provenance=p.provenance,
                                    derivation=p.derivation)
        return p

    def model(self, material: str, model: str) -> None:
        """Model claims: raises UNSUPPORTED_MODEL if the record's sources do
        not carry that model (P-8j)."""
        rec = self.record(material)
        if model not in rec.models:
            raise ContractRefusal(
                RefusalKind.UNSUPPORTED_MODEL,
                f"'{material}' does not support model '{model}' (supported: "
                f"{sorted(rec.models)}); no isotropic or 3D claim may be "
                f"invented from uniaxial data")

    # -- declared-basis derivations -------------------------------------------

    def density_from_sg(self, material: str, basis_kg_m3: float,
                        basis_conditions: str) -> MaterialProperty:
        """SG (specific gravity) -> density REQUIRES a declared reference
        basis. Without it: MISSING_BASIS (P-8i). With it: a DERIVED value
        whose derivation string carries the arithmetic (P-8i second half).
        The basis itself is validated (positive, finite) -- a garbage basis
        is refused, not divided through."""
        if math.isnan(basis_kg_m3) or math.isinf(basis_kg_m3) or basis_kg_m3 <= 0:
            raise ContractRefusal(RefusalKind.PHYSICALLY_INVALID,
                                  "reference basis density must be a positive "
                                  "finite kg/m^3 value with stated conditions")
        sg = self.get(material, "SG")
        if _norm_unit(sg.unit) not in ("sg", "1", "ratio"):
            raise ContractRefusal(RefusalKind.UNKNOWN_UNIT,
                                  f"SG property carries unit '{sg.unit}', not "
                                  f"a dimensionless specific gravity")
        val = sg.value * basis_kg_m3
        return MaterialProperty(
            name="derived:density", value=val, unit="kg/m^3",
            source=(f"derived from {material}.SG = {sg.value} ({sg.source}) "
                    f"x declared basis {basis_kg_m3} kg/m^3 ({basis_conditions})"),
            conditions=f"{sg.conditions}; basis: {basis_conditions}",
            provenance=Provenance.DERIVED,
            derivation=(f"rho = SG x rho_ref = {sg.value} x {basis_kg_m3} "
                        f"= {val} kg/m^3"))


# ── orthotropic stiffness + material frame validation (P-8f, P-8g) ───────────

def validate_orthotropic(C: "list[list[float]] | object",
                         frame: "list[tuple[float, float, float]] | None" = None,
                         tol: float = 1e-9) -> None:
    """C: 6x6 stiffness (Voigt). Checks, each with its named convention:
      symmetry        C must equal C^T (orthotropic constitutive law)
      positive        all eigenvalues > 0 (stored elastic energy > 0)
      frame           the material frame's axes must be orthonormal
    Raises ContractRefusal naming the FIRST violated convention."""
    try:
        import numpy as np
    except ImportError:  # pragma: no cover - numpy is a repo baseline
        raise
    M = np.asarray(C, dtype=float)
    if M.shape != (6, 6):
        raise ContractRefusal(RefusalKind.PHYSICALLY_INVALID,
                              f"stiffness must be 6x6 Voigt, got {M.shape}")
    asym = float(np.abs(M - M.T).max())
    if asym > tol:
        raise ContractRefusal(RefusalKind.PHYSICALLY_INVALID,
                              f"orthotropic symmetry violated: max|C - C^T| = "
                              f"{asym:.3e} > {tol:.1e} (Voigt convention)")
    eig = np.linalg.eigvalsh(0.5 * (M + M.T))
    if eig.min() <= 0.0:
        raise ContractRefusal(RefusalKind.PHYSICALLY_INVALID,
                              f"stiffness is not positive definite: min "
                              f"eigenvalue {eig.min():.6e} <= 0")
    if frame is not None:
        E = np.asarray(frame, dtype=float)
        if E.shape != (3, 3):
            raise ContractRefusal(RefusalKind.PHYSICALLY_INVALID,
                                  "material frame must be 3 axis vectors")
        gram = E @ E.T
        dev = float(np.abs(gram - np.eye(3)).max())
        if dev > 1e-9:
            raise ContractRefusal(RefusalKind.PHYSICALLY_INVALID,
                                  f"material frame is not orthonormal: "
                                  f"max|E E^T - I| = {dev:.3e}")


# ── bindings: one record, many geometries (P-8h) ─────────────────────────────

@dataclass
class Binding:
    geometry_id: str
    material: str
    _contract: "MaterialContract"

    def get(self, prop: str, as_unit: str | None = None) -> MaterialProperty:
        # dereferences the SHARED record at call time: mutations propagate.
        return self._contract.get(self.material, prop, as_unit)


def bind(contract: MaterialContract, material: str, geometry_id: str) -> Binding:
    contract.record(material)      # refuse to bind an unknown material
    return Binding(geometry_id=geometry_id, material=material, _contract=contract)


# ── the white_oak record, built from the repo's own sourced store ────────────

def build_white_oak_record() -> MaterialRecord:
    """Sourced from tools/matter_data.py (USDA FPL GTR-190, Table 5-3b and
    Table 5-1), provenance carried through as RESEARCHED. Only properties
    the Handbook table actually publishes are added -- G_LT/G_TR absolutes
    and Poisson's ratios are NOT published there, so they are absent, and
    `get` refuses them by name (P-8b)."""
    import matter_data

    wood = matter_data.WOOD["white_oak"]
    rec = MaterialRecord(
        name="white_oak",
        models=frozenset({"uniaxial_along_grain", "orthotropic_ratios"}),
        notes="clear straight-grained wood at 12% moisture content",
    )
    CONDITIONS = "clear straight-grained wood, 12% MC"
    # Only properties the Handbook tables actually publish enter the record.
    # G_LT/G_TR absolutes and Poisson's ratios are NOT published -> absent,
    # and get() refuses them by name (P-8b). Each entry's own source string,
    # unit and provenance are carried through verbatim.
    for prop_name in ("E_L", "MOR", "shear_par", "tens_perp", "SG",
                      "ET_EL", "ER_EL", "GLR_EL"):
        entry = wood.get(prop_name)
        if entry is None:
            continue
        note = entry.get("note")
        rec.add(MaterialProperty(
            name=prop_name, value=float(entry["value"]),
            unit=str(entry["unit"]), source=str(entry["source"]),
            conditions=(f"{note}; {CONDITIONS}" if note else CONDITIONS),
            provenance=Provenance.RESEARCHED))
    return rec
