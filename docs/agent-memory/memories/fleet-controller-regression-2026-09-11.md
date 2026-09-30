---
name: fleet-controller-regression-2026-09-11
description: The review-handoff claim-interceptor regression (dead auto-spawn,
  unbound instance fence) and its fix lane — controller context that outlives
  the session
metadata:
  node_type: memory
  type: project
  originSessionId: sess_8207b32c-37a6-443b-91a8-b9f8901a74d5
---

On 2026-09-11 the instance-plane live smoke (PR #74) proved a production regression in the deployed controller (deployment slot-expansion-e1e0ab98): `ReviewHandoffControl._dispatch` in tools/agent_fleet/review_handoff.py intercepts `claim` unconditionally, and its `_claim_with_detached_review_capacity` (a) omits the fleet-slot-expansion-03 auto-spawn branch (the on-demand slot feature was dead code; live `no_free_slot` refusals at revs 767/781/~890), (b) never binds `owner_instance` (the instance fence was inert — an unfenced twin checkpoint was accepted at rev 778), (c) lacks the enforced-mode `instance_binding_required` guard.

Fix lane: fleet-review-handoff-claim-delegation-02 (successor of -01, which was retired for scope incompleteness — a stale test in test_review_handoff.py pinned the regressed behavior and had to change WITH the fix). Fix shipped as PR #80 (+29/-7, review_handoff.py only, detached-REVIEW capacity accounting the sole deviation; review APPROVE_WITH_FOLLOWUPS with 4/4 mutation probes). **STATUS UPDATE (2026-09-11 night): PR #80 integrated (d8e3b5f5) and its controlled deployment transition COMPLETED — the fix is LIVE in production (auto-spawn, owner_instance binding, enforced guard restored; ALL-EQUAL verified).** Deployment transitions are controlled procedures (backup → fingerprint → quiescence → stop-old → start-new → ALL-EQUAL).

Related systemic fix in flight: evidence-forensics-byte-stability-01 (.gitattributes `-text` for docs/evidence/** — the CRLF forensics class that produced PR #69's gen-2 requeue).

**SECOND controller gap (found by holodeck-gov-06, PR #84, measured on the real 240-card graph)**: the deployed `catalogue_next` (control.py:816-825 exact-casefold id matching) never binds card `GOV-0X` to realized task `holodeck-gov-0X`, so the realized root is perpetually re-proposed and every dependent is permanently blocked — the discovery engine cannot see the fleet's realization-id convention. Fix `fleet-catalogue-realization-matching-01` (PR #92, APPROVE_WITH_FOLLOWUPS with 4/4 mutation probes + four-way backward-compat): match via the tasks' `realized_from` provenance field (card realized iff a realized-or-active task cites it; abandonment re-proposes; OLD id-matching stays as fallback). **STATUS: PR #92 integrated (bf1a72f6) and DEPLOYMENT TRANSITION #2 COMPLETE (catalogue-provenance-bf1a72f6, ALL-EQUAL rev 1065) — but the LIVE test still returns [GOV-01]**: the fix is correct, the DATA predates it — every existing holodeck task was created before `realized_from` existed (additive migration setdefaults None → provenance sets empty → id-fallback applies). Data fix: `fleet-task-provenance-backfill-01` (rev 1066; supervisor `task_provenance_set` op + backfill of holodeck-gov-01..06/math-01/mat-01 AFTER the op deploys; itself the first task created WITH realized_from='GOV-06'). Forward admissions carry realized_from at create_task — lead practice effective immediately. catalogue_next is NOT yet the roadmap source of truth until backfill lands.

**Why:** the regression shaped a whole session wave; the -01→-02 retirement also set the precedent for fixing tests that pin bugs (rename + assert restored semantics, same PR as the fix); the provenance data gap is the standing example that a correct fix + legacy data still needs a migration lane.
**How to apply:** PR #80's fix is live (auto-spawn + instance binding verified by three independent lane-side measurements); after the backfill op deploys and the eight tasks are backfilled, verify catalogue_next offers the true frontier before trusting it.
