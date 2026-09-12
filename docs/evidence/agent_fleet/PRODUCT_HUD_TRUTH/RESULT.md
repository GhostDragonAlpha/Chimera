# product-hud-truth-01 — RESULT

Task packet: the PR #97 blind dyad judge's findings 4(b) (the joint row named
the SHOW sweep's cycling joint over a 0.00 theta while the right arm rose) and
4(d) (the on-screen clock advanced ~36 s per declared frame and wrapped a
112 s lap — "not a real-time capture"). Deliverable: no readout displays a
number that is not the live value of the thing it names.

## What changed (base cb874a3a -> head)

- `ui.hpp set_joints_view` — derives the EDIT-DRIVEN SET from the view it
  already receives: while owner==1 the sweep branch cannot write thetas, so any
  theta change IS a programmatic drive. Bit k = joint k; cleared when the show
  reclaims the pose.
- `ui.cpp build_chrome` HUD row — in the driven regime the row names the driven
  joint(s) (up to 3, then a count) with LIVE thetas from the same pushed view
  the pose kernel wrote (st +7) — the 2026-09-04 EDIT-selection law generalized.
- `ui.cpp` TIMELINE readout — in the driven regime the plane shows the
  show-clock PARAMETER itself (the timeline the driving interaction pins
  through POST /show's scrub), labeled "show clock; show sweep paused" — the
  idle 112 s lap never appears beside edit-held motion.
- `ui.cpp` timeline footer — labels the sweep paused and counts the posed joints.
- `engine.cpp reel_note_grab` — the reel caption (and GET /reel) name a DRIVEN
  joint (+count) with its live st+7 theta while edit-held, not the sweep's
  cycling lane.
- Engine's `set_show_clock` pushes unchanged: the sweep clock stays a live
  parameter; the DISPLAY law chooses the plane by pose owner. main.cpp and
  engine.hpp untouched (out of scope; the derivation needs nothing there).

## Verification (prereg PREREGISTRATION.md; checker verify_clauses.py)

- **Run 1 — F2 FIRED, retained** (`run1_retained_F2/`, VERIFY_RUN1_retained.txt:
  53 checks / 2 FAIL): every joint-row and reel clause passed, but the clock
  readout showed 0.963/1.763 s at g012/g020 vs the predicted (i-10)x0.1. Root
  cause measured: clk itself was EXACT (i x 0.1, pinned); the constant offset
  was my origin event (owner 0->1 transition), which lands one frame BEFORE
  that iteration's scrub consumes and therefore captured the frozen boot clock
  (0.237 s). The prereg's "claim at f10" also misread the protocol — the PR #97
  script drives /joint from f0. Correction (no tolerance changed): the readout
  shows the show-clock parameter itself, which needs no origin.
- **Run 2 — 68 checks / 0 FAIL** (VERIFY_RUN2.txt), same protocol as PR #97
  (same rig, script, camera, keyframes, captures) plus the preregistered
  /show pin+scrub and numeric captures:
  - P1: driven-regime row = "EDIT <driven joints> <live thetas>"; g020/g025
    name shoulder_R +36.00 and elbow_R +75.00 EXACTLY; REST rows unchanged
    ("SHOW ..."). Tolerance 0.05 deg: max observed deviation 0.004 deg.
  - P2: GET /joints (st +7) vs commanded <= 0.05 deg everywhere (exact).
  - P3: judge-visible readout "EDIT t = <i x 0.1> s (show clock; show sweep
    paused)" — 1.200/2.000/2.500/3.500/4.400 EXACT (readout_transcription.json,
    hand-transcribed from frames/g012..g044.png); deltas 0.800/0.500/1.000/
    0.900 EXACT vs declared gaps; no "112.0 s (lap" string in the driven regime.
  - P4: REST regime unchanged (row prefix SHOW; sweep readout form).
  - P5: reel captions/entries carry the driven law ("t1.90 EDIT shou +36.0d";
    /reel joint='shoulder_R+1').
- Numeric verification channels: /studio_chrome serves the exact drawn row
  strings (one formatting site); /joints, /show, /reel are engine truth.

## Acceptance

- Numerical gates P1-P5: PASS (run 2).
- P6 (blind dyad re-run, judge free of the 4(b)/4(d) classes): **OPEN —
  NOT_CLAIMED.** The spawn is the lead's (PR #97 pattern, message a5f70dbe7d7b
  precedent): coordination request posted to glm53-lead-02's mailbox with the
  committed spec (dyad_orderedframes_spec.json, sha-verified frames), exact
  prompt dyad_plan/exact_prompt_product-hud-after-orderedframes-v1.txt
  (sha256 bb63487d3c06b1eb73cda0065506030ca0379167aa71fdbaef65200463958931),
  blind to family/scripting/expected behavior. The verdict assembles into
  DYAD_REPORT.txt here.
