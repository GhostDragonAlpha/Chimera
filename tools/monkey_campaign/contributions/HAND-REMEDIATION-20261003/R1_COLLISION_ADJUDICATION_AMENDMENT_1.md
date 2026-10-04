# R1 COLLISION-ADJUDICATION AMENDMENT-1 (DRAFT) — the pre-run corrections from the live audit (the fold defects; the anchor classification; the pad phrasing; the adapter)

Status: DRAFT authored by `wk-hand-remediation` for the Lieutenant's pin
(separate-first; PRE-RUN — the adjudication is ON HOLD: no geometry
execution until this amendment is pinned AND the corrected implementation
passes review). The pinned prereg bytes (adc41045 / `1362f92f...`) are
never edited; this amendment corrects them per the live audit.

## 1. THE THREE FOLD DEFECTS (the audit's findings; fixed in the implementation)

The original driver folded three independent readings into one another,
violating the prereg's own closed-outcome-space law. THE FIXES (applied to
`run_collision_adjudication.py`, unsealed, awaiting review):

1. SELF-PENETRATION FOLDED INTO THE TRUNK CLASS: the driver derived ONE
   candidate class from `pen_pairs or self_genuine` conflated. FIXED: the
   trunk reading and the self-collision reading are SEPARATE named
   components (`components.trunk_class`, `components.self_class`) recorded
   per candidate; the candidate class follows the DECLARED precedence
   (any component GENUINE -> GENUINE_PENETRATION with the source named;
   else any component UNRESOLVED -> UNRESOLVED_GEOMETRY; else
   COLLISION_CLEAR). The components make the fold impossible to hide.
2. SELF TOUCHING/UNRESOLVED DISCARDED: the driver retained only the
   GENUINE self rows in the summary. FIXED: every adjudicated self row is
   retained with its class (GENUINE, TOUCHING, UNRESOLVED alike), the
   posture summary carries the full class breakdown, and the per-candidate
   record carries the touching and unresolved pair lists.
3. THE L1 PAIR ROWS OMITTED: the driver emitted only the adjudicated
   proxy-overlap subset. FIXED: the FULL Level-1 pair rows (all 190 pairs
   per posture: distance, radius_sum, clearance, adjacent, proxy_overlap)
   are retained in the receipt (`level1_pair_rows_retained`).

## 2. (a) THE S5-P3 ANCHOR CORRECTION (the frozen prediction is wrong as written; amended)

S5-P3 AS FROZEN said: "ZERO UNRESOLVED_GEOMETRY on the bone-vs-trunk
pairs... the class is reserved for anchor-envelope rows (recorded
separately)". THE CORRECTION: the anchor-vs-TRUNK pair is an ORDINARY
represented-surface adjudication with the ordinary three surface classes
(CLEAR/TOUCHING/GENUINE_PENETRATION) — it is NOT an UNRESOLVED source.
Stage 1 ALREADY adjudicated it (every raised-cap survivor row carries its
`anchor_envelope` record) — the adjudication RE-EMITS and VERIFIES those
rows for complete coverage; the anchor is never labeled newly-omitted.
The `UNRESOLVED_GEOMETRY` class properly applies to the ANCHOR-vs-BONE
pairs (the coarse 1920-point envelope vs the bone meshes — the instrument
declaration's own source-fidelity class), which the full self-collision
sweep covers (the anchor is in the 190-pair grid). AMENDED S5-P3: zero
UNRESOLVED outcomes at the candidate level; any UNRESOLVED component
(anchor-vs-bone) yields the candidate class UNRESOLVED_GEOMETRY, recorded
and routed. TEETH unchanged in kind: the counts close; any unnamed state
refuses.

## 3. (b) THE PAD PHRASING (the post-hoc classification law)

S5-P1's basis is RE-WORDED: "the strict represented-BONE adjudication
will find penetration" — each admitted candidate's bone vertices sit
(pi_c, 4.0e-3] m inside the trunk and the strict instrument reads the
bone against the UNOFFSET trunk surface. RECORDED beside it: the possible
VPL-1 geometry-law READING — the pad model's invariant is bone clearance
vs the OFFSET surface (trunk offset inward by t), a DIFFERENT quantity
from the strict bone-vs-unoffset-trunk distance; the two coexist and are
never conflated. THE RAISED-CAP RUN's pad classes were POST-HOC
CLASSIFICATION, never a physically-added mesh; NO CLAIM that pad contact
was physically resolved exists anywhere in this lane's records, and none
may be derived from this adjudication.

## 4. (c) THE PAD-SUBSTITUTED RIGID BONE IN THE FULL GEOMETRY RECORD

The audit's concrete omission: the raised-cap driver removed the
pad-substituted body from its exact-adjudication set
(`check_set.discard(pad_bone)`), so the stage-1/raised-cap receipt's rows
do not carry that bone's strict class. THE STAGE-1 RECEIPT BYTES STAY
FROZEN (never edited). THE ADJUDICATION driver emits ALL 19 bones per
candidate UNCONDITIONALLY (the pad-substituted rigid bone included in the
full geometry record: `strict_trunk_classes` covers every bone; the pad
body's own strict class is the S5-P1 reading). The stage-1 omission is
thereby COMPLETELY COVERED by the adjudication's own record — the receipt
bytes are not retrofitted.

## 5. (d) THE ADAPTER (deterministic; class-scoped tolerances)

THE ADAPTER IS THIS LANE'S OWN DRIVER: it consumes the stored
(posture, theta_index, mirror, o, u) tuples directly from the pinned
raised-cap receipt and replays them EXACTLY (no re-solving, no re-
derivation of the placement). TOLERANCES ARE CLASS-SCOPED: tau = 1.0e-4
applies to ALL pairs (the instrument's contact tolerance); pi_c = 1.0e-3
belongs ONLY to the declared distal_thumb/distph3 contact segments of the
stage-1 PLACEMENT predicate and is NOT applied in the strict collision
classes; r_joint = 5.0e-3 lives ONLY inside the 19 certified joint-region
scopes of `adjudicate_pair`. THE 40 q_zero rows are COMPARISON POSTURES,
labeled as such, never substitutes for the q_c family.
NOTE 2 (the reviewer's ruling on the reconciliation scope): the
as-frozen per-(theta, mirror) reconciliation against the R2 rows is
IMPOSSIBLE without adding the R2 receipt as an input (the sealed v2.0
receipt carries no r2 key). THE LAWFUL RESOLUTION, ADOPTED: the labeled
summary (the two families named, the construction offsets recorded) PLUS
the evidence-verified ranges (q_c 2.83-9.63 mm; q_zero 25.6-26.0 mm)
STAND AS THE RECONCILIATION RECORD; the families structurally never
conflate (the reviewer verified the R2 rows are unused in the
classification); and AT MINIMUM the driver emits the EXPLICIT unmatched
q_zero count = 40 (implemented, per the review's floor).
REFERENCE NOTE (the Buffy-Freebuff offer, attributed proposal-only): the
review-only replay-package offer was sought for its adapter design; its
bytes were not locatable in this lane's reachable stores at authoring
time. Adoption stays in THIS lane under THIS prereg; NO external code
enters the sealed package unreviewed; the uncredentialed identity holds
no dispatch/admission/release authority.

## 6. THE HOLD (honored) AND THE REVIEW GATE

The pre-correction local dev run was STOPPED mid-execution when the HOLD
arrived (the process killed; pid 84100); its earlier completed attempt
(exit 0, the summary-crash state) is PRESERVED as a dev artifact under
the hold and is NEVER citable as an adjudication outcome. THE REVIEW
GATE: the corrected implementation + this amendment go to Sergeant
review BEFORE any seal or run. The seal-store capture applies at the
post-review seal. Anti-tuning unchanged; the outcome space remains
closed; the erratum's governing P1 label carried.

## 7. GOVERNANCE

Authored by wk-hand-remediation; DRAFT for the Lieutenant's pin
(pre-run). The implementation revision pins THIS amendment's committed
sha next to the prereg's and refuses on drift. No merge/review authority
claimed; the uncredentialed external identity holds no authority here;
author self-review certifies nothing.
