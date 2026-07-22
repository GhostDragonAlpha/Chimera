"""Compose the golden NOUN with the wind VERB — blow(construct(picture)).

  noun = lift(flatten(picture, golden_rule), 1.0)   # the construction that won on evidence
  blown = pose(noun, wind, t)                        # give it the verb
  put together like normal programming.

Renders ParticleEngine stills (photo evidence, oblique 3D view) at CALM / mid /
GALE, and writes the interactive orbit+wind viewer.

Run:  python -m Construction.demo_compose
"""
from __future__ import annotations
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Construction import tree as T
from Construction import lift as L
from Construction import viewer_nv as VNV

SEED, TH, TR, MD = 42, 320, 14, 4
CALM = {"lean": 0.00, "sway": 0.03, "flutter": 0.05, "gust_hz": 0.35, "sky": 0.00}
GALE = {"lean": 0.60, "sway": 0.40, "flutter": 0.85, "gust_hz": 1.10, "sky": 0.60}
POSE_TIME = 1.5


def wind_fill(t):
    return {k: CALM[k] * (1 - t) + GALE[k] * t for k in CALM}


def golden_noun():
    """construct(picture): flatten to a 2D picture, lift by the golden rule."""
    sk = T.build_skeleton(seed=SEED, trunk_height=TH, trunk_radius=TR, max_depth=MD)
    return L.lift(L.flatten(sk, L.golden_rule), 1.0)


def render_stills(noun, out_dir):
    from Construction import backend_3d as B3
    try:
        from PIL import Image
    except Exception as e:
        print("PIL unavailable, skipping stills:", repr(e))
        return
    md = T.max_depth_of(noun)
    az, el = -math.pi / 2 + 0.8, 0.18   # 3/4 oblique so both the 3D and the wind read
    for t in (0.0, 0.5, 1.0):
        w = wind_fill(t)
        blown = T.pose(noun, w, POSE_TIME, md)          # noun + verb
        img = B3.render([(blown, (0.0, 0.0, 0.0))], w, orbit_az=az, elev=el)
        path = os.path.join(out_dir, f"compose_t{int(t * 100):03d}.png")
        Image.fromarray(img).save(path)
        print(f"  wind t={t:.2f}  ->  {os.path.basename(path)}")


def main():
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "renders")
    os.makedirs(out_dir, exist_ok=True)
    noun = golden_noun()
    print(f"noun = golden construction (max|Y|={L.y_spread(noun):.0f}); verb = wind")
    print("3D backend (ParticleEngine stills, noun+verb):")
    render_stills(noun, out_dir)
    print("HTML backend (orbit + wind viewer):")
    pl = VNV.payload([(noun, (0.0, 0.0, 0.0))], CALM, GALE, T.max_depth_of(noun))
    page = VNV.write_page(os.path.join(out_dir, "compose.html"), pl)
    frag = os.path.join(out_dir, "compose.fragment.html")
    with open(frag, "w", encoding="utf-8") as fh:
        fh.write(VNV.build_fragment(pl))
    print(f"  -> {os.path.basename(page)} (+ .fragment.html)")
    print("done ->", out_dir)


if __name__ == "__main__":
    main()
