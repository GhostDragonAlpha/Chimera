"""splat_density.py -- HOW MANY SPLATS DOES EACH OBJECT SPEND, AND HOW MANY DOES IT NEED?

MEASUREMENT ONLY. This instrument reads the scene and changes nothing in it. The blind read named
"low detail"; "low detail" is not a number and cannot be acted on. This turns it into four numbers
per object -- splats spent, splats per pixel, OVERDRAW, and HOLE FRACTION -- plus the cheapest
count that would make the object legible, DERIVED from the object's own finest feature rather than
chosen.

WHY THOSE FOUR. A blob and a sieve are opposite failures and both read as "low detail":

    OVERDRAW  = (sum of splat areas) / (pixels actually covered).  High overdraw means splats are
                stacked on top of each other: the object is paying for detail it cannot show, and
                the surplus is exactly what could be spent making it finer instead.
    HOLES     = fraction of the silhouette's interior that no splat covers. High holes means the
                object reads as sparse dots -- the stone's own history, "40 splats read as a ~15 px
                faint smudge".

An object can have BOTH at once, and usually does when its splats are too big: they pile up in the
middle and still miss the edges. That is why one number ("density") cannot diagnose this and four
are the minimum.

THE FOOTPRINT FACTOR IS MEASURED, NOT NOMINAL. `tools/splat_ruler.py` established that one ball
paints ~2.4-2.7x its nominal size s = SIZE * base_scale, because the renderer's kernel has skirts
the arithmetic does not. Deriving a density against the nominal size would be deriving against a
number the screen does not use, so this instrument renders one grain through the REAL pipeline and
measures the factor before it computes anything. If the pipeline is unavailable it REFUSES; a
nominal fallback would be an assumption wearing a hat.

THE JUDGMENT DISTANCE IS THE BLIND READ'S, NOT A NEW ONE (3.2 m -- `tools/stone_legibility.py`,
`live_viewer`'s own third-person formula). Measuring legibility at a distance nobody judges from
would answer a question nobody asked.

    python tools/splat_density.py                 # the table, at 3.2 m
    python tools/splat_density.py --dist 2.0      # any distance
    python tools/splat_density.py --terrain       # include the ground (slow: it carves)
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "ChimeraEngine"))
sys.path.insert(0, str(REPO / "story"))

W, H = 1920, 1080
FOCAL = (H / 2.0) / math.tan(math.radians(30.0))     # 935.3 px at vfov 60 -- the pipeline's own
JUDGE_M = 3.2                                        # the blind read's camera distance
BASE_SCALE = 0.5                                     # FullGPUPipeline's default


class NoPipeline(RuntimeError):
    """The footprint factor could not be measured. There is no nominal fallback on purpose."""


def measure_footprint_factor(base_scale=BASE_SCALE, size=0.02, dist=5.0) -> float:
    """Render ONE grain through the real pipeline and measure what it actually paints.

    Same rig as splat_ruler: one green ball, known SIZE, known distance, count the pixels.
    Returns diameter_px / (FOCAL * size * base_scale / dist) -- how many multiples of the
    nominal footprint the renderer really lays down.
    """
    try:
        from ParticleEngine.gpu_pipeline import FullGPUPipeline
        from ParticleEngine.camera import FirstPersonCamera
        from matter import blank, SOLID
    except Exception as e:                            # noqa: BLE001 -- the refusal is the point
        raise NoPipeline(f"cannot reach the render pipeline ({type(e).__name__}: {e}). "
                         f"REFUSING to substitute the nominal footprint: splat_ruler measured "
                         f"2.4-2.7x, so nominal would understate every density here by ~2.5x.")
    b = blank(1)
    b[0, 0], b[0, 1], b[0, 2] = 0.0, 0.0, 0.9
    b[0, 16:19] = (0.0, 1.0, 0.0)
    b[0, 19], b[0, 20], b[0, 11] = 0.95, size, SOLID
    b[0, 21:24] = 0.0
    pipe = FullGPUPipeline(base_scale=base_scale)
    cam = FirstPersonCamera((0.0, -dist, 0.9), yaw=np.pi / 2.0, pitch=0.0)
    pipe.upload(b)
    img = pipe.render_from_gpu(cam, cam.params(W, H))
    r, g, bl = img[:, :, 0].astype(int), img[:, :, 1].astype(int), img[:, :, 2].astype(int)
    ys, xs = np.nonzero((g > 120) & (r < 100) & (bl < 100))
    if len(xs) == 0:
        raise NoPipeline("the reference grain rendered to nothing -- the factor is unmeasurable")
    dia = max(xs.max() - xs.min() + 1, ys.max() - ys.min() + 1)
    return float(dia) / (FOCAL * size * base_scale / dist)


def rasterise(cx, cy, rad, pad=1.15, grid=900):
    """Cover / overdraw / holes for a set of projected discs, by actually filling them in.

    Not a formula: the discs are stamped onto a grid and counted. Overlap is what the formula
    cannot know, and overlap IS the diagnosis -- an object whose splats sit on top of each other
    is paying for resolution it cannot deliver.
    """
    if len(cx) == 0:
        return 0.0, 0.0, 0.0, 0.0
    x0, x1 = cx.min() - rad.max() * pad, cx.max() + rad.max() * pad
    y0, y1 = cy.min() - rad.max() * pad, cy.max() + rad.max() * pad
    span = max(x1 - x0, y1 - y0, 1e-9)
    px = span / grid                                   # metres... no: pixels per cell
    gx = np.clip(((cx - x0) / px).astype(int), 0, grid - 1)
    gy = np.clip(((cy - y0) / px).astype(int), 0, grid - 1)
    gr = np.maximum(rad / px, 0.5)
    hits = np.zeros((grid, grid), np.int32)
    rmax = int(math.ceil(gr.max()))
    yy, xx = np.mgrid[-rmax:rmax + 1, -rmax:rmax + 1]
    d2 = (xx * xx + yy * yy).astype(np.float32)
    for i in range(len(gx)):
        r2 = gr[i] * gr[i]
        m = d2 <= r2
        ys, xs = np.nonzero(m)
        ay, ax = gy[i] + ys - rmax, gx[i] + xs - rmax
        ok = (ay >= 0) & (ay < grid) & (ax >= 0) & (ax < grid)
        np.add.at(hits, (ay[ok], ax[ok]), 1)
    cell_px2 = px * px
    covered = int((hits > 0).sum())
    painted = int(hits.sum())
    # THE SILHOUETTE is the covered set closed over its own holes: fill any empty cell that has
    # covered cells on both sides in BOTH axes. Cheap, and it does not need scipy.
    occ = hits > 0
    fill = np.zeros_like(occ)
    for axis in (0, 1):
        a = occ if axis == 0 else occ.T
        cum_f = np.maximum.accumulate(a, axis=1)
        cum_b = np.maximum.accumulate(a[:, ::-1], axis=1)[:, ::-1]
        inside = cum_f & cum_b
        fill |= inside if axis == 0 else inside.T
    sil = int(fill.sum())
    holes = max(sil - covered, 0)
    return (covered * cell_px2, painted * cell_px2, sil * cell_px2,
            (holes / sil) if sil else 0.0)


def project(buf, dist, factor, base_scale=BASE_SCALE):
    """Object-space splats -> image-plane discs, viewed head-on from `dist`.

    HEAD-ON AND ORTHOGRAPHIC-IN-DEPTH ON PURPOSE: every splat is scaled by the SAME dist, so the
    numbers describe the object rather than one camera's parallax. A per-splat depth would fold
    the object's thickness into its density and make two runs incomparable.
    """
    c = buf[:, :3].astype(float)
    c = c - c.mean(axis=0)
    k = FOCAL / dist
    return c[:, 0] * k, c[:, 2] * k, buf[:, 20].astype(float) * base_scale * factor * 0.5 * k


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dist", type=float, default=JUDGE_M)
    ap.add_argument("--terrain", action="store_true", help="include the ground (slow: it carves)")
    a = ap.parse_args(argv)

    factor = measure_footprint_factor()
    print("=" * 108)
    print(f"  SPLAT DENSITY AT THE JUDGMENT DISTANCE -- measurement only, no scene is touched")
    print(f"  {W}x{H}, vfov 60 -> focal {FOCAL:.1f} px | base_scale {BASE_SCALE} | "
          f"judgment distance {a.dist:.1f} m")
    print(f"  FOOTPRINT FACTOR MEASURED through the real pipeline: one splat paints "
          f"{factor:.2f}x its nominal size (splat_ruler's 2.4-2.7x band)")
    print("=" * 108)

    import touchables as to
    import walker as wk

    # A REAL WALKER, NOT A STUB. The first version passed a hand-made object with x/y/z/yaw/clock
    # and it raised on `w.sun` -- an object's buffer is SHADED by the world's own sun, so the
    # thing being measured genuinely depends on the walker. Faking the walker would have meant
    # faking the light, and this project has already paid for a baked light once.
    w = wk.Walker()

    rows = []
    objs = to.spawn()
    # THE FINEST FEATURE EACH OBJECT MUST SHOW, taken from the object's OWN published geometry.
    # Nothing here is chosen: each is a number touchables.py already derives and states.
    feature = {
        "Stone": (2.0 * math.pi * (to._STONE_D / 2.0) / 7.0,
                  "facet chord: 7 facet planes around the sphere (the FACETS membrane)"),
        "Tuft":  (2.0 * to._TUFT_DISK_R * math.pi / max(to._TUFT_BLADES, 1),
                  f"inter-blade spacing: {to._TUFT_BLADES} blades round a "
                  f"{2*to._TUFT_DISK_R:.1f} m disk"),
        "Pile":  (to._CLOD, "the display clod -- the pile's own grain-splat size"),
    }
    targets = [(type(o).__name__, o) for o in objs]
    for name, o in targets:
        buf = o.buffer(w)
        n = len(buf)
        s_m = float(np.median(buf[:, 20])) * BASE_SCALE
        cx, cy, rad = project(buf, a.dist, factor)
        cov, painted, sil, holefrac = rasterise(cx, cy, rad)
        d_px = 2.0 * float(np.median(rad))
        feat_m, why = feature.get(name, (s_m, "no published feature -- splat size used"))
        feat_px = FOCAL * feat_m / a.dist
        # TWO BOUNDS, AND THE FIRST VERSION COLLAPSED THEM INTO ONE AND GOT NONSENSE ("the stone
        # needs 5 splats"). Sizing a splat AT the feature does not show the feature -- it replaces
        # it with one blob. The bounds are independent and both must hold:
        #
        #   A RESOLUTION (Nyquist): to read a feature you need two samples across it, so the
        #     splat diameter must be <= feature/2. If it is not, NO COUNT HELPS.
        #   B SOLIDITY (random coverage): n discs of area `ad` scattered over silhouette `A` leave
        #     an uncovered fraction exp(-n*ad/A). Inverting gives the count for a target hole
        #     fraction: n = (A/ad) * ln(1/h). The model is CHECKED below against the holes this
        #     scene actually has, rather than asserted.
        d_max = feat_px / 2.0
        a_max = math.pi / 4.0 * max(d_max, 1e-9) ** 2
        cov_eff = n * (math.pi / 4.0 * d_px ** 2) / max(sil, 1e-9)
        cov_from_holes = math.log(1.0 / max(holefrac, 1e-9)) if holefrac > 0 else float("inf")
        rows.append(dict(name=name, n=n, s_m=s_m, d_px=d_px, sil=sil, cov=cov,
                         over=painted / max(cov, 1e-9), hole=holefrac,
                         per_px=n / max(sil, 1e-9), feat_m=feat_m, feat_px=feat_px,
                         d_max=d_max, a_max=a_max, cov_eff=cov_eff,
                         cov_from_holes=cov_from_holes, why=why))

    if a.terrain:
        print("  [terrain] building the ground around the walker (this is the slow one)...")
        buf = np.asarray(wk.scene_around(w), dtype=np.float32)
        n = len(buf)
        s_m = float(np.median(buf[:, 20])) * BASE_SCALE
        # THE GROUND IS NOT AN OBJECT: it has no silhouette, so its density is per square metre of
        # SURFACE, converted to the screen at the judgment distance. Reporting it as if it had a
        # bounding box would be the same misfold as quoting a sky's diameter.
        ext = float(np.ptp(buf[:, 0])) * float(np.ptp(buf[:, 1]))
        per_m2 = n / max(ext, 1e-9)
        px_per_m2 = (FOCAL / a.dist) ** 2
        rows.append(dict(name="Terrain", n=n, s_m=s_m,
                         d_px=FOCAL * s_m * factor / a.dist, sil=float("nan"),
                         cov=float("nan"), over=float("nan"), hole=float("nan"),
                         per_px=per_m2 / px_per_m2, feat_m=float("nan"),
                         feat_px=float("nan"), d_max=float("nan"), a_max=float("nan"),
                         cov_eff=float("nan"), cov_from_holes=float("nan"),
                         why=f"ground: {per_m2:.1f} splats/m^2 over {ext:.0f} m^2"))

    print(f"\n  {'object':<9} {'splats':>7} {'size':>8} {'on-screen':>10} {'silhouette':>11} "
          f"{'splats':>9} {'OVERDRAW':>9} {'HOLES':>7}")
    print(f"  {'':<9} {'spent':>7} {'(m)':>8} {'dia (px)':>10} {'(px^2)':>11} "
          f"{'per px^2':>9} {'x':>9} {'%':>7}")
    print("  " + "-" * 104)
    for r in rows:
        sil = "        n/a" if r["sil"] != r["sil"] else f"{r['sil']:11.0f}"
        ov = "      n/a" if r["over"] != r["over"] else f"{r['over']:9.2f}"
        ho = "    n/a" if r["hole"] != r["hole"] else f"{100*r['hole']:7.1f}"
        print(f"  {r['name']:<9} {r['n']:>7d} {r['s_m']:>8.4f} {r['d_px']:>10.2f} {sil} "
              f"{r['per_px']:>9.4f} {ov} {ho}")

    # THE COVERAGE MODEL, CHECKED BEFORE IT IS USED. exp(-coverage) = hole fraction is the random
    # -placement result; these splats are NOT randomly placed (they sit on a surface, more evenly
    # than Poisson), so the model should read the holes as LARGER than they are. Printing both
    # tells the reader how much to trust the counts below instead of asking them to assume.
    print("\n  COVERAGE MODEL CHECK (before it is used to derive anything)")
    print("  Random placement predicts hole fraction = exp(-coverage). Real splats sit on a")
    print("  surface, so they cover more evenly and the model should OVERSTATE the holes.")
    print("  " + "-" * 104)
    for r in rows:
        if r["cov_eff"] != r["cov_eff"]:
            continue
        pred_h = math.exp(-r["cov_eff"])
        print(f"  {r['name']:<9} coverage {r['cov_eff']:5.2f} -> model predicts "
              f"{100*pred_h:5.1f}% holes, measured {100*r['hole']:5.1f}%  "
              f"({'model conservative, as expected' if pred_h >= r['hole'] else 'MODEL UNDER-READS -- treat the counts below as a floor'})")

    print("\n  THE CHEAPEST DENSITY THAT MAKES EACH OBJECT LEGIBLE -- two bounds, both binding")
    print("  A RESOLUTION (Nyquist): splat diameter <= feature/2. Violate it and NO count helps.")
    print("  B SOLIDITY: n = (silhouette / splat_area) * ln(1/h) for a target hole fraction h.")
    print("  h is THE HUMAN's dial (touchables.py calls legibility a render row, not physics);")
    print("  the formula is given so the operator can move it. h = 1% is shown as the example.")
    print("  " + "-" * 104)
    H_TARGET = 0.01
    for r in rows:
        if r["d_max"] != r["d_max"]:
            print(f"  {r['name']:<9} {r['why']}")
            continue
        n_need = r["sil"] / r["a_max"] * math.log(1.0 / H_TARGET)
        print(f"  {r['name']:<9} feature {r['feat_m']*1000:7.1f} mm = {r['feat_px']:6.2f} px "
              f"({r['why']})")
        print(f"  {'':<9}   A: needs splats <= {r['d_max']:6.2f} px; has {r['d_px']:6.2f} px "
              f"-> {'PASS' if r['d_px'] <= r['d_max'] else 'FAIL'}")
        print(f"  {'':<9}   B: at that size, {n_need:8.0f} splats for {100*H_TARGET:.0f}% holes; "
              f"spends {r['n']:d} at {100*r['hole']:.1f}% holes")
        if r["d_px"] > r["d_max"]:
            print(f"  {'':<9}   *** ITS SPLATS ARE {r['d_px']/r['d_max']:.2f}x THE NYQUIST LIMIT. "
                  f"No count fixes this: the feature cannot resolve until the splat is smaller "
                  f"than half the thing it must show. SHRINK FIRST, then count.")
        elif r["n"] > 1.3 * n_need:
            print(f"  {'':<9}   -> spends {r['n']/n_need:.1f}x what solidity needs at overdraw "
                  f"{r['over']:.1f}x. The surplus buys nothing; spending it on SMALLER splats "
                  f"buys resolution.")
    print("\n  Read the two together. OVERDRAW says how much of what an object spends lands on")
    print("  top of itself; bound A says whether its splat is even small enough to carry the")
    print("  detail asked of it. A blob and a sieve both read as 'low detail' and these separate")
    print("  them. This tool changes nothing -- the scene edits belong to whoever owns the scene.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except NoPipeline as e:
        print(f"REFUSED: {e}")
        sys.exit(2)
