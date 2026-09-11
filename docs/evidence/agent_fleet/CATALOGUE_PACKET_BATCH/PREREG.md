# PREREG — catalogue-packet-batch-01 (gen 1)

- Agent: subagent-worker-10 (instance-protocol session, qualified cpu/docs/evidence/git/python)
- Lead: glm53-lead-02, epoch 5. Slot: 5. Worktree: E:\ChimeraWork\slot-05
- Registered base: bf9d532b361361137e8253c00d498a9326d38fe8; provisioned there, then
  reconciled (fast-forward, zero own commits existed) to then-tip
  4c31999797a9383ea252019be1f32511709fa280 which contains the registered base.
  Provision note: the provisioner left a stale zero-byte index.lock and an empty index
  (11:50 window, no git process alive when checked at 12:02); stale lock removed, index
  rebuilt by the same local reset. Recorded in RESULT.md.
- Catalogue digest used for ALL reads: b9d32319b43a03bbb713f1a4e6120f24065839f15383b0729fb587ba04f9000a
  (imported_revision 651, epoch 5; unchanged through this task — see P5).
- Scope: docs/evidence/agent_fleet/CATALOGUE_PACKET_BATCH only.
- This commit contains the prereg ONLY. No drafts, no actuals, no results.

## TASK MEMBRANE (quoted from the registry packet)

- STATEMENT: the drafts are PLANNING DATA for the lead — faithful to the cards, each with a
  real falsifiable theory sketch, no invented authority.
- PREDICTION: 12 packet drafts + a coverage table mapping card-id -> draft; the lead's
  create_task calls remain the only live mutation path (this lane never calls create_task).
- FALSIFIER: a draft claims acceptance; a card's dependency graph misrepresented; catalogue
  data mutated; or the lead path bypassed.

## PREREGISTERED PREDICTIONS AND THEIR FALSIFIERS (stated before the drafting run)

Orientation disclosure: `catalogue_next` was called while claiming (read-only) and returned
exactly ["GOV-01"]; the card dependency graph of the import source was enumerated read-only
from the frozen source revision 5199d9c3 to design the procedure below. Everything AFTER
this prereg is measurement.

- P1 (batch derivation, deterministic): the "next 12 eligible cards (respects dependencies)"
  are the first 12 pop()s of the deterministic expansion: repeatedly take the sorted
  catalogue_next-style candidate set (status PROPOSED, not realized live, ALL depends_on
  already done), pop the lexicographically smallest id, mark done, recompute.
  PREDICTED OUTPUT (the batch): GOV-01, GOV-02, GOV-03, GOV-04, GOV-05, GOV-06, MATH-01,
  MATH-02, MATH-03, MATH-04, MATH-05, MATH-06.
  FALSIFIER: any of the 12 has an unmet dependency inside the ordered list; or any other
  PROPOSED card lexicographically precedes a listed card at the moment that card is popped.
- P2 (card fidelity): every statement/prediction/falsifier sketch in every draft is copied
  verbatim (or a substring) from that card's own catalogue_read record at digest b9d32319,
  whose raw JSON and content_sha256 are retained under raw/catalogue_read/.
  FALSIFIER: a sketch field not derivable from the retained record; or a sha mismatch.
- P3 (no acceptance claim): every draft is headed `STATUS: DRAFT (PLANNING DATA ... NOT
  ADMITTED)` and no draft claims its card accepted, integrated, or approved.
  FALSIFIER: grep over drafts/ for acceptance-claim phrasing hits a live claim.
- P4 (scope safety): every proposed scope in every draft is relative, has no '..'/'.' or
  drive component, no '.git' part, and does not overlap `chimeraengine/engine/build`.
  FALSIFIER: the programmatic path_scope check (checks output retained as *.txt) reports
  any refusal.
- P5 (no mutation, no bypass): this session's controller ops are exactly: snapshot, claim
  (own task), catalogue_next, catalogue_read x12, checkpoint (own task, optional),
  submit_review (own task). No create_task, no catalogue_import, no foreign-task op; the
  catalogue import digest is still b9d32319 at submit time.
  FALSIFIER: controller events show any other mutation op from this agent, or the digest
  changed without a lead-authorized import.
- P6 (dependency honesty): the coverage table marks GOV-01 ELIGIBLE-NOW and every other
  draft BLOCKED-ON with the exact unmet card deps at their draft time; no blocked card is
  labeled eligible. FALSIFIER: any table/draft eligibility label contradicts the retained
  raw reads.

## METHOD (fixed before the run)

1. Copy raw reads (catalogue_next output; 12 catalogue_read records) into
   `raw/` verbatim as evidence.
2. Generate the 12 drafts from the raw records by script (no hand transcription):
   `drafts/DRAFT-holodeck-<card-id-lower>.md` each carrying: proposed stable id
   (`holodeck-gov-01` ... `holodeck-math-06`; card-derived, path-safe, matching the
   controller id regex), proposed scopes (path-safe, non-protected, explicitly PROPOSALS —
   each card's write_scope is UNRESERVED and only the lead may assign exact exclusive
   paths), proposed capabilities (cpu/docs/python unless the card demands more), proposed
   dependencies mapped from the card graph to draft ids, and a FULL packet text whose
   statement/prediction/falsifier are the card's own fields, plus the card's
   threshold_policy, deliverables, mathematics and DYAD policy — faithful, no invented
   authority, nothing claims admission.
3. `COVERAGE.md`: card-id -> draft file -> proposed id -> deps -> eligibility.
4. `checks/evidence` retained as *.txt: path-safety check output (P4), acceptance-phrase
   scan (P3), batch-derivation replay (P1).
5. `RESULT.md`: actuals, commit chain, worktree/provision reconciliation record.
6. Commit(s) on astra/tasks/catalogue-packet-batch-01, trailer `Agent: subagent-worker-10`,
   push no-force, PR into astra/gait-capture, submit_review with the exact pushed HEAD.

Refusal policy: any STOP condition (refusal from controller, scope conflict, digest change
underneath this task) halts the lane and is recorded, not worked around.
