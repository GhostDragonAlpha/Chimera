# PREREGISTRATION — ONT-A03 (attempt 9435c49896af49d18c70a08ce20138d2)

Frozen 2026-09-27, BEFORE any measurement, transform execution, render or receipt run
of this attempt. Arrival `arrival-bb1ef1a6a3994ca9bb660ad90af78d6d`. Card ONT-A03,
planning id A03. Criteria sha256
`d15183d955c5d3764ed605e4c265145400806e5fb7e67738cebb3cf569056e7d`.
Scope sha256 `01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6`.
Verification profile `anatomy` (`visible_static`), `numerical_evidence_required: true`,
`clean_view_required: true`.

## done_when (exact card clause)

> Architect approves mapping/supersession, historical radius preserved, new
> transforms and regressions qualified

Kind `decision+implementation`. The three clauses are implemented as ONE staged
candidate that the card's own completion clause routes through lead review:
"Lead-approved exact-head PR merged with full ontology qualification evidence."

## Reconciliation (read-only, completed before this freeze)

- ONT-A01 (dependency) DONE/merged (PR #176): ulna volar-side roll sign resolved
  (O1, unanimous no-flip). ONT-A02 (dependency) DONE/merged (PR #181, head
  `dadfda280d7c4abcc403b78f5c5b6ecd8332a402`, merge `970ffe1a`): the radioulnar
  definition, the R1 refutation, the authorized B4 diagnostic (T1–T5 PASS both
  sides + T6 process PASS) and the closed-form before/after radius map are
  presented and independently reviewed.
- A02's merged qualification receipt bounds THIS card verbatim: "a diagnostic PASS
  does not close A03 or authorize mechanically qualified grasp"; "source-kinematic
  fidelity only; R1 refutation retained"; "old radius record, U-ANA, H-BODY and
  every failed alternative remain history". Those bounds are carried, not relaxed.
- The architectural decision left open at I7 (DR-B: the re-anchor's basis) is
  presented by this candidate as a DECISION RECORD with its evidence and bounds;
  in this campaign the operator-appointed connected lead is the architect's
  approval authority for card completion (MERGE_SERVICE.md; the card completion
  clause), so the approval act for this mapping/supersession is the lead's
  merge of this exact head. A lead CHANGES_REQUIRED supersedes it.
- The U-STR record chain (I7 consolidated receipt + ADDENDUM 1, ANATOMICAL
  DECISION TABLE, R1/C1/O1/B4 audits, I7 receipts 00/07/08/09/10, the session-5
  baseline snapshot and the two vendor bone meshes) is extracted BYTE-PRESERVED
  into `reference/` from the MERGED ONT-A02 contribution at base commit
  `2e258b45c9c4e24fa6843a65d9d5324156d10b8d` (branch `astra/gait-capture` of
  `E:/PythonChimera`, read-only `git show`; origin commit/path/blob-sha1/raw-sha256
  recorded per file in `reference/EXTRACTION.json`).
- Base revision of this attempt: `2e258b45c9c4e24fa6843a65d9d5324156d10b8d`
  (attempt checkout branch `branch-2` fast-forwarded to the base head).
- No prior ONT-A03 attempt produced artifacts; this attempt is the first A03
  artifact run.

## Statement (frozen)

Implement the supported ulna correspondence as a STAGED, versioned
mapping/supersession record, without touching any production source, model store,
fit or training body:

1. **Mapping adopted (staged).** The U-STR candidate — P = `body_origin:ulna` ↔
   `elbow_R` (anchor gap 0.0), P_d = `body_origin:radius` ↔ the derived point at
   5.1158 mm from the elbow along the elbow→wrist axis — WITH the O1-resolved roll
   (declared pair source `site:TRIlat-P5` ↔ the shipped `_band_roll` extreme
   vertex; measured residual 0.1535°; the residual SELECTS the pair and is NOT
   validation), exactly as frozen in I7 receipt 00 and passed by the authorized
   B4 diagnostic.
2. **Decision basis (recorded, not relabeled).** The basis for adopting the
   re-anchoring is SOURCE-KINEMATIC CONVENTION FIDELITY — the measured, B4-passed
   consistency of the candidate with the source author's joint-frame convention
   and the forced first-child closure of the shared elbow-region joint. R1's
   refutation of the ANATOMICAL reading is carried VERBATIM into the staged
   record (radial head ≈ 0 % ± 1 % of forearm length, London 1981; Brownhill
   2009; Hollister 1994 — outside the frozen 4–12 % band by ≥ 3.0 points); the
   source convention is NOT presented as anatomical evidence. The selection is
   NOT made for favorable moment arms or any utility (T6 ban carried; no
   moment-arm computation is used in the selection).
3. **Supersession (staged, historical preserved).** The staged record computes
   and records the AFTER radius transforms (both sides): P moves `elbow_R` →
   `ulna.P_d`; uniform scale 0.22170679566544982 → 0.20418868001006546
   (−7.9015 %); span 64.7449 mm → 59.6291 mm; det(full map) = s³; the rigid part
   G and the roll basis Bp unchanged (same edge line, same roll witness); the
   16+16 radius site globals recomputed with max displacement 4.9510 mm
   (`BICshort-P6`) / 4.9484 mm (`BIClong_l-P9`); source locals untouched. The
   superseded set (radius/radius_l `local_to_world` (R, t), the
   max-reconstruction-error record, the experiment step-A mirror table, the
   A4/B4 receipt set) is enumerated as HISTORY; the BEFORE record is preserved
   byte-exact (hash-pinned). NOTHING outside this contribution directory is
   written; the staged record is not applied to any production asset.
4. **Mechanism (executed).** The first-child shared-joint closure
   (`compiler.py:399-423`, `JOINT_EPS = 1e-9` at `:47`) is executed as code
   against the staged inputs: with the ulna edge declared, the FROZEN radius
   record is refused by name (`shared_joint_separation`,
   gap 5.1158 mm ≫ 1e-9) and the staged AFTER record closes the shared joint
   exactly (max separation 0.0).
5. **Regressions.** A CPU-only suite re-runs every staged value against the
   pinned receipts and the property laws (orthonormality, det(L) = s³, on-axis
   P_d, mirror scales, fraction law), the mechanism refusal/closure, the
   preservation invariants, the tendon-coverage effects (PT/PT_l newly defined;
   BRD/BRD_l elbow arms repaired; terminal hand sites still undefined; BIC
   thorax-blocked — receipt 10), and the capture-manifest/bounds contract of the
   anatomy profile.

## Approval semantics (frozen)

This candidate does NOT self-approve. `transforms/radius_supersession_record.json`
carries `status = "STAGED_FOR_ARCHITECT_APPROVAL"`, and the approval act is the
connected lead's merge of this exact head (the card completion clause). The
staged record additionally does NOT claim mechanically qualified grasp: A03's
implementation is the correspondence and its transforms/regressions only; grasp
qualification is G-chain work (G01+).

## Frozen predictions (probe M = execution + re-measurement from pinned inputs)

Identity: every `reference/` file matches `reference/EXTRACTION.json` (raw
sha256); `monkey_birth.bin` sha256 = `550a5b3e…`, `monkey_joints.bin` sha256 =
`74b3ab04…`; the extracted meshes match A02's merged copies byte-exact.

M1 (definition, from the pinned XML alone — inputs still bind): |ulna→radius| =
23.0746 mm ± 0.0005; radius→hand = 292.0294 mm ± 0.0005; elbow→hand = 305.7922 mm
± 0.0005; components 14.324 / 18.088 / 0.301 mm ± 0.0005; obliquity 51.63° ±
0.01; authored fraction 7.5459 % ± 0.001; C1 basis reproduced ≤ 1e-5; arm quats
identity.

M2 (staged supersession vs I7 receipt 08, both sides): before scale
`0.22170679566544982`, span `0.06474489854186721` m, P = elbow_R packet value;
gap `0.005115804490107064` m; after scale `0.20418868001006546`, span
`0.05962909405176015` m, det = s³ within 1e-15, `G`/`Bp` vs packet ≤ 1e-15
max-abs (receipt: 2.22e-16 right / 6.66e-16 left), t after = receipt value
± 1e-9, P_d unchanged, all 16 site deltas per side within ±1e-9 m of receipt 08,
worst sites `BICshort-P6` / `BIClong_l-P9`, scale change −7.901478889180636 %;
BEFORE map reproduces the packet fitted globals ≤ 1e-9 (locals untouched); the
staged record file equals a fresh in-memory recompute (no drift).

M3 (mechanism, executed): `JOINT_EPS` parsed from the extracted
`baseline_snapshot/code/compiler.py` line 47 equals `1e-9`; the refusal name
`shared_joint_separation` appears in the closure block (lines 399–423); executing
the closure check on the frozen record RAISES the named refusal (gap
5.1158 mm > 1e-9); on the staged record the shared-joint separation is exactly
0.0 ≤ 1e-9.

M4 (coverage effects, from receipt 10): scenario counts baseline 2 /
diagnostic_ulna_only 4 / plus-hand (context) 14; in the ulna-only scenario PT,
PT_l, BRD, BRD_l complete with no unresolved owners; ECRB/ECRL/ECU/FCR/FCU (×2)
breaker = hand_r/hand_l; BIClong/BICshort (×2) breaker = thorax; T6 utility-ban
PASS carried and the candidate selection rule is residual-derived (no utility).

M5 (decision record): the staged record quotes the R1 refutation verbatim,
states the kinematic-convention basis, enumerates the superseded set (radius
local_to_world (R, t); max reconstruction-error record; step-A mirror table;
A4/B4 receipt set) as history, carries `status =
STAGED_FOR_ARCHITECT_APPROVAL`, and carries the no-mechanical-grasp bound.

M6 (fraction law, exact-float form): 7.545856…% × 1.0471281884537094 =
7.901478841651782 % (equality ≤ 1e-9); derived distal point = |ulna→radius| ×
k_rad = 5.115804… mm.

## Falsifier (decidable either way, reported as it falls)

Card falsifier: wrong owner/frame, hidden outside placement, clipped/occluded
subject or label ambiguity fails. View toggles must preserve the physical state
hash.

- **F1 identity**: any `reference/` file mismatching `EXTRACTION.json`, or a mesh
  input pin mismatch — recorded, attempt result DISCREPANCY_RECORDED.
- **F2 value**: any M1/M2/M6 check outside its frozen tolerance — recorded as it
  falls; nothing is tuned.
- **F3 visual**: capture manifest structurally invalid, a view's declared subject
  outside its framed panel, a diagnostic/clean pair not sharing camera+state, or
  a clean row carrying diagnostics — recorded.
- **F4 execution/authority**: any write outside this contribution directory, any
  production/source/fit/training mutation, any relabeling of R1's refutation as
  anatomical support, any utility/moment-arm selection, or any claim of
  mechanically qualified grasp — recorded as an attempt failure, not silently
  repaired.

Bound carried from the merged A02 receipt: a diagnostic PASS never closed A03;
conversely this card's implementation does not authorize mechanically qualified
grasp and does not modify the training body.
