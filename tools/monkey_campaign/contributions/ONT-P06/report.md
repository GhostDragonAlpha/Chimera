# ONT-P06 CORRECTION REPORT — blob-anchored re-pinning + corrected claim

Attempt `d6f9a19bb3ed49619b5e75ab9a4a93fd` (arrival
`arrival-c077fc4dd7284df7a4aad08605ed24f6`), correcting attempt
`ae96df0371894a94a9ccb114975f8197` whose publication
`publication-94455595e531451db91a9ed701e9fc3f` was withheld by lead finding
`arrival-876e63bf9dbb44a8b10c5b546f783e9b` (evidence
`E:/ChimeraWork/monkey-coordination/lead-verify-20260926/ONT-P06.json`).

## Finding 1 — cited sources no longer exist (card falsifier fired)

The play worktree `E:/ChimeraWork/monkey-play-20260924` was reorganized at
HEAD `8d16d3c1`; every previously cited on-disk source disappeared and the
prior tool failed at setup (0/6, FileNotFoundError).

FIX: every cited source is re-pointed to a PINNED GIT REVISION and recovered
byte-exactly, read-only, into this workspace's `reference/` tree (the
accepted ONT-X02/ONT-P03/ONT-U02 blob-anchor pattern):

| pinned source | commit | blob sha256 (first 8) |
|---|---|---|
| clearing_declaration.json | c9aee37c | 18dd2ff6 |
| trunk_declaration.json | b4de4de8 | 94ff906e |
| product/session_flow.py | 42f7cdc4 | 30e06c04 |
| product/input_mapper.py (dep) | 8550b634 | 7a36a45e |
| typeb_export/command_record.py (dep) | e028d6fb | 67711759 |
| playable_slice/slice_server.py | 0b3b22a5 | 5accc730 |
| science_funnel/first_skill/acceptance.py | 8294053b | 1065ab2f |
| validation/gait_zero_20260919/receipt_wave47.json | 33e7a444 | 4480d18b |
| ChimeraEngine/engine/gait_controller.hpp | 8cec4a6b | f0ffea12 |
| ChimeraEngine/engine/earth_environment.hpp | ee52a99f | b4747d34 |

`implementation.py` asserts at import that each reference byte matches its
pinned sha256 AND that `git cat-file -e <commit>:<path>` still resolves in
the play repository — the card falsifier ("any source identity that does not
exist") now fires loudly both on byte drift and on identity removal
(negative-checked). The play worktree was NOT modified (read-only
`git show`/`cat-file` only); no writes outside this attempt workspace.

## Finding 2 — "each re-measured at runtime" overstated for 7/15 limits

All 7 previously value-hardcoded limits now genuinely read their pinned
bytes; every one of the 15 limits carries a `provenance` entry with the
exact method (also summarized as `measurement_modes` in the proposal):

- controls-bindings: the session_flow import is no longer dead —
  `DEFAULT_FLOW_BINDINGS` is imported from the hash-asserted pinned module
  and inverted key->action (Return/Escape/R/Q).
- simulation-tick-hz: regex-parsed from the pinned gait_controller.hpp
  require line (dt<=1/300., substeps==4, line 1961 @8cec4a6b), cross-checked
  against earth_environment.hpp:91 (tick_hz==300 @ee52a99f); the tool
  refuses if the pins disagree.
- walking-worst-ledger-j: regex-parsed from the pinned receipt_wave47.json
  @33e7a444 ("worst moving ledger 30.970714 J", 4 occurrences, all must
  agree).
- trunk-blocking-radius-m: the previously hardcoded 0.037 is now measured
  (trunk_declaration.json geometry.radius_m @b4de4de8) plus the measured
  envelope 0.250, rounded 3 dp.
- stability-settle-sink-m: the pinned line's own recorded bar "0.010000 m"
  (line 48 @0b3b22a5) is parsed AND cross-checked against the line
  expression `13824.5 * 9.81 / 1.3562e7` = 0.009999878 m, which rounds to
  the recorded bar at the line's 4-dp display (tool refuses on mismatch);
  the 13824.5 kg lineage stays under the preserved D-W04 caveat.
- stability-settle-vy-ms: literal parsed (SETTLE_VY = 0.05, line 44).
- ui-poll-cadence-ms: regex-parsed ("every 100 ms", line 449).

The corrected claim text (proposal `law`): "every numeric is DERIVED
(re-measured at run time from sha256-asserted bytes recovered read-only at
pinned git revisions into reference/; no live-worktree source is read) or
explicitly OPERATOR_DECISION_REQUESTED; zero fabricated numbers."

## Unchanged (per the lead's verification)

All 15 derived VALUES are bit-identical to the prior verified proposal
(checked programmatically: zero diffs); the 4 operator decision requests are
identical; the unresolved D-W04 CoT denominator lineage (13824.5 vs
10.038 kg) is preserved, now also naming the SETTLE_SINK_M lineage as the
lead's own anomaly note did.

## Tests and artifacts

`python -B test_implementation.py` (CPU-only, stdlib): **Ran 6 tests, OK**
(6/6), deterministic on rerun; falsifier negative-checked. Artifacts:
PREREGISTRATION.md (frozen before the corrected tool ran, honestly amended),
implementation.py, test_implementation.py, limits_proposal.json
(schema ont-p06.release_limits.proposal.v1), reference/ (10 pinned blobs),
this report. Hashes are recorded in the publication request.

## Remaining gates (unchanged)

Operator answers to the 4 decision requests freeze the last limits before
acceptance trials; absolute CoT limits stay blocked pending the D-W04
registration.

Failures: none.
