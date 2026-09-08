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
CAM_RADIUS = 6.0
CAM_THETA = 0.0
CAM_PHI = 0.3
NEUTRAL_RGB = (0.60, 0.60, 0.65)


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
                    slotmode: float = 0.0) -> bytes:
    """The engine's /mesh_bin payload: [u32 N][u32 idxCount][f32 cr][f32 ct]
    [f32 cp][f32 slotmode][f32*9*N verts][u32*idxCount].  Vertex layout
    pos3 normal3 color3.  Normals are the area-weighted accumulation of the
    ACCEPTED geometry's face normals (from the certified evaluator's
    current-geometry normals); colors are a fixed neutral -- no second
    visual law."""
    pos32 = np.ascontiguousarray(positions_f64, dtype="<f4")
    ev = evaluate_surface(np.asarray(positions_f64, dtype=np.float64),
                          faces, np.zeros(len(faces)))
    acc = np.zeros((len(positions_f64), 3), dtype=np.float64)
    for f_idx, tri in enumerate(faces):
        for v in tri:
            acc[v] += ev.normals[f_idx]
    nrm = np.linalg.norm(acc, axis=1, keepdims=True)
    nrm32 = np.where(nrm > 0, acc / np.where(nrm > 0, nrm, 1.0), 0.0).astype("<f4")
    col = np.tile(np.asarray(NEUTRAL_RGB, dtype="<f4"), (len(positions_f64), 1))
    verts = np.concatenate([pos32, nrm32, col], axis=1).astype("<f4")
    idx = np.ascontiguousarray(faces, dtype="<u4")
    header = struct.pack("<IIffff", len(positions_f64), len(faces),
                         float(cam_radius), float(cam_theta), float(cam_phi),
                         float(slotmode))
    return header + verts.tobytes() + idx.tobytes()


def upload_positions_f32(positions_f64: np.ndarray) -> bytes:
    """The exact f32 vertex positions the payload carries (recorded so the
    render-vs-state link is checkable byte-for-byte)."""
    return np.ascontiguousarray(positions_f64, dtype="<f4").tobytes()


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
                        label: str) -> dict:
    """One fixed-camera capture with its state-ID sidecar.  Returns the
    capture record; the sidecar is what makes the capture certifiable."""
    payload = encode_mesh_bin(positions_f64, faces, CAM_RADIUS, CAM_THETA, CAM_PHI)
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
    upload32 = upload_positions_f32(positions_f64)
    record = {
        "label": label, "utc": datetime.now(timezone.utc).isoformat(),
        "engine_url": engine_url,
        "png_file": str(png_path.relative_to(ROOT)),
        "png_sha256": sha256_bytes(png),
        "camera": {"radius": CAM_RADIUS, "theta": CAM_THETA, "phi": CAM_PHI},
        "state_id": state["state_id"],
        "state": {
            "fixture": FIXTURE, "gamma_J_per_m2": state["gamma"],
            "iteration": state["iteration"], "energy_J": state["energy"],
            "geometry_sha256_f64le": state["geometry_sha256_f64le"],
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

    # the zero-gamma control, recorded alongside (F2's evidence source)
    zero_run = projected_descent(b2["positions"], b2["faces"],
                                 np.zeros(len(b2["faces"])), commit,
                                 max_steps=args.max_steps)
    zero_final = zero_run["iterations"][-1]

    result = {
        "schema": "chimera-membrane-window-demo-v1", "utc": stamp,
        "source_commit": commit, "fixture": FIXTURE,
        "gamma_J_per_m2": gamma_val,
        "gamma_provenance": {"source": gprop.source, "unit": gprop.unit,
                             "provenance": gprop.provenance.value,
                             "conditions": gprop.conditions},
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
            outdir, args.label or f"gamma{gamma_val:g}_final"))
    result["captures"] = captures
    (outdir / "result.json").write_text(json.dumps(result, indent=2),
                                        encoding="utf-8")

    print(json.dumps({
        "evidence": str(outdir), "status": run["status"],
        "gamma_J_per_m2": gamma_val,
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
