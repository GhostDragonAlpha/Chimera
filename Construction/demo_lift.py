"""Demo: run a flat 2D picture through the construction algorithm into 3D.

  - author a tree, FLATTEN it to a 2D picture (Construction/lift.flatten)
  - 3D backend: orbit stills that PROVE the lift produces real volume
      * amount=0 seen obliquely -> a flat card (nearly edge-on it vanishes)
      * amount=1 from three yaw angles -> a volume (silhouette changes with angle)
  - HTML backend: the orbitable viewer with the FLAT<->VOLUME depth dial

Run:  python -m Construction.demo_lift
"""
from __future__ import annotations
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Construction import tree as T
from Construction import lift as L
from Construction import viewer3d as V

SEED, TH, TR, MAXD = 42, 320, 14, 4
CALM = {"flutter": 0.0, "sky": 0.0}   # no wind for the construction demo


def render_stills(flat, out_dir):
    from Construction import backend_3d as B3
    try:
        from PIL import Image
    except Exception as e:
        print("PIL unavailable, skipping stills:", repr(e))
        return []
    base = -math.pi / 2
    # The proof is the EDGE-ON pair: looking along X (az = base + 90 deg), the flat
    # 2D card collapses to a thin strip, but the lifted volume stays a full tree —
    # the third dimension really was filled in.
    shots = [
        ("flat_face", 0.0, base,               0.14),   # 2D picture, full face
        ("flat_edge", 0.0, base + math.pi / 2, 0.14),   # SAME picture edge-on -> a strip
        ("vol_face",  1.0, base,               0.14),   # lifted, front
        ("vol_edge",  1.0, base + math.pi / 2, 0.14),   # lifted, edge-on -> still full
    ]
    saved = []
    for name, amt, az, el in shots:
        lifted = L.lift(flat, amt)
        img = B3.render([(lifted, (0.0, 0.0, 0.0))], CALM, orbit_az=az, elev=el)
        path = os.path.join(out_dir, f"lift_{name}.png")
        Image.fromarray(img).save(path)
        saved.append(path)
        print(f"  {name:12s} amount={amt:.1f} yaw={math.degrees(az - base):5.0f}deg  "
              f"max|Y|={L.y_spread(lifted):6.1f}  -> {os.path.basename(path)}")
    return saved


def main():
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "renders")
    os.makedirs(out_dir, exist_ok=True)

    sk = T.build_skeleton(seed=SEED, trunk_height=TH, trunk_radius=TR, max_depth=MAXD)
    flat = L.flatten(sk)
    print("authored a tree, flattened to a 2D picture (max|Y| of flat =",
          round(L.y_spread(L.lift(flat, 0.0)), 3), ")")

    print("3D backend (ParticleEngine orbit stills):")
    render_stills(flat, out_dir)

    print("HTML backend (orbitable 3D viewer + depth dial):")
    pl = V.payload([(flat, (0.0, 0.0, 0.0))])
    page = V.write_page(os.path.join(out_dir, "viewer3d.html"), pl)
    frag = os.path.join(out_dir, "viewer3d.fragment.html")
    with open(frag, "w", encoding="utf-8") as fh:
        fh.write(V.build_fragment(pl))
    print(f"  -> {os.path.basename(page)} (+ .fragment.html)")
    print("done ->", out_dir)


if __name__ == "__main__":
    main()
