# PENDING HEURISTICS — the Gardener's queue

Candidates distilled from repeated failures/surprises in the DNA graph.
The human approves or vetoes each: edit `status:` to `approved` or `vetoed`.
On approval the agent promotes to the named organ and records it via
`python -m core.graphify_record heuristic ...`, then sets status `promoted`.
NOTHING here is active until promoted.


<!-- distilled 2026-07-06T15:32:20Z -->
## H-1: compilation_fail
- status: pending
- kind: failure  |  count: 60  |  last_seen: 2026-07-06T07:36:10
- proposed_organ: gate
- evidence: mutation_53730a2744e1, mutation_5bb42aaba4c8, mutation_de53b37d8a1f, mutation_e29ea9edacfe, mutation_14a347b241fc, mutation_8c5a4195d2b4, mutation_68c61ac2b981, mutation_9cd27cf80996
- sample: compilation_fail
- sample: E:\PythonChimera\Chimera\Source\Chimera\ProceduralGenerated\Tests\ChimeraDSLTests.cpp(52,53): error C2039: 'GetCurrentFuelLiters': is not a member of 'UFlightCo
- sample: error C2039: not a member
- draft_rule: A C2039 missing-member error in ProceduralGenerated/ means template drift — emit the accessor in the same generator change that emits its test.
- agent_note: gate_build_succeeded already BLOCKS on these; this rule is the preventive half (fix at generator, same change). Approve as claude_md rule, or veto as sufficiently covered by the existing gate.

## H-2: grade_CF: Visual_Verification
- status: pending
- kind: grade  |  count: 41  |  last_seen: 2026-07-06T02:51:08
- proposed_organ: claude_md
- evidence: professor_grade_d543406104bab7ca, professor_grade_4b3ac1a8094ad245, professor_grade_5c4febabf91f23f0, professor_grade_caf6e3de66d62355, professor_grade_146029f24a743a1c, professor_grade_7a0262bc83441f63, professor_grade_978b8c378d8792a9, professor_grade_2a89a1885ad991df
- sample: Visual verification returned aborted_wrong_window: Foreground window was 'PythonChimera – README.md'
- sample: Visual verification returned incomplete: Screenshot aborted: Unreal Editor was not the foreground window
- sample: Visual verification returned aborted_wrong_window: Foreground window was 'Claude'
- draft_rule: Never verify from desktop screenshots — capture via MCP control_editor screenshot mode=editor_viewport, which renders the viewport regardless of window focus.
- agent_note: 41 wasted verification cycles from window-focus roulette (pyautogui desktop capture). The MCP pathway exists but the PROHIBITION was never constitutional. Recommend APPROVE -> claude_md. H-4/H-5/H-6 are facets of this same era; consider approving this one and vetoing those as subsumed.

## H-3: verification_not_verified
- status: pending
- kind: failure  |  count: 25  |  last_seen: 2026-07-06T04:49:48
- proposed_organ: claude_md
- evidence: vis_verify_92dc19c53dee1fce, vis_verify_14a9670662e49822, vis_verify_4bbddd832cfdc342, vis_verify_3c1cb72d235b1348, vis_verify_b7d7dde641bafaf1, vis_verify_ab68e97ab2ffc2c8, vis_verify_55ea97d9592750a9, vis_verify_c9087d54692aafbc
- sample: Visual verification: Ground_Metal_Surface → not_verified. {"verified": false, "what_you_see": "The user wants me to act as a visual verification analyst for the
- sample: Visual verification: Ground_Metal_Surface → not_verified. {"verified": false, "what_you_see": "Here's a thinking process:\n\n1.  **Understand User Input:**\n   
- sample: Visual verification: Ground_Sand_Surface → not_verified. {"verified": false, "what_you_see": "Here's a thinking process:\n\n1.  **Understand User Input:**\n   -
- draft_rule: An LM response containing its own reasoning dump ("Here's a thinking process") is a RETRY with a larger token budget, never a verdict — schema-validate before consuming.
- agent_note: 25 false not_verified verdicts because the local model's meta-output was parsed as the answer. Same failure hit THIS session (empty vision verdicts until max_tokens raised 80->1200). Recommend APPROVE -> claude_md; applies to all remaining LM layers (vision is tertiary evidence now).

## H-4: verification_aborted_wrong_window
- status: pending
- kind: failure  |  count: 21  |  last_seen: 2026-07-06T01:01:53
- proposed_organ: mcp_pathways
- evidence: mutation_04bdae683780, mutation_2e94b4f36b73, mutation_84b13589f1b4, mutation_7b2e8cdb643b, mutation_471ed34dd599, mutation_06ee05b777cb, mutation_bd7985b2897a, mutation_bb367018ee94
- sample: Visual verification aborted_wrong_window: AI analysis completed
- draft_rule: (subsumed by H-2 — same window-focus lesson, abort-marker facet)
- agent_note: Recommend VETO as duplicate-of-H-2; this entry stays here as a suppression tombstone so the signature is never re-proposed.

## H-5: verification_fail
- status: pending
- kind: failure  |  count: 20  |  last_seen: 2026-07-05T06:13:09
- proposed_organ: claude_md
- evidence: mutation_5e647acb4c73, mutation_50043ecc32cb, mutation_29c6952a0461, mutation_c04ecc1695bb, mutation_ffafe42c9fb1, mutation_d4c975ea0395, mutation_ac1291294589, mutation_93f9998f0246
- sample: Visual verification fail: AI analysis completed
- draft_rule: (subsumed by H-2/H-3 — generic fail marker from the same desktop-capture + unparsed-LM era)
- agent_note: Recommend VETO as subsumed; tombstone prevents re-proposal.

## H-6: verification_incomplete
- status: pending
- kind: failure  |  count: 19  |  last_seen: 2026-07-06T02:51:08
- proposed_organ: claude_md
- evidence: mutation_da18bce08a2d, mutation_29db1adf57a9, mutation_ef4fa0a4c278, mutation_a9ff385f3008, mutation_35355fd5287f, mutation_163787d7e922, mutation_4ee700064f51, mutation_da563159cf38
- sample: Visual verification incomplete: AI analysis completed
- draft_rule: (subsumed by H-2/H-3 — incomplete marker from the same era)
- agent_note: Recommend VETO as subsumed; tombstone prevents re-proposal.

<!-- distilled 2026-07-06T15:40:55Z -->
## H-7: ralph_apply_<feature>_step
- status: pending
- kind: failure  |  count: 18  |  last_seen: 2026-07-06T04:41:13
- proposed_organ: claude_md
- evidence: mutation_77ea6ac769eb79e4, mutation_fff72331841ce16c, mutation_88ffc7f7d2acfa55, mutation_4ce2fdea764203a0, mutation_d330ae3f9571ef7e, mutation_eb7afcc8d7eeeea7, mutation_dc815743abb2e926, mutation_363c59e1ae09acbf
- sample: RalphLoop: apply_Player_Character_Model_step1 → failed. {"message": "[DynamicToolManager] Initialized with 22 tools across 4 categories\n[UE-MCP] UE_PROJECT_PAT
- sample: RalphLoop: apply_Player_Character_Suit_step1 → failed. {"message": "[DynamicToolManager] Initialized with 22 tools across 4 categories\n[UE-MCP] UE_PROJECT_PATH
- sample: RalphLoop: apply_Player_Character_Lighting_step1 -> failed. {"message": "[DynamicToolManager] Initialized with 22 tools across 4 categories\n[UE-MCP] UE_PROJECT
- draft_rule: Record the MCP response's error field, never raw CLI stdout — a DynamicToolManager boot banner inside an "error" means the wrong stream was captured.
- agent_note: 18 apply-step failures whose recorded "error" is the CLI's startup spam; the true failure was lost, making the failures untriageable later. Recommend APPROVE -> claude_md (observability rule for all MCP-calling code).

## H-8: grade_CF: Player_Character_Lighting
- status: pending
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
- status: pending
- kind: failure  |  count: 12  |  last_seen: 2026-07-04T05:35:13
- proposed_organ: claude_md
- evidence: mutation_7ecfb3f135b7ae18, mutation_550c879fe28b4124, mutation_ff729ef0505792cc, mutation_a5cc94c1b1df7f6d, mutation_54db1006d3560a99, mutation_b88e4aa5d3be8b28, mutation_43b4754d74ead0ff, mutation_8af106100d89ceb8
- sample: RalphLoop: ralph_loop_complete_Player_Character_Lighting -> incomplete. {"feature": "Player_Character_Lighting", "loop": 0, "status": "needs_refinement", "verif
- draft_rule: Twelve incomplete loop endings for one feature is retry churn without a targeted study guide — every re-research prompt must quote the grader's lowest categories.
- agent_note: Recommend VETO as superseded — the result-grader redesign already generates study guides on C/F and the H-8 root cause (LM meta-dump grades) drove the churn. Tombstone prevents re-proposal.

## H-10: pathway: build_orchestrator.ue_shutdown -> killed_for_build
- status: pending
- kind: pathway  |  count: 12  |  last_seen: 2026-07-06T04:02:31
- proposed_organ: mcp_pathways
- evidence: pathway_attempt_3e517c048179cfdd, pathway_attempt_3d5996596d09f1f7, pathway_attempt_9f39685541ef77e3, pathway_attempt_3574744951ff40af, pathway_attempt_e8985cac48e6c15d, pathway_attempt_921e5813592aa091, pathway_attempt_ee865905242c80ff, pathway_attempt_cf31600eb01f0688
- sample: Pathway attempt recorded: tool 'build_orchestrator', action 'ue_shutdown', result 'killed_for_build'
- draft_rule: killed_for_build is the build lifecycle working as designed, not a pathway failure — record intended shutdowns as success with a note, or routine builds pollute the failure ledger.
- agent_note: 12 routine pre-build UE shutdowns mis-recorded as failed pathways (they cluster as failures forever). Recommend APPROVE -> claude_md + the concrete fix: build_orchestrator's record call should pass result='success' for intended kills. The distiller itself flagged its own noise source here.

<!-- distilled 2026-07-06T18:34:16Z -->
## H-11: ralph_ralph_loop_complete_Player_Character_Model
- status: pending
- kind: failure  |  count: 12  |  last_seen: 2026-07-06T04:49:48
- proposed_organ: claude_md
- evidence: mutation_28c2cd27ce30a284, mutation_0b49ebfeb34e12e4, mutation_4dff0fabb310dec5, mutation_55aaeca6facbc536, mutation_cb0f8548a01157e2, mutation_a75a79da8dd27502, mutation_dd8771a50908e4d5, mutation_71aaaea24b2aff0d
- sample: RalphLoop: ralph_loop_complete_Player_Character_Model → incomplete. {"feature": "Player_Character_Model", "loop": 0, "status": "needs_refinement", "verified": f
- sample: RalphLoop: ralph_loop_complete_Player_Character_Model -> incomplete. {"feature": "Player_Character_Model", "loop": 0, "status": "needs_refinement", "verified": 
- draft_rule: (same lesson as H-9: incomplete-loop churn from the pre-result-grader era; the feature was later verified A 98.8 under the new regime)
- agent_note: Recommend VETO as superseded — same era and root cause as H-9; tombstone prevents re-proposal.

## H-12: grade_CF: Build_Pipeline
- status: pending
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
- status: pending
- kind: grade  |  count: 3  |  last_seen: 2026-07-06T06:58:24
- proposed_organ: claude_md
- evidence: professor_grade_7886af92f495ccd1, professor_grade_364a07e3116f20a6, professor_grade_bf25d5d3a1fc673f
- sample: Professor review: Price bounds D, Fluctuation F (needs mean reversion), Station spread A. Overall C pending adjustments.
- sample: [result-grader 52.8/100] correctness 13.3/40: 1/1 tests passed; coverage 1/3 declared criteria | stability 15.0/25: crash-free; fps unmeasured (0/5); growth unm
- sample: [result-grader 59.5/100] correctness 20.0/40: 2/2 tests passed; coverage 2/4 declared criteria | stability 15.0/25: crash-free; fps unmeasured (0/5); growth unm
- draft_rule: Economy features repeatedly grade C/F on partial criteria coverage and unmeasured fps; run telemetry foregrounded and test every declared criterion before grading System_Economy.

<!-- distilled 2026-07-07T00:17:27Z -->
## H-14: human_rejection: Verb_Step
- status: pending
- kind: human_rejection  |  count: 1  |  last_seen: 2026-07-07T00:07:52
- proposed_organ: claude_md
- evidence: observation_f629252c5bdbcd07
- sample: I have no ability to move my character
- draft_rule: (agent: write ONE sentence from the evidence, <=25 words)
