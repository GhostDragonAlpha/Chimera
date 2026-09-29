# MAT2-F02 — source-bound qualification receipt: terrain rendering and collision through the shared material/contact path

**Verdict: PASS.** The pinned F01 terrain asset (render arrays = query
triangulation, raw sha256 `446ed3fbd0f50205c61a7233ceca289bfc3316f76dfc672fec307b20d8305d52`) was bound to the
shared MAT2-M06 contact path (`chimera.local_contact.v1`): a pinned contact
body SLICED from the render ground section (exact array equality:
True), declared material
`clearing_ground_topsoil` on surface `monkey_clearing_ground`, five settled probes,
frozen geometric tolerances held, five falsifier bites all biting fail-first,
frames rendered from the same arrays with the settled contact state, and the
campaign capture manifest structurally valid against the REGISTRY profile
object. CPU-only (stdlib, Python 3.14); no engine run; no runtime or training
claim.

- card: MAT2-F02; attempt `c05153d7973f4e92bcda2759e0977b8d`; arrival
  `arrival-46852a2416264ac1858a4fc6196a1533`; criteria sha256
  `16ee643245f3db63a9ca367ab05792e4ed4bcdc13f5bbab95d506319290f59c1`; scope
  sha256 `cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`;
  planning id F02; base revision `c525b82c7c3ce0128565424764293a3c85811ab3`
  (branch-1); preregistration committed BEFORE implementation at `729af62a`.
- PREREGISTRATION.md frozen first (P1-P8, FB1-FB5, cameras, sites, materials);
  Amendments A1/A2 disclosed in section 7 (metric operationalization only; no
  bar loosened where frozen).

## 1. Reconcile-first (what was reused)

Published dependency bytes only — no re-implementation: F01's tied asset
(`terrain_bundle.json` + `terrain_bundle.py` + `terrain_query.py` + recipe +
declarations), F01's render law (`implementation.py`, vendored
byte-identical), M06's shared contact path (`local_contact.py`,
byte-identical, imported — never forked) and its `contact_law.json`
declarations. All nine pins raw-sha256 verified at build
(`all pins raw_match: True`).
The world-build-20260928 4 km terrain lane stays read-only context
(hashes in PREREGISTRATION section 1): it has no rendered asset yet; mixing
it in would fabricate the mismatch the falsifier punishes.

## 2. Material-first: the tied asset and the shared path (P1, P2)

- P1 tied asset: contact body vertices == render ground vertices EXACTLY
  (9600 vertices, worst component diff 0);
  surface_id `monkey_clearing_ground` == render section id
  (True); contact extent == rendered extent
  ([20.0, 20.0] vs half 20.0); both mapped
  orders hashed (562ae0634ccc63b4..., 562ae0634ccc63b4...).
  The asset's own validator receipt passes (worst discretization
  0.0064595 m <= 0.01 frozen; grid identity
  0; hygiene broken/deviant
  0/0).
- P2 shared path: 1283 contact records across the five
  settles, ALL through `local_contact.solve_tick` (module
  `local_contact (vendored M06 byte-identic...`); `validate_local_contact` passed on the assembled
  document (53 last-tick records); per-tick
  ledger identity enforced by the module, worst residual
  1.55e-17; declarations match `contact_law.json`
  (True). Materials: terrain
  `monkey_clearing_ground`/`clearing_ground_topsoil` mu 0.9/0.65 pinned;
  probes `mass_tetra` (0.12 kg pinned row) mu 0.6/0.4; thickness 0.002 (M02
  shell pin); `pair_mu` elementwise min.
- P2b subset property: sweep_and_prune resting state == exhaustive reference
  BIT-IDENTICAL at S1 (True;
  separations 0.00201 / 0.00201 m).

## 3. The frozen geometric tolerance (P3) and point/normal identity (P4)

Resting agreement — the settled probe's lowest point above its local query
height, window = contact band [0.0015, 0.0025] + the site's own within-cell
diagonal relief (`site_band`, frozen asset quantity; Amendment A1):

| site | min corner separation | site band | window | in window | centre sep (diagnostic) |
|---|---|---|---|---|---|
| S1 | 0.00201 m | 0 m | [0.0015, 0.0025] m | True | 0.00201 |
| S2 | 0.00201000915 m | 2.4e-05 m | [0.0015, 0.002524] m | True | 0.00240501 |
| S3 | 0.00201066743 m | 0.000293 m | [0.0015, 0.002793] m | True | 0.00464517 |
| S4 | 0.00201 m | 0 m | [0.0015, 0.0025] m | True | 0.00201 |
| S5 | 0.00263304103 m | 0.000603 m | [0.0015, 0.003103] m | True | 0.00327586 |

- P4: every recorded contact point lies ON its recorded ground triangle
  (worst plane error 1.39e-17 m <= 1e-9 over
  1283 records); on every recorded triangle the mesh face
  normal == `terrain_query.normal_at` at that triangle's centroid EXACTLY
  (worst 0 <= 1e-9) — the
  query surface and the contact body are the same normal field; the raw
  closest-feature normal tilts from the face normal by at most
  0.0145 rad <= the asset's own frozen
  slope law 0.05
  (declared bound, feature-contact geometry, recorded not hidden).

## 4. Falsifiers (recorded first; every one bites)

| FB1_ghost_support_decoupled_asset | BITES |
| FB2_parallel_solver_unaccepted | BITES |
| FB3_material_identity_detached | BITES |
| FB4_ghost_support_past_boundary | BITES |
| FB5_off_frame_probe_subject | BITES |

FB1 decouples the collision surface (+1 cm ghost vertex under S1) and the
resting bar detects it; FB2 proves a parallel height-clamp solver leaves ZERO
`local_contact.v1` records and is refused; FB3 detaches the material identity
and is refused; FB4 extends the contact body past the rendered extent and the
extent rule fires; FB5 classifies a required subject 155.7 deg off the seam
camera OFF_FRAME (tags alone do not establish contact).

- Review disclosure (N1, sgt-pr249-be2a097): the committed FB2 bite stub constructs its own empty `support_records` input (circular); the protection is nonetheless real — an independent live tamper (settle tick loop replaced by a direct height clamp) left zero `local_contact.v1` records and the full build refused with `f02_no_contact_records` (review evidence: kanban-reviews/MAT2-F02/sgt-pr249-be2a097/falsifiers/FB2_live_parallel_solver.log); the stub is left unchanged.

## 5. Render/collision correspondence and shear (P5, P6)

- P5 (F01's `classify_probe`, bars 1e-6 visibility / 1e-9 height / 1e-12
  normal, pure ray/geometry — probes never read pixels): per view
  (S1=spawn, S2=mound top, S3=mound flank, S4=terrain/trunk seam, S5=shear):

| view | outcomes |
|---|---|
| V1_clearing_overview | S1=VISIBLE_EXACT S2=VISIBLE_EXACT S3=VISIBLE_EXACT S4=VISIBLE_EXACT S5=VISIBLE_EXACT |
| V2_contact_seam | S1=OFF_FRAME S2=OFF_FRAME S3=OFF_FRAME S4=VISIBLE_EXACT S5=OFF_FRAME |
| V3_side_depth | S1=OFF_FRAME S2=VISIBLE_EXACT S3=VISIBLE_EXACT S4=OFF_FRAME S5=OFF_FRAME |
| V4_oblique_depth | S1=VISIBLE_EXACT S2=VISIBLE_EXACT S3=VISIBLE_EXACT S4=VISIBLE_EXACT S5=VISIBLE_EXACT |

  Assigned markers: ALL VISIBLE_EXACT; no
  VISIBLE_BUT_MISMATCH anywhere (0 failures).
- P6 shear: S5 impact shear absorbed through the friction law — jt over the
  run 0.04355 N·s, displacement 0.03322 m
  (< 0.5 m bar), final speed 1.22e-17 m/s,
  resting separation 0.00263304103 m in window. On this
  terrain slopes <= the asset slope law << mu_s: gravity alone must NOT
  sustain sliding, and none ran away.

## 6. Visual evidence and capture binding (P7) + determinism (P8)

- Frames: 4 views x (clean + diagnostic + depth) rendered from the pinned
  arrays; V2/V3 targets are the settled probe centres; 16-field camera
  records in `evidence/camera_manifest.json`
  (frame_id...state_or_tick_interval); ok=True.
- Capture manifest: `chimera.visual_capture_manifest.v1`, task_id `F02`,
  profile_id `forest`, run_id `mat2-f02-forest-20260928-c05153d7`;
  subject_sha256 = sha256(pins/terrain_bundle.json) =
  `446ed3fbd0f50205c61a7233ceca289bfc3316f76dfc672fec307b20d8305d52`; capture_sha256 bound to the SINGLE
  gate-bound artifact `evidence/frame_V1_clearing_overview_clean.bmp` = `b4aab2898a01afd9a3b7446f1f2305d5f8a06abb26208b1f195c35405ce43644`;
  per-row raw_sha256 recomputed from committed BMPs; state_binding =
  sha256(evidence/contact_trace.json).
- REGISTRY validation: profile object read READ-ONLY from
  `E:/ChimeraWork/monkey-coordination/agent_slots.sqlite3 kanban.cards[MAT2-F02].spec.ontology_qualification.task.verification_profile`; validator
  `E:\PythonChimera\tools\monkey_campaign/visual_capture.py`; structurally_valid=True;
  fired=[]. Structural only — independent visual review
  remains mandatory and the numerical bars above do not exempt the frames.
- P8 determinism: full pinned pass run twice — canonical results byte-identical
  (True, pass sha256 be24c77ad396dfef...);
  no wall-clock, no RNG anywhere in the build.

## 7. Disclosed amendments (post-first-run, bars unchanged where frozen)

- A1 (P3/P4 operationalization): the resting metric is the settled probe's
  LOWEST point above its local query height (centre-of-face separation kept
  as a diagnostic); the window adds the site's own within-cell diagonal
  relief `site_band` (max |h00−h01−h10+h11| under the probe footprint) — a
  frozen quantity of the pinned bytes — because a corner may legitimately
  rest on a cell-diagonal crease the 2D query sampling at that point does not
  serve. The P4 normal identity is checked where it is exact (contact point
  on recorded triangle; face normal == query normal at that triangle's
  centroid, 1e-9); the raw closest-feature normal is RECORDED under the
  asset's own declared slope-law bound. Derivation, not tuning: the first
  run's values are the committed values; no threshold was fitted.
- A1b (P5 marker oracle): settled contact markers may sit exactly ON a
  triangle edge or vertex (feature contacts), where the render ray's first
  hit is a face ADJACENT to the query-served one; heights still agree
  exactly. The marker oracle normal is therefore F01's own piecewise-linear
  set mechanism (`oracle_n_set`, its A3): the normals of all ground triangles
  whose footprint contains the point, and the hit face must match one of
  them at the frozen 1e-12 bar. First-run exposure: S5-in-V4, height error
  7.9e-16, single-normal comparison 2.6e-2. Mechanism reuse, not a bar
  change.
- A2 (V2/V3 camera targets): the prereg formula named the pre-settle probe
  centre; the shipped target is the SETTLED probe centre (the declared
  intent, "frame the settled probe"), deviation 0.052 m, disclosed here.

## 8. Honest boundaries

- engine run, native load_mesh upload, or HTTP playthrough
- boundary-post or trunk contact (F03/next-card scope; inventoried)
- world-build 4 km terrain lane integration (context only, hashes in PREREGISTRATION section 1)
- training, runtime or playable-build acceptance
- any visual acceptance beyond the declared cameras and this receipt

## 9. Evidence inventory (committed bytes, sha256)

| evidence/depth_V1_clearing_overview.bmp | 130c5a26f0a2f782ce0deaacb01895b1e4169027d04f686a672641e0098dadc4 |
| evidence/depth_V2_contact_seam.bmp | e45ab8a3c7391a4833e02b27b5e20d6ed2e70db3d681bedb8f2ce34db67bf89c |
| evidence/depth_V3_side_depth.bmp | d241db6a3d4a0fa9b6284b78982ed2367ebee6c891340a2a96fc414dfd1b4b7c |
| evidence/depth_V4_oblique_depth.bmp | 4eb25c122eced05609707b211c621fa6b57d99dd02f13a462a12a5de48f22ba0 |
| evidence/frame_V1_clearing_overview_clean.bmp | b4aab2898a01afd9a3b7446f1f2305d5f8a06abb26208b1f195c35405ce43644 |
| evidence/frame_V1_clearing_overview_diagnostic.bmp | f2cf09a590fdc06fb5d1ab7a697d16272ca03ca9536f0c42ad6b64a86dade986 |
| evidence/frame_V2_contact_seam_clean.bmp | 47b647e1b20401959f47a0b7153d0b6fbe1e30f7dbbf19b5a2e8be8bddda06c0 |
| evidence/frame_V2_contact_seam_diagnostic.bmp | 5e99a7fe2127a47a434392669c172fffad18e825f01fbdcb25c16b2fd24bf7bc |
| evidence/frame_V3_side_depth_clean.bmp | 15249d0870ca5679c79d6f1d60a9d19a81c5aee9776d2a5b76f70d03d71326a9 |
| evidence/frame_V3_side_depth_diagnostic.bmp | 7c69073a0618006129677a8de561eefab019c5acca90ff30253ea99627d395fb |
| evidence/frame_V4_oblique_depth_clean.bmp | eb5c5d7eaa6e98247fe88c2d4b53405df524972a4ae22593d04ccd92241c7205 |
| evidence/frame_V4_oblique_depth_diagnostic.bmp | af2824c721413ea9a7c77b5eb6c8c1f27b40ffb2d1c6beebd7dc1ced172f2f8d |

- evidence/checks.json — the receipt this report was generated from
- evidence/bites.json — the fail-first record
- evidence/validation_receipt.json — registry-profile structural validation
- evidence/capture_manifest.json — the campaign capture manifest

## 10. Exact commands (from this directory, Python 3.14, CPU only)

```
python -B run_terrain_contact.py build    # bites -> checks -> frames -> receipt
python -B make_capture_manifest.py        # campaign manifest + registry validation
python -B make_report.py                  # this file, from the receipt
python -B -m unittest test_implementation -v
```
