# W3 report — narrowly-scoped current-reader repair for B7-M13

Agent: W3 · worktree `E:/ChimeraWork/mvc-20260924` (branch `material-volume-campaign-20260924`,
HEAD at session open `d1c9933589a116f0a58ab73151e6da730bbd3718`) · CPU-only · Python 3.14.3,
numpy 2.2.6 · brief verbatim: `brief.md` · frozen preregistration: `PREREGISTRATION.md`
(sha256 `09c4739797472160b7f0e2e2966509c180b9cccab6665cec0511f307c47bc8d0`, never edited after freeze).

**VERDICT: DONE — all six acceptance items green, falsifier HELD.**

## 1. What was done

The only `tools/` file edited: `tools/material_volume_body_export_reader.py`
(sha256 before `6b9890111a96491073761df688d5390c26611dd09784878bce76c4e3bdcc34ef` →
after `83b057391ab6d8e10352129a29d7903d15b4d59f2c7103e907d1f98069f274df`; +40/−4 lines).
The frozen audited revision `1af0bbde` and all extracted copies were never touched.

Three narrow conversion helpers were added and wired to exactly the three preregistered
coercion sites in `summarize_export_report`:

- `_as_float_array(value, refusal)` — catches `(TypeError, ValueError)` from
  `np.asarray(value, dtype=np.float64)` and re-raises `exporter.ExportInputError("bad_export_report", refusal)`
  chained `from` the original exception. Used for the inertia-tensor and center-of-mass sites.
- `_as_number(value, refusal)` — same shape for `float(...)` on `mass.value`, substituted at
  BOTH occurrences inside the existing short-circuit condition, so the evaluation order and
  laziness of the original chain are preserved exactly (see K5).
- Module docstring gains one sentence recording the refusal discipline. No other lines changed;
  `main()` untouched, so the public CLI contract (stdout canonical JSON / exit 0, stderr
  `"{reason}: {detail}\n"` / exit 2, unexpected exceptions crash with traceback / exit 1) is
  byte-preserved.

No blanket try/except: a static guard test asserts the source contains no `except:`,
`except Exception`, or `except BaseException`, and exactly two `except (TypeError, ValueError)`
clauses (the two helpers). Guard tests inject `RuntimeError` at the tensor coercion and at the
finite check and prove it still propagates uncaught, in-process and through `main()`.

## 2. Acceptance

**(1) Frozen conversion table** — `PREREGISTRATION.md` §"The frozen conversion table",
written and hashed BEFORE any edit: 13 crash-class input shapes (T1–T13: ragged truncated row =
B7-M13 exact, deep ragged, rectangular non-numeric string entry, dict value, non-numeric string
scalar — at both `np.asarray` sites; `null` / non-numeric string / list / dict mass — at the
`float` site), each mapped to its frozen refusal detail, plus 6 already-named controls (K1–K6)
and 2 out-of-scope observations (O1: numeric-string/bool silent coercions — a campaign decision
request, NOT converted because refusing them would change today's exit-0 behavior; O2: NaN/
Infinity/1e400 already refused by the strict loader per B7-M14).

**(2) Before-tracebacks preserved verbatim** — `receipts/before/` (30 cases: full stderr, exit,
stdout sha256 per case; `manifest.json` pins reader sha at capture). `receipts/before/b7_corrupt_m13.stderr.txt`
reproduces the M13 finding verbatim against the current reader: uncaught
`ValueError: setting an array element with a sequence. The requested array has an inhomogeneous
shape after 1 dimensions.` at reader line 52, `exit=1` — same numpy message as B7's
`missed_case_evidence.txt`.

**(3) Failing-then-passing** — `receipts/suite_BEFORE_fix.txt`: against the unedited reader the
suite ran 11 tests → FAILED (failures=24, errors=6): every T-row subtest failed (CLI demanded
exit 2 + frozen line; in-process demanded `ExportInputError`), and the no-blanket-catch static
guard failed (0 catches present) — while every K-row kept-refusal test, every unexpected-
exception guard, and all 3 golden tests ALREADY PASSED (the preservation baseline, proven
pre-edit). `receipts/suite_AFTER_fix.txt`: `Ran 11 tests ... OK` (exit 0).

**(4) Valid output byte-identical (hash proof)** — `work/capture.py` ran the reader over all 30
inputs before and after the edit; diffing `receipts/before/manifest.json` vs
`receipts/after/manifest.json`:
- All 8 valid reports: exit 0 and stdout sha256 IDENTICAL pre/post — B7 valid_report,
  `tools/material_volume_body_export_example_report.json`, B3's rotated `rotcoupon/report.json`,
  B3's shipped_example report, and M07's four genuine reports (C1 complete, C2 refused,
  C3 partial, C4 blocked). Zero stdout changes anywhere in the 30-case matrix.
- Independent anchors (not self-referential): reader stdout on B3's two reports is byte-equal
  to B3's historical `summary.json` receipts (2902 and 2707 bytes), and on M07's C1–C4 reports
  byte-equal to `probe-r{1,2,3,4}-reader.json` receipts.

**(5) Unexpected-exception guard proven** — `TestUnexpectedStillUnexpected` (3 dynamic tests,
green both pre- and post-fix): injected `RuntimeError` at the tensor `np.asarray` site and at
`math.isfinite` propagates uncaught from `summarize_export_report`, is not masked into a
refusal type, and propagates through `reader.main()`; plus the static no-blanket-catch source
guard (green post-fix).

**(6) Integrity** — paste of `git status --porcelain` (full worktree) at close:

```
 M tools/material_volume_body_export_reader.py
 M tools/material_volume_export_proof_verify.py
?? material_volume_campaign/impl/W1_source_verify/
?? material_volume_campaign/impl/W3_reader_m13/
?? material_volume_campaign/impl/W6_validator/
```

My writes are exactly `tools/material_volume_body_export_reader.py` (modified) and
`material_volume_campaign/impl/W3_reader_m13/` (untracked, mine). The `material_volume_export_proof_verify.py`
modification is NOT mine: it is the parallel M01-F1/W1 worker's append-style edit (labeled
"M01-F1 (2026-09-24, append-style)" in its own diff text; `W1_source_verify/` and `W6_validator/`
are sibling agents' untracked dirs), which landed in the shared worktree during this session —
this session opened with an empty porcelain on the same HEAD. The reader battery is green with
that append present (`Ran 8 tests ... OK`, twice).

## 3. Post-fix refusal lines (frozen; exit 2)

- `bad_export_report: body_groups[1] mass_properties.inertia_tensor_about_com.value is malformed: not a rectangular numeric array` (T1–T5 + B7's corrupt_M13.json)
- `bad_export_report: body_groups[1] mass_properties.center_of_mass.value is malformed: not a numeric array of length 3` (T6–T9)
- `bad_export_report: body_groups[1] mass_properties.mass.value is malformed: not a finite JSON number` (T10–T13)

Crash→refusal conversion measured on all 14 crash inputs (13 preregistered fixtures + B7's own
`corrupt_M13.json`): exit 1 (traceback) → exit 2 (named refusal), 14/14.
Kept-refusal byte-identity on all 8 exit-2 inputs (K1–K5 + M07's tampered R5 fixture + the two
B3 summary inputs): stderr sha256 identical pre/post, 8/8.

## 4. Re-runs

- W3 suite: `python tests/test_w3_reader_m13.py` → 11 tests OK (post), FAILED (failures=24,
  errors=6) pre — failing-first demonstrated.
- Reader's OWN battery: `python tools/material_volume_export_proof_verify.py` → exit 0,
  `Ran 8 tests ... OK` (receipts `own_battery_AFTER.txt`, `own_battery_AFTER_rerun.txt`); this
  internally reproduces the 17+21+8 legacy suites, 5+8 proof suites, CLI determinism, and the
  reader validation test.
- M07 reader probes on genuine reports: R1–R4 reproduce their receipts byte-for-byte (stdout
  equal, exit equal, stderr empty) and R5 reproduces `blocked_group_has_mass: body_groups[0] is
  not exported but includes properties` exit 2 with byte-equal stderr against
  `probe-r5-reader.stderr` — asserted in the suite (`test_m07_probe_receipts_reproduce_byte_for_byte`,
  `test_k6_m07_r5_blocked_group_refusal_unchanged`) and in the before/after capture diff.

## 5. Falsifier verdict (RULE 0)

HELD. All six predictions of the frozen theory measured true: (a) 14/14 crash inputs now exit 2
with exactly the frozen lines; (b) 8/8 already-named refusals byte-identical; (c) 8/8 golden
valid outputs sha256-identical (plus two independent historical receipt anchors); (d) injected
RuntimeError still propagates uncaught; (e) own battery green; (f) M07 probes byte-reproduce.
No falsifier fired; nothing was tuned away.

## 6. Artifacts

- `brief.md` — task brief, verbatim
- `PREREGISTRATION.md` — frozen conversion table + theory/falsifier (pre-edit hash in `receipts/freeze_hashes.txt`)
- `tests/test_w3_reader_m13.py` — 11 regressions (conversions, kept refusals, unexpected guards, goldens)
- `tests/fixtures/` — 18 generated fixtures (13 crash + 5 control), canonical JSON
- `work/make_fixtures.py`, `work/capture.py` — deterministic fixture generation; before/after behavior capture
- `receipts/before/`, `receipts/after/` — verbatim pre/post CLI behavior, 30 cases each
- `receipts/suite_BEFORE_fix.txt`, `receipts/suite_AFTER_fix.txt` — failing-first proof
- `receipts/own_battery_AFTER.txt`, `receipts/own_battery_AFTER_rerun.txt` — reader's own battery green
- `receipts/freeze_hashes.txt` — reader + preregistration sha256 at freeze
