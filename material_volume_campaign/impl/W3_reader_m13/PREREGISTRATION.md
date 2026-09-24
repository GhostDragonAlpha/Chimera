# W3 preregistration — frozen conversion table (written BEFORE any edit to the reader)

Frozen: 2026-09-24, against `tools/material_volume_body_export_reader.py` at HEAD
`d1c9933589a116f0a58ab73151e6da730bbd3718` (branch `material-volume-campaign-20260924`).
Reader file sha256 at freeze: see `receipts/freeze_hashes.txt` (written by the same
command that captured it; this file is never edited after freeze).

## RULE 0 — the theory of this repair

**STATEMENT.** Every uncaught numeric-coercion crash in the current reader originates at
exactly three coercion sites in `summarize_export_report` — the `np.asarray(..., dtype=np.float64)`
calls for `inertia_tensor_about_com.value` and `center_of_mass.value`, and the `float(...)`
call on `mass.value` — and converting `(TypeError, ValueError)` raised at exactly those three
sites into the reader's existing named-refusal type (`exporter.ExportInputError`, reason
`bad_export_report`, located detail) eliminates the B7-M13 escape class without changing a
single byte of any valid output and without changing the refusal (name AND detail) of any
input that already terminates in a named refusal.

**PREDICTION (not yet measured at freeze time).** After the edit: (a) all thirteen crash-class
fixtures below exit 2 on the CLI with exactly the frozen stderr line; (b) the four
already-named control fixtures produce byte-identical stderr to their pre-edit runs;
(c) sha256 of reader stdout on every golden valid report is identical pre/post edit;
(d) an injected `RuntimeError` at either coercion site still propagates uncaught (traceback,
exit 1); (e) the reader's own battery (`tools/material_volume_export_proof_verify.py`) stays
green; (f) M07's R1–R4 reader-probe outputs reproduce their receipts byte-for-byte.

**FALSIFIER (named before the run).** The repair is WRONG if any of: a golden valid-output
hash differs pre/post; an already-named control changes its refusal line; a crash fixture
still exits non-2 or exits 2 with an unfrozen message; an injected non-(ValueError, TypeError)
exception is converted or swallowed; the reader's own battery or M07 probes regress.
Any falsifier hit is reported, not tuned away.

## Scope law (no blanket catch)

Only the three named coercion expressions are wrapped; each catches exactly
`(TypeError, ValueError)` (the documented coercion-failure types of `np.asarray(..., dtype=...)`
and `float(...)`) and re-raises `exporter.ExportInputError` chained `from` the original
exception (mechanism preserved in in-process tracebacks; CLI output unchanged — `main()`
prints `reason: detail` and exits 2 exactly as before). No other exception type is caught
anywhere new. `RuntimeError`/`KeyError`/`AttributeError`/`MemoryError` etc. keep surfacing
as unexpected (guard-tested).

## The frozen conversion table

Refusal type for every row: `exporter.ExportInputError`; reason for every row:
`bad_export_report` (the reader's existing name for malformed report structure; the refusal
stays inside the reader's existing taxonomy — no new names are invented). `{label}` is the
reader's existing `body_groups[{index}]` prefix; the field path is the JSON key path under
that group. CLI output format is the reader's existing `f"{reason}: {detail}\n"` on stderr,
exit 2.

| id | site (current reader line) | malformed input shape (JSON class) | current behavior (measured pre-edit, numpy 2.2.6 / py 3.14.3) | frozen refusal detail |
|---|---|---|---|---|
| T1 | L52 `np.asarray(inertia["value"])` | ragged nested list — truncated row (B7-M13 exact) | uncaught `ValueError` (inhomogeneous shape), CLI exit 1 | `{label} mass_properties.inertia_tensor_about_com.value is malformed: not a rectangular numeric array` |
| T2 | L52 | ragged nested list — deeper ragged (list nested inside a row) | uncaught `ValueError` (inhomogeneous) | same as T1 |
| T3 | L52 | rectangular list with a non-numeric string entry | uncaught `ValueError` (could not convert string to float) | same as T1 |
| T4 | L52 | dict (whole value) | uncaught `TypeError` (float() argument … dict) | same as T1 |
| T5 | L52 | non-numeric string scalar | uncaught `ValueError` (could not convert) | same as T1 |
| T6 | L53 `np.asarray(center["value"])` | ragged list (nested list entry) | uncaught `ValueError` (inhomogeneous) | `{label} mass_properties.center_of_mass.value is malformed: not a numeric array of length 3` |
| T7 | L53 | list with a non-numeric string entry | uncaught `ValueError` (could not convert) | same as T6 |
| T8 | L53 | dict (whole value) | uncaught `TypeError` | same as T6 |
| T9 | L53 | non-numeric string scalar | uncaught `ValueError` | same as T6 |
| T10 | L57 `float(mass["value"])` | `null` | uncaught `TypeError` (NoneType) | `{label} mass_properties.mass.value is malformed: not a finite JSON number` |
| T11 | L57 | non-numeric string scalar | uncaught `ValueError` | same as T10 |
| T12 | L57 | list | uncaught `TypeError` | same as T10 |
| T13 | L57 | dict | uncaught `TypeError` | same as T10 |

Wording note: the details extend the reader's existing `{label} …` sentence pattern
(“has malformed mass fields”, “has invalid numeric properties”) with the precise field path
demanded by the brief. The mass wording reuses the exporter taxonomy's own number phrasing
(“a finite JSON number”, cf. `bad_number` in `tools/material_volume_body_export.py`), but the
reason stays `bad_export_report` — the reader validates report content, not export inputs.

## Already-named controls (must stay byte-identical — regression-tested, not converted)

| id | input shape | current (kept) behavior |
|---|---|---|
| K1 | wrong-shape rectangular tensor, e.g. 2x2 | `bad_export_report: body_groups[1] has invalid numeric properties`, exit 2 |
| K2 | center of shape (1,3) | same line, exit 2 |
| K3 | `null` entries inside an otherwise rectangular tensor (numpy maps to NaN) | `… has invalid numeric properties` via the isfinite guard, exit 2 |
| K4 | scalar/1x3/bool tensor values (shape != (3,3)) | `… has invalid numeric properties`, exit 2 |
| K5 | wrong-shape tensor AND non-convertible mass in the same body | `… has invalid numeric properties` — the mass coercion is lazy in the current short-circuit chain and must STAY lazy (precedence preserved exactly) |
| K6 | `blocked_group_has_mass` (M07-R5 shape) | unchanged (not touched by this repair) |

## Recorded observations — OUT of scope (coercion succeeds today; a refusal would be a behavior change beyond the narrow repair)

- O1: tensor entries that are numeric strings (`"1.5"`) are silently coerced by numpy and can
  pass every check (silent-acceptance, F1-class); same for `mass: "2.0"` and `mass: true`.
  Converting these would change exit-0 behavior — a decision request for the campaign, not
  part of the authorized narrow repair.
- O2: the strict loader (`read_json_file`) already refuses NaN/Infinity literals and 1e400
  overflow (`input_read_error`, exit 2) before the reader sees them (B7-M14), so nonfinite
  tensor entries are only reachable as NaN via numeric-string coercion (O1) — not converted here.

## Failing-first protocol

1. Generate the 13 crash fixtures + 6 controls as minimal diffs of
   `agents/B7_faultinjection/fixtures/valid_report.json` (mutations at `body_groups[1]`
   unless the case needs otherwise); M13's own regression uses B7's `corrupt_M13.json`
   fixture verbatim.
2. Capture each case's CURRENT reader behavior verbatim (CLI stderr + exit, in-process
   exception + traceback) into `receipts/before/` — BEFORE the edit.
3. Write the regression suite; run it against the UNFIXED reader; every T-row test must FAIL
   (that failure IS the M13 finding reproduced), every K-row test must PASS (already named),
   guards must PASS (nothing to convert unexpectedly yet), golden must PASS.
4. Edit the reader. Re-run: all green. Then the reader's own battery + M07 probe reproduction
   + golden hashes + integrity paste.
