# PREREGISTRATION — I-S04-PLAYER-DIAGNOSTICS-FOLLOWUP (correction: seam vendored, tests self-contained)

Card `I-S04-PLAYER-DIAGNOSTICS-FOLLOWUP` (planning S04; parent
I-S04-PLAYER-DIAGNOSTICS = merged PR #125; accepted module
`player_diagnostics.py` sha256 `53e34c62…` pinned at bind, tamper refused).
Attempt `e8b61636f59d45ca835e1d1fbe9e08a5`, arrival
`arrival-c59287b07e0c438e9b8866aa7086e1b1`, criteria
`9fa0a82d860fcf38f0a1809fab638ac1187962a257127a4d26de86c721bbe4f3`.
Written BEFORE any probe ran in this attempt. This attempt supersedes the
drift finding on prior request `publication-e7eeb8677a2b400aaded97c27d66e95d`
(lead verification: as-specified run failed 4/9 ModuleNotFoundError because the
unpinned seam was resolved from the live play worktree, whose HEAD `8d16d3c1`
reorg deleted `tools/science_funnel/`).

## STATEMENT (correction)

The SAME narrow adapter — zero new vocabulary, every message/action from the
accepted module's `explain*` functions — becomes self-contained at ANY checkout
when the seam sources it drives are VENDORED byte-identically from the pinned
revision `9afbddcd90164b5544a16fd0bc72278d985eb6e3` (the same revision the
accepted parent ledger cites) under a local `reference/` directory with an
`EXTRACTION_LEDGER.json`, and are materialized hash-asserted at import (the
campaign's established I-U07-TRACE-FOLLOWUP / I-R05 pattern): each pinned file
is copied to a fresh OS temp directory in canonical repo layout, its sha256 is
checked against the pin, and ANY mismatch refuses by name before import.
Vendored seam: `input_settings.py`, `session_flow.py`, `input_mapper.py`,
`command_record.py`. The accepted `player_diagnostics` module is still
IMPORTED, never copied (sha pin stays; recorded ledger-wise as
import-only pin). No live play-worktree path and no parent-reference directory
remains on the seam import path.

## PREDICTION (not yet measured)

1. `python -B test_implementation.py` runs the SAME nine tests and reports
   9/9 OK in this workspace, WITHOUT the play worktree contributing any
   import (the previously failing seam chain
   `input_settings -> input_mapper -> tools.science_funnel.typeb_export.command_record`
   resolves entirely from hash-asserted `reference/` materialization).
2. Tampering with any vendored reference byte produces a named refusal
   (`pinned_source_hash_mismatch`), not a silently different module.
3. The adapter behavior is unchanged from the verified control run: REAL
   corrupt-json load -> refused -> KNOWN damaged-file message; REAL unknown
   action `teleport` -> KNOWN no-such-action message; REAL `session_flow`
   key_press drop outside `playing` -> KNOWN flow message; fabricated future
   code and path-bearing exception -> UNKNOWN with correlation id, path only
   in the developer `diagnostic`, scrubbed from `message`; `loaded`/
   `first_run` -> None (module law).
4. `implementation.py` re-renders the same deterministic `samples.json`
   schema (`i-s04-followup.feedback_adapter.v1`, 4 samples) for later HUMAN
   review.

## FALSIFIER

Any of the nine tests failing; a pinned reference hash mismatch NOT refused;
any successful import that silently depended on
`E:/ChimeraWork/monkey-play-20260924` HEAD (or any unpinned path); a message/
action not produced by the accepted module; a path leaking into a
player-facing `message`; `loaded`/`first_run` producing a diagnostic; accepted
module sha256 drift not refusing at bind.

## BOUNDS

CPU-only, stdlib; extraction from the play repository is READ-ONLY git
(`git show 9afbddcd…:<path>`), no checkout/branch/worktree mutation; all
writes confined to this attempt workspace; output budget ≤ 16 MiB; samples
are rendered for HUMAN review — no player-validation is claimed.
