"""matter_derive — THE LIVING MATTER Phase 2: the 5x5 J, DERIVED, not fitted.

The membrane is docs/THE_LIVING_MATTER.md "Phase 2 — THE DERIVATION" (stated before
the run). What this module is:

  THE MEASUREMENTS. Tissue surface tensions from Foty, Pfleger, Forgacs & Steinberg
  1996 (Development 122:1611-1620, parallel-plate compression, chick embryo):
      limb bud mesoderm 20.1 | retinal pigmented epithelium 12.6 | heart 8.5 |
      liver 4.6 | neural retina 1.6          [dyne/cm = mN/m]
  and the adhesion-independent cortical floor 0.32 mN/m from Foty & Steinberg 2005
  (Dev. Biol. 278:255 — tension linear in cadherin, R^2=0.9965, intercept at zero
  cadherin). Tissue-tissue INTERFACIAL tensions are not systematically measured
  (Pajic-Lijakovic et al. 2023) — a named gap carried by the Girifalco-Good default.

  THE TYPE MAPPING (an assumption; F2 judges it):
      BONE <- limb bud mesoderm 20.1 (deepest tissue, both hierarchies)
      MUSCLE <- heart 8.5            (heart IS muscle)
      SKIN <- neural retina 1.6      (the universal enveloper, lowest measured)
      TENDON <- pigmented epithelium 12.6 (second-deepest, rung-1's tendon slot)

  THE SCALE (the ONE kinetic freedom; F3 guards it):
      kT_eff = sigma_cortex * ell^2     (fluctuation energy over one contact area)
      E0 = kT_eff / temp                (one constant serves alpha and temp)
      alpha = ell^2 / E0                (J = alpha * gamma_phys + J_sym)

  THE MATRIX. J(a,a) = alpha*sigma_a ; J(a,MED) = alpha*sigma_a + J(a,a)/2 ;
  J(a,b) = alpha*(sqrt(sigma_a)-sqrt(sigma_b))^2 + (J(a,a)+J(b,b))/2.

__main__ runs THE CONTROL: the rung-1 scramble under the derived J against the
uniform contrast (F1), and the energy traces of derived vs rung-1 J for tau_sort
(F3). F2 is analytic and printed. Numbers are computed here, never hand-copied.
"""

from __future__ import annotations

import math

import numpy as np

from core.matter import MEDIUM, BONE, MUSCLE, SKIN, TENDON, NAMES, J_PROVEN_DIFFERENTIAL

# THE MEASUREMENTS (Foty et al. 1996), mN/m = dyne/cm.
SIGMA_MN_M = {
    "bone": 20.1,     # limb bud mesoderm
    "tendon": 12.6,   # retinal pigmented epithelium
    "muscle": 8.5,    # heart
    "skin": 1.6,      # neural retina
}
SIGMA_CORTEX_MN_M = 0.32   # Foty & Steinberg 2005: zero-cadherin intercept
ELL_M = 10e-6              # one lattice site = one cell
TEMP = 12.0                # the rung-1 protocol's temperature; E0 derives FROM it

# THE TWO ANCHORS for kT_eff (the ONE kinetic freedom; THE_LIVING_MATTER Phase 2/2b):
#   cortex    — Phase 2: the PASSIVE floor (Foty & Steinberg 2005 intercept).
#               F3 FIRED on it: structure yes, kinetics no (tau ratio 0.07).
#   liquidity — Phase 2b: kT_eff = sigma_geo*ell^2, the geometric mean of the four
#               measured tensions (7.66 mN/m): a liquid is liquid because its
#               fluctuation energy per contact ~ its bond energy per contact.
SIGMA_GEO_MN_M = float(np.prod(list({
    "bone": 20.1, "tendon": 12.6, "muscle": 8.5, "skin": 1.6}.values())) ** 0.25)
_ANCHOR_SIGMA = {"cortex": SIGMA_CORTEX_MN_M, "liquidity": SIGMA_GEO_MN_M}

_TYPE_INDEX = {"bone": BONE, "muscle": MUSCLE, "skin": SKIN, "tendon": TENDON}


def alpha(temp: float = TEMP, anchor: str = "cortex") -> float:
    """The lattice constant, J^-1 m^2: kT_eff = sigma_anchor*ell^2 ; E0 = kT_eff/temp."""
    kT_eff = _ANCHOR_SIGMA[anchor] * 1e-3 * ELL_M**2  # J, the fluctuation energy
    E0 = kT_eff / temp                                # J, the model energy unit
    return ELL_M**2 / E0                              # J^-1 m^2


def derive_J(temp: float = TEMP, anchor: str = "cortex") -> np.ndarray:
    """The derived 5x5 J (MEDIUM/BONE/MUSCLE/SKIN/TENDON), in lattice units."""
    a = alpha(temp, anchor)
    J = np.zeros((5, 5), dtype=np.float64)
    tissues = list(SIGMA_MN_M)
    for t in tissues:
        i = _TYPE_INDEX[t]
        J[i, i] = a * SIGMA_MN_M[t] * 1e-3                     # self-cohesion
        J[i, MEDIUM] = J[MEDIUM, i] = 1.5 * a * SIGMA_MN_M[t] * 1e-3
    for p, t1 in enumerate(tissues):
        for t2 in tissues[p + 1:]:
            i, j = _TYPE_INDEX[t1], _TYPE_INDEX[t2]
            g_ab = (math.sqrt(SIGMA_MN_M[t1]) - math.sqrt(SIGMA_MN_M[t2]))**2
            J[i, j] = J[j, i] = a * g_ab * 1e-3 + 0.5 * (J[i, i] + J[j, j])
    return J


def gamma_cpm(J: np.ndarray) -> np.ndarray:
    """Exact CPM algebra: gamma(a,b) = J(a,b) - (J(a,a)+J(b,b))/2."""
    d = np.diag(J)
    return J - 0.5 * (d[:, None] + d[None, :])


def tau_sort(sw: np.ndarray) -> float:
    """Sweeps for the per-sweep mean H to fall (1 - 1/e) of the total drop,
    the drop measured from sweep 0 to the last-10% plateau mean."""
    plateau = float(sw[-max(1, len(sw) // 10):].mean())
    drop = float(sw[0] - plateau)
    if drop <= 0:
        return float("nan")
    thresh = float(sw[0]) - (1.0 - 1.0 / math.e) * drop
    hits = np.nonzero(sw <= thresh)[0]
    return float(hits[0] + 1) if len(hits) else float("nan")


def _scramble(n: int = 96, seed: int = 0):
    """The rung-1 scramble, identical to matter_gpu.__main__ (same rng stream)."""
    shape = (n, n, n)
    rng = np.random.RandomState(seed)
    grid = np.zeros(shape, dtype=np.int16)
    c, r = n // 2, n // 3
    zz, yy, xx = np.mgrid[0:n, 0:n, 0:n]
    blob = (zz - c) ** 2 + (yy - c) ** 2 + (xx - c) ** 2 < r * r
    picks = rng.choice((BONE, MUSCLE, SKIN), size=int(blob.sum()))
    grid[blob] = picks
    targets = {t: int((grid == t).sum()) for t in (BONE, MUSCLE, SKIN)}
    return grid, shape, targets


if __name__ == "__main__":
    import argparse
    from core.matter_gpu import open_lattice, step, close, parity_report

    ap = argparse.ArgumentParser(description="THE LIVING MATTER Phase 2/2b control run")
    ap.add_argument("--n", type=int, default=96)
    ap.add_argument("--sweeps", type=int, default=200)
    ap.add_argument("--anchor", choices=sorted(_ANCHOR_SIGMA), default="liquidity",
                    help="kT_eff anchor: cortex (Phase 2, F3 fired) or liquidity (Phase 2b)")
    a_ns = ap.parse_args()

    J5 = derive_J(anchor=a_ns.anchor)
    J4 = J5[np.ix_([MEDIUM, BONE, MUSCLE, SKIN], [MEDIUM, BONE, MUSCLE, SKIN])]

    print("THE DERIVED J [%s anchor] (lattice units; alpha = %.4e J^-1 m^2 = %.3f per mN/m)"
          % (a_ns.anchor, alpha(anchor=a_ns.anchor), alpha(anchor=a_ns.anchor) * 1e-3))
    order = [MEDIUM, BONE, MUSCLE, SKIN, TENDON]
    print("           " + "  ".join(f"{NAMES[t]:>8}" for t in order))
    for i in order:
        print(f"  {NAMES[i]:>8} " + "  ".join(f"{J5[i, j]:8.2f}" for j in order))
    g = gamma_cpm(J5)
    print("gamma_CPM vs MEDIUM (lattice units; = %.3f x measured mN/m):"
          % (alpha(anchor=a_ns.anchor) * 1e-3))
    for t in (BONE, TENDON, MUSCLE, SKIN):
        print(f"  {NAMES[t]:>8} {g[t, MEDIUM]:8.2f}   (measured "
              f"{SIGMA_MN_M[NAMES[t]]:5.2f} mN/m)")

    # F2 — analytic, no run: measured ordering must reproduce rung-1's burial order.
    g1 = gamma_cpm(J_PROVEN_DIFFERENTIAL)
    meas_order = sorted(SIGMA_MN_M, key=SIGMA_MN_M.get, reverse=True)
    rung1_order = sorted((BONE, TENDON, MUSCLE, SKIN),
                         key=lambda t: {BONE: g1[BONE, MEDIUM], MUSCLE: g1[MUSCLE, MEDIUM],
                                        SKIN: g1[SKIN, MEDIUM], TENDON: 13.5}[t],
                         reverse=True)
    f2 = [NAMES[t] for t in rung1_order] == meas_order
    print(f"\nF2 (ordering): measured {meas_order} vs rung-1 "
          f"{[NAMES[t] for t in rung1_order]} -> {'PASS' if f2 else 'FAIL'}")

    grid, shape, targets = _scramble(a_ns.n)
    J_unif = np.full_like(J4, 8.0)
    np.fill_diagonal(J_unif, 4.0)
    J_unif[MEDIUM, MEDIUM] = 0.0

    # F1 — the anatomy control: derived J must layer, uniform must not.
    rep = parity_report(grid, shape, targets, J4, J_unif,
                        sweeps=a_ns.sweeps, seed=0)
    d = rep["differential"]
    f1 = d[BONE] < d[MUSCLE] < d[SKIN]
    for label in ("differential", "uniform"):
        r = rep[label]
        print(f"  {label:<13} mean radius  " +
              "  ".join(f"{NAMES[t]}:{r[t]:.1f}" for t in (BONE, MUSCLE, SKIN)))
    print(f"F1 (anatomy, derived sorts bone<muscle<skin): "
          f"{'PASS' if f1 else 'FAIL'}  ({rep['seconds']:.1f}s)")

    # F3 — tau_sort(derived) vs tau_sort(rung-1), same protocol, same instrument.
    taus = {}
    for label, Jx in (("derived", J4), ("rung-1", J_PROVEN_DIFFERENTIAL)):
        h = open_lattice(grid.copy(), shape, targets, Jx, temp=TEMP, lam=0.9, seed=0)
        tr = step(h, 8 * a_ns.sweeps, trace=True)
        close(h)
        sw = tr.reshape(a_ns.sweeps, 8).mean(axis=1)
        taus[label] = tau_sort(sw)
        print(f"  {label:<8} H {sw[0]:.3f} -> {sw[-1]:.3f}, "
              f"tau_sort = {taus[label]:.0f} sweeps")
    ratio = taus["derived"] / taus["rung-1"]
    # F3 is TWO-SIDED (the theory: "differs by more than 2x" — either direction):
    # the scale constant must leave the kinetics within a factor of 2 of rung-1's.
    f3 = 0.5 <= ratio <= 2.0
    print(f"F3 (tau ratio {ratio:.2f} within [0.5, 2]): "
          f"{'PASS' if f3 else 'FAIL — FIRED'}")

    print(f"\nPHASE 2 VERDICT: F1 {'PASS' if f1 else 'FAIL'} | "
          f"F2 {'PASS' if f2 else 'FAIL'} | F3 {'PASS' if f3 else 'FIRED'}")
