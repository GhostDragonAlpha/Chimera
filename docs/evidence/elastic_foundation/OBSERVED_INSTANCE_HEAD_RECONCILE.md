# HEAD_RECONCILE — observed instance (buffy-02, 2026-09-10)

The `fleet-head-reconcile-01` task packet describes this exact failure mode and
asks for a read-only instrument. This note records the instance that actually
happened to me while resubmitting my two owned tasks, so the next agent does
not have to rediscover it. It is an OBSERVATION, not an implementation of the
task (the task is integration-scoped and lead-only; I could not claim it).

## What happened

I recovered as `buffy-02` and asked the controller for my tasks. It reported:

- `elastic-ref-publish` — state REVIEW, gen 6, **head `1896c721`**
- `master-catalogue-sync-01` — state RUNNING, gen 3, **head `c324df8d`**

But the actual worktrees were already ahead of both recorded heads:

| slot | worktree branch | actual HEAD | controller head | gap |
|---|---|---|---|---|
| 02 | elastic-ref-publish | `9877179b` (gen 6) | `1896c721` (gen 5) | +1 generation, evidence-only |
| 04 | master-catalogue-sync-01 | `3c08f56d` (gen 4) | `c324df8d` (gen 3) | +1 generation, validator hardening |

The controller's recorded heads were **stale by exactly one generation on both
tasks**, and the remote had moved further still (elastic remote `fc5711eb`,
catalogue remote `c324df8d`).

## The mechanism

`control.py` `review_requeue` clears the head and bumps the generation, but the
**agent's own checkpoint/submit_review calls use the generation the agent
remembers**, not the one the controller now holds. My `submit_review(gen=6)`
was refused with `stale_or_foreign_claim` because the task was already gen 7 by
then. The recorded head is only ever written by `submit_review`, so a requeue
that nobody re-submits from leaves the head frozen at the pre-requeue value.

The commits themselves were legitimate and mine: `9877179b` is an evidence-only
append over `1896c721` (one GPU_VALIDATION_GAP.md, no source change), and
`3c08f56d` is a validator hardening commit. Neither was destructive or
foreign.

## What I did (the manual reconcile the instrument would automate)

1. Read the controller snapshot + events to learn the current generation
   (elastic gen 7, catalogue gen 4) and that the head had been cleared.
2. Verified ancestry and identity per worktree: `git merge-base --is-ancestor`
   of the recorded head under the actual head, and `diff --stat` from the
   merge-base to confirm the delta was evidence/scope-only.
3. Re-ran each task's own acceptance battery **on the actual worktree HEAD**
   (never on the recorded head): run_falsify 19/19 + pytest 7 + demo_sheet for
   elastic; 52 passed for the catalogue.
4. Found and fixed one real defect my own scope falsifier caught (the fixture
   verifier was outside the declared scopes) and one real test failure in the
   committed catalogue head (an empty test stub).
5. Committed, pushed, verified `remote head == local head` for both, and
   re-submitted with the controller's current generation.

## The part that should not need me

Steps 1-3 are mechanical and read-only. The instrument the task asks for would
do them and report "safe evidence-only append, continue the existing valid
claim" — which is exactly what happened here. The only thing requiring judgment
was step 4 (finding genuine defects), and step 5 (submitting at the right
generation).

Note also: `submit_review` requires `state == RUNNING`, so a task sitting in
REVIEW cannot be checkpointed — the controller must requeue it first. I hit
`task_not_owned_active` trying to checkpoint an already-reviewed task.

## Related open item

`fleet-slot-binding-01` depends on `master-catalogue-sync-01` and is READY once
the lead integrates it. Its scope is the controller, a slot-binding test, and a
SLOT_BINDING evidence dir. Slot-01 is free.