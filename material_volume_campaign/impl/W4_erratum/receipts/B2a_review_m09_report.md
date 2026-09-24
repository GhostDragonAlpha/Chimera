# B2a review report — independent review of the M09 diagnostic CLI

Reviewer: B2a · 2026-09-24 · worktree `E:/ChimeraWork/mvc-20260924`
(branch `material-volume-campaign-20260924`) · under review: commit `7701d8db`,
`material_volume_campaign/agents/M09_diagnostic/`

**Overall verdict: ACCEPT-WITH-NOTES.** Every claimed result reproduced exactly
by independent rerun; the U7 finding verified with my own fixtures; all three
M09 falsifiers (F1/F2/F3) clean under my runs. No blocking defect. I found
three minor defects, all requiring hostile (reader-accepted but
contract-violating) input and all display-path-only, plus one exit-code
collision and test-traceability drift — details below. I fixed nothing.

My check list was preregistered and frozen before execution:
`receipts/preregistration_checklist.md`. Receipts in `receipts/`; all my
fixtures/scripts in `work/`; the suite I ran is a SHA-256-verified verbatim
copy (`work/m09_copy/`), so I never wrote inside the M09 directory.

---

## Area 1 — CLAIM VERIFICATION: CLAIMS-VERIFIED

| M09 claim | My independent result | Evidence |
|---|---|---|
| 11/11 tests pass | 11/11 OK, 4 runs (3 x `unittest discover` + 1 verbose): `Ran 11 tests ... OK` every time | `receipts/b2a_suite_runs.log`, `b2a_suite_full.log` |
| ~3.6 s suite | 3.94-4.50 s on my runs — same magnitude, machine-load dependent | same logs |
| 415-file read-only proof | 415 files snapshotted (tools/ + Chimera/docs/matter, SHA-256 + st_mtime_ns); before/after ALL my runs: `added=0 removed=0 changed=0`, `before_after_identical=true` | `receipts/b2a_snapshot_before.json.txt`, `b2a_snapshot_after_diff.json`, `b2a_snapshot_final_diff.json` (tool: `work/snapshot.py`) |
| exit codes {0 accepted, 2 reader-rejected, 4 alarm} | On my own fixtures: complete/partial/blocked/unsupported/refused -> 0; malformed -> 2; exit 4 and exit 1 never observed on genuine inputs | `receipts/b2a_claims_receipt.txt` |
| readiness false in every output | All 12 human runs end `readiness: false`; all JSON payloads `"readiness": false` with every `readiness_claimed == False`. Violations found: NONE | `receipts/b2a_claims_receipt.txt` |
| fixtures generated via exporter's public `build_export_report` | Independently rebuilt: `exporter.canonical_json(build_export_report(manifest, partition, groups))` is byte-identical to the shipped example report (`True`); in-suite assertion exists (tests L74-78, runs in `setUpClass`) | `receipts/b2a_claims_receipt.txt`; C1.5 line in it |

The suite I ran was copied verbatim first — SHA-256 equality verified for
`material_volume_diagnostic.py`, `tests/test_material_volume_diagnostic.py`,
`run_suite.py` (`work/` copy step output: `VERBATIM ...` for all three).

## Area 2 — CODE REVIEW: CLAIMS-VERIFIED with 1 minor defect + notes

- **Public-API-only: VERIFIED.** The CLI touches exactly four reader/exporter
  members: `exporter.read_json_file` (L246), `exporter.ExportInputError`
  (L248), `reader.summarize_export_report` (L247), `reader.canonical_json`
  (L260). Zero underscore/private access (grep: none). No re-parsing of report
  internals to produce statuses: every `export_status` (root and per-body) is
  copied from the summary (L102-104, L140); the raw mapping is used only for
  the passthrough keys the frozen contract declares (`blocking_cell_ids`,
  `blocking_assignment_statuses`, `admission_reason_codes`, per-cell
  `unassigned_cells` rows, top-level `reason_codes`/`detail`) — L96-135,
  L152-156.
- **Write paths: VERIFIED none.** Only `sys.stdout.write`/`sys.stderr.write`
  in the CLI (grep). `sys.dont_write_bytecode = True` at L37, before any
  reader import (first import happens in `main` -> `load_reader`). My snapshot
  diff confirms empirically across all my runs.
- **Status invention: none found.** Synthesized display values, each judged:
  (a) `omitted` boolean (L106) — declared in the frozen contract; (b)
  `admission_status` null -> `"not_reported"` (L141-143) — declared in the
  frozen contract, and no collision: contract CON-13 mandates the real value
  be `validation_only_admissible`; (c) `units.add("kg")` (L117) — a display
  synthesis faithful to the summary's `mass_kg` semantics; note the reader
  itself renames `mass.value` to `mass_kg` without checking the raw unit, so a
  hostile non-kg raw unit would display as kg — that assumption is the
  READER's (preserved, not fixed; outside M09's read-only scope). (d)
  `frames`/`units` aggregate exported bodies only — consistent with the frozen
  contract's "summary data" and T11's `(none)` expectation.
- **Readiness can never display true at top level: VERIFIED.** JSON payload
  hard-codes `"readiness": False` (L258); human tail hard-codes
  `readiness: false` (L221); a summary carrying true would render honestly and
  fire the stderr alarm + exit 4 (L254-255, L264-267) — exactly the frozen
  contract.
- **Exit-code mapping: DEFECT (minor) — usage errors exit 2, colliding with
  the frozen `2 = reader rejected`.** The frozen preregistration says
  "other nonzero — usage errors (argparse)", but argparse's usage-error exit
  IS 2. Measured: no-args -> exit 2; `--bogus-flag` -> exit 2
  (`receipts/b2a_probes_receipt.txt`, P7). A wrapper keying on exit codes
  cannot distinguish "bad invocation" from "reader-rejected report" (stderr
  text does differ). Alarm-vs-rejection precedence is 4 before 2 (L264-269) —
  unreachable in practice since the reader hard-codes readiness False.
- **Note:** the CLI docstring lists `EXPORT_SCHEMA` as part of its interface,
  but the CLI never references it (only the tests do); the frozen invariant
  "schema_version must equal EXPORT_SCHEMA" holds by the reader's construction
  (summary hard-codes it, reader.py L93) rather than a CLI assertion. Harmless.
- **Note (see Area 4, P3b):** `diag.STATUSES` is defined but never used by CLI
  code (only in test T8), so an out-of-vocabulary per-body status is displayed
  verbatim with no flag.

## Area 3 — TEST QUALITY: GAP (real, honest coverage; traceability drift + 3 gaps)

T1-T8 and T10 map cleanly onto the preregistered plan with the preregistered
assertions (verified assertion by assertion). Fixture generation is exactly as
claimed: public `build_export_report` on mutated IN-MEMORY copies
(L42-65), per-fixture status asserts (L67-73), only the 2 malformed files
hand-written, authenticity assert present and running (L74-78). Honest extras:
T6 asserts rejected entries carry NO summary fields; T3/T4 lock the U7
observations with `assertNotIn`.

Gaps found:

1. **T9 drift:** preregistered T9 = SHA-256+mtime before/after proof; the
   implemented `test_t9` checks only `__pycache__` absence. The hash proof
   lives in `run_suite.py`, not in the unittest suite — running the suite
   alone does not prove F1. (run_suite.py does it and its receipt is
   genuine; I reproduced the proof independently. Traceability, not absence.)
2. **T11 drift:** preregistered T11 = "U7 record"; implemented `test_t11` =
   human grammar on blocked (not in the preregistered numbered plan). The U7
   record is covered by T3/T4 asserts + `run_suite.u7_reader_probe()` +
   `receipts/u7_reader_probe.txt`. Numbering no longer maps 1:1.
3. **Frozen human grammar deviation, untested:** `render_human` L204 emits
   `unassigned_cells: (not reported)` when the raw report lacks the key — a
   third token not in the frozen grammar (`<count|(none)>`), with zero test
   coverage (grep: no test references "(not reported)"). Both the shipped
   example and the blocked fixture carry `unassigned_cells: []`, so the branch
   is never exercised.
4. **Exit-4 alarm path untested** (would require mocking the reader;
   preregistration only says it "must never fire" — it never fired in any of
   my runs either).
5. **Mixed invocation untested:** no test runs accepted+rejected paths in ONE
   invocation (T6 = both rejected; T7 = all accepted), so the mixed exit code
   (2) and per-entry ordering are unpinned.

## Area 4 — ADVERSARIAL PROBES: DEFECT-FOUND (minor; hostile-input-only)

Full transcript: `receipts/b2a_probes_receipt.txt`; fixtures in `work/probes/`.
"Reader accepts" below = verified via the reader's public
`summarize_export_report` on my fixture before running the CLI.

- **P1 empty `body_groups: []` + root `complete`:** reader ACCEPTS; CLI clean
  (exit 0, `bodies: 0`). CLEAN. (Reader accepting a body-less `complete` is a
  reader-semantics question — preserved, not fixed.)
- **P2 all bodies omitted, minimal rows (no reason/blocking keys):** reader
  ACCEPTS; CLI renders every diagnostic as `(none)`, exit 0. CLEAN.
- **P3/P3b per-body status outside the contract vocabulary** (`exploded`,
  `mass_properties: null`; P3's first build wrongly kept mass_properties and
  was correctly rejected `blocked_group_has_mass`): reader ACCEPTS; CLI
  displays `export_status=exploded` verbatim as omitted, exit 0, no
  vocabulary flag. GAP/note — F3-honest (nothing invented; the reader is the
  validator and accepted it), but a diagnostic could reasonably flag it.
- **P4 `unassigned_cell_ids` as a string** (`"cell-B"`): reader ACCEPTS (it
  does not validate the field); human output MANGLES to
  `unassigned_cell_ids: c, e, l, l, -, B` (per-character); JSON fine; exit 0.
  **DEFECT — the exact mangle class M09's report.md says was "fixed and
  locked" (for `blocking_assignment_statuses`, T11) survives in
  `unassigned_cell_ids`: a `str` is a `Sequence`, so `_plural_list` (L162-163)
  iterates characters.**
- **P5 `unassigned_cells` rows as plain strings:** reader ACCEPTS; JSON mode
  fine (rows passed through raw, L133-135); human mode CRASHES —
  `AttributeError: 'str' object has no attribute 'get'` at render_human's
  `row.get('cell_id')` (L205-208) -> traceback, **exit 1**, violating the
  frozen exit-code contract ({0,2,4} + usage). **DEFECT.**
- **P6 depth-2000 nested `reason_codes`:** reader ACCEPTS; CLI renders the
  nested structure verbatim, exit 0 in both modes. CLEAN — this falsified my
  pre-probe crash hypothesis (parser recursion bomb); recorded honestly.
- **P7 invocation errors:** nonexistent path and directory-as-path ->
  clean `ok=false` / `input_read_error`, exit 2. Usage errors -> exit 2
  (the collision, see Area 2).

## Area 5 — U7 FINDING: CLAIMS-VERIFIED (own fixtures)

Transcript: `receipts/b2a_u7_receipt.txt`; fixtures `work/fx_blocked.json`,
`work/fx_refused.json` (genuine exporter path, built in `work/claims_check.py`).

1. **No misbehavior — reproduced.** Reader CLI on my blocked and refused
   fixtures: exit 0, stderr none, `export_status` correct, readiness False.
2. **Summary thinning — reproduced field by field.** Blocked: reader summary
   body entries carry NONE of `blocking_cell_ids` /
   `blocking_assignment_statuses` / `admission_reason_codes` (CON-4) although
   all three are present in every raw group row; top-level summary lacks
   `reason_codes`/`detail` (CON-6); per-cell `unassigned_cells` rows (CON-7)
   are reduced to bare `unassigned_cell_ids`. Refused: same CON-6 drop.
3. **CLI compensation — reproduced.** The M09 CLI surfaces all dropped fields
   from the raw mapping on my fixtures (e.g. body-B
   `blocking_cell_ids=['cell-B']`, `blocking_assignment_statuses=[{'cell_id':
   'cell-B', 'status': 'invalid_material_reference'}]`).
4. **Exporter semantics observation — reproduced:** with the report-global
   admission failure, raw body-A carries `blocking_cell_ids: []` (its cell
   still `resolved`) and only body-B names `cell-B` — matching M09's locked
   observation. M09's `receipts/u7_reader_probe.txt` matches my independent
   observation exactly. The T3/T4 `assertNotIn` pins would indeed flag any
   future reader-summary extension, as report.md claims.

## Overall verdict

**ACCEPT-WITH-NOTES.** No blocking defect. Non-blocking findings, in priority
order:

- D1 (minor defect): argparse usage errors exit 2, colliding with the frozen
  `2 = reader-rejected` code (CLI L226-238; frozen preregistration.md L122-123).
- D2 (minor defect): human-mode crash, exit 1 + traceback, on reader-accepted
  `unassigned_cells` rows that are not objects (render_human L205-208).
- D3 (minor defect): per-character mangle of a string `unassigned_cell_ids`
  in human output (`_plural_list`, L162-163) — the same class M09 claims was
  fixed and locked for a sibling field.
- G1 (gap): `(not reported)` grammar token not in the frozen grammar and
  untested; T9/T11 preregistration numbering drift; exit-4 path and mixed
  invocations untested; out-of-vocabulary per-body statuses displayed without
  flag.

All three defects require hostile input that the READER accepts — genuine
exporter output can never trigger them (the exporter always emits lists of
objects and list-valued IDs), no claimed M09 result is affected, and every
claim I tested reproduced exactly. Findings only; I changed nothing outside
`agents/B2a_review_m09/`.

## Integrity paste

```
$ git -C E:/ChimeraWork/mvc-20260924 status --porcelain -- tools Chimera/docs/matter material_volume_campaign/agents/M09_diagnostic
(empty; exit 0)
```

Before my runs: empty. After all my runs: empty. Final snapshot diff:
`before_after_identical=true, files_snapshotted=415, added=0, removed=0,
changed=0`. No `__pycache__` in `tools/` (grep: none). My writes were
exclusively under `material_volume_campaign/agents/B2a_review_m09/`.
