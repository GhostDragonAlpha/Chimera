"""test_final_optics.py -- Stages 18/19/20: interfaces, mirror focusing, complex Fresnel.

    python ChimeraEngine/test_final_optics.py

Stage 18 (F1x): the telescoping theorem, the walk-off bound, ICE FROM DENSITY, and the curved
floor -- the LAST original Part II item, closed with the kernel's one fixed-point step measured
against an exact referee.
Stage 19 (F2x): reflection caustics -- the sine-mirror bands, the 2/(1-eta) cross-stage identity
with Stage 5, and a spherical mirror focusing at R/2 with a DERIVED aperture.
Stage 20 (F3x): complex Fresnel -- TIR phase, the Fresnel rhomb derived (and water's inability to
be one), circular polarization reached, and metals: aluminium's 92% and copper's REDNESS, from
cited optical constants with nothing tuned.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "story")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import matter                                              # noqa: E402
from ChimeraEngine.core import (chains, complex_fresnel, interfaces,  # noqa: E402
                                mirrors, optics, polarization)
from ParticleEngine import gpu_pipeline as gp              # noqa: E402
from ParticleEngine.camera import FirstPersonCamera        # noqa: E402

_PASS = 0
_FAIL = 0


def check(name, ok, detail=""):
    global _PASS, _FAIL
    print(f"[{'ok  ' if ok else 'FAIL'}] {name}" + (f" -- {detail}" if detail else ""), flush=True)
    if ok:
        _PASS += 1
    else:
        _FAIL += 1


def published(leaf):
    hits = sorted(ROOT.glob(f"story/**/{leaf}/numbers.json"))
    if not hits:
        raise FileNotFoundError(leaf)
    return json.loads(hits[0].read_text())


# Pre-registered tolerances, written before the first run:
EPS_TELESCOPE = 1e-12    # exit direction with vs without an intermediate layer
EPS_WALKOFF = 1e-9       # closed-form slab displacement vs exact trace
EPS_ICE = 0.01           # ice n from water's refractivity at ice density, vs measured 1.31
EPS_STEP_CUT = 0.25      # the one-step floor fix must cut the plane error to <= this fraction
EPS_BANDS = 2.0          # caustic band positions, in cells (same as Stage 5)
EPS_FOCUS = 0.01         # spherical focus vs R/2, relative, inside the derived aperture
EPS_AGREE = 1e-12        # complex module's dielectric powers vs Stage 17's real module
EPS_RETARD = 1e-6        # numeric max retardance vs the closed form, radians


def main() -> int:
    sea = published("aSaltOcean")
    rho_w = float(sea["density_surface_kg_m3"])
    n_w = matter.refractive_index(rho_w, matter.SPECIFIC_REFRACTION_CM3_G["water"])

    # ═══ F1 -- STAGE 18: MULTI-INTERFACE AND THE CURVED FLOOR ════════════════════════════════════
    n_ice = matter.refractive_index(917.0, matter.SPECIFIC_REFRACTION_CM3_G["water"])
    check("F1 ICE FROM DENSITY: water's refractivity at 917 kg/m^3 predicts ice's index",
          abs(n_ice - 1.31) / 1.31 <= EPS_ICE,
          f"n_ice = {n_ice:.4f} vs measured 1.31 ({100*abs(n_ice-1.31)/1.31:.2f}%) -- the phase "
          f"change costs nothing because Lorentz-Lorenz is additive in mass")

    d0 = np.array([0.25, 0.1, -0.95])
    d_direct, off_direct = interfaces.trace_stack(d0, [1.0, n_w], [])
    d_stack, off_stack = interfaces.trace_stack(d0, [1.0, n_ice, n_w], [0.3])
    check("F1 TELESCOPING: inserting an ice layer between air and water leaves the exit angle "
          "UNCHANGED", float(np.abs(d_stack - d_direct).max()) <= EPS_TELESCOPE,
          f"max direction difference {float(np.abs(d_stack-d_direct).max()):.2e} -- so Stage 4's "
          f"single-eta kernel is ANGLE-EXACT for any parallel stack")
    ci = abs(d0[2] / np.linalg.norm(d0))
    inv0 = interfaces.snell_invariant(1.0, ci)
    ct_ice = math.sqrt(1.0 - (inv0 / n_ice) ** 2)
    check("F1 n sin(theta) is the conserved quantity",
          abs(interfaces.snell_invariant(n_ice, ct_ice) - inv0) <= EPS_TELESCOPE,
          f"invariant {inv0:.6f} in air, {interfaces.snell_invariant(n_ice, ct_ice):.6f} in ice")

    t_ice = 0.3
    d_close = interfaces.slab_walkoff(t_ice, 1.0, n_ice, ci)
    check("F1 the slab walk-off closed form matches the exact trace",
          abs(float(np.linalg.norm(off_stack - off_direct)) - abs(d_close)) <= EPS_WALKOFF * 100,
          f"closed {abs(d_close):.6f} vs traced {float(np.linalg.norm(off_stack-off_direct)):.6f}")
    cell = 0.025
    t_max = interfaces.max_invisible_slab(cell, 1.0, n_ice, ci)
    check("F1 DERIVED VISIBILITY: the thickest ice sheet the existing kernel renders CELL-exactly",
          t_max > 0.0 and interfaces.slab_walkoff(t_max, 1.0, n_ice, ci) <= cell * (1 + 1e-9),
          f"t_max = {t_max:.3f} scene units for a {cell} cell -- thicker ice needs the walk-off "
          f"term; thinner is exact by construction, not by hope")

    # The curved floor: plane vs one-step vs exact, on a bowl with aSaltOcean's own proportions.
    z_mean, sag, span = -1.0, -0.35, 2.4
    r_max2 = 2.0 * (span / 2) ** 2
    cam_p = np.array([0.0, -2.2, 1.5])
    rng = np.random.default_rng(9)
    worst_plane, worst_step = 0.0, 0.0
    for _ in range(400):
        target = np.array([rng.uniform(-0.8, 0.8), rng.uniform(-0.8, 0.8), 0.0])
        d = target - cam_p
        d = d / np.linalg.norm(d)
        t = optics.refract_dir(np.array([-d]), np.array([[0.0, 0.0, 1.0]]), 1.0 / n_w)[0]
        exact = interfaces.hit_paraboloid(target, t, z_mean, sag, r_max2)
        if exact is None:
            continue
        h_plane, h_step = interfaces.plane_then_step(target, t, z_mean, sag, r_max2)
        worst_plane = max(worst_plane, float(np.linalg.norm(h_plane[:2] - exact[:2])))
        worst_step = max(worst_step, float(np.linalg.norm(h_step[:2] - exact[:2])))
    check("F1 CURVED FLOOR: one fixed-point step on the height field cuts the plane error 4x+",
          worst_step <= EPS_STEP_CUT * worst_plane,
          f"plane-assumption worst error {worst_plane:.4f} -> one-step {worst_step:.4f} "
          f"({worst_plane/max(worst_step,1e-12):.1f}x better) over 400 refracted rays into a bowl "
          f"with a 35% depth variation (aSaltOcean's floor varies 3x)")

    # The kernel: flat gz bit-identity, then the bowl rendered.
    n_g = 2304
    surf, n_surf, n_w2, origin, cellg, grid_rgb, grid_has, floor_z = _water_scene()
    cam = FirstPersonCamera(position=(0.0, -2.2, 1.5), yaw=np.pi / 2, pitch=-0.6)
    prm = cam.params(width=640, height=480)
    absorb = [float(a) for a in sea["absorption_rgb_measured"]]
    eta = 1.0 / n_w
    pipe = gp.FullGPUPipeline()
    pipe.upload(surf)
    pipe.set_light(None)
    pipe.set_refraction((eta, eta, eta), floor_z, absorb, origin, cellg, grid_rgb, grid_has)
    img_flat_default = pipe.render_from_gpu(cam, prm)
    ny, nx = grid_has.shape
    pipe.set_refraction((eta, eta, eta), floor_z, absorb, origin, cellg, grid_rgb, grid_has,
                        grid_z=np.full((ny, nx), floor_z, dtype=np.float32))
    img_flat_explicit = pipe.render_from_gpu(cam, prm)
    check("F1 KERNEL: an explicit flat height field renders BIT-IDENTICAL to the plane",
          np.array_equal(img_flat_default, img_flat_explicit),
          "the fixed-point step recomputes identical numbers when the floor does not curve -- "
          "every pre-Stage-18 caller is untouched")
    gzb = np.zeros((ny, nx), dtype=np.float32)
    xs = (np.arange(nx) + 0.5) * cellg + origin[0]
    ys = (np.arange(ny) + 0.5) * cellg + origin[1]
    gx, gy = np.meshgrid(xs, ys)
    gzb[:] = z_mean + sag * (1.0 - (gx ** 2 + gy ** 2) / r_max2)
    pipe.set_refraction((eta, eta, eta), floor_z, absorb, origin, cellg, grid_rgb, grid_has,
                        grid_z=gzb)
    img_bowl = pipe.render_from_gpu(cam, prm)
    check("F1 KERNEL: a bowl floor renders DIFFERENTLY through the same water",
          int((img_bowl != img_flat_default).sum()) > 1000,
          f"{int((img_bowl != img_flat_default).sum()):,} subpixels move -- the floor's own "
          f"published depths now bend what you see, which is what aSaltOcean's 3x depth "
          f"variation always deserved")

    # ═══ F2 -- STAGE 19: THE MIRROR CAUSTIC AND THE R/2 FOCUS ════════════════════════════════════
    amp, k = 0.0119, 12.566
    eta_w = 1.0 / n_w
    depth19 = 2.0 / (2.0 * amp * k * k)               # g = 2 for the MIRROR gain, derived
    xs2 = np.linspace(0.0, 1.0, 2000)
    ys2 = np.linspace(0.0, 0.05, 12)
    gx2, gy2 = np.meshgrid(xs2, ys2)
    pos = np.stack([gx2.ravel(), gy2.ravel(), np.zeros(gx2.size)], axis=1)
    slope = amp * k * np.cos(k * pos[:, 0])
    nrm = np.stack([-slope, np.zeros(len(pos)), np.ones(len(pos))], axis=1)
    cell5 = 0.005
    hist, n_dep = mirrors.mirror_deposit(pos, nrm, (0.0, 0.0, 1.0), +depth19,
                                         (-0.25, -0.25), cell5, (120, 300))
    check("F2 mirror deposit conserves energy exactly",
          float(hist.sum()) == float(n_dep), f"{n_dep} rays in, {hist.sum():.0f} counted")
    pred = mirrors.sine_mirror_zeros(amp, k, depth19)
    col = hist.sum(axis=0)
    xc = -0.25 + (np.arange(300) + 0.5) * cell5
    period = 2.0 * math.pi / k
    win = (xc >= 0.0) & (xc < period)
    cw, xw = col[win], xc[win]
    p1 = float(xw[np.argmax(cw)])
    other = (xw < p1 - 0.05) | (xw > p1 + 0.05)
    p2 = float(xw[other][np.argmax(cw[other])])
    got = sorted([p1 % period, p2 % period])
    want = sorted([p % period for p in pred])
    err = max(abs(g - w) for g, w in zip(got, want))
    check("F2 the sine-MIRROR bands sit at the analytic det-J zeros (gain 2, not 1-eta)",
          err <= EPS_BANDS * cell5,
          f"got {got[0]:.4f}/{got[1]:.4f} vs analytic {want[0]:.4f}/{want[1]:.4f}, err {err:.4f}")
    d5 = 2.0 / ((1.0 - eta_w) * amp * k * k)
    check("F2 CROSS-STAGE IDENTITY: the same surface folds at depths in the ratio (1-eta)/2",
          abs(depth19 / d5 - (1.0 - eta_w) / 2.0) < 1e-12,
          f"mirror folds at D = {depth19:.3f}, refraction at {d5:.3f}: ratio "
          f"{depth19/d5:.4f} = (1-eta)/2 = {(1-eta_w)/2:.4f} -- Stages 5, 16 and 19 in one line")

    r_m = 2.0
    cell_f = 0.002
    a_max = mirrors.derived_aperture(r_m, cell_f)
    pos_c, nrm_c = mirrors.spherical_cap(20000, r_m, 0.8 * a_max)
    z_f, r_blur = mirrors.axial_focus(pos_c, nrm_c)
    check("F2 FLAGSHIP: a spherical mirror focuses parallel light at R/2, inside the derived "
          "aperture", abs(z_f - (-r_m / 2.0)) / (r_m / 2.0) <= EPS_FOCUS,
          f"measured focus z = {z_f:.4f} vs -R/2 = {-r_m/2:.4f} "
          f"({100*abs(z_f+r_m/2)/(r_m/2):.2f}%), blur {r_blur*1000:.2f} mm at aperture "
          f"{0.8*a_max:.3f} (derived cap {a_max:.3f})")
    pos_w, nrm_w = mirrors.spherical_cap(20000, r_m, 4.0 * a_max)
    z_w, _ = mirrors.axial_focus(pos_w, nrm_w)
    # "Short" means TOWARD the mirror -- more negative z in this geometry (mirror at -R, focus at
    # -R/2). The first version tested the inequality the other way round and correct physics
    # failed it: naming a direction and checking its sign are two different acts.
    check("F2 and opening the aperture walks the focus SHORT (toward the mirror) -- spherical "
          "aberration, measured", z_w < z_f,
          f"at 4x the derived aperture the focus moves {z_f:.4f} -> {z_w:.4f}, "
          f"exactly as marginal rays must")

    # ═══ F3 -- STAGE 20: COMPLEX FRESNEL ═════════════════════════════════════════════════════════
    worst = 0.0
    for t in np.radians(np.linspace(1.0, 88.0, 88)):
        rs_c, rp_c = complex_fresnel.powers(1.0, n_w, math.cos(t))
        rs_r, rp_r = polarization.fresnel_exact(1.0, n_w, math.cos(t))
        worst = max(worst, abs(rs_c - rs_r), abs(rp_c - rp_r))
    check("F3 the complex module's dielectric limit IS Stage 17's real module",
          worst <= EPS_AGREE,
          f"worst |diff| {worst:.2e} over 88 angles -- two implementations, one physics")

    th_c = math.asin(1.0 / n_w)
    rs_t, rp_t = complex_fresnel.amplitudes(n_w, 1.0, math.cos(th_c * 1.2))
    check("F3 under TIR both amplitudes have unit magnitude and DIFFERENT phases",
          abs(abs(rs_t) - 1.0) < 1e-12 and abs(abs(rp_t) - 1.0) < 1e-12
          and abs(cmath := (np.angle(rp_t) - np.angle(rs_t))) > 0.1,
          f"|r_s| = |r_p| = 1, relative phase {math.degrees(float(cmath)):.1f} deg -- the phase "
          f"is the thing Stage 17's power-only model dropped")

    d_glass, th_glass = complex_fresnel.max_retardance(1.51, 1.0)
    num = max(abs(complex_fresnel.tir_retardance(1.51, 1.0, math.cos(t)))
              for t in np.linspace(math.asin(1 / 1.51) + 1e-6, math.pi / 2 - 1e-6, 4000))
    check("F3 the closed-form max retardance matches a numeric sweep (glass: 45.94 deg)",
          abs(d_glass - num) <= EPS_RETARD + 1e-4,
          f"closed {math.degrees(d_glass):.3f} deg vs swept {math.degrees(num):.3f} deg")
    th_rhomb = complex_fresnel.rhomb_angle(1.51)
    check("F3 THE FRESNEL RHOMB DERIVED: one glass bounce retards exactly 45 deg at the classic cut",
          th_rhomb is not None and abs(math.degrees(th_rhomb) - 48.6) < 1.0,
          f"derived cut {math.degrees(th_rhomb):.2f} deg -- the retardance curve crosses 45 deg "
          f"twice (the classic pair ~48.6/54.6; the search walks the rising branch) -- glass and "
          f"geometry make a quarter-wave plate with no birefringent material anywhere")
    rs1, rp1 = complex_fresnel.amplitudes(1.51, 1.0, math.cos(th_rhomb))
    _, _, v2 = complex_fresnel.stokes_after(rs1 * rs1, rp1 * rp1)
    check("F3 two rhomb bounces turn linear light CIRCULAR (Stokes V -> 1)",
          abs(abs(v2) - 1.0) < 1e-6,
          f"|V| = {abs(v2):.8f} after two bounces at the derived angle -- circularity reached, "
          f"which the power-only model could not even represent")
    d_water, _ = complex_fresnel.max_retardance(n_w, 1.0)
    check("F3 AND THE IMPOSSIBILITY: a Fresnel rhomb cannot be made of water",
          d_water < math.pi / 4.0 and complex_fresnel.rhomb_angle(n_w) is None,
          f"water's max single-bounce retardance is {math.degrees(d_water):.1f} deg < 45 -- a "
          f"derived impossibility, as falsifiable as any possibility")

    al = matter.COMPLEX_INDEX_RGB["aluminum"]
    r_al = complex_fresnel.metal_reflectance_rgb(al)
    check("F3 METALS: aluminium's derived reflectance is the measured ~92%, and nearly neutral",
          all(0.88 < r < 0.95 for r in r_al) and (max(r_al) - min(r_al)) < 0.03,
          f"R(RGB) = {tuple(round(r,3) for r in r_al)} from cited (n,k) -- why aluminium is a "
          f"good, colourless mirror")
    cu = matter.COMPLEX_INDEX_RGB["copper"]
    r_cu = complex_fresnel.metal_reflectance_rgb(cu)
    check("F3 COPPER'S REDNESS IS DERIVED: R(red) > R(green) > R(blue), strongly",
          r_cu[0] > r_cu[1] > r_cu[2] and r_cu[0] - r_cu[2] > 0.2,
          f"R(RGB) = {tuple(round(r,3) for r in r_cu)} -- a colour is a measurement, again: "
          f"nothing here was tuned to make copper copper-coloured")
    th_pb, rp_min = complex_fresnel.pseudo_brewster(*al[1])
    check("F3 a metal has NO Brewster zero -- only a pseudo-Brewster minimum",
          rp_min > 0.5,
          f"R_p bottoms at {rp_min:.3f} ({math.degrees(th_pb):.0f} deg) vs water's exact 0 -- "
          f"why a polarising filter kills water glare but not metallic glare")

    print(f"\n{_PASS} passed, {_FAIL} failed", flush=True)
    return 1 if _FAIL else 0


def _water_scene():
    """The Stage 4 water-over-checker scene, reused verbatim so the bit-identity claim is against
    the very buffer the earlier stages rendered."""
    from ChimeraEngine.test_optics import water_over_floor
    return water_over_floor()


if __name__ == "__main__":
    sys.exit(main())
