# Correction-head provisioning gate — preregistration

Recorded after review of the first green candidate runs and before adding or
running the tests below.  It narrows authenticated controller behavior; it does
not claim that the controller fences arbitrary filesystem or process access.

## Statement

After a detached review is requeued or recovered and a replacement claims it,
the reviewed commit is only a required materialization receipt until
`provision_slot` verifies that exact `correction_base_head`.  Before that gate,
the claimed task may checkpoint preservation notes, but its authenticated task
API cannot obtain runtime resources or submit another review.

## Prediction

`resource_request`, legacy `resource_acquire`, and `submit_review` for the exact
owner/generation will refuse `correction_provision_required` without changing
the registry.  A wrong actor/generation still gets the inherited claim-identity
refusal.  Exact-head `provision_slot` removes the pending marker; normal resource
admission and review submission then resume.  Restarting the extension from the
same schema-1 SQLite registry preserves a detached handoff and its subsequent
correction/recovery fields.

## Falsifiers

The statement loses if any named operation succeeds before provisioning,
mutates the registry on refusal, masks a stale/foreign claim as a provisioning
error, stays blocked after exact provisioning, or if restart loses the frozen
review/handoff receipt or prevents replacement claim from the recorded head.
