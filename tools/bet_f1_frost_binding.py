#!/usr/bin/env python
"""bet_f1_frost_binding.py -- THE FROST CANNOT DETACH (BET-F1 first leg, visual).

Port 22 (tri_gauss) proved the ALGEBRA: a filled triangle's uniform-measure covariance
is exactly Sigma_2 = (1/12) sum (v_i-m)(v_i-m)^T, so the derived 2D splat is the
triangle's OWN dispersion. This script proves the RENDER: drive cad_bear's lattice with
the triangle carrier CA (area + bending + curvature, the between-neighbor physics), and
per frame draw the SAME triangles TWO ways --

    leg H  hard triangles   (PIL polygon raster, painter's far->near)
    leg G  derived 2D Gaussians (position = centroid, rotation = eigen-frame z->normal
            with in-plane twist fixed by the major eigenvector, scale = sqrt(eigenvalues),
            free params = opacity 1 + flat lambert shade -- the 10-derived/4-free split)

-- and measure how well leg G tracks leg H under the motion. The identity is exact, so
any residual is RASTERIZATION (view + resolution) and must be STRAIN-INVARIANT: if the
splat lost its triangle, its centroid or y-ellipse would drift as strain grows.

RULE 0, stated before the run:
  STATEMENT   leg G and leg H are one row -- the derived 2D splat moves with the hard
              triangle by construction, at every strain the CA produces.
  PREDICTION  per frame, image-space centroid drift <= 1.5 px and covariance relative
              error <= 10% (rasterization cushion over the exact identity), and the
              per-frame residuals do not GROW with |A/A0-1| (Pearson <= +0.5 over the
              strained frames).
  FALSIFIER   any frame's centroid drift > 2.0 px, any frame's covariance rel err >
              10%, or residual Pearson vs max-strain > +0.5 -- the frost bound broke.

Usage:   python tools/bet_f1_frost_binding.py
Output:  PNG strips (hard | derived-splat | diff) per frame +
         models/cad_bear/frost_binding.json + verdict table on stdout.
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))
from LightEngine import constants as C  # noqa: E402
import ca_triangle as ct  # noqa: E402 -- build_lattice + area/bend/curv functions, importable (main-guarded)

# ---- FILTER (triangle carrier only: area + bending + curvature; the octree point-walk is a
# different substrate and not part of the frost claim) -----------------------------------------
TICKS = 40000          # integration length, multiple of the 4 capture ticks (approx 20ms sim time)
CAPTURE = (0, 4000, 15000, 40000)
DT = 5.0e-7           # cliff-safe substep (ca_stab.txt / ca_triangle.dt_int convention)
PERT_AMP = 0.03       # deterministic initial fold (seed 0): the CA restores it, strain varies
W, H = 480, 270       # render resolution (modest: 59k tris x 2 legs x 4 frames)
CENTROID_PREDICT = 1.5   # px, named before the run
COV_PREDICT = 0.10       # relative, named before the run
CENTROID_FALSIFY = 2.0   # px, named before the run
COV_FALSIFY = 0.10       # relative, named before the run
PEARSON_FALSIFY = 0.5    # residual vs strain may not trend up, named before the run
OUT_JSON = ROOT / "models" / "cad_bear" / "frost_binding.json"
OUT_PNG = ROOT / "ChimeraEngine" / "engine" / "scratch" / "proof_restore"

FOV_DEG = 45.0
LIGHT = np.array([0.35, -0.8, 0.5]); LIGHT /= np.linalg.norm(LIGHT)


# ---- camera + projection (the repo's own, imported -- no second copy) --------------------------
from lasso_label import camera, project, ellipses_2d, quat_to_R  # noqa: E402


def _R_to_quat(R: np.ndarray) -> np.ndarray:
    """(3,3) -> wxyz quaternion (Shepperd). Standard linear algebra, not a membrane fact."""
    t = np.trace(R)
    if t > 0:
        s = math.sqrt(t + 1.0) * 2.0
        return np.array([0.25 * s, (R[2, 1] - R[1, 2]) / s,
                         (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s])
    if R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = math.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2.0
        return np.array([(R[2, 1] - R[1, 2]) / s, 0.25 * s,
                         (R[0, 1] + R[1, 0]) / s, (R[0, 2] + R[2, 0]) / s])
    if R[1, 1] > R[2, 2]:
        s = math.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2.0
        return np.array([(R[0, 2] - R[2, 0]) / s, (R[0, 1] + R[1, 0]) / s,
                         0.25 * s, (R[1, 2] + R[2, 1]) / s])
    s = math.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2.0
    return np.array([(R[1, 0] - R[0, 1]) / s, (R[0, 2] + R[2, 0]) / s,
                     (R[1, 2] + R[2, 1]) / s, 0.25 * s])


def derived_splats(pos: np.ndarray, tris: np.ndarray, normals: np.ndarray):
    """THE FROST: per-triangle 2D Gaussian from geometry ONLY -- the 10 derived params.

    position = centroid; rotation = orthonormal frame z->normal, x = major eigenvector of
    Sigma_2 (in-plane twist FIXED, never free); scale = sqrt(eigenvalues) of Sigma_2 with a
    zero-thickness third axis (a 2D splat per the amendment). 4 free params: opacity (1) and
    RGB (flat lambert by the imported normal). NO binding code exists.
    """
    a, b, c = pos[tris[:, 0]], pos[tris[:, 1]], pos[tris[:, 2]]
    m = (a + b + c) / 3.0
    n = normals
    nrm = np.linalg.norm(n, axis=1, keepdims=True)
    n = n / np.where(nrm > 0, nrm, 1.0)
    buf = np.zeros((len(tris), 14))
    buf[:, 0:3] = m
    lam = np.clip(n @ LIGHT, 0.0, 1.0)
    shade = 0.55 + 0.45 * lam
    buf[:, 3:6] = (np.array([205, 168, 122]) / 255.0)[None, :] * shade[:, None]
    buf[:, 6] = 1.0
    ev = np.empty((len(tris), 3))
    evec = np.empty((len(tris), 3, 3))
    for i in range(len(tris)):
        S = sum(np.outer(v - m[i], v - m[i]) for v in (a[i], b[i], c[i])) / 12.0  # = Sigma_2
        w, V = np.linalg.eigh(S)
        o = np.argsort(w)[::-1]
        w, V = w[o], V[:, o]                     # w0 >= w1 >= w2(~0)
        # frame: x = major eigenvector (in-plane twist FIXED), z = face normal (positive x . E)
        x = V[:, 0]
        if float(np.dot(x, n[i])) < 0.0:
            x = -x
        y = np.cross(n[i], x)
        y /= np.linalg.norm(y) + 1e-30
        R = np.column_stack([x, y, n[i]])
        evec[i] = R
        ev[i] = np.array([max(w[0], 0.0), max(w[1], 0.0), 0.0])
    buf[:, 7:10] = np.sqrt(ev)
    for i in range(len(tris)):
        buf[i, 10:14] = _R_to_quat(evec[i])
    return buf


def leg_hard(pos: np.ndarray, tris: np.ndarray, normals: np.ndarray, cam, w, h):
    """Hard-triangle leg: painter's far->near flat-shaded polygon raster + z-buffer mask."""
    from PIL import Image as _I, ImageDraw as _D
    img = _I.new("RGB", (w, h), (12, 12, 20))
    dr = _D.Draw(img)
    shade = (0.55 + 0.45 * np.clip(normals @ LIGHT, 0.0, 1.0))
    verts = pos
    zcent = verts[tris].mean(axis=1)[:, 2]
    order = np.argsort(zcent)  # far first, near last -> nearest wins by overwrite
    mask = np.zeros((h, w), dtype=bool)
    for ti in order:
        p = verts[tris[ti]]
        u, v, z = project(p, cam, w, h)
        if np.any(z <= 0):
            continue
        if (np.ptp(u) < 0.5 and np.ptp(v) < 0.5):
            continue
        xy = [(float(u[j]), float(v[j])) for j in range(3)]
        if (min(u) >= w or max(u) < 0 or min(v) >= h or max(v) < 0):
            continue
        col = int(np.clip(shade[ti], 0, 1) * 255)
        dr.polygon(xy, fill=(col, int(col * 0.9), int(col * 0.72)))
    arr = np.asarray(img)
    return arr, np.any(arr != (12, 12, 20), axis=2)


def leg_gauss(buf: np.ndarray, cam, w, h):
    """Derived-Gaussian leg: the repo's true anisotropic-ellipse mini rasterizer (lasso_label
    ellipses_2d + qualify_corpus render_soft pattern), 3-sigma soft falloff, back-to-front."""
    u, v, z, sa, sb, th, ok = ellipses_2d(buf, cam, w, h, k=1.0)
    rgb = buf[ok, 3:6]
    alpha = np.clip(buf[ok, 6], 0, 1)
    acc = np.zeros((h, w, 3))
    acc_a = np.zeros((h, w))
    for i in np.argsort(-z):
        rad = int(math.ceil(3.0 * max(sa[i], sb[i]))) + 1
        x0, x1 = max(0, int(u[i]) - rad), min(w, int(u[i]) + rad + 1)
        y0, y1 = max(0, int(v[i]) - rad), min(h, int(v[i]) + rad + 1)
        if x1 <= x0 or y1 <= y0 or sa[i] < 1e-3 or sb[i] < 1e-3:
            continue
        ys, xs = np.mgrid[y0:y1, x0:x1]
        dx, dy = xs - u[i], ys - v[i]
        c, s = math.cos(th[i]), math.sin(th[i])
        da = dx * c + dy * s
        db = -dx * s + dy * c
        gw = alpha[i] * np.exp(-0.5 * ((da / sa[i]) ** 2 + (db / sb[i]) ** 2))
        a = acc_a[y0:y1, x0:x1]
        acc[y0:y1, x0:x1] = acc[y0:y1, x0:x1] + (1 - a)[..., None] * gw[..., None] * rgb[i]
        acc_a[y0:y1, x0:x1] = a + (1 - a) * gw
    bg = np.array([12, 12, 20]) / 255.0
    out = acc + (1 - acc_a)[..., None] * bg[None, None, :]
    return (np.clip(out, 0, 1) * 255).astype(np.uint8), acc_a > 0.5


def _moments2(mask: np.ndarray) -> tuple[np.ndarray, float, float]:
    """Image-space centroid + covariance of a boolean mask (pixels w=1 inside)."""
    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        return np.zeros(2), np.zeros((2, 2)), 0.0
    N = len(ys)
    m = np.array([xs.mean(), ys.mean()])
    d = np.stack([xs - m[0], ys - m[1]], axis=1)
    S = d.T @ d / N
    return m, S, N


def main() -> int:
    t0 = time.perf_counter()
    print("BET-F1 FROST-BINDING -- the frost cannot detach (visual leg)\n" + "=" * 88)
    print("RULE 0, pre-registered BEFORE the run:")
    print("  STATEMENT   leg G (derived 2D Gaussian) and leg H (hard triangle) are one row; the")
    print("              splat moves with the CA vertex by construction, at every strain.")
    print(f"  PREDICTION  centroid drift <= {CENTROID_PREDICT} px AND covariance rel err <= "
          f"{COV_PREDICT:.0%} per frame, residuals NOT growing with |A/A0-1| "
          f"(Pearson <= +{PEARSON_FALSIFY}).")
    print(f"  FALSIFIER   centroid drift > {CENTROID_FALSIFY} px, cov rel err > {COV_FALSIFY:.0%}, "
          f"or residual Pearson > +{PEARSON_FALSIFY} on ANY frame.")
    print("=" * 88, flush=True)

    # ---- lattice: the bit-exact import chain, deduped to walk space -----------------------------
    Vg, Tg, A0, S, e_med, n_orig, n_merge = ct.build_lattice()
    keep = A0 >= ct.NEAR_ZERO_A0
    Tc = np.ascontiguousarray(Tg[keep])
    Ac = np.ascontiguousarray(A0[keep])
    print(f"lattice: {len(Tc):,} tris ({int((~keep).sum()):,} degenerate dropped), "
          f"{len(Vg):,} verts, e_med={e_med:.4g}, scale_S={S:.3g}")

    # ---- triangle-carrier CA structures (exactly ca_triangle's, all DERIVED) --------------------
    G, N0, fd_max = ct.area_grads(Vg, Tc)
    k = 0.75 * C.K_BOND / Ac                        # R7b derivative (d2U/dlam^2 = 3*K_BOND)
    hi0, hi1, hi2, hi3 = ct.build_hinges(Tc)
    theta0 = ct.compute_theta0(hi0, hi1, hi2, hi3, Vg)
    K_b = C.K_BOND
    ei, ej, ew = ct.build_cot_edges(Vg, Tc)
    K0 = np.zeros((len(Vg), 3)); ct._mean_curv_norm(Vg, ei, ej, ew, K0)
    K_curv = C.K_BOND
    Tg_flat = np.ascontiguousarray(Tc.ravel())
    cnt = np.bincount(Tg_flat, minlength=len(Vg))
    start = np.empty(len(Vg) + 1, dtype=np.int64); start[0] = 0
    np.cumsum(cnt, out=start[1:])
    entries = np.empty(3 * len(Tc), dtype=np.int64)
    cursor = start[:-1].copy()
    for r in range(Tg_flat.shape[0]):
        v = int(Tg_flat[r]); entries[int(cursor[v])] = r; cursor[v] += 1

    # ---- CA integrate (deterministic fold start -> area/bend/curv restore, symplectic Euler) ----
    print(f"CA: {TICKS} ticks dt={DT:.0e} pert={PERT_AMP} (area+bend+curv, the between-triangle "
          f"physics; the point-octree walk is a different substrate and not in this claim)",
          flush=True)
    # A DETERMINISTIC INITIAL FOLD (seed 0): a smooth half-cycle ridge across the lattice so the
    # bend/area/curv restore against real, non-uniform strain. NO rtndomness, NO free number --
    # it is the initial condition the falsifier needs (the family of defects the frost must ride).
    rng = np.random.default_rng(0)
    phase = Vg[:, 0] * 6.0 + Vg[:, 2] * 9.0
    ridge = np.sin(phase)[:, None] * np.array([1.0, 1.2, 0.8])
    perturb = PERT_AMP * C.R_BOND * ridge * (rng.standard_normal((len(Vg), 3)) * 0.5 + 1.0)
    pos = np.ascontiguousarray(Vg + perturb, dtype=np.float64)
    vel = np.zeros((len(Vg), 3), dtype=np.float64)
    Kbuf = np.zeros((len(Vg), 3), dtype=np.float64)
    frames, strains = {}, {}
    normals_all = np.cross(Vg[Tc[:, 1]] - Vg[Tc[:, 0]], Vg[Tc[:, 2]] - Vg[Tc[:, 0]])
    s0, _ = ct._k1_state(pos, Tc, Ac, k, N0)
    frames[0] = pos.copy()
    strains[0] = float(np.abs(s0).max())
    tick_start = time.perf_counter()
    for tick in range(1, TICKS + 1):
        sarr, _ = ct._k1_state(pos, Tc, Ac, k, N0)
        fca = ct._k2_forces(sarr, G, k, start, entries)
        fbend, _, _ = ct._bend_forces(hi0, hi1, hi2, hi3, pos, theta0, K_b, 0.244)
        Kbuf[:] = 0.0
        ct._mean_curv_norm(pos, ei, ej, ew, Kbuf)
        Fcurv = np.zeros((len(Vg), 3))
        ct._curv_force(Kbuf, K0, ei, ej, ew, K_curv, Fcurv)
        a_tot = fca + fbend + Fcurv
        if not bool(np.all(np.isfinite(a_tot))):
            print(f"NON-FINITE at tick {tick} -- {tick} ticks done"); break
        vel += a_tot * DT
        pos += vel * DT
        if tick in CAPTURE:
            strain = float(np.abs(sarr).max())
            frames[tick] = pos.copy()
            strains[tick] = strain
    print(f"  integrated {tick}/{TICKS} ticks in {time.perf_counter()-tick_start:.1f}s")
    for tk, st in strains.items():
        print(f"    tick {tk:4d}  max |A/A0-1| = {st:.4f}")

    # ---- render + measure per frame -------------------------------------------------------------
    cam = camera(az=0.45, el=0.12, r=1.75 * float(np.linalg.norm(Vg.max(0) - Vg.min(0))),
                 target=Vg.mean(0))
    rows = []
    print("  rendering both legs per frame ...", flush=True)
    for tk in CAPTURE:
        if tk not in frames:
            continue
        P = frames[tk]
        disp = float(np.sqrt(np.mean(np.sum((P - frames[CAPTURE[0]]) ** 2, axis=1)))) / C.R_BOND
        normals = normals_all
        Him, Hmask = leg_hard(P, Tc, normals, cam, W, H)
        G_buf = derived_splats(P, Tc, normals)
        Gim, Gmask = leg_gauss(G_buf, cam, W, H)
        mH, SH, NH = _moments2(Hmask)
        mG, SG, NG = _moments2(Gmask)
        cent = float(np.linalg.norm(mH - mG))
        covr = float(np.linalg.norm(SH - SG, "fro") / max(float(np.linalg.norm(SH, "fro")), 1e-30))
        rows.append(dict(tick=int(tk), strain=float(strains[tk]), n_px_masks=(int(NH), int(NG)),
                         rms_disp_bonds=disp, centroid_drift_px=cent, cov_rel=float(covr)))
        # strip: hard | gauss | mask-overlay diff
        diff = np.abs(Him.astype(np.float32) - Gim.astype(np.float32)).mean(axis=2)
        dm = np.clip(diff * 4.0, 0, 255).astype(np.uint8)
        z = np.zeros((H, 1, 3), dtype=np.uint8)
        strip = np.concatenate([Him, Gim, np.repeat(dm[:, :, None], 3, axis=2)], axis=1)
        OUT_PNG.mkdir(parents=True, exist_ok=True)
        Image.fromarray(strip).save(str(OUT_PNG / f"frost_tick{tk:04d}.png"))
        print(f"    tick {tk:4d} strain {strains[tk]:.4f}  rms_disp {disp:.3f}b  "
              f"centroid {cent:.3f}px  cov_rel {covr:.4f}")

    # ---- verdict: named-before-run falsifier ------------------------------------------------------
    cent_max = max(r["centroid_drift_px"] for r in rows)
    cov_max = max(r["cov_rel"] for r in rows)
    xs = np.array([r["strain"] for r in rows], dtype=float)
    ys = np.array([r["centroid_drift_px"] for r in rows], dtype=float)
    zs = np.array([r["rms_disp_bonds"] for r in rows], dtype=float)
    if len(rows) >= 3 and xs.std() > 1e-12:
        pearson = float(np.corrcoef(xs, ys)[0, 1])
        slope_c, slope_res = np.polyfit(xs, ys, 1)
        corr_const = (np.corrcoef(xs, zs)[0, 1] if zs.std() > 1e-12 else 0.0)
        # colour the CA statement: the fold must actually be relaxing (strain->disp correlation)
    else:
        pearson = 0.0; slope_c = 0.0; slope_res = 0.0; corr_const = 0.0
    fy_cov = any(r["cov_rel"] > COV_FALSIFY for r in rows)
    fy_cent = cent_max > CENTROID_FALSIFY
    fy_pear = pearson > PEARSON_FALSIFY
    ok = not (fy_cov or fy_cent or fy_pear)
    print("\nFROST-BINDING VERDICT:", "FROST HOLDS" if ok else "FROST BROKE")
    print(f"  centroid drift max {cent_max:.3f} px (falsify > {CENTROID_FALSIFY})")
    print(f"  covariance rel err max {cov_max:.4f} (falsify > {COV_FALSIFY:.0%})")
    print(f"  residual vs strain Pearson {pearson:+.3f} (falsify > +{PEARSON_FALSIFY})")
    print(f"  residual-vs-strain slope {slope_c:+.3f} px per strain-unit (0 = constant offset, no")
    print(f"    growth); fold actually relaxing? strain-disp corr {corr_const:+.3f}")
    out = dict(pre_registered=dict(statement=(
        "leg G (derived 2D Gaussian) and leg H (hard triangle) are one row; the splat moves "
        "with the CA vertex by construction, at every strain the CA produces"),
        prediction=f"centroid <= {CENTROID_PREDICT}px, cov rel <= {COV_PREDICT:.0%}, "
                   f"Pearson <= +{PEARSON_FALSIFY}",
        falsifier=f"centroid > {CENTROID_FALSIFY}px OR cov > {COV_FALSIFY:.0%} OR "
                  f"Pearson > +{PEARSON_FALSIFY} on any frame"),
        lattice=dict(n_tris=int(len(Tc)), n_verts=int(len(Vg)), scale_S=float(S),
                     degenerate_dropped=int((~keep).sum())),
        ca=dict(ticks=int(tick), dt=float(DT), perturb_amp=float(PERT_AMP),
                forces="area+bend+curv (triangle carrier only)"),
        frames=rows, verdict=bool(ok),
        metrics=dict(centroid_drift_px_max=cent_max, cov_rel_max=cov_max,
                     residual_vs_strain_pearson=pearson, residual_vs_strain_slope=slope_c,
                     ca_strain_vs_disp_corr=corr_const),
        falsifiers_fired=dict(cov=fy_cov, centroid=fy_cent, pearson=fy_pear))
    OUT_JSON.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"  JSON: {OUT_JSON}")
    print(f"  PNGs: {OUT_PNG}\\frost_tick*.png")
    print(f"  total {time.perf_counter()-t0:.1f}s")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())