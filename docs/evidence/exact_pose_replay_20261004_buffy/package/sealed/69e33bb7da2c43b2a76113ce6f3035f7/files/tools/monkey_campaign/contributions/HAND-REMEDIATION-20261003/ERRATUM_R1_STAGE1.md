# ERRATUM — R1 STAGE 1 claims record (dated 2026-10-05; per the sgt adjudication of the collaborator's dispute)

This is a dated correction entry to the published record (PR #333, merge 28e372ff). Nothing
below edits sealed or published bytes; the correction rides this entry per the record law.
The adjudication anchor: sealed v2.0 receipt 065328e4; stage-1 receipt/report 2b52b55d/ba9a98d8;
runner receipt f4304a68; prereg blob 9213bf7d; amendment blob 018f0bc1 — all read at pin 0c06e093.

## P1 — RE-SCORED: PARTIALLY FALSIFIED as literally frozen (a RESULT, not an error; the run is NOT invalidated)

The frozen text predicted "**every** S0_REJECT_TIP_DEEP row with d in (1.0e-3, 4.0e-3] m whose
deepest vertex lies in the declared pad patch reclassifies to PAD_CONTACT with recorded
u = d − t in (0, 2.0e-3] m; the receipt basis is 954/954 rows inside the window." The sealed
result: 534/954 PAD_CONTACT with u in (0,2 mm]; 292 PAD_ABSORBED (u = 0, no outer-surface
contact — inside P1's scope by depth and witness); 128 PAD_REFUSED_DEPTH. The universal claim
was not met under any consistent reading of "d" (under the receipt basis, 478 of the 954 have
u = d − t ≤ 0 — the frozen text was internally incoherent for half its own basis from pinning
day). "P1 TRUE" as published is revoked.

Three causes, all recorded:
(a) DEPTH-BASIS SWITCH, never declared: the sealed receipt's TIP_DEEP depth is a
FIRST-PROVEN-EVENT depth (the sealed scan "early-exits on the first proven event") while the
pad scan takes the MAXIMUM over pad-covered vertices. Measured delta: median +5.86e-4 m,
max +1.08e-3 m (q_c). This alone moved 128 rows from in-window to refused and shifted every
recorded u by ~0.6–0.76 mm median. The pad-deepest-vertex basis is defensible (it is the
amendment's own C6 control law) but was never named as P1's basis.
(b) THE CONTRADICTION LIST COULD NOT BITE on the observed deviation classes ("any row remaining
TIP_DEEP" is structurally unfireable — no pad class carries that name; the u>u_max and
missing-witness clauses do not reach u=0 rows or refusals). This trips the prereg's own
Concealed-falsification law (§5) and is carried into stage 2's prediction-set requirements:
every named falsifier needs bite-able teeth against the FULL outcome space.
(c) The run is NOT invalidated because the "run is invalid" consequence attached only to the
contradiction list firing (it did not fire), and the instrument-defect presumption is
affirmatively excluded (C6/C7/C10 classify constructed truths exactly; every conversion that
occurred individually satisfies the frozen window+patch+u_max+witness law). Per the prereg's
own disposition law: a falsified frozen prediction is a RESULT.

## P4 — SUSTAINED IN PART

The count-identity clause ("per-posture conversion counts equal exactly the window-and-patch
row counts derived from the sealed receipts") was NEVER IMPLEMENTED in the sealed driver —
the in-run P4 covered battery/identity/arithmetic only; the count clause was verified post-hoc
by review (and holds: 826 satisfied = exactly the in-patch in-window rows). "P4 TRUE" is
scoped to its three executed conjuncts; the count clause is marked post-hoc-verified. Note:
the dispute's own q_zero figures (58/262/66/60) are wrong; the row-accurate classes are
58/262/530/182.

## P2 — DISMISSED (stands; basis clarified)

The run tests the pad-covered depth — a STRICTER basis than the frozen original-d. Zero
satisfied rows exceed 4 mm under either basis at both postures (q_c max 3.6043e-3 sealed).
P2 TRUE stands; the basis equivalence (0/0 discrepancies) is recorded.

## Determinism slice — DISMISSED (wording note)

The pad slice is the SAME instrument as the sealed v2.0 receipt's own determinism_slice
(same-process re-solve, repr-compared, 16 cells), extended to pad rows as frozen. Independent
cross-process replay was never the frozen claim and is not claimed. EVIDENCE wording must not
be read as independent-replay evidence.

## The amendment §2 envelope estimate — SUPERSEDED

The amendment's "646 measured-anchored + 308 extrapolated = 954 convert" estimate is superseded
by the measured split (534 convert: 184 anchored + 350 extrapolated; 292 absorbed at u=0;
128 refused). The estimate also rested on the unnamed first-event depth basis.

## Receipt convention note

The stage-1 receipt's per-posture predictions.update() leaves the top-level P1 block carrying
q_zero's counts (58/262/530/182); q_c's counts live in pad_rows/pad_counters. The raised-cap
revision (already coded) keys per-posture blocks — the fix rides it.

## What stands UNCHANGED (the substantive deliverables)

The survivor verdict PAD_ADMITTED_SURVIVORS_PRESENT_STAGE1; the counts (826/534/292/614/0; 98
survivors); P3 (0/486 opposing-bone conversions — the causes remain separated); the sealed-row
identity gates; the C1–C10 battery incl. the anti-masking control; the force record (forces
only on the 616 PAD_CONTACT rows; absorbed rows carry none); all honest caveats. The original
APPROVE is AMENDED, not withdrawn: the substance stands; the claims-record labels are corrected
by this entry.

## Stage-2 gate

HOLDS until this erratum lands in the published record — and stage 2's prediction set must be
authored against the corrected reading (an explicit absorbed-band prediction; bite-able
contradiction teeth for every named falsifier per §5).

## Retention

The stage-1 seal directory (manifest 0737f0c2, patch 4cf28d15, 13 files) was deleted from
package/sealed/ during the raised-cap work; the publication carries this manifest's hash
records (verified in full by the adjudication and the filed review). Both seals are preserved
going forward.

## Durable lessons (into the campaign law)

(a) A prediction's named contradiction list must be audited for BITE-ABILITY AGAINST THE FULL
OUTCOME SPACE at prereg time — P1's list could not fire on absorb/refuse outcomes, and that
gap produced this dispute. (b) When a frozen prediction cites an instrument quantity ("d"),
the receipt-producing code path for that quantity must be named in the prereg — the
first-event vs deepest-vertex distinction is a basis switch worth 128 row-outcomes.
(c) Per-posture prediction results belong in posture-keyed receipt blocks; last-writer-wins
update() hides the falsifying posture's own counts.
