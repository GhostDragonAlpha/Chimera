# PREREGISTRATION — I-GOV-PR-HANDOFF-REPAIR (PR #116 worker handoff + explicit routing)

- **Attempt:** ad0b478dfafe4b7f8fc471edb5571ea0 (arrival-f4b9cb2857a0457ab737de76eed3af12)
- **Criteria sha256:** 71c0089538a563ea19173cd7e60604c150c51603e8538b3d1dad724fc92ecf9c
- **Pinned review target:** PR #116 head `8730d3841c00cc7c6732d7e4ec702044c4f7f586`
  (review: E:/Chimera/pr-review-20260925/REVIEW.md, "changes required", two findings)
- **Frozen:** 2026-09-25, before any patch edit. Governance support card; does not
  close P01 and does not alter game scope.

## STATEMENT

PR #116's kanban routing has two reproducible defects: (1) an explicit task request for
a card where the same worker already holds a WORKING attempt returns the wrong card
(the explicit lookup only matches PAUSED/PR_SUBMITTED, then the generic loop returns
the worker's first WORKING attempt anywhere), and revisiting one task while working
another leaves two WORKING attempts with no defined transition; (2) the documented
PR-request bridge exists only as prose — posting a request leaves the attempt WORKING,
so the worker's next poll returns the same card (trapped), and no durable request
record, identity verification, or lead fulfilment path exists. Both are repairable in
kanban.py + worker_start.py without changing criteria, capacity, or review/merge
authority.

## PREDICTIONS (falsified-by-run)

- **PD1:** with the pinned kanban.py in an isolated registry, the sequence
  submit-T0 → join-T1 → revisit-T0(explicit) → request-T1(explicit) returns T0, and
  after the revisit the worker holds two WORKING attempts.
- **PD2:** with the pinned kanban.py, after a worker signals a PR request (any
  inbox-message form), a generic poll returns the SAME card again, because the
  attempt is still WORKING; there is no request state or transition.
- **PD3 (post-repair):** the same sequences against the patched code return T1 for an
  explicit T1 request, hold at most one WORKING attempt per worker (displaced attempt
  becomes PAUSED with a recorded checkpoint), move a requesting worker to a different
  card on the next poll, refuse stale criteria/head identity, treat repeated identical
  requests and fulfilments idempotently, and leave card criteria, slot count and
  ten-card capacity unchanged. A request never sets REVIEW/DONE, never creates a
  `prs` entry, and never resolves messages.

## FALSIFIERS (named before the run)

- **F1 wrong card:** patched explicit request for T1 returns anything but T1's
  existing attempt for that worker → repair failed.
- **F2 trapped worker:** after request_publication, the worker's next generic join
  returns the requested card again → repair failed.
- **F3 masquerade:** a publication request changes card state to REVIEW/DONE, creates
  a prs entry, marks an attempt WON/SUPERSEDED, or resolves an inbox message → repair
  failed (a request is never a submission or a merge).
- **F4 identity hole:** a request with wrong criteria_sha256, wrong agent, or a
  non-40-hex head is accepted → repair failed.
- **F5 capacity/criteria drift:** refill behavior, slot numbering, ten-card capacity,
  or any card's criteria hash changes due to the patch → repair failed.
- **F6 cessation fabrication:** the patch manufactures cessation of ANOTHER worker's
  attempt (only the requesting worker's own attempts may transition) → repair failed.
- **F7 non-reproduction:** if PD1/PD2 do not reproduce against the pinned code in an
  isolated registry, my premise is wrong and the repair must stop and report instead.

## Probes (frozen)

- probe_defects.py against reference/kanban.py (pinned bytes) in a temp registry:
  reproduce PD1 and PD2, print observed states.
- test_repair.py against the patched code in isolated temp registries: PD3 plus all
  card-required scenarios (explicit return; request → next work without REST
  credentials — no network use at all; stale head/criteria refusal; concurrent/
  repeated retries; ten-card capacity preservation; request-not-merge invariants;
  outstanding lead messages preserved across request retries).

## Bounds

- CPU-only isolated temp registries; no production registry edits, no credentials,
  no network, no models, no process control; each test invocation ≤ 120 s;
  new output ≤ 16 MiB. The patch is proposed only — the lead applies it.
