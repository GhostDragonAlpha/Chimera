# MAT2-B02 qualification receipt — supported static exporter coverage at frozen revision 1af0bbde

- attempt: 5cf7f1cc0d1b40cb9f4a08fc12c4c535 · agent arrival-cccbccce34f94eb294f9e71640348b64
- date: 2026-09-26/27 · machine: CPU-only Windows 11, CPython 3.14.3,
  numpy 2.2.6, jsonschema 4.25.1, `python -B`,
  `PYTHONDONTWRITEBYTECODE=1`; no GPU, no network use during execution.
- pinned target (no substitution): `1af0bbdee68d6ddfdd02bf9bd948f7b22f914d56`
  (byte-exact blob-form extraction, 34 files, provenance in
  `work/frozen/1af0bbde/provenance.json`; exporter/reader/admission/compiler
  modules never modified).
- criteria sha256: `151a4aa7693f30c49a32167c78301240b68d701ce1ea766134c71a4080454d7e`
- preregistration frozen before any authoring or execution:
  `PREREGISTRATION.md`, raw sha256
  `8d5c922a0ab88a2c773d905481d16af0b644748c01789a5b9a94ceb656c51238`
  (predictions P-U2/P-U5/P-U2S/P-U6/P-U7/P-U3/P-U4/P-OR/P-NC/P-DET/P-HASH/
  P-COUNT/P-BOUND and falsifiers F-B02-1..14 frozen before the first probe;
  the file is preserved verbatim, including its one transcription defect,
  see Firing record).
- profile: records / offline · numerical evidence required · falsifier:
  "Missing identities or a claimed pass unsupported by records fails; a
  screenshot is not a substitute."

## Verdict

**The done_when is met with fresh, source-bound numerical evidence at the
pinned bytes. No criterion falsifier fired.** One prereg literal check fired
as written (F-B02-8 class: transcription defect in the frozen file itself) —
adjudicated below, with the frozen file preserved unmodified. Counts:
unittest suite `Ran 11 tests — OK` (0 failures, 0 errors) asserting 239
fields; static diagnostics asserting 396 further fields; **635 total
individually-asserted field comparisons** (≥ 500 required by P-COUNT),
recorded identically across two determinism runs of the diagnostics
generator (byte-identical outputs).

## Clause-to-evidence map (done_when: "Authorized scale/transform/status/numerical tests and static diagnostics ship with distinct evidence classes")

| clause | evidence (all under tools/monkey_campaign/contributions/MAT2-B02/) | result |
|---|---|---|
| **scale** (U2) | suite test_01: cm-authored coupon_u (scale_to_m 0.01) vs coupon_n — both bodies' mass, volume, COM (body frame), full inertia tensor equal to the exact oracle within T1=1e-12; suite test_03: scale_to_m = 0.0 / −1.0 / missing → admission refused (`bad_scale` ×2, `bad_schema`), export_status `blocked`, every mass_properties None, CLI exit 1 | PASS |
| **scale + numerical** (U5, C04) | suite test_02: s ∈ {0.5, 2, 10} sweep — m ∝ s³, volume ∝ s³, every inertia entry ∝ s⁵, COM via the authored-frame law Rᵀ(s·c−o), units and frame-invariant flags unchanged, all within T1 | PASS |
| **transform** (U6) | suite test_04: coupon_r = coupon_n under vertex-ID bijection + reversed vertex/cell rows + within-body cell-id sort flip + even per-cell vertex permutation — export_status/reason_codes/unassigned identical, every mass-property number within T1, `supplied_geometry_signature` exactly equal, all three input_hashes and admission_report_sha256 differ (recorded, not compared), CLI report bytes differ | PASS |
| **status** (U7) | suite tests 05–09: blocked report (missing density on cell-na2; body-B carries no blocking rows) read by the pinned reader exit 0 with per-body mass None; refused reports (unknown group cell `unknown_group_cell_id`; non-orthonormal frame `invalid_authored_frame` with admission `not_evaluated`) exit 1, reader exit 0; tamper control: mass injected into a non-exported group → reader exit 2 `blocked_group_has_mass`; bogus status → exit 2 `bad_export_status` | PASS |
| **numerical** (U4, C02/C03) | diagnostics: coupon_l (coordinates ~3e6, T2=1e-9 budget) vs exact Fraction oracle — mass, COM components, full tensor incl. off-diagonals within budget; coupon_d (sliver, height 2**-20, normalized det ≈9.5e-7 ≫ 64·eps refusal line): mass/volume/inertia within T1 of exact (m = 2**-20 exactly); coupon_x (density ratio 1e15 across one body): total mass within T1 of exact 500000000+1/6000000, all finite | PASS |
| **static diagnostics** (U3) | diagnostics: cube 6-tet, 3-region coupon — exactly 4 cross-region interface rows, each √2/2 within T1; pair sums CA-CB = √2, CB-CC = √2; no CA-CC row; regions meeting at vertex 000 = {region-CA, region-CB, region-CC} (>2); 12 boundary faces each 1/2 (exact cross-check); per-body masses 1, 4/3, 5/3; whole-partition recombination 4 kg (no interface mass) | PASS |
| **distinct evidence classes** | `work/runs/static_diagnostics.json` evidence_classes: every contribution artifact recorded with raw working-tree sha256, LF-canonical sha256, and git blob OID as three separate labeled classes; materialization demo (CRLF copy of PREREGISTRATION.md): raw ≠ LF-canonical with the LF-canonical identity and committed blob OID stable; every hash quoted in this receipt names its class | PASS |

## Contracts

- **C02 mass inventory**: exact masses for disjoint cells aggregated per body
  (11/2 kg body-A = 2 kg + 7/2 kg; 500/3 kg body-B; cube 1 + 4/3 + 5/3 = 4 kg
  recombination); disjoint ownership enforced by admission; internal shared
  faces contribute no material (cube: interface rows only, no mass rows).
- **C03 COM + inertia**: full symmetric tensors including off-diagonals vs
  this attempt's exact `fractions.Fraction` reference-simplex oracle (pure
  stdlib, no frozen-module imports); authored-frame rotation covariance via
  Rᵀ·I·R with exact rational rotations.
- **C04 scaling/conditioning**: exporter-level s³/s⁵ covariance (U5) plus
  adverse-conditioning diagnostics (large coordinates, sliver, extreme
  density ratio) with declared per-case budgets (T1/T2). Boundary recorded,
  not claimed: `scale_to_m` is a single positive scalar — anisotropic scaling
  enters only as authored geometry integrated per cell.

## Firing record (honest adjudication; frozen file untouched)

- **F-B02-8 fired once, as designed for prereg self-errors**: literal check
  `x_cell_a_mass_as_written` — prereg writes "m_xa = 1/600000 kg"; the exact
  derivation is V·ρ = (1/6)·(1/10⁶) = **1/6000000** kg. The prereg file is
  preserved verbatim; the diagnostics record both the as-written check
  (fired) and the as-derived check (match). This is a transcription defect
  in the frozen text (same class as the frozen receipt's C-5/C-6 preserved
  corrections), not a physics or tolerance change; the exporter/oracle
  prediction P-U4 itself passes against the derived value.
- No other falsifier fired. Suite `Ran 11 tests — OK`; the negative control
  (P-NC) fired correctly when a +1e-6-perturbed expectation was rejected;
  determinism runs are byte-identical.

## Pre-pass tooling defects of this attempt (fixed before any passing claim; preserved)

1. Oracle first/second moments were scaled by `mass` instead of
   `density·det` (exact factor 6) — caught because the frozen hand literals
   (25/44, 9/22, 9/22; 11/2) mismatched; fixed; oracle now reproduces every
   hand literal exactly (22/23 checks, the 1 remaining being the prereg typo
   above). Two suite runs failed on this before the recorded passing run.
2. Builder dropped body-B's authored frame origin (defaulted to zero) —
   caught by suite test_01 (com_body actual 5.25 vs expected 0.25); fixed.
3. Builder initially gave two regions the same mass owner and aliased
   shared-face vertices — refused by the pinned compiler
   (`duplicate_mass_owner_id`, `duplicate_vertex_position`); realized per R1/R2
   below. Two Kuhn tets were listed inverted; builder auto-orients (R3).

## Realization notes (pinned validation forced these; no frozen quantity changed)

- **R1**: cell-na2 shares its face vertices by ID (a1,a2,a3); the prereg's
  b0/b1/b2 aliases carried duplicate positions. Same coordinates, same
  positive orientation, V = 1/2.
- **R2**: distinct owner labels per region (pinned compiler: one owner per
  region; one material per region). The prereg's "same mass owner" /
  coupon-X "one region" phrasing is realized as region-A2 (owner-A2) and
  region-XA/XB (owner-XA/XB); bodies still aggregate cells across regions,
  so the frozen physics (coordinates, densities, body composition, frames)
  is unchanged.
- **R3**: two Kuhn tets were listed inverted; the builder deterministically
  swaps the last two vertex IDs when det < 0 (same tetrahedron, positive
  orientation; the pinned code never repairs vertex order).
- **R4**: the pinned `material_volume_body_export_schema.json` is the export
  REQUEST (groups) schema — it rejects the pinned revision's own example
  report (pre-existing at 1af0bbde, recorded). All 13 coupon groups
  documents plus the pinned example validate against it; the report contract
  is enforced by the pinned reader + determinism probes.

## Boundaries (P-BOUND; claim scope)

- U8 (consumer cross-report composition), U9 (consumption-contract clauses),
  U10 (anything beyond synthetic coupons) are recorded UNRESOLVED in
  `static_diagnostics.json#unresolved_inventory` — downstream
  consumer/runtime work this offline records card does not own (B01 frozen
  receipt boundary restated, not claimed).
- No runtime, anatomical, or dynamics claim anywhere. Every report carries
  `validation_only: true`, `production_wired: false`,
  `dynamics_readiness_claimed: false`. All coupons are fixtures; no fixture
  became a release gate (card observation honored).
- Card observation honored: none of these probes was promoted to a runtime
  or release gate; they are records evidence only.

## How to re-run (exact commands, from `<attempt>/checkout/tools/monkey_campaign/contributions/MAT2-B02/work`)

```
python -B b02_checks.py                 # Ran 11 tests — OK; writes runs/suite_comparison_count.json
python -B diagnostics/b02_diagnostics.py   # writes runs/static_diagnostics.json; run twice, byte-compare
```

Prerequisites: the blob-form extraction `work/frozen/1af0bbde/` (regenerate
with `git cat-file blob 1af0bbde:<path>`) and the coupons
`python -B coupons/build_coupons.py` (deterministic).

## Primary artifact identity (raw sha256, bytes on disk)

- `work/runs/static_diagnostics.json`:
  `f91c9fc1dca57234e23c1540f40c66c167e6946635270ea36285b002b0e59aed`
  (byte-identical across two runs; full three-class manifest for every
  artifact inside the file itself).
- `PREREGISTRATION.md` (frozen, verbatim):
  `8d5c922a0ab88a2c773d905481d16af0b644748c01789a5b9a94ceb656c51238`
- `clause_map.md` (reconcile deliverable):
  `c6bd992129fe2171bf3d895cc9b63955311402f2d7c3a1b739c537c8a865d2e6`
- Remaining identities: `work/runs/static_diagnostics.json#/evidence_classes`
  (raw / LF-canonical / git blob OID per artifact, 40+ artifacts).
