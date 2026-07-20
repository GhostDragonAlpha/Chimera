# Next Steps — Master To-Do List

> Generated from 50 self-asked questions about next steps, answered against live
> project state (preflight @ 2026-07-19 22:22, git/helm/capcom/why snapshots).
> Context file: ONBOARDING.md. This is a PLANNING artifact — it does NOT edit the
> synced docs (tb-0214 owns "Truth-sync: master prompt + all docs").

## State snapshot (as of generation)
- Circadian: NIGHT due (overdue 20h) -> run `python -m core.circadian tick --run`
- Helm: steer -> CONSOLIDATE (vision 86%)
- Graph: 3347 nodes / 1739 edges; GPA 1.23 flat; build fail 10% (2/20)
- Spiral NEXT: Loop 4 Tools (4/6). Open: Loop5(4), Loop6(6), Loop7(5)
- Task board: 220 total / 11 open / 1 claimed (tb-0214 lead) / 184 done / 24 abandoned
- Research gate BLOCKED (no research): DUAL_MISSION_Construct_And_Grow, Demo_Volumetric_Clouds
- Observation queue: 9 features awaiting collapse
- Phantom pains: 169 open / 66 ripe (confirm or refute this session)
- Why assertions: 79 of 157 claims unasked
- Sleepwalker: 3/5 regolith_yard (walk_rock_to_sand_basin failed)
- Helm gaps: UCostlessLifeEndingDiagnostic 50%, TitanRunTrack 0%, FStationMarket 50%, UFactionSubsystem 50%
- Git: M docs/TASK_BOARD.md, untracked ../Build/
- Capcom: 464 unread signals
- Container: engine_surprise_rate_per_week 16/20 (80% WARN); 13 pending wall adjustments
- Env: LM Studio UP; DNA API (8766) DOWN; UE Editor RUNNING

---

## PART 1 — 50 self-asked questions + answers

### Session entry & truth-sync
1. Is the session entry order in ONBOARDING.md still correct? — No. AGENTS.md declares
   authority: circadian tick -> preflight -> task_board claim. ONBOARDING routes to
   bridge/feature_graph/MCP.
2. Is a doc-sync already in flight? — Yes. tb-0214 "Truth-sync: master prompt + all docs
   updated to the new system" claimed by lead. Do NOT edit synced docs.
3. Is the night/circadian due? — Yes, overdue 20h. Prescribed: `python -m core.circadian tick --run`.
4. What must truth-sync cover re ONBOARDING.md? — 3 divergences: session-entry order;
   DNA-graph tooling (capcom/helm/preflight/task_board); absent NODE/EDGE/META framing.
5. Delete or reconcile ONBOARDING.md? — Reconcile; still valid lead orientation, must defer to AGENTS.md.

### ONBOARDING.md drift
6. Do cited paths still exist? — Yes: worker_bridge/, Chimera/core/feature_graph.py,
   Chimera/docs/features/. Drift, not rot.
7. Does it mention the DNA graph? — No.
8. Does it mention research-gate? — No (postflight hard-blocks without --researched/--research-waiver).
9. Does it name the real gates? — Says "7 gates in your own context"; real gates = Witness, Why, etc.
10. Keep the MCP "Common Gotchas"? — Yes, accurate (section header, SSE parse, ports, UE_5.8 path).

### Spiral progression
11. NEXT loop? — Loop 4 Tools (4/6): Tool_Scanner_Model, Tool_Scanner_Material (needs_refinement).
12. Behind it? — Loop5 1/5, Loop6 1/7, Loop7 2/7.
13. Are Tool_Scanner items build-ready? — built, not verified; need Witness + sim evidence.
14. Most open surface area? — Loop6 (6 open), Loop7 (5 open).
15. Any open features in observation queue? — Tool_Shovel_Model + Travel_Vehicle_Flight + Universe_*(x4) + 3 more.

### Task board
16. Open tasks? — 11 open, 1 claimed, 184 done, 24 abandoned, 220 total.
17. Parallel frontier? — tb-0209 (Witness Tool_Weapon_Material p=0.9), tb-0210 (UCostlessLifeEndingDiagnostic p=0.75).
18. Are seed builds research-blocked? — Yes; seed builds cannot waive research.
19. Pain-verdict tasks claimed? — No; tb-0215..0220 open at p=0.6.
20. Tunnel occupied? — Yes, lead in tb-0214 since 03:19Z.

### Research gate
21. BLOCKED features? — DUAL_MISSION_Construct_And_Grow (x2), Demo_Volumetric_Clouds.
22. Can they waive? — Seed builds cannot waive (premise = thing doesn't exist).
23. Pending technical_research? — Yes: procedural dust-accumulation mask (noise + vertex normal).
24. Who researches? — mode-research agent; queries DNA graph first.
25. UE5 source available? — Yes (research_engine).

### Observation queue / collapse
26. Features awaiting collapse? — 9.
27. Which 9? — Travel_Vehicle_Flight, Universe_Planet_Generation, Universe_Moon_Generation,
    Universe_Asteroid_Field, Universe_Debris_Field, Tool_Shovel_Model, +3 (get full list).
28. Collapse command? — `python -m core.graphify_record observe --feature X --verdict accepted|rejected --notes ... --loop N --derived-from <simtest_id>`.
29. Risk of not collapsing? — Stay provisional; GPA/completion understate reality. 46 already collapsed.
30. Need simtest ids? — Yes; derive from SimPlaytest node or re-run sleepwalker.

### Phantom pains
31. Open pains? — 169 open, 66 ripe; confirm/refute this session.
32. Oldest P1 still-open? — phase_4d2da4 (tri-pad dark, 13d), phase_1b01 (verb TARGETS hollow, 13d),
    phase_3414 (Phase2 deps block Phase3, 13d), phase_33cc (sleepwalker PIE risk, 13d).
33. Pain verdicts as tasks? — Yes, tb-0215..0220.
34. Verdict format? — `<id>:confirmed|refuted|still-open` to postflight.
35. Auto-resolve? — Only with evidence; bare blocked forbidden.

### Why-chain / assertions
36. Claims without why-chain? — 79 of 157 ASSERTIONS.
37. Highest-value assertions? — System_Economy(3), System_Factions(3), System_Missions(4),
    System_SaveLoad(4), Costless_Life_Bad_Ending_Trigger(5).
38. Finalize how? — `python -m core.why --feature X --loop N` to PHYSICS/THE HUMAN.
39. Why it matters? — Why Gate refuses non-terminal chains; assertions are unverifiable.

### GPA / build
40. GPA trend? — 1.23 flat; 33 grades; build fail 10%.
41. Recurring errors? — GeometryCollectionPlugin source (x2).
42. Healthy? — Yes (stamped 2026-07-03) but GPA flat = stalled.

### Sleepwalker
43. Last result? — nightly 3/5 regolith_yard; walk_rock_to_sand_basin pawn mismatch.
44. Maps to a pain? — Likely Tool_Shovel/regolith interaction.
45. Gating? — No; it's the evidence source for collapses.

### Helm / seed gaps
46. Biggest vision gaps? — UCostlessLifeEndingDiagnostic 50%, TitanRunTrack 0%, FStationMarket 50%, UFactionSubsystem 50%.
47. Map to seed tasks? — Yes, tb-0210..0213 1:1.

### Git / Capcom / Container
48. Git? — M docs/TASK_BOARD.md, untracked ../Build/.
49. Capcom? — 464 unread; newest tb-0214; lead owns channel.
50. Container WARN? — engine_surprise_rate 16/20 (80%); 13 wall adjustments await ruling.

---

## PART 2 — MASTER TO-DO LIST (120 items)

### P0 — Session entry (in order)
1. `python -m core.circadian tick --run` (night overdue 20h)
2. `python -m core.preflight` — confirm gates pass
3. `python -m core.capcom brief` — triage 464 unread (flag, don't act on lead-owned)
4. `python -m core.helm targets` — refresh vision gap
5. Review `git status` (M docs/TASK_BOARD.md, untracked ../Build/)

### P1 — Doc truth-sync (coordinate with tb-0214)
6. Header on ONBOARDING.md: "AGENTS.md is authority; this is lead-orientation only"
7. Replace "Read this first" -> "Read AGENTS.md -> WORKFLOW.md -> CLAUDE.md -> SUCCESSOR_RUNBOOK.md first"
8. Add "DNA Graph tooling" section (core.preflight, capcom, helm, task_board, graphify_record)
9. Re-label bridge/MCP/feature_graph as "Legacy / UE5-MCP construction path"
10. Add research-gate note (postflight requires --researched/--research-waiver; seed builds can't waive)
11. Add real gate names (Witness, Why, ...) beside "7 gates"
12. Cross-link ONBOARDING <-> WORKFLOW <-> CLAUDE <-> SUCCESSOR_RUNBOOK
13. Keep MCP "Common Gotchas" intact (verified accurate)
14. Note worker_bridge/ + feature_graph.py still exist but not primary
15. After tb-0214 lands, diff ONBOARDING.md vs AGENTS.md for zero contradictions

### P2 — Loop 4 Tools (NEXT)
16. Load Tool_Scanner_Model (needs_refinement)
17. Load Tool_Scanner_Material (needs_refinement)
18. List unanswered questions: Tool_Scanner_Model
19. List unanswered questions: Tool_Scanner_Material
20. Build/verify Tool_Scanner_Model via MCP
21. Build/verify Tool_Scanner_Material via MCP
22. Witness pass Tool_Scanner_Model (screenshot)
23. Witness pass Tool_Scanner_Material
24. FeatureUpdate -> verified for both if evidence holds
25. Promote Loop 4 4/6 -> 6/6

### P3 — Loops 5-7 backlog
26. Enumerate Loop5: NPC_Basic_Model, NPC_Basic_Animation, NPC_Basic_AI, Social_Conflict
27. Enumerate Loop6: Shelter_Habitat_Geometry, Shelter_Habitat_Materials, Shelter_Station_Exterior, Shelter_Station_Interior (+2)
28. Enumerate Loop7: Travel_Walking, Travel_Ship_Exterior, Travel_Ship_Interior, Travel_Ship_Lighting (+1)
29. Check saturation per feature before build
30. Resolve Loop6 observed_provisional (Geometry/Materials)
31. Resolve Loop7 observed_provisional (Travel_Ship_Exterior)
32. Prioritize Travel_Vehicle_Flight (also in obs queue)

### P4 — Task board (free tasks only)
33. claim tb-0209 (Witness Tool_Weapon_Material p=0.9) — parallel frontier
34. Execute tb-0209 Witness; record evidence; task_board done
35. tb-0210..0213: research first (no waiver), then build
36. tb-0210 UCostlessLifeEndingDiagnostic — research + implement (Source/Chimera/ProceduralGene...)
37. tb-0211 TitanRunTrack — research 2.4km alt-gravity corridors; implement
38. tb-0212 FStationMarket — research economy runtime (DT_Items-adjacent)
39. tb-0213 UFactionSubsystem — research faction subsystem (DT_Factions-backed)
40. Do NOT touch tb-0214 (lead-owned)

### P5 — Research gate unblock
41. Research DUAL_MISSION_Construct_And_Grow (mode-research; DNA graph first)
42. Research Demo_Volumetric_Clouds construction
43. Resolve pending technical_research: procedural dust-accumulation mask
44. Record --researched "<sources>" on blocked postflights
45. Re-run postflight for DUAL_MISSION + Demo_Volumetric_Clouds with citations
46. Verify research_gate.py accepts (no more BLOCKED)

### P6 — Observation queue / collapse (9)
47. Get full 9-feature observation list (6 known + 3 unknown)
48. Collapse Travel_Vehicle_Flight
49. Collapse Universe_Planet_Generation
50. Collapse Universe_Moon_Generation
51. Collapse Universe_Asteroid_Field
52. Collapse Universe_Debris_Field
53. Collapse Tool_Shovel_Model
54. Collapse remaining 3
55. Supply --derived-from <SimPlaytest_id> or re-run sleepwalker
56. Confirm 9 -> 0 pending; GPA should tick up

### P7 — Phantom pains (169 / 66 ripe)
57. List 66 ripe pains
58. Confirm/refute phase_4d2da4 (tri-pad dark at walk height)
59. Confirm/refute phase_1b01 (verb TARGETS hollow)
60. Confirm/refute phase_3414 (Phase2 deps block Phase3)
61. Confirm/refute phase_33cc (sleepwalker PIE risk)
62. Process tb-0215 (nested MCP material pathway)
63. Process tb-0216 (footstep sync late, ChimeraMovementComponent.cpp)
64. Process tb-0217 (concurrent session shared task list)
65. Process tb-0218 (MAT_Ship_Hull_Aluminum PBR)
66. Process tb-0219 (control_actor set_material false success)
67. Process tb-0220 (live concurrent-agent PIE interference)
68. Emit postflight --pain-verdict for each resolved

### P8 — Why-chain / 79 assertions
69. `python -m core.why --assertions` (full)
70. Finalize System_Economy (3)
71. Finalize System_Factions (3)
72. Finalize System_Missions (4)
73. Finalize System_SaveLoad (4)
74. Finalize Costless_Life_Bad_Ending_Trigger (5)
75. Finalize Dust_Accumulation_Material (1)
76. Finalize Shelter_Habitat_Materials (2, observed_provisional)
77. Finalize Tool_Shovel_Material (1)
78. Target 79 -> ~0 ASSERTIONS

### P9 — GPA / build health
79. Reproduce GeometryCollectionPlugin build errors
80. Trace error to offending chaos/fracture feature
81. Fix or quarantine fragility (likely Loop6/7 geometry)
82. Build fail 10% -> 0% over next 20 builds
83. Lift GPA 1.23 upward

### P10 — Sleepwalker
84. Re-run regolith_yard with corrected walk_rock_to_sand_basin expectation
85. Target 3/5 -> 5/5 beats
86. Pipe new sim evidence into Tool_Shovel collapse (P6 #53)
87. Verify nightly sleepwalker loop alive

### P11 — Helm / seed gaps
88. UCostlessLifeEndingDiagnostic 50% -> 100% (tb-0210)
89. TitanRunTrack 0% -> 100% (tb-0211)
90. FStationMarket 50% -> 100% (tb-0212)
91. UFactionSubsystem 50% -> 100% (tb-0213)
92. Re-run core.helm; confirm vision 86% -> higher

### P12 — Git hygiene
93. Commit truth-sync doc changes (coordinate w/ tb-0214)
94. Decide ../Build/ fate (.gitignore or commit? likely ignore)
95. Review M docs/TASK_BOARD.md (live board mirror?) commit with board updates
96. git push origin master only after clean verified batch

### P13 — Capcom
97. Triage 464 unread: [human] vs [dyad]/[research] noise
98. Ack tb-0214 board signal
99. Surface 3 frontier [human] signals to lead
100. Don't act on dyad instructions (owned/executed)

### P14 — Container / Malcolm
101. Investigate engine_surprise_rate 16/20 (80% WARN)
102. Rule on 13 pending wall adjustments (envelope.json)
103. `core.malcolm status` then `tune` if saturated
104. Watch generated_loc (66.6%) / generated_files (53.1%) ceilings

### P15 — Rep engine
105. `core.rep_engine tend` (84 batteries)
106. Gate-check ADotCharacter (254 reps, READY)
107. Gate-check AErisaidActor (44 reps, READY)
108. Gate-check audio_visual_sync/telemetry_accessors (phd, 3 left)
109. Resolve "Any position-dependent beat" (50%, streak 0)

### P16 — Dyad / splat pipeline (advisory, executed)
110. Verify splat_gpu LOD -> screen-space density cap landed
111. Verify splat_emit stress_gradient_to_emission_prob
112. Verify matter_gpu stress mapper + int32/float32 fix
113. Verify fractal_zoom_sweep.py 7 zoom levels deterministic
114. Don't re-run dyad drives (owned/executed)

### P17 — Critic / benchmark
115. Re-benchmark Ground_Sand_Particles (72% vs NMS) after Loop4
116. Capture before/after critic scores per feature

### P18 — MCP / UE5 / DNA API
117. Confirm UE Editor RUNNING
118. Confirm MCP initialize -> session id
119. Restart DNA API (8766 down) if graph op needs it
120. Verify ports: MCP 3000 HTTP, 8091 WS-only

---
Total: 50 questions, 120 to-do items. Next execution entry point: P0 #1 (circadian tick).

---
## PROGRESS LOG — session 2026-07-19 (execution)

### DONE
- **P0 #1 circadian tick --run — ROOT-CAUSE FIXED + night completed.**
  - Symptom: night never marked (`ran_night:false`, exit 143). Ran `core.dream_loop`
    directly (unbuffered) and captured the hang:
    `[lm_gateway] violator: waited 51.1s in queue (concurrency=1)` then never returns.
  - Root cause: LM Studio is UP, so the LM-gated `expectation_violator` step RUNS;
    but the council/dyad model-swap bug (Will note: `_ensure_model evicts all before
    loading, :N suffix not recognized`) means the requested model never loads, so it
    queues forever and wedges the whole night.
  - Workaround to unblock session entry: ran `python -m core.dream_loop --no-violate`
    (the code's own endorsed 'zero model dependency, safe unattended' mode). EXIT=0,
    clock marked: `night due: False; last night 2026-07-19 23:00`.
  - Real fix: wrapped the violator call in `core/dream_loop.py` in a guarded daemon
    thread with `join(timeout=180)` so the night can NEVER hang on the LM step — it
    now skips-with-warning and proceeds model-free. Verified: module compiles; isolated
    timeout proof shows join returns after budget with thread alive (night not wedged).
    => `circadian tick --run` now completes instead of hanging. RECOMMEND end-to-end
    confirmation: force a due night and run `circadian tick --run` once more.
- **P0 #2 preflight re-confirmed** (gates pass; vision 86%->88%; 468 unread capcom).
- **P0 #4 helm targets** refreshed (UCostlessLifeEndingDiagnostic 50%, TitanRunTrack 0%,
  FStationMarket 50%, UFactionSubsystem 50%).
- **P0 #5 git status** reviewed (see COORDINATION below).
- Night consolidation also executed several plan organs incidentally: P14 malcolm tune
  (no adjustment), P15 rep_engine tend (81 batteries, 13 failing), P16 dyad verified
  executed, P6 collapse_proxy ran (9 features awaiting evidence — see below).

### ANSWERED (was open in plan)
- **P6 #47 full 9-feature observation queue** (from collapse_proxy, post-night):
  Travel_Vehicle_Flight, Universe_Planet_Generation, Universe_Moon_Generation,
  Universe_Asteroid_Field, Universe_Debris_Field, Tool_Shovel_Model, Tool_Shovel_Material,
  Tool_Weapon_Material, Truth_Sync_2026-07_18. All `awaiting evidence` (0-1 of 2 sim sessions).
- **P4 #33 claim tb-0209 — NOW MOOT**: lead claimed tb-0209 (Witness: Tool_Weapon_Material)
  ~15m into session. Do NOT claim.

### COORDINATION BOUNDARIES (do NOT cross this session)
- **P1 doc truth-sync = lead-owned (tb-0214)**. Lead reports docs updated + code audit
  (5 new findings); a report-judge flagged `NEEDS_REFINEMENT` and postflight shows
  `BLOCKED (no research)`. Do NOT edit ONBOARDING.md / synced docs — coordinate only.
- **tb-0209 (Tool_Weapon_Material) = lead-owned.** Do not process.
- **Do NOT fabricate pain verdicts or observation collapses** without sim evidence
  (violates Why/Witness gates). tb-0215..0220 + new tb-0221..0223 need real evidence.
- Git: night rewrote docs/HISTORY_BOOK.md, docs/PENDING_HEURISTICS.md, docs/DREAM_REPORT.md,
  docs/HERALD.md, rep batteries, envelope proposals. These are machine-local night
  artifacts; commit only in a clean verified batch with the lead's doc sync.

### NEW / CHANGED since plan written
- New tasks ripened by the night: tb-0221, tb-0222, tb-0223 (pains -> micro-tasks).
- Task board now ~223 tasks (was 220); open count grew by the 3 ripened + still 11 prior
  minus any claimed.
- Recommended next fix (not yet applied — lead is live on council/dyad): repair the
  LM model-swap bug in `lm_gateway._ensure_model` so the violator step runs for real
  instead of timing out. Offer to apply after tb-0214 settles.

### NEXT SAFE EXECUTION BATCH (pending your go)
1. End-to-end confirm `circadian tick --run` now completes (force due night).
2. Collapse observation-queue features that already HAVE 2 sim sessions (check SimPlaytest
   nodes; Tool_Weapon_Material may get one from lead's tb-0209).
3. Prepare (not apply) the lm_gateway model-swap fix.
4. Begin P2 Loop 4 Tools ONLY after lead releases the construction lane.

---
## BATCH 2 — recommended items executed (2026-07-19, post night-fix)

### (1) End-to-end confirm `circadian tick --run` — DONE
- Forced a due night (moved docs/world/last_night.json aside), ran the REAL
  `python -m core.circadian tick --run`.
- EXIT=0. The violator printed the intended guard:
  `[dream] expectation-violator skipped: timed out after 180s (LM gateway still
  queued - night proceeds model-free)` and result shows `ran_night: true`.
- The prescribed session-entry command is now fixed end-to-end.
- Restored: the run re-created docs/world/last_night.json (clock marked 23:24).

### (2) Collapse observation-queue features with >=2 sim sessions — NOTHING READY
- `collapse_proxy.tend(min_sessions=2)` -> 0 collapsed, 9 awaiting evidence.
- Only `Travel_Vehicle_Flight` has any (1/2); the other 8 are 0/2.
- Per project rule 'no reference, no verdict', NONE were collapsed (would fabricate).
- To unblock: run sleepwalker sim sessions for these features so each reaches 2/2.
  Closest candidate: Travel_Vehicle_Flight needs 1 more session.

### (3) Prepare (NOT apply) the lm_gateway._ensure_model fix — DONE (proposed)
- KEY CORRECTION: the bug is in `core/council.py::_ensure_model` (Will mislabeled it
  `lm_gateway`). AND in THIS environment `CHIMERA_FAST_MODEL`/`CHIMERA_DEEP_MODEL` are
  UNSET -> `_SWAP_ENABLED=False` -> `_ensure_model` is a NO-OP. So it did NOT cause the
  observed night-hang.
- The actual hang = violator generation request stalling in the lm_gateway fair-queue
  (concurrency=1); already neutralized by the dream_loop 180s thread-timeout (Batch 1).
- The `_ensure_model` `:N`-suffix / evict-order defect is a REAL LATENT bug (per Will)
  that bites only when swap is enabled. Proposed fix written to
  `docs/COUNCIL_ENSURE_MODEL_FIX.md`: load-then-evict (no empty-VRAM window),
  `_normalize_model_id` for unrecognized `:N` suffixes, and a loud failure if the
  endpoint ends up empty. NOT applied (lead is live on council/dyad).
- Companion recommendation (separate, for the real hang): add a per-request timeout to
  the violator generation so a wedged model skips cleanly instead of burning 180s.


