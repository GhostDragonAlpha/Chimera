# MAT2-F03 — source-bound qualification receipt: the rigid climbable trunk as an explicitly reduced material object

**Verdict: BUILT AND SELF-CONSISTENT. The pinned trunk_01 asset (chimera.trunk_asset.v1) now carries the card's material-first addition: a chimera.material_state.v1 object (single-owner matter wood_trunk_01, mass from the declared exact collision solid and a researched, cached-source wood density, with the pinned matter library's NO-WOOD-ENTRY absence recorded), a chimera.passive_law.v1 RIGID assignment (M04's rigid profile), and an unmodified-M06 contact binding of the pinned triangle set with climb-relevant contact experiments whose per-tick ledgers balance. Suite 13/13, bites 7/7 fail-first, probes 47/47 views clean (zero mismatches, zero unrendered), capture manifest structurally valid under the REGISTRY forest profile with a single gate-bound artifact, and two full rebuilds byte-identical (15/15 artifacts). Visual acceptance itself belongs to the independent visual reviewer.**

- card: `MAT2-F03`; attempt `865039032f8148f6ac0a5f6532a73984`; arrival `arrival-6f97681152bd47bdbdfb943530771c32`; criteria sha256 `143a172d9531251d45952aa78c0e565b75c4409b3d7070b56109d6ef299f1ddd`; scope sha256 `cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`; planning id F03; base revision `30cd0f75a2aac6cd8e16504ddfbabf6fa955f1e0` (branch-2, sealed line; M02/M03/M04/M06/B03/B04 merged); PREREGISTRATION.md frozen before any build run with disclosed Amendments A1-A3 (probe count arithmetic; measured seam-duplicate topology; scoped M06 co-instantiation), each committed separately BEFORE the build.
- done_when (verbatim): "Trunk geometry, surface IDs, material provenance and collision representation are explicit. Material-first addition: The rigid trunk is an explicitly reduced material object using the same contact interfaces. Full wood growth/fracture or all tree rings are not prerequisites."
- falsifier (verbatim): "Rendered/collision mismatch, ghost support, missing boundaries or off-frame probe subject fails; tags alone do not establish contact."

## Reconcile-first: what was reused (nothing re-derived)

The trunk asset itself already existed as pinned data: the trunk declaration pin at `tools/monkey_campaign/data/monkey_trunk/trunk_declaration.json` @ dc7ea811 (raw sha256 `94ff906ec5e8b8388e4de318aa3321bad9c791fbb168e8234c371ed1d327e3f1`, embedded declaration_sha256 `b7089e7826a221a570b261b8c69666a4017a6ab62d20a2223d061654d0f63fe3`). This attempt added the material layer; the geometry, surface ids, site, analytic collision law and 32-segment render/contact mesh are the pinned bytes, loaded through F01's PASS-reviewed scene path (clearing recipe + declaration + TerrainSurface bundle, pins re-materialized and raw-hash-verified here). The M01 material-state validator, M06 local-contact solver, M04 passive-law validator and the campaign capture validator/gate are byte-pinned UNMODIFIED copies in evidence/pins_materialized/ (hashes in checks.json -> pins).

## Measured results (every number from the receipts)

- P1 identity/partition (Amendment A2 recorded): 130 vertices, 128 triangles -> lateral 64 / base_cap 32 / top_cap 32 by the declared center-vertex rule; RAW open edges 128 (EXACT seam-ring duplicates, worst duplicate distance 0 m, 66 distinct positions of 130); WELDED closure 0 open edges, outward-consistent. Region kind: `shell`, volume claim null (M02 closure rule: open edges -> shell, never sealed).
- P2 volume cross-check: welded divergence-theorem volume 0.0049484238288722421 m3 (orderings agree to 0 relative); analytic solid pi*R^2*H = 0.0049803731169212051 m3; ratio 0.99358496094591531 vs inscribed-polygon prediction 0.99358685114420575 (bar [0.99355, 0.99362], 1e-5 relative).
- P3 mass provenance: the pinned matter library (sha256 `de10200fb87bf48c3cc80d5e223805f02e27df115b91186f42f28064a64054ed`) has NO wood/bark entry — recorded, none invented. Declared density 760 kg/m3 (researched class per the library's own definition: cited external measurement with a cached source on disk) from tree_architecture_reference.md line 149 (raw sha256 `3cb871b0a1617f85d826608733add543e5d7f9b01c63e0e32770f69743880206`, table "Wood Density Database (Typical Values)", row "Oak (white)"), band [650.0, 850.0]. Honesty: the source states typical values with no moisture/conditions basis; under-specification recorded (MAT-03 heritage); proxy species white oak declared. Mass m = rho x V_analytic = 3.7850835688601157 kg (band [3.2372425259987834, 4.2333171493830246]).
- P4 documents: chimera.material_state.v1 validated by the unmodified M01 validator (canonical sha256 `91c17a5c59ce79af3dc0e8a6dadb00c92a039075775a0a1de618da12dfca61bd`); chimera.passive_law.v1 rigid assignment validated by the unmodified M04 validator (canonical sha256 `31fdf94b493ecf37bc0a6fe0c798fb3e0bfc49e3e9c7fa9c185d1e159a9a3510`); bonds [] and contacts [] with declared reasons (rigid and rooted; M06 owns contacts at runtime).
- P5 M06 binding (unmodified solver, sha256 `1cd662b30343011eb4a0a01e461a1e82b00482d0371857c8e42d6bec8f9a28dc`): S1 grip press 0.30 m/s at `trunk_01.lateral`: mode `stick`, jn 0.29999999999999999 N*s (bar 0.30 +-1e-9), tangential speed arrested to 1.1287980034305093e-28 m/s (bar 1e-12), ledger residual 7.3547637345053755e-51; measured grip capacity mu_s*jn/(g*dt) = 3.6697247706422016 kg. S2 counterfactual mu 0.15: mode `slip`, vt_post 0.004050000000000005 m/s (expected 0.004050000000000005; > 0). S3 40-tick rest on `trunk_01.top_cap`: max displacement 9.9999999998434674e-06 m (bar 2e-3), final mode `still`, ledger residual exactly 0. Surface ids flow through the records. Full-split co-instantiation recorded REFUSED by the pinned law (nonfinite_state) — the duplicated seam rings put lateral/cap pairs of two PINNED bodies into exact contact; each experiment instantiates exactly the parts it touches (Amendment A3).
- P6 correspondence: max lateral-vertex radial gap to the analytic cylinder 3.6713695708567862e-07 m (declared tolerance 2e-4); all vertices inside-or-on the solid within 3.1266084265374472e-07 m; 47 probes x 3 views: OCCLUDED 12, OFF_FRAME 27, VISIBLE_EXACT 102 — ZERO VISIBLE_BUT_MISMATCH, zero UNRENDERED; every view has >= 1 VISIBLE_EXACT trunk subject probe; seam probes obey the exact cylinder-silhouette prediction in V2.
- P7 captures: task_id `F03`, run_id `mat2-f03-trunk-20260928-86503903`, profile `forest` read READ-ONLY from the registry (canonical sha256 `d5b25ab9dcc5de7e15b1116f6f9c4da66b6c01d761a0913ef92443294c6bc5e7`, attempt state `WORKING`), tick_interval [0, 0]; 6 rows (3 profile views x diagnostic/clean); single gate-bound artifact `evidence/frame_V1_clearing_overview_clean.bmp` (sha256 `b4aab2898a01afd9a3b7446f1f2305d5f8a06abb26208b1f195c35405ce43644`); subject = trunk declaration pin; validate_manifest: structurally valid, capture_kind `image`, view_count 6; visual_gate.verify passed on the committed bytes; all six BMPs listed with recomputed sha256s. visual_acceptance false BY DESIGN — it belongs to the independent visual reviewer.
- P8 determinism: two full rebuilds byte-identical across all 15 artifacts (6 BMPs, checks, bites, capture manifest/context, validation receipt, 4 asset documents); recorded run hashes equal.

## Falsifier bites (fail-first, recorded before the pinned pass)

- B1_ghost_support: a +1 cm collision-surface push is a 0.01 m render/collision mismatch (> declared tolerance 0.0002); the pinned mesh measures 3.67137e-07 m
- B2_provenance_fabrication: the pinned matter library has no materials.wood entry
- B3_missing_boundary: without the top cap the WELDED mesh has 32 open edges; a volume claim is refused
- B4_off_frame_probe_subject: probe 1.0 m off-axis at 155.7 deg off the V2 view azimuth and 2.5 m up classifies OFF_FRAME
- B5_bad_friction: M06 refused: bad_friction
- B6_ledger_tamper: flipping one impulse breaks the per-tick ledger identity; residual norm 0.0981 > 1e-12
- B7_understated_friction: the understated-mu counterfactual slips (mode slip, vt_post 0.00405 m/s); a stick claim there is false

Bites run as `python -B implementation.py bites` -> 7/7 raise, then `build` -> all_ok: true (order recorded in evidence/bites.json and checks.json).

## What the material object says (the card's four clauses)

- Trunk geometry: the pinned analytic cylinder (R = 0.037 m, H = 1.158 m, base (11.976783, 0.0, 2.471766), axis +Y) with its pinned 32-segment triangle mesh; measured seam topology recorded (A2).
- Surface IDs: trunk_01.lateral / trunk_01.base_cap / trunk_01.top_cap, partition verified per-triangle, carried through M06 contact records as surface_a/surface_b, climbable flags inherited from the asset declaration.
- Material provenance: matter wood_trunk_01 owned exactly once; density researched from a cached on-disk source with the absence of any wood entry in the pinned matter library recorded; friction 0.6/0.6 carried as the recorded UNEVIDENCED-PLACEHOLDER (G04 debt).
- Collision representation: the asset's exact analytic cylinder solid plus the pinned triangle set as the M06 contact surface (identity mapping visual/physical, thickness 0.0 — no shell thickness invented), with measured render/collision correspondence inside the declared 2e-4 m tolerance.

## Honest limitations

- Static-scene evidence plus single-tick/40-tick contact experiments; no engine run, no climb controller, no appendage anatomy, no native change, no GPU, no training. The grip-capacity number is a property of the declared contact law at the frozen probe, not a climbing verdict.
- The friction 0.6 remains an UNEVIDENCED-PLACEHOLDER below the library's provisional class (acquisition is G04's); the density is a proxy-species typical value with the source's missing conditions recorded.
- The full 3-part split cannot be co-solved under the pinned M06 law (measured refusal, A3); the per-part experiments are the declared scope.
- The capture renders are a stdlib software rasterizer (F01-adapted) for presentation; the correspondence evidence is pure ray/geometry and never reads pixels. V1/V3 show the trunk subject at overview scale (sub-2-px wide); the seam close-up V2 carries the visually resolvable trunk, and the V2 diagnostic frame carries all five profile layers (render-mesh wireframe, scene bounds, normals/contact markers, stable 3D labels, collision surfaces via the exact-surface probes).
- Deformable branches, bark damage, growth, fracture and tree rings are out of scope per the card's own wording and are modeled nowhere.

## Exact commands (CPU-only, Python 3.14, stdlib, from this directory)

    python -B -m unittest test_implementation -v   # 13/13 ok
    python -B implementation.py bites             # 7/7 fail-first
    python -B implementation.py build             # all_ok: true
    python -B make_report.py                      # this report
    python -B implementation.py build             # byte-identical repeat (determinism)

Artifact canonical sha256 values are in evidence/checks.json; the capture manifest is evidence/capture_manifest.json; the gate-bound capture is evidence/frame_V1_clearing_overview_clean.bmp.

