# BODY_ATLAS_SPEC — camera awareness for touch (agent G2)

Date: 2026-09-13 · Slot: slot-01 · Branch: `astra/tasks/matter-kernel-format-01`
Files: `tools/body_atlas.py` (builder/verifier), `tools/body_atlas.json` (the atlas, built output)
Engine contract: **GET-only against http://127.0.0.1:8107** — this tool never builds, starts or stops the engine.

## RULE 0 MEMBRANE (stated before the build)

- **STATEMENT**: the 28 pins of `.tmp/joints28.json` can each be mapped to a skin
  aim point that is within 5 cm of the actual surface, computed in one pass from
  `GET /verts`, with no trial-and-error probing of the body.
- **PREDICTION** (unmeasured at statement time): a 16-vertex same-facing disc
  anchored at each joint's nearest vertex has a centroid within 5 cm of the skin.
- **FALSIFIER**: run the builder; any pin with `|aim − nearest vertex| > 0.05 m`
  measured against `/verts` kills it. First build **failed the falsifier on 4
  pins** (worst 10.17 cm — see "the measured failure"); the anchor redesign was
  derived from that measurement. Final: **28/28 PASS, worst 4.17 cm.**

## WHY (the lead's #1 examination finding)

Every touch and capture required trial-and-error probing: nothing mapped body-part
names to skin coordinates. R4 had already measured the cost — a pack belly target
0.355 m from the nearest vertex is kernel-dead (press Gaussian is 3 cm) while the
engine answers `ok:true` with zero effect.

## THE LEAD WORKFLOW (no scanning)

```
python tools/body_atlas.py            # rebuild + verify (fresh pose snapshot)
python tools/body_atlas.py --verify-only   # re-check saved aims vs live skin
POST /tick_touch {"hit": <pins.neck.aim>, "force_n": 20000}
POST /tick_touch_clear {}             # release
```

Read `tools/body_atlas.json`, aim at the pin's `aim`, approach along `normal`
(`radial` is the whole-body-center fallback direction). The press lands on skin.

## INPUT LAYOUT

`GET /verts` → `[u32 n][f32 × 9n]`, 9 floats per vertex:
`pos[0:3] + unit normal[3:6] + color[6:9]` (color unused here; normals renormalized).
Measured live: n = 18459. `.tmp/joints28.json`: 28 pins, `{name, J, axis, ext, flex}`.
`GET /tick_state`: live sealed-cell y-bands, volumes, pressures (read at build time).

## DERIVATIONS (no taste numbers)

| choice | value | derivation |
|---|---|---|
| skin density | 18459 / 89.799 m² | n from `/verts`; area from `MATTER_KERNEL/SEAL_PREREGISTRATION` (divergence theorem) |
| mean vertex spacing | 6.97 cm | 1/sqrt(density) |
| patch size K | 16 verts | disc radius ≈ 15.7 cm ≈ 2.6× the 3 cm press-Gaussian footprint; big enough to average noise, small enough for one feature |
| anchor | joint's nearest vertex | the press must land on the skin closest to the joint |
| same-side filter | dot(n, n_anchor) > 0.35 | a patch must never straddle a limb or wrap a ridge |
| verify bar | 0.05 m | task bar; > press Gaussian (3 cm), the honesty limit |
| ambiguity flag | coherence < 0.55 or fallback | coherence = \|mean patch unit normal\|; low = wraps an edge/thin feature |

## THE MEASURED FAILURE (first build, kept honest)

Taking the 16 nearest verts **around the joint** failed for deep midline joints:
the patch is a ring around the body axis, its centroid sinks inside.
Measured: `spine_upper` 10.17 cm off skin, `spine_mid` 9.97 cm, `tail_base` 9.19 cm,
`neck` fell back to an unfiltered ring. Fix (derived, not tuned): anchor at the
joint's projection (nearest vertex) and take the compact same-facing disc around
the **anchor**. Post-fix worst pin: 4.17 cm. Recorded because the ring failure is
the general trap for any future joint→skin mapping.

## ATLAS SCHEMA (`tools/body_atlas.json`)

```
meta    base, fetched_utc, engine_ticks, n_verts, density, spacing,
        press_gaussian_m=0.03, verify_bar_m=0.05, patch params, pose note
bbox    min/max x,y,z over all verts      [-3.067,-0.020,-4.288] .. [3.067,9.971,1.853]
cells   the FOUR sealed cells (live /tick_state y-bands), each:
        y_band, V_m3, P_mpa, center (centroid of band verts), verts;
        the feet cell also carries center_L / center_R (one cell, two feet)
parts   for each of the 10 major parts (head neck chest belly hip_L hip_R
        knee_L knee_R foot_L foot_R): front (max z), back (min z),
        side_L (max x), side_R (min x) — exact mesh verts, on-skin by definition
pins    the 28: {"aim":[x,y,z], "normal":[x,y,z], "verts":N,   <- contract keys
                 "radial", "skin_m", "patch_m", "anchor_m", "coherence", "ambiguous"}
```

Cells measured this build (rest pose, gravity on, stance off, ticks 137313):
feet y[-0.02,0.338] V=0.2879 center [0,0.160,0.715] (L [0.932,0.160,0.715] / R [−0.932,0.160,0.715]);
shins y[0.338,1.903] (ankle→knee) V=0.3346; thighs y[1.903,3.415] (knee→hip) V=0.6930;
torso y[3.415,9.971] V=12.5091. The standing-pose hint (feet ≈ ±0.46, z ±0.3) does NOT
match the current slumped rest pose — the measured centers above are the truth at build time.

## VERIFICATION (this build)

28/28 pins within 5 cm of skin, `--verify-only` re-run against the live ticking
mesh: ALL PASS. Worst pins: mouth_R 4.17 cm, jaw 4.13 cm, mouth_L 3.41 cm,
shoulder_L/R 3.79 cm. Median pin ≈ 1.4 cm. Exit code is 0 iff all pins pass, so
the builder doubles as a gate.

## AMBIGUOUS PINS (honest report)

- **tail_base** — the tail-root/torso junction. The same-side filter found <4
  pool verts (junction normals fan out), so it fell back to the unfiltered pool;
  coherence 0.77. The aim is still ON skin (1.17 cm) and usable, but at a
  junction the "outward" normal is soft — for a crisp press prefer `tail_mid`.
- **spine_lower** — not flagged by the metrics (skin 3.01 cm, coherence 0.98),
  but its aim coincides exactly with `hip_L`'s (the pelvis-midline joint's nearest
  skin is the left hip crease). Touching "spine_lower" presses hip-L skin.
- Eyes-on caution for `jaw` / `mouth_R` (4.1 cm, thinnest margins) — still PASS.

## CAVEATS

- The body is alive: the atlas is exact for the pose at `fetched_utc`. Re-run the
  builder after any pose change; `--verify-only` is the cheap drift check.
- Units are engine meters (creature ≈ 10 m tall; press Gaussian 3 cm).
- Patch sizes vary (7–16 verts) where the same-side filter trims curved or
  multi-layer regions; `verts` and `patch_m` report the actual patch per pin.
