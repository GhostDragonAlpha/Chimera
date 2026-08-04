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


# ------------------------------------------------------------------------------------------------
# THE WORLD (Phase 4 first control): sand/rock/medium. Every input researched, in the
# library or cited in docs/THE_LIVING_MATTER.md "Phase 4 (first control)":
#   gamma_sand = c*d = 0.5 kPa x 0.072 mm   (Mitchell 1972 cohesion x Carrier 2003 D50)
#   gamma_rock = K_IC^2/(2E) = (2.4 MPa*m^0.5)^2/(2*78 GPa)   (Griffith; basalt K_IC
#              1.8-3.0 — Whittaker 1992 / Zhang 1998 / Demkowicz 2012; E = Quaglio 2020)
#   ell = one sand grain (the flowing phase sets the lattice constant, as the cell did)
#   scale = the SAME liquidity anchor as Phase 2b (geometric mean), no new freedom.
# ------------------------------------------------------------------------------------------------
WSAND, WROCK, WICE, WMETAL, WBASIN = 1, 2, 3, 4, 5     # world-lattice ids (MEDIUM = 0)
WORLD_NAMES = {MEDIUM: "medium", WSAND: "sand", WROCK: "rock",
               WICE: "ice", WMETAL: "metal", WBASIN: "basin"}
GAMMA_SAND_J_M2 = 0.5e3 * 0.072e-3                    # c·d = 0.036 J/m^2
GAMMA_ROCK_J_M2 = (2.4e6) ** 2 / (2.0 * 78e9)         # K_IC^2/2E = 36.9 J/m^2
ELL_WORLD_M = 0.072e-3                                # one site = one sand grain

# PHASE 4 (full families): the five world materials with measured or Griffith-derived
# surface energies — every number cited in THE_LIVING_MATTER.md "Phase 4 (full
# families)". Metal's 6,094 J/m^2 is a ductile TEARING energy (plastic work included);
# the mapping is told the truth about which number it is eating.
GAMMA_ICE_J_M2 = (115e3) ** 2 / (2.0 * 9e9)           # K_IC 115 kPa*m^0.5 -> 0.735 J/m^2
GAMMA_METAL_J_M2 = (29e6) ** 2 / (2.0 * 69e9)         # K_IC 29 MPa*m^0.5 -> 6094 J/m^2
GAMMA_BASIN_J_M2 = 0.2e3 * 0.028e-3                   # c·d = 0.0056 J/m^2
WORLD_MATS = {WSAND: GAMMA_SAND_J_M2, WROCK: GAMMA_ROCK_J_M2, WICE: GAMMA_ICE_J_M2,
              WMETAL: GAMMA_METAL_J_M2, WBASIN: GAMMA_BASIN_J_M2}


def build_world_J(gammas: dict, temp: float = TEMP) -> np.ndarray:
    """The derived world J (MEDIUM + the given materials), same algebra as the tissue J.
    alpha = temp / sigma_geo (the liquidity anchor makes ell cancel: kT_eff =
    sigma_geo*ell^2, E0 = kT_eff/temp, alpha = ell^2/E0 = temp/sigma_geo — the
    degeneracy THE_LIVING_MATTER names: the lattice reads only gamma/temp)."""
    items = sorted(gammas.items())
    sig_geo = float(np.prod([g for _, g in items])) ** (1.0 / len(items))
    a = temp / sig_geo
    n = max(gammas) + 1
    J = np.zeros((n, n), dtype=np.float64)
    for i, g in items:
        J[i, i] = a * g
        J[i, MEDIUM] = J[MEDIUM, i] = 1.5 * a * g
    for p in range(len(items)):
        for q in range(p + 1, len(items)):
            (i, gi), (j, gj) = items[p], items[q]
            g_ab = (math.sqrt(gi) - math.sqrt(gj)) ** 2        # Girifalco-Good default
            J[i, j] = J[j, i] = a * g_ab + 0.5 * (J[i, i] + J[j, j])
    return J


def derive_world_J(temp: float = TEMP) -> np.ndarray:
    """The derived 3x3 world J (MEDIUM/SAND/ROCK) — the Phase 4 first control, kept
    identical to within one float rounding of the geometric-mean computation
    (measured: max rel. diff ~1e-19 vs the pre-refactor path)."""
    return build_world_J({WSAND: GAMMA_SAND_J_M2, WROCK: GAMMA_ROCK_J_M2}, temp)


def _world_scramble(n: int = 96, seed: int = 0, types: tuple = (WSAND, WROCK)):
    """The rung-1 blob protocol, world materials: the given types scrambled in the
    core third."""
    shape = (n, n, n)
    rng = np.random.RandomState(seed)
    grid = np.zeros(shape, dtype=np.int16)
    c, r = n // 2, n // 3
    zz, yy, xx = np.mgrid[0:n, 0:n, 0:n]
    blob = (zz - c) ** 2 + (yy - c) ** 2 + (xx - c) ** 2 < r * r
    grid[blob] = rng.choice(types, size=int(blob.sum()))
    targets = {t: int((grid == t).sum()) for t in types}
    return grid, shape, targets


def _world_seed_scramble(n: int = 96, seed: int = 0, seed_r: int = 12,
                         seed_off: int = 14):
    """The nucleation protocol (Phase 4 nucleation membrane): TWO compact metal
    seeds (radius seed_r, centred seed_off OFF the z axis — core-position is not
    baked in), the rest of the blob scrambled over the other four materials."""
    shape = (n, n, n)
    rng = np.random.RandomState(seed)
    grid = np.zeros(shape, dtype=np.int16)
    c, r = n // 2, n // 3
    zz, yy, xx = np.mgrid[0:n, 0:n, 0:n]
    blob = (zz - c) ** 2 + (yy - c) ** 2 + (xx - c) ** 2 < r * r
    others = (WROCK, WICE, WSAND, WBASIN)
    grid[blob] = rng.choice(others, size=int(blob.sum()))
    seeds = ((zz - c) ** 2 + (yy - (c - seed_off)) ** 2 + (xx - c) ** 2 < seed_r ** 2) | \
            ((zz - c) ** 2 + (yy - (c + seed_off)) ** 2 + (xx - c) ** 2 < seed_r ** 2)
    grid[seeds] = WMETAL
    targets = {t: int((grid == t).sum()) for t in (WMETAL,) + others}
    return grid, shape, targets


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
    ap.add_argument("--world", action="store_true",
                    help="Phase 4 control: sand/rock/medium instead of the tissue scramble")
    ap.add_argument("--world-full", action="store_true",
                    help="Phase 4 full families: sand/rock/ice/metal/basin scramble, "
                         "derived 6x6 J, radius-ordering verdict")
    ap.add_argument("--world-seed", action="store_true",
                    help="Phase 4 nucleation: compact metal seeds in the 4-material "
                         "scramble — survival and compactness verdict")
    ap.add_argument("--fracture", action="store_true",
                    help="Phase 3: rupture pass on the world scramble, temps {1.2, 12, 120}")
    ap.add_argument("--metal-jail", dest="metal_jail", action="store_true",
                    help="Phase 6: the nucleation protocol with per-type lambda — "
                         "metal jailed at 1.4 (2*1.4*T > drive 37,676), all other "
                         "families at rung-1's 0.9")
    a_ns = ap.parse_args()

    if a_ns.lam_derived:
        from core.matter import metrics_3d
        # PHASE 5: lambda_t = K_t * ell^3 / (2 * T_t * E0). Every input measured or
        # already derived: K_soft = 2.3 GPa (water-like soft tissue), K_bone = 13.9 GPa
        # (cortical, E=17 GPa nu=0.3), E0 = liquidity anchor at temp=12, ell = 10 um.
        K_PA = {BONE: 13.9e9, MUSCLE: 2.3e9, SKIN: 2.3e9, TENDON: 2.3e9}
        E0 = SIGMA_GEO_MN_M * 1e-3 * ELL_M**2 / TEMP          # J, liquidity anchor
        grid, shape, targets = _scramble(a_ns.n)
        lam = {t: K_PA[t] * ELL_M**3 / (2.0 * targets[t] * E0)
               for t in (BONE, MUSCLE, SKIN)}
        print("PHASE 5 — THE LAMBDA MEMBRANE: derived per-tissue lambda "
              + ", ".join(f"{NAMES[t]} {lam[t]:.0f}" for t in (BONE, MUSCLE, SKIN))
              + f"  (E0 = {E0:.3e} J; rung-1's hand value: 0.9)")
        J4 = derive_J(anchor="liquidity")[np.ix_([0, 1, 2, 3], [0, 1, 2, 3])]
        h = open_lattice(grid, shape, targets, J4, temp=TEMP, lam=lam, seed=0)
        tr = step(h, 8 * a_ns.sweeps, trace=True)
        final = close(h)
        sw = tr.reshape(a_ns.sweeps, 8).mean(axis=1)
        r = metrics_3d(final, shape)["radius"]
        drift = {t: int((final == t).sum()) - targets[t] for t in (BONE, MUSCLE, SKIN)}
        sorted_ = r[BONE] < r[MUSCLE] < r[SKIN]
        print(f"  H {sw[0]:.1f} -> {sw[-1]:.1f} (drop {sw[0] - sw[-1]:.1f}), "
              f"tau_sort = {tau_sort(sw):.0f}")
        print(f"  radii: bone {r[BONE]:.1f} muscle {r[MUSCLE]:.1f} skin {r[SKIN]:.1f} "
              f"-> sorted {sorted_}")
        print(f"  count drift: {drift}  (targets frozen = mapping's freeze prediction)")
        print(f"PHASE 5 VERDICT: {'mapping SURVIVES (sorted despite derived lambda)' if sorted_ else 'mapping DEAD — froze, as predicted' if abs(sw[0] - sw[-1]) < 0.01 * sw[0] else 'UNEXPECTED: moved but did not sort — publish'}")
        raise SystemExit(0)

    if a_ns.fracture:
        from core.matter import metrics_3d
        sig_geo = math.sqrt(GAMMA_SAND_J_M2 * GAMMA_ROCK_J_M2)
        a = TEMP / sig_geo
        # PHASE 3b: fracture is reserved for materials that POSSESS fracture toughness.
        # Rock: wcrit = alpha * gamma_f (basalt K_IC). Sand: NO number — a granular
        # material has no K_IC; carried tension dissipates by rearrangement (the flip
        # dynamics), never by annihilation. 1e30 = un-fracturable.
        wcrit = {WSAND: 1e30, WROCK: a * GAMMA_ROCK_J_M2}
        print("PHASE 3b/3c — FRACTURE + VOID-CONNECTIVITY: rock ruptures from "
              f"void-connected surfaces (wcrit/face {wcrit[WROCK]:.1f}), "
              f"sand un-fracturable; temp={TEMP}")
        grid, shape, targets = _world_scramble(a_ns.n)
        h = open_lattice(grid, shape, targets, derive_world_J(TEMP),
                         temp=TEMP, lam=0.9, seed=0, rupture_wcrit=wcrit)
        step(h, 8 * a_ns.sweeps, trace=False)
        rup = h.ruptures[:a_ns.sweeps]
        final = close(h)
        counts, viol = rup[:, 0], int(rup[:, 1].sum())
        sand_dead, rock_dead = int(rup[:, 2 + WSAND].sum()), int(rup[:, 2 + WROCK].sum())
        total = int(counts.sum())
        first20, last20 = int(counts[:20].sum()), int(counts[-20:].sum())
        r = metrics_3d(final, shape)["radius"]
        voids = int((final == MEDIUM).sum()) - int((grid == MEDIUM).sum())
        buried = r.get(WROCK, 1e9) < r.get(WSAND, -1e9)
        print(f"  ruptures {total} (rock {rock_dead}, sand {sand_dead}), "
              f"bulk violations {viol}, voids {voids:+d}")
        print(f"  decay: first-20-sweeps {first20} vs last-20 {last20}")
        print(f"  radii: rock {r.get(WROCK, float('nan')):.1f} < "
              f"sand {r.get(WSAND, float('nan')):.1f}: {buried}")
        fA = viol == 0
        fB = sand_dead == 0
        fC = last20 < first20
        print(f"  FALSIFIER A (bulk violations = 0): {'PASS' if fA else 'FAIL — FIRED'}")
        print(f"  FALSIFIER B (sand deaths = 0): {'PASS' if fB else 'FAIL — FIRED'}")
        print(f"  FALSIFIER C (rupture curve decays): {'PASS' if fC else 'FAIL — FIRED'}")
        verdict = fA and fB and fC and buried
        print(f"PHASE 3b VERDICT: {'PASS' if verdict else 'FIRED'}")
        raise SystemExit(0 if verdict else 1)

    if a_ns.world:
        Jw = derive_world_J()
        print("THE DERIVED WORLD J (lattice units; gammas: sand %.4f J/m^2 = c*d, "
              "rock %.2f J/m^2 = K_IC^2/2E)" % (GAMMA_SAND_J_M2, GAMMA_ROCK_J_M2))
        print("           " + "  ".join(f"{WORLD_NAMES[t]:>8}" for t in (MEDIUM, WSAND, WROCK)))
        for i in (MEDIUM, WSAND, WROCK):
            print(f"  {WORLD_NAMES[i]:>8} " + "  ".join(f"{Jw[i, j]:8.2f}" for j in (MEDIUM, WSAND, WROCK)))
        gw = gamma_cpm(Jw)
        spread = gw[WROCK, MEDIUM] - gw[WSAND, MEDIUM] - gw[WSAND, WROCK]
        print(f"spreading coefficient S(sand over rock) = {spread:.2f} "
              f"(>0: sand must wet the rock core)")
        grid, shape, targets = _world_scramble(a_ns.n)
        J_unif = np.full_like(Jw, 8.0)
        np.fill_diagonal(J_unif, 4.0)
        J_unif[MEDIUM, MEDIUM] = 0.0
        rep = parity_report(grid, shape, targets, Jw, J_unif,
                            sweeps=a_ns.sweeps, seed=0, types=(WSAND, WROCK))
        d = rep["differential"]
        buried = d[WROCK] < d[WSAND]
        for label in ("differential", "uniform"):
            r = rep[label]
            print(f"  {label:<13} mean radius  " +
                  "  ".join(f"{WORLD_NAMES[t]}:{r[t]:.1f}" for t in (WSAND, WROCK)))
        print(f"WORLD VERDICT: rock burial under derived J: {'PASS' if buried else 'FAIL — FIRED'}"
              f"  ({rep['seconds']:.1f}s)")
        h = open_lattice(grid.copy(), shape, targets, Jw, temp=TEMP, lam=0.9, seed=0)
        tr = step(h, 8 * a_ns.sweeps, trace=True)
        close(h)
        sw = tr.reshape(a_ns.sweeps, 8).mean(axis=1)
        print(f"  trace: H {sw[0]:.1f} -> {sw[-1]:.1f} "
              f"(ledger record; no tau bar this run — quench regime by design)")
        raise SystemExit(0 if buried else 1)

    if a_ns.world_full:
        mats = (WMETAL, WROCK, WICE, WSAND, WBASIN)     # expected burial order
        Jw = build_world_J(WORLD_MATS)
        sig_geo = float(np.prod(list(WORLD_MATS.values()))) ** (1.0 / len(WORLD_MATS))
        print("PHASE 4 (FULL FAMILIES) — THE WORLD, ALL FAMILIES")
        print(f"  gammas (J/m^2): " + "  ".join(
            f"{WORLD_NAMES[t]} {WORLD_MATS[t]:.4g}" for t in mats))
        print(f"  sigma_geo = {sig_geo:.3f} J/m^2, alpha = temp/sigma_geo = "
              f"{TEMP / sig_geo:.3f} J^-1 m^2 at temp={TEMP}")
        print(f"  quench caveat: metal J/temp = {Jw[WMETAL, WMETAL] / TEMP:.0f} "
              f"-- prediction is on RADIUS ORDERING only")
        order = (MEDIUM,) + tuple(sorted(mats))
        print("  THE DERIVED 6x6 WORLD J (lattice units):")
        print("           " + "  ".join(f"{WORLD_NAMES[t]:>8}" for t in order))
        for i in order:
            print(f"  {WORLD_NAMES[i]:>8} " +
                  "  ".join(f"{Jw[i, j]:8.1f}" for j in order))
        grid, shape, targets = _world_scramble(a_ns.n, types=mats)
        J_unif = np.full_like(Jw, 8.0)
        np.fill_diagonal(J_unif, 4.0)
        J_unif[MEDIUM, MEDIUM] = 0.0
        rep = parity_report(grid, shape, targets, Jw, J_unif,
                            sweeps=a_ns.sweeps, seed=0, types=mats)
        for label in ("differential", "uniform"):
            r = rep[label]
            print(f"  {label:<13} mean radius  " +
                  "  ".join(f"{WORLD_NAMES[t]}:{r[t]:.1f}" for t in mats))
        d, u = rep["differential"], rep["uniform"]
        # The falsifier's four clean decades: metal/rock/ice/sand each >= 10x apart.
        clean = (WMETAL, WROCK, WICE, WSAND)
        decades_ok = all(d[clean[k]] < d[clean[k + 1]] for k in range(3))
        full_ok = decades_ok and d[WSAND] < d[WBASIN]
        uniform_sorted = all(u[mats[k]] < u[mats[k + 1]] for k in range(4))
        print(f"  falsifier A (decade pairs metal<rock<ice<sand): "
              f"{'PASS' if decades_ok else 'FAIL -- FIRED'}")
        print(f"  full ordering incl. basin (sand<basin, 6.4x -- GG-precision band): "
              f"{'ordered' if d[WSAND] < d[WBASIN] else 'INVERTED -- GG-precision limit, recorded'}")
        print(f"  falsifier B (uniform does NOT order): "
              f"{'PASS' if not uniform_sorted else 'FAIL -- FIRED'}")
        h = open_lattice(grid.copy(), shape, targets, Jw, temp=TEMP, lam=0.9, seed=0)
        tr = step(h, 8 * a_ns.sweeps, trace=True)
        final = close(h)
        sw = tr.reshape(a_ns.sweeps, 8).mean(axis=1)
        drift = {WORLD_NAMES[t]: int((final == t).sum()) - targets[t] for t in mats}
        print(f"  trace: H {sw[0]:.1f} -> {sw[-1]:.1f}; count drift {drift}")
        verdict = decades_ok and not uniform_sorted
        print(f"PHASE 4 (FULL FAMILIES) VERDICT: {'PASS' if verdict else 'FIRED'} "
              f"({'full ordering' if full_ok else 'decades only'}; {rep['seconds']:.1f}s)")
        raise SystemExit(0 if verdict else 1)

    if a_ns.world_seed:
        mats = (WMETAL, WROCK, WICE, WSAND, WBASIN)
        Jw = build_world_J(WORLD_MATS)
        grid, shape, targets = _world_seed_scramble(a_ns.n)
        n0 = targets[WMETAL]
        m0 = np.nonzero(grid == WMETAL)
        cy, cx = m0[1].mean(), m0[2].mean()
        r0 = float(np.sqrt((m0[1] - cy) ** 2 + (m0[2] - cx) ** 2).mean())
        print("PHASE 4 (NUCLEATION) — METAL ALLOWED TO EXIST")
        print(f"  two seeds r=12 at y +/- 14 off-axis: {n0} metal cells, "
              f"initial radius {r0:.1f}; derived 6x6 J, temp={TEMP}")
        # The derived kinetics, printed from the J the run uses (never hand-copied):
        J = Jw
        dH_corner = 3 * (J[WSAND, WSAND] - J[WMETAL, WMETAL])
        dH_face = 5 * (J[WSAND, WMETAL] - J[WMETAL, WMETAL]) + \
                  (J[WSAND, WSAND] - J[WSAND, WMETAL])
        print(f"  kinetics: corner dH {dH_corner:.0f} (erodes) | "
              f"face dH +{dH_face:.0f} (frozen) | crevice dH {-dH_face:.0f} (fills)")
        J_unif = np.full_like(Jw, 8.0)
        np.fill_diagonal(J_unif, 4.0)
        J_unif[MEDIUM, MEDIUM] = 0.0
        rep = parity_report(grid, shape, targets, Jw, J_unif,
                            sweeps=a_ns.sweeps, seed=0, types=mats)
        for label in ("differential", "uniform"):
            r, ar = rep[label], rep[label + "_area"]
            print(f"  {label:<13} radius " +
                  "  ".join(f"{WORLD_NAMES[t]}:{r[t]:.1f}" for t in mats) +
                  f"  | metal {ar[WMETAL]}/{n0}")
        d, u = rep["differential"], rep["uniform"]
        surv = rep["differential_area"][WMETAL] / n0
        surv_u = rep["uniform_area"][WMETAL] / n0
        r_metal, r_metal_u = d[WMETAL], u[WMETAL]
        inflate = abs(r_metal - r0) / r0
        inflate_u = abs(r_metal_u - r0) / r0
        clean = (WROCK, WICE, WSAND)
        ordering_ok = all(d[clean[k]] < d[clean[k + 1]] for k in range(2))
        fA = surv >= 0.50
        fB = inflate <= 0.20
        fC = ordering_ok
        fD = inflate_u >= 0.20      # uniform must NOT keep the seeds compact
        print(f"  falsifier A (survival >= 50%): {surv:.3f} "
              f"{'PASS' if fA else 'FAIL -- FIRED'}  (dispersion kept 0.008)")
        print(f"  falsifier B (compact, inflation <= 20%): {inflate:.3f} "
              f"{'PASS' if fB else 'FAIL -- FIRED'}")
        print(f"  falsifier C (rock < ice < sand): "
              f"{'PASS' if fC else 'FAIL -- FIRED'}")
        print(f"  falsifier D (uniform disperses, inflation >= 20%): {inflate_u:.3f} "
              f"{'PASS' if fD else 'FAIL -- FIRED'}  (uniform survival {surv_u:.3f})")
        h = open_lattice(grid.copy(), shape, targets, Jw, temp=TEMP, lam=0.9, seed=0)
        tr = step(h, 8 * a_ns.sweeps, trace=True)
        final = close(h)
        sw = tr.reshape(a_ns.sweeps, 8).mean(axis=1)
        drift = {WORLD_NAMES[t]: int((final == t).sum()) - targets[t] for t in mats}
        print(f"  trace: H {sw[0]:.1f} -> {sw[-1]:.1f}; count drift {drift}")
        verdict = fA and fB and fC and fD
        print(f"PHASE 4 (NUCLEATION) VERDICT: {'PASS' if verdict else 'FIRED'} "
              f"({rep['seconds']:.1f}s)")
        raise SystemExit(0 if verdict else 1)

    if a_ns.metal_jail:
        # PHASE 6 — THE METAL JAIL (membrane stated in docs/THE_LIVING_MATTER.md
        # BEFORE this run). The nucleation protocol UNCHANGED except per-type lam:
        # metal at 1.4 (jail 2*1.4*T_m > the derived drive 37,676), every other
        # family at rung-1's 0.9. Tests the survival law's lambda-linearity.
        mats = (WMETAL, WROCK, WICE, WSAND, WBASIN)
        Jw = build_world_J(WORLD_MATS)
        grid, shape, targets = _world_seed_scramble(a_ns.n)
        n0 = targets[WMETAL]
        m0 = np.nonzero(grid == WMETAL)
        cy, cx = m0[1].mean(), m0[2].mean()
        r0 = float(np.sqrt((m0[1] - cy) ** 2 + (m0[2] - cx) ** 2).mean())
        DRIVE_METAL = 37_676    # the derived face-erosion drive (ledger, Phase 4
                                # nucleation post-mortem, 18-connectivity check)
        lam_m = 1.4
        lam = {t: 0.9 for t in mats}
        lam[WMETAL] = lam_m
        jail = 2.0 * lam_m * n0
        print("PHASE 6 — THE METAL JAIL: per-type lambda, metal jailed alone")
        print(f"  the law, live: jail 2*{lam_m}*{n0} = {jail:,.0f} vs drive "
              f"{DRIVE_METAL:,} -> margin {jail / DRIVE_METAL - 1.0:+.1%} "
              f"(law predicts {'SURVIVAL' if jail > DRIVE_METAL else 'EXTINCTION'})")
        print(f"  protocol UNCHANGED from --world-seed: two r=12 seeds, {n0} metal "
              f"cells, temp={TEMP}, lam others 0.9")
        J_unif = np.full_like(Jw, 8.0)
        np.fill_diagonal(J_unif, 4.0)
        J_unif[MEDIUM, MEDIUM] = 0.0
        rep = parity_report(grid, shape, targets, Jw, J_unif,
                            sweeps=a_ns.sweeps, seed=0, types=mats, lam=lam)
        for label in ("differential", "uniform"):
            r, ar = rep[label], rep[label + "_area"]
            print(f"  {label:<13} radius " +
                  "  ".join(f"{WORLD_NAMES[t]}:{r[t]:.1f}" for t in mats) +
                  f"  | metal {ar[WMETAL]}/{n0}")
        d = rep["differential"]
        surv = rep["differential_area"][WMETAL] / n0
        r_metal = d[WMETAL]
        inflate = abs(r_metal - r0) / r0
        clean = (WROCK, WICE, WSAND)
        ordering_ok = all(d[clean[k]] < d[clean[k + 1]] for k in range(2))
        fA = surv >= 0.50
        fB = not (0.45 <= surv <= 0.55)
        fC = ordering_ok
        print(f"  falsifier 1 (survival >= 50% at lam_m=1.4): {surv:.3f} "
              f"{'PASS' if fA else 'FAIL -- FIRED'}  (uniform-lambda runs: 0.008, 0.000)")
        print(f"  falsifier 2 (margin is signal, not noise -- outside 0.45-0.55): "
              f"{'PASS' if fB else 'FAIL -- FIRED'}")
        print(f"  falsifier 3 (no leak: rock < ice < sand preserved): "
              f"{'PASS' if fC else 'FAIL -- FIRED'}")
        h = open_lattice(grid.copy(), shape, targets, Jw, temp=TEMP, lam=lam, seed=0)
        tr = step(h, 8 * a_ns.sweeps, trace=True)
        final = close(h)
        sw = tr.reshape(a_ns.sweeps, 8).mean(axis=1)
        drift = {WORLD_NAMES[t]: int((final == t).sum()) - targets[t] for t in mats}
        print(f"  trace: H {sw[0]:.1f} -> {sw[-1]:.1f}; count drift {drift} "
              f"(leak check: rock's recorded equilibrium bleed is ~-4%)")
        verdict = fA and fB and fC
        print(f"PHASE 6 (METAL JAIL) VERDICT: {'PASS' if verdict else 'FIRED'} "
              f"({rep['seconds']:.1f}s)")
        raise SystemExit(0 if verdict else 1)

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
