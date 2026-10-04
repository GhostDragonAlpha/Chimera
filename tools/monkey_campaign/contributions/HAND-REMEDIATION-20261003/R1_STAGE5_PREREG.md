# R1 STAGE-5 PREREGISTRATION (DRAFT) — the runtime-evidence rung at the DECLARED RIGID-CONTACT scope on the headless native solver

Status: DRAFT authored by `wk-hand-remediation` for the Lieutenant's pin
(separate-first; the committed bytes are the freeze). PRE-RUN of the
stage-5 class. NO_WORKTREES honored; all CPU through the canonical runner;
the capture machinery per the sealed capture-gate template.

## 0. THE SCOPE DECISION FIRST (the Lieutenant's question, answered before anything else)

THE HONEST OPTIONS CONSIDERED:

- (a-FULL) headless-native runtime evidence WITH the pad-interface
  COMPLIANT contact model (VPL-1 implemented in the solver): NOT RUNNABLE
  TODAY. The current solver's contact model is the sealed DECLARED RIGID
  fixture (A4: "declared rigid pads pressed at the operating point"); a
  compliant layer is NEW contact-model code in the native solver — new
  physics requiring its own prereg, review, and qualification chain
  (exactly the VPL-1 precedent: a declared model class earns its own pin
  before it executes). Declaring it inside a runtime prereg would be a
  silent model change against the sealed W03 line. NAMED-UNMET RUNG:
  recorded, owned, and sequenced after this stage.
- (a-SCOPED — FROZEN): the headless-native runtime-evidence run on the
  W03 native solver at the DECLARED RIGID-CONTACT scope (the solver's
  existing sealed contact model), with the per-tick SIGNED channel
  instrumentation, the CAPTURE-BOUND states per the sealed capture-gate
  template (VISUAL-GATE-1: capture -> gate -> receipts one flow), and the
  PARITY RE-BIND per the G08 law (the changed contact dynamics get their
  own identity gates; walking certification is not inherited). This is
  the DEEPEST EVIDENCE the current corpus supports TODAY: the only
  physical body in the corpus is the headless native solver, and its
  fixture-grasp path (G04 grip contact, G06 hold, G07 release) is sealed
  and runnable.
- (b) the membrane pair's runtime scene leg: DECLINED. It is another
  lane's ownership (the pair-assembly lane), it is the same solver family
  (no added evidence), and depending on it violates the non-dependence
  rule (the transactional window 65a23111 is REFERENCED, never depended
  on; the W03 signed-instrumentation lane is likewise referenced as the
  deeper instrumentation, never depended on — this run declares its OWN
  minimal signed channels).
- (c) a named refusal: DECLINED AS DISHONEST. The fixture-scope runtime
  evidence IS runnable today on the only physical body and IS evidence
  for the grasp chain — honestly labeled. Refusing to run it would hide
  the deepest available evidence behind a scope technicality.

FROZEN: (a-SCOPED), with the VPL-1 compliant layer's runtime
demonstration as the NAMED-UNMET RUNG (requiring the solver
contact-model implementation under its own prereg + review), and the
not-claims at maximum. The pad-interface grasp runtime claim CANNOT be
made today; what CAN be demonstrated is the fixture-pattern
grasp/hold/release mechanics running in the native solver with
capture-bound evidence and parity — the runtime evidence for the grasp
CHAIN at the declared scope.

## 1. THE HONEST QUESTION, ANSWERED (what can lawfully run TODAY)

The product runtime FAILS readiness 0/5 (PR #334: no body, no
actuation) — it cannot host runtime evidence and is EXCLUDED. The
headless W03 native solver is the ONLY physical body in the corpus; its
fixture-grasp path is sealed and runnable. The capture-bound-state
machinery exists (the sealed capture-gate template `03a95c39...`,
VISUAL-GATE-1, 7/7 planted defects, sergeant visual PASS; the
K02/landing pattern). The parity machinery exists (the G08 law). The
signed-instrumentation CLASS exists (this lane's stage-3 per-tick signed
records, carried to runtime).

## 2. THE RUN (what executes)

The headless native solver executes the fixture-pattern grasp/hold/
release schedule at the sealed operating point (the 60 N/channel
declared press; DT = 5.0e-3 s; the friction placeholders mu_s = 0.6 /
mu_k = 0.4), with:

- PER-TICK SIGNED CHANNELS (this run's own minimal instrumentation, the
  stage-3 class carried to runtime): the press impulse (signed),
  the friction impulse (signed), the load impulse (signed), per channel,
  per tick — reversals VISIBLE, never absorbed (the walk/pair lesson).
- CAPTURE-BOUND STATES: the capture frames bound to the state receipt
  per the capture-gate template (the state binding hash on every
  retained frame; `visual_capture.validate_manifest` or the template's
  gate call; a PASS without the gate having run is structurally
  impossible in the template flow).
- THE PARITY RE-BIND: the CPU reference vs the runtime identity gates
  re-bound to this run's contact dynamics (the G08 law).

THE PHASES (the sealed G04/G06/G07 pattern): press -> hold -> release,
per channel, at the declared operating point.

## 3. THE OUTCOME SPACE (declared before the run; counts close)

- SCHEDULE: {COMPLETED, REFUSED} — exactly one.
- HOLD phase per channel: {HOLD_SUSTAINED, HOLD_SLIP} — exactly one per
  channel (the sealed G06 law: the friction limit mu_s*N vs the load;
  slip class never holds — the band_hi|n=1 precedent).
- RELEASE phase per channel: {RELEASE_SEPARATED, RELEASE_RESIDUAL} —
  exactly one per channel (the sealed G07 law: the press removed
  EXACTLY, W_press == 0.0 J every release tick; the free-fall recursion
  v_down(k)-v_down(k-1) == g*DT to the sealed tolerance; a residual
  force after release is a REAL finding, recorded and routed — the
  invisible-anchor class).
- CAPTURE: {GATE_PASS, GATE_FAIL} — exactly one (the template's exit
  code law).
- PARITY: {PARITY_BOUND, PARITY_MISMATCH} — exactly one.
COVERAGE ARITHMETIC: every phase/channel/tick accounted; any unnamed
state = `stage5_outcome_space_broken` (refusal).

## 4. THE FROZEN PREDICTIONS (honest; the basis is the sealed pair-path evidence; a falsified prediction = a routed result)

- S5-P1: the schedule COMPLETES (the sealed path ran it; TEETH: a REFUSED
  schedule = the scene contract changed under this run — routed).
- S5-P2: every channel HOLD_SUSTAINED at the operating point (the sealed
  evidence's own result: holds at ~zero KE; the mu=0 control non-closing
  is the retained bite, run in-run as the contrast case). TEETH: any
  HOLD_SLIP — a RESULT routed (the operating point or the contact model
  shifted under this run).
- S5-P3: every channel RELEASE_SEPARATED (W_press == 0.0 J every release
  tick; the free-fall identity within the sealed tolerance). TEETH: any
  RELEASE_RESIDUAL — the invisible-anchor class, a MAJOR result routed.
- S5-P4: the signed channels show the press-signed press work
  (0.8069338128977511 J-class per the sealed 20-tick hold reading —
  recorded, never gating) and the friction-signed losses balancing the
  gravity work to the sealed delta (~1e-12 relative; the hold-at-zero-KE
  precedent). TEETH: a sign reversal unexplained by the phase schedule,
  or a balance failure beyond the declared tolerance.
- S5-P5: CAPTURE GATE_PASS and PARITY_BOUND. TEETH: either failing = the
  runtime evidence is not capture-bound / not identity-bound — the run
  records the failure and routes it (the runtime stage does not pass on
  unbound evidence).
- THE ABSORBED-BAND ANALOG (the institutionalized lesson): the fixture
  pads are RIGID — this run's outcome space has NO compliant-absorption
  class, and the receipt states the VPL-1 compliant layer is the NAMED-
  UNMET RUNG; the coexistence note (the strict-bone reading vs the
  offset-surface reading) is carried verbatim in the receipt.

## 5. THE QUANTITY CODE-PATH TABLE (the depth-basis law)

Every emitted number names its producer: the press impulse — the
solver's press channel accumulator at the declared operating point; the
friction impulse — the solver's friction channel; the load impulse —
the body weight line (the declared reading, placeholder-labeled); the
hold verdict — the G06 law (mu_s*N vs the load); the release verdict —
the G07 identity (W_press == 0; the free-fall recursion); the capture
binding — the capture-gate template's gate call + the state-binding
hash; parity — the re-bound identity gates. NO quantity is cited from
an analytic stage: stage 5 is RUNTIME-ONLY evidence.

## 6. THE HONEST-ABSENT LIST (binding; the not-claims at maximum)

- THE PAD-INTERFACE COMPLIANT LAYER IS NOT AT RUNTIME: the VPL-1
  compliant layer is the NAMED-UNMET RUNG (the solver contact-model
  implementation under its own prereg + review). Every runtime record
  here carries the RIGID-fixture contact scope. NO sentence in any
  artifact may call the fixture pads "the pad interface" or "the pad
  model".
- NO GRASP-COMPLETION CLAIM: the objective-line law — a completed
  specification is not a trained skill; the playable-monkey goal stays
  open until the positive behavior is demonstrated AT ITS OWN SCOPE.
- TC-8 = 0/8; x_press ABSENT; the 60 N/channel press is a DECLARED
  fixture, never an actuator qualification; the same-hands debt stands
  (the 0.049 kg hand vs the 10.038 kg line); friction PLACEHOLDER (A5);
  the mass lineage UNRESOLVED (gap 9, per-reading); the product runtime
  is EXCLUDED (readiness 0/5, PR #334).
- THE ERRATUM'S GOVERNING P1 LABEL carried in the receipt
  (`governing_labels`); the corrected ladder label carried: pad-geometry
  + capacity + law-form + collision-adjudication (strict-fail named)
  stages complete; the exact-candidate collision adjudication at the
  PAD-INTERFACE scope remains the named-unmet collision rung; RUNTIME
  EVIDENCE at the declared rigid-contact scope = this stage; stage 5
  completion names the next unmet rungs, never closes the goal.

## 7. EXECUTION AND CONVENTIONS

Gate: the Lieutenant pins THIS file (separate-first), then releases; the
package seals against the pin commit; the seal bytes are captured into
`seal-store/` at creation; run class `stage5_runtime_evidence` with a
receipt-level delta note. Slot discipline per the corrected record (slot
2 first, fallback 3; BUSY = retry; this lane's refusals leave no runner
rows and other lanes' rows are never cited as this lane's attempts).
Anti-tuning: the schedule, the operating point, and every constant above
are frozen pre-run; post-run change requests are FINDINGS, never edits.
Receipt conventions: script-emitted hash lines only; keyed blocks; named
artifacts; the coexistence note verbatim. No merge/review authority
claimed; Sergeant review requested through the Lieutenant; author
self-review certifies nothing.
