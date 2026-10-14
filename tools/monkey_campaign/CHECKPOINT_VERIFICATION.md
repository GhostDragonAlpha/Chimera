# Checkpoint workflow verification — 2026-09-24

Scope: planner completion semantics and a read-only checkpoint evidence checker.
Preregistered in CHECKPOINT_PREREGISTRATION.md (staged as PREREGISTRATION.md before code/tests).

Failing-first regression, before the fix:

```
test_integrated_tasks_do_not_prove_visual_or_human_acceptance ... FAIL
AssertionError: True is not false
Ran 1 test in 0.001s
FAILED (failures=1)
```

The old planner set goal_complete=true from controller INTEGRATED records with nonempty
receipt strings. The correction separates implementation_integrated and leaves actual
goal acceptance to the coordinator's complete evidence/human check.

Post-fix staged battery: 41 tests discovered, 40 passed, one skipped (existing symlink
fixture: host did not permit creating links). The new tests exercise first-unmet-gate
selection, physics failure despite visual PASS, inconclusive visual review, changed/missing
evidence, scope/claim/generation/candidate/criteria/run mismatch, mixed capture/state
intervals, still-image motion claims, self-review, N/A waivers, context tampering, nonvisual
exceptions, fake human authority, path escapes, bounded reads and malformed receipt JSON.

Independent review found a concurrent-context-rewrite defect in the first checker version:
the file was hashed and then reopened for parsing. A targeted pre-fix test failed with
`'controller_acceptance' != 'visual'` (1 test, 1 failure). The checker now parses exactly
the bounded byte buffer whose digest was checked; that regression passes in the final
battery. Both pre-fix failures are preserved here instead of being omitted from the record.

The candidate identity tests mutate manifest bytes for EXE/shader/scene/policy claims.
They do not inspect those binaries or establish what a running process actually loaded.

Tests use synthetic evidence bytes; even the .mp4 fixture is synthetic. No video decoding,
actual visual judgment, physics test, human authentication, engine run, GPU work, fleet
dispatch, publisher operation or continued coordinator execution is claimed by this suite.
The evidence checker never returns goal_complete=true. ready_for_controller_review means
the supplied record structure and file hashes passed; real judgments remain to be verified.

The original scope catalogue is not edited. No deployment or claim that the model harness
automatically resumes follows from these local tests. The workflow explicitly requires
observing real completion-to-next-action events without operator prompting.
