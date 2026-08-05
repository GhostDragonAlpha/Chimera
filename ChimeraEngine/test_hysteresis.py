"""test_hysteresis.py -- Stage 13's falsifiers, and a correction to Stage 12's record.

    python ChimeraEngine/test_hysteresis.py

THE CORRECTION (Y6). Stage 12 recorded that hysteretic rolling loss "needs a published loss
tangent that no membrane has". Building it proved that too broad: CONTACT MICROSLIP hysteresis
needs only mu and G*, both already derived, and only BULK VISCOELASTIC loss still needs a cited
constant. The claim is corrected here rather than quietly amended, and the sharper split is now
what the ledger carries.

THE DIAGNOSIS (Y2). Stage 11's tangential law is a linear spring under a hard cap: loading and
unloading trace the SAME path, so it encloses zero area BY CONSTRUCTION. That is computed here
with the same loop integral used on Mindlin's curve -- shown, not asserted -- so the reason the
earlier model could not dissipate is on the record as a number.

THE FLAGSHIP (Y3). The loop energy is CUBIC in tangential amplitude, dW ~ 2T^3/(9 mu N k_t) --
the known signature of fretting/microslip damping. The asymptote is derived in hysteresis.py and
the exact loop integral must converge to it; the log-log slope must reach 3.
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

from ChimeraEngine.core import hertz, hysteresis, rolling, seam   # noqa: E402

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
EPS_TANGENT = 1e-6      # Mindlin's initial slope vs Stage 11's k_t
EPS_ASYMPTOTE = 0.02    # exact loop integral vs the derived cubic asymptote, at small amplitude
EPS_SLOPE = 0.02        # measured log-log slope vs the derived 3
EPS_ZERO = 1e-18        # the linear+cap loop must enclose nothing


def main() -> int:
    gnd = published("theGround")
    blue = published("aBlueWorld")

    B, G, E, nu = hertz.elastic_constants("silicate")
    e_star = hertz.contact_modulus(E, nu)
    g_star = hertz.shear_contact_modulus(G, nu)
    rho_s = 2650.0
    mu = seam.friction_coefficient(float(gnd["repose_deg"]))
    g_here = float(blue["g"])

    r_ball = 0.05
    m_ball = rho_s * (4.0 / 3.0) * math.pi * r_ball ** 3
    n_force = m_ball * g_here
    h = hertz.penetration_for_force(n_force, r_ball, e_star)
    a = float(hertz.contact_radius(h, r_ball))
    kt = float(hertz.tangential_stiffness(h, r_ball, g_star))
    cap = mu * n_force

    # ═══ Y1 -- THE SOFTENING CURVE, AND WHAT STAGE 11 APPROXIMATED ═══════════════════════════════
    dt = 1e-9 * cap
    slope0 = float(hysteresis.virgin_displacement(dt, mu, n_force, kt)) / dt
    check("Y1 Mindlin's tangent at the origin IS Stage 11's linear law (1/k_t)",
          abs(slope0 - 1.0 / kt) / (1.0 / kt) <= EPS_TANGENT,
          f"initial compliance {slope0:.6e} m/N vs 1/k_t = {1/kt:.6e} m/N -- the linear law was "
          f"the tangent, which is why it was right at small load and lossless everywhere")
    d_full = hysteresis.full_slip_displacement(mu, n_force, kt)
    check("Y1 full slip arrives 1.5x further out than the linear law put it",
          abs(d_full / (cap / kt) - 1.5) < 1e-12,
          f"Mindlin {d_full*1e6:.3f} um vs linear {cap/kt*1e6:.3f} um -- the approximation, "
          f"stated as a number instead of a shrug")

    # ═══ Y2 -- THE DIAGNOSIS: the old law could not dissipate, and here is the zero ══════════════
    t_star = 0.4 * cap
    w_lin = hysteresis.linear_cap_loop_energy(t_star, mu, n_force, kt)
    w_mind = hysteresis.loop_energy(t_star, mu, n_force, kt)
    check("Y2 Stage 11's linear+cap loop encloses EXACTLY ZERO area (computed, not asserted)",
          w_lin <= EPS_ZERO,
          f"{w_lin:.3e} J per cycle -- loading and unloading retrace one line, so the missing "
          f"hysteresis was the APPROXIMATION, never a missing material constant")
    check("Y2 Mindlin's loop encloses real area at the same amplitude",
          w_mind > 0.0, f"{w_mind:.3e} J per cycle at T = {t_star/cap:.0%} of the ceiling")

    # ═══ Y3 -- THE FLAGSHIP: the cubic law ═══════════════════════════════════════════════════════
    # THE CUBIC LAW IS AN ASYMPTOTE, AND THE TEST MUST BE ASKED IN ITS OWN REGIME. The first
    # version of this fitted 2-16% of the ceiling and read 3.0474, then called the model wrong.
    # It was the test that was wrong: the integral is converged to nine significant figures
    # (n_pts 5k -> 320k moves it in the 9th), so the rise is PHYSICS -- the loop stiffens as full
    # slip approaches. Measured in the asymptotic regime it goes to 3, and the departure outside
    # it is recorded below as a fact rather than smoothed away by a wider tolerance.
    fracs = np.array([0.0025, 0.005, 0.01, 0.02])
    ws = np.array([hysteresis.loop_energy(f * cap, mu, n_force, kt) for f in fracs])
    slope, _ = np.polyfit(np.log(fracs * cap), np.log(ws), 1)
    check("Y3 FLAGSHIP: microslip loss is CUBIC in tangential amplitude (asymptotic regime)",
          abs(slope - 3.0) <= EPS_SLOPE,
          f"measured log-log slope {slope:.4f} vs derived 3, over 0.25-2% of the Coulomb ceiling "
          f"-- the known fretting signature, and nothing here was fitted to it")
    big = np.array([0.1, 0.2, 0.3, 0.4])
    ws_big = np.array([hysteresis.loop_energy(f * cap, mu, n_force, kt) for f in big])
    slope_big, _ = np.polyfit(np.log(big * cap), np.log(ws_big), 1)
    check("Y3 and the exponent RISES above 3 as full slip is approached (measured, not smoothed)",
          slope_big > slope + 0.1,
          f"slope {slope_big:.4f} at 10-40% of the ceiling vs {slope:.4f} asymptotically -- the "
          f"slip annulus is eating the contact, so the loop grows faster than cubic")
    small = 0.01 * cap
    exact = hysteresis.loop_energy(small, mu, n_force, kt)
    asym = hysteresis.loop_energy_asymptote(small, mu, n_force, kt)
    check("Y3 the exact loop integral converges to the DERIVED asymptote 2T^3/(9 mu N k_t)",
          abs(exact - asym) / asym <= EPS_ASYMPTOTE,
          f"exact {exact:.6e} J vs asymptote {asym:.6e} J ({100*abs(exact-asym)/asym:.2f}%) -- "
          f"two routes, one number")
    check("Y3 and the loop vanishes as the amplitude does (no loss without a load cycle)",
          hysteresis.loop_energy(0.0, mu, n_force, kt) == 0.0,
          "exactly zero -- like Stage 12's rolling torque at rest, dissipation is a RATE of doing")
    check("Y3 loss grows monotonically with amplitude", bool(np.all(np.diff(ws) > 0)),
          f"{['%.2e' % w for w in ws]} J per cycle")

    # ═══ Y4 -- THE ROLLING APPLICATION ═══════════════════════════════════════════════════════════
    for frac in (0.1, 0.5, 0.9):
        mu_r = hysteresis.microslip_rolling_coefficient(frac * cap, mu, n_force, kt, a)
        check(f"Y4 microslip rolling resistance at {frac:.0%} tractive force",
              mu_r > 0.0,
              f"mu_r = {mu_r:.3e} (a driven wheel pays cubically; a coasting one barely pays)")
    # Asked in the asymptotic regime, for the same reason as Y3.
    mu_r_1 = hysteresis.microslip_rolling_coefficient(0.01 * cap, mu, n_force, kt, a)
    mu_r_2 = hysteresis.microslip_rolling_coefficient(0.02 * cap, mu, n_force, kt, a)
    check("Y4 doubling the tractive force costs ~8x the rolling loss (cubic, in the rolling form)",
          abs(mu_r_2 / mu_r_1 - 8.0) / 8.0 < 0.05,
          f"{mu_r_2/mu_r_1:.3f}x -- a statement the constant-mu_r model cannot make at all")
    mu_r_10 = hysteresis.microslip_rolling_coefficient(0.1 * cap, mu, n_force, kt, a)
    mu_r_20 = hysteresis.microslip_rolling_coefficient(0.2 * cap, mu, n_force, kt, a)
    check("Y4 and harder driving costs MORE than cubic (the same departure Y3 measured)",
          mu_r_20 / mu_r_10 > 8.0,
          f"{mu_r_20/mu_r_10:.3f}x at 10-20% of the ceiling -- a wheel worked near its friction "
          f"limit pays disproportionately, which is a real and useful thing to be able to say")

    # ═══ Y5 -- THE TWO MECHANISMS SIDE BY SIDE, HONESTLY ═════════════════════════════════════════
    zeta_a = hertz.radiation_impedance_per_area(B, G, rho_s)
    mu_rad = rolling.rolling_resistance_coefficient(1.0, a, r_ball, zeta_a, n_force)
    mu_micro = hysteresis.microslip_rolling_coefficient(0.9 * cap, mu, n_force, kt, a)
    check("Y5 microslip DOMINATES radiation for a hard-driven contact",
          mu_micro > mu_rad,
          f"microslip {mu_micro:.3e} vs Stage 12's radiative floor {mu_rad:.3e} at 1 m/s "
          f"({mu_micro/mu_rad:.1f}x) -- and they add, being different mechanisms")
    check("Y5 both together are STILL below a handbook mu_r, and that gap is named",
          mu_micro + mu_rad < 1e-3,
          f"total {mu_micro + mu_rad:.3e} vs steel-on-steel ~1e-3; BULK viscoelastic hysteresis "
          f"needs a published loss tangent and remains UNBUILT -- the honest remainder")

    # ═══ Y6 -- THE CORRECTION TO STAGE 12's RECORD ═══════════════════════════════════════════════
    check("Y6 CORRECTION PINNED: contact hysteresis needed NO new constant after all",
          mu_micro > 0.0,
          "Stage 12 said hysteretic loss 'needs a loss tangent no membrane publishes'. That was "
          "too broad: this whole module is built from mu (grown repose) and G* (cited shear "
          "modulus), both already in hand. Only BULK viscoelastic loss still needs a citation")

    print(f"\n{_PASS} passed, {_FAIL} failed", flush=True)
    return 1 if _FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
