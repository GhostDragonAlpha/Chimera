"""splat_densify.py -- thicken a trained 3DGS shell: clone splats with in-ellipsoid jitter.

WHY (operator directive, 2026-08-20): the movie-pipeline bears are "the best quality of the
three but need more density in order not be see-through. THE FIBERS." Retraining with
heavier densification is the principled fix but costs a GPU window; this tool is the cheap
probe of the same hypothesis on the existing asset.

RULE 0:
  STATEMENT  — the see-through patches are a SAMPLING problem, not a missing-content
               problem: the trained shell's splats tile the surface too sparsely, so clones
               jittered inside each splat's own covariance ellipsoid fill the gaps without
               inventing geometry.
  PREDICTION — at 2x count the 6-angle renders show visibly fewer see-through patches and
               no new artifacts (no fuzz halo, no doubled silhouette).
  FALSIFIER  — the densified render shows the same holes (sampling wasn't the cause ->
               need retraining/capture), or new artifacts appear (jitter model wrong ->
               this tool reports that honestly).

CLONE MODEL: for each splat, K clones with position offset = R(q) @ (randn(3) * scales *
--jitter). Color, alpha, scale, rotation copied verbatim. Same draw order interleave is
harmless: the engine/viewer sorts by depth.

Usage:
  .venv-gs/Scripts/python.exe tools/splat_densify.py <in.splat|in.ply> --out <out.splat>
      [--factor 1] [--jitter 0.5] [--seed 0]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ChimeraEngine"))
sys.path.insert(0, str(ROOT / "ChimeraEngine" / "native"))

import cpp_bridge as cb  # noqa: E402
from ply_to_splat import load_3dgs_ply  # noqa: E402


def load_any(path: str) -> np.ndarray:
    if path.endswith(".splat"):
        return cb.load_splat(path)
    return load_3dgs_ply(path)


def densify(buf: np.ndarray, factor: int, jitter: float, seed: int) -> tuple[np.ndarray, dict]:
    rng = np.random.default_rng(seed)
    n = len(buf)
    pos, scales = buf[:, 0:3].astype(np.float64), buf[:, 7:10].astype(np.float64)
    R = cb._quat_to_matrix(buf[:, 10:14].astype(np.float64))  # (n,3,3), wxyz in
    clones = [buf]
    for _ in range(factor):
        local = rng.standard_normal((n, 3)) * scales * jitter          # (n,3) in splat frame
        offset = np.einsum("nij,nj->ni", R, local).astype(np.float32)  # to world frame
        c = buf.copy()
        c[:, 0:3] += offset
        clones.append(c)
    out = np.concatenate(clones, axis=0)
    report = {"in": n, "factor": factor, "jitter": jitter, "seed": seed, "out": int(len(out))}
    return out, report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("src")
    ap.add_argument("--out", required=True)
    ap.add_argument("--factor", type=int, default=1, help="clones per splat (1 = 2x count)")
    ap.add_argument("--jitter", type=float, default=0.5,
                    help="jitter in units of the splat's own per-axis scale")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    buf = load_any(a.src)
    out, report = densify(buf, a.factor, a.jitter, a.seed)
    print(json.dumps(report, indent=1))
    cb.save_splat(a.out, out)
    Path(a.out + ".densify.json").write_text(json.dumps(report, indent=1))
    print(f"saved {a.out}: {len(out)} splats ({len(out)//report['in']}x)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
