# DEV_RUN_REFUSALS - MAT2-G08 (candidate-scoped disclosure; W08 lesson)

Candidate: base 5f82a3dd, prereg chain f5ae83ce -> 65bccc76, package write
scope tools/monkey_campaign/contributions/MAT2-G08. This file discloses every
dev-run event and measurement-form finding from the development sealed runs.
No entry below changes any frozen prereg window, verdict law, battery or
falsifier arm.

## Dev runner jobs (sealed, slot 0)

- 3bf2c810ffaf4abc8860efcc107f587a - FAILED before execution: the command
  vector lacked the interpreter prefix (WinError 2). Infrastructure error,
  not a card refusal.
- e81b257088124ae182eec05229c81666 - FAILED (exit 1): AttributeError
  assembly_line.seam_union - a code defect (the A8 block was lost to a
  truncated file append during authoring); fixed before any measurement.
- 640586e3bfc2406a9e807ce4a88a8631 - FAILED (exit 1): TypeError
  gc.NAMED_ABSENT indexed as dicts - a code defect (G04's NAMED_ABSENT rows
  are (name, quantity, provenance) tuples); fixed before any measurement.
- ceaf93af1c1043109819976ff393ad20 - exit 0, receipt state FAILED ONLY for
  declared-keep bookkeeping (no --keep file paths existed; stdout lives in
  runner.log). Re-run fa4bef789a84433fb3102ee53f731a42 PASSED with the
  trace+receipt declared: A1/A2/A3/A4/A6/A8 GREEN on the first full
  measurement; A5/A7/A9 red - all traced to MEASUREMENT-SCOPE defects in the
  G08 probes below (the A1 byte-level line identity against the certified
  G06/G07 traces was already true, so the assembled physics was never in
  question).

## Measurement-form findings (fixed to the sealed laws' own scopes)

1. flight_closed_form: first applied the sealed G06 advance model to ALL
   ticks; its sealed domain is the FLIGHT WINDOW [handover, climb_stop] per
   run (the release fall belongs to the free-fall laws). The out-of-domain
   worst 0.0002452500000000001 m is exactly g*DT^2 (an unpressed free-fall
   tick, not a model violation). Fixed to the sealed domain.
2. press_establishment / conversion: first included every pad with any
   positive recorded contact jn, which sweeps in noise-level contacts
   (e.g. 5.7e-11 N*s) that the sealed laws never treat as operating points.
   Fixed to the sealed operating-point scope: established jn >= P/2 on
   non-approach, non-release ticks, with the unpressed flight channel
   excluded.
3. handover_jt: first measured (m/n)*g*DT over ALL cases' holders; the
   sealed G06 law is (m/(n-1))*g*DT for STICKING holders of the CLOSING
   cases (the sealed G01 admissibility condition); honest non-closings slip
   by declaration. Fixed to the sealed scope.
4. release bars: the frozen law is the PER-SCENARIO bar share_kg * 1e-10
   N*s/kg (prereg section 7 names the 1e-10 scale). Measured as the worst
   RATIO of the scenario's recorded maxima to its OWN derived bar
   (window 1.0); comparing raw N*s against the bare scale would misstate
   scenarios with larger shares (the sealed G07 worst jn 4.384506202278262e-10
   N*s belongs to a scenario whose own bar is 1.0037998000000001e-09).
5. stored-energy drift + exact-form continuity: first measured on ALL ticks;
   the sealed G07 laws are UNOBSTRUCTED-tick identities (the two-tier law;
   collision-tick exchanges are recorded evidence). Fixed to the sealed
   scope; the collision-tick kinematic maximum is reported alongside
   (measured 5.075238746559199e-06-scale values are the certified two-tier
   class, not violations).
6. friction split: first measured |work_friction_J - loss_solver_J|; the
   sealed G07 dissipation sign convention is work_friction_J +
   loss_solver_J == 0. Fixed to the sealed identity.

## Refusal codes observed in dev runs

None beyond the prereg section 13 registry. The two code defects above
(AttributeError/TypeError) were authoring defects surfaced before any
physics measurement; they are not card refusal codes and fire nowhere in the
candidate.

## Full-gate dev job (937ca06de8564d1686c49403f729bdc4)

main GREEN (A1-A9), determinism byte-identical across fresh jobs (trace sha
764f3755... in three independent jobs), F_all_green (5/5 arms),
P_regression_suite_green (6 suites) -- then the named-check suite failed 1
of 22: the test's frozen-marker literal 'Amendment a1' does not appear
verbatim in the prereg flat text (the prereg section reads '14. Amendments -
a1 (pre-experiment'). A TEST defect (wrong literal), not a receipt or physics
defect; fixed by matching the actual frozen text. No refusal code fired.
Same job disclosed the capture camera-cover requirement: the composed-axis
camera samples need real poses at the axis ends, so the assembly story
stores ticks 1 (T) and 1/30 (R) in addition to the declared frame beats --
story beats (the frames) are unchanged from the prereg declaration.

## r1 correction (PR #310 CHANGES_REQUIRED; receipt-scoped; no physics,
gate-verdict, window, battery or prereg change)

The review found the amendment a1(ii) composition binding implemented only
over the R collision-event values, with A7 conversion and the A9
press_establishment row measured over just the 10 story ticks of
band_mid|n=3. Correction implemented exactly as instructed:

1. conversion binding across the WHOLE assembled battery, measured-vs-
   certified against the pinned G06 x_evidence.conversion_worst_N, refusal
   identity_binding_mismatch armed;
2. A7 + the A9 press row re-measured over the whole battery;
3. measured-vs-certified reported (receipt section 4.1 of REPORT.md);
4. the A7 domain disclosed in the receipt (A7_evidence.conversion_domain).

Two probe defects were found and fixed while implementing the correction
(both in the G08 probes only; the sealed G06 X4 scope was taken verbatim as
the authority): (a) the operating-point filter jn >= P/2 swept in slip-mode
transient contact spikes (e.g. 2.2110979233185386 N*s at scene|n=3 tick
134) that the sealed law excludes (a pad that honestly separated or slips
is not in the pressed attached state); (b) the flyer_pressed transcription
had the flight clause inverted (points during the flight window instead of
outside it). The corrected whole-battery measurement reproduces the
reviewer's values exactly: conversion worst 1.1144422273901e-08 N at
(scene|n=2, tick 193, pad 0) == the certified G06 value (measured minus
certified 0.0); jn worst 5.5722093605936607e-11 N*s (the reviewer's
5.57e-11 class); A5 flight binding delta 0.0. New receipt sha256
1f8a0bb23a830008be97f4fbc7f9e8bc7d735bb664df6ef47d3a84e0417853bd; trace
unchanged (17f83488...); sealed physics job f4d985854bdf4d3bbad98eb6ec29b8dd
PASSED, cleanup_verified true.
