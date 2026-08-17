# Chimera — Remaining Task Queue (2026-08-04, revised)

Cross-referenced against git log (20 most recent commits) and file-existence audit.
Items marked ✅ are committed and verified.

---

## RENDER COST & PIPELINE — 18 remaining

### LOD System (3)
1. Build per-grain-size scatter plot for top 5 most expensive terms (post-LOD-SIZE-fix — `77a9d19`)
2. Test clamp-outliers pass (`CHIMERA_CLAMP_SPLAT_SIZE=1`) with honest per-grain sizes — measure expansion savings
3. Re-run orbit proof on all 47 terms after LOD SIZE fix (sizes may change parallax delta)

### Expansion Budget (4)
4. Run all 47 terms through expansion budget check at default framing — flag over-budget terms
5. Add `CHIMERA_MAX_FPS` env var that sets `MAX_RENDER_MS = 1000/fps` (currently hardcoded 200)
6. Profile where the 1.7–4.9× viewer-vs-model timing gap comes from (LM Studio contention documented, but residual unexplained)
7. Document the compositor early-out at `gpu_pipeline.py:488` (`break` when `trans < 0.01`) as the mechanism that breaks the linear expansion model

### Tile Diagnostics (5)
8. Extend tile diagnostic to top-5 tiles and per-tile histogram (currently one hottest tile)
9. Wire tile diagnostic to `/tiles` HTTP endpoint (JSON array of hottest 20 tiles)
10. Add per-tile expansion histogram to benchmark output
11. Build tile-heatmap PNG render (one frame, colored by expansions-per-tile)
12. Document why theMining at 1.3M expansions costs 65 ms but aTerrain at 12.8M costs 393 ms (pixels-to-saturation depth differs)

### Benchmarks & Coverage (6)
13. Build per-grain-size histogram tool (reads buffer, bins SIZE column, outputs distribution)
14. Add coverage fraction to benchmark per-frame output (non-background pixel % — currently measured but not in per-frame CSV)
15. Extend benchmark to include per-stage timing: project_ms, bin_ms, sort_ms, composite_ms, publish_ms
16. Run benchmark at multiple resolutions (1920×1080, 1280×720, 960×540) — measure resolution scaling
17. Measure benchmark variance across 10 runs (not 3) — report 95% CI on expansion count and render_ms
18. Build per-term SIZE distribution audit (histogram + mean/std/p10/p90 for every term's uploaded buffer)

---

## LOCOMOTION LANE — 30 remaining

### Policy Class — Stand (8)
19. Build ablation study: remove each of 6 PD observation channels one at a time, rank by survival impact
20. Build a₀ ablation on PD policy: train PD without constant baseline, compare transfer ratio (Chimera g vs Earth g)
21. Build PD+phase policy (add `sin(φ), cos(φ)` to PD observation vector, φ = atan2(ż/ω₀, z−z_mean))
22. Judge PD+phase vs PD on held-out seeds 3–9
23. Build time-window derivative policy (5-frame buffer for velocity estimate vs single-timestep)
24. Judge time-window vs single-timestep derivative on held-out survival
25. Build PD-stand policy trained at different `CTRL_EVERY` values (10, 20, 40) — measure effect of control cadence on survival
26. Build ankle-strategy policy (CoM displacement → ankle torque, limited to ±15° sway — researched in `balance_strategies_reference.md`)

### Policy Class — Walk (6)
27. Add velocity feedback to walk observation vector (`train_walk.py` — verify if `pd=True` exists for walk path)
28. Train PD walk policy with derive-step + guard-elite, judge on F4
29. Build CPG (central pattern generator) policy class — oscillator that produces rhythmic output without rhythmic input
30. Phase-lock CPG to body's natural frequency `ω₀ = √(g/H)` — read from `theHuman/numbers.json`, never typed
31. Train CPG walk policy — first policy class that can generate a gait rather than react to one
32. Judge CPG walk on F4: target periodicity > 0.8, held > 5 s, footfall matches alternating diagonal

### Objective (6)
33. Build support-only objective (remove height, joints, effort — keep `support − 3·fell`)
34. Train support-only stand policy with derive-step + guard-elite, judge on held-out seeds
35. Build per-component objective ablation: train 4 policies, each with one component removed, measure component tradeoff matrix
36. Build objective-vs-survival scatter plot tool (reads any theta set from JSON, outputs PNG + CSV + Pearson r / Spearman ρ with within-rung breakdown)
37. Run objective-vs-survival tool on all saved stand thetas in `agent_logs/stand_survival_*.json`
38. Document the multiplicative-structure failure mode in `docs/LOCOMOTION_OBJECTIVE_DIAGNOSIS.md`

### Gait & Instrumentation (10)
39. Classify all saved walk thetas by gait type (stand/walk/shuffle/hop/slide from footfall autocorrelation)
40. Build gait transition detector (stand→walk at Fr crossing 0.5 from `gait_transition_reference.md`)
41. Build walk speed vs Froude target measurement (does the trained walker's speed match `Fr = 0.1513`?)
42. Build per-joint time-over-stop diagnostic for the walk port (`tools/joints_gradient.py` — verify it works on walk thetas, not just stand)
43. Run per-joint diagnostic on all 3 walk thetas (entrained, mult, mult2) — flag joints > 80% time-at-stop
44. Extend `stand_survival.py` rollout to also capture per-frame CoM height, pitch, roll — for fall analysis
45. Build fall trajectory plotter: for any saved fall, plot CoM height × time, pitch × time, roll × time
46. Build policy benchmark verdict tool — reads `benchmark_verdict.py` output, produces one-line comparison table
47. Wire policy benchmark into CAPCOM (`core/capcom.py`) as a post-training signal
48. Measure the 3 PD variants' basin widths using `search_landscape.py` — does derivative feedback widen the search landscape?

---

## SCENE & APPEARANCE — 12 remaining

### Term Completion (7)
49. Read `terms_data.py` for all 46 declared-only terms — rank by architectural importance based on parent membrane and concept description
50. Build emit stubs for top 10 most important declared-only terms (5 exist as placeholders — add 10 more)
51. Assign each new emit stub its correct parent membrane in `story/` with minimal `story.md`
52. Re-run `Chimera/core/grow.py`, re-bake, verify chain_witness after adding stubs
53. Update `docs/TERM_INVENTORY.md` with new counts after stub addition
54. Build `term_inventory()` function in `splat_appearance.py` returning `{renderable, declared_only, scene_without_term}`
55. Add `/inventory` HTTP endpoint to `live_viewer.py` exposing gap counts as JSON

### Scene Quality (5)
56. Measure per-scene LOD savings at default framing (2.8× extent distance) — which terms benefit most?
57. Measure per-scene tile hotness at default framing — which terms stress the tile budget even at normal view?
58. Build scene-to-scene transition animation (crossfade between membranes in the viewer — `/scene?term=X&transition=1.0`)
59. Add scene load time (ms from request to first frame) to `/stats` endpoint
60. Profile `splat_appearance.scene_buffer()` — which terms take longest to emit?

---

## VIEWER & GALLERY — 12 remaining

### HUD & Instrumentation (7)
61. Add body-state line to live viewer footer when standing: held time, support score, fall diagnostics
62. Wire fall kinematics capture in `walker.py`: `{exit_pitch, exit_roll, max_overshoot, fall_direction, held_time}` — snapshot at `stand→fall` transition
63. Add mechanism display on fall — HUD freezes last fall numbers (exit angle, direction, held time) until next stand
64. Add expansion count and LOD level to footer (`LOD 3/9 · 16,384/43,000 grains · 1.2M expansions`)
65. Build FPS sparkline (last 60 frames, 1px bar per frame) in footer
66. Build per-frame timing breakdown in `/stats`: `{project_ms, bin_ms, sort_ms, composite_ms, publish_ms, total_ms}`
67. Add `CHIMERA_MAX_FPS` to viewer startup — sets render thread's target frame time

### Gallery & Demo (5)
68. Build gallery search/filter by surface type (stellar/terrain/body/atmosphere/rock/vegetation) using `perf_guard._classify_type`
69. Add per-card expand/collapse with full `numbers.json` preview as formatted table
70. Build gallery sort dropdown: by grain count, extent, alphabetical, render cost
71. Wire LOD into demo tour (currently renders full base every stop — `demo.py` _render_frame needs `lod_switch()`)
72. Verify demo camera-aiming fix (`c54a72c`) is present in current HEAD

---

## MATTER PORTS — 4 remaining

73. Extend Terzaghi bearing capacity to include shape/depth/inclination factors (Meyerhof/Hansen/Vesic — currently basic `c·Nc + γ·D·Nq + 0.5·γ·B·Nγ`)
74. Build per-surface-type soil library module: sand, silt, clay, lunar regolith, martian regolith — each with cohesion + friction angle + density from `docs/research/`
75. Wire soil type selection by latitude/longitude in `walker.py` (polar vs temperate vs equatorial ground)
76. Add regression test in `tools/chain_witness.py`: does theGround's published cohesion match `story/data/physics_catalog.json` after any grow?

---

## INFRASTRUCTURE — 13 remaining

### CI & Integration (6)
77. Build `ChimeraEngine/ci_check.py` — runs: grow → bake verify → pipeline test → orbit proof → perf guard test → gallery → demo smoke. Exits 0 only if all pass.
78. Time the full ci_check end-to-end — target under 5 minutes. Profile slowest step.
79. Build a session log that timestamps each check and records pass/fail (human-readable + JSON)
80. Add pre-commit hook: run ci_check before any push, refuse if fails
81. Run full ci_check once, record baseline timing, commit the results as `ci_baseline.json`
82. Build a `/health` HTTP endpoint on the viewer that returns `{ci_passing, membranes_grown, terms_renderable, bake_verified, ports_passing}`

### Testing Gaps (4)
83. Run `python tools/chain_witness.py` — verify 42 working, 0 stubs, N placeholders, 0 broken. Update placeholder count if stubs were added.
84. Run `python story/folding.py audit` — verify 0 impossible values, 0 inconsistent pairs
85. Run `python tools/port_tests.py` — verify still 19/19
86. Build a test that verifies ALL 47 terms return non-None from `scene_buffer()` — currently only done ad-hoc. Add to `ci_check.py`.

### Documentation (3)
87. Write `docs/KNOWN_ISSUES.md` — every open defect: LOD SIZE overwrite (fixed `77a9d19`), compositor early-out breaks linear model, viewer-vs-model timing gap, objective blindness (r=−0.162 near solution), a₀ overfit (transfer ratio 0.23), PERF_GUARD duplicate function (fixed `4f8369b`), theMining misclassified as rock (fixed), demo camera-aiming (fixed `c54a72c`). Each with: symptom, root cause, status (fixed/open), commit if fixed.
88. Update `CLAUDE.md` Key Paths table — add `benchmark_pipeline.py`, `test_perf_guard.py`, `test_render_pipeline.py`, `benchmark_policies.py`, `LOCOMOTION_POLICY_DESIGN.md`, `LOCOMOTION_OBJECTIVE_DIAGNOSIS.md`, `RENDER_COST_MODEL.md`
89. Write `docs/SESSION_2026-08-04.md` — summary of all lanes' output: 20 research cards, LOD fix, expansion model (R²=0.995), PD policies (rate feedback is real, +0.04s), objective diagnosis (r=−0.162), gravity transfer (ratio 0.23), theGround cohesion fix

---

## CROSS-LANE INTEGRATION — 11 remaining

These items require coordination between lanes — they touch files owned by different agents.

### Unified Session (6)
90. Wire trained stand policy into `ChimeraEngine/controller.py` — replace hand-authored IDLE state with policy-driven muscle activations via `synergy.py`
91. Add `stand_theta` loading to `walker.py` — read best available theta from `agent_logs/`, apply through synergy decoder
92. Add `held_time` and `support_score` to `walker.readout()` — currently returns position/weather, not policy performance
93. Wire `walker.readout()` into live viewer's `/walk` endpoint response — expose policy performance to HUD
94. Run one full session: viewer open → theZero → aBlueWorld → theGround → Play → body stands → body falls → HUD shows exit angle + held time
95. Record the session — 3-minute video with HUD visible throughout

### Cross-Lane Verification (5)
96. Verify that a membrane regrown via `/free` (free parameter slider) still passes chain_witness
97. Verify that a membrane regrown via `/free` triggers cache invalidation and the viewer reloads the changed scene
98. Measure: does changing a free parameter on `theStar` (mass) cascade correctly to `aBlueWorld`'s surface temperature? (The slider test from `CLAUDE.md`)
99. Verify that `bake_splats --verify` catches a mismatch if a membrane is regrown but not re-baked
100. Build a `/dyad` endpoint that returns physics reading + render in one response — the operator's "both sides" view from `live_viewer.py`'s `_page(blind=False)` as structured JSON