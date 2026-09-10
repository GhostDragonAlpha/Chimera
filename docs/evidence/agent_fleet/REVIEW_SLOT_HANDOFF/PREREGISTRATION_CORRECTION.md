# Capacity and correction-flow correction

Recorded after root review of the written preregistration and private draft, and
before executing any candidate tests.  This supersedes two predictions in the
first preregistration.

A detached REVIEW (`state=REVIEW`, `slot=None`, with a valid handoff receipt) does
not consume an agent's execution capacity.  It remains an active scope barrier,
so overlapping claims are still refused.  The extension overrides `claim` by
copying the base authorization, qualification, dependency, scope, slot-kind, and
return behavior and changing only the active-capacity predicate to exclude a
detached REVIEW.  It does not temporarily change task owner or state.  Tests must
compare all base claim gates and show two detached PR reviews do not exhaust a
worker's capacity for executable work.

A correction request does not allocate a slot inside `review_requeue` and does
not require the previous submitter to remain available.  The lead/current-epoch
transition changes a detached REVIEW to READY, retains submitter and review
identity in history, sets owner/slot/head to null, records the reviewed head as
`correction_base_head`, and cancels only target pending integration requests.
Generation remains unchanged at requeue because generation counts claim
incarnations.  A subsequent ordinary authenticated `claim` by the same or another
qualified agent allocates a matching free slot and increments generation exactly
once.  Normal `provision_slot` must then bind the materialized correction
worktree at `correction_base_head`.

The corrected design is falsified if detached reviews consume execution capacity,
cease blocking overlapping scope, claim loses any inherited gate, requeue needs a
free slot or live old owner, requeue itself increments generation, or ordinary
claim cannot allocate/increment exactly once for a qualified replacement.
