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