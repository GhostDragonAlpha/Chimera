# RESULT — fleet-followups-batch-03 (gen 1)

Agent: subagent-worker-11 · slot 7 · worktree E:\ChimeraWork\slot-07 · branch
astra/tasks/fleet-followups-batch-03 · base
d8e3b5f54ce95e0f9690a73c381bc5ef20d76f8b (= remote tip at claim, rev 934;
provision verified HEAD==base, clean; no reconcile needed).
Commits: [prereg] PREREG.md committed FIRST (no actuals) -> [this commit]
corrections + consoles + proofs. Trailer on every commit:
Agent: subagent-worker-11. Acceptance NOT_CLAIMED.

## SCOREBOARD (predictions P1-P5, fixed in PREREG before any correction/run)

| row | prediction | verdict |
|-----|------------|---------|
| P1 | C1 tighten: test_task_abandon green, tightened line passes | HELD — 20/20 OK (console_test_task_abandon.txt); the refusal at :310 is 'missing_abandon_reason' (same guard already proven at :121-123) |
| P2 | C2 narrowing: test_capture_window green incl. new falsifier; AST: zero changed assertion sets in pre-existing methods; retry surface strictly narrower | HELD — 35/35 OK (console_test_capture_window.txt, incl. NEW test_size_mismatched_occlusion_not_retried); ast_assertion_proof.txt: capture_window REMOVED [] CHANGED [] ADDED [1 test]; task_abandon shows exactly ONE changed assertion set = the C1 tighten, base `assertRaises(Refusal)` -> head `assertRaisesRegex(Refusal,'missing_abandon_reason')` (strictly stronger: the regex form passes wherever the bare form passed, not vice versa) |
| P3 | C3-C7 docs: dated append-only, numstat +N/-0 each, prior bytes identical | HELD — git diff --numstat: THE_STUDIO_GRID_DEPTH.md +14/-0; CATALOGUE_DETERMINISM/RESULT.txt +11/-0; EVIDENCE_LINK_AUDIT/RESULT.md +13/-0; INSTANCE_LIVE_SMOKE/PREREG.txt +11/-0; INSTANCE_LIVE_SMOKE/RESULT.txt +11/-0. ZERO deletions anywhere. (Working-copy CRLF normalization declared in PREREG; index blobs LF, attr text=auto.) |
| P4 | C8 lineage commits verified + plan recorded (below) | HELD — git cat-file -t: 6a04e2ab = commit, 05f2dac5 = commit; `git branch -r --contains 6a04e2ab` = EMPTY (no remote branch contains them — local-only after the remote branch deletion, as recorded) |
| P5 | C9 consoles retained (*.txt, full output) | HELD — console_test_task_abandon.txt (Ran 20 tests, OK), console_test_capture_window.txt (Ran 35 tests, OK), raw and complete |

## THE NINE, as landed

- C1 (PR #71 MINOR-2, echoed by #81): test_task_abandon.py:310
  `assertRaises(Refusal)` -> `assertRaisesRegex(Refusal,'missing_abandon_reason')`.
  One line, 1/1 numstat; the assertion is strictly stronger; the module is green.
- C2 (PR #75 LOW): test_capture_window.py verify_with_transient_tolerance
  trigger narrowed to VERDICT + SIZE-MATCH (`pinned_size == client_size`), with
  the named reason 'size_mismatch_not_transient' for a size-inconsistent
  occluded record; NEW synthetic falsifier
  test_size_mismatched_occlusion_not_retried (verify called exactly once, zero
  repaints, tolerance not fired); the scripted records now carry the faithful
  `pinned_size` key. Today's legal retry set is unchanged (an occluded verdict
  implies the size gate passed); the tolerance is now immune to future
  verdict-path changes. Docstring updated to match.
- C3 (PR #74 LOW-1): INSTANCE_LIVE_SMOKE/RESULT.txt — appended dated
  correction: FL3 relabeled NOT HIT per the preregistered mapping (twin
  probes 777/778 are excluded from the FL3 population); observations kept
  verbatim above the block.
- C4 (PR #74 LOW-2): INSTANCE_LIVE_SMOKE/PREREG.txt — appended dated note:
  header "generation 1, slot 13" is POST-RUN METADATA, never a preregistered
  field.
- C5 (PR #76 MINOR-1): THE_STUDIO_GRID_DEPTH.md — appended dated amendment:
  the accepted fill is a FAMILY; the frost pipeline (engine.cpp ~4865-4879 at
  d59518b9: "frost REPLACES the fill when live — ... it must mark the stencil
  exactly like create_triangle_pipeline's fill") also marks. Verified in this
  worktree BEFORE the run (git show d59518b9:ChimeraEngine/engine/engine.cpp).
- C6 (PR #70 LOW): EVIDENCE_LINK_AUDIT/RESULT.md — appended dated narrowing
  of the reproducibility wording (:21-22): re-runs at the PR head reproduce
  the audit over the final RESULT.md corpus; byte-identical reproduction
  required the run-time stub state.
- C7 (PR #78 LOW): CATALOGUE_DETERMINISM/RESULT.txt — appended dated note
  grounding the MANIFEST citation:
  E:/ChimeraWork/control/deployments/slot-expansion-e1e0ab98/MANIFEST.json
  carries the f32d16ac pin (f32d16ac105eb6fca11e27d466f61352b79174ef0d8780553
  dcea7052ae05c0e) — read and verified 2026-09-11 before the append.
- C8 (PR #80 INFO-2): recorded HERE (below).
- C9 (PR #79 LOW-2, apply forward): consoles retained for EVERY suite this
  lane ran — exactly the two touched modules; both raw *.txt under this
  directory; no other suite was run, so no other console is owed.

## C8 — the -01 lineage durable-tag plan (PR #80 INFO-2)

Recorded lineage: fleet-review-handoff-claim-delegation-01 (the
owner_instance claim-path lane) left its two lineage commits LOCAL-ONLY after
its remote branch was deleted:

- 6a04e2abf71aa427940a8c5c855be55f60a322a8 — "preregister + instrument
  claim-delegation regression fix (no fix yet, no actuals)"
- 05f2dac5 (05f2dac5...) — "fail-pre-fix proof retained (5 regression
  failures at unfixed base, 7 preservation passes)"

Verified in this worktree at base d8e3b5f5: both exist as commit objects
(git cat-file -t = commit); `git branch -r --contains 6a04e2ab` is empty.
PLAN (for the lead/supervisor to authorize — this lane has no push authority
beyond its own task branch): push durable lineage tags so task history
survives remote branch deletion:

    git tag astra/lineage/fleet-review-handoff-claim-delegation-01 6a04e2ab
    git push origin astra/lineage/fleet-review-handoff-claim-delegation-01

(or one tag per lineage commit). Convention proposal for the followups
series: any lane whose remote branch is deleted after integration gets a
lineage tag `astra/lineage/<task-id>` at its HEAD, pushed by the integrator
at ack_integration time. Until adopted, lineage recovery remains
local-clone-dependent (the worktrees hold the objects).

## FALSIFIER STATUS

- Any deletion in prior evidence: NOT FIRED (numstat shows -0 on every doc).
- Any loosened assertion: NOT FIRED (ast_assertion_proof.txt: the only changed
  assertion is the C1 TIGHTEN; capture_window zero changed sets).
- A fired regression in either touched module: NOT FIRED (both consoles OK).
- A correction that edits instead of appends: NOT FIRED (all five doc blocks
  are appended; prior bytes byte-identical in the index).

## LIMITATIONS

- The C5 engine.cpp line range (~4865-4879) is cited at d59518b9 as recorded
  by the reviewer; this worktree verified the quote's content at that commit
  (git show), not at every later tip.
- The C7 MANIFEST path is verified on this machine's deployment directory;
  other deployments carry their own MANIFEST names.
- C9 covers the suites THIS lane ran (the two touched modules). The full
  fleet suite was not re-run in this lane; the two modules are the suites the
  touched lanes own (batch-03 packet's tighten-only scope).

Acceptance: NOT CLAIMED — awaiting lead review (machine-generated brief;
verdict self-integrates on APPROVE).

## COMMIT-MECHANICS NOTE (disclosed before push)

The C6 append makes EVIDENCE_LINK_AUDIT/RESULT.md a changed file, so
doc_lint re-validated its citations and flagged the two UNRESOLVED paths the
audit itself quotes as findings (docs/fixture/FIXTURE.md,
tools/no_such_dir_zz/file.py). Precedent: the audit lane's own commit
(214231d7) used CHIMERA_SKIP_DOCLINT=1 "for THIS commit only: the outputs
quote unresolved paths verbatim (that quoting is the deliverable)". This
lane's commit uses the same narrow skip (doclint stanza only; every other
pre-commit gate still ran and passed) for the same reason — the quoted
broken paths are the audit's deliverable, not drift. The append-only
falsifier made editing the quoted lines impossible by design.
