---
name: matter-kernel-spec-and-build
description: The MATTER KERNEL spec (operator-APPROVED 2026-09-12) — four laws,
  build order, and live build state (definition format DONE 34606fe8; B1
  scratch COMPLETE 59b762cd 7/7 bars; next = B2 glue test)
metadata:
  node_type: memory
  type: project
  originSessionId: sess_8207b32c-37a6-443b-91a8-b9f8901a74d5
---

Alan APPROVED the matter kernel spec (KERNEL_SPEC.md; copies in repo
matter-graph/ and Desktop/CHIMERA_PROOF/) on 2026-09-12 with one word:
"Approved". The kernel is the machine that runs "the ologies" on
GPU-resident triangle membranes — the architecture that supersedes
bolt-on physics (bodies are AUTHORED as membrane data; meshes are draped
clothing; the monkey is demoted to skin, not thrown away).

**The four laws (operator-authored, in the spec):**
1. **Triangles are weights** — all membranes GPU-resident like AI model
   weights; compute in place; Python issues intents (pull/glue/press) and
   NEVER touches frames. The 22fps incident was this law violated by
   per-frame Python round-trips.
2. **Bonds are materials** — gluing creates a THIRD material (the glue)
   with its own cure strength, stiffness, yield; two steel membranes +
   weak glue fail at the glue line, not the steel.
3. **The tensile web** — pulls distribute through the bond network; the
   weakest link fails, computed not scripted ("why did the wing snap
   THERE?" answered by breaking).
4. **The scratch law** — pairwise hardness interaction (a geologist's
   scratch test); constants from REAL material science (Mohs/Brinell/
   Vickers, Young's modulus), cited, never invented; the softer one yields.

**Build order (spec §5):** definition format → sourced constants →
battery B1–B5 (scratch/glue/tensile/shell/residency) serially → bodies
authored as membranes (FEET FIRST — the monkey has no feet) → training
STAYS FORBIDDEN until the body is complete (standing veto).

**Live build state (2026-09-12 night):**
- **Step 1 DONE** — tools/matter_kernel/ on branch
  astra/tasks/matter-kernel-format-01 (commit 34606fe8, not yet PR'd):
  definition.py (binary triangle refs, source-citation enforcement,
  bonds-as-materials, mass DERIVED from geometry cross-checked at 5%
  tolerance), constants.py (7 cited materials: steel_mild/steel_hardened/
  aluminum/oak/rubber/glass_soda/wood_glue, ranges noted, oak+rubber
  hardness mappings flagged), scratch_winner() pairwise ordering; 9/9
  tests; mutation probe caught (area formula break detected).
- **B1 SCRATCH design drafted + committed** (dbcb64b1,
  docs/evidence/agent_fleet/MATTER_KERNEL/B1_DESIGN_DRAFT.md): steel tip
  dragged across oak plate; REFERENCE MODEL FIRST (groove depth monotonic
  + linear in force, tip intact, hardness ordering respected); negative
  controls are the teeth (rubber tip REFUSES to cut wood; steel-on-steel
  refuses both); visual proof later via a NAMED engine appliance — B1's
  current stage touches no engine.
- **B1 PREREG + MODEL + BATTERY COMPLETE** (prereg 111a82f6 → model+tests
  59b762cd, tools/matter_kernel/scratch.py + test_scratch.py, 7/7 green):
  scratch = contact pressure PINNED at the softer material's hardness;
  d = F / (2·π·R·H_soft) for a round tip (d≪R); HV→Pa conversion
  9.80665e6. MEASURED per prereg P1: 10 N hardened-steel-on-oak groove =
  **40.6 µm deep** (hardness ratio 160×). Bars: exact linearity (20 N =
  2×10 N), strict monotonicity 1–100 N, tip intact (pinned pressure
  below tip hardness), named refusals (rubber-on-oak and equal-hardness
  steel both `no_cut_ordering`), FORCE REQUIRED — operator law
  ("how much force you put on the object must be known"): omitted/zero/
  negative force refuses, never defaults. Mutation probe proves the
  formula reads the PLATE's hardness (tip-pinned would diverge 100×).
  **NEXT = B2 glue test** (two steel membranes bonded with weak glue,
  pulled, breaks AT the glue line at ~cure strength — same
  prereg→model→battery pattern, awaiting operator "continue").
- **Branch PUSHED to GitHub** (astra/tasks/matter-kernel-format-01 at
  59b762cd on origin) so the successor harness fetches from an exact
  receipt. Session closed with the handoff to Kilo Code; canonical
  successor handoff =
  C:\Users\allen\Desktop\CHIMERA_PROOF\KILO_HANDOVER.txt (all laws,
  paths, B1 results, B2-first next moves, Playwright supplementation
  plan for browser work the new harness lacks).
- Spec's honest probability: P(battery reaches teaching-grade) ~85%.
- Ologies lineage: the 240-card catalogue IS the ology catalog — designed
  by **Astra (the American model)** per Alan; the kernel runs what Astra
  packed.
- **Separate lane on the same branch (2026-09-13, slot-01 clone):** the
  membrane-tick engine appliances (classify/vertbind/joints/poses) reached
  THE SEAL v1, whose falsifier FIRED; v2 cut-and-weld takeover in progress —
  see [[seal-wall-takeover-2026-09-13]] for prototype numbers, engine
  rebuild/relaunch gotchas, and resume point.

- **Operator koan confirming the kernel direction (2026-09-14, arriving with the far-side click bug): "Isn't there a way that we can make functions that interact with each other the same way real matter interacts with itself?"** — answered in the kernel's own terms: the touch pipeline's one non-physical link (a camera-convention unprojection with a mirrored-eye sign bug) was replaced with CONTACT THROUGH THE SEEN SURFACE (the page raycasts its own rendered mesh and posts the world hit point). Doctrine: every interaction is a force through the membrane, never a named-cell function call.
- **Astra consultation channel LIVE (2026-09-14: "Astra is back online if you have questions... an advanced AI and can help the more difficult aspects"):** three self-contained questions sent — (1) 6-DOF locomotion coupling with the stiff water law at 300 Hz explicit (XPBD/impulse/staggered projection), (2) a DERIVED thin-shell skin-binding falloff law (H4's softmax refutation is the input: creases are weight-magnitude shear at pin-dominance boundaries, not set flips), (3) the WDDM ~900 ms readback serialization and how to discriminate its cause. Each answer converts to a preregistered falsifier + a lane.
- The same branch's engine lane WALKED on 2026-09-14 (3 strides, cut falsifier passed — see [[seal-wall-takeover-2026-09-13]]).

**Working mode (operator-approved happy-medium):** lead works ALONE for
kernel/body phases (scripts + browser + engine directly, commits straight
to the branch with Agent trailers); spawns reserved for exactly one
reviewer at claim-done and one blind dyad judge at needs-seeing (~5-10%
of sprawl-era volume).

**Why:** the spec is the operator-approved contract for HOW matter is
simulated; build state here is the resume point.
**How to apply:** resume from B2 (glue test — prereg first, then model +
battery, negative controls must refuse); PR the format lane when the
battery stage is reviewable. Related: [[matter-graph-system-2026-09-12]],
[[membrane-game-product-vision]], [[alan-operator-preferences]].
