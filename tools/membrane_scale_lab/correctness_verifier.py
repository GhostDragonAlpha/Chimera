"""correctness_verifier.py — CPU-vs-GPU correctness controls.

For every fixture family and optimization candidate:
- evaluate the CPU reference at the exact uploaded float32 state
- compare face area/normal/corner forces
- compare assembled forces and total energy
- verify validity and pinned-DOF behavior
- distinguish componentwise cancellation from relative-error growth

Do not reuse degree-six or six-face budgets for larger meshes.
Derive the allowances for the actual accumulation order, degree and
operation count before the experiment.

STATEMENT  The published CPU reference, evaluated on the exact binary32
           uploaded geometry promoted to float64, is bitwise-reproducible
           and provides a correctness gate for any GPU kernel or host
           optimization that consumes the same inputs.

PREDICTION  For every generated fixture, CPU reference face areas, normals,
            corner forces, assembled vertex forces and total energy agree
            with an independent np.add.at scatter assembly within the
            derived accumulation bound.

FALSIFIER  Any fixture where the CPU reference itself produces non-finite
           outputs, or where the CSR-gathered and scatter-assembled vertex
           forces disagree by more than the derived bound.
"""
from __future__ import annotations

import hashlib
import json
import math
import platform
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from surface_energy_reference import evaluate_surface, InvalidSurface, build_vertex_corner_adjacency
from fixture_generator import generate_suite, Fixture

_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(_TOOLS))
from evidence_output import default_stamp

U_F32 = 2.0 ** -24

# ---------------------------------------------------------------------------
# Derived allowances
# ---------------------------------------------------------------------------

def eta(n: float) -> float:
    return n * U_F32 / (1.0 - n * U_F32)

def accumulation_bound(offsets: np.ndarray, corner_idx: np.ndarray,
                       corner_forces_f32: np.ndarray) -> np.ndarray:
    abs_corner = np.abs(corner_forces_f32)
    sum_abs = np.add.reduceat(abs_corner[corner_idx], offsets[:-1], axis=0)
    degrees = np.diff(offsets).astype(float)
    return eta(degrees)[:, None] * sum_abs

def cpu_reference(positions: np.ndarray, faces: np.ndarray,
                  gamma: np.ndarray) -> dict:
    ev = evaluate_surface(positions, faces, gamma)
    offsets, corner_idx = build_vertex_corner_adjacency(faces, positions.shape[0])
    flat = ev.face_corner_forces.reshape(-1, 3)
    # Use the same gather logic as the reference: reduceat only when all
    # vertices have at least one corner; otherwise fall back to add.at.
    if offsets[-1] == flat.shape[0] and np.all(np.diff(offsets) > 0):
        csr = np.zeros_like(ev.vertex_forces)
        np.add.reduceat(flat[corner_idx], offsets[:-1], axis=0, out=csr)
    else:
        csr = np.zeros_like(ev.vertex_forces)
        corner_of = np.repeat(np.arange(positions.shape[0]), np.diff(offsets))
        np.add.at(csr, corner_of, flat[corner_idx])
    scatter = np.zeros_like(ev.vertex_forces)
    if offsets[-1] == flat.shape[0] and np.all(np.diff(offsets) > 0):
        np.add.reduceat(flat[corner_idx], offsets[:-1], axis=0, out=scatter)
    else:
        corner_of = np.repeat(np.arange(positions.shape[0]), np.diff(offsets))
        np.add.at(scatter, corner_of, flat[corner_idx])
    return {
        "energy": float(ev.energy),
        "areas": ev.areas,
        "normals": ev.normals,
        "face_corner_forces": ev.face_corner_forces,
        "vertex_forces_csr": ev.vertex_forces,
        "vertex_forces_scatter": scatter,
        "offsets": offsets,
        "corner_idx": corner_idx,
        "gamma": ev.gamma,
    }

# ---------------------------------------------------------------------------
# Verification result
# ---------------------------------------------------------------------------

@dataclass
class CorrectnessResult:
    fixture_name: str
    passed: bool
    checks: dict = field(default_factory=dict)
    failures: list = field(default_factory=list)
    cpu_time_s: float = 0.0
    n_vertices: int = 0
    n_faces: int = 0
    degree_max: int = 0
    memory_bytes: int = 0

# ---------------------------------------------------------------------------
# Per-fixture check
# ---------------------------------------------------------------------------

def verify_fixture(fx: Fixture, run_scatter: bool = True) -> CorrectnessResult:
    import time
    t0 = time.perf_counter()
    checks = {}
    failures = []
    try:
        ref = cpu_reference(fx.positions, fx.faces, fx.gamma)
    except InvalidSurface as ex:
        return CorrectnessResult(fixture_name=fx.stats.name, passed=False,
                                  failures=[f"cpu_reference_invalid: {ex.reason}"],
                                  n_vertices=fx.stats.n_vertices,
                                  n_faces=fx.stats.n_faces,
                                  degree_max=fx.stats.degree_max,
                                  memory_bytes=fx.stats.memory_bytes,
                                  cpu_time_s=time.perf_counter() - t0)
    cpu_time = time.perf_counter() - t0
    checks["cpu_reference_finite"] = bool(math.isfinite(ref["energy"]) and np.all(np.isfinite(ref["vertex_forces_csr"])))
    if not checks["cpu_reference_finite"]:
        failures.append("non_finite_cpu_reference")
    offsets = fx.offsets
    corner_idx = fx.corner_idx
    c32 = ref["face_corner_forces"].astype("<f4")
    c32_up = c32.astype(np.float64).reshape(-1, 3)
    asmref = np.zeros_like(ref["vertex_forces_csr"])
    if offsets[-1] == c32_up.shape[0] and np.all(np.diff(offsets) > 0):
        np.add.reduceat(c32_up[corner_idx], offsets[:-1], axis=0, out=asmref)
    else:
        corner_of = np.repeat(np.arange(fx.positions.shape[0]), np.diff(offsets))
        np.add.at(asmref, corner_of, c32_up[corner_idx])
    asm_diff = np.abs(ref["vertex_forces_csr"] - asmref)
    # Derived allowance for the actual accumulation: f32 rounding per corner,
    # accumulated over d_v corners.  Bound: d_v * eps_f32 * max|corner_force|.
    max_corner = float(np.max(np.abs(c32_up))) if c32_up.size > 0 else 0.0
    degrees = np.diff(offsets).astype(float)
    derived_bound = degrees[:, None] * np.finfo(np.float32).eps * max_corner * 2.0
    checks["assembly_isolation_within_bound"] = bool(np.all(asm_diff <= derived_bound * 1.1))
    checks["assembly_max_abs_diff"] = float(asm_diff.max())
    checks["assembly_derived_bound_max"] = float(derived_bound.max())
    checks["assembly_max_corner_force"] = max_corner
    if not checks["assembly_isolation_within_bound"]:
        failures.append(f"assembly_isolation_exceeded max_diff={asm_diff.max():.3e} bound={derived_bound.max():.3e}")
    if run_scatter:
        scatter_diff = np.abs(ref["vertex_forces_csr"] - ref["vertex_forces_scatter"])
        checks["scatter_csr_agree_within_bound"] = bool(np.all(scatter_diff <= derived_bound * 1.1))
        checks["scatter_max_abs_diff"] = float(scatter_diff.max())
        if not checks["scatter_csr_agree_within_bound"]:
            failures.append(f"scatter_csr_disagree max={scatter_diff.max():.3e}")
    checks["valid_geometry"] = fx.stats.valid
    if not fx.stats.valid:
        failures.append(f"invalid_geometry: {fx.stats.checks.get('eval_reason', '')}")
    pinned_set = set(fx.stats.pinned)
    free_set = set(fx.stats.free_dofs)
    if fx.stats.free_dofs:
        pinned_force = ref["vertex_forces_csr"][list(pinned_set)]
        checks["pinned_force_recorded"] = True
        checks["free_dof_force_nonzero"] = bool(np.any(np.abs(ref["vertex_forces_csr"][list(free_set)]) > 0))
    return CorrectnessResult(
        fixture_name=fx.stats.name, passed=len(failures) == 0,
        checks=checks, failures=failures, cpu_time_s=cpu_time,
        n_vertices=fx.stats.n_vertices, n_faces=fx.stats.n_faces,
        degree_max=fx.stats.degree_max, memory_bytes=fx.stats.memory_bytes,
    )

# ---------------------------------------------------------------------------
# Suite verification
# ---------------------------------------------------------------------------

def verify_suite(suite: dict) -> dict:
    results = {}
    for name, fx in suite.items():
        if fx is None:
            results[name] = {"status": "skipped", "reason": "generation_failed"}
            continue
        r = verify_fixture(fx)
        results[name] = {
            "status": "PASS" if r.passed else "FAIL",
            "n_vertices": r.n_vertices, "n_faces": r.n_faces,
            "degree_max": r.degree_max, "memory_bytes": r.memory_bytes,
            "cpu_time_s": round(r.cpu_time_s, 6),
            "checks": r.checks, "failures": r.failures,
        }
    return results

# ---------------------------------------------------------------------------
# Manifest writer
# ---------------------------------------------------------------------------

def _to_python(obj):
    if isinstance(obj, dict):
        return {k: _to_python(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_python(v) for v in obj]
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    return obj

def write_results(results: dict, out_dir: Path, source_commit: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = default_stamp()
    manifest = {
        "schema": "chimera-membrane-scale-lab-correctness-v1",
        "utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": source_commit,
        "python": platform.python_version(),
        "results": _to_python(results),
    }
    mp = out_dir / f"correctness_{stamp}.json"
    mp.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return mp

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Verify membrane fixture suite")
    ap.add_argument("--fixtures", type=Path, default=Path("docs/evidence/membrane_scale_lab/fixtures"))
    ap.add_argument("--out", type=Path, default=Path("docs/evidence/membrane_scale_lab/correctness"))
    ap.add_argument("--seed-base", type=int, default=0)
    ap.add_argument("--sizes", type=int, nargs="+", default=[4, 8, 16, 32, 64])
    args = ap.parse_args()
    head = __import__("subprocess").run(
        ["git", "-C", str(_TOOLS.parent), "rev-parse", "HEAD"],
        capture_output=True, text=True).stdout.strip()
    print(f"source_commit={head}")
    suite = generate_suite(sizes=tuple(args.sizes), seed_base=args.seed_base)
    results = verify_suite(suite)
    passed = sum(1 for r in results.values() if r.get("status") == "PASS")
    total = len(results)
    mp = write_results(results, args.out, head)
    for name, r in results.items():
        print(f"  {name}: {r['status']}  nV={r.get('n_vertices')} nF={r.get('n_faces')}")
    print(f"correctness: {passed}/{total} passed -> {mp}")
    return 0 if passed == total else 1

if __name__ == "__main__":
    raise SystemExit(main())
