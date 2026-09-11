# DRAFT PACKET — holodeck-gov-05 — from catalogue card GOV-05

STATUS: DRAFT (PLANNING DATA for the lead — NOT ADMITTED; this lane never calls create_task; nothing here claims acceptance, integration or approval)

- SOURCE: card GOV-05, plane=card, catalogue digest `b9d32319b43a03bbb713f1a4e6120f24065839f15383b0729fb587ba04f9000a` (imported_revision 651, epoch 5), content_sha256 `d0f492ac4aaf212a3bd5498f348ba21031c0c4122c43db538c62bd4a2ee4b30c`, source C:\Users\allen\AppData\Local\Temp\import-5199\docs\roadmap\holodeck_tasks.json index 4. Raw read retained at `raw/catalogue_read/GOV-05.json`.
- ELIGIBILITY: BLOCKED-ON: GOV-01 (card depends_on ["GOV-01"]; at drafting time none of these is an INTEGRATED live task, so catalogue_next did not offer this card). Becomes eligible only after the dependency chain is INTEGRATED.

## Proposed task fields (for the lead’s create_task — every value is a PROPOSAL)

- **id**: `holodeck-gov-05` (card-derived, path-safe, matches the controller id regex `[a-z0-9][a-z0-9-]{0,63}`; no collision with any live task id)
- **scopes** (PROPOSALS ONLY — the card’s own write_scope field is: "UNRESERVED: coordinator must assign exact exclusive paths before implementation."; only the lead may assign exact exclusive paths; the controller refuses any scope overlapping `chimeraengine/engine/build`, `.git`, absolute or `..` paths):
  - `docs/evidence/agent_fleet/HOLODECK/GOV/GOV-05`
- **capabilities**: `cpu`, `docs`, `python`
- **dependencies** (card graph mapped to draft ids; the lead must admit these tasks first — create_task refuses dependencies that do not exist): `holodeck-gov-01`
- **kind**: worker

## FULL PACKET TEXT (draft `packet` argument)

Realize catalogue card GOV-05 "Crash recovery and publication" (domain GOV, kind engineering) at reference revision: catalogue import b9d32319b43a (source C:\Users\allen\AppData\Local\Temp\import-5199\docs\roadmap\holodeck_tasks.json index 4, content_sha256 d0f492ac4aaf212a3bd5498f348ba21031c0c4122c43db538c62bd4a2ee4b30c).

**Theory membrane — drafted from the card’s own gates (verbatim card fields; the admitting agent must prereg its own concrete numbers/thresholds before any implementation test):**

- CARD STATEMENT: Recovery journal and serialized integration procedure
- CARD PREDICTION: Replay reconstructs accepted task state without overwriting unpublished work
- CARD FALSIFIER: Duplicate publication or orphaned ownership changes task truth
- CARD MATHEMATICS: event sourcing; content addressing; idempotence
- CARD THRESHOLD POLICY: Derive the fixture-specific bound or ratify product target before implementation tests; preserve existing frozen gates; a catalogue prediction is not a preregistered numeric certificate.
- CARD DYAD POLICY: REQUIRED when integrated changes affect visible behavior; GLM operates the documented image/question workflow. Reference-only or source-only scope records NOT_APPLICABLE with reason.
- CARD DELIVERABLES:
  1. Recovery journal and serialized integration procedure
  2. Independent reference/benchmark and executed negative controls appropriate to this scope
  3. Reproduction commands, source identity, preserved evidence and limitations
  4. Integration contract and full autonomous handoff

**Scope note:** the card reserves no paths itself (write_scope: "UNRESERVED: coordinator must assign exact exclusive paths before implementation."). The scope proposed above is the evidence/records home; the lead assigns the exact exclusive implementation paths when admitting this task, under the controller path-scope rules.

**Falsifier (named before the run, from the card):** Duplicate publication or orphaned ownership changes task truth

Acceptance: NOT CLAIMED. This draft is planning data; admission, execution, evidence and acceptance run only through the lead-authorized task lifecycle (create_task → claim → prereg → run → submit_review → review → integration).

