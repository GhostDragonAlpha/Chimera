# RULE 0 PREREGISTRATION — OBS-POPULATE (2026-09-20)

Lane: `lane/obs-populate-20260920` (Agent: obspop) @ 1beb72e9 (the landed
interface-freeze tip, "LANE RECEIPT ... STATE-ALIASING FIRED").
This file is frozen BEFORE the delivery module is written, BEFORE the fresh walk
run, and BEFORE any measurement of this lane. The order is the law: (1) this
prereg (with the pre-measured context named below, the obs-split pattern:
context first, then freeze, then build), (2) the delivery build, (3) the fresh
end-to-end run, (4) the measurements, (5) the receipt. Nothing below is edited
after a measurement lands; the receipt appends.

## THE DECIDING CONTEXT (measured BEFORE this freeze, carried as pins)

The interface-freeze lane's F1 STATE-ALIASING audit FIRED: 21 aliased pairs on
the live 302-tick walk (bit-identical float32 80-field observations, differing
labels). The pairs' deciding quantities, from that lane's own
`aliased_pairs.json` (sha-pinned artifact in ITS dir, untouched by this lane):

- 20 pairs carry the body-advance clause (label vx = per-tick base-x delta x
  300 Hz, differing by >= the frozen graded bar 0.05 m/s): 16 exclusively
  ((11,38),(11,39),(14,38),(14,39),(23,38),(23,39),(24,38),(24,39),(27,38),
  (27,39),(29,38),(29,39),(18,33),(19,34),(20,35),(40,54)) and 4 that ALSO
  carry the pad-deformation clause (> kSinkRateMax 2.349e-3 m/tick on pad 3 =
  the rear-right paw): ((8,38),(8,39),(9,38),(9,39)).
- 1 pair is touch-pattern only: (12,25) — fore feet (False,True,..) vs
  (True,False,..); its named deciding fields are the per-foot slots 9-14.

The audit's mask census: `com_vel_x_heading` was NEVER-AVAILABLE (54 such
fields) — the body_velocity group rides mask 0 / mean fill; the values were
never delivered by the record. The frozen 80-field table ALREADY DECLARES the
field (index 21, group body_velocity, source `com_vel[0]`, m/s, heading frame,
CoM velocity); nothing about the table changes here.

PRE-MEASURED on the anchor trace (sha c6f9b6c0..., the interface-freeze audit
trace, byte-exact): the trace's per-tick `[dv] com=(east,south)` CoM projection
(gait_unit.cpp: `support.com_projection_east_m/south_m`) first-differenced at
the walk's own 300 Hz clock yields a com_vel x series that differs across BOTH
members of ALL 21 aliased pairs (16 pairs exclusively-body-advance, 4 pad+body
pairs, and the touch pair (12,25)); margins range 3.0e-4 m/s (pair (20,35) —
one 1e-6 m print quantum) to 9.1e-2 m/s. The base-x delta (the audit's label
quantity) also separates all 21 with larger margins. Both derivations are
derived-from-trace; zero engine bytes either way.

## THE THEORY (statement)

SENSOR-SIDE DELIVERY OF THE NAMED UNDETERMINED FIELDS SEPARATES THE ACTIONABLE
ALIASED PAIRS WITHOUT TOUCHING THE FROZEN INTERFACE OR THE WALK'S PHYSICS
BYTES. Field 21 `com_vel_x_heading` — delivered as the per-tick first
difference of the trace's own CoM projection east at the walk's own 300 Hz
clock, through the Python observation assembly (the trace->record bridge), with
the frozen reader UNCHANGED (it already reads `com_vel[0]`; the group gate
`available_groups` is the record's own delivery declaration) — separates every
aliased pair on this walk. The per-foot slots (9-20) remain STRUCTURAL on this
body: the frozen reader reads `foot_contacts`/`foot_forces` as an all-or-nothing
6-slot vector (fl,fr,ml,mr,hl,hr) and this walker has FOUR paws (fore_left,
fore_right, rear_left, rear_right — the interface-freeze lane's declared
walker-shape finding); the ml/mr slots are UNINHABITED, no lawful per-element
delivery exists, and slots ride unavailable — never invented. The frame
condition is declared: the delivered delta is world/east; on this walk the
heading frame coincides with the walk axis because the v1 command record's yaw
authority is NONE (command_record.py: yaw_rate RESERVED, zero measured
authority) — the equivalence is a property of the frozen command set, not a new
number.

A description survives any result; a theory can lose. The falsifiers below are
named before the run.

## PREDICTION (pre-named, unmeasured on the fresh end-to-end run)

- P1: the 20 body-advance pairs separate (16 exclusively-body + 4 pad+body).
- P2: the touch-pattern pair (12,25) separates ON THIS WALK through field 21
  (its members' delivered com_vel differ) — while its NAMED deciding fields
  (per-foot slots 9-14) remain structurally undetermined; the structural
  residual is DECLARED, not solved: a hypothetical state pair differing ONLY in
  fore-foot touch identity at equal body advance would still alias.
- P3: no NEW aliased pairs appear (a delivery only adds information; the
  post-delivery bit-identical group count cannot exceed the pre-delivery one).
- P4: the 4 pad-deformation pairs separate WITHOUT any pad-deformation
  vocabulary delivery (their body-advance clause carries them on this walk).
  The deformation-rate vocabulary question — whether a FROZEN-VOCABULARY field
  can carry the per-paw min-gap deformation rate — is NOT solved here: the pad
  channels are per-ENDPOINT, hind-legs-only, and the endpoint-signed ones ride
  'lohi' unavailable on this record set; a pair differing ONLY in deformation
  rate would be a v3-schema question for another lane. Declared residual.

## FALSIFIERS

### F1 — SEPARATION (the re-run audit)

**Statement.** Re-running the aliasing audit END-TO-END (fresh scene, fresh
out-of-tree cl.exe GAIT_EVENT_TRACE build from this HEAD, fresh walk, fresh
parse, the interface-freeze mine's own clauses verbatim) with the delivered
values leaves ZERO aliased pairs among the 21; every pair whose deciding field
became determined separates.

**Fires if.** Any of the 21 pairs survives bit-identical post-delivery
(a surviving separable pair), or a NEW aliased pair appears.

**Pre-committed action on FIRE.** Report the surviving pairs verbatim with
numbers; do NOT extend the delivery beyond the decreed derivation to force
separation; carry the red in the receipt.

### F2 — TRACE-INVARIANCE (the walk may not move)

**Statement.** Observations are passive telemetry: the delivery (Python-side,
post-trace) cannot move the walk. The fresh run's scene FILE sha equals the
wave-38/interface-freeze anchor f6844eeae3dc87170a572ccdeedf326a6cac4f73d1448941808bd8b25a8db342;
the fence legs hold: LEG A trace-build stdout == no-trace-build stdout
byte-for-byte, both == the wave-47 ship anchor 8c537cdb7cb8c43cf9423cb50056787bcc31ee487d70d3c2a1e73ed5d60b06cc
(fence_audit_stdout.py, reused unmodified); the stderr walk trace equals the
interface-freeze audit's anchor c6f9b6c00a1d549a4bc709724d2f62f8f28b37823696de4689e1950651c37481
byte-for-byte; the control leg (the interface-freeze mine run VERBATIM on the
fresh trace) reproduces their 21-pair census exactly.

**Fires if.** Any anchor sha differs, or the control leg's census differs from
the pinned aliased_pairs.json (21 pairs, 13 context pairs, 277 distinct
observations, 13 bit-identical groups over 38 ticks).

**Pre-committed action on FIRE.** STOP; diagnose (instrument, scene, or
environment drift); the lane ships nothing until the walk bytes are re-anchored.

### F3 — TABLE-INVARIANCE (the frozen 80 fields)

**Statement.** The frozen interface table regenerates BYTE-IDENTICAL
(sha256 e8c2d698dee0337414c48e8d2f6569c45f6f61828dabdeff6a4f1188b1c0671c,
68230 bytes) from the live code and the pinned section
(3de82a1156ac2f39ed04da24c7fd40357642d7bc029e09b509dfc3ea1af63079);
OBS_SCHEMA_VERSION stays 2; no tracked byte outside
`tools/science_funnel/typeb_export/**` (ONE additive module),
`tools/science_funnel/validation/obs_populate_20260920/**`, and the declared
test file moves. observation_schema.py, the table JSON, INTERFACE.md,
gait_controller.hpp, gait_* validation, command_record.py, option_certificate.py:
untouched.

**Fires if.** The regeneration differs by one byte, or the scope diff shows any
undeclared path.

**Pre-committed action on FIRE.** STOP; a table change is a v3 lane's work and
this lane ships nothing.

### F4 — CORPUS-REFREEZE (what moves, with cause; nothing else)

**Statement.** The observation stream changes BY CONSTRUCTION (the delivered
field + the mask census it feeds: com_vel_x_heading available on 301/302 ticks;
mask_mean/mask_frac_avail shift for every tick). This is legal PRE-training:
no frozen actor exists — this lane IS the pre-training gate. The cause is
registered here. What must NOT move: the P3 manifest hash 9ca7e976dfb0dedd3f56dfa404673ee77c00801acb2753cdfd83604c480c35b7,
the P3 action-stream replay sha e25406e86cbf5347683ee3824d385bc1d07bfd500e83eb6b9133a1e82d4bfbd9
(the pinned slice trace_slice_wave38.json 69babe84... carries NO com_vel keys —
measured — so its projections are untouched), the section sha 3de82a11..., the
table sha e8c2d698..., the legacy 64-literal. The body_velocity normalization
constants REMAIN the frozen 0/1 never-available placeholders (F3 pins the
section); the delivered field therefore rides raw-scale under clip 8.0 —
recorded cause — and the measured-constants regeneration for the newly
delivered field is the trainer lane's declared contract (the same shape as the
obs-split lane's declared 64->80 actor resize).

**Fires if.** Any pinned hash above moves, or anything moves that is not the
declared stream change.

**Pre-committed action on FIRE.** Diagnose the leak (the delivery must not
touch the P3 harness, records, or manifests); report; never re-pin silently.

### F5 — DETERMINISM (3-run byte-identity)

**Statement.** The delivered pipeline (fresh trace parse -> delivery ->
projection -> search) is deterministic: 3 runs produce byte-identical
artifacts (mine output text + pair ledger JSON).

**Fires if.** Any run differs by a byte.

**Pre-committed action on FIRE.** Diagnose before shipping.

## DECLARED SCOPE (honesty)

- Zero engine bytes. No build is committed; the walk harness is the
  interface-freeze lane's out-of-tree pattern (scratch GAIT_EVENT_TRACE +
  no-trace builds of the IDENTICAL HEAD source; nothing tracked is built or
  modified).
- The delivery is ONE additive module in `typeb_export/` (the trace->record
  bridge, pad_channels.py's pattern) + ONE additive mine in this dir + the
  declared test file. The frozen reader is NOT modified: it already reads
  `com_vel[0]` through the group gate.
- Fields 22-25 (com_vel_y_heading, com_vel_z, yaw_rate, yaw_rate_prev) are NOT
  delivered: not deciding quantities for any fired pair, and outside this lane's
  decree (primary: field 21; secondary: per-foot slots). They ride unavailable.
  com_vel_z is not determined by the trace at all (the CoM projection is
  planar); com_vel_y_heading IS derivable (the south delta) and its
  non-delivery is a scope decision, declared — not a determinacy claim.
- The per-foot slots (9-20) are STRUCTURAL: no delivery exists on this body
  (all-or-nothing 6-slot read vs four paws). The touch-pattern pair's named
  deciding fields therefore stay undetermined; P2's separation is via field 21.
- The interface-freeze lane's artifacts (their validation dir) are read-only;
  this lane's re-run artifacts live in THIS dir.
