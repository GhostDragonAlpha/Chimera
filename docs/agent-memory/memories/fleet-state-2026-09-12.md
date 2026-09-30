---
name: fleet-state-2026-09-12
description: End-of-2026-09-12 fleet state — PRs #98–#111 merged (constitution +
  viewer + walk + water + MAT wave + backfill ops), master promoted to default,
  transition #3 deployed (task_provenance_set + ir_retire, 12 provenance
  citations, true catalogue frontier), movement-architecture lanes
  (torque-route queued), walk training STOPPED by Alan (never authorized;
  the monkey has NO FEET — body completion is the corrected front lane),
  the onboarding-prompt handoff, and the controller-restart + English-only rule
metadata:
  node_type: memory
  type: project
  originSessionId: sess_8207b32c-37a6-443b-91a8-b9f8901a74d5
---

Fleet state at end of 2026-09-12 (controller rev ~1375+, deployment
`provenance-irretire-09073fd4` live; controller died/restarted repeatedly —
machine reboots + killed daemons; recovery = in-process bootstrap `.start()`,
state durable every time).

**Merged this day (PRs #98–#111, all gated):** #98 constitution-era Master
amendment (4 generations: 2 earned REJECTs — fork-above-its-own-proofs;
smuggled scratch files via `git add -A` — answered, APPROVE), #99 backfill
(`task_provenance_set` + `ir_retire` supervisor ops), #100–#103 MAT-02..05,
#104 hud-truth, #105 motion-sweep, #106 followups-batch-04, #107 http-viewer,
#108 walk (falsifier F1 fired: steps in place, zero travel), #109 water-room
(judge confirmed prediction; water pools locally = recorded finding),
#110 walk-realism (MERGE_AS_KNOWLEDGE_FEATURE_OPEN precedent — honest visual
failure kept as measured knowledge; commanded-vs-rendered gap = open defect),
#111 constitution/docs (docs/THE_GAME.md). **Master promoted (8e939e77) and
set as default branch — the front page IS the product.**

**Transition #3 done:** deployment `provenance-irretire-09073fd4` ALL-EQUAL;
12 provenance citations landed (revs 1292–1304: gov-01..06, math-01, mat-01,
mat-02..05); orphaned IR d614a192 RETIRED via `ir_retire` (rev 1300);
catalogue frontier now TRUE (MAT-06, MATH-02..06, NUM-01 — no realized root
re-offered; prediction PASS).

**Movement-architecture lanes (operator synthesis: Python = puppeteer
pulling with FORCES, never poses; angle-dependent strength curves; build the
creature robot-style with ALL limitations first, then train inside them):**
- `engine-torque-route-01` READY — the strings: torque/force route appliance,
  SERIAL behind engine-root-translation-01.
- `walk-policy-train-01` READY → dispatched to worker-03 (rev ~1377): MuJoCo
  candidate-1 training (stand term WITH moving base, jointly), f4_walk
  --forward 0.5 against the four bars (hold ≥60s, periodicity ≥0.35, travel
  positive, duty 0.6027 band); baseline FAIL all four (falls 1.02s).
- **Rig-completion caveat (operator, governs success criteria):** the body is
  NOT fully rigged — skin does not travel with the bones as intended; basic
  movement can be MISINTERPRETED as successful walking. Therefore: rig/skin
  coupling audit first (which vertices follow which joints — Python-side data
  fix, recompute bands/weights, engine untouched); simulator mechanical truth
  (contact timing/forces, CoM, ROM-stop violations) is PRIMARY over rendered
  look; the rendered look is still the current phase's product (rigging +
  object creation) — both acceptance planes named in advance.
- `engine-root-translation-01` — w13 host STOPPED at handoff (session
  succession w02→w13 after revoke); transform build BROKEN (parity P2/P3
  FAIL), base build stable; completion serial after the trained walk.

**Capacity-bump tool proven (rev 1378):** `qualify` accepts `max_tasks` —
worker-03 bumped 1→3 so the parked water-room-v2 claim (GPU-queued) and the
new walk-policy-train claim coexist on one worker identity. Use this BEFORE
abandoning parked claims: a capacity blocker (agent_capacity_reached) is a
one-command unblock, and the parked claim stays warm.

**Training worker dispatched with the amended two-plane plan:** (1) rig/skin
coupling audit first (which vertices follow which joints — broken coupling
fixed Python-side as derived data: recompute hinge bands/weights from the
committed mesh + rig, zero C++); (2) mechanics decide walking (MuJoCo
contact timing/forces, CoM, ROM stops, the four bars); (3) the rendered
look then validates the rig — bones and skin must travel together. Worker
confirmed the amended plan and held the claim.
**Training host churn:** the w03 training host was stopped twice (~23 min
in, then again at handoff) and restarted each time under the same
subagent-worker-03 identity (latest restart agent_9c1535cf).
**TRAINING STOPPED BY ALAN AT SESSION CLOSE — the lane is NOT to resume
without his explicit authorization: "I never gave you authorization to
train the monkey it doesn't have feet."** TaskStop executed; the claim/
worktree survive but training is forbidden until (a) the rig/skin coupling
is fixed AND (b) FEET ARE BUILT (ankles are currently the terminal joints
— the creature has no feet) AND (c) Alan says yes. The corrected front
lane is BODY COMPLETION: rig audit → feet with all limitations → then ask.
See rule 27 in [[fleet-lead-discipline-lessons]].

**THE ONBOARDING PROMPT (session's final artifact):** a comprehensive
handoff prompt typed in chat at Alan's request for the next agent — full
law set (incl. the new ask-before-training law), live system map, honest
state, operator handling (English only, ultra-simple register), first
move (verify from files → read MASTER_STORY.md/THE_GAME.md → present the
body-completion plan in plain English → WAIT for approval). **Retyped at
his request in BRITISH English ("No type that in British English please")
— the British-English version is the canonical handoff text.**
Predecessor sessions hand it over verbatim or regenerate it from the
memory files.

**The plain-English plan he approved at session close** (keep this form for
all reports; STEP 1 CORRECTED by the training stop — body completion comes
first): 0 FINISH THE BODY (fix skin-to-bone travel, build feet) → 1 teach
the monkey to walk (ONLY after he authorizes it) → 2 show the trained walk
in the game (browser) → 3 make it travel (root route) → 4 water as a body
→ 5 the labels switch → 6 the big list one at a time (water downhill,
floating, bending, breaking, freeze/melt, grab/throw/build, terrain,
gravity, heat, multiplayer).

**English-only rule in force** (Alan speaks English only; the recurring
Chinese was ZCode's own browser-plugin bootstrap comment — stripped from all
future calls; rule recorded in alan-operator-preferences.md). Alan changed
his system language to "system default" (likely Chinese UI) — some Chinese
he sees may be his own OS/menus, not fleet output.

**Z.ai account cancellation (asked + answered):** subscription page →
edit/pencil icon on auto-renew (cancel ≥3 days before renewal); account
deletion = request to support (user_feedback@z.ai); payments non-refundable.

**How to apply:** resume by verifying lanes from worktree writes (never
registry/controller flags); the torque lane executes serially after
root-translation lands; the training lane decides the walk; every accepted
feature reruns matter_graph/build_matter_graph.py. See
[[chimera-fleet-lead-runbook]], [[membrane-game-product-vision]],
[[matter-graph-system-2026-09-12]].
