"""mat02_reference_model.py -- independent reference model of catalogue card
MAT-02 "Constitutive capability matrix" (holodeck-mat-02).
Card: STATEMENT "Explicit supported model and required-parameter registry";
PREDICTION "Missing inputs prevent unsupported capability claims"; FALSIFIER
"Density and one modulus are assumed sufficient for every response";
MATHEMATICS "isotropy; orthotropy; state variables; model domains".
UNITS BACKBONE (citation duty): dimensional analysis defers to MATH-01's
integrated typed-quantity algebra (../../MATH/MATH-01/reference/
math01_reference_model.py -- exact Fraction (L,M,T) Dimensions, Quantity with
named `dimension_mismatch` refusals). Independence is claimed from the AUDITED
deployed code (tools/material_contract.py, tools/elastic_foundation/
materials.py), not from MATH-01. This model adds the CAPABILITY layer: a
closed registry of supported constitutive models, each declaring required
typed parameters, required state variables, a declared validity domain, and
the DERIVED independent-constant count of its symmetry class. NO registered
model admits density as a stiffness constant (the falsifier's structural
negation). Derived counts (constant origin, GOV-03 discipline): isotropy = 2
(C = lambda d_ij d_kl + mu(d_ik d_jl + d_il d_jk)); orthotropy = 9 (12 written
constants with the three reciprocity relations nu_ij/E_i = nu_ji/E_j).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

_MATH01_DIR = (Path(__file__).resolve().parents[3] / "MATH" / "MATH-01"
               / "reference")
sys.path.insert(0, str(_MATH01_DIR))
import math01_reference_model as m01  # noqa: E402

R_UNKNOWN_MODEL = "unknown_model"
R_MISSING_INPUT = "missing_input"
R_DIMENSION_MISMATCH = "dimension_mismatch"
R_PHYSICALLY_INVALID = "physically_invalid"
R_MISSING_STATE = "missing_state"
R_STATE_OUT_OF_DOMAIN = "state_out_of_domain"
R_UNSUPPORTED_RESPONSE = "unsupported_response"
R_UNSUPPORTED_DERIVATION = "unsupported_derivation"
R_INCOMPLETE_SPEC = "incomplete_spec"
R_FROZEN = "matrix_frozen"

_DENSITY_NOTE = ("density is not a stiffness constant: rho carries the "
                 "(L^-3 M) dimension and counts toward NO model's "
                 "independent stiffness constants")


class Mat02Refusal(ValueError):
    """Named refusal of the capability registry."""

    def __init__(self, reason: str, message: str):
        super().__init__(message)
        self.reason = reason
        self.message = message

    def __repr__(self):
        return f"Mat02Refusal({self.reason!r}, {self.message!r})"


GATE_POSITIVE = "positive"
GATE_FRACTION = "fraction"          # [0, 1]
GATE_NU_RANGE = "nu_range"          # (-1, 1/2): positive-definite 2D form

# dimensions used by the registry (all through MATH-01's exact algebra)
DIM_RHO = m01.Dimension((-3, 1, 0))     # kg m^-3
DIM_PA = m01.Dimension.PA               # kg m^-1 s^-2
DIM_DIMLESS = m01.Dimension.DIMENSIONLESS
DIM_M = m01.Dimension.M
DIM_L3 = m01.Dimension((3, 0, 0))       # m^3
DIM_MASS = m01.Dimension.KG


@dataclass(frozen=True)
class Requirement:
    """A required parameter: declared name, MATH-01 Dimension, value gate."""

    name: str
    dimension: object
    gate: str

    def check(self, q) -> None:
        if not isinstance(q, m01.Quantity) or q.dimension != self.dimension:
            have = (type(q).__name__ if not isinstance(q, m01.Quantity)
                    else str(q.dimension))
            raise Mat02Refusal(
                R_DIMENSION_MISMATCH, f"{self.name} must be a MATH-01 "
                f"Quantity of {self.dimension}, got {have}")
        v = q.value
        if self.gate == GATE_POSITIVE and not v > 0.0:
            raise Mat02Refusal(R_PHYSICALLY_INVALID,
                               f"{self.name} = {v} must be positive")
        if self.gate == GATE_FRACTION and not 0.0 <= v <= 1.0:
            raise Mat02Refusal(R_PHYSICALLY_INVALID,
                               f"{self.name} = {v} must lie in [0, 1]")
        if self.gate == GATE_NU_RANGE and not -1.0 < v < 0.5:
            raise Mat02Refusal(R_PHYSICALLY_INVALID, f"{self.name} = {v} "
                               "must lie in (-1, 1/2) for a positive-definite "
                               "quadratic form")


@dataclass(frozen=True)
class StateVariable:
    """A required state variable with a declared acceptance check."""

    name: str
    kind: str                 # "nonempty" | "range"
    bounds: tuple = None

    def check(self, value) -> None:
        if self.kind == "nonempty":
            if value is None or (hasattr(value, "__len__") and not len(value)):
                raise Mat02Refusal(R_STATE_OUT_OF_DOMAIN,
                                   f"state '{self.name}' is empty")
        else:
            lo, hi = self.bounds
            if not (isinstance(value, (int, float)) and lo <= value <= hi):
                raise Mat02Refusal(R_STATE_OUT_OF_DOMAIN,
                                   f"state '{self.name}' = {value!r} outside "
                                   f"its declared band {self.bounds}")


@dataclass(frozen=True)
class ModelSpec:
    """One supported constitutive model: the card statement's registry row."""

    model_id: str
    response_family: str
    required: tuple                    # primary Requirement set
    domain: str                        # declared validity domain (nonempty)
    symmetry_class: str
    constant_origin: str               # derivation of the constant count
    independent_constant_count: int
    alternatives: tuple = ()           # other declared complete sets
    required_state: tuple = ()         # names (declared-state mathematics)
    state_variables: tuple = ()        # StateVariable specs


def _validated(spec: ModelSpec) -> ModelSpec:
    """Constructor gate: an incomplete spec is refused at REGISTRATION time
    (the GOV-03 missing_domain / missing_constant_origin analog)."""
    missing = []
    if not spec.model_id or not spec.response_family:
        missing.append("model_id/response_family")
    if not spec.domain or not spec.domain.strip():
        missing.append("domain")
    if not spec.required:
        missing.append("required")
    for r in spec.required:
        if not isinstance(r, Requirement) or not isinstance(
                r.dimension, m01.Dimension):
            missing.append(f"untyped:{getattr(r, 'name', r)!r}")
    if not spec.constant_origin or not spec.constant_origin.strip():
        missing.append("constant_origin")
    if spec.independent_constant_count <= 0:
        missing.append("independent_constant_count")
    if missing:
        raise Mat02Refusal(R_INCOMPLETE_SPEC, f"spec {spec.model_id!r} is "
                           f"incomplete: {sorted(missing)}")
    return spec


@dataclass(frozen=True)
class CapabilityClaim:
    """The successful claim token: what the model now licenses, on what
    basis. Frozen; no arithmetic of its own."""

    model_id: str
    response_family: str
    satisfied: tuple
    basis: str


def _check_set(reqs, params):
    """missing_input names EVERY absent parameter; then the typed gates."""
    missing = [r.name for r in reqs if r.name not in params]
    if missing:
        note = ("; " + _DENSITY_NOTE) if "rho" in params else ""
        raise Mat02Refusal(R_MISSING_INPUT, f"missing required inputs "
                           f"{missing}; the capability claim is refused, "
                           f"never defaulted{note}")
    for r in reqs:
        r.check(params[r.name])


def _pair_gate(reqs, values):
    missing = [r.name for r in reqs if r.name not in values]
    if missing:
        note = ("; " + _DENSITY_NOTE) if "rho" in values else ""
        raise Mat02Refusal(R_MISSING_INPUT, f"missing required inputs "
                           f"{missing}; the claim is refused, never "
                           f"defaulted{note}")
    for r in reqs:
        r.check(values[r.name])


def mass(values):
    """rho x volume -> mass. The ONE response density alone supports."""
    _pair_gate((Requirement("rho", DIM_RHO, GATE_POSITIVE),), values)
    volume = values.get("volume")
    if not isinstance(volume, m01.Quantity) or volume.dimension != DIM_L3:
        have = (str(volume.dimension) if isinstance(volume, m01.Quantity)
                else type(volume).__name__)
        raise Mat02Refusal(R_DIMENSION_MISMATCH, f"volume must be a MATH-01 "
                           f"Quantity of L^3, got {have}")
    out = values["rho"] * volume
    if out.dimension != DIM_MASS:
        raise Mat02Refusal(R_DIMENSION_MISMATCH,
                           f"rho x V composed to {out.dimension}, not mass")
    return out


def shear_from_E_nu(values):
    """G = E / (2(1+nu)) -- the declared isotropy relation; legal only with
    BOTH inputs present (nu is never assumed from E, and never from rho)."""
    _pair_gate((Requirement("E", DIM_PA, GATE_POSITIVE),
                Requirement("nu", DIM_DIMLESS, GATE_NU_RANGE)), values)
    return values["E"] / m01.Quantity(2.0 * (1.0 + values["nu"].value),
                                      DIM_DIMLESS)


def plane_stress_mu_bar(values):
    """mu_bar = E / (2(1+nu)) -- the deployed thin-plate plane-stress shear
    reduced modulus (ElasticMaterial2D.mu_bar), re-derived via MATH-01 as an
    independent cross-check of that ratified formula."""
    return shear_from_E_nu(values)


DERIVATIONS = {
    "mass": ("rho x volume -> mass (MATH-01 composition)", mass),
    "shear_from_E_nu": ("G = E / (2(1+nu))", shear_from_E_nu),
    "plane_stress_mu_bar": ("mu_bar = E / (2(1+nu))", plane_stress_mu_bar),
}


def derive(derivation_id, values):
    """Run a declared derivation. Unknown ids are refused -- there is no
    'nu from density' or any other invented relation. Returns
    (Quantity, derivation string): the arithmetic is always carried."""
    if derivation_id not in DERIVATIONS:
        raise Mat02Refusal(R_UNSUPPORTED_DERIVATION, f"no derivation "
                           f"{derivation_id!r} is declared in this registry; "
                           "deriving it would invent physics")
    desc, fn = DERIVATIONS[derivation_id]
    return fn(values), desc


class CapabilityMatrix:
    """The explicit supported-model + required-parameter registry (the card
    statement), closed and frozen at construction."""

    def __init__(self, specs):
        self._specs = {}
        for spec in specs:
            _validated(spec)
            if spec.model_id in self._specs:
                raise Mat02Refusal(R_INCOMPLETE_SPEC, f"duplicate model id "
                                   f"{spec.model_id!r}")
            self._specs[spec.model_id] = spec
        if not self._specs:
            raise Mat02Refusal(R_INCOMPLETE_SPEC, "empty registry")
        self._frozen = True

    @property
    def specs(self):
        return MappingProxyType(dict(self._specs))

    def __setattr__(self, name, value):
        if getattr(self, "_frozen", False) and name != "_frozen":
            raise Mat02Refusal(R_FROZEN, "the capability matrix is frozen "
                               "at build")
        object.__setattr__(self, name, value)

    def spec(self, model_id):
        if model_id not in self._specs:
            raise Mat02Refusal(R_UNKNOWN_MODEL, f"model {model_id!r} is not "
                               f"in the supported registry "
                               f"{sorted(self._specs)}; there is deliberately "
                               "no 'any response' wildcard model")
        return self._specs[model_id]

    def claim(self, model_id, params, state=None):
        """THE CARD PREDICTION'S SURFACE. Gate order: unknown_model ->
        missing_input -> dimension/physics gates -> missing_state ->
        state_out_of_domain. Success returns a frozen CapabilityClaim; any
        refusal leaves NO claim and NO response Quantity."""
        spec = self.spec(model_id)                     # 1 unknown_model
        params, state = dict(params or {}), dict(state or {})
        try:
            _check_set(spec.required, params)          # 2/3/4 primary set
        except Mat02Refusal as primary:
            if primary.reason != R_MISSING_INPUT:
                raise
            for alt in spec.alternatives:              # declared only
                if all(r.name in params for r in alt):
                    _check_set(alt, params)
                    break
            else:
                raise
        for sv in spec.state_variables:                # 5/6 state gates
            if sv.name not in state:
                raise Mat02Refusal(R_MISSING_STATE, f"model {model_id!r} "
                                   f"requires state variable '{sv.name}' "
                                   f"({sv.kind}); a claim without the state "
                                   "is unsupported")
            sv.check(state[sv.name])
        return CapabilityClaim(
            model_id=model_id, response_family=spec.response_family,
            satisfied=tuple(r.name for r in spec.required),
            basis=(f"{model_id}: required set complete, dimensions typed "
                   f"via MATH-01, gates passed, domain declared: "
                   f"{spec.domain}"))

    def demand(self, claim, requested_family):
        """A claim licenses only its declared response family (modeled on the
        deployed P-8j shape: no 3D claim may be invented from uniaxial
        data)."""
        if not isinstance(claim, CapabilityClaim):
            raise Mat02Refusal(R_MISSING_INPUT, "demand requires a "
                               f"CapabilityClaim from claim(); got "
                               f"{type(claim).__name__}")
        if requested_family != claim.response_family:
            raise Mat02Refusal(R_UNSUPPORTED_RESPONSE, f"claim on "
                               f"{claim.model_id!r} licenses "
                               f"'{claim.response_family}' only; "
                               f"'{requested_family}' is not supported by "
                               "that model's inputs -- no extrapolated "
                               "capability may be invented")


_ISO_ORIGIN = ("isotropic fourth-order tensor: C = lambda d_ij d_kl + "
               "mu(d_ik d_jl + d_il d_jk) -> exactly 2 constants (classical "
               "Voigt reduction)")
_ORTHO_ORIGIN = ("orthotropic linear elastic: E1,E2,E3,G12,G13,G23,nu12,"
                 "nu13,nu23 with reciprocity nu_ij/E_i = nu_ji/E_j -> 12 "
                 "written, 9 independent (classical Voigt reduction)")


def build_default_matrix() -> CapabilityMatrix:
    """The shipped closed registry: six specs (the card's mathematics -- 
    isotropy, orthotropy, state variables, domains -- one row each)."""
    E = lambda n: Requirement(n, DIM_PA, GATE_POSITIVE)
    FR = lambda n: Requirement(n, DIM_DIMLESS, GATE_FRACTION)
    NU = lambda n: Requirement(n, DIM_DIMLESS, GATE_NU_RANGE)
    return CapabilityMatrix([
        ModelSpec(
            model_id="mass", response_family="mass",
            required=(Requirement("rho", DIM_RHO, GATE_POSITIVE),),
            domain=("homogeneous part; bulk density of the declared "
                    "composition; licenses mass/inertia claims ONLY"),
            symmetry_class="scalar",
            constant_origin=("mass = rho x V: one scalar field; the only "
                             "response density alone supports"),
            independent_constant_count=1),
        ModelSpec(
            model_id="uniaxial_along_grain",
            response_family="axial_static_along_grain",
            required=(E("E_L"),),
            domain=("static, small-strain, 1D response along the declared "
                    "grain axis only; no transverse, shear or 3D claim"),
            symmetry_class="uniaxial",
            constant_origin=("one measured modulus along one axis -> one "
                             "axis's static stiffness; nothing else "
                             "follows"),
            independent_constant_count=1),
        ModelSpec(
            model_id="isotropic_linear_elastic",
            response_family="isotropic_3d_linear_elastic",
            required=(E("E"), NU("nu")),
            alternatives=((E("E"), E("G")),),
            domain=("small strain, linear; isotropy DECLARED by the source "
                    "(never assumed); nu in (-1, 1/2) for the (E, nu) pair"),
            symmetry_class="isotropic",
            constant_origin=_ISO_ORIGIN,
            independent_constant_count=2),
        ModelSpec(
            model_id="isotropic_plane_stress_sheet",
            response_family="plane_stress_sheet",
            required=(E("E"), NU("nu"),
                      Requirement("h", DIM_M, GATE_POSITIVE)),
            domain=("thin isotropic sheet, plane stress; nu in (-1, 1/2); "
                    "h is geometry, not a stiffness constant"),
            symmetry_class="isotropic_2d",
            constant_origin=_ISO_ORIGIN,
            independent_constant_count=2),
        ModelSpec(
            model_id="orthotropic_3d_elastic",
            response_family="orthotropic_3d_linear_elastic",
            required=(E("E1"), E("E2"), E("E3"), E("G12"), E("G13"),
                      E("G23"), FR("nu12"), FR("nu13"), FR("nu23")),
            domain=("linear orthotropic in a DECLARED orthonormal material "
                    "frame; normal-shear decoupled (Voigt xx,yy,zz,yz,xz,"
                    "xy)"),
            symmetry_class="orthotropic",
            constant_origin=_ORTHO_ORIGIN,
            independent_constant_count=9),
        ModelSpec(
            model_id="linear_viscoelastic",
            response_family="linear_viscoelastic",
            required=(E("E"), NU("nu")),
            required_state=("relaxation_spectrum", "temperature_k"),
            state_variables=(StateVariable("relaxation_spectrum", "nonempty"),
                             StateVariable("temperature_k", "range",
                                           (150.0, 500.0))),
            domain=("linear viscoelastic, thermorheologically simple; the "
                    "relaxation state is required AT CLAIM TIME"),
            symmetry_class="isotropic_viscoelastic",
            constant_origin=(_ISO_ORIGIN + "; the state variables are not "
                             "stiffness constants"),
            independent_constant_count=2),
    ])
