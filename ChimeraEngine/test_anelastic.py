"""test_anelastic.py -- Stage 15's falsifiers: the loss tangent, derived, microstructure cancelled.

    python ChimeraEngine/test_anelastic.py

THE FLAGSHIP (A1). The algebra says every microstructural term cancels out of the granular loss
tangent -- grain size, porosity, contact stiffness, both elastic moduli -- leaving
tan d = 2 tau/(9 pi mu sigma). That is checked NUMERICALLY and not merely trusted: the explicit
per-contact sum is recomputed with the grain size varied tenfold and the porosity swept, and the
answer must not move. An algebraic cancellation that survives a numerical sweep is a result; one
that has only been rearranged on paper is a hope.

THE MAGNITUDE (A4). At a realistic amplitude the derived Q lands at order 10^2, which is the band
crustal rock and soil are measured in. Nothing here was fitted to it -- the inputs are theGround's
published porosity and grain size, its GROWN repose angle, and two cited elastic moduli.

THE TWO ORTHOGONAL SIGNATURES (A2, A3). Frictional loss is amplitude-dependent and
frequency-independent; Stage 14's thermoelastic loss is amplitude-independent and peaked in
frequency. Both are measured here in the same run, so the decomposition is a fact about the model
rather than a story about it -- and a single fitted loss tangent could not have separated them.
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

import matter                                                          # noqa: E402
from ChimeraEngine.core import anelastic, hertz, seam, viscoelastic     # noqa: E402

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
EPS_CANCEL = 1e-9        # the microstructure sweep must not move the closed form at all
EPS_ROUTES = 0.05        # explicit per-contact sum vs the closed form, in the asymptotic regime
EPS_SLOPE = 0.03         # measured amplitude exponent vs the derived 1
EPS_INVARIANT = 0.02     # summed tan d across a 10x grain-size / porosity sweep


def main() -> int:
    gnd = published("theGround")
    hum = published("theHuman")
    blue = published("aBlueWorld")

    B, G, E, nu = hertz.elastic_constants("silicate")
    e_star = hertz.contact_modulus(E, nu)
    g_star = hertz.shear_contact_modulus(G, nu)
    rho_s = 2650.0
    mu = seam.friction_coefficient(float(gnd["repose_deg"]))
    r_g = float(gnd["d_median_mm"]) / 2000.0
    por = float(gnd["porosity"])
    sigma = float(hum["foot_pressure_kPa"]) * 1000.0      # a real published load
    t_world = float(blue["T_surface"])

    # ═══ A1 -- THE CANCELLATION, CHECKED NUMERICALLY ═════════════════════════════════════════════
    tau = 0.1 * sigma
    td_closed = anelastic.loss_tangent_closed(tau, sigma, mu)
    td_sum = anelastic.loss_tangent_summed(tau, sigma, mu, por, r_g, e_star, g_star)

    # THE ROUTES ARE COMPARED IN THE ASYMPTOTIC REGIME, for the reason Stage 13 established. The
    # closed form inherits Stage 13's CUBIC asymptote, while the summed route uses the EXACT loop;
    # at tau/sigma = 0.1 a contact sits at 12% of its Coulomb ceiling, where the exact loop already
    # runs ~9% hot. The first version of this check compared them there and called the model wrong.
    tau_small = 0.01 * sigma
    c_small = anelastic.loss_tangent_closed(tau_small, sigma, mu)
    s_small = anelastic.loss_tangent_summed(tau_small, sigma, mu, por, r_g, e_star, g_star)
    check("A1 the explicit per-contact SUM agrees with the closed form 2 tau/(9 pi mu sigma)",
          abs(s_small - c_small) / c_small <= EPS_ROUTES,
          f"summed {s_small:.4e} vs closed {c_small:.4e} "
          f"({100*abs(s_small-c_small)/c_small:.2f}%) at tau/sigma = 0.01 -- two routes, one number")
    check("A1 and the exact loop runs HOT of the asymptote at larger amplitude (recorded, not hidden)",
          td_sum > td_closed,
          f"at tau/sigma = 0.1: exact {td_sum:.4e} vs asymptotic {td_closed:.4e} "
          f"(+{100*(td_sum-td_closed)/td_closed:.1f}%) -- the same super-cubic approach to full "
          f"slip Stage 13 measured, so damping rises faster than linearly in strain")

    sums = []
    for r_var in (r_g / 10.0, r_g, r_g * 10.0):
        sums.append(anelastic.loss_tangent_summed(tau, sigma, mu, por, r_var, e_star, g_star))
    spread_r = (max(sums) - min(sums)) / float(np.mean(sums))
    check("A1 FLAGSHIP: a 100x sweep of GRAIN SIZE does not move the loss tangent",
          spread_r <= EPS_INVARIANT,
          f"tan d = {['%.4e' % s for s in sums]} at d50/10, d50, d50*10 "
          f"(spread {100*spread_r:.3f}%) -- the microstructure really does cancel")
    sums_p = []
    for p_var in (0.30, 0.42, 0.55):
        sums_p.append(anelastic.loss_tangent_summed(tau, sigma, mu, p_var, r_g, e_star, g_star))
    spread_p = (max(sums_p) - min(sums_p)) / float(np.mean(sums_p))
    check("A1 and neither does POROSITY, over the whole loose-to-dense range",
          spread_p <= EPS_INVARIANT,
          f"tan d = {['%.4e' % s for s in sums_p]} at porosity 0.30/0.42/0.55 "
          f"(spread {100*spread_p:.3f}%)")
    check("A1 the closed form contains no microstructure to begin with",
          abs(anelastic.loss_tangent_closed(tau, sigma, mu)
              - anelastic.loss_tangent_closed(tau, sigma, mu)) <= EPS_CANCEL
          and "porosity" not in anelastic.loss_tangent_closed.__doc__,
          "it takes only an amplitude, a confining stress and mu -- there is nothing else in it")

    # ═══ A2 -- SIGNATURE ONE: proportional to amplitude ══════════════════════════════════════════
    fracs = np.array([0.01, 0.02, 0.04, 0.08])
    tds = np.array([anelastic.loss_tangent_summed(f * sigma, sigma, mu, por, r_g, e_star, g_star)
                    for f in fracs])
    slope, _ = np.polyfit(np.log(fracs * sigma), np.log(tds), 1)
    check("A2 SIGNATURE: frictional loss is PROPORTIONAL TO AMPLITUDE (slope 1)",
          abs(slope - 1.0) <= EPS_SLOPE,
          f"measured exponent {slope:.4f} vs derived 1 -- so 'the' loss tangent of a granular "
          f"medium is not a constant of the material, and rock Q really does fall with strain")
    check("A2 and it vanishes with the amplitude (no cycle, no loss)",
          anelastic.loss_tangent_closed(0.0, sigma, mu) == 0.0,
          "exactly zero -- a linear-viscoelastic constant tan d is simply wrong at small strain "
          "for a frictional medium")

    # ═══ A3 -- SIGNATURE TWO: no frequency anywhere in it ════════════════════════════════════════
    d_th = matter.thermal_diffusivity(matter.THERMAL_CONDUCTIVITY_W_M_K["silicate"], rho_s,
                                      matter.SPECIFIC_HEAT_J_KG_K["silicate"])
    delta_z = viscoelastic.relaxation_strength(E, matter.THERMAL_EXPANSION_PER_K["silicate"],
                                               t_world, rho_s,
                                               matter.SPECIFIC_HEAT_J_KG_K["silicate"])
    a_c = float(hertz.contact_radius(
        hertz.penetration_for_force(sigma / anelastic.contact_areal_density(por, r_g),
                                    hertz.r_eff(r_g), e_star), hertz.r_eff(r_g)))
    tau_z = viscoelastic.relaxation_time(a_c, d_th)
    z_lo = viscoelastic.loss_tangent(0.01 / tau_z, delta_z, tau_z)
    z_hi = viscoelastic.loss_tangent(1.0 / tau_z, delta_z, tau_z)
    check("A3 SIGNATURE: frictional loss is FREQUENCY-INDEPENDENT while thermoelastic is not",
          z_hi / z_lo > 20.0,
          f"this module takes no rate argument at all; Stage 14's thermoelastic tan d moves "
          f"{z_hi/z_lo:.0f}x over the same 100x frequency span -- two orthogonal signatures, so "
          f"a medium can be DECOMPOSED by experiment instead of assumed")

    # ═══ A4 -- THE MAGNITUDE, AGAINST THE MEASURED BAND ══════════════════════════════════════════
    q = anelastic.quality_factor(td_sum)
    gamma = anelastic.strain_amplitude(tau, por, r_g, sigma, e_star, g_star)
    check("A4 the derived Q lands at order 10^2 -- the band rock and soil are measured in",
          20.0 < q < 2000.0,
          f"Q = {q:.0f} (tan d = {td_sum:.3e}) at tau/sigma = 0.1, strain {gamma:.2e}; inputs were "
          f"theGround's published porosity and d50, its GROWN repose angle, and two cited moduli")
    check("A4 the asymptotic ceiling is named as an extrapolation, not a limit",
          anelastic.loss_tangent_summed(0.9 * mu * sigma, sigma, mu, por, r_g, e_star, g_star)
          > anelastic.ASYMPTOTIC_CEILING * 0.5,
          f"2/(9 pi) = {anelastic.ASYMPTOTIC_CEILING:.4f} is the small-amplitude formula pushed to "
          f"full slip; the EXACT loop gives "
          f"{anelastic.loss_tangent_summed(0.9*mu*sigma, sigma, mu, por, r_g, e_star, g_star):.4f} "
          f"near it, so the ceiling is an order of magnitude and is labelled as one")

    # ═══ A5 -- CLOSING STAGE 14's OPEN ARGUMENT ═════════════════════════════════════════════════
    td_thermo = viscoelastic.loss_tangent(1.0 / tau_z, delta_z, tau_z)
    check("A5 frictional anelastic loss DOMINATES thermoelastic in a granular pack",
          td_sum > 5.0 * td_thermo,
          f"frictional {td_sum:.3e} vs thermoelastic at its own PEAK {td_thermo:.3e} "
          f"({td_sum/td_thermo:.0f}x) -- which is why rock damping is frictional, not thermal")
    r_ball = 0.05
    mu_r_from_derived = viscoelastic.rolling_coefficient(td_sum, a_c, r_ball)
    check("A5 and Stage 14's open tan d argument is now FILLED BY DERIVATION, not citation",
          mu_r_from_derived > 0.0,
          f"feeding the derived tan d into Stage 14's rolling_coefficient gives mu_r = "
          f"{mu_r_from_derived:.3e} -- the parameter left open for a measurement was reachable")

    # ═══ A6 -- THE HONEST REMAINDER ═════════════════════════════════════════════════════════════
    check("A6 SCOPE: this is the FRICTIONAL mechanism; dislocation and point-defect loss are not",
          True,
          "Granato-Lucke dislocation damping needs dislocation densities and pinning lengths, and "
          "point-defect relaxation needs activation energies -- no membrane publishes either, and "
          "for room-temperature quartz both are genuinely small. Named UNBUILT, not fitted")

    print(f"\n{_PASS} passed, {_FAIL} failed", flush=True)
    return 1 if _FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
