# PREREGISTRATION — ONT-P03 (ledger reconciliation)

Card `ONT-P03` (planning P03, group "Scope, identity, and fleet"). Attempt
`309c75627a4d415e8d55707c0f65c9d5`, agent `c95e1722350849bca846b237c1f60997`,
criteria `1fcf0eea7c11d4d6346a27b09c88bf7144dff9219ff1c0de7f77505e27b5f391`.
Written BEFORE the reconciliation tool ran against the live registry.

## STATEMENT (a theory that can lose)

The campaign's own live registry (E:/ChimeraWork/monkey-coordination, opened
read-only through `agent_slots.Registry`) already carries, for every active
task card, the four ledger identities the card demands — owner (attempt
agent), source revision (criteria hash + winner/PR head or attempt workspace
branch), scoped verdict (card state + recorded review verdicts + publication
request states), and receipt (PR URLs, merge SHAs, publication-request ids
with artifact hashes, review results) — such that a deterministic read-only
reconciliation can table every card and name any missing identity explicitly,
reusing prior completed work (merged winners, recorded reviews) rather than
re-deriving it.

## PREDICTION (not yet measured)

1. Reading the live board: ≥20 cards; every card carries a non-empty
   `criteria_sha256` and `id`; every non-DONE card with attempts carries
   attempt identities (id, agent, state, workspace).
2. DONE cards carry winner identities (pr_url + head_sha + merge_commit_sha)
   — the merged PRs #117–#120 and their predecessors.
3. Review-lane cards carry PR records; recorded reviews (PASS/CHANGES) appear
   as review results bound to exact heads (this session's R5 + ONT-P01 PASS
   reviews are among them).
4. This session's seven publication requests appear as PENDING requests with
   artifact receipts (path + sha256) — reconciled as "awaiting lead
   fulfilment", NOT as missing.
5. The reconciliation reports zero cards with a MISSING required identity;
   any card that does lack one is named with the missing field — the tool
   never silently passes a gap (falsifier: "missing identities … fails").

## FALSIFIER

Any active card whose owner/revision/verdict/receipt identity is absent AND
unreported (silent gap); any fabricated identity (a field the registry does
not actually contain); any write to the live registry (the tool is read-only
by construction); or a claimed pass unsupported by the records it cites.
If prediction 5 fails — real missing identities exist — they are REPORTED as
the finding, which is the card's work product, not a probe failure.

## BOUNDS

Read-only over the live registry; CPU-only, stdlib-only; fixture tests in
temp dirs; no production edits; ≤16 MiB output.
