# RECEIPT — Workflow Telemetry Pilot (Astra P0), 2026-09-21

Lane: `agent/workflow-telemetry-20260921` (base `6ea2702c`, master tip at clone).
Agent: GLM 5.3. Prereg (Rule 0, frozen BEFORE any collection code):
`PREREGISTER_F_EVENT_GAP.md` in this directory.

## What was built (new files only; no lane touched; read-only over the fleet)

- `tools/agent_fleet/workflow_telemetry/schema.py` — the append-only JSONL event
  schema (6-line summary in its docstring): event = {ts, lane, attempt_id,
  parent_manifest, claim_digest, phase, active_seconds, wait_seconds, outcome,
  resources, parent_attempt, child_attempts, policy_version, anchors, note};
  phases registered|building|running|verifying|deciding; outcomes
  certified|fired|pruned|abandoned|pending; UNKNOWN timing is null, never zero.
- `tools/agent_fleet/workflow_telemetry/collectors.py` — four retroactive
  collectors over EXISTING evidence only: (1) wave receipts 28–38 mined from the
  w35–w39 worktrees (sha256-anchored), (2) git wave-commit history from the
  canonical clone AND the chained w38 lane repo, (3) the janitor JSONL
  (`E:/ChimeraWork/lane-archive/_janitor/janitor.jsonl`, 113 rows, 4 on wave
  dirs), (4) `.tmp/wNN_receipt/` artifact mtimes for waves 35–38 — the only
  sub-commit-granularity clock that survives.
- `tools/agent_fleet/workflow_telemetry/reconstruct.py` — attempt graph, serial
  path, F-EVENT-GAP + F-TIME-ACCOUNTING reconciliation.
- `tools/agent_fleet/workflow_telemetry/run_pilot.py` — orchestrator.
- Artifacts here: `ledger.jsonl` (36 events), `serial_path_35_38.json`,
  `f_event_gap.json`.

## The reconstructed attempt graph (waves 28–38 + the 28b fork arm)

12 attempts, fully linked parent→child by ship-sha → base-manifest match
(wave-27 base `d981bc04` is outside scope; wave-28 is the scope root):

| attempt | ship | outcome | successor base names it |
|---|---|---|---|
| wave-28 | 0557fc99 | fired | receipt pass=false |
| wave-28b | 0759f4b2 | abandoned* | "banked as THE HONEST NEGATIVE", no receipt |
| wave-29 | ab60a20b | fired | receipt pass=false |
| wave-30 | 5ff710f2 | pruned | premise FALSIFIED per ship message |
| wave-31 | 5b5c1b13 | pruned (discrepancy recorded) | pass=null; subject names a sub-hypothesis FALSIFIED and ALSO reports the law SHIPPED |
| wave-32 | 77b36f45 | fired | receipt pass=false |
| wave-33 | f5d2656f | fired | receipt pass=false (3 amendments before ship) |
| wave-34 | 0ee71811 | fired | receipt pass=false, law REVERTED |
| wave-35 | e3b1cc83 | fired | pass=false, law REVERTED |
| wave-36 | 38b9c2b1 | fired | pass=false, law REVERTED |
| wave-37 | 371f80d6 | fired | pass=false, law REVERTED |
| wave-38 | 30821ef7 | **certified** | pass=true — the only certified wave in the window |

*wave-28b: the frozen rule maps no-receipt → abandoned; the note in the ledger
cites its real terminal record (`0759f4b2`) verbatim rather than hiding it.

NOTE on wave-31 (a finding about the frozen rule, recorded not tuned away):
the outcome rule matched the keyword FALSIFIED in wave-31's ship subject, but
the full subject shows that keyword names a SUB-hypothesis ("THE PIN-STALENESS
HYPOTHESIS FALSIFIED") inside a formal decomposition whose law "(c) SHIPPED" and
delivered. The frozen rule's output (pruned) is kept in the ledger; the deciding
event's note carries the DISCREPANCY verbatim so the auditor can adjudicate from
the raw anchors in `f_event_gap.json`. Outcome-vocabulary lesson for the live
schema: the deciding event needs the receipt's own letter (pass field), not a
message keyword, wherever a receipt exists.

## THE SERIAL-PATH DIVISION, waves 35–38 (the number that steers investment)

Per-wave seconds on the serial critical path (all four lanes reconcile to
delta 0.0 s — F-TIME-ACCOUNTING PASS at the preregistered ±120 s tolerance):

| wave | span | wait_for_lead | reproduce | mine_derive | build_run | verify_decide |
|---|---|---|---|---|---|---|
| 35 | 4446 s | 776 | 290 | 1762 | 1356 | 262 |
| 36 | 4056 s | 639 | 75 | 2099 | 1120 | 123 |
| 37 | 4005 s | 342 | 72 | 2448 | 904 | 239 |
| 38 | 3491 s | 303 | 96 | 2260 | 201 | 631 |
| **Σ** | **15998 s (266.6 min)** | **2060 (12.9%)** | **533 (3.3%)** | **8569 (53.6%)** | **3581 (22.4%)** | **1255 (7.8%)** |

**Measured division: mining 53.6% / building+running 22.4% / waiting-for-lead
12.9% / verifying+deciding 7.8% / parent-reproduction 3.3%.**

The preregistered PREDICTION held: mine_derive is the largest single fraction
(53.6%, against the operator's ~60% consult estimate). Second finding: build+run
is 22.4% — the wave-38 law build took only 201 s once the composed-law tooling
existed, so the build_run fraction is compressible. Third: waiting-for-lead
averages 8.6 min per handoff (12.9%) — a real queue term the incident ledger
never recorded, and Astra-P1 (verification farm) material.

Accounting limitations, recorded not hidden: (a) build and run are NOT separable
in the surviving artifacts — one combined interval, never split by guess;
(b) wave-36's first run excluded a carried-in harness whose mtime predates the
lane start (inherited state, listed in `carried_in_artifacts_ignored`);
(c) waves 28–34 timings are null (unknown) — the sub-commit artifacts did not
survive; per the prereg they are never imputed zero.

## F-EVENT-GAP: PASS

Every wave-level attempt visible in the independent records (receipts 28–38,
git prereg/ship/merge commits in two repos, janitor events) exists in the
ledger; every ledger attempt carries ≥1 independent anchor (2–7 records each;
counts in `f_event_gap.json`). Missing-from-ledger: none. Unanchored: none.
F-TIME-ACCOUNTING: PASS on all four timed waves (delta 0.0 s each).

## Gates (run on this branch, this lane's state)

- creature_graph, BOTH roots: `pytest tools/creature_graph/tests` from repo root
  AND from `tools/` → **19 passed, 27 subtests** each.
- matter_kernel: `python -m unittest tools.matter_kernel.test_definition` →
  **9/9 OK**.
- training_gate: `python -B tools/training_gate.py` → **PASS** (comfortable
  speed 0.9924 m/s, every target Froude-consistent).

## Honest scope

Retroactive reconstruction only — the collectors mine existing evidence; no lane
was instrumented and no live event collection is wired yet. The next wave can
adopt `schema.py` as its event format; F-EVENT-GAP then becomes a standing
reconciler instead of a one-shot archaeology. The 90-minute law-cycle consult
figure is not reproduced here (that cycle is a different pipeline); this receipt
measures the gait wave cycle at 44.5–74.1 min per wave, mining-dominated.
