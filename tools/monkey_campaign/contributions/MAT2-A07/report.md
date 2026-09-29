# REPORT — MAT2-A07 "Resolve failed/outside attachment placements lawfully"

Sergeant-implementer record. Attempt 638d4dc8a3384216b526ebc8bc16c3fe,
arrival-2b610e46ac9a41e79daff5bfea970f34, 2026-09-29. Attempt workspace prepared
by this instance per checkout_identity.json (the kanban attempt directory did
not exist at start; `worker_checkout.prepare` was run with the startup
assignment). No pushes, no PRs, no registry writes; the lead publishes to
review/MAT2-A07.

## Identity

- Card MAT2-A07, slot 4, branch-4. The prepared base 9ba1be77 was stale
  (ancestor check) and was fast-forwarded to the sealed tip
  fa8ecf67be01a7ff0dbb4c538ad88b68ef196b5a (astra/gait-capture, carrying A06 =
  PR #250) BEFORE any edit.
- Remote (reported, never used): `git@github.com-fleetdeploy:GhostDragonAlpha/Chimera.git`.
- Criteria sha256 c4d4ae430027d489d58007cae3895b81dcbfa604c045aa35049c3ecf333373f8
  (startup assignment == kanban.cards[MAT2-A07], read read-only from
  E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3).
- done_when (verbatim): "Attachment validity is supported or explicitly
  unresolved; any new fitting experiment is separately authorized".
- Card observation honoured verbatim: "Candidate C remains failed at 67.147
  micrometres per side; four wrist sites outside under both loops".
- Profile: anatomy (visible_static); capture with task_id short form "A07";
  profile object read read-only from agent_slots.sqlite3;
  registry card criteria_sha256 == document criteria_sha256 (asserted at
  capture time).
- Preregistration frozen SEPARATE-FIRST: commit 619ed3ad3919c8e84b7cc29c4d548
  efdafd044fe contains ONLY PREREGISTRATION.md; the validator refuses any
  document whose preregistration_sha256 does not match the live file bytes.

## What was delivered (all under tools/monkey_campaign/contributions/MAT2-A07/)

1. PREREGISTRATION.md — frozen before any implementation artifact: the lawful
   vocabulary (supported / explicitly_unresolved, nothing else), the frozen
   envelope bounds test, the measured outside set (8 records, exact per-axis
   excesses), resolution rules R1-R8, predictions P1-P10, validation plan,
   honest limitations.
2. placement_resolution.py — builds chimera.attachment_placement_resolution.v1
   from the sealed A06 registry (committed bytes pinned
   f1f04307...; any other bytes refuse `a06_registry_pin_mismatch`) + the
   sha-pinned A05 structure + osim/hand.vtp pins:
   - 48 path_resolutions: osim-reference placement supported (pin) for all;
     mutant-assembly placement: 3 mapped -> supported by Captain decision
     A05-DIGIT-MUTATION-20260928 (+ criteria sha + recorded distance verbatim);
     14 pending -> explicitly_unresolved naming
     "recorded_assembly_mapping_decision" (7 measured outside, 7 inside —
     envelope presence creates no ownership, B04 law); 31 forearm ->
     explicitly_unresolved naming "forearm_assembly_correspondence_record".
   - 26 attachment_resolutions: osim-reference supported (explicit_declaration
     + interface, inherited); mutant-assembly follows the path record (2
     supported / 24 explicitly_unresolved); C17 mechanics blocks inherited
     verbatim (open).
   - 22 waypoint_resolutions: never attachment ports (interface=None,
     bond=False, A06 law inherited); 1 supported / 21 explicitly_unresolved;
     the 4 outside hand waypoints carry placement_failed_outside.
   - 6 grasp_endpoint_resolutions: supported (A05 decision + sha).
   - carried_observation block: the Candidate C record verbatim with sources,
     resolved explicitly_unresolved + fitting_not_authorized (missing evidence
     "separately_authorized_fitting_experiment").
   - Envelope measurement: axis-aligned bounds test against the A05-recorded
     hand_vtp_bounds_m; per-axis signed excesses recorded exactly; validator
     RECOMPUTES it and refuses disagreement.
   - Named refusals: a06_registry_pin_mismatch, live_source_hash_mismatch,
     frozen_count_mismatch, resolution_missing, silent_default_refused,
     supported_claim_missing_pin, fitting_unauthorized_refused,
     measured_status_mismatch, location_not_verbatim,
     mutant_mapping_status_altered, attachment_stiffness_unsourced,
     waypoint_is_not_attachment_port.
3. test_placement_resolution.py — 25 unittest cases covering P1-P9 (pins,
   frozen counts, exact outside set and excesses, totality/vocabulary,
   evidence binding, no-fitted-keys, recomputed measurement, registry
   conservation, C17 honesty, byte determinism) and the falsifier probes.
4. capture_resolution.py + capture/capture_mat2_a07_resolution_20260929.png +
   evidence/ — visible_static capture, task_id "A07": one 1280x4320 PNG sheet,
   6 rows = 3 profile views x diagnostic/clean (side/oblique row has two
   viewports), pure-PIL orthographic projection of the resolution state over
   the hand.vtp envelope point cloud + A05 skeleton; markers colored by lawful
   resolution (green filled = supported, amber hollow = explicitly_unresolved,
   red ring = measured outside with the exact excess in the label); 16-field
   cameras with computed unit quaternions (self-test asserted); every row's
   state_binding is the placement_resolution.json sha256 (view toggles
   preserve the physical state hash); manifest validated with the UNMODIFIED
   source-head visual_capture.validate_manifest against the registry profile;
   numerical_evidence carries the 8 outside records with exact floats.
5. qualification_receipt.json — clause-to-evidence map, commands, falsifier
   proofs, artifact hashes, limitations.

## Commands executed and observed results

All with /c/Python314/python -B from the contribution directory:

1. `placement_resolution.py --emit --verify` — exit 0; validate_document PASS:
   48/26/22/6 resolution rows; 3 mapped + 14 pending; 8 measured outside
   (4 insertions + 4 waypoints); attachments 2 supported / 24 unresolved;
   waypoints 1/21; live pins verified; separation check true/true.
2. `placement_resolution.py --tamper-supported-pin --tamper-default
   --tamper-fit --tamper-flip --tamper-stiffness --tamper-registry` — all 6
   probes BIT (table below).
   - DEFECTS FOUND AND FIXED during development (preserved honestly): the
     first T-FIT tamper fired earlier semantic refusals (stale
     missing_evidence, then child-row consistency) instead of the no-fit law;
     the probe was made faithful (lawful row + only the smuggled fitted
     fields) so exactly `fitting_unauthorized_refused` fires. The no-fit key
     scan initially caught the law's own prose key (`measured_not_fitted`);
     the law_statement prose block is now a declared exemption.
3. `python -m unittest test_placement_resolution` — Ran 25 tests, OK, 0.04s.
4. `placement_resolution.py --emit` twice — byte-identical
   (cd596d7c21fa81a4c2632e13b63ba26e62da51d44eca2355147fd5dff1587490).
5. `capture_resolution.py` — verdict structurally_valid=True; ran TWICE,
   byte-identical PNG both runs: capture sha256
   8ada9447414d5ae370695e71d0d232640a268acc1d7a2cbed037b74822aee390; state
   sha256 cd596d7c21fa81a4c2632e13b63ba26e62da51d44eca2355147fd5dff1587490.
   - CAPTURE DEFECTS FOUND AND FIXED (each preserved honestly; intermediate
     sheets discarded, only the final sheet committed): (a) the honest-gaps
     prose clipped at the right edge of the 640px side/oblique viewports —
     fixed with width-aware wrapping (draw_wrapped); (b) a partially occluded
     "WPT" glyph fragment in the overview cluster (rendered glyphs exceeding
     textlength boxes let a later label's backdrop clip them) — fixed with
     margin-inflated occupied boxes in the collision-avoiding labeler.
   - After fixes every row was visually inspected at 1:1 and 2-3x zoom:
     overview diagnostic (wrapped panels, all labels legible, red rings on
     the 8 outside records), overview clean, close-up diagnostic (every OUT
     label with its exact excess legible: z+0.002449870, z+0.001310210,
     z+0.000713400, z-0.000395750, z+0.001190690, z+0.001892820; SUP markers
     green), close-up clean, side+oblique diagnostic (wrist-cluster spread
     labels legible, no clipping), side+oblique clean. Independent pixel
     review remains mandatory and is not claimed.

## Falsifier proof (per dispatch requirement)

| probe | tamper | observed |
|---|---|---|
| T-SUPPORTED-NO-PIN | supported claim stripped of its sha | BIT: supported_claim_missing_pin:grasp.fingertip.thumb:sha |
| T-DEFAULT | pending mapping silently defaulted ("defaulted" state) | BIT: silent_default_refused:path.abd_poll_longus.3:defaulted |
| T-FIT | fitted_mutant_body/fitted_distance_m smuggled into a lawful row | BIT: fitting_unauthorized_refused:path_resolutions:fitted_mutant_body |
| T-FLIP | measured-outside record relabeled inside | BIT: measured_status_mismatch:path.abd_poll_longus.3 |
| T-STIFFNESS | stiffness injected into an inherited C17 block | BIT: attachment_stiffness_unsourced:altered:attach.abd_poll_longus.origin |
| T-PIN | mutated A06 registry (location edited) | BIT: a06_registry_pin_mismatch |

Separation: the A06 registry digest is pinned and unchanged; the carried
blocks (observation, envelope test) are independent of the resolution rows.

## The lawful resolution, in one view

- SUPPORTED (pinned evidence): 3 A05-recorded mutant mappings (2 insertion
  attachments + 1 waypoint, incl. the outside-bounds waypoint whose mapping
  stands with the outside measurement recorded as a declared deviation),
  6 grasp endpoints, and the osim-reference placement of all 48 records / 26
  attachments / 22 waypoints.
- EXPLICITLY UNRESOLVED (named missing evidence): 14 hand-body points with no
  recorded assembly-mapping decision (7 measured outside); 31 forearm records
  (A05 mutation scope is the hand); the carried Candidate C record (missing
  evidence: a separately authorized fitting experiment; the sealed record
  itself states none is authorized).
- MEASURED OUTSIDE (frozen bounds test, all Z-axis): 8 records — insertions
  ext_carpi_rad_longus.3 (+0.0000727770 m), ext_indicis.3 (+0.001892820 m),
  flex_carpi_ulnaris.2 (-0.000395750 m), palmaris_longus.3 (-0.000427250 m);
  waypoints abd_poll_longus.3 (+0.002449870 m), ext_carp_rad_brevis.2
  (+0.000713400 m), ext_digiti.2 (+0.001190690 m), ext_digitorum.2
  (+0.001310210 m). Exactly 4 outside INSERTIONS — the same count as the
  carried observation's "four wrist sites outside", recorded as convergence
  context only (the historical loops were not re-run).
- NO FITTING was run, simulated, or recorded anywhere.

## Artifact hashes (final)

See qualification_receipt.json artifact_sha256 (authoritative). Key values:
placement_resolution.json cd596d7c21fa81a4c2632e13b63ba26e62da51d44eca2355147f
d5dff1587490; capture PNG 8ada9447414d5ae370695e71d0d232640a268acc1d7a2cbed037
b74822aee390; PREREGISTRATION.md a54fec6082de6aa395796bf98ad015057da58d951cae8
5f1ae9786d4b19f6e1c (bound inside the validated document).

## Honest limitations

- Static completion-of-record only; no runtime/dynamic claim; the visible_static
  profile's runtime phases remain pending and are NOT passed by these fixtures.
- The 14 pending mappings and the Candidate C record remain explicitly
  unresolved BY LAW: resolving them requires recorded lead/captain decisions
  (and, for the observation, a separately authorized fitting experiment) that
  do not exist and were not invented.
- The historical candidate-loop receipts were not re-located in this attempt;
  the loops were not re-run (that would be the unauthorized fit).
- The envelope test is an axis-aligned bounds measurement, not a mesh-inside
  test.
- The capture is a 2D orthographic PIL projection (no 3D renderer/GPU);
  validate_manifest is structural only; independent visual review remains
  mandatory and is not claimed.
- The A05 live pin verifies only when the A05 attempt workspace exists; the
  envelope bounds are frozen preregistration constants, equality-checked
  against the live file whenever present.
- C17 stays open; nothing was invented.
