# HIP-ARMS RECORD — Rule 0 membrane, written BEFORE any arm scan of this lane

Lane `agent/hip-arms-20260920` (branch `lane/hip-arms-20260920` @ a13a4d87, FROM the landed
k-fill lane). Mission: derive the hip moment-arm curves from the deposit's OWN geometry — the
same exact `-dL/dq` machinery that produced the knee/ankle/MTP arms
(`pulley_rederivation_20260920/derive_pulley_arms.py`, imported UNMODIFIED) — for the
hip-extensor set the rear-up book consumes (BFL, GMax, SM, ST, plus the admitted hip crossers
inventoried), then re-run the hip-extension capability book and the rear-up class C* verdict
with DERIVED arms replacing the record's straight-line arms. The prior verdict
(NOT COVERED, 26.582 < 33.6) updates honestly in whichever direction the numbers go — BOTH
outcomes are results, never tuned.

This file was written before this lane computed its first moment arm. The sections below the
GEOMETRY INSPECTION heading are determinations on already-committed, sha-verified bytes
(parse-only structural reads of the deposited .osim; no arm number existed at write time).

## RULE 0

**STATEMENT.** The deposit's hip path geometry yields moment-arm curves sufficient to retire
the k-fill book's named straight-line caveat (the DECLARED 25% unknown — the estimate class
the pulley lane falsified at the knee, ratio 0.00) and to re-adjudicate the operator's rear-up
class C* in (22.4, 33.6] N.m on measured-deposit arms. Someone could disagree: (a) the
deposited hip paths may carry no wrap/via structure at all, in which case "straight line" IS
the geometry's answer and nothing is retired except the unknown's size — this branch is
DECLARED, not failed; (b) the derived arms may move the hip capability across the 33.6 N.m
class top (or not) — either way the verdict updates; (c) the derived arms may invert a sign —
recorded, never normalized away.

**PREDICTION (pre-named, from the mission).** Derived arms exceed the straight-line record
arms for at least BFL/SM at mid-stance hip angles (geometry concentration of the moment arm:
the record's arms came from its OWN 2D schematic hindlimb, not the deposit; the deposit's 3D
point paths sit at different perpendicular distances from the hip axis). Named sub-prediction
P1: at the Oku mid-stance walk node (hip_flexion_r = -0.0272 rad, the x=0.50 entry of the
sha-pinned Oku node table) the derived extension arms of R_BFL and R_SM each EXCEED their
record arms (0.056704702 m, 0.059558106 m). The honest alternative is named in advance: if
EVERY derived arm sits within the record straight-line band, that is the answer and the
prediction FIRES. Internal anatomical sub-prediction P0: the known flexor R_ILI shows a
POSITIVE arm about hip_flexion_r at the model default pose and the known extensors
R_BFL/R_GMax/R_SM/R_ST show NEGATIVE arms there (a uniform inversion is recorded as a
convention divergence, not silently normalized).

**FALSIFIERS (the mission's five, verbatim in substance).**
- **F1 NO-GEOMETRY** — no wrap/via structure at the hip: the lane reports
  straight-line-as-geometry with the tightened bound (the measured derived-vs-record spread
  replaces the declared 25% unknown) and still re-runs the book. Declared, not failed.
- **F2 VERDICT-DRIFT** — the re-run verdict changes: report both books side by side with the
  arm curves as evidence; NO constant may move except the arms themselves (forces byte-equal
  to the k-fill set, demand C* = 33.6 N.m fixed, class fixed at the k-fill primary class).
- **F3 TRACEABILITY** — every number sha-pinned (the .osim pin, the scan script, the force
  set commit a13a4d87); zero uncited constants.
- **F4 DETERMINISM** — 3 independent full derivations byte-identical; sha256 of the
  deliverable recorded in the receipt.
- **F5 CONTAINMENT** — no source changes outside
  `tools/science_funnel/validation/hip_arms_20260920/` (unittest-asserted via
  `git status --porcelain`).

Any hit is measured and recorded. Nothing is tuned.

## GEOMETRY INSPECTION (risk check 1 — parse-only structural reads, performed before this
prereg was finalized; zero arm numbers computed)

The deposited .osim (sha d5c65cbc0a72bd2d5c2258c6bd018fe850ae25cce6fb07c1f268b91e598c88e9,
byte-matching the pulley lane's and k-forensics' pins) declares 14 wrap objects. The
hip-crossing muscles:

- **The k-fill primary class has NO wraps and NO via-point structure:**
  R_BFL 2 path points (Pelvis -> shank_r, one straight segment spanning hip AND knee),
  R_GMax 3 points (Pelvis -> Pelvis -> thigh_r), R_SM 3 points (Pelvis -> thigh_r ->
  shank_r), R_ST 4 points (Pelvis -> thigh_r -> shank_r -> shank_r). PathPoints ARE the path;
  there is no PathWrap reference on any of the four. **F1's condition is MET in advance** for
  the primary class: the machinery runs as-is (exact `-dL/dq` on the poly-line through the
  hip CustomJoint FK), and the lane's deliverable is the certified arm curves plus the honest
  re-verdict, with the 25% unknown collapsing to the measured derived-vs-record spread.
- **Wrap structure at the hip EXISTS in the deposit and is honored where referenced** (so
  "no geometry anywhere" is false): R_AL -> rIschium_Cylinder (on Pelvis); R_ILI and R_RF ->
  rFemoralneck (on thigh_r); R_SAR -> rFemoralMedialCondyle_Sphere (on thigh_r). Active
  flags recorded in the run audit. These muscles enter the inventory with wraps resolved by
  the imported machinery, exactly as the pulley lane resolved them at the knee/ankle/MTP.
- hip_r is a CustomJoint (hip_flexion_r, hip_rotation_r, hip_adduction_r, each range
  [-1.5708, 1.5708] rad; default hip_flexion_r = 0.37350046631756723 rad, others ~0).

## DECISIONS (openly recorded, one number one reason, nothing swept)

**D1 — SCAN COORDINATE AND RANGE.** Coordinate: hip_flexion_r ONLY — the extension book's
axis; the capability law is per-axis `-dL/dq`, so no abduction scan is demanded by the book.
Range: the deposit's own declared range [-1.5708, 1.5708] rad, 2001 samples (the lane's scan
size), all other coordinates at model-file defaults (the pulley lane's declared protocol).
Advisory context only: the adduction-axis arm of every class muscle at the model default
pose via the same FD (a named reading, never consumed by any capability sum).

**D2 — WINDOWS READ OFF THE ONE CURVE.** One scan per muscle over the full declared range;
windows evaluated on it, never re-scanned:
- WALK window = the Oku 2021 before-alteration recorded hip range
  [min_rad, max_rad] = [-0.1556169071, +0.8906684904] rad
  (byte-pinned `hind_torque_book_20260921/inputs/derived_numbers.snapshot.json`,
  oku_before_alteration.angles.hip).
- REAR-UP window = the extension side of the deposit's own declared range, [-1.5708, 0] rad;
  anchored context from the receipts: the standing-pose-of-record hips sit at
  -0.165336845485 / -0.163993995356 rad (hipL/hipR flexion,
  `standing_pose_20260921/pose.json` maximin) — inside this window — and the recorded hip
  bound of that lane (+/-2.0943951 rad) EXCEEDS the deposit's declared range, so the deposit
  range binds. The rear-up class C* is adjudicated on the REAR-UP window; the walk window is
  reported as the walk-side capability reading.

**D3 — THE CLASS IS FIXED (F2).** Primary class = the k-fill book's own hip_extensors
functional group: R_BFL + R_GMax + R_SM + R_ST, forces byte-equal to
`k_fill_20260920/k_fill_book.json` derived_force_set.muscles (BFL 271.23914145829923 N,
GMax 124.39006222755602 N, SM 61.58807486670213 N, ST 49.96725178663907 N). The adductor
secondary is named exactly as the k-fill book named it (R_AL + R_AM + R_GRA + R_PECT), as a
named secondary — not in the primary class. The remaining ADMITTED hip crossers (R_ILI,
R_GMed, R_GMin, R_PIRI) are inventoried and named as a NON-CLASS reading (reported, never
summed into the primary class). The QUARANTINED hip crossers (R_RF, R_SAR, R_AB) stay NAMED
GAPS — quarantined forces are never admitted (the k-fill substitution policy, inherited).

**D4 — CAP LAW FIXED (F2).** The k-fill books' law, applied unchanged: per window,
cap = max over q of SUM over class of F_m x |r_m(q)|, with the per-muscle per-q SIGN GATE
(the ankle book's sign law): a muscle contributes only where its derived arm carries the
direction's sign. Sign convention, declared in advance: r = -dL/dq about hip_flexion_r;
POSITIVE arm = flexor torque (increases hip_flexion_r), NEGATIVE arm = extensor torque
(extension = decreasing hip_flexion_r). The extension capability sums NEGATIVE arms as
|r|. The only consumer-side change in the whole lane: r_m(q) is the DERIVED curve instead of
the record's straight-line scalar.

**D5 — THE VERDICT.** covered iff max capability > 33.6 N.m (C* top, operator-authored,
consumed as given). PRIMARY = the derived hip-extension book at the REAR-UP window;
CONSERVATIVE = max over the measured-arm books (knee 8.489511, ankle plantar 4.398653,
ankle dorsal 0.573906, MTP 1.163086 — the k-fill book's own numbers, untouched). Both books
side by side in the receipt; both outcomes are results.

**D6 — MACHINERY (F5).** `pulley_rederivation_20260920/derive_pulley_arms.py` is imported
UNMODIFIED (sys.path import of the sibling lane; its file sha is pinned in the receipt).
FD step 1e-4 rad central differences (the lane's step); -dL/dq authoritative (the pulley
lane's verdict); advisory geometric arm recorded only where a pelvis-thigh joint-spanning
segment exists (R_BFL spans pelvis->shank in ONE segment, so its advisory arm is undefined —
recorded as null with that reason; -dL/dq does not need it).

**D7 — DETERMINISM (F4).** Three independent full derivations to three paths; the
deliverable's sha256 must be identical across all three; recorded in the receipt.
