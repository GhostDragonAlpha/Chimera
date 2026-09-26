# ONT-P03 — ledger reconciliation report

**Verdict: the live campaign ledger reconciles read-only: 23 cards tabled,
8 DONE with full winner receipts, 10 awaiting lead publication/review/merge
with recorded request receipts — and exactly TWO named identity gaps
(ONT-P06, ONT-X01: never-claimed cards with no owner), reported by the tool
as the card's work product. Zero silent gaps.**

- Card `ONT-P03`, attempt `309c75627a4d415e8d55707c0f65c9d5`, agent
  `c95e1722350849bca846b237c1f60997`, criteria
  `1fcf0eea7c11d4d6346a27b09c88bf7144dff9219ff1c0de7f77505e27b5f391`.
- Preregistration written before the run; prior completed work REUSED as
  recorded (winners, reviews, publication requests) — nothing re-derived.

## The reconciliation tool

`implementation.py::reconcile(registry_root)` — opens the live registry
READ-ONLY through `agent_slots.Registry`, tables every card with the four
ledger identities (owner = attempt agents; source revision = criteria hash +
winner head/merge/PR; scoped verdict = card state + recorded review verdicts
+ publication-request states; receipt = PR URLs, merge SHA, publication-request
ids with artifact counts, review records), and names any missing identity
(`missing[]` per card; `awaiting` classification: lead_publication /
review_or_merge). Output: `reconciliation.json` (full table) + stdout summary.

## Measured against the LIVE registry (2026-09-25)

```
card_count: 23
done_with_winner: 8                      (merged PRs incl. #117-#120, #126, #127)
cards_awaiting_lead_publication: 7       (this session's publication requests,
                                          each with artifact receipts)
cards_awaiting_review_or_merge: 3
cards_with_missing_identities: 2         -> GAP ONT-P06 ['owner:no_active_attempt']
                                          -> GAP ONT-X01 ['owner:no_active_attempt']
```

Spot-verified rows: DONE cards carry winner head+merge+PR and recorded
ACCEPTED reviews (e.g. R5-forest-review: 5 review records incl. this agent's
ACCEPTED at head `7467bed2`; ONT-P01: 2 ACCEPTED); this session's candidates
appear as PENDING publication requests with artifact counts (e.g.
I-R02-SAVE-STORE-FOLLOWUP `publication-3c5e…`, 4 artifacts). Competing
attempts on one card are legal per KANBAN and are tabled per-owner, not
flagged.

## Tests (4/4 OK)

Fixture registries: unclaimed card → owner gap reported (never silent);
claimed card → complete identities; winner + recorded review → receipts and
awaiting classification tabled; live-registry structure check (23 cards, 8
winners, gaps == missing_detail length).

## Falsifier scorecard

- Silent missing identity: NOT FIRED (the two gaps are the finding).
- Fabricated identity: NOT FIRED — every field read from the live registry;
  spot-checks quoted above.
- Registry write: NONE (read-only open by construction).
- Claimed pass unsupported by records: NOT FIRED — the tool claims only what
  the table shows; the two owner gaps are REPORTED, not resolved by fiat
  (claiming them is dispatch work, not ledger work).

## Work product for the lead

The two never-claimed cards (ONT-P06, ONT-X01) are the ledger's actual gaps:
they need assignment/dispatch (or explicit backlog deferral) to satisfy
"every active task has one owner". The reconciliation tool reruns
deterministically as the standing ledger check.
