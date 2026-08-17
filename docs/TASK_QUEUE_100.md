# Chimera — 100-Task Queue (2026-08-04)

Generated from full project audit. Organized by lane, priority-ordered within each section.
Every item traces to a specific file, measurement, or gap found in today's sessions.

---

## RENDER COST & PIPELINE — 25 items

### LOD System (10)
1. Fix LOD SIZE overwrite in `lod.py:125` — base level preserves emitted sizes, mip levels only get uniform `β·2R/√N`
2. Re-run splat-size histogram on aYellowStar (should show bimodal core+corona after fix)
3. Re-run splat-size histogram on aRockyPlanet (should stop inflating sizes 3×)
4. Re-run full 35-row benchmark with honest per-grain sizes
5. Update `docs/RENDER_COST_MODEL.md` with post-fix correlation matrix
6. Test clamp-outliers pass (`CHIMERA_CLAMP_SPLAT_SIZE=1`) — should actually do something now
7. Measure expansions saved by clamp on theMining at 0.25× zoom
8. Verify LOD pop guard still holds (max ratio 4.00×) with per-grain sizes
9. Build per-grain-size scatter plot for top 5 most expensive terms
10. Document the SIZE-overwrite finding in `docs/KNOWN_ISSUES.md`

### Expansion Budget (10)
11. Set per-surface-class expansion budgets from benchmark data (measured median × 1.5)
12. Wire `MAX_RENDER_MS` as the one configurable wall (currently 200 ms = 5 fps)
13. Add expansion budget to `/stats` endpoint response
14. Build expansion-over-time graph per frame in live viewer HUD (sparkline)
15. Add expansion budget guard to demo.py per-frame output
16. Run all 47 terms through expansion budget check — flag any over budget at default framing
17. Derive MAX_RENDER_MS from target fps (currently hardcoded 200)
18. Add `CHIMERA_MAX_FPS` env var that sets `MAX_RENDER_MS = 1000/fps`
19. Profile where the 1.7–4.9× viewer-vs-model gap comes from
20. Document the compositor early-out (`trans < 0.01` at `gpu_pipeline.py:488`) as the mechanism that breaks the linear expansion model

### Tile Diagnostics (5)
21. Extend tile diagnostic to top-5 tiles and per-tile histogram
22. Wire tile diagnostic output to a `/tiles` HTTP endpoint (JSON array of hottest 20 tiles)
23. Add per-tile expansion histogram to benchmark output
24. Build tile-heatmap PNG render (one frame, colored by expansions-per-tile)
25. Document why theMining at 1.3M expansions costs 65 ms but aTerrain at 12.8M costs 393 ms (pixels-to-saturation depth)

---

## LOCOMOTION LANE — 25 items

### Policy Class (12)
26. Add velocity feedback to stand observation vector (add `ż` and `θ̇`)
27. Train PD stand policy with derive-step + guard-elite (24 candidates × 30 turns, 3 seeds)
28. Judge PD policy on held-out seeds 3–9 against P-only baseline
29. Add velocity feedback to walk observation vector
30. Train PD walk policy with derive-step + guard-elite
31. Judge PD walk policy on F4 instrument against P-only baseline
32. Build ablation study: remove each of 6 observation channels one at a time, rank by survival impact
33. Build a₀ ablation on PD policy: train without constant baseline, compare transfer ratio
34. Build PD+phase policy (add `sin(φ), cos(φ)` to observation vector)
35. Judge PD+phase vs PD on held-out survival
36. Build time-window derivative policy (5-frame buffer for velocity estimate)
37. Judge time-window vs single-timestep derivative on held-out survival

### Objective (7)
38. Build support-only objective (remove height, joints, effort)
39. Train support-only stand policy with derive-step + guard-elite
40. Judge support-only vs full objective on held-out survival
41. Build per-component objective ablation: train 4 policies, each with one component removed
42. Measure component tradeoff matrix for all 4 variants
43. Document the multiplicative-structure failure mode in `docs/LOCOMOTION_OBJECTIVE_DIAGNOSIS.md`
44. Build objective-vs-survival scatter plot tool (reads any theta set, outputs PNG + CSV)

### Walk Gait (6)
45. Classify all saved walk thetas by gait type (stand/walk/shuffle/hop/slide)
46. Build CPG (central pattern generator) policy class
47. Phase-lock CPG to body's natural frequency `ω₀ = √(g/H)`
48. Train CPG walk policy — first policy class that can generate a gait
49. Judge CPG walk on F4: target periodicity > 0.8, held > 5 s
50. Build gait transition detector (stand→walk, walk→run) from Froude number

---

## SCENE & APPEARANCE — 15 items

### Term Completion (8)
51. Read `terms_data.py` for all 46 declared-only terms — rank by architectural importance
52. Build emit stubs for the top 10 most important declared-only terms
53. Assign each new emit stub its correct parent membrane in `story/`
54. Re-run `Chimera/core/grow.py` after adding stubs
55. Re-bake all terms after grow (`bake_splats.py --verify`)
56. Update `docs/TERM_INVENTORY.md` with new counts
57. Build `term_inventory()` bridge in `splat_appearance.py`
58. Add `/inventory` HTTP endpoint exposing term gap counts

### Scene Quality (7)
59. Measure per-scene LOD savings at default framing
60. Measure per-scene tile hotness at default framing
61. Re-run orbit proof on all 47 terms after LOD SIZE fix
62. Verify the 6 planar-by-design membranes still read as planar after SIZE fix
63. Build scene-to-scene transition animation (crossfade between membranes)
64. Add scene load time to `/stats`
65. Profile `splat_appearance.scene_buffer()` — which terms take longest to emit?

---

## VIEWER & GALLERY — 12 items

### HUD & Instrumentation (7)
66. Add body-state line to live viewer footer when standing
67. Wire fall kinematics capture: `{exit_pitch, exit_roll, max_overshoot, fall_direction, held_time}`
68. Add mechanism display on fall — HUD holds last fall numbers until next stand
69. Add expansion count to footer alongside grain count
70. Build FPS sparkline (last 60 frames) in footer
71. Add LOD level indicator: `LOD 3/9 (16,384 / 43,000 grains)`
72. Build per-frame timing breakdown in `/stats`

### Gallery & Demo (5)
73. Build gallery search/filter by surface type
74. Add per-card expand/collapse with full numbers.json preview
75. Build gallery sort by grain count, extent, or alphabetical
76. Wire LOD into demo tour
77. Fix demo camera-aiming for off-axis angles

---

## MATTER PORTS — 9 items

78. Verify theGround's cohesion reads from the library (regression-guard existing)
79. Verify theHuman's footprint depth against independent port derivation (guard exists)
80. Add regression test: does theGround's published cohesion match `physics_catalog.json`?
81. Extend Terzaghi bearing capacity to include shape/depth/inclination factors
82. Verify `landing_ground_holds = False` on this world's regolith — document as game fact
83. Measure footprint depth at Earth g (20.9 mm) vs Chimera g (3.1 mm)
84. Build per-surface-type soil library: sand, silt, clay, regolith
85. Wire soil type selection by latitude/longitude
86. Verify chain_witness after any story/ changes

---

## INFRASTRUCTURE & INTEGRATION — 14 items

### Testing (7)
87. Run `ChimeraEngine/test_perf_guard.py` — 11 tests, all must pass
88. Run `ChimeraEngine/test_render_pipeline.py` — 47/47 against baseline
89. Run `python Chimera/core/grow.py` — must complete with 0 broken membranes
90. Run `python -m core.why --feature X --loop` on a representative membrane
91. Run `python story/folding.py audit` — must report 0 impossible values
92. Run `python tools/port_tests.py` — must report 19/19
93. Run `python tools/chain_witness.py` — must report 42 working, 0 broken

### Integration (4)
94. Run a full end-to-end session: grow → bake → verify → pipeline test → orbit proof → perf guard → gallery → demo smoke
95. Build `ChimeraEngine/ci_check.py` — runs full end-to-end, exits 0 only if all pass
96. Time the full end-to-end — target under 5 minutes
97. Build a session log that timestamps each check and records pass/fail

### Documentation (3)
98. Update `CLAUDE.md` Key Paths table with all new files from 2026-08-04 sessions
99. Write `docs/SESSION_2026-08-04.md` — summary of all lanes' output today
100. Write `docs/KNOWN_ISSUES.md` — every open finding from today (LOD SIZE overwrite, compositor early-out, viewer-vs-model timing gap, objective blindness, a₀ overfit, PERF_GUARD duplicate function bug)