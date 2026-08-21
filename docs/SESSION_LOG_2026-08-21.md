# SESSION LOG 2026-08-21 — the sectioning method is declared and locked

## What happened, in order

1. Resumed mid-iteration on bear-34 region labels (post-compaction). Judged round-4
   shots; labels anatomically clean. Added eye regions from MEASURED dark-splat
   clusters (two clusters at y=0.109, symmetric about the measured head center
   x=-0.047) — not eyeballed.
2. `tools/label_regions.py` committed (e903f83): ellipsoid base spec, labels traced on
   the outer membrane, stable NAME-keyed colors (spec edits never reshuffle palette).
3. Operator rulings, in force:
   - Donor = pajama bear (CO3D 34) — YES. Torso genome will be printed flannel, head/
     paws/feet are fur; two material classes from one donor, technique must handle both.
   - Sectioning must be part of the CAD process — it is: labels live on splats
     (authoritative), both CAD membranes inherit by nearest splat.
   - *"Take the original object, not the circle-sphere object"* — the first chalk
     renderer drew circular dots (the "orbs" the operator correctly rejected); v2
     renders true projected-covariance ellipses.
   - The technique must run photogrammetry-style: circle each part from MANY angles,
     intersect the views; contamination that can't be circled twice dies (SfM logic).
   - Add the stick figure: a skeleton drawn INSIDE the bear, adjusted per view the
     same way as the chalk — recursive co-improvement; the marks files accumulate as
     the training record for a future auto-marker.
4. Format dispute settled BY MEASUREMENT: co3d_34.splat = 84,589 splats x 32 bytes,
   decodes to 14 floats (pos3 rgb3 alpha1 scale3 quat4), anisotropy median 6.9 /
   p90 28.8, quats non-identity (|w| median 0.519). NOT 7-variable. The real loss vs
   the training PLY is dropped spherical harmonics (flat RGB) — noted, not blocking.
5. Built `tools/lasso_label.py` (the tailor's chalk): subcommands render/sheet/skel/
   apply. Ops: set / replace (redraw releases old members, refill nearest) / sub;
   surface_only front-layer picking per pixel; multi-view INTERSECTION; --denoise
   off-membrane drop; hierarchy recorded in the labels JSON.
6. Whole-body chalk pass (`tools/specs/bear34_chalk2.json`): 16 regions incl. paw_L,
   foot_L, foot_R. First intersections caught two of my own aiming errors (ear_L
   front∧left = empty; paw_L = 20 splats) — the method rejecting bad second views,
   working as designed. Fixed to single-view slabs for those; final counts sane
   (snout 1657 > nose 342; eyes 151/191; feet ~1800 each; torso 12,113).
7. Skeleton (`tools/specs/bear34_skeleton.json`): 16 joints, pixel-marked across
   front/right/left, least-squares triangulated. First-pass reprojection RMS
   1.5–20 px; all joints measured inside the body (0–28 mm from core surface).
   Overlay verified on all six sheet tiles — the figure sits inside the bear.
8. Committed b8f04b7. Presented chalk + skeleton + labeled result on one page.
   **Operator: "Yes that's more like it. We now have our methodology locked in
   place."** — documented in `docs/THE_SECTIONING_METHOD.md`; pointer added to
   THE_AUTHORED_PIPELINE.md (Trainable COAT extracts PER REGION, post-sectioning).

## State

- Donor: `models/co3d/co3d_34.splat` + `bear34_shells.npz` + `bear34_labels.json`
  (16 regions, hierarchy, splat/membrane/core labels) + `bear34_skeleton_solved.json`.
- Restart incident mid-session: no work lost (all committed); viewer server + browser
  tasks were relaunched.

## Next

- Per-label margin genome extraction (patches relative to the inner core).
- Spray: rebuild bear 34 from its own genomes onto its own core (reconstruction
  test — must pass before any novel body).

## Late session — the Authored Parts pipeline (operator-directed, locked)

1. **Parts plan** (`tools/specs/bear34_parts_plan.json`): one part at a time, each =
   analytic primitive + material + connection point. Exploded parts diagram at the end.
2. **Material concept training** (`tools/train_material.py`): selection by chromaticity +
   log-intensity k-means (extract_materials' law: never raw RGB); GMM over
   [rgb, log scale, h, alpha]; likelihood floor (p1) + per-channel color box (p1/p99) +
   fiber-length cap (p99) + real q_local bootstrap. `fur_brown` trained from head cluster 6
   (lit tan fur, n=1623). Registry: `models/co3d/materials/library.json`.
3. **Zero convention (operator)**: zero = the INNER MEMBRANE along its average normal.
   fit_parts now fits primitives to `shells["inner"]` (hard beads eyes/nose keep shell
   fit — they sit proud); cut_patches flattens each patch to a robust plane through the
   membrane points of the window; application zero = extraction zero by construction.
4. **Tip line (operator)**: per-material elevation cutoff where the h-histogram drops
   below 2% of peak — covers the tips, deletes floaters. Measured: head 8.5mm,
   ears ~3mm, feet ~11.5mm. Wired through extraction -> training -> spray clamp.
5. **14-variable gate is code**: loaders REFUSE any sample without full 14-var 3DGS
   (anisotropic scale + unit quats). "Find a different sample."
6. **Corpus** (`tools/cut_patches.py`): 281 flat reference-plane patches from bear 34
   fur regions, (N=512, 14 feats), membrane-plane zero.
7. **Donor pipeline** (`tools/donor_corpus.py`): one command per donor (14-var gate ->
   shells -> whole genome). Bear 187 processed: 59,571 splats — but it is a DIRTY donor
   (black background clouds; 25k-splat pure-red interior artifact, invisible from
   outside, auto-excluded by the patch h-window). Recoverable materials: grey fur,
   magenta fabric.
8. **MCP integration**: parts pipeline exposed on the chimera-engine server —
   `parts_fit`, `part_spray`, `material_clusters`, `material_train`, `corpus_cut`,
   `parts_status` (subprocess wrappers over tools/*.py under .venv-gs).
9. Torso sprayed from the fur_brown concept on the membrane zero: 16,195 splats,
   uniform tan, no decal bleed, verified six-view sheet.

## Next

- Large corpus: more donors (52GB CO3D teddybear category; gs-library), then the
  conditioned point-field generator (flow matching over attributed splat patches).
- Fix eye/nose label bleed (rod fits), leg bones for the sitting pose.
- Remaining parts one at a time; exploded parts diagram.

## Qualification gate calibrated (evening)

The eye rejected 100% of corpus patches across three renderer attempts; each
failure was traced to PRESENTATION, not data:

1. Hard-polygon renderer -> shards (renderer artifact; replaced by render_soft,
   a numpy Gaussian-falloff rasterizer).
2. render_soft at 4cm/640px -> still rejected. Ground truth through the REAL
   viewer (patch_gt.splat in viewer.html) showed a soft fur tuft: the numpy
   renderer was the liar. Rule: qualification renders go through the real
   viewer, always (`--via viewer`, tools/qualify_shots.js, one headless browser
   session for the whole batch; #loading/#hud hidden via addInitScript).
3. Even truthful renders rejected when the window is shown past NATIVE
   resolution. gsplat trains at ~1 px per splat footprint (~0.8mm); presenting
   a 10cm window at 640px shows gaps the data never had. Verified by cropping a
   fur region from the whole-bear render at native scale: eye said YES
   immediately ("dense, fuzzy texture consistent with teddy bear fur").
   Presentation is now native-res (window ~150px) + crop + upscale.
4. Patch ISOLATION removed the backing layer: H_MIN was -3mm, so gaps had no
   backing and read as holes. H_MIN now -10mm (the full fur column; zero is
   still the membrane, backing gives opacity on application).
5. Corpus labeling bug: torso/arm/leg regions on bear 34 are the red floral
   PAJAMA, not fur. Fur corpus = head, ears, snout, paws, feet only.
6. Needle outliers: SCALE_CAP 3mm at cut time (tip-line for size).

Corpus re-cut: PATCH_HALF 0.020->0.050 (10cm material-scale windows, the
operator's "larger patches read better"), N_PTS 512->2048, 60% 2D-occupancy
gate (6x6 grid) kills edge-band windows. bear34: 20 patches; bear187: 30.

co3d_34_mcmc (520k splats) is GARBAGE: median scale ~0 (point dust), whole-bear
render is a dark fragment with red interior bleed. Its donor directory exists
but is excluded from qualification. Recorded so nobody trusts it.

Full eye qualification of the 50-patch corpus runs through the real viewer;
report.json is written incrementally every 10 patches (a crash loses nothing).

NEXT: train bear 598 (dataset ready, 202 images) with DefaultStrategy tuned for
density; unzip teddybear_002 (19GB, ~40 bears) for the donor pool.

## Source-hunt lane (evening, operator ruling)
- OPERATOR RULING: candidates are judged as FINISHED 3DGS files (.ply/.splat), never raw
  photogrammetry. "We can't sort through people's photogrammetry -- we sort through people's
  end results." CO3D self-training lane demoted to fallback.
- PLAYWRIGHT IS MANDATORY in the hunt lane: the AI never judges what it has not seen; the
  human sees the same pixels through the same viewer. Built: tools/hunt_shot.js
  (page|splat modes) + MCP tools hunt_view / hunt_fetch / hunt_stage in
  ChimeraEngine/mcp_server.py. Documented in MCP_ENGINE.md ("The source hunt").
- Engine UI SOURCE tab now carries the DONOR UNDER REVIEW section: 6-view sheet + eye table
  + orbitable donor.splat iframe (same page for human and AI).
- orient_splat extrinsic-up bug found+fixed: the file must store camtoworld 3x4 blocks
  (columns = camera axes in world); I had saved them transposed. Also gsplat
  normalize_world_space reorients the frame AFTER COLMAP -- raw extrinsics never apply;
  recompute the Parser normalization and take up from normalized cameras.
- Donor 246 dense retrain (grow_grad2d 1e-4): 195,887 splats (was 94k), loss 0.002,
  6.5 min. Oriented upright via fixed extrinsic-up + --flip-up. Eye is NOISY on the source
  gate (front scored 90 then 0 on identical geometry) -- human terminal rules this gate.

## DONOR ADOPTED: littleBear (SuperSplat dcb0a76d)
- Hunted via the Playwright lane: Sketchfab had zero downloadable teddy splats; SuperSplat
  gallery search "teddy" -> littleBear by mosheca, a REAL SCAN ("Fluffy brown bear, approx
  10x10cm"), 241,251 gaussians, 3 SH bands, served as a SOG v2 bundle (CloudFront meta.json
  + 7 webp planes). Decoded with @playcanvas/splat-transform (zip dir -> .sog -> .ply).
- Operator ruling (the human terminal): ACCEPTED as donor. Slight transparency is FINE --
  fibers are see-through; the CAD inner core fills it in a DARKER shade of each surface
  (darker brown under fur, darker green under the shirt). Hole on butt/back-of-legs waived:
  sample fur ONLY from head and hands -- where there's clipping there's noise.
- Materials by COLOR SORT (operator): brown fur / green knit / cream snout+feet / black
  eyes+nose -- color defines regions; one scan yields four labeled materials.
- Canonical frame: pinned, --ry -90 (face = +Z front), height 0.3m, blob-keep ->
  models/littlebear/donor.splat (+ donor.space.json sidecar, donor_full.ply with full SH).
  Engine UI SOURCE tab now carries this donor; mcp_server DONOR paths moved to
  models/littlebear/*.
- Eye on the 6-view gate: front 95 / back 95 / left 90 / right 95 / top 0 / bottom 5
  (top/bottom are the known framing artifact + the waived butt hole).

## Region cutting + patch corpus (night, operator-authorized)
- METHOD (operator, locked): RGB on a hue wheel, take angular sections, then
  cross-reference with the splat pattern (aniso separates knit from fur where hues
  collide); regions = hue sections + spatial volumes + pattern. Per-region statistical
  distributions (color, log_size, aniso, opacity) ARE the training targets.
- GROUND MARGIN (operator): the bottom 5% of the donor's Y range is excluded from
  EVERY region forever -- contact shadow and static live where the bear touches ground.
- `tools/littlebear_regions.py` cuts models/littlebear/genomes/{fur,sweater,cream,dark}.npz
  (full 14-var attributes + hue/sat/val/aniso) + paints a verification splat
  (_qualify/regions.splat: fur red, sweater green, cream white, dark gray, else faded).
  Counts: fur 111,523 / sweater 17,167 / cream 3,464 / dark 537. Operator AUTHORIZED
  the paint after orbiting it ("You picked smart ones").
- FRAME TRAP (measured, cost a cycle): donor.splat raw bytes ARE the canonical frame
  (+Y up, face +Z); cpp_bridge.load_splat applies SPLAT_ORIENT ON TOP (loaded =
  (raw.z, -raw.y, raw.x)) -- probes run in loaded space measured the LEGS thinking
  they were the head, and the verification paint landed upside-down on the bear.
  littlebear_regions.py now parses .splat bytes directly and never calls cpp_bridge.
- `tools/cut_patches.py --raw`: patches from region genomes without shells -- local
  sheet plane from the window's own splats (SVD), normal flipped so the relief tail
  points OUT, zero shifted to the p5 height (backing floor = inner-membrane stand-in).
  WINDOW-SIZE LESSON: the 5cm half-window was tuned for a ~0.6m bear; on the 0.3m
  littlebear it spanned the head's curvature radius and every patch rendered as a
  RING (flat slab through a curved shell). Scale the window to the donor: half=0.025.
- Corpus (operator-reviewed preview sheet, "everything looks good ... begin training"):
  fur 274 patches (2048 splats each), sweater 165 (~660 median), cream 85.
- `tools/qualify_corpus.py --half`: presentation zoom now matches the cut window.
  Fur qualification (274 patches, qwen3.8 YES/NO + reason, rejects sheet for operator
  audit) running at commit time.
- `tools/preview_corpus.py`: the corpus contact sheet is a real tool now (was heredoc).
- Engine UI MATERIAL tab: regions table (color swatch, n, aniso, opacity, definition)
  + orbitable verification paint + regions sheet + patch preview + qualification
  verdicts + rejects audit sheet. sync_ui.py carries the littlebear artifacts.

## fur_brown TRAINED (night)
- Eye qualification: 136/274 patches PASS (biased toward rejection by design; rejects
  sheet synced to the MATERIAL tab for operator audit). 276,763 qualified splats.
- `train_material.py --corpus`: 12-component GMM over [rgb, log scale, h_mm, alpha],
  likelihood floor -7.3, mean color (0.71, 0.60, 0.45), real color box clamped.
  models/littlebear/materials/fur_brown.npz + library.json.
- Synthesis smoke test (GMM sample + q_local bootstrap on a flat 5cm membrane,
  2048 splats, h clamped to the model's measured -2.1..14.7mm): renders as a full
  fur-textured sheet with standing relief in the real viewer. Known limit: per-splat
  independence cannot grow correlated lock structure (the wavy tufts) -- that is the
  v2 pattern-conditioned generator.

## furgen v1 SAMPLED + OPERATOR PASS (night)
- Sampled 8 patches from models/littlebear/furgen.pt (flow-matching transformer,
  20k steps, conditioning borrowed from random real patches).
- First sample run: 2/8 eye PASS -- white blowout streaks. Added sample-time
  physical cleanup to tools/train_furgen.py (--euler 100 --material fur_brown.npz:
  rgb clamped to the measured color box, scales to scale_cap, alpha<0.05 -> padding).
  Re-sampled: 3/8 eye PASS (gen0, gen2, gen6). Real corpus passes at ~50%, so v1 is
  below the real-data gate; known levers: more donor data, classifier-free guidance.
- tools/stage_furgen_grid.py: all 8 gen patches as ONE orbitable 3D scene
  (_qualify/furgen_grid.splat, 15,902 splats, 4x2 grid, patch_buffer frame change +
  save_splat). hunt_shot.js splat lane needs the .splat EXTENSION in the name arg
  (qualify_shots.js appends it; hunt_shot does not) -- extensionless name 404s black.
- OPERATOR RULING: the 3D grid is a PASS ("borderline but a pass"). The human is the
  terminal; recorded. Next gate: CAD inner core (darker shade per material) + parts.
