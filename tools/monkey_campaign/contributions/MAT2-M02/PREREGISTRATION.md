# MAT2-M02 PREREGISTRATION — frozen before implementation

Frozen: 2026-09-28Z, before authoring compile_material_regions.py or any test run
or any capture. Task: MAT2-M02 / planning id M02 — "Compile imported triangles into
explicit material regions" (criteria sha256
792f1c718d505b106cfe0d411be9c40a952cec9afc86e661cf3f64c50d471b0d, attempt
9abf87253e91484cabbb825acb44a7e3, arrival arrival-7f4ff43a4901497a9026e6d7c43ed044,
base revision c4650f0a8a321353d5409ce6244aa5e6a2fe61b2 = origin/astra/gait-capture
which contains the merged MAT2-M01 schema, isolated local branch-3 checkout).

## Frozen statement

The pinned monkey mesh (the seven macaque-arm VTP geometry assets admitted as
geom.macaque_arm.* in the creature graph at the base revision) and a simple
independent shape are COMPILED into explicit `chimera.material_state.v1` material
regions (M01 schema, reused verbatim from
tools/monkey_campaign/contributions/MAT2-M01/material_state.py):

- Units: every imported mesh carries its declared `source_units_to_m` pin
  ([0.001, 0.001, 0.001], mm -> m) from the graph entry; the compiler verifies the
  source blob sha256, applies exactly that scale, and runs a magnitude envelope
  gate on the compiled metre bounds. No other unit conversion exists.
- Orientation: for a closed mesh the compiler demands every undirected edge be
  shared by exactly two triangles, every directed edge appear exactly once
  (consistent winding), and the signed volume be positive (outward).
- Closure: a mesh with zero open edges and consistent outward orientation is a
  volume region (kind "region"); a mesh with open edges is an open surface region
  (kind "shell") and MUST NOT be treated as sealed (no volume claim from it).
- Shell thickness: where a shell thickness is used at all it is an explicit
  authored declaration with provenance; the compiled bone surfaces declare
  thickness null (no source thickness exists; inventing one would fabricate
  tissue). The declaration path is exercised on an authored plate.
- Intersections: triangle-triangle intersection between every pair of compiled
  regions in the common world frame (default pose, source joint transforms) is
  measured and REPORTED per pair; nothing is hidden. Region ownership keeps every
  matter id owned exactly once regardless of geometric overlap, so overlapping
  surfaces never double-count mass.
- Region ownership: one matter id per body (source .osim segment mass, scope
  "effective body segment, not isolated visible bone"), owned by that body's
  single region; zero-mass bodies keep their source zero with provenance.
- Separation: surface subdivision (the imported triangle sets, stored as hashed
  mesh blobs) is a separate artifact from the semantic material assignment (the
  material_state documents); the mapping between them and between the visual mesh
  and the physical mesh is an explicit identity mapping per region.
- Absent internal anatomy is reported, never invented.
- Mechanical connections are the source-declared OpenSim joint chains, emitted as
  explicit bonds (status source_declared) between named region ports; kinematic
  declaration is NOT a qualified reaction force. No contact or bond is implied by
  geometry or proximity.

Two documents are compiled:
1. `monkey_arm_regions.json` (object monkey-arm-regions, revision 1): seven
   regions sternum, clavicle, scapula, humerus, ulna, radius, hand.
2. `independent_shape_regions.json` (object independent-shape-regions, revision 1):
   a simple independent shape authored analytically, NOT derived from the macaque
   data: one closed right tetrahedron (volume region) and one open square plate
   (shell region with authored thickness) that exercises the shell-thickness
   declaration path.

## Frozen pinned-input predictions (from graph entries at base revision; my
compiler output must reproduce these within 1e-9 relative tolerance)

| region | source blob | sha256 (first 12) | tris | verts | signed_volume_m3 | open_edges | kind |
|---|---|---|---|---|---|---|---|
| sternum | Geometry/sternum.vtp | fc688ea2643c | 16 | 10 | 2.6493280581797473e-07 | 0 | region |
| clavicle | Geometry/clavicle.vtp | 84caf2d4724a | 156 | 80 | 1.3101298443114225e-06 | 0 | region |
| scapula | Geometry/scapula.vtp | e9ffe8ef9ad2 | 358 | 180 | 9.136383923955177e-06 | 10 | shell |
| humerus | Geometry/humerus.vtp | 87f6034aa082 | 464 | 234 | 1.2504681471383375e-05 | 0 | region |
| ulna | Geometry/ulna.vtp | 8f80ac47453f | 444 | 224 | 5.699077518562791e-06 | 0 | region |
| radius | Geometry/radius.vtp | 8a2d3f2fe5f8 | 222 | 113 | 5.0558415568324745e-06 | 0 | region |
| hand | Geometry/hand.vtp | a06ea7e079c8 | 3724 | 1920 | 1.5702994816386723e-06 | 18 | shell |

Source masses (pinned .osim body masses, kg): sternum 6.6, clavicle 0.0,
scapula 0.0, humerus 0.203, ulna 0.0922, radius 0.0618, hand 0.049;
arm total (counted once) 7.006 kg.

Independent shape (authored, exact analytic values): right tetrahedron with
vertices (0,0,0), (0.1,0,0), (0,0.1,0), (0,0,0.1) m outward-wound: triangles 4,
open edges 0, signed volume +1.6666666666666667e-04 m3, surface area
0.023660254037844386 m2; authored mass 0.120 kg. Square plate 0.2 m x 0.1 m, two
triangles, area 0.02 m2 exactly, 4 boundary (open) edges, authored thickness
0.002 m, authored mass 0.020 kg; independent total 0.140 kg.

## Frozen positive predictions (checks that must PASS)

P1 (schema): both compiled documents validate through the unmodified M01
`validate_material_state` and round-trip byte-identically through its canonical
encoder; all ids match the M01 id pattern; counts: arm regions 7 (5 region + 2
shell), independent 2 (1 region + 1 shell); bonds 6 (arm) / 0 (independent);
matter rows 7 / 2; every matter row owned exactly once; contacts 0 in both.
P2 (pinned metrics): every compiled region's triangle/vertex counts, signed
volume, surface area and open-edge count equal the pinned table above (arm) and
the analytic values (independent), relative tolerance 1e-9 (areas/volumes),
exact (counts).
P3 (units): every arm region records source_units_to_m [0.001, 0.001, 0.001],
compiled bounds equal raw-parsed-mm bounds scaled by exactly 0.001 per axis, and
every compiled per-axis extent lies inside the envelope [2e-4, 0.6] m; the
independent shapes record source_units_to_m [1, 1, 1] (authored in metres).
P4 (ownership/oracle): M01 `total_mass_once` returns 7.006 exactly (float sum of
the seven pinned values) for the arm document and 0.14 for the independent
document; no reference claims exist in either document at revision 1.
P5 (bonds): the six arm bonds are exactly the source joint chains between
geometry-bearing bodies (sternum-clavicle via sterno_clavicle; clavicle-scapula
via clav_scapular; scapula-humerus via shoulder; humerus-ulna via elbow+ulna1
weld; ulna-radius via ulnar_radial+radius_jcc weld; radius-hand via
wrist_tmp+wrist welds), status source_declared, transfers force_moment, each
endpoint naming an existing region port; no other bond exists.
P6 (mapping): for every region the mesh blob records one visual mesh and one
physical mesh that are the SAME triangle list (identity mapping, equal counts,
single blob sha256 recorded in rest_geometry); visual triangle count == physical
triangle count == pinned count.
P7 (absent anatomy): each document's provenance carries an explicit absent-
anatomy inventory that names at least: no skin/fat surface, no muscle volumes
(39 source muscles are 1D path points only), no organs or internal tissue
surfaces, no layer thicknesses; and states that the compiled regions are bone
surface segments only.
P8 (separation): the material_state documents reference the subdivision only
through mesh-blob sha256 + region keys; mutating a triangle in a mesh blob
changes the blob sha256 but no material assignment id, and the assignment layer
never stores coordinates (structural test).
P9 (render to physics): the capture renderer consumes ONLY the mesh blobs + the
material_state documents (no other geometry source); the manifest binds the
rendered subject by the document canonical sha256.
P10 (capture/validator): 6 manifest views (3 profile view ids x diagnostic/clean),
video lossless ffv1 1280x720, 12 s, 1 fps; validator
visual_capture.validate_manifest returns structurally_valid True with no fired
check; motion requires trace state binding, video locator, 2+ camera samples per
camera, and clean rows carry zero labels/layers/bindings.
P11 (regression): M01's frozen probe suite (test_material_state.py) still passes
unmodified in this checkout.

## Frozen falsifier probes (each must FAIL LOUDLY with the named refusal)

F1 (open treated as sealed): compiling the hand mesh (18 open edges) or the
scapula mesh (10 open edges) through the volume-region path is REFUSED with
named code containing "open_surface_not_sealed"; the compiler emits them only as
shells and the shell rows carry open_edge_count > 0 and volume claim null.
F2 (overlapping matter counted twice): (a) a second owner claim for an already
owned matter id is REFUSED ("duplicate_matter_owner"); (b) two authored test
shapes made to overlap, sharing one matter id as owner+reference, still total
that mass exactly once (total unchanged by overlap).
F3 (subdivision invents tissue): a material assignment that references a
triangle id outside the imported subdivision is REFUSED
("assignment_outside_subdivision"); and a region row without any mesh blob
reference or analytic definition is REFUSED ("region_without_geometry_source") —
no region can exist without imported or declared geometry.
F4 (unit error): recompiling a mm-pinned mesh with the scale pin dropped
(scale [1,1,1]) is REFUSED by the envelope gate with named code containing
"unit_scale_violation" (mm extents ~1e2-1e3 exceed the envelope).
F5 (orientation): flipping the winding of exactly one tetrahedron face is
REFUSED ("mesh_orientation_inconsistent") by the directed-edge rule; flipping
all four faces yields negative signed volume and is REFUSED
("mesh_orientation_negative").

## Frozen capture plan (before any frame exists)

Profile (read-only from registry card MAT2-M02): id material, kind motion,
views ["whole experiment at fixed distance", "orthogonal side and front",
"oblique close-up of the loaded interface"], clean_view_required true, all five
diagnostic layers required, 16 camera fields per camera.

- Renderer: real 3D orthographic projection of the actual compiled triangle
  sets (numpy -> PIL painter's algorithm, depth-sorted, occlusion_mode
  depth_tested), quaternion wxyz camera-to-frame convention, forward -Z, up +Y,
  right-handed, coordinate_unit m, near/far declared. Every declared camera
  number is the number used to project the pixels.
- Views: (1) whole scene at fixed distance (arm + independent shape, one
  viewport); (2) orthogonal side and front (two declared viewports/cameras,
  same state); (3) oblique close-up (25 deg about X) of the elbow interface
  (humerus-ulna bond endpoints humerus.surface/ulna.surface) with at least two
  stable triangle ids labeled at the interface.
- Diagnostic layers: stable membrane/triangle/port IDs rendered; rest/current
  geometry rendered as records (rest == current, revision 1, no solver);
  contact/bond state rendered (bonds; no contacts declared); simulation tick
  rendered as the frame stamp; pressure/force vectors and energy/work are
  EXPLICITLY ABSENT (no solver exists) and are drawn as an absence inventory,
  never fabricated; no material directions are declared (inventory notes the
  absence instead of inventing one).
- Motion interval: degenerate state hold like M01 — tick_interval [0, 1], one
  fixed compiled snapshot replayed identically at both ticks, fixed_bookmark
  cameras, no overlay-driven motion; per-tick canonical-hash invariance is the
  recorded check.
- Disclosure: the profile view name "oblique close-up of the loaded interface"
  is kept verbatim with an on-canvas disclosure that NO contact in state
  "loaded" (or any contact at all) exists at revision 1 — bonds are
  source_declared kinematic connections, not qualified reaction forces.
- Manifest: generated from the drawing code path (the same script that draws the
  labels records the label/layer inventory and camera numbers); subject_sha256 =
  canonical subject binding of the compiled documents + mesh blobs; capture
  sha256 = sha256 of the assembled ffv1 video; validated with
  E:/PythonChimera/tools/monkey_campaign/visual_capture.validate_manifest and
  the registry profile read read-only.

## Honest boundary

Offline compilation and structural qualification of imported geometry into the
M01 schema: no runtime physics, no GPU, no training, no deformable solve; "rest"
and "current" geometry are equal at revision 1. Bones are display-grade research
geometry with unconfirmed scan ancestry (source limitation carried from the
graph). Measured intersections are reported, not resolved. Visual acceptance
belongs to the independent reviewer; the validator receipt is
camera-metadata structure only.

## AMENDMENT A1 (2026-09-28Z, before any successful measurement; all numeric
predictions above unchanged)

Trigger: the assigned base lineage (c4650f0a = origin/astra/gait-capture) does
NOT contain tools/science_funnel/ or tools/creature_graph/; the pinned macaque
intake and the admitted graph snapshot live on a different lineage at recorded
revision eafbc15161ae10ae95b62d07d3f4878aefa34d9d ("Compile pinned macaque
anatomy through the graph into native jointed geometry", 2026-09-16). Before
this amendment, only read-only source inspection and the pin-verification
query above had been run; no compile, test or capture measurement existed yet.

Resolutions (M01 extraction pattern, "committed fixture so probes are
self-contained"):

1. build_pinned_inputs.py extracts, via `git show <rev>:<path>` from the
   attempt checkout (read-only; never modifies any tree):
   (a) every download-receipt-pinned intake file at revision eafbc151, each
   byte-verified against the receipt sha256 AND the graph asset sha pins, into
   the committed data/macaque_arm/ directory (MIT license file included);
   (b) the admitted graph snapshot at the same revision, distilled to the
   macaque rows only (geom.macaque_arm.* asset+metrics pins,
   model.anatomy.macaque_arm model block, ref.macaque_arm.body.*
   world_from_local transforms) into committed data/graph_pins.json with the
   extraction revision recorded. Any mismatch with the frozen pinned table
   above refuses loudly (graph_pin_drift / source_pin_drift).
2. The contribution vendors a small credited adaptation of the qualified VTP
   parser and mesh metrics (tools/science_funnel/macaque_anatomy.py at
   eafbc151) so it is self-contained at the integration base; the vendored
   parser's output is verified against the graph-pinned metrics (P2), which
   are the qualified admitted numbers.
3. Body masses, joints and world transforms come from the distilled admitted
   graph rows (reusing admitted outputs, not re-deriving kinematics).
4. P3's pin cross-checks run against data/graph_pins.json (distilled at the
   recorded revision; identical sha + unit pins). Everything else in the
   frozen statement, predictions, falsifier probes and capture plan stands
   exactly as written above.
