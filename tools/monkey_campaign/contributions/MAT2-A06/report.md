# REPORT — MAT2-A06 "Resolve attachment and waypoint ownership"

Sergeant-implementer record. Attempt d35796819ef74e6681f1bc6a5fd2ec9e,
arrival-6fa733ab10c745d580180fe59cd2565f, 2026-09-29. Attempt workspace prepared
by this instance per checkout_identity.json (the kanban attempt directory did not
exist at start; `worker_checkout.prepare` was run with the startup assignment).
No pushes, no PRs, no registry writes; the lead publishes to review/MAT2-A06.

## Identity

- Card MAT2-A06, slot 3, branch-3, base c525b82c7c3ce0128565424764293a3c85811ab3.
- Remote (reported, never used): `git@github.com-fleetdeploy:GhostDragonAlpha/Chimera.git`.
- Criteria sha256 31b38a12a8d7a1f28d6b5191e428bab4c11b7267649c549416d85225ee39ecbe.
- done_when (verbatim): "Every grasp-relevant endpoint and waypoint has an
  explicit approved body and role. Material-first addition: Represent
  tissue-to-bone attachments explicitly; ontology containment and conventional
  rig parentage never silently create a mechanical bond."
- Card observation honoured: "Do not reinterpret waypoints as attachment ports".
- Profile: anatomy (visible_static); capture REQUIRED with task_id short form
  "A06"; profile object read read-only from
  E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3
  (kanban.cards[MAT2-A06]...verification_profile); registry card
  criteria_sha256 equals the attempt criteria hash (asserted at capture time).
- Preregistration frozen SEPARATE-FIRST: commit c436b865d4173cd50e8a0ed5bf7a828
  9e540ef42 contains ONLY PREREGISTRATION.md; the validator refuses to validate
  any document whose preregistration_sha256 does not match the live file bytes
  (freeze is git-provable and hash-bound).

## What was delivered (all under tools/monkey_campaign/contributions/MAT2-A06/)

1. PREREGISTRATION.md — frozen before any implementation artifact: the
   grasp-relevant definition, exact counts, role vocabulary, refusal codes,
   falsifiable predictions P1-P9, validation plan, honest limitations.
2. attachment_ownership.py — the ownership registry (stdlib-only, deterministic):
   - Builds chimera.attachment_ownership.v1 from live sha-verified pins:
     monkeyArm_current.osim (4148aee2...), hand.vtp (a06ea7e0...), the A05
     winner's mutation_structure.json (48b03759..., on-disk bytes; the A05
     correction added stl_sha256 fields after the originally recorded
     8d51b551... — the on-disk hash is pinned, recorded in the prereg).
   - 48 path records for the 13 grasp-relevant muscles (definition frozen in
     prereg: any muscle with a PathPoint on osim body `hand`): every record
     carries owner_body (osim body verbatim), role (origin_attachment /
     insertion_attachment / path_waypoint / conditional_waypoint), approved_by
     osim sha, and an honest mutant mapping column (3 A05-recorded mapped,
     14 pending_assembly_mapping — never silently defaulted). The pinned osim's
     ConditionalPathPoint (flex_digit_profundus-P2, radius, radial_pronation,
     range [-1.5708, 0.352382]) is carried verbatim as a conditional waypoint.
   - 6 A05 grasp endpoints (5 fingertips -> distal_thumb/distph2..distph5,
     positions verbatim from the A05 record; palm anchor) with roles
     grasp_contact_endpoint / grasp_palm_reference and Captain-decision
     approval references.
   - 26 explicit tissue-to-bone attachments (one per muscle path endpoint; all
     13 insertions on hand), each with identified interface
     iface:tendon-<muscle>-{origin,insertion}, transfers=force, provenance
     explicit_declaration — an attachment exists ONLY through its interface
     (M05 law).
   - 22 mechanical bonds (the A05 mutant's 20 digit joints + 2 wrist dofs),
     provenance explicit_declaration (Captain decision A05 + A05 criteria sha).
   - 31 containment edges (osim Model frame membership + A05 MJCF rig
     parentage) in a SEPARATE relation list — placement/ontology only.
   - C17 (finite attachment mechanics) left open: every attachment carries the
     required-inputs list with status inputs_unavailable_in_pinned_sources; no
     stiffness/couple number is invented anywhere.
3. test_attachment_ownership.py — 22 unittest cases covering P1-P8 (pins,
   scope counts, ownership, waypoint port rule, explicit attachments,
   no-silent-bond, separation check, byte determinism, C17 honesty) and the
   falsifier probes T1/T1b/T2/T3/T4/T5/T6, each asserting the exact named
   refusal.
4. capture_ownership.py + capture/capture_mat2_a06_ownership_20260929.png +
   evidence/ — visible_static capture, task_id "A06": one 1280x4320 PNG sheet,
   6 rows = 3 profile views x diagnostic/clean (side/oblique row has two
   viewports), pure-PIL orthographic projection of the ownership state + A05
   mutant skeleton over the hand.vtp envelope point cloud; 16-field cameras
   with computed unit quaternions (self-test asserted) and exact distances;
   every row's state_binding is the attachment_ownership.json sha256 (view
   toggles preserve the physical state hash); manifest validated with the
   UNMODIFIED source-head visual_capture.validate_manifest against the
   registry profile.
5. qualification_receipt.json — clause-to-evidence map, commands, falsifier
   proofs, dependency heads, artifact hashes, limitations.

## Commands executed and observed results

All with /c/Python314/python -B from the contribution directory:

1. `attachment_ownership.py --emit --verify` — exit 0; validate_document PASS:
   48 records / 17 hand-body / 26 endpoints / 22 waypoints (21+1 conditional) /
   26 attachments / 22 bonds / 31 containment edges / 6 grasp endpoints /
   3 mapped + 14 pending; live pins verified; separation check true/true.
2. `attachment_ownership.py --tamper-rig --tamper-containment --tamper-unowned
   --tamper-role --tamper-waypoint --tamper-stiffness` — all 6 probes BIT:
   bond_from_parentage_refused x2, unowned_endpoint, unowned_role,
   waypoint_is_not_attachment_port, attachment_stiffness_unsourced.
   - DEFECT FOUND AND FIXED during development (preserved honestly): the first
     validator ordering let aggregate count checks (bond_count_invalid /
     grasp_scope_mismatch) fire BEFORE the semantic refusals on three tampers;
     the validator was reordered so provenance/ownership refusals bite first.
     Final run: 6/6 BIT.
3. `python -m unittest test_attachment_ownership` — Ran 22 tests, OK, 0.025s.
4. `capture_ownership.py` — verdict structurally_valid=True (profile anatomy,
   view_count 6, capture_kind image); ran TWICE, byte-identical PNG both runs:
   capture sha256 3cea13a8ed67d31950367819e61fa403cd38eb6e49536d4259ba1a633c3
   babb0; state sha256 f1f0430772258e8449fc354841becf2f1869783399e63f3f145565b
   8d0b1041c.
   - CAPTURE DEFECTS FOUND AND FIXED (each preserved honestly; intermediate
     sheets were discarded, only the final sheet is committed):
     (a) the side/oblique diagnostic rows piled 17 labels into the cluster and
        clipped text at the right edge (label-ambiguity falsifier risk) — fixed
        with a collision-avoiding labeler (right-edge flip + occupied-box
        search; an unplaceable label is NOT drawn and NOT bound), a spread
        labeled subset for the side viewports (all markers still drawn), and
        required_subject_ids reduced to what is actually drawn;
     (b) thin skeleton/path lines crossed label text — fixed with a backdrop
        rectangle behind every label;
     (c) later markers could overlap earlier labels — fixed by two-pass
        rendering (all markers, then all labels).
   - After fixes every row was visually inspected at 1:1 and 3x zoom: row 0
     overview diagnostic (layers/legend/frame axes/labels legible), row 1
     overview clean (no diagnostics), row 2 close-up diagnostic (ATT/WPT/GRASP
     labels and mapped rings legible), row 3 close-up clean (no diagnostics),
     row 4 side+oblique diagnostic (spread subset legible, no clipping), row 5
     side+oblique clean (no diagnostics). Independent pixel review remains
     mandatory and is not claimed.

## Falsifier proof (per dispatch requirement)

| probe | tamper | observed |
|---|---|---|
| T1 rig-parentage | A05 anchor->firstmc MJCF parent promoted to a bond | BIT: bond_from_parentage_refused:bond.rig_tamper.anchor_firstmc:rig_parentage |
| T1b containment | osim Model-frame containment promoted to an attachment | BIT: bond_from_parentage_refused:attach.containment_tamper |
| T2 unowned | owner body / role stripped | BIT: unowned_endpoint / unowned_role (never defaulted) |
| T3 waypoint port | hand-body waypoint given an interface | BIT: waypoint_is_not_attachment_port:path.abd_poll_longus.3 |
| T4 owner default | resolve_owner called with no explicit owner | BIT: owner_default_refused |
| T5 wrong pin | non-pinned file as osim | BIT: live_source_hash_mismatch |
| T6 stiffness | stiffness claimed without inputs | BIT: attachment_stiffness_unsourced |

Separation check (B04 law): deleting all containment_edges leaves bonds and
attachments digests byte-identical; deleting all attachments+bonds leaves the
containment digest byte-identical.

## Artifact hashes (final)

| artifact | sha256 |
|---|---|
| PREREGISTRATION.md (commit c436b865) | 442b072234ac56c1be6ed43573c12a6b040d844a120d8d6c500dd9b677877242 |
| attachment_ownership.py | 7c9a50900aaf74b786b19b3830f373b648c8dca15e51d0809e72c7abd02797a1 |
| test_attachment_ownership.py | 9fcc62331707aa322e31da69df04e503b3241389e38f936a58c2cb4b99d7d984 |
| attachment_ownership.json | f1f0430772258e8449fc354841becf2f1869783399e63f3f145565b8d0b1041c |
| capture_ownership.py | 534e40b236299dac7c20720333696400a590b0d23e82d6fdc56aada491733408 |
| capture/capture_mat2_a06_ownership_20260929.png | 3cea13a8ed67d31950367819e61fa403cd38eb6e49536d4259ba1a633c3babb0 |
| evidence/cameras.json | 15af7278e83385d334e344333f7732d4674ffd519151f5f8bcef954c52dbe75e |
| evidence/capture_manifest.json | 8588656382ec2543dafc7cb0d0d546a75b9d6a042e6338d18642e9d8c61a72da |
| evidence/capture_context.json | 667c89c2473efe77dbc268bd8fd29fac4de59c5ab54c3d2dca9803f1c69672a5 |
| evidence/validation_receipt.json | e4184177eb9c836babc77be5f9d4e323bed023133551eb3f15d116e99eea5309 |
| qualification_receipt.json | 3994477d5249f90b4b3b8224f3455a9dbb7c940cdc548ee388e2ed134da0a40f |

(qualification_receipt.json carries the authoritative per-file sha256 map
computed after the final render; PREREGISTRATION.md's hash is additionally
bound inside the validated document.)

## Honest limitations

- This is a static ownership registry; no runtime/dynamic claim is made. The
  visible_static profile's runtime phases remain pending and are NOT passed by
  these fixtures.
- The osim stays an independent unmerged reference (B04 record); attachments
  bind osim bodies. Only the 3 A05-recorded anchors carry mutant mappings; 14
  hand-body points are pending_assembly_mapping (explicit inventory, not
  defaults).
- C17 stays open: no attachment patch area/shape, areal stiffness, couple
  resistance or weights exist in the pinned sources; none was invented.
- The capture is a 2D orthographic PIL projection (no 3D renderer/GPU);
  validate_manifest is structural only; author pixel inspection is recorded
  but independent visual review remains mandatory.
- Roles are path-structural (Schutte1993Muscle_Deprecated tendon paths), not
  histological claims; no wrapping surfaces are declared for the 13 muscles.
- The A05 structure pin is the on-disk post-correction bytes (48b03759...),
  not the pre-correction 8d51b551... hash in A05's original report; the
  difference is the review-mandated stl_sha256 metadata correction, declared
  in the prereg.
