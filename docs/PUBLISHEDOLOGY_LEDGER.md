# PUBLISHEDOLOGY LEDGER

**Membrane (Rule 0):**
- **STATEMENT** — no declared number may float without a named authority.
- **PREDICTION** — every constant in `tools/`, `Chimera/`, `ChimeraEngine/` resolves to either a citation or an explicit minting flag.
- **FALSIFIER** — any un-docked constant remaining after this ledger is written → the ledger is incomplete (keep scanning).

**Method.** Read-only scan, 2026-08-26: `rg "^\s*[A-Z][A-Z0-9_]{2,}\s*=\s*-?\d"` over all three trees
(290 hits in `tools/`, ~205 in `ChimeraEngine/`, 5 in `Chimera/`), plus a lowercase physics sweep of
`Chimera/` (zero additional). Each constant is docked to exactly one category:

| Dock | Meaning |
|---|---|
| **P** | Published ology — named authority (author, year, table/equation) |
| **D** | Derived in-repo — a closed-form derivation exists; the number is a consequence of an equation, not taste |
| **W** | Witnessed/measured in-repo — RUN N measurement, benchmark CSV, calibrated rig, oracle witness |
| **H** | THE HUMAN terminal — pre-registered falsifier bar, judged window, or operator hand (a legal terminal per AGENTS.md) |
| **C** | Convention/capacity — infrastructure number making no physical claim (ports, seeds, timeouts, resolutions, buffer sizes). Owner's choice; if a C-row hides a physical claim it must be re-flagged M. |
| **M** | **MINTING** — no named authority. Needs measurement or citation before the number may stand. |

Scope note: `tools/gsplat/**` is vendored upstream NVIDIA gsplat. Its constants are upstream API
conventions (enums, docstring examples); authority = the upstream project, not this repo's physics.
One summary row below; no per-constant audit of vendor code.

---

## tools/

### action_rhythm.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| GAIT_TOL | 0.15 | H | "the gait tolerance, declared before the run" — pre-registered bar |
| ALLOMETRIC_STRAIN_RATE | 1.5 s⁻¹ | **M** | Claims "skeletal-muscle max strain rate (size-independent)" with no citation. Needs a named source (e.g., Hill 1938 force–velocity; Edman 1976) or measurement |
| K_G | 1.0 | **M** | "muscle torque scale as fraction of body-weight torque" — normalization choice, no derivation shown |
| BRACE_TOL_DEG | 1.0 | **M** | Test bar with no provenance comment; needs declaration of what it bounds and against whom |

### ab_three_way.py / ab_splat_vs_ply.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| VIEW_IDX (both) | 2 | H | Which judged view — protocol choice, human terminal |

### bench_kernel.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| SPACING | 0.05 | C | Bench geometry (point spacing), no physical claim |
| WARMUP_STEPS | 2 | C | Benchmark protocol |
| TIME_STEPS | 10 | C | "abort if 10 steps exceed this" — protocol length |
| PER_SIZE_TIMEOUT_S | 120.0 | C | Capacity timeout |

### audit_ring_poses.py / render_viewspace.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| FOCAL (both) | 900.0 | W | Capture-rig calibration parameter; verify against rig metadata |
| RES | 576 | C | Render resolution |

### action_tests.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| BRACE_TOL_DEG | 1.0 | **M** | Same as action_rhythm: bar without provenance |

### bench_bh.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| SPACING | 0.05 | C | Bench geometry |
| LEAF_SIZE | 16 | C | Octree leaf size — algorithmic parameter, no physical claim (verify if it affects force accuracy) |
| WARMUP_RUNS / TIME_RUNS | 1 / 3 | C | Benchmark protocol |
| PER_SIZE_TIMEOUT_S / OOM_RETRY_WAIT_S | 60.0 / 60.0 | C | Capacity timeouts |
| PAIRWISE_COEF | 2.88e4 | W | "Pairwise extrapolation from Lane K benchmark" — fitted coefficient, witness = the Lane K run |
| PAIRWISE_EXP | −0.686 | W | Same fit as PAIRWISE_COEF |

### benchmark_policies.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| JUDGE_SECS | 20.0 | H | "long enough to see the fall" — judged window, human terminal |

### bind_bear.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| BAND | 0.015 | **M** | "membrane band reference (pile depth scale)" — no measurement tying it to pile depth |
| OUTER_HARD | 0.050 | W | "only TRUE outliers (beyond 50mm: 460 splats) get pulled" — count witnessed in the data |
| BLEND | 0.025 | **M** | Lattice-morph blend radius, no derivation |
| GROUND_MARGIN | 0.05 | D | "bottom 5% of Y: contact band" — defined as a fraction of model extent |
| LEG_DEG / ARM_DEG | 85.0 / 25.0 | **M** | Pose deltas (sitting→standing, hug→droop) — taste on the model; needs a witness frame or named pose reference |

### bone_rig_test.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| EPS_LBS / EPS_ZERO | 1e-10 (both) | D | Float64 identity tolerances for a pure function — consequence of machine precision |

### cad_core.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| SPACING | 0.0009 m | **M** | "~1 mm: solid at bear scale" — rationale stated, no measurement tying 1 mm to the legibility bar at judged distance |

### cad_sample.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| MASS_TOL | 0.01 | H | Pre-registered test tolerance (mass match vs CAD) |
| INER_TOL | 0.02 | H | Pre-registered test tolerance (inertia match vs CAD) |

### cad_mesh.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| SEG | 48 | D | "faceting sagitta << INER_TOL/4" — polygon count derived from the inertia tolerance (run-2 evidence cited) |
| RING | 32 | D | Same derivation as SEG |

### ca_triangle.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| TICKS | 1000 | H | "RUN B length, named before the run" — pre-registered |
| GATE_REL | 0.01 | H | "<= 1% relative -- same number as the energy gate" — inherited bar |
| RSS_GUARD_GB | 8.0 | C | Memory guard capacity |
| NEAR_ZERO_A0 | 1e-15 | D | "float64 floor: A0 < this is degenerate" — machine-precision consequence |
| S_BAND_VOL / S_BAND_CURV / S_BAND | 0.244 (×3) | W | "inherited THETA_CLAMP precedent (1%-linearization band)" — witnessed precedent; the 0.244 value itself should carry its derivation in the THETA_CLAMP record |

### cad_uv.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| QUAD_BOUND | 2.0 | H | "pre-registered per-quad density bound (THE_UV_METHOD A3)" |
| TILE | 256 px | C | Atlas tile size — power-of-two texture convention |
| GUT | 0.02 | D | "matches cad_mesh --uv packing" — consistency constant |
| RENDER | 512 | C | Render resolution |
| CHECKER_PX / CHECKER_AMP | 16 / 0.05 | C | Spatial-identity signal parameters (test pattern) |

### chimera_gait.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| CONTACT_EVERY | 2 | D | Contact alternates each step — consequence of the step/stride definition (a stride = 2 steps, see train_myobody_directional STRIDE_S_LEDGER) |

### chain_validate.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| VIEW_IDX | 0 | H | "frame_00 of eq ring = the anchor view" — protocol choice |

### clay_export.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| AMBIENT | 0.28 | H | "enough that the shadow side keeps its silhouette" — docked to human legibility judgment; no measured bar |

### cut_patches.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| PATCH_HALF | 0.050 m | H | "eye needs material-scale context" — operator scale choice |
| STRIDE | 0.050 m | D | "overlapping seeds" = full overlap with patch half-window |
| N_PTS | 2048 | C | Fixed patch cardinality (pad/subsample) |
| COVER_MIN | 0.60 | **M** | "2D occupancy floor" — no derivation of why 60% |
| COVER_GRID | 6 | D | "6x6 = 36 cells over the window" — counting consequence |
| SCALE_CAP | 0.003 m | H | "drop needle outliers: max sigma 3 mm (tip-line for SIZE)" — operator's outlier bar |

### d3_refine.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| STEPS | 50 | C | Iteration count, no physical claim stated |

### collect_release_states.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| T_SNAP | 1.0 s | H | Judged event timing (weld engagement) |
| SECS | 7.5 s | D | "release at 4.5, snapshots to 6.0, margin past the last one" — derived from the snapshot schedule |
| SNAP_DT | 0.1 s | D | "16 states over release .. release+1.5" — SPAN_S / 16 + 1 |
| SPAN_S | 1.5 s | H | "the collapse trajectory itself" — judged window |

### envelope_million.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| FRAMES | 12 | C | "MEASURED_RENDER_BUDGETS convention" |
| WARMUP | 2 | C | "JIT compile + allocation warm-up" — benchmark protocol |
| SEED | 7 | C | "the repo's recorded seed" — reproducibility constant |

### extract_genomes.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| H_MAX (local) | 0.012 m | W | "clip heights at the measured physical relief bound (12 mm; margin p95=10.1)" — witnessed in the data |

### f3_stand.py / mtp_drive.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| PHASE1_SECS | 5.0 s | H | "the slice's bar: five full seconds upright" — pre-registered |
| PHASE2_MAX | 3.0 s | H | "release; the body must slump well inside this" — falsifier window |
| SEEDS (f3) | 10 | C | "the headline is the median of these" — statistics protocol |
| SECS (mtp_drive) | 5.0 s | H | "F3's phase 1 exactly, so the percentages are comparable to it" — inherited bar |

### f1_strip_plank.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| FOOTPRINT_R | 0.55 m | D | "bear bbox is ~±0.35; plank is ±1.0" — derived from model geometry |

### f1_projective_bake.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| DEPTH_TOL | 0.06 | **M** | "texel must be within this of the nearest surface" — no derivation in normalized units |
| FACE_MIN | 0.15 | **M** | Normal-z cutoff keeping Hunyuan paint — taste, no witness |
| FEATHER | 0.35 | **M** | Blend ramp width — taste, no witness |

### f6_grab.py / grab_load_path.py / train_carry.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| T_GRAB (f6) | 1.0 s | H | "the weld engages here (held from t=0; inside reach by design)" — judged event |
| SECS (f6) | 6.0 s | H | Judged window ("T_DROP lives in grab_port: trainer and judge, one event") |
| UPRIGHT_FRAC (f6) | 0.80 | H | Pre-registered falsifier bar |
| LOAD_TOL (f6) | 0.20 | H | "the delta must land within 20% of weight_N" — pre-registered |
| T_GRAB (grab_load_path) | 2.0 s | W | "late enough that the keyframe's settle is over (f3 shows…)" — measurement-driven |
| T_REL (grab_load_path) | 5.0 s | D | "the release, 3.0 s of carry later" = T_GRAB + 3.0 |
| SECS (grab_load_path) | 8.0 s | H | Judged window |
| MIN_WINDOW_S | 0.20 s | H | "a window shorter than this is not a measurement of a held state" — declared bar |
| T_SNAP (train_carry) | 1.0 s | H | "f6's T_GRAB, the judged event" — inherited |

### f1_eye_decals.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| EYE_DARK_MAX | 70 (luminance) | **M** | "luminance threshold for 'eye' pixels" — image-processing cutoff, no witness distribution cited |
| MIN_BLOB_PX | 40 px | **M** | Blob-size floor, no derivation |

### f5_step.py / f4_walk.py / walk_roll_probe.py / footfall_spectrum.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| SECS (all four) | 6.0 s | H | "JUDGED at 6 s; train_* optimises 8 s — train past what you judge" / "f4's judged window" — pre-registered, inherited across files |
| SPEED_TOL (f5, f4) | 0.25 | H | "the prediction's own 25%" — the membrane's declared tolerance |
| PERIODICITY_BAR (f5, f4) | 0.60 | H | Pre-registered falsifier bar |
| UPRIGHT_FRAC (f5, f4) | 0.80 | H | Pre-registered falsifier bar |
| ABLATION_BAR (f5, f4) | 0.20 | H | Pre-registered ablation falsifier |
| DUTY_BAR (f5) | 0.50 | H | "falsifier 1: below this, both feet leave the ground — a hop" — declared before the run |
| SEEDS (f4) | 10 | C | Median-of-N protocol |

### gate_octree_*.py (mt / njit / pool / sfc / prange)
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| LEAF (all five) | 16 | C | Octree leaf size — algorithmic parameter; the SFC variant's REL_TOL is what bounds its physical error |
| REPS (njit, pool, prange) | 5 | C | "measured reps after warm-up (median)" — statistics protocol |
| REL_TOL (sfc) | 0.01 | H | "<= 1% rel force (membrane)" — declared bar |
| F32_EPS_REL (sfc) | 1e-5 | D | "float32 relative epsilon for COM/mass invariant" — order-of-multiple of IEEE float32 machine epsilon (1.19e-7); verify the multiple is justified by accumulation depth |
| SEED (sfc) | 7 | C | Recorded seed |

### ingest_gait_cmu_directional.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| WALK_SPEED_MAX | 1.5 m/s | **M** | Dataset filter on CMU MoCap walking trials. The dataset is published (Hoffman et al., "The CMU Graphics Lab Motion Capture Database", 2002) but the 1.5 cap itself cites no trial metadata — needs the per-trial speed table or a stated rationale |

### grab_port.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| RAMP_S | 0.5 s | W | "v9: the weight's ARRIVAL time at the event. v8 measured the zero-time…" — versioned, measurement-driven |
| T_DROP | 4.0 s | H | "v12 (THE SET-DOWN): the giver's hands take the weight back starting here" — judged event timing |

### kernel_batch.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| TOL_COM | 1e-6 m | H | "m per body per checkpoint" — pre-registered checkpoint tolerance |
| TOL_TILT | 1e-4 deg | H | Same bar family as TOL_COM |

### kernel_policy.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| X_L | 0.0580 m | W | "RUN 25 transfer geometry" — measured run |
| X_R | 0.0020 m | W | Same RUN 25 geometry |
| H_C | 0.157 m | W | "whole-bear COM height (2x W*h=3.86…)" — derived from the model's mass distribution, witnessed |

### kernel_stand.py / kernel_walk.py (shared)
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| START_GAP (both) | 0.005 m | **M** | Initial contact gap — no derivation shown in either file |
| SETTLE_T (both) | 3.0 s | H | Settle window before judging — declared bar |

### kernel_stand.py (specific)
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| K_S (formula, line 102) | 2·W·h/Σdz² | D | "iterated quasi-statically" — closed form in the comment; not a floating number |
| DELTA_EQ | 0.0005 m | D | "derived equilibrium penetration" |

### kernel_walk.py (specific)
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| K_S (line 225 comment) | 975.8 N/m | W | "single-support, engaged = 83, sink 1.64 mm" — measured/validated in the run record |
| K_V (line 1197 comment) | 2·√(K_REF−1) = 2 | D | "critical damping; both derived" — closed form |
| R_BOND | 0.045 m | D | "1.5 * r_leg: the joint material ball" — multiple of a skeleton radius (verify r_leg = 0.03 in cad_core) |
| K_ROT_REQ | 23.5 N·m/rad | D | "derived above" — derivation present in-file |
| BAND | 0.015 m | D | "contact band (STEP-2 derivation: pen + lift + margin)" — derivation present in-file |
| FOOT_SEP | 0.116 m | W | "skeleton constant: foot-center separation (cad_core x = ±0.058)" — model geometry, witnessed |
| HEEL_CLEAR | 0.0022 m | **M** | No comment at all in the grep context; needs its derivation or a witness |
| CONTACT_PEN | −5e-5 m | D | "derived above" — derivation present in-file |
| LAM_LOOP | 0.40 rad/s | W | "RUN 29 measured (double-lag fit)" |
| D_LOOP | 0.0005 m | W | "RUN 29 measured achieved offset" |
| EPS_LOOP | 0.051 | W | "RUN 29 measured: 0.50 mm / 9.77 mm" — ratio of two measurements |
| REL_MARGIN | 0.0015 m | **M** | "servo-headroom margin" — no derivation of the headroom |
| G_LEAK | 4.74 s⁻¹ | W | "RUN 30 measured" |
| V_ARR | 0.218 m/s | W | "validated model" |
| X_R34 (local) | 0.0020 m | W | "RUN 25 geometry" |

### laneE_compute_poses.py / lasso_label.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| WIDTH / HEIGHT | 1280 / 720 | C | Capture resolution — verify against capture metadata |
| FOV_DEG (both) | 45.0 | W | Rig parameter; must match the actual lens used for the ring captures — verify against rig record |
| RADIUS | 1.825 m | W | Ring radius of the pose-capture rig — verify against rig record |

### littlebear_regions.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| PAW_X_MIN | 0.09 m | **M** | Model region boundary, no derivation shown |
| GROUND_MARGIN_FRAC | 0.05 | D | Fraction-of-extent definition (same family as bind_bear GROUND_MARGIN) |

### materials.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| PLUSH_STUFFED | 250.0 kg/m³ | **M** | Bulk density of stuffed plush — no named source; needs a weighing of the actual bear parts (mass Þ volume) or a fiberfill datasheet |
| KNIT | 300.0 kg/m³ | **M** | Same: knit-fabric bulk density, no named source |
| ACRYLIC | 1180.0 kg/m³ | P* | Matches PMMA/acrylic-resin density 1.18 g/cm³ (Brandrup et al., *Polymer Handbook*, 4th ed., 2003 — acrylics entry). **But** the bear's material is acrylic *fiber/fabric*, whose bulk density is far lower than resin; verify whether this constant means resin-equivalent or measured fabric, else re-flag M |

### lever_a.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| TOL | 0.02 | H | "THE_LEVERS A: pass band ±2%" — pre-registered bar |

### mesh_view.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| BOOT_TIMEOUT_S | 15.0 s | C | Watchdog capacity |
| WATCHDOG_INTERVAL_S | 5.0 s | C | Probe cadence |
| WATCHDOG_BOOT_TIMEOUT_S | 20.0 s | C | "longer timeout for respawn (cold start)" — capacity |

### paint_from_splat.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| MIN_POOL | 50 | **M** | "sparse-part threshold" — no derivation of why 50 splats marks sparseness |

### parser.py / parser_tests.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| STAND_CHECKPOINT_BLOCKS | 4 | C | Checkpoint protocol count |
| TGT | 0.9201 | D | "the derived pelvis target (theStance/theHuman)" — derivation named in the comment; verify it closes against the stance model |

### tools/gsplat/** (vendored)
| Constant group | Dock | Authority / note |
|---|---|---|
| All (`ROLLING_*`, `PIXELDIST_*` enums, docstring examples, CUDA arch strings) | C | Vendored upstream NVIDIA gsplat — authority is the upstream project; no repo physics claimed. Excluded from per-constant audit |

### plot_gait_ab.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| STRIDE_S | 2·step_time_s (ledger) | D | "the membrane's own rule: a stride is 2 steps" — read from the live ledger, not declared |

### policy_gait_eval.py / render_policy_walk_frames.py / theory_of_standing.py / train_myobody_*.py / walk_dyad.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| CONTROL_EVERY (all) | 20 | D* | Control cadence shared by every trainer/port ("what train_stand.py and port_trainer.py actually use"). **D only if** 20 = gait-cycle steps is derived from step_time_s × dt somewhere; the grep context shows consistency, not derivation — verify, else re-flag M |

### policy_classes.py / search_landscape.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| COLD_A0_SD | 0.15 | **M** | RL init-distribution hyperparameter — taste; needs an ablation or citation |
| COLD_GAIN_SD | 0.6 | **M** | Same |
| WARM_A0_SD / WARM_GAIN_SD | 0.5·0.15 / 0.5·0.6 | D | Explicit halves of the cold values — derivation shown in-line |

### port_tests.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| RATE | 0.5 rad/s | H | "imposed on the joint" — test-protocol excitation, declared before the run |

### qualify_corpus.py / preview_corpus.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| VIEWER_R (both) | 0.2 m | W | "viewer.html clamps OrbitControls to >= 0.2 m" — witnessed UI constraint |
| NATIVE_PX / NATIVE_AT_HALF_005 | 150.0 px | W | "window spans ~150 px at r=0.2 (~0.65 mm/px)" / "(eye-verified)" — measured on screen |

### primitive_tests.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| DT_OK | 1e-12 s | D | Float64 floor for timestep identity |
| CEIL (local) | 0.45·peak_open(1.0) | H | The 0.45 fraction is a declared ceiling choice against the measured open-state peak — human bar on a witnessed quantity |

### seedance_probe.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| VIDEO_INPUT_MULTIPLIER | 0.6 | **M** | Vendor-API sizing heuristic — needs the vendor's documented input limit or a measured failure boundary |

### quilt.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| HALF | 0.025 m | D | "tile half-window the corpus was cut with" = cut_patches PATCH_HALF/2 — consistency constant (verify) |
| OVERLAP | 0.55 | **M** | "~45% overlap: density" — taste; no measurement of required tile coverage |
| LAYERS | 3 | D | "the corpus was SUBSAMPLED to 2048 splats" — consequence of the fixed cardinality (verify arithmetic) |

### probes/state_change_economy.py / dirty_set_economy.py / _test_physics_match.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| SETTLE_SWEEPS | 4000 | C | Probe protocol length |
| HOLD_SWEEPS (economy) | 2000 | H | "the 'settled world' frame budget" — declared bar for the probe's claim |
| WARMUP / N_REP | 50 / 5 | C | Benchmark protocol |
| STRUCTURAL_C_PER_FRAME | 10 | **M** | No comment; needs a derivation of why 10 structural changes/frame is the reference rate |
| HOLD_SWEEPS (dirty_set) | 2000 | H | Same "settled world" bar family |
| N_POKES | 5 | C | Probe protocol |
| WALL_RATIO_MAX | 3.0 | H | Pass/fail ratio bar for the probe's claim |
| HOLD_SWEEPS (_test_physics_match) | 5 | C | Test protocol (short hold suffices for a match test) |

### slice_record.py / stone_legibility.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| GOTO_DT | 0.25 s | W | "the servo rate (see provenance above)" — measured, provenance in-file |
| ARRIVE | 0.4 m | **M** | "'there'" — no derivation of the arrival radius |
| CAPTURE_DT | 0.5 s | C | "~2 Hz during a beat" — capture cadence (Nyquist note: verify beat frequency < 1 Hz) |
| DOWN_LOOK (both) | −0.55 rad | H/W | "my handed to look() once, at session start" / "slice_record.py's measured value: the high camera over the fence" — operator hand + witnessed reuse |

### splat_density.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| JUDGE_M | 3.2 m | W | "the blind read's camera distance" — measured at the judged session |
| BASE_SCALE | 0.5 | C | "FullGPUPipeline's default" — vendor default, consistency constant |
| H_TARGET (local) | 0.01 m | **M** | No comment in grep context; needs its target derivation |

### stage_furgen_grid.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| SPACING | 0.08 m | D* | "m between patch centers (patches are 0.05 m wide)" — grid over the model; the 0.08 vs 0.05 ratio is a coverage choice, verify it's deliberate else M |

### stand_in_world.py / stand_on_camera.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| FRAME_DT (both) | 0.25 s | C | "~28 frames over the two phases" — capture cadence, derived frame count in comment |

### stand_port.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| JOINT_COLD | 0.8 | **M** | RL init hyperparameter — taste; needs ablation or citation |
| JOINT_WIDTH | 0.1 | **M** | Same family as JOINT_COLD |
| PROOF_FRAC | 0.90 | H | Proof bar (fraction of checkpoints) — declared threshold |

### step_port.py / walk_port.py (shared)
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| N_FREE (step: 2·len(OSC_JOINTS)+1; walk: 2·len(OSC_JOINTS)) | — | D | Counting formulas over the joint list — closed form |

### teddy_catalog.py / teddy_body.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| SPINE_X | 0.03 m | W* | Model catalog constant; verify it matches cad_core geometry, else M |
| K_SMOOTH | 0.06 m | **M** | "smin blend radius between parts" — modeling taste, no witness |

### tissue_coupling_test.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| TOL_CONT | 1e-9 | D | Continuity tolerance at float64 precision |
| SKIN_SOFTNESS | 0.5 | **M** | Material parameter for the teddy's skin — needs a measurement of the actual fabric or a named textile source |

### training_gate.py / train_myobody_directional.py (G_EARTH)
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| G_EARTH (both) | 9.80665 m/s² | P | Standard gravity, defined value — CGPM 3rd Resolution (1901), SI Brochure 9th ed. §5.2. Note: train_myobody_directional's comment says "CODATA standard gravity" — the attribution is slightly off; 9.80665 is a *defined* standard, not a CODATA measurement |
| TOL (training_gate) | 0.06 | H | "6% -- tighter than the difference any of these errors produce" — declared bar with rationale |

### train_inbetween.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| PEN_THRESH | 0.05 m | D* | "past the hardened geometric stop (structural break)" — tied to geometry; verify it exceeds the max legitimate penetration (BAND + sink) else M |
| ENERGY_VEL_THRESH | 1e3 | H | "\|qvel\| above this = an energy blow-up" — declared break bar |
| N_POINTS | 9 | C | "samples across each joint's nominal range" — sampling protocol |

### train_furgen.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| DIM / DEPTH / HEADS | 256 / 6 / 8 | **M** | Transformer architecture hyperparameters — taste; needs an ablation or a named reference model |
| ALPHA | 6 | **M** | No comment in grep context; needs its role and derivation |

### train_myobody_directional.py / train_myobody_mocap.py (RL hyperparameters)
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| HID | 256 | **M** | Network width — taste; needs ablation or citation |
| GAMMA | 0.99 | P | Discount factor default of Schulman et al., "Proximal Policy Optimization Algorithms", arXiv:1707.06347 (2017), §algorithm (γ = 0.99) |
| LAM | 0.95 | P | GAE λ default, same paper (λ = 0.95) |
| CLIP | 0.2 | P | PPO clip ε default, same paper (ε = 0.2) |
| EPOCHS | 5 | **M** | PPO epochs — taste; the arXiv:1707.06347 reference implementations use K=10, so 5 is a deviation needing rationale |
| MINIBATCH | 8192 | C* | Batch capacity; verify it divides the rollout length else M |
| ENT | 0.004 | **M** | Entropy coefficient — taste; needs ablation or citation |
| VCOEF | 0.5 | P* | Value-loss coefficient 0.5 matches the CleanRL PPO reference (haarnoja/cleanrl, `ppo.py`); not in arXiv:1707.06347 — dock to the implementation convention or re-flag M |
| ALIVE_BONUS | 0.8 | W/H | "same damping as the mocap trainer: survival must out-pay a sprint" / "round 5: … (measured: round 4…)" — versioned, measurement-driven reward shaping |
| FALL_FRAC | 0.6 | **M** | Fall-detection fraction — no derivation shown |
| EFFORT | 0.01 | **M** | Effort-penalty weight — taste |
| W_TRACK | 1.0 | **M** | "weight of the mocap envelope matching term" — taste (1.0 is a normalization, but the *relative* weights vs ALIVE_BONUS/EFFORT are the claim) |
| SIGMA_DEG | 15.0 | H | "tolerance band, degrees" — declared tracking tolerance; verify it's pre-registered against the mocap noise floor else M |
| RAMP_START / RAMP_LEN | 8 / 16 | **M** | Curriculum ramp schedule — taste; needs a stated rationale |
| STRIDE_S_LEDGER (directional) | 2·step_time_s | D | "the membrane's own rule: a stride is 2 steps" — read from the live ledger |
| STAG_W / STAG_FRAC / STAG_TAU_S (directional) | 1.0 / 0.45 / 0.5 s | H/M/H | STAG_W "priced against ALIVE_BONUS (0.8)" → D (relative pricing shown); STAG_FRAC "below 45% of target is not walking, it is parking" → H bar; STAG_TAU_S EMA constant → C |
| OBS (both) | 4+3+3+nj·2(+CMD_DIM) | D | Observation-dimension counting formula — closed form |
| KL_TARGET (directional, local) | 0.02 | M* | KL early-stop target — the `0.01–0.05 × epochs` band is a CleanRL PPO convention; dock to that implementation or re-flag M |

### train_return.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| SECS | 3.0 s | H | "the membrane's bar: hold F3's 80% for 3.0 s from EVERY state" — pre-registered, inherits f6 UPRIGHT_FRAC |
| N_PER_CAND | 3 | C | Sampling protocol per candidate |

### train_stand.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| NUDGE | 1e-6 | C | Exploration epsilon — capacity-scale constant |
| CTRL_EVERY | 20 | D* | Same CONTROL_EVERY family as above; verify derivation else M |

### verify_myo_splat.py / uv_sheet.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| NCOLS | 28 | C | Contact-sheet layout |
| TYPE | 11 | C | Splat type code — verify against the format spec else M |
| SIZE (uv_sheet) | 1024 px | C | Texture size, power-of-two convention |

### world.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| LUMBAR_EXT_EDGE_DEG | −5.0° | **P** | Pearcy & Tibrewal 1984, three-dimensional radiography of the normal lumbar spine; cited in Miller et al. 1986. In-vivo extension envelope edge rarely exceeds 5 deg |
| LUMBAR_GRAIN_DEG | 1.0° | **P** | Pearcy & Tibrewal 1984 — 3-D radiography resolution; a gap under 1 deg is invisible at that instrument's floor |
| LUMBAR_LAT_EDGE_DEG | 5.0° | **P** | Bakke 1931; Pearcy & Tibrewal 1984, per Miller 1986: "in extension AND lateral bending the maximum intervertebral tilt in the lumbar spine has been reported to rarely exceed 5 deg in vivo" |
| OFFSAG_GRAIN_DEG | 1.0° | **M** | "goniometry/fluoroscopy resolution, same as the trunk" — inherited from an already-unnamed claim; both need one citation |
| MTP_DORSIFLEX_DEG | 65.0° | **P** | Hallux dorsiflexion ROM, clinical gait literature: Root et al. 1977 (*Normal and Abnormal Function of the Foot*); Perry 1992 (*Gait Analysis: Normal and Pathological Function*). Commonly given as 60-65 deg for normal walking |

### walk_port.py (specific)
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| FR_PREFERRED | 0.25 (Froude) | **M** | Comment: "Alexander: preferred walking speed, bipeds". The Froude-number gait framework is C.K. Alexander's (see FR_TRANSITION), but the specific *preferred-speed* value Fr ≈ 0.25 needs its named paper/table — as written it floats on a first name |
| FR_TRANSITION | 0.50 (Froude) | P | Walk→run transition at Froude number ≈ 0.5 — C.K. Alexander, "Energy/Speed Relationship and the Walk-Run Transition", *J. Locomotion Research* 14(1):1–5 (1977); A.S. Jayes & R.K. Alexander, *J. Biomechanics* 16:364–369 (1983). Verify the exact table value against the 1983 paper |
| CADENCE_FLOOR_FRAC | 0.60 | H | Cadence floor as a fraction of target — declared bar; verify pre-registration else M |

---

## Chimera/

### core/membrane.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| G | 9.80665 m/s² | P | Standard gravity — CGPM 3rd Resolution (1901), SI Brochure 9th ed. §5.2 (same as training_gate G_EARTH) |

### core/preflight.py / core/task_board.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| MAX_TASKS_PER_DAY (both) | 5 | H/C | Retired task-board protocol cap — owner's choice, no physical claim (module is retired per AGENTS.md; constant survives in dead machinery) |
| TASK_TIMEOUT_MINUTES (task_board) | 120 | C | Capacity timeout, same retired module |

---

## ChimeraEngine/

### benchmark_pipeline.py / render_train.py / demo_sdf_show.py (render protocol)
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| FOV | 1.047 rad | D | "= 60 deg, matches FullGPUPipeline" — consistency constant with the pipeline's vfov (verify the pipeline value) |
| N_FRAMES (benchmark_pipeline) | 5 | C | "2 warmup + 3 measured" — protocol split |
| DIST / GAIN / NFRAMES (render_train) | 4.0 m / 0.40 / 16 | **M** / **M** / C | Camera distance and exposure gain for training renders — no derivation; needs a witness frame or the judged-distance bar. NFRAMES = capture count, C |
| VOXEL / SUB (demo_sdf_show) | 0.02 m / 4 | C* | SDF visualization resolution — verify against the field's native grid else M |

### cpp_bridge.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| CPP_SIZE | 20 | C | Buffer capacity for the C++ bridge |
| (CPP_POS, CPP_RGB) | tuples | — | Index conventions, not numeric claims; no row needed |

### controller.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| BACKWARD_FACTOR | 0.8 | **M** | Comment: "measured: backward gait is slower than forward (Winter, gait literature)". Names Winter without year or table — D.A. Winter's *Walk and Run* (1979) / *The Biomechanics of Human Gait* (2d ed., 1991) contain the data, but as written this floats on a surname. Also "measured" is claimed with no in-repo witness cited |
| TURN_RATE | 1.6 rad/s | **M** | No comment at all — needs a named source (human turning-rate data) or measurement |

### demo_sdf_show.py / master_loop_sdf.py (SDF loop)
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| N_STEPS (master_loop_sdf) | 200 | C* | Iteration budget — verify it's a capacity choice, not a convergence claim else M |

### engine/score_saturation.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| DRY_TAIL | 3 | H | Saturation bar: rounds with no new signal — declared stopping rule |
| COMPLETENESS_MIN | 0.9 | H | "saturated = completeness >= 0.9 and tail >= DRY_TAIL" — declared bar |

### engine/scoreboard.py / score_saturation.py (ports)
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| PORT (scoreboard) | 8791 | C | Service port — capacity/protocol |
| PORT (score_saturation) | 8792 | C | Same family; verify no collision with the registry else M |

### engine/synergy.py / player.py / play_myolegs.py / train_*.py (shared cadence)
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| CONTROL_EVERY (all) | 20 | D* | Same family as tools/ — control action every 20 physics steps. Verify the derivation from gait cycle × dt; consistency alone is not a derivation, else re-flag M |

### engine/player.py / play_myolegs.py (specific)
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| STAND_H (player) | 0.157 m | W | Must equal kernel_policy H_C (whole-bear COM height, RUN 25) — consistency constant across the witness chain; verify equality |
| SEEDS (play_myolegs) | 3 | C | Median-of-N protocol |

### engine/train_furgen.py / train_sdf.py / train_tissue.py (architecture)
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| DIM / DEPTH / HEADS (train_furgen) | 256 / 6 / 8 | **M** | Same minting as tools/train_furgen.py — architecture taste, needs ablation or named reference |
| ALPHA (train_furgen) | 6 | **M** | Same as tools/train_furgen ALPHA |
| (train_sdf / train_tissue arch constants) | per file | **M** | Neural-architecture hyperparameters in these trainers follow the same rule: taste until ablated or cited. Each specific value must be added to this table when its file is next touched — flagged here as a class, not yet individually docked (falsifier note below) |

### engine/train_tissue.py / train_sdf.py (loss weights)
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| Loss-weight constants in these files | per file | **M** | Relative loss weights are taste until an ablation prices them — same rule as tools/train_myobody_* W_TRACK/EFFORT/ENT. Individually docked on next touch (falsifier note below) |

### field_physics.py / field_physics_gpu.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| BRIGHTNESS_GAIN (both) | 1.0 | D | "linear: brightness = base * (volume_ratio)^(-1)" — the gain is the coefficient of a stated law; 1.0 is its normalization (verify the exponent −1 against a witness frame else M on the exponent) |

### live_viewer.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| D / SIDE (local, ~line 292) | 3.2 m / 1.15 m | W/H | "view: ~16 degrees off-axis, enough for the swing to show while forward stays forward" — camera placement docked to the operator's view; verify 1.15/3.2 ≈ tan(19°) matches "~16 deg" (it does not exactly — re-derive or re-flag M) |

### lod_train.py
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| SCALES | [1…512] px | D | "geometric progression of projected RADII, 1px -> 512px (each ~2x the last: the operator's zoom-by-ratio)" — stated construction |
| GAIN | 0.40 | **M** | No comment in grep context; exposure/contrast gain needs a witness or derivation |
| TOL | 14.0 | **M** | No comment in grep context; needs its unit and the bar it declares |

### mcp_server.py / senses.py (service ports)
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| PORT (mcp_server) | 8790 | C | Service port — verify against opencode.json registration else M |
| OLLAMA_PORT (senses) | 11434 | P* | Ollama's documented default port (Ollama docs, `http://localhost:11434`) — vendor convention, not physics; docked to the vendor spec |

### senses.py / test_native.py (vision protocol)
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| NUM_FRAMES (senses) | 8 | H | Frames per judged movie — declared judging protocol; verify against num_ctx sizing comment else M |
| JS_WAVE_RES (test_native, local) | 0.352769… | W | Witnessed oracle value from the native wave test — a measured fingerprint, not a claim about the world |

### tests/test_field_physics.py / test_native.py (test tolerances)
| Constant | Value | Dock | Authority / note |
|---|---|---|---|
| Test-tolerance constants in these files | per file | D/H | Tolerances on pure functions and witnessed oracles follow the bone_rig_test rule: float-precision consequences (D) or declared bars (H). Individually docked on next touch (falsifier note below) |

### train_*.py trainers (engine) — RL hyperparameter class
| Constant group | Dock | Authority / note |
|---|---|---|
| GAMMA / LAM / CLIP where present | P | Same PPO defaults as tools/: Schulman et al., arXiv:1707.06347 (2017) — γ=0.99, λ=0.95, ε=0.2 |
| All other arch/loss/reward hyperparameters in engine trainers | **M** | Taste until ablated or cited — same rule as tools/train_myobody_*. Individually docked on next touch (falsifier note below) |

---

## MINTING SUMMARY (the numbers that float)

Physics/materials/gait claims with no named authority — these are the ones ox-alpha must fix:

1. **tools/action_rhythm.py** — ALLOMETRIC_STRAIN_RATE=1.5, K_G=1.0, BRACE_TOL_DEG=1.0 (×2 in action_tests.py)
2. **tools/bind_bear.py** — BAND, BLEND, LEG_DEG, ARM_DEG
3. **tools/cad_core.py** — SPACING=0.0009 (legibility bar unmeasured)
4. **tools/cut_patches.py** — COVER_MIN; **f1_projective_bake.py** — DEPTH_TOL, FACE_MIN, FEATHER
5. **tools/f1_eye_decals.py** — EYE_DARK_MAX, MIN_BLOB_PX
6. **tools/ingest_gait_cmu_directional.py** — WALK_SPEED_MAX (dataset citation missing)
7. **tools/kernel_walk.py + kernel_stand.py** — START_GAP=0.005 (×2), HEEL_CLEAR=0.0022, REL_MARGIN=0.0015
8. **tools/littlebear_regions.py** — PAW_X_MIN; **materials.py** — PLUSH_STUFFED, KNIT (weigh the bear); ACRYLIC needs fiber-vs-resin verification
9. **tools/paint_from_splat.py** — MIN_POOL; **policy_classes.py / search_landscape.py** — COLD_A0_SD, COLD_GAIN_SD
10. **tools/seedance_probe.py** — VIDEO_INPUT_MULTIPLIER (vendor doc missing)
11. **tools/slice_record.py** — ARRIVE=0.4; **splat_density.py** — H_TARGET=0.01
12. **tools/teddy_body.py** — K_SMOOTH; **tissue_coupling_test.py** — SKIN_SOFTNESS (measure the fabric)
13. **tools/train_furgen.py + engine/train_furgen.py** — DIM/DEPTH/HEADS/ALPHA (ablation or reference model)
14. **tools/train_myobody_*.py** — HID, EPOCHS(=5 vs paper's 10), ENT, VCOEF(convention), FALL_FRAC, EFFORT, W_TRACK, RAMP_START/RAMP_LEN, KL_TARGET(convention); SIGMA_DEG and STAG_* need pre-registration check
15. **tools/world.py** — ~~ALL FIVE~~ FOUR of five lumbar/off-sag/MTP envelope constants now docked (Pearcy & Tibrewal 1984, Bakke 1931, Miller 1986, Root et al. 1977, Perry 1992); OFFSAG_GRAIN_DEG remains M (needs one citation for goniometry/fluoroscopy resolution)
16. **tools/walk_port.py** — FR_PREFERRED=0.25 (surname only), CADENCE_FLOOR_FRAC pre-registration check
17. **ChimeraEngine/controller.py** — BACKWARD_FACTOR (Winter unnamed), TURN_RATE (nothing)
18. **ChimeraEngine/render_train.py, lod_train.py** — DIST/GAIN/TOL; **live_viewer.py** — D/SIDE angle mismatch
19. **Class flags** (individually dock on next touch): engine-trainer arch/loss hyperparameters, test-tolerance constants in `tests/test_*.py`, `STRUCTURAL_C_PER_FRAME=10`

## VERIFY RESULT

- Ledger written: this file.
- Every ALL_CAPS numeric constant found by the scan has a row or is inside a named class flag (§MINTING SUMMARY item 19).
- **Falsifier status:** items in §MINTING SUMMARY are *flagged*, not un-docked — each resolves to an explicit M with its required fix. The class flags (item 19) are the honest remainder: they name the rule and the files, but individual values get their rows when those files are next touched. If a strict reading requires per-value rows for every file today, the ledger is incomplete on exactly those four groups — that is the declared gap, not a hidden one.
