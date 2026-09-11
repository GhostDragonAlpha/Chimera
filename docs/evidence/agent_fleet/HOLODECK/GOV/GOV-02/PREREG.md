# PREREG — holodeck-gov-02 (gen 1)

- Agent: subagent-worker-10. Slot 9, worktree E:\ChimeraWork\slot-09, branch
  astra/tasks/holodeck-gov-02, base 62b8e35757c71e31d621c26b32a7c52558905b02
  (verified HEAD==base, clean, index 6050 entries, before any work).
- Card GOV-02 verbatim from the integrated draft
  docs/evidence/agent_fleet/CATALOGUE_PACKET_BATCH/drafts/DRAFT-holodeck-gov-02.md
  (catalogue digest b9d32319, content_sha256 46a03c8e5f7b829b...); dep holodeck-gov-01
  INTEGRATED (PR #77, my lane).
- SOURCE-ONLY lane: DEPLOYED contract studied from the source text at base
  (tools/agent_fleet/control.py, review_handoff.py; sha256 recorded in RESULT.md).
  The live service at 127.0.0.1:8099 is NEVER contacted. DYAD: NOT_APPLICABLE —
  source-only scope; reason in RESULT.md per the card's DYAD policy.
- This commit contains the prereg ONLY. No model, no controls, no results.

## CARD MEMBRANE (quoted verbatim from the card)

- CARD STATEMENT: Per-device and per-law support records with independent evidence classes
- CARD PREDICTION: Missing runtime or DYAD evidence remains unknown regardless of unit-test success
- CARD FALSIFIER (named BEFORE the run, for the reference model and the source trace):
  **Any inferred capability is advertised as executed**
- CARD MATHEMATICS: typed states; proof obligations; epistemic uncertainty
- CARD THRESHOLD POLICY: Derive the fixture-specific bound or ratify product target
  before implementation tests; preserve existing frozen gates; a catalogue prediction is
  not a preregistered numeric certificate.

## REFERENCE MODEL CONTRACT (fixed before implementation)

`reference/gov02_capability_registry.py`, stdlib-only, inside this evidence scope.
Evidence-class registry with typed states (MISSING < INFERRED < EXECUTED per class;
classes are INDEPENDENT):

- record key = device or law id. Classes tracked per key: `unit_test`, `runtime`, `dyad`.
- `record_unit_test(key)` — sets unit_test=EXECUTED; MUST leave runtime/dyad untouched.
- `infer(key, cls, source)` — sets cls=INFERRED (never EXECUTED, whatever the source claims).
- `reserve_device(key)` — the only path to runtime=EXECUTED (models a real reservation,
  mirroring the deployed resource class system).
- `record_dyad(key, holder)` — requires the same-holder GPU device record at runtime
  EXECUTED, else refuse `dyad_requires_gpu_reservation` (deployed control.py:581).
- `advertise(key, cls, as_executed=False)` — advertisement MUST match the stored class:
  EXECUTED only when that class is EXECUTED; INFERRED stays INFERRED; MISSING stays
  UNKNOWN; any request to advertise a non-EXECUTED class as executed refuses
  `inferred_advertised_as_executed` (the card falsifier gate).
- `qualify(agent, caps, evidence)` — SUPERVISOR-only; requires non-empty evidence text
  (mirrors deployed control.py:430-439); is the ONLY op that mutates an agent's
  capability set; test results can never call it.
- `claim_requires(agent, caps)` — subset gate refusing `capability_missing` (deployed 526).
- `save()/load()` — registry survives restart with all evidence classes intact.

## PREREGISTERED NUMBERS / THRESHOLDS (stated before ANY implementation test)

Verdict rule: every row must reach its full N/N; a miss is REPORTED (and for model rows
the model is corrected with the fired run retained); deployed-source findings are never
edited to fit.

- R1 positives, N=4/4: (a) unit-test pass recorded, runtime/dyad untouched (still
  MISSING); (b) full chain unit→reserve→dyad advertises EXECUTED at all three classes;
  (c) supervisor qualify with evidence text grants caps; subset claim then passes;
  (d) save→load preserves every class status exactly (3 keys × 3 classes).
- R2 falsifier-direction negatives (card prediction clause 1 + falsifier), N=4/4 —
  (a) unit-test EXECUTED + advertise runtime as executed → refuse
  `inferred_advertised_as_executed`; runtime stays MISSING (UNKNOWN);
  (b) INFERRED runtime + advertise as executed → refuse; stays INFERRED;
  (c) runtime EXECUTED but dyad MISSING + advertise dyad/full visual capability as
  executed → refuse; dyad stays MISSING (unknown regardless of unit-test success);
  (d) INFERRED from a 'benchmark suite passed' source + advertise executed → refuse;
  source authority never promotes INFERRED.
- R3 chain + authority gates (deployed-mirroring), N=3/3 —
  (a) dyad evidence with no same-holder GPU runtime reservation → refuse
  `dyad_requires_gpu_reservation`;
  (b) non-supervisor qualify → refuse `supervisor_only`;
  (c) qualify with empty evidence → refuse `missing_qualification_evidence`.
- R4 falsifier quantification: across the whole run, the count of states where a
  non-EXECUTED class is advertised as executed must be 0 (this is the card falsifier
  firing count on the model); the count of states where missing dyad/runtime keeps a
  visual capability UNKNOWN must be exactly 3 (R2 c + R2 a runtime + R2 a dyad paths).
- R5 deployed-source trace, N=8/8 gates found and quoted at base with file:line —
  supervisor_only (control.py:431); qualification_evidence required (438); claim caps
  gate capability_missing (526); closed resource-class set (190-191); dyad chain
  dyad_requires_gpu_reservation (581); engine chain engine_requires_gpu_reservation
  (582); scheduler chain chained_requires_gpu_same_task (255); NO-mutation property:
  checkpoint/submit_review store evidence text and never mutate capabilities (quoted
  op bodies; exact lines recorded).
- R6 deviation re-measure at THIS base (62b8e357): owner_instance occurrences in
  review_handoff.py — predicted still 0 (fix PR #80 in review, not integrated at this
  base); control.py count — predicted 9 per the gov-01 measurement at d59518b9 unless
  the file moved, exact count measured and reported either way.

## METHOD

1. `controls/run_controls.py` executes R1-R4 in one process, writes
   `checks/r1_positive.txt`, `checks/r2_falsifier_negatives.txt`,
   `checks/r3_chain_authority.txt`, `checks/r4_falsifier_quantification.txt`.
2. R5/R6 measured read-only from the source text at base into
   `checks/r5_source_trace.txt`, `checks/r6_owner_instance_delta.txt`.
3. RESULT.md: scoreboard, reproduction commands, source identity (git base + file
   sha256), limitations, DYAD NOT_APPLICABLE record.
4. Commits on astra/tasks/holodeck-gov-02 (trailer `Agent: subagent-worker-10`), push
   no-force, PR into astra/gait-capture, submit_review with exact HEAD.
