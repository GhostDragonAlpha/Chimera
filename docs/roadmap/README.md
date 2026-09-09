# Living blueprint — review and adoption

This directory is part of the Chimera repository proposal, not a second live
ledger. `docs/THE_MASTER_LIST.md` remains the operational entry point after
coordinated adoption. The catalogue and generated book describe future work;
they do not reassign the five current agents.

## Files and purpose

- `docs/THE_HOLODECK_BLUEPRINT.md`: the human-readable book, 240 cards/40 domains.
- `docs/roadmap/holodeck_tasks.json`: canonical new card definitions and source snapshot.
- `tools/roadmap_query.py`: read-only validation, search, task display and prompt generation.
- `docs/roadmap/blueprint_validation.json`: structural/tool checks only.
- `docs/THE_MASTER_LIST.md`: proposed Master list against the inspected base.

## Coordinated adoption

This draft PR combines the catalogue with the five-slot control reference.
Current agents continue their assigned work. The base is
`bf0a62162008c8415b88091c671ac180dbb50193`; the unrelated unpublished Master
list edit in ASTRA's source checkout was deliberately not copied or changed.
Review the insertion against the actual integration head before merging.

Read `docs/AGENT_START.md` and `docs/THE_AGENT_FLEET.md`. After activation, the
Master list points to controller state. `roadmap_query.py` only proposes work;
it never claims it. Optional query state is a derived planning snapshot, not
a second writable authority. Deployment and production acceptance remain
separate from this review proposal.

## Read-only query examples

Run from a checkout containing the proposed paths:

```bash
python tools/roadmap_query.py validate
python tools/roadmap_query.py summary
python tools/roadmap_query.py search "pressure"
python tools/roadmap_query.py show INT-03
python tools/roadmap_query.py packet ELA-02
```

`packet` prints a complete proposed operating packet plus the card; it does
not assign an agent or run tools. The coordinator must add actual exclusive
write scope, evidence, numeric thresholds and implementation dependencies.
No API for autonomous claiming or mutating the ledger is implemented here.

An optional reconciled state file is:

```json
{
  "tasks": {
    "GOV-01": {
      "status": "ACCEPTED",
      "evidence": ["replace-with-actual-scoped-review-reference"]
    },
    "MATH-01": {"status": "RUNNING", "owner": "replace-with-actual-owner"}
  }
}
```

This is a format example, not accepted evidence. Never install these example
states as real progress. Then `ready --state <path>` reports eligible planning
candidates. It neither verifies evidence contents nor checks resources, scope
claims or all implementation-specific dependencies. Its output is not work
authorization. Existing active tasks take precedence over catalogue planning.

## How to evolve the cards

Edit the JSON definitions through the coordinator and regenerate the card
appendix before publication. `python tools/roadmap_query.py render-book` emits the regenerated book to
stdout; inspect it in a new file before replacing the old book. Do not
manually change a generated card in the
book alone. Preserve stable IDs; use explicit successor links when splitting
or retiring tasks. Add new physical dependencies and numeric gate references
when a task is activated. Keep current status in the Master list or its linked
coordinator-owned records, not divergent copies in multiple agent checkouts.

All physical-law gates require future task-specific preregistration and tests.
The supplied structural tests do not validate physics, Vulkan execution,
runtime behavior, DYAD or human acceptance.
