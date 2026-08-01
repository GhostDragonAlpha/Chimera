"""harvest_material.py -- take the APPEARANCE out of a generated take, and leave the shape behind.

THE REALISATION THIS FILE EXISTS FOR, and it makes the geometry failure irrelevant.

visual_hull.py measured the generated astronaut against the membrane's own geometry and it did not
survive: 0.45 hull IoU against a control's 0.10, and a generated body 25% less voluminous than the
derived one. Read one way that kills the pipeline.

Read the other way it does not matter at all, because A MATERIAL GENOME CONTAINS NO POSITIONS.
Open story/data/material_genomes.json and every feature is a DISTRIBUTION -- log_size, aniso, R, G,
B, opacity, greenness, each carrying a mean, a std, a p10 and a p90. Not one of them says where
anything is. So:

    WE NEVER NEEDED THE GENERATOR TO PRESERVE GEOMETRY.
    WE HAVE THE GEOMETRY. The membranes derive it -- that is the whole project.
    What we cannot derive is what a surface LOOKS like, and that is the one thing it can give us.

A slimmer astronaut still wears the same fabric. The visor is still the same glass. The weathering
is still the same weathering. Harvest the distributions, apply them to OUR body, and the generator's
opinion about proportions is discarded along with everything else it was never asked for.

WHAT THIS EXTRACTS, and what it honestly cannot. From video frames it can read colour and local
texture scale -- R, G, B, greenness, and a gradient-based proxy for how fine the surface detail is.
It CANNOT read splat size, anisotropy or opacity: those live in a 3D fit, which needs the GPU and
the Construction/ pipeline. So this recovers the colour half of a genome and says so, rather than
inventing the rest.

THE CLAY IS THE CONTROL, and it is the honest one. The same extraction run on the clay we SENT must
come back as a single grey element with near-zero saturation -- because that is what clay is. If
the generated take does not separate into more elements than the clay did, nothing was gained.

RUN:  python tools/harvest_material.py clay_exports/capture_aHuman --elements 4
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))


def frames_of(path, n=None):
    import cv2
    cap = cv2.VideoCapture(str(path))
    out = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        out.append(f[:, :, ::-1])
    cap.release()
    if n and len(out) > n:
        out = [out[int(i * (len(out) - 1) / (n - 1))] for i in range(n)]
    return out


def sample(frames, black_bg, tol=0.22, per_frame=4000, seed=3):
    """Pixels of the SUBJECT ONLY, with a local texture scale for each.

    The mask matters more than anything else here: a genome contaminated by background is a genome
    that will paint the sky onto a suit. Black-void takes threshold on luminance and keep the
    largest component; the clay control sits on known 0.5 grey and thresholds on distance from it."""
    import numpy as np
    import cv2

    rng = np.random.default_rng(seed)
    feats = []
    for img in frames:
        a = np.asarray(img, np.float32) / 255.0
        if black_bg:
            m = (a.max(axis=2) > tol).astype(np.uint8)
            n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
            if n > 1:
                m = (lab == (1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])))).astype(np.uint8)
            m = m.astype(bool)
        else:
            m = np.abs(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0 - 0.5) > 0.02
        # LOCAL TEXTURE SCALE: how much the surface varies within a few pixels. It is a PROXY for
        # the genome's log_size -- fine detail means small elements -- and it is named a proxy
        # because the real thing is a splat radius from a 3D fit.
        g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
        detail = np.abs(g - cv2.GaussianBlur(g, (0, 0), 2.0))
        ys, xs = np.nonzero(m)
        if not len(ys):
            continue
        k = rng.choice(len(ys), size=min(per_frame, len(ys)), replace=False)
        ys, xs = ys[k], xs[k]
        rgb = a[ys, xs]
        lum = rgb.mean(axis=1, keepdims=True)
        sat = rgb.max(axis=1) - rgb.min(axis=1)
        green = rgb[:, 1] - 0.5 * (rgb[:, 0] + rgb[:, 2])
        feats.append(np.column_stack([rgb, lum[:, 0], sat, green, detail[ys, xs]]))
    return np.concatenate(feats) if feats else np.zeros((0, 7), np.float32)


def stats(v):
    import numpy as np
    return {"mean": float(np.mean(v)), "std": float(np.std(v)),
            "p10": float(np.percentile(v, 10)), "p90": float(np.percentile(v, 90))}


def harvest(F, k, seed=0):
    """Cluster the pixels into ELEMENTS and describe each as distributions -- the same shape of
    record Construction/material_elements.py produces, so the two can share a codebook."""
    import numpy as np
    import cv2
    if len(F) < k * 10:
        return []
    # CLUSTER ON CHROMATICITY, NOT ON RGB. Raw RGB is dominated by how brightly a point is lit, so
    # clustering on it splits an object into BRIGHTNESS BANDS and calls them materials -- which is
    # what the first run of this file did, finding four shades of grey in clay and four shades of
    # grey in a suit and concluding nothing had been gained. That is the same error as the shading
    # metric in clay_check and the border mask in seedance_probe: measuring the light instead of
    # the thing. Divide by luminance and what is left is the surface's OWN colour, which is what a
    # material genome is made of. Texture scale joins it because fabric and glass differ in how
    # fine they are even when they are the same hue.
    lum = np.maximum(F[:, 3:4], 1e-3)
    chroma = F[:, 0:3] / lum
    data = np.column_stack([chroma * 2.0, F[:, 6] * 8.0]).astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 0.2)
    _, lab, _ = cv2.kmeans(data, k, None, crit, 6, cv2.KMEANS_PP_CENTERS)
    lab = lab.ravel()
    out = []
    for i in range(k):
        sel = F[lab == i]
        if not len(sel):
            continue
        out.append({
            "element": i,
            "fraction": float(len(sel)) / len(F),
            "n_px": int(len(sel)),
            "features": {"R": stats(sel[:, 0]), "G": stats(sel[:, 1]), "B": stats(sel[:, 2]),
                         "luminance": stats(sel[:, 3]), "saturation": stats(sel[:, 4]),
                         "greenness": stats(sel[:, 5]), "detail_scale": stats(sel[:, 6])},
        })
    return sorted(out, key=lambda e: -e["fraction"])


def show(name, els):
    print(f"\n{name}")
    print(f"   {'elem':>4} {'frac':>7} {'R':>6} {'G':>6} {'B':>6} {'sat':>6} {'detail':>7}")
    for e in els:
        f = e["features"]
        print(f"   {e['element']:>4} {e['fraction']:>7.3f} {f['R']['mean']:>6.3f} "
              f"{f['G']['mean']:>6.3f} {f['B']['mean']:>6.3f} {f['saturation']['mean']:>6.3f} "
              f"{f['detail_scale']['mean']:>7.4f}")


def main():
    import numpy as np
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("take_dir")
    ap.add_argument("--elements", type=int, default=4)
    ap.add_argument("--frames", type=int, default=12)
    a = ap.parse_args()
    take = Path(a.take_dir)

    gen = harvest(sample(frames_of(take / "generated.mp4", a.frames), True), a.elements)
    cla = harvest(sample(frames_of(take / "clay.mp4", a.frames), False), a.elements)

    show("THE CLAY WE SENT -- the control", cla)
    show("THE TAKE THAT CAME BACK", gen)

    def spread(els):
        if not els:
            return 0.0
        return float(np.std([e["features"]["saturation"]["mean"] for e in els]))
    cs = max(e["features"]["saturation"]["mean"] for e in cla) if cla else 0.0
    gs = max(e["features"]["saturation"]["mean"] for e in gen) if gen else 0.0
    print()
    print(f"peak element saturation   clay {cs:.4f}   generated {gs:.4f}")
    print(f"spread of saturation across elements   clay {spread(cla):.4f}   "
          f"generated {spread(gen):.4f}")
    print()
    # the clay is ONE material by construction, so the honest test is whether the take separates
    # into elements the clay cannot: more chromatic spread AND more variety of surface detail.
    if gs > cs * 1.8 and spread(gen) > spread(cla) * 1.5:
        print("MATERIAL WAS GAINED. The clay is one grey with nothing to separate; the take "
              "carries distinct elements with different colour and different surface detail. "
              "None of it depends on the geometry being right, because none of it is a position.")
    else:
        print("NOTHING WAS GAINED -- the take is no more materially varied than the clay.")

    (take / "material.json").write_text(json.dumps(
        {"source": "generated take, colour half of a genome; size/aniso/opacity need the 3D fit",
         "elements": gen, "clay_control": cla}, indent=1), encoding="utf8")
    print(f"\nwrote {take/'material.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
