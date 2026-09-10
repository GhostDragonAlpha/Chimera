"""make_fixtures.py -- freeze CPU-reference fixtures for the GPU handoff.

Writes a deterministic, immutable fixture set under docs/evidence/elastic_foundation/fixtures/:
    v1/<run>/<stem>.npz        float32/uint32 arrays (rest+current states, material, sheet info)
    v1/manifest.json           SHA-256 of every array payload + spec of shapes/dtypes
    v1/README.md               what each fixture is and the acceptance workflow

Fixtures are the FROZEN reference inputs for GPU stage A (per-face corner forces + energy) and
stage B (CSR gather), described in GPU_HANDOFF.md. verify_fixtures.py recomputes the CPU-law
reference answers from these exact byte streams (float64, then truncated to float32) and checks
the manifest hashes hold. Regeneration is allowed only with a higher version (append-only: an
older fixture set is never overwritten).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from . import geometry as G
from . import law as L
from . import materials as M
from . import run_falsify as RF

ROOT = Path(__file__).resolve().parent.parent.parent
FIX_ROOT = ROOT / "docs" / "evidence" / "elastic_foundation" / "fixtures"


def sha256_bytes(b) -> str:
    return hashlib.sha256(b).digest().hex()


def npz_sha(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_fixture(out_dir: Path, name: str, arrays: dict) -> Path:
    path = out_dir / f"{name}.npz"
    np.savez_compressed(path, **{k: np.asarray(v) for k, v in arrays.items()})
    return path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="freeze CPU-reference fixtures (append-only)")
    ap.add_argument("--run", default="", help="optional run label")
    args = ap.parse_args(argv)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    version = "v1"
    run_dir = FIX_ROOT / version / (f"run_{stamp}" + (f"_{args.run}" if args.run else ""))
    run_dir.mkdir(parents=True, exist_ok=False)

    material = M.synthetic(E=1.0, nu=0.3, h=1.0)
    fixtures = {}

    # --- fixture F-trisingle: one non-aligned triangle, single current pose (STRETCH @ TRANSLATE)
    name = "trisingle_stretch"
    pos_r = np.array([[0.10, 0.20, 0.00],
                      [1.00, 0.05, 0.00],
                      [0.15, 0.90, 0.00]], dtype=np.float64)
    faces = np.array([[0, 1, 2]], dtype=np.int64)
    y = G.apply_affine(pos_r, np.diag([1.2, 0.93, 1.0]), t=(0.27, -0.13, 0.05))
    pos_r_f32 = pos_r.astype(np.float32)   # the byte-stream inputs the GPU will read
    y_f32 = y.astype(np.float32)
    geom = G.build_rest_geometry(pos_r_f32, faces, build_info={"units": "m", "kind": "fixture"})
    ev = L.evaluate_elastic(geom, material, y_f32.astype(np.float64))
    fixtures[name] = {
        "rest_pos": pos_r_f32,
        "cur_pos": y_f32,
        "faces_int32": faces.astype(np.int32),
        "E": np.float32(material.E), "nu": np.float32(material.nu), "h": np.float32(material.h),
        "lam_bar": np.float32(material.lambda_bar), "mu_bar": np.float32(material.mu_bar),
        "E_f64": material.E, "nu_f64": material.nu, "h_f64": material.h,
        "rest_t1": geom.frame_t1.astype(np.float32), "rest_t2": geom.frame_t2.astype(np.float32),
        "rest_n": geom.frame_n.astype(np.float32),
        "rest_B_f32": geom.B.astype(np.float32),
        "rest_areas0_f32": geom.areas0.astype(np.float32),
        "exp_energy_f64": ev.energy,
        "exp_corner_f64": ev.corner_forces,
        "exp_vertex_f64": ev.vertex_forces,
        "exp_source": "from_f32_inputs",
    }

    # --- fixture F-patch8x4: the demo-size sheet at the pinned-shear pose (stage A + B)
    name = "patch_8x4_shear"
    W, H, NX, NY = 2.0, 1.0, 8, 4
    pos_r, faces = G.unit_make_grid(W, H, NX, NY)
    y = np.array(pos_r, dtype=np.float64)
    y[np.abs(y[:, 0] - W) < 1e-12, 1] = pos_r[np.abs(pos_r[:, 0] - W) < 1e-12, 1] + 0.25
    pos_r_f32 = pos_r.astype(np.float32)
    y_f32 = y.astype(np.float32)
    geom = G.build_rest_geometry(pos_r_f32, faces, build_info={"units": "m", "kind": "fixture"})
    ev = L.evaluate_elastic(geom, material, y_f32.astype(np.float64))
    fixtures[name] = {
        "rest_pos": pos_r_f32,
        "cur_pos": y_f32,
        "faces_int32": faces.astype(np.int32),
        "E": np.float32(material.E), "nu": np.float32(material.nu), "h": np.float32(material.h),
        "lam_bar": np.float32(material.lambda_bar), "mu_bar": np.float32(material.mu_bar),
        "E_f64": material.E, "nu_f64": material.nu, "h_f64": material.h,
        "rest_t1": np.broadcast_to(geom.frame_t1, (geom.n_faces, 3)).astype(np.float32),
        "rest_t2": np.broadcast_to(geom.frame_t2, (geom.n_faces, 3)).astype(np.float32),
        "rest_n": geom.n.astype(np.float32),
        "rest_B_f32": geom.B.astype(np.float32),
        "rest_areas0_f32": geom.areas0.astype(np.float32),
        "csr_offsets_u32": geom.csr_offsets.astype(np.uint32),
        "csr_corners_u32": geom.csr_corners.astype(np.uint32),
        "exp_energy_f64": ev.energy,
        "exp_corner_f64": ev.corner_forces,
        "exp_vertex_f64": ev.vertex_forces,
        "exp_source": "from_f32_inputs",
    }

    paths = []
    manifest = {"version": version, "generated_utc": stamp,
                "law": "isotropic STVK membrane, energy per rest area (DERIVATION.md)",
                "material": {"E": 1.0, "nu": 0.3, "h": 1.0, "synthetic": True},
                "fixtures": {}, "env": {"python": sys.version.split()[0],
                                        "numpy": np.version.version},
                "git_e_pythonchimera": RF.git_facts(ROOT)}
    for fname, arrays in fixtures.items():
        path = write_fixture(run_dir, fname, arrays)
        paths.append(path)
        manifest["fixtures"][fname] = {
            "file": path.name, "sha256": npz_sha(path),
            "arrays": {k: {"shape": list(np.asarray(v).shape),
                           "dtype": str(np.asarray(v).dtype)} for k, v in arrays.items()}}
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf8")
    (run_dir / "README.md").write_text(
        "CPU-reference fixtures for GPU stage A/B acceptance. verify_fixtures.py recomputes\n"
        "the float64 reference answers and checks the manifest hashes; the float32 arrays here\n"
        "are the exact inputs the GPUHANDOFF shader reads (see GPU_HANDOFF.md).\n",
        encoding="utf8")
    for p in paths:
        print(p)
    print(f"manifest: {run_dir / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())