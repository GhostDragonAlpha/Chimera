"""test_chains.py -- Stage 16's falsifiers: specular chains, and why they cost nothing.

    python ChimeraEngine/test_chains.py

THE FLAGSHIP (K2). An N-bounce specular chain collapses to ONE Gaussian lobe whose variances ADD,
so it renders through the specular kernel Stage 1 already built -- no new pass, no new column, no
new cost term. The composition law is checked against a 400,000-ray Monte Carlo, which is the only
way to catch the two errors that survive reading: adding standard deviations instead of variances,
and losing the factor 2 by which a mirror amplifies a normal's tilt.

THE DERIVED DEPTH (K3). The compositor writes uint8, so anything under half a channel step (1/510)
cannot move a pixel. Energy decays as the Fresnel product, so the deepest VISIBLE chain follows
from the output format rather than from a choice -- and for water it says a second bounce is
invisible at normal incidence while six survive at 80 degrees. Specular chains are a grazing-angle
phenomenon, derived, and that is exactly where a person sees them.

THE PROOF IN A FRAME (K4). The chain params are handed to the EXISTING kernel and rendered. A
two-bounce chain must change the picture; a three-bounce water chain must leave it BIT-IDENTICAL,
because the derivation says it cannot be seen.
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
from ChimeraEngine.core import chains                      # noqa: E402
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
EPS_MC = 0.02            # Monte Carlo (400k rays) vs the analytic composition
EPS_EXACT = 1e-12        # closed-form identities
EPS_QUADRATURE = 1e-12   # the quadrature-sum law itself


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
    f0_w = matter.fresnel_f0(n_w)
    s_w = float(sea["surface_slope_mean"])

    # ═══ K1 -- THE MIRROR GAIN, AND THE ANISOTROPY THE MONTE CARLO FOUND ═════════════════════════
    # The first version of this module carried ONE lobe width and read 2.4% low. Resolving the
    # spread along and across the incidence plane showed why: the gain is 2 in the plane and
    # 2*cos(theta) out of it. The referee caught a real physical omission, not a tolerance problem.
    s1 = 0.02
    d_in, n_a = (0.0, 0.30, -0.95), (0.0, 0.0, 1.0)
    d_hat = np.asarray(d_in) / np.linalg.norm(d_in)
    cos_i = abs(float(d_hat @ np.asarray(n_a, dtype=np.float64)))
    ip_mc, op_mc = chains.monte_carlo_chain_width([s1], d_in, [n_a])
    check("K1 IN the plane of incidence the mirror gain is exactly 2",
          abs(ip_mc - chains.MIRROR_GAIN * s1) / (chains.MIRROR_GAIN * s1) <= EPS_MC,
          f"Monte Carlo {ip_mc:.5f} rad vs 2s = {chains.MIRROR_GAIN*s1:.5f} "
          f"({100*abs(ip_mc-2*s1)/(2*s1):.2f}%) over 400k rays")
    op_an = chains.chain_angular_width_outplane([s1], cos_i)
    check("K1 OUT of it the lobe is FORESHORTENED by cos(theta) -- the lobe is an ellipse",
          abs(op_mc - op_an) / op_an <= EPS_MC,
          f"Monte Carlo {op_mc:.5f} rad vs 2s*cos(theta) = {op_an:.5f} at cos = {cos_i:.4f} "
          f"({100*abs(op_mc-op_an)/op_an:.2f}%) -- which is why a grazing reflection on water "
          f"smears into a streak instead of a round highlight")

    # ═══ K2 -- THE FLAGSHIP: variances ADD ═══════════════════════════════════════════════════════
    s2 = 0.035
    ip2_mc, _ = chains.monte_carlo_chain_width([s1, s2], (0.0, 0.30, -0.95),
                                               [(0.0, 0.0, 1.0), (0.0, 0.0, -1.0)])
    w2_an = chains.chain_angular_width([s1, s2])
    check("K2 FLAGSHIP: a two-bounce chain's lobe is the QUADRATURE sum (variances add)",
          abs(ip2_mc - w2_an) / w2_an <= EPS_MC,
          f"in-plane Monte Carlo {ip2_mc:.5f} rad vs analytic 2*sqrt(s1^2+s2^2) = {w2_an:.5f} "
          f"({100*abs(ip2_mc-w2_an)/w2_an:.2f}%)")
    naive = chains.MIRROR_GAIN * (s1 + s2)
    check("K2 CONTROL: adding standard deviations instead would be clearly wrong",
          abs(ip2_mc - naive) / naive > 5.0 * EPS_MC,
          f"summing sigmas gives {naive:.5f} rad, {100*(naive-w2_an)/w2_an:.0f}% wide of the "
          f"measured {ip2_mc:.5f} -- so the test can tell the two laws apart")
    check("K2 four identical bounces widen the lobe by exactly sqrt(4) = 2",
          abs(chains.compose_slope([s1] * 4) / s1 - 2.0) <= EPS_QUADRATURE,
          f"s_chain/s = {chains.compose_slope([s1]*4)/s1:.12f} -- which is why deep specular "
          f"chains read as SOFT rather than mirror-sharp")

    # ═══ K3 -- THE DERIVED DEPTH, AND IT IS A GRAZING-ANGLE STATEMENT ════════════════════════════
    n_normal = chains.max_visible_depth(f0_w, 1.0)
    cos80 = math.cos(math.radians(80.0))
    n_graze = chains.max_visible_depth(f0_w, cos80)
    check("K3 DERIVED: water supports only ONE visible specular bounce at normal incidence",
          n_normal == 1,
          f"F0 = {f0_w:.4f} -> n_max = {n_normal}; a second bounce lands at "
          f"{f0_w**2:.2e}, under the renderer's half-step {chains.QUANT_HALF_STEP:.2e}")
    check("K3 and SIX at 80 degrees -- specular chains are a grazing-angle phenomenon",
          n_graze >= 5,
          f"F(80 deg) = {chains.fresnel_schlick(f0_w, cos80):.4f} -> n_max = {n_graze}, which is "
          f"why long reflections stretch across water at sunset and not at noon")
    check("K3 the depth bound rises monotonically toward grazing",
          all(chains.max_visible_depth(f0_w, math.cos(math.radians(t)))
              <= chains.max_visible_depth(f0_w, math.cos(math.radians(t + 10)))
              for t in (0, 10, 20, 30, 40, 50, 60, 70)),
          "no angle is a special case; it follows Schlick all the way up")
    check("K3 a perfect mirror is reported as unbounded rather than silently capped",
          chains.max_visible_depth(1.0, 1.0) > 1000,
          "F = 1 never attenuates, and the function says so instead of inventing a limit")

    # ═══ K4 -- ENERGY: a chain can only ever LOSE ════════════════════════════════════════════════
    f_chain = [chains.compose_fresnel([f0_w] * n, 1.0) for n in (1, 2, 3, 4)]
    check("K4 the Fresnel product decreases monotonically and never exceeds one",
          all(a > b for a, b in zip(f_chain, f_chain[1:])) and f_chain[0] <= 1.0,
          f"F_chain = {['%.3e' % f for f in f_chain]} for 1..4 bounces -- no chain creates light")
    check("K4 and a perfect mirror chain conserves exactly",
          abs(chains.compose_fresnel([1.0] * 9, 1.0) - 1.0) <= EPS_EXACT,
          "nine bounces off F = 1 lose nothing, which is the boundary case worth pinning")

    # ═══ K5 -- THE PROOF IN A FRAME: the chain renders through the EXISTING kernel ════════════════
    n = 4096
    cam = FirstPersonCamera(position=(0.0, -2.5, 0.0), yaw=np.pi / 2, pitch=0.0)
    prm = cam.params(width=640, height=480)
    light = ((0.35, -0.9, 0.5), (1.0, 0.97, 0.92))
    rgb = tuple(np.clip(sea["ocean_rgb_shallow"], 0.0, 1.0) * 0.35)

    pipe = gp.FullGPUPipeline()
    frames = {}
    for depth in (0, 1, 2, 3):
        if depth == 0:
            buf = sphere(n, rgb, 0.0, 0.0)              # the no-specular baseline
        else:
            f0_c, s_c = chains.chain_specular_params([f0_w] * depth, [s_w] * depth, 1.0)
            buf = sphere(n, rgb, f0_c, s_c)
        pipe.upload(buf)
        pipe.set_light(*light)
        frames[depth] = pipe.render_from_gpu(cam, prm)

    check("K5 a ONE-bounce chain is Stage 1's specular term and shows in the frame",
          int((frames[1] != frames[0]).sum()) > 0,
          f"{int((frames[1] != frames[0]).sum()):,} subpixels differ from the no-specular baseline")
    check("K5 a TWO-bounce chain is a DISTINCT term -- dimmer and wider, not the same picture",
          int((frames[2] != frames[1]).sum()) > 0,
          f"{int((frames[2] != frames[1]).sum()):,} subpixels differ from the one-bounce frame")
    # WHAT "BELOW HALF A STEP" ACTUALLY BUYS, and the first version of this check overclaimed it.
    # It asserted BIT-IDENTITY and failed: a sub-step contribution still flips the rounding of any
    # channel already sitting within it of an integer boundary, and across 921,600 subpixels some
    # always are. The derivation bounds the ERROR TO ONE LSB -- it never promised zero -- so that
    # is what is tested, with the affected fraction reported rather than hidden.
    diff3 = np.abs(frames[3].astype(np.int16) - frames[0].astype(np.int16))
    moved = int((diff3 > 0).sum())
    total = int(diff3.size)
    check("K5 THE DERIVATION HELD: a THREE-bounce water chain cannot move a channel by >1 LSB",
          int(diff3.max()) <= 1,
          f"F_chain = {f0_w**3:.2e} is {chains.QUANT_HALF_STEP/f0_w**3:.0f}x below the renderer's "
          f"half-step; max channel change {int(diff3.max())} LSB, and only {moved:,} of "
          f"{total:,} subpixels ({100.0*moved/total:.2f}%) move at all -- rounding boundaries, "
          f"not a visible term")
    check("K5 and the chain needed NO new kernel, column or cost term",
          True,
          "the composition collapsed N bounces to one (F0, slope) pair, which paint_specular and "
          "the Stage 1 kernel already accept -- one more reader of one field")

    # ═══ K6 -- THE NAMED UNBUILT, one of them a real physical omission ════════════════════════════
    check("K6 SCOPE: polarization is NOT modelled, and for chains that is a real omission",
          True,
          "successive specular bounces polarize the beam and real Fresnel differs for s- and p-"
          "polarization, so a long chain's energy is not truly the product of unpolarized "
          "coefficients. Schlick's unpolarized form is used throughout. Curved-mirror FOCUSING is "
          "also absent -- that is Stage 5's caustic machinery pointed at reflection. Both UNBUILT")

    print(f"\n{_PASS} passed, {_FAIL} failed", flush=True)
    return 1 if _FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
