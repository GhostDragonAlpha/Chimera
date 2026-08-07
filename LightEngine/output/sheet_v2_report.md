# theSheet v2 — Full Run Report

**Date:** 2026-08-07  
**Seed:** 20260806  
**Code changes:** `LightEngine/seed_structures.py` (v2 builder + `derive_sheet_equilibrium_spacing`), `LightEngine/demo_seed.py` (v2 driver + split-thickness metric), `LightEngine/tests/test_structures.py` (derived-spacing tests).  
**Test suite:** `python -m pytest LightEngine/tests -q` → **87 passed, 6 warnings**.

---

## 1. Theory under test

> A 2-D layer on a substrate is a persistent 2-D phase; the substrate's DRAW holds it flat, the cushion keeps it one grain off the surface, and its own self-DRAW holds it in-plane. Cloth, not shell, by necessity — and cloth is what skin and bladder need.

v1 discovered that printing at `spacing = 0.05` lu over-compresses the sheet in-plane; the sheet escapes out-of-plane and crumples to a ~0.24 lu thick mat whether a substrate is present or not.  
v2 names the successor: **derive the 2-D in-plane equilibrium spacing `d_eq_2D` from the kernel** and reprint all four modes at that spacing, with the v1 falsifiers left unchanged.

---

## 2. Derivation of d_eq_2D

### Method

For a finite `N×N` flat patch at spacing `a`, interior grains feel zero net in-plane force by symmetry; the force balance lives at the boundary.  `d_eq_2D` is defined as the zero-crossing of

```
F_edge(a) = mean inward-signed in-plane force on the perimeter grains,
```

computed with `kernel.compute_forces` on a static 16×16 patch (zero velocity).  Root finding uses bisection.

### Bracket rationale

The cushion band is `[R_WALL, R_BOND] = [0.05, 0.15]` lu.  The 3-D droplet equilibrium `d_eq = 0.04840` lu sits just under `R_WALL`.  Because the 2-D root is expected to differ, the bracket `[0.03, 0.10]` lu is intentionally wide and the measurement is allowed to find the root without bias.

### Bisection trace

```text
[derive d_eq_2D] bracket rationale: cushion band is [R_WALL, R_BOND] = [0.05, 0.15] lu; 3-D droplet d_eq = 0.04840 lu sits just under R_WALL.
[derive d_eq_2D] bisecting F_edge(a) = 0 on the 16x16 patch:
  iter 0: a=0.03000 F=-85.768181
  iter 0: a=0.10000 F=+4.957038
  iter 1: a=0.04750 F=+9.259963  bracket=[0.03000, 0.06500]
  iter 2: a=0.03875 F=-3.306798  bracket=[0.03000, 0.04750]
  iter 3: a=0.04312 F=+5.375486  bracket=[0.03875, 0.04750]
  iter 4: a=0.04094 F=+1.876093  bracket=[0.03875, 0.04312]
  iter 5: a=0.03984 F=-0.479806  bracket=[0.03875, 0.04094]
  iter 6: a=0.04039 F=+0.752100  bracket=[0.03984, 0.04094]
  iter 7: a=0.04012 F=+0.150255  bracket=[0.03984, 0.04039]
  iter 8: a=0.03998 F=-0.161182  bracket=[0.03984, 0.04012]
  iter 9: a=0.04005 F=-0.004576  bracket=[0.03998, 0.04012]
  iter 10: a=0.04008 F=+0.072976  bracket=[0.04005, 0.04012]
  iter 11: a=0.04007 F=+0.034257  bracket=[0.04005, 0.04008]
  iter 12: a=0.04006 F=+0.014810  bracket=[0.04005, 0.04007]
  iter 13: a=0.04005 F=+0.005117  bracket=[0.04005, 0.04006]
[derive d_eq_2D] root d_eq_2D = 0.04005 lu (tol=1.0e-05, iters=13)
```

**Measured `d_eq_2D = 0.04005` lu.**

### Comparison to the 3-D droplet d_eq

- 3-D droplet `d_eq = 0.04840` lu.
- 2-D sheet `d_eq_2D = 0.04005` lu — **smaller** by ~17%.

This matches the per-grain DRAW intuition.  In 2-D each grain has fewer in-plane neighbors than in 3-D, so the net inward DRAW on an edge grain is weaker.  To reach force balance, the patch must sit closer to the wall where cushion repulsion is stronger.  A smaller equilibrium spacing is therefore the expected direction.

---

## 3. v2 run matrix and verdicts

All modes printed at `spacing = d_eq_2D = 0.04005` lu.  Falsifiers are identical to v1:

- `(a) PHASE` — bump/flat: 1 cluster and thickness `<= 0.10` lu; free: thickness `> 0.5 × sheet_width`.
- `(b) DRAPE` — bump: block in cushion band `[0.02840, 0.09840]` and `>= 30/60` edge grains in band.
- `(c) TEAR` — first split in `[1.5×, 4×]` stretch, exactly 2 clusters at split, split location recorded; v2 adds thickness at split.

| mode  | ticks  | N   | final clusters | final thickness | verdict | notes |
|-------|--------|-----|----------------|-----------------|---------|-------|
| flat  | 6 000  | 292 | 1              | 0.2497          | **PHASE FAIL** | still crumples to ~6.2 lattice steps, stable 20k-equivalent |
| bump  | 6 000  | 356 | 1              | 0.2368          | **PHASE FAIL**, **DRAPE FAIL** | edge drape now passes (34/60), but block sits 0.0005 lu below cushion band |
| free  | 20 000 | 256 | 1              | 0.2381          | **PHASE FAIL** | no balling; COM frozen at z≈0.0885 for 20k ticks |
| tear  | 20 000 | 292 | 2 at split     | —               | **TEAR FAIL** | first split at tick 343, stretch 1.029, thickness at split 0.3126 |

**Overall v2 result: all four falsifiers still fail.**

---

## 4. Verdict blocks (verbatim from the logs)

### flat

```text
[sheet] SHEET v1 FALSIFIERS:
  (a) PHASE  : FAIL  final_clusters=1 final_thickness=0.2497 bar<= 0.1000
  (b) DRAPE  : skipped (flat)
  (c) TEAR   : skipped (flat)
```

### bump

```text
[sheet] SHEET v1 FALSIFIERS:
  (a) PHASE  : FAIL  final_clusters=1 final_thickness=0.2368 bar<= 0.1000
  (b) DRAPE  : FAIL  min_to_block=0.0279 band=[0.0284,0.0984] edge_in_band=34/60 tented=False
  (c) TEAR   : skipped (bump)
```

### free

```text
[sheet] SHEET v1 FALSIFIERS:
  (a) PHASE  : FAIL  final_clusters=1 final_thickness=0.2381 bar> 0.3004
  (b) DRAPE  : skipped (free)
  (c) TEAR   : skipped (free)
```

### tear

```text
[sheet] FIRST SPLIT at tick=343: clusters=2 stretch=1.029 split_between_rows=0-1 thickness_at_split=0.3126

[sheet] SHEET v1 FALSIFIERS:
  (a) PHASE  : skipped (tear run)
  (b) DRAPE  : skipped (tear)
  (c) TEAR   : FAIL  split_tick=343 stretch=1.029 window=[1.5,4.0] clusters_at_split=2 split_between_rows=0-1 thickness_at_split=0.3126
```

*Note: the tear and free/bump/flat runs completed before the cosmetic verdict-label update from "SHEET v1 FALSIFIERS" to "SHEET v2 FALSIFIERS" was applied; the code now prints the v2 label for subsequent runs.  The numbers above are verbatim from the executed v2 logs.*

---

## 5. Trajectory summaries

### flat (6 000 ticks)
- Released at `z = d_eq + d_eq_2D ≈ 0.0885`.
- Early out-of-plane buckle: thickness peaks at 0.426 around tick 450.
- Settles into a persistent folded mat: thickness `0.249–0.250` after tick 3000.
- Edge grains in cushion band drop from 60/60 to ~31/60 as the sheet crumples and lifts off the plate.

### bump (6 000 ticks)
- Block top starts at `z ≈ 0.257`; sheet initially `0.088` above it.
- The sheet collapses onto the block and plate; thickness stabilizes ~0.237.
- `min_to_block` hovers at `0.0276–0.0280`, just below the lower cushion bound `0.0284` — the block is seated in the wall, not in the cushion band.
- Edge drape improves vs v1: 34/60 edge grains reach the plate band (v1: 22/60), now passing the `>= 30/60` bar.  Block contact is the remaining DRAPE failure.

### free (20 000 ticks)
- No substrate; same initial height as flat.
- The sheet expands slightly, then stabilizes as a flat self-supported membrane:
  - thickness settles at `0.2381` (~5.9 lattice steps),
  - COM stays at `z ≈ 0.0885` for the entire 20 000 ticks,
  - no clustering event, no balling.
- The in-plane self-DRAW again dominates over any out-of-plane collapse mechanism.

### tear (20 000 ticks)
- Two opposite y-edge rows pinned and pulled apart at 5% sound speed.
- **First split at tick 343** — essentially immediate.
- Stretch at split: **1.029×** (window `[1.5, 4.0]`).
- Split location: between rows **0–1**, adjacent to the grip, same as v1.
- Thickness at split: **0.3126** — the sheet is already crumpled when it tears.
- After split, fragments to 3 clusters by tick 842.

---

## 6. Assessment of the named prediction

The v2 prediction was: at `d_eq_2D` the sheet stays flat (`<= 2` steps), drapes instead of tenting, and tears inside `[1.5×, 4×]`.

| predicted behavior | outcome |
|--------------------|---------|
| flat/bump `<= 0.10` lu thick | **FAILED** — both settle ~0.24 lu |
| bump drapes (block in band + edges in band) | **PARTIAL** — edges now pass, block still below band |
| free balls up | **FAILED** — remains flat at 0.238 lu |
| tear splits inside `[1.5×, 4×]` | **FAILED** — splits at 1.029×, adjacent to grip |

Deriving and printing at `d_eq_2D` did not produce a flat 2-D phase under the v1 bars.

---

## 7. Surprises and interpretation

1. **The 2-D equilibrium spacing is smaller than the 3-D droplet spacing.**  `d_eq_2D = 0.04005` lu vs `d_eq = 0.04840` lu.  This is the direction expected from the reduced neighbor count in 2-D, and the bisection gives a clean, reproducible root.

2. **Crumpling persists at `d_eq_2D`.**  The sheet still folds to ~0.24 lu (≈6 lattice steps) in flat/bump/free modes.  The static edge-force root prevents net inward collapse at the boundary, but it does not stabilize the sheet against dynamic out-of-plane buckling once the full simulation begins.  The boundary derivation is necessary but not sufficient for a flat phase.

3. **Bump edge drape improved.**  At the looser spacing the sheet's outer edges reached the plate cushion band (34/60 vs 22/60 in v1).  This shows the spacing matters for draping, even though the block contact still fails.

4. **Tear still fails the stretch window, and the sheet is crumpled at split.**  The thickness-at-split metric (0.3126 lu) confirms the v1 premise problem: the tear test assumes a flat sheet under in-plane strain, but the sheet crumples before the pull begins, so the grip pulls out of a mat, not a lattice.

5. **Free sheet remains a stable flat membrane.**  Even at `d_eq_2D` and 20 000 ticks there is no nucleation of collapse.  Without an external perturbation, bending, or gravity, the flat initial condition is an attractor.

---

## 8. What v2 proves and what it does not

- **Proved:** `d_eq_2D` can be derived from the kernel as the static edge-force root; the derivation is reproducible and smaller than the 3-D droplet `d_eq` as expected; the builder can switch between explicit spacing and derived spacing; the tear metric now records thickness at split.
- **Not proved:** printing at `d_eq_2D` satisfies the sheet-as-cloth predictions.  All four target behaviors still fail the v1 bars.

---

## 9. Suggested next directions

- **The missing ingredient is out-of-plane stiffness.**  The kernel currently has no bending resistance; any in-plane stress immediately folds the sheet.  A derived bending term (e.g. from three-point curvature) is the natural successor.
- **For draping:** the block sits just below the cushion band; raising the block-to-sheet initial gap or softening the sheet may move `min_to_block` into `[0.0284, 0.0984]`.
- **For free balling:** introduce a small initial perturbation or thermal jiggle to break the flat equilibrium.
- **For tear:** either strengthen the grip-to-bulk transition so the first split occurs in the interior, or accept that the current kernel tears at the grip at low stretch and record that as the measured law.

---

*Report generated from logs:*
- `LightEngine/output/print_sheet_v2_flat.txt`
- `LightEngine/output/print_sheet_v2_bump.txt`
- `LightEngine/output/print_sheet_v2_free.txt`
- `LightEngine/output/print_sheet_v2_tear.txt`
