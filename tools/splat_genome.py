"""splat_genome.py -- the half of a material genome that only a GPU fit can read.

WHAT WAS MISSING. harvest_material.py reads a generated take's COLOUR: R, G, B, greenness, and a
gradient proxy for how fine the surface detail is. It cannot read the three features that make a
splat a splat -- log_size, aniso and opacity -- because those are not properties of a pixel. They
are properties of a PRIMITIVE that was fitted to the pixels, and fitting requires a differentiable
renderer and a GPU.

Construction/gsplat_fit.py already is that renderer. It optimises N 2D Gaussians -- position,
anisotropic scale, rotation, colour, opacity -- against an image by Adam on the GPU, and its output
has the same field names story/data/material_genomes.json uses.

AND THE ANSWER IS NO, WHICH THIS FILE NOW EXISTS TO RECORD. Fitting the generated take and then
fitting THE CLAY WE SENT -- rendered by our own engine from geometry we derived, known to be one
flat grey -- returned the same shape statistics for both:

    feature      generated     clay control      differ by
    log_size       -0.0243        -0.0392          (both ~0 by construction)
    aniso           0.4472         0.4185            6.9%
    opacity         0.8022         0.8059            0.5%
    R,G,B      .667/.635/.629  .888/.887/.870     -0.22 to -0.25   <-- the ONLY real signal

THE REASON IS STRUCTURAL, NOT A BUG. gsplat_fit optimises a FIXED N. With N fixed and the subject's
pixel area fixed, mean splat area is area/N by conservation -- log_size was pinned before the first
Adam step, and aniso follows from the same uniformity. Real 3DGS scans escape this through ADAPTIVE
DENSITY CONTROL: splats with high positional gradient are split, low-opacity ones pruned, so fine
detail accumulates many small splats and flat surfaces keep few large ones. THAT is what makes the
size distribution a material property in the real codebook. Without densification, these numbers
describe the --splats flag.

DENSIFICATION WAS THEN BUILT, AND IT DID NOT RESCUE THEM (2026-08-01). gsplat_fit now grows the
population where the residual says the surface is unresolved. It is a real improvement -- error
down ~25%, and the reconstructions are visibly better -- but measured against the same clay control
the three features still do not separate:

    log_size sd  0.3804 vs 0.4113   7.5%  |  aniso  0.5001 vs 0.4694  6.5%
    opacity      0.7793 vs 0.8286   6.0%  |  bar for "material, not fitter": 15%

So the honest verdict stands, now with the obvious remedy tried and measured rather than assumed:

    log_size, aniso, opacity from a generated video: NOT RECOVERABLE.
    Per-splat distributions need a real multi-view 3DGS scan. Adaptive densification is
    necessary but not sufficient -- a single 2D fit has no photometric consistency across
    views to force a splat to be the size of the thing it represents.

WHAT DENSIFICATION DID DELIVER is a measurement that did not exist before: SPLAT DEMAND. Because
growth stops when a splat's residual falls under an absolute threshold, a resolved surface stops
asking and a complicated one keeps going -- so the final splat count per subject pixel is a
property of the surface. At matched starting density the take asks for 1.398x the primitives flat
clay does.

AND THE FIXED-N MEASURE IT SITS BESIDE: SURFACE COMPLEXITY. At a budget set PER SUBJECT PIXEL, the
take costs 1.71x the fitting error of flat clay, and that survives a bilateral denoise
(1.655 -> 1.565) which strips 2.3x more high-frequency energy from the take than from the clay. So
it is edge-preserved surface detail, not codec grain.

    THE TWO ARE NOT THE SAME NUMBER AND BOTH ARE KEPT. surface_complexity asks "how wrong are you
    at a fixed budget" (densify=False, deliberately). splat_demand asks "how much budget did you
    need". A surface can be expensive in one sense and cheap in the other.

MASK FIRST, OR HARVEST THE BACKDROP. The fit is run on the SUBJECT ONLY: splats that land on a
black void would come back as a large, dark, low-opacity element and enter the codebook as a
material. Capture mode's black floor makes that mask exact.

    python tools/splat_genome.py clay_exports/capture_aHuman --frames 3 --splats 12000
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "Construction"))


def subject_frames(video, n, tol=0.22, pad=12, black_bg=True, bg="auto", masks_png=None,
                   frame_size=None):
    """The subject, cropped out of each sampled frame, with everything else set to black.

    Cropping matters as much as masking: fitting a few thousand Gaussians to a frame that is 90%
    empty spends nearly all of them on nothing, and their scales then describe the void.

    THE BACKDROP IS MEASURED, NOT ASSUMED (bg="auto"). The first version knew two backdrops -- the
    black void capture mode renders, and the 0.5 grey our clay sits on -- and both were hardcoded.
    That is fine until a take arrives on neither, which is what every probe made before capture
    mode existed looks like: probe_aTerrain sits on a mid grey that is neither 0.5 nor black, and
    both hardcoded rules mask the entire frame as subject. `auto` takes the median colour of the
    frame's outer border and calls everything far from it subject.

    THIS IS THE SAME MECHANISM THAT FAILED ONCE, so it is bounded rather than trusted: a
    border-colour mask scored 0.13 on a take with a lit environment, because it grabbed the wall.
    It is safe here only because the backdrop is a flat uncluttered plate, and `masks_png` exists
    so that claim is looked at instead of asserted."""
    import cv2
    import numpy as np

    cap = cv2.VideoCapture(str(video))
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f[:, :, ::-1])
    cap.release()
    pick = [frames[int(i * (len(frames) - 1) / max(n - 1, 1))] for i in range(n)]
    # MATCH THE RESOLUTION, or "it needed more splats" is partly "it had more pixels". The clay we
    # send is rendered at our own size and the take comes back at whatever the generator produced:
    # for probe_aTerrain that is 480x480 against 640x640, so the generated frame carries 1.78x the
    # pixels for the same object. Splats-per-pixel normalisation handles subject AREA but not
    # sampling RATE -- a finer grid genuinely resolves detail a coarser one cannot -- so both sides
    # are brought to a common frame size before anything is measured.
    if frame_size:
        pick = [cv2.resize(f, (frame_size, frame_size), interpolation=cv2.INTER_AREA)
                for f in pick]
    out, shots = [], []
    for img in pick:
        a = np.asarray(img, np.float32) / 255.0
        if bg == "auto":
            b = 6
            border = np.concatenate([a[:b].reshape(-1, 3), a[-b:].reshape(-1, 3),
                                     a[:, :b].reshape(-1, 3), a[:, -b:].reshape(-1, 3)])
            bgc = np.median(border, axis=0)
            m = (np.abs(a - bgc[None, None, :]).max(axis=2) > 0.10).astype(np.uint8)
        elif black_bg:
            m = (a.max(axis=2) > tol).astype(np.uint8)
        else:
            m = (np.abs(a.mean(axis=2) - 0.5) > 0.02).astype(np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        # FILL THE INTERIOR, or the genome comes back too bright. A colour-distance mask punches
        # holes wherever the SUBJECT happens to match the backdrop -- on probe_aTerrain that is
        # every shadowed slope that lands within 0.10 of the grey plate, which is precisely the
        # darkest surface the material has. Dropping it is not a small hole in a picture, it is a
        # systematic bias in every colour statistic downstream. The subject is solid, so background
        # is only background where it CONNECTS TO THE FRAME BORDER; anything enclosed is interior.
        nb, blab = cv2.connectedComponents((1 - m).astype(np.uint8), 8)
        edge = set(np.unique(np.concatenate([blab[0], blab[-1], blab[:, 0], blab[:, -1]])))
        m = np.isin(blab, list(edge - {0}), invert=True).astype(np.uint8) if nb > 1 else m
        k, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
        if k > 1:
            m = (lab == (1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA])))).astype(np.uint8)
        ys, xs = np.nonzero(m)
        if len(ys) < 200:
            continue
        y0, y1 = max(0, ys.min() - pad), min(a.shape[0], ys.max() + pad)
        x0, x1 = max(0, xs.min() - pad), min(a.shape[1], xs.max() + pad)
        crop = a[y0:y1, x0:x1] * m[y0:y1, x0:x1, None]
        out.append((crop, m[y0:y1, x0:x1].astype(bool)))
        if masks_png:
            v = a.copy(); v[m == 0] *= 0.18            # dim what the mask rejected
            shots.append((np.concatenate([a, v], axis=1) * 255).astype(np.uint8))
    if masks_png and shots:
        from PIL import Image
        h = sum(x.shape[0] for x in shots); w = max(x.shape[1] for x in shots)
        can = np.zeros((h, w, 3), np.uint8); y = 0
        for x_ in shots:
            can[y:y+x_.shape[0], :x_.shape[1]] = x_; y += x_.shape[0]
        Image.fromarray(can).save(masks_png)
    return out


def stats(v):
    import numpy as np
    return {"mean": float(np.mean(v)), "std": float(np.std(v)),
            "p10": float(np.percentile(v, 10)), "p90": float(np.percentile(v, 90))}


def main():
    import numpy as np
    import torch
    from PIL import Image
    import gsplat_fit as G

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("take_dir")
    ap.add_argument("--frames", type=int, default=3)
    ap.add_argument("--splats", type=int, default=12000,
                    help="ignored when --density is set (the default), which is the fair way")
    ap.add_argument("--density", type=float, default=0.12,
                    help="STARTING splats per subject pixel. Set per-pixel rather than as a flat N "
                         "because the take and the clay are framed differently -- at a flat N the "
                         "clay got 1.62x the splats per pixel and any comparison measured the "
                         "framing. With densification on this is a starting point, not a budget.")
    ap.add_argument("--no-densify", action="store_true",
                    help="fixed-N fitting, the old behaviour, for comparison")
    ap.add_argument("--iters", type=int, default=600)
    ap.add_argument("--elements", type=int, default=5)
    ap.add_argument("--video", default="generated.mp4")
    ap.add_argument("--bg", default="auto", choices=("auto", "black", "grey"),
                    help="how to find the subject. auto measures the frame border's median colour "
                         "-- use it for any take not made in capture mode's black void.")
    ap.add_argument("--control", default="clay.mp4",
                    help="THE CONTROL, and the only reason this file can be believed. The clay was "
                         "rendered by OUR OWN splat engine, so fitting it the same way says what a "
                         "fit returns when the material is known to be one flat grey. If the "
                         "generated take's aniso and opacity match the clay's, those numbers are "
                         "the FITTER'S signature and not the material's.")
    a = ap.parse_args()
    take = Path(a.take_dir)

    import cv2 as _cv
    def _side(v):
        c = _cv.VideoCapture(str(take / v)); ok, f = c.read(); c.release()
        return min(f.shape[:2]) if ok else None
    sides = [x for x in (_side(a.video), _side(a.control)) if x]
    FRAME = min(sides) if len(sides) == 2 and len(set(sides)) > 1 else None
    if FRAME:
        print(f"resolutions differ {sorted(set(sides))} -> both resampled to {FRAME}x{FRAME}")

    free, total = (x / 2 ** 30 for x in torch.cuda.mem_get_info())
    print(f"GPU {torch.cuda.get_device_name(0)}   {free:.1f} of {total:.1f} GiB free")
    print(f"fitting {a.splats} splats x {a.frames} frames, {a.iters} iters each")

    def run(video, black_bg, tag):
      views = subject_frames(take / video, a.frames, black_bg=black_bg, bg=a.bg,
                             masks_png=take / f"mask_{tag}.png", frame_size=FRAME)
      allp = {"log_size": [], "aniso": [], "R": [], "G": [], "B": [], "opacity": [], "greenness": []}
      dens_hist = []
      for i, (crop, mask) in enumerate(views):
          H, W, _ = crop.shape
          tgt = torch.tensor(crop, device=G.DEV)
          print(f"\nview {i}: {W}x{H}")
          px = int(mask.sum())
          N0 = int(round(a.density * px)) if a.density else a.splats
          P, recon, _ = G.fit(tgt, N=N0, iters=a.iters, K=11,
                              densify=not a.no_densify, budget=6 * N0, verbose=False)
          dens_hist.append((px, N0, P["n_splats"]))
          print(f"  {px:,} subject px   {N0:,} -> {P['n_splats']:,} splats "
                f"({P['n_splats']/px:.3f}/px)"
                + ("   [BUDGET CAP BOUND]" if P.get("budget_bound") else ""))

          mu = P["mu"].cpu().numpy()
          sc = P["scale"].cpu().numpy()
          col = P["color"].cpu().numpy()
          opa = P["opacity"].cpu().numpy()

          # KEEP ONLY THE SPLATS THAT LANDED ON THE SUBJECT. A fit places Gaussians everywhere the
          # loss asks it to, including on the black we masked in -- and those would enter the
          # codebook as a very dark, very large material that does not exist.
          xi = np.clip(mu[:, 0].astype(int), 0, W - 1)
          yi = np.clip(mu[:, 1].astype(int), 0, H - 1)
          # OPACITY > 0.5, THE CODEBOOK'S OWN CUT. material_elements.py states the reason in one
          # line -- "haze is not a material" -- and a genome built with a looser cut is not comparable
          # to one built with this one.
          on = mask[yi, xi] & (opa > 0.5)
          sc, col, opa = sc[on], col[on], opa[on]
          if not len(sc):
              continue

          # LOG_SIZE IS RELATIVE TO THE SUBJECT, not to the image. The codebook's feature is
          # `log_size_rel` for exactly this reason: a splat's absolute pixel size means nothing
          # across takes at different framings, and the subject's own extent is the only scale a
          # boundary supplies for itself.
          # ── THE CODEBOOK'S DEFINITIONS, NOT MY OWN ─────────────────────────────────────────────
          # The first version of this file invented its own and the numbers came back OUTSIDE the
          # measured range: aniso 2.25 against real scans' 0.296-0.996. Not noise -- a different
          # formula wearing the same name, which is the misfold this project built folding.py to
          # catch, turning up in a place folding.py cannot see. Construction/material_elements.py
          # `features()` is the authority and every line below matches it.
          ss = np.sort(sc, axis=1)                       # per-splat axes, ascending
          # ANISO = 1 - smallest/largest, so 0 is a circle and 1 is a needle. Mine was max/min,
          # which is a different quantity on a different interval.
          allp["aniso"].append(1.0 - ss[:, 0] / (ss[:, -1] + 1e-9))
          # LOG_SIZE is RELATIVE to this capture's own median splat -- "1.0 = typical", the
          # `log_size_rel` the codebook is built on -- not to the image, which would make every
          # take's numbers depend on how it happened to be framed. A 2D fit has two axes where a
          # 3D scan has three, so the geometric mean stands in for the median axis and is said to.
          gm = np.sqrt(ss[:, 0] * ss[:, -1])
          allp["log_size"].append(np.log(np.maximum(gm / max(np.median(gm), 1e-9), 1e-9)))
          allp["R"].append(col[:, 0]); allp["G"].append(col[:, 1]); allp["B"].append(col[:, 2])
          allp["opacity"].append(opa)
          # GREENNESS = G - max(R,B), the codebook's form. Mine used the mean of R and B, which
          # reads a magenta surface as green.
          allp["greenness"].append(col[:, 1] - np.maximum(col[:, 0], col[:, 2]))
          Image.fromarray((recon.clamp(0, 1).cpu().numpy() * 255).astype(np.uint8)).save(
              take / f"splat_recon_{tag}_{i}.png")

      if not allp["R"]:
          return None
      out = {k: np.concatenate(v) for k, v in allp.items()}
      out["_density"] = float(np.mean([n / px for px, _, n in dens_hist])) if dens_hist else 0.0
      return out

    print("\n=== THE TAKE THAT CAME BACK " + "=" * 50)
    F = run(a.video, True, "gen")
    if F is None:
        print("no splats survived the mask")
        return 1
    C = None
    if (take / a.control).exists():
        print("\n=== THE CLAY WE SENT -- the control " + "=" * 42)
        C = run(a.control, False, "clay")

    n = len(F["R"])
    print(f"\n{n:,} splats on the subject")
    hdr = f"\n{'feature':<12} {'mean':>10} {'std':>10} {'p10':>10} {'p90':>10}"
    print(hdr + (f" | {'CLAY mean':>10} {'delta':>9}" if C else ""))
    genome, clay_g = {}, {}
    # SPLAT DEMAND -- how many primitives the surface asked for, per pixel, at a matched start.
    # This is the number densification exists to produce: growth stops when the residual under a
    # splat falls under an absolute threshold, so a resolved surface stops asking and a complicated
    # one keeps going. The clay is the zero point.
    if C is not None and C.get("_density"):
        dg, dc = F["_density"], C["_density"]
        genome["splat_demand"] = {"value": dg / max(dc, 1e-9), "generated_per_px": dg,
                                  "clay_per_px": dc, "unit": "x flat-clay splat density"}
        print(f"\nSPLAT DEMAND   generated {dg:.3f}/px   clay {dc:.3f}/px   "
              f"ratio {dg/max(dc,1e-9):.3f}" +
              ("   THE SURFACE ASKED FOR MORE PRIMITIVES THAN FLAT CLAY."
               if dg/max(dc,1e-9) > 1.1 else "   no more than flat clay."))

    for k in ("log_size", "aniso", "R", "G", "B", "opacity", "greenness"):
        st = stats(F[k])
        genome[k] = st
        row = (f"{k:<12} {st['mean']:>10.4f} {st['std']:>10.4f} "
               f"{st['p10']:>10.4f} {st['p90']:>10.4f}")
        if C:
            cst = stats(C[k])
            clay_g[k] = cst
            row += f" | {cst['mean']:>10.4f} {st['mean'] - cst['mean']:>+9.4f}"
        print(row)

    # THE CONTROL'S VERDICT, and it is the only part of this file that can be believed on its own.
    # Six measurements in this project have failed by reading the INSTRUMENT instead of the
    # subject -- a border mask that grabbed the wall, an edge mask that grabbed the shadow, a
    # chamfer score that matched a control as well as the real thing -- and every one was caught
    # by a control rather than by inspection. The clay was rendered by OUR OWN splat engine from
    # geometry we derived, so a fit of the clay is a fit of a KNOWN single flat grey. Whatever the
    # generated take shares with it is the fitter talking; only the difference is the material.
    if C:
        print()
        # log_size is compared by SPREAD, not by mean. Both sides subtract their own capture's
        # median, so the mean is near zero on both by construction and says nothing; the width of
        # the distribution is what a mix of fine and coarse grain actually looks like.
        for k, lbl, gv, cvv in (
                ("log_size", "log_size sd", genome["log_size"]["std"], clay_g["log_size"]["std"]),
                ("aniso", "aniso", genome["aniso"]["mean"], clay_g["aniso"]["mean"]),
                ("opacity", "opacity", genome["opacity"]["mean"], clay_g["opacity"]["mean"])):
            rel = abs(gv - cvv) / max(abs(cvv), 1e-9)
            print(f"   {lbl:<12} generated {gv:.4f}   clay {cvv:.4f}   differ by {rel * 100:5.1f}%"
                  f"   {'MATERIAL' if rel > 0.15 else 'still mostly the fitter'}")

    # ── WHAT A FIXED-N FIT CAN STILL MEASURE ──────────────────────────────────────────────────
    # The three shape features are dead (see the docstring), but the question underneath them is
    # not: HOW COMPLEX IS THIS SURFACE? At a fixed budget that has a direct answer -- how much
    # error survives. A flat grey fits almost perfectly with few splats; a woven, panelled,
    # weathered surface does not, at any budget.
    #
    # TWO CONFOUNDS, BOTH MEASURED RATHER THAN ASSUMED:
    #  1. FRAMING. The first run of this gave the take 34,453 subject px and the clay 21,231 at the
    #     same N -- so the clay had 1.62x the splats per pixel and was always going to win. It
    #     reported 2.39x. Setting the budget PER SUBJECT PIXEL cut that to 1.31x, meaning well over
    #     half the "structure" was how the two subjects happened to be framed.
    #  2. CODEC GRAIN. Noise is expensive to fit and means nothing. A bilateral filter removes
    #     grain and preserves edges; it stripped 2.3x more high-frequency energy from the take than
    #     from the clay, and the cost ratio still barely moved (1.655 -> 1.565). So what is left is
    #     edge-preserved detail, which is surface.
    if C is not None:
        print("\nSURFACE COMPLEXITY -- fitting cost at EQUAL splats per subject pixel")
        # DENSITIES WHERE THE COMPARISON MEANS ANYTHING. At 0.06 splats/px the measured ratio is
        # 0.958 -- BELOW one -- because at that budget neither surface is represented at all and
        # the error is dominated by the coarse blobs both are reduced to. A budget too small to
        # resolve a difference cannot report one, and averaging it in only dilutes the result
        # toward 1. Both points below are fine enough to resolve the subject.
        dens = [0.20, 0.60]
        gv = subject_frames(take / a.video, 1, black_bg=True, bg=a.bg, frame_size=FRAME)[0]
        cv_ = subject_frames(take / a.control, 1, black_bg=False, bg=a.bg, frame_size=FRAME)[0]
        cost = {}
        for tag, (crop, mask) in (("generated", gv), ("clay", cv_)):
            px = int(mask.sum())
            tgt = torch.tensor(np.ascontiguousarray(crop), device=G.DEV)
            errs = []
            for d in dens:
                torch.manual_seed(0)
                # densify=False ON PURPOSE. This measure is defined as fitting cost at EQUAL
                # splats per pixel; letting the population grow lets each side buy its way out of
                # its own error and there is no longer a fixed budget to compare at.
                _, recon, _ = G.fit(tgt, N=max(64, int(round(d * px))), iters=400, K=11,
                                    densify=False, verbose=False)
                errs.append(float(np.abs((recon - tgt).cpu().numpy())[mask].mean()))
            cost[tag] = (px, errs)
            print(f"   {tag:<10} {px:>7,} px   " +
                  "   ".join(f"{d:.2f}/px -> err {e:.5f}" for d, e in zip(dens, errs)))
        cx = float(np.mean([g / max(c, 1e-9) for g, c
                            in zip(cost["generated"][1], cost["clay"][1])]))
        genome["surface_complexity"] = {"value": cx, "unit": "x flat-clay fitting cost",
                                        "densities": dens}
        print(f"\n   surface_complexity {cx:.3f}x the flat clay   " +
              ("REAL SURFACE DETAIL WAS RECOVERED." if cx > 1.15 else
               "no more detail than flat clay -- nothing was gained."))

    out = take / "splat_genome.json"
    out.write_text(json.dumps(
        {"n_splats": n, "views": a.frames,
         "RECOVERABLE": ["R", "G", "B", "greenness", "surface_complexity"],
         "NOT_RECOVERABLE": {
             "features": ["log_size", "aniso", "opacity"],
             "reason": "fixed-N 2D fitting pins them; they matched the clay control to 7%. "
                       "They need a real 3DGS scan or adaptive densification."},
         "features": genome, "clay_control": clay_g}, indent=1), encoding="utf8")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
