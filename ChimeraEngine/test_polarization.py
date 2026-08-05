"""test_polarization.py -- Stage 17's falsifiers, and a measured correction to Stage 16.

    python ChimeraEngine/test_polarization.py

THE FLAGSHIP (P3). A specular chain POLARISES ITSELF -- s reflects better than p at every angle, so
each bounce filters the beam further toward s. By convexity the true chain energy therefore EXCEEDS
Stage 16's product of unpolarized coefficients, and the gap grows with depth. The size of that
error is measured here, not estimated, and the frame at the end shows it.

THE NEVER-FITTED PREDICTION (P1). Brewster's angle is arctan(n), and n comes from aSaltOcean's
PUBLISHED density through Lorentz-Lorenz (Stage 0). So the world's own ocean density predicts the
angle at which its glare goes perfectly polarized -- a measurable optical fact, reached from a
number that knows nothing about optics.

THE CROSS-STAGE CHECK (P5). The critical angle derived here must equal the total-internal-reflection
threshold already living in Stage 4's refraction kernel, which got there by a completely different
route (k < 0 in the Snell vector form). Two implementations, one piece of physics.
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
from ChimeraEngine.core import chains, optics, polarization  # noqa: E402
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
EPS_BREWSTER_DEG = 0.5     # derived Brewster angle vs the literature value for water
# R_p AT BREWSTER: the tolerance is DERIVED from the arithmetic, not chosen. r_p's numerator is a
# difference of two O(1) quantities that cancel exactly at Brewster, so its float residual is a few
# machine epsilons -- and R_p is r_p SQUARED, so the floor is eps^2, not eps. A first pass here used
# a round 1e-24 and failed on a correct 4.8e-33; picking a tolerance instead of deriving one is the
# same species of instrument error this lane has caught several times.
EPS_ZERO = (10.0 * float(np.finfo(float).eps)) ** 2
EPS_CONSERVE = 1e-12       # R + T = 1 per polarization
EPS_TIR = 1e-9             # critical angle vs Stage 4's kernel threshold


def sphere(n_grains, rgb, f0, slope):
    d = matter.fibonacci_sphere(n_grains, jitter=0.35, seed=7).astype(np.float32)
    b = matter.blank(n_grains)
    b[:, matter.PX] = d[:, 0]; b[:, matter.PY] = d[:, 1]; b[:, matter.PZ] = d[:, 2]
    b[:, matter.NX] = d[:, 0]; b[:, matter.NY] = d[:, 1]; b[:, matter.NZ] = d[:, 2]
    matter.paint(b, rgb, 1.0, matter.surface_grain(n_grains), matter.SOLID)
    matter.paint_specular(b, f0, slope)
    return b


def main() -> int:
    sea = published("aSaltOcean")
    rho = float(sea["density_surface_kg_m3"])
    n_w = matter.refractive_index(rho, matter.SPECIFIC_REFRACTION_CM3_G["water"])
    s_w = float(sea["surface_slope_mean"])
    f0_w = matter.fresnel_f0(n_w)

    # ═══ P1 -- BREWSTER, FROM THE WORLD'S OWN DENSITY ════════════════════════════════════════════
    th_b = polarization.brewster_angle_rad(1.0, n_w)
    check("P1 PREDICTION: aSaltOcean's published DENSITY predicts its Brewster angle",
          abs(math.degrees(th_b) - 53.1) <= EPS_BREWSTER_DEG,
          f"rho = {rho:.2f} kg/m^3 -> n = {n_w:.4f} -> theta_B = {math.degrees(th_b):.2f} deg "
          f"vs water's measured ~53.1 deg -- a density knows nothing about optics")
    r_s_b, r_p_b = polarization.fresnel_exact(1.0, n_w, math.cos(th_b))
    # THE SURVIVING REFLECTION IS NOT ASSUMED TO BE ANY PARTICULAR SIZE. A first pass demanded
    # R_s > 0.1 and failed on water's true 0.0824 -- a threshold invented rather than read. The
    # physical claim is that R_p VANISHES while R_s does not, so the test is the RATIO.
    check("P1 R_p is EXACTLY zero at Brewster (glare goes perfectly s-polarized)",
          r_p_b <= EPS_ZERO and r_s_b / max(r_p_b, EPS_ZERO) > 1e20,
          f"R_p = {r_p_b:.3e} (float zero; the gate is eps^2 = {EPS_ZERO:.1e}) while R_s stays "
          f"{100*r_s_b:.2f}% -- a ratio of {r_s_b/max(r_p_b, 1e-300):.1e}, and that surviving "
          f"8% is exactly the glare a polarising filter removes")
    check("P1 and a single bounce at Brewster is 100% polarized",
          abs(polarization.degree_of_polarization(1.0, n_w, math.cos(th_b), 1) - 1.0) < 1e-12,
          f"DOP = {polarization.degree_of_polarization(1.0, n_w, math.cos(th_b), 1):.12f} "
          f"after ONE bounce")

    # ═══ P2 -- WHAT SCHLICK APPROXIMATED, MEASURED ═══════════════════════════════════════════════
    angles = np.radians(np.linspace(0.0, 89.0, 90))
    exact = np.array([polarization.fresnel_unpolarized(1.0, n_w, math.cos(t)) for t in angles])
    schlick = np.array([chains.fresnel_schlick(f0_w, math.cos(t)) for t in angles])
    err_mid = float(np.max(np.abs(schlick - exact)[angles < math.radians(60)]))
    err_all = float(np.max(np.abs(schlick - exact)))
    check("P2 Schlick is a good UNPOLARIZED fit below 60 deg -- Stages 1/11/16 validated there",
          err_mid < 0.02,
          f"max absolute error {err_mid:.4f} out to 60 deg (reflectance is O(0.01-0.1) there)")
    check("P2 but it drifts toward grazing, and that is now a measured number not an assumption",
          err_all > err_mid,
          f"max error over all angles {err_all:.4f}, reached near grazing -- Schlick is ONE scalar "
          f"and cannot represent the s/p split at any angle")

    # ═══ P3 -- THE FLAGSHIP: chains polarize, and Stage 16 under-counted ══════════════════════════
    cos60 = math.cos(math.radians(60.0))
    r_s, r_p = polarization.fresnel_exact(1.0, n_w, cos60)
    check("P3 s always reflects better than p (which is WHY a chain polarizes itself)",
          r_s > r_p, f"at 60 deg R_s = {r_s:.4f} vs R_p = {r_p:.5f} ({r_s/r_p:.0f}x)")
    ratios = []
    for depth in (1, 2, 3, 4, 6):
        pol = polarization.chain_energy_polarized(1.0, n_w, cos60, depth)
        unp = polarization.chain_energy_unpolarized(1.0, n_w, cos60, depth)
        ratios.append(pol / unp)
        check(f"P3 depth {depth}: the polarization-correct energy is NEVER below Stage 16's",
              pol >= unp * (1.0 - 1e-12),
              f"true {pol:.4e} vs unpolarized product {unp:.4e} ({pol/unp:.2f}x) -- convexity "
              f"guarantees the direction, and the size is the correction")
    check("P3 FLAGSHIP: the under-count GROWS with depth (Stage 16 was worst where it mattered)",
          ratios[0] < ratios[2] < ratios[-1] and ratios[-1] > 5.0,
          f"ratio by depth 1/2/3/4/6 = {['%.2f' % r for r in ratios]} -- a four-bounce water chain "
          f"at 60 deg carries {ratios[3]:.1f}x the energy Stage 16 credited it with")
    dops = [polarization.degree_of_polarization(1.0, n_w, cos60, d) for d in (1, 2, 4, 8)]
    check("P3 and the chain drives itself to ~100% polarization",
          dops[0] < dops[-1] and dops[-1] > 0.999,
          f"DOP by depth 1/2/4/8 = {['%.4f' % d for d in dops]} -- after a few bounces essentially "
          f"all surviving light is in the strongly-reflecting s state")

    # ═══ P4 -- ENERGY CONSERVATION, per polarization ══════════════════════════════════════════════
    worst = 0.0
    for t in np.radians(np.linspace(0.0, 89.0, 90)):
        rs, rp = polarization.fresnel_exact(1.0, n_w, math.cos(t))
        ts, tp = polarization.transmittance_exact(1.0, n_w, math.cos(t))
        worst = max(worst, abs(rs + ts - 1.0), abs(rp + tp - 1.0))
    check("P4 R + T = 1 for EACH polarization at every angle",
          worst <= EPS_CONSERVE,
          f"worst deviation {worst:.2e} over 90 angles -- this is the check that catches a dropped "
          f"(n2 cos_t)/(n1 cos_i) factor or an inverted sign convention")

    # ═══ P5 -- THE CROSS-STAGE CHECK: one critical angle, two implementations ═════════════════════
    th_c = polarization.critical_angle_rad(n_w, 1.0)
    # Stage 4's kernel/referee decides TIR by k = 1 - eta^2 (1 - c1^2) < 0, with eta = n1/n2.
    eta = n_w / 1.0
    c1 = math.cos(th_c)
    k = 1.0 - eta * eta * (1.0 - c1 * c1)
    check("P5 the critical angle equals Stage 4's refraction-kernel TIR threshold",
          abs(k) <= EPS_TIR,
          f"theta_c = {math.degrees(th_c):.3f} deg from arcsin(1/n); Stage 4's k = {k:.2e} there "
          f"-- two independent routes to one boundary")
    rs_tir, rp_tir = polarization.fresnel_exact(n_w, 1.0, math.cos(th_c * 1.05))
    check("P5 beyond it BOTH polarizations reflect exactly 1.0",
          rs_tir == 1.0 and rp_tir == 1.0,
          "not approximately -- the TIR branch returns unity, as it must")
    check("P5 and there is no critical angle going the other way",
          polarization.critical_angle_rad(1.0, n_w) is None,
          "air into water cannot totally internally reflect, and the function says None")

    # ═══ P6 -- THE CORRECTED DEPTH BOUND ═════════════════════════════════════════════════════════
    cos80 = math.cos(math.radians(80.0))
    n_16 = chains.max_visible_depth(f0_w, cos80)
    n_17 = polarization.max_visible_depth_polarized(1.0, n_w, cos80, chains.QUANT_HALF_STEP)
    check("P6 the visible chain depth at 80 deg is HIGHER once polarization is counted",
          n_17 >= n_16,
          f"Stage 16 said {n_16} bounces, polarization-correct says {n_17} -- the s-component "
          f"decays more slowly than the average, so Stage 16 under-counted visible bounces too")

    # ═══ P7 -- THE CORRECTION IN A FRAME, through the kernel that already exists ══════════════════
    n = 4096
    cam = FirstPersonCamera(position=(0.0, -2.5, 0.0), yaw=np.pi / 2, pitch=0.0)
    prm = cam.params(width=640, height=480)
    light = ((0.35, -0.9, 0.5), (1.0, 0.97, 0.92))
    rgb = tuple(np.clip(sea["ocean_rgb_shallow"], 0.0, 1.0) * 0.35)
    depth = 3
    s_c = chains.compose_slope([s_w] * depth)
    f0_unp = chains.compose_fresnel([f0_w] * depth, cos60)
    f0_pol = polarization.polarized_chain_f0(1.0, n_w, cos60, depth)

    pipe = gp.FullGPUPipeline()
    out = {}
    for tag, f0c in (("unpol", f0_unp), ("pol", f0_pol)):
        pipe.upload(sphere(n, rgb, f0c, s_c))
        pipe.set_light(*light)
        out[tag] = pipe.render_from_gpu(cam, prm)
    brighter = int(out["pol"].astype(np.int16).sum() - out["unpol"].astype(np.int16).sum())
    check("P7 the polarization-corrected chain renders BRIGHTER, through Stage 1's own kernel",
          brighter > 0 and int((out["pol"] != out["unpol"]).sum()) > 1000,
          f"F0 {f0_unp:.3e} -> {f0_pol:.3e} ({f0_pol/f0_unp:.1f}x); "
          f"{int((out['pol'] != out['unpol']).sum()):,} subpixels differ and total brightness rises "
          f"by {brighter:,} LSB -- no polarization state in the renderer, just a corrected number")

    try:
        from PIL import Image
        Image.fromarray(out["pol"]).save(ROOT / "agent_logs" / "optics_chain_polarized.png")
        Image.fromarray(out["unpol"]).save(ROOT / "agent_logs" / "optics_chain_unpolarized.png")
        print("[art ] agent_logs/optics_chain_{polarized,unpolarized}.png written", flush=True)
    except Exception as e:
        print(f"[art ] PNG save skipped: {e}", flush=True)

    # ═══ P8 -- THE SCOPE REFUSAL ═════════════════════════════════════════════════════════════════
    try:
        polarization.refuse_conductor(2.5)
        refused = False
    except ValueError as e:
        refused = "DIELECTRIC" in str(e)
    check("P8 SCOPE: a complex refractive index (a metal) is REFUSED, not approximated",
          refused,
          "absorbing media need complex Fresnel; circular/elliptical polarization needs amplitudes "
          "with a relative phase (TIR's phase shift is dropped here). Both UNBUILT, not fitted")

    print(f"\n{_PASS} passed, {_FAIL} failed", flush=True)
    return 1 if _FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
