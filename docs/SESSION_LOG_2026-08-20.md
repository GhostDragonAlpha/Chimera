# SESSION LOG — 2026-08-20

The day the pipeline changed shape. Morning: photogrammetry-of-AI-video (the genbear lane)
hit its ceiling. Afternoon: the operator set the governing architecture — the **authored
pipeline**: a CAD-style parametric body is the gravitational substrate, paint particles
rain onto it and settle by physics, appearance is spray-painted on, regions on the surface
are addressable and repaintable. The bear is the demo; **this is the game-asset workflow**.

## What died and why (measured, not vibes)

- **Single-image 3D generation (TripoSplat/TRELLIS class) is rejected as a source.** The
  SOURCE gate (front == back, texture AND topology) has never passed on any single-image
  mesh: TripoSplat T-pose had 4 arms and a 40–50% darker back; TRELLIS vertex-color spread
  was 0.5–4% but never eye-verified and is 7-float, not the 14-float 3DGS the engine eats.
- **AI-video photogrammetry (Seedance orbit → COLMAP → gsplat) works but is spendy and
  soft.** It produced the first SOURCE-pass bear (08-19) but multi-pass video drift leaves
  alignment ghosts. Measured this session: **simultaneity is worth +4.1 dB** — the eq-only
  SV3D bear (21 one-pass views, `models/genbear3/eqonly_med.splat`, 31,396 splats) scored
  **27.21 dB held-out** vs 23.1 for the 101 mixed-pass view set. One consistent pass beats
  five inconsistent ones.

## The authored pipeline (the architecture, approved step by step by the operator)

1. **BODY** — `tools/teddy_catalog.py` + `tools/teddy_body.py`. A parts catalog: 13 slots
   (torso/head/muzzle/ears/segmented arms/segmented legs), 2–3 styles per slot, every
   segment with joint pivot+axis (JOINTS table), analytic mass, union SDF with smin blend.
   `assemble(style_map)` builds a bear from picks.
2. **SETTLE** — `tools/teddy_skin.py::settle_coat()`. The operator's model: **every part
   is a gravitational body.** Paint starts as an orb around each part; attraction ∝ part
   mass (capture dynamics), particle budget ∝ part surface area (coverage scales r², mass
   r³ — mass must not set the budget or small parts starve); union-SDF collision +
   tangential slide + mutual repulsion → an even coat at physics equilibrium. Every splat
   leaves the settle with an **identity**: `(part_id, uv)` — capsule uv = (axial t, angle),
   ellipsoid uv = (azimuth, elevation).
3. **PAINT** — positions welded after settling; only color/alpha/scale train.
   `tools/train_spray.py` spray-paints from ANY source (SV3D frames: 28.0 dB held-out on
   the authored body, `models/genbear3/authbear1.splat`; real CO3D photos: 21.4 dB,
   `authbear2.splat`). v5 experiment (outside-only shell + clamped offsets, 5000 steps)
   REGRESSED to 15.6 dB — the lesson: weld positions, don't clamp-train them.
4. **REGIONS** — a region is a named predicate over (part_id, uv). "Bow tie" = neck-band
   angle window → its own material channel → repaint just that subset. (Layer designed
   this session; demo pending.)

## CO3D real-data lane (validated)

- `capture/co3d/teddybear_00{0,1}.zip` (606 MB): 3 sequences × 202 frames + masks +
  pointcloud + annotations. Sequence 34_1479_4753 chosen (sharp portrait, 1066×1896).
- `tools/co3d_to_views.py`: PyTorch3D→OpenCV camera conversion
  (`R_c = D@R.T, t_c = D@T, D=diag(-1,-1,1)`, `f_px = f_ndc·min(H,W)/2`).
  **Validated: real pointcloud projected through converted cameras → 99.5% mask hit.**
- `tools/fit_body_to_cloud.py`: cluster labels assigned by PROJECTING centroids onto a
  photo frame (the CO3D world is upside-down — head at −y); centroid-anchored capsule +
  percentile ellipsoid fit, children FOLLOW parents → `.tmp/fitted_parts.json`.

## Tooling traps added this session (do not re-pay)

- gsplat CUDA runs ONLY via `cmd //c "tools\laneE_vcvars_run.bat <script>"` from
  `tools/gsplat/examples` with PYTHONPATH=examples; scripts take ABSOLUTE paths.
- gsplat `rasterization()`: omit the `backgrounds` kwarg (expects per-image shape; default
  black is right for masked training).
- gsplat Dataset returns TENSORS, not numpy.
- `cpp_bridge.save_splat` files need `orient=1` in `tools/http_shots.js` / the web viewer.
- `views.json` carries ABSOLUTE frame paths (trainer cwd is not the repo root).
- alpha is column 6 in `cb.load_splat` output (layout: pos3, rgb3, alpha1, scale3, quat4).

## Open

- gravity-settled coat: inspection pending (this log will be amended with the numbers)
- per-part shell min/max in the catalog (operator asked; trainer has a global band)
- fur strands on the settled coat (shelved until the coat itself passes the eye)
- gravity-driven joint posing (the CA membrane) — untouched this session

---

## Late session (post-CO3D lane) — T-pose source, paint-by-assignment, THE METHOD declared

- **T-pose source lane.** 5 SDXL T-pose candidates (`models/imagegen/apose_{100,200,307,411,523}.png`).
  `apose_100` was picked by the agent, REJECTED by the operator on sight; **`apose_523`
  authorized by the operator** — the source gate is now human-first, always.
- `gen_teddy_apose.py` parameterized (argv: input png + output name) →
  `teddy_523.splat` (262,144 splats). Presented in the interactive viewer; operator
  verdict: **success, one defect — too transparent**.
- `tools/densify_splat.py` (alpha floor/gain + scale growth). Measured: TripoSplat alpha
  min was already 0.6 — transparency is a footprint/pinhole problem, not an alpha
  problem. First pass grew splats 1.25× and the operator caught the tradeoff instantly:
  growth softens fur detail. Retuned to floor 0.7 / gain 1.5 / grow 1.1.
- **Paint-by-assignment** (`tools/paint_from_splat.py`): front-facing settled splats
  IDW-sample k=4 nearest same-part target splats; back-facing splats sample the
  z-mirrored front within the same part (the generator's averaged back is REPLACED by
  assignment, per the operator's design). First run exposed two defects in
  self-inspection: (1) head z-mirror painted eye color onto the back of the skull —
  fixed with a NO_MIRROR set (head/muzzle/eyes sample direct); (2) `w.sum(1)`
  broadcasting bug — fixed. Clean run: 60,000 splats, {direct 35,694, mirror_back
  24,306, twin 0, global 0}.
- **Real-photo hypothesis.** Operator: "the picture has to be of a REAL teddy bear."
  Correction logged: the good sitting `teddy.splat` also came from an AI image
  (`cand_classic.png`, Aug 16 → teddy.splat Aug 17); pose/lighting/detail separated the
  bears, not real-vs-generated. Test assets downloaded anyway (Wikimedia Commons:
  `.tmp/real_mumbles.jpg`, `.tmp/real_schultz.jpg`) — awaiting the operator's pick.
  Honest tension recorded: real bears are almost never photographed in T-pose.
- **THE METHOD DECLARED (2026-08-20, operator):** mandatory human-authorized stage
  gates; everything presented in the Chimera web viewer FIRST (2D picture before
  generation, splat, CAD, trained coat); manual method proven before the dyad is
  applied; every process becomes an MCP tool on the server that controls Chimera
  Engine. Written to `docs/THE_METHOD.md`; viewer enhancement (stage slots) follows.

## 2026-08-21 (late) — the build-our-own orbit lane, first real-photo run

- **Provenance saga closed.** The "good bear" = TripoSplat `teddy.splat` from
  `cand_classic.png` (262,144 splats exactly). The million-plus artifacts the operator
  remembered were TRELLIS *meshes* from the same image. `genbear_front.splat` (Seedance
  movie → COLMAP → 3DGS, Aug 19) is the shard-fur method the operator pointed at;
  abandoned then for generated-video camera drift (double-image ghost).
- **The fur law** (settled, written into THE_METHOD): fur relief needs multi-view
  disagreement; every single-image feed-forward model is a membrane by construction.
- **Operator directive:** build our own CAT3D-class lane from local pieces (SV3D +
  gsplat), after the survey found the described technique (1°-increment generative
  orbit + additive fusion + loop closure) is Google's closed CAT3D/ReconFusion.
- **Run:** source = the operator's real plush photo (`models/imagegen/real_plush.jpg`,
  OneDrive). New tools: `tools/cut_anchor.py` (rembg cutout → 1024² RGBA anchor),
  `tools/assemble_ring_poses.py` (ring dirs → poses.json; frame_00 of non-eq rings
  dropped — duplicate anchor view). `gen_ring.py` parameterized (`--anchor`/`--out`).
- 5 rings × 21 frames generated (eq, ±20, ±40; flip trick for negatives). Agent
  inspected frames at multiple azimuths/elevations: coherent back, correct flip,
  no ghosting visible in the views themselves.
- Focal calibration: best f=750px, interior of the 300–1500 grid, median reprojection
  2.97px at 576² — RULE 0 falsifier did not fire. Dataset: 101 images, r=1.562.
- Training traps re-hit and recorded for good: bash eats backslashes in absolute
  `--data_dir` (use forward slashes); the in-repo examples copy defaults
  `data_factor 4` (proven run used `--data_factor 1`); torch's extension loader needs
  `ninja` ON PATH even for the cached build (prepend `.venv-gs/Scripts` to PATH).

## 2026-08-21 (later still) — canonical space + the trainable-layers architecture

- **"Alignment is off" diagnosed at the root:** THREE stacked statistical rotations —
  the trainer's `normalize_world_space` (camera-align + PCA over the RANDOM init cloud)
  and then PCA again at export. Fix: `--no-normalize-world-space` + `orient_splat.py
  --pinned` (identity rotation; the commanded orbit IS the frame). Pinned bear exported:
  `models/sv3d_real/sv3d_real_pinned.splat` (58,019 splats, 0.35m, sidecar written).
  Trap recorded: `http_shots.js` defaults orient=0; save_splat-written files need
  orient=1 — mixed views scrambled the first orientation A/B.
- **THE SPACE declared** (`docs/THE_SPACE.md`): meters, +Y universe up, gravity-up
  declared equal for dev, OBJECT_UP as per-asset metadata; no silent normalization;
  every conversion writes its transform; capture density standard = hundreds of
  agreeing views, single-pass consistency over multi-pass count.
- **The bear declared the reference asset** (THE_METHOD): first occupant of every
  slot, the template all later objects copy.
- **Lane decisions, operator-gated:** 2D-only novel-view generators REJECTED (no object
  memory -> cross-view drift, measured 0.030 vs 0.004). The render->edit->retrain loop
  (Instruct-GS2GS/GaussCtrl class) survives as the TOUCH-UP pass, not the main lane.
- **The main lane became the trainable-layers architecture** (THE_AUTHORED_PIPELINE):
  trainable COAT = context-keyed patch genomes extracted from real ADC-trained scans
  (distribution, never the average; nap direction field included) + trainable BODY =
  parametric shape space over CAD fits of real scans (SMAL precedent). Build order:
  CO3D bears -> full 3DGS -> extract_patches.py -> spray upgrade.
