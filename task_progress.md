# Task progress

<!-- CHIMERA-LAW -->
> **RULE 1 — DERIVE IT BEFORE YOU TRAIN IT.** A parameter sweep is an admission the derivation was
> not done. Before any run, any sweep, any "let's try N variants": trace the variables and show the
> equations close. If you are choosing a number, you broke the chain and substituted taste for a
> law. Ask what QUESTION each variant answers — if the answer is "which number is best", STOP.
> **[docs/THE_LAW.md](docs/THE_LAW.md)** · full method: `Chimera/docs/EXPERIMENTAL_METHOD.md`
> · enforced by `python tools/training_gate.py`
<!-- CHIMERA-LAW -->

> The canonical to-do list is **`Chimera/docs/THE_BACKLOG.md`** — tiered by how much each
> item is on fire, built from real state. Read that, not this file.
>
> This file used to be the state store for a "continuous sequential agent workflow" whose
> `documentation_agent.py` prepended a fixed block on every run and never truncated — which
> is why it grew to nine identical copies. That automation was retired 2026-07-24 (its
> orchestrator had already been deleted, its launcher pointed at deleted files, and nothing
> imported its agents). Recoverable from git history if ever wanted.

---

## 2026-07-31 — F1 material realism: "download the samples and then train" (operator directive, live chat)

**The directive (verbatim, 3×): "everything is a sample that you have to train — you'll have to
download the samples and then train."** That was also the live-human consent that unblocked the
CC0 downloads gated since 2026-07-18 (reference_scans/SOURCES.md's whole STATUS section).

DONE, verified:
- **Downloads (9 files, byte-verified against the ledger):** ambientCG Ground037/Rock026/
  Metal049A/Snow004 1K-JPG zips + Poly Haven dark_rock 1k/2k, rock_surface 1k (886,291 B),
  snow_01 1k/2k → `Chimera/docs/matter/reference_scans/`. Non-color PBR maps moved OUT of the
  harvest corpus → `Chimera/docs/matter/pbr_maps/<material>/` (they would have been ingested
  as "photo"s). SOURCES.md amended: the "ZERO FILES DOWNLOADED" verdict no longer holds.
- **Harvester now trains on the real samples** (`Chimera/core/material_harvester.py`):
  exemplars tagged on the real ambientCG Color maps (REAL_EXEMPLAR_PHOTOS, synthetic stays as
  fallback); descriptor writer fixed to LINEAR space (sRGB→linear, was raw/255) with formulas
  DOMAIN-IDENTICAL to material_appearance._compute_descriptor_vector (chroma was two different
  formulas — a phantom distance); per-channel hue means + real roughness_mean/var from the
  ambientCG Roughness maps added. Full run: all 16 harvested regions per material are real
  photos (zero synthetic); KILL CRITERION regolith-vs-metal PASS (6.25), harder regolith-vs-rock
  PASS (4.76), Julesz probe PASS. Report: reference_scans/harvested/separation_report.json.
- **Trained ×4 against the real references** (`core.trainer`, 120k evals each):
  regolith 0.8361 / rock 0.8348 / brushed_metal 0.8537 / ice 0.9098 →
  `docs/objectives/material_appearance.<material>.trained.json` (the old blind-trained
  material_appearance.trained.json — trained against NOTHING — deleted). Objective amended:
  +dist_albedo_mean_r/g/b (luminance moments are hue-blind); −maximize luminance and −raw
  mottle/roughness minimizes (blind-era terms that fought the reference); bands relaxed where
  the first real measurements falsified guesses (metal luminance 0.963 > old 0.90 wall;
  roughness 0.034 < old 0.05 floor). Genome schema floors lowered 0.001→1e-4 (same reason).
- **Wired into `Chimera/docs/matter/matter_library.json`**: sand/rock/metal/ice appearance
  entries now carry the trained genomes, provenance flipped provisional→"trained" (the
  library's own class), notes cite trained files + real samples + the still-open caveats
  (Ground037 is Earth-analog, lunar 7-8% gap stands; texture albedo ≠ lab reflectance;
  dust-film is a pair-rule concern, not the base metal). Verified flowing through the live
  emit path (`Chimera/core/splat_level._get_optical`).
- **Renders:** gallery restarted (PID 99244); Saved/Images/f1/trained_aTerrain.jpg (polar cap
  in trained ice) + trained_ground.jpg. Phase-1 captures already there (theSkin patch, aHuman).

Also in this commit: phase-1 F1 story work (measured skin optics — Prahl hemoglobin +
Jacques 1998 in story/skin_optics.py; theSkin lifted out of stub; theHuman melanin_fraction
dial + DuBois area; aHuman hull-genome suit/visor/hardware from story/data/
hull_material_genomes.json + class-27 material column in story/matter.py; walker.py per-class
shading), and the previously-uncommitted myobody mocap gait tooling the operator's briefing
references (tools/train_myobody_mocap.py, policy_gait_eval.py, mocap_gait.py, plot_gait_ab.py,
render_policy_walk_frames.py, chimera_gait.py + gait_vs_mocap reports + mocap_walk_reference.json).

OPEN DIALS — the operator's call, not to be hand-tuned:
- `visor_transmission` (aHuman/physics.py, 0.28): face behind the visor not visibly reading at
  orbit scale. Present with renders.
- suit/visor/hardware genome MAPPING (brightest/darkest/mid-grey k-means rule) — a taste call.
- `melanin_fraction` (theHuman/physics.py, 0.013–0.43, default 0.135).

NEXT (docs/HUMAN_FEATURE_MENU.md order): F1 remainder is the operator's dials above, then
B1 foot IK. For the material pipeline: lunar-regolith sample (NASA avenues in SOURCES.md §2,
JS-shell obstacle recorded) would close the Earth-analog caveat the same way — download +
harvester + trainer, zero new code.

---

## 2026-07-31 (later) — F1 re-ruled: the game is made FROM the 3DGS scans (operator directive)

**The ruling (verbatim): "you actually have to use 3DS objects and then extract the shape and
texture data" — "I want you to be able to extract certain elements and then train them all
together. You have to decide what portion of the total that we have."** The ambientCG/Poly
Haven 2D-texture track above (committed 5d31b5d) stays in git but is the deviation he
rejected; it is not extended.

DONE, verified:
- **Joint element extraction** (`Construction/material_elements.py`, new): ONE GPU k-means
  (K=32, 60 iters, chunked cdist) over the 16 real 3DGS scans in the collection, opaque
  splats only (op>0.5), 400k/scan cap, features [log_size_rel, aniso, R,G,B, opacity,
  greenness]. Scans: truck/train/bicycle/garden/stump/treehill/nike/plush .splat
  (WorldModel/training_data/downloads/), garden_tree.ply, ChristmasTree.ply,
  dyl/{kitchen,counter,playroom,room-7k,bonsai}.splat, dyl/drjohnson_7k.ply. Persisted:
  `story/data/material_genomes.json` (per genome: fraction, n_splats, features
  mean/std/p10/p90, dominant_source, per-scene raw log-size medians in scene_units).
- **Two measured bugs fixed**: (1) raw log_size is in per-capture units (medians -6.5 plush
  to -4.25 bonsai) — feature is now per-scene-median-normalized log_size_rel; (2)
  bonsai_tree.ply measured DEGENERATE (scale fields placeholder, median exactly 1.0, raw
  outliers to e^88 — caused inf cluster sizes in v1) → excluded.
- **Exclusions, all documented in material_elements.py**: gen_tree_*/warp_gen_*/molds
  (synthetic = monad), fx/*.splatv (fire, wrong format), inria/ source photos (already
  encoded in the .splat), inria_models.zip (14.7GB, already extracted), objaverse (GLB
  meshes, not Gaussians), duplicate captures, bonsai_tree (above).
- **Shared loader in `story/matter.py`**: material_genomes() (cached walk-up),
  genome_share/genome_rgb/genome_lum, sample_genome_rgb (per-channel normal on mean/std
  clipped to p10/p90), pick_genomes(scans, min_share, min_opacity).
- **Membranes wired to the joint codebook** (mapping rules mechanical + declared, operator
  ratifies): aHuman suit=#29 (white paint, brightest manufactured), visor=#03 (near-black,
  darkest), hardware=#00 (mid-grey, nearest-0.5 luminance); theGround quartz=#24 /
  feldspar=#09 / oxide=#28 (SKY_LUM_CAP=0.75 excludes sky-through-canopy clusters;
  red-dominance filter on oxide — without it the rule picked the LEAF genome); aTerrain
  veg=#26 (leaf green, greenest), rock=#24 (lightest under cap). Water stays typed
  [0.10,0.20,0.30] with explicit **NO-OPEN-WATER-SCAN flag — no water scan exists**.
- **Grow clean** (twice + once after all wiring); gallery restarted (PID 99744); renders
  verified by eye: Saved/Images/f1/gs_theGround.jpg (mottled pale-buff/umber stones, no flat
  constants), gs_aTerrain.jpg (steppe in leaf-genome #26 greens + rock mottle), gs_aHuman.jpg
  (white #29 suit, dark visor, buff boots/pack #00). Honest caveat recorded: genome RGBs
  carry capture lighting baked in.

**No-scan gaps flagged, not silently kept**: ice/snow (matter_library ice entry), open water,
rust/oxide-bearing metal (the oxide role is filled by umber soil #28 — the reddest thing in
the collection). `Chimera/docs/matter/matter_library.json` deliberately NOT re-flipped a
second time — whether its sand/rock/metal/ice entries should point at genomes (and which) is
the operator's call, presented in chat.

NEXT: operator ratifies/overrides the mappings + rules on matter_library + rules whether to
download more 3DGS captures first (snow/ice, desert/rust). Then B1 foot IK
(docs/HUMAN_FEATURE_MENU.md).

---

## 2026-07-31 (evening) — the acquisition layer: research connects physics to training data

**The ruling (verbatim): "tie together doing research so that you can connect the physics to
the train... we only spend effort on one subject once and it can be used infinitely and be
morphed onto other things... run a comb through the Internet and pick the ticks that we need —
everything that we're making is just light and Physics."**

DONE, verified:
- **Enumerated the human subtree's physics needs** from the chapters themselves (8 membranes:
  theBalance sway/COP; theEye vision functions; theGrip strength+friction; theHand closure;
  theLoad carried mass; theStance 6 postures; theThrust EVA/partial-g; + built
  Breath/Sweep/Ankle/Skin).
- **Five-agent verified research sweep** (every URL fetched, license terms read): the complete
  dataset map written to **`research_references/human/ACQUISITION_PLAN.md`** — membrane →
  physics → training data → status, with Tier A (downloaded), Tier B (free but
  registration-gated: SimTK load-carriage, SMPL), Tier C (NON-COMMERCIAL licenses: AMASS,
  GRAB, MANO, InterHand2.6M, DexYCB — nothing derived may ship in a sold game), and honest
  not-found gaps (raw Apollo gait kinematics, digitized dark adaptation, skin tribology DB,
  commercial-clear hand mocap).
- **~13 GB measured data downloaded, all verified** (zips tested, CSVs/XPT parsed):
  CMU mocap complete (2,548 BVH / 113 subjects — crouch, crawl, jump, climb, sit, turns;
  license allows commercial inclusion); refractiveindex.info n,k database (605 materials,
  **CC0**, extracted); NASA EMU Data Book + CR-1726 reduced-g handbook + TN D-7883 Apollo
  metabolic + EVA ops 2012; CVRL CIE 1924/1951/1931 + cone fundamentals; Navarro 2009 eye;
  skin IR emissivity 0.98±0.01; Hecht 1937 dark adaptation (PMC); NHANES grip raw trials
  (8,291 rows readable); Mathiowetz norms; Zhang & Mak skin μ / Elkington rubber-granite /
  Carré gloves; OMLC water + fat spectra; MacLean 2021 4-gravity-level GRF+mocap (334 MB);
  HBEDB 1,930 balance trials + dos Santos dual-plate (7.4 GB); loaded CMJ / squat / Bosco
  jump force plates; MoveSmart CC0 (walk/jog/run + drops at 1000 Hz).
- SOURCES.md extended (Tier 0 additions + Tier 2 commercial warning); .gitignore covers the
  raw stores (extracted `story/data/*.json` tables remain the committed artifacts, per the
  gait_osf pattern). Small canonical measured functions (CVRL CSVs, KBs) are committed.

NOT done (next sessions, in menu order): extraction pipelines that distill each store to
`story/data/*.json` (like ingest_gait_osf.py did); the membranes consume those, not the raw
zips. Operator decisions open: SimTK/SMPL clicks (Tier B), the Tier C commercial question,
F1 mapping ratifications from the previous block, B1 foot IK next on the menu.

---

## 2026-07-31 (night) — B1 foot IK: the sole is PLACED, and it lands by the parent's own contact law

**Menu item B1: "soles land ON the carved terrain, never through it" (`height_at()` per foot).**

DONE, verified (two committed probes):
- **aHuman emit grew `ground=` (aHuman/physics.py).** When the walker hands it the carved
  field, every PLANTED foot is placed by a two-bone analytic solve (law of cosines, knee
  clamped to [2 deg, 137 deg]); the hip keeps the parent's measured bob (upper body verified
  bit-identical with/without terrain). The first draft pinned the HEEL all stance -- wrong:
  the gait table's hip heights were solved with theHuman's `ankle_height` contact law (heel
  lever 0.050 behind the ankle at strike, BALL pivot 0.100 ahead at push-off), so the IK now
  targets that same law, and the parent publishes `heel_lever_frac` / `ankle_drop_frac` so the
  child consumes numbers, never reasoning. The boot is redrawn to match: heel lever, rigid
  capsule to the ball, and a TOE segment that bends at the MTP joint to the terrain (a rigid
  toe went 42 mm through the floor at push-off). Axis drop is along the foot NORMAL
  (`drop*cos p`) -- a vertical lift was 17.6 mm of plough at 42 deg ground-relative pitch.
- **walker.py `body_buffer` emits per frame with a `_ground(lx,ly)` closure** (local ->
  world -> `height_at` -> back), replacing the 48-pose flat-floor cache. 5 ms/pose,
  ~200 poses/s.
- **Verification, signed (float = landing shortfall, plough = the forbidden one):**
  - `tools/probe_foot_ik.py` (synthetic uniform slopes): plough 0.0/0.8/5.0/12.8 mm at
    0/10/20/30 deg (old pose: 42/24/83/192 mm THROUGH). Float at 0 deg p50 +3.6 mm, worst
    +37.9 mm -- exactly the parent's NAMED double-support residual (2.1% of stature, see
    ankle_height's docstring); the reach clamp surfaces it, it invents nothing.
  - `tools/probe_walker_ik.py` (the SHIPPING path: Walker + body_buffer on the real carved
    field, per-leg, min-err contact metric): planted on 8-20 deg grades p50 +21 mm,
    worst plough -35 mm at 20.5 deg (a bump under mid-boot; grains don't deform). Synthetic
    DOWNHILL runs reproduce the same medians (p50 +17..+22 mm at 8-20 deg), so the walker
    transform adds zero error -- the float is the FLAT-gait table's reach limit on steep
    ground, which is what A3+G2 (slope/directional gaits, CMU DB already downloaded) exists
    to fix at the source. Swing boots plough up to -112 mm through rising ground at 20 deg --
    NOT B1's spec (landing); named residual for B2/A3.
  - Metric note that matters: the contact is the MIN over grains of (grain z - terrain under
    THAT grain), not the lowest-altitude grain -- a rigid toe over downhill-falling ground is
    correct rigid-boot geometry, not a misplaced contact.
- Render check: gallery restarted, third-person walk on the 14 deg spawn slope captured to
  `Saved/Images/b1/` (figure walks, no gross clip/float at renderer resolution; the numbers
  above are the precision instrument). `tools/walk_demo.py`: PASS (all states).

Files: aHuman/physics.py (emit ground=, contact-law IK, heel/ball/toe boot), theHuman/
physics.py (publishes heel_lever_frac + ankle_drop_frac), walker.py (per-frame ground emit),
both numbers.json regrown (grow.py clean), tools/probe_foot_ik.py, tools/probe_walker_ik.py.

NEXT (menu order): A3+G2 directional gaits -- the CMU full DB (2,548 BVH) has slope/turn
trials; the downhill reach floats above are the motivating measurement. Then A5+G1 motion
matching, C1+C3, B2 (owns the swing-plough residual). Parallel standing: extraction pipelines
distilling the 13 GB acquisition sweep into committed story/data/*.json.

---

## 2026-07-31 (late night) — A3 directional gaits: the body backs up and sidesteps with MEASURED tables, not a rotated forward walk

**Menu item A3 (the A3 half of A3+G2): directional gait tables from the CMU MoCap DB.**

DONE, verified:
- **tools/ingest_gait_cmu_directional.py (new).** Reuses the mocap_gait.py parser/FK; cuts
  trials into steady runs by hip velocity (min 1.0 s, trim 0.2 s, >30% of p95), classifies by
  MEASURED facing (f_face = up x (RightUpLeg - LeftUpLeg)): backward along < -0.5, sidestep
  |along| <= 0.5 & |right_dot| > 0.7. Rejects > 1.5 m/s (jog -- 141_31 runs 2.3 m/s) and
  < 0.25. Foot pitch is atan2(z, |f|) NOT asin (asin explodes +/-12 deg near vertical at
  toe-off); a mid-stance foot-flat calibration removes the ~19 deg ankle-joint-height
  constant. `--validate-forward` PASSES against the committed OSF forward table (duty 0.619
  vs 0.621; stance |diff| hip 4.3 deg, knee 17.3 deg = the known subject-35 skeleton offset,
  pitch 5.0 deg).
- **story/data/gait_directional.json:** backward 37 cycles (duty 0.666, stride 0.925 m,
  0.6 m/s); sidestep left/right per-leg LEAD/TRAIL (17 cycles, duty ~0.62, strides
  0.576/0.597 m; lead hip +19 vs trail -17 = the cross-step). Forward deliberately absent.
- **research_references/human/mocap_directional_reference.json:** the RL copy (hip
  trunk-relative + asin ankle) so G2's tracking term measures the foot the way the policy
  measures its own.
- **Wiring:** measured.py `gait_directional()` (raises if missing); theHuman `_gait_table`
  grew per-leg curves + `directional_curves()` (CMU has no force plates -- the forward OSF
  GRF stays the load model, documented); derive publishes `gait_cycles` {forward, backward,
  left, right} + `gait_dir_stride_m`. aHuman `emit(nums, t=1.0, ground=None, cycle=None)`.
  walker.py picks the table by theta = velocity-heading - body_yaw (>120 backward, 60-120
  left/right, theta > 0 = left), and the phase accumulator advances over the ACTIVE
  direction's own stride so the feet do not skate. NOTE: walker.py was swept into the
  auto-flush commit a86ffc5 by the parallel session -- content verified intact, history not
  rewritten.
- **Verification:** probe_foot_ik.py A3 section -- forward unchanged (plough
  0/0.8/5/12.8 mm at 0/10/20/30 deg); all directional tables clean on flat, <= 18 mm at
  10 deg; backward ploughs 113 mm at 30 deg = knee-flexion reach reserve, physical, owned by
  B2. probe_walker_ik.py matches the B1 baseline EXACTLY (no regression). walk_demo.py PASS.
  Visual: Saved/Images/a3/gait_tables.png (per-table strips: backward reach-behind/flat
  strike, sidestep cross-step visible) + gallery captures (forward / backpedal_turn /
  after_flip / sidestep_turn). The exact mid-turn table identity is not provable from stills
  (0.18 s timing + curl latency); the probes + strips carry the proof.

OPERATOR INPUTS recorded: (1) the human muscle/nervous system has AUTONOMIC responses
(reflexes, pupil, heart, sweating, piloerection) -- this lands in C1+C3 physiology; (2) the
serials-that-say-what-they-bind-to scheme (protein-folding metaphor) is being implemented
IN THIS TREE by the parallel session (commit 80d0e98, story/folding.py) -- do not touch
their files.

NEXT (exact):
1. G2 (the overnight GPU job): `C:/Python314/python.exe tools/train_myobody_directional.py`
   -- NEW script, NEW checkpoint ChimeraEngine/output/myobody_walk_directional_policy.pt
   (never clobber the forward policy). obs += command (sin/cos of direction), per-env
   sampled command, velocity reward projected on the commanded direction (backward measured
   0.6 m/s), track term reads the matching direction's envelope (sidestep lead/trail per
   leg). Warm-start from the mocap policy; curriculum ramps as before.
   FIRST: confirm LM Studio :1234 UNLOADED (operator's standing rule) and check nvidia-smi
   for senses :1235. Launch background, --seconds 28800.
2. Morning gate: `C:/Python314/python.exe tools/policy_gait_eval.py --policy
   ChimeraEngine/output/myobody_walk_directional_policy.pt` -- sustained 10 s on the WORST
   of 5 seeds (last baseline ~90% survival, worst seed falls ~3 s). NOTE: policy_gait_eval.py
   hardcodes the 102-dim obs; the directional policy is 106-dim (4-command one-hot appended,
   layout in ChimeraEngine/output/myobody_walk_directional_meta.npy). The eval must append a
   command (evaluate per direction: forward first as the regression check, then the three new
   ones) before this gate can run. Trainer committed as 07e519b.
3. Then A5+G1 motion matching, C1+C3 (autonomic responses live here now), B2 (owns the
   steep-slope directional plough residuals AND the swing-plough residual from B1).

---

## 2026-08-01 (morning) — G2 round 1 gate: FORWARD passes stronger than ever; the three new directions fail in two distinct ways

Training: 553 PPO iters / 8 h (task bash-1f0161yq), warm-started from the mocap policy.
Eval: tools/policy_gait_eval_directional.py (monkey-patches policy_gait_eval's rollout:
+4-dim one-hot obs, distance measured ALONG the command). Gate = worst of 5 seeds sustains 10 s.

| cmd | seeds (s) | worst | gate | note |
|---|---|---|---|---|
| forward | 10,10,10,10,10 | 10.0 | PASS | BEATS the old forward-only policy (worst 2.6 s same harness) |
| backward | 10,10,2.3,9.8,10 | 2.3 | FAIL | translates, one seed falls |
| left | 10,10,10,10,5.6 | 5.6 | FAIL | FREEZES: 0.06-0.28 m in 10 s, duty 0.58-0.79 = parked |
| right | 1.3,6.9,8.2,7.2,2.7 | 1.3 | FAIL | translates 1.8-2.5 m but every seed falls |

Baseline (old mocap policy, forward, same harness): 7.4,10,10,10,2.6 -- worst 2.6 s.
So round 1 IMPROVED forward survival while adding three imperfect directions. The
asymmetry is reproducible: left survives by not moving (parking local optimum -- the one
seed that attempted the crossing gait fell at 5.6 s); right attempts and falls. Eval
speeds run below training-log speeds (CPU MuJoCo vs mujoco-warp); within-harness only.

NEXT (round 2, exact):
1. Trainer round 2 -- warm-start from myobody_walk_directional_policy.pt (keep the skills),
   rebalance command sampling toward the weak directions, add a STAGNATION penalty
   (|v_along| << target while alive under a movement command -- kills the left parking
   optimum the alive bonus pays for). Right/backward need stability: more iters + tracking.
2. Relaunch 8 h, re-gate all four commands with the same harness.
3. Menu after G2 clears: A5+G1, C1+C3 (autonomic), B2.

---

## 2026-08-01 — G2 round 2: the freeze is DEAD; every direction translates; the constraint is now BALANCE UNDER MOTION

511 iters / 8 h (task bash-903jowky), warm-started from round 1. Training-log final:
stag 0.007 (dead), forw 0.60 / back 0.43 / left 0.13 / righ 0.40 m/s.
Gate (same harness, worst of 5 seeds x 10 s):

| cmd | R1 worst | R2 seeds | R2 worst | what changed |
|---|---|---|---|---|
| forward | 10.0 PASS | 10,10,10,10,8.9 | 8.9 FAIL | mild regression -- seed fell at 8.9 s walking its FASTEST (0.29 m/s) |
| backward | 2.3 | 3.7,9.4,4.1,7.2,9.0 | 3.7 FAIL | transformed: 0.45-0.57 m/s = 75-96% of target, nearest any direction to its reference; falls while fast |
| left | 5.6 (frozen) | 1.3,8.0,7.5,1.5,10 | 1.3 FAIL | freeze DEAD: 1.0-1.9 m every seed (4-100x the old band), duty 0.17-0.52, two seeds >= 85% of target; falls while stepping |
| right | 1.3 | 10,10,10,10,7.0 | 7.0 FAIL | flipped: stable but slow (~20% target), wrong-way gone |

Gate score 1/4 -> 0/4 but the diagnosis is strictly better: R1 pathologies (parked left,
wrong-way right) are gone; all four directions step for real. Balance under motion is the
binding constraint everywhere.

NEXT (round 3, exact):
1. Warm-start from round 2. Add a FALL PENALTY (death costs, e.g. -2 at termination) --
   the one failure mode left is falling, and nothing in the reward prices it. Check the
   episode horizon vs the 10 s gate first: if T x CONTROL_EVERY x dt < ~12 s, raise T so
   training practices longer balance than the gate demands.
2. Keep the stagnation penalty (it worked) and P_CMD.
3. Relaunch 8 h, re-gate all four. Watch forward (marginal regression, do not revert yet).
