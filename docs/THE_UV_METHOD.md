# THE UV METHOD — CAD triangles ↔ 2D material sheets

*2026-08-22. Commissioned by the operator under the scoped doctrine amendment
(`SESSION_LOG_2026-08-22.md`): AI is admitted at ONE slot — the 2D material
sheet — and nowhere else. Geometry is authored (CAD), physics is kernel-native,
signals (gait, later UV layout) are evolved locally. This file owns the flow
that binds the CAD triangle skin to 2D UV material sheets, and the
pre-registered tests that prove each link before the next is built.
Research backing: `research/2026-08-22_local_uv_generation_models.md`.*

## THE FLOW (five links, each one gated)

```
CAD part (parametric grid)          link 1: UV      -- analytic, no unwrap
   -> TEXCOORD_0 per vertex
MATERIAL SHEET (per material)       link 2: SHEET   -- placeholder first,
   (fur / sweater / eye / nose)                AI generator drops in later
   -> extraction                    link 3: EXTRACT -- per-region color/relief
      statistics (the splat-era qualification, triangle carrier)
   -> application                   link 4: APPLY   -- sheet sampled at UV,
      baseColorTexture on the GLB
   -> verification                  link 5: VERIFY  -- numbers round-trip +
      the operator's eyes (dyad; he authorizes every transition)
```

Decisions recorded:

- **Analytic UVs, not unwrapped UVs.** Every CAD primitive is already a
  parametric grid (ellipsoid: phi/theta; capsule: row/theta). UV is index
  arithmetic — there is no unwrap step, no Blender, one known seam (the theta
  wrap) per part. The atlas is one tile per part, 5x4 grid for 19 parts;
  parts that share a material sample the same SHEET through different tiles.
- **The sheet is the only AI slot.** Placeholder (procedural, known
  statistics) proves the chain first; then SD 3.5 Medium / DreamMat output
  replaces the placeholder at link 2 with zero downstream changes.
- **Evolved UVs come later.** The analytic layout is the baseline; the atlas
  packing / distortions are a future evolution target, exactly like the gait
  signal. Not before link 5 passes on the baseline.
- **Extraction inherits the splat-era lessons**: qualify by color region
  (hue-wheel range per label), density/thickness window, margin cut at
  contact zones, and the 0-100 "does this look like X" scoring ladder —
  carrier is triangles now, criteria unchanged.

## PRE-REGISTERED TESTS

### TEST A — UV correctness (link 1)

- **STATEMENT**: analytic UVs from the parametric grid are injective per part
  (no two surface points share a texel except at the known theta seam and the
  poles) and low-distortion.
- **PREDICTION**: per part, max/min texel density ratio inside a bound named
  here: ellipsoid/capsule-caps <= 1.5 x (r_max/r_min)^2 x RING/pi (~15.3 at
  RING=32 — ERRATUM, pre-data: the first bound omitted the phi/theta grid's
  inherent pole distortion, 1/sin(pi/RING) ~= RING/pi; caught before the
  run, bound fixed forward); capsule WALL band = 1.0 exactly (developable).
  Degenerate pole triangles (zero 3D or UV area) are counted, not measured.
- **FALSIFIER**: any off-seam UV adjacency tear (UV jump > 2x the local
  parametric step between grid neighbors), or area ratio above the bound ->
  the analytic map is wrong; successor = per-part relaxation, still local.

### TEST B — chain proof (links 2-4, placeholder sheet)

- **STATEMENT**: a sheet with KNOWN statistics survives the round trip
  sheet -> extract -> apply -> render measurably unchanged.
- **PREDICTION**: placeholder = per-material procedural sheet (known mean/std
  RGB per channel + a 16 px checker for spatial identity). After apply, the
  rendered part's measured channel stats match the sheet's within 2/255 per
  channel, and the checker phase is recoverable (spatial correlation > 0.9).
- **FALSIFIER**: stats drift beyond tolerance or the checker is
  unrecoverable -> a link is lossy; the failing link is named by which
  measurement broke.

### TEST C — generator slot (link 2, the AI sheet)

- **STATEMENT**: SD 3.5 Medium (local, access granted) generates a seamless
  tileable plush-fur sheet at 1024px on the 4090 alongside the training load.
- **PREDICTION**: generation completes in VRAM without OOM; tileability
  measured as edge-wrap mean |delta| < the sheet's internal local std.
- **FALSIFIER**: OOM at fp16 with the training resident, or edge-wrap error
  above the bound -> successor = fp8/sequential scheduling, or DreamMat for
  the mesh-fitted route. The eye (does it read as fur) is the operator's
  call at link 5, not this test's.

*Results get recorded below this line, never above it.*

---

## RESULTS

### TEST A, RUN-1 (uniform-theta v) — **FAIL**, falsifier fired 2026-08-22

Tears: **zero on all 19 parts** (injective off-seam holds). Distortion: every
part broke the bound — ellipsoids 398–599, capsules 7682–14007, feet 2785,
vs bounds 15–29. The ERRATUM bound was still an order of magnitude short:
uniform-theta v gives per-strip UV area constant while 3D strip area falls
like sin(phi) all the way to the pole, so the worst non-degenerate pole
triangles carry density ~1/sin^2 near the fan, not ~1/sin. The uniform-v
analytic map is wrong for a fur sheet (fur density would thin exactly where
the eye reads it — muzzle top, head crown). **Successor named before the
rerun: TEST A2, equal-area v.**

### TEST A2 — equal-area v (PRE-REGISTERED before its run)

- **STATEMENT**: setting each grid row's v from the *measured cumulative
  strip area of the tessellation itself* (v[row] = sum of strip 3D areas up
  to row / total area) makes texel density constant across the whole part.
- **PREDICTION**: per-part max/min density ratio <= 2.0 on all 19 parts.
  Derivation: by rotational symmetry every quad in a strip is congruent, so
  equal-area strips give density identically 1 up to quantization — EXCEPT
  ellipsoids with r_x != r_z, whose surface element varies within a strip by
  up to (r_x/r_z)^2; measured from PRIMS that factor maxes at 1.89 (nose),
  next 1.74 (torso). Bound 2.0 covers 1.89 + quantization. Tears stay zero;
  tear criterion revised for the variable dv: column neighbors must share u
  exactly with v strictly increasing down-column; row neighbors must step
  exactly du (the properties that matter — uniformity of dv was never load-
  bearing).
- **FALSIFIER**: any part ratio > 2.0, or a tear -> successor = per-quad u
  weighting (u step varies with theta to match the local metric).

### TEST A2, RUN (equal-area v) — **FAIL**, falsifier fired 2026-08-22

Tears: 0 on ellipsoids, **48 on every capsule**; ratio stuck at ~140.5 on
EVERY part (bound 2.0). Both symptoms diagnosed from the numbers, not
guessed:

1. **The theta-seam triangles wrap the whole tile.** With u = j/SEG and
   j2 = (j+1) % SEG, the wrap quad's UV spans u = 47/48 -> 0, i.e. the full
   tile width. Those triangles' auv is 47x normal -> they are the density
   minimum, and the ratio 140.5 = 47 x (fan factor ~2) x (anisotropy ~1.5)
   is EXPLAINED, part-independent, exactly as measured. In a real renderer
   (REPEAT wrap interpolates through the middle) this is a full-tile smear
   across the bear — a genuine defect the test caught, not a measurement
   technicality.
2. **Capsules carry a coincident equator ring**: the explicit ring@b AND the
   top cap's first row (phi = pi/2) are the same circle -> a zero-area strip
   -> dv = 0 -> 48 "not strictly increasing" tears. 192 degenerate triangles
   per capsule = 96 pole-fan + 96 zero-strip, confirmed by count.

Successor named before the rerun: TEST A3.

### TEST B, RUN-1 — **FAIL**, falsifier fired 2026-08-22

All 19 parts: |dmean| ~6-11.5/255 (tol 2/255), checker corr 0.35-0.74 (tol
0.9). Diagnosis: the test compared a VERTEX-SAMPLED chain render against a
PER-PIXEL reference. Vertex sampling discards sub-triangle sheet content by
construction — with a 16px checker + std .04 noise the measured dmean ~0.036
IS the sheet's high-frequency energy, not a chain defect. The real renderer
(UE) samples per-pixel at interpolated UV — the reference side of my own
comparison. Category error, caught by the falsifier. The extract link itself
passed silently: sheet tile stats match the known MAT statistics exactly
(fur mean 114.78 vs 0.45*255=114.75; std 16.33 vs sqrt(.04^2+.05^2)*255 =
16.3). Successor: TEST B2.

### TEST A3 — duplicated seam column, no zero strips (PRE-REGISTERED)

- **STATEMENT**: giving the theta seam its own column (j = SEG duplicates
  j=0's position with u = 1.0 — the standard UV cut), removing the
  coincident capsule equator ring, and keeping equal-area v yields an
  injective-except-pole-fan UV with constant texel density per quad.
- **PREDICTION**: per-QUAD max/min density ratio <= 2.0 on all 19 parts
  (per-quad = the fan's half-cell pairs with its degenerate twin, so the
  fan factor-2 cancels; residual = within-strip (r_x/r_z)^2 <= 1.89, nose).
  Per-triangle ratio reported for transparency (bound 4.0 = 2 x 1.89).
  Tears = 0 with the cut checked explicitly: j=0 and j=SEG share 3D position
  and v, differ by exactly 1.0 in u. Degenerate triangles only at pole fans
  (96 per ellipsoid, 96 per capsule — zero strip gone). Tessellation
  conservation: per-part surface area and volume equal to the pre-A3 mesh
  (git HEAD tessellation) within 1e-4 relative — seam duplication adds no
  surface, removing a zero-area strip removes none.
- **FALSIFIER**: quad ratio > 2.0, any tear, a broken cut, or area/volume
  drift -> successor = per-quad u weighting or a different primitive map,
  named from which measurement broke.

### TEST B2 — chain proof through the actual GLB artifact (PRE-REGISTERED)

- **STATEMENT**: the GLB we write carries the mapping we computed: TEXCOORD_0
  read BACK out of models/cad_bear/cad_bear_uv.glb reproduces the analytic
  packed UVs, and a per-pixel render through the read-back UVs equals the
  per-pixel reference.
- **PREDICTION**: max |duv| readback < 1e-6 (float32 round-trip only);
  per-pixel renders: |dmean| < 2/255 per channel, checker corr > 0.99.
- **FALSIFIER**: drift beyond either bound -> the GLB writer/packing link is
  lossy; the failing measurement names it (readback mismatch = writer bug;
  render mismatch = interpolation/packing bug).

### TEST A3, RUN — **PASS** 2026-08-22

All 19 parts: tears = 0, cut clean (j=0 vs j=SEG share position and v,
delta-u exactly 1.0), degenerate triangles exactly 96 everywhere (pole fans
only — the capsule zero-area strip is gone), per-quad density ratio
1.000-1.370 (bound 2.0; worst = nose, exactly the (r_x/r_z)^2 = 1.89
anisotropy ranking predicted, absorbed below bound by equal-area v).
Per-triangle ratio 2.99-3.00 = the pole-fan half-cell factor, as predicted.
Tessellation conservation vs the pre-A3 mesh (git HEAD): worst per-part
surface-area and volume drift 3e-16 relative (bound 1e-4) — machine epsilon.

### TEST B2, RUN — **PASS** 2026-08-22

Readback of TEXCOORD_0 from the written cad_bear_uv.glb: |duv| = 0.0 exactly
on all 19 parts (bit-exact float32 round trip). Per-pixel render through the
read-back UVs vs the per-pixel reference: dmean = 0.000/255 every channel,
checker corr = 1.0000 every part. The chain analytic-UV -> atlas pack ->
GLB write -> GLB read -> surface render is exact. Link 3 EXTRACT against
known statistics: fur mean (114.78, 76.49, 45.89) vs known (114.75, 76.5,
45.9), std (16.33,16.29,16.34) vs known sqrt(.04^2+.05^2)*255 = 16.32.

**Links 1, 3, 4, 5 are proven. Link 2 (the sheet itself) is the open gate:
TEST C admits the first AI-generated sheet.**

### TEST C, RUN-1 — **FAIL** (falsifier fired) 2026-08-22

fp16 fit alongside the training load (17.5 GiB, no OOM; 11 s for 28 steps at
1024px). The image itself reads as dense dark-brown plush fur, no shadows or
borders (operator's eye pending). But the sheet is NOT seamless: edge-wrap
mean|delta| = 19.23/255 vs internal local mean|delta| = 14.30/255 (ratio
1.34 — the wrap boundary is a third harsher than interior variation). A
prompt alone cannot promise seamlessness; the network pads its convs with
zeros, so edges are always special. Successor: TEST C2.

### TEST C2 — circular-padding generation (PRE-REGISTERED)

- **STATEMENT**: flipping every Conv2d in the denoiser transformer and the
  VAE decoder to padding_mode="circular" makes the latent/feature maps wrap
  by construction, so the generated sheet is seamless not by luck but by
  architecture.
- **PREDICTION**: same model/prompt/seed budget; edge-wrap mean|delta| <=
  internal local mean|delta| (ratio <= 1.0). VRAM unchanged (no new
  tensors). Quality (reads as fur) unchanged to the eye.
- **FALSIFIER**: ratio still > 1.0, or visible degradation -> successor =
  post-hoc mirror-blend of the RUN-1 sheet (deterministic, always seamless,
  costs a visible symmetry axis), or DreamMat mesh-fitted route.

### TEST C2, RUN — **PASS** 2026-08-22

55 conv layers flipped to circular padding (transformer + VAE decoder), VRAM
unchanged (17.5 GiB alongside training), 11 s generation. Edge-wrap
mean|delta| = 11.76/255 vs internal 14.17/255, ratio 0.83 (bound <= 1.0) —
the wrap boundary is now SMOOTHER than the interior average. Sheet:
models/materials/fur_sd35_testc2.png.

### LINK-2 GATE, OPERATOR VERDICT (2026-08-22): the RUN-1 LOOK

The operator judged both sheets: **the shorter-fiber RUN-1 sheet reads more
like a teddy bear** (his words: "the shorter fur looks better, more like a
teddy bear"). The approved look is fur_sd35_testc.png — but that sheet is
the one that failed seamlessness (ratio 1.34). The human terminal has ruled
on taste; the physics gate on wrap still stands. Successor: TEST C3.

### TEST C3 — seamless-ify the APPROVED sheet (PRE-REGISTERED)

- **STATEMENT**: a deterministic offset + cosine cross-fade (the classic
  make-seamless: roll by half a tile, feather the seam band) applied to the
  APPROVED RUN-1 sheet makes it tile while preserving its statistics and
  look — no regeneration, no seed lottery.
- **PREDICTION**: edge-wrap mean|delta| <= internal local mean|delta| (ratio
  <= 1.0) on the output; per-channel mean/std drift < 2/255 vs the approved
  sheet (the blend must not wash out the contrast he approved).
- **FALSIFIER**: wrap ratio > 1.0 or stats drift beyond tolerance -> the
  blend band is eating the sheet; successor = narrower feather band, or
  circular-padding regeneration steered at the short-fiber look with a fixed
  seed set (and the operator re-judges).

### TEST C3, RUN — **FAIL** (falsifier fired) 2026-08-22

Wrap ratio 1.06 (bound 1.0), stats drift dmean 5.32/255 (tol 2.0).
Diagnosis: cross-fading two UNCORRELATED fur fields double-exposes the
fibers across the whole 10% band (~19% of the image), which both washes the
contrast he approved and dilutes the internal-delta denominator. A narrower
band only trades one symptom for the other (wrap stays ~14.4, internal rises
back to ~14.3, ratio ~1.01 — still on the wrong side). Blending is the wrong
tool for uncorrelated texture; seamlessness must come from the generator,
not the filter. Successor as named: TEST C4.

### TEST C4 — circular generation, short-fiber steering, 4 fixed seeds
### (PRE-REGISTERED)

- **STATEMENT**: the C2 architecture (circular padding) already proved
  seamlessness (0.83); the RUN-1/C2 look difference was seed luck, not
  architecture. Generating 4 candidates with the approved short-fiber prompt
  at fixed seeds (0,1,2,3) gives the operator a real choice among sheets
  that ALL pass the wrap bound.
- **PREDICTION**: every candidate has wrap ratio <= 1.0; generation cost
  ~45 s total (4 x 11 s, one pipeline load). Output: 4 PNGs + one 2x2
  contact sheet for the operator's verdict.
- **FALSIFIER**: any candidate ratio > 1.0 -> the circular-padding claim was
  seed-luck, remeasure; if NONE please his eye -> DreamMat mesh-fitted
  route, or prompt surgery (pile length terms) and another seed set.







