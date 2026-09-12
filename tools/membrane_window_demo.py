"""membrane_window_demo.py -- THE FIRST MATERIAL-DRIVEN MEMBRANE WINDOW DEMO.

Task LUNA-WINDOW-01. Rule-0 membrane (preregistered before implementation,
recorded in docs/THE_MEMBRANE_WINDOW_DEMO.md):

  STATEMENT:  accepted iterations of the declared overdamped update satisfy
              the existing energy/geometry gates, and the renderer consumes
              that accepted geometry (no second visual pose).
  PREDICTION: positive gamma visibly reduces the B2 centre bump; zero gamma
              leaves geometry bit-unchanged; fixed-state gamma doubling
              doubles energy and force within the existing bounds.
  FALSIFIER:  any accepted-state gate breach, separate visual geometry,
              failed zero/doubling control, or a capture whose record lacks
              a matching state ID.

THE RAIL CONSTRAINT (derived, not chosen):
  B2's centre vertex (index 6) is constrained to the VERTICAL RAIL through
  its initial position: x,y held at their initial values, z free.  The rim
  vertices 0..5 are pinned (exact zero displacement, as run_descent does).

  The declared update is p = P.F with P = 1/gamma_max.  On the constrained
  subspace the admissible directions are (0,0,dz) at the centre, and the
  restricted gradient is (F.e_z)e_z because the constraint subspace is a
  linear subspace: the x/y force components are orthogonal to it.  So the
  PROJECTED direction is p_rail = P * F_cz * e_z at the centre and 0 at the
  rim.  ALL THREE FORCE COMPONENTS are computed and recorded at every
  iteration BEFORE projection (the requirement); only the DIRECTION is
  projected.  The acceptance rule is exactly the declared one:
    (a) Armijo:  U(x+) <= U(x) - c1*alpha*<F, p_rail>   (c1 = ARMIJO_C1;
        <F, p_rail> = F_cz * p_rail_z is the exact directional derivative
        along the rail)
    (b) geometry validity via evaluate_surface's own named refusals
  with the same backtracking (BACKTRACK_FACTOR, MAX_BACKTRACKS), the same
  step-scale guard (GUARD_FRAC over min_edge), the same stationarity scale
  (RESIDUAL_TOL_FRAC * mean_edge, applied to the single free DOF), the same
  stagnation scale (STAGNATION_FRAC), and the same five named terminal
  states.  Constants are IMPORTED from tools/overdamped_descent.py -- none
  is re-declared here.

  EQUIVALENCE CONTROL: on B2 the fixture is 6-fold symmetric, so the
  centre's x/y force components are EXACTLY zero (manifest gamma1
  centre_force_N == [0,0,-0.42857...]).  The projected run must therefore
  be BIT-IDENTICAL to overdamped_descent.run_descent(pos, faces, gamma,
  fixed_vertices=[0..5]).  membrane_window_demo_checks.py falsifies the
  projection instrument if that identity breaks.

  gamma = 0 short-circuits exactly as run_descent's R4-U1 branch does:
  forces are exactly zero, the run is STATIONARY at iteration 0, geometry
  bit-unchanged.

ITERATIONS ARE NOT TIME.  There is no dt anywhere in this module; the
accepted result is an optimization state, not inertial dynamics.

RENDERING CONSUMES THE ACCEPTED GEOMETRY.  The driver uploads the accepted
positions (f32 quantization for the GPU vertex format only, recorded) via
POST /mesh_bin to a SEPARATELY LAUNCHED engine instance on its own port
(NOT the operator's session), then GETs /frame once with a FIXED camera.
Every capture carries a state-ID sidecar; a capture without a matching
state record cannot certify the law (the checks refuse it).

The engine session this driver starts is the operator's to stop; the
driver itself never starts, stops, or replaces any engine unless asked
(--upload/--capture are opt-in flags).  Default mode is numerical-only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

from surface_energy_reference import evaluate_surface, InvalidSurface  # noqa: E402
from overdamped_descent import (  # noqa: E402
    ARMIJO_C1, BACKTRACK_FACTOR, MAX_BACKTRACKS, GUARD_FRAC,
    RESIDUAL_TOL_FRAC, STAGNATION_FRAC, DEFAULT_MAX_STEPS,
    STATIONARY, STAGNATED, STEP_LIMIT, NO_DESCENT_STEP, INVALID_SURFACE,
    run_descent,
)
from material_contract import (  # noqa: E402
    MaterialContract, MaterialRecord, MaterialProperty, Provenance,
    bind, ContractRefusal,
)

FIXTURES = ROOT / "docs" / "evidence" / "gpu_fixtures"
EVIDENCE = ROOT / "docs" / "evidence" / "membrane_window_demo"

FIXTURE = "b2"
RIM = list(range(6))
CENTRE = 6
# Fixed demonstration camera (the same values for every capture of this demo;
# recorded in each capture's sidecar so captures are comparable).
# GLM-DYAD-01 amendment: phi raised 0.3 -> 0.7 rad. The dyad + pixel
# measurement showed phi=0.3 (~17 deg, near grazing) foreshortens the
# membrane to a sliver and hides the centre offset; 0.7 rad (~40 deg)
# resolves the height while keeping the fixed-camera comparability law
# (all captures of a run share one camera, recorded in the sidecar).
CAM_RADIUS = 6.0
CAM_THETA = 0.0
CAM_PHI = 0.7
# slotmode 2 = fill + wireframe (engine: mode = slotmode % 10): the dyad's
# requested additional evidence -- rim edges and the centre fan visible as
# lines regardless of shading.
SLOTMODE = 2.0
NEUTRAL_RGB = (0.60, 0.60, 0.65)

# THE B2 COORDINATE MAPPING (declared, GLM-WINDOW-02): 1 world unit = 1 metre.
# gamma is admitted ONLY in J/m^2. With positions in metres:
#   area  [m^2] * gamma [J/m^2]  -> energy [J]
#   force [J/m]
# and the preconditioner P = 1/gamma_max carries [m^2/J] (GLM-WINDOW-03
# correction: the dimensionless ratio 1/gamma has the AREA unit of the
# energy's denominator -- m^2/J, NOT m/J), so the update p = P·F is
#   [m^2/J] · [J/m] = [m]   -- dimensionally a length.
# NO generic J/wu^2 unit is added to the contract; the "wu" tables in
# tools/overdamped_descent.py are bound to metres HERE, at this boundary.
WU_TO_M = 1.0
GAMMA_UNIT = "J/m^2"

# THE PRESENTATION LIFT (GLM-DYAD-02, preregistered BEFORE the controlled
# test it enables; the full preregistration is PRESENTATION_LIFT below):
# the engine rasterizes its floor and the mesh shadow in the SAME y=0 plane
# the flat membrane's rim maps to, so a coplanar flat membrane fights the
# floor for depth (round-3 dyad artifact: banding + black lens). The lift
# is a RIGID PRESENTATION TRANSLATION of the mapped upload bytes along the
# engine's vertical axis -- render presentation, never the physics.
PRESENTATION_LIFT_M = 0.5
LIFT_AXIS_ENGINE = "y"   # the engine world's vertical (B2 z maps to -y)

# THE AXIS-CONVENTION MAPPING (declared, GLM-DYAD-01; found by the dyad +
# pixel measurement): the B2 fixture is Z-UP (height in z, rim in the xy
# plane at z=0) while the engine world is Y-UP (floor = XZ, height = Y).
# Uploaded without mapping, the membrane stands VERTICALLY with the bump
# pointing along the view axis and its face normals 90 degrees from the
# top light -- the dyad read it as "empty viewport". The mapping below is a
# RIGID rotation of the ACCEPTED geometry at the upload boundary (a
# presentation transform, NOT a second simulation and not a visual
# approximation): the state of record stays the f64 B2 geometry; the engine
# consumes the mapped f32 bytes, and both hashes are recorded.
#   (x, y, z)_b2  ->  (x, z, -y)_engine      (rotation about X by -90 deg)
# so height z_b2 -> y_engine: the membrane lies IN the floor plane with the
# bump pointing UP, matching the engine's ground grid and lighting.
def axis_map_b2_to_engine(v: np.ndarray, lift_m: float = 0.0) -> np.ndarray:
    """B2 (z-up) -> engine (y-up) rigid rotation, plus an optional rigid
    vertical PRESENTATION lift (`lift_m`, engine y): render presentation
    only, the physical state of record is untouched."""
    v = np.asarray(v, dtype=np.float64)
    out = np.empty_like(v)
    out[:, 0] = v[:, 0]
    out[:, 1] = v[:, 2] + lift_m
    out[:, 2] = -v[:, 1]
    return out
AXIS_MAPPING = {
    "name": "b2_zup_to_engine_yup",
    "formula": "(x, y, z)_b2 -> (x, z, -y)_engine",
    "reason": "fixture is z-up; engine world is y-up; uploaded unmapped the "
              "membrane stood vertically and read as invisible (dyad finding)",
    "kind": "rigid rotation of the accepted geometry at the upload boundary; "
            "state of record unchanged",
}
# DIAGNOSTIC VIEW CAMERAS (explicitly recorded; never mixed with the fixed
# camera law -- each sidecar labels its camera). 'top' is the dyad-requested
# near-top-down from GLM-DYAD-01; 'low' is a mid-elevation view where the
# centre's height separates from the rim in SILHOUETTE (the top view
# collapses the rail axis almost entirely). GLM-DYAD-02 test view: 'low'.
DIAGNOSTIC_VIEWS = (
    ("top", {"radius": 3.5, "theta": 0.0, "phi": 1.45,
             "why": "near-top-down (~83 deg): minimal projection of the rail "
                    "axis; dyad-requested in GLM-DYAD-01"}),
    ("low", {"radius": 4.0, "theta": 0.0, "phi": 1.10,
             "why": "~63 deg elevation: centre height separates from the rim "
                    "in silhouette; the GLM-DYAD-02 test view"}),
    ("oblique", {"radius": 3.0, "theta": 0.0, "phi": 0.55,
                 "why": "~32 deg elevation (dyad round-4 request after the "
                        "phi=1.10 pair read INCONCLUSIVE): the 0.125 m centre "
                        "height must break the hexagon silhouette or show as "
                        "rim/centre parallax; the minimal discriminator the "
                        "dyad named"}),
)

# The engine's persisted /mesh_bin blob (CWD-relative inside the demo
# instance's own working directory; a second demo instance shares no
# persistent files with the operator's session -- verified in source).
MESH_BLOB = (ROOT / ".tmp" / "engine_demo_build" / "Release" /
             "session_snapshot" / "mesh_bin.blob")

PRESENTATION_LIFT = {
    "task": "GLM-DYAD-02 (preregistered before the controlled test)",
    "statement": "Removing floor overlap (rigid +0.5 m presentation lift "
                 "along engine y, identical across compared captures) "
                 "improves surface legibility without changing the accepted "
                 "physical geometry.",
    "prediction": "With the lift, rim and centre are distinguishable and a "
                  "raised-vs-flat comparison becomes resolvable in captures "
                  "made with identical presentation, camera and render "
                  "settings.",
    "falsifier": "The depth/banding ambiguity persists in lifted captures, "
                 "the uploaded physical geometry changes, or centre height "
                 "remains visually unresolved (recorded INCONCLUSIVE for "
                 "that visual comparison).",
    "lift_m": PRESENTATION_LIFT_M, "axis": LIFT_AXIS_ENGINE,
    "no_exaggeration": "lift is rigid, applied identically to every compared "
                       "capture; the physical geometry of record is hashed "
                       "unchanged and no contact physics is introduced",
}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    return sha256_bytes(p.read_bytes())


def load_b2() -> dict:
    fx = FIXTURES / FIXTURE
    pos32 = np.load(fx / "geometry" / "positions_f32.npy", allow_pickle=False)
    faces = np.load(fx / "geometry" / "indices_u32.npy", allow_pickle=False)
    return {
        "positions_f32": pos32,
        "positions": pos32.astype(np.float64),
        "faces": faces.astype(np.int64),
        "fixture_root": fx,
    }


# ── the validated material contract ─────────────────────────────────────────


def contract_gamma(gamma_value: float) -> tuple[MaterialContract, object]:
    """Declare gamma through the validated material contract and return the
    binding. gamma must be finite and nonnegative (surface_energy type,
    energy_area family, unit J/m^2) -- the contract refuses anything else
    with a NAMED refusal; nothing is defaulted."""
    contract = MaterialContract()
    rec = MaterialRecord(
        name="b2_fixture_gamma",
        models=frozenset({"constant_gamma_surface_energy"}),
        notes="B2 frozen fixture analytic control gamma (GLM-FREEZE 2026-09-07)",
    )
    rec.add(MaterialProperty(
        name="gamma", value=float(gamma_value), unit="J/m^2",
        source=f"docs/evidence/gpu_fixtures/{FIXTURE}/geometry/gamma*_f32.npy",
        conditions="dimensionless analytic control fixture; constant per-face "
                   "gamma held fixed during the derivative; not water or cup "
                   "material calibration",
        provenance=Provenance.RESEARCHED))
    contract.register(rec)
    b = bind(contract, "b2_fixture_gamma", FIXTURE)
    prop = b.get("gamma", as_unit="J/m^2")
    return contract, prop


def admitted_gamma_snapshot(gprop) -> dict:
    """The IMMUTABLE per-run admitted-value snapshot (GLM-WINDOW-02): the
    exact property the contract admitted, with its value bits, written into
    this run's evidence before any computation consumes it. Synthetic by
    declaration: this is the analytic control fixture's gamma, NOT a
    calibrated physical material."""
    return {
        "record_name": "b2_fixture_gamma",
        "synthetic": True,
        "synthetic_label": "dimensionless analytic control fixture gamma; "
                           "NOT a calibrated physical material",
        "property": {
            "name": gprop.name,
            "value": float(gprop.value),
            "value_hex": float(gprop.value).hex(),
            "unit": gprop.unit,
            "source": gprop.source,
            "conditions": gprop.conditions,
            "provenance": gprop.provenance.value,
        },
        "admission_path": "MaterialProperty.__post_init__ gate -> "
                          "MaterialRecord.add -> MaterialContract.register "
                          "-> bind -> Binding.get(as_unit='J/m^2')",
        "contract_refusals": "none",
    }


# ── the f32 upload boundary (GLM-WINDOW-02) ─────────────────────────────────


def quantize_positions_f32(positions_f64: np.ndarray):
    """THE f32 UPLOAD BOUNDARY. Policy: round-to-nearest f32 (the GPU vertex
    format). A converted value that is non-finite (overflow) is REFUSED, not
    clamped; a positive f64 value that rounds to zero is REPORTED as
    quantization loss -- never claimed as preservation. The original f64
    value alone is not sufficient: the validation happens on the CONVERTED
    value, at the boundary where precision is actually lost."""
    pos = np.asarray(positions_f64, dtype=np.float64)
    if not np.all(np.isfinite(pos)):
        raise ValueError("upload positions contain non-finite f64 values")
    pos32 = np.ascontiguousarray(pos, dtype="<f4")
    nonfinite = ~np.isfinite(pos32)
    if np.any(nonfinite):
        idx = np.argwhere(nonfinite)[0]
        raise ValueError(
            f"f32 upload boundary refuses overflow: f64 value "
            f"{pos[tuple(idx)]:.6e} at vertex {int(idx[0])} component "
            f"{int(idx[1])} is not representable in float32; refusing the "
            f"upload rather than clamping")
    under_mask = (pos != 0.0) & (pos32.astype(np.float64) == 0.0)
    under_idx = np.argwhere(under_mask)
    report = {
        "policy": "round-to-nearest-f32; overflow refused, never clamped; "
                  "positive underflow reported, never claimed as preservation",
        "applies_to": "positions_only",
        "n_values": int(pos.size),
        "overflow_refused": 0,
        "positive_underflow_count": int(under_idx.shape[0]),
        "positive_underflow_values_f64": [float(pos[tuple(i)])
                                          for i in under_idx[:16]],
        "max_abs_f64": float(np.max(np.abs(pos))),
        "max_abs_roundtrip_error_f64": float(np.max(np.abs(
            pos32.astype(np.float64) - pos))),
    }
    return pos32, report


def gamma_f32_boundary_status() -> dict:
    """GLM-WINDOW-03: gamma does NOT cross any float32 boundary in this CPU
    demo. It is admitted as f64 through the material contract, broadcast to
    an f64 per-face array, consumed by the f64 evaluator, and never uploaded
    to the engine (the /mesh_bin payload carries positions/normals/colors
    only -- no per-face gamma field). Stated NOT_APPLICABLE here; the future
    GPU gamma boundary is NOT certified by this demo."""
    return {
        "status": "NOT_APPLICABLE",
        "reason": "this CPU demo performs no gamma upload or f32 gamma "
                  "conversion; gamma stays float64 end to end",
        "precision_path": "float64",
        "certifies_future_gpu_gamma_boundary": False,
    }


# ── state IDs ───────────────────────────────────────────────────────────────


def state_id(source_commit: str, gamma: float, iteration: int,
             positions: np.ndarray, energy: float) -> str:
    """Deterministic state identity: same inputs -> same ID.  Binds the
    numerical state (f64 geometry, energy bits) to the task's source."""
    geom = sha256_bytes(np.ascontiguousarray(positions, dtype="<f8").tobytes())
    record = json.dumps({
        "commit": source_commit, "fixture": FIXTURE,
        "gamma_bits": float(gamma).hex(), "iteration": int(iteration),
        "geometry_sha256_f64le": geom, "energy_bits": float(energy).hex(),
    }, sort_keys=True)
    return sha256_bytes(record.encode("utf-8"))


# ── the rail-projected declared descent ─────────────────────────────────────


def projected_descent(positions, faces, gamma_arr, source_commit: str,
                      max_steps: int = DEFAULT_MAX_STEPS,
                      max_backtracks: int = MAX_BACKTRACKS) -> dict:
    """The declared optimization on the constrained subspace.

    Reuses the certified evaluator and the declared constants; the only
    structural difference from run_descent is the direction projection at
    the centre vertex onto the vertical rail (all three force components
    are computed and recorded first).  On B2 the projection is a no-op by
    symmetry -- the checks prove bit-identity with run_descent.
    """
    pos = np.asarray(positions, dtype=np.float64)
    gam = np.asarray(gamma_arr, dtype=np.float64)
    ev = evaluate_surface(pos, faces, gam)

    gamma_max = float(np.max(gam)) if gam.size else 0.0
    out = {
        "status": None, "reason": "", "positions": pos.copy(),
        "energy": ev.energy, "n_accepted": 0, "n_trials": 0,
        "iterations": [], "constants": {
            "ARMIJO_C1": ARMIJO_C1, "BACKTRACK_FACTOR": BACKTRACK_FACTOR,
            "MAX_BACKTRACKS": MAX_BACKTRACKS, "GUARD_FRAC": GUARD_FRAC,
            "RESIDUAL_TOL_FRAC": RESIDUAL_TOL_FRAC,
            "STAGNATION_FRAC": STAGNATION_FRAC,
            "DEFAULT_MAX_STEPS": DEFAULT_MAX_STEPS,
        },
        "force_all_components_first_iteration": ev.vertex_forces[CENTRE].tolist(),
    }

    # gamma = 0: forces are exactly zero -> STATIONARY at zero steps,
    # geometry bit-unchanged (mirrors run_descent's R4-U1 branch).
    if gamma_max <= 0.0:
        out["status"] = STATIONARY
        out["iterations"].append(_record(out, pos, ev, 0, source_commit))
        return out

    P = 1.0 / gamma_max
    tri = np.asarray(faces)
    a, b, c = pos[tri[:, 0]], pos[tri[:, 1]], pos[tri[:, 2]]
    e_sq = np.stack([np.sum((b - a) ** 2, axis=1),
                     np.sum((c - b) ** 2, axis=1),
                     np.sum((a - c) ** 2, axis=1)])
    mean_edge = float(np.mean(np.sqrt(e_sq)))
    min_edge = float(np.sqrt(e_sq.min()))
    residual_tol = RESIDUAL_TOL_FRAC * mean_edge
    rail0 = pos[CENTRE].copy()          # the declared rail anchor

    for it in range(1, max_steps + 1):
        F = ev.vertex_forces
        p = np.zeros_like(pos)
        p[CENTRE, 2] = P * F[CENTRE, 2]         # rail projection (z only)
        # ALL THREE components were retained above in F (recorded); the
        # direction uses only the rail component.
        p_norm = abs(p[CENTRE, 2])
        if p_norm == 0.0:
            out["status"] = STATIONARY
            out["iterations"].append(_record(out, pos, ev, it, source_commit))
            break
        alpha_max = min(1.0, (GUARD_FRAC * min_edge) / p_norm)

        accepted = False
        alpha = alpha_max
        f_dot_p = float(F[CENTRE, 2] * p[CENTRE, 2])   # >= 0 by construction
        for _bt in range(max_backtracks + 1):
            out["n_trials"] += 1
            trial = pos.copy()
            trial[CENTRE] += alpha * p[CENTRE]
            try:
                ev_plus = evaluate_surface(trial, faces, gam)
            except InvalidSurface as ex:
                alpha *= BACKTRACK_FACTOR
                if _bt == max_backtracks:
                    out["status"] = NO_DESCENT_STEP
                    out["reason"] = ex.reason
                    out["iterations"].append(_record(out, pos, ev, it, source_commit))
                    return out
                continue
            if not (ev_plus.energy <= ev.energy - ARMIJO_C1 * alpha * f_dot_p):
                alpha *= BACKTRACK_FACTOR
                if _bt == max_backtracks:
                    out["status"] = NO_DESCENT_STEP
                    out["reason"] = "armijo_not_met"
                    out["iterations"].append(_record(out, pos, ev, it, source_commit))
                    return out
                continue
            accepted = True
            break
        if not accepted:  # pragma: no cover (handled inside the loop)
            out["status"] = NO_DESCENT_STEP
            out["reason"] = "no_descent_step"
            break

        prev_energy = ev.energy
        pos = trial
        ev = ev_plus
        out["positions"] = pos.copy()
        out["energy"] = ev.energy
        out["n_accepted"] += 1
        rec = _record(out, pos, ev, it, source_commit)
        rec["alpha"] = alpha
        rec["armijo_lhs_U"] = ev.energy
        rec["armijo_rhs_U"] = prev_energy - ARMIJO_C1 * alpha * f_dot_p
        out["iterations"].append(rec)

        res = abs(P * ev.vertex_forces[CENTRE, 2])
        rec["free_residual_z"] = res
        if res <= residual_tol:
            out["status"] = STATIONARY
            break
        if prev_energy - ev.energy <= STAGNATION_FRAC * np.finfo(np.float64).eps * max(prev_energy, 1.0):
            out["status"] = STAGNATED
            out["reason"] = "decrease_below_machine_scale"
            break
    else:
        out["status"] = STEP_LIMIT

    # the rail holds by construction; measure it anyway (honesty over trust)
    out["rail_deviation_max_xy"] = float(np.max(np.abs(out["positions"][CENTRE, :2] - rail0[:2])))
    out["reaction_force_centre_xy"] = ev.vertex_forces[CENTRE, :2].tolist()
    return out


def _record(run: dict, pos, ev, it: int, source_commit: str) -> dict:
    sid = state_id(source_commit, float(ev.gamma[0]) if ev.gamma.size else 0.0,
                   it, pos, ev.energy)
    return {
        "iteration": it, "state_id": sid, "energy_J": ev.energy,
        "centre_force_N": ev.vertex_forces[CENTRE].tolist(),
        "centre_force_x_retained": ev.vertex_forces[CENTRE, 0],
        "centre_force_y_retained": ev.vertex_forces[CENTRE, 1],
        "centre_force_z_retained": ev.vertex_forces[CENTRE, 2],
        "geometry_sha256_f64le": sha256_bytes(
            np.ascontiguousarray(pos, dtype="<f8").tobytes()),
        "max_abs_force_component_N": float(np.max(np.abs(ev.vertex_forces))),
        "n_faces_valid": int(ev.n_faces),
    }


# ── gamma controls at a FIXED state ─────────────────────────────────────────


def gamma_double_control(positions, faces, gamma1: float) -> dict:
    """Fixed-state gamma doubling: U(2g) must equal 2*U(g) and F(2g) must
    equal 2*F(g) componentwise within the fixture's preregistered bounds
    (energy allowance at gamma1, force_z allowance 1e-6 N).  Doubling is a
    statement about ENERGY AND FORCE at fixed geometry; it does NOT imply
    twice-speed relaxation (iterations are not time)."""
    ev1 = evaluate_surface(positions, faces, np.full(len(faces), gamma1))
    ev2 = evaluate_surface(positions, faces, np.full(len(faces), 2.0 * gamma1))
    e_allow = 9.36375259151094e-07   # fixture preregistered allowance at gamma1
    f_allow = 1e-6                   # fixture preregistered force_z allowance
    return {
        "energy_gamma1_J": ev1.energy,
        "energy_gamma2_J": ev2.energy,
        "energy_ratio": ev2.energy / ev1.energy if ev1.energy else None,
        "energy_abs_err_J": abs(ev2.energy - 2.0 * ev1.energy),
        "energy_bound_J": e_allow,
        "force_gamma1_N": ev1.vertex_forces[CENTRE].tolist(),
        "force_gamma2_N": ev2.vertex_forces[CENTRE].tolist(),
        "force_z_ratio": (ev2.vertex_forces[CENTRE, 2] / ev1.vertex_forces[CENTRE, 2]
                          if ev1.vertex_forces[CENTRE, 2] else None),
        "force_component_abs_err_N": float(np.max(np.abs(
            ev2.vertex_forces[CENTRE] - 2.0 * ev1.vertex_forces[CENTRE]))),
        "force_bound_N": f_allow,
    }


# ── engine upload + capture (opt-in) ────────────────────────────────────────


def encode_mesh_bin(positions_f64: np.ndarray, faces: np.ndarray,
                    cam_radius: float, cam_theta: float, cam_phi: float,
                    slotmode: float = 0.0,
                    lift_m: float = PRESENTATION_LIFT_M) -> bytes:
    """The engine's /mesh_bin payload: [u32 N][u32 idxCount][f32 cr][f32 ct]
    [f32 cp][f32 slotmode][f32*9*N verts][u32*idxCount].  Vertex layout
    pos3 normal3 color3.

    THE AXIS MAPPING (GLM-DYAD-01): the accepted B2 geometry (z-up) is
    rotated into the engine's y-up world at this boundary (axis_map_b2_to_
    engine) BEFORE quantization; normals are mapped with the same rotation.
    THE PRESENTATION LIFT (GLM-DYAD-02, default PRESENTATION_LIFT_M): a
    rigid translation of the mapped upload along engine y so the surface no
    longer lies in the floor/shadow plane. Presentation only: the f64 B2
    geometry of record and the mapped f32 upload bytes are BOTH hashed and
    recorded; lift=0.0 reproduces the coplanar presentation exactly."""
    mapped = axis_map_b2_to_engine(positions_f64, lift_m=lift_m)
    pos32 = np.ascontiguousarray(mapped, dtype="<f4")
    ev = evaluate_surface(np.asarray(positions_f64, dtype=np.float64),
                          faces, np.zeros(len(faces)))
    acc = np.zeros((len(positions_f64), 3), dtype=np.float64)
    for f_idx, tri in enumerate(faces):
        for v in tri:
            acc[v] += ev.normals[f_idx]
    # map the accumulated normals with the same rigid rotation (no lift:
    # normals are directions, not positions)
    acc = axis_map_b2_to_engine(acc)
    nrm = np.linalg.norm(acc, axis=1, keepdims=True)
    nrm32 = np.where(nrm > 0, acc / np.where(nrm > 0, nrm, 1.0), 0.0).astype("<f4")
    col = np.tile(np.asarray(NEUTRAL_RGB, dtype="<f4"), (len(positions_f64), 1))
    verts = np.concatenate([pos32, nrm32, col], axis=1).astype("<f4")
    idx = np.ascontiguousarray(faces, dtype="<u4").reshape(-1)
    # idxCount is the NUMBER OF INDICES (3 per triangle), matching the
    # engine's expected size 24 + N*9*4 + idxCount*4 (main.cpp /mesh_bin).
    # Defect found live 2026-09-08: packing len(faces) here made the payload
    # 24 bytes longer than declared -> "size mismatch" (preserved failed run).
    header = struct.pack("<IIffff", len(positions_f64), int(idx.size),
                         float(cam_radius), float(cam_theta), float(cam_phi),
                         float(slotmode))
    return header + verts.tobytes() + idx.tobytes()


def upload_positions_f32(positions_f64: np.ndarray,
                         lift_m: float = PRESENTATION_LIFT_M) -> bytes:
    """The exact f32 vertex positions the payload carries (recorded so the
    render-vs-state link is checkable byte-for-byte): the AXIS-MAPPED and
    LIFTED geometry, quantized by the SAME validated boundary as the driver
    (overflow refused, positive underflow reported)."""
    mapped = axis_map_b2_to_engine(positions_f64, lift_m=lift_m)
    pos32, _report = quantize_positions_f32(mapped)
    return pos32.tobytes()


def blob_position_hash() -> str:
    """Hash of the POSITION bytes in the engine's persisted /mesh_bin blob
    (documented format: [u32 N][u32 idxCount][f32 cr ct cp slotmode][verts
    pos3+nrm3+col3 f32][u32 indices]) -- positions only, NEVER a whole-blob
    hash compared against a position hash (GLM-WINDOW-03 rule). The blob is
    CWD-relative to the DEMO INSTANCE; when a second build directory is in
    use, CHIMERA_MESH_BLOB overrides the default path so corroboration
    always reads the engine that actually served the capture."""
    import os
    blob_path = os.environ.get("CHIMERA_MESH_BLOB") or MESH_BLOB
    blob = Path(blob_path).read_bytes()
    n, _idx_count = struct.unpack_from("<II", blob, 0)
    pos = b"".join(blob[24 + i * 36: 24 + i * 36 + 12] for i in range(n))
    return sha256_bytes(pos)


def diagnostic_capture(engine_url: str, positions_f64: np.ndarray,
                       faces: np.ndarray, state: dict, outdir: Path,
                       label: str, gamma_value: float, view_name: str,
                       view: dict, lift_m: float) -> dict:
    """One DIAGNOSTIC extra view of the SAME uploaded state: an
    explicitly-labelled recorded camera (never the fixed demo camera), with
    the blob corroboration asserted AT capture time (no other upload may
    intervene)."""
    upload32 = upload_positions_f32(positions_f64, lift_m=lift_m)
    upload_hash = sha256_bytes(upload32)
    payload = encode_mesh_bin(positions_f64, faces, view["radius"],
                              view["theta"], view["phi"], SLOTMODE,
                              lift_m=lift_m)
    status, body = http_post(f"{engine_url}/mesh_bin", payload,
                             "application/octet-stream")
    if status != 200 or b'"ok":true' not in body:
        raise RuntimeError(f"mesh_bin upload failed: {status} {body[:200]!r}")
    cam = json.dumps({"cam_radius": view["radius"],
                      "cam_theta": view["theta"],
                      "cam_phi": view["phi"]}).encode()
    http_post(f"{engine_url}/camera", cam, "application/json")
    status, png, ctype = http_get(f"{engine_url}/frame")
    if status != 200 or "image/png" not in ctype:
        raise RuntimeError(f"/frame failed: {status} {ctype!r}")
    blob_hash = blob_position_hash()
    if blob_hash != upload_hash:
        raise RuntimeError(
            f"blob corroboration FAILED at capture: {blob_hash} != {upload_hash}")
    png_path = outdir / f"{label}_{view_name}.png"
    png_path.write_bytes(png)
    record = {
        "label": f"{label}_{view_name}",
        "kind": "DIAGNOSTIC extra view; explicitly-labelled recorded camera, "
                "not the demo's fixed camera",
        "view": view,
        "engine_url": engine_url,
        "png_file": str(png_path.relative_to(ROOT)),
        "png_sha256": sha256_bytes(png),
        "camera": {"radius": view["radius"], "theta": view["theta"],
                   "phi": view["phi"]},
        "slotmode": SLOTMODE,
        "presentation_lift": {"axis": LIFT_AXIS_ENGINE, "metres": lift_m,
                              "kind": "rigid render-presentation translation; "
                                      "physical state of record unchanged"},
        "upload_positions_f32le_sha256": upload_hash,
        "blob_position_hash_at_capture": blob_hash,
        "blob_corroboration": "MATCH",
        "state_id": state["state_id"],
        "state": {
            "fixture": FIXTURE, "gamma_J_per_m2": gamma_value,
            "iteration": state["iteration"], "energy_J": state["energy_J"],
            "geometry_sha256_f64le": state["geometry_sha256_f64le"],
            "centre_height_b2_z_m": float(positions_f64[CENTRE, 2]),
            "upload_positions_f32le_sha256": upload_hash,
        },
    }
    sidecar = outdir / f"{label}_{view_name}.capture.json"
    sidecar.write_text(json.dumps(record, indent=2), encoding="utf-8")
    record["sidecar"] = str(sidecar.relative_to(ROOT))
    return record


def http_post(url: str, body: bytes, content_type: str, timeout: float = 30.0):
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": content_type},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def http_get(url: str, timeout: float = 30.0):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.status, r.read(), r.headers.get("Content-Type", "")


def capture_from_engine(engine_url: str, positions_f64: np.ndarray,
                        faces: np.ndarray, state: dict, outdir: Path,
                        label: str, gamma_value: float,
                        lift_m: float = PRESENTATION_LIFT_M) -> dict:
    """One fixed-camera capture with its state-ID sidecar.  `state` is the
    final iteration record (iteration/state_id/energy_J/geometry hash).
    `lift_m` is the preregistered presentation lift (identical across every
    compared capture; recorded in the sidecar). Returns the capture record;
    the sidecar is what makes the capture certifiable."""
    payload = encode_mesh_bin(positions_f64, faces, CAM_RADIUS, CAM_THETA,
                              CAM_PHI, SLOTMODE, lift_m=lift_m)
    status, body = http_post(f"{engine_url}/mesh_bin", payload,
                             "application/octet-stream")
    if status != 200 or b'"ok":true' not in body:
        raise RuntimeError(f"mesh_bin upload failed: {status} {body[:200]!r}")
    # fixed camera (same values the upload carried; explicit for the record)
    cam = json.dumps({"cam_radius": CAM_RADIUS, "cam_theta": CAM_THETA,
                      "cam_phi": CAM_PHI}).encode()
    http_post(f"{engine_url}/camera", cam, "application/json")
    status, png, ctype = http_get(f"{engine_url}/frame")
    if status != 200 or "image/png" not in ctype:
        raise RuntimeError(f"/frame failed: {status} {ctype!r}")
    png_path = outdir / f"{label}.png"
    png_path.write_bytes(png)
    upload32 = upload_positions_f32(positions_f64, lift_m=lift_m)
    record = {
        "label": label, "utc": datetime.now(timezone.utc).isoformat(),
        "engine_url": engine_url,
        "png_file": str(png_path.relative_to(ROOT)),
        "png_sha256": sha256_bytes(png),
        "camera": {"radius": CAM_RADIUS, "theta": CAM_THETA, "phi": CAM_PHI},
        "slotmode": SLOTMODE,
        "presentation_lift": {"axis": LIFT_AXIS_ENGINE, "metres": lift_m,
                              "kind": "rigid render-presentation translation; "
                                      "physical state of record unchanged"},
        "state_id": state["state_id"],
        "state": {
            "fixture": FIXTURE, "gamma_J_per_m2": gamma_value,
            "iteration": state["iteration"], "energy_J": state["energy_J"],
            "geometry_sha256_f64le": state["geometry_sha256_f64le"],
            "centre_height_b2_z_m": float(positions_f64[CENTRE, 2]),
            "upload_positions_f32le_sha256": sha256_bytes(upload32),
        },
        "certifiable": True,   # the CHECKS verify this, not this flag
    }
    sidecar = outdir / f"{label}.capture.json"
    sidecar.write_text(json.dumps(record, indent=2), encoding="utf-8")
    record["sidecar"] = str(sidecar.relative_to(ROOT))
    return record


# ── main ────────────────────────────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gamma", type=float, default=1.0)
    ap.add_argument("--max-steps", type=int, default=DEFAULT_MAX_STEPS)
    ap.add_argument("--engine-url", default=None,
                    help="e.g. http://localhost:8091 -- a SEPARATE demo "
                         "instance you started; the operator's session is "
                         "never contacted")
    ap.add_argument("--label", default=None)
    ap.add_argument("--no-capture", action="store_true",
                    help="numerical run only; no engine contact")
    ap.add_argument("--lift-m", type=float, default=PRESENTATION_LIFT_M,
                    help="rigid vertical PRESENTATION lift (engine y, "
                         "metres); 0.0 = the original coplanar presentation")
    ap.add_argument("--view", choices=("fixed", "top", "low", "oblique", "both"),
                    default="fixed",
                    help="additional explicitly-recorded diagnostic cameras "
                         "to capture of the same uploaded state")
    args = ap.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    outdir = EVIDENCE / stamp
    outdir.mkdir(parents=True, exist_ok=False)

    b2 = load_b2()
    contract, gprop = contract_gamma(args.gamma)   # validated at the door
    gamma_val = float(gprop.value)
    gamma_arr = np.full(len(b2["faces"]), gamma_val)

    head, _ = _git("rev-parse", "HEAD")
    commit = head.strip()

    run = projected_descent(b2["positions"], b2["faces"], gamma_arr, commit,
                            max_steps=args.max_steps)
    final_state = run["iterations"][-1]

    # THE UPLOAD STATE (iteration 0, BEFORE any accepted step): the exact
    # geometry/force the run starts from, so captures and numerical records
    # share one pre-step anchor. The force here is compared by the checks
    # against the FROZEN manifest reference within the manifest's own
    # componentwise budget -- not against the analytic ideal.
    ev_upload = evaluate_surface(b2["positions"], b2["faces"], gamma_arr)
    upload_state = {
        "iteration": 0,
        "state_id": state_id(commit, gamma_val, 0, b2["positions"],
                             ev_upload.energy),
        "energy_J": ev_upload.energy,
        "geometry_sha256_f64le": sha256_bytes(
            np.ascontiguousarray(b2["positions"], dtype="<f8").tobytes()),
        "centre_force_N": ev_upload.vertex_forces[CENTRE].tolist(),
        "centre_force_x_retained": ev_upload.vertex_forces[CENTRE, 0],
        "centre_force_y_retained": ev_upload.vertex_forces[CENTRE, 1],
        "centre_force_z_retained": ev_upload.vertex_forces[CENTRE, 2],
    }

    # the f32 upload boundary is validated on the CONVERTED values (the
    # accepted geometry), before anything is encoded for the engine. This
    # boundary applies to POSITIONS ONLY; gamma has no upload boundary in
    # this demo (gamma_f32_boundary_status records NOT_APPLICABLE).
    pos32_upload, upload_report = quantize_positions_f32(
        axis_map_b2_to_engine(run["positions"], lift_m=args.lift_m))
    upload_report["axis_mapping"] = AXIS_MAPPING
    upload_report["presentation_lift"] = {"axis": LIFT_AXIS_ENGINE,
                                          "metres": args.lift_m}

    # the zero-gamma control, recorded alongside (F2's evidence source)
    zero_run = projected_descent(b2["positions"], b2["faces"],
                                 np.zeros(len(b2["faces"])), commit,
                                 max_steps=args.max_steps)
    zero_final = zero_run["iterations"][-1]

    result = {
        "schema": "chimera-membrane-window-demo-v1", "utc": stamp,
        "source_commit": commit, "fixture": FIXTURE,
        "gamma_J_per_m2": gamma_val,
        "gamma_admitted": admitted_gamma_snapshot(gprop),
        "coordinate_mapping": {"wu_to_m": WU_TO_M,
                               "gamma_unit": GAMMA_UNIT,
                               "declaration": "1 wu = 1 m; gamma admitted "
                                              "only in J/m^2"},
        "f32_upload_boundary": upload_report,
        "gamma_f32_boundary": gamma_f32_boundary_status(),
        "rim_pinned": RIM, "centre_vertex": CENTRE,
        "rail": "centre x,y fixed at initial; z free (vertical rail)",
        "upload_state": upload_state,
        "status": run["status"], "reason": run["reason"],
        "n_accepted": run["n_accepted"], "n_trials": run["n_trials"],
        "energy_initial_J": run["iterations"][0]["energy_J"],
        "energy_final_J": final_state["energy_J"],
        "centre_force_initial_N": run["iterations"][0]["centre_force_N"],
        "centre_force_final_N": final_state["centre_force_N"],
        "rail_deviation_max_xy": run.get("rail_deviation_max_xy"),
        "iterations": run["iterations"],
        "constants": run["constants"],
        "iterations_are_not_time": True,
        "gamma_double_control_fixed_state":
            gamma_double_control(run["positions"], b2["faces"], gamma_val),
        "zero_gamma_control": {
            "status": zero_run["status"], "reason": zero_run["reason"],
            "n_accepted": zero_run["n_accepted"],
            "n_trials": zero_run["n_trials"],
            "energy_J": zero_run["energy"],
            "iteration": zero_final["iteration"],
            "geometry_sha256_f64le": zero_final["geometry_sha256_f64le"],
            "state_id": zero_final["state_id"],
        },
        "checks_script": "tools/membrane_window_demo_checks.py",
    }
    (outdir / "result.json").write_text(json.dumps(result, indent=2),
                                        encoding="utf-8")

    captures = []
    if args.engine_url and not args.no_capture:
        captures.append(capture_from_engine(
            args.engine_url, run["positions"], b2["faces"], final_state,
            outdir, args.label or f"gamma{gamma_val:g}_final", gamma_val,
            lift_m=args.lift_m))
        for view_name, view in DIAGNOSTIC_VIEWS:
            if args.view == "fixed":
                continue
            if args.view in ("top", "low") and view_name != args.view:
                continue
            captures.append(diagnostic_capture(
                args.engine_url, run["positions"], b2["faces"], final_state,
                outdir, args.label or f"gamma{gamma_val:g}_final", gamma_val,
                view_name, view, lift_m=args.lift_m))
    result["presentation_lift"] = {
        "metres": args.lift_m, "axis": LIFT_AXIS_ENGINE,
        "preregistration": PRESENTATION_LIFT,
    }
    result["captures"] = captures
    (outdir / "result.json").write_text(json.dumps(result, indent=2),
                                        encoding="utf-8")

    print(json.dumps({
        "evidence": str(outdir), "status": run["status"],
        "gamma_J_per_m2": gamma_val,
        "lift_m": args.lift_m,
        "n_accepted": run["n_accepted"],
        "energy_initial_J": result["energy_initial_J"],
        "energy_final_J": result["energy_final_J"],
        "state_id": final_state["state_id"],
        "captures": [c["png_file"] for c in captures],
    }, indent=2))
    return 0 if run["status"] in (STATIONARY, STAGNATED, STEP_LIMIT) else 1


def _git(*args):
    import subprocess
    p = subprocess.run(["git", "-C", str(ROOT), *args],
                       capture_output=True, text=True)
    return p.stdout, p.returncode


if __name__ == "__main__":
    raise SystemExit(main())
