# P10 — MAT2-A04 geometry-coverage determination (correction PC-6)

Attempt `c8bb40c32ddb4b01a1c99d7a66582e37`, agent `arrival-749dfd83baf04ac3835e45ef54657633`.
Correction preregistration frozen at `1f2a58b7eddfc992cd3fc9f0394a58bdabde8f23` before
any run. Basis bytes: the merged ONT-A04 evidence at the correction base `4dba6cb1`,
hash-identical to the lead-ACCEPTED ONT-A04 pins (PC-2, 7/7) and re-derived byte-identical
by the probe rerun (PC-3: `numerical_receipt.json` `e3864b16…`, `state_snapshot.json`
`33d3219c…`); the frozen capture bytes (`capture_a04.png` `878eb3de…`,
`capture_manifest.json` `4447058a…`, `capture_receipt.json` `74731438…`) — no rebuild.

## The required result, defined FROM THE MERGED EVIDENCE'S OWN CLAIMS

The done_when clause is "Source and target assembly correspondence is evidenced,
including palm sign and geometry coverage". The merged evidence's own coverage claims,
which define what "geometry coverage" means for this card, are:

1. **Source assembly identity — 27/27.** C1 `identity_pins` (ok=true):
   `mesh_scales_identity=true`, `n_right_geoms=27`, `n_left_geoms=27` — every vendor
   STL of the 27-bone right hand assembly matches its s1 pin at scale [1,1,1]; the
   correspondence inventory (C6) enumerates exactly these 27 source bone IDs plus
   5 port IDs.
2. **Full-assembly placement bound into the visual evidence — 342,111 vertices.**
   `capture_receipt.json → capture_truth.placed_source_vertex_count = 342111` with
   `bounds_check.all_inside = true` across all declared cameras; subjects
   `src/assembly/27_bones` (and its carpal_row sub-subject) and
   `tgt/envelope/distal_band` (and its proximal_segment sub-subject). The whole placed
   source assembly is evidenced inside the capture frame set — nothing outside the
   declared bounds, nothing clipped.
3. **C16 identity-leg topology.** C6 `correspondence_and_coverage_inventory` (ok=true):
   27 source bone IDs, 5 source port IDs with per-port owner map (each port cited to
   its bone: ECRB-P4→3mc, ECRL-P4→2mc, ECU-P6→5mc, FCR-P3→2mc, FCU-P4→pisiform),
   2 target anchors (wrist_R, elbow_R), 1 target band region.
4. **Anchor-class correspondence quality.** C4 `anchor_class_landmarks` (ok=true):
   governing bar 3.5 mm; all five cited anchor sites reproduce within it
   (exact point-to-surface 1.3e-6 … 1.09e-5 m; nearest-vertex metric within
   0.0008 m except the recorded FCU-P4 0.0168 m convention entry — the merged-recorded
   C4 deviation, inside the governing class), with the stricter frozen 19-link rule
   preserved-fired in s2 and NOT used as the governing bar.
5. **Explicit coverage boundary — carried, never hidden.** C6 `covered`:
   13 carpals/metacarpals region-covered by the target band (region homology ONLY,
   scale UNDECIDED); C6 `not_covered`: the 14 phalanges + thumb distal ray with the
   asset-level reason (no IDENTIFIED digit anatomy in the target: 0 digit joints
   source+target, no persistent grooves ≥ 20 mm; distal lobation is sampling-scale,
   not digit structure).

## Verification at the preserved bytes

Every number above was re-derived at the correction base by the frozen probe rerun
(PC-3, all_green=True with exactly the two merged-recorded deviations) regenerating the
numerical leg byte-identically, and the capture half by hash-checking the frozen bytes
against the accepted pins (PC-2). Nothing was re-measured into existence; nothing was
rebuilt.

## Determination

**The 14-phalanges gap does NOT leave the done_when clause unsatisfiable, and no
amendment is requested.** Basis:

- The IDENTICAL clause text (definition `57ded6eb…`, same C01/C16, same profile) was
  already qualified by the merged, lead-ACCEPTED ONT-A04 winner — lead review
  `6e27829fa06c44cc92907bb5fa0273c8`, `done_when_verified: true`, `profile_verified:
  true` — with the SAME explicit 14-phalanges inventory carried in its own C6 record.
  The campaign's accepted reading of "geometry coverage" is therefore: coverage AS THE
  EVIDENCE DEFINES IT — the correspondence evidence covers the hand assembly at the
  scope its own inventory claims (27/27 identity, 342,111-vertex placed assembly bound
  in-frame, band region homology for the 13-bone carpometacarpal ensemble, anchor-class
  correspondence), with every uncovered element NAMED, counted, and reason-recorded.
- The operator's palm decision itself records what it does NOT close: digit structure
  (the 14 phalanges) stays outside this card's closure — owned by A05 ("Acquire or
  author evidenced hand/digit structure"), exactly as the merged record and this
  candidate's `gaps_standing` G3 already state.
- Claiming per-phalanx target coverage would require manufacturing digit anatomy that
  the target asset does not contain — forbidden by the card falsifier (F-D) and by the
  Lieutenant ruling ("never manufacture anatomy"). Silently dropping the gap would be
  the forbidden weakening. Both are refused.

**Amendment decision request: NOT FILED — not needed.** Had PC-6-FIRED (any claim in
legs 1–5 contradicted by the re-verified bytes), the request would have named exactly
the missing scope; it did not fire. The gap stays recorded verbatim, unchanged, in
`reconciliation.json → gaps_standing` (G3, owner A05) and in
`qualification_receipt.json → gaps_standing`. Nothing about the clause, the contracts,
the profile, or any standing gap text was weakened by this correction.
