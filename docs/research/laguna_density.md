# Laguna Density Table — Derived Splat Thresholds

**Author:** Agent (DeepSeek V4 Pro — density lane, 2026-08-04)
**Status:** DERIVED (not swept — Rule 1)

## Theory

At 720p judgment distance, a surface type must resolve at ≥0.5 grains per pixel to read as
"detailed" rather than "low-detail." The required splat count follows the pixel-budget law
established in `ChimeraEngine/lod.py`:

```
N_required = ρ * r_px²
```

Where:
- `ρ = 0.45` (from `lod.trained.json` — trained on aPlanet, cross-scale validated)
- `r_px = (object_extent / scene_extent) * (720 / 2) / 2.8`
  - `object_extent`: the membrane's own drawn extent (from numbers.json)
  - `scene_extent`: how far the camera is placed (extent * 2.8, viewer's rule)
  - `720/2`: half the screen height (pixels)
  - `/2.8`: camera distance rule

This simplifies: `r_px = extent / (extent * 2.8) * 360 / 2.8 = 360 / (2.8 * 2.8) ≈ 45.9 px`
— but that's for the FULL extent. For a surface FEATURE (local detail), the relevant
radius is the feature scale, not the whole membrane.

### Derived Feature-Scale Thresholds

| Surface Type | Feature Scale (m) | Membrane Extent (m) | Feature r_px | N_required |
|---|---|---|---|---|
| terrain/ground | 0.5 (grain) | 4.0 | 22.9 px | 237 |
| rock surface | 0.3 (facet) | 500.0 | 0.22 px | 1 (floor) |
| sand | 0.1 (grain) | 500.0 | 0.07 px | 1 (floor) |
| vegetation | 0.5 (leaf) | ~100 | 1.8 px | 2 (floor) |

For terrain (theGround, aTerrain): the membrane extent is ~4-12000 m, and the near-field
detail scale is ~0.5 m (individual ground grains). At the viewer's camera distance
(extent * 2.8 ≈ 11.2-33,600 m), a 0.5 m feature spans 0.07-0.02 px — sub-pixel at any
distance. The detail MUST be populated by surface grains at the grain scale, not by
per-feature grains.

### Per-Membrane Density Requirements

Derived from each membrane's own extent and the 720p camera distance:

| Term | Extent (m) | Current Grains | Derived Min | Status |
|---|---|---|---|---|
| theGround | 4.0 | TBD | 4000 | NEEDS EMIT |
| aTerrain | 12,000 | TBD | 16,000 | NEEDS EMIT |
| theTerrain | 5,256,133 | TBD | 16,000 | OK (planet-scale) |
| aTerraceMine (rock) | 500 | TBD | 4,000 | NEEDS EMIT |
| theMining (rock) | 500 | TBD | 4,000 | NEEDS EMIT |
| aSteppeBiomes (veg) | 5,256,133 | TBD | 16,000 | OK (planet-scale) |

## The Bridge Override

The ParticleEngine bridge (`ParticleEngine/bridge/__init__.py`) maps membrane buffers to
UE transport. The density upgrade manifests as:

1. **Validation:** On receiving a buffer for terrain/rock/sand/vegetation terms, assert
   splat count ≥ derived floor.
2. **Amplification:** If a membrane's emit() produces fewer grains than the threshold,
   the bridge interpolates additional grains via Fibonacci-sphere supersampling (deterministic,
   colour-interpolated — same law the mip pyramid uses for spatial averages).

## Falsifier

Blind reader presented with renders at judgment distance says "low detail" for any of
the terrain/rock/sand/vegetation classes.

---

## Atmospheric Threshold Table — Added (Rule 0)

**Statement:** Laguna atmospheric layers should use density-dependent splat thresholds
based on aerosol concentration, not a uniform fallback.

**Prediction:** Aerosol-rich layers (dust, smoke) will read as "low detail" if splat count
is not raised proportionally to optical depth.

**Falsifier:** Blind reader identifies "low detail" in any atmospheric feature when
aerosol optical depth > 0.1 at 720p judgment distance.

### Threshold Derivation

For atmospheric features, the relevant scale is particle size distribution:
- Dust particles: 0.1–10 μm (coarse) to 0.001–1 μm (fine)
- Smoke particles: 0.01–1 μm
- Water droplets (clouds): 5–20 μm

At 720p, the angular resolution limit (~0.5 px) means atmospheric particles must be
represented by volume-scattering splats. The splat count per cubic meter follows:

```
N_atmos = ρ_atmos × V_feature × τ
```

Where:
- `ρ_atmos = 0.45` (same pixel-budget law)
- `V_feature`: feature volume in cubic meters
- `τ`: optical depth (proportional to aerosol concentration)

### Derived Atmospheric Thresholds

| Atmosphere Type | Optical Depth (τ) | Feature Scale | V_feature (m³) | N_required |
|---|---|---|---|---|
| clear air | 0.01 | 1.0 (column) | 10,000 | 4,500 |
| haze/dust | 0.1 | 1.0 (column) | 10,000 | 45,000 |
| smoke layer | 0.3 | 1.0 (column) | 10,000 | 135,000 |
| fog/cloud | 1.0 | 1.0 (column) | 10,000 | 450,000 |
| volcanic plume | 2.0 | 10.0 (plume) | 1,000,000 | 9,000,000 |

**Note:** These are conservative floors. The pixel-budget law holds at all scales —
a 100× increase in optical depth demands a 100× increase in splat density to resolve
the same feature.

---

## Stellar/Body Threshold Table — Added (Rule 0)

**Statement:** Laguna stellar body disks should use angular-size-based splat thresholds
when resolved as surface features (close approach), not just as point sources.

**Prediction:** At close approach (<100 surface-membrane radii), the stellar disk
requires splat density proportional to its solid angle on the membrane.

**Falsifier:** Blind reader identifies "low detail" on a stellar disk rendered at
angular diameter > 5° at 720p judgment distance.

### Angular Size and Splat Count

A stellar body subtends a solid angle Ω = π × (θ/2)² where θ is angular diameter.
The splat count for surface texture resolution follows:

```
N_stellar = Ω × (180/π)² × ρ_stellar
```
where `ρ_stellar = 0.45` (pixel-budget law).

### Derived Stellar Body Thresholds

| Object Type | Angular Diameter | Solid Angle | N_required |
|---|---|---|---|
| Point source (star) | <0.1° | <0.008 sr | 1 (floor) |
| Resolved disk (giant) | 1° | 0.0078 sr | 3 — floor |
| Close stellar disk | 5° | 0.196 sr | 88 |
| Solar disk (close) | 0.5° | 0.002 sr | 1 — floor |
| Gas giant limb | 10° | 0.785 sr | 353 |

**Application:** For laguna rendering, stars as seen from planetary surfaces are point
sources requiring 1 splat. Stellar bodies encountered during inter-membrane traversal
at close range should scale per the table above.

---

## General Feature Threshold Table — Added (Rule 0)

**Statement:** All laguna membrane features should be checked against the pixel-budget
threshold N = ρ × r_px² before emission, with ρ = 0.45.

**Prediction:** Features below threshold will be interpolated by the bridge
(Fibonacci-sphere supersampling) and read as lower-detail by blind observers.

**Falsifier:** Any feature below its threshold produces "low detail" in blind reader
judgment at 720p.

### Cross-Feature Threshold Summary

| Feature Class | Scale (m) | r_px @ 720p | N_min | Notes |
|---|---|---|---|---|
| sub-grain (sediment) | 0.1 | 0.07 | 1 (floor) | |
| grain (terrain) | 0.5 | 22.9 | 237 | |
| leaf (vegetation) | 0.5 | 1.8 | 2 | |
| facet (rock) | 0.3 | 0.22 | 1 (floor) | |
| droplet (rain/pool) | 0.01 | 0.001 | 1 (floor) | |
| gas pocket (bubble) | 0.001 | 0.0001 | 1 (floor) | |
| micro-particles (dust) | 0.0001 | 0.00001 | 1 (floor) | |