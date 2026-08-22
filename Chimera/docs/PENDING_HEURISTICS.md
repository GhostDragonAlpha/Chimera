# PENDING HEURISTICS — the Gardener's queue

Candidates distilled from repeated failures/surprises in the DNA graph.
DELEGATED GARDENER (amendment 2026-07-07): `python -m core.gardener --tend`
(inside every dream_loop) auto-rules this queue — doc-organ entries with a
draft rule self-promote; gate-organ approvals queue for capable implementation;
subsumed entries tombstone. THE HUMAN'S VETO IS ALWAYS LIVE: edit any entry's
status to `vetoed` and the next tend demotes it (doc line removed, veto recorded).
Statuses: pending | promoted (auto ...) | approved (auto — implementation pending)
| vetoed-auto (tombstone) | vetoed (human — demoted ...).


<!-- distilled 2026-07-06T15:32:20Z -->
## H-1: compilation_fail
- status: promoted (auto 2026-07-07)
- kind: failure  |  count: 60  |  last_seen: 2026-07-06T07:36:10
- proposed_organ: gate
- evidence: mutation_53730a2744e1, mutation_5bb42aaba4c8, mutation_de53b37d8a1f, mutation_e29ea9edacfe, mutation_14a347b241fc, mutation_8c5a4195d2b4, mutation_68c61ac2b981, mutation_9cd27cf80996
- sample: compilation_fail
- sample: E:\PythonChimera\Chimera\Source\Chimera\ProceduralGenerated\Tests\ChimeraDSLTests.cpp(52,53): error C2039: 'GetCurrentFuelLiters': is not a member of 'UFlightCo
- sample: error C2039: not a member
- draft_rule: A C2039 missing-member error in ProceduralGenerated/ means template drift — emit the accessor in the same generator change that emits its test.
- agent_note: gate_build_succeeded already BLOCKS on these; this rule is the preventive half (fix at generator, same change). Approve as claude_md rule, or veto as sufficiently covered by the existing gate.

## H-2: grade_CF: Visual_Verification
- status: promoted (auto 2026-07-07)
- kind: grade  |  count: 41  |  last_seen: 2026-07-06T02:51:08
- proposed_organ: claude_md
- evidence: professor_grade_d543406104bab7ca, professor_grade_4b3ac1a8094ad245, professor_grade_5c4febabf91f23f0, professor_grade_caf6e3de66d62355, professor_grade_146029f24a743a1c, professor_grade_7a0262bc83441f63, professor_grade_978b8c378d8792a9, professor_grade_2a89a1885ad991df
- sample: Visual verification returned aborted_wrong_window: Foreground window was 'PythonChimera – README.md'
- sample: Visual verification returned incomplete: Screenshot aborted: Unreal Editor was not the foreground window
- sample: Visual verification returned aborted_wrong_window: Foreground window was 'Claude'
- draft_rule: Never verify from desktop screenshots — capture via MCP control_editor screenshot mode=editor_viewport, which renders the viewport regardless of window focus.
- agent_note: 41 wasted verification cycles from window-focus roulette (pyautogui desktop capture). The MCP pathway exists but the PROHIBITION was never constitutional. Recommend APPROVE -> claude_md. H-4/H-5/H-6 are facets of this same era; consider approving this one and vetoing those as subsumed.

## H-3: verification_not_verified
- status: promoted (auto 2026-07-07)
- kind: failure  |  count: 25  |  last_seen: 2026-07-06T04:49:48
- proposed_organ: claude_md
- evidence: vis_verify_92dc19c53dee1fce, vis_verify_14a9670662e49822, vis_verify_4bbddd832cfdc342, vis_verify_3c1cb72d235b1348, vis_verify_b7d7dde641bafaf1, vis_verify_ab68e97ab2ffc2c8, vis_verify_55ea97d9592750a9, vis_verify_c9087d54692aafbc
- sample: Visual verification: Ground_Metal_Surface → not_verified. {"verified": false, "what_you_see": "The user wants me to act as a visual verification analyst for the
- sample: Visual verification: Ground_Metal_Surface → not_verified. {"verified": false, "what_you_see": "Here's a thinking process:\n\n1.  **Understand User Input:**\n   
- sample: Visual verification: Ground_Sand_Surface → not_verified. {"verified": false, "what_you_see": "Here's a thinking process:\n\n1.  **Understand User Input:**\n   -
- draft_rule: An LM response containing its own reasoning dump ("Here's a thinking process") is a RETRY with a larger token budget, never a verdict — schema-validate before consuming.
- agent_note: 25 false not_verified verdicts because the local model's meta-output was parsed as the answer. Same failure hit THIS session (empty vision verdicts until max_tokens raised 80->1200). Recommend APPROVE -> claude_md; applies to all remaining LM layers (vision is tertiary evidence now).

## H-4: verification_aborted_wrong_window
- status: vetoed-auto (tombstone 2026-07-07 — subsumed)
- kind: failure  |  count: 21  |  last_seen: 2026-07-06T01:01:53
- proposed_organ: mcp_pathways
- evidence: mutation_04bdae683780, mutation_2e94b4f36b73, mutation_84b13589f1b4, mutation_7b2e8cdb643b, mutation_471ed34dd599, mutation_06ee05b777cb, mutation_bd7985b2897a, mutation_bb367018ee94
- sample: Visual verification aborted_wrong_window: AI analysis completed
- draft_rule: (subsumed by H-2 — same window-focus lesson, abort-marker facet)
- agent_note: Recommend VETO as duplicate-of-H-2; this entry stays here as a suppression tombstone so the signature is never re-proposed.

## H-5: verification_fail
- status: vetoed-auto (tombstone 2026-07-07 — subsumed)
- kind: failure  |  count: 20  |  last_seen: 2026-07-05T06:13:09
- proposed_organ: claude_md
- evidence: mutation_5e647acb4c73, mutation_50043ecc32cb, mutation_29c6952a0461, mutation_c04ecc1695bb, mutation_ffafe42c9fb1, mutation_d4c975ea0395, mutation_ac1291294589, mutation_93f9998f0246
- sample: Visual verification fail: AI analysis completed
- draft_rule: (subsumed by H-2/H-3 — generic fail marker from the same desktop-capture + unparsed-LM era)
- agent_note: Recommend VETO as subsumed; tombstone prevents re-proposal.

## H-6: verification_incomplete
- status: vetoed-auto (tombstone 2026-07-07 — subsumed)
- kind: failure  |  count: 19  |  last_seen: 2026-07-06T02:51:08
- proposed_organ: claude_md
- evidence: mutation_da18bce08a2d, mutation_29db1adf57a9, mutation_ef4fa0a4c278, mutation_a9ff385f3008, mutation_35355fd5287f, mutation_163787d7e922, mutation_4ee700064f51, mutation_da563159cf38
- sample: Visual verification incomplete: AI analysis completed
- draft_rule: (subsumed by H-2/H-3 — incomplete marker from the same era)
- agent_note: Recommend VETO as subsumed; tombstone prevents re-proposal.

<!-- distilled 2026-07-06T15:40:55Z -->
## H-7: ralph_apply_<feature>_step
- status: promoted (auto 2026-07-07)
- kind: failure  |  count: 18  |  last_seen: 2026-07-06T04:41:13
- proposed_organ: claude_md
- evidence: mutation_77ea6ac769eb79e4, mutation_fff72331841ce16c, mutation_88ffc7f7d2acfa55, mutation_4ce2fdea764203a0, mutation_d330ae3f9571ef7e, mutation_eb7afcc8d7eeeea7, mutation_dc815743abb2e926, mutation_363c59e1ae09acbf
- sample: RalphLoop: apply_Player_Character_Model_step1 → failed. {"message": "[DynamicToolManager] Initialized with 22 tools across 4 categories\n[UE-MCP] UE_PROJECT_PAT
- sample: RalphLoop: apply_Player_Character_Suit_step1 → failed. {"message": "[DynamicToolManager] Initialized with 22 tools across 4 categories\n[UE-MCP] UE_PROJECT_PATH
- sample: RalphLoop: apply_Player_Character_Lighting_step1 -> failed. {"message": "[DynamicToolManager] Initialized with 22 tools across 4 categories\n[UE-MCP] UE_PROJECT
- draft_rule: Record the MCP response's error field, never raw CLI stdout — a DynamicToolManager boot banner inside an "error" means the wrong stream was captured.
- agent_note: 18 apply-step failures whose recorded "error" is the CLI's startup spam; the true failure was lost, making the failures untriageable later. Recommend APPROVE -> claude_md (observability rule for all MCP-calling code).

## H-8: grade_CF: Player_Character_Lighting
- status: vetoed-auto (tombstone 2026-07-07 — subsumed)
- kind: grade  |  count: 12  |  last_seen: 2026-07-04T05:18:34
- proposed_organ: claude_md
- evidence: prof_grade_76ec897d5061a616, prof_grade_55783a2583f54dd8, prof_grade_9b000e15bf8b6d6a, prof_grade_0ccf095915f32920, prof_grade_7dfe00e4c944fd99, prof_grade_5c5143f0cf135bce, prof_grade_cee394fd32358a7b, prof_grade_76afa05b125eea94
- sample: The user wants me to act as the Professor for the Chimera Project's Ralph Loop.
I need to review a research summary provided in the prompt.
Wait, looking at the
- sample: Here's a thinking process:

1.  **Analyze User Input:**
   - Role: Research analyst for Chimera Project (deep-space trading game in UE5)
   - Task: Feature = 'P
- sample: 
   - *F: Inadequate or missing research.*

   Let's check the provided summary against these criteria:
   - **Technical Parameters:** Has `dimensions`, `radius
- draft_rule: (related to H-3 — the professor-review path parsed LM meta-dumps as grade reasoning; 12 C/F verdicts may be parsing artifacts, not judgments)
- agent_note: Recommend VETO as subsumed by H-3 (schema-validate ALL LM output) — or approve separately if you want the professor path named explicitly. Note: these 12 historic C/F grades polluted GPA history with possibly-false verdicts; the result-grader redesign already removed the LM from the gate path.

<!-- distilled 2026-07-06T16:24:28Z -->
## H-9: ralph_ralph_loop_complete_Player_Character_Lighting
- status: vetoed-auto (tombstone 2026-07-07 — per agent_note)
- kind: failure  |  count: 12  |  last_seen: 2026-07-04T05:35:13
- proposed_organ: claude_md
- evidence: mutation_7ecfb3f135b7ae18, mutation_550c879fe28b4124, mutation_ff729ef0505792cc, mutation_a5cc94c1b1df7f6d, mutation_54db1006d3560a99, mutation_b88e4aa5d3be8b28, mutation_43b4754d74ead0ff, mutation_8af106100d89ceb8
- sample: RalphLoop: ralph_loop_complete_Player_Character_Lighting -> incomplete. {"feature": "Player_Character_Lighting", "loop": 0, "status": "needs_refinement", "verif
- draft_rule: Twelve incomplete loop endings for one feature is retry churn without a targeted study guide — every re-research prompt must quote the grader's lowest categories.
- agent_note: Recommend VETO as superseded — the result-grader redesign already generates study guides on C/F and the H-8 root cause (LM meta-dump grades) drove the churn. Tombstone prevents re-proposal.

## H-10: pathway: build_orchestrator.ue_shutdown -> killed_for_build
- status: promoted (auto 2026-07-07)
- kind: pathway  |  count: 12  |  last_seen: 2026-07-06T04:02:31
- proposed_organ: mcp_pathways
- evidence: pathway_attempt_3e517c048179cfdd, pathway_attempt_3d5996596d09f1f7, pathway_attempt_9f39685541ef77e3, pathway_attempt_3574744951ff40af, pathway_attempt_e8985cac48e6c15d, pathway_attempt_921e5813592aa091, pathway_attempt_ee865905242c80ff, pathway_attempt_cf31600eb01f0688
- sample: Pathway attempt recorded: tool 'build_orchestrator', action 'ue_shutdown', result 'killed_for_build'
- draft_rule: killed_for_build is the build lifecycle working as designed, not a pathway failure — record intended shutdowns as success with a note, or routine builds pollute the failure ledger.
- agent_note: 12 routine pre-build UE shutdowns mis-recorded as failed pathways (they cluster as failures forever). Recommend APPROVE -> claude_md + the concrete fix: build_orchestrator's record call should pass result='success' for intended kills. The distiller itself flagged its own noise source here.

<!-- distilled 2026-07-06T18:34:16Z -->
## H-11: ralph_ralph_loop_complete_Player_Character_Model
- status: vetoed-auto (tombstone 2026-07-07 — subsumed)
- kind: failure  |  count: 12  |  last_seen: 2026-07-06T04:49:48
- proposed_organ: claude_md
- evidence: mutation_28c2cd27ce30a284, mutation_0b49ebfeb34e12e4, mutation_4dff0fabb310dec5, mutation_55aaeca6facbc536, mutation_cb0f8548a01157e2, mutation_a75a79da8dd27502, mutation_dd8771a50908e4d5, mutation_71aaaea24b2aff0d
- sample: RalphLoop: ralph_loop_complete_Player_Character_Model → incomplete. {"feature": "Player_Character_Model", "loop": 0, "status": "needs_refinement", "verified": f
- sample: RalphLoop: ralph_loop_complete_Player_Character_Model -> incomplete. {"feature": "Player_Character_Model", "loop": 0, "status": "needs_refinement", "verified": 
- draft_rule: (same lesson as H-9: incomplete-loop churn from the pre-result-grader era; the feature was later verified A 98.8 under the new regime)
- agent_note: Recommend VETO as superseded — same era and root cause as H-9; tombstone prevents re-proposal.

## H-12: grade_CF: Build_Pipeline
- status: implemented (2026-07-07, capable cycle — gate hardened in core/graphify_interface.py (new extract_ubt_failure_line, used by _mutate_compilation's F-grade reasoning) + core/build_orchestrator.py (self.last_ubt_output persisted across retries; build_project's compile-failure and static-analysis-failure returns now carry verbatim text instead of "Compilation failed"/"Pre-compilation static analysis failed") + core/game_generation_orchestrator.py (forwards full ubt_output, not just the short error string). Placeholder now only fires when a caller truly passed zero output, and says so explicitly instead of "no error text captured". Verified via monkeypatched unit tests (real DNA graph untouched); no live UBT build re-run as part of this change.
- reverified: 2026-07-08, capable cycle (pending_heuristics_review dispatched again; the 2026-07-07 changes above were found already sitting uncommitted in the working tree, so this pass did NOT trust the "implemented" label at face value — re-read all three files line by line and wrote a fresh isolated test harness before accepting it). Result: the prior implementation is real and functionally correct. Test harness monkeypatched load_dna_graph/save_dna_graph, run_static_analysis, compile_with_ubt, and subprocess.run (UnrealEditor.exe was live/running during this session — a real tasklist/taskkill would have killed it, confirming the mock was load-bearing, not paranoia) so nothing touched the live DNA graph, Chimera.Build.cs, level files, or the running editor; confirmed via mtime/process checks after. Covered: extract_ubt_failure_line's 3 tiers, _mutate_compilation's F-grade reasoning for both real and truly-empty ubt_output, build_project's static-analysis-failure and compile-failure return dicts, and the game_generation_orchestrator forwarding line. One real gap found by the harness and fixed: _UBT_CODE_RE only matched C#### compiler codes, so a linker/tool diagnostic with an error code but not the literal word "error" nearby fell through to the tier-3 last-line fallback instead of the real error line — broadened to also match LNK#/MSB#/RC#. (Historical LNK2019 captures already in chimera_dna_graph.json confirm real MSVC output always pairs linker codes with the word "error", so this was defensive hardening for an edge case, not a fix for an observed live failure.) All checks pass after the fix. Still NOT done: no live UBT build was re-run end-to-end (would require deliberately breaking generated C++ and running the full pipeline, which restarts/kills the currently-running UE Editor — out of proportion for this task); changes remain uncommitted in the working tree, same as the 2026-07-07 pass left them.
- reconfirmed: 2026-07-08, capable cycle (pending_heuristics_review dispatched a 3rd time; dispatch text claimed status was still "approved (implementation pending)", which was already stale — did not trust that either). Independently re-read all three files again and wrote two fresh isolated test harnesses from scratch (not reusing prior scripts): 5 checks on extract_ubt_failure_line's tiering (exact MSVC "file(line,col): error CNNNN" line, linker-style "error LNK2019" line with no (line,col) shape, keyword/code-free fallback to last non-blank line, empty input, whitespace-only input), 5 checks on _mutate_compilation/mutate("compilation",...) end-to-end (ProfessorGrade.reasoning and Mutation.fix_description both carry the verbatim line; empty-input case names the gap instead of the old bare "no error text captured"), and 13 checks on build_orchestrator (build_project's static-analysis-fail and compile-fail return dicts under both real-text and empty-text conditions, plus _single_compile's pass/fail/exception paths all setting self.last_ubt_output correctly) — all 23 passed against the real production code. Isolation this pass additionally monkeypatched assemble_uproject and UBTBuilder (neither prior pass had stubbed these at the build_project level), so Step 1's Build.cs/level-copy side effects and the actual UBT subprocess were never invoked either. Grepped for the old "no error text captured"/bare "Compilation failed" placeholders and for any test file asserting the old strings — none remain anywhere in core/ or tests/. Also checked core/result_grader.py specifically (the dispatch text's other suggested location): confirmed it has zero references to compilation/UBT/build-failure text at all — the real path was always graphify_interface.py's automatic F-grade, not the feature-rubric grader, so nothing there needed touching. New fact this pass, not previously true: mid-session a concurrent process (this project's own perpetual orchestrator — task_progress.md's top entries show duty cycles running throughout) committed the entire working tree as `2c074d5` ("chore: add wind system, dust accumulation materials, player character lighting tests, social trade component, universe generation, and workflow updates; update DNA graph and documentation"), which included all three H-12 files verbatim-unchanged (`git diff HEAD~1 HEAD` on the three files matches the working-tree diff already reviewed exactly). **The fix is therefore no longer sitting uncommitted — it is on HEAD as of this pass, closing the one gap the 2026-07-08 reverification explicitly flagged.** I did not run `git commit` myself; this landed from the concurrent process, confirmed via `git log`/`git reflog`, not assumed. Still NOT done, same as both prior passes: no live UBT end-to-end rebuild (still out of proportion — would kill the running editor for a verification-only task). Separately found, NOT fixed (out of scope for H-12, flagged as its own background task instead): `core/graphify_interface.py` defines `save_dna_graph` twice — line 57 (atomic, lock-guarded, the one whose docstring explicitly names the "nightly dream_loop vs a duty cycle vs the sleepwalker" concurrent-writer scenario this exact session just observed happening live) and line 1340 (plain, non-atomic, no lock). Python keeps only the second definition; every real call in this module resolves to the non-atomic one, so the lock-guard is dead code and concurrent writers can race and silently drop each other's nodes. Pre-existing (confirmed already in HEAD before any of today's changes, via `git show HEAD:...`), unrelated to H-12's own text-capture fix, not touched here.
- kind: grade  |  count: 11  |  last_seen: 2026-07-06T07:36:10
- proposed_organ: gate
- evidence: professor_grade_1a92c9ff41eb66f4, professor_grade_8f4a03f041187ce9, professor_grade_0f7ad1992f6d1372, professor_grade_3b51652770d01ac1, professor_grade_828db6a52893ed78, professor_grade_9892b433ad232f61, professor_grade_1f10acc06dc1729d, professor_grade_8de5ed93050d580d
- sample: UBT compilation fail: E:\PythonChimera\Chimera\Source\Chimera\ProceduralGenerated\Tests\ChimeraDSLTests.cpp(52,53): error C2039: 'GetCurrentFuelLiters': is not 
- sample: UBT compilation fail: no error text captured
- sample: UBT compilation fail: error C2039: not a member
- draft_rule: A build-failure grade must carry the failing file:line verbatim — "no error text captured" makes the F untriageable and wastes the retry.
- agent_note: Same family as H-1 (template drift) but the distinct lesson is OBSERVABILITY: one sample lost the error text entirely. Recommend APPROVE -> claude_md (record UBT output verbatim, always), or fold into H-7's capture-the-right-stream rule if you prefer one observability heuristic.

<!-- distilled 2026-07-06T19:43:37Z -->
## H-13: grade_CF: System_Economy
- status: promoted (auto 2026-07-07)
- kind: grade  |  count: 3  |  last_seen: 2026-07-06T06:58:24
- proposed_organ: claude_md
- evidence: professor_grade_7886af92f495ccd1, professor_grade_364a07e3116f20a6, professor_grade_bf25d5d3a1fc673f
- sample: Professor review: Price bounds D, Fluctuation F (needs mean reversion), Station spread A. Overall C pending adjustments.
- sample: [result-grader 52.8/100] correctness 13.3/40: 1/1 tests passed; coverage 1/3 declared criteria | stability 15.0/25: crash-free; fps unmeasured (0/5); growth unm
- sample: [result-grader 59.5/100] correctness 20.0/40: 2/2 tests passed; coverage 2/4 declared criteria | stability 15.0/25: crash-free; fps unmeasured (0/5); growth unm
- draft_rule: Economy features repeatedly grade C/F on partial criteria coverage and unmeasured fps; run telemetry foregrounded and test every declared criterion before grading System_Economy.

<!-- distilled 2026-07-07T00:17:27Z -->
## H-14: human_rejection: Verb_Step
- status: promoted (auto 2026-07-07)
- kind: human_rejection  |  count: 1  |  last_seen: 2026-07-07T00:07:52
- proposed_organ: claude_md
- evidence: observation_f629252c5bdbcd07
- sample: I have no ability to move my character
- draft_rule: Verified-by-injection is not playable — never stage a feature for observation until real player input drives it end-to-end, read back in PIE.

<!-- distilled 2026-07-07T07:15:00Z -->
## H-15: surprise: beat discovered expected gap
- status: vetoed-auto (tombstone 2026-07-07 — subsumed)
- kind: surprise  |  count: 19  |  last_seen: 2026-07-07T07:13:39
- proposed_organ: claude_md
- evidence: surprise_561ad640d61383db, surprise_f732e4e5178a9cc4, surprise_bd61a47547bc4f90, surprise_22575007835ae5b4, surprise_4723e5cef53ef4cf, surprise_d0db022ba909e608, surprise_717d27a484955a65, surprise_b6864047f6143dfc
- sample: expected '' but 'failed: {"expect": {"log_contains": "[DEMOBEAT]"}, "ok": fal'
- sample: expected '' but 'blocked: {"error": "unknown action {'camera_yaw_rotate': 360'
- sample: expected '' but 'blocked: {"error": "unknown action {'simulate_input': {'type'
- draft_rule: (subsumed by the level-clobber root-cause fix 2026-07-07 — this sim_rejection was a wrong-world artifact; beats now assert world_is)

## H-16: pathway: sleepwalker.beat_run -> partial
- status: vetoed-auto (tombstone 2026-07-07 — subsumed)
- kind: pathway  |  count: 3  |  last_seen: 2026-07-07T07:13:39
- proposed_organ: mcp_pathways
- evidence: pathway_attempt_fddb0da7c8b8b33e, pathway_attempt_bb59070e8142192f, pathway_attempt_98698af558567a7c
- sample: Pathway attempt recorded: tool 'sleepwalker', action 'beat_run', result 'partial'
- draft_rule: (subsumed by the level-clobber root-cause fix 2026-07-07 — this sim_rejection was a wrong-world artifact; beats now assert world_is)

<!-- distilled 2026-07-07T13:37:34Z -->
## H-17: sim_rejection: verb_interactions/visor_inspection_pedestal
- status: promoted (auto 2026-07-07)
- kind: sim_rejection  |  count: 3  |  last_seen: 2026-07-07T07:25:01
- proposed_organ: claude_md
- evidence: simtest_0bb93cab8b7d662a, simtest_591e6833d4c01704, simtest_fbd1071132dfb65a
- sample: blocked: [{"error": "unknown action {'move_to': {'x': 600, 'y': 600, 'z': 120}}"}]
- sample: failed: [{"expect": {"screenshot_taken": "visor_inspection_pedestal"}, "ok": false, "note": "unknown expect ['screenshot_taken']
- sample: failed: [{"expect": {"pawn_within": {"x": 600, "y": 600, "r": 300}}, "ok": false, "note": "dist=14216uu (loc x=14803.14792394638
- draft_rule: Beat scripts must declare only Sleepwalker-registered actions before playtest dispatch.
- evidence_count: 3 (all 9 beats in sim_verb_interactions session failed with unknown action errors)
- sample_evidence: "visor_inspection_pedestal blocked: unknown action {'move_to': {'x': 600, 'y': 600, 'z': 120}}"
- gardener_recommendation: APPROVE — Sleepwalker discovers beat-schema gaps (missing move_to, simulate_input, camera actions) before human playtest. Gate recommendation: validate beat actions at dispatch time, not runtime.

## H-18: sim_rejection: verb_interactions/weapon_tool_examine
- status: promoted (auto 2026-07-07)
- kind: sim_rejection  |  count: 3  |  last_seen: 2026-07-07T07:25:01
- proposed_organ: claude_md
- evidence: simtest_0bb93cab8b7d662a, simtest_591e6833d4c01704, simtest_fbd1071132dfb65a
- sample: blocked: [{"error": "unknown action {'move_to': {'x': 400, 'y': -400, 'z': 50}}"}]
- sample: failed: [{"expect": {"screenshot_taken": "weapon_tool_examine"}, "ok": false, "note": "unknown expect ['screenshot_taken']"}]
- sample: failed: [{"expect": {"pawn_within": {"x": 400, "y": -400, "r": 300}}, "ok": false, "note": "dist=17209uu (loc x=17603.9282441139
- possible_conflict_with: H-17  (IDENTICAL ROOT CAUSE: same session, same unknown-action class)
- draft_rule: Beat scripts must declare only Sleepwalker-registered actions before playtest dispatch.
- evidence_count: 3 (same sim_verb_interactions session; all 9 beats failed with unknown action errors)
- sample_evidence: "weapon_tool_examine blocked: unknown action {'move_to': {'x': 400, 'y': -400, 'z': 50}}"
- gardener_recommendation: VETO as subsumed by H-17 — identical root cause (beat-schema gap) from same session. Consolidate into one heuristic: "Sleepwalker discovers beat-schema gaps before playtest."

<!-- distilled 2026-07-08T07:15:02Z -->
## H-19: human_rejection: Verb_Look
- status: promoted (auto 2026-07-08)
- kind: human_rejection  |  count: 3  |  last_seen: 2026-07-08T04:19:38
- proposed_organ: claude_md
- evidence: observation_4f5df1d23ee81c4b, observation_29973953faf496a2, observation_bdbc5d02c1f55134
- sample: automated rejection sweep: simulation evidence indicts this feature (1 failing outcome(s)) in simtest_fbd1071132dfb65a
- sample: Independently re-verified beyond the suspect beat evidence. The ORIGINAL task_9c0d4fd9 caveat (wrong pawn class DefaultPawn + unregistered MCP actions) is REFUT
- sample: Rig re-verified clean post-input-fix across 2 consecutive sleepwalk sessions (simtest_fadc939050ee23a7, simtest_e9854be8cf3d0d83): world_is/is_pie/pawn_class al
- draft_rule: Before running a rejection sweep, use the most recent simtest for that feature -- an old simtest_id can indict a feature already fixed and re-verified since.

## H-20: human_rejection: Verb_Bend
- status: vetoed-auto (tombstone 2026-07-08 — subsumed)
- kind: human_rejection  |  count: 3  |  last_seen: 2026-07-08T04:19:38
- proposed_organ: claude_md
- evidence: observation_44efdff7a36a3d5c, observation_f425fa8d8104e1ab, observation_895434ae9b085bf4
- sample: automated rejection sweep: simulation evidence indicts this feature (1 failing outcome(s)) in simtest_fbd1071132dfb65a
- sample: Independently verified beyond beat evidence (rig defects refuted -- see Verb_Look). Verb_Bend has NO input binding anywhere in the codebase: BP_Astronaut_Charac
- sample: Rig re-verified clean post-input-fix (2 sessions), but the beat only checks is_pie/pawn_class -- it does not test crouch functionally. The immediately-prior ses
- draft_rule: (subsumed by H-19 -- identical stale-rejection root cause, same simtest_fbd1071132dfb65a already refuted by 2 later clean sessions; its functional-gap concern is separately covered by H-14)

<!-- distilled 2026-07-08T19:41:42Z -->
## H-21: human_rejection: Verb_Shovel
- status: promoted (auto 2026-07-11)
- kind: human_rejection  |  count: 4  |  last_seen: 2026-07-08T15:37:57
- proposed_organ: claude_md
- evidence: observation_45b8b52d04bb680f, observation_bb1ac7c1c90f2343, observation_c1af4475a658d6b3, observation_d30ab5686b763ed3
- sample: automated rejection sweep: simulation evidence indicts this feature (3 failing outcome(s)) in simtest_fbd1071132dfb65a
- sample: Independently verified beyond beat evidence (rig defects refuted -- see Verb_Look). Two additional, separate gaps found: (1) ATool_Shovel (Source/Chimera/Proced
- sample: Beats FAILED (not reached) in both fresh sessions (simtest_fadc939050ee23a7: dist=9735/10535uu; simtest_e9854be8cf3d0d83: dist=9535/10335uu) -- but this is the 
- draft_rule: A verb needs behavior, not metadata: ATool_Shovel had DigRadius but no Dig() — beats must press the verb key and assert a world-state change.
- agent_note: drafted 2026-07-11 from observation_bb1ac7c1c90f2343 (static prop, numeric metadata, zero digging logic; beat only walked pad proximity). Distinct from H-14: even with input wired there is no function to call. APPROVE -> claude_md.

## H-22: human_rejection: Verb_PickUp
- status: promoted (auto 2026-07-11)
- kind: human_rejection  |  count: 4  |  last_seen: 2026-07-08T15:38:23
- proposed_organ: claude_md
- evidence: observation_e9e42a55deceea63, observation_bbd3824598c5d283, observation_894b90c0c982fb7e, observation_ed0254872e5fb7b9
- sample: automated rejection sweep: simulation evidence indicts this feature (1 failing outcome(s)) in simtest_fbd1071132dfb65a
- sample: Independently verified beyond beat evidence (rig defects refuted -- see Verb_Look). Triple gap, each confirmed directly rather than inferred: (1) BP_Astronaut_C
- sample: Rig re-verified clean post-input-fix (2 sessions), same shallow is_pie/pawn_class check as before. The immediately-prior session's direct component-listing evid
- draft_rule: Read back live-PIE pawn components before staging an interaction verb — PickUp's component was never attached, bound, or given a level actor to grab.
- agent_note: drafted 2026-07-11 from observation_bbd3824598c5d283 (two independent live-PIE component listings: 5 components, no UPickupInteractionComponent; no Interact binding; no APickupActor in level). APPROVE -> claude_md.

<!-- distilled 2026-07-08T23:20:13Z -->
## H-23: human_rejection: Verb_Drop
- status: vetoed-auto (tombstone 2026-07-11 — subsumed)
- kind: human_rejection  |  count: 4  |  last_seen: 2026-07-08T15:38:32
- proposed_organ: claude_md
- evidence: observation_22aff4c35c846157, observation_837c826fac9186ed, observation_2d845fd5545f3279, observation_6bea305cf7f95767
- sample: automated rejection sweep: simulation evidence indicts this feature (1 failing outcome(s)) in simtest_fbd1071132dfb65a
- sample: Independently verified beyond beat evidence (rig defects refuted -- see Verb_Look). Same missing-binding gap as Verb_PickUp: no Drop key binding exists anywhere
- sample: Rig re-verified clean post-input-fix (2 sessions), same shallow is_pie/pawn_class check as before. ADropActor exists as a reasonably complete physics-drop imple
- draft_rule: (subsumed by H-22 — same never-wired gap: ADropActor physics is complete but no input path and nothing in inventory until PickUp lands; input-wiring lesson already covered by H-14)

## H-24: human_rejection: Ground_Rock_Surface
- status: promoted (auto 2026-07-11)
- kind: human_rejection  |  count: 1  |  last_seen: 2026-07-08T04:18:59
- proposed_organ: claude_md
- evidence: observation_cf32cafa76fd3b40
- sample: Reopening the 2026-07-07T06:46:59 observed_provisional acceptance (simtest_0dec5fc92db45fee, 4 clean sessions). walk_metal_to_rock -- the only beat tagging this
- draft_rule: A feature tagged only by movement beats is hostage to rig health — zero-displacement failures (GameMode PlayerControllerClass unset) indict the rig, not the surface.
- agent_note: drafted 2026-07-11 from observation_cf32cafa76fd3b40 (material acceptance reopened by frozen-at-spawn beats; root cause was the rig, fixed task_c11196d2 and re-verified at ~727-867uu/s). APPROVE -> claude_md.

<!-- distilled 2026-07-08T23:31:30Z -->
## H-25: sim_rejection: verb_interactions/verb_shovel_rock_surface_location
- status: promoted (auto 2026-07-11)
- kind: sim_rejection  |  count: 13  |  last_seen: 2026-07-08T23:31:23
- proposed_organ: claude_md
- evidence: simtest_591e6833d4c01704, simtest_fbd1071132dfb65a, simtest_c18e964f43800746, simtest_fadc939050ee23a7, simtest_efc1292c57ce8798, simtest_e9854be8cf3d0d83, simtest_33f22bb0dbe1ec5f, simtest_4c757e3acd6ad033
- sample: failed: [{"expect": {"screenshot_taken": "verb_shovel_rock_view"}, "ok": false, "note": "unknown expect ['screenshot_taken']"}]
- sample: failed: [{"expect": {"pawn_within": {"x": 2000, "y": 0, "r": 900}}, "ok": false, "note": "dist=5601uu (loc x=7600.763583183289, 
- sample: failed: [{"expect": {"pawn_within": {"x": 2000, "y": 0, "r": 900}}, "ok": false, "note": "dist=2000uu (loc x=0, y=0)"}]
- possible_conflict_with: heuristic_5031dfdbe0e5667d (Beat scripts must declare only Sleepwalker-registered action); heuristic_2dfd6804008ee83d (Beat scripts must declare only Sleepwalker-registered action); H-17; H-18  (Gardener: reconcile)
- draft_rule: Position-expect beats must reset_position at beat start — W-drift accumulates across sequential beats and BugItGo is refused during PIE.
- agent_note: drafted 2026-07-11; reconciles the H-17/H-18 conflict flag: H-17 covers unregistered ACTIONS at dispatch, this covers runtime drift between position expects (regolith_yard already carries the fix in its provenance note). H-26/H-27 are the same root cause and are subsumed here. APPROVE -> claude_md.

## H-26: sim_rejection: verb_interactions/verb_shovel_sand_surface_location
- status: vetoed-auto (tombstone 2026-07-11 — subsumed)
- kind: sim_rejection  |  count: 13  |  last_seen: 2026-07-08T23:31:23
- proposed_organ: claude_md
- evidence: simtest_591e6833d4c01704, simtest_fbd1071132dfb65a, simtest_c18e964f43800746, simtest_fadc939050ee23a7, simtest_efc1292c57ce8798, simtest_e9854be8cf3d0d83, simtest_33f22bb0dbe1ec5f, simtest_4c757e3acd6ad033
- sample: failed: [{"expect": {"actor_exists": "SandDrift_FX"}, "ok": false, "note": "present=False"}]
- sample: failed: [{"expect": {"actor_exists": "SandDrift_FX"}, "ok": true, "note": "present=True"}]
- sample: blocked: [{"error": "control_editor.console_command: Command not executed: BugItGo 4000.0 0.0 150.0 0.0 0.0 0.0"}]
- possible_conflict_with: heuristic_5031dfdbe0e5667d (Beat scripts must declare only Sleepwalker-registered action); heuristic_2dfd6804008ee83d (Beat scripts must declare only Sleepwalker-registered action); H-17; H-18  (Gardener: reconcile)
- draft_rule: (subsumed by H-25 — same accumulated-drift root cause, sand-pad facet; its BugItGo-refused sample is the one H-25's rule quotes)

<!-- distilled 2026-07-08T23:36:25Z -->
## H-27: sim_rejection: verb_interactions/verb_shovel_metal_surface_location
- status: vetoed-auto (tombstone 2026-07-11 — subsumed)
- kind: sim_rejection  |  count: 13  |  last_seen: 2026-07-08T23:34:54
- proposed_organ: claude_md
- evidence: simtest_591e6833d4c01704, simtest_fbd1071132dfb65a, simtest_fadc939050ee23a7, simtest_efc1292c57ce8798, simtest_e9854be8cf3d0d83, simtest_33f22bb0dbe1ec5f, simtest_4c757e3acd6ad033, simtest_04c6edf075c50145
- sample: failed: [{"expect": {"screenshot_taken": "verb_shovel_metal_view"}, "ok": false, "note": "unknown expect ['screenshot_taken']"}]
- sample: failed: [{"expect": {"pawn_within": {"x": 0, "y": 0, "r": 600}}, "ok": false, "note": "dist=3600uu (loc x=3600.0008583068848, y=
- sample: failed: [{"expect": {"pawn_within": {"x": 0, "y": 0, "r": 600}}, "ok": false, "note": "dist=9735uu (loc x=9727.041600935105, y=4
- possible_conflict_with: heuristic_5031dfdbe0e5667d (Beat scripts must declare only Sleepwalker-registered action); heuristic_2dfd6804008ee83d (Beat scripts must declare only Sleepwalker-registered action); H-17; H-18  (Gardener: reconcile)
- draft_rule: (subsumed by H-25 — same accumulated-drift root cause, metal-pad facet)

## H-28: sim_rejection: regolith_yard/jump_probe
- status: promoted (auto 2026-07-11)
- kind: sim_rejection  |  count: 8  |  last_seen: 2026-07-08T20:26:54
- proposed_organ: claude_md
- evidence: simtest_6a0be0d290cf9c59, simtest_d6e2cb58b97175ad, simtest_613400f2fcc63327, simtest_9cd9a1ac25867a73, simtest_b9c246f4cef92293, simtest_1c77ee388da8bbd4, simtest_96d43b91bd6167e2, simtest_8d3a74728559a85a
- sample: failed: [{"expect": {"log_contains": "[DEMOBEAT]"}, "ok": false, "note": "log_hit=False"}]
- sample: failed: [{"expect": {"pawn_z_above": 130}, "ok": false, "note": "z=102"}]
- sample: failed: [{"expect": {"pawn_z_above": 130}, "ok": false, "note": "z=-26947"}]
- draft_rule: Probe jumps by timed pawn_z read-back, not log_contains — and reset_position first: z=-26947 shows the pawn had already drifted off the world.
- agent_note: drafted 2026-07-11; the beat file's _note records the sim finding its own weak log_contains test (surprise 2026-07-06); z=102 samples are the pre-input-fix era, z=-26947 is drift off the playable floor. APPROVE -> claude_md.

<!-- distilled 2026-07-08T23:45:34Z -->
## H-29: sim_rejection: regolith_yard/walk_rock_to_sand_basin
- status: promoted (auto 2026-07-11)
- kind: sim_rejection  |  count: 4  |  last_seen: 2026-07-08T04:13:49
- proposed_organ: claude_md
- evidence: simtest_d6e2cb58b97175ad, simtest_613400f2fcc63327, simtest_9cd9a1ac25867a73, simtest_b9c246f4cef92293
- sample: failed: [{"expect": {"actor_exists": "SandDrift_FX"}, "ok": true, "note": "present=True"}]
- possible_conflict_with: H-28  (Gardener: reconcile)
- draft_rule: Compound beats fail for shifting root causes (frozen input, then missing SandDrift_FX) — attribute rejection to the failing expect's subsystem, not every tagged feature.
- agent_note: drafted 2026-07-11; reconciles the H-28 flag: H-28 is the jump-probe read-back lesson, this is compound-beat attribution. Deliberately NOT subsumed/tombstoned — the signature has a LIVE new failure mode (simtest_ef8ab7dcb8119386 2026-07-11: pawn_within ok at dist=1uu, actor_exists SandDrift_FX present=False, the inverse of these four evidenced runs) and a tombstone would false-suppress it (open phantom pain phase_da55128aec6d109a:P1). APPROVE -> claude_md.

<!-- distilled 2026-07-09T07:15:01Z -->
## H-30: sim_rejection: verb_interactions/verb_look_location
- status: promoted (auto 2026-07-11)
- kind: sim_rejection  |  count: 4  |  last_seen: 2026-07-09T06:38:38
- proposed_organ: claude_md
- evidence: simtest_591e6833d4c01704, simtest_fbd1071132dfb65a, simtest_f276468c8122d640, simtest_f06ba5fb30ea6ffc
- sample: failed: [{"expect": {"screenshot_taken": "verb_look_360_view"}, "ok": false, "note": "unknown expect ['screenshot_taken']"}]
- sample: failed: [{"expect": {"pawn_class": "BP_Astronaut_Character_C"}, "ok": false, "note": "pawn_class=DefaultPawn"}]
- sample: failed: [{"expect": {"control_rotation_yaw_delta": 0.5}, "ok": false, "note": "inspect.get_property failed on all controller pat
- possible_conflict_with: heuristic_5031dfdbe0e5667d (Beat scripts must declare only Sleepwalker-registered action); heuristic_2dfd6804008ee83d (Beat scripts must declare only Sleepwalker-registered action); H-17; H-18  (Gardener: reconcile)
- draft_rule: Expects are schema-bound like actions — unknown expects (screenshot_taken, unreadable controller properties) fail beats at runtime; validate the expect vocabulary at dispatch.
- agent_note: drafted 2026-07-11; reconciles the H-17/H-18 conflict flag: H-17's promoted rule covers ACTIONS only, this extends the dispatch-time validation lesson to EXPECTS (pawn_class=DefaultPawn samples are the fixed rig era, not the live lesson). APPROVE -> claude_md.

<!-- distilled 2026-07-11T22:27:44Z -->
## H-31: sim_rejection: audio_visual_sync/spawn_and_verify_audio_system
- status: promoted (auto 2026-07-11)
- kind: sim_rejection  |  count: 4  |  last_seen: 2026-07-11T19:09:25
- proposed_organ: claude_md
- evidence: simtest_dbe50ff88351edb2, simtest_f2dc4faedd6ac1c6, simtest_f2425d6b7d751016, simtest_750dc02ab4f67c81
- sample: blocked: [{"error": "unknown action {'command': 'ClearFootstepSyncTelemetry'}"}]
- sample: blocked: [{"error": "manage_tools.ClearFootstepSyncTelemetry: failed"}]
- draft_rule: Telemetry commands that fall back to hardcoded defaults indicate missing component integration at runtime (UComponent not attached, or not populating properties at BeginPlay) — verify component attachment in character blueprint and initialization order before blaming MCP action handlers.
- agent_note: Investigated 2026-07-11 via av_sync_agent5_investigation (simtest). ClearFootstepSyncTelemetry hits both manage_tools and execute_python fallbacks but beat passes because real beat expectations haven't been checked yet. Downstrea m walk_slow_on_sand (H-32) hits same root cause when expecting telemetry data. Root cause: SandSoundComponent (Source/Chimera/SandSoundComponent.cpp) either not attached to BP_Astronaut_Character or not populating footstep counters at runtime. APPROVE -> claude_md (component integration protocol).

## H-32: sim_rejection: audio_visual_sync/walk_slow_on_sand
- status: promoted (auto 2026-07-11)
- kind: sim_rejection  |  count: 4  |  last_seen: 2026-07-11T19:09:25
- proposed_organ: claude_md
- evidence: simtest_dbe50ff88351edb2, simtest_f2dc4faedd6ac1c6, simtest_f2425d6b7d751016, simtest_750dc02ab4f67c81
- sample: failed: [{"expect": {"sync_events_recorded": 3, "note": "Expect ~3 footsteps during 2.5s walk (400ms interval)"}, "ok": false, "
- sample: blocked: [{"error": "manage_tools.GetFootstepSyncEventCount: failed"}]
- possible_conflict_with: H-31  (Gardener: reconcile)
- draft_rule: When telemetry queries return hardcoded defaults (count=0, latency=999), the beat's expectations fail not because of beat schema but because the backend component isn't populating data — verify SandSoundComponent attachment and footstep event tracking at runtime before debugging beat expectations.
- agent_note: Investigated 2026-07-11 via av_sync_agent5_investigation (simtest av_sync_agent5_investigation). All 6 footstep telemetry getters (GetFootstepSyncEventCount, GetMaxFootstepSyncLatencyMs, GetLastFootstepVolume) hit fallback defaults. Beat walked 1600uu (pawn_within passed), then expected sync_events_recorded >= 3 and sync_latency_ms_max < 100 but got 0 and 999. Shared root cause with H-31: SandSoundComponent integration. Reconcile H-31 + H-32 into one rule (component integration protocol) or keep separate for beat-schema vs backend-integration distinction. APPROVE -> claude_md (Shift key naming is separate issue; 3rd beat walk_fast_on_sand hit "Invalid key: Shift" error — sleepwalker sends "Shift" but control_editor expects LShift/RShift).

<!-- distilled 2026-07-11T23:32:56Z -->
## H-33: sim_rejection: audio_visual_sync/report_telemetry
- status: promoted (auto 2026-07-11)
- kind: sim_rejection  |  count: 5  |  last_seen: 2026-07-11T23:10:40
- proposed_organ: claude_md
- evidence: simtest_dbe50ff88351edb2, simtest_f2dc4faedd6ac1c6, simtest_f2425d6b7d751016, simtest_750dc02ab4f67c81, simtest_b8f7b2ffb83d2b12
- sample: blocked: [{"error": "unknown action {'command': 'GetFootstepSyncEventCount', 'store_as': 'total_events'}"}]
- sample: blocked: [{"error": "manage_tools.GetFootstepSyncEventCount: failed"}]
- sample: blocked: [{"error": "inspect.runtime_report: failed"}]
- possible_conflict_with: heuristic_fe52b1dc74838df6 (Investigate audio_visual_sync sim_rejection; verify test har); heuristic_f3583c561cfd251c (Investigate audio_visual_sync sim_rejection; verify test har); H-31; H-32  (Gardener: reconcile)
- draft_rule: Investigate audio_visual_sync report_telemetry; verify test harness and beat reg

<!-- distilled 2026-07-12T07:15:01Z -->
## H-34: human_rejection: audio_visual_sync/telemetry_accessors
- status: promoted (auto 2026-07-12)
- kind: human_rejection  |  count: 1  |  last_seen: 2026-07-12T00:01:01
- proposed_organ: claude_md
- evidence: observation_b7a437ed43c79e13
- sample: SandSoundComponent either not attached to BP_Astronaut_Character or not populating footstep counters at runtime; verify component attachment and initialization 
- draft_rule: Verify required components and assets are spawned and registered.

<!-- distilled 2026-07-12T22:19:43Z -->
## H-35: elimination_audio_visual_sync/telemetry_accessors
- status: promoted (auto 2026-07-12)
- kind: failure  |  count: 3  |  last_seen: 2026-07-12T16:24:06
- proposed_organ: claude_md
- evidence: elim_65f84a195c149377, elim_71b935361cee2319, elim_043bb7affad30ff4
- sample: Eliminated for audio_visual_sync/telemetry_accessors: MCP action handlers / command dispatch as root cause
- sample: Eliminated for audio_visual_sync/telemetry_accessors: beat expect schema as root cause
- sample: Eliminated for audio_visual_sync/telemetry_accessors: beat schema or MCP dispatch as root cause
- draft_rule: Investigate elimination_audio_visual_sync telemetry_accessors; verify test harne

<!-- distilled 2026-07-13T07:15:01Z -->
## H-36: sim_rejection: audio_visual_sync/walk_fast_on_sand
- status: promoted (auto 2026-07-13)
- kind: sim_rejection  |  count: 9  |  last_seen: 2026-07-12T18:33:35
- proposed_organ: claude_md
- evidence: simtest_dbe50ff88351edb2, simtest_f2dc4faedd6ac1c6, simtest_f2425d6b7d751016, simtest_750dc02ab4f67c81, simtest_b8f7b2ffb83d2b12, simtest_536c81002961d807, simtest_b1e7984ff89a9bdc, simtest_1e4fe7b372af6644
- sample: failed: [{"expect": {"volume_scales_with_speed": true, "note": "Sprint volume should be 2-3x louder than walk"}, "ok": false, "n
- sample: blocked: [{"error": "control_editor.simulate_input: Invalid key: Shift"}]
- sample: blocked: [{"error": "control_editor.simulate_input: failed"}]
- possible_conflict_with: heuristic_fe52b1dc74838df6 (Investigate audio_visual_sync sim_rejection; verify test har); heuristic_f3583c561cfd251c (Investigate audio_visual_sync sim_rejection; verify test har); heuristic_d79d01761718bc42 (Investigate audio_visual_sync report_telemetry; verify test ); H-31  (Gardener: reconcile)
- draft_rule: Implement missing input bindings and verify actor registration.

## H-37: sim_rejection: regolith_yard/walk_metal_to_rock
- status: promoted (auto 2026-07-13)
- kind: sim_rejection  |  count: 4  |  last_seen: 2026-07-08T04:13:49
- proposed_organ: claude_md
- evidence: simtest_d6e2cb58b97175ad, simtest_613400f2fcc63327, simtest_9cd9a1ac25867a73, simtest_b9c246f4cef92293
- sample: failed: [{"expect": {"pawn_within": {"x": 2000, "y": 0, "r": 900}}, "ok": false, "note": "dist=2000uu (loc x=0, y=0)"}]
- sample: failed: [{"expect": {"pawn_within": {"x": 2000, "y": 0, "r": 900}}, "ok": false, "note": "dist=3550uu (loc x=5527.516165861163, 
- sample: failed: [{"expect": {"pawn_within": {"x": 2000, "y": 0, "r": 900}}, "ok": false, "note": "dist=3549uu (loc x=5526.689419635806, 
- possible_conflict_with: heuristic_52e2728aa88ab00a (Probe jumps by timed pawn_z read-back, not log_contains — an); heuristic_66e973934c7b5322 (Compound beats fail for shifting root causes (frozen input, ); H-28; H-29  (Gardener: reconcile)
- draft_rule: Verify beat spawn location distances and pawn navigation constraints.

<!-- distilled 2026-07-14T04:00:39Z -->
## H-38: surprise: correction feature finalized frame
- status: promoted (auto 2026-07-14)
- kind: surprise  |  count: 29  |  last_seen: 2026-07-12T00:00:40
- proposed_organ: claude_md
- evidence: surprise_8f2156a52fee6dee, surprise_8f38358cf130c841, surprise_4af0a68589b9d1dd, surprise_4cd71430620dd2fe, surprise_7ae3863c51fbb9fe, surprise_ddf35ced39c5314c, surprise_e1e3e5bbbf25c0dc, surprise_9442148eacc4d1da
- sample: expected 'system verification (rubric grade) matches human judgment' but 'I have no ability to move my character'
- sample: expected 'system verification (rubric grade) matches human judgment' but 'automated rejection sweep: simulation evidence indicts this '
- sample: expected 'system verification (rubric grade) matches human judgment' but 'Independently re-verified beyond the suspect beat evidence. '
- draft_rule: Investigate correction feature; verify test harness and beat registration.

## H-39: pathway: animation_physics.add_anim_notify -> failed
- status: promoted (auto 2026-07-14)
- kind: pathway  |  count: 3  |  last_seen: 2026-07-07T05:50:08
- proposed_organ: mcp_pathways
- evidence: pathway_attempt_e7fbb6ba12043a86, pathway_attempt_27bd6312e8b9fe29, pathway_attempt_b3ba3afc4acb9122
- sample: Pathway attempt recorded: tool 'animation_physics', action 'add_anim_notify', result 'failed'
- draft_rule: Investigate add_anim_notify animation_physics; verify test harness and beat regi

<!-- distilled 2026-07-15T04:32:28Z -->
## H-40: surprise: actors bp_verb_ hollow may
- status: promoted (auto 2026-07-15)
- kind: surprise  |  count: 4  |  last_seen: 2026-07-14T16:20:26
- proposed_organ: claude_md
- evidence: surprise_f9cf5c9392753082, surprise_f6e315251e2d0141, surprise_72d5eb06de75526f, surprise_43076b35ddcff068
- sample: expected 'research per Research Depth Protocol' but 'Pain verdict confirmed via existing Verb_Shovel rejection ev'
- draft_rule: Investigate actors bp_verb_; verify test harness and beat registration.

## H-41: surprise: bad costless creation ending
- status: promoted (auto 2026-07-15)
- kind: surprise  |  count: 4  |  last_seen: 2026-07-15T03:42:51
- proposed_organ: claude_md
- evidence: surprise_d2a5983cf9bb4a7d, surprise_0b43b9494057da46, surprise_20cde4e1a1895920, surprise_810c554ed2310b0f
- sample: expected 'research per Research Depth Protocol' but 'GenerationSubsystem implementation followed existing generat'
- sample: expected 'fix the generator template, never the generated C++' but '1 hand-edit(s) to generator-owned C++:'
- sample: expected 'Research Depth Protocol requires research (incl. technical/i' but 'no research recorded this session; postflight blocked'
- draft_rule: Investigate bad costless; verify test harness and beat registration.

<!-- distilled 2026-07-15T07:15:01Z -->
## H-42: surprise: blocker draft dream endpoint
- status: promoted (auto 2026-07-15)
- kind: surprise  |  count: 3  |  last_seen: 2026-07-14T15:28:19
- proposed_organ: claude_md
- evidence: surprise_c2ba39e5fbaa9fbe, surprise_52995c367eff645c, surprise_d03593c26a8651ef
- sample: expected '' but 'Solver drafted a fix plan (confidence 0.85); steps executed:'
- sample: expected '' but 'Solver drafted a fix plan (confidence 0.3); steps executed: '
- draft_rule: Investigate blocker draft; verify test harness and beat registration.

## H-43: surprise: chaos chaos_organ core created
- status: promoted (auto 2026-07-15)
- kind: surprise  |  count: 3  |  last_seen: 2026-07-15T03:00:32
- proposed_organ: claude_md
- evidence: surprise_2883a942c2459d92, surprise_420156d675dfd220, surprise_30b89fa3d45aa1f7
- sample: expected 'Research Depth Protocol requires research (incl. technical/i' but 'no research recorded this session; postflight blocked'
- sample: expected 'research per Research Depth Protocol' but 'Creating chaos_organ (core/chaos.py) and noting CostlessLife'
- draft_rule: Investigate chaos chaos_organ; verify test harness and beat registration.

<!-- distilled 2026-07-15T08:46:03Z -->
## H-44: surprise: fixes generationsubsystem pipeline research
- status: promoted (auto 2026-07-15)
- kind: surprise  |  count: 3  |  last_seen: 2026-07-15T04:25:06
- proposed_organ: claude_md
- evidence: surprise_ff25347b7a993099, surprise_932e235b57f7963b, surprise_8b867b81b45fa731
- sample: expected 'research per Research Depth Protocol' but 'VoiceEntity USoundCue to USoundBase cast fix followed UE5 C+'
- sample: expected 'research per Research Depth Protocol' but 'GenerationSubsystem implementation followed existing generat'
- draft_rule: Investigate fixes generationsubsystem; verify test harness and beat registration

<!-- distilled 2026-07-15T12:18:02Z -->
## H-45: surprise: bridge dsl fixes mapping
- status: promoted (auto 2026-07-15)
- kind: surprise  |  count: 4  |  last_seen: 2026-07-15T10:16:20
- proposed_organ: claude_md
- evidence: surprise_cadbd73e8c930326, surprise_f2caceb3e708111d, surprise_4619a4612c524abc, surprise_2762ec5e33f38f09
- sample: expected 'research per Research Depth Protocol' but 'DSL beat fixes based on existing verb_interactions.beats.jso'
- sample: expected 'research per Research Depth Protocol' but 'DSL beat fixes verified against existing verb_interactions.b'
- possible_conflict_with: heuristic_29d3294b7875942a (Investigate fixes generationsubsystem; verify test harness a); H-44  (Gardener: reconcile)
- draft_rule: Investigate bridge dsl; verify test harness and beat registration.

<!-- distilled 2026-07-16T07:15:02Z -->
## H-46: human_rejection: Sky_Starfield
- status: promoted (auto 2026-07-16)
- kind: human_rejection  |  count: 1  |  last_seen: 2026-07-16T00:12:31
- proposed_organ: claude_md
- evidence: observation_408512d7f36aff6e
- sample: automated rejection sweep: simulation evidence indicts this feature (1 failing outcome(s)) in simtest_7c114b5f49f6462f
- draft_rule: Investigate human_rejection sky_starfield; verify test harness and beat registra

## H-47: human_rejection: Sky_Atmosphere_Scattering
- status: promoted (auto 2026-07-16)
- kind: human_rejection  |  count: 1  |  last_seen: 2026-07-16T00:30:28
- proposed_organ: claude_md
- evidence: observation_6df7bf32c69dc5ff
- sample: automated rejection sweep: simulation evidence indicts this feature (1 failing outcome(s)) in simtest_66602b2b8529179a
- draft_rule: Investigate human_rejection sky_atmosphere_scattering; verify test harness and b

<!-- distilled 2026-07-17T03:37:16Z -->
## H-48: human_rejection: Tool_Scanner_Model
- status: pending
- kind: human_rejection  |  count: 1  |  last_seen: 2026-07-16T15:21:04
- proposed_organ: claude_md
- evidence: observation_b1c08c983da0e237
- sample: automated rejection sweep: simulation evidence indicts this feature (1 failing outcome(s)) in simtest_df1a03ae03c7e517
- draft_rule: (agent: write ONE sentence from the evidence, <=25 words)

## H-49: human_rejection: Tool_Scanner_Material
- status: pending
- kind: human_rejection  |  count: 1  |  last_seen: 2026-07-17T01:29:07
- proposed_organ: claude_md
- evidence: observation_92639a8143037cac
- sample: automated rejection sweep: simulation evidence indicts this feature (1 failing outcome(s)) in simtest_55695e524afd4f24
- draft_rule: (agent: write ONE sentence from the evidence, <=25 words)

<!-- distilled 2026-07-17T03:38:39Z -->
## H-50: grade_CF: X
- status: pending
- kind: grade  |  count: 11  |  last_seen: 2026-07-16T20:41:02
- proposed_organ: claude_md
- evidence: professor_grade_ac905fba474a25d0, professor_grade_82edc8d7f573c657, professor_grade_b938fb4036ab29b8, professor_grade_09a3128fe31df8dd, professor_grade_ce42b26ebc8e6140, professor_grade_350c4b5e69351cc1, professor_grade_e0670fd69dcea3fd, professor_grade_e331abf160ee4053
- sample: [result-grader 40.0/100] correctness 40.0/40: 1/1 tests passed; coverage 1/1 declared criteria | stability 0.0/25: crash evidence or unknown (0/12); fps unmeasu
- sample: [result-grader 10.0/100] correctness 10.0/40: 1/1 tests passed; coverage 1/4 declared criteria | stability 0.0/25: crash evidence or unknown (0/12); fps unmeasu
- sample: [result-grader 30.0/100] correctness 30.0/40: 3/3 tests passed; coverage 3/4 declared criteria | stability 0.0/25: crash evidence or unknown (0/12); fps unmeasu
- draft_rule: (agent: write ONE sentence from the evidence, <=25 words)

## H-51: surprise: gate postflight refused shelter_habitat_materials
- status: promoted (auto 2026-07-17)
- kind: surprise  |  count: 3  |  last_seen: 2026-07-17T03:08:57
- proposed_organ: claude_md
- evidence: surprise_51840d8c049bd7db, surprise_0fbe4b443a01a026, surprise_95e75709dbfd8690
- sample: expected 'a finalized claim's why-chain reaches PHYSICS or THE HUMAN' but 'no because-edge at all — NOBODY EVER ASKED why this is verif'
- sample: expected 'the local model must LOOK at a verified feature (viewport sc' but 'no LM screenshot analysis on record this session'
- draft_rule: Implement screenshot action and state-capture in sleepwalker beat registry.

<!-- distilled 2026-07-18T03:13:54Z -->
## H-52: sim_rejection: social_trade/social_trade_npc_proximity
- status: promoted (auto 2026-07-18)
- kind: sim_rejection  |  count: 5  |  last_seen: 2026-07-18T00:38:02
- proposed_organ: claude_md
- evidence: simtest_33f305d33bb1b38d, simtest_51d4dd9d23e83dd4, simtest_ba2a6d157832970a, simtest_79842a4f344337f9, simtest_d18f9ee548524798
- sample: failed: [{"expect": {"log_contains": "[NPCTrade] Player within trade range", "note": "Social_Trade witness: NPC trade component 
- draft_rule: Verify required components and assets are spawned and registered.

## H-53: sim_rejection: social_trade/social_trade_npc_interact
- status: promoted (auto 2026-07-18)
- kind: sim_rejection  |  count: 5  |  last_seen: 2026-07-18T00:38:02
- proposed_organ: claude_md
- evidence: simtest_33f305d33bb1b38d, simtest_51d4dd9d23e83dd4, simtest_ba2a6d157832970a, simtest_79842a4f344337f9, simtest_d18f9ee548524798
- sample: failed: [{"expect": {"log_contains": "[NPCTrade] Trade interaction started", "note": "Social_Trade witness: NPC trade component 
- possible_conflict_with: H-52  (Gardener: reconcile)
- draft_rule: Verify required components and assets are spawned and registered.

<!-- distilled 2026-07-18T03:15:25Z -->
## H-54: sim_rejection: gesture_wheel/gesture_wheel_open_close
- status: promoted (auto 2026-07-18)
- kind: sim_rejection  |  count: 4  |  last_seen: 2026-07-17T14:22:44
- proposed_organ: claude_md
- evidence: simtest_b30c4432bd2ecd93, simtest_1b335e28c700cd59, simtest_79c27b8c157dad4d, simtest_457320c3449e9c1f
- sample: failed: [{"expect": {"log_contains": "[GestureWheel] OpenWheel"}, "ok": false, "note": "log_hit=False"}]
- draft_rule: Verify event logging and signal traces on success path.

## H-55: sim_rejection: gesture_wheel/gesture_wheel_commit_gesture
- status: promoted (auto 2026-07-18)
- kind: sim_rejection  |  count: 4  |  last_seen: 2026-07-17T14:22:44
- proposed_organ: claude_md
- evidence: simtest_b30c4432bd2ecd93, simtest_1b335e28c700cd59, simtest_79c27b8c157dad4d, simtest_457320c3449e9c1f
- sample: failed: [{"expect": {"log_contains": "[GestureWheel] CommitGesture"}, "ok": false, "note": "log_hit=False"}]
- possible_conflict_with: H-54  (Gardener: reconcile)
- draft_rule: Verify event logging and signal traces on success path.

<!-- distilled 2026-07-18T03:20:53Z -->
## H-56: sim_rejection: verb_interactions/verb_bend_location
- status: promoted (auto 2026-07-18)
- kind: sim_rejection  |  count: 4  |  last_seen: 2026-07-18T00:28:41
- proposed_organ: claude_md
- evidence: simtest_591e6833d4c01704, simtest_fbd1071132dfb65a, simtest_e497ac97c0583b74, simtest_16a2853df3c50be7
- sample: failed: [{"expect": {"pawn_class": "BP_Astronaut_Character_C"}, "ok": false, "note": "pawn_class=DefaultPawn"}]
- sample: failed: [{"expect": {"pawn_property_toggles": {"key": "C", "component": "CollisionCylinder", "property": "CapsuleHalfHeight", "m
- possible_conflict_with: heuristic_5031dfdbe0e5667d (Beat scripts must declare only Sleepwalker-registered action); heuristic_2dfd6804008ee83d (Beat scripts must declare only Sleepwalker-registered action); heuristic_c7175a86c82c29e9 (Position-expect beats must reset_position at beat start — W-); heuristic_1d155a205edbbd4b (Expects are schema-bound like actions — unknown expects (scr)  (Gardener: reconcile)
- draft_rule: Implement missing input bindings and verify actor registration.

## H-57: sim_rejection: verb_interactions/verb_pickup_weapon_tool_location
- status: promoted (auto 2026-07-18)
- kind: sim_rejection  |  count: 4  |  last_seen: 2026-07-18T00:28:41
- proposed_organ: claude_md
- evidence: simtest_591e6833d4c01704, simtest_fbd1071132dfb65a, simtest_e497ac97c0583b74, simtest_16a2853df3c50be7
- sample: failed: [{"expect": {"screenshot_taken": "verb_pickup_weapon_tool_view"}, "ok": false, "note": "unknown expect ['screenshot_take
- sample: failed: [{"expect": {"pawn_class": "BP_Astronaut_Character_C"}, "ok": false, "note": "pawn_class=DefaultPawn"}]
- sample: failed: [{"expect": {"log_contains": "[DEMOBEAT] Interact action triggered - picked up", "note": "Verb_PickUp witness: pickup ac
- possible_conflict_with: heuristic_5031dfdbe0e5667d (Beat scripts must declare only Sleepwalker-registered action); heuristic_2dfd6804008ee83d (Beat scripts must declare only Sleepwalker-registered action); heuristic_c7175a86c82c29e9 (Position-expect beats must reset_position at beat start — W-); heuristic_1d155a205edbbd4b (Expects are schema-bound like actions — unknown expects (scr)  (Gardener: reconcile)
- draft_rule: Verify event logging and signal traces on success path.

<!-- distilled 2026-07-18T03:25:32Z -->
## H-58: sim_rejection: verb_interactions/verb_drop_location
- status: promoted (auto 2026-07-18)
- kind: sim_rejection  |  count: 3  |  last_seen: 2026-07-18T00:28:41
- proposed_organ: claude_md
- evidence: simtest_591e6833d4c01704, simtest_fbd1071132dfb65a, simtest_16a2853df3c50be7
- sample: failed: [{"expect": {"pawn_class": "BP_Astronaut_Character_C"}, "ok": false, "note": "pawn_class=DefaultPawn"}]
- sample: blocked: [{"error": "inspect.runtime_report: failed"}]
- possible_conflict_with: heuristic_5031dfdbe0e5667d (Beat scripts must declare only Sleepwalker-registered action); heuristic_2dfd6804008ee83d (Beat scripts must declare only Sleepwalker-registered action); heuristic_c7175a86c82c29e9 (Position-expect beats must reset_position at beat start — W-); heuristic_1d155a205edbbd4b (Expects are schema-bound like actions — unknown expects (scr)  (Gardener: reconcile)
- draft_rule: Verify correct pawn class and rig bindings on initialization.

## H-59: surprise: aerisaidactor candidate expectation score
- status: pending
- kind: surprise  |  count: 4  |  last_seen: 2026-07-18T03:24:46
- proposed_organ: claude_md
- evidence: surprise_188b627fe0fafb46, surprise_14f14118b700a6ec, surprise_8b8219fa2d79c5c8, surprise_3dadbf9549ff2e3a
- sample: expected 'the player's assumed mental model for the system' but 'VIOLATE 'Players will assume they are supposed to examine or'
- sample: expected 'the player's assumed mental model for the system' but 'VIOLATE 'Players will assume the half-buried leviathan shell'
- sample: expected 'the player's assumed mental model for the system' but 'VIOLATE 'Players will assume there is an interactive termina'
- draft_rule: (agent: write ONE sentence from the evidence, <=25 words)

<!-- distilled 2026-07-18T07:15:02Z -->
## H-60: surprise: research shelter_habitat_lighting waived witness
- status: pending
- kind: surprise  |  count: 7  |  last_seen: 2026-07-18T03:37:47
- proposed_organ: claude_md
- evidence: surprise_525df411ff6355c6, surprise_ab437e4cfa7eb7f6, surprise_1294466e9aad704c, surprise_8a6188c5662a79cf, surprise_b5a537d36011f9a1, surprise_644a93ce02af1591, surprise_35c442795c19e6ba
- sample: expected 'research per Research Depth Protocol' but 'Witness task verifying existing feature — no new technical d'
- possible_conflict_with: heuristic_29d3294b7875942a (Investigate fixes generationsubsystem; verify test harness a); H-44  (Gardener: reconcile)
- draft_rule: (agent: write ONE sentence from the evidence, <=25 words)

## H-61: surprise: atom beat_scripts_tautology_fix fix red
- status: pending
- kind: surprise  |  count: 3  |  last_seen: 2026-07-17T19:16:06
- proposed_organ: claude_md
- evidence: surprise_4ed053b71dd5028c, surprise_074c4f5ce8137b19, surprise_e09b060aa7dd655a
- sample: expected 'research per Research Depth Protocol' but 'No technical research needed for this fix - it was a STALE p'
- draft_rule: (agent: write ONE sentence from the evidence, <=25 words)

<!-- distilled 2026-07-19T03:50:43Z -->
## H-62: sim_rejection: travel_vehicle_basic/vehicle_component_initialized
- status: pending
- kind: sim_rejection  |  count: 5  |  last_seen: 2026-07-18T20:28:51
- proposed_organ: claude_md
- evidence: simtest_7b4a0574d9da53d0, simtest_8c89d59be803b78e, simtest_294b7002d65b7a26, simtest_12a08e5b4755f972, simtest_549d2c42e57f4a6e
- sample: failed: [{"expect": {"actor_exists": "AShip_Trader_Vessel_Alpha"}, "ok": false, "note": "present=False"}]
- sample: blocked: [{"error": "RIG FAULT (tb-0184, not a feature defect): reset_position wrote z=130 but pawn now reads z=3130 (delta=+3000
- draft_rule: (agent: write ONE sentence from the evidence, <=25 words)

## H-63: sim_rejection: solar_system_stand/stand_on_grown_ocean_world
- status: pending
- kind: sim_rejection  |  count: 4  |  last_seen: 2026-07-18T22:45:01
- proposed_organ: claude_md
- evidence: simtest_579122ea55c61beb, simtest_42f9f67531bcb374, simtest_140a70674941d472, simtest_ae7dc6dd3cca28a9
- sample: blocked: [{"error": "RIG FAULT (tb-0184, not a feature defect): reset_position wrote z=130 but pawn now reads z=3630 (delta=+3500
- sample: blocked: [{"error": "RIG FAULT (tb-0184, not a feature defect): reset_position wrote z=130 but pawn now reads z=3085 (delta=+2955
- sample: blocked: [{"error": "RIG FAULT (tb-0184, not a feature defect): reset_position wrote z=130 but pawn now reads z=3130 (delta=+3000
- draft_rule: (agent: write ONE sentence from the evidence, <=25 words)

<!-- distilled 2026-07-20T03:51:55Z -->
## H-64: surprise: dyad result turn
- status: pending
- kind: surprise  |  count: 12  |  last_seen: 2026-07-19T10:19:10
- proposed_organ: claude_md
- evidence: surprise_bb04ffd93eadb5b0, surprise_50aa93e241e92881, surprise_743f29b584411eea, surprise_b98b3f6e530ffac8, surprise_61b630f8e526afb3, surprise_8f32ce33f19809ef, surprise_d76ed429f8dc58e4, surprise_95db455df6642c79
- sample: expected 'the dyad's instruction was executed' but 'Tool_Scanner does not exist as a concrete feature. The brief'
- sample: expected 'the dyad's instruction was executed' but 'Fractal zoom sweep test built and executed on a 157K-splat g'
- sample: expected 'the dyad's instruction was executed' but 'Spatial LOD merger built and tested. Results on 157K-splat l'
- draft_rule: (agent: write ONE sentence from the evidence, <=25 words)

<!-- distilled 2026-07-20T22:07:21Z -->
## H-65: sim_rejection: chimera_complete/generation_transition
- status: promoted (auto 2026-07-20)
- kind: sim_rejection  |  count: 3  |  last_seen: 2026-07-20T20:39:53
- proposed_organ: claude_md
- evidence: simtest_9d46c02be04fed93, simtest_7e4fff8702385eef, simtest_dd356f6bd6db7922
- sample: failed: [{"expect": {"log_contains": "Generation"}, "ok": false, "note": "log_hit=False"}]
- draft_rule: Verify event logging and signal traces on success path.

<!-- distilled 2026-07-21T03:15:33Z -->
## H-66: sim_rejection: edu_spawn/collect_basalt
- status: promoted (auto 2026-07-22)
- kind: sim_rejection  |  count: 6  |  last_seen: 2026-07-20T23:20:27
- proposed_organ: claude_md
- evidence: simtest_05a96cc543e6043a, simtest_c139965ec7ef5bb6, simtest_b1ae25ecb20b0b9c, simtest_1b320af1b5dbdea7, simtest_389e4bb9d076f794, simtest_cbda9590f7c48bb3
- sample: failed: [{"expect": {"log_contains": "LEARN"}, "ok": false, "note": "log_hit=False"}]
- sample: blocked: [{"error": "inspect.runtime_report: failed"}]
- draft_rule: Verify event logging and signal traces on success path.

## H-67: surprise: beat collect_basalt discovered edu_spawn
- status: promoted (auto 2026-07-22)
- kind: surprise  |  count: 6  |  last_seen: 2026-07-20T23:20:27
- proposed_organ: claude_md
- evidence: surprise_cc736cb01c0f6d7e, surprise_88c4b8cbabfde265, surprise_6e6a54a107c68d50, surprise_00176d3091bb0704, surprise_90801c95182e56ba, surprise_43d31a5704136b1b
- sample: expected '' but 'failed: {"expect": {"log_contains": "LEARN"}, "ok": false, "'
- sample: expected '' but 'blocked: {"error": "inspect.runtime_report: failed"}'
- possible_conflict_with: heuristic_393319affe39ee06 (Investigate correction feature; verify test harness and beat); heuristic_c4ab980eb2ceee7d (Investigate actors bp_verb_; verify test harness and beat re); heuristic_96e67135d9845f6a (Investigate bad costless; verify test harness and beat regis); heuristic_009462cbb6e7e534 (Investigate blocker draft; verify test harness and beat regi)  (Gardener: reconcile)
- draft_rule: Verify event logging and signal traces on success path.

<!-- distilled 2026-07-21T07:15:01Z -->
## H-68: sim_rejection: regolith_yard/spawn_on_metal_pad
- status: promoted (auto 2026-07-22)
- kind: sim_rejection  |  count: 3  |  last_seen: 2026-07-21T06:00:16
- proposed_organ: claude_md
- evidence: simtest_9cd9a1ac25867a73, simtest_b9c246f4cef92293, simtest_26952ede18597de8
- sample: failed: [{"expect": {"pawn_within": {"x": 0, "y": 0, "r": 600}}, "ok": false, "note": "dist=3225uu (loc x=3200, y=400)"}]
- sample: failed: [{"expect": {"pawn_within": {"x": 0, "y": 0, "r": 600}}, "ok": false, "note": "dist=1414213562uu (loc x=None, y=None)"}]
- possible_conflict_with: heuristic_52e2728aa88ab00a (Probe jumps by timed pawn_z read-back, not log_contains — an); heuristic_66e973934c7b5322 (Compound beats fail for shifting root causes (frozen input, ); heuristic_040256f8f18a3de0 (Verify beat spawn location distances and pawn navigation con); H-28  (Gardener: reconcile)
- draft_rule: Verify beat spawn location distances and pawn navigation constraints.

<!-- distilled 2026-07-24T04:51:30Z -->
## H-69: human_rejection: Tool_Weapon_Model
- status: pending
- kind: human_rejection  |  count: 1  |  last_seen: 2026-07-08T00:26:29
- proposed_organ: claude_md
- evidence: observation_af7f40abe37d1f59
- sample: automated rejection sweep: simulation evidence indicts this feature (2 failing outcome(s)) in simtest_fbd1071132dfb65a
- draft_rule: (agent: write ONE sentence from the evidence, <=25 words)

## H-70: human_rejection: Ground_Sand_Particles
- status: pending
- kind: human_rejection  |  count: 1  |  last_seen: 2026-07-08T04:18:59
- proposed_organ: claude_md
- evidence: observation_c1eb6cfb82d8fc19
- sample: Reopening the 2026-07-07T06:46:59 observed_provisional acceptance (simtest_0dec5fc92db45fee, 4 clean sessions). Mixed signal: walk_rock_to_sand_basin (the more 
- draft_rule: (agent: write ONE sentence from the evidence, <=25 words)

<!-- distilled 2026-07-24T07:15:02Z -->
## H-71: human_rejection: Ground_Sand_Footprints
- status: pending
- kind: human_rejection  |  count: 1  |  last_seen: 2026-07-08T20:28:14
- proposed_organ: claude_md
- evidence: observation_e0159ce465c0a841
- sample: Sleepwalk ground_sand_footprints_verify: beat walk_rock_to_sand_basin reached successfully (player walked from spawn to sand basin over ~2.6s). Visual inspectio
- draft_rule: (agent: write ONE sentence from the evidence, <=25 words)

## H-72: human_rejection: visual_validation_phenotypic_analysis
- status: pending
- kind: human_rejection  |  count: 1  |  last_seen: 2026-07-23T20:12:48
- proposed_organ: claude_md
- evidence: observation_3a35d3db21c10a8a
- sample: High clamping detected, color distribution too uniform. Pass rate: 0.0%
- draft_rule: (agent: write ONE sentence from the evidence, <=25 words)

<!-- distilled 2026-07-25T07:15:02Z -->
## H-73: human_rejection: recombination_genetic_inheritance
- status: pending
- kind: human_rejection  |  count: 1  |  last_seen: 2026-07-23T20:13:24
- proposed_organ: claude_md
- evidence: observation_8a8bfdb0aa23971b
- sample: Values between parents: False for all tested recombinations. Success rate: 40.0%
- draft_rule: (agent: write ONE sentence from the evidence, <=25 words)

<!-- distilled 2026-08-11T07:15:02Z -->
## H-74: surprise: atom atom_6fca5cb0478c commit fix
- status: pending
- kind: surprise  |  count: 3  |  last_seen: 2026-08-10T07:15:57
- proposed_organ: claude_md
- evidence: surprise_e27259a1e48e0170, surprise_1d9edc17625ec504, surprise_c80324215ef941b5
- sample: expected 'the atom's constraint would keep holding' but 'bloodhound bisect names the commit: a8106d4 the wave: seven '
- sample: expected 'the atom's constraint would keep holding' but 'bloodhound bisect names the commit: e5872c1 PHASE A DONE: 12'
- sample: expected 'the atom's constraint would keep holding' but 'bloodhound bisect names the commit: 96f2bbe VERDICTs 14-23: '
- possible_conflict_with: H-61  (Gardener: reconcile)
- draft_rule: (agent: write ONE sentence from the evidence, <=25 words)

<!-- distilled 2026-08-22T07:15:01Z -->
## H-75: sim_rejection: regolith_yard/sand_basin_dwell_and_frame
- status: pending
- kind: sim_rejection  |  count: 3  |  last_seen: 2026-08-22T06:00:37
- proposed_organ: claude_md
- evidence: simtest_26952ede18597de8, simtest_1d75735165b76345, simtest_0b481b2537770a60
- sample: blocked: [{"error": "reset_position failed: no possessed pawn found in runtime_report"}]
- sample: blocked: [{"error": "inspect.runtime_report: failed"}]
- sample: failed: [{"expect": {"is_pie": true}, "ok": true, "note": "isPIE=True"}]
- possible_conflict_with: heuristic_52e2728aa88ab00a (Probe jumps by timed pawn_z read-back, not log_contains — an); heuristic_66e973934c7b5322 (Compound beats fail for shifting root causes (frozen input, ); heuristic_040256f8f18a3de0 (Verify beat spawn location distances and pawn navigation con); heuristic_fd052ff001f27417 (Verify beat spawn location distances and pawn navigation con)  (Gardener: reconcile)
- draft_rule: (agent: write ONE sentence from the evidence, <=25 words)
