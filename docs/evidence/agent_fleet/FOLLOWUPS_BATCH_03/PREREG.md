# PREREG — fleet-followups-batch-03 (gen 1)

- Agent: subagent-worker-11. Slot 7, worktree E:\ChimeraWork\slot-07, branch
  astra/tasks/fleet-followups-batch-03, base
  d8e3b5f54ce95e0f9690a73c381bc5ef20d76f8b (= remote tip at claim, rev 934;
  provision verified HEAD==base, clean; no reconcile needed).
- Nine recorded review followups (C1-C9) as one smallest-corrections lane.
  This commit contains the prereg ONLY. No correction, no run output.
- Code changes TIGHTEN-ONLY; every doc change is a DATED APPEND-ONLY block
  (numstat +N/-0, prior bytes identical modulo the declared CRLF working-form
  normalization; index blobs are LF, attr text=auto — declared here).

## THE NINE (each with its origin; target = this lane's assigned scopes)

- C1 (PR #71 MINOR-2, echoed by #81): tools/agent_fleet/test_task_abandon.py:310
  — the third bare `assertRaises(Refusal)` (empty/whitespace abandon reason)
  tightened to `assertRaisesRegex(Refusal, 'missing_abandon_reason')`. The
  reason name is already proven in the same file (:121-123) for the identical
  guard, so the tightened assertion is verifiable-before-run.
- C2 (PR #75 LOW): tools/agent_fleet/test_capture_window.py — narrow the
  verify_with_transient_tolerance retry trigger from verdict-only to
  VERDICT + SIZE-MATCH: a retry fires only when the first record is
  'occluded_or_foreign_content' AND pinned_size == client_size. Today the
  occluded verdict implies the size gate passed (sizes equal by construction),
  so the set of legal retries is UNCHANGED; the narrowed trigger makes the
  tolerance immune to future verdict-path changes (a size-inconsistent record
  can never be retried). One NEW synthetic falsifier: a scripted occluded
  record with pinned_size != client_size must NOT be retried (verify called
  exactly once, tolerance not fired, reason 'size_mismatch_not_transient').
  The scripted records in TransientToleranceTests gain the faithful
  `pinned_size` key (real records always carry it); NO existing assertion is
  removed or weakened (AST proof retained at run time).
- C3 (PR #74 LOW-1): docs/evidence/agent_fleet/INSTANCE_LIVE_SMOKE/RESULT.txt
  — dated append-only correction relabeling FL3 per the PREREGISTERED
  mapping (the smoke prereg EXCLUDES the deliberate twin probes from the FL3
  population): the observations at revs 777/778 are kept verbatim above; the
  substance label becomes NOT HIT — no unplanned instance-less event occurred.
- C4 (PR #74 LOW-2): docs/evidence/agent_fleet/INSTANCE_LIVE_SMOKE/PREREG.txt
  — dated append-only note annotating the header's "generation 1, slot 13"
  as POST-RUN METADATA (recorded after the run for navigation), never a
  preregistered field.
- C5 (PR #76 MINOR-1): docs/THE_STUDIO_GRID_DEPTH.md — dated append-only
  one-item amendment: the parenthetical at :85-91 ("the contract's mark comes
  only from the accepted fill draw (`create_triangle_pipeline`...)") is
  incomplete: the frost pipeline (engine.cpp ~4865-4879 at d59518b9, "frost
  REPLACES the fill when live — the accepted body, so it must mark the
  stencil exactly like create_triangle_pipeline's fill") also marks; the
  accepted fill is a FAMILY. Verified in this worktree before the run.
- C6 (PR #70 LOW): docs/evidence/agent_fleet/EVIDENCE_LINK_AUDIT/RESULT.md
  — dated append-only wording correction for :21-22: the exact
  reproducibility condition is that re-runs at the PR head include the final
  RESULT.md corpus; the BYTE-IDENTICAL reproduction required the run-time
  stub state (the retained snapshot), not the committed tree alone.
- C7 (PR #78 LOW): docs/evidence/agent_fleet/CATALOGUE_DETERMINISM/RESULT.txt
  — dated append-only note recording the deployment MANIFEST path cited by
  the LF/CRLF clause: E:/ChimeraWork/control/deployments/<deployment-name>/
  MANIFEST.json carries the f32d16ac pin (alternative was dropping the
  clause; the path is recorded instead).
- C8 (PR #80 INFO-2): THIS lane's RESULT.md records the -01 lineage
  durable-tag plan: lineage commits 6a04e2ab / 05f2dac5
  (fleet-review-handoff-claim-delegation-01) are local-only after the remote
  branch deletion; plan = push durable lineage tags
  (astra/lineage/<task-id>) so history survives branch deletion. Both
  commits verified present as local commit objects at base before this run.
- C9 (PR #79 LOW-2, apply forward): this lane retains its own full
  gate-capture consoles (*.txt) for every suite it runs —
  console_test_task_abandon.txt and console_test_capture_window.txt under
  this directory, raw and complete.

## PREREGISTERED PREDICTIONS (stated before any correction or run)

- P1 (C1): after tightening, tools/agent_fleet/test_task_abandon.py is GREEN
  (the full module runs 0 failures), and the tightened line passes — the
  refusal really is 'missing_abandon_reason'.
- P2 (C2): tools/agent_fleet/test_capture_window.py is GREEN after the
  narrowing (34 prior tests + 1 new = 35); an AST assertion-set proof vs the
  batch base shows ZERO changed assertion sets in pre-existing test methods
  (the only additions are the new test and the scripted records' faithful
  pinned_size key); the net retry surface is strictly narrower.
- P3 (C3-C7): `git diff --numstat` on the five touched docs shows +N/-0 each
  (N>=3), with every added block dated and prior bytes identical; `git
  diff` shows no removed line in any of them.
- P4 (C8): both lineage commits exist locally (git cat-file -t = commit) and
  the plan is recorded in this lane's RESULT.md.
- P5 (C9): both consoles exist, non-empty, and contain the full unittest
  output ( Ran N tests ... OK ) for the two touched modules.

## FALSIFIER (named before the run)

Any deletion in prior evidence (numstat -N on any touched doc, or a missing
prior byte); any loosened assertion (AST proof or diff inspection); a fired
regression in either touched module; a correction that edits instead of
appends. Any hit is REPORTED, never patched around.

## METHOD (binding)

Prereg commit -> C1+C2 code tightening -> both module runs (C9 consoles) ->
AST proof -> C3-C7 dated appends -> numstat verification -> C8+C9 into
RESULT.md -> evidence commit -> push no-force -> PR -> submit_review at
exact HEAD. Acceptance NOT_CLAIMED. Trailer: Agent: subagent-worker-11.
