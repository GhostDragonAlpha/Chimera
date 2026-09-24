# B2a preregistered review check list — FROZEN before execution

Reviewer: B2a · 2026-09-24 · under review: `material_volume_campaign/agents/M09_diagnostic/`
at commit `7701d8db`. This file is written BEFORE any check below is executed.
Orientation reads (M09 files, reader, exporter, contract) were performed first;
no check below has been run yet. Only reads of the reviewed tree and writes
inside `agents/B2a_review_m09/` are permitted to me.

## THEORY (Rule 0, reviewer form)

- STATEMENT: M09's claimed results (11/11 pass, read-only 415-file proof,
  exit-code map {0,2,4}, readiness always false, public-API-only usage, U7
  summary-thinning finding) are reproducible from the committed artifacts by an
  independent reviewer without touching tools/, docs/, or the M09 directory.
- PREDICTION (untested by me until executed): the suite reruns green from a
  scratch copy; hash snapshots of tools/ + Chimera/docs/matter are identical
  across ALL my runs; no display path can show readiness true; the U7 thinning
  reproduces with my own fixture.
- FALSIFIER for the review itself (named now): if any M09 claim fails my
  independent reproduction, or any code defect/probe below fires, I record it
  as DEFECT-FOUND and the overall verdict cannot be ACCEPT.

## AREA 1 — CLAIM VERIFICATION

- C1.1 Record `git -C E:/ChimeraWork/mvc-20260924 status --porcelain -- tools
  Chimera/docs/matter material_volume_campaign/agents/M09_diagnostic` BEFORE my
  runs (must be empty) and AGAIN at the end (acceptance requires empty).
- C1.2 Snapshot SHA-256 + st_mtime_ns of every file under `tools/` and
  `Chimera/docs/matter` before my runs; re-snapshot after; require identical
  (added=removed=changed=0) and record the file count (M09 claims 415).
- C1.3 Copy the M09 suite VERBATIM into `work/m09_copy/` (CLI, tests/,
  run_suite.py); verify verbatim by SHA-256 equality against the originals.
- C1.4 Run the copied suite with `PYTHONDONTWRITEBYTECODE=1`, 3 times; require
  11/11 OK every time; record wall-clock timings (M09 claims ~3.6 s).
- C1.5 Independently verify the fixture-authenticity claim: my own script
  builds `build_export_report(manifest, partition, groups)` from the shipped
  examples and byte-compares against the shipped example report.
- C1.6 Exit codes: run the copied CLI myself on the shipped example (expect 0),
  a malformed fixture (expect 2), and confirm no run returns 1 or 4.
- C1.7 Readiness: grep every human output + JSON payload I generate for any
  readiness value other than false; final human line must be `readiness: false`.

## AREA 2 — CODE REVIEW (material_volume_diagnostic.py, committed text)

- C2.1 Public-API audit: enumerate every attribute the CLI reads off `reader`
  and `exporter`; require all to be public (no leading underscore), and all
  validation/statuses to come from `summarize_export_report` (no re-parsing of
  report internals to produce statuses; raw report used only for display
  passthrough keys named in the frozen contract).
- C2.2 Write-path audit: enumerate every filesystem-mutating call in the CLI
  (`open(...,'w')`, `write_text`, `mkdir`, `unlink`, `rename`, `shutil`, etc.).
  Require: none outside stdout/stderr. Confirm `sys.dont_write_bytecode = True`
  precedes the reader import.
- C2.3 Status-invention audit: every `export_status`/per-body status displayed
  must originate in the summary or be echoed verbatim from the raw report;
  `admission_status` null -> `"not_reported"` is allowed (frozen contract
  declares it); flag any other synthesized value. Known synthesized values to
  judge: `units.add("kg")` (line ~117), `omitted` boolean,
  `frames`/`units` aggregation.
- C2.4 Readiness audit (F2): enumerate every place `readiness` /
  `readiness_claimed` is rendered; confirm JSON payload hard-codes false,
  human tail line hard-codes false, and exit-4 alarm fires if a summary ever
  carries true.
- C2.5 Exit-code map audit: 0 all accepted / 2 any ExportInputError / 4
  readiness alarm / other = argparse usage; check precedence when both a
  rejection and an alarm exist (preregistration silent — record actual).
- C2.6 Error-path audit: exceptions NOT in {ExportInputError} that the CLI can
  raise on reader-accepted-but-hostile input (per-body status not in
  {exported, not_exported}; non-list unassigned_cell_ids; non-Mapping
  unassigned_cells rows; non-serializable passthrough values) — traced by
  reading, then CONFIRMED by Area-4 probes.

## AREA 3 — TEST QUALITY (tests/test_material_volume_diagnostic.py)

- C3.1 Map each preregistered test T1..T11 (preregistration.md) to an actual
  test method; name any preregistered assertion with no test, and any test with
  no preregistration (traceability drift).
- C3.2 Verify the in-suite fixture-authenticity assertion exists and runs
  (claimed: `build_export_report` on unmutated examples == shipped example).
- C3.3 Verify fixtures are generated via the exporter's public
  `build_export_report` on mutated in-memory copies (no hand-authored genuine
  statuses), with only the 2 malformed files hand-written.
- C3.4 Check the human-grammar coverage: does any test pin the FULL frozen
  grammar (every line kind), and does any test cover the `(not reported)`
  variant the implementation renders for absent raw `unassigned_cells`?
- C3.5 Check exit-code coverage: is exit 4 (readiness alarm) tested at all?
  Is multi-report mixing (accepted + rejected in one invocation) tested?

## AREA 4 — ADVERSARIAL PROBES (my fixtures, my dir, run against a verbatim
copy of the committed CLI)

- P1. Empty `body_groups: []` with root status `complete` (reader-accepted?):
  expect clean diagnosis, `bodies: 0`, exit 0.
- P2. All bodies omitted: root `blocked`, one `not_exported` body row WITHOUT
  `reason_codes`/`blocking_cell_ids` keys — expect `(none)` renderings, exit 0.
- P3. Per-body status the reader accepts but the vocabulary forbids:
  `export_status: "exploded"` (mass_properties null) under root `partial` —
  expect reader accepts, CLI displays verbatim as omitted; judge F3 honesty.
- P4. `unassigned_cell_ids` as a STRING ("cell-B") instead of a list (reader
  does not validate it): JSON mode vs human mode — check for per-character
  mangle (the defect class M09 claims was "fixed and locked").
- P5. `unassigned_cells` rows as plain strings instead of objects: JSON mode vs
  human mode — check for AttributeError crash / exit-code violation.
- P6. Deeply nested `reason_codes` (depth ~2000) — check reader parser
  RecursionError escapes the CLI's `except ExportInputError` -> traceback,
  exit code not in {0,2,4}.
- P7. Nonexistent path + directory-as-path — expect clean ok=false, exit 2.

Acceptance for probes: record actual stdout/exit per probe; classify each as
CLEAN / MANGLE / CRASH / EXIT-VIOLATION; a CRASH or EXIT-VIOLATION in a
reader-accepted report is a CLI defect (minor if only hostile/contrived inputs).

## AREA 5 — U7 INDEPENDENT VERIFICATION

- C5.1 Build my OWN blocked fixture (genuine exporter path, my dir) and run the
  reader's `summarize_export_report` on it: verify summary body entries lack
  `blocking_cell_ids` / `blocking_assignment_statuses` /
  `admission_reason_codes`, and top-level summary lacks `reason_codes`/`detail`.
- C5.2 Same for my OWN refused fixture: top-level `reason_codes`/`detail`
  dropped by summary; reader exits 0, readiness False, no stderr.
- C5.3 Verify the CLI (not the summary) surfaces those fields from the raw
  report on my fixtures.
- C5.4 Verify M09's receipt `u7_reader_probe.txt` content matches what I
  observe (reader CLI exits 0, correct statuses).

## DELIVERABLES (this dir only)

report.md with per-area verdicts (CLAIMS-VERIFIED / DEFECT-FOUND / GAP) +
overall ACCEPT / ACCEPT-WITH-NOTES / REJECT; receipts/ (hash snapshots, suite
logs x3, probe transcripts, U7 transcript); final integrity paste.

FROZEN AT: 2026-09-24, before C1.2's first hash command and all probes.
