"""test_rolling.py -- Stage 12's falsifiers: contact torque, and rolling resistance without a knob.

    python ChimeraEngine/test_rolling.py

THE FLAGSHIP (L4). A sphere launched sliding transitions to rolling at exactly v = (5/7)v0 --
independent of the friction coefficient, of gravity, of the sphere's mass and radius, and of the
material. It depends on one thing: the 2/5 in a solid sphere's moment of inertia. The fraction 5/7
appears NOWHERE in the code, so measuring it tests the lever arm, the Coulomb ceiling, the inertia
and the integrator simultaneously against a number none of them contains. It is checked across two
frictions and two gravities precisely because it must not move.

THE DERIVATION CHECK (L1). Rolling resistance is computed here as a MOMENT integral; the power it
removes is computed as an ENERGY integral. tau_r * omega must equal that power. Two different
integrals of the same physics -- if the algebra is wrong, they part company.

THE HONEST RESULT (L5). The radiative rolling resistance comes out microscopic next to sliding
friction and next to any handbook mu_r. That is not a failure and it is not hidden: this model
contains ONLY the acoustic contribution, and real rolling resistance is dominated by bulk
hysteresis, which needs a loss tangent no membrane publishes. The gap IS the missing measurement.
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

import matter                                          # noqa: E402
from ChimeraEngine.core import hertz, rolling, seam     # noqa: E402

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
EPS_QUAD = 1e-6        # closed form vs quadrature of the same integral
EPS_ENERGY = 1e-6      # moment route vs energy route
EPS_57 = 2e-3          # measured v_roll/v0 vs 5/7 (Verlet-free Euler + the Mindlin transient)
EPS_LINEAR = 1e-12     # tau_r must be exactly proportional to v


def main() -> int:
    gnd = published("theGround")
    blue = published("aBlueWorld")

    B, G, E, nu = hertz.elastic_constants("silicate")
    e_star = hertz.contact_modulus(E, nu)
    g_star = hertz.shear_contact_modulus(G, nu)
    rho_s = 2650.0
    zeta_a = hertz.radiation_impedance_per_area(B, G, rho_s)
    c_p = hertz.p_wave_speed(B, G, rho_s)
    g_here = float(blue["g"])
    mu = seam.friction_coefficient(float(gnd["repose_deg"]))

    # ═══ L0 -- THE IMPEDANCE PER UNIT AREA, AND A FREE CHECK ON BOTH CITED MODULI ════════════════
    check("L0 the solid's longitudinal speed comes out at quartz's measured ~6000 m/s",
          5500.0 < c_p < 6500.0,
          f"c_p = sqrt((B + 4G/3)/rho) = {c_p:.0f} m/s from the two cited moduli -- a free check "
          f"that neither is wrong (Stage 9's sqrt(B/rho) is the FLUID speed and would give "
          f"{math.sqrt(B/rho_s):.0f})")

    # ═══ L1 -- TWO INTEGRALS OF THE SAME PHYSICS MUST AGREE ══════════════════════════════════════
    r_ball, v_test = 0.05, 1.0
    m_ball = rho_s * (4.0 / 3.0) * math.pi * r_ball ** 3
    n_force = m_ball * g_here
    h = hertz.penetration_for_force(n_force, r_ball, e_star)
    a = float(hertz.contact_radius(h, r_ball))
    tau_closed = rolling.rolling_torque(v_test, a, r_ball, zeta_a)
    tau_quad = rolling.rolling_torque_numeric(v_test, a, r_ball, zeta_a)
    check("L1 closed-form rolling torque == quadrature over the contact patch",
          abs(tau_closed - tau_quad) / tau_quad <= EPS_QUAD,
          f"closed {tau_closed:.6e} N.m, quadrature {tau_quad:.6e} N.m")
    power = rolling.rolling_dissipation_power(v_test, a, r_ball, zeta_a)
    check("L1 the MOMENT route and the ENERGY route agree (tau_r * omega == dissipated power)",
          abs(tau_closed * (v_test / r_ball) - power) / power <= EPS_ENERGY,
          f"tau*omega = {tau_closed * v_test / r_ball:.6e} W, direct integral {power:.6e} W")

    # ═══ L2/L3 -- WHAT VISCOUS MEANS, AND WHY IT MATTERS ═════════════════════════════════════════
    check("L2 a body at REST feels no rolling resistance (a constant-mu_r model wrongly would)",
          rolling.rolling_torque(0.0, a, r_ball, zeta_a) == 0.0,
          "exactly zero -- no stiction hack needed, because the damping is a RATE effect")
    t1 = rolling.rolling_torque(1.0, a, r_ball, zeta_a)
    t3 = rolling.rolling_torque(3.0, a, r_ball, zeta_a)
    check("L3 rolling resistance is VISCOUS -- exactly proportional to speed",
          abs(t3 / t1 - 3.0) <= EPS_LINEAR,
          f"3x the speed is {t3/t1:.12f}x the torque; the textbook constant-mu_r model predicts "
          f"1x, so this is a genuine disagreement and it is on the record")
    a2 = float(hertz.contact_radius(hertz.penetration_for_force(8.0 * n_force, r_ball, e_star),
                                    r_ball))
    scale = rolling.rolling_torque(1.0, a2, r_ball, zeta_a) / t1
    check("L3 and it stiffens as N^(4/3) (tau_r ~ a^4, a ~ N^(1/3))",
          abs(scale - 8.0 ** (4.0 / 3.0)) / 8.0 ** (4.0 / 3.0) < 1e-9,
          f"8x the load gives {scale:.3f}x the torque; 8^(4/3) = {8.0**(4/3):.3f}")

    # ═══ L4 -- THE FLAGSHIP: 5/7, AND IT MUST NOT MOVE ═══════════════════════════════════════════
    for mu_t, g_t, label in ((mu, g_here, "grown mu, this world's g"),
                             (0.35, g_here, "half the friction"),
                             (mu, 9.80665, "Earth gravity")):
        ratio, t_slip, n = rolling.sliding_to_rolling(m_ball, r_ball, g_t, 2.0, mu_t,
                                                      e_star, g_star)
        check(f"L4 FLAGSHIP ({label}): sliding -> rolling at exactly 5/7 v0",
              abs(ratio - 5.0 / 7.0) <= EPS_57,
              f"v_roll/v0 = {ratio:.5f} vs 5/7 = {5/7:.5f}; slipped for {t_slip*1000:.1f} ms "
              f"over {n:,} steps -- and 5/7 appears nowhere in the code")

    r_big = 0.20
    m_big = rho_s * (4.0 / 3.0) * math.pi * r_big ** 3
    ratio_big, _, _ = rolling.sliding_to_rolling(m_big, r_big, g_here, 2.0, mu, e_star, g_star)
    check("L4 and it is independent of size and mass too (64x the mass, 4x the radius)",
          abs(ratio_big - 5.0 / 7.0) <= EPS_57,
          f"v_roll/v0 = {ratio_big:.5f} -- only the sphere's 2/5 inertia factor survives")

    # ═══ L5 -- CONTACT TORQUE, AND THE HONEST SIZE OF THE RADIATIVE FLOOR ════════════════════════
    f_t = mu * n_force
    check("L5 contact torque is the moment of Stage 11's tangential force, tau = R F_t",
          abs(rolling.contact_torque(r_ball, f_t) - r_ball * f_t) < 1e-15,
          f"{rolling.contact_torque(r_ball, f_t):.4f} N.m at the Coulomb ceiling -- this is what "
          f"spins a grain up, and what the 5/7 result is built out of")
    mu_r = rolling.rolling_resistance_coefficient(1.0, a, r_ball, zeta_a, n_force)
    check("L5 rolling is vastly cheaper than sliding (this is why a wheel is worth having)",
          mu_r < mu / 1000.0,
          f"mu_r = {mu_r:.3e} at 1 m/s vs sliding mu = {mu:.3f} -- a factor of {mu/mu_r:,.0f}")
    check("L5 HONEST SCOPE: this is the RADIATIVE FLOOR, orders below any handbook mu_r",
          mu_r < 1e-4,
          f"a handbook steel-on-steel mu_r is ~1e-3 and rubber-on-road ~1e-2; this model has only "
          f"the acoustic term, and bulk HYSTERESIS -- which needs a loss tangent no membrane "
          f"publishes -- is the missing measurement, named UNBUILT rather than fitted")

    print(f"\n{_PASS} passed, {_FAIL} failed", flush=True)
    return 1 if _FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
