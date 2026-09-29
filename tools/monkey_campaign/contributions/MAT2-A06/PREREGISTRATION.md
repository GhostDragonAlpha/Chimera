# PREREGISTRATION — MAT2-A06 "Resolve attachment and waypoint ownership"

Preregistered 2026-09-29 by the Sergeant-implementer (arrival-6fa733ab10c745d580180fe59cd2565f,
attempt d35796819ef74e6681f1bc6a5fd2ec9e) BEFORE authoring the ownership registry,
validator, falsifier probes or any capture frame. This file is committed alone,
before any implementation artifact, so the freeze is git-provable (separate-first).
Inputs were read read-only from the pinned sources; the counts and refusals below
are the statements the deliverables must reproduce exactly.

## Task identity

- Card MAT2-A06, slot 3, branch-3, base c525b82c7c3ce0128565424764293a3c85811ab3.
- Criteria sha256 31b38a12a8d7a1f28d6b5191e428bab4c11b7267649c549416d85225ee39ecbe.
- done_when (verbatim): "Every grasp-relevant endpoint and waypoint has an explicit
  approved body and role. Material-first addition: Represent tissue-to-bone
  attachments explicitly; ontology containment and conventional rig parentage never
  silently create a mechanical bond."
- Card observation (binding): "Do not reinterpret waypoints as attachment ports".
- Profile: anatomy (visible_static), subject "Creature structure, bone/muscle/skin
  correspondence and attachment ownership"; capture REQUIRED with task_id short form
  "A06"; 3 profile views, clean_view_required=true, 6 diagnostic_layers, 16
  camera_required_fields, numerical_evidence_required=true. The profile object is
  read read-only from E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3
  (kanban.cards[MAT2-A06].spec.ontology_qualification.task.verification_profile)
  at capture time; registry card criteria_sha256 matches the attempt criteria hash.
- Depends on (all DONE, exact-revision inputs): MAT2-A03 (ulna correspondence,
  head 775d09dea53051d28c84b197bdb9ec58a5d4efd4), MAT2-A05 (first mutation,
  winner head a4fdaaa721f14ec085768bf5dcff2c6834a9abeb, criteria
  34411771f7bd5dea2ec2cc4775d44b33df422e5454d283eae40676d1e3346544), MAT2-M05
  (interface exchange, winner head cadaabc6ae0522c2530ce6fa090f07725d19a25f).
  Law lineage carried through: B04 frame forest (containment and bonds are DISJOINT
  relation lists; head ba24f78622bbf5e1e0e4338187e7889b7da221f5) and M05
  (bonds exist only through IDENTIFIED interfaces; `refuse_auto_bond`).
- Attempt workspace prepared by this instance (checkout_identity.json:
  task MAT2-A06, attempt d35796819ef74e6681f1bc6a5fd2ec9e, branch-3, sparse path
  tools/monkey_campaign/contributions/MAT2-A06). No pushes, no PRs; the lead
  publishes to review/MAT2-A06.

## Reconciled subject (what this card owns)

1. THE PINNED OSIM REFERENCE — monkeyArm_current.osim
   (E:/PythonChimera/tools/science_funnel/data/macaque_arm/monkeyArm_current.osim,
   sha256 4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde0a68a3e0dc67faec67b895).
   The osim is an INDEPENDENT arm reference (B04 recorded it unmerged); this card
   resolves its muscle attachment/waypoint OWNERSHIP explicitly — it does not merge
   the osim into the mutant assembly.
2. THE A05 MUTANT HAND — mutation_structure.json of the A05 winner workspace
   (19 digit bodies + anchor; per-body 20 digit joints + 2 wrist dofs on the anchor;
   Captain decision A05-DIGIT-MUTATION-20260928). Its grasp endpoints (5 fingertips)
   and palm anchor get explicit approved owner bodies and roles.
3. The no-silent-bond law, generalized from B04/M05 to this data: containment edges
   (osim Model frame membership; A05 MJCF rig parentage) are one relation list;
   mechanical bonds (A05 mutant joints) and tissue-to-bone attachments (tendon
   endpoint interfaces) are DIFFERENT relation lists with explicit declared
   provenance. No containment edge or parent attribute may appear as, or silently
   create, a bond or an attachment.

## Grasp-relevant set (frozen definition)

A muscle is grasp-relevant iff it has at least one PathPoint on osim body `hand`.
Exactly 13 muscles qualify (verified against the pinned osim before this freeze):
abd_poll_longus, ext_carpi_rad_longus, ext_carp_rad_brevis, ext_carpi_ulnaris,
ext_digitorum, ext_digiti, ext_indicis, flex_carpi_radialis, flex_carpi_ulnaris,
flex_digit_profundus, flex_digit_superficialis, flex_poll_longus, palmaris_longus.

A grasp-relevant PATH RECORD is every path point of a grasp-relevant muscle, on
whatever body it declares. Frozen counts (from the pinned osim bytes):

- 48 path points total across the 13 muscles (ext_digitorum et al. repeat path
  point NAMES inside one muscle — e.g. two `ext_digitorum-P2` — so record identity
  is (muscle, index-in-XML-order), carrying the declared name verbatim, including
  the literal `default` name on abd_poll_longus index 1).
- flex_digit_profundus contains ONE ConditionalPathPoint
  (`flex_digit_profundus-P2`, body `radius`, coordinate `radial_pronation`,
  range [-1.5708, 0.352382]); it is a range-conditioned WAYPOINT and is recorded
  with its coordinate/range verbatim.
- 17 of the 48 points lie on body `hand`; 26 points are path ENDPOINTS
  (index 0 = tendon ORIGIN, last index = tendon INSERTION; all 13 insertions lie
  on `hand`; origins: 8 on humerus, 4 on ulna, 1 on radius); 22 points are
  WAYPOINTS (intermediate; 21 unconditional + 1 conditional).
- A05 previously mapped 3 hand-frame anchors into the mutant
  (ext_digitorum-P3 -> macaque_hand_anchor, ext_digitorum-P2 -> proxph3,
  flex_digit_profundus-P4 -> fifthmc, with distances 0.010058306369454054 /
  0.004674974795050801 / 0.012604227792366404 m). Those 3 hand-body waypoints/
  endpoints carry mutant_mapping status `mapped`; the other 14 hand-body points
  carry status `pending_assembly_mapping` — inventoried explicitly, NOT silently
  defaulted, and downstream skills are not required to accept them (profile
  procedure). The source-approved OWNER for every path record is the osim body
  verbatim; the mutant mapping is a separate, honest column.

A05 GRASP ENDPOINTS (from the A05 winner record, envelope_check
fingertip_positions_m, macaque hand frame, meters): thumb -> owner distal_thumb,
digit2 -> distph2, digit3 -> distph3, digit4 -> distph4, digit5 -> distph5;
plus the palm anchor macaque_hand_anchor. Roles: `grasp_contact_endpoint` (5) and
`grasp_palm_reference` (1). Approval reference: Captain decision
A05-DIGIT-MUTATION-20260928 + A05 winner criteria sha256 34411771f7bd5dea2ec2
cc4775d44b33df422e5454d283eae40676d1e3346544.

## What the deliverable IS (declared in advance)

A DERIVED ownership registry document (schema chimera.attachment_ownership.v1,
canonical JSON, stable IDs) built by attachment_ownership.py from the pinned
sources, plus a validator with named refusals, plus falsifier tamper probes, plus
the visible_static capture. The registry carries:

- sources: the three pinned inputs (osim, hand.vtp, A05 mutation_structure.json
  on-disk sha256 48b037593f63ec473947d787077ab6fbcd3b364afd15765bff508e7d54f45649)
  and dependency card identities (A03/A05/M05/B04 heads + criteria).
- frames: osim macaque hand body frame = A05 mutant frame
  (macaque_arm_hand_mutation_frame, anchor = macaque hand body origin, m) — the
  correspondence is the A05-recorded verbatim anchor transfer, not a new fit.
- path_records: 48 rows {record_id, muscle, index, name, body (owner), role:
  origin_attachment | insertion_attachment | path_waypoint | conditional_waypoint,
  location_m, approved_by: osim sha256, mutant_mapping}.
- grasp_endpoints: 6 rows with owner body, role, position_m, approval references.
- attachments: 26 tissue-to-bone attachment records — one per path ENDPOINT, each
  {attachment_id, path_record_id, tissue (muscle), bone (owner body), interface_id
  (iface:tendon-<muscle>-origin / -insertion), transfers: 'force',
  provenance: explicit_declaration (sha-pinned osim)}. An attachment EXISTS only
  through its declared interface (M05 law); there is no other way to make one.
- bonds: the 22 A05 mutant joint records (20 digit joints + 2 wrist dofs), kind
  'mechanical_bond', provenance explicit_declaration (Captain decision A05 +
  A05 criteria sha), each referenced to its A05 record — never derived from the
  MJCF/registry parent attribute.
- containment_edges: osim Model frame membership (11 bodies) and A05 rig parentage
  (anchor + 19 digit bodies) — kind 'containment', placement/ontology only.
- c17 (Finite attachment mechanics) inventory: each attachment carries a mechanics
  block listing the C17 required inputs (patch area/shape, areal stiffness, couple
  resistance, weights, frame) with status `inputs_unavailable_in_pinned_sources`:
  the osim pins path POINTS only and no attachment patch geometry/stiffness exists
  in any pinned source. NO stiffness or rotational-resistance number is derived;
  NO synthetic lambda_min is claimed. A validator refusal
  (`attachment_stiffness_unsourced`) fires if any attachment claims a stiffness
  value without declared inputs.

## Falsifiable predictions

- P1 Pins: live sha256 of the osim == 4148aee2c8dda1dcb0918496ad7c5e1adcf4ebabde
  0a68a3e0dc67faec67b895; hand.vtp == a06ea7e079c849df07d6eec001e9bcc2ea193ecd391
  4011c78a993a5faa94fc6; A05 mutation_structure.json == 48b037593f63ec473947d78707
  7ab6fbcd3b364afd15765bff508e7d54f45649. FALSIFIER T5: any other digest refuses
  `live_source_hash_mismatch`.
- P2 Scope: exactly 13 grasp-relevant muscles (the list above), exactly 48 path
  records, exactly 17 on body `hand`, exactly 26 endpoints / 22 waypoints
  (21 unconditional + 1 conditional flex_digit_profundus-P2 on radius with
  coordinate radial_pronation and range [-1.5708, 0.352382]). FALSIFIER: any other
  count or an unresolvable (muscle, index).
- P3 Ownership: every one of the 48 path records carries a non-empty osim owner
  body (ground/sternum/clavicle/scapula/humerus/ulna1/ulna/radius_jcc/radius/
  radius1/hand vocabulary) and a role from the frozen role set; every one of the 6
  grasp endpoints carries its A05 owner body and role. FALSIFIER T2: removing any
  owner body or role refuses `unowned_endpoint` / `unowned_role` — never a
  default. FALSIFIER T4: the owner-resolution helper called with an unmapped point
  and no explicit owner refuses `owner_default_refused` (it must not fall back to
  a parent/containing body).
- P4 Waypoints are not attachment ports: all 22 waypoint rows carry interface=None
  and bond=False, including abd_poll_longus index 4 (`abd_poll_longus-P3`, body
  hand) and ext_carp_rad_brevis index 3 / ext_digitorum index 3 / ext_digiti
  index 3 — hand-body points that are NOT insertions. FALSIFIER T3: adding an
  interface or bond to a waypoint refuses `waypoint_is_not_attachment_port`.
- P5 Explicit tissue-to-bone attachments: exactly 26 attachment rows, one per
  endpoint, all 13 insertions on body `hand`, each with interface_id + transfers
  'force' + provenance explicit_declaration; the sets {containment ids},
  {attachment ids}, {bond ids} are pairwise disjoint. FALSIFIER: an attachment
  without an interface, a duplicate interface id, or any identity overlap refuses.
- P6 No-silent-bond law: every bond row's provenance.kind == 'explicit_declaration'
  with sha pin; FALSIFIER T1 (the rig-parentage tamper): any bond or attachment
  whose provenance.kind is 'containment' or 'rig_parentage' — e.g. a tampered
  document that adds the A05 MJCF parent attribute `macaque_hand_anchor ->
  firstmc` (or the osim radius1->hand joint-tree parentage) as a mechanical bond —
  refuses `bond_from_parentage_refused`. Separation check: deleting ALL
  containment_edges leaves the attachments and bonds digests byte-identical, and
  deleting all attachments/bonds leaves the containment digest byte-identical
  (B04-style, proven on the emitted document).
- P7 Determinism: building the document twice produces byte-identical canonical
  bytes (same sha256); the validator receipt is a pure function of the document.
- P8 C17 honesty: zero stiffness/rotational-resistance numbers anywhere in the
  document; every mechanics block status == 'inputs_unavailable_in_pinned_sources';
  FALSIFIER: a mechanics block carrying a stiffness value refuses
  `attachment_stiffness_unsourced`.
- P9 Capture (visible_static, task_id "A06"): one PNG sheet, 6 rows = 3 profile
  views x diagnostic/clean (side/oblique view = two viewports per row), rendered
  by pure-PIL orthographic projection of the mutant skeleton + osim hand-body path
  points over the hand.vtp envelope point cloud; diagnostic rows show the 6
  profile layers and stable labels bound to record ids (path records, attachment
  ids, grasp endpoint ids); every row's state_binding.sha256 equals the sha256 of
  the emitted attachment_ownership.json (view toggles preserve the physical state
  hash); validate_manifest returns structurally_valid=True, profile_id 'anatomy',
  capture_kind 'image', view_count 6, with the profile read read-only from
  agent_slots.sqlite3 and task_id "A06" in manifest and context. FALSIFIER: label
  ambiguity (drawn label without a bound stable id), missing camera field, or a
  clean row carrying diagnostics refuses.

## Validation plan (committed, runnable read-only)

attachment_ownership.py --emit builds the document; --verify validates it and runs
the P1-P8 checks; --tamper-rig runs falsifier T1; --tamper-unowned runs T2;
--tamper-waypoint runs T3; --tamper-default runs T4; --tamper-stiffness runs the
P8 refusal; all tamper probes must FAIL with exactly the named refusal.
test_attachment_ownership.py asserts the full P1-P8 set plus byte-determinism.
capture_ownership.py renders the sheet and validates the manifest against the
registry profile (visual_capture.validate_manifest, unmodified, from the source
head). qualification_receipt.json maps every done_when clause and calculation
contract to its evidence; report.md carries commands, observed results, failures
and limits.

## Honest limitations (declared in advance)

- The osim remains an independent unmerged reference (B04): attachments bind the
  osim's own bodies; only the 3 A05-recorded anchors carry mutant mappings. 14
  hand-body points are `pending_assembly_mapping`, not silently mapped.
- C17 stays an open contract: no attachment patch area/shape, areal stiffness,
  couple resistance or weights exist in the pinned sources; none is invented.
- The capture is a 2D orthographic PIL projection (no 3D renderer, no GPU);
  validate_manifest is structural only — independent pixel review remains
  mandatory and is not claimed here.
- The osim muscle model is Schutte1993Muscle_Deprecated tendon paths: roles are
  path-structural (origin/insertion/waypoint), not histological claims.
- Tendon paths that wrap or branch beyond these PathPoints (wrapping surfaces)
  are not declared in the pinned osim for the 13 muscles and are inventoried as
  absent, not approximated.
