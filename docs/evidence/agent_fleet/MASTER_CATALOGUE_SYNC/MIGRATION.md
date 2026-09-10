# Master catalogue sync — migration instructions for the lead

Task: `master-catalogue-sync-01` (owner buffy-02, slot-04, generation 1).
Packet requirement: the ENTIRE canonical Master list in the controller task
catalogue, imported as tested, idempotent, provenance-preserving planning
data — with no competing live ledger and no mutation of live tasks, claims,
resources or slots.

## What landed

- `tools/agent_fleet/master_catalogue.py` — read-only payload builder:
  parses every card of `docs/roadmap/holodeck_tasks.json` (schema
  `chimera-holodeck-roadmap-v1`) and every L*/B*/H* task row of
  `docs/THE_MASTER_LIST.md` inside THE LINES / THE BACKLOG / THE NEXT HARD
  QUEUE, keeping source path, line number, column content and a content
  sha256 per record. Repeated observations of the same row ID accumulate;
  nothing is deduplicated or dropped. Non-task pipe rows inside the scoped
  sections are reported in `coverage.unresolved` (currently zero on the real
  document); pipe rows elsewhere are counted as
  `pipe_rows_outside_scoped_sections`.
- `tools/agent_fleet/control.py` — additive catalogue plane:
  - `catalogue_import` (current lead + epoch only): validates the payload
    (`validate_payload` refuses duplicates, unknown dependencies, cycles,
    malformed records, empty imports), refuses a repeated identical import
    (`duplicate_catalogue_import`) and a payload that is not built on the
    current import (`stale_catalogue_import`). Refusals roll back: no
    revision bump, no event, zero state mutation.
  - `catalogue_read` (any live agent): record-level read by digest+plane+id.
  - `catalogue_next` (any live agent): planning-only candidates — cards with
    `PROPOSED` status whose dependencies are INTEGRATED live tasks; matches
    live IDs case-insensitively and never creates tasks.
  - `snapshot` carries only the catalogue summary (digest, coverage,
    imports); never the payload body.
- `tools/agent_fleet/test_master_catalogue.py` — isolated-registry suite
  (temp SQLite only; never touches `E:/ChimeraWork/control/state.sqlite`).
- `tools/roadmap_query.py`, `docs/THE_AGENT_FLEET.md`,
  `docs/AGENT_START.md` — wording reconciliation: GLM-only publisher and
  stop-after-task phrasing replaced with the current controller/PR workflow
  policy; the fleet doc documents the catalogue operations.

## Migration steps (lead, current epoch)

1. Build the import arguments (read-only; no controller calls):

   ```bash
   python tools/agent_fleet/master_catalogue.py --out .tmp/catalogue_import.json
   ```

   Expect: `coverage.cards = 240`, `coverage.domains = 40`,
   `coverage.master_row_ids = 41`, `coverage.master_row_observations = 41`,
   `unresolved = []`.

2. Import through the lead's session:

   ```bash
   python tools/agent_fleet/client.py --session <lead-session-path> \
       catalogue_import --arguments .tmp/catalogue_import.json
   ```

   (The arguments file is `{"payload": {...}, "digest": "<64-hex>"}` as
   emitted by step 1.)

3. Verify:

   ```bash
   python tools/agent_fleet/client.py --session <lead-session-path> snapshot
   ```

   `state.catalogue.import.digest` must equal the emitted digest;
   `state.tasks`, `state.resources`, `state.slots` unchanged;
   revision advanced by exactly 1.

## Semantics the fleet can rely on

- Idempotent: re-running step 2 with the same digest is refused with
  `duplicate_catalogue_import` and leaves revision, state and events
  untouched — repeat execution cannot corrupt or duplicate the catalogue.
- Fresh content: build a new payload after editing the sources; import it
  with the CURRENT digest (stale imports refused). Replacement rewrites only
  `state.catalogue`; live tasks/claims/resources/slots are untouched and
  survive controller restart (covered by tests).
- Read path: `catalogue_read {digest, plane: "card"|"master_row", id}`;
  `catalogue_next {digest}` for planning-only candidates. Neither mutates
  state (no revision bump, no event).
- Rollback: the plane is additive; deleting the `catalogue` key from the
  state body (supervisor, offline) removes it without touching anything else.
  No live-plane operation reads the catalogue for authority decisions.

## Test evidence

`RUN_RECORD.json` beside this file records the executed commands, the full
suite result (11/11 catalogue + 36/36 controller tests) and the real-source
coverage/digest from a verification build. All tests ran against isolated
temp registries; the live registry was not imported into, per the packet.
