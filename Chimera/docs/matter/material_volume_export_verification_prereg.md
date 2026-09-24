# Preregistration — export verification pass (V1–V3)

**Status: frozen and committed before any check below executes.** Scope:
verification of the export-proof package at exact revision `1af0bbde`, run in
an isolated checkout (worktree, dedicated branch) because the shared branch
moved mid-session. This pass changes **no** fixture, frozen expectation,
tolerance, or acceptance criterion of the export proofs.

**Independence disclosure (binding on all outputs of this pass).** Subagent
deployment is unavailable in this session. This pass is executed by the same
author as the code under test. It is **not** independent review, and no output
of this pass may be cited as such. Independent verification remains OPEN; a
reviewer brief accompanies the receipt.

**Preserved record.** Earlier failures and corrections stand as recorded in
`material_volume_export_proof_results.md`: C-0 (pre-freeze derivation
correction), C-1 (saved-example serialization regeneration, content
unchanged), C-2 (proof comparator labels), C-3 (audit allowlist). The open
reporting discrepancy — "59 leaf" vs "66 leaf tests" for the same final
receipt — is adjudicated by check V2 below against the actual test inventory;
it is a reporting error in the earlier handoff message, not a test defect.

## New checks (frozen)

| id | check | method | acceptance criterion | falsifier |
|---|---|---|---|---|
| V1 | Battery reproduction | run all six suites from the isolated checkout of `1af0bbde` (five leaf suites + verification suite) | every suite green with counts 17 / 21 / 8 / 5 / 8 / 7 as reported | V1-F: any non-green run or count mismatch → regression finding, preserved verbatim |
| V2 | Unique-test inventory vs repeated executions | enumerate every test identity as (module, qualified name) via unittest discovery without relying on run logs; keep a separate ledger of repeated executions (the verification suite re-executes the five leaf suites as nested subprocesses) | unique identities = 59 leaf + 7 verification = 66 total; one full-battery invocation executes 7 verification cases plus 59 nested leaf cases (66 case executions), while the verification runner reports only `Ran 7 tests` | V2-F: any enumerated count differing from 17 / 21 / 8 / 5 / 8 / 7 → reporting-error finding; the 59/66 wording is resolved only by this enumeration |
| V3 | Full artifact hash manifest | SHA-256 of every lane file in the isolated checkout; compare the 14 previously reported hashes field-by-field | all 14 previously reported hashes match exactly; complete manifest recorded in the receipt | V3-F: any hash mismatch → artifact-drift finding |

## Untested-assertion rule

This pass also freezes the rule that any assertion not exercised by an
existing test remains **untested** — enumeration of such assertions is
reporting only and never converts them into tested claims.

No fixtures, expectations, tolerances, or acceptance criteria are altered.
Failures found are preserved as observed before any classification.
