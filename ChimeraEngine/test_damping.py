"""test_damping.py -- Stage 10: damping is the medium, not a coefficient. And friction.

    python ChimeraEngine/test_damping.py

THE CLAIM ON TRIAL. Every contact model in the world carries a damping constant somebody chose.
This one does not: what a truncated simulation calls damping is the IMPEDANCE of the material it
truncated, Z = sqrt(k m), and that is derivable twice over from numbers already published.

THE DYAD THAT PROVES IT (D3). The same impact is run two ways:
  * RADIATING: an impactor strikes a chain whose contacts are PURELY ELASTIC -- there is no
    damping term anywhere in that code path. Any restitution below 1 is energy walking away as
    sound, which is a thing the model does rather than a thing it was told.
  * LUMPED: the entire medium replaced by ONE dashpot of the derived Z.
If the two restitutions agree, the dashpot IS the medium and the coefficient was never free.
If they disagree, Z is wrong and no tuning is permitted to rescue it -- that is the falsifier.

FRICTION is labelled honestly: mu = tan(phi) is the DEFINITION of a friction angle, so it is a
restatement, not a derivation. What is not trivial is that phi here was GROWN -- theGround's
repose angle emerged at 40.03 degrees from the granular trainer -- and that the resulting
walkability independently reproduces a boolean theGround already publishes.
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
from ChimeraEngine.core import seam                    # noqa: E402

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
EPS_IMPEDANCE = 1e-12      # two closed forms of one number, float64
EPS_REFLECT = 0.03         # measured R vs transmission-line theory (discrete + pulse dispersion)
EPS_BOOKS = 1e-3           # energy in == absorbed + remaining, over ~40k Verlet steps
EPS_DYAD = 0.05            # radiating chain vs lumped dashpot: the falsifier of Z itself


def main() -> int:
    sea = published("aSaltOcean")
    gnd = published("theGround")
    ter = published("aTerrain")
    hum = published("theHuman")

    rho = float(sea["density_surface_kg_m3"])
    B = matter.BULK_MODULUS_PA["water"]
    m = matter.grain_mass(rho, 0.01)

    # ═══ D1 -- THE IMPEDANCE IS DERIVED TWICE AND AGREES ═════════════════════════════════════════
    z_chain = seam.radiation_impedance(m, B, rho)
    z_cont = seam.continuum_impedance(m, B, rho)
    check("D1 Z = sqrt(km) IS sqrt(2/3)*rho*c*A -- the same packing fraction that set the speed",
          abs(z_chain - z_cont) / z_cont <= EPS_IMPEDANCE,
          f"Z = {z_chain:.6e} N.s/m by both routes")
    k = math.pi * B * (2.0 * seam.rest_radius(m, rho)) / 4.0
    check("D1 Z is exactly critical for one packet on the medium (zeta = Z/2sqrt(kM) = 1/2)",
          abs(z_chain / (2.0 * math.sqrt(k * m)) - 0.5) < 1e-12,
          "a grain meeting its own medium is half-critically damped, with nothing chosen")

    # ═══ D2 -- A TERMINATOR AT Z DOES NOT REFLECT (and the test can fail) ════════════════════════
    for factor, want in ((1.0, 0.0), (2.0, 1.0 / 9.0), (0.5, 1.0 / 9.0), (0.0, 1.0)):
        r_meas, t_meas, books = seam.simulate_reflection(400, m, B, rho, factor)
        check(f"D2 termination at {factor:g}Z reflects {want:.3f} as theory says",
              abs(r_meas - want) <= EPS_REFLECT,
              f"measured R = {r_meas:.4f}, T = {t_meas:.4f} (theory R = ((f-1)/(f+1))^2)")
        # NOTE THE `0.0 <=`: the first version of this check was `books <= tol`, which a NEGATIVE
        # imbalance satisfies -- and that is exactly how a -1e8 energy ratio passed for a while.
        check(f"D2 energy books close at {factor:g}Z (R + T + remaining == 1)",
              0.0 <= books <= EPS_BOOKS, f"imbalance {books:.2e}")

    # ═══ D3 -- THE IMPACT ROUTE TO Z: v(t) = v0 exp(-Z t / M) ════════════════════════════════════
    for mass_ratio in (100.0, 40.0):
        m_imp = mass_ratio * m
        rate, rate_pred, r2, far = seam.impactor_decay(400, m_imp, m, B, rho, v0=0.05)
        check(f"D3 at M/m = {mass_ratio:g}: the impactor decays at exactly Z/M, Z = sqrt(km)",
              abs(rate - rate_pred) / rate_pred <= EPS_DYAD,
              f"measured {rate:.2f} 1/s vs predicted {rate_pred:.2f} 1/s "
              f"({100 * abs(rate - rate_pred) / rate_pred:.2f}%) -- and there is NO damping term "
              f"anywhere in that code path")
        check(f"D3 the decay is a clean exponential at M/m = {mass_ratio:g}", r2 >= 0.999,
              f"R^2 = {r2:.6f} on ln(v) vs t")
        check(f"D3 no reflection contaminated the fit at M/m = {mass_ratio:g}",
              far < 1e-6 * 0.05, f"far grain speed {far:.2e} m/s")

    # THE FIT WINDOW MUST NOT BE THE ANSWER: vary it and the rate must not move.
    rates = [seam.impactor_decay(400, 100.0 * m, m, B, rho, 0.05, n_efold=e)[0]
             for e in (2.0, 3.0, 4.0)]
    spread = (max(rates) - min(rates)) / float(np.mean(rates))
    check("D3 the measured rate is INSENSITIVE to the fit window (2, 3, 4 e-foldings)",
          spread < 0.02, f"rates {['%.1f' % r for r in rates]}, spread {100 * spread:.2f}%")

    # THE CONTROL: the measurement must be able to reject a wrong Z.
    rate, rate_pred, _, _ = seam.impactor_decay(400, 100.0 * m, m, B, rho, v0=0.05)
    check("D3 CONTROL: the same measurement REJECTS Z/2 and 2Z (it can fail)",
          abs(rate - 0.5 * rate_pred) / (0.5 * rate_pred) > EPS_DYAD
          and abs(rate - 2.0 * rate_pred) / (2.0 * rate_pred) > EPS_DYAD,
          f"measured {rate:.2f} sits {100 * abs(rate - 0.5 * rate_pred) / (0.5 * rate_pred):.0f}% "
          f"from Z/2 and {100 * abs(rate - 2 * rate_pred) / (2 * rate_pred):.0f}% from 2Z")

    # ═══ D3b -- THE TOPOLOGY THE CHAIN CORRECTED (recorded so it cannot come back) ═══════════════
    e_series = seam.restitution_lumped_series(100.0 * m, m, B, rho, v0=0.05)
    check("D3b REFUTED TOPOLOGY pinned: the medium is in SERIES with the contact, not parallel",
          abs(e_series) < 0.2,
          f"series (correct) leaves the impactor at {e_series:+.4f} v0 -- it LANDS; the parallel "
          f"wiring predicted a lively e = 0.859, and the radiating chain (no damping term to "
          f"argue with) said ~0. A wrong topology has the right units and the right constants")
    check("D3b dissipation is now REAL (Stage 9's undamped contact returned exactly 1.0)",
          abs(e_series) < 1.0, "restitution is no longer unity: the body lands instead of bouncing")

    # ═══ D4 -- FRICTION, FROM AN ANGLE THIS WORLD GREW ═══════════════════════════════════════════
    repose = float(gnd["repose_deg"])
    mu = seam.friction_coefficient(repose)
    check("D4 the friction angle is GROWN, not looked up (the granular trainer's own repose)",
          39.0 < repose < 41.0,
          f"repose {repose:.2f} deg -> mu = {mu:.4f} (mu = tan(phi) is the DEFINITION of a "
          f"friction angle -- the derivation is upstream, in how phi was obtained)")
    check("D4 the ceiling on standable ground IS the repose angle",
          abs(seam.max_walkable_slope_deg(mu) - repose) < 1e-9,
          f"max walkable {seam.max_walkable_slope_deg(mu):.2f} deg")

    p95 = float(ter["p95_slope_deg"])
    mean_slope = float(ter["mean_slope_deg"])
    check("D4 PREDICTION: the terrain this world grew is walkable by the repose angle it grew",
          p95 < repose and mean_slope < repose,
          f"aTerrain p95 {p95:.2f} deg and mean {mean_slope:.2f} deg vs repose {repose:.2f} deg "
          f"-- margin {mu / math.tan(math.radians(p95)):.2f}x at the steepest published slope")
    # READ FROM THE MEMBRANE THAT PUBLISHES IT. The first version asked theGround for
    # `slopes_below_repose` and got None -- it is aTerrain's number. Matching names is not
    # matching definitions, and neither is guessing which membrane owns one.
    check("D4 and aTerrain already published that conclusion independently",
          bool(ter.get("slopes_below_repose")) is True,
          "aTerrain's own `slopes_below_repose` = true; two routes, one answer")

    W = float(hum["weight_N"])
    shear_avail = mu * W
    check("D4 a standing body has friction to spare (available shear vs its own weight)",
          shear_avail > 0.5 * W,
          f"{shear_avail:.1f} N available against {W:.1f} N of weight -- a foot on this ground "
          f"does not slide until the surface tilts past {repose:.1f} deg")

    print(f"\n{_PASS} passed, {_FAIL} failed", flush=True)
    return 1 if _FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
