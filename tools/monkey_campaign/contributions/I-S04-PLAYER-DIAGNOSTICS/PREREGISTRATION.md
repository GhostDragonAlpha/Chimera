# PREREGISTRATION — I-S04-PLAYER-DIAGNOSTICS

Attempt: d24bd30d38234a4cae33288048cce14f · branch-9 · pinned source revision
9afbddcd90164b5544a16fd0bc72278d985eb6e3 (monkey-play: F08 integrated).
Written BEFORE any implementation edits (Rule 0: state it before you build it).

## STATEMENT (someone could disagree with this)

A stdlib-only, deterministic, headless translation module can cover the REAL named
refusal/failure identities of the pinned product modules — `input_settings.py`,
`session_flow.py`, keyed against the U06 prompt states in `state_feedback.py` at the
pinned revision — such that every player-facing message offers only actions those
modules actually support, every unexpected error falls to an honest fallback carrying
a deterministic correlation ID, and no player-facing text ever contains a local path,
username, environment variable, or stack detail (developer traces live in a separate
diagnostic field only). Disagreement would say: the named refusals are too entangled
with engine internals to translate without inventing capability, or that a fallback
needs wall-clock/nonces from the OS to be collision-safe. Both are testable claims.

## PREDICTION (not yet measured)

1. The pinned revision contains a bounded, countable set of named refusal identities
   across `input_settings.py` and `session_flow.py` — predicted on the order of 5–20
   distinct named states/failure identities (exact count measured only during the
   inventory step, after this file is frozen).
2. Every one of those named identities can be translated WITHOUT inventing climbing
   capability or new physical behavior — the U06 five prompt states (available climb,
   unavailable support, holding, falling, recovery) in `state_feedback.py` are
   sufficient as the action vocabulary.
3. Same input → byte-identical output records (determinism), including the
   correlation ID derived as sha256 over the error text + a caller-supplied nonce —
   no wall clock, no `random`, no environment reads.
4. Unknown/unexpected errors NEVER map to success and always carry a correlation ID.

## FALSIFIER (named before the run — the card's authority, verbatim)

Any ONE of these fails the build, regardless of anything else passing:

- F1: the player receives raw local paths (`E:\...`, `C:\Users\...` style substrings
  in player-facing text).
- F2: a message claims an unsupported action (an action the pinned modules' real
  states do not offer).
- F3: unknown errors silently report success (an unrecognized error string mapped to
  a success-shaped or known-refusal-shaped record instead of the honest fallback).

Supporting gate (not a substitute for F1–F3): determinism — same input must produce
byte-identical output; a first-run test failure is recorded honestly in receipt.json,
never tuned away silently.

## SCOPE GUARDS

- Map ONLY supported states; no new physical behavior, no climbing capability invented.
- Stdlib only, Python 3.11+, headless, deterministic; no network/GUI/training.
- Source repo `E:/ChimeraWork/monkey-play-20260924` is READ-ONLY (`git show` only);
  extracted reference bytes go to `WS/reference/` with sha256 ledger, read-only after.
- Existing equivalents at the pinned revision are checked first (`git grep` over
  `tools/monkey_campaign/product/*.py` for user-message/translation helpers); build on
  what exists rather than duplicate.
