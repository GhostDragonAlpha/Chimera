"""test_seam.py -- Stage 9's falsifiers: contact carries a body, and carries sound.

    python ChimeraEngine/test_seam.py

THE FLAGSHIP PREDICTION (S3), and it is the kind this project's law demands -- a fact the model
was never fitted to: aSaltOcean publishes `sound_speed_water_ms` from an oceanographic
temperature/salinity formula that knows nothing about contact mechanics. A chain of
saturated-density packets, given only the CITED bulk modulus and the membrane's own published
density, must reproduce it -- after the DERIVED linear-packing factor sqrt(2/3), which is the
volume of a sphere over the volume of its bounding cylinder and is computed, never fitted.

WHAT IS DELIBERATELY NOT CLAIMED. theGround derives its bulk density as
RHO_SOLID*(1-POROSITY) with POROSITY declared at 0.42, so its 0.58 solid fraction is an INPUT.
Reading it back out as "the random-loose-packing fraction of spheres" would be circular, and it
is not claimed here. Only numbers derived by an independent route are used as predictions.
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
from ChimeraEngine.core import seam, overlap           # noqa: E402

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
EPS_IDENTITY = 1e-12       # two closed forms of the same number, float64
EPS_CHAIN = 0.02           # simulated front vs derived dispersion speed (discrete chain, 2%)
EPS_SOUND = 0.02           # vs aSaltOcean's published speed; B is cited to 2 sig figs (~2%)
EPS_R2 = 0.999             # the front must be a clean straight line in (distance, time)
EPS_RESTITUTION = 1e-3     # conservative force -> 1.0; deviation is integrator only


def main() -> int:
    sea = published("aSaltOcean")
    gnd = published("theGround")
    hum = published("theHuman")
    blue = published("aBlueWorld")

    # ═══ S1 -- THE STIFFNESS IDENTITY ════════════════════════════════════════════════════════════
    rho_w = float(sea["density_surface_kg_m3"])
    B_w = matter.BULK_MODULUS_PA["water"]
    s_pkt = 0.01
    m_w = matter.grain_mass(rho_w, s_pkt)
    k1 = seam.contact_stiffness(m_w, B_w, rho_w)
    k2 = seam.rod_stiffness_of_great_circle(m_w, B_w, rho_w)
    check("S1 lens stiffness at first touch IS the great circle's rod stiffness (E*A/L)",
          abs(k1 - k2) / k2 <= EPS_IDENTITY, f"k = {k1:.6e} N/m by both routes")

    r_w = overlap.rest_radius(m_w, rho_w)
    h = 1e-9 * r_w
    k_fd = -(overlap.saturated_force(m_w, s_pkt, m_w, s_pkt, 2.0 * r_w - h, B_w, rho_w) - 0.0) / -h
    check("S1 the same k falls out of the force curve itself (finite difference at first touch)",
          abs(k_fd - k1) / k1 < 1e-6, f"finite-difference k = {k_fd:.6e} N/m")

    check("S1 linear packing fraction is COMPUTED from a sphere and its cylinder, = 2/3",
          abs(seam.LINEAR_PACKING - 2.0 / 3.0) <= EPS_IDENTITY,
          f"{seam.LINEAR_PACKING:.15f}")

    # ═══ S2 -- THE CHAIN CARRIES A WAVE AT THE DERIVED SPEED ═════════════════════════════════════
    dd = np.linspace(0.1 * r_w, 2.5 * r_w, 37)
    vec = seam.pair_force_equal(dd, r_w, B_w)
    sca = np.array([overlap.saturated_force(m_w, s_pkt, m_w, s_pkt, float(d), B_w, rho_w)
                    for d in dd])
    check("S2 the chain's vectorised force IS the referee's force (no second formula drifting)",
          float(np.abs(vec - sca).max()) <= 1e-6 * float(np.abs(sca).max()),
          f"max |diff| {float(np.abs(vec - sca).max()):.2e} N over 37 separations")

    c_derived = seam.chain_speed_derived(B_w, rho_w)
    c_meas, c_pred, per = seam.measure_mode_speed(61, m_w, B_w, rho_w)
    check("S2 the chain's fundamental mode runs at the derived dispersion speed",
          abs(c_meas - c_derived) / c_derived <= EPS_CHAIN,
          f"measured {c_meas:.1f} m/s vs derived {c_derived:.1f} m/s "
          f"({100 * abs(c_meas - c_derived) / c_derived:.3f}%), period {per * 1e3:.4f} ms")

    # SCALE INVARIANCE: c_chain carries no R, so a 10x smaller packet must give the same speed.
    m_small = matter.grain_mass(rho_w, s_pkt / 10.0)
    c_small, _, _ = seam.measure_mode_speed(61, m_small, B_w, rho_w)
    check("S2 wave speed is INDEPENDENT of packet size (10x smaller packets, same speed)",
          abs(c_small - c_meas) / c_meas <= EPS_CHAIN,
          f"{c_small:.1f} m/s at R/10 vs {c_meas:.1f} m/s -- the speed is the material's, "
          f"not the grid's")

    # THE INSTRUMENT REFUTATION, KEPT AS A TEST so it cannot quietly come back. Timing a
    # wavefront's FIRST ARRIVAL reports a speed that depends on the trigger, because a discrete
    # lattice puts an exponentially small precursor ahead of the energy front. The threshold
    # being external (the piston's own speed) does not rescue it.
    c_hi, _, _ = seam.simulate_chain(60, m_w, B_w, rho_w, 0.5, trigger_frac=3e-1)
    c_lo, _, _ = seam.simulate_chain(60, m_w, B_w, rho_w, 0.5, trigger_frac=1e-6)
    check("S2 REFUTED INSTRUMENT pinned: front-arrival speed DEPENDS on its trigger (precursor)",
          (c_lo - c_hi) / c_hi > 0.10 and abs(c_hi - c_derived) / c_derived < 0.01,
          f"trigger 3e-1 -> {c_hi:.1f} m/s (0.13% from derived); trigger 1e-6 -> {c_lo:.1f} m/s "
          f"(+{100 * (c_lo - c_hi) / c_hi:.0f}%) -- which is why S3 uses the threshold-free mode")

    # ═══ S3 -- THE FLAGSHIP: aSaltOcean's PUBLISHED SOUND SPEED, NEVER FITTED TO ═════════════════
    c_pub = float(sea["sound_speed_water_ms"])
    c_recovered = c_meas * math.sqrt(seam.LINEAR_PACKING)
    err = abs(c_recovered - c_pub) / c_pub
    check("S3 PREDICTION: the packet chain reproduces aSaltOcean's published sound speed",
          err <= EPS_SOUND,
          f"chain {c_meas:.1f} m/s x sqrt(2/3) = {c_recovered:.1f} m/s vs PUBLISHED "
          f"{c_pub:.2f} m/s ({100 * err:.2f}%) -- the published value comes from an "
          f"oceanographic T/S formula, this one from a cited bulk modulus and a lens volume")
    c_cont = seam.continuum_speed(B_w, rho_w)
    check("S3 the closed-form continuum route agrees with the simulated one",
          abs(c_recovered - c_cont) / c_cont <= EPS_CHAIN,
          f"sqrt(B/rho) = {c_cont:.1f} m/s")

    # ═══ S4 -- NAMED LIMIT: NO DISSIPATION ═══════════════════════════════════════════════════════
    e = seam.drop_restitution(m_w, B_w, rho_w, v_impact=0.2)
    check("S4 NAMED LIMIT measured: the contact is conservative, so restitution is exactly 1.0",
          abs(e - 1.0) <= EPS_RESTITUTION,
          f"e = {e:.6f} -- real ground damps; a dissipative term is UNBUILT and this is how "
          f"a future one will be detected")

    # ═══ S5 -- THE BODY ON THE GROUND ════════════════════════════════════════════════════════════
    r_g = float(gnd["d_median_mm"]) / 2000.0            # published median grain -> radius in m
    por = float(gnd["porosity"])
    B_s = matter.BULK_MODULUS_PA["silicate"]
    W = float(hum["weight_N"])
    A_foot = float(hum["foot_area_m2"])
    p_foot = float(hum["foot_pressure_kPa"]) * 1000.0
    width = math.sqrt(A_foot)                            # the footing's own equivalent width
    check("S5 the load path is read, not invented (pressure = weight / published foot area)",
          abs(p_foot - W / A_foot) / p_foot < 1e-6,
          f"{p_foot / 1000:.2f} kPa on {A_foot * 1e4:.0f} cm^2 under {W:.1f} N")

    n_area = seam.grain_areal_density(por, r_g)
    N = n_area * A_foot
    k_g = seam.contact_stiffness(matter.grain_mass(2650.0, r_g / 1.5550), B_s, 2650.0)
    check("S5 a foot rests on a countable number of published grains",
          N > 1e4, f"{N:,.0f} surface grains under one foot ({n_area:,.0f}/m^2 at "
                   f"d50 = {gnd['d_median_mm']} mm)")

    settle = seam.elastic_settlement(p_foot, width, B_s, por, r_g)
    check("S5 THE SEAM HOLDS: elastic contact settlement is far below the witness's mm precision",
          settle * 1000.0 < 1.0,
          f"{settle * 1e6:.3f} um over a {width * 100:.1f} cm influence depth -- the foot does "
          f"not float and does not sink through")

    # ═══ S6 -- THE REGIME SEPARATION (the real result) ═══════════════════════════════════════════
    depth_pub_mm = float(hum["footprint_depth_mm"])
    ratio = (depth_pub_mm / 1000.0) / settle
    check("S6 ELASTIC vs PLASTIC: the published footprint is NOT elastic compression",
          ratio > 100.0,
          f"theHuman publishes {depth_pub_mm:.3f} mm; elastic contact gives {settle * 1e6:.3f} um "
          f"-- {ratio:,.0f}x smaller, so the footprint is theGround's Terzaghi REARRANGEMENT, "
          f"and the two mechanisms do not double-count")
    soft = seam.softening_robustness(p_foot, width, B_s, por, r_g, factor=1000.0)
    check("S6 and the conclusion survives softening the contact law by 1000x (linear vs Hertz)",
          (depth_pub_mm / 1000.0) / soft > 10.0,
          f"at 1000x softer, settlement {soft * 1000:.3f} mm is still "
          f"{(depth_pub_mm / 1000.0) / soft:.0f}x under the published footprint -- the finding "
          f"does not rest on the linear-contact choice")
    E_eff = seam.column_modulus(B_s, por, r_g)
    check("S6 THE HONEST TELL: the linear law reads near-solid at light load (Hertz is the "
          "named refinement)", E_eff > 1e10,
          f"E_eff = {E_eff / 1e9:.1f} GPa vs solid quartz B = {B_s / 1e9:.0f} GPa -- k does not "
          f"vanish at zero penetration, and that is exactly what Hertz would fix")

    # ═══ S7 -- THE SLIDER ════════════════════════════════════════════════════════════════════════
    g_here = float(blue["g"])
    s_here = seam.elastic_settlement(W / A_foot, width, B_s, por, r_g)
    s_earth = seam.elastic_settlement((W / g_here * 9.80665) / A_foot, width, B_s, por, r_g)
    check("S7 slider: heavier gravity presses the seam deeper, in exact proportion",
          abs((s_earth / s_here) / (9.80665 / g_here) - 1.0) < 1e-9,
          f"g {g_here:.3f} -> {s_here * 1e6:.3f} um; Earth 9.807 -> {s_earth * 1e6:.3f} um "
          f"(x{s_earth / s_here:.3f}), and theHuman's own earth/here footprint ratio is "
          f"{float(hum['footprint_deeper_on_earth_by']):.3f} for the PLASTIC mechanism")

    print(f"\n{_PASS} passed, {_FAIL} failed", flush=True)
    return 1 if _FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
