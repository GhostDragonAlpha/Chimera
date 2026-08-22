# THE GAME-ASSET WORKFLOW — the step-by-step series

**This is the workflow for every game asset, not just the bear.** The bear is instance #1 —
the first asset carried end-to-end through it. (The file predates the reframe; the old name
"THE BEAR WORKFLOW" is kept only so links don't break.)

Single entry point. Do the steps **in order**; each has a **GATE** that must pass before the
next. Detailed docs are *pointed to*, not duplicated. A step is not "done" until its gate
passes — "looks okay" is not a pass.

**Long-term goal (operator directive, 2026-08-18):** the whole workflow must be reproducible
as a **tool-call system** — every step invocable as a named tool, possibly surfaced through
an **MCP server**, so an agent can run SOURCE → VERIFY → EXTRACT → REAPPLY → RIG → DRIVE on
any asset. Not built yet; record it here so it doesn't get lost.

## The checklist

### 1. SOURCE a valid bear
- **What:** a bear with 2 NORMAL arms (not two fused into one per side), front and back
  identical in texture and color.
- **How:** SDXL-Turbo image → TripoSplat `.splat` (see `THE_BEAR_PIPELINE.md` §1–2).
- **SOURCE RULE CHANGE (operator directive, 2026-08-19 — supersedes the above for new
  assets):** single-image AI-generated 3D is REJECTED as a source (TripoSplat AND TRELLIS —
  2D→3D generation cannot pass the front==back gate by construction). Legal sources:
  1. **REAL CAPTURE — VIDEO PHOTOGRAMMETRY (the preferred lane; "the only reliable source
     of visual data"):** `tools/video_to_splat.py` — a slow orbit video of a still, lit
     object → frames (ffmpeg) → SfM (`tools/colmap`, 4.1.1 CUDA: feature → sequential match
     → map → undistort) → 3DGS training (gsplat `simple_trainer.py` in `.venv-gs`, torch
     2.11 cu128 on the 4090) → `ply` → `ChimeraEngine/native/ply_to_splat.py` → `.splat`.
     Capture gate: ≥80% of frames registered, else re-shoot. (nerfstudio FAILED to install
     on py3.13 — its pinned PyAV has no cp313 wheel; recorded so nobody repays it. gsplat
     directly is the leaner stack anyway.)
     Toolchain traps, all solved 2026-08-19 (do NOT re-pay):
     - pycolmap ≥3.12 removed `SceneManager` → `tools/gsplat/examples/datasets/pycolmap_shim.py`
       (Reconstruction-backed drop-in; colmap.py falls back to it automatically).
     - The gsplat pip repo examples must match the installed package tag (v1.5.3).
     - Windows `rpcndr.h` `#define small char` collides with torch 2.11's
       `CUDACachingAllocator.h` ctor param in EVERY nvcc build → the installed header is
       patched (param renamed `small_`; ABI-neutral). Reinstalling torch reverts it.
     - gsplat 1.5.3 hardcodes gcc flag `-Wno-attributes` for cl → patched platform-conditional
       in `.venv-gs` (site-packages). JIT build needs VS2022 vcvars (VS18/MSVC 14.51 is
       REJECTED by CUDA 12.8 nvcc) — `tools/train_capture.bat` wraps that env.
     - fused-ssim will not build here (torch header + MSVC C2872 'std' ambiguity);
       simple_trainer.py falls back to torchmetrics SSIM automatically.
     gsplat CUDA extension is BUILT and cached (gsplat_cuda.pyd, torch_extensions cache) —
     later runs need no compiler.
     STATUS (2026-08-19): verified END-TO-END on a synthetic capture (72 engine-rendered
     orbit frames of the painted koala → COLMAP 55/72 → gsplat → `.splat` → engine
     render). Ready for real footage: film a slow steady orbit of a still, well-lit
     object (~60–90 s), then `tools/train_capture.bat frames orbit.mp4 --dir
     capture/<name>` → `sfm` → `train --steps 30000` → `export`.
  1b. **AI-GENERATED CAPTURE — SEEDANCE 2.5 VIA FAL.AI (operator's subscription):**
     `tools/gen_orbit_video.py <front.png> --name <n>` — one still (e.g. the eye-approved
     SDXL bear `models/imagegen/tpose2_640.png`) → Seedance 2.5 image-to-video prompted
     for a slow single-shot frozen-object 360° orbit → `capture/<n>/orbit.mp4`, which
     flows into the SAME pipeline above. First run (`capture/genbear`, 30 s, 720p):
     **COLMAP registered 250/250 frames — the AI video passes the capture gate.**
     The prompt is the capture protocol (frozen object, fixed light, camera-only motion,
     one continuous shot); the falsifier is the registration gate itself.
     Mapper trap: COLMAP 4.x can emit several disconnected models (sparse/0,1,2…) NOT
     size-ordered — the sfm stage now undistorts the LARGEST (was hardcoded sparse/0).
  1c. **FEED-FORWARD MULTI-IMAGE — ANYSPLAT (no SfM, no training):** `tools/anysplat_recon.py
     --frames <dir> --k 64 --skip 2 --out <ply>` in `.venv-anysplat` — K orbit frames →
     AnySplat (VGGT backbone + gaussian head, `lhjiang/anysplat`) regresses a standard
     DC-only 3DGS PLY + per-view cam2world (`_extrinsic.npy`) and NORMALIZED intrinsics
     (`_intrinsic.npy`: multiply rows 0,1 by res for pixels) in ONE forward pass. This is
     the lane the operator asked for ("a model fed the photogrammetry that uses multiple
     images"). Then: `tools/crop_ply_orbit.py` (camera-ring crop — AnySplat c2w ring, pick
     the extrinsic reading with low orbit-radius cv) → `tools/orient_splat.py` with
     `--opacity-raw` (AnySplat stores raw alpha, NOT logit), `--alpha-min 0.3`,
     `--lum-min 0.10` (0.12 shreds dark face fur), `--density-k 3`, `--blob-keep`
     (largest-26-connected-voxel-blob smart-clip; kills junk smears whose opacity the
     refinement boosts past the alpha gate — the teddy-envelope aniso/size filter does NOT
     substitute: it eats the face, use `--no-envelope` on this lane), `--extrinsic-up <npy>`
     (world up = mean −camera_y of the ring; PCA-Y tips a T-pose bear because arm-span >
     height). Optional polish: `tools/anysplat_refine.py` (bat wrapper
     `tools/anysplat_refine.bat` for the vcvars env — gsplat JIT needs cl+ninja, the
     monkeypatch alone is not enough because a real recompile is triggered) — gsplat
     photometric fit of the AnySplat init against the real frames, exports the same PLY
     layout. Face direction lands 90° off the engine front convention on genbear2 — fixed
     with `--ry -90`, decided by eye render.
     Shims live in `external/anysplat/` (torch_scatter, xformers→SDPA), upstream repo
     untouched. 64 views → ~8M gaussians, ~3M after crop, ~111k after cleaning.
     Needs no fal.ai spend. STATUS (2026-08-19): genbear2 (250 Seedance frames, K=64)
     → refine 3000 steps (SSIM 0.93, PSNR 28) → `models/genbear2/genbear2_as64_refined.splat`
     (110,897 splats) — eye gate: 2 arms + 2 legs, face at front, back fur == front fur —
     the best movie-pipeline bear to date.
  2. **MESH-DERIVED 3DGS (exact geometry):** `ChimeraEngine/native/mesh_to_splat.py` —
     area-uniform surface samples → point cloud (`<out>.points.npy`) + thin disk-Gaussians
     oriented to smooth normals; UV/vertex-color TEXTURE-aware (this is what padillasplats'
     mesh2splat did, but with true color when the mesh has it). Normalizes to longest
     axis = 2.0 (their convention). Instance #2 = the koala (mesh had no texture — LOD
     color codes only; painted from a reference palette via `native/paint_parts.py`).
  3. **NATIVE-3D GENERATIVE** (GaussianCube/DiffSplat lane; our gates are its quality
     filter) — noted, not built.
  Always re-orient the source to front=+z BEFORE measuring (raw-space position+quat
  rotation, e.g. `koala_500k_front.splat`), so the f08=front orbit convention holds.
- **GATE:** the eye reports exactly 2 arms AND front texture == back texture.
- **GATE STATUS (2026-08-19): PASSED for the first time** — `models/genbear/genbear_front.splat`
  (AI-video photogrammetry lane 1b). Eye on the 24-frame orbit: coherent bear, 2 arms +
  2 legs, back fur == front fur — PASS. The bear/koala lane below kept its separate
  T-pose run's status; this gate now has a live, repeatable route (one still → one orbit
  video → one splat).
- **STATUS (2026-08-18, second run): PASSED** — `models/imagegen/tpose2_640.png` (SDXL
  seed 640, eye-picked of 4 seeds) → `tpose2_640.splat` (262,144 gaussians). Eye verdict on
  the 24-frame orbit movie (`ChimeraEngine/output/tpose2_640_movie/`): exactly 2 arms, no
  fused/duplicated limbs, back fur == front fur, head connected — **PASS**. Data confirms:
  arm z-spread narrow (σ≈0.05, no front+back merged copies), back only ~8–11% darker than
  front (the failed bear was 40–50%).
- (first run, same day: FAILED — `teddy_tpose.splat` arms melded, 2 fused per side.)

### 2. VERIFY (static)
- **What:** the eye produces a defect report (limb count, proportions, front/back consistency).
- **How:** `ChimeraEngine/native/skeleton.py analyze` (render N views + vision-describe).
- **GATE:** no duplicated limbs, no front/back mismatch.
- **STATUS:** caught the 4-arms + color/texture mismatch. The eye perceives; the code agent
  analyzes physics (verifies the defect in the data).

### 3. EXTRACT materials
- **What:** section the cloud into named PARTS (the "UV unwrap of a 3DGS"), then extract each
  part's **color genome** (RGB) AND **texture genome** (`log_size`, `aniso`, `opacity` from
  splat `scale`).
- **How (settled 2026-08-18, the operator's pivot):** the part geometry comes from a
  **measured, symmetric stick figure**, never from eye-drawn seams:
  1. `ChimeraEngine/native/stickfigure.py build` — measure the cloud (neck = width minimum
     below the head, arm axis = height of extreme-x splats, crotch = where the center column
     empties, torso width = median torso-band width, paws/feet = distal centroids), then fit a
     SYMMETRIC skeleton (L/R mirror-averaged; elbows/knees are stated construction midpoints).
  2. `stickfigure.py overlay` — the GATE: bones drawn on the render must run down the middle
     of the limbs (cross-checked against the eye-triangulated `skeleton.py` skeleton:
     agreement ~2 cm).
  3. `section.py cut --skeleton` — parts = bones by **nearest-bone assignment** (segment
     Voronoi; junctions resolve by geometry), splats beyond the last joint → hands/feet; face
     features (eyes, nose, mouth, muzzle, ears) keep eye-drawn **ring prisms** (reliable on
     the face). Giant filler splats (mag > 10× median) are excluded from the body.
     Two 2026-08-19 refinements: **eyes are symmetrized** (`_symmetrize_eyes` — the eye's two
     eye rings anchored asymmetrically, one read as "on the snout"; mirror-average across x=0,
     bead radius = mean of the two rings' OWN radii, not the pooled spread), and the
     **limb-root plane rule** (a limb claims only splats beyond its root joint along the limb
     axis — without it the armpit/chest wedge binds to the arm stub's endpoint and STREAKS
     when posed; a radial cap failed first because the wedge is contiguous with the arm
     cylinder, so no percentile separates it).
  Color genomes still come from `extract_materials.py` (chromaticity k-means).
- **Failed paths, recorded so nobody repays them:** eye-drawn seam rings on extremities are
  unreliable (wrist rings collapsed to a point, shoulder rings landed mid-chest — measured);
  graph flood with big-M barrier planes leaks when locality balls overlap (thigh_right flooded
  half the body). Nearest-bone won. The legacy eye-ring path remains as `section.py cut`.
- **GATE:** the part-colored orbit (`section.py verify`) — the eye reports no bleed, no
  splits, parts seated; confirmed against the frames directly.
- **STATUS (2026-08-18, stick-figure run): DONE** — `models/imagegen/tpose2_640_rig/skeleton_sym.json`
  + `models/imagegen/tpose2_640_section/part_assignment.npy` (21 parts: head 71.9k, torso
  51.2k, uparms 13.9k/15.7k, forearms 4.8k/3.4k, hands 4.3k/1.6k, thighs 18.4k/21.0k, shins
  19.3k/19.2k, feet 4.1k/4.0k, face features 77–3.8k). Eye verdict PASS; back of head clean
  (no face-color bleed). Known: hand L/R asymmetry (the right paw is genuinely thinner).
- (color-only clustering `teddy2_materials.json` remains the 3-material genome source;
  superseded for REGIONS by the part assignment above.)

### 4. REAPPLY
- **What:** recolor every splat to its material's average color, and rescale to its material's
  mean size (preserving anisotropy) — "paint" the surface with the extracted averages.
- **How:** `ChimeraEngine/native/reapply_materials.py` — per splat, by its saved material
  assignment: `color = material mean RGB`, `geomean(scale) = material front mean`
  (anisotropy preserved), `alpha = material front mean`. Writes a new 32-byte-record
  `.splat`; positions and rotations untouched, so no orientation round-trip is needed.
- **GATE:** front and back agree in color AND in `log_size`/opacity distribution.
- **STATUS (2026-08-18, second run): DONE** — `ChimeraEngine/native/reapply_materials.py`
  repainted `tpose2_640.splat` → `models/imagegen/tpose2_640_repainted.splat` (positions and
  rotations untouched; color = material mean, geomean(scale) = material front mean,
  alpha = material front mean — the back inherits the front's coverage). Theory confirmed by
  measurement: pre-repaint the back was genuinely thinner (tan opacity 0.102 back vs 0.129
  front; cream 0.021 back vs 0.173 front — the see-through was a generation asymmetry, not a
  renderer bug). Post-repaint front == back per material by construction, and the eye
  confirmed the back render: fully opaque, uniform tan, no patches, no defects. One region
  refinement was needed first: the front-only regions had bled through z (4,105 cream + 1,761
  black splats on the back half) — reassigned to tan plush; final counts tan 255,050 / cream
  6,853 / black 241 (`teddy2_assignment.npy`, `teddy2_materials.json`).
- (first run: color DONE, texture DONE — front/back `log_size` converged −6.629 vs −6.628;
  superseded with the retired bear.)

### 5. RIG
- **What:** mark joints → triangulate → assign bones → skin.
- **How:** `ChimeraEngine/native/skeleton.py mark | triangulate | assign`; the stick-figure
  measurement path is `ChimeraEngine/native/stickfigure.py` (symmetric skeleton) +
  `section.py cut --skeleton` (nearest-bone rigid assignment = the w=1.0 baseline).
- **Method (from research, `docs/research/rigging_static_objects_reference.md`):** rigid
  nearest-bone IS the standard rigid-skinning floor; the skinning layer is
  `ChimeraEngine/native/skin.py` — a smooth LBS band at each joint (two influences, exp
  falloff, band = 0.8 × the limb's MEASURED cross-section radius at the joint — the seam a
  bend opens is ~r·θ; distance = along-bone distance to the joint plane + a lateral gate),
  means by LBS, Gaussian rotations by weighted sign-aligned quaternion average,
  scale/opacity/color untouched; DQS is the escalation if a band ever shows volume loss.
- **GATE:** static verification (2 normal arms, coherent limb assignment), then a posed
  orbit movie with no seam cracks or joint volume collapse.
- **SPECIES BRANCH (2026-08-19, koala = instance #2):** the pipeline is
  species-parameterized end-to-end. Quadruped: `stickfigure_quad.py` (feet = k-means(4) on
  the bottom band; neck = width minimum between chest and the EAR width-maximum;
  elbow/knee at RESEARCHED anatomical ratios — `docs/research/koala_anatomy_reference.md`,
  LEG_MID_FRAC 0.526/0.441), `section.py SPECIES_SPECS["quadruped"]` (torso bone runs
  pelvis→neck; per-leg root planes), `skin.py _skin_spec` (QUAD_BONE_TREE/JOINT_BONES/FK
  order). The skeleton JSON's `"species"` field selects the branch; biped is the default
  and the teddy path is untouched. **Measured LBS envelope on the koala: PASS at ≤30°
  shoulder, FAIL at 55°** (a surface-only cloud has no splats on the concavity a widely
  lifted leg exposes — coverage property, not a bug; DQS or corrective splats are the
  escalation past the edge). Monochrome sources: the eye can mark nose/muzzle/ear rings
  but eye/mouth rings failed (junk geometry) — dropped; needs shading-independent marking.
- **STATUS (2026-08-19): DONE** — `skin.py weights` (87k blended / 175k rigid) +
  `skin.py pose --spec pose_wave.json` (shoulder 45°, elbow 40°, neck 15°): the eye's
  verdict on the posed orbit = PASS (fur continuous at shoulder/elbow, no cracks, no
  artifacts); confirmed against the frames directly (the one streak found was the armpit
  wedge — fixed by the root-plane rule in step 3; the 314 giant filler splats are hidden
  in posed renders: static they're invisible haze, posed they streak). The painted-verify
  eye FAIL of 2026-08-19 was a FALSE POSITIVE (end-on arm discs on side views read as
  foreign blobs — verify prompt amended; frames re-checked directly: no bleed).

### 6. DRIVE
- **What:** the CA/force dynamics — gravity is a *field*, muscles are CA forces, contact acts
  through the feet; the pose (stand/walk) **emerges**, never assigned.
- **See:** `THE_RENDERER_DECISION.md` NEXT MEMBRANE.

## Where each doc lives

| topic | doc / tool |
|---|---|
| renderer (14-float 3DGS, Vulkan engine) | `docs/THE_RENDERER_DECISION.md` |
| splat format, generation, verification, series | `docs/THE_BEAR_PIPELINE.md` |
| workflow tool (analyze/mark/triangulate/assign) | `ChimeraEngine/native/skeleton.py` |
| stick-figure skeleton (measure → symmetric fit) | `ChimeraEngine/native/stickfigure.py` |
| quadruped stick figure (koala; measure → symmetric fit) | `ChimeraEngine/native/stickfigure_quad.py` |
| skinning (LBS band, FK pose) | `ChimeraEngine/native/skin.py` |
| rigging/skinning research reference | `docs/research/rigging_static_objects_reference.md` |
| koala skeletal anatomy (bone ratios for LEG_MID_FRAC) | `docs/research/koala_anatomy_reference.md` |
| material harvest (chromaticity clustering) | `tools/harvest_material.py` |
| material extraction (k-means genomes + assignment) | `ChimeraEngine/native/extract_materials.py` |
| material reapply (repaint genomes onto the splat) | `ChimeraEngine/native/reapply_materials.py` |
| part sectioning (marker "UV unwrap" of a 3DGS) | `ChimeraEngine/native/section.py` |
| material labeling (serial numbers) | `ChimeraEngine/vision/vision_pattern_labeler.py` |
| vision backend (the eye) | `ChimeraEngine/senses.py` |

Agent: Kilo (chimera-code)
