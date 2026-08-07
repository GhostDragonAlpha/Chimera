# theSheet v1 — Full Run Report

**Date:** 2026-08-07  
**Seed:** 20260806  
**Code:** `LightEngine/seed_structures.py:sheet(...)`, `LightEngine/demo_seed.py:sheet_main(...)`  
**Test suite:** `python -m pytest LightEngine/tests -q` → **84 passed, 6 warnings**

---

## 1. Theory under test

> A 2-D layer on a substrate is a persistent 2-D phase; the substrate's DRAW holds it flat, the cushion keeps it one grain off the surface, and its own self-DRAW holds it in-plane. Cloth, not shell, by necessity — and cloth is what skin and bladder need.

**Prediction:**
- `flat` and `bump` prints settle as a single connected sheet `<= 2` lattice steps thick.
- `bump` drapes so the block top and the plate edges are both in cushion contact.
- `free` sheet balls up (thickness > half sheet width).
- `tear` splits once at a global stretch between `1.5x` and `4x`.

**Falsifiers:**
- `(a) PHASE` — bump/flat not 1 cluster or thickness > 2 lattice steps; free sheet does not ball.
- `(b) DRAPE` — bump: block not in cushion band or < half edge grains in cushion band.
- `(c) TEAR` — first split outside `[1.5x, 4x]` or fragmentation > 2 clusters.

**Derived constants (shared across modes):**
- `d_eq = 0.04840`
- cushion band = `[0.02840, 0.09840]`
- sheet_width = `0.75000`
- 2 lattice steps ≈ `0.0968`, half sheet width = `0.3750`

---

## 2. Run matrix and verdicts

| mode  | ticks  | N   | clusters final | thickness final | verdict | notes |
|-------|--------|-----|----------------|-----------------|---------|-------|
| flat  | 6 000  | 292 | 1              | 0.2414          | **PHASE FAIL** | settles ~5× lattice-step thick, crumples rather than staying 2-D |
| bump  | 6 000  | 356 | 1              | 0.2482          | **PHASE FAIL**, **DRAPE FAIL** | thickness stable but too bulky; block sits just below cushion band; only 22/60 edge grains in band |
| free  | 20 000 | 256 | 1              | 0.2411          | **PHASE FAIL** | no collapse/balling; COM frozen at z≈0.0984; sheet remains flat and self-supported |
| tear  | 20 000 | 292 | 2 at split     | —               | **TEAR FAIL** | first split at tick 341, stretch 1.023, between grip rows 0–1; far below [1.5, 4.0] window |

**Overall v1 result: all four falsifiers fired.**

---

## 3. Trajectory summaries

### flat (6 000 ticks)
- Rapid out-of-plane wrinkling: thickness jumps from 0.003 → 0.44 by tick 600.
- After tick ~1500 the sheet reaches a steady-state crumple:
  - thickness oscillates in `[0.2385, 0.2416]`
  - COM drifts to `(-0.0013, 0.0011, 0.0413)`
  - edge grains in cushion band settle at 35/60.
- The final sheet is ~2.5× the allowed thickness bar (`<= 0.1000`).

### bump (6 000 ticks)
- Initial drop wraps the sheet around the central block.
- Transient bifurcation: `clusters=2` at tick 750, then re-merges by tick 900.
- Steady state:
  - thickness `0.2481–0.2482`
  - `min_to_block` hovers at `0.0278–0.0280` (just under the lower cushion bound `0.0284`)
  - `edge_in_band` plateaus at 22/60, well under the 30/60 threshold.
- No tenting was recorded; the block pins the center too low.

### free (20 000 ticks)
- No substrate or block; sheet is released with zero initial velocity.
- Instead of collapsing into a ball, it expands slightly then stabilizes as a flat, self-supporting membrane:
  - thickness stays near `0.2411` (≈5× lattice step)
  - COM stays at `z ≈ 0.0984` for the entire run
  - no clustering event, no balling
- The in-plane self-DRAW is evidently stronger than the out-of-plane thermal/jiggle terms over this timescale.

### tear (20 000 ticks)
- Two grip rows (rows 0 and 15) are pinned and pulled apart at constant speed.
- **First split at tick 341** — almost immediately.
- Stretch at split: **1.023x** (window is `[1.5, 4.0]`).
- Split location: between rows **0–1**, i.e. adjacent to the pinned grip row, not in the bulk.
- After split, system fragments to 3 clusters by tick 500 and continues drifting.

---

## 4. Honest surprises and interpretation

1. **The sheet does not stay 2-D.**  
   The flat/bump final thickness is ~0.24, about **5 lattice steps**. The physical model seems to produce a finite-thickness membrane rather than a true 2-D cloth. The PHASE bar of `<= 2 lattice steps` was missed by a large margin.

2. **The free sheet does not ball up.**  
   Even at 20 000 ticks the free sheet remains essentially flat and stationary. This suggests the self-DRAW/in-plane forces and the initial zero-velocity condition create a stable equilibrium, with no mechanism to nucleate a collapse. A thermal kick, bending stiffness, or gravity may be needed to trigger balling.

3. **The bump run fails DRAPE twice.**  
   The block sits ~0.0004 below the cushion band lower bound, and fewer than half the edge grains contact the plate cushion. The block is too attractive or the sheet too stiff to drape over it.

4. **The tear splits too early and at the grip.**  
   A stretch of 1.023x means the material separates almost under its own setup tension. The failure starts at the grip boundary, which is an artifact of the boundary condition rather than a bulk tear. This indicates the grip-to-sheet coupling is the weakest link, not the sheet's fracture toughness.

---

## 5. What v1 proves and what it does not

- **Proved:** the builder produces deterministic, connected, non-overlapping sheets; the driver prints falsifiable numbers; the test harness reports honest failures.
- **Not proved:** the physical model satisfies the sheet-as-cloth predictions. All four target behaviors failed the chosen bars.

---

## 6. Suggested next directions

- **Reduce effective sheet thickness** by strengthening the out-of-plane confinement or adding a bending resistance that penalizes crumpling.
- **For free balling:** introduce a small initial perturbation/thermal jiggle or gravity to break the flat equilibrium.
- **For bump drape:** raise the block cushion interaction or soften the sheet so it tents over the block instead of sitting below the band.
- **For tear:** move the grip coupling away from row 0 (e.g. a transition row with stronger bonds) so the first split occurs in the bulk at a higher stretch.

---

*Report generated from logs:*
- `LightEngine/output/print_sheet_v1_flat.txt`
- `LightEngine/output/print_sheet_v1_bump.txt`
- `LightEngine/output/print_sheet_v1_free.txt`
- `LightEngine/output/print_sheet_v1_tear.txt`
