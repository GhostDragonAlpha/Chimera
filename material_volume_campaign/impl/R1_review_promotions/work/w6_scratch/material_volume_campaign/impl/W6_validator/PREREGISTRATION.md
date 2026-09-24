# W6 PREREGISTRATION — reconciliation of the M10 static consumption validator with decided contract v1.0, and promotion preparation

Frozen: 2026-09-24, BEFORE any edit to the staged validator copy. The staged copy
(`rigid_body_mass_consumption_validator.py`) is byte-identical to
`agents/M10_validator/rigid_body_mass_consumption_validator.py`
(sha256 `94c2ee772c4a15db0966fcf963ed13fe2fcb9987f45c5897f8072a62f636f5dd`); its
frozen test suite passed 71/71 before this file was written. This file's SHA-256 is
recorded in `receipts/freeze_sha256.txt` before the first edit. Any change after the
freeze must be an appended amendment, never an edit.

## Rule-0 membrane

- **STATEMENT.** The M10 validator's five strictest-reading spots (decision requests
  D1–D5) were written against the v0.9 proposal; contract v1.0 has since DECIDED all
  five. Reconciling the validator to the decided readings changes only what the
  decisions actually changed — the decided D2 diagnostic-display duty (preserve
  omitted bodies + unassigned cells on `partial`), the decided D3 read-only
  CON-16 verification aggregation (separate from validation, explicit frames,
  disjoint ownership, never collapsing bodies), and the three separately-decided
  items MV-O1 (hash-scope documentation + separate full-report identity), M06-H04
  (exit classes 0/2/1), MV-B3-1 (summary projection refused by name) — while the
  report-side rejections (partial-assembly rejection, source-effective exclusion,
  flat v1 frames, static-only use) stay exactly as approved.
- **PREDICTION (not yet measured).** (1) The frozen reconciliation table below
  requires NO rule change for D1/D4/D5 (strictest reading = decided reading, quoted).
  (2) After the five preregistered deltas are applied failing-first, the adapted
  original suite plus the new tests all pass; (3) the original M10 directory is
  byte-untouched (`git status --porcelain` on it stays empty); (4) every behavior
  delta has a captured failing-first receipt.
- **FALSIFIER (named before the run).** Falsified if: any D1/D4/D5 rule turns out to
  need a code delta that contradicts its "NO-CHANGE" row; any new test passes before
  its delta is implemented (not failing-first); the adapted suite or new tests fail
  at the end; the CON-16 aggregation collapses bodies, infers joints, regroups at
  runtime, mutates the input report, or emits anything other than an in-memory
  verification artifact; a blocked-body hash is ever described as a full-report
  hash; the original M10 artifacts change.

## Part 1 — THE RECONCILIATION TABLE (frozen)

Contract = the MAIN checkout's
`E:/PythonChimera/Chimera/docs/matter/rigid_body_mass_export_consumption_contract_v1_proposal.md`
(v1.0, D1–D5 decided 2026-09-24 — READ-ONLY). NOT the worktree's v0.9 copy.
M10 side quoted from `agents/M10_validator/PREREGISTRATION.md` § DECISION REQUESTS
and the validator it froze. "Spot" = where M10 asked Astra to decide; "decided
reading" = contract §5 as issued.

### Spot D1 — readiness promotion (M10: R12)

- **M10 strictest spot (PREREGISTRATION § DECISION REQUESTS):** "D1 readiness
  promotion → enforced by R12: any readiness claim anywhere = REJECT; no promotion
  path exists in this validator."
- **Decided v1.0 reading (§5 D1, as issued):** "Approve the contract for **static
  inspection and validation only**. Exporter success cannot promote a body to
  dynamics-ready. Runtime binding requires a separate Astra-approved qualification
  gate." Operative effect: "CON-2/CON-14 stand: no readiness-promotion authority
  exists in v1; the claim class stays closed."
- **Verdict: NO-CHANGE.** R12 (recursive claim scan, exact-false root flag) implements
  precisely the decided closed claim class; D1 decided adds no relaxation a static
  validator must express. Delta: framing only — the verdict's `decision_requests`
  entries become `decision_records` with `"decided": true` and the decided reading
  quoted (they are no longer requests).

### Spot D2 — `partial` policy (M10: R2/R14)

- **M10 strictest spot:** "D2 `partial` policy → enforced by R2/R14: `partial` (and
  any unassigned cell) = REJECT always; no explicit-subset path exists."
- **Decided v1.0 reading (§5 D2, as issued):** "**Reject `partial` reports for
  assembly.** Diagnostic tools may inspect exported bodies only while explicitly
  displaying omitted bodies and unassigned cells. No subset-binding exception yet."
  Operative effect: "CON-3 amended: subset consumption is not permitted (the earlier
  subset-binding reading is superseded); diagnostics must explicitly display omitted
  bodies and unassigned cells." §2 `partial` row: "**REJECT for assembly (D2),
  including any subset binding.** Diagnostic tools may inspect exported bodies only
  while explicitly displaying omitted bodies and unassigned cells (CON-3)".
- **Verdict: NO-CHANGE to the rejection; ONE delta to the diagnostic duty.** R2/R14's
  unconditional assembly rejection IS the decided reading (operator: "Keep …
  partial-assembly rejection"). But the decided clause "diagnostics must explicitly
  display omitted bodies and unassigned cells" binds any diagnostic that does
  inspect: M10's `preserved_diagnostics` echoes blocking/reason diagnostics for
  `blocked`/`refused` roots only, so a `partial` rejection does not explicitly
  display the unassigned cells or the omitted bodies. **Delta W6-D2:** extend
  `preserved_diagnostics` to `partial` roots (echo `unassigned_cell_ids`,
  `unassigned_cells`, `all_supplied_cells_assigned`, and per-body
  id/status/reason_codes — the omitted bodies and the gaps, by id, never merged into
  a body). Failing-first test on a genuine exporter-shaped `partial` report (root
  `partial` + unassigned cell + still-`exported` bodies, M07 C3 shape).

### Spot D3 — composite recombination (M10: R15)

- **M10 strictest spot:** "D3 composite recombination → enforced by R15: any
  recombination claim = REJECT; the validator computes no composite math."
- **Decided v1.0 reading (§5 D3, as issued):** "Allow **read-only aggregate
  calculations for verification**, with explicit frames and disjoint cell ownership.
  Do not collapse bodies, infer joints, or change runtime grouping." Operative
  effect: "new CON-16: verification-only aggregation math is permitted read-only;
  body collapse, joint inference, and runtime regrouping stay forbidden." CON-16:
  "Read-only aggregate calculations are permitted for **verification only**:
  composite mass, COM, and full inertia may be computed across exported bodies
  (e.g. parallel-axis aggregation) provided that (a) frames are stated explicitly,
  (b) cell ownership remains disjoint with one mass owner per cell taken verbatim
  from `cell_provenance`, (c) the result is recorded as a verification artifact with
  its own error accounting, and (d) no body record is collapsed, rewritten, or
  merged. Inferring joints, collapsing bodies, or changing runtime grouping is
  forbidden." Operator binding: "Separate read-only verification aggregation is
  allowed under CON-16 with explicit frames and disjoint ownership. It does not
  authorize collapsed export bodies, inferred joints, or runtime regrouping."
- **Verdict: NO-CHANGE to R15's report-field rejection; ONE delta adding the allowed
  aggregation shape.** A report that itself carries collapsed/recombined bodies
  (`composite_of`, …) is still rejected — CON-16's "no body record is collapsed,
  rewritten, or merged" and the operator's "does not authorize collapsed export
  bodies" keep R15 exactly as approved. The relaxation lives in a SEPARATE, explicit
  read-only verification entry point. **Delta W6-D3:** add
  `verify_con16_aggregate(report)` (CLI: `--verify-aggregate`) which:
  (a) runs only on reports whose full static validation ACCEPTs (CON-1/2: across
  **exported** bodies of a `complete` report), refusing otherwise with the failures
  named; (b) refuses non-disjoint cell ownership across bodies, naming the colliding
  cells and owners (CON-16b: one mass owner per cell, verbatim from
  `cell_provenance` — never inferred); (c) states frames explicitly: target frame =
  the report's domain frame (every body's `domain_from_body` target), convention
  quoted, per-body `frame_id`/rotation/origin recorded, parallel-axis contributions
  in domain coordinates (CON-10, never repaired — rotations are verified proper
  orthonormal as authored); (d) emits an in-memory verification artifact
  (`artifact_kind: "con16_verification_aggregate"`, `not_a_v1_body_record: true`)
  with its own error accounting (per-body orthonormality residuals, displacement
  norms, aggregation count); (e) never mutates, collapses, rewrites, or merges any
  body record, infers no joint, and changes no runtime grouping. The validation
  verdict itself gains no aggregate field (no silent expansion of the validation
  API). R15's failure detail is re-worded to cite decided D3 (text-only change).
  Failing-first tests: allowed shape (two-body example aggregate: mass 3.0 kg
  exactly; independently recomputed domain COM; single-body self-identity
  I_domain = R·I·Rᵀ), boundary refusals (non-ACCEPT report; overlapping cross-body
  cell ownership), and non-mutation (deep-equal before/after).

### Spot D4 — parent-frame lineage schema (M10: R16)

- **M10 strictest spot:** "D4 parent-frame lineage schema → enforced by R16: any
  lineage field / non-v1 version = REJECT."
- **Decided v1.0 reading (§5 D4, as issued):** "Retain v1's flat, pre-composed
  transforms. Defer v2." Operative effect: "CON-15 stands; the lineage schema
  (`chimera.rigid_body_cell_groups.v2`) stays deferred and is not designed here."
- **Verdict: NO-CHANGE.** R16 (flat-frame purity, lineage-field rejection, v1-only
  schema) is exactly the decided reading ("Keep … flat v1 frames"). Delta: the same
  `decision_records` reframing as D1.

### Spot D5 — source-effective mass transport (M10: R2/R11/R13)

- **M10 strictest spot:** "D5 source-effective mass transport → enforced by
  R2/R11/R13: `unsupported` status, non-`reconstructed_tissue_mass` authority, or
  any consumed source-payload flag = REJECT."
- **Decided v1.0 reading (§5 D5, as issued):** "Source-effective masses remain
  **unsupported**. No fallback or transport is authorized." Operative effect:
  "CON-5 stands for v1 with no substitution path; any future transport would need
  new authority design."
- **Verdict: NO-CHANGE.** R2's `unsupported` rejection, R11's
  `reconstructed_tissue_mass` authority pin, and R13's consumed-payload flag checks
  are exactly the decided reading (operator: "Keep … source-effective exclusion").
  Delta: the same `decision_records` reframing as D1.

## Part 2 — brief-mandated non-spot deltas (each itself a decided item)

### Delta W6-MVO1 (MV-O1, decided) — blocked-body hash scope + separate full-report identity

MV-O1 as issued: "Preserve the v1 producer's existing bytes and formula. Document
precisely which reduced object a blocked-body hash covers; never call it a
full-report hash. Verify full-report identity separately at the handoff. Add a
regression for the distinction." Evidence: M07 O1 — the exporter's `_blocked_group`
(`tools/material_volume_body_export.py`) hashes the REDUCED two-field object
`_canonical_hash({"reason_codes": admission_reason_codes, "decision":
admission_decision})` for `not_exported` bodies, while root and
exported/unsupported records bind `_canonical_hash(admission_report)` (the full
admission report document). The W6 validator adds to every verdict an
`admission_hash_scopes` block that (a) labels each body's
`admission_report_sha256` scope — `reduced_block_record` for `not_exported` bodies
(documenting the exact two-field object, with the exporter function named) vs
`admission_report_document` for the root and exported/unsupported records — and
never labels a reduced hash as a full-report hash; and (b) verifies full-report
identity SEPARATELY at the handoff as `full_report_identity` carrying the
contract §6 identities of the delivered report document itself:
`raw_file_sha256` (exact bytes) and `canonical_content_sha256` (CRLF/CR → LF,
§6 canonical-content rule, the report being a declared text artifact) — each named
by its §6 claim kind, never conflated with any `admission_report_sha256`.
Regression (failing-first) on a GENUINE exporter blocked report (generated by
`tools/material_volume_body_export.build_export_report` from the example inputs
with `tissue-B density_kg_m3: null`, M07 C4 construction, frozen as
`tests/fixtures/genuine_blocked_report.json`): the documented reduced object
recomputed from the fixture's own fields MUST equal each blocked body's recorded
hash (precision proof), the scope label MUST be `reduced_block_record`, the block
MUST contain the "never call it a full-report hash" statement, and
`full_report_identity.raw_file_sha256` MUST equal the file's byte hash and differ
from the body hashes (distinction measured). On the clean `complete` report all
scopes are `admission_report_document` and body hashes equal the root binding.

### Delta W6-EXIT (M06-H04, decided) — CLI exit classes 0/2/1

M06-H04 as issued: "For the promoted validation CLI, use 0 for accepted static
validation, 2 for named input/status refusal, 1 for unexpected internal failure."
M10's mapping was 0 = ACCEPT, 1 = REJECT, 2 = could-not-evaluate. The promoted CLI
implements: **0** = ACCEPT; **2** = every named refusal — a REJECT verdict (status
or rule refusal, reasons enumerated) and a named input refusal (unreadable/invalid
input, `could_not_evaluate: …` on stderr; argparse usage errors also exit 2); **1**
= unexpected internal failure only (an exception escaping the evaluation path is
caught, reported as `unexpected_internal_failure: …` on stderr, exit 1).
Compatibility note (goes in the module docstring, `--help` epilog, and docs): the
original M10 tool keeps 0/1/2 = accept/reject/unreadable as the campaign artifact;
the promoted tool carries the decided mapping. A `--version` action carries the
tool identity (name, promotion revision, exit-class contract, contract version).
Failing-first: the copied M10 exit test asserts REJECT→1, so it fails against the
new mapping until adapted; new tests pin ACCEPT→0, REJECT→2,
missing-file→2, injected-internal-failure→1.

### Delta W6-RAW (MV-B3-1, decided) — full raw report only; summary refused by name

MV-B3-1 as issued: "summarize_export_report is a display projection... Consumption
validation reads the full raw report... Do not silently expand or reinterpret the
existing summary API." The validator already reads only the raw report (R0 runs the
reader on the raw document and never trusts the summary; B3 measured 42 summary
DROPs). The promoted validator ADDS a named refusal for summary-shaped input: a
document matching v1's `schema_version` whose body records live under `bodies`
(the summary projection's key) instead of `body_groups` is refused with reason
`summary_projection_is_not_a_consumption_document`, citing MV-B3-1 — refused BY
NAME, not merely as a shape error. The summary API itself is not imported,
extended, or reinterpreted. Failing-first test: feed the genuine reader summary of
the accept fixture; assert refusal names the summary projection.

## Part 3 — frozen test plan

Baseline: staged M10 suite, 71/71 PASS (captured in `receipts/baseline_71.txt`)
after path adaptation only (fixtures moved under `tests/fixtures`; no assertion
changed). Then, in order, each delta's tests are added FIRST, run, and the failure
captured under `receipts/failing_first/`, then implemented, then green:

1. W6-RAW tests (`tests/test_w6_fullreport_mvb31.py`)
2. W6-MVO1 tests (`tests/test_w6_hash_scope_mvo1.py`)
3. W6-D2 preservation tests + `decision_records` reframing tests
   (`tests/test_w6_reconciled_records.py`)
4. W6-EXIT tests (`tests/test_w6_exit_classes.py`)
5. W6-D3 CON-16 tests (`tests/test_w6_con16_aggregate.py`)

The original `tests/test_validator.py` is adapted only where a preregistered delta
changes its assertions (exit codes in `test_cli_exit_codes`;
`decision_requests`→`decision_records` in `test_accept_clean_example_report`; the
source-scan test's composite-math ban is narrowed to runtime/dynamics symbols plus
the requirement that aggregation lives only in the CON-16 entry point and never in
`validate_report`); each adaptation names its delta in a comment.

CPU-only, no runtime wiring, no physics imports beyond numpy, no network. Writes
only under `material_volume_campaign/impl/W6_validator/`. The genuine blocked
fixture is generated ONCE by `tests/fixtures/make_genuine_blocked_fixture.py`
(importing the read-only tools modules with bytecode writing disabled) and frozen.

## Amendments

(none yet)
