"""Densify a .splat: smart-clip the background shell, grow body footprints.

Measured 2026-08-20 (vd_native / vd_dense / vd_roundtrip A-B): a load/save
round-trip is render-identical, but a global alpha floor turns TripoSplat's
faint near-white background-residue shell into an opaque cocoon — the bear
vanishes from above (dark stack in front) and blows out from below (white
stack). So:

  1. NO global alpha edits. Native alpha is already >= 0.6 everywhere.
  2. SMART CLIP (the operator's density latch): a splat belongs to the bear if
     its k-th nearest neighbor is close (local density) — the shell and
     floaters are sparse. Delete d_k > median * clip_factor.
  3. Sharpen alpha on the SURVIVORS only (alpha' = alpha^gamma, gamma < 1).
     This is only safe AFTER the clip: the v1 bug was flooring alpha on the
     shell splats, which no longer exist here.
  4. Grow the survivors' footprints (grow) to close the pinholes that made the
     body read see-through.

Usage: python tools/densify_splat.py in.splat out.splat [grow] [k] [clip_factor] [gamma]
Defaults: grow=1.1 k=8 clip_factor=3.0 gamma=0.6

NOTE: cb.load_splat applies the viewer orientation, so the output renders
with orient=1 in viewer.html (like every cb.save_splat file).
"""
import sys

import numpy as np

sys.path.insert(0, r"E:\PythonChimera\ChimeraEngine")
import cpp_bridge as cb  # noqa: E402


def main():
    in_path, out_path = sys.argv[1], sys.argv[2]
    grow = float(sys.argv[3]) if len(sys.argv) > 3 else 1.1
    k = int(sys.argv[4]) if len(sys.argv) > 4 else 8
    clip_factor = float(sys.argv[5]) if len(sys.argv) > 5 else 3.0
    gamma = float(sys.argv[6]) if len(sys.argv) > 6 else 0.6

    from scipy.spatial import cKDTree

    buf = cb.load_splat(in_path)
    P = buf[:, 0:3]

    d, _ = cKDTree(P).query(P, k=k + 1)  # d[:, 0] is self
    dk = d[:, k]
    med = np.median(dk)
    keep = dk < med * clip_factor

    out = buf[keep].copy()
    out[:, 6] = np.power(out[:, 6], gamma)  # sharpen alpha, survivors only
    out[:, 7:10] *= grow
    cb.save_splat(out_path, out)

    print(f"{len(buf)} -> {len(out)} splats "
          f"(deleted {len(buf) - len(out)} sparse shell/floaters; "
          f"d{k} median {med:.4f}, clip at {med * clip_factor:.4f}); "
          f"alpha^{gamma}, scale x{grow}")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
