# GEN-11 FRESH-SYSTEM VERIFICATION — RUN RECORD (2026-09-10, glm53-fresh-01)

Task `master-catalogue-sync-01` · generation **11** · owner `glm53-fresh-01` · slot `2` ·
branch `astra/tasks/master-catalogue-sync-01` (base of record `7d3601e7`; gen-7 preserved head
`1dd77367`; this record's commit is the new exact head submitted through the controller).
Preregistration: `GEN11_FRESH_SYSTEM_PREREGISTRATION_20260910.md` (written before any run).

## Context of this round

The gen-7 review (controller rev 416) was requeued by the lead (rev 429); owner buffy-02 was
revoked by the operator (rev 433); the supervisor recovered the task (rev 434, "returned for
fresh-system testing") and this session claimed it fresh (rev 442). Worktree verified before any
write: clean tree, exact branch, local HEAD == `origin/astra/tasks/master-catalogue-sync-01` ==
controller slot-2 `worktree_head` (`1dd77367`). No other slot's runtime, executable or session
files were used.

## Executed runs (fresh system, isolated registries only)

| # | Command (cwd `E:/ChimeraWork/slot-02`) | Result |
|---|---|---|
| R1 | `python -m pytest . -q` (cwd `tools/agent_fleet`), BEFORE any edit | **109 passed, 1 skipped** (78 s) — preserved gen-7 deliverable green on this fresh system |
| R2 | `python tools/agent_fleet/master_catalogue.py --out .tmp/glm53_catalogue_import.json` — **FAILED**: `UnicodeEncodeError: 'charmap' codec can't encode character '\u2192'` (cp1252 console); `--out` file never written; MIGRATION.md step 1 fails verbatim on a stock Windows console | FALSIFIER FIRED (prediction b) |
| R3 | Same with `PYTHONUTF8=1`: payload reproduces exactly — cards 240, domains 40, master_row_ids 65, observations 68, unresolved 3, unkeyed_requirements 271; version_pin Master `f389f913…` / catalog `d9bb4419…` == recorded gen-7 pins; digest `5e1eb0c9…` vs recorded `b72818d6…` | content reproducible; digest differs |
| R4 | Full structural walk of recorded gen-7 payload vs rebuilt payload: **ZERO content differences**. Every delta is `source.path` (builder-host directory `slot-04` vs `slot-02`) or advisory `source_manifest.*.git_commit` (`d7acd0fb` vs `1dd77367`) — documented ADVISORY provenance, never authentication; `validate_payload` recomputes truth from retained text | prediction (c) resolved: exact source-hash + builder-host explanation |
| R5 | Correction (console-summary robustness only; artifact/digest semantics untouched) + regression test | see below |
| R6 | `python -m pytest test_master_catalogue.py -q` after correction: first run **1 failed** (test's own harness bug: relied on default source paths instead of explicit files — the test rebuilt the real canonical payload), then fixed test | **23 passed** |
| R7 | `python tools/agent_fleet/master_catalogue.py --out .tmp/glm53_catalogue_import.json` on the STOCK cp1252 console | exit 0; artifact written; summary survived; **digest byte-identical to R3** (`5e1eb0c9…`) — console-only change |
| R8 | `python -m pytest . -q` (full suite, after correction) | **110 passed, 1 skipped** (77 s) |

## Correction made (minimal, in scope)

`tools/agent_fleet/master_catalogue.py` `main()`: the import-arguments artifact is now written
BEFORE the console summary, and the summary is ASCII-escaped with a `backslashreplace` fallback
so a cp1252 console can never again cost the deliverable. The `--out` file keeps verbatim
Unicode; the payload digest is unchanged (console path only; R7 proves it).

New regression test `test_cli_stdout_survives_ascii_console_and_writes_out_first` (in
`tools/agent_fleet/test_master_catalogue.py`): drives `main()` against explicit temp source
files containing U+2192 under a StringIO stdout, asserting exit 0, an encodable-on-ASCII summary,
the artifact written first with a matching digest, and verbatim Unicode retention. Its first
version FAILED (harness used default paths and rebuilt the real canonical payload instead of its
fixture) and is preserved in this record as failed-correction history; no tolerance was widened
and no assertion was weakened to pass.

## Falsifier ledger for this round

- FIRED once (R2, cp1252 console crash) — corrected in scope, verified by R7/R8.
- Not fired: no test failure of the committed suite (R1 green); no `validate_payload` refusal on
  the real-source payload (R3/R5 emit zero refusals); no coverage-counter drift (all recorded
  values reproduced); no write outside declared scopes; no live-registry contact; no protected
  build path touched; historical evidence untouched (append-only).

## Verdicts (separate, honestly stated)

- Suite (fresh system): **PASS** — 110 passed, 1 skipped, isolated temp registries only.
- Payload reproduction: **PASS** — content bit-reproducible against pinned source hashes
  (`f389f913…` / `d9bb4419…`); digest is transport-reproducible but embeds the builder-host
  path and advisory git commit, so it is per-host by design (documented; lead import step must
  build from the lead's own checkout, which MIGRATION.md already instructs).
- CLI console robustness: **PASS after correction** (fired falsifier preserved as history).
- Live-registry import: **NOT PERFORMED** — packet reserves it for the lead (never by this
  worker). Catalogue availability stays planning-data only; no admission/authority claimed.
- Human acceptance: **NOT CLAIMED**. Runtime/DYAD/engine: NOT_TESTED (out of scope, CPU/docs).
