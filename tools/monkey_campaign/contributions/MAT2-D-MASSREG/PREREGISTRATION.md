# PREREGISTRATION - MAT2-D-MASSREG (the mass register)

Frozen 2026-09-30, BEFORE implementation and before any register enumeration
or implied-BW execution run. Composed against CARD_STARTER v3 (the 12-gate
batch harness, the evidence-anchoring law, the publication pattern), the
house-standards IMPLEMENTER_CHECKLIST G1-G9 / TOOLKIT P1-P9, FORMAT_SPEC v0
(content addressing: every acceptance-bearing claim names a sha256), and the
card-kit generator pattern (canonical bytes, named refusals, clean-control
falsifier arms). This file exists before the implementation files named in
section 7; at freeze time none of them existed.

## 1. Task identity

- task_id: MAT2-D-MASSREG (registry SHORT form for any manifest/context: D-MASSREG is NOT used - this card has no ontology verification profile; the SHORT form would be `D-MASSREG`, but no capture manifest is produced by this card).
- planning_ids: D-MASSREG. Lead-authored registration card (re-pin ORDER 0),
  successor of the D-W04-MASS lineage; NOT one of the 95 catalog requirements.
- attempt id: 33f33eb7fed04003857b6a3fbaedf9ed
- agent: wk-massreg-d01
- criteria_sha256: fce0e3b30b21ae0f45493fd7d493c9ad694120bb6edc870e1f2cee56f65afa2f
  (identical across dispatch, registry card+attempt, this prereg, and the
  checks identity; to be carried into the publication request args).
- workspace: E:/ChimeraWork/monkey-coordination/kanban-attempts/MAT2-D-MASSREG/33f33eb7fed04003857b6a3fbaedf9ed
- checkout: sparse at tools/monkey_campaign/contributions/MAT2-D-MASSREG/,
  branch-1, prepared head (base) c525b82c7c3ce0128565424764293a3c85811ab3.
- CPU-ONLY card: no GPU queue submission, no training, no runtime. Records
  and offline arithmetic over pinned bytes.

## 2. done_when (verbatim from the card)

"Lead-approved exact-head PR merged with the mass register, the zero-mass-delta proof, and both pinned-audit reproductions. A diagnostic or partial register cannot close this card. This is a lead-authored registration card (arm re-pin adjudication, re-pin step 0), outside the 95-requirement catalog denominator; it gates later mass work, not the goal count."

## 3. Card falsifier (verbatim) + the Lieutenant addendum

"Any mass contributor absent from the register fails. A register total that does not reproduce the pinned audit numbers bit-exact from the pinned producers fails. Any simulation mass value changed by this card fails (zero-mass-delta proof required). A register entry without an evidence anchor fails the write-time gate. Declaring the two systems reconciled into one fails: the adjudication is register, not repair."

ADDENDUM (Lieutenant, 2026-09-30, adopted into this prereg BEFORE the freeze
of section 6's execution): the card owns ONE settling measurement - the
implied-BW evaluation of the Cheng M2-8 segment-mass regressions at the sealed
scene's own segment masses (forelimb 0.812002, hind 1.854, HAT-carved pelvis;
scene f6844eea + the D-W04 mass matrix inputs) with the atlas's uncertainty
discipline. Every scene-side register entry must carry its specimen class,
backed by the measurement receipt (not asserted). If implied BW lands ~9-11
kg: the walk scene is a Cheng-consistent heavier (male-class) animal and the
two-class registration is the close. If implied BW lands inside 5.4-6.9 kg:
Side A's scene is internally inconsistent - NOT repaired; the register records
the inconsistency honestly and flags escalation to the walk-tier scene card,
recorded as a REFUSED-step outcome for the reconciliation claim, not a card
failure.

## 4. Base and reconciliation

- The candidate lineage lives unsquashed in this attempt checkout on branch-1
  at the prepared head c525b82c7c3ce0128565424764293a3c85811ab3 (shared
  object store of E:/PythonChimera; no full clone).
- This card is ADDITIVE-ONLY over
  tools/monkey_campaign/contributions/MAT2-D-MASSREG/ (the checkout's sparse
  path). The zero-mass-delta proof (section 8) asserts repo-wide that no path
  outside that prefix changes between base and candidate head.
- Publication (per CARD_STARTER v3): ONE fresh `Agent:`-trailered commit
  carrying the final card bytes onto the PR base astra/gait-capture, pushed
  as review/MAT2-D-MASSREG; the commit message lists the full lineage. The
  publication head vs the candidate card dir differs by NOTHING (the
  .gitattributes `* -text` is part of the card dir itself). History is never
  rewritten.

## 5. Input pins (sha256 per file; the generator refuses input_pin_drift)

Coordination-space sealed audit bytes (b07-prereqs lane):

| role | path | sha256 |
|---|---|---|
| D-W04 mass matrix | E:/ChimeraWork/monkey-coordination/b07-prereqs/inputs/dw04_mass_matrix.json | 6a32229438f59158a0995b6b90043639e8b103eedf2d09243502faaa9a68ff39 |
| Buffy 02 producer output | E:/ChimeraWork/monkey-coordination/b07-prereqs/inputs/actual_monkey_fit@43b599a7.json | 7b5d6345f6d56ec77c072aecefde2ae592e3bc3fc96b439e5eff164425834268 |
| B03 counted-set material | E:/ChimeraWork/monkey-coordination/b07-prereqs/inputs/b03_material.json | 6e8033f26c823f410eb5beb8fdaaefd4c0c37db61327a86221e087bc832b9ddc |
| B05 port requirements | E:/ChimeraWork/monkey-coordination/b07-prereqs/inputs/b05_ports.json | ef69ee740262cc5783e763517e4d27e0306f31d059b8273bb125486ad7647f3d |
| B06 audit receipt (sealed numbers) | E:/ChimeraWork/monkey-coordination/b07-prereqs/numerical/mass_audit_receipt.json | 3aea85bc7e07ebceb3d1f6f9e969fc9af14edc198620d28ef955da619d351922 |
| B06 audit script (regression arm) | E:/ChimeraWork/monkey-coordination/b07-prereqs/mass_audit.py | 8191f724a6fa3a19dd4f78ac311f8dabaa228b9550aaf968c0c8650ea5e2e886 |
| B06 closure document | E:/ChimeraWork/monkey-coordination/b07-prereqs/READINESS_CLOSURE.md | 94bb88daad6ce964378d5b01a9a6902f53449602912a8f6f8c9a157c339fabb6 |

Implied-BW measurement inputs:

| role | path | sha256 |
|---|---|---|
| Cheng M2-8 regressions | E:/ChimeraWork/research-data/20260929/cheng_tables/M2-8_regressions.csv | b185ee8e98b6e663defed0abd4d004fec053eb6417e027c54801070cd894ec22 |
| Cheng M2-6 mulatta inertials | E:/ChimeraWork/research-data/20260929/cheng_tables/M2-6_mulatta_inertials.csv | 1948a2d8399b5253461c6ed70eed87ea38c5df4083b75437e1e3dbd1a4ce93f3 |
| muscle atlas (discipline source) | E:/ChimeraWork/research-data/20260929/atlas/MUSCLE_ATLAS.md | e51c8bb211ec15ea9fbe84cfb6c8f5dae421d276b48f39b4703936d6c88d1a16 |
| gait benchmark anchor (scene identity) | E:/ChimeraWork/research-data/20260929/gait-benchmark/GAIT_BENCHMARK.md | cb98a8f9ffd67b272215a2e7667bc9dfff99b81fad5eefba5d96263d5d5f851a |
| grasp benchmark anchor (BW band reading) | E:/ChimeraWork/research-data/20260929/benchmark-grasp/GRASP_BENCHMARK.md | d936cebe38b1416dfc417db727ea81396eb8eb9217efed3f05b344db17f71610 |

Scene-side pinned producers (git objects of E:/PythonChimera; extracted at run
time with `git cat-file blob`, sha256-verified against THESE byte pins; the
blob sha1s are the D-W04 record's citations):

| role | git blob (sha1) | commit | sha256 of blob bytes |
|---|---|---|---|
| gait_scene.py (scene builder) | 5c8792aef60f9eb2eb2e10549546ff12a2efe21b | 33e7a444fe7b4c35aa99afe7ef898046877025b4 | 92d3011f7f728c6f6f2dcb40c39497737c4e5af67033c92da6a3b46dd2d42f9d |
| derived_numbers.json (body model) | 8b6d75fbd408a8e1e2db31cdf15fc4a104b9a36a | 33e7a444fe7b4c35aa99afe7ef898046877025b4 | 013810f87a6ca7c1e01916ef7a5454e61e8d0e88f8d6a589fbfdd1514017a173 |
| derive_k_fill.py (OKU total/midpoint) | bfce9681049b7d9354bd498fbf011a633f0ed26f | 33e7a444fe7b4c35aa99afe7ef898046877025b4 | 5150792591a63252abc6a150148b6519b4704abf020e563db5a4a1c20f392bea |
| derive_adjudication.py (band midpoint) | 53c324f354576f32d99bbc67b70fce2dc7744f6a | 33e7a444fe7b4c35aa99afe7ef898046877025b4 | 5912fb21e57d963780a4b81200f8746235243aa64a172f492a8a5820afe2db8b |
| actual_monkey_fit.json (producer bytes) | b76546c2ffbd022639ebeba3fd7dc26d2d5b50bf | 43b599a7c1f11e789cd414b40d7305b9be05066d | 7b5d6345f6d56ec77c072aecefde2ae592e3bc3fc96b439e5eff164425834268 |

Osseous reference family:

| role | path | sha256 |
|---|---|---|
| M02 material regions blob (osim region masses) | E:/ChimeraWork/monkey-coordination/kanban-attempts/MAT2-M02/9abf87253e91484cabbb825acb44a7e3/checkout/tools/monkey_campaign/contributions/MAT2-M02/monkey_arm_regions.json | 15ae0e5a3d540d52b9a0e5c9b8af2f8a6bf7f2c9770a5f2cd7c1e9e8758366f1 |
| re-pin study (adjudication + out-of-scope fixture enumeration) | E:/ChimeraWork/monkey-coordination/re-pin/REPIN_STUDY.md | 99cde4758566784b5b98ad45db19f50beba2c81d8b1761428af19e32290c318b |

The producer fit bytes are doubly pinned: the b07 sealed copy AND the git
object blob hash to the SAME sha256 (verified at prereg feasibility time);
the generator re-verifies both at run time.

## 6. THE FROZEN REGISTER SCHEMA (freeze-before-implementation)

Register document: `mass_register.json`, canonical JSON bytes (sorted keys,
no spaces, ensure_ascii=False, allow_nan=False, UTF-8, LF), schema string
`chimera.massreg.register.v1`.

Per-entry fields (the card's frozen schema, in order of the card text):

1. `contributor_id` - string, dotted namespace `<family>.<name>`.
2. `system` - CLOSED: `scene` | `biological-reference`.
   - `scene`: masses the simulation law consumes or carries (the sealed walk
     scene family and the acceptance-denominator membrane inventory).
   - `biological-reference`: masses that live in biological/specimen reference
     ledgers (the Buffy transported assembly, the B03 counted bone set, the
     osim effective-segment claims, the Turnquist body-weight band).
3. `source_kind` - CLOSED: `pinned-producer` | `det-scaled` |
   `reference-constant`.
   - `pinned-producer`: the value is read bit-copied from a pinned producer
     document/blob at the row's producer_receipt_sha256.
   - `det-scaled`: the value is the producer's `mass_src * |det D|` product
     under the producer's own recorded uniform_constant_density_scale
     assumption (the Buffy non-root bodies; the product is read from the
     pinned bytes, never recomputed to replace them).
   - `reference-constant`: a receipted literature/reference constant (the
     Turnquist band; the B03 authored density).
4. `value_kg` - float, BIT-COPIED from the pinned producer bytes (repr of the
   parsed double recorded in `value_literal`). THE REGISTER CHANGES NO VALUE:
   every entry's value must equal its source bytes' value bit-exactly
   (test T10 asserts per row).
5. `producer_receipt_sha256` - 64-hex sha256 of the exact pinned bytes the
   value was read from (one of section 5's pins).
6. `validation_state` - CLOSED, with frozen semantics:
   - `validated`: the value is bit-anchored to a pinned, receipted source at
     its DECLARED SCOPE (for scene rows: bit-identity with the sealed,
     trainer-consumed scene bytes = scene-scope certification; for the band:
     the receipted Turnquist & Kessler 1989 literature band). The state makes
     NO biological-specimen claim; biological-reading caveats ride
     `validation_note` + `specimen_class` + the gap ledger.
   - `unvalidated-density`: the value's physical reading is gated by an
     unvalidated density/scaling assumption with no measured source (B03
     authored 1800 kg/m3, GAP-4; the producer's
     uniform_constant_density_scale det-scaling, density_validated=false;
     the membrane inventory's authored water-density derivation).
   - `non-physical-reference`: a declared reference/bookkeeping quantity
     excluded from physical admission by its own producer or seal (pelvis
     root_ref_frame_unscaled; osim effective-segment bookkeeping, GAP-8;
     producer-unresolved bodies with zero transported mass).
Honesty fields (required, beyond the card's six):
7. `evidence_anchor` - `{path, sha256}` naming a store-anchored file (the
   write-time gate: NO entry without an anchor). The anchor is the pinned
   producer copy or receipt the row was read from, anchored through
   evidence-store anchor.py (store-relative path + sha256).
8. `validation_note` - one-line honest scope statement.
9. `specimen_class` (scene-side rows only) + `specimen_class_receipt_sha256`
   - the class assigned by section 7's frozen decision rule, backed by
   `implied_bw_receipt.json`'s sha256 (never asserted without it).
10. `role` - flags carried from the pinned sources (e.g. is_training_body,
    is_cot_denominator, counted/excluded status, counted_set membership).

Top-level register keys: `schema`, `card`, `attempt_id`, `criteria_sha256`,
`composed_against`, `law` (register-not-repair statement + the
never-reconciled clause), `input_pins` (section 5 table),
`systems` (the two system definitions, declared DISTINCT: the register does
not reconcile them), `entries` (the rows), `totals` (section 8's numbers),
`subsumption_hazard` (carried verbatim-class from the B06 audit),
`declared_out_of_scope` (the demonstrator-fixture ledger), `gaps` (the mass
gaps this register carries, by the re-pin study's GAP ids), `zero_mass_delta`
(the proof receipt's identity), `determinism` (canonical bytes law).

## 7. THE FROZEN ENUMERATION + IMPLIED-BW MEASUREMENT DESIGN

### 7.1 Families and frozen counts (counts are producer-derived facts read at prereg feasibility time; the generator refuses count_mismatch if a pinned producer yields a different count)

- `scene.walk` - 14 bodies from gait_scene.py @33e7a444 (blob 5c8792ae):
  ground 0.0 (declared zero), pelvis = 8.184 - 2x0.406001 = 7.371998,
  thigh_l/r 0.557, shank_l/r 0.269, foot_l/r 0.08, toe_l/r 0.021,
  upperarm fore_l/fore_r 0.2737, forearm fore_l/fore_r 0.1323.
  All source_kind pinned-producer, validation_state validated (scene scope),
  with the builder's own GAP-3 confession carried on the four strut rows
  ("measured total arm mass and documented lengths; the quad-share lane's
  admitted hind-thigh:shank split supplies the two segment masses").
- `scene.acceptance_denominator` - 1 row: 13824.5 kg (D-W04 masses[0];
  13.824536 m^3 sealed matter cells at authored water density 1000 kg/m^3;
  is_training_body=false, is_cot_denominator=true), validation_state
  unvalidated-density.
- `buffy.transported` - 9 rows from the pinned producer fit (file order):
  pelvis 11.777 (root_ref_frame_unscaled, det_scale 1.0) ->
  non-physical-reference; then 8 det-scaled bodies -> unvalidated-density:
  femur_r 1.4354939022274895, tibia_r 0.3541672062742369, femur_l
  1.4354939973493177, tibia_l 0.3541671966276213, humerus 0.8339432683327799,
  radius 0.007944462945010423, humerus_l 0.8338240132524405, radius_l
  0.007944462945010423.
- `buffy.unresolved` - 9 declared-zero rows (hand_l, hand_r, talus_l,
  talus_r, thorax, toes_l, toes_r, ulna, ulna_l): value 0.0,
  non-physical-reference, note "producer unresolved, zero transported mass,
  not silently repaired (B06 CHK-8); the B05 carried-load question has no
  transported backing".
- `b03.counted` - 7 matter rows of the pinned B03 document: five counted
  bones (clavicle 0.002358233719760561, humerus 0.0225084266484900514,
  radius 0.0091005148022984695, sternum 0.000476879050472354905, ulna
  0.0102583395334129614) at authored density -> unvalidated-density; shell_hand
  and shell_scapula 0.0 (zero by refusal) -> non-physical-reference.
- `b03.density` - 1 row: 1800.0 kg/m3 (band [1650, 1950]), reference-constant,
  unvalidated-density (GAP-4; no gravimetric source exists, Astra gap).
- `osim.regions` - 7 rows from the M02 regions blob: clavicle 0.0, hand 0.049,
  humerus 0.203, radius 0.0618, scapula 0.0, sternum 6.6, ulna 0.0922; system
  biological-reference, pinned-producer, non-physical-reference (authored
  effective-segment bookkeeping; GAP-8 for sternum 6.6; the 0.406 kg free-limb
  subset is the B06 EXCLUDED-claims family, screened INSIDE-1SD by S-MASS-05,
  never validated for this specimen; counted=false on every row).
- `reference.turnquist` - 3 rows: band low 5.4, midpoint 6.15, high 6.9 kg;
  reference-constant, validated (receipted adult-female M. mulatta band,
  Turnquist & Kessler 1989; D-W04 masses[2]; derive_adjudication.py
  BAND_MIDPOINT_KG; derive_k_fill.py AF_MIDPOINT_KG). This is the adjudicated
  body-mass REFERENCE for every BW-normalized claim (re-pin study section 3).
- `declared_out_of_scope` (NOT register entries; completeness ledger):
  M03 membrane 0.05 kg, M05 fixture bodies 0.05/0.02/0.002 kg, M07/M08
  fixture masses (0.02/0.02/0 x2) - synthetic_authored demonstrator fixtures,
  not contributors to either registered system; enumerated by REPIN_STUDY
  sections 1.5-1.8, anchored to that document's sha256.

Total frozen register rows: 15 scene-side (14 walk + 1 denominator) + 18
buffy + 8 b03 + 7 osim + 3 reference = 51, plus 7 declared-out-of-scope rows.

### 7.2 Frozen totals (all reproduced bit-exact from pinned bytes at run time)

| total | frozen value (literal) | source of truth |
|---|---|---|
| scene certified body total | 10.038 | D-W04 masses[1].kg; derived_numbers body_model.mass_kg |
| scene carve sum | 10.037998 | D-W04 masses[1].derivation_recomputed; GAIT_BENCHMARK.md scene f6844eea model sum |
| buffy all_transported | 17.039978509953905 | pinned producer fit admission.totals_mass_kg; B06 audit CHK-4 |
| buffy transported_under_assumption | 5.262978509953907 | same, CHK-2 |
| buffy root reference share | 0.6911393692850295 | 11.777/all_transported, CHK-9 |
| b03 counted set | 0.0447023937544344 | b03 counted_set.counted_total_kg; B06 R-MASS-01 |
| osim excluded claims (free limb) | 0.406 | B06 CHK-8 excluded_osim_segment_claims_kg |
| turnquist midpoint | 6.15 | D-W04 masses[2].kg |

Float-order law (declared BEFORE the run; feasibility-checked at prereg
time in float64): (a) body-model order 8.184 + 2x(0.557+0.269+0.080+0.021)
== 10.038 BIT-EXACT; (b) carve order (8.184-2x0.406001) + 2x0.927 +
2x(0.2737+0.1323) == 10.037998 BIT-EXACT; (c) the builder's ordered 14-body
sum (ground first, builder body order) evaluates to 10.037998000000004 -
NOT bit-equal to the carve literal; the register records this honestly as
`builder_order_sum` with the mass_audit FLOAT_FLOOR discipline (1e-12
relative), and the sealed totals remain the pinned literals (a) and (b);
(d) the buffy sums use the mass_audit CHK-2/CHK-3 declared order over the
pinned file's row order (bit-exact, max_abs_diff 0.0 expected); (e) the
strut pair sum 0.2737+0.1323 = 0.40600000000000003 != 0.406001 (the carve
constant) - recorded honestly on the strut rows.

### 7.3 The implied-BW measurement (FROZEN DESIGN - executes AFTER this commit)

Method (atlas section 5 discipline): implied BW (kg) = (mass_g - b_g) /
(m_g/kg) from the M2-8 `Segment mass` m/b rows. The M2-8 hand row carries NO
significance mark (transcription: Segment mass p = UA*, FA*, Hand empty,
F+H*) and is the atlas's named high-leverage stress row.

Predeclared evaluation rows (ALL run; none post-hoc):

- E1 upper_arm at the scene upperarm strut 273.7 g. Declared
  split-dependent: the 0.2737/0.1323 split is the admitted hind-borrowed
  split (GAP-3).
- E2 forearm at the scene forearm strut 132.3 g (same caveat).
- E3 hand at the scene hand mass - NOT EVALUABLE, named refusal
  `hand_row_no_scene_mass`: the sealed scene carries no hand segment (the
  builder's forelimb is two struts; contact points are not mass bodies).
- E4 PRIMARY, split-free: the per-arm carve mass 406.001 g (the only scene
  arm quantity with a source: the Oku HAT carve, builder lines 70-72)
  against the summed upper_arm+forearm M2-8 coefficients (m = 34.4 + 22.4 =
  56.8 g/kg, b = 23.0 + 17.5 = 40.5 g). The hand row is NOT consumed in the
  primary because the scene arm carries no hand segment (declared here, not
  silent). Linear-coefficient summation assumes conditional independence of
  segment errors given BW (atlas A4 analog: correlations NOT modeled).
- E5 secondary disclosure variant: summed upper_arm+forearm+hand
  coefficients (m = 59.57, b = 75.9) at 406.001 g - the stress variant that
  consumes the not-significant hand row; recorded as stress only.

Calibration checks (regression validity class, atlas reproduction):
- C1: the M2-6 means (upper arm 294 g, forearm 194 g, hand 57 g) inverted
  through the M2-8 rows must reproduce the atlas's 7.88 / 7.88 / 7.80 kg at
  the atlas's printed precision (its section 5 flags).
- C2: the sealed osim claims (humerus 203 g, radius+ulna 154 g, hand 49 g)
  must reproduce the atlas's implied-BW row values 5.2326 / 6.0938 / 4.9097
  kg at its printed precision.
- C3: the scene strut masses vs the M2-6 bands (294 +/- 119, 194 +/- 78 g):
  z-scores and the atlas t-PI (n=6, df=5, t=2.570582, sqrt(1+1/6)=1.080123,
  multiplier 2.776546) computed and recorded; atlas assumptions A1-A5
  carried verbatim-class; M2-8 prints no dispersion, so every implied-BW
  number is recorded as an UNCERTAINTY-UNCALIBRATED order-of-magnitude
  screen (atlas A5), never as a calibrated bound.

Decision rule (applied to E4-primary ONLY; frozen before the run):
- E4 in [9.0, 11.0] kg -> scene specimen_class
  `cheng-consistent-male-class`; the two-class registration is the close;
  both classes registered.
- E4 in [5.4, 6.9] kg -> scene specimen_class
  `internally-inconsistent-female-band`; the register records the
  inconsistency honestly and flags escalation to the walk-tier scene card;
  the reconciliation claim records the REFUSED-step outcome with refusal
  code `reconciliation_refused_internal_inconsistency`; nothing is repaired.
- otherwise -> scene specimen_class `intermediate-unresolved`; no
  reclassification; the measured tension is recorded.
The class is recorded on EVERY scene-side register row (system-level class;
per-row evaluation values ride the receipt). The receipt
(`implied_bw_receipt.json`, schema `chimera.massreg.implied_bw.v1`) carries
every input pin, every evaluation row, the calibration checks, the decision
inputs and the applied branch.

### 7.4 Falsifier arms (bite suite; tampered copies in attempt scratch, never committed; each arm: clean control FIRST, named premature guard, receipt row)

- FA1 `massreg_fb1_row_omission_bites`: delete one Buffy transported row from
  a scratch register copy -> the completeness check must FAIL (family count
  and total both break).
- FA2 `massreg_fb2_value_perturbation_bites`: perturb one scene value
  (10.038 -> 10.0381) in a scratch copy -> the bit-exact reproduction check
  must FAIL.
- FA3 `massreg_fb3_anchor_mismatch_bites`: corrupt one entry's
  evidence_anchor sha in a scratch copy -> the anchor gate must FAIL.
- FA4 `massreg_fb4_reconciliation_declaration_bites`: tamper the register
  law field to declare one reconciled system -> the register-not-repair
  check must FAIL.
Preflight: the tampered fixtures must discriminate (clean copies pass all
four checks first in the same executable; guards
`massreg_fb<n>_premature`).

## 8. Zero-mass-delta proof (frozen)

`zero_mass_delta_receipt.json` (schema `chimera.massreg.zero_delta.v1`)
records, executed at the candidate head:
- Z1: `git diff --name-status <base>..<head>` - EVERY changed path is under
  tools/monkey_campaign/contributions/MAT2-D-MASSREG/ (base
  c525b82c7c3ce0128565424764293a3c85811ab3).
- Z2: each section 5 git-object producer blob re-extracted at base AND at
  head - sha256 equal (the producers are historical pins; the card changes
  no byte of them).
- Z3: the totals recomputed from the pinned producer bytes at the candidate
  head equal the SEALED b07 receipt numbers bit-exact (17.039978509953905 /
  5.262978509953907 / 11.777; mass_audit_receipt.json sha
  3aea85bc7e07ebceb3d1f6f9e969fc9af14edc198620d28ef955da619d351922) and the
  scene literals equal D-W04 masses[1] bit-exact (10.038 / 10.037998).
- Z4: per-register-row bit-copy law - every entry value equals its source
  bytes' value (the register repairs nothing).

## 9. Declared gates, execution modes, and report law

Generator `build_register.py` modes (canonical() byte law; named refusal
codes; no wall-clock in receipts):
- `main` - verify pins; enumerate; classify; compute totals in the declared
  orders; run the implied-BW measurement; write `mass_register.json`,
  `implied_bw_receipt.json`, `zero_mass_delta_receipt.json`,
  `enumeration_receipt.json` (schema `chimera.massreg.enumeration.v1`).
- `rerun` + `compare` - register byte-identity determinism (X2: the register
  file is the determinism unit; receipts compared with declared augmentation
  keys only).
- `falsify` - the four FA arms (scratch tampered copies; clean controls
  first) -> `falsifier_receipt.json`.
- `regression` - the sealed b07 mass_audit.py re-run UNMODIFIED at the
  candidate revision (exit 0; its receipt byte-stable) ->
  `regression_receipt.json`.

Named-check suite `test_massreg_checks.py`: one check per done_when clause
(T1 schema, T2 field/vocabulary gates, T3 specimen-class backing, T4 buffy
totals bit-exact, T5 scene totals bit-exact, T6 b03 counted bit-exact, T7
zero-delta receipt green, T8 register-not-repair, T9 implied-BW receipt +
calibration, T10 per-row bit-copy), plus the four FA arms asserted with
clean controls. ZERO skips planned; the claim will state `N executed,
0 skipped`.

Report: GENERATED by `make_report.py` from the receipts only (done_when
clause map, determinism, falsifier proof with clean controls, the
implied-BW verdict and its branch, amendments, honest limitations, file
identities). `lint_report_numbers.py` (+ `--selftest`) enforces
printed-precision traceability of every report number (P2).

Nonvisual rationale (predeclared): records/offline card over pinned bytes -
no rendered scene, no camera, no verification profile exists on this D-card;
visual evidence classes do not apply. Numerical + independent review remain
required.

Evidence anchoring: every artifact referenced by the register/receipts is
anchored through `evidence-store/anchor.py add <file> --card
MAT2-D-MASSREG` (write-time gate); reference fields carry one path + one
sha256, never prose.

## 10. Refusal codes declared now

`input_pin_missing`, `input_pin_drift`, `producer_blob_missing`,
`producer_blob_drift`, `count_mismatch`, `row_absent_from_producer`,
`value_not_bit_copied`, `anchor_missing`, `anchor_sha_mismatch`,
`specimen_class_unbacked`, `hand_row_no_scene_mass`,
`reconciliation_refused_internal_inconsistency`,
`register_total_mismatch`, `non_card_path_changed`, `vacuous_comparison_refused`.

## 11. Known limits declared now

- The register registers; it does not admit. No R-MASS-04-style lead
  decision is recorded or implied by this card; the Buffy quantities stay
  uncounted; the two systems stay DISTINCT ledgers.
- The implied-BW number is an uncertainty-uncalibrated screen (atlas A5),
  recorded as the addendum's classification evidence, not as biology.
- GAP-1 (muscle fiber/tendon placeholders), GAP-5 (palm friction), GAP-6
  (lawful absence of attachment stiffness), GAP-7 (no muscle mass/PCSA),
  GAP-9 (missing duty-factor channel) are OUT of this card's mass scope;
  GAP-2/3/4/8 are carried by the register's gap ledger.
