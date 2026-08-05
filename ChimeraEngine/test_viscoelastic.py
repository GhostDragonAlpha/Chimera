"""test_viscoelastic.py -- Stage 14's falsifiers, and the closing decomposition of rolling loss.

    python ChimeraEngine/test_viscoelastic.py

THE FLAGSHIP (V3). Thermoelastic loss requires the awkward middle between isothermal and adiabatic,
so for a rolling contact there is a SPEED at which it is maximal: v_peak = D/(pi a), derived from
thermal diffusivity and contact size alone. Roll slower and heat equilibrates; roll faster and it
cannot move at all. Both ends dissipate nothing, for two different reasons.

THE CLOSING DECOMPOSITION (V5). Three mechanisms now exist and they are not interchangeable:
    radiation  -- proportional to v; resists a coasting wheel, vanishes at rest
    microslip  -- proportional to T^3; EXACTLY ZERO for a freely coasting wheel
    hysteresis -- proportional to tan d(w); resists a coasting wheel, peaked in speed
Which one dominates is a question with an answer, and it is measured here rather than asserted.

THE HONEST REMAINDER (V6). Thermoelastic damping is a derived FLOOR on bulk loss, never the whole
of it -- anelastic mechanisms need a measured loss tangent no membrane publishes. The machinery
takes tan d as an argument precisely so that a future measurement plugs into it unchanged.
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

import matter                                                        # noqa: E402
from ChimeraEngine.core import hertz, hysteresis, rolling, seam, viscoelastic  # noqa: E402

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
EPS_PEAK = 1e-9          # the Debye peak sits at wt = 1 and equals Delta/2
EPS_SLIDER = 1e-12       # Delta is exactly proportional to temperature
EPS_LOAD = 0.01          # measured mu_r load exponent vs the derived 1/3
EPS_ROBUST = 3.0         # each cited thermal constant varied by this factor


def main() -> int:
    gnd = published("theGround")
    blue = published("aBlueWorld")

    B, G, E, nu = hertz.elastic_constants("silicate")
    e_star = hertz.contact_modulus(E, nu)
    g_star = hertz.shear_contact_modulus(G, nu)
    rho_s = 2650.0
    t_world = float(blue["T_surface"])          # READ from the world, never assumed
    g_here = float(blue["g"])
    mu = seam.friction_coefficient(float(gnd["repose_deg"]))

    r_ball = 0.05
    m_ball = rho_s * (4.0 / 3.0) * math.pi * r_ball ** 3
    n_force = m_ball * g_here
    h = hertz.penetration_for_force(n_force, r_ball, e_star)
    a = float(hertz.contact_radius(h, r_ball))
    kt = float(hertz.tangential_stiffness(h, r_ball, g_star))

    alpha = matter.THERMAL_EXPANSION_PER_K["silicate"]
    c_p = matter.SPECIFIC_HEAT_J_KG_K["silicate"]
    k_th = matter.THERMAL_CONDUCTIVITY_W_M_K["silicate"]
    d_th = matter.thermal_diffusivity(k_th, rho_s, c_p)

    # ═══ V1 -- THE RELAXATION STRENGTH, AND IT READS THE WORLD'S OWN TEMPERATURE ═════════════════
    delta = viscoelastic.relaxation_strength(E, alpha, t_world, rho_s, c_p)
    check("V1 Delta = E alpha^2 T/(rho c_p) is dimensionless and derived",
          0.0 < delta < 1.0,
          f"Delta = {delta:.4e} at aBlueWorld's PUBLISHED T_surface = {t_world:.2f} K "
          f"(the world's own temperature, read not assumed)")
    d2 = viscoelastic.relaxation_strength(E, alpha, 2.0 * t_world, rho_s, c_p)
    check("V1 SLIDER: warm the world and its rock damps more, in exact proportion",
          abs(d2 / delta - 2.0) <= EPS_SLIDER,
          f"2x T gives {d2/delta:.12f}x Delta -- a colder world's rock is a better spring, and "
          f"that is a consequence, not a setting")

    # ═══ V2 -- THE DEBYE SHAPE: two limits, two different reasons ════════════════════════════════
    tau = viscoelastic.relaxation_time(a, d_th)
    check("V2 the peak sits at w tau = 1 and equals Delta/2 exactly",
          abs(viscoelastic.loss_tangent(1.0 / tau, delta, tau) - delta / 2.0) <= EPS_PEAK * delta,
          f"tan d at wt=1 is {viscoelastic.loss_tangent(1/tau, delta, tau):.6e}, Delta/2 = "
          f"{delta/2:.6e}")
    slow = viscoelastic.loss_tangent(1e-6 / tau, delta, tau)
    fast = viscoelastic.loss_tangent(1e6 / tau, delta, tau)
    check("V2 loss vanishes at BOTH ends -- isothermal one side, adiabatic the other",
          slow < delta / 1e5 and fast < delta / 1e5,
          f"tan d = {slow:.2e} at wt=1e-6 (heat equilibrates: no gradient ever forms) and "
          f"{fast:.2e} at wt=1e6 (heat cannot move at all) -- same zero, opposite causes")
    check("V2 and it is a genuine peak, not a plateau",
          viscoelastic.loss_tangent(1 / tau, delta, tau)
          > 4.0 * viscoelastic.loss_tangent(10 / tau, delta, tau),
          "an order of magnitude off the peak already costs most of the loss")

    # ═══ V3 -- THE FLAGSHIP: a rolling speed of maximum loss ═════════════════════════════════════
    v_peak = viscoelastic.peak_rolling_speed(a, d_th)
    speeds = np.array([v_peak / 100.0, v_peak / 10.0, v_peak, v_peak * 10.0, v_peak * 100.0])
    tds = np.array([viscoelastic.loss_tangent(viscoelastic.rolling_omega(v, a), delta, tau)
                    for v in speeds])
    check("V3 FLAGSHIP: thermoelastic loss is MAXIMAL at the derived rolling speed D/(pi a)",
          int(np.argmax(tds)) == 2,
          f"v_peak = {v_peak*1000:.2f} mm/s for a {a*1e6:.0f} um contact; tan d over "
          f"v_peak/100 .. v_peak*100 is {['%.2e' % t for t in tds]} -- the middle wins")
    a_big = 4.0 * a
    check("V3 and a BIGGER contact peaks SLOWER (v_peak ~ 1/a)",
          abs(viscoelastic.peak_rolling_speed(a_big, d_th) / v_peak - 0.25) < 1e-12,
          f"4x the contact radius gives {viscoelastic.peak_rolling_speed(a_big, d_th)*1000:.3f} "
          f"mm/s -- exactly a quarter, because heat has four times as far to go")

    # ═══ V4 -- THE ROLLING COEFFICIENT AND ITS LOAD SCALING ══════════════════════════════════════
    loads, mus = [], []
    for factor in (1.0, 8.0, 64.0, 512.0):
        nn = n_force * factor
        hh = hertz.penetration_for_force(nn, r_ball, e_star)
        aa = float(hertz.contact_radius(hh, r_ball))
        td = viscoelastic.loss_tangent(1.0 / viscoelastic.relaxation_time(aa, d_th),
                                       delta, viscoelastic.relaxation_time(aa, d_th))
        loads.append(nn)
        mus.append(viscoelastic.rolling_coefficient(td, aa, r_ball))
    slope, _ = np.polyfit(np.log(loads), np.log(mus), 1)
    check("V4 hysteretic mu_r scales as N^(1/3) -- the classic load dependence, at fixed tan d",
          abs(slope - 1.0 / 3.0) <= EPS_LOAD,
          f"measured exponent {slope:.4f} vs derived 1/3 over a 512x load range")

    # ═══ V5 -- THE CLOSING DECOMPOSITION: three mechanisms, and when each matters ════════════════
    zeta_a = hertz.radiation_impedance_per_area(B, G, rho_s)
    v_test = 1.0
    mu_hyst, td_roll, _, _, _ = viscoelastic.thermoelastic_rolling(
        "silicate", E, rho_s, t_world, v_test, a, r_ball)
    mu_rad = rolling.rolling_resistance_coefficient(v_test, a, r_ball, zeta_a, n_force)
    cap = mu * n_force
    mu_micro_free = hysteresis.microslip_rolling_coefficient(1e-12 * cap, mu, n_force, kt, a)
    mu_micro_driven = hysteresis.microslip_rolling_coefficient(0.9 * cap, mu, n_force, kt, a)
    check("V5 a FREELY COASTING wheel pays radiation and hysteresis but NOT microslip",
          mu_micro_free < 1e-12 * mu_rad,
          f"microslip {mu_micro_free:.2e} (T^3 -> vanishes with the tractive force) vs radiation "
          f"{mu_rad:.2e} and hysteresis {mu_hyst:.2e} -- the three are not interchangeable")
    check("V5 a HARD-DRIVEN wheel is dominated by microslip instead",
          mu_micro_driven > 100.0 * max(mu_rad, mu_hyst),
          f"microslip {mu_micro_driven:.2e} at 90% traction vs radiation {mu_rad:.2e} and "
          f"hysteresis {mu_hyst:.2e} -- which mechanism rules is a question with an answer")
    check("V5 for HARD quartz, thermoelastic hysteresis is the SMALLEST of the three",
          mu_hyst < mu_rad,
          f"hysteresis {mu_hyst:.2e} < radiation {mu_rad:.2e} at 1 m/s; a soft polymer would "
          f"invert this entirely (tan d ~ 0.1 is four orders above quartz's thermoelastic "
          f"{td_roll:.1e}), which is why rubber tyres and rock behave nothing alike")

    # ═══ V6 -- ROBUSTNESS, AND THE NAMED REMAINDER ══════════════════════════════════════════════
    worst = mu_hyst
    for name, store in (("expansion", matter.THERMAL_EXPANSION_PER_K),
                        ("specific heat", matter.SPECIFIC_HEAT_J_KG_K),
                        ("conductivity", matter.THERMAL_CONDUCTIVITY_W_M_K)):
        original = store["silicate"]
        for f in (EPS_ROBUST, 1.0 / EPS_ROBUST):
            store["silicate"] = original * f
            m_r, *_ = viscoelastic.thermoelastic_rolling("silicate", E, rho_s, t_world,
                                                         v_test, a, r_ball)
            worst = max(worst, m_r)
        store["silicate"] = original
    check("V6 the conclusion survives varying EVERY cited thermal constant by 3x either way",
          worst < 1e-4,
          f"worst-case mu_r across all variations is {worst:.2e}, still far under a handbook "
          f"~1e-3 -- the finding does not rest on the precision of a cited constant")
    check("V6 the machinery takes tan d as an ARGUMENT, so a measured loss tangent plugs straight in",
          viscoelastic.rolling_coefficient(0.1, a, r_ball) > 100.0 * mu_hyst,
          f"a polymer's tan d = 0.1 would give mu_r = "
          f"{viscoelastic.rolling_coefficient(0.1, a, r_ball):.3e} through the same function -- "
          f"ANELASTIC bulk loss (dislocations, grain boundaries) is still UNBUILT and still needs "
          f"a published measurement, but nothing has to be rewritten to accept one")

    print(f"\n{_PASS} passed, {_FAIL} failed", flush=True)
    return 1 if _FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
