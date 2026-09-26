# REPORT — I-S04-PLAYER-DIAGNOSTICS-FOLLOWUP (correction: seam vendored, 9/9 self-contained)

Attempt `e8b61636f59d45ca835e1d1fbe9e08a5`, arrival
`arrival-c59287b07e0c438e9b8866aa7086e1b1`, task
`I-S04-PLAYER-DIAGNOSTICS-FOLLOWUP`, criteria
`9fa0a82d860fcf38f0a1809fab638ac1187962a257127a4d26de86c721bbe4f3`.
PREREGISTRATION frozen before probes:
sha256 `eaeb01282549012c6e05e3a05a4a248f018fccd925fbedbac0600b78d7c99806`.

## What was corrected

Lead pre-publication verification of request
`publication-e7eeb8677a2b400aaded97c27d66e95d`
(`E:/ChimeraWork/monkey-coordination/lead-verify-20260926/I-S04-PLAYER-DIAGNOSTICS-FOLLOWUP.json`)
showed the adapter itself is sound but the as-specified run failed 4/9
ModuleNotFoundError: the seam (`input_settings -> input_mapper ->
tools.science_funnel.typeb_export.command_record`) was resolved from the LIVE
play worktree, and HEAD `8d16d3c1` there deleted `tools/science_funnel/`.
Control rerun serving the seam from pinned rev `9afbddcd` blobs: 9/9. This
attempt lands the fix the lead specified.

## Seam-pinning approach (the campaign's established reference/ pattern,
as accepted on I-U07-TRACE-FOLLOWUP and I-R05-FOLLOWUP)

1. VENDOR: the four seam files were extracted READ-ONLY from the pinned
   revision `9afbddcd90164b5544a16fd0bc72278d985eb6e3` (the same revision the
   accepted parent ledger cites) via
   `git -c safe.directory=... -C E:/ChimeraWork/monkey-play-20260924 show 9afbddcd...:<path>`
   into `reference/` at canonical repo-relative paths. Extracted bytes hashes
   match the accepted ledgers EXACTLY (parent I-S04 ledger for the three
   product files; I-U07-TRACE-FOLLOWUP ledger for `command_record.py`):
   - `tools/monkey_campaign/product/input_settings.py`
     `8d1a49d63f85164f3b9ac27f3387237d0a0790f68075e2455a74e2caa485a2f1` (22608 B)
   - `tools/monkey_campaign/product/session_flow.py`
     `30e06c04dc33da271bfe817d26a4adbf1251f392b224546fc795f307458455cf` (16981 B)
   - `tools/monkey_campaign/product/input_mapper.py`
     `7a36a45ead6637d9ba5659ea43b54a6b424803c8e57d02720ac970b42cfe6b44` (18349 B)
   - `tools/science_funnel/typeb_export/command_record.py`
     `6771175933ad20ac6d20c360df96f6a9729a56deb31c58a13be5e76e1cc4355e` (12095 B)
2. LEDGER: `reference/EXTRACTION_LEDGER.json` records extracted_by (task /
   attempt / arrival), provenance (seam revision, read-only extraction, the
   correction being made), per-file `repo_path / reference_path / revision /
   sha256 / size_bytes / role`, the accepted module under
   `pins_for_import_only` (IMPORTED, never copied:
   `player_diagnostics.py` `53e34c62850ff222e2ecd92d20498baf88e9f8f0189b8c215d0cc79b06a7a339`,
   merged PR #125), and `read_only_after_extraction: true`.
3. ASSERT AT IMPORT: `implementation.materialize_pinned_seam()` copies the
   vendored bytes into a fresh OS temp directory in canonical repo layout,
   asserting every pin hash first; any missing file or drifted byte raises
   `AdapterIdentityFailure("pinned_source_hash_mismatch" /
   "pinned_source_missing")` BEFORE any import. `bind()` additionally
   cross-checks the ledger's `files[]` hashes and `seam_revision` against the
   code pins and refuses divergence. The accepted module bind keeps its
   sha256 tamper refusal. The prior live-worktree `sys.path.append(play_root)`
   is GONE — no unpinned path remains on the seam import path.

## Evidence (9/9, as-specified command, this workspace)

`python -B test_implementation.py` (run twice: from the workspace and from an
unrelated cwd `C:/` to demonstrate checkout-independence):

    Ran 9 tests in 0.148s / OK  (EXIT=0)
    Ran 9 tests in 0.097s / OK  (from C:/)

Full transcript: `test_run_evidence.txt` (sha256
`f470703a1356005dc61b3901db556d53a9b19489a83e7d3f528b1b7d2a75d305`).
Test 1 now also proves the pin law mechanically: hash-asserted
materialization of all four vendored files plus a drifted-pin refusal
(`pinned_source_hash_mismatch`) — without touching the real reference bytes.
`python -B implementation.py` regenerated `samples.json` (schema
`i-s04-followup.feedback_adapter.v1`, 4 deterministic samples for later HUMAN
review; correlation ids are the accepted module's per-call identifiers).
Behavior is unchanged from the lead-verified control run: REAL corrupt-json
refusal -> KNOWN damaged-file message; REAL unknown action `teleport` ->
KNOWN no-such-action message; REAL session_flow key_press drop outside
`playing` -> KNOWN flow message; fabricated future code and path-bearing
exception -> UNKNOWN with correlation id and paths confined to the developer
`diagnostic`; `loaded`/`first_run` -> None.

## Bounds / hygiene

CPU-only stdlib; play repository touched ONLY via read-only `git show` at the
pinned rev (no checkout/branch/worktree mutation); zero writes outside this
attempt workspace; artifacts ≤ 16 MiB. The rogue dir that formerly occupied
the patch path was lead-quarantined; nothing was restored from it — every
file here is freshly written in THIS attempt, and the preregistration names
THIS attempt `e8b61636f59d45ca835e1d1fbe9e08a5`.

## Artifact hashes (sha256, at submission time)

See `publication_request.json` `artifacts[]` — generated after all files were
final; the submit tool re-asserts every hash.
