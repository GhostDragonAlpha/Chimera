# PREREGISTRATION — MAT2-A09 "Issue the grasp anatomy input package"

Preregistered 2026-09-30 by the Worker-implementer (agent id
chimera-worker-A09, attempt 2c3a18f2fa494ce1a06ca691dd9fe03c) BEFORE authoring
the package generator, validator, falsifier probes, report or any capture
frame. This file is committed ALONE, before any implementation artifact, so
the freeze is git-provable (separate-first). Inputs were read read-only from
the pinned sources at the sealed tip; every count below was computed from the
pinned bytes BEFORE this freeze and is the exact statement the deliverables
must reproduce.

Composed against CARD_STARTER.md v2 (v1 base + v2 evidence-anchoring and
sequential-banking additions), house standards IMPLEMENTER_CHECKLIST.md
(G1-G9) and TOOLKIT.md (P1-P9), card-kit (batch_gates.py 9 CPU gates;
templates), FORMAT_SPEC.md v0 and CODEC_STANDARD.md.

## 0. Existence statement (what did NOT yet exist at freeze)

At this commit, none of the following existed: `grasp_package.py`,
`grasp_package.json`, `qualification_receipt.json`,
`evidence/falsifier_receipt.json`, `make_report.py`, `report.md`,
`lint_report_numbers.py`, `test_grasp_package.py`, `capture_package.py`, any
`evidence/` file, `capture/` file, or the card `.gitattributes`. No packaging,
closure, conservation or classification computation for this card had been
run except the frozen counts quoted in section 7 (computed once from pinned
bytes to freeze them; the validator recomputes them from bytes and refuses
any disagreement). No GPU job is planned: this card's scope is CPU-only
packaging + a 2D static capture (declared in Honest limitations).

## 1. Task identity

- Task: MAT2-A09 (planning id A09) — "Issue the grasp anatomy input package";
  kind `integration`, group "Anatomy and grasp prerequisites".
- criteria_sha256: `f56d4ddbb0cf92a0897d30cda743a37554d9d7a30c6d69f151c6b41360f6026f`
  (identical across the dispatch, the card and the attempt in
  `E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3` read mode=ro;
  asserted equal again at capture time).
- scope_sha256: `cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`
- definition_raw_sha256: `57ded6eb2f2cc6aa914d6f68c8efb55b215790fc7a9d0baa5dfd2c49fd1465c1`
- Attempt: `2c3a18f2fa494ce1a06ca691dd9fe03c`; agent id `chimera-worker-A09`.
- Verification profile (read mode=ro from the registry, G7/P7): id `anatomy`,
  kind `visible_static`, subject "Creature structure, bone/muscle/skin
  correspondence and attachment ownership", `numerical_evidence_required:
  true`, `clean_view_required: true`, `camera_required_fields` = 16 fields,
  nonvisual_reason: null — CAPTURE IS REQUIRED for this card (unlike A08's
  records/offline profile).
- Base: line tip `ee2bcb98cd627b796662edaf9ad75b8c1f7f7be5` (= merge of PR
  #274, MAT2-A08 = `origin/astra/gait-capture`); attempt branch
  `codex/monkey-mat2-a09-2c3a18f2fa49` cut from the tip; publication branch
  `review/MAT2-A09`, PR base `astra/gait-capture`.
- Provisioning disclosure: `worker_checkout.prepare` failed at its slot-branch
  fetch step (remote branch-2 7effbcf8 and the source clone's copied ref
  aa669cfd have diverged; NEITHER is an ancestor of the tip — both carry dead
  M10 slot history). Provisioning was completed manually in the attempt's
  private shared clone only, following the two sealed precedents (A07
  fast-forwarded its prepared slot base to the sealed tip before any edit; A08
  worked a codex/monkey-mat2-a08-<attempt> branch cut from the tip and
  published to review/MAT2-A08). Recorded in `checkout_identity.json`.
- task_id SHORT form used everywhere in generated artifacts: `A09`.

## 2. done_when (verbatim) and binding observations

done_when (verbatim): "One versioned package carries supported mappings,
parameters, provenance and explicit gaps. Material-first addition: Package
the skeletal/tissue/interface graph and each explicit reduction; removal of
represented tissue must remove its mechanical connection."

Card observation (verbatim): "Anatomy completion does not itself prove
climbing."

Card falsifier (verbatim): "Wrong owner/frame, hidden outside placement,
clipped/occluded subject or label ambiguity fails. View toggles must preserve
the physical state hash."

Profile falsifier (verbatim): identical text.

## 3. Lawful-close discipline (declared BEFORE packaging)

- The package is a DERIVED, VERSIONED, CARRIED document built ONLY from
  pinned sealed upstream bytes. It invents NO anatomy, NO constant and NO
  mapping. Every row keeps its sealed provenance class; no provenance class
  is upgraded.
- The sealed A07 law binds this card: placement terminal vocabulary is exactly
  {supported, explicitly_unresolved}; no fitting experiment is run or
  simulated; the emitted document refuses `fitted*`/`optimized*` keys; the
  carried Candidate C observation is carried verbatim, still
  explicitly_unresolved.
- The sealed A08 law binds: biological vs engineering namespaces stay disjoint
  by identity; no density/stiffness/activation law from geometry alone; the
  39/15 registry rows and U1-U8 unresolved entries are carried verbatim-class,
  never repaired.
- The sealed M09 law is the runtime precedent for the material-first removal
  clause: explicit release removes ALL bond-type connective material bitwise
  (M09 T4, measured). This card carries that semantics as the declared removal
  law of the packaged graph and proves the STATIC closure numerically; it runs
  no dynamics.
- C17 stays OPEN exactly as A06/A07 left it (same required_inputs; zero
  stiffness/couple numbers); C01/C05/C06/C18 are registered OPEN-INVENTORY
  exactly as the completion map records them ("no new numerical result
  claimed").

## 4. Base, reconciliation and dependency INPUT PINS (sha256 per file)

Base head `ee2bcb98cd627b796662edaf9ad75b8c1f7f7be5` equals the sealed line
tip; attempt branch is a fresh branch at that sha (no other commits exist on
it at freeze). Repo inputs are read from the candidate commit's working tree
(sparse checkout of the named contribution dirs); host inputs are read at
their absolute pinned paths. The generator verifies every pin against on-disk
bytes before any emission and refuses `input_pin_drift` on mismatch.

| role | file | sha256 |
|---|---|---|
| A06 ownership registry (paths/attachments/bonds/containment/endpoints) | repo `tools/monkey_campaign/contributions/MAT2-A06/attachment_ownership.json` | `f1f0430772258e8449fc354841becf2f1869783399e63f3f145565b8d0b1041c` |
| A07 placement resolution (terminal states, envelope test) | repo `tools/monkey_campaign/contributions/MAT2-A07/placement_resolution.json` | `cd596d7c21fa81a4c2632e13b63ba26e62da51d44eca2355147fd5dff1587490` |
| A08 parameter envelope (39 bio rows, 15 eng rows, U1-U8) | repo `tools/monkey_campaign/contributions/MAT2-A08/parameter_envelope.json` | `2fb43fd44f13e8b927142d72b79d36246ee7d71fd954a39ffeb12b74dc716424` |
| A05 mutant hand structure (19 digit bodies, anchors, envelope) | repo `tools/monkey_campaign/contributions/MAT2-A05/mutation_structure.json` | `48b037593f63ec473947d787077ab6fbcd3b364afd15765bff508e7d54f45649` |
| M02 pinned arm model (osim; 39 actuators; the A08/A06 source of record) | repo `tools/monkey_campaign/contributions/MAT2-M02/data/macaque_arm/monkeyArm_current.osim` | `4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895` |
| M02 pinned graph rows (whole-arm body frames, geom pins, scope) | repo `tools/monkey_campaign/contributions/MAT2-M02/data/graph_pins.json` | `849f9988d1a6ccb451bb45d79f298dd954c4e5605acd19d7d882a5c70a285b97` |
| M03 active-pressure carrier (authored membrane constants) | repo `tools/monkey_campaign/contributions/MAT2-M03/pressure_state.json` | `8182da4720f26154dfff3c54711e66cb318cc7bb9c989de77b7ee0a2f2b2ec03` |
| M04 arm passive-law carrier (7 regions rigid-by-declaration) | repo `tools/monkey_campaign/contributions/MAT2-M04/arm_rigid_laws.json` | `a9e971db4b36c1a6c35f9c27171ebd06787d5ffc96d58cd4b039e9e4e7f02d32` |
| M05 interface-exchange state (bond/contact port semantics carrier) | repo `tools/monkey_campaign/contributions/MAT2-M05/interface_state.json` | `c09bdf0564d152fa8b9a41489bd874fd0570f75e40ed3ce848f4c474fd0320c6` |
| M09 loose-bones demo receipt (X1_pass, T1-T10 probes) | repo `tools/monkey_campaign/contributions/MAT2-M09/experiment_receipt.json` | `b949374dd9a9b7918daf179d0bf415ab88e1032d52721c8fb794abe31b6ccf24` |
| M09 loose-bones trace (bound/release docs, declaration) | repo `tools/monkey_campaign/contributions/MAT2-M09/experiment_trace.json` | `273dbc4f8c73a6f562c0260050f7d23012288af29426f4d7b8a191b35efeb744` |
| osim source of record (host copy, identity with the repo pin) | host `E:/PythonChimera/tools/science_funnel/data/macaque_arm/monkeyArm_current.osim` | `4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895` |
| hand envelope geometry (capture context) | host `E:/PythonChimera/tools/science_funnel/data/macaque_arm/Geometry/hand.vtp` | `a06ea7e079c849df07d6eec001e9bcc2ea193ecd3914011c78a993a5faa94fc6` |

Runtime verification refuses `input_pin_drift`.

## 5. What the deliverable IS (declared in advance)

ONE versioned package document, `grasp_package.json`
(schema `chimera.a09_grasp_anatomy_package.v1`, revision 1, canonical JSON,
stable ids, `object_id mat2_a09_grasp_anatomy_package`), built by
`grasp_package.py` from the pinned inputs; one validator with named refusals
(--verify recomputes every carried classification/closure from the pinned
bytes and refuses disagreement); one falsifier suite (tamper arms with clean
controls); the visible_static capture (PNG sheet + manifest/context/validation
receipt) bound to the package document sha; `qualification_receipt.json`
(schema `chimera.qualification_receipt.v1`) mapping every done_when clause to
its evidence; `report.md` GENERATED by `make_report.py` from receipts only
(zero hand-transcribed numbers), policed by `lint_report_numbers.py`
(+`--selftest`); named checks in `test_grasp_package.py` (unittest).
Determinism: two consecutive `--emit` runs are byte-identical (sha256 equal).

The upstream registries are READ-ONLY to this card: no upstream byte changes,
no rebuilt variants; separation asserted by pinning upstream digests.

## 6. Frozen implementation statement — the package document structure

1. `identity` — task, criteria, scope, attempt, agent, base, profile snapshot
   sha, preregistration sha, date_frozen.
2. `input_pins` — the section-4 table as verified bytes.
3. `frame_chain` (C01 registration) — the two A06-declared frames
   (`macaque_arm_hand_mutation_frame`, sha-pinned A05 anchor transfer,
   coordinate_unit m; `osim.body.hand` owner-body-local path declaration) plus
   the M02 osim model-frame body_frames pin; every packaged position carries
   its frame declaration; NO transform composition, NO new fit; the
   verification still REQUIRED downstream (round-trip, handedness, landmark
   checks) is stated in the C01 contract row.
4. `skeletal_graph` — 24 nodes: the 19 A05 mutant digit bodies +
   `macaque_hand_anchor` (ids `ref.macaque_arm_hand_mutation.body.*`) + the 4
   grasp-scope forearm/arm bodies {humerus, ulna, radius, hand}; edges: the 22
   A06 bonds and 31 A06 containment edges carried verbatim (placement/
   ontology-only law carried: containment/parentage is not a mechanical bond),
   plus A05 parent chain edges. Grasp-scope boundary recorded: shoulder-chain
   bodies from the M02 graph (ground/sternum/clavicle/scapula and other
   arm-region frames) are NOT packaged; the boundary is explicit, not silent.
5. `tissue_graph` — 39 muscle nodes (one per A08 actuator row; ids
   `muscle.<osim_muscle>`), each carrying its A08 parameter row verbatim-class
   (fmax_n, l0m_m, l0t_m, pennation_deg/rad, fingerprints, mapping, screens,
   source_class, provenance) and `grasp_relevant` = true for exactly the 13
   grasp-scope muscles (A06 grasp_scope frozen list); the 26 non-grasp
   actuators carry parameters only, with the missing path geometry recorded as
   an explicit scope gap (never silently dropped).
6. `interface_graph` — for the 13 grasp muscles: 48 path-record connections
   (13 origin + 13 insertion attachments and 21 waypoints + 1 conditional
   waypoint, ids `path.<muscle>.<i>`, positions verbatim with owner body and
   A07 terminal resolution), 26 attachment interfaces (`attach.*` /
   `iface:tendon-<muscle>-{origin,insertion}` with A07 attachment
   resolutions), 6 grasp endpoints (mutation-frame anchors, A05-recorded); the
   C17 mechanics blocks carried VERBATIM from A07 (open, required_inputs
   unchanged, zero numbers).
7. `engineering_carriers` — M03 membrane constants, M04 rigid-law
   declaration (7 regions, parameters {}), M05 interface-exchange carrier,
   M09 demonstrator rig (2 bone scaffolds, 2 bonds, 1 contact at bound doc
   revision 47) — each `never_biological: true`, provenance
   `chosen_engineering`, disjoint from the tissue namespace by identity.
8. `explicit_reductions` — the declared reduction ledger, each entry with id,
   what is reduced, sealed source (pinned), and removal semantics:
   - RED-1 rigid-by-declaration passive law (M04): region rigidity replaces
     passive response; removing the declaration reverts to unpinned passive
     behavior — no mechanical connection is silently retained.
   - RED-2 active-pressure membrane tissue (M03): soft-tissue volume reduced
     to the membrane carrier; removing the membrane removes its mass and
     pressure constants from the package (they appear ONLY under
     engineering_carriers).
   - RED-3 loose-bones assembly (M09): joints reduced away; assembly exists
     ONLY through explicit connective material (2 bonds + 1 contact); declared
     removal semantics = the measured M09 release: ALL bond-type connective
     material removed bitwise (T4 `bitwise_zero_after_release: true`).
   - RED-4 measurement-only restraint (M09): derived per tick from active
     connections, never applies force, vanishes bitwise with them.
   - RED-5 axis-aligned envelope bounds test (A07): mesh-inside tests reduced
     to the A05-recorded per-axis bounds measurement (declared approximation
     carried verbatim).
   - RED-6 osim path-point tendon reduction (A06/A08): tendons carried as
     path points and parameter rows, not volumes; muscle mass/PCSA absent
     (U-gaps carried, never substituted).
   - RED-7 hand mutation structure (A05): digit bodies are the authored hybrid
     structure with the recorded assembly mapping (3 mapped / 14 pending
     carried as A07 terminal states).
9. `removal_closure` (the material-first addition, proven numerically) — the
   removal operator removes a muscle node and EXACTLY its incident
   connections; the validator recomputes, for each of the 13 grasp muscles,
   the removed-record table (path records + attachment interfaces attributed
   to that muscle) and asserts the conservation identity: the per-muscle
   removed counts sum to exactly 74 (= 48 path records + 26 attachment
   interfaces) and the reduced package has ZERO dangling references (every
   remaining connection references an existing tissue node and skeletal
   node). Frozen per-muscle degrees (computed pre-freeze from pinned bytes;
   validator reproduces exactly): the 13 muscles own ALL 74 records — 26
   attachment interfaces and 48 path records, each attributed to exactly one
   muscle by its record id.
10. `explicit_gaps` — carried verbatim-class: A08 U1-U8 (with their
    missing-evidence + authorizing-rank blocks); A07's 14 pending assembly
    mappings + 7 pending-and-outside + the carried Candidate C observation;
    the grasp-scope boundary gaps (26 non-grasp actuators without packaged
    path geometry; shoulder chain out of scope); C17 open; skin/fat geometry
    absent (M02 scope_limitation); each gap names what would resolve it and
    the rank that must authorize it.
11. `calculation_contracts` — C01, C05, C06, C17, C18 registered
    OPEN-INVENTORY exactly as the completion map records them: required
    inputs (catalog text), which package sections supply them, per-input
    status (source_backed / declared / explicitly_unresolved), and the
    verification still REQUIRED downstream (C01: round-trip/handedness/
    landmark checks; C05: FK closure + finite differences; C06: momentum/work
    ledgers + interventions; C17: approved finite-area formulation with real
    parameters; C18: finite differences/virtual work + unresolved-owner
    rejection). This card runs NO evaluation and claims NO new numerical
    result.
12. `consumer_contract` — the G-lane handoff: G01 (support/grip feasibility)
    consumes skeletal_graph + endpoints + actuator bounds (U-gaps disclosed);
    G02 (finite-area attachments) consumes interface_graph + C17 required
    inputs (open); G03 (tendon routing) consumes interface_graph paths + C18
    (open) with the unresolved-owner rejection law stated.
13. `checks` — preregistered predictions P1-P12 (below), gate codes, criteria
    hash identity.

## 7. Frozen measured result (computed from pinned bytes before this freeze;
the validator must reproduce every count exactly)

- A06: 48 path records (13 origin + 13 insertion + 21 waypoint + 1
  conditional waypoint), 26 attachments, 22 bonds, 31 containment edges, 6
  grasp endpoints, 13 grasp-scope muscles.
- Path-record owner bodies: radius 18, hand 17, humerus 8, ulna 5. Attachment
  bones: hand 13, humerus 8, ulna 4, radius 1. Grasp-endpoint owners: 5 distal
  digit bodies + macaque_hand_anchor. All 48 path records and all 26
  attachments attribute to exactly the 13 grasp-scope muscles (no orphan).
- A07: 48 path resolutions, 26 attachment resolutions, 22 waypoint
  resolutions, 6 endpoint resolutions; 3 mapped / 14 pending; 8 measured
  outside (4 insertions + 4 waypoints, all-Z violations); 7 pending-and-
  outside; 2 attachments + 1 waypoint mutant-supported, 24 attachments + 21
  waypoints mutant-unresolved.
- A08: 39 actuator rows (13 grasp-relevant + 26 parameters-only), 15
  engineering rows, U1-U8, C07/C18 OPEN-INVENTORY.
- Tissue-carried connection total: 74 (48 path records + 26 attachment
  interfaces); per-muscle removal degrees sum to exactly 74.

## 8. Declared gates, thresholds and preregistered predictions

All thresholds/classes are inherited from sealed sources (cited), never tuned
by this card. No numeric window is introduced by this card (there is no
simulation; every number is a count, a verbatim carried value, or a sha).

- P1 Pins: all 11 repo pins and 2 host pins (section 4) verify against
  on-disk bytes at emit; any mismatch refuses `input_pin_drift`.
  FALSIFIER: FB7 mutates a pinned copy.
- P2 Conservation: the package carries exactly the frozen counts of section
  7 (A06 48/26/22/31/6; A07 48/26/22/6 resolutions with 3/14, 8 outside;
  A08 39+15+8; skeletal 24 nodes; tissue 39 nodes with exactly 13
  grasp-relevant; connections 74). FALSIFIER: any other count refuses
  `frozen_count_mismatch`.
- P3 Provenance totality: every packaged row carries exactly one sealed
  provenance class (source_backed / declared_carrier_not_source_backed /
  chosen_engineering / explicitly_unresolved) inherited from its upstream
  document. FALSIFIER: a row without provenance refuses
  `silent_default_refused`.
- P4 Parameter carriage: all 39 tissue rows match the pinned A08 actuator
  rows field-for-field on the carried fields; the 15 engineering rows and
  U1-U8 match the pinned A08 document; biological vs engineering namespaces
  share zero row identity. FALSIFIER: any mutated carried value refuses
  `parameter_carriage_mismatch`.
- P5 Placement carriage: all 48/26/22/6 A07 resolutions match the pinned A07
  document field-for-field on the carried fields (terminal state, measured
  outside axes with exact excesses). FALSIFIER: FB3 flips an outside record;
  any other edit refuses `placement_carriage_mismatch`.
- P6 Owner/frame closure: every connection references an existing skeletal
  node and tissue node; owner-body sets equal the frozen sets of section 7;
  every position carries a frame declaration from the A06-declared frame
  chain; grasp endpoints carry `macaque_arm_hand_mutation_frame`. FALSIFIERS:
  FB1 repoints an owner (`wrong_owner_refused`); FB2 relabels a grasp
  endpoint's frame (`frame_mismatch_refused`).
- P7 Removal closure (the material-first law): for each of the 13 grasp
  muscles the validator applies the declared removal operator and asserts
  (a) removed count == that muscle's frozen degree, (b) the per-muscle counts
  sum to 74, (c) the reduced package has zero dangling references.
  FALSIFIER: FB4 removes a muscle but keeps one of its path records in the
  reduced graph (`dangling_connection_after_removal_refused`).
- P8 Reduction ledger: all seven declared reductions (RED-1..RED-7) present,
  each with a pinned sealed source and non-empty removal semantics.
  FALSIFIER: an empty removal_semantics refuses `missing_removal_semantics`.
- P9 Contracts: C01/C05/C06/C17/C18 appear exactly as the completion map
  records them (titles + result_status verbatim), each mapped to its supplying
  package sections; C17 keeps the A06/A07 open status and required_inputs;
  zero stiffness/couple numbers exist anywhere in the document. FALSIFIER:
  FB6-class scan refuses any invented result key.
- P10 No fitting: the document contains no `fitted*`/`optimized*` key
  (whole-document scan at validation time, sealed A07 law). FALSIFIER: FB6
  injects one (`fitting_unauthorized_refused`).
- P11 Determinism: two consecutive `--emit` runs produce byte-identical
  package bytes (sha256 equal).
- P12 Capture (visible_static, task_id "A09"): one PNG sheet, 6 rows = 3
  profile views x diagnostic/clean (side/oblique row = two viewports),
  rendered by pure-PIL orthographic projection of the package graph over the
  hand.vtp envelope point cloud + A05 skeleton (the same declared 2D
  reduction as sealed A07). Diagnostic rows draw the six profile layers and
  label the 8 outside placements with their exact per-axis excesses plus the
  mapped/terminal-state markers; every drawn label is bound to a stable
  subject id (no ambiguity); every manifest view row's
  `state_binding.sha256` equals the sha256 of `grasp_package.json` (view
  toggles preserve the physical state hash); `validate_manifest` returns
  `structurally_valid=True` with the profile read mode=ro from
  agent_slots.sqlite3 (profile_id "anatomy", capture_kind "image") and the
  registry card criteria sha asserted equal to the document's. Clean rows
  carry no layers, labels or bindings. FALSIFIERS: FB8a draws a label without
  a binding (`label_ambiguity_refused`); FB8b gives one manifest row a
  foreign state sha (`view_toggle_state_hash_refused`).

## 9. Falsifier arms (every arm: clean control FIRST, named premature guard
`a09_fb<n>_premature`, receipt row with clean_control block; each must BIT on
its tampered fixture only)

- FB1 `wrong_owner_refused` — repoint one attachment's bone to a non-owner
  (e.g. a hand attachment to humerus) and one path record's owner body.
- FB2 `frame_mismatch_refused` — relabel one grasp endpoint's frame to
  `osim.body.hand`.
- FB3 `hidden_outside_refused` — flip one of the 8 outside placements to
  inside (clear its outside_axes) in the carried placement row.
- FB4 `dangling_connection_after_removal_refused` — apply the removal
  operator to a muscle but retain one of its path records in the reduced
  graph.
- FB5 `silent_default_refused` — strip the provenance block from one carried
  parameter row.
- FB6 `fitting_unauthorized_refused` — inject a `fitted_origin_m` key into a
  carried path record (whole-document scan must refuse).
- FB7 `input_pin_drift` — mutate one byte of a pinned upstream copy (the
  generator refuses at emit and at verify).
- FB8 capture arms — FB8a `label_ambiguity_refused` (a diagnostic marker
  drawn whose label lacks a bound stable subject id); FB8b
  `view_toggle_state_hash_refused` (a manifest row carrying a foreign
  state_binding sha). These run in the capture self-check and must refuse
  before any manifest is written.

## 10. House gates at freeze (G1-G9 disposition)

G1 applies (FB1-FB8 with clean controls + guards + receipt rows). G2 applies
(lint + selftest; every report number traceable at printed precision). G3
applies (qualitative claims rendered from probe receipts with named refusal
codes). G4 NOT APPLICABLE in its video form — the capture is a single PNG
sheet (no encoded video exists); disclosed, not skipped silently. G5 applies
where any comparison exists (count identities carry named refusal codes; no
relative-tolerance window exists in this card). G6 applies (per-document
extractors keyed by document/role; no mixed scans). G7 applies (profile
loaded mode=ro; task_id SHORT; criteria identity across dispatch/registry/
prereg/checks). G8 applies in the single-image form: exactly one gate-bound
capture identity — sheet PNG disk sha256 == manifest.capture_sha256 ==
context.capture_sha256 == determinism record; identical
`state_binding.sha256` on every view row. G9 applies (prereg committed
separately BEFORE implementation; contribution within 32 files / 16 MB;
commit-message metrics generated from FINAL receipts; byte-exact carry via
the card `.gitattributes` `* -text`; ONE publication commit on the base with
the `Agent:` trailer).

## 11. Evidence anchoring (CARD_STARTER v2)

Qualification evidence references are file paths (never directories),
store-relative where possible; before any attempt-workspace artifact is
referenced by the registry it is copied into
`E:/ChimeraWork/monkey-coordination/evidence-store/MAT2-A09/` sha-verified.
No prose in reference fields; compound pins live in the report body.

## 12. Honest limitations (declared in advance)

- Static completion-of-record only: no runtime/dynamic claim; the visible_static
  profile's runtime phases stay pending and are NOT passed by these fixtures.
- The capture is a 2D orthographic PIL projection (no 3D renderer/GPU);
  validate_manifest is structural only; independent pixel review remains
  mandatory and is not claimed.
- The removal closure is a STATIC graph identity over the packaged document;
  the dynamic (runtime bitwise-release) proof remains the sealed M09 T4
  measurement, carried by reference.
- No transform is composed between the two declared frames (the A05 anchor
  transfer is carried by reference; the C01 round-trip verification is
  registered as still REQUIRED downstream).
- 26 non-grasp actuators carry parameters without packaged path geometry
  (grasp-scope boundary per A06); this is disclosed in explicit_gaps, never
  silently dropped.
- C17 stays open; no attachment patch area/shape, areal stiffness, couple
  resistance or weights exist in the pinned sources; none is invented.
- Anatomy completion does not itself prove climbing (card observation,
  verbatim).

## Amendment A1 (pre-implementation, append-only; own commit)

Timing: after the initial freeze commit 2640fa86, BEFORE any implementation
artifact existed and before any generator run (no measurement has occurred).
Reason: section 6.11 says the C01/C05/C06/C17/C18 contracts are carried
"exactly as the completion map records them" but the section-4 pin table did
not name the file those records are read from; A1 pins it so the phrase is
byte-anchored and the carried catalog text is verbatim-from-bytes, never
transcribed.

- ADDED input pin (read at the candidate commit, verified like every other
  pin; refusal code input_pin_drift unchanged):
  | role | file | sha256 |
  |---|---|---|
  | completion-map catalog records (C01/C05/C06/C17/C18 titles, required inputs, result_status) | repo tools/monkey_campaign/monkey_completion_map.json | 3efbfb141299d7cad63724431f7e5269febe15eee68d812b80d91de324385b84 |
- NO threshold, count, prediction, falsifier or structure change of any kind.
- The pin count in P1 becomes 12 repo pins + 2 host pins = 14 pins total.
