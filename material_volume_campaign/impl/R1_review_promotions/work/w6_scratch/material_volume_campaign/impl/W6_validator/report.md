# W6 REPORT — validator reconciled to decided contract v1.0 + promotion prepared

Agent: W6_validator · 2026-09-24 · worktree `E:/ChimeraWork/mvc-20260924`
(branch `material-volume-campaign-20260924`; initial tip `d1c99335`, final tip `feb01661` —
W3+W1 integrated mid-session, see §6). No commit made (none requested); all W6 writes
confined to `material_volume_campaign/impl/W6_validator/`.

## ACCEPTANCE VERDICT: MET

All five acceptance criteria are satisfied. Measured headline numbers:

- **Suite: 101/101 green** (`receipts/test_run_full.txt`, pytest 9.0.2, Python 3.14.3, 2.0s) —
  the adapted M10 frozen suite (71) + 30 new reconciliation tests, re-run AFTER the
  sibling W3 reader integration so the green run tests the current dependency tip.
- **Every behavior change failing-first**: 5 captured FAIL→PASS receipt pairs under
  `receipts/failing_first/` (W6-RAW 1→3, W6-MVO1 5→5, W6-D2+records 4→5, W6-EXIT 3→7,
  W6-D3 11→11 counts are fail-then-pass totals per delta).
- **Original M10 dir untouched**: `git status --porcelain -- material_volume_campaign/agents/M10_validator`
  is EMPTY (`receipts/integrity_and_hashes.txt` paste); the staged copy was proven
  byte-identical (`cmp`) to the M10 original before the first edit, and the frozen
  M10 baseline was REPRODUCED green on the exact original bytes — 71/71
  (`receipts/baseline_71.txt`, run preserved under `receipts/baseline_reproduction/`).
- **Preregistration frozen BEFORE edits**: `PREREGISTRATION.md` sha256
  `d6ee7c1a6a10bd411f9142a042b8ca9ae40e992d7e90c0a178b02149918f9fe3`
  (`receipts/freeze_sha256.txt`, frozen 16:38:02; first code edit after it).
- **Dependency manifest + docs stub + tool-home proposal**: `docs/` (3 files, §5).

## 1. The reconciliation table (frozen; applied)

Contract = the MAIN checkout's
`E:/PythonChimera/Chimera/docs/matter/rigid_body_mass_export_consumption_contract_v1_proposal.md`
— **v1.0, D1–D5 decided 2026-09-24** (blob `ee254224…` @ main HEAD `b04a3acd`; raw
sha256 `c6977868…`). The worktree's copy is v0.9 and was NOT used
(grep: zero "decided" occurrences). M10 side = its PREREGISTRATION § DECISION
REQUESTS. Full quotes: `PREREGISTRATION.md` Part 1 (frozen). Summary:

| spot | M10 strictest reading | decided v1.0 reading (§5, as issued) | code delta |
|---|---|---|---|
| **D1** ← R12 | "any readiness claim anywhere = REJECT; no promotion path" | "Approve the contract for **static inspection and validation only**. Exporter success cannot promote a body to dynamics-ready. Runtime binding requires a separate Astra-approved qualification gate." (CON-14 stands) | **NO-CHANGE** to R12 — strictest = decided. Framing only: verdict's `decision_requests` → `decision_records`, `decided: true`, reading quoted |
| **D2** ← R2/R14 | "`partial` (and any unassigned cell) = REJECT always; no explicit-subset path" | "**Reject `partial` reports for assembly.** Diagnostic tools may inspect exported bodies only while explicitly displaying omitted bodies and unassigned cells. No subset-binding exception yet." (CON-3 amended) | **NO-CHANGE to the rejection** (operator: "Keep … partial-assembly rejection"); **DELTA W6-D2**: `preserved_diagnostics` now explicitly displays omitted bodies + unassigned cells on `partial` roots (was `blocked`/`refused` only) |
| **D3** ← R15 | "any recombination claim = REJECT; the validator computes no composite math" | "Allow **read-only aggregate calculations for verification**, with explicit frames and disjoint cell ownership. Do not collapse bodies, infer joints, or change runtime grouping." (new CON-16) | **NO-CHANGE to R15** (CON-16d + operator: does not authorize collapsed export bodies — report-side rejection kept); **DELTA W6-D3**: separate `verify_con16_aggregate` entry point (allowed shape implemented, see §3) |
| **D4** ← R16 | "any lineage field / non-v1 schema = REJECT" | "Retain v1's flat, pre-composed transforms. Defer v2." (CON-15 stands) | **NO-CHANGE** — strictest = decided |
| **D5** ← R2/R11/R13 | "`unsupported` status, non-`reconstructed_tissue_mass` authority, or any consumed source-payload flag = REJECT" | "Source-effective masses remain **unsupported**. No fallback or transport is authorized." (CON-5 stands) | **NO-CHANGE** — strictest = decided (operator: "Keep … source-effective exclusion") |

Non-spot deltas mandated by the brief, each itself a decided item: **W6-MVO1**
(MV-O1), **W6-EXIT** (M06-H04), **W6-RAW** (MV-B3-1) — quoted and specified in
`PREREGISTRATION.md` Part 2.

## 2. MV-O1 regression — blocked-body reduced hash vs full-report hash

New genuine producer evidence: `tests/fixtures/genuine_blocked_report.json`, generated
by the REAL exporter (`build_export_report`, example inputs with `tissue-B
density_kg_m3: null` — M07's C4 construction). Its hashes reproduce the M07 ownership
receipt EXACTLY: bodies `298c544846f7…` (reduced), root `4d4c43e1e0d1…` (full admission
document). The verdict now carries `admission_hash_scopes`:

- (a) **documents which reduced object a blocked-body hash covers**: each
  `not_exported` body is labeled `scope: "reduced_block_record"` with the exact
  definition — canonical-JSON sha256 of
  `{"decision": <body admission_status>, "reason_codes": <body admission_reason_codes>}`
  (exporter `_blocked_group`), explicitly "**NOT the admission report document and
  NEVER a full-report hash**".
- **Precision proof (test)**: recomputing the documented two-field object from the
  fixture's own fields equals each blocked body's recorded hash — measured
  `298c544846f7f6e521db7205472ccf542501d95db7c1b4a11f6ad744cf8dd60f`, exact match.
- (b) **verifies full-report identity separately at the handoff**: `full_report_identity`
  carries the contract §6 identities of the delivered document — `raw_file_sha256`
  (exact bytes) and `canonical_content_sha256` (CRLF/CR→LF), each named by its §6 claim
  kind, never conflated with any `admission_report_sha256`. Test measures the
  distinction: the raw-file hash differs from every blocked-body reduced hash on the
  same document.

## 3. CON-16 aggregation boundary — allowed shape implemented, forbidden shapes refused

D3 decided describes the allowed shape concretely, so it is IMPLEMENTED as a separate
entry point `verify_con16_aggregate(report)` + CLI `--verify-aggregate`
(docs/USAGE.md):

- (a) frames explicit: target = the report's **domain** frame with the CON-10
  convention stated, per-body `frame_id`/rotation/origin recorded verbatim;
  rotations consumed as authored, non-proper-orthonormal → refusal, never repair.
- (b) ownership disjoint and verbatim: cross-body cell overlap REFUSES naming the
  cell and both owners (tested: a crafted report that still passes per-body R11
  validation is refused by the aggregator — `ownership_not_disjoint: … cell-A …
  owner-A … owner-B`); one mass owner per cell from `cell_provenance`.
- (c) verification artifact with error accounting: `artifact_kind:
  "con16_verification_aggregate"`, orthonormality/determinant residuals,
  parallel-axis displacement norms, bodies count, tolerance 1e-12.
- (d) no collapse/rewrite/merge: input proven deep-equal before/after (test);
  artifact marked `not_a_v1_body_record`, `joints_inferred: false`,
  `runtime_grouping_changed: false`; `validate_report`'s verdict carries NO
  aggregate keys (separation test).
- Math measured: two-body example → mass `3.0 kg` exact; COM matches an independent
  in-test recomputation to ≤1e-15; single-rotated-body aggregate recovers
  `R·I·Rᵀ` / `R·com+origin` to ≤1e-15; symmetric positive-definite.
- Runs only on ACCEPT-verdicted reports (CON-1/2); refusal on everything else.
- R15 unchanged: a report carrying recombination fields is still REJECTED.

## 4. Exit classes (M06-H04 decided) — measured live

| input | exit | observed |
|---|---|---|
| accept fixture | **0** | `ACCEPT` on stdout (`receipts/cli_smoke.txt`) |
| genuine `partial` report | **2** | `REJECT` + `partial_rejected` named; preserved keys `['all_supplied_cells_assigned','bodies','unassigned_cell_ids','unassigned_cells']` |
| missing file | **2** | `could_not_evaluate: input_read_error: … FileNotFoundError` on stderr |
| injected internal failure | **1** | monkeypatched `validate_file` → `unexpected_internal_failure`, exit 1 |
| argparse usage error | **2** | named input refusal |

Compatibility note shipped in the module docstring, `--help` epilog, `--version`, and
docs: the original M10 tool keeps 0/1/2 = accept/reject/could-not-evaluate; the
promoted tool carries the decided mapping. `--version` identity:
`rigid_body_mass_consumption_validator W6-promotion 1.0.0 (M10 lineage, 71-test frozen
suite; contract v1.0, D1-D5 decided 2026-09-24; exit classes 0=accepted/2=named
refusal/1=unexpected internal failure per M06-H04)`.

## 5. Full-report requirement + promotion prep

- **MV-B3-1 (test-pinned)**: a GENUINE reader summary (produced in-test by the
  read-only `summarize_export_report` on the accept fixture) is REFUSED BY NAME:
  `summary_projection_is_not_a_consumption_document`, citing MV-B3-1 and
  `summarize_export_report`. A retyped summary (bodies grafted under
  `body_groups`) still REJECTS via the §1 authority rules the projection cannot
  satisfy (R11+R13 measured). The summary API is never imported, extended, or
  reinterpreted.
- **Promotion prep**: `docs/DEPENDENCY_MANIFEST.md` (exact 4-module import closure,
  proven by sandboxed import test incl. the `material_volume` transitive dep that
  broke M07's harness; Git blob OIDs at BOTH tips — authoritative `feb01661`:
  reader `1ee791e0…` (W3-repaired), exporter `f6fd2af1…`, admission `41615ec7…`,
  `material_volume.py` `3d46b030…`; decided-contract identity pinned to the MAIN
  checkout, blob `ee254224…`); `docs/TOOL_HOME_PROPOSAL.md`
  (the proposed home: tools/ + `rigid_body_mass_consumption_validator.py` (created at promotion), conventions checked against
  the existing `tools/` family, installation steps + explicit non-authorizations);
  `docs/USAGE.md` (usage, exit codes, static-only/no-runtime claim, hash scopes,
  CON-16 allowance).

## 6. Integrity (pastes in `receipts/integrity_and_hashes.txt`)

```
$ git -C E:/ChimeraWork/mvc-20260924 status --porcelain -- material_volume_campaign/agents/M10_validator
(empty)
$ git -C E:/ChimeraWork/mvc-20260924 status --porcelain | grep -v impl/W6_validator
?? material_volume_campaign/impl/W5_diag_promo/
?? material_volume_campaign/impl/W6_validator/
?? material_volume_campaign/impl/receipts/
```

- `tools/__pycache__` does NOT exist (M10 guard test passes in-suite).
- Final promoted-tool sha256:
  `5ecce0b5bbae6bf4e5e509a7eb72d45353ae42b6158a94d11ad7245d572c74fe`.
- **Mid-session sibling integration**: W3 (reader M13 repair) and W1 landed at
  16:50–16:51, moving the tip `d1c99335`→`feb01661`. Exactly one pinned dependency
  changed (the reader, +44 lines, blob `8a30267f…`→`1ee791e0…`; import block and
  summary layout unchanged). Manifest updated to pin the authoritative tip; the
  FULL suite was re-run AFTER integration: **101/101 green** (the green receipt
  tests the repaired reader). The earlier transient `M
  tools/material_volume_export_proof_verify.py` was W1's working tree, committed in
  `fe031402` — not a W6 write (`receipts/worktree_concurrent_activity.txt`).

## 7. Incidents (preserved per campaign law)

1. `tools/__pycache__` leak observed once mid-session (one
   `material_volume_body_export.cpython-314.pyc`), caught by the M10 guard test.
   Decisive attribution experiment: an UNPROTECTED in-process reader import
   reproduces exactly those pycs; all W6 deliverables are double-protected (env var
   + `sys.dont_write_bytecode` before import) and verified clean — including with
   the env var absent. Cleaned; full record: `receipts/tools_pycache_incident.txt`.
2. Fixture-generator first draft produced `blocked` instead of `partial` for the
   D2 fixture (unresolvable cell ≠ unassigned cell); fixed by replicating M07's
   exact C3 construction (region-C/tissue-C/matter-ownership). The blocked fixture
   regenerated byte-identically across runs (determinism observed).
3. Initial sandbox for the import-closure test used a POSIX temp path invisible to
   Windows Python; redone inside `tempfile` — result unchanged.

## 8. Files

- `E:/ChimeraWork/mvc-20260924/material_volume_campaign/impl/W6_validator/brief.md` (verbatim task brief)
- `…/impl/W6_validator/PREREGISTRATION.md` (frozen reconciliation table + membrane)
- `…/impl/W6_validator/rigid_body_mass_consumption_validator.py` (promotion candidate)
- `…/impl/W6_validator/tests/` (test_validator.py adapted + 5 new delta files; fixtures/ 56 files incl. 2 genuine exporter reports + 2 generators)
- `…/impl/W6_validator/docs/` (DEPENDENCY_MANIFEST.md, TOOL_HOME_PROPOSAL.md, USAGE.md)
- `…/impl/W6_validator/receipts/` (freeze_sha256, baseline_71, failing_first/ ×10, test_run_full, cli_smoke, integrity_and_hashes, tools_pycache_incident, worktree_concurrent_activity)
