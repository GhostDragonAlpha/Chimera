# MAT2-M02 report — compile imported triangles into explicit material regions

Attempt 9abf87253e91484cabbb825acb44a7e3, arrival
arrival-7f4ff43a4901497a9026e6d7c43ed044, criteria sha256
792f1c718d505b106cfe0d411be9c40a952cec9afc86e661cf3f64c50d471b0d. Isolated
attempt checkout of E:\PythonChimera at base c4650f0a8a321353d5409ce6244aa5e6a
2fe61b2 (= origin/astra/gait-capture, which contains the merged MAT2-M01
schema), local branch branch-3; no pushes, no PRs. Preregistration
(PREREGISTRATION.md + Amendment A1) was frozen before implementation and
before any measurement; the capture preregistration (PREDICTIONS.md in the
capture workspace) was frozen before any capture code existed.

## done_when clause map (all clauses executed on the exact candidate revision)

| clause | execution | result |
|---|---|---|
| Import the pinned monkey mesh | 7 admitted geom.macaque_arm.* VTP assets extracted byte-verified at recorded revision eafbc151 (Amendment A1) and compiled | 7 regions, pins verified (graph + receipt) |
| and a simple independent shape | authored analytic right tetrahedron (closed, volume) + open square plate (shell, authored thickness) compiled through the same path | 2 regions, analytic values reproduced exactly |
| check units | source blob sha pins + declared source_units_to_m [0.001 x3] applied; metre-envelope gate; F4 probe | green; dropped mm pin refused `unit_scale_violation` |
| orientation | directed-edge consistency + positive signed volume; F5 probes | green; flipped face refused `mesh_orientation_inconsistent`; inverted solid refused `mesh_orientation_negative` |
| closure for volume regions | undirected edge rule; closed+outward -> region, open -> shell that never claims volume; F1 probe | 5 arm regions closed (sternum, clavicle, humerus, ulna, radius); scapula (10 open edges) + hand (18) are shells; hand/scapula refused as sealed volumes (`open_surface_not_sealed`) |
| shell thickness where used | plate: authored 0.002 m with provenance; bone surfaces: thickness null, none used, none invented | green; thickness always explicit |
| intersections | triangle-triangle (Moeller) between every region pair in the common world frame at the default pose | arm: 0 of 21 pairs intersect (8 share AABBs, 0 intersecting triangles); independent shape disjoint from all (frozen margins 0.08-0.10 m); every pair recorded in provenance.intersection_check |
| region ownership | one matter id per source body mass (admitted .osim masses incl. two zero-mass shoulder-girdle bodies), owned exactly once; F2 probes | arm total 7.006 kg counted once; independent 0.14 kg; second owner refused `duplicate_matter_owner`; overlap never double-counts |
| separate surface subdivision from semantic material assignment | triangle sets live in hashed mesh blobs; documents reference by sha256 and embed no coordinates; assignment bounds checked; F3 probes | green; out-of-subdivision assignment refused `assignment_outside_subdivision`; geometry-less region refused `region_without_geometry_source` |
| report absent internal anatomy | explicit inventory in both documents' provenance (no skin/fat, no muscle volumes - 39 muscles are 1D paths, no organs, no layer thicknesses, no directions/laws) | green |
| preserve visual mesh and physical mesh mapping | per-region identity mapping: visual triangle list == physical triangle list (same blob, equal counts); the capture renders exactly these triangles | green |

## Checks run (exact commands, candidate revision)

Run from the attempt checkout root with /c/Python314/python:

1. `python -B tools/monkey_campaign/contributions/MAT2-M02/compile_material_regions.py`
   -> emits monkey_arm_regions.json, independent_shape_regions.json,
   monkey_arm_independent_meshes.json (blob sha256 51d8231e0d1eacd7...),
   compile_receipt.json; both documents pass the unmodified M01 validator at
   emission.
2. `python -B tools/monkey_campaign/contributions/MAT2-M02/test_material_regions.py`
   -> "checks: 142/142 passed ... ALL FROZEN PROBES GREEN (P1-P9, P11,
   F1-F5)" (P11 = unmodified M01 probe suite, still green).
3. `python -B tools/monkey_campaign/contributions/MAT2-M02/render_material_regions.py`
   -> material_display.json numerical-evidence display.

Preserved intermediate failures (fixed before the final green run; details in
the capture workspace EVIDENCE.md section 6): missing tools.science_funnel on
the base lineage (resolved by Amendment A1 extraction + vendored credited
parser), ndarray conversion bug in pair_intersections, M01 bond-schema field
rejection (provenance moved to document provenance), and five test-side fixes
(refusal codes and compiler behavior unchanged). The falsifier probes
themselves are the recorded intended failures: F1-F5 all bite with the named
codes.

## Motion-profile capture (visual evidence, material profile)

Built per the M01 discipline in
`E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-M02\capture-evidence-20260928\`
(preregistered in PREDICTIONS.md before any capture code; full record in its
EVIDENCE.md):

- Real 3D orthographic renders of the compiled triangle sets; 6 manifest views
  (3 profile view ids x diagnostic/clean), 12 lossless FFV1 frames 1280x720,
  12 s, 1 fps; degenerate state hold (no solver at revision 1).
- Cameras: whole 3/4 view (position [1.096786, -0.667424, 0.508239], distance
  1.2 m, span 0.375456 m); orthogonal front (span 0.527632 m) + side (span
  0.179512 m) viewports; oblique 25 deg close-up of the humerus-ulna elbow
  interface (span 0.05 m; target and labeled triangle ids tri:humerus#66 /
  tri:ulna#120 from ONE function; centroid distance 0.0012035 m).
- Every declared camera number is the number that projected the pixels;
  manifest visibility claims are generated by the drawing code path
  (evidence/visibility.json); clean rows carry zero diagnostics; absence
  inventory (force vectors, energy/work, directions, contacts, bone
  thickness) drawn on every diagnostic frame instead of fabrication.
- `visual_capture.validate_manifest` (profile read read-only from registry
  card MAT2-M02): structurally_valid=True, fired=[], capture_kind video,
  view_count 6, visual_acceptance=false (gate decision belongs to the
  independent visual reviewer).
- Identity: run_id mat2-m02-visual-20260928-74774685; subject sha256
  51ab4eaa02d9cbf0a52f4cc77a184e5db27ab98b85359cf1285c4b6ca35a7930 (composite
  of both documents' canonical hashes + mesh blob hash); capture sha256
  74774685213c6146ffce824ccff0ecf1dcda9ccc10b54dffcf0ee27a963f2498.

Key evidence hashes: capture .mkv
74774685213c6146ffce824ccff0ecf1dcda9ccc10b54dffcf0ee27a963f2498;
capture_manifest.json d70637f7a97f445c68470490783aa1fe6e61ce8cc529bef6889e5ce
2c0089843; display_trace.json e546267e1476dbdeadda69f6f82f10e65e3832d23008c17
f237276b2c1d5b995; validation_receipt.json d16bd67820dbe8b7a03676c5cfd99ea73
9e72395fe9ce2d4213c06d73795ce45; PREDICTIONS.md
7526b1d54d6ea86548206ab146f6629f7f0e08c40f6cb636e476db60f8748d37.

## Honest limitations

- No runnable material solver exists at revision 1: rest == current, the
  motion interval is a state hold, and force/energy evidence is inventoried
  absence. Runtime-facing visual evidence remains deferred (M03/M04,
  MAT-PRESSURE).
- The pinned intake lives on a different lineage; it is extracted and
  byte-verified at the recorded admission revision (Amendment A1) rather than
  imported from the base tree. The vendored VTP parser/metrics are a credited
  adaptation of the qualified code, verified against the admitted graph
  metrics.
- Measured non-intersection is pose-dependent (default pose), not a general
  claim; intra-mesh self-intersection is not claimed either way (source
  qualification limit).
- The independent shape is authored (analytic), not a second imported mesh;
  its masses are authored at chosen fidelity with explicit provenance.
- visual_acceptance is false by design in the validator receipt; human/independent
  visual acceptance is outstanding.

## File identities (sha256, this directory)

Computed at commit time and recorded in the handoff message: PREREGISTRATION.md,
compile_material_regions.py, build_pinned_inputs.py, test_material_regions.py,
render_material_regions.py, monkey_arm_regions.json,
independent_shape_regions.json, monkey_arm_independent_meshes.json,
material_display.json, compile_receipt.json, data/graph_pins.json,
data/macaque_arm/* (10 receipt-pinned files + LICENSE).
