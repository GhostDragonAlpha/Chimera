# W3b report — F-R2-3 repair: out-of-range JSON integers now refused by name

**Verdict: ACCEPTED.** All five acceptance items measured green. Falsifiers
F-W3b-1…4 did not fire. The prereg (`PREREGISTRATION.md`, sha256
`57a310e7080cc805a547313f94592a0cd1e8e73ba75e0188b565ac4d7fc27523`, frozen at
HEAD `1afb552a` before the edit, unchanged since — receipts `00_/01_`) was
written and hashed before the reader file was touched.

## What was done

`tools/material_volume_body_export_reader.py` — the only file changed
(git: 1 file, +13/−2; full diff receipt `20_edit_diff.txt`). Per the frozen
prereg, inside each of the two coercion helpers (`_as_float_array`,
`_as_number`) one clause was added:

```python
    except OverflowError as error:
        raise exporter.ExportInputError("bad_export_report", refusal) from error
```

plus the two helpers' docstrings amended to name OverflowError. No refusal
text, control flow, other exception class, or other file changed.

**Deviation from the brief's letter, preregistered before the edit:** the brief
said "add OverflowError to the two catch tuples". The literal tuple extension
`except (TypeError, ValueError, OverflowError)` contains W3's pinned substring
`except (TypeError, ValueError)` **0 times** (measured pre-edit; W3's
`test_reader_source_has_no_blanket_catch` asserts `source.count(...) == 2`),
and W3's test file is READ-ONLY for this task — so the single-tuple edit
provably breaks acceptance item (4). The prereg froze the disjoint-clause
shape instead: `OverflowError` derives from `ArithmeticError` and is disjoint
from `TypeError`/`ValueError`, so both shapes convert identical exception
sets at identical sites. Measured outcome: W3's suite is fully green,
substring count still 2, `except OverflowError` count exactly 2 (pinned by my
own source guard in my dir).

## Measured numbers

| Check | Pre-edit | Post-edit |
|---|---|---|
| W3b suite (`tests/test_w3b_overflow.py`, 8 tests) | **FAILED (failures=3, errors=2)**, exit 1 — receipt `10_before_failing_first.txt` | **8/8 OK**, exit 0 — `30_after_w3b_suite.txt` |
| W3 suite (`impl/W3_reader_m13/tests/`) | 11/11 OK, exit 0 (baseline, in-session) | **11/11 OK**, exit 0 — `32_after_w3_suite.txt` |
| Battery (`tools/material_volume_export_proof_verify.py`) | 8/8 OK, exit 0 (baseline, in-session) | **8/8 OK**, exit 0 — `33_after_battery.txt` |
| v1 mass 10**400 CLI | exit 1, 0-byte stdout, `OverflowError` traceback — `11_before_cli_traceback_v1_mass.txt` (verbatim) | exit 2, stderr `bad_export_report: body_groups[1] mass_properties.mass.value is malformed: not a finite JSON number` — `31_after_refusal_lines.txt` |
| v2 tensor 10**400 CLI | exit 1, 0-byte stdout, `OverflowError` traceback — `11_before_cli_traceback_v2_tensor.txt` (verbatim) | exit 2, stderr `bad_export_report: body_groups[1] mass_properties.inertia_tensor_about_com.value is malformed: not a rectangular numeric array` |
| Valid control stdout | 1643 bytes, sha256 `3a18ed3335df7f6a01aaa8b71161d6a9567efa629cea415ef90e23bc5777fe97` (`02_preedit_control_stdout_hash.txt`) | **identical** (byte count + hash, `31_after_refusal_lines.txt`) |

Pre-edit crash sites, verbatim from the preserved tracebacks: reader line 43
`_as_number` → `float(value)` (v1) and line 35 `_as_float_array` →
`np.asarray(value, dtype=np.float64)` (v2), both
`OverflowError: int too large to convert to float` — matching R2's A/B
receipts (`40_/41_r2_v1_mass_hugeint_*`), i.e. pre-existing, non-regression.

## Falsifier ledger

| Falsifier | Status |
|---|---|
| F-W3b-1 (pre-edit exit 0 or non-OverflowError class) | not fired — both fixtures crashed with bare `OverflowError`, exit 1 |
| F-W3b-2 (any W3/battery/golden red post-edit) | not fired — 11/11, 8/8, control hash identical |
| F-W3b-3 (over-broad conversion; injected RuntimeError/KeyError swallowed) | not fired — guard tests green post-edit |
| F-W3b-4 (valid-output bytes changed) | not fired — sha256 `3a18ed33…` unchanged |

## Acceptance

1. **Frozen prereg** — `PREREGISTRATION.md`, hashed before the edit, unchanged (receipt `00_`).
2. **Before-tracebacks preserved** — `receipts/11_before_cli_traceback_v1_mass.txt`, `..._v2_tensor.txt` (verbatim, with exit codes), plus the full failing unittest output `10_before_failing_first.txt`.
3. **Failing→passing demonstrated** — 5 of 8 tests red pre-edit (2 ERRORs = the escaping OverflowError, 2 CLI FAILs exit 1≠2, 1 source-pin FAIL), 8/8 green post-edit.
4. **W3 suite + battery green, goldens unchanged** — 11/11 OK and 8/8 OK post-edit (W3's own golden manifest tests, which hash stdout against the pre-W3 capture and B3/M07 historical receipts, all pass); my control's stdout hash byte-identical pre/post.
5. **Integrity** — `git status`: ` M tools/material_volume_body_export_reader.py` + `?? material_volume_campaign/impl/W3b_overflow/` only. R2/W3 evidence untouched (R2 fixtures read, not modified; my fixtures regenerated from the description into `tests/fixtures/`, single-diff property pinned by test).

## Files

- `E:/ChimeraWork/mvc-20260924/tools/material_volume_body_export_reader.py` — the repair
- `E:/ChimeraWork/mvc-20260924/material_volume_campaign/impl/W3b_overflow/PREREGISTRATION.md` — frozen prereg
- `E:/ChimeraWork/mvc-20260924/material_volume_campaign/impl/W3b_overflow/tests/test_w3b_overflow.py` — failing-first suite (now regression-green)
- `E:/ChimeraWork/mvc-20260924/material_volume_campaign/impl/W3b_overflow/tests/make_w3b_fixtures.py` + `tests/fixtures/w3b_v{0,1,2}_*.json` — regenerated fixtures
- `E:/ChimeraWork/mvc-20260924/material_volume_campaign/impl/W3b_overflow/receipts/` — 11 receipts (hashes, tracebacks, diff, all suite/battery runs)

Not committed (no commit requested). Stopping here per the brief: acceptance verdicted.
