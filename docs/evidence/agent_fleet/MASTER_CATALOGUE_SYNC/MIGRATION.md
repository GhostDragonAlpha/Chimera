# Master catalogue sync — migration instructions for the lead

> **GEN-11 FRESH-SYSTEM ADDENDUM (2026-09-10, glm53-fresh-01, gen 11, slot 2).** The
> task was recovered for fresh-system testing (controller rev 434) and re-verified:
> full isolated suite **110 passed, 1 skipped**; payload content reproduces exactly
> against the same pinned source hashes (Master `f389f913…`, catalog `d9bb4419…`; 240
> cards / 40 domains / 65 row IDs / 68 observations / 3 unresolved / 271 unkeyed
> requirements / exhaustive 2,430-line partition). One fresh-system falsifier FIRED
> and was corrected: on a stock cp1252 Windows console the old builder crashed with
> `UnicodeEncodeError` on the canonical document's arrows **before writing `--out`**
> (MIGRATION step 1 failed verbatim); the builder now writes the artifact first and
> ASCII-escapes only the console summary (digest unchanged; regression test added).
> Also made explicit here: the payload digest is **transport-reproducible but per-host
> by design** — it embeds the builder-host `source.path` and the ADVISORY (never
> authenticating) `git_commit`; a full structural walk of the gen-7 recorded payload
> vs this rebuild shows ZERO content differences outside those two fields. Step 1
> therefore still must run from the lead's own checkout, as instructed below; that
> is now a stated property, not an accident. Full record:
> `GEN11_FRESH_SYSTEM_RUN_RECORD_20260910.md` (+ its preregistration file).

> **PRIOR ADDENDUM (generation 7, head `c23fd00f`+ gen-7 commit).** The
> sections below were written at generation 1 and are preserved as history.
> The parser has since been generalized (every section, unkeyed requirements,
> exhaustive line partition) and the validator hardened (recomputed manifests
> and counters; catalog text retained and always rebuilt; exact source-index
> enumeration). Current verified coverage at spine `0e878758`: **240 cards,
> 40 domains, 65 master-row IDs, 68 observations, 3 unresolved (identifiable
> actor roster), 271 unkeyed requirements, 2,430-line exhaustive partition**
> — pinned to Master sha `f389f91300f2…`, catalog sha `d9bb441939c0…`.
> `git_commit` fields are ADVISORY provenance, not authentication: a
> well-formed SHA string never proves the payload was produced from that Git
> revision. Tested import arguments for the CURRENT source state are in
> `import_arguments_CURRENT.json` (payload + digest, built by
> `python tools/agent_fleet/master_catalogue.py`); import via
> `POST /v1/action` with `operation: catalogue_import` and those arguments,
> from the current lead's session. Never import a payload whose digest was
> computed against a different source state — rebuild if the Master changed.

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
