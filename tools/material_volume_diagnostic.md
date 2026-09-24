# `material_volume_diagnostic` — usage, frozen exit contract, ordering & identity documentation

Promotion home: `tools/` (game lineage) — see `../report.md` §Publication.
This doc travels with the tool. Version 1.0.0 (promotion candidate, post-B8
code, pinned by blob in `dependency_manifest.md`).

## 1. What it is

A **read-only, static diagnostic CLI** for `chimera.rigid_body_mass_export.v1`
reports. It validates NOTHING of its own: all parsing goes through
`material_volume_body_export.read_json_file` (strict: duplicate keys and
nonstandard constants rejected), all validation/statuses/summaries/readiness
through `material_volume_body_export_reader.summarize_export_report`, machine
serialization through `material_volume_body_export_reader.canonical_json`.
Fields the reader's summary drops (`blocking_cell_ids`,
`blocking_assignment_statuses`, top-level `reason_codes`/`detail`,
per-cell `unassigned_cells` rows) are passed through FROM THE RAW READER-PARSED
MAPPING for DISPLAY only — never re-validated, never turned into new statuses.
No input file is ever written or mutated; `sys.dont_write_bytecode` is set
before the reader import so no `__pycache__` can appear in `tools/`. Readiness
is displayed as-is and stays `false` (CON-14); nothing is ever promoted.
CPU-only; no runtime wiring into any engine or pipeline.

## 2. Usage

```
python material_volume_diagnostic.py REPORT [REPORT ...] [--json] [--tools-dir DIR]
```

- `REPORT` — one or more export-report JSON paths (read-only).
- `--json` — machine output: one object, canonical JSON (frozen contract:
  top-level `tool`, `readiness: false`, `reports[]` in argv order; per-report
  fields per M09's frozen output contract v1).
- default — deterministic human-readable line grammar; the FINAL LINE of every
  human-mode run is `readiness: false` (F2 sentinel).
- `--tools-dir DIR` (or env `M09_TOOLS_DIR`, or default: nearest ancestor
  directory containing `tools/material_volume_body_export_reader.py`) — the
  ONE dependency directory; all four local modules must coexist there (see
  `dependency_manifest.md`). The env var keeps its frozen historical name
  `M09_TOOLS_DIR`; renaming it would be a behavior edit, which promotion
  preparation forbids.

## 3. Exit codes — frozen, THIS TOOL's OWN contract

| exit | meaning |
|---|---|
| `0` | every report accepted by the reader — ANY of the five statuses (`complete`, `partial`, `blocked`, `unsupported`, `refused`) is a successfully DIAGNOSED report |
| `2` | the reader rejected at least one report (`ExportInputError`) |
| `4` | readiness-violation alarm (falsifier F2: a summary carried `dynamics_readiness_claimed != false`; must never fire) |
| `64` | usage error (argparse; BSD `sysexits.h` EX_USAGE convention — B8's recorded decision for the frozen "other nonzero" slot, distinct from {0, 2, 4}; stderr text byte-identical to argparse's default) |

**Scope note (explicit):** this 0/2/4/64 contract is the diagnostic CLI's own
frozen contract (M09 `preregistration.md`, "Exit codes (frozen)", B8 decision
D1). The 0/2/1 exit mapping discussed under M06-H04 belongs to the VALIDATION
CLI (M10/W6), NOT to this tool. Do not reconcile the two tables; they govern
different programs.

## 4. Ordering and invariance — MV-O2/O3

> Astra decision, verbatim: "Document the producer's exact current ordering and
> supported physical-invariance promises, backed by the M05 receipts. Separate
> input permutation, physical-value equality, output-array order and byte
> equality. Do not promise invariance outside the proved domain or change
> sorting merely to make an assertion true."

The producer is `tools/material_volume_body_export.py` (this tool only DISPLAYS
its reports). Four separate claims, four separate statuses. Receipts:
`material_volume_campaign/agents/M05_order/report.md` +
`M05_order/receipts/` (7 runs: base P0a, rerun P0b, permutations P1–P5, coupon
fixture with 6 tets / 3 bodies / mixed densities in body-alpha).

| # | claim | status | evidence (M05) |
|---|---|---|---|
| 1 | **Input permutation** (permuting input rows — cells, groups, group-cell records, manifest entries — changes the report's `input_hashes`) | **PROMISED** by the producer doc: per-document hashes "identif[y] the exact serialized inputs, **including row ordering**" (`Chimera/docs/matter/material_volume_body_export.md` L46). Hashes are order-sensitive BY DESIGN. | PASS-PROMISED 5/5: each permutation moved EXACTLY the one hash field corresponding to the permuted document, at exactly 4 JSON paths (`$.input_hashes.X` + 3 body copies), never elsewhere; every emitted hash equals the exporter's own canonical hash of that run's fixture triple (7/7 independently recomputed). |
| 2 | **Physical-value equality** (mass, volume, COM (3 comps), full 9-entry inertia tensor, ownership, cell provenance, unassigned set, statuses, `admission_report_sha256` under input permutation) | **PROVED-EXACT at M05, NOT YET PROMISED in prose** (this measurement gap is exactly decision request MV-O2; until Astra writes the promise, cite the receipts, not a doc line). | PASS-EXACT 5/5: bit-identical (`float.hex` equality) to baseline under every permutation; the frozen ≤1e-12 tolerance was never needed; `admission_report_sha256` had 1 distinct value across all 7 runs. Mechanism: the exporter sorts group `cell_ids`, groups by `body_id`, cells by `cell_id` BEFORE `_integrate_cells`, so float64 summation order is ID-fixed. |
| 3 | **Output-array order** (`body_groups`, `owned_cell_ids`, `cell_provenance` ordering in the EMITTED report) | **CURRENT BEHAVIOR: canonical stable-ID order — implemented but UNPROMISED** (decision request MV-O3 open; no doc line promises it: the serialization line is silent on arrays, and "array order preserved" is a serialization-time disclaimer only). Recorded, not tuned. | Measured: under P3 (groups reordered) and P4 (group-cell records reversed), emitted order remained `[alpha, beta, gamma]` (ID-sorted, NOT input-following); `owned_cell_ids` remained sorted. Implementation: `tools/material_volume_body_export.py` `_parse_groups` / `cells.sort` (sorts at parse time). |
| 4 | **Byte equality** of producer stdout | **PROMISED for same-input determinism** ("The command emits deterministic `chimera.rigid_body_mass_export.v1` JSON to stdout", body_export doc L14; "Output records are key-sorted canonical JSON with no timestamps, random IDs, or non-finite numbers", L46). **NOT promised and NOT true** that different-order inputs give equal bytes — claim 1 says the opposite. | P0a == P0b byte-identical (rerun determinism held, sha256 `8a69419e…`, 8927 B). Under permutation, bytes change EXACTLY and ONLY in the licensed hash fields (claim 1). |

**Proved domain (do not exceed it):** the physical-equality proof covers
export-report-level ROW permutations P1–P5 of the M05 coupon fixture (cell
reorder, cell shuffle, groups reorder, group-cell-record reversal, manifest
entry reversal). The VERTEX-RENUMBER half of open item U6 is NOT tested at
export-report level (admission level already covers it). Nothing here may be
read as promising invariance for transforms, rescaling, different fixtures, or
any mutation other than input-row permutation — those are separate campaign
results (M02/M03/M04/M08), not this document's claims. No sorting was changed
to make any assertion true; all ordering statements describe the producer's
existing code.

## 5. Artifact identity layers — MV-B4-1

> Astra decision, verbatim: "Preserve the existing pretty-form artifacts. Use
> Git blob identity and the consumption contract's LF-only text identity for
> portable claims; raw equality remains a distinct claim."

Three identity claims, deliberately NOT interchangeable (mechanism measured by
B4: disk and `git archive` extracts are the CRLF-smudged layer — 0/37
blob-identical; B4's portability contract: "blob OID at pinned rev + SHA-256
over LF-canonical bytes — disk hashes and archive-extract hashes are neither"):

1. **Git blob identity** — `git ls-tree <rev> -- <path>` OID. The portable
   identity for ANY claim about "the same file". Used throughout
   `dependency_manifest.md` (every dependency and source blob).
2. **LF-only text identity** — SHA-256 over LF-canonical bytes (the consumption
   contract's text-identity rule). The portable claim for CONTENT across
   checkouts with different `core.autocrlf` materializations.
3. **Raw (disk) equality** — SHA-256 of the checkout's on-disk bytes.
   Checkout-materialization-dependent; a DISTINCT, weaker claim. Recorded in
   this promotion (`receipts/dependency_oids.json`
   `working_tree_sha256_at_freeze`) only as a freeze-time fact, never
   substituted for 1 or 2.

Application to this promotion: the pretty-form artifacts (human-mode outputs,
`output_samples.txt`, this documentation, the receipts themselves) are
PRESERVED as-is — nothing was re-canonicalized to make comparisons easier.
Where W5 receipts claim equality between runs, they use layer 1 or layer 2
(battery: full stdout/stderr byte comparison within ONE checkout, which is a
raw claim scoped to a single materialization — valid there because both CLIs
ran in the same checkout; cross-checkout claims must use 1/2).

## 6. Source receipt trail

- **M09** (commit `7701d8db`): implemented + integrated, 11/11 tests, U7
  finding recorded. Preregistration: `agents/M09_diagnostic/preregistration.md`.
- **B2a** (review, `agents/B2a_review_m09/report.md`): ACCEPT-WITH-NOTES;
  hostile-input-only defects D1/D2/D3 named with probes.
- **B8** (commit `8c4f8ba2`, `agents/B8_fixes/fixes.md`): D1/D2/D3 fixed
  failing-first, 17/17, genuine outputs byte-identical pre/post (SHA-256
  `de0fdc5e…` on record).
- **W5** (this directory): promotion preparation — dependency pinning, docs,
  clean home copy, suite equivalence. No behavior change; publication after
  non-author review (hook in `../report.md`).
