# RESULT — holodeck-gov-01 (gen 1)

Agent: subagent-worker-10 · slot 4 · worktree E:\ChimeraWork\slot-04 · branch
astra/tasks/holodeck-gov-01 · base d59518b9d9dc002cba43d071495576a236b9d498 (HEAD at
claim, provision verified HEAD==base, clean). CPU only; no GPU/model/engine process;
no controller resources; the live service at 127.0.0.1:8099 was NEVER contacted.

## SOURCE IDENTITY (the deployed contract, read-only reference text)

- tools/agent_fleet/control.py, 839 lines, sha256
  7cee259b35a21ebe689feb5d77c8f2bb10b7125cd1ea9c3ac06e1cb6254bfa30
- tools/agent_fleet/review_handoff.py, 227 lines, sha256
  ad3674bd2e1f1a60a3762e44cd26578150b2c475b064af042a40bace30b51811
- Both at git base d59518b9 (verified by `git cat-file` blobs of the working tree at HEAD).

## DELIVERABLES

- `reference/gov01_reference_model.py` — independent, stdlib-only reference model of the
  INTENDED base contract: claim gate chain (control.py:520-555 semantics), owner+generation
  CAS mutation gate (`_task`, control.py:116-124, including the INTENDED owner_instance
  binding), committed-blob persistence boundary (control.py:65-66/351 semantics).
- `controls/run_controls.py` — executes preregistered R1-R4; every refusal recorded
  verbatim; every post-state assertion computed.
- `checks/r1_positive.txt` — R1 HOLDS 6/6 (legal claim; scope-disjoint claim; exact-gen
  mutation; save→load→mutate; capacity boundary; casefold-prefix disjointness a/b vs a/bc).
- `checks/r2_conflicting_claims.txt` — R2 HOLDS 5/5: equal scope, parent/child,
  child/parent, casefold duplicate all refused `write_scope_conflict` with post-state
  INTACT (owner None, generation 0, READY, unbound slot); same-task double claim refused
  `task_not_ready` leaving single owner alice/gen 1.
- `checks/r3_stale_generation.txt` — R3 HOLDS 4/4: stale generation refused AND stale
  payload not applied; foreign actor refused; unknown task refused; old owner after
  release→re-claim by B refused (`stale_or_foreign_claim`), newer claim intact.
- `checks/r4_restart_persistence.txt` — R4 HOLDS 13/13 (threshold 12): all 5 fields ×
  2 tasks identical after save→load, instance binding preserved across restart,
  post-reload stale mutation refused, post-reload legal mutation accepted.
- `checks/r5_source_trace.txt` — the card prediction judged against the DEPLOYED text:
  3/3 semantics present at base with exact quoted lines: write_scope_conflict
  (control.py:530-532; interceptor copy review_handoff.py:74-77), stale_or_foreign_claim
  CAS (control.py:116-124), serialization+persistence (BEGIN IMMEDIATE control.py:308;
  revision bump 344; state committed 351; state/events tables 65-66; ROLLBACK 359).
- `checks/r6_owner_instance_delta.txt` — measured deviation (below).
- `PREREG.md` — committed FIRST (36b4dbbc), untouched since.

## PREDICTION SCOREBOARD (card prediction / prereg rows)

| row | prediction (fixed in PREREG before any run) | verdict |
|-----|---------------------------------------------|---------|
| R1 | model accepts 6/6 legal sequences | HOLDS 6/6 |
| R2 | model refuses all 5 conflicting-claim paths | HOLDS 5/5 |
| R3 | model refuses all 4 stale-mutation paths | HOLDS 4/4 |
| R4 | persistence preserves 2×5 fields + stale refused + legal accepted | HOLDS 13/13 |
| R5 | all 3 control semantics found in deployed text with quoted lines | HOLDS 3/3 |
| R6 | interceptor bind missing owner_instance; rh occurrences == 0 | HOLDS (rh measured 0) |
| R6-count | control.py owner_instance count == 4 | **MISSED**: measured 9 (5 sites); disclosed per prereg rule "exact count measured and reported" |

## CARD VERDICT (GOV-01 at catalogue digest b9d32319)

- CARD PREDICTION "Conflicting claims are rejected and active assignments survive
  restart": SUPPORTED by the independent reference model (R2/R3 never reproduce the
  falsifier; R4 persistence holds) and by the deployed source text at base (R5: the
  scope gate, the CAS gate, and the serialized committed state are all present).
- CARD FALSIFIER "Two agents own the same write scope or stale state replaces a newer
  claim": NOT reproduced by the intended contract — every attempted dual-ownership and
  stale-write path is refused by name and rolls back without state change.
- MEASURED DEVIATION (finding, not adopted as truth): the live claim path is served by
  the review-handoff interceptor (review_handoff.py:54-93), whose bind at rh.py:90-91
  sets {owner, slot, state, generation} and omits owner_instance (control.py:553-554
  binds all five), and which performs no instance_fencing gate (contrast
  control.py:550-551). Consequence measured at control.py:121-123: for interceptor-claimed
  tasks owner_instance stays None, so the `instance_not_bound` requirement is skipped —
  the INTENDED per-instance fencing is inert on the live claim path while
  instance_fencing=='compat'. This matches feedback c4212657; the fix is in flight as
  fleet-review-handoff-claim-delegation-01. The reference model deliberately models the
  INTENDED contract (binding present, R4 asserts its persistence), not the deviation.

## PRE-RUN RUNNER BUGS (disclosed; model untouched by them)

Three defects in controls/run_controls.py surfaced before any verdict was recorded:
argv plumbing (main(base)), a broken format-concatenation in R1(f), and R4's mutate not
presenting the bound instance (which the model correctly refused with
instance_not_bound — the model enforcing its contract, not a model bug). All three were
runner-side, fixed, and re-run; no control output was edited after the fact. The model
file itself needed one fix pre-run (release_and_reclaim slot capture), committed before
controls ran.

## DYAD RECORD

NOT_APPLICABLE — source-only scope: no executed runtime behavior of the deployed
system was produced or altered; the deliverables are a reference model, its in-process
controls, and static source measurements. Per the card's DYAD policy, reference-only
scope records NOT_APPLICABLE with this reason.

## REPRODUCTION

```
git -C <checkout> rev-parse d59518b9            # base identity
cd docs/evidence/agent_fleet/HOLODECK/GOV/GOV-01
python controls/run_controls.py .               # rewrites checks/r1..r4 (R1-R4)
sha256sum ../../../../../../tools/agent_fleet/control.py \
          ../../../../../../tools/agent_fleet/review_handoff.py   # R5/R6 identity
```
R5/R6 quotes can be re-derived with `sed -n '<line>p'` at the recorded line numbers.

## LIMITATIONS

- The reference model covers claim/CAS/persistence semantics only (the card's
  statement scope); it does not model resources, requests, elections, or the catalogue
  plane.
- Persistence is modeled as whole-registry JSON save/load; the deployed controller uses
  one SQLite BEGIN IMMEDIATE transaction per op. The modeled boundary (committed state
  survives restart; refusal = no state change) is the same; SQLite's crash semantics
  (durability under power loss) are NOT modeled.
- R6 is a static textual measurement of one base revision; it does not observe the live
  service and makes no claim about the in-flight fix's content.
- Concurrency is modeled as sequential calls; the deployed serialization guarantee is
  cited from source (BEGIN IMMEDIATE + ROLLBACK), not stress-tested here.

## SHIP RECORD

- Commit chain: 36b4dbbc (PREREG) -> artifact commit(s) -> pushed HEAD recorded in the
  controller submit_review event; PR into astra/gait-capture; pushed no-force.
- Files changed: docs/evidence/agent_fleet/HOLODECK/GOV/GOV-01/** only.
