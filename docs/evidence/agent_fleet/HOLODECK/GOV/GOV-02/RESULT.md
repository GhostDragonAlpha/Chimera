# RESULT — holodeck-gov-02 (gen 1)

Agent: subagent-worker-10 · slot 9 · worktree E:\ChimeraWork\slot-09 · branch
astra/tasks/holodeck-gov-02 · base 62b8e35757c71e31d621c26b32a7c52558905b02 (HEAD at
claim, provision verified HEAD==base, clean, index 6050). CPU only; no GPU/model/engine
process; no controller resources; the live service at 127.0.0.1:8099 was NEVER contacted.

## SOURCE IDENTITY (the deployed contract, read-only reference text)

- tools/agent_fleet/control.py, 839 lines, sha256
  7cee259b35a21ebe689feb5d77c8f2bb10b7125cd1ea9c3ac06e1cb6254bfa30 — byte-identical to
  the gov-01 base (d59518b9); the file did not move between the two bases.
- tools/agent_fleet/review_handoff.py, 227 lines, sha256
  ad3674bd2e1f1a60a3762e44cd26578150b2c475b064af042a40bace30b51811 — likewise identical.

## CARD (verbatim, from the integrated draft DRAFT-holodeck-gov-02.md, PR #67)

- CARD STATEMENT: Per-device and per-law support records with independent evidence classes
- CARD PREDICTION: Missing runtime or DYAD evidence remains unknown regardless of unit-test success
- CARD FALSIFIER: Any inferred capability is advertised as executed

## DELIVERABLES

- `reference/gov02_capability_registry.py` — independent stdlib-only model: typed states
  MISSING < INFERRED < EXECUTED per INDEPENDENT evidence class (unit_test / runtime /
  dyad); unit-test success can never touch runtime/dyad; INFERRED is the ceiling of any
  non-executed source; a real (modeled) reservation is the only path to runtime=EXECUTED;
  DYAD chains to the same-holder GPU runtime record (deployed control.py:581 semantics);
  advertisement must match the stored class and refuses `inferred_advertised_as_executed`;
  SUPERVISOR-only qualify with required evidence text (deployed 430-439); claim subset
  gate (deployed 526); save/load persistence.
- `controls/run_controls.py` + `checks/`:
  - `r1_positive.txt` — R1 HOLDS 4/4 (unit-test isolation; full chain advertises
    EXECUTED; qualify+subset claim; 9 class statuses across save/load).
  - `r2_falsifier_negatives.txt` — R2 HOLDS 4/4: unit-success advertising runtime →
    refused, runtime stays MISSING; INFERRED advertising executed → refused, stays
    INFERRED; unit+runtime EXECUTED with dyad MISSING → visual-executed advertisement
    refused, dyad stays UNKNOWN; authoritative-sounding INFERRED source → refused.
  - `r3_chain_authority.txt` — R3 HOLDS 3/3: `dyad_requires_gpu_reservation`;
    `supervisor_only`; `missing_qualification_evidence`.
  - `r4_falsifier_quantification.txt` — R4 HOLDS: 0 advertised-as-executed violations
    over the full key×class sweep (threshold 0); 3/3 preregistered unknown-kept probes.
- `checks/r5_source_trace.txt` — 8/8 deployed gates quoted at base with file:line:
  supervisor_only (431), qualification_evidence (438), capability_missing (526), closed
  class set (190-191), dyad_requires_gpu_reservation (581), engine_requires_gpu_reservation
  (582), chained_requires_gpu_same_task (255), and the no-mutation property.
- `checks/r6_owner_instance_delta.txt` (in r5 file tail) — deviation re-measure: below.
- `PREREG.md` — committed FIRST (8234ae04), untouched since.

## PREDICTION SCOREBOARD

| row | prediction (fixed in PREREG before any run) | verdict |
|-----|---------------------------------------------|---------|
| R1 | model accepts 4/4 legal sequences | HOLDS 4/4 |
| R2 | model refuses all 4 falsifier-direction paths | HOLDS 4/4 |
| R3 | model refuses all 3 chain/authority violations | HOLDS 3/3 |
| R4 | 0 advertised-as-executed violations; 3/3 unknown-kept probes | HOLDS |
| R5 | 8/8 deployed gates found and quoted at base | HOLDS 8/8 |
| R6a | review_handoff.py owner_instance occurrences == 0 at this base | HOLDS (measured 0) |
| R6b | control.py count == 9 (byte-identical file) | HOLDS (measured 9) |

## CARD VERDICT (GOV-02 at catalogue digest b9d32319)

- CARD PREDICTION "Missing runtime or DYAD evidence remains unknown regardless of
  unit-test success": SUPPORTED by the reference model (R2a/R2c, R4 probes: unit-test
  EXECUTED leaves runtime/dyad MISSING; even unit+runtime EXECUTED leaves the DYAD/visual
  class UNKNOWN) and consistent with the deployed text: the ONLY `capabilities=` /
  `qualified=` assignment in control.py is inside the SUPERVISOR-only qualify op (line
  436, evidence-required) — no test result, checkpoint, or submit_review can mutate a
  capability record (grep enumeration in r5_source_trace.txt), and the DYAD class chains
  to a real same-task GPU reservation (581), which a unit test cannot produce.
- CARD FALSIFIER "Any inferred capability is advertised as executed": NOT reproducible
  in the reference model (every path refuses by name; 0 violations in the sweep). In the
  deployed text the advertisement boundary is the qualification authority itself
  (supervisor + evidence text) plus the class chain gates: the falsifier is prevented by
  construction at these gates, with the caveat below.
- MEASURED CAVEAT (deviation finding, not adopted): the deployed registry stores
  qualification provenance as a free-text `qualification` string (436-438) and resource
  classes are declared/validated (186-196) but there is no per-class EXECUTED/INFERRED
  ledger for agent capabilities — the evidence-class separation the card asks for lives
  in the REVIEWER's judgment of that text and in the resource-class chain, not in typed
  registry state. The reference model is the typed-state target the card points at;
  adopting it would be an extension of the deployed contract, not a description of it.
- KNOWN REGRESSION note (per packet): live claim path drops owner_instance
  (review_handoff.py:90-91 binds 4 fields vs base control.py:553-554 binding 5; measured
  again at this base: rh occurrences 0, control.py 9) — fix in review as PR #80
  (fleet-review-handoff-claim-delegation-01). Recorded as a measured finding; the
  intended contract is what the models encode.

## PRE-RUN RUNNER BUGS (disclosed; model untouched by them)

One runner defect surfaced before any verdict was recorded: R3(a) asserted on a record
key that a refused op never creates. The refusal-before-state-creation is the model
mirroring the deployed require→Refusal→ROLLBACK semantics (a refused op creates no
state), so the runner now treats record-absence as MISSING. Also, before any run, the
R4 counter was rewritten to count exactly the preregistered quantities (sweep violations
+ the 3 named probes) after the first draft was found to over-count by construction.
No control output was edited after the fact; the model file needed no post-prereg change.

## DYAD RECORD

NOT_APPLICABLE — source-only scope: no executed runtime behavior of the deployed system
was produced or altered; deliverables are a reference model, its in-process controls,
and static source measurements. Per the card's DYAD policy, reference-only scope records
NOT_APPLICABLE with this reason.

## REPRODUCTION

```
git -C <checkout> rev-parse 62b8e357            # base identity
cd docs/evidence/agent_fleet/HOLODECK/GOV/GOV-02
python controls/run_controls.py .               # rewrites checks/r1..r4 (R1-R4)
sha256sum ../../../../../../tools/agent_fleet/control.py \
          ../../../../../../tools/agent_fleet/review_handoff.py   # R5/R6 identity
```
R5/R6 quotes re-derivable with `sed -n '<line>p'` at the recorded line numbers.

## LIMITATIONS

- The reference model covers the capability/evidence-class semantics named by the card;
  it does not model the resource scheduler's feasibility search, elections, or the
  catalogue plane.
- "runtime" evidence is modeled as a reservation event; the deployed system's richer
  runtime gates (engine build identity, port reservation) are out of scope.
- R5/R6 are static measurements of one base revision; no claim is made about the
  in-flight fix's content (PR #80).
- Concurrency is modeled as sequential calls; the deployed serialization guarantee is
  cited from source (BEGIN IMMEDIATE + ROLLBACK, control.py:308/359), not stress-tested.

## SHIP RECORD

- Commit chain: 8234ae04 (PREREG) -> this artifact commit -> pushed HEAD recorded in the
  controller submit_review event; PR into astra/gait-capture; pushed no-force.
- Files changed: docs/evidence/agent_fleet/HOLODECK/GOV/GOV-02/** only.
