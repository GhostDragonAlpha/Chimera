"""test_hertz.py -- Stage 11: the contact law that vanishes at zero load, and the tangential half.

    python ChimeraEngine/test_hertz.py

THE FLAGSHIP (H4). Because Hertzian stiffness rises with the load it carries, the speed of sound
in a granular pack must scale as P^(1/6) -- a textbook result of granular physics that nothing
here was fitted to. It is measured with Stage 9's ALREADY-VALIDATED threshold-free mode
instrument, so what is on trial is the contact law and not the measurement. The linear law is run
through the identical instrument as a CONTROL and must return exponent 0, because its stiffness
does not know what load it is carrying. A test that cannot come out two ways proves nothing.

THE IDENTITY (H2). k_t/k_n = 2(1-nu)/(2-nu) -- every modulus cancels and only Poisson's ratio
survives. Checked against the full Mindlin/Hertz expressions rather than trusted.

WHAT THIS CLOSES (H5). Stage 9 recorded E_eff = 31.1 GPa under a foot as the linear law's honest
tell, and claimed the elastic-vs-plastic finding "survives softening by 1000x". Hertz now supplies
the REAL softening factor, so that bracket stops being hypothetical.
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
from ChimeraEngine.core import hertz, seam             # noqa: E402

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
EPS_IDENTITY = 1e-12       # two closed forms of one number
EPS_ROUNDTRIP = 1e-9       # invert Hertz and come back
EPS_EXPONENT = 0.02        # measured log-log slope vs the derived 1/6
EPS_MODE = 0.02            # measured mode speed vs its own closed form
EPS_ANGLE = 1e-6           # tilt-table release vs atan(mu), in degrees


def main() -> int:
    gnd = published("theGround")
    ter = published("aTerrain")
    hum = published("theHuman")
    blue = published("aBlueWorld")

    # ═══ H1 -- TWO CITED MODULI, EVERYTHING ELSE DERIVED ═════════════════════════════════════════
    B, G, E, nu = hertz.elastic_constants("silicate")
    check("H1 E and nu are DERIVED from the two cited moduli (B, G)",
          abs(E - 9 * B * G / (3 * B + G)) < 1e-6 and 0.0 < nu < 0.5,
          f"B = {B/1e9:.1f} GPa, G = {G/1e9:.1f} GPa -> E = {E/1e9:.1f} GPa, nu = {nu:.4f} "
          f"(alpha-quartz's Poisson ratio is unusually low, and this is it)")
    try:
        hertz.elastic_constants("water")
        refused = False
    except KeyError as e:
        refused = "shear modulus" in str(e)
    check("H1 SCOPE REFUSAL: a fluid has no shear modulus, so Hertz refuses water",
          refused, "no number is substituted -- a missing constant is a boundary, not a gap")

    e_star = hertz.contact_modulus(E, nu)
    g_star = hertz.shear_contact_modulus(G, nu)

    # ═══ H2 -- THE IDENTITY EVERY MODULUS CANCELS OUT OF ═════════════════════════════════════════
    r_g = float(gnd["d_median_mm"]) / 2000.0
    re = hertz.r_eff(r_g)
    h_probe = 1e-9
    ratio_full = (float(hertz.tangential_stiffness(h_probe, re, g_star))
                  / float(hertz.hertz_stiffness(h_probe, re, e_star)))
    check("H2 k_t/k_n IS 2(1-nu)/(2-nu) -- moduli cancel, only Poisson's ratio survives",
          abs(ratio_full - hertz.stiffness_ratio(nu)) / hertz.stiffness_ratio(nu) <= EPS_IDENTITY,
          f"{ratio_full:.6f} by the full expressions, {hertz.stiffness_ratio(nu):.6f} by the "
          f"closed form")
    check("H2 the ratio is independent of penetration (both stiffnesses share a(h))",
          abs(float(hertz.tangential_stiffness(1e-5, re, g_star))
              / float(hertz.hertz_stiffness(1e-5, re, e_star)) - ratio_full) <= EPS_IDENTITY,
          "so a contact's stick-to-slip character does not drift as it loads")

    # ═══ H3 -- THE DEFECT STAGE 9 NAMED IS FIXED: STIFFNESS VANISHES AT ZERO LOAD ════════════════
    ks = [float(hertz.hertz_stiffness(h, re, e_star)) for h in (0.0, 1e-12, 1e-9, 1e-6)]
    check("H3 THE FIX: Hertzian stiffness vanishes at zero penetration (linear law's did not)",
          ks[0] == 0.0 and ks[1] < ks[2] < ks[3],
          f"k_n(0) = 0 exactly, then {ks[1]:.3e} -> {ks[2]:.3e} -> {ks[3]:.3e} N/m; "
          f"the linear law held pi*B*R/2 = {math.pi*3.7e10*r_g/2:.3e} N/m all the way to h = 0")
    f_t = 1e-3
    h_t = hertz.penetration_for_force(f_t, re, e_star)
    check("H3 force <-> penetration round-trips",
          abs(float(hertz.hertz_force(h_t, re, e_star)) - f_t) / f_t <= EPS_ROUNDTRIP,
          f"{f_t} N -> h = {h_t*1e9:.2f} nm -> {float(hertz.hertz_force(h_t, re, e_star)):.6e} N")
    h_fine = np.linspace(1e-9, 1e-6, 20001)
    work = float(np.trapezoid(hertz.hertz_stiffness(h_fine, re, e_star), h_fine))
    df = float(hertz.hertz_force(h_fine[-1], re, e_star) - hertz.hertz_force(h_fine[0], re, e_star))
    check("H3 k_n really is dF/dh (integrating the stiffness returns the force)",
          abs(work - df) / df < 1e-6, f"integral {work:.6e} N vs delta-F {df:.6e} N")

    # ═══ H4 -- THE FLAGSHIP: c ~ P^(1/6) EMERGES, AND THE LINEAR CONTROL SAYS 0 ══════════════════
    rho_s = 2650.0
    m_g = matter.grain_mass(rho_s, r_g / 1.5550)        # a packet whose rest radius is r_g
    forces, speeds = [], []
    for h0 in (2e-9, 6e-9, 2e-8, 6e-8, 2e-7):
        c_meas, c_pred, f0 = hertz.measure_mode_speed_hertz(61, m_g, r_g, e_star, h0)
        check(f"H4 the Hertz chain's mode matches its own closed form at h0 = {h0*1e9:.0f} nm",
              abs(c_meas - c_pred) / c_pred <= EPS_MODE,
              f"measured {c_meas:.1f} m/s vs derived {c_pred:.1f} m/s, contact force {f0:.3e} N")
        forces.append(f0)
        speeds.append(c_meas)
    slope, _ = np.polyfit(np.log(forces), np.log(speeds), 1)
    check("H4 FLAGSHIP: granular sound speed scales as F^(1/6) -- the textbook exponent EMERGES",
          abs(slope - 1.0 / 6.0) <= EPS_EXPONENT,
          f"measured exponent {slope:.4f} vs derived 1/6 = {1/6:.4f} over a 100x force range "
          f"({min(speeds):.0f} -> {max(speeds):.0f} m/s); nothing here was fitted to it")

    lin_speeds = []
    for frac in (1e-4, 1e-3, 1e-2):
        c_lin, _, _ = seam.measure_mode_speed(61, m_g, B, rho_s, precompress_frac=frac)
        lin_speeds.append(c_lin)
    lin_spread = (max(lin_speeds) - min(lin_speeds)) / float(np.mean(lin_speeds))
    check("H4 CONTROL: the LINEAR law gives exponent ~0 through the same instrument",
          lin_spread < 0.02,
          f"speeds {['%.0f' % s for s in lin_speeds]} m/s over a 100x pre-compression range "
          f"(spread {100*lin_spread:.2f}%) -- pressure-independent, which is the defect Hertz "
          f"fixes and the proof this test can come out two ways")

    # ═══ H5 -- CLOSING STAGE 9's HYPOTHETICAL BRACKET WITH THE REAL NUMBER ═══════════════════════
    por = float(gnd["porosity"])
    p_foot = float(hum["foot_pressure_kPa"]) * 1000.0
    width = math.sqrt(float(hum["foot_area_m2"]))
    n_area = seam.grain_areal_density(por, r_g)
    e_lin = seam.column_modulus(B, por, r_g)
    e_hz = hertz.column_modulus_hertz(p_foot, n_area, r_g, e_star)
    check("H5 Hertz softens the pack at light load, as Stage 9 predicted it would",
          e_hz < e_lin / 10.0,
          f"E_eff: linear {e_lin/1e9:.1f} GPa -> Hertz {e_hz/1e6:.0f} MPa "
          f"({e_lin/e_hz:.0f}x softer, and a real soil small-strain modulus is tens of MPa)")
    settle_hz = p_foot / e_hz * width
    depth_pub = float(hum["footprint_depth_mm"]) / 1000.0
    check("H5 Stage 9's 'survives 1000x softening' bracket was HONEST (real factor is inside it)",
          e_lin / e_hz < 1000.0 and depth_pub / settle_hz > 10.0,
          f"real softening {e_lin/e_hz:.0f}x (< the 1000x tested); settlement {settle_hz*1e6:.1f} um "
          f"still {depth_pub/settle_hz:.0f}x under theHuman's published {depth_pub*1000:.3f} mm "
          f"footprint -- elastic and plastic stay separate mechanisms")

    # ═══ H6 -- THE TANGENTIAL FORCE, AND THE TILT TABLE ══════════════════════════════════════════
    repose = float(gnd["repose_deg"])
    mu = seam.friction_coefficient(repose)
    g_here = float(blue["g"])
    m_body = float(hum["mass_kg"])
    released = hertz.tilt_table(mu, m_body, g_here, re, g_star, e_star)
    check("H6 THE SIMULATED TILT TABLE returns the angle the granular trainer GREW",
          abs(released - repose) <= EPS_ANGLE,
          f"the contact lets go at {released:.6f} deg; theGround's grown repose is {repose:.6f} "
          f"deg -- a tilting experiment and a pile-building experiment, one number")

    # THE LOAD IS SHARED, and using the whole body weight on ONE grain would be a fiction that
    # inflates every contact-scale number (it reported a 56 um pre-slip; the real one is nanometres).
    # Stage 9 counted the contacts from published numbers -- use that count.
    n_contacts = seam.grain_areal_density(por, r_g) * float(hum["foot_area_m2"])
    th = math.radians(float(ter["p95_slope_deg"]))
    fn = m_body * g_here * math.cos(th) / n_contacts
    drive = m_body * g_here * math.sin(th) / n_contacts
    h = hertz.penetration_for_force(fn, re, e_star)
    kt = float(hertz.tangential_stiffness(h, re, g_star))
    ft, sliding, preslip = hertz.tangential_response(h, drive / kt, mu, re, g_star, e_star)
    check("H6 a body HOLDS on the steepest slope this world published",
          not sliding and abs(ft - drive) / drive < 1e-9,
          f"at aTerrain's p95 {math.degrees(th):.2f} deg each of {n_contacts:,.0f} contacts "
          f"carries its {drive*1e3:.3f} mN share without slipping")
    check("H6 pre-slip displacement is a real nanometre-scale quantity, not a smoothing",
          0.0 < preslip < 1e-6,
          f"the contact deforms {preslip*1e9:.1f} nm tangentially before it lets go -- "
          f"tribology's pre-sliding displacement, and it falls out of Mindlin + Coulomb")

    ft_s, sliding_s, _ = hertz.tangential_response(h, 100.0 * preslip, mu, re, g_star, e_star)
    check("H6 past the ceiling it SLIDES at exactly mu*F_n and no more",
          sliding_s and abs(abs(ft_s) - mu * fn) / (mu * fn) < 1e-9,
          f"F_t caps at {abs(ft_s)*1e3:.3f} mN = mu*F_n; the spring cannot hold more")
    d_slide = 0.01
    fn_foot = m_body * g_here * math.cos(th)
    check("H6 sliding dissipates mu*F_n*d (the ceiling doing work)",
          abs(hertz.slide_dissipation(mu, fn_foot, d_slide) - mu * fn_foot * d_slide) < 1e-12,
          f"a whole foot skidding {d_slide*100:.0f} cm turns {hertz.slide_dissipation(mu, fn_foot, d_slide):.2f} J "
          f"into heat -- the first genuinely IRREVERSIBLE process in this contact model")

    print(f"\n{_PASS} passed, {_FAIL} failed", flush=True)
    return 1 if _FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
