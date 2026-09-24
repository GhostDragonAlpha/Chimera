# M05 report — input-order invariance of `chimera.rigid_body_mass_export.v1`

Agent M05 · 2026-09-24 · workspace worktree `E:/ChimeraWork/mvc-20260924`
(branch `material-volume-campaign-20260924`; campaign base `3db8bc4e`; HEAD at prereg freeze
`0c5cbbf0`, HEAD at report time `f666e84f` — two parallel-agent commits landed mid-task,
`git diff 0c5cbbf0 f666e84f -- tools Chimera/docs/matter` is empty, see §6).
Preregistration: `prereg.md` (frozen BEFORE first successful exporter execution).
All artifacts under `material_volume_campaign/agents/M05_order/`; `tools/` and `docs/` untouched.

## 0. Verdict summary

| layer | result |
|---|---|
| **PHYSICAL invariance** | **PASS-EXACT, all 5 permutations + rerun**: mass, volume, COM (3 comps), full 9-entry inertia tensor, ownership, cell provenance, unassigned set, statuses — bit-identical (`float.hex` equality) to baseline under every permutation. The ≤1e-12 frozen tolerance was never needed; no deviation existed to classify. |
| **BYTE behavior** | **PASS-PROMISED, all 5 permutations**: each permutation changes stdout bytes EXACTLY and ONLY in the one `input_hashes.*_sha256` field that corresponds to the permuted document (root + 3 body copies; 4 JSON paths, nothing else). Rerun determinism P0a==P0b byte-identical. |
| **Falsifiers** | None fired. No physical-quantity change (defect rule 1), no byte change outside the promised hash fields (defect rule 2), no unresponsive hash (defect rule 2b), no crash/refusal on valid permuted input (rule 4). |

One **UNPROMISED-OBSERVED** finding (favorable direction, §5) and two **decision requests** (§5).

## 1. The promised contract (quote table)

Established from docs + schemas before execution. `NONE-exists` does NOT hold: serialization
determinism IS promised; input-order behavior is promised for the HASHES, and is SILENT for the
export report's physical content and array order.

| # | source | quote (verbatim) | what it promises about order |
|---|---|---|---|
| Q1 | `Chimera/docs/matter/material_volume_body_export.md` L14 | "The command emits deterministic `chimera.rigid_body_mass_export.v1` JSON to stdout." | Same inputs → same output bytes. Says nothing about which INPUTS are "the same" (bytes? rows?). |
| Q2 | body_export doc L46 | "Each document hash uses UTF-8 compact canonical JSON (sorted object keys, array order preserved); it identifies the exact serialized inputs, **including row ordering**." | Input-document hashes are ORDER-SENSITIVE by design: permuting input rows MUST change the corresponding hash. Object-key order is NOT part of identity; array/row order IS. |
| Q3 | body_export doc L46 | "Output records are key-sorted canonical JSON with no timestamps, random IDs, or non-finite numbers." | Output object keys are canonicalized; no nondeterministic content. Silent on output ARRAY order. |
| Q4 | body_export doc L66 | checks cover "deterministic hashes/report serialization" | Author claims same-input determinism is tested. Verified at `tools/material_volume_body_export_checks.py:228` (`test_report_hashes_and_cli_output_are_deterministic_and_finite`): same-input only — input-ORDER variance is NOT tested there. |
| Q5 | `material_volume_admission.md` L51 | "The adapter turns stable IDs into a deterministic compiler indexing order only in local arrays. It does not reorder or repair tetrahedron orientation." | Admission-layer ordering is ID-canonicalized, promised deterministic. |
| Q6 | admission doc L87 | "The report includes cell rows sorted by stable cell ID, sorted discrepancy/reason lists, canonical JSON key order, compact separators, ASCII escaping, and `allow_nan=False`." | The freshly recomputed admission report (hence `admission_report_sha256`) is built from order-normalized structures. |
| Q7 | admission doc L63, L67 | identity digests are "SHA-256 of sorted records … Stable IDs, region labels, proposal order, input cell order, and local vertex numbering are excluded"; "reorder input cell rows; reorder the vertex table … **Preserve canonical identity**" | Canonical identity vs physical equivalence split is explicit AT ADMISSION LEVEL. |
| Q8 | `material_volume_compiler.md` L29, L32, L16 | "The compiler never reorders or repairs a cell"; "`cell_proposals` … Exactly `nT` rows in tetrahedron order"; "one output accounting row for every input tetrahedron" | Compiler lane: rows are POSITIONAL (permuting cells without proposals would be a different input); not the exporter's row-permutation path (exporter cells carry proposals inline). |
| Q9 | exporter report self-description (`tools/material_volume_body_export.py:168`, emitted into every report) | `"serialization": "UTF-8 canonical JSON (sorted object keys; array order preserved)"` | The report itself declares the hash canonicalization; "array order preserved" = serialization does not reorder arrays — it does NOT say output arrays follow input order. |
| Q10 | `rigid_body_mass_export_consumption_contract_v1_proposal.md` L31 (proposal v0.9) | "`input_hashes` \| SHA-256 of manifest, partition, body-group documents (canonical JSON) \| integrity anchors" | Hashes are integrity anchors over exact serialized inputs. |
| Q11 | `material_volume_export_verification_receipt.md` L148 (OPEN U6) | "cell-reorder / vertex-renumber invariance of the **export report** (admission-report level is tested; export-report level is not)" | The author's own open item: export-report-level order invariance UNTESTED. **This experiment is that test** (cell-reorder half; vertex-renumber half remains open — outside this brief's permutation set). |
| Q12 | campaign `TASK_BOARD.md` L19 (C-1) | "C-1 = example-report serialization regenerated as canonical CLI bytes, content unchanged" | C-1 concerns the saved example matching CLI canonical bytes; it adds no input-order promise. |
| Q13 | `tools/material_volume_body_export_schema.json` | (grep for order/determin/canon/sort/stable: **no matches**; only frame descriptions) | The groups request schema promises NOTHING about ordering. |

**The gap this experiment measured** (not a promise, a measurement): no prose line states that
exported mass/COM/inertia/ownership or output array order are invariant to input row order.
Q2 licenses (indeed requires) the input hashes to move; everything else moving is licensed by
nothing — which is why E-BYTE-1..5 froze "exactly and only the hash field" as the promised shape.

## 2. Frozen preregistration

`prereg.md` — fixtures' sha256s, permutation definitions (P1 cells-reversed, P2 cells-shuffled
seed `random.Random(20260924)`, P3 groups-reordered, P4 group-cell-records-reversed,
P5 manifest-entries-reversed), expectations E-PHYS-1/2/3 + E-BYTE-0..5 + negative control,
verdict rules. Frozen before the first successful exporter execution; the only execution before
the freeze was fixture construction (`work/build_fixtures.py`, pure-geometry checks, no pipeline
import).

Fixture: Kuhn-subdivided unit cube, 6 positively oriented conforming tets, 12 boundary
triangles, closed boundary edges, oppositely oriented shared faces (validated pure-numpy).
3 regions/materials/owners (12.0 / 6.0 / 3.5 kg/m^3), 3 bodies: `body-alpha` = {t0,t1,t2}
(MIXED densities — makes float summation order observable if cell order leaked into integration),
`body-beta` = {t3,t4}, `body-gamma` = {t5}. All from the EXISTING schemas
(`chimera.fitting_manifest.v1`, `chimera.material_partition.v1`, `chimera.rigid_body_cell_groups.v1`).

## 3. Receipts (7 runs; all exit 0, all `export_status: complete`)

| run | fixture | stdout sha256 | bytes |
|---|---|---|---|
| P0a | base | `8a69419e03d6db59e8b9e6bbdb779299732a7700eb39d8cc845f2c8cd4648d11` | 8927 |
| P0b | base | `8a69419e03d6db59e8b9e6bbdb779299732a7700eb39d8cc845f2c8cd4648d11` | 8927 |
| P1-cells-reversed | P1 | `3157db428ba94c30b8a36a3f57a2480cf919752167a697847e90c6021f275934` | 8927 |
| P2-cells-shuffled | P2 | `39cfb76f7760a2afe423dd6a8831aafcab0c7e424cb08bd8debddcb76d7f5e9b` | 8927 |
| P3-groups-reordered | P3 | `3b047ca95da07e40bb15c1943894cc7d4268ac6f6ea786623dbdba7aa6e23b77` | 8927 |
| P4-group-cell-records-reversed | P4 | `bc0c2ccd4a9d3f49cc58a5d96804881e87b526002581bed07ab8c94770198ee5` | 8927 |
| P5-manifest-entries-reversed | P5 | `c65dbbad9101575883bd97b607b68d3206b624e434e861488638c29fc4599577` | 8927 |

Raw captures: `receipts/run_*.stdout.json` (+ empty stderr files), `receipts/runs_summary.json`,
full comparison transcript `receipts/compare_output.txt`, dir seal `receipts/receipts_manifest.sha256`.
Module copies `work/modules/` verified sha256-identical to `tools/` originals before running
(`material_volume.py 6d2817b7…`, `material_volume_admission.py d6d4b0e0…`,
`material_volume_body_export.py 04be88a7…`); `PYTHONDONTWRITEBYTECODE=1`; CPU-only.

## 4. Comparisons

### 4a. Byte layer (vs P0a; full paths in `receipts/compare_output.txt`)

| permutation | diff paths | changed field(s) | outside promise | verdict |
|---|---|---|---|---|
| P0b (rerun) | 0 | none | none | **PASS** (Q1 determinism held: byte-identical) |
| P1 cells-reversed | 4 | `partition_sha256` only (`b0b8366e…`→`b276a269…`) | none | **PASS-PROMISED** (exactly Q2's shape) |
| P2 cells-shuffled | 4 | `partition_sha256` only (`…`→`35740839…`) | none | **PASS-PROMISED** |
| P3 groups-reordered | 4 | `body_groups_sha256` only (`c1e57698…`→`9c228df8…`) | none | **PASS-PROMISED** |
| P4 group-cell-records-reversed | 4 | `body_groups_sha256` only (`…`→`743dbdc4…`) | none | **PASS-PROMISED** |
| P5 manifest-entries-reversed | 4 | `manifest_sha256` only (`ec2da158…`→`6df6cd1e…`) | none | **PASS-PROMISED** |

The 4 paths per permutation are `$.input_hashes.X` and `$.body_groups[0..2].input_hashes.X`.
Negative controls both clean: (i) no byte moved outside the licensed field; (ii) every permuted
input's hash DID move, and each emitted hash value equals the exporter's own canonical hash of
that run's fixture triple (recomputed independently in `work/compare.py` — 7/7 True), so the
hashes genuinely identify "the exact serialized inputs, including row ordering" (Q2).

### 4b. Physical layer (parsed reports; floats compared via `float.hex`)

| run | mass/volume/COM/inertia (all bodies) | ownership + provenance + statuses | `admission_report_sha256` | verdict |
|---|---|---|---|---|
| P0b, P1, P2, P3, P4, P5 | bit-identical to P0a | identical | identical (1 distinct value across all 7 runs) | **PASS-EXACT** |

- E-PHYS-1: exact equality held everywhere — the frozen ≤1e-12 tolerance was never consulted.
  This matches the derivation: the exporter sorts group `cell_ids`, sorts groups by `body_id`,
  and sorts cells by `cell_id` BEFORE `_integrate_cells`, so the float64 summation order is fixed
  by IDs; permuting input rows cannot perturb even one ulp. The mixed-density body-alpha made any
  order leak observable; none occurred.
- E-PHYS-2: `export_status: complete`, `admission_status: validation_only_admissible`,
  empty `unassigned_cell_ids`, sorted `owned_cell_ids` and `cell_provenance` — identical under
  all permutations. P3 output body order remained `[alpha, beta, gamma]` (ID-sorted, NOT
  input-following); P4 output `owned_cell_ids` remained sorted.
- Analytic anchors: volumes exact — alpha 0.5, beta 1/3, gamma 1/6 (delta +0.000e+00 each).
  **Honest anchor correction**: prereg §2 wrote "masses 6.0 / 2.0 / 0.5833… kg" — an arithmetic
  slip in MY prereg (I derived anchors from a density mapping I did not use when authoring the
  fixture). The anchors implied by the frozen fixture definition are alpha = 21.5/6 =
  3.583333333333333…, beta = 18/6 = 3.0, gamma = 3.5/6 = 0.5833333333333333…; the exporter
  matches all three (gamma differs 1 ulp from the naive `3.5/6` float expression because the
  exporter computes `volume*density`, not `density/6` — anchor-side artifact, not a pipeline
  deviation). The preregistered comparisons (all P0-relative) are unaffected by the anchor slip.

## 5. Findings and decision requests

1. **UNPROMISED-OBSERVED (favorable): output array order is ID-sorted, not input-following.**
   Under P3/P4 the emitted `body_groups` and `owned_cell_ids`/`cell_provenance` orders are
   canonical ID order. No doc line promises this (Q3 is silent on arrays; Q9 explicitly
   disclaims reordering only at serialization time). It is implemented
   (`_parse_groups`, `cells.sort` at `tools/material_volume_body_export.py:146/152/472`) but
   UNPROMISED. Recorded, not tuned.
2. **DECISION REQUEST (Astra): promise physical invariance explicitly.** The property this
   campaign cares about — "permuting input rows does not change exported mass/COM/inertia/
   ownership; the input hashes alone carry row-order identity" — is implemented and now
   measured, but zero prose states it (Q1–Q13; the receipt's U6 is the acknowledgment of the
   hole). One sentence in `material_volume_body_export.md` §"Report and hashes" would close it.
   What SHOULD be promised is Astra's call; M05 only records that the current behavior equals
   the natural reading of Q2+Q6.
3. **DECISION REQUEST (Astra): promise output array order.** Either "output arrays are ordered
   by stable ID" or "output arrays follow input order" — today it is the former by code only.
   Related open item U6's vertex-renumber half remains untested (outside this brief's
   permutation set); the admission layer already covers it (Q7).
4. **U6 status**: the cell-reorder half of U6 is now measured at export-report level (5
   permutations, PASS). This is evidence for the open reviewer item, not an adjudication of it.

## 6. Integrity

```
$ git -C E:/ChimeraWork/mvc-20260924 status --porcelain -- tools Chimera/docs/matter
(empty — exit 0)
```

## 7. Execution notes (failures preserved)

- **First harness invocation failed 7/7** (exit 1, empty stdout, stderr preserved at
  `receipts/run_P0a.stderr.txt` etc.): my hand-built subprocess environment dropped the variable
  numpy needed (`ModuleNotFoundError: numpy`). Harness bug, not pipeline behavior; fixed by
  inheriting `os.environ` + forcing `PYTHONDONTWRITEBYTECODE=1` in the child
  (`work/run_permutations.py`). The broken run's stdout hash `e3b0c442…` (empty-input sha256)
  is preserved in `runs_summary.json` history of that invocation only via stderr files.
  A stale `work/modules/__pycache__/` from that un-banned child was deleted before sealing.
- **Shared-worktree drift**: commits `7701d8db` (M09) and `f666e84f` (M04 log) landed after my
  freeze; `git diff 0c5cbbf0 f666e84f -- tools Chimera/docs/matter` is EMPTY (verified), so the
  code under test did not move during the experiment. No commit made by M05.

## 8. STOP statement

Verdicts rendered per prereg §3: PHYSICAL PASS-EXACT (5/5 permutations), BYTE PASS-PROMISED
(5/5) + determinism PASS, zero falsifier hits, one UNPROMISED-OBSERVED finding, two decision
requests. Failures preserved (§7). M05 stops here.
