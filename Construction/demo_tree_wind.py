"""Walking-skeleton demo: a grove in the wind (DESIGN §8).

Wires ONE scene model and ONE wind axis, then drives BOTH backends from it:
  - 3D backend  -> ParticleEngine stills at dial t = 0.0, 0.5, 1.0
  - HTML backend -> an interactive CALM<->GALE dial page

Run:  python -m Construction.demo_tree_wind
"""
from __future__ import annotations
import os
import sys

# allow `python Construction/demo_tree_wind.py` as well as `-m`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Construction.scene import Scene, PlacedObject, Anchor, Axis, Dial
from Construction import tree as T
from Construction import backend_html as H


# ── the ONE axis: the difference between two moments is the dimension ────────
CALM = Anchor("CALM", {"lean": 0.00, "sway": 0.03, "flutter": 0.05, "gust_hz": 0.35, "sky": 0.00})
GALE = Anchor("GALE", {"lean": 0.60, "sway": 0.40, "flutter": 0.85, "gust_hz": 1.10, "sky": 0.60})
WIND = Axis("wind", CALM, GALE)

# ── the scene: a small grove, directly placed (map-lift identity case) ───────
GROVE = [
    dict(seed=7,   trunk_height=280, trunk_radius=12, origin=(-320.0, 0.0, 0.0)),
    dict(seed=42,  trunk_height=320, trunk_radius=14, origin=(  10.0, 0.0, 0.0)),
    dict(seed=123, trunk_height=300, trunk_radius=13, origin=( 330.0, 0.0, 0.0)),
]
POSE_TIME = 1.5   # a representative moment for the stills (gusts are mid-swing)


def build_scene():
    scene = Scene()
    scene.add_dial("wind", Dial(WIND, 0.0))
    skeletons = []
    for g in GROVE:
        scene.add(PlacedObject("tree", "physics_tree", g["seed"], g["origin"],
                               params={"trunk_height": g["trunk_height"],
                                       "trunk_radius": g["trunk_radius"]}))
        sk = T.build_skeleton(seed=g["seed"], trunk_height=g["trunk_height"],
                              trunk_radius=g["trunk_radius"], max_depth=4)
        skeletons.append((sk, g["origin"]))
    return scene, skeletons


def render_stills(skeletons, out_dir):
    from Construction import backend_3d as B3
    try:
        from PIL import Image
    except Exception as e:
        print("PIL unavailable, skipping stills:", repr(e))
        return []
    max_depth = max(T.max_depth_of(sk) for sk, _ in skeletons)
    saved = []
    for t in (0.0, 0.5, 1.0):
        wind = WIND.fill(t)
        posed = [(T.pose(sk, wind, POSE_TIME, max_depth), origin)
                 for sk, origin in skeletons]
        img = B3.render(posed, wind)
        path = os.path.join(out_dir, f"wind_t{int(t*100):03d}.png")
        Image.fromarray(img).save(path)
        saved.append(path)
        print(f"  t={t:.2f}  wind={{lean:{wind['lean']:.2f} sway:{wind['sway']:.2f} "
              f"flutter:{wind['flutter']:.2f} sky:{wind['sky']:.2f}}}  ->  {os.path.basename(path)}  {img.shape}")
    return saved


def write_html(skeletons, out_dir):
    max_depth = max(T.max_depth_of(sk) for sk, _ in skeletons)
    pl = H.payload(skeletons, CALM.params, GALE.params, max_depth)
    page = H.write_page(os.path.join(out_dir, "dev_tree_wind.html"), pl)
    frag = os.path.join(out_dir, "dev_tree_wind.fragment.html")
    with open(frag, "w", encoding="utf-8") as f:
        f.write(H.build_fragment(pl))
    print(f"  HTML dev backend -> {os.path.basename(page)} (+ .fragment.html)")
    return page, frag


def main():
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "renders")
    os.makedirs(out_dir, exist_ok=True)
    scene, skeletons = build_scene()
    print(f"scene: {len(scene.objects)} trees, dial 'wind' on axis "
          f"{WIND.lo.name}<->{WIND.hi.name}")
    print("3D backend (ParticleEngine stills):")
    render_stills(skeletons, out_dir)
    print("HTML backend:")
    write_html(skeletons, out_dir)
    print("done ->", out_dir)


if __name__ == "__main__":
    main()
