# Continuous ten-slot work cycle

Keep the same arrival ID. Execute the returned assignment, then immediately call
startup again through the appropriate handoff command. Do not end after a report
while another useful assignment is available. Commands return the next assignment;
the host agent must execute it. These helpers do not launch an AI model themselves.

1. Implement or correct a card in its isolated attempt workspace. Read its ontology
   packets and task inbox. Preserve criteria and resource limits.
2. For a candidate awaiting lead publication, fill publication_request_template with
   the actual file paths and raw SHA-256 hashes and use:
   `worker_start.py --arrival-id YOUR_ID --request-pr candidate.json`
   This records PUBLICATION_REQUESTED, preserves the candidate and assigns next work.
   A candidate request is not a GitHub PR. Lead publication is still required.
3. For an actual PR, use the existing --submit-pr handoff. Only verified merged PRs
   close/refill cards. A submitted PR occupies its slot while workers move onward.
4. Once no eligible implementation remains, startup assigns an independent PR review
   at a pinned head. When all ten cards have PRs, review is the remaining work cycle.
   Rerun appropriate checks, inspect actual visual evidence where required, and retain
   failures. Missing native/visual evidence is a gap, never a synthetic PASS.
5. Fill review_result_template and invoke:
   `worker_start.py --arrival-id YOUR_ID --review-result review.json`
   This returns the next assignment. CHANGES_REQUIRED reopens correction work. PASS
   records a recommendation; it never fabricates lead approval or a GitHub merge.
6. The lead reviews verification receipts, publishes/merges acceptable exact heads,
   and records the verified merge to refill each slot. The next task keeps that
   slot's numbered branch and receives its own ontology binding and criteria hash.

An explicit switch away from active work requires a saved checkpoint and --park.
No other worker is stopped, expired or impersonated. Do not review your own PR as
independent. If all eligible work is awaiting lead publication/merge, or only your
own PRs remain, preserve state and report that exact gate rather than loop wastefully.
Actual task/resource blockers remain valid; do not invent tasks to conceal them.
The cancelled timer remains cancelled; these transitions happen when workers or
the operator-engaged lead invoke the system.
