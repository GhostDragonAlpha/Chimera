# PREREGISTRATION AMENDMENT (DRAFT v1) — SPECIES-HAND CONTINUATION: the rim-aware capped oblique-cut extraction (Stage 0 continuation)

- Lane: `wk-species-hand`, `E:/ChimeraWork/monkey-coordination/species-hand/`.
  Status: DRAFT for the Lieutenant's pin. This amendment is a NEW declared
  prereg addition THROUGH THE PIN LAW: the Lieutenant commits this file
  ALONE FIRST on the publication lineage (proposed contribution path
  `tools/monkey_campaign/contributions/SPECIES-HAND-20261004/PREREG_AMENDMENT_CONTINUATION.md`);
  the committed bytes are the freeze; the continuation implementation
  package pins the amendment commit and refuses on bytes mismatch. It
  amends and extends ONLY the Stage-0 method (section 2) of the committed
  prereg (c31227e9..., blob `77513d08...`); every other section of the
  committed prereg stands unmodified (the instrument, tolerances, families,
  predictions-UNKNOWN discipline, falsifiers FA1-FA6, report law).
- NO_WORKTREES honored (slots 2/3); NO physics runs in this amendment's
  scope; the ladder remains gated behind the re-review below.

## 0. What this amendment is (and the verdict it responds to)

The Sergeant's visual labeling review (verdict recorded chain-side: PASS w/
the gate consequence) measured the Stage-0 extraction against reality:
cand2 is the RIGHT hand, cand3 is the LEFT hand, cand0 is MUSEUM HARDWARE,
and **0/14 cand2 parts resolve to a single A05 bone — all GROUP/OTHER =
UNRESOLVED_BONE**; the bones fuse in webbing and the extracted parts are
thin 1.5-1.9mm wall shells — SURFACES, not volumes. The Lieutenant's branch
ruling: OPTION (B), the named continuation — this amendment — with the
honest UNRESOLVED closure (0 verdict-bearing bones from this source at this
method) recorded as the fallback that FIRES if the continuation's own
review fails. The Captain's both-in-parallel ruling supports pursuing the
extraction; nothing here touches any ladder quantity.

## 1. Recorded review-derived constants (inputs from the visual review; NEVER from any ladder quantity)

- cand2 = right hand; cand3 = left hand; cand0 = museum hardware (excluded
  from the continuation; its diagnostic receipt stands as the hardware
  lesson record); cand1 = unresolved class (not a hand per the verdict).
- cand2's 14 parts: all GROUP/OTHER = UNRESOLVED_BONE; walls 1.5-1.9mm;
  bones fuse in webbing.
- The wrist of cand2 sat inside the chosen end bin — the end-bin RULE was
  not the failure; the AXIS-ALIGNED plane REPRESENTATION was (the pose is
  oblique). Hence: continuation cut planes are POSE-ALIGNED OBLIQUE planes,
  NEVER axis-aligned end-bin planes (falsifier FA8).

## 2. The declared continuation method (constants frozen BEFORE implementation)

For each hand candidate (cand2, cand3):

- C1 LARGER BOXES: the candidate box grows by `GROW = 30` mm on ALL six
  sides (clipped to the skeleton AABB) so the hand + wrist + distal
  forearm enter the extraction volume.
- C2 POSE-ALIGNED OBLIQUE FOREARM CUT: a single cut plane per candidate,
  given as POINT p0 (source units) + UNIT NORMAL n (pointing proximal).
  PRIMARY source: the Sergeant's recorded wrist identification (the re-review
  below supplies p0/n per hand; they are review-derived constants, recorded
  in the sealed receipt). DECLARED FALLBACK (only if the record is absent):
  n = principal axis of the voxels with EDT >= 1.0mm inside the box's
  proximal half; p0 = the centroid of those voxels; both recorded. Triangles
  with ANY vertex satisfying dot(x - p0, n) > 0 are excluded (any-vertex
  rule); an oblique sealing slab `|dot(x - p0, n)| <= 2 voxels` bounds the
  fill; everything beyond the plane is removed; faces toward the removed
  region are charged as authored cuts.
- C3 RIM-AWARE CAPPING: at each of the six box faces, seal ONLY the rim
  components that actually touch the face (per face: the shell voxels lying
  in the boundary layer, grown 2 voxels inward, per connected component).
  NEVER a full-face slab (the v4 defect: full-face caps enclose the outer
  background and fill the whole box).
- C4 PER-AXIS 2D SLICE FILLS: solid = 3D_fill(shell+caps+slab) UNION
  (union over the 3 axes of per-slice 2D fills of the shell). The over-fill
  risk (a 2D fill seals any cross-section that happens to be closed,
  including genuine air gaps between fingers) is DECLARED and mitigated by
  the fill-validity gate (C6), the opening-based webbing test (C5), and the
  re-review (section 5).
- C5 ANTI-WEBBING OPENING, SEPARATION ANALYSIS ONLY: markers come from the
  EDT of `opened = binary_opening(solid, ball radius 1 voxel)`; the Voronoi
  assignment runs on the UNOPENED solid (the mesh source stays the un-opened
  fill — fidelity to the source bytes). Robustness column r = 2 voxels,
  recorded never decisive. FA9: applying any opening to the GEOMETRY
  (the exported meshes) is forbidden.
- C6 FILL-VALIDITY GATE (gating): the post-fill solid must show VOLUME
  interiors — median EDT >= 0.8mm over the solid AND >= 40 percent of solid
  voxels with EDT >= 0.8mm — else the candidate is recorded THIN_SHELL
  (surfaces, not volumes) and STOPS (no labeling request from it). The
  EDT-decile + h-sweep diagnostic runs on every extraction (the cand0
  lesson).
- C7 THIN-SHELL GROUP LAW (standing, codifying the Sergeant verdict): any
  part with max EDT < 0.8mm (the declared minimum half-thickness of a
  verdict-bearing bone) is classed THIN_SHELL = SURFACE = UNRESOLVED_BONE,
  never verdict-bearing, regardless of its cut fraction. The ladder
  consumes watertight VOLUME meshes; feeding surface shells to it would
  falsify the instrument's predicate — this is the thin-shell consumption
  note, binding on every downstream card.
- C8 UNCHANGED: voxel size 0.30mm; 16-point barycentric sampling; shell
  dilation 1; h-maxima floors (0.8mm min EDT, h=0.20mm; robustness h=0.10mm
  recorded never decisive); component-wise Voronoi; fragment merge < 15mm^3;
  UNRESOLVED ceiling 0.35; deterministic renders; determinism twins; slots
  2/3; stdlib+numpy+scipy(+skimage/matplotlib for authoring/renders only).

## 3. SELFTEST v6 FIRST (the v-lineage pattern; BEFORE any real-data rerun)

Synthetic cases, all declared with expected outcomes; any miss = the
continuation is STAGE0_INVALID and nothing runs:

- S6-1 OBLIQUE WEBBED HAND-MIMIC: five tapered rods (proximal half-width
  ~2mm) in an OBLIQUE pose (rotated ~30 degrees out of every box axis),
  joined end-to-end by webbing sheets 2 voxels thick, attached to a forearm
  stump (r=4mm) that crosses a box face; the declared oblique plane passes
  through the wrist at the recorded pose angle. EXPECT: fill-validity gate
  PASSES (median EDT >= 0.8mm); the stump is removed; the opening kills the
  webbing; markers = 5 (one per rod).
- S6-2 CLOSED-BLOB CONTROL: a closed ellipsoid (no plane, no caps) fills
  and segments as one part (regression guard for the 3D fill).
- S6-3 HOLLOW-WALL TUBE (regression): stays markerless and unassigned
  (the v5 case).
- S6-4 HARDWARE-MIMIC: two long straight rods crossing the box (cand0
  class) — EXPECT the honest non-fan outcome recorded (large parts with
  high aspect; no hand claim; the identification lesson L1 is a REVIEW
  task, not a pipeline output).

## 4. Frozen predictions (honest; stated before any run)

- PA1 SELFTEST BATTERY (gating): all four S6 cases classify as declared;
  any miss => STAGE0_INVALID, the continuation stops, the defect is the
  finding.
- PA2 THE RESOLUTION QUESTION: **UNKNOWN — no predicted direction.** The
  webbing that defeated the v5 extraction (Sergeant-measured 1.5-1.9mm
  walls; bones fused in webbing) may also defeat rim-capped filling + 1-voxel
  opening; a properly filled volume may equally separate cleanly. The
  continuation measures rather than guesses. The DECLARED gate that does
  have a direction is C6: if the fill-validity gate fails, the candidate is
  THIN_SHELL and stops — that outcome is a valid, honest result of this
  amendment.
- PA3 DETERMINISM: the coarse pass already demonstrated byte-identical
  twins; the continuation repeats one twin check on the new fine pipeline.

## 5. Then the re-run, the re-review, and only then the ladder

1. Re-run: cand2 + cand3 only (cand0 = hardware, excluded; cand1 = not a
   hand per the verdict, excluded) with the pinned continuation package;
   slots 2/3; declared envelope <= 2 CPU-hour cumulative for this
   amendment; keeps = receipts, tables, meshes, renders (including the NEW
   declared whole-body-context render per extraction — the L2 lesson: each
   candidate's render set gains one overview image locating it in the full
   skeleton).
2. Re-review: the Sergeant visual labeling review re-requested through the
   Lieutenant on the new artifacts (same five-question shape, updated for
   the oblique planes and the THIN_SHELL classes).
3. Ladder contact ONLY after that review passes with >= 1 part labeled as a
   single A05 bone and no THIN_SHELL violations.
4. THE CLOSURE: if the re-review fails (parts still GROUP/UNRESOLVED at
   labeling, or the fill-validity gate stops both candidates), the honest
   UNRESOLVED closure FIRES: 0 verdict-bearing bones from this source at
   this phase's method, recorded chain-wide as the species-true geometry
   answer for the Pisa surface-scan source; the fallback branch is already
   law (the Lieutenant's ruling).

## 6. Falsifiers (inherited FA1-FA6 plus the continuation's own)

- FA7: any THIN_SHELL part used as verdict-bearing, or any surface-shell
  mesh fed to the ladder => card invalid.
- FA8: any axis-aligned end-bin plane used as a continuation cut plane
  (oblique pose-aligned planes only).
- FA9: any opening applied to the exported GEOMETRY (opening is for
  separation analysis only; the mesh source is the un-opened fill).
- FA10: any wrist plane constant whose provenance is not the recorded
  review identification or the declared fallback rule, or edited after the
  re-review began.

## 7. Resources and governance

- CPU ONLY via the canonical runner, slots 2/3; declared envelope <= 2
  CPU-hour cumulative for this amendment (selftest battery + rerun +
  diagnostics); F6 law applies (no silent extension).
- Declared keeps (< 64 MiB): selftest v6 receipts, per-candidate receipts/
  tables/meshes/renders (incl. the whole-body-context overview), diag
  receipts, determinism twin receipt. Evidence anchoring before any
  registry reference.
- Governance: this DRAFT => the Lieutenant commits it ALONE FIRST =>
  implementation package pins the amendment commit (refusal on mismatch)
  => selftest v6 battery => re-run => diagnostics => re-review (Sergeant,
  through the Lieutenant) => ladder gate decision. Author self-review
  certifies nothing. The Captain's referral stays open until the Lieutenant
  records the branch outcome (continuation success, or the closure).
