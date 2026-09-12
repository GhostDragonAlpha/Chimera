"""mat04_reference_model.py -- independent reference model of catalogue card
MAT-04 "Parameter identification" (holodeck-mat-04).

Card contract (quoted from the card, preregistered in ../PREREGISTRATION.txt):
  STATEMENT: Calibration tools with confidence and parameter-correlation
             outputs
  PREDICTION: Held-out experiments agree within declared predictive
              uncertainty
  FALSIFIER: Training-fit success is called predictive material validation
  MATHEMATICS: inverse problems; sensitivity; experimental design

STDLIB ONLY (math, sys, dataclasses, fractions, pathlib) PLUS the MATH-01
typed-quantity backbone (the task packet's designated units backbone:
docs/evidence/agent_fleet/HOLODECK/MATH/MATH-01/reference/
math01_reference_model.py -- Dimension over exact Fraction (L,M,T)
exponents, Quantity with named `dimension_mismatch` refusals, UnitRegistry
declared-only conversions). This is an independent model of the INTENDED
contract: least-squares identification of a declared tension fixture with
confidence intervals, a parameter-correlation output, D-optimal experimental
design over candidate load programs, and a held-out judge whose
AGREES/DISAGREES verdict is COMPUTED from the declared band, never
advertised. It is NOT the deployed material plane (tools/material_contract.py,
tools/materials.py, tools/elastic_foundation/*), which is measured separately
in checks/r5_source_trace.txt and checks/r6_findings.txt.

The card falsifier lives in the validation surface: the ONLY way to a verdict
is judge()/validate() against a held-out experiment; with no held-out data or
no degrees of freedom the refusal is NAMED (no_heldout_evidence /
no_dof_for_uncertainty) and the verdict vocabulary is closed
{AGREES, DISAGREES} -- no "VALIDATED" label exists to hand out.

Every refusal carries a named reason (Mat04Refusal.reason).
"""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

# ---- the MATH-01 units backbone (dependency, cited at every dimensional
# touchpoint; independence is claimed from the DEPLOYED code, not from this
# designated backbone) --------------------------------------------------------

_HOLODECK = next(p for p in Path(__file__).resolve().parents
                 if p.name == "HOLODECK")
sys.path.insert(0, str(_HOLODECK / "MATH" / "MATH-01" / "reference"))
import math01_reference_model as m01  # noqa: E402

UNIT_REGISTRY = m01.UnitRegistry()  # declared-only conversions (cited)


class Mat04Refusal(ValueError):
    """Named refusal of the identification contract."""

    def __init__(self, reason: str, message: str):
        super().__init__(message)
        self.reason = reason
        self.message = message

    def __repr__(self):
        return f"Mat04Refusal({self.reason!r}, {self.message!r})"


# ---- the declared fixture's dimensional algebra (MATH-01 cited) --------------
# d = k*F + d0:  compliance k [m/N] -> Dimension L/N; offset d0 [m] -> L;
# observation d [m] -> L; load column F [N] -> Dimension.N.
PARAM_DIM_K = m01.Dimension.M / m01.Dimension.N      # L/N  (compliance)
PARAM_DIM_D0 = m01.Dimension.M                        # L    (offset)
PARAM_DIMS = (PARAM_DIM_K, PARAM_DIM_D0)
OBS_DIM = m01.Dimension.M                             # L
LOAD_DIM = m01.Dimension.N


def _check(cond, reason, message):
    if not cond:
        raise Mat04Refusal(reason, message)


# ---- experiments and designs -------------------------------------------------

@dataclass(frozen=True)
class Experiment:
    """One tension experiment. The observed extension arrives with a UNIT;
    gates run at fit()/judge() time (the boundary), not here."""
    exp_id: str
    load: m01.Quantity          # Dimension N
    obs_value: float            # as stated in obs_unit
    obs_unit: str
    sigma: float                # declared noise scale [same unit as obs]

    def obs_si(self, registry=UNIT_REGISTRY) -> float:
        """Observation re-expressed in SI metres via a DECLARED unit only."""
        _check(obs_unit_ok(self.obs_unit, registry),
               "undeclared_observation_unit",
               f"no declared unit {self.obs_unit!r}: the declared-only "
               "unit registry (MATH-01, cited) refuses it")
        _check(isinstance(self.obs_value, (int, float))
               and not isinstance(self.obs_value, bool)
               and math.isfinite(float(self.obs_value)),
               "nonfinite_observation",
               f"observation value must be finite, got {self.obs_value!r}")
        _dim, scale = registry.units[self.obs_unit]
        return float(self.obs_value) * scale


def obs_unit_ok(unit, registry=UNIT_REGISTRY):
    return unit in registry.units


def load_n(newtons: float) -> m01.Quantity:
    """A load Quantity of Dimension N (the model's load language)."""
    return m01.Quantity(newtons, m01.Dimension.N)


@dataclass(frozen=True)
class DesignSpec:
    """Column language of the design matrix. 'load' columns carry the
    experiment's load (Dimension N); 'one' columns are the constant 1
    (DIMENSIONLESS). The design gate (in fit) checks, per column, that
    column Dimension x parameter Dimension == observation Dimension through
    MATH-01's exact composition (cited, not reimplemented)."""
    name: str
    columns: tuple              # e.g. ("load", "one")


def _column_dim(kind):
    return LOAD_DIM if kind == "load" else m01.Dimension.DIMENSIONLESS


# ---- exact algebra (Fractions): Gramian determinant = rank gate + design ----

def gramian_exact(loads):
    """Exact (F^T F) and its determinant for rows [F_i, 1] over Fractions.
    det = n*sum(F^2) - (sum F)^2 = sum_{i<j}(F_i - F_j)^2 >= 0 exactly."""
    fr = [Fraction(str(float(f))) for f in loads]
    n = Fraction(len(fr))
    a = sum((f * f for f in fr), Fraction(0))
    b = sum(fr, Fraction(0))
    det = a * n - b * b
    return (a, b, n), det


def design_correlation(loads):
    """Design-stage parameter-correlation output: for C = s2*(F^T F)^-1 the
    s2 cancels, so rho = -(sum F)/sqrt(n*sum(F^2)) -- exact Fractions inside.
    Negative for positive loads (AMENDMENT 1); an unidentifiable design has
    no correlation and refuses."""
    (a, b, n), det = gramian_exact(loads)
    _check(det != 0, "rank_deficient_design",
           "a rank-deficient design has no parameter correlation")
    return float(-b) / math.sqrt(float(a * n))


def _t_pdf(u, dof):
    return (math.gamma((dof + 1) / 2.0)
            / (math.sqrt(dof * math.pi) * math.gamma(dof / 2.0))
            ) * (1.0 + u * u / dof) ** (-(dof + 1) / 2.0)


_T_CACHE = {}


def t_two_sided(dof, conf=0.95):
    """Two-sided conf quantile of Student-t with `dof` dof, stdlib-only:
    Simpson integral of the pdf + bisection on the CDF. No table constants
    inside the model (the published table is the CONTROL's oracle)."""
    key = (dof, conf)
    if key in _T_CACHE:
        return _T_CACHE[key]
    target = conf / 2.0            # mass in [0, t]
    lo, hi = 0.0, 20.0

    def mass(t, panels=2000):
        h = t / panels
        s = _t_pdf(0.0, dof) + _t_pdf(t, dof)
        for i in range(1, panels):
            s += _t_pdf(i * h, dof) * (4 if i % 2 else 2)
        return s * h / 3.0

    for _ in range(200):
        mid = (lo + hi) / 2.0
        if mass(mid) < target:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-13:
            break
    val = (lo + hi) / 2.0
    _T_CACHE[key] = val
    return val


# ---- the fit (inverse problem + sensitivity + confidence outputs) ------------
# Sensitivity: for the linear design, the Jacobian of predictions wrt theta
# IS the design matrix (col 0 = F [N], col 1 = 1); its columns carry the
# MATH-01 Dimensions checked by the design gate below.

@dataclass(frozen=True)
class FitResult:
    """Frozen identification result: the card's confidence outputs.
    theta = (k_hat, d0_hat) in SI; cov = s^2 (F^T F)^-1; corr = the
    parameter-correlation matrix (dimensionless). s2/cov/corr are None when
    dof == 0 (a perfect training fit carries NO declared uncertainty)."""
    theta: tuple
    cov: tuple
    corr: tuple
    s2: float
    dof: int
    n: int
    det_gramian: Fraction
    loads: tuple
    training_ids: tuple
    design_name: str


def fit(experiments, design: DesignSpec, registry=UNIT_REGISTRY):
    experiments = tuple(experiments)          # defensive copy of the ledger
    # per-experiment gates (order: unit -> value -> noise)
    obs_si = [e.obs_si(registry) for e in experiments]
    for e in experiments:
        _check(isinstance(e.sigma, (int, float))
               and not isinstance(e.sigma, bool)
               and math.isfinite(float(e.sigma)) and float(e.sigma) > 0.0,
               "invalid_noise_sigma",
               f"declared noise sigma must be finite and positive, "
               f"got {e.sigma!r} on experiment {e.exp_id!r}")
    # dimension gate: column Dimension x parameter Dimension == observation
    # Dimension, through MATH-01's exact algebra (cited) -- the metre-newton
    # pose refuses here before any arithmetic.
    obs_dim = registry.units[experiments[0].obs_unit][0]
    for col, pdim in zip(design.columns, PARAM_DIMS):
        _check(_column_dim(col) * pdim == obs_dim,
               "dimension_mismatch",
               f"design column {col!r} ({_column_dim(col)}) x parameter "
               f"({pdim}) != observation dimension ({obs_dim}): "
               "MATH-01 dimension_mismatch (cited)")
    for e in experiments:
        _check(e.load.dimension == LOAD_DIM,
               "dimension_mismatch",
               f"load of experiment {e.exp_id!r} carries {e.load.dimension},"
               f" expected {LOAD_DIM}")
    loads = [e.load.value for e in experiments]
    # exact rank gate: an unidentifiable design is refused, never fitted
    _gram, det = gramian_exact(loads)
    _check(det != 0, "rank_deficient_design",
           f"Gramian determinant is exactly {det}: the design cannot "
           "identify (k, d0); refusing to fit")
    # float normal equations: [[sum F^2, sum F],[sum F, n]] th = [sum F d, sum d]
    fa = [float(f) for f in loads]
    na = len(fa)
    a = sum(f * f for f in fa)
    b = float(sum(Fraction(str(f)) for f in fa))
    c = float(na)
    rhs0 = sum(f * d for f, d in zip(fa, obs_si))
    rhs1 = sum(obs_si)
    detf = a * c - b * b
    k_est, d0_est = _solve2(a, b, b, c, rhs0, rhs1)
    resid = [d - (k_est * f + d0_est) for f, d in zip(fa, obs_si)]
    ssr = sum(r * r for r in resid)
    dof = na - len(PARAM_DIMS)
    if dof <= 0:
        s2 = cov = corr = None
    else:
        s2 = ssr / dof
        inv00, inv01 = c / detf, -b / detf
        inv11 = a / detf
        cov = ((s2 * inv00, s2 * inv01),
               (s2 * inv01, s2 * inv11))
        rho = cov[0][1] / math.sqrt(cov[0][0] * cov[1][1])
        corr = ((1.0, rho), (rho, 1.0))
    return FitResult(theta=(k_est, d0_est), cov=cov, corr=corr, s2=s2,
                     dof=dof, n=na, det_gramian=det,
                     loads=tuple(loads),   # frozen copies
                     training_ids=tuple(e.exp_id for e in experiments),
                     design_name=design.name)


def _solve2(a00, a01, a10, a11, r0, r1):
    """Solve [[a00,a01],[a10,a11]] x = r by Cramer after the pivot check
    (2x2 partial pivot: caller orders the larger first-column first)."""
    det = a00 * a11 - a01 * a10
    _check(det != 0.0, "rank_deficient_design",
           "singular normal equations (float determinant 0)")
    x0 = (r0 * a11 - a01 * r1) / det
    x1 = (a00 * r1 - r0 * a10) / det
    return (x0, x1)


def confidence_intervals(fitres, conf=0.95):
    """The card's confidence output: theta_j +/- t * sqrt(C_jj) [SI]."""
    _check(fitres.s2 is not None, "no_dof_for_uncertainty",
           f"dof = {fitres.dof}: no degrees of freedom, no declared "
           "uncertainty (a perfect training fit is not a confident one)")
    t = t_two_sided(fitres.dof, conf)
    half_k = t * math.sqrt(fitres.cov[0][0])
    half_d0 = t * math.sqrt(fitres.cov[1][1])
    return ((fitres.theta[0] - half_k, fitres.theta[0] + half_k),
            (fitres.theta[1] - half_d0, fitres.theta[1] + half_d0))


# ---- declared predictive band and the held-out judge -------------------------

@dataclass(frozen=True)
class Prediction:
    """A declared predictive band at a load: mean Quantity of Dimension L
    and half-width Quantity of Dimension L, declared BEFORE any reveal."""
    mean: m01.Quantity
    half_width: m01.Quantity
    load: m01.Quantity
    fit: FitResult


def declare_predictive_band(fitres, load: m01.Quantity, conf=0.95):
    _check(load.dimension == LOAD_DIM, "dimension_mismatch",
           f"band load must be {LOAD_DIM}, got {load.dimension}")
    _check(fitres.s2 is not None, "no_dof_for_uncertainty",
           f"dof = {fitres.dof}: a perfect training fit declares no "
           "predictive uncertainty and can never be judged")
    # leverage x' (F^T F)^-1 x at x = [F, 1]:
    #   = (n*F^2 - 2*(sum F)*F + sum(F^2)) / det(F^T F)
    fr = [Fraction(str(f)) for f in fitres.loads]            # exact sums
    A = float(sum(f * f for f in fr))                        # sum F^2
    sum_f = float(sum(fr))                                   # sum F
    n = float(fitres.n)
    detf = float(fitres.det_gramian)
    f2 = load.value * load.value
    lev = (n * f2 - 2.0 * sum_f * load.value + A) / detf
    var = fitres.s2 * (1.0 + lev)
    half = t_two_sided(fitres.dof) * math.sqrt(var)
    # MATH-01 cited: mean/half-width are Quantities of Dimension L; the
    # composition dim(k) x dim(F) == dim(d) holds exactly (R1(h)).
    mean_q = m01.Quantity(fitres.theta[0] * load.value + fitres.theta[1],
                          OBS_DIM)
    return Prediction(mean=mean_q, half_width=m01.Quantity(half, OBS_DIM),
                      load=load, fit=fitres)


@dataclass(frozen=True)
class Verdict:
    """Computed agreement verdict. The vocabulary is CLOSED:
    {AGREES, DISAGREES}. There is no VALIDATED/OK label in this contract."""
    verdict: str
    exp_id: str
    distance: float
    half_width: float


Verdict.VALUES = ("AGREES", "DISAGREES")


def judge(prediction: Prediction, experiment: Experiment,
          registry=UNIT_REGISTRY):
    # THE CARD FALSIFIER'S GATE: a training point agreeing with its own fit
    # is NOT validation -- refused by name.
    _check(experiment.exp_id not in prediction.fit.training_ids,
           "heldout_overlaps_training",
           f"experiment {experiment.exp_id!r} is in the training ledger: "
           "a training point cannot validate the fit that consumed it")
    obs_si = experiment.obs_si(registry)
    distance = abs(obs_si - prediction.mean.value)
    agree = distance <= prediction.half_width.value
    return Verdict(verdict=("AGREES" if agree else "DISAGREES"),
                   exp_id=experiment.exp_id, distance=distance,
                   half_width=prediction.half_width.value)


def validate(fitres, heldout, registry=UNIT_REGISTRY):
    """The validation surface over a HELD-OUT ledger. Empty -> refusal (the
    card falsifier's exact pose: training success alone validates nothing).
    A zero-dof fit refuses before any verdict can exist."""
    heldout = tuple(heldout)
    _check(len(heldout) > 0, "no_heldout_evidence",
           "the held-out ledger is empty: training-fit success is NOT "
           "predictive material validation")
    _check(fitres.s2 is not None, "no_dof_for_uncertainty",
           f"dof = {fitres.dof}: no declared uncertainty can exist, so no "
           "agreement verdict can exist")
    verdicts = []
    for e in heldout:
        band = declare_predictive_band(fitres, e.load)
        verdicts.append(judge(band, e, registry=registry))
    return tuple(verdicts)


# ---- experimental design (D-optimal, exact) ----------------------------------

def choose_design(candidates):
    """D-optimal choice among {name: [loads in N]}: maximize det(F^T F) by
    exact-Fraction determinant. Exact ties refuse (design is derived, not
    tasted)."""
    dets = {name: gramian_exact(loads)[1]
            for name, loads in candidates.items()}
    best = max(dets.values())
    winners = [name for name, d in dets.items() if d == best]
    _check(len(winners) == 1, "ambiguous_design",
           f"exact determinant tie between {winners}: no unique D-optimal "
           "program")
    return winners[0], dets[winners[0]], dets
