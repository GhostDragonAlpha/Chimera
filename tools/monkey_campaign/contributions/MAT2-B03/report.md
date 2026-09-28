# MAT2-B03 report — real validated material-volume input for the selected body

Attempt 845efd334f914a5197b00f670f6c344a, arrival
arrival-fe837f4a12534d63b9e7f32759726ee0, criteria sha256
a68706372065cef87c1151c1b3af6b139865fff795c5e99af290dd7be4f8ecd1. Isolated
attempt checkout of E:\PythonChimera; local branch branch-1 fast-forwarded
from c525b82c to the merged integration tip
986f270ef24cda0008c52bd40d4b6d08565c0692 (origin/astra/gait-capture), which
carries this card's exact-revision dependencies (MAT2-P02, MAT2-M02); no
pushes, no PRs (the lead publishes). Preregistration (PREREGISTRATION.md)
was frozen and committed (421a9873) BEFORE any implementation or measurement;
the capture predictions (capture workspace PREDICTIONS.md) were frozen before
any capture code existed.

## done_when clause map (all clauses executed on the exact candidate revision)

| clause | execution | result |
|---|---|---|
| Actual geometry ... complete input for the selected body | material_volume_input.json (chimera.material_state.v1, object monkey-arm-material-volume-input): 7 regions from the pinned M02 macaque arm meshes (5 closed volumes + 2 shells), M02 bonds preserved, validated by the UNMODIFIED M01 validator | green; M01 summary 7 regions / 2 shells / 7 matter / 6 bonds |
| material ownership | every region owned exactly once: bone_<region> (volume-owned, counted) or shell_<region> (zero volume mass); M02's .osim segment masses recorded as EXCLUDED claims, never counted | green; owner_count 7, duplicate ownership refused by M01 (F6) |
| density source support ... density provenance | archived matter library materials.bone entry (mean 1800 kg/m3, band [1650,1950], provenance class "researched"), byte-pinned extract data/matter_library_1af0bbde.json (sha256 de10200f...); conditions stated honestly (source states none); density-envelope gate [500,3000] kg/m3 | green; density removed -> refused (F2a); g/cm3 slip refused (F4); library byte tamper refused (F2b) |
| Author only the matter required at selected fidelity | matter authored ONLY inside the 5 closed bone regions at uniform apparent density; no heterogeneous field, no muscle volumes, no skin/fat (absences inventoried in the document) | green |
| mass/volume ownership | C02: m = integral rho dV = rho*V per counted region; counted total 0.044702393754434 kg == M01 validator total exactly; excluded claims explicit | green; +1% mass tamper refused (F1) |
| static meshes do not implicitly provide interiors | the two OPEN surfaces (scapula 10 open edges, hand 18) claim ZERO volume-owned mass with an explicit refusal note in the document | green; shell volume claim refused (F3) |
| C02 Mass inventory | two independent volume formulations (divergence-theorem monomial integrals; signed tetra decomposition with reference-simplex covariance mapping) agree to <=1e-9; volumes continuous with M02 claims and admitted graph pins to <=1e-12; analytic cube + right-tetra closed forms reproduced | green (receipt probes V1-V3) |
| C03 Centre of mass and inertia | full symmetric 3x3 inertia about the aggregate COM (off-diagonals included) in world:default_pose; COM [0.0291822509, -0.0807765038, 0.0038711023] m inside the pinned AABB; eigenvalues [6.748e-05, 1.582e-04, 2.169e-04] kg m2 | green |
| C03 verification | independent quadrature (cross-method COM/inertia <=1e-9); rotation covariance under the two preregistered rotations (30 deg +Z, 25 deg +X); parallel-axis recombination; symmetry exact; positive-definite; excluded claims contribute exactly zero | green (receipt probes W1-W5) |
| verification profile anatomy (visible_static) | 6 lossless PNG frames 1280x720 (3 profile views x diagnostic/clean), real orthographic z-buffer renders of these exact triangle sets; manifest+context task_id SHORT form "B03"; visual_capture.validate_manifest run before handoff | structurally_valid=True, fired=[], view_count=6, capture_kind=image; visual acceptance belongs to the independent reviewer |

## Checks run (exact commands, candidate revision)

Run from the attempt checkout root with /c/Python314/python:

1. `python -B tools/monkey_campaign/contributions/MAT2-B03/derive_material_volume_input.py derive`
   -> emits material_volume_input.json (canonical sha256
   7fa15c8d04b7df3bbd018fbc486a66bd2c3c9898d8cccca3fd769a94a79c68b8) +
   derivation_receipt.json; 8 frozen verification probes green; re-validates
   the emitted document with the unmodified M01 validator.
2. `python -B tools/monkey_campaign/contributions/MAT2-B03/derive_material_volume_input.py verify`
   -> recomputes everything from the sha256-pinned inputs; counted total ==
   M01 total == receipt (0.044702393754434397 kg).
3. `python -B tools/monkey_campaign/contributions/MAT2-B03/test_material_volume_input.py`
   -> "checks: 19/19 passed ... ALL FROZEN PROBES GREEN (P1-P10, F1-F7 incl.
   F2a/F2b/F7a/F7b)"; proof written to work/runs/probe_suite.json.
4. Capture (workspace
   E:\ChimeraWork\monkey-coordination\kanban-attempts\MAT2-B03\capture-evidence-20260928,
   see its EVIDENCE.md): `python -B build_capture.py` then
   `python -B make_manifest.py` -> 6 frames + manifest/context +
   validation receipt; run_id mat2-b03-visual-20260928-02a9dc41.

## Falsifier proof (each: tamper a COPY, watch the named refusal, discard)

All seven preregistered falsifiers bite with the frozen codes (probe suite
output, preserved in work/runs/probe_suite.json):

- F1 mass_inventory_mismatch:sternum (+1% sternum mass in a copy)
- F2a density_source_missing:humerus (density_source block deleted in a copy)
- F2b input_pin_mismatch:matter_library (library bytes changed in a copied
  contribution tree)
- F3 shell_volume_claim_refused:scapula (shell given volume mass in a copy)
- F4 density_unit_scale_violation (density 1800 -> 1.8 g/cm3 in a copy)
- F5 rotation_covariance_violation (aggregate tensor frame-substituted in a
  copy)
- F6 duplicate_matter_owner:bone_humerus (second owner claim in a copy,
  unmodified M01 refusal)
- F7a mesh_blob_sha256_mismatch (one blob vertex shifted 1e-6 in a copy);
  F7b volume_continuity_violation:radius (recorded volume claim +1% in a
  copy)

P10 confirms the committed input document and pinned blob were byte-identical
after the falsifier run; tampered copies were discarded.

## Capture status + identities

- subject_sha256 10433f7bc74242a4818bb1bf7e1b66a1fcbc43de93b53fc270b7f3429d717b6d
  (composite of the emitted document canonical sha + pinned blob sha);
  identical on every frame and in manifest/context.
- capture_sha256 02a9dc41f7d1c7a36907b1fb5d08d12812a3f447e9c25e49ec382813d0b2b53d
  (concatenated frame_00..05 PNG bytes); per-frame sha256 in the manifest.
- manifest/context task_id "B03" (SHORT form); profile anatomy
  (visible_static) read read-only from registry card MAT2-B03;
  visual_capture.validate_manifest: structurally_valid=True, fired=[],
  view_count=6, capture_kind=image, visual_acceptance=false BY DESIGN (the
  gate decision belongs to the independent visual reviewer).
- All six profile diagnostic layers covered; clean rows carry zero
  diagnostics; state hash identical across all views. Full record incl.
  preserved intermediate render failures: capture workspace EVIDENCE.md.

## Honest limitations

- Density provenance class is "researched" (archived matter library entry;
  biomechanics-review citation in the library bytes). Per MAT-03 honesty,
  citing it is NOT claimed to be proof of authentic measurement, and the
  source states no temperature/moisture/strain-rate conditions (recorded as
  a limitation, not fabricated).
- Uniform per-region apparent density is an authored fidelity decision;
  heterogeneous density, muscle volumes (39 muscles are 1D path points), and
  skin/fat are absent and inventoried, never fabricated.
- The counted mass (44.7 g of bone at the sourced density) is NOT comparable
  to the .osim effective segment masses (7.006 kg); those are recorded as
  excluded segment-level claims, not replaced.
- Measured non-intersection of regions is pose-dependent (M02's default-pose
  evidence, re-read not re-measured); intra-mesh self-intersection remains
  unclaimed either way (source qualification limit).
- No runtime solver exists: rest == current, the visual capture is a
  visible_static state hold (tick interval [0, 0]).
- Preregistration prediction table carried two mis-transcribed printed digits
  (humerus, total); Amendment A1 records the erratum; the operative frozen
  arithmetic predictions were reproduced to 1.55e-15 relative.
- visual_acceptance=false in the validator receipt by design; human/
  independent visual acceptance is outstanding.

## File identities (sha256 at commit time, this directory)

Recorded in the handoff message: PREREGISTRATION.md (incl. Amendment A1),
derive_material_volume_input.py, test_material_volume_input.py, report.md,
data/matter_library_1af0bbde.json, material_volume_input.json,
derivation_receipt.json, work/runs/probe_suite.json.
