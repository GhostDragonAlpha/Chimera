# PREREGISTRATION — ONT-P06 CORRECTION (release acceptance limits, blob-anchored)

Card `ONT-P06` (decision; observation: "No numeric product-wide limits
supplied; **do not fabricate them**"), state CHANGES_REQUESTED on
`publication-94455595e531451db91a9ed701e9fc3f`. Correction attempt
`d6f9a19bb3ed49619b5e75ab9a4a93fd`, arrival
`arrival-c077fc4dd7284df7a4aad08605ed24f6`, criteria
`7bea081e57fa35a83fcedfc7dfc8243c63d027448b0d9b104eab179dd96f1333`.
Written BEFORE the corrected limits tool ran in this workspace. This prereg
AMENDS attempt `ae96df0371894a94a9ccb114975f8197`'s prereg honestly: the two
lead findings below are incorporated verbatim as the correction scope; the
15 derived VALUES are not contested and do not change.

## CORRECTION SCOPE (lead finding arrival-876e63bf, evidence lead-verify-20260926/ONT-P06.json)

1. The play worktree `E:/ChimeraWork/monkey-play-20260924` was reorganized at
   HEAD `8d16d3c1` (2026-09-26 01:28), removing every cited on-disk source, so
   the prior tool failed at setup (0/6, FileNotFoundError) and the card
   falsifier "any source identity (path/commit) that does not exist" FIRED.
2. The prior claim "each re-measured at runtime" was overstated for 7/15
   limits (controls-bindings, tick-hz, worst-ledger hardcoded; blocking-radius,
   settle-sink/vy, ui-poll value-hardcoded re-measuring only line numbers;
   session_flow import dead code).

## STATEMENT (a theory that can lose)

Every cited source can be re-pointed to a PINNED GIT REVISION of the play
repository and recovered byte-exactly, read-only (`git show <commit>:<path>`),
into this attempt's `reference/` tree with sha256 asserted at import (the
accepted ONT-X02/ONT-P03/ONT-U02 blob-anchor pattern); the tool then reads
ONLY those hash-asserted pinned bytes (no live-worktree read anywhere, the
play worktree untouched), so every one of the 15 DERIVED limits is genuinely
re-measured at run time — including the 7 the lead found hardcoded — while
every VALUE stays bit-identical to the verified prior proposal, and the 4
taste limits remain explicit OPERATOR DECISION REQUESTS.

## PREDICTION (not yet measured by this attempt)

Pinned lineage (commit: path = blob sha256 asserted at import; recoverable
read-only from the play repo; live worktree at HEAD 8d16d3c1 untouched):

1. clearing_declaration.json @ c9aee37c — half-width 20.0, spawn (0,0,0),
   clearance 1.5, envelope 0.25, seed 4598321 (json-field reads).
2. trunk_declaration.json @ b4de4de8 — site base centre
   (11.976783, 0, 2.471766) AND trunk bound radius_m **0.037** (json-field
   reads; the prior run hardcoded 0.037 — now measured).
3. trunk-blocking radius **0.287 = measured 0.037 + measured 0.250**, rounded
   to 3 dp (arithmetic over two pinned operands; F07 derivation rule).
4. session_flow.py @ 42f7cdc4 (blob 30e06c04..., the X02 pin) imported from
   reference/ — DEFAULT_FLOW_BINDINGS read live: Return/Escape/R/Q (the prior
   dead import now does the reading).
5. gait_controller.hpp @ 8cec4a6b — the require line `dt<=1/300.` +
   `substeps==4` regex-parsed (tick 300 Hz, substeps 4); corroborated by
   earth_environment.hpp @ ee52a99f line 91 `tick_hz==300`; the two pins must
   agree or the tool refuses.
6. acceptance.py @ 8294053b — EPISODE_CAP_TICKS (line 19) = 300 and
   EVAL_WINDOW_TICKS (line 20) = 270 literal-parsed (prior prereg said
   lines 18-19; the pinned object shows 19-20 — corrected here).
7. receipt_wave47.json @ 33e7a444 — "worst moving ledger **30.970714 J**"
   regex-parsed (4 occurrences, all must agree).
8. slice_server.py @ 0b3b22a5 — SETTLE_VY literal 0.05 (line 44) parsed;
   SETTLE_SINK_M (line 48): the line's own recorded bar "0.010000 m" parsed
   AND cross-checked against the line expression
   `13824.5 * 9.81 / 1.3562e7` evaluated = 0.009999878 m, which rounds to the
   recorded bar at the line's own 4-dp display (both must agree; the
   13824.5 kg lineage stays under the preserved D-W04 caveat); the page's own
   poll cadence "every 100 ms" (line 449) parsed.

Exactly 15 DERIVED limits, values bit-identical to the prior verified
proposal; exactly 4 OPERATOR DECISION REQUESTS unchanged; the unresolved
D-W04 CoT denominator lineage (13824.5 vs 10.038 kg) preserved. Tests 6/6.

## FALSIFIER

Any pinned reference byte whose sha256 drifts from the pinned value; any
pinned commit:path identity that does not exist in the play repository;
any measured value that disagrees with its cross-check (gait vs earth tick;
SETTLE_SINK_M recorded bar vs rounded expression; the 4 ledger occurrences);
any change to the 15 derived values or the 4 decision requests. The tool and
the tests must fail loudly on any of these rather than ship.

## BOUNDS

CPU-only, stdlib + the local git CLI used read-only (`git show`,
`git cat-file -e`) over `E:/ChimeraWork/monkey-play-20260924`; ZERO writes
outside this attempt workspace; the play worktree and E:/PythonChimera are
not modified; ≤16 MiB artifact output.
