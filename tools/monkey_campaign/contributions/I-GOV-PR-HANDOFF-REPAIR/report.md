# Report — I-GOV-PR-HANDOFF-REPAIR (PR #116 worker handoff + explicit routing)

- **Attempt:** ad0b478dfafe4b7f8fc471edb5571ea0 (arrival-f4b9cb2857a0457ab737de76eed3af12)
- **Criteria sha256:** 71c0089538a563ea19173cd7e60604c150c51603e8538b3d1dad724fc92ecf9c
- **Pinned review target:** PR #116 head `8730d3841c00cc7c6732d7e4ec702044c4f7f586`
  (review: E:/Chimera/pr-review-20260925/REVIEW.md — two "changes required" findings)
- **Date:** 2026-09-25 · Governance support card; does not close P01, no scope change.

## Summary

Both review findings were reproduced against the pinned PR #116 `kanban.py` in an
isolated temporary registry (`probe_defects.py reference` → exit 2), repaired in a
self-contained patch (`proposed.patch`, 3 files), and verified: the same probe against
the patched code exits 0, and a 14-test suite covers every scenario the card requires
plus the falsifiers. No production registry, code or credentials were touched.

## Reproduction (pinned code, isolated registry)

- **D1** (finding 1): submit T0 → join T1 → revisit T0 → **explicit request for T1
  returned T0**; two WORKING attempts coexist after the revisit.
- **D2** (finding 2): the documented PR-request bridge is prose-only — after posting
  the request message the attempt stays WORKING and the next generic poll **returns the
  same card**; no request state, no transition, no fulfilment path.

## The repair (proposed.patch — apply at repo root, `git -c core.autocrlf=false apply`)

1. `tools/monkey_campaign/kanban.py`
   - **Explicit selection** now matches the worker's own attempt on the requested card
     in any active state (`WORKING`, `PAUSED`, `PR_SUBMITTED`, `PUBLICATION_REQUESTED`)
     — an explicit request always resolves to the requested card, never another.
   - **Checkpointed transition** (`displace_working`): resuming or starting a card
     parks the *same worker's* other WORKING attempts as `PAUSED` with a recorded
     `auto_displaced_by_explicit_task_selection` checkpoint. Only own attempts
     transition; another worker's attempts are never touched.
   - **`request_publication`**: durable PR-request handoff — verifies ownership,
     criteria hash and a full 40-hex head; requires checkpoint + `writes_stopped`;
     records an idempotent request (same identity → same `pub-…` id,
     `REQUEST_ALREADY_RECORDED`); a new head supersedes the worker's earlier open
     request while preserving it; moves the attempt to `PUBLICATION_REQUESTED`; never
     touches card state, `prs`, reviews or messages; needs no network or credentials.
   - **`fulfil_publication`** (lead-only): records the real PR against the verified
     request identity through the same `_record_pr` core as `submit` (refactored, not
     duplicated); idempotent (`ALREADY_FULFILLED`); the PR then follows the normal
     review/merge path exactly.
   - Generic-join exclusion extended so requesting workers are never re-served their
     requested card; they get the next eligible card.
2. `tools/monkey_campaign/worker_start.py` — new `--request-pr <json>` handoff wired
   exactly like `--submit-pr`/`--park` (identity check, size limit), then next card.
3. `tools/monkey_campaign/KANBAN.md` — the bridge paragraph now documents the real
   durable mechanism instead of the inbox-message prose that was never implemented.

## Verification evidence

| Command | Result |
|---------|--------|
| `python -B probe_defects.py reference` | **2 defects reproduced, exit 2** (matches the review exactly) |
| `python -B probe_defects.py patched` | **0 defects, exit 0** — explicit T1 returns T1; single WORKING attempt; request moves worker to T1 `ASSIGNED` |
| `python -B -m unittest test_repair -v` | **14/14 OK in 0.358 s** (isolated temp registries only) |
| `python -m py_compile patched/kanban.py patched/worker_start.py` | OK |
| `git -c core.autocrlf=false apply --check proposed.patch` (on pinned extracts) | OK; applied output **byte-identical** to `patched/*` (round-trip verified) |

Tests cover the card's required scenarios: T0→T1→revisit T0→explicit return T1;
request → next card without REST credentials (pure local call); stale head/criteria
refusals (`criteria_changed`, `full_request_head_required`, `wrong_attempt_owner`,
`request_checkpoint_and_stopped_writes_required`); idempotent retries + supersession
preservation; ten-card capacity and all criteria hashes unchanged; request never sets
REVIEW/DONE, never creates a `prs` entry, never resolves messages; explicit revisit of
a requested card preserves the outstanding request; lead fulfilment refusals
(`request_head_changed`, `lead_action_required`, `unknown_publication_request`);
merge still requires an ACCEPTED review (`merged_head_not_approved`); worker
`--submit-pr` path unchanged (`PR_RECORDED`/`PR_ALREADY_RECORDED`).

## Falsifier outcomes

F1 wrong card — not fired (explicit T1/T2 return T1/T2). F2 trapped worker — not fired
(next card after request). F3 masquerade — not fired (request leaves card OPEN, `prs`
empty; merge still gated). F4 identity hole — not fired (all four refusals tested).
F5 capacity/criteria drift — not fired (capacity 10, criteria hashes identical
before/after). F6 cessation fabrication — not fired (displacement is own-attempts
only, tested with a second worker). F7 non-reproduction — not fired (both defects
reproduced first).

## Failures encountered during development (preserved)

- Probe D2 initially polluted by D1's leftover WORKING attempt — fixed with a fresh
  registry per defect.
- My first `join()` restructure left explicit new-card selection falling into the
  generic resume loop (2 test failures) — restructured so explicit selection always
  resolves to the requested card, with displacement applied only once assignment is
  certain. Found by the suite, not by inspection.

## Remaining gates

Independent review; lead applies the reviewed patch to the live workflow code and
verifies deployment (separate from this card). Nothing here changes card criteria,
review/merge authority, or the ten-card capacity. New output ≈ 130 KB ≪ 16 MiB; every
test invocation < 1 s ≪ 120 s; CPU-only.
