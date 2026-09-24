# M05 preregistration — input-order invariance of the body-mass export (FROZEN)

Frozen: 2026-09-24, BEFORE any exporter execution in this task. Agent M05.
Workspace: worktree `E:/ChimeraWork/mvc-20260924`, branch `material-volume-campaign-20260924`,
HEAD at freeze time `0c5cbbf0f1cb29d10848c0de4fed59cb35f8db6b` (base `3db8bc4e` is an ancestor).
tools/ and docs/ untouched (READ-ONLY law); all writes confined to `material_volume_campaign/agents/M05_order/`.

## 0. What was done before this freeze (fixture construction only, no pipeline execution)

Fixture builder `work/build_fixtures.py` (pure numpy geometry checks; the exporter/admission/compiler
were NOT imported or run before this freeze). It authored a Kuhn-subdivided unit cube
(6 positively oriented conforming tets, 12 boundary triangles, closed boundary edges,
oppositely oriented shared faces, no coincident nodes, no duplicate tets) with 3 regions/
materials/owners (densities 12.0 / 6.0 / 3.5 kg/m^3) and 3 authored bodies:
`body-alpha` = {cell-t0, cell-t1, cell-t2} (mixed densities), `body-beta` = {cell-t3, cell-t4},
`body-gamma` = {cell-t5}. Mixed densities inside one body make float summation order observable
if the exporter failed to canonicalize cell order.

Fixture file sha256s at freeze time (files under `fixtures/`):

| run | manifest.json | partition.json | groups.json |
|---|---|---|---|
| base | `c7db5ed02530dfd7238e150d3cfc51dc0dd8e620d3b91da1422d0f0dd7fccc15` | `6d84a7777980b5b9fd5c5ebd924c53b06a602386e163a767b2cd5b12d26f96e8` | `9e8c4ac3ff02bcb4dce45ca424d074bb8e7fb0c37d3eab8b26a20bc54f6c3d50` |
| P1-cells-reversed | `c7db5ed0…ccc15` (same) | `95fa5ff014597b0e5ebd15da9717980231d56ca5e075b0abda751aeb046035e9` | `9e8c4ac3…c3d50` (same) |
| P2-cells-shuffled | `c7db5ed0…ccc15` (same) | `5076ec218e8180fe119d4ae1a7622faf74158589edaa4038064c80793175e4da` | `9e8c4ac3…c3d50` (same) |
| P3-groups-reordered | `c7db5ed0…ccc15` (same) | `6d84a777…f96e8` (same) | `062d8ad1b3b6a56fe1e8573059051149bdbe5f82a38b40713d666d8cb1fc01fa` |
| P4-group-cell-records-reversed | `c7db5ed0…ccc15` (same) | `6d84a777…f96e8` (same) | `3785a3db26e93878d125565fe5510630ac03c77c3b8bd085d114679c6134a08f` |
| P5-manifest-entries-reversed | `6de528960bafead577ac27cdd0c47bbda346790bf42216a40c2121dfba8c6ab2` | `6d84a777…f96e8` (same) | `9e8c4ac3…c3d50` (same) |

Each permutation changes exactly ONE input document's bytes; the other two are byte-identical to base.

## 1. Permutations (frozen definitions)

- **P0 (baseline reference)**: unpermuted fixture triple; run TWICE (P0a, P0b) for the determinism control.
- **P1 `cells-reversed`**: `partition.cells` array order reversed.
- **P2 `cells-shuffled`**: `partition.cells` shuffled with `random.Random(20260924).shuffle`
  (frozen seed; observed resulting order: cell-t3, cell-t5, cell-t2, cell-t1, cell-t4, cell-t0).
- **P3 `groups-reordered`**: `groups.body_groups` array order reversed.
- **P4 `group-cell-records-reversed`**: within each body group, `cell_ids` array reversed.
- **P5 `manifest-entries-reversed`**: manifest arrays `vertices`, `cells`, `regions`,
  `matter_ownership` each reversed (`source_effective_segment_ids` is `[]`; reversing is a no-op — recorded).

## 2. Expectations, frozen before execution

Layer (a) PHYSICAL — per permutation P1..P5 vs P0, parsed from the emitted reports:
- **E-PHYS-1 (primary, exact)**: every body's `mass.value`, `volume.value`, `center_of_mass.value`
  (3 components), and `inertia_tensor_about_com.value` (9 entries) are **bit-identical** to P0
  (exact float equality; recorded as float.hex()).
- **E-PHYS-1 (fallback freeze)**: if any quantity differs, it is graded against relative tolerance
  **≤ 1e-12**; anything within is recorded as PASS-WITHIN-FROZEN-TOLERANCE and **FLAGGED** with
  analysis (defect vs summation-order artifact); anything beyond is FAIL.
- **E-PHYS-2**: ownership/accounting identical: `export_status`, `admission_status`,
  `admission_reason_codes`, `unassigned_cell_ids`, and per body `owned_cell_ids` +
  full `cell_provenance` rows.
- **E-PHYS-3**: `admission_report_sha256` (root and per body) identical across P0..P5.
  Rationale (derivation, not hope): the exporter sorts group cell_ids (`_parse_groups`), sorts
  groups by `body_id`, sorts cells by `cell_id` before `_integrate_cells`, and the admission
  adapter sorts vertices/cells/materials/regions/claims and emits sorted rows — so the float64
  summation order and every output array are fixed by IDs, not by input order. The ≤1e-12
  tolerance exists only in case a summation order subtly differs; exact equality is the derived
  expectation.
- Physical sanity anchors (analytic): cube volume 1.0 m^3; body-alpha V=1/2, body-beta V=1/3,
  body-gamma V=1/6; masses 6.0 / 2.0 / 0.5833… kg.

Layer (b) BYTE — per permutation vs P0, over captured stdout bytes:
- **E-BYTE-0**: P0a vs P0b byte-identical stdout (promise: "emits deterministic … JSON to stdout").
- **E-BYTE-1/2 (P1/P2)**: stdout differs from P0 **exactly and only** in the
  `input_hashes.partition_sha256` field values (root + each `body_groups[*].input_hashes`).
- **E-BYTE-3/4 (P3/P4)**: differ exactly and only in `input_hashes.body_groups_sha256`.
- **E-BYTE-5 (P5)**: differs exactly and only in `input_hashes.manifest_sha256`.
  Promise basis: the input-document hashes are defined over "the exact serialized inputs,
  including row ordering" (body_export doc L46) — so the hash of a permuted document MUST change,
  and no other output byte is licensed to change by any contract line found.
- **E-BYTE-NEG (negative control)**: a byte change ANYWHERE OUTSIDE the input_hashes fields is a
  falsifier hit (see §3). Conversely, a permuted input whose hash did NOT change is also a
  falsifier hit (the hash would fail to "identify the exact serialized inputs, including row ordering").

## 3. Verdict rules / falsifiers (frozen)

1. PHYSICAL quantity change under any permutation:
   - exact-identical → **PASS-EXACT** (physical invariance holds bitwise).
   - within ≤1e-12 relative → **PASS-WITHIN-FROZEN-TOLERANCE** + mandatory FLAG + analysis
     (defect vs summation artifact).
   - beyond → **DEFECT** (preserved: inputs, outputs, diff under receipts/).
2. BYTE change violating a promise:
   - output bytes change outside `input_hashes.*` fields under a pure input permutation →
     **DEFECT** (violates the determinism + hash-carries-ordering design; nothing else in the
     contract licenses input order to alter output content).
   - permuted input's hash NOT changing → **DEFECT** (violates "identifies the exact serialized
     inputs, including row ordering").
   - byte change confined to the corresponding `*_sha256` field → **PASS-PROMISED**
     (the change IS the promise: order-sensitive input hashes).
3. Byte behavior not covered by any promise and not in (2) → **UNPROMISED-OBSERVED** finding +
   decision request (what should be promised is Astra's, not M05's).
4. Any run crashing / refusing on a valid permuted fixture → **DEFECT** (preserve stderr+exit).

## 4. Execution plan (frozen)

- Module copies under `work/modules/` (`material_volume.py`, `material_volume_admission.py`,
  `material_volume_body_export.py`); run from `work/modules` so imports resolve to the copies;
  `PYTHONDONTWRITEBYTECODE=1`; CPU-only (numpy only; no Ollama/GPU).
- 7 runs total: P0a, P0b, P1..P5. Each: `python material_volume_body_export.py --manifest …
  --partition … --groups …` with stdin/stdout captured as raw bytes to `receipts/`;
  sha256 per capture; exit codes recorded.
- Comparison harness `work/compare.py`: (i) byte layer — sha256 table + recursive JSON-path diff
  of parsed reports; (ii) physical layer — exact float comparison (float.hex) of the §2 fields;
  (iii) verdicts per §3.
- Integrity: `git -C E:/ChimeraWork/mvc-20260924 status --porcelain -- tools Chimera/docs/matter`
  must paste EMPTY in report.md.

## 5. Promise ledger quoted at freeze time (details in report.md §1)

- body_export doc L14: "emits deterministic `chimera.rigid_body_mass_export.v1` JSON to stdout".
- body_export doc L46: hashes use "UTF-8 compact canonical JSON (sorted object keys, array order
  preserved); it identifies the exact serialized inputs, including row ordering"; "Output records
  are key-sorted canonical JSON with no timestamps, random IDs, or non-finite numbers."
- admission doc L51/L87: "deterministic compiler indexing order only in local arrays";
  "cell rows sorted by stable cell ID, sorted discrepancy/reason lists, canonical JSON key order".
- admission doc L63/L67: geometry signature "invariant to cell order"; reordering input cell rows
  "preserve[s] canonical identity".
- compiler doc L16/L29/L32: one accounting row per input tet; "The compiler never reorders or
  repairs a cell"; `cell_proposals` "Exactly nT rows in tetrahedron order" (positional binding).
- In-report self-description (exporter L168): `"serialization": "UTF-8 canonical JSON (sorted
  object keys; array order preserved)"`.
- Consumption proposal v0.9 L31: `input_hashes` = "SHA-256 of manifest, partition, body-group
  documents (canonical JSON) | integrity anchors".
- Receipt L148 (U6, OPEN): "cell-reorder / vertex-renumber invariance of the **export report**
  (admission-report level is tested; export-report level is not)" — THIS EXPERIMENT IS THAT TEST
  for the cell-reorder half (vertex-renumber half remains open; not in this brief's permutation set).
- NO prose line found promises export-report physical quantities or output array order are
  invariant to input row order. That invariance is this experiment's measurement, not a promise.
