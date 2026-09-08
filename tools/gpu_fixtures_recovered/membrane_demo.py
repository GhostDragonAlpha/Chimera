"""membrane_demo.py — A3 milestone, step 1: the CPU membrane relaxation.

A triangulated disk spans a fixed planar rim; a smooth out-of-plane bump is
relaxed toward the flat minimum by the certified guarded descent
(overdamped_descent.run_descent, R4 law). This is the numerical-reference
run that ASTRA's A3 demonstration will later transcribe to GPU (per the A2
contract) and only then verify in the engine window (DYAD).

PREREGISTRATION — written before first execution; adopted from ASTRA A3
(2026-09-07). Bounds marked PROVISIONAL await ASTRA-B2's concretization and
are never silently tightened to obtain a pass.

STATEMENT  For this nondegenerate disk-like mesh with its rim pinned, fixed
           positive gamma and no other forces, accepted optimization steps
           reduce current-area energy U = sum_t gamma_t A_t while preserving
           the rim.

PREDICTIONS
  P1  U is nonincreasing across every accepted step; every pinned
      coordinate is bit-identical to its initial value; the run's recorded
      initial energy equals an independent evaluation bit-exactly.
  P2  The bump relaxes toward the planar reference (PROVISIONAL bounds):
      U_final - gamma*A_flat <= 0.1*(U_0 - gamma*A_flat) and
      max|z_final| <= 0.1*max|z_0|.
  P3  Zero-gamma control: gamma = 0 returns status "stationary" with zero
      accepted steps and bit-identical geometry.
  P4  Gamma-doubling control at IDENTICAL geometry: U and every force
      component are EXACTLY 2x. (Exact because 2 is a power of two: doubling
      changes no mantissa. Any non-power-of-two factor is only approximate;
      a P=1/gamma_max optimizer intentionally cancels uniform gamma scaling,
      so NO double-speed relaxation is predicted — A3.)
  P5  The terminal verdict is reported verbatim ("stationary" or "stagnated"
      are the accepted terminal states for this fixture); it is never
      relabeled "converged" and never claimed as proof of stable equilibrium.

FALSIFIERS  Any pin moves; any accepted step increases U; the zero-gamma
control deforms; P4 returns anything but exactly 2x; results presented as
physical time evolution. Iterations are iterations — NOT seconds.

UNITS  positions [wu], gamma [J/wu^2], U [J], forces [J/wu], residual [wu].
The material is a SYNTHETIC DECLARED interface (GAMMA below, provenance:
fixture declaration); no physical calibration is claimed. Admission routing
through material_contract is deferred until BP-A1 lands (unit-family table).

VERIFICATION CLASS  CPU numerical reference only. No engine-window, DYAD,
GPU, or visual claim exists or may be inferred from this file.
"""
from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

import numpy as np

_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(_TOOLS))

from surface_energy_reference import evaluate_surface   # noqa: E402
from overdamped_descent import run_descent              # noqa: E402
from evidence_output import default_stamp               # noqa: E402

GAMMA = 1.0          # [J/wu^2] synthetic DECLARED interface (fixture choice)
N_RING = 12          # boundary + mid-ring vertex count   (fixture choice)
RADIUS = 1.0         # [wu] rim radius                    (fixture choice)
BUMP = 0.1           # [wu] peak bump amplitude           (fixture choice)
BUMP_SIGMA = 0.35    # [wu] gaussian bump width           (fixture choice)
MAX_STEPS = 2000     # budget; exhaustion reports step_limit verbatim


def disk_mesh(n_ring: int = N_RING, radius: float = RADIUS,
              bump: float = BUMP, sigma: float = BUMP_SIGMA):
    """Center + mid ring + boundary ring, CCW-wound, gaussian bump on the
    interior vertices only (the rim is planar by construction).
    Returns (V, F, boundary_indices, A_flat)."""
    ang = 2.0 * np.pi * np.arange(n_ring) / n_ring
    cos, sin = np.cos(ang), np.sin(ang)
    mid = np.stack([0.5 * radius * cos, 0.5 * radius * sin,
                    np.zeros(n_ring)], axis=1)
    r2 = mid[:, 0] ** 2 + mid[:, 1] ** 2
    mid[:, 2] = bump * np.exp(-r2 / (2.0 * sigma ** 2))
    center = np.array([[0.0, 0.0, bump]])
    outer = np.stack([radius * cos, radius * sin, np.zeros(n_ring)], axis=1)
    V = np.vstack([center, mid, outer])

    mids = list(range(1, n_ring + 1))
    outs = list(range(n_ring + 1, 2 * n_ring + 1))
    F = []
    for i in range(n_ring):                       # center fan
        j = (i + 1) % n_ring
        F.append([0, mids[i], mids[j]])
    for i in range(n_ring):                       # annulus, 2 triangles per quad
        j = (i + 1) % n_ring
        F.append([mids[i], outs[i], outs[j]])
        F.append([mids[i], outs[j], mids[j]])
    F = np.asarray(F, dtype=np.int64)

    Vf = V.copy()                                 # planar reference area
    Vf[:, 2] = 0.0
    a, b, c = Vf[F[:, 0]], Vf[F[:, 1]], Vf[F[:, 2]]
    A_flat = float(0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1).sum())
    return V, F, [int(i) for i in outs], A_flat


def main() -> int:
    V0, F, boundary, A_flat = disk_mesh()
    gamma = GAMMA

    ev0 = evaluate_surface(V0, F, gamma)
    U0 = ev0.energy

    r = run_descent(V0.copy(), F, gamma, fixed_vertices=boundary,
                    max_steps=MAX_STEPS)

    Uend = r.energy
    excess0 = U0 - gamma * A_flat        # the bump's initial area excess [J]
    excess1 = Uend - gamma * A_flat      # P2 bound PROVISIONAL pending B2
    z0 = float(np.abs(V0[:, 2]).max())
    z1 = float(np.abs(r.positions[:, 2]).max())
    mono = all(r.energies[i + 1] <= r.energies[i]
               for i in range(len(r.energies) - 1))
    pins_exact = bool(np.array_equal(r.positions[boundary], V0[boundary]))
    u0_consistent = bool(len(r.energies) > 0 and r.energies[0] == U0)

    rz = run_descent(V0.copy(), F, 0.0, fixed_vertices=boundary,
                     max_steps=10)       # P3 zero-gamma control
    zg = bool(rz.status == "stationary" and rz.n_accepted == 0
              and np.array_equal(rz.positions, V0))

    ev1x = evaluate_surface(V0, F, gamma)          # P4 doubling exactness
    ev2x = evaluate_surface(V0, F, 2.0 * gamma)
    dbl = bool(ev2x.energy == 2.0 * ev1x.energy
               and np.equal(ev2x.vertex_forces,
                            2.0 * ev1x.vertex_forces).all())

    p5 = r.status in ("stationary", "stagnated")   # P5 verdict verbatim

    checks = {
        "P1_energy_nonincrease_pins_exact": bool(mono and pins_exact
                                                 and u0_consistent),
        "P2_bump_relaxes_to_planar": bool(excess1 <= 0.1 * excess0
                                          and z1 <= 0.1 * z0),
        "P3_zero_gamma_control": zg,
        "P4_gamma_doubling_exact": dbl,
        "P5_verdict_verbatim": p5,
    }
    ok = all(checks.values())

    record = {
        "what": "A3 milestone step 1 — CPU membrane relaxation (numerical only)",
        "registration": "ASTRA A3 adopted 2026-09-07; P2 bounds PROVISIONAL pending B2",
        "verification_class": "CPU numerical reference; NO engine-window/DYAD/GPU claim",
        "time_note": "iterations are NOT seconds; no physical time is simulated",
        "python": platform.python_version(),
        "numpy": np.__version__,
        "fixture": {"gamma_J_per_wu2": gamma, "n_ring": N_RING,
                    "radius_wu": RADIUS, "bump_wu": BUMP,
                    "bump_sigma_wu": BUMP_SIGMA, "n_vertices": int(V0.shape[0]),
                    "n_faces": int(F.shape[0]), "A_flat_wu2": A_flat,
                    "max_steps": MAX_STEPS,
                    "fixture_choice_note": "chosen before first run; B2 may replace"},
        "U0_J": U0, "U_final_J": Uend,
        "U_flat_reference_J": gamma * A_flat,
        "excess_initial_J": excess0, "excess_final_J": excess1,
        "max_abs_z_initial_wu": z0, "max_abs_z_final_wu": z1,
        "status": r.status, "reason": r.reason,
        "n_accepted": r.n_accepted, "n_trials": r.n_trials,
        "free_residual_wu": r.free_residual,
        "net_pin_load_J_per_wu": (None if r.reaction_forces is None
                                  else float(np.sum(r.reaction_forces))),
        "constants_audit": r.constants_audit,
        "checks": checks, "all_pass": ok,
    }

    out_dir = _TOOLS.parent / "agent_logs" / "glm_foundation_g01"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"membrane_demo_results_{default_stamp()}.json"
    if out_path.exists():                # evidence law: never silent overwrite
        raise SystemExit(f"evidence_path_exists: {out_path} — rerun or --out")
    out_path.write_text(json.dumps(record, indent=2), encoding="utf-8")

    width = max(len(k) for k in checks)
    for k, v in checks.items():
        print(f"  {k:<{width}}  {'PASS' if v else 'FAIL'}")
    print(f"  status={r.status}  n_accepted={r.n_accepted}  n_trials={r.n_trials}")
    print(f"  U: {U0:.12g} -> {Uend:.12g} J   (flat reference "
          f"{gamma * A_flat:.12g} J)")
    print(f"  residual={r.free_residual:.3g} wu   "
          f"max|z|: {z0:.4g} -> {z1:.4g} wu")
    print(f"  results: {out_path}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
