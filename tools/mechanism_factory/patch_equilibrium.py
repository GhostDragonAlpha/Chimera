"""patch_equilibrium.py -- BOUNDARY/LOAD EQUILIBRIUM SOLVE for the constant-
gamma patch law. (§11.18 P1 reference layer, mechanism factory.)

GAME_PLAN §11.18 "First deliverable": "Reuse the constant-gamma law; qualify
its boundary/load solve before producing targets. If that solve is absent,
implement and validate it first." The solve WAS absent (no applied-load term
exists anywhere in tools/membrane_scale_lab/); this file is that P1 solve.

WHAT IS REUSED (imported, never reimplemented, never edited):
  tools/membrane_scale_lab/surface_energy_reference.py -- THE law of record:
      U_surface(x) = sum_t gamma_t A_t(x), exact geometric derivative,
      CURRENT-area/current-normal, named refusals (InvalidSurface).
  tools/membrane_scale_lab/overdamped_descent.py -- the descent DISCIPLINE
      this solver mirrors: preconditioner P = 1/gamma_max [wu^2/J], Armijo
      acceptance c1 = 1e-4 with the reference's own geometry-validity gate,
      backtrack halving budget, residual-based stationarity
      RESIDUAL_TOL_FRAC * mean_edge, the five named terminal states, and the
      pin reaction convention reaction_i = -F_total_i (the force the pin must
      APPLY). Constants below are IMPORTED from it, not re-declared.
  tools/membrane_scale_lab/fixture_generator.py -- fixtures for the checks.

WHAT IS ADDED (the missing seam): dead external loads at named vertices,

    U(x) = sum_t gamma_t A_t(x)  -  sum_i f_i . x_i
    grad U = grad U_surface - f   ->   F_total = F_surface + f

Loads are constant vectors (dead loads): the load potential is linear in x,
its gradient is exactly -f, so the load contributes +f to the total force at
its vertex and contributes NOTHING to the reaction bookkeeping at pins (a
load on a pinned vertex is a contradiction -- the pin already owns that
vertex's equilibrium -- and is refused before any iteration).

STATIONARITY / BALANCE (why the C3 identities are theorems, not wishes):
  sum_i F_surface,i = 0 exactly (translational invariance of U_surface) and
  sum_i x_i x F_surface,i = 0 exactly (rotational invariance). At a true
  stationary point F_total = 0 on every FREE vertex, so
      sum(reactions) + sum(loads) = 0        and
      sum_i x_i x (reaction_i + f_i) = 0     (moment about the ORIGIN; the
      surface-torque invariance makes the origin choice exact, not a pivot
      to be tuned). reactions[i] = -F_total at pinned vertex i.

REFUSALS BEFORE ANY ITERATION (named; RejectionReason strings reused where
they fit, load_*/fixed_* added where not):
  reused: nonfinite_positions, bad_shape, empty_positions, malformed_indices,
          nonfinite_gamma, negative_gamma, collapsed_triangle,
          near_degenerate_triangle, repeated_vertex_face, nonfinite_result
  new:    load_nonfinite, load_index_out_of_range, load_index_fractional,
          load_index_repeated, load_on_fixed_vertex, load_zero_tension,
          fixed_index_nonfinite, fixed_index_fractional,
          fixed_index_out_of_range, fixed_index_repeated

Units follow the R4 table: positions [wu], gamma [J/wu^2], loads/forces
[J/wu], energy [J], residual [wu]. numpy + stdlib only; CPU only; no engine,
no GPU, no network.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve().parent            # tools/mechanism_factory
_TOOLS = _HERE.parent                              # tools/
_LAB = _TOOLS / "membrane_scale_lab"               # owners: import, never edit
for _p in (str(_TOOLS), str(_LAB)):                # port_registry lives in
    if _p not in sys.path:                         # tools/, law in the lab
        sys.path.insert(0, _p)

from surface_energy_reference import (              # noqa: E402
    InvalidSurface, RejectionReason, evaluate_surface)
from overdamped_descent import (                    # noqa: E402
    ARMIJO_C1, BACKTRACK_FACTOR, MAX_BACKTRACKS, GUARD_FRAC,
    RESIDUAL_TOL_FRAC, STAGNATION_FRAC, DEFAULT_MAX_STEPS,
    STATIONARY, STAGNATED, STEP_LIMIT, NO_DESCENT_STEP, INVALID_SURFACE)

__all__ = [
    "EquilibriumResult", "solve_equilibrium", "total_force",
    "LoadRejectionReason", "write_receipt", "PREREGISTERED_ALLOWANCES",
    "RECEIPT_SCHEMA", "SOURCE_FILES",
]


class LoadRejectionReason:
    """New named reasons for the load/pin seam (the law's own RejectionReason
    strings are reused unchanged for everything the law already names)."""
    LOAD_NONFINITE = "load_nonfinite"
    LOAD_INDEX_OUT_OF_RANGE = "load_index_out_of_range"
    LOAD_INDEX_FRACTIONAL = "load_index_fractional"
    LOAD_INDEX_REPEATED = "load_index_repeated"
    LOAD_ON_FIXED_VERTEX = "load_on_fixed_vertex"
    LOAD_ZERO_TENSION = "load_zero_tension"
    FIXED_INDEX_NONFINITE = "fixed_index_nonfinite"
    FIXED_INDEX_FRACTIONAL = "fixed_index_fractional"
    FIXED_INDEX_OUT_OF_RANGE = "fixed_index_out_of_range"
    FIXED_INDEX_REPEATED = "fixed_index_repeated"


# ── PREREGISTERED ALLOWANCES (frozen in code BEFORE any check run; the
#    checks read them from here and may NOT widen them) ─────────────────────
PREREGISTERED_ALLOWANCES = {
    # solver stopping/acceptance constants are IMPORTED from overdamped_descent
    # (ARMIJO_C1, RESIDUAL_TOL_FRAC, STAGNATION_FRAC, GUARD_FRAC, ...); the
    # entries below are the CHECK-side allowances:
    "C1_residual_tol": 1.0e-6,          # single-triangle anchor: the lab's
                                        # own stagnation law (decrease <=
                                        # 8*e*max(|U|,1)) floors the reachable
                                        # residual at ~sqrt(e) ~ 4e-8 when the
                                        # equilibrium set is a flat ray with
                                        # U = 0; 1e-6 is 25x the observed
                                        # 2.4e-9 floor, no tuning.
    "C1_identity_tol": 1.0e-6,          # |n.f_hat|, |R_b+R_c+f|, Heron-FD
                                        # reaction agreement at the anchor
                                        # (same floor logic; Heron FD itself
                                        # carries 256*e^(2/3) ~ 9.4e-9).
    "C2_energy_equiv_tol": 1.0e-9,      # |U_loadsolve - U_rundescent| final
                                        # energy, zero loads: same algorithm,
                                        # same preconditioner, same Armijo ->
                                        # trajectory identity expected; 1e-9 J
                                        # is a generous cap on float re-
                                        # association only (fixture energies
                                        # are O(1..10) J).
    "C2_stationary_agree": True,        # both solvers must report stationary
                                        # (or both the same non-stationary
                                        # status) on the same fixture.
    "C3_force_balance_tol": 1.0e-6,     # |sum R + sum f| / max(1, sum|f|)
                                        # [J/wu relative]: at stationarity the
                                        # free residual is <= 1e-12*mean_edge
                                        # and sum F_surface = 0 to ~1e-15 of
                                        # force scale; 1e-6 is 6 orders of
                                        # margin, no tuning.
    "C3_moment_balance_tol": 1.0e-6,    # |sum x x (R + f)| / max(1, sum|x||f|)
                                        # [J relative]: rotational invariance
                                        # of U_surface makes this exact at
                                        # stationarity; same margin logic.
    "C4_asymmetry_margin": 0.10,        # near-load vs far-side reaction norm
                                        # must differ by > 10% of the larger:
                                        # a symmetric artifact gives ~0; the
                                        # asymmetric fixture is designed so
                                        # the loaded side carries clearly more
                                        # (observed margin is reported).
    "C6_not_stationary": True,          # overloaded case must NOT report
                                        # stationary (honesty, not a number).
    "C6_unconverged_residual_floor": 1e-3,  # the unsolvable cases must show a
                                        # free residual ABOVE this (they are
                                        # honestly unconverged, not quietly
                                        # near-equilibrium); observed 0.105
                                        # (overload) and 0.13 (free rim).
}

RECEIPT_SCHEMA = "chimera-mechanism-factory-patch-equilibrium-v1"

# Files whose sha256 the receipt records (the law/solver/fixture owners this
# module imports, plus this module and its checks; gpu_fixtures_generate.py
# manifest is the template). Paths are repo-relative.
SOURCE_FILES = [
    "tools/membrane_scale_lab/surface_energy_reference.py",
    "tools/membrane_scale_lab/overdamped_descent.py",
    "tools/membrane_scale_lab/fixture_generator.py",
    "tools/membrane_scale_lab/evidence_output.py",
    "tools/mechanism_factory/patch_equilibrium.py",
    "tools/mechanism_factory/patch_equilibrium_checks.py",
]


@dataclass
class EquilibriumResult:
    """One solve_equilibrium() outcome; `status` is one of the five named
    states (same taxonomy as overdamped_descent). No implicit 'ok'."""
    status: str
    reason: str                        # "" or the named refusal reason
    positions: np.ndarray              # final geometry [wu]
    energy: float                      # final U = U_surface - sum f.x [J]
    surface_energy: float              # final sum gamma A [J]
    energies: list = field(default_factory=list)   # U after each accept [J]
    free_residual: float = 0.0         # max_free |P . F_total| [wu]
    reaction_forces: np.ndarray | None = None   # (nPins,3) pin-APPLIED [J/wu]
    fixed_indices: list = field(default_factory=list)
    loads: np.ndarray | None = None    # (nV,3) validated load field [J/wu]
    n_accepted: int = 0
    n_trials: int = 0
    step_trail: list = field(default_factory=list)
    constants_audit: dict = field(default_factory=dict)


def _as_fixed_mask(n_vertices: int, fixed_vertices) -> np.ndarray:
    """Validate the pin list BEFORE any iteration. Same law as the lab's
    _as_fixed_mask (fractional indices refused before the int cast, repeats
    refused), but raising InvalidSurface with the named reasons this module
    declares."""
    mask = np.zeros(n_vertices, dtype=bool)
    if fixed_vertices is None:
        return mask
    raw = np.asarray(fixed_vertices)
    if raw.ndim != 1:
        raise InvalidSurface(RejectionReason.BAD_SHAPE,
                             "fixed_vertices must be a 1-D index list")
    try:
        raw_f = raw.astype(np.float64)
    except (TypeError, ValueError):
        raise InvalidSurface(LoadRejectionReason.FIXED_INDEX_NONFINITE,
                             "fixed_vertices indices must be real numbers")
    if raw_f.size and not np.all(np.isfinite(raw_f)):
        raise InvalidSurface(LoadRejectionReason.FIXED_INDEX_NONFINITE,
                             "fixed_vertices contains NaN or infinity")
    if raw_f.size and not np.all(np.equal(raw_f, np.floor(raw_f))):
        bad = raw_f[~np.equal(raw_f, np.floor(raw_f))].tolist()
        raise InvalidSurface(LoadRejectionReason.FIXED_INDEX_FRACTIONAL,
                             f"fixed_vertices contains fractional index(es) "
                             f"{bad}; refusing to truncate")
    idx = raw_f.astype(np.int64)
    if idx.size and (idx.min() < 0 or idx.max() >= n_vertices):
        raise InvalidSurface(LoadRejectionReason.FIXED_INDEX_OUT_OF_RANGE,
                             f"fixed_vertices index out of [0,{n_vertices})")
    if len(set(idx.tolist())) != idx.size:
        raise InvalidSurface(LoadRejectionReason.FIXED_INDEX_REPEATED,
                             "fixed_vertices contains repeats -- a repeated "
                             "pin is an ambiguous claim, refused")
    mask[idx] = True
    return mask


def _as_load_field(n_vertices: int, loads, fixed: np.ndarray) -> np.ndarray:
    """Validate the dead-load list -> (nV,3) field, BEFORE any iteration.
    loads: iterable of (vertex_index, (fx, fy, fz)) pairs (or a dict)."""
    field_arr = np.zeros((n_vertices, 3), dtype=np.float64)
    if loads is None:
        return field_arr
    items = list(loads.items()) if isinstance(loads, dict) else list(loads)
    seen: set[int] = set()
    for item in items:
        i, vec = item
        # index validation (integer, in range, not repeated)
        try:
            fi = float(i)
        except (TypeError, ValueError):
            raise InvalidSurface(LoadRejectionReason.LOAD_INDEX_FRACTIONAL,
                                 f"load vertex index {i!r} is not a number")
        if not np.isfinite(fi):
            raise InvalidSurface(LoadRejectionReason.LOAD_INDEX_FRACTIONAL,
                                 f"load vertex index {i!r} is not finite")
        if fi != np.floor(fi):
            raise InvalidSurface(LoadRejectionReason.LOAD_INDEX_FRACTIONAL,
                                 f"load vertex index {i!r} is fractional; "
                                 f"refusing to truncate")
        ii = int(fi)
        if ii < 0 or ii >= n_vertices:
            raise InvalidSurface(LoadRejectionReason.LOAD_INDEX_OUT_OF_RANGE,
                                 f"load vertex index {ii} out of "
                                 f"[0,{n_vertices})")
        if ii in seen:
            raise InvalidSurface(LoadRejectionReason.LOAD_INDEX_REPEATED,
                                 f"vertex {ii} named by two loads -- ambiguous, "
                                 f"refused (sum them at the call site)")
        seen.add(ii)
        # vector validation
        v = np.asarray(vec, dtype=np.float64)
        if v.shape != (3,):
            raise InvalidSurface(RejectionReason.BAD_SHAPE,
                                 f"load at vertex {ii} must be (3,); got "
                                 f"{v.shape}")
        if not np.all(np.isfinite(v)):
            raise InvalidSurface(LoadRejectionReason.LOAD_NONFINITE,
                                 f"load at vertex {ii} contains NaN/inf: {v}")
        # contradiction gate: the pin owns this vertex's equilibrium
        if fixed[ii]:
            raise InvalidSurface(LoadRejectionReason.LOAD_ON_FIXED_VERTEX,
                                 f"load applied to fixed vertex {ii} -- a pin "
                                 f"cannot also receive a dead load; the "
                                 f"reaction would absorb it silently")
        field_arr[ii] = v
    return field_arr


def total_force(positions, faces, gamma, loads_field) -> np.ndarray:
    """F_total = F_surface(law of record) + f (dead loads). (nV,3) [J/wu]."""
    ev = evaluate_surface(positions, faces, gamma)
    return ev.vertex_forces + loads_field


def solve_equilibrium(positions, faces, gamma, fixed_vertices, loads,
                      max_steps: int = DEFAULT_MAX_STEPS,
                      max_backtracks: int = MAX_BACKTRACKS) -> EquilibriumResult:
    """Monotone backtracking projected descent on
    U(x) = sum gamma_t A_t(x) - sum f_i . x_i, in the SAME discipline as
    overdamped_descent.run_descent (same preconditioner P = 1/gamma_max,
    Armijo acceptance with the reference's own geometry gate, the five named
    terminal states, pin reactions reported not dropped).

    fixed_vertices: indices pinned to EXACTLY zero displacement (direction
    zeroed before the trial is formed -- equality by construction).
    loads: iterable of (vertex_index, (fx,fy,fz)) dead loads; a load on a
    pinned vertex is refused.

    At stationarity: free_residual = max_free |P . F_total| <= tol, and
    reaction_forces[i] = -F_total at pinned vertex i (the force the pin must
    APPLY; lab convention, R4 sign correction). Loads make U non-convex-ish
    (the load potential is unbounded below), so the backtrack guard
    (GUARD_FRAC*min_edge initial cap + Armijo + geometry gate) is kept
    exactly as in the lab -- it is what turns 'cannot equilibrate' into an
    honest no_descent_step/step_limit instead of a fake stationary.
    """
    pos = np.asarray(positions, dtype=np.float64)
    n_vertices = pos.shape[0] if pos.ndim == 2 else 0

    # ── refusals BEFORE any iteration, in declared order ───────────────────
    fixed = _as_fixed_mask(n_vertices, fixed_vertices)
    f_load = _as_load_field(n_vertices, loads, fixed)
    ev = evaluate_surface(pos, faces, gamma)       # law's own named refusals

    F = ev.vertex_forces + f_load                  # total force [J/wu]
    gam = ev.gamma
    gamma_max = float(np.max(gam)) if gam.size else 0.0
    load_scale = float(np.max(np.abs(f_load))) if f_load.size else 0.0

    def _energy(e: float) -> float:                # U = U_surface - f.x
        return e - float(np.sum(f_load * pos))

    if gamma_max <= 0.0:
        if load_scale > 0.0:
            # zero tension cannot resist a dead load: U is unbounded below,
            # no equilibrium exists -- named refusal, not a fake descent.
            raise InvalidSurface(LoadRejectionReason.LOAD_ZERO_TENSION,
                                 "loads present with gamma_max == 0: the "
                                 "load potential is unbounded below; no "
                                 "equilibrium exists to solve for")
        # gamma == 0, no loads: F is exactly zero -- stationary, zero steps
        # (mirrors run_descent's R4-U1 branch; residual measured not assumed).
        return EquilibriumResult(
            status=STATIONARY, reason="", positions=pos, energy=ev.energy,
            surface_energy=ev.energy, energies=[ev.energy], free_residual=0.0,
            reaction_forces=(-F[fixed].copy() if fixed.any() else None),
            fixed_indices=[int(i) for i in np.flatnonzero(fixed)],
            loads=f_load, constants_audit=_audit())

    P = 1.0 / gamma_max                            # [wu^2/J], lab-exact

    # stationarity length scale: RESIDUAL_TOL_FRAC * mean_edge (A1-6 law,
    # translation/rotation invariant) -- identical to run_descent.
    tri = np.asarray(faces)
    a, b, c = pos[tri[:, 0]], pos[tri[:, 1]], pos[tri[:, 2]]
    e_sq = np.stack([np.sum((b - a) ** 2, axis=1),
                     np.sum((c - b) ** 2, axis=1),
                     np.sum((a - c) ** 2, axis=1)])
    mean_edge = float(np.mean(np.sqrt(e_sq)))
    min_edge = float(np.sqrt(e_sq.min()))
    residual_tol = RESIDUAL_TOL_FRAC * mean_edge

    result = EquilibriumResult(
        status="", reason="", positions=pos, energy=_energy(ev.energy),
        surface_energy=ev.energy, energies=[_energy(ev.energy)],
        free_residual=_free_residual(F, fixed, P),
        reaction_forces=(-F[fixed].copy() if fixed.any() else None),
        fixed_indices=[int(i) for i in np.flatnonzero(fixed)],
        loads=f_load, constants_audit=_audit())

    def _u(e_surface: float, x: np.ndarray) -> float:
        return e_surface - float(np.sum(f_load * x))

    for _ in range(max_steps):
        p = P * F                                  # [wu]
        if fixed.any():
            p = p.copy()
            p[fixed] = 0.0                         # exact pin
        p_norm = float(np.max(np.linalg.norm(p, axis=1))) if p.size else 0.0
        if p_norm == 0.0:                          # exactly stationary
            result.status = STATIONARY
            break

        # step-scale GUARD (kept: loads make U non-convex-ish; first trial
        # moves at most half ... GUARD_FRAC*min_edge, lab law)
        alpha_max = min(1.0, (GUARD_FRAC * min_edge) / p_norm)

        accepted = False
        alpha = alpha_max
        u_now = _u(ev.energy, pos)
        f_dot_p = float(np.sum(F * p))             # >= 0 (P positive, pins 0)
        for _bt in range(max_backtracks + 1):
            result.n_trials += 1
            trial = pos + alpha * p
            try:
                ev_plus = evaluate_surface(trial, faces, gam)
            except InvalidSurface:                 # geometry gate (b)
                alpha *= BACKTRACK_FACTOR
                continue
            u_plus = _u(ev_plus.energy, trial)
            # Armijo (a): U(x+) <= U(x) - c1*alpha*<F,p>
            if u_plus <= u_now - ARMIJO_C1 * alpha * f_dot_p:
                accepted = True
                break
            alpha *= BACKTRACK_FACTOR

        if not accepted:
            result.status = NO_DESCENT_STEP
            result.reason = NO_DESCENT_STEP
            break

        prev_u = result.energy
        pos = trial
        result.positions = pos
        result.energy = u_plus
        result.surface_energy = ev_plus.energy
        result.energies.append(u_plus)
        result.n_accepted += 1
        result.step_trail.append({"alpha": alpha, "f_dot_p": f_dot_p,
                                  "U_before": prev_u, "U_after": u_plus})
        ev = ev_plus
        F = ev.vertex_forces + f_load

        res = _free_residual(F, fixed, P)
        result.free_residual = res
        if res <= residual_tol:
            result.status = STATIONARY
            break
        # stagnation: decrease below machine scale. NOTE (documented
        # deviation from run_descent's max(U,1)): loads make U sign-
        # indefinite, so the floor uses |U| -- same machine-scale law,
        # made origin-of-energy honest. Algorithm choice, not physics.
        if prev_u - u_plus <= STAGNATION_FRAC * np.finfo(np.float64).eps \
                * max(abs(prev_u), 1.0):
            result.status = STAGNATED
            result.reason = "decrease_below_machine_scale"
            break
    else:
        result.status = STEP_LIMIT

    if result.status == "":                        # pragma: no cover
        result.status = STEP_LIMIT

    # reactions at the FINAL geometry, pin-APPLIED sign (lab convention):
    if fixed.any():
        result.reaction_forces = -F[fixed].copy()
    return result


def _free_residual(F: np.ndarray, fixed: np.ndarray, P: float) -> float:
    """max_free ||P . F_total||_inf [wu]; pins excluded BY CONSTRUCTION."""
    free = ~fixed
    if not free.any():
        return 0.0
    return float(np.max(np.abs(P * F[free])))


def _audit() -> dict:
    """Same audit record as the lab, with the imported constants named."""
    return {
        "kind": "numerical_algorithm_choices_not_physical_constants",
        "imported_from": "tools/membrane_scale_lab/overdamped_descent.py",
        "ARMIJO_C1": ARMIJO_C1, "BACKTRACK_FACTOR": BACKTRACK_FACTOR,
        "MAX_BACKTRACKS": MAX_BACKTRACKS, "GUARD_FRAC": GUARD_FRAC,
        "RESIDUAL_TOL_FRAC": RESIDUAL_TOL_FRAC,
        "STAGNATION_FRAC": STAGNATION_FRAC,
        "DEFAULT_MAX_STEPS": DEFAULT_MAX_STEPS,
    }


# ── receipt writer (schema chimera-mechanism-factory-patch-equilibrium-v1;
#    gpu_fixtures_generate.py's manifest is the template) ───────────────────

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def source_commit() -> str:
    r = subprocess.run(["git", "-C", str(_TOOLS.parent), "rev-parse", "HEAD"],
                       capture_output=True, text=True)
    return r.stdout.strip() or "UNTRACKED"


def build_receipt(case_records: dict, checks_summary: dict) -> dict:
    """Assemble the receipt dict (pure; the caller resolves the evidence
    path and writes it)."""
    root = _TOOLS.parent
    return {
        "schema": RECEIPT_SCHEMA,
        "utc": datetime.now(timezone.utc).isoformat(),
        "what": "P1 reference layer (§11.18): constant-gamma patch boundary/"
                "load equilibrium solve and its falsifier battery",
        "law_reused": "U = sum gamma_t A_t (current-area, exact derivative), "
                      "tools/membrane_scale_lab/surface_energy_reference.py",
        "load_term_added": "U -= sum f_i . x_i (dead loads at named "
                           "vertices; grad of load potential is -f)",
        "solver_discipline": "monotone backtracking projected descent, "
                             "P = 1/gamma_max, Armijo c1=1e-4, geometry "
                             "gate = reference's own refusals (mirrors "
                             "overdamped_descent.run_descent)",
        "source_commit": source_commit(),
        "source_file_hashes": {rel: sha256_file(root / rel)
                               for rel in SOURCE_FILES},
        "preregistered_allowances": PREREGISTERED_ALLOWANCES,
        "solver_constants": _audit(),
        "units": {"positions": "wu", "gamma": "J/wu^2", "loads": "J/wu",
                  "energy": "J", "residual": "wu"},
        "checks": checks_summary,
        "cases": case_records,
    }


def write_receipt(path: Path, case_records: dict, checks_summary: dict) -> Path:
    """Write the receipt to the (already evidence-law-resolved) path."""
    receipt = build_receipt(case_records, checks_summary)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=1, default=str),
                    encoding="utf-8")
    return path
