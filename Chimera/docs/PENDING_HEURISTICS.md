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
