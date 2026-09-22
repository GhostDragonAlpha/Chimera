# RULE 0 PRE-REGISTRATION — Workflow Telemetry Pilot (Astra P0 lane)

Written BEFORE any collection/analysis code exists in `tools/agent_fleet/workflow_telemetry/`.
Frozen: 2026-09-21, lane `agent/workflow-telemetry-20260921`, base `6ea2702c` (master tip).

## THEORY (Rule 0, three parts)

**STATEMENT:** The gait campaign's last 10 waves (28–38) are reconstructable as a causal
attempt graph from EXISTING evidence alone (wave receipts, git commit history, the janitor
JSONL, lane `.tmp` artifact mtimes), with separate active and waiting intervals — no new
instrumentation of the lanes is required for the historical half.

**PREDICTION (not yet measured):** For waves 35–38 the reconstructed serial critical path
divides into wait-for-lead / reproduce-parent / mine+derive / build+run-candidate /
verify+decide, and the largest single fraction is mine+derive (the operator's measured 60%
mining claim at wave granularity) — NOT build+run and NOT verify.

**FALSIFIER (named before the run): F-EVENT-GAP**
Reconcile the reconstructed ledger against INDEPENDENT records:
(a) git commit history (preregistration + ship commits per wave on master and lane branches),
(b) the janitor ledger `E:/ChimeraWork/lane-archive/_janitor/janitor.jsonl`,
(c) receipt file sha256 over the receipt JSONs themselves.
**F-EVENT-GAP FIRES if any wave-level attempt visible in the independent records is missing
from the reconstructed ledger, or if any ledger attempt node lacks at least one independent
anchor (git sha, receipt sha256, or janitor event).** Known-scope caveats fixed in advance:
wave 33 has no dedicated ship commit discoverable by the wave-33 grep below the wave-33
receipt search; if it cannot be anchored, that is a GAP and FIRES the falsifier — it may not
be silently dropped or imputed. Missing historical phase TIMINGS are marked `null`
(unknown), never zero — a timing gap is NOT an event gap and does not fire.

**Secondary falsifier (from the Astra protocol, carried): F-TIME-ACCOUNTING** — for waves
35–38, lane duration (base ship commit → this lane's ship commit) must reconcile with the
sum of the five reconstructed phase intervals within ±120 s (artifact mtime granularity);
else FIRES.

## Phase definitions (fixed before measurement; artifact-anchored)

1. `wait_for_lead` — parent's SHIP commit time → first file mtime in this lane's
   `.tmp/wN_receipt/` (or first lane commit if no .tmp survives).
2. `reproduce` — first receipt-dir artifact → `base_tr_stdout` mtime (the parent-state
   byte-reproduction runs).
3. `mine_derive` — `base_tr_stdout` → this wave's PRE-REGISTRATION commit (mining scripts,
   exploration/instrument runs, prereg drafting; the prereg freeze closes the phase).
4. `build_run` — PRE-REGISTRATION commit → candidate `wN_stdout.txt` mtime (amended build +
   candidate run; compile time is NOT separable from run time in these artifacts and is
   reported combined — recorded as an accounting limitation, not split by guess).
5. `verify_decide` — candidate stdout → SHIP commit (trace rerun, fence checks, measurement
   append, ship commit).

Waves 28–34: outcome graph + parent links only; phase timings `null` where artifacts or
commits do not survive (janitor archived w34-agent; lanes 33/34 folded into later lanes).

## Outcome vocabulary

`certified` (ship pass=true, law kept) · `fired` (falsifier fired, law reverted) ·
`pruned` (premise falsified before ship) · `abandoned` (lane ended without terminal record)
· `pending`. Assigned from the receipts' own `pass` / ship-commit message verdicts; no
re-judgment of the physics.

## Gates to run on this branch before receipt

`creature_graph` both roots · `matter_kernel` 9/9 (`tools/port_tests_matter.py`) ·
`python tools/training_gate.py` PASS.
