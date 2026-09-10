# VERIFIER-REPAIR-02

## Core increment — 2026-09-10

STATEMENT/PREDICTION/FALSIFIER recorded in PREREGISTRATION.md before edits.
Built from cf275281, in registered slot 1, generation 1, epoch 2.
Muse's isolated candidate supplied the initial duplicate/unknown/nonfinite
diagnosis and seven counterexamples; independent Codex review found four
remaining false-PASS variants and a separate sparse-column failure.

Core implementation admits complete finite numeric tokens, validates structured
rod/rope/theta fields, retains duplicate verdict rows, distinguishes unknown
names from known-but-undecidable rules, and uses one per-file policy in both
CLI modes. Invalid inputs fail before recomputation. Explicit multi-file mode
now preserves other reports when a file raises. No physics equation or
comparison tolerance changed. Known incomplete rules remain UNCHECKED; this
is not a completeness certificate for arbitrary LightEngine log families.

Tests on Windows CPython 3.14.3:
- Baseline: 23 original tests pass; 34 new regressions fail, 5 compatibility
  checks pass (before.txt, combined 34 failed / 28 passed).
- First core: 62/62 pass (core_after.txt).
- Structured-field extension: 18 new failures before correction
  (structured_before.txt); complete core: 80/80 pass (core_final.txt).
- Five valid committed fixtures preserve their exact stdout bytes against the
  pre-edit hashes in baseline.json. Hashes are of Windows subprocess bytes.
- git diff --check passes. No GPU/runtime/DYAD or performance claim.

Exact targeted command:
`python -m pytest tools/test_verify_run.py tools/test_verify_run_integrity.py -q`

Failed runs are retained; no expected numerical threshold was changed. The
single old EXTRA/UNCHECKED assertion now expects UNKNOWN, with new CLI tests
also requiring exit 1. Missing columns remain a separately preregistered S1
increment; core catches its exception as ERROR without claiming schema validation.

## Recovery and workspace safety

Alan confirmed Codex is the sole active agent and requested continuation.
The existing bootstrap restarted the reconciled controller on its original DB
and credentials, PID 34084. Trusted enrollment issued a distinct Codex session;
supervisor qualification cited the independently executed 78/78 Windows fleet
suite and verifier review. Prior sessions were revoked under Alan's current
instruction, not elapsed-time inference; controller elected Codex at epoch 2.
Original snapshots and transitions remain under
E:/ChimeraWork/control/snapshots/codex-recovery-20260910 and in controller events.
No credentials are included here. Elastic publication remains RECOVERY_HOLD
with its committed source at 302da837 preserved in the operator checkout.

Task verifier-repair-02 was claimed for slot1, generation1. Provisioned via
documented --no-checkout + sparse exclusions because provision_slot.py create
would check out protected build artifacts. Its verify command passed; protected
engine/build path does not exist in slot1. No shared operator file was changed
except new quarantined recovery script .tmp/codex_recover_20260910.py.
The controller still runs original source, not PR11; PR11 deployment remains
separate from its independently passing Windows suite.

## S1 — sparse-column increment

Preregistered separately above; implemented after core commit 6ca08bba.
The union of observed numeric and structured sample columns defines the
per-file schema. Each sample must contain these columns. This catches sparse
first rows as well as later omissions, while intentionally minimal uniform
logs remain legal. Direct recomputation also refuses parsed integrity errors.
No missing sample is synthesized or zero-filled to make a metric pass.

Before S1: 18 sparse placement regressions fail, one minimal-schema control
passes (sparse_before.txt). After S1: all 99 combined tests pass. Raw final:
final_tests.txt, 99 passed in 5.42 s, Windows CPython 3.14.3. Sparse sample
positions first/middle/last cross bad-file positions first/middle/last and both
CLI modes. Each must report MISSING_COLUMN, include tip_to_drop, retain all
three file reports and exit 1 without traceback.

Compatibility: baseline_lf.json adds a portable LF oracle derived from the
immutable cf275281 source, with the original Windows byte hashes checked again
first. Windows tests retain raw-byte checks; only native line-ending conversion
is normalized for the additional portable check. Original baseline.json and
all failed evidence are unchanged. Linux execution is not claimed here.

Review limits: the schema detects inconsistent observed columns, not a complete
schema for every log family. A column absent from every sample is still governed
by the existing supported/UNCHECKED rule behavior. Unsupported physical verdicts
are UNKNOWN and fail. Skipped known rules remain UNCHECKED by existing policy.
No universal malformed-input or physics-verification completeness is claimed.

Independent prior fleet review evidence is retained as windows_fleet_pr11.txt:
78/78 Windows tests at 8bf8f643, including stop/restart; it does not certify
external model-client retry handling or deploy the candidate.

## Independent review correction — 2026-09-10

A separate read-only review helper found two false-PASS cases at fe27095d:
`(z) FROBNICATE PASS` was ignored, and `(i) HOLD: BOGUS` became UNCHECKED with
exit 0. The original 99-test suite still passed during that review. These
findings narrow the earlier claim; the original passing evidence is retained.

Controller review was reopened at claim generation 2. Preregistered syntax
and status regressions failed 16/16 before correction (review_before.txt).
Result-shaped lines outside the definition block now fail when their syntax
is invalid. A status must match a complete supported token before a verdict
can reach the known-but-undecidable UNCHECKED path. Unknown rule diagnostics
are retained even when their status is malformed.

After correction: `python -m pytest tools/test_verify_run.py
tools/test_verify_run_integrity.py -q` passed **115/115**, Windows CPython
3.14.3, 6.80 s (review_after.txt). This includes five original valid output
oracles. `git diff --check` passed. No physics formulas or tolerances changed.
The malformed-line detector covers result-shaped parenthesized identifiers;
this remains bounded log admission, not an arbitrary-text grammar certificate.

Follow-up review reproduced missing separator/closing-parenthesis prefixes;
four new CLI-mode regressions failed (review_prefix_before.txt). An overly
broad opening-parenthesis detector then rejected a legitimate `(and ... )`
narrative in the v3 control fixture: four full-suite failures retained in
review_final.txt. No assertion was relaxed. The detector now distinguishes
closed identifier prefixes or a single identifier followed by an uppercase
rule name from that narrative. Final correction: **119/119** pass in 7.33 s,
review_corrected.txt, including all five unchanged valid stdout oracles.
