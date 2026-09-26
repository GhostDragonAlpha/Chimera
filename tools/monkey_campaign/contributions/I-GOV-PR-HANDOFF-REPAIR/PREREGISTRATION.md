# PREREGISTRATION — I-GOV-PR-HANDOFF-REPAIR (correction attempt)

Card: `I-GOV-PR-HANDOFF-REPAIR` (planning P01, governance support; does not close
P01 or alter scope). Correction attempt `1ccb4bcdcddc4cf39c16a3fd1289e7c8`,
agent `c95e1722350849bca846b237c1f60997`, criteria
`71c0089538a563ea19173cd7e60604c150c51603e8538b3d1dad724fc92ecf9c`.
Responds to lead correction `msg-a5dc3bf59c41441c89676dced7a37dc0` (CHANGES
REQUIRED on PR #128 @ 8594a5fc). Written BEFORE the reconciliation probe ran.

## The correction decision (derived from the lead's message + current code)

PR #128 repaired two PR #116 review findings (D1 explicit-routing wrong-card,
D2 prose-only PR-request bridge) against the OLD workflow. The installed
astra-0017..0026 workflow already contains the successor machinery:

- **D2 is superseded**: `continuous_cycle.request_publication` + `worker_start
  --request-pr` implement the durable PR-request handoff (exact identity,
  idempotence, next-card transition, no credentials). Live proof: this same
  agent used `--request-pr` four times earlier TODAY (requests
  `publication-3c5e99f9…`, `publication-e371340a…`, `publication-da5f190d…`,
  `publication-32e57764…`), each recording `PUBLICATION_REQUESTED` and
  returning the next card.
- **D1 is superseded by an explicit-refusal + park protocol**: current
  `continuous_cycle.join` filters candidates to the requested card and, when
  the worker holds other WORKING work, REFUSES by name
  (`checkpoint_active_work_before_switch`) instead of silently returning
  another card. PR #128's AUTOMATIC displacement contradicts astra-0022
  ("No automatic parking or other worker takeover is permitted") and must not
  be installed.

Per the lead's instruction, the deliverable is therefore a **no-change
reconciliation receipt** with a probe proving the original defects cannot
reproduce against the CURRENT modules in an isolated registry — not the
obsolete patch.

## PREDICTIONS (not yet measured by this attempt)

Against current `E:/PythonChimera/tools/monkey_campaign` modules in isolated
temp registries configured like production (`continuous_cycle`,
`separate_review_lane`, `TEN_PERSISTENT_SLOT_BRANCHES`):

1. **D1 cannot reproduce**: explicit request for card X while other work is
   WORKING raises the named refusal `checkpoint_active_work_before_switch`
   and returns NO card packet; an explicit request with no other active work
   returns exactly card X; after parking, an explicit request for a card with
   a pending publication request never returns a different card (no packet
   with `task_id != X` is ever produced by an explicit request for X).
2. **D2 cannot reproduce**: `request_publication` records a durable request
   bound to attempt/criteria/artifacts, flips the attempt to
   `PUBLICATION_REQUESTED`, is idempotent for the same artifacts
   (`REQUEST_ALREADY_RECORDED`, same request id), refuses a wrong criteria
   hash by name, and the next generic join returns a DIFFERENT card — all
   offline (registry file ops only).
3. **Invariants**: board capacity stays 10; every card's `criteria_sha256` is
   unchanged by joins/requests/parks; no attempt of ANOTHER agent is ever
   touched (auto-displacement absent).

## FALSIFIER

Any probe outcome deviating from 1–3 (a wrong card returned by an explicit
request, a trapped worker, a masqueraded request, or changed
criteria/capacity) FAILS the reconciliation and means PR #128 (or a minimal
subset) is still needed — that would be reported, not smoothed over. Lying
about the live-session evidence, or editing any production registry/module,
also fails. No production edits occur; all probes run in `tempfile` registries.

## BOUNDS

CPU-only; stdlib + the campaign modules imported read-only from
`E:/PythonChimera/tools/monkey_campaign`; isolated temp registries; no
credentials, no network, no process control; ≤16 MiB output.
