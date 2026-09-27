# PREREGISTRATION — MAT2-X01 (repeatable objective definition, material-first era)

Card `MAT2-X01` (decision; done_when: "A finite purpose/lesson/free-play
completion definition is selected without inventing a campaign"). Attempt
`c593fffda68845b9bc76d361ef8065dd`, agent
`arrival-44b4c756e017416b9c81f9532c4cb3a1`, criteria sha256
`e2f2c219a438c9575c01698dc5dd66f799f6eef8a7577ad3571dcae8c8d1c9aa`,
active scope sha256 `cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`,
archived scope sha256 `01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6`,
planning id `X01`. Written BEFORE the extraction ran. Verification profile:
`records` (offline; numerical evidence required; falsifier: "Missing
identities or a claimed pass unsupported by records fails; a screenshot is
not a substitute.").

## RECONCILE / DECIDE (before implementation)

The exact decision has a recorded ruling chain; nothing is chosen by default:

1. MAT2-P01 completion contract (merged at 97993cbe, PR #192, card criteria
   `e4521ad79a5bc263ba333b81ebe36599e1d6da5a13eed92c2ff5fa3a0e670c5e`) froze
   the finite game frame verbatim: core clause "One monkey, ground movement,
   one climbable trunk, return to ground, explicit success/failure behavior;
   broader features excluded" (carried from ONT-P01, archived board DONE) plus
   the material-first addition that orders the milestones: walking through
   woods first, then the climb/return goal.
2. The complete-game framing (not movement demo) is recovered, not invented:
   the hash-pinned goal line in `docs/MONKEY_RUN.md` demands "complete player
   flow"; the X01 catalog observation states the choice explicitly.
3. Legacy reuse is scoped: archived ONT-X01 (attempt
   `30614130594b42b1afd8cbcfe5e6c840`, PR #136 ACCEPTED under archived scope
   `01ea5cdd...`) contributes structure and its disclosed open operator
   decision request. Its DONE is NOT promoted: the archived contract's
   envelope numbers (20.0 m clearing; trunk 11.976783/2.471766) and its
   "B01-B07 never auto-activated" wording are OBSOLETE in this revision
   (MONKEY_RUN: the selected material assembly consumes B01-B07 and they are
   required; MAT2-F01 authors the clearing). K08 is cited from the CURRENT
   catalog, where it is a live task, not from the archived contract.
4. The single residual operator taste is presentation-level
   (objective-presentation-surface), disclosed open in the lead review of PR
   #136; it is carried forward as the one decision request, not answered.

## STATEMENT (a theory that can lose)

The frozen records already select the small game's repeatable objective: ONE
finite, repeatable session loop — ground movement; approach/attach the one
climbable trunk; climb; hold; descend; release; return to ground/walk again —
with explicit success/failure behavior, framed as a complete game (not a
movement demo), repeated as free play with no scripted progression and no
campaign (broader features excluded by the frozen contract). The material-first
addition orders the same finite frame: walking through woods is the first
product milestone, the climb/return loop the next; nothing outside the frozen
frame gates completion. Every clause of this definition is quotable verbatim
from hash-pinned current records; the spatial envelope and numeric acceptance
limits are NOT frozen yet (MAT2-F01, MAT2-P06 are open cards) and appear only
as explicit unresolved inventory. Exactly one presentation-level operator
decision request remains.

## PREDICTION (not yet measured)

1. Probes P1-P4 pass: the MAT2-P01 contract artifact, the three authority
   files and the current catalog reproduce every pinned identity and quote.
2. The definition emerges with every quote reproducing from its pinned source
   (whitespace-normalized) and zero invented elements.
3. Exactly one operator decision request (objective-presentation-surface);
   zero thresholds, scores, missions, campaign structure.
4. The archived-era envelope tokens do not appear anywhere in the definition;
   the unresolved inventory names MAT2-F01 (envelope), MAT2-P06 (limits) and
   MAT2-X02 (session flow owner) explicitly.

## FROZEN PROBES

- P1 CONTRACT_IDENTITY: sha256(MAT2-P01 contract.json) ==
  `e255eb44203212c039598d28629c21e6e1c019d1abe6caa07b4430fca53715a5`; schema
  `chimera.completion_contract.v1`; task_id `MAT2-P01`; identities equal
  {criteria_sha256: `e4521ad79a5bc263ba333b81ebe36599e1d6da5a13eed92c2ff5fa3a0e670c5e`,
  active_scope_sha256: `cb5475f8486197a973edc4360b177fc31a629c4f0979ebf80dd76aae57996097`,
  archived_scope_sha256: `01ea5cddca8d4795caa096945edf7eadcd1f3eb3e2f084fd2ee36a08cae12ef6`,
  instruction_revision: `astra-0031`} byte-for-byte (full hashes, no prefixes).
- P2 CLAUSE_CARRY: normalized core_clause.text and material_first_addition.text
  both reproduce inside the CURRENT catalog task P01's done_when sentence (the
  planning clauses the frozen contract carries); and the MAT2-X01 card
  done_when equals the catalog X01 done_when byte-for-byte (normalized).
  [Wording corrected pre-run from an earlier draft that misstated the carry
  target as the MAT2-X01 done_when; no probe has run yet.]
- P3 AUTHORITY_HASHES: full sha256 of MATERIAL_PLAN_ADOPTION.md ==
  `81f432fc9fcee8aee6fcdcac39487f50538f1f4c1b9d4c2821d3bb0f40e47287`,
  APPROVED_SCOPE.json ==
  `fe74180d7b6ad584f48c5fd9a642db4393c26c4e4cd64c8b41652e9b30c27660`,
  docs/MONKEY_RUN.md ==
  `2d4611802c6338c26c43bd5217e59ab514588a0a25b949ac5c8fbbe22651359d`
  (matches the contract's 16-hex authority prefixes and the lead review
  evidence EVIDENCE.md lines 91-93).
- P4 CURRENT_CATALOG_QUOTES: pinned sha256(monkey_completion_map.json) ==
  `8fa2e1409a2da1e3cbe70a84f59f7620a61d3eed12519171190e9c61543cb272`;
  sha256(docs/roadmap/holodeck_tasks.json) ==
  `d5c7aa8b9e264e96bb3de6a0f3d48069ee0b88c9f10ae84b52bd8cfce797fcd8`;
  K08, X02, S05 done_when, X01 observation and finish_line quotes reproduce
  from the map; MONKEY_RUN goal line, physical law and backlog-law sentences
  reproduce from MONKEY_RUN.md.
- F1 TAMPER_REFUSAL: any identity mismatch raises ExtractionFailure; no
  objective_definition.json is written.
- F2 INVENTION_SCAN: word-boundary regex for {mission, quest, level-up,
  campaign structure, score threshold, achievement, leaderboard} finds nothing
  in the definition JSON.
- F3 ENVELOPE_NON_PROMOTION: tokens {20.0 m, 11.976783, 2.471766} absent from
  `selected_definition` (the objective content itself); they may appear only in
  `legacy_crosswalk.not_carried` as the explicit non-promotion record;
  unresolved_inventory lists mat2-f01-spatial-envelope,
  mat2-p06-acceptance-limits, mat2-x02-session-flow as pending downstream, with
  the archived-promotion flags false.
- F4 SINGLE_DECISION_REQUEST: exactly one request, id
  `objective-presentation-surface`, options {silent free-play, attempt
  counter, timer + counter}, provenance ONT-X01 PR #136 review disclosure.
- F5 QUOTE_REPRODUCTION: every entry of the definition's evidence map
  (field -> source path + sha256 + verbatim quote) reproduces from the pinned
  file; a mismatch fails the run (records oracle; no unsupported pass).
- F6 IDENTITY_COMPLETENESS: every records entry carries a full 64-hex sha256;
  no prefix-only or missing identities.

## BOUNDS

CPU-only, stdlib only, `python -B`; sources read-only at their pinned paths;
writes confined to this attempt workspace under
`tools/monkey_campaign/contributions/MAT2-X01/`; output <= 16 MiB. The
archived ONT-X01 workspace is read-only; only its disclosed decision request
and structure are reused, with provenance recorded in the definition. No
runtime/GPU/visual claim is made: profile `records`, nonvisual_reason applies
("A source/contract/measurement task whose truth requires records or numerical
oracles, not a 3D image.").
