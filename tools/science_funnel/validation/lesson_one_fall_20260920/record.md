# RULE 0 PREREGISTRATION — LESSON ONE: "THE FALL" (lane lesson-one-fall-20260920)

Agent: lesson · Base: 2c7f9b08 (origin/master tip, INTEGRATION PASS 6) · Worktree: E:/ChimeraWork/buffy-lesson-agent
Committed BEFORE any lane code (this commit).

## STATEMENT

The real CT-derived body's fall — the engine's own root law, already measured
by the realbody-movie lane (peak 0.9009 m, max |vy| 3.6792 m/s, landed
0.1247 m at the derived attractor) — can be LESSON ONE: the player triggers
the fall with ONE key, watches it live, and the physics that moves the body
SURFACES as on-screen visible elements fed by the engine's own status, every
displayed number traced to an engine API response in the receipt. The
project law — "all invisible elements should be able to be seen when put in
motion" — becomes a teaching method: gravity, contact, and the balance of
forces are not prose; they are the visible bars, traces, and counters of the
lesson page while the real body falls.

## WHAT SHIPS (all under tools/lesson_shell/ + this lane dir; the slice page
tools/playable_slice/index.html is ANOTHER LANE'S and is not touched)

- `lesson_server.py`: a stdlib front door in the game_shell/slice_server
  shape — serves the lesson page, boots its OWN engine on a bind-tested free
  port (8127 refused by code), imports THE REAL BODY through
  `tools/playable_slice/scene_boot.py` reused AS A MODULE (no slice-page
  edits; additive reuse of the boot machinery the receipts banked), and
  fronts the fall: gravity off → authored-rest seat → gravity on → the
  engine's real descent, contact catch, and settle. The fall verdict reads
  the ENGINE's numbers (the drop_test pattern, unchanged semantics).
- `index.html`: the lesson page. First-run guide in plain words, every
  control keyboard-first and named on-page, the error beacon (the repo's
  page-error ledger pattern), and the live physics surfaces:
  - HEIGHT: the body's root height above the settled floor, from
    /api/status root_y (engine bytes).
  - WEIGHT: m·g from the banked constants (m=13824.5 kg, g=9.81 m/s^2 —
    membrane_tick.hpp/cpp, banked in slice_server.py and this receipt);
    shown as a downward bar.
  - FLOOR HOLD: the contact force the floor is currently exerting
    (engine contact while grounded; 0 while falling), shown as an upward
    bar — while falling the two bars visibly disagree; at rest they
    visibly match. THE TEACHING IMAGE: falling = weight > hold; settled =
    weight == hold.
  - THE FALL TRACE: root_y history drawn as a curve as it happens.
  - LANDED / SETTLED banners from the engine's own verdict.
- The teaching beat, in plainest words, on the page, timed to the phases:
  falling: "gravity pulls everything down — nothing holds the body";
  contact: "the floor catches it — the hold grows until it carries all the
  weight"; settled: "where the hold equals the weight, everything balances:
  that is where it rests." What the player should UNDERSTAND after 60 s:
  a body falls because of gravity, lands because of contact, settles where
  forces balance.

## PREDICTIONS (named before the run)

- P-KEY: the page's own key list names exactly ONE primary key (F = fall),
  plus R (reset lesson), H (help), C (camera keys inherited from the house
  pattern) — and the walkthrough presses each and sees its effect.
- P-FALL-SHAPE: the lesson's measured fall matches the engine's banked
  shape within the pre-declared bars below (peak, max speed, landed height)
  — because it IS the engine's fall, not a lesson-scripted animation.
- P-SURFACE: every displayed number on the page is byte-traceable to an
  engine API response recorded in the receipt (the number-trace table).
- P-UNDERSTOOD: the scripted stranger, reading ONLY the page, presses F,
  watches the fall, and reaches the lesson's "understood" state (all three
  teaching lines surfaced with their engine evidence) inside 60 s.

## FALSIFIERS (any one failing = the theory loses; the RED is recorded,
never tuned away)

| id | pass condition |
|----|----------------|
| F-LESSON-60 | the lesson's key moment — the fall TRIGGERED BY THE STRANGER'S OWN KEY PRESS and its landing — is reached with no external help in **under 60 s from page load**; the trigger key is chosen from the page's own words |
| F-NUMBERS-ENGINE | every displayed number traces byte-for-byte to an engine API response: the receipt carries a number-trace table (displayed value → API endpoint → recorded response); NO hardcoded physics prose anywhere on the page |
| F-FALL-SHAPE | the measured fall through the lesson matches the engine's banked numbers within pre-declared bars: peak root_y 0.9009 ± 0.02 m; max |vy| 3.6792 ± 0.05 m/s; landed root_y 0.1246 ± 0.002 m (bars = the banked measurements' own last-digit precision, derived NOT tuned) |
| F-SURFACES-LIVE | the weight bar and the floor-hold bar are driven by /api/status polling during the fall: while airborne hold < weight (visible), at settle hold == weight within display precision (visible); the trace draws ≥ 1 sample per 100 ms during the descent |
| F-KEYS-NAMED-WORK | every key named on the page works through its key path, verified by the walkthrough with per-stage effects (the stranger lane's dead-keys lesson: the handler is checked against the page's OWN key list) |
| F-ZERO-ERRORS | the on-page error beacon counts ZERO at the end, AND the harness's captured console.error/pageerror/requestfailed (minus by-design poll aborts, counted separately) is empty — through boot, fall, and settle |
| F-ONE-COMMAND | the lesson boots from ONE command (a .ps1) on this machine: engine build check → engine start → real-body import → lesson server up → page answers; measured in the receipt |
| F-SCOPE | zero edits under ChimeraEngine/, zero edits to tools/playable_slice/* (the slice lane owns it), zero edits to engine physics or gait_controller.hpp; lane edits only in tools/lesson_shell/ and this lane dir; no 4090/GPU compute; bundled chromium ONLY (MACHINE_FINDINGS: installed Chrome cannot navigate on this machine — optionally canary-gated per the escape pattern); push ONLY lane/lesson-one-fall-20260920; no master |

## DERIVED, NOT TUNED (Rule 1)

- The 60 s bar is the mission's named bar (the stranger lane's precedent,
  the same class of claim). The fall-shape bars are the banked measurements'
  own precision, not chosen to pass. The weight constant m·g = 135,614 N
  comes from the banked membrane_tick constants already pinned in
  slice_server.py — the lesson does not introduce a single new constant.
- The floor-hold displayed value is the engine's contact force response
  (membrane_tick's F_contact in y'' = F_contact/m − g); if the engine's
  /tick_state does not expose F_contact directly, the lesson displays the
  DERIVED hold m·(g + y'') from the engine's own root_vy stream — derived
  from engine responses, still byte-traceable, and the derivation is
  printed beside the number. No third path exists.
- The teach lines are CHECKED against the engine's phases (falling =
  root_vy < −0.05 while airborne; contact = hold rising; settled = the
  server's own settled flag), not by a timer.

## RUN PLAN

Prereg (this file) → engine build in THIS worktree (.tmp/lesson_build,
background-friendly, never block-wait) → lesson_server.py + index.html →
walkthrough.js (private headless playwright, BUNDLED chromium, fresh
context; page-error ledger; per-stage trace + budgets + watchdog — the
stranger lane's hardening pattern) → run_walkthrough.ps1 → 3 runs, identical
verdicts required → number-trace table → receipt.json + report.md →
commit ("Agent: lesson") → push ONLY the lane branch.

Receipt: tools/science_funnel/validation/lesson_one_fall_20260920/receipt.json.
Prereg: this file.
