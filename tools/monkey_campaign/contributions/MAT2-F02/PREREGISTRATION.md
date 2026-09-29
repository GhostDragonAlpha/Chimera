# MAT2-F02 PREREGISTRATION — matching terrain rendering and collision through the shared material/contact path

Card MAT2-F02, planning id F02, calculation contract C14. Attempt
`c05153d7973f4e92bcda2759e0977b8d`, arrival
`arrival-46852a2416264ac1858a4fc6196a1533`, criteria sha256
`16ee643245f3db63a9ca367ab05792e4ed4bcdc13f5bbab95d506319290f59c1`, scope
sha256 `cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`,
base revision `c525b82c7c3ce0128565424764293a3c85811ab3` (slot branch-1).
Done_when (verbatim): "Rendered ground and physical query surfaces agree
within frozen geometric tolerance. Material-first addition: Terrain contact
uses the shared material/contact path; surface shape, material identity and
collision geometry stay tied to the rendered asset."

This document is committed BEFORE any build/verify run in this workspace and
before the implementation commit. Every bar below is frozen here; the
implementation may only record observations against them.

## 1. Reconcile-first: what already exists and is reused (nothing re-implemented)

Read before any write: task inbox (EMPTY at dispatch), the two dependency
cards, and their published candidates on `origin/astra/gait-capture`
(tree `18327e7b6e7b8d4b2243362fb3d14a7a77f9672e`):

- MAT2-F01 (registry-verified, PR #188 lineage): the finite clearing. Its
  `terrain_bundle.json` IS the tied asset this card qualifies for contact:
  `render.vertices`/`render.indices` are the engine `load_mesh` arrays and
  `collision.same_arrays_as_render = true`; `terrain_query.py` is the ONE
  physical query surface; `terrain_bundle.py` is its validator. F01's report
  explicitly reserves C14/F02 wording for this lineage. F01's renderer
  (`implementation.py`, z-buffer raster + `classify_probe` + BMP writers) is
  reused verbatim as the render law — vendored byte-identical.
- MAT2-M06 (published candidate `03f039b1`, review head `055071c8`): the
  shared material/contact path `local_contact.v1` (`local_contact.py`):
  candidate search -> exact tri-tri contact -> Coulomb friction -> CCD ->
  reciprocal impulses + ledger. Terrain contact MUST go through this module
  (imported, never forked, never re-solved in parallel).
- MAT2-M01 capture pattern: campaign manifest schema
  `chimera.visual_capture_manifest.v1`, profile object read read-only from
  `agent_slots.sqlite3` (`kanban.cards[MAT2-F02].spec.ontology_qualification
  .task.verification_profile`), `capture_sha256` bound to a single committed
  on-disk artifact.

Pinned inputs (committed under `pins/`, raw sha256 asserted at build; all
bytes re-materialized in this attempt from the published trees and
hash-verified against F01's own recorded pin table BEFORE this freeze):

| pin | published path (astra/gait-capture) | sha256 |
|---|---|---|
| clearing_recipe.py | contributions/MAT2-F01/evidence/pins_materialized/clearing_recipe.py | `ab800d2257655118296519b606c77ddc7116f524ae0c2e6a0bab3b38473892dc` |
| clearing_declaration.json | contributions/MAT2-F01/evidence/pins_materialized/clearing_declaration.json | `18dd2ff65410cd1cf184a7a8df61c7503a6ce15083f30159e727e9a8117bfbc1` |
| terrain_bundle.py | contributions/MAT2-F01/evidence/pins_materialized/terrain_bundle.py | `c6ada25a1b6192aa86add8b09bc19161c0cd81e3fb3d4bd267492660c0be8f2e` |
| terrain_query.py | contributions/MAT2-F01/evidence/pins_materialized/terrain_query.py | `b1e244b8843671afc29af530c4725bf812ffd5f8967130f0202792aeb7a8cce1` |
| terrain_bundle.json | contributions/MAT2-F01/evidence/pins_materialized/terrain_bundle.json | `446ed3fbd0f50205c61a7233ceca289bfc3316f76dfc672fec307b20d8305d52` |
| trunk_declaration.json | contributions/MAT2-F01/evidence/pins_materialized/trunk_declaration.json | `94ff906ec5e8b8388e4de318aa3321bad9c791fbb168e8234c371ed1d327e3f1` |
| f01_implementation.py | contributions/MAT2-F01/implementation.py | `50e191cfc6f592fd9919534c8986c049939a4e88c4922e135f383bbf06e693af` |
| local_contact.py | contributions/MAT2-M06/local_contact.py | `1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc` |
| contact_law.json | contributions/MAT2-M06/contact_law.json | `583962c29f18118a478dedb167f2c3667414b86f5cab4ee54763416f1df7e41b` |

Scope decision (recorded, falsifiable): the card is qualified on the
campaign's COMMITTED, registry-verified terrain asset (F01's clearing
bundle), because the done_when demands that the query surface the contact
path sees and the rendered surface come from ONE tied asset. The
world-build-20260928 terrain lane (law grid 1536x1536 @ 9.1205 m cell,
half-extent 7000 m, `terrain_grid.npz` sha256
`9790fd252825278060f555f545f21b733cb6df9047d0ce1886d006fa87dfd012`;
walk core 1999x1999 @ 2 m, `walk_core_4km.npz` sha256
`4d7bcb662330cbdb3645b0b7aefb97a5ffb3158c3f673e7fdb4ad5f4229d5ab4`;
`terrain_field.py` sha256
`588d04a6b19641fe60cc1b4e18446c78b4a98207d444e5a4f520b0e19447d226`;
`terrain_law.py` sha256
`c4cb44a08cd098fb24d58f3fd7cf697156226d12d15c97c3754262fbe73906fe`) is
read-only context for a FUTURE render-asset card: it has no rendered asset
yet, is uncommitted in any revision this card can pin, and mixing an
unrelated height source into this asset would manufacture exactly the
render/collision mismatch the falsifier punishes. Hashes recorded here make
that lane exactly recoverable later.

## 2. Statement and prediction

The terrain contact body is built FROM the pinned render arrays (ground
section only, 3200 triangles), pinned, with a declared surface material;
probe bodies settle onto it ONLY through `local_contact.solve_tick`. If the
rendered surface and the physical query surface were to disagree, the
resting probes would sit at the wrong height or the contact points/normals
would miss the rendered triangles — all measured below.

Frame map (declared, right-handed rotation +90 deg about +X, det=+1,
winding-preserving): clearing (x, y, y-up, z-south) -> contact
(x, -z, y); M06 gravity (-Z contact) maps back to clearing gravity (-Y).
Inverse: contact (a, b, c) -> clearing (a, c, -b). Both bodies are mapped
by the SAME rule; all contact records are mapped back for comparison
against the clearing-frame query surface.

Material-first declarations (synthetic_authored, recorded-not-derived, in
the M06 vocabulary; `pair_mu` = elementwise min):

- terrain: `surface_id = "monkey_clearing_ground"` (EXACTLY the render
  section's surface_id), `matter_id = "clearing_ground_topsoil"`,
  `mu_s = 0.9`, `mu_k = 0.65`, `thickness_m = 0.002` (MAT2-M02 shell pin),
  pinned.
- probe shells: `matter_id = "mass_tetra"` (pinned compiled matter row,
  mass 0.12 kg as in M06's fixtures), `mu_s = 0.6`, `mu_k = 0.4`
  (M06 block declarations), `thickness_m = 0.002`, 12-triangle box shell,
  half-extent 0.1 m, free, not pinned.

Frozen experiment: 4 drop sites + 1 shear site, all in the clearing frame,
none inside the trunk footprint bound (0.5 m about (11.976783, 2.471766)):
S1 spawn (0, 0); S2 mound m1 top (-18.312917, -6.422639); S3 mound m1 flank
(-15.035646, -6.422639) (centre + 0.6*R_east); S4 terrain/trunk seam
(11.226783, 2.471766) (0.75 m west of the trunk axis); S5 shear: mound m3
top (19.265584, 6.057064) with initial horizontal velocity (-0.35, 0, 0)
m/s. Drop height 0.05 m above `terrain_query.height_at` (bottom face); S1–S4
settle 40 ticks (0.2 s), S5 runs 80 ticks (0.4 s). DT = 0.005 s (M06). Max
per-tick motion at impact ~0.005 m < the M06 declared capture bound
0.02 m/tick, so CCD never needs its fallback.

## 3. Frozen checks (pinned pass, recorded AFTER the bites)

- P1 tied_asset_identity: the contact body's mapped vertex array equals the
  render ground vertices element-for-element (bar 0.0, exact); both orders'
  sha256 recorded; surface_id identity with the render section recorded.
  Inherited asset integrity: vendored `validate_bundle` passes on the pinned
  bundle bytes (worst discretization <= 0.01 m inherited bar; grid identity
  <= 1e-9; hygiene broken/deviant == 0).
- P2 contact_through_shared_path: every support impulse on every settled
  probe appears as `local_contact.v1` contact records (no parallel solver);
  `validate_local_contact` passes on the assembled document; per-tick ledger
  residuals == 0 (module-refused otherwise) and reciprocity residual
  recorded; `exhaustive=True` reference run at S1 produces the same resting
  state as `sweep_prune` (candidate-subset property on this scene).
- P3 resting_agreement (THE frozen geometric tolerance): at S1–S5 the
  settled probe bottom mid-surface sits ABOVE the query height with
  separation in [0.0015, 0.0025] m; hard bar: separation <= TOL_REST_M =
  0.0025 m. Derivation: shell inflations thickness/2 + thickness/2 = 0.002 m
  plus M06 equilibrium band (SLOP 1e-5 + MARGIN 1e-5), rounded UP to 3
  decimal places in millimetres -> 0.0025 m; no tuning after measurement.
  Penetration below the query surface beyond the same window refuses.
- P4 point_and_normal_agreement: each recorded contact point_b maps back ONTO
  its recorded ground triangle's plane (bar 1e-9 m) inside the triangle's
  footprint; the mapped contact normal agrees with
  `terrain_query.normal_at` at that point (bar 1e-9 max component, sign
  normalized outward/up; declared).
- P5 render_collision_correspondence: F01's `classify_probe` (bars 1e-6
  visibility, 1e-9 height, 1e-12 normal) run on the settled contact points
  as probes: every site marker VISIBLE_EXACT in its assigned view (S3 in
  V1+V3, S4 in V2, S1 in V1, S5 in V4), no VISIBLE_BUT_MISMATCH anywhere;
  OFF_FRAME counts as failure for an assigned subject.
- P6 shear_is_finite: at S5 the tangential impact is absorbed through the
  friction law (jt impulses recorded, finite), displacement after 80 ticks
  is bounded (< 0.5 m), final speed <= 1e-4 m/s, resting bar P3 holds. (On
  this terrain slopes <= 0.05 << mu_s, so gravity alone must NOT sustain
  sliding; a runaway slide refuses.)
- P7 frames_and_manifest: 3 profile-view pairs + 1 supplementary view
  rendered from the pinned arrays with the settled probes; 16-field camera
  records per frame; capture manifest in `chimera.visual_capture_manifest.v1`
  with task_id "F02", profile_id "forest", every binding hash recomputed
  from committed bytes; `visual_capture.validate_manifest` passes against
  the REGISTRY profile object (read read-only from agent_slots.sqlite3);
  `capture_sha256` = sha256 of `evidence/frame_V1_clearing_overview_clean.bmp`
  (single gate-bound artifact).
- P8 determinism: the full settle+checks run twice in-process produces
  byte-identical canonical results; re-rendering V1 clean twice produces
  identical BMP sha256; no wall-clock, no RNG anywhere.

## 4. Falsifiers (bite-first, run and recorded BEFORE the pinned pass)

- FB1 ghost_support_decoupled_asset: raise ONE ground vertex of the CONTACT
  body copy by +0.01 m under S1 (render untouched), re-settle: resting
  separation leaves the P3 window -> detected. (A collision surface that
  drifted from the rendered asset cannot hide.)
- FB2 parallel_solver_unaccepted: replace the shared path with a direct
  height-clamp (the forbidden second solver) at S1: the check "every support
  impulse appears in local_contact records" fires (zero records).
- FB3 material_identity_detached: rename the terrain matter_id to a foreign
  id ("mass_plate") -> the material-identity check against the declared
  asset material fires.
- FB4 ghost_support_past_boundary: extend the contact body with one triangle
  1 m outside the rendered extent -> the contact-body extent == rendered
  extent check fires (no invisible wall, no support past the boundary).
- FB5 off_frame_probe_subject: the S4 seam subject required in V2 is
  classified from a camera pointed 155.7 degrees off it -> OFF_FRAME is
  returned (the visibility classifier detects off-frame required subjects;
  tags alone do not establish contact).

All five must bite (fail-first) or the build refuses.

## 5. Frozen cameras (clearing frame, pinhole, z-buffer, 1280x720, near 0.05 far 200)

- V1_clearing_overview: position [0, 46, -32], target [0, 0, 0], vfov 55 deg
  (F01 heritage view, unchanged law).
- V2_contact_seam (profile view "terrain/trunk seam close-up"): position
  [9.95, 1.30, 1.60], target [11.226783, h_query(11.226783, 2.471766)+0.05,
  2.471766] (the settled S4 probe centre), vfov 55 deg.
- V3_side_depth (profile view "side and oblique depth checks"): position
  [-15.035646, 2.60, -14.50], target the settled S3 probe centre, vfov 45 deg.
- V4_oblique_depth (supplementary, committed + classified, NOT a manifest
  pair): position [-34, 20, -30], target [0, 0, 0], vfov 55 deg (F01
  heritage).

Diagnostic layers exactly the five profile layers: render-mesh wireframe;
collision surfaces (probe shell wireframe + recorded contact-triangle
outlines); normals/contact markers (contact points + up normal stubs);
scene bounds; stable 3D labels (spawn, trunk_01, mound_m1, mound_m3,
probe_S1..S5). Clean rows carry none of these by design.

## 6. Honesty boundaries (declared now)

- CPU-only, stdlib-only, Python 3.14; NO engine run, no native
  `load_mesh` upload, no GPU, no training or runtime acceptance claim.
- Contact scope: the GROUND section of the terrain asset. Boundary posts and
  the prototype trunk remain rendered scene subjects; their contact is
  F03/next-card scope and is inventoried, not claimed.
- The world-build 4 km terrain lane is context only (hashes in section 1);
  integrating it is future card work.
- The visual gate proves correspondence of markers and asset pixels with
  declared cameras; it does not substitute for the numerical bars, and the
  numerical bars do not exempt the frames.

Signed freeze: this file is committed alone, before implementation, in the
attempt checkout on branch-1 at base c525b82c.

---

## AMENDMENTS (disclosed after the first run; no frozen bar loosened)

### Amendment A1 — P3/P4 measurement operationalization (derivation, not tuning)

The first settle run revealed two measurement ambiguities in sections 2-3,
both resolved using ONLY frozen asset quantities:

1. P3's "the settled probe bottom" is measured as the settled probe's LOWEST
   point above its local query height (min over the shell vertices of
   `z - height_at(x, z)` in the clearing frame). On slopes the bottom-CENTRE
   separation conflates the contact gap with planar geometry (a flat box on a
   planar slope rests corner-first). The centre separation stays recorded as
   a diagnostic. The frozen window [0.0015, 0.0025] is unchanged for the
   contact band and is extended per site by `site_band`: the maximum
   |h00 - h01 - h10 + h11| over the grid cells under the probe footprint —
   the asset's own within-cell diagonal relief (a corner may rest on a cell
   diagonal the 2D query at that exact point does not serve). site_band is
   computed from the pinned bytes only; no observed value entered its
   definition.
2. P4's normal identity is checked where it is mathematically exact:
   (a) every contact point lies on its recorded ground triangle's plane and
   footprint (bar 1e-9 m, unchanged); (b) on every recorded triangle the mesh
   face normal (engine formula, same vertices) equals
   `terrain_query.normal_at` at that triangle's centroid (bar 1e-9,
   unchanged) — the query surface and contact body are the same normal field;
   (c) the RAW closest-feature contact normal (M06's normalized p - q, which
   for edge/vertex feature contacts is the common perpendicular, not a face
   normal) is RECORDED under the declared bound = the asset's own frozen
   slope law (`max_slope_bound_m_per_m`). The original blanket 1e-9 normal
   bar against `normal_at` at the contact point was under-derived for
   feature contacts and is replaced by (a)+(b)+(c), not relaxed: the exact
   identities remain at 1e-9 and the only quantity checked against a slope
   bound was previously unbarred.

### Amendment A1b — P5 marker oracle normal set

The settled contact markers may sit exactly ON a triangle edge or vertex
(feature contacts; M06's closest-point lands on the terrain triangle's
boundary). F01's own piecewise-linear mechanism applies (its A3 for grid-node
probes): the marker's oracle normal is the SET of normals of all ground
triangles whose footprint contains the point (`_incident_ground_normals`);
the render ray's first-hit face must match ONE of them at the frozen 1e-12
bar. Heights stay exact at 1e-9. First run exposed this at S5-in-V4 (the
marker rests on an inter-cell edge; height error 7.9e-16, single-normal
comparison 2.6e-2); the fix is the established F01 mechanism, not a bar
change.

### Amendment A2 — V2/V3 camera targets

The section 5 formula named the pre-settle probe centre as the V2/V3 target;
the shipped target is the SETTLED probe centre (the declared intent: "frame
the settled probe"). Deviation 0.052 m, deterministic, disclosed; positions,
fov, near/far and all 16 recorded fields unchanged.

Both amendments are committed with the implementation that motivated them,
after the freeze commit, and are reproduced verbatim in report.md.
