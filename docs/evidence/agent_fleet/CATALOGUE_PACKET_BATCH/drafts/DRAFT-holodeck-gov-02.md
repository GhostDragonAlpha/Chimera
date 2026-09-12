# DRAFT PACKET — holodeck-gov-02 — from catalogue card GOV-02

STATUS: DRAFT (PLANNING DATA for the lead — NOT ADMITTED; this lane never calls create_task; nothing here claims acceptance, integration or approval)

- SOURCE: card GOV-02, plane=card, catalogue digest `b9d32319b43a03bbb713f1a4e6120f24065839f15383b0729fb587ba04f9000a` (imported_revision 651, epoch 5), content_sha256 `46a03c8e5f7b829b3b920494abb74a4444c819eb91c6b9364f2fca357da2fc78`, source C:\Users\allen\AppData\Local\Temp\import-5199\docs\roadmap\holodeck_tasks.json index 1. Raw read retained at `raw/catalogue_read/GOV-02.json`.
- ELIGIBILITY: BLOCKED-ON: GOV-01 (card depends_on ["GOV-01"]; at drafting time none of these is an INTEGRATED live task, so catalogue_next did not offer this card). Becomes eligible only after the dependency chain is INTEGRATED.

## Proposed task fields (for the lead’s create_task — every value is a PROPOSAL)

- **id**: `holodeck-gov-02` (card-derived, path-safe, matches the controller id regex `[a-z0-9][a-z0-9-]{0,63}`; no collision with any live task id)
- **scopes** (PROPOSALS ONLY — the card’s own write_scope field is: "UNRESERVED: coordinator must assign exact exclusive paths before implementation."; only the lead may assign exact exclusive paths; the controller refuses any scope overlapping `chimeraengine/engine/build`, `.git`, absolute or `..` paths):
  - `docs/evidence/agent_fleet/HOLODECK/GOV/GOV-02`
- **capabilities**: `cpu`, `docs`, `python`
- **dependencies** (card graph mapped to draft ids; the lead must admit these tasks first — create_task refuses dependencies that do not exist): `holodeck-gov-01`
- **kind**: worker

## FULL PACKET TEXT (draft `packet` argument)

Realize catalogue card GOV-02 "Capability and evidence registry" (domain GOV, kind engineering) at reference revision: catalogue import b9d32319b43a (source C:\Users\allen\AppData\Local\Temp\import-5199\docs\roadmap\holodeck_tasks.json index 1, content_sha256 46a03c8e5f7b829b3b920494abb74a4444c819eb91c6b9364f2fca357da2fc78).

**Theory membrane — drafted from the card’s own gates (verbatim card fields; the admitting agent must prereg its own concrete numbers/thresholds before any implementation test):**

- CARD STATEMENT: Per-device and per-law support records with independent evidence classes
- CARD PREDICTION: Missing runtime or DYAD evidence remains unknown regardless of unit-test success
- CARD FALSIFIER: Any inferred capability is advertised as executed
- CARD MATHEMATICS: typed states; proof obligations; epistemic uncertainty
- CARD THRESHOLD POLICY: Derive the fixture-specific bound or ratify product target before implementation tests; preserve existing frozen gates; a catalogue prediction is not a preregistered numeric certificate.
- CARD DYAD POLICY: REQUIRED when integrated changes affect visible behavior; GLM operates the documented image/question workflow. Reference-only or source-only scope records NOT_APPLICABLE with reason.
- CARD DELIVERABLES:
  1. Per-device and per-law support records with independent evidence classes
  2. Independent reference/benchmark and executed negative controls appropriate to this scope
  3. Reproduction commands, source identity, preserved evidence and limitations
  4. Integration contract and full autonomous handoff

**Scope note:** the card reserves no paths itself (write_scope: "UNRESERVED: coordinator must assign exact exclusive paths before implementation."). The scope proposed above is the evidence/records home; the lead assigns the exact exclusive implementation paths when admitting this task, under the controller path-scope rules.

**Falsifier (named before the run, from the card):** Any inferred capability is advertised as executed

Acceptance: NOT CLAIMED. This draft is planning data; admission, execution, evidence and acceptance run only through the lead-authorized task lifecycle (create_task → claim → prereg → run → submit_review → review → integration).

