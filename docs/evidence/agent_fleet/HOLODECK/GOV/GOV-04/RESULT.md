# RESULT — holodeck-gov-04 "Agent packet generation" (gen 1)

Agent: subagent-worker-03 · Slot 10 (`E:\ChimeraWork\slot-10`) · branch
`astra/tasks/holodeck-gov-04` · base `62b8e35757c71e31d621c26b32a7c52558905b02`
(task-record base = tip; HEAD==base verified clean before any work).

## Verdict

**PASS — card falsifier NOT fired in the model; measured comparison complete.**
The independent stdlib-only reference model of the INTENDED base contract
(packet/admission semantics: create_task validation, catalogue admission
gates, claim admission of generated packets, packet content, and the card's
scheduling mathematics) passed every preregistered row at full N/N, and the
measured source comparison at base confirmed each mapped deployed refusal.
The one recorded deviation (live claim path drops `owner_instance`) measured
exactly as predicted and is recorded as a finding — the model keeps the
INTENDED binding.

## Scoreboard (prereg thresholds, all full)

| Row | Threshold | Measured | Content |
|---|---|---|---|
| R1 positive | 8/8 | **8/8** | legal create; claim of READY; packet 4/4 required elements; disjoint second task; catalogue_next eligibility flips only on INTEGRATED dependency; valid topo order; capacity boundary; intended instance-bound mutation accepted (foreign `instance_not_bound`) |
| R2 card falsifier | 6/6 | **6/6** | blocked (dep unintegrated) `dependencies_not_integrated`; RUNNING re-claim `task_not_ready`; overlapping active scope `write_scope_conflict`; BLOCKED-state `task_not_ready`; duplicate id `invalid_or_duplicate_task` with original packet byte-identical; REVIEW-state `task_not_ready` — post-state (owner/generation/state/slot/packet/owner_instance) unchanged in EVERY case |
| R3 admission integrity | 6/6 | **6/6** | `dependencies_must_exist`; absolute scope; `..` scope; protected build scope (child); protected build scope (parent direction); `.git` scope |
| R4 mathematics | 4/4 | **4/4** | valid topological order; critical path == 4 nodes (t-a→t-c→t-e→t-g, derived); 2-worker-slot batches never exceed 2; 7/7 packets in topo order each with 4/4 required elements |
| R5 source trace | 6/6 | **6/6** | every mapped deployed refusal/property present with exact measured file:line (below) |
| R6 deviation | predicted delta | **CONFIRMED** | `owner_instance` occurrences: control.py **8** (predicted 8), review_handoff.py **0** (predicted 0) |

Card falsifier — *"A blocked or already claimed task is silently reassigned"* —
is REFUTED AS A DEFECT in the intended contract: every path that could silently
reassign is gated (`task_not_ready`, `dependencies_not_integrated`,
`write_scope_conflict`, `invalid_or_duplicate_task`) and the model's post-state
assertions show nothing moves. The model itself encodes the gates, so the
falsifier cannot fire against the intended semantics; the DEPLOYED deviation is
the R6 finding below.

## R5 measured source anchors (base 62b8e357, control.py 839 lines)

PREREG quoted approximate anchors read before measurement; the executed rows
are search-anchored and these are the exact measured lines (correction
disclosed, never silently reconciled):

| Semantic | Measured location |
|---|---|
| create_task lead-only gate | `_lead` control.py:113-114 (applied at 504) |
| id regex + duplicate refusal | control.py:506 |
| `path_scope` rules (relative, `.`, `..`, empty, `.git`, protected build both directions) | control.py:41-48 |
| `dependencies_must_exist` | control.py:509 |
| claim READY gate (`task_not_ready`) | control.py:522 |
| `dependencies_not_integrated` | control.py:529 |
| `write_scope_conflict` vs ACTIVE | control.py:531-532 |
| catalogue_next eligibility (PROPOSED, casefold live/done, INTEGRATED-only deps, sorted) | control.py:804-826 |

## R6 measured deviation (recorded finding; fix PR #80 in review at this base)

- Base claim binds the instance: control.py:553-554
  (`owner_instance=p.get('_resolved_instance')`).
- `_task` enforces it: control.py:121-123 (`instance_not_bound`).
- The interceptor claim (`review_handoff.py:55-93`, serving claims when
  active) binds `{owner, slot, state, generation}` at review_handoff.py:90-91
  with NO instance check.
- Measured occurrence counts: `owner_instance` == **0** in review_handoff.py,
  == **8** in control.py (121,122,123,323,499,501,554,697). Both as predicted.
- Consequence: for interceptor-claimed tasks `owner_instance` stays None and
  the intended per-instance fencing is inert on the live claim path
  (`compat` fencing). The reference model keeps the intended binding; the
  deviation is a deployed-contract finding, not model truth.

## Reproduction

```
cd E:/ChimeraWork/slot-10
python docs/evidence/agent_fleet/HOLODECK/GOV/GOV-04/controls/run_controls.py
```
Exit 0 and the scoreboard `{"R1_positive": "8/8", "R2_falsifier_reassignment":
"6/6", "R3_admission_integrity": "6/6", "R4_scheduling": "4/4",
"R5_source_trace": "6/6"}` with `checks/r6_owner_instance_delta.txt` ending
`R6 VERDICT: CONFIRMED`.

## Source identity

- Repository HEAD at execution: 0bcc03ff (prereg commit) + this evidence
  commit; base 62b8e357 (merge of PR #77).
- `tools/agent_fleet/control.py` sha256
  `7cee259b35a21ebe689feb5d77c8f2bb10b7125cd1ea9c3ac06e1cb6254bfa30` (839 lines).
- `tools/agent_fleet/review_handoff.py` sha256
  `ad3674bd2e1f1a60a3762e44cd26578150b2c475b064af042a40bace30b51811` (227 lines).
- Reference model `reference/gov04_reference_model.py` sha256
  `d69a6f5fc1a0130b08f3dc5c940717e2bbf3a8f0a85985da6314a40f0487bbd1` (351 lines,
  stdlib-only: re, pathlib).
- Controls runner `controls/run_controls.py` sha256
  `3f383392eeba01980a62beae59af88bafffb187e67b1f5b17fc4c153da0716be`.

## Corrections and limitations (disclosed)

1. **PREREG line-anchor correction**: the prereg quoted approximate control.py
   anchors (508, 520-521, 525-526, 531-532, 822-825) read before measurement;
   measured anchors differ (509, 522, 529, 531-532, 804-826). The executed R5
   rows are search-anchored; semantics-present is the gate, anchors are
   recorded. First R5 run fired 2/6 on the misanchored fixed-offset checks —
   retained in the runner's history? No: the runner is a single committed
   artifact; the misanchored run was pre-commit and is disclosed here. The
   committed checks/*.txt are from the final search-anchored run.
2. **Fixture id rendering**: the prereg DAG wrote `t_a…t_g`; the model
   correctly refused underscores under the deployed id regex
   (`[a-z0-9][a-z0-9-]{0,63}`, control.py:506) — that refusal is itself the
   R5(a) gate working. The fixture is rendered `t-a…t-g` (same DAG shape,
   same critical path 4).
3. **Model scope**: the model mirrors claim/create_task/catalogue/scheduler
   semantics, not the full controller (no agents enrollment, resources,
   feedback, slots provisioning machinery). The interceptor's detached-REVIEW
   capacity accounting (review_handoff.py:66-71) is NOT modeled — it does not
   affect packet generation/admission semantics measured here.
4. **Critical path derivation** is dependency-edge-count based (node count);
   the card names no duration weights, so no weighted variant is claimed.
5. The live service at 127.0.0.1:8099 was never contacted; every deployed
   finding is judged from the source text at base, as the packet requires.

## DYAD

NOT_APPLICABLE — source-only scope: this lane executed no visible behavior and
produced no render; the card's DYAD policy ("REQUIRED when integrated changes
affect visible behavior") does not engage for a reference-model + source-trace
evidence lane. Reason recorded here per the card.

## Integration contract and handoff (card deliverable 4)

- Evidence scope only: `docs/evidence/agent_fleet/HOLODECK/GOV/GOV-04/`
  (PREREG.md, RESULT.md, reference/, controls/, checks/*.txt as *.txt per the
  packet). No production file is touched; frozen gates untouched.
- Downstream consumers (GOV-05+ or the packet-generation tooling lane) inherit:
  the reference model as the executable spec of the INTENDED
  packet/admission/scheduler contract; the R6 measured delta as the regression
  test target for PR #80 (after integration, re-running
  `run_controls.py`'s R6 logic against the integrated base should measure
  owner_instance occurrences in review_handoff.py >= 1 and the interceptor
  binding the instance); and the search-anchored R5 method for future
  contract traces.
- Finish criteria met: packets (this task record's own admission) carried
  dependencies (holodeck-gov-01 INTEGRATED), actual evidence (this file +
  checks/), write scope (the GOV-04 evidence path, exclusively), and finish
  criteria (submit_review with exact HEAD → review → integration).
