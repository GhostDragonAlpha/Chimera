# Duty Mode — run EXACTLY ONE cycle, honestly, then hand off

The authoritative procedure is `CYCLE_PROMPT.md` at the workspace root — open it and follow
it EXACTLY (branches A > B > C > C2 > D, first match wins). Improvise nothing. This file adds
only the hard token rules and the branch summary:

- **A**: human wrote approved/vetoed in `Chimera/docs/PENDING_HEURISTICS.md` -> promote/tombstone.
- **B**: human gave a playtest temperature -> record verbatim, attribute, present the table.
- **C**: execute the FIRST executable NEXT item in `task_progress.md` (skip `capable sessions
  only` items if you are a weak session; skip items without recipes).
- **C2**: NEXT empty -> `python -m core.rehearsal --candidates-file docs/rehearsal_candidates.json
  --decide`, then execute the item it wrote (respect capable-only marking).
- **D**: fallback pipeline health check (`python run_deep_space_trader_pipeline.py`;
  requires `lms load qwen3.6-35b-a3b-mtp@iq2_m` first). Record UBT verbatim.

TOKEN RULES (hard): never read a file wholesale — grep/head with limits; do not re-read files
you just wrote; view at most 1 screenshot; quote <=5 lines of any tool output. STOP RULE: any
step failing twice -> record pathway failed -> note in task_progress.md -> proceed to postflight.
A recorded failure is a successful cycle. A sharp C outranks a fake A.

NEVER SKIP the close: postflight -> dream_loop -> task_progress prepend -> git add/commit/push.
