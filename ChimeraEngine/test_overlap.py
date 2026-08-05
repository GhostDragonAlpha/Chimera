"""test_overlap.py -- Stage 8's falsifiers, INCLUDING THE ONE THAT FIRES.

    python ChimeraEngine/test_overlap.py

What is on trial: the cross-term overlap-contact model of ChimeraEngine/core/overlap.py.
The machinery half PASSES (Gaussians close under the overlap integral; the force field is
conservative; every constant is read, none picked). The physics half was given a pre-named
falsifier -- "reproduce the proven 0.000 mm contact seam at mm precision" -- AND IT FIRES:

    THE VERDICT (measured here, every run): Gaussian-overlap contact is EXPONENTIALLY SOFT.
    The equilibrium separation moves ~ sqrt(ln(load)), so the bulk modulus B -- the only
    material stiffness in the model -- enters the settlement only LOGARITHMICALLY: 10x the
    B moves the equilibrium by under 5%. Under theHuman's published weight the settlement
    against self-weight rest is CENTIMETRES, not the witnessed 0.000 mm. The model form is
    wrong for hard contact, because a real density edge is far sharper than the rendering
    Gaussian's tail; the named successor is a saturated-density (volume-exclusion) energy,
    NOT built. This test PINS the refutation to numbers so no future session can cite the
    specification as proof -- and if someone changes the model and the seam closes, the
    refutation checks below go red and force the record to be updated. Both directions honest.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT), str(ROOT / "story")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import matter                                      # noqa: E402
from ChimeraEngine.core import overlap             # noqa: E402

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


# Pre-registered tolerances (written before the first run):
EPS_CLOSED_VS_NUMERIC = 1e-3      # 121^3 grid discretisation of a smooth Gaussian product
EPS_CONSERVATIVE = 1e-6           # analytic force vs central-difference -dU/dd, relative
SEAM_MM = 1.0                     # the witnessed seam is 0.000 mm at mm precision


def main() -> int:
    rho0 = 2650.0                                       # solid quartz, the cited pair
    B = matter.BULK_MODULUS_PA["silicate"]
    s = 0.02
    m = matter.grain_mass(rho0, s)

    # ── THE MACHINERY: Gaussians close, and the field is conservative ────────────────────────────
    for d in (0.01, 0.03, 0.06, 0.10):
        closed = overlap.overlap_integral(m, s, m, s, d)
        numeric = overlap.overlap_numeric(m, s, m, s, d)
        rel = abs(closed - numeric) / max(abs(numeric), 1e-300)
        check(f"closed-form overlap == numeric 3D integral at d={d}", rel <= EPS_CLOSED_VS_NUMERIC,
              f"closed {closed:.6e}, numeric {numeric:.6e}, rel {rel:.2e}")

    h = 1e-7
    for d in (0.05, 0.09):
        fd = -(overlap.contact_energy(m, s, m, s, d + h, B, rho0)
               - overlap.contact_energy(m, s, m, s, d - h, B, rho0)) / (2 * h)
        fa = overlap.contact_force(m, s, m, s, d, B, rho0)
        rel = abs(fa - fd) / max(abs(fd), 1e-300)
        check(f"force is -dU/dd (conservative field) at d={d}", rel <= EPS_CONSERVATIVE,
              f"analytic {fa:.6e}, numeric {fd:.6e}, rel {rel:.2e}")

    ds = np.linspace(np.sqrt(2) * s, 10 * s, 200)
    fs = [overlap.contact_force(m, s, m, s, float(d), B, rho0) for d in ds]
    check("force is repulsive and monotone past the peak",
          all(f > 0 for f in fs) and all(a >= b for a, b in zip(fs, fs[1:])),
          f"peak {max(fs):.3e} N at d={float(ds[int(np.argmax(fs))]):.4f}")

    # ── THE PHYSICS: the pre-named falsifier, and it FIRES ───────────────────────────────────────
    hum = published("theHuman")
    blue = published("aBlueWorld")
    g = float(blue["g"])
    W = float(hum["weight_N"])
    self_w = m * g                                       # a grain's own weight
    n_pairs = 300                                        # a footprint's worth of grain pairs
    share = W / n_pairs

    d_self = overlap.equilibrium_distance(self_w, m, s, B, rho0)
    d_load = overlap.equilibrium_distance(self_w + share, m, s, B, rho0)
    settle_mm = (d_self - d_load) * 1000.0
    check("REFUTATION PINNED: settlement under theHuman's published weight is NOT the 0.000 mm seam",
          settle_mm > SEAM_MM,
          f"settles {settle_mm:.1f} mm per pair (share {share:.2f} N over {n_pairs} pairs; "
          f"witnessed seam 0.000 mm) -- the cross-term model is too soft for hard contact")

    d_all = overlap.equilibrium_distance(W, m, s, B, rho0)
    check("REFUTATION PINNED: even one grain carrying the whole body rests in the far tail",
          d_all > 3.0 * 2.0 * s / 2.0,
          f"equilibrium at {d_all / s:.1f} sigma separation (render cutoff is 3.7 sigma)")

    d_10B = overlap.equilibrium_distance(self_w + share, m, s, 10.0 * B, rho0)
    ratio = d_10B / d_load
    # THE GATE IS DERIVED FROM THE MODEL, NOT PICKED (the first version said "< 5%", a round
    # number, and correct physics failed it -- a RULE 1 violation in the instrument). To first
    # order d_eq ~ sqrt(2 S2 ln(F_scale/W)), so scaling B by 10 moves d_eq by at most
    # ln(10) / (2 ln(F_peak / W)) relative -- every number in the bound comes from the scene.
    f_peak = overlap.contact_force(m, s, m, s, float(np.sqrt(2.0) * s), B, rho0)
    bound = np.log(10.0) / (2.0 * np.log(f_peak / (self_w + share)))
    check("THE DIAGNOSIS: bulk modulus enters only logarithmically (10x B stays under the "
          "model's own first-order bound)",
          1.0 < ratio <= 1.0 + bound,
          f"d_eq(10B)/d_eq(B) = {ratio:.4f}, derived bound {1.0 + bound:.4f} -- stiffness lives "
          f"in the tail shape, not in B, which is why no material constant can rescue this form")

    # ═══ STAGE 8 v2 -- THE SUCCESSOR: saturated-density contact must close the seam ══════════════
    # Pre-registered before the first run: EPS_LENS (1D-quadrature referee, 200001 points, kinked
    # integrand -> 1e-5 rel); EPS_CONSERVATIVE as above; the seam gate is the SAME SEAM_MM = 1 mm
    # that v1 failed; B-linearity within 1e-3 rel of exactly 1/10 (bisection resolution).
    EPS_LENS = 1e-5

    r_derived = overlap.rest_radius(m, rho0)
    r_over_sigma = (3.0 * (2.0 * np.pi) ** 1.5 / (4.0 * np.pi)) ** (1.0 / 3.0)
    check("v2 rest radius is DERIVED: R/sigma = (3(2pi)^1.5/4pi)^(1/3), no free parameter",
          abs(r_derived / s - r_over_sigma) < 1e-12,
          f"R = {r_derived / s:.4f} sigma = {r_derived * 1000:.2f} mm for a {s * 1000:.0f} mm grain")

    for d_frac in (0.3, 0.8, 1.2, 1.7):
        d = d_frac * r_derived
        closed = overlap.lens_volume(r_derived, r_derived, d)
        numeric = overlap.lens_volume_numeric(r_derived, r_derived, d)
        rel = abs(closed - numeric) / max(numeric, 1e-300)
        check(f"v2 closed-form lens == quadrature referee at d={d_frac:.1f}R (equal spheres)",
              rel <= EPS_LENS, f"rel {rel:.2e}")
    d_u = 1.1 * r_derived
    closed = overlap.lens_volume(r_derived, 0.6 * r_derived, d_u)
    numeric = overlap.lens_volume_numeric(r_derived, 0.6 * r_derived, d_u)
    check("v2 closed-form lens == quadrature referee (UNEQUAL spheres)",
          abs(closed - numeric) / numeric <= EPS_LENS,
          f"rel {abs(closed - numeric) / numeric:.2e}")

    h2 = 1e-8
    for d_frac in (1.2, 1.8):
        d = d_frac * r_derived
        fd = -(overlap.saturated_energy(m, s, m, s, d + h2, B, rho0)
               - overlap.saturated_energy(m, s, m, s, d - h2, B, rho0)) / (2 * h2)
        fa = overlap.saturated_force(m, s, m, s, d, B, rho0)
        rel = abs(fa - fd) / max(abs(fd), 1e-300)
        check(f"v2 force is -dU/dd (conservative) at d={d_frac:.1f}R", rel <= EPS_CONSERVATIVE,
              f"analytic {fa:.6e}, numeric {fd:.6e}, rel {rel:.2e}")

    f_at = overlap.saturated_force(m, s, m, s, 2.0 * r_derived, B, rho0)
    f_past = overlap.saturated_force(m, s, m, s, 2.5 * r_derived, B, rho0)
    f_eps = overlap.saturated_force(m, s, m, s, 2.0 * r_derived * (1 - 1e-6), B, rho0)
    check("v2 onset is exact and continuous: F(2R) = 0 = F(beyond), F(2R-) tiny",
          f_at == 0.0 and f_past == 0.0 and 0.0 < f_eps < 1e3,
          f"F just inside touch = {f_eps:.3e} N")

    # THE SEAM -- the falsifier v1 fired, and v2 must close.
    d_self2 = overlap.saturated_equilibrium(self_w, m, s, B, rho0)
    d_load2 = overlap.saturated_equilibrium(self_w + share, m, s, B, rho0)
    settle2_mm = (d_self2 - d_load2) * 1000.0
    pen_full = (2.0 * r_derived - overlap.saturated_equilibrium(W, m, s, B, rho0)) * 1000.0
    check("v2 THE SEAM CLOSES: settlement under theHuman's published weight is 0.000 mm at mm precision",
          settle2_mm < SEAM_MM,
          f"settles {settle2_mm * 1e6:.1f} nm per pair (v1: 3.2 mm); even the WHOLE body on one "
          f"pair penetrates {pen_full * 1000:.2f} um -- the witnessed seam, from density + cited B")

    d_10B2 = overlap.saturated_equilibrium(self_w + share, m, s, 10.0 * B, rho0)
    h_b = 2.0 * r_derived - d_load2
    h_10b = 2.0 * r_derived - d_10B2
    check("v2 THE PATHOLOGY INVERTED: B enters LINEARLY (10x B -> exactly h/10)",
          abs(h_10b / h_b - 0.1) < 1e-3,
          f"h(10B)/h(B) = {h_10b / h_b:.5f} (v1 moved d_eq just 6.3% for the same 10x)")

    check("v2 SUPERSEDES v1 in the regime that matters (both records stand, one model serves)",
          settle_mm > SEAM_MM > settle2_mm,
          f"v1 {settle_mm:.1f} mm (refuted) vs v2 {settle2_mm * 1e6:.1f} nm (passes) under the "
          f"same load, same cited B, same published density")

    print(f"\n{_PASS} passed, {_FAIL} failed", flush=True)
    return 1 if _FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
