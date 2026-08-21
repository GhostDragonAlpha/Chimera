# THE SPACE — the canonical environment (declared 2026-08-21)

> Operator: *"We need to think about this with the CAD mentality — we're actually
> measuring. Generate 1cm when needed, 1m when needed. PCA wobble means we don't have
> a stable platform. We have to think about not only the splats but the empty space
> in which they exist."*

This document is the law of WHERE things are. Before it, every stage picked its own
frame (SV3D's gauge, gsplat's silent normalization, PCA's statistical axes, the
viewer's default camera) and "alignment is off" was the inevitable symptom. After it,
there is ONE space, everything carries its frame in writing, and a render that
disagrees with the sidecar is a bug in the tool, not a matter of taste.

## The canonical frame

- **Units are meters.** 1 world unit = 1 meter, real scale. A 35cm plush is 0.35
  tall; a landscape is hundreds. Generation and CAD tools must be able to produce a
  1cm feature or a 1m feature on demand — scale is a declared quantity, never an
  artifact of whichever model ran last.
- **Axes:** right-handed, **+Y = UNIVERSE_UP**, **+Z = front** (the default camera
  sits on +Z looking at the origin), +X = right. This matches the commanded-orbit
  convention in `tools/sv3d_to_colmap.py`, so capture lands in canonical space by
  construction.
- **The empty space is standardized too.** Camera rings, scene bounds, and gravity
  fields are defined in the same metric frame. A capture rig is a measured object:
  orbit radius, elevations, and focal length live in `poses.json` in canonical units.

## The three ups

1. **UNIVERSE_UP** = +Y. Fixed. The frame everything is written in.
2. **GRAVITY_UP** = local, per-body (a planet's surface normal at your feet). For
   development, GRAVITY_UP is DECLARED equal to UNIVERSE_UP. When a body with its own
   gravity exists, it is a property of that body, not of the universe.
3. **OBJECT_UP** = per-asset metadata: the asset's intrinsic up in its bind pose
   (a teddy's feet→head axis). It exists for ORIENTATION, not gravity — when an
   object is set down on a planet, whether it keeps standing is a locomotion/physics
   question the legs answer; OBJECT_UP is how the rest of the system knows which way
   the thing faces before physics runs.

## The sidecar: `space.json`

Every asset carries a `<name>.space.json` beside it:

```json
{
  "units": "meters",
  "up": [0, 1, 0],
  "front": [0, 0, 1],
  "height_m": 0.35,
  "transform_to_canonical": "identity | 4x4 row-major, written by the converting tool",
  "provenance": ["cut_anchor", "sv3d ring eq x21", "gsplat 30k", "export pinned-frame"]
}
```

## The rules

1. **No silent normalization, anywhere.** A tool that changes an asset's frame writes
   the transform it applied into `transform_to_canonical`. The trainer's
   camera-align + init-cloud-PCA normalization is DISABLED for our datasets
   (`normalize_world_space: false`); the commanded orbit IS the frame.
2. **PCA is a measurement, never an orientation.** Statistics may REPORT an asset's
   axes; they may not CHOOSE them. Orientation comes from the capture rig's commanded
   poses or the author's hand.
3. **Falsifier for every conversion:** render the asset from the canonical front
   camera; if it does not match the sidecar's up/front/height within tolerance, the
   converting tool lied. Report, don't patch.

## Capture density standard

Photogrammetry earns its name at hundreds of agreeing views, not tens. Single-pass
consistency beats multi-pass count (measured 2026-08-21: 5 independent rings = mush,
1 ring = coherent, train loss 0.030 vs 0.004). The target: single-pass or jointly-
generated view sets in the hundreds — the simultaneous-multi-view generation problem
the orbit lane is driving at.
