"""Densify a .splat: raise opacity and grow splat footprints.

TripoSplat clouds render see-through because (a) many splats carry low alpha
and (b) splat footprints leave pinholes between neighbors. This applies the
two derived corrections:

  alpha' = clip(alpha * gain, floor, 1.0)   -- every real splat mostly opaque
  scale' = scale * grow                     -- footprints overlap, pinholes close

Usage: python tools/densify_splat.py in.splat out.splat [floor] [gain] [grow]
Defaults: floor=0.6 gain=1.4 grow=1.25

NOTE: cb.load_splat applies the viewer orientation, so the output renders
with orient=1 in viewer.html (like every cb.save_splat file).
"""
import sys

import numpy as np

sys.path.insert(0, r"E:\PythonChimera\ChimeraEngine")
import cpp_bridge as cb  # noqa: E402


def main():
    in_path, out_path = sys.argv[1], sys.argv[2]
    floor = float(sys.argv[3]) if len(sys.argv) > 3 else 0.6
    gain = float(sys.argv[4]) if len(sys.argv) > 4 else 1.4
    grow = float(sys.argv[5]) if len(sys.argv) > 5 else 1.25

    buf = cb.load_splat(in_path)
    a = buf[:, 6]
    buf[:, 6] = np.clip(a * gain, floor, 1.0)
    buf[:, 7:10] *= grow
    cb.save_splat(out_path, buf)

    n = len(buf)
    print(f"{n} splats: alpha [{a.min():.3f}..{a.max():.3f}] -> "
          f"[{buf[:, 6].min():.3f}..{buf[:, 6].max():.3f}], scale x{grow}")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
