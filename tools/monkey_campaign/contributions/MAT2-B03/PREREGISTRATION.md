# MAT2-B03 PREREGISTRATION — frozen before implementation or measurement

Frozen: 2026-09-28Z, before derive_material_volume_input.py, the test suite, the
renderer or any capture code was written, and before any new number was
measured. This file is committed as the first candidate commit on the attempt
branch. Task: MAT2-B03 "Produce real validated material-volume input".
Attempt: 845efd334f914a5197b00f670f6c344a. Arrival:
arrival-fe837f4a12534d63b9e7f32759726ee0. Criteria sha256:
a68706372065cef87c1151c1b3af6b139865fff795c5e99af290dd7be4f8ecd1.

## Frozen execution identity

- Attempt workspace:
  E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-B03\845efd334f914a5197b00f670f6c344a
  (prepared by tools/monkey_campaign/worker_checkout.py prepare; sparse paths
  contributions/MAT2-B03 (writable) plus read-only input trees MAT2-M01 and
  MAT2-M02).
- Attempt branch branch-1 fast-forwarded locally from c525b82c to the merged
  integration tip 986f270ef24cda0008c52bd40d4b6d08565c0692
  (origin/astra/gait-capture), which contains the exact-revision inputs this
  card depends on (MAT2-P02 and MAT2-M02). No push, no PR, no shared-branch
  checkout; the lead publishes.
- All new work lives under tools/monkey_campaign/contributions/MAT2-B03/.
  Existing M01/M02 files are read-only inputs; no existing valid work is
  modified.

## Frozen input identities (sha256, recorded at freeze time)

| role | path (from contributions/) | sha256 |
|---|---|---|
| schema authority (unmodified M01 validator) | MAT2-M01/material_state.py | b6b009713daa4b315c6b5cb43c7ad4e756123b50edcdd802eeebd55c6afd6c40 |
| M02 arm regions document | MAT2-M02/monkey_arm_regions.json | 15ae0e5a3d540d52b9a0e5c9b8af2f8a6bf7f2c9770a5f2cd7c1e9e8758366f1 |
| M02 independent shape document | MAT2-M02/independent_shape_regions.json | 0f0b7165883183446b15b7043fd5471f0b12d6d992ffabc27107f4de1238887e |
| M02 mesh blob (vertices + triangles) | MAT2-M02/monkey_arm_independent_meshes.json | 51d8231e0d1eacd7f0d4b558699f011e35ff765f5d0e07ef5889ded27216a834 |
| M02 compile receipt | MAT2-M02/compile_receipt.json | 7192aed9a373e3ee639fafa44d4e86132eb3b37fb8187157ec906d399b8e430f |
| M02 graph pins (admitted metrics, body frames, 39 muscle path sets) | MAT2-M02/data/graph_pins.json | 849f9988d1a6ccb451bb45d79f298dd954c4e5605acd19d7d882a5c70a285b97 |
| density source (archived matter library, byte-identical extract in this directory) | data/matter_library_1af0bbde.json (extract of MAT2-B02/work/frozen/1af0bbde/Chimera/docs/matter/matter_library.json) | de10200fb87bf48c3cc80d5e223805f02e27df115b91186f42f28064a64054ed |

If any pinned input at derivation time fails its sha256 check, the derivation
refuses (`input_pin_mismatch:<path>`) and the attempt records the failure; no
silent re-pin.

## Frozen reconciliation (clause map at arrival, read-only)

done_when: "Actual geometry, material ownership and density source support a
complete input for the selected body. Material-first addition: Author only the
matter required at selected fidelity, with mass/volume ownership and density
provenance; static meshes do not implicitly provide interiors."

- Actual geometry: PRESENT upstream (M02 compiled 7 regions from the pinned
  macaque arm VTP assets at recorded revision eafbc151, blob
  51d8231e0d1eacd7...). Not yet a complete volume input: no density, no
  integrated mass, no COM/inertia anywhere on the line for this body.
- Material ownership: PRESENT as .osim effective body-segment mass claims
  (M02 matter rows, 7.006 kg total, sternum body 6.6 kg). These are
  segment-level claims, explicitly "effective body segment, not isolated
  visible bone". They are not volume-owned mass and carry no density.
- Density source: ABSENT at arrival for this body (Buffy 02 observation stands:
  bbox scale/origin/basis supply neither volume nor density; M02 deliberately
  compiled none). First unmet clause: density provenance + volume-owned mass
  inventory (C02) + COM/inertia (C03).
- Dependency verdicts: P02 present on the base tip (contributions/MAT2-P02,
  qualification_receipt.json); M02 present at its merged revision (files
  pinned above). Both satisfied; no decision request needed.

## Frozen design decisions (made now, before any measurement)

D1 Selected body and fidelity: the macaque forelimb material regions exactly
as compiled by M02 (object monkey-arm-regions). Matter is authored ONLY where
the actual geometry supports it: uniform apparent bone density inside the five
closed bone regions (clavicle, humerus, radius, sternum, ulna). No
heterogeneous density field, no muscle volumes, no skin/fat, no organ matter:
none is authored because none is supported by pinned geometry (absences are
inventoried, not filled).

D2 Density source and conditions: archived matter library entry
`materials.bone.physical.density_kg_m3` (mean 1800 kg/m3, spread 150 kg/m3,
provenance class "researched"; biomechanics-review citation recorded in the
library bytes). Authored value for every counted region: the mean 1800.0 kg/m3;
the spread is carried as the source uncertainty band [1650, 1950] kg/m3 and is
NOT averaged in. Condition statement (frozen, honest): the source library does
not state temperature/moisture/strain-rate conditions for this entry; the value
is treated as apparent cortical bone density at reference (near-ambient, wet
tissue) conditions, and this under-specification is recorded as a limitation
rather than fabricated precision. MAT-03 honesty rule: citing the library
provenance is NOT claimed to be proof of authentic measurement; the source
class stays "researched" with its citation.

D3 Counted set (volume ownership): exactly the five closed regions
(closure "closed_outward_consistent" per M02). The two open surfaces (scapula,
10 open edges; hand, 18) are shells: they claim ZERO volume-owned mass —
static meshes do not implicitly provide interiors (F3 falsifier bites this
exact refusal). Per-region counted mass m_i = rho * V_i with V_i the region
volume and rho the D2 density; uniform density makes the integral reduce
exactly to rho*V (stated, not approximated).

D4 Excluded claims (C02 output requires them explicit): (a) the M02 .osim
effective segment masses for all seven bodies (clavicle 0.0, hand 0.049,
humerus 0.203, radius 0.0618, scapula 0.0, sternum 6.6, ulna 0.0922 kg) are
recorded as excluded segment-level claims with reason "effective body segment
mass from the admitted .osim row; not owned by this bone-geometry input; not
counted"; (b) shell regions carry no volume mass; (c) surface mass is not
represented (no authored shell thickness exists for bone surfaces per M02).
The M01 validator total of the emitted document equals the counted total —
the validator's total and the C02 counted total are forced to be the same
number by construction, and the excluded claims live in provenance.

D5 Frames: volumes/masses are frame-invariant; COM and inertia are authored in
the M02 default-pose world frame ("world:default_pose", the admitted
world_from_local transforms carried by the blob's world_vertices_m) and
additionally per region about its own COM. Aggregate COM/inertia = mass-weighted
combination over the counted set only.

D6 Matter ids: new volume-owned matter ids `bone_<region>` (no identity
collision with M02's `mass_<region>` claim ids; M02's document is not
modified). Each region keeps exactly one owner (F6 bites double ownership via
the unmodified M01 refusal). Shell regions are owned by `shell_<region>`
matter rows with mass_kg 0.0 and provenance recording the excluded .osim
claim.

## Frozen calculations and acceptance tolerances

C02 mass inventory: m_i = integral rho dV = rho * V_i (D3); counted total
M = sum m_i over the five counted regions. Verification (all must pass):
- V1 volume cross-method: divergence-theorem surface integral (method A) vs
  independent tetrahedral decomposition from an arbitrary fixed interior
  origin with parallel-axis combination (method B) agree to relative 1e-9 per
  region.
- V2 continuity with admitted pins: per-region volume equals the M02 emitted
  volume_claim_m3 AND the admitted graph-pin metrics signed_volume_m3 to
  relative 1e-12 (same triangle sets; larger drift = broken pipeline).
- V3 analytic cell: unit-axis-aligned cube mesh through the same pipeline
  reproduces V = s^3, mass = rho*s^3, COM = center, inertia diag = m*s^2/6
  with zero off-diagonals to relative 1e-9; right tetrahedron (a=b=c=0.1)
  reproduces its closed-form V = a^3/6 and inertia to relative 1e-9.
- V4 disjoint ownership: counted regions remain pairwise non-intersecting per
  the M02 recorded intersection check (re-read, not re-measured; re-measuring
  intersections is M02's evidence, freshness pinned by blob sha).
- V5 counted total equals the unmodified M01 validator total of the emitted
  document exactly.

C03 COM and inertia: c = (integral rho x dV)/m and
I_c = integral rho[(r.r)Id - r r^T]dV over the counted set in the
world:default_pose frame; full symmetric 3x3 including off-diagonals emitted.
Verification (all must pass):
- W1 independent quadrature: COM and inertia from method B (tetra
  decomposition, per-tet exact formulas + parallel axis) match method A
  (divergence-theorem volume integrals) to relative 1e-9.
- W2 rotation covariance: for two fixed preregistered rotations (30 deg about
  +Z, then 25 deg about +X — Rodrigues, seed-free deterministic), recomputing
  inertia of the rotated geometry and comparing R I R^T agrees to relative
  1e-9; COM maps as R c.
- W3 parallel-axis recombination: sum over regions of
  (I_i,com + m_i (|d|^2 Id - d d^T)) equals the directly computed aggregate
  inertia to relative 1e-9; aggregate COM equals the mass-weighted mean to
  absolute 1e-15 m.
- W4 symmetry + positive-definiteness of the emitted tensor (symmetry exact
  by construction check, eigenvalues > 0).
- W5 excluded claims contribute nothing: recomputing aggregate quantities
  with shells included at zero mass is byte-identical.

## Frozen falsifier probes (each: tamper a COPY, watch the named refusal, discard; committed artifacts are never modified)

- F1 mass_inventory_tamper: +1% on one mass_kg in a copy of the emitted
  document must refuse `mass_inventory_mismatch:<region>` at re-verification.
- F2 density_provenance_missing: delete the density_source block in a copy ->
  `density_source_missing`; corrupt the library sha pin -> `input_pin_mismatch`.
- F3 shell_volume_claim: give a shell copy a positive volume-owned mass ->
  `shell_volume_claim_refused` (the card's "static meshes do not implicitly
  provide interiors" refusal).
- F4 density_unit_tamper: replace 1800.0 with 1.8 (g/cm3 slip) in a copy ->
  `density_unit_scale_violation` (density outside the physical envelope gate
  [500, 3000] kg/m3 for authored bone matter).
- F5 rotation_covariance_tamper: substitute the unrotated tensor for the
  rotated one in a verification copy -> `rotation_covariance_violation`.
- F6 duplicate ownership: add a second owner claim in a copy -> unmodified
  M01 refusal `duplicate_matter_owner`.
- F7 blob_pin_tamper: one vertex coordinate changed by +1e-6 in a copied blob
  -> `mesh_blob_sha256_mismatch`, and its recomputed volume fails V2 ->
  `volume_continuity_violation`.
Every F-probe output (command, refused code, tampered-copy path, discard
confirmation) is recorded under work/runs/ in the candidate commit. A falsifier
that does not bite is a failed review, not a adjusted tolerance.

## Frozen predictions (arithmetic on already-admitted pin numbers; reproduction of these numbers by the implementation is the prediction)

rho = 1800.0 kg/m3 on the five counted regions, V from the admitted graph-pin
metrics (849f9988...):

| region | V (m3, admitted pin) | predicted mass (kg) |
|---|---|---|
| clavicle | 1.310129844311e-06 | 0.002358234 (0.002358233719760...) |
| humerus | 1.250468147138e-05 | 0.022508427 (0.022508426664849...) |
| radius | 5.055841556832e-06 | 0.009100515 (0.009100514802297...) |
| sternum | 2.649328058180e-07 | 0.000476879 (0.000476879050472...) |
| ulna | 5.699077518563e-06 | 0.010258340 (0.010258339533413...) |
| counted total | — | 0.044702394 (0.044702393770792...) |

Predicted document shape: chimera.material_state.v1, 7 regions (5 region +
2 shell), 7 matter rows (5 bone_* with D3 masses, 2 shell_* rows at 0.0),
validator total_mass_kg == counted total above; aggregate COM inside the arm
world AABB (M02 measured x [-0.0554, 0.4237], y [-0.1405, 0.0225],
z [-0.0567, 0.0997]); emitted tensor symmetric with positive eigenvalues.
Humerus is predicted to dominate the counted mass (~50.35% of total). Any
prediction miss is reported as a failed prediction and investigated; silently
adjusting the frozen table is prohibited.

## Frozen visual capture plan (profile "anatomy", kind visible_static)

- Profile read read-only from registry card MAT2-B03 at validation time; views
  verbatim: "whole-creature overview", "local attachment close-up",
  "orthogonal side and oblique views"; clean_view_required true; all six
  diagnostic layers must be covered by diagnostic views: outer envelope,
  selected bones/joints, muscle/tendon paths, attachment sites, frame axes,
  stable 3D labels.
- Artifact: 6 lossless PNG frames 1280x720 (3 views x diagnostic/clean pairs),
  rendered by a deterministic pure-Python orthographic z-buffer rasterizer
  from the emitted input document + pinned mesh blob (depth-tested triangles,
  fixed per-region colors). No solver exists at revision 1: the state is a
  hold; the capture subject hash binds exactly the emitted document + blob.
- Manifest/context task_id: the SHORT form "B03" (registry qualification id),
  not "MAT2-B03" — recorded here because two prior cards failed acceptance on
  this exact defect. visual_capture.validate_manifest must be run before
  handoff; its structural receipt is included, and visual acceptance itself
  belongs to the independent reviewer.
- Cameras: every one of the 16 profile-required camera fields present per
  view; orthographic, metres, right-handed, quaternion wxyz camera-to-frame
  convention verified by round trip against the declared basis; near/far
  [0.01, 5.0]; fixed bookmark samples.
- Muscle/tendon paths layer: drawn from the pinned graph_pins model (39
  muscles, path points with body + location_m), rendered as source-declared
  1D polylines labelled "path points only — no volume authored"; if extraction
  proves impossible, the layer is inventoried absent on the diagnostic frames
  instead of fabricated.
- Frame-composition falsifier (profile): view toggles must preserve the
  physical state hash — the same state hash appears on every frame; the clean
  rows carry zero diagnostics. A second-stage capture predictions file
  (PREDICTIONS.md with scene/camera numbers) is frozen after the input
  document exists but before any capture code runs.

## Out of scope (recorded, not attempted)

No engine integration, no runtime solver, no muscle volume/skin geometry
authoring, no new meshes, no .osim segment-mass replacement (excluded claims
only), no master merge, no push (the lead publishes). If a frozen clause
cannot be met, the attempt records the gap honestly rather than widening
scope.
