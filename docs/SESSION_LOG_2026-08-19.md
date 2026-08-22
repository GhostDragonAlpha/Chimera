# SESSION LOG — 2026-08-19

The video-photogrammetry capture stack brought up and fought through four Windows toolchain
walls. The lane text lives in [`THE_BEAR_WORKFLOW.md`](THE_BEAR_WORKFLOW.md) (SOURCE step,
lane 1); this log records what it took to make it run.

## The stack (all verified working this session)

- `tools/colmap/` — COLMAP 4.1.1 CUDA. Trap: 4.x `sequential_matcher` takes NO
  `--image_path` (matchers read only the database); the orchestrator was fixed.
- `.venv-gs` (Python 3.13.5) — torch 2.11.0+cu128, gsplat 1.5.3, pycolmap 3.13.0.
- `tools/gsplat` — the gsplat repo CHECKED OUT AT THE v1.5.3 TAG (main's examples are
  newer than the pip package and break on import).
- `tools/video_to_splat.py` — frames (ffmpeg) → sfm (COLMAP) → train (gsplat
  `simple_trainer.py`) → export (`ply_to_splat.py`).

## The four walls (do not re-pay)

1. **pycolmap ≥ 3.12 removed `SceneManager`.** Fixed by
   `tools/gsplat/examples/datasets/pycolmap_shim.py` — a Reconstruction-backed drop-in
   (cameras/images/points3D/track surface). Verified against a hand-written COLMAP text
   model. `colmap.py` falls back to it automatically.
2. **Windows `rpcndr.h` `#define small char` collides with torch 2.11's
   `CUDACachingAllocator.h`** (`StreamSegmentSize(cudaStream_t s, bool small, ...)` →
   `bool char`) in EVERY nvcc extension build. Fixed by patching the installed torch
   header (param renamed `small_`; parameter name only, ABI-neutral). Reinstalling torch
   reverts it — reapply.
3. **CUDA 12.8 nvcc rejects the VS 18 toolchain (MSVC 14.51).** VS 2022 BuildTools
   (MSVC 14.44) is installed at `C:\Program Files (x86)\Microsoft Visual Studio\2022\
   BuildTools` — builds must run through its `vcvars64.bat`. Wrappers:
   `tools/train_capture.bat` (pipeline), `.tmp/build_gsplat_jit.bat` (one-off JIT build).
4. **gsplat 1.5.3 passes gcc flag `-Wno-attributes` to cl.** Patched platform-conditional
   in the installed package (`.venv-gs/.../gsplat/cuda/_backend.py`). The JIT build then
   succeeded: `gsplat_cuda.pyd` is cached under torch_extensions — later runs need no
   compiler.

5. **torch's extension loader requires `ninja` even to LOAD a cached JIT build** —
   `pip install ninja` in `.venv-gs` (done). Also: `simple_trainer.py` gets ABSOLUTE
   `--data_dir`/`--result_dir` (it runs with cwd=tools/gsplat/examples).

nerfstudio was attempted first and abandoned: its pinned PyAV has no cp313 wheel.
fused-ssim does not build here (torch header + MSVC C2872 'std' ambiguity); the trainer
falls back to torchmetrics SSIM automatically (patch in the v1.5.3 examples copy).

## New/extended tools

- `ChimeraEngine/cpp_bridge.py::save_splat()` — exact inverse of `load_splat()`
  (u8 packing incl. SPLAT_ORIENT inverse). Verified by byte-exact round-trip render.
- `ChimeraEngine/native/mesh_to_splat.py` — trimesh area-uniform sampling →
  `.points.npy` (xyz+rgb+normal) + thin-disk `.splat`; UV/vertex-color texture-aware.
- `ChimeraEngine/native/ply_to_splat.py` — standard-3DGS PLY (f_dc/opacity logit/
  scale logs/rot) → 32-byte `.splat` via `save_splat`.

## Closed-loop E2E test (synthetic capture)

To prove the chain without waiting for real footage: the Vulkan engine rendered a 72-frame
3-elevation orbit of `models/koala/koala_500k_painted.splat` into
`capture/synth_koala/frames/`. COLMAP registered 55/72 (76% — just under the 80% gate;
ring transitions on a smooth synthetic surface). The full chain then ran: **frames →
COLMAP sfm → gsplat train → ply → ply_to_splat → engine render all PASS**
(`capture/synth_koala/synth_koala.splat`, renders through `render_splat()`). Two runs:
1000 steps → 6,557 gaussians; 7000 steps → 24,389 gaussians (`synth_koala_7k.splat`,
clearly readable quadruped: ears/head/body/legs). Wrong-side-up as expected — COLMAP's
world frame is arbitrary, re-orient downstream like any capture. The remaining fuzz is the
synthetic source's fault (smooth painted surface, 55 views, smoke-scale steps), not the
plumbing's. (Export trap also fixed: `train_out/ply` glob now sorts numerically —
`point_cloud_999` sorts after `point_cloud_6999` lexically.) The pipeline is READY;
what it needs is a real orbit video of a real object.

## AI-generated capture (operator directive: Seedance 2.5 via FAL.ai)

Instead of filming a real object, GENERATE the capture video. `tools/gen_orbit_video.py`
anchors Seedance 2.5 image-to-video on one still (`models/imagegen/tpose2_640.png`, the
eye-approved SDXL bear) with a frozen-object 360°-orbit prompt → 30 s 720p
`capture/genbear/orbit.mp4` → 250 frames (8.3 fps). **COLMAP registered 250/250** —
the AI video is 3D-consistent enough to solve cameras on every frame. The mapper wrote
three disconnected models (4 / 10 / 250 images, NOT size-ordered); the sfm stage now
undistorts the largest. Trained 30k steps (~11 min on the 4090, ~45 it/s) → 121,665
gaussians → `ply_to_splat` → cropped alpha<0.1 haze and r>0.18 outliers (102,714 kept),
recentered, PCA-uprighted (long axis → +Y, head-up sign picked by eye from 2 candidate
renders) → **`models/genbear/genbear_front.splat` — the first photoreal asset**.
SOURCE gate on the 24-frame engine orbit (eye, qwen3.8): coherent bear all the way around,
exactly 2 arms + 2 legs, back fur matches front in color/texture — **PASS** (first source
ever to pass). Eye's caveat: "slightly artificial/cartoonish" — softness from 720p input;
the same pipeline at 1080p/30 s or real footage raises the ceiling.


## The full loop, closed (genbear)

`models/genbear/genbear_front.splat` went through the ENTIRE recorded rig workflow:
1. **RIG** — `stickfigure.py build/overlay` (normalized to height 1.0 first — the tools
   expect the koala convention; positions AND gaussian radii scale together). Eye on 4
   overlays: bones centered in limbs, joints at junctions — **PASS**
   (`models/genbear/rig/skeleton_sym.json`).
2. **SECTION** — `section.py movie → mark → cut --skeleton` (the eye placed all markers in
   one watch: 10 seeds, 7 face rings, 9 joint bands; skeleton-driven nearest-bone cut with
   the limb-root-plane rule) → verify orbit — **PASS** (no bleed, no splits).
3. **SKIN** — `skin.py weights`: 47,535 blended / 55,179 rigid, exp-falloff LBS bands.
4. **POSE** — `models/genbear/rig/pose_wave.json` (neck 12°, shoulder_right 30°,
   elbow_right 55°) → 16-frame posed orbit. Eye: right arm visibly raised, fur continuous
   across shoulder+elbow bands, no cracks, no candy-wrapper collapse — **PASS**.

The platform loop the operator named is now demonstrated end to end on a photoreal asset:
**one still → Seedance orbit video → COLMAP → gsplat → .splat → measured skeleton →
sectioned parts → LBS skin → posed character.**

## Artifact hunt (evening) — genbear "unusable" → clean

**Complaint:** engine render had major artifacts (smoke, black glossy blob above head,
ember specks, detached puff near the raised paw in wave). **Root cause:** NOT the engine,
NOT skinning, NOT the CA (the CA is not in this render path at all) — junk baked into the
trained cloud by the AI orbit video's near-black background. Invisible at training views,
exposed by free camera + LBS.

**Fix:** new pipeline stage `tools/clean_splat.py` (recorded, reproducible). Filters, all
eye-confirmed via render-only-suspects / render-without-them through the live engine:
smoke (lum<0.08 & aniso>8) 5512 · needles (aniso>150 & lum<0.35) 6398 · oversized
(smax>0.02) 1708 · embers/off-hue 18282 · sparse (<8 neighbours @ r=0.04) 313 · one
eye-directed box cut behind/above the head 14052 (dense dark shell — attribute filters
could not separate it from fur; zone rendered alone = pure junk, removed = head intact).
Total: 102,714 → 77,340. Output: `models/genbear/genbear_clean.splat` +
`genbear_clean_section/skin_weights.npz` (masked to match).

**Verified:** engine reloaded via `engine_skin.py`; rest+wave captured at theta 0/pi +
high angle — smoke, blob, streaks, detached paw puff all GONE; P-toggle intact. Remaining
nits (accepted, logged): 1-2 ember specks above bear, gray scraggle on right ear (may be
legit light inner-ear fur), faint under-foot shadow splats.

**Trap added:** `/camera` endpoint takes JSON (`{"cam_radius","cam_theta","cam_phi"}`),
NOT the binary `<3f` used by `/membrane_bin` — binary body silently falls back to
defaults (radius 12 → tiny bear).

## Silhouette carve stage validated (genbear1 dry run)

New pipeline stage `tools/silhouette_carve.py` (operator directive: photogrammetry trim,
outline the shape to ~5mm). Visual-hull constraint: a splat projecting outside the
object's silhouette in a registered view cannot be real. Stronger than clean_splat's
attribute heuristics — it removes the dense dark shell and view-dependent billboards
WITHOUT box cuts (the earlier box cut amputated the crown/face from head-on views).

**Root-cause fix mid-validation:** first run kept 25/121665 — the trained PLY lives in
gsplat's NORMALIZED frame (`normalize_world_space=True` default, T = T3?@T2@T1), not the
raw COLMAP world frame, so raw-camera projection missed everything. The tool now
replicates the parser's transform chain (similarity_from_cameras -> align_principal_axes
-> conditional z-flip, tools/gsplat/examples/datasets/normalize.py) and projects with
normalized-frame cameras.

**Result on genbear1:** keep 96,870 / 121,665 (79.6%, inside the >=60% prediction);
cut 24,795 ≈ the ~25k billboard/junk population found by hand earlier. Eye-check through
the live engine (carved vs full, same camera): carved view shows IDENTICAL anatomy
(head, ears, limbs), junk/shell gone — falsifier passed, carve does not eat fur.

**Also new:** `tools/orient_splat.py` — the previously ad-hoc export step made a tool:
PLY -> carve mask -> alpha>=0.1 crop -> PCA upright (long axis -> +Y) -> normalize height
1.0 -> .splat, with explicit --flip-up/--flip-front decided by eye render.

## teddyloop: pipeline validated end-to-end on perfect input

Experiment: render 250 orbit frames of the KNOWN-GOOD teddy.splat with our own engine
(radius 1.8, phi 0.15, 360 deg) and run the full capture chain on them. Perfect input
cannot lie: any artifact in the output is the PIPELINE's fault, not the source's.

**Result: PASS.** sfm 250/250 -> train 30k -> carve (kept 35,604/42,529 = 84%) ->
teddy-envelope filter (cut 2,245: aniso>50, size>1% diag) -> robust-core PCA orient
(needed --flip-up --flip-front) -> 31,969 splats, height 1.0. Engine eye-check:
front (theta=pi, on-convention) crisp face + bow tie, back pale (FAITHFUL — the source
teddy is pale behind), side pale, high angle solid with minor crown fuzz.

**Lessons measured, not opined:**
- Splat-count bloat is an inconsistency signal: noisy AI video -> 210k splats; perfect
  input -> 42k for the same object class. The trainer adds splats to fit contradictions.
- The teddy envelope (from teddy.splat stats): alpha median 0.976, aniso 99% < 11
  (max 47), smax 99% < 1% of diagonal. Now the DEFAULT filter in orient_splat.py.
- genbear2's hollow face / spike stars = source-side (video drift), unfixable by
  trimming. Confirmed by contrast: same pipeline + clean input = clean bear.
- Single-elevation orbit leaves the crown under-observed -> needle fuzz on top.
  NEXT CAPTURE: 2-3 elevations (user directive: "top bottom side front everything").
- genbear3 generator upgraded (end_image_url loop closure, 1080p, bitrate_mode high,
  black-bg anchor composite, rigid-statue prompt) — BLOCKED: fal.ai balance exhausted.

genbear3 is queued to fire on top-up: tools/gen_orbit_video.py <anchor> --name genbear3 --black-bg

## AnySplat lane CLOSED: feed-forward multi-image 3DGS + photometric refine = good bear

The operator's directed pivot ("a model you fed the photogrammetry into that uses multiple
images") is AnySplat, and it delivered. Full chain on genbear2 (250 Seedance frames, K=64):

1. `tools/anysplat_recon.py` (.venv-anysplat, shims in `external/anysplat/`) → 7.94M-gaussian
   PLY + cam2world ring + normalized intrinsics, ONE forward pass, no SfM, no training.
2. `tools/crop_ply_orbit.py` → ~3M (orbit-ring crop, c2w picked by low orbit-radius cv).
3. `tools/anysplat_refine.py` via `tools/anysplat_refine.bat` (vcvars env — gsplat JIT
   needs cl; the cached pyd did NOT spare the recompile) → 3000 steps, SSIM 0.93 / PSNR 28.
4. `tools/orient_splat.py --opacity-raw --alpha-min 0.3 --lum-min 0.10 --no-envelope
   --density-k 3 --blob-keep --extrinsic-up <npy> --ry -90` →
   `models/genbear2/genbear2_as64_refined.splat` (110,897 splats, height 1.0).

**Eye gate: PASS** — front shows face (eyes/snout) + 2 arms + 2 legs, side/back dense and
photoreal, back fur == front fur. Best movie-pipeline bear to date; loaded in the engine.

**Lessons measured this round:**
- The refinement RESURRECTS junk: background smears that failed the alpha gate before come
  back opaque (they fit the dark background). Attribute filters can't separate them from fur.
- The fix is the operator's own smart-clip: `--blob-keep` (new in orient_splat.py) keeps only
  the largest 26-connected voxel blob (union-find, cell 0.03x diag). Cut 11.5k junk splats;
  bear untouched. This also fixes CENTERING — junk streaks were skewing the bbox recenter.
- The teddy-envelope filter (aniso>50, size>1% diag) EATS THE FACE on this lane — the face
  is carried by large/anisotropic splats. `--no-envelope` mandatory here (envelope stays
  valid for the COLMAP/gsplat lane it was measured on).
- Face direction lands 90° off the engine front convention → `--ry -90`, decided by eye.
- ninja/cl check: monkeypatching `verify_ninja_availability` is NOT enough — torch's
  `_jit_compile` does a version check and recompiles; run through the vcvars bat instead.

Workflow doc §1 lane 1c updated with the full recipe. fal.ai spend: zero (genbear3 re-shoot
still queued on balance top-up, but lane 1c no longer needs it).

---

## Late session: the dyad pivot + theSeed PROVEN + genbear3 bake-off launched

**Operator redirect:** off ad-hoc pipeline work, onto the project's own method — the
chimera-engine MCP dyad workflow. theSeed was mid-proof; finished it tonight.

**theSeed PROVEN (dyadAnalysis complete, boundary crossed via MCP):**
- S0 claim: "A teddy bear generated from controlled multi-view AI imagery has no unobserved side."
- S2: 16 variables, saturated (7-round dry tail, Chao2 ~0 unseen).
- Appearance: the DYAD HOLDS at 0.85 — qwen3.8 (Ollama, LOCAL — the operator's trust condition)
  watched a 12-frame turntable and read the same solid bear from all sides.
- S5: every PHYSICS variable carries a measurement pointer into `story/theSeed/numbers.json`,
  which records the honest flaws: top-heavy ring (49/64 views above +30 deg el), mid-band
  azimuth max gap 178.6 deg, crown wisp, grainy fur. Not smoothed over.
- New membrane: `story/theSeed/physics.py` — loads the proven asset
  `models/genbear2/genbear2_final_engine.splat` (182,724 splats), turntables it over a static
  ground (the ground exists because the blind eye read groundless rotation as "tumbling in the
  air" — a falsifier-driven scene fix, same class as theVerbs).

**Dyad machinery fixes (all measured, commented in code):**
- `/membrane` JSON upload KILLS the engine process at ~64k particles (WinError 10054, process
  death, reproduced twice). `cpp_bridge.load_membrane` now uploads via the binary 14-float
  `/membrane_bin` path. Engine restart required after each kill.
- `human_messenger.PHYSICS_READING["theSeed"]` was STALE — the old cosmic story's expected
  reading ("dots connected by lines") judging a teddy bear: alignment 0.000, the eye was right
  and the physics reading was wrong. Rewritten from the current claim.
- The dyad judged only [begin, end] — 2 stills of a symmetric bear read as "no change"/"one
  frame". New `cpp_bridge.render_term_movie` renders the full timeline (12 frames); the
  messenger expands the 2-path shorthand to the real movie (lives in human_messenger because
  /reload hot-reloads it and NOT engine_state). Frames downscaled to 384px — the eye is
  calibrated at FRAME_TOKENS=86 measured at 384px; full-res 12x8MB payloads killed the watch.
- Engine-culling deception on record: the engine window's center-based culling can HIDE junk
  the HTTP viewer reveals. The HTTP viewer (Spark, :8081) is the trusted verification
  instrument; `tools/http_shots.js` screenshots 6 angles for the gate.

**genbear3 bake-off launched (operator: "test all methods, the dyad will decide"):**
- Anchor: SDXL (local, free, no gate) → `capture/genbear3/anchor_00..03.png`; anchor_03 chosen
  (most uniform near-black background, classic proportions, black bow).
- Lane A: EscherNet full-sphere view grid (kxhit/EscherNet) → AnySplat. [running]
- Lane B: Zero123++ fixed 6-view grid (sudo-ai/zero123plus-v1.2) → AnySplat. [running]
- Lane C: LTX-Video local I2V orbit (replaces Seedance, $0) → proven movie recipe. [running]
- Lane D: DiffSplat text→3DGS direct (chenguolin/DiffSplat), no anchor. [running]
- Each lane: own Rule-0 falsifier named up front, deliverable = `models/genbear3/lane*.splat`
  + 6-angle previews in `.tmp/lane*/`. Dyad judges all on the same gate.
- fal.ai spend remains zero. All local, all open weights.

---

## 2026-08-20 — bake-off RESULTS, the aligner bug, D3/D4 refinement rounds

**Bake-off final standings (ledger: `capture/genbear3/bakeoff_results.jsonl`):**
- laneA_eschernet struct 0.0 · laneB_zero123pp struct 0.0 · laneC_ltx struct 0.0 — all dead.
- laneD_diffsplat struct 1.0 — the only structurally solid lane (DiffSplat SD1.5 text→3DGS).
- genbear2_photo struct 0.5 (translucency on the 6-angle gate).

**ALIGNER BUG (caught 2026-08-20, on record):** `senses.align` fuzzy-scored long
"Verdict: No" answers as photo 0.9–1.0 against PHOTO_EXPECTED — every photoreal number in
the ledger before this date is unreliable; the eye's WORDS said NO on all of them
(genbear2 "Verdict: No" scored 0.9; laneE 1.0; d2 candidates 1.0). The eye's words are the
terminal. FIX: `tools/judge_lane.py` photo gate now requires an explicit `Verdict: YES/NO`
final line parsed from the eye's own reading (`_photo_verdict`); fuzzy align kept only as
a secondary field. Second instrument fix: `tools/http_shots.js` hides the viewer HUD
before screenshots — the eye was citing the UI overlay itself as a "3D viewport" tell.

**D3 round (lane D refinement, `tools/d3_refine.py`, every command logged to
`capture/genbear3/d3_commands.jsonl` — the original laneD prompt was never logged and is
lost; that failure mode ends here).** Lever: 20→50 steps + face-detail prompts (embroidered
nose / glass button eyes / amber glass eyes), 4 prompts × seeds {0,7} + one CFG-9 probe.
RESULT: 5/9 structure ≥ 0.7, ALL 9 photo Verdict: NO. HUD-free re-judge of the 4 strongest
(incl. original laneD): still all NO. **Falsifier fired: SD1.5 text-cond sampling settings
are exhausted; the lever is not steps/prompts.**

**D4 lane (image-conditioned DiffSplat):** new `external/diffsplat/infer_sd15_image_ply_only.py`
ports the official image-cond path to PLY-only (v_prediction, in_channels 11, guidance 2.0
per official warning, plucker first-view concat; rembg wrapper bypassed — it shells to
`python3`, which does not exist on Windows, and swallows the failure). Checkpoint
`gsdiff_gobj83k_sd15_image__render` downloaded (ungated). d4_anchor03_s0: 60,533 Gaussians,
fur visibly more photographic BUT structure 0.2 — hollow scooped-out back, and the
judge shots show a profile where the face should be (camera-geometry mismatch suspect:
anchor is straight-on, default elevation 10 passed; el=0 run queued).

**Blocked lever (operator action needed):** DiffSplat's best released backbone is
SD3.5-medium (`gsdiff_gobj83k_sd35m`, ungated) but its base text encoders/VAE come from
`stabilityai/stable-diffusion-3.5-medium`, a GATED HF repo. No HF token on this machine.
To unlock: free HF account → accept the SD3.5 license → `huggingface-cli login`.

**D4 seed round (results):** d4_anchor03_s0 struct 0.2, s7 struct 0.7 (but eye read it as a
DOG — wrong object), s42 struct 0.1, el0_s0 struct 0.1; photo Verdict NO on all four.
Elevation 0 did not fix the mismatch. **D4 falsifier fired: image-conditioned DiffSplat
(SD1.5, GObjaverse hard-surface training) is structurally broken on plush — hollow backs,
wrong-object drift. Not a settings problem; a training-distribution problem.**

**D5 round (SD3.5-medium text-cond DiffSplat — the operator unblocked the gated repo by
accepting the SD3.5m license; HF login as GhostDragonAlpha):** new
`external/diffsplat/infer_sd35m_ply_only.py` (checkpoint `gsdiff_gobj83k_sd35m__render`).
Best fur texture of any DiffSplat lane — eye praised the mottled fur. BUT the geometry is
SYSTEMATICALLY folded/lying (bear tipped forward, face down): `tools/orient_splat.py`
gained `--rz`, and ±90° rx/rz probes showed NO rigid rotation fixes it — the fold is in the
generated geometry, not the pose. d5_golden_emb_s0 struct 0.75 ("upside-down in all views"),
photo NO. **D5 falsifier fired: SD3.5m improves texture, not structure.**

**D6 round (SD3.5m image-cond, checkpoint `gsdiff_gobj83k_sd35m_image__render`):**
d6_anchor03_s0 struct 0.2 — melted; top/bottom views hollow/cavernous per the eye.
Photo NO. **D6 falsifier fired. CONCLUSION on the whole DiffSplat lane (D3–D6): the
256px/4-view gsrecon architecture is exhausted for photoreal plush. Texture ceiling and
structural priors are both training-distribution-bound. Lane closed.**

**Lane F (Hunyuan3D-2.1 image→PBR-mesh → `ChimeraEngine/native/mesh_to_splat.py`):**
`tencent/Hunyuan3D-2.1` (UNGATED — note the lowercase org; `Tencent-Hunyuan/*` 404s),
own venv `.venv-hy3d` (Py 3.11, torch 2.5.1+cu124; needs `HF_HUB_DISABLE_SYMLINKS=1` and
`torchvision_fix.py` before paint imports; run scripts with cwd=`external/hunyuan3d-2.1`).
Shape (`.tmp/f1_shape_only.py`) → `f1_hunyuan_anchor03_untextured.glb` (351k verts);
paint (`.tmp/f1_paint_only.py`, max_num_view=6, resolution=512) →
`f1_hunyuan_anchor03.glb` (23,938v/40,000f, baseColor+metallic+roughness 2048²).
One hallucination: the shape model added a ~2×2-unit wooden PLANK under the bear.
`tools/f1_strip_plank.py` removes it: the mesh is ~219 disconnected shells (bear ≈ 200
small parts; plank = 2 giant flat sheets), so it drops plank-LIKE components (flat up-axis
extent <0.05, horizontal span >1.0) + a bottom-slice rim cut — "keep largest component"
would keep the plank's inner disc and delete the bear (learned the hard way).
Stripped: 18,955v/30,778f. Turntable verified by eye (me): coherent bear all around —
face, bow, white paws/snout front; seamed fur back. `mesh_to_splat.py --n 500000` →
`f1_hunyuan_anchor03.splat`.

**Judge-instrument fix #3 (orientation):** `cb.save_splat` pre-applies the SPLAT_ORIENT
inverse, so mesh-derived splats must be judged with the viewer's DEFAULT orientation;
`tools/http_shots.js` and `tools/judge_lane.py` gained an `orient` arg (0 = DiffSplat/raw,
1 = save_splat lane). First f1 judge ran orient=0 (bear sideways) — still struct PASS 1.0
(same solid object, top/bottom correct — first-ever full structural pass). Re-judged
upright: struct 0.9, photo Verdict NO. The eye's bill of particulars: no fur micro-texture
("plastic/clay"), NO EYES, white paw pads (should be dark), warped bow, flat lighting on a
black void.

**Diagnosis (measured, not guessed):** the 2048² painted atlas DOES carry strand fur on
body islands, but the FRONT lost the anchor's defining detail — eyes washed out, black
nose → brown dot, dark paw pads → white. The anchor (`capture/genbear3/anchor_03.png`,
1024²) is genuinely photoreal. Move: `tools/f1_projective_bake.py` — weak-perspective
registration (scale/cx/cy fit by silhouette IoU against a full-res rembg cutout,
`anchor_03_rgba_1024.png`, bria-rmbg-2.0), per-face depth map for occlusion, per-texel
barycentric bake of the anchor onto front-facing texels. Rule 0: STATEMENT — the NO is
dominated by paint-stage albedo loss, not geometry or splat count. PREDICTION — eyes,
black nose, dark pads, and fur strands return in the front render. FALSIFIER — if the
re-judged front still reads eyeless/smooth, registration is wrong (head bow) and this
approach fails. [bake running]

**F1 bake round (results):** `tools/f1_projective_bake.py` — silhouette fit converged at
s=1024.5 cx=551 cy=526 (IoU 0.604 with anisotropic search; the mesh bear is more compact
than the anchor — the similarity fit can only do so much, pose differs). Bake restored the
BLACK NOSE + mouth line + dark leather paw pads + richer leg fur (verified in the render).
Eyes did NOT bake (their surface tilts away from the camera — normal gate), so
`tools/f1_eye_decals.py` planted them by direct raycast from the anchor's measured eye
positions (465,302)/(605,295) → UV decals with highlight. Face verified: two button eyes,
nose, mouth. Known cosmetic flaw: the bake left high-contrast blotchy patches on the
feet/legs ("cow print" — the anchor's shadowed inner-leg fur transferred with its shading).

**INSTRUMENT FINDING (decisive, 2026-08-20): the qwen3.8 photo gate is unreachable through
this render path.** Controls run through the identical 6-angle gate:
- `teddy.splat` (the bear the OPERATOR approved as "beautiful"): struct 1.0, photo NO
  ("fur too uniform, flat black eyes, sterile lighting").
- Same on a composited studio backdrop (soft gradient + floor, kills the "black void"
  tell): still NO ("flat lighting, painted fur").
- `koala_mesh2splat.splat` control: renders FLAT GRAY in the viewer (stale/broken artifact,
  no color) — and the eye still hallucinated a fur/eyes description over a gray blob.
  Note: the eye also intermittently attends to only 3 of 6 frames.
Conclusion: the photo gate measures the unlit 720p render path + the eye's own resolution
limits more than the asset. It has never passed ANY splat, including the best one the
operator ever approved. Taste bottoms out in THE HUMAN — final verdict escalated to the
operator with the interactive viewer.
