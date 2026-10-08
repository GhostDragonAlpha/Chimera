# SHAPE-SILHOUETTE-02 — PREREGISTRATION AND OFFLINE ANALYSIS

**Term:** `theShape`  
**Status:** FAIL_RESTART (alignment 0.200, standard watch prompt, 12-frame movie, size_scale=0.35)  
**Task:** Isolated offline analysis + preregistration for controlled runtime comparison  
**Date:** 2026-09-10  

## 1 · Frozen geometry and cell-size law

### 1.1 Original lattice (HEAD, s = 0.01 m)

| Property | Value |
|----------|-------|
| cell_size | 0.01 m |
| grid_shape | [47, 97, 94] cells |
| cell_count | 24,801 |
| origin | [-0.23172844, -0.50248924, -0.47978729] m |
| world bbox | [-0.2317, -0.5025, -0.4798] to [0.2383, 0.4675, 0.4602] m |
| world extent | [0.470, 0.970, 0.940] m |
| approx volume | 0.0248 m³ |
| cell-center COM | [0.0325, -0.0246, -0.0251] m |
| connected components | 131 (main body: 24,550 cells; fragments: 19, 13, 9, 8, 8, 8, 7, 6, 5, ...) |
| CoM gap (phase0) | 0.312 cells per-axis max, 0.538 cells worst magnitude |
| slack_bound | 1.0 cell |

### 1.2 Current lattice (working tree, s = 0.02 m)

| Property | Value |
|----------|-------|
| cell_size | 0.02 m |
| grid_shape | [24, 49, 48] cells |
| cell_count | 6,595 |
| origin | [-0.23672844, -0.50748924, -0.48478729] m |
| world bbox | [-0.2367, -0.5075, -0.4848] to [0.2433, 0.4725, 0.4752] m |
| world extent | [0.480, 0.980, 0.960] m |
| approx volume | 0.0528 m³ |
| cell-center COM | [0.0187, -0.0364, -0.0333] m |
| connected components | 4 (main body: 6,589 cells; fragments: 3, 2, 1) |
| CoM gap (phase0) | 0.649 cells per-axis max, 0.653 cells worst magnitude |
| slack_bound | 1.0 cell |

### 1.3 Comparison: what changed and what did not

**What did NOT change:**
- Source cloud: `models/genbear2/genbear2_final_engine.splat` (182,724 raw splats, 64,309 after alpha_cut=0.5)
- Axis mapping: asset Y-up → membrane Z-up via `(x, y, z) → (x, -z, y)`
- Emission function: `emit()` rotates around Z-axis (PX, PY) by `ang = pi * t`
- Ground plane: 900 grains at `z_floor - s`, spread to `r_xy = 1.5 * max(|x|, |y|)`
- Color: bear brown (0.45, 0.30, 0.18), ground (0.16, 0.15, 0.14)
- TYPE = 3.0, ALPHA = 1.0

**What changed:**
- `cell_size` s doubled from 0.01 m to 0.02 m
- `grid_shape` halved from [47, 97, 94] to [24, 49, 48]
- `cell_count` reduced from 24,801 to 6,595
- `origin` shifted by -0.005 m on each axis (half the original s)
- World bbox expanded slightly: +0.01 m on max side, -0.005 m on min side
- Connected components reduced from 131 to 4 (coarser lattice merges small fragments)
- CoM gap increased from 0.312 to 0.649 cells (still within 1.0-cell slack bound)

**Key observation:** The world-space bounding box changed by less than 2% on each axis. The lattice is the SAME bear at a COARSER resolution. The physics changed the discretization, not the shape.

## 2 · Camera and projection tracing

### 2.1 Camera positioning (Python bridge → C++ engine)

In `render_term_movie`:
```python
extent = float(np.linalg.norm(buf[:, 0:3], axis=1).max()) or 1.0
cam_pos = (0.0, -2.7 * extent, 0.72 * extent)
```

For current buffer (t=0):
- `extent` = 0.880 m (max norm of all splats, including ground)
- `cam_pos` = (0.0, -2.376, 0.634) m

Converted to spherical via `_spherical()`:
- `r` = 2.459 m
- `theta` = atan2(0, -0.634) = π rad
- `phi` = asin(-2.376 / 2.459) = -1.300 rad = -74.5°

### 2.2 C++ engine camera convention

From `engine.cpp`:
```cpp
float eye[3] = {
    target[0] + radius * cos(phi) * sin(theta),
    target[1] + radius * sin(phi),
    target[2] - radius * cos(phi) * cos(theta)
};
```

`set_camera()` sets `target = (0, 0, 0)`. So:
- `eye` = (0, -2.376, 0.634) m
- Camera looks at origin from below and slightly above (Z = 0.634 > 0)

### 2.3 Projection parameters

From `update_camera_matrices()`:
- Vertical FOV: 45°
- Near plane: 0.1 m
- Far plane: 1000.0 m
- Aspect: viewport width / viewport height (default 1920/1080 = 16:9)

### 2.4 Framing analysis

Visible height at distance r = 2.459 m:
```
h_visible = 2 * r * tan(fov/2) = 2 * 2.459 * tan(22.5°) = 2.04 m
```

Bear height (PY axis in membrane = -asset Z):
- PY range: [-0.497, 0.463] m → height = 0.960 m
- Bear fills 0.960 / 2.04 = 47% of vertical frame

Bear width (PX axis):
- PX range: [-0.227, 0.233] m → width = 0.460 m
- At 16:9 aspect, visible width = 2.04 * 16/9 = 3.63 m
- Bear fills 0.460 / 3.63 = 13% of horizontal frame

**Critical finding:** The ground plane dominates the frame. Ground grains spread to `r_xy = 1.5 * max(|x|, |y|) ≈ 1.5 * 0.695 = 1.04 m`. The ground plane is a flat disk at z ≈ -0.525 m. From the camera at z = 0.634 m, the ground plane is 1.16 m away and subtends an angular radius of `atan(1.04 / 1.16) ≈ 41°`. This is almost the entire 45° vertical FOV.

The bear is a small object IN the middle of a large ground disk. The eye reads the ground as "a flat gray shadow" and the bear as "a small brown blob."

### 2.5 Clipping

- Near plane at 0.1 m: no clipping (camera is 2.46 m from origin)
- Far plane at 1000 m: no clipping
- The ground plane grains are at z ≈ -0.525 m, which is in front of the camera (camera looks towards -Z in camera space)

## 3 · Offline orthographic silhouette projections

Saved to `docs/evidence/shape_silhouette_02/shape_silhouettes_filled.png` and `shape_silhouettes_vs_cloud.png`.

**Observations from projections:**
- The current lattice (s = 0.02 m, 6,595 cells) preserves the overall bear silhouette in all three principal views.
- The original lattice (s = 0.01 m, 24,801 cells) shows finer detail but the same overall shape.
- The bear has a distinctive head (round, at +PZ), body (large, at middle PY), limbs (at ±PY, ±PX), and ears (small protrusions at high PZ).
- The Y-Z projection (PY vs PZ) shows the clearest bear profile: head at top (high PZ), body in middle, feet at bottom (low PZ).

**Diagnostic conclusion:** The bear silhouette IS recognizable in orthographic projection. The issue is NOT the lattice geometry — it's the perspective framing that makes the bear small and centered on a large ground disk.

## 4 · Preregistered controlled runtime comparison

### 4.1 Statement

The `theShape` dyad fails because the camera framing makes the bear small relative to the ground plane, not because the lattice is wrong. A controlled comparison will test this by changing ONE presentation variable at a time while keeping geometry and reading fixed.

### 4.2 Prediction

(a) Reducing the ground plane extent from `1.5 * max(|xy|)` to `0.8 * max(|xy|)` will make the bear fill ≥ 60% of the frame height while keeping the ground visible as a subtle shadow.  
(b) Moving the camera closer (radius 1.5 * extent instead of 2.7 * extent) will make the bear fill ≥ 70% of the frame height, but may clip the ground or distort perspective.  
(c) A higher camera elevation (phi = -0.5 rad instead of -1.30 rad) will show the bear from above, making the head and limb structure more visible.

### 4.3 Falsifiers

(i) The eye still reads "small blob on flat gray shadow" after ground reduction → the issue is not ground extent.  
(ii) The eye reads the bear as a different shape or object → the camera angle is distorting the silhouette.  
(iii) Alignment does not improve with any single variable change → the issue is the combination of variables, requiring a new preregistration.

### 4.4 Bounds

- Geometry is fixed: current lattice (s = 0.02 m, 6,595 cells), same emit(), same axis mapping.
- Reading is fixed: "a brown teddy bear shape built from many small overlapping brown grains or soft blobs, forming the same bear as the smooth cloud but with a visible grain texture -- ROTATING on the spot like a turntable inspection over a dim dark ground that stays STILL: one solid animal (head, ears, body, limbs) at every angle, front and back, NOT hollow, NOT flat, NOT a different object"
- Threshold is fixed: 0.6 alignment
- Only ONE variable changes per run:
  1. Ground extent multiplier: 1.5 → 0.8 (in `emit()`, line 232)
  2. Camera radius multiplier: 2.7 → 1.5 (in `render_term_movie`, line 36)
  3. Camera phi: -1.30 → -0.5 rad (in `render_term_movie`, line 36)
- Each run renders a 12-frame movie and evaluates with the standard watch prompt.

### 4.5 NOT authorized

- Changing physics.py cell-size law again
- Changing the lattice (cells, origin, cell_size)
- Changing the expected reading to match a texture question
- Changing the alignment threshold
- Running multiple experiments in one "fix" pass

## 5 · Next steps (gated by claim/reservation)

1. **Claim SHAPE-SILHOUETTE-02** through the control service with the preregistration above.
2. **Reserve isolated engine slot** (own build, own CWD, free port, `--no-restore`).
3. **Initialize DYAD** under THE_DYAD_PROTOCOL.md: one image per call, served model identity, physical context, non-leading questions.
4. **Run Experiment 1** (ground extent 0.8): render 12-frame movie, run dyad, record alignment and observed text.
5. **If Experiment 1 fails**, run Experiment 2 (camera radius 1.5) in a separate slot.
6. **If Experiment 2 fails**, run Experiment 3 (camera phi -0.5) in a separate slot.
7. **If all fail**, report precisely bounded unresolved result: the silhouette is recognizable in orthographic projection but not in the available perspective framing, and the fix requires a NEW preregistration for camera/scene redesign.

## 6 · Evidence archive

- `docs/evidence/shape_silhouette_02/shape_silhouettes_filled.png` — orthographic projections of current lattice and source cloud
- `docs/evidence/shape_silhouette_02/shape_silhouettes_vs_cloud.png` — lattice vs source cloud comparison
- `docs/evidence/shape_silhouette_02/preregistration.md` — this document
- `docs/evidence/shape_silhouette_02/geometry_freeze.json` — exact geometry snapshot (to be generated when claim is active)

## 7 · What this analysis does NOT do

- It does NOT change physics.py, numbers.json, or the lattice.
- It does NOT run runtime experiments without a claim/reservation.
- It does NOT substitute a texture question for silhouette acceptance.
- It does NOT relabel the subject to raise alignment.
- It does NOT widen the threshold or falsifier.
- It does NOT claim the dyad will pass — it preregisters a controlled test to isolate the cause.
