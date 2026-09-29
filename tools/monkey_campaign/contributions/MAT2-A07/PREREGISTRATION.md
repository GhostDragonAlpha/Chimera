# PREREGISTRATION — MAT2-A07 "Resolve failed/outside attachment placements lawfully"

Preregistered 2026-09-29 by the Sergeant-implementer (arrival-2b610e46ac9a41e79daff5bfea970f34,
attempt 638d4dc8a3384216b526ebc8bc16c3fe) BEFORE authoring the resolution builder,
validator, falsifier probes or any capture frame. This file is committed ALONE,
before any implementation artifact, so the freeze is git-provable (separate-first).
Inputs were read read-only from the pinned sources and the sealed tip; the counts,
ids and refusals below are the statements the deliverables must reproduce exactly.

## Task identity

- Card MAT2-A07, slot 4, branch-4, base fa8ecf67be01a7ff0dbb4c538ad88b68ef196b5a
  (the sealed tip of astra/gait-capture; the prepared branch-4 base 9ba1be77 was
  an ancestor and was fast-forwarded to the sealed tip before any edit).
- Criteria sha256 c4d4ae430027d489d58007cae3895b81dcbfa604c045aa35049c3ecf333373f8
  (startup assignment == kanban.cards[MAT2-A07] in
  E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3, read read-only).
- done_when (verbatim): "Attachment validity is supported or explicitly
  unresolved; any new fitting experiment is separately authorized".
- Card observation (binding, carried verbatim): "Candidate C remains failed at
  67.147 micrometres per side; four wrist sites outside under both loops".
- Profile: anatomy (visible_static), subject "Creature structure,
  bone/muscle/skin correspondence and attachment ownership"; capture REQUIRED with
  task_id short form "A07"; 3 profile views, clean_view_required=true, 6
  diagnostic_layers, 16 camera_required_fields, numerical_evidence_required=true.
  The profile object is read read-only from
  E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3
  (kanban.cards[MAT2-A07].spec.ontology_qualification.task.verification_profile)
  at capture time; registry card criteria_sha256 must equal the document's
  criteria_sha256 (asserted at capture time).
- Depends on: MAT2-A06 — DONE, merged as PR #250 (merge commit fa8ecf67;
  publication commit 3271888c "MAT2-A06: explicit attachment and waypoint
  ownership (publication of Sergeant candidate dbdd6b10)"). Its registry is read
  as committed bytes: tools/monkey_campaign/contributions/MAT2-A06/
  attachment_ownership.json, sha256 f1f0430772258e8449fc354841becf2f1869783399e6
  3f3f145565b8d0b1041c (A06 report table) — any other bytes refuse
  `a06_registry_pin_mismatch` (completion-of-record over the EXACT sealed A06
  registry, never a rebuilt variant).
- Attempt workspace prepared by this instance (checkout_identity.json: task
  MAT2-A07, attempt 638d4dc8a3384216b526ebc8bc16c3fe, branch-4, sparse path
  tools/monkey_campaign/contributions/MAT2-A07). No pushes, no PRs; the lead
  publishes to review/MAT2-A07.

## Reconciled subject (what this card owns)

A06 left an explicit, honest completion-of-record debt. This card resolves it
WITHOUT any new fitting: every FAILED or OUTSIDE placement in the A06 registry
becomes exactly one of the two lawful terminal states.

1. THE LAWFUL VOCABULARY (frozen; exactly two terminal states):
   - `supported` — the placement is backed by pinned evidence: a named pinned
     source with its sha256 AND an approval reference (recorded captain/lead
     decision or the sha-pinned osim declaration itself).
   - `explicitly_unresolved` — the placement carries a missing_evidence block
     that NAMES the absent record or decision (and the rank that must authorize
     it). Being unresolved is an honest terminal state, not a failure of this
     card.
   Nothing else is lawful: no guessed body, no nearest-neighbor default, no
   silent "supported", no fit. Any new fitting experiment is SEPARATELY
   authorized (a recorded lead/captain decision); none is authorized for this
   card, so none is run and none is simulated.

2. THE MEASURED OUTSIDE TEST (frozen instrument; a measurement, not a fit):
   For each of the 17 osim hand-body path records, the registry's location_m is
   tested against the A05-recorded hand envelope bounds
   (mutation_structure.json envelope_check.hand_vtp_bounds_m, lo=[-0.0124375,
   -0.0837075, -0.00152775], hi=[0.020731000000000003, -0.00010125000000000001,
   0.004639750000000001], pinned by the A05 structure sha256
   48b037593f63ec473947d787077ab6fbcd3b364afd15765bff508e7d54f45649). A point is
   INSIDE iff lo[axis] <= x[axis] <= hi[axis] for all three axes; otherwise it is
   OUTSIDE with per-axis signed excess_m recorded exactly (no clamping, no
   rounding). Declared approximation: an axis-aligned bounds test against the
   A05-recorded envelope bounds — not a mesh-inside test; the A05 falsifier
   tradition itself uses per-axis spans ("Y-span coherence is the preregistered
   falsifier ... recorded per axis"). Forearm bodies are OUT OF SCOPE of this
   envelope test by construction (the envelope is the hand.vtp bounds; forearm
   points are never tested against it).

3. FROZEN MEASURED RESULT (computed from the pinned bytes before this freeze;
   the validator must reproduce it exactly):
   - 17 hand-body records = 13 insertion attachments + 4 waypoints
     (hand waypoints: path.abd_poll_longus.3, path.ext_carp_rad_brevis.2,
     path.ext_digiti.2, path.ext_digitorum.2).
   - EXACTLY 8 records measure OUTSIDE, every violation on the Z axis:
     INSERTIONS (4): path.ext_carpi_rad_longus.3 (z above_hi excess_m
     7.276999999999978e-05), path.ext_indicis.3 (z above_hi 0.001892819999999999),
     path.flex_carpi_ulnaris.2 (z below_lo -0.00039575000000000005),
     path.palmaris_longus.3 (z below_lo -0.0004272500000000001).
     WAYPOINTS (4): path.abd_poll_longus.3 (z above_hi 0.002449869999999999),
     path.ext_carp_rad_brevis.2 (z above_hi 0.0007133999999999995),
     path.ext_digiti.2 (z above_hi 0.0011906899999999995), path.ext_digitorum.2
     (z above_hi 0.0013102099999999992; NOTE this record is one of the 3
     A05-MAPPED points — its mapping stays supported by the A05 record; the
     outside measurement is recorded as a declared deviation, never as a
     refutation of the recorded mapping and never repaired here).
   - The 4 outside INSERTIONS are wrist-region extensor/flexor insertion sites —
     the same count the card observation records for the historical loops ("four
     wrist sites outside"). The convergence of COUNTS is recorded as context
     ONLY; the two instruments are distinct and this card does not claim to have
     re-derived the historical loops (see Honest limitations).

4. RESOLUTION RULES (frozen, deterministic functions of the pinned inputs):
   - R1 hand-body record with mutant_mapping.status == "mapped" (3):
     mutant-assembly placement `supported`; evidence = A05 Captain decision
     A05-DIGIT-MUTATION-20260928 + A05 criteria sha256 34411771f7bd5dea2ec2cc477
     5d44b33df422e5454d283eae40676d1e3346544 + A05 structure sha256 48b03759...,
     with the A05-recorded distance_m verbatim; plus the osim pin for the osim
     reference. If measured outside, deviation recorded; support unchanged.
   - R2 hand-body record with mutant_mapping.status == "pending_assembly_mapping"
     (14): `explicitly_unresolved`; missing_evidence names
     "recorded_assembly_mapping_decision" — no lead/captain-recorded
     nearest-mutant-body correspondence exists for this point in any pinned
     source; an authorized assembly-mapping decision (recorded, with distance)
     is required. Measured inside does NOT resolve it (envelope presence creates
     no ownership — B04 law); measured outside adds placement_failed_outside.
     7 of the 14 measure outside; 7 measure inside.
   - R3 forearm records (origins on humerus(8)/ulna(4)/radius(1) and their
     waypoints): osim-reference placement `supported` by the sha-pinned osim
     declaration; mutant-assembly placement `explicitly_unresolved` with
     missing_evidence "forearm_assembly_correspondence_record" (the A05 mutation
     record's scope is the hand; no recorded forearm correspondence exists).
   - R4 every attachment (26): osim-reference validity `supported`
     (provenance explicit_declaration + interface iface:tendon-<muscle>-{origin,
     insertion} + transfers force + osim sha, all inherited from A06); its
     MUTANT-ASSEMBLY validity follows its path record's rule (R1/R2 for the 13
     hand insertions; R3 for the 13 forearm origins).
   - R5 every waypoint (22): a path-shape record — osim-reference validity
     `supported` by the osim pin; it is NEVER an attachment port (A06 law
     inherited); mutant-assembly placement follows R1/R2; the 4 outside hand
     waypoints carry placement_failed_outside=true.
   - R6 the 6 grasp endpoints (5 fingertips + palm anchor): `supported` by the
     A05 Captain decision + criteria sha (positions are the A05 record's own
     envelope_check data; no new measurement needed).
   - R7 C17 (finite attachment mechanics) stays OPEN exactly as A06 left it:
     every attachment's mechanics block keeps required_inputs + status
     inputs_unavailable_in_pinned_sources; zero stiffness/couple numbers appear.
   - R8 the CARRIED OBSERVATION ("Candidate C ... 67.147 micrometres per side;
     four wrist sites outside under both loops") is carried verbatim with its
     sources (monkey_completion_map.json#tasks/A07 "observation" and
     MONKEY_COMPLETION_MAP.md "Anatomy" bullet, both at the sealed tip) and
     resolved `explicitly_unresolved` + fitting_not_authorized: the same sealed
     record states "No radius supersession or new fitting candidate is
     authorized", so the missing evidence is "a separately authorized (recorded
     lead/captain) fitting experiment"; this card runs none.

## What the deliverable IS (declared in advance)

A DERIVED resolution document (schema chimera.attachment_placement_resolution.v1,
canonical JSON, stable ids) built by placement_resolution.py from the sealed A06
registry bytes + the sha-pinned A05 structure (live-verified) + the osim/hand.vtp
pins, plus a validator with named refusals, plus falsifier tamper probes, plus
the visible_static capture. The registry (A06) is READ-ONLY to this card: no A06
byte changes, no rebuilt variant, separation is asserted by pinning the A06 file
digest.

## Falsifiable predictions

- P1 Pins: A06 registry file bytes sha256 == f1f0430772258e8449fc354841becf2f186
  9783399e63f3f145565b8d0b1041c; live osim == 4148aee2c8dda1dcb0918496ad7c5e1adc
  f4ebabde0a68a3e0dc67faec67b895; live hand.vtp == a06ea7e079c849df07d6eec001e9bc
  c2ea193ecd3914011c78a993a5faa94fc6; live A05 structure ==
  48b037593f63ec473947d787077ab6fbcd3b364afd15765bff508e7d54f45649.
  FALSIFIER T-PIN: any other digest refuses (a06_registry_pin_mismatch /
  live_source_hash_mismatch).
- P2 Inventory conservation: the resolution document covers EVERY row of the A06
  registry — 48 path_resolutions, 26 attachment_resolutions, 22
  waypoint_resolutions, 6 grasp_endpoint_resolutions — with no invented rows and
  none dropped; frozen aggregates: 17 hand-body, 3 mapped, 14 pending, 8 outside
  (frozen id list above), 4 outside insertions, 4 outside waypoints, 7
  pending-and-outside. FALSIFIER: any other count refuses frozen_count_mismatch.
- P3 Totality + vocabulary: every covered row carries EXACTLY one terminal
  resolution — `supported` (with a complete evidence block: source id + sha256
  in the pinned set + approval reference) or `explicitly_unresolved` (with a
  non-empty missing_evidence naming the absent record/decision and the
  authorizing rank). FALSIFIER T-DEFAULT: a resolution with any other state
  (e.g. "defaulted") or an empty missing_evidence refuses silent_default_refused.
- P4 Evidence binding: every `supported` claim carries its pin. FALSIFIER
  T-SUPPORTED-NO-PIN: deleting the evidence block (or its sha) from a supported
  resolution refuses supported_claim_missing_pin.
- P5 No unauthorized fitting: no fitted coordinates, fitted bodies or optimizer
  outputs exist anywhere in the document; the only numbers are verbatim pinned
  values and the frozen test's signed excesses. FALSIFIER T-FIT: adding a
  fitted_* / *_fit / optimized_* field (or a "new_fit" resolution) refuses
  fitting_unauthorized_refused.
- P6 Measured honesty: the validator RECOMPUTES the envelope test from the
  registry locations + pinned bounds and refuses any per-record measurement that
  disagrees. FALSIFIER T-FLIP: relabeling an outside record as inside (or
  editing an excess) refuses measured_status_mismatch.
- P7 Registry conservation: the A06 registry digest is carried and asserted;
  building the resolution changes no A06 byte (the document is additive and
  separate).
- P8 C17 honesty inherited: zero stiffness numbers; every inherited mechanics
  block keeps its status. FALSIFIER T-STIFFNESS: injecting a stiffness value
  refuses attachment_stiffness_unsourced.
- P9 Determinism: building the document twice produces byte-identical canonical
  bytes.
- P10 Capture (visible_static, task_id "A07"): one PNG sheet, 6 rows = 3 profile
  views x diagnostic/clean (side/oblique row = two viewports), rendered by
  pure-PIL orthographic projection of the resolution state over the hand.vtp
  envelope point cloud + A05 skeleton; diagnostic rows color markers by terminal
  state (green = supported, amber = explicitly_unresolved, red ring = measured
  outside deviation) and label the 8 outside + 3 mapped records with their
  record ids and exact excesses (numerical_evidence_required); every row's
  state_binding.sha256 equals the sha256 of placement_resolution.json (view
  toggles preserve the physical state hash); validate_manifest returns
  structurally_valid=True with the profile read read-only from
  agent_slots.sqlite3, profile_id "anatomy", capture_kind "image", and the
  registry card criteria sha asserted equal to the document's. FALSIFIER: label
  ambiguity (drawn label without a bound stable id), missing camera field, or a
  clean row carrying diagnostics refuses.

## Validation plan (committed, runnable read-only)

placement_resolution.py --emit builds placement_resolution.json; --verify
validates it against P1-P8; --self-check builds + validates in memory;
--tamper-supported-pin runs T-SUPPORTED-NO-PIN; --tamper-default runs T-DEFAULT;
--tamper-fit runs T-FIT; --tamper-flip runs T-FLIP; --tamper-stiffness runs
T-STIFFNESS; --tamper-registry runs T-PIN against a mutated registry copy. All
tamper probes must FAIL with exactly the named refusal.
test_placement_resolution.py asserts P1-P9 plus the probes.
capture_resolution.py renders the sheet and validates the manifest with the
UNMODIFIED source-head visual_capture.validate_manifest against the registry
profile (task_id "A07"). qualification_receipt.json maps every done_when clause
to its evidence; report.md carries commands, observed results, failures, limits.

## Honest limitations (declared in advance)

- Static completion-of-record only: no runtime/dynamic claim; the visible_static
  profile's runtime phases stay pending and are NOT passed by these fixtures.
- No fitting experiment is run or simulated; resolving the 14 pending mappings
  or the outside sites requires recorded decisions this card does not have and
  must not invent.
- The carried Candidate C observation is cited from the sealed completion-map
  records; the historical loop receipts were not re-located in this attempt and
  the loops were not re-run (running them would be the unauthorized fit). The
  count convergence (four outside wrist-region insertion sites) is recorded as
  context, not as identity of instruments.
- The envelope test is an axis-aligned bounds measurement against the
  A05-recorded bounds, not a mesh-inside test.
- The capture is a 2D orthographic PIL projection (no 3D renderer/GPU);
  validate_manifest is structural only; independent pixel review remains
  mandatory and is not claimed.
- The osim remains an independent unmerged reference (B04); "supported" for
  osim-reference validity never claims mutant-assembly placement.
- C17 stays open; no attachment patch area/shape, areal stiffness, couple
  resistance or weights exist in the pinned sources; none is invented.
