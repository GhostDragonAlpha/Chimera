# Export verification receipt (single receipt)

**Verified revision:** `1af0bbde` = `1af0bbdee68d6ddfdd02bf9bd948f7b22f914d56`
(export proofs as previously reported). Verification executed in an isolated
checkout (worktree `_wt_export_verification`, dedicated branch
`material-volume-export-20260924`) because the shared branch moved mid-session
(to `02da40be`). New checks V1–V3 were preregistered and frozen first
(`material_volume_export_verification_prereg.md`, commit `f2bcac88`).

## Agent assignments

**Subagent deployment unavailable.** This session has no delegation tool.
Actual assignments: **none** — zero subagents deployed. The three requested
briefs were **not** executed as agents; per coordination rules no sequential
work is relabeled as agents and **no independent review is claimed**.

| requested brief | status | executed by |
|---|---|---|
| 1 — independent reproduction | executed as **author-side reproduction** (independent character OPEN) | session author, isolated checkout |
| 2 — proof audit | **NOT executed**; independent review OPEN (reviewer brief below) | — |
| 3 — consumption-contract draft | drafted as **proposal** (author-side), pending Astra decisions | session author |

## Reconciled test inventory (check V2 — adjudicates the 59/66 discrepancy)

Unique test identity = (module, qualified name), enumerated by unittest
discovery over the exact revision (no run-log parsing).

| module | unique identities | listing-sha256[:16] | class |
|---|---|---|---|
| material_volume_checks | 17 | 838d5bf26e7eb88d | leaf |
| material_volume_admission_checks | 21 | 3b230e19d1e95da9 | leaf |
| material_volume_body_export_checks | 8 | f02f7f4b4ff01133 | leaf |
| material_volume_shared_interface_proof | 5 | 3366b8c609c51d5d | leaf |
| material_volume_frame_composition_proof | 8 | 25507952edb39d51 | leaf |
| material_volume_export_proof_verify | 7 | 489fdeabce8367d6 | verification |
| **total** | **66** | | |

**Adjudication of 59/66 (reporting correction C-6).** Both figures appeared
for the same final receipt; the inventory settles it:

- **59** = leaf-suite identities (17+21+8+5+8). Correct when counting leaf
  suites only.
- **66** = all unique identities (59 leaf + 7 verification).
- The earlier phrase "66 leaf tests" was a **mislabel** of "66 unique tests,
  of which 59 are leaf". It was a reporting error in the handoff message and
  in one table cell of the results report (see ERRATUM there), not a test or
  count defect. Every enumerated count matches the reported suite counts.

**Repeated executions (separate ledger, scope: proof campaign since freeze
`d2c23741`).** One full-battery invocation runs the verification suite's 7
cases, of which two spawn the five leaf suites as **nested subprocesses** (59
case executions); the verification runner reports only `Ran 7 tests`. That
reporting asymmetry is the second half of the 59/66 confusion.

| suite | identities | standalone runs | nested runs | total case executions |
|---|---|---|---|---|
| material_volume_checks | 17 | 1 (R1) | 4 | 85 |
| material_volume_admission_checks | 21 | 1 (R1) | 4 | 105 |
| material_volume_body_export_checks | 8 | 1 (R1) | 4 | 40 |
| material_volume_shared_interface_proof | 5 | 2 (first failed C-2, re-run) | 4 | 30 |
| material_volume_frame_composition_proof | 8 | 1 (R3) | 4 | 40 |
| material_volume_export_proof_verify | 7 | 4 (first failed C-3, then R4, R5, V1) | — | 28 |
| **totals** | 66 | 10 | 20 | **328** |

V2 enumeration itself executes zero test cases (discovery only).

## Verification results

**V1 — battery reproduction: PASS.** One full-battery invocation in the
isolated checkout of `1af0bbde`: `Ran 7 tests ... OK`; nested leaf counts
asserted green as 17/21/8/5/8.

**V2 — unique-test inventory: PASS** (table above; counts match 17/21/8/5/8/7).

**V3 — full artifact hash manifest: falsifier V3-F FIRED (preserved).**
First execution reported all 14 recorded hashes mismatching in the isolated
checkout. Classification (finding M-1, two parts):

- **M-1a (substantive): recorded artifact hashes are checkout-materialization
  dependent.** The 14 values reported earlier were SHA-256 over *working-copy
  bytes*. Under `core.autocrlf=true`, the origin tree holds LF-authored bytes
  while a fresh checkout materializes CRLF (13 of 14 files; the example report
  is CRLF-authored and matched everywhere). Git blob OIDs are **identical**
  across checkouts, and LF-canonical content is byte-identical cross-tree for
  all 33 lane files (`CROSS_TREE_CANONICAL_EQUAL True`). So there is **no
  content drift** — but working-copy hashes are not portable identities.
  Portable identity for all future receipts: **git blob OID at the revision**
  (listing of 33 blobs at `1af0bbde`, sorted, digest
  `ee27dcd22aedac909984650dcc69f02ea8d66f4eea4bfd96d00ce29604f048a4`)
  plus **SHA-256 over LF-canonical bytes**.
- **M-1b (pass-internal defect, corrective action C-5):** the V3 comparison
  script contained a transcription typo in one expected value (example report,
  one hex digit dropped). With the corrected value it matches the recorded
  hash in every form.

V3 recheck after C-5 (no frozen criterion altered): recorded == origin-tree
working bytes for **14/14**; recorded == canonical form for **14/14**;
recorded == fresh-checkout working bytes for **1/14** (CRLF-authored example
report) — consistent with M-1a. The preregistered acceptance ("the 14
previously reported hashes match exactly **in the isolated checkout**") is
therefore **not met as worded**; V3-F remains on record and is not rescinded.
The canonical manifest below supersedes working-copy hashes for identity.

### Canonical artifact manifest (33 files at 1af0bbde, LF-canonical SHA-256)

Key artifacts (full 33-row manifest produced in the run log; cross-tree
equality verified for every row):

| artifact | canonical sha256 (first 16) |
|---|---|
| tools/material_volume_export_proof_prereg_derivation.py | 15a42e3d21357350 |
| tools/material_volume_shared_interface_proof.py | 844170e92bd4cf82 |
| tools/material_volume_frame_composition_proof.py | a5d762daefb136a0 |
| tools/material_volume_export_proof_verify.py | 282bc52bfa997c6c |
| tools/material_volume_body_export_example_report.json | 5485c8c4fe73d679 |
| Chimera/docs/matter/material_volume_export_proof_results.md | d190eae0791277d1 |
| Chimera/docs/matter/material_volume_export_proof_prereg_shared_interface.md | 546c943d585cab6b |
| Chimera/docs/matter/material_volume_export_proof_prereg_frame_composition.md | e5bf32fd94dcfd7f |

Note: the example report's canonical (LF) hash `5485c8c4…` differs from its
earlier working-copy hash `d71f7621…` (CRLF bytes) — one file, two lawful
byte forms; M-1a in a nutshell.

## Preserved corrections and failures ledger

| id | record |
|---|---|
| C-0 | pre-freeze derivation correction (FC combined inertia double-count) — preserved in preregistration 2/2 |
| C-1 | saved-example serialization regenerated as canonical CLI bytes; content unchanged (verified json-equal) |
| C-2 | SI proof comparator label mismatch; labels aligned |
| C-3 | verification audit allowlist omitted `__future__` |
| C-5 | V3 comparison-script transcription typo (this pass) |
| C-6 | reporting correction: "66 leaf tests" mislabel, adjudicated by V2 (this pass) |
| V3-F | fired falsifier, preserved verbatim above (M-1) |

C-1/C-2/C-3 acceptance-criteria adjudication is **open reviewer work** (not
claimed here): see brief below.

## Untested-assertion inventory (reporting only; these remain UNTESTED)

| id | assertion not covered by any test at 1af0bbde |
|---|---|
| U1 | bodies owning **more than one** cell (multi-cell aggregation, mixed-material provenance consistency under aggregation) |
| U2 | `scale_to_m != 1.0` input-scaling path in the exporter (fixtures use 1.0) |
| U3 | multi-face interfaces (area sums over several shared faces; >2 regions meeting) |
| U4 | numerical stress: large coordinates, near-degenerate tets, extreme density ratios |
| U5 | uniform-scale covariance of the export report (mass ∝ λ³, inertia ∝ λ⁵ at exporter level; only compiler-level is tested) |
| U6 | cell-reorder / vertex-renumber invariance of the **export report** (admission-report level is tested; export-report level is not) |
| U7 | reader behavior on `blocked` / `refused` reports in the integrated verification (legacy tests cover `unsupported`) |
| U8 | cross-report composition by consumers (forbidden silently by contract CON-3/CON-9; no test enforces consumer behavior) |
| U9 | consumption-contract clauses themselves (no consumer exists) |
| U10 | anything beyond the two synthetic coupons: no anatomical, mechanical, or dynamics claim is tested anywhere |

## Open reviewer brief (independent proof audit — NOT executed)

For a reviewer with independent provenance (different author/tooling):

1. Independently reproduce the battery from `1af0bbde` and this receipt's
   inventory; compare against the tables above.
2. Adjudicate **mathematical independence beyond import separation**: H
   (hand rationals) and Q (Hammer–Stroud) are algebraically independent of
   the exporter's moment path and of each other's algebra, but **both were
   written by the same author as the exporter** — correlated authorial error
   is the residual risk no in-repo check removes. Check the fixture semantics
   (especially the proposals→regions→materials mapping) independently.
3. Check that C-1/C-2/C-3 preserved the frozen acceptance criteria (diff the
   corrections against the two preregistrations; confirm no fixture,
   expectation, tolerance, or acceptance criterion changed).
4. Re-derive the SI/FC analytic expectations from scratch and compare to the
   frozen tables.
5. Treat every U1–U10 row above as untested unless separately evidenced.

Until that review exists, the correct claim remains: **export arithmetic
verified on the tested coupons by author-executed checks; independent
verification OPEN.**
