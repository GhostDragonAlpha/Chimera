# theSheet v3 — THE FRAMED SHEET Report

**Date:** 2026-08-07  
**Seed:** 20260806  
**Code changes:** `LightEngine/seed_structures.py` (`framed` parameter), `LightEngine/demo_seed.py` (v3 header, framed tear protocol, v3 falsifiers), `LightEngine/tests/test_structures.py` (framed builder tests).  
**Test suite:** `python -m pytest LightEngine/tests -q` → **90 passed, 6 warnings**.

---

## 1. Theory under test

> A flat membrane exists only in a frame; the frame IS the membrane that holds the plane. Cloth, not shell, by necessity.

v1 and v2 showed that a free 16×16 sheet has no flat 2-D phase at any tested spacing: it folds into a ~0.24 lu thick mat whether a substrate is present or not.  v3 applies the bone lesson — **form lives in membranes** — by pinning the four border rows (60 grains) in their print positions and removing the substrate plate entirely.  The frame itself is the membrane that is supposed to hold the plane.

---

## 2. Builder changes

`seed_structures.sheet(..., framed=False)`:
- `framed=False` preserves v1/v2 behavior.
- `framed=True`:
  - Omits the 6×6 ground plate.
  - Pins every grain with local x-index `0` or `15` **or** y-index `0` or `15` — exactly the 60 border grains.
  - Reports `derived["frame"] = 60`.
  - In framed tear mode, two opposite y-edge rows of the frame are the moving grips; the other two frame edges stay fixed.

---

## 3. v3 falsifiers

All prints use the derived 2-D spacing `d_eq_2D = 0.04005` lu, so the flat bar is derived in code:

```python
flat_bar = 2.0 * derived["spacing"]  # = 0.08011 lu
```

- **(a) PHASE-FRAMED** (settle run): every sampled tick of a 6000-tick run must have `clusters == 1` **and** `thickness <= flat_bar`.  If any sample fails, report the first fail tick and the maximum thickness.
- **(c) TEAR-FRAMED** (tear run): first split must occur at stretch `∈ [1.5×, 4×]`, with exactly 2 clusters at split, and `thickness_at_split <= flat_bar` (was the sheet still flat when torn?).  Split location is recorded.

---

## 4. Run matrix and verdicts

| run    | ticks  | N   | max thickness | first fail / split | verdict |
|--------|--------|-----|---------------|--------------------|---------|
| framed settle | 6 000  | 256 | 0.3961        | tick 300           | **PHASE-FRAMED FAIL** |
| framed tear   | 20 000 | 256 | —             | tick 362, stretch 1.031 | **TEAR-FRAMED FAIL** |

**Overall v3 result: both falsifiers fail.**

---

## 5. Verdict blocks (verbatim)

### framed settle

```text
[sheet] SHEET v3 FALSIFIERS:
  (a) PHASE-FRAMED : FAIL  samples=41 max_thickness=0.3961 bar<= 0.08011 first_fail_tick=300
  (b) DRAPE  : skipped (flat)
  (c) TEAR   : skipped (flat)
```

### framed tear

```text
[sheet] FIRST SPLIT at tick=362: clusters=2 stretch=1.031 split_between_rows=0-1 thickness_at_split=0.2817

[sheet] SHEET v3 FALSIFIERS:
  (a) PHASE  : skipped (tear run)
  (b) DRAPE  : skipped (tear)
  (c) TEAR-FRAMED   : FAIL  split_tick=362 stretch=1.031 window=[1.5,4.0] clusters_at_split=2 split_between_rows=0-1 thickness_at_split=0.2817 flat_at_split=False
```

---

## 6. Trajectory summaries

### framed settle (6 000 ticks)

- The print starts flat at `z ≈ 0.0885` with all 256 grains in one cluster.
- Buckling begins immediately: thickness rises to **0.3961 lu by tick 600** (≈10 lattice steps, ~5× the flat bar).
- The sheet transiently splits into **2 clusters** from tick 600 through tick 4500.
- After tick 4650 the two halves reconnect into one cluster, but the sheet remains heavily folded:
  - thickness stabilizes around **0.222 lu** (≈5.5 lattice steps),
  - COM drifts in-plane to `(-0.107, -0.181, 0.088)` by tick 6000.
- The frame prevents total collapse into a ball, but it does **not** enforce flatness.

### framed tear (split + 500-tick margin)

- Two opposite y-edge frame rows are pulled apart at 5% sound speed.
- **First split at tick 362** with global stretch **1.031×** (window `[1.5×, 4×]`).
- Split location: between rows **0–1**, adjacent to the moving grip — the same location as v1/v2.
- `thickness_at_split = 0.2817 lu`, well above the flat bar `0.08011 lu`; the sheet is already folded when it tears.
- Post-split the two fragments remain connected through the frame and recombine to one cluster by tick 500, while the grips continue to separate.

---

## 7. Assessment of the named prediction

The v3 prediction was:
1. The framed sheet holds flat (thickness ≤ 2 lattice steps).
2. When two opposite frame rows are pulled apart, it tears once inside `[1.5×, 4×]` while still flat.

| predicted behavior | outcome |
|--------------------|---------|
| framed sheet stays flat | **FAILED** — thickness exceeds flat bar at tick 300 and peaks at 0.3961 lu |
| tear inside `[1.5×, 4×]` | **FAILED** — splits at 1.031×, same early-grip location as v1/v2 |
| flat at tear moment | **FAILED** — thickness at split 0.2817 lu, `flat_at_split=False` |

The frame changes the dynamics but does not create a flat 2-D phase under the stated bar.

---

## 8. Surprises and interpretation

1. **The frame delays but does not prevent buckling.**  The free sheet in v1/v2 collapsed to ~0.24 lu almost immediately.  The framed sheet buckles to a similar folded state, but takes ~600 ticks to develop the first major fold and transiently splits into two clusters before reconnecting.

2. **The frame converts the failure mode from crumple to in-plane drift.**  Because the border grains are pinned, the folded sheet cannot ball up; instead the entire interior drags the frame in-plane (COM moves to `-0.11, -0.18` by tick 6000).  The frame is doing work, but not the work the falsifier asked.

3. **Tear still occurs at the grip at very low stretch.**  Even with the frame holding the borders, the first split is between rows 0–1 at stretch 1.031×.  The failure mode is identical to v1/v2: strain concentration at the moving boundary tears the sheet before the bulk experiences the intended `[1.5×, 4×]` window.

4. **The sheet is not flat at tear time.**  `thickness_at_split = 0.2817 lu` confirms that the v3(c) premise — a flat sheet under in-plane strain — is still not met.  The grip pulls a folded membrane apart.

---

## 9. What v3 proves and what it does not

- **Proved:** a pinned frame changes the sheet's failure mode.  It prevents balling and produces transient two-cluster dynamics, showing that boundary conditions are active, not cosmetic.
- **Not proved:** the frame is sufficient to create a flat 2-D phase or a clean in-window tear.  Both falsifiers still fail.

---

## 10. Suggested next directions

- **Out-of-plane bending stiffness is still missing.**  The kernel has no mechanism to resist folding.  A derived bending term (e.g. curvature penalty from triplets of grains) is the natural next successor.
- **Grip stress concentration must be addressed before the tear window can be tested.**  Options: widen the pinned grip region (a reinforced hem), or pre-stretch the sheet quasistatically before measuring the bulk tear.
- **The flat bar itself may need revisiting.**  At `d_eq_2D = 0.04005` lu, 2 lattice steps = 0.0801 lu.  Even a small thermal ripple or print jitter exceeds this, so the bar may be too strict for a zero-bending-stiffness material.  A derived tolerance from the jitter amplitude may be more honest.

---

*Report generated from logs:*
- `LightEngine/output/print_sheet_v3_framed.txt`
- `LightEngine/output/print_sheet_v3_tear.txt`
