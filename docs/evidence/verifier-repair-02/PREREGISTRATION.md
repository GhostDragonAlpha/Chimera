# VERIFIER-REPAIR-02 — before implementation, 2026-09-10

Owner codex-lead-20260910, leadership epoch 2, slot 1, claim generation 1.
Base cf27528166b7df1e20ddf474396624c8bf7f63a3. Verifier baseline blob
52b9052eefd42c66f4399be7ca7bf1da6d5290cc. Muse's candidate SHA256
d71562096ba1ee376097f083f0a7b616cce8698f275aeb177fbda1e680f32b60 is a reviewed
precursor, not accepted source. Its seven supplied single-file cases pass;
Codex review additionally found batch UNKNOWN/EMPTY and numeric prefix/overflow
false PASS. The original reports remain preserved in their existing locations.

STATEMENT: complete numeric-token admission and a common file-verification
pipeline reject malformed, duplicate, unknown and nonfinite input consistently
across single-file, explicit-list and --all modes, without modifying physics
recomputation equations or tolerances.

PREDICTION: five committed valid log stdout streams remain byte-identical and
exit 0. Every preregistered invalid case produces exit 1 and its named reason;
no traceback or swallowed following file. Unknown names remain UNKNOWN even if
printed skipped. Supported but undecidable rules remain explicitly UNCHECKED.

FALSIFIERS: any invalid case exits 0; any expected diagnostic absent; any valid
stdout byte changes; lost later file; any physics comparison/tolerance edit.
Empty directory and logs without verdicts fail for lack of evidence.

Derivation: success(files) = nonempty(files) AND all(success(file)). A file's
success requires samples, verdicts, no input integrity errors, and no UNKNOWN
or DISAGREE row. Parsing must consume a complete numeric token before units or
annotations; converting a syntactically numeric exponent may overflow, so
finiteness is tested after conversion. Duplicate identifiers must retain all
rows and fail instead of selecting one. These are logical requirements, with
no tuned numerical constants.

Tests: python -m pytest tools/test_verify_run.py tools/test_verify_run_integrity.py
First run new CLI regressions against unmodified source (retain failures), then
repair. Independent compatibility oracle: capture_baseline.py records stdout
hashes before any source edit using the five committed fixtures. All runs use
slot1, private tmp files and CPU only. No renderer/DYAD claim applies.

Separate increment S1 (preregistered, not silently folded into core patch):
STATEMENT: a file's observed numeric/structured telemetry columns define its
per-file sample schema; missing a column in any sample is insufficient evidence,
never an implicit zero or KeyError. PREDICTION: sparse samples in first/middle/
last positions produce MISSING_COLUMN and preserve other files in both modes;
uniform intentionally minimal fixtures continue passing. FALSIFIER: inconsistent
columns accepted, traceback, globally mandatory columns invented across families,
or valid fixture regression. Implement and record S1 in a separate commit.

Core review amendment before expanded tests: structured rod/rope/theta numeric
tokens must obey the same finite, complete-token policy as scalars. Prediction:
NaN/Inf/overflow in these fields yields NONFINITE; a truncated field, empty
generic numeric field, or invalid boolean yields MALFORMED. Falsifier: exit 0,
generic ERROR instead of the named cause, or valid-format output change.

## Independent review correction — generation 2

Read-only reviewer found two counterexamples at fe27095d: a missing-colon
verdict is ignored, and HOLD: BOGUS succeeds as UNCHECKED. Before correction:
STATEMENT: verdict-shaped lines outside the FALSIFIERS definition block must
have valid syntax and a complete supported status token before recomputation.
PREDICTION: missing colon, invalid identifiers, and unknown/truncated statuses
produce MALFORMED and exit 1 in both CLI modes, including known undecidable
rules. Valid fixture output and known skipped behavior remain unchanged.
FALSIFIER: any new case exits 0, any valid golden output changes, or a missing
physics prerequisite is invented to make a known rule computable. Unknown
rule names with a valid status remain UNKNOWN. Record failing tests first.

Follow-up before the second correction: the reviewer reproduced `(z)HOLD: PASS`
and `(z HOLD: PASS` disappearing. The same prediction/falsifier now explicitly
covers missing whitespace and a missing closing parenthesis in a result prefix.
