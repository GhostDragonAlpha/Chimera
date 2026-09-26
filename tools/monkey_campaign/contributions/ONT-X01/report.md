# ONT-X01 — repeatable objective definition (record-bound)

**Verdict: the small game's repeatable objective is RECOVERED from frozen
records, not invented: one complete ground→trunk→climb→hold→descend→ground
loop (the frozen K08 clause, verbatim), repeated as free play inside the
frozen clearing envelope, with physical/visible failure semantics and no
campaign (the contract's exclusions already forbid one). The demo-vs-game
framing is likewise recovered ("complete player flow"). Exactly ONE operator
decision request remains: the presentation surface.**

- Card `ONT-X01` (decision; observation "Movement demo versus complete game
  needs this explicit product choice"), attempt `30614130594b42b1afd8cbcfe5e6c840`,
  agent `c95e1722350849bca846b237c1f60997`, criteria
  `ff69d9a1099058276b43af6721a2ff118523235f936bc6de0782173dbbbaa74f`.
- Preregistration written before the extraction ran.

## The definition (objective_definition.json, schema ont-x01.objective.v1)

- **Repeatable objective**: ONE complete ground → trunk → climb → hold →
  descend → ground loop in one session; success clause = K08 VERBATIM
  ("Player approaches, attaches, ascends, holds, descends, releases and
  resumes all-fours walking in one session" — frozen completion contract,
  ONT-P01 v1.0.0, artifact sha256 `80b2e2f2…` verified, scope fingerprint
  `01ea5cdd…` asserted).
- **Failure semantics**: physical and visible (falls, rejected grips, lost
  contact); no silent teleport/hidden support; explicit in-game continue path
  (contract SC-FAILURE-BEHAVIOR).
- **Repetition**: free-play, no scripted progression, inside the frozen
  envelope (half-width 20.0 m; one trunk at (11.976783, 0, 2.471766)).
- **Framing**: complete game (not movement demo) — recovered from the sealed
  goal line's "complete player flow" (verified present in docs/MONKEY_RUN.md;
  the matcher normalizes line wrapping).
- **No-campaign law**: already frozen — the contract's exclusions list the
  deferred families and forbidden substitutes by name; nothing new needed.
- **Operator decision request (the one genuine residual)**:
  `objective-presentation-surface` — silent free-play vs attempt counter vs
  timer+counter; recommendation: attempt counter carried by the page's
  existing state feedback (no new HUD surface, no thresholds, no scores).

## Verification

`python -B -m unittest test_implementation -v` → **6/6 OK**: K08 clause
verbatim; NO invented elements (word-boundary scan for mission/quest/level-up/
campaign-structure/score-threshold/achievement/leaderboard — all absent);
exactly one decision request with 3 options; framing recovered not invented;
identities pinned (scope sha, contract version, artifact sha256); tampered
contract (wrong scope sha) → loud ExtractionFailure.

## Falsifier scorecard

- Quoted clause not reproducing: NOT FIRED (extraction asserts both quotes at
  run time; the goal-line matcher caught its own wrap bug during development
  and was fixed to normalize whitespace — recorded honestly).
- Invented objective element: NOT FIRED (banned-element scan green).
- More/fewer decision requests: NOT FIRED (exactly one).
- Identity mismatch: NOT FIRED (tamper test refuses).

## Bounds honored

Read-only over the ONT-P01 review checkout artifact + MONKEY_RUN.md; CPU-only;
own workspace; no campaign, no scope change, no edits to any record.
