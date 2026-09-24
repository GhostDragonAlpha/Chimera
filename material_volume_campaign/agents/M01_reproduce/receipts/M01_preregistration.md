# M01 preregistration — independent reproduction of frozen `1af0bbde`

Written and frozen BEFORE any proof-suite execution (timestamp of file creation
precedes all run receipts in `receipts/`). Agent M01; date 2026-09-24.

## Statement

The frozen revision `1af0bbde` body-export proof battery (SI 5/5, FC 8/8,
verify 7/7; 59 leaf identities + 7 verification identities = 66) passes TODAY,
from a fresh independent extraction of the exact git blobs, on a fresh
interpreter, with byte-identical (modulo unittest's duration string) output
across repeated runs.

## Environment (declared before runs)

- OS: Windows 10.0.26200 x64; CPU-only; no GPU, no browsers.
- Python 3.14.3 (MSC 1944), numpy 2.2.6. Author's interpreter version unknown
  (not recorded in the receipt) — float behavior is IEEE-754 binary64
  regardless; any count/count disagreement is a finding, not an excuse.
- Extraction method: `git show 1af0bbde:tools/<file>` (raw blob bytes, LF
  canonical; immune to core.autocrlf=true). 27 files extracted flat into
  `work/tools/`; each verified BYTE-EXACT against `git cat-file blob` sha256.
- `PYTHONDONTWRITEBYTECODE=1` on every invocation.
- Measured pre-run diagnostic (declared so the branch is pre-registered, not
  discovered mid-run): this interpreter writes `\r\n` to piped stdout; the
  frozen `material_volume_body_export_example_report.json` blob is LF-authored
  (0 CRLF, 1 LF, 5472 bytes).

## Expectations (frozen before execution)

E1. `material_volume_shared_interface_proof.py`: exit 0, `Ran 5 tests`, OK.
E2. `material_volume_frame_composition_proof.py`: exit 0, `Ran 8 tests`, OK.
E3. `material_volume_export_proof_verify.py`: exit 0, `Ran 7 tests`, OK, and
    its nested leaf runs report 17/21/8/5/8.
E4. Standalone legacy suites: `Ran 17` / `Ran 21` / `Ran 8`, all OK, exit 0.
E5. Observed exporter values equal the frozen decimal literals in the two
    preregistrations exactly where the proofs use rationals; tolerance TOL
    1e-12 absolute (the suites enforce this internally). Expected max deltas
    from the results doc: ≤ 9.44e-16 (I do not require reproducing those
    exact deltas bit-for-bit across interpreters, only ≤ 1e-12; deltas are
    recorded, not gated).
E6. Determinism: two runs of each script produce identical exit codes,
    identical `Ran N` counts, identical verdict lines, and identical stdout
    after normalizing the sole variant token `in <float>s` (unittest wall
    time). The CLI byte-identicality asserted inside verify (out1 == out2)
    must hold verbatim.
E7. Derivation script `material_volume_export_proof_prereg_derivation.py`
    exits 0 (H == Q == R2 three-way cross-check within 1e-12; re-check of the
    C-0 receipt).
E8. My own from-scratch Fraction re-derivation of the SI/FC expectations
    (written independently by M01, in `work/m01_independent_derivation.py`)
    agrees with every frozen literal in the two preregistrations within 1e-12.

## Environment-sensitivity branch (pre-declared, not a surprise)

HYP (measured basis above): in Run-Set A (raw-blob LF extraction),
`test_cli_determinism_and_saved_example_bytes` fails at `assertEqual(out1,
saved)` — CLI emits trailing `\r\n` (Windows text-mode pipe), saved blob has
`\n` — a 1-byte trailing-newline difference, all JSON content equal.
- If verify instead passes 7/7 in Run-Set A: HYP is wrong; recorded; no
  content concern.
- If verify fails exactly as HYP predicts: Run-Set B (checkout-equivalent:
  same blobs materialized with CRLF, as core.autocrlf=true does on checkout)
  must reproduce the author's reported 7/7. Run-Set B 7/7 + Run-Set A 6/7
  together CONFIRM: the reported counts are real and reproduce in the author's
  materialization; the battery's saved-example byte-compare is
  checkout-materialization dependent (M-1a family, now inside a test
  assertion — an M01 finding candidate, pre-declared here).
- Any OTHER failure mode (different test, different assertion, count
  mismatch) is a reproduction failure, preserved verbatim.

## Falsifiers

- F-M01-1: any `Ran N` count mismatch vs (5, 8, 7, 17, 21, 8).
- F-M01-2: any test failure in Run-Set B, or in Run-Set A outside the exact
  HYP branch (wrong test, wrong assertion, non-newline byte difference).
- F-M01-3: non-determinism across the two runs of any script (exit code,
  count, verdict, or normalized stdout).
- F-M01-4: observed exporter values deviating from frozen literals by > 1e-12.
- F-M01-5: my independent derivation disagreeing with any frozen literal by
  > 1e-12 (this falsifies the FROZEN TABLES, not just the code — a stronger
  check than re-running the author's own oracle).
- F-M01-6: derivation script exits nonzero.

## Stop rule

Two clean attempts per script (Run-Set A and Run-Set B constitute the two
attempts where materialization is the only difference). Failures preserved
verbatim in `receipts/`. After two attempts per script, verdicts are recorded
as measured; no third attempt, no tuning.

## Independence characteristics (declared)

Different author (M01 session; not glm53-lead-02/Codebuff), no shared session
state, fresh directory extraction from git objects (never a checkout of the
author's working tree), fresh interpreter processes. Shared: same machine,
same git object store (that is the point — identity is pinned by blob OIDs),
same numpy build. Authorial-correlation risk in the H/Q oracles is addressed
by E8/F-M01-5 (my own derivation) and by the audit, not assumed away.
