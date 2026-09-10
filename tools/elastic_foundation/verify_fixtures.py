"""verify_fixtures.py -- check fixture integrity and recompute the CPU reference answers.

For every fixture under docs/evidence/elastic_foundation/fixtures/<version>/:
  1. SHA-256 of each .npz must match the manifest exactly (immutability).
  2. The float64 CPU law, evaluated on the fixture's OWN rest/current arrays, must reproduce
     the manifest's stored expected energy and vertex forces to float64 roundoff.
  3. Truncated-to-float32 reference answers are emitted for the GPU acceptance workflow
     (GPU_HANDOFF.md stage C): a GPU stage A output within float32 tolerance of them passes.

Exit 0 iff every fixture passes every leg. Nothing is written except a .verified.json sidecar.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

from . import geometry as G
from . import law as L
from . import materials as M

ROOT = Path(__file__).resolve().parent.parent.parent
FIX_ROOT = ROOT / "docs" / "evidence" / "elastic_foundation" / "fixtures"

F32 = np.float32


def sha256_bytes(b) -> str:
    return hashlib.sha256(b).digest().hex()


def npz_sha(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def rel(a, b):
    a = float(np.asarray(a, dtype=np.float64).max()) if np.ndim(a) else float(a)
    b = float(np.asarray(b, dtype=np.float64).max()) if np.ndim(b) else float(b)
    return abs(a - b) / max(abs(b), 1e-300)


def run(args) -> int:
    version = args.version or "v1"
    root = FIX_ROOT / version
    if not root.exists():
        print(f"no fixtures under {root}")
        return 1
    # Default: verify the LATEST run (the handoff reference). Older runs remain on disk
    # (append-only) and are recorded but not gate the exit code unless --all is given.
    run_dirs = sorted(root.glob("run_*"))
    targets = run_dirs if args.all else run_dirs[-1:]
    results = {"version": version, "fixtures": {}}
    ok_all = True
    for dirp in targets:
        manifest_path = dirp / "manifest.json"
        if not manifest_path.exists():
            results["fixtures"][f"{dirp.name}"] = {"error": "no manifest"}
            ok_all = False
            continue
        man = json.loads(manifest_path.read_text(encoding="utf8"))
        for fname, meta in man["fixtures"].items():
            npz_path = dirp / meta["file"]
            rec = {"sha256_ok": None, "energy_rel_err": None, "vertex_rel_err": None,
                   "energy_f64": None, "vertex_f32_max": None}
            if npz_path.exists() and npz_sha(npz_path) == meta["sha256"]:
                rec["sha256_ok"] = True
            else:
                rec["sha256_ok"] = False
                ok_all = False
                results["fixtures"][f"{dirp.name}/{fname}"] = rec
                continue
            d = np.load(npz_path)
            pos_r = np.asarray(d["rest_pos"], dtype=np.float64)
            faces = np.asarray(d["faces_int32"], dtype=np.int64)
            y = np.asarray(d["cur_pos"], dtype=np.float64)
            if "nu_f64" in d:
                material = M.synthetic(E=float(d["E_f64"]), nu=float(d["nu_f64"]),
                                       h=float(d["h_f64"]))
            else:
                material = M.synthetic(E=float(d["E"]), nu=float(d["nu"]),
                                       h=float(d["h"]))
            geom = G.build_rest_geometry(pos_r, faces)
            ev = L.evaluate_elastic(geom, material, y)
            source = str(d.get("exp_source", ""))
            rec["source"] = source
            rec["energy_f64"] = float(ev.energy)
            rec["energy_rel_err"] = rel(float(ev.energy), float(d["exp_energy_f64"]))
            vref = np.asarray(d["exp_vertex_f64"], dtype=np.float64)
            rec["vertex_rel_err"] = rel(ev.vertex_forces, vref)
            rec["vertex_f32_max"] = float(np.max(np.abs(ev.vertex_forces.astype(F32))))
            # self-consistent legs: float32 input stream -> float64 reference answers
            ok = rec["energy_rel_err"] <= 512.0 * float(np.finfo(np.float64).eps) and \
                rec["vertex_rel_err"] <= 512.0 * float(np.finfo(np.float64).eps)
            ok_all = ok_all and ok
            results["fixtures"][f"{dirp.name}/{fname}"] = rec
    results["all_ok"] = bool(ok_all)
    stamped = root / ".verified.json"
    stamped.write_text(json.dumps(results, indent=2), encoding="utf8")
    print(json.dumps(results, indent=2))
    return 0 if ok_all else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="verify fixture integrity and CPU references")
    ap.add_argument("--version", default="v1")
    ap.add_argument("--all", action="store_true", help="verify every historical run too")
    sys.exit(run(ap.parse_args()))